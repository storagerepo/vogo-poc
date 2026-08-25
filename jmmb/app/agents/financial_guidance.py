"""
agents/financial_guidance.py

Goal-first financial guidance agent for the JMMB Voice POC.

Instead of jumping straight to a product recommendation, SARA first
understands the customer's financial goal, classifies the underlying
need (saving, investing, borrowing, or general guidance), asks only
the minimum qualifying questions, and then recommends the best-fit
product from the mock financial_products.json catalog — explaining
*why* it fits in plain language.

Borrowing/financing intent is detected early and routed to the Loan
agent via `transfer_to_loan`.
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

# ── Goal-classification keyword map ──────────────────────────────────
# Maps goal categories to keyword sets used by `classify_financial_goal`.
# Each entry: category_key -> (display_label, need_type, keyword_set,
#                               suggested_product_categories)

_GOAL_KEYWORDS: dict[str, tuple[str, str, set[str], list[str]]] = {
    "emergency_fund": (
        "Emergency fund",
        "saving",
        {"emergency", "rainy day", "unforeseen", "unexpected", "safety net", "just in case"},
        ["savings"],
    ),
    "general_savings": (
        "General savings",
        "saving",
        {"save", "saving", "savings", "put away", "set aside", "keep money", "safe place"},
        ["savings"],
    ),
    "grow_money": (
        "Grow existing money",
        "investing",
        {"grow", "growth", "increase", "multiply", "return", "returns", "interest", "yield"},
        ["savings", "fixed_income", "mutual_fund"],
    ),
    "wealth_building": (
        "Wealth building",
        "investing",
        {"wealth", "portfolio", "invest", "investing", "investment", "build wealth", "long-term growth"},
        ["mutual_fund", "equity_fund"],
    ),
    "education": (
        "Education",
        "saving",
        {"education", "school", "college", "university", "tuition", "children", "child", "kid", "study"},
        ["goal_based"],
    ),
    "retirement": (
        "Retirement",
        "investing",
        {"retire", "retirement", "pension", "old age", "after work"},
        ["mutual_fund", "equity_fund"],
    ),
    "vehicle": (
        "Acquire a vehicle",
        "guidance",
        {"car", "vehicle", "auto", "truck", "motorcycle", "motor"},
        ["savings", "fixed_income"],
    ),
    "home": (
        "Acquire a home",
        "guidance",
        {"house", "home", "apartment", "property", "real estate", "condo", "dwelling"},
        ["fixed_income", "mutual_fund"],
    ),
    "business": (
        "Business financing",
        "borrowing",
        {"business", "company", "startup", "venture", "commercial", "inventory", "equipment", "working capital", "expand"},
        [],
    ),
    "short_term_cash": (
        "Short-term cash need",
        "borrowing",
        {"quick cash", "short-term", "urgent", "need money", "cash now", "immediate"},
        [],
    ),
    "wedding": (
        "Wedding planning",
        "saving",
        {"wedding", "marriage", "ceremony", "reception"},
        ["savings", "fixed_income"],
    ),
    "long_term_investment": (
        "Long-term investment",
        "investing",
        {"long term", "long-term", "years", "decade", "future"},
        ["mutual_fund", "equity_fund", "fixed_income"],
    ),
}

# Keywords that signal borrowing/financing intent — triggers loan routing.
_BORROWING_KEYWORDS: set[str] = {
    "loan", "borrow", "financing", "finance", "mortgage", "monthly payment",
    "installment", "instalment", "credit", "lend", "lending", "how much can i borrow",
    "debt", "repayment",
}

# ── Horizon helpers for scoring ──────────────────────────────────────
_SHORT_HORIZON_CATEGORIES = {"savings", "goal_based"}
_MEDIUM_HORIZON_CATEGORIES = {"savings", "fixed_income", "goal_based"}
_LONG_HORIZON_CATEGORIES = {"fixed_income", "mutual_fund", "equity_fund"}

_HIGH_LIQUIDITY_CATEGORIES = {"savings"}
_LOW_LIQUIDITY_CATEGORIES = {"fixed_income", "mutual_fund", "equity_fund", "goal_based"}

INSTRUCTIONS = f"""
{BANK_CONTEXT}
{VOICE_STYLE_GUIDE}

You are SARA, now helping the customer with financial guidance. The
customer has already been greeted, onboarded, and verified — do NOT ask
for their name, phone, email, or OTP again. Do NOT introduce yourself
or greet the customer. They are already in the middle of a conversation
with you. Seamlessly continue based on the context.

─── YOUR CONVERSATION FLOW ───

