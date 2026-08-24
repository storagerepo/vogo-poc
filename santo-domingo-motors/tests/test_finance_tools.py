"""
test_finance_tools.py
---------------------
Tests for the Finance Agent tools and OTP service.
"""
import os
import shutil
import sys
import tempfile
import time

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import data_store  # noqa: E402
from app.services import otp_service  # noqa: E402


@pytest.fixture()
def temp_data_dir(monkeypatch):
    """Copy mock_data into a temp dir so tests don't mutate real data."""
    src = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mock_data"
    )
    tmp = tempfile.mkdtemp()
    for fname in os.listdir(src):
        shutil.copy(os.path.join(src, fname), tmp)
    monkeypatch.setattr(data_store, "DATA_DIR", tmp)
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture(autouse=True)
def clear_otp_store():
    """Ensure OTP store is clean between tests."""
    otp_service._otp_store.clear()
    yield
    otp_service._otp_store.clear()


# -----------------------------------------------------------------------
# OTP Service
# -----------------------------------------------------------------------

class TestOTPService:
    def test_send_otp_success(self):
        result = otp_service.send_otp("809-555-1234")
        assert result["success"] is True
        assert "_debug_otp" in result
        assert len(result["_debug_otp"]) == 4

    def test_send_otp_with_email(self):
        result = otp_service.send_otp("809-555-1234", "test@example.com")
        assert result["success"] is True
        assert "test@example.com" in result["message"]

    def test_send_otp_invalid_phone(self):
        result = otp_service.send_otp("abc")
        assert result["success"] is False

    def test_send_otp_invalid_email(self):
        result = otp_service.send_otp("809-555-1234", "not-an-email")
        assert result["success"] is False

    def test_verify_otp_correct(self):
        send_result = otp_service.send_otp("809-555-1234")
        code = send_result["_debug_otp"]
        verify_result = otp_service.verify_otp("809-555-1234", code)
        assert verify_result["verified"] is True

    def test_verify_otp_incorrect(self):
        otp_service.send_otp("809-555-1234")
        verify_result = otp_service.verify_otp("809-555-1234", "0000")
        assert verify_result["verified"] is False
        assert verify_result["reason"] == "incorrect_otp"
        assert verify_result["remaining_attempts"] == 2

    def test_verify_otp_max_attempts(self):
        otp_service.send_otp("809-555-1234")
        for _ in range(3):
            otp_service.verify_otp("809-555-1234", "0000")
        result = otp_service.verify_otp("809-555-1234", "0000")
        assert result["verified"] is False
        assert result["reason"] == "max_attempts"

    def test_verify_otp_expired(self, monkeypatch):
        otp_service.send_otp("809-555-1234")
        # Fast-forward time past TTL
        record = otp_service._otp_store["809-555-1234"]
        record["created_at"] = time.time() - (otp_service.OTP_TTL_SECONDS + 10)
        result = otp_service.verify_otp("809-555-1234", record["otp"])
        assert result["verified"] is False
        assert result["reason"] == "otp_expired"

    def test_verify_otp_no_otp_sent(self):
        result = otp_service.verify_otp("809-555-9999", "1234")
        assert result["verified"] is False
        assert result["reason"] == "no_otp_sent"


# -----------------------------------------------------------------------
# Vehicle Lookup Tools
# -----------------------------------------------------------------------

class TestVehicleLookup:
    def test_get_vehicle_brands(self, temp_data_dir):
        from app.tools import finance_tools

        result = finance_tools.get_vehicle_brands()
        brands = result["brands"]
        assert len(brands) > 0
        assert "Chevrolet" in brands
        assert "Nissan" in brands
        assert "Cadillac" in brands

    def test_get_vehicle_models(self, temp_data_dir):
        from app.tools import finance_tools

        result = finance_tools.get_vehicle_models("Chevrolet")
        assert result["found"] is True
        models = [m["model"] for m in result["models"]]
        assert "Groove" in models
        assert "Tracker" in models

    def test_get_vehicle_models_unknown_brand(self, temp_data_dir):
        from app.tools import finance_tools

        result = finance_tools.get_vehicle_models("UnknownBrand")
        assert result["found"] is False

    def test_get_vehicle_details_found(self, temp_data_dir):
        from app.tools import finance_tools

        result = finance_tools.get_vehicle_details("Chevrolet", "Groove")
        assert result["found"] is True
        assert result["price_available"] is True
        assert result["price_usd"] == 24900
        assert result["price_dop"] > 0
        assert result["currency"] == "DOP"

    def test_get_vehicle_details_not_found(self, temp_data_dir):
        from app.tools import finance_tools

        result = finance_tools.get_vehicle_details("Chevrolet", "Nonexistent")
        assert result["found"] is False

    def test_get_vehicle_details_no_price(self, temp_data_dir):
        from app.tools import finance_tools

        # Yamaha Ténéré 700 has price: null in the data
        result = finance_tools.get_vehicle_details("Yamaha", "Ténéré")
        assert result["found"] is True
        assert result["price_available"] is False


# -----------------------------------------------------------------------
# Bank & Financing Plan Tools
# -----------------------------------------------------------------------

