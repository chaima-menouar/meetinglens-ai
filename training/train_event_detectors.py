from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    precision_recall_curve,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import FeatureUnion, Pipeline

EVENT_LABELS = ("decision", "action", "risk")


def _split_groups(df: pd.DataFrame, test_size: float, random_state: int):
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    left_idx, right_idx = next(splitter.split(df, groups=df["meeting_id"]))
    return df.iloc[left_idx].copy(), df.iloc[right_idx].copy()


def split_train_val_test(df: pd.DataFrame):
    train_val, test = _split_groups(df, test_size=0.20, random_state=42)
    train, val = _split_groups(train_val, test_size=0.20, random_state=43)
    return train, val, test


def _model_text(df: pd.DataFrame) -> pd.Series:
    dialogue = df.get("dialogue_act", pd.Series("", index=df.index)).fillna("").astype(str)
    text = df["text"].fillna("").astype(str)
    return "[DA] " + dialogue + " [TEXT] " + text


def build_detector() -> Pipeline:
    features = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.995, sublinear_tf=True, max_features=90000)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True, max_features=70000)),
    ])
    classifier = LogisticRegression(
        max_iter=2500,
        class_weight="balanced",
        C=1.5,
        solver="liblinear",
        random_state=42,
    )
    return Pipeline([("features", features), ("classifier", classifier)])


def _best_threshold(y_true: np.ndarray, probabilities: np.ndarray) -> tuple[float, float]:
    precision, recall, thresholds = precision_recall_curve(y_true, probabilities)
    if len(thresholds) == 0:
        return 0.5, 0.0
    f1 = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-12)
    best = int(np.nanargmax(f1))
    return float(thresholds[best]), float(f1[best])


def _evaluate(y_true: np.ndarray, probabilities: np.ndarray, threshold: float) -> dict:
    pred = (probabilities >= threshold).astype(int)
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, pred, average="binary", zero_division=0
    )
    positives = int(np.sum(y_true))
    negatives = int(len(y_true) - positives)
    return {
        "threshold": round(float(threshold), 6),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "support_positive": positives,
        "support_negative": negatives,
        "average_precision": float(average_precision_score(y_true, probabilities)) if positives else 0.0,
        "roc_auc": float(roc_auc_score(y_true, probabilities)) if positives and negatives else 0.0,
    }


def train_event_detectors(data_path: str | Path, output_dir: str | Path) -> dict:
    df = pd.read_csv(data_path).dropna(subset=["text", "label", "meeting_id"])
    df = df[df["text"].astype(str).str.len() >= 2].copy()
    if df["meeting_id"].nunique() < 5:
        raise ValueError("Need at least five meetings for train/validation/test group splits.")

    train_df, val_df, test_df = split_train_val_test(df)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    metrics: dict[str, object] = {
        "model": "event_specific_tfidf_word_char_logistic_regression",
        "rows_total": int(len(df)),
        "train_rows": int(len(train_df)),
        "validation_rows": int(len(val_df)),
        "test_rows": int(len(test_df)),
        "train_meetings": sorted(train_df["meeting_id"].unique().tolist()),
        "validation_meetings": sorted(val_df["meeting_id"].unique().tolist()),
        "test_meetings": sorted(test_df["meeting_id"].unique().tolist()),
        "events": {},
    }

    prediction_frame = test_df[["meeting_id", "speaker", "text", "label"]].copy()

    for event in EVENT_LABELS:
        y_train = (train_df["label"].astype(str) == event).astype(int).to_numpy()
        y_val = (val_df["label"].astype(str) == event).astype(int).to_numpy()
        y_test = (test_df["label"].astype(str) == event).astype(int).to_numpy()
        if y_train.sum() == 0 or y_val.sum() == 0 or y_test.sum() == 0:
            raise ValueError(f"Event {event!r} is missing positives in one of the meeting-level splits.")

        model = build_detector()
        model.fit(_model_text(train_df), y_train)
        val_prob = model.predict_proba(_model_text(val_df))[:, 1]
        threshold, validation_f1 = _best_threshold(y_val, val_prob)
        test_prob = model.predict_proba(_model_text(test_df))[:, 1]

        event_metrics = _evaluate(y_test, test_prob, threshold)
        event_metrics["validation_best_f1"] = validation_f1
        event_metrics["train_positive"] = int(y_train.sum())
        event_metrics["validation_positive"] = int(y_val.sum())
        metrics["events"][event] = event_metrics

        joblib.dump(
            {"model": model, "threshold": threshold, "event": event, "version": 2},
            output / f"{event}_detector.joblib",
        )
        prediction_frame[f"{event}_probability"] = test_prob
        prediction_frame[f"{event}_prediction"] = (test_prob >= threshold).astype(int)

    event_f1s = [float(metrics["events"][event]["f1"]) for event in EVENT_LABELS]
    event_aps = [float(metrics["events"][event]["average_precision"]) for event in EVENT_LABELS]
    metrics["macro_event_f1"] = float(np.mean(event_f1s))
    metrics["macro_event_average_precision"] = float(np.mean(event_aps))

    prediction_frame.to_csv(output / "test_predictions.csv", index=False)
    df["label"].value_counts().rename_axis("label").reset_index(name="count").to_csv(
        output / "label_distribution.csv", index=False
    )
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train MeetingLens event-specific AMI detectors")
    parser.add_argument("--data", default="data/processed/ami_events.csv")
    parser.add_argument("--output", default="artifacts/meeting_event_detectors_v2")
    args = parser.parse_args()
    result = train_event_detectors(args.data, args.output)
    print(json.dumps({
        "macro_event_f1": result["macro_event_f1"],
        "macro_event_average_precision": result["macro_event_average_precision"],
        "events": result["events"],
    }, indent=2))
