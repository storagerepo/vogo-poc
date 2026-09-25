"""
Entrypoint for the Amadita POC voice agent worker.

Run with:
    python -m agent.main dev      # local dev, connects to LIVEKIT_URL
    python -m agent.main start    # production worker mode

This process is a single LiveKit Agents "worker": for every room it's
dispatched into (a browser widget session, or a phone call once SIP is
attached — see docs/ARCHITECTURE.md) it spins up one AgentSession
backed by the Gemini Live Realtime API, wires in the mock-data tools,
and enforces the POC's language-lock behavior (§2 of the plan).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    WorkerOptions,
    cli,
)
from livekit.plugins import google
from .import config

from .prompts import build_instructions
from .tools import ALL_TOOLS


logger = logging.getLogger("amadita-agent")
logging.basicConfig(level=logging.INFO)


class AmaditaAgent(Agent):
    """Amadita Laboratorio Clínico voice assistant agent."""

    def __init__(self) -> None:
        super().__init__(
            instructions=build_instructions(),
            tools=ALL_TOOLS,
        )



def prewarm(proc: JobProcess) -> None:
    # Nothing heavy to preload for this POC (no local VAD/STT models —
    # Gemini Live handles audio end-to-end). Kept as a hook for parity
    # with standard LiveKit Agents worker structure.
    pass



async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    agent = AmaditaAgent()

    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model=config.GEMINI_REALTIME_MODEL,
            api_key=config.GOOGLE_API_KEY,
            voice=config.GEMINI_VOICE,
        ),
    )
    await session.start(agent=agent, room=ctx.room)

    await session.generate_reply()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        agent_name="amadita-poc",
        entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