class TestBankTools:
    def test_get_financing_banks(self, temp_data_dir):
        from app.tools import finance_tools

        result = finance_tools.get_financing_banks()
        banks = result["banks"]
        assert len(banks) == 6
        bank_ids = [b["bank_id"] for b in banks]
        assert "motor_credit" in bank_ids
        assert "banco_popular" in bank_ids
        assert "scotiabank" in bank_ids
        assert "banreservas" in bank_ids
        assert "santa_cruz" in bank_ids
        assert "bhd_bank" in bank_ids
        assert result["initial_payment_percent"] == 15

    def test_get_financing_plans(self, temp_data_dir):
        from app.tools import finance_tools

        result = finance_tools.get_financing_plans("motor_credit")
        assert result["found"] is True
        assert result["bank_name"] == "Motor Credit"
        assert len(result["plans"]) == 2
        rates = [p["interest_rate"] for p in result["plans"]]
        assert 13.45 in rates
        assert 14.45 in rates

    def test_get_financing_plans_unknown_bank(self, temp_data_dir):
        from app.tools import finance_tools

        result = finance_tools.get_financing_plans("unknown_bank")
        assert result["found"] is False


# -----------------------------------------------------------------------
# Finance Calculation
# -----------------------------------------------------------------------

class TestCalculation:
    def test_calculate_financing_correct_math(self, temp_data_dir):
        from app.tools import finance_tools

        # Known values: 24900 USD, 15% down, 14.45% rate, 36 months
        result = finance_tools.calculate_financing(
            vehicle_price_usd=24900,
            initial_payment_percent=15,
            interest_rate=14.45,
            term_months=36,
        )
        assert result["initial_payment_percent"] == 15
        assert result["currency"] == "DOP"
        assert result["monthly_payment_dop"] > 0
        assert result["total_payment_dop"] > result["financed_amount_dop"]
        assert result["total_interest_dop"] > 0
        assert result["estimate_only"] is True

        # Manual verification: 85% of (24900 * 56.50) = 1,195,222.50
        exchange_rate = result["exchange_rate"]
        expected_financed = round(24900 * exchange_rate * 0.85, 2)
        assert abs(result["financed_amount_dop"] - expected_financed) < 0.02

    def test_calculate_financing_enforces_15_percent(self, temp_data_dir):
        from app.tools import finance_tools

        # Pass 10% — should be overridden to 15%
        result = finance_tools.calculate_financing(
            vehicle_price_usd=30000,
            initial_payment_percent=10,
            interest_rate=13.00,
            term_months=24,
        )
        assert result["initial_payment_percent"] == 15

    def test_calculate_financing_zero_rate(self, temp_data_dir):
        from app.tools import finance_tools

        result = finance_tools.calculate_financing(
            vehicle_price_usd=10000,
            initial_payment_percent=15,
            interest_rate=0,
            term_months=12,
        )
        expected_financed = round(10000 * result["exchange_rate"] * 0.85, 2)
        expected_monthly = round(expected_financed / 12, 2)
        assert abs(result["monthly_payment_dop"] - expected_monthly) < 0.02


# -----------------------------------------------------------------------
# Finance Lead Creation
# -----------------------------------------------------------------------

class TestLeadCreation:
    def _make_lead_args(self):
        return dict(
            customer_name="Juan Pérez",
            phone="809-555-4321",
            email="juan@example.com",
            phone_verified=True,
            vehicle_brand="Chevrolet",
            vehicle_model="Groove",
            vehicle_id="veh_002",
            vehicle_price_usd=24900,
            bank_id="motor_credit",
            bank_name="Motor Credit",
            initial_payment_percent=15,
            initial_payment_dop=211027.50,
            financed_amount_dop=1195822.50,
            interest_rate=14.45,
            rate_type="fixed",
            term_months=36,
            monthly_payment_dop=41080.00,
            total_interest_dop=283058.50,
            total_payment_dop=1478881.00,
            idempotency_key="test-idem-key-001",
        )

    def test_create_finance_lead_persists(self, temp_data_dir):
        from app.tools import finance_tools

        args = self._make_lead_args()
        result = finance_tools.create_finance_lead(**args)
        assert result["created"] is True
        lead = result["lead"]
        assert lead["lead_id"].startswith("FIN-")
        assert lead["customer"]["name"] == "Juan Pérez"
        assert lead["customer"]["verified"] is True
        assert lead["vehicle"]["brand"] == "Chevrolet"
        assert lead["financing"]["bank_name"] == "Motor Credit"
        assert lead["status"] == "finance_requested"

        # Check persisted
        stored = data_store.read_table("finance_leads")
        assert any(rec["lead_id"] == lead["lead_id"] for rec in stored)

    def test_create_finance_lead_idempotent(self, temp_data_dir):
        from app.tools import finance_tools

        args = self._make_lead_args()
        result1 = finance_tools.create_finance_lead(**args)
        result2 = finance_tools.create_finance_lead(**args)

        assert result1["created"] is True
        assert result2["created"] is False
        assert result1["lead"]["lead_id"] == result2["lead"]["lead_id"]

        # Only one lead in store
        stored = data_store.read_table("finance_leads")
        matching = [r for r in stored if r.get("idempotency_key") == "test-idem-key-001"]
        assert len(matching) == 1
