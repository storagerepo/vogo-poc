"""
agents/supervisor.py

The Supervisor Agent is the single entry point of the whole system:
    - Greets the customer
    - Runs basic onboarding (name / phone / email)
    - Generates + verifies a mock OTP
    - Detects intent and routes to the right specialist by returning a
      new Agent instance from a function tool (a "handoff")

Everything it collects lives on `context.userdata` (SessionUserData), so
every specialist agent can see it without re-asking.
"""
from __future__ import annotations

import logging
import uuid

from livekit.agents import Agent, RunContext, function_tool

from app.core import store
from app.core.userdata import SessionUserData
from app.prompts.base import BANK_CONTEXT, VOICE_STYLE_GUIDE
from app.services import otp_service

logger = logging.getLogger("jmmb-supervisor")

INSTRUCTIONS = f"""
{BANK_CONTEXT}
{VOICE_STYLE_GUIDE}

You are SARA, handling the initial greeting, onboarding, and verification
stage of the conversation. Your job, in order:

1. GREETING: Warmly greet the customer as SARA, the JMMB Banking
   Assistant, and briefly mention you can help with financial guidance,
   loans.

2. ONBOARDING & VERIFICATION: Before helping with any topic, collect the 
   customer's full name, phone number, and email address, one at a time.
   Confirm each piece back to the customer as you go if you're not fully
   sure you heard it correctly.
   
   Once you have all three, call `send_otp` to send a verification code.
   Tell the customer a 4-digit code was sent to their phone and ask them
   to provide it. When they provide the code, call `verify_otp` with that
   code and their phone number. If verification fails, allow up to 3
   attempts before asking them to contact JMMB support.

4. ROUTING: Once verified, figure out what the customer actually needs
   and use the appropriate routing tool:
   - `route_to_financial_guidance` for general financial questions or
     product recommendations
   - `route_to_loan` for loan inquiries, eligibility, amounts, tenure,
     interest rate, or monthly payment questions

   Do not attempt to answer those topics yourself — always route once
   you're confident about the customer's intent. You can ask one short
   clarifying question first if the intent is ambiguous.

IMPORTANT: Never tell the customer you are "transferring" or "connecting"
them to anyone. You are SARA the whole time. Just smoothly shift to
helping them with the new topic.

Never skip verification before routing, unless the customer is already
marked verified in session data.
"""


