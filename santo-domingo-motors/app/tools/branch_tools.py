"""
branch_tools.py
----------------
Shared tools for branch selection and information.
"""
from __future__ import annotations

from app import data_store
from app.utils.logger import get_logger

log = get_logger("tools.branch")


def get_all_branches() -> list[dict]:
    """Return all branches."""
    return data_store.read_table("branches")


def get_branch_details(branch_id: str) -> dict | None:
    """Return details for a specific branch."""
    return data_store.find_one("branches", lambda b: b["id"] == branch_id)


def find_branch(
    city: str | None = None,
    area: str | None = None,
    service: str | None = None,
    brand: str | None = None,
) -> dict:
    """
    Find branches matching the criteria.
    Returns structured results to support multiple matches.
    """
    branches = get_all_branches()
    active_branches = [b for b in branches if b.get("active", True)]

    # Filter sequentially
    candidates = active_branches

    if city:
        city_lower = city.lower()
        candidates = [b for b in candidates if city_lower in b["city"].lower()]

    if service:
        service_lower = service.lower()
        candidates = [b for b in candidates if service_lower in (s.lower() for s in b.get("services", []))]

    if brand:
        brand_lower = brand.lower()
        candidates = [b for b in candidates if brand_lower in (b_name.lower() for b_name in b.get("brands", []))]

    log.info(f"find_branch(city={city}, service={service}, brand={brand}) found {len(candidates)} matches.")
    
    return {
        "count": len(candidates),
        "matches": candidates
    }
