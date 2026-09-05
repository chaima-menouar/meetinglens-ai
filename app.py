from __future__ import annotations
import json, re
import pandas as pd
import plotly.express as px
import streamlit as st
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

st.set_page_config(page_title='MeetingLens AI', page_icon='🎙️', layout='wide', initial_sidebar_state='expanded')

CSS='''<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Manrope:wght@600;700;800&display=swap');
:root{--line:rgba(255,255,255,.08);--muted:#9ba4b8}.stApp{background:radial-gradient(circle at 12% 8%,rgba(112,91,255,.18),transparent 26%),radial-gradient(circle at 88% 16%,rgba(38,183,255,.10),transparent 24%),linear-gradient(180deg,#090b12 0%,#0a0d16 60%,#090b12 100%)}
html,body,[class*=css]{font-family:Inter,sans-serif}[data-testid=stSidebar]{background:linear-gradient(180deg,rgba(16,19,30,.98),rgba(10,12,20,.99));border-right:1px solid var(--line)}[data-testid=stHeader]{background:transparent}.block-container{max-width:1450px;padding-top:1.2rem;padding-bottom:4rem}
.brand{display:flex;align-items:center;gap:.7rem;margin-bottom:1.3rem}.mark{width:36px;height:36px;border-radius:12px;display:grid;place-items:center;background:linear-gradient(135deg,#8171ff,#4ecbff);box-shadow:0 10px 30px rgba(99,95,255,.3);font-weight:800}.name{font-family:Manrope;font-weight:800;font-size:1.08rem}.name span{color:#8b7cf6}.side-card{padding:1rem;border:1px solid var(--line);border-radius:16px;background:rgba(255,255,255,.025);margin-top:1rem}.small{font-size:.72rem;color:#707990;text-transform:uppercase;letter-spacing:.09em;font-weight:800}.strong{font-size:.84rem;font-weight:700;margin-top:.25rem}
.topbar{display:flex;justify-content:space-between;align-items:center;padding:.4rem .15rem 1rem;border-bottom:1px solid var(--line);margin-bottom:1.4rem}.eyebrow{color:var(--muted);font-size:.78rem;letter-spacing:.09em;text-transform:uppercase}.live{display:inline-flex;align-items:center;gap:.45rem;padding:.48rem .75rem;border:1px solid rgba(110,231,183,.22);background:rgba(110,231,183,.08);border-radius:999px;color:#9ff4cf;font-size:.78rem;font-weight:700}.dot{width:7px;height:7px;border-radius:50%;background:#6ee7b7;animation:pulse 2s infinite}@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(110,231,183,.45)}70%{box-shadow:0 0 0 10px rgba(110,231,183,0)}100%{box-shadow:0 0 0 0 rgba(110,231,183,0)}}
.hero{position:relative;overflow:hidden;border:1px solid var(--line);border-radius:28px;padding:2.15rem;background:linear-gradient(135deg,rgba(25,29,47,.92),rgba(13,16,28,.95));box-shadow:0 30px 80px rgba(0,0,0,.28)}.hero:before{content:'';position:absolute;inset:-45% auto auto 55%;width:520px;height:520px;border-radius:50%;background:radial-gradient(circle,rgba(110,102,246,.32),rgba(99,216,255,.08) 42%,transparent 68%);animation:floatGlow 8s ease-in-out infinite alternate}@keyframes floatGlow{from{transform:translate(-10px,-8px)}to{transform:translate(20px,18px) scale(1.08)}}.hero-grid{position:relative;display:grid;grid-template-columns:minmax(0,1.2fr) minmax(280px,.8fr);gap:2rem;align-items:center}.kicker{color:#bdb6ff;font-weight:700;font-size:.75rem;text-transform:uppercase;letter-spacing:.12em;margin-bottom:.9rem}.hero h1{font-family:Manrope;font-size:clamp(2rem,4.2vw,4rem);line-height:1.02;letter-spacing:-.055em;margin:0 0 1rem}.gradient{background:linear-gradient(90deg,#fff 12%,#b9b0ff 52%,#69dcff 92%);-webkit-background-clip:text;background-clip:text;color:transparent}.hero p{color:#adb5c8;font-size:1rem;line-height:1.75}.chips{display:flex;flex-wrap:wrap;gap:.65rem;margin-top:1.2rem}.chip{padding:.5rem .7rem;border:1px solid var(--line);border-radius:999px;color:#c9cede;background:rgba(255,255,255,.035);font-size:.78rem}
.wave{height:230px;border-radius:22px;border:1px solid var(--line);background:linear-gradient(180deg,rgba(13,17,30,.84),rgba(9,12,21,.9));display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden}.bars{display:flex;align-items:center;gap:7px;height:120px}.bars i{display:block;width:6px;border-radius:10px;background:linear-gradient(180deg,#80e4ff,#8a76ff);animation:wave 1.6s ease-in-out infinite}.bars i:nth-child(2n){animation-delay:.12s}.bars i:nth-child(3n){animation-delay:.25s}@keyframes wave{0%,100%{height:18px;opacity:.45}50%{height:92px;opacity:1}}
.kpi{border:1px solid var(--line);border-radius:20px;padding:1.15rem 1.2rem;background:linear-gradient(180deg,rgba(20,24,38,.8),rgba(13,16,27,.82));min-height:125px;transition:.2s}.kpi:hover{transform:translateY(-3px);border-color:rgba(139,124,246,.35)}.kl{color:var(--muted);font-size:.75rem;text-transform:uppercase;letter-spacing:.08em;font-weight:700}.kv{font-family:Manrope;font-size:1.9rem;font-weight:800;letter-spacing:-.05em;margin:.35rem 0 .2rem}.kn{color:#818ba2;font-size:.75rem}.panel{border:1px solid var(--line);border-radius:22px;padding:1.3rem;background:linear-gradient(180deg,rgba(19,23,37,.79),rgba(12,15,25,.82));margin-bottom:1rem}.pt{font-family:Manrope;font-size:1.05rem;font-weight:800}.ps{color:var(--muted);font-size:.78rem;margin-bottom:1rem}.tag{display:inline-block;font-size:.64rem;font-weight:800;border-radius:999px;padding:.22rem .42rem;margin-left:.4rem;background:rgba(139,124,246,.12);color:#bcb5ff}.muted{color:var(--muted);font-size:.8rem;line-height:1.55}.owner{font-size:.68rem;border-radius:999px;padding:.24rem .48rem;background:rgba(99,216,255,.09);color:#92e8ff}.footer{text-align:center;color:#596277;font-size:.72rem;margin-top:3rem;padding-top:1.4rem;border-top:1px solid rgba(255,255,255,.05)}.stTabs [data-baseweb=tab-list]{gap:.5rem}.stTabs [data-baseweb=tab]{background:rgba(255,255,255,.025);border:1px solid var(--line);border-radius:12px;padding:.55rem .9rem}@media(max-width:900px){.hero-grid{grid-template-columns:1fr}.wave{height:170px}.hero{padding:1.4rem}}
</style>'''
st.markdown(CSS,unsafe_allow_html=True)

