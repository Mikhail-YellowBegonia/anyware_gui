from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Iterator

from core import GUI

from .component import Component, ComponentGroup

DEFAULT_COLOR = "CRT_Cyan"
BOLD_COLOR = "White"
CODE_COLOR = "neon_yellow"
QUOTE_COLOR = "CRT_Green"


@dataclass(frozen=True)
class TextSpan:
    text: str
    color: str = DEFAULT_COLOR
    style_tag: str | None = None


@dataclass(frozen=True)
class TextLine:
    spans: list[TextSpan]

    def plain_text(self) -> str:
        return "".join(span.text for span in self.spans)

    @staticmethod
    def from_text(text: str, *, color: str = DEFAULT_COLOR) -> "TextLine":
        return TextLine([TextSpan(text=text, color=color)])


class MarkdownSimplifier:
    @staticmethod
    def parse_line(line: str) -> list[TextSpan]:
        if line.startswith("> "):
            return [TextSpan(text=line[2:], color=QUOTE_COLOR, style_tag="quote")]
        stripped = line.lstrip()
        if stripped.startswith("#"):
            level = 0
            while level < len(stripped) and stripped[level] == "#":
                level += 1
            if level > 0 and (level == len(stripped) or stripped[level] == " "):
                text = stripped[level + 1 :] if level < len(stripped) else ""
                return [TextSpan(text=text, color=BOLD_COLOR, style_tag="heading")]

        spans: list[TextSpan] = []
        current_color = DEFAULT_COLOR
        current_tag: str | None = None
        buf: list[str] = []

        def flush() -> None:
            if not buf:
                return
            spans.append(TextSpan(text="".join(buf), color=current_color, style_tag=current_tag))
            buf.clear()

        i = 0
        while i < len(line):
            if line.startswith("**", i):
                flush()
                if current_color == BOLD_COLOR:
                    current_color = DEFAULT_COLOR
                    current_tag = None
                else:
                    current_color = BOLD_COLOR
                    current_tag = "bold"
                i += 2
                continue
            if line[i] == "`":
                flush()
                if current_color == CODE_COLOR:
                    current_color = DEFAULT_COLOR
                    current_tag = None
                else:
                    current_color = CODE_COLOR
                    current_tag = "code"
                i += 1
                continue
            buf.append(line[i])
            i += 1

        flush()
        if not spans:
            spans.append(TextSpan(text="", color=DEFAULT_COLOR))
        return spans


class ChatStreamBuffer:
    def __init__(self, *, markdown: MarkdownSimplifier | None = None, default_color: str = DEFAULT_COLOR):
        self._markdown = markdown or MarkdownSimplifier()
        self._default_color = default_color
        self._raw_lines: list[str] = []
        self.lines: list[TextLine] = []

    def reset(self) -> None:
        self._raw_lines = []
        self.lines = []

    def append_delta(self, delta: str) -> list[TextLine]:
        if not self._raw_lines:
            self._raw_lines = [""]
            self.lines = []

        parts = delta.split("\n")
        self._raw_lines[-1] += parts[0]
        for extra in parts[1:]:
            self._raw_lines.append(extra)

        start_index = max(0, len(self._raw_lines) - len(parts))
        for idx in range(start_index, len(self._raw_lines)):
            raw = self._raw_lines[idx]
            spans = self._markdown.parse_line(raw)
            if not spans:
                spans = [TextSpan(text="", color=self._default_color)]
            if idx < len(self.lines):
                self.lines[idx] = TextLine(spans)
            else:
                self.lines.append(TextLine(spans))
        return self.lines


