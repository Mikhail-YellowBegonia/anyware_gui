from __future__ import annotations

import os
import threading
from queue import SimpleQueue
from typing import Callable, Iterable, Protocol

import pygame

from .page import Page
from .text import Label
from .llm_ui import ChatDialogPanel, ChatInputLine, TextViewport

from .nonstandard_llm.client import DeepSeekClient
from .nonstandard_llm.config import load_config
from .nonstandard_llm.middleware.dispatcher import ToolDispatcher
from .nonstandard_llm.middleware.parser import parse_intent
from .nonstandard_llm.types import Message, ToolCallEvent


class StreamClient(Protocol):
    def stream_chat(self, messages: list[Message]) -> Iterable[str | ToolCallEvent]:
        ...


_STREAM_DONE = object()


class LLMStreamSession:
    def __init__(
        self,
        panel: ChatDialogPanel,
        client: StreamClient,
        *,
        on_text: Callable[[str], None] | None = None,
    ) -> None:
        self._panel = panel
        self._client = client
        self._queue: SimpleQueue[object] = SimpleQueue()
        self._done = False
        self._thread: threading.Thread | None = None
        self._on_text = on_text

    @property
    def done(self) -> bool:
        return self._done

    def start(self, messages: list[Message]) -> None:
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
                if self._on_text is not None:
                    self._on_text(item)
                self._panel.append_assistant_delta(item)


