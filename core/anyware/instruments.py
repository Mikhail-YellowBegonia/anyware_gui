from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable

from .component import Component


def _resolve_value(value, ctx):
    if callable(value):
        return value(ctx)
    return value


def _normalize_value(value, min_value: float, max_value: float) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.0
    if max_value == min_value:
        return 0.0
    return max(0.0, min(1.0, (v - min_value) / (max_value - min_value)))


@dataclass
class ValueFormat:
    label: str | None = None
    label_suffix: str = ":"
    unit: str | None = None
    unit_sep: str = " "
    fmt: str | Callable[[object], str] | None = None


class ValueText(Component):
    """Simple value readout for dashboards."""

    def __init__(
        self,
        *,
        value_id: str | None = None,
        gx: int = 0,
        gy: int = 0,
        value: object | Callable[[object], object] = "",
        color: str = "CRT_Cyan",
        orientation: str = "horizontal",
        line_step: int = 1,
        visible: bool = True,
        enabled: bool = True,
        label: str | None = None,
        unit: str | None = None,
        fmt: str | Callable[[object], str] | None = None,
        label_suffix: str = ":",
        unit_sep: str = " ",
    ):
        super().__init__(component_id=value_id, visible=visible, enabled=enabled)
        self.gx = int(gx)
        self.gy = int(gy)
        self.value = value
        self.color = color
        self.orientation = orientation
        self.line_step = max(1, int(line_step))
        self.format = ValueFormat(
            label=label,
            label_suffix=label_suffix,
            unit=unit,
            unit_sep=unit_sep,
            fmt=fmt,
        )

    def _format_value(self, raw, ctx) -> str:
        if raw is None:
            return ""
        fmt = self.format.fmt
        if callable(fmt):
            return str(fmt(raw))
        if isinstance(fmt, str):
            try:
                return fmt.format(raw)
            except Exception:
                return str(raw)
        return str(raw)

    def _build_text(self, ctx) -> str:
        raw = _resolve_value(self.value, ctx)
        text = self._format_value(raw, ctx)
        if self.format.unit:
            text = f"{text}{self.format.unit_sep}{self.format.unit}"
        if self.format.label:
            return f"{self.format.label}{self.format.label_suffix} {text}"
        return text

    def render(self, ctx) -> None:
        if not self.visible:
            return
        ctx.label(
            self.gx,
            self.gy,
            self.color,
            self._build_text(ctx),
            orientation=self.orientation,
            line_step=self.line_step,
        )


class MeterBar(Component):
    """Linear meter with bar/segments modes."""

    def __init__(
        self,
        *,
        meter_id: str | None = None,
        gx: float = 0.0,
        gy: float = 0.0,
        width_px: float = 120.0,
        height_px: float = 12.0,
        value: object | Callable[[object], object] = 0.0,
        min_value: float = 0.0,
        max_value: float = 1.0,
        mode: str = "bar",
        segments: int = 10,
        gap_px: float = 2.0,
        orientation: str = "horizontal",
        color: str = "CRT_Cyan",
        empty_color: str | None = None,
        border_color: str | None = None,
        border_thickness: float = 1.0,
        padding_px: float = 2.0,
        visible: bool = True,
        enabled: bool = True,
    ):
        super().__init__(component_id=meter_id, visible=visible, enabled=enabled)
        self.gx = float(gx)
        self.gy = float(gy)
        self.width_px = float(width_px)
        self.height_px = float(height_px)
        self.value = value
        self.min_value = float(min_value)
        self.max_value = float(max_value)
        self.mode = str(mode).lower()
        self.segments = max(1, int(segments))
        self.gap_px = float(gap_px)
        self.orientation = str(orientation).lower()
        self.color = color
        self.empty_color = empty_color
        self.border_color = border_color or color
        self.border_thickness = float(border_thickness)
        self.padding_px = max(0.0, float(padding_px))

    def _rect_px(self, ctx):
        return (ctx.gx(self.gx), ctx.gy(self.gy), self.width_px, self.height_px)

    def _draw_bar(self, ctx, x, y, w, h, norm: float):
        if self.empty_color:
            ctx.draw_rect(self.empty_color, x, y, w, h, filled=True, thickness=1)
        inner_x = x + self.padding_px
        inner_y = y + self.padding_px
        inner_w = max(0.0, w - self.padding_px * 2)
        inner_h = max(0.0, h - self.padding_px * 2)
        if inner_w <= 0 or inner_h <= 0:
            return
        if self.orientation == "vertical":
            fill_h = inner_h * norm
            fill_y = inner_y + inner_h - fill_h
            ctx.draw_rect(self.color, inner_x, fill_y, inner_w, fill_h, filled=True, thickness=1)
            return
        fill_w = inner_w * norm
        ctx.draw_rect(self.color, inner_x, inner_y, fill_w, inner_h, filled=True, thickness=1)

    def _draw_segments(self, ctx, x, y, w, h, norm: float):
        count = self.segments
        filled = int(norm * count)
        if norm >= 1.0:
            filled = count
        inner_x = x + self.padding_px
        inner_y = y + self.padding_px
        inner_w = max(0.0, w - self.padding_px * 2)
        inner_h = max(0.0, h - self.padding_px * 2)
        if inner_w <= 0 or inner_h <= 0:
            return
        if self.orientation == "vertical":
            seg_h = (inner_h - self.gap_px * (count - 1)) / count
            for i in range(count):
                seg_y = inner_y + (count - 1 - i) * (seg_h + self.gap_px)
                color = self.color if i < filled else self.empty_color
                if color is None:
                    continue
                ctx.draw_rect(color, inner_x, seg_y, inner_w, seg_h, filled=True, thickness=1)
            return
        seg_w = (inner_w - self.gap_px * (count - 1)) / count
        for i in range(count):
            seg_x = inner_x + i * (seg_w + self.gap_px)
            color = self.color if i < filled else self.empty_color
            if color is None:
                continue
            ctx.draw_rect(color, seg_x, inner_y, seg_w, inner_h, filled=True, thickness=1)

    def render(self, ctx) -> None:
        if not self.visible:
            return
        x, y, w, h = self._rect_px(ctx)
        raw = _resolve_value(self.value, ctx)
        norm = _normalize_value(raw, self.min_value, self.max_value)
        if self.border_color:
            ctx.draw_rect(self.border_color, x, y, w, h, filled=False, thickness=self.border_thickness)
        if self.mode == "segments":
            self._draw_segments(ctx, x, y, w, h, norm)
            return
        self._draw_bar(ctx, x, y, w, h, norm)


