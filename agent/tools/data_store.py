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
ADD_ONS_PATH = DATA_DIR / "add_ons.json"

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


# ---------------------------------------------------------------------------
# Add-ons — loading, validation, pricing
# ---------------------------------------------------------------------------

VALID_CATEGORIES = {"transportation", "food_dining"}
VALID_PRICING_TYPES = {"per_stay", "per_day", "per_guest", "per_guest_per_day"}


def _load_add_ons() -> list[dict[str, Any]]:
    """Load the add-on configuration from mock_data/add_ons.json."""
    return _load(ADD_ONS_PATH)


def get_available_add_ons(category: str | None = None) -> list[dict[str, Any]]:
    """Return add-ons that are marked available, optionally filtered by category."""
    add_ons = _load_add_ons()
    results = []
    for a in add_ons:
        if not a.get("available", False):
            continue
        if category and a.get("category", "").lower() != category.strip().lower():
            continue
        results.append(a)
    return results


def get_add_on_by_id(add_on_id: str) -> dict[str, Any] | None:
    """Look up a single add-on by its ID."""
    add_ons = _load_add_ons()
    for a in add_ons:
        if a["add_on_id"].lower() == add_on_id.strip().lower():
            return a
    return None


def validate_selected_add_ons(add_on_ids: list[str]) -> dict[str, Any]:
    """Validate every selected add-on ID.

    Checks:
    1. add_on_id exists
    2. add-on is available
    3. no duplicates
    4. category is supported
    5. price is valid (> 0)
    6. pricing_type is supported

    Returns {"valid": True, "add_ons": [...]} or {"valid": False, "errors": [...]}.
    """
    if not add_on_ids:
        return {"valid": True, "add_ons": []}

    errors: list[str] = []
    seen_ids: set[str] = set()
    validated: list[dict[str, Any]] = []

    for raw_id in add_on_ids:
        aid = raw_id.strip().lower()

        # Duplicate check
        if aid in seen_ids:
            errors.append(f"Duplicate add-on: '{raw_id}'")
            continue
        seen_ids.add(aid)

        addon = get_add_on_by_id(raw_id)
        if addon is None:
            errors.append(f"Add-on not found: '{raw_id}'")
            continue

        if not addon.get("available", False):
            errors.append(f"Add-on '{addon['name']}' ({raw_id}) is not available")
            continue

        cat = addon.get("category", "")
        if cat not in VALID_CATEGORIES:
            errors.append(f"Add-on '{addon['name']}' has unsupported category: '{cat}'")
            continue

        price = addon.get("price")
        if price is None or not isinstance(price, (int, float)) or price <= 0:
            errors.append(f"Add-on '{addon['name']}' has invalid price: {price}")
            continue

        pt = addon.get("pricing_type", "")
        if pt not in VALID_PRICING_TYPES:
            errors.append(f"Add-on '{addon['name']}' has unsupported pricing type: '{pt}'")
            continue

        validated.append(addon)

    if errors:
        return {"valid": False, "errors": errors}
    return {"valid": True, "add_ons": validated}


def calculate_add_on_price(
    add_on_id: str,
    nights: int,
    guests: int,
) -> dict[str, Any]:
    """Server-side price calculation for a single add-on.

    Pricing rules:
      per_stay            → price
      per_day             → price × nights
      per_guest           → price × guests
      per_guest_per_day   → price × guests × nights

    Returns the full breakdown including the calculated total.
    """
    addon = get_add_on_by_id(add_on_id)
    if addon is None:
        return {"error": f"Add-on not found: '{add_on_id}'"}

    price = addon["price"]
    pt = addon["pricing_type"]

    if pt == "per_stay":
        total = price
    elif pt == "per_day":
        total = price * nights
    elif pt == "per_guest":
        total = price * guests
    elif pt == "per_guest_per_day":
        total = price * guests * nights
    else:
        return {"error": f"Unsupported pricing type: '{pt}'"}

    return {
        "add_on_id": addon["add_on_id"],
        "name": addon["name"],
        "category": addon["category"],
        "price": price,
        "pricing_type": pt,
        "nights": nights,
        "guests": guests,
        "calculated_total": total,
    }


