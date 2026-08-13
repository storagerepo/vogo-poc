"""
Function tools for add-on packages: get_available_add_ons, validate_and_calculate_add_ons,
and calculate_booking_total. Wired to Gemini's native function calling via
LiveKit's @function_tool decorator.
"""

from __future__ import annotations

from livekit.agents import function_tool, RunContext

from . import data_store


@function_tool()
async def get_available_add_ons_tool(
    context: RunContext,
    category: str | None = None,
) -> dict:
    """Get available add-on packages to offer the customer.
    
    Args:
        category: Filter by category (e.g., "transportation", "food_dining") or None for all.
        
    Returns:
        {"add_ons": [...], "count": ...}
    """
    results = data_store.get_available_add_ons(category=category)
    return {"add_ons": results, "count": len(results)}


@function_tool()
async def validate_and_calculate_add_ons_tool(
    context: RunContext,
    add_on_ids: list[str],
    nights: int,
    guests: int,
) -> dict:
    """Validate selected add-ons and calculate their individual prices.
    
    Args:
        add_on_ids: List of add-on IDs selected by the customer.
        nights: Number of nights for the stay.
        guests: Number of guests for the stay.
        
    Returns:
        {"valid": True, "add_ons": [...]} with calculated totals for each,
        or {"valid": False, "errors": [...]} if any selections are invalid.
    """
    validation = data_store.validate_selected_add_ons(add_on_ids)
    if not validation["valid"]:
        return validation
        
    # Calculate pricing for each valid add-on
    results = []
    for aid in add_on_ids:
        price_result = data_store.calculate_add_on_price(aid, nights, guests)
        if "error" in price_result:
            return {"valid": False, "errors": [price_result["error"]]}
        results.append(price_result)
        
    return {"valid": True, "add_ons": results}


@function_tool()
async def calculate_booking_total_tool(
    context: RunContext,
    accommodation_total: float,
    add_on_ids: list[str],
    nights: int,
    guests: int,
) -> dict:
    """Calculate the final booking total including accommodation and all add-ons.
    Always read the complete breakdown back to the customer before asking for confirmation.
    
    Args:
        accommodation_total: The base price for the accommodation.
        add_on_ids: List of add-on IDs selected by the customer.
        nights: Number of nights for the stay.
        guests: Number of guests for the stay.
        
    Returns:
        {"success": True, "accommodation_total": ..., "add_ons": [...], "add_ons_total": ..., "final_total": ...}
        or {"success": False, "errors": [...]} if validation fails.
    """
    return data_store.calculate_booking_total(
        accommodation_total=accommodation_total,
        add_on_ids=add_on_ids,
        nights=nights,
        guests=guests,
    )
