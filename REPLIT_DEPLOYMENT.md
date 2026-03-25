# Deploying to Replit

This guide will help you deploy your Movie Ticket Booking Agent to Replit.

## Prerequisites

- A free [Replit account](https://replit.com)
- Your AWS Bedrock credentials (from `.env.example`)

## Step-by-Step Deployment

### 1. Upload Code to Replit

**Option A: Direct Upload (Easiest)**

1. Go to [replit.com](https://replit.com)
2. Click **"+ Create"** or **"Create Replit"**
3. Select **"Import from GitHub"** or **"Upload Files"**
4. Upload your entire project folder
5. Replit will automatically detect `requirements.txt`

**Option B: GitHub Integration**

1. Push your code to GitHub
2. Go to [replit.com](https://replit.com)
3. Click **"+ Create"**
4. Select **"Import from GitHub"**
5. Paste your GitHub repository URL
6. Click **"Import"**

**Option C: Use Replit CLI**

```bash
# Install Replit CLI globally
pip install replit

# From your project directory
replit create my-movie-booking-agent
```

### 2. Configure Environment Variables

1. In Replit, go to the **Secrets** tab (lock icon)
2. Add these environment variables:

```
USE_BEDROCK=True
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
AWS_ACCESS_KEY_ID=<your key from .env>
AWS_SECRET_ACCESS_KEY=<your secret from .env>
BACKEND_URL=http://localhost:5000
DEBUG=True
ENABLE_RECOMMENDATIONS=True
TRACK_USER_PREFERENCES=True
```

**⚠️ Secure Your Credentials:**
- Do NOT commit `.env` file
- Use Replit Secrets for all sensitive data
- Rotate AWS keys periodically

### 3. Install Dependencies

Replit automatically installs from `requirements.txt`. If needed, manually install:

```bash
pip install -r requirements.txt
```

### 4. Run the Application

1. Click **"Run"** button (or Ctrl + Enter)
2. The system will:
   - Install dependencies from `requirements.txt`
   - Start backend API on port 5000
   - Start web UI on port 5001
3. Replit will show a **"Webview"** tab with your app

### 5. Access Your App

- Click the **"Webview"** tab to see the live UI
- Share the URL with others (Replit generates a public URL)
- Use the chat interface to:
  - Search for movies
  - Book tickets
  - Get AI recommendations

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'backend'"

**Solution:**
1. Make sure all files are uploaded to the same directory
2. Check that `__init__.py` files exist in `backend/`, `agent/`, and `examples/` directories
3. Verify directory structure matches:
```
.
├── main.py (entry point)
├── requirements.txt
├── .env (with your credentials)
├── backend/
│   ├── __init__.py
│   ├── app.py
│   ├── models.py
│   ├── database.py
│   └── recommendations.py
├── agent/
│   ├── __init__.py
│   ├── agent.py
│   ├── config.py
│   ├── prompts.py
│   └── tools.py
└── examples/
    ├── __init__.py
    └── web_ui.py
```

### Issue: "AWS Authentication Failed"

**Solution:**
1. Double-check your credentials in Replit Secrets
2. Verify AWS credentials are valid in AWS Console
3. Ensure your AWS user has Bedrock permissions
4. Check AWS_REGION is correct (us-east-1, us-west-2, or eu-central-1)

### Issue: Connection Refused on Port 5000/5001

**Solution:**
- Replit automatically manages ports
- If errors occur, clear cache: Settings → Storage → Clear
- Restart the Replit

### Issue: Out of Memory

**Solution:**
- Replit free tier has memory limits
- Use paid tier if experiencing crashes
- Kill other browser tabs using the Replit

## File Structure for Replit

```
movie-ticket-booking-agent/
├── .replit                           # Replit configuration
├── main.py                           # Replit entry point
├── requirements.txt                  # Python dependencies
├── .env                              # Your AWS credentials (SECRET!)
├── .gitignore                        # Prevents .env from being committed
├── README.md
├── QUICK_START.md
├── IMPLEMENTATION_GUIDE.md
├── BEDROCK_SETUP_SUMMARY.md
├── backend/
│   ├── __init__.py
│   ├── app.py
│   ├── models.py
│   ├── database.py
│   └── recommendations.py
├── agent/
│   ├── __init__.py
│   ├── agent.py
│   ├── config.py
│   ├── prompts.py
│   └── tools.py
└── examples/
    ├── __init__.py
    └── web_ui.py
```

## Features Available on Replit

✅ Movie Search & Filtering  
✅ Theatre & Show Information  
✅ Ticket Booking with Claude AI  
✅ AI Recommendations  
✅ User Preference Tracking  
✅ Real-time Chat Interface  
✅ Personalized Suggestions  

## Performance Notes

- First run may take 30-60 seconds as dependencies install
- Subsequent runs are faster
- Replit auto-hibernates after inactivity (free tier)
- Pro tier keeps app always running

## Next Steps

1. ✅ Deploy to Replit
2. 📧 Test the booking workflow
3. 🎯 Customize recommendations
4. 📊 Monitor API usage
5. 🚀 Scale to paid tier if needed

## Need Help?

- **Replit Docs:** https://docs.replit.com/
- **AWS Bedrock Docs:** https://docs.aws.amazon.com/bedrock/
- **Claude API:** https://docs.anthropic.com/

Good luck! 🎬🎫
