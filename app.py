from __future__ import annotations

import json
import re

import pandas as pd
import plotly.express as px
import streamlit as st
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

st.set_page_config(page_title="MeetingLens AI", page_icon="◉", layout="wide", initial_sidebar_state="expanded")

HERO = "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&w=1900&q=90"
SECOND = "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=1600&q=88"

CSS = r'''<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root{--bg:#0d0f11;--bg2:#121518;--panel:#191d21;--text:#f2efe9;--muted:#98a0a5;--line:rgba(255,255,255,.08);--bronze:#b99764;--gold:#d5b681;--sage:#8fa79c;--steel:#8997a3;--warm:#cfc7bb}
*{box-sizing:border-box}html,body,[class*=css]{font-family:Inter,sans-serif}.stApp{color:var(--text);background:radial-gradient(circle at 8% 4%,rgba(213,182,129,.07),transparent 22%),radial-gradient(circle at 92% 18%,rgba(143,167,156,.05),transparent 25%),linear-gradient(180deg,#0b0d0f 0%,#121518 50%,#0d0f11 100%)}[data-testid=stHeader]{background:transparent}.block-container{max-width:1550px;padding-top:1rem;padding-bottom:5rem}[data-testid=stSidebar]{background:linear-gradient(180deg,#111417,#0d0f11);border-right:1px solid var(--line)}
@keyframes up{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}@keyframes drift{to{transform:translate(30px,24px) scale(1.08)}}@keyframes pulse{0%,100%{opacity:.42;box-shadow:0 0 0 0 rgba(143,167,156,.18)}50%{opacity:1;box-shadow:0 0 0 8px transparent}}@keyframes sweep{0%,58%{transform:translateX(-125%)}78%,100%{transform:translateX(125%)}}@keyframes breathe{to{background-size:112% auto}}@keyframes floaty{50%{transform:translateY(-8px)}}@keyframes wave{0%,100%{height:6px;opacity:.3}50%{height:34px;opacity:.95}}@keyframes grow{from{transform:scaleX(.05);opacity:.2}to{transform:scaleX(1);opacity:1}}@keyframes flow{to{background-position:-200% 0}}@keyframes ticker{to{transform:translateX(-50%)}}@keyframes glow{0%,100%{opacity:.25}50%{opacity:.65}}
.ambient{position:fixed;inset:0;pointer-events:none;overflow:hidden}.orb{position:absolute;border-radius:50%;filter:blur(80px);opacity:.12;animation:drift 18s ease-in-out infinite alternate}.o1{width:340px;height:340px;background:#b99764;left:-130px;top:7%}.o2{width:430px;height:430px;background:#6e8179;right:-175px;top:27%;animation-duration:24s}.o3{width:280px;height:280px;background:#74818c;left:42%;bottom:-130px;animation-duration:20s}
.brand{display:flex;align-items:center;gap:.75rem;margin:.15rem 0 1.3rem;animation:up .65s ease both}.logo{width:45px;height:45px;border-radius:15px;display:grid;place-items:center;border:1px solid rgba(213,182,129,.28);background:linear-gradient(145deg,#292e32,#171a1d);color:var(--gold);font-family:Manrope;font-weight:800;box-shadow:0 12px 34px rgba(0,0,0,.28)}.name{font-family:Manrope;font-size:1.08rem;font-weight:800;letter-spacing:-.035em}.name span{color:var(--gold)}.micro{font-size:.64rem;text-transform:uppercase;letter-spacing:.15em;color:#737b80;font-weight:700}.side{border:1px solid var(--line);background:rgba(255,255,255,.018);border-radius:17px;padding:1rem;margin-top:.85rem;transition:.25s}.side:hover{transform:translateY(-2px);border-color:rgba(213,182,129,.17)}.side strong{display:block;margin-top:.3rem;font-size:.84rem}.line{height:1px;background:linear-gradient(90deg,rgba(213,182,129,.45),transparent);margin-top:.7rem}
.top{display:flex;align-items:center;justify-content:space-between;padding:.35rem 0 1rem;border-bottom:1px solid var(--line);margin-bottom:1.1rem;animation:up .6s ease both}.eye{font-size:.68rem;text-transform:uppercase;letter-spacing:.15em;color:#7e858a;font-weight:700}.live{display:inline-flex;align-items:center;gap:.5rem;padding:.46rem .72rem;border-radius:999px;border:1px solid rgba(143,167,156,.22);background:rgba(143,167,156,.055);color:#becbc5;font-size:.72rem;font-weight:650}.dot{width:7px;height:7px;border-radius:50%;background:var(--sage);animation:pulse 2.2s infinite}
.hero{position:relative;display:grid;grid-template-columns:1.02fr .98fr;min-height:600px;overflow:hidden;border:1px solid var(--line);border-radius:34px;background:linear-gradient(135deg,#181c20,#111416);box-shadow:0 45px 120px rgba(0,0,0,.32);isolation:isolate;animation:up .8s cubic-bezier(.2,.8,.2,1) both}.hero:before{content:'';position:absolute;inset:0;background:linear-gradient(118deg,transparent 20%,rgba(255,255,255,.028) 42%,transparent 58%);transform:translateX(-125%);animation:sweep 9s ease-in-out infinite;z-index:9;pointer-events:none}.hero:after{content:'';position:absolute;width:520px;height:520px;border-radius:50%;left:-330px;bottom:-340px;border:1px solid rgba(213,182,129,.12);box-shadow:0 0 0 54px rgba(213,182,129,.018),0 0 0 108px rgba(213,182,129,.01);animation:floaty 12s ease-in-out infinite}
.hleft{position:relative;padding:4.65rem 3.6rem 3.4rem;display:flex;flex-direction:column;justify-content:center;z-index:3}.label{display:inline-flex;width:max-content;padding:.47rem .72rem;border-radius:999px;border:1px solid rgba(213,182,129,.2);background:rgba(185,151,100,.045);color:#d4bea0;font-size:.65rem;text-transform:uppercase;letter-spacing:.125em;font-weight:700;margin-bottom:1.25rem;animation:up .8s .08s ease both}.hero h1{font-family:Manrope;font-size:clamp(3rem,5.35vw,6.15rem);line-height:.905;letter-spacing:-.071em;margin:0;max-width:780px;font-weight:800;animation:up .84s .16s ease both}.hero h1 em{font-style:normal;color:var(--gold);font-weight:700;position:relative}.hero h1 em:after{content:'';position:absolute;left:0;right:0;bottom:-8px;height:1px;background:linear-gradient(90deg,var(--gold),transparent);transform-origin:left;animation:grow 1.2s .55s ease both}.hero p{font-size:1.01rem;line-height:1.8;color:#aeb4b7;max-width:620px;margin:1.4rem 0 0;animation:up .84s .24s ease both}.chips{display:flex;flex-wrap:wrap;gap:.56rem;margin-top:1.45rem;animation:up .84s .32s ease both}.chip{font-size:.72rem;color:#c7cccf;border:1px solid var(--line);border-radius:999px;padding:.46rem .68rem;background:rgba(255,255,255,.018);transition:.22s}.chip:hover{border-color:rgba(213,182,129,.22);color:#e6dac7;transform:translateY(-2px)}.signal{display:flex;align-items:center;gap:.8rem;margin-top:1.8rem;animation:up .84s .4s ease both}.signal span{font-size:.63rem;text-transform:uppercase;letter-spacing:.12em;color:#747d82;font-weight:700}.sigline{height:1px;flex:1;max-width:275px;background:linear-gradient(90deg,rgba(213,182,129,.85),rgba(143,167,156,.42),transparent);background-size:200% 100%;animation:flow 4s linear infinite}
.hright{position:relative;min-height:600px;background-image:linear-gradient(180deg,rgba(14,16,18,.03),rgba(14,16,18,.75)),url('''+HERO+r''');background-size:104% auto;background-position:center;overflow:hidden;animation:breathe 18s ease-in-out infinite alternate}.hright:after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,#181c20 0%,rgba(24,28,32,.32) 18%,transparent 45%)}.float{position:absolute;z-index:4;border:1px solid rgba(255,255,255,.11);background:rgba(16,18,20,.72);backdrop-filter:blur(18px);box-shadow:0 20px 58px rgba(0,0,0,.3);border-radius:20px;padding:1rem 1.05rem;animation:floaty 6s ease-in-out infinite}.f1{top:2rem;right:2rem;width:210px}.f2{top:9.3rem;right:3.8rem;width:178px;animation-delay:-2.2s}.f3{bottom:2rem;left:2rem;right:2rem;animation-duration:7.5s;animation-delay:-1.4s}.flabel{font-size:.59rem;text-transform:uppercase;letter-spacing:.12em;color:#7e868b;font-weight:700}.fvalue{font-family:Manrope;font-size:1.36rem;font-weight:800;letter-spacing:-.045em;margin-top:.24rem}.fnote{font-size:.71rem;color:#aeb4b7;margin-top:.22rem}.wave{display:flex;align-items:center;gap:4px;height:40px;margin-top:.48rem}.wave i{display:block;width:3px;border-radius:99px;background:linear-gradient(180deg,var(--gold),var(--sage));animation:wave 1.7s ease-in-out infinite;opacity:.8}.wave i:nth-child(2n){animation-delay:.14s}.wave i:nth-child(3n){animation-delay:.29s}.wave i:nth-child(5n){animation-delay:.41s}
.ticker{overflow:hidden;border:1px solid var(--line);border-radius:16px;background:rgba(255,255,255,.014);margin:1rem 0 1.25rem}.track{display:flex;width:max-content;gap:2.6rem;padding:.68rem 1rem;animation:ticker 30s linear infinite}.track span{white-space:nowrap;font-size:.66rem;color:#7e868b;letter-spacing:.08em;text-transform:uppercase}.track b{color:#c9b38d;font-weight:700}.track i{font-style:normal;color:#a7b4ae;margin-left:.35rem}.section{margin:1.5rem 0 .82rem;animation:up .72s ease both}.section h3{font-family:Manrope;margin:0;font-size:1.16rem;letter-spacing:-.03em}.section p{margin:.25rem 0 0;color:#7f878c;font-size:.76rem}.idx{font-size:.63rem;letter-spacing:.15em;text-transform:uppercase;color:#737b80;font-weight:700}
.kpi{position:relative;overflow:hidden;border:1px solid var(--line);border-radius:21px;padding:1.22rem;min-height:145px;background:linear-gradient(180deg,rgba(28,32,36,.92),rgba(20,23,26,.95));transition:.28s;animation:up .68s ease both}.kpi:hover{transform:translateY(-6px);border-color:rgba(213,182,129,.2);box-shadow:0 22px 58px rgba(0,0,0,.25)}.kpi:after{content:'';position:absolute;inset:0;background:linear-gradient(115deg,transparent 24%,rgba(255,255,255,.035) 48%,transparent 68%);transform:translateX(-130%);transition:.85s}.kpi:hover:after{transform:translateX(130%)}.kl{font-size:.63rem;text-transform:uppercase;letter-spacing:.12em;color:#7f878c;font-weight:700}.kv{font-family:Manrope;font-size:2.08rem;font-weight:800;letter-spacing:-.058em;margin:.4rem 0 .18rem}.kn{font-size:.74rem;color:#8e969b}.badge{position:absolute;right:1rem;top:1rem;width:7px;height:7px;border-radius:50%;background:var(--bronze);box-shadow:0 0 0 5px rgba(185,151,100,.055)}.meter{height:3px;border-radius:99px;background:rgba(255,255,255,.05);overflow:hidden;margin-top:.84rem}.meter span{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--bronze),var(--sage));transform-origin:left;animation:grow 1.25s .2s ease both}
.story{display:grid;grid-template-columns:repeat(5,1fr);gap:.75rem;margin:1.15rem 0 1.35rem}.step{position:relative;border:1px solid var(--line);background:rgba(255,255,255,.015);border-radius:18px;padding:1rem;min-height:122px;transition:.25s;overflow:hidden}.step:hover{transform:translateY(-4px);border-color:rgba(213,182,129,.18)}.step:before{content:'';position:absolute;left:0;right:0;top:0;height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent);opacity:.25;animation:glow 3s ease-in-out infinite}.snum{font-size:.58rem;color:#6f787d;letter-spacing:.13em}.stitle{font-family:Manrope;font-size:.9rem;font-weight:750;margin-top:.45rem}.snote{font-size:.69rem;color:#858e93;line-height:1.45;margin-top:.25rem}
.panel{position:relative;overflow:hidden;border:1px solid var(--line);border-radius:23px;background:linear-gradient(180deg,rgba(25,29,33,.86),rgba(20,23,26,.9));padding:1.35rem;box-shadow:inset 0 1px 0 rgba(255,255,255,.02);animation:up .76s ease both}.pt{font-family:Manrope;font-size:1.03rem;font-weight:760;letter-spacing:-.025em}.ps{font-size:.75rem;color:#858d92;margin:.26rem 0 1rem}.moment{display:grid;grid-template-columns:60px 1fr;gap:.82rem;padding:.9rem .18rem;border-bottom:1px solid rgba(255,255,255,.055);transition:.22s}.moment:last-child{border-bottom:0}.moment:hover{padding-left:.55rem;background:linear-gradient(90deg,rgba(185,151,100,.035),transparent)}.time{font-size:.65rem;color:var(--gold);padding-top:.18rem;font-weight:700}.mh{font-size:.82rem;font-weight:650}.tag{display:inline-block;font-size:.55rem;text-transform:uppercase;letter-spacing:.07em;border:1px solid rgba(185,151,100,.16);background:rgba(185,151,100,.05);color:#cbb18b;padding:.18rem .38rem;border-radius:999px;margin-left:.32rem}.mt{font-size:.76rem;line-height:1.58;color:#9ea5aa;margin-top:.24rem}.decision{padding:.9rem .96rem;margin:.72rem 0;border-radius:16px;background:rgba(255,255,255,.015);border:1px solid rgba(255,255,255,.055);transition:.22s}.decision:hover{transform:translateX(4px);border-color:rgba(213,182,129,.16)}.conf,.owner{display:inline-flex;font-size:.57rem;margin-top:.45rem;padding:.2rem .4rem;border-radius:999px;border:1px solid rgba(143,167,156,.14);color:#b8c9c1;background:rgba(143,167,156,.055)}.owner{margin-left:.35rem;border-color:rgba(137,151,163,.13);color:#b8c0c8;background:rgba(137,151,163,.055)}.confidencebar{height:3px;background:rgba(255,255,255,.045);border-radius:99px;margin-top:.6rem;overflow:hidden}.confidencebar span{height:100%;display:block;background:linear-gradient(90deg,var(--bronze),var(--gold));animation:grow 1.1s ease both;transform-origin:left}.risk{display:flex;justify-content:space-between;gap:1rem;padding:.78rem .15rem;border-bottom:1px solid rgba(255,255,255,.05)}.risk:last-child{border-bottom:0}.sev{font-size:.56rem;text-transform:uppercase;letter-spacing:.09em;color:#c5b08d;border:1px solid rgba(185,151,100,.15);border-radius:999px;padding:.2rem .4rem}
.visual{position:relative;min-height:360px;border-radius:23px;overflow:hidden;background-image:linear-gradient(180deg,rgba(14,16,18,.05),rgba(14,16,18,.85)),url('''+SECOND+r''');background-size:103% auto;background-position:center;animation:breathe 18s ease-in-out infinite alternate}.visual:after{content:'';position:absolute;inset:0;background:linear-gradient(115deg,transparent 20%,rgba(255,255,255,.025) 47%,transparent 68%);transform:translateX(-120%);animation:sweep 10s ease-in-out infinite}.vcopy{position:absolute;z-index:2;left:1.3rem;right:1.3rem;bottom:1.2rem}.vbig{font-family:Manrope;font-size:1.55rem;font-weight:800;letter-spacing:-.045em;line-height:1.08}.vnote{font-size:.75rem;color:#b8bdc0;margin-top:.4rem}.memory{display:grid;grid-template-columns:1.1fr .9fr;gap:1rem;margin-top:1rem}.quote{border-left:1px solid rgba(213,182,129,.28);padding-left:1rem}.qbig{font-family:Manrope;font-size:1.28rem;font-weight:760;line-height:1.2}.qnote{font-size:.73rem;color:#8f979c;margin-top:.45rem}
.stTabs [data-baseweb=tab-list]{gap:.45rem;border-bottom:1px solid var(--line);padding-bottom:.55rem}.stTabs [data-baseweb=tab]{font-size:.69rem;border-radius:10px;padding:.48rem .8rem;background:rgba(255,255,255,.018);border:1px solid var(--line);color:#9da4a8;transition:.2s}.stTabs [data-baseweb=tab]:hover{border-color:rgba(213,182,129,.14)}.stTabs [aria-selected=true]{background:rgba(185,150,98,.09)!important;color:#d6c5aa!important;border-color:rgba(185,150,98,.2)!important}[data-testid=stFileUploader]{border:1px dashed rgba(208,176,122,.18);border-radius:16px;padding:.3rem;background:rgba(185,150,98,.018)}[data-testid=stDataFrame]{border:1px solid var(--line);border-radius:16px;overflow:hidden}.footer{text-align:center;color:#596065;font-size:.64rem;margin-top:3rem;padding-top:1.2rem;border-top:1px solid rgba(255,255,255,.045)}
@media(max-width:1050px){.hero{grid-template-columns:1fr}.hright{min-height:440px}.hleft{padding:3.2rem 1.7rem}.story{grid-template-columns:repeat(2,1fr)}.memory{grid-template-columns:1fr}}@media(max-width:700px){.float.f1,.float.f2{display:none}.story{grid-template-columns:1fr}.block-container{padding-left:.75rem;padding-right:.75rem}}
</style>'''
st.markdown(CSS, unsafe_allow_html=True)
st.markdown('<div class="ambient"><span class="orb o1"></span><span class="orb o2"></span><span class="orb o3"></span></div>', unsafe_allow_html=True)

