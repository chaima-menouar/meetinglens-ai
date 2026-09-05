from __future__ import annotations

import json
import streamlit as st
from meetinglens_auth import require_user

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

identity = require_user()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600&family=Sora:wght@400;500;600&display=swap');
html,body,[class*=css]{font-family:Inter,system-ui,sans-serif}.stApp{background:linear-gradient(180deg,#090b0e,#0e1215);color:#f2f0eb}.block-container{max-width:1320px;padding-top:2rem}.hero{border:1px solid rgba(255,255,255,.08);border-radius:28px;padding:2rem;background:radial-gradient(circle at 80% 10%,rgba(146,169,159,.11),transparent 28%),rgba(255,255,255,.018)}.hero h1{font-family:Sora;font-size:clamp(2.4rem,5vw,4.6rem);letter-spacing:-.055em;line-height:1;margin:.45rem 0}.eyebrow{font-family:'DM Mono';font-size:.66rem;letter-spacing:.14em;text-transform:uppercase;color:#c7ad82}.card{border:1px solid rgba(255,255,255,.075);border-radius:18px;padding:1rem;background:rgba(255,255,255,.015);margin:.65rem 0}.small{font-size:.76rem;color:#8e979c}.kind{font-family:'DM Mono';font-size:.58rem;letter-spacing:.08em;text-transform:uppercase;color:#c8b18d}.vault{font-family:'DM Mono';font-size:.62rem;color:#9ba4a9}
</style>
""", unsafe_allow_html=True)


def _secret(name: str) -> str:
    try:
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


store = get_memory_store(
    supabase_url=_secret("SUPABASE_URL"),
    supabase_key=_secret("SUPABASE_SERVICE_KEY") or _secret("SUPABASE_KEY"),
    supabase_table=_secret("SUPABASE_TABLE") or None,
)
if "meeting_vault" not in st.session_state:
    st.session_state.meeting_vault = store.load()

st.markdown("""<div class='hero'><div class='eyebrow'>Cross-meeting intelligence</div><h1>Turn meetings into organizational memory.</h1><p class='small'>Search across meetings, surface repeated blockers, detect decision drift, and expose execution gaps before they disappear into another meeting.</p></div>""", unsafe_allow_html=True)
st.caption(f"Memory backend · {getattr(store, 'backend', 'unknown')}")

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
        try:
            st.session_state.meeting_vault = store.replace_all(merged)
            st.success(f"Added {len(merged) - before} meeting(s) to the vault.")
        except Exception as exc:
            st.error(f"Could not persist imported meetings: {exc}")

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
    selected_index = st.selectbox(
        "Open a stored meeting",
        options=list(range(len(vault))),
        format_func=lambda i: vault[i].get("title", f"Meeting {i + 1}"),
    )
with s2:
    st.write("")
    st.write("")
    if st.button("Open in dashboard", use_container_width=True):
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
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Tracked actions", len(execution))
    e2.metric("Needs attention", len(attention))
    e3.metric("Owned + dated", len(execution) - len(attention))
    e4.metric("Done", sum(1 for x in execution if x["status"].lower() == "done"))
    if not execution:
        st.info("No action items are stored yet.")
    else:
        st.dataframe(execution, use_container_width=True, hide_index=True, column_order=["meeting", "task", "owner", "due", "status", "missing", "timestamp"])
        if attention:
            st.warning(f"{len(attention)} action item(s) are missing an owner, a deadline, or both.")

        st.markdown("#### Update execution state")
        action_choice = st.selectbox(
            "Action item",
            options=list(range(len(execution))),
            format_func=lambda i: f"{execution[i]['meeting']} · {execution[i]['task'][:80]}",
            key="execution_action_choice",
        )
        selected_action = execution[action_choice]
        with st.form("execution_update_form"):
            f1, f2, f3 = st.columns(3)
            with f1:
                owner = st.text_input("Owner", value=selected_action["owner"])
            with f2:
                due = st.text_input("Deadline", value=selected_action["due"])
            with f3:
                statuses = ["Open", "In progress", "Blocked", "Done"]
                current_status = selected_action["status"] if selected_action["status"] in statuses else "Open"
                status = st.selectbox("Status", statuses, index=statuses.index(current_status))
            submitted = st.form_submit_button("Save action update", use_container_width=True)
        if submitted:
            mi = int(selected_action["meeting_index"])
            ai = int(selected_action["action_index"])
            updated = list(vault)
            updated[mi]["actions"][ai]["owner"] = owner.strip() or "Unassigned"
            updated[mi]["actions"][ai]["due"] = due.strip() or "Not stated"
            updated[mi]["actions"][ai]["status"] = status
            try:
                st.session_state.meeting_vault = store.replace_all(updated)
                if st.session_state.get("current_meeting", {}).get("meeting_id") == updated[mi].get("meeting_id"):
                    st.session_state.current_meeting = updated[mi]
                    st.session_state.dashboard_meeting = updated[mi]
                st.success("Action state saved.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not save action update: {exc}")

with t4:
    topics = build_topic_index(vault)
    if topics:
        st.dataframe([{"topic": t, "mentions": n} for t, n in topics], use_container_width=True, hide_index=True)

st.divider()
vault_json = json.dumps({"meetings": vault}, indent=2, ensure_ascii=False)
st.download_button("Export Memory Vault", vault_json, "meetinglens_memory_vault.json", "application/json", use_container_width=True)
if st.button("Clear Memory Vault", use_container_width=True):
    try:
        store.clear()
        st.session_state.meeting_vault = []
        st.rerun()
    except Exception as exc:
        st.error(f"Could not clear Memory Vault: {exc}")

if getattr(store, "backend", "runtime-json") == "supabase":
    st.caption("Memory Vault is using the configured Supabase backend for durable hosted storage.")
else:
    st.caption("Memory Vault is persisted in the running deployment and survives browser sessions. Streamlit Community Cloud can recreate its filesystem after a reboot/redeploy, so Export Memory Vault remains the portable backup until Supabase is configured.")
