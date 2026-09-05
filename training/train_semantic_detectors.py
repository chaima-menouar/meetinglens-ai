from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    precision_recall_curve,
    precision_recall_fscore_support,
    roc_auc_score,
)

from training.train_event_detectors import EVENT_LABELS, split_train_val_test

DEFAULT_ENCODER = "sentence-transformers/all-MiniLM-L6-v2"


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


def _encode(model: SentenceTransformer, series: pd.Series, batch_size: int) -> np.ndarray:
    return model.encode(
        series.fillna("").astype(str).tolist(),
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )


def train_semantic_detectors(
    data_path: str | Path,
    output_dir: str | Path,
    encoder_name: str = DEFAULT_ENCODER,
    batch_size: int = 128,
) -> dict:
    df = pd.read_csv(data_path).dropna(subset=["text", "meeting_id"])
    df = df[df["text"].astype(str).str.len() >= 2].copy()
    target_column = "gold_label" if "gold_label" in df.columns else "label"
    df[target_column] = df[target_column].fillna("other").astype(str)
    train_df, val_df, test_df = split_train_val_test(df)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    encoder = SentenceTransformer(encoder_name, device="cpu")
    x_train = _encode(encoder, train_df["text"], batch_size)
    x_val = _encode(encoder, val_df["text"], batch_size)
    x_test = _encode(encoder, test_df["text"], batch_size)

    metrics: dict[str, object] = {
        "model": "semantic_minilm_logistic_regression",
        "encoder": encoder_name,
        "target_column": target_column,
        "supervision": "gold_summary_links" if target_column == "gold_label" else "legacy_mixed_labels",
        "production_features": ["transcript_text"],
        "annotation_features_excluded_from_inputs": ["dialogue_act", "summary_links"],
        "rows_total": int(len(df)),
        "train_rows": int(len(train_df)),
        "validation_rows": int(len(val_df)),
        "test_rows": int(len(test_df)),
        "embedding_dimension": int(x_train.shape[1]),
        "events": {},
    }
    keep_cols = [c for c in ["meeting_id", "speaker", "text", "label", "label_source", "gold_label"] if c in test_df.columns]
    predictions = test_df[keep_cols].copy()

    for event in EVENT_LABELS:
        y_train = (train_df[target_column] == event).astype(int).to_numpy()
        y_val = (val_df[target_column] == event).astype(int).to_numpy()
        y_test = (test_df[target_column] == event).astype(int).to_numpy()
        if y_train.sum() == 0 or y_val.sum() == 0 or y_test.sum() == 0:
            raise ValueError(f"Event {event!r} is missing gold positives in one split")

        classifier = LogisticRegression(
            max_iter=2500,
            class_weight="balanced",
            C=1.0,
            solver="liblinear",
            random_state=42,
        )
        classifier.fit(x_train, y_train)

        val_prob = classifier.predict_proba(x_val)[:, 1]
        threshold, validation_f1 = _best_threshold(y_val, val_prob)
        test_prob = classifier.predict_proba(x_test)[:, 1]

        event_metrics = _evaluate(y_test, test_prob, threshold)
        event_metrics["validation_best_f1"] = validation_f1
        event_metrics["train_positive"] = int(y_train.sum())
        event_metrics["validation_positive"] = int(y_val.sum())
        metrics["events"][event] = event_metrics

        joblib.dump(
            {
                "classifier": classifier,
                "threshold": threshold,
                "event": event,
                "version": "semantic-minilm-gold-v2",
                "encoder": encoder_name,
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
    parser = argparse.ArgumentParser(description="Train transcript-only semantic MeetingLens detectors")
    parser.add_argument("--data", default="data/processed/ami_events.csv")
    parser.add_argument("--output", default="artifacts/meeting_event_detectors_semantic")
    parser.add_argument("--encoder", default=DEFAULT_ENCODER)
    parser.add_argument("--batch-size", type=int, default=128)
    args = parser.parse_args()

    result = train_semantic_detectors(
        args.data,
        args.output,
        encoder_name=args.encoder,
        batch_size=args.batch_size,
    )
    print(json.dumps({
        "encoder": result["encoder"],
        "supervision": result["supervision"],
        "macro_event_f1": result["macro_event_f1"],
        "macro_event_average_precision": result["macro_event_average_precision"],
        "events": result["events"],
    }, indent=2))
