from __future__ import annotations

import json
import streamlit as st

from meetinglens_diagnostics import collect_runtime_status, readiness_score

st.set_page_config(page_title="Production Status · MeetingLens AI", page_icon="◉", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600&family=Sora:wght@400;500;600&display=swap');
html,body,[class*=css]{font-family:Inter,system-ui,sans-serif}.stApp{background:linear-gradient(180deg,#090b0e,#0e1215);color:#f2f0eb}.block-container{max-width:1280px;padding-top:2rem}.hero{border:1px solid rgba(255,255,255,.08);border-radius:28px;padding:2rem;background:radial-gradient(circle at 82% 12%,rgba(199,173,130,.11),transparent 28%),rgba(255,255,255,.018)}.hero h1{font-family:Sora;font-size:clamp(2.35rem,5vw,4.5rem);letter-spacing:-.055em;line-height:1;margin:.45rem 0}.eyebrow{font-family:'DM Mono';font-size:.66rem;letter-spacing:.14em;text-transform:uppercase;color:#c7ad82}.small{font-size:.78rem;color:#90999e}.card{border:1px solid rgba(255,255,255,.075);border-radius:18px;padding:1rem;background:rgba(255,255,255,.015);margin:.65rem 0}.ok{color:#9eb9ac}.warn{color:#d5bc91}
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class='hero'><div class='eyebrow'>Production diagnostics</div><h1>Know what is actually ready.</h1><p class='small'>Check transcription, promoted AI artifacts, Memory Vault backend, optional diarization, and hosted persistence without exposing credentials.</p></div>""", unsafe_allow_html=True)
st.write("")

check_memory = st.toggle("Test Memory Vault connection now", value=False, help="When Supabase is configured this sends one small server-side read request. No secret is displayed.")
status = collect_runtime_status(check_memory=check_memory)
score = readiness_score(status)
mem = status["memory"]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Core readiness", f"{score}%")
c2.metric("Memory mode", status.get("mode", "unknown"))
c3.metric("Workspace", mem.get("workspace_id", "default"))
c4.metric("Transcription", "Ready" if status["transcription"]["ok"] else "Unavailable")
c5.metric("AI rankers", "Ready" if status["candidate_rankers"]["ok"] else "Missing")

st.divider()
left, right = st.columns(2)
with left:
    st.subheader("Core runtime")
    st.markdown(f"<div class='card'><strong>Python {status['python']['version']}</strong><div class='small'>{status['python']['platform']}</div></div>", unsafe_allow_html=True)
    tr = status["transcription"]
    st.markdown(f"<div class='card'><strong>Whisper transcription · {'Ready' if tr['ok'] else 'Unavailable'}</strong><div class='small'>{tr['detail']}</div></div>", unsafe_allow_html=True)
    cr = status["candidate_rankers"]
    st.markdown(f"<div class='card'><strong>Decision + Action rankers · {'Ready' if cr['ok'] else 'Incomplete'}</strong><div class='small'>Decision {cr['decision']['size_kb']} KB · Action {cr['action']['size_kb']} KB · metrics {'present' if cr['metrics']['ok'] else 'missing'}</div></div>", unsafe_allow_html=True)

with right:
    st.subheader("Optional / hosted services")
    di = status["diarization"]
    st.markdown(f"<div class='card'><strong>Automatic diarization · {'Ready' if di['ok'] and di['hf_token_configured'] else 'Optional setup incomplete'}</strong><div class='small'>pyannote runtime: {di['runtime_installed']} · HF token configured: {di['hf_token_configured']}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='card'><strong>Memory Vault · {mem.get('backend','unknown')}</strong><div class='small'>Workspace: {mem.get('workspace_id','default')} · {mem.get('detail','')}</div></div>", unsafe_allow_html=True)
    if status.get("supabase_configured"):
        st.success("Hosted Memory Vault is configured. Use the connection test above to validate the table from this deployment.")
    else:
        st.info("The app is currently using runtime JSON memory. Add SUPABASE_URL + SUPABASE_SERVICE_KEY in Streamlit Secrets for durable hosted storage.")

st.divider()
st.subheader("Deployment checklist")
checks = [
    ("Core transcription runtime", status["transcription"]["ok"]),
    ("Promoted Decision/Action rankers", status["candidate_rankers"]["ok"]),
    ("Memory backend readable", status["memory"].get("ok", True)),
    ("Hosted Supabase persistence", status.get("supabase_configured", False)),
    ("Automatic diarization runtime + token", di["runtime_installed"] and di["hf_token_configured"]),
]
for label, ok in checks:
    st.write(("✅ " if ok else "◻️ ") + label)

with st.expander("Safe diagnostic JSON"):
    st.code(json.dumps(status, indent=2), language="json")

st.caption("MeetingLens never renders API keys or Hugging Face tokens in this page. Diarization remains optional for the lightweight public deployment.")
