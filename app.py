from __future__ import annotations

import json
import re

import pandas as pd
import plotly.express as px
import streamlit as st
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

st.set_page_config(page_title="MeetingLens AI", page_icon="◉", layout="wide", initial_sidebar_state="expanded")

HERO_IMAGE = "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&w=1800&q=88"
SECONDARY_IMAGE = "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=1400&q=86"

CSS = r'''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@1,700&display=swap');
:root{--ink:#11110f;--ink2:#181816;--paper:#f4f0e8;--soft:#c8c4bb;--line:rgba(244,240,232,.12);--acid:#d9ff63;--rose:#ff4fa3;--mint:#79f2cc;--orange:#ff8b4d;--panel:rgba(24,24,22,.78)}
html,body,[class*=css]{font-family:Manrope,sans-serif}.stApp{color:var(--paper);background:radial-gradient(circle at 8% 12%,rgba(217,255,99,.07),transparent 22%),radial-gradient(circle at 93% 18%,rgba(255,79,163,.07),transparent 24%),linear-gradient(180deg,#0d0d0c,#121210 50%,#0e0e0d)}[data-testid="stHeader"]{background:transparent}.block-container{max-width:1540px;padding-top:1.15rem;padding-bottom:5rem}[data-testid="stSidebar"]{background:#0a0a09;border-right:1px solid rgba(244,240,232,.09)}
.ml-brand{display:flex;align-items:center;gap:.8rem;margin:.15rem 0 1.3rem}.ml-logo{width:44px;height:44px;border-radius:50%;display:grid;place-items:center;background:var(--acid);color:#111;font-weight:900;box-shadow:0 0 0 6px rgba(217,255,99,.06),0 16px 40px rgba(217,255,99,.1)}.ml-name{font-size:1.08rem;font-weight:800;letter-spacing:-.04em}.ml-name span{font-family:'Playfair Display',serif;font-style:italic;color:var(--rose);font-size:1.15rem}.ml-kicker-small{font-family:'DM Mono';text-transform:uppercase;letter-spacing:.12em;font-size:.65rem;color:#7f7d76}.ml-side-card{border:1px solid var(--line);background:rgba(255,255,255,.025);border-radius:18px;padding:1rem;margin-top:.85rem}.ml-side-card strong{display:block;margin-top:.3rem;font-size:.86rem}.ml-side-pulse{height:5px;border-radius:99px;background:linear-gradient(90deg,var(--acid),var(--rose),var(--mint));background-size:200% 100%;animation:flow 4s linear infinite;margin-top:.65rem}@keyframes flow{to{background-position:-200% 0}}
.ml-topbar{display:flex;align-items:center;justify-content:space-between;padding:.35rem 0 1rem;border-bottom:1px solid var(--line);margin-bottom:1rem}.ml-eyebrow{font-family:'DM Mono';font-size:.7rem;text-transform:uppercase;letter-spacing:.14em;color:#8f8c84}.ml-live{display:inline-flex;align-items:center;gap:.5rem;border:1px solid rgba(217,255,99,.28);background:rgba(217,255,99,.07);padding:.48rem .72rem;border-radius:999px;color:#e9ff9e;font-size:.74rem;font-weight:700}.ml-dot{width:7px;height:7px;border-radius:50%;background:var(--acid);animation:pulse 1.8s infinite}@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(217,255,99,.4)}70%{box-shadow:0 0 0 9px rgba(217,255,99,0)}100%{box-shadow:0 0 0 0 rgba(217,255,99,0)}}
.ml-hero{position:relative;display:grid;grid-template-columns:1.15fr .85fr;min-height:560px;border-radius:34px;overflow:hidden;border:1px solid var(--line);background:#11110f;box-shadow:0 45px 120px rgba(0,0,0,.35)}.ml-hero-left{position:relative;padding:4.2rem 3.4rem 3.2rem;display:flex;flex-direction:column;justify-content:center;z-index:2}.ml-hero-left:before{content:'';position:absolute;width:420px;height:420px;border-radius:50%;left:-260px;top:-170px;border:70px solid rgba(217,255,99,.055);animation:spin 24s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}.ml-label{display:inline-flex;width:max-content;align-items:center;gap:.55rem;font-family:'DM Mono';font-size:.67rem;text-transform:uppercase;letter-spacing:.13em;padding:.47rem .68rem;border:1px solid rgba(217,255,99,.25);border-radius:999px;color:#eaff9a;background:rgba(217,255,99,.055);margin-bottom:1.1rem}.ml-hero h1{font-size:clamp(3rem,5.6vw,6.5rem);line-height:.87;letter-spacing:-.075em;margin:0;max-width:780px;font-weight:800}.ml-hero h1 em{font-family:'Playfair Display',serif;font-weight:700;color:var(--rose)}.ml-hero p{font-size:1.03rem;line-height:1.75;color:#bdb9b0;max-width:610px;margin:1.35rem 0 0}.ml-chips{display:flex;flex-wrap:wrap;gap:.55rem;margin-top:1.4rem}.ml-chip{font-size:.74rem;color:#dfdbd2;border:1px solid var(--line);border-radius:999px;padding:.45rem .67rem;background:rgba(255,255,255,.025)}.ml-hero-right{position:relative;min-height:560px;background-image:linear-gradient(180deg,rgba(10,10,9,.05),rgba(10,10,9,.7)),url(''' + HERO_IMAGE + r''');background-size:cover;background-position:center;overflow:hidden}.ml-hero-right:after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,#11110f 0%,transparent 22%)}.ml-orbit{position:absolute;right:-120px;top:-110px;width:360px;height:360px;border:1px solid rgba(244,240,232,.22);border-radius:50%;z-index:3;animation:orbit 13s ease-in-out infinite alternate}@keyframes orbit{to{transform:translate(-30px,25px) rotate(25deg)}}.ml-glass{position:absolute;z-index:4;left:2rem;right:2rem;bottom:2rem;border-radius:24px;padding:1.1rem 1.15rem;background:rgba(13,13,12,.72);backdrop-filter:blur(18px);border:1px solid rgba(244,240,232,.16);box-shadow:0 18px 60px rgba(0,0,0,.34)}.ml-glass-title{font-family:'DM Mono';font-size:.65rem;text-transform:uppercase;letter-spacing:.13em;color:#99968f}.ml-glass-main{font-size:1.12rem;font-weight:800;line-height:1.3;margin:.42rem 0}.ml-wave{display:flex;align-items:center;gap:4px;height:42px}.ml-wave i{display:block;width:4px;border-radius:99px;background:linear-gradient(180deg,var(--acid),var(--rose));animation:wave 1.15s ease-in-out infinite}.ml-wave i:nth-child(2n){animation-delay:.12s}.ml-wave i:nth-child(3n){animation-delay:.23s}@keyframes wave{0%,100%{height:7px;opacity:.45}50%{height:37px;opacity:1}}
.ml-marquee{overflow:hidden;margin:1rem 0 1.1rem;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:.72rem 0}.ml-track{display:flex;gap:2.1rem;width:max-content;animation:marquee 22s linear infinite;font-family:'DM Mono';font-size:.67rem;text-transform:uppercase;letter-spacing:.12em;color:#8e8b83}.ml-track b{color:var(--acid);font-weight:500}@keyframes marquee{to{transform:translateX(-50%)}}
.ml-kpi{position:relative;overflow:hidden;border:1px solid var(--line);border-radius:24px;padding:1.2rem 1.22rem;min-height:140px;background:linear-gradient(180deg,rgba(30,30,27,.86),rgba(19,19,17,.88));transition:.25s ease}.ml-kpi:hover{transform:translateY(-6px) rotate(-.4deg);border-color:rgba(217,255,99,.28);box-shadow:0 20px 60px rgba(0,0,0,.28)}.ml-kpi:before{content:'';position:absolute;right:-18px;bottom:-30px;width:100px;height:100px;border-radius:50%;background:rgba(255,79,163,.06)}.ml-kpi-label{font-family:'DM Mono';font-size:.65rem;text-transform:uppercase;letter-spacing:.12em;color:#85827b}.ml-kpi-value{font-size:2.15rem;font-weight:800;letter-spacing:-.065em;margin:.38rem 0 .15rem}.ml-kpi-note{font-size:.76rem;color:#908d86}.ml-kpi-badge{position:absolute;right:1rem;top:1rem;width:9px;height:9px;border-radius:50%;background:var(--acid);box-shadow:0 0 0 5px rgba(217,255,99,.06)}
.ml-panel{border:1px solid var(--line);border-radius:26px;background:rgba(24,24,22,.76);padding:1.35rem;box-shadow:inset 0 1px 0 rgba(255,255,255,.025)}.ml-panel-title{font-size:1.08rem;font-weight:800;letter-spacing:-.025em}.ml-panel-sub{font-size:.77rem;color:#8e8b84;margin:.25rem 0 1rem}.ml-moment{display:grid;grid-template-columns:60px 1fr;gap:.85rem;padding:.86rem .2rem;border-bottom:1px solid rgba(244,240,232,.07)}.ml-moment:last-child{border-bottom:0}.ml-time{font-family:'DM Mono';font-size:.67rem;color:var(--acid);padding-top:.2rem}.ml-moment-head{font-size:.84rem;font-weight:700}.ml-tag{font-family:'DM Mono';font-size:.57rem;text-transform:uppercase;letter-spacing:.08em;border:1px solid rgba(255,79,163,.25);background:rgba(255,79,163,.07);color:#ff9bcb;padding:.17rem .38rem;border-radius:999px;margin-left:.35rem}.ml-moment-text{font-size:.77rem;line-height:1.55;color:#a9a69f;margin-top:.25rem}.ml-decision{padding:.9rem 1rem;margin:.7rem 0;border-radius:17px;background:rgba(255,255,255,.022);border:1px solid rgba(244,240,232,.07)}.ml-confidence{display:inline-flex;font-family:'DM Mono';font-size:.58rem;margin-top:.45rem;padding:.2rem .4rem;border-radius:999px;color:#dfffa0;background:rgba(217,255,99,.07);border:1px solid rgba(217,255,99,.15)}.ml-owner{display:inline-block;font-family:'DM Mono';font-size:.58rem;margin-left:.35rem;padding:.18rem .4rem;border-radius:999px;background:rgba(121,242,204,.08);color:#a8f6de;border:1px solid rgba(121,242,204,.15)}.ml-visual{position:relative;min-height:330px;border-radius:24px;overflow:hidden;background-image:linear-gradient(180deg,rgba(10,10,9,.1),rgba(10,10,9,.78)),url(''' + SECONDARY_IMAGE + r''');background-size:cover;background-position:center}.ml-visual-copy{position:absolute;left:1.25rem;right:1.25rem;bottom:1.2rem}.ml-visual-big{font-size:1.55rem;font-weight:800;letter-spacing:-.045em;line-height:1.05}.ml-visual-note{font-size:.76rem;color:#c4c0b6;margin-top:.4rem}.stTabs [data-baseweb="tab-list"]{gap:.55rem;border-bottom:1px solid var(--line);padding-bottom:.6rem}.stTabs [data-baseweb="tab"]{font-family:'DM Mono';font-size:.68rem;letter-spacing:.05em;border-radius:999px;padding:.5rem .85rem;background:rgba(255,255,255,.025);border:1px solid var(--line);color:#aaa79f}.stTabs [aria-selected="true"]{background:var(--acid)!important;color:#111!important;border-color:var(--acid)!important}[data-testid="stFileUploader"]{border:1px dashed rgba(217,255,99,.25);border-radius:18px;padding:.35rem;background:rgba(217,255,99,.025)}[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:18px;overflow:hidden}.ml-footer{text-align:center;color:#5f5d57;font-family:'DM Mono';font-size:.64rem;margin-top:3rem;padding-top:1.2rem;border-top:1px solid rgba(244,240,232,.06)}@media(max-width:1000px){.ml-hero{grid-template-columns:1fr}.ml-hero-right{min-height:420px}.ml-hero-left{padding:3rem 1.6rem}.ml-hero h1{font-size:clamp(3rem,11vw,5rem)}}
</style>'''
st.markdown(CSS, unsafe_allow_html=True)

