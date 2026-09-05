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


def meeting_search(meetings: list[dict[str, Any]], query: str, limit: int = 12) -> list[dict[str, Any]]:
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
            })
    return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]


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


def decision_drift(meetings: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                })

    drift = []
    for i, old in enumerate(decisions):
        for new in decisions[i + 1:]:
            if new["meeting_index"] <= old["meeting_index"]:
                continue
            sim = similarity(old["text"], new["text"])
            if sim < 0.22:
                continue
            old_t, new_t = tokens(old["text"]), tokens(new["text"])
            has_change = bool(new_t & _CHANGE)
            negation_shift = bool((old_t ^ new_t) & _NEGATION)
            if has_change or negation_shift or sim >= 0.5:
                drift.append({
                    "from_meeting": old["meeting"],
                    "to_meeting": new["meeting"],
                    "previous": old["text"],
                    "current": new["text"],
                    "similarity": round(sim, 2),
                    "reason": "possible reversal/change" if (has_change or negation_shift) else "same decision topic evolved",
                })
    return sorted(drift, key=lambda x: x["similarity"], reverse=True)[:12]


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
