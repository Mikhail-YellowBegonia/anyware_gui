from __future__ import annotations

import json
from typing import Iterable

from .types import ToolCall

_CALL_PREFIX = "[CALL]"
_FENCE_START = "```tool"
_FENCE_END = "```"


def parse_intent(text: str | None) -> ToolCall | None:
    if not text:
        return None
    raw = text if isinstance(text, str) else str(text)
    fenced = _parse_fenced_block(raw)
    if fenced is not None:
        return fenced
    for line in raw.splitlines():
        candidate = _parse_call_line(line)
        if candidate is not None:
            return candidate
    return None


def _parse_fenced_block(text: str) -> ToolCall | None:
    lines = text.splitlines()
    start_idx = _find_fence(lines, _FENCE_START)
    if start_idx is None:
        return None
    end_idx = _find_fence(lines[start_idx + 1 :], _FENCE_END)
    if end_idx is None:
        return None
    payload_lines = lines[start_idx + 1 : start_idx + 1 + end_idx]
    payload = "\n".join(payload_lines).strip()
    if not payload:
        return None
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    name = data.get("name")
    args = data.get("args", {})
    if not isinstance(name, str):
        return None
    if not isinstance(args, dict):
        return None
    return ToolCall(name=name, args=args, raw=payload)


def _find_fence(lines: Iterable[str], fence: str) -> int | None:
    for idx, line in enumerate(lines):
        if line.strip().startswith(fence):
            return idx
    return None


def _parse_call_line(line: str) -> ToolCall | None:
    stripped = line.strip()
    if not stripped.startswith(_CALL_PREFIX):
        return None
    rest = stripped[len(_CALL_PREFIX) :].strip()
    if not rest:
        return None
    if " " in rest:
        name, payload = rest.split(None, 1)
        payload = payload.strip()
        if not payload:
            args = {}
        else:
            try:
                args = json.loads(payload)
            except json.JSONDecodeError:
                return None
    else:
        name = rest
        args = {}
    if not isinstance(args, dict):
        return None
    return ToolCall(name=name, args=args, raw=stripped)
