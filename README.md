# MeetingLens AI

**MeetingLens AI** turns meeting audio into timestamped evidence, speaker-aware transcripts, decisions, action items, risks, and cross-meeting organizational memory.

> From conversation to decisions that move.

## Current product

MeetingLens ships as **one Streamlit application** so transcription, intelligence, review, memory, and the executive workspace deploy together.

```text
Meeting audio
    |
    +--> faster-whisper -------------------------+
    |                                            |
    +--> optional pyannote diarization ----------+--> aligned transcript
                                                     |
                                                     +--> sentiment
                                                     +--> high-precision rules
                                                     +--> AMI-trained candidate ranking
                                                     +--> owner + due-date extraction
                                                     +--> risk signals
                                                     |
                                                     v
                                                 Meeting JSON
                                                     |
              +----------------------+--------------+------------------+
              |                      |                                 |
              v                      v                                 v
        Main dashboard         Speaker Review                    AI Review Queue
                                                                       |
                                                                       v
                                                               confirmed memory
                                                                       |
                                                                       v
                                                                  Memory Vault
                                                                       |
                             +----------------+-------------------------+----------------+
                             |                |                         |                |
                             v                v                         v                v
                        hybrid search   recurring blockers        Decision Drift   execution tracking
```

## Main workspace

- Executive meeting overview
- Clarity / meeting-health signals
- Decisions, risks, ownership, and key moments
- AI candidate-review preview
- Search inside the current meeting
- Sentiment and participation analytics
- Direct handoff from analyzed audio or a stored meeting

The dashboard uses the meeting selected/analyzed in the current session rather than forcing the built-in demo.

## Real audio analysis

Open **Analyze Audio** from the Streamlit navigation.

- MP3 / WAV / M4A / MP4 / WEBM / MPEG upload
- `faster-whisper` English transcription on CPU
- VAD + timestamps
- cached Whisper model instances to avoid reloading the model on every analysis
- segment sentiment
- Decision extraction with timestamped evidence
- Action extraction with owner and due-date detection
- Risk extraction and severity
- optional automatic speaker diarization
- AMI-trained Decision/Action candidate ranking
- save to Memory Vault
- open directly in the full dashboard
- download meeting JSON

The Streamlit upload limit is capped at **100 MB** for the free deployment.

## Automatic speaker diarization

MeetingLens contains an optional diarization layer based on **pyannote Community-1**.

```text
audio
  +--> faster-whisper --> timestamped transcript
  +--> pyannote -------> speaker turns
                              |
                              v
                    timestamp overlap alignment
                              |
                              v
                   Speaker 1 / Speaker 2 / ...
```

Install the optional runtime locally or on a dedicated worker:

```bash
pip install -r requirements-diarization.txt
```

Configure `HF_TOKEN` in the environment or Streamlit Secrets. If diarization cannot run, transcription remains usable and MeetingLens routes speaker labels to **Speaker Review**.

### Diarization quality diagnostics

MeetingLens records detected speakers, speaker turns, direct-overlap coverage, fallback assignments, and a `high / medium / review` quality state. Low-quality alignment is not silently treated as ground truth.

## Speaker Review

**Speaker Review** lets the user rename or correct speaker labels. A correction recomputes participation, speaking balance, action ownership, and meeting intelligence.

## AI Review Queue

Open **AI Review** after an analyzed meeting.

The AMI-trained rankers surface likely Decision and Action evidence, but MeetingLens does **not** silently promote ambiguous candidates. The review workflow supports:

- confirm Decision candidate
- confirm Action candidate
- reject candidate
- persistent review history
- confirmed Action owner initialized from the speaker
- save reviewed meeting back to Memory Vault
- open reviewed meeting directly in the main dashboard

This keeps the product human-in-the-loop while still benefiting from learned ranking.

## Cross-meeting Memory Intelligence

Memory Intelligence supports:

- import/export of MeetingLens JSON
- automatic deduplication with meeting fingerprints
- **hybrid word + character TF-IDF retrieval** across meetings
- source meeting + timestamp evidence
- recurring blocker clustering
- Decision Drift detection
- execution accountability across meetings
- missing owner/deadline flags
- action lifecycle editing: `Open / In progress / Blocked / Done`
- persistent owner/deadline corrections
- topic-frequency index
- open any stored meeting directly in the dashboard

### Memory backends

MeetingLens has two backends behind the same interface:

1. **runtime JSON fallback** — works with zero external configuration and survives browser sessions while the Streamlit instance remains alive;
2. **Supabase backend** — durable hosted storage across instance restarts/redeploys.

