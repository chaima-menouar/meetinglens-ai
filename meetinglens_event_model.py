from __future__ import annotations

import os
from pathlib import Path
from typing import Any


DEFAULT_MODEL_PATH = "artifacts/meeting_event_baseline/meeting_event_baseline.joblib"


class EventModel:
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
        }


_MODEL: EventModel | None = None


def get_event_model() -> EventModel:
    global _MODEL
    if _MODEL is None:
        _MODEL = EventModel()
    return _MODEL