DEMO={"title":"Product Intelligence Weekly","duration_min":47,"summary":"The team aligned on launch readiness, analytics fixes, and ownership for the next release.","participants":[{"name":"Maya","talk_pct":31},{"name":"Noah","talk_pct":27},{"name":"Lina","talk_pct":23},{"name":"Omar","talk_pct":19}],"segments":[{"minute":3,"speaker":"Maya","kind":"context","text":"We need to leave today with one launch decision and clear owners.","sentiment":"neutral"},{"minute":12,"speaker":"Noah","kind":"risk","text":"The analytics patch is still blocking our final validation.","sentiment":"negative"},{"minute":21,"speaker":"Lina","kind":"decision","text":"We will keep the Friday release if analytics passes tomorrow morning.","sentiment":"positive"},{"minute":29,"speaker":"Omar","kind":"action","text":"I will own the analytics validation and post results before noon.","sentiment":"positive"},{"minute":38,"speaker":"Maya","kind":"decision","text":"Support will receive the rollout notes before the release window.","sentiment":"positive"}],"decisions":[{"title":"Keep Friday release target","detail":"Conditional on analytics validation tomorrow morning.","confidence":.94},{"title":"Share rollout notes with Support","detail":"Notes must land before the release window.","confidence":.91}],"actions":[{"task":"Validate analytics patch","owner":"Omar","due":"Tomorrow 12:00","status":"Open"},{"task":"Prepare rollout notes","owner":"Maya","due":"Friday 09:00","status":"Open"}],"risks":[{"title":"Analytics validation delay","severity":"Medium"}]}
ANALYZER=SentimentIntensityAnalyzer()
def classify(text):
    score=ANALYZER.polarity_scores(text or '')['compound']
    return 'positive' if score>=.18 else 'negative' if score<=-.18 else 'neutral'
