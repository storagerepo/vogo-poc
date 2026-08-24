"""Simple, dependency-free ID generators for mock records."""
import random
import string
import time


def _suffix(n: int = 5) -> str:
    return "".join(random.choices(string.digits, k=n))


def new_id(prefix: str) -> str:
    """e.g. new_id('LEAD') -> 'LEAD-174000-83921'"""
    return f"{prefix}-{int(time.time())}-{_suffix()}"


def new_lead_id() -> str:
    return new_id("LEAD")


def new_booking_id() -> str:
    return new_id("TDB")


def new_appointment_id() -> str:
    return new_id("APT")


def new_finance_lead_id() -> str:
    return new_id("FIN")


def new_idempotency_key(*parts: str) -> str:
    """Generate a deterministic idempotency key from session/request parts.

    Used to prevent duplicate finance leads when the same request is
    submitted multiple times (e.g. voice retry, duplicate tool call).
    """
    import hashlib

    raw = "|".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

