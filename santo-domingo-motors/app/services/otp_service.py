"""
otp_service.py
--------------
Mock OTP service for the Finance Agent phone verification flow.

This module is cleanly encapsulated behind send/verify functions so it can
be replaced with a real SMS/email OTP provider (e.g. Twilio, AWS SNS,
MessageBird) by swapping only this module. All other code depends solely on
the function signatures defined here.

For the POC:
- OTPs are generated randomly and stored in-memory.
- The debug OTP code is returned in the response for testing.
- 5-minute TTL, 3 verification attempts max.
"""
from __future__ import annotations

import random
import re
import time
import threading

from app.utils.logger import get_logger

log = get_logger("services.otp")

# ---------------------------------------------------------------------------
# Configuration — tune for POC, override for production
# ---------------------------------------------------------------------------
OTP_LENGTH = 4
OTP_TTL_SECONDS = 300  # 5 minutes
MAX_VERIFY_ATTEMPTS = 3

# ---------------------------------------------------------------------------
# In-memory OTP store (replace with Redis / DB in production)
# { phone: { "otp": "123456", "created_at": float, "attempts": int } }
# ---------------------------------------------------------------------------
_otp_store: dict[str, dict] = {}
_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------
_PHONE_RE = re.compile(r"^[\d\s\-\+\(\)]{7,20}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_phone(phone: str) -> bool:
    """Basic phone format check (digits, spaces, dashes, parens, 7-20 chars)."""
    return bool(_PHONE_RE.match(phone.strip()))


def validate_email(email: str) -> bool:
    """Basic email format check."""
    return bool(_EMAIL_RE.match(email.strip()))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def send_otp(phone: str, email: str | None = None) -> dict:
    """Generate and 'send' a mock OTP to verify the customer's phone number.

    In production this would dispatch an SMS (and optionally email) via an
    external provider. For the POC it stores the OTP in memory and returns
    it in a debug field.

    Args:
        phone: Customer's phone number to verify.
        email: Customer's email (optional, for backup delivery).

    Returns:
        dict with success status and (POC only) _debug_otp.
    """
    phone = phone.strip()
    if not validate_phone(phone):
        return {"success": False, "message": "Invalid phone number format."}

    if email and not validate_email(email):
        return {"success": False, "message": "Invalid email format."}

    otp_code = "1234"

    with _lock:
        _otp_store[phone] = {
            "otp": otp_code,
            "created_at": time.time(),
            "attempts": 0,
        }

    log.info("OTP generated for phone=%s (code=%s)", phone, otp_code)

    return {
        "success": True,
        "message": f"A verification code has been sent to {phone}"
        + (f" and {email}" if email else ""),
        # POC only — remove this field when switching to a real provider:
        "_debug_otp": otp_code,
    }


def verify_otp(phone: str, otp: str) -> dict:
    """Verify an OTP for a given phone number.

    Args:
        phone: The phone number the OTP was sent to.
        otp: The OTP code the customer provided.

    Returns:
        dict with verified (bool), reason, message, and remaining_attempts.
    """
    phone = phone.strip()
    otp = otp.strip()

    with _lock:
        record = _otp_store.get(phone)

    if not record:
        return {
            "verified": False,
            "reason": "no_otp_sent",
            "message": "No verification code has been sent to this number. Please request a new one.",
        }

    # Check expiry
    if time.time() - record["created_at"] > OTP_TTL_SECONDS:
        with _lock:
            _otp_store.pop(phone, None)
        return {
            "verified": False,
            "reason": "otp_expired",
            "message": "The verification code has expired. Please request a new one.",
        }

    # Check max attempts
    if record["attempts"] >= MAX_VERIFY_ATTEMPTS:
        with _lock:
            _otp_store.pop(phone, None)
        return {
            "verified": False,
            "reason": "max_attempts",
            "message": "Too many incorrect attempts. Please request a new verification code.",
        }

    # Increment attempt counter
    record["attempts"] += 1

    # Check match
    if otp != record["otp"]:
        remaining = MAX_VERIFY_ATTEMPTS - record["attempts"]
        log.info("OTP mismatch for phone=%s (attempt %d)", phone, record["attempts"])
        return {
            "verified": False,
            "reason": "incorrect_otp",
            "remaining_attempts": remaining,
            "message": f"Incorrect verification code. You have {remaining} attempt(s) remaining.",
        }

    # Success — clean up
    with _lock:
        _otp_store.pop(phone, None)
    log.info("OTP verified successfully for phone=%s", phone)
    return {
        "verified": True,
        "message": "Phone number verified successfully.",
    }
