from __future__ import annotations

import colorsys
import hashlib
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from core import GUI
from .widgets import Button
from .page import Page
from .id import stable_component_id

try:
    import yaml
except Exception:  # pragma: no cover - optional dependency
    yaml = None


def _require_yaml() -> None:
    if yaml is None:
        raise RuntimeError("PyYAML is required for YAML layouts. Install with: pip install pyyaml")


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    raw = value.strip().lstrip("#")
    if len(raw) != 6:
        raise ValueError(f"Invalid hex color: {value}")
    return (int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16))


def _register_palette_color(name: str, hex_value: str, *, index: int) -> None:
    r, g, b = _hex_to_rgb(hex_value)
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    GUI.hsv_palette[index] = (h, s, v, name)


def _install_palette(globals_block: dict[str, Any]) -> None:
    palette = globals_block.get("palette")
    if not isinstance(palette, dict):
        return

    colors = palette.get("colors")
    index_start = int(palette.get("index_start", 240))
    if isinstance(colors, dict) and colors:
        for offset, (name, hex_value) in enumerate(colors.items()):
            _register_palette_color(str(name), str(hex_value), index=index_start + offset)
    else:
        bg_hex = palette.get("bg_hex")
        default_hex = palette.get("default_hex")
        special_hex = palette.get("special_hex")
        if default_hex:
            _register_palette_color("Solar_Default", str(default_hex), index=index_start)
        if special_hex:
            _register_palette_color("Solar_Special", str(special_hex), index=index_start + 1)
        if bg_hex:
            GUI.set_display_defaults(window_bg_color_rgb=_hex_to_rgb(str(bg_hex)))

    GUI.refresh_palette_cache()


def _stable_hash(value: str) -> int:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _normalize_rect(node: dict[str, Any]) -> tuple[float, float, float, float]:
    rect = node.get("rect")
    if rect is not None:
        if not isinstance(rect, (list, tuple)) or len(rect) != 4:
            raise ValueError(f"rect must be [gx, gy, gw, gh], got: {rect}")
        return (float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]))
    return (
        float(node.get("gx", 0)),
        float(node.get("gy", 0)),
        float(node.get("gw", 0)),
        float(node.get("gh", 0)),
    )


def _merge_style(target: dict[str, Any], source: dict[str, Any] | None) -> None:
    if not isinstance(source, dict):
        return
    for key, value in source.items():
        target[key] = value


_WARNED_STYLE_KEYS: set[str] = set()
_TEXT_TYPES = {"text", "super_text"}
_SHAPE_TYPES = {"rect", "box", "poly", "arrow"}


def _warn_style_once(key: str, message: str) -> None:
    if key in _WARNED_STYLE_KEYS:
        return
    _WARNED_STYLE_KEYS.add(key)
    warnings.warn(message)


def _normalize_color_style(
    style: dict[str, Any],
    element_type: str | None,
    element_id: str | None,
) -> dict[str, Any]:
    if element_type is None:
        return style

    normalized = dict(style)
    label = element_id or element_type

    if element_type in _TEXT_TYPES:
        if "text_color" not in normalized and "color" in normalized:
            normalized["text_color"] = normalized.get("color")
        if "color" in normalized and "text_color" in normalized:
            if normalized.get("color") != normalized.get("text_color"):
                _warn_style_once(
                    f"text-color-conflict:{label}",
                    f"[layout_dsl] {label} defines both color and text_color with different values; "
                    "text_color will be used for text rendering.",
                )
        return normalized

    if element_type in _SHAPE_TYPES:
        fill_value = normalized.get("fill")
        filled_flag = bool(normalized.get("filled") or fill_value is not None)

        if isinstance(fill_value, str):
            normalized.setdefault("fill_color", fill_value)
            normalized.setdefault("filled", True)
            filled_flag = True
        elif fill_value is not None and not isinstance(fill_value, bool):
            normalized.setdefault("filled", True)
            filled_flag = True

        if "line_color" not in normalized and "color" in normalized:
            normalized["line_color"] = normalized.get("color")

        if filled_flag and "fill_color" not in normalized and "color" in normalized:
            if normalized.get("line_color") != normalized.get("color"):
                normalized["fill_color"] = normalized.get("color")

        if (
            "color" in normalized
            and "line_color" in normalized
            and normalized.get("color") != normalized.get("line_color")
            and not filled_flag
            and "fill_color" not in normalized
        ):
            _warn_style_once(
                f"shape-color-conflict:{label}",
                f"[layout_dsl] {label} defines color and line_color with different values, "
                "but fill is not enabled; color will be ignored.",
            )
        return normalized

    return normalized


