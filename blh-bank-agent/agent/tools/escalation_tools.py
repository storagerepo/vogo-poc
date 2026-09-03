"""Tools for escalating customer requests to a human representative."""

from __future__ import annotations

from livekit.agents import RunContext, function_tool

from .. import data_store


@function_tool()
async def escalate_to_human(
    context: RunContext,
    customer_name: str | None = None,
    phone: str | None = None,
    reason: str = "",
    transcript_summary: str = "",
    language: str = "es",
) -> dict:
    """Hand off the conversation to a human representative queue with context.

    Call this for account operations, transaction inquiries, complex requests
    that cannot be answered with current tools, or when the customer asks
    to speak with a representative.

    Args:
        customer_name: The customer's full name if provided.
        phone: The customer's contact phone number if provided.
        reason: Short reason for escalation, e.g. "wants to apply for loan".
        transcript_summary: Brief summary of the call context.
        language: Preferred conversation language ("es" or "en").
    """
    ticket = data_store.create_escalation(
        customer_name=customer_name,
        phone=phone,
        reason=reason,
        transcript_summary=transcript_summary,
        language=language,
    )
    return {"escalated": True, "ticket": ticket}
