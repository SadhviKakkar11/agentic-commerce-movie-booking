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
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0"/>
<title>CineBot – Movie Ticket Booking</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"/>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden}
body{background:#F0F4FA;color:#1C2B4A;font-family:'Plus Jakarta Sans',sans-serif;-webkit-font-smoothing:antialiased}

@keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}
@keyframes popIn{0%{opacity:0;transform:scale(0.93)}100%{opacity:1;transform:scale(1)}}
@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.5}}

.app{display:flex;height:100vh;overflow:hidden}

/* ── LEFT PANE ── */
.pane-left{width:270px;flex-shrink:0;display:flex;flex-direction:column;background:white;border-right:1px solid #DDE3EE;height:100vh;overflow:hidden}
.pl-header{padding:14px 16px 12px;border-bottom:1px solid #EEF1F7;display:flex;align-items:center;gap:9px;flex-shrink:0}
.logo-icon{width:32px;height:32px;border-radius:9px;background:linear-gradient(135deg,#B20710,#E50914);display:flex;align-items:center;justify-content:center;color:#fff;font-size:13px;font-weight:800;box-shadow:0 3px 8px rgba(229,9,20,.3)}
.logo-name{font-size:13px;font-weight:800;color:#1C2B4A;letter-spacing:.3px}
.logo-sub{font-size:7px;color:#E50914;letter-spacing:2px;font-family:'JetBrains Mono',monospace}
.pl-body{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;align-items:center}
.pl-body::-webkit-scrollbar{width:3px}
.pl-body::-webkit-scrollbar-thumb{background:#E0E6F0;border-radius:2px}
.mascot-wrap{text-align:center;margin-bottom:12px;animation:float 3.5s ease-in-out infinite}
.mascot-label{font-size:12px;font-weight:800;color:#1C2B4A;margin-top:6px;letter-spacing:.3px}
.mascot-label span{color:#E50914}
.mascot-tag{font-size:9px;color:#8FA3C0;font-family:'JetBrains Mono',monospace;letter-spacing:1px;margin-top:2px}
.pl-welcome{font-size:12px;color:#5A7090;line-height:1.65;text-align:center;padding:0 4px;margin-bottom:12px}
.pl-hint{font-size:10px;color:#A0B4C8;font-family:'JetBrains Mono',monospace;text-align:center;line-height:1.5}
.query-display{width:100%;background:#FFF5F0;border:1px solid #FFD0C0;border-radius:12px;padding:12px 14px;margin-bottom:12px;animation:fadeUp .4s ease}
.query-display-lbl{font-size:9px;font-weight:700;color:#B20710;letter-spacing:2px;margin-bottom:6px;font-family:'JetBrains Mono',monospace}
.query-display-txt{font-size:12px;color:#3A1A08;line-height:1.6;font-weight:500}
.status-box{width:100%;background:#F5F7FA;border:1px solid #DDE3EE;border-radius:10px;padding:10px 12px;animation:fadeUp .4s ease}
.status-lbl{font-size:8px;font-weight:700;color:#8FA3C0;letter-spacing:2px;margin-bottom:5px;font-family:'JetBrains Mono',monospace}
.status-stage{font-size:13px;font-weight:700;color:#1C2B4A}
.status-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#E50914;margin-right:6px;animation:pulse 1.4s ease-in-out infinite}
.pl-pts{width:100%;background:linear-gradient(135deg,#fff7ed,#fff);border:1px solid #fde68a;border-radius:10px;padding:9px 12px;margin-top:10px;display:flex;align-items:center;gap:8px}
.pl-pts-icon{font-size:18px}
.pl-pts-info .lbl{font-size:8px;font-weight:700;color:#92400e;letter-spacing:1.5px}
.pl-pts-info .val{font-size:15px;font-weight:800;color:#d97706}
.pl-footer{flex-shrink:0;padding:12px 14px;border-top:1px solid #EEF1F7;background:white}
.input-row{display:flex;gap:8px;align-items:flex-end}
.chat-input{flex:1;border:1.5px solid #C8D4E8;border-radius:12px;padding:10px 12px;font-size:13px;color:#1C2B4A;font-family:'Plus Jakarta Sans',sans-serif;background:white;outline:none;resize:none;line-height:1.5;max-height:90px;box-shadow:0 2px 6px rgba(28,43,74,.07);transition:border-color .2s}
.chat-input:focus{border-color:#E50914}
.chat-input:disabled{background:#F5F7FA;color:#A0B4C8;cursor:not-allowed}
.send-btn{width:38px;height:38px;border-radius:10px;border:none;background:linear-gradient(135deg,#B20710,#E50914);color:#fff;cursor:pointer;flex-shrink:0;box-shadow:0 3px 8px rgba(229,9,20,.3);transition:transform .15s;display:flex;align-items:center;justify-content:center}
.send-btn:active{transform:scale(.93)}
.send-btn:disabled{opacity:.4;cursor:default}

/* ── RIGHT PANE ── */
.pane-right{flex:1;display:flex;flex-direction:column;overflow:hidden;background:#F0F4FA}
.pr-stage-bar{flex-shrink:0;padding:10px 20px;border-bottom:1px solid #DDE3EE;background:rgba(240,244,250,.97);backdrop-filter:blur(12px);display:flex;align-items:center;gap:4px}
.sp{font-size:8px;font-weight:600;letter-spacing:.5px;padding:3px 8px;border-radius:20px;font-family:'JetBrains Mono',monospace;color:#9AABC0;background:#E8EDF5;border:1px solid #DDE3EE;transition:all .5s;white-space:nowrap}
.sp.active{color:#B20710;background:#FFF0E8;border-color:#FFB899}
.sp.done{color:#00875A;background:#E6F7F1;border-color:#A8DECA}
.ss{width:10px;height:1.5px;background:#DDE3EE;flex-shrink:0;transition:background .5s}
.ss.done{background:#00875A}
.pr-feed{flex:1;overflow-y:auto;padding:20px 22px 40px}
.pr-feed::-webkit-scrollbar{width:4px}
.pr-feed::-webkit-scrollbar-thumb{background:#C8D4E8;border-radius:2px}
.pr-welcome{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;text-align:center;padding:40px 30px;color:#8FA3C0}
.pr-welcome-icon{font-size:36px;margin-bottom:16px;opacity:.5}
.pr-welcome-txt{font-size:14px;color:#8FA3C0;line-height:1.7;max-width:280px}

/* ── CHAT MESSAGES ── */
.msg{display:flex;gap:9px;margin-bottom:14px;animation:fadeUp .4s ease;max-width:640px}
.msg.user{flex-direction:row-reverse}
.av{width:28px;height:28px;border-radius:50%;flex-shrink:0;margin-top:2px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800}
.av.ag{background:linear-gradient(135deg,#B20710,#E50914);color:#fff;box-shadow:0 2px 6px rgba(229,9,20,.25)}
.av.ok{background:linear-gradient(135deg,#00875A,#006644);color:white;box-shadow:0 2px 6px rgba(0,135,90,.22)}
.av.us{background:#1C2B4A;color:white}
.bbl{padding:10px 14px;border-radius:14px;max-width:86%;font-size:13px;line-height:1.72}
.bbl.ag{background:white;border:1px solid #DDE3EE;border-radius:3px 14px 14px 14px;color:#2C3E5A;box-shadow:0 2px 8px rgba(28,43,74,.06)}
.bbl.us{background:linear-gradient(135deg,#B20710,#E50914);color:white;border-radius:14px 3px 14px 14px;font-size:13px;font-weight:500;box-shadow:0 2px 10px rgba(229,9,20,.25)}
.cur{animation:blink .7s step-end infinite;color:#E50914}
.bbl.ag strong{color:#d97706}
.bbl.ag ul,.bbl.ag ol{margin:4px 0 4px 18px}
.bbl.ag li{margin:3px 0}
.bbl.ag h2,.bbl.ag h3{color:#d97706;margin:6px 0 3px}

/* section label */
.sec{font-size:8px;font-weight:700;color:#8FA3C0;letter-spacing:2.5px;margin:14px 0 10px 2px;font-family:'JetBrains Mono',monospace;animation:fadeUp .4s ease}

/* ── QUICK BUTTONS ── */
.quick-btns{display:flex;gap:7px;margin-bottom:11px;flex-wrap:wrap}
.qb{background:white;border:1.5px solid #DDE3EE;color:#1C2B4A;border-radius:20px;padding:5px 13px;font-size:12px;cursor:pointer;transition:all .18s;white-space:nowrap;font-family:'Plus Jakarta Sans',sans-serif;font-weight:600}
.qb:hover{background:#E50914;border-color:#E50914;color:white}

/* ── CONFIRM BUTTON ── */
.conf-btn{width:100%;max-width:640px;border:none;border-radius:12px;padding:13px;font-size:14px;font-weight:700;color:white;cursor:pointer;font-family:'Plus Jakarta Sans',sans-serif;background:linear-gradient(135deg,#B20710,#E50914);box-shadow:0 4px 16px rgba(229,9,20,.28);margin-top:10px;margin-bottom:16px;animation:fadeUp .4s ease;transition:transform .15s}
.conf-btn:active{transform:scale(.98)}
.conf-btn:disabled{opacity:.45;cursor:default}

/* ── PAYMENT CARDS ── */
.card3-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:9px;margin-bottom:8px;max-width:640px;animation:fadeUp .5s ease}
.ccard{background:white;border-radius:13px;padding:14px;border:2px solid #DDE3EE;box-shadow:0 2px 8px rgba(28,43,74,.06);transition:all .4s;cursor:pointer;position:relative;overflow:visible;animation:fadeUp .4s ease both}
.ccard.ncs{border-color:#d97706;background:linear-gradient(160deg,#fffdf5,white)}
.ccard.sel{border-color:#B20710;box-shadow:0 5px 18px rgba(229,9,20,.18);transform:translateY(-3px)}
.ccard.ncs.sel{border-color:#d97706;box-shadow:0 5px 20px rgba(217,119,6,.25);transform:translateY(-3px)}
.top-badge{position:absolute;top:-1px;left:50%;transform:translateX(-50%);font-size:8px;font-weight:700;padding:3px 10px;border-radius:0 0 10px 10px;white-space:nowrap;letter-spacing:.3px}
.tbg{background:linear-gradient(135deg,#d97706,#f59e0b);color:#fff}
.ccard-type{display:inline-block;font-size:8px;font-weight:700;padding:2px 7px;border-radius:8px;margin-bottom:7px;margin-top:3px}
.ccard-bank{font-size:9px;font-weight:600;color:#8FA3C0;margin-bottom:2px}
.ccard-name{font-size:11px;font-weight:700;color:#1C2B4A;margin-bottom:8px;line-height:1.3}
.ccard-row{display:flex;justify-content:space-between;align-items:flex-start;padding:5px 7px;border-radius:7px;margin-bottom:3px;background:#F5F7FA;gap:4px}
.ccard-rl{font-size:8px;color:#5A7090;font-weight:500;flex-shrink:0;line-height:1.4}
.ccard-rv{font-size:8px;font-weight:700;text-align:right;line-height:1.4}
.ccard-total{margin-top:7px;padding:8px 7px;border-radius:9px;text-align:center}
.ccard-tl{font-size:7px;font-weight:700;color:#8FA3C0;letter-spacing:1px;margin-bottom:2px}
.ccard-tv{font-size:16px;font-weight:800}

/* ── OTP ── */
.otp-card{background:white;border-radius:16px;border:1.5px solid #DDE3EE;overflow:hidden;box-shadow:0 6px 28px rgba(28,43,74,.1);animation:popIn .5s cubic-bezier(.34,1.4,.64,1);margin-bottom:10px;max-width:480px}
.otp-hdr{background:#1A1F71;padding:14px 18px;display:flex;align-items:center;gap:11px}
.mc-r{width:24px;height:24px;border-radius:50%;background:#EB001B;flex-shrink:0}
.mc-y{width:24px;height:24px;border-radius:50%;background:#F79E1B;opacity:.95;margin-left:-8px;flex-shrink:0}
.otp-ht{font-size:12px;font-weight:700;color:white}
.otp-hs{font-size:9px;color:rgba(255,255,255,.6);font-family:'JetBrains Mono',monospace;margin-top:1px}
.otp-body{padding:18px}
.otp-merch{display:flex;justify-content:space-between;padding:9px 12px;background:#F5F7FA;border-radius:10px;margin-bottom:14px;border:1px solid #EEF1F7}
.otp-ml{font-size:9px;color:#8FA3C0;font-weight:600;margin-bottom:2px}
.otp-mv{font-size:13px;font-weight:700;color:#1C2B4A}
.otp-info{font-size:12px;color:#3A5070;line-height:1.65;margin-bottom:14px}
.otp-info strong{color:#1C2B4A}
.otp-fields{display:flex;gap:7px;justify-content:center;margin-bottom:12px}
.otp-box{width:38px;height:46px;border:2px solid #C8D4E8;border-radius:10px;font-size:20px;font-weight:700;color:#1C2B4A;text-align:center;font-family:'JetBrains Mono',monospace;background:white;outline:none;transition:border-color .2s}
.otp-box:focus{border-color:#E50914;box-shadow:0 0 0 3px rgba(229,9,20,.1)}
.otp-box.filled{border-color:#E50914;background:#FFF5F0}
.otp-hint{font-size:10px;color:#8FA3C0;text-align:center;margin-bottom:14px;font-family:'JetBrains Mono',monospace}
.otp-sub{width:100%;border:none;border-radius:10px;padding:13px;font-size:14px;font-weight:700;color:white;cursor:pointer;font-family:'Plus Jakarta Sans',sans-serif;background:linear-gradient(135deg,#1A1F71,#0D1255);box-shadow:0 3px 14px rgba(26,31,113,.28);transition:transform .15s}
.otp-sub:active{transform:scale(.98)}
.otp-sub:disabled{opacity:.45;cursor:default}
.otp-foot{padding:10px 18px;border-top:1px solid #EEF1F7;display:flex;align-items:center;gap:6px;background:#FAFBFD}
.otp-fl{font-size:9px;color:#8FA3C0;font-family:'JetBrains Mono',monospace}

/* ── CHECKOUT ROWS ── */
.crow{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;margin-bottom:6px;border-radius:11px;background:white;border:1px solid #DDE3EE;box-shadow:0 1px 4px rgba(28,43,74,.05);transition:opacity .5s;max-width:640px}
.cl{font-size:12px;color:#5A7090;font-family:'JetBrains Mono',monospace}
.cv{font-size:12px;font-weight:700}

/* ── SUMMARY ── */
.summary{background:white;border-radius:16px;overflow:hidden;border:1.5px solid #A8DECA;box-shadow:0 6px 28px rgba(0,135,90,.1);animation:popIn .6s cubic-bezier(.34,1.4,.64,1);margin-top:4px;max-width:640px}
.sum-h{background:linear-gradient(135deg,#00875A,#006644);padding:18px 20px;display:flex;align-items:center;gap:11px}
.sum-ck{width:40px;height:40px;border-radius:50%;background:rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center;font-size:18px}
.sum-t{font-size:17px;font-weight:800;color:white}
.sum-s{font-size:10px;color:rgba(255,255,255,.7);margin-top:2px;font-family:'JetBrains Mono',monospace}
.stats{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;padding:16px 18px 0}
.stat{text-align:center;padding:12px 6px;background:#F5F7FA;border-radius:11px;border:1px solid #EEF1F7}
.sl{font-size:8px;font-weight:700;color:#8FA3C0;letter-spacing:2px;margin-bottom:5px;font-family:'JetBrains Mono',monospace}
.sv{font-size:16px;font-weight:800}
.tot{margin:12px 18px 16px;padding:11px 14px;border-radius:11px;background:#F0F4FA;border:1px solid #DDE3EE;display:flex;justify-content:space-between;align-items:center}
.tl{font-size:11px;color:#5A7090;font-family:'JetBrains Mono',monospace}
.tv{font-size:14px;font-weight:800;color:#00875A}

.hidden{display:none}

@media(max-width:700px){
  .app{flex-direction:column}
  .pane-left{width:100%;height:auto;flex-direction:row;align-items:center;gap:8px;padding:10px 14px;border-right:none;border-bottom:1px solid #DDE3EE}
  .pl-header{border:none;padding:0;flex-shrink:0}
  .pl-body{display:none}
  .pl-footer{flex:1;padding:0;border:none}
  .pane-right{flex:1;min-height:0;overflow:hidden}
  .card3-grid{grid-template-columns:1fr}
}
</style>
</head>
<body>
<div class="app">

  <!-- LEFT PANE -->
  <div class="pane-left">
    <div class="pl-header">
      <div class="logo-icon">CB</div>
      <div>
        <div class="logo-name">CINEBOT</div>
        <div class="logo-sub">COMMERCE AGENT</div>
      </div>
    </div>

    <div class="pl-body" id="plBody">
      <div class="mascot-wrap">
        <!-- CineBot mascot SVG: cinema-themed character -->
        <svg width="76" height="108" viewBox="0 0 90 128" fill="none" xmlns="http://www.w3.org/2000/svg">
          <ellipse cx="45" cy="124" rx="22" ry="4" fill="#1C2B4A" opacity="0.12"/>
          <!-- Legs -->
          <ellipse cx="33" cy="116" rx="11" ry="5" fill="#0d1e45"/>
          <ellipse cx="57" cy="116" rx="11" ry="5" fill="#0d1e45"/>
          <!-- Body -->
          <path d="M18 70 Q14 80 12 110 L78 110 Q76 80 72 70 Q60 62 45 62 Q30 62 18 70Z" fill="#1C2B4A"/>
          <!-- Shirt detail / film strip on chest -->
          <rect x="33" y="72" width="24" height="16" rx="3" fill="#E50914" opacity="0.85"/>
          <rect x="33" y="72" width="4" height="16" rx="1" fill="#fff" opacity="0.35"/>
          <rect x="53" y="72" width="4" height="16" rx="1" fill="#fff" opacity="0.35"/>
          <rect x="38" y="75" width="14" height="3" rx="1" fill="#fff" opacity="0.5"/>
          <rect x="38" y="81" width="14" height="3" rx="1" fill="#fff" opacity="0.5"/>
          <!-- Arms -->
          <path d="M18 70 Q8 80 10 100 Q14 102 18 100 Q20 82 24 74Z" fill="#1C2B4A"/>
          <ellipse cx="13" cy="102" rx="5" ry="6" fill="#C8956A" transform="rotate(-10 13 102)"/>
          <path d="M72 70 Q82 78 80 98 Q76 100 72 98 Q70 80 66 74Z" fill="#1C2B4A"/>
          <ellipse cx="77" cy="100" rx="5" ry="6" fill="#C8956A" transform="rotate(10 77 100)"/>
          <!-- Neck -->
          <rect x="40" y="54" width="10" height="12" rx="5" fill="#C8956A"/>
          <!-- Head -->
          <ellipse cx="45" cy="38" rx="18" ry="20" fill="#C8956A"/>
          <!-- Hair -->
          <path d="M27 32 Q28 16 45 14 Q62 16 63 32 Q58 22 45 20 Q32 22 27 32Z" fill="#1A1008"/>
          <path d="M27 32 Q24 28 26 38 Q28 34 30 32Z" fill="#1A1008"/>
          <path d="M63 32 Q66 28 64 38 Q62 34 60 32Z" fill="#1A1008"/>
          <!-- Chin -->
          <path d="M31 46 Q33 58 45 60 Q57 58 59 46 Q54 54 45 55 Q36 54 31 46Z" fill="#1A1008" opacity="0.85"/>
          <!-- Mouth -->
          <path d="M38 44 Q42 47 45 46 Q48 47 52 44" stroke="#1A1008" stroke-width="2" stroke-linecap="round" fill="none" opacity="0.9"/>
          <!-- Eyes whites -->
          <ellipse cx="38" cy="36" rx="4" ry="3.5" fill="white"/>
          <ellipse cx="52" cy="36" rx="4" ry="3.5" fill="white"/>
          <!-- Pupils -->
          <ellipse cx="39" cy="36" rx="2.2" ry="2.2" fill="#1A1008"/>
          <ellipse cx="53" cy="36" rx="2.2" ry="2.2" fill="#1A1008"/>
          <!-- Eye shine -->
          <circle cx="40" cy="35" r="0.7" fill="white"/>
          <circle cx="54" cy="35" r="0.7" fill="white"/>
          <!-- Eyebrows -->
          <path d="M34 31 Q38 29 42 31" stroke="#1A1008" stroke-width="1.8" stroke-linecap="round" fill="none"/>
          <path d="M48 31 Q52 29 56 31" stroke="#1A1008" stroke-width="1.8" stroke-linecap="round" fill="none"/>
          <!-- Earring / popcorn bucket icon -->
          <circle cx="27" cy="38" r="2" fill="#E50914" opacity="0.85"/>
        </svg>
        <div class="mascot-label">CINEBOT<br><span>Commerce Agent</span></div>
        <div class="mascot-tag">Expert. Undercover. Best Deal.</div>
      </div>

      <div id="plWelcome">
        <p class="pl-welcome">Tell me what movie you want to watch and when. I'll find the best seats, apply your loyalty points, and handle payment end to end.</p>
        <p class="pl-hint">&#8595; Type your request below and tap send</p>
      </div>

      <div id="plQuery" class="hidden">
        <div class="query-display">
          <div class="query-display-lbl">YOUR REQUEST</div>
          <div class="query-display-txt" id="queryTxt"></div>
        </div>
        <div class="status-box">
          <div class="status-lbl">MISSION STATUS</div>
          <div class="status-stage" id="statusStage"><span class="status-dot"></span>In progress...</div>
        </div>
      </div>

      <div class="pl-pts">
        <div class="pl-pts-icon">⭐</div>
        <div class="pl-pts-info">
          <div class="lbl">LOYALTY POINTS</div>
          <div class="val" id="ptsDisplay">1000 pts</div>
        </div>
      </div>
    </div>

    <div class="pl-footer">
      <div class="quick-btns">
        <button class="qb" onclick="hint('I want to book 2 tickets for Dhurandhar this Sunday afternoon')">🎥 Book Movie</button>
        <button class="qb" onclick="hint('What Hindi movies are playing this week?')">🎬 Now Playing</button>
        <button class="qb" onclick="hint('Show my past bookings')">📋 My Bookings</button>
      </div>
      <div class="input-row">
        <textarea class="chat-input" id="inp" rows="2" placeholder="e.g. Book 2 tickets for Dhurandhar this Sunday afternoon…" oninput="resizeInp(this)" onkeydown="onKey(event)"></textarea>
        <button class="send-btn" id="sendBtn" onclick="send()">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </div>
    </div>
  </div>

  <!-- RIGHT PANE -->
  <div class="pane-right">
    <div class="pr-stage-bar hidden" id="stages">
      <div class="sp" id="s1">SEARCH</div><div class="ss" id="sep1"></div>
      <div class="sp" id="s2">CONFIRM</div><div class="ss" id="sep2"></div>
      <div class="sp" id="s3">PAYMENT</div><div class="ss" id="sep3"></div>
      <div class="sp" id="s4">VERIFY</div><div class="ss" id="sep4"></div>
      <div class="sp" id="s5">DONE</div>
    </div>
    <div class="pr-feed" id="feed">
      <div class="pr-welcome" id="prWelcome">
        <div class="pr-welcome-icon">🎬</div>
        <div class="pr-welcome-txt">Your agentic booking flow will appear here. Type your request on the left to begin.</div>
      </div>
    </div>
  </div>
</div>

<script>
marked.setOptions({breaks:true, gfm:true});

/* ── AUDIO CHIMES ── */
var audioCtx=null;
function ensureAudio(){if(!audioCtx){try{audioCtx=new(window.AudioContext||window.webkitAudioContext)();}catch(e){audioCtx=null;}}if(audioCtx&&audioCtx.state==='suspended')audioCtx.resume();return audioCtx;}
function playNote(ctx,freq,t,dur,vol){try{var osc=ctx.createOscillator(),g=ctx.createGain();osc.connect(g);g.connect(ctx.destination);osc.type='sine';osc.frequency.setValueAtTime(freq,t);g.gain.setValueAtTime(0.001,t);g.gain.linearRampToValueAtTime(vol||0.1,t+0.025);g.gain.setValueAtTime(vol||0.1,t+0.06);g.gain.exponentialRampToValueAtTime(0.001,t+dur);osc.start(t);osc.stop(t+dur+0.08);}catch(e){}}
var CHIMES={scan:[[523,0,.55,.08],[659,.22,.65,.09]],cardReveal:[[523,0,.28,.08],[659,.16,.28,.09],[784,.32,.5,.08]],cardPick:[[659,0,.24,.1],[784,.14,.24,.11],[880,.28,.24,.11],[1047,.42,.55,.12]],otpOk:[[784,0,.22,.11],[1047,.16,.26,.13],[1319,.34,.6,.11]],complete:[[523,0,.2,.09],[659,.14,.2,.1],[784,.28,.2,.11],[1047,.42,.2,.12],[1319,.56,.2,.11],[1047,.7,.7,.09]]};
function chime(type){var ctx=ensureAudio();if(!ctx)return;var notes=CHIMES[type]||CHIMES.scan,now=ctx.currentTime;notes.forEach(function(n){playNote(ctx,n[0],now+n[1],n[2],n[3]);});}

/* ── STATE ── */
const USER_ID='user_ram_001';
var feed=document.getElementById('feed'),inp=document.getElementById('inp'),sBtn=document.getElementById('sendBtn');
var _bookingId=null,_selectedCardOption=null,_selCardIdx=null;
var wait=function(ms){return new Promise(function(r){setTimeout(r,ms);});};

/* ── HELPERS ── */
function resizeInp(el){el.style.height='auto';el.style.height=Math.min(el.scrollHeight,90)+'px';}
function onKey(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}}
function goBottom(){setTimeout(function(){feed.scrollTop=feed.scrollHeight;},80);}
function hint(t){inp.value=t;resizeInp(inp);inp.focus();}
function lock(){inp.disabled=true;sBtn.disabled=true;}
function unlock(){inp.disabled=false;sBtn.disabled=false;}
function esc(t){var d=document.createElement('div');d.appendChild(document.createTextNode(t));return d.innerHTML;}

function setStage(n){
  var lbl=['','Searching','Confirming','Payment','Verifying','Complete'];
  for(var i=1;i<=5;i++){document.getElementById('s'+i).className='sp'+(i<n?' done':(i===n?' active':''));if(i<5)document.getElementById('sep'+i).className='ss'+(i<n?' done':'');}
  var el=document.getElementById('statusStage');
  if(el)el.innerHTML='<span class="status-dot'+(n===5?' hidden':'')+'"></span>'+lbl[n];
}

function showPostSend(txt){
  document.getElementById('plWelcome').classList.add('hidden');
  document.getElementById('plQuery').classList.remove('hidden');
  document.getElementById('queryTxt').textContent=txt;
}

function userBubble(txt){
  var d=document.createElement('div');d.className='msg user';
  d.innerHTML='<div class="av us">👤</div><div class="bbl us">'+esc(txt)+'</div>';
  feed.appendChild(d);goBottom();
}

async function tw(el,text,spd){
  return new Promise(function(res){var i=0;var t=setInterval(function(){i++;el.innerHTML=text.slice(0,i)+(i<text.length?'<span class="cur">▌</span>':'');if(i>=text.length){clearInterval(t);res();}},spd||20);});
}

async function agentMsg(text,ok,isMarkdown){
  var d=document.createElement('div');d.className='msg';
  d.innerHTML='<div class="av '+(ok?'ok':'ag')+'">'+(ok?'✓':'🎬')+'</div><div class="bbl ag"><span class="tw2"></span></div>';
  feed.appendChild(d);goBottom();
  var sp=d.querySelector('.tw2');
  if(isMarkdown){
    await tw(sp,text,18);
    sp.innerHTML=marked.parse(text);
  } else {
    await tw(sp,text,20);
  }
  await wait(200);
  return d.querySelector('.bbl');
}

function secLbl(t){var d=document.createElement('div');d.className='sec';d.textContent=t;feed.appendChild(d);}

/* ── SEND ── */
async function send(){
  var txt=inp.value.trim();if(!txt)return;
  ensureAudio();
  lock();
  document.getElementById('prWelcome').style.display='none';
  document.getElementById('stages').classList.remove('hidden');
  showPostSend(txt);
  userBubble(txt);
  inp.value='';resizeInp(inp);
  await wait(300);
  await runChatFlow(txt);
}

/* ── MAIN FLOW: send to backend, handle response, then show payment UI ── */
async function runChatFlow(userText){
  setStage(1);
  chime('scan');

  const tid=addTypingIndicator();
  let botReply='';
  try{
    const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:USER_ID,message:userText})});
    const d=await r.json();
    removeTyping(tid);
    botReply=d.response||('❌ '+(d.error||'Unknown error'));
  }catch(e){
    removeTyping(tid);
    botReply='❌ Connection error: '+e.message;
  }

  // Scan reply for booking ID
  var bkMatch=botReply.match(/\\b(BK\\d{3,})\\b/);
  if(bkMatch)_bookingId=bkMatch[1];

  // Detect current stage from reply content
  var lowerReply=botReply.toLowerCase();
  if(lowerReply.includes('seats reserved')||lowerReply.includes('booking id')){setStage(2);}
  else if(lowerReply.includes('payment')||lowerReply.includes('option 1')||lowerReply.includes('option 2')){setStage(3);}

  var bubbleEl=await agentMsg(botReply,false,true);
  refreshPoints();

  // If this is the payment step, render the card comparison UI
  if(_bookingId&&(lowerReply.includes('payment')&&(lowerReply.includes('option')||lowerReply.includes('points')))){
    setStage(3);
    await wait(400);
    await renderPaymentCards(bubbleEl);
  }

  unlock();
  goBottom();
}

/* ── TYPING INDICATOR ── */
function addTypingIndicator(){
  var d=document.createElement('div');d.className='msg';var id='t'+Date.now();d.id=id;
  d.innerHTML='<div class="av ag">🎬</div><div class="bbl ag" style="padding:12px 15px"><span style="display:flex;gap:5px"><span style="width:7px;height:7px;background:#ccc;border-radius:50%;animation:bop 1.3s ease infinite"></span><span style="width:7px;height:7px;background:#ccc;border-radius:50%;animation:bop 1.3s ease .2s infinite"></span><span style="width:7px;height:7px;background:#ccc;border-radius:50%;animation:bop 1.3s ease .4s infinite"></span></span></div>';
  feed.appendChild(d);
  var s=document.createElement('style');s.textContent='@keyframes bop{0%,80%,100%{transform:scale(.8);opacity:.4}40%{transform:scale(1.1);opacity:1}}';document.head.appendChild(s);
  goBottom();return id;
}
function removeTyping(id){var e=document.getElementById(id);if(e)e.remove();}

/* ── REFRESH POINTS BADGE ── */
function refreshPoints(){
  fetch('/api/users/'+USER_ID+'/profile').then(r=>r.json()).then(p=>{
    if(p.success&&p.profile&&p.profile.cc_points!==undefined)
      document.getElementById('ptsDisplay').textContent=p.profile.cc_points+' pts';
  }).catch(()=>{});
}

/* ── PAYMENT CARDS ── */
async function renderPaymentCards(bubbleEl){
  if(!_bookingId)return;
  try{
    const r=await fetch('/api/bookings/'+_bookingId+'/payment-recommendation');
    const data=await r.json();
    if(!data.success)return;
    chime('cardReveal');
    var wrap=buildCardGrid(data);
    bubbleEl.appendChild(wrap);
    goBottom();
    await wait(600);
    await agentMsg('I\'ve compared all your options above. The highlighted card gives you the best return. Tap to select, then confirm payment.',false,false);
  }catch(e){}
}

function cardBank(name){
  if(name.includes('HDFC'))return 'HDFC Bank';
  if(name.includes('ICICI'))return 'ICICI Bank';
  if(name.includes('SBI'))return 'SBI';
  if(name.includes('Axis'))return 'Axis Bank';
  if(name.includes('Kotak'))return 'Kotak Bank';
  return name.split(' ')[0]+' Bank';
}

function buildCardGrid(data){
  secLbl('PAYMENT OPTIONS · COMPARE & CHOOSE');
  var rec=data.recommendation&&data.recommendation.recommended_option;
  var own=data.current_card_option;
  var wrap=document.createElement('div');wrap.style.maxWidth='640px';

  var grid=document.createElement('div');grid.className='card3-grid';wrap.appendChild(grid);

  // Card 1: Loyalty points
  var ownSaving=own.discount_amount;
  var ownPayable=own.estimated_payable;
  var c1=makeCard({
    idx:0,isNew:false,isBest:rec==='redeem_own_points',
    typeLabel:'YOU OWN THIS',typeCls:'background:#d4edda;color:#155724;border:1px solid #c3e6cb',
    applyTag:false,
    bank:own.credit_card_bank,name:'Loyalty Points Redemption',
    rows:[
      {l:'Points used',v:own.points_used+' pts',c:'#d97706'},
      {l:'Rate',v:'Rs. 0.50 / pt',c:'#16a34a'},
      {l:'Discount',v:'Rs. '+ownSaving,c:'#16a34a'},
      {l:'Bank offer',v:'No ✗',c:'#dc2626'},
      {l:'Total saving',v:'Rs. '+ownSaving,c:'#1C2B4A'},
    ],
    total:'Rs. '+ownPayable,totalColor:'#d97706',totalBg:'#fffbeb',
    optionKey:'redeem_own_points',label:'Loyalty Points'
  });
  grid.appendChild(c1);

  // Cards 2-3: Top 2 credit cards
  var topCards=(data.all_card_options||[]).slice(0,2);
  var amtColors=['#f97316','#2563eb'];
  topCards.forEach(function(card,i){
    var cc=makeCard({
      idx:i+1,isNew:true,isBest:rec==='best_available_card'&&i===0,
      typeLabel:'NEW CARD',typeCls:'background:#fff3cd;color:#856404;border:1px solid #ffc107',
      applyTag:true,
      bank:cardBank(card.card_name),name:card.card_name,
      rows:[
        {l:'Discount',v:card.discount_percent+'% off',c:'#d97706'},
        {l:'Saving',v:'Rs. '+card.discount_amount,c:'#16a34a'},
        {l:'Bank offer',v:'Yes ✓',c:'#16a34a'},
        {l:'Instant apply',v:'Yes ✓',c:'#16a34a'},
        {l:'Total saving',v:'Rs. '+card.discount_amount,c:'#1C2B4A'},
      ],
      total:'Rs. '+card.final_payable,totalColor:amtColors[i],totalBg:'#f0f9ff',
      optionKey:'best_available_card',label:card.card_name
    });
    grid.appendChild(cc);
  });

  var btn=document.createElement('button');btn.className='conf-btn hidden';btn.id='payConfBtn';btn.textContent='Confirm Payment →';
  btn.onclick=function(){confirmPayment();};
  wrap.appendChild(btn);
  return wrap;
}

function makeCard(o){
  var el=document.createElement('div');
  el.className='ccard'+(o.isNew?' ncs':'')+(o.isBest?' sel':'');
  el.id='cc'+o.idx;
  if(o.isBest){var b=document.createElement('div');b.className='top-badge tbg';b.textContent='BEST RETURN';el.appendChild(b);}
  var typeEl=document.createElement('div');typeEl.className='ccard-type';typeEl.style.cssText=o.typeCls;typeEl.textContent=o.typeLabel;el.appendChild(typeEl);
  if(o.applyTag){var at=document.createElement('div');at.style.cssText='display:inline-block;background:#d97706;color:#fff;font-size:8px;font-weight:700;padding:2px 7px;border-radius:8px;margin-bottom:5px;margin-top:2px;font-family:JetBrains Mono,monospace';at.textContent='APPLY INSTANTLY';el.appendChild(at);}
  var bankEl=document.createElement('div');bankEl.className='ccard-bank';bankEl.textContent=o.bank;el.appendChild(bankEl);
  var nameEl=document.createElement('div');nameEl.className='ccard-name';nameEl.textContent=o.name;el.appendChild(nameEl);
  o.rows.forEach(function(row){var r=document.createElement('div');r.className='ccard-row';r.innerHTML='<span class="ccard-rl">'+esc(row.l)+'</span><span class="ccard-rv" style="color:'+row.c+'">'+esc(row.v)+'</span>';el.appendChild(r);});
  var tot=document.createElement('div');tot.className='ccard-total';tot.style.background=o.totalBg;
  tot.innerHTML='<div class="ccard-tl">YOU PAY</div><div class="ccard-tv" style="color:'+o.totalColor+'">'+esc(o.total)+'</div>';
  el.appendChild(tot);
  el.onclick=(function(idx,optKey,lbl){return function(){pickPayCard(idx,optKey,lbl);};})(o.idx,o.optionKey,o.label);
  return el;
}

function pickPayCard(idx,optKey,label){
  _selCardIdx=idx;_selectedCardOption={key:optKey,label:label};
  document.querySelectorAll('.ccard').forEach(function(c,j){c.classList.toggle('sel',j===idx);});
  chime('cardPick');
  var btn=document.getElementById('payConfBtn');
  if(btn){btn.classList.remove('hidden');btn.textContent='Pay with '+label+' →';}
  goBottom();
}

async function confirmPayment(){
  if(!_selectedCardOption||!_bookingId)return;
  document.getElementById('payConfBtn').disabled=true;
  userBubble('Use '+_selectedCardOption.label);
  await wait(400);
  setStage(4);
  await runOTPVerification();
}

/* ── OTP ── */
async function runOTPVerification(){
  await agentMsg('Redirecting to Mastercard SecureCode for 2-factor authentication…',false,false);
  await wait(1600);
  secLbl('PAYMENT VERIFICATION · MASTERCARD SECURECODE™');
  var oc=document.createElement('div');oc.className='otp-card';oc.id='otpCard';
  var boxes='';for(var b=0;b<6;b++)boxes+='<input class="otp-box" id="ob'+b+'" maxlength="1" inputmode="numeric" type="tel">';
  var amtText=document.querySelector('.ccard.sel .ccard-tv');var amtStr=amtText?amtText.textContent:'Amount';
  oc.innerHTML='<div class="otp-hdr"><div style="display:flex;align-items:center"><div class="mc-r"></div><div class="mc-y"></div></div>'+
    '<div style="margin-left:10px"><div class="otp-ht">Mastercard SecureCode™</div><div class="otp-hs">3D Secure 2.0 Authentication</div></div></div>'+
    '<div class="otp-body"><div class="otp-merch">'+
    '<div><div class="otp-ml">MERCHANT</div><div class="otp-mv">BookMyShow India</div></div>'+
    '<div style="text-align:right"><div class="otp-ml">AMOUNT</div><div class="otp-mv">'+esc(amtStr)+'</div></div></div>'+
    '<div class="otp-info">A One-Time Password has been sent to your registered mobile <strong>••••••7823</strong>. Enter it below to authorise payment.</div>'+
    '<div class="otp-fields">'+boxes+'</div>'+
    '<div class="otp-hint">Did not receive it? <a href="#" onclick="return false">Resend in 0:28</a></div>'+
    '<button class="otp-sub" id="osub" onclick="verifyOTP()" disabled>Verify &amp; Pay →</button></div>'+
    '<div class="otp-foot"><span style="font-size:13px">🔒</span><span class="otp-fl">256-bit SSL · PCI DSS Compliant</span>'+
    '<div style="margin-left:auto;display:flex;align-items:center;gap:3px;font-size:8px;color:#1A1F71;font-weight:700;letter-spacing:.5px"><div style="display:flex;align-items:center"><div style="width:11px;height:11px;border-radius:50%;background:#EB001B"></div><div style="width:11px;height:11px;border-radius:50%;background:#F79E1B;margin-left:-4px;opacity:.95"></div></div>&nbsp;SecureCode</div></div>';
  feed.appendChild(oc);goBottom();
  for(var b2=0;b2<6;b2++){
    (function(idx){
      var box=document.getElementById('ob'+idx);
      box.addEventListener('input',function(){otpIn(box,idx);});
      box.addEventListener('keydown',function(e){otpKey(e,idx);});
    })(b2);
  }
  await wait(300);document.getElementById('ob0').focus();
}

function otpIn(el,idx){
  el.value=el.value.replace(/[^0-9]/g,'');
  el.classList.toggle('filled',!!el.value);
  if(el.value&&idx<5)document.getElementById('ob'+(idx+1)).focus();
  var full=true;for(var i=0;i<6;i++){if(!document.getElementById('ob'+i).value){full=false;break;}}
  document.getElementById('osub').disabled=!full;
}

function otpKey(e,idx){
  if(e.key==='Backspace'&&!document.getElementById('ob'+idx).value&&idx>0)document.getElementById('ob'+(idx-1)).focus();
}

async function verifyOTP(){
  var sub=document.getElementById('osub');
  sub.disabled=true;sub.textContent='Verifying...';
  for(var i=0;i<6;i++)document.getElementById('ob'+i).disabled=true;
  await wait(1800);
  chime('otpOk');
  sub.textContent='✓ Verified — Payment Authorised';sub.style.background='linear-gradient(135deg,#00875A,#006644)';
  await wait(800);
  await executePaymentAndSummary();
}

/* ── PAYMENT EXECUTION + SUMMARY ── */
async function executePaymentAndSummary(){
  setStage(5);
  await agentMsg('Payment authenticated. Confirming your booking…',false,false);
  await wait(1200);

  // Hit the pay API
  var txnId='TXN-OK';var finalAmt='';var paid=false;
  try{
    const r=await fetch('/api/bookings/'+_bookingId+'/pay',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({payment_option:_selectedCardOption.key,points_to_redeem:0})});
    const d=await r.json();
    if(d.success||d.transaction_id){paid=true;txnId=d.transaction_id||txnId;finalAmt=d.final_amount||d.total_amount||'';}
  }catch(e){}

  chime('complete');
  refreshPoints();

  secLbl('BOOKING CONFIRMED · SUMMARY');
  var amtEl=document.querySelector('.ccard.sel .ccard-tv');
  var amtStr=amtEl?amtEl.textContent:(finalAmt?'Rs. '+finalAmt:'');
  var saveEl=document.querySelector('.ccard.sel .ccard-rv[style*="16a34a"]');
  var saveStr=saveEl?saveEl.textContent:'—';

  var rows=[
    {l:'Booking ID',v:_bookingId,c:'#1C2B4A'},
    {l:'Transaction ID',v:txnId,c:'#1C2B4A'},
    {l:'Payment method',v:_selectedCardOption.label,c:'#d97706'},
    {l:'Discount applied',v:saveStr,c:'#16a34a'},
  ];
  var rw=document.createElement('div');rw.style.marginBottom='18px';
  rows.forEach(function(row,i){
    var r=document.createElement('div');r.className='crow';r.id='cr'+i;r.style.opacity='0';
    r.innerHTML='<span class="cl">'+esc(row.l)+'</span><span class="cv" style="color:'+row.c+'">'+esc(row.v)+'</span>';
    rw.appendChild(r);
  });
  feed.appendChild(rw);
  for(var i=0;i<4;i++){await wait(700);document.getElementById('cr'+i).style.opacity='1';goBottom();}
  await wait(500);

  var ptsEl=document.getElementById('ptsDisplay');var ptsLeft=ptsEl?ptsEl.textContent:'—';
  var sum=document.createElement('div');sum.className='summary';
  sum.innerHTML='<div class="sum-h"><div class="sum-ck">✓</div><div><div class="sum-t">Booking Confirmed!</div><div class="sum-s">'+esc(_bookingId)+' · Enjoy the show 🍿</div></div></div>'+
    '<div class="stats">'+
    '<div class="stat"><div class="sl">YOU PAID</div><div class="sv" style="color:#1C2B4A">'+esc(amtStr)+'</div></div>'+
    '<div class="stat"><div class="sl">YOU SAVED</div><div class="sv" style="color:#16a34a">'+esc(saveStr)+'</div></div>'+
    '<div class="stat"><div class="sl">PTS LEFT</div><div class="sv" style="color:#d97706">'+esc(ptsLeft)+'</div></div>'+
    '</div><div class="tot"><span class="tl">Transaction: '+esc(txnId)+'</span><span class="tv">✅ Complete</span></div>';
  feed.appendChild(sum);goBottom();
  await wait(400);
  await agentMsg('Your seats are reserved! 🎬 Show your booking ID **'+_bookingId+'** at the theatre. Enjoy the movie, Ram! 🍿',true,false);
}
</script>

</body>
</html>"""

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

/* ── Payment Cards UI ───────────────────────────── */
.pay-wrap{margin:14px 0 4px}
.pay-hdr{font-size:10px;font-weight:700;color:#999;letter-spacing:2px;text-align:center;margin-bottom:14px}
.pay-cards{display:flex;gap:10px;flex-wrap:wrap}
.pay-card{flex:1;min-width:145px;max-width:195px;border:1.5px solid #e2e2e6;border-radius:14px;background:#fff;position:relative;padding-top:10px;display:flex;flex-direction:column}
.pay-card.best{border-color:#e0a800;box-shadow:0 4px 18px rgba(224,168,0,.28)}
.pay-best-badge{position:absolute;top:-11px;left:50%;transform:translateX(-50%);background:#e0a800;color:#fff;font-size:9px;font-weight:800;padding:3px 12px;border-radius:20px;letter-spacing:.8px;white-space:nowrap}
.pay-flags{display:flex;gap:4px;flex-wrap:wrap;padding:4px 10px 0;min-height:22px}
.pay-flag{font-size:9px;font-weight:700;border-radius:20px;padding:2px 7px;white-space:nowrap}
.pay-flag.own{background:#d4edda;color:#155724;border:1px solid #c3e6cb}
.pay-flag.new-card{background:#fff3cd;color:#856404;border:1px solid #ffc107}
.pay-flag.apply{background:#e0a800;color:#fff}
.pay-body{padding:8px 12px 0;flex:1}
.pay-bank{font-size:10px;color:#888;margin-bottom:1px}
.pay-name{font-size:12px;font-weight:800;color:#1a1a1a;margin-bottom:8px;line-height:1.3}
.pay-row{display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-top:1px solid #f0f0f2;font-size:11px;gap:4px}
.pay-row .lbl{color:#555;flex-shrink:0}
.pay-row .pval{font-weight:700;text-align:right}
.pval-green{color:#16a34a}.pval-orange{color:#d97706}.pval-red{color:#dc2626}.pval-blue{color:#2563eb}
.pay-foot{background:#f9f9fb;border-top:1px solid #eee;padding:10px 12px 6px;text-align:center;border-radius:0 0 0 0}
.pay-foot-lbl{font-size:9px;font-weight:700;color:#999;letter-spacing:1.5px;margin-bottom:2px}
.pay-foot-amt{font-size:20px;font-weight:900}
.pay-foot-amt.gold{color:#e0a800}.pay-foot-amt.orange{color:#f97316}.pay-foot-amt.blue{color:#2563eb}
.pay-btn{width:calc(100% - 20px);margin:6px 10px 10px;padding:8px;border:none;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;transition:opacity .18s;display:block}
.pay-btn.primary{background:#E50914;color:#fff}.pay-btn.secondary{background:#f0f0f2;color:#1a1a1a}
.pay-btn:hover:not(:disabled){opacity:.82}.pay-btn:disabled{opacity:.5;cursor:default}
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
    <button class="qb" onclick="hint('I want to book 2 tickets for Dhurandhar this Sunday afternoon')">🎥 Book Movies</button>
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

<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script>
marked.setOptions({breaks:true, gfm:true});

const USER_ID = 'user_ram_001';
const chat    = document.getElementById('chatArea');
let _bookingId = null;

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
      const bub=addMsg(d.response,'bot',true);
      scanForBookingId(d.response);
      if(isPaymentStep(d.response)) maybeRenderPaymentCards(bub);
    }
    else addMsg('❌ Error: '+(d.error||'Unknown error'),'bot',false);
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
  return b;
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

function scanForBookingId(text){
  const m=text.match(/\b(BK\d{3,})\b/);
  if(m) _bookingId=m[1];
}
function isPaymentStep(text){
  return /option\s*[12]/i.test(text)&&/(loyalty|points|credit card|payment option)/i.test(text);
}
async function maybeRenderPaymentCards(bubbleEl){
  if(!_bookingId) return;
  try{
    const r=await fetch('/api/bookings/'+_bookingId+'/payment-recommendation');
    const data=await r.json();
    if(!data.success) return;
    bubbleEl.appendChild(buildPaymentCards(data));
    chat.scrollTop=chat.scrollHeight;
  }catch(e){}
}
function cardBank(name){
  if(name.includes('HDFC')) return 'HDFC Bank';
  if(name.includes('ICICI')) return 'ICICI Bank';
  if(name.includes('SBI')) return 'SBI';
  if(name.includes('Axis')) return 'Axis Bank';
  if(name.includes('Kotak')) return 'Kotak Bank';
  return name.split(' ')[0]+' Bank';
}
function buildPaymentCards(data){
  const wrap=document.createElement('div'); wrap.className='pay-wrap';
  const hdr=document.createElement('div'); hdr.className='pay-hdr'; hdr.textContent='PAYMENT OPTIONS \u00b7 COMPARE & CHOOSE'; wrap.appendChild(hdr);
  const cardsEl=document.createElement('div'); cardsEl.className='pay-cards'; wrap.appendChild(cardsEl);
  const rec=data.recommendation&&data.recommendation.recommended_option;
  const own=data.current_card_option;
  // Card 1 — Loyalty Points
  cardsEl.appendChild(makePayCard({
    best:rec==='redeem_own_points', flags:[{label:'YOU OWN THIS',cls:'own'}],
    bank:own.credit_card_bank, name:'Loyalty Points Redemption',
    rows:[
      {lbl:'Points used',val:own.points_used+' pts',cls:'pval-orange'},
      {lbl:'Rate',val:'Rs.0.50/pt',cls:'pval-green'},
      {lbl:'Discount',val:'Rs.'+own.discount_amount,cls:'pval-green'},
      {lbl:'Bank offer',val:'No \u2717',cls:'pval-red'},
      {lbl:'Total benefit',val:'Rs.'+own.discount_amount,cls:'pval-green'}
    ],
    payable:own.estimated_payable, amtCls:'gold',
    optionKey:'redeem_own_points', bookingId:data.booking_id, cardLabel:'Loyalty Points'
  }));
  // Cards 2-3 — Top 2 credit cards
  const topCards=(data.all_card_options||[]).slice(0,2);
  const amtClasses=['orange','blue'];
  topCards.forEach(function(card,i){
    cardsEl.appendChild(makePayCard({
      best:rec==='best_available_card'&&i===0,
      flags:[{label:'NEW CARD',cls:'new-card'},{label:'APPLY INSTANTLY',cls:'apply'}],
      bank:cardBank(card.card_name), name:card.card_name,
      rows:[
        {lbl:'Discount',val:card.discount_percent+'% off',cls:'pval-orange'},
        {lbl:'Savings',val:'Rs.'+card.discount_amount,cls:'pval-green'},
        {lbl:'Bank offer',val:'Yes \u2713',cls:'pval-green'},
        {lbl:'Apply instantly',val:'Yes \u2713',cls:'pval-green'},
        {lbl:'Total benefit',val:'Rs.'+card.discount_amount,cls:'pval-green'}
      ],
      payable:card.final_payable, amtCls:amtClasses[i],
      optionKey:'best_available_card', bookingId:data.booking_id, cardLabel:card.card_name
    }));
  });
  return wrap;
}
function makePayCard(o){
  const card=document.createElement('div');
  card.className='pay-card'+(o.best?' best':'');
  if(o.best){const b=document.createElement('div');b.className='pay-best-badge';b.textContent='BEST RETURN';card.appendChild(b);}
  const flagsEl=document.createElement('div'); flagsEl.className='pay-flags';
  o.flags.forEach(function(f){const s=document.createElement('span');s.className='pay-flag '+f.cls;s.textContent=f.label;flagsEl.appendChild(s);});
  card.appendChild(flagsEl);
  const body=document.createElement('div'); body.className='pay-body';
  body.innerHTML='<div class="pay-bank">'+esc(o.bank)+'</div><div class="pay-name">'+esc(o.name)+'</div>';
  o.rows.forEach(function(row){const r=document.createElement('div');r.className='pay-row';r.innerHTML='<span class="lbl">'+esc(row.lbl)+'</span><span class="pval '+row.cls+'">'+esc(row.val)+'</span>';body.appendChild(r);});
  card.appendChild(body);
  const foot=document.createElement('div'); foot.className='pay-foot';
  foot.innerHTML='<div class="pay-foot-lbl">YOU PAY</div><div class="pay-foot-amt '+o.amtCls+'">Rs.'+o.payable+'</div>';
  card.appendChild(foot);
  const btn=document.createElement('button');
  btn.className='pay-btn '+(o.best?'primary':'secondary');
  btn.textContent='Pay Rs.'+o.payable;
  btn.onclick=function(){execPayment(o.bookingId,o.optionKey,btn,o.cardLabel);};
  card.appendChild(btn);
  return card;
}
async function execPayment(bookingId,option,btn,cardLabel){
  btn.disabled=true; btn.textContent='Processing...';
  try{
    const r=await fetch('/api/bookings/'+bookingId+'/pay',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({payment_option:option,points_to_redeem:0})
    });
    const d=await r.json();
    if(d.success||d.transaction_id){
      btn.textContent='\u2705 Paid!'; btn.style.background='#16a34a'; btn.style.color='#fff';
      addMsg('\u2705 **Payment confirmed** via '+cardLabel+'!\n\nTransaction ID: '+(d.transaction_id||'TXN-OK'),'bot',true);
    } else { btn.textContent='Retry'; btn.disabled=false; }
  }catch(e){ btn.textContent='Error \u2014 Retry'; btn.disabled=false; }
}

document.getElementById('inp').addEventListener('keydown',e=>{
  if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}
});
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
