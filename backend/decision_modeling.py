"""
Decision Modeling and Scoring System
Recommends best booking option based on user preferences
"""
from typing import Dict, List, Optional
from backend.user_profiles import UserPreferences

class BookingOptionScorer:
    """Scores and ranks booking options based on user preferences"""
    
    @staticmethod
    def score_option(show: Dict, preferences: UserPreferences) -> Dict:
        """
        Score a booking option based on user preferences
        Returns score with breakdown
        """
        score = {
            "option": show,
            "total_score": 0,
            "breakdown": {}
        }
        
        # 1. Portal preference match (0-25 points)
        portal_score = BookingOptionScorer._score_portal(
            show.get("portal", ""), 
            preferences.preferred_theatres
        )
        score["breakdown"]["portal_match"] = portal_score
        score["total_score"] += portal_score
        
        # 2. Theatre preference match (0-20 points)
        theatre_score = BookingOptionScorer._score_theatre(
            show.get("theatre", ""),
            preferences.preferred_locations
        )
        score["breakdown"]["theatre_match"] = theatre_score
        score["total_score"] += theatre_score
        
        # 3. Seat type preference match (0-20 points)
        seat_score = BookingOptionScorer._score_seat_type(
            show.get("format", ""),
            preferences.preferred_seat_types
        )
        score["breakdown"]["seat_match"] = seat_score
        score["total_score"] += seat_score
        
        # 4. Timing preference match (0-15 points)
        timing_score = BookingOptionScorer._score_timing(
            show.get("timing", ""),
            preferences.preferred_timings
        )
        score["breakdown"]["timing_match"] = timing_score
        score["total_score"] += timing_score
        
        # 5. Offer match (0-15 points)
        offer_score = BookingOptionScorer._score_offer(
            show.get("offer", ""),
            preferences.preferred_offers
        )
        score["breakdown"]["offer_match"] = offer_score
        score["total_score"] += offer_score
        
        # 6. Budget alignment (0-5 points)
        budget_score = BookingOptionScorer._score_budget(
            show.get("price", 0),
            preferences.average_budget
        )
        score["breakdown"]["budget_alignment"] = budget_score
        score["total_score"] += budget_score
        
        return score
    
    @staticmethod
    def _score_portal(portal: str, preferred: List[str]) -> int:
        """Score based on portal preference (0-25)"""
        if not preferred:
            return 15
        if portal in preferred:
            return 25
        return 10
    
    @staticmethod
    def _score_theatre(theatre: str, preferred_locations: List[str]) -> int:
        """Score based on theatre/location preference (0-20)"""
        if not preferred_locations:
            return 12
        for location in preferred_locations:
            if location.lower() in theatre.lower():
                return 20
        return 8
    
    @staticmethod
    def _score_seat_type(seat_format: str, preferred_seats: List[str]) -> int:
        """Score based on seat type preference (0-20)"""
        if not preferred_seats:
            return 12
        if seat_format in preferred_seats:
            return 20
        return 10
    
    @staticmethod
    def _score_timing(timing: str, preferred_timings: List[str]) -> int:
        """Score based on timing preference (0-15)"""
        if not preferred_timings:
            return 9
        # Extract hour from timing (e.g., "1:30 PM" → 1)
        timing_hour = int(timing.split(":")[0])
        
        for pref_timing in preferred_timings:
            if "1-3 PM" in pref_timing and 1 <= timing_hour <= 3:
                return 15
            elif "Evening" in pref_timing and 4 <= timing_hour <= 7:
                return 15
            elif "Night" in pref_timing and timing_hour >= 8:
                return 15
        return 5
    
    @staticmethod
    def _score_offer(offer: str, preferred_offers: List[str]) -> int:
        """Score based on offer preference (0-15)"""
        if offer == "None" or not offer:
            return 5
        if not preferred_offers:
            return 10
        if any(pref in offer for pref in preferred_offers):
            return 15
        return 8
    
    @staticmethod
    def _score_budget(price: float, avg_budget: float) -> int:
        """Score based on budget alignment (0-5)"""
        if avg_budget == 0:
            return 3
        ratio = price / avg_budget
        if 0.8 <= ratio <= 1.2:
            return 5
        elif 0.6 <= ratio <= 1.4:
            return 3
        else:
            return 1

class DecisionModeler:
    """Recommends best booking option based on user preferences"""
    
    @staticmethod
    def recommend_best_option(shows: List[Dict], 
                             preferences: UserPreferences) -> Optional[Dict]:
        """
        Evaluate all shows and recommend the best option
        """
        if not shows:
            return None
        
        # Score all options
        scored_options = []
        for show in shows:
            scored = BookingOptionScorer.score_option(show, preferences)
            scored_options.append(scored)
        
        # Sort by score (highest first)
        scored_options.sort(key=lambda x: x["total_score"], reverse=True)
        
        # Return top option with reasoning
        best = scored_options[0]
        best["reasoning"] = DecisionModeler._generate_reasoning(best)
        
        return best
    
    @staticmethod
    def _generate_reasoning(scored_option: Dict) -> str:
        """Generate human-readable reasoning for recommendation"""
        option = scored_option["option"]
        breakdown = scored_option["breakdown"]
        score = scored_option["total_score"]
        
        reasons = []
        
        # Find top 3 scoring factors
        top_factors = sorted(
            breakdown.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        for factor, points in top_factors:
            if points > 0:
                factor_name = factor.replace("_", " ").title()
                reasons.append(f"{factor_name}: +{points}")
        
        reasoning = f"""
Best Option (Score: {score}/100):
• Theatre: {option.get('theatre')} ({option.get('location')})
• Timing: {option.get('timing')}
• Seats: {option.get('format')} Format
• Price: Rs. {option.get('price')}
• Offer: {option.get('offer')}

Why this option:
{chr(10).join('• ' + r for r in reasons)}
"""
        return reasoning.strip()

class BookingRecommender:
    """High-level recommendation engine"""
    
    def __init__(self, scorer: BookingOptionScorer = None):
        self.scorer = scorer or BookingOptionScorer()
    
    def get_recommendation(self, shows: List[Dict], 
                          preferences: UserPreferences) -> Dict:
        """Get best booking recommendation with reasoning"""
        best_option = DecisionModeler.recommend_best_option(shows, preferences)
        
        if not best_option:
            return {"success": False, "error": "No shows available"}
        
        return {
            "success": True,
            "recommended_show": best_option["option"],
            "score": best_option["total_score"],
            "reasoning": best_option["reasoning"],
            "breakdown": best_option["breakdown"]
        }
