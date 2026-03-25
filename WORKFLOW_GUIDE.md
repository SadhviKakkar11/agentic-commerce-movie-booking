# Enhanced Workflow: User Preference-Driven Booking with Claude

## Overview

Your movie ticket booking system now uses an advanced 6-stage workflow that combines Claude AI with user preferences, decision modeling, and multi-step execution:

**A → B → C → D → E → F**

## Workflow Stages

### A. INTENT CAPTURE
- User describes what they want (e.g., "I want to book 2 tickets for Dhurandhar this Sunday using my reward points")
- Claude captures the intent and extracts key parameters

### B. PREFERENCE ALIGNMENT  
- Claude retrieves user's profile with historical preferences:
  - **Preferred Theatres**: PVR, BMS
  - **Preferred Seats**: Recliner, Premium
  - **Preferred Timings**: 1-3 PM (Sunday afternoon)
  - **Preferred Offers**: BOGO, Student Discount
  - **Preferred Locations**: Andheri, Bandra, Sion
  - **CC Points**: 1000 points available

### C. DATA AGGREGATION & SEARCH (Claude + API Integration)
- Claude calls `/api/recommendations/smart-search` endpoint
- Searches across multiple portals (BMS, PVR, INOX, Cinepolis)
- Gathers all available options

### D. DECISION MODELING (Intelligent Recommendation)
- Claude receives scoring breakdown for each option
- System scores each show based on:
  - Portal match (0-25 points)
  - Theatre/Location match (0-20 points)
  - Seat type match (0-20 points)
  - Timing preference match (0-15 points)
  - Offer availability (0-15 points)
  - Budget alignment (0-5 points)
  
- **Example Decision**:
  > "Sunday 29-Mar-2026, 2 Recliner seats at PVR Bandra, 1-3 PM showing, for INR 1400 using 1000 CC Points + INR 400 cash"

### E. AUTHORIZATION
- Claude presents the recommendation with full breakdown
- User reviews and approves
- User specifies how many CC points to redeem

### F. EXECUTION (Multi-step orchestration)
Three parallel operations:

1. **Reservation** - Claude reserves seats via BMS portal
2. **Points Redemption** - Claude redeems CC points from rewards database
3. **Payment Processing** - Claude processes remaining payment through gateway

All three must succeed for booking to complete.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    User (RAM)                             │
│  "Book 2 tickets using my points and reward offer"       │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────────────┐
│              Claude AI Agent                             │
│  Orchestrates entire workflow with Claude tools          │
└────────────────────┬─────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ↓                         ↓
    User Profiles           Booking Portals
    • Preferences           • BMS
    • History              • PVR
    • CC Points            • INOX
    • Bookings             • Cinepolis
        │                         
        └────────────┬────────────┘
                     ↓
        ┌────────────────────────────────┐
        │   Decision Modeling            │
        │   Score & Rank Options         │
        │   (100-point scale)            │
        └────────────┬────────────────────┘
                     │
                     ↓
        ┌────────────────────────────────┐
        │   Execution Engine             │
        │   1. Reserve Seats             │
        │   2. Redeem CC Points          │
        │   3. Process Payment           │
        └────────────────────────────────┘
```

## New API Endpoints

### Get User Profile
```bash
GET /api/users/<user_id>/profile
```
Returns user preferences, booking history, and CC points balance.

### Smart Search with Preferences
```bash
POST /api/recommendations/smart-search
{
  "user_id": "user_ram_001",
  "movie_title": "Dhurandhar",
  "location": "Delhi",
  "date": "2026-03-29"
}
```
Returns:
- All available shows across portals
- Best recommendation with scoring breakdown
- User's current preferences
- Available CC points

### Execute Smart Booking
```bash
POST /api/bookings/execute-smart-booking
{
  "user_id": "user_ram_001",
  "show_id": "BMS_show_001",
  "num_seats": 2,
  "portal": "BMS",
  "cc_points_to_redeem": 1000
}
```
Executes all three steps:
1. Reserve seats
2. Redeem points
3. Process payment

Response includes:
- Reservation ID
- Transaction ID
- Amount paid breakdown
- Total cost

## Sample User Profile (RAM)

```python
User ID: user_ram_001
Name: Ram Kumar
Email: ram@example.com
Phone: 9876543210

