"""Telephony port — the bidirectional audio contract for a call.

The audio format mirrors Vonage's websocket media contract (research 230001) so the
LocalSim browser softphone (Phase 2) and the real Vonage adapter (Phase 6) are
interchangeable behind this interface: **16 kHz, 16-bit signed little-endian, mono
PCM, in ~20 ms frames**.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

# Audio contract (identical on LocalSim and Vonage).
AUDIO_RATE = 16000          # Hz
SAMPLE_WIDTH = 2            # bytes per sample (16-bit)
CHANNELS = 1               # mono
FRAME_MS = 20              # frame duration
FRAME_BYTES = AUDIO_RATE * SAMPLE_WIDTH * FRAME_MS // 1000   # 640 bytes/frame


class TelephonyPort(ABC):
    """A live call's audio channel with the remote party.

    Concrete adapters implement the streaming details. The conversation orchestrator
    reads caller audio via `recv_audio()`, sends agent audio via `send_audio()`, and
    calls `clear()` to cut off playback on barge-in (maps to Vonage `{"action":"clear"}`).
    """

    name: str = "telephony"

    @abstractmethod
    async def recv_audio(self) -> bytes | None:
        """Next inbound PCM frame from the caller, or None when the call ends."""

    @abstractmethod
    async def send_audio(self, pcm: bytes) -> None:
        """Queue agent PCM audio for playback to the caller."""

    @abstractmethod
    async def clear(self) -> None:
        """Immediately stop/flush queued playback (barge-in)."""

    @abstractmethod
    async def hangup(self) -> None:
        """End the call."""
