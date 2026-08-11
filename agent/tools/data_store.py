"""
data_store.py

A tiny in-memory / file-backed "database" over the mock JSON fixtures in
/mock_data. This stands in for Vogo's real backend & partner APIs during
the POC (see Section 16 of the plan for what gets swapped in later).

All functions here are plain Python — no LiveKit / Gemini imports — so
they can be unit tested independently of the voice stack.
"""

from __future__ import annotations

import json
import random
import string
import uuid
from datetime import datetime, date
from pathlib import Path
from threading import Lock
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "mock_data"
PROPERTIES_PATH = DATA_DIR / "properties.json"
BOOKINGS_PATH = DATA_DIR / "bookings.json"
USERS_PATH = DATA_DIR / "users.json"
TICKETS_PATH = DATA_DIR / "tickets.json"  # created at runtime

_lock = Lock()


def _load(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, "r") as f:
        return json.load(f)


def _save(path: Path, data: list[dict[str, Any]]) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Properties / search
# ---------------------------------------------------------------------------

def search_stays(
    destination: str | None = None,
    check_in: str | None = None,
    check_out: str | None = None,
    guests: int | None = None,
    budget_tier: str | None = None,
    property_type: str | None = None,
    beachfront_only: bool = False,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Search mocked properties by loose criteria. Returns top matches
    sorted by rating. Never raises on empty results — returns []."""
    properties = _load(PROPERTIES_PATH)
    results = []

    dest = (destination or "").strip().lower()

    for p in properties:
        if dest and dest not in p["city"].lower() and dest not in p["area"].lower():
            continue
        if guests and p["max_guests"] < guests:
            continue
        if budget_tier and p["price_tier"].lower() != budget_tier.strip().lower():
            continue
        if property_type and property_type.strip().lower() not in p["type"].lower():
            continue
        if beachfront_only and not p["beachfront"]:
            continue
        results.append(p)

    results.sort(key=lambda p: p["rating"], reverse=True)
    return results[:limit]


def get_stay_details(property_id: str) -> dict[str, Any] | None:
    properties = _load(PROPERTIES_PATH)
    for p in properties:
        if p["property_id"].lower() == property_id.strip().lower():
            return p
    return None


def check_availability(
    property_id: str,
    check_in: str,
    check_out: str,
    guests: int,
) -> dict[str, Any]:
    """POC-simplified availability check. Since there is no real
    inventory/calendar, we deterministically simulate availability from
    the property_id + dates so demo runs are repeatable, and always
    respect the max_guests cap (a real capacity constraint)."""
    prop = get_stay_details(property_id)
    if prop is None:
        return {"available": False, "reason": "Property not found"}

    if guests > prop["max_guests"]:
        return {
            "available": False,
            "reason": f"Property sleeps up to {prop['max_guests']} guests",
        }

    seed = f"{property_id}:{check_in}:{check_out}"
    rng = random.Random(seed)
    available = rng.random() > 0.12  # ~88% available, occasionally sold out for realism

    nights = _nights_between(check_in, check_out)
    total = prop["price_per_night_usd"] * max(nights, 1) if nights else None

    return {
        "available": available,
        "property_id": property_id,
        "check_in": check_in,
        "check_out": check_out,
        "nights": nights,
        "price_per_night_usd": prop["price_per_night_usd"],
        "price_total_usd": total,
        "reason": None if available else "No rooms left for those dates in this mock inventory",
    }


def _nights_between(check_in: str, check_out: str) -> int | None:
    try:
        d1 = datetime.strptime(check_in, "%Y-%m-%d").date()
        d2 = datetime.strptime(check_out, "%Y-%m-%d").date()
        delta = (d2 - d1).days
        return delta if delta > 0 else None
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------

def create_booking(
    property_id: str,
    check_in: str,
    check_out: str,
    guests: int,
    guest_name: str,
    contact: str,
) -> dict[str, Any]:
    """Create a mock booking. This is a state-changing action — the agent
    must have already gotten explicit verbal confirmation before calling
    this (see guardrail #5 in instructions.py)."""
    prop = get_stay_details(property_id)
    if prop is None:
        return {"success": False, "error": "Property not found"}

    avail = check_availability(property_id, check_in, check_out, guests)
    if not avail["available"]:
        return {"success": False, "error": avail.get("reason", "Not available")}

    with _lock:
        bookings = _load(BOOKINGS_PATH)
        booking_id = f"BK{len(bookings) + 1:04d}-{uuid.uuid4().hex[:4].upper()}"
        confirmation_code = "VG" + "".join(random.choices(string.digits, k=5))

        new_booking = {
            "booking_id": booking_id,
            "confirmation_code": confirmation_code,
            "guest_name": guest_name,
            "email": contact,
            "property_id": property_id,
            "property_name": prop["name"],
            "city": prop["city"],
            "check_in": check_in,
            "nights": avail["nights"],
            "guests": guests,
            "status": "confirmed",
            "price_total_usd": avail["price_total_usd"],
            "has_open_issue": False,
            "issue_notes": None,
        }
        bookings.append(new_booking)
        _save(BOOKINGS_PATH, bookings)

    return {"success": True, "booking": new_booking}


def get_booking_status(
    confirmation_code: str | None = None,
    guest_name: str | None = None,
    email: str | None = None,
) -> list[dict[str, Any]]:
    """Look up bookings by confirmation code, name, or email. Returns a
    list because a name lookup could match more than one booking — the
    agent should disambiguate with the caller rather than guessing."""
    bookings = _load(BOOKINGS_PATH)
    matches = []

    for b in bookings:
        if confirmation_code and b["confirmation_code"].lower() == confirmation_code.strip().lower():
            matches.append(b)
        elif guest_name and guest_name.strip().lower() in b["guest_name"].lower():
            matches.append(b)
        elif email and b["email"].lower() == email.strip().lower():
            matches.append(b)

    return matches


def modify_or_cancel_booking(booking_id: str, action: str) -> dict[str, Any]:
    """action: 'cancel' or 'modify' (modify is stubbed for POC — real
    date/room changes would need re-running availability + repricing)."""
    with _lock:
        bookings = _load(BOOKINGS_PATH)
        for b in bookings:
            if b["booking_id"].lower() == booking_id.strip().lower():
                if action == "cancel":
                    b["status"] = "cancelled"
                    _save(BOOKINGS_PATH, bookings)
                    return {"success": True, "booking": b}
                elif action == "modify":
                    return {
                        "success": False,
                        "error": "Modifications aren't supported in this POC — "
                                 "escalate to a human for date/room changes.",
                    }
                else:
                    return {"success": False, "error": f"Unknown action '{action}'"}
        return {"success": False, "error": "Booking not found"}


# ---------------------------------------------------------------------------
# Issues / escalation
# ---------------------------------------------------------------------------

def report_issue(booking_id: str, issue_type: str, description: str) -> dict[str, Any]:
    with _lock:
        tickets = _load(TICKETS_PATH)
        ticket_id = f"TCK{len(tickets) + 1:04d}-{uuid.uuid4().hex[:4].upper()}"
        ticket = {
            "ticket_id": ticket_id,
            "booking_id": booking_id,
            "issue_type": issue_type,
            "description": description,
            "status": "open",
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        tickets.append(ticket)
        _save(TICKETS_PATH, tickets)

    return {"success": True, "ticket": ticket}


def escalate_to_human(reason: str, urgency: str = "normal", booking_id: str | None = None) -> dict[str, Any]:
    """Stub for handing off to a human agent path. In production this
    would page a live support queue; for the POC it just logs the
    escalation and returns a reference so Aria can read it back."""
    with _lock:
        tickets = _load(TICKETS_PATH)
        escalation_id = f"ESC{len(tickets) + 1:04d}-{uuid.uuid4().hex[:4].upper()}"
        record = {
            "ticket_id": escalation_id,
            "type": "escalation",
            "booking_id": booking_id,
            "reason": reason,
            "urgency": urgency,
            "status": "handed_off",
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        tickets.append(record)
        _save(TICKETS_PATH, tickets)

    return {"success": True, "escalation_id": escalation_id}


# ---------------------------------------------------------------------------
# Mock OTP verification (POC only — no real SMS/email)
# ---------------------------------------------------------------------------

_otp_store: dict[str, dict[str, Any]] = {}  # keyed by contact


def send_mock_otp(contact: str) -> dict[str, Any]:
    """Generate a 4-digit OTP, store it against *contact* with a 5-min expiry,
    and print it to the console for POC testing. No real SMS/email is sent."""
    from datetime import timedelta

    otp = "1234"
    _otp_store[contact] = {
        "otp": otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=5),
        "attempts": 0,
    }
    print(f"[MOCK OTP] {contact} -> {otp}")
    return {"success": True, "message": f"OTP sent to {contact}"}


def verify_mock_otp(contact: str, otp: str) -> dict[str, Any]:
    """Check the OTP the user read back. Returns verified: true/false.
    Max 3 incorrect attempts; expires after 5 minutes."""
    entry = _otp_store.get(contact)

    if entry is None:
        return {"verified": False, "reason": "No OTP found for this contact. Please request a new one."}

    if datetime.utcnow() > entry["expires_at"]:
        del _otp_store[contact]
        return {"verified": False, "reason": "OTP has expired. Please request a new one."}

    if entry["attempts"] >= 3:
        del _otp_store[contact]
        return {"verified": False, "reason": "Too many incorrect attempts. Please request a new OTP."}

    if otp.strip() == entry["otp"]:
        del _otp_store[contact]
        return {"verified": True}

    entry["attempts"] += 1
    remaining = 3 - entry["attempts"]
    return {"verified": False, "reason": f"Incorrect OTP. {remaining} attempt(s) remaining."}
