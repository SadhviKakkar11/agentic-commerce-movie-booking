# Project Structure & File Navigation Guide

## 📁 Complete Project Layout

```
c:\Users\sakakkar\movie-ticket-booking-agent/
│
├── 📄 README.md
│   └─ Overview of the entire project
│
├── 📄 QUICK_START.md ⭐ START HERE
│   └─ 5-minute quick start guide
│
├── 📄 IMPLEMENTATION_GUIDE.md
│   └─ Comprehensive 500+ line implementation guide with examples
│
├── 📄 requirements.txt
│   └─ Python dependencies (anthropic, flask, etc.)
│
├── 📄 .env.example
│   └─ Copy this to .env and add ANTHROPIC_API_KEY
│
├── 🗂️ backend/
│   │
│   ├── 📄 __init__.py
│   │   └─ Makes backend a Python package
│   │
│   ├── 📄 models.py (100 lines)
│   │   └─ Data models:
│   │      • Movie - title, genre, rating, duration, description
│   │      • Theatre - name, location, amenities, capacity
│   │      • Show - movie, theatre, time, price, available_seats
│   │      • Booking - confirmation details, seats, payment status
│   │
│   ├── 📄 database.py (450+ lines) ⭐ KEY FILE
│   │   └─ MockDatabase class:
│   │      • _init_movies() - Creates 10 sample movies
│   │      • _init_theatres() - Creates 5 sample theatres
│   │      • _init_shows() - Generates tomorrow's shows
│   │      • query methods: search_movies(), get_shows_for_movie()
│   │      • booking methods: create_booking(), cancel_booking()
│   │
│   ├── 📄 routes.py (280+ lines)
│   │   └─ Flask API endpoints:
│   │      GET  /api/movies             - List/search movies
│   │      GET  /api/movies/<id>        - Movie details
│   │      GET  /api/theatres           - List theatres
│   │      GET  /api/theatres/<id>      - Theatre details
│   │      GET  /api/shows              - Search shows
│   │      GET  /api/shows/<id>         - Show details
│   │      GET  /api/shows/movie/<id>   - Shows for a movie
│   │      POST /api/bookings           - Create booking
│   │      GET  /api/bookings/<id>      - Booking details
│   │      POST /api/bookings/<id>/cancel - Cancel booking
│   │      GET  /api/health             - Health check
│   │
│   └── 📄 app.py (30 lines)
│       └─ Flask app factory and setup
│
├── 🗂️ agent/
│   │
│   ├── 📄 __init__.py
│   │   └─ Makes agent a Python package
│   │
│   ├── 📄 config.py (20 lines)
│   │   └─ Configuration:
│   │      • ANTHROPIC_API_KEY - from .env
│   │      • ANTHROPIC_MODEL - defaults to claude-3-5-sonnet
│   │      • BACKEND_URL - localhost:5000
│   │
│   ├── 📄 prompts.py (50 lines)
│   │   └─ System prompts:
│   │      • SYSTEM_PROMPT - Instructions for Claude
│   │      • USER_CONTEXT_TEMPLATE - User preferences format
│   │
│   ├── 📄 tools.py (350+ lines) ⭐ KEY FILE
│   │   └─ Tool definitions:
│   │      • TOOLS list with 11 tool definitions
│   │      • ToolHandler class with 11 methods
│   │        1. search_movies()
│   │        2. get_movie_details()
│   │        3. get_theatres()
│   │        4. get_theatre_details()
│   │        5. search_shows()
│   │        6. get_show_details()
│   │        7. get_shows_for_movie()
│   │        8. book_tickets()
│   │        9. get_booking_details()
│   │       10. get_user_bookings()
│   │       11. cancel_booking()
│   │      • process_tool_call() - Routes tool calls
│   │
│   └── 📄 agent.py (200+ lines) ⭐ KEY FILE
│       └─ MovieBookingAgent class:
│          • __init__(user_id) - Initialize agent
│          • chat(user_message) - Main conversation method
│          • _get_claude_response() - Call Claude API
│          • _handle_tool_use() - Process tool calls
│          • _extract_text_response() - Get text from response
│          • clear_history() - Reset conversation
│          • get_history() - View conversation history
│          • run_agent_loop() - Interactive CLI loop
│
├── 🗂️ examples/
│   │
│   ├── 📄 __init__.py
│   │   └─ Makes examples a Python package
│   │
│   ├── 📄 simple_booking.py (40 lines) ⭐ START HERE IF TESTING
│   │   └─ Predefined conversation:
│   │      1. Search for action movie
│   │      2. Ask for theatre details
│   │      3. Book 2 tickets
│   │      Shows expected flow and outputs
│   │
│   ├── 📄 advanced_agent.py (80 lines)
│   │   └─ Advanced scenarios:
│   │      • Scenario 1: Filtered search
│   │      • Scenario 2: Location-based search
│   │      • Scenario 3: Complex booking requirements
│   │      • Scenario 4: Follow-up refinements
│   │      • Scenario 5: View past bookings
│   │
│   └── 📄 web_ui.py (200 lines)
│       └─ Web interface:
│          • Flask server on port 5001
│          • HTML/CSS/JavaScript chat UI
│          • Real-time messaging
│          • Session management
│
└── 📚 DOCUMENTATION FILES
    ├── This file (FILE_STRUCTURE.md)
    ├── README.md - Project overview
    ├── QUICK_START.md - 5-minute startup
    └── IMPLEMENTATION_GUIDE.md - Comprehensive guide
```

