"""
Function tools for support: report_issue, escalate_to_human.

Guardrail note (Section 9.6 — escalation): the system prompt defines the
trigger list (repeated frustration/anger, refund/compensation demands,
legal threats, safety concerns, 3 failed attempts at the same request).
This module just logs the escalation and hands back a reference; deciding
WHEN to call it is the model's job, steered by instructions.py.
"""

from __future__ import annotations

from livekit.agents import function_tool, RunContext

from . import data_store


@function_tool()
async def report_issue_tool(
    context: RunContext,
    booking_id: str,
    issue_type: str,
    description: str,
) -> dict:
    """Log a support ticket against a mock booking.

    Args:
        booking_id: The internal booking ID this issue relates to.
        issue_type: Short category, e.g. "host_unresponsive", "double_charge",
            "property_mismatch", "cleanliness", "other".
        description: A concise summary of what the user reported, in your
            own words — don't editorialize or add details they didn't give.

    Returns:
        {"success": True, "ticket": {"ticket_id": ..., ...}} — always read
        the ticket_id back to the user.
    """
    return data_store.report_issue(booking_id=booking_id, issue_type=issue_type, description=description)


@function_tool()
async def escalate_to_human_tool(
    context: RunContext,
    reason: str,
    urgency: str = "normal",
    booking_id: str | None = None,
) -> dict:
    """Hand off to a human support path. Use this when a defined
    escalation trigger fires (see system instructions) — do not try to
    resolve refund disputes, legal threats, or safety concerns yourself.

    Args:
        reason: Short, factual reason for the handoff (e.g. "guest requesting
            refund beyond policy", "repeated failed resolution attempts",
            "guest reported a safety concern at the property").
        urgency: "normal", "high", or "urgent". Use "urgent" for safety
            concerns or anything time-sensitive.
        booking_id: Related booking ID, if any.

    Returns:
        {"success": True, "escalation_id": "..."} — read this reference
        back to the user along with what happens next, and don't promise
        an outcome (refund amount, resolution time) you can't guarantee.
    """
    return data_store.escalate_to_human(reason=reason, urgency=urgency, booking_id=booking_id)
