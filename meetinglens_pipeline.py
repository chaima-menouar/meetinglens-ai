from __future__ import annotations

from functools import lru_cache
from datetime import datetime, timezone
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
_EVENT_PATTERNS = {"decision": _DECISION_PATTERNS, "action": _ACTION_PATTERNS, "risk": _RISK_PATTERNS}
_DUE_PATTERNS = [
    r"\b(today|tomorrow|tonight)\b",
    r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    r"\b(by|before)\s+([A-Za-z]+(?:day)?(?:\s+(?:morning|afternoon|evening|noon))?)\b",
    r"\b(by|before)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
]


def _sentiment(text: str) -> str:
    compound = _SENTIMENT.polarity_scores(text or "")["compound"]
    if compound >= 0.2:
        return "positive"
    if compound <= -0.2:
        return "negative"
    return "neutral"


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _matches(text: str, patterns: list[str]) -> bool:
    low = text.lower()
    return any(re.search(pattern, low) for pattern in patterns)


def _kind(text: str) -> str:
    if _matches(text, _RISK_PATTERNS):
        return "risk"
    if _matches(text, _ACTION_PATTERNS):
        return "action"
    if _matches(text, _DECISION_PATTERNS):
        return "decision"
    return "conversation"


def _confidence(text: str, patterns: list[str], probability: float | None = None) -> float:
    rule = 0.88 if _matches(text, patterns) else 0.62
    if probability is None:
        return rule
    return round(min(0.99, max(rule, probability)), 2)


def _ml_scores(text: str) -> dict[str, float]:
    try:
        from meetinglens_event_model import predict_event_scores
        return predict_event_scores(text)
    except Exception:
        return {}


def _event_signal(text: str, event: str, scores: dict[str, float]) -> tuple[bool, str, float | None]:
    patterns = _EVENT_PATTERNS[event]
    if _matches(text, patterns):
        return True, "rule", None
    score = scores.get(event)
    if score is None:
        return False, "none", None
    thresholds = {"decision": 0.72, "action": 0.7, "risk": 0.78}
    return score >= thresholds[event], "ml", score


def _rank_candidates(segments: list[dict[str, Any]], event: str, top_k: int) -> list[dict[str, Any]]:
    try:
        from meetinglens_candidate_ranker import rank_meeting_candidates
        return rank_meeting_candidates(segments, event=event, top_k=top_k)
    except Exception:
        return []


