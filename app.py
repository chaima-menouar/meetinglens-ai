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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root{--bg:#101214;--bg2:#15181b;--panel:#181c20;--panel2:#1c2126;--text:#f1efe9;--muted:#9ca3a8;--line:rgba(255,255,255,.08);--bronze:#b99662;--bronze2:#d0b07a;--sage:#8ca399;--steel:#8b98a5;--warm:#cfc7bb}
html,body,[class*=css]{font-family:Inter,sans-serif}.stApp{color:var(--text);background:radial-gradient(circle at 14% 8%,rgba(185,150,98,.06),transparent 22%),radial-gradient(circle at 84% 18%,rgba(140,163,153,.045),transparent 24%),linear-gradient(180deg,#0f1113 0%,#121518 48%,#0f1113 100%)}[data-testid="stHeader"]{background:transparent}.block-container{max-width:1500px;padding-top:1.1rem;padding-bottom:4.5rem}[data-testid="stSidebar"]{background:linear-gradient(180deg,#111316,#0d0f11);border-right:1px solid var(--line)}
.ml-brand{display:flex;align-items:center;gap:.75rem;margin:.2rem 0 1.35rem}.ml-logo{width:42px;height:42px;border-radius:14px;display:grid;place-items:center;border:1px solid rgba(208,176,122,.26);background:linear-gradient(145deg,#24282c,#171a1d);color:var(--bronze2);font-weight:800;box-shadow:0 12px 30px rgba(0,0,0,.24)}.ml-name{font-family:Manrope,sans-serif;font-size:1.05rem;font-weight:800;letter-spacing:-.03em}.ml-name span{color:var(--bronze2);font-weight:700}.ml-kicker-small{font-size:.67rem;text-transform:uppercase;letter-spacing:.14em;color:#737a80;font-weight:700}.ml-side-card{border:1px solid var(--line);background:rgba(255,255,255,.018);border-radius:16px;padding:1rem;margin-top:.85rem}.ml-side-card strong{display:block;margin-top:.3rem;font-size:.84rem;font-weight:650}.ml-side-line{height:1px;background:linear-gradient(90deg,rgba(208,176,122,.42),transparent);margin-top:.7rem}
.ml-topbar{display:flex;align-items:center;justify-content:space-between;padding:.35rem 0 1rem;border-bottom:1px solid var(--line);margin-bottom:1.1rem}.ml-eyebrow{font-size:.69rem;text-transform:uppercase;letter-spacing:.14em;color:#7e858a;font-weight:700}.ml-live{display:inline-flex;align-items:center;gap:.5rem;padding:.46rem .7rem;border-radius:999px;border:1px solid rgba(140,163,153,.22);background:rgba(140,163,153,.06);color:#bbc8c2;font-size:.73rem;font-weight:650}.ml-dot{width:7px;height:7px;border-radius:50%;background:var(--sage);animation:softpulse 2.4s ease-in-out infinite}@keyframes softpulse{0%,100%{opacity:.55;transform:scale(.9)}50%{opacity:1;transform:scale(1.1)}}
.ml-hero{position:relative;display:grid;grid-template-columns:1.08fr .92fr;min-height:530px;overflow:hidden;border:1px solid var(--line);border-radius:30px;background:linear-gradient(135deg,#171a1d,#111315);box-shadow:0 32px 90px rgba(0,0,0,.26)}.ml-hero-left{position:relative;padding:4rem 3.3rem 3.2rem;display:flex;flex-direction:column;justify-content:center;z-index:2}.ml-hero-left:after{content:'';position:absolute;width:360px;height:360px;border-radius:50%;left:-210px;bottom:-210px;border:1px solid rgba(208,176,122,.12)}.ml-label{display:inline-flex;width:max-content;align-items:center;gap:.5rem;padding:.45rem .68rem;border-radius:999px;border:1px solid rgba(208,176,122,.2);background:rgba(185,150,98,.045);color:#d2bea0;font-size:.66rem;text-transform:uppercase;letter-spacing:.12em;font-weight:700;margin-bottom:1.2rem}.ml-hero h1{font-family:Manrope,sans-serif;font-size:clamp(2.9rem,5vw,5.7rem);line-height:.93;letter-spacing:-.066em;margin:0;max-width:760px;font-weight:800}.ml-hero h1 em{font-style:normal;color:var(--bronze2);font-weight:700}.ml-hero p{font-size:1rem;line-height:1.75;color:#aeb4b7;max-width:600px;margin:1.25rem 0 0}.ml-chips{display:flex;flex-wrap:wrap;gap:.55rem;margin-top:1.35rem}.ml-chip{font-size:.73rem;color:#c7cccf;border:1px solid var(--line);border-radius:999px;padding:.45rem .66rem;background:rgba(255,255,255,.018)}.ml-hero-right{position:relative;min-height:530px;background-image:linear-gradient(180deg,rgba(15,17,19,.12),rgba(15,17,19,.72)),url(''' + HERO_IMAGE + r''');background-size:cover;background-position:center;overflow:hidden}.ml-hero-right:after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,#171a1d 0%,transparent 24%)}.ml-glass{position:absolute;z-index:4;left:2rem;right:2rem;bottom:2rem;border-radius:20px;padding:1.05rem 1.1rem;background:rgba(16,18,20,.76);backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,.11);box-shadow:0 18px 50px rgba(0,0,0,.28)}.ml-glass-title{font-size:.64rem;text-transform:uppercase;letter-spacing:.12em;color:#80878b;font-weight:700}.ml-glass-main{font-size:1.05rem;font-weight:700;line-height:1.35;margin:.4rem 0}.ml-wave{display:flex;align-items:center;gap:4px;height:36px}.ml-wave i{display:block;width:3px;border-radius:99px;background:linear-gradient(180deg,var(--bronze2),var(--sage));animation:wave 1.8s ease-in-out infinite;opacity:.8}.ml-wave i:nth-child(2n){animation-delay:.14s}.ml-wave i:nth-child(3n){animation-delay:.27s}@keyframes wave{0%,100%{height:6px;opacity:.35}50%{height:28px;opacity:.9}}
.ml-kpi{position:relative;overflow:hidden;border:1px solid var(--line);border-radius:20px;padding:1.18rem 1.2rem;min-height:132px;background:linear-gradient(180deg,rgba(27,31,35,.9),rgba(20,23,26,.92));transition:transform .2s ease,border-color .2s ease,box-shadow .2s ease}.ml-kpi:hover{transform:translateY(-3px);border-color:rgba(208,176,122,.18);box-shadow:0 14px 36px rgba(0,0,0,.2)}.ml-kpi-label{font-size:.65rem;text-transform:uppercase;letter-spacing:.11em;color:#7f878c;font-weight:700}.ml-kpi-value{font-family:Manrope,sans-serif;font-size:2rem;font-weight:800;letter-spacing:-.055em;margin:.38rem 0 .16rem}.ml-kpi-note{font-size:.75rem;color:#8e969b}.ml-kpi-badge{position:absolute;right:1rem;top:1rem;width:7px;height:7px;border-radius:50%;background:var(--bronze)}
.ml-panel{border:1px solid var(--line);border-radius:22px;background:rgba(24,28,32,.78);padding:1.3rem;box-shadow:inset 0 1px 0 rgba(255,255,255,.02)}.ml-panel-title{font-family:Manrope,sans-serif;font-size:1.02rem;font-weight:750;letter-spacing:-.02em}.ml-panel-sub{font-size:.76rem;color:#858d92;margin:.25rem 0 1rem}.ml-moment{display:grid;grid-template-columns:58px 1fr;gap:.8rem;padding:.85rem .15rem;border-bottom:1px solid rgba(255,255,255,.055)}.ml-moment:last-child{border-bottom:0}.ml-time{font-size:.66rem;color:var(--bronze2);padding-top:.18rem;font-weight:700}.ml-moment-head{font-size:.82rem;font-weight:650}.ml-tag{display:inline-block;font-size:.57rem;text-transform:uppercase;letter-spacing:.07em;border:1px solid rgba(185,150,98,.16);background:rgba(185,150,98,.055);color:#cbb18b;padding:.18rem .38rem;border-radius:999px;margin-left:.32rem}.ml-moment-text{font-size:.77rem;line-height:1.55;color:#9ea5aa;margin-top:.24rem}.ml-decision{padding:.88rem .95rem;margin:.7rem 0;border-radius:15px;background:rgba(255,255,255,.015);border:1px solid rgba(255,255,255,.055)}.ml-confidence{display:inline-flex;font-size:.59rem;margin-top:.44rem;padding:.2rem .4rem;border-radius:999px;color:#b7c8c0;background:rgba(140,163,153,.055);border:1px solid rgba(140,163,153,.14)}.ml-owner{display:inline-block;font-size:.59rem;margin-left:.35rem;padding:.18rem .4rem;border-radius:999px;background:rgba(139,152,165,.055);color:#b8c0c8;border:1px solid rgba(139,152,165,.13)}.ml-visual{position:relative;min-height:330px;border-radius:22px;overflow:hidden;background-image:linear-gradient(180deg,rgba(14,16,18,.08),rgba(14,16,18,.82)),url(''' + SECONDARY_IMAGE + r''');background-size:cover;background-position:center}.ml-visual-copy{position:absolute;left:1.2rem;right:1.2rem;bottom:1.15rem}.ml-visual-big{font-family:Manrope,sans-serif;font-size:1.45rem;font-weight:800;letter-spacing:-.04em;line-height:1.08}.ml-visual-note{font-size:.75rem;color:#b8bdc0;margin-top:.4rem}
.stTabs [data-baseweb="tab-list"]{gap:.45rem;border-bottom:1px solid var(--line);padding-bottom:.55rem}.stTabs [data-baseweb="tab"]{font-size:.69rem;border-radius:10px;padding:.48rem .78rem;background:rgba(255,255,255,.018);border:1px solid var(--line);color:#9da4a8}.stTabs [aria-selected="true"]{background:rgba(185,150,98,.09)!important;color:#d6c5aa!important;border-color:rgba(185,150,98,.2)!important}[data-testid="stFileUploader"]{border:1px dashed rgba(208,176,122,.18);border-radius:16px;padding:.3rem;background:rgba(185,150,98,.018)}[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:16px;overflow:hidden}.ml-footer{text-align:center;color:#596065;font-size:.64rem;margin-top:2.8rem;padding-top:1.2rem;border-top:1px solid rgba(255,255,255,.045)}@media(max-width:1000px){.ml-hero{grid-template-columns:1fr}.ml-hero-right{min-height:400px}.ml-hero-left{padding:3rem 1.6rem}.ml-hero h1{font-size:clamp(2.8rem,10vw,4.8rem)}}
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
    st.markdown('<div class="ml-kicker-small">Conversation intelligence</div>',unsafe_allow_html=True)
    uploaded=st.file_uploader('Upload meeting JSON',type=['json'])
    st.markdown('<div class="ml-side-card"><div class="ml-kicker-small">Mode</div><strong>Decision intelligence</strong><div class="ml-side-line"></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="ml-side-card"><div class="ml-kicker-small">Runtime</div><strong>Unified Streamlit app</strong></div>',unsafe_allow_html=True)
meeting=DEMO
if uploaded:
    candidate,err=load_upload(uploaded)
    if candidate: meeting=candidate; st.sidebar.success('Meeting loaded')
    else: st.sidebar.error(f'Invalid JSON: {err}')
st.markdown('<div class="ml-topbar"><div class="ml-eyebrow">Meeting intelligence workspace</div><div class="ml-live"><span class="ml-dot"></span>engine online</div></div>',unsafe_allow_html=True)
tabs=st.tabs(['Overview','Meeting Analyzer','Knowledge Search','Insights'])
with tabs[0]:
    bars=''.join('<i></i>' for _ in range(18))
    st.markdown(f'''<div class="ml-hero"><div class="ml-hero-left"><div class="ml-label">AI meeting intelligence</div><h1>Turn conversation into <em>clarity.</em></h1><p>{meeting.get('summary','Turn conversations into decisions, ownership, and searchable memory.')}</p><div class="ml-chips"><span class="ml-chip">{meeting.get('title','Meeting')}</span><span class="ml-chip">{meeting.get('duration_min',0)} min</span><span class="ml-chip">{len(meeting.get('participants',[]))} participants</span></div></div><div class="ml-hero-right"><div class="ml-glass"><div class="ml-glass-title">Conversation signal</div><div class="ml-glass-main">Decision patterns detected</div><div class="ml-wave">{bars}</div></div></div></div>''',unsafe_allow_html=True)
    h=health(meeting);vals=[('Meeting health',f"{h['overall']}/100",'Clarity, balance & tone'),('Decisions',len(meeting.get('decisions',[])),'Captured commitments'),('Action items',len(meeting.get('actions',[])),'Owners & deadlines'),('Risks',len(meeting.get('risks',[])),'Needs follow-up')]
    st.write('');cols=st.columns(4)
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
            fig=px.pie(frame,values='talk_pct',names='name',hole=.74,color_discrete_sequence=['#b99662','#8ca399','#8b98a5','#6f777f']);fig.update_layout(height=320,margin=dict(l=0,r=0,t=0,b=0),showlegend=False,paper_bgcolor='rgba(0,0,0,0)',font_color='#f1efe9');st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
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
            counts=seg['sentiment'].value_counts().rename_axis('sentiment').reset_index(name='count');fig=px.bar(counts,x='sentiment',y='count',color='sentiment',color_discrete_map={'positive':'#8ca399','neutral':'#8b98a5','negative':'#9b7d72'});fig.update_layout(height=340,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font_color='#f1efe9',showlegend=False);st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
    with right: st.markdown('<div class="ml-visual"><div class="ml-visual-copy"><div class="ml-kicker-small">Next intelligence layer</div><div class="ml-visual-big">From meeting notes to decision memory.</div><div class="ml-visual-note">Audio → speakers → decisions → actions → risks → cross-meeting search.</div></div></div>',unsafe_allow_html=True)
st.markdown('<div class="ml-footer">MEETINGLENS AI — FROM CONVERSATION TO CLARITY</div>',unsafe_allow_html=True)
