from meetinglens_memory_store import SupabaseMeetingMemoryStore


def sample_meeting():
    return {
        "title": "Supabase Test",
        "duration_min": 12,
        "segments": [{"text": "We will ship Friday."}],
        "decisions": [],
        "actions": [],
        "risks": [],
    }


def test_supabase_healthcheck_does_not_expose_secret(monkeypatch):
    store = SupabaseMeetingMemoryStore("https://example.supabase.co", "super-secret-key", workspace_id="team-a")

    def fake_request(method, query=None, payload=None, prefer=None):
        assert method == "GET"
        assert query == {"select": "meeting_id", "limit": "1", "workspace_id": "eq.team-a"}
        return [{"meeting_id": "abc"}]

    monkeypatch.setattr(store, "_request", fake_request)
    status = store.healthcheck()
    assert status["ok"] is True
    assert status["backend"] == "supabase"
    assert status["workspace_id"] == "team-a"
    assert "super-secret-key" not in str(status)


def test_supabase_upsert_uses_workspace_conflict(monkeypatch):
    store = SupabaseMeetingMemoryStore("https://example.supabase.co", "key", workspace_id="team-a")
    calls = []
    loaded = []

    def fake_request(method, query=None, payload=None, prefer=None):
        calls.append((method, query, payload, prefer))
        if method == "GET":
            assert query.get("workspace_id") == "eq.team-a"
            return [{"payload": item} for item in loaded]
        if method == "POST":
            assert all(row["workspace_id"] == "team-a" for row in payload)
            loaded.clear()
            loaded.extend(row["payload"] for row in payload)
            return None
        raise AssertionError(method)

    monkeypatch.setattr(store, "_request", fake_request)
    meetings, created = store.upsert(sample_meeting())
    assert created is True
    assert len(meetings) == 1
    post = [call for call in calls if call[0] == "POST"][0]
    assert post[1] == {"on_conflict": "workspace_id,meeting_id"}
    assert "resolution=merge-duplicates" in post[3]


def test_supabase_replace_all_dedupes(monkeypatch):
    store = SupabaseMeetingMemoryStore("https://example.supabase.co", "key", workspace_id="team-b")
    stored = []

    def fake_request(method, query=None, payload=None, prefer=None):
        if method == "POST":
            assert all(row["workspace_id"] == "team-b" for row in payload)
            stored.clear()
            stored.extend(row["payload"] for row in payload)
            return None
        if method == "GET":
            assert query.get("workspace_id") == "eq.team-b"
            return [{"payload": item} for item in stored]
        raise AssertionError(method)

    monkeypatch.setattr(store, "_request", fake_request)
    output = store.replace_all([sample_meeting(), sample_meeting()])
    assert len(output) == 1


def test_supabase_clear_is_scoped_to_workspace(monkeypatch):
    store = SupabaseMeetingMemoryStore("https://example.supabase.co", "key", workspace_id="team-c")
    calls = []

    def fake_request(method, query=None, payload=None, prefer=None):
        calls.append((method, query, prefer))
        return None

    monkeypatch.setattr(store, "_request", fake_request)
    store.clear()
    assert calls == [("DELETE", {"workspace_id": "eq.team-c"}, "return=minimal")]
