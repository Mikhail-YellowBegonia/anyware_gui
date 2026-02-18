from __future__ import annotations

import colorsys
import importlib.util
import sys
import time
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parents[3]
APPS_DIR = ROOT / "apps"
for path in (ROOT, APPS_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from _bootstrap import FONTS_DIR, ensure_repo_root_on_path

ensure_repo_root_on_path()

from core import GUI
from core.anyware import AnywareApp, Button, Page

from reactor_client import ReactorClient

LAYOUT_PATH = Path(__file__).resolve().parent / "reactor_ui_layout.py"
LAYOUT_MODULE_NAME = "reactor_ui_layout"


def _load_layout_module(path: Path):
    spec = importlib.util.spec_from_file_location(LAYOUT_MODULE_NAME, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load layout module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[LAYOUT_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    raw = value.strip().lstrip("#")
    if len(raw) != 6:
        raise ValueError(f"Invalid hex color: {value}")
    return (int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16))


def _register_palette_color(name: str, hex_value: str, *, index: int) -> None:
    r, g, b = _hex_to_rgb(hex_value)
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    GUI.hsv_palette[index] = (h, s, v, name)


def _install_palette(layout_module) -> None:
    palette = getattr(layout_module, "PALETTE", {})
    bg_hex = palette.get("bg_hex", "#fdf6f0")
    default_hex = palette.get("default_hex", "#586e75")
    special_hex = palette.get("special_hex", "#78cd26")

    _register_palette_color("Solar_Default", default_hex, index=240)
    _register_palette_color("Solar_Special", special_hex, index=241)

    GUI.refresh_palette_cache()
    GUI.set_layout_mode(False)
    GUI.set_display_defaults(window_bg_color_rgb=_hex_to_rgb(bg_hex))


class LayoutReloader:
    def __init__(self, path: Path, *, min_interval_s: float = 0.2):
        self.path = path
        self.min_interval_s = float(min_interval_s)
        self.module = None
        self._last_mtime_ns = 0
        self._last_check = 0.0
        self.error = None
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
            module = _load_layout_module(self.path)
            self.module = module
            self._last_mtime_ns = mtime_ns
            self.error = None
            _install_palette(module)
            return True
        except Exception as exc:
            self.error = f"Layout reload failed: {exc}"
            return False


class ReactorPage(Page):
    def __init__(self, page_id: str, *, app: AnywareApp, layout: LayoutReloader):
        super().__init__(page_id)
        self.app = app
        self.layout = layout
        self._focus_scope = "nav"

    def on_enter(self, ctx) -> None:
        self._sync_components(ctx)

    def update(self, ctx, dt: float) -> None:
        if self.layout.reload():
            self._sync_components(ctx)

    def handle_event(self, event, ctx) -> bool:
        if event.type == pygame.KEYDOWN:
            if ctx.key_to_focus_direction(event.key) is not None:
                ctx.move_focus_by_key(event.key)
                return True
        return super().handle_event(event, ctx)

    def _sync_components(self, ctx) -> None:
        layout = self.layout.module
        if layout is None:
            return
        scope = str(getattr(layout, "FOCUS_SCOPE", "nav"))
        self._focus_scope = scope
        ctx.set_active_focus_scope(scope)
        components = self._build_nav_buttons(ctx, layout, scope)
        self.set_components(ctx, components)

    def _build_nav_buttons(self, ctx, layout, scope: str):
        buttons = list(getattr(layout, "NAV_BUTTONS", []))
        comps = []
        color = getattr(layout, "DEFAULT_COLOR", "Solar_Default")
        active_color = getattr(layout, "SPECIAL_COLOR", "Solar_Special")
        for btn in buttons:
            bid = str(btn.get("id"))
            label = btn.get("label") or bid
            gx = btn.get("gx", 0)
            gy = btn.get("gy", 0)
            gw = btn.get("gw", 1)
            gh = btn.get("gh", 1)
            target = btn.get("target")
            x, y, w, h = self._grid_rect_px(ctx, gx, gy, gw, gh)
            comps.append(
                Button(
                    bid,
                    label,
                    gx=gx,
                    gy=gy,
                    width_px=w,
                    height_px=h,
                    scope=scope,
                    nav=btn.get("nav"),
                    color=color,
                    label_align_h="center",
                    label_align_v="center",
                    label_line_step=1,
                    status=lambda _b, _ctx, target=target, page_id=self.page_id: (
                        "active" if target == page_id else None
                    ),
                    status_color_map={"active": active_color},
                    status_default_color=None,
                    on_select=lambda _b, _ctx, target=target: self._on_nav_select(target, _b),
                )
            )
        return comps

    def _on_nav_select(self, target: str | None, button) -> None:
        if button is not None:
            button.selected = False
        if not target or target == self.page_id:
            return
        self.app.switch_page(target)

    def _grid_rect_px(self, ctx, gx: float, gy: float, gw: float, gh: float):
        x1 = ctx.gx(gx)
        y1 = ctx.gy(gy)
        x2 = ctx.gx(gx + gw)
        y2 = ctx.gy(gy + gh)
        return (x1, y1, x2 - x1, y2 - y1)

    def _render_layout_error(self, ctx, message: str):
        ctx.draw_text_box(2, 45, 124, 3, "Solar_Default", message, align_h="left", align_v="top", line_step=1)

    def render(self, ctx) -> None:
        layout = self.layout.module
        if layout is None:
            self._render_layout_error(ctx, self.layout.error or "Layout missing")
            return

        nav_area = getattr(layout, "NAV_AREA", None)
        if nav_area:
            x, y, w, h = self._grid_rect_px(ctx, nav_area["gx"], nav_area["gy"], nav_area["gw"], nav_area["gh"])
            ctx.draw_rect(
                nav_area.get("color", "Solar_Default"),
                x,
                y,
                w,
                h,
                filled=nav_area.get("filled", False),
                thickness=nav_area.get("thickness", 1),
            )

        footer_area = getattr(layout, "FOOTER_AREA", None)
        if footer_area:
            x, y, w, h = self._grid_rect_px(ctx, footer_area["gx"], footer_area["gy"], footer_area["gw"], footer_area["gh"])
            ctx.draw_rect(
                footer_area.get("color", "Solar_Default"),
                x,
                y,
                w,
                h,
                filled=footer_area.get("filled", False),
                thickness=footer_area.get("thickness", 1),
            )

        logo = getattr(layout, "LOGO_POLY", None)
        if logo:
            x = ctx.gx(logo.get("gx", 0))
            y = ctx.gy(logo.get("gy", 0))
            ctx.draw_poly(
                logo.get("vertices_px", []),
                logo.get("color", "Solar_Default"),
                x,
                y,
                filled=logo.get("filled", False),
                thickness=logo.get("thickness", 1),
            )

        net_box = getattr(layout, "NET_INDICATOR", None)
        if net_box:
            x, y, w, h = self._grid_rect_px(ctx, net_box["gx"], net_box["gy"], net_box["gw"], net_box["gh"])
            ctx.draw_rect(
                net_box.get("color", "Solar_Default"),
                x,
                y,
                w,
                h,
                filled=net_box.get("filled", False),
                thickness=net_box.get("thickness", 1),
            )

        comms = getattr(layout, "COMMS_INDICATOR", None)
        if comms:
            x, y, w, h = self._grid_rect_px(ctx, comms["gx"], comms["gy"], comms["gw"], comms["gh"])
            ctx.draw_rect(
                comms.get("color", "Solar_Special"),
                x,
                y,
                w,
                h,
                filled=True,
                thickness=1,
            )

        net_info = getattr(layout, "NET_INFO_BOX", None)
        if net_info:
            x, y, w, h = self._grid_rect_px(ctx, net_info["gx"], net_info["gy"], net_info["gw"], net_info["gh"])
            ctx.draw_rect(
                net_info.get("color", "Solar_Default"),
                x,
                y,
                w,
                h,
                filled=False,
                thickness=1,
            )
            lines = list(net_info.get("text_lines", []))
            if lines:
                ctx.draw_text_box(
                    net_info["gx"] + 1,
                    net_info["gy"],
                    max(1, net_info["gw"] - 2),
                    net_info["gh"],
                    net_info.get("color", "Solar_Default"),
                    "\n".join(lines),
                    align_h="left",
                    align_v="center",
                    line_step=1,
            )

        panels = getattr(layout, "PANELS", {})
        panel = panels.get(self.page_id)
        if panel:
            x, y, w, h = self._grid_rect_px(ctx, panel["gx"], panel["gy"], panel["gw"], panel["gh"])
            ctx.draw_rect(
                panel.get("color", getattr(layout, "DEFAULT_COLOR", "Solar_Default")),
                x,
                y,
                w,
                h,
                filled=panel.get("filled", False),
                thickness=panel.get("thickness", 1),
            )

        footer_blocks = getattr(layout, "FOOTER_BLOCKS", [])
        for block in footer_blocks:
            x, y, w, h = self._grid_rect_px(ctx, block["gx"], block["gy"], block["gw"], block["gh"])
            ctx.draw_rect(
                block.get("color", "Solar_Default"),
                x,
                y,
                w,
                h,
                filled=True,
                thickness=1,
            )

        footer_texts = getattr(layout, "FOOTER_TEXTS", [])
        for text in footer_texts:
            ctx.draw_text_box(
                text["gx"],
                text["gy"],
                text["gw"],
                text["gh"],
                text.get("color", "Solar_Default"),
                text.get("text", ""),
                align_h=text.get("align_h", "left"),
                align_v=text.get("align_v", "center"),
                line_step=text.get("line_step", 1),
            )

        super().render(ctx)

        if comms:
            x, y, w, h = self._grid_rect_px(ctx, comms["gx"], comms["gy"], comms["gw"], comms["gh"])
            ctx.draw_super_text_px(
                x,
                y,
                getattr(layout, "DEFAULT_COLOR", "Solar_Default"),
                comms.get("text", "COMMS"),
                align_h="center",
                align_v="center",
                box_w_px=w,
                box_h_px=h,
                line_step=1,
            )

        if self.layout.error:
            self._render_layout_error(ctx, self.layout.error)


class ReactorApp:
    def __init__(self):
        self.layout = LayoutReloader(LAYOUT_PATH)
        self.client = ReactorClient()

        self.app = AnywareApp(
            title="Anyware Reactor UI (v0.0.9)",
            clear_color="Solar_Default",
            display_defaults={
                "fps": 16,
                "target_fps": 60,
                "rows": 48,
                "cols": 128,
                "window_noframe": False,
                "window_always_on_top": False,
            },
            allow_raw_gui=False,
        )

        font_ascii = FONTS_DIR / "DEM-MO typeface" / "Mono" / "DEM-MOMono-300.otf"
        font_cjk = FONTS_DIR / "wqy-zenhei" / "wqy-zenhei.ttc"
        self.app.set_fonts(ascii_path=str(font_ascii), cjk_path=str(font_cjk), cell_w=8, cell_h=16, size_px=16)

        pages = [
            ReactorPage("status", app=self.app, layout=self.layout),
            ReactorPage("diagram", app=self.app, layout=self.layout),
            ReactorPage("control", app=self.app, layout=self.layout),
            ReactorPage("core", app=self.app, layout=self.layout),
        ]
        self.app.register_pages(pages)
        self.app.set_root_page(pages[0])

    def run(self) -> None:
        original_update = self.app.page_stack.update

        def _update(ctx, dt: float) -> None:
            self.client.poll_and_log()
            original_update(ctx, dt)

        self.app.page_stack.update = _update
        self.app.run()


def main() -> None:
    ReactorApp().run()


if __name__ == "__main__":
    main()
