# audio_trigger.py — pushes a WAV directly into the realtime model's
# input buffer, bypassing LiveKit rooms/tracks entirely.

import asyncio
import logging
import wave
from pathlib import Path

from livekit import rtc
from livekit.agents import llm

logger = logging.getLogger(__name__)

_FRAME_DURATION_MS = 20


async def trigger_agent_with_audio(
    rt_session: llm.RealtimeSession,
    wav_file_path: str,
) -> None:
    """Feed a WAV file into the model's audio input as if it were user speech."""
    with wave.open(wav_file_path, "rb") as wav:
        sample_rate = wav.getframerate()
        num_channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        if sample_width != 2:
            raise ValueError("WAV must be 16-bit PCM")
        raw_audio = wav.readframes(wav.getnframes())

    samples_per_chunk = sample_rate * _FRAME_DURATION_MS // 1000
    bytes_per_sample = sample_width * num_channels
    chunk_bytes = samples_per_chunk * bytes_per_sample

    offset = 0
    while offset < len(raw_audio):
        end = min(offset + chunk_bytes, len(raw_audio))
        chunk = raw_audio[offset:end]
        if len(chunk) < chunk_bytes:
            chunk += b"\x00" * (chunk_bytes - len(chunk))

        frame = rtc.AudioFrame(
            data=chunk,
            sample_rate=sample_rate,
            num_channels=num_channels,
            samples_per_channel=samples_per_chunk,
        )
        rt_session.push_audio(frame)
        offset = end

    logger.info("audio_trigger: finished pushing %s into realtime session", wav_file_path)
