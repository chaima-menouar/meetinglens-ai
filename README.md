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
- Decision Drift detection with interpretable change type
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
MEETINGLENS_WORKSPACE_ID = "default"
```

The service-role key is used server-side only. The repository intentionally creates no public/anon table policy.

### Workspace isolation

Hosted meetings are scoped by `workspace_id`. The Supabase primary key is `(workspace_id, meeting_id)`, reads only query the active workspace, and destructive operations such as **Clear Memory Vault** are also workspace-scoped.

This gives the project an organization/workspace boundary before full multi-user authorization is enabled.

## Optional OIDC authentication

MeetingLens now supports Streamlit-native OIDC authentication while preserving the current public/single-user deployment by default.

- if no `[auth]` section exists in Streamlit Secrets, all pages behave exactly as before;
- if OIDC is configured, `app.py` and every page require a logged-in user;
- the sidebar exposes sign-out only in authenticated mode;
- a CI guard checks that new Streamlit pages cannot silently omit the auth gate.

Example configuration:

```toml
[auth]
redirect_uri = "https://your-app.streamlit.app/oauth2callback"
cookie_secret = "generate-a-long-random-secret"
client_id = "your-oidc-client-id"
client_secret = "your-oidc-client-secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

`Authlib` is included because Streamlit authentication requires it. The complete commented example is in `.streamlit/secrets.example.toml`.

## Production Status

Open **Production Status** to inspect the deployed runtime without exposing credentials.

It reports:

- Python/runtime compatibility
- whether `faster-whisper` is installed
- whether the promoted Decision/Action ranker artifacts are present
- current Memory Vault backend (`runtime-json` or `supabase`)
- active workspace ID
- optional Supabase connection health check
- whether `pyannote.audio` is installed
- whether a Hugging Face token is configured
- a core readiness score

The page never renders API keys or Hugging Face tokens.

## Real-audio benchmark harness

Use the benchmark command with a real meeting recording to compare runtime behavior between models and deployments:

```bash
python benchmarks/benchmark_audio_pipeline.py meeting.wav --model tiny.en --output tiny_result.json
```

With diarization configured:

```bash
python benchmarks/benchmark_audio_pipeline.py meeting.wav --model tiny.en --diarize --hf-token "$HF_TOKEN" --min-speakers 2 --max-speakers 6 --output diarized_result.json
```

The report records elapsed time, audio size, meeting duration, transcript segment count, detected speakers, decisions/actions/risks, AI candidate counts, diarization status, coverage, quality, and fallback assignments.

A manual GitHub Actions workflow, `.github/workflows/benchmark-real-audio.yml`, can also download an official AMI multi-speaker sample and publish the benchmark report as an artifact. Diarization mode requires the repository `HF_TOKEN` secret.

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
meetinglens_auth.py                 optional Streamlit OIDC gate
meetinglens_pipeline.py             transcription + intelligence pipeline
meetinglens_candidate_ranker.py     promoted Decision/Action ranker runtime
meetinglens_diarization.py          speaker diarization + timestamp alignment
meetinglens_diagnostics.py          safe deployment/runtime readiness checks
meetinglens_event_model.py          research/production detector loader
meetinglens_intelligence.py         retrieval, drift, blockers, execution analytics
meetinglens_memory_store.py         JSON + Supabase + workspace-scoped memory
meetinglens_review.py               confirm/reject AI candidate operations
supabase_schema.sql                 durable workspace-aware Memory Vault schema

pages/1_Analyze_Audio.py            audio analysis workflow
pages/2_Memory_Intelligence.py      cross-meeting memory + execution tracking
pages/3_Speaker_Review.py           speaker correction workflow
pages/4_AI_Review.py                human-in-the-loop candidate confirmation
pages/5_Production_Status.py        runtime/deployment diagnostics

benchmarks/benchmark_audio_pipeline.py real-audio benchmark command
.github/workflows/benchmark-real-audio.yml manual AMI benchmark workflow

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
- Authlib / OIDC (optional authentication)
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
- Decision Drift is interpretable but still heuristic rather than a dedicated contradiction model;
- a real multi-speaker end-to-end diarization benchmark still requires `HF_TOKEN` and an environment capable of running pyannote;
- OIDC authentication is implemented but remains disabled until real identity-provider credentials are configured.

## Next production milestones

1. run the manual real-audio benchmark in the target environment;
2. connect and validate the real Supabase project from Production Status;
3. configure the real OIDC identity provider if login is desired;
4. map authenticated identities to organization/workspace membership when true multi-user authorization is required.

---

**MeetingLens AI** — meeting audio → speakers → evidence → review → decisions → execution → organizational memory.
