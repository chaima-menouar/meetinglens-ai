from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Any

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_SENTIMENT = SentimentIntensityAnalyzer()
_DECISION_PATTERNS = [r"\bwe (?:will|'ll|are going to)\b", r"\bwe (?:decided|agreed|confirmed|approved)\b", r"\blet(?:'s| us)\b", r"\bthe decision is\b", r"\bwe're keeping\b", r"\bwe chose\b"]
_ACTION_PATTERNS = [r"\bi (?:will|'ll|am going to)\b", r"\bwe need to\b", r"\bneed to\b", r"\baction item\b", r"\bfollow up\b", r"\bi can\b", r"\bi'll own\b"]
_RISK_PATTERNS = [r"\brisk\b", r"\bblock(?:er|ed|ing)?\b", r"\bdelay(?:ed|ing)?\b", r"\bissue\b", r"\bproblem\b", r"\bconcern\b", r"\bmight fail\b", r"\bmay fail\b", r"\bnot ready\b", r"\bdependency\b"]
_EVENT_PATTERNS = {
    "decision": _DECISION_PATTERNS,
    "action": _ACTION_PATTERNS,
    "risk": _RISK_PATTERNS,
}
_DUE_PATTERNS = [
    r"\b(today|tomorrow|tonight)\b",
    r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    r"\b(by|before)\s+([A-Za-z]+(?:day)?(?:\s+(?:morning|afternoon|evening|noon))?)\b",
    r"\b(by|before)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
]


def _sentiment(text: str) -> str:
    compound = _SENTIMENT.polarity_scores(text or "")["compound"]
    return "positive" if compound >= 0.18 else "negative" if compound <= -0.18 else "neutral"


def _matches(text: str, patterns: list[str]) -> bool:
    value = (text or "").lower()
    return any(re.search(pattern, value) for pattern in patterns)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _ml_scores(text: str) -> dict[str, dict[str, Any]]:
    """Return reviewed production-model scores when promoted artifacts are present.

    Model loading is optional and lazy. A deployment without artifacts or without the
    training runtime keeps using deterministic rules with no behavior regression.
    """
    try:
        from meetinglens_event_model import get_production_event_detectors

        detectors = get_production_event_detectors()
        return detectors.score(text) if detectors.available else {}
    except Exception:
        return {}


def _event_signal(text: str, event: str, scores: dict[str, dict[str, Any]] | None = None) -> tuple[bool, str, float | None]:
    patterns = _EVENT_PATTERNS[event]
    if _matches(text, patterns):
        return True, "rule", None
    values = (scores or _ml_scores(text)).get(event, {})
    if bool(values.get("detected")):
        return True, "model", float(values.get("probability", 0.0))
    return False, "none", None


def _confidence(text: str, patterns: list[str], model_probability: float | None = None) -> float:
    hits = sum(1 for pattern in patterns if re.search(pattern, text.lower()))
    length_bonus = 0.04 if len(text.split()) >= 8 else 0
    rule_confidence = min(0.97, 0.70 + hits * 0.09 + length_bonus)
    if model_probability is None:
        return round(rule_confidence, 2)
    return round(max(rule_confidence if hits else 0.0, model_probability), 2)


def _kind(text: str) -> str:
    scores = _ml_scores(text)
    for event in ("risk", "decision", "action"):
        detected, _, _ = _event_signal(text, event, scores)
        if detected:
            return event
    if "?" in text:
        return "question"
    return "conversation"


def _due(text: str) -> str:
    low = text.lower()
    for pattern in _DUE_PATTERNS:
        m = re.search(pattern, low, flags=re.I)
        if m:
            return _clean(m.group(0)).title()
    return "Not stated"


