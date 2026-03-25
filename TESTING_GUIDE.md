# Testing Guide: Recommendations & Bedrock

Quick test scenarios to verify everything works correctly.

## Prerequisites

✅ Dependencies installed: `pip install -r requirements.txt`
✅ `.env` configured (Bedrock OR Anthropic)
✅ Backend running: `python -m backend.app`
✅ Agent running: `python agent/agent.py`

---

## Test 1: Recommendations Work

### Scenario: First-time user asks for recommendations

**Input:**
```
You: What movies do you recommend?
```

**Expected Output:**
Claude should call `get_popular_movies_recommendation()` and show:
- List of 5 highest-rated movies
- Each with title, rating, genre, duration, description
- Formatted nicely with ratings

**Example Response:**
```
🤖 Claude: I'd love to help you find a great movie! Here are my top picks:

📽️ TOP RECOMMENDATIONS
========================

1. Oppenheimer (4.6/5) ⭐ 3 hours | Drama
   "The story of American scientist J. Robert Oppenheimer"

2. Mission Impossible: Dead Reckoning (4.5/5) ⭐ 2h 43m | Action
   ...

3. Inside Out 2 (4.5/5) ⭐ 1h 36m | Animation
   ...

Would any of these interest you?
```

---

## Test 2: Genre Recommendations

### Scenario: User specifies genre preference

**Input:**
```
You: Show me the best action movies
```

**Expected Output:**
Claude should call `get_genre_recommendations("Action")` and return:
- Only action movies
- Sorted by rating (highest first)
- Clear genre confirmation

**Example Response:**
```
🤖 Claude: Great! Here are the top-rated action movies available:

🎬 ACTION MOVIES
========================

1. Mission Impossible: Dead Reckoning (4.5/5)
   -Ethan Hunt faces his most dangerous mission yet

2. John Wick: Chapter 4 (4.4/5)
   - John takes on his most formidable enemies

Would you like to book one of these?
```

---

## Test 3: Similar Movies Recommendation

### Scenario: User likes a specific movie

**Input:**
```
You: I love John Wick. What similar movies do you have?
```

**Expected Output:**
Claude should:
1. Recognize "John Wick" = movie_id 2
2. Call `get_similar_movies_recommendation(2)`
3. Show similar action movies

**Example Response:**
```
🤖 Claude: Since you love John Wick, you'll probably enjoy these similar films:

🎬 SIMILAR TO JOHN WICK
========================

1. Mission Impossible: Dead Reckoning (4.5/5)
   - Similar action-packed intensity
   - Excellent choreography

2. Fast X (4.2/5) [Coming Soon]
   - High-octane action
   - Great ensemble cast

Ready to book any of these?
```

---

## Test 4: Budget-Friendly Recommendations

### Scenario: User wants to stay within budget

**Input:**
```
You: What can I watch for under $15?
```

**Expected Output:**
Claude should:
1. Call `get_budget_friendly_recommendations(15)`
2. Show shows available for $15 or less
3. Include theatre names and times

**Example Response:**
```
🤖 Claude: Perfect! Here are great films you can see for under $15:

💰 BUDGET PICKS (Under $15)
========================

1. Mission Impossible @ Central Plex - $15/ticket
   Time: 8:00 PM | Seats: 120 available

2. Dune: Part Two @ Central Plex - $15/ticket
   Time: 7:00 PM | Seats: 95 available

3. Barbie @ Central Plex - $15/ticket
   Time: 9:30 PM | Seats: 110 available

Central Plex offers the best value! Want to book?
```

---

## Test 5: Best Showtimes Analysis

### Scenario: User wants to know best times for a movie

**Input:**
```
You: What are the best showtimes for Oppenheimer?
```

**Expected Output:**
Claude should:
1. Call `get_best_showtimes(movie_id=4)`
2. Analyze all showtimes
3. Show pricing, availability, recommendation

**Example Response:**
```
🤖 Claude: Let me analyze the showtimes for Oppenheimer:

⏰ SHOWTIME ANALYSIS - OPPENHEIMER
========================

7:00 PM (Downtown Cinema)
├─ Price: $18/ticket
├─ Seats Available: 120
├─ Recommendation: ✅ BEST VALUE & AVAILABILITY
└─ Best for: Maximum comfort

8:00 PM (Metro Theatre)  
├─ Price: $20/ticket (Premium)
├─ Seats Available: 85
├─ Recommendation: Premium experience
└─ Best for: Ultimate comfort with luxury seating

10:00 PM (Central Plex)
├─ Price: $15/ticket
├─ Seats Available: 110
├─ Recommendation: ✅ BEST PRICE
└─ Best for: Budget-conscious viewers

My pick: 7:00 PM at Downtown Cinema - great balance of price & availability!

Ready to book?
```

---

## Test 6: Complete Booking with Recommendations

### Scenario: Full conversation flow with recommendation

**Input Sequence:**
```
1. You: Help me find a good movie
2. You: I like sci-fi
3. You: Book me 2 tickets for Dune
4. You: Tomorrow evening
```

