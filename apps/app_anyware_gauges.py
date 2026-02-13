import math

import pygame

from _bootstrap import FONTS_DIR, ensure_repo_root_on_path

ensure_repo_root_on_path()

from core.anyware import AnywareApp, ButtonArray, Label, Page


class GaugesPage(Page):
    def __init__(self):
        super().__init__("gauges")
        self.selected_label = "NONE"
        self.channel = "anyware_gauges.sim"
        self.current_value = 0.0

        self.add(Label(gx=2, gy=1, text="ANYWARE GAUGES", color="CRT_Cyan"))
        self.add(Label(gx=2, gy=2, text="ARROWS:navigate  ENTER/SPACE:select  ESC:quit", color="CRT_Cyan"))
        self.add(Label(gx=34, gy=4, text=lambda c: f"FOCUS: {c.get_focus('none')}", color="CRT_Cyan"))
        self.add(Label(gx=34, gy=5, text=lambda _: f"SELECT: {self.selected_label}", color="CRT_Cyan"))
        self.add(Label(gx=6, gy=16, text=lambda _: f"{self.current_value:05.1f}", color="CRT_Cyan"))
        self.add(Label(gx=16, gy=26, text=lambda _: f"{self.current_value:05.1f}", color="CRT_Cyan"))
        self.add(Label(gx=58, gy=10, text="TEXT", color="CRT_Cyan", orientation="vertical", line_step=2))

        self.main_buttons = ButtonArray(
            "main_button_array",
            labels=["ENG", "FUEL", "ELEC", "HYD", "OXY", "APU"],
            gx=34,
            gy=6,
            cols=3,
            rows=2,
            scope="main",
            id_start=1,
            on_select=self._on_button_select,
        )
        self.add(self.main_buttons)

    def on_enter(self, ctx) -> None:
        ctx.set_dynamic_offset(self.channel, 50.0, wrap=100.0)
        first = self.main_buttons.buttons[0] if self.main_buttons.buttons else None
        if first is not None:
            ctx.set_active_focus_scope("main")
            ctx.set_focus(first.button_id)

    def _on_button_select(self, button, ctx) -> None:
        self.selected_label = button.label

    def handle_event(self, event, ctx) -> bool:
        if event.type == pygame.KEYDOWN and ctx.key_to_focus_direction(event.key) is not None:
            ctx.move_focus_by_key(event.key)
            return True
        return super().handle_event(event, ctx)

    def _draw_round_gauge(self, ctx, x_px: float, y_px: float, value: float, *, color: str = "CRT_Cyan"):
        circle_poly = []
        for i in range(0, 360):
            rad = i * math.pi / 180.0
            circle_poly.append((math.cos(rad) * 20.0, math.sin(rad) * 20.0))
        ctx.draw_poly(circle_poly, color, x_px, y_px, filled=False, thickness=1)

        ratio = max(0.0, min(1.0, value / 100.0))
        angle = ratio * 360.0 - 90.0
        needle = [(-2.0, 10.0), (0.0, -22.0), (2.0, 10.0), (0.0, 6.0)]
        theta = math.radians(angle)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        needle_rot = []
        for x, y in needle:
            needle_rot.append((x * cos_t - y * sin_t, x * sin_t + y * cos_t))
        ctx.draw_poly(needle_rot, color, x_px, y_px, filled=False, thickness=1)
        ctx.label(
            int(round(ctx.px(x_px))) - 2,
            int(round(ctx.py(y_px))) + 3,
            color,
            f"{value:05.1f}",
        )

    def _draw_fan_gauge(self, ctx, x_px: float, y_px: float, value: float, *, color: str = "CRT_Cyan"):
        ratio = max(0.0, min(1.0, value / 100.0))
        radius = 28.0
        start_deg = 0
        sweep_deg = 270.0
        fill_deg = sweep_deg * ratio

        def arc_points(sweep):
            pts = []
            end = start_deg + sweep
            for deg in range(int(round(start_deg)), int(round(end)) + 1):
                rad = math.radians(deg)
                pts.append((math.cos(rad) * radius, math.sin(rad) * radius))
            return pts

        total_fan = [(0.0, 0.0)] + arc_points(sweep_deg) + [(0.0, 0.0)]
        filled_fan = [(0.0, 0.0)] + arc_points(fill_deg) + [(0.0, 0.0)]

        ctx.draw_poly(filled_fan, color, x_px, y_px, filled=True, thickness=1)
        ctx.draw_poly(total_fan, color, x_px, y_px, filled=False, thickness=1)
        ctx.label(
            int(round(ctx.px(x_px))) - 2,
            int(round(ctx.py(y_px))) + 3,
            color,
            f"{value:05.1f}",
        )

    def render(self, ctx) -> None:
        value = ctx.step_dynamic_offset(self.channel, speed=0.7, wrap=100.0)
        self.current_value = value

        ctx.draw_box(0, 0, 60, 30, "CRT_Cyan", thickness=2)

        self._draw_round_gauge(ctx, ctx.gx(10), ctx.gy(10), value)
        self._draw_fan_gauge(ctx, ctx.gx(20), ctx.gy(20), value)

        super().render(ctx)
        ctx.draw_focus_frame("blink18", padding=2.0, thickness=1.2)


def main():
    app = AnywareApp(
        title="Anyware Gauges",
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

    font_ascii = FONTS_DIR / "DEM-MO typeface" / "Mono" / "DEM-MOMono-300.otf"
    font_cjk = FONTS_DIR / "wqy-zenhei" / "wqy-zenhei.ttc"
    app.set_fonts(ascii_path=str(font_ascii), cjk_path=str(font_cjk), cell_w=8, cell_h=16, size_px=16)
    app.set_root_page(GaugesPage())
    app.run()


if __name__ == "__main__":
    main()
