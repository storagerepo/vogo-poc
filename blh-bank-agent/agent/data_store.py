"""
Mock "backend" for the BLH Voice Agent POC.

This is intentionally NOT a database, ORM, or REST API. It's a thin
in-memory layer over the JSON files in mock_data/, built so that
agent/tools/*.py never touch the filesystem directly and so that this
whole module can be swapped with real core banking / scheduling API
clients in production without touching tools/ or main.py.

Everything here operates on module-level data loaded at import time.
"""

from __future__ import annotations

import json
import threading
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent.parent / "mock_data"

_lock = threading.Lock()


def _load(name: str) -> Any:
    path = DATA_DIR / name
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(name: str, data: Any) -> None:
    with open(DATA_DIR / name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _normalize(text: str) -> str:
    """Lowercase + strip accents, so 'Santo Domingo' matches 'santo domingo'."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


_products_data: dict[str, Any] = _load("products.json")
_loans_data: dict[str, Any] = _load("loans.json")
_branches_data: dict[str, Any] = _load("branches.json")
_faqs_data: dict[str, Any] = _load("faqs.json")

products: list[dict[str, Any]] = _products_data.get("products", [])
loans: list[dict[str, Any]] = _loans_data.get("loans", [])
loan_general_benefits: dict[str, list[str]] = _loans_data.get("general_benefits", {})
branches: list[dict[str, Any]] = _branches_data.get("branches", [])
atms: list[dict[str, Any]] = _branches_data.get("atms", [])
general_contact: dict[str, Any] = _branches_data.get("general_contact", {})
faq_categories: list[dict[str, Any]] = _faqs_data.get("faq_categories", [])

_escalations: list[dict[str, Any]] = []


def find_faqs(query: str | None = None) -> list[dict[str, Any]]:
    """Search FAQs by query."""
    all_faqs = []
    for cat in faq_categories:
        for q in cat.get("questions", []):
            all_faqs.append({"category": cat.get("category"), "question": q.get("question"), "answer": q.get("answer")})
            
    if not query:
        return all_faqs
        
    q = _normalize(query)
    results = []
    for faq in all_faqs:
        haystack = _normalize(" ".join([faq["category"], faq["question"], faq["answer"]]))
        if q in haystack:
            results.append(faq)
    return results


# ------------------------------------------------------------------ Products

def list_product_categories() -> list[str]:
    seen: list[str] = []
    for p in products:
        category = p.get("category")
        if category and category not in seen:
            seen.append(category)
    return seen


def find_products(query: str | None = None) -> list[dict[str, Any]]:
    """Search products by free-text query against id/name/category/description."""
    if not query:
        return products
    q = _normalize(query)
    results = []
    for p in products:
        haystack = _normalize(
            " ".join(
                [
                    p.get("id", ""),
                    p.get("category", ""),
                    p.get("name_es", ""),
                    p.get("name_en", ""),
                    p.get("description_es", ""),
                    p.get("description_en", ""),
                ]
            )
        )
        if q in haystack:
            results.append(p)
    return results


def get_product(product_id: str) -> dict[str, Any] | None:
    pid = _normalize(product_id)
    return next((p for p in products if _normalize(p.get("id", "")) == pid), None)


# --------------------------------------------------------------------- Loans

_LOAN_ALIASES: dict[str, str] = {
    "car": "vehicle",
    "auto": "vehicle",
    "carro": "vehicle",
    "vehiculo": "vehicle",
    "casa": "mortgage",
    "vivienda": "mortgage",
    "hipoteca": "mortgage",
    "hipotecario": "mortgage",
    "dolares": "foreign_currency",
    "dollars": "foreign_currency",
    "divisas": "foreign_currency",
    "consumo": "consumer",
    "personal": "consumer",
    "rapido": "immediate",
    "inmediato": "immediate",
    "fast": "immediate",
}


def find_loans(query: str | None = None) -> list[dict[str, Any]]:
    if not query:
        return loans
    q = _normalize(query)
    q_type = _LOAN_ALIASES.get(q, q)
    results = []
    for loan in loans:
        haystack = _normalize(
            " ".join(
                [
                    loan.get("id", ""),
                    loan.get("type", ""),
                    loan.get("name_es", ""),
                    loan.get("name_en", ""),
                    loan.get("purpose_es", ""),
                    loan.get("purpose_en", ""),
                ]
            )
        )
        if q in haystack or q_type in haystack:
            results.append(loan)
    return results


def get_loan_by_type(loan_type: str) -> dict[str, Any] | None:
    matches = find_loans(loan_type)
    return matches[0] if matches else None


# ---------------------------------------------------------- Branches & ATMs

def list_cities() -> list[str]:
    seen: list[str] = []
    for b in branches:
        city = b.get("city")
        if city and city not in seen:
            seen.append(city)
    return seen


def find_branches(query: str | None = None) -> list[dict[str, Any]]:
    """Search branches by city, zone, name, or address."""
    if not query:
        return branches
    q = _normalize(query)
    results = []
    for b in branches:
        haystack = _normalize(
            " ".join(
                [
                    b.get("id", ""),
                    b.get("city", ""),
                    b.get("zone", ""),
                    b.get("name_es", ""),
                    b.get("name_en", ""),
                    b.get("address", ""),
                ]
            )
        )
        if q in haystack:
            results.append(b)
    return results


def get_branch(branch_id: str) -> dict[str, Any] | None:
    bid = _normalize(branch_id)
    return next((b for b in branches if _normalize(b.get("id", "")) == bid), None)


def find_atms(query: str | None = None) -> list[dict[str, Any]]:
    """Search ATMs by address or location description."""
    if not query:
        return atms
    q = _normalize(query)
    return [
        a for a in atms
        if q in _normalize(a.get("address", "")) or q in _normalize(a.get("location_es", "")) or q in _normalize(a.get("location_en", ""))
    ]


# ---------------------------------------------------------------- Escalation

def create_escalation(
    customer_name: str | None = None,
    phone: str | None = None,
    reason: str = "",
    transcript_summary: str = "",
    language: str = "es",
) -> dict[str, Any]:
    with _lock:
        record = {
            "id": f"T-{uuid.uuid4().hex[:6].upper()}",
            "customer_name": customer_name or "unknown",
            "phone": phone or "unknown",
            "reason": reason,
            "transcript_summary": transcript_summary,
            "language": language,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "status": "queued_for_human",
        }
        _escalations.append(record)
        return record


# End of data_store.py