def _resolve_style(
    styles: dict[str, Any],
    group_style: dict[str, Any] | None,
    element_style: dict[str, Any] | None,
    element: dict[str, Any],
    *,
    element_type: str | None = None,
    element_id: str | None = None,
) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    _merge_style(resolved, styles.get("default"))
    if isinstance(group_style, str):
        _merge_style(resolved, styles.get(group_style))
    else:
        _merge_style(resolved, group_style)
    if isinstance(element_style, str):
        _merge_style(resolved, styles.get(element_style))
    else:
        _merge_style(resolved, element_style)
    for key, value in element.items():
        if key in {
            "color",
            "text_color",
            "line_color",
            "fill",
            "filled",
            "fill_color",
            "thickness",
            "align_h",
            "align_v",
            "line_step",
            "orientation",
            "label_align_h",
            "label_align_v",
            "label_orientation",
            "label_line_step",
            "pattern",
            "pattern_color",
            "pattern_spacing",
            "pattern_angle_deg",
            "pattern_thickness",
            "pattern_offset",
            "pattern_outline",
        }:
            resolved[key] = value
    resolved = _normalize_color_style(resolved, element_type, element_id)
    return resolved


def _resolve_binding(bindings: Any, key: str, ctx) -> Any:
    if bindings is None or key is None:
        return None
    if callable(bindings):
        return bindings(key, ctx)
    if isinstance(bindings, dict):
        if key in bindings:
            value = bindings[key]
            return value(ctx) if callable(value) else value
        if "." in key:
            current: Any = bindings
            for part in key.split("."):
                if isinstance(current, dict) and part in current:
                    current = current[part]
                    continue
                return None
            return current(ctx) if callable(current) else current
    return None


def _text_from_element(element: dict[str, Any], bindings: Any, ctx) -> str:
    bind_key = element.get("bind")
    if bind_key:
        value = _resolve_binding(bindings, str(bind_key), ctx)
        if value is not None:
            return str(value)
    value = element.get("text")
    if value is None:
        return ""
    return str(value)


@dataclass
class LayoutDocument:
    path: Path
    data: dict[str, Any]
    globals: dict[str, Any]
    styles: dict[str, Any]
    pages: dict[str, Any]
    templates: dict[str, Any]


@dataclass
class LayoutRenderPlan:
    page_id: str
    components: list[Any]
    drawables: list[dict[str, Any]]
    slots: dict[str, dict[str, Any]]
    state_sources: dict[str, Any]


_STATE_STYLE_KEYS = {
    "color",
    "text_color",
    "line_color",
    "fill",
    "filled",
    "fill_color",
    "thickness",
    "align_h",
    "align_v",
    "line_step",
    "orientation",
    "label_align_h",
    "label_align_v",
    "label_orientation",
    "label_line_step",
    "pattern",
    "pattern_color",
    "pattern_spacing",
    "pattern_angle_deg",
    "pattern_thickness",
    "pattern_offset",
    "pattern_outline",
}


