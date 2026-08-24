"""
agents/Security.py

Handles suspicious-transaction/Security inquiries: identifying the issue,
looking up the mock account, opening a mock Security case with a reference
number, and flagging serious cases for escalation.
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

logger = logging.getLogger("jmmb-Security")

HIGH_SEVERITY_KEYWORDS = (
    "unauthorized",
    "unauthorised",
    "stolen",
    "lost card",
    "identity theft",
    "large",
    "account takeover",
    "hacked",
)

INSTRUCTIONS = f"""
{BANK_CONTEXT}
{VOICE_STYLE_GUIDE}

You are SARA, now helping the customer with a security concern. The
customer has already been onboarded and verified — do not ask for their
name or verify them again. Do NOT introduce yourself or greet the customer, as they
are already in the middle of a conversation with you. Seamlessly continue the
conversation based on the context.
Stay calm and reassuring; customers reporting security issues are often anxious.

Your job:
- Ask what happened: what they noticed, roughly when, and whether their
  card, account, or credentials might be compromised.
- If they give you an account number, use `check_customer_account` to
  pull the mock account and recent transactions so you can confirm what
  they're seeing.
- Once you understand the issue, use `create_Security_case` to open a mock
  case. Always read the case reference number back to the customer
  clearly.
- If the case looks serious (unauthorized/large transactions, a lost or
  stolen card, suspected identity theft), tell the customer this has
  been flagged for priority review, and advise them to also call the
  JMMB security hotline for anything requiring an immediate card block,
  since this demo cannot block cards for real.
- When done, or if they need something else, use `return_to_supervisor`.
"""


class SecurityAgent(DepartmentAgent):
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(instructions=INSTRUCTIONS, chat_ctx=chat_ctx)
    department: str = "security"



    @function_tool()
    async def check_customer_account(
        self, context: RunContext[SessionUserData], account_number: str
    ) -> dict:
        """Look up a mock account and its recent transactions by account
        number.

        Args:
            account_number: The account number the customer provided.
        """
        account = store.find_one(
            "accounts.json", lambda a: a["account_number"] == account_number
        )
        if not account:
            return {"found": False, "reason": f"No account found matching '{account_number}'."}
        return {"found": True, **account}

    @function_tool()
    async def create_Security_case(
        self,
        context: RunContext[SessionUserData],
        issue_type: str,
        description: str,
        account_number: str | None = None,
    ) -> dict:
        """Open a mock Security case and generate a case reference number.

        Args:
            issue_type: Short category, e.g. 'unrecognized transaction',
                'lost card', 'stolen card', 'suspected identity theft',
                'phishing attempt'.
            description: A brief description of what the customer reported.
            account_number: Optional related account number, if known.
        """
        userdata = context.userdata

        text = f"{issue_type} {description}".lower()
        escalate = any(keyword in text for keyword in HIGH_SEVERITY_KEYWORDS)

        case = {
            "case_id": f"Security-{uuid.uuid4().hex[:8].upper()}",
            "customer_id": userdata.customer_id,
            "customer_name": userdata.name,
            "phone": userdata.phone,
            "account_number": account_number,
            "issue_type": issue_type,
            "description": description,
            "status": "escalated" if escalate else "open",
            "priority": "high" if escalate else "normal",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        store.append_record("Security_cases.json", case)
        logger.info("Created Security case: %s (priority=%s)", case["case_id"], case["priority"])
        return case

    # The transfer_to_supervisor and human_handoff tools are inherited from DepartmentAgent
