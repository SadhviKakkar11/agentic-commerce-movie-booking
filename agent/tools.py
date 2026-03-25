"""
Tool definitions for Claude agent
Maps backend APIs to tools Claude can call
"""
import json
import requests
from .config import BACKEND_URL

class ToolHandler:
    """Handles tool calls from Claude"""

    MIN_HINDI_RELEASE_DATE = "2026-03-12"
    
    @staticmethod
    def search_movies(genre=None, min_rating=None, language="Hindi", released_on_or_after=None):
        """Search for movies by genre/rating, defaulting to Hindi releases from 12-Mar-2026."""
        params = {}
        if genre:
            params['genre'] = genre
        if min_rating:
            params['min_rating'] = min_rating
        params['language'] = language
        params['released_on_or_after'] = released_on_or_after or ToolHandler.MIN_HINDI_RELEASE_DATE
        
        try:
            response = requests.get(f"{BACKEND_URL}/api/movies", params=params)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_movie_details(movie_id):
        """Get detailed information about a specific movie"""
        try:
            response = requests.get(f"{BACKEND_URL}/api/movies/{movie_id}")
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_theatres(city=None):
        """Get list of theatres, optionally filtered by city"""
        params = {}
        if city:
            params['city'] = city
        
        try:
            response = requests.get(f"{BACKEND_URL}/api/theatres", params=params)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_theatre_details(theatre_id):
        """Get detailed information about a specific theatre"""
        try:
            response = requests.get(f"{BACKEND_URL}/api/theatres/{theatre_id}")
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def search_shows(movie_id=None, theatre_id=None, date=None, max_price=None):
        """Search for shows with multiple criteria"""
        params = {}
        if movie_id:
            params['movie_id'] = movie_id
        if theatre_id:
            params['theatre_id'] = theatre_id
        if date:
            params['date'] = date
        if max_price:
            params['max_price'] = max_price
        
        try:
            response = requests.get(f"{BACKEND_URL}/api/shows", params=params)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_show_details(show_id):
        """Get detailed information about a specific show"""
        try:
            response = requests.get(f"{BACKEND_URL}/api/shows/{show_id}")
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_shows_for_movie(movie_id, date=None):
        """Get all available shows for a specific movie"""
        params = {}
        if date:
            params['date'] = date
        
        try:
            response = requests.get(f"{BACKEND_URL}/api/shows/movie/{movie_id}", params=params)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def book_tickets(user_id, show_id, num_seats, seats):
        """Book tickets for a show"""
        payload = {
            'user_id': user_id,
            'show_id': show_id,
            'num_seats': num_seats,
            'seats': seats
        }
        
        try:
            response = requests.post(f"{BACKEND_URL}/api/bookings", json=payload)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_booking_details(booking_id):
        """Get details about a booking"""
        try:
            response = requests.get(f"{BACKEND_URL}/api/bookings/{booking_id}")
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_user_bookings(user_id):
        """Get all bookings for a user"""
        try:
            response = requests.get(f"{BACKEND_URL}/api/bookings/user/{user_id}")
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def cancel_booking(booking_id):
        """Cancel an existing booking"""
        try:
            response = requests.post(f"{BACKEND_URL}/api/bookings/{booking_id}/cancel")
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_payment_options(booking_id):
        """Get payment options for a pending booking."""
        try:
            response = requests.get(f"{BACKEND_URL}/api/bookings/{booking_id}/payment-options")
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def make_payment(booking_id, payment_option, points_to_redeem=0):
        """Complete payment for a booking using selected payment option."""
        payload = {
            'payment_option': payment_option,
            'points_to_redeem': points_to_redeem
        }

        try:
            response = requests.post(f"{BACKEND_URL}/api/bookings/{booking_id}/pay", json=payload)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_payment_recommendation(booking_id):
        """Compare own card points vs better new-card option for this booking."""
        try:
            response = requests.get(f"{BACKEND_URL}/api/bookings/{booking_id}/payment-recommendation")
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def smart_search_shows(user_id, movie_title=None, location="Mumbai", date=None):
        """Find the best show option using user preferences and decision modeling."""
        payload = {
            "user_id": user_id,
            "movie_title": movie_title,
            "location": location,
            "date": date
        }
        try:
            response = requests.post(f"{BACKEND_URL}/api/recommendations/smart-search", json=payload)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_personalized_recommendations(user_id, limit=5):
        """Get personalized movie recommendations for a user based on their history"""
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/recommendations/personalized/{user_id}",
                params={"limit": limit}
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_popular_movies_recommendation(limit=5):
        """Get highest-rated popular movies"""
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/recommendations/popular",
                params={"limit": limit}
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_genre_recommendations(genre, limit=5):
        """Get recommendations for a specific genre"""
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/recommendations/by-genre",
                params={"genre": genre, "limit": limit}
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_similar_movies_recommendation(movie_id, limit=5):
        """Get movies similar to a given movie"""
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/recommendations/similar/{movie_id}",
                params={"limit": limit}
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_budget_friendly_recommendations(max_price, limit=5):
        """Get best show deals within a budget"""
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/recommendations/budget-friendly",
                params={"max_price": max_price, "limit": limit}
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_best_showtimes(movie_id):
        """Get recommendations for best show times for a movie"""
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/recommendations/best-showtimes/{movie_id}"
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}


