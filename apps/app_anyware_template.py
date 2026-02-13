import pygame
from _bootstrap import FONTS_DIR, ensure_repo_root_on_path

ensure_repo_root_on_path()

from core.anyware import AnywareApp, Label, Page


class HomePage(Page):
    def __init__(self):
        super().__init__("home")
        self._selected = False
        self.add(Label(gx=2, gy=1, text="ANYWARE TEMPLATE", color="CRT_Cyan"))
        self.add(Label(gx=2, gy=2, text="ARROWS: focus  ENTER/SPACE: toggle  ESC: quit", color="CRT_Cyan"))
        self.add(Label(gx=2, gy=4, text=lambda c: f"FRAME: {c.frame.frame}  DT: {c.frame.dt:.3f}", color="CRT_Cyan"))
        self.add(Label(gx=2, gy=5, text=lambda _: f"SELECTED: {self._selected}", color="CRT_Cyan"))
        self.add(Label(gx=6, gy=9, text="BTN 1", color="CRT_Cyan"))
        self.add(Label(gx=21, gy=9, text="BTN 2", color="CRT_Cyan"))

    def on_enter(self, ctx) -> None:
        gx = ctx.gx(4)
        gy = ctx.gy(8)
        ctx.add_focus_node("demo_btn_1", (gx, gy, 96, 20), nav={"right": "demo_btn_2"}, scope="main")
        ctx.add_focus_node("demo_btn_2", (gx + 120, gy, 96, 20), nav={"left": "demo_btn_1"}, scope="main")
        ctx.set_active_focus_scope("main")
        ctx.set_focus("demo_btn_1")

    def handle_event(self, event, ctx) -> bool:
        if event.type == pygame.KEYDOWN:
            if ctx.key_to_focus_direction(event.key) is not None:
                ctx.move_focus_by_key(event.key)
                return True
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._selected = not self._selected
                return True
        return False

    def render(self, ctx) -> None:
        ctx.draw_box(0, 0, 60, 30, "CRT_Cyan", thickness=2)

        ctx.draw_rect("CRT_Cyan", ctx.gx(4), ctx.gy(8), 96, 20, filled=False, thickness=1)
        ctx.draw_rect("CRT_Cyan", ctx.gx(19), ctx.gy(8), 96, 20, filled=False, thickness=1)
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

    font_ascii = FONTS_DIR / "DEM-MO typeface" / "Mono" / "DEM-MOMono-400.otf"
    font_cjk = FONTS_DIR / "wqy-zenhei" / "wqy-zenhei.ttc"
    app.set_fonts(ascii_path=str(font_ascii), cjk_path=str(font_cjk), cell_w=8, cell_h=16, size_px=16)

    app.set_root_page(HomePage())
    app.run()


if __name__ == "__main__":
    main()
