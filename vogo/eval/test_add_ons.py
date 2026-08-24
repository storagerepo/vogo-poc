import pytest
from datetime import date
from unittest.mock import patch

from agent.tools import data_store

@pytest.fixture
def mock_add_ons():
    return [
        {
            "add_on_id": "addon_bike_001",
            "name": "Bike/Scooter Rental",
            "category": "transportation",
            "price": 15,
            "pricing_type": "per_day",
            "available": True
        },
        {
            "add_on_id": "addon_car_001",
            "name": "Car Rental",
            "category": "transportation",
            "price": 50,
            "pricing_type": "per_day",
            "available": True
        },
        {
            "add_on_id": "addon_breakfast_001",
            "name": "Breakfast",
            "category": "food_dining",
            "price": 10,
            "pricing_type": "per_guest_per_day",
            "available": True
        },
        {
            "add_on_id": "addon_full_meal_001",
            "name": "Full Meal Package",
            "category": "food_dining",
            "price": 25,
            "pricing_type": "per_guest_per_day",
            "available": True
        },
        {
            "add_on_id": "addon_unavailable",
            "name": "Unavailable Add-on",
            "category": "transportation",
            "price": 100,
            "pricing_type": "per_stay",
            "available": False
        },
        {
            "add_on_id": "addon_per_stay",
            "name": "Per Stay Add-on",
            "category": "transportation",
            "price": 100,
            "pricing_type": "per_stay",
            "available": True
        },
        {
            "add_on_id": "addon_per_guest",
            "name": "Per Guest Add-on",
            "category": "food_dining",
            "price": 20,
            "pricing_type": "per_guest",
            "available": True
        }
    ]

@pytest.fixture(autouse=True)
def setup_mock_data(monkeypatch, mock_add_ons):
    monkeypatch.setattr(data_store, "_load_add_ons", lambda: mock_add_ons)

def test_get_available_add_ons():
    all_available = data_store.get_available_add_ons()
    assert len(all_available) == 6
    assert not any(a["add_on_id"] == "addon_unavailable" for a in all_available)

    transportation = data_store.get_available_add_ons(category="transportation")
    assert len(transportation) == 3

    food = data_store.get_available_add_ons(category="food_dining")
    assert len(food) == 3

def test_validate_selected_add_ons_valid():
    res = data_store.validate_selected_add_ons(["addon_bike_001", "addon_breakfast_001"])
    assert res["valid"] is True
    assert len(res["add_ons"]) == 2

def test_validate_selected_add_ons_empty():
    res = data_store.validate_selected_add_ons([])
    assert res["valid"] is True
    assert len(res["add_ons"]) == 0
    
    res = data_store.validate_selected_add_ons(None)
    assert res["valid"] is True
    assert len(res["add_ons"]) == 0

def test_validate_selected_add_ons_duplicate():
    res = data_store.validate_selected_add_ons(["addon_bike_001", "addon_bike_001"])
    assert res["valid"] is False
    assert "Duplicate add-on: 'addon_bike_001'" in res["errors"]

def test_validate_selected_add_ons_unavailable():
    res = data_store.validate_selected_add_ons(["addon_unavailable"])
    assert res["valid"] is False
    assert "is not available" in res["errors"][0]

def test_validate_selected_add_ons_not_found():
    res = data_store.validate_selected_add_ons(["addon_fake"])
    assert res["valid"] is False
    assert "Add-on not found" in res["errors"][0]

def test_calculate_add_on_price_per_day():
    res = data_store.calculate_add_on_price("addon_bike_001", nights=3, guests=2)
    assert res["calculated_total"] == 15 * 3

def test_calculate_add_on_price_per_guest_per_day():
    res = data_store.calculate_add_on_price("addon_breakfast_001", nights=3, guests=2)
    assert res["calculated_total"] == 10 * 3 * 2

def test_calculate_add_on_price_per_stay():
    res = data_store.calculate_add_on_price("addon_per_stay", nights=3, guests=2)
    assert res["calculated_total"] == 100

def test_calculate_add_on_price_per_guest():
    res = data_store.calculate_add_on_price("addon_per_guest", nights=3, guests=2)
    assert res["calculated_total"] == 20 * 2

def test_calculate_booking_total():
    res = data_store.calculate_booking_total(
        accommodation_total=300,
        add_on_ids=["addon_bike_001", "addon_breakfast_001"],
        nights=3,
        guests=2
    )
    assert res["success"] is True
    assert res["accommodation_total"] == 300
    # bike: 15 * 3 = 45. breakfast: 10 * 3 * 2 = 60. total add-ons = 105
    assert res["add_ons_total"] == 105
    assert res["final_total"] == 405
    assert len(res["add_ons"]) == 2

@patch("agent.tools.data_store.check_availability")
@patch("agent.tools.data_store.get_stay_details")
@patch("agent.tools.data_store._load")
@patch("agent.tools.data_store._save")
def test_create_booking_with_add_ons(mock_save, mock_load, mock_get_stay, mock_check_avail):
    mock_load.return_value = []
    mock_get_stay.return_value = {"name": "Test Hotel", "city": "Test City"}
    mock_check_avail.return_value = {
        "available": True,
        "nights": 3,
        "price_total_usd": 300
    }

    res = data_store.create_booking(
        property_id="PROP001",
        check_in="2026-08-20",
        check_out="2026-08-23",
        guests=2,
        guest_name="John Doe",
        contact="test@example.com",
        selected_add_on_ids=["addon_bike_001", "addon_breakfast_001"]
    )

    assert res["success"] is True
    booking = res["booking"]
    assert booking["accommodation_total_usd"] == 300
    assert booking["add_ons_total_usd"] == 105
    assert booking["price_total_usd"] == 405
    assert len(booking["selected_add_ons"]) == 2
    assert booking["confirmation_code"].startswith("VG")

@patch("agent.tools.data_store.check_availability")
@patch("agent.tools.data_store.get_stay_details")
@patch("agent.tools.data_store._load")
@patch("agent.tools.data_store._save")
def test_create_booking_idempotency(mock_save, mock_load, mock_get_stay, mock_check_avail):
    mock_load.return_value = []
    mock_get_stay.return_value = {"name": "Test Hotel", "city": "Test City"}
    mock_check_avail.return_value = {
        "available": True,
        "nights": 3,
        "price_total_usd": 300
    }

    res1 = data_store.create_booking(
        property_id="PROP001",
        check_in="2026-08-20",
        check_out="2026-08-23",
        guests=2,
        guest_name="John Doe",
        contact="test@example.com",
        selected_add_on_ids=["addon_bike_001"],
        idempotency_key="test_key_123"
    )
    
    assert res1["success"] is True
    
    # Try again with same key
    res2 = data_store.create_booking(
        property_id="PROP001",
        check_in="2026-08-20",
        check_out="2026-08-23",
        guests=2,
        guest_name="John Doe",
        contact="test@example.com",
        selected_add_on_ids=["addon_bike_001"],
        idempotency_key="test_key_123"
    )
    
    assert res1 == res2
