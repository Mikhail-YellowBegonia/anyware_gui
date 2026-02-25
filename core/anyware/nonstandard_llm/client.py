from __future__ import annotations

import json
import ssl
import sys
import urllib.error
import urllib.request
from typing import Iterable
from urllib.parse import urljoin

from .config import LLMConfig
from .types import Message, ToolCallEvent


class DeepSeekClient:
    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    def _build_payload(self, messages: list[Message], tools: list[dict] | None, tool_choice: str | None) -> dict:
        payload: dict = {
            "model": self.config.model,
            "messages": messages,
            "stream": True,
        }
        if self.config.temperature is not None:
            payload["temperature"] = self.config.temperature
        if self.config.top_p is not None:
            payload["top_p"] = self.config.top_p
        if self.config.max_tokens is not None:
            payload["max_tokens"] = self.config.max_tokens
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice
        return payload

    def stream_chat(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        tool_choice: str | None = None,
    ) -> Iterable[str | ToolCallEvent]:
        if not self.config.stream:
            raise ValueError("stream_chat requires stream=True in config")

        payload = self._build_payload(messages, tools, tool_choice)
        body = json.dumps(payload).encode("utf-8")
        url = urljoin(self.config.base_url.rstrip("/") + "/", "chat/completions")

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        context = ssl.create_default_context()

        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_s, context=context) as response:
                for event in _iter_sse_events(response):
                    if event == "[DONE]":
                        return

                    chunk = json.loads(event)
                    choices = chunk.get("choices", [])
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})
                    if not delta:
                        continue

                    if "tool_calls" in delta or "function_call" in delta:
                        yield ToolCallEvent(raw=delta)
                        continue

                    content = delta.get("content")
                    if content:
                        yield content
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {error_body}") from exc



def _iter_sse_events(response) -> Iterable[str]:
    data_lines: list[str] = []
    for raw_line in response:
        line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
        if not line:
            if data_lines:
                yield "\n".join(data_lines)
                data_lines.clear()
            continue
        if line.startswith(":"):
            continue
        if line.startswith("data:"):
            data_lines.append(line[len("data:") :].lstrip())
            continue
        # Ignore other SSE fields like id/event/retry.
    if data_lines:
        yield "\n".join(data_lines)


def render_tool_event(event: ToolCallEvent) -> None:
    print("\n[tool-call placeholder]", file=sys.stderr)
    print(json.dumps(event.raw, ensure_ascii=False, indent=2), file=sys.stderr)
