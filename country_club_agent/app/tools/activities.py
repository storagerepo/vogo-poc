"""Tool: get_activity_info

Returns information about club activities/sports (golf, tennis, padel,
swimming, fitness, racquetball) from the mock activities.json dataset.
"""

from __future__ import annotations

from typing import Optional

from . import load_json, normalize

_FILE = "activities.json"


def get_activity_info(activity: Optional[str] = None) -> dict:
    """Return info for a single activity, or the full list if none given.

    Args:
        activity: Free-text activity name spoken by the user, e.g. "tennis",
            "pádel", "swimming pool". Matched loosely (case/accent
            insensitive substring match) against known activity ids/names.
    """
    data = load_json(_FILE)
    activities = data["activities"]

    if not activity:
        return {
            "found": True,
            "club_name": data["club_name"],
            "activities": [
                {"id": a["id"], "name_en": a["name_en"], "name_es": a["name_es"]}
                for a in activities
            ],
        }

    query = normalize(activity)
    # simple accent-insensitive normalization for common Spanish terms
    accent_map = str.maketrans("áéíóúñ", "aeioun")
    query_ascii = query.translate(accent_map)

    for a in activities:
        candidates = [a["id"], a["name_en"], a["name_es"]]
        candidates_ascii = [normalize(c).translate(accent_map) for c in candidates]
        if any(query_ascii in c or c in query_ascii for c in candidates_ascii):
            return {"found": True, "activity": a}

    return {
        "found": False,
        "message": f"No activity information found matching '{activity}'.",
        "available_activities": [a["id"] for a in activities],
    }


def get_club_overview() -> dict:
    """Return general club info: name, tagline, hours, contact, areas."""
    data = load_json(_FILE)
    return {
        "club_name": data["club_name"],
        "tagline": data["tagline"],
        "founded_years_ago": data["founded_years_ago"],
        "areas": data["areas"],
        "hours": data["hours"],
        "contact": data["contact"],
    }
