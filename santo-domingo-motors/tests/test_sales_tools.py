"""
Unit tests for the mock data layer + sales tools. These do NOT require
LiveKit, an LLM, or any network access — they exercise the plain Python
functions directly, which is the whole point of separating tools/ from
agents/.

Run with: pytest -q
"""
import json
import os
import shutil
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import data_store  # noqa: E402


@pytest.fixture()
def temp_data_dir(monkeypatch):
    """Copy the real /mock_data dir to a temp dir and point data_store at it,
    so tests never mutate the shipped mock data."""
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mock_data")
    tmp = tempfile.mkdtemp()
    for fname in os.listdir(src):
        shutil.copy(os.path.join(src, fname), tmp)
    monkeypatch.setattr(data_store, "DATA_DIR", tmp)
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


def test_read_vehicles_table(temp_data_dir):
    vehicles = data_store.read_table("vehicles")
    assert isinstance(vehicles, list)
    assert len(vehicles) >= 1
    assert "vehicle_id" in vehicles[0]


def test_search_vehicles_by_budget(temp_data_dir):
    from app.tools import sales_tools

    results = sales_tools.search_vehicles(vehicle_type="SUV", max_budget=40000)
    assert all(v["type"] == "SUV" for v in results)
    assert all(v["price"] <= 40000 for v in results)


def test_compare_vehicles(temp_data_dir):
    from app.tools import sales_tools

    result = sales_tools.compare_vehicles(["Groove", "Tracker"])
    assert len(result["vehicles"]) == 2
    assert result["not_found"] == []


def test_get_vehicle_price_from_data_not_llm(temp_data_dir):
    from app.tools import sales_tools

    result = sales_tools.get_vehicle_price("Groove")
    assert result is not None
    assert result["price"] == 24900


def test_book_test_drive_removes_slot(temp_data_dir):
    from app.tools import sales_tools

    before = sales_tools.check_test_drive_availability("kennedy", "2026-08-13")
    assert "09:00" in before

    result = sales_tools.book_test_drive(
        customer_name="Jane Doe",
        phone="809-555-9999",
        email=None,
        vehicle="Groove",
        location="kennedy",
        date="2026-08-13",
        time="09:00",
    )
    assert result["success"] is True

    after = sales_tools.check_test_drive_availability("kennedy", "2026-08-13")
    assert "09:00" not in after


def test_create_sales_lead_persists(temp_data_dir):
    from app.tools import sales_tools

    lead = sales_tools.create_sales_lead(
        customer_name="John Smith",
        phone="809-555-0199",
        email="john@example.com",
        interested_vehicle="Santa Fe",
        customer_requirement="7-seater SUV under 40k",
        test_drive_interest=True,
    )
    stored = data_store.read_table("sales_leads")
    assert any(rec["lead_id"] == lead["lead_id"] for rec in stored)
