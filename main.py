"""
Replit entry point - starts backend and web UI
"""
import subprocess
import os
import sys
import time

# Set environment variables for Replit
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['FLASK_ENV'] = 'production'

print("🎬 Movie Ticket Booking Agent - Starting on Replit...")
print("=" * 60)

# Start backend server in background
print("\n📡 Starting backend API server on port 5000...")
backend_process = subprocess.Popen(
    [sys.executable, '-m', 'backend.app'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait for backend to start
time.sleep(3)

# Start web UI server
print("🌐 Starting web UI on port 5001...")
print("=" * 60)
print("\n✅ Application is running!")
print("📖 Open the Replit web preview to access the app")
print("\n" + "=" * 60)

web_ui_process = subprocess.Popen(
    [sys.executable, 'examples/web_ui.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Keep processes running
web_ui_process.wait()
