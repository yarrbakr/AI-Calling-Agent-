"""Canned (offline, $0) LLM.

Returns scripted replies in order, so the whole system runs and tests are fully
deterministic without any API key or network. Agents/tests inject a `script`
(a list of `LLMReply`); when the script is exhausted it falls back to a polite
default. This is what powers the guaranteed-$0 demo and CI.
"""

from __future__ import annotations

from typing import Any

from app.llm.base import LLM, LLMReply, ToolSpec


class CannedLLM(LLM):
    name = "canned"

    def __init__(self, script: list[LLMReply] | None = None, default_text: str | None = None):
        self._script = list(script or [])
        self._i = 0
        self._default = default_text or "Okay, thank you. I'll make a note of that."

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[ToolSpec] | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> LLMReply:
        if self._i < len(self._script):
            reply = self._script[self._i]
            self._i += 1
            return reply
        return LLMReply(text=self._default, stop_reason="end")
