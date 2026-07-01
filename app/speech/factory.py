"""Pick the active speech engine from config.

Default ``SPEECH_MODE=browser`` (zero-install, $0, client-side speech). Set
``SPEECH_MODE=local`` to run faster-whisper + Piper server-side (needs the voice
deps). Same shape as the CRM/ATS/telephony factories.
"""

from __future__ import annotations

from app.config import Settings
from app.config import settings as _default_settings
from app.speech.base import SpeechEngine


def get_speech(settings: Settings | None = None) -> SpeechEngine:
    s = settings or _default_settings
    if (s.speech_mode or "browser").lower() == "local":
        from app.speech.local import LocalSpeech

        return LocalSpeech(s)
    from app.speech.browser import BrowserSpeech

    return BrowserSpeech()
