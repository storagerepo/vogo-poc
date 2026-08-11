"""
audio_trigger.py — Reusable LiveKit audio trigger utility.

Works around a limitation in Gemini 3.1 (and similar realtime models)
where generate_reply(), update_instructions(), and update_chat_ctx() are
ignored mid-session.  Instead of those out-of-band calls, this module
connects a *separate*, short-lived participant to the LiveKit room and
streams a local WAV file (e.g. a pre-recorded "Hey") into the room.
The agent hears it as regular user speech and responds naturally.

The real user never hears the trigger audio — the module uses the
LiveKit Server API to unsubscribe every non-agent participant from
the trigger track *before* streaming begins.  From the user's point
of view the agent simply introduces itself unprompted.

Why a separate participant?
---------------------------
LiveKit agents only process audio from *remote* participants.  If the
agent's own process published the track, the framework would treat it as
its own outgoing audio and the model would never "hear" it.  By spinning
up a lightweight second connection with a distinct identity, the audio
arrives as a genuine remote track.

Usage
-----
    from agent.audio_trigger import trigger_agent_with_audio

    # Inside your entrypoint, after session.start():
    await trigger_agent_with_audio(
        room_name=ctx.room.name,
        wav_file_path="hey.wav",
    )

The function is intentionally self-contained so it can be dropped into
any LiveKit project that uses realtime models with the same limitation.
"""

from __future__ import annotations

import asyncio
import logging
import os
import wave
from pathlib import Path

from livekit import api, rtc

logger = logging.getLogger(__name__)

# ── Defaults ────────────────────────────────────────────────────────────
_DEFAULT_TRIGGER_IDENTITY = "audio-trigger-bot"
_DEFAULT_TRIGGER_NAME = "Audio Trigger"
_FRAME_DURATION_MS = 20  # 20 ms chunks — standard for WebRTC pacing


async def trigger_agent_with_audio(
    agent_session: "livekit.agents.AgentSession",
    room_name: str,
    wav_file_path: str | os.PathLike,
    *,
    livekit_url: str | None = None,
    api_key: str | None = None,
    api_secret: str | None = None,
    participant_identity: str = _DEFAULT_TRIGGER_IDENTITY,
    participant_name: str = _DEFAULT_TRIGGER_NAME,
    settle_delay: float = 0.2,
) -> None:
    """Connect a temporary participant and stream a WAV file into the room.

    Only the agent hears the audio — all other participants (the real
    user, egress recorders, etc.) are automatically unsubscribed from the
    trigger track via the LiveKit Server API before streaming begins.
    From the user's perspective the agent simply starts talking on its own.

    Parameters
    ----------
    room_name:
        Name of the LiveKit room the agent is already in.
    wav_file_path:
        Path to a **16-bit PCM** WAV file (mono or stereo).
    livekit_url:
        LiveKit server URL.  Falls back to ``LIVEKIT_URL`` env var.
    api_key / api_secret:
        LiveKit credentials.  Fall back to ``LIVEKIT_API_KEY`` /
        ``LIVEKIT_API_SECRET`` env vars.
    participant_identity:
        Identity string for the temporary participant.
    participant_name:
        Display name for the temporary participant.
    settle_delay:
        Seconds to wait after connecting before streaming, giving the
        agent time to notice the new participant's audio track.
    """

    wav_path = Path(wav_file_path)
    if not wav_path.is_file():
        raise FileNotFoundError(f"WAV file not found: {wav_path}")

    url = livekit_url or os.getenv("LIVEKIT_URL")
    key = api_key or os.getenv("LIVEKIT_API_KEY")
    secret = api_secret or os.getenv("LIVEKIT_API_SECRET")

    if not url or not key or not secret:
        raise EnvironmentError(
            "LiveKit connection details are required.  Set LIVEKIT_URL, "
            "LIVEKIT_API_KEY, and LIVEKIT_API_SECRET environment variables "
            "or pass them explicitly."
        )

    # ── 1. Read and validate the WAV file ──────────────────────────────
    with wave.open(str(wav_path), "rb") as wav:
        sample_rate = wav.getframerate()
        num_channels = wav.getnchannels()
        sample_width = wav.getsampwidth()

        if sample_width != 2:
            raise ValueError(
                f"WAV file must be 16-bit PCM (sampwidth=2), "
                f"got sampwidth={sample_width}.  Re-encode the file with: "
                f"ffmpeg -i {wav_path.name} -ar 48000 -ac 1 -sample_fmt s16 output.wav"
            )

        # Read all frames up-front (the file is tiny — a few seconds max)
        raw_audio = wav.readframes(wav.getnframes())
        total_frames = wav.getnframes()

    logger.info(
        "audio_trigger: loaded %s — %d Hz, %d ch, %.2f s",
        wav_path.name,
        sample_rate,
        num_channels,
        total_frames / sample_rate,
    )

    # ── 2. Mint a short-lived access token for the trigger bot ─────────
    token = (
        api.AccessToken(key, secret)
        .with_identity(participant_identity)
        .with_name(participant_name)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=False,  # we only publish, never subscribe
            )
        )
        .to_jwt()
    )

    # ── 3. Connect the temporary participant ───────────────────────────
    trigger_room = rtc.Room()

    try:
        await trigger_room.connect(
            url,
            token,
            options=rtc.RoomOptions(auto_subscribe=False),
        )
        logger.info(
            "audio_trigger: connected to room '%s' as '%s'",
            room_name,
            participant_identity,
        )

        # ── 4. Create audio source & publish track ─────────────────────
        source = rtc.AudioSource(sample_rate, num_channels)
        track = rtc.LocalAudioTrack.create_audio_track(
            "trigger-audio", source
        )
        publish_options = rtc.TrackPublishOptions(
            source=rtc.TrackSource.SOURCE_MICROPHONE,
        )
        publication = await trigger_room.local_participant.publish_track(
            track, publish_options
        )
        logger.info("audio_trigger: published track %s", publication.sid)

        # ── 5. Mute the trigger track for all real users ───────────────
        # We start the API call to unsubscribe users, but we don't await it
        # immediately so we can overlap it with the settle_delay.
        mute_task = asyncio.create_task(
            _mute_trigger_for_users(
                url=url,
                api_key=key,
                api_secret=secret,
                room_name=room_name,
                trigger_track_sid=publication.sid,
                trigger_identity=participant_identity,
            )
        )

        # ── 6. Wire the trigger bot into the agent's audio pipeline ────
        # The AgentSession normally locks onto the first participant it sees
        # (the real user). We temporarily force it to listen to our bot.
        original_linked_participant = agent_session.room_io.linked_participant
        original_identity = (
            original_linked_participant.identity
            if original_linked_participant
            else None
        )
        agent_session.room_io.set_participant(participant_identity)
        logger.info(
            "audio_trigger: switched AgentSession input from %s to %s",
            original_identity,
            participant_identity,
        )

        # Give the agent a moment to subscribe to the new participant's
        # audio track before we start streaming.
        await asyncio.sleep(settle_delay)
        
        # Ensure the mute API call completed before we stream
        await mute_task

        # ── 7. Stream frames at real-time pace ─────────────────────────
        samples_per_chunk = sample_rate * _FRAME_DURATION_MS // 1000
        bytes_per_sample = sample_width * num_channels
        chunk_bytes = samples_per_chunk * bytes_per_sample
        sleep_duration = _FRAME_DURATION_MS / 1000.0

        offset = 0
        while offset < len(raw_audio):
            end = min(offset + chunk_bytes, len(raw_audio))
            chunk = raw_audio[offset:end]

            # Pad the final chunk to a full frame if needed
            if len(chunk) < chunk_bytes:
                chunk += b"\x00" * (chunk_bytes - len(chunk))

            frame = rtc.AudioFrame(
                data=chunk,
                sample_rate=sample_rate,
                num_channels=num_channels,
                samples_per_channel=samples_per_chunk,
            )
            await source.capture_frame(frame)
            await asyncio.sleep(sleep_duration)
            offset = end

        # Small trailing silence so the agent's VAD registers end-of-speech
        silence = b"\x00" * chunk_bytes
        for _ in range(10):  # 200 ms of silence
            frame = rtc.AudioFrame(
                data=silence,
                sample_rate=sample_rate,
                num_channels=num_channels,
                samples_per_channel=samples_per_chunk,
            )
            await source.capture_frame(frame)
            await asyncio.sleep(sleep_duration)

        logger.info("audio_trigger: finished streaming audio")

        # Brief pause to let the last frames propagate through WebRTC
        await asyncio.sleep(0.5)

        # ── 8. Restore the original user in the agent's pipeline ───────
        agent_session.room_io.set_participant(original_identity)
        logger.info(
            "audio_trigger: restored AgentSession input back to %s",
            original_identity,
        )

    finally:
        # ── 9. Clean up — disconnect the temporary participant ─────────
        await trigger_room.disconnect()
        logger.info("audio_trigger: disconnected trigger participant")


