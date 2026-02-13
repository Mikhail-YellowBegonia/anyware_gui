from __future__ import annotations

from dataclasses import dataclass

from core import GUI

REQUIRED_GUI_STABLE_API = (
    "begin_frame",
    "finish_frame",
    "gx",
    "gy",
    "px",
    "py",
    "grid_to_px",
    "static",
    "hstatic",
    "ani_char",
    "draw_box",
    "draw_rect",
    "draw_poly",
    "draw_pattern_rect",
    "draw_pattern_poly",
    "add_focus_node",
    "update_focus_node",
    "remove_focus_node",
    "set_focus",
    "get_focus",
    "set_active_focus_scope",
    "move_focus_by_key",
    "key_to_focus_direction",
    "draw_focus_frame",
    "get_dynamic_offset",
    "set_dynamic_offset",
    "step_dynamic_offset",
)
TEXT_ORIENTATIONS = ("horizontal", "vertical")


@dataclass
class FrameInfo:
    frame: int = 0
    dt: float = 0.0


class AnywareContext:
    """
    Anyware app context.

    Rule:
    - Anyware-first APIs should be used by default.
    - Raw GUI access is optional and explicitly gated.
    """

    def __init__(self, runtime, *, allow_raw_gui: bool = False):
        self.runtime = runtime
        self.frame = FrameInfo()
        self._allow_raw_gui = bool(allow_raw_gui)
        contract = GUI.get_api_contract()
        stable = set(contract.get("stable", []))
        missing = [name for name in REQUIRED_GUI_STABLE_API if name not in stable]
        if missing:
            missing_csv = ", ".join(missing)
            raise RuntimeError(f"GUI stable API contract missing required entries: {missing_csv}")

    def set_frame_info(self, frame: int, dt: float) -> None:
        self.frame.frame = int(frame)
        self.frame.dt = float(dt)

    # Lifecycle
    def begin_frame(self, *, clear_char: str = " ", clear_color=0, reset_overlay: bool = True, advance_frame: bool = True):
        return self.runtime.begin_frame(
            clear_char=clear_char,
            clear_color=clear_color,
            reset_overlay=reset_overlay,
            advance_frame=advance_frame,
        )

    def finish_frame(self, surface, *, flip: bool = False):
        return self.runtime.finish_frame(surface, flip=flip)

    # Coordinate mapping
    def gx(self, value: float) -> float:
        return GUI.gx(value)

    def gy(self, value: float) -> float:
        return GUI.gy(value)

    def px(self, value: float) -> float:
        return GUI.px(value)

    def py(self, value: float) -> float:
        return GUI.py(value)

    def grid_to_px(self, gx_value: float, gy_value: float, ox: float = 0, oy: float = 0):
        return GUI.grid_to_px(gx_value, gy_value, ox=ox, oy=oy)

    # Text and drawing wrappers
    def clear_screen(self, char: str = " ", color=0):
        return GUI.clear_screen(char=char, color=color)

    def _normalize_text_orientation(self, orientation: str | None) -> str:
        if orientation is None:
            return "horizontal"
        lower = str(orientation).strip().lower()
        if lower not in TEXT_ORIENTATIONS:
            raise ValueError(f"Unsupported text orientation: {orientation}")
        return lower

    def label(
        self,
        x: int,
        y: int,
        color,
        content,
        *,
        orientation: str = "horizontal",
        line_step: int = 1,
    ):
        orient = self._normalize_text_orientation(orientation)
        if orient == "vertical":
            return GUI.hstatic(x, y, color, content, line_step=line_step)
        return GUI.static(x, y, color, content)

    def text(
        self,
        x: int,
        y: int,
        color,
        content,
        *,
        orientation: str = "horizontal",
        line_step: int = 1,
    ):
        return self.label(
            x,
            y,
            color,
            content,
            orientation=orientation,
            line_step=line_step,
        )

    def static(self, x: int, y: int, color, content):
        """Compatibility path. Prefer label()/text() in Anyware code."""
        return self.label(x, y, color, content, orientation="horizontal")

    def hstatic(self, x: int, y: int, color, content, line_step: int = 1):
        """Compatibility path. Prefer label()/text() in Anyware code."""
        return self.label(x, y, color, content, orientation="vertical", line_step=line_step)

    def ani_char(self, x: int, y: int, color, animation, *, local_offset=None, global_offset=None, slowdown=None):
        return GUI.ani_char(
            x,
            y,
            color,
            animation,
            local_offset=local_offset,
            global_offset=global_offset,
            slowdown=slowdown,
        )

    def draw_box(self, gx_value: float, gy_value: float, gw: float, gh: float, color, *, padding=None, thickness=None):
        return GUI.draw_box(gx_value, gy_value, gw, gh, color, padding=padding, thickness=thickness)

    def draw_rect(self, color, x_px: float, y_px: float, w_px: float, h_px: float, *, filled=None, thickness=None, base_font_height_px=None):
        return GUI.draw_rect(
            color,
            x_px,
            y_px,
            w_px,
            h_px,
            filled=filled,
            thickness=thickness,
            base_font_height_px=base_font_height_px,
        )

    def draw_poly(self, shape_or_vertices, color, x_px: float, y_px: float, *, filled=None, thickness=None, base_font_height_px=None):
        return GUI.draw_poly(
            shape_or_vertices,
            color,
            x_px,
            y_px,
            filled=filled,
            thickness=thickness,
            base_font_height_px=base_font_height_px,
        )

    def draw_pattern_rect(self, color, x_px: float, y_px: float, w_px: float, h_px: float, *, spacing=None, angle_deg=None, thickness=None, offset=None, base_font_height_px=None):
        return GUI.draw_pattern_rect(
            color,
            x_px,
            y_px,
            w_px,
            h_px,
            spacing=spacing,
            angle_deg=angle_deg,
            thickness=thickness,
            offset=offset,
            base_font_height_px=base_font_height_px,
        )

    def draw_pattern_poly(self, shape_or_vertices, color, x_px: float, y_px: float, *, spacing=None, angle_deg=None, thickness=None, offset=None, base_font_height_px=None):
        return GUI.draw_pattern_poly(
            shape_or_vertices,
            color,
            x_px,
            y_px,
            spacing=spacing,
            angle_deg=angle_deg,
            thickness=thickness,
            offset=offset,
            base_font_height_px=base_font_height_px,
        )

    # Focus wrappers
    def key_to_focus_direction(self, key):
        return GUI.key_to_focus_direction(key)

    def move_focus_by_key(self, key):
        return GUI.move_focus_by_key(key)

    def get_focus(self, default=None):
        return GUI.get_focus(default)

    def add_focus_node(self, node_id, rect, *, enabled=True, visible=True, nav=None, scope="default"):
        return GUI.add_focus_node(
            node_id,
            rect,
            enabled=enabled,
            visible=visible,
            nav=nav,
            scope=scope,
        )

    def update_focus_node(self, node_id, *, rect=None, enabled=None, visible=None, nav=None, scope=None):
        return GUI.update_focus_node(
            node_id,
            rect=rect,
            enabled=enabled,
            visible=visible,
            nav=nav,
            scope=scope,
        )

    def remove_focus_node(self, node_id):
        return GUI.remove_focus_node(node_id)

    def set_focus(self, node_id, *, activate_scope=True):
        return GUI.set_focus(node_id, activate_scope=activate_scope)

    def set_active_focus_scope(self, scope, *, pick_first=True):
        return GUI.set_active_focus_scope(scope, pick_first=pick_first)

    def draw_focus_frame(self, color, *, node_id=None, padding=0.0, thickness=1.0):
        return GUI.draw_focus_frame(color, node_id=node_id, padding=padding, thickness=thickness)

    # Dynamic channels
    def get_dynamic_offset(self, channel="default", default=0.0):
        return GUI.get_dynamic_offset(channel=channel, default=default)

    def set_dynamic_offset(self, channel="default", value=0.0, wrap=None):
        return GUI.set_dynamic_offset(channel=channel, value=value, wrap=wrap)

    def step_dynamic_offset(self, channel="default", speed=0.0, wrap=None):
        return GUI.step_dynamic_offset(channel=channel, speed=speed, wrap=wrap)

    # Escape hatch
    def raw_gui(self):
        if not self._allow_raw_gui:
            raise RuntimeError(
                "Raw GUI access is disabled. "
                "Enable allow_raw_gui=True explicitly when creating AnywareApp."
            )
        return GUI
