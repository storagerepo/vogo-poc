from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class SessionUserData:
    # --- identity captured during session ---
    customer_name: str | None = None
    phone: str | None = None
    email: str | None = None
    language: str = "en"

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
    def record_visit(self, agent_name: str) -> None:
        self.current_agent = agent_name
        self.visited_agents.append(agent_name)

    def summary(self) -> str:
        """Small human-readable snapshot, handy for logs / debugging."""
        return (
            f"customer={self.customer_name!r} phone={self.phone!r} email={self.email!r} "
            f"language={self.language!r} current_agent={self.current_agent!r}"
        )
