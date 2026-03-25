"""
CineBot — end-to-end booking example (actual use case)

Simulates Ram Kumar's full journey:
  1. Ram tells the bot he wants to book tickets for Dhurandhar
  2. CineBot fetches his preferences, picks the best PVR Recliner show at 2 PM
  3. Ram confirms
  4. CineBot books the seats and immediately shows payment options
     (his 1000 ICICI Bank points vs. the best available card offer)
  5. Ram chooses a payment option
  6. CineBot processes payment and shows booking confirmation

Run:
    python -m examples.simple_booking
    (make sure BACKEND_URL and AWS credentials are set, or the combined server is running)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.agent import MovieBookingAgent


def run():
    # Ram's pre-seeded profile: PVR, Recliner, 1-3 PM, Andheri/Bandra/Sion, ICICI 1000 pts
    agent = MovieBookingAgent(user_id="user_ram_001")

    print("=" * 65)
    print("  🎬  CineBot — Agentic Movie Booking Demo")
    print("  User : Ram Kumar (user_ram_001)")
    print("  AI   : Claude 3.5 Sonnet via AWS Bedrock")
    print("=" * 65)

    # ── The actual conversation flow ─────────────────────────────────────
    turns = [
        # Step 1: Ram initiates — natural language, date-anchored
        "I want to book 2 tickets for Dhurandhar this Sunday afternoon",

        # Step 3: Ram confirms CineBot's single recommendation
        "Yes, go ahead and reserve those seats",

        # Step 5: Ram chooses payment option after CineBot presents both
        "Option 1 — use my ICICI points",
    ]

    step_labels = [
        "Ram states his intent",
        "Ram confirms the recommendation",
        "Ram selects payment option",
    ]

    for label, message in zip(step_labels, turns):
        print(f"\n{'─'*65}")
        print(f"  👤  [{label}]")
        print(f"  Ram: {message}")
        print(f"{'─'*65}")
        print("  🤖  CineBot (thinking…)\n")
        response = agent.chat(message)
        print(response)

    print(f"\n{'='*65}")
    print("  ✅  Demo complete!")
    print(f"  Messages in session : {len(agent.conversation_history)}")
    print("=" * 65)


if __name__ == "__main__":
    run()
