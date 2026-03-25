# 🎯 Bedrock + Recommendations Implementation Summary

## ✅ What's Been Added

Your movie ticket booking agent now has two major upgrades:

### 1️⃣ AWS Bedrock Support
- **Dual API Support**: Choose between direct Anthropic API or AWS Bedrock
- **Simple Configuration**: Just set `USE_BEDROCK=True` in `.env`
- **Enterprise Ready**: Works with your AWS infrastructure and billing

### 2️⃣ Smart Recommendations Engine
Claude can now proactively recommend movies in 6 different ways:

| Type | Description | Claude Tool |
|------|-------------|-------------|
| **Personalized** | Based on user's booking history | `get_personalized_recommendations()` |
| **Popular** | Highest-rated movies | `get_popular_movies_recommendation()` |
| **Genre-Based** | Top movies in a category | `get_genre_recommendations()` |
| **Similar** | Movies like one they like | `get_similar_movies_recommendation()` |
| **Budget-Friendly** | Best shows within price range | `get_budget_friendly_recommendations()` |
| **Best Showtimes** | Analysis of times and pricing | `get_best_showtimes()` |

---

## 📁 Files Created / Modified

### New Files Created:
```
backend/recommendations.py        (300+ lines)
BEDROCK_RECOMMENDATIONS.md        (~400 lines)
```

### Files Modified:
```
.env.example                       (Updated with Bedrock options)
agent/config.py                    (Added Bedrock configuration)
agent/agent.py                     (Complete rewrite with Bedrock support)
agent/tools.py                     (Added 6 recommendation tools)
agent/prompts.py                   (Updated with recommendations guidance)
backend/routes.py                  (Added 6 recommendation endpoints)
backend/database.py                (Added TRACK_USER_PREFERENCES flag)
requirements.txt                   (Added boto3)
QUICK_START.md                     (Updated with Bedrock info)
```

---

## 🔑 Key Components

### Backend Recommendation Engine
`backend/recommendations.py` contains:

```python
class RecommendationEngine:
    - get_personalized_recommendations()
    - get_popular_movies()
    - get_genre_recommendations()
    - get_similar_movies()
    - get_budget_friendly_recommendations()
    - get_best_show_times()
    - track_booking()  # Learns user preferences
```

### API Endpoints
New endpoints added to `backend/routes.py`:

```
GET  /api/recommendations/personalized/<user_id>
GET  /api/recommendations/popular
GET  /api/recommendations/by-genre
GET  /api/recommendations/similar/<movie_id>
GET  /api/recommendations/budget-friendly
GET  /api/recommendations/best-showtimes/<movie_id>
```

### Claude Tools (Functions)
6 new tools defined in `agent/tools.py`:

```python
1. get_personalized_recommendations(user_id, limit=5)
2. get_popular_movies_recommendation(limit=5)
3. get_genre_recommendations(genre, limit=5)
4. get_similar_movies_recommendation(movie_id, limit=5)
5. get_budget_friendly_recommendations(max_price, limit=5)
6. get_best_showtimes(movie_id)
```

### Updated Agent
`agent/agent.py` now:

```python
- Detects API provider at startup
- Initializes Bedrock OR Anthropic based on config
- Handles both API response formats
- Transparently routes tool calls to either service
- Shows which API is being used in debug mode
```

---

## 🚀 Quick Setup (Choose One)

### Option A: AWS Bedrock

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env:
# USE_BEDROCK=True
# AWS_REGION=us-east-1
# BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# 3. Run
python -m backend.app         # Terminal 1
python agent/agent.agent      # Terminal 2
```

### Option B: Direct Anthropic API (Keep Existing)

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env:
# ANTHROPIC_API_KEY=sk-ant-...
# USE_BEDROCK=False

# 3. Run
python -m backend.app         # Terminal 1
python agent/agent.agent      # Terminal 2
```

---

## 💬 Example: How Recommendations Work

