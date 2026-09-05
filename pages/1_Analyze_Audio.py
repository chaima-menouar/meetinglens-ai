from __future__ import annotations

import pandas as pd
import streamlit as st

from meetinglens_pipeline import transcribe_audio

st.set_page_config(page_title="Analyze audio · MeetingLens AI", page_icon="◌", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600&family=Sora:wght@400;500;600;700&display=swap');
    html,body,[class*=css]{font-family:Inter,system-ui,sans-serif}
    .stApp{background:linear-gradient(180deg,#090b0e,#0f1316 55%,#0a0c0f);color:#f2f0eb}
    [data-testid=stHeader]{background:transparent}
    .block-container{max-width:1280px;padding-top:2rem;padding-bottom:5rem}
    .hero{border:1px solid rgba(255,255,255,.08);border-radius:28px;padding:2.2rem;background:radial-gradient(circle at 85% 20%,rgba(199,173,130,.08),transparent 28%),linear-gradient(135deg,#171b1f,#101316);box-shadow:0 30px 90px rgba(0,0,0,.3)}
    .eyebrow{font-family:'DM Mono';font-size:.65rem;text-transform:uppercase;letter-spacing:.16em;color:#bba784}
    .hero h1{font-family:Sora;font-size:clamp(2.2rem,5vw,4.2rem);line-height:1;letter-spacing:-.05em;margin:.7rem 0 .9rem;font-weight:550}
    .hero p{color:#a2aab0;max-width:760px;line-height:1.7}
    .status{display:inline-flex;margin-top:1rem;padding:.45rem .65rem;border-radius:999px;border:1px solid rgba(146,169,159,.18);color:#b9c7c0;background:rgba(146,169,159,.045);font-size:.72rem}
    .card{border:1px solid rgba(255,255,255,.075);border-radius:20px;padding:1.15rem;background:rgba(255,255,255,.015);min-height:130px}
    .card b{font-family:Sora;font-size:1.9rem;font-weight:550}
    .muted{color:#899298;font-size:.76rem}
    [data-testid=stFileUploader]{border:1px dashed rgba(199,173,130,.25);border-radius:18px;background:rgba(199,173,130,.02)}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Audio intelligence pipeline</div>
      <h1>Upload a meeting. Get the signal.</h1>
      <p>MeetingLens transcribes the recording locally on CPU, timestamps the conversation, scores tone, and extracts first-pass decisions, actions, and risks. This is the first functional audio layer; speaker diarization is the next pipeline stage.</p>
      <div class="status">English · no external API key required</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")
audio = st.file_uploader("Meeting audio", type=["mp3", "wav", "m4a", "mp4", "webm"])
model_size = st.selectbox("Transcription model", ["tiny.en", "base.en"], index=0, help="tiny.en is fastest and safest for the free Streamlit deployment. base.en is more accurate but heavier.")

if audio is not None:
    st.audio(audio)
    if st.button("Analyze meeting", type="primary", use_container_width=True):
        progress = st.progress(5, text="Preparing audio…")
        try:
            progress.progress(20, text="Loading Whisper model…")
            with st.spinner("Transcribing and extracting meeting intelligence…"):
                meeting = transcribe_audio(audio, model_size=model_size)
            progress.progress(100, text="Analysis complete")
            st.session_state["meetinglens_audio_result"] = meeting
        except Exception as exc:
            progress.empty()
            st.error(f"Audio analysis failed: {exc}")

meeting = st.session_state.get("meetinglens_audio_result")
if meeting:
    st.success(f"Analysis ready · {meeting.get('title', 'Meeting')}")
    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        ("Duration", f"{meeting.get('duration_min', 0)} min"),
        ("Decisions", len(meeting.get("decisions", []))),
        ("Actions", len(meeting.get("actions", []))),
        ("Risks", len(meeting.get("risks", []))),
    ]
    for col, (label, value) in zip((c1, c2, c3, c4), metrics):
        with col:
            st.markdown(f'<div class="card"><div class="muted">{label}</div><b>{value}</b></div>', unsafe_allow_html=True)

    st.subheader("Meeting summary")
    st.write(meeting.get("summary", ""))

    t1, t2, t3, t4 = st.tabs(["Transcript", "Decisions", "Actions", "Risks"])
    with t1:
        transcript = pd.DataFrame(meeting.get("segments", []))
        wanted = [c for c in ["timestamp", "speaker", "text", "sentiment"] if c in transcript.columns]
        st.dataframe(transcript[wanted] if wanted else transcript, use_container_width=True, hide_index=True)
    with t2:
        if meeting.get("decisions"):
            for item in meeting["decisions"]:
                st.markdown(f"**{item.get('title','Decision')}**  \n{item.get('detail','')} · confidence {round(float(item.get('confidence',0))*100)}%")
                st.divider()
        else:
            st.info("No strong decision signal detected.")
    with t3:
        actions = pd.DataFrame(meeting.get("actions", []))
        if actions.empty:
            st.info("No strong action signal detected.")
        else:
            st.dataframe(actions, use_container_width=True, hide_index=True)
    with t4:
        risks = pd.DataFrame(meeting.get("risks", []))
        if risks.empty:
            st.info("No strong risk signal detected.")
        else:
            st.dataframe(risks, use_container_width=True, hide_index=True)

    st.caption("Current extraction is an evidence-first heuristic layer. The next milestone replaces these heuristics with trained/LLM-assisted structured extraction and adds real speaker diarization.")
