# Reactor Backend Spec (v0.0.9)

Doc purpose: list all available inputs/outputs and summarize the simplified reactor principles used by the simulator, for UI design reference.

## Runtime Overview

- Backend file: `integration_test/v0.0.9/reactor_backend.py`
- Simulator core: `integration_test/v0.0.9/reactor_sim.py`
- Default address: `http://127.0.0.1:8787`
- Default tick: `0.2s`
- Speed range: `0.1` to `5.0`

## Endpoints

- `GET /health`
- `GET /state`
- `GET /metrics`
- `GET /catalog`
- `GET /events`
- `GET /history`
- `POST /control`
- `POST /scenario`
- `POST /fault`
- `POST /sim`
- `POST /action`

## Output: `GET /state`

Response shape:

```json
{
  "ok": true,
  "state": {
    "time_s": 12.4,
    "scenario": "running",
    "status": "RUNNING",
    "controls": { ... },
    "actuators": { ... },
    "metrics": { ... },
    "alarms": [ ... ],
    "faults": [ ... ],
    "health": { ... }
  }
}
```

### `state` fields

- `time_s`: elapsed simulation time in seconds.
- `scenario`: `cold_start` or `running`.
- `status`: `RUNNING`, `SCRAM`, `COLD`, `STARTUP`.
- `controls`: last commanded targets (input setpoints).
- `actuators`: actual achieved values after inertia.
- `metrics`: simulated physical values.
- `alarms`: active alarm codes.
- `faults`: active fault keys.
- `health`: subsystem health scores.
- `mission`: pseudo-game mission state (`phase`, `score`, `steps`, `actions_ready`).
- `alarm_state`: alarm list with acknowledge state.
- `events_tail`: recent event entries for lightweight UI updates.

### `controls`

- `rods`: 0–100, control rod insertion (%). 100 = fully inserted.
- `pump_speed`: 0–100 (%).
- `valve`: 0–100 (%).
- `load`: 0–100 (%).
- `scram`: boolean, emergency shutdown.
- `emergency_inject`: boolean, emergency coolant injection.

### `actuators`

- `rods`: 0–100, actual rod position.
- `pump_speed`: 0–100, actual pump speed.
- `valve`: 0–100, actual valve opening.
- `load`: 0–100, actual electrical load.

### `metrics`

- `power_mw`: thermal power, 0–3000 MW.
- `core_temp_c`: core temperature, roughly 220–880 °C.
- `coolant_in_c`: coolant inlet temperature, °C.
- `coolant_out_c`: coolant outlet temperature, °C.
- `pressure_mpa`: primary pressure, ~9–19 MPa.
- `steam_pressure_mpa`: secondary steam pressure, ~1–9 MPa.
- `coolant_flow`: 0–100 (% effective flow).
- `turbine_rpm`: turbine speed, roughly 0–5000 RPM.
- `electric_mw`: electric output, roughly 0–1000 MW.
- `neutron_flux`: 0–1 (normalized).

### `alarms`

- `CORE_OVERHEAT`
- `OVERPRESSURE`
- `LOW_COOLANT_FLOW`
- `LOW_STEAM_PRESSURE`
- `SCRAM_ACTIVE`
- `EMERGENCY_INJECT`
- `FAULT_<FAULT_NAME>`

### `faults`

- `pump_degraded`
- `coolant_leak`
- `valve_stuck`
- `pressure_spike`
- `sensor_drift`
- `fuel_quality_low`

### `health`

- `core`: 40–100
- `cooling`: 40–100
- `steam`: 40–100
- `sensors`: 40–100

### `mission`

- `phase`: current mission phase (`startup_precheck`, `startup_neutron_rise`, `turbine_spinup`, `grid_sync`, `power_hold`, `stable_operation`, `emergency_recovery`).
- `objective`: current objective text.
- `score`: operator score (0+).
- `stable_time_s`: accumulated stable operation time.
- `steps`: startup checklist booleans.
- `actions_ready`: UI hints for action buttons.

### `alarm_state`

Each item:
- `code`: alarm code
- `severity`: `critical` / `warning` / `info`
- `acknowledged`: whether operator acknowledged the alarm

## Output: `GET /metrics`

Response shape:

