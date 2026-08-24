"""
main.py
-------
LiveKit Agents worker entrypoint for the Santo Domingo Motors AI Voice Agent
POC. Run with:

    python -m app.main dev      # local development, connects to LiveKit Cloud/OSS server
    python -m app.main start    # production worker

The Supervisor pattern:
    Every new call/session starts on `SupervisorAgent`. From there, the
    Supervisor hands the session off to SalesAgent / ServiceAgent /
    FinanceAgent (see app/agents/supervisor.py for the routing logic), and
    those agents can hand back to the Supervisor or escalate to a human.

Voice model:
    This POC uses Google's Gemini Realtime (speech-to-speech) model as a
    single combined STT+LLM+TTS engine via LiveKit's `google.beta.realtime`
    plugin -- there is no separate STT/LLM/TTS pipeline to wire up. The same
    RealtimeModel instance/config is reused by every agent in the handoff
    chain since LiveKit's AgentSession owns the model and swaps only the
    active `Agent` (instructions + tools) on handoff.
"""

from __future__ import annotations

from livekit.agents import (
    AgentSession,
    JobContext,
    RoomInputOptions,
    WorkerOptions,
    cli,
)
from livekit.plugins import google, noise_cancellation

from app.agents.supervisor import SupervisorAgent
from app.config import settings
from app.utils.logger import get_logger
from app.audio_trigger import trigger_agent_with_audio
from pathlib import Path

log = get_logger("main")


async def entrypoint(ctx: JobContext) -> None:
    log.info("Job starting for room: %s", ctx.room.name)
    await ctx.connect()

    # Gemini Realtime handles audio-in -> understanding -> audio-out directly,
    # so this single model powers every department agent in the handoff chain.
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model=settings.GEMINI_REALTIME_MODEL,
            voice=settings.GEMINI_VOICE,
            temperature=settings.GEMINI_TEMPERATURE,
            api_key=settings.GOOGLE_API_KEY or None,
        ),
    )
    agent = SupervisorAgent()


    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # Filters background noise from the caller's mic before it
            # reaches the model. Safe to remove if you don't need it.
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await trigger_agent_with_audio(
        agent.realtime_llm_session,
        wav_file_path=str(Path(__file__).parent / "audio_trigger" / "hey.wav"),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        agent_name="santo-domingo-motors-voice-agent",
        entrypoint_fnc=entrypoint))
