from __future__ import annotations

import re
from collections import Counter
from typing import Any

_STOP = {
    "the", "and", "that", "this", "with", "from", "for", "will", "have", "has",
    "was", "were", "are", "our", "your", "their", "about", "into", "before",
    "after", "meeting", "team", "need", "needs", "still", "should", "would",
}
_NEGATION = {"not", "no", "never", "cancel", "cancelled", "canceled", "stop", "drop", "revert", "delay", "postpone"}
_CHANGE = {"instead", "change", "changed", "switch", "move", "replace", "revert", "delay", "postpone", "cancel", "cancelled", "canceled"}
_STATE_TERMS = {
    "cancelled": {"cancel", "cancelled", "canceled", "drop", "stop"},
    "delayed": {"delay", "delayed", "postpone", "postponed", "later"},
    "reverted": {"revert", "reverted", "rollback", "rolled"},
    "switched": {"switch", "switched", "replace", "replaced", "instead"},
    "approved": {"approve", "approved", "confirm", "confirmed", "keep", "keeping", "proceed"},
}
_WEEKDAYS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}


def tokens(text: str) -> set[str]:
    return {
        t for t in re.findall(r"[a-z0-9']+", (text or "").lower())
        if len(t) > 2 and t not in _STOP
    }


def similarity(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _lexical_meeting_search(meetings: list[dict[str, Any]], query: str, limit: int = 12) -> list[dict[str, Any]]:
    q = tokens(query)
    if not q:
        return []
    results: list[dict[str, Any]] = []
    for mi, meeting in enumerate(meetings):
        title = meeting.get("title", f"Meeting {mi + 1}")
        for seg in meeting.get("segments", []):
            body = " ".join([
                str(seg.get("speaker", "")), str(seg.get("kind", "")), str(seg.get("text", "")), title
            ])
            body_tokens = tokens(body)
            overlap = len(q & body_tokens)
            if not overlap:
                continue
            score = overlap / max(1, len(q))
            if seg.get("kind") in {"decision", "risk", "action"}:
                score += 0.12
            results.append({
                "score": round(score, 3),
                "meeting": title,
                "meeting_index": mi,
                "timestamp": seg.get("timestamp") or f"{int(seg.get('minute', 0)):02d}:00",
                "speaker": seg.get("speaker", "Speaker"),
                "kind": seg.get("kind", "conversation"),
                "text": seg.get("text", ""),
                "retrieval": "lexical",
            })
    return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]


def meeting_search(meetings: list[dict[str, Any]], query: str, limit: int = 12) -> list[dict[str, Any]]:
    """Hybrid word/character TF-IDF retrieval with a safe lexical fallback."""
    value = (query or "").strip()
    if not value:
        return []

    records: list[dict[str, Any]] = []
    documents: list[str] = []
    for mi, meeting in enumerate(meetings):
        title = meeting.get("title", f"Meeting {mi + 1}")
        for seg in meeting.get("segments", []):
            text = str(seg.get("text", "")).strip()
            if not text:
                continue
            kind = str(seg.get("kind", "conversation"))
            speaker = str(seg.get("speaker", "Speaker"))
            documents.append(f"{title} {speaker} {kind} {text}")
            records.append({
                "meeting": title,
                "meeting_index": mi,
                "timestamp": seg.get("timestamp") or f"{int(seg.get('minute', 0)):02d}:00",
                "speaker": speaker,
                "kind": kind,
                "text": text,
            })

    if not records:
        return []

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer

        corpus = documents + [value]
        word = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
        char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, min_df=1)
        word_matrix = word.fit_transform(corpus)
        char_matrix = char.fit_transform(corpus)
        word_scores = (word_matrix[:-1] @ word_matrix[-1].T).toarray().ravel()
        char_scores = (char_matrix[:-1] @ char_matrix[-1].T).toarray().ravel()
        scores = 0.72 * word_scores + 0.28 * char_scores

        output = []
        for index, record in enumerate(records):
            score = float(scores[index])
            if record["kind"] in {"decision", "action", "risk"}:
                score += 0.05
            if score < 0.025:
                continue
            output.append({**record, "score": round(min(1.0, score), 3), "retrieval": "hybrid-tfidf"})
        return sorted(output, key=lambda x: x["score"], reverse=True)[:limit]
    except Exception:
        return _lexical_meeting_search(meetings, value, limit=limit)


def recurring_blockers(meetings: list[dict[str, Any]], min_occurrences: int = 2) -> list[dict[str, Any]]:
    clusters: list[dict[str, Any]] = []
    for mi, meeting in enumerate(meetings):
        for risk in meeting.get("risks", []):
            text = risk.get("title", "")
            if not text:
                continue
            best_i, best_sim = None, 0.0
            for ci, cluster in enumerate(clusters):
                sim = similarity(text, cluster["representative"])
                if sim > best_sim:
                    best_i, best_sim = ci, sim
            item = {
                "meeting": meeting.get("title", f"Meeting {mi + 1}"),
                "minute": risk.get("minute", 0),
                "severity": risk.get("severity", "Medium"),
                "text": text,
            }
            if best_i is not None and best_sim >= 0.28:
                clusters[best_i]["occurrences"].append(item)
            else:
                clusters.append({"representative": text, "occurrences": [item]})

    output = []
    for cluster in clusters:
        if len(cluster["occurrences"]) >= min_occurrences:
            output.append({
                "topic": cluster["representative"],
                "count": len(cluster["occurrences"]),
                "meetings": sorted({x["meeting"] for x in cluster["occurrences"]}),
                "evidence": cluster["occurrences"],
            })
    return sorted(output, key=lambda x: x["count"], reverse=True)


