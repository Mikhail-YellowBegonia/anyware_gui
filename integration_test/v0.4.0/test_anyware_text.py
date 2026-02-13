import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pygame

from core import GUI
from core.anyware.context import AnywareContext
from core.anyware import Button, Label


def _init_fonts():
    font_ascii = ROOT / "assets" / "fonts" / "DEM-MO typeface" / "Mono" / "DEM-MOMono-300.otf"
    font_cjk = ROOT / "assets" / "fonts" / "wqy-zenhei" / "wqy-zenhei.ttc"
    GUI.set_fonts(ascii_path=str(font_ascii), cjk_path=str(font_cjk), cell_w=8, cell_h=16, size_px=16)


def main():
    pygame.init()
    _init_fonts()

    runtime = GUI.create_runtime(min_api_level=1)
    ctx = AnywareContext(runtime)

    assert ctx.grid_to_px(1, 1) == GUI.grid_to_px(1, 1)

    width, height = ctx.measure_text_cells("A\nBC")
    assert (width, height) == (2, 2)

    GUI.clear_screen()
    ctx.draw_text_box(0, 0, 5, 1, "CRT_Cyan", "A", align_h="center")
    assert GUI.screen[0][2] == "A"

    GUI.reset_overlays()
    ok = ctx.draw_super_text_px(12, 20, "CRT_Cyan", "A", scale=2)
    assert ok is True
    assert len(GUI.super_text_queue) == 1

    GUI.clear_screen()
    label = Label(gx=0, gy=0, gw=5, gh=3, text="A", align_h="center", align_v="center")
    label.render(ctx)
    assert GUI.screen[1][2] == "A"

    GUI.clear_screen()
    btn = Button(
        "btn_test",
        "A",
        gx=0,
        gy=0,
        width_px=27,
        height_px=17,
        label_align_h="center",
        label_align_v="center",
        label_padding_gx=0,
        label_padding_gy=0,
        focusable=False,
        pressable=False,
    )
    btn.render(ctx)
    assert GUI.screen[0][1] == "A"

    print("Anyware text tests: PASS")


if __name__ == "__main__":
    main()
