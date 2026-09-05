from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from meetinglens_pipeline import transcribe_audio


class LocalUpload:
    def __init__(self, path: Path):
        self.path = path
        self.name = path.name

    def getbuffer(self):
        return self.path.read_bytes()


def run_benchmark(
    audio_path: Path,
    model_size: str = "tiny.en",
    diarize: bool = False,
    hf_token: str = "",
    min_speakers: int | None = None,
    max_speakers: int | None = None,
) -> dict:
    started = time.perf_counter()
    meeting = transcribe_audio(
        LocalUpload(audio_path),
        model_size=model_size,
        diarize=diarize,
        hf_token=hf_token,
        min_speakers=min_speakers,
        max_speakers=max_speakers,
    )
    elapsed = time.perf_counter() - started
    diarization = meeting.get("diarization", {}) or {}
    return {
        "audio_file": audio_path.name,
        "audio_size_mb": round(audio_path.stat().st_size / 1024 / 1024, 2),
        "model_size": model_size,
        "diarization_requested": diarize,
        "elapsed_seconds": round(elapsed, 2),
        "duration_min": meeting.get("duration_min", 0),
        "segments": len(meeting.get("segments", [])),
        "speakers": len(meeting.get("participants", [])),
        "decisions": len(meeting.get("decisions", [])),
        "actions": len(meeting.get("actions", [])),
        "risks": len(meeting.get("risks", [])),
        "decision_candidates": len(meeting.get("decision_candidates", [])),
        "action_candidates": len(meeting.get("action_candidates", [])),
        "diarization_status": meeting.get("diarization_status"),
        "diarization_coverage_pct": diarization.get("coverage_pct"),
        "diarization_quality": diarization.get("quality"),
        "fallback_segments": diarization.get("fallback_segments"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark MeetingLens on one real meeting recording.")
    parser.add_argument("audio", type=Path)
    parser.add_argument("--model", default="tiny.en", choices=["tiny.en", "base.en"])
    parser.add_argument("--diarize", action="store_true")
    parser.add_argument("--hf-token", default="")
    parser.add_argument("--min-speakers", type=int, default=None)
    parser.add_argument("--max-speakers", type=int, default=None)
    parser.add_argument("--output", type=Path, default=Path("benchmark_result.json"))
    args = parser.parse_args()

    if not args.audio.exists():
        raise SystemExit(f"Audio file not found: {args.audio}")

    result = run_benchmark(
        args.audio,
        model_size=args.model,
        diarize=args.diarize,
        hf_token=args.hf_token,
        min_speakers=args.min_speakers,
        max_speakers=args.max_speakers,
    )
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"Saved benchmark report to {args.output}")


if __name__ == "__main__":
    main()