DEMO={"title":"Product Intelligence Weekly","duration_min":47,"summary":"The team aligned on launch readiness, analytics fixes, and ownership for the next release.","participants":[{"name":"Maya","talk_pct":31},{"name":"Noah","talk_pct":27},{"name":"Lina","talk_pct":23},{"name":"Omar","talk_pct":19}],"segments":[{"minute":3,"speaker":"Maya","kind":"context","text":"We need to leave today with one launch decision and clear owners.","sentiment":"neutral"},{"minute":12,"speaker":"Noah","kind":"risk","text":"The analytics patch is still blocking our final validation.","sentiment":"negative"},{"minute":21,"speaker":"Lina","kind":"decision","text":"We will keep the Friday release if analytics passes tomorrow morning.","sentiment":"positive"},{"minute":29,"speaker":"Omar","kind":"action","text":"I will own the analytics validation and post results before noon.","sentiment":"positive"},{"minute":38,"speaker":"Maya","kind":"decision","text":"Support will receive the rollout notes before the release window.","sentiment":"positive"}],"decisions":[{"title":"Keep Friday release target","detail":"Conditional on analytics validation tomorrow morning.","confidence":.94},{"title":"Share rollout notes with Support","detail":"Notes must land before the release window.","confidence":.91}],"actions":[{"task":"Validate analytics patch","owner":"Omar","due":"Tomorrow 12:00","status":"Open"},{"task":"Prepare rollout notes","owner":"Maya","due":"Friday 09:00","status":"Open"}],"risks":[{"title":"Analytics validation delay","severity":"Medium"}]}
ANALYZER=SentimentIntensityAnalyzer()
def classify(text):
    score=ANALYZER.polarity_scores(text or "")["compound"]
    return "positive" if score>=.18 else "negative" if score<=-.18 else "neutral"
