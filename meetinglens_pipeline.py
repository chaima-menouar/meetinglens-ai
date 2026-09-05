from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Any

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_SENTIMENT = SentimentIntensityAnalyzer()

_DECISION_PATTERNS = [
    r"\bwe (?:will|'ll|are going to)\b",
    r"\bwe (?:decided|agreed|confirmed|approved)\b",
    r"\blet(?:'s| us)\b",
    r"\bthe decision is\b",
    r"\bwe're keeping\b",
]
_ACTION_PATTERNS = [
    r"\bi (?:will|'ll|am going to)\b",
    r"\bwe need to\b",
    r"\bneed to\b",
    r"\baction item\b",
    r"\bfollow up\b",
]
_RISK_PATTERNS = [
    r"\brisk\b",
    r"\bblock(?:er|ed|ing)?\b",
    r"\bdelay(?:ed|ing)?\b",
    r"\bissue\b",
    r"\bproblem\b",
    r"\bconcern\b",
    r"\bmight fail\b",
    r"\bmay fail\b",
]


def _sentiment(text: str) -> str:
    compound = _SENTIMENT.polarity_scores(text or "")["compound"]
    if compound >= 0.18:
        return "positive"
    if compound <= -0.18:
        return "negative"
    return "neutral"


def _matches(text: str, patterns: list[str]) -> bool:
    value = (text or "").lower()
    return any(re.search(pattern, value) for pattern in patterns)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _confidence(text: str, patterns: list[str]) -> float:
    hits = sum(1 for pattern in patterns if re.search(pattern, text.lower()))
    return round(min(0.97, 0.72 + hits * 0.08), 2)


def _extract_decisions(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in segments:
        text = _clean(item.get("text", ""))
        if text and _matches(text, _DECISION_PATTERNS):
            out.append(
                {
                    "title": text,
                    "detail": f"Detected at {item.get('timestamp', '00:00')}",
                    "confidence": _confidence(text, _DECISION_PATTERNS),
                    "minute": item.get("minute", 0),
                }
            )
    return out[:8]


def _extract_actions(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in segments:
        text = _clean(item.get("text", ""))
        if text and _matches(text, _ACTION_PATTERNS):
            owner = item.get("speaker") or "Unassigned"
            out.append(
                {
                    "task": text,
                    "owner": owner,
                    "due": "Not stated",
                    "status": "Open",
                    "minute": item.get("minute", 0),
                }
            )
    return out[:10]


def _extract_risks(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in segments:
        text = _clean(item.get("text", ""))
        if text and _matches(text, _RISK_PATTERNS):
            out.append(
                {
                    "title": text,
                    "severity": "Medium" if item.get("sentiment") != "negative" else "High",
                    "minute": item.get("minute", 0),
                }
            )
    return out[:8]


def _summary(decisions: list[dict[str, Any]], actions: list[dict[str, Any]], risks: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    if decisions:
        parts.append(f"{len(decisions)} decision{'s' if len(decisions) != 1 else ''} detected")
    if actions:
        parts.append(f"{len(actions)} follow-up action{'s' if len(actions) != 1 else ''}")
    if risks:
        parts.append(f"{len(risks)} unresolved risk{'s' if len(risks) != 1 else ''}")
    if not parts:
        return "The meeting was transcribed successfully. No strong decision, action, or risk signals were detected yet."
    return "MeetingLens found " + ", ".join(parts) + ". Review the evidence below before treating extracted items as final."


def _timestamp(seconds: float) -> str:
    seconds = max(0, int(seconds))
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def transcribe_audio(uploaded_file: Any, model_size: str = "tiny.en") -> dict[str, Any]:
    """Transcribe an uploaded English meeting and build the first intelligence layer.

    faster-whisper is imported lazily so the demo/JSON path can still render if the
    optional model dependency is temporarily unavailable during deployment.
    """
    try:
        from faster_whisper import WhisperModel
    except Exception as exc:  # pragma: no cover - deployment-specific
        raise RuntimeError(
            "Audio transcription is unavailable because faster-whisper could not be loaded."
        ) from exc

    suffix = Path(getattr(uploaded_file, "name", "meeting.wav")).suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        audio_path = tmp.name

    try:
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        whisper_segments, info = model.transcribe(
            audio_path,
            language="en",
            vad_filter=True,
            beam_size=3,
            condition_on_previous_text=True,
        )
        segments: list[dict[str, Any]] = []
        for idx, seg in enumerate(whisper_segments, start=1):
            text = _clean(seg.text)
            if not text:
                continue
            start = float(seg.start or 0)
            segments.append(
                {
                    "id": idx,
                    "minute": int(start // 60),
                    "start_sec": round(start, 2),
                    "end_sec": round(float(seg.end or start), 2),
                    "timestamp": _timestamp(start),
                    "speaker": "Speaker",
                    "kind": "conversation",
                    "text": text,
                    "sentiment": _sentiment(text),
                }
            )

        decisions = _extract_decisions(segments)
        actions = _extract_actions(segments)
        risks = _extract_risks(segments)
        duration_sec = max((s["end_sec"] for s in segments), default=0)

        return {
            "title": Path(getattr(uploaded_file, "name", "Meeting")).stem.replace("_", " ").replace("-", " ").title(),
            "duration_min": max(1, round(duration_sec / 60)),
            "language": getattr(info, "language", "en") or "en",
            "summary": _summary(decisions, actions, risks),
            "participants": [{"name": "Speaker", "talk_pct": 100}],
            "segments": segments,
            "decisions": decisions,
            "actions": actions,
            "risks": risks,
            "source": "audio",
            "diarization_status": "pending",
        }
    finally:
        try:
            os.remove(audio_path)
        except OSError:
            pass
