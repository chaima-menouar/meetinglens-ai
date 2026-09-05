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
    store = SupabaseMeetingMemoryStore("https://example.supabase.co", "super-secret-key")

    def fake_request(method, query=None, payload=None, prefer=None):
        assert method == "GET"
        assert query == {"select": "meeting_id", "limit": "1"}
        return [{"meeting_id": "abc"}]

    monkeypatch.setattr(store, "_request", fake_request)
    status = store.healthcheck()
    assert status["ok"] is True
    assert status["backend"] == "supabase"
    assert "super-secret-key" not in str(status)


def test_supabase_upsert_uses_meeting_id_conflict(monkeypatch):
    store = SupabaseMeetingMemoryStore("https://example.supabase.co", "key")
    calls = []
    loaded = []

    def fake_request(method, query=None, payload=None, prefer=None):
        calls.append((method, query, payload, prefer))
        if method == "GET":
            return [{"payload": item} for item in loaded]
        if method == "POST":
            loaded.clear()
            loaded.extend(row["payload"] for row in payload)
            return None
        raise AssertionError(method)

    monkeypatch.setattr(store, "_request", fake_request)
    meetings, created = store.upsert(sample_meeting())
    assert created is True
    assert len(meetings) == 1
    post = [call for call in calls if call[0] == "POST"][0]
    assert post[1] == {"on_conflict": "meeting_id"}
    assert "resolution=merge-duplicates" in post[3]


def test_supabase_replace_all_dedupes(monkeypatch):
    store = SupabaseMeetingMemoryStore("https://example.supabase.co", "key")
    stored = []

    def fake_request(method, query=None, payload=None, prefer=None):
        if method == "POST":
            stored.clear()
            stored.extend(row["payload"] for row in payload)
            return None
        if method == "GET":
            return [{"payload": item} for item in stored]
        raise AssertionError(method)

    monkeypatch.setattr(store, "_request", fake_request)
    output = store.replace_all([sample_meeting(), sample_meeting()])
    assert len(output) == 1
