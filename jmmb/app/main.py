"""
agent.py

LiveKit worker entrypoint for the JMMB AI Voice Banking Assistant POC.

Wires together:
  - Google Gemini Realtime (Live API) as the speech-to-speech model
  - The Supervisor Agent as the initial agent in the session
  - SessionUserData as the shared state carried across every hand-off

Run it with:
    python agent.py console     # talk to it directly in your terminal
    python agent.py dev         # run as a worker for a real LiveKit room
"""
from __future__ import annotations

import logging

from livekit import agents
from livekit.agents import AgentSession, JobContext, RoomInputOptions, WorkerOptions, cli
from livekit.plugins import google, noise_cancellation

import asyncio
import os
from pathlib import Path

from app import config
from app.agents.supervisor import SupervisorAgent
from app.audio_trigger.audio_trigger import trigger_agent_with_audio
from app.core.userdata import SessionUserData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jmmb-voice-poc")


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    session: AgentSession[SessionUserData] = AgentSession[SessionUserData](
        userdata=SessionUserData(),
        llm=google.beta.realtime.RealtimeModel(
            model=config.GEMINI_REALTIME_MODEL,
            voice=config.GEMINI_VOICE,
            temperature=config.GEMINI_TEMPERATURE,
            
           
        ),
    )
    agent = SupervisorAgent()

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation.
            # If self-hosting, this can be omitted.
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await trigger_agent_with_audio(
        agent.realtime_llm_session,
        wav_file_path=str(Path(__file__).parent / "audio_trigger" / "hey.wav"),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        agent_name="jmmb-voice-agent",
        entrypoint_fnc=entrypoint))
