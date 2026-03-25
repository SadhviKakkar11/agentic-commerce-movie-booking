# AWS Bedrock & Recommendations Setup Guide

## Using Claude via AWS Bedrock

This guide explains how to use the movie booking agent with AWS Bedrock instead of the direct Anthropic API.

### Why use Bedrock?

- **Enterprise Integration** - Integrates with your AWS infrastructure
- **Cost Management** - Lever your AWS accounts and billing
- **VPC Support** - Can run in your private VPC
- **Compliance** - Easier compliance with enterprise policies
- **Multi-model Support** - Access to various Claude models

### Prerequisites

1. **AWS Account** with access to Bedrock
2. **AWS CLI** configured with credentials
3. **Bedrock Model Access** - Request access to Claude models in your region

### Step 1: Get AWS Credentials

```bash
# Option 1: Using AWS CLI (recommended)
aws configure

# Option 2: Manual environment setup
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-east-1
```

### Step 2: Enable Bedrock Model Access

1. Go to AWS Console → Bedrock
2. Click "Model access" in the sidebar
3. Search for "Claude"
4. Click "Request access" for desired Claude models
5. Wait for approval (usually instant)

### Step 3: Update Configuration

**Option A: Via .env file**

```bash
cp .env.example .env
```

Then edit `.env`:

```env
# Use Bedrock
USE_BEDROCK=True

# AWS Configuration
AWS_REGION=us-east-1  # or your region
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# Optional: Override credentials (if not using AWS CLI)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Enable recommendations
ENABLE_RECOMMENDATIONS=True
TRACK_USER_PREFERENCES=True
```

**Option B: Via environment variables**

```bash
export USE_BEDROCK=True
export AWS_REGION=us-east-1
export BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

### Step 4: Run the Agent

```bash
# Start backend
python -m backend.app

# In another terminal, start agent
python agent/agent.py
```

You should see:
```
✅ Initialized Bedrock client with model: anthropic.claude-3-5-sonnet-20241022-v2:0
🎬 Movie Ticket Booking Agent
API Provider: AWS Bedrock
```

### Available Bedrock Models

```
# Latest models available (as of March 2026)
anthropic.claude-3-5-sonnet-20241022-v2:0
anthropic.claude-3-5-haiku-20241022-v1:0
anthropic.claude-3-opus-20250219-v1:0

# Pricing varies by region
# Check AWS Bedrock console for current costs
```

---

## Recommendations System

The movie booking agent now includes an advanced recommendations engine with 6 types of suggestions.

### Recommendation Features

#### 1. Personalized Recommendations
For returning users, based on their booking history:

```
User booking history: Action movies, $15-20 range
Claude: "Based on your history with action movies, I recommend:
- Mission Impossible (4.5/5)
- John Wick 4 (4.4/5)
- Fast X (coming soon)"
```

**Tool**: `get_personalized_recommendations(user_id)`

#### 2. Popular Movies
Highest-rated movies - perfect for indecisive users:

```
User: "What's good playing right now?"
Claude: "Let me get the highest-rated movies available:
1. Dhurandhar (4.9/5)
2. Oppenheimer (4.6/5)
3. Mission Impossible (4.5/5)
4. Inside Out 2 (4.5/5)"
```

**Tool**: `get_popular_movies_recommendation(limit=5)`

#### 3. Genre Recommendations
Top-rated movies in a specific genre:

```
User: "Show me great sci-fi movies"
Claude: "Here are top-rated sci-fi films:
1. Dune: Part Two (4.4/5)
2. The Marvels (3.8/5)"
```

**Tool**: `get_genre_recommendations(genre, limit=5)`

#### 4. Similar Movies
Find movies similar to one the user likes:

```
User: "I loved John Wick. What else should I watch?"
Claude: "Since you enjoyed John Wick, you might like:
- Mission Impossible (similar action, 4.5/5)
- Fast X (similar style, upcoming)"
```

**Tool**: `get_similar_movies_recommendation(movie_id, limit=5)`

#### 5. Budget-Friendly Deals
Best shows and times within a price range:

```
User: "I don't want to spend more than Rs300"
Claude: "Great! Here are the best deals within Rs300:
1. Central Plex - Most screens, avg Rs300
2. Downtown Cinema - Premium at Rs600 (slightly over)"
```

**Tool**: `get_budget_friendly_recommendations(max_price, limit=5)`

#### 6. Best Showtimes
Analyze availability and pricing for different times:

```
User: "What time should I book for Oppenheimer?"
Claude: "7:00 PM - Best value, 120 seats, Rs300
8:00 PM - Most popular, fewer seats, Rs300
10:00 PM - Latest option, 110 seats, Rs500"
```

**Tool**: `get_best_showtimes(movie_id)`

### How Claude Uses Recommendations

Claude automatically decides when to use recommendations:

1. **User asks for suggestions** → Uses `get_popular_movies_recommendation()`
2. **User mentions genre** → Uses `get_genre_recommendations(genre)`
3. **User mentions a movie** → Uses `get_similar_movies_recommendation()`
4. **User mentions budget** → Uses `get_budget_friendly_recommendations()`
5. **User is indecisive** → Suggests using these tools

### Tracking User Preferences

When `TRACK_USER_PREFERENCES=True`, the system learns:

```python
# Tracked after each booking:
- Genres watched
- Average rating preference
- Total bookings
- Movie history
```

This data is used for personalized recommendations.

### Example Conversations with Recommendations

#### Conversation 1: First-time User

```
User: I want to go to the movies tomorrow but I'm not sure what to watch