Preferences:
├── Preferred Theatres: ["PVR", "BMS"]
├── Preferred Seats: ["Recliner", "Premium"]
├── Preferred Timings: ["1-3 PM", "Evening"]
├── Preferred Offers: ["BOGO", "Student Discount"]
├── Preferred Locations: ["Andheri", "Bandra", "Sion"]
├── Preferred Genres: ["Action", "Comedy"]
└── Average Budget: Rs. 1500

Account:
├── CC Points: 1000
├── Total Spent: Rs. 5000
├── Bookings Count: 10
└── Member Since: March 2024
```

## Scoring Examples

### Option 1: PVR Andheri, 1:30 PM, Recliner
```
Portal Match (PVR): 25 points ✓ (Preferred)
Theatre Match (Andheri): 20 points ✓ (Andheri is preferred location)
Seat Match (Recliner): 20 points ✓ (Preferred)
Timing Match (1:30 PM): 15 points ✓ (Falls in 1-3 PM window)
Offer Match (BOGO): 15 points ✓ (Preferred offer)
Budget Match (Rs. 350): 5 points ✓ (Within budget)
─────────────────────════════════════
TOTAL SCORE: 100/100 ★★★★★ PERFECT!
```

### Option 2: INOX Sion, 7:30 PM, Standard
```
Portal Match (INOX): 10 points (Not preferred)
Theatre Match (Sion): 20 points ✓ (Sion is preferred location)
Seat Match (Standard): 10 points (Not preferred)
Timing Match (7:30 PM): 0 points (Evening, but not in preferred window)
Offer Match (None): 5 points (No offer)
Budget Match (Rs. 250): 5 points ✓ (Below budget)
─────────────────────════════════════
TOTAL SCORE: 50/100 ★★ ACCEPTABLE
```

## Claude's Role in the Workflow

### 1. Intent Understanding
```
User: "Book 2 tickets for Dhurandhar Sunday afternoon using my points"
Claude extracts: movie="Dhurandhar", date="Sunday", time="afternoon", num_seats=2, use_points=true
```

### 2. Preference-Aware Search
```
Claude thinks:
"RAM prefers PVR, Recliner seats, Sunday 1-3 PM, and has BOGO offers.
Let me search for shows matching these criteria."
→ Calls: /api/recommendations/smart-search
```

### 3. Recommendation Explanation
```
Claude to user:
"Based on your preferences, I recommend:
• Sunday 29-Mar, 1:30 PM at PVR Andheri
• 2 Recliner seats (Your preferred type!)
• Rs. 700 total (Rs. 350 per seat)
• BOGO offer available!

I can pay Rs. 400 from your 1000 CC points and Rs. 300 from your card.
Shall I proceed?"
```

### 4. Multi-Step Execution
```
Claude (on approval) executes:
1. Reserve seats at BMS portal ✓
2. Redeem 1000 points from rewards ✓
3. Process Rs. 400 payment ✓
→ Booking Confirmed!
```

## Features

✅ **Preference Learning** - System learns from past bookings  
✅ **Smart Scoring** - 100-point scale considering 6 factors  
✅ **Multi-Portal Search** - Searches BMS, PVR, INOX, Cinepolis  
✅ **CC Rewards Integration** - Automatic point redemption  
✅ **Decision Modeling** - AI recommends best option with reasoning  
✅ **Multi-Step Execution** - Atomic transactions  
✅ **User Profiles** - Complete booking history and preferences  
✅ **Real-Time Availability** - Mock realistic portal responses  

## Testing the Workflow

### 1. Check User Profile
```bash
curl http://localhost:5000/api/users/user_ram_001/profile
```

### 2. Smart Search
```bash
curl -X POST http://localhost:5000/api/recommendations/smart-search \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_ram_001",
    "movie_title": "Dhurandhar",
    "location": "Delhi"
  }'
```

### 3. Execute Booking
```bash
curl -X POST http://localhost:5000/api/bookings/execute-smart-booking \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_ram_001",
    "show_id": "BMS_show_001",
    "num_seats": 2,
    "portal": "BMS",
    "cc_points_to_redeem": 1000
  }'
```

## Next Steps

1. ✅ Deploy to Replit
2. Test full workflow with Claude
3. Add real booking portal integrations
4. Implement user authentication
5. Add payment gateway integration
6. Deploy to production (AWS Lambda)

---

**Built with Claude AI + AWS Bedrock + Flask Backend**
