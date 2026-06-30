"""Local Ollama adapter (truly $0, offline).

Talks to a local `ollama serve` via /api/chat. Newer Ollama supports tool calling;
small local models do it less reliably than hosted Claude/Mistral, so this is best
for text-heavy flows. Wired here so it's ready once Ollama is stable on this box.
"""

from __future__ import annotations

import json
from typing import Any

import requests

from app.llm.base import LLM, LLMReply, ToolCall, ToolSpec


class OllamaLLM(LLM):
    name = "ollama"

    def __init__(self, host: str, model: str):
        self.host = host.rstrip("/")
        self.model = model

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[ToolSpec] | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> LLMReply:
        chat: list[dict[str, Any]] = []
        if system:
            chat.append({"role": "system", "content": system})
        for m in messages:
            if m["role"] == "user":
                chat.append({"role": "user", "content": m["content"]})
            elif m["role"] == "tool":
                chat.append({"role": "tool", "content": m.get("content", "")})
            elif m["role"] == "assistant":
                a: dict[str, Any] = {"role": "assistant", "content": m.get("content", "")}
                if m.get("tool_calls"):
                    a["tool_calls"] = [
                        {"function": {"name": tc.name, "arguments": tc.arguments}}
                        for tc in m["tool_calls"]
                    ]
                chat.append(a)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": chat,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if tools:
            payload["tools"] = [
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

        r = requests.post(f"{self.host}/api/chat", json=payload, timeout=600)
        r.raise_for_status()
        msg = r.json().get("message", {})

        tool_calls: list[ToolCall] = []
        for i, tc in enumerate(msg.get("tool_calls") or []):
            fn = tc.get("function", {})
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            tool_calls.append(ToolCall(id=f"ollama-{i}", name=fn.get("name", ""), arguments=args))

        return LLMReply(text=(msg.get("content") or "").strip(), tool_calls=tool_calls, raw=msg)
