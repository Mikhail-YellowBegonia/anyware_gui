from __future__ import annotations

from .component import ComponentGroup


class Page(ComponentGroup):
    """A page is a top-level composition unit in Anyware."""

    def __init__(self, page_id: str):
        super().__init__(component_id=page_id, visible=True, enabled=True)
        self.page_id = page_id

    def on_enter(self, ctx) -> None:
        return None

    def on_exit(self, ctx) -> None:
        return None


class PageStack:
    """Browser-like page stack with push/pop/replace."""

    def __init__(self):
        self._stack: list[Page] = []

    def current(self) -> Page | None:
        if not self._stack:
            return None
        return self._stack[-1]

    def push(self, page: Page, ctx) -> Page:
        current = self.current()
        if current is not None:
            current.on_exit(ctx)
            if current.mounted:
                current.unmount(ctx)
        self._stack.append(page)
        if not page.mounted:
            page.mount(ctx)
        page.on_enter(ctx)
        return page

    def pop(self, ctx) -> Page | None:
        if not self._stack:
            return None
        top = self._stack.pop()
        top.on_exit(ctx)
        if top.mounted:
            top.unmount(ctx)
        new_top = self.current()
        if new_top is not None:
            if not new_top.mounted:
                new_top.mount(ctx)
            new_top.on_enter(ctx)
        return top

    def replace(self, page: Page, ctx) -> Page:
        if self._stack:
            old = self._stack.pop()
            old.on_exit(ctx)
            if old.mounted:
                old.unmount(ctx)
        self._stack.append(page)
        if not page.mounted:
            page.mount(ctx)
        page.on_enter(ctx)
        return page

    def clear(self, ctx) -> None:
        while self._stack:
            page = self._stack.pop()
            page.on_exit(ctx)
            if page.mounted:
                page.unmount(ctx)

    def handle_event(self, event, ctx) -> bool:
        top = self.current()
        if top is None or not top.enabled:
            return False
        return top.handle_event(event, ctx)

    def update(self, ctx, dt: float) -> None:
        top = self.current()
        if top is None or not top.enabled:
            return
        top.update(ctx, dt)

    def render(self, ctx) -> None:
        top = self.current()
        if top is None or not top.visible:
            return
        top.render(ctx)