# Tool definitions for Claude
TOOLS = [
    {
        "name": "search_movies",
        "description": "Search for movies in the catalog. By default this returns Hindi movies released on/after 2026-03-12. You can filter further by genre and minimum rating.",
        "input_schema": {
            "type": "object",
            "properties": {
                "genre": {
                    "type": "string",
                    "description": "Movie genre to search for (e.g., 'Action', 'Comedy', 'Drama', 'Sci-Fi')"
                },
                "min_rating": {
                    "type": "number",
                    "description": "Minimum movie rating (0-5)"
                },
                "language": {
                    "type": "string",
                    "description": "Movie language filter. Defaults to Hindi."
                },
                "released_on_or_after": {
                    "type": "string",
                    "description": "Release date floor in YYYY-MM-DD. Defaults to 2026-03-12."
                }
            }
        }
    },
    {
        "name": "get_movie_details",
        "description": "Get detailed information about a specific movie including synopsis, runtime, and rating.",
        "input_schema": {
            "type": "object",
            "properties": {
                "movie_id": {
                    "type": "integer",
                    "description": "The ID of the movie"
                }
            },
            "required": ["movie_id"]
        }
    },
    {
        "name": "get_theatres",
        "description": "Get list of available theatres. Optionally filter by city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City to search for theatres (e.g., 'New York', 'Los Angeles')"
                }
            }
        }
    },
    {
        "name": "get_theatre_details",
        "description": "Get detailed information about a specific theatre including location and amenities.",
        "input_schema": {
            "type": "object",
            "properties": {
                "theatre_id": {
                    "type": "integer",
                    "description": "The ID of the theatre"
                }
            },
            "required": ["theatre_id"]
        }
    },
    {
        "name": "search_shows",
        "description": "Search for movie shows with advanced filtering. Can filter by movie, theatre, date, and maximum price.",
        "input_schema": {
            "type": "object",
            "properties": {
                "movie_id": {
                    "type": "integer",
                    "description": "Filter by specific movie ID"
                },
                "theatre_id": {
                    "type": "integer",
                    "description": "Filter by specific theatre ID"
                },
                "date": {
                    "type": "string",
                    "description": "Filter by show date (format: YYYY-MM-DD)"
                },
                "max_price": {
                    "type": "number",
                    "description": "Maximum ticket price"
                }
            }
        }
    },
    {
        "name": "get_show_details",
        "description": "Get detailed information about a specific show including movie, theatre, time, and available seats.",
        "input_schema": {
            "type": "object",
            "properties": {
                "show_id": {
                    "type": "integer",
                    "description": "The ID of the show"
                }
            },
            "required": ["show_id"]
        }
    },
    {
        "name": "get_shows_for_movie",
        "description": "Get all available shows for a specific movie. Optionally filter by date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "movie_id": {
                    "type": "integer",
                    "description": "The ID of the movie"
                },
                "date": {
                    "type": "string",
                    "description": "Optional date filter (format: YYYY-MM-DD)"
                }
            },
            "required": ["movie_id"]
        }
    },
    {
        "name": "book_tickets",
        "description": "Book tickets for a show. Provide user ID, show ID, number of seats, and seat numbers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user ID making the booking"
                },
                "show_id": {
                    "type": "integer",
                    "description": "The ID of the show to book"
                },
                "num_seats": {
                    "type": "integer",
                    "description": "Number of seats to book"
                },
                "seats": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of seat numbers (e.g., ['A1', 'A2', 'B3'])"
                }
            },
            "required": ["user_id", "show_id", "num_seats", "seats"]
        }
    },
    {
        "name": "smart_search_shows",
        "description": "Get the best theatre, show timing, and seat format recommendation for a user using preference alignment and scoring.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user ID (e.g., user_ram_001)"
                },
                "movie_title": {
                    "type": "string",
                    "description": "Optional movie title. Must be a Hindi movie released on/after 2026-03-12."
                },
                "location": {
                    "type": "string",
                    "description": "City/location for search (default: Mumbai)"
                },
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD"
                }
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "get_booking_details",
        "description": "Get details about a specific booking using the booking ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "booking_id": {
                    "type": "string",
                    "description": "The booking ID"
                }
            },
            "required": ["booking_id"]
        }
    },
    {
        "name": "get_user_bookings",
        "description": "Get all bookings made by a specific user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user ID to retrieve bookings for"
                }
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "cancel_booking",
        "description": "Cancel an existing booking using the booking ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "booking_id": {
                    "type": "string",
                    "description": "The ID of the booking to cancel"
                }
            },
            "required": ["booking_id"]
        }
    },
    {
        "name": "get_payment_options",
        "description": "Get payment options for a booking. Shows user points redemption details and best available credit card offer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "booking_id": {
                    "type": "string",
                    "description": "Booking ID for which payment options are required"
                }
            },
            "required": ["booking_id"]
        }
    },
    {
        "name": "make_payment",
        "description": "Make payment for a booking. Option 1: redeem_own_points, Option 2: best_available_card.",
        "input_schema": {
            "type": "object",
            "properties": {
                "booking_id": {
                    "type": "string",
                    "description": "Booking ID to pay for"
                },
                "payment_option": {
                    "type": "string",
                    "description": "Payment option: 'redeem_own_points' or 'best_available_card'"
                },
                "points_to_redeem": {
                    "type": "integer",
                    "description": "Optional points to redeem when using redeem_own_points"
                }
            },
            "required": ["booking_id", "payment_option"]
        }
    },
    {
        "name": "get_payment_recommendation",
        "description": "Get payment recommendation that compares current card points redemption versus best new card offer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "booking_id": {
                    "type": "string",
                    "description": "Booking ID to evaluate payment strategy"
                }
            },
            "required": ["booking_id"]
        }
    },
    {
        "name": "get_personalized_recommendations",
        "description": "Get personalized movie recommendations for a user based on their booking history and preferences. Great for repeat customers!",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user ID to get recommendations for"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of recommendations to return (default: 5)"
                }
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "get_popular_movies_recommendation",
        "description": "Get the highest-rated and most popular movies currently showing. Perfect for users who want the best-reviewed options.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of movies to return (default: 5)"
                }
            }
        }
    },
    {
        "name": "get_genre_recommendations",
        "description": "Get top-rated movies in a specific genre. Use this to help users find movies they'll love in their favorite category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "genre": {
                    "type": "string",
                    "description": "Movie genre (e.g., 'Action', 'Comedy', 'Drama', 'Sci-Fi', 'Horror')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of movies to return (default: 5)"
                }
            },
            "required": ["genre"]
        }
    },
    {
        "name": "get_similar_movies_recommendation",
        "description": "Get movies similar to a movie the user likes or is considering. Great for when they want more like that one movie.",
        "input_schema": {
            "type": "object",
            "properties": {
                "movie_id": {
                    "type": "integer",
                    "description": "The ID of the movie to find similar movies for"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of similar movies to return (default: 5)"
                }
            },
            "required": ["movie_id"]
        }
    },
    {
        "name": "get_budget_friendly_recommendations",
        "description": "Find the best movie deals within a specified budget. Shows available theatres and times for each movie.",
        "input_schema": {
            "type": "object",
            "properties": {
                "max_price": {
                    "type": "number",
                    "description": "Maximum ticket price in Rupees"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of recommendations to return (default: 5)"
                }
            },
            "required": ["max_price"]
        }
    },
    {
        "name": "get_best_showtimes",
        "description": "Get analysis of the best show times for a movie with pricing and availability information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "movie_id": {
                    "type": "integer",
                    "description": "The ID of the movie"
                }
            },
            "required": ["movie_id"]
        }
    }
]


