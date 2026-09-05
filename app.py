from __future__ import annotations

import json
import re

import pandas as pd
import plotly.express as px
import streamlit as st
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

st.set_page_config(page_title="MeetingLens AI", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
HERO_IMAGE = "https://images.unsplash.com/photo-1769739576456-0aefcff3f4b9?auto=format&fit=crop&fm=jpg&q=86&w=2200"

CSS = r'''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');
:root{--bg:#090b0e;--panel:rgba(18,22,26,.78);--line:rgba(255,255,255,.09);--text:#f5f4ef;--muted:#9da4a7;--coral:#ff6b57;--amber:#ffc857;--mint:#62e6b7;--ice:#a7d7ff}
html,body,[class*=css]{font-family:'DM Sans',sans-serif}.stApp{background:radial-gradient(circle at 11% 6%,rgba(255,107,87,.14),transparent 25%),radial-gradient(circle at 86% 10%,rgba(255,200,87,.09),transparent 23%),radial-gradient(circle at 60% 90%,rgba(98,230,183,.06),transparent 30%),linear-gradient(180deg,#080a0c 0%,#0b0e11 58%,#090b0e 100%);color:var(--text)}[data-testid="stHeader"]{background:transparent}.block-container{max-width:1500px;padding-top:1.25rem;padding-bottom:5rem}[data-testid="stSidebar"]{background:linear-gradient(180deg,#0c0f12 0%,#0a0d10 100%);border-right:1px solid var(--line)}
.ml-eyebrow{font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;font-weight:800;color:#c3c8c8}.ml-muted{color:var(--muted);font-size:.85rem;line-height:1.6}.ml-sep{height:1px;background:linear-gradient(90deg,var(--line),transparent);margin:1.1rem 0}.ml-brand{display:flex;align-items:center;gap:.75rem;margin:.15rem 0 1.35rem}.ml-logo{width:42px;height:42px;border-radius:14px;display:grid;place-items:center;color:#111;background:linear-gradient(145deg,var(--amber),var(--coral));font-weight:900;font-family:'Plus Jakarta Sans';box-shadow:0 14px 40px rgba(255,107,87,.22)}.ml-name{font-family:'Plus Jakarta Sans';font-weight:800;font-size:1.08rem;letter-spacing:-.03em}.ml-name span{color:var(--coral)}.ml-side-card{border:1px solid var(--line);background:linear-gradient(180deg,rgba(255,255,255,.035),rgba(255,255,255,.018));border-radius:18px;padding:1rem;margin-top:.9rem}.ml-side-label{font-size:.68rem;text-transform:uppercase;letter-spacing:.12em;color:#6f787d;font-weight:800}.ml-side-value{font-weight:700;margin-top:.28rem;font-size:.88rem}.ml-status{display:flex;align-items:center;gap:.5rem;color:#bdf6df;font-size:.78rem;font-weight:700}.ml-status-dot{width:8px;height:8px;border-radius:50%;background:var(--mint);box-shadow:0 0 0 0 rgba(98,230,183,.35);animation:mlpulse 2s infinite}@keyframes mlpulse{0%{box-shadow:0 0 0 0 rgba(98,230,183,.4)}70%{box-shadow:0 0 0 10px rgba(98,230,183,0)}100%{box-shadow:0 0 0 0 rgba(98,230,183,0)}}
.ml-topbar{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line);padding:.35rem .1rem 1rem;margin-bottom:1.25rem}.ml-pill{display:inline-flex;align-items:center;gap:.42rem;border:1px solid rgba(98,230,183,.22);background:rgba(98,230,183,.08);border-radius:999px;padding:.46rem .72rem;color:#bdf6df;font-size:.75rem;font-weight:700}
.ml-hero{position:relative;overflow:hidden;border-radius:30px;border:1px solid var(--line);min-height:520px;background:#111418;box-shadow:0 38px 100px rgba(0,0,0,.35)}.ml-hero-bg{position:absolute;inset:0;background-image:linear-gradient(90deg,rgba(7,9,11,.98) 0%,rgba(7,9,11,.90) 37%,rgba(7,9,11,.38) 68%,rgba(7,9,11,.22) 100%),url(''' + HERO_IMAGE + r''');background-size:cover;background-position:center;transform:scale(1.02);animation:mlzoom 18s ease-in-out infinite alternate}@keyframes mlzoom{from{transform:scale(1.02)}to{transform:scale(1.08)}}.ml-hero-glow{position:absolute;width:480px;height:480px;left:-160px;bottom:-260px;border-radius:50%;background:radial-gradient(circle,rgba(255,107,87,.22),transparent 68%)}.ml-hero-content{position:relative;z-index:2;max-width:700px;padding:4.35rem 3.2rem 3.2rem}.ml-kicker{display:inline-flex;align-items:center;gap:.5rem;border:1px solid rgba(255,200,87,.22);background:rgba(255,200,87,.08);color:#ffe7a7;padding:.46rem .72rem;border-radius:999px;font-size:.72rem;text-transform:uppercase;letter-spacing:.12em;font-weight:800;margin-bottom:1.25rem}.ml-hero h1{font-family:'Plus Jakarta Sans';font-size:clamp(2.55rem,5.2vw,5.7rem);line-height:.95;letter-spacing:-.072em;margin:0 0 1.25rem;max-width:760px;color:#f8f6ef}.ml-accent{background:linear-gradient(90deg,#ff7a66 0%,#ffc857 55%,#d9ffc9 100%);-webkit-background-clip:text;background-clip:text;color:transparent}.ml-hero p{font-size:1.03rem;line-height:1.75;color:#c4c9ca;max-width:610px;margin:0}.ml-chips{display:flex;flex-wrap:wrap;gap:.58rem;margin-top:1.35rem}.ml-chip{border:1px solid rgba(255,255,255,.12);background:rgba(8,10,12,.5);backdrop-filter:blur(12px);padding:.48rem .72rem;border-radius:999px;color:#e1e3e2;font-size:.77rem}.ml-float{position:absolute;right:3.1rem;z-index:3;border:1px solid rgba(255,255,255,.16);background:rgba(9,12,14,.74);backdrop-filter:blur(18px);border-radius:18px;box-shadow:0 18px 60px rgba(0,0,0,.32)}.ml-float.one{top:3.1rem;width:220px;padding:1rem;animation:mlfloat 5s ease-in-out infinite}.ml-float.two{bottom:2.7rem;width:250px;padding:1rem;animation:mlfloat 6.5s ease-in-out infinite reverse}@keyframes mlfloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}.ml-float-title{font-size:.66rem;color:#8b9599;text-transform:uppercase;letter-spacing:.11em;font-weight:800}.ml-float-main{font-family:'Plus Jakarta Sans';font-size:1.6rem;font-weight:800;letter-spacing:-.04em;margin:.22rem 0}.ml-float-note{font-size:.73rem;color:#c4c9ca}.ml-bars{display:flex;align-items:center;gap:4px;height:38px;margin-top:.55rem}.ml-bars i{width:4px;border-radius:99px;background:linear-gradient(180deg,var(--amber),var(--coral));animation:mlwave 1.2s ease-in-out infinite}.ml-bars i:nth-child(2n){animation-delay:.12s}.ml-bars i:nth-child(3n){animation-delay:.25s}@keyframes mlwave{0%,100%{height:8px;opacity:.55}50%{height:34px;opacity:1}}
.ml-kpi{position:relative;overflow:hidden;border:1px solid var(--line);border-radius:22px;padding:1.25rem;background:linear-gradient(180deg,rgba(22,26,30,.92),rgba(14,17,20,.9));min-height:135px;transition:transform .25s ease,border-color .25s ease,box-shadow .25s ease}.ml-kpi:hover{transform:translateY(-5px);border-color:rgba(255,200,87,.22);box-shadow:0 20px 50px rgba(0,0,0,.24)}.ml-kpi:after{content:'';position:absolute;width:90px;height:90px;border-radius:50%;right:-40px;top:-40px;background:radial-gradient(circle,rgba(255,107,87,.15),transparent 70%)}.ml-kpi-label{color:#8e979b;font-size:.7rem;text-transform:uppercase;letter-spacing:.11em;font-weight:800}.ml-kpi-value{font-family:'Plus Jakarta Sans';font-size:2rem;font-weight:800;letter-spacing:-.055em;margin:.42rem 0 .18rem;color:#f7f4ee}.ml-kpi-note{font-size:.76rem;color:#858e92}.ml-panel{border:1px solid var(--line);border-radius:24px;background:linear-gradient(180deg,rgba(21,25,29,.86),rgba(13,16,19,.90));padding:1.35rem;min-height:100%;box-shadow:inset 0 1px 0 rgba(255,255,255,.025)}.ml-panel-title{font-family:'Plus Jakarta Sans';font-size:1.07rem;font-weight:800;letter-spacing:-.02em}.ml-panel-sub{color:#858e92;font-size:.78rem;margin:.25rem 0 1rem}.ml-moment{position:relative;padding:.85rem .9rem .85rem 1rem;border-left:2px solid rgba(255,200,87,.5);background:rgba(255,255,255,.018);border-radius:0 14px 14px 0;margin:.7rem 0}.ml-moment:hover{background:rgba(255,255,255,.035)}.ml-moment-head{font-weight:700;font-size:.82rem}.ml-tag{display:inline-block;margin-left:.4rem;font-size:.62rem;font-weight:800;text-transform:uppercase;letter-spacing:.06em;border-radius:999px;padding:.2rem .42rem;background:rgba(255,107,87,.12);color:#ff9c8e}.ml-moment-text{color:#aab1b4;font-size:.78rem;line-height:1.55;margin-top:.3rem}.ml-decision{padding:.9rem 1rem;border:1px solid rgba(255,255,255,.06);border-radius:16px;background:rgba(255,255,255,.02);margin:.72rem 0}.ml-confidence{display:inline-flex;margin-top:.45rem;font-size:.67rem;border-radius:999px;padding:.22rem .48rem;background:rgba(98,230,183,.09);color:#a9f3d8}.ml-owner{display:inline-block;font-size:.66rem;font-weight:800;border-radius:999px;padding:.22rem .48rem;background:rgba(167,215,255,.10);color:#c6e5ff;margin-left:.35rem}.ml-risk{border-left:3px solid var(--coral);background:rgba(255,107,87,.055);padding:.82rem .9rem;border-radius:0 14px 14px 0;margin:.6rem 0}.stTabs [data-baseweb="tab-list"]{gap:.5rem;border-bottom:1px solid var(--line);padding-bottom:.55rem}.stTabs [data-baseweb="tab"]{border:1px solid var(--line);background:rgba(255,255,255,.02);border-radius:999px;padding:.5rem .9rem;color:#aeb4b6}.stTabs [aria-selected="true"]{background:linear-gradient(90deg,rgba(255,107,87,.13),rgba(255,200,87,.09))!important;border-color:rgba(255,200,87,.22)!important}[data-testid="stFileUploader"]{border:1px dashed rgba(255,200,87,.24);border-radius:16px;padding:.4rem;background:rgba(255,200,87,.025)}[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:16px;overflow:hidden}.ml-footer{text-align:center;color:#5f686c;font-size:.72rem;margin-top:3rem;padding-top:1.4rem;border-top:1px solid rgba(255,255,255,.05)}@media(max-width:1000px){.ml-hero{min-height:620px}.ml-hero-content{padding:3rem 1.6rem;max-width:100%}.ml-float.one{right:1.5rem;top:auto;bottom:8.2rem}.ml-float.two{right:1.5rem;bottom:1.8rem}.ml-hero h1{font-size:clamp(2.3rem,9vw,4.4rem)}}@media(max-width:700px){.ml-float{display:none}.ml-hero{min-height:520px}.block-container{padding-left:.8rem;padding-right:.8rem}}
</style>'''
st.markdown(CSS, unsafe_allow_html=True)

DEMO={"title":"Product Intelligence Weekly","duration_min":47,"summary":"The team aligned on launch readiness, analytics fixes, and ownership for the next release.","participants":[{"name":"Maya","talk_pct":31},{"name":"Noah","talk_pct":27},{"name":"Lina","talk_pct":23},{"name":"Omar","talk_pct":19}],"segments":[{"minute":3,"speaker":"Maya","kind":"context","text":"We need to leave today with one launch decision and clear owners.","sentiment":"neutral"},{"minute":12,"speaker":"Noah","kind":"risk","text":"The analytics patch is still blocking our final validation.","sentiment":"negative"},{"minute":21,"speaker":"Lina","kind":"decision","text":"We will keep the Friday release if analytics passes tomorrow morning.","sentiment":"positive"},{"minute":29,"speaker":"Omar","kind":"action","text":"I will own the analytics validation and post results before noon.","sentiment":"positive"},{"minute":38,"speaker":"Maya","kind":"decision","text":"Support will receive the rollout notes before the release window.","sentiment":"positive"}],"decisions":[{"title":"Keep Friday release target","detail":"Conditional on analytics validation tomorrow morning.","confidence":.94},{"title":"Share rollout notes with Support","detail":"Notes must land before the release window.","confidence":.91}],"actions":[{"task":"Validate analytics patch","owner":"Omar","due":"Tomorrow 12:00","status":"Open"},{"task":"Prepare rollout notes","owner":"Maya","due":"Friday 09:00","status":"Open"}],"risks":[{"title":"Analytics validation delay","severity":"Medium"}]}
ANALYZER=SentimentIntensityAnalyzer()
def classify(text):
    score=ANALYZER.polarity_scores(text or "")["compound"]
    return "positive" if score>=.18 else "negative" if score<=-.18 else "neutral"
def health(meeting):
    p=[x.get("talk_pct",0) for x in meeting.get("participants",[])];balance=80 if not p else max(0,100-(max(p)-min(p))*2);clarity=min(100,55+len(meeting.get("decisions",[]))*12+len(meeting.get("actions",[]))*7);seg=meeting.get("segments",[]);pos=sum(1 for x in seg if x.get("sentiment")=="positive");sentiment=int(pos/max(1,len(seg))*100);return {"overall":round(balance*.3+clarity*.45+sentiment*.25),"clarity":int(clarity),"balance":int(balance),"sentiment":sentiment}
def tokens(text): return {x for x in re.findall(r"[a-zA-Z0-9']+",(text or "").lower()) if len(x)>2}
def search_meeting(meeting,query):
    q=tokens(query);found=[]
    for segment in meeting.get("segments",[]):
        score=len(q & tokens(" ".join([segment.get("speaker",""),segment.get("kind",""),segment.get("text","")])))
        if score: found.append((score,segment))
    return [segment for _,segment in sorted(found,key=lambda x:-x[0])]
def load_upload(file):
    try:
        data=json.load(file)
        for segment in data.get("segments",[]): segment["sentiment"]=segment.get("sentiment") or classify(segment.get("text",""))
        return data,None
    except Exception as exc: return None,str(exc)

with st.sidebar:
    st.markdown('<div class="ml-brand"><div class="ml-logo">M</div><div class="ml-name">MeetingLens <span>AI</span></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="ml-muted">Turn every meeting into decisions, ownership and searchable memory.</div>',unsafe_allow_html=True)
    st.markdown('<div class="ml-sep"></div>',unsafe_allow_html=True)
    st.markdown('<div class="ml-side-label">Demo input</div>',unsafe_allow_html=True)
    uploaded=st.file_uploader("Upload meeting JSON",type=["json"],label_visibility="collapsed")
    st.caption("Temporary demo input · audio upload comes next")
    st.markdown('<div class="ml-side-card"><div class="ml-status"><span class="ml-status-dot"></span>AI workspace online</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="ml-side-card"><div class="ml-side-label">Architecture</div><div class="ml-side-value">Unified Streamlit app</div><div class="ml-muted" style="margin-top:.3rem">One deployment, one runtime, no frontend/backend mismatch.</div></div>',unsafe_allow_html=True)
meeting=DEMO
if uploaded:
    candidate,err=load_upload(uploaded)
    if candidate: meeting=candidate;st.sidebar.success("Meeting loaded")
    else: st.sidebar.error(f"Invalid JSON: {err}")
st.markdown('<div class="ml-topbar"><div class="ml-eyebrow">Conversation Intelligence · Workspace</div><div class="ml-pill"><span class="ml-status-dot"></span>Live analysis ready</div></div>',unsafe_allow_html=True)
tabs=st.tabs(["Overview","Meeting Analyzer","Knowledge Search","Insights"])
with tabs[0]:
    bars=''.join('<i></i>' for _ in range(18))
    st.markdown(f'''<section class="ml-hero"><div class="ml-hero-bg"></div><div class="ml-hero-glow"></div><div class="ml-hero-content"><div class="ml-kicker">✦ Decision intelligence for every conversation</div><h1>Your meetings should leave behind <span class="ml-accent">clarity.</span></h1><p>{meeting.get("summary","Turn conversations into decisions, actions and searchable knowledge.")}</p><div class="ml-chips"><span class="ml-chip">{meeting.get("title","Meeting")}</span><span class="ml-chip">{meeting.get("duration_min",0)} min</span><span class="ml-chip">{len(meeting.get("participants",[]))} speakers</span><span class="ml-chip">AI analyzed</span></div></div><div class="ml-float one"><div class="ml-float-title">Conversation pulse</div><div class="ml-bars">{bars}</div><div class="ml-float-note">Detecting shifts, decisions and risk.</div></div><div class="ml-float two"><div class="ml-float-title">Latest decision</div><div class="ml-float-main">Captured ✓</div><div class="ml-float-note">Friday release remains the target after validation.</div></div></section>''',unsafe_allow_html=True)
    st.write("");h=health(meeting);values=[("Meeting health",f"{h['overall']}/100","Clarity, balance & tone"),("Decisions",len(meeting.get("decisions",[])),"Captured commitments"),("Action items",len(meeting.get("actions",[])),"Owners & deadlines"),("Risks",len(meeting.get("risks",[])),"Needs follow-up")];cols=st.columns(4)
    for col,(label,value,note) in zip(cols,values):
        with col: st.markdown(f'<div class="ml-kpi"><div class="ml-kpi-label">{label}</div><div class="ml-kpi-value">{value}</div><div class="ml-kpi-note">{note}</div></div>',unsafe_allow_html=True)
    st.write("");left,right=st.columns([1.2,.8],gap="large")
    with left:
        st.markdown('<div class="ml-panel"><div class="ml-panel-title">Conversation timeline</div><div class="ml-panel-sub">The moments that changed the direction of the meeting.</div>',unsafe_allow_html=True)
        for segment in meeting.get("segments",[]): st.markdown(f'<div class="ml-moment"><div class="ml-moment-head">{str(segment.get("minute",0)).zfill(2)}:00 · {segment.get("speaker","Speaker")} <span class="ml-tag">{segment.get("kind","moment")}</span></div><div class="ml-moment-text">{segment.get("text","")}</div></div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with right:
        st.markdown('<div class="ml-panel"><div class="ml-panel-title">Speaker balance</div><div class="ml-panel-sub">Share of speaking time across the conversation.</div>',unsafe_allow_html=True);frame=pd.DataFrame(meeting.get("participants",[]))
        if not frame.empty:
            fig=px.pie(frame,values="talk_pct",names="name",hole=.72);fig.update_layout(height=340,margin=dict(l=0,r=0,t=0,b=0),showlegend=True,legend=dict(orientation="h",y=-.08,x=.5,xanchor="center"),paper_bgcolor="rgba(0,0,0,0)",font_color="#e7e5df");fig.update_traces(marker=dict(colors=["#ff6b57","#ffc857","#62e6b7","#a7d7ff"]));st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>',unsafe_allow_html=True)
    st.write("");left,right=st.columns(2,gap="large")
    with left:
        st.markdown('<div class="ml-panel"><div class="ml-panel-title">Decisions captured</div><div class="ml-panel-sub">What the team actually committed to.</div>',unsafe_allow_html=True)
        for decision in meeting.get("decisions",[]): st.markdown(f'<div class="ml-decision"><strong>✓ {decision.get("title","Decision")}</strong><div class="ml-moment-text">{decision.get("detail","")}</div><span class="ml-confidence">{round(float(decision.get("confidence",0))*100)}% confidence</span></div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with right:
        st.markdown('<div class="ml-panel"><div class="ml-panel-title">Action radar</div><div class="ml-panel-sub">Ownership and deadlines extracted from the discussion.</div>',unsafe_allow_html=True)
        for action in meeting.get("actions",[]): st.markdown(f'<div class="ml-decision"><strong>{action.get("task","Task")}</strong><span class="ml-owner">{action.get("owner","Unassigned")}</span><div class="ml-moment-text">Due {action.get("due","TBD")} · {action.get("status","Open")}</div></div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
with tabs[1]:
    st.markdown("## Meeting Analyzer");st.caption("Inspect the structured meeting record, decisions, actions and risks.");c1,c2=st.columns(2,gap="large")
    with c1:
        st.markdown('<div class="ml-panel"><div class="ml-panel-title">Decisions</div>',unsafe_allow_html=True)
        for decision in meeting.get("decisions",[]): st.markdown(f'<div class="ml-decision"><strong>✓ {decision.get("title","Decision")}</strong><div class="ml-moment-text">{decision.get("detail","")}</div></div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="ml-panel"><div class="ml-panel-title">Risk signals</div>',unsafe_allow_html=True);risks=meeting.get("risks",[])
        if risks:
            for risk in risks: st.markdown(f'<div class="ml-risk"><strong>{risk.get("title","Risk")}</strong><div class="ml-moment-text">Severity · {risk.get("severity","Unknown")}</div></div>',unsafe_allow_html=True)
        else: st.markdown('<div class="ml-muted">No risk signal detected in this meeting.</div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    st.write("");st.dataframe(pd.DataFrame(meeting.get("segments",[])),use_container_width=True,hide_index=True)
with tabs[2]:
    st.markdown("## Knowledge Search");st.caption("Search inside this meeting today. Cross-meeting memory comes next.");query=st.text_input("Ask about this meeting",placeholder="Example: What did we decide about the release?")
    if query:
        results=search_meeting(meeting,query)
        if not results: st.info("No matching moment found.")
        else:
            for segment in results: st.markdown(f'<div class="ml-panel"><div class="ml-panel-title">{str(segment.get("minute",0)).zfill(2)}:00 · {segment.get("speaker","Speaker")}</div><div class="ml-panel-sub">{segment.get("kind","moment")} · {segment.get("sentiment","neutral")}</div><div class="ml-moment-text">{segment.get("text","")}</div></div>',unsafe_allow_html=True)
with tabs[3]:
    st.markdown("## Meeting Insights");st.caption("A compact read on clarity, participation and conversation tone.");h=health(meeting);i1,i2,i3=st.columns(3)
    for col,label,value in [(i1,"Decision clarity",h["clarity"]),(i2,"Speaker balance",h["balance"]),(i3,"Positive tone",h["sentiment"])]:
        with col: st.markdown(f'<div class="ml-kpi"><div class="ml-kpi-label">{label}</div><div class="ml-kpi-value">{value}/100</div><div class="ml-kpi-note">MeetingLens signal</div></div>',unsafe_allow_html=True)
    st.write("");sentiment_frame=pd.DataFrame(meeting.get("segments",[]))
    if not sentiment_frame.empty and "minute" in sentiment_frame and "sentiment" in sentiment_frame:
        mapping={"negative":-1,"neutral":0,"positive":1};sentiment_frame["score"]=sentiment_frame["sentiment"].map(mapping).fillna(0);fig=px.line(sentiment_frame,x="minute",y="score",markers=True,hover_data=["speaker","text"]);fig.update_layout(height=360,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="#dfe2df",xaxis_title="Minute",yaxis_title="Conversation tone",yaxis=dict(tickvals=[-1,0,1],ticktext=["Negative","Neutral","Positive"],gridcolor="rgba(255,255,255,.06)"),xaxis=dict(gridcolor="rgba(255,255,255,.05)"),margin=dict(l=15,r=15,t=15,b=15));fig.update_traces(line=dict(color="#ffc857",width=3),marker=dict(size=9,color="#ff6b57"));st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
st.markdown('<div class="ml-footer">MeetingLens AI · Decision intelligence for modern teams</div>',unsafe_allow_html=True)
