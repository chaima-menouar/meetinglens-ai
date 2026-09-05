from __future__ import annotations

import argparse
import json
from pathlib import Path

from training.ami_dataset import build_examples, write_csv
from training.download_ami import download_annotations
from training.train_baseline import train


def run(skip_download: bool = False, corpus_root: str | None = None) -> dict:
    if corpus_root:
        root = Path(corpus_root)
    elif skip_download:
        root = Path("data/raw/ami/ami_public_manual_1.6.2")
    else:
        root = download_annotations()

    if not root.exists():
        raise FileNotFoundError(f"AMI corpus directory not found: {root}")

    dataset_path = Path("data/processed/ami_events.csv")
    artifact_dir = Path("artifacts/meeting_event_baseline")

    examples = build_examples(root)
    if not examples:
        raise RuntimeError(
            "No training examples were extracted. Check the AMI annotation directory layout."
        )
    write_csv(examples, dataset_path)

    metrics = train(dataset_path, artifact_dir)
    summary = {
        "dataset": str(dataset_path),
        "artifact_dir": str(artifact_dir),
        "examples": len(examples),
        "labels": metrics["labels"],
        "macro_f1": metrics["classification_report"]["macro avg"]["f1-score"],
        "weighted_f1": metrics["classification_report"]["weighted avg"]["f1-score"],
        "train_meetings": len(metrics["train_meetings"]),
        "test_meetings": len(metrics["test_meetings"]),
    }
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the MeetingLens AMI baseline training pipeline")
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--corpus-root", default=None)
    args = parser.parse_args()
    run(skip_download=args.skip_download, corpus_root=args.corpus_root)
