"""
User Profiles and Preferences Management
Tracks user booking history and preferences
"""
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict

@dataclass
class UserPreferences:
    """User booking preferences based on history"""
    preferred_theatres: List[str] = field(default_factory=list)  # e.g., ["PVR", "BMS"]
    preferred_seat_types: List[str] = field(default_factory=list)  # e.g., ["Recliner", "Premium"]
    preferred_timings: List[str] = field(default_factory=list)  # e.g., ["1-3 PM", "Evening"]
    preferred_offers: List[str] = field(default_factory=list)  # e.g., ["BOGO", "Student Discount"]
    preferred_locations: List[str] = field(default_factory=list)  # e.g., ["Andheri", "Bandra"]
    preferred_genres: List[str] = field(default_factory=list)  # e.g., ["Action", "Comedy"]
    average_budget: float = 0.0

@dataclass
class UserProfile:
    """Complete user profile with booking history and preferences"""
    user_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Rewards and points
    credit_card_bank: str = "ICICI Bank"
    cc_points: int = 0  # Credit card reward points
    total_spent: float = 0.0
    bookings_count: int = 0
    
    # Preferences
    preferences: UserPreferences = field(default_factory=UserPreferences)
    
    # Booking history
    booking_history: List[Dict] = field(default_factory=list)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "credit_card_bank": self.credit_card_bank,
            "cc_points": self.cc_points,
            "total_spent": self.total_spent,
            "bookings_count": self.bookings_count,
            "preferences": asdict(self.preferences),
            "created_at": self.created_at
        }

class UserProfileManager:
    """Manages user profiles and preferences"""
    
    def __init__(self):
        self.profiles: Dict[str, UserProfile] = {}
        self._init_sample_users()
    
    def _init_sample_users(self):
        """Initialize sample user profiles"""
        # Sample user: RAM
        ram_profile = UserProfile(
            user_id="user_ram_001",
            name="Ram Kumar",
            email="ram@example.com",
            phone="9876543210",
            credit_card_bank="ICICI Bank",
            cc_points=1000,
            total_spent=5000.0,
            bookings_count=10,
            preferences=UserPreferences(
                preferred_theatres=["PVR"],
                preferred_seat_types=["Recliner", "Premium"],
                preferred_timings=["1-3 PM", "Evening"],
                preferred_offers=["BOGO", "Student Discount"],
                preferred_locations=["Andheri", "Bandra", "Sion"],
                preferred_genres=["Action", "Comedy"],
                average_budget=1500.0
            )
        )
        self.profiles[ram_profile.user_id] = ram_profile
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID"""
        return self.profiles.get(user_id)
    
    def create_user_profile(self, user_id: str, name: str, 
                           email: Optional[str] = None,
                           phone: Optional[str] = None) -> UserProfile:
        """Create a new user profile"""
        if user_id in self.profiles:
            return self.profiles[user_id]
        
        profile = UserProfile(
            user_id=user_id,
            name=name,
            email=email,
            phone=phone
        )
        self.profiles[user_id] = profile
        return profile
    
    def get_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """Get user preferences"""
        profile = self.get_user_profile(user_id)
        return profile.preferences if profile else None
    
    def update_preferences(self, user_id: str, preferences: UserPreferences) -> bool:
        """Update user preferences"""
        profile = self.get_user_profile(user_id)
        if profile:
            profile.preferences = preferences
            return True
        return False
    
    def add_booking(self, user_id: str, booking_data: Dict) -> bool:
        """Record a booking in user history"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return False
        
        # Add to history
        booking_record = {
            "booking_id": booking_data.get("id"),
            "movie": booking_data.get("title"),
            "theatre": booking_data.get("theatre_name"),
            "seats": booking_data.get("seats"),
            "amount": booking_data.get("total_price"),
            "timestamp": datetime.now().isoformat()
        }
        profile.booking_history.append(booking_record)
        
        # Update stats
        profile.bookings_count += 1
        profile.total_spent += booking_data.get("total_price", 0)
        
        # Learn preferences
        self._learn_preferences(user_id, booking_data)
        
        return True
    
    def _learn_preferences(self, user_id: str, booking_data: Dict):
        """Learn user preferences from booking data"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return
        
        prefs = profile.preferences
        
        # Update preferred theatres
        theatre = booking_data.get("theatre_name")
        if theatre and theatre not in prefs.preferred_theatres:
            prefs.preferred_theatres.append(theatre)
        
        # Update preferred genres
        genre = booking_data.get("genre")
        if genre and genre not in prefs.preferred_genres:
            prefs.preferred_genres.append(genre)
        
        # Update average budget
        amount = booking_data.get("total_price", 0)
        if prefs.average_budget == 0:
            prefs.average_budget = amount
        else:
            prefs.average_budget = (prefs.average_budget + amount) / 2
    
    def add_cc_points(self, user_id: str, points: int) -> bool:
        """Add credit card reward points"""
        profile = self.get_user_profile(user_id)
        if profile:
            profile.cc_points += points
            return True
        return False
    
    def redeem_cc_points(self, user_id: str, points: int) -> bool:
        """Redeem credit card reward points"""
        profile = self.get_user_profile(user_id)
        if profile and profile.cc_points >= points:
            profile.cc_points -= points
            return True
        return False
    
    def get_all_profiles(self) -> List[UserProfile]:
        """Get all user profiles"""
        return list(self.profiles.values())


# Global user profile manager instance
user_profile_manager = UserProfileManager()
