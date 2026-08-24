"""
finance_tools.py
-----------------
Plain Python functions backing the Finance Agent journey.

6. Tools implemented:
    1. get_vehicle_brands     — List available vehicle brands
    2. get_vehicle_models     — List models for a given brand
    3. get_vehicle_details    — Full vehicle record including price
    4. get_financing_banks    — List available financing banks
    5. get_financing_plans    — Plans for a specific bank
    6. calculate_financing    — Amortizing-loan monthly payment calculation
    7. create_finance_lead    — Create an idempotent finance lead record

IMPORTANT:
    - Vehicle prices come from the vehicle data source, NEVER invented.
    - Interest rates come from bank configuration, NEVER invented.
    - The 15% initial payment is enforced in backend code, not by prompt.
    - Monthly payment is calculated by standard amortization, not approximated.
    - All customer-facing amounts are in DOP (converted from USD vehicle prices).
    - Finance leads are idempotent — duplicate requests return the existing lead.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app import data_store
from app.utils.ids import new_finance_lead_id, new_idempotency_key
from app.utils.logger import get_logger

log = get_logger("tools.finance")

# ---------------------------------------------------------------------------
# Constants (enforced by code, not by prompt)
# ---------------------------------------------------------------------------
INITIAL_PAYMENT_PERCENT = 15


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_finance_config() -> dict:
    """Load the bank financing configuration."""
    return data_store.read_table("finance_banks")


def _get_exchange_rate() -> float:
    """Get the configurable USD → DOP exchange rate."""
    config = _get_finance_config()
    return config.get("usd_to_dop_exchange_rate", 56.50)


def _usd_to_dop(amount_usd: float) -> float:
    """Convert a USD amount to DOP."""
    return round(amount_usd * _get_exchange_rate(), 2)


# ---------------------------------------------------------------------------
# 2. Vehicle Lookup Tools
# ---------------------------------------------------------------------------

def get_vehicle_brands() -> dict:
    """Get all available vehicle brands from the vehicle catalog.

    Returns:
        dict with list of brand names.
    """
    vehicles = data_store.read_table("vehicles")
    brands = sorted(set(v["brand"] for v in vehicles if v.get("in_stock", True)))
    log.info("get_vehicle_brands -> %d brands", len(brands))
    return {"brands": brands}


def get_vehicle_models(brand: str) -> dict:
    """Get available models for a specific vehicle brand.

    Args:
        brand: The vehicle brand name (case-insensitive).

    Returns:
        dict with brand, list of models, or error if brand not found.
    """
    vehicles = data_store.read_table("vehicles")
    brand_lower = brand.strip().lower()

    matching = [
        {"model": v["model"], "type": v["type"], "price_usd": v["price"], "vehicle_id": v["vehicle_id"]}
        for v in vehicles
        if v["brand"].lower() == brand_lower and v.get("in_stock", True)
    ]

    if not matching:
        return {"found": False, "brand": brand, "message": f"No vehicles found for brand '{brand}'."}

    return {"found": True, "brand": brand, "models": matching}


def get_vehicle_details(brand: str, model: str) -> dict:
    """Get full details for a specific vehicle by brand and model.

    Includes the price in both USD and DOP.

    Args:
        brand: The vehicle brand name (case-insensitive).
        model: The vehicle model name (case-insensitive, partial match).

    Returns:
        dict with vehicle details including prices, or error if not found.
    """
    vehicles = data_store.read_table("vehicles")
    brand_lower = brand.strip().lower()
    model_lower = model.strip().lower()

    vehicle = None
    for v in vehicles:
        if v["brand"].lower() == brand_lower and model_lower in v["model"].lower():
            vehicle = v
            break

    if not vehicle:
        return {
            "found": False,
            "brand": brand,
            "model": model,
            "message": f"No vehicle found matching brand '{brand}' and model '{model}'.",
        }

    price_usd = vehicle.get("price")
    if price_usd is None:
        return {
            "found": True,
            "vehicle": vehicle,
            "price_available": False,
            "message": f"The {brand} {vehicle['model']} is available but the price is not yet listed. "
                       "Please contact the dealership for pricing.",
        }

    price_dop = _usd_to_dop(price_usd)

    return {
        "found": True,
        "price_available": True,
        "vehicle_id": vehicle["vehicle_id"],
        "brand": vehicle["brand"],
        "model": vehicle["model"],
        "type": vehicle["type"],
        "year": vehicle["year"],
        "price_usd": price_usd,
        "price_dop": price_dop,
        "exchange_rate": _get_exchange_rate(),
        "currency": "DOP",
        "engine": vehicle.get("engine"),
        "transmission": vehicle.get("transmission"),
        "fuel_type": vehicle.get("fuel_type"),
    }


# ---------------------------------------------------------------------------
# 3. Bank & Financing Plan Tools
# ---------------------------------------------------------------------------

def get_financing_banks() -> dict:
    """Get the list of available financing banks.

    Returns:
        dict with list of banks (id + name).
    """
    config = _get_finance_config()
    banks = [
        {"bank_id": b["bank_id"], "bank_name": b["bank_name"]}
        for b in config.get("banks", [])
    ]
    log.info("get_financing_banks -> %d banks", len(banks))
    return {"banks": banks, "initial_payment_percent": config.get("initial_payment_percent", INITIAL_PAYMENT_PERCENT)}


def get_financing_plans(
    bank_id: str,
    vehicle_type: str = "new",
    usage: str = "personal",
) -> dict:
    """Get financing plans for a specific bank, filtered by vehicle type and usage.

    Args:
        bank_id: The bank identifier (e.g. "motor_credit").
        vehicle_type: "new" or "used" (default "new").
        usage: "personal" or "commercial" (default "personal").

    Returns:
        dict with bank info and list of matching plans, or error if bank not found.
    """
    config = _get_finance_config()
    bank_id_lower = bank_id.strip().lower()

    bank = None
    for b in config.get("banks", []):
        if b["bank_id"].lower() == bank_id_lower:
            bank = b
            break

    if not bank:
        return {
            "found": False,
            "bank_id": bank_id,
            "message": f"Bank '{bank_id}' not found. Use get_financing_banks() to see available banks.",
        }

    # Filter plans by vehicle type and usage
    vt = vehicle_type.strip().lower()
    us = usage.strip().lower()
    plans = [
        p for p in bank.get("plans", [])
        if p.get("vehicle_type", "new").lower() == vt
        and p.get("usage", "personal").lower() == us
    ]

    if not plans:
        return {
            "found": True,
            "bank_id": bank["bank_id"],
            "bank_name": bank["bank_name"],
            "plans": [],
            "message": f"No {vehicle_type}/{usage} financing plans available for {bank['bank_name']}.",
        }

    return {
        "found": True,
        "bank_id": bank["bank_id"],
        "bank_name": bank["bank_name"],
        "plans": plans,
        "_rate_disclaimer": "All rates shown are POC/mock rates. Final rates are subject to the bank's conditions.",
    }


# ---------------------------------------------------------------------------
# 4. Finance Calculation
# ---------------------------------------------------------------------------

def calculate_financing(
    vehicle_price_usd: float,
    initial_payment_percent: int,
    interest_rate: float,
    term_months: int,
) -> dict:
    """Calculate monthly installments using standard amortizing-loan formula.

    The 15% initial payment is ENFORCED by this function — if a different
    percentage is passed, it is overridden to 15% and a warning is logged.

    All output amounts are in DOP.

    Args:
        vehicle_price_usd: Vehicle price in USD (from vehicle data).
        initial_payment_percent: Must be 15; overridden if not.
        interest_rate: Annual interest rate as a percentage (e.g. 13.45).
        term_months: Loan term in months (e.g. 24, 36, 48, 60).

    Returns:
        dict with full financing breakdown in DOP.
    """
    # Enforce the fixed 15% initial payment
    if initial_payment_percent != INITIAL_PAYMENT_PERCENT:
        log.warning(
            "initial_payment_percent=%d overridden to %d",
            initial_payment_percent,
            INITIAL_PAYMENT_PERCENT,
        )
        initial_payment_percent = INITIAL_PAYMENT_PERCENT

    # Convert vehicle price to DOP
    exchange_rate = _get_exchange_rate()
    vehicle_price_dop = round(vehicle_price_usd * exchange_rate, 2)

    # Calculate initial payment and financed amount
    initial_payment = round(vehicle_price_dop * (initial_payment_percent / 100), 2)
    financed_amount = round(vehicle_price_dop - initial_payment, 2)

    # Standard amortizing-loan formula:
    # M = P * [r(1+r)^n] / [(1+r)^n - 1]
    # where P = principal, r = monthly rate, n = number of payments
    monthly_rate = (interest_rate / 100) / 12

    if monthly_rate == 0:
        monthly_payment = financed_amount / term_months if term_months > 0 else 0
    else:
        monthly_payment = (
            financed_amount
            * (monthly_rate * (1 + monthly_rate) ** term_months)
            / ((1 + monthly_rate) ** term_months - 1)
        )

    monthly_payment = round(monthly_payment, 2)
    total_payment = round(monthly_payment * term_months, 2)
    total_interest = round(total_payment - financed_amount, 2)

    config = _get_finance_config()

    return {
        "vehicle_price_usd": vehicle_price_usd,
        "vehicle_price_dop": vehicle_price_dop,
        "exchange_rate": exchange_rate,
        "initial_payment_percent": initial_payment_percent,
        "initial_payment_dop": initial_payment,
        "financed_amount_dop": financed_amount,
        "interest_rate": interest_rate,
        "rate_type": "fixed",
        "term_months": term_months,
        "monthly_payment_dop": monthly_payment,
        "total_payment_dop": total_payment,
        "total_interest_dop": total_interest,
        "currency": "DOP",
        "estimate_only": True,
        "disclaimer": config.get(
            "disclaimer",
            "This is an estimated financing calculation for reference only. "
            "Final terms are subject to the financing institution's conditions.",
        ),
    }


# ---------------------------------------------------------------------------
# 5. Finance Lead Creation (idempotent)
# ---------------------------------------------------------------------------

def create_finance_lead(
    customer_name: str,
    phone: str,
    email: str | None,
    phone_verified: bool,
    vehicle_brand: str,
    vehicle_model: str,
    vehicle_id: str,
    vehicle_price_usd: float,
    bank_id: str,
    bank_name: str,
    initial_payment_percent: int,
    initial_payment_dop: float,
    financed_amount_dop: float,
    interest_rate: float,
    rate_type: str,
    term_months: int,
    monthly_payment_dop: float,
    total_interest_dop: float,
    total_payment_dop: float,
    idempotency_key: str | None = None,
) -> dict:
    """Create a finance lead record. Idempotent on idempotency_key.

    If a lead with the same idempotency_key already exists, the existing
    lead is returned instead of creating a duplicate.

    Args:
        customer_name: Customer's full name.
        phone: Customer's verified phone number.
        email: Customer's email.
        phone_verified: Must be True (customer OTP verified).
        vehicle_brand: Selected vehicle brand.
        vehicle_model: Selected vehicle model.
        vehicle_id: Vehicle ID from catalog.
        vehicle_price_usd: Vehicle price in USD.
        bank_id: Selected bank ID.
        bank_name: Selected bank display name.
        initial_payment_percent: Always 15.
        initial_payment_dop: Initial payment amount in DOP.
        financed_amount_dop: Amount financed in DOP.
        interest_rate: Annual interest rate.
        rate_type: "fixed" or "variable".
        term_months: Financing term in months.
        monthly_payment_dop: Estimated monthly payment in DOP.
        total_interest_dop: Total estimated interest in DOP.
        total_payment_dop: Total estimated repayment in DOP.
        idempotency_key: Unique key to prevent duplicate leads.

    Returns:
        dict with the created (or existing) lead.
    """
    # Generate idempotency key if not provided
    if not idempotency_key:
        idempotency_key = new_idempotency_key(
            phone, vehicle_id, bank_id, str(term_months), str(interest_rate)
        )

    # Check for existing lead with same idempotency key
    existing = data_store.find_one(
        "finance_leads",
        lambda r: r.get("idempotency_key") == idempotency_key,
    )
    if existing:
        log.info(
            "Idempotent hit: returning existing lead %s for key=%s",
            existing["lead_id"],
            idempotency_key,
        )
        return {"created": False, "lead": existing, "message": "Finance lead already exists for this request."}

    lead = {
        "lead_id": new_finance_lead_id(),
        "customer": {
            "name": customer_name,
            "phone": phone,
            "email": email,
            "verified": phone_verified,
        },
        "vehicle": {
            "brand": vehicle_brand,
            "model": vehicle_model,
            "vehicle_id": vehicle_id,
            "price_usd": vehicle_price_usd,
            "price_dop": _usd_to_dop(vehicle_price_usd),
        },
        "financing": {
            "bank_id": bank_id,
            "bank_name": bank_name,
            "initial_payment_percent": initial_payment_percent,
            "initial_payment_dop": initial_payment_dop,
            "financed_amount_dop": financed_amount_dop,
            "interest_rate": interest_rate,
            "rate_type": rate_type,
            "term_months": term_months,
            "monthly_payment_dop": monthly_payment_dop,
            "total_interest_dop": total_interest_dop,
            "total_payment_dop": total_payment_dop,
            "currency": "DOP",
        },
        "status": "finance_requested",
        "idempotency_key": idempotency_key,
        "lead_source": "AI Voice Agent",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    data_store.append_record("finance_leads", lead)
    log.info("Finance lead created: %s (key=%s)", lead["lead_id"], idempotency_key)
    return {"created": True, "lead": lead, "message": "Finance lead created successfully."}
