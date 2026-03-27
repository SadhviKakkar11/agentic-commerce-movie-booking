"""
Mock Booking Portals and Payment Gateway
Simulates integration with BMS, PVR, and payment systems
"""
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class BookingPortal:
    """Mock booking portal (BMS, PVR, etc.)"""
    portal_name: str
    available_shows: List[Dict] = None
    commission_rate: float = 0.05  # 5% commission
    processing_fee: float = 20.0  # Fixed processing fee in Rs.
    
    def __post_init__(self):
        if self.available_shows is None:
            self.available_shows = []

class BookingPortalManager:
    """Manages mock booking portals"""
    
    def __init__(self):
        self.portals = {
            "BMS": BookingPortal("BMS (BookMyShow)"),
            "PVR": BookingPortal("PVR"),
            "INOX": BookingPortal("INOX"),
            "Cinepolis": BookingPortal("Cinepolis")
        }
    
    def search_shows(self, portal_name: str, movie_title: str, 
                    location: str, date: str) -> List[Dict]:
        """Search shows in a specific portal"""
        if portal_name not in self.portals:
            return []
        
        # Simulate portal search results
        shows = [
            {
                "show_id": f"{portal_name}_show_001",
                "portal": portal_name,
                "movie": movie_title,
                "theatre": "PVR Andheri",
                "location": location,
                "date": date,
                "timing": "1:30 PM",
                "format": "Recliner",
                "price": 600,
                "available_seats": 45,
                "offer": "BOGO"
            },
            {
                "show_id": f"{portal_name}_show_002",
                "portal": portal_name,
                "movie": movie_title,
                "theatre": "PVR Bandra",
                "location": location,
                "date": date,
                "timing": "4:00 PM",
                "format": "Premium",
                "price": 400,
                "available_seats": 60,
                "offer": "Student Discount"
            },
            {
                "show_id": f"{portal_name}_show_003",
                "portal": portal_name,
                "movie": movie_title,
                "theatre": "PVR Sion",
                "location": location,
                "date": date,
                "timing": "7:30 PM",
                "format": "Standard",
                "price": 250,
                "available_seats": 30,
                "offer": "None"
            }
        ]
        
        return shows
    
    def reserve_seats(self, portal_name: str, show_id: str, 
                     num_seats: int) -> Dict:
        """Reserve seats in a portal"""
        if portal_name not in self.portals:
            return {"success": False, "error": "Portal not found"}
        
        # Simulate reservation
        return {
            "success": True,
            "portal": portal_name,
            "show_id": show_id,
            "seats_reserved": num_seats,
            "reservation_id": f"RES_{portal_name}_{show_id}_{datetime.now().timestamp()}",
            "reservation_valid_until": "2026-03-25T12:00:00"
        }
    
    def get_portal_for_preference(self, preferred_portals: List[str]) -> str:
        """Get best portal based on user preference"""
        for portal in preferred_portals:
            if portal in self.portals:
                return portal
        return "BMS"  # Default to BMS

class CreditCardRewardsDB:
    """Mock credit card rewards database"""
    
    def __init__(self):
        self.redemption_rate = 0.5  # 1 point = Rs. 0.5
        self.credit_card_offers = [
            {
                "card_name": "HDFC Regalia",
                "discount_percent": 12,
                "max_discount": 300
            },
            {
                "card_name": "SBI Elite",
                "discount_percent": 10,
                "max_discount": 250
            },
            {
                "card_name": "ICICI Sapphiro",
                "discount_percent": 15,
                "max_discount": 350
            },
            {
                "card_name": "Axis Ace",
                "discount_percent": 8,
                "max_discount": 200
            }
        ]
    
    def redeem_points(self, user_id: str, points: int) -> Dict:
        """Redeem CC points and deduct from user profile"""
        from .user_profiles import user_profile_manager
        amount_redeemed = points * self.redemption_rate

        # Deduct points from the user's profile
        profile = user_profile_manager.get_user_profile(user_id)
        if profile:
            profile.cc_points = max(0, profile.cc_points - points)

        return {
            "success": True,
            "user_id": user_id,
            "points_redeemed": points,
            "amount_credited": amount_redeemed,
            "remaining_points": profile.cc_points if profile else 0,
            "redemption_id": f"REDEEM_{user_id}_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat()
        }

    def get_best_credit_card_offer(self, amount: float) -> Dict:
        """Return the best available credit card offer for an amount."""
        if amount <= 0:
            return {
                "card_name": None,
                "discount_percent": 0,
                "discount_amount": 0.0,
                "final_payable": 0.0
            }

        best_offer = None
        for offer in self.credit_card_offers:
            raw_discount = amount * (offer["discount_percent"] / 100.0)
            discount_amount = min(raw_discount, offer["max_discount"])
            final_payable = max(0.0, amount - discount_amount)

            candidate = {
                "card_name": offer["card_name"],
                "discount_percent": offer["discount_percent"],
                "discount_amount": round(discount_amount, 2),
                "final_payable": round(final_payable, 2)
            }

            if not best_offer or candidate["discount_amount"] > best_offer["discount_amount"]:
                best_offer = candidate

        return best_offer