To enable Supabase, run `supabase_schema.sql` once in Supabase SQL Editor, then add these to Streamlit Secrets:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_SERVICE_KEY = "your_server_side_service_role_key"
SUPABASE_TABLE = "meetinglens_meetings"
```

The service-role key is used server-side only. The repository intentionally creates no public/anon table policy.

## AMI training and evaluation

MeetingLens includes a reproducible training track based on the **AMI Meeting Corpus manual annotations**.

```bash
pip install -r requirements-training.txt
python -m training.run_ami_training
```

The dataset builder separates gold evidence from weak research labels and uses meeting-level train/validation/test groups to prevent leakage.

### Production formulation

A global utterance classifier was a poor fit for Decision detection because Decision evidence is sparse inside long meetings. MeetingLens therefore moved from “classify every utterance” to **rank the most useful candidate segments inside each meeting**.

The reviewed candidate rankers use transcript text only with within-meeting negative sampling.

Current validated held-out AMI ranking results:

| Event | Hit@5 | Hit@10 | Hit@20 |
|---|---:|---:|---:|
| Decision | 68.0% | 80.0% | 88.0% |
| Action | 77.8% | — | 94.4% |

`Risk` remains rule/hybrid-oriented because the current learned transcript-only detector did not justify replacing the high-precision deterministic rules.

## Model promotion

GitHub Actions trains and evaluates the candidate rankers. A quality gate must pass before `decision_ranker.joblib` and `action_ranker.joblib` are promoted into:

```text
artifacts/meeting_candidate_rankers/
```

The app loads them through `meetinglens_candidate_ranker.py`. If promoted artifacts are missing or fail to load, deterministic extraction remains available.

## Important files

```text
app.py                              main executive workspace
meetinglens_pipeline.py             transcription + intelligence pipeline
meetinglens_candidate_ranker.py     promoted Decision/Action ranker runtime
meetinglens_diarization.py          speaker diarization + timestamp alignment
meetinglens_event_model.py          research/production detector loader
meetinglens_intelligence.py         retrieval, drift, blockers, execution analytics
meetinglens_memory_store.py         JSON + optional Supabase Memory Vault backend
meetinglens_review.py               confirm/reject AI candidate operations
supabase_schema.sql                 durable Memory Vault schema

pages/1_Analyze_Audio.py            audio analysis workflow
pages/2_Memory_Intelligence.py      cross-meeting memory + execution tracking
pages/3_Speaker_Review.py           speaker correction workflow
pages/4_AI_Review.py                human-in-the-loop candidate confirmation

training/ami_dataset.py             AMI NXT/XML -> gold/weak training rows
training/train_baseline.py          multiclass research baseline
training/train_event_detectors.py   annotation-assisted research detectors
training/train_production_detectors.py transcript-only detector benchmark
training/train_candidate_rankers.py meeting-level Decision/Action rankers
training/run_ami_training.py        end-to-end AMI training pipeline
```

## Run locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

For automatic speaker diarization:

```bash
pip install -r requirements-diarization.txt
```

## Deployment

Target: **Streamlit Community Cloud**

- repository: `chaima-menouar/meetinglens-ai`
- branch: `main`
- main file: `app.py`

The standard deployment intentionally does not force the heavy pyannote runtime. Diarization can be enabled in an environment where the optional dependencies and Hugging Face access are configured.

## Stack

- Python
- Streamlit
- faster-whisper
- pyannote.audio (optional)
- scikit-learn
- Pandas
- Plotly
- VADER Sentiment
- Supabase (optional durable memory)
- GitHub Actions
- Streamlit Community Cloud

## Current limitations

- transcription is English-first in the current workflow;
- automatic diarization requires the optional pyannote runtime and Hugging Face access;
- runtime JSON storage is not guaranteed across Streamlit instance recreation unless Supabase is configured;
- Decision Drift is still based on lexical/topic similarity plus change/negation signals rather than a dedicated contradiction model;
- a real multi-speaker end-to-end audio benchmark is still needed for the deployed Whisper + diarization path.

## Next production milestones

1. run a real multi-speaker audio benchmark on the deployed environment;
2. strengthen Decision Drift with contradiction-aware modeling;
3. add authentication when multi-user hosted storage is enabled;
4. add organization/workspace boundaries once multi-user data exists.

---

**MeetingLens AI** — meeting audio → speakers → evidence → review → decisions → execution → organizational memory.
