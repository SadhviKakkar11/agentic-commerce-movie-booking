"""
Recommendation engine for personalized movie suggestions
"""
from typing import List, Dict, Optional
from datetime import datetime
from .database import db
from .models import Movie

HINDI_LANGUAGE = "Hindi"
MIN_RELEASE_DATE = datetime.strptime("2026-03-12", "%Y-%m-%d").date()

class RecommendationEngine:
    """Generates personalized movie recommendations"""
    
    def __init__(self):
        self.user_preferences = {}  # Track user preferences
        self.user_history = {}      # Track user booking history
    
    def track_booking(self, user_id: str, show_id: int):
        """Track a user's booking for preference learning"""
        if not db.TRACK_USER_PREFERENCES:
            return
        
        show = db.get_show(show_id)
        if not show:
            return
        
        movie = db.get_movie(show.movie_id)
        if not movie:
            return
        
        # Initialize user profile if needed
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                'genres': {},
                'avg_rating': 0,
                'total_bookings': 0
            }
            self.user_history[user_id] = []
        
        # Track genre preference
        for genre in movie.genre.split('/'):
            genre = genre.strip()
            self.user_preferences[user_id]['genres'][genre] = \
                self.user_preferences[user_id]['genres'].get(genre, 0) + 1
        
        # Track rating preference
        old_avg = self.user_preferences[user_id]['avg_rating']
        total = self.user_preferences[user_id]['total_bookings']
        self.user_preferences[user_id]['avg_rating'] = \
            (old_avg * total + movie.rating) / (total + 1)
        
        self.user_preferences[user_id]['total_bookings'] += 1
        self.user_history[user_id].append(show.movie_id)

    @staticmethod
    def _is_eligible_movie(movie: Movie) -> bool:
        """Movies must be Hindi and released on/after 12-Mar-2026."""
        try:
            release_date = datetime.strptime(movie.release_date, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return False

        return movie.language.lower() == HINDI_LANGUAGE.lower() and release_date >= MIN_RELEASE_DATE
    
    def get_personalized_recommendations(
        self, user_id: str, limit: int = 5
    ) -> List[Movie]:
        """Get personalized movie recommendations for a user"""
        
        # If no user history, return popular movies
        if user_id not in self.user_history or not self.user_history[user_id]:
            return self.get_popular_movies(limit)
        
        prefs = self.user_preferences[user_id]
        recommendations = []
        watched_movie_ids = set(self.user_history[user_id])
        
        # Find top genre preference
        if prefs['genres']:
            top_genre = max(prefs['genres'].items(), key=lambda x: x[1])[0]
            min_rating = max(0, prefs['avg_rating'] - 0.5)  # Similar or higher rated
            
            # Search by top genre and rating
            movies = db.search_movies(
                genre=top_genre,
                min_rating=min_rating,
                language=HINDI_LANGUAGE,
                released_on_or_after=MIN_RELEASE_DATE.strftime("%Y-%m-%d")
            )
            
            # Filter out already watched
            movies = [m for m in movies if m.id not in watched_movie_ids]
            
            recommendations.extend(movies[:limit])
        
        # If we need more recommendations, add popular movies
        if len(recommendations) < limit:
            popular = self.get_popular_movies(limit * 2)
            popular = [m for m in popular if m.id not in watched_movie_ids]
            
            for movie in popular:
                if movie not in recommendations and len(recommendations) < limit:
                    recommendations.append(movie)
        
        return recommendations[:limit]
    
    def get_popular_movies(self, limit: int = 5) -> List[Movie]:
        """Get highest-rated movies"""
        movies = [m for m in db.get_all_movies() if self._is_eligible_movie(m)]
        movies.sort(key=lambda m: m.rating, reverse=True)
        return movies[:limit]
    
    def get_genre_recommendations(
        self, genre: str, limit: int = 5, exclude_movie_ids: Optional[List[int]] = None
    ) -> List[Movie]:
        """Get recommendations for a specific genre"""
        movies = db.search_movies(
            genre=genre,
            language=HINDI_LANGUAGE,
            released_on_or_after=MIN_RELEASE_DATE.strftime("%Y-%m-%d")
        )
        
        if exclude_movie_ids:
            movies = [m for m in movies if m.id not in exclude_movie_ids]
        
        movies.sort(key=lambda m: m.rating, reverse=True)
        return movies[:limit]
    
    def get_similar_movies(
        self, movie_id: int, limit: int = 5
    ) -> List[Movie]:
        """Get movies similar to a given movie"""
        movie = db.get_movie(movie_id)
        if not movie:
            return []
        
        # Find other movies with same genre
        similar = self.get_genre_recommendations(
            movie.genre.split('/')[0].strip(),
            limit * 2
        )
        
        # Filter out the input movie
        similar = [m for m in similar if m.id != movie_id]
        
        return similar[:limit]
    
    def get_budget_friendly_recommendations(
        self, max_price: float, limit: int = 5
    ) -> Dict:
        """Get recommendations within a budget"""
        
        # Get all shows within budget
        eligible_movie_ids = {
            m.id for m in db.get_all_movies() if self._is_eligible_movie(m)
        }
        shows = [
            s for s in db.shows.values()
            if s.price <= max_price and s.movie_id in eligible_movie_ids
        ]
        shows.sort(key=lambda s: db.get_movie(s.movie_id).rating if db.get_movie(s.movie_id) else 0, reverse=True)
        
        recommendations = {
            'budget': max_price,
            'shows': [],
            'count': 0
        }
        
        seen_movies = set()
        for show in shows:
            if show.movie_id not in seen_movies and len(recommendations['shows']) < limit:
                movie = db.get_movie(show.movie_id)
                theatre = db.get_theatre(show.theatre_id)
                
                recommendations['shows'].append({
                    'show_id': show.id,
                    'movie_title': movie.title if movie else 'Unknown',
                    'theatre_name': theatre.name if theatre else 'Unknown',
                    'show_time': show.show_time,
                    'price': show.price,
                    'rating': movie.rating if movie else 0
                })
                seen_movies.add(show.movie_id)
                recommendations['count'] += 1
        
        return recommendations
    
    def get_best_show_times(self, movie_id: int) -> Dict:
        """Recommend best show times for a movie"""
        shows = db.get_shows_for_movie(movie_id)
        shows = [s for s in shows if s.available_seats > 10]  # Show available shows
        
        # Group by time and rank by availability
        time_groups = {}
        for show in shows:
            time = show.show_time
            if time not in time_groups:
                time_groups[time] = {
                    'shows': [],
                    'avg_price': 0,
                    'avg_seats': 0
                }
            time_groups[time]['shows'].append(show)
        
        # Calculate averages and rank
        recommendations = {}
        for time_slot, data in time_groups.items():
            if data['shows']:
                data['avg_price'] = sum(s.price for s in data['shows']) / len(data['shows'])
                data['avg_seats'] = sum(s.available_seats for s in data['shows']) / len(data['shows'])
                
                recommendations[time_slot] = {
                    'available_theatres': len(data['shows']),
                    'average_price': round(data['avg_price'], 2),
                    'average_seats_available': int(data['avg_seats']),
                    'best_price': min(s.price for s in data['shows']),
                    'most_seats': max(s.available_seats for s in data['shows'])
                }
        
        return recommendations


# Global recommendation engine instance
recommendation_engine = RecommendationEngine()
