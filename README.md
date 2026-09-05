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

MeetingLens contains an optional diarization layer based on **pyannote Community-1**.

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

Install the optional runtime locally/worker-side:

```bash
pip install -r requirements-diarization.txt
```

Then configure `HF_TOKEN` in the environment or Streamlit Secrets. If diarization cannot run, transcription remains usable and MeetingLens falls back to Speaker Review.

### Diarization quality diagnostics

Automatic diarization is not accepted blindly. MeetingLens records:

- number of detected speakers
- number of diarization turns
- transcript coverage by real speaker overlap
- nearest-turn fallbacks
- quality state: high / medium / review

Low-quality diarization is routed to Speaker Review rather than silently treated as ground truth.

### Speaker review

Open **Speaker Review** to rename or correct speaker labels after transcription/diarization. The review recomputes speaking balance, participant percentages, action ownership, and meeting-event intelligence.

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

## AMI meeting-event training track

The product now includes a reproducible training path based on the **AMI Meeting Corpus manual annotations**. The official corpus provides manual NXT/XML transcripts, dialogue acts, summaries, and decision-related annotations under CC BY 4.0.

Install training dependencies:

```bash
pip install -r requirements-training.txt
```

Run the complete pipeline:

```bash
python -m training.run_ami_training
```

That command performs:

```text
official AMI manual annotations
          |
          v
NXT/XML parser + dialogue-act references
          |
          v
MeetingLens event labels
 decision / action / risk / other
          |
          v
meeting-level train/test split
          |
          v
TF-IDF word + character features
          |
          v
balanced Logistic Regression baseline
          |
          v
metrics.json + predictions + model.joblib
```

Generated data and model artifacts are intentionally ignored by Git. This prevents the public repository from shipping corpus data or large local model files.

The baseline uses a **meeting-level split**, not a random utterance split, so transcript fragments from the same meeting cannot leak into both train and test sets.

Current label construction is evidence-first:

- AMI decision references and decision-like dialogue acts → `decision`
- commit/directive/suggestion-like dialogue acts → `action`
- lexical blocker/problem signals → weak `risk` labels
- remaining dialogue acts → `other`

This baseline is a benchmark, not the final classifier. Its purpose is to give us a measurable macro-F1 target before moving to a transformer model or richer context-window classifier.

## Trained model integration

`meetinglens_event_model.py` is already prepared to load a trained artifact from:

```text
artifacts/meeting_event_baseline/meeting_event_baseline.joblib
```

or from a custom path set with:

```text
MEETINGLENS_EVENT_MODEL=/path/to/model.joblib
```

The current public app keeps the heuristic extractor active until a trained artifact has been evaluated and approved.

## Architecture

```text
Meeting audio
    |
    +--> faster-whisper -----------+
    |                              |
    +--> optional pyannote --------+--> aligned speaker transcript
                                      |
                                      +--> sentiment
                                      +--> meeting-event model / fallback extraction
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
```

## Important files

```text
app.py                          main visual workspace
meetinglens_pipeline.py         transcription + extraction + diarization integration
meetinglens_diarization.py      pyannote speaker turns + Whisper alignment
meetinglens_event_model.py      trained event-model loader
meetinglens_intelligence.py     cross-meeting intelligence
training/download_ami.py        official AMI annotation downloader
training/ami_dataset.py         NXT/XML -> labeled examples
training/train_baseline.py      leakage-safe baseline training + evaluation
training/run_ami_training.py    end-to-end training command
requirements.txt                light/public application dependencies
requirements-diarization.txt    optional automatic diarization runtime
requirements-training.txt       training dependencies
pages/1_Analyze_Audio.py        audio + automatic diarization workflow
pages/2_Memory_Intelligence.py  organizational memory
pages/3_Speaker_Review.py       speaker correction + recomputation
```

## Run locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy

1. Open Streamlit Community Cloud.
2. Sign in with GitHub.
3. Create an app from `chaima-menouar/meetinglens-ai`.
4. Branch: `main`.
5. Main file: `app.py`.
6. Deploy.

The public `requirements.txt` deliberately stays light. Automatic diarization and model training use separate dependency profiles.

## Stack

- Python
- Streamlit
- faster-whisper
- pyannote.audio
- scikit-learn
- Pandas
- Plotly
- VADER Sentiment
- GitHub Actions
- Streamlit Community Cloud

## Current limitations

- English transcription only in the current workflow.
- Automatic diarization requires the optional pyannote runtime and Hugging Face access.
- The AMI-trained baseline still needs to be executed and evaluated on the downloaded corpus before replacing heuristic extraction.
- `risk` labels are currently weakly supervised because AMI's strongest released annotations focus more directly on dialogue acts and decision discussion.
- Memory Vault persistence is portable JSON/session state, not a production database yet.

## Next research milestones

- execute AMI dataset build and baseline training
- inspect label balance and annotation mapping
- establish macro-F1 / per-class precision-recall benchmark
- compare transformer/context-window model against baseline
- activate trained classifier only if it improves validation performance
- semantic embeddings for cross-meeting retrieval
- stronger Decision Drift model
- persistent meeting memory

---

**MeetingLens AI** — meeting audio → speakers → decisions → ownership → organizational memory.
