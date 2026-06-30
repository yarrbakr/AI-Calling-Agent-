"""Anthropic Claude adapter.

Translates the neutral message format to Anthropic's content-block API and back.
Tool results are Anthropic `tool_result` blocks carried on a *user* turn; runs of
consecutive neutral `tool` messages are coalesced into one user turn so the
required user/assistant alternation holds.
"""

from __future__ import annotations

from typing import Any

from app.llm.base import LLM, LLMReply, ToolCall, ToolSpec


class ClaudeLLM(LLM):
    name = "claude"

    def __init__(self, api_key: str, model: str):
        from anthropic import Anthropic  # imported lazily so the dep is optional

        self._client = Anthropic(api_key=api_key)
        self.model = model

    @staticmethod
    def _to_anthropic_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        pending_tool_results: list[dict[str, Any]] = []

        def flush_tool_results() -> None:
            if pending_tool_results:
                out.append({"role": "user", "content": list(pending_tool_results)})
                pending_tool_results.clear()

        for m in messages:
            role = m["role"]
            if role == "tool":
                pending_tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": m["tool_call_id"],
                        "content": m.get("content", ""),
                    }
                )
                continue

            flush_tool_results()
            if role == "user":
                out.append({"role": "user", "content": m["content"]})
            elif role == "assistant":
                blocks: list[dict[str, Any]] = []
                if m.get("content"):
                    blocks.append({"type": "text", "text": m["content"]})
                for tc in m.get("tool_calls", []):
                    blocks.append(
                        {
                            "type": "tool_use",
                            "id": tc.id,
                            "name": tc.name,
                            "input": tc.arguments,
                        }
                    )
                out.append({"role": "assistant", "content": blocks or m.get("content", "")})

        flush_tool_results()
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
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": self._to_anthropic_messages(messages),
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = [
                {"name": t.name, "description": t.description, "input_schema": t.input_schema}
                for t in tools
            ]

        resp = self._client.messages.create(**kwargs)

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(id=block.id, name=block.name, arguments=dict(block.input)))

        return LLMReply(
            text="".join(text_parts).strip(),
            tool_calls=tool_calls,
            stop_reason=resp.stop_reason or "end",
            raw=resp,
        )