DEMO={'title':'Product Intelligence Weekly','duration_min':47,'summary':'The team aligned on launch readiness, analytics fixes, and ownership for the next release.','participants':[{'name':'Maya','talk_pct':31},{'name':'Noah','talk_pct':27},{'name':'Lina','talk_pct':23},{'name':'Omar','talk_pct':19}],'segments':[{'minute':3,'speaker':'Maya','kind':'context','text':'We need to leave today with one launch decision and clear owners.','sentiment':'neutral'},{'minute':12,'speaker':'Noah','kind':'risk','text':'The analytics patch is still blocking our final validation.','sentiment':'negative'},{'minute':21,'speaker':'Lina','kind':'decision','text':'We will keep the Friday release if analytics passes tomorrow morning.','sentiment':'positive'},{'minute':29,'speaker':'Omar','kind':'action','text':'I will own the analytics validation and post results before noon.','sentiment':'positive'},{'minute':38,'speaker':'Maya','kind':'decision','text':'Support will receive the rollout notes before the release window.','sentiment':'positive'}],'decisions':[{'title':'Keep Friday release target','detail':'Conditional on analytics validation tomorrow morning.','confidence':.94},{'title':'Share rollout notes with Support','detail':'Notes must land before the release window.','confidence':.91}],'actions':[{'task':'Validate analytics patch','owner':'Omar','due':'Tomorrow 12:00','status':'Open'},{'task':'Prepare rollout notes','owner':'Maya','due':'Friday 09:00','status':'Open'}],'risks':[{'title':'Analytics validation delay','severity':'Medium'}]}
AN=SentimentIntensityAnalyzer()
def classify(text):
 s=AN.polarity_scores(text or '')['compound'];return 'positive' if s>=.18 else 'negative' if s<=-.18 else 'neutral'
