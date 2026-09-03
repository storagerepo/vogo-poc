"""SessionUserData carries customer state across the LiveKit session."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SessionUserData:
    name: str | None = None
    phone: str | None = None
    verified: bool = False
