import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import GUI
from core.anyware import AnywareApp, Page

FONTS_DIR = ROOT / "assets" / "fonts"
LAYOUT_PATH = ROOT / "apps" / "text_layout_demo_layout.py"
LAYOUT_MODULE_NAME = "text_layout_demo_layout"


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
        self._last_mtime = 0.0
        self._last_check = 0.0
        self.error = None
        self.reload(force=True)

    def reload(self, *, force: bool = False):
        now = time.time()
        if not force and now - self._last_check < self.min_interval_s:
            return
        self._last_check = now
        try:
            mtime = self.path.stat().st_mtime
        except FileNotFoundError:
            self.error = f"Layout file not found: {self.path}"
            return
        if not force and mtime <= self._last_mtime:
            return
        try:
            module = _load_layout_module(self.path)
            self.module = module
            self._last_mtime = mtime
            self.error = None
        except Exception as exc:
            self.error = f"Layout reload failed: {exc}"


class TextLayoutDemo(Page):
    def __init__(self):
        super().__init__("text_layout_demo")
        self._blink = False
        self._last_toggle = 0.0
        self._layout = LayoutReloader(LAYOUT_PATH)

    def update(self, ctx, dt: float) -> None:
        now = time.time()
        if now - self._last_toggle > 0.6:
            self._blink = not self._blink
            self._last_toggle = now
        self._layout.reload()

    def _render_layout_error(self, ctx, message: str):
        ctx.draw_text_box(2, 24, 56, 4, "CRT_Red", message, align_h="left", align_v="top", line_step=1)

    def render(self, ctx) -> None:
        if not self.visible:
            return
        layout = self._layout.module
        if layout is None:
            self._render_layout_error(ctx, self._layout.error or "Layout missing")
            return

        for box in getattr(layout, "TEXT_BOXES", []):
            ctx.draw_text_box(
                box["gx"],
                box["gy"],
                box["gw"],
                box["gh"],
                box["color"],
                box["text"],
                align_h=box.get("align_h", "left"),
                align_v=box.get("align_v", "top"),
                orientation=box.get("orientation", "horizontal"),
                line_step=box.get("line_step", 1),
            )

        for item in getattr(layout, "SUPER_TEXT", []):
            px, py = ctx.grid_to_px(item["gx"], item["gy"])
            ctx.draw_super_text_px(
                px,
                py,
                item["color"],
                item["text"],
                scale=item.get("scale", 1),
                mode=item.get("mode"),
                line_step=item.get("line_step", 1),
            )

        if self._blink and hasattr(layout, "BLINK_SUPER"):
            item = layout.BLINK_SUPER
            px, py = ctx.grid_to_px(item["gx"], item["gy"])
            ctx.draw_super_text_px(
                px,
                py,
                item["color"],
                item["text"],
                scale=item.get("scale", 1),
                mode=item.get("mode"),
                line_step=item.get("line_step", 1),
            )

        if self._layout.error:
            self._render_layout_error(ctx, self._layout.error)


def main():
    import pygame

    pygame.init()

    GUI.set_display_defaults(
        fps=16,
        target_fps=60,
        window_noframe=False,
        window_always_on_top=False,
        window_bg_color_rgb=(8, 12, 14),
    )

    font_ascii = FONTS_DIR / "DEM-MO typeface" / "Mono" / "DEM-MOMono-300.otf"
    font_cjk = FONTS_DIR / "wqy-zenhei" / "wqy-zenhei.ttc"
    GUI.set_fonts(ascii_path=str(font_ascii), cjk_path=str(font_cjk), cell_w=8, cell_h=16, size_px=16)

    app = AnywareApp(title="Anyware Text Layout Demo")
    app.set_root_page(TextLayoutDemo())
    app.run()


if __name__ == "__main__":
    main()
