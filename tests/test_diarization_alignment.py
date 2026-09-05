from meetinglens_diarization import (
    SpeakerTurn,
    assign_speakers_to_segments,
    diarization_diagnostics,
)


def test_assigns_speaker_with_largest_overlap():
    segments = [
        {"start_sec": 0.0, "end_sec": 4.0, "speaker": "Speaker 1", "text": "first"},
        {"start_sec": 4.0, "end_sec": 8.0, "speaker": "Speaker 1", "text": "second"},
    ]
    turns = [
        SpeakerTurn(0.0, 3.6, "Speaker 1"),
        SpeakerTurn(3.6, 8.0, "Speaker 2"),
    ]

    result = assign_speakers_to_segments(segments, turns)

    assert result[0]["speaker"] == "Speaker 1"
    assert result[1]["speaker"] == "Speaker 2"
    assert result[0]["speaker_assignment"] == "overlap"
    assert result[1]["speaker_assignment"] == "overlap"
    assert result[0]["speaker_overlap_ratio"] > 0.8


def test_uses_nearest_turn_when_segment_has_no_overlap():
    segments = [
        {"start_sec": 5.0, "end_sec": 5.4, "speaker": "Speaker 1", "text": "gap"},
    ]
    turns = [
        SpeakerTurn(0.0, 2.0, "Speaker 1"),
        SpeakerTurn(6.0, 9.0, "Speaker 2"),
    ]

    result = assign_speakers_to_segments(segments, turns)

    assert result[0]["speaker"] == "Speaker 2"
    assert result[0]["speaker_assignment"] == "nearest"
    assert result[0]["speaker_overlap_ratio"] == 0.0


def test_keeps_segments_when_no_diarization_turns_exist():
    segments = [
        {"start_sec": 0.0, "end_sec": 2.0, "speaker": "Speaker 1", "text": "hello"},
    ]

    result = assign_speakers_to_segments(segments, [])

    assert result[0]["speaker"] == "Speaker 1"


def test_diagnostics_mark_high_quality_alignment():
    segments = [
        {"start_sec": 0.0, "end_sec": 4.0, "speaker": "Speaker 1"},
        {"start_sec": 4.0, "end_sec": 8.0, "speaker": "Speaker 1"},
    ]
    turns = [
        SpeakerTurn(0.0, 4.0, "Speaker 1"),
        SpeakerTurn(4.0, 8.0, "Speaker 2"),
    ]

    aligned = assign_speakers_to_segments(segments, turns)
    meta = diarization_diagnostics(aligned, turns)

    assert meta["speaker_count"] == 2
    assert meta["coverage_pct"] == 100
    assert meta["fallback_segments"] == 0
    assert meta["quality"] == "high"


def test_diagnostics_recommend_review_for_gap_heavy_alignment():
    segments = [
        {"start_sec": 10.0, "end_sec": 12.0, "speaker": "Speaker 1"},
        {"start_sec": 20.0, "end_sec": 22.0, "speaker": "Speaker 1"},
    ]
    turns = [SpeakerTurn(0.0, 2.0, "Speaker 1")]

    aligned = assign_speakers_to_segments(segments, turns)
    meta = diarization_diagnostics(aligned, turns)

    assert meta["coverage_pct"] == 0
    assert meta["fallback_segments"] == 2
    assert meta["quality"] == "review"
