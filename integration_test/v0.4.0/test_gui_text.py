import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pygame

from core import GUI


def _init_fonts():
    font_ascii = ROOT / "assets" / "fonts" / "DEM-MO typeface" / "Mono" / "DEM-MOMono-300.otf"
    font_cjk = ROOT / "assets" / "fonts" / "wqy-zenhei" / "wqy-zenhei.ttc"
    GUI.set_fonts(ascii_path=str(font_ascii), cjk_path=str(font_cjk), cell_w=8, cell_h=16, size_px=16)


def test_measure_text_cells():
    assert GUI.measure_text_cells("ABC") == (3, 1)
    assert GUI.measure_text_cells("A\nBC") == (2, 2)
    assert GUI.measure_text_cells("A\nBC", line_step=2) == (2, 3)
    assert GUI.measure_text_cells("测") == (2, 1)
    assert GUI.measure_text_cells("A\nB", orientation="vertical") == (2, 1)


def test_draw_text_box_alignment():
    GUI.clear_screen()
    GUI.draw_text_box(0, 0, 5, 1, "CRT_Cyan", "A", align_h="center", align_v="top")
    assert GUI.screen[0][2] == "A"

    GUI.clear_screen()
    GUI.draw_text_box(0, 0, 3, 3, "CRT_Cyan", "A", align_h="left", align_v="center")
    assert GUI.screen[1][0] == "A"


def test_draw_text_box_multiline_and_truncation():
    GUI.clear_screen()
    GUI.draw_text_box(0, 0, 5, 3, "CRT_Cyan", "A\nB", align_h="left")
    assert GUI.screen[0][0] == "A"
    assert GUI.screen[1][0] == "B"

    GUI.clear_screen()
    GUI.draw_text_box(0, 0, 3, 1, "CRT_Cyan", "ABCDE", align_h="left")
    assert "".join(GUI.screen[0][0:3]) == "ABC"


def test_draw_super_text_px():
    GUI.reset_overlays()
    before = len(GUI.super_text_queue)
    ok = GUI.draw_super_text_px(10, 10, "CRT_Cyan", "A", scale=2)
    assert ok is True
    assert len(GUI.super_text_queue) == before + 1

    GUI.reset_overlays()
    ok = GUI.draw_super_text_px(10, 10, "CRT_Cyan", "AB", box_w_px=8)
    assert ok is True
    assert len(GUI.super_text_queue) == 1

    GUI.reset_overlays()
    ok = GUI.draw_super_text_px(10, 10, "CRT_Cyan", "A", mode="5x7")
    assert ok is True
    assert len(GUI.super_text_queue) == 1


def main():
    pygame.init()
    _init_fonts()
    test_measure_text_cells()
    test_draw_text_box_alignment()
    test_draw_text_box_multiline_and_truncation()
    test_draw_super_text_px()
    print("GUI text tests: PASS")


if __name__ == "__main__":
    main()
