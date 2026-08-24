"""
service_tools.py
-----------------
Plain Python functions backing the Service journey (section 5 of the POC plan).
"""
from __future__ import annotations
from datetime import datetime

from app import data_store
from app.utils.ids import new_appointment_id
from app.utils.logger import get_logger

log = get_logger("tools.service")


def get_service_types() -> list[dict]:
    return data_store.read_table("service_types")

def get_service_locations() -> list[dict]:
    """Returns a list of branches that offer service."""
    from app.tools.branch_tools import get_all_branches
    branches = get_all_branches()
    return [b for b in branches if b.get("active", True) and "service" in (s.lower() for s in b.get("services", []))]




def get_service_details(service_type: str | None = None) -> list[dict]:
    """Returns info about one service type, or all of them if none given."""
    types = data_store.read_table("service_types")
    if not service_type:
        return types
    st = service_type.strip().lower()
    return [t for t in types if st in t["service_type"].lower()]


def check_service_availability(location_id: str, date: str) -> list[str]:
    slots = data_store.read_table("service_slots")
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        day_of_week = dt.strftime("%A")
    except ValueError:
        return []
    return slots.get(location_id, {}).get(day_of_week, [])


def book_service_appointment(
    customer_name: str,
    phone: str,
    vehicle: str,
    service_type: str,
    location: str,
    date: str,
    time: str,
    branch_id: str | None = None,
    branch_name: str | None = None,
) -> dict:
    slots = data_store.read_table("service_slots")
    
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
    data_store.write_table("service_slots", slots)

    appointment = {
        "appointment_id": new_appointment_id(),
        "customer_name": customer_name,
        "phone": phone,
        "vehicle": vehicle,
        "service_type": service_type,
        "location": location,
        "branch_id": b_id,
        "branch_name": branch_name,
        "date": date,
        "time": time,
        "status": "Confirmed",
    }
    data_store.append_record("service_appointments", appointment)
    log.info("Service appointment booked: %s", appointment["appointment_id"])
    return {"success": True, "appointment": appointment}


def get_appointment_details(appointment_id: str) -> dict | None:
    return data_store.find_one(
        "service_appointments", lambda a: a["appointment_id"] == appointment_id
    )
