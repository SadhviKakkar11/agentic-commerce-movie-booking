"""
CodeSandbox combined entry point.
Runs the backend API and the chat web UI on a single Flask server (port 3000).

Usage:
    python codesandbox_app.py

Environment variables (set in CodeSandbox Secrets or create a .env file):
    USE_BEDROCK=True
    AWS_REGION=us-east-1
    BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
    AWS_ACCESS_KEY_ID=<your-key>
    AWS_SECRET_ACCESS_KEY=<your-secret>
"""
import os
import sys

# Ensure the project root is always on sys.path and is the working directory,
# regardless of where Python is launched from (CodeSandbox, Codespaces, local).
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

# ---------------------------------------------------------------------------
# Load dotenv FIRST so env vars (including PORT, AWS keys) are resolved before
# anything else reads them.
# ---------------------------------------------------------------------------
from dotenv import load_dotenv
load_dotenv()

# Resolve PORT — CodeSandbox injects $PORT at runtime; fall back to 3000.
PORT = int(os.environ.get("PORT", 3000))

# Tell the agent which base URL the API lives at (same server, same port).
os.environ["BACKEND_URL"] = f"http://localhost:{PORT}"

from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS

# Backend routes are pure Python — safe to import eagerly.
try:
    from backend.routes import api_bp
    _backend_ok = True
except Exception as _be:
    _backend_ok = False
    _backend_err = str(_be)
    print(f"[CineBot] WARNING: Could not import backend routes: {_backend_err}")

# Agent module is imported LAZILY (inside _get_agent) so that missing AWS
# credentials or any import-time error never prevents the server from starting.
_MovieBookingAgent = None
_agent_import_error = None

def _load_agent_class():
    global _MovieBookingAgent, _agent_import_error
    if _MovieBookingAgent is not None:
        return _MovieBookingAgent
    try:
        from agent.agent import MovieBookingAgent
        _MovieBookingAgent = MovieBookingAgent
        print("[CineBot] Agent module loaded successfully.")
    except Exception as exc:
        _agent_import_error = str(exc)
        print(f"[CineBot] ERROR loading agent module: {_agent_import_error}")
    return _MovieBookingAgent

app = Flask(__name__)
CORS(app)

# Mount the full REST API at /api/ (if backend loaded correctly)
if _backend_ok:
    app.register_blueprint(api_bp)

# ---------------------------------------------------------------------------
# Per-session agent store (keyed by user_id)
# ---------------------------------------------------------------------------
_agents: dict = {}


def _get_agent(user_id: str):
    AgentClass = _load_agent_class()
    if AgentClass is None:
        raise RuntimeError(
            f"Agent module failed to load: {_agent_import_error}. "
            "Check that AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and "
            "AWS_DEFAULT_REGION are set in the CodeSandbox Secrets (Env) panel."
        )
    if user_id not in _agents:
        _agents[user_id] = AgentClass(user_id=user_id)
    return _agents[user_id]


