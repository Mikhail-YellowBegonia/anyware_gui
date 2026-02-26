import math
from datetime import datetime
from pathlib import Path

import pygame

from _bootstrap import FONTS_DIR, ensure_repo_root_on_path

ensure_repo_root_on_path()

from core.anyware import (
    AnywareApp,
    Button,
    ButtonArray,
    CheckboxMenu,
    DialGauge,
    Label,
    LLMPage,
    MeterBar,
    Page,
    SegmentDisplay,
    ValueText,
    stable_component_id,
)
from core.anyware.nonstandard_llm.middleware.dispatcher import ToolDispatcher
from core.anyware.nonstandard_llm.middleware.registry import ToolRegistry
from core.anyware.nonstandard_llm.middleware.types import ToolResult, ToolSpec

_PROMPTS_DIR = Path(__file__).resolve().parents[1] / "core" / "anyware" / "nonstandard_llm" / "prompts"


def _read_prompt(name: str) -> str:
    path = _PROMPTS_DIR / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _build_system_prompt() -> str:
    parts = []
    for name in ("system.txt", "tools_info.txt"):
        content = _read_prompt(name)
        if content:
            parts.append(content)
    return "\n\n".join(parts)


def _build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()

    def _get_time(args: dict[str, object]) -> ToolResult:
        fmt = args.get("format")
        fmt_str = fmt if isinstance(fmt, str) and fmt else "%Y-%m-%d %H:%M:%S"
        now = datetime.now().strftime(fmt_str)
        return ToolResult.success(now, data={"timestamp": now})

    registry.register(
        ToolSpec(
            name="get_time",
            description="Return current local time.",
            args_schema={"required": [], "properties": {"format": {"type": "string"}}},
            handler=_get_time,
        )
    )
    return registry


class DemoArchivePage(Page):
    def __init__(self, app: AnywareApp, gauges_page: "GaugesPage", dynamic_page: "DynamicPage", llm_page: "LLMPage"):
        super().__init__("demo_archive")
        self._app = app
        self._gauges_page = gauges_page
        self._dynamic_page = dynamic_page
        self._llm_page = llm_page
        self.channel = "anyware_demo.sim"
        self.selected = "NONE"
        self.value = 0.0

        self.add(Label(gx=2, gy=1, text="ANYWARE DEMO ARCHIVE", color="CRT_Cyan"))
        self.add(Label(gx=2, gy=2, text="TEMP SHOWCASE OF STABLE COMPONENTS", color="CRT_Cyan"))
        self.add(Label(gx=2, gy=3, text="ARROWS:navigate  ENTER/SPACE:select  G:gauges  D:dynamic  L:llm  ESC:quit", color="CRT_Cyan"))
        self.add(ValueText(gx=2, gy=5, label="VALUE", value=lambda _: self.value, fmt="{:05.1f}", color="CRT_Cyan"))
        self.add(ValueText(gx=24, gy=5, label="SELECT", value=lambda _: self.selected, color="CRT_Cyan"))
        self.add(Label(gx=56, gy=8, text="VERT", color="CRT_Cyan", orientation="vertical", line_step=2))

        self.add(
            MeterBar(
                gx=2,
                gy=8,
                width_px=140,
                height_px=10,
                value=lambda _: self.value,
                min_value=0,
                max_value=100,
                mode="bar",
                color="CRT_Cyan",
                empty_color="CRT_BlueDark",
            )
        )
        self.add(
            MeterBar(
                gx=2,
                gy=10,
                width_px=140,
                height_px=10,
                value=lambda _: self.value,
                min_value=0,
                max_value=100,
                mode="segments",
                segments=8,
                color="CRT_Cyan",
                empty_color="CRT_BlueDark",
            )
        )
        self.add(
            DialGauge(
                center_gx=26,
                center_gy=18,
                radius_px=24,
                value=lambda _: self.value,
                min_value=0,
                max_value=100,
                start_angle_deg=-135,
                end_angle_deg=135,
                style="both",
                color="CRT_Cyan",
            )
        )
        self.add(
            Button(
                "status_light",
                "STATUS",
                gx=44,
                gy=4,
                width_px=70,
                height_px=20,
                pressable=False,
                focusable=False,
                status=lambda *_: self._status(),
                status_color_map={"ok": "CRT_Green", "warn": "CRT_Yellow", "fail": "CRT_Red"},
            )
        )
        self.add(
            SegmentDisplay(
                gx=2,
                gy=24,
                text=lambda _: f"{self.value:05.1f}",
                digits=6,
                on_color="CRT_Cyan",
                off_color="CRT_BlueDark",
            )
        )
        self.mode_menu = CheckboxMenu(
            "mode_menu",
            "CTRL",
            states=["手动", "自动", "锁定"],
            gx=4,
            gy=20,
            width_px=120,
            height_px=20,
            scope="main",
            on_change=self._on_mode_change,
        )
        self.add(self.mode_menu)

        self.buttons = ButtonArray(
            "archive_buttons",
            labels=["BTN-A", "BTN-B", "BTN-C", "BTN-D"],
            gx=4,
            gy=8,
            cols=2,
            rows=2,
            scope="main",
            id_start=1,
            on_select=self._on_select,
        )
        self.add(self.buttons)

    def on_enter(self, ctx) -> None:
        ctx.set_dynamic_offset(self.channel, 25.0, wrap=100.0)
        first = self.buttons.buttons[0] if self.buttons.buttons else None
        if first is not None:
            ctx.set_active_focus_scope("main")
            ctx.set_focus(first.button_id)

    def _on_select(self, button, ctx) -> None:
        self.selected = button.label
    
    def _on_mode_change(self, menu, ctx) -> None:
        self.selected = f"{menu.base_label}:{menu.get_value()}"

    def _status(self) -> str:
        if self.value < 40:
            return "ok"
        if self.value < 70:
            return "warn"
        return "fail"

    def handle_event(self, event, ctx) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                self._app.push_page(self._gauges_page)
                return True
            if event.key == pygame.K_d:
                self._app.push_page(self._dynamic_page)
                return True
            if event.key == pygame.K_l:
                self._app.push_page(self._llm_page)
                return True
            if ctx.key_to_focus_direction(event.key) is not None:
                ctx.move_focus_by_key(event.key)
                return True
        return super().handle_event(event, ctx)

    def render(self, ctx) -> None:
        self.value = ctx.step_dynamic_offset(self.channel, speed=0.5, wrap=100.0)

        ctx.draw_box(0, 0, 60, 30, "CRT_Cyan", thickness=2)

        super().render(ctx)
        ctx.draw_focus_frame("blink18", padding=2.0, thickness=1.2)


