from __future__ import annotations

import streamlit as st
from meetinglens_auth import require_user

from meetinglens_memory_store import get_memory_store
from meetinglens_review import confirm_candidate, reject_candidate, review_stats

st.set_page_config(page_title="AI Review · MeetingLens AI", page_icon="◇", layout="wide")

identity = require_user()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600&family=Sora:wght@400;500;600&display=swap');
html,body,[class*=css]{font-family:Inter,system-ui,sans-serif}.stApp{background:linear-gradient(180deg,#090b0e,#0e1215);color:#f2f0eb}.block-container{max-width:1260px;padding-top:2rem}.hero{border:1px solid rgba(255,255,255,.08);border-radius:28px;padding:2rem;background:radial-gradient(circle at 82% 10%,rgba(199,173,130,.11),transparent 30%),rgba(255,255,255,.018);margin-bottom:1rem}.hero h1{font-family:Sora;font-size:clamp(2.2rem,5vw,4.5rem);letter-spacing:-.055em;line-height:1;margin:.45rem 0}.eyebrow{font-family:'DM Mono';font-size:.65rem;letter-spacing:.14em;text-transform:uppercase;color:#c7ad82}.card{border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:1.15rem;background:rgba(255,255,255,.018);margin:.7rem 0}.small{font-size:.78rem;color:#929ba0;line-height:1.6}.meta{font-family:'DM Mono';font-size:.58rem;text-transform:uppercase;letter-spacing:.08em;color:#cbb58f}.score{display:inline-block;border:1px solid rgba(199,173,130,.18);border-radius:999px;padding:.2rem .45rem;font-size:.68rem;color:#d9c5a5;margin-top:.45rem}
</style>
""", unsafe_allow_html=True)

store = get_memory_store()
if "meeting_vault" not in st.session_state:
    try:
        st.session_state.meeting_vault = store.load()
    except Exception:
        st.session_state.meeting_vault = []

st.markdown("""<div class='hero'><div class='eyebrow'>Human-in-the-loop intelligence</div><h1>Review the signals before they become memory.</h1><p class='small'>The AMI-trained rankers surface likely Decision and Action evidence. You decide what becomes a confirmed commitment.</p></div>""", unsafe_allow_html=True)

vault = st.session_state.meeting_vault
current = st.session_state.get("current_meeting") or st.session_state.get("dashboard_meeting")

sources = []
if current:
    sources.append(("current", current))
for index, meeting in enumerate(vault):
    if not current or meeting.get("meeting_id") != current.get("meeting_id"):
        sources.append((f"vault-{index}", meeting))

if not sources:
    st.info("No meeting is available for review. Analyze audio first or load a meeting into Memory Vault.")
    st.stop()

choice = st.selectbox(
    "Meeting to review",
    options=list(range(len(sources))),
    format_func=lambda i: sources[i][1].get("title", "Meeting") + (" · current" if sources[i][0] == "current" else " · vault"),
)
meeting = sources[choice][1]
st.session_state.current_meeting = meeting

stats = review_stats(meeting)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Decision candidates", stats["decision_candidates"])
c2.metric("Action candidates", stats["action_candidates"])
c3.metric("Confirmed", stats["confirmed"])
c4.metric("Rejected", stats["rejected"])


def persist(updated):
    st.session_state.current_meeting = updated
    st.session_state.dashboard_meeting = updated
    try:
        vault_after, _ = store.upsert(updated)
        st.session_state.meeting_vault = vault_after
        return None
    except Exception as exc:
        return str(exc)


def candidate_card(event: str, candidate: dict, index: int):
    label = "Decision" if event == "decision" else "Action"
    st.markdown(
        f"<div class='card'><div class='meta'>{label} candidate · rank #{candidate.get('rank', index + 1)} · {candidate.get('speaker','Speaker')} · {candidate.get('timestamp','00:00')}</div><strong>{candidate.get('text','')}</strong><br><span class='score'>candidate score {round(float(candidate.get('score',0))*100)}%</span></div>",
        unsafe_allow_html=True,
    )
    a, b = st.columns(2)
    with a:
        if st.button(f"Confirm {label.lower()}", key=f"confirm-{event}-{index}-{candidate.get('timestamp','')}", use_container_width=True):
            updated = confirm_candidate(meeting, event, candidate)
            error = persist(updated)
            if error:
                st.error(f"Candidate was confirmed in this session, but persistence failed: {error}")
            else:
                st.success(f"{label} confirmed and saved to Memory Vault.")
            st.rerun()
    with b:
        if st.button("Reject candidate", key=f"reject-{event}-{index}-{candidate.get('timestamp','')}", use_container_width=True):
            updated = reject_candidate(meeting, event, candidate)
            error = persist(updated)
            if error:
                st.error(f"Candidate was rejected in this session, but persistence failed: {error}")
            else:
                st.info("Candidate rejected and removed from the queue.")
            st.rerun()


t1, t2, t3 = st.tabs(["Decision candidates", "Action candidates", "Review history"])
with t1:
    candidates = meeting.get("decision_candidates", []) or []
    if not candidates:
        st.success("No pending Decision candidates for this meeting.")
    for index, candidate in enumerate(candidates):
        candidate_card("decision", candidate, index)

with t2:
    candidates = meeting.get("action_candidates", []) or []
    if not candidates:
        st.success("No pending Action candidates for this meeting.")
    for index, candidate in enumerate(candidates):
        candidate_card("action", candidate, index)

with t3:
    history = meeting.get("review_history", []) or []
    if not history:
        st.caption("No candidate decisions have been reviewed yet.")
    else:
        rows = []
        for item in history:
            candidate = item.get("candidate", {})
            rows.append({
                "event": item.get("event"),
                "outcome": item.get("outcome"),
                "speaker": candidate.get("speaker"),
                "timestamp": candidate.get("timestamp"),
                "score": candidate.get("score"),
                "text": candidate.get("text"),
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

st.divider()
if st.button("Open reviewed meeting in dashboard", use_container_width=True):
    st.session_state.dashboard_meeting = st.session_state.current_meeting
    st.switch_page("app.py")

st.caption("MeetingLens AI · ranked evidence → human review → confirmed organizational memory")
