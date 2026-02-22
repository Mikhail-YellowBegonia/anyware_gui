import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import GUI
from core.anyware import AnywareApp, LayoutPage, LayoutReloader

FONTS_DIR = ROOT / "assets" / "fonts"
LAYOUT_PATH = ROOT / "apps" / "layouts" / "text_layout_demo_layout.yaml"


class TextLayoutDemo(LayoutPage):
    def __init__(self, layout: LayoutReloader):
        self._blink = False
        self._last_toggle = 0.0
        self._layout = layout
        bindings = {
            "blink_text": lambda _ctx: "BLINK" if self._blink else "",
        }
        super().__init__("text_layout_demo", layout=layout, bindings=bindings)

    def update(self, ctx, dt: float) -> None:
        now = time.time()
        if now - self._last_toggle > 0.6:
            self._blink = not self._blink
            self._last_toggle = now
        super().update(ctx, dt)


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
    layout = LayoutReloader(LAYOUT_PATH)
    app.set_root_page(TextLayoutDemo(layout))
    app.run()


if __name__ == "__main__":
    main()
