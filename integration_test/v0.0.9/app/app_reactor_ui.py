from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APPS_DIR = ROOT / "apps"
for path in (ROOT, APPS_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from _bootstrap import FONTS_DIR, ensure_repo_root_on_path

ensure_repo_root_on_path()

from core.anyware import AnywareApp
from core.anyware.layout_dsl import LayoutPage, LayoutReloader

from reactor_client import ReactorClient

LAYOUT_PATH = Path(__file__).resolve().parent / "layouts" / "reactor_ui.yaml"


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

        font_ascii = FONTS_DIR / "DEM-MO typeface" / "Mono" / "DEM-MOMono-400.otf"
        font_cjk = FONTS_DIR / "长坂点宋16" / "长坂点宋16.ttf"
        self.app.set_fonts(ascii_path=str(font_ascii), cjk_path=str(font_cjk), cell_w=8, cell_h=16, size_px=16)

        actions = {
            "go_page.status": lambda _b, _ctx, _el: self.app.switch_page("status"),
            "go_page.diagram": lambda _b, _ctx, _el: self.app.switch_page("diagram"),
            "go_page.control": lambda _b, _ctx, _el: self.app.switch_page("control"),
            "go_page.core": lambda _b, _ctx, _el: self.app.switch_page("core"),
        }

        pages = [
            LayoutPage("status", layout=self.layout, actions=actions),
            LayoutPage("diagram", layout=self.layout, actions=actions),
            LayoutPage("control", layout=self.layout, actions=actions),
            LayoutPage("core", layout=self.layout, actions=actions),
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