def _apply_state_style(base: dict[str, Any], overlay: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(overlay, dict) or not overlay:
        return base
    merged = dict(base)
    for key, value in overlay.items():
        if key in _STATE_STYLE_KEYS:
            merged[key] = value
    if "color" in overlay and "text_color" not in overlay:
        merged["text_color"] = overlay.get("color")
    return merged


def _apply_bound_style(
    base: dict[str, Any],
    bind_style: dict[str, Any] | None,
    bindings: Any,
    ctx,
    *,
    element_type: str | None = None,
    element_id: str | None = None,
) -> dict[str, Any]:
    if not isinstance(bind_style, dict) or not bind_style:
        return base
    merged = dict(base)
    for key, bind_key in bind_style.items():
        if bind_key is None:
            continue
        value = _resolve_binding(bindings, str(bind_key), ctx)
        if value is None:
            continue
        merged[key] = value
    merged = _normalize_color_style(merged, element_type, element_id)
    return merged


class _InvisibleButton(Button):
    def render(self, ctx) -> None:
        return None


class LayoutReloader:
    def __init__(self, path: Path, *, min_interval_s: float = 0.2):
        self.path = path
        self.min_interval_s = float(min_interval_s)
        self.document: LayoutDocument | None = None
        self._last_mtime_ns = 0
        self._last_check = 0.0
        self.error: str | None = None
        self.reload(force=True)

    def _mtime_ns(self) -> int:
        stat = self.path.stat()
        return int(getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000)))

    def reload(self, *, force: bool = False) -> bool:
        now = time.time()
        if not force and now - self._last_check < self.min_interval_s:
            return False
        self._last_check = now
        try:
            mtime_ns = self._mtime_ns()
        except FileNotFoundError:
            self.error = f"Layout file not found: {self.path}"
            return False
        if not force and mtime_ns <= self._last_mtime_ns:
            return False
        try:
            _require_yaml()
            raw = self.path.read_text(encoding="utf-8")
            data = yaml.safe_load(raw) or {}
            if not isinstance(data, dict):
                raise ValueError("Layout YAML must be a mapping at top level.")
            doc = LayoutDocument(
                path=self.path,
                data=data,
                globals=dict(data.get("globals") or {}),
                styles=dict(data.get("styles") or {}),
                pages=dict(data.get("pages") or {}),
                templates=dict(data.get("templates") or {}),
            )
            self.document = doc
            self._last_mtime_ns = mtime_ns
            self.error = None
            return True
        except Exception as exc:
            self.error = f"Layout reload failed: {exc}"
            return False


