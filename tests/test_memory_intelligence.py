from pathlib import Path

from meetinglens_intelligence import action_accountability, decision_drift, recurring_blockers
from meetinglens_memory_store import MeetingMemoryStore, meeting_fingerprint


def sample_meetings():
    return [
        {
            "title": "Launch Weekly 1",
            "duration_min": 20,
            "segments": [{"text": "We will keep the Friday release.", "speaker": "Maya"}],
            "decisions": [{"title": "We will keep the Friday release", "detail": "Launch stays Friday"}],
            "actions": [{"task": "Validate analytics", "owner": "Omar", "due": "Tomorrow", "status": "Open"}],
            "risks": [{"title": "Analytics validation is blocking release", "severity": "High", "minute": 12}],
        },
        {
            "title": "Launch Weekly 2",
            "duration_min": 25,
            "segments": [{"text": "We changed the Friday release and will delay it.", "speaker": "Maya"}],
            "decisions": [{"title": "We changed the Friday release", "detail": "Delay the launch instead"}],
            "actions": [{"task": "Prepare revised rollout", "owner": "Unassigned", "due": "Not stated", "status": "Open"}],
            "risks": [{"title": "Analytics validation is still blocking the release", "severity": "High", "minute": 8}],
        },
    ]


def test_memory_store_upserts_and_persists(tmp_path: Path):
    path = tmp_path / "vault.json"
    store = MeetingMemoryStore(path)
    meetings = sample_meetings()
    vault, created = store.upsert(meetings[0])
    assert created is True
    assert len(vault) == 1
    assert store.load()[0]["meeting_id"] == meeting_fingerprint(meetings[0])

    vault, created = store.upsert(meetings[0])
    assert created is False
    assert len(vault) == 1

    vault, created = store.upsert(meetings[1])
    assert created is True
    assert len(store.load()) == 2


def test_decision_drift_finds_changed_decision():
    drift = decision_drift(sample_meetings())
    assert drift
    assert drift[0]["from_meeting"] == "Launch Weekly 1"
    assert drift[0]["to_meeting"] == "Launch Weekly 2"


def test_recurring_blockers_cluster_related_risks():
    blockers = recurring_blockers(sample_meetings())
    assert blockers
    assert blockers[0]["count"] == 2


def test_action_accountability_flags_missing_owner_and_deadline():
    rows = action_accountability(sample_meetings())
    attention = [row for row in rows if row["needs_attention"]]
    assert len(rows) == 2
    assert len(attention) == 1
    assert attention[0]["missing"] == "owner, deadline"
