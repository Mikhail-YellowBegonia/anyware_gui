from __future__ import annotations

import time

import pygame

from core import GUI
from .context import AnywareContext
from .page import Page, PageStack


class AnywareApp:
    """Anyware application runtime with page stack."""

    def __init__(
        self,
        *,
        title: str = "Anyware App",
        clear_color="Black",
        display_defaults: dict | None = None,
        allow_raw_gui: bool = False,
        output_mode: str = "pygame",
        logic_fps: float | None = None,
        present_fps: float | None = None,
        frame_exporter=None,
        min_gui_api_level: int = 1,
        quit_on_escape: bool = True,
    ):
        pygame.init()
        if display_defaults:
            GUI.set_display_defaults(**display_defaults)

        self.runtime = GUI.create_runtime(min_api_level=min_gui_api_level)
        self.ctx = AnywareContext(self.runtime, allow_raw_gui=allow_raw_gui)
        self.page_stack = PageStack()
        self.page_registry: dict[str, Page] = {}

        # Pre-adaptation output config placeholders (no behavior change yet).
        self.output_mode = str(output_mode)
        self.logic_fps = None if logic_fps is None else float(logic_fps)
        self.present_fps = None if present_fps is None else float(present_fps)
        self.frame_exporter = frame_exporter
        self._present_to_screen = self.output_mode == "pygame"
        self._use_offscreen = (self.output_mode != "pygame") or (self.frame_exporter is not None)
        self._display_warning_emitted = False

        self._init_render_surfaces(title=title)

        self.clear_color = clear_color
        self.quit_on_escape = bool(quit_on_escape)
        self.clock = pygame.time.Clock()
        self.running = False
        self._last_logic_time = time.time()

    def _init_render_surfaces(self, *, title: str | None = None) -> None:
        self.screen_surf = pygame.display.set_mode(GUI.get_window_size_px(), GUI.get_window_flags())
        if title is not None:
            pygame.display.set_caption(title)
        if GUI.window_always_on_top:
            GUI._set_window_always_on_top(True)
        self._display_surface_id = id(self.screen_surf)
        self.offscreen_surf = pygame.Surface(GUI.get_window_size_px()) if self._use_offscreen else None
        self._render_surf = self.offscreen_surf if self.offscreen_surf is not None else self.screen_surf

    def set_fonts(self, *, ascii_path=None, cjk_path=None, cell_w=None, cell_h=None, size_px=None):
        GUI.set_fonts(
            ascii_path=ascii_path,
            cjk_path=cjk_path,
            cell_w=cell_w,
            cell_h=cell_h,
            size_px=size_px,
        )
        self._init_render_surfaces()
        return self

    def set_root_page(self, page: Page):
        self.page_registry[page.page_id] = page
        return self.page_stack.replace(page, self.ctx)

    def register_pages(self, pages: list[Page]):
        for page in pages:
            self.page_registry[page.page_id] = page
        return self

    def switch_page(self, page_id: str):
        page = self.page_registry.get(page_id)
        if page is None:
            return None
        return self.page_stack.replace(page, self.ctx)

    def push_page(self, page: Page):
        self.page_registry[page.page_id] = page
        return self.page_stack.push(page, self.ctx)

    def pop_page(self):
        return self.page_stack.pop(self.ctx)

    def stop(self):
        self.running = False

    def _handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return True
        if self.quit_on_escape and event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.running = False
            return True
        return self.page_stack.handle_event(event, self.ctx)

    def _warn_if_display_replaced(self) -> None:
        if not self._present_to_screen:
            return
        current = pygame.display.get_surface()
        if current is None:
            return
        if current is not self.screen_surf and not self._display_warning_emitted:
            print(
                "AnywareApp warning: display surface replaced outside AnywareApp. "
                "Avoid calling pygame.display.set_mode() in Anyware apps."
            )
            self._display_warning_emitted = True

    def run(self):
        self.running = True
        self._last_logic_time = time.time()
        while self.running:
            for event in pygame.event.get():
                self._handle_event(event)

            now = time.time()
            logic_interval = 1.0 / max(1, GUI.fps)
            if now - self._last_logic_time >= logic_interval:
                self._warn_if_display_replaced()
                dt = now - self._last_logic_time
                frame = self.runtime.begin_frame(clear_color=self.clear_color)
                self.ctx.set_frame_info(frame=frame, dt=dt)

                self.page_stack.update(self.ctx, dt)
                self.page_stack.render(self.ctx)

                self.runtime.finish_frame(self._render_surf)
                if self.frame_exporter is not None:
                    self.frame_exporter(self._render_surf, self.ctx)
                if self._present_to_screen and self.offscreen_surf is not None:
                    self.screen_surf.blit(self.offscreen_surf, (0, 0))
                self._last_logic_time = now

            if self._present_to_screen:
                pygame.display.flip()
            self.clock.tick(max(1, GUI.target_fps))

        self.page_stack.clear(self.ctx)
        pygame.quit()