Follow this flow naturally — do NOT skip steps or jump straight to a
product recommendation:

1. UNDERSTAND THE GOAL
   Listen to what the customer says and understand their financial goal.
   Recognise goals expressed in natural language. Examples:
   - "I want to buy a car" → vehicle-related financial goal
   - "I want to buy a house" → home-related financial goal
   - "I have some money and want it to grow" → investment / savings growth
   - "I want to keep money safe for emergencies" → emergency fund
   - "I need money for my business" → business financing

2. CLASSIFY THE GOAL
   Use `classify_financial_goal` with the customer's statement. This
   tells you the goal category, need type (saving / investing /
   borrowing / guidance), and whether to route to loans.

3. ROUTE IF BORROWING
   If the customer clearly wants to borrow, finance, get a loan, make
   monthly payments, check loan eligibility, get a mortgage, or finance
   a vehicle/home/business — use `transfer_to_loan` IMMEDIATELY. Do NOT
   continue recommending savings/investment products.
   Examples that should route to loans:
   - "I need a loan."
   - "How much can I borrow?"
   - "What would my monthly payment be?"
   - "I want financing for a car."
   - "Can I get a mortgage?"
   - "I need money for my business."

4. CLARIFY AMBIGUOUS GOALS
   If the goal could mean saving OR financing (e.g. "I want to buy a
   car"), ask ONE clarifying question:
   "Are you looking to finance the vehicle, or are you planning to
    save toward the purchase?"
   Then route or continue accordingly.

5. ASK QUALIFYING QUESTIONS (only what's needed)
   For saving / investing goals, you may need to understand:
   a) What is the money for? (if not already clear)
   b) When will they need it? (time horizon)
   c) Do they need easy access to the money? (liquidity)

   RULES:
   - Ask ONE question at a time.
   - Never interrogate — ask only what you actually need.
   - If the customer has already told you enough, skip to recommending.
   - Do NOT ask the customer about risk tolerance, risk level, or risk
     comfort. Never ask "What is your risk tolerance?" or "Are you
     low, medium, or high risk?" — risk is explained, not collected.

6. RECOMMEND A PRODUCT
   Use `recommend_product` with whatever qualifying information you
   have gathered. The tool will find the best-fit product.

   When presenting the recommendation:
   - Briefly explain WHY this product fits the customer's situation.
   - Use language like: "Based on what you've told me, this may be a
     good fit because…"
   - NEVER say "This is definitely the best product for you."
   - NEVER claim a product is guaranteed to be the best financial
     decision.
   - Do NOT dump a list of products. Recommend ONE product.

7. OFFER NEXT STEPS
   After recommending, ask if they'd like more details, want to explore
   other options, or would prefer to speak with an advisor. Do NOT
   automatically schedule an appointment.

─── RISK HANDLING ───

Do NOT ask the customer to self-select a risk level. Instead, explain
risk naturally based on the product being discussed.

When recommending or comparing products, briefly explain relevant
trade-offs in plain language. Factors you can mention:
- Potential return vs. uncertainty
- Whether the investment can lose value
- How time horizon affects ability to ride out fluctuations
- Whether access to money is easy or locked for a fixed term
- Whether returns are predictable (savings/fixed-income) or variable
  (market-based investments)
- Whether the money's purpose (emergency, near-term expense, long-term
  growth) affects what type of product is appropriate
- How spreading money across options can reduce concentration risk

Do NOT turn risk into a questionnaire. Weave it into the conversation.
For example, if a customer wants to grow RD$500,000:
  "If you may need the money soon, keeping some in an accessible
   savings option can be useful. Investments with higher growth
   potential can fluctuate more and are generally better suited to
   money you can leave invested for longer."
Then ask the next useful question: "How soon might you need access?"

Do NOT make guaranteed-return claims or present a product as risk-free
unless the product data explicitly supports that statement.

─── ADVISOR APPOINTMENTS ───

Use `schedule_advisory_appointment` ONLY when:
- The customer explicitly asks to speak to an advisor / expert.
- The customer asks for deeper investment guidance or financial planning.
- The situation is clearly beyond basic POC guidance capability.
When scheduling, collect only the information needed (date, time, topic).
Do NOT automatically schedule after every recommendation.

─── PRODUCT CATEGORIES (for reference) ───

The catalog includes these types of products:
- Savings accounts
- Certificates / fixed-income products
- Investment funds (mutual funds)
- Securities / equity funds
- Goal-based investment solutions

Do NOT invent products that are not in the catalog.
Do NOT mention product IDs, JSON, catalog, rule engine, or any internal
implementation details to the customer.

