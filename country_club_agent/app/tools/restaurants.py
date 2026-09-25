"""Tool: get_restaurant_info

Returns dining venue info from the mock restaurants.json dataset. Supports
looking up a single venue by name, or listing all venues.
"""

from __future__ import annotations

from typing import Optional

from . import load_json, normalize

_FILE = "restaurants.json"


def get_restaurant_info(restaurant: Optional[str] = None) -> dict:
    """Return info for a single restaurant/venue, or the full list if none given.

    Args:
        restaurant: Free-text venue name spoken by the user, e.g. "Hoyo 19",
            "sports bar", "pool". Matched loosely against known venue
            ids/names.
    """
    data = load_json(_FILE)
    restaurants = data["restaurants"]

    if not restaurant:
        return {
            "found": True,
            "restaurants": [{"id": r["id"], "name": r["name"]} for r in restaurants],
            "note_en": data["note_en"],
            "note_es": data["note_es"],
        }

    query = normalize(restaurant)

    for r in restaurants:
        candidates = [r["id"], r["name"]]
        if any(query in normalize(c) or normalize(c) in query for c in candidates):
            return {"found": True, "restaurant": r}

    return {
        "found": False,
        "message": f"No restaurant found matching '{restaurant}'.",
        "available_restaurants": [r["name"] for r in restaurants],
    }