class DialGauge(Component):
    """Dial gauge with needle and/or fill arc."""

    def __init__(
        self,
        *,
        gauge_id: str | None = None,
        center_gx: float = 0.0,
        center_gy: float = 0.0,
        radius_px: float = 40.0,
        value: object | Callable[[object], object] = 0.0,
        min_value: float = 0.0,
        max_value: float = 1.0,
        start_angle_deg: float = -135.0,
        end_angle_deg: float = 135.0,
        style: str = "needle",
        color: str = "CRT_Cyan",
        needle_width_px: float = 2.0,
        fill_steps: int = 24,
        center_dot_px: float = 3.0,
        visible: bool = True,
        enabled: bool = True,
    ):
        super().__init__(component_id=gauge_id, visible=visible, enabled=enabled)
        self.center_gx = float(center_gx)
        self.center_gy = float(center_gy)
        self.radius_px = float(radius_px)
        self.value = value
        self.min_value = float(min_value)
        self.max_value = float(max_value)
        self.start_angle_deg = float(start_angle_deg)
        self.end_angle_deg = float(end_angle_deg)
        self.style = str(style).lower()
        self.color = color
        self.needle_width_px = float(needle_width_px)
        self.fill_steps = max(6, int(fill_steps))
        self.center_dot_px = float(center_dot_px)

    def _center_px(self, ctx):
        return (ctx.gx(self.center_gx), ctx.gy(self.center_gy))

    def _angle_for_value(self, norm: float) -> float:
        return math.radians(self.start_angle_deg + (self.end_angle_deg - self.start_angle_deg) * norm)

    def _line_poly(self, x1, y1, x2, y2, thickness: float):
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        if length == 0:
            half = thickness / 2.0
            return [(x1 - half, y1 - half), (x1 + half, y1 - half), (x1 + half, y1 + half), (x1 - half, y1 + half)]
        nx = -dy / length
        ny = dx / length
        half = thickness / 2.0
        ox = nx * half
        oy = ny * half
        return [
            (x1 - ox, y1 - oy),
            (x1 + ox, y1 + oy),
            (x2 + ox, y2 + oy),
            (x2 - ox, y2 - oy),
        ]

    def _arc_vertices(self, start_rad: float, end_rad: float, steps: int):
        vertices = []
        if steps <= 1:
            steps = 2
        for i in range(steps + 1):
            t = i / steps
            ang = start_rad + (end_rad - start_rad) * t
            x = math.cos(ang) * self.radius_px
            y = math.sin(ang) * self.radius_px
            vertices.append((x, y))
        return vertices

    def render(self, ctx) -> None:
        if not self.visible:
            return
        cx, cy = self._center_px(ctx)
        raw = _resolve_value(self.value, ctx)
        norm = _normalize_value(raw, self.min_value, self.max_value)
        angle = self._angle_for_value(norm)
        if self.style in ("fill", "both"):
            start_rad = math.radians(self.start_angle_deg)
            arc_vertices = self._arc_vertices(start_rad, angle, self.fill_steps)
            poly = [(0.0, 0.0)] + arc_vertices
            ctx.draw_poly(poly, self.color, cx, cy, filled=True, thickness=1)
        if self.style in ("needle", "both"):
            x2 = math.cos(angle) * self.radius_px
            y2 = math.sin(angle) * self.radius_px
            poly = self._line_poly(0.0, 0.0, x2, y2, self.needle_width_px)
            ctx.draw_poly(poly, self.color, cx, cy, filled=True, thickness=1)
        if self.center_dot_px > 0:
            half = self.center_dot_px / 2.0
            ctx.draw_rect(self.color, cx - half, cy - half, self.center_dot_px, self.center_dot_px, filled=True, thickness=1)