def health(meeting):
    p=[x.get("talk_pct",0) for x in meeting.get("participants",[])];balance=80 if not p else max(0,100-(max(p)-min(p))*2)
    clarity=min(100,55+len(meeting.get("decisions",[]))*12+len(meeting.get("actions",[]))*7)
    seg=meeting.get("segments",[]);pos=sum(1 for x in seg if x.get("sentiment")=="positive");sentiment=int(pos/max(1,len(seg))*100)
    return {"overall":round(balance*.3+clarity*.45+sentiment*.25),"clarity":int(clarity),"balance":int(balance),"sentiment":sentiment}
def tokens(text): return {x for x in re.findall(r"[a-zA-Z0-9']+",(text or "").lower()) if len(x)>2}
def search_meeting(meeting,query):
    q=tokens(query);found=[]
    for segment in meeting.get("segments",[]):
        score=len(q & tokens(" ".join([segment.get("speaker",""),segment.get("kind",""),segment.get("text","")])))
        if score: found.append((score,segment))
    return [s for _,s in sorted(found,key=lambda x:-x[0])]
def load_upload(file):
    try:
        data=json.load(file)
        for segment in data.get("segments",[]): segment["sentiment"]=segment.get("sentiment") or classify(segment.get("text",""))
        return data,None
    except Exception as exc: return None,str(exc)