```json
{
  "ok": true,
  "metrics": {
    "time_s": 12.4,
    "status": "NORMAL",
    "power_mw": 2100.0,
    "core_temp_c": 560.2,
    "pressure_mpa": 15.1,
    "coolant_flow": 78.0,
    "steam_pressure_mpa": 6.5,
    "electric_mw": 690.0,
    "alarms": ["LOW_STEAM_PRESSURE"]
  }
}
```

Notes:
- `status` here is only `NORMAL` or `SCRAM`.
- Use this endpoint for high-frequency UI polling.
- Includes `phase`, `score`, `grid_stability_pct`, `thermal_margin_c`, and `alarm_count`.

## Output: `GET /catalog`

- `scenarios`: available scenario names.
- `faults`: available fault keys and descriptions.
- `controls`: numeric ranges and types.
- `actions`: operator actions and descriptions.

## Output: `GET /events`

Query params:
- `limit`: 1–200 (default 30)
- `severity`: optional filter (`critical` / `warning` / `info`)

Response:
```json
{
  "ok": true,
  "events": [
    {
      "time_s": 42.6,
      "code": "ALARM_RAISED",
      "severity": "warning",
      "message": "Alarm raised: LOW_COOLANT_FLOW",
      "details": { "alarm": "LOW_COOLANT_FLOW" }
    }
  ]
}
```

## Output: `GET /history`

Query params:
- `limit`: 1–240 (default 120)

Response items contain:
- `time_s`, `status`, `phase`, `power_mw`, `core_temp_c`, `pressure_mpa`, `electric_mw`, `alarm_count`, `score`

## Input: `POST /control`

Payload fields (any subset is allowed):

- `rods`: 0–100
- `pump_speed`: 0–100
- `valve`: 0–100
- `load`: 0–100
- `scram`: boolean
- `emergency_inject`: boolean

Response returns full `state`.

## Input: `POST /scenario`

Payload:

- `name`: `cold_start` or `running`

Resets the sim and returns full `state`.

## Input: `POST /fault`

Payload:

- `name`: fault key, or `clear_all`
- `enabled`: boolean (default `true`)

Returns full `state`.

## Input: `POST /sim`

Payload:

- `paused`: boolean
- `speed`: 0.1–5.0

Returns full `state`.

## Input: `POST /action`

Payload:
- `name`: action name

Supported actions:
- `ack_alarms`
- `quick_start`
- `stabilize`
- `clear_scram`

Response:
```json
{
  "ok": true,
  "message": "Quick-start setpoints applied",
  "state": { ... }
}
```

## Reactor Principles (Simplified, UI-Friendly)

This simulator is intentionally simplified and deterministic. It is meant for UI layout and interaction testing, not physical accuracy.

### 1) Power, Reactivity, and Control Rods

- Control rods reduce reactivity.
- Rod insertion 100% means near-zero power.
- Rod withdrawal increases power, which raises temperature and pressure.

### 2) Cooling Loop and Heat Removal

- Pumps and valves increase coolant flow.
- Higher flow removes more heat, lowering core temperature.
- Low flow increases temperatures and pressure, causing alarms.

### 3) Steam and Turbine Output

- Higher core power generates more steam pressure.
- Steam pressure drives turbine RPM.
- Electrical output scales with power and load setting.

### 4) Load Effects

- Higher load draws more electrical output.
- Load changes affect turbine RPM and pressure stability.

### 5) Safety Logic

- High temperature or pressure triggers SCRAM.
- SCRAM forces power to zero and sets `SCRAM_ACTIVE` alarm.
- Emergency injection reduces reactivity further.

### 6) Faults (UI-Driven Behavior)

- `pump_degraded`: reduces effective cooling.
- `coolant_leak`: lowers flow and raises temperature.
- `valve_stuck`: limits valve opening.
- `pressure_spike`: adds pressure bias.
- `sensor_drift`: adds mild oscillation to readings.
- `fuel_quality_low`: reduces max power.

## UI Design Suggestions

- Keep primary dashboards for core, cooling, steam, and electrical sections.
- Show both `controls` (setpoint) and `actuators` (actual) so users see inertia.
- Use alarm panel fed by `alarms` list.
- Use `health` for subsystem status lights or progress bars.
- Provide a scenario switcher (`cold_start`, `running`).
- Offer a fault toggle panel for each fault key.
- Avoid heavy animation; use slow updates and stable gauges.

## Notes on Determinism

- The simulator uses deterministic math, no randomness.
- Minor oscillations are sine-based and repeatable.
- This allows UI developers to compare runs reliably.
