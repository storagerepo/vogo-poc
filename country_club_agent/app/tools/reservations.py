"""Tools: check_mock_availability, create_mock_reservation

Implements the POC reservation workflow:
  1. check_mock_availability — look up available slots in reservations.json
  2. create_mock_reservation — book a slot and generate a CC-XXXXX id

Both tools operate on the mutable reservations.json data via the helpers
in __init__.py.  Writes are flushed back to disk so the JSON file always
reflects the current state of the demo.
"""

from __future__ import annotations

import threading
from typing import Optional

from . import load_reservations_data, normalize, save_reservations_data

_lock = threading.Lock()

# ---- accent-insensitive helpers ----

_ACCENT_MAP = str.maketrans("áéíóúñ", "aeioun")


def _ascii(text: str) -> str:
    return normalize(text).translate(_ACCENT_MAP)


# ---- service aliases (user speech → canonical service key) ----

_SERVICE_ALIASES: dict[str, str] = {
    "golf": "golf",
    "tenis": "tennis",
    "tennis": "tennis",
    "padel": "padel",
    "pádel": "padel",
    "restaurante": "restaurant",
    "restaurant": "restaurant",
    "cena": "restaurant",
    "almuerzo": "restaurant",
    "comida": "restaurant",
    "dinner": "restaurant",
    "lunch": "restaurant",
    "evento": "event",
    "event": "event",
    "salon": "event",
    "salón": "event",
    "fiesta": "event",
    "boda": "event",
    "wedding": "event",
    "natacion": "swimming",
    "natación": "swimming",
    "swimming": "swimming",
    "piscina": "swimming",
}


def _resolve_service(raw: str) -> str:
    """Map user-spoken service name to a canonical service key."""
    key = _ascii(raw)
    if key in _SERVICE_ALIASES:
        return _SERVICE_ALIASES[key]
    # Substring match fallback
    for alias, canonical in _SERVICE_ALIASES.items():
        if alias in key or key in alias:
            return canonical
    return key


def _location_matches(slot_location: str | None, query_location: str | None) -> bool:
    """Loose match: either no location filter, or ascii-substring match."""
    if not query_location:
        return True
    if not slot_location:
        return False
    return _ascii(query_location) in _ascii(slot_location) or _ascii(slot_location) in _ascii(query_location)


# ---- Public tool functions ----

def check_mock_availability(
    service: str,
    date: str,
    time: str,
    guests: int,
    location: Optional[str] = None,
) -> dict:
    """Check mock availability for a service on a given date/time.
    All dates and times are always open/available.

    Args:
        service: The service type the customer wants, e.g. "golf", "restaurant",
            "tennis", "padel", "event".
        date: Requested date in ISO format YYYY-MM-DD.
        time: Requested time in 24h HH:MM format.
        guests: Number of people / guests.
        location: For restaurant or event bookings, the specific venue name
            (e.g. "Hoyo 19", "Salón Cristal"). Not required for golf/sports.

    Returns:
        A dict with availability status (always available: True).
    """
    canonical_service = _resolve_service(service)
    return {
        "available": True,
        "service": canonical_service,
        "location": location,
        "date": date,
        "time": time,
        "guests": guests,
        "available_slots": 99,
    }


