from __future__ import annotations

import json
import os
import streamlit as st

from meetinglens_pipeline import transcribe_audio

st.set_page_config(page_title="Analyze Audio · MeetingLens AI", page_icon="◉", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600&family=Sora:wght@400;500;600&display=swap');
html,body,[class*=css]{font-family:Inter,system-ui,sans-serif}.stApp{background:linear-gradient(180deg,#090b0e,#0e1215);color:#f2f0eb}.block-container{max-width:1260px;padding-top:2rem}.hero{border:1px solid rgba(255,255,255,.08);border-radius:28px;padding:2rem;background:radial-gradient(circle at 85% 10%,rgba(199,173,130,.12),transparent 28%),rgba(255,255,255,.018);margin-bottom:1.2rem}.eyebrow{font-family:'DM Mono';font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;color:#c7ad82}.hero h1{font-family:Sora;font-size:clamp(2.4rem,5vw,4.6rem);letter-spacing:-.055em;line-height:1;margin:.45rem 0}.hero p{color:#98a1a6;max-width:760px;line-height:1.7}.card{border:1px solid rgba(255,255,255,.075);border-radius:20px;padding:1.15rem;background:rgba(255,255,255,.015);margin:.75rem 0}.card strong{font-family:Sora}.tag{display:inline-block;font-family:'DM Mono';font-size:.6rem;letter-spacing:.08em;text-transform:uppercase;border:1px solid rgba(199,173,130,.18);color:#cdb68f;padding:.22rem .45rem;border-radius:999px}.small{font-size:.76rem;color:#8d969b}.stButton>button{border-radius:999px;border:1px solid rgba(199,173,130,.24);background:#d7c09b;color:#15181b;font-weight:700}.stButton>button:hover{border-color:#ead8bb;color:#15181b;background:#ead8bb}
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class='hero'><div class='eyebrow'>Audio intelligence pipeline</div><h1>Upload. Transcribe. Understand.</h1><p>Turn an English meeting recording into timestamped evidence, speaker-aware conversation turns, decisions, follow-up actions, risks, and a searchable meeting object.</p></div>""", unsafe_allow_html=True)

if "meeting_vault" not in st.session_state:
    st.session_state.meeting_vault = []


def get_hf_token() -> str:
    token = os.getenv("HF_TOKEN", "").strip()
    if token:
        return token
    try:
        return str(st.secrets.get("HF_TOKEN", "")).strip()
    except Exception:
        return ""


left, right = st.columns([1.1, .9])
with left:
    audio = st.file_uploader("Meeting recording", type=["mp3", "wav", "m4a", "mp4", "webm", "mpeg"])
    if audio:
        st.audio(audio)
    model = st.selectbox("Whisper model", ["tiny.en", "base.en"], index=0, help="tiny.en is faster on free CPU. base.en is more accurate but heavier.")

    st.markdown("#### Speaker detection")
    auto_diarize = st.toggle(
        "Automatic speaker diarization",
        value=False,
        help="Uses pyannote Community-1 when the optional diarization environment is installed and HF_TOKEN is configured.",
    )
    min_speakers = max_speakers = None
    if auto_diarize:
        d1, d2 = st.columns(2)
        with d1:
            min_speakers = st.number_input("Minimum speakers", min_value=1, max_value=12, value=2, step=1)
        with d2:
            max_speakers = st.number_input("Maximum speakers", min_value=1, max_value=20, value=6, step=1)
        if max_speakers < min_speakers:
            st.warning("Maximum speakers must be greater than or equal to minimum speakers.")
        if not get_hf_token():
            st.warning("Automatic diarization needs HF_TOKEN in Streamlit Secrets or the environment. Transcription will still work and fall back to Speaker Review.")

    analyze = st.button("Analyze meeting", type="primary", use_container_width=True, disabled=audio is None or (auto_diarize and max_speakers < min_speakers))

with right:
    st.markdown("""<div class='card'><span class='tag'>Current pipeline</span><p><strong>1 · Transcription</strong><br><span class='small'>faster-whisper on CPU with timestamps and VAD.</span></p><p><strong>2 · Speaker diarization</strong><br><span class='small'>Optional pyannote Community-1 speaker turns aligned to Whisper segments.</span></p><p><strong>3 · Conversation intelligence</strong><br><span class='small'>Sentiment plus decision, action, risk, owner, and due-date extraction.</span></p><p><strong>4 · Memory-ready output</strong><br><span class='small'>The meeting can be added to Memory Vault for cross-meeting analysis.</span></p></div>""", unsafe_allow_html=True)
    if auto_diarize:
        st.info("Automatic diarization is requested. MeetingLens now checks alignment coverage before trusting the speaker labels. Low-confidence output is routed to Speaker Review.")
    else:
        st.info("Speaker Review remains available after transcription. Enable automatic diarization when the pyannote runtime is configured.")

if analyze and audio is not None:
    status = st.status("MeetingLens is processing the recording…", expanded=True)
    try:
        status.write("Loading speech model…")
        result = transcribe_audio(
            audio,
            model_size=model,
            diarize=auto_diarize,
            hf_token=get_hf_token(),
            min_speakers=int(min_speakers) if auto_diarize else None,
            max_speakers=int(max_speakers) if auto_diarize else None,
        )
        if auto_diarize:
            status.write("Aligning speaker turns with transcript timestamps…")
            status.write("Checking diarization coverage and fallback assignments…")
        status.write("Extracting decisions, actions, risks, owners, and sentiment…")
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

    diarization_status = meeting.get("diarization_status", "speaker-review-needed")
    diarization_meta = meeting.get("diarization", {})
    if diarization_status == "automatic-complete":
        st.success(f"Automatic diarization complete · {len(meeting.get('participants', []))} speakers detected")
    elif diarization_status == "automatic-review-recommended":
        st.warning("Automatic diarization ran, but alignment confidence is low. Review speaker labels before relying on speaker-level analytics.")
    elif diarization_status == "automatic-failed":
        st.warning("Transcription completed, but automatic diarization could not run. Speaker Review can still be used.")
        if meeting.get("diarization_error"):
            with st.expander("Diarization technical detail"):
                st.code(meeting["diarization_error"])
    else:
        st.info("Speaker labels are provisional. Use Speaker Review to rename or correct them.")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Duration", f"{meeting.get('duration_min', 0)} min")
    c2.metric("Speakers", len(meeting.get("participants", [])))
    c3.metric("Decisions", len(meeting.get("decisions", [])))
    c4.metric("Actions", len(meeting.get("actions", [])))
    c5.metric("Risks", len(meeting.get("risks", [])))

    if diarization_meta:
        st.markdown("### Diarization quality")
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Coverage", f"{diarization_meta.get('coverage_pct', 0)}%")
        q2.metric("Speaker turns", diarization_meta.get("turn_count", 0))
        q3.metric("Fallback segments", diarization_meta.get("fallback_segments", 0))
        q4.metric("Quality", str(diarization_meta.get("quality", "review")).title())
        if diarization_meta.get("quality") == "review":
            st.info("Speaker Review is recommended because too much transcript timing had weak direct overlap with the diarization turns.")

    if meeting.get("participants"):
        st.markdown("### Speaker balance")
        st.dataframe(meeting.get("participants", []), use_container_width=True, hide_index=True)

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
            st.markdown(f"<div class='card'><strong>{r.get('title','')}</strong><br><span class='small'>{r.get('speaker','Speaker')} · {r.get('severity','Medium')} · {r.get('timestamp', '00:00')}</span></div>", unsafe_allow_html=True)
    with b:
        st.markdown("### Action items")
        if not meeting.get("actions"):
            st.caption("No strong action signals detected.")
        for x in meeting.get("actions", []):
            st.markdown(f"<div class='card'><strong>{x.get('task','')}</strong><br><span class='small'>Owner: {x.get('owner','Unassigned')} · Due: {x.get('due','Not stated')} · {x.get('timestamp', '00:00')}</span></div>", unsafe_allow_html=True)

    st.markdown("### Timestamped transcript")
    transcript_columns = ["timestamp", "speaker", "speaker_overlap_ratio", "speaker_assignment", "kind", "text", "sentiment"]
    transcript_rows = [{key: row.get(key) for key in transcript_columns} for row in meeting.get("segments", [])]
    st.dataframe(transcript_rows, use_container_width=True, hide_index=True)

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

st.caption("MeetingLens AI · audio → speaker → evidence → decision → memory")
