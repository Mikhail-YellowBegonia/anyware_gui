from __future__ import annotations

import math
from typing import Dict, List


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


class ReactorSim:
    def __init__(self) -> None:
        self.time_s = 0.0
        self.sim_speed = 1.0
        self.paused = False
        self.faults = set()
        self.controls: Dict[str, float | bool] = {}
        self.actuators: Dict[str, float] = {}
        self.metrics: Dict[str, float | str] = {}
        self.alarms: List[str] = []
        self.reset("cold_start")

    def reset(self, scenario: str) -> None:
        if scenario not in SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario}")
        self.scenario = scenario
        self.time_s = 0.0
        self.faults.clear()
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
        self.alarms = []

    def set_controls(self, **kwargs: float | bool) -> None:
        for key, value in kwargs.items():
            if key not in self.controls:
                continue
            if isinstance(self.controls[key], bool):
                self.controls[key] = bool(value)
                continue
            if not isinstance(value, (int, float)):
                continue
            if key == "rods":
                self.controls[key] = clamp(float(value), 0.0, 100.0)
            elif key in ("pump_speed", "valve", "load"):
                self.controls[key] = clamp(float(value), 0.0, 100.0)
            else:
                self.controls[key] = float(value)

    def set_fault(self, name: str, enabled: bool) -> None:
        if name not in FAULTS:
            return
        if enabled:
            self.faults.add(name)
        else:
            self.faults.discard(name)

    def set_sim(self, *, paused: bool | None = None, speed: float | None = None) -> None:
        if paused is not None:
            self.paused = bool(paused)
        if speed is not None:
            self.sim_speed = clamp(float(speed), 0.1, 5.0)

    def step(self, dt: float) -> None:
        if self.paused:
            return
        dt = max(0.0, dt)
        self.time_s += dt

        rods_target = float(self.controls["rods"])
        pump_target = float(self.controls["pump_speed"])
        valve_target = float(self.controls["valve"])
        load_target = float(self.controls["load"])

        # Actuator inertia (slow but visible)
        self.actuators["rods"] = approach(self.actuators["rods"], rods_target, 25.0, dt)
        self.actuators["pump_speed"] = approach(self.actuators["pump_speed"], pump_target, 20.0, dt)
        self.actuators["valve"] = approach(self.actuators["valve"], valve_target, 18.0, dt)
        self.actuators["load"] = approach(self.actuators["load"], load_target, 15.0, dt)

        reactivity = clamp(1.0 - self.actuators["rods"] / 100.0, 0.0, 1.0)
        if self.controls["scram"]:
            reactivity = 0.0
        if self.controls["emergency_inject"]:
            reactivity *= 0.2

        pump_eff = 1.0
        if "pump_degraded" in self.faults:
            pump_eff *= 0.6
        if "coolant_leak" in self.faults:
            pump_eff *= 0.7

        valve_eff = 1.0
        if "valve_stuck" in self.faults:
            valve_eff *= 0.55

        power_derate = 0.0
        if "fuel_quality_low" in self.faults:
            power_derate = 0.18

        pressure_bias = 0.0
        if "pressure_spike" in self.faults:
            pressure_bias = 1.4

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
        power_mw = float(self.metrics["power_mw"])
        power_mw = approach(power_mw, power_target, 160.0, dt)

        core_temp_target = 260.0 + power_mw / 25.0 - cooling_factor * 60.0
        core_temp_target = clamp(core_temp_target, 220.0, 880.0)
        core_temp_c = float(self.metrics["core_temp_c"])
        core_temp_c = approach(core_temp_c, core_temp_target, 18.0, dt)

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

        # Apply mild deterministic noise
        core_temp_c += noise
        pressure_mpa += noise * 0.05
        steam_pressure_mpa += noise * 0.04

        # Auto SCRAM on extreme conditions
        if core_temp_c > 740.0 or pressure_mpa > 18.0 or coolant_flow < 8.0:
            self.controls["scram"] = True

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
            }
        )

        self.alarms = self._compute_alarms()

    def _compute_alarms(self) -> List[str]:
        alarms: List[str] = []
        if self.metrics["core_temp_c"] > 650.0:
            alarms.append("CORE_OVERHEAT")
        if self.metrics["pressure_mpa"] > 17.0:
            alarms.append("OVERPRESSURE")
        if self.metrics["coolant_flow"] < 30.0:
            alarms.append("LOW_COOLANT_FLOW")
        if self.metrics["steam_pressure_mpa"] < 3.5 and self.actuators["load"] > 50.0:
            alarms.append("LOW_STEAM_PRESSURE")
        if self.controls["scram"]:
            alarms.append("SCRAM_ACTIVE")
        if self.controls["emergency_inject"]:
            alarms.append("EMERGENCY_INJECT")
        for fault in sorted(self.faults):
            alarms.append(f"FAULT_{fault.upper()}")
        return alarms

    def get_state(self) -> Dict[str, object]:
        status = "RUNNING"
        if self.controls["scram"]:
            status = "SCRAM"
        elif self.metrics["power_mw"] < 80.0:
            status = "COLD" if self.scenario == "cold_start" else "STARTUP"
        elif self.metrics["power_mw"] < 900.0:
            status = "STARTUP"

        health = {
            "core": 100.0 - (20.0 if "fuel_quality_low" in self.faults else 0.0),
            "cooling": 100.0 - (25.0 if "pump_degraded" in self.faults else 0.0) - (15.0 if "coolant_leak" in self.faults else 0.0),
            "steam": 100.0 - (15.0 if "pressure_spike" in self.faults else 0.0),
            "sensors": 100.0 - (20.0 if "sensor_drift" in self.faults else 0.0),
        }
        health = {k: clamp(v, 40.0, 100.0) for k, v in health.items()}

        return {
            "time_s": round(self.time_s, 2),
            "scenario": self.scenario,
            "status": status,
            "controls": self._rounded_dict(self.controls),
            "actuators": self._rounded_dict(self.actuators),
            "metrics": self._rounded_dict(self.metrics),
            "alarms": list(self.alarms),
            "faults": sorted(self.faults),
            "health": self._rounded_dict(health),
        }

    def get_metrics(self) -> Dict[str, object]:
        return {
            "time_s": round(self.time_s, 2),
            "status": "SCRAM" if self.controls["scram"] else "NORMAL",
            "power_mw": round(float(self.metrics["power_mw"]), 2),
            "core_temp_c": round(float(self.metrics["core_temp_c"]), 2),
            "pressure_mpa": round(float(self.metrics["pressure_mpa"]), 2),
            "coolant_flow": round(float(self.metrics["coolant_flow"]), 2),
            "steam_pressure_mpa": round(float(self.metrics["steam_pressure_mpa"]), 2),
            "electric_mw": round(float(self.metrics["electric_mw"]), 2),
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
