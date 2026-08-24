"""
common_tools.py
----------------
Shared logic for Human Handoff (section 7 of the POC plan). In the real
system this would ring a queue in the CRM / call center platform. For the
POC it just logs the structured handoff payload — this is the seam where a
real integration (e.g. transferring the LiveKit room / SIP call, or opening
a ticket in the CRM) would be plugged in.
"""
from __future__ import annotations

from app.utils.logger import get_logger
from app.services.otp_service import send_otp, verify_otp

log = get_logger("tools.handoff")
log_otp = get_logger("tools.otp")

VALID_TEAMS = {"sales", "service", "finance"}


def human_handoff(team: str, reason: str, context_summary: str) -> dict:
    team_key = team.strip().lower()
    if team_key not in VALID_TEAMS:
        team_key = "sales"  # sensible default routing

    payload = {
        "handoff_team": team_key,
        "reason": reason,
        "context_summary": context_summary,
        "status": "queued_for_human",
    }
    log.info("Human handoff requested -> team=%s reason=%s", team_key, reason)
    # TODO(production): trigger real transfer here, e.g.
    #   - SIP transfer for phone calls
    #   - notify CRM / call center queue
    #   - push `context_summary` into the CRM ticket
    return payload

# ---------------------------------------------------------------------------
# OTP Tools
# ---------------------------------------------------------------------------

def send_customer_otp(phone: str, email: str | None = None) -> dict:
    """Send a verification code to the customer's phone number.

    Args:
        phone: Customer's phone number.
        email: Customer's email for backup delivery (optional).

    Returns:
        dict with success status and message.
    """
    result = send_otp(phone=phone, email=email)
    log_otp.info("send_customer_otp phone=%s success=%s", phone, result.get("success"))
    return result


def verify_customer_otp(phone: str, otp: str) -> dict:
    """Verify the OTP code provided by the customer.

    Args:
        phone: The phone number the OTP was sent to.
        otp: The OTP code the customer provided.

    Returns:
        dict with verified (bool), reason, and message.
    """
    result = verify_otp(phone=phone, otp=otp)
    log_otp.info("verify_customer_otp phone=%s verified=%s", phone, result.get("verified"))
    return result
