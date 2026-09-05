from __future__ import annotations

import argparse
import json
from pathlib import Path

from training.ami_dataset import build_examples, write_csv
from training.download_ami import download_annotations
from training.train_baseline import train
from training.train_candidate_rankers import train_candidate_rankers
from training.train_event_detectors import train_event_detectors
from training.train_production_detectors import train_production_detectors


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
    baseline_dir = Path("artifacts/meeting_event_baseline")
    detectors_dir = Path("artifacts/meeting_event_detectors_v2")
    production_dir = Path("artifacts/meeting_event_detectors_production")
    rankers_dir = Path("artifacts/meeting_candidate_rankers")

    examples = build_examples(root)
    if not examples:
        raise RuntimeError(
            "No training examples were extracted. Check the AMI annotation directory layout."
        )
    write_csv(examples, dataset_path)

    baseline = train(dataset_path, baseline_dir)
    detectors = train_event_detectors(dataset_path, detectors_dir)
    production = train_production_detectors(dataset_path, production_dir)
    rankers = train_candidate_rankers(dataset_path, rankers_dir)
    summary = {
        "dataset": str(dataset_path),
        "baseline_artifact_dir": str(baseline_dir),
        "detectors_artifact_dir": str(detectors_dir),
        "production_artifact_dir": str(production_dir),
        "rankers_artifact_dir": str(rankers_dir),
        "examples": len(examples),
        "labels": baseline["labels"],
        "baseline_macro_f1": baseline["classification_report"]["macro avg"]["f1-score"],
        "baseline_weighted_f1": baseline["classification_report"]["weighted avg"]["f1-score"],
        "v2_macro_event_f1": detectors["macro_event_f1"],
        "v2_macro_event_average_precision": detectors["macro_event_average_precision"],
        "v2_events": detectors["events"],
        "production_macro_event_f1": production["macro_event_f1"],
        "production_macro_event_average_precision": production["macro_event_average_precision"],
        "production_events": production["events"],
        "candidate_rankers": rankers["events"],
        "train_meetings": len(baseline["train_meetings"]),
        "test_meetings": len(baseline["test_meetings"]),
    }
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the MeetingLens AMI training pipeline")
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--corpus-root", default=None)
    args = parser.parse_args()
    run(skip_download=args.skip_download, corpus_root=args.corpus_root)