def health(meeting):
    p=[x.get('talk_pct',0) for x in meeting.get('participants',[])];balance=80 if not p else max(0,100-(max(p)-min(p))*2)
    clarity=min(100,55+len(meeting.get('decisions',[]))*12+len(meeting.get('actions',[]))*7)
    seg=meeting.get('segments',[]);pos=sum(1 for x in seg if x.get('sentiment')=='positive');sentiment=int(pos/max(1,len(seg))*100)
    return {'overall':round(balance*.3+clarity*.45+sentiment*.25),'clarity':int(clarity),'balance':int(balance),'sentiment':sentiment}
def tokens(text):
    return {x for x in re.findall(r"[a-zA-Z0-9']+",(text or '').lower()) if len(x)>2}
def search_meeting(meeting,query):
    q=tokens(query);found=[]
    for segment in meeting.get('segments',[]):
        score=len(q & tokens(' '.join([segment.get('speaker',''),segment.get('kind',''),segment.get('text','')])))
        if score: found.append((score,segment))
    return [s for _,s in sorted(found,key=lambda x:-x[0])]
def load_upload(file):
    try:
        data=json.load(file)
        for segment in data.get('segments',[]):
            segment['sentiment']=segment.get('sentiment') or classify(segment.get('text',''))
        return data,None
    except Exception as exc:
        return None,str(exc)

