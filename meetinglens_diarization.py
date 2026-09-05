from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SpeakerTurn:
    start: float
    end: float
    speaker: str


def _normalize_speaker(label: str, index_map: dict[str, str]) -> str:
    if label not in index_map:
        index_map[label] = f"Speaker {len(index_map) + 1}"
    return index_map[label]


def diarize_audio_file(
    audio_path: str,
    hf_token: str,
    min_speakers: int | None = None,
    max_speakers: int | None = None,
) -> list[SpeakerTurn]:
    """Run pyannote Community-1 diarization and return normalized speaker turns.

    pyannote.audio is imported lazily so the public Streamlit build can stay light.
    Install requirements-diarization.txt only in environments where automatic
    diarization is enabled.
    """
    if not hf_token:
        raise RuntimeError("A Hugging Face token is required for automatic speaker diarization.")

    try:
        from pyannote.audio import Pipeline
    except Exception as exc:  # pragma: no cover - optional deployment dependency
        raise RuntimeError(
            "Automatic diarization is not installed in this environment. "
            "Install requirements-diarization.txt first."
        ) from exc

    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-community-1",
            token=hf_token,
        )
    except Exception as exc:
        raise RuntimeError(
            "Could not load the pyannote Community-1 model. Check the Hugging Face token "
            "and confirm that the model usage conditions were accepted."
        ) from exc

    kwargs: dict[str, Any] = {}
    if min_speakers is not None:
        kwargs["min_speakers"] = int(min_speakers)
    if max_speakers is not None:
        kwargs["max_speakers"] = int(max_speakers)

    output = pipeline(audio_path, **kwargs)
    annotation = getattr(output, "exclusive_speaker_diarization", None)
    if annotation is None:
        annotation = getattr(output, "speaker_diarization", output)

    raw_turns: list[tuple[float, float, str]] = []
    try:
        iterator = annotation.itertracks(yield_label=True)
        for turn, _, label in iterator:
            raw_turns.append((float(turn.start), float(turn.end), str(label)))
    except AttributeError:
        for turn, label in annotation:
            raw_turns.append((float(turn.start), float(turn.end), str(label)))

    labels: dict[str, str] = {}
    return [
        SpeakerTurn(start=start, end=end, speaker=_normalize_speaker(label, labels))
        for start, end, label in sorted(raw_turns, key=lambda item: (item[0], item[1]))
        if end > start
    ]


def _overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def assign_speakers_to_segments(
    segments: list[dict[str, Any]],
    turns: list[SpeakerTurn],
) -> list[dict[str, Any]]:
    """Assign each transcript segment to the speaker with the most time overlap."""
    if not turns:
        return segments

    for segment in segments:
        start = float(segment.get("start_sec", 0.0))
        end = float(segment.get("end_sec", start))
        if end <= start:
            end = start + 0.2

        scores: dict[str, float] = {}
        for turn in turns:
            if turn.end < start or turn.start > end:
                continue
            amount = _overlap(start, end, turn.start, turn.end)
            if amount > 0:
                scores[turn.speaker] = scores.get(turn.speaker, 0.0) + amount

        segment_duration = max(0.2, end - start)
        if scores:
            speaker, overlap = max(scores.items(), key=lambda item: item[1])
            segment["speaker"] = speaker
            segment["speaker_overlap_ratio"] = round(min(1.0, overlap / segment_duration), 3)
            segment["speaker_assignment"] = "overlap"
            continue

        midpoint = (start + end) / 2
        nearest = min(
            turns,
            key=lambda turn: min(abs(midpoint - turn.start), abs(midpoint - turn.end)),
        )
        segment["speaker"] = nearest.speaker
        segment["speaker_overlap_ratio"] = 0.0
        segment["speaker_assignment"] = "nearest"

    return segments


def diarization_diagnostics(
    segments: list[dict[str, Any]],
    turns: list[SpeakerTurn],
) -> dict[str, Any]:
    speakers = sorted({turn.speaker for turn in turns})
    total_segment_time = 0.0
    overlap_weighted = 0.0
    fallback_segments = 0

    for segment in segments:
        start = float(segment.get("start_sec", 0.0))
        end = float(segment.get("end_sec", start))
        duration = max(0.2, end - start)
        ratio = float(segment.get("speaker_overlap_ratio", 0.0) or 0.0)
        total_segment_time += duration
        overlap_weighted += duration * ratio
        if segment.get("speaker_assignment") == "nearest":
            fallback_segments += 1

    coverage = overlap_weighted / total_segment_time if total_segment_time else 0.0
    if coverage >= 0.82 and fallback_segments <= max(1, len(segments) // 10):
        quality = "high"
    elif coverage >= 0.6:
        quality = "medium"
    else:
        quality = "review"

    return {
        "speaker_count": len(speakers),
        "speakers": speakers,
        "turn_count": len(turns),
        "coverage_pct": round(coverage * 100),
        "fallback_segments": fallback_segments,
        "quality": quality,
    }
