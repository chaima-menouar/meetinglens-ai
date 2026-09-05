# MeetingLens AI

**MeetingLens AI** is a conversation-intelligence product that turns meeting audio into timestamped evidence, decisions, action items, risks, speaker-aware review, and cross-meeting organizational memory.

> From conversation to decisions that move.

## Current product

MeetingLens is deliberately shipped as **one Streamlit application** so the UI and intelligence workflow deploy together without a frontend/backend mismatch.

### Main workspace

- Premium animated meeting-intelligence interface
- Executive meeting overview
- Clarity / meeting-health signals
- Decision and risk visualization
- Action ownership
- Key-moment timeline
- Search inside the current meeting
- Sentiment and participation analytics

### Real audio analysis

Open **Analyze Audio** from the Streamlit page navigation.

- MP3 / WAV / M4A / MP4 / WEBM upload
- `faster-whisper` English transcription on CPU
- Voice-activity filtering and timestamps
- Segment sentiment
- Decision extraction with confidence and evidence timestamps
- Action extraction with owner and due-date detection
- Risk extraction and severity
- Downloadable meeting JSON
- Add analyzed meetings to the in-session Memory Vault

### Speaker review

Open **Speaker Review** to correct speaker labels after transcription.

The free deployment currently does **not** run a heavy automatic diarization model. Instead, the review workflow lets users assign speaker names to transcript turns and then automatically recomputes:

- speaking-time balance
- participant percentages
- action ownership
- decision / action / risk intelligence

This keeps the public deployment light while preserving speaker-aware downstream analytics.

### Cross-meeting intelligence

Open **Memory Intelligence** to analyze multiple meetings together.

- Import multiple MeetingLens JSON files
- Search evidence across all meetings
- Source meeting + timestamp in results
- Recurring blocker detection
- Decision Drift detection between earlier and later decisions
- Topic-frequency index
- Memory Vault import/export

The Memory Vault is session-based on Streamlit Community Cloud. Export the vault JSON to keep a portable copy across restarts.

## Architecture

```text
Meeting audio
    |
    v
faster-whisper
    |
    v
Timestamped transcript
    |
    +--> sentiment
    +--> decision extraction
    +--> action + due-date extraction
    +--> risk extraction
    |
    v
Meeting JSON
    |
    +--> Speaker Review
    |
    v
Memory Vault
    |
    +--> cross-meeting search
    +--> recurring blockers
    +--> Decision Drift
    +--> topic intelligence
    |
    v
One Streamlit deployment
```

## Files

```text
app.py                         main visual workspace
meetinglens_pipeline.py        transcription + meeting extraction
meetinglens_intelligence.py    cross-meeting intelligence
pages/1_Analyze_Audio.py       audio workflow
pages/2_Memory_Intelligence.py organizational memory
pages/3_Speaker_Review.py      speaker correction + recomputation
```

## Run locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The first run of audio transcription downloads the selected Whisper model.

## Deploy

1. Open Streamlit Community Cloud.
2. Sign in with GitHub.
3. Create an app from `chaima-menouar/meetinglens-ai`.
4. Branch: `main`.
5. Main file: `app.py`.
6. Deploy.

No Vercel deployment and no external API key are required for the current audio pipeline.

## Stack

- Python
- Streamlit
- faster-whisper
- Pandas
- Plotly
- VADER Sentiment
- GitHub
- Streamlit Community Cloud

## Current limitations

- English transcription only in the public workflow.
- Automatic multi-speaker diarization is not enabled on the free deployment yet.
- Decision/action/risk extraction is currently evidence-first heuristic extraction rather than a fine-tuned meeting-event model.
- Memory Vault persistence is portable JSON/session state, not a production database yet.

## Next model layer

The research/model track can now focus on the differentiators rather than UI plumbing:

- trained meeting-event classifier
- automatic diarization for local/GPU mode
- semantic embeddings for cross-meeting retrieval
- stronger decision-reversal / drift model
- AMI Meeting Corpus evaluation

---

**MeetingLens AI** — meeting audio → decisions → ownership → organizational memory.
