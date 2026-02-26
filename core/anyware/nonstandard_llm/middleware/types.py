from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict[str, object]
    raw: str | None = None


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    output: str
    data: dict[str, object] | None = None
    error: str | None = None

    @staticmethod
    def success(output: str, *, data: dict[str, object] | None = None) -> "ToolResult":
        return ToolResult(ok=True, output=output, data=data, error=None)

    @staticmethod
    def failure(error: str) -> "ToolResult":
        return ToolResult(ok=False, output="", data=None, error=error)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    args_schema: dict[str, object] | None
    handler: Callable[[dict[str, object]], ToolResult]
    requires_confirm: bool = False