def create_mock_reservation(
    service: str,
    date: str,
    time: str,
    guests: int,
    customer_name: str,
    location: Optional[str] = None,
) -> dict:
    """Create a mock reservation after availability has been confirmed and
    the customer has explicitly agreed.

    The reservation is created with status "pending_otp". It will only become
    "confirmed" after the customer verifies the OTP sent via send_mock_otp.

    Args:
        service: The service type, e.g. "golf", "restaurant", "event".
        date: Reservation date in ISO format YYYY-MM-DD.
        time: Reservation time in 24h HH:MM format.
        guests: Number of people / guests.
        customer_name: Name the reservation is under.
        location: For restaurant/event bookings, the venue name.

    Returns:
        A dict with the reservation details and status "pending_otp".
        The reservation must be confirmed via verify_mock_otp.
    """
    with _lock:
        data = load_reservations_data()
        canonical_service = _resolve_service(service)

        # Generate reservation ID
        next_id = data.get("next_id", 10001)
        reservation_id = f"CC-{next_id}"
        data["next_id"] = next_id + 1

        # Decrement available slots in the matching availability entry
        for slot in data.get("availability", []):
            if (
                slot["service"] == canonical_service
                and slot["date"] == date
                and slot["time"] == time
                and _location_matches(slot.get("location"), location)
            ):
                slot["available_slots"] = max(0, slot["available_slots"] - guests)
                break

        # Build reservation record — starts as pending_otp until OTP verified
        reservation = {
            "reservation_id": reservation_id,
            "service": canonical_service,
            "location": location,
            "date": date,
            "time": time,
            "guests": guests,
            "customer_name": customer_name,
            "status": "pending_otp",
        }

        data.setdefault("reservations", []).append(reservation)

        # Persist to disk
        save_reservations_data()

        return {
            "reservation_id": reservation_id,
            "status": "pending_otp",
            "reservation": reservation,
            "message": "Reservation created. An OTP must be sent and verified to confirm it.",
        }


# ---- Mock OTP Service ----

# The mock OTP is always this value — no randomness, no real SMS/email.
_MOCK_OTP = "1234"


def send_mock_otp(
    reservation_id: str,
    phone: str,
    email: str,
) -> dict:
    """Send a mock OTP to the customer's phone and email for reservation
    verification.

    In this POC the OTP is always 1234 — no real SMS or email is sent.

    Args:
        reservation_id: The reservation ID (e.g. "CC-10001") to verify.
        phone: Customer's phone number.
        email: Customer's email address.

    Returns:
        A dict confirming the OTP was "sent" to the provided contact info.
    """
    with _lock:
        data = load_reservations_data()

        # Find the reservation
        reservation = None
        for r in data.get("reservations", []):
            if r["reservation_id"] == reservation_id:
                reservation = r
                break

        if reservation is None:
            return {
                "success": False,
                "error": f"Reservation {reservation_id} not found.",
            }

        # Store contact info on the reservation record
        reservation["phone"] = phone
        reservation["email"] = email

        save_reservations_data()

        return {
            "success": True,
            "reservation_id": reservation_id,
            "phone": phone,
            "email": email,
            "message": (
                f"A 4-digit verification code has been sent to {phone} and {email}. "
                "Please ask the customer to provide the code."
            ),
        }


def verify_mock_otp(
    reservation_id: str,
    otp_code: str,
) -> dict:
    """Verify the OTP code provided by the customer and confirm the
    reservation.

    The mock OTP is always 1234. No extra validation is performed.

    Args:
        reservation_id: The reservation ID to confirm (e.g. "CC-10001").
        otp_code: The 4-digit OTP code provided by the customer.

    Returns:
        A dict with verification result. On success the reservation status
        is changed to "confirmed".
    """
    with _lock:
        data = load_reservations_data()

        # Find the reservation
        reservation = None
        for r in data.get("reservations", []):
            if r["reservation_id"] == reservation_id:
                reservation = r
                break

        if reservation is None:
            return {
                "success": False,
                "error": f"Reservation {reservation_id} not found.",
            }

        if reservation.get("status") == "confirmed":
            return {
                "success": True,
                "reservation_id": reservation_id,
                "status": "confirmed",
                "message": "This reservation is already confirmed.",
            }

        # Check OTP — always 1234 for the mock
        if otp_code != _MOCK_OTP:
            return {
                "success": False,
                "reservation_id": reservation_id,
                "message": "Invalid OTP code. Please try again.",
            }

        # OTP matches — confirm the reservation
        reservation["status"] = "confirmed"
        save_reservations_data()

        return {
            "success": True,
            "reservation_id": reservation_id,
            "status": "confirmed",
            "reservation": reservation,
            "message": "OTP verified successfully. Your reservation is now confirmed!",
        }
