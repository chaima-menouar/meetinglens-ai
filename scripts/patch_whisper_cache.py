from pathlib import Path

path = Path("meetinglens_pipeline.py")
text = path.read_text(encoding="utf-8")
if "from functools import lru_cache" not in text:
    text = text.replace("from __future__ import annotations\n\n", "from __future__ import annotations\n\nfrom functools import lru_cache\n", 1)

marker = "\ndef transcribe_audio(\n"
loader = '''\n@lru_cache(maxsize=2)\ndef _get_whisper_model(model_size: str):\n    try:\n        from faster_whisper import WhisperModel\n    except Exception as exc:\n        raise RuntimeError(\"Audio transcription is unavailable because faster-whisper could not be loaded.\") from exc\n    return WhisperModel(model_size, device=\"cpu\", compute_type=\"int8\")\n\n\n'''
if "def _get_whisper_model(" not in text:
    if marker not in text:
        raise SystemExit("transcribe_audio marker not found")
    text = text.replace(marker, loader + "def transcribe_audio(\n", 1)

old_import = '''    try:\n        from faster_whisper import WhisperModel\n    except Exception as exc:\n        raise RuntimeError(\"Audio transcription is unavailable because faster-whisper could not be loaded.\") from exc\n\n'''
text = text.replace(old_import, "", 1)
text = text.replace('        model = WhisperModel(model_size, device="cpu", compute_type="int8")\n', '        model = _get_whisper_model(model_size)\n', 1)
path.write_text(text, encoding="utf-8")
print("Whisper model cache patch applied")
