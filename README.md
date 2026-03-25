# Movie Ticket Booking Agent

An AI-powered movie ticket booking system using Claude's tool use capabilities to help users search, filter, and book movie tickets.

## Project Overview

This project demonstrates an agentic commerce use case where Claude AI (via AWS Bedrock) acts as a smart booking assistant that can:
- Browse available movies and theatres
- Filter by movie genre, theatre location, show time, and price
- Check seat availability
- Process ticket bookings
- Provide recommendations based on user preferences
- Recommend only Hindi movies released on/after 12-Mar-2026
- Compare payment savings between current card points and better new-card offers

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude AI Agent                          │
│  (Tool Use / Function Calling)                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    ┌────────┐   ┌─────────┐   ┌──────────┐
    │ Movies │   │ Theatres│   │ Bookings │
    │  API   │   │  API    │   │  API     │
    └────────┘   └─────────┘   └──────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
            ┌──────────▼──────────┐
            │   Mock Database     │
            │  (JSON files or     │
            │   in-memory)        │
            └─────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.8+
- AWS Bedrock access to Claude model
- AWS credentials with permission to call Bedrock runtime

### Installation
```bash
# Clone or navigate to project directory
cd movie-ticket-booking-agent

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Run the Agent
```bash
python agent.py
```

### Run on CodeSandbox (Python)
```bash
pip install -r requirements.txt
cp .env.example .env
# Update AWS credentials and Bedrock model in .env
python -m backend.app
```

In a second terminal:
```bash
python examples/web_ui.py
```

Then open the preview URL for port 5001.

## Project Structure

```
movie-ticket-booking-agent/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment variables template
│
├── backend/                           # Mock Backend APIs
│   ├── app.py                        # Flask/FastAPI server
│   ├── database.py                   # In-memory database
│   ├── models.py                     # Data models (Movie, Theatre, Booking)
│   └── routes.py                     # API endpoints
│
├── agent/                            # Claude Agent Code
│   ├── agent.py                      # Main agent logic
│   ├── tools.py                      # Tool definitions
│   ├── prompts.py                    # System prompts
│   └── config.py                     # Configuration
│
└── examples/                         # Example implementations
    ├── simple_booking.py             # Basic booking flow
    ├── advanced_agent.py             # Complex multi-turn conversations
    └── web_ui.py                     # Simple web interface (optional)
```

## Step-by-Step Implementation Guide

See the individual files for detailed implementation steps.

## API Endpoints

### Movies API
- `GET /movies` - List all movies
- `GET /movies/:id` - Get movie details
- `GET /movies/search?genre=action&rating=4.5` - Search movies

### Theatres API
- `GET /theatres` - List all theatres
- `GET /theatres/:id` - Get theatre details
- `GET /theatres/shows?movie_id=1&date=2024-03-25` - Get available shows

### Bookings API
- `POST /bookings` - Create a new booking
- `GET /bookings/:id` - Get booking details
- `GET /bookings` - List user's bookings
- `GET /bookings/:id/payment-recommendation` - Compare current-card points vs best new-card offer

## Tools Available to Claude

The agent has access to these tools:
1. **search_movies** - Search Hindi movies released on/after 12-Mar-2026 (default)
2. **get_theatre_shows** - Get available shows for a movie
3. **check_seat_availability** - Check available seats for a show
4. **book_tickets** - Reserve and book tickets
5. **get_booking_details** - Retrieve booking information
6. **smart_search_shows** - Get best theatre/seat format/timing recommendation
7. **get_payment_recommendation** - Get the best payment strategy before checkout

## Example Conversation

```
User: "I want to watch an action movie tomorrow evening in downtown area"

Claude: I'll help you find and book an action movie for tomorrow evening. Let me search for available options...
[Calls search_movies with genre=action and date filters]
[Calls get_theatre_shows to find downtown locations]

Claude: I found 3 great action movies available:
1. Mission Impossible - 7:00 PM at Downtown Cinema
2. John Wick 4 - 9:00 PM at Metro Theatre
3. Fast X - 8:30 PM at Central Plex

Which one interests you?

User: "Book 2 tickets for John Wick 4 at Metro Theatre"

Claude: Perfect! Let me check seat availability and complete your booking...
[Calls check_seat_availability]
[Calls book_tickets]

Claude: ✓ Booking confirmed!
Booking ID: BK123456
Movie: John Wick 4
Theatre: Metro Theatre
Time: 9:00 PM
Seats: A5, A6
Total: $30
```

## Claude's Tool Use Features

This implementation uses:
- **Function Calling** - Claude calls backend APIs as functions
- **Multi-turn Conversations** - Context maintained across multiple interactions
- **Iterative Refinement** - User feedback refines search results
- **Error Handling** - Graceful handling of API errors
- **Natural Language** - Conversational UX with Claude

## Running Locally with Mock Data

The mock database includes:
- 10 sample movies with genres, ratings, and descriptions
- 5 sample theatres with locations and capacities
- Sample shows with various times and prices
- Mock seat inventory (100 seats per theatre per show)

## Next Steps

1. Start with `backend/database.py` to understand the data structure
2. Review `backend/app.py` for API implementation
3. Study `agent/tools.py` to see tool definitions for Claude
4. Check `agent/agent.py` for the main agent logic
5. Run `examples/simple_booking.py` to see a basic example
6. Try `examples/advanced_agent.py` for complex scenarios

## Production Considerations

- Add authentication and user management
- Implement real payment processing
- Add email/SMS notifications
- Create a proper database (PostgreSQL, MongoDB)
- Add caching for performance
- Implement rate limiting
- Add comprehensive logging

## Support & Documentation

For more on Claude's tool use:
- https://docs.anthropic.com/en/docs/build-a-chatbot-with-tool-use
- https://docs.anthropic.com/en/docs/build-a-chatbot-with-tool-use#automatic-tool-use

## License

MIT
