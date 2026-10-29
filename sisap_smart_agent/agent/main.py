"""LiveKit entrypoint: one Gemini Live (realtime, multilingual) voice agent.

Run:
    python -m agent.main console   # talk from your terminal (mic + speakers)
    python -m agent.main dev       # connect to LiveKit and wait for a room (use the Agents Playground)
    python -m agent.main start     # production mode (used by Docker)
"""
import logging
from pathlib import Path

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
from agent.instructions import INSTRUCTIONS, GREETING_INSTRUCTIONS
from agent.tools import ALL_TOOLS
from agent.tools.data_store import SessionState

logger = logging.getLogger("sisap-voice-agent")
logger.setLevel(logging.INFO)

GEMINI_MODEL = "gemini-3.8-live"
GEMINI_VOICE = "Puck"  # primary voice; alternates: Kore, Leda, Aoede, Sulafat


class SisapAgent(Agent):
    """SISAP's voice agent. Instructions + tools are injected here;
    all guardrail language lives in instructions.py so it's reviewable
    and editable in one place."""

    def __init__(self) -> None:
        super().__init__(instructions=INSTRUCTIONS, tools=ALL_TOOLS)


def prewarm(proc: JobProcess) -> None:
    """Optional prewarm hook — reserved for warming up any local models
    (e.g. VAD) if a cascaded fallback pipeline is added later. No-op for
    the native-audio Gemini Live path used in this POC."""
    pass


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    state = SessionState(session_id=ctx.room.name if ctx.room else "console")
    session = AgentSession[SessionState](
        userdata=state,
        llm=google.beta.realtime.RealtimeModel(
            model=GEMINI_MODEL,
            voice=GEMINI_VOICE,
            temperature=0.6,
        ),
    )

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

    sisap_agent = SisapAgent()

    await session.start(
        agent=sisap_agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
        room_output_options=RoomOutputOptions(
            transcription_enabled=True,
        ),
    )

    await session.generate_reply(instructions=GREETING_INSTRUCTIONS)

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            agent_name="sisap-voice-agent",
            entrypoint_fnc=entrypoint
        )
    )