def health(m):
 p=[x.get('talk_pct',0) for x in m.get('participants',[])];bal=80 if not p else max(0,100-(max(p)-min(p))*2);clarity=min(100,55+len(m.get('decisions',[]))*12+len(m.get('actions',[]))*7);seg=m.get('segments',[]);pos=sum(1 for x in seg if x.get('sentiment')=='positive');sent=int(pos/max(1,len(seg))*100);return {'overall':round(bal*.3+clarity*.45+sent*.25),'clarity':int(clarity),'balance':int(bal),'sentiment':sent}
def tokens(t):return {x for x in re.findall(r"[a-zA-Z0-9']+",(t or '').lower()) if len(x)>2}
def search(m,q):
 q=tokens(q);out=[]
 for s in m.get('segments',[]):
  score=len(q & tokens(' '.join([s.get('speaker',''),s.get('kind',''),s.get('text','')])))
  if score:out.append((score,s))
 return [s for _,s in sorted(out,key=lambda x:-x[0])]
def load_upload(f):
 try:
  d=json.load(f)
  for s in d.get('segments',[]):s['sentiment']=s.get('sentiment') or classify(s.get('text',''))
  return d,None
 except Exception as e:return None,str(e)

with st.sidebar:
 st.markdown('<div class="brand"><div class="mark">M</div><div class="name">MeetingLens <span>AI</span></div></div>',unsafe_allow_html=True);st.caption('Conversation intelligence workspace');uploaded=st.file_uploader('Upload meeting JSON',type=['json']);st.markdown('<div class="side-card"><div class="small">Deployment</div><div class="strong">Streamlit Community Cloud</div></div>',unsafe_allow_html=True);st.markdown('<div class="side-card"><div class="small">Architecture</div><div class="strong">Unified app · no frontend/backend split</div></div>',unsafe_allow_html=True)
meeting=DEMO
if uploaded:
 candidate,err=load_upload(uploaded)
 if candidate:meeting=candidate;st.sidebar.success('Meeting loaded')
 else:st.sidebar.error(f'Invalid JSON: {err}')
st.markdown('<div class="topbar"><div class="eyebrow">Conversation Intelligence Workspace</div><div class="live"><span class="dot"></span>AI engine online</div></div>',unsafe_allow_html=True)
tabs=st.tabs(['Overview','Meeting Analyzer','Knowledge Search','Insights'])
with tabs[0]:
 bars=''.join(f'<i style="height:{h}px"></i>' for h in [24,42,65,35,85,56,99,62,40,78,54,88,38,70,52,92,48,60,30]);st.markdown(f'''<div class="hero"><div class="hero-grid"><div><div class="kicker">✦ AI meeting intelligence</div><h1>See what your meeting <span class="gradient">actually decided.</span></h1><p>{meeting.get('summary','Turn conversations into decisions, actions, and searchable knowledge.')}</p><div class="chips"><span class="chip">{meeting.get('title','Meeting')}</span><span class="chip">{meeting.get('duration_min',0)} min</span><span class="chip">{len(meeting.get('participants',[]))} participants</span></div></div><div class="wave"><div class="bars">{bars}</div></div></div></div>''',unsafe_allow_html=True)
 st.write('');h=health(meeting);vals=[('Meeting health',f"{h['overall']}/100",'Clarity, balance & tone'),('Decisions',len(meeting.get('decisions',[])),'Captured commitments'),('Action items',len(meeting.get('actions',[])),'Owners & deadlines'),('Risks',len(meeting.get('risks',[])),'Needs follow-up')];cols=st.columns(4)
 for c,(a,b,n) in zip(cols,vals):
  with c:st.markdown(f'<div class="kpi"><div class="kl">{a}</div><div class="kv">{b}</div><div class="kn">{n}</div></div>',unsafe_allow_html=True)
 st.write('');a,b=st.columns([1.15,.85])
 with a:
  st.markdown('<div class="panel"><div class="pt">Key moments</div><div class="ps">Moments that changed the direction of the conversation.</div>',unsafe_allow_html=True)
  for s in meeting.get('segments',[]):st.markdown(f"**{str(s.get('minute',0)).zfill(2)}:00 · {s.get('speaker','Speaker')}** <span class='tag'>{s.get('kind','moment')}</span><br><span class='muted'>{s.get('text','')}</span>",unsafe_allow_html=True)
  st.markdown('</div>',unsafe_allow_html=True)
 with b:
  st.markdown('<div class="panel"><div class="pt">Speaker balance</div><div class="ps">Share of speaking time.</div>',unsafe_allow_html=True);frame=pd.DataFrame(meeting.get('participants',[]))
  if not frame.empty:
   fig=px.pie(frame,values='talk_pct',names='name',hole=.72);fig.update_layout(height=330,margin=dict(l=0,r=0,t=0,b=0),showlegend=False,paper_bgcolor='rgba(0,0,0,0)',font_color='#d9ddec');st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
  st.markdown('</div>',unsafe_allow_html=True)
