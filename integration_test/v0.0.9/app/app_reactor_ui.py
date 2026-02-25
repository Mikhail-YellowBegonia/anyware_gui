from __future__ import annotations

import atexit
import math
import subprocess
import sys
import time
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
from core.anyware.instruments import DialGauge

from reactor_client import ReactorClient

LAYOUT_PATH = Path(__file__).resolve().parent / "layouts" / "reactor_ui.yaml"


class DiagramPage(LayoutPage):
    def __init__(
        self,
        page_id: str,
        *,
        layout: LayoutReloader,
        actions: dict | None = None,
        bindings: dict | None = None,
    ):
        super().__init__(page_id, layout=layout, actions=actions, bindings=bindings)
        self._gauge = DialGauge(
            gauge_id="demo_fill_gauge",
            center_gx=24,
            center_gy=34,
            radius_px=24,
            value=self._gauge_value,
            min_value=0.0,
            max_value=100.0,
            start_angle_deg=-135.0,
            end_angle_deg=135.0,
            style="fill",
            color="Solar_Special",
            fill_steps=24,
            center_dot_px=3.0,
        )

    def _gauge_value(self, _ctx):
        return 50.0 + 50.0 * math.sin(time.time() * 0.8)

    def _sync_components(self, ctx) -> None:
        super()._sync_components(ctx)
        if self._plan is None:
            return
        components = list(self._plan.components)
        components.append(self._gauge)
        self.set_components(ctx, components)


class ReactorApp:
    def __init__(self):
        self.layout = LayoutReloader(LAYOUT_PATH)
        self.client = ReactorClient()
        self._backend_proc: subprocess.Popen | None = None
        self._net_info = {
            "port": self.client.port,
            "latency_ms": None,
            "comms_on": False,
        }
        self._ensure_backend()

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

        font_ascii = FONTS_DIR / "长坂点宋16" / "长坂点宋16.ttf"
        font_cjk = FONTS_DIR / "长坂点宋16" / "长坂点宋16.ttf"
        self.app.set_fonts(ascii_path=str(font_ascii), cjk_path=str(font_cjk), cell_w=8, cell_h=16, size_px=16)

        actions = {
            "go_page.status": lambda _b, _ctx, _el: self.app.switch_page("status"),
            "go_page.diagram": lambda _b, _ctx, _el: self.app.switch_page("diagram"),
            "go_page.control": lambda _b, _ctx, _el: self.app.switch_page("control"),
            "go_page.core": lambda _b, _ctx, _el: self.app.switch_page("core"),
        }
        bindings = {
            "net": {
                "info": lambda _ctx: self._net_info_text(),
                "comms_on": lambda _ctx: self._net_info.get("comms_on", False),
                "comms_color": lambda _ctx: "Solar_Special"
                if self._net_info.get("comms_on", False)
                else "Solar_Default",
            }
        }

        pages = [
            LayoutPage("status", layout=self.layout, actions=actions, bindings=bindings),
            DiagramPage("diagram", layout=self.layout, actions=actions, bindings=bindings),
            LayoutPage("control", layout=self.layout, actions=actions, bindings=bindings),
            LayoutPage("core", layout=self.layout, actions=actions, bindings=bindings),
        ]
        self.app.register_pages(pages)
        self.app.set_root_page(pages[0])

    def _net_info_text(self) -> str:
        port = self._net_info.get("port")
        latency = self._net_info.get("latency_ms")
        latency_text = "--ms" if latency is None else f"{int(round(latency))}ms"
        return f"PORT {port}\nLATENCY {latency_text}"

    def _ensure_backend(self) -> None:
        if self.client.health_check():
            return
        backend_path = Path(__file__).resolve().parents[1] / "reactor_backend.py"
        if not backend_path.exists():
            return
        cmd = [
            sys.executable,
            str(backend_path),
            "--host",
            "127.0.0.1",
            "--port",
            str(self.client.port),
        ]
        try:
            self._backend_proc = subprocess.Popen(cmd)
        except Exception:
            self._backend_proc = None
            return
        atexit.register(self._stop_backend)
        for _ in range(15):
            time.sleep(0.2)
            if self.client.health_check():
                return

    def _stop_backend(self) -> None:
        if self._backend_proc is None:
            return
        if self._backend_proc.poll() is None:
            self._backend_proc.terminate()
        self._backend_proc = None

    def run(self) -> None:
        original_update = self.app.page_stack.update

        def _update(ctx, dt: float) -> None:
            self.client.poll_and_log()
            comms_on = self.client.comms_ok()
            self._net_info["comms_on"] = comms_on
            self._net_info["latency_ms"] = self.client.last_latency_ms if comms_on else None
            original_update(ctx, dt)

        self.app.page_stack.update = _update
        self.app.run()


def main() -> None:
    ReactorApp().run()


if __name__ == "__main__":
    main()
