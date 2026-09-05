from __future__ import annotations

import json
import streamlit as st

from meetinglens_intelligence import (
    action_accountability,
    build_topic_index,
    decision_drift,
    memory_stats,
    meeting_search,
    recurring_blockers,
)
from meetinglens_memory_store import get_memory_store, meeting_fingerprint

st.set_page_config(page_title="Memory Intelligence · MeetingLens AI", page_icon="◉", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600&family=Sora:wght@400;500;600&display=swap');
html,body,[class*=css]{font-family:Inter,system-ui,sans-serif}.stApp{background:linear-gradient(180deg,#090b0e,#0e1215);color:#f2f0eb}.block-container{max-width:1320px;padding-top:2rem}.hero{border:1px solid rgba(255,255,255,.08);border-radius:28px;padding:2rem;background:radial-gradient(circle at 80% 10%,rgba(146,169,159,.11),transparent 28%),rgba(255,255,255,.018)}.hero h1{font-family:Sora;font-size:clamp(2.4rem,5vw,4.6rem);letter-spacing:-.055em;line-height:1;margin:.45rem 0}.eyebrow{font-family:'DM Mono';font-size:.66rem;letter-spacing:.14em;text-transform:uppercase;color:#c7ad82}.card{border:1px solid rgba(255,255,255,.075);border-radius:18px;padding:1rem;background:rgba(255,255,255,.015);margin:.65rem 0}.small{font-size:.76rem;color:#8e979c}.kind{font-family:'DM Mono';font-size:.58rem;letter-spacing:.08em;text-transform:uppercase;color:#c8b18d}.vault{font-family:'DM Mono';font-size:.62rem;color:#9ba4a9}
</style>
""", unsafe_allow_html=True)

store = get_memory_store()
if "meeting_vault" not in st.session_state:
    st.session_state.meeting_vault = store.load()

st.markdown("""<div class='hero'><div class='eyebrow'>Cross-meeting intelligence</div><h1>Turn meetings into organizational memory.</h1><p class='small'>Search across meetings, surface repeated blockers, detect decision drift, and expose execution gaps before they disappear into another meeting.</p></div>""", unsafe_allow_html=True)

st.write("")
uploaded = st.file_uploader("Import meeting JSON or a Meeting Vault", type=["json"], accept_multiple_files=True)
if uploaded:
    merged = list(st.session_state.meeting_vault)
    before = len(merged)
    seen = {meeting_fingerprint(m) for m in merged}
    for f in uploaded:
        try:
            payload = json.load(f)
            items = payload if isinstance(payload, list) else payload.get("meetings", []) if isinstance(payload, dict) and "meetings" in payload else [payload]
            for m in items:
                if isinstance(m, dict) and m.get("segments") is not None:
                    fp = meeting_fingerprint(m)
                    if fp not in seen:
                        merged.append(m); seen.add(fp)
        except Exception as exc:
            st.error(f"Could not import {getattr(f, 'name', 'file')}: {exc}")
    if len(merged) > before:
        st.session_state.meeting_vault = store.replace_all(merged)
        st.success(f"Added {len(merged) - before} meeting(s) to the vault.")

vault = st.session_state.meeting_vault
stats = memory_stats(vault)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Meetings", stats["meetings"]); c2.metric("Decisions", stats["decisions"]); c3.metric("Actions", stats["actions"]); c4.metric("Open risks", stats["risks"])

if not vault:
    st.info("The Memory Vault is empty. Analyze audio in the Analyze Audio page or import meeting JSON files here.")
    st.stop()

st.caption("Vault: " + " · ".join(m.get("title", "Meeting") for m in vault))

s1, s2 = st.columns([1.5, .5])
with s1:
    selected_title = st.selectbox("Open a stored meeting", [m.get("title", f"Meeting {i+1}") for i, m in enumerate(vault)])
with s2:
    st.write("")
    st.write("")
    if st.button("Open in dashboard", use_container_width=True):
        selected_index = [m.get("title", f"Meeting {i+1}") for i, m in enumerate(vault)].index(selected_title)
        st.session_state.dashboard_meeting = vault[selected_index]
        st.session_state.current_meeting = vault[selected_index]
        st.switch_page("app.py")

q = st.text_input("Ask across all meetings", placeholder="What did we decide about the launch? / analytics / support / deadline...")
if q:
    results = meeting_search(vault, q)
    if not results:
        st.info("No matching evidence found.")
    for r in results:
        st.markdown(f"<div class='card'><div class='kind'>{r['kind']} · {r['meeting']} · {r['timestamp']}</div><strong>{r['speaker']}</strong><div class='small'>{r['text']}</div></div>", unsafe_allow_html=True)

st.divider()
t1, t2, t3, t4 = st.tabs(["Recurring blockers", "Decision drift", "Execution", "Topics"])
with t1:
    blockers = recurring_blockers(vault)
    if not blockers:
        st.info("No repeated blockers detected yet. This becomes useful after multiple meetings contain related risks.")
    for b in blockers:
        st.markdown(f"<div class='card'><div class='kind'>Recurring blocker · {b['count']} mentions</div><strong>{b['topic']}</strong><div class='small'>Seen in: {' · '.join(b['meetings'])}</div></div>", unsafe_allow_html=True)
        with st.expander("Evidence"):
            st.dataframe(b["evidence"], use_container_width=True, hide_index=True)

with t2:
    drift = decision_drift(vault)
    if not drift:
        st.info("No possible decision drift detected yet.")
    for d in drift:
        st.markdown(f"<div class='card'><div class='kind'>{d['reason']} · similarity {round(d['similarity']*100)}%</div><strong>{d['from_meeting']} → {d['to_meeting']}</strong><div class='small'><b>Before:</b> {d['previous']}<br><b>Later:</b> {d['current']}</div></div>", unsafe_allow_html=True)

with t3:
    execution = action_accountability(vault)
    attention = [x for x in execution if x["needs_attention"]]
    e1, e2, e3 = st.columns(3)
    e1.metric("Tracked actions", len(execution))
    e2.metric("Needs attention", len(attention))
    e3.metric("Owned + dated", len(execution) - len(attention))
    if not execution:
        st.info("No action items are stored yet.")
    else:
        st.dataframe(execution, use_container_width=True, hide_index=True, column_order=["meeting", "task", "owner", "due", "status", "missing", "timestamp"])
        if attention:
            st.warning(f"{len(attention)} action item(s) are missing an owner, a deadline, or both.")

with t4:
    topics = build_topic_index(vault)
    if topics:
        st.dataframe([{"topic": t, "mentions": n} for t, n in topics], use_container_width=True, hide_index=True)

st.divider()
vault_json = json.dumps({"meetings": vault}, indent=2, ensure_ascii=False)
st.download_button("Export Memory Vault", vault_json, "meetinglens_memory_vault.json", "application/json", use_container_width=True)
if st.button("Clear Memory Vault", use_container_width=True):
    store.clear()
    st.session_state.meeting_vault = []
    st.rerun()

st.caption("Memory Vault is persisted in the running deployment and survives browser sessions. Streamlit Community Cloud can recreate its filesystem after a reboot/redeploy, so Export Memory Vault remains the portable backup until a hosted database is connected.")
