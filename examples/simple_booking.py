"""
Simple example: Basic movie booking flow
Run this to see the agent in action with a predefined conversation
"""
from agent.agent import MovieBookingAgent

def example_simple_booking():
    """Demonstrate a simple booking flow"""
    agent = MovieBookingAgent(user_id="user_demo_123")
    
    print("🎬 Movie Ticket Booking - Simple Example")
    print("=" * 60)
    
    # Example conversation flow
    conversation = [
        "I want to watch an action movie tomorrow evening",
        "What about the one at Downtown Cinema? Can you show me more details?",
        "Looks good! Can you book 2 tickets for me? Let's go with front row middle seats.",
    ]
    
    for i, message in enumerate(conversation, 1):
        print(f"\n📌 Step {i}")
        print(f"User: {message}")
        print("\n🤖 Claude:")
        response = agent.chat(message)
        print(response)
        print("-" * 60)
    
    # Show booking confirmation
    print("\n✅ Booking Complete!")
    print("\nConversation Summary:")
    print(f"Total messages exchanged: {len(agent.conversation_history)}")


if __name__ == "__main__":
    example_simple_booking()
