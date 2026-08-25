"""
config.py
---------
Central place for environment-driven configuration. Uses env vars only --
no secrets are hard-coded. Copy .env.example to .env and fill in real
credentials before running the worker.

This POC uses Google Gemini's realtime (speech-to-speech) model as the
single voice model for every agent -- there is no separate STT/LLM/TTS
pipeline to configure. See app/main.py.
"""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # LiveKit server connection
    LIVEKIT_URL: str = os.getenv("LIVEKIT_URL", "")
    LIVEKIT_API_KEY: str = os.getenv("LIVEKIT_API_KEY", "")
    LIVEKIT_API_SECRET: str = os.getenv("LIVEKIT_API_SECRET", "")

    # Google Gemini Realtime (speech-to-speech) model
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    GEMINI_REALTIME_MODEL: str = "gemini-3.1-flash-live-preview"
    GEMINI_VOICE: str = "Kore"
    GEMINI_TEMPERATURE: float = 0.3

    DEALERSHIP_NAME: str = "Santo Domingo Motors"


settings = Settings()
