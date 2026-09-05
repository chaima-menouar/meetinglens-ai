from pathlib import Path

from meetinglens_diagnostics import collect_runtime_status, readiness_score
from meetinglens_memory_store import MeetingMemoryStore


def test_runtime_json_healthcheck_is_safe(tmp_path: Path):
    store = MeetingMemoryStore(tmp_path / "vault.json")
    status = store.healthcheck()
    assert status["ok"] is True
    assert status["backend"] == "runtime-json"
    assert "key" not in str(status).lower()


def test_diagnostics_has_core_sections():
    status = collect_runtime_status(check_memory=False)
    assert {"python", "transcription", "candidate_rankers", "diarization", "memory", "mode"}.issubset(status)
    assert 0 <= readiness_score(status) <= 100
    assert "SUPABASE_SERVICE_KEY" not in str(status)
    assert "HF_TOKEN" not in str(status)


def test_promoted_ranker_files_are_detected():
    status = collect_runtime_status(check_memory=False)
    rankers = status["candidate_rankers"]
    assert rankers["decision"]["ok"] is True
    assert rankers["action"]["ok"] is True
    assert rankers["metrics"]["ok"] is True
