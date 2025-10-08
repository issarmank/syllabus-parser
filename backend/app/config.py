# app/config.py
from dotenv import load_dotenv
import os

# load_dotenv() will load from .env file if it exists (local dev)
# On Vercel, it won't find a .env file, but that's fine because
# environment variables are injected directly into the system
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Strip whitespace if key exists
if OPENAI_API_KEY:
    OPENAI_API_KEY = OPENAI_API_KEY.strip()
    
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

# Debug logging (will appear in Vercel logs)
if OPENAI_API_KEY:
    print(f"✓ OPENAI_API_KEY loaded (length: {len(OPENAI_API_KEY)})")
    print(f"✓ First 7 chars: {OPENAI_API_KEY[:7]}")
    print(f"✓ Last 4 chars: ...{OPENAI_API_KEY[-4:]}")
    print(f"✓ Has whitespace: {OPENAI_API_KEY != OPENAI_API_KEY.strip()}")
    print(f"✓ Type: {type(OPENAI_API_KEY)}")
else:
    print("✗ OPENAI_API_KEY not found in environment variables")