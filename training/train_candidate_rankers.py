from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import FeatureUnion, Pipeline

from training.train_event_detectors import split_train_val_test

RANKED_EVENTS = ("decision", "action")
TOP_KS = (1, 3, 5, 10, 20)


def build_ranker() -> Pipeline:
    features = FeatureUnion([
        ("word", TfidfVectorizer(
            ngram_range=(1, 2), min_df=2, max_df=0.995,
            sublinear_tf=True, max_features=30000,
        )),
        ("char", TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), min_df=2,
            sublinear_tf=True, max_features=30000,
        )),
    ])
    classifier = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        C=2.0,
        solver="liblinear",
        random_state=42,
    )
    return Pipeline([("features", features), ("classifier", classifier)])


def sample_within_meeting_negatives(
    df: pd.DataFrame,
    event: str,
    negative_ratio: int = 20,
    random_state: int = 42,
) -> pd.DataFrame:
    """Keep all gold positives and sample hard-enough negatives from the same meetings.

    This changes the learning problem from global rare-event classification into
    within-meeting candidate discrimination, matching how MeetingLens will use the
    model: rank transcript segments after a meeting has already been transcribed.
    """
    rng = np.random.default_rng(random_state)
    parts: list[pd.DataFrame] = []
    for _, group in df.groupby("meeting_id", sort=False):
        positives = group[group["gold_label"] == event]
        if positives.empty:
            continue
        negatives = group[group["gold_label"] != event]
        count = min(len(negatives), max(20, len(positives) * negative_ratio))
        if count < len(negatives):
            chosen = rng.choice(len(negatives), size=count, replace=False)
            negatives = negatives.iloc[chosen]
        parts.extend([positives, negatives])
    if not parts:
        raise ValueError(f"No training rows available for event {event!r}")
    return pd.concat(parts, ignore_index=True).sample(frac=1, random_state=random_state)


def ranking_metrics(frame: pd.DataFrame, probability_column: str, event: str) -> dict:
    meetings: list[dict[str, float]] = []
    for _, group in frame.groupby("meeting_id", sort=False):
        positives = int((group["gold_label"] == event).sum())
        if positives == 0:
            continue
        ranked = group.sort_values(probability_column, ascending=False)
        flags = (ranked["gold_label"].to_numpy() == event)
        ranks = np.flatnonzero(flags) + 1
        row: dict[str, float] = {
            "positive_count": float(positives),
            "first_positive_rank": float(ranks[0]),
        }
        for k in TOP_KS:
            hits = int(flags[:k].sum())
            row[f"hit@{k}"] = float(hits > 0)
            row[f"recall@{k}"] = float(hits / positives)
        meetings.append(row)

    if not meetings:
        return {"meetings_with_gold": 0}
    result = pd.DataFrame(meetings)
    metrics: dict[str, float | int] = {
        "meetings_with_gold": int(len(result)),
        "mrr": float((1.0 / result["first_positive_rank"]).mean()),
        "median_first_positive_rank": float(result["first_positive_rank"].median()),
    }
    for k in TOP_KS:
        metrics[f"hit@{k}"] = float(result[f"hit@{k}"].mean())
        metrics[f"recall@{k}"] = float(result[f"recall@{k}"].mean())
    return metrics


def train_candidate_rankers(
    data_path: str | Path,
    output_dir: str | Path,
    negative_ratio: int = 20,
) -> dict:
    df = pd.read_csv(data_path).dropna(subset=["text", "meeting_id"])
    if "gold_label" not in df.columns:
        raise ValueError("Candidate ranking requires the gold_label column from AMI summary links")
    df = df[df["text"].astype(str).str.len() >= 2].copy()
    df["gold_label"] = df["gold_label"].fillna("other").astype(str)
    train_df, val_df, test_df = split_train_val_test(df)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    metrics: dict[str, object] = {
        "model": "meeting_candidate_ranker_tfidf_word_char_logistic",
        "supervision": "gold_summary_links",
        "input": "transcript_text_only",
        "negative_sampling": "within_meeting",
        "negative_ratio": int(negative_ratio),
        "events": {},
    }
    prediction_frame = test_df[["meeting_id", "speaker", "text", "gold_label"]].copy()

    for event in RANKED_EVENTS:
        sampled = sample_within_meeting_negatives(
            train_df, event, negative_ratio=negative_ratio, random_state=42
        )
        y_train = (sampled["gold_label"] == event).astype(int)
        model = build_ranker()
        model.fit(sampled["text"].astype(str), y_train)

        val_prob = model.predict_proba(val_df["text"].astype(str))[:, 1]
        test_prob = model.predict_proba(test_df["text"].astype(str))[:, 1]
        val_scored = val_df[["meeting_id", "gold_label"]].copy()
        val_scored["probability"] = val_prob
        test_scored = test_df[["meeting_id", "gold_label"]].copy()
        test_scored["probability"] = test_prob

        event_metrics = {
            "sampled_train_rows": int(len(sampled)),
            "train_positive": int(y_train.sum()),
            "test_positive": int((test_df["gold_label"] == event).sum()),
            "test_average_precision": float(average_precision_score(
                (test_df["gold_label"] == event).astype(int), test_prob
            )),
            "validation_ranking": ranking_metrics(val_scored, "probability", event),
            "test_ranking": ranking_metrics(test_scored, "probability", event),
        }
        metrics["events"][event] = event_metrics
        prediction_frame[f"{event}_rank_probability"] = test_prob

        joblib.dump(
            {
                "model": model,
                "event": event,
                "version": "candidate-ranker-gold-v1",
                "input": "transcript_text_only",
                "supervision": "gold_summary_links",
                "usage": "rank_segments_within_meeting",
                "default_top_k": 10 if event == "decision" else 5,
            },
            output / f"{event}_ranker.joblib",
            compress=3,
        )

    prediction_frame.to_csv(output / "test_rankings.csv", index=False)
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train MeetingLens within-meeting candidate rankers")
    parser.add_argument("--data", default="data/processed/ami_events.csv")
    parser.add_argument("--output", default="artifacts/meeting_candidate_rankers")
    parser.add_argument("--negative-ratio", type=int, default=20)
    args = parser.parse_args()
    result = train_candidate_rankers(args.data, args.output, negative_ratio=args.negative_ratio)
    print(json.dumps(result, indent=2))
