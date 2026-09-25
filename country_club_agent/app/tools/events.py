"""Tool: get_event_info

Returns event/venue info (capacity, event types, facilities) from the mock
events.json dataset.
"""

from __future__ import annotations

from typing import Optional

from . import load_json, normalize

_FILE = "events.json"


def get_event_info(venue: Optional[str] = None) -> dict:
    """Return info for a single event venue, or the full list if none given.

    Args:
        venue: Free-text venue name spoken by the user, e.g. "Salón Cristal",
            "Sala de Fiestas". Matched loosely against known venue names.
    """
    data = load_json(_FILE)
    venues = data["venues"]

    if not venue:
        return {
            "found": True,
            "venues": [{"id": v["id"], "name": v["name"], "capacity": v["capacity"]} for v in venues],
            "contact": data["contact"],
        }

    query = normalize(venue)

    for v in venues:
        candidates = [v["id"], v["name"]]
        if any(query in normalize(c) or normalize(c) in query for c in candidates):
            return {"found": True, "venue": v, "contact": data["contact"]}

    return {
        "found": False,
        "message": f"No event venue found matching '{venue}'.",
        "available_venues": [v["name"] for v in venues],
    }
