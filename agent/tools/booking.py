"""
Function tools for booking lifecycle: create_booking, get_booking_status,
modify_or_cancel_booking.

Guardrail note (Section 9.5 — confirm-before-action): create_booking and
modify_or_cancel_booking are state-changing. The system prompt instructs
Aria to get an explicit verbal "yes" and read back property, dates,
guests, and total price BEFORE calling create_booking_tool — this file
does not enforce that itself (it can't observe the conversation), so the
instructions.py guardrail text is load-bearing here.
"""

from __future__ import annotations

from livekit.agents import function_tool, RunContext

from . import data_store


@function_tool()
async def create_booking_tool(
    context: RunContext,
    property_id: str,
    check_in: str,
    check_out: str,
    guests: int,
    guest_name: str,
    contact: str,
) -> dict:
    """Create a mock booking. Only call this AFTER the user has explicitly
    confirmed the property, dates, guest count, and total price out loud.

    Args:
        property_id: The property's ID, e.g. "PROP007".
        check_in: ISO date (YYYY-MM-DD).
        check_out: ISO date (YYYY-MM-DD).
        guests: Number of guests.
        guest_name: Name to put the booking under. This is mock/demo data —
            never ask for or store real government ID or payment details.
        contact: Email or phone the user gives for the mock booking.

    Returns:
        {"success": True, "booking": {...}} with a confirmation_code to
        read back, or {"success": False, "error": "..."} if unavailable —
        in which case tell the user honestly and offer alternatives.
    """
    return data_store.create_booking(
        property_id=property_id,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        guest_name=guest_name,
        contact=contact,
    )


@function_tool()
async def get_booking_status_tool(
    context: RunContext,
    confirmation_code: str | None = None,
    guest_name: str | None = None,
    email: str | None = None,
) -> dict:
    """Look up an existing mock booking by confirmation code, name, or email.
    Provide at least one identifier.

    Args:
        confirmation_code: e.g. "VG48213", if the caller has it.
        guest_name: Full or partial name, if that's what the caller gives.
        email: Email address, if given.

    Returns:
        {"matches": [...]} — could be empty, one, or several bookings. If
        several match a name, ask the user to disambiguate (e.g. by
        confirmation code or check-in date) rather than picking one.
    """
    matches = data_store.get_booking_status(
        confirmation_code=confirmation_code,
        guest_name=guest_name,
        email=email,
    )
    return {"matches": matches, "count": len(matches)}


@function_tool()
async def modify_or_cancel_booking_tool(context: RunContext, booking_id: str, action: str) -> dict:
    """Cancel or (attempt to) modify a mock booking. Only call after
    explicit verbal confirmation of the action and which booking it applies to.

    Args:
        booking_id: The internal booking ID (e.g. "BK0003-9F2A"), not the
            confirmation code — look it up via get_booking_status_tool first.
        action: "cancel" or "modify". Modify is not supported in this POC
            and will return an error directing you to escalate.

    Returns:
        {"success": True/False, ...}
    """
    return data_store.modify_or_cancel_booking(booking_id=booking_id, action=action)