def _dedupe(items: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    seen = set()
    output = []
    for item in items:
        value = _clean(str(item.get(key, ""))).lower()
        if value and value not in seen:
            seen.add(value)
            output.append(item)
    return output


def _extract_due(text: str) -> str:
    low = text.lower()
    for pattern in _DUE_PATTERNS:
        match = re.search(pattern, low, flags=re.I)
        if match:
            return match.group(0).strip().title()
    return "Not stated"


def _extract_decisions(segments: list[dict[str, Any]], rankings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = {int(row["segment_index"]): row for row in rankings}
    out = []
    for index, item in enumerate(segments):
        text = _clean(item.get("text", ""))
        if not text:
            continue
        scores = _ml_scores(text)
        detected, source, probability = _event_signal(text, "decision", scores)
        if detected:
            row = {
                "title": text,
                "detail": text,
                "confidence": _confidence(text, _DECISION_PATTERNS, probability),
                "signal_source": source,
                "minute": item.get("minute", 0),
                "timestamp": item.get("timestamp", "00:00"),
                "speaker": item.get("speaker", "Speaker"),
            }
            if index in ranked:
                row["candidate_rank"] = int(ranked[index]["rank"])
                row["candidate_score"] = float(ranked[index]["score"])
            out.append(row)
    out.sort(key=lambda row: (row.get("candidate_rank", 10_000), -float(row.get("confidence", 0.0))))
    return _dedupe(out, "title")[:8]


def _extract_actions(segments: list[dict[str, Any]], rankings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = {int(row["segment_index"]): row for row in rankings}
    out = []
    for index, item in enumerate(segments):
        text = _clean(item.get("text", ""))
        if not text:
            continue
        scores = _ml_scores(text)
        detected, source, probability = _event_signal(text, "action", scores)
        if detected:
            row = {
                "task": text,
                "owner": item.get("speaker", "Unassigned"),
                "due": _extract_due(text),
                "status": "Open",
                "confidence": _confidence(text, _ACTION_PATTERNS, probability),
                "signal_source": source,
                "minute": item.get("minute", 0),
                "timestamp": item.get("timestamp", "00:00"),
            }
            if index in ranked:
                row["candidate_rank"] = int(ranked[index]["rank"])
                row["candidate_score"] = float(ranked[index]["score"])
            out.append(row)
    out.sort(key=lambda row: (row.get("candidate_rank", 10_000), -float(row.get("confidence", 0.0))))
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


def _review_candidates(segments: list[dict[str, Any]], rankings: list[dict[str, Any]], event: str) -> list[dict[str, Any]]:
    patterns = _EVENT_PATTERNS[event]
    output: list[dict[str, Any]] = []
    for ranking in rankings:
        index = int(ranking["segment_index"])
        if index < 0 or index >= len(segments):
            continue
        segment = segments[index]
        text = _clean(segment.get("text", ""))
        if not text or _matches(text, patterns):
            continue
        output.append({
            "text": text,
            "speaker": segment.get("speaker", "Speaker"),
            "timestamp": segment.get("timestamp", "00:00"),
            "minute": segment.get("minute", 0),
            "rank": int(ranking["rank"]),
            "score": float(ranking["score"]),
            "event": event,
            "status": "Needs review",
            "signal_source": "candidate-ranker",
            "model_version": ranking.get("version", "unknown"),
        })
    return output


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
    return [{"name": name, "talk_pct": round(value / total * 100)} for name, value in sorted(durations.items(), key=lambda x: -x[1])]


def refresh_intelligence(meeting: dict[str, Any]) -> dict[str, Any]:
    segments = meeting.get("segments", [])
    for s in segments:
        s["kind"] = _kind(s.get("text", ""))
        s["sentiment"] = s.get("sentiment") or _sentiment(s.get("text", ""))

    decision_rankings = _rank_candidates(segments, "decision", top_k=10)
    action_rankings = _rank_candidates(segments, "action", top_k=5)
    meeting["participants"] = recompute_participants(segments)
    meeting["decisions"] = _extract_decisions(segments, decision_rankings)
    meeting["actions"] = _extract_actions(segments, action_rankings)
    meeting["risks"] = _extract_risks(segments)
    meeting["decision_candidates"] = _review_candidates(segments, decision_rankings, "decision")
    meeting["action_candidates"] = _review_candidates(segments, action_rankings, "action")
    meeting["candidate_ranking"] = {
        "available": bool(decision_rankings or action_rankings),
        "decision_candidates_ranked": len(decision_rankings),
        "action_candidates_ranked": len(action_rankings),
        "mode": "review-first",
    }
    meeting["summary"] = _summary(meeting["decisions"], meeting["actions"], meeting["risks"])
    return meeting


@lru_cache(maxsize=2)
def _get_whisper_model(model_size: str):
    try:
        from faster_whisper import WhisperModel
    except Exception as exc:
        raise RuntimeError("Audio transcription is unavailable because faster-whisper could not be loaded.") from exc
    return WhisperModel(model_size, device="cpu", compute_type="int8")


def transcribe_audio(
    uploaded_file: Any,
    model_size: str = "tiny",
    diarize: bool = False,
    hf_token: str | None = None,
    min_speakers: int | None = None,
    max_speakers: int | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    suffix = Path(getattr(uploaded_file, "name", "meeting.wav")).suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        audio_path = tmp.name

    try:
        model = _get_whisper_model(model_size)
        whisper_segments, info = model.transcribe(
            audio_path,
            language=language,
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
                from meetinglens_diarization import assign_speakers_to_segments, diarization_diagnostics, diarize_audio_file
                turns = diarize_audio_file(
                    audio_path,
                    hf_token=hf_token or "",
                    min_speakers=min_speakers,
                    max_speakers=max_speakers,
                )
                segments = assign_speakers_to_segments(segments, turns)
                diarization_meta = diarization_diagnostics(segments, turns)
                diarization_status = "automatic-complete" if diarization_meta.get("quality") in {"high", "medium"} else "automatic-review-recommended"
            except Exception as exc:
                diarization_status = "automatic-failed"
                diarization_error = str(exc)

        duration_sec = max((s["end_sec"] for s in segments), default=0)
        detected_language = getattr(info, "language", None) or language or "unknown"
        meeting = {
            "title": Path(getattr(uploaded_file, "name", "Meeting")).stem.replace("_", " ").replace("-", " ").title(),
            "duration_min": max(1, round(duration_sec / 60)),
            "language": detected_language,
            "language_probability": round(float(getattr(info, "language_probability", 0.0) or 0.0), 3),
            "participants": [{"name": "Speaker 1", "talk_pct": 100}],
            "segments": segments,
            "source": "audio",
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
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
