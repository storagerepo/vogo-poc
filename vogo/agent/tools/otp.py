"""
Function tools for mock OTP verification.

These are additive tools — the existing booking tools are not modified.
The agent uses these before state-changing actions (create_booking_tool,
modify_or_cancel_booking_tool) to verify the caller's identity via a
mock 4-digit OTP printed to the backend console.
"""

from __future__ import annotations

from livekit.agents import function_tool, RunContext

from . import data_store


@function_tool()
async def send_otp_tool(context: RunContext, contact: str) -> dict:
    """Send a mock 4-digit OTP to the given contact for identity verification.
    Call this BEFORE executing a state-changing action (booking or cancellation).

    Ask the user for their phone number or email first, then call this tool.

    Args:
        contact: The user's phone number or email address.

    Returns:
        {"success": True, "message": "OTP sent to <contact>"}
    """
    return data_store.send_mock_otp(contact=contact)


@function_tool()
async def verify_otp_tool(context: RunContext, contact: str, otp: str) -> dict:
    """Verify the OTP code the user reads back. Call this after send_otp_tool.

    Args:
        contact: The same phone number or email used in send_otp_tool.
        otp: The 4-digit code the user provides.

    Returns:
        {"verified": True} on success, or {"verified": False, "reason": "..."}
        on failure. Only proceed with the booking/cancellation if verified is True.
    """
    return data_store.verify_mock_otp(contact=contact, otp=otp)
