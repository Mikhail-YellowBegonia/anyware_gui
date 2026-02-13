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
