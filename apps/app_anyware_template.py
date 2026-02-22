from pathlib import Path

from _bootstrap import FONTS_DIR, ensure_repo_root_on_path

ensure_repo_root_on_path()

from core.anyware import AnywareApp, LayoutPage, LayoutReloader

ROOT = Path(__file__).resolve().parents[1]
LAYOUT_PATH = ROOT / "apps" / "layouts" / "anyware_template_layout.yaml"


class HomePage(LayoutPage):
    def __init__(self, layout: LayoutReloader):
        self._selected = ""
        self._layout = layout
        actions = {
            "select_button": self._on_button_select,
        }
        bindings = {
            "frame": lambda ctx: f"FRAME: {ctx.frame.frame}  DT: {ctx.frame.dt:.3f}",
            "selected": lambda ctx: f"SELECTED: {self._selected}",
        }
        super().__init__("home", layout=layout, actions=actions, bindings=bindings)

    def _on_button_select(self, button, ctx, _element=None) -> None:
        self._selected = button.label

    def render(self, ctx) -> None:
        super().render(ctx)
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

    layout = LayoutReloader(LAYOUT_PATH)
    app.set_root_page(HomePage(layout))
    app.run()


if __name__ == "__main__":
    main()
