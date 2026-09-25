"""
Mock "backend" for the Amadita POC.

This is intentionally NOT a database, ORM, or REST API. It's a thin
in-memory layer over the JSON files in agent/data/, built so that
agent/tools/*.py never touch the filesystem directly and so that this
whole module can be deleted and replaced with real LIS/scheduling API
clients in production (see README + POC plan §11) without touching
tools/ or main.py.

Everything here is a plain function operating on module-level lists of
dicts loaded at import time. Writes (booking/canceling/escalating) also
get flushed back to disk so state is visible if you inspect the JSON
files during/after a demo, and survives a worker restart.
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent.parent / "mock_data"

_lock = threading.Lock()

_WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _load(name: str) -> list[dict[str, Any]]:
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def _save(name: str, data: list[dict[str, Any]]) -> None:
    with open(DATA_DIR / name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


branches: list[dict[str, Any]] = _load("branches.json")
patients: list[dict[str, Any]] = _load("patients.json")
tests: list[dict[str, Any]] = _load("tests.json")
appointments: list[dict[str, Any]] = _load("appointments.json")
results: list[dict[str, Any]] = _load("results.json")


def _next_weekday(weekday_name: str, from_date: date | None = None) -> date:
    """Resolve 'friday' -> the date of the next upcoming Friday (today counts
    if today IS that weekday), so demo appointment data always looks fresh
    no matter when the POC is run."""
    from_date = from_date or date.today()
    target = _WEEKDAYS.index(weekday_name.lower())
    delta = (target - from_date.weekday()) % 7
    return from_date + timedelta(days=delta)


def _resolve_appt_date(appt: dict[str, Any]) -> str:
    if "date" in appt:
        return appt["date"]
    return _next_weekday(appt["relative_weekday"]).isoformat()


# ---------------------------------------------------------------- patients

def find_patient(
    query: str | None = None,
    name: str | None = None,
    phone: str | None = None,
) -> dict[str, Any] | None:
    """Lookup patient record by full name, phone number, both, or query string."""
    def clean_digits(val: str | None) -> str:
        return "".join(c for c in str(val or "") if c.isdigit())

    phone_digits = clean_digits(phone)
    name_clean = (name or "").strip().lower()

    # If both name and phone are provided
    if name_clean and phone_digits:
        for p in patients:
            p_digits = clean_digits(p.get("phone", ""))
            if (phone_digits in p_digits or p_digits in phone_digits) and (
                name_clean in p.get("full_name", "").lower() or p.get("full_name", "").lower() in name_clean
            ):
                return p
        # If combined match not found, try matching by phone first
        for p in patients:
            p_digits = clean_digits(p.get("phone", ""))
            if phone_digits and (phone_digits == p_digits or phone_digits in p_digits or p_digits in phone_digits):
                return p
        # Then name match
        for p in patients:
            if name_clean in p.get("full_name", "").lower() or p.get("full_name", "").lower() in name_clean:
                return p

    if phone_digits:
        for p in patients:
            p_digits = clean_digits(p.get("phone", ""))
            if phone_digits == p_digits or phone_digits in p_digits or p_digits in phone_digits:
                return p

    if name_clean:
        for p in patients:
            if name_clean in p.get("full_name", "").lower() or p.get("full_name", "").lower() in name_clean:
                return p

    q = (query or "").strip().lower()
    if not q:
        return None

    q_digits = clean_digits(q)
    for p in patients:
        if q == p.get("patient_id", "").lower() or q == p.get("phone", "").lower():
            return p
        if q_digits and q_digits == clean_digits(p.get("phone", "")):
            return p

    for p in patients:
        if q in p.get("full_name", "").lower():
            return p

    return None


def get_patient_by_id(patient_id: str) -> dict[str, Any] | None:
    return next((p for p in patients if p["patient_id"] == patient_id), None)


def patient_history(patient_id: str) -> dict[str, Any]:
    appts = [dict(a, date=_resolve_appt_date(a)) for a in appointments if a["patient_id"] == patient_id]
    p = get_patient_by_id(patient_id)
    notes = p["notes"] if p else []
    return {"appointments": appts, "notes": notes}


def create_patient(name: str, phone: str, email: str | None = None, date_of_birth: str | None = None) -> dict[str, Any]:
    with _lock:
        new_id = f"P-{uuid.uuid4().hex[:4].upper()}"
        new_patient = {
            "patient_id": new_id,
            "full_name": name,
            "phone": phone,
            "email": email or "",
            "date_of_birth": date_of_birth or "",
            "preferred_language": None,
            "notes": []
        }
        patients.append(new_patient)
        _save("patients.json", patients)
        return new_patient


# --------services (lab tests + imaging)------------------------------

# Unified alias map covering both lab tests and imaging services.
_SERVICE_ALIASES: dict[str, str] = {
    # --- lab test aliases ---
    "perfil_lipidico": "perfil_lipidico", "lipid_profile": "perfil_lipidico",
    "lipidos": "perfil_lipidico", "colesterol": "perfil_lipidico",
    "cbc": "hemograma", "blood_count": "hemograma",
    "conteo_sanguineo": "hemograma", "analisis_de_sangre": "hemograma",
    "urinalysis": "orina", "urine": "orina", "examen_de_orina": "orina",
    "fasting_glucose": "glucosa", "glucose": "glucosa",
    "azucar": "glucosa", "azucar_en_sangre": "glucosa",
    # --- thyroid ---
    "tiroides": "tiroides", "thyroid": "tiroides",
    "tsh": "tiroides", "t3": "tiroides", "t4": "tiroides",
    "perfil_tiroideo": "tiroides", "thyroid_panel": "tiroides",
    # --- vitamin D ---
    "vitamina_d": "vitamina_d", "vitamin_d": "vitamina_d",
    "25_oh": "vitamina_d", "vit_d": "vitamina_d",
    # --- HbA1c ---
    "hba1c": "hba1c", "hemoglobina_glicosilada": "hba1c",
    "glycated_hemoglobin": "hba1c", "a1c": "hba1c",
    # --- HIV ---
    "vih": "vih", "hiv": "vih", "elisa": "vih",
    "prueba_vih": "vih", "hiv_test": "vih",
    # --- COVID ---
    "covid": "covid_pcr", "covid_19": "covid_pcr", "pcr": "covid_pcr",
    "covid_pcr": "covid_pcr", "prueba_covid": "covid_pcr",
    # --- imaging aliases ---
    "resonancia_magnetica": "resonancia", "mri": "resonancia",
    "resonance": "resonancia", "magnetic_resonance": "resonancia",
    "rm": "resonancia",
    "ct_scan": "tomografia", "ct": "tomografia",
    "tomografia_computarizada": "tomografia", "cat_scan": "tomografia",
    "tac": "tomografia",
    "sonografia": "sonografia", "ultrasonido": "sonografia",
    "ultrasound": "sonografia", "sonography": "sonografia",
    "eco": "sonografia",
    "radiografia": "radiografia", "rayos_x": "radiografia",
    "x_ray": "radiografia", "xray": "radiografia",
    "x-ray": "radiografia", "rx": "radiografia",
    # --- mammography ---
    "mamografia": "mamografia", "mammography": "mamografia",
    "mammogram": "mamografia", "mamograma": "mamografia",
    # --- densitometry ---
    "densitometria": "densitometria", "densitometry": "densitometria",
    "dexa": "densitometria", "bone_density": "densitometria",
    "densidad_osea": "densitometria",
}


def get_service(service_id: str) -> dict[str, Any] | None:
    """Look up any schedulable service (lab test OR imaging) by id or alias."""
    sid = service_id.strip().lower().replace(" ", "_").replace("-", "_")
    sid = _SERVICE_ALIASES.get(sid, sid)
    return next((t for t in tests if t["test_id"] == sid), None)


# Keep the old name as a thin wrapper so nothing breaks.
def get_test(test_id: str) -> dict[str, Any] | None:
    """Backward-compatible wrapper — delegates to get_service."""
    return get_service(test_id)


# ------------------------------------------------------------------ branches

def get_branch(branch_id: str) -> dict[str, Any] | None:
    return next((b for b in branches if b["branch_id"] == branch_id), None)


def branch_capability(branch_id: str, service_id: str) -> dict[str, Any]:
    """Check whether a branch offers a given service (lab test or imaging)."""
    b = get_branch(branch_id)
    if not b:
        return {"found": False, "reason": "unknown_branch"}
    svc = get_service(service_id)
    sid = svc["test_id"] if svc else service_id
    # Support both old "tests_offered" key and new "services_offered" key.
    offered_list = b.get("services_offered") or b.get("tests_offered", [])
    offered = sid in offered_list
    unavailable_reason = b.get("unavailable_this_week", {}).get(sid)
    return {
        "found": True,
        "branch_id": branch_id,
        "branch_name": b["name"],
        "offers_service": offered and not unavailable_reason,
        "normally_offers_service": offered,
        "unavailable_this_week_reason": unavailable_reason,
        # Keep old key names for backward compat with anything reading them.
        "offers_test": offered and not unavailable_reason,
        "normally_offers_test": offered,
    }


def branches_offering(service_id: str) -> list[dict[str, Any]]:
    """Return branches that currently offer a given service."""
    svc = get_service(service_id)
    sid = svc["test_id"] if svc else service_id
    out = []
    for b in branches:
        cap = branch_capability(b["branch_id"], sid)
        if cap["offers_service"]:
            out.append(b)
    return out


# --------------------------------------------------------------- scheduling

def available_slots(branch_id: str, service_ids: list[str], fasting_only: bool = False,
                     days_ahead: int = 5) -> list[dict[str, Any]]:
    """Deterministic mock slot generator: a fixed daily pattern filtered by
    branch hours and (if any service requires fasting) morning-only slots.

    Works identically for lab tests and imaging services.
    """
    b = get_branch(branch_id)
    if not b:
        return []
    needs_fasting = fasting_only or any(
        (get_service(s) or {}).get("fasting_hours", 0) > 0 for s in service_ids
    )
    candidate_times = ["07:00", "07:30", "08:00", "09:00"] if needs_fasting else \
        ["07:00", "07:30", "08:00", "09:00", "11:00", "13:00", "15:00"]

    open_h, close_h = b["opens"], b["closes"]
    candidate_times = [t for t in candidate_times if open_h <= t <= close_h]

    slots = []
    d = date.today()
    added = 0
    day_i = 0
    while added < days_ahead and day_i < 14:
        day = d + timedelta(days=day_i)
        day_i += 1
        if day.weekday() == 6 and not b["open_sundays_holidays"]:
            continue
        for t in candidate_times:
            slots.append({"date": day.isoformat(), "weekday": _WEEKDAYS[day.weekday()], "time": t})
        added += 1
    return slots


def book_appointment(patient_id: str, branch_id: str, date_iso: str, time_str: str,
                      service_ids: list[str], cancel_appointment_id: str | None = None) -> dict[str, Any]:
    """Book an appointment for one or more services (lab tests and/or imaging).

    The `service_ids` parameter accepts both lab test ids and imaging service
    ids interchangeably.
    """
    with _lock:
        if cancel_appointment_id:
            for a in appointments:
                if a["appointment_id"] == cancel_appointment_id:
                    a["status"] = "cancelled"

        fasting_required = any((get_service(s) or {}).get("fasting_hours", 0) > 0 for s in service_ids)
        new_id = f"A-{uuid.uuid4().hex[:6].upper()}"
        new_appt = {
            "appointment_id": new_id,
            "patient_id": patient_id,
            "branch_id": branch_id,
            "date": date_iso,
            "time": time_str,
            "tests": service_ids,
            "status": "booked",
            "fasting_required": fasting_required,
        }
        appointments.append(new_appt)
        _save("appointments.json", appointments)
        return new_appt


def get_appointment(appointment_id: str) -> dict[str, Any] | None:
    for a in appointments:
        if a["appointment_id"] == appointment_id:
            return dict(a, date=_resolve_appt_date(a))
    return None


# ---------------------------------------------------------------- results

def get_result(patient_id: str, test_id: str) -> dict[str, Any] | None:
    test = get_test(test_id)
    tid = test["test_id"] if test else test_id
    return next((r for r in results if r["patient_id"] == patient_id and r["test_id"] == tid), None)


# ------------------------------------------------------------- notify / escalate

_sent_notifications: list[dict[str, Any]] = []
_escalations: list[dict[str, Any]] = []


def send_notification(patient_id: str, channel: str, message: str) -> dict[str, Any]:
    record = {
        "id": f"N-{uuid.uuid4().hex[:6].upper()}",
        "patient_id": patient_id,
        "channel": channel,
        "message": message,
        "sent_at": datetime.now().isoformat(timespec="seconds"),
    }
    _sent_notifications.append(record)
    return record


def create_escalation(patient_id: str, reason: str, transcript_summary: str, language: str) -> dict[str, Any]:
    record = {
        "id": f"T-{uuid.uuid4().hex[:6].upper()}",
        "patient_id": patient_id,
        "reason": reason,
        "transcript_summary": transcript_summary,
        "language": language,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "queued_for_human",
    }
    _escalations.append(record)
    return record


# ------------------------------------------------------------- home service (servicio a domicilio)

_home_visits: list[dict[str, Any]] = []


def check_home_service_eligible(service_ids: list[str]) -> dict[str, Any]:
    """Check which of the requested services are eligible for home visits."""
    eligible = []
    ineligible = []
    for sid in service_ids:
        svc = get_service(sid)
        if not svc:
            ineligible.append({"service_id": sid, "reason": "unknown_service"})
            continue
        if svc.get("home_service_eligible", False):
            eligible.append(svc)
        else:
            ineligible.append({"service_id": svc["test_id"], "name_es": svc["name_es"], "reason": "not_available_at_home"})
    return {"eligible": eligible, "ineligible": ineligible, "all_eligible": len(ineligible) == 0}


def branches_with_home_service() -> list[dict[str, Any]]:
    """Return branches that offer home/domicilio service in their coverage area."""
    return [b for b in branches if b.get("home_service", False)]


def book_home_visit(
    patient_id: str,
    service_ids: list[str],
    date_iso: str,
    time_str: str,
    address: str,
    zone: str | None = None,
) -> dict[str, Any]:
    """Book a home-visit appointment for lab tests that are eligible for
    servicio a domicilio."""
    with _lock:
        fasting_required = any((get_service(s) or {}).get("fasting_hours", 0) > 0 for s in service_ids)
        new_id = f"HV-{uuid.uuid4().hex[:6].upper()}"
        visit = {
            "visit_id": new_id,
            "patient_id": patient_id,
            "date": date_iso,
            "time": time_str,
            "address": address,
            "zone": zone,
            "tests": service_ids,
            "status": "scheduled",
            "fasting_required": fasting_required,
        }
        _home_visits.append(visit)
        return visit

