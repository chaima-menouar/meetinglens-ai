from pathlib import Path

# Patch Analyze Audio.
audio_path = Path("pages/1_Analyze_Audio.py")
audio = audio_path.read_text(encoding="utf-8")
audio = audio.replace(
    "from meetinglens_pipeline import transcribe_audio\n",
    "from meetinglens_pipeline import transcribe_audio\nfrom meetinglens_memory_store import get_memory_store\n",
    1,
)
audio = audio.replace(
    'if "meeting_vault" not in st.session_state:\n    st.session_state.meeting_vault = []\n',
    'store = get_memory_store()\nif "meeting_vault" not in st.session_state:\n    st.session_state.meeting_vault = store.load()\n',
    1,
)
old_buttons = '''    b1, b2 = st.columns(2)
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
'''
new_buttons = '''    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("Save to Memory Vault", use_container_width=True):
            vault, created = store.upsert(meeting)
            st.session_state.meeting_vault = vault
            st.success("Saved to Memory Vault." if created else "Memory Vault updated.")
    with b2:
        if st.button("Open full dashboard", use_container_width=True):
            st.session_state.dashboard_meeting = meeting
            st.switch_page("app.py")
    with b3:
        st.download_button("Download meeting JSON", data=json.dumps(meeting, indent=2, ensure_ascii=False), file_name=f"{meeting.get('title','meeting').replace(' ','_').lower()}.json", mime="application/json", use_container_width=True)
'''
if old_buttons not in audio:
    raise SystemExit("Analyze Audio action block not found")
audio = audio.replace(old_buttons, new_buttons, 1)
audio_path.write_text(audio, encoding="utf-8")

# Patch main dashboard to use session-selected/analyzed meeting before demo.
app_path = Path("app.py")
app = app_path.read_text(encoding="utf-8")
old = '''meeting=DEMO
if uploaded:
    candidate,err=load_upload(uploaded)
    if candidate:meeting=candidate;st.sidebar.success("Meeting loaded")
    else:st.sidebar.error(f"Invalid JSON: {err}")
h=health(meeting)
'''
new = '''meeting=st.session_state.get("dashboard_meeting") or st.session_state.get("current_meeting") or DEMO
if uploaded:
    candidate,err=load_upload(uploaded)
    if candidate:
        meeting=candidate
        st.session_state.dashboard_meeting=candidate
        st.sidebar.success("Meeting loaded")
    else:st.sidebar.error(f"Invalid JSON: {err}")
if meeting is not DEMO:
    st.sidebar.caption("Dashboard source · analyzed / Memory Vault meeting")
h=health(meeting)
'''
if old not in app:
    raise SystemExit("Main dashboard meeting selection block not found")
app = app.replace(old, new, 1)
app_path.write_text(app, encoding="utf-8")
print("Patched Analyze Audio and main dashboard product flow")
