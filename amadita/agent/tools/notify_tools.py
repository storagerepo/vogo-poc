from livekit.agents import RunContext, function_tool

from .. import data_store


@function_tool()
async def send_confirmation(context: RunContext, patient_id: str, message: str, channel: str = "sms") -> dict:
    """Send a confirmation message to the patient (mock SMS/email — no
    real message is sent in this POC, it's logged for the demo). Call
    this after a successful booking, reschedule, or cancellation so the
    patient has it in writing.

    Args:
        patient_id: The patient's ID, e.g. "P-1001".
        message: The confirmation text, in the locked session language.
        channel: "sms" or "email".
    """
    record = data_store.send_notification(patient_id, channel, message)
    return {"sent": True, "notification": record}
