from meetinglens_review import confirm_candidate, reject_candidate, review_stats


def meeting():
    return {
        "title": "Review Test",
        "decisions": [],
        "actions": [],
        "decision_candidates": [
            {"rank": 1, "score": 0.81, "text": "We should keep Friday.", "speaker": "Maya", "timestamp": "12:10", "minute": 12}
        ],
        "action_candidates": [
            {"rank": 1, "score": 0.77, "text": "I can validate analytics.", "speaker": "Omar", "timestamp": "18:30", "minute": 18}
        ],
    }


def test_confirm_decision_promotes_and_removes_candidate():
    source = meeting()
    candidate = source["decision_candidates"][0]
    updated = confirm_candidate(source, "decision", candidate)
    assert len(updated["decisions"]) == 1
    assert updated["decisions"][0]["signal_source"] == "human-confirmed-ranker"
    assert updated["decision_candidates"] == []
    assert source["decisions"] == []
    assert review_stats(updated)["confirmed"] == 1


def test_confirm_action_uses_speaker_as_owner():
    source = meeting()
    candidate = source["action_candidates"][0]
    updated = confirm_candidate(source, "action", candidate)
    assert updated["actions"][0]["owner"] == "Omar"
    assert updated["actions"][0]["status"] == "Open"
    assert updated["action_candidates"] == []


def test_reject_removes_candidate_without_confirming():
    source = meeting()
    candidate = source["decision_candidates"][0]
    updated = reject_candidate(source, "decision", candidate)
    assert updated["decision_candidates"] == []
    assert updated["decisions"] == []
    assert review_stats(updated)["rejected"] == 1
