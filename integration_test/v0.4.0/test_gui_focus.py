import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import GUI


def _reset():
    GUI.clear_focus_nodes()
    GUI.set_active_focus_scope("default")


def test_focus_score_prefers_low_weighted_secondary():
    _reset()
    GUI.add_focus_node("cur", (0, 0, 10, 10))
    GUI.add_focus_node("a", (30, 0, 10, 10))   # primary 30, secondary 0
    GUI.add_focus_node("b", (20, 12, 10, 10))  # primary 20, secondary 12
    GUI.set_focus("cur")
    # With score = primary + 2*secondary, "a" should win (30 vs 44)
    assert GUI.move_focus("right") == "a"


def test_focus_score_keeps_half_plane_filter_with_fallback():
    _reset()
    GUI.add_focus_node("cur", (0, 0, 10, 10))
    GUI.add_focus_node("left", (-30, 0, 10, 10))
    GUI.set_focus("cur")
    # No right-side candidates; fallback should move to next in order
    assert GUI.move_focus("right") == "left"
