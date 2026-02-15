import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.anyware.page import Page, PageStack


class DummyPage(Page):
    def __init__(self, page_id: str, log: list[str]):
        super().__init__(page_id)
        self.log = log

    def on_enter(self, ctx) -> None:
        self.log.append(f"enter:{self.page_id}")

    def on_exit(self, ctx) -> None:
        self.log.append(f"exit:{self.page_id}")


def test_page_stack_push_pop_calls_hooks():
    ctx = object()
    stack = PageStack()
    log: list[str] = []
    p1 = DummyPage("p1", log)
    p2 = DummyPage("p2", log)

    stack.push(p1, ctx)
    stack.push(p2, ctx)
    stack.pop(ctx)

    assert log == ["enter:p1", "exit:p1", "enter:p2", "exit:p2", "enter:p1"]
