# MeetingLens AI

**MeetingLens AI** is a conversation-intelligence product that turns meeting audio into timestamped evidence, speaker-aware transcripts, decisions, action items, risks, and cross-meeting organizational memory.

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
- Optional automatic speaker diarization
- Downloadable meeting JSON
- Add analyzed meetings to the in-session Memory Vault

### Automatic speaker diarization

MeetingLens now contains an optional diarization layer based on **pyannote Community-1**.

When enabled, the pipeline runs:

```text
audio
  |
  +--> faster-whisper --> timestamped transcript
  |
  +--> pyannote Community-1 --> speaker turns
                         |
                         v
              timestamp overlap alignment
                         |
                         v
             Speaker 1 / Speaker 2 / ...
                         |
                         v
           speaker-aware meeting intelligence
```

The diarization dependency is intentionally separated from the light public build because `pyannote.audio` and its ML runtime are much heavier than the standard Streamlit deployment.

For a local/worker environment:

```bash
pip install -r requirements-diarization.txt
```

Then configure `HF_TOKEN` either as an environment variable or in Streamlit Secrets. The Hugging Face account must also accept the usage conditions for `pyannote/speaker-diarization-community-1`.

The Analyze Audio page lets the user set minimum and maximum expected speakers. If diarization cannot run, transcription still succeeds and MeetingLens falls back to Speaker Review instead of failing the whole meeting analysis.

### Speaker review

Open **Speaker Review** to rename or correct speaker labels after transcription/diarization.

The review workflow automatically recomputes:

- speaking-time balance
- participant percentages
- action ownership
- decision / action / risk intelligence

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
    +--> faster-whisper -----------+
    |                              |
    +--> optional pyannote --------+--> aligned speaker transcript
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
                              One Streamlit product
```

## Files

```text
app.py                         main visual workspace
meetinglens_pipeline.py        transcription + extraction + diarization integration
meetinglens_diarization.py     pyannote speaker turns + Whisper timestamp alignment
meetinglens_intelligence.py    cross-meeting intelligence
requirements.txt               light/public application dependencies
requirements-diarization.txt   optional automatic diarization runtime
pages/1_Analyze_Audio.py       audio + automatic diarization workflow
pages/2_Memory_Intelligence.py organizational memory
pages/3_Speaker_Review.py      speaker correction + recomputation
```

## Run locally

Light version:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

With automatic diarization:

```bash
pip install -r requirements-diarization.txt
```

Then set `HF_TOKEN` before starting Streamlit.

The first run downloads the selected Whisper model and, when diarization is enabled, the pyannote model assets.

## Deploy

1. Open Streamlit Community Cloud.
2. Sign in with GitHub.
3. Create an app from `chaima-menouar/meetinglens-ai`.
4. Branch: `main`.
5. Main file: `app.py`.
6. Deploy.

The standard `requirements.txt` deliberately keeps the public build light. Automatic diarization is designed to run in the optional diarization profile/local worker until the heavier runtime is validated against the free Streamlit resource limits.

## Stack

- Python
- Streamlit
- faster-whisper
- pyannote.audio (optional diarization profile)
- Pandas
- Plotly
- VADER Sentiment
- GitHub
- Streamlit Community Cloud

## Current limitations

- English transcription only in the current workflow.
- Automatic diarization requires the optional pyannote runtime and Hugging Face access token/model terms.
- Decision/action/risk extraction is currently evidence-first heuristic extraction rather than a fine-tuned meeting-event model.
- Memory Vault persistence is portable JSON/session state, not a production database yet.

## Next model layer

The next research/model milestones are:

- validate diarization on AMI Meeting Corpus
- compute speaker diarization metrics
- trained meeting-event classifier
- semantic embeddings for cross-meeting retrieval
- stronger decision-reversal / drift model
- persistent meeting memory

---

**MeetingLens AI** — meeting audio → speakers → decisions → ownership → organizational memory.
