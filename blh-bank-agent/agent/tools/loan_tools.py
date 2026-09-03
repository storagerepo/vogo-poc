"""Tools that expose BLH loan-catalog information to the voice agent."""

from __future__ import annotations

from livekit.agents import RunContext, function_tool

from .. import data_store


@function_tool()
async def get_loan_info(context: RunContext, loan_type: str = "") -> dict:
    """Look up information about BLH loan products.

    Use this whenever the customer asks about loans in general, or about a
    specific loan type: mortgage/housing, vehicle/car, consumer/personal,
    foreign currency/dollar, or immediate/fast-disbursement loans. This
    returns purpose, eligibility, requirements, required documents and basic
    terms. It does NOT calculate a payment — call calculate_loan for that.

    Args:
        loan_type: Free-text loan type the customer mentioned (e.g. "vehicle",
            "vehiculo", "car", "mortgage", "hipotecario", "personal loan").
            Leave empty to list all loan types BLH offers along with the
            general loan benefits.
    """
    if not loan_type.strip():
        summary = [
            {
                "id": loan["id"],
                "type": loan["type"],
                "name_es": loan["name_es"],
                "name_en": loan["name_en"],
            }
            for loan in data_store.loans
        ]
        return {
            "loan_types": summary,
            "general_benefits": data_store.loan_general_benefits,
        }

    matches = data_store.find_loans(loan_type)
    if not matches:
        available = [loan["type"] for loan in data_store.loans]
        return {
            "found": False,
            "message": f"No loan type matched '{loan_type}'. Available types: {', '.join(available)}.",
        }

    return {"found": True, "loans": matches}
