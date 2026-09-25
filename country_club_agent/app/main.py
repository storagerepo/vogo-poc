"""Entrypoint for the Santo Domingo Country Club Voice Agent POC.

Run locally with:
    python -m app.main dev

This starts a LiveKit Agents worker that, for each room/session, spins up
Sofia (CountryClubAgent) backed by Google Gemini Live as the realtime
speech-to-speech model (STT + LLM + TTS in one multimodal model, with
native multilingual support for Spanish/English).
"""


from __future__ import annotations

import logging
import os
from pathlib import Path
from .import config


from dotenv import load_dotenv
from livekit.agents import (
    AgentSession,
    JobContext,
    JobProcess,
    RoomInputOptions,
    WorkerOptions,
    cli,
)
from livekit.plugins import google, noise_cancellation

from .agent import CountryClubAgent

load_dotenv()

logger = logging.getLogger("country-club-agent")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


def prewarm(proc: JobProcess) -> None:
    """Optional: warm up anything expensive before the first job. Kept as a
    no-op placeholder for this POC since there is no local model/VAD to
    preload when using Gemini Live's built-in speech handling."""
    return


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model=config.GEMINI_REALTIME_MODEL,
            voice=config.GEMINI_VOICE,
            # Gemini Live handles speech in / speech out end-to-end and
            # supports multiple languages natively; the agent's system
            # prompt instructs it to detect and mirror the caller's
            # language (Spanish or English).
            temperature=0.7,
        ),
    )

    agent = CountryClubAgent()

    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await session.generate_reply()

        



if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            agent_name="country-club-agent",
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        )
    )
