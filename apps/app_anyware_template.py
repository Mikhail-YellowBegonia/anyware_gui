import importlib.util
import sys
import time
from pathlib import Path

import pygame
from _bootstrap import FONTS_DIR, ensure_repo_root_on_path

ensure_repo_root_on_path()

from core import GUI
from core.anyware import AnywareApp, Button, Page, stable_component_id

ROOT = Path(__file__).resolve().parents[1]
LAYOUT_PATH = ROOT / "apps" / "anyware_template_layout.py"
LAYOUT_MODULE_NAME = "anyware_template_layout"


def _load_layout_module(path: Path):
    spec = importlib.util.spec_from_file_location(LAYOUT_MODULE_NAME, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load layout module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[LAYOUT_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


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
            return True
        except Exception as exc:
            self.error = f"Layout reload failed: {exc}"
            return False


class HomePage(Page):
    def __init__(self):
        super().__init__("home")
        self._selected = False
        self._layout = LayoutReloader(LAYOUT_PATH)
        self._focus_scope = "main"

    def _sync_layout_mode(self) -> None:
        layout = self._layout.module
        if layout is None:
            return
        module_mode = getattr(layout, "LAYOUT_MODE", getattr(layout, "layout_mode", True))
        _, file_mode = self._read_layout_mode_file()
        mode = bool(module_mode)
        if file_mode is not None:
            mode = bool(file_mode)
        GUI.set_layout_mode(mode)

    def _read_layout_mode_file(self):
        try:
            data = LAYOUT_PATH.read_text(encoding="utf-8", errors="ignore")
            raw = data.splitlines()
        except Exception:
            return None, None
        for line in raw:
            stripped = line.strip()
            lower = stripped.lower()
            if lower.startswith("layout_mode"):
                value = None
                if "=" in stripped:
                    rhs = lower.split("=", 1)[1].strip()
                    if rhs.startswith("true"):
                        value = True
                    elif rhs.startswith("false"):
                        value = False
                return stripped, value
        return None, None

    def _build_components(self, ctx, layout, scope: str):
        buttons = list(getattr(layout, "BUTTONS", []))
        comps = []
        for idx, btn in enumerate(buttons):
            bid = str(btn.get("id") or stable_component_id("btn", seed=idx))
            label = btn.get("label") or btn.get("text") or bid
            gx = btn.get("gx", 0)
            gy = btn.get("gy", 0)
            gw = btn.get("gw", 1)
            gh = btn.get("gh", 1)
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
                    label_align_h=btn.get("label_align_h", "center"),
                    label_align_v=btn.get("label_align_v", "center"),
                    label_orientation=btn.get("label_orientation", "horizontal"),
                    label_line_step=btn.get("label_line_step", 1),
                    on_select=self._on_button_select,
                )
            )
        return comps

    def _sync_components(self, ctx) -> None:
        layout = self._layout.module
        if layout is None:
            return
        scope = str(getattr(layout, "FOCUS_SCOPE", "main"))
        self._focus_scope = scope
        ctx.set_active_focus_scope(scope)
        components = self._build_components(ctx, layout, scope)
        self.set_components(ctx, components)

    def _grid_rect_px(self, ctx, gx: float, gy: float, gw: float, gh: float):
        x1 = ctx.gx(gx)
        y1 = ctx.gy(gy)
        x2 = ctx.gx(gx + gw)
        y2 = ctx.gy(gy + gh)
        return (x1, y1, x2 - x1, y2 - y1)

    def on_enter(self, ctx) -> None:
        self._sync_layout_mode()
        self._sync_components(ctx)

    def update(self, ctx, dt: float) -> None:
        if self._layout.reload():
            self._sync_layout_mode()
            self._sync_components(ctx)

    def handle_event(self, event, ctx) -> bool:
        if event.type == pygame.KEYDOWN:
            if ctx.key_to_focus_direction(event.key) is not None:
                ctx.move_focus_by_key(event.key)
                return True
        return super().handle_event(event, ctx)

    def _on_button_select(self, button, ctx) -> None:
        self._selected = button.label

    def _render_layout_error(self, ctx, message: str):
        ctx.draw_text_box(2, 24, 56, 4, "CRT_Red", message, align_h="left", align_v="top", line_step=1)

    def render(self, ctx) -> None:
        ctx.draw_box(0, 0, 60, 30, "CRT_Cyan", thickness=2)

        layout = self._layout.module
        if layout is None:
            self._render_layout_error(ctx, self._layout.error or "Layout missing")
            return

        text_map = {
            "title": "ANYWARE TEMPLATE",
            "hint": "ARROWS: focus  ENTER/SPACE: toggle  ESC: quit",
            "frame": f"FRAME: {ctx.frame.frame}  DT: {ctx.frame.dt:.3f}",
            "selected": f"SELECTED: {self._selected}",
        }

        for rect in getattr(layout, "RECTS", []):
            x, y, w, h = self._grid_rect_px(ctx, rect["gx"], rect["gy"], rect["gw"], rect["gh"])
            ctx.draw_rect(
                rect.get("color", "CRT_Cyan"),
                x,
                y,
                w,
                h,
                filled=rect.get("filled", False),
                thickness=rect.get("thickness", 1),
            )

        for box in getattr(layout, "TEXT_BOXES", []):
            text = box.get("text")
            if text is None:
                text = text_map.get(box.get("id"), "")
            ctx.draw_text_box(
                box["gx"],
                box["gy"],
                box["gw"],
                box["gh"],
                box.get("color", "CRT_Cyan"),
                text,
                align_h=box.get("align_h", "left"),
                align_v=box.get("align_v", "top"),
                orientation=box.get("orientation", "horizontal"),
                line_step=box.get("line_step", 1),
            )

        super().render(ctx)

        if self._layout.error:
            self._render_layout_error(ctx, self._layout.error)

        ctx.draw_focus_frame("blink18", padding=2.0, thickness=1.2)


def main():
    app = AnywareApp(
        title="Anyware Template",
        clear_color="Black",
        display_defaults={
            "fps": 16,
            "target_fps": 60,
            "window_noframe": False,
            "window_always_on_top": False,
            "window_bg_color_rgb": (8, 12, 14),
        },
        allow_raw_gui=False,
    )

    font_ascii = FONTS_DIR / "DEM-MO typeface" / "Mono" / "DEM-MOMono-300.otf"
    font_cjk = FONTS_DIR / "wqy-zenhei" / "wqy-zenhei.ttc"
    app.set_fonts(ascii_path=str(font_ascii), cjk_path=str(font_cjk), cell_w=8, cell_h=16, size_px=16)

    app.set_root_page(HomePage())
    app.run()


if __name__ == "__main__":
    main()
