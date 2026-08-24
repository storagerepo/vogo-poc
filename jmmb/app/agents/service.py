"""
agents/service.py

Handles general service requests: branch selection, mock availability
checks, and booking a mock appointment.
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

logger = logging.getLogger("jmmb-service")

INSTRUCTIONS = f"""
{BANK_CONTEXT}
{VOICE_STYLE_GUIDE}

You are SARA, now helping the customer with service requests. The customer
has already been onboarded and verified — do not ask for their name or
verify them again.  Do NOT introduce yourself or greet the customer, as they
are already in the middle of a conversation with you. Seamlessly continue the
conversation based on the context.

Your job:
- Understand what kind of service the customer needs (e.g. account
  opening help, card services, a general inquiry) and which branch or
  city is convenient for them.
- Use `get_service_branches` to find branches, optionally filtered by
  city or the service they need.
- Use `check_service_availability` to see open time slots at a chosen
  branch on a given date.
- Once the customer picks a slot, use `book_service_appointment` to
  confirm the booking, then read back the confirmation details (branch,
  date, time, reference number).
- When done, or if they need something else (loans, financial guidance,
  or security), use `return_to_supervisor`.
"""


class ServiceAgent(DepartmentAgent):
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(instructions=INSTRUCTIONS, chat_ctx=chat_ctx)
    department: str = "service"

    @function_tool()
    async def get_service_branches(
        self, context: RunContext[SessionUserData], city: str | None = None, service_type: str | None = None
    ) -> list[dict]:
        """List JMMB branches, optionally filtered by city and/or the
        type of service offered.

        Args:
            city: Optional city name to filter branches by, e.g. 'Santo Domingo'.
            service_type: Optional service filter, e.g. 'account opening',
                'card services', 'loan consultation', 'Security support',
                'general inquiry'.
        """
        branches = store.find_all("service_branches.json")
        if city:
            branches = [b for b in branches if b["city"].lower() == city.lower()]
        if service_type:
            branches = [
                b for b in branches if service_type.lower() in [s.lower() for s in b["services"]]
            ]
        return branches

    @function_tool()
    async def check_service_availability(
        self, context: RunContext[SessionUserData], branch_id: str, date: str
    ) -> dict:
        """Check mock available appointment slots at a branch on a given
        date (YYYY-MM-DD).

        Args:
            branch_id: The branch identifier, e.g. 'BR-KGN01'.
            date: Date to check, formatted YYYY-MM-DD.
        """
        branch = store.find_one("service_branches.json", lambda b: b["branch_id"] == branch_id)
        if not branch:
            return {"available": False, "reason": f"Unknown branch '{branch_id}'."}

        slots = branch.get("available_slots", {}).get(date, [])
        return {
            "branch": branch["name"],
            "date": date,
            "available_slots": slots,
            "available": len(slots) > 0,
        }

    @function_tool()
    async def book_service_appointment(
        self,
        context: RunContext[SessionUserData],
        branch_id: str,
        date: str,
        time: str,
        service_type: str,
    ) -> dict:
        """Book a mock appointment at a branch for a specific date/time.

        Args:
            branch_id: The branch identifier, e.g. 'BR-KGN01'.
            date: Appointment date, formatted YYYY-MM-DD.
            time: Appointment time, e.g. '10:30'.
            service_type: What the appointment is for, e.g. 'card services'.
        """
        userdata = context.userdata
        branch = store.find_one("service_branches.json", lambda b: b["branch_id"] == branch_id)
        if not branch:
            return {"confirmed": False, "reason": f"Unknown branch '{branch_id}'."}

        slots = branch.get("available_slots", {}).get(date, [])
        if time not in slots:
            return {
                "confirmed": False,
                "reason": f"{time} is not available at {branch['name']} on {date}.",
                "available_slots": slots,
            }

        # remove the booked slot from the branch's mock availability
        branch["available_slots"][date].remove(time)
        branches = store.find_all("service_branches.json")
        for i, b in enumerate(branches):
            if b["branch_id"] == branch_id:
                branches[i] = branch
        store.write("service_branches.json", branches)

        appointment = {
            "appointment_id": f"APPT-{uuid.uuid4().hex[:8].upper()}",
            "customer_id": userdata.customer_id,
            "customer_name": userdata.name,
            "branch_id": branch_id,
            "branch_name": branch["name"],
            "date": date,
            "time": time,
            "service_type": service_type,
            "status": "confirmed",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        store.append_record("appointments.json", appointment)
        logger.info("Booked appointment: %s", appointment["appointment_id"])
        return {"confirmed": True, **appointment}

    # The transfer_to_supervisor and human_handoff tools are inherited from DepartmentAgent