**Expected Flow:**
```
Turn 1:
→ Claude: I'll show you our best movies
→ Calls: get_popular_movies_recommendation()

Turn 2:
→ Claude: Here are top-rated sci-fi films
→ Calls: get_genre_recommendations("Sci-Fi")

Turn 3:
→ Claude: Great choice! Let me find showtimes for Dune
→ Calls: search_shows(movie_id=7) OR get_shows_for_movie(7)
→ Shows available times and prices

Turn 4:
→ Claude: Booking 2 tickets for tomorrow evening
→ Calls: book_tickets(user_id, show_id, 2, seats=["B5", "B6"])

Final:
→ Claude: ✅ Booking confirmed!
→ Shows: Confirmation, movie, time, seats, price
```

---

## Test 7: Bedrock vs Anthropic API

### Check Which API is Active

**If using Bedrock, you should see on startup:**
```
✅ Initialized Bedrock client with model: anthropic.claude-3-5-sonnet-20241022-v2:0
🎬 Movie Ticket Booking Agent
API Provider: AWS Bedrock
```

**If using Anthropic, you should see:**
```
✅ Initialized Anthropic client with model: claude-3-5-sonnet-20241022
🎬 Movie Ticket Booking Agent
API Provider: Anthropic
```

### Verify in .env Which is Active

```bash
# Check your .env
grep USE_BEDROCK .env
# Should show: USE_BEDROCK=True  (for Bedrock)
#           or USE_BEDROCK=False (for Anthropic)
```

---

## Test 8: Tool Usage Logging

**If you want to see which tools Claude is using:**

Set `DEBUG=True` in `.env`:

```env
DEBUG=True
```

Then you'll see:

```
📝 User: What movies do you recommend?

🔧 Calling tool: get_popular_movies_recommendation
   Input: {"limit": 5}
   Result: {"success": true, "count": 5, "popular_movies": [...]}

🤖 Claude: [Generates friendly response]
```

---

## Test 9: Multiple Recommendations in One Chat

### Scenario: Claude uses recommendations strategically

**Input:**
```
You: I'm not sure what to watch. I have $16 to spend. 
     I love action. What do you recommend?
```

**Expected Claude Behavior:**
1. Recognizes: User is indecisive + budget constraint + genre preference
2. Calls MULTIPLE recommendation tools:
   - `get_budget_friendly_recommendations(16)` → Available shows under $16
   - `get_genre_recommendations("Action", limit=5)` → Top action films
3. Cross-references to find: Action movies available for under $16
4. Makes strategic recommendation showing best options

---

## Common Issues & Solutions

### Issue: "Tool not found" error

**Fix:**
```python
# Make sure tool is in TOOLS list (agent/tools.py)
# and process_tool_call handles it (agent/tools.py)
```

### Issue: Recommendations return empty

**Fix:**
```python
# Check 1: Mock data has movies
# backend/database.py has movies loaded

# Check 2: Shows database has shows for tomorrow
# backend/database.py creates shows for tomorrow

# Check 3: Feature enabled
# ENABLE_RECOMMENDATIONS=True in .env
```

### Issue: Bedrock key error

**Fix:**
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Verify model access
aws bedrock list-foundation-models --region us-east-1

# Check .env has all required fields
grep -E "AWS_|BEDROCK" .env
```

---

## Performance Test

Try this to test system performance:

**Input:**
```
You: Book me 3 tickets. I want action, under $18, show me recommendations first
```

**Expected:**
- Response within 2-3 seconds
- Shows multiple recommendations
- Books tickets successfully

---

## Recommendation Quality Test

### Test Personalization Learning

**Session 1:**
```
User: Book 2 tickets for Mission Impossible (action movie)
→ System learns: User likes action, $18 price point
```

**Session 2 (same user_id):**
```
User: What do you recommend?
→ Claude: Get personalized recommendations should show action movies
→ Calls: get_personalized_recommendations(user_id)
```

---

## Success Criteria Checklist

✅ All 6 recommendation tools work
✅ Claude calls recommendations proactively when relevant
✅ Budget filtering works correctly
✅ Genre recommendations return correct movies
✅ Similar movies are actually similar
✅ Booking still works with recommendations
✅ Both Bedrock AND Anthropic API work
✅ Debug mode shows tool calls
✅ No errors in logs
✅ Responses are within 2-3 seconds

---

## Running Full Test Suite

```bash
# Terminal 1
python -m backend.app

# Terminal 2
python agent/agent.py

# Terminal 3 (run tests one by one from this guide)
# Try each test scenario above
```

---

## Debugging Commands

```bash
# Check if backend is running
curl http://localhost:5000/api/health

# Check available movies
curl http://localhost:5000/api/movies

# Check recommendations endpoint
curl http://localhost:5000/api/recommendations/popular

# Check your model
grep BEDROCK .env OR grep ANTHROPIC .env
```

---

Good luck with testing! All features should work seamlessly. 🚀
