import unittest

from core.anyware.nonstandard_llm.middleware.dispatcher import ToolDispatcher
from core.anyware.nonstandard_llm.middleware.parser import parse_intent
from core.anyware.nonstandard_llm.middleware.registry import ToolRegistry
from core.anyware.nonstandard_llm.middleware.types import ToolResult, ToolSpec


def _echo_tool(args: dict[str, object]) -> ToolResult:
    return ToolResult.success(f"echo:{args.get('value')}")


class TestMiddlewareParser(unittest.TestCase):
    def test_parse_call_line(self) -> None:
        call = parse_intent('[CALL] echo {"value": 3}')
        self.assertIsNotNone(call)
        assert call is not None
        self.assertEqual(call.name, "echo")
        self.assertEqual(call.args["value"], 3)

    def test_parse_fenced_block(self) -> None:
        text = "```tool\n{\"name\":\"echo\",\"args\":{\"value\":1}}\n```"
        call = parse_intent(text)
        self.assertIsNotNone(call)
        assert call is not None
        self.assertEqual(call.name, "echo")
        self.assertEqual(call.args["value"], 1)

    def test_parse_invalid_json(self) -> None:
        call = parse_intent('[CALL] echo {"value": }')
        self.assertIsNone(call)


class TestMiddlewareDispatcher(unittest.TestCase):
    def test_dispatcher_unknown_tool(self) -> None:
        registry = ToolRegistry()
        dispatcher = ToolDispatcher(registry)
        text, result, call = dispatcher.handle_text('[CALL] missing {"value":1}')
        self.assertIsNone(text)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertFalse(result.ok)
        self.assertIn("Unknown tool", result.error or "")
        self.assertIsNotNone(call)

    def test_dispatcher_validates_args(self) -> None:
        registry = ToolRegistry()
        registry.register(
            ToolSpec(
                name="echo",
                description="echo value",
                args_schema={"required": ["value"], "properties": {"value": {"type": "number"}}},
                handler=_echo_tool,
            )
        )
        dispatcher = ToolDispatcher(registry)
        text, result, call = dispatcher.handle_text('[CALL] echo {"value":"x"}')
        self.assertIsNone(text)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertFalse(result.ok)
        self.assertIn("Invalid type", result.error or "")
        self.assertIsNotNone(call)

    def test_dispatcher_runs_tool(self) -> None:
        registry = ToolRegistry()
        registry.register(
            ToolSpec(
                name="echo",
                description="echo value",
                args_schema={"required": ["value"], "properties": {"value": {"type": "number"}}},
                handler=_echo_tool,
            )
        )
        dispatcher = ToolDispatcher(registry)
        text, result, call = dispatcher.handle_text('[CALL] echo {"value":7}')
        self.assertIsNone(text)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertTrue(result.ok)
        self.assertEqual(result.output, "echo:7")
        self.assertIsNotNone(call)


if __name__ == "__main__":
    unittest.main()
