"""
Flask application setup for the movie booking backend API
"""
from flask import Flask
from .routes import api_bp
from .user_profiles import UserProfileManager
from .booking_portals import BookingPortalManager, CreditCardRewardsDB, PaymentGateway

# Initialize global managers
user_profile_manager = UserProfileManager()
booking_portal_manager = BookingPortalManager()
cc_rewards_db = CreditCardRewardsDB()
payment_gateway = PaymentGateway()

def create_app():
    """Create and configure the Flask app"""
    app = Flask(__name__)
    
    # Configuration
    app.config['JSON_SORT_KEYS'] = False
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Simple root endpoint
    @app.route('/')
    def index():
        return {
            'message': 'Movie Ticket Booking API',
            'version': '2.0',
            'docs': 'See /api/health for status'
        }
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