Claude: I'd love to help! Let me show you some great options.
[Calls get_popular_movies_recommendation()]

Claude: Here are our most highly-rated movies:
1. 🎬 Dhurandhar (4.9/5) - 3.5 hours - Thriller
2. 🎬 Oppenheimer (4.6/5) - 3 hours - Drama
3. 🎬 Mission Impossible: Dead Reckoning (4.5/5) - 2h 43m - Action
4. 🎬 Inside Out 2 (4.5/5) - 1h 36m - Animation

Which genre interests you most?

User: I like action movies

Claude: Perfect! Here are top action films:
[Calls get_genre_recommendations("Action")]

Claude: 1. Dhurandhar (4.9/5) - Rs900 - Many showtimes
       2. John Wick 4 (4.4/5) - Rs600 - Evening options
       3. Fast X - Coming soon

Ready to book?

User: Yes, book 2 tickets for Dhurandhar tomorrow at 8 PM

Claude: ✅ Booking confirmed!
[Calls book_tickets()]
```

#### Conversation 2: Returning User

```
User: Hello! I'm back for another movie

Claude: Welcome back! Since you've booked with us before, I have personalized recommendations for you.
[Calls get_personalized_recommendations("user_123")]

Claude: Based on your love of action movies, I recommend:
1. John Wick 4 (4.4/5) - Similar to movies you've watched
2. Killers of the Flower Moon (4.2/5) - Different genre, top-rated
3. Mission Impossible (4.5/5) - Your genre, must-watch

Is any of these interesting?

User: What about budget? I have only $20

Claude: Let me find the best value options...
[Calls get_budget_friendly_recommendations(20)]

Claude: Great! All these are within $20:
- Downtown Cinema: Rs900/ticket
- Central Plex: Rs600/ticket (best value!)
- Metro Theatre: Rs1000/ticket (premium experience)

Book at Central Plex to save?

User: Yes, book 2 at Central Plex

Claude: ✅ Booked! Confirmation: BK2047
Movie: John Wick 4 at Central Plex
Time: 8:00 PM
Seats: B5, B6
Total: $30
```

#### Conversation 3: Decision Help

```
User: I can't decide between two movies

Claude: No problem! What are your options?

User: John Wick 4 or Oppenheimer? Both are good ratings

Claude: Let me analyze both options for you:
[Gets showtimes and availability]

Claude: Here's a comparison:
📊 JOHN WICK 4 (Action, 4.4/5)
- Showtimes: 7PM ($18), 9PM ($18), 10:30PM ($15)
- Availability: 85 seats average
- Best for: Quick 2h 45m intense action

📊 OPPENHEIMER (Drama, 4.6/5)  
- Showtimes: 7PM ($18), 8PM ($18)
- Availability: 70 seats average
- Best for: Thoughtful 3-hour epic
- Pro Tip: Slightly higher rating, but longer

My recommendation: Based on your action movie history,
John Wick 4 might be more your speed. But if you want something
more critically acclaimed, Oppenheimer is incredible.

Which appeals to you?

User: Let's go with Oppenheimer

Claude: Great choice! Let me get the best showtime...
[Calls get_best_showtimes(4)]

Claude: The 7 PM showing has the best combination of price and availability.
Book 2 tickets for Oppenheimer at 7 PM?

User: Yes!

Claude: ✅ All set! [Booking details]
```

### Troubleshooting Recommendations

| Issue | Solution |
|-------|----------|
| No recommendations shown | Check `ENABLE_RECOMMENDATIONS=True` in .env |
| Same recommendations each time | This is expected - data is limited |
| Budget recommendations not working | Make sure shows exist within price range |
| Personalized recs not working | User needs booking history first |

### Performance Tips

- Recommendations are **instant** (using in-memory data)
- No external API calls except to backend
- Bedrock handles the intelligence, not the database

### Future Enhancements

1. Add collaborative filtering (what users like you watched)
2. Real-time trending analysis
3. Season analysis (best times to watch certain genres)
4. Social recommendations (friend group preferences)
5. Weather-based recommendations
6. Mood-based recommendations using sentiment analysis

---

## Integration with Production Systems

### Moving to Real Database

Replace `backend/database.py` MockDatabase with:

```python
class PostgresDatabase:
    def __init__(self, connection_string):
        self.engine = create_engine(connection_string)
    
    def get_all_movies(self):
        return db.session.query(Movie).all()
    
    # ... implement other methods
```

### Adding Analytics

```python
# Track recommendation effectiveness
def track_recommendation_used(user_id, movie_id, recommendation_type):
    analytics.log({
        'event': 'recommendation_used',
        'user_id': user_id,
        'movie_id': movie_id,
        'type': recommendation_type,
        'timestamp': datetime.now()
    })
```

### Cost Optimization

If using Bedrock:

```bash
# Monitor usage
aws bedrock-runtime describe-metrics

# Set up cost alerts
aws cloudwatch put-metric-alarm \
  --alarm-name bedrock-high-cost \
  --threshold 1000 \
  --statistic Sum
```

---

## Summary

✅ **Bedrock Integration**: Works seamlessly with AWS infrastructure
✅ **6 Recommendation Types**: Personalized, Popular, Genre, Similar, Budget, Showtime
✅ **Smart Claude**: Automatically uses right recommendations at right time
✅ **User Tracking**: Learns preferences from booking history
✅ **Production Ready**: Scale with real data backends

Start with the QUICK_START.md and come back here for advanced setup! 🚀
