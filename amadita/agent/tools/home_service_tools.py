from livekit.agents import RunContext, function_tool

from .. import data_store


@function_tool()
async def check_home_service(
    context: RunContext,
    service_ids: list[str],
) -> dict:
    """Check whether the requested lab tests/services can be performed at
    the patient's home via Amadita's "servicio a domicilio". Only lab
    sample-collection tests are available for home visits — imaging
    services (MRI, CT, X-ray, sonography, mammography, densitometry)
    require the patient to visit a branch.

    Call this when a patient mentions they want a home visit, wants
    someone to come to their house, or mentions "servicio a domicilio".

    Args:
        service_ids: List of service ids the patient wants at home,
            e.g. ["hemograma", "glucosa"].
    """
    return data_store.check_home_service_eligible(service_ids)


@function_tool()
async def list_home_service_branches(context: RunContext) -> dict:
    """List all Amadita branches that offer home-visit ("servicio a
    domicilio") in their coverage area. Use this to help the patient
    understand which zone can dispatch a phlebotomist to their address.
    """
    branches = data_store.branches_with_home_service()
    return {"branches": branches}


@function_tool()
async def book_home_visit(
    context: RunContext,
    patient_id: str,
    service_ids: list[str],
    date_iso: str,
    time_str: str,
    address: str,
    zone: str | None = None,
) -> dict:
    """Book a home-visit appointment for eligible lab tests. A
    phlebotomist will go to the patient's address to collect samples.

    Only call this after:
    1. check_home_service confirmed the tests are eligible.
    2. The patient provided their address.
    3. The patient agreed to a specific date and time.

    Args:
        patient_id: The patient's ID, e.g. "P-1001".
        service_ids: List of home-eligible service ids.
        date_iso: Visit date, ISO format YYYY-MM-DD.
        time_str: Visit time, 24h "HH:MM".
        address: The patient's home address for the visit.
        zone: Optional zone/city for routing, e.g. "Santo Domingo".
    """
    visit = data_store.book_home_visit(
        patient_id, service_ids, date_iso, time_str, address, zone
    )
    return {"booked": True, "visit": visit}