with tabs[1]:
 st.subheader('Meeting Analyzer');st.caption('Inspect transcript moments, decisions, actions, and risks from one structured meeting file.');c1,c2=st.columns(2)
 with c1:
  st.markdown('<div class="panel"><div class="pt">Decisions captured</div>',unsafe_allow_html=True)
  for d in meeting.get('decisions',[]):st.markdown(f"**✓ {d.get('title','Decision')}**  \n<span class='muted'>{d.get('detail','')}</span>  \n`{round(float(d.get('confidence',0))*100)}% confidence`",unsafe_allow_html=True)
  st.markdown('</div>',unsafe_allow_html=True)
 with c2:
  st.markdown('<div class="panel"><div class="pt">Action radar</div>',unsafe_allow_html=True)
  for x in meeting.get('actions',[]):st.markdown(f"**{x.get('task','Task')}** <span class='owner'>{x.get('owner','Unassigned')}</span>  \n<span class='muted'>Due {x.get('due','TBD')} · {x.get('status','Open')}</span>",unsafe_allow_html=True)
  st.markdown('</div>',unsafe_allow_html=True)
 st.dataframe(pd.DataFrame(meeting.get('segments',[])),use_container_width=True,hide_index=True)
with tabs[2]:
 st.subheader('Knowledge Search');st.caption('Search the current meeting memory for topics, owners, decisions, or risks.');q=st.text_input('Ask the meeting memory',placeholder='e.g. analytics patch, Friday release, Support...')
 if q:
  r=search(meeting,q)
  if not r:st.info('No matching moment found.')
  for s in r:st.markdown(f"<div class='panel'><div class='pt'>{s.get('speaker','Speaker')} · {s.get('minute',0)}:00 <span class='tag'>{s.get('kind','moment')}</span></div><div class='muted'>{s.get('text','')}</div></div>",unsafe_allow_html=True)
 else:st.info('Type a topic above to search inside the meeting.')
with tabs[3]:
 st.subheader('Insights');st.caption('A compact read on participation, clarity, tone, and follow-through.');h=health(meeting);c1,c2,c3,c4=st.columns(4);c1.metric('Overall',f"{h['overall']}/100");c2.metric('Clarity',f"{h['clarity']}/100");c3.metric('Balance',f"{h['balance']}/100");c4.metric('Positive tone',f"{h['sentiment']}%");seg=pd.DataFrame(meeting.get('segments',[]))
 if not seg.empty:
  counts=seg['sentiment'].value_counts().rename_axis('sentiment').reset_index(name='count');fig=px.bar(counts,x='sentiment',y='count');fig.update_layout(height=320,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font_color='#d9ddec');st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
 st.markdown('<div class="panel"><div class="pt">Next intelligence layer</div><div class="ps">Roadmap</div><div class="muted">AMI ingestion → faster-whisper transcription → speaker diarization → DuckDB meeting memory → semantic search → custom classifier for decisions, actions, risks, questions and disagreement.</div></div>',unsafe_allow_html=True)
st.markdown('<div class="footer">MeetingLens AI · From conversation to clarity.</div>',unsafe_allow_html=True)