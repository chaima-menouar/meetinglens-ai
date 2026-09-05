# MeetingLens AI

**MeetingLens AI** turns meeting audio into timestamped evidence, speaker-aware transcripts, decisions, action items, risks, and cross-meeting organizational memory.

> From conversation to decisions that move.

## Current product

MeetingLens is shipped as **one Streamlit application** so transcription, intelligence, review, memory, and the executive workspace deploy together.

### Product flow

```text
Meeting audio
    |
    +--> faster-whisper -------------------------+
    |                                            |
    +--> optional pyannote speaker diarization --+--> aligned transcript
                                                     |
                                                     +--> sentiment
                                                     +--> deterministic high-precision extraction
                                                     +--> AMI-trained candidate ranking
                                                     +--> owner + due-date extraction
                                                     +--> risk signals
                                                     |
                                                     v
                                                 Meeting JSON
                                                     |
                   +---------------------------------+------------------+
                   |                                 |                  |
                   v                                 v                  v
             Main dashboard                   Speaker Review      Memory Vault
                                                                        |
                                                                        +--> search
                                                                        +--> recurring blockers
                                                                        +--> Decision Drift
                                                                        +--> execution accountability
                                                                        +--> topic intelligence
```

## Main workspace

- Executive meeting overview
- Clarity / meeting-health signals
- Decisions, risks, ownership, and key moments
- AI candidate-review queue for uncertain Decision/Action evidence
- Search inside the current meeting
- Sentiment and participation analytics
- Direct handoff from analyzed audio or a stored meeting

The dashboard now uses the meeting selected in the current session instead of forcing the built-in demo after analysis.

## Real audio analysis

Open **Analyze Audio** from the Streamlit navigation.

- MP3 / WAV / M4A / MP4 / WEBM / MPEG upload
- `faster-whisper` English transcription on CPU
- VAD + timestamps
- Segment sentiment
- Decision extraction with timestamped evidence
- Action extraction with owner and due-date detection
- Risk extraction and severity
- Optional automatic speaker diarization
- AI candidate ranking for Decision and Action evidence
- Save to Memory Vault
- Open the analyzed meeting directly in the full dashboard
- Download meeting JSON

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

**Speaker Review** lets the user rename or correct speaker labels. A correction recomputes participation, speaking balance, action ownership, and the meeting intelligence output.

## Cross-meeting Memory Intelligence

The Memory Vault now has a runtime persistence layer in `meetinglens_memory_store.py` rather than being only a browser-session list.

Memory Intelligence supports:

- import/export of MeetingLens JSON
- automatic deduplication with meeting fingerprints
- search across meetings with source + timestamp evidence
- recurring blocker clustering
- Decision Drift detection
- execution accountability across meetings
- missing owner/deadline flags
- topic-frequency index
- open a stored meeting directly in the main dashboard

The JSON runtime store survives browser sessions while the deployment instance remains alive. **Streamlit Community Cloud can recreate its filesystem after a reboot or redeploy**, so exporting the Memory Vault remains the portable backup until a hosted database is connected.

## AMI training and evaluation

MeetingLens includes a reproducible training track based on the **AMI Meeting Corpus manual annotations**.

```bash
pip install -r requirements-training.txt
python -m training.run_ami_training
```

The dataset builder separates:

- gold evidence from AMI extractive/abstractive summary links
- weak auxiliary labels used for research
- meeting-level train / validation / test groups to prevent leakage

### Why the production formulation changed

A global utterance classifier was a poor fit for Decision detection because Decision evidence is sparse inside long meetings. MeetingLens therefore moved from “classify every utterance” to **rank the most useful candidate segments inside each meeting**.

The reviewed candidate rankers are trained on transcript text only with within-meeting negative sampling.

Current validated ranking results on the held-out AMI meeting split:

| Event | Hit@5 | Hit@10 | Hit@20 |
|---|---:|---:|---:|
| Decision | 68.0% | 80.0% | 88.0% |
| Action | 77.8% | — | 94.4% |

These rankers are **review-first**, not silent auto-confirmation models. Deterministic high-precision rules continue to produce confirmed Decision/Action items; the rankers surface additional evidence in the UI for human review.

`Risk` remains a hybrid/rule-oriented signal because the current transcript-only learned model did not outperform the high-precision deterministic rules enough to justify promotion.

## Model promotion

GitHub Actions trains and evaluates the candidate rankers. A quality gate must pass before the reviewed `decision_ranker.joblib` and `action_ranker.joblib` artifacts are promoted into:

```text
artifacts/meeting_candidate_rankers/
```

The app loads these promoted artifacts through `meetinglens_candidate_ranker.py`. If artifacts are absent or fail to load, the application keeps working with deterministic extraction.

## Important files

```text
app.py                              main executive workspace
meetinglens_pipeline.py             transcription + intelligence pipeline
meetinglens_candidate_ranker.py     promoted Decision/Action ranker runtime
meetinglens_diarization.py          speaker diarization + timestamp alignment
meetinglens_event_model.py          research/production detector loader
meetinglens_intelligence.py         search, drift, blockers, execution analytics
meetinglens_memory_store.py         runtime-persistent Memory Vault backend

pages/1_Analyze_Audio.py            audio analysis workflow
pages/2_Memory_Intelligence.py      cross-meeting organizational memory
pages/3_Speaker_Review.py           speaker correction workflow

training/ami_dataset.py             AMI NXT/XML -> gold/weak training rows
training/train_baseline.py          multiclass research baseline
training/train_event_detectors.py   annotation-assisted research detectors
training/train_production_detectors.py transcript-only detector benchmark
training/train_candidate_rankers.py meeting-level Decision/Action rankers
training/run_ami_training.py        end-to-end AMI training pipeline

requirements.txt                    deployed app dependencies
requirements-diarization.txt        optional pyannote runtime
requirements-training.txt           AMI training dependencies
requirements-semantic.txt           semantic-model research dependencies
```

## Run locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

For automatic speaker diarization also install:

```bash
pip install -r requirements-diarization.txt
```

## Deployment

Target deployment: **Streamlit Community Cloud**

- repository: `chaima-menouar/meetinglens-ai`
- branch: `main`
- main file: `app.py`

The standard deployment intentionally does not force the heavy pyannote runtime. Diarization can be enabled in an environment where the optional dependencies and Hugging Face access are configured.

## Stack

- Python
- Streamlit
- faster-whisper
- pyannote.audio (optional diarization)
- scikit-learn
- Pandas
- Plotly
- VADER Sentiment
- GitHub Actions
- Streamlit Community Cloud

## Current limitations

- Current transcription workflow is English-first.
- Automatic diarization requires the optional pyannote runtime and Hugging Face access.
- Streamlit Community Cloud runtime storage is not guaranteed across instance recreation; a hosted database is the next persistence upgrade.
- Decision/Action candidate rankers surface likely evidence but do not replace human confirmation for ambiguous language.
- Decision Drift currently uses lexical/topic similarity and change/negation signals rather than a dedicated contradiction model.

## Next production milestones

1. hosted durable meeting storage (database-backed Memory Vault)
2. real multi-speaker audio benchmark for Whisper + diarization alignment
3. stronger semantic cross-meeting retrieval
4. contradiction-aware Decision Drift
5. action lifecycle editing (open / done / blocked) and persistent status
6. authentication once durable multi-user storage is introduced

---

**MeetingLens AI** — meeting audio → speakers → evidence → decisions → ownership → organizational memory.
