from __future__ import annotations

import json
import re
import pandas as pd
import plotly.express as px
import streamlit as st
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

st.set_page_config(
    page_title="MeetingLens AI",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

HERO = "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&w=1900&q=90"
SECOND = "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=1500&q=88"

CSS = r'''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');

:root{
  --bg:#0b0d0f; --bg2:#101316; --panel:#171b1f; --panel2:#1b2025;
  --text:#f3f0ea; --muted:#969da2; --line:rgba(255,255,255,.075);
  --bronze:#b99661; --gold:#d8ba83; --sage:#8ba297; --steel:#87939e;
  --ivory:#e7e0d5;
}
*{box-sizing:border-box}
html,body,[class*=css]{font-family:Manrope,sans-serif}
.stApp{
  color:var(--text);
  background:
    radial-gradient(circle at 10% 8%,rgba(216,186,131,.055),transparent 22%),
    radial-gradient(circle at 87% 20%,rgba(139,162,151,.04),transparent 25%),
    linear-gradient(180deg,#0a0c0e 0%,#101316 52%,#0b0d0f 100%);
}
[data-testid=stHeader]{background:transparent}
.block-container{max-width:1580px;padding-top:.9rem;padding-bottom:5rem}
[data-testid=stSidebar]{background:linear-gradient(180deg,#101316,#0c0e10);border-right:1px solid var(--line)}
.stTabs [data-baseweb=tab-list]{gap:.5rem;border-bottom:1px solid var(--line);padding-bottom:.55rem}
.stTabs [data-baseweb=tab]{font-size:.7rem;border-radius:12px;padding:.5rem .82rem;background:rgba(255,255,255,.018);border:1px solid var(--line);color:#9da4a8}
.stTabs [aria-selected=true]{background:rgba(185,150,97,.09)!important;color:#dcc8a9!important;border-color:rgba(185,150,97,.21)!important}
[data-testid=stFileUploader]{border:1px dashed rgba(216,186,131,.18);border-radius:16px;background:rgba(185,150,97,.015)}

@keyframes up{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@keyframes drift{to{transform:translate(40px,25px) scale(1.08)}}
@keyframes sweep{0%,60%{transform:translateX(-130%)}82%,100%{transform:translateX(130%)}}
@keyframes floaty{50%{transform:translateY(-8px)}}
@keyframes wave{0%,100%{height:6px;opacity:.28}50%{height:34px;opacity:.95}}
@keyframes ring{to{transform:rotate(360deg)}}
@keyframes meter{from{transform:scaleX(.05)}to{transform:scaleX(1)}}
@keyframes scan{0%{top:-12%}100%{top:112%}}
@keyframes marquee{to{transform:translateX(-50%)}}
@keyframes glow{0%,100%{opacity:.25}50%{opacity:.62}}

.ambient{position:fixed;inset:0;pointer-events:none;overflow:hidden;z-index:0}
.orb{position:absolute;border-radius:50%;filter:blur(85px);opacity:.09;animation:drift 22s ease-in-out infinite alternate}
.o1{width:360px;height:360px;background:#b99661;left:-130px;top:8%}
.o2{width:430px;height:430px;background:#687b72;right:-180px;top:30%;animation-duration:28s}
.o3{width:300px;height:300px;background:#6e7a84;left:43%;bottom:-140px;animation-duration:24s}

.brand{display:flex;align-items:center;gap:.76rem;margin:.15rem 0 1.25rem;animation:up .65s both}
.logo{width:46px;height:46px;border-radius:15px;display:grid;place-items:center;border:1px solid rgba(216,186,131,.26);background:linear-gradient(145deg,#292e32,#171a1d);color:var(--gold);font-family:Manrope;font-weight:800;box-shadow:0 14px 34px rgba(0,0,0,.28)}
.name{font-size:1.08rem;font-weight:800;letter-spacing:-.035em}
.name span{color:var(--gold)}
.micro{font-family:'DM Mono',monospace;font-size:.62rem;text-transform:uppercase;letter-spacing:.14em;color:#747b80}
.side{border:1px solid var(--line);background:rgba(255,255,255,.016);border-radius:17px;padding:1rem;margin-top:.85rem;transition:.25s}
.side:hover{transform:translateY(-2px);border-color:rgba(216,186,131,.16)}
.side strong{display:block;margin-top:.35rem;font-size:.84rem}
.side-line{height:1px;background:linear-gradient(90deg,rgba(216,186,131,.45),transparent);margin-top:.7rem}

.top{display:flex;align-items:center;justify-content:space-between;padding:.35rem 0 1rem;border-bottom:1px solid var(--line);margin-bottom:1rem;animation:up .6s both}
.eye{font-family:'DM Mono';font-size:.66rem;text-transform:uppercase;letter-spacing:.14em;color:#7c8489}
.live{display:inline-flex;align-items:center;gap:.5rem;padding:.46rem .72rem;border-radius:999px;border:1px solid rgba(139,162,151,.2);background:rgba(139,162,151,.05);color:#becbc5;font-size:.72rem;font-weight:650}
.dot{width:7px;height:7px;border-radius:50%;background:var(--sage);animation:glow 2s infinite}

.hero{position:relative;display:grid;grid-template-columns:1.02fr .98fr;min-height:630px;overflow:hidden;border:1px solid var(--line);border-radius:34px;background:linear-gradient(135deg,#181c20,#111416);box-shadow:0 46px 125px rgba(0,0,0,.33);isolation:isolate;animation:up .85s both}
.hero:before{content:'';position:absolute;inset:0;background:linear-gradient(120deg,transparent 18%,rgba(255,255,255,.028) 44%,transparent 58%);transform:translateX(-130%);animation:sweep 10s ease-in-out infinite;z-index:9;pointer-events:none}
.hero:after{content:'';position:absolute;inset:14px;border:1px solid rgba(255,255,255,.03);border-radius:26px;pointer-events:none;z-index:8}
.hleft{position:relative;padding:4.9rem 3.8rem 3.7rem;display:flex;flex-direction:column;justify-content:center;z-index:3}
.label{display:inline-flex;width:max-content;padding:.48rem .72rem;border-radius:999px;border:1px solid rgba(216,186,131,.2);background:rgba(185,150,97,.045);color:#d7c0a1;font-family:'DM Mono';font-size:.63rem;text-transform:uppercase;letter-spacing:.125em;margin-bottom:1.28rem;animation:up .8s .1s both}
.hero h1{font-size:clamp(3.35rem,5.5vw,6.5rem);line-height:.885;letter-spacing:-.074em;margin:0;max-width:800px;font-weight:800;animation:up .85s .17s both}
.hero h1 em{font-style:normal;color:var(--gold);font-weight:700;position:relative}
.hero h1 em:after{content:'';position:absolute;left:0;right:0;bottom:-9px;height:1px;background:linear-gradient(90deg,var(--gold),transparent);transform-origin:left;animation:meter 1.2s .72s both}
.hero p{font-size:1.02rem;line-height:1.82;color:#aeb4b7;max-width:620px;margin:1.4rem 0 0;animation:up .85s .25s both}
.chips{display:flex;flex-wrap:wrap;gap:.55rem;margin-top:1.45rem;animation:up .85s .34s both}
.chip{font-size:.72rem;color:#c7cccf;border:1px solid var(--line);border-radius:999px;padding:.46rem .68rem;background:rgba(255,255,255,.018);transition:.2s}
.chip:hover{transform:translateY(-2px);border-color:rgba(216,186,131,.2);color:#e4d8c7}
.signal{display:flex;align-items:center;gap:.8rem;margin-top:1.85rem;animation:up .85s .42s both}
.signal span{font-family:'DM Mono';font-size:.61rem;text-transform:uppercase;letter-spacing:.12em;color:#737c81}
.sigline{height:1px;flex:1;max-width:300px;background:linear-gradient(90deg,rgba(216,186,131,.82),rgba(139,162,151,.45),transparent);background-size:200% 100%;animation:sweep 5.2s linear infinite}

.hright{position:relative;min-height:630px;background-image:linear-gradient(180deg,rgba(14,16,18,.05),rgba(14,16,18,.76)),url('''+HERO+r''');background-size:106% auto;background-position:center;overflow:hidden;animation:herozoom 18s ease-in-out infinite alternate}
@keyframes herozoom{to{background-size:114% auto}}
.hright:after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,#181c20 0%,rgba(24,28,32,.32) 18%,transparent 46%)}
.scan{position:absolute;z-index:3;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(216,186,131,.34),transparent);box-shadow:0 0 24px rgba(216,186,131,.1);animation:scan 7s linear infinite}
.hud{position:absolute;z-index:4;top:2rem;left:2rem;width:136px;height:136px;border-radius:50%;display:grid;place-items:center;background:rgba(13,15,17,.54);backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,.1)}
.hud:before{content:'';position:absolute;inset:8px;border-radius:50%;border:1px dashed rgba(216,186,131,.34);animation:ring 15s linear infinite}
.hud:after{content:'';position:absolute;inset:21px;border-radius:50%;border:1px solid rgba(139,162,151,.18)}
.hud .n{font-size:1.8rem;font-weight:800}.hud .t{font-family:'DM Mono';font-size:.5rem;text-transform:uppercase;letter-spacing:.11em;color:#899196;margin-top:-4px}
.float{position:absolute;z-index:5;border:1px solid rgba(255,255,255,.11);background:rgba(16,18,20,.72);backdrop-filter:blur(18px);box-shadow:0 18px 55px rgba(0,0,0,.28);border-radius:18px;padding:1rem;animation:floaty 6s ease-in-out infinite}
.f1{top:2rem;right:2rem;width:210px}.f2{top:9.3rem;right:3.4rem;width:182px;animation-delay:-2s}.f3{bottom:2rem;left:2rem;right:2rem;animation-duration:7.5s;animation-delay:-1.4s}
.flabel{font-family:'DM Mono';font-size:.58rem;text-transform:uppercase;letter-spacing:.12em;color:#7e868b}
.fvalue{font-size:1.35rem;font-weight:800;letter-spacing:-.045em;margin-top:.24rem}
.fnote{font-size:.7rem;color:#aeb4b7;margin-top:.22rem}
.wave{display:flex;align-items:center;gap:4px;height:40px;margin-top:.45rem}
.wave i{display:block;width:3px;border-radius:99px;background:linear-gradient(180deg,var(--gold),var(--sage));animation:wave 1.7s ease-in-out infinite;opacity:.8}
.wave i:nth-child(2n){animation-delay:.14s}.wave i:nth-child(3n){animation-delay:.29s}.wave i:nth-child(5n){animation-delay:.41s}

.ticker{margin:1rem 0 1.2rem;border-top:1px solid var(--line);border-bottom:1px solid var(--line);overflow:hidden;background:rgba(255,255,255,.008)}
.ticktrack{display:flex;gap:2rem;width:max-content;padding:.72rem 0;animation:marquee 30s linear infinite}
.tick{display:flex;align-items:center;gap:.55rem;color:#7f878c;font-size:.66rem;white-space:nowrap}
.tick b{color:#c9b18d;font-weight:700}
.tinywave{display:flex;gap:2px;align-items:center;height:14px}.tinywave i{width:2px;border-radius:9px;background:#8ba297;animation:wave 1.5s infinite}.tinywave i:nth-child(2n){animation-delay:.2s}

.section{margin:1.6rem 0 .85rem;animation:up .7s both}
.idx{font-family:'DM Mono';font-size:.61rem;text-transform:uppercase;letter-spacing:.15em;color:#737b80}
.section h3{font-size:1.22rem;margin:.22rem 0 0;letter-spacing:-.03em}
.section p{font-size:.76rem;color:#7f878c;margin:.25rem 0 0}

.kpi{position:relative;overflow:hidden;border:1px solid var(--line);border-radius:21px;padding:1.2rem 1.22rem;min-height:152px;background:linear-gradient(180deg,rgba(28,32,36,.92),rgba(20,23,26,.94));transition:.28s;animation:up .7s both}
.kpi:hover{transform:translateY(-6px);border-color:rgba(216,186,131,.2);box-shadow:0 24px 58px rgba(0,0,0,.24)}
.kpi:after{content:'';position:absolute;inset:0;background:linear-gradient(115deg,transparent 24%,rgba(255,255,255,.035) 48%,transparent 68%);transform:translateX(-130%);transition:.85s}.kpi:hover:after{transform:translateX(130%)}
.kl{font-family:'DM Mono';font-size:.6rem;text-transform:uppercase;letter-spacing:.12em;color:#7f878c}.kv{font-size:2.15rem;font-weight:800;letter-spacing:-.058em;margin:.4rem 0 .18rem}.kn{font-size:.74rem;color:#8e969b}
.badge{position:absolute;right:1rem;top:1rem;width:7px;height:7px;border-radius:50%;background:var(--bronze);box-shadow:0 0 0 5px rgba(185,150,97,.05)}
.meter{height:3px;border-radius:99px;background:rgba(255,255,255,.05);overflow:hidden;margin-top:.85rem}.meter span{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--bronze),var(--sage));transform-origin:left;animation:meter 1.2s .25s both}

.story{display:grid;grid-template-columns:repeat(5,1fr);gap:.7rem;margin:1rem 0 1.2rem}
.storycard{position:relative;border:1px solid var(--line);border-radius:18px;padding:1rem;background:rgba(255,255,255,.014);min-height:125px;overflow:hidden;transition:.25s}
.storycard:hover{transform:translateY(-4px);border-color:rgba(216,186,131,.18)}
.storycard:before{content:'';position:absolute;left:0;top:0;width:100%;height:2px;background:linear-gradient(90deg,var(--bronze),transparent)}
.storynum{font-family:'DM Mono';font-size:.55rem;color:#737b80;letter-spacing:.14em;text-transform:uppercase}
.storytitle{font-weight:750;margin-top:.45rem;font-size:.95rem}.storynote{font-size:.7rem;color:#90979b;margin-top:.28rem;line-height:1.5}

.panel{position:relative;overflow:hidden;border:1px solid var(--line);border-radius:23px;background:linear-gradient(180deg,rgba(25,29,33,.86),rgba(20,23,26,.88));padding:1.35rem;box-shadow:inset 0 1px 0 rgba(255,255,255,.02);animation:up .78s both}
.pt{font-size:1.05rem;font-weight:760;letter-spacing:-.025em}.ps{font-size:.75rem;color:#858d92;margin:.26rem 0 1rem}
.moment{display:grid;grid-template-columns:60px 1fr;gap:.82rem;padding:.9rem .18rem;border-bottom:1px solid rgba(255,255,255,.055);transition:.22s}.moment:last-child{border-bottom:0}
.moment:hover{padding-left:.55rem;background:linear-gradient(90deg,rgba(185,150,97,.035),transparent)}
.time{font-family:'DM Mono';font-size:.63rem;color:var(--gold);padding-top:.18rem}.mh{font-size:.82rem;font-weight:650}
.tag{display:inline-block;font-family:'DM Mono';font-size:.54rem;text-transform:uppercase;letter-spacing:.07em;border:1px solid rgba(185,150,97,.16);background:rgba(185,150,97,.05);color:#cbb18b;padding:.18rem .38rem;border-radius:999px;margin-left:.32rem}
.mt{font-size:.76rem;line-height:1.58;color:#9ea5aa;margin-top:.24rem}
.decision{padding:.92rem .98rem;margin:.72rem 0;border-radius:16px;background:rgba(255,255,255,.015);border:1px solid rgba(255,255,255,.055);transition:.22s}.decision:hover{transform:translateX(4px);border-color:rgba(216,186,131,.16)}
.conf,.owner{display:inline-flex;font-family:'DM Mono';font-size:.56rem;margin-top:.45rem;padding:.2rem .4rem;border-radius:999px;border:1px solid rgba(139,162,151,.14);color:#b8c9c1;background:rgba(139,162,151,.055)}
.owner{margin-left:.35rem;border-color:rgba(135,147,158,.13);color:#b8c0c8;background:rgba(135,147,158,.055)}
.cbar{height:3px;border-radius:99px;background:rgba(255,255,255,.05);overflow:hidden;margin-top:.65rem}.cbar span{display:block;height:100%;background:linear-gradient(90deg,var(--bronze),var(--sage));transform-origin:left;animation:meter 1.1s .2s both}
.risk{display:flex;justify-content:space-between;gap:1rem;padding:.78rem .15rem;border-bottom:1px solid rgba(255,255,255,.05)}.risk:last-child{border-bottom:0}
.sev{font-family:'DM Mono';font-size:.55rem;text-transform:uppercase;letter-spacing:.09em;color:#c5b08d;border:1px solid rgba(185,150,97,.15);border-radius:999px;padding:.2rem .4rem}

.changegrid{display:grid;grid-template-columns:1.15fr .85fr;gap:1rem;margin-top:1rem}
.change{border:1px solid var(--line);border-radius:22px;padding:1.25rem;background:linear-gradient(180deg,rgba(28,32,36,.82),rgba(18,21,24,.88))}
.changehead{font-family:'DM Mono';font-size:.58rem;text-transform:uppercase;letter-spacing:.13em;color:#7b8388}
.changeline{display:flex;gap:.8rem;align-items:flex-start;padding:.82rem 0;border-bottom:1px solid rgba(255,255,255,.05)}.changeline:last-child{border-bottom:0}
.cnum{width:28px;height:28px;border-radius:50%;display:grid;place-items:center;border:1px solid rgba(216,186,131,.18);color:#cfb38a;font-family:'DM Mono';font-size:.58rem;flex:0 0 auto}
.ctitle{font-size:.82rem;font-weight:700}.ctext{font-size:.72rem;color:#91999d;margin-top:.22rem;line-height:1.55}

.memory{position:relative;overflow:hidden;border:1px solid var(--line);border-radius:22px;padding:1.25rem;background:linear-gradient(180deg,rgba(20,23,26,.92),rgba(14,17,20,.95))}
.memory:before{content:'';position:absolute;right:-70px;top:-70px;width:180px;height:180px;border-radius:50%;border:1px solid rgba(216,186,131,.09);box-shadow:0 0 0 26px rgba(216,186,131,.015),0 0 0 52px rgba(216,186,131,.008)}
.memq{font-size:.78rem;color:#aeb4b7;margin-top:.8rem;padding:.8rem;border:1px solid rgba(255,255,255,.06);border-radius:14px;background:rgba(255,255,255,.015)}
.mema{font-size:.75rem;color:#d7d1c8;margin-top:.7rem;line-height:1.65}
.memsrc{font-family:'DM Mono';font-size:.54rem;color:#7d858a;margin-top:.5rem}

.visual{position:relative;min-height:360px;border-radius:23px;overflow:hidden;background-image:linear-gradient(180deg,rgba(14,16,18,.06),rgba(14,16,18,.84)),url('''+SECOND+r''');background-size:103% auto;background-position:center;animation:vzoom 16s ease-in-out infinite alternate}
@keyframes vzoom{to{background-size:110% auto}}
.vcopy{position:absolute;left:1.3rem;right:1.3rem;bottom:1.2rem}.vbig{font-size:1.55rem;font-weight:800;letter-spacing:-.045em;line-height:1.08}.vnote{font-size:.74rem;color:#b9bec1;margin-top:.42rem}

.footer{text-align:center;color:#596065;font-family:'DM Mono';font-size:.61rem;margin-top:3rem;padding-top:1.2rem;border-top:1px solid rgba(255,255,255,.045)}

@media(max-width:1100px){.hero{grid-template-columns:1fr}.hright{min-height:470px}.hleft{padding:3.4rem 1.8rem}.story{grid-template-columns:1fr 1fr}.changegrid{grid-template-columns:1fr}}
@media(max-width:720px){.story{grid-template-columns:1fr}.float.f1,.float.f2{display:none}.hud{width:110px;height:110px}.hero h1{font-size:clamp(3rem,12vw,4.8rem)}}
</style>'''

st.markdown(CSS, unsafe_allow_html=True)
st.markdown('<div class="ambient"><span class="orb o1"></span><span class="orb o2"></span><span class="orb o3"></span></div>', unsafe_allow_html=True)

DEMO = {
    "title":"Product Intelligence Weekly",
    "duration_min":47,
    "summary":"The team aligned on release readiness, resolved the ownership gap around analytics validation, and kept the Friday launch conditional on tomorrow morning’s test.",
    "participants":[
        {"name":"Maya","talk_pct":31},
        {"name":"Noah","talk_pct":27},
        {"name":"Lina","talk_pct":23},
        {"name":"Omar","talk_pct":19},
    ],
    "segments":[
        {"minute":3,"speaker":"Maya","kind":"context","text":"We need to leave today with one launch decision and clear owners.","sentiment":"neutral"},
        {"minute":12,"speaker":"Noah","kind":"risk","text":"The analytics patch is still blocking our final validation.","sentiment":"negative"},
        {"minute":21,"speaker":"Lina","kind":"decision","text":"We will keep the Friday release if analytics passes tomorrow morning.","sentiment":"positive"},
        {"minute":29,"speaker":"Omar","kind":"action","text":"I will own the analytics validation and post results before noon.","sentiment":"positive"},
        {"minute":38,"speaker":"Maya","kind":"decision","text":"Support will receive the rollout notes before the release window.","sentiment":"positive"},
    ],
    "decisions":[
        {"title":"Keep the Friday release target","detail":"Release remains conditional on analytics validation tomorrow morning.","confidence":.94},
        {"title":"Send rollout notes to Support","detail":"Support receives rollout context before the release window.","confidence":.91},
    ],
    "actions":[
        {"task":"Validate analytics patch","owner":"Omar","due":"Tomorrow 12:00","status":"Open"},
        {"task":"Prepare rollout notes","owner":"Maya","due":"Friday 09:00","status":"Open"},
    ],
    "risks":[{"title":"Analytics validation may delay launch","severity":"Medium"}]
}

ANALYZER = SentimentIntensityAnalyzer()

def classify(text):
    s = ANALYZER.polarity_scores(text or "")["compound"]
    return "positive" if s >= .18 else "negative" if s <= -.18 else "neutral"

def health(meeting):
    p = [x.get("talk_pct",0) for x in meeting.get("participants",[])]
    balance = 80 if not p else max(0,100-(max(p)-min(p))*2)
    clarity = min(100,55+len(meeting.get("decisions",[]))*12+len(meeting.get("actions",[]))*7)
    seg = meeting.get("segments",[])
    pos = sum(1 for x in seg if x.get("sentiment")=="positive")
    sentiment = int(pos/max(1,len(seg))*100)
    overall = round(balance*.30 + clarity*.45 + sentiment*.25)
    return {"overall":overall,"clarity":int(clarity),"balance":int(balance),"sentiment":sentiment}

def tokens(text):
    return {x for x in re.findall(r"[a-zA-Z0-9']+",(text or "").lower()) if len(x)>2}

def search_meeting(meeting,query):
    q = tokens(query)
    found = []
    for segment in meeting.get("segments",[]):
        score = len(q & tokens(" ".join([segment.get("speaker",""),segment.get("kind",""),segment.get("text","")])))
        if score:
            found.append((score,segment))
    return [s for _,s in sorted(found,key=lambda x:-x[0])]

def load_upload(file):
    try:
        data = json.load(file)
        for segment in data.get("segments",[]):
            segment["sentiment"] = segment.get("sentiment") or classify(segment.get("text",""))
        return data,None
    except Exception as exc:
        return None,str(exc)

with st.sidebar:
    st.markdown('<div class="brand"><div class="logo">M</div><div class="name">MeetingLens <span>AI</span></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="micro">Meeting intelligence workspace</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Load structured meeting", type=["json"])
    st.markdown('<div class="side"><div class="micro">Focus</div><strong>Decisions, ownership, unresolved work</strong><div class="side-line"></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="side"><div class="micro">Current build</div><strong>Unified Streamlit application</strong></div>', unsafe_allow_html=True)

meeting = DEMO
if uploaded:
    candidate,err = load_upload(uploaded)
    if candidate:
        meeting = candidate
        st.sidebar.success("Meeting loaded")
    else:
        st.sidebar.error(f"Invalid JSON: {err}")

h = health(meeting)
st.markdown('<div class="top"><div class="eye">Meeting intelligence / workspace</div><div class="live"><span class="dot"></span>analysis ready</div></div>', unsafe_allow_html=True)

tabs = st.tabs(["Overview","Decisions & ownership","Search memory","Signals"])

with tabs[0]:
    bars = ''.join('<i></i>' for _ in range(18))
    st.markdown(f'''
    <div class="hero">
      <div class="hleft">
        <div class="label">MeetingLens intelligence layer</div>
        <h1>Know what changed <em>after the meeting.</em></h1>
        <p>{meeting.get("summary","MeetingLens turns conversations into decisions, ownership, unresolved work, and searchable memory.")}</p>
        <div class="chips">
          <span class="chip">{meeting.get("title","Meeting")}</span>
          <span class="chip">{meeting.get("duration_min",0)} minutes</span>
          <span class="chip">{len(meeting.get("participants",[]))} participants</span>
        </div>
        <div class="signal"><span>conversation → consequence</span><div class="sigline"></div></div>
      </div>
      <div class="hright">
        <div class="scan"></div>
        <div class="hud"><div><div class="n">{h["overall"]}</div><div class="t">clarity score</div></div></div>
        <div class="float f1"><div class="flabel">Decision state</div><div class="fvalue">{len(meeting.get("decisions",[]))} confirmed</div><div class="fnote">Key commitments identified</div></div>
        <div class="float f2"><div class="flabel">Open attention</div><div class="fvalue">{len(meeting.get("risks",[]))} risk</div><div class="fnote">Still needs follow-up</div></div>
        <div class="float f3"><div class="flabel">Conversation signal</div><div class="fvalue">Decision moment detected</div><div class="wave">{bars}</div></div>
      </div>
    </div>
    ''', unsafe_allow_html=True)

    ticker_items = []
    for s in meeting.get("segments",[]):
        ticker_items.append(f'<div class="tick"><div class="tinywave"><i></i><i></i><i></i></div><b>{str(s.get("minute",0)).zfill(2)}:00</b> {s.get("speaker","Speaker")} — {s.get("text","")}</div>')
    track = "".join(ticker_items*2)
    st.markdown(f'<div class="ticker"><div class="ticktrack">{track}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section"><div class="idx">01 / meeting state</div><h3>A meeting is useful when its consequences are visible.</h3><p>Not just what was said — what moved, what stayed open, and who now owns the next step.</p></div>', unsafe_allow_html=True)

    vals = [
        ("Clarity",f'{h["overall"]}/100',"How clearly the meeting ended",h["overall"]),
        ("Decisions",len(meeting.get("decisions",[])),"Confirmed outcomes",82),
        ("Owned actions",len(meeting.get("actions",[])),"Next steps with a name",88),
        ("Open attention",len(meeting.get("risks",[])),"Items that can still drift",46),
    ]
    cols = st.columns(4)
    for c,(a,b,n,pct) in zip(cols,vals):
        with c:
            st.markdown(f'<div class="kpi"><span class="badge"></span><div class="kl">{a}</div><div class="kv">{b}</div><div class="kn">{n}</div><div class="meter"><span style="width:{pct}%"></span></div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section"><div class="idx">02 / intelligence path</div><h3>From conversation to institutional memory.</h3><p>Each layer answers a different question that ordinary meeting notes miss.</p></div>', unsafe_allow_html=True)
    story = [
        ("01","Conversation","What actually happened?"),
        ("02","Signal","What changed the direction?"),
        ("03","Decision","What became true after this meeting?"),
        ("04","Ownership","Who is responsible for the next move?"),
        ("05","Memory","Will this still be findable three weeks later?"),
    ]
    st.markdown('<div class="story">' + ''.join(f'<div class="storycard"><div class="storynum">{n}</div><div class="storytitle">{t}</div><div class="storynote">{d}</div></div>' for n,t,d in story) + '</div>', unsafe_allow_html=True)

    left,right = st.columns([1.15,.85])
    with left:
        st.markdown('<div class="panel"><div class="pt">Moments that changed the room</div><div class="ps">A compact timeline of context, tension, decisions, and ownership.</div>', unsafe_allow_html=True)
        for s in meeting.get("segments",[]):
            st.markdown(f'<div class="moment"><div class="time">{str(s.get("minute",0)).zfill(2)}:00</div><div><div class="mh">{s.get("speaker","Speaker")} <span class="tag">{s.get("kind","moment")}</span></div><div class="mt">{s.get("text","")}</div></div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><div class="pt">Speaking balance</div><div class="ps">Participation is context, not the final outcome.</div>', unsafe_allow_html=True)
        frame = pd.DataFrame(meeting.get("participants",[]))
        if not frame.empty:
            fig = px.pie(frame,values="talk_pct",names="name",hole=.76,color_discrete_sequence=["#d8ba83","#8ba297","#87939e","#b99661"])
            fig.update_layout(height=330,margin=dict(l=0,r=0,t=0,b=0),showlegend=False,paper_bgcolor="rgba(0,0,0,0)",font_color="#f3f0ea")
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section"><div class="idx">03 / consequence view</div><h3>What is different now?</h3><p>This is the layer that turns a transcript into something operational.</p></div>', unsafe_allow_html=True)
    st.markdown('''
    <div class="changegrid">
      <div class="change">
        <div class="changehead">After this meeting</div>
        <div class="changeline"><div class="cnum">01</div><div><div class="ctitle">Friday release remains possible</div><div class="ctext">But only if analytics validation passes tomorrow morning.</div></div></div>
        <div class="changeline"><div class="cnum">02</div><div><div class="ctitle">Analytics ownership is no longer ambiguous</div><div class="ctext">Omar now owns validation and must post results before noon.</div></div></div>
        <div class="changeline"><div class="cnum">03</div><div><div class="ctitle">Support has a defined handoff</div><div class="ctext">Rollout notes must arrive before the release window.</div></div></div>
      </div>
      <div class="memory">
        <div class="changehead">Memory preview</div>
        <div class="memq">“What did we decide about the Friday release?”</div>
        <div class="mema">The team kept the Friday release target, conditional on analytics validation passing tomorrow morning.</div>
        <div class="memsrc">Source · Product Intelligence Weekly · 21:00</div>
      </div>
    </div>
    ''', unsafe_allow_html=True)

with tabs[1]:
    st.markdown('<div class="section"><div class="idx">Decisions / ownership</div><h3>The meeting should end with fewer ambiguities than it started with.</h3><p>Every decision should have context. Every next step should have an owner.</p></div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div class="panel"><div class="pt">What was decided</div><div class="ps">Commitments with confidence and context.</div>', unsafe_allow_html=True)
        for d in meeting.get("decisions",[]):
            pct = round(float(d.get("confidence",0))*100)
            st.markdown(f'<div class="decision"><strong>{d.get("title","Decision")}</strong><div class="mt">{d.get("detail","")}</div><span class="conf">{pct}% confidence</span><div class="cbar"><span style="width:{pct}%"></span></div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="panel"><div class="pt">Who owns what now</div><div class="ps">Next steps with names and timing.</div>', unsafe_allow_html=True)
        for x in meeting.get("actions",[]):
            st.markdown(f'<div class="decision"><strong>{x.get("task","Task")}</strong><span class="owner">{x.get("owner","Unassigned")}</span><div class="mt">Due {x.get("due","TBD")} · {x.get("status","Open")}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="section"><div class="idx">Still unresolved</div><h3>Open loops deserve their own surface.</h3><p>If something can derail execution later, it should not disappear inside a summary paragraph.</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="panel"><div class="pt">Attention required</div><div class="ps">Items that can still drift after the call ends.</div>', unsafe_allow_html=True)
    for r in meeting.get("risks",[]):
        st.markdown(f'<div class="risk"><div>{r.get("title","Risk")}</div><span class="sev">{r.get("severity","Open")}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(meeting.get("segments",[])),use_container_width=True,hide_index=True)

with tabs[2]:
    st.markdown('<div class="section"><div class="idx">Search memory</div><h3>Ask the meeting instead of replaying it.</h3><p>Search by topic, person, decision, risk, or phrase.</p></div>', unsafe_allow_html=True)
    q = st.text_input("Search this meeting", placeholder="e.g. Friday release, analytics validation, Support...")
    if q:
        results = search_meeting(meeting,q)
        if not results:
            st.info("No matching moment found.")
        for s in results:
            st.markdown(f'<div class="panel" style="margin-bottom:.7rem"><div class="pt">{s.get("speaker","Speaker")} · {s.get("minute",0)}:00 <span class="tag">{s.get("kind","moment")}</span></div><div class="mt">{s.get("text","")}</div></div>', unsafe_allow_html=True)
    else:
        st.info("Type a topic above to search inside the current meeting.")

with tabs[3]:
    st.markdown('<div class="section"><div class="idx">Conversation signals</div><h3>Useful signals, without pretending every metric is a decision.</h3><p>Tone, balance, and clarity are context for understanding the meeting — not the product by themselves.</p></div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Overall clarity",f'{h["overall"]}/100')
    c2.metric("Decision clarity",f'{h["clarity"]}/100')
    c3.metric("Participation balance",f'{h["balance"]}/100')
    c4.metric("Positive tone",f'{h["sentiment"]}%')
    left,right = st.columns([.64,.36])
    with left:
        seg = pd.DataFrame(meeting.get("segments",[]))
        if not seg.empty:
            counts = seg["sentiment"].value_counts().rename_axis("sentiment").reset_index(name="count")
            fig = px.bar(counts,x="sentiment",y="count",color="sentiment",color_discrete_map={"positive":"#8ba297","neutral":"#87939e","negative":"#b99661"})
            fig.update_layout(height=350,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="#f3f0ea",showlegend=False)
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    with right:
        st.markdown('<div class="visual"><div class="vcopy"><div class="micro">Next layer</div><div class="vbig">One meeting is analysis. Many meetings become memory.</div><div class="vnote">The long-term value is cross-meeting decision history, unresolved issue tracking, and decision drift detection.</div></div></div>', unsafe_allow_html=True)

st.markdown('<div class="footer">MEETINGLENS AI — MAKE THE CONSEQUENCES OF A MEETING VISIBLE</div>', unsafe_allow_html=True)