def compile_layout(
    ctx,
    document: LayoutDocument,
    page_id: str,
    *,
    actions: dict[str, Callable] | None = None,
    bindings: Any = None,
) -> LayoutRenderPlan:
    actions = actions or {}
    page = document.pages.get(page_id)
    if page is None:
        raise ValueError(f"Unknown page id: {page_id}")

    styles = document.styles
    drawables: list[dict[str, Any]] = []
    components: list[Any] = []
    slots: dict[str, dict[str, Any]] = {}
    state_sources: dict[str, Any] = {}

    def compile_elements(
        elements: Iterable[dict[str, Any]],
        *,
        origin_gx: float = 0.0,
        origin_gy: float = 0.0,
        group_style: dict[str, Any] | str | None = None,
        state_owner: str | None = None,
    ) -> None:
        for idx, element in enumerate(elements):
            if not isinstance(element, dict):
                continue
            etype = str(element.get("type", "text")).lower()
            if etype == "label":
                etype = "text"
            if etype == "supertext":
                etype = "super_text"
            if etype == "panel":
                etype = "rect"

            gx, gy, gw, gh = _normalize_rect(element)
            gx += origin_gx
            gy += origin_gy
            element_id = str(element.get("id") or stable_component_id(etype, seed=idx))
            style = _resolve_style(
                styles,
                group_style,
                element.get("style"),
                element,
                element_type=etype,
                element_id=element_id,
            )
            z_index = int(element.get("z_index", 0))
            stable_order = _stable_hash(element_id)

            if etype == "slot":
                slots[element_id] = {"id": element_id, "gx": gx, "gy": gy, "gw": gw, "gh": gh}
                continue

            if etype == "button":
                x1 = ctx.gx(gx)
                y1 = ctx.gy(gy)
                x2 = ctx.gx(gx + gw)
                y2 = ctx.gy(gy + gh)
                label = element.get("label") or element.get("text") or element_id
                on_click = element.get("on_click")
                nav = element.get("nav")
                components.append(
                    Button(
                        element_id,
                        str(label),
                        gx=gx,
                        gy=gy,
                        width_px=x2 - x1,
                        height_px=y2 - y1,
                        scope=str(element.get("scope") or page.get("focus_scope") or document.globals.get("focus_scope") or "main"),
                        nav=nav,
                        color=style.get("color"),
                        label_align_h=style.get("label_align_h", "center"),
                        label_align_v=style.get("label_align_v", "center"),
                        label_orientation=style.get("label_orientation", "horizontal"),
                        label_line_step=style.get("label_line_step", style.get("line_step", 1)),
                        on_select=(
                            None
                            if on_click is None
                            else (lambda btn, c, action=str(on_click), element=element: _dispatch_action(actions, action, btn, c, element))
                        ),
                    )
                )
                state_sources[element_id] = components[-1]
                continue

            drawables.append(
                {
                    "id": element_id,
                    "type": etype,
                    "gx": gx,
                    "gy": gy,
                    "gw": gw,
                    "gh": gh,
                    "style": style,
                    "element": element,
                    "z_index": z_index,
                    "stable_order": stable_order,
                    "state_owner": state_owner,
                    "state_styles": element.get("state_styles"),
                }
            )

    def compile_group(
        group: dict[str, Any],
        *,
        parent_origin=(0.0, 0.0),
        parent_style=None,
        parent_state_owner: str | None = None,
    ) -> None:
        gx, gy, gw, gh = _normalize_rect(group)
        origin_gx = parent_origin[0] + gx
        origin_gy = parent_origin[1] + gy
        group_style = group.get("style", parent_style)
        group_state_owner = parent_state_owner

        interaction = group.get("interaction")
        if isinstance(interaction, dict) and str(interaction.get("type", "button")).lower() == "button":
            interaction_id = str(interaction.get("id") or group.get("id") or stable_component_id("group_button"))
            x1 = ctx.gx(origin_gx)
            y1 = ctx.gy(origin_gy)
            x2 = ctx.gx(origin_gx + gw)
            y2 = ctx.gy(origin_gy + gh)
            on_click = interaction.get("on_click")
            nav = interaction.get("nav")
            scope = interaction.get("scope") or page.get("focus_scope") or document.globals.get("focus_scope") or "main"
            button = _InvisibleButton(
                interaction_id,
                "",
                gx=origin_gx,
                gy=origin_gy,
                width_px=x2 - x1,
                height_px=y2 - y1,
                scope=str(scope),
                nav=nav,
                on_select=(
                    None
                    if on_click is None
                    else (lambda btn, c, action=str(on_click), element=group: _dispatch_action(actions, action, btn, c, element))
                ),
                pressable=bool(interaction.get("pressable", True)),
                focusable=bool(interaction.get("focusable", True)),
            )
            components.append(button)
            state_sources[interaction_id] = button
            group_state_owner = interaction_id

        elements = group.get("elements", [])
        if isinstance(elements, list):
            compile_elements(
                elements,
                origin_gx=origin_gx,
                origin_gy=origin_gy,
                group_style=group_style,
                state_owner=group_state_owner,
            )
        for child in group.get("groups", []) or []:
            if isinstance(child, dict):
                compile_group(
                    child,
                    parent_origin=(origin_gx, origin_gy),
                    parent_style=group_style,
                    parent_state_owner=group_state_owner,
                )

    page_elements = page.get("elements", [])
    if isinstance(page_elements, list):
        compile_elements(page_elements)

    for group in page.get("groups", []) or []:
        if isinstance(group, dict):
            compile_group(group)

    drawables.sort(key=lambda item: (item["z_index"], item["stable_order"]))

    return LayoutRenderPlan(
        page_id=page_id,
        components=components,
        drawables=drawables,
        slots=slots,
        state_sources=state_sources,
    )


def _dispatch_action(actions: dict[str, Callable], action: str, button, ctx, element) -> None:
    fn = actions.get(action)
    if fn is None:
        return
    try:
        fn(button, ctx, element)
        return
    except TypeError:
        pass
    try:
        fn(button, ctx)
        return
    except TypeError:
        pass
    fn(ctx)


