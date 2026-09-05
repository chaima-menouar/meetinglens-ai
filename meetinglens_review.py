from __future__ import annotations

from copy import deepcopy
from typing import Any


def _candidate_key(candidate: dict[str, Any]) -> tuple[Any, ...]:
    return (
        candidate.get("segment_id"),
        candidate.get("timestamp"),
        candidate.get("speaker"),
        candidate.get("text"),
    )


def confirm_candidate(meeting: dict[str, Any], event: str, candidate: dict[str, Any]) -> dict[str, Any]:
    """Promote one ranked candidate into confirmed meeting intelligence."""
    if event not in {"decision", "action"}:
        raise ValueError("Only decision/action candidates can be confirmed")

    updated = deepcopy(meeting)
    score = float(candidate.get("score", 0.0) or 0.0)
    text = str(candidate.get("text", "")).strip()
    speaker = candidate.get("speaker") or "Speaker"
    timestamp = candidate.get("timestamp") or "00:00"
    minute = candidate.get("minute", 0)

    if event == "decision":
        item = {
            "title": text,
            "detail": f"Human-confirmed AI candidate · {speaker} at {timestamp}",
            "confidence": round(score, 2),
            "signal_source": "human-confirmed-ranker",
            "minute": minute,
            "timestamp": timestamp,
            "speaker": speaker,
        }
        existing = {str(x.get("title", "")).strip().lower() for x in updated.get("decisions", [])}
        if text.lower() not in existing:
            updated.setdefault("decisions", []).append(item)
        queue_key = "decision_candidates"
    else:
        item = {
            "task": text,
            "owner": speaker,
            "due": "Not stated",
            "status": "Open",
            "confidence": round(score, 2),
            "signal_source": "human-confirmed-ranker",
            "minute": minute,
            "timestamp": timestamp,
        }
        existing = {str(x.get("task", "")).strip().lower() for x in updated.get("actions", [])}
        if text.lower() not in existing:
            updated.setdefault("actions", []).append(item)
        queue_key = "action_candidates"

    key = _candidate_key(candidate)
    updated[queue_key] = [x for x in updated.get(queue_key, []) if _candidate_key(x) != key]
    updated.setdefault("review_history", []).append({
        "event": event,
        "outcome": "confirmed",
        "candidate": candidate,
    })
    return updated


def reject_candidate(meeting: dict[str, Any], event: str, candidate: dict[str, Any]) -> dict[str, Any]:
    if event not in {"decision", "action"}:
        raise ValueError("Only decision/action candidates can be rejected")
    updated = deepcopy(meeting)
    queue_key = "decision_candidates" if event == "decision" else "action_candidates"
    key = _candidate_key(candidate)
    updated[queue_key] = [x for x in updated.get(queue_key, []) if _candidate_key(x) != key]
    updated.setdefault("review_history", []).append({
        "event": event,
        "outcome": "rejected",
        "candidate": candidate,
    })
    return updated


def review_stats(meeting: dict[str, Any]) -> dict[str, int]:
    history = meeting.get("review_history", []) or []
    return {
        "decision_candidates": len(meeting.get("decision_candidates", []) or []),
        "action_candidates": len(meeting.get("action_candidates", []) or []),
        "confirmed": sum(1 for x in history if x.get("outcome") == "confirmed"),
        "rejected": sum(1 for x in history if x.get("outcome") == "rejected"),
    }
