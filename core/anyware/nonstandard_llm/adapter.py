from __future__ import annotations

from typing import Iterable, Protocol

from .types import Message, ToolCallEvent


class LLMAdapter(Protocol):
    def stream_chat(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        tool_choice: str | None = None,
    ) -> Iterable[str | ToolCallEvent]:
        ...