# ── Helpers ─────────────────────────────────────────────────────────────


async def _mute_trigger_for_users(
    *,
    url: str,
    api_key: str,
    api_secret: str,
    room_name: str,
    trigger_track_sid: str,
    trigger_identity: str,
) -> None:
    """Unsubscribe every non-agent participant from the trigger track.

    Uses ``LiveKitAPI.room.update_subscriptions`` to set
    ``subscribe=False`` for each real user.  Agent participants
    (kind == AGENT) are left alone so the model still hears the audio.
    """

    # ParticipantInfo.Kind enum values from livekit protocol
    PARTICIPANT_KIND_AGENT = 4

    lk_api = api.LiveKitAPI(url, api_key=api_key, api_secret=api_secret)

    try:
        resp = await lk_api.room.list_participants(
            api.ListParticipantsRequest(room=room_name)
        )

        for participant in resp.participants:
            # Skip the trigger bot itself
            if participant.identity == trigger_identity:
                continue

            # Skip agent participants — they need to hear the trigger
            if participant.kind == PARTICIPANT_KIND_AGENT:
                logger.debug(
                    "audio_trigger: keeping subscription for agent '%s'",
                    participant.identity,
                )
                continue

            # Unsubscribe this participant from the trigger audio track
            try:
                await lk_api.room.update_subscriptions(
                    api.UpdateSubscriptionsRequest(
                        room=room_name,
                        identity=participant.identity,
                        track_sids=[trigger_track_sid],
                        subscribe=False,
                    )
                )
                logger.info(
                    "audio_trigger: unsubscribed '%s' from trigger track",
                    participant.identity,
                )
            except Exception as exc:
                # Non-fatal — the user might briefly hear the trigger
                # but the core flow (agent responding) still works.
                logger.warning(
                    "audio_trigger: failed to unsubscribe '%s': %s",
                    participant.identity,
                    exc,
                )
    finally:
        await lk_api.aclose()
