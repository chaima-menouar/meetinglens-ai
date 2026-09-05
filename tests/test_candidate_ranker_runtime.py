from meetinglens_candidate_ranker import MeetingCandidateRankers
from meetinglens_pipeline import refresh_intelligence


def _segments():
    return [
        {
            "id": 1,
            "speaker": "Maya",
            "timestamp": "00:03",
            "minute": 0,
            "start_sec": 3.0,
            "end_sec": 7.0,
            "text": "The customer feedback from last week was mostly positive.",
        },
        {
            "id": 2,
            "speaker": "Noah",
            "timestamp": "00:12",
            "minute": 0,
            "start_sec": 12.0,
            "end_sec": 17.0,
            "text": "We decided to keep the enterprise launch on Friday.",
        },
        {
            "id": 3,
            "speaker": "Lina",
            "timestamp": "00:21",
            "minute": 0,
            "start_sec": 21.0,
            "end_sec": 26.0,
            "text": "I will send the revised rollout checklist tomorrow.",
        },
        {
            "id": 4,
            "speaker": "Omar",
            "timestamp": "00:29",
            "minute": 0,
            "start_sec": 29.0,
            "end_sec": 34.0,
            "text": "The analytics dependency may delay the final dashboard.",
        },
    ]


def test_promoted_rankers_load_and_rank_real_artifacts():
    rankers = MeetingCandidateRankers()
    assert rankers.complete, rankers.errors
    assert not rankers.errors

    decision = rankers.rank_segments(_segments(), "decision", top_k=4)
    action = rankers.rank_segments(_segments(), "action", top_k=4)

    assert len(decision) == 4
    assert len(action) == 4
    assert [row["rank"] for row in decision] == [1, 2, 3, 4]
    assert [row["rank"] for row in action] == [1, 2, 3, 4]
    assert all(decision[i]["score"] >= decision[i + 1]["score"] for i in range(3))
    assert all(action[i]["score"] >= action[i + 1]["score"] for i in range(3))


def test_pipeline_uses_rankers_as_review_first_candidates():
    meeting = {"segments": _segments()}
    enriched = refresh_intelligence(meeting)

    assert enriched["candidate_ranking"]["available"] is True
    assert enriched["candidate_ranking"]["mode"] == "review-first"
    assert enriched["candidate_ranking"]["decision_candidates_ranked"] == 4
    assert enriched["candidate_ranking"]["action_candidates_ranked"] == 4

    assert any("enterprise launch" in row["title"] for row in enriched["decisions"])
    assert any("rollout checklist" in row["task"] for row in enriched["actions"])
    assert any("analytics dependency" in row["title"] for row in enriched["risks"])

    assert all(row["status"] == "Needs review" for row in enriched["decision_candidates"])
    assert all(row["status"] == "Needs review" for row in enriched["action_candidates"])
