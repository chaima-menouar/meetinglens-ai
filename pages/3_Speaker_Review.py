from __future__ import annotations

import json
import pandas as pd
import streamlit as st
from meetinglens_auth import require_user

from meetinglens_pipeline import refresh_intelligence

st.set_page_config(page_title="Speaker Review · MeetingLens AI", page_icon="◉", layout="wide")

identity = require_user()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600&family=Sora:wght@400;500;600&display=swap');
html,body,[class*=css]{font-family:Inter,system-ui,sans-serif}.stApp{background:linear-gradient(180deg,#090b0e,#0e1215);color:#f2f0eb}.block-container{max-width:1260px;padding-top:2rem}.hero{border:1px solid rgba(255,255,255,.08);border-radius:28px;padding:2rem;background:radial-gradient(circle at 85% 10%,rgba(199,173,130,.10),transparent 30%),rgba(255,255,255,.018)}.hero h1{font-family:Sora;font-size:clamp(2.3rem,5vw,4.4rem);letter-spacing:-.055em;line-height:1;margin:.45rem 0}.eyebrow{font-family:'DM Mono';font-size:.66rem;letter-spacing:.14em;text-transform:uppercase;color:#c7ad82}.small{font-size:.78rem;color:#939ca1}
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class='hero'><div class='eyebrow'>Speaker-aware review</div><h1>Assign who said what.</h1><p class='small'>The free deployment does not run a heavy diarization model yet. This review layer lets you correct speaker labels, then recalculates ownership and speaking-time analytics from the edited transcript.</p></div>""", unsafe_allow_html=True)

meeting = st.session_state.get("current_meeting")
if meeting is None:
    uploaded = st.file_uploader("Load analyzed meeting JSON", type=["json"])
    if uploaded:
        try:
            meeting = json.load(uploaded)
            st.session_state.current_meeting = meeting
        except Exception as exc:
            st.error(str(exc))

if meeting is None:
    st.info("Analyze an audio file first, or upload an analyzed meeting JSON.")
    st.stop()

segments = pd.DataFrame(meeting.get("segments", []))
if segments.empty:
    st.warning("This meeting has no transcript segments.")
    st.stop()

for col in ["timestamp", "speaker", "text", "kind", "sentiment", "start_sec", "end_sec", "minute", "id"]:
    if col not in segments.columns:
        segments[col] = "" if col in {"timestamp", "speaker", "text", "kind", "sentiment"} else 0

st.caption("Edit only the Speaker column unless you intentionally want to correct transcript metadata.")
edited = st.data_editor(
    segments[["id", "timestamp", "speaker", "text", "kind", "sentiment", "start_sec", "end_sec", "minute"]],
    use_container_width=True,
    hide_index=True,
    disabled=["id", "timestamp", "text", "kind", "sentiment", "start_sec", "end_sec", "minute"],
    column_config={"speaker": st.column_config.TextColumn("Speaker", help="Use consistent names, e.g. Maya, Omar, Speaker 1")},
)

if st.button("Apply speaker labels and recompute intelligence", type="primary", use_container_width=True):
    meeting["segments"] = edited.to_dict("records")
    meeting = refresh_intelligence(meeting)
    meeting["diarization_status"] = "speaker-reviewed"
    st.session_state.current_meeting = meeting
    st.success("Speaker labels applied. Action ownership and participant balance were recomputed.")

st.divider()
if meeting.get("participants"):
    c1, c2 = st.columns([.8, 1.2])
    with c1:
        st.markdown("### Speaking balance")
        st.dataframe(meeting.get("participants", []), use_container_width=True, hide_index=True)
    with c2:
        st.markdown("### Ownership after review")
        st.dataframe(meeting.get("actions", []), use_container_width=True, hide_index=True)

st.download_button("Download speaker-reviewed meeting", json.dumps(meeting, indent=2, ensure_ascii=False), "meetinglens_speaker_reviewed.json", "application/json", use_container_width=True)
