"""Tools that expose OTP generation and verification for the BLH voice agent."""

from __future__ import annotations

from livekit.agents import RunContext, function_tool

from ..services import otp_service
from ..userdata import SessionUserData


@function_tool()
async def send_otp(
    context: RunContext[SessionUserData],
    name: str,
    phone: str,
) -> str:
    """Send a 4-digit verification code (OTP) to the customer's phone number.

    Call this after collecting the customer's name and phone number.

    Args:
        name: Customer's full name.
        phone: Customer's phone number.
    """
    clean_name = name.strip()
    clean_phone = phone.strip()

    context.userdata.name = clean_name
    context.userdata.phone = clean_phone

    otp_service.send_otp(clean_phone)

    return (
        f"Saved details for {clean_name}. A 4-digit verification code has been sent to {clean_phone}. "
        "Ask the customer to read back the 4-digit code."
    )


@function_tool()
async def verify_otp(
    context: RunContext[SessionUserData],
    code: str,
) -> str:
    """Verify the 4-digit OTP code that the customer reads back.

    Args:
        code: The 4-digit verification code provided by the customer (e.g. '1234').
    """
    clean_code = str(code).strip()
    phone = context.userdata.phone or ""

    result = otp_service.verify_otp(phone=phone, otp=clean_code)

    if result.get("verified"):
        context.userdata.verified = True
        return "Verification successful. The customer is now verified."

    return "Incorrect verification code. Please ask the customer to try again."
