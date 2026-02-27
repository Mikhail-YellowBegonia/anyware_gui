from __future__ import annotations

import math
from typing import Dict, List, Tuple


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def approach(current: float, target: float, rate_per_sec: float, dt: float) -> float:
    if current < target:
        return min(current + rate_per_sec * dt, target)
    return max(current - rate_per_sec * dt, target)


FAULTS = {
    "pump_degraded": {
        "label": "Pump efficiency degraded",
        "impact": "Reduces coolant flow effectiveness",
    },
    "coolant_leak": {
        "label": "Coolant leak",
        "impact": "Lowers effective flow and raises temperature",
    },
    "valve_stuck": {
        "label": "Valve stuck partially closed",
        "impact": "Limits valve opening range",
    },
    "pressure_spike": {
        "label": "Primary pressure spike",
        "impact": "Adds bias to pressure",
    },
    "sensor_drift": {
        "label": "Sensor drift",
        "impact": "Adds mild deterministic noise",
    },
    "fuel_quality_low": {
        "label": "Fuel quality low",
        "impact": "Derates max power",
    },
}

SCENARIOS = {
    "cold_start": "Cold start (offline, low power)",
    "running": "Stable running",
}

ACTIONS = {
    "ack_alarms": {
        "label": "Acknowledge alarms",
        "description": "Acknowledge all currently active alarms.",
    },
    "quick_start": {
        "label": "Quick start",
        "description": "Apply startup-friendly control setpoints.",
    },
    "stabilize": {
        "label": "Stabilize loop",
        "description": "Apply conservative steady-state setpoints.",
    },
    "clear_scram": {
        "label": "Clear SCRAM",
        "description": "Attempt SCRAM recovery when process values are safe.",
    },
}

ALARM_SEVERITY = {
    "CORE_OVERHEAT": "critical",
    "OVERPRESSURE": "critical",
    "SCRAM_ACTIVE": "critical",
    "LOW_COOLANT_FLOW": "warning",
    "LOW_STEAM_PRESSURE": "warning",
    "EMERGENCY_INJECT": "warning",
}


