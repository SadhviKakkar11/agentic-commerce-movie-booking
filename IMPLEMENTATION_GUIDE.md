# Step-by-Step Implementation Guide

## CineBot — Hindi Movie Booking Agent (Claude on AWS Bedrock)

This guide covers the complete implementation of CineBot, an agentic movie booking assistant for Ram Kumar.  
CineBot recommends Hindi movies (released ≥ 12-Mar-2026), books seats based on user preferences, and compares payment options (own CC points vs. best available card offer) — all powered by Claude 3.5 Sonnet via AWS Bedrock.

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites & Setup](#prerequisites--setup)
3. [Step 1: Set Up Backend API](#step-1-set-up-backend-api)
4. [Step 2: Mock Data — Movies, Theatres & User Profile](#step-2-mock-data--movies-theatres--user-profile)
5. [Step 3: Claude Agent & Strict Booking Flow](#step-3-claude-agent--strict-booking-flow)
6. [Step 4: Chat UI (CodeSandbox)](#step-4-chat-ui-codesandbox)
7. [Step 5: Test the Integration](#step-5-test-the-integration)
8. [Step 6: Deploy to CodeSandbox / GitHub Codespaces](#step-6-deploy-to-codesandbox--github-codespaces)

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│              CineBot Chat UI  (port 3000 / browser)          │
│      User types: "I want to book 2 tickets for Dhurandhar"   │
└─────────────────────────┬────────────────────────────────────┘
                          │  POST /chat
                          ▼
┌──────────────────────────────────────────────────────────────┐
│           codesandbox_app.py  (combined Flask server)        │
│  • Serves Chat UI at GET /                                   │
│  • Mounts backend Blueprint at /api/*                        │
│  • /chat  →  MovieBookingAgent.chat(message)                 │
└──────────┬───────────────────────────────────┬───────────────┘
           │                                   │
           ▼                                   ▼
┌─────────────────────┐             ┌──────────────────────────┐
│  MovieBookingAgent  │             │   Flask REST API (api_bp) │
│  (agent/agent.py)   │             │                           │
│                     │             │  GET  /api/movies         │
│  Sends messages to  │             │  GET  /api/shows          │
│  Claude via Bedrock │             │  POST /api/bookings       │
│  Tools loop until   │◄──calls────►│  POST /api/recommendations│
│  final response     │             │       /smart-search       │
└─────────┬───────────┘             │  GET  /api/bookings/<id>  │
          │                         │       /payment-recomm.    │
          │ InvokeModel             │  POST /api/payments       │
          ▼                         └──────────────┬────────────┘
┌─────────────────────┐                            │
│  AWS Bedrock        │                            ▼
│  Claude 3.5 Sonnet  │             ┌──────────────────────────┐
│  (tool use)         │             │  MockDatabase             │
└─────────────────────┘             │  • 10 Hindi movies        │
                                    │  • 5 Mumbai theatres      │
                                    │  • Show schedules          │
                                    │  • Booking records         │
                                    │  • User profile (Ram)      │
                                    │  • CC rewards & offers     │
                                    └──────────────────────────┘
```

### Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| LLM | Claude 3.5 Sonnet via AWS Bedrock | Enterprise-grade, no direct API key exposed |
| Booking flow | Strict 6-step (enforced in system prompt) | Prevents Claude skipping confirmation or payment steps |
| Payment | Own points vs. best card offer | Shows real monetary comparison, not just feature listing |
| Deployment | Single `codesandbox_app.py` on port 3000 | No separate backend process needed on CodeSandbox |
| UI buttons | Hint chips (fill input, no auto-send) | User stays in control; Claude doesn't fire on click |

---

## Prerequisites & Setup

### Requirements

- Python 3.11 or higher
- AWS account with Bedrock access (Claude 3.5 Sonnet enabled in `us-east-1`)
- AWS credentials: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`
- _(Optional)_ Anthropic API key for direct fallback mode

### Enable Claude on AWS Bedrock

1. Sign in to the [AWS Console](https://console.aws.amazon.com/bedrock)
2. Go to **Bedrock → Model access** in `us-east-1`
3. Request access to **Claude 3.5 Sonnet** (`anthropic.claude-3-5-sonnet-20241022-v2:0`)
4. Wait for access approval (usually instant for most accounts)

### Installation Steps

```bash
# 1. Clone the repo or open in CodeSandbox / GitHub Codespaces

# 2. Install dependencies (Python 3.11+)
pip install -r requirements.txt

# 3. Set environment variables
#    On CodeSandbox: use the Secrets panel
#    Locally: create a .env file

AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1

# 4. (Optional) Fall back to direct Anthropic API
USE_BEDROCK=false
ANTHROPIC_API_KEY=sk-ant-...
```

### Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `AWS_ACCESS_KEY_ID` | Yes (Bedrock) | — | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | Yes (Bedrock) | — | AWS credentials |
| `AWS_DEFAULT_REGION` | No | `us-east-1` | Bedrock region |
| `USE_BEDROCK` | No | `true` | Set `false` to use Anthropic directly |
| `ANTHROPIC_API_KEY` | Only if `USE_BEDROCK=false` | — | Direct Anthropic key |
| `BEDROCK_MODEL_ID` | No | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Bedrock model ID |

---

## Step 1: Set Up Backend API

### What We're Building

A REST API that provides:
- Hindi movie search with language + release-date filtering
- Mumbai theatre information
- Show schedules with seat availability
- Booking creation and management
- Payment recommendation (own CC points vs. best available card offer)
- Smart preference-based show search (used by Claude's `smart_search_shows` tool)

### Files Involved

```
backend/
  ├── models.py          - Data models (Movie, Theatre, Show, Booking)
  ├── database.py        - In-memory database: 10 Hindi movies, 5 theatres, Ram's profile
  ├── recommendations.py - Scoring engine; enforces Hindi + ≥2026-03-12 constraints
  ├── user_profiles.py   - UserProfileManager: preferences, CC points, booking history
  ├── booking_portals.py - CreditCardRewardsDB, PaymentGateway, BookingPortalManager
  ├── decision_modeling.py - Weighted scoring for smart recommendations
  ├── routes.py          - All API endpoints (Blueprint: api_bp)
  └── app.py             - Standalone Flask app (not used on CodeSandbox)
```

### How to Run (combined server — recommended)

```bash
# From the project root:
python codesandbox_app.py
# Chat UI + API both served at http://localhost:3000
```

### How to Run (backend only)

```bash
python -m backend.app
# API only at http://localhost:5000
```

### Test the API

```bash
# Health check
curl http://localhost:3000/api/health

# List Hindi movies (default filter: language=Hindi, released_on_or_after=2026-03-12)
curl http://localhost:3000/api/movies

# Filter by genre
curl "http://localhost:3000/api/movies?genre=Action"

# Get shows for a specific date
curl "http://localhost:3000/api/shows?date=2026-03-29"

# Get payment recommendation for a booking
curl http://localhost:3000/api/bookings/BK1001/payment-recommendation
```

### Data Models

**Movie** (`backend/models.py`)
```python
{
    "id": 1,
    "title": "Dhurandhar",
    "genre": "Action",
    "language": "Hindi",          # always "Hindi"
    "rating": 4.5,
    "duration": 148,              # minutes
    "description": "...",
    "release_date": "2026-03-14"  # must be >= 2026-03-12
}
```

**Show**
```python
{
    "id": 101,
    "movie_id": 1,
    "theatre_id": 1,
    "show_time": "2:00 PM",
    "date": "2026-03-29",
    "price": 700,                 # Rs. per seat
    "available_seats": 40,
    "seat_type": "Recliner"
}
```

**Booking**
```python
{
    "id": "BK1000",
    "user_id": "user_ram_001",
    "show_id": 101,
    "num_seats": 2,
    "seats": ["D5", "D6"],
    "total_price": 1400,          # Rs.
    "status": "confirmed",
    "payment_status": "pending"   # updated after make_payment
}
```

---

## Step 2: Mock Data — Movies, Theatres & User Profile

### Hindi Movies Catalog (`backend/database.py`)

All 10 movies are Hindi-language releases from March 2026:

| # | Title | Genre | Rating | Release |
|---|---|---|---|---|
| 1 | Dhurandhar | Action | 4.5 | 14-Mar-2026 |
| 2 | Khooni Raasta | Thriller | 4.3 | 12-Mar-2026 |
| 3 | Dil Dosti Drama | Comedy | 4.1 | 13-Mar-2026 |
| 4 | Aakhri Faisla | Drama | 4.6 | 16-Mar-2026 |
| 5 | Mumbai Files | Crime | 4.2 | 15-Mar-2026 |
| 6 | Shakti Sena | Action | 3.9 | 12-Mar-2026 |
| 7 | Registan 2 | Adventure | 4.0 | 18-Mar-2026 |
| 8 | Hasna Mana Hai | Comedy | 4.4 | 17-Mar-2026 |
| 9 | Tez Raftaar | Action | 4.2 | 20-Mar-2026 |
| 10 | Kaali Raat | Horror | 3.8 | 22-Mar-2026 |

### Mumbai Theatres

| # | Name | Area | Seat Types |
|---|---|---|---|
| 1 | Downtown Cinema (PVR) | Andheri West | Standard, Recliner |
| 2 | Metro Theatre (PVR) | Bandra West | Standard, Recliner, IMAX |
| 3 | Central Plex (INOX) | Sion | Standard, Gold Class |
| 4 | Sunset Theatre (PVR) | Andheri East | Standard, Recliner |
| 5 | Hollywood Premium (INOX) | Bandra East | Standard, Gold Class |

### Sample User — Ram Kumar (`user_ram_001`)

```python
# Preferences seeded in backend/database.py and user_profiles.py
{
    "user_id":   "user_ram_001",
    "name":      "Ram Kumar",
    "city":      "Mumbai",
    "preferred_theatres":  ["PVR"],
    "preferred_seat_type": "Recliner",
    "preferred_timings":   ["1:00 PM", "2:00 PM", "3:00 PM"],
    "preferred_locations": ["Andheri", "Bandra", "Sion"],
    "preferred_offers":    ["BOGO"],
    "preferred_genres":    ["Action", "Comedy"],
    "avg_budget":          1500,          # Rs. per outing

    # Credit card
    "cc_provider":  "ICICI Bank",
    "cc_points":    1000,                 # 1 pt = Rs. 0.50 → Rs. 500 total
}
```

### Payment Options (`backend/booking_portals.py`)

```python
# CreditCardRewardsDB — module-level singletons
cc_rewards_db      # tracks user CC points; redemption_rate = Rs. 0.50 / point
payment_gateway    # processes payments, updates booking status
booking_portal_manager  # orchestrates the full booking + payment flow

# Available card offers compared during payment recommendation:
ICICI Sapphiro  — 15% off, max discount Rs. 350
HDFC Regalia    — 12% off, max discount Rs. 300
SBI Elite       — 10% off, max discount Rs. 250
Axis Ace        —  8% off, max discount Rs. 200
```

### How Eligibility Filtering Works (`backend/recommendations.py`)

```python
def _is_eligible_movie(self, movie) -> bool:
    """Only Hindi movies released on/after 2026-03-12 pass through."""
    cutoff = date(2026, 3, 12)
    return (
        getattr(movie, 'language', 'Hindi').lower() == 'hindi'
        and movie.release_date >= cutoff
    )
```

This filter is applied inside every recommendation method — `get_popular_movies`, `get_genre_recommendations`, `get_personalized_recommendations`, and `get_best_deal_shows`.

---

## Step 3: Claude Agent & Strict Booking Flow

### Key Files

```
agent/
  ├── config.py       - USE_BEDROCK flag, BEDROCK_MODEL_ID, BACKEND_URL
  ├── tools.py        - Tool definitions (TOOLS list) + ToolHandler + process_tool_call dispatcher
  ├── prompts.py      - SYSTEM_PROMPT: enforces 6-step booking flow
  └── agent.py        - MovieBookingAgent: chat(), _get_claude_response(), tool-use loop
```

### Available Tools (19+)

| Tool | Purpose |
|---|---|
| `search_movies` | Search Hindi movies (defaults: `language=Hindi`, `released_on_or_after=2026-03-12`) |
| `get_movie_details` | Full details for a movie ID |
| `get_theatres` | List theatres in a city |
| `search_shows` | Find shows with genre/date/price filters |
| `get_shows_for_movie` | All shows for a specific movie |
| `get_show_details` | Seat availability and pricing for a show |
| **`smart_search_shows`** | Decision-modeled search: picks best show matching user preferences (Step 1) |
| `book_tickets` | Create a reservation (Step 3) |
| `get_booking_details` | Retrieve a booking |
| `get_user_bookings` | All bookings for a user |
| `cancel_booking` | Cancel a booking |
| `get_user_preferences` | Fetch Ram's stored preferences |
| `get_recommendations` | Genre/popularity-based recommendations |
| `get_best_deals` | Budget-filtered show recommendations |
| `get_similar_movies` | Movies similar to a given title |
| **`get_payment_recommendation`** | Compare own CC points vs. best card offer (Step 4) |
| **`make_payment`** | Execute payment with chosen option (Step 5) |
| `get_payment_options` | Raw list of all available payment methods |
| `redeem_points` | Standalone CC point redemption |

### The 6-Step Booking Flow (`agent/prompts.py`)

The system prompt instructs Claude to follow this exact sequence every time a user wants to book:

```
STEP 1 — PREFERENCE ALIGNMENT
  Claude calls smart_search_shows → picks single best match for Ram
  (PVR, Recliner, 1-3 PM, Andheri/Bandra/Sion)
  Presents structured card, asks: "Shall I reserve these seats?"

STEP 2 — AUTHORIZATION  ← hard gate, no booking without this
  Waits for explicit: yes / confirm / okay / go ahead

STEP 3 — RESERVATION
  Calls book_tickets(user_id="user_ram_001", show_id, num_seats, seats)
  Reports: "✅ Seats reserved! Booking ID: BKxxxx."

STEP 4 — PAYMENT RECOMMENDATION  ← triggered automatically after booking
  Calls get_payment_recommendation(booking_id)
  Presents BOTH options side-by-side:
    💳 Option 1 — ICICI Bank Points: 1000 pts → Rs. 500 off → You pay Rs. 900
    🏦 Option 2 — ICICI Sapphiro:   15% off   → Rs. 210 off → You pay Rs. 1190
    ⭐ Recommended: Option 1 — saves Rs. 290 more
  Asks: "Which option would you like?"

STEP 5 — PAYMENT EXECUTION
  Waits for "Option 1" or "Option 2"
  Calls make_payment(payment_option="redeem_own_points" | "best_available_card")

STEP 6 — BOOKING CONFIRMATION
  Final summary: movie, show, seats, payment method, amount paid, booking ID, txn ID
```

### How the Bedrock Tool-Use Loop Works

```python
# agent/agent.py  (simplified)
def _get_claude_response(self, messages):
    while True:
        response = bedrock_client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body={"messages": messages, "tools": TOOLS, ...}
        )
        if response["stop_reason"] == "tool_use":
            # Claude wants to call a tool
            tool_results = []
            for tool_call in response["content"]:
                result = process_tool_call(tool_call["name"], tool_call["input"])
                tool_results.append(result)
            messages.append({"role": "assistant", "content": response["content"]})
            messages.append({"role": "user",      "content": tool_results})
            # loop continues → Claude gets tool results, decides next action
        else:
            # stop_reason == "end_turn" → final text response
            return extract_text(response)
```

---

## Step 5: Test the Integration

### Test 1: Start the Combined Server

```bash
python codesandbox_app.py
# Open http://localhost:3000 in your browser
```

### Test 2: Full Chat Booking Flow

In the chat UI at `http://localhost:3000`:

1. **Type** (or click the hint chip): `I want to book 2 tickets for Dhurandhar this Sunday afternoon`
2. CineBot calls `smart_search_shows` and replies with a single recommendation card
3. **Confirm**: `Yes, go ahead` or `Confirm`
4. CineBot books the seats and immediately presents payment options
5. **Choose**: `Option 1` or `Option 2`
6. CineBot processes payment and shows the final confirmation

### Test 3: API Health Check

```bash
curl http://localhost:3000/api/health
# {"status": "ok", "service": "Movie Booking API"}

curl http://localhost:3000/api/movies
# Returns all 10 Hindi movies

curl "http://localhost:3000/api/movies?genre=Action"
# Filters to Action movies only
```

### Test 4: Payment Recommendation Endpoint

```bash
# First create a booking via POST /api/bookings
curl -X POST http://localhost:3000/api/bookings \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user_ram_001","show_id":101,"num_seats":2,"seats":["D5","D6"]}'

# Then get payment recommendation
curl http://localhost:3000/api/bookings/BK1001/payment-recommendation
# Returns: own_points option, best_card option, and recommended_option with reasoning
```

### Test 5: CLI Agent (no browser)

```bash
python agent/agent.py
# Interactive REPL — type messages, see Claude's responses
```

---

## Step 6: Deploy to CodeSandbox / GitHub Codespaces

### CodeSandbox (auto-configured)

The repo includes `.codesandbox/tasks.json`:
```json
{
  "tasks": {
    "install": { "command": "pip install -r requirements.txt" },
    "start":   { "command": "python codesandbox_app.py", "preview": { "port": 3000 } }
  }
}
```
Just open the repo in CodeSandbox — it installs deps and starts the server automatically.  
**Add your AWS secrets** in the CodeSandbox "Secrets" panel (ENV tab):
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION` (default: `us-east-1`)

### GitHub Codespaces (auto-configured)

The repo includes `.devcontainer/devcontainer.json` with Python 3.11 and port 3000 forwarded:
```json
{
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  "postCreateCommand": "pip install -r requirements.txt",
  "forwardPorts": [3000]
}
```
Add secrets in **GitHub → Settings → Codespaces → Secrets**.

### Push to GitHub Without Git Binary (`push_to_github.ps1`)

If you don't have `git` installed, run the PowerShell script — it uses the GitHub REST API directly:
```powershell
.\push_to_github.ps1
# Prompts for: GitHub username, personal access token (PAT), repo name
# Creates a new private repo and uploads all project files
```

---

## 📚 Example Conversations

### Example 1: End-to-End Booking with Payment Comparison

```
Ram: I want to book 2 tickets for Dhurandhar this Sunday afternoon

CineBot: [calls smart_search_shows(user_id="user_ram_001", movie="Dhurandhar", date="2026-03-29")]

        🎬 Dhurandhar
        📅 Date & Time  : Sunday, 29-Mar-2026, 2:00 PM
        🏛️ Theatre      : PVR Downtown Cinema, Andheri West
        💺 Seats        : Recliner — D5, D6
        💰 Base Price   : Rs. 1400 for 2 tickets
        🎟️ Offer        : Weekend Recliner Special

        Shall I go ahead and reserve these seats for you?

Ram: Yes, confirm

CineBot: [calls book_tickets(user_id="user_ram_001", show_id=101, num_seats=2, seats=["D5","D6"])]

        ✅ Seats reserved! Booking ID: BK1042. Now let me find the best payment option for you.

        [calls get_payment_recommendation(booking_id="BK1042")]

        💳 Option 1 — Your ICICI Bank Points
        • Points available : 1000 pts
        • Discount        : Rs. 500
        • You pay         : Rs. 900

        🏦 Option 2 — ICICI Sapphiro (New/Other Card)
        • Discount        : 15% off → Rs. 210 saved
        • You pay         : Rs. 1190
        • Note: This card may require a new application if you don't have it.

        ⭐ Recommended: Option 1 — saves you Rs. 290 more.

        Which option would you like to use for payment?

Ram: Option 1

CineBot: [calls make_payment(booking_id="BK1042", payment_option="redeem_own_points")]

        ✅ Booking Confirmed!
        🎬 Movie          : Dhurandhar
        📅 Show           : Sunday, 29-Mar-2026, 2:00 PM
        🏛️ Theatre        : PVR Downtown Cinema, Andheri West
        💺 Seats          : D5, D6
        💳 Payment        : ICICI Bank Reward Points (1000 pts redeemed)
        💰 Amount Paid    : Rs. 900
        🎟️ Booking ID     : BK1042
        🧾 Transaction ID : TXN8821

        Enjoy the movie, Ram! 🍿
```

### Example 2: What's Playing (discovery, no booking)

```
Ram: Show me all Hindi movies available this week

CineBot: [calls search_movies(language="Hindi", released_on_or_after="2026-03-12")]

        Here are the Hindi movies showing this week:

        1. 🎬 Aakhri Faisla — Drama, ⭐ 4.6  (Best rated!)
        2. 🎬 Dhurandhar    — Action, ⭐ 4.5
        3. 🎬 Hasna Mana Hai — Comedy, ⭐ 4.4
        4. 🎬 Khooni Raasta  — Thriller, ⭐ 4.3
        ...and 6 more.

        Would you like to book tickets for any of these, or want me to
        find shows that match your preferred timing and theatre?
```

### Example 3: View Booking History

```
Ram: Show my past bookings

CineBot: [calls get_user_bookings(user_id="user_ram_001")]

        📋 Your Bookings:

        BK1042 — Dhurandhar | PVR Andheri | 29-Mar-2026, 2 PM | Seats D5, D6 | Rs. 900 ✅ Confirmed

        Would you like to cancel or get details for any booking?
```

---

## 🔧 API Reference

### Movies Endpoint

```
GET /api/movies
Query Parameters:
  - genre              (optional) e.g. "Action"
  - min_rating         (optional) e.g. 4.0
  - language           (optional, default "Hindi")
  - released_on_or_after (optional, default "2026-03-12")

Response:
{
    "success": true,
    "count": 10,
    "movies": [
        { "id": 1, "title": "Dhurandhar", "language": "Hindi",
          "genre": "Action", "rating": 4.5, "release_date": "2026-03-14" }
    ]
}
```

### Smart Search Endpoint

```
POST /api/recommendations/smart-search
Request Body:
{
    "user_id": "user_ram_001",
    "movie_title": "Dhurandhar",
    "date": "2026-03-29",
    "num_seats": 2
}

Response:
{
    "success": true,
    "best_option": {
        "show_id": 101, "movie": "Dhurandhar",
        "theatre": "PVR Downtown Cinema", "location": "Andheri West",
        "show_time": "2:00 PM", "date": "2026-03-29",
        "seat_type": "Recliner", "available_seats": ["D5","D6","D7","D8"],
        "price_per_seat": 700, "total_price": 1400, "score": 92.5
    }
}
```

### Bookings Endpoint

```
POST /api/bookings
Request Body:
{
    "user_id": "user_ram_001",
    "show_id": 101,
    "num_seats": 2,
    "seats": ["D5", "D6"]
}

Response:
{
    "success": true,
    "booking": {
        "id": "BK1042", "user_id": "user_ram_001",
        "show_id": 101, "num_seats": 2, "seats": ["D5", "D6"],
        "total_price": 1400, "status": "confirmed", "payment_status": "pending"
    }
}
```

### Payment Recommendation Endpoint

```
GET /api/bookings/<booking_id>/payment-recommendation

Response:
{
    "success": true,
    "booking_id": "BK1042",
    "total_price": 1400,
    "recommendation": {
        "own_points":         { "points_available": 1000, "discount_amount": 500, "amount_payable": 900 },
        "best_available_card":{ "card_name": "ICICI Sapphiro", "discount_percent": 15,
                                "discount_amount": 210, "amount_payable": 1190 },
        "recommended_option": "own_points",
        "why": "Redeeming your 1000 ICICI points saves Rs. 500, which is Rs. 290 more than the best card offer."
    }
}
```

### Payment Endpoint

```
POST /api/payments
Request Body:
{
    "booking_id": "BK1042",
    "user_id": "user_ram_001",
    "payment_option": "redeem_own_points"   // or "best_available_card"
}

Response:
{
    "success": true,
    "transaction_id": "TXN8821",
    "amount_charged": 900,
    "payment_method": "ICICI Bank Reward Points",
    "points_redeemed": 1000,
    "booking_status": "confirmed"
}
```

---

## ❓ Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'backend'` or `'agent'`

**Solution:** Always run from the project root using:
```bash
python codesandbox_app.py
```
The file sets `sys.path` and `os.chdir` automatically. Do NOT run `python backend/app.py` directly.

### Issue: `botocore.exceptions.NoCredentialsError`

**Solution:** AWS credentials are missing. Set them as environment variables or in `.env`:
```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
```
On CodeSandbox / Codespaces use the Secrets panel — never commit credentials.

### Issue: `ValidationException` or `AccessDeniedException` from Bedrock

**Solution:** 
1. Confirm you're in the correct region (`us-east-1` by default)
2. Enable model access: AWS Console → Bedrock → Model access → Request `Claude 3.5 Sonnet`
3. To test without Bedrock, set `USE_BEDROCK=false` and provide `ANTHROPIC_API_KEY`

### Issue: Claude skips confirmation and books immediately

**Solution:** The system prompt in `agent/prompts.py` has a "STEP 2 — AUTHORIZATION" hard gate. If Claude is bypassing it, ensure you're running the latest version of `prompts.py` and there are no conflicting instructions in the conversation history. Reset the session by restarting the server.

### Issue: Backend API not responding on `/api/`

**Solution:** Confirm the combined server is running on port 3000:
```bash
python codesandbox_app.py
curl http://localhost:3000/api/health
```

### Issue: Tool calls not routing correctly

**Solution:** Check `agent/tools.py` → `process_tool_call()`. Every tool in the `TOOLS` list must have a matching `elif tool_name == "..."` branch in the dispatcher.

---

## 📖 Further Learning

- [Claude Tool Use Documentation](https://docs.anthropic.com/en/docs/build-a-chatbot-with-tool-use)
- [AWS Bedrock Claude Setup](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

## Next Steps

1. ✅ Set up AWS Bedrock access (Claude 3.5 Sonnet, `us-east-1`)
2. ✅ Install dependencies: `pip install -r requirements.txt`
3. ✅ Set AWS credentials as environment variables / Secrets
4. ✅ Run: `python codesandbox_app.py` → open `http://localhost:3000`
5. ✅ Try: "I want to book 2 tickets for Dhurandhar this Sunday afternoon"
6. ✅ Push to GitHub with `push_to_github.ps1` (no git binary needed)
7. ✅ Open in CodeSandbox or GitHub Codespaces — auto-configured via `.codesandbox/tasks.json` / `.devcontainer/devcontainer.json`

---

Happy booking, Ram! 🎬🍿
