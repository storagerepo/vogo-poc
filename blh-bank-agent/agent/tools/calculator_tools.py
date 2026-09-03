"""Loan payment calculator tool.

Implements a standard fixed-rate amortization formula so the voice agent can
give the customer an ESTIMATED monthly payment. This is explicitly a
POC-level estimate: no credit decision, no approval, no binding offer.
"""

from __future__ import annotations

from livekit.agents import RunContext, function_tool

from .. import data_store


def _amortized_monthly_payment(principal: float, annual_rate_pct: float, term_months: int) -> float:
    """Standard amortization formula: M = P * r(1+r)^n / ((1+r)^n - 1)."""
    if term_months <= 0:
        raise ValueError("term_months must be positive")
    if principal <= 0:
        raise ValueError("principal must be positive")

    monthly_rate = (annual_rate_pct / 100.0) / 12.0
    if monthly_rate == 0:
        return principal / term_months

    factor = (1 + monthly_rate) ** term_months
    return principal * (monthly_rate * factor) / (factor - 1)


@function_tool()
async def calculate_loan(
    context: RunContext,
    loan_type: str,
    amount: float,
    down_payment: float = 0.0,
    term_months: int = 0,
    annual_interest_rate_pct: float = 0.0,
) -> dict:
    """Calculate an ESTIMATED monthly loan payment for the customer.

    Always call get_loan_info first if you don't already know the loan's
    default term/rate limits. Collect missing required fields from the
    customer through natural conversation before calling this — do not
    guess values the customer has not provided. If `term_months` or
    `amount` is 0/missing, this tool will return which fields still need
    to be collected instead of a result.

    Args:
        loan_type: The loan type, e.g. "vehicle", "mortgage", "consumer",
            "foreign_currency", "immediate".
        amount: Total price of the asset or amount requested by the
            customer, in the loan's currency (DOP unless it's a foreign
            currency loan, which is USD).
        down_payment: Down payment amount the customer will pay upfront.
            Defaults to 0 if not applicable or not mentioned.
        term_months: Financing term in months (e.g. 60 for 5 years). Ask
            the customer for this if they only gave you years.
        annual_interest_rate_pct: Optional. Override the default annual
            interest rate for this loan type. Leave as 0 to use BLH's
            standard POC rate for that loan type.
    """
    loan = data_store.get_loan_by_type(loan_type)

    if loan is None:
        return {
            "ok": False,
            "message": f"Unknown loan type '{loan_type}'. Call get_loan_info first to see valid types.",
        }

    terms = loan.get("terms", {})
    currency = "USD" if loan.get("type") == "foreign_currency" else "DOP"

    missing = []
    if not amount or amount <= 0:
        missing.append("amount")
    if not term_months or term_months <= 0:
        missing.append("term_months")
    if missing:
        return {
            "ok": False,
            "missing_fields": missing,
            "message": (
                "Still need the following from the customer before calculating: "
                + ", ".join(missing)
            ),
            "loan_defaults": terms,
            "currency": currency,
        }

    max_term = terms.get("max_term_months")
    if max_term and term_months > max_term:
        return {
            "ok": False,
            "message": (
                f"Requested term of {term_months} months exceeds the maximum of "
                f"{max_term} months for this loan type. Ask the customer to choose "
                f"a shorter term."
            ),
        }

    rate = annual_interest_rate_pct if annual_interest_rate_pct > 0 else terms.get("annual_interest_rate_pct", 0.0)
    principal = max(amount - down_payment, 0)

    if principal <= 0:
        return {
            "ok": False,
            "message": "Down payment cannot be greater than or equal to the total amount.",
        }

    try:
        monthly_payment = _amortized_monthly_payment(principal, rate, term_months)
    except ValueError as exc:
        return {"ok": False, "message": str(exc)}

    total_paid = monthly_payment * term_months
    total_interest = total_paid - principal

    return {
        "ok": True,
        "estimate_disclaimer": (
            "This is an ESTIMATE only, not a loan approval, credit decision, "
            "or final offer. Final terms are subject to BLH credit approval."
        ),
        "loan_type": loan.get("type"),
        "loan_name_es": loan.get("name_es"),
        "loan_name_en": loan.get("name_en"),
        "currency": currency,
        "financed_amount": round(principal, 2),
        "down_payment": round(down_payment, 2),
        "term_months": term_months,
        "annual_interest_rate_pct": rate,
        "estimated_monthly_payment": round(monthly_payment, 2),
        "estimated_total_interest": round(total_interest, 2),
        "estimated_total_paid": round(total_paid, 2),
    }
