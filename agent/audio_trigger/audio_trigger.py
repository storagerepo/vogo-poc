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


class AudioTrigger:
    """Pre-connects and streams a trigger WAV file into a LiveKit room."""
    
    def __init__(
        self,
        room_name: str,
        wav_file_path: str | os.PathLike | None = None,
        *,
        livekit_url: str | None = None,
        api_key: str | None = None,
        api_secret: str | None = None,
        participant_identity: str = _DEFAULT_TRIGGER_IDENTITY,
        participant_name: str = _DEFAULT_TRIGGER_NAME,
        settle_delay: float = 0.2,
    ) -> None:
        self.room_name = room_name
        self.wav_file_path = Path(wav_file_path) if wav_file_path else Path(__file__).parent / "hey.wav"
        self.url = livekit_url or os.getenv("LIVEKIT_URL")
        self.key = api_key or os.getenv("LIVEKIT_API_KEY")
        self.secret = api_secret or os.getenv("LIVEKIT_API_SECRET")
        self.participant_identity = participant_identity
        self.participant_name = participant_name
        self.settle_delay = settle_delay

        if not self.url or not self.key or not self.secret:
            raise EnvironmentError(
                "LiveKit connection details are required. Set LIVEKIT_URL, "
                "LIVEKIT_API_KEY, and LIVEKIT_API_SECRET."
            )

        if not self.wav_file_path.is_file():
            raise FileNotFoundError(f"WAV file not found: {self.wav_file_path}")

        self.trigger_room = rtc.Room()
        self.source = None
        self.mute_task = None
        self.raw_audio = b""
        self.sample_rate = 0
        self.num_channels = 0
        self.sample_width = 0

    async def start(self) -> None:
        """Connects the temporary participant and publishes the audio track."""
        # ── 1. Read and validate the WAV file ──────────────────────────────
        with wave.open(str(self.wav_file_path), "rb") as wav:
            self.sample_rate = wav.getframerate()
            self.num_channels = wav.getnchannels()
            self.sample_width = wav.getsampwidth()

            if self.sample_width != 2:
                raise ValueError(
                    f"WAV file must be 16-bit PCM (sampwidth=2), "
                    f"got sampwidth={self.sample_width}.  Re-encode the file with: "
                    f"ffmpeg -i {self.wav_file_path.name} -ar 48000 -ac 1 -sample_fmt s16 output.wav"
                )

            # Read all frames up-front
            self.raw_audio = wav.readframes(wav.getnframes())
            total_frames = wav.getnframes()

        logger.info(
            "audio_trigger: loaded %s — %d Hz, %d ch, %.2f s",
            self.wav_file_path.name,
            self.sample_rate,
            self.num_channels,
            total_frames / self.sample_rate,
        )

        # ── 2. Mint a short-lived access token for the trigger bot ─────────
        token = (
            api.AccessToken(self.key, self.secret)
            .with_identity(self.participant_identity)
            .with_name(self.participant_name)
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=self.room_name,
                    can_publish=True,
                    can_subscribe=False,
                )
            )
            .to_jwt()
        )

        # ── 3. Connect the temporary participant ───────────────────────────
        await self.trigger_room.connect(
            self.url,
            token,
            options=rtc.RoomOptions(auto_subscribe=False),
        )
        logger.info(
            "audio_trigger: connected to room '%s' as '%s'",
            self.room_name,
            self.participant_identity,
        )

        # ── 4. Create audio source & publish track ─────────────────────
        self.source = rtc.AudioSource(self.sample_rate, self.num_channels)
        track = rtc.LocalAudioTrack.create_audio_track("trigger-audio", self.source)
        publish_options = rtc.TrackPublishOptions(
            source=rtc.TrackSource.SOURCE_MICROPHONE,
        )
        publication = await self.trigger_room.local_participant.publish_track(
            track, publish_options
        )
        logger.info("audio_trigger: published track %s", publication.sid)

        # ── 5. Mute the trigger track for all real users ───────────────
        self.mute_task = asyncio.create_task(
            _mute_trigger_for_users(
                url=self.url,
                api_key=self.key,
                api_secret=self.secret,
                room_name=self.room_name,
                trigger_track_sid=publication.sid,
                trigger_identity=self.participant_identity,
            )
        )

    async def trigger(self, agent_session: "livekit.agents.AgentSession") -> None:
        """Wires the trigger bot into the agent's pipeline and streams audio."""
        try:
            # ── 6. Wire the trigger bot into the agent's audio pipeline ────
            original_linked_participant = agent_session.room_io.linked_participant
            original_identity = (
                original_linked_participant.identity
                if original_linked_participant
                else None
            )
            agent_session.room_io.set_participant(self.participant_identity)
            logger.info(
                "audio_trigger: switched AgentSession input from %s to %s",
                original_identity,
                self.participant_identity,
            )

            await asyncio.sleep(self.settle_delay)
            if self.mute_task:
                await self.mute_task

            # ── 7. Stream frames at real-time pace ─────────────────────────
            samples_per_chunk = self.sample_rate * _FRAME_DURATION_MS // 1000
            bytes_per_sample = self.sample_width * self.num_channels
            chunk_bytes = samples_per_chunk * bytes_per_sample
            sleep_duration = _FRAME_DURATION_MS / 1000.0

            offset = 0
            while offset < len(self.raw_audio):
                end = min(offset + chunk_bytes, len(self.raw_audio))
                chunk = self.raw_audio[offset:end]

                if len(chunk) < chunk_bytes:
                    chunk += b"\x00" * (chunk_bytes - len(chunk))

                frame = rtc.AudioFrame(
                    data=chunk,
                    sample_rate=self.sample_rate,
                    num_channels=self.num_channels,
                    samples_per_channel=samples_per_chunk,
                )
                await self.source.capture_frame(frame)
                await asyncio.sleep(sleep_duration)
                offset = end

            # Small trailing silence
            silence = b"\x00" * chunk_bytes
            for _ in range(10):
                frame = rtc.AudioFrame(
                    data=silence,
                    sample_rate=self.sample_rate,
                    num_channels=self.num_channels,
                    samples_per_channel=samples_per_chunk,
                )
                await self.source.capture_frame(frame)
                await asyncio.sleep(sleep_duration)

            logger.info("audio_trigger: finished streaming audio")

            await asyncio.sleep(0.5)

            # ── 8. Restore the original user in the agent's pipeline ───────
            agent_session.room_io.set_participant(original_identity)
            logger.info(
                "audio_trigger: restored AgentSession input back to %s",
                original_identity,
            )

        finally:
            # ── 9. Clean up — disconnect the temporary participant ─────────
            await self.trigger_room.disconnect()
            logger.info("audio_trigger: disconnected trigger participant")


async def trigger_agent_with_audio(
    agent_session: "livekit.agents.AgentSession",
    room_name: str,
    wav_file_path: str | os.PathLike | None = None,
    *,
    livekit_url: str | None = None,
    api_key: str | None = None,
    api_secret: str | None = None,
    participant_identity: str = _DEFAULT_TRIGGER_IDENTITY,
    participant_name: str = _DEFAULT_TRIGGER_NAME,
    settle_delay: float = 0.2,
) -> None:
    """Connect a temporary participant and stream a WAV file into the room."""
    trigger_obj = AudioTrigger(
        room_name=room_name,
        wav_file_path=wav_file_path,
        livekit_url=livekit_url,
        api_key=api_key,
        api_secret=api_secret,
        participant_identity=participant_identity,
        participant_name=participant_name,
        settle_delay=settle_delay,
    )
    await trigger_obj.start()
    await trigger_obj.trigger(agent_session)


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