def _resolve_state(plan: LayoutRenderPlan, ctx, owner_id: str | None) -> str:
    if owner_id is None:
        return "normal"
    source = plan.state_sources.get(owner_id)
    if source is not None and getattr(source, "selected", False):
        return "active"
    if ctx.get_focus(None) == owner_id:
        return "hover"
    return "normal"


def render_layout(ctx, plan: LayoutRenderPlan, *, bindings: Any = None) -> None:
    for item in plan.drawables:
        etype = item["type"]
        element = item["element"]
        style = item["style"]
        element_id = item.get("id")
        state_styles = item.get("state_styles")
        if isinstance(state_styles, dict) and state_styles:
            state = _resolve_state(plan, ctx, item.get("state_owner"))
            overlay = state_styles.get(state)
            if overlay is None and state != "normal":
                overlay = state_styles.get("normal")
            style = _apply_state_style(style, overlay)
        style = _apply_bound_style(
            style,
            element.get("bind_style"),
            bindings,
            ctx,
            element_type=etype,
            element_id=element_id,
        )
        style = _normalize_color_style(style, etype, element_id)
        gx = item["gx"]
        gy = item["gy"]
        gw = item["gw"]
        gh = item["gh"]

        if etype == "text":
            text = _text_from_element(element, bindings, ctx)
            ctx.draw_text_box(
                gx,
                gy,
                gw,
                gh,
                style.get("text_color") or style.get("color") or "White",
                text,
                align_h=style.get("align_h", "left"),
                align_v=style.get("align_v", "top"),
                orientation=style.get("orientation", "horizontal"),
                line_step=style.get("line_step", 1),
            )
            continue

        if etype == "super_text":
            text = _text_from_element(element, bindings, ctx)
            if not text:
                continue
            px, py = ctx.grid_to_px(gx, gy)
            ctx.draw_super_text_px(
                px,
                py,
                style.get("text_color") or style.get("color") or "White",
                text,
                scale=element.get("scale", 1),
                mode=element.get("mode"),
                line_step=element.get("line_step", 1),
            )
            continue

        if etype == "rect":
            x1 = ctx.gx(gx)
            y1 = ctx.gy(gy)
            x2 = ctx.gx(gx + gw)
            y2 = ctx.gy(gy + gh)
            line_color = style.get("line_color") or style.get("color") or "White"
            fill_color = style.get("fill_color")
            filled = bool(style.get("filled", style.get("fill") is not None))
            pattern_cfg = style.get("pattern")
            pattern_enabled = bool(pattern_cfg)
            pattern_opts = dict(pattern_cfg) if isinstance(pattern_cfg, dict) else {}
            spacing = pattern_opts.get("spacing", style.get("pattern_spacing"))
            angle_deg = pattern_opts.get("angle_deg", style.get("pattern_angle_deg"))
            pattern_thickness = pattern_opts.get("thickness", style.get("pattern_thickness"))
            offset = pattern_opts.get("offset", style.get("pattern_offset"))
            pattern_color = pattern_opts.get("color", style.get("pattern_color", line_color))
            pattern_outline = pattern_opts.get("outline", style.get("pattern_outline", True))

            if filled:
                ctx.draw_rect(
                    fill_color or line_color,
                    x1,
                    y1,
                    x2 - x1,
                    y2 - y1,
                    filled=True,
                    thickness=style.get("thickness", 1),
                )
            if pattern_enabled:
                ctx.draw_pattern_rect(
                    pattern_color or line_color,
                    x1,
                    y1,
                    x2 - x1,
                    y2 - y1,
                    spacing=spacing,
                    angle_deg=angle_deg,
                    thickness=pattern_thickness,
                    offset=offset,
                )
                if pattern_outline:
                    ctx.draw_rect(
                        line_color,
                        x1,
                        y1,
                        x2 - x1,
                        y2 - y1,
                        filled=False,
                        thickness=style.get("thickness", 1),
                    )
            elif not filled:
                ctx.draw_rect(
                    line_color,
                    x1,
                    y1,
                    x2 - x1,
                    y2 - y1,
                    filled=False,
                    thickness=style.get("thickness", 1),
                )
            continue

        if etype == "box":
            ctx.draw_box(
                gx,
                gy,
                gw,
                gh,
                style.get("line_color") or style.get("color") or "White",
                thickness=style.get("thickness", 1),
            )
            continue

        if etype == "poly":
            vertices = element.get("vertices_px", [])
            if not vertices:
                continue
            origin_x = ctx.gx(gx)
            origin_y = ctx.gy(gy)
            line_color = style.get("line_color") or style.get("color") or "White"
            fill_color = style.get("fill_color")
            filled = bool(style.get("filled", style.get("fill") is not None))
            pattern_cfg = style.get("pattern")
            pattern_enabled = bool(pattern_cfg)
            pattern_opts = dict(pattern_cfg) if isinstance(pattern_cfg, dict) else {}
            spacing = pattern_opts.get("spacing", style.get("pattern_spacing"))
            angle_deg = pattern_opts.get("angle_deg", style.get("pattern_angle_deg"))
            pattern_thickness = pattern_opts.get("thickness", style.get("pattern_thickness"))
            offset = pattern_opts.get("offset", style.get("pattern_offset"))
            pattern_color = pattern_opts.get("color", style.get("pattern_color", line_color))
            pattern_outline = pattern_opts.get("outline", style.get("pattern_outline", True))

            if filled:
                ctx.draw_poly(
                    vertices,
                    fill_color or line_color,
                    origin_x,
                    origin_y,
                    filled=True,
                    thickness=style.get("thickness", 1),
                )
            if pattern_enabled:
                ctx.draw_pattern_poly(
                    vertices,
                    pattern_color or line_color,
                    origin_x,
                    origin_y,
                    spacing=spacing,
                    angle_deg=angle_deg,
                    thickness=pattern_thickness,
                    offset=offset,
                )
                if pattern_outline:
                    ctx.draw_poly(
                        vertices,
                        line_color,
                        origin_x,
                        origin_y,
                        filled=False,
                        thickness=style.get("thickness", 1),
                    )
            elif not filled:
                ctx.draw_poly(
                    vertices,
                    line_color,
                    origin_x,
                    origin_y,
                    filled=False,
                    thickness=style.get("thickness", 1),
                )
            continue

        if etype == "arrow":
            start = element.get("start_gx"), element.get("start_gy")
            end = element.get("end_gx"), element.get("end_gy")
            if None in start or None in end:
                continue
            start_px = (ctx.gx(float(start[0])), ctx.gy(float(start[1])))
            end_px = (ctx.gx(float(end[0])), ctx.gy(float(end[1])))
            _draw_arrow(
                ctx,
                start_px,
                end_px,
                color=style.get("line_color") or style.get("color") or "White",
                thickness=float(style.get("thickness", 1.0)),
                head_len=float(element.get("head_len_px", 10)),
                head_w=float(element.get("head_w_px", 6)),
            )


