"""Tool: get_golf_info

Returns golf course, services, on-course dining, and reservation info from
the mock golf.json dataset.
"""

from __future__ import annotations

from typing import Optional

from . import load_json, normalize

_FILE = "golf.json"


def get_golf_info(topic: Optional[str] = None) -> dict:
    """Return golf information.

    Args:
        topic: Optional sub-topic to narrow the answer, e.g. "course",
            "carts", "caddies", "shop", "dining", "reservations". If omitted,
            returns the full golf dataset.
    """
    data = load_json(_FILE)

    if not topic:
        return {"found": True, "golf": data}

    t = normalize(topic)

    if any(k in t for k in ["course", "campo", "hole", "hoyo"]):
        return {"found": True, "topic": "course", "course": data["course"]}

    if any(k in t for k in ["cart", "carro"]):
        return {
            "found": True,
            "topic": "golf_carts",
            "service": next(s for s in data["services"] if s["id"] == "golf_carts"),
        }

    if "caddie" in t or "caddy" in t:
        return {
            "found": True,
            "topic": "caddies",
            "service": next(s for s in data["services"] if s["id"] == "caddies"),
        }

    if "shop" in t or "tienda" in t:
        return {
            "found": True,
            "topic": "golf_shop",
            "service": next(s for s in data["services"] if s["id"] == "golf_shop"),
        }

    if any(k in t for k in ["dining", "eat", "comida", "restaurant"]):
        return {"found": True, "topic": "on_course_dining", "dining": data["on_course_dining"]}

    if any(k in t for k in ["reserv", "book", "tee time"]):
        return {"found": True, "topic": "reservations", "reservations": data["reservations"]}

    return {"found": True, "topic": "general", "golf": data}