class TextViewport(Component):
    def __init__(
        self,
        *,
        viewport_id: str | None = None,
        gx: int,
        gy: int,
        gw: int,
        gh: int,
        scope: str = "main",
        focusable: bool = True,
        color: str = DEFAULT_COLOR,
    ):
        resolved_id = str(viewport_id) if viewport_id else "viewport"
        super().__init__(component_id=resolved_id, visible=True, enabled=True)
        self.gx = int(gx)
        self.gy = int(gy)
        self.gw = max(1, int(gw))
        self.gh = max(1, int(gh))
        self.scope = str(scope)
        self.focusable = bool(focusable)
        self.color = color
        self.lines: list[TextLine] = []
        self.scroll_offset = 0
        self.auto_follow = True
        self._registered = False

    @staticmethod
    def _measure_cells(text: str) -> int:
        return GUI.measure_text_cells(text)[0]

    def wrap_lines(self, lines: Iterable[TextLine]) -> list[TextLine]:
        max_cells = max(1, int(self.gw))
        wrapped: list[TextLine] = []

        for line in lines:
            spans = line.spans or []
            if not spans:
                wrapped.append(TextLine.from_text("", color=self.color))
                continue
            current_spans: list[TextSpan] = []
            current_width = 0

            def flush() -> None:
                nonlocal current_spans, current_width
                if current_spans:
                    wrapped.append(TextLine(list(current_spans)))
                else:
                    wrapped.append(TextLine.from_text("", color=self.color))
                current_spans = []
                current_width = 0

            for span in spans:
                text = span.text or ""
                if not text:
                    continue
                while text:
                    remaining = max_cells - current_width
                    if remaining <= 0:
                        flush()
                        remaining = max_cells
                    chunk = GUI._truncate_line_to_cells(text, remaining)
                    if not chunk:
                        flush()
                        continue
                    current_spans.append(TextSpan(text=chunk, color=span.color, style_tag=span.style_tag))
                    current_width += self._measure_cells(chunk)
                    text = text[len(chunk) :]
            if current_spans or not wrapped:
                wrapped.append(TextLine(list(current_spans)) if current_spans else TextLine.from_text("", color=self.color))
        return wrapped

    def _rect_px(self, ctx):
        x1 = ctx.gx(self.gx)
        y1 = ctx.gy(self.gy)
        x2 = ctx.gx(self.gx + self.gw)
        y2 = ctx.gy(self.gy + self.gh)
        return (x1, y1, x2 - x1, y2 - y1)

    def _max_scroll_offset(self) -> int:
        return max(0, len(self.lines) - self.gh)

    def is_at_bottom(self) -> bool:
        return self.scroll_offset >= self._max_scroll_offset()

    def set_lines(self, lines: list[TextLine]) -> None:
        self.lines = self.wrap_lines(lines)
        max_offset = self._max_scroll_offset()
        if self.auto_follow:
            self.scroll_offset = max_offset
        else:
            self.scroll_offset = min(self.scroll_offset, max_offset)

    def append_lines(self, lines: Iterable[TextLine]) -> None:
        self.lines.extend(self.wrap_lines(lines))
        if self.auto_follow:
            self.scroll_offset = self._max_scroll_offset()

    def set_lines_wrapped(self, lines: list[TextLine]) -> None:
        self.lines = list(lines)
        max_offset = self._max_scroll_offset()
        if self.auto_follow:
            self.scroll_offset = max_offset
        else:
            self.scroll_offset = min(self.scroll_offset, max_offset)

    def scroll(self, delta_lines: int) -> None:
        max_offset = self._max_scroll_offset()
        self.scroll_offset = max(0, min(self.scroll_offset + int(delta_lines), max_offset))
        self.auto_follow = self.is_at_bottom()

    def jump_to_bottom(self) -> None:
        self.scroll_offset = self._max_scroll_offset()
        self.auto_follow = True

    def visible_lines(self) -> list[TextLine]:
        start = max(0, self.scroll_offset)
        end = min(len(self.lines), start + self.gh)
        return self.lines[start:end]

    def mount(self, ctx) -> None:
        super().mount(ctx)
        if not self.focusable:
            return
        ctx.add_focus_node(
            self.component_id or "viewport",
            self._rect_px(ctx),
            enabled=self.enabled,
            visible=self.visible,
            nav=None,
            scope=self.scope,
        )
        self._registered = True

    def unmount(self, ctx) -> None:
        if self._registered and self.component_id is not None:
            ctx.remove_focus_node(self.component_id)
            self._registered = False
        super().unmount(ctx)

    def update(self, ctx, dt: float) -> None:
        if not self._registered or self.component_id is None:
            return
        ctx.update_focus_node(
            self.component_id,
            rect=self._rect_px(ctx),
            enabled=self.enabled,
            visible=self.visible,
            nav=None,
            scope=self.scope,
        )

    def handle_event(self, event, ctx) -> bool:
        if not self.focusable or not self.enabled or not self.visible:
            return False
        if self.component_id is None or ctx.get_focus(None) != self.component_id:
            return False
        import pygame

        if event.type != pygame.KEYDOWN:
            return False
        if event.key == pygame.K_UP:
            self.scroll(-1)
            return True
        if event.key == pygame.K_DOWN:
            self.scroll(1)
            return True
        if event.key == pygame.K_PAGEUP:
            self.scroll(-max(1, self.gh - 1))
            return True
        if event.key == pygame.K_PAGEDOWN:
            self.scroll(max(1, self.gh - 1))
            return True
        if event.key == pygame.K_HOME:
            self.scroll_offset = 0
            self.auto_follow = False
            return True
        if event.key == pygame.K_END:
            self.jump_to_bottom()
            return True
        return False

    def render(self, ctx) -> None:
        if not self.visible:
            return
        for row, line in enumerate(self.visible_lines()):
            y_cell = self.gy + row
            x_cell = self.gx
            offset_cells = 0
            for span in line.spans:
                if not span.text:
                    continue
                remaining = self.gw - offset_cells
                if remaining <= 0:
                    break
                text = span.text
                width_cells, _ = ctx.measure_text_cells(text)
                if width_cells > remaining:
                    text = GUI._truncate_line_to_cells(text, remaining)
                    width_cells, _ = ctx.measure_text_cells(text)
                x_px = ctx.gx(x_cell + offset_cells)
                y_px = ctx.gy(y_cell)
                ctx.draw_super_text_px(x_px, y_px, span.color, text)
                offset_cells += width_cells


