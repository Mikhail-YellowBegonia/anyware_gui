import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.anyware.component import Component, ComponentGroup


class DummyCtx:
    def __init__(self):
        self.focus = None

    def get_focus(self, default=None):
        return self.focus if self.focus is not None else default

    def set_focus(self, node_id, *, activate_scope=True):
        self.focus = node_id
        return True


class Probe(Component):
    def __init__(self, cid, *, focusable=False):
        super().__init__(component_id=cid, visible=True, enabled=True)
        self.mount_count = 0
        self.unmount_count = 0
        self._focusable = focusable

    def mount(self, ctx):
        self.mount_count += 1
        super().mount(ctx)

    def unmount(self, ctx):
        self.unmount_count += 1
        super().unmount(ctx)

    def focus_ids(self):
        if not self._focusable:
            return []
        return [str(self.component_id)]


def test_reconcile_mount_unmount_and_replace():
    ctx = DummyCtx()
    group = ComponentGroup("root")

    a = Probe("a", focusable=True)
    b = Probe("b", focusable=True)
    c = Probe("c", focusable=True)

    group.reconcile_children(ctx, [a, b])
    assert a.mount_count == 1
    assert b.mount_count == 1
    assert a.unmount_count == 0

    ctx.focus = "a"
    group.reconcile_children(ctx, [b, c])
    assert a.unmount_count == 1
    assert b.mount_count == 1
    assert c.mount_count == 1
    assert ctx.focus in ("b", "c")


def test_reconcile_requires_unique_ids():
    ctx = DummyCtx()
    group = ComponentGroup("root")
    a1 = Probe("dup")
    a2 = Probe("dup")
    try:
        group.reconcile_children(ctx, [a1, a2])
        assert False, "Expected duplicate id error"
    except ValueError:
        pass


if __name__ == "__main__":
    test_reconcile_mount_unmount_and_replace()
    test_reconcile_requires_unique_ids()
    print("ok")

