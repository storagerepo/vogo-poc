"""
agents/financial_guidance.py

Handles general financial questions, basic product info, and simple
recommendations against the mock financial_products.json catalog.
"""
from __future__ import annotations

import logging
import uuid

from livekit.agents import RunContext, function_tool

from app.agents.base import DepartmentAgent
from app.core import store
from app.core.userdata import SessionUserData
from app.prompts.base import BANK_CONTEXT, VOICE_STYLE_GUIDE

logger = logging.getLogger("jmmb-financial-guidance")

INSTRUCTIONS = f"""
{BANK_CONTEXT}
{VOICE_STYLE_GUIDE}

You are SARA, now helping the customer with financial guidance. The
customer has already been greeted, onboarded, and verified — do not ask
for their name or verify them again. Do NOT introduce yourself or greet the customer, as they
are already in the middle of a conversation with you. Seamlessly continue the
conversation based on the context.

Your job:
- Understand what the customer is trying to achieve (e.g. saving for an
  emergency, growing wealth, saving for a child's education, low-risk
  parking of cash).
- Ask brief qualifying questions if needed: their goal, their rough time
  horizon, and comfort with risk (low, medium, high).
- Use `get_financial_products` to see the catalog, and
  `recommend_product` to propose the single best-fit product, explaining
  briefly why it fits.
- If the customer starts asking about borrowing money, loan amounts, or
  monthly payments instead of investing/saving, use
  `transfer_to_loan` to smoothly shift to helping them with loans.
- If the customer wants deeper consultation, investment advice, or asks
  to speak to a financial advisor/expert, use `schedule_advisory_appointment`
  to book an appointment for them with a generic advisor role (e.g., Wealth Advisor).
- If the customer is done or asks for something outside financial
  guidance or loans (service appointment, security report), use
  `return_to_supervisor`.
"""


class FinancialGuidanceAgent(DepartmentAgent):
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(instructions=INSTRUCTIONS, chat_ctx=chat_ctx)
    department: str = "financial guidance"



    @function_tool()
    async def get_financial_products(
        self, context: RunContext[SessionUserData], category: str | None = None
    ) -> list[dict]:
        """List available financial products, optionally filtered by
        category (e.g. 'savings', 'fixed_income', 'mutual_fund',
        'equity_fund', 'goal_based').

        Args:
            category: Optional category filter.
        """
        products = store.find_all("financial_products.json")
        if category:
            products = [p for p in products if p["category"] == category]
        return products

    @function_tool()
    async def recommend_product(
        self,
        context: RunContext[SessionUserData],
        goal: str,
        risk_tolerance: str,
        horizon: str,
    ) -> dict:
        """Recommend the single best-fit financial product based on the
        customer's stated goal, risk tolerance, and time horizon.

        Args:
            goal: What the customer wants to achieve, e.g. 'emergency fund',
                'retirement', 'education planning', 'wealth building'.
            risk_tolerance: One of 'low', 'medium', or 'high'.
            horizon: Rough time horizon, e.g. 'short-term', '5+ years'.
        """
        products = store.find_all("financial_products.json")
        risk_tolerance = risk_tolerance.lower()

        # Simple rule-based mock "recommendation engine" — good enough for
        # a POC demo, not a real advisory model.
        candidates = [p for p in products if p["risk_level"] == risk_tolerance]
        if not candidates:
            candidates = products

        goal_matches = [
            p for p in candidates if any(goal.lower() in tag.lower() for tag in p["best_for"])
        ]
        best = goal_matches[0] if goal_matches else candidates[0]

        logger.info(
            "Recommended %s for goal=%r risk=%r horizon=%r",
            best["name"],
            goal,
            risk_tolerance,
            horizon,
        )
        return best

    @function_tool()
    async def schedule_advisory_appointment(
        self,
        context: RunContext[SessionUserData],
        advisor_role: str,
        date: str,
        time: str,
        topic: str,
    ) -> str:
        """Schedule an appointment with a financial advisor for the customer.
        Use this if the customer asks for a deeper consultation, investment 
        advice, or explicitly asks to speak to an expert/advisor.

        Args:
            advisor_role: The generic role of the advisor (e.g., "Wealth Advisor", "Investment Specialist").
            date: Preferred date for the appointment (e.g., "2026-08-25").
            time: Preferred time for the appointment (e.g., "10:00 AM").
            topic: A brief summary of what the customer wants to discuss.
        """
        appointment_id = str(uuid.uuid4())[:8]
        
        record = {
            "appointment_id": appointment_id,
            "customer_id": context.userdata.customer_id,
            "customer_name": context.userdata.name,
            "advisor_role": advisor_role,
            "date": date,
            "time": time,
            "topic": topic,
            "status": "scheduled"
        }
        
        store.append_record("appointments.json", record)
        
        logger.info("Scheduled advisory appointment: %r", record)
        return f"Successfully scheduled a {advisor_role} appointment on {date} at {time}. Appointment ID is {appointment_id}."

    @function_tool()
    async def transfer_to_loan(self, context: RunContext[SessionUserData]):
        """Hand off directly to the Loan specialist, e.g. when the
        customer starts asking about financing/borrowing instead of
        saving or investing. No re-verification needed."""
        from app.agents.loan import LoanAgent

        context.userdata.last_intent = "loan"
        logger.info("Routing: Financial Guidance -> Loan")
        return LoanAgent(chat_ctx=self.chat_ctx), (
            "Absolutely, let me help you with the loan details."
        )

    # The transfer_to_supervisor and human_handoff tools are inherited from DepartmentAgent
