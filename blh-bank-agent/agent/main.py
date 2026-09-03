"""
Entrypoint for the BLH POC voice agent worker.

Run with:
    python -m agent.main dev      # local dev, connects to LIVEKIT_URL
    python -m agent.main start    # production worker mode

This process is a single LiveKit Agents "worker": for every room it's
dispatched into (a browser widget session, or a phone call once SIP is
attached) it spins up one AgentSession backed by the Gemini Live Realtime API
and wires in the banking mock-data tools.
"""

from __future__ import annotations

import logging
from pathlib import Path

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
)
from livekit.plugins import google

from . import config
from .audio_trigger import trigger_agent_with_audio
from .prompts import build_instructions
from .tools import ALL_TOOLS
from .userdata import SessionUserData

logger = logging.getLogger("blh-voice-agent")
logging.basicConfig(level=logging.INFO)


class BLHAgent(Agent):
    """The BLH voice banking assistant persona, wired to its business tools."""

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

    agent = BLHAgent()

    session = AgentSession[SessionUserData](
        userdata=SessionUserData(),
        llm=google.beta.realtime.RealtimeModel(
            model=config.GEMINI_REALTIME_MODEL,
            api_key=config.GOOGLE_API_KEY,
            voice=config.GEMINI_VOICE,
        ),
    )
    await session.start(agent=agent, room=ctx.room)
    await trigger_agent_with_audio(
        agent.realtime_llm_session,
        wav_file_path=str(Path(__file__).parent / "audio_trigger" / "hey.wav"),
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            agent_name="blh-voice-poc",
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        )
    )
