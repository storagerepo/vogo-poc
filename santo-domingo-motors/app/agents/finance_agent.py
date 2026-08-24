"""
finance_agent.py
-----------------
Finance department agent — handles the complete financing flow:

Customer Details → OTP Verification → Vehicle Selection → Fixed 15% Initial
Payment → Bank Selection → Bank-Specific Financing Plans → Monthly Installment
Calculation → Finance Summary → Customer Confirmation → Finance Lead Creation.

All calculations are performed by backend tools (not the LLM). Vehicle prices,
bank rates, and terms come from data sources — the LLM never invents them.
"""
from __future__ import annotations

from livekit.agents import RunContext, function_tool, llm

from app.agents.base import DepartmentAgent
from app.tools import finance_tools
from app.utils.logger import get_logger

log = get_logger("agents.finance")

FINANCE_INSTRUCTIONS = """
You are the AI assistant for Santo Domingo Motors, speaking with a
customer over a live voice call. Do NOT introduce yourself or greet the customer,
as they are already in the middle of a conversation with you. Seamlessly continue
the conversation based on the context.

YOUR JOB:
You guide the customer through a financing estimate step by step. Follow this
exact progressive flow — collect one piece of information at a time, never
ask for everything at once:

CRITICAL: The customer's name, phone, email, and phone verification are ALREADY
completed and verified. NEVER ask the customer for their name, phone, or email under any circumstance. Extract them directly from the conversation history when calling tools like create_finance_lead.

STEP 1 — VEHICLE SELECTION:
  a) Ask which vehicle brand the customer is interested in (unless already known).
  b) Call get_vehicle_brands to confirm the brand exists.
  c) Ask which model they want, after calling get_vehicle_models to show
     available models for that brand.
  d) Call get_vehicle_details to get the vehicle price. Tell the customer
     the price in DOP.
  e) NEVER invent a vehicle price — it must come from get_vehicle_details.
  f) If the vehicle has no listed price, tell the customer and offer to
     connect them with the dealership.

STEP 2 — INITIAL PAYMENT:
  The initial/down payment is FIXED at 15%. Do NOT ask the customer how much
  they want to pay. Simply state: "The required initial payment is 15% of the
  vehicle price." Then state the calculated amount. The backend enforces this.

STEP 3 — BANK SELECTION:
  a) Call get_financing_banks to get the list of banks.
  b) Present the banks clearly: Motor Credit, Banco Popular, Scotiabank,
     BanReservas, Santa Cruz, BHD Bank.
  c) Ask the customer which bank they'd like to consider.

STEP 4 — FINANCING PLAN SELECTION:
  a) Call get_financing_plans with the selected bank to get available plans.
  b) Present the plans clearly, including term and interest rate.
     Example: "Motor Credit offers a 2-year fixed rate at 13.45% and a 3-year
     fixed rate at 14.45%. Which option would you prefer?"
  c) NEVER invent interest rates or terms — they must come from the tool.

STEP 5 — CALCULATION:
  a) Call calculate_financing with the vehicle price, 15% initial payment,
     the bank's interest rate, and the selected term.
  b) The tool returns the exact monthly payment — do NOT calculate it yourself.

STEP 6 — FINANCE SUMMARY:
  Present a clear, complete verbal summary containing:
  - Customer name
  - Vehicle brand, model, and price in DOP
  - Initial payment: 15%, and the amount in DOP
  - Amount financed in DOP
  - Selected bank name
  - Interest rate and rate type (fixed/variable)
  - Financing term
  - Estimated monthly payment in DOP
  - Estimated total interest in DOP
  - Estimated total repayment in DOP

  ALWAYS end the summary with a disclaimer such as:
  "Please note that this is an estimated financing calculation for reference
  only. The final interest rate, financing terms and approval are subject to
  the financing institution's conditions."

  NEVER say "Your financing is approved."

STEP 7 — CONFIRMATION:
  Ask the customer if they want to proceed with this financing request.

  If YES:
    Call create_finance_lead with all the details.
    If the lead is created successfully, confirm to the customer:
    "Your financing request has been submitted. Our finance team will follow
    up with you at [phone] to proceed with the next steps."
    If lead creation fails, apologize and offer to connect with a human.

  If NO:
    Ask what they'd like to change — vehicle, bank, or term.
    Only recalculate the affected parts. Do NOT re-ask for customer info.
    - If changing vehicle: go back to Step 1.
    - If changing bank: go back to Step 3.
    - If changing term: go back to Step 4.

IMPORTANT RULES:
- Keep responses short and conversational — this is a spoken conversation.
- Ask ONE question at a time.
- Do not repeat information already collected.
- All monetary amounts presented to the customer must be in DOP (Dominican Pesos).
- If the customer asks "how much will I pay per month?", calculate using the
  selected vehicle, bank, rate, term, and fixed 15% initial payment.
- If the customer asks to return to vehicle sales, vehicle details, another vehicle,
  test drive, or sales-related information, call transfer_to_sales to access sales tools.
- If asked something outside Finance (like Service), or the customer wants a human,
  call human_handoff or return_to_supervisor as appropriate.
"""


