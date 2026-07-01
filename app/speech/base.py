"""Speech port — the STT + TTS contract the voice agent talks to.

Same design language as the rest of the app (ports + adapters, mock-first): the
conversation orchestrator never cares *how* speech happens, only that it can turn
caller audio into text and agent text into audio.

Two adapters implement it:

* ``BrowserSpeech`` (default) — speech runs **client-side** in the browser via the
  Web Speech API. It is ``server_side = False``: the server exchanges *text* over
  the websocket and never touches audio. Zero install, $0, always works — the
  reliable path for the hero demo.
* ``LocalSpeech`` (env-gated) — speech runs **server-side** with faster-whisper +
  Piper over the 16 kHz PCM telephony contract (:mod:`app.telephony.base`). It is
  ``server_side = True`` and is a drop-in for the real Vonage media path later.

Audio, when it flows server-side, uses the telephony contract: 16 kHz, 16-bit
signed little-endian, mono PCM.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class SpeechEngine(ABC):
    """Bidirectional speech for a call: PCM <-> text."""

    name: str = "speech"

    #: When False, the browser does STT/TTS and the server exchanges text only.
    #: When True, the server runs STT/TTS on PCM audio itself.
    server_side: bool = False

    @abstractmethod
    def stt(self, pcm: bytes) -> str:
        """Transcribe a chunk of caller PCM audio to text."""

    @abstractmethod
    def tts(self, text: str) -> bytes:
        """Synthesize agent text to PCM audio (16 kHz mono, 16-bit LE)."""
