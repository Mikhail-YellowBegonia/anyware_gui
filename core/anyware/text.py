from __future__ import annotations

from typing import Callable

from .component import Component


class Label(Component):
    """Simple text component for Anyware pages."""

    def __init__(
        self,
        *,
        label_id: str | None = None,
        gx: int = 0,
        gy: int = 0,
        text: str | Callable[[object], str] = "",
        color: str = "CRT_Cyan",
        orientation: str = "horizontal",
        line_step: int = 1,
        visible: bool = True,
        enabled: bool = True,
    ):
        super().__init__(component_id=label_id, visible=visible, enabled=enabled)
        self.gx = int(gx)
        self.gy = int(gy)
        self.text = text
        self.color = color
        self.orientation = orientation
        self.line_step = max(1, int(line_step))

    def set_text(self, text: str | Callable[[object], str]) -> None:
        self.text = text

    def _resolve_text(self, ctx) -> str:
        if callable(self.text):
            value = self.text(ctx)
            return "" if value is None else str(value)
        return str(self.text)

    def render(self, ctx) -> None:
        if not self.visible:
            return
        ctx.label(
            self.gx,
            self.gy,
            self.color,
            self._resolve_text(ctx),
            orientation=self.orientation,
            line_step=self.line_step,
        )


class Text(Label):
    """Alias for Label, kept for naming preference in app code."""
