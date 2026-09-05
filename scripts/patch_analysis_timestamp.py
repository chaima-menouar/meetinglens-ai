from pathlib import Path

path = Path("meetinglens_pipeline.py")
text = path.read_text(encoding="utf-8")

if "from datetime import datetime, timezone" not in text:
    text = text.replace(
        "from functools import lru_cache\n",
        "from functools import lru_cache\nfrom datetime import datetime, timezone\n",
        1,
    )

old = '''            "segments": segments,\n            "source": "audio",\n            "diarization_status": diarization_status,\n'''
new = '''            "segments": segments,\n            "source": "audio",\n            "analyzed_at": datetime.now(timezone.utc).isoformat(),\n            "diarization_status": diarization_status,\n'''
if '"analyzed_at": datetime.now(timezone.utc).isoformat()' not in text:
    if old not in text:
        raise SystemExit("Meeting payload marker not found")
    text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
print("Added analyzed_at timestamp to audio meeting payloads")
