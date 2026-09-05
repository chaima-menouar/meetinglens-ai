from __future__ import annotations

import json
import streamlit as st

from meetinglens_intelligence import decision_drift, memory_stats, meeting_search, recurring_blockers, build_topic_index

st.set_page_config(page_title="Memory Intelligence · MeetingLens AI", page_icon="◉", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600&family=Sora:wght@400;500;600&display=swap');
html,body,[class*=css]{font-family:Inter,system-ui,sans-serif}.stApp{background:linear-gradient(180deg,#090b0e,#0e1215);color:#f2f0eb}.block-container{max-width:1320px;padding-top:2rem}.hero{border:1px solid rgba(255,255,255,.08);border-radius:28px;padding:2rem;background:radial-gradient(circle at 80% 10%,rgba(146,169,159,.11),transparent 28%),rgba(255,255,255,.018)}.hero h1{font-family:Sora;font-size:clamp(2.4rem,5vw,4.6rem);letter-spacing:-.055em;line-height:1;margin:.45rem 0}.eyebrow{font-family:'DM Mono';font-size:.66rem;letter-spacing:.14em;text-transform:uppercase;color:#c7ad82}.card{border:1px solid rgba(255,255,255,.075);border-radius:18px;padding:1rem;background:rgba(255,255,255,.015);margin:.65rem 0}.small{font-size:.76rem;color:#8e979c}.kind{font-family:'DM Mono';font-size:.58rem;letter-spacing:.08em;text-transform:uppercase;color:#c8b18d}.vault{font-family:'DM Mono';font-size:.62rem;color:#9ba4a9}
</style>
""", unsafe_allow_html=True)

if "meeting_vault" not in st.session_state:
    st.session_state.meeting_vault = []

st.markdown("""<div class='hero'><div class='eyebrow'>Cross-meeting intelligence</div><h1>Turn meetings into organizational memory.</h1><p class='small'>Search across meetings, surface repeated blockers, and detect when a later decision appears to change an earlier one.</p></div>""", unsafe_allow_html=True)

st.write("")
uploaded = st.file_uploader("Import meeting JSON or a Meeting Vault", type=["json"], accept_multiple_files=True)
if uploaded:
    added = 0
    for f in uploaded:
        try:
            payload = json.load(f)
            items = payload if isinstance(payload, list) else payload.get("meetings", []) if isinstance(payload, dict) and "meetings" in payload else [payload]
            for m in items:
                if isinstance(m, dict) and m.get("segments") is not None:
                    fp = (m.get("title"), m.get("duration_min"), len(m.get("segments", [])))
                    if not any((x.get("title"), x.get("duration_min"), len(x.get("segments", []))) == fp for x in st.session_state.meeting_vault):
                        st.session_state.meeting_vault.append(m); added += 1
        except Exception as exc:
            st.error(f"Could not import {getattr(f, 'name', 'file')}: {exc}")
    if added:
        st.success(f"Added {added} meeting(s) to the vault.")

vault = st.session_state.meeting_vault
stats = memory_stats(vault)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Meetings", stats["meetings"]); c2.metric("Decisions", stats["decisions"]); c3.metric("Actions", stats["actions"]); c4.metric("Open risks", stats["risks"])

if not vault:
    st.info("The Memory Vault is empty. Analyze audio in the Analyze Audio page or import meeting JSON files here.")
    st.stop()

st.caption("Vault: " + " · ".join(m.get("title", "Meeting") for m in vault))

q = st.text_input("Ask across all meetings", placeholder="What did we decide about the launch? / analytics / support / deadline...")
if q:
    results = meeting_search(vault, q)
    if not results:
        st.info("No matching evidence found.")
    for r in results:
        st.markdown(f"<div class='card'><div class='kind'>{r['kind']} · {r['meeting']} · {r['timestamp']}</div><strong>{r['speaker']}</strong><div class='small'>{r['text']}</div></div>", unsafe_allow_html=True)

st.divider()
t1, t2, t3 = st.tabs(["Recurring blockers", "Decision drift", "Topics"])
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
    topics = build_topic_index(vault)
    if topics:
        st.dataframe([{"topic": t, "mentions": n} for t, n in topics], use_container_width=True, hide_index=True)

st.divider()
vault_json = json.dumps({"meetings": vault}, indent=2, ensure_ascii=False)
st.download_button("Export Memory Vault", vault_json, "meetinglens_memory_vault.json", "application/json", use_container_width=True)
if st.button("Clear in-session vault", use_container_width=True):
    st.session_state.meeting_vault = []
    st.rerun()

st.caption("Memory Vault is session-based on the free deployment. Export it to keep a portable copy between restarts.")
