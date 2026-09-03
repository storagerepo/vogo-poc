import os

from dotenv import load_dotenv

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY", ""))
GEMINI_REALTIME_MODEL = "gemini-3.1-flash-live-preview"
GEMINI_VOICE = "Charon"

AGENT_BANK_NAME = os.getenv("AGENT_BANK_NAME", "Banco López de Haro (BLH)")