class LLMPage(Page):
    def __init__(
        self,
        *,
        page_id: str = "llm_chat",
        viewport_rect: tuple[int, int, int, int] = (2, 4, 116, 24),
        input_rect: tuple[int, int, int, int] = (2, 29, 116, 8),
        scope: str = "main",
        hint_text: str = "TAB:focus  CTRL+ENTER:send  UP/DOWN:scroll  CTRL+H:back  /tool:placeholder",
        status_color: str = "CRT_Green",
        hint_color: str = "CRT_Cyan",
        system_prompt: str | Callable[[], str] | None = None,
        dispatcher: ToolDispatcher | None = None,
        client_factory: Callable[[], StreamClient] | None = None,
        config_path: str | None = None,
        simulate_response: Callable[[str], Iterable[str]] | None = None,
        on_back: Callable[[], None] | None = None,
        back_key: int = pygame.K_h,
        back_mod: int = pygame.KMOD_CTRL,
        enable_tool_placeholder: bool = True,
    ) -> None:
        super().__init__(page_id)
        vx, vy, vw, vh = viewport_rect
        ix, iy, iw, ih = input_rect
        self.viewport = TextViewport(viewport_id="llm_viewport", gx=vx, gy=vy, gw=vw, gh=vh, scope=scope)
        self.input_line = ChatInputLine(
            input_id="llm_input",
            gx=ix,
            gy=iy,
            gw=iw,
            gh=ih,
            scope=scope,
            on_send=self._on_send,
        )
        self.panel = ChatDialogPanel(panel_id="llm_panel", viewport=self.viewport, input_line=self.input_line)
        self.status = Label(
            gx=vx,
            gy=vy - 3,
            gw=vw,
            gh=1,
            text=lambda _: self._status_text(),
            color=status_color,
        )
        self.hint = Label(
            gx=vx,
            gy=vy - 2,
            gw=vw,
            gh=1,
            text=hint_text,
            color=hint_color,
        )

        self.add(self.status)
        self.add(self.hint)
        self.add(self.panel)

        self._focus_ids = [self.input_line.input_id, self.viewport.component_id]
        self._focus_index = 0
        self._llm_client: StreamClient | None = None
        self._llm_session: LLMStreamSession | None = None
        self._assistant_buffer = ""
        self._assistant_start_index: int | None = None
        self._messages: list[Message] = []
        self._system_prompt = system_prompt or ""
        self._dispatcher = dispatcher
        self._status_override: str | None = None
        self._status_ttl = 0.0
        self._tool_followup = False
        self._client_factory = client_factory
        self._config_path = config_path
        self._simulate_response = simulate_response
        self._on_back = on_back
        self._back_key = back_key
        self._back_mod = back_mod
        self._enable_tool_placeholder = enable_tool_placeholder

    def _status_text(self) -> str:
        if self._status_override:
            return self._status_override
        if self.panel.status_message:
            return self.panel.status_message
        if not self.viewport.auto_follow:
            return "Paused"
        return ""

    def on_enter(self, ctx) -> None:
        ctx.set_active_focus_scope(self.viewport.scope)
        ctx.set_focus(self.input_line.input_id)

    def handle_event(self, event, ctx) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == self._back_key and event.mod & self._back_mod:
                if self._on_back is not None:
                    self._on_back()
                    return True
            if event.key == pygame.K_TAB:
                self._cycle_focus(ctx)
                return True
        return super().handle_event(event, ctx)

    def update(self, ctx, dt: float) -> None:
        if self._status_override:
            self._status_ttl = max(0.0, self._status_ttl - float(dt))
            if self._status_ttl <= 0:
                self._status_override = None
        if self._llm_session is not None:
            self._llm_session.poll()
            if self._llm_session.done:
                assistant_text = self._assistant_buffer
                self._llm_session = None
                if assistant_text:
                    self._finalize_assistant(assistant_text)
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

    def _ensure_client(self) -> StreamClient | None:
        if self._llm_client is not None:
            return self._llm_client
        if self._client_factory is not None:
            try:
                self._llm_client = self._client_factory()
            except Exception as exc:
                self.panel.append_error(f"LLM client init failed: {exc}")
                return None
            return self._llm_client
        config_path = self._config_path or os.environ.get("ANYWARE_LLM_CONFIG")
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
        self._assistant_buffer = ""
        self._assistant_start_index = len(self.viewport.lines)
        self._messages.append({"role": "user", "content": raw})
        if self._enable_tool_placeholder and raw.lower().startswith("/tool"):
            self.panel.start_stream(iter([{"tool": "placeholder"}]))
        else:
            client = self._ensure_client()
            if client is None:
                if self._simulate_response is not None:
                    self.panel.start_stream(self._simulate_response(raw))
                return
            session = LLMStreamSession(self.panel, client, on_text=self._capture_assistant_delta)
            session.start(self._build_messages())
            self._llm_session = session
        self.input_line.clear()

    def _capture_assistant_delta(self, delta: str) -> None:
        self._assistant_buffer += delta

    def _resolve_system_prompt(self) -> str:
        if callable(self._system_prompt):
            value = self._system_prompt()
            return str(value) if value else ""
        return str(self._system_prompt) if self._system_prompt else ""

    def _build_messages(self) -> list[Message]:
        system_prompt = self._resolve_system_prompt()
        if not system_prompt:
            return list(self._messages)
        return [{"role": "system", "content": system_prompt}] + list(self._messages)

    def _finalize_assistant(self, assistant_text: str) -> None:
        if self._tool_followup:
            self._tool_followup = False
            if parse_intent(assistant_text) is not None:
                self._remove_last_assistant_render()
                self._set_status_temp("tool call suppressed", ttl=3.0)
                self.panel.append_error("[tool] suppressed; expected natural reply")
                self._messages.append({"role": "assistant", "content": assistant_text})
                self._assistant_start_index = None
                return
            self._messages.append({"role": "assistant", "content": assistant_text})
            self._assistant_start_index = None
            return
        if self._dispatcher is None:
            self._messages.append({"role": "assistant", "content": assistant_text})
            self._assistant_start_index = None
            return
        _, result, call = self._dispatcher.handle_text(assistant_text)
        if call is None or result is None:
            self._messages.append({"role": "assistant", "content": assistant_text})
            self._assistant_start_index = None
            return
        self._remove_last_assistant_render()
        if result.ok:
            self._set_status_temp(f"tool:{call.name} ok", ttl=3.0)
            tool_msg = f"Tool {call.name} result: {result.output}"
            self._messages.append({"role": "system", "content": tool_msg})
            self._messages.append(
                {
                    "role": "user",
                    "content": f"{tool_msg}. Please respond in natural language and do not call tools.",
                }
            )
        else:
            self._set_status_temp(f"tool:{call.name} error", ttl=3.0)
            self.panel.append_error(f"[tool:{call.name}] {result.error or 'error'}")
            tool_msg = f"Tool {call.name} error: {result.error or 'error'}"
            self._messages.append({"role": "system", "content": tool_msg})
            self._messages.append(
                {
                    "role": "user",
                    "content": f"{tool_msg}. Please respond in natural language and do not call tools.",
                }
            )
        client = self._ensure_client()
        if client is None:
            return
        self.panel.stream_buffer.reset()
        self._assistant_buffer = ""
        self._assistant_start_index = len(self.viewport.lines)
        self._tool_followup = True
        session = LLMStreamSession(self.panel, client, on_text=self._capture_assistant_delta)
        session.start(self._build_messages())
        self._llm_session = session

    def _remove_last_assistant_render(self) -> None:
        if self._assistant_start_index is None:
            return
        self.viewport.set_lines(self.viewport.lines[: self._assistant_start_index])
        if self.viewport.auto_follow:
            self.viewport.jump_to_bottom()
        self._assistant_start_index = None

    def _set_status_temp(self, message: str, *, ttl: float) -> None:
        self._status_override = message
        self._status_ttl = max(0.0, float(ttl))
