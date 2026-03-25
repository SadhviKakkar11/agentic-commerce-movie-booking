"""
Data models for the movie booking system
"""
from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime

@dataclass
class Movie:
    """Movie model"""
    id: int
    title: str
    genre: str
    rating: float
    duration: int  # in minutes
    description: str
    release_date: str
    language: str = "Hindi"
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Theatre:
    """Theatre model"""
    id: int
    name: str
    location: str
    city: str
    area: str
    capacity: int
    amenities: List[str]
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Show:
    """Show model (movie + theatre + time)"""
    id: int
    movie_id: int
    theatre_id: int
    show_time: str
    date: str
    price: float
    available_seats: int
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Booking:
    """Booking model"""
    id: str
    user_id: str
    show_id: int
    num_seats: int
    seats: List[str]  # e.g., ["A1", "A2", "B3"]
    total_price: float
    booking_date: str
    status: str  # "confirmed", "cancelled", "pending"
    payment_status: str  # "pending", "completed", "failed"
    payment_method: Optional[str] = None
    points_redeemed: int = 0
    discount_amount: float = 0.0
    final_amount: Optional[float] = None
    transaction_id: Optional[str] = None
    
    def to_dict(self):
        data = asdict(self)
        data['booking_date'] = str(self.booking_date)
        return data
