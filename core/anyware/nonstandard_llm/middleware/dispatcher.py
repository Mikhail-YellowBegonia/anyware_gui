from __future__ import annotations

from .parser import parse_intent
from .registry import ToolRegistry
from .types import ToolCall, ToolResult, ToolSpec


class ToolDispatcher:
    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def handle_text(self, text: str) -> tuple[str | None, ToolResult | None, ToolCall | None]:
        call = parse_intent(text)
        if call is None:
            return text, None, None
        spec = self._registry.get(call.name)
        if spec is None:
            return None, ToolResult.failure(f"Unknown tool: {call.name}"), call
        ok, err = _validate_args(spec, call.args)
        if not ok:
            return None, ToolResult.failure(err or "Invalid tool arguments"), call
        try:
            result = spec.handler(call.args)
        except Exception as exc:  # pragma: no cover - call sites should surface
            result = ToolResult.failure(str(exc))
        return None, result, call


def _validate_args(spec: ToolSpec, args: dict[str, object]) -> tuple[bool, str | None]:
    schema = spec.args_schema or {}
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    if not isinstance(required, list):
        required = []
    if not isinstance(properties, dict):
        properties = {}
    for key in required:
        if key not in args:
            return False, f"Missing required arg: {key}"
    for key, value in args.items():
        prop = properties.get(key)
        if not isinstance(prop, dict):
            continue
        expected = prop.get("type")
        if expected is None:
            continue
        if not _check_type(expected, value):
            return False, f"Invalid type for arg '{key}': expected {expected}"
    return True, None


def _check_type(expected: str, value: object) -> bool:
    match expected:
        case "string":
            return isinstance(value, str)
        case "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        case "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        case "boolean":
            return isinstance(value, bool)
        case "array":
            return isinstance(value, list)
        case "object":
            return isinstance(value, dict)
        case _:
            return True
