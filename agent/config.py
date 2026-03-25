"""
Configuration for Claude Agent
Supports both direct Anthropic API and AWS Bedrock
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ===== API Provider Configuration =====
# Defaults to True — CodeSandbox/Codespaces deployments use AWS Bedrock.
# Set USE_BEDROCK=false and provide ANTHROPIC_API_KEY to use the direct Anthropic API instead.
USE_BEDROCK = os.getenv('USE_BEDROCK', 'True').lower() == 'true'

# ===== Direct Anthropic API Configuration =====
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')

# ===== AWS Bedrock Configuration =====
AWS_REGION = os.getenv('AWS_REGION', os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))
BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# ===== Backend Configuration =====
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:3000')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# ===== Feature Flags =====
ENABLE_RECOMMENDATIONS = os.getenv('ENABLE_RECOMMENDATIONS', 'True').lower() == 'true'
TRACK_USER_PREFERENCES = os.getenv('TRACK_USER_PREFERENCES', 'True').lower() == 'true'

# Warn (don't crash) at import time — the server must start even if secrets aren't set yet.
# Errors will surface with a clear message when the first chat message is sent.
if USE_BEDROCK:
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        print(
            "[CineBot] WARNING: AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY not set. "
            "Add them as Secrets in CodeSandbox (Env tab) and restart the task."
        )
else:
    if not ANTHROPIC_API_KEY:
        print(
            "[CineBot] WARNING: ANTHROPIC_API_KEY not set and USE_BEDROCK=false. "
            "Set ANTHROPIC_API_KEY in Secrets, or set USE_BEDROCK=true to use AWS Bedrock."
        )