def _dedupe(items: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: list[set[str]] = []
    for item in items:
        words = {w for w in re.findall(r"[a-z0-9']+", item.get(field, "").lower()) if len(w) > 2}
        if any(words and len(words & prev) / max(1, len(words | prev)) > 0.72 for prev in seen):
            continue
        out.append(item)
        seen.append(words)
    return out


def _extract_decisions(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for item in segments:
        text = _clean(item.get("text", ""))
        if not text:
            continue
        scores = _ml_scores(text)
        detected, source, probability = _event_signal(text, "decision", scores)
        if detected:
            out.append({
                "title": text,
                "detail": f"Evidence: {item.get('speaker','Speaker')} at {item.get('timestamp','00:00')}",
                "confidence": _confidence(text, _DECISION_PATTERNS, probability),
                "signal_source": source,
                "minute": item.get("minute", 0),
                "timestamp": item.get("timestamp", "00:00"),
                "speaker": item.get("speaker", "Speaker"),
            })
    return _dedupe(out, "title")[:8]


def _extract_actions(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for item in segments:
        text = _clean(item.get("text", ""))
        if not text:
            continue
        scores = _ml_scores(text)
        detected, source, probability = _event_signal(text, "action", scores)
        if detected:
            out.append({
                "task": text,
                "owner": item.get("speaker") or "Unassigned",
                "due": _due(text),
                "status": "Open",
                "confidence": _confidence(text, _ACTION_PATTERNS, probability),
                "signal_source": source,
                "minute": item.get("minute", 0),
                "timestamp": item.get("timestamp", "00:00"),
            })
    return _dedupe(out, "task")[:10]


def _extract_risks(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for item in segments:
        text = _clean(item.get("text", ""))
        if not text:
            continue
        scores = _ml_scores(text)
        detected, source, probability = _event_signal(text, "risk", scores)
        if detected:
            severity = "High" if item.get("sentiment") == "negative" or re.search(r"\b(blocked|blocking|critical|fail|delay)\b", text.lower()) else "Medium"
            out.append({
                "title": text,
                "severity": severity,
                "confidence": _confidence(text, _RISK_PATTERNS, probability),
                "signal_source": source,
                "minute": item.get("minute", 0),
                "timestamp": item.get("timestamp", "00:00"),
                "speaker": item.get("speaker", "Speaker"),
            })
    return _dedupe(out, "title")[:8]


def _summary(decisions: list[dict[str, Any]], actions: list[dict[str, Any]], risks: list[dict[str, Any]]) -> str:
    parts = []
    if decisions:
        parts.append(f"{len(decisions)} decision{'s' if len(decisions) != 1 else ''}")
    if actions:
        parts.append(f"{len(actions)} follow-up action{'s' if len(actions) != 1 else ''}")
    if risks:
        parts.append(f"{len(risks)} unresolved risk{'s' if len(risks) != 1 else ''}")
    return "MeetingLens found " + ", ".join(parts) + ". Every extracted item keeps timestamped evidence for review." if parts else "The meeting was transcribed successfully, but no strong decision, action, or risk signals were detected."


def _timestamp(seconds: float) -> str:
    seconds = max(0, int(seconds))
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


def recompute_participants(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    durations: dict[str, float] = {}
    for s in segments:
        name = s.get("speaker") or "Speaker"
        durations[name] = durations.get(name, 0.0) + max(0.2, float(s.get("end_sec", 0)) - float(s.get("start_sec", 0)))
    total = sum(durations.values()) or 1
    return [
        {"name": name, "talk_pct": round(value / total * 100)}
        for name, value in sorted(durations.items(), key=lambda x: -x[1])
    ]


def refresh_intelligence(meeting: dict[str, Any]) -> dict[str, Any]:
    segments = meeting.get("segments", [])
    for s in segments:
        s["kind"] = _kind(s.get("text", ""))
        s["sentiment"] = s.get("sentiment") or _sentiment(s.get("text", ""))
    meeting["participants"] = recompute_participants(segments)
    meeting["decisions"] = _extract_decisions(segments)
    meeting["actions"] = _extract_actions(segments)
    meeting["risks"] = _extract_risks(segments)
    meeting["summary"] = _summary(meeting["decisions"], meeting["actions"], meeting["risks"])
    return meeting


def transcribe_audio(
    uploaded_file: Any,
    model_size: str = "tiny.en",
    diarize: bool = False,
    hf_token: str | None = None,
    min_speakers: int | None = None,
    max_speakers: int | None = None,
) -> dict[str, Any]:
    try:
        from faster_whisper import WhisperModel
    except Exception as exc:
        raise RuntimeError("Audio transcription is unavailable because faster-whisper could not be loaded.") from exc

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
        segments = []
        for idx, seg in enumerate(whisper_segments, start=1):
            text = _clean(seg.text)
            if not text:
                continue
            start = float(seg.start or 0)
            end = float(seg.end or start)
            segments.append({
                "id": idx,
                "minute": int(start // 60),
                "start_sec": round(start, 2),
                "end_sec": round(end, 2),
                "timestamp": _timestamp(start),
                "speaker": "Speaker 1",
                "kind": _kind(text),
                "text": text,
                "sentiment": _sentiment(text),
            })

        diarization_status = "speaker-review-needed"
        diarization_error = None
        diarization_meta: dict[str, Any] | None = None
        if diarize:
            try:
                from meetinglens_diarization import (
                    assign_speakers_to_segments,
                    diarization_diagnostics,
                    diarize_audio_file,
                )

                turns = diarize_audio_file(
                    audio_path,
                    hf_token=hf_token or "",
                    min_speakers=min_speakers,
                    max_speakers=max_speakers,
                )
                segments = assign_speakers_to_segments(segments, turns)
                diarization_meta = diarization_diagnostics(segments, turns)
                diarization_status = (
                    "automatic-complete"
                    if diarization_meta.get("quality") in {"high", "medium"}
                    else "automatic-review-recommended"
                )
            except Exception as exc:
                diarization_status = "automatic-failed"
                diarization_error = str(exc)

        duration_sec = max((s["end_sec"] for s in segments), default=0)
        meeting = {
            "title": Path(getattr(uploaded_file, "name", "Meeting")).stem.replace("_", " ").replace("-", " ").title(),
            "duration_min": max(1, round(duration_sec / 60)),
            "language": getattr(info, "language", "en") or "en",
            "participants": [{"name": "Speaker 1", "talk_pct": 100}],
            "segments": segments,
            "source": "audio",
            "diarization_status": diarization_status,
        }
        if diarization_meta:
            meeting["diarization"] = diarization_meta
        if diarization_error:
            meeting["diarization_error"] = diarization_error
        return refresh_intelligence(meeting)
    finally:
        try:
            os.remove(audio_path)
        except OSError:
            pass
