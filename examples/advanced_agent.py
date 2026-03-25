"""
Advanced example: Complex multi-turn conversation with various scenarios
"""
from agent.agent import MovieBookingAgent

def example_advanced_scenarios():
    """Demonstrate advanced booking scenarios"""
    agent = MovieBookingAgent(user_id="user_advanced_456")
    
    print("🎬 Movie Ticket Booking - Advanced Examples")
    print("=" * 70)
    
    # Scenario 1: Filtered Search
    print("\n\n📍 SCENARIO 1: Filtered Movie Search")
    print("=" * 70)
    print("User wants a comedy movie with good rating")
    response = agent.chat("Find me a comedy movie with rating above 4.0")
    print(f"Assistant: {response}\n")
    
    # Scenario 2: Location-based search
    print("\n\n📍 SCENARIO 2: Location-Based Theatre Search")
    print("=" * 70)
    print("User wants theatres in a specific city")
    response = agent.chat("What theatres do you have in Los Angeles?")
    print(f"Assistant: {response}\n")
    
    # Scenario 3: Complex booking request
    print("\n\n📍 SCENARIO 3: Complex Booking with Requirements")
    print("=" * 70)
    print("User has specific requirements for booking")
    response = agent.chat(
        "I want to watch a sci-fi movie at a premium theatre in New York tomorrow afternoon. "
        "Budget is $20 per ticket. Book 3 seats if available."
    )
    print(f"Assistant: {response}\n")
    
    # Scenario 4: Follow-up questions
    print("\n\n📍 SCENARIO 4: Follow-up Refinements")
    print("=" * 70)
    print("User refines their search")
    response = agent.chat("Which one would you recommend and why?")
    print(f"Assistant: {response}\n")
    
    # Scenario 5: View bookings
    print("\n\n📍 SCENARIO 5: View Past Bookings")
    print("=" * 70)
    print("User checks their bookings")
    response = agent.chat("Can you show me all my existing bookings?")
    print(f"Assistant: {response}\n")
    
    print("\n" + "=" * 70)
    print("✅ Advanced Examples Complete!")
    print(f"Total conversation turns: {len(agent.conversation_history)}")


if __name__ == "__main__":
    example_advanced_scenarios()
