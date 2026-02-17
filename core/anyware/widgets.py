from __future__ import annotations

from typing import Callable

import pygame

from .component import Component, ComponentGroup


class Button(Component):
    """Focusable/selectable button with Anyware-first API surface."""

    def __init__(
        self,
        button_id: str,
        label: str,
        *,
        gx: float,
        gy: float,
        width_px: float = 96,
        height_px: float = 20,
        scope: str = "main",
        color: str = "CRT_Cyan",
        nav: dict | None = None,
        on_select: Callable[["Button", object], None] | None = None,
        pressable: bool = True,
        focusable: bool = True,
        lighted: bool | Callable[["Button", object], bool] = False,
        light_color: str | None = None,
        status: object | Callable[["Button", object], object] | None = None,
        status_color_map: dict | None = None,
        status_default_color: str = "CRT_Cyan",
        label_align_h: str = "left",
        label_align_v: str = "top",
        label_line_step: int = 1,
        label_orientation: str = "horizontal",
        label_padding_gx: int = 1,
        label_padding_gy: int = 1,
    ):
        super().__init__(component_id=button_id, visible=True, enabled=True)
        self.button_id = button_id
        self.label = label
        self.gx = float(gx)
        self.gy = float(gy)
        self.width_px = float(width_px)
        self.height_px = float(height_px)
        self.scope = str(scope)
        self.color = color
        self.nav = dict(nav or {})
        self.on_select = on_select
        self.pressable = bool(pressable)
        self.focusable = bool(focusable)
        self.lighted = lighted
        self.light_color = light_color
        self.status = status
        self.status_color_map = dict(status_color_map or {})
        self.status_default_color = status_default_color
        self.label_align_h = str(label_align_h)
        self.label_align_v = str(label_align_v)
        self.label_line_step = max(1, int(label_line_step))
        self.label_orientation = str(label_orientation)
        self.label_padding_gx = int(label_padding_gx)
        self.label_padding_gy = int(label_padding_gy)
        self.selected = False
        self._registered = False

    def _rect_px(self, ctx):
        return (ctx.gx(self.gx), ctx.gy(self.gy), self.width_px, self.height_px)

    def _resolve_bool(self, value, ctx) -> bool:
        if callable(value):
            return bool(value(self, ctx))
        return bool(value)

    def _resolve_status_color(self, ctx):
        if self.status is None:
            return None
        value = self.status(self, ctx) if callable(self.status) else self.status
        return self.status_color_map.get(value, self.status_default_color)

    def mount(self, ctx) -> None:
        super().mount(ctx)
        if not self.focusable:
            return
        ctx.add_focus_node(
            self.button_id,
            self._rect_px(ctx),
            enabled=self.enabled,
            visible=self.visible,
            nav=self.nav,
            scope=self.scope,
        )
        self._registered = True

    def unmount(self, ctx) -> None:
        if self._registered:
            ctx.remove_focus_node(self.button_id)
            self._registered = False
        super().unmount(ctx)

    def update(self, ctx, dt: float) -> None:
        if not self._registered:
            return
        ctx.update_focus_node(
            self.button_id,
            rect=self._rect_px(ctx),
            enabled=self.enabled,
            visible=self.visible,
            nav=self.nav,
            scope=self.scope,
        )

    def handle_event(self, event, ctx) -> bool:
        if not self.enabled or not self.visible or not self.pressable:
            return False
        if event.type != pygame.KEYDOWN:
            return False
        if event.key not in (pygame.K_RETURN, pygame.K_SPACE):
            return False
        if ctx.get_focus(None) != self.button_id:
            return False
        self.selected = not self.selected
        if self.on_select is not None:
            self.on_select(self, ctx)
        return True

    def focus_ids(self) -> list[str]:
        if not self.focusable:
            return []
        return [str(self.button_id)]

    def render(self, ctx) -> None:
        if not self.visible:
            return
        x, y, w, h = self._rect_px(ctx)
        focused = self.focusable and ctx.get_focus(None) == self.button_id
        border_color = "blink18" if focused else self.color
        ctx.draw_rect(border_color, x, y, w, h, filled=False, thickness=1)
        status_color = self._resolve_status_color(ctx)
        if status_color is None and self._resolve_bool(self.lighted, ctx):
            status_color = self.light_color or self.color
        if status_color is not None:
            ctx.draw_rect(status_color, x + 2, y + 2, w - 4, h - 4, filled=True, thickness=1)
        if focused:
            ctx.draw_rect(self.color, x + 2, y + 2, w - 4, h - 4, filled=False, thickness=1)
        if self.selected:
            ctx.draw_pattern_rect(self.color, x + 2, y + 2, w - 4, h - 4, thickness=1)
        gx = int(round(ctx.px(x)))
        gy = int(round(ctx.py(y)))
        gw = max(1, int(round(ctx.px(x + w) - ctx.px(x))))
        gh = max(1, int(round(ctx.py(y + h) - ctx.py(y))))
        inner_gx = gx + self.label_padding_gx
        inner_gy = gy + self.label_padding_gy
        inner_gw = gw - (self.label_padding_gx * 2)
        inner_gh = gh - (self.label_padding_gy * 2)
        if inner_gw > 0 and inner_gh > 0:
            ctx.draw_text_box(
                inner_gx,
                inner_gy,
                inner_gw,
                inner_gh,
                border_color,
                self.label,
                align_h=self.label_align_h,
                align_v=self.label_align_v,
                orientation=self.label_orientation,
                line_step=self.label_line_step,
            )
        else:
            ctx.label(
                gx,
                gy,
                border_color,
                self.label,
                orientation=self.label_orientation,
                line_step=self.label_line_step,
            )


