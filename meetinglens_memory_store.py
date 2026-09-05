from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_STORE_PATH = "data/runtime/meeting_vault.json"


def meeting_fingerprint(meeting: dict[str, Any]) -> str:
    title = str(meeting.get("title", "Meeting")).strip()
    duration = str(meeting.get("duration_min", 0))
    segments = meeting.get("segments", []) or []
    transcript = "\n".join(str(s.get("text", "")) for s in segments)
    raw = f"{title}|{duration}|{len(segments)}|{transcript}".encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()[:20]


def prepare_meeting(meeting: dict[str, Any]) -> dict[str, Any]:
    item = dict(meeting)
    item.setdefault("meeting_id", meeting_fingerprint(item))
    item.setdefault("saved_at", datetime.now(timezone.utc).isoformat())
    return item


class MeetingMemoryStore:
    """Small durable store for the free Streamlit deployment.

    The default JSON backend persists across browser sessions while the Streamlit
    instance is alive. Streamlit Community Cloud may recreate the filesystem during
    redeploys/reboots, so export remains the portable backup. The interface is kept
    backend-agnostic so a hosted database can replace it without changing pages.
    """

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or os.getenv("MEETINGLENS_MEMORY_PATH", DEFAULT_STORE_PATH))

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []
        items = payload.get("meetings", []) if isinstance(payload, dict) else payload
        return [m for m in items if isinstance(m, dict)] if isinstance(items, list) else []

    def save(self, meetings: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "meetings": meetings}
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        temp.replace(self.path)

    def upsert(self, meeting: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
        item = prepare_meeting(meeting)
        meetings = self.load()
        meeting_id = item["meeting_id"]
        for index, existing in enumerate(meetings):
            if existing.get("meeting_id") == meeting_id or meeting_fingerprint(existing) == meeting_id:
                item["saved_at"] = existing.get("saved_at", item["saved_at"])
                meetings[index] = item
                self.save(meetings)
                return meetings, False
        meetings.append(item)
        self.save(meetings)
        return meetings, True

    def replace_all(self, meetings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped: list[dict[str, Any]] = []
        seen: set[str] = set()
        for meeting in meetings:
            if not isinstance(meeting, dict):
                continue
            item = prepare_meeting(meeting)
            if item["meeting_id"] in seen:
                continue
            seen.add(item["meeting_id"])
            deduped.append(item)
        self.save(deduped)
        return deduped

    def clear(self) -> None:
        self.save([])


_STORE: MeetingMemoryStore | None = None


def get_memory_store() -> MeetingMemoryStore:
    global _STORE
    if _STORE is None:
        _STORE = MeetingMemoryStore()
    return _STORE
