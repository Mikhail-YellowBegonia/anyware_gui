import unittest

from core.anyware.nonstandard_llm.client import _iter_sse_events


def _as_bytes(lines: list[str]) -> list[bytes]:
    return [line.encode("utf-8") for line in lines]


class TestSSEParser(unittest.TestCase):
    def test_basic_event(self) -> None:
        lines = _as_bytes(["data: {\"ok\": true}\n", "\n"])
        events = list(_iter_sse_events(lines))
        self.assertEqual(events, ['{"ok": true}'])

    def test_ignores_comments(self) -> None:
        lines = _as_bytes([": ping\n", "data: hello\n", "\n"])
        events = list(_iter_sse_events(lines))
        self.assertEqual(events, ["hello"])

    def test_multiline_event(self) -> None:
        lines = _as_bytes(["data: line1\n", "data: line2\n", "\n"])
        events = list(_iter_sse_events(lines))
        self.assertEqual(events, ["line1\nline2"])

    def test_flush_on_eof(self) -> None:
        lines = _as_bytes(["data: tail\n"])
        events = list(_iter_sse_events(lines))
        self.assertEqual(events, ["tail"])


if __name__ == "__main__":
    unittest.main()
