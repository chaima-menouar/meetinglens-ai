# MeetingLens AI

**MeetingLens AI** is a modern conversation-intelligence workspace that turns meeting transcripts into decisions, action items, risks, speaker insights, sentiment, and searchable knowledge.

> From conversation to clarity.

## Current version

The first public MVP is deliberately packaged as **one Streamlit application**. The interface and the lightweight analysis logic run from the same `app.py`, which avoids frontend/backend deployment mismatch and makes the project easy to run for free on Streamlit Community Cloud.

### Included now

- Premium dark meeting-intelligence UI
- Animated audio waveform and live AI status
- Executive overview dashboard
- Meeting Health score
- Speaker balance analytics
- Decisions and AI confidence
- Action items with owners and deadlines
- Risk tracking
- Transcript/key-moment timeline
- VADER sentiment analysis
- Search inside meeting memory
- JSON meeting upload
- Responsive layout
- Demo meeting data built into the app

## Architecture

```text
Meeting JSON / demo meeting
          |
          v
     Streamlit app.py
      /    |     \
     /     |      \
  UI   Analytics   Search
     \     |      /
      \    |     /
       One deployment
          |
          v
Streamlit Community Cloud
```

There is no separate frontend server and backend server in this MVP.

## Run locally

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy for free

1. Open Streamlit Community Cloud.
2. Sign in with GitHub.
3. Create a new app.
4. Select repository `chaima-menouar/meetinglens-ai`.
5. Select branch `main`.
6. Set the main file path to `app.py`.
7. Deploy.

No Vercel setup is required.

## Meeting JSON format

```json
{
  "title": "Meeting title",
  "duration_min": 45,
  "summary": "Short executive summary",
  "participants": [{"name": "Maya", "talk_pct": 50}],
  "segments": [{"minute": 3, "speaker": "Maya", "kind": "decision", "text": "..."}],
  "decisions": [],
  "actions": [],
  "risks": []
}
```

## Next milestones

The next layer will add real AMI audio ingestion, local/faster-whisper transcription, speaker diarization, DuckDB multi-meeting memory, semantic search, and a custom meeting-event classifier. Heavy transcription will be kept outside the free public app when needed so the Streamlit deployment stays stable.

## Stack

- Python
- Streamlit
- Plotly
- Pandas
- VADER Sentiment
- GitHub
- Streamlit Community Cloud

---

**MeetingLens AI** — conversation intelligence for decisions, follow-through, and organizational memory.