# ---------------------------------------------------------------------------
# Chat web-UI routes
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>CineBot – Movie Ticket Booking</title>
<style>
:root{
  --red:#E50914;--red2:#B20710;
  --bg:#f7f7f8;--surface:#ffffff;--surface2:#f0f0f2;--surface3:#e2e2e6;
  --text:#1a1a1a;--muted:#6b6b6b;--accent:#d97706;
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',Tahoma,Verdana,sans-serif;background:var(--bg);color:var(--text);height:100vh;display:flex;flex-direction:column;overflow:hidden}

/* ── Header ─────────────────────────────────────────── */
.header{background:linear-gradient(90deg,var(--red),var(--red2));padding:12px 24px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 2px 12px rgba(0,0,0,.6);flex-shrink:0}
.logo{font-size:20px;font-weight:700;letter-spacing:.5px;display:flex;align-items:center;gap:8px;color:#fff}
.logo span{font-size:11px;font-weight:400;color:#fff;opacity:.9;margin-left:4px}
.user-pill{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2);border-radius:20px;padding:6px 16px;display:flex;align-items:center;gap:10px;font-size:13px}
.pts{background:var(--accent);color:#111;border-radius:10px;padding:2px 9px;font-weight:700;font-size:12px}

/* ── chat area ──────────────────────────────────────── */
.chat-wrap{flex:1;overflow-y:auto;padding:20px 16px;display:flex;flex-direction:column;gap:14px}
.chat-wrap::-webkit-scrollbar{width:5px}
.chat-wrap::-webkit-scrollbar-thumb{background:#c8c8cc;border-radius:4px}

.msg{display:flex;gap:10px;max-width:82%;animation:pop .25s ease}
@keyframes pop{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.msg.user{align-self:flex-end;flex-direction:row-reverse}
.msg.bot{align-self:flex-start}

.avatar{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0}
.avatar.bot{background:linear-gradient(135deg,var(--red),var(--red2))}
.avatar.user{background:linear-gradient(135deg,#667eea,#764ba2)}

.bubble{padding:11px 15px;border-radius:16px;line-height:1.65;font-size:14px;word-wrap:break-word}
.msg.bot .bubble{background:var(--surface);border:1px solid var(--surface3);border-top-left-radius:4px}
.msg.user .bubble{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border-top-right-radius:4px}

/* markdown inside bubbles */
.bubble h1,.bubble h2,.bubble h3{margin:8px 0 4px;line-height:1.3}
.bubble h2{font-size:15px;color:var(--accent)}
.bubble h3{font-size:14px}
.bubble p{margin:4px 0}
.bubble ul,.bubble ol{margin:4px 0 4px 20px}
.bubble li{margin:3px 0}
.bubble strong{color:var(--accent)}
.bubble em{color:#555}
.bubble code{background:rgba(0,0,0,.07);padding:1px 5px;border-radius:3px;font-size:12px;font-family:monospace}
.bubble pre{background:rgba(0,0,0,.05);padding:10px;border-radius:8px;overflow-x:auto;margin:8px 0}
.bubble hr{border:none;border-top:1px solid var(--surface3);margin:8px 0}
.bubble blockquote{border-left:3px solid var(--accent);padding-left:10px;color:var(--muted);margin:6px 0}
.bubble table{border-collapse:collapse;width:100%;margin:8px 0;font-size:13px}
.bubble th,.bubble td{border:1px solid var(--surface3);padding:6px 10px;text-align:left}
.bubble th{background:var(--surface2)}

/* typing dots */
.typing{display:flex;gap:5px;padding:12px 15px;background:var(--surface);border-radius:16px;border-top-left-radius:4px;width:fit-content}
.dot{width:7px;height:7px;background:var(--muted);border-radius:50%;animation:bop 1.3s ease-in-out infinite}
.dot:nth-child(2){animation-delay:.2s}.dot:nth-child(3){animation-delay:.4s}
@keyframes bop{0%,80%,100%{transform:scale(.8);opacity:.4}40%{transform:scale(1.1);opacity:1}}

/* ── Input bar ──────────────────────────────────────── */
.input-bar{background:var(--surface);border-top:1px solid var(--surface3);padding:14px 20px;flex-shrink:0}
.quick-btns{display:flex;gap:7px;margin-bottom:11px;flex-wrap:wrap}
.qb{background:var(--surface2);border:1px solid var(--surface3);color:var(--text);border-radius:20px;padding:5px 13px;font-size:12px;cursor:pointer;transition:all .18s;white-space:nowrap}
.qb:hover{background:var(--red);border-color:var(--red);color:#fff}
.row{display:flex;gap:10px;align-items:center}
.row input{flex:1;background:var(--surface2);border:1px solid var(--surface3);border-radius:25px;padding:11px 18px;color:var(--text);font-size:14px;outline:none;transition:border-color .2s}
.row input:focus{border-color:var(--red)}
.row input::placeholder{color:var(--muted)}
.send{background:var(--red);border:none;border-radius:50%;width:42px;height:42px;color:#fff;font-size:19px;cursor:pointer;transition:background .18s;flex-shrink:0;display:flex;align-items:center;justify-content:center}
.send:hover{background:var(--red2)}.send:disabled{background:#bbb;cursor:not-allowed}

/* constraint tag */
.tag{background:rgba(229,9,20,.15);border:1px solid rgba(229,9,20,.3);color:#f87171;border-radius:6px;padding:2px 8px;font-size:11px;font-weight:600}

/* ── Stage bar ──────────────────────────────────────── */
.stage-bar{background:var(--surface);border-bottom:1px solid var(--surface3);padding:10px 24px;display:flex;align-items:center;justify-content:center;gap:0;flex-shrink:0}
.stage{display:flex;align-items:center;gap:6px;font-size:11px;font-weight:600;color:var(--muted);transition:color .3s}
.stage.active{color:var(--red)}
.stage.done{color:#16a34a}
.stage .dot-s{width:24px;height:24px;border-radius:50%;border:2px solid currentColor;display:flex;align-items:center;justify-content:center;font-size:11px;transition:all .3s;background:transparent}
.stage.active .dot-s{background:var(--red);border-color:var(--red);color:#fff}
.stage.done .dot-s{background:#16a34a;border-color:#16a34a;color:#fff}
.stage-line{width:40px;height:2px;background:var(--surface3);margin:0 6px;border-radius:2px;transition:background .3s}
.stage-line.done{background:#16a34a}

/* ── Payment overlay ────────────────────────────────── */
.pay-overlay{position:fixed;inset:0;background:rgba(0,0,0,.62);display:none;align-items:flex-end;justify-content:center;z-index:200;backdrop-filter:blur(4px)}
.pay-overlay.open{display:flex}
.pay-panel{background:var(--bg);border-radius:22px 22px 0 0;padding:24px 20px 32px;width:min(780px,100vw);box-shadow:0 -12px 50px rgba(0,0,0,.3);animation:slideup .28s ease}
@keyframes slideup{from{transform:translateY(100%)}to{transform:translateY(0)}}
.pay-panel-hdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
.pay-panel-hdr h3{font-size:13px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:var(--muted)}
.pay-cancel-x{background:none;border:none;font-size:18px;color:var(--muted);cursor:pointer;line-height:1}
.opt-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin-top:14px}
.opt-card{background:var(--surface);border:2px solid var(--surface3);border-radius:16px;padding:18px 16px 14px;cursor:pointer;position:relative;transition:all .2s;display:flex;flex-direction:column;gap:8px}
.opt-card:hover{border-color:var(--red);box-shadow:0 6px 20px rgba(229,9,20,.15);transform:translateY(-3px)}
.opt-card.best{border-color:var(--accent);box-shadow:0 4px 16px rgba(217,119,6,.2)}
.opt-badge{position:absolute;top:-10px;left:50%;transform:translateX(-50%);background:var(--accent);color:#111;font-size:9px;font-weight:800;padding:3px 10px;border-radius:10px;letter-spacing:.6px;white-space:nowrap}
.own-badge{position:absolute;top:10px;right:10px;background:#1d4ed8;color:#fff;font-size:8px;font-weight:800;padding:2px 8px;border-radius:8px;letter-spacing:.5px}
.pref-badge{position:absolute;top:10px;right:10px;background:#16a34a;color:#fff;font-size:8px;font-weight:800;padding:2px 8px;border-radius:8px;letter-spacing:.5px}
.opt-name{font-size:13px;font-weight:700;color:var(--text);line-height:1.3}
.opt-sub{font-size:11px;color:var(--muted)}
.opt-row{display:flex;justify-content:space-between;font-size:11px;padding:4px 0;border-top:1px solid var(--surface3)}
.opt-row span:last-child{font-weight:600;color:var(--text)}
.opt-pay{margin-top:6px;background:var(--red);color:#fff;border:none;border-radius:10px;padding:9px;font-size:13px;font-weight:700;cursor:pointer;transition:background .18s;width:100%}
.opt-card.best .opt-pay{background:var(--accent);color:#111}
.opt-pay:hover{opacity:.88}

/* ── Booking confirmed card ─────────────────────────── */
.confirmed-card{background:linear-gradient(135deg,#064e3b,#065f46);border-radius:14px;padding:20px;margin:6px 0;color:#fff;font-size:13px}
.confirmed-card .tick{font-size:28px;display:block;margin-bottom:6px}
.confirmed-card h4{font-size:15px;margin-bottom:12px}
.confirmed-card .info-row{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(255,255,255,.1);font-size:12px}
.confirmed-card .info-row:last-child{border:none}
.confirmed-card .info-row span:first-child{color:rgba(255,255,255,.65)}

/* ── Booking action buttons ─────────────────────────── */
.action-btns{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;padding-top:10px;border-top:1px solid var(--surface3)}
.ab{border:none;border-radius:12px;padding:8px 14px;font-size:12px;font-weight:600;cursor:pointer;transition:all .18s;white-space:nowrap}
.ab-yes{background:#16a34a;color:#fff}.ab-yes:hover{background:#15803d}
.ab-seat{background:var(--surface2);border:1px solid var(--surface3);color:var(--text)}.ab-seat:hover{background:#2563eb;border-color:#2563eb;color:#fff}
.ab-theatre{background:var(--surface2);border:1px solid var(--surface3);color:var(--text)}.ab-theatre:hover{background:#7c3aed;border-color:#7c3aed;color:#fff}
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div class="logo">🎬 CineBot</div>
  <div class="user-pill">
    <span>👤 Ram Kumar</span>
    <span style="color:rgba(255,255,255,.4)">·</span>
    <span>ICICI Bank</span>
    <span class="pts" id="ptsDisplay">⭐ 1000 pts</span>
  </div>
</div>

<!-- Stage bar -->
<div class="stage-bar" id="stageBar">
  <div class="stage active" id="st0"><div class="dot-s">1</div><span>Search</span></div>
  <div class="stage-line" id="sl0"></div>
  <div class="stage" id="st1"><div class="dot-s">2</div><span>Select</span></div>
  <div class="stage-line" id="sl1"></div>
  <div class="stage" id="st2"><div class="dot-s">3</div><span>Payment</span></div>
  <div class="stage-line" id="sl2"></div>
  <div class="stage" id="st3"><div class="dot-s">✓</div><span>Confirmed</span></div>
</div>

<!-- Chat -->
<div class="chat-wrap" id="chatArea">
  <div class="msg bot">
    <div class="avatar bot">🤖</div>
    <div class="bubble">
      <strong>Hi Ram! 👋 I'm CineBot, your personal movie booking assistant.</strong><br><br>
      Just tell me what you'd like to watch and when. I'll check your preferences, recommend the best theatre &amp; seats, and handle everything from booking to payment. 🎬
    </div>
  </div>
</div>

<!-- Input -->
<div class="input-bar">
  <div class="quick-btns">
    <button class="qb" onclick="hint('I want to book 2 tickets for Dhurandhar this Sunday afternoon')">🎥 Book Dhurandhar</button>
    <button class="qb" onclick="hint('Show me all Hindi movies available this week')">🎬 What\'s Playing</button>
    <button class="qb" onclick="hint('Show my past bookings')">📋 My Bookings</button>
    <button class="qb" onclick="hint('What Hindi movies are releasing in action genre?')">⭐ Action Movies</button>
  </div>
  <div class="row">
    <input type="text" id="inp"
      placeholder="e.g. I want to book 2 tickets for Dhurandhar this Sunday afternoon…"
      autocomplete="off"/>
    <button class="send" id="sendBtn" onclick="send()">➤</button>
  </div>
</div>

<!-- Payment overlay -->
<div class="pay-overlay" id="payOverlay">
  <div class="pay-panel">
    <div class="pay-panel-hdr">
      <h3>💳 Payment Options &nbsp;·&nbsp; Compare &amp; Choose</h3>
      <button class="pay-cancel-x" onclick="closePayment()">✕</button>
    </div>
    <div class="opt-grid" id="optGrid"></div>
  </div>
</div>

<script>
// Inline micro-markdown — no CDN dependency
function marked(s){
  return s
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,'<em>$1</em>')
    .replace(/`([^`]+)`/g,'<code>$1</code>')
    .replace(/^#{3}\s+(.+)$/gm,'<h3>$1</h3>')
    .replace(/^#{2}\s+(.+)$/gm,'<h2>$1</h2>')
    .replace(/^#{1}\s+(.+)$/gm,'<h1>$1</h1>')
    .replace(/^[-*]\s+(.+)$/gm,'<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs,'<ul>$1</ul>')
    .replace(/\\n\\n+/g,'</p><p>')
    .replace(/\\n/g,'<br>');
}
marked.parse = marked;

const USER_ID = 'user_ram_001';
const chat    = document.getElementById('chatArea');

// hint: fill input and focus (let user edit or press Enter/send)
function hint(t){
  const inp=document.getElementById('inp');
  inp.value=t;
  inp.focus();
  inp.setSelectionRange(t.length,t.length);
}
function qs(t){hint(t);}

function send(){
  const inp=document.getElementById('inp');
  const msg=inp.value.trim();
  if(!msg)return;

  const btn=document.getElementById('sendBtn');
  btn.disabled=true;
  addMsg(msg,'user',false);
  inp.value='';

  const tid=addTyping();

  fetch('/chat',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({user_id:USER_ID, message:msg})
  })
  .then(r=>r.json())
  .then(d=>{
    rmTyping(tid);
    btn.disabled=false;
    if(d.response){
      addMsg(d.response,'bot',true);
      maybeShowPayment(d.response);
    } else addMsg('❌ Error: '+(d.error||'Unknown error'),'bot',false);
    // Refresh points badge after every bot reply
    fetch('/api/users/'+USER_ID+'/profile').then(r=>r.json()).then(p=>{
      if(p.success && p.profile && p.profile.cc_points !== undefined){
        document.getElementById('ptsDisplay').textContent='⭐ '+p.profile.cc_points+' pts';
      }
    }).catch(()=>{});
  })
  .catch(e=>{
    rmTyping(tid);
    btn.disabled=false;
    addMsg('❌ Connection error: '+e.message,'bot',false);
  });
}

function addMsg(text, who, md){
  const wrap=document.createElement('div');
  wrap.className='msg '+who;

  const av=document.createElement('div');
  av.className='avatar '+who;
  av.textContent = who==='bot'?'🤖':'👤';

  const b=document.createElement('div');
  b.className='bubble';
  b.innerHTML = md ? marked.parse(text) : esc(text);
  if(who==='bot') maybeShowActions(b, text);

  wrap.appendChild(av);
  wrap.appendChild(b);
  chat.appendChild(wrap);
  chat.scrollTop=chat.scrollHeight;
}

// ── Booking action buttons after recommendation ─────
function maybeShowActions(bubble, text){
  if(!/shall i|should i|go ahead|reserve these|confirm.*seat|want me to book/i.test(text.toLowerCase())) return;
  const d=document.createElement('div');
  d.className='action-btns';
  [
    ['ab-yes','\u2705 Yes, Book It!','Yes, go ahead and book it'],
    ['ab-seat','\ud83d\udcba Change Seats','Change the seats, suggest different seats based on my preferences'],
    ['ab-theatre','\ud83c\udfdb\ufe0f Change Theatre','Change the theatre, suggest another theatre based on my preferences']
  ].forEach(function(item){
    var btn=document.createElement('button');
    btn.className='ab '+item[0];
    btn.textContent=item[1];
    btn.onclick=(function(msg){return function(){hint(msg);};})(item[2]);
    d.appendChild(btn);
  });
  bubble.appendChild(d);
}

function addTyping(){
  const wrap=document.createElement('div');
  wrap.className='msg bot';
  const id='t'+Date.now();
  wrap.id=id;
  const av=document.createElement('div');
  av.className='avatar bot';
  av.textContent='🤖';
  const t=document.createElement('div');
  t.className='typing';
  t.innerHTML='<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
  wrap.appendChild(av);
  wrap.appendChild(t);
  chat.appendChild(wrap);
  chat.scrollTop=chat.scrollHeight;
  return id;
}
function rmTyping(id){const e=document.getElementById(id);if(e)e.remove();}
function esc(t){const d=document.createElement('div');d.appendChild(document.createTextNode(t));return d.innerHTML;}

document.getElementById('inp').addEventListener('keydown',e=>{
  if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}
});

// ── Stage bar ────────────────────────────────────────
const STAGES = ['st0','st1','st2','st3'];
const LINES  = ['sl0','sl1','sl2'];
function setStage(n){
  STAGES.forEach((id,i)=>{
    const el=document.getElementById(id);
    el.classList.remove('active','done');
    if(i<n) el.classList.add('done');
    else if(i===n) el.classList.add('active');
  });
  LINES.forEach((id,i)=>{
    document.getElementById(id).classList.toggle('done', i<n);
  });
}

// ── Audio chime (Web Audio API) ───────────────────────
function playChime(){
  try{
    const ctx=new(window.AudioContext||window.webkitAudioContext)();
    const notes=[523.25,659.25,783.99,1046.50]; // C5 E5 G5 C6
    notes.forEach((freq,i)=>{
      const o=ctx.createOscillator(),g=ctx.createGain();
      o.type='sine'; o.frequency.value=freq;
      g.gain.setValueAtTime(0,ctx.currentTime+i*0.18);
      g.gain.linearRampToValueAtTime(0.18,ctx.currentTime+i*0.18+0.04);
      g.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+i*0.18+0.55);
      o.connect(g); g.connect(ctx.destination);
      o.start(ctx.currentTime+i*0.18);
      o.stop(ctx.currentTime+i*0.18+0.6);
    });
  }catch(e){}
}

// ── Payment flow ─────────────────────────────────────
let _pendingBooking = {};

function parseOptions(text){
  // Each option block: "Option N — Title" followed by bullet lines
  const optRe = /Option\s*(\d+)\s*[—–-]+\s*([^\\n]+)/gi;
  const opts = [];
  let m;
  while((m = optRe.exec(text)) !== null){
    const num   = m[1];
    const title = m[2].trim();
    const start = m.index + m[0].length;
    const nextM = optRe.exec(text);
    const block = nextM ? text.slice(start, nextM.index) : text.slice(start);
    if(nextM) optRe.lastIndex = nextM.index;

    const bullets = [...block.matchAll(/[•*-]\s*([^\\n]+)/g)].map(b=>b[1].trim());

    const payM = block.match(/you pay[:\s]+(?:Rs\.?\s*|₹\s*)([\d,]+(?:\.\d+)?)/i)
                 || block.match(/(?:Rs\.?\s*|₹\s*)([\d,]+(?:\.\d+)?)/i);
    const amt = payM ? Math.round(parseFloat(payM[1].replace(/,/g,''))) : null;

    // Detect if this is a card the user already owns (known bank names)
    const knownBanks = /icici|hdfc|sbi|axis|kotak|yes bank|indusind|idfc|loyalty|reward.*point/i;
    const ownThis = knownBanks.test(title);

    // Detect if bot marked it as recommended/preferred
    const preferred = /recommend|prefer|best.*option|option.*1/i.test(block + title);

    opts.push({num, title, bullets, amt, ownThis, preferred});
  }
  return opts;
}

function maybeShowPayment(text){
  const tl = text.toLowerCase();
  if(/\bconfirmed\b|\bpaid\b|payment success|booking confirmed/i.test(tl)) { setStage(3); return; }
  else if(/\bshow\b|seat|theatre|available/i.test(tl)) setStage(1);

  const opts = parseOptions(text);
  if(!opts.length) return;

  setStage(2);
  const grid = document.getElementById('optGrid');
  grid.innerHTML = '';

  const minAmt = Math.min(...opts.filter(o=>o.amt).map(o=>o.amt));

  opts.forEach(opt=>{
    const isBest = opt.amt && opt.amt === minAmt;
    const card = document.createElement('div');
    card.className = 'opt-card' + (isBest ? ' best' : '');

    let inner = isBest ? '<span class="opt-badge">BEST DEAL</span>' : '';
    if(opt.preferred && !isBest) inner += '<span class="pref-badge">PREFERRED</span>';
    else if(opt.ownThis && !isBest && !opt.preferred) inner += '<span class="own-badge">YOU OWN THIS</span>';
    inner += `<div class="opt-name">${esc(opt.title)}</div>`;
    opt.bullets.forEach(bl=>{
      const parts = bl.split(':');
      const label = esc(parts[0]);
      const val   = parts.length>1 ? esc(parts.slice(1).join(':').trim()) : '';
      inner += `<div class="opt-row"><span>${label}</span><span>${val}</span></div>`;
    });
    const amtTxt = opt.amt ? '₹'+opt.amt.toLocaleString('en-IN') : 'Pay';
    inner += `<button class="opt-pay" onclick="confirmPayment('${esc(opt.title)}','${amtTxt}')">Pay ${amtTxt}</button>`;
    card.innerHTML = inner;
    grid.appendChild(card);
  });

  document.getElementById('payOverlay').classList.add('open');
}

function closePayment(){
  document.getElementById('payOverlay').classList.remove('open');
}

function confirmPayment(optName, amt){
  closePayment();
  setStage(3);
  playChime();
  const card = optName || _pendingBooking.card || 'Payment option';
  const amtTxt = amt || _pendingBooking.amount || '';
  const wrap = document.createElement('div');
  wrap.className = 'msg bot';
  const av = document.createElement('div');
  av.className = 'avatar bot'; av.textContent = '🤖';
  const b = document.createElement('div');
  b.className = 'bubble';
  b.innerHTML = `<div class="confirmed-card">
    <span class="tick">✅</span>
    <h4>Booking Confirmed!</h4>
    <div class="info-row"><span>Option chosen</span><span>${esc(card)}</span></div>
    <div class="info-row"><span>Amount charged</span><span>${esc(amtTxt)}</span></div>
    <div class="info-row"><span>Status</span><span>Payment successful</span></div>
  </div>`;
  wrap.appendChild(av); wrap.appendChild(b);
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
}
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_id = data.get("user_id", "user_default")
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "No message provided"}), 400

    try:
        agent = _get_agent(user_id)
        response = agent.chat(message)
        return jsonify({"response": response})
    except RuntimeError as exc:
        # Friendly message shown in the chat bubble
        return jsonify({"response": f"⚠️ **Setup required**\n\n{exc}"}), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Start-up
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        from agent.config import USE_BEDROCK, BEDROCK_MODEL_ID, ANTHROPIC_MODEL
        provider = f"AWS Bedrock ({BEDROCK_MODEL_ID})" if USE_BEDROCK else f"Anthropic API ({ANTHROPIC_MODEL})"
    except Exception:
        provider = "(config not yet loaded — check Secrets/env vars)"

    print("=" * 60)
    print("  🎬  CineBot – Agentic Movie Booking")
    print(f"  AI Provider : {provider}")
    print(f"  Serving     : http://0.0.0.0:{PORT}")
    print(f"  API docs    : http://0.0.0.0:{PORT}/api/health")
    print("=" * 60)

    # Use Flask dev server only for local runs.
    # On CodeSandbox/Codespaces, gunicorn is used via tasks.json.
    app.run(host="0.0.0.0", port=PORT, debug=False)