---

## 🚀 How to Navigate This Project

### For Beginners: Start Here
1. Read: `QUICK_START.md` (5 min)
2. Run: `python -m backend.app` (Terminal 1)
3. Run: `python agent/agent.py` (Terminal 2)
4. Chat: Try booking a movie

### For Understanding the Code
1. Study: `backend/models.py` - Data structures
2. Review: `backend/database.py` - Mock data creation
3. Read: `backend/routes.py` - API endpoints
4. Analyze: `agent/tools.py` - Tool definitions (11 tools)
5. Debug: `agent/agent.py` - Agent main logic

### For Running Examples
1. `python examples/simple_booking.py` - Basic example
2. `python examples/advanced_agent.py` - Complex scenarios
3. `python examples/web_ui.py` - Web interface

### For Customization
1. Edit `backend/database.py` to add/change movies
2. Modify `agent/prompts.py` to change Claude's personality
3. Add new tools in `agent/tools.py` and `backend/routes.py`

---

## 📊 Data Flow Diagram

```
USER INPUT (Chat message)
    │
    ▼
┌──────────────────────────────────┐
│ agent/agent.py                   │
│ MovieBookingAgent.chat()         │
└──────────────────────────────────┘
    │
    ├─→ Add message to history
    │
    ├─→ Call Claude API with tools
    │   (system prompt + tools + message)
    │
    ▼
┌──────────────────────────────────┐
│ Claude Determines Which Tools    │
│ to Call (if any needed)          │
└──────────────────────────────────┘
    │
    ├─→ Tool Use? ──Yes──→ agent/agent.py
    │                      _handle_tool_use()
    │                           │
    │                           ▼
    │                    agent/tools.py
    │                    process_tool_call()
    │                           │
    │                           ▼
    │                    ToolHandler class
    │                    Makes HTTP request
    │                           │
    │                           ▼
    │                    backend/routes.py
    │                    Flask API endpoints
    │                           │
    │                           ▼
    │                    backend/database.py
    │                    Query/modify data
    │                           │
    │                    ◄──────┴──────────
    │
    ├─→ No More Tools? ──Yes──→
    │
    ▼
┌──────────────────────────────────┐
│ Extract Final Response from      │
│ Claude's Message                 │
└──────────────────────────────────┘
    │
    ▼
RETURN RESPONSE TO USER
```

---

## 🔑 Key File Relationships

### Files You'll Modify First

1. **backend/database.py**
   - To customize movies, theatres, shows
   - Change pricing, add more movies
   - Add real database connection

2. **agent/prompts.py**
   - Change Claude's personality/instructions
   - Add domain-specific knowledge
   - Adjust response tone

3. **agent/tools.py**
   - Add new capabilities
   - Modify tool definitions
   - Change how tools interact with API

