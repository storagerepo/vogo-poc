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

    # NOTE: Gemini's realtime/live model ids change fairly often. Check
    # LiveKit's Google plugin docs / Google AI Studio for the current id
    # before running the POC and update this default (or the .env value)
    # accordingly.
    GEMINI_REALTIME_MODEL: str = os.getenv("GEMINI_REALTIME_MODEL", "gemini-2.0-flash-live-001")
    GEMINI_VOICE: str = os.getenv("GEMINI_VOICE", "Puck")
    GEMINI_TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))

    DEALERSHIP_NAME: str = os.getenv("DEALERSHIP_NAME", "Santo Domingo Motors")


settings = Settings()