class PaymentGateway:
    """Mock payment gateway"""
    
    def __init__(self):
        self.transaction_id_counter = 10000
        self.processing_fee = 20  # Rs.
    
    def process_payment(self, user_id: str, amount: float, 
                       payment_method: str = "credit_card") -> Dict:
        """Process payment through gateway"""
        self.transaction_id_counter += 1
        
        # Simulate payment processing
        total_with_fee = amount + self.processing_fee
        
        return {
            "success": True,
            "transaction_id": f"TXN_{self.transaction_id_counter}",
            "user_id": user_id,
            "amount": amount,
            "processing_fee": self.processing_fee,
            "total_amount": total_with_fee,
            "payment_method": payment_method,
            "status": "Completed",
            "timestamp": datetime.now().isoformat()
        }

class ExecutionEngine:
    """Executes multi-step booking operations"""
    
    def __init__(self, portal_manager: BookingPortalManager,
                 rewards_db: CreditCardRewardsDB,
                 payment_gateway: PaymentGateway):
        self.portal_manager = portal_manager
        self.rewards_db = rewards_db
        self.payment_gateway = payment_gateway
    
    def execute_booking(self, user_id: str, show_id: str, num_seats: int,
                       portal: str, cc_points_to_redeem: int = 0,
                       price_per_seat: int = 600, offer: str = "None") -> Dict:
        """Execute complete booking with multiple steps"""
        
        results = {
            "steps": {},
            "success": False,
            "error": None
        }
        
        # Step 1: Reserve seats
        reservation = self.portal_manager.reserve_seats(portal, show_id, num_seats)
        results["steps"]["reservation"] = reservation
        
        if not reservation["success"]:
            results["error"] = "Failed to reserve seats"
            return results
        
        # Step 2: Redeem CC points (if any)
        amount_from_points = 0
        if cc_points_to_redeem > 0:
            redemption = self.rewards_db.redeem_points(user_id, cc_points_to_redeem)
            results["steps"]["redemption"] = redemption
            amount_from_points = redemption.get("amount_credited", 0)
        
        # Step 3: Process payment
        # Apply BOGO: every 2 seats, 1 is free (pay for ceil(num_seats / 2))
        if offer == "BOGO":
            paid_seats = (num_seats + 1) // 2
        else:
            paid_seats = num_seats
        ticket_price = price_per_seat * paid_seats
        # processing_fee is added inside process_payment — do not add it here
        amount_to_pay = max(0.0, ticket_price - amount_from_points)
        
        payment = self.payment_gateway.process_payment(user_id, amount_to_pay)
        results["steps"]["payment"] = payment
        
        if payment["success"]:
            results["success"] = True
            results["booking_summary"] = {
                "reservation_id": reservation["reservation_id"],
                "transaction_id": payment["transaction_id"],
                "num_seats": num_seats,
                "ticket_price": ticket_price,
                "points_redeemed": cc_points_to_redeem,
                "amount_from_points": amount_from_points,
                "total_paid": payment["total_amount"]
            }
        else:
            results["error"] = "Payment processing failed"
        
        return results


# Global service instances
booking_portal_manager = BookingPortalManager()
cc_rewards_db = CreditCardRewardsDB()
payment_gateway = PaymentGateway()
