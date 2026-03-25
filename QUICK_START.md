# Quick Start Guide

Get started with the Movie Ticket Booking Agent in 5 minutes!

## 🚀 Quick Start (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up API Key
```bash
# Copy the environment template
cp .env.example .env

# Edit .env and choose ONE of these options:

# Option A: Direct Anthropic API
# ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
# USE_BEDROCK=False

# Option B: AWS Bedrock (Recommended if you have AWS credentials)
# USE_BEDROCK=True
# AWS_REGION=us-east-1
# BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
# AWS_ACCESS_KEY_ID=your-key
# AWS_SECRET_ACCESS_KEY=your-secret
```

### 3. Start Backend API (Terminal 1)
```bash
python -m backend.app
```

Wait for: `Running on http://localhost:5000`

### 4. Run Agent (Terminal 2)
```bash
python agent/agent.py
```

It will show which API provider is being used (Bedrock or Anthropic).

### 5. Start Booking with Recommendations!
```
You: I want to watch a movie tomorrow. What do you recommend for action fans?

🤖 Claude: I'd be happy to help! Let me get some personalized recommendations for you.
[Gets popular action movies]

Claude: Here are my top action movie picks:
1. Mission Impossible - 4.5 rating
2. John Wick 4 - 4.4 rating
[...]

You: Book me 2 tickets for John Wick 4 at 8 PM

🤖 Claude: [Completes the booking]
```

## 📚 Example Commands

### Try These Commands in the Chat

```
# Get Recommendations
"What movies do you recommend?" (gets popular movies)
"Recommend something for an action fan" (genre-based)
"I loved John Wick, what else should I watch?" (similar movies)
"What's the best value within $15?" (budget-friendly)
"What are the best showtimes for Oppenheimer?" (time analysis)

# Search for movies
"Show me action movies with high ratings"
"Find comedies under $15"

# Search by location
"What theatres do you have in New York?"
"Find shows at Downtown Cinema"

# Book tickets
"Book 2 tickets for Oppenheimer tomorrow at 8 PM"
"I want to see Inside Out 2, book 3 seats please"

# Manage bookings
"Show me my bookings"
"Cancel my booking from yesterday"
```

## 🧪 Run Examples

### Simple Example (predefined conversation)
```bash
python examples/simple_booking.py
```

### Advanced Examples (complex scenarios)
```bash
python examples/advanced_agent.py
```

### Web UI (Optional - requires backend running)
```bash
python examples/web_ui.py
# Open: http://localhost:5001
```

## 📝 Key Files

| File | Purpose |
|------|---------|
| `backend/app.py` | Flask API server |
| `agent/agent.py` | Claude agent main logic |
| `agent/tools.py` | Tool definitions for Claude |
| `examples/simple_booking.py` | Basic example |
| `IMPLEMENTATION_GUIDE.md` | Comprehensive guide |

## 🎯 What Actually Happens

```
You send a message (e.g., "Book tickets for action movie")
         │
         ▼
Claude analyzes: "User wants to search for action movies and book"
    
Claude calls tools in sequence:
  1. search_movies(genre="action")
  2. get_shows_for_movie(movie_id=...)
  3. book_tickets(show_id=..., num_seats=...)
    
Claude gets results and generates a friendly response
         │
         ▼
You see: "✅ Booking confirmed! Here are your details..."
```

## 🛠️ Troubleshooting

**Error: "Connection refused"**
→ Make sure backend API is running on port 5000

**Error: "ANTHROPIC_API_KEY not found"**
→ Check your .env file has the API key

**Error: "No module named anthropic"**
→ Run: `pip install anthropic`

## 📊 Architecture at a Glance

```
┌──────────────────────┐
│   You (User)         │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────┐
│   Claude AI Agent                │
│   (Understands & Decides)        │
└────┬─────────────┬─────────┬─────┘
     │             │         │
     ▼             ▼         ▼
  Movies       Theatres   Bookings
   Tools        Tools      Tools
     │             │         │
     └─────────────┼─────────┘
                   │
                   ▼
        ┌────────────────────┐
        │  Backend REST API  │
        │  (Flask Server)    │
        └────────────────────┘
                   │
                   ▼
        ┌────────────────────┐
        │  Mock Database     │
        │  (In-Memory)       │
        └────────────────────┘
```

## 🎬 Sample Movie Database

The system comes with 10 pre-loaded movies:
- Mission Impossible: Dead Reckoning
- John Wick: Chapter 4
- Barbie
- Oppenheimer
- Killers of the Flower Moon
- The Marvels
- Dune: Part Two
- Inside Out 2
- Deadpool & Wolverine
- Nosferatu

And 5 theatres in New York and Los Angeles.

## 💡 Pro Tips

1. **Be conversational** - The agent understands natural language
   ```
   ✅ "I want an action movie tomorrow evening"
   ✅ "Book 2 tickets for John Wick please"
   ```

2. **Specify preferences** - Helps narrow down options
   ```
   ✅ "Comedy movie under $15 near downtown"
   ✅ "Premium theatre with reclining seats"
   ```

3. **Refine your search** - Follow-up naturally
   ```
   User: "Show me action movies"
   Claude: [Shows 3 options]
   User: "Which is the longest?"
   Claude: [Analyzes & responds]
   ```

## 🚀 Next Steps

1. ✅ Get it running locally
2. ⬜ Customize mock data in `backend/database.py`
3. ⬜ Connect to a real database
4. ⬜ Add payment integration
5. ⬜ Deploy to cloud

## 📞 API Endpoints Available

```
GET  /api/movies
GET  /api/movies/<id>
GET  /api/theatres
GET  /api/theatres/<id>
GET  /api/shows
GET  /api/shows/<id>
POST /api/bookings
GET  /api/bookings/<id>
POST /api/bookings/<id>/cancel
```

---

**Ready?** Run `python agent/agent.py` and start booking! 🎬🎫
