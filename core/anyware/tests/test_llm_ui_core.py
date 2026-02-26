import unittest

from core.anyware.llm_ui import (
    BOLD_COLOR,
    CODE_COLOR,
    DEFAULT_COLOR,
    QUOTE_COLOR,
    ChatInputLine,
    ChatStreamBuffer,
    ChatDialogPanel,
    MarkdownSimplifier,
    TextLine,
    TextSpan,
    TextViewport,
)


class TestTextViewport(unittest.TestCase):
    def test_auto_follow_sets_scroll_offset(self) -> None:
        viewport = TextViewport(gx=0, gy=0, gw=10, gh=3)
        lines = [TextLine([TextSpan(text=str(i), color=DEFAULT_COLOR)]) for i in range(5)]
        viewport.set_lines(lines)
        self.assertEqual(viewport.scroll_offset, 2)
        self.assertTrue(viewport.is_at_bottom())

    def test_scroll_disables_auto_follow(self) -> None:
        viewport = TextViewport(gx=0, gy=0, gw=10, gh=3)
        lines = [TextLine([TextSpan(text=str(i), color=DEFAULT_COLOR)]) for i in range(5)]
        viewport.set_lines(lines)
        viewport.scroll(-1)
        self.assertEqual(viewport.scroll_offset, 1)
        self.assertFalse(viewport.auto_follow)
        viewport.jump_to_bottom()
        self.assertTrue(viewport.auto_follow)
        self.assertEqual(viewport.scroll_offset, 2)


class TestChatStreamBuffer(unittest.TestCase):
    def test_append_delta_multiline(self) -> None:
        buffer = ChatStreamBuffer()
        buffer.append_delta("Hello")
        buffer.append_delta("\nWorld")
        texts = [line.plain_text() for line in buffer.lines]
        self.assertEqual(texts, ["Hello", "World"])

    def test_reset_clears_lines(self) -> None:
        buffer = ChatStreamBuffer()
        buffer.append_delta("Hello")
        buffer.reset()
        self.assertEqual(buffer.lines, [])


class TestMarkdownSimplifier(unittest.TestCase):
    def test_inline_bold_and_code(self) -> None:
        spans = MarkdownSimplifier.parse_line("hello **bold** `code`")
        self.assertEqual([span.text for span in spans], ["hello ", "bold", " ", "code"])
        self.assertEqual([span.color for span in spans], [DEFAULT_COLOR, BOLD_COLOR, DEFAULT_COLOR, CODE_COLOR])

    def test_quote_line(self) -> None:
        spans = MarkdownSimplifier.parse_line("> quoted line")
        self.assertEqual([span.text for span in spans], ["quoted line"])
        self.assertEqual([span.color for span in spans], [QUOTE_COLOR])

    def test_heading_line(self) -> None:
        spans = MarkdownSimplifier.parse_line("## heading")
        self.assertEqual([span.text for span in spans], ["heading"])
        self.assertEqual([span.color for span in spans], [BOLD_COLOR])


class TestChatInputLine(unittest.TestCase):
    def test_insert_backspace_cursor(self) -> None:
        input_line = ChatInputLine(input_id="input", gx=0, gy=0, gw=10, gh=1)
        input_line.insert_text("hello")
        self.assertEqual(input_line.text, "hello")
        input_line.move_left()
        input_line.backspace()
        self.assertEqual(input_line.text, "helo")
        input_line.insert_text("l")
        self.assertEqual(input_line.text, "hello")


class DummyToolEvent:
    def __init__(self, payload: dict):
        self.payload = payload


class TestChatDialogPanel(unittest.TestCase):
    def test_streaming_updates_viewport(self) -> None:
        viewport = TextViewport(gx=0, gy=0, gw=12, gh=2)
        input_line = ChatInputLine(input_id="input", gx=0, gy=3, gw=12, gh=1)
        panel = ChatDialogPanel(panel_id="panel", viewport=viewport, input_line=input_line)

        panel.start_stream(iter(["Hello", " world"]))
        panel.poll_stream()

        self.assertEqual([line.plain_text() for line in viewport.lines], ["Hello world"])

    def test_tool_event_sets_status(self) -> None:
        viewport = TextViewport(gx=0, gy=0, gw=12, gh=2)
        input_line = ChatInputLine(input_id="input", gx=0, gy=3, gw=12, gh=1)
        panel = ChatDialogPanel(panel_id="panel", viewport=viewport, input_line=input_line)

        panel.start_stream(iter([DummyToolEvent({"tool": "x"})]))
        panel.poll_stream()

        self.assertIn("tool", panel.status_message)

    def test_append_user_splits_multiline(self) -> None:
        viewport = TextViewport(gx=0, gy=0, gw=12, gh=3)
        input_line = ChatInputLine(input_id="input", gx=0, gy=4, gw=12, gh=1)
        panel = ChatDialogPanel(panel_id="panel", viewport=viewport, input_line=input_line)

        panel.append_user("first line\nsecond line")

        self.assertEqual([line.plain_text() for line in viewport.lines], ["first line", "second line"])


if __name__ == "__main__":
    unittest.main()
