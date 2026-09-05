from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import FeatureUnion, Pipeline


def split_by_meeting(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42):
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(splitter.split(df, groups=df["meeting_id"]))
    return df.iloc[train_idx].copy(), df.iloc[test_idx].copy()


def build_pipeline() -> Pipeline:
    features = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.98, sublinear_tf=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, max_features=60000, sublinear_tf=True)),
    ])
    classifier = LogisticRegression(
        max_iter=2500,
        class_weight="balanced",
        C=2.0,
        solver="liblinear",
        random_state=42,
    )
    return Pipeline([("features", features), ("classifier", classifier)])


def train(data_path: str | Path, output_dir: str | Path) -> dict:
    df = pd.read_csv(data_path).dropna(subset=["text", "label", "meeting_id"])
    df = df[df["text"].astype(str).str.len() >= 2].copy()
    if df["label"].nunique() < 2:
        raise ValueError("Need at least two labels to train the baseline model.")
    if df["meeting_id"].nunique() < 3:
        raise ValueError("Need at least three meetings for a leakage-safe train/test split.")

    train_df, test_df = split_by_meeting(df)
    model = build_pipeline()
    model.fit(train_df["text"].astype(str), train_df["label"].astype(str))
    pred = model.predict(test_df["text"].astype(str))

    labels = sorted(df["label"].unique().tolist())
    report = classification_report(test_df["label"], pred, labels=labels, output_dict=True, zero_division=0)
    matrix = confusion_matrix(test_df["label"], pred, labels=labels).tolist()

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output / "meeting_event_baseline.joblib")
    test_df.assign(prediction=pred).to_csv(output / "test_predictions.csv", index=False)
    df["label"].value_counts().rename_axis("label").reset_index(name="count").to_csv(output / "label_distribution.csv", index=False)

    metrics = {
        "model": "tfidf_word_char_logistic_regression",
        "labels": labels,
        "rows_total": int(len(df)),
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "train_meetings": sorted(train_df["meeting_id"].unique().tolist()),
        "test_meetings": sorted(test_df["meeting_id"].unique().tolist()),
        "classification_report": report,
        "confusion_matrix": {"labels": labels, "values": matrix},
    }
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the MeetingLens AMI event baseline")
    parser.add_argument("--data", default="data/processed/ami_events.csv")
    parser.add_argument("--output", default="artifacts/meeting_event_baseline")
    args = parser.parse_args()

    result = train(args.data, args.output)
    print(json.dumps({
        "rows_total": result["rows_total"],
        "train_rows": result["train_rows"],
        "test_rows": result["test_rows"],
        "macro_f1": result["classification_report"]["macro avg"]["f1-score"],
        "weighted_f1": result["classification_report"]["weighted avg"]["f1-score"],
    }, indent=2))