with st.sidebar:
    st.markdown('<div class="brand"><div class="logo">M</div><div class="name">MeetingLens <span>AI</span></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="micro">Conversation intelligence</div>',unsafe_allow_html=True)
    uploaded=st.file_uploader('Upload meeting JSON',type=['json'])
    st.markdown('<div class="side"><div class="micro">Mode</div><strong>Decision intelligence</strong><div class="line"></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="side"><div class="micro">Runtime</div><strong>Unified Streamlit app</strong></div>',unsafe_allow_html=True)
meeting=DEMO
if uploaded:
    candidate,err=load_upload(uploaded)
    if candidate:
        meeting=candidate;st.sidebar.success('Meeting loaded')
    else:
        st.sidebar.error(f'Invalid JSON: {err}')

st.markdown('<div class="top"><div class="eye">Meeting intelligence / live workspace</div><div class="live"><span class="dot"></span>engine online</div></div>',unsafe_allow_html=True)
tabs=st.tabs(['Overview','Meeting Analyzer','Knowledge Search','Insights'])

with tabs[0]:
    bars=''.join('<i></i>' for _ in range(20))
    st.markdown(f'''<div class="hero"><div class="hleft"><div class="label">◉ AI meeting intelligence</div><h1>Turn conversation into <em>clarity.</em></h1><p>{meeting.get('summary','Turn meetings into decisions, owners, risks, and searchable memory.')}</p><div class="chips"><span class="chip">{meeting.get('title','Meeting')}</span><span class="chip">{meeting.get('duration_min',0)} min</span><span class="chip">{len(meeting.get('participants',[]))} participants</span></div><div class="signal"><span>Signal detected</span><div class="sigline"></div></div></div><div class="hright"><div class="float f1"><div class="flabel">Meeting health</div><div class="fvalue">{health(meeting)['overall']}/100</div><div class="fnote">Clear, balanced, actionable</div></div><div class="float f2"><div class="flabel">Decision confidence</div><div class="fvalue">94%</div><div class="fnote">Strong commitment signal</div></div><div class="float f3"><div class="flabel">Live conversation signal</div><div class="fvalue">Decision pattern detected</div><div class="wave">{bars}</div></div></div></div>''',unsafe_allow_html=True)
    ticker=''.join([f'<span><b>{str(s.get("minute",0)).zfill(2)}:00</b><i>{s.get("speaker","Speaker")}</i> — {s.get("text","")}</span>' for s in meeting.get('segments',[])])
    st.markdown(f'<div class="ticker"><div class="track">{ticker}{ticker}</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="section"><div class="idx">01 / Executive signal</div><h3>What this meeting produced</h3><p>A compact view of clarity, commitments, ownership and risk.</p></div>',unsafe_allow_html=True)
    h=health(meeting);vals=[('Meeting health',f"{h['overall']}/100",'Clarity, balance & tone',h['overall']),('Decisions',len(meeting.get('decisions',[])),'Captured commitments',82),('Action items',len(meeting.get('actions',[])),'Owners & deadlines',76),('Risks',len(meeting.get('risks',[])),'Needs follow-up',42)]
    cols=st.columns(4)
    for c,(a,b,n,pct) in zip(cols,vals):
        with c: st.markdown(f'<div class="kpi"><span class="badge"></span><div class="kl">{a}</div><div class="kv">{b}</div><div class="kn">{n}</div><div class="meter"><span style="width:{pct}%"></span></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="section"><div class="idx">02 / Intelligence flow</div><h3>From talk to institutional memory</h3><p>MeetingLens converts a raw conversation into a structured, reusable decision trail.</p></div>',unsafe_allow_html=True)
    st.markdown('<div class="story"><div class="step"><div class="snum">01</div><div class="stitle">Conversation</div><div class="snote">Capture the discussion and every speaker turn.</div></div><div class="step"><div class="snum">02</div><div class="stitle">Signal</div><div class="snote">Detect tension, commitments and important moments.</div></div><div class="step"><div class="snum">03</div><div class="stitle">Decision</div><div class="snote">Extract what the team actually agreed to do.</div></div><div class="step"><div class="snum">04</div><div class="stitle">Ownership</div><div class="snote">Attach owners, deadlines and unresolved responsibilities.</div></div><div class="step"><div class="snum">05</div><div class="stitle">Memory</div><div class="snote">Make every past decision searchable across meetings.</div></div></div>',unsafe_allow_html=True)
    c1,c2=st.columns([1.2,.8])
    with c1:
        st.markdown('<div class="panel"><div class="pt">Key moments</div><div class="ps">The moments that changed the direction of the meeting.</div>',unsafe_allow_html=True)
        for s in meeting.get('segments',[]):
            st.markdown(f'<div class="moment"><div class="time">{str(s.get("minute",0)).zfill(2)}:00</div><div><div class="mh">{s.get("speaker","Speaker")} <span class="tag">{s.get("kind","moment")}</span></div><div class="mt">{s.get("text","")}</div></div></div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="panel"><div class="pt">Speaker balance</div><div class="ps">Share of speaking time.</div>',unsafe_allow_html=True)
        frame=pd.DataFrame(meeting.get('participants',[]))
        if not frame.empty:
            fig=px.pie(frame,values='talk_pct',names='name',hole=.75,color_discrete_sequence=['#d5b681','#8fa79c','#8997a3','#cfc7bb'])
            fig.update_layout(height=330,margin=dict(l=0,r=0,t=0,b=0),showlegend=False,paper_bgcolor='rgba(0,0,0,0)',font_color='#f2efe9')
            st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
        st.markdown('</div>',unsafe_allow_html=True)

