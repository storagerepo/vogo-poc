"""
supervisor.py
--------------
The Supervisor Agent — the entry point of the whole system and the heart of
the "Supervisor pattern" used in this POC.

Pattern summary
----------------
- The Supervisor is the FIRST agent the caller talks to. It greets the
  customer, listens, and classifies intent into Sales / Service / Finance.
- It does NOT execute domain tools itself (no vehicle search, no booking,
  no finance math). Its only job is: understand -> route -> hand off.
- Routing is implemented via LiveKit Agents' agent-handoff mechanism: a
  `function_tool` returns a NEW `Agent` instance (SalesAgent / ServiceAgent /
  FinanceAgent). The AgentSession swaps the active agent to that instance,
  carrying the conversation (chat history) forward automatically.
- Each department agent can hand the conversation BACK to the Supervisor
  (e.g. "actually I also want to ask about financing") via `return_to_supervisor`,
  or escalate straight to a human via `human_handoff` (defined on the shared
  DepartmentAgent base class).

This mirrors a real-world dealership call center: a receptionist/supervisor
triages the call and transfers it to the right specialist, and specialists
can transfer back to the supervisor or to a human when needed.
"""
from __future__ import annotations

from livekit.agents import Agent, RunContext, function_tool, llm

from app.config import settings
from app.utils.logger import get_logger

log = get_logger("agents.supervisor")

SUPERVISOR_INSTRUCTIONS = f"""
You are the AI assistant for {settings.DEALERSHIP_NAME}, answering an
inbound voice call on the website. Be warm, brief, and natural — this is a
spoken conversation, not a chat window.

Your job is to:
1. Greet the customer once, briefly, and ask how you can help them today and mention how you're helpful.
2. Listen to the customer's request and understand their intent.
3. Once you understand what they need, collect the customer's name, phone number, and email (ask for these one by one).
4. Send an OTP to their phone using the send_customer_otp tool.
5. Ask the customer for the OTP code they received and verify it using verify_customer_otp.
6. ONLY AFTER the phone is successfully verified, transition the conversation using the appropriate tools:
   - transfer_to_sales: buying, browsing, comparing, pricing, or test-driving a vehicle.
   - transfer_to_service: maintenance, repairs, oil changes, appointments for an
     existing vehicle.
   - transfer_to_finance: financing, loans, monthly payments, eligibility.
7. If the request is clearly outside Sales/Service/Finance, or the customer asks
   for a human directly, call human_handoff.

Do NOT attempt to answer detailed vehicle, service, or finance questions
yourself — always use the tools to transition the flow. NEVER tell the user
you are transferring them or routing them to a specialist. To the user, you are a
single unified assistant.
If it's unclear what the customer needs, ask ONE short
clarifying question before continuing.
"""


class SupervisorAgent(Agent):
    def __init__(self, chat_ctx: llm.ChatContext | None = None) -> None:
        super().__init__(instructions=SUPERVISOR_INSTRUCTIONS, chat_ctx=chat_ctx)

    async def on_enter(self) -> None:
        # generate_reply is not supported by Gemini 3.1 Live; 
        # initial greeting is handled via audio_trigger in main.py
        pass

    @function_tool()
    async def send_customer_otp(
        self, context: RunContext, phone: str, email: str | None = None
    ):
        """Send a verification code to the customer's phone number.

        Call this after collecting the customer's name, phone, and email.

        Args:
            phone: Customer's phone number.
            email: Customer's email address (optional).
        """
        from app.tools import common_tools
        return common_tools.send_customer_otp(phone=phone, email=email)

    @function_tool()
    async def verify_customer_otp(self, context: RunContext, phone: str, otp: str):
        """Verify the code the customer provides.

        Args:
            phone: The phone number the code was sent to.
            otp: The verification code the customer said.
        """
        from app.tools import common_tools
        return common_tools.verify_customer_otp(phone=phone, otp=otp)

    @function_tool()
    async def transfer_to_sales(self, context: RunContext):
        """Transfer the customer to the Sales specialist.

        Use for: finding a vehicle, comparing models, pricing, test drives,
        or general purchase interest.
        """
        from app.agents.sales_agent import SalesAgent

        log.info("Routing: Supervisor -> Sales")
        return SalesAgent(chat_ctx=self.chat_ctx.copy(exclude_instructions=True)), "Let me pull up that information for you."

    @function_tool()
    async def transfer_to_service(self, context: RunContext):
        """Transfer the customer to the Service specialist.

        Use for: maintenance, repairs, oil changes, or booking a service
        appointment for a vehicle they already own.
        """
        from app.agents.service_agent import ServiceAgent

        log.info("Routing: Supervisor -> Service")
        return ServiceAgent(chat_ctx=self.chat_ctx.copy(exclude_instructions=True)), "I can help you with your service needs. Let me check the details."

    @function_tool()
    async def transfer_to_finance(self, context: RunContext):
        """Transfer the customer to the Finance specialist.

        Use for: financing options, loan eligibility, or payment estimates.
        """
        from app.agents.finance_agent import FinanceAgent

        log.info("Routing: Supervisor -> Finance")
        return FinanceAgent(chat_ctx=self.chat_ctx.copy(exclude_instructions=True)), "Let's look at the financing options together."

    @function_tool()
    async def human_handoff(self, context: RunContext, reason: str, context_summary: str):
        """Escalate directly to a human when the request is outside Sales,
        Service, and Finance, or the customer explicitly asks for a person.

        Args:
            reason: Short reason for the handoff.
            context_summary: Summary of the conversation so far.
        """
        from app.tools import common_tools

        result = common_tools.human_handoff(
            team="sales", reason=reason, context_summary=context_summary
        )
        log.info("Supervisor human_handoff result: %s", result)
        return (
            "Let me connect you with a member of our team who can help with that. "
            "Tell the customer a human representative will join shortly."
        )