class ChatInputLine(Component):
    def __init__(
        self,
        *,
        input_id: str,
        gx: int,
        gy: int,
        gw: int,
        gh: int,
        scope: str = "main",
        color: str = DEFAULT_COLOR,
        focusable: bool = True,
        on_send: Callable[[str], None] | None = None,
    ):
        super().__init__(component_id=input_id, visible=True, enabled=True)
        self.input_id = str(input_id)
        self.gx = int(gx)
        self.gy = int(gy)
        self.gw = max(1, int(gw))
        self.gh = max(1, int(gh))
        self.scope = str(scope)
        self.color = color
        self.focusable = bool(focusable)
        self.on_send = on_send
        self.text = ""
        self.cursor = 0
        self._registered = False
        self._text_input_active = False

    def _rect_px(self, ctx):
        x1 = ctx.gx(self.gx)
        y1 = ctx.gy(self.gy)
        x2 = ctx.gx(self.gx + self.gw)
        y2 = ctx.gy(self.gy + self.gh)
        return (x1, y1, x2 - x1, y2 - y1)

    def _clamp_cursor(self) -> None:
        self.cursor = max(0, min(self.cursor, len(self.text)))

    def insert_text(self, text: str) -> None:
        if not text:
            return
        self.text = self.text[: self.cursor] + text + self.text[self.cursor :]
        self.cursor += len(text)
        self._clamp_cursor()

    def backspace(self) -> None:
        if self.cursor <= 0:
            return
        self.text = self.text[: self.cursor - 1] + self.text[self.cursor :]
        self.cursor -= 1
        self._clamp_cursor()

    def delete(self) -> None:
        if self.cursor >= len(self.text):
            return
        self.text = self.text[: self.cursor] + self.text[self.cursor + 1 :]
        self._clamp_cursor()

    def move_left(self) -> None:
        self.cursor = max(0, self.cursor - 1)

    def move_right(self) -> None:
        self.cursor = min(len(self.text), self.cursor + 1)

    def move_home(self) -> None:
        self.cursor = 0

    def move_end(self) -> None:
        self.cursor = len(self.text)

    def clear(self) -> None:
        self.text = ""
        self.cursor = 0

    def mount(self, ctx) -> None:
        super().mount(ctx)
        if not self.focusable:
            return
        ctx.add_focus_node(
            self.input_id,
            self._rect_px(ctx),
            enabled=self.enabled,
            visible=self.visible,
            nav=None,
            scope=self.scope,
        )
        self._registered = True

    def unmount(self, ctx) -> None:
        if self._registered:
            ctx.remove_focus_node(self.input_id)
            self._registered = False
        if self._text_input_active:
            import pygame

            pygame.key.stop_text_input()
            self._text_input_active = False
        super().unmount(ctx)

    def update(self, ctx, dt: float) -> None:
        if not self._registered:
            return
        ctx.update_focus_node(
            self.input_id,
            rect=self._rect_px(ctx),
            enabled=self.enabled,
            visible=self.visible,
            nav=None,
            scope=self.scope,
        )
        focused = self._has_focus(ctx) and self.enabled and self.visible
        if focused and not self._text_input_active:
            import pygame

            pygame.key.start_text_input()
            self._text_input_active = True
        elif not focused and self._text_input_active:
            import pygame

            pygame.key.stop_text_input()
            self._text_input_active = False

    def _has_focus(self, ctx) -> bool:
        return self.focusable and ctx.get_focus(None) == self.input_id

    def handle_event(self, event, ctx) -> bool:
        if not self._has_focus(ctx) or not self.enabled or not self.visible:
            return False
        import pygame

        if event.type == pygame.TEXTINPUT:
            self.insert_text(event.text)
            return True
        if event.type == pygame.TEXTEDITING:
            return True
        if event.type != pygame.KEYDOWN:
            return False

        if event.key == pygame.K_BACKSPACE:
            self.backspace()
            return True
        if event.key == pygame.K_DELETE:
            self.delete()
            return True
        if event.key == pygame.K_LEFT:
            self.move_left()
            return True
        if event.key == pygame.K_RIGHT:
            self.move_right()
            return True
        if event.key == pygame.K_HOME:
            self.move_home()
            return True
        if event.key == pygame.K_END:
            self.move_end()
            return True

        if event.key == pygame.K_RETURN:
            if event.mod & pygame.KMOD_CTRL:
                if self.on_send is not None:
                    self.on_send(self.text)
                return True
            self.insert_text("\n")
            return True

        if not self._text_input_active and event.unicode:
            self.insert_text(event.unicode)
            return True
        return False

    def render(self, ctx) -> None:
        if not self.visible:
            return
        x, y, w, h = self._rect_px(ctx)
        focused = self._has_focus(ctx)
        border_color = "blink18" if focused else self.color
        ctx.draw_rect(border_color, x, y, w, h, filled=False, thickness=1)
        ctx.draw_text_box(
            self.gx,
            self.gy,
            self.gw,
            self.gh,
            self.color,
            self.text,
            align_h="left",
            align_v="top",
        )
        self._render_cursor(ctx)

    def _render_cursor(self, ctx) -> None:
        if not self._has_focus(ctx):
            return
        before = self.text[: self.cursor]
        parts = before.split("\n")
        row = max(0, len(parts) - 1)
        col_text = parts[-1] if parts else ""
        col_cells, _ = ctx.measure_text_cells(col_text)
        gx = self.gx + col_cells
        gy = self.gy + row
        if gy >= self.gy + self.gh:
            return
        cell_w = ctx.gx(1) - ctx.gx(0)
        cell_h = ctx.gy(1) - ctx.gy(0)
        x_px = ctx.gx(gx)
        y_px = ctx.gy(gy)
        ctx.draw_rect(self.color, x_px, y_px, cell_w, cell_h, filled=True, thickness=1)


