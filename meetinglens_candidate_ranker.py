from __future__ import annotations

import os
from pathlib import Path
from typing import Any


DEFAULT_RANKER_DIR = "artifacts/meeting_candidate_rankers"
RANKED_EVENTS = ("decision", "action")


class MeetingCandidateRankers:
    """Load promoted within-meeting candidate rankers.

    The rankers are intentionally treated as candidate generators, not as final
    decision/action classifiers. They rank transcript segments inside one meeting;
    deterministic extraction rules can then use the score for ordering while the
    UI may expose top model-only candidates for review.
    """

    def __init__(self, ranker_dir: str | Path | None = None):
        self.ranker_dir = Path(
            ranker_dir or os.getenv("MEETINGLENS_CANDIDATE_RANKER_DIR", DEFAULT_RANKER_DIR)
        )
        self.rankers: dict[str, dict[str, Any]] = {}
        self.errors: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not self.ranker_dir.exists():
            return
        try:
            import joblib
        except Exception as exc:
            self.errors["runtime"] = str(exc)
            return

        for event in RANKED_EVENTS:
            path = self.ranker_dir / f"{event}_ranker.joblib"
            if not path.exists():
                continue
            try:
                payload = joblib.load(path)
                if not isinstance(payload, dict):
                    raise TypeError("Expected a ranker payload dictionary")
                if payload.get("input") != "transcript_text_only":
                    raise ValueError("Refusing a ranker trained with non-production input features")
                if payload.get("usage") != "rank_segments_within_meeting":
                    raise ValueError("Refusing an artifact that is not a meeting candidate ranker")
                if payload.get("event") != event:
                    raise ValueError(f"Ranker event mismatch: expected {event}")
                model = payload.get("model")
                if model is None or not hasattr(model, "predict_proba"):
                    raise TypeError("Ranker payload does not contain a probabilistic model")
                self.rankers[event] = payload
            except Exception as exc:
                self.errors[event] = str(exc)

    @property
    def available(self) -> bool:
        return bool(self.rankers)

    @property
    def complete(self) -> bool:
        return all(event in self.rankers for event in RANKED_EVENTS)

    def rank_segments(
        self,
        segments: list[dict[str, Any]],
        event: str,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        if event not in self.rankers:
            return []
        payload = self.rankers[event]
        model = payload["model"]

        indexed: list[tuple[int, str]] = []
        for index, segment in enumerate(segments):
            text = " ".join(str(segment.get("text", "")).split()).strip()
            if text:
                indexed.append((index, text))
        if not indexed:
            return []

        probabilities = model.predict_proba([text for _, text in indexed])[:, 1]
        scored = [
            {
                "event": event,
                "segment_index": index,
                "score": round(float(probability), 6),
                "version": payload.get("version", "unknown"),
            }
            for (index, _), probability in zip(indexed, probabilities)
        ]
        scored.sort(key=lambda item: float(item["score"]), reverse=True)

        limit = top_k
        if limit is None:
            limit = int(payload.get("default_top_k", 10 if event == "decision" else 5))
        limit = max(1, min(int(limit), len(scored)))
        for rank, item in enumerate(scored[:limit], start=1):
            item["rank"] = rank
        return scored[:limit]


_RANKERS: MeetingCandidateRankers | None = None


def get_candidate_rankers() -> MeetingCandidateRankers:
    global _RANKERS
    if _RANKERS is None:
        _RANKERS = MeetingCandidateRankers()
    return _RANKERS