def process_tool_call(tool_name, tool_input):
    """Process a tool call from Claude"""
    if tool_name == "search_movies":
        return ToolHandler.search_movies(**tool_input)
    elif tool_name == "smart_search_shows":
        return ToolHandler.smart_search_shows(**tool_input)
    elif tool_name == "get_movie_details":
        return ToolHandler.get_movie_details(**tool_input)
    elif tool_name == "get_theatres":
        return ToolHandler.get_theatres(**tool_input)
    elif tool_name == "get_theatre_details":
        return ToolHandler.get_theatre_details(**tool_input)
    elif tool_name == "search_shows":
        return ToolHandler.search_shows(**tool_input)
    elif tool_name == "get_show_details":
        return ToolHandler.get_show_details(**tool_input)
    elif tool_name == "get_shows_for_movie":
        return ToolHandler.get_shows_for_movie(**tool_input)
    elif tool_name == "book_tickets":
        return ToolHandler.book_tickets(**tool_input)
    elif tool_name == "get_booking_details":
        return ToolHandler.get_booking_details(**tool_input)
    elif tool_name == "get_user_bookings":
        return ToolHandler.get_user_bookings(**tool_input)
    elif tool_name == "cancel_booking":
        return ToolHandler.cancel_booking(**tool_input)
    elif tool_name == "get_payment_options":
        return ToolHandler.get_payment_options(**tool_input)
    elif tool_name == "make_payment":
        return ToolHandler.make_payment(**tool_input)
    elif tool_name == "get_payment_recommendation":
        return ToolHandler.get_payment_recommendation(**tool_input)
    elif tool_name == "get_personalized_recommendations":
        return ToolHandler.get_personalized_recommendations(**tool_input)
    elif tool_name == "get_popular_movies_recommendation":
        return ToolHandler.get_popular_movies_recommendation(**tool_input)
    elif tool_name == "get_genre_recommendations":
        return ToolHandler.get_genre_recommendations(**tool_input)
    elif tool_name == "get_similar_movies_recommendation":
        return ToolHandler.get_similar_movies_recommendation(**tool_input)
    elif tool_name == "get_budget_friendly_recommendations":
        return ToolHandler.get_budget_friendly_recommendations(**tool_input)
    elif tool_name == "get_best_showtimes":
        return ToolHandler.get_best_showtimes(**tool_input)
    else:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}
