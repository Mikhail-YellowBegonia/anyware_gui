from __future__ import annotations

import atexit
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[3]
APPS_DIR = ROOT / "apps"
for path in (ROOT, APPS_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from _bootstrap import FONTS_DIR, ensure_repo_root_on_path

ensure_repo_root_on_path()

from core.anyware import AnywareApp, Button, DialGauge, MeterBar
from core.anyware.component import ComponentGroup
from core.anyware.layout_dsl import LayoutPage, LayoutReloader

from reactor_client import ReactorClient

LAYOUT_PATH = Path(__file__).resolve().parent / "layouts" / "reactor_ui.yaml"


class VisualLayoutPage(LayoutPage):
    def __init__(
        self,
        page_id: str,
        *,
        layout: LayoutReloader,
        actions: dict | None = None,
        bindings: dict | None = None,
        visual_factory: Callable[[Any, Any], list[Any]] | None = None,
    ) -> None:
        super().__init__(page_id, layout=layout, actions=actions, bindings=bindings)
        self._visual_factory = visual_factory

    def _sync_components(self, ctx) -> None:
        super()._sync_components(ctx)
        if self._plan is None or self._visual_factory is None:
            return
        visuals = self._visual_factory(ctx, self._plan)
        if not visuals:
            return
        components = list(self._plan.components)
        components.extend(visuals)
        self.set_components(ctx, components)


class DynamicAlarmChipPanel(ComponentGroup):
    def __init__(
        self,
        *,
        panel_id: str,
        gx: float,
        gy: float,
        gw: float,
        gh: float,
        alarm_provider: Callable[[], list[dict]],
        on_select_alarm: Callable[[str], None] | None = None,
        scope: str = "main",
    ) -> None:
        super().__init__(component_id=panel_id, visible=True, enabled=True)
        self.gx = float(gx)
        self.gy = float(gy)
        self.gw = float(gw)
        self.gh = float(gh)
        self._alarm_provider = alarm_provider
        self._on_select_alarm = on_select_alarm
        self.scope = scope
        self._alarm_map: dict[str, dict] = {}
        self._signature: tuple[str, ...] = ()

    def _chip_status(self, code: str) -> str:
        item = self._alarm_map.get(code, {})
        return "ACK" if bool(item.get("acknowledged")) else "NEW"

    def _chip_color(self, code: str) -> str:
        item = self._alarm_map.get(code, {})
        severity = str(item.get("severity", "info"))
        if severity == "critical":
            return "Solar_Special"
        return "Solar_Default"

    def _build_children(self, ctx, alarms: list[dict]) -> list[Any]:
        if not alarms:
            return []

        cols = 2 if self.gw >= 18.0 else 1
        row_h = 1.6
        rows = max(1, int(self.gh // row_h))
        max_items = max(1, cols * rows)
        items = alarms[:max_items]
        chip_gw = max(5.0, (self.gw - (cols - 1) * 0.8) / cols)

        children: list[Any] = []
        for idx, item in enumerate(items):
            code = str(item.get("code", f"ALARM_{idx}"))
            r = idx // cols
            c = idx % cols
            chip_gx = self.gx + c * (chip_gw + 0.8)
            chip_gy = self.gy + r * row_h
            chip_w_px = max(26.0, float(ctx.gx(chip_gx + chip_gw) - ctx.gx(chip_gx)))
            chip_h_px = max(12.0, float(ctx.gy(chip_gy + 1.2) - ctx.gy(chip_gy)))
            label = code.replace("FAULT_", "F:")[:18]
            children.append(
                Button(
                    button_id=f"alarm_chip::{code}",
                    label=label,
                    gx=chip_gx,
                    gy=chip_gy,
                    width_px=chip_w_px,
                    height_px=chip_h_px,
                    scope=self.scope,
                    color=self._chip_color(code),
                    nav={},
                    on_select=(None if self._on_select_alarm is None else (lambda _btn, _ctx, alarm=code: self._on_select_alarm(alarm))),
                    pressable=self._on_select_alarm is not None,
                    focusable=True,
                    status=(lambda _btn, _ctx, alarm=code: self._chip_status(alarm)),
                    status_color_map={"NEW": "Solar_Special", "ACK": "Solar_Default"},
                    status_default_color="Solar_Default",
                    label_align_h="center",
                    label_align_v="center",
                    label_line_step=1,
                )
            )
        return children

    def update(self, ctx, dt: float) -> None:
        super().update(ctx, dt)
        alarms = self._alarm_provider()
        self._alarm_map = {str(item.get("code", "")): dict(item) for item in alarms}
        signature = tuple(str(item.get("code", "")) for item in alarms)
        if signature == self._signature:
            return
        self._signature = signature
        next_children = self._build_children(ctx, alarms)
        self.reconcile_children(ctx, next_children, ensure_focus=True)


class ReactorApp:
    def __init__(self) -> None:
        self.layout = LayoutReloader(LAYOUT_PATH)
        self.client = ReactorClient(poll_interval_s=0.35, timeout_s=0.7)
        self._backend_proc: subprocess.Popen | None = None

        self._state: dict | None = None
        self._events: list[dict] = []
        self._history: list[dict] = []
        self._catalog: dict | None = None
        self._last_result = "READY"

        self._last_state_poll = 0.0
        self._last_event_poll = 0.0
        self._last_history_poll = 0.0
        self._state_poll_s = 0.35
        self._events_poll_s = 0.9
        self._history_poll_s = 0.9

        self._net_info = {
            "port": self.client.port,
            "latency_ms": None,
            "comms_on": False,
        }

        self._ensure_backend()
        self._bootstrap_data()

        self.app = AnywareApp(
            title="Anyware Reactor UI (v0.0.9)",
            clear_color="Solar_Default",
            display_defaults={
                "fps": 16,
                "target_fps": 60,
                "rows": 48,
                "cols": 128,
                "window_noframe": False,
                "window_always_on_top": False,
            },
            allow_raw_gui=False,
        )

        font_ascii = FONTS_DIR / "长坂点宋16" / "长坂点宋16.ttf"
        font_cjk = FONTS_DIR / "长坂点宋16" / "长坂点宋16.ttf"
        self.app.set_fonts(ascii_path=str(font_ascii), cjk_path=str(font_cjk), cell_w=8, cell_h=16, size_px=16)

        actions = {
            "go_page.status": lambda _b, _ctx, _el: self.app.switch_page("status"),
            "go_page.diagram": lambda _b, _ctx, _el: self.app.switch_page("diagram"),
            "go_page.control": lambda _b, _ctx, _el: self.app.switch_page("control"),
            "go_page.core": lambda _b, _ctx, _el: self.app.switch_page("core"),
            "control.adjust": self._action_control_adjust,
            "control.set_bool": self._action_control_set_bool,
            "scenario.set": self._action_set_scenario,
            "fault.toggle": self._action_toggle_fault,
            "fault.clear_all": self._action_clear_faults,
            "action.run": self._action_run_operator,
        }

        bindings = {
            "net": {
                "info": lambda _ctx: self._net_info_text(),
                "comms_on": lambda _ctx: self._net_info.get("comms_on", False),
                "comms_color": lambda _ctx: "Solar_Special"
                if self._net_info.get("comms_on", False)
                else "Solar_Default",
            },
            "status": {
                "metrics_block": lambda _ctx: self._status_metrics_block(),
                "mission_block": lambda _ctx: self._status_mission_block(),
                "alarm_block": lambda _ctx: self._status_alarm_block(),
                "last_result": lambda _ctx: self._last_result,
            },
            "trend": {
                "history_block": lambda _ctx: self._trend_history_block(),
                "events_block": lambda _ctx: self._trend_events_block(),
            },
            "control": {
                "targets_block": lambda _ctx: self._control_targets_block(),
                "metrics_block": lambda _ctx: self._control_metrics_block(),
            },
            "core": {
                "faults_block": lambda _ctx: self._core_faults_block(),
                "events_block": lambda _ctx: self._trend_events_block(),
            },
            "footer": {
                "info": lambda _ctx: self._footer_info(),
            },
        }

        pages = [
            VisualLayoutPage(
                "status",
                layout=self.layout,
                actions=actions,
                bindings=bindings,
                visual_factory=self._build_status_visuals,
            ),
            VisualLayoutPage("diagram", layout=self.layout, actions=actions, bindings=bindings),
            VisualLayoutPage(
                "control",
                layout=self.layout,
                actions=actions,
                bindings=bindings,
                visual_factory=self._build_control_visuals,
            ),
            VisualLayoutPage(
                "core",
                layout=self.layout,
                actions=actions,
                bindings=bindings,
                visual_factory=self._build_core_visuals,
            ),
        ]
        self.app.register_pages(pages)
        self.app.set_root_page(pages[0])

    def _net_info_text(self) -> str:
        port = self._net_info.get("port")
        latency = self._net_info.get("latency_ms")
        latency_text = "--ms" if latency is None else f"{int(round(latency))}ms"
        return f"PORT {port}\\nLAT {latency_text}"

    def _ensure_backend(self) -> None:
        if self.client.health_check():
            return
        backend_path = Path(__file__).resolve().parents[1] / "reactor_backend.py"
        if not backend_path.exists():
            return
        cmd = [
            sys.executable,
            str(backend_path),
            "--host",
            "127.0.0.1",
            "--port",
            str(self.client.port),
        ]
        try:
            self._backend_proc = subprocess.Popen(cmd)
        except Exception:
            self._backend_proc = None
            return
        atexit.register(self._stop_backend)
        for _ in range(20):
            time.sleep(0.2)
            if self.client.health_check():
                return

    def _stop_backend(self) -> None:
        if self._backend_proc is None:
            return
        if self._backend_proc.poll() is None:
            self._backend_proc.terminate()
        self._backend_proc = None

    def _bootstrap_data(self) -> None:
        self._poll_state(force=True)
        self._poll_events(force=True)
        self._poll_history(force=True)
        self._catalog = self.client.fetch_catalog()

    def _extract_state(self, payload: dict | None) -> dict | None:
        if not isinstance(payload, dict):
            return None
        state = payload.get("state")
        if isinstance(state, dict):
            return state
        return None

    def _post_result_to_state(self, payload: dict | None, *, default_ok: str = "OK") -> None:
        if not isinstance(payload, dict):
            self._last_result = "REQUEST FAILED"
            return
        state = payload.get("state")
        if isinstance(state, dict):
            self._state = state
        msg = payload.get("message")
        if isinstance(msg, str) and msg:
            self._last_result = msg.upper()
            return
        if payload.get("ok") is True:
            self._last_result = default_ok
            return
        err = payload.get("error")
        if isinstance(err, str) and err:
            self._last_result = err.upper()
            return
        self._last_result = "REQUEST DONE"

    def _poll_state(self, *, force: bool = False) -> None:
        now = time.time()
        if not force and now - self._last_state_poll < self._state_poll_s:
            return
        self._last_state_poll = now
        payload = self.client.fetch_state()
        state = self._extract_state(payload)
        if state is not None:
            self._state = state
            events_tail = state.get("events_tail")
            if isinstance(events_tail, list):
                self._events = [e for e in events_tail if isinstance(e, dict)]

    def _poll_events(self, *, force: bool = False) -> None:
        now = time.time()
        if not force and now - self._last_event_poll < self._events_poll_s:
            return
        self._last_event_poll = now
        payload = self.client.fetch_events(limit=30)
        if isinstance(payload, dict) and isinstance(payload.get("events"), list):
            self._events = [e for e in payload["events"] if isinstance(e, dict)]

    def _poll_history(self, *, force: bool = False) -> None:
        now = time.time()
        if not force and now - self._last_history_poll < self._history_poll_s:
            return
        self._last_history_poll = now
        payload = self.client.fetch_history(limit=36)
        if isinstance(payload, dict) and isinstance(payload.get("history"), list):
            self._history = [h for h in payload["history"] if isinstance(h, dict)]

    def _run_periodic_refresh(self) -> None:
        self._poll_state()
        self._poll_events()
        self._poll_history()

    def _action_control_adjust(self, _button, _ctx, element: dict) -> None:
        if not isinstance(element, dict):
            return
        key = element.get("key")
        delta = element.get("delta")
        if not isinstance(key, str) or not isinstance(delta, (int, float)):
            return
        controls = self._state_controls()
        current = float(controls.get(key, 0.0))
        result = self.client.post_control({key: current + float(delta)})
        self._post_result_to_state(result, default_ok=f"SET {key}")

    def _action_control_set_bool(self, _button, _ctx, element: dict) -> None:
        if not isinstance(element, dict):
            return
        key = element.get("key")
        if not isinstance(key, str):
            return
        if "value" in element and isinstance(element["value"], bool):
            value = bool(element["value"])
        else:
            value = not bool(self._state_controls().get(key, False))
        result = self.client.post_control({key: value})
        self._post_result_to_state(result, default_ok=f"SET {key}")

    def _action_set_scenario(self, _button, _ctx, element: dict) -> None:
        name = element.get("name") if isinstance(element, dict) else None
        if not isinstance(name, str):
            return
        result = self.client.post_scenario(name)
        self._post_result_to_state(result, default_ok=f"SCENARIO {name}")

    def _action_toggle_fault(self, _button, _ctx, element: dict) -> None:
        name = element.get("name") if isinstance(element, dict) else None
        if not isinstance(name, str):
            return
        current_faults = set(self._state_faults())
        enabled = name not in current_faults
        result = self.client.post_fault(name, enabled=enabled)
        self._post_result_to_state(result, default_ok=f"FAULT {name}")

    def _action_clear_faults(self, _button, _ctx, _element: dict) -> None:
        result = self.client.post_fault("clear_all", enabled=False)
        self._post_result_to_state(result, default_ok="FAULTS CLEARED")

    def _action_run_operator(self, _button, _ctx, element: dict) -> None:
        name = element.get("name") if isinstance(element, dict) else None
        if not isinstance(name, str):
            return
        result = self.client.post_action(name)
        self._post_result_to_state(result, default_ok=f"ACTION {name}")

    def _action_ack_alarm_chip(self, _code: str) -> None:
        result = self.client.post_action("ack_alarms")
        self._post_result_to_state(result, default_ok="ALARMS ACK")

    def _state_controls(self) -> dict:
        if isinstance(self._state, dict):
            controls = self._state.get("controls")
            if isinstance(controls, dict):
                return controls
        return {}

    def _state_actuators(self) -> dict:
        if isinstance(self._state, dict):
            actuators = self._state.get("actuators")
            if isinstance(actuators, dict):
                return actuators
        return {}

    def _state_metrics(self) -> dict:
        if isinstance(self._state, dict):
            metrics = self._state.get("metrics")
            if isinstance(metrics, dict):
                return metrics
        return {}

    def _state_faults(self) -> list[str]:
        if isinstance(self._state, dict):
            faults = self._state.get("faults")
            if isinstance(faults, list):
                return [str(x) for x in faults]
        return []

    def _state_alarm_entries(self) -> list[dict]:
        if isinstance(self._state, dict):
            alarm_state = self._state.get("alarm_state")
            if isinstance(alarm_state, list):
                return [item for item in alarm_state if isinstance(item, dict)]
        return []

    def _state_health(self) -> dict:
        if isinstance(self._state, dict):
            health = self._state.get("health")
            if isinstance(health, dict):
                return health
        return {}

    def _metric_value(self, name: str) -> float:
        value = self._state_metrics().get(name, 0.0)
        if isinstance(value, (int, float)):
            return float(value)
        return 0.0

    def _actuator_value(self, name: str) -> float:
        value = self._state_actuators().get(name, 0.0)
        if isinstance(value, (int, float)):
            return float(value)
        return 0.0

    def _health_value(self, name: str) -> float:
        value = self._state_health().get(name, 40.0)
        if isinstance(value, (int, float)):
            return float(value)
        return 40.0

    def _slot_rect(self, ctx, plan: Any, slot_id: str) -> tuple[float, float, float, float] | None:
        slots = getattr(plan, "slots", {})
        if not isinstance(slots, dict):
            return None
        slot = slots.get(slot_id)
        if not isinstance(slot, dict):
            return None
        gx = float(slot.get("gx", 0.0))
        gy = float(slot.get("gy", 0.0))
        gw = float(slot.get("gw", 0.0))
        gh = float(slot.get("gh", 0.0))
        width_px = max(6.0, float(ctx.gx(gx + gw) - ctx.gx(gx)))
        height_px = max(4.0, float(ctx.gy(gy + gh) - ctx.gy(gy)))
        return (gx, gy, width_px, height_px)

    def _slot_grid(self, plan: Any, slot_id: str) -> tuple[float, float, float, float] | None:
        slots = getattr(plan, "slots", {})
        if not isinstance(slots, dict):
            return None
        slot = slots.get(slot_id)
        if not isinstance(slot, dict):
            return None
        gx = float(slot.get("gx", 0.0))
        gy = float(slot.get("gy", 0.0))
        gw = float(slot.get("gw", 0.0))
        gh = float(slot.get("gh", 0.0))
        return (gx, gy, gw, gh)

    def _build_meter(
        self,
        ctx,
        plan: Any,
        *,
        meter_id: str,
        slot_id: str,
        value_fn: Callable[[Any], float],
        min_value: float,
        max_value: float,
        mode: str = "bar",
        segments: int = 12,
        color: str = "Solar_Special",
    ) -> MeterBar | None:
        slot = self._slot_rect(ctx, plan, slot_id)
        if slot is None:
            return None
        gx, gy, width_px, height_px = slot
        return MeterBar(
            meter_id=meter_id,
            gx=gx,
            gy=gy,
            width_px=width_px,
            height_px=height_px,
            value=value_fn,
            min_value=min_value,
            max_value=max_value,
            mode=mode,
            segments=segments,
            color=color,
            empty_color="Solar_Default" if mode == "segments" else None,
            border_color="Solar_Default",
            border_thickness=1.0,
            padding_px=1.0,
        )

    def _build_status_visuals(self, ctx, plan: Any) -> list[Any]:
        visuals: list[Any] = []
        for meter in (
            self._build_meter(
                ctx,
                plan,
                meter_id="meter_status_power",
                slot_id="status_slot_power",
                value_fn=lambda _c: self._metric_value("power_mw"),
                min_value=0.0,
                max_value=3000.0,
            ),
            self._build_meter(
                ctx,
                plan,
                meter_id="meter_status_temp",
                slot_id="status_slot_temp",
                value_fn=lambda _c: self._metric_value("core_temp_c"),
                min_value=220.0,
                max_value=880.0,
            ),
            self._build_meter(
                ctx,
                plan,
                meter_id="meter_status_press",
                slot_id="status_slot_press",
                value_fn=lambda _c: self._metric_value("pressure_mpa"),
                min_value=8.0,
                max_value=19.0,
            ),
            self._build_meter(
                ctx,
                plan,
                meter_id="meter_status_flow",
                slot_id="status_slot_flow",
                value_fn=lambda _c: self._metric_value("coolant_flow"),
                min_value=0.0,
                max_value=100.0,
            ),
        ):
            if meter is not None:
                visuals.append(meter)

        dial_slot = self._slot_rect(ctx, plan, "status_slot_stability")
        if dial_slot is not None:
            gx, gy, width_px, height_px = dial_slot
            visuals.append(
                DialGauge(
                    gauge_id="dial_status_stability",
                    center_gx=gx + float((plan.slots["status_slot_stability"]["gw"])) * 0.5,
                    center_gy=gy + float((plan.slots["status_slot_stability"]["gh"])) * 0.5,
                    radius_px=max(4.0, min(width_px, height_px) * 0.45),
                    value=lambda _c: self._metric_value("grid_stability_pct"),
                    min_value=0.0,
                    max_value=100.0,
                    style="both",
                    color="Solar_Special",
                )
            )

        chip_slot = self._slot_grid(plan, "status_slot_alarm_dynamic")
        if chip_slot is not None:
            gx, gy, gw, gh = chip_slot
            visuals.append(
                DynamicAlarmChipPanel(
                    panel_id="status_alarm_dynamic",
                    gx=gx,
                    gy=gy,
                    gw=gw,
                    gh=gh,
                    alarm_provider=self._state_alarm_entries,
                    on_select_alarm=self._action_ack_alarm_chip,
                    scope="main",
                )
            )
        return visuals

    def _build_control_visuals(self, ctx, plan: Any) -> list[Any]:
        visuals: list[Any] = []
        for meter in (
            self._build_meter(
                ctx,
                plan,
                meter_id="meter_control_rods",
                slot_id="control_slot_rods",
                value_fn=lambda _c: self._actuator_value("rods"),
                min_value=0.0,
                max_value=100.0,
                mode="segments",
                segments=20,
            ),
            self._build_meter(
                ctx,
                plan,
                meter_id="meter_control_pump",
                slot_id="control_slot_pump",
                value_fn=lambda _c: self._actuator_value("pump_speed"),
                min_value=0.0,
                max_value=100.0,
                mode="segments",
                segments=20,
            ),
            self._build_meter(
                ctx,
                plan,
                meter_id="meter_control_valve",
                slot_id="control_slot_valve",
                value_fn=lambda _c: self._actuator_value("valve"),
                min_value=0.0,
                max_value=100.0,
                mode="segments",
                segments=20,
            ),
            self._build_meter(
                ctx,
                plan,
                meter_id="meter_control_load",
                slot_id="control_slot_load",
                value_fn=lambda _c: self._actuator_value("load"),
                min_value=0.0,
                max_value=100.0,
                mode="segments",
                segments=20,
            ),
            self._build_meter(
                ctx,
                plan,
                meter_id="meter_control_grid",
                slot_id="control_slot_grid",
                value_fn=lambda _c: self._metric_value("grid_stability_pct"),
                min_value=0.0,
                max_value=100.0,
            ),
        ):
            if meter is not None:
                visuals.append(meter)
        return visuals

    def _build_core_visuals(self, ctx, plan: Any) -> list[Any]:
        visuals: list[Any] = []
        for meter in (
            self._build_meter(
                ctx,
                plan,
                meter_id="meter_core_health_core",
                slot_id="core_slot_h_core",
                value_fn=lambda _c: self._health_value("core"),
                min_value=40.0,
                max_value=100.0,
            ),
            self._build_meter(
                ctx,
                plan,
                meter_id="meter_core_health_cooling",
                slot_id="core_slot_h_cooling",
                value_fn=lambda _c: self._health_value("cooling"),
                min_value=40.0,
                max_value=100.0,
            ),
            self._build_meter(
                ctx,
                plan,
                meter_id="meter_core_health_steam",
                slot_id="core_slot_h_steam",
                value_fn=lambda _c: self._health_value("steam"),
                min_value=40.0,
                max_value=100.0,
            ),
        ):
            if meter is not None:
                visuals.append(meter)
        return visuals

    def _fmt_num(self, value: object, *, digits: int = 1) -> str:
        if isinstance(value, (int, float)):
            return f"{float(value):.{digits}f}"
        return "--"

    def _fmt_bool(self, value: object) -> str:
        return "ON" if bool(value) else "OFF"

    def _status_metrics_block(self) -> str:
        if not isinstance(self._state, dict):
            return "NO STATE\nWaiting backend data..."
        metrics = self._state_metrics()
        return "\n".join(
            [
                "[Reactor Status]",
                f"Scenario : {self._state.get('scenario', '--')}",
                f"Status   : {self._state.get('status', '--')}",
                f"Time(s)  : {self._fmt_num(self._state.get('time_s'), digits=2)}",
                "",
                f"Power MW : {self._fmt_num(metrics.get('power_mw'))}",
                f"Core C   : {self._fmt_num(metrics.get('core_temp_c'))}",
                f"Press MPa: {self._fmt_num(metrics.get('pressure_mpa'), digits=2)}",
                f"Steam MPa: {self._fmt_num(metrics.get('steam_pressure_mpa'), digits=2)}",
                f"Flow %   : {self._fmt_num(metrics.get('coolant_flow'))}",
                f"Elec MW  : {self._fmt_num(metrics.get('electric_mw'))}",
            ]
        )

    def _status_mission_block(self) -> str:
        mission = self._state.get("mission") if isinstance(self._state, dict) else None
        if not isinstance(mission, dict):
            return "[Mission]\n--"
        steps = mission.get("steps") if isinstance(mission.get("steps"), dict) else {}
        return "\n".join(
            [
                "[Mission]",
                f"Phase     : {mission.get('phase', '--')}",
                f"Score     : {self._fmt_num(mission.get('score'), digits=1)}",
                f"Stable(s) : {self._fmt_num(mission.get('stable_time_s'), digits=1)}",
                "",
                f"Loop Ready: {self._fmt_bool(steps.get('primary_loop_ready'))}",
                f"Critical  : {self._fmt_bool(steps.get('reactor_critical'))}",
                f"Turbine   : {self._fmt_bool(steps.get('turbine_spinup'))}",
                f"Grid Sync : {self._fmt_bool(steps.get('grid_sync'))}",
                "",
                "Objective:",
                str(mission.get("objective", "--")),
            ]
        )

    def _status_alarm_block(self) -> str:
        alarm_state = self._state.get("alarm_state") if isinstance(self._state, dict) else None
        lines = ["[Alarms]"]
        if isinstance(alarm_state, list) and alarm_state:
            for item in alarm_state[:8]:
                if not isinstance(item, dict):
                    continue
                code = str(item.get("code", "--"))
                sev = str(item.get("severity", "info"))
                ack = "ACK" if bool(item.get("acknowledged")) else "NEW"
                lines.append(f"{sev[:1].upper()} {ack} {code[:28]}")
        else:
            lines.append("No active alarms")

        lines.append("")
        lines.append("[Recent Events]")
        for event in self._events[-6:]:
            if not isinstance(event, dict):
                continue
            t = self._fmt_num(event.get("time_s"), digits=1)
            code = str(event.get("code", "EV"))
            lines.append(f"t={t} {code[:28]}")
        return "\n".join(lines)

    def _trend_history_block(self) -> str:
        lines = ["[History Snapshot]", " t    status   MW    T(C)   P(MPa) Elec  A  Score"]
        if not self._history:
            lines.append(" no history")
            return "\n".join(lines)
        for row in self._history[-20:]:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"{self._fmt_num(row.get('time_s'), digits=1):>5} "
                f"{str(row.get('status', '--'))[:7]:<7} "
                f"{self._fmt_num(row.get('power_mw'), digits=0):>5} "
                f"{self._fmt_num(row.get('core_temp_c'), digits=0):>6} "
                f"{self._fmt_num(row.get('pressure_mpa'), digits=1):>7} "
                f"{self._fmt_num(row.get('electric_mw'), digits=0):>5} "
                f"{str(row.get('alarm_count', '--')):>2} "
                f"{self._fmt_num(row.get('score'), digits=0):>5}"
            )
        return "\n".join(lines)

    def _trend_events_block(self) -> str:
        lines = ["[Event Stream]"]
        if not self._events:
            lines.append(" no events")
            return "\n".join(lines)
        for event in self._events[-20:]:
            if not isinstance(event, dict):
                continue
            t = self._fmt_num(event.get("time_s"), digits=1)
            sev = str(event.get("severity", "i"))[:1].upper()
            code = str(event.get("code", "--"))[:24]
            lines.append(f"{t:>5} {sev} {code}")
        return "\n".join(lines)

    def _control_targets_block(self) -> str:
        controls = self._state_controls()
        actuators = self._state_actuators()
        return "\n".join(
            [
                "[Setpoint / Actuator]",
                f"Rods    : {self._fmt_num(controls.get('rods'))}% / {self._fmt_num(actuators.get('rods'))}%",
                f"Pump    : {self._fmt_num(controls.get('pump_speed'))}% / {self._fmt_num(actuators.get('pump_speed'))}%",
                f"Valve   : {self._fmt_num(controls.get('valve'))}% / {self._fmt_num(actuators.get('valve'))}%",
                f"Load    : {self._fmt_num(controls.get('load'))}% / {self._fmt_num(actuators.get('load'))}%",
                "",
                f"SCRAM   : {self._fmt_bool(controls.get('scram'))}",
                f"E-INJ   : {self._fmt_bool(controls.get('emergency_inject'))}",
            ]
        )

    def _control_metrics_block(self) -> str:
        metrics = self._state_metrics()
        return "\n".join(
            [
                "[Derived Metrics]",
                f"Flux         : {self._fmt_num(metrics.get('neutron_flux'), digits=3)}",
                f"GridStable % : {self._fmt_num(metrics.get('grid_stability_pct'), digits=1)}",
                f"Margin C     : {self._fmt_num(metrics.get('thermal_margin_c'), digits=1)}",
                f"Efficiency % : {self._fmt_num(metrics.get('efficiency_pct'), digits=1)}",
                "",
                "Use +/- to tune setpoints.",
                "Use scenario button for reset.",
            ]
        )

    def _core_faults_block(self) -> str:
        faults = set(self._state_faults())
        known = [
            "pump_degraded",
            "coolant_leak",
            "valve_stuck",
            "pressure_spike",
            "sensor_drift",
            "fuel_quality_low",
        ]
        lines = ["[Fault Matrix]"]
        for name in known:
            flag = "ON " if name in faults else "OFF"
            lines.append(f"{flag} {name}")
        lines.append("")
        lines.append("Press toggle buttons to inject/clear faults")
        return "\n".join(lines)

    def _footer_info(self) -> str:
        status = "--"
        if isinstance(self._state, dict):
            status = str(self._state.get("status", "--"))
        return f"STATUS {status} | RESULT {self._last_result}"

    def run(self) -> None:
        original_update = self.app.page_stack.update

        def _update(ctx, dt: float) -> None:
            self._run_periodic_refresh()
            comms_on = self.client.comms_ok()
            self._net_info["comms_on"] = comms_on
            self._net_info["latency_ms"] = self.client.last_latency_ms if comms_on else None
            original_update(ctx, dt)

        self.app.page_stack.update = _update
        self.app.run()


def main() -> None:
    ReactorApp().run()


if __name__ == "__main__":
    main()