with st.sidebar:
    st.markdown('<div class="ml-brand"><div class="ml-logo">M</div><div class="ml-name">MeetingLens <span>AI</span></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="ml-kicker-small">Conversation intelligence studio</div>',unsafe_allow_html=True)
    uploaded=st.file_uploader('Upload meeting JSON',type=['json'])
    st.markdown('<div class="ml-side-card"><div class="ml-kicker-small">Mode</div><strong>Decision intelligence</strong><div class="ml-side-pulse"></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="ml-side-card"><div class="ml-kicker-small">Runtime</div><strong>Unified Streamlit app</strong></div>',unsafe_allow_html=True)
meeting=DEMO
if uploaded:
    candidate,err=load_upload(uploaded)
    if candidate: meeting=candidate; st.sidebar.success('Meeting loaded')
    else: st.sidebar.error(f'Invalid JSON: {err}')
st.markdown('<div class="ml-topbar"><div class="ml-eyebrow">Meeting intelligence / live workspace</div><div class="ml-live"><span class="ml-dot"></span>engine online</div></div>',unsafe_allow_html=True)
tabs=st.tabs(['Overview','Meeting Analyzer','Knowledge Search','Insights'])
with tabs[0]:
    bars=''.join('<i></i>' for _ in range(18))
    st.markdown(f'''<div class="ml-hero"><div class="ml-hero-left"><div class="ml-label">◉ AI meeting intelligence</div><h1>Turn talk into <em>traction.</em></h1><p>{meeting.get('summary','Turn conversations into decisions, ownership, and searchable memory.')}</p><div class="ml-chips"><span class="ml-chip">{meeting.get('title','Meeting')}</span><span class="ml-chip">{meeting.get('duration_min',0)} min</span><span class="ml-chip">{len(meeting.get('participants',[]))} participants</span></div></div><div class="ml-hero-right"><div class="ml-orbit"></div><div class="ml-glass"><div class="ml-glass-title">Conversation pulse</div><div class="ml-glass-main">Decision signal detected</div><div class="ml-wave">{bars}</div></div></div></div>''',unsafe_allow_html=True)
    st.markdown('<div class="ml-marquee"><div class="ml-track"><span><b>01</b> decisions</span><span><b>02</b> owners</span><span><b>03</b> risks</span><span><b>04</b> unresolved issues</span><span><b>05</b> meeting memory</span><span><b>01</b> decisions</span><span><b>02</b> owners</span><span><b>03</b> risks</span><span><b>04</b> unresolved issues</span><span><b>05</b> meeting memory</span></div></div>',unsafe_allow_html=True)
    h=health(meeting);vals=[('Meeting health',f"{h['overall']}/100",'Clarity, balance & tone'),('Decisions',len(meeting.get('decisions',[])),'Captured commitments'),('Action items',len(meeting.get('actions',[])),'Owners & deadlines'),('Risks',len(meeting.get('risks',[])),'Needs follow-up')]
    cols=st.columns(4)
    for c,(a,b,n) in zip(cols,vals):
        with c: st.markdown(f'<div class="ml-kpi"><span class="ml-kpi-badge"></span><div class="ml-kpi-label">{a}</div><div class="ml-kpi-value">{b}</div><div class="ml-kpi-note">{n}</div></div>',unsafe_allow_html=True)
    st.write('');c1,c2=st.columns([1.25,.75])
    with c1:
        st.markdown('<div class="ml-panel"><div class="ml-panel-title">Key moments</div><div class="ml-panel-sub">The moments that changed the meeting.</div>',unsafe_allow_html=True)
        for s in meeting.get('segments',[]): st.markdown(f'<div class="ml-moment"><div class="ml-time">{str(s.get("minute",0)).zfill(2)}:00</div><div><div class="ml-moment-head">{s.get("speaker","Speaker")} <span class="ml-tag">{s.get("kind","moment")}</span></div><div class="ml-moment-text">{s.get("text","")}</div></div></div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="ml-panel"><div class="ml-panel-title">Speaker balance</div><div class="ml-panel-sub">Share of speaking time.</div>',unsafe_allow_html=True)
        frame=pd.DataFrame(meeting.get('participants',[]))
        if not frame.empty:
            fig=px.pie(frame,values='talk_pct',names='name',hole=.74,color_discrete_sequence=['#d9ff63','#ff4fa3','#79f2cc','#ff8b4d']);fig.update_layout(height=320,margin=dict(l=0,r=0,t=0,b=0),showlegend=False,paper_bgcolor='rgba(0,0,0,0)',font_color='#f4f0e8');st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
        st.markdown('</div>',unsafe_allow_html=True)
