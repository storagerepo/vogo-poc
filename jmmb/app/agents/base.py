"""
base.py
-------
Shared base class for every department agent in JMMB Voice POC. 
Centralizes the `human_handoff` tool and `return_to_supervisor` tool.
It also includes an `on_enter` method that plays an audio greeting when the
Supervisor hands off to it.
"""
from __future__ import annotations

import logging
from pathlib import Path

from livekit.agents import Agent, RunContext, function_tool

from app.audio_trigger.audio_trigger import trigger_agent_with_audio
from app.core.userdata import SessionUserData

logger = logging.getLogger("jmmb-base-agent")

class DepartmentAgent(Agent):
    """Base class for Loan / Service / Financial Guidance / Security agents."""

    department: str = "general"

    async def on_enter(self) -> None:
        """Trigger an audio greeting when this department agent becomes active."""
        if self.session and self.session.userdata:
            self.session.userdata.record_visit(self.department)
            
        if self.session and self.realtime_llm_session:
            wav_path = str(Path(__file__).parent.parent / "audio_trigger" / "hey.wav")
            await trigger_agent_with_audio(self.realtime_llm_session, wav_path)

    @function_tool()
    async def human_handoff(
        self,
        context: RunContext[SessionUserData],
        reason: str,
        context_summary: str,
    ):
        """Transfer the customer to a human representative.

        Call this when: the customer explicitly asks for a human, the
        request is outside your capabilities, you cannot find reliable
        information, the issue is complex, financing needs final approval,
        the customer has a complaint, or they request a specialist.

        Args:
            reason: Short reason for the handoff (e.g. "customer requested a human").
            context_summary: Summary of the conversation so far for the human agent.
        """
        logger.info(
            "human_handoff queued for department '%s'. Reason: %s, Context: %s",
            self.department,
            reason,
            context_summary,
        )
        return (
            f"Handoff queued. Reason: {reason}. "
            f"Tell the customer that a JMMB representative will be with them shortly "
            f"and they won't need to repeat anything — you've noted all the details."
        )

    @function_tool()
    async def return_to_supervisor(self, context: RunContext[SessionUserData]):
        """Hand the conversation back to the Supervisor to re-route.

        Call this when the customer's need is now clearly in a different
        department (e.g. a Loan customer suddenly asks about booking a 
        service appointment) instead of trying to handle it yourself.
        """
        from app.agents.supervisor import SupervisorAgent

        context.userdata.record_visit("supervisor")
        logger.info("Routing: %s -> Supervisor", self.department)
        return SupervisorAgent(chat_ctx=self.chat_ctx.copy(exclude_instructions=True)), "Continue seamlessly in the same language the customer has been using. Help them with their request."
