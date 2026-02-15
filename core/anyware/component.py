from __future__ import annotations

from typing import Iterable


class Component:
    """Base class for Anyware components."""

    def __init__(self, component_id: str | None = None, *, visible: bool = True, enabled: bool = True):
        self.component_id = component_id
        self.visible = bool(visible)
        self.enabled = bool(enabled)
        self._mounted = False

    def mount(self, ctx) -> None:
        self._mounted = True

    def unmount(self, ctx) -> None:
        self._mounted = False

    def update(self, ctx, dt: float) -> None:
        return None

    def render(self, ctx) -> None:
        return None

    def handle_event(self, event, ctx) -> bool:
        return False

    def focus_ids(self) -> list[str]:
        """Return focus node ids owned by this component (if any)."""
        return []

    @property
    def mounted(self) -> bool:
        return self._mounted


class ComponentGroup(Component):
    """Composite component that forwards lifecycle and events to children."""

    def __init__(self, component_id: str | None = None, *, visible: bool = True, enabled: bool = True):
        super().__init__(component_id, visible=visible, enabled=enabled)
        self.children: list[Component] = []

    def add(self, child: Component) -> Component:
        self.children.append(child)
        return child

    def extend(self, children: Iterable[Component]) -> None:
        self.children.extend(children)

    def remove(self, child: Component) -> bool:
        if child not in self.children:
            return False
        self.children.remove(child)
        return True

    def focus_ids(self) -> list[str]:
        ids: list[str] = []
        for child in self.children:
            ids.extend(child.focus_ids())
        return ids

    def mount(self, ctx) -> None:
        super().mount(ctx)
        for child in self.children:
            if not child.mounted:
                child.mount(ctx)

    def unmount(self, ctx) -> None:
        for child in reversed(self.children):
            if child.mounted:
                child.unmount(ctx)
        super().unmount(ctx)

    def update(self, ctx, dt: float) -> None:
        if not self.enabled:
            return
        for child in self.children:
            if child.enabled:
                child.update(ctx, dt)

    def render(self, ctx) -> None:
        if not self.visible:
            return
        for child in self.children:
            if child.visible:
                child.render(ctx)

    def handle_event(self, event, ctx) -> bool:
        if not self.enabled:
            return False
        for child in reversed(self.children):
            if not child.enabled:
                continue
            if child.handle_event(event, ctx):
                return True
        return False

    def reconcile_children(self, ctx, next_children: Iterable[Component], *, ensure_focus: bool = True) -> None:
        """Replace children using id-based reconciliation (flat list).

        Requirements:
        - Every component must have a unique component_id (stringable).
        - Use this only when dynamic add/remove/replace is needed.
        """
        next_list = list(next_children)
        seen: set[str] = set()
        next_by_id: dict[str, Component] = {}
        for child in next_list:
            cid = child.component_id
            if cid is None:
                raise ValueError("Dynamic reconcile requires component_id on every component.")
            cid = str(cid)
            if cid in seen:
                raise ValueError(f"Duplicate component_id in reconcile: {cid}")
            seen.add(cid)
            next_by_id[cid] = child

        # Unmount removed/replaced children.
        for old in list(self.children):
            oid = old.component_id
            if oid is None:
                if old.mounted:
                    old.unmount(ctx)
                continue
            oid = str(oid)
            new = next_by_id.get(oid)
            if new is None or new is not old:
                if old.mounted:
                    old.unmount(ctx)

        # Apply new list and mount newcomers.
        self.children = next_list
        for child in self.children:
            if not child.mounted:
                child.mount(ctx)

        if ensure_focus:
            focus_ids = self.focus_ids()
            if focus_ids:
                current = ctx.get_focus(None)
                if current not in focus_ids:
                    for fid in focus_ids:
                        if ctx.set_focus(fid):
                            break
