from __future__ import annotations

import importlib.util
import os
import platform
import sys
from pathlib import Path
from typing import Any

from meetinglens_memory_store import get_memory_store

ROOT = Path(__file__).resolve().parent
RANKER_DIR = ROOT / "artifacts" / "meeting_candidate_rankers"


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def _secret_configured(name: str) -> bool:
    if os.getenv(name, "").strip():
        return True
    try:
        import streamlit as st
        return bool(str(st.secrets.get(name, "")).strip())
    except Exception:
        return False


def _file_state(path: Path) -> dict[str, Any]:
    exists = path.exists() and path.is_file()
    return {
        "ok": exists,
        "path": str(path.relative_to(ROOT)) if path.is_absolute() and ROOT in path.parents else str(path),
        "size_kb": round(path.stat().st_size / 1024, 1) if exists else 0.0,
    }


def collect_runtime_status(check_memory: bool = False) -> dict[str, Any]:
    """Collect safe production diagnostics without exposing credentials."""
    store = get_memory_store()
    decision_ranker = _file_state(RANKER_DIR / "decision_ranker.joblib")
    action_ranker = _file_state(RANKER_DIR / "action_ranker.joblib")
    metrics = _file_state(RANKER_DIR / "metrics.json")

    memory = {
        "ok": True,
        "backend": getattr(store, "backend", "unknown"),
        "workspace_id": getattr(store, "workspace_id", "default"),
        "detail": "Connection not tested yet.",
    }
    if check_memory:
        memory = store.healthcheck()

    pyannote_installed = _module_available("pyannote.audio")
    hf_configured = _secret_configured("HF_TOKEN")
    supabase_configured = getattr(store, "backend", "") == "supabase"

    return {
        "python": {
            "ok": sys.version_info >= (3, 11),
            "version": platform.python_version(),
            "platform": platform.platform(),
        },
        "transcription": {
            "ok": _module_available("faster_whisper"),
            "module": "faster_whisper",
            "detail": "Installed" if _module_available("faster_whisper") else "Not installed in this runtime",
        },
        "candidate_rankers": {
            "ok": decision_ranker["ok"] and action_ranker["ok"],
            "decision": decision_ranker,
            "action": action_ranker,
            "metrics": metrics,
        },
        "diarization": {
            "ok": pyannote_installed,
            "runtime_installed": pyannote_installed,
            "hf_token_configured": hf_configured,
            "detail": "Ready" if pyannote_installed and hf_configured else "Optional runtime/token incomplete",
        },
        "memory": memory,
        "supabase_configured": supabase_configured,
        "mode": "hosted-memory" if supabase_configured else "runtime-json-memory",
    }


def readiness_score(status: dict[str, Any]) -> int:
    checks = [
        bool(status.get("python", {}).get("ok")),
        bool(status.get("transcription", {}).get("ok")),
        bool(status.get("candidate_rankers", {}).get("ok")),
        bool(status.get("memory", {}).get("ok")),
    ]
    # Diarization is optional in the public deployment, so it does not reduce the core score.
    return round(sum(checks) / len(checks) * 100) if checks else 0
