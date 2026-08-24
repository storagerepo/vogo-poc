"""
Function tools for finding stays: search_stays, get_stay_details,
check_availability. Wired to Gemini's native function calling via
LiveKit's @function_tool decorator.

Guardrail note (Section 9.2 — grounding): Aria must only speak prices,
ratings, or availability that came back from one of these calls in the
current turn. Nothing here is decorative — every field returned is meant
to be read aloud verbatim or summarized faithfully, never embellished.
"""

from __future__ import annotations

from livekit.agents import function_tool, RunContext

from . import data_store


@function_tool()
async def search_stays_tool(
    context: RunContext,
    destination: str,
    guests: int | None = None,
    budget_tier: str | None = None,
    property_type: str | None = None,
    beachfront_only: bool = False,
    check_in: str | None = None,
    check_out: str | None = None,
) -> dict:
    """Search mocked Vogo listings for a stay.

    Args:
        destination: City or area the guest wants, e.g. "Goa" or "Manali".
        guests: Number of guests, if the caller mentioned it.
        budget_tier: One of "budget", "mid-range", "luxury" if implied.
        property_type: e.g. "villa", "resort", "homestay" if implied.
        beachfront_only: True only if the caller specifically wants beachfront.
        check_in: ISO date (YYYY-MM-DD) if known.
        check_out: ISO date (YYYY-MM-DD) if known.

    Returns:
        A dict with a "results" list (top 2-3 matches) or an empty list if
        nothing matched — in which case tell the user honestly rather than
        inventing an option.
    """
    results = data_store.search_stays(
        destination=destination,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        budget_tier=budget_tier,
        property_type=property_type,
        beachfront_only=beachfront_only,
    )
    return {"results": results, "count": len(results)}


@function_tool()
async def get_stay_details_tool(context: RunContext, property_id: str) -> dict:
    """Get full details for one specific mocked property.

    Args:
        property_id: The property's ID, e.g. "PROP007".

    Returns:
        The property record, or {"found": False} if it doesn't exist —
        never guess at details for a property that wasn't found.
    """
    prop = data_store.get_stay_details(property_id)
    if prop is None:
        return {"found": False}
    return {"found": True, "property": prop}


@function_tool()
async def check_availability_tool(
    context: RunContext,
    property_id: str,
    check_in: str,
    check_out: str,
    guests: int,
) -> dict:
    """Check whether a mocked property is available and get the priced total.

    Args:
        property_id: The property's ID, e.g. "PROP007".
        check_in: ISO date (YYYY-MM-DD).
        check_out: ISO date (YYYY-MM-DD).
        guests: Number of guests.

    Returns:
        Availability, nightly price, and total price for the stay. Always
        read the returned total back to the user before booking — never
        calculate or state a total yourself.
    """
    return data_store.check_availability(property_id, check_in, check_out, guests)
