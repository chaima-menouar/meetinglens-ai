from __future__ import annotations

import os
from pathlib import Path
from typing import Any


DEFAULT_MODEL_PATH = "artifacts/meeting_event_baseline/meeting_event_baseline.joblib"
DEFAULT_DETECTOR_DIR = "artifacts/meeting_event_detectors_production"
EVENTS = ("decision", "action", "risk")


class EventModel:
    """Compatibility loader for the original multiclass research baseline."""

    def __init__(self, model_path: str | Path | None = None):
        self.model_path = Path(model_path or os.getenv("MEETINGLENS_EVENT_MODEL", DEFAULT_MODEL_PATH))
        self.model = None
        self.labels: list[str] = []
        self.error: str | None = None
        self._load()

    def _load(self) -> None:
        if not self.model_path.exists():
            return
        try:
            import joblib

            self.model = joblib.load(self.model_path)
            classifier = self.model.named_steps.get("classifier") if hasattr(self.model, "named_steps") else None
            self.labels = [str(x) for x in getattr(classifier, "classes_", [])]
        except Exception as exc:
            self.error = str(exc)
            self.model = None

    @property
    def available(self) -> bool:
        return self.model is not None

    def predict(self, text: str) -> dict[str, Any] | None:
        if not self.available or not (text or "").strip():
            return None
        label = str(self.model.predict([text])[0])
        confidence = None
        probabilities: dict[str, float] = {}
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba([text])[0]
            classifier = self.model.named_steps.get("classifier") if hasattr(self.model, "named_steps") else None
            classes = [str(x) for x in getattr(classifier, "classes_", [])]
            probabilities = {name: round(float(value), 4) for name, value in zip(classes, probs)}
            confidence = probabilities.get(label)
        return {
            "label": label,
            "confidence": round(float(confidence), 4) if confidence is not None else None,
            "probabilities": probabilities,
            "model_path": str(self.model_path),
            "mode": "research-multiclass",
        }


class ProductionEventDetectors:
    """Load independently thresholded transcript-only detectors.

    Training artifacts are deliberately optional. Until a reviewed artifact is promoted
    into the deployed app, ``available`` is false and the application can safely retain
    its deterministic heuristic fallback.
    """

    def __init__(self, detector_dir: str | Path | None = None):
        self.detector_dir = Path(
            detector_dir or os.getenv("MEETINGLENS_EVENT_DETECTOR_DIR", DEFAULT_DETECTOR_DIR)
        )
        self.detectors: dict[str, dict[str, Any]] = {}
        self.errors: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not self.detector_dir.exists():
            return
        try:
            import joblib
        except Exception as exc:
            self.errors["runtime"] = str(exc)
            return

        for event in EVENTS:
            path = self.detector_dir / f"{event}_detector.joblib"
            if not path.exists():
                continue
            try:
                payload = joblib.load(path)
                if not isinstance(payload, dict):
                    raise TypeError("Expected a detector payload dictionary")
                if payload.get("input") not in {None, "transcript_text_only"}:
                    raise ValueError("Refusing detector trained with non-production input features")
                self.detectors[event] = payload
            except Exception as exc:
                self.errors[event] = str(exc)

    @property
    def available(self) -> bool:
        return bool(self.detectors)

    @property
    def complete(self) -> bool:
        return all(event in self.detectors for event in EVENTS)

    def score(self, text: str) -> dict[str, dict[str, Any]]:
        value = (text or "").strip()
        if not value:
            return {}
        output: dict[str, dict[str, Any]] = {}
        for event, payload in self.detectors.items():
            vectorizer = payload.get("vectorizer")
            classifier = payload.get("classifier")
            threshold = float(payload.get("threshold", 0.5))
            if vectorizer is None or classifier is None:
                continue
            matrix = vectorizer.transform([value])
            probability = float(classifier.predict_proba(matrix)[0, 1])
            output[event] = {
                "probability": round(probability, 4),
                "threshold": round(threshold, 4),
                "detected": probability >= threshold,
                "version": payload.get("version", "unknown"),
            }
        return output

    def strongest(self, text: str) -> dict[str, Any] | None:
        scores = self.score(text)
        detected = [
            (event, data)
            for event, data in scores.items()
            if bool(data.get("detected"))
        ]
        if not detected:
            return None
        event, data = max(
            detected,
            key=lambda item: float(item[1]["probability"]) - float(item[1]["threshold"]),
        )
        return {"label": event, **data, "mode": "production-detector"}


_MODEL: EventModel | None = None
_PRODUCTION: ProductionEventDetectors | None = None


def get_event_model() -> EventModel:
    global _MODEL
    if _MODEL is None:
        _MODEL = EventModel()
    return _MODEL


def get_production_event_detectors() -> ProductionEventDetectors:
    global _PRODUCTION
    if _PRODUCTION is None:
        _PRODUCTION = ProductionEventDetectors()
    return _PRODUCTION