def calculate_booking_total(
    accommodation_total: float,
    add_on_ids: list[str],
    nights: int,
    guests: int,
) -> dict[str, Any]:
    """Calculate the full booking total with breakdown.

    1. Validates all add-ons
    2. Calculates each add-on price server-side
    3. Sums everything

    Returns a complete breakdown dict.
    """
    # Validate first
    validation = validate_selected_add_ons(add_on_ids)
    if not validation["valid"]:
        return {"success": False, "errors": validation["errors"]}

    add_on_details: list[dict[str, Any]] = []
    add_ons_total = 0.0

    for aid in add_on_ids:
        result = calculate_add_on_price(aid, nights, guests)
        if "error" in result:
            return {"success": False, "errors": [result["error"]]}
        add_on_details.append(result)
        add_ons_total += result["calculated_total"]

    final_total = accommodation_total + add_ons_total

    return {
        "success": True,
        "accommodation_total": accommodation_total,
        "add_ons": add_on_details,
        "add_ons_total": add_ons_total,
        "final_total": final_total,
    }


# ---------------------------------------------------------------------------
# Enhanced booking creation with add-on support
# ---------------------------------------------------------------------------

_finalized_bookings: dict[str, dict[str, Any]] = {}  # idempotency_key → result


def _generate_confirmation_code() -> str:
    """Generate a simple confirmation code in format VGXXXXX."""
    return "VG" + "".join(random.choices(string.digits, k=5))


def create_booking(
    property_id: str,
    check_in: str,
    check_out: str,
    guests: int,
    guest_name: str,
    contact: str,
    selected_add_on_ids: list[str] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Create a mock booking. This is a state-changing action — the agent
    must have already gotten explicit verbal confirmation before calling
    this (see guardrail #5 in instructions.py).

    Extended to support optional add-ons: validates, prices, and stores
    them with the booking. The idempotency_key prevents duplicate bookings
    from retries.
    """
    # Duplicate booking protection
    if idempotency_key and idempotency_key in _finalized_bookings:
        return _finalized_bookings[idempotency_key]

    prop = get_stay_details(property_id)
    if prop is None:
        return {"success": False, "error": "Property not found"}

    avail = check_availability(property_id, check_in, check_out, guests)
    if not avail["available"]:
        return {"success": False, "error": avail.get("reason", "Not available")}

    # Validate and calculate add-ons
    resolved_add_ons: list[dict[str, Any]] = []
    add_ons_total = 0.0
    nights = avail["nights"] or 1

    if selected_add_on_ids:
        validation = validate_selected_add_ons(selected_add_on_ids)
        if not validation["valid"]:
            return {"success": False, "error": f"Add-on validation failed: {'; '.join(validation['errors'])}"}

        # Re-validate availability at confirmation time
        for aid in selected_add_on_ids:
            addon = get_add_on_by_id(aid)
            if addon is None or not addon.get("available", False):
                return {"success": False, "error": f"Add-on '{aid}' is no longer available"}

            price_result = calculate_add_on_price(aid, nights, guests)
            if "error" in price_result:
                return {"success": False, "error": price_result["error"]}

            resolved_add_ons.append(price_result)
            add_ons_total += price_result["calculated_total"]

    accommodation_total = avail["price_total_usd"]
    final_total = accommodation_total + add_ons_total

    with _lock:
        bookings = _load(BOOKINGS_PATH)
        booking_id = f"BK{len(bookings) + 1:04d}-{uuid.uuid4().hex[:4].upper()}"
        confirmation_code = _generate_confirmation_code()

        new_booking = {
            "booking_id": booking_id,
            "confirmation_code": confirmation_code,
            "guest_name": guest_name,
            "email": contact,
            "property_id": property_id,
            "property_name": prop["name"],
            "city": prop["city"],
            "check_in": check_in,
            "check_out": check_out,
            "nights": nights,
            "guests": guests,
            "status": "confirmed",
            "accommodation_total_usd": accommodation_total,
            "selected_add_ons": resolved_add_ons,
            "add_ons_total_usd": add_ons_total,
            "price_total_usd": final_total,
            "has_open_issue": False,
            "issue_notes": None,
        }
        bookings.append(new_booking)
        _save(BOOKINGS_PATH, bookings)

    result = {"success": True, "booking": new_booking}

    # Store for idempotency
    if idempotency_key:
        _finalized_bookings[idempotency_key] = result

    return result

