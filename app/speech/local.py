"""Local speech adapter — offline server-side STT + TTS.

The env-gated "real" speech path: faster-whisper for STT and Piper for TTS, over
the 16 kHz mono PCM contract in :mod:`app.telephony.base`. Fully offline and $0
once the voice deps + models are present, and a drop-in for the real Vonage media
websocket in Phase 6.

Heavy dependencies (``faster-whisper``, ``piper-tts``, ``numpy``) are imported
lazily inside the methods, so importing this module never drags them in and the
default browser path installs nothing extra. Selecting ``SPEECH_MODE=local``
without the deps raises a clear, actionable error.

NOTE: This adapter is implemented but not exercised in the Phase 2 browser demo;
the models are downloaded on first use. See progress.md.
"""

from __future__ import annotations

import io
import wave

from app.config import Settings
from app.config import settings as _default_settings
from app.speech.base import SpeechEngine
from app.telephony.base import AUDIO_RATE


def _missing(dep: str, pkg: str) -> ImportError:
    return ImportError(
        f"SPEECH_MODE=local needs '{dep}'. Install the voice stack into the shared venv:\n"
        f"    .venv/Scripts/python.exe -m pip install {pkg}"
    )


class LocalSpeech(SpeechEngine):
    name = "local"
    server_side = True

    def __init__(self, settings: Settings | None = None) -> None:
        self._s = settings or _default_settings
        self._whisper = None  # lazy faster-whisper model
        self._piper = None    # lazy piper voice

    # --- STT: faster-whisper ------------------------------------------------
    def _get_whisper(self):
        if self._whisper is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:  # pragma: no cover - optional dep
                raise _missing("faster-whisper", "faster-whisper") from exc
            # int8 on CPU keeps it light; model auto-downloads on first use.
            self._whisper = WhisperModel(self._s.whisper_model, device="cpu", compute_type="int8")
        return self._whisper

    def stt(self, pcm: bytes) -> str:
        try:
            import numpy as np
        except ImportError as exc:  # pragma: no cover - optional dep
            raise _missing("numpy", "numpy") from exc
        model = self._get_whisper()
        # 16-bit LE PCM -> float32 in [-1, 1], which faster-whisper accepts directly.
        audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
        segments, _ = model.transcribe(audio, language="en", vad_filter=True)
        return " ".join(seg.text.strip() for seg in segments).strip()

    # --- TTS: Piper ---------------------------------------------------------
    def _get_piper(self):
        if self._piper is None:
            try:
                from piper import PiperVoice
            except ImportError as exc:  # pragma: no cover - optional dep
                raise _missing("piper-tts", "piper-tts") from exc
            self._piper = PiperVoice.load(self._s.piper_voice)
        return self._piper

    def tts(self, text: str) -> bytes:
        voice = self._get_piper()
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(AUDIO_RATE)
            voice.synthesize(text, wav)
        # Return raw PCM frames (strip the WAV header) to match the telephony contract.
        buf.seek(0)
        with wave.open(buf, "rb") as wav:
            return wav.readframes(wav.getnframes())
