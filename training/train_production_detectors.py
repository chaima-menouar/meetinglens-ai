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

from training.train_event_detectors import EVENT_LABELS, split_train_val_test


def build_detector(max_features: int = 12000) -> tuple[TfidfVectorizer, LogisticRegression]:
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.995,
        sublinear_tf=True,
        max_features=max_features,
    )
    classifier = LogisticRegression(
        max_iter=2500,
        class_weight="balanced",
        C=1.5,
        solver="liblinear",
        random_state=42,
    )
    return vectorizer, classifier


def _best_threshold(y_true: np.ndarray, probabilities: np.ndarray) -> tuple[float, float]:
    precision, recall, thresholds = precision_recall_curve(y_true, probabilities)
    if len(thresholds) == 0:
        return 0.5, 0.0
    f1 = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-12)
    best = int(np.nanargmax(f1))
    return float(thresholds[best]), float(f1[best])


def _evaluate(y_true: np.ndarray, probabilities: np.ndarray, threshold: float) -> dict:
    pred = (probabilities >= threshold).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, pred, average="binary", zero_division=0
    )
    positives = int(y_true.sum())
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


def train_production_detectors(data_path: str | Path, output_dir: str | Path) -> dict:
    df = pd.read_csv(data_path).dropna(subset=["text", "meeting_id"])
    df = df[df["text"].astype(str).str.len() >= 2].copy()
    target_column = "gold_label" if "gold_label" in df.columns else "label"
    df[target_column] = df[target_column].fillna("other").astype(str)
    train_df, val_df, test_df = split_train_val_test(df)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    metrics: dict[str, object] = {
        "model": "production_text_only_tfidf_logistic_regression",
        "target_column": target_column,
        "supervision": "gold_summary_links" if target_column == "gold_label" else "legacy_mixed_labels",
        "production_features": ["transcript_text"],
        "annotation_features_excluded_from_inputs": ["dialogue_act", "summary_links"],
        "rows_total": int(len(df)),
        "train_rows": int(len(train_df)),
        "validation_rows": int(len(val_df)),
        "test_rows": int(len(test_df)),
        "events": {},
    }
    keep_cols = [c for c in ["meeting_id", "speaker", "text", "label", "label_source", "gold_label"] if c in test_df.columns]
    predictions = test_df[keep_cols].copy()

    train_text = train_df["text"].fillna("").astype(str)
    val_text = val_df["text"].fillna("").astype(str)
    test_text = test_df["text"].fillna("").astype(str)

    for event in EVENT_LABELS:
        y_train = (train_df[target_column] == event).astype(int).to_numpy()
        y_val = (val_df[target_column] == event).astype(int).to_numpy()
        y_test = (test_df[target_column] == event).astype(int).to_numpy()
        if y_train.sum() == 0 or y_val.sum() == 0 or y_test.sum() == 0:
            raise ValueError(f"Event {event!r} is missing gold positives in one split")

        vectorizer, classifier = build_detector()
        x_train = vectorizer.fit_transform(train_text)
        classifier.fit(x_train, y_train)

        val_prob = classifier.predict_proba(vectorizer.transform(val_text))[:, 1]
        threshold, validation_f1 = _best_threshold(y_val, val_prob)
        test_prob = classifier.predict_proba(vectorizer.transform(test_text))[:, 1]

        event_metrics = _evaluate(y_test, test_prob, threshold)
        event_metrics["validation_best_f1"] = validation_f1
        event_metrics["train_positive"] = int(y_train.sum())
        event_metrics["validation_positive"] = int(y_val.sum())
        metrics["events"][event] = event_metrics

        joblib.dump(
            {
                "vectorizer": vectorizer,
                "classifier": classifier,
                "threshold": threshold,
                "event": event,
                "version": "production-text-gold-v2",
                "input": "transcript_text_only",
                "supervision": metrics["supervision"],
            },
            output / f"{event}_detector.joblib",
            compress=3,
        )
        predictions[f"{event}_probability"] = test_prob
        predictions[f"{event}_prediction"] = (test_prob >= threshold).astype(int)

    metrics["macro_event_f1"] = float(np.mean([
        float(metrics["events"][event]["f1"]) for event in EVENT_LABELS
    ]))
    metrics["macro_event_average_precision"] = float(np.mean([
        float(metrics["events"][event]["average_precision"]) for event in EVENT_LABELS
    ]))

    predictions.to_csv(output / "test_predictions.csv", index=False)
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train production-safe MeetingLens event detectors")
    parser.add_argument("--data", default="data/processed/ami_events.csv")
    parser.add_argument("--output", default="artifacts/meeting_event_detectors_production")
    args = parser.parse_args()
    result = train_production_detectors(args.data, args.output)
    print(json.dumps({
        "supervision": result["supervision"],
        "macro_event_f1": result["macro_event_f1"],
        "macro_event_average_precision": result["macro_event_average_precision"],
        "events": result["events"],
    }, indent=2))