class SupervisorAgent(Agent):
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(instructions=INSTRUCTIONS, chat_ctx=chat_ctx)

    async def on_enter(self) -> None:
        userdata: SessionUserData = self.session.userdata
        userdata.record_visit("supervisor")
        # Let the model greet first, rather than us hardcoding a script.
        # generate_reply is not supported by Gemini 3.1 Live; 
        # the agent will respond automatically to the first user input.
        # self.session.generate_reply()

    # ------------------------------------------------------------------
    # Onboarding & Verification tools
    # ------------------------------------------------------------------
    @function_tool()
    async def send_otp(
        self,
        context: RunContext[SessionUserData],
        name: str,
        phone: str,
        email: str,
    ) -> str:
        """Send a 4-digit verification code to the customer's phone number.
        Call this after collecting the customer's name, phone, and email.

        Args:
            name: Customer's full name.
            phone: Customer's phone number, digits only where possible.
            email: Customer's email address.
        """
        userdata = context.userdata
        userdata.name = name
        userdata.phone = phone
        userdata.email = email

        # Look for an existing mock customer record, else "create" one.
        existing = store.find_one(
            "customers.json", lambda c: c.get("phone") == phone or c.get("email") == email
        )
        if existing:
            userdata.customer_id = existing["customer_id"]
        else:
            new_customer = {
                "customer_id": f"CUST-{uuid.uuid4().hex[:6].upper()}",
                "name": name,
                "phone": phone,
                "email": email,
                "created_at": userdata.session_started_at,
            }
            store.append_record("customers.json", new_customer)
            userdata.customer_id = new_customer["customer_id"]

        logger.info("Onboarded customer: %s", userdata.summary())
        
        result = otp_service.send_otp(phone=userdata.phone, email=userdata.email)
        logger.info("send_otp result for phone=%r: %s", userdata.phone, result)
        if result.get("success"):
            debug_otp = result.get("_debug_otp", "1234")
            return f"Saved details. A verification code has been sent.  Ask the customer to read it back."
        return result.get("message", "Failed to send OTP.")

    @function_tool()
    async def verify_otp(self, context: RunContext[SessionUserData], phone: str, code: str) -> str:
        """Verify the OTP code the customer read back to you.

        Args:
            phone: Customer's phone number.
            code: The 4-digit verification code.
        """
        userdata = context.userdata
        result = otp_service.verify_otp(phone=phone, otp=code)
        
        # if result.get("verified"):
        userdata.verified = True
        return "Verification successful. The customer is now verified for this session."
            
        # reason = result.get("reason")
        # if reason == "max_attempts":
        #     return (
        #         "Verification failed after max attempts. Apologize and advise the customer "
        #         "to contact JMMB support directly to verify their identity."
        #     )
        # elif "remaining_attempts" in result:
        #     return f"That code did not match. {result['remaining_attempts']} attempt(s) remaining — ask them to try again."
        # return result.get("message", "Verification failed.")

    # ------------------------------------------------------------------
    # Routing / handoff tools
    # ------------------------------------------------------------------
    def _require_verified(self, context: RunContext[SessionUserData]) -> str | None:
        if not context.userdata.verified:
            return (
                "The customer is not verified yet. Do not route them — finish onboarding "
                "and OTP verification first."
            )
        return None

    @function_tool()
    async def route_to_financial_guidance(self, context: RunContext[SessionUserData]):
        """Hand off to the Financial Guidance specialist for general
        financial questions or product recommendations."""
        blocker = self._require_verified(context)
        if blocker:
            return blocker

        from app.agents.financial_guidance import FinancialGuidanceAgent

        context.userdata.last_intent = "financial_guidance"
        context.userdata.record_visit("financial_guidance")
        logger.info("Routing: Supervisor -> Finance")
        return FinancialGuidanceAgent(chat_ctx=self.chat_ctx.copy(exclude_instructions=True)), "Continue seamlessly in the same language the customer has been using. Help them explore their financial options."

    @function_tool()
    async def route_to_loan(self, context: RunContext[SessionUserData]):
        """Hand off to the Loan specialist for loan eligibility, amount,
        tenure, interest rate, or repayment questions."""
        blocker = self._require_verified(context)
        if blocker:
            return blocker

        from app.agents.loan import LoanAgent

        context.userdata.last_intent = "loan"
        context.userdata.record_visit("loan")
        logger.info("Routing: Supervisor -> Loan")
        return LoanAgent(chat_ctx=self.chat_ctx.copy(exclude_instructions=True)), "Continue seamlessly in the same language the customer has been using. Help them with their loan inquiry."

    # @function_tool()
    # async def route_to_service(self, context: RunContext[SessionUserData]):
    #     """Hand off to the Service specialist for branch visits,
    #     appointments, or general service requests."""
    #     blocker = self._require_verified(context)
    #     if blocker:
    #         return blocker

    #     from app.agents.service import ServiceAgent

    #     context.userdata.last_intent = "service"
    #     logger.info("Routing: Supervisor -> Service")
    #     return ServiceAgent(chat_ctx=self.chat_ctx.copy(exclude_instructions=True)), "Continue seamlessly in the same language the customer has been using. Help them with their service request."

    # @function_tool()
    # async def route_to_security(self, context: RunContext[SessionUserData]):
    #     """Hand off to the Security specialist for suspicious transactions
    #     or Security/security concerns."""
    #     blocker = self._require_verified(context)
    #     if blocker:
    #         return blocker

    #     from app.agents.Security import SecurityAgent

    #     context.userdata.last_intent = "Security"
    #     logger.info("Routing: Supervisor -> Security")
    #     return SecurityAgent(chat_ctx=self.chat_ctx.copy(exclude_instructions=True)), "Continue seamlessly in the same language the customer has been using. Look into this security matter for them."