class SegmentDisplay(Component):
    """Multi-segment digital tube display (7-seg only)."""

    _DEFAULT_SEGMENT_POLYS_NORM = {
        # Normalized polygons in 0..1 box (digit_w_px x digit_h_px).
        "A": [(0.18, 0.00), (0.82, 0.00), (0.74, 0.08), (0.26, 0.08)],
        "B": [(0.82, 0.00), (0.92, 0.10), (0.92, 0.48), (0.82, 0.40)],
        "C": [(0.82, 0.60), (0.92, 0.52), (0.92, 0.90), (0.82, 1.00)],
        "D": [(0.18, 1.00), (0.82, 1.00), (0.74, 0.92), (0.26, 0.92)],
        "E": [(0.08, 0.52), (0.18, 0.60), (0.18, 1.00), (0.08, 0.90)],
        "F": [(0.08, 0.10), (0.18, 0.00), (0.18, 0.40), (0.08, 0.48)],
        "G": [(0.22, 0.46), (0.78, 0.46), (0.70, 0.54), (0.30, 0.54)],
        "DP": [(1.02, 0.88), (1.14, 0.88), (1.14, 1.00), (1.02, 1.00)],
    }
    _UNSET = object()
    DEFAULTS = {
        "digit_w_px": 14.0,
        "digit_h_px": 24.0,
        "spacing_px": 3.0,
        "on_color": "CRT_Cyan",
        "off_color": None,
        "segment_style": "classic",
        "segment_thickness": 0.16,
        "segment_margin": 0.10,
        "segment_polys": {},
    }

    @classmethod
    def set_defaults(cls, **kwargs) -> None:
        for key, value in kwargs.items():
            if key not in cls.DEFAULTS:
                raise KeyError(f"Unknown SegmentDisplay default: {key}")
            cls.DEFAULTS[key] = value

    @classmethod
    def get_defaults(cls) -> dict:
        return dict(cls.DEFAULTS)

    def __init__(
        self,
        *,
        display_id: str | None = None,
        gx: float = 0.0,
        gy: float = 0.0,
        text: str | Callable[[object], str] = "",
        digits: int = 0,
        align: str = "right",
        pad_char: str = " ",
        digit_w_px: float | object = _UNSET,
        digit_h_px: float | object = _UNSET,
        spacing_px: float | object = _UNSET,
        on_color: str | object = _UNSET,
        off_color: str | None | object = _UNSET,
        segment_style: str | object = _UNSET,
        segment_thickness: float | object = _UNSET,
        segment_margin: float | object = _UNSET,
        segment_polys: dict | None | object = _UNSET,
        visible: bool = True,
        enabled: bool = True,
    ):
        super().__init__(component_id=display_id, visible=visible, enabled=enabled)
        defaults = self.DEFAULTS
        self.gx = float(gx)
        self.gy = float(gy)
        self.text = text
        self.digits = max(0, int(digits))
        self.align = str(align).lower()
        self.pad_char = str(pad_char) if pad_char else " "
        digit_w_px = defaults["digit_w_px"] if digit_w_px is self._UNSET else digit_w_px
        digit_h_px = defaults["digit_h_px"] if digit_h_px is self._UNSET else digit_h_px
        spacing_px = defaults["spacing_px"] if spacing_px is self._UNSET else spacing_px
        on_color = defaults["on_color"] if on_color is self._UNSET else on_color
        off_color = defaults["off_color"] if off_color is self._UNSET else off_color
        segment_style = defaults["segment_style"] if segment_style is self._UNSET else segment_style
        segment_thickness = defaults["segment_thickness"] if segment_thickness is self._UNSET else segment_thickness
        segment_margin = defaults["segment_margin"] if segment_margin is self._UNSET else segment_margin
        segment_polys = defaults["segment_polys"] if segment_polys is self._UNSET else segment_polys
        self.digit_w_px = float(digit_w_px)
        self.digit_h_px = float(digit_h_px)
        self.spacing_px = float(spacing_px)
        self.on_color = on_color
        self.off_color = off_color
        self.segment_style = str(segment_style).lower() if segment_style else "classic"
        self.segment_thickness = float(segment_thickness)
        self.segment_margin = float(segment_margin)
        self.segment_polys = dict(segment_polys or {})

    def _resolve_text(self, ctx) -> str:
        if callable(self.text):
            value = self.text(ctx)
            return "" if value is None else str(value)
        return str(self.text)

    def _segments_for_char(self, ch: str):
        table = {
            "0": {"A", "B", "C", "D", "E", "F"},
            "1": {"B", "C"},
            "2": {"A", "B", "G", "E", "D"},
            "3": {"A", "B", "G", "C", "D"},
            "4": {"F", "G", "B", "C"},
            "5": {"A", "F", "G", "C", "D"},
            "6": {"A", "F", "G", "E", "C", "D"},
            "7": {"A", "B", "C"},
            "8": {"A", "B", "C", "D", "E", "F", "G"},
            "9": {"A", "B", "C", "D", "F", "G"},
            "-": {"G"},
            " ": set(),
        }
        return table.get(ch.upper(), set())

    def _parse_text(self, text: str):
        digits = []
        for ch in text:
            if ch == ".":
                if digits:
                    digits[-1]["dp"] = True
                else:
                    digits.append({"char": " ", "dp": True})
                continue
            digits.append({"char": ch, "dp": False})
        return digits

    def _apply_digit_limit(self, digits):
        if self.digits <= 0:
            return digits
        total = self.digits
        if len(digits) >= total:
            return digits[-total:] if self.align == "right" else digits[:total]
        pad_count = total - len(digits)
        pad = [{"char": self.pad_char, "dp": False}] * pad_count
        return pad + digits if self.align == "right" else digits + pad

    def _rect_segment_polys_norm(self):
        t = max(0.04, min(0.40, self.segment_thickness))
        m = max(0.0, min(0.30, self.segment_margin))
        y_mid = 0.5
        split_gap = max(0.02, m * 0.5)

        def rect(x1, y1, x2, y2):
            return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]

        top_end = max(0.0, y_mid - split_gap)
        bot_start = min(1.0, y_mid + split_gap)
        return {
            "A": rect(m, 0.0, 1.0 - m, t),
            "D": rect(m, 1.0 - t, 1.0 - m, 1.0),
            "G": rect(m, y_mid - t / 2.0, 1.0 - m, y_mid + t / 2.0),
            "F": rect(0.0, m, t, top_end),
            "E": rect(0.0, bot_start, t, 1.0 - m),
            "B": rect(1.0 - t, m, 1.0, top_end),
            "C": rect(1.0 - t, bot_start, 1.0, 1.0 - m),
            "DP": list(self._DEFAULT_SEGMENT_POLYS_NORM["DP"]),
        }

    def _segment_style_polys_norm(self):
        style = self.segment_style or "classic"
        if style in ("classic", "default", "trapezoid"):
            return dict(self._DEFAULT_SEGMENT_POLYS_NORM)
        if style in ("rect", "rectangle"):
            return self._rect_segment_polys_norm()
        return dict(self._DEFAULT_SEGMENT_POLYS_NORM)

    def _resolve_segment_polys(self):
        source = self._segment_style_polys_norm()
        if self.segment_polys:
            source.update(self.segment_polys)
        polys = {}
        for name, poly in source.items():
            polys[name] = [(float(x) * self.digit_w_px, float(y) * self.digit_h_px) for x, y in poly]
        return polys

    def _draw_poly(self, ctx, x, y, poly, color):
        if not poly:
            return
        shifted = [(x + px, y + py) for px, py in poly]
        ctx.draw_poly(shifted, color, 0.0, 0.0, filled=True, thickness=1)

    def _draw_digit(self, ctx, x, y, ch: str, dp: bool, polys):
        segments_on = self._segments_for_char(ch)
        for name in ("A", "B", "C", "D", "E", "F", "G"):
            color = self.on_color if name in segments_on else self.off_color
            if color is None:
                continue
            self._draw_poly(ctx, x, y, polys.get(name, []), color)
        if dp:
            self._draw_poly(ctx, x, y, polys.get("DP", []), self.on_color)

    def render(self, ctx) -> None:
        if not self.visible:
            return
        text = self._resolve_text(ctx)
        digits = self._apply_digit_limit(self._parse_text(text))
        x0 = ctx.gx(self.gx)
        y0 = ctx.gy(self.gy)
        polys = self._resolve_segment_polys()
        for idx, info in enumerate(digits):
            x = x0 + idx * (self.digit_w_px + self.spacing_px)
            self._draw_digit(ctx, x, y0, info["char"], info["dp"], polys)
