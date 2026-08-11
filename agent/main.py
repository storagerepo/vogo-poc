"""
main.py — LiveKit Agent entrypoint for Aria, Vogo's voice concierge POC.

Run with:
    python -m agent.main dev          # connect to LiveKit Agents Playground
    python -m agent.main start        # run as a production worker

See README.md for full setup (env vars, LiveKit project, Google AI key).

Model notes (Section 7 of the plan):
- Primary model: gemini-3.1-flash-live-preview. This is a PREVIEW model.
  It currently restricts send_client_content to initial history seeding
  only, and mid-session generate_reply()/update_instructions()/
  update_chat_ctx() calls are not honored. We work around this by relying
  entirely on function calling (unaffected) and a static system prompt
  set once at session start (see instructions.py) — never call those
  mid-session update methods with this model.
- If the Week-1 spike shows this blocks either use case, flip
  GEMINI_MODEL below to the fallback: gemini-live-2.5-flash-native-audio.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    RoomInputOptions,
    RoomOutputOptions,
    WorkerOptions,
    cli,
    metrics,
)
from livekit.plugins import google, noise_cancellation

from agent.audio_trigger import AudioTrigger
from agent.instructions import ARIA_INSTRUCTIONS
from agent.tools import ALL_TOOLS

load_dotenv()

logger = logging.getLogger("vogo-voice-agent")
logger.setLevel(logging.INFO)

# Primary preview model per the plan. Swap to the fallback string in the
# module docstring above if the Week-1 spike surfaces a blocker.
GEMINI_MODEL = "gemini-3.1-flash-live-preview"
GEMINI_VOICE = "Kore"  # primary voice; alternates: Leda, Aoede, Sulafat

# Path to the short WAV file used to trigger the agent's opening greeting.
# The agent "hears" this as a real user saying "Hey" and responds naturally,
# working around Gemini 3.1's limitation of ignoring generate_reply() mid-session.
TRIGGER_WAV_PATH = Path(__file__).resolve().parent.parent / "hey.wav"

# Soft session-length cap for the POC only (Section 9.12) — not a
# production limitation, just keeps demo cost/scope predictable.
SESSION_TIME_LIMIT_SECONDS = 10 * 60


class AriaAgent(Agent):
    """Vogo's voice concierge. Instructions + tools are injected here;
    all guardrail language lives in instructions.py so it's reviewable
    and editable in one place."""

    def __init__(self) -> None:
        super().__init__(instructions=ARIA_INSTRUCTIONS, tools=ALL_TOOLS)


def prewarm(proc: JobProcess) -> None:
    """Optional prewarm hook — reserved for warming up any local models
    (e.g. VAD) if a cascaded fallback pipeline is added later. No-op for
    the native-audio Gemini Live path used in this POC."""
    pass


async def entrypoint(ctx: JobContext) -> None:
    # Kick off the trigger connection concurrently to save 3-5 seconds of startup time
    audio_trigger = AudioTrigger(
        room_name=ctx.room.name,
        wav_file_path=TRIGGER_WAV_PATH,
    )
    trigger_prepare_task = asyncio.create_task(audio_trigger.start())

    await ctx.connect()

    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model=GEMINI_MODEL,
            voice=GEMINI_VOICE,
            temperature=0.7,
        ),
    )

    # --- Observability (Section 12): log every tool call and usage metrics ---
    @session.on("function_tools_executed")
    def _on_tools_executed(event) -> None:
        for call, output in zip(event.function_calls, event.function_call_outputs):
            logger.info(
                "tool_call name=%s args=%s -> %s",
                call.name,
                call.arguments,
                output,
            )

    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics(event) -> None:
        metrics.log_metrics(event.metrics)
        usage_collector.collect(event.metrics)

    async def log_session_summary() -> None:
        summary = usage_collector.get_summary()
        logger.info("session usage summary: %s", summary)

    ctx.add_shutdown_callback(log_session_summary)

    await session.start(
        agent=AriaAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
        room_output_options=RoomOutputOptions(
            transcription_enabled=True,
        ),
    )

    # Gemini 3.1 ignores generate_reply() mid-session, so we trigger the
    # greeting by streaming a short "Hey" audio clip into the room from a
    # temporary participant.  The agent hears it as real speech and responds.
    await trigger_prepare_task
    await audio_trigger.trigger(agent_session=session)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            agent_name="vogo-voice-agent",
            entrypoint_fnc=entrypoint
        )
    )