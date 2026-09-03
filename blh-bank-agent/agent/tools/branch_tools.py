"""Tools that expose BLH branch/ATM location information to the voice agent."""

from __future__ import annotations

from livekit.agents import RunContext, function_tool

from .. import data_store


@function_tool()
async def find_branch(context: RunContext, city_or_area: str = "") -> dict:
    """Find BLH branch information (address, phone, hours) for a city or area.

    Use this whenever the customer asks about branch locations, hours,
    phone numbers, or "where is the nearest branch". If the customer hasn't
    told you a city or area yet, ask them before calling this with an empty
    value — or call it with an empty value to get the full list of cities
    BLH operates in.

    Args:
        city_or_area: City, zone, or neighborhood the customer mentioned,
            e.g. "Santiago", "Santo Domingo", "Punta Cana", "Bavaro".
    """
    if not city_or_area.strip():
        return {
            "cities": data_store.list_cities(),
            "general_contact": data_store.general_contact,
        }

    matches = data_store.find_branches(city_or_area)
    if not matches:
        return {
            "found": False,
            "message": (
                f"No branch matched '{city_or_area}'. Cities with BLH branches: "
                f"{', '.join(data_store.list_cities())}."
            ),
            "general_contact": data_store.general_contact,
        }

    return {"found": True, "branches": matches}


@function_tool()
async def list_branches(context: RunContext) -> dict:
    """List all BLH branch locations and contact information."""
    return {"branches": data_store.branches, "general_contact": data_store.general_contact}


@function_tool()
async def find_atm(context: RunContext, city_or_area: str = "") -> dict:
    """Find BLH ATM locations, optionally filtered by city or area name.

    Args:
        city_or_area: City, zone, or neighborhood the customer mentioned.
            Leave empty to list all known ATM locations.
    """
    matches = data_store.find_atms(city_or_area.strip() if city_or_area else None)
    return {"atms": matches}