### Files You'll Reference

```
API Endpoint ← routes.py ← models.py
     ↑
     └← database.py (Logic)
        
Claude ← tools.py (Maps to API)
  ↑
  └← agent.py (Main logic)
```

---

## 📝 File Purpose Summary

| File | Purpose | Lines | Key Classes/Functions |
|------|---------|-------|----------------------|
| models.py | Data structures | 100 | Movie, Theatre, Show, Booking |
| database.py | Mock data & queries | 450+ | MockDatabase, search, book, cancel |
| routes.py | API endpoints | 280+ | 11 Flask route handlers |
| app.py | Flask setup | 30 | create_app() |
| config.py | Configuration | 20 | API_KEY, MODEL, Backend URL |
| prompts.py | System prompts | 50 | SYSTEM_PROMPT |
| tools.py | Tool definitions | 350+ | 11 tools, ToolHandler class |
| agent.py | Agent logic | 200+ | MovieBookingAgent, chat(), tool use |
| simple_booking.py | Basic example | 40 | Example conversation |
| advanced_agent.py | Complex example | 80 | 5 scenarios |
| web_ui.py | Web interface | 200 | Flask web server, HTML UI |

---

## 🎯 Common Tasks & Where to Find Code

| Task | File | Section |
|------|------|---------|
| Add a new movie | backend/database.py | _init_movies() |
| Add a theatre | backend/database.py | _init_theatres() |
| Create new API | backend/routes.py | Add @api_bp.route() |
| Change Claude's tone | agent/prompts.py | SYSTEM_PROMPT |
| Add a new tool | agent/tools.py | Add to TOOLS list |
| Connect real database | backend/database.py | Replace MockDatabase |
| Run all tests | examples/ | Each .py file |
| Deploy the app | (Docker needed) | Dockerfile at root |

---

## 💡 Understanding Tool Use Flow

When user says "Book 2 tickets for action movie":

```
Step 1: Send to Claude
┌─────────────────────────────────────────┐
│ System Prompt: "You're a booking agent" │
│ Tools: [search_movies, book_tickets...] │
│ User Message: "Book 2 tickets..."       │
└─────────────────────────────────────────┘

Step 2: Claude Decides
Claude: "I need to search movies, get shows, then book"
Tool Calls: [search_movies(), get_shows_for_movie(), book_tickets()]

Step 3: Execute Tools (agent.py → tools.py)
search_movies("Action") 
  → HTTP GET /api/movies?genre=Action
  → backend/routes.py
  → backend/database.py
  → Returns: [Movie objects]

Step 4: Claude Sees Results
Claude: "Now I'll get shows for Movie ID 1"
Tool Calls: [get_shows_for_movie(1)]

Step 5: More Tool Calls
[... repeat for each tool ...]

Step 6: Final Response
Claude: "✅ Booked! Confirmation BK1000, Seats A1-A2, $36"

Return to User ✓
```

---

## 🔧 Troubleshooting: Which File to Check?

| Symptom | Check File | Fix |
|---------|-----------|-----|
| "Connection refused" | backend/app.py | Start backend server |
| "API key not found" | agent/config.py | Check .env file |
| "Tool not found" | agent/tools.py | Verify tool names match |
| Wrong movie data | backend/database.py | Modify _init_movies() |
| API returns error | backend/routes.py | Check API logic |
| Claude errors | agent/agent.py | Check tool calling |
| Web UI doesn't work | examples/web_ui.py | Check port 5001 |

---

## 📚 Learning Path

Beginner → Intermediate → Advanced

```
Beginner:
  1. Read: QUICK_START.md
  2. Run: examples/simple_booking.py
  3. Run: agent/agent.py (interactive)

Intermediate:
  1. Study: backend/database.py
  2. Study: agent/tools.py
  3. Run: examples/advanced_agent.py
  4. Modify: backend/database.py (add own movies)

Advanced:
  1. Study: agent/agent.py (tool use logic)
  2. Study: backend/routes.py (API design)
  3. Add: New tools to agent/tools.py
  4. Connect: Real database
  5. Deploy: To cloud
```

---

Good luck! Start with `QUICK_START.md` 🚀
