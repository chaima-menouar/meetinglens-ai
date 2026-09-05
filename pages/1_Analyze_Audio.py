from __future__ import annotations

import json
import streamlit as st

from meetinglens_pipeline import transcribe_audio

st.set_page_config(page_title="Analyze Audio · MeetingLens AI", page_icon="◉", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600&family=Sora:wght@400;500;600&display=swap');
html,body,[class*=css]{font-family:Inter,system-ui,sans-serif}.stApp{background:linear-gradient(180deg,#090b0e,#0e1215);color:#f2f0eb}.block-container{max-width:1260px;padding-top:2rem}.hero{border:1px solid rgba(255,255,255,.08);border-radius:28px;padding:2rem;background:radial-gradient(circle at 85% 10%,rgba(199,173,130,.12),transparent 28%),rgba(255,255,255,.018);margin-bottom:1.2rem}.eyebrow{font-family:'DM Mono';font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;color:#c7ad82}.hero h1{font-family:Sora;font-size:clamp(2.4rem,5vw,4.6rem);letter-spacing:-.055em;line-height:1;margin:.45rem 0}.hero p{color:#98a1a6;max-width:760px;line-height:1.7}.card{border:1px solid rgba(255,255,255,.075);border-radius:20px;padding:1.15rem;background:rgba(255,255,255,.015);margin:.75rem 0}.card strong{font-family:Sora}.tag{display:inline-block;font-family:'DM Mono';font-size:.6rem;letter-spacing:.08em;text-transform:uppercase;border:1px solid rgba(199,173,130,.18);color:#cdb68f;padding:.22rem .45rem;border-radius:999px}.small{font-size:.76rem;color:#8d969b}.stButton>button{border-radius:999px;border:1px solid rgba(199,173,130,.24);background:#d7c09b;color:#15181b;font-weight:700}.stButton>button:hover{border-color:#ead8bb;color:#15181b;background:#ead8bb}
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class='hero'><div class='eyebrow'>Audio intelligence pipeline</div><h1>Upload. Transcribe. Understand.</h1><p>Turn an English meeting recording into timestamped evidence, decisions, follow-up actions, risks, and a searchable meeting object.</p></div>""", unsafe_allow_html=True)

if "meeting_vault" not in st.session_state:
    st.session_state.meeting_vault = []

left, right = st.columns([1.1, .9])
with left:
    audio = st.file_uploader("Meeting recording", type=["mp3", "wav", "m4a", "mp4", "webm", "mpeg"])
    if audio:
        st.audio(audio)
    model = st.selectbox("Whisper model", ["tiny.en", "base.en"], index=0, help="tiny.en is faster on free CPU. base.en is more accurate but heavier.")
    analyze = st.button("Analyze meeting", type="primary", use_container_width=True, disabled=audio is None)

with right:
    st.markdown("""<div class='card'><span class='tag'>Current pipeline</span><p><strong>1 · Transcription</strong><br><span class='small'>faster-whisper on CPU with timestamps and VAD.</span></p><p><strong>2 · Conversation signals</strong><br><span class='small'>Sentiment plus decision, action, and risk extraction.</span></p><p><strong>3 · Memory-ready output</strong><br><span class='small'>The result can be added to the in-session Meeting Vault for cross-meeting analysis.</span></p></div>""", unsafe_allow_html=True)
    st.info("Automatic multi-speaker diarization is not enabled in the free deployment yet. Audio is currently labeled as one speaker; speaker-aware analysis is the next model layer.")

if analyze and audio is not None:
    status = st.status("MeetingLens is processing the recording…", expanded=True)
    try:
        status.write("Loading speech model…")
        result = transcribe_audio(audio, model_size=model)
        status.write("Extracting decisions, actions, risks, and sentiment…")
        st.session_state.current_meeting = result
        status.update(label="Analysis complete", state="complete", expanded=False)
    except Exception as exc:
        status.update(label="Analysis failed", state="error", expanded=True)
        st.error(str(exc))

meeting = st.session_state.get("current_meeting")
if meeting:
    st.divider()
    st.subheader(meeting.get("title", "Analyzed meeting"))
    st.caption(meeting.get("summary", ""))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Duration", f"{meeting.get('duration_min', 0)} min")
    c2.metric("Decisions", len(meeting.get("decisions", [])))
    c3.metric("Actions", len(meeting.get("actions", [])))
    c4.metric("Risks", len(meeting.get("risks", [])))

    a, b = st.columns(2)
    with a:
        st.markdown("### Decisions")
        if not meeting.get("decisions"):
            st.caption("No strong decision signals detected.")
        for d in meeting.get("decisions", []):
            st.markdown(f"<div class='card'><strong>{d.get('title','')}</strong><br><span class='small'>{d.get('detail','')} · {round(float(d.get('confidence',0))*100)}% confidence</span></div>", unsafe_allow_html=True)
        st.markdown("### Risks")
        if not meeting.get("risks"):
            st.caption("No strong risk signals detected.")
        for r in meeting.get("risks", []):
            st.markdown(f"<div class='card'><strong>{r.get('title','')}</strong><br><span class='small'>{r.get('severity','Medium')} · minute {r.get('minute',0)}</span></div>", unsafe_allow_html=True)
    with b:
        st.markdown("### Action items")
        if not meeting.get("actions"):
            st.caption("No strong action signals detected.")
        for x in meeting.get("actions", []):
            st.markdown(f"<div class='card'><strong>{x.get('task','')}</strong><br><span class='small'>Owner: {x.get('owner','Unassigned')} · Due: {x.get('due','Not stated')}</span></div>", unsafe_allow_html=True)

    st.markdown("### Timestamped transcript")
    st.dataframe(meeting.get("segments", []), use_container_width=True, hide_index=True)

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Add this meeting to Memory Vault", use_container_width=True):
            vault = st.session_state.meeting_vault
            fingerprint = (meeting.get("title"), meeting.get("duration_min"), len(meeting.get("segments", [])))
            exists = any((m.get("title"), m.get("duration_min"), len(m.get("segments", []))) == fingerprint for m in vault)
            if not exists:
                vault.append(meeting)
                st.success("Added to Memory Vault.")
            else:
                st.info("This meeting is already in the vault.")
    with b2:
        st.download_button("Download meeting JSON", data=json.dumps(meeting, indent=2, ensure_ascii=False), file_name=f"{meeting.get('title','meeting').replace(' ','_').lower()}.json", mime="application/json", use_container_width=True)

st.caption("MeetingLens AI · audio → evidence → decision → memory")
