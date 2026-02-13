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
        self.selected = False
        self._registered = False

    def _rect_px(self, ctx):
        return (ctx.gx(self.gx), ctx.gy(self.gy), self.width_px, self.height_px)

    def mount(self, ctx) -> None:
        super().mount(ctx)
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
        if not self.enabled or not self.visible:
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

    def render(self, ctx) -> None:
        if not self.visible:
            return
        x, y, w, h = self._rect_px(ctx)
        focused = ctx.get_focus(None) == self.button_id
        border_color = "blink18" if focused else self.color
        ctx.draw_rect(border_color, x, y, w, h, filled=False, thickness=1)
        if focused:
            ctx.draw_rect(self.color, x + 2, y + 2, w - 4, h - 4, filled=False, thickness=1)
        if self.selected:
            ctx.draw_pattern_rect(self.color, x + 2, y + 2, w - 4, h - 4, thickness=1)
        text_x = int(round(ctx.px(x))) + 1
        text_y = int(round(ctx.py(y))) + 1
        ctx.label(text_x, text_y, border_color, self.label[:12], orientation="horizontal")


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