with tabs[1]:
    st.subheader('Meeting Analyzer');st.caption('Inspect decisions, actions, risks, and transcript moments from the current meeting.')
    c1,c2=st.columns(2)
    with c1:
        st.markdown('<div class="ml-panel"><div class="ml-panel-title">Decisions captured</div><div class="ml-panel-sub">Commitments with confidence.</div>',unsafe_allow_html=True)
        for d in meeting.get('decisions',[]): st.markdown(f'<div class="ml-decision"><strong>✓ {d.get("title","Decision")}</strong><div class="ml-moment-text">{d.get("detail","")}</div><span class="ml-confidence">{round(float(d.get("confidence",0))*100)}% confidence</span></div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="ml-panel"><div class="ml-panel-title">Action radar</div><div class="ml-panel-sub">What needs to happen next.</div>',unsafe_allow_html=True)
        for x in meeting.get('actions',[]): st.markdown(f'<div class="ml-decision"><strong>{x.get("task","Task")}</strong><span class="ml-owner">{x.get("owner","Unassigned")}</span><div class="ml-moment-text">Due {x.get("due","TBD")} · {x.get("status","Open")}</div></div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(meeting.get('segments',[])),use_container_width=True,hide_index=True)
with tabs[2]:
    st.subheader('Knowledge Search');st.caption('Search the current meeting memory for topics, owners, decisions, or risks.')
    q=st.text_input('Ask the meeting memory',placeholder='e.g. analytics patch, Friday release, Support...')
    if q:
        results=search_meeting(meeting,q)
        if not results: st.info('No matching moment found.')
        for s in results: st.markdown(f'<div class="ml-panel"><div class="ml-panel-title">{s.get("speaker","Speaker")} · {s.get("minute",0)}:00 <span class="ml-tag">{s.get("kind","moment")}</span></div><div class="ml-moment-text">{s.get("text","")}</div></div>',unsafe_allow_html=True)
    else: st.info('Type a topic above to search inside the meeting.')
with tabs[3]:
    st.subheader('Insights');st.caption('A compact read on clarity, balance, tone, and follow-through.')
    h=health(meeting);c1,c2,c3,c4=st.columns(4);c1.metric('Overall',f"{h['overall']}/100");c2.metric('Clarity',f"{h['clarity']}/100");c3.metric('Balance',f"{h['balance']}/100");c4.metric('Positive tone',f"{h['sentiment']}%")
    left,right=st.columns([.65,.35])
    with left:
        seg=pd.DataFrame(meeting.get('segments',[]))
        if not seg.empty:
            counts=seg['sentiment'].value_counts().rename_axis('sentiment').reset_index(name='count');fig=px.bar(counts,x='sentiment',y='count',color='sentiment',color_discrete_map={'positive':'#d9ff63','neutral':'#79f2cc','negative':'#ff4fa3'});fig.update_layout(height=340,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font_color='#f4f0e8',showlegend=False);st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
    with right: st.markdown('<div class="ml-visual"><div class="ml-visual-copy"><div class="ml-kicker-small">Next intelligence layer</div><div class="ml-visual-big">From meeting notes to decision memory.</div><div class="ml-visual-note">Audio → speakers → decisions → actions → risks → cross-meeting search.</div></div></div>',unsafe_allow_html=True)
st.markdown('<div class="ml-footer">MEETINGLENS AI — FROM CONVERSATION TO CLARITY</div>',unsafe_allow_html=True)
