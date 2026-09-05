from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_STORE_PATH = "data/runtime/meeting_vault.json"
DEFAULT_SUPABASE_TABLE = "meetinglens_meetings"


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


def _dedupe(meetings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for meeting in meetings:
        if not isinstance(meeting, dict):
            continue
        item = prepare_meeting(meeting)
        if item["meeting_id"] in seen:
            continue
        seen.add(item["meeting_id"])
        output.append(item)
    return output


class MeetingMemoryStore:
    """JSON runtime backend used when no hosted store is configured."""

    backend = "runtime-json"

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
        payload = {"version": 1, "meetings": _dedupe(meetings)}
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
                return self.load(), False
        meetings.append(item)
        self.save(meetings)
        return self.load(), True

    def replace_all(self, meetings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self.save(_dedupe(meetings))
        return self.load()

    def clear(self) -> None:
        self.save([])

    def healthcheck(self) -> dict[str, Any]:
        try:
            meetings = self.load()
            self.path.parent.mkdir(parents=True, exist_ok=True)
            return {
                "ok": True,
                "backend": self.backend,
                "meeting_count": len(meetings),
                "detail": "Runtime JSON store is readable.",
            }
        except Exception as exc:
            return {"ok": False, "backend": self.backend, "meeting_count": 0, "detail": str(exc)}


class SupabaseMeetingMemoryStore:
    """Hosted Memory Vault through the Supabase REST API.

    Requires a private server-side key and the schema in `supabase_schema.sql`.
    The app never sends the key to the browser; all requests execute server-side.
    """

    backend = "supabase"

    def __init__(self, url: str, key: str, table: str = DEFAULT_SUPABASE_TABLE):
        self.url = url.rstrip("/")
        self.key = key.strip()
        self.table = table.strip() or DEFAULT_SUPABASE_TABLE
        if not self.url or not self.key:
            raise ValueError("Supabase URL and key are required")

    @property
    def endpoint(self) -> str:
        return f"{self.url}/rest/v1/{self.table}"

    def _request(self, method: str, query: dict[str, str] | None = None, payload: Any = None, prefer: str | None = None) -> Any:
        url = self.endpoint
        if query:
            url += "?" + urlencode(query, safe="(),.*")
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=15) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except (HTTPError, URLError) as exc:
            detail = ""
            if isinstance(exc, HTTPError):
                try:
                    detail = exc.read().decode("utf-8")
                except Exception:
                    detail = ""
            raise RuntimeError(f"Supabase Memory Vault request failed: {exc}. {detail}".strip()) from exc

    def load(self) -> list[dict[str, Any]]:
        rows = self._request("GET", {"select": "payload", "order": "saved_at.asc"}) or []
        return [row.get("payload") for row in rows if isinstance(row, dict) and isinstance(row.get("payload"), dict)]

    def upsert(self, meeting: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
        item = prepare_meeting(meeting)
        existing = {m.get("meeting_id") for m in self.load()}
        row = {"meeting_id": item["meeting_id"], "saved_at": item["saved_at"], "payload": item}
        self._request("POST", {"on_conflict": "meeting_id"}, [row], "resolution=merge-duplicates,return=minimal")
        return self.load(), item["meeting_id"] not in existing

    def replace_all(self, meetings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        items = _dedupe(meetings)
        if items:
            rows = [{"meeting_id": m["meeting_id"], "saved_at": m["saved_at"], "payload": m} for m in items]
            self._request("POST", {"on_conflict": "meeting_id"}, rows, "resolution=merge-duplicates,return=minimal")
        return self.load()

    def clear(self) -> None:
        self._request("DELETE", {"meeting_id": "not.is.null"}, prefer="return=minimal")

    def healthcheck(self) -> dict[str, Any]:
        try:
            rows = self._request("GET", {"select": "meeting_id", "limit": "1"}) or []
            return {
                "ok": True,
                "backend": self.backend,
                "meeting_count": None,
                "detail": f"Supabase table '{self.table}' is reachable.",
                "sample_rows": len(rows),
            }
        except Exception as exc:
            return {
                "ok": False,
                "backend": self.backend,
                "meeting_count": None,
                "detail": str(exc),
                "sample_rows": 0,
            }


_STORE: MeetingMemoryStore | SupabaseMeetingMemoryStore | None = None
_STORE_KEY: tuple[str, str, str] | None = None


def _streamlit_secret(name: str) -> str:
    try:
        import streamlit as st
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def get_memory_store(
    supabase_url: str | None = None,
    supabase_key: str | None = None,
    supabase_table: str | None = None,
) -> MeetingMemoryStore | SupabaseMeetingMemoryStore:
    global _STORE, _STORE_KEY
    url = (supabase_url or os.getenv("SUPABASE_URL", "") or _streamlit_secret("SUPABASE_URL")).strip()
    key = (
        supabase_key
        or os.getenv("SUPABASE_SERVICE_KEY", "")
        or os.getenv("SUPABASE_KEY", "")
        or _streamlit_secret("SUPABASE_SERVICE_KEY")
        or _streamlit_secret("SUPABASE_KEY")
    ).strip()
    table = (
        supabase_table
        or os.getenv("SUPABASE_TABLE", "")
        or _streamlit_secret("SUPABASE_TABLE")
        or DEFAULT_SUPABASE_TABLE
    ).strip()
    store_key = (url, key, table)
    if _STORE is not None and _STORE_KEY == store_key:
        return _STORE
    _STORE_KEY = store_key
    _STORE = SupabaseMeetingMemoryStore(url, key, table) if url and key else MeetingMemoryStore()
    return _STORE
