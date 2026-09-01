from livekit.agents import RunContext, function_tool

from .. import data_store


@function_tool()
async def lookup_patient(
    context: RunContext,
    name: str | None = None,
    phone: str | None = None,
    name_phone_or_id: str | None = None,
) -> dict:
    """Find an existing patient's record using their full name and phone number
    (both mandatory when identifying an existing patient), or by patient ID/search query.
    Call this first whenever an existing patient identifies themselves with both
    their name and phone number, before checking history, appointments, or results.

    Args:
        name: The full name of the patient (e.g. "Maria Fernandez").
        phone: The phone number of the patient (e.g. "8095551001").
        name_phone_or_id: Search query or patient ID (e.g. "P-1001") if provided as a single string.
    """
    patient = data_store.find_patient(query=name_phone_or_id, name=name, phone=phone)
    if not patient:
        return {"found": False, "message": "No patient record matched the provided name and phone number."}
    return {"found": True, "patient": patient}


@function_tool()
async def get_patient_history(context: RunContext, patient_id: str) -> dict:
    """Return a patient's past and upcoming appointments and any account
    notes/flags (e.g. a prior complaint). Call this after lookup_patient
    to check "has this person been here before, any notes" before acting
    on their request.

    Args:
        patient_id: The patient_id returned by lookup_patient, e.g. "P-1001".
    """
    history = data_store.patient_history(patient_id)
    if not history["appointments"] and not history["notes"]:
        return {"found": bool(data_store.get_patient_by_id(patient_id)), **history}
    return {"found": True, **history}


@function_tool()
async def create_patient(
    context: RunContext, 
    name: str, 
    phone: str, 
    email: str | None = None, 
    date_of_birth: str | None = None
) -> dict:
    """Register a new patient into the system.
    Call this ONLY when a user confirms they are a new patient and provides
    their name and phone number.

    Args:
        name: The full name of the new patient.
        phone: The patient's phone number.
        email: The patient's email address (optional).
        date_of_birth: The patient's date of birth, e.g. "YYYY-MM-DD" (optional).
    """
    patient = data_store.create_patient(name, phone, email, date_of_birth)
    return {"success": True, "patient": patient}
