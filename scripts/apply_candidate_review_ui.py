from pathlib import Path

path = Path("app.py")
text = path.read_text(encoding="utf-8")
old = '''with tabs[1]:
    st.subheader("Decisions & ownership");st.caption("What was agreed, who owns the next move, and what still needs attention.")
    c1,c2=st.columns(2)
    with c1:
        st.markdown('<div class="panel"><div class="pt">What was decided</div><div class="ps">Commitments extracted from the conversation.</div>',unsafe_allow_html=True)
        for d in meeting.get("decisions",[]):st.markdown(f'<div class="decision"><strong>{d.get("title","Decision")}</strong><div class="mt">{d.get("detail","")}</div><span class="conf">{round(float(d.get("confidence",0))*100)}% confidence</span></div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="panel"><div class="pt">Who owns what now</div><div class="ps">Follow-through starts with a named owner.</div>',unsafe_allow_html=True)
        for x in meeting.get("actions",[]):st.markdown(f'<div class="decision"><strong>{x.get("task","Task")}</strong><div class="mt">{x.get("owner","Unassigned")} · due {x.get("due","TBD")} · {x.get("status","Open")}</div></div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
'''
new = '''with tabs[1]:
    st.subheader("Decisions & ownership");st.caption("What was agreed, who owns the next move, and what still needs attention.")
    c1,c2=st.columns(2)
    with c1:
        st.markdown('<div class="panel"><div class="pt">What was decided</div><div class="ps">Commitments extracted from the conversation.</div>',unsafe_allow_html=True)
        for d in meeting.get("decisions",[]):st.markdown(f'<div class="decision"><strong>{d.get("title","Decision")}</strong><div class="mt">{d.get("detail","")}</div><span class="conf">{round(float(d.get("confidence",0))*100)}% confidence</span></div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="panel"><div class="pt">Who owns what now</div><div class="ps">Follow-through starts with a named owner.</div>',unsafe_allow_html=True)
        for x in meeting.get("actions",[]):st.markdown(f'<div class="decision"><strong>{x.get("task","Task")}</strong><div class="mt">{x.get("owner","Unassigned")} · due {x.get("due","TBD")} · {x.get("status","Open")}</div></div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)

    decision_candidates=meeting.get("decision_candidates",[])
    action_candidates=meeting.get("action_candidates",[])
    if decision_candidates or action_candidates:
        st.markdown('<div class="section"><div class="num">AI / candidate review</div><h3>Signals worth a second look</h3><p>The ranker surfaces likely evidence without silently turning uncertain language into a confirmed commitment.</p></div>',unsafe_allow_html=True)
        r1,r2=st.columns(2)
        with r1:
            st.markdown('<div class="panel"><div class="pt">Decision candidates</div><div class="ps">Ranked transcript moments · review before confirming.</div>',unsafe_allow_html=True)
            if decision_candidates:
                for x in decision_candidates:st.markdown(f'<div class="decision"><strong>#{x.get("rank","–")} · {x.get("speaker","Speaker")} · {x.get("timestamp","00:00")}</strong><div class="mt">{x.get("text","")}</div><span class="conf">candidate score {round(float(x.get("score",0))*100)}%</span></div>',unsafe_allow_html=True)
            else:st.markdown('<div class="mt">No additional decision candidates need review.</div>',unsafe_allow_html=True)
            st.markdown('</div>',unsafe_allow_html=True)
        with r2:
            st.markdown('<div class="panel"><div class="pt">Action candidates</div><div class="ps">Potential follow-through that did not match a deterministic rule.</div>',unsafe_allow_html=True)
            if action_candidates:
                for x in action_candidates:st.markdown(f'<div class="decision"><strong>#{x.get("rank","–")} · {x.get("speaker","Speaker")} · {x.get("timestamp","00:00")}</strong><div class="mt">{x.get("text","")}</div><span class="conf">candidate score {round(float(x.get("score",0))*100)}%</span></div>',unsafe_allow_html=True)
            else:st.markdown('<div class="mt">No additional action candidates need review.</div>',unsafe_allow_html=True)
            st.markdown('</div>',unsafe_allow_html=True)
'''

if old not in text:
    raise SystemExit("Expected Decisions & ownership block was not found; refusing to patch app.py")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Candidate review UI inserted into app.py")