class GaugesPage(Page):
    def __init__(self, app: AnywareApp):
        super().__init__("gauges")
        self._app = app
        self.selected_label = "NONE"
        self.channel = "anyware_gauges.sim"
        self.current_value = 0.0

        self.add(Label(gx=2, gy=1, text="ANYWARE GAUGES", color="CRT_Cyan"))
        self.add(Label(gx=2, gy=2, text="ARROWS:navigate  ENTER/SPACE:select  CTRL+H:back  ESC:quit", color="CRT_Cyan"))
        self.add(Label(gx=34, gy=4, text=lambda c: f"FOCUS: {c.get_focus('none')}", color="CRT_Cyan"))
        self.add(Label(gx=34, gy=5, text=lambda _: f"SELECT: {self.selected_label}", color="CRT_Cyan"))
        self.add(Label(gx=6, gy=16, text=lambda _: f"{self.current_value:05.1f}", color="CRT_Cyan"))
        self.add(Label(gx=16, gy=26, text=lambda _: f"{self.current_value:05.1f}", color="CRT_Cyan"))
        self.add(Label(gx=58, gy=10, text="TEXT", color="CRT_Cyan", orientation="vertical", line_step=2))

        self.main_buttons = ButtonArray(
            "main_button_array",
            labels=["ENG", "FUEL", "ELEC", "HYD", "OXY", "APU"],
            gx=34,
            gy=6,
            cols=3,
            rows=2,
            scope="main",
            id_start=1,
            on_select=self._on_button_select,
        )
        self.add(self.main_buttons)

    def on_enter(self, ctx) -> None:
        ctx.set_dynamic_offset(self.channel, 50.0, wrap=100.0)
        first = self.main_buttons.buttons[0] if self.main_buttons.buttons else None
        if first is not None:
            ctx.set_active_focus_scope("main")
            ctx.set_focus(first.button_id)

    def _on_button_select(self, button, ctx) -> None:
        self.selected_label = button.label

    def handle_event(self, event, ctx) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_h:
                self._app.pop_page()
                return True
            if ctx.key_to_focus_direction(event.key) is not None:
                ctx.move_focus_by_key(event.key)
                return True
        return super().handle_event(event, ctx)

    def _draw_round_gauge(self, ctx, x_px: float, y_px: float, value: float, *, color: str = "CRT_Cyan"):
        circle_poly = []
        for i in range(0, 360):
            rad = i * math.pi / 180.0
            circle_poly.append((math.cos(rad) * 20.0, math.sin(rad) * 20.0))
        ctx.draw_poly(circle_poly, color, x_px, y_px, filled=False, thickness=1)

        ratio = max(0.0, min(1.0, value / 100.0))
        angle = ratio * 360.0 - 90.0
        needle = [(-2.0, 10.0), (0.0, -22.0), (2.0, 10.0), (0.0, 6.0)]
        theta = math.radians(angle)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        needle_rot = []
        for x, y in needle:
            needle_rot.append((x * cos_t - y * sin_t, x * sin_t + y * cos_t))
        ctx.draw_poly(needle_rot, color, x_px, y_px, filled=False, thickness=1)
        ctx.label(
            int(round(ctx.px(x_px))) - 2,
            int(round(ctx.py(y_px))) + 3,
            color,
            f"{value:05.1f}",
        )

    def _draw_fan_gauge(self, ctx, x_px: float, y_px: float, value: float, *, color: str = "CRT_Cyan"):
        ratio = max(0.0, min(1.0, value / 100.0))
        radius = 28.0
        start_deg = 0
        sweep_deg = 270.0
        fill_deg = sweep_deg * ratio

        def arc_points(sweep):
            pts = []
            end = start_deg + sweep
            for deg in range(int(round(start_deg)), int(round(end)) + 1):
                rad = math.radians(deg)
                pts.append((math.cos(rad) * radius, math.sin(rad) * radius))
            return pts

        total_fan = [(0.0, 0.0)] + arc_points(sweep_deg) + [(0.0, 0.0)]
        filled_fan = [(0.0, 0.0)] + arc_points(fill_deg) + [(0.0, 0.0)]

        ctx.draw_poly(filled_fan, color, x_px, y_px, filled=True, thickness=1)
        ctx.draw_poly(total_fan, color, x_px, y_px, filled=False, thickness=1)
        ctx.label(
            int(round(ctx.px(x_px))) - 2,
            int(round(ctx.py(y_px))) + 3,
            color,
            f"{value:05.1f}",
        )

    def render(self, ctx) -> None:
        value = ctx.step_dynamic_offset(self.channel, speed=0.7, wrap=100.0)
        self.current_value = value

        ctx.draw_box(0, 0, 60, 30, "CRT_Cyan", thickness=2)

        self._draw_round_gauge(ctx, ctx.gx(10), ctx.gy(10), value)
        self._draw_fan_gauge(ctx, ctx.gx(20), ctx.gy(20), value)

        super().render(ctx)
        ctx.draw_focus_frame("blink18", padding=2.0, thickness=1.2)


