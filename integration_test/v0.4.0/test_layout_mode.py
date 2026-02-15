import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import GUI


class DummySurface:
    def __init__(self):
        self.fills = []

    def fill(self, color, rect=None):
        self.fills.append((tuple(color), rect))


def test_layout_mode_colors_override():
    GUI.set_layout_mode(False)
    assert GUI.get_color_rgb("White") == (255, 255, 255)

    GUI.set_layout_mode(True)
    assert GUI.get_color_rgb("White") == (130, 159, 23)
    assert GUI.get_layout_mode() is True
    colors = GUI.get_layout_mode_colors()
    assert colors["bg_rgb"] == (200, 190, 180)
    assert colors["fg_rgb"] == (130, 159, 23)


def test_layout_mode_background_override():
    GUI.set_layout_mode(False)
    GUI.set_display_defaults(window_bg_color_rgb=(1, 2, 3))
    rt = GUI.create_runtime()
    rt.begin_frame()
    GUI.render(GUI.screen, GUI.screen_color)
    s1 = DummySurface()
    GUI.draw_to_surface(s1)
    assert s1.fills and s1.fills[0][0] == (1, 2, 3)

    GUI.set_layout_mode(True)
    rt.begin_frame()
    GUI.render(GUI.screen, GUI.screen_color)
    s2 = DummySurface()
    GUI.draw_to_surface(s2)
    assert s2.fills and s2.fills[0][0] == (200, 190, 180)


if __name__ == "__main__":
    # Minimal standalone run (without pytest).
    test_layout_mode_colors_override()
    test_layout_mode_background_override()
    print("ok")
