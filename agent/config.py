"""
Configuration for Claude Agent
Supports both direct Anthropic API and AWS Bedrock
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ===== API Provider Configuration =====
USE_BEDROCK = os.getenv('USE_BEDROCK', 'False').lower() == 'true'

# ===== Direct Anthropic API Configuration =====
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')

# ===== AWS Bedrock Configuration =====
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# ===== Backend Configuration =====
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5000')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# ===== Feature Flags =====
ENABLE_RECOMMENDATIONS = os.getenv('ENABLE_RECOMMENDATIONS', 'True').lower() == 'true'
TRACK_USER_PREFERENCES = os.getenv('TRACK_USER_PREFERENCES', 'True').lower() == 'true'

# Validate configuration
if USE_BEDROCK:
    if not AWS_REGION or not BEDROCK_MODEL_ID:
        raise ValueError(
            "Bedrock configuration incomplete. "
            "Please set AWS_REGION and BEDROCK_MODEL_ID in .env"
        )
else:
    if not ANTHROPIC_API_KEY:
        raise ValueError(
            "Anthropic API key not found. "
            "Please set ANTHROPIC_API_KEY in .env or set USE_BEDROCK=True"
        )
