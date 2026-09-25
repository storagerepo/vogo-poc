"""
Shared helpers for the Country Club POC tools.

All "business data" for this POC is mocked as static JSON files under /mock_data.
No database, ORM, or external API is used - this keeps the POC simple and
makes it trivial to swap the JSON layer for a real API/DB later without
touching the agent or tool signatures.
"""

from __future__ import annotations

import json
import threading
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "mock_data"

_lock = threading.Lock()


@lru_cache(maxsize=None)
def load_json(filename: str) -> dict:
    """Load and cache a JSON data file from the /mock_data directory.

    Cached with lru_cache since the POC data is static for the lifetime of
    the process; avoids re-reading disk on every tool call.

    NOTE: Do NOT use this for reservations.json — that file is mutable.
    Use load_reservations_data() / save_reservations_data() instead.
    """
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Mock data file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize(text: str) -> str:
    """Lowercase + strip helper for loose matching against user speech."""
    return (text or "").strip().lower()


# ---- Mutable data helpers (for reservations) ----

_reservations_data: dict[str, Any] | None = None


def load_reservations_data() -> dict[str, Any]:
    """Load reservations.json into memory. Not cached via lru_cache because
    the reservation data is mutable (we write back after each booking)."""
    global _reservations_data
    with _lock:
        if _reservations_data is None:
            path = DATA_DIR / "reservations.json"
            if not path.exists():
                _reservations_data = {"availability": [], "reservations": [], "next_id": 10001}
            else:
                with path.open("r", encoding="utf-8") as f:
                    _reservations_data = json.load(f)
        return _reservations_data


def save_reservations_data() -> None:
    """Persist the in-memory reservations data back to disk so state is
    visible if you inspect the JSON file during/after a demo, and survives
    a worker restart."""
    with _lock:
        if _reservations_data is not None:
            path = DATA_DIR / "reservations.json"
            with path.open("w", encoding="utf-8") as f:
                json.dump(_reservations_data, f, ensure_ascii=False, indent=2)