class CheckboxMenu(Button):
    """Single item, multi-state toggle (label + state)."""

    def __init__(
        self,
        menu_id: str,
        label: str,
        *,
        states: list[str],
        index: int = 0,
        label_sep: str = ": ",
        gx: float,
        gy: float,
        width_px: float = 96,
        height_px: float = 20,
        scope: str = "main",
        color: str = "CRT_Cyan",
        nav: dict | None = None,
        on_change: Callable[["CheckboxMenu", object], None] | None = None,
        pressable: bool = True,
        focusable: bool = True,
        label_align_h: str = "left",
        label_align_v: str = "top",
        label_line_step: int = 1,
        label_orientation: str = "horizontal",
        label_padding_gx: int = 1,
        label_padding_gy: int = 1,
    ):
        self.base_label = str(label)
        self.states = [str(state) for state in states]
        self.label_sep = str(label_sep)
        self.index = max(0, int(index))
        self.on_change = on_change
        super().__init__(
            menu_id,
            "",
            gx=gx,
            gy=gy,
            width_px=width_px,
            height_px=height_px,
            scope=scope,
            color=color,
            nav=nav,
            on_select=None,
            pressable=pressable,
            focusable=focusable,
            label_align_h=label_align_h,
            label_align_v=label_align_v,
            label_line_step=label_line_step,
            label_orientation=label_orientation,
            label_padding_gx=label_padding_gx,
            label_padding_gy=label_padding_gy,
        )
        self._sync_label()

    def _sync_label(self) -> None:
        state = self.get_value()
        if state:
            self.label = f"{self.base_label}{self.label_sep}{state}"
        else:
            self.label = self.base_label

    def get_value(self) -> str:
        if not self.states:
            return ""
        idx = self.index % len(self.states)
        return self.states[idx]

    def set_index(self, index: int) -> None:
        self.index = max(0, int(index))
        self._sync_label()

    def handle_event(self, event, ctx) -> bool:
        if not self.enabled or not self.visible or not self.pressable:
            return False
        if event.type != pygame.KEYDOWN:
            return False
        if event.key not in (pygame.K_RETURN, pygame.K_SPACE):
            return False
        if ctx.get_focus(None) != self.button_id:
            return False
        if not self.states:
            return False
        self.index = (self.index + 1) % len(self.states)
        self._sync_label()
        if self.on_change is not None:
            self.on_change(self, ctx)
        return True


class ButtonArray(ComponentGroup):
    """Grid button collection with deterministic local nav links."""

    def __init__(
        self,
        array_id: str,
        *,
        labels: list[str],
        gx: float,
        gy: float,
        cols: int,
        rows: int,
        scope: str = "main",
        gx_spacing: float = 15.0,
        gy_spacing: float = 2.0,
        width_px: float = 96,
        height_px: float = 20,
        color: str = "CRT_Cyan",
        id_start: int = 1,
        on_select: Callable[[Button, object], None] | None = None,
    ):
        super().__init__(component_id=array_id, visible=True, enabled=True)
        self.scope = str(scope)
        self._labels = list(labels)
        self._buttons: list[Button] = []
        total = min(len(self._labels), max(1, cols) * max(1, rows))

        for idx in range(total):
            r = idx // max(1, cols)
            c = idx % max(1, cols)
            node_num = id_start + idx
            button_id = f"{self.scope}_btn_{node_num}"
            nav = {}
            if c > 0:
                nav["left"] = f"{self.scope}_btn_{node_num - 1}"
            if c < cols - 1 and idx + 1 < total:
                nav["right"] = f"{self.scope}_btn_{node_num + 1}"
            if r > 0:
                nav["up"] = f"{self.scope}_btn_{node_num - cols}"
            if r < rows - 1 and idx + cols < total:
                nav["down"] = f"{self.scope}_btn_{node_num + cols}"

            btn = Button(
                button_id,
                self._labels[idx],
                gx=gx + c * gx_spacing,
                gy=gy + r * gy_spacing,
                width_px=width_px,
                height_px=height_px,
                scope=self.scope,
                color=color,
                nav=nav,
                on_select=on_select,
            )
            self._buttons.append(btn)
            self.add(btn)

    @property
    def buttons(self) -> list[Button]:
        return list(self._buttons)

    def button_by_id(self, button_id: str) -> Button | None:
        for btn in self._buttons:
            if btn.button_id == button_id:
                return btn
        return None