class ReactorSim:
    def __init__(self) -> None:
        self.time_s = 0.0
        self.sim_speed = 1.0
        self.paused = False
        self.faults: set[str] = set()
        self.controls: Dict[str, float | bool] = {}
        self.actuators: Dict[str, float] = {}
        self.metrics: Dict[str, float | str] = {}
        self.alarms: List[str] = []

        self.events: List[Dict[str, object]] = []
        self.history: List[Dict[str, object]] = []
        self.score = 0.0
        self.mission_phase = "startup_precheck"
        self.mission_steps: Dict[str, bool] = {}
        self.stable_time_s = 0.0

        self.alarm_acknowledged: set[str] = set()
        self._last_alarms: set[str] = set()
        self._last_status = "COLD"
        self._history_accum_s = 0.0

        self._max_events = 200
        self._max_history = 240
        self._history_sample_s = 0.5

        self.reset("cold_start")

    def reset(self, scenario: str) -> None:
        if scenario not in SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario}")
        self.scenario = scenario
        self.time_s = 0.0
        self.faults.clear()
        self.events.clear()
        self.history.clear()
        self.alarm_acknowledged.clear()
        self._last_alarms.clear()
        self._history_accum_s = 0.0

        if scenario == "cold_start":
            self.controls = {
                "rods": 100.0,
                "pump_speed": 0.0,
                "valve": 0.0,
                "load": 0.0,
                "scram": False,
                "emergency_inject": False,
            }
            self.actuators = {
                "rods": 100.0,
                "pump_speed": 0.0,
                "valve": 0.0,
                "load": 0.0,
            }
            self.metrics = {
                "power_mw": 0.0,
                "core_temp_c": 260.0,
                "coolant_in_c": 230.0,
                "coolant_out_c": 240.0,
                "pressure_mpa": 9.8,
                "steam_pressure_mpa": 1.5,
                "coolant_flow": 0.0,
                "turbine_rpm": 0.0,
                "electric_mw": 0.0,
                "neutron_flux": 0.0,
            }
            self.score = 0.0
            self.stable_time_s = 0.0
            self.mission_phase = "startup_precheck"
            self.mission_steps = {
                "primary_loop_ready": False,
                "reactor_critical": False,
                "turbine_spinup": False,
                "grid_sync": False,
            }
        else:
            self.controls = {
                "rods": 35.0,
                "pump_speed": 80.0,
                "valve": 70.0,
                "load": 75.0,
                "scram": False,
                "emergency_inject": False,
            }
            self.actuators = {
                "rods": 35.0,
                "pump_speed": 78.0,
                "valve": 68.0,
                "load": 72.0,
            }
            self.metrics = {
                "power_mw": 2200.0,
                "core_temp_c": 560.0,
                "coolant_in_c": 290.0,
                "coolant_out_c": 320.0,
                "pressure_mpa": 15.2,
                "steam_pressure_mpa": 6.5,
                "coolant_flow": 78.0,
                "turbine_rpm": 3200.0,
                "electric_mw": 720.0,
                "neutron_flux": 0.72,
            }
            self.score = 220.0
            self.stable_time_s = 30.0
            self.mission_phase = "power_hold"
            self.mission_steps = {
                "primary_loop_ready": True,
                "reactor_critical": True,
                "turbine_spinup": True,
                "grid_sync": True,
            }

        self.alarms = []
        self._last_status = self._derive_status()
        self._log_event(
            "SCENARIO_RESET",
            message=f"Scenario set to {scenario}",
            details={"scenario": scenario},
        )
        self.step(0.0)

    def set_controls(self, **kwargs: float | bool) -> None:
        changed: Dict[str, float | bool] = {}
        for key, value in kwargs.items():
            if key not in self.controls:
                continue
            old = self.controls[key]
            if isinstance(old, bool):
                if not isinstance(value, bool):
                    continue
                if old != value:
                    self.controls[key] = value
                    changed[key] = value
                continue
            if not isinstance(value, (int, float)):
                continue
            if key == "rods":
                new = clamp(float(value), 0.0, 100.0)
            elif key in ("pump_speed", "valve", "load"):
                new = clamp(float(value), 0.0, 100.0)
            else:
                new = float(value)
            if abs(float(old) - new) >= 0.1:
                self.controls[key] = new
                changed[key] = new
        if changed:
            self._log_event(
                "CONTROL_UPDATE",
                message="Control targets updated",
                details={"changed": self._rounded_dict(changed)},
            )

    def set_fault(self, name: str, enabled: bool) -> None:
        if name not in FAULTS:
            return
        if enabled and name not in self.faults:
            self.faults.add(name)
            self._log_event(
                "FAULT_ENABLED",
                severity="warning",
                message=f"Fault enabled: {name}",
                details={"fault": name},
            )
        elif not enabled and name in self.faults:
            self.faults.discard(name)
            self._log_event(
                "FAULT_DISABLED",
                message=f"Fault disabled: {name}",
                details={"fault": name},
            )

    def set_sim(self, *, paused: bool | None = None, speed: float | None = None) -> None:
        if paused is not None:
            self.paused = bool(paused)
            self._log_event(
                "SIM_PAUSED" if self.paused else "SIM_RESUMED",
                message="Simulation paused" if self.paused else "Simulation resumed",
            )
        if speed is not None:
            self.sim_speed = clamp(float(speed), 0.1, 5.0)
            self._log_event(
                "SIM_SPEED",
                message=f"Simulation speed set to {self.sim_speed:.2f}",
                details={"speed": round(self.sim_speed, 2)},
            )

    def acknowledge_alarms(self) -> int:
        current = set(self.alarms)
        before = len(self.alarm_acknowledged)
        self.alarm_acknowledged.update(current)
        acked = len(self.alarm_acknowledged) - before
        if acked > 0:
            self._log_event(
                "ALARMS_ACK",
                message=f"Acknowledged {acked} alarms",
                details={"acked": acked},
            )
        return acked

    def execute_action(self, name: str) -> Tuple[bool, str]:
        if name == "ack_alarms":
            acked = self.acknowledge_alarms()
            return True, f"{acked} alarms acknowledged"

        if name == "quick_start":
            if bool(self.controls["scram"]):
                return False, "Cannot quick-start while SCRAM is active"
            self.set_controls(rods=72.0, pump_speed=55.0, valve=45.0, load=18.0)
            self._log_event("ACTION_QUICK_START", message="Quick-start setpoints applied")
            return True, "Quick-start setpoints applied"

        if name == "stabilize":
            if bool(self.controls["scram"]):
                return False, "Cannot stabilize while SCRAM is active"
            self.set_controls(rods=44.0, pump_speed=78.0, valve=66.0, load=52.0, emergency_inject=False)
            self._log_event("ACTION_STABILIZE", message="Stabilization setpoints applied")
            return True, "Stabilization setpoints applied"

        if name == "clear_scram":
            if not bool(self.controls["scram"]):
                return False, "SCRAM is not active"
            if not self._safe_to_clear_scram():
                return False, "Unsafe conditions for SCRAM clear"
            self.controls["scram"] = False
            self.controls["emergency_inject"] = False
            self._log_event("SCRAM_CLEARED", message="Operator cleared SCRAM")
            return True, "SCRAM cleared"

        return False, f"Unknown action: {name}"

    def step(self, dt: float) -> None:
        if self.paused:
            return

        dt = max(0.0, dt)
        self.time_s += dt

        rods_target = float(self.controls["rods"])
        pump_target = float(self.controls["pump_speed"])
        valve_target = float(self.controls["valve"])
        load_target = float(self.controls["load"])

        # Actuator inertia keeps UI changes visible and testable.
        self.actuators["rods"] = approach(self.actuators["rods"], rods_target, 25.0, dt)
        self.actuators["pump_speed"] = approach(self.actuators["pump_speed"], pump_target, 20.0, dt)
        self.actuators["valve"] = approach(self.actuators["valve"], valve_target, 18.0, dt)
        self.actuators["load"] = approach(self.actuators["load"], load_target, 15.0, dt)

        reactivity = clamp(1.0 - self.actuators["rods"] / 100.0, 0.0, 1.0)
        if bool(self.controls["scram"]):
            reactivity = 0.0
        if bool(self.controls["emergency_inject"]):
            reactivity *= 0.2

        pump_eff = 1.0
        if "pump_degraded" in self.faults:
            pump_eff *= 0.6
        if "coolant_leak" in self.faults:
            pump_eff *= 0.7

        valve_eff = 1.0
        if "valve_stuck" in self.faults:
            valve_eff *= 0.55

        power_derate = 0.18 if "fuel_quality_low" in self.faults else 0.0
        pressure_bias = 1.4 if "pressure_spike" in self.faults else 0.0

        noise = math.sin(self.time_s * 0.6) * 0.4 + math.sin(self.time_s * 0.17 + 1.2) * 0.2
        if "sensor_drift" in self.faults:
            noise *= 1.6

        cooling_factor = clamp(
            (self.actuators["pump_speed"] / 100.0)
            * (self.actuators["valve"] / 100.0)
            * pump_eff
            * valve_eff,
            0.0,
            1.0,
        )

        max_power = 3000.0
        power_target = max_power * reactivity * (1.0 - power_derate)
        power_mw = approach(float(self.metrics["power_mw"]), power_target, 160.0, dt)

        core_temp_target = 260.0 + power_mw / 25.0 - cooling_factor * 60.0
        core_temp_target = clamp(core_temp_target, 220.0, 880.0)
        core_temp_c = approach(float(self.metrics["core_temp_c"]), core_temp_target, 18.0, dt)

        coolant_flow = clamp(self.actuators["pump_speed"] * pump_eff, 0.0, 100.0)

        coolant_in_target = core_temp_c - (30.0 + cooling_factor * 40.0)
        coolant_out_target = core_temp_c - (6.0 + cooling_factor * 10.0)
        coolant_in_c = approach(float(self.metrics["coolant_in_c"]), coolant_in_target, 14.0, dt)
        coolant_out_c = approach(float(self.metrics["coolant_out_c"]), coolant_out_target, 16.0, dt)

        pressure_target = 12.0 + power_mw / 460.0 + (1.0 - cooling_factor) * 1.6 + pressure_bias
        pressure_mpa = approach(float(self.metrics["pressure_mpa"]), pressure_target, 0.6, dt)

        steam_target = 5.0 + power_mw / 720.0 - (1.0 - cooling_factor) * 0.4
        steam_pressure_mpa = approach(float(self.metrics["steam_pressure_mpa"]), steam_target, 0.5, dt)

        turbine_target = 900.0 + steam_pressure_mpa * 380.0 - self.actuators["load"] * 2.5
        turbine_rpm = approach(float(self.metrics["turbine_rpm"]), turbine_target, 120.0, dt)

        electric_mw = power_mw * 0.33 * (self.actuators["load"] / 100.0)
        neutron_flux = clamp(power_mw / max_power, 0.0, 1.0)

        core_temp_c += noise
        pressure_mpa += noise * 0.05
        steam_pressure_mpa += noise * 0.04

        # Avoid instant startup SCRAM: low-flow only matters once reactor has notable power.
        if core_temp_c > 740.0 or pressure_mpa > 18.0 or (power_mw > 200.0 and coolant_flow < 8.0):
            if not bool(self.controls["scram"]):
                self._log_event(
                    "AUTO_SCRAM",
                    severity="critical",
                    message="Automatic SCRAM triggered by unsafe process values",
                )
            self.controls["scram"] = True

        reactivity_pcm = (reactivity - 0.5) * 2000.0
        thermal_margin_c = 780.0 - core_temp_c
        efficiency_pct = 0.0 if power_mw < 50.0 else (electric_mw / power_mw) * 100.0
        pressure_norm = abs(pressure_mpa - 14.5)
        steam_norm = abs(steam_pressure_mpa - 6.3)
        rpm_norm = abs(turbine_rpm - 3200.0) / 1600.0
        grid_stability_pct = clamp(100.0 - pressure_norm * 8.0 - steam_norm * 10.0 - rpm_norm * 30.0, 0.0, 100.0)
        coolant_inventory_pct = clamp(100.0 - (12.0 if "coolant_leak" in self.faults else 0.0), 55.0, 100.0)

        self.metrics.update(
            {
                "power_mw": power_mw,
                "core_temp_c": core_temp_c,
                "coolant_in_c": coolant_in_c,
                "coolant_out_c": coolant_out_c,
                "pressure_mpa": pressure_mpa,
                "steam_pressure_mpa": steam_pressure_mpa,
                "coolant_flow": coolant_flow,
                "turbine_rpm": turbine_rpm,
                "electric_mw": electric_mw,
                "neutron_flux": neutron_flux,
                "reactivity_pcm": reactivity_pcm,
                "thermal_margin_c": thermal_margin_c,
                "efficiency_pct": efficiency_pct,
                "grid_stability_pct": grid_stability_pct,
                "coolant_inventory_pct": coolant_inventory_pct,
            }
        )

        self.alarms = self._compute_alarms()
        self._update_alarm_events()

        status = self._derive_status()
        if status != self._last_status:
            self._log_event(
                "STATUS_CHANGE",
                message=f"Status changed: {self._last_status} -> {status}",
                details={"from": self._last_status, "to": status},
            )
            self._last_status = status

        self._update_mission(status, dt)
        self._append_history_sample(force=(dt == 0.0))

    def _alarm_severity(self, code: str) -> str:
        if code.startswith("FAULT_"):
            return "warning"
        return ALARM_SEVERITY.get(code, "info")

    def _update_alarm_events(self) -> None:
        current = set(self.alarms)
        raised = sorted(current - self._last_alarms)
        cleared = sorted(self._last_alarms - current)
        for code in raised:
            self._log_event(
                "ALARM_RAISED",
                severity=self._alarm_severity(code),
                message=f"Alarm raised: {code}",
                details={"alarm": code},
            )
        for code in cleared:
            self._log_event(
                "ALARM_CLEARED",
                message=f"Alarm cleared: {code}",
                details={"alarm": code},
            )
            self.alarm_acknowledged.discard(code)
        self._last_alarms = current

    def _update_mission(self, status: str, dt: float) -> None:
        step_conditions = {
            "primary_loop_ready": self.actuators["pump_speed"] >= 40.0 and self.actuators["valve"] >= 35.0,
            "reactor_critical": float(self.metrics["power_mw"]) >= 120.0,
            "turbine_spinup": float(self.metrics["turbine_rpm"]) >= 1200.0,
            "grid_sync": float(self.metrics["electric_mw"]) >= 250.0 and self.actuators["load"] >= 35.0,
        }
        for step, ok in step_conditions.items():
            if ok and not self.mission_steps.get(step, False):
                self.mission_steps[step] = True
                self.score += 12.0
                self._log_event(
                    "MISSION_STEP",
                    message=f"Mission step completed: {step}",
                    details={"step": step},
                )

        critical_alarms = {"CORE_OVERHEAT", "OVERPRESSURE", "SCRAM_ACTIVE"}
        warning_alarms = {"LOW_COOLANT_FLOW", "LOW_STEAM_PRESSURE", "EMERGENCY_INJECT"}
        alarms_set = set(self.alarms)

        if status == "SCRAM":
            self.mission_phase = "emergency_recovery"
            self.stable_time_s = 0.0
            self.score -= 4.0 * dt
        else:
            all_steps_done = all(self.mission_steps.values())
            if not self.mission_steps["primary_loop_ready"]:
                self.mission_phase = "startup_precheck"
            elif not self.mission_steps["reactor_critical"]:
                self.mission_phase = "startup_neutron_rise"
            elif not self.mission_steps["turbine_spinup"]:
                self.mission_phase = "turbine_spinup"
            elif not self.mission_steps["grid_sync"]:
                self.mission_phase = "grid_sync"
            elif all_steps_done:
                stable_window = (
                    1100.0 <= float(self.metrics["power_mw"]) <= 2500.0
                    and 12.0 <= float(self.metrics["pressure_mpa"]) <= 16.0
                    and 460.0 <= float(self.metrics["core_temp_c"]) <= 650.0
                )
                if stable_window and not (alarms_set & critical_alarms):
                    self.stable_time_s += dt
                    self.score += 1.2 * dt
                    if self.stable_time_s >= 60.0:
                        self.mission_phase = "stable_operation"
                    else:
                        self.mission_phase = "power_hold"
                else:
                    self.stable_time_s = max(0.0, self.stable_time_s - dt * 0.7)
                    self.score += 0.2 * dt

        if alarms_set & critical_alarms:
            self.score -= 2.2 * dt
        elif alarms_set & warning_alarms:
            self.score -= 0.9 * dt
        elif alarms_set:
            self.score -= 0.4 * dt

        self.score = clamp(self.score, 0.0, 9999.0)

    def _append_history_sample(self, *, force: bool = False) -> None:
        if not force:
            dt = max(0.0, self.time_s - (self.history[-1]["time_s"] if self.history else 0.0))
            self._history_accum_s += dt
            if self._history_accum_s < self._history_sample_s:
                return
            self._history_accum_s = 0.0

        self.history.append(
            {
                "time_s": round(self.time_s, 2),
                "status": self._derive_status(),
                "phase": self.mission_phase,
                "power_mw": round(float(self.metrics["power_mw"]), 2),
                "core_temp_c": round(float(self.metrics["core_temp_c"]), 2),
                "pressure_mpa": round(float(self.metrics["pressure_mpa"]), 2),
                "electric_mw": round(float(self.metrics["electric_mw"]), 2),
                "alarm_count": len(self.alarms),
                "score": round(self.score, 2),
            }
        )
        if len(self.history) > self._max_history:
            self.history = self.history[-self._max_history :]

    def _safe_to_clear_scram(self) -> bool:
        return (
            float(self.metrics["core_temp_c"]) < 520.0
            and float(self.metrics["pressure_mpa"]) < 14.5
            and float(self.metrics["coolant_flow"]) > 45.0
        )

    def _derive_status(self) -> str:
        if bool(self.controls.get("scram", False)):
            return "SCRAM"
        power = float(self.metrics.get("power_mw", 0.0))
        if power < 80.0:
            return "COLD" if self.scenario == "cold_start" else "STARTUP"
        if power < 900.0:
            return "STARTUP"
        return "RUNNING"

    def _compute_alarms(self) -> List[str]:
        alarms: List[str] = []
        if float(self.metrics["core_temp_c"]) > 650.0:
            alarms.append("CORE_OVERHEAT")
        if float(self.metrics["pressure_mpa"]) > 17.0:
            alarms.append("OVERPRESSURE")
        if float(self.metrics["coolant_flow"]) < 30.0:
            alarms.append("LOW_COOLANT_FLOW")
        if float(self.metrics["steam_pressure_mpa"]) < 3.5 and self.actuators["load"] > 50.0:
            alarms.append("LOW_STEAM_PRESSURE")
        if bool(self.controls["scram"]):
            alarms.append("SCRAM_ACTIVE")
        if bool(self.controls["emergency_inject"]):
            alarms.append("EMERGENCY_INJECT")
        for fault in sorted(self.faults):
            alarms.append(f"FAULT_{fault.upper()}")
        return alarms

    def _log_event(
        self,
        code: str,
        *,
        severity: str = "info",
        message: str = "",
        details: Dict[str, object] | None = None,
    ) -> None:
        event: Dict[str, object] = {
            "time_s": round(self.time_s, 2),
            "code": code,
            "severity": severity,
            "message": message or code,
        }
        if details:
            event["details"] = details
        self.events.append(event)
        if len(self.events) > self._max_events:
            self.events = self.events[-self._max_events :]

    def get_events(self, limit: int = 30, severity: str | None = None) -> List[Dict[str, object]]:
        limit = max(1, min(int(limit), self._max_events))
        selected = self.events
        if severity:
            selected = [event for event in selected if str(event.get("severity")) == severity]
        return [dict(event) for event in selected[-limit:]]

    def get_history(self, limit: int = 120) -> List[Dict[str, object]]:
        limit = max(1, min(int(limit), self._max_history))
        return [dict(item) for item in self.history[-limit:]]

    def _mission_state(self, status: str) -> Dict[str, object]:
        return {
            "phase": self.mission_phase,
            "objective": "Hold stable operation for 60s without critical alarms",
            "score": round(self.score, 2),
            "stable_time_s": round(self.stable_time_s, 2),
            "steps": dict(self.mission_steps),
            "actions_ready": {
                "ack_alarms": len(self.alarms) > 0,
                "quick_start": not bool(self.controls["scram"]),
                "stabilize": not bool(self.controls["scram"]),
                "clear_scram": bool(self.controls["scram"]) and self._safe_to_clear_scram(),
            },
            "status": status,
        }

    def get_state(self) -> Dict[str, object]:
        status = self._derive_status()
        health = {
            "core": 100.0 - (20.0 if "fuel_quality_low" in self.faults else 0.0),
            "cooling": 100.0
            - (25.0 if "pump_degraded" in self.faults else 0.0)
            - (15.0 if "coolant_leak" in self.faults else 0.0),
            "steam": 100.0 - (15.0 if "pressure_spike" in self.faults else 0.0),
            "sensors": 100.0 - (20.0 if "sensor_drift" in self.faults else 0.0),
        }
        health = {k: clamp(v, 40.0, 100.0) for k, v in health.items()}
        alarm_state = [
            {
                "code": code,
                "severity": self._alarm_severity(code),
                "acknowledged": code in self.alarm_acknowledged,
            }
            for code in self.alarms
        ]

        return {
            "time_s": round(self.time_s, 2),
            "scenario": self.scenario,
            "status": status,
            "controls": self._rounded_dict(self.controls),
            "actuators": self._rounded_dict(self.actuators),
            "metrics": self._rounded_dict(self.metrics),
            "alarms": list(self.alarms),
            "alarm_state": alarm_state,
            "faults": sorted(self.faults),
            "health": self._rounded_dict(health),
            "mission": self._mission_state(status),
            "events_tail": self.get_events(limit=8),
        }

    def get_metrics(self) -> Dict[str, object]:
        return {
            "time_s": round(self.time_s, 2),
            "status": "SCRAM" if bool(self.controls["scram"]) else "NORMAL",
            "phase": self.mission_phase,
            "score": round(self.score, 2),
            "power_mw": round(float(self.metrics["power_mw"]), 2),
            "core_temp_c": round(float(self.metrics["core_temp_c"]), 2),
            "pressure_mpa": round(float(self.metrics["pressure_mpa"]), 2),
            "coolant_flow": round(float(self.metrics["coolant_flow"]), 2),
            "steam_pressure_mpa": round(float(self.metrics["steam_pressure_mpa"]), 2),
            "electric_mw": round(float(self.metrics["electric_mw"]), 2),
            "grid_stability_pct": round(float(self.metrics["grid_stability_pct"]), 2),
            "thermal_margin_c": round(float(self.metrics["thermal_margin_c"]), 2),
            "alarm_count": len(self.alarms),
            "alarms": list(self.alarms),
        }

    @staticmethod
    def _rounded_dict(data: Dict[str, float | bool | str]) -> Dict[str, float | bool | str]:
        result: Dict[str, float | bool | str] = {}
        for key, value in data.items():
            if isinstance(value, bool):
                result[key] = value
            elif isinstance(value, (int, float)):
                result[key] = round(float(value), 2)
            else:
                result[key] = value
        return result
