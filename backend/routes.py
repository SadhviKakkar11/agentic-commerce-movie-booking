"""
Flask API routes for the movie booking system
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from .database import db
from .recommendations import recommendation_engine

api_bp = Blueprint('api', __name__, url_prefix='/api')
MIN_HINDI_RELEASE_DATE = "2026-03-12"

# ============== MOVIES ENDPOINTS ==============

@api_bp.route('/movies', methods=['GET'])
def get_movies():
    """Get all movies or search by filters"""
    genre = request.args.get('genre')
    min_rating = request.args.get('min_rating', type=float)
    language = request.args.get('language')
    released_on_or_after = request.args.get('released_on_or_after')
    
    if genre or min_rating or language or released_on_or_after:
        movies = db.search_movies(
            genre=genre,
            min_rating=min_rating,
            language=language,
            released_on_or_after=released_on_or_after
        )
    else:
        movies = db.get_all_movies()
    
    return jsonify({
        'success': True,
        'count': len(movies),
        'movies': [m.to_dict() for m in movies]
    })

@api_bp.route('/movies/<int:movie_id>', methods=['GET'])
def get_movie(movie_id):
    """Get a specific movie"""
    movie = db.get_movie(movie_id)
    
    if not movie:
        return jsonify({'success': False, 'error': 'Movie not found'}), 404
    
    return jsonify({
        'success': True,
        'movie': movie.to_dict()
    })

# ============== THEATRES ENDPOINTS ==============

@api_bp.route('/theatres', methods=['GET'])
def get_theatres():
    """Get all theatres or filter by city"""
    city = request.args.get('city')
    
    if city:
        theatres = db.get_theatres_by_city(city)
    else:
        theatres = db.get_all_theatres()
    
    return jsonify({
        'success': True,
        'count': len(theatres),
        'theatres': [t.to_dict() for t in theatres]
    })

@api_bp.route('/theatres/<int:theatre_id>', methods=['GET'])
def get_theatre(theatre_id):
    """Get a specific theatre"""
    theatre = db.get_theatre(theatre_id)
    
    if not theatre:
        return jsonify({'success': False, 'error': 'Theatre not found'}), 404
    
    return jsonify({
        'success': True,
        'theatre': theatre.to_dict()
    })

# ============== SHOWS ENDPOINTS ==============

@api_bp.route('/shows', methods=['GET'])
def search_shows():
    """Search shows with multiple filters"""
    movie_id = request.args.get('movie_id', type=int)
    theatre_id = request.args.get('theatre_id', type=int)
    date = request.args.get('date')
    max_price = request.args.get('max_price', type=float)
    
    shows = db.search_shows(
        movie_id=movie_id,
        theatre_id=theatre_id,
        date=date,
        max_price=max_price
    )
    
    # Enrich with movie and theatre details
    enriched_shows = []
    for show in shows:
        movie = db.get_movie(show.movie_id)
        theatre = db.get_theatre(show.theatre_id)
        
        show_dict = show.to_dict()
        show_dict['movie_title'] = movie.title if movie else 'Unknown'
        show_dict['theatre_name'] = theatre.name if theatre else 'Unknown'
        enriched_shows.append(show_dict)
    
    return jsonify({
        'success': True,
        'count': len(enriched_shows),
        'shows': enriched_shows
    })

@api_bp.route('/shows/<int:show_id>', methods=['GET'])
def get_show(show_id):
    """Get a specific show with enriched details"""
    show = db.get_show(show_id)
    
    if not show:
        return jsonify({'success': False, 'error': 'Show not found'}), 404
    
    movie = db.get_movie(show.movie_id)
    theatre = db.get_theatre(show.theatre_id)
    
    show_dict = show.to_dict()
    show_dict['movie_title'] = movie.title if movie else 'Unknown'
    show_dict['movie_duration'] = movie.duration if movie else None
    show_dict['theatre_name'] = theatre.name if theatre else 'Unknown'
    show_dict['theatre_location'] = theatre.location if theatre else None
    
    return jsonify({
        'success': True,
        'show': show_dict
    })

@api_bp.route('/shows/movie/<int:movie_id>', methods=['GET'])
def get_shows_for_movie(movie_id):
    """Get all shows for a movie"""
    date = request.args.get('date')
    shows = db.get_shows_for_movie(movie_id, date=date)
    
    # Filter out shows with no available seats by default
    shows = [s for s in shows if s.available_seats > 0]
    
    enriched_shows = []
    for show in shows:
        theatre = db.get_theatre(show.theatre_id)
        show_dict = show.to_dict()
        show_dict['theatre_name'] = theatre.name if theatre else 'Unknown'
        show_dict['theatre_location'] = theatre.location if theatre else None
        enriched_shows.append(show_dict)
    
    return jsonify({
        'success': True,
        'count': len(enriched_shows),
        'shows': enriched_shows
    })

# ============== BOOKINGS ENDPOINTS ==============

@api_bp.route('/bookings', methods=['POST'])
def create_booking():
    """Create a new booking"""
    data = request.get_json()
    
    required_fields = ['user_id', 'show_id', 'num_seats', 'seats']
    if not all(field in data for field in required_fields):
        return jsonify({
            'success': False,
            'error': f'Missing required fields: {required_fields}'
        }), 400
    
    booking = db.create_booking(
        user_id=data['user_id'],
        show_id=data['show_id'],
        num_seats=data['num_seats'],
        seats=data['seats']
    )
    
    if not booking:
        return jsonify({
            'success': False,
            'error': 'Failed to create booking. Show not found or insufficient seats.'
        }), 400
    
    return jsonify({
        'success': True,
        'message': 'Seats selected. Please complete payment to confirm booking.',
        'next_step': {
            'action': 'make_payment',
            'payment_options_endpoint': f'/api/bookings/{booking.id}/payment-options',
            'payment_endpoint': f'/api/bookings/{booking.id}/pay'
        },
        'booking': booking.to_dict()
    }), 201

@api_bp.route('/bookings/<booking_id>', methods=['GET'])
def get_booking(booking_id):
    """Get a specific booking"""
    booking = db.get_booking(booking_id)
    
    if not booking:
        return jsonify({'success': False, 'error': 'Booking not found'}), 404
    
    show = db.get_show(booking.show_id)
    movie = db.get_movie(show.movie_id) if show else None
    theatre = db.get_theatre(show.theatre_id) if show else None
    
    booking_dict = booking.to_dict()
    booking_dict['movie_title'] = movie.title if movie else 'Unknown'
    booking_dict['theatre_name'] = theatre.name if theatre else 'Unknown'
    booking_dict['show_time'] = show.show_time if show else 'Unknown'
    booking_dict['show_date'] = show.date if show else 'Unknown'
    
    return jsonify({
        'success': True,
        'booking': booking_dict
    })

@api_bp.route('/bookings/user/<user_id>', methods=['GET'])
def get_user_bookings(user_id):
    """Get all bookings for a user"""
    bookings = db.get_user_bookings(user_id)
    
    enriched_bookings = []
    for booking in bookings:
        show = db.get_show(booking.show_id)
        movie = db.get_movie(show.movie_id) if show else None
        theatre = db.get_theatre(show.theatre_id) if show else None
        
        booking_dict = booking.to_dict()
        booking_dict['movie_title'] = movie.title if movie else 'Unknown'
        booking_dict['theatre_name'] = theatre.name if theatre else 'Unknown'
        enriched_bookings.append(booking_dict)
    
    return jsonify({
        'success': True,
        'count': len(enriched_bookings),
        'bookings': enriched_bookings
    })

@api_bp.route('/bookings/<booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    """Cancel a booking"""
    success = db.cancel_booking(booking_id)
    
    if not success:
        return jsonify({'success': False, 'error': 'Booking not found'}), 404
    
    booking = db.get_booking(booking_id)
    return jsonify({
        'success': True,
        'message': 'Booking cancelled successfully',
        'booking': booking.to_dict()
    })


@api_bp.route('/bookings/<booking_id>/payment-options', methods=['GET'])
def get_booking_payment_options(booking_id):
    """Get payment options for a booking."""
    options = db.get_payment_options(booking_id)

    if not options:
        return jsonify({'success': False, 'error': 'Booking not found'}), 404

    return jsonify({
        'success': True,
        'payment_options': options
    })


@api_bp.route('/bookings/<booking_id>/pay', methods=['POST'])
def process_booking_payment(booking_id):
    """Process payment for a booking using selected payment option."""
    data = request.get_json() or {}
    payment_option = data.get('payment_option')
    points_to_redeem = data.get('points_to_redeem', 0)

    if not payment_option:
        return jsonify({
            'success': False,
            'error': "Missing 'payment_option'. Use 'redeem_own_points' or 'best_available_card'"
        }), 400

    result = db.process_payment(
        booking_id=booking_id,
        payment_option=payment_option,
        points_to_redeem=points_to_redeem
    )

    if not result.get('success'):
        return jsonify(result), 400

    return jsonify(result)

# ============== RECOMMENDATIONS ENDPOINTS ==============

@api_bp.route('/recommendations/personalized/<user_id>', methods=['GET'])
def get_personalized_recommendations(user_id):
    """Get personalized movie recommendations for a user"""
    limit = request.args.get('limit', 5, type=int)
    
    recommendations = recommendation_engine.get_personalized_recommendations(user_id, limit)
    
    return jsonify({
        'success': True,
        'user_id': user_id,
        'count': len(recommendations),
        'recommended_movies': [m.to_dict() for m in recommendations]
    })

@api_bp.route('/recommendations/popular', methods=['GET'])
def get_popular_recommendations():
    """Get popular/highest-rated movies"""
    limit = request.args.get('limit', 5, type=int)
    
    movies = recommendation_engine.get_popular_movies(limit)
    
    return jsonify({
        'success': True,
        'count': len(movies),
        'popular_movies': [m.to_dict() for m in movies]
    })

@api_bp.route('/recommendations/by-genre', methods=['GET'])
def get_genre_recommendations():
    """Get recommendations for a specific genre"""
    genre = request.args.get('genre')
    limit = request.args.get('limit', 5, type=int)
    
    if not genre:
        return jsonify({
            'success': False,
            'error': 'Genre parameter required'
        }), 400
    
    movies = recommendation_engine.get_genre_recommendations(genre, limit)
    
    return jsonify({
        'success': True,
        'genre': genre,
        'count': len(movies),
        'movies': [m.to_dict() for m in movies]
    })

@api_bp.route('/recommendations/similar/<int:movie_id>', methods=['GET'])
def get_similar_recommendations(movie_id):
    """Get movies similar to a given movie"""
    limit = request.args.get('limit', 5, type=int)
    
    movie = db.get_movie(movie_id)
    if not movie:
        return jsonify({'success': False, 'error': 'Movie not found'}), 404
    
    similar = recommendation_engine.get_similar_movies(movie_id, limit)
    
    return jsonify({
        'success': True,
        'movie_title': movie.title,
        'count': len(similar),
        'similar_movies': [m.to_dict() for m in similar]
    })

@api_bp.route('/recommendations/budget-friendly', methods=['GET'])
def get_budget_friendly_recommendations():
    """Get recommendations within a budget"""
    max_price = request.args.get('max_price', type=float)
    limit = request.args.get('limit', 5, type=int)
    
    if not max_price:
        return jsonify({
            'success': False,
            'error': 'max_price parameter required'
        }), 400
    
    recommendations = recommendation_engine.get_budget_friendly_recommendations(max_price, limit)
    
    return jsonify({
        'success': True,
        'recommendations': recommendations
    })

@api_bp.route('/recommendations/best-showtimes/<int:movie_id>', methods=['GET'])
def get_best_showtimes(movie_id):
    """Get recommendations for best show times for a movie"""
    movie = db.get_movie(movie_id)
    if not movie:
        return jsonify({'success': False, 'error': 'Movie not found'}), 404
    
    showtimes = recommendation_engine.get_best_show_times(movie_id)
    
    return jsonify({
        'success': True,
        'movie_title': movie.title,
        'best_showtimes': showtimes
    })

# ============== HEALTH CHECK ==============

# ============== USER PROFILE & PREFERENCES ENDPOINTS ==============

@api_bp.route('/users/<user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    """Get user profile with preferences"""
    from .user_profiles import user_profile_manager
    
    profile = user_profile_manager.get_user_profile(user_id)
    if not profile:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'profile': profile.to_dict()
    })

@api_bp.route('/users/<user_id>/preferences', methods=['GET'])
def get_user_preferences(user_id):
    """Get user preferences"""
    from .user_profiles import user_profile_manager
    from dataclasses import asdict
    
    preferences = user_profile_manager.get_preferences(user_id)
    if not preferences:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'preferences': asdict(preferences)
    })

# ============== DECISION MODELING ENDPOINTS ==============

@api_bp.route('/recommendations/smart-search', methods=['POST'])
def smart_search_shows():
    """Smart search with preference alignment and decision modeling"""
    from .user_profiles import user_profile_manager
    from .booking_portals import BookingPortalManager
    from .decision_modeling import BookingRecommender
    
    data = request.get_json()
    user_id = data.get('user_id')
    movie_title = data.get('movie_title')
    location = data.get('location', 'Mumbai')
    date = data.get('date', (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"))

    eligible_movies = db.search_movies(
        language='Hindi',
        released_on_or_after=MIN_HINDI_RELEASE_DATE
    )

    if not eligible_movies:
        return jsonify({'success': False, 'error': 'No eligible Hindi releases found'}), 404

    if movie_title:
        matching_movies = [
            movie for movie in eligible_movies
            if movie_title.lower() in movie.title.lower()
        ]
        if not matching_movies:
            return jsonify({
                'success': False,
                'error': 'Requested movie is not a Hindi release on/after 2026-03-12'
            }), 400
        selected_movie = sorted(matching_movies, key=lambda m: m.rating, reverse=True)[0]
    else:
        selected_movie = sorted(eligible_movies, key=lambda m: m.rating, reverse=True)[0]
        movie_title = selected_movie.title
    
    # Get user profile and preferences
    profile = user_profile_manager.get_user_profile(user_id)
    if not profile:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    # Search across portals
    portal_manager = BookingPortalManager()
    preferred_portal = portal_manager.get_portal_for_preference(
        profile.preferences.preferred_theatres
    )
    
    shows = portal_manager.search_shows(preferred_portal, movie_title, location, date)
    
    # Get best recommendation based on preferences
    recommender = BookingRecommender()
    recommendation = recommender.get_recommendation(shows, profile.preferences)
    
    return jsonify({
        'success': recommendation['success'],
        'constraints': {
            'language': 'Hindi',
            'released_on_or_after': MIN_HINDI_RELEASE_DATE
        },
        'selected_portal': preferred_portal,
        'user_preferences': {
            'preferred_theatre': preferred_portal,
            'preferred_seats': profile.preferences.preferred_seat_types,
            'preferred_timings': profile.preferences.preferred_timings,
            'preferred_offers': profile.preferences.preferred_offers,
            'preferred_locations': profile.preferences.preferred_locations,
            'cc_points': profile.cc_points
        },
        'recommended_option': recommendation.get('recommended_show'),
        'recommendation_score': recommendation.get('score'),
        'reasoning': recommendation.get('reasoning'),
        'all_options': shows
    })


@api_bp.route('/bookings/<booking_id>/payment-recommendation', methods=['GET'])
def get_payment_recommendation(booking_id):
    """Compare own-card points redemption vs best new-card offer and recommend best value."""
    from .user_profiles import user_profile_manager
    from .booking_portals import cc_rewards_db

    booking = db.get_booking(booking_id)
    if not booking:
        return jsonify({'success': False, 'error': 'Booking not found'}), 404

    profile = user_profile_manager.get_user_profile(booking.user_id)
    available_points = profile.cc_points if profile else 0
    current_card_bank = profile.credit_card_bank if profile else 'Current card'
    base_amount = booking.total_price

    max_redeemable_points = int(base_amount / cc_rewards_db.redemption_rate)
    own_points_used = min(available_points, max_redeemable_points)
    own_discount = round(own_points_used * cc_rewards_db.redemption_rate, 2)
    own_payable = round(max(0.0, base_amount - own_discount), 2)

    best_new_card = cc_rewards_db.get_best_credit_card_offer(base_amount)
    new_card_payable = round(best_new_card.get('final_payable', base_amount), 2)

    if own_payable <= new_card_payable:
        recommendation = {
            'recommended_option': 'redeem_own_points',
            'why': f"Your current {current_card_bank} points provide equal or better net payable.",
            'estimated_payable': own_payable
        }
    else:
        recommendation = {
            'recommended_option': 'best_available_card',
            'why': f"Applying for/using {best_new_card['card_name']} gives a lower payable than current points.",
            'estimated_payable': new_card_payable
        }

    return jsonify({
        'success': True,
        'booking_id': booking_id,
        'base_amount': round(base_amount, 2),
        'current_card_option': {
            'credit_card_bank': current_card_bank,
            'available_points': available_points,
            'points_used': own_points_used,
            'discount_amount': own_discount,
            'estimated_payable': own_payable
        },
        'new_card_best_option': best_new_card,
        'recommendation': recommendation
    })

# ============== BOOKING EXECUTION ENDPOINTS ==============

@api_bp.route('/bookings/execute-smart-booking', methods=['POST'])
def execute_smart_booking():
    """Execute complete booking with auto-redemption and payment"""
    from .user_profiles import user_profile_manager
    from .booking_portals import BookingPortalManager, CreditCardRewardsDB, PaymentGateway, ExecutionEngine
    
    data = request.get_json()
    user_id = data.get('user_id')
    show_id = data.get('show_id')
    num_seats = data.get('num_seats', 2)
    portal = data.get('portal', 'BMS')
    cc_points_to_redeem = data.get('cc_points_to_redeem', 0)
    
    # Get user profile
    profile = user_profile_manager.get_user_profile(user_id)
    if not profile:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    # Initialize execution engine
    portal_manager = BookingPortalManager()
    rewards_db = CreditCardRewardsDB()
    payment_gateway = PaymentGateway()
    execution_engine = ExecutionEngine(portal_manager, rewards_db, payment_gateway)
    
    # Execute booking
    result = execution_engine.execute_booking(
        user_id, show_id, num_seats, portal, cc_points_to_redeem
    )
    
    if result['success']:
        # Update user profile
        booking_data = {
            'id': result['booking_summary']['reservation_id'],
            'seats': num_seats,
            'total_price': result['booking_summary']['total_paid']
        }
        user_profile_manager.add_booking(user_id, booking_data)
    
    return jsonify(result)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'API is running',
        'timestamp': datetime.now().isoformat()
    })
