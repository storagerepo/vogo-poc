"""
base.py
-------
Shared base class for every department agent. Centralizes the
`human_handoff` tool (available in every department, per section 7 of the
POC plan) and a helper to build the greeting each sub-agent gives when the
Supervisor hands off to it.
"""
from __future__ import annotations

from livekit.agents import Agent, RunContext, function_tool

from app.tools import common_tools
from app.utils.logger import get_logger

log = get_logger("agents.base")


class DepartmentAgent(Agent):
    """Base class for Sales / Service / Finance agents.

    Adds the common `human_handoff` tool so any department can escalate to
    a human without re-implementing the same function_tool everywhere.
    """

    department: str = "general"

    async def on_enter(self) -> None:
        """Trigger an audio greeting when this department agent becomes active."""
        from pathlib import Path
        from app.audio_trigger import trigger_agent_with_audio

        if self.session and self.realtime_llm_session:
            wav_path = str(Path(__file__).parent.parent / "audio_trigger" / "hey.wav")
            await trigger_agent_with_audio(self.realtime_llm_session, wav_path)

    @function_tool()
    async def human_handoff(
        self,
        context: RunContext,
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
        result = common_tools.human_handoff(
            team=self.department, reason=reason, context_summary=context_summary
        )
        log.info("human_handoff tool result: %s", result)
        return (
            f"Handoff queued for the {self.department} team. Reason: {reason}. "
            f"Tell the customer a human representative will join shortly with full context "
            f"of this conversation, so they won't need to repeat themselves."
        )

    @function_tool()
    async def return_to_supervisor(self, context: RunContext):
        """Hand the conversation back to the Supervisor to re-route.

        Call this when the customer's need is now clearly in a different
        department (e.g. a Sales customer suddenly asks about financing or
        booking a service appointment) instead of trying to handle it yourself.
        """
        from app.agents.supervisor import SupervisorAgent

        log.info("Routing: %s -> Supervisor", self.department)
        return SupervisorAgent(chat_ctx=self.chat_ctx.copy(exclude_instructions=True)), "Let me bring you back to our main assistant to redirect you."