### User Conversation
```
User: What movies do you recommend?

🤖 Claude: Let me get some great recommendations for you!
[Calls: get_popular_movies_recommendation()]

Claude: Here are the highest-rated movies:
1. Oppenheimer (4.6/5) - Epic drama
2. Mission Impossible (4.5/5) - Action-packed
3. Inside Out 2 (4.5/5) - Heartwarming animation

What type appeals to you?

User: I like action movies

Claude: Great! Let me find top action films for you.
[Calls: get_genre_recommendations("Action")]

Claude: Here are the best action movies:
1. Mission Impossible: Dead Reckoning (4.5/5)
2. John Wick: Chapter 4 (4.4/5)

Want to see showtimes for either?

User: How much does Mission Impossible cost?

Claude: Let me check the best showtimes and pricing.
[Calls: get_best_showtimes(movie_id=1)]

Claude: Mission Impossible showtimes:
- 7:00 PM: $18 (120 seats available)
- 8:00 PM: $18 (95 seats available)
- 9:30 PM: $15 (50 seats available - best price!)

Book 2 tickets for 9:30 PM?

User: Yes

Claude: ✅ Booking confirmed!
[Calls: book_tickets()]
Confirmation: BK1025
Movie: Mission Impossible
Time: 9:30 PM
Seats: B5, B6
Total: $30
```

---

## 📊 Architecture Updates

### Before:
```
User → Claude → Tools → Backend API
```

### After:
```
User → Claude (Bedrock OR Anthropic) 
    ↓
    → Search Tools (movies, theatres, shows)
    → Booking Tools (book, cancel, manage)
    → Recommendation Tools (NEW!)
    ↓
    → Backend API
    ↓
    → Mock Database + Recommendation Engine
```

---

## 🔄 How Preferences Are Tracked

When `TRACK_USER_PREFERENCES=True`:

```python
# User makes a booking
booking = book_tickets(user_id="user_123", ...)

# System automatically learns:
recommendation_engine.track_booking(user_id, show_id)

# Tracks:
- Genres watched (e.g., "Action": 5 bookings)
- Average rating preference (e.g., avg 4.2)
- Total bookings (e.g., 10)
- Movie history (e.g., [1, 5, 7, 12])

# Later, personalized recommendations use this:
get_personalized_recommendations("user_123")
# → Recommends similar genre, similar or higher rating
```

---

## 🛠️ Configuration Options

### In `.env`:

```env
# API Choice
USE_BEDROCK=True/False

# Direct Anthropic (if not using Bedrock)
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# AWS Bedrock
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Features
ENABLE_RECOMMENDATIONS=True
TRACK_USER_PREFERENCES=True

# Backend
BACKEND_URL=http://localhost:5000
DEBUG=False
```

---

## 📖 Documentation Files

| File | Purpose |
|------|---------|
| `QUICK_START.md` | 5-min setup (updated) |
| `BEDROCK_RECOMMENDATIONS.md` | Complete Bedrock + recommendations guide |
| `IMPLEMENTATION_GUIDE.md` | Comprehensive architecture guide |
| `FILE_STRUCTURE.md` | File navigation |
| `.env.example` | Configuration template |

---

## 🎓 What to Try First

1. **Run the agent**: `python agent/agent.py`
2. **Ask for recommendations**: "What movies do you recommend?"
3. **Try budget search**: "What can I watch for under $15?"
4. **Get personalized suggestions**: "What action movies do you recommend?" (if first time, gets popular ones)
5. **Book a movie**: "Book 2 tickets for John Wick at 8 PM"

---

## ✨ Next Steps

### For Testing:
- [ ] Set up Bedrock credentials
- [ ] Run backend and agent
- [ ] Test all 6 recommendation types
- [ ] Try booking with recommendations

### For Production:
- [ ] Connect real database
- [ ] Add authentication
- [ ] Implement payment processing
- [ ] Deploy to AWS (Lambda + RDS)
- [ ] Set up monitoring

### For Enhancement:
- [ ] Add collaborative filtering
- [ ] Implement trend analysis
- [ ] Add user ratings
- [ ] Build feedback loop for better recommendations

---

## 🐛 Debugging Help

### Bedrock not working?

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check Bedrock access
aws bedrock list-foundation-models

# Check model availability in your region
aws bedrock describe-foundation-models
```

### Recommendations not showing?

```python
# Check if enabled in .env
ENABLE_RECOMMENDATIONS=True

# Check if Claude is using the tools
# Set DEBUG=True in .env to see tool calls
```

### Still having issues?

Check `BEDROCK_RECOMMENDATIONS.md` troubleshooting section!

---

## 📞 Support

All documentation is included:
- **QUICK_START.md** - For getting started
- **BEDROCK_RECOMMENDATIONS.md** - For Bedrock setup and recommendations
- **IMPLEMENTATION_GUIDE.md** - For understanding the architecture
- **FILE_STRUCTURE.md** - For code navigation

---

**You're all set! Start with `python agent/agent.py` 🚀**
