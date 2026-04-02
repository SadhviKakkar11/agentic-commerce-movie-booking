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
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
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
.qb:hover{background:var(--red);border-color:var(--red)}
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
.pay-overlay{position:fixed;inset:0;background:rgba(0,0,0,.55);display:none;align-items:center;justify-content:center;z-index:200;backdrop-filter:blur(3px)}
.pay-overlay.open{display:flex}
.pay-panel{background:var(--surface);border-radius:18px;padding:28px 28px 22px;width:min(520px,96vw);box-shadow:0 24px 60px rgba(0,0,0,.35);animation:pop .25s ease}
.pay-panel h3{font-size:16px;font-weight:700;margin-bottom:4px}
.pay-panel .sub{font-size:12px;color:var(--muted);margin-bottom:18px}
.card-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:18px}
.cc-card{background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:14px;padding:16px 18px;cursor:pointer;border:2px solid transparent;transition:all .2s;position:relative;overflow:hidden}
.cc-card:hover{border-color:var(--red);transform:translateY(-2px);box-shadow:0 8px 24px rgba(229,9,20,.25)}
.cc-card.selected{border-color:var(--accent);box-shadow:0 8px 24px rgba(217,119,6,.3)}
.cc-card .net{font-size:10px;font-weight:600;letter-spacing:.8px;color:rgba(255,255,255,.5);text-transform:uppercase;margin-bottom:8px}
.cc-card .num{font-size:14px;font-weight:600;color:#fff;letter-spacing:2px;margin-bottom:10px;font-family:monospace}
.cc-card .bank{font-size:11px;color:rgba(255,255,255,.7);font-weight:500}
.cc-card .badge{position:absolute;top:10px;right:12px;font-size:9px;font-weight:700;padding:2px 7px;border-radius:8px}
.badge-visa{background:#1a6ed8;color:#fff}
.badge-mc{background:#eb001b;color:#fff}
.badge-rupay{background:#138e4a;color:#fff}
.pay-total{background:var(--surface2);border-radius:10px;padding:12px 16px;font-size:13px;display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.pay-total strong{font-size:16px;color:var(--accent)}
.pay-confirm-btn{width:100%;background:var(--red);color:#fff;border:none;border-radius:12px;padding:13px;font-size:15px;font-weight:600;cursor:pointer;transition:background .18s}
.pay-confirm-btn:hover{background:var(--red2)}
.pay-confirm-btn:disabled{background:#bbb;cursor:not-allowed}
.pay-cancel{display:block;text-align:center;margin-top:10px;font-size:12px;color:var(--muted);cursor:pointer;text-decoration:underline}

/* ── Booking confirmed card ─────────────────────────── */
.confirmed-card{background:linear-gradient(135deg,#064e3b,#065f46);border-radius:14px;padding:20px;margin:6px 0;color:#fff;font-size:13px}
.confirmed-card .tick{font-size:28px;display:block;margin-bottom:6px}
.confirmed-card h4{font-size:15px;margin-bottom:12px}
.confirmed-card .info-row{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(255,255,255,.1);font-size:12px}
.confirmed-card .info-row:last-child{border:none}
.confirmed-card .info-row span:first-child{color:rgba(255,255,255,.65)}
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
    <h3>💳 Select Payment Card</h3>
    <p class="sub">Choose a card to complete your booking</p>
    <div class="card-grid">
      <div class="cc-card" onclick="selectCard(this,'ICICI Bank Platinum','****4521')">
        <div class="net">Visa</div>
        <div class="num">•••• •••• •••• 4521</div>
        <div class="bank">ICICI Bank Platinum</div>
        <span class="badge badge-visa">VISA</span>
      </div>
      <div class="cc-card" onclick="selectCard(this,'HDFC Regalia','****7832')">
        <div class="net">Mastercard</div>
        <div class="num">•••• •••• •••• 7832</div>
        <div class="bank">HDFC Regalia</div>
        <span class="badge badge-mc">MC</span>
      </div>
      <div class="cc-card" onclick="selectCard(this,'SBI Card Elite','****2190')">
        <div class="net">Visa</div>
        <div class="num">•••• •••• •••• 2190</div>
        <div class="bank">SBI Card Elite</div>
        <span class="badge badge-visa">VISA</span>
      </div>
      <div class="cc-card" onclick="selectCard(this,'Axis Bank Magnus','****6647')">
        <div class="net">RuPay</div>
        <div class="num">•••• •••• •••• 6647</div>
        <div class="bank">Axis Bank Magnus</div>
        <span class="badge badge-rupay">RUPAY</span>
      </div>
    </div>
    <div class="pay-total">
      <span>Total payable</span>
      <strong id="payAmount">₹0</strong>
    </div>
    <button class="pay-confirm-btn" id="payBtn" disabled onclick="confirmPayment()">Confirm Payment</button>
    <span class="pay-cancel" onclick="closePayment()">Cancel</span>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script>
marked.setOptions({breaks:true, gfm:true});

const USER_ID = 'user_ram_001';
const chat    = document.getElementById('chatArea');

// hint: fill the input box but do NOT auto-send — user types and presses Send
function hint(t){
  const inp=document.getElementById('inp');
  inp.value=t;
  inp.focus();
  // place cursor at end
  inp.setSelectionRange(t.length, t.length);
}
// qs kept for backward compat but now same as hint
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

  wrap.appendChild(av);
  wrap.appendChild(b);
  chat.appendChild(wrap);
  chat.scrollTop=chat.scrollHeight;
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

function maybeShowPayment(text){
  // Advance stage based on keywords in bot reply
  const tl = text.toLowerCase();
  if(/confirm|book|paid|payment success/i.test(tl)) setStage(3);
  else if(/select.*card|payment|checkout/i.test(tl)) setStage(2);
  else if(/show|seat|theatre|available|option/i.test(tl)) setStage(1);

  // Trigger payment panel when agent response contains a price/total line
  const m = text.match(/(?:total|amount|pay(?:able)?)\D{0,12}₹\s*([\d,]+)/i)
            || text.match(/₹\s*([\d,]+)/);
  if(m){
    _pendingBooking.amount = '₹'+m[1].replace(/,/g,'').replace(/^(\d+)$/,n=>Number(n).toLocaleString('en-IN'));
    document.getElementById('payAmount').textContent = _pendingBooking.amount;
    document.getElementById('payOverlay').classList.add('open');
    setStage(2);
  }
}

function selectCard(el, bank, num){
  document.querySelectorAll('.cc-card').forEach(c=>c.classList.remove('selected'));
  el.classList.add('selected');
  _pendingBooking.card = bank+' '+num;
  document.getElementById('payBtn').disabled = false;
}

function closePayment(){
  document.getElementById('payOverlay').classList.remove('open');
  document.querySelectorAll('.cc-card').forEach(c=>c.classList.remove('selected'));
  document.getElementById('payBtn').disabled = true;
}

function confirmPayment(){
  closePayment();
  setStage(3);
  playChime();
  const card = _pendingBooking.card || 'Card';
  const amt  = _pendingBooking.amount || '';
  // Show a booking-confirmed card in the chat
  const wrap = document.createElement('div');
  wrap.className = 'msg bot';
  const av = document.createElement('div');
  av.className = 'avatar bot'; av.textContent = '🤖';
  const b = document.createElement('div');
  b.className = 'bubble';
  b.innerHTML = `<div class="confirmed-card">
    <span class="tick">✅</span>
    <h4>Booking Confirmed!</h4>
    <div class="info-row"><span>Card used</span><span>${esc(card)}</span></div>
    <div class="info-row"><span>Amount charged</span><span>${esc(amt)}</span></div>
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
