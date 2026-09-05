from __future__ import annotations
import json, re
import pandas as pd
import plotly.express as px
import streamlit as st
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

st.set_page_config(page_title="MeetingLens AI", page_icon="◌", layout="wide", initial_sidebar_state="expanded")
HERO_IMAGE="https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&w=1900&q=88"

CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600&family=Sora:wght@400;500;600;700&display=swap');
:root{--bg:#0b0d10;--panel:#12161a;--text:#f2f0eb;--muted:#8f989f;--line:rgba(255,255,255,.075);--champ:#c7ad82;--champ2:#e3cfad;--sage:#92a99f;--steel:#8c9aa6}
*{box-sizing:border-box}html,body,[class*=css]{font-family:Inter,system-ui,sans-serif}
.stApp{color:var(--text);background:radial-gradient(circle at 8% 8%,rgba(199,173,130,.055),transparent 22%),radial-gradient(circle at 88% 18%,rgba(146,169,159,.04),transparent 24%),linear-gradient(180deg,#090b0e 0%,#0d1114 54%,#0a0c0f 100%)}
[data-testid=stHeader]{background:transparent}[data-testid=stSidebar]{background:rgba(10,12,15,.95);border-right:1px solid var(--line)}
.block-container{max-width:1560px;padding-top:.75rem;padding-bottom:5rem}
.stTabs [data-baseweb=tab-list]{gap:.55rem;border-bottom:1px solid var(--line);padding-bottom:.55rem;animation:fadeSlide .65s .12s both}.stTabs [data-baseweb=tab]{font-size:.74rem;border-radius:999px;padding:.5rem .88rem;color:#959da3;background:transparent;border:1px solid transparent;transition:.25s}.stTabs [data-baseweb=tab]:hover{color:#ded5c6;transform:translateY(-1px)}.stTabs [aria-selected=true]{color:#e8ddca!important;background:rgba(199,173,130,.07)!important;border-color:rgba(199,173,130,.16)!important}
[data-testid=stFileUploader]{border:1px dashed rgba(199,173,130,.16);border-radius:18px;background:rgba(255,255,255,.01);transition:.3s}[data-testid=stFileUploader]:hover{border-color:rgba(199,173,130,.34);background:rgba(199,173,130,.025)}
@keyframes fadeSlide{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}@keyframes fadeLeft{from{opacity:0;transform:translateX(-22px)}to{opacity:1;transform:none}}@keyframes fadeRight{from{opacity:0;transform:translateX(22px)}to{opacity:1;transform:none}}@keyframes drift{to{transform:translate(34px,22px) scale(1.08)}}@keyframes breathe{0%,100%{transform:translate(-50%,-50%) scale(1);box-shadow:0 0 55px rgba(199,173,130,.06)}50%{transform:translate(-50%,-50%) scale(1.055);box-shadow:0 0 105px rgba(199,173,130,.16)}}@keyframes ring{to{transform:rotate(360deg)}}@keyframes dash{to{stroke-dashoffset:-120}}@keyframes wave{0%,100%{height:5px;opacity:.28}50%{height:30px;opacity:.92}}@keyframes sweep{0%,58%{transform:translateX(-140%)}80%,100%{transform:translateX(140%)}}@keyframes ticker{to{transform:translateX(-50%)}}@keyframes flow{to{background-position:-200% 0}}@keyframes imageBreath{from{transform:scale(1.02)}to{transform:scale(1.09)}}@keyframes floatA{0%,100%{transform:translateY(0)}50%{transform:translateY(-9px)}}@keyframes floatB{0%,100%{transform:translateY(0) translateX(0)}50%{transform:translateY(7px) translateX(-4px)}}@keyframes softGlow{0%,100%{opacity:.55}50%{opacity:1}}@keyframes meterGrow{from{transform:scaleX(.06);opacity:.25}to{transform:scaleX(1);opacity:1}}@keyframes shimmer{0%{transform:translateX(-130%)}100%{transform:translateX(130%)}}@keyframes scanY{0%{top:-6%}100%{top:106%}}
.ambient{position:fixed;inset:0;pointer-events:none;overflow:hidden}.glow{position:absolute;border-radius:50%;filter:blur(90px);opacity:.085;animation:drift 22s ease-in-out infinite alternate}.g1{width:360px;height:360px;background:#bda273;left:-140px;top:9%}.g2{width:420px;height:420px;background:#6e8179;right:-170px;top:28%;animation-duration:29s}.g3{width:300px;height:300px;background:#70808d;left:46%;bottom:-150px;animation-duration:25s}
.brand{display:flex;align-items:center;gap:.8rem;margin:.2rem 0 1.35rem;animation:fadeLeft .65s both}.logo{width:43px;height:43px;border-radius:15px;display:grid;place-items:center;border:1px solid rgba(227,207,173,.22);background:linear-gradient(145deg,#20252a,#12161a);color:var(--champ2);font-family:Sora;font-weight:600;transition:.3s}.logo:hover{transform:rotate(-5deg) scale(1.05);box-shadow:0 12px 28px rgba(0,0,0,.28)}.brandname{font-family:Sora;font-size:1rem;font-weight:600;letter-spacing:-.025em}.brandname span{color:var(--champ2)}.micro{font-family:'DM Mono';font-size:.62rem;text-transform:uppercase;letter-spacing:.16em;color:#717a80;font-weight:500}.sidebox{border:1px solid var(--line);border-radius:17px;padding:1rem;margin-top:.85rem;background:rgba(255,255,255,.012);transition:.3s;animation:fadeLeft .65s .08s both}.sidebox:hover{transform:translateY(-4px);border-color:rgba(199,173,130,.19);box-shadow:0 14px 36px rgba(0,0,0,.17)}.sidebox strong{display:block;margin-top:.35rem;font-size:.82rem;font-weight:550}
.top{display:flex;justify-content:space-between;align-items:center;padding:.35rem 0 .95rem;border-bottom:1px solid var(--line);margin-bottom:1.1rem;animation:fadeSlide .6s both}.crumb{font-family:'DM Mono';font-size:.64rem;text-transform:uppercase;letter-spacing:.16em;color:#747d83}.ready{display:inline-flex;align-items:center;gap:.5rem;font-size:.69rem;color:#b8c5bf;border:1px solid rgba(146,169,159,.18);padding:.45rem .7rem;border-radius:999px;background:rgba(146,169,159,.04)}.ready i{width:6px;height:6px;border-radius:50%;background:var(--sage);display:block;box-shadow:0 0 0 5px rgba(146,169,159,.05);animation:softGlow 1.8s infinite}
.hero{display:grid;grid-template-columns:1.08fr .92fr;min-height:610px;border:1px solid var(--line);border-radius:32px;overflow:hidden;background:linear-gradient(135deg,#14181c,#0f1215);box-shadow:0 42px 120px rgba(0,0,0,.28);position:relative;animation:fadeSlide .8s both;isolation:isolate}.hero:before{content:'';position:absolute;inset:0;background:linear-gradient(120deg,transparent 22%,rgba(255,255,255,.03) 46%,transparent 60%);transform:translateX(-140%);animation:sweep 10s ease-in-out infinite;pointer-events:none;z-index:9}.hero:after{content:'';position:absolute;inset:12px;border:1px solid rgba(255,255,255,.025);border-radius:24px;z-index:8;pointer-events:none}
.copy{padding:4.2rem 3.4rem 3.5rem;display:flex;flex-direction:column;justify-content:center;position:relative;z-index:3}.eyebrow{width:max-content;font-family:'DM Mono';font-size:.62rem;text-transform:uppercase;letter-spacing:.16em;color:#bba784;border:1px solid rgba(199,173,130,.17);border-radius:999px;padding:.45rem .65rem;background:rgba(199,173,130,.035);margin-bottom:1.35rem;animation:fadeLeft .65s .15s both}.hero h1{font-family:Sora,system-ui,sans-serif;font-weight:500;font-size:clamp(2.35rem,3.55vw,4.15rem);line-height:1.08;letter-spacing:-.045em;margin:0;max-width:760px;word-break:keep-all;overflow-wrap:normal;hyphens:none;text-wrap:balance;animation:fadeLeft .75s .24s both}.hero h1 .accent{font-weight:600;color:var(--champ2);position:relative;white-space:nowrap}.hero h1 .accent:after{content:'';position:absolute;left:0;bottom:-10px;width:72%;height:1px;background:linear-gradient(90deg,var(--champ2),transparent);transform-origin:left;animation:meterGrow 1s .8s both}.hero p{max-width:620px;color:#a7afb4;font-size:.98rem;line-height:1.72;margin:1.5rem 0 0;animation:fadeLeft .75s .34s both}.chips{display:flex;gap:.55rem;flex-wrap:wrap;margin-top:1.35rem;animation:fadeLeft .75s .42s both}.chip{font-size:.71rem;color:#c2c8cb;border:1px solid var(--line);border-radius:999px;padding:.44rem .65rem;background:rgba(255,255,255,.014);transition:.25s}.chip:hover{transform:translateY(-3px);border-color:rgba(199,173,130,.2);color:#e2d8c8}.promise{display:flex;align-items:center;gap:.75rem;margin-top:1.7rem;font-family:'DM Mono';font-size:.63rem;letter-spacing:.13em;text-transform:uppercase;color:#747d82;animation:fadeLeft .75s .5s both}.promise span{height:1px;flex:1;max-width:260px;background:linear-gradient(90deg,var(--champ),var(--sage),transparent);background-size:200% 100%;animation:flow 4.5s linear infinite}
.canvas{position:relative;min-height:610px;overflow:hidden;background:#0f1316;animation:fadeRight .85s .12s both}.canvas-bg{position:absolute;inset:0;background-image:linear-gradient(180deg,rgba(8,11,13,.42),rgba(8,11,13,.76)),linear-gradient(90deg,rgba(9,12,15,.6),rgba(9,12,15,.16)),url('__HERO__');background-size:cover;background-position:center;animation:imageBreath 16s ease-in-out infinite alternate;transform-origin:center}.canvas:before{content:'';position:absolute;inset:0;background:radial-gradient(circle at 58% 48%,rgba(199,173,130,.12),transparent 22%),radial-gradient(circle at 52% 45%,rgba(146,169,159,.06),transparent 36%);z-index:1;animation:softGlow 5s ease-in-out infinite}.canvas:after{content:'';position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);background-size:42px 42px;mask-image:linear-gradient(to bottom,rgba(0,0,0,.9),transparent);z-index:2}.scanline{position:absolute;left:0;right:0;height:1px;z-index:4;background:linear-gradient(90deg,transparent,rgba(227,207,173,.32),transparent);box-shadow:0 0 20px rgba(227,207,173,.12);animation:scanY 7s linear infinite}.photo-tag{position:absolute;left:1.25rem;top:1.25rem;z-index:6;border:1px solid rgba(255,255,255,.1);background:rgba(10,13,16,.62);backdrop-filter:blur(14px);border-radius:999px;padding:.42rem .62rem;font-family:'DM Mono';font-size:.56rem;text-transform:uppercase;letter-spacing:.12em;color:#a6aeb3;animation:floatA 6s ease-in-out infinite}.orbit{position:absolute;left:50%;top:48%;transform:translate(-50%,-50%);width:320px;height:320px;border-radius:50%;border:1px solid rgba(255,255,255,.1);z-index:3}.orbit:before,.orbit:after{content:'';position:absolute;border-radius:50%;inset:25px;border:1px dashed rgba(199,173,130,.28);animation:ring 18s linear infinite}.orbit:after{inset:70px;border-style:solid;border-color:rgba(146,169,159,.17);animation-direction:reverse;animation-duration:25s}.core{position:absolute;left:50%;top:48%;transform:translate(-50%,-50%);width:120px;height:120px;border-radius:50%;display:grid;place-items:center;z-index:5;background:rgba(14,18,22,.82);backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.12);animation:breathe 4.8s ease-in-out infinite}.core strong{font-family:Sora;font-size:1.9rem;font-weight:500;letter-spacing:-.05em}.core small{display:block;text-align:center;font-family:'DM Mono';font-size:.52rem;text-transform:uppercase;letter-spacing:.13em;color:#7f888e;margin-top:-14px}
.node{position:absolute;z-index:6;width:185px;border:1px solid rgba(255,255,255,.11);border-radius:18px;padding:.9rem;background:rgba(13,17,20,.76);backdrop-filter:blur(18px);box-shadow:0 18px 55px rgba(0,0,0,.28);transition:.3s;overflow:hidden}.node:before,.kpi:before,.memory:before{content:'';position:absolute;inset:0;background:linear-gradient(115deg,transparent 24%,rgba(255,255,255,.035) 48%,transparent 68%);transform:translateX(-130%);animation:shimmer 8s ease-in-out infinite;pointer-events:none}.node:hover{border-color:rgba(199,173,130,.24);box-shadow:0 22px 58px rgba(0,0,0,.34)}.n1{top:3rem;right:2.2rem;animation:floatA 6s ease-in-out infinite}.n2{bottom:3.2rem;right:2.8rem;animation:floatB 7s ease-in-out infinite}.n3{left:2rem;bottom:3rem;animation:floatA 6.8s -2s ease-in-out infinite}.node .k{font-family:'DM Mono';font-size:.56rem;text-transform:uppercase;letter-spacing:.13em;color:#858e94}.node .v{font-family:Sora;font-size:1rem;font-weight:500;margin-top:.3rem}.node .s{font-size:.68rem;color:#a1a8ad;margin-top:.25rem;line-height:1.45}.wave{display:flex;align-items:center;gap:3px;height:34px;margin-top:.45rem}.wave i{width:3px;border-radius:10px;background:linear-gradient(180deg,var(--champ2),var(--sage));animation:wave 1.55s infinite}.wave i:nth-child(2n){animation-delay:.13s}.wave i:nth-child(3n){animation-delay:.27s}.path{position:absolute;inset:0;z-index:2}.path svg{width:100%;height:100%}.path path{fill:none;stroke:rgba(199,173,130,.24);stroke-width:1;stroke-dasharray:7 10;animation:dash 6.5s linear infinite}
.ticker{margin:1rem 0 1.3rem;overflow:hidden;border-top:1px solid var(--line);border-bottom:1px solid var(--line);animation:fadeSlide .7s .2s both}.track{display:flex;width:max-content;gap:2rem;padding:.68rem 0;animation:ticker 27s linear infinite}.ticker:hover .track{animation-play-state:paused}.titem{font-size:.66rem;color:#7f888d;white-space:nowrap}.titem b{color:#c8b28f;font-weight:500}
.section{margin:1.5rem 0 .8rem;animation:fadeSlide .7s both}.section .num{font-family:'DM Mono';font-size:.6rem;text-transform:uppercase;letter-spacing:.15em;color:#6f787e}.section h3{font-family:Sora;font-size:1.12rem;font-weight:500;letter-spacing:-.025em;margin:.2rem 0 0}.section p{font-size:.76rem;color:#7f888d;margin:.25rem 0 0}
.kpi{border:1px solid var(--line);border-radius:20px;padding:1.15rem 1.2rem;min-height:142px;background:linear-gradient(180deg,rgba(25,29,33,.9),rgba(18,21,24,.9));transition:.3s;position:relative;overflow:hidden;animation:fadeSlide .7s both}.kpi:hover{transform:translateY(-7px) scale(1.01);border-color:rgba(199,173,130,.2);box-shadow:0 22px 52px rgba(0,0,0,.27)}.kpi .l{font-family:'DM Mono';font-size:.61rem;text-transform:uppercase;letter-spacing:.13em;color:#788187}.kpi .v{font-family:Sora;font-size:2rem;font-weight:500;letter-spacing:-.05em;margin:.42rem 0 .15rem}.kpi .n{font-size:.73rem;color:#899196}.meter{height:2px;background:rgba(255,255,255,.045);margin-top:.9rem;border-radius:99px;overflow:hidden}.meter span{display:block;height:100%;background:linear-gradient(90deg,var(--champ),var(--sage));transform-origin:left;animation:meterGrow 1.15s .25s ease both}
.panel{border:1px solid var(--line);border-radius:22px;background:rgba(19,23,27,.78);padding:1.25rem;animation:fadeSlide .75s both;transition:.3s}.panel:hover{border-color:rgba(199,173,130,.13);box-shadow:0 20px 48px rgba(0,0,0,.15)}.pt{font-family:Sora;font-size:.98rem;font-weight:500}.ps{font-size:.74rem;color:#7f888e;margin:.25rem 0 1rem}.moment{display:grid;grid-template-columns:58px 1fr;gap:.8rem;padding:.82rem .1rem;border-bottom:1px solid rgba(255,255,255,.05);transition:.28s}.moment:last-child{border-bottom:0}.moment:hover{padding-left:.55rem;transform:translateX(3px);background:linear-gradient(90deg,rgba(199,173,130,.04),transparent)}.time{font-family:'DM Mono';font-size:.64rem;color:#c8b28f}.mh{font-size:.8rem;font-weight:500}.tag{font-family:'DM Mono';font-size:.55rem;text-transform:uppercase;letter-spacing:.07em;color:#b9a27d;border:1px solid rgba(199,173,130,.14);padding:.16rem .34rem;border-radius:999px;margin-left:.3rem}.mt{font-size:.75rem;color:#959da2;line-height:1.55;margin-top:.22rem}.decision{padding:.85rem .9rem;border:1px solid rgba(255,255,255,.055);border-radius:15px;background:rgba(255,255,255,.012);margin:.65rem 0;transition:.28s}.decision:hover{transform:translateX(6px);border-color:rgba(199,173,130,.17);background:rgba(199,173,130,.018)}.conf{font-family:'DM Mono';font-size:.57rem;color:#b7c5bf;border:1px solid rgba(146,169,159,.14);padding:.18rem .38rem;border-radius:999px;display:inline-flex;margin-top:.4rem}
.memory{border:1px solid var(--line);border-radius:22px;background:linear-gradient(180deg,rgba(23,27,31,.9),rgba(15,18,21,.94));padding:1.2rem;position:relative;overflow:hidden;animation:fadeRight .8s both;transition:.3s}.memory:hover{transform:translateY(-4px);border-color:rgba(199,173,130,.17);box-shadow:0 22px 55px rgba(0,0,0,.22)}.q{font-family:Sora;font-size:1.12rem;font-weight:500;color:#ded6ca;line-height:1.35}.answer{font-size:.76rem;color:#9ba3a8;line-height:1.6;margin-top:.7rem}.source{margin-top:.9rem;font-family:'DM Mono';font-size:.62rem;text-transform:uppercase;letter-spacing:.11em;color:#b7a17e}.footer{text-align:center;color:#555d63;font-family:'DM Mono';font-size:.62rem;margin-top:3rem;padding-top:1.2rem;border-top:1px solid rgba(255,255,255,.045);animation:fadeSlide .8s both}
@media(max-width:1050px){.hero{grid-template-columns:1fr}.canvas{min-height:520px}.copy{padding:3.4rem 1.8rem}.hero h1{font-size:clamp(2.5rem,7.8vw,4.1rem)}}@media(max-width:700px){.node.n2{display:none}.node{width:160px}.canvas{min-height:470px}.orbit{width:250px;height:250px}.hero h1 .accent{white-space:normal}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation-duration:.01ms!important;animation-iteration-count:1!important;scroll-behavior:auto!important;transition-duration:.01ms!important}}
</style>
""".replace("__HERO__", HERO_IMAGE)
st.markdown(CSS, unsafe_allow_html=True)
st.markdown('<div class="ambient"><div class="glow g1"></div><div class="glow g2"></div><div class="glow g3"></div></div>', unsafe_allow_html=True)

DEMO={"title":"Product Intelligence Weekly","duration_min":47,"summary":"The team kept Friday as the target, gave analytics validation a clear owner, and left one release risk open.","participants":[{"name":"Maya","talk_pct":31},{"name":"Noah","talk_pct":27},{"name":"Lina","talk_pct":23},{"name":"Omar","talk_pct":19}],"segments":[{"minute":3,"speaker":"Maya","kind":"context","text":"We need to leave today with one launch decision and clear owners.","sentiment":"neutral"},{"minute":12,"speaker":"Noah","kind":"risk","text":"The analytics patch is still blocking our final validation.","sentiment":"negative"},{"minute":21,"speaker":"Lina","kind":"decision","text":"We will keep the Friday release if analytics passes tomorrow morning.","sentiment":"positive"},{"minute":29,"speaker":"Omar","kind":"action","text":"I will own the analytics validation and post results before noon.","sentiment":"positive"},{"minute":38,"speaker":"Maya","kind":"decision","text":"Support will receive the rollout notes before the release window.","sentiment":"positive"}],"decisions":[{"title":"Keep Friday as the release target","detail":"The date holds if analytics passes tomorrow morning.","confidence":.94},{"title":"Send rollout notes to Support","detail":"Support gets the final notes before release.","confidence":.91}],"actions":[{"task":"Validate analytics patch","owner":"Omar","due":"Tomorrow 12:00","status":"Open"},{"task":"Prepare rollout notes","owner":"Maya","due":"Friday 09:00","status":"Open"}],"risks":[{"title":"Analytics validation may delay release","severity":"Medium"}]}
AN=SentimentIntensityAnalyzer()
def classify(text):
    s=AN.polarity_scores(text or "")["compound"]; return "positive" if s>=.18 else "negative" if s<=-.18 else "neutral"
def health(m):
    p=[x.get("talk_pct",0) for x in m.get("participants",[])]; balance=80 if not p else max(0,100-(max(p)-min(p))*2); clarity=min(100,55+len(m.get("decisions",[]))*12+len(m.get("actions",[]))*7); seg=m.get("segments",[]); pos=sum(1 for x in seg if x.get("sentiment")=="positive"); tone=int(pos/max(1,len(seg))*100); return {"overall":round(balance*.3+clarity*.45+tone*.25),"clarity":int(clarity),"balance":int(balance),"tone":tone}
def tokens(t): return {x for x in re.findall(r"[A-Za-z0-9']+",(t or "").lower()) if len(x)>2}
def search_meeting(m,q):
    q=tokens(q); out=[]
    for s in m.get("segments",[]):
        score=len(q & tokens(" ".join([s.get("speaker",""),s.get("kind",""),s.get("text","")])))
        if score: out.append((score,s))
    return [s for _,s in sorted(out,key=lambda x:-x[0])]
def load_upload(f):
    try:
        d=json.load(f)
        for s in d.get("segments",[]): s["sentiment"]=s.get("sentiment") or classify(s.get("text",""))
        return d,None
    except Exception as e:return None,str(e)

with st.sidebar:
    st.markdown('<div class="brand"><div class="logo">M</div><div class="brandname">MeetingLens <span>AI</span></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="micro">Meeting intelligence workspace</div>',unsafe_allow_html=True)
    uploaded=st.file_uploader("Load structured meeting",type=["json"])
    st.markdown('<div class="sidebox"><div class="micro">Focus</div><strong>Decisions, ownership, unresolved work</strong></div>',unsafe_allow_html=True)
    st.markdown('<div class="sidebox"><div class="micro">Current build</div><strong>Unified Streamlit application</strong></div>',unsafe_allow_html=True)

meeting=st.session_state.get("dashboard_meeting") or st.session_state.get("current_meeting") or DEMO
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
st.markdown('<div class="top"><div class="crumb">MeetingLens / intelligence workspace</div><div class="ready"><i></i> analysis ready</div></div>',unsafe_allow_html=True)
tabs=st.tabs(["Overview","Decisions & ownership","Search memory","Signals"])

with tabs[0]:
    bars="".join("<i></i>" for _ in range(22))
    st.markdown(f"""
    <div class="hero">
      <div class="copy">
        <div class="eyebrow">Decision intelligence</div>
        <h1>From conversation to<br><span class="accent">decisions that move.</span></h1>
        <p>{meeting.get("summary","Turn conversation into durable decisions, clear ownership, and searchable memory.")}</p>
        <div class="chips"><span class="chip">{meeting.get("title","Meeting")}</span><span class="chip">{meeting.get("duration_min",0)} minutes</span><span class="chip">{len(meeting.get("participants",[]))} participants</span></div>
        <div class="promise">conversation → consequence <span></span></div>
      </div>
      <div class="canvas"><div class="canvas-bg"></div><div class="scanline"></div><div class="photo-tag">live meeting context</div>
        <div class="path"><svg viewBox="0 0 800 610" preserveAspectRatio="none"><path d="M130 490 C250 370,250 170,400 290 S620 220,700 100"/><path d="M105 115 C250 200,310 420,420 300 S610 400,700 490"/></svg></div>
        <div class="orbit"></div><div class="core"><div><strong>{h["overall"]}</strong><small>clarity</small></div></div>
        <div class="node n1"><div class="k">Decision signal</div><div class="v">{len(meeting.get("decisions",[]))} commitments</div><div class="s">What the team actually agreed to.</div></div>
        <div class="node n2"><div class="k">Open attention</div><div class="v">{len(meeting.get("risks",[]))} unresolved</div><div class="s">Work that still needs a decision.</div></div>
        <div class="node n3"><div class="k">Live conversation</div><div class="v">Signal detected</div><div class="wave">{bars}</div></div>
      </div>
    </div>""",unsafe_allow_html=True)
    ticker_items=[f'<span class="titem"><b>{str(s.get("minute",0)).zfill(2)}:00</b> · {s.get("speaker","Speaker")} — {s.get("text","")}</span>' for s in meeting.get("segments",[])]
    line="".join(ticker_items);st.markdown(f'<div class="ticker"><div class="track">{line}{line}</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="section"><div class="num">01 / outcome</div><h3>What this meeting left behind</h3><p>A fast read on clarity, commitments, follow-through, and open attention.</p></div>',unsafe_allow_html=True)
    vals=[("Clarity",f'{h["overall"]}/100',"How decisively the meeting closed",h["overall"]),("Decisions",len(meeting.get("decisions",[])),"Explicit commitments",min(100,45+len(meeting.get("decisions",[]))*22)),("Owned work",len(meeting.get("actions",[])),"Tasks with responsibility",min(100,40+len(meeting.get("actions",[]))*24)),("Open attention",len(meeting.get("risks",[])),"Still unresolved",max(20,100-len(meeting.get("risks",[]))*22))]
    cols=st.columns(4)
    for c,(lab,val,note,pct) in zip(cols,vals):
        with c:st.markdown(f'<div class="kpi"><div class="l">{lab}</div><div class="v">{val}</div><div class="n">{note}</div><div class="meter"><span style="width:{pct}%"></span></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="section"><div class="num">02 / trace</div><h3>Where the conversation changed direction</h3><p>Moments that created a decision, owner, risk, or new context.</p></div>',unsafe_allow_html=True)
    c1,c2=st.columns([1.12,.88])
    with c1:
        st.markdown('<div class="panel"><div class="pt">Conversation trace</div><div class="ps">The meeting, reduced to meaningful turns.</div>',unsafe_allow_html=True)
        for s in meeting.get("segments",[]):st.markdown(f'<div class="moment"><div class="time">{str(s.get("minute",0)).zfill(2)}:00</div><div><div class="mh">{s.get("speaker","Speaker")} <span class="tag">{s.get("kind","moment")}</span></div><div class="mt">{s.get("text","")}</div></div></div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with c2:
        ans=meeting.get("decisions",[{"title":"No decision found","detail":""}])[0]
        st.markdown(f'<div class="memory"><div class="micro">Meeting memory preview</div><div class="q">“What did we decide about the Friday release?”</div><div class="answer">{ans.get("title","")} — {ans.get("detail","")}</div><div class="source">Source · decision trace</div></div>',unsafe_allow_html=True)
        st.write("");frame=pd.DataFrame(meeting.get("participants",[]))
        if not frame.empty:
            fig=px.pie(frame,values="talk_pct",names="name",hole=.76,color_discrete_sequence=["#c7ad82","#92a99f","#8c9aa6","#6f777e"]);fig.update_layout(height=300,margin=dict(l=0,r=0,t=5,b=0),showlegend=False,paper_bgcolor="rgba(0,0,0,0)",font_color="#e8e3db");st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

with tabs[1]:
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
    st.dataframe(pd.DataFrame(meeting.get("segments",[])),use_container_width=True,hide_index=True)

with tabs[2]:
    st.subheader("Search memory");st.caption("Ask the meeting what happened instead of rereading the transcript.")
    q=st.text_input("Search this meeting",placeholder="e.g. Friday release, analytics, Support...")
    if q:
        results=search_meeting(meeting,q)
        if not results:st.info("No matching moment found.")
        for s in results:st.markdown(f'<div class="panel"><div class="pt">{s.get("speaker","Speaker")} · {s.get("minute",0)}:00</div><div class="mt">{s.get("text","")}</div></div>',unsafe_allow_html=True)
    else:st.info("Type a topic to search the meeting memory.")

with tabs[3]:
    st.subheader("Signals");st.caption("A compact read on clarity, balance, tone, and unresolved work.")
    c1,c2,c3,c4=st.columns(4);c1.metric("Clarity",f'{h["overall"]}/100');c2.metric("Decision clarity",f'{h["clarity"]}/100');c3.metric("Participation",f'{h["balance"]}/100');c4.metric("Positive tone",f'{h["tone"]}%')
    seg=pd.DataFrame(meeting.get("segments",[]))
    if not seg.empty:
        counts=seg["sentiment"].value_counts().rename_axis("sentiment").reset_index(name="count");fig=px.bar(counts,x="sentiment",y="count",color="sentiment",color_discrete_map={"positive":"#92a99f","neutral":"#8c9aa6","negative":"#9d7f73"});fig.update_layout(height=340,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="#e8e3db",showlegend=False);st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

st.markdown('<div class="footer">MEETINGLENS AI · CONVERSATION → DECISION → MEMORY</div>',unsafe_allow_html=True)