def _decision_state(text: str) -> str:
    t = tokens(text)
    for state in ("cancelled", "delayed", "reverted", "switched", "approved"):
        if t & _STATE_TERMS[state]:
            return state
    return "neutral"


def _schedule_markers(text: str) -> set[str]:
    low = (text or "").lower()
    markers = set(re.findall(r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", low))
    markers.update(re.findall(r"\b\d{1,2}(?:st|nd|rd|th)?\b", low))
    return markers


def _topic_similarity(a: str, b: str) -> float:
    remove = _CHANGE | _NEGATION | set().union(*_STATE_TERMS.values()) | _WEEKDAYS
    ta = tokens(a) - remove
    tb = tokens(b) - remove
    if not ta or not tb:
        return similarity(a, b)
    return len(ta & tb) / len(ta | tb)


def decision_drift(meetings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Detect interpretable changes between related decisions across meetings.

    This is evidence-based drift logic, not a neural contradiction model. It separates
    topic similarity from change-state and schedule markers so the UI can explain why
    a pair was flagged.
    """
    decisions: list[dict[str, Any]] = []
    for mi, meeting in enumerate(meetings):
        for di, decision in enumerate(meeting.get("decisions", [])):
            text = " ".join([decision.get("title", ""), decision.get("detail", "")]).strip()
            if text:
                decisions.append({
                    "meeting_index": mi,
                    "meeting": meeting.get("title", f"Meeting {mi + 1}"),
                    "decision_index": di,
                    "text": text,
                    "minute": decision.get("minute", 0),
                    "state": _decision_state(text),
                    "schedule": _schedule_markers(text),
                })

    drift: list[dict[str, Any]] = []
    for i, old in enumerate(decisions):
        for new in decisions[i + 1:]:
            if new["meeting_index"] <= old["meeting_index"]:
                continue
            topic_sim = _topic_similarity(old["text"], new["text"])
            raw_sim = similarity(old["text"], new["text"])
            if max(topic_sim, raw_sim) < 0.20:
                continue

            state_changed = old["state"] != new["state"] and new["state"] != "neutral"
            schedule_changed = bool(old["schedule"] and new["schedule"] and old["schedule"] != new["schedule"])
            explicit_change = bool(tokens(new["text"]) & _CHANGE)
            negation_shift = bool((tokens(old["text"]) ^ tokens(new["text"])) & _NEGATION)

            change_type = None
            if new["state"] == "cancelled":
                change_type = "cancellation"
            elif new["state"] == "delayed":
                change_type = "delay"
            elif new["state"] == "reverted":
                change_type = "reversal"
            elif new["state"] == "switched":
                change_type = "choice change"
            elif schedule_changed:
                change_type = "schedule shift"
            elif state_changed or negation_shift or explicit_change:
                change_type = "decision change"
            elif topic_sim >= 0.55:
                change_type = "decision evolution"

            if not change_type:
                continue

            evidence_count = sum([state_changed, schedule_changed, explicit_change, negation_shift])
            confidence = min(0.98, 0.48 + max(topic_sim, raw_sim) * 0.35 + evidence_count * 0.09)
            drift.append({
                "from_meeting": old["meeting"],
                "to_meeting": new["meeting"],
                "previous": old["text"],
                "current": new["text"],
                "similarity": round(max(topic_sim, raw_sim), 2),
                "topic_similarity": round(topic_sim, 2),
                "change_type": change_type,
                "previous_state": old["state"],
                "current_state": new["state"],
                "schedule_changed": schedule_changed,
                "confidence": round(confidence, 2),
                "reason": change_type,
            })
    return sorted(drift, key=lambda x: (x["confidence"], x["similarity"]), reverse=True)[:12]


def memory_stats(meetings: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "meetings": len(meetings),
        "decisions": sum(len(m.get("decisions", [])) for m in meetings),
        "actions": sum(len(m.get("actions", [])) for m in meetings),
        "risks": sum(len(m.get("risks", [])) for m in meetings),
    }


def build_topic_index(meetings: list[dict[str, Any]], top_n: int = 12) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for meeting in meetings:
        for seg in meeting.get("segments", []):
            counter.update(tokens(seg.get("text", "")))
    return counter.most_common(top_n)


def action_accountability(meetings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten action items and flag ownership/deadline gaps for execution review."""
    output: list[dict[str, Any]] = []
    for meeting_index, meeting in enumerate(meetings):
        meeting_title = meeting.get("title", f"Meeting {meeting_index + 1}")
        for action_index, action in enumerate(meeting.get("actions", [])):
            owner = str(action.get("owner") or "Unassigned").strip()
            due = str(action.get("due") or "Not stated").strip()
            status = str(action.get("status") or "Open").strip()
            missing_owner = owner.lower() in {"unassigned", "unknown", "speaker", "speaker 1", ""}
            missing_due = due.lower() in {"not stated", "tbd", "unknown", "none", ""}
            gaps = []
            if missing_owner:
                gaps.append("owner")
            if missing_due:
                gaps.append("deadline")
            output.append({
                "meeting": meeting_title,
                "meeting_index": meeting_index,
                "action_index": action_index,
                "task": action.get("task", ""),
                "owner": owner,
                "due": due,
                "status": status,
                "timestamp": action.get("timestamp", "00:00"),
                "confidence": action.get("confidence"),
                "needs_attention": bool(gaps),
                "missing": ", ".join(gaps) if gaps else "—",
            })
    return sorted(output, key=lambda x: (not x["needs_attention"], x["meeting_index"], x["action_index"]))
