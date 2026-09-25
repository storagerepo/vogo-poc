from livekit.agents import RunContext, function_tool

from .. import data_store


@function_tool()
async def escalate_to_human(
    context: RunContext,
    patient_id: str,
    reason: str,
    transcript_summary: str,
    language: str = "en",
) -> dict:
    """Hand off the conversation to a human queue with full context
    attached, so the patient doesn't have to repeat themselves. Call
    this for data mix-ups, privacy concerns, repeated complaints,
    requests you can't resolve with your other tools, or an upset
    patient asking for a supervisor.

    Args:
        patient_id: The patient's ID if known, otherwise "unknown".
        reason: Short reason for the escalation, e.g.
            "results mixed up with another patient, repeat complaint".
        transcript_summary: A brief summary of what happened in this
            session so the human agent has context immediately.
        language: The locked session language ("es" or "en"), so the
            human queue routes to a matching agent.
    """
    ticket = data_store.create_escalation(patient_id, reason, transcript_summary, language)
    return {"escalated": True, "ticket": ticket}
