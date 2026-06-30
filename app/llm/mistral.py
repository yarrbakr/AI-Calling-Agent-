"""Mistral adapter (La Plateforme).

Uses the `mistralai` SDK. The neutral format maps almost 1:1 onto Mistral's
OpenAI-style chat shape: assistant turns carry `tool_calls`, and each tool result
is its own `{"role": "tool", ...}` message. Mistral returns tool-call arguments as
a JSON *string*, so we parse them back to a dict.

Mistral's free "Experiment" tier supports function calling, which is what our
agents rely on — see research/20260630-230002... and the Mistral docs.
"""

from __future__ import annotations

import json
from typing import Any

from app.llm.base import LLM, LLMReply, ToolCall, ToolSpec


class MistralLLM(LLM):
    name = "mistral"

    def __init__(self, api_key: str, model: str):
        from mistralai import Mistral  # lazy import keeps the dep optional

        self._client = Mistral(api_key=api_key)
        self.model = model

    @staticmethod
    def _to_mistral_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for m in messages:
            role = m["role"]
            if role == "user":
                out.append({"role": "user", "content": m["content"]})
            elif role == "tool":
                out.append(
                    {
                        "role": "tool",
                        "tool_call_id": m["tool_call_id"],
                        "content": m.get("content", ""),
                    }
                )
            elif role == "assistant":
                msg: dict[str, Any] = {"role": "assistant", "content": m.get("content", "")}
                tcs = m.get("tool_calls", [])
                if tcs:
                    msg["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            },
                        }
                        for tc in tcs
                    ]
                out.append(msg)
        return out

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[ToolSpec] | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> LLMReply:
        chat_messages: list[dict[str, Any]] = []
        if system:
            chat_messages.append({"role": "system", "content": system})
        chat_messages.extend(self._to_mistral_messages(messages))

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.input_schema,
                    },
                }
                for t in tools
            ]
            kwargs["tool_choice"] = "auto"

        resp = self._client.chat.complete(**kwargs)
        msg = resp.choices[0].message

        tool_calls: list[ToolCall] = []
        for tc in (msg.tool_calls or []):
            args = tc.function.arguments
            if isinstance(args, str):
                try:
                    args = json.loads(args or "{}")
                except json.JSONDecodeError:
                    args = {}
            tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))

        return LLMReply(
            text=(msg.content or "").strip() if isinstance(msg.content, str) else "",
            tool_calls=tool_calls,
            stop_reason=resp.choices[0].finish_reason or "end",
            raw=resp,
        )
