"""
core/userdata.py

SessionUserData is the single piece of shared state that travels with the
LiveKit AgentSession across every agent hand-off (Supervisor -> Financial
Guidance -> Loan -> ...). This is how the POC satisfies:

    "Once verified, the customer does not need to repeat OTP verification
     when moving between agents."

Any agent's @function_tool can read/write it via `context.userdata`
(RunContext[SessionUserData]).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class SessionUserData:
    # --- identity captured during onboarding ---
    customer_id: str | None = None
    name: str | None = None
    phone: str | None = None
    email: str | None = None

    # --- OTP / verification state ---
    verified: bool = False

    # --- routing / bookkeeping ---
    current_agent: str = "supervisor"
    last_intent: str | None = None
    visited_agents: list[str] = field(default_factory=list)
    session_started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def onboarding_complete(self) -> bool:
        return bool(self.name and self.phone and self.email)

    def record_visit(self, agent_name: str) -> None:
        self.current_agent = agent_name
        self.visited_agents.append(agent_name)

    def summary(self) -> str:
        """Small human-readable snapshot, handy for logs / debugging."""
        return (
            f"customer={self.name!r} phone={self.phone!r} email={self.email!r} "
            f"verified={self.verified} current_agent={self.current_agent!r}"
        )