─── CONVERSATION STYLE ───

- Keep responses short: 1–3 sentences per turn.
- Ask one question at a time.
- Speak naturally and conversationally.
- Give simple explanations — do not sound like a financial textbook.
- Do not expose internal tool names.
- If the customer is done or asks for something outside financial
  guidance or loans (service appointment, security concern), use
  `return_to_supervisor`.
"""


class FinancialGuidanceAgent(DepartmentAgent):
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(instructions=INSTRUCTIONS, chat_ctx=chat_ctx)
    department: str = "financial guidance"

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    @function_tool()
    async def classify_financial_goal(
        self,
        context: RunContext[SessionUserData],
        customer_statement: str,
    ) -> dict:
        """Classify the customer's financial goal from their natural-
        language statement into a structured category and need type.

        Call this early in the conversation once you understand what the
        customer wants to achieve. The result tells you the goal
        category, whether the customer needs saving, investing,
        borrowing, or general guidance, and whether you should route
        to the Loan agent.

        Args:
            customer_statement: What the customer said about their
                financial goal, in their own words.
        """
        statement_lower = customer_statement.lower()

        # --- Check for explicit borrowing intent first ---
        if any(kw in statement_lower for kw in _BORROWING_KEYWORDS):
            # Determine a more specific borrowing category if possible
            category = "short_term_cash"
            if any(w in statement_lower for w in ("car", "vehicle", "auto", "truck")):
                category = "vehicle"
            elif any(w in statement_lower for w in ("house", "home", "property", "mortgage", "apartment")):
                category = "home"
            elif any(w in statement_lower for w in ("business", "company", "commercial", "inventory", "equipment")):
                category = "business"

            label = _GOAL_KEYWORDS.get(category, ("Borrowing / financing", "borrowing", set(), []))[0]
            result = {
                "goal_category": category,
                "goal_label": label,
                "need_type": "borrowing",
                "should_transfer_to_loan": True,
                "suggested_product_categories": [],
                "confidence": "high",
            }
            logger.info("Goal classified: %r → %s (borrowing)", customer_statement, category)
            return result

        # --- Match against goal keyword map ---
        best_category = "other"
        best_score = 0
        for cat_key, (label, need, keywords, prod_cats) in _GOAL_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in statement_lower)
            if score > best_score:
                best_score = score
                best_category = cat_key

        if best_category != "other" and best_score > 0:
            label, need_type, _, prod_cats = _GOAL_KEYWORDS[best_category]
        else:
            # Fallback: check against financial_goals.json names
            goals = store.find_all("financial_goals.json")
            for g in goals:
                if any(word in statement_lower for word in g["name"].lower().split()):
                    best_category = g["category"]
                    label = g["name"]
                    need_type = "saving" if g["category"] in ("savings", "event") else "guidance"
                    prod_cats = [
                        p["category"]
                        for pid in g.get("related_products", [])
                        for p in store.find_all("financial_products.json")
                        if p["product_id"] == pid
                    ]
                    break
            else:
                label = "Other financial goal"
                need_type = "guidance"
                prod_cats = []

        result = {
            "goal_category": best_category,
            "goal_label": label,
            "need_type": need_type,
            "should_transfer_to_loan": need_type == "borrowing",
            "suggested_product_categories": prod_cats,
            "confidence": "high" if best_score >= 2 else ("medium" if best_score == 1 else "low"),
        }
        logger.info("Goal classified: %r → %s (%s)", customer_statement, best_category, need_type)
        return result

    @function_tool()
    async def get_financial_products(
        self, context: RunContext[SessionUserData], category: str | None = None
    ) -> list[dict]:
        """List available financial products from the catalog, optionally
        filtered by category.

        Supported categories: 'savings', 'fixed_income', 'mutual_fund',
        'equity_fund', 'goal_based'.

        Use this to browse the catalog when you need to see what's
        available. For a tailored recommendation, use `recommend_product`
        instead.

        Args:
            category: Optional category filter (e.g. 'savings').
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
        need_type: str,
        horizon: str = "",
        liquidity_need: str = "",
    ) -> dict:
        """Recommend the single best-fit financial product based on the
        customer's goal and qualifying information.

        The recommendation engine prioritises:
        1. Goal / purpose (matched against each product's 'best_for' tags)
        2. Product category vs. need type (saving → savings category, etc.)
        3. Time horizon (short → savings; long → funds/fixed-income)
        4. Liquidity requirement (high → savings; low → deposits/funds)
        5. Inferred risk suitability (derived from need type and horizon;
           risk is never asked directly from the customer)

        Only pass the parameters you have actually gathered from the
        customer. The engine works without optional fields.

        Args:
            goal: What the customer wants to achieve, e.g. 'emergency
                fund', 'retirement', 'education', 'wealth building',
                'grow money', 'acquire vehicle', 'acquire home'.
            need_type: One of 'saving', 'investing', 'guidance'. Comes
                from `classify_financial_goal`.
            horizon: Rough time horizon if known, e.g. 'short-term',
                'medium-term', '5+ years', 'long-term'. Empty string if
                not yet discussed.
            liquidity_need: 'high' if the customer needs quick access,
                'low' if they can lock the money up, or empty string if
                not yet discussed.
        """
        products = store.find_all("financial_products.json")
        if not products:
            return {"error": "No products available in the catalog."}

        goal_lower = goal.lower()
        horizon_lower = horizon.lower().strip()
        liquidity_lower = liquidity_need.lower().strip()

        # ── Infer risk preference from need_type + horizon ───────────
        # Instead of asking the customer directly, we derive a suitable
        # risk level from the context they've already provided.
        inferred_risk = "low"  # safe default
        if need_type == "investing":
            if horizon_lower and any(w in horizon_lower for w in ("long", "years", "5+", "10+", "decade")):
                inferred_risk = "medium"  # longer horizon → can tolerate more
            else:
                inferred_risk = "low"  # investing but short/unknown → stay safe
        elif need_type == "saving":
            inferred_risk = "low"

        scored: list[tuple[float, dict]] = []

        for product in products:
            score = 0.0

            # ── 1. Goal / purpose match (weight: 10 per tag hit) ─────
            best_for_tags = [tag.lower() for tag in product.get("best_for", [])]
            for tag in best_for_tags:
                # Check if goal words appear in the tag or vice-versa
                if goal_lower in tag or tag in goal_lower:
                    score += 10.0
                    break
                # Partial word overlap
                goal_words = set(goal_lower.split())
                tag_words = set(tag.split())
                overlap = goal_words & tag_words
                if overlap:
                    score += 5.0 * len(overlap)

            # ── 2. Category vs. need-type match (weight: 6) ─────────
            cat = product.get("category", "")
            if need_type == "saving" and cat in ("savings", "goal_based"):
                score += 6.0
            elif need_type == "investing" and cat in ("mutual_fund", "equity_fund", "fixed_income"):
                score += 6.0
            elif need_type == "guidance":
                score += 2.0  # neutral — could be anything

            # ── 3. Time horizon match (weight: 4) ───────────────────
            if horizon_lower:
                is_short = any(w in horizon_lower for w in ("short", "soon", "few months", "within a year", "1 year", "immediate"))
                is_long = any(w in horizon_lower for w in ("long", "years", "5+", "10+", "decade", "retirement"))
                if is_short and cat in _SHORT_HORIZON_CATEGORIES:
                    score += 4.0
                elif is_long and cat in _LONG_HORIZON_CATEGORIES:
                    score += 4.0
                elif not is_short and not is_long and cat in _MEDIUM_HORIZON_CATEGORIES:
                    score += 3.0

            # ── 4. Liquidity match (weight: 3) ──────────────────────
            if liquidity_lower:
                if liquidity_lower == "high" and cat in _HIGH_LIQUIDITY_CATEGORIES:
                    score += 3.0
                elif liquidity_lower == "low" and cat in _LOW_LIQUIDITY_CATEGORIES:
                    score += 3.0

            # ── 5. Inferred risk suitability (weight: 2 — tiebreaker)
            # Derived from need_type and horizon, never asked directly.
            if product.get("risk_level", "").lower() == inferred_risk:
                score += 2.0

            scored.append((score, product))

        # Sort descending by score; on tie, preserve catalog order
        scored.sort(key=lambda x: x[0], reverse=True)
        best = scored[0][1]

        logger.info(
            "Recommended %s (score=%.1f) for goal=%r need=%r horizon=%r liquidity=%r inferred_risk=%r",
            best["name"],
            scored[0][0],
            goal,
            need_type,
            horizon,
            liquidity_need,
            inferred_risk,
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
        context.userdata.record_visit("loan")
        logger.info("Routing: Financial Guidance -> Loan")
        return LoanAgent(chat_ctx=self.chat_ctx.copy(exclude_instructions=True)), (
            "Continue seamlessly in the same language the customer has been using. Help them with their loan inquiry."
        )

    # The transfer_to_supervisor and human_handoff tools are inherited from DepartmentAgent
