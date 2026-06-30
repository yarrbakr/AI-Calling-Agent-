"""The LLM port: a small, provider-neutral abstraction for tool-using chat.

Design goals
------------
* Agents build a list of **neutral messages** and a list of **Tools**, then call
  `run_tool_loop(...)`. They never see provider-specific shapes.
* Each adapter (`claude`, `mistral`, `ollama`, `canned`) translates the neutral
  format to/from its own API.

Neutral message format (a list of dicts):
    {"role": "user",      "content": "<text>"}
    {"role": "assistant", "content": "<text>", "tool_calls": [ToolCall, ...]}
    {"role": "tool",      "tool_call_id": "<id>", "content": "<stringified result>"}
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


# --------------------------------------------------------------------------- #
# Value types
# --------------------------------------------------------------------------- #
@dataclass
class ToolSpec:
    """The declaration of a tool sent to the model."""

    name: str
    description: str
    input_schema: dict[str, Any]  # JSON Schema for the arguments object


@dataclass
class ToolCall:
    """A model's request to call a tool."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMReply:
    """A single model response: free text and/or tool-call requests."""

    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end"
    raw: Any = None


@dataclass
class Tool:
    """A tool spec bundled with the function that executes it."""

    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[[dict[str, Any]], Any]

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(self.name, self.description, self.input_schema)


# --------------------------------------------------------------------------- #
# Neutral message builders
# --------------------------------------------------------------------------- #
def user_msg(text: str) -> dict[str, Any]:
    return {"role": "user", "content": text}


def assistant_msg(text: str = "", tool_calls: list[ToolCall] | None = None) -> dict[str, Any]:
    return {"role": "assistant", "content": text or "", "tool_calls": tool_calls or []}


def tool_result_msg(tool_call_id: str, content: Any) -> dict[str, Any]:
    if not isinstance(content, str):
        content = json.dumps(content, default=str)
    return {"role": "tool", "tool_call_id": tool_call_id, "content": content}


# --------------------------------------------------------------------------- #
# The port
# --------------------------------------------------------------------------- #
class LLM(ABC):
    """A chat model that can optionally use tools."""

    name: str = "llm"

    @abstractmethod
    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[ToolSpec] | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> LLMReply:
        """One model turn over the neutral message list."""
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Tool-use loop (the thing agents actually call)
# --------------------------------------------------------------------------- #
def run_tool_loop(
    llm: LLM,
    *,
    system: str,
    messages: list[dict[str, Any]],
    tools: list[Tool] | None = None,
    max_steps: int = 8,
    max_tokens: int = 1024,
    temperature: float = 0.3,
    on_event: Callable[[str, Any], None] | None = None,
) -> LLMReply:
    """Drive a full reason→act loop.

    Appends the assistant reply and any tool results onto `messages` in place, and
    returns the final (text) reply once the model stops requesting tools.
    """
    tools = tools or []
    tool_map = {t.name: t for t in tools}
    specs = [t.spec for t in tools] or None

    reply = LLMReply()
    for _ in range(max_steps):
        reply = llm.complete(
            system=system,
            messages=messages,
            tools=specs,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        messages.append(assistant_msg(reply.text, reply.tool_calls))
        if on_event and reply.text:
            on_event("assistant_text", reply.text)

        if not reply.tool_calls:
            return reply

        for tc in reply.tool_calls:
            if on_event:
                on_event("tool_call", tc)
            tool = tool_map.get(tc.name)
            if tool is None:
                result: Any = {"error": f"unknown tool '{tc.name}'"}
            else:
                try:
                    result = tool.handler(tc.arguments)
                except Exception as exc:  # surface tool errors back to the model
                    result = {"error": f"{type(exc).__name__}: {exc}"}
            if on_event:
                on_event("tool_result", {"name": tc.name, "result": result})
            messages.append(tool_result_msg(tc.id, result))

    return reply