with tabs[1]:
    st.markdown('<div class="section"><div class="idx">Analyzer</div><h3>Decisions, owners and risks</h3><p>Inspect the structured intelligence extracted from the current meeting.</p></div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        st.markdown('<div class="panel"><div class="pt">Decisions captured</div><div class="ps">Commitments with confidence.</div>',unsafe_allow_html=True)
        for d in meeting.get('decisions',[]):
            conf=int(float(d.get('confidence',0))*100)
            st.markdown(f'<div class="decision"><strong>✓ {d.get("title","Decision")}</strong><div class="mt">{d.get("detail","")}</div><span class="conf">{conf}% confidence</span><div class="confidencebar"><span style="width:{conf}%"></span></div></div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="panel"><div class="pt">Action ownership</div><div class="ps">What needs to happen next.</div>',unsafe_allow_html=True)
        for x in meeting.get('actions',[]):
            st.markdown(f'<div class="decision"><strong>{x.get("task","Task")}</strong><span class="owner">{x.get("owner","Unassigned")}</span><div class="mt">Due {x.get("due","TBD")} · {x.get("status","Open")}</div></div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    st.write('')
    st.dataframe(pd.DataFrame(meeting.get('segments',[])),use_container_width=True,hide_index=True)

with tabs[2]:
    st.markdown('<div class="section"><div class="idx">Knowledge search</div><h3>Ask the meeting memory</h3><p>Search the current meeting for topics, owners, decisions and risks.</p></div>',unsafe_allow_html=True)
    q=st.text_input('Search',placeholder='e.g. analytics patch, Friday release, Support...')
    if q:
        results=search_meeting(meeting,q)
        if not results: st.info('No matching moment found.')
        for s in results:
            st.markdown(f'<div class="panel"><div class="pt">{s.get("speaker","Speaker")} · {s.get("minute",0)}:00 <span class="tag">{s.get("kind","moment")}</span></div><div class="mt">{s.get("text","")}</div></div>',unsafe_allow_html=True)
            st.write('')
    else:
        st.info('Type a topic above to search inside the meeting.')

with tabs[3]:
    st.markdown('<div class="section"><div class="idx">Insights</div><h3>Meeting intelligence at a glance</h3><p>Clarity, balance, tone and follow-through in one view.</p></div>',unsafe_allow_html=True)
    h=health(meeting)
    c1,c2,c3,c4=st.columns(4);c1.metric('Overall',f"{h['overall']}/100");c2.metric('Clarity',f"{h['clarity']}/100");c3.metric('Balance',f"{h['balance']}/100");c4.metric('Positive tone',f"{h['sentiment']}%")
    left,right=st.columns([.62,.38])
    with left:
        seg=pd.DataFrame(meeting.get('segments',[]))
        if not seg.empty:
            counts=seg['sentiment'].value_counts().rename_axis('sentiment').reset_index(name='count')
            fig=px.bar(counts,x='sentiment',y='count',color='sentiment',color_discrete_map={'positive':'#8fa79c','neutral':'#8997a3','negative':'#b99764'})
            fig.update_layout(height=360,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font_color='#f2efe9',showlegend=False)
            st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
    with right:
        st.markdown('<div class="visual"><div class="vcopy"><div class="micro">Cross-meeting memory</div><div class="vbig">A decision should not disappear when the meeting ends.</div><div class="vnote">MeetingLens turns every conversation into searchable organizational memory.</div></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="memory"><div class="panel"><div class="pt">Why it matters</div><div class="quote"><div class="qbig">“What did we decide, who owns it, and is it still unresolved?”</div><div class="qnote">This is the question MeetingLens is designed to answer across every meeting.</div></div></div><div class="panel"><div class="pt">Next intelligence layer</div><div class="ps">Audio → speakers → decisions → actions → risks → cross-meeting search.</div></div></div>',unsafe_allow_html=True)

st.markdown('<div class="footer">MEETINGLENS AI — FROM CONVERSATION TO CLARITY</div>',unsafe_allow_html=True)
