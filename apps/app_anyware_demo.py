import math

import pygame

from _bootstrap import FONTS_DIR, ensure_repo_root_on_path

ensure_repo_root_on_path()

from core.anyware import AnywareApp, ButtonArray, Label, Page


class DemoArchivePage(Page):
    def __init__(self):
        super().__init__("demo_archive")
        self.channel = "anyware_demo.sim"
        self.selected = "NONE"
        self.value = 0.0

        self.add(Label(gx=2, gy=1, text="ANYWARE DEMO ARCHIVE", color="CRT_Cyan"))
        self.add(Label(gx=2, gy=2, text="TEMP SHOWCASE OF STABLE COMPONENTS", color="CRT_Cyan"))
        self.add(Label(gx=2, gy=3, text="ARROWS:navigate  ENTER/SPACE:select  ESC:quit", color="CRT_Cyan"))
        self.add(Label(gx=2, gy=5, text=lambda _: f"VALUE: {self.value:05.1f}", color="CRT_Cyan"))
        self.add(Label(gx=24, gy=5, text=lambda _: f"SELECT: {self.selected}", color="CRT_Cyan"))
        self.add(Label(gx=56, gy=8, text="VERT", color="CRT_Cyan", orientation="vertical", line_step=2))

        self.buttons = ButtonArray(
            "archive_buttons",
            labels=["BTN-A", "BTN-B", "BTN-C", "BTN-D"],
            gx=4,
            gy=8,
            cols=2,
            rows=2,
            scope="main",
            id_start=1,
            on_select=self._on_select,
        )
        self.add(self.buttons)

    def on_enter(self, ctx) -> None:
        ctx.set_dynamic_offset(self.channel, 25.0, wrap=100.0)
        first = self.buttons.buttons[0] if self.buttons.buttons else None
        if first is not None:
            ctx.set_active_focus_scope("main")
            ctx.set_focus(first.button_id)

    def _on_select(self, button, ctx) -> None:
        self.selected = button.label

    def handle_event(self, event, ctx) -> bool:
        if event.type == pygame.KEYDOWN and ctx.key_to_focus_direction(event.key) is not None:
            ctx.move_focus_by_key(event.key)
            return True
        return super().handle_event(event, ctx)

    def _draw_arc_gauge(self, ctx, x_px: float, y_px: float, value: float):
        ratio = max(0.0, min(1.0, value / 100.0))
        radius = 24.0
        sweep = 270.0
        fill = sweep * ratio

        def arc_points(sweep_deg):
            points = []
            for deg in range(0, int(round(sweep_deg)) + 1):
                rad = math.radians(deg)
                points.append((math.cos(rad) * radius, math.sin(rad) * radius))
            return points

        total = [(0.0, 0.0)] + arc_points(sweep) + [(0.0, 0.0)]
        filled = [(0.0, 0.0)] + arc_points(fill) + [(0.0, 0.0)]
        ctx.draw_poly(filled, "CRT_Cyan", x_px, y_px, filled=True, thickness=1)
        ctx.draw_poly(total, "CRT_Cyan", x_px, y_px, filled=False, thickness=1)

    def render(self, ctx) -> None:
        self.value = ctx.step_dynamic_offset(self.channel, speed=0.5, wrap=100.0)

        ctx.draw_box(0, 0, 60, 30, "CRT_Cyan", thickness=2)
        self._draw_arc_gauge(ctx, ctx.gx(26), ctx.gy(18), self.value)

        super().render(ctx)
        ctx.draw_focus_frame("blink18", padding=2.0, thickness=1.2)


def main():
    app = AnywareApp(
        title="Anyware Demo Archive",
        clear_color="Black",
        display_defaults={
            "fps": 16,
            "target_fps": 60,
            "window_noframe": False,
            "window_always_on_top": False,
            "window_bg_color_rgb": (8, 12, 14),
        },
        allow_raw_gui=False,
        min_gui_api_level=1,
    )

    font_ascii = FONTS_DIR / "DEM-MO typeface" / "Mono" / "DEM-MOMono-400.otf"
    font_cjk = FONTS_DIR / "wqy-zenhei" / "wqy-zenhei.ttc"
    app.set_fonts(ascii_path=str(font_ascii), cjk_path=str(font_cjk), cell_w=8, cell_h=16, size_px=16)
    app.set_root_page(DemoArchivePage())
    app.run()


if __name__ == "__main__":
    main()