def _draw_arrow(ctx, start_px, end_px, *, color, thickness, head_len, head_w) -> None:
    sx, sy = start_px
    ex, ey = end_px
    dx = ex - sx
    dy = ey - sy
    length = (dx * dx + dy * dy) ** 0.5
    if length <= 0.01:
        return
    ux = dx / length
    uy = dy / length
    px = -uy
    py = ux
    base_x = ex - ux * head_len
    base_y = ey - uy * head_len
    left_x = base_x + px * head_w
    left_y = base_y + py * head_w
    right_x = base_x - px * head_w
    right_y = base_y - py * head_w

    ctx.draw_poly([(0.0, 0.0), (dx, dy)], color, sx, sy, filled=False, thickness=thickness)
    ctx.draw_poly(
        [(ex, ey), (left_x, left_y), (right_x, right_y)],
        color,
        0.0,
        0.0,
        filled=True,
        thickness=1,
    )


class LayoutPage(Page):
    def __init__(
        self,
        page_id: str,
        *,
        layout: LayoutReloader,
        actions: dict[str, Callable] | None = None,
        bindings: Any = None,
    ):
        super().__init__(page_id)
        self._layout = layout
        self._actions = actions or {}
        self._bindings = bindings
        self._plan: LayoutRenderPlan | None = None

    def _apply_globals(self) -> None:
        doc = self._layout.document
        if doc is None:
            return
        layout_mode = doc.globals.get("layout_mode")
        if layout_mode is not None:
            GUI.set_layout_mode(bool(layout_mode))
        _install_palette(doc.globals)

    def _normalize_component_overrides(self, raw: Any) -> dict[str, dict[str, Any]]:
        if not isinstance(raw, dict):
            return {}
        overrides: dict[str, dict[str, Any]] = {}
        for key, value in raw.items():
            if isinstance(value, dict):
                overrides[str(key)] = dict(value)
                continue
            overrides[str(key)] = {"enabled": bool(value), "visible": bool(value)}
        return overrides

    def _collect_component_overrides(self) -> dict[str, dict[str, Any]]:
        doc = self._layout.document
        if doc is None:
            return {}

        page_block = doc.pages.get(self.page_id, {})
        overrides: dict[str, dict[str, Any]] = {}

        def add_overrides(raw: Any) -> None:
            normalized = self._normalize_component_overrides(raw)
            if not normalized:
                return
            overrides.update(normalized)

        def add_disabled(raw: Any) -> None:
            if not isinstance(raw, (list, tuple, set)):
                return
            for item in raw:
                overrides[str(item)] = {"enabled": False, "visible": False}

        add_overrides(doc.globals.get("components"))
        add_overrides(page_block.get("components"))
        add_disabled(doc.globals.get("disable_components") or doc.globals.get("disabled_components"))
        add_disabled(page_block.get("disable_components") or page_block.get("disabled_components"))

        return overrides

    def _apply_component_overrides(self, components: Iterable[Any]) -> list[Any]:
        overrides = self._collect_component_overrides()
        if not overrides:
            return list(components)

        filtered: list[Any] = []
        for component in components:
            component_id = getattr(component, "component_id", None)
            if component_id is None:
                filtered.append(component)
                continue
            override = overrides.get(str(component_id))
            if override is None:
                filtered.append(component)
                continue
            if override.get("present") is False or override.get("remove") is True:
                continue
            if "enabled" in override:
                component.enabled = bool(override["enabled"])
            if "visible" in override:
                component.visible = bool(override["visible"])
            filtered.append(component)
        return filtered

    def _sync_components(self, ctx) -> None:
        doc = self._layout.document
        if doc is None:
            return
        focus_scope = doc.pages.get(self.page_id, {}).get("focus_scope") or doc.globals.get("focus_scope") or "main"
        ctx.set_active_focus_scope(str(focus_scope))
        try:
            plan = compile_layout(ctx, doc, self.page_id, actions=self._actions, bindings=self._bindings)
        except Exception as exc:
            self._layout.error = f"Layout compile failed: {exc}"
            return
        self._layout.error = None
        self._plan = plan
        self.set_components(ctx, self._plan.components)

    def set_components(self, ctx, components, *, ensure_focus: bool = True) -> None:
        filtered = self._apply_component_overrides(components)
        super().set_components(ctx, filtered, ensure_focus=ensure_focus)

    def on_enter(self, ctx) -> None:
        self._apply_globals()
        self._sync_components(ctx)

    def update(self, ctx, dt: float) -> None:
        if self._layout.reload():
            self._apply_globals()
            self._sync_components(ctx)
        super().update(ctx, dt)

    def handle_event(self, event, ctx) -> bool:
        import pygame

        if getattr(event, "type", None) == pygame.KEYDOWN:
            if ctx.key_to_focus_direction(event.key) is not None:
                ctx.move_focus_by_key(event.key)
                return True
        return super().handle_event(event, ctx)

    def _render_layout_error(self, ctx, message: str) -> None:
        ctx.draw_text_box(2, 2, 40, 4, "CRT_Red", message, align_h="left", align_v="top", line_step=1)

    def render(self, ctx) -> None:
        if self._layout.document is None:
            self._render_layout_error(ctx, self._layout.error or "Layout missing")
            return
        if self._plan is None:
            self._sync_components(ctx)
        if self._plan is not None:
            render_layout(ctx, self._plan, bindings=self._bindings)
        super().render(ctx)
        if self._layout.error:
            self._render_layout_error(ctx, self._layout.error)
