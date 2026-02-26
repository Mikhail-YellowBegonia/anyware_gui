from __future__ import annotations

from typing import Iterable
import os
from queue import SimpleQueue
import threading

from _bootstrap import FONTS_DIR, ensure_repo_root_on_path

ensure_repo_root_on_path()

from core.anyware import (
    AnywareApp,
    ChatDialogPanel,
    ChatInputLine,
    Label,
    Page,
    TextViewport,
)
from core.anyware.nonstandard_llm.client import DeepSeekClient
from core.anyware.nonstandard_llm.config import load_config
from core.anyware.nonstandard_llm.types import ToolCallEvent


_STREAM_DONE = object()


class LLMStreamSession:
    def __init__(self, panel: ChatDialogPanel, client: DeepSeekClient) -> None:
        self._panel = panel
        self._client = client
        self._queue: SimpleQueue[object] = SimpleQueue()
        self._done = False
        self._thread: threading.Thread | None = None

    @property
    def done(self) -> bool:
        return self._done

    def start(self, messages: list[dict]) -> None:
        def _run() -> None:
            try:
                for event in self._client.stream_chat(messages):
                    self._queue.put(event)
            except Exception as exc:  # pragma: no cover - surfaced to UI
                self._queue.put(exc)
            finally:
                self._queue.put(_STREAM_DONE)

        self._panel.status_message = "llm streaming..."
        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def poll(self) -> None:
        while not self._queue.empty():
            item = self._queue.get_nowait()
            if item is _STREAM_DONE:
                self._done = True
                self._panel.status_message = ""
                return
            if isinstance(item, Exception):
                self._panel.append_error(str(item))
                self._done = True
                self._panel.status_message = ""
                return
            if isinstance(item, ToolCallEvent):
                self._panel.status_message = "tool-call placeholder"
                self._done = True
                return
            if isinstance(item, str):
                self._panel.append_assistant_delta(item)


class LLMUIDemoPage(Page):
    def __init__(self):
        super().__init__("llm_ui_demo")
        self.viewport = TextViewport(viewport_id="llm_viewport", gx=2, gy=4, gw=56, gh=16, scope="main")
        self.input_line = ChatInputLine(
            input_id="llm_input",
            gx=2,
            gy=21,
            gw=56,
            gh=6,
            scope="main",
            on_send=self._on_send,
        )
        self.panel = ChatDialogPanel(panel_id="llm_panel", viewport=self.viewport, input_line=self.input_line)
        self.status = Label(
            gx=2,
            gy=1,
            gw=56,
            gh=1,
            text=lambda _: self.panel.status_message,
            color="CRT_Green",
        )
        self.hint = Label(
            gx=2,
            gy=2,
            gw=56,
            gh=1,
            text="TAB:focus  CTRL+ENTER:send  UP/DOWN:scroll  /tool:placeholder",
            color="CRT_Cyan",
        )

        self.add(self.status)
        self.add(self.hint)
        self.add(self.panel)

        self._focus_ids = [self.input_line.input_id, self.viewport.component_id]
        self._focus_index = 0
        self._llm_client: DeepSeekClient | None = None
        self._llm_session: LLMStreamSession | None = None

    def on_enter(self, ctx) -> None:
        ctx.set_active_focus_scope("main")
        ctx.set_focus(self.input_line.input_id)

    def handle_event(self, event, ctx) -> bool:
        import pygame

        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            self._cycle_focus(ctx)
            return True
        return super().handle_event(event, ctx)

    def update(self, ctx, dt: float) -> None:
        if self._llm_session is not None:
            self._llm_session.poll()
            if self._llm_session.done:
                self._llm_session = None
        else:
            self.panel.poll_stream()
        super().update(ctx, dt)

    def render(self, ctx) -> None:
        self._draw_borders(ctx)
        super().render(ctx)
        ctx.draw_focus_frame("blink18", padding=2.0, thickness=1.2)

    def _cycle_focus(self, ctx) -> None:
        self._focus_index = (self._focus_index + 1) % len(self._focus_ids)
        ctx.set_focus(self._focus_ids[self._focus_index])

    def _draw_borders(self, ctx) -> None:
        for component in (self.viewport, self.input_line):
            x1 = ctx.gx(component.gx)
            y1 = ctx.gy(component.gy)
            x2 = ctx.gx(component.gx + component.gw)
            y2 = ctx.gy(component.gy + component.gh)
            ctx.draw_rect("CRT_Cyan", x1, y1, x2 - x1, y2 - y1, filled=False, thickness=1)

    def _ensure_client(self) -> DeepSeekClient | None:
        if self._llm_client is not None:
            return self._llm_client
        config_path = os.environ.get("ANYWARE_LLM_CONFIG")
        try:
            config = load_config(config_path)
        except Exception as exc:
            self.panel.append_error(f"LLM config not available: {exc}")
            return None
        self._llm_client = DeepSeekClient(config)
        return self._llm_client

    def _on_send(self, text: str) -> None:
        raw = text.strip()
        if not raw:
            return
        if self._llm_session is not None:
            self.panel.append_system_message("LLM busy; wait for current response.", color="CRT_Yellow")
            return
        self.panel.append_user(raw)
        self.panel.stream_buffer.reset()
        if raw.lower().startswith("/tool"):
            self.panel.start_stream(iter([{"tool": "placeholder"}]))
        else:
            client = self._ensure_client()
            if client is None:
                self.panel.start_stream(iter(self._simulate_response(raw)))
            else:
                session = LLMStreamSession(self.panel, client)
                session.start([{"role": "user", "content": raw}])
                self._llm_session = session
        self.input_line.clear()

    def _simulate_response(self, text: str) -> Iterable[str]:
        response = f"Echo: {text}"
        chunk = 6
        for idx in range(0, len(response), chunk):
            yield response[idx : idx + chunk]


def build_demo_page() -> LLMUIDemoPage:
    return LLMUIDemoPage()


def main() -> None:
    app = AnywareApp(title="Anyware LLM UI Demo", clear_color="Black")
    font_main = FONTS_DIR / "长坂点宋16" / "长坂点宋16.ttf"
    app.set_fonts(ascii_path=str(font_main), cjk_path=str(font_main), cell_w=8, cell_h=16, size_px=16)
    app.set_root_page(build_demo_page())
    app.run()


if __name__ == "__main__":
    main()
