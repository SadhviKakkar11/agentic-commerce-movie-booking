"""
Mock in-memory database with sample data
"""
from datetime import datetime, timedelta
import json
from typing import List, Dict, Optional
from .models import Movie, Theatre, Show, Booking
from .user_profiles import user_profile_manager
from .booking_portals import cc_rewards_db, payment_gateway

MIN_HINDI_RELEASE_DATE = "2026-03-12"

class MockDatabase:
    """Mock database with sample movie booking data"""
    
    def __init__(self):
        self.movies = self._init_movies()
        self.theatres = self._init_theatres()
        self.shows = self._init_shows()
        self.bookings = {}
        self.booking_counter = 1000
    
    def _init_movies(self) -> Dict[int, Movie]:
        """Initialize sample movies"""
        movies_data = [
            {
                "id": 1,
                "title": "Dhurandhar",
                "genre": "Action",
                "rating": 4.5,
                "duration": 163,
                "description": "An action-packed Hindi thriller.",
                "release_date": "2026-03-18",
                "language": "Hindi"
            },
            {
                "id": 2,
                "title": "Khooni Raasta",
                "genre": "Action",
                "rating": 4.3,
                "duration": 154,
                "description": "A revenge drama set in Mumbai's underworld.",
                "release_date": "2026-03-14",
                "language": "Hindi"
            },
            {
                "id": 3,
                "title": "Dil Dosti Drama",
                "genre": "Comedy/Romance",
                "rating": 4.1,
                "duration": 132,
                "description": "A light-hearted campus love story with musical twists.",
                "release_date": "2026-03-12",
                "language": "Hindi"
            },
            {
                "id": 4,
                "title": "Aakhri Faisla",
                "genre": "Drama",
                "rating": 4.6,
                "duration": 171,
                "description": "A courtroom drama about truth, power, and sacrifice.",
                "release_date": "2026-03-19",
                "language": "Hindi"
            },
            {
                "id": 5,
                "title": "Mumbai Files",
                "genre": "Crime",
                "rating": 4.2,
                "duration": 148,
                "description": "A crime investigation thriller based on a high-profile case.",
                "release_date": "2026-03-16",
                "language": "Hindi"
            },
            {
                "id": 6,
                "title": "Shakti Sena",
                "genre": "Action/Sci-Fi",
                "rating": 3.9,
                "duration": 139,
                "description": "A team of heroes defends the city from a futuristic threat.",
                "release_date": "2026-03-20",
                "language": "Hindi"
            },
            {
                "id": 7,
                "title": "Registan 2",
                "genre": "Sci-Fi",
                "rating": 4.0,
                "duration": 158,
                "description": "A grand sci-fi saga unfolding in an epic desert world.",
                "release_date": "2026-03-21",
                "language": "Hindi"
            },
            {
                "id": 8,
                "title": "Hasna Mana Hai",
                "genre": "Comedy",
                "rating": 4.4,
                "duration": 122,
                "description": "A family entertainer packed with humor and heart.",
                "release_date": "2026-03-22",
                "language": "Hindi"
            },
            {
                "id": 9,
                "title": "Tez Raftaar",
                "genre": "Action/Comedy",
                "rating": 4.2,
                "duration": 136,
                "description": "Two rival cops unite for a high-octane chase mission.",
                "release_date": "2026-03-15",
                "language": "Hindi"
            },
            {
                "id": 10,
                "title": "Kaali Raat",
                "genre": "Horror",
                "rating": 3.8,
                "duration": 129,
                "description": "A supernatural mystery in an old hill town mansion.",
                "release_date": "2026-03-13",
                "language": "Hindi"
            }
        ]
        
        return {movie['id']: Movie(**movie) for movie in movies_data}
    
    def _init_theatres(self) -> Dict[int, Theatre]:
        """Initialize sample theatres"""
        theatres_data = [
            {
                "id": 1,
                "name": "Downtown Cinema",
                "location": "Link Road",
                "city": "Mumbai",
                "area": "Andheri",
                "capacity": 250,
                "amenities": ["IMAX", "Dolby Surround", "Reclining Seats"]
            },
            {
                "id": 2,
                "name": "Metro Theatre",
                "location": "Hill Road",
                "city": "Mumbai",
                "area": "Bandra",
                "capacity": 350,
                "amenities": ["4DX", "Premium Seats", "Gourmet Food"]
            },
            {
                "id": 3,
                "name": "Central Plex",
                "location": "LBS Marg",
                "city": "Mumbai",
                "area": "Sion",
                "capacity": 500,
                "amenities": ["IMAX", "Standard Screens", "Budget Friendly"]
            },
            {
                "id": 4,
                "name": "Sunset Theatre",
                "location": "SV Road",
                "city": "Mumbai",
                "area": "Andheri",
                "capacity": 280,
                "amenities": ["Dolby Surround", "Reclining Seats"]
            },
            {
                "id": 5,
                "name": "Hollywood Premium",
                "location": "Turner Road",
                "city": "Mumbai",
                "area": "Bandra",
                "capacity": 400,
                "amenities": ["4DX", "IMAX", "Restaurant"]
            }
        ]
        
        return {theatre['id']: Theatre(**theatre) for theatre in theatres_data}
    
    def _init_shows(self) -> Dict[int, Show]:
        """Initialize sample shows for the next 7 days"""
        shows_data = []
        show_id = 1
        
        times = ["11:00 AM", "2:00 PM", "5:30 PM", "9:00 PM"]
        today = datetime.now()
        
        # Generate shows for today + next 7 days so any day the user asks for is covered
        dates = [(today + timedelta(days=d)).strftime("%Y-%m-%d") for d in range(0, 8)]
        
        for date in dates:
            for movie_id in [1, 2, 3, 4, 5, 6, 7, 8]:
                for theatre_id in [1, 2, 3]:
                    for time in times[:2]:  # 2 shows per theatre per movie per day
                        shows_data.append({
                            "id": show_id,
                            "movie_id": movie_id,
                            "theatre_id": theatre_id,
                            "show_time": time,
                            "date": date,
                            "price": 500.00 if theatre_id == 3 else (600.00 if theatre_id == 1 else 1200.00),
                            "available_seats": 80 + (show_id % 30)
                        })
                        show_id += 1
        
        return {show['id']: Show(**show) for show in shows_data}
    
    # Movie methods
    def get_all_movies(self) -> List[Movie]:
        """Get all movies"""
        return list(self.movies.values())
    
    def get_movie(self, movie_id: int) -> Optional[Movie]:
        """Get a specific movie"""
        return self.movies.get(movie_id)
    
    def search_movies(self, genre: Optional[str] = None,
                     min_rating: Optional[float] = None,
                     language: Optional[str] = None,
                     released_on_or_after: Optional[str] = None) -> List[Movie]:
        """Search movies by genre, rating, language, and release date."""
        results = list(self.movies.values())
        
        if genre:
            genre_lower = genre.lower()
            results = [m for m in results if genre_lower in m.genre.lower()]
        
        if min_rating:
            results = [m for m in results if m.rating >= min_rating]

        if language:
            results = [m for m in results if m.language.lower() == language.lower()]

        if released_on_or_after:
            try:
                cutoff = datetime.strptime(released_on_or_after, "%Y-%m-%d").date()
            except ValueError:
                cutoff = datetime.strptime(MIN_HINDI_RELEASE_DATE, "%Y-%m-%d").date()
            results = [
                m for m in results
                if datetime.strptime(m.release_date, "%Y-%m-%d").date() >= cutoff
            ]
        
        return results
    
    # Theatre methods
    def get_all_theatres(self) -> List[Theatre]:
        """Get all theatres"""
        return list(self.theatres.values())
    
    def get_theatre(self, theatre_id: int) -> Optional[Theatre]:
        """Get a specific theatre"""
        return self.theatres.get(theatre_id)
    
    def get_theatres_by_city(self, city: str) -> List[Theatre]:
        """Get theatres in a specific city"""
        return [t for t in self.theatres.values() if t.city.lower() == city.lower()]
    
    # Show methods
    def get_shows_for_movie(self, movie_id: int, date: Optional[str] = None) -> List[Show]:
        """Get all shows for a specific movie"""
        shows = [s for s in self.shows.values() if s.movie_id == movie_id]
        
        if date:
            shows = [s for s in shows if s.date == date]
        
        return shows
    
    def get_shows_for_theatre(self, theatre_id: int, date: Optional[str] = None) -> List[Show]:
        """Get all shows for a specific theatre"""
        shows = [s for s in self.shows.values() if s.theatre_id == theatre_id]
        
        if date:
            shows = [s for s in shows if s.date == date]
        
        return shows
    
    def get_show(self, show_id: int) -> Optional[Show]:
        """Get a specific show"""
        return self.shows.get(show_id)
    
    def search_shows(self, movie_id: Optional[int] = None, 
                    theatre_id: Optional[int] = None,
                    date: Optional[str] = None,
                    max_price: Optional[float] = None) -> List[Show]:
        """Search shows with multiple filters"""
        results = list(self.shows.values())
        
        if movie_id:
            results = [s for s in results if s.movie_id == movie_id]
        
        if theatre_id:
            results = [s for s in results if s.theatre_id == theatre_id]
        
        if date:
            results = [s for s in results if s.date == date]
        
        if max_price:
            results = [s for s in results if s.price <= max_price]
        
        return results
    
    # Booking methods
    def create_booking(self, user_id: str, show_id: int, 
                      num_seats: int, seats: List[str]) -> Optional[Booking]:
        """Create a new booking"""
        show = self.get_show(show_id)
        
        if not show:
            return None
        
        if show.available_seats < num_seats:
            return None
        
        booking_id = f"BK{self.booking_counter}"
        self.booking_counter += 1
        
        booking = Booking(
            id=booking_id,
            user_id=user_id,
            show_id=show_id,
            num_seats=num_seats,
            seats=seats,
            total_price=show.price * num_seats,
            booking_date=datetime.now().isoformat(),
            status="pending_payment",
            payment_status="pending",
            final_amount=show.price * num_seats
        )
        
        # Update available seats
        show.available_seats -= num_seats
        
        self.bookings[booking_id] = booking
        return booking

    def get_payment_options(self, booking_id: str) -> Optional[Dict]:
        """Get payment options for a booking.

        Users can either redeem points from their own card profile or choose
        the best card discount from available card offers.
        """
        booking = self.get_booking(booking_id)
        if not booking:
            return None

        if booking.payment_status == "completed":
            return {
                "booking_id": booking_id,
                "payment_status": booking.payment_status,
                "message": "Payment already completed for this booking"
            }

        total_amount = booking.total_price
        profile = user_profile_manager.get_user_profile(booking.user_id)
        available_points = profile.cc_points if profile else 0
        card_bank = profile.credit_card_bank if profile else "ICICI Bank"

        # Own card points redemption
        max_redeemable_points = int(total_amount / cc_rewards_db.redemption_rate)
        usable_points = min(available_points, max_redeemable_points)
        points_discount = round(usable_points * cc_rewards_db.redemption_rate, 2)
        payable_with_points = round(max(0.0, total_amount - points_discount), 2)

        # Best available card offer
        best_offer = cc_rewards_db.get_best_credit_card_offer(total_amount)

        return {
            "booking_id": booking_id,
            "payment_status": booking.payment_status,
            "base_amount": round(total_amount, 2),
            "options": {
                "redeem_own_points": {
                    "credit_card_bank": card_bank,
                    "available_points": available_points,
                    "max_redeemable_points": usable_points,
                    "point_value": cc_rewards_db.redemption_rate,
                    "max_discount": points_discount,
                    "payable_after_points": payable_with_points
                },
                "best_available_card": best_offer
            }
        }

    def process_payment(self, booking_id: str, payment_option: str,
                       points_to_redeem: int = 0) -> Dict:
        """Process booking payment using selected option."""
        booking = self.get_booking(booking_id)
        if not booking:
            return {"success": False, "error": "Booking not found"}

        if booking.payment_status == "completed":
            return {
                "success": False,
                "error": "Payment already completed for this booking"
            }

        total_amount = booking.total_price
        discount_amount = 0.0
        points_redeemed = 0
        payment_method = None

        if payment_option == "redeem_own_points":
            profile = user_profile_manager.get_user_profile(booking.user_id)
            available_points = profile.cc_points if profile else 0
            card_bank = profile.credit_card_bank if profile else "ICICI Bank"

            if points_to_redeem <= 0:
                points_to_redeem = available_points

            max_redeemable_points = int(total_amount / cc_rewards_db.redemption_rate)
            points_redeemed = max(0, min(points_to_redeem, available_points, max_redeemable_points))
            discount_amount = round(points_redeemed * cc_rewards_db.redemption_rate, 2)

            if points_redeemed > 0:
                user_profile_manager.redeem_cc_points(booking.user_id, points_redeemed)

            payment_method = f"own_credit_card_points:{card_bank}"

        elif payment_option == "best_available_card":
            best_offer = cc_rewards_db.get_best_credit_card_offer(total_amount)
            discount_amount = best_offer["discount_amount"]
            payment_method = f"best_available_card:{best_offer['card_name']}"

        else:
            return {
                "success": False,
                "error": "Invalid payment option. Use 'redeem_own_points' or 'best_available_card'"
            }

        amount_after_discount = round(max(0.0, total_amount - discount_amount), 2)
        payment_result = payment_gateway.process_payment(
            user_id=booking.user_id,
            amount=amount_after_discount,
            payment_method=payment_method
        )

        if not payment_result.get("success"):
            booking.payment_status = "failed"
            return {"success": False, "error": "Payment processing failed"}

        booking.payment_status = "completed"
        booking.status = "confirmed"
        booking.payment_method = payment_method
        booking.points_redeemed = points_redeemed
        booking.discount_amount = discount_amount
        booking.final_amount = payment_result.get("total_amount", amount_after_discount)
        booking.transaction_id = payment_result.get("transaction_id")

        return {
            "success": True,
            "booking_id": booking.id,
            "payment_option": payment_option,
            "base_amount": round(total_amount, 2),
            "discount_amount": round(discount_amount, 2),
            "amount_after_discount": amount_after_discount,
            "payment": payment_result,
            "booking": booking.to_dict()
        }
    
    def get_booking(self, booking_id: str) -> Optional[Booking]:
        """Get a specific booking"""
        return self.bookings.get(booking_id)
    
    def get_user_bookings(self, user_id: str) -> List[Booking]:
        """Get all bookings for a user"""
        return [b for b in self.bookings.values() if b.user_id == user_id]
    
    def cancel_booking(self, booking_id: str) -> bool:
        """Cancel a booking"""
        booking = self.bookings.get(booking_id)
        
        if not booking:
            return False
        
        booking.status = "cancelled"
        
        # Restore available seats
        show = self.get_show(booking.show_id)
        if show:
            show.available_seats += booking.num_seats
        
        return True

# Global database instance
db = MockDatabase()
