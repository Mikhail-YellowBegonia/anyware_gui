import pygame

from _bootstrap import FONTS_DIR, ensure_repo_root_on_path

ensure_repo_root_on_path()

from core.anyware import AnywareApp, Button, Label, Page, stable_component_id


class DynamicTempPage(Page):
    def __init__(self):
        super().__init__("dynamic_temp")
        self.mode = 0
        self._dirty = True
        self.value = 0

    def _build_components(self):
        if self.mode == 0:
            return [
                Label(label_id="title", gx=2, gy=2, text="DYNAMIC MODE A", color="CRT_Cyan"),
                Label(label_id="hint", gx=2, gy=3, text="T:toggle  ESC:quit", color="CRT_Cyan"),
                Button(
                    "btn_a",
                    "BTN-A",
                    gx=4,
                    gy=6,
                    width_px=80,
                    height_px=20,
                    scope="main",
                ),
            ]
        return [
            Label(label_id="title", gx=2, gy=2, text="DYNAMIC MODE B", color="CRT_Cyan"),
            Label(label_id="hint", gx=2, gy=3, text="T:toggle  ESC:quit", color="CRT_Cyan"),
            Button(
                stable_component_id("btn", seed="b"),
                "BTN-B",
                gx=4,
                gy=6,
                width_px=80,
                height_px=20,
                scope="main",
            ),
        ]

    def on_enter(self, ctx) -> None:
        ctx.set_active_focus_scope("main")
        self.set_components(ctx, self._build_components())

    def handle_event(self, event, ctx) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                self.mode = 1 - self.mode
                self._dirty = True
                return True
            if ctx.key_to_focus_direction(event.key) is not None:
                ctx.move_focus_by_key(event.key)
                return True
        return super().handle_event(event, ctx)

    def update(self, ctx, dt: float) -> None:
        if self._dirty:
            self.set_components(ctx, self._build_components())
            self._dirty = False

    def render(self, ctx) -> None:
        ctx.draw_box(0, 0, 60, 30, "CRT_Cyan", thickness=2)
        super().render(ctx)
        ctx.draw_focus_frame("blink18", padding=2.0, thickness=1.2)


def main():
    app = AnywareApp(
        title="Anyware Dynamic Temp",
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

    app.set_root_page(DynamicTempPage())
    app.run()


if __name__ == "__main__":
    main()
