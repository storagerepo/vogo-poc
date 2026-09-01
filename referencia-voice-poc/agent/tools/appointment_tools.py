from livekit.agents import RunContext, function_tool

from .. import data_store


@function_tool()
async def check_appointment_slots(
    context: RunContext,
    branch_id: str,
    service_ids: list[str],
    fasting_only: bool = False,
) -> dict:
    """Check open appointment slots at a branch for one or more services
    (lab tests or imaging). Automatically restricts to morning
    fasting-compatible slots if any of the given services require fasting
    (or if fasting_only is set).

    Args:
        branch_id: Branch identifier, e.g. "piantini".
        service_ids: List of service ids to book together, e.g.
            ["hemograma", "perfil_lipidico"] for lab tests or
            ["resonancia", "radiografia"] for imaging services.
        fasting_only: Force morning-only fasting-compatible slots even
            if none of the services strictly require it.
    """
    slots = data_store.available_slots(branch_id, service_ids, fasting_only=fasting_only)
    return {"branch_id": branch_id, "slots": slots}


@function_tool()
async def book_appointment(
    context: RunContext,
    patient_id: str,
    branch_id: str,
    date_iso: str,
    time_str: str,
    service_ids: list[str],
    cancel_appointment_id: str | None = None,
) -> dict:
    """Book a new appointment for a patient for lab tests and/or imaging
    services, optionally cancelling/replacing an existing appointment in
    the same call (e.g. when combining two services into one visit).
    Only call this after you've confirmed the slot with
    check_appointment_slots and the patient has agreed to the specific time.

    Args:
        patient_id: The patient's ID, e.g. "P-1001".
        branch_id: Branch identifier for the new appointment.
        date_iso: Date of the new appointment, ISO format YYYY-MM-DD,
            taken from a slot returned by check_appointment_slots.
        time_str: Time of the new appointment, 24h "HH:MM", taken from a
            slot returned by check_appointment_slots.
        service_ids: List of service ids for this visit, e.g.
            ["hemograma", "perfil_lipidico"] for lab tests or
            ["tomografia"] for imaging.
        cancel_appointment_id: If this booking replaces an existing
            appointment, its appointment_id, so it gets cancelled
            atomically with this booking. Omit for a brand new booking.
    """
    appt = data_store.book_appointment(
        patient_id, branch_id, date_iso, time_str, service_ids, cancel_appointment_id
    )
    return {"booked": True, "appointment": appt}
