"""Browser speech adapter — the default, zero-install, $0 path.

Speech-to-text and text-to-speech both run in the *browser* using the Web Speech
API (``SpeechRecognition`` + ``speechSynthesis``), including client-side VAD and
barge-in. The server therefore never processes audio: the call websocket carries
plain text turns. This class is a marker/no-op so the factory can return a uniform
:class:`SpeechEngine`; calling ``stt``/``tts`` here is a programming error because
the server side has no audio in browser mode.
"""

from __future__ import annotations

from app.speech.base import SpeechEngine


class BrowserSpeech(SpeechEngine):
    name = "browser"
    server_side = False

    def stt(self, pcm: bytes) -> str:  # pragma: no cover - never called server-side
        raise NotImplementedError(
            "browser speech mode does STT in the client; the server exchanges text only"
        )

    def tts(self, text: str) -> bytes:  # pragma: no cover - never called server-side
        raise NotImplementedError(
            "browser speech mode does TTS in the client; the server exchanges text only"
        )
