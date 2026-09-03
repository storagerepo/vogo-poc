"""Tools that expose BLH product-catalog information to the voice agent."""

from __future__ import annotations

from livekit.agents import RunContext, function_tool

from .. import data_store


@function_tool()
async def get_product_info(context: RunContext, product_or_category: str = "") -> dict:
    """Look up BLH banking product information for the customer.

    Use this whenever the customer asks what products BLH offers, or asks about
    a specific product such as savings accounts, current accounts, credit cards,
    debit cards, term deposits, safe deposit boxes, or foreign exchange.
    Do NOT use this tool for loan-specific questions — use get_loan_info instead.

    Args:
        product_or_category: Free-text name of the product or category the
            customer is asking about (e.g. "savings accounts", "cuentas de
            ahorro", "credit card", "tarjeta de crédito"). Leave empty to list
            all product categories BLH offers.
    """
    if not product_or_category.strip():
        categories = data_store.list_product_categories()
        summary = [
            {
                "category": c,
                "products": [p["name_es"] for p in data_store.products if p.get("category") == c],
            }
            for c in categories
        ]
        return {"categories": summary}

    matches = data_store.find_products(product_or_category)
    if not matches:
        return {
            "found": False,
            "message": (
                f"No product matched '{product_or_category}'. Available categories: "
                f"{', '.join(data_store.list_product_categories())}."
            ),
        }

    return {"found": True, "products": matches}
