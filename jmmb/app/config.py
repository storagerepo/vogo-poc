"""
Central configuration for the JMMB Voice POC.

Keeps every tunable (model name, voice, data directory) in one place so
agents never hardcode values.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "mock_data"

# ---------------------------------------------------------------------------
# Gemini Realtime (Live API) settings
# ---------------------------------------------------------------------------
GEMINI_REALTIME_MODEL = os.getenv("GEMINI_REALTIME_MODEL", "gemini-3.1-flash-live-preview")
GEMINI_VOICE = os.getenv("GEMINI_VOICE", "Zephyr")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))

# ---------------------------------------------------------------------------
# Bank identity used inside prompts
# ---------------------------------------------------------------------------
BANK_NAME = "JMMB"
