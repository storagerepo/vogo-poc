"""
schemas.py
----------
Lightweight dataclass-style shape references for the mock "tables".
These are NOT enforced ORM models (there is no DB) — they exist purely
as documentation + light validation helpers for the tool layer so the
JSON shapes stay consistent across sales/service/finance tools.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SalesLead:
    lead_id: str
    customer_name: str
    phone: str
    email: Optional[str]
    interested_vehicle: str
    customer_requirement: str
    test_drive_interest: bool
    preferred_location: Optional[str]
    preferred_branch_id: Optional[str] = None
    preferred_branch_name: Optional[str] = None
    customer_city: Optional[str] = None
    preferred_datetime: Optional[str] = None
    lead_source: str = "AI Voice Agent"
    lead_status: str = "New"


@dataclass
class TestDriveBooking:
    booking_id: str
    customer_name: str
    phone: str
    email: Optional[str]
    vehicle: str
    location: str
    date: str
    time: str
    branch_id: Optional[str] = None
    branch_name: Optional[str] = None
    status: str = "Confirmed"


@dataclass
class ServiceAppointment:
    appointment_id: str
    customer_name: str
    phone: str
    vehicle: str
    service_type: str
    location: str
    date: str
    time: str
    branch_id: Optional[str] = None
    branch_name: Optional[str] = None
    status: str = "Confirmed"


@dataclass
class FinanceState:
    """Tracks the progressive state of a finance conversation.

    This is NOT persisted — it lives in-memory during the agent session
    to guide the progressive collection flow and prevent re-asking for
    information already collected.
    """

    # Customer details
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    phone_verified: bool = False
    otp_attempts: int = 0

    # Vehicle selection
    vehicle_brand: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_id: Optional[str] = None
    vehicle_price: Optional[float] = None

    # Financing parameters (15% is enforced by backend, not prompt)
    initial_payment_percent: int = 15
    initial_payment: Optional[float] = None
    financed_amount: Optional[float] = None
    selected_bank: Optional[str] = None
    selected_bank_name: Optional[str] = None
    interest_rate: Optional[float] = None
    rate_type: Optional[str] = None
    term_months: Optional[int] = None

    # Calculation results
    monthly_payment: Optional[float] = None
    total_interest: Optional[float] = None
    total_payment: Optional[float] = None

    # Lead tracking
    finance_lead_id: Optional[str] = None
    lead_status: Optional[str] = None


@dataclass
class FinanceLead:
    lead_id: str
    customer_name: str
    phone: str
    email: Optional[str]
    phone_verified: bool
    vehicle_brand: str
    vehicle_model: str
    vehicle_id: str
    vehicle_price: float
    initial_payment_percent: int
    initial_payment: float
    financed_amount: float
    selected_bank: str
    selected_bank_name: str
    interest_rate: float
    rate_type: str
    term_months: int
    monthly_payment: float
    total_interest: float
    total_payment: float
    idempotency_key: Optional[str] = None
    lead_source: str = "AI Voice Agent"
    lead_status: str = "finance_requested"
    created_at: Optional[str] = None