class FinanceAgent(DepartmentAgent):
    department = "finance"

    def __init__(self, chat_ctx: llm.ChatContext | None = None) -> None:
        super().__init__(instructions=FINANCE_INSTRUCTIONS, chat_ctx=chat_ctx)

    @function_tool()
    async def transfer_to_sales(self, context: RunContext):
        """Access sales tools for vehicle sales, test drives, or other vehicle details."""
        from app.agents.sales_agent import SalesAgent

        log.info("Routing: Finance -> Sales")
        agent = SalesAgent(chat_ctx=self.chat_ctx.copy(exclude_instructions=True))
       
        return agent, "Let's go back to the vehicle details."

    # ------------------------------------------------------------------
    # Vehicle lookup tools
    # ------------------------------------------------------------------

    @function_tool()
    async def get_vehicle_brands(self, context: RunContext):
        """Get all available vehicle brands."""
        return finance_tools.get_vehicle_brands()

    @function_tool()
    async def get_vehicle_models(self, context: RunContext, brand: str):
        """Get available models for a vehicle brand.

        Args:
            brand: The vehicle brand name, e.g. "Chevrolet".
        """
        return finance_tools.get_vehicle_models(brand=brand)

    @function_tool()
    async def get_vehicle_details(
        self, context: RunContext, brand: str, model: str
    ):
        """Get full details and price for a specific vehicle.

        Args:
            brand: The vehicle brand name.
            model: The vehicle model name.
        """
        return finance_tools.get_vehicle_details(brand=brand, model=model)

    # ------------------------------------------------------------------
    # Bank & plan tools
    # ------------------------------------------------------------------

    @function_tool()
    async def get_financing_banks(self, context: RunContext):
        """Get the list of available financing banks."""
        return finance_tools.get_financing_banks()

    @function_tool()
    async def get_financing_plans(
        self,
        context: RunContext,
        bank_id: str,
        vehicle_type: str = "new",
        usage: str = "personal",
    ):
        """Get financing plans for a specific bank.

        Args:
            bank_id: The bank identifier, e.g. "motor_credit".
            vehicle_type: "new" or "used" (default "new").
            usage: "personal" or "commercial" (default "personal").
        """
        return finance_tools.get_financing_plans(
            bank_id=bank_id, vehicle_type=vehicle_type, usage=usage
        )

    # ------------------------------------------------------------------
    # Calculation tool
    # ------------------------------------------------------------------

    @function_tool()
    async def calculate_financing(
        self,
        context: RunContext,
        vehicle_price_usd: float,
        initial_payment_percent: int,
        interest_rate: float,
        term_months: int,
    ):
        """Calculate the estimated monthly payment using standard amortization.

        The 15% initial payment is enforced by the backend — always pass 15.

        Args:
            vehicle_price_usd: Vehicle price in USD from the vehicle catalog.
            initial_payment_percent: Must be 15 (enforced by backend).
            interest_rate: Annual interest rate from the bank's plan.
            term_months: Loan term in months from the bank's plan.
        """
        return finance_tools.calculate_financing(
            vehicle_price_usd=vehicle_price_usd,
            initial_payment_percent=initial_payment_percent,
            interest_rate=interest_rate,
            term_months=term_months,
        )

    # ------------------------------------------------------------------
    # Lead creation tool
    # ------------------------------------------------------------------

    @function_tool()
    async def create_finance_lead(
        self,
        context: RunContext,
        customer_name: str,
        phone: str,
        email: str | None,
        phone_verified: bool,
        vehicle_brand: str,
        vehicle_model: str,
        vehicle_id: str,
        vehicle_price_usd: float,
        bank_id: str,
        bank_name: str,
        initial_payment_percent: int,
        initial_payment_dop: float,
        financed_amount_dop: float,
        interest_rate: float,
        rate_type: str,
        term_months: int,
        monthly_payment_dop: float,
        total_interest_dop: float,
        total_payment_dop: float,
        idempotency_key: str | None = None,
    ):
        """Create a finance lead after the customer confirms.

        Only call this when the customer explicitly agrees to proceed. If the
        lead already exists for this request (idempotency), the existing lead
        is returned.

        Args:
            customer_name: Customer's full name.
            phone: Customer's verified phone number.
            email: Customer's email address.
            phone_verified: True if OTP verified.
            vehicle_brand: Selected vehicle brand.
            vehicle_model: Selected vehicle model.
            vehicle_id: Vehicle ID from catalog.
            vehicle_price_usd: Vehicle price in USD.
            bank_id: Selected bank ID.
            bank_name: Selected bank display name.
            initial_payment_percent: Always 15.
            initial_payment_dop: Initial payment in DOP.
            financed_amount_dop: Amount financed in DOP.
            interest_rate: Annual interest rate.
            rate_type: "fixed" or "variable".
            term_months: Financing term in months.
            monthly_payment_dop: Estimated monthly payment in DOP.
            total_interest_dop: Total estimated interest in DOP.
            total_payment_dop: Total estimated repayment in DOP.
            idempotency_key: Optional unique key for this request.
        """
        return finance_tools.create_finance_lead(
            customer_name=customer_name,
            phone=phone,
            email=email,
            phone_verified=phone_verified,
            vehicle_brand=vehicle_brand,
            vehicle_model=vehicle_model,
            vehicle_id=vehicle_id,
            vehicle_price_usd=vehicle_price_usd,
            bank_id=bank_id,
            bank_name=bank_name,
            initial_payment_percent=initial_payment_percent,
            initial_payment_dop=initial_payment_dop,
            financed_amount_dop=financed_amount_dop,
            interest_rate=interest_rate,
            rate_type=rate_type,
            term_months=term_months,
            monthly_payment_dop=monthly_payment_dop,
            total_interest_dop=total_interest_dop,
            total_payment_dop=total_payment_dop,
            idempotency_key=idempotency_key,
        )
