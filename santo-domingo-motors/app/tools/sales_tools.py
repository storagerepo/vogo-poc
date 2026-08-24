"""
sales_tools.py
--------------
Plain Python functions backing the Sales journey (section 4 of the POC plan).
These are wrapped as @function_tool inside app/agents/sales_agent.py — kept
separate here so they're easy to unit test without spinning up LiveKit.
"""
from __future__ import annotations
from datetime import datetime

from app import data_store
from app.utils.ids import new_booking_id, new_lead_id
from app.utils.logger import get_logger

log = get_logger("tools.sales")


def search_vehicles(
    vehicle_type: str | None = None,
    max_budget: float | None = None,
    min_budget: float | None = None,
    model: str | None = None,
    min_seating: int | None = None,
    fuel_type: str | None = None,
    transmission: str | None = None,
    in_stock_only: bool = True,
) -> list[dict]:
    """Search the mock vehicle catalog by loose, optional filters."""

    def matches(v: dict) -> bool:
        if vehicle_type and v["type"].lower() != vehicle_type.lower():
            return False
        if model and model.lower() not in v["model"].lower():
            return False
        if max_budget is not None and v["price"] > max_budget:
            return False
        if min_budget is not None and v["price"] < min_budget:
            return False
        if min_seating is not None and v["seating_capacity"] < min_seating:
            return False
        if fuel_type and v["fuel_type"].lower() != fuel_type.lower():
            return False
        if transmission and v["transmission"].lower() != transmission.lower():
            return False
        if in_stock_only and not v["in_stock"]:
            return False
        return True

    results = data_store.find_all("vehicles", matches)
    log.info("search_vehicles -> %d result(s)", len(results))
    return results


def get_vehicle_by_id_or_name(identifier: str) -> dict | None:
    """Resolve a vehicle by its ID or a fuzzy match on model name."""
    ident = identifier.strip().lower()

    def matches(v: dict) -> bool:
        return v["vehicle_id"].lower() == ident or ident in v["model"].lower()

    return data_store.find_one("vehicles", matches)


def compare_vehicles(identifiers: list[str]) -> dict:
    """Compare 2+ vehicles across price, engine, features, safety, etc."""
    vehicles = []
    not_found = []
    for ident in identifiers:
        v = get_vehicle_by_id_or_name(ident)
        if v:
            vehicles.append(v)
        else:
            not_found.append(ident)

    comparison = {
        "vehicles": vehicles,
        "not_found": not_found,
        "fields_compared": [
            "price", "engine", "transmission", "fuel_type",
            "seating_capacity", "safety_features", "features", "performance",
        ],
    }
    return comparison


def get_vehicle_price(identifier: str) -> dict | None:
    """Price must come from the vehicle data source, never invented by the LLM."""
    v = get_vehicle_by_id_or_name(identifier)
    if not v:
        return None
    return {"vehicle_id": v["vehicle_id"], "model": v["model"], "price": v["price"]}


def check_test_drive_availability(location_id: str, date: str) -> list[str]:
    slots = data_store.read_table("test_drive_slots")
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        day_of_week = dt.strftime("%A")
    except ValueError:
        return []
    return slots.get(location_id, {}).get(day_of_week, [])


def book_test_drive(
    customer_name: str,
    phone: str,
    email: str | None,
    vehicle: str,
    location: str,
    date: str,
    time: str,
    branch_id: str | None = None,
    branch_name: str | None = None,
) -> dict:
    """Books a test drive if the slot is still available, then removes it
    from the available pool (mock concurrency handling)."""
    slots = data_store.read_table("test_drive_slots")
    
    # Fallback if the agent still uses location instead of branch_id
    b_id = branch_id or location
    
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        day_of_week = dt.strftime("%A")
    except ValueError:
        return {"success": False, "reason": "Invalid date format. Use YYYY-MM-DD."}
    
    day_slots = slots.get(b_id, {}).get(day_of_week, [])
    if time not in day_slots:
        return {"success": False, "reason": "Selected slot is no longer available."}

    day_slots.remove(time)
    slots[b_id][day_of_week] = day_slots
    data_store.write_table("test_drive_slots", slots)

    booking = {
        "booking_id": new_booking_id(),
        "customer_name": customer_name,
        "phone": phone,
        "email": email,
        "vehicle": vehicle,
        "location": location,
        "branch_id": b_id,
        "branch_name": branch_name,
        "date": date,
        "time": time,
        "status": "Confirmed",
    }
    data_store.append_record("bookings", booking)
    log.info("Test drive booked: %s", booking["booking_id"])
    return {"success": True, "booking": booking}


def create_sales_lead(
    customer_name: str,
    phone: str,
    email: str | None,
    interested_vehicle: str,
    customer_requirement: str,
    test_drive_interest: bool = False,
    preferred_location: str | None = None,
    preferred_datetime: str | None = None,
    preferred_branch_id: str | None = None,
    preferred_branch_name: str | None = None,
    customer_city: str | None = None,
) -> dict:
    lead = {
        "lead_id": new_lead_id(),
        "customer_name": customer_name,
        "phone": phone,
        "email": email,
        "interested_vehicle": interested_vehicle,
        "customer_requirement": customer_requirement,
        "test_drive_interest": test_drive_interest,
        "preferred_location": preferred_location,
        "preferred_branch_id": preferred_branch_id,
        "preferred_branch_name": preferred_branch_name,
        "customer_city": customer_city,
        "preferred_datetime": preferred_datetime,
        "lead_source": "AI Voice Agent",
        "lead_status": "New",
    }
    data_store.append_record("sales_leads", lead)
    log.info("Sales lead created: %s", lead["lead_id"])
    return lead
