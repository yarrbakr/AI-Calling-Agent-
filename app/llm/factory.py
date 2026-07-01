"""Build the active LLM from config / available keys.

Preference for `LLM_BACKEND=auto` (the default): free **Mistral** → **Claude** →
offline **canned**. So a free Mistral key gives a real brain at $0, Claude is a
premium swap, and with no keys at all it still runs (canned).
"""

from __future__ import annotations

import logging

from app.config import Settings, settings as _default_settings
from app.llm.base import LLM, LLMReply
from app.llm.canned import CannedLLM

log = logging.getLogger(__name__)


def get_llm(
    settings: Settings | None = None,
    *,
    realtime: bool = False,
    script: list[LLMReply] | None = None,
) -> LLM:
    """Return the configured LLM. `realtime=True` picks a lower-latency model for
    live calls. `script` only applies to the canned backend.

    Mock-first safety net: if the chosen provider's SDK can't be imported or its
    client can't be built (missing/broken dep), we log and fall back to the
    offline `canned` brain so the app never crashes on a bad dependency.
    """
    s = settings or _default_settings
    backend = s.active_llm_backend()

    try:
        if backend == "mistral":
            from app.llm.mistral import MistralLLM

            model = s.mistral_model_realtime if realtime else s.mistral_model
            return MistralLLM(s.mistral_api_key, model)

        if backend == "claude":
            from app.llm.claude import ClaudeLLM

            model = s.anthropic_model_realtime if realtime else s.anthropic_model
            return ClaudeLLM(s.anthropic_api_key, model)

        if backend == "ollama":
            from app.llm.ollama import OllamaLLM

            return OllamaLLM(s.ollama_host, s.ollama_model)
    except Exception as exc:  # noqa: BLE001 - degrade instead of crashing the call
        log.warning("LLM backend %r unavailable (%s); falling back to canned.", backend, exc)

    return CannedLLM(script=script)
