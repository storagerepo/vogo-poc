"""
agents/loan.py

Handles loan inquiries: eligibility, amount, tenure, interest rate,
estimated monthly repayment, and creating a mock loan lead.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from livekit.agents import RunContext, function_tool

from app.agents.base import DepartmentAgent
from app.core import store
from app.core.userdata import SessionUserData
from app.prompts.base import BANK_CONTEXT, VOICE_STYLE_GUIDE

logger = logging.getLogger("jmmb-loan")

INSTRUCTIONS = f"""
{BANK_CONTEXT}
{VOICE_STYLE_GUIDE}

You are SARA, now helping the customer with loan-related questions. The
customer has already been onboarded and verified — do not ask for their
name or verify them again.  Do NOT introduce yourself or greet the customer, as they
are already in the middle of a conversation with you. Seamlessly continue the
conversation based on the context.

Your job:
- Understand what kind of loan they're interested in (e.g. personal, new vehicle, used vehicle, mortgage).
- Gather their rough monthly income, desired loan amount, and preferred tenure (in months).
- For vehicle or mortgage loans, gather the vehicle or property value.
- Gather their preferred JMMB office branch.
- Ask if they authorize JMMB Bank SA to review their credit bureau report.
- Use `check_loan_eligibility` to give a quick eligibility read based on
  income and product minimums.
- Use `calculate_loan_payment` to estimate the monthly repayment for a
  given amount, tenure, and product type.
- If they want to proceed, use `create_loan_lead` to log a mock lead for
  a human loan officer to follow up on, and give them a lead reference
  number.
- If the conversation shifts to general financial/investment questions
  instead of borrowing, use `transfer_to_financial_guidance`.
- If the customer asks for something outside of loans (like service
  appointments or security concerns), use `return_to_supervisor`.

Always state clearly that repayment figures are estimates and any actual
loan is subject to full underwriting — this is a demo, not a real offer.
"""


class LoanAgent(DepartmentAgent):
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(instructions=INSTRUCTIONS, chat_ctx=chat_ctx)
    department: str = "loan"

    def _get_product(self, product_type: str) -> dict | None:
        return store.find_one(
            "loans.json",
            lambda p: p["product_type"] == product_type,
            collection_key="loan_products",
        )

    @function_tool()
    async def check_loan_eligibility(
        self,
        context: RunContext[SessionUserData],
        product_type: str,
        monthly_income: float,
        requested_amount: float,
    ) -> dict:
        """Check basic mock eligibility for a loan product.

        Args:
            product_type: One of 'personal_loan', 'auto_loan', 'mortgage'.
            monthly_income: Customer's stated gross monthly income.
            requested_amount: The loan amount the customer wants.
        """
        product = self._get_product(product_type)
        if not product:
            return {"eligible": False, "reason": f"Unknown product type '{product_type}'."}

        reasons = []
        eligible = True

        if monthly_income < product["min_monthly_income"]:
            eligible = False
            reasons.append(
                f"Minimum monthly income for this product is {product['min_monthly_income']}."
            )
        if not (product["min_amount"] <= requested_amount <= product["max_amount"]):
            eligible = False
            reasons.append(
                f"Amount must be between {product['min_amount']} and {product['max_amount']}."
            )

        return {
            "eligible": eligible,
            "product": product["display_name"],
            "annual_interest_rate": product["annual_interest_rate"],
            "reasons": reasons or ["Meets basic mock eligibility criteria."],
        }

    @function_tool()
    async def calculate_loan_payment(
        self,
        context: RunContext[SessionUserData],
        product_type: str,
        amount: float,
        tenure_months: int,
    ) -> dict:
        """Estimate the monthly repayment for a loan using standard
        amortization math.

        Args:
            product_type: One of 'personal_loan', 'auto_loan', 'mortgage'.
            amount: Principal loan amount.
            tenure_months: Loan tenure in months.
        """
        product = self._get_product(product_type)
        if not product:
            return {"error": f"Unknown product type '{product_type}'."}

        annual_rate = product["annual_interest_rate"]
        monthly_rate = annual_rate / 12

        if monthly_rate == 0:
            monthly_payment = amount / tenure_months
        else:
            monthly_payment = (
                amount
                * monthly_rate
                * (1 + monthly_rate) ** tenure_months
                / ((1 + monthly_rate) ** tenure_months - 1)
            )

        total_repayment = monthly_payment * tenure_months
        total_interest = total_repayment - amount

        result = {
            "product": product["display_name"],
            "principal": round(amount, 2),
            "tenure_months": tenure_months,
            "annual_interest_rate": annual_rate,
            "estimated_monthly_payment": round(monthly_payment, 2),
            "estimated_total_interest": round(total_interest, 2),
            "estimated_total_repayment": round(total_repayment, 2),
        }
        logger.info("Loan calc: %s", result)
        return result

    @function_tool()
    async def create_loan_lead(
        self,
        context: RunContext[SessionUserData],
        product_type: str,
        amount: float,
        tenure_months: int,
        monthly_income: float,
        preferred_office: str,
        credit_authorization: bool,
        asset_value: float = 0.0,
    ) -> dict:
        """Create a mock loan lead for a human loan officer to follow up
        on, once the customer wants to proceed.

        Args:
            product_type: The type of loan requested.
            amount: Requested loan amount.
            tenure_months: Requested tenure in months.
            monthly_income: Customer's stated monthly income.
            preferred_office: The JMMB office branch they prefer.
            credit_authorization: True if they authorized checking their credit bureau report.
            asset_value: The value of the vehicle or property (default 0.0).
        """
        userdata = context.userdata
        lead = {
            "lead_id": f"LOAN-{uuid.uuid4().hex[:8].upper()}",
            "customer_id": userdata.customer_id,
            "customer_name": userdata.name,
            "phone": userdata.phone,
            "email": userdata.email,
            "product_type": product_type,
            "requested_amount": amount,
            "tenure_months": tenure_months,
            "monthly_income": monthly_income,
            "preferred_office": preferred_office,
            "credit_authorization": credit_authorization,
            "asset_value": asset_value,
            "status": "new",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        store.append_record("loans.json", lead, collection_key="leads")
        logger.info("Created loan lead: %s", lead["lead_id"])
        return lead

    @function_tool()
    async def transfer_to_financial_guidance(self, context: RunContext[SessionUserData]):
        """Hand off to the Financial Guidance specialist if the
        conversation shifts to investing/saving instead of borrowing."""
        from app.agents.financial_guidance import FinancialGuidanceAgent

        context.userdata.last_intent = "financial_guidance"
        context.userdata.record_visit("financial_guidance")
        logger.info("Routing: Loan -> Financial Guidance")
        return FinancialGuidanceAgent(chat_ctx=self.chat_ctx.copy(exclude_instructions=True)), (
            "Continue seamlessly in the same language the customer has been using. Help them explore their financial options."
        )

    # The transfer_to_supervisor and human_handoff tools are inherited from DepartmentAgent