class ChatDialogPanel(ComponentGroup):
    def __init__(
        self,
        *,
        panel_id: str,
        viewport: TextViewport,
        input_line: ChatInputLine,
    ):
        super().__init__(component_id=panel_id, visible=True, enabled=True)
        self.viewport = viewport
        self.input_line = input_line
        self.stream_buffer = ChatStreamBuffer()
        self._stream_base_lines: list[TextLine] = []
        self._stream_iter: Iterator[object] | None = None
        self._on_tool_event: Callable[[object], None] | None = None
        self._status_hint: str | None = None
        self.status_message = ""
        self.add(viewport)
        self.add(input_line)

    def start_stream(self, events: Iterable[object], *, on_tool_event: Callable[[object], None] | None = None) -> None:
        self._stream_iter = iter(events)
        self._on_tool_event = on_tool_event
        self._status_hint = None
        self._stream_base_lines = list(self.viewport.lines)

    def poll_stream(self, *, max_steps: int = 8) -> bool:
        if self._stream_iter is None:
            return False
        steps = 0
        while steps < max_steps:
            try:
                event = next(self._stream_iter)
            except StopIteration:
                self._stream_iter = None
                return False
            steps += 1
            if isinstance(event, str):
                self.append_assistant_delta(event)
                continue
            if self._on_tool_event is not None:
                self._on_tool_event(event)
            self._status_hint = "tool-call placeholder"
            self.status_message = self._status_hint
            self._stream_iter = None
            return False
        return True

    @staticmethod
    def _lines_from_text(text: str, *, color: str = DEFAULT_COLOR) -> list[TextLine]:
        parts = str(text).split("\n")
        if not parts:
            parts = [""]
        return [TextLine.from_text(part, color=color) for part in parts]

    def append_user(self, text: str) -> None:
        self.viewport.append_lines(self._lines_from_text(text, color=DEFAULT_COLOR))

    def append_assistant_delta(self, delta: str) -> None:
        if not self.stream_buffer.lines:
            self._stream_base_lines = list(self.viewport.lines)
        self.stream_buffer.append_delta(delta)
        wrapped = self.viewport.wrap_lines(self.stream_buffer.lines)
        self.viewport.set_lines_wrapped(self._stream_base_lines + wrapped)
        if self.viewport.auto_follow:
            self.viewport.jump_to_bottom()

    def append_system_message(self, text: str, *, color: str = DEFAULT_COLOR) -> None:
        self.viewport.append_lines(self._lines_from_text(text, color=color))
        if self.viewport.auto_follow:
            self.viewport.jump_to_bottom()

    def append_error(self, text: str) -> None:
        self._status_hint = text
        self.append_system_message(text, color="CRT_Red")

    def update(self, ctx, dt: float) -> None:
        if self._status_hint is not None:
            self.status_message = self._status_hint
        elif not self.viewport.auto_follow:
            self.status_message = "Paused"
        else:
            self.status_message = ""
        super().update(ctx, dt)
