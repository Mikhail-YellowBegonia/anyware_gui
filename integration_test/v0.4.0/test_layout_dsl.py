import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.anyware.layout_dsl import LayoutReloader, compile_layout, render_layout


class DummyCtx:
    def __init__(self, *, scale=10):
        self.scale = scale
        self.draw_calls = []
        self._focus = None

    def gx(self, value):
        return value * self.scale

    def gy(self, value):
        return value * self.scale

    def grid_to_px(self, gx_value, gy_value, ox=0, oy=0):
        return (self.gx(gx_value) + ox, self.gy(gy_value) + oy)

    def draw_text_box(self, gx, gy, gw, gh, color, text, **kwargs):
        self.draw_calls.append(("text", gx, gy, gw, gh, color, text, kwargs))

    def draw_rect(self, color, x, y, w, h, **kwargs):
        self.draw_calls.append(("rect", color, x, y, w, h, kwargs))

    def draw_box(self, gx, gy, gw, gh, color, **kwargs):
        self.draw_calls.append(("box", gx, gy, gw, gh, color, kwargs))

    def draw_poly(self, vertices, color, x, y, **kwargs):
        self.draw_calls.append(("poly", vertices, color, x, y, kwargs))

    def draw_super_text_px(self, x, y, color, text, **kwargs):
        self.draw_calls.append(("super_text", x, y, color, text, kwargs))

    def get_focus(self, default=None):
        return self._focus if self._focus is not None else default

    def set_focus(self, node_id, *, activate_scope=True):
        self._focus = node_id
        return True


YAML_CONTENT = """
globals:
  layout_mode: false

styles:
  default:
    color: CRT_Cyan
    text_color: CRT_Cyan
  accent:
    color: CRT_Green

pages:
  home:
    elements:
      - id: frame_box
        type: box
        rect: [0, 0, 12, 4]
        color: White
        z_index: 0
      - id: header
        type: text
        rect: [1, 1, 10, 1]
        text: "HELLO"
        z_index: 1
      - id: bound
        type: text
        rect: [1, 2, 10, 1]
        bind: status.value
        z_index: 0
      - id: frame_rect
        type: rect
        rect: [0, 4, 12, 1]
        filled: true
        z_index: 0
      - id: nav_btn
        type: button
        rect: [2, 3, 3, 1]
        label: "OK"
        on_click: do_it
        z_index: 0
      - id: tri
        type: poly
        rect: [0, 0, 0, 0]
        vertices_px: [[0, 0], [2, 0], [1, 2]]
        z_index: 0
      - id: super_demo
        type: super_text
        gx: 3
        gy: 7
        text: "BIG"
        scale: 2
        color: CRT_Yellow
        z_index: 0
      - id: arrow1
        type: arrow
        start_gx: 0
        start_gy: 0
        end_gx: 1
        end_gy: 1
        z_index: 0
    groups:
      - id: g1
        rect: [10, 10, 0, 0]
        style: accent
        elements:
          - id: gtext
            type: text
            rect: [1, 1, 4, 1]
            text: "IN"
            z_index: 2
"""


def _write_yaml(tmp_path: Path) -> Path:
    path = tmp_path / "layout.yaml"
    path.write_text(YAML_CONTENT, encoding="utf-8")
    return path


def test_layout_compile_and_render():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        yaml_path = _write_yaml(tmp_path)
        loader = LayoutReloader(yaml_path)
        assert loader.document is not None

        ctx = DummyCtx()
        actions_called = []

        def do_it(button, ctx, element):
            actions_called.append((button.button_id, element.get("id")))

        bindings = {"status": {"value": 123}}
        plan = compile_layout(ctx, loader.document, "home", actions={"do_it": do_it}, bindings=bindings)

        assert len(plan.components) == 1
        btn = plan.components[0]
        assert btn.button_id == "nav_btn"
        btn.on_select(btn, ctx)
        assert actions_called == [("nav_btn", "nav_btn")]

        z_orders = [item["z_index"] for item in plan.drawables]
        assert z_orders == sorted(z_orders)

        render_layout(ctx, plan, bindings=bindings)
        texts = [call for call in ctx.draw_calls if call[0] == "text"]
        assert any(call[6] == "123" for call in texts)
        supers = [call for call in ctx.draw_calls if call[0] == "super_text"]
        assert any(call[4] == "BIG" for call in supers)

        gtext = [item for item in plan.drawables if item["id"] == "gtext"]
        assert gtext
        assert gtext[0]["gx"] == 11
        assert gtext[0]["gy"] == 11


if __name__ == "__main__":
    test_layout_compile_and_render()
    print("ok")