class DynamicPage(Page):
    def __init__(self, app: AnywareApp):
        super().__init__("dynamic")
        self._app = app
        self._mode = 0
        self._dirty = True

    def _build_components(self):
        if self._mode == 0:
            return [
                Label(label_id="dyn_title", gx=2, gy=1, text="DYNAMIC COMPONENTS (A)", color="CRT_Cyan"),
                Label(label_id="dyn_hint", gx=2, gy=2, text="T:toggle  CTRL+H:back  ESC:quit", color="CRT_Cyan"),
                Button(
                    "dyn_btn_a",
                    "BTN-A",
                    gx=4,
                    gy=6,
                    width_px=80,
                    height_px=20,
                    scope="main",
                ),
            ]
        return [
            Label(label_id="dyn_title", gx=2, gy=1, text="DYNAMIC COMPONENTS (B)", color="CRT_Cyan"),
            Label(label_id="dyn_hint", gx=2, gy=2, text="T:toggle  CTRL+H:back  ESC:quit", color="CRT_Cyan"),
            Button(
                stable_component_id("dyn_btn", seed="b"),
                "BTN-B",
                gx=4,
                gy=6,
                width_px=80,
                height_px=20,
                scope="main",
            ),
        ]

    def on_enter(self, ctx) -> None:
        ctx.set_active_focus_scope("main")
        self.set_components(ctx, self._build_components())

    def handle_event(self, event, ctx) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_h and event.mod & pygame.KMOD_CTRL: # ctrl+h = back
                self._app.pop_page()
                return True
            if event.key == pygame.K_t:
                self._mode = 1 - self._mode
                self._dirty = True
                return True
            if ctx.key_to_focus_direction(event.key) is not None:
                ctx.move_focus_by_key(event.key)
                return True
        return super().handle_event(event, ctx)

    def update(self, ctx, dt: float) -> None:
        if self._dirty:
            self.set_components(ctx, self._build_components())
            self._dirty = False

    def render(self, ctx) -> None:
        ctx.draw_box(0, 0, 60, 30, "CRT_Cyan", thickness=2)
        super().render(ctx)
        ctx.draw_focus_frame("blink18", padding=2.0, thickness=1.2)




def _simulate_response(text: str):
    response = f"Echo: {text}"
    chunk = 6
    for idx in range(0, len(response), chunk):
        yield response[idx : idx + chunk]



def main():
    app = AnywareApp(
        title="Anyware Demo Archive",
        clear_color="Black",
        display_defaults={
            "fps": 16,
            "target_fps": 60,
            "window_noframe": False,
            "window_always_on_top": False,
            "window_bg_color_rgb": (8, 12, 14),
            "cols": 120,
            "rows": 40,
        },
        allow_raw_gui=False,
        min_gui_api_level=1,
    )

    font_main = FONTS_DIR / "长坂点宋16" / "长坂点宋16.ttf"
    app.set_fonts(ascii_path=str(font_main), cjk_path=str(font_main), cell_w=8, cell_h=16, size_px=16)

    gauges = GaugesPage(app)
    dynamic = DynamicPage(app)
    llm_page = LLMPage(
        page_id="llm_chat",
        viewport_rect=(2, 4, 116, 24),
        input_rect=(2, 29, 116, 8),
        system_prompt=_build_system_prompt,
        dispatcher=ToolDispatcher(_build_tool_registry()),
        simulate_response=_simulate_response,
        on_back=app.pop_page,
    )
    demo = DemoArchivePage(app, gauges, dynamic, llm_page)
    app.set_root_page(demo)
    app.run()


if __name__ == "__main__":
    main()
