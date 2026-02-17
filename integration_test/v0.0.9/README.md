# Anyware Integration Test v0.0.9 – Reactor Backend

Purpose: provide a deterministic, API-driven backend for the UI integration test (cold start + running). No external dependencies.

## Run

```bash
python3 integration_test/v0.0.9/reactor_backend.py --scenario cold_start
```

Default address: `http://127.0.0.1:8787`

## Endpoints

- `GET /health` → `{ ok: true }`
- `GET /state` → full state (controls, actuators, metrics, alarms)
- `GET /metrics` → key metrics (UI fast polling)
- `GET /catalog` → available scenarios, faults, control ranges
- `POST /control` → update control targets
- `POST /scenario` → reset scenario (`cold_start` / `running`)
- `POST /fault` → enable/disable a fault
- `POST /sim` → pause or set speed

## Example Requests

```bash
curl -s http://127.0.0.1:8787/state
```

```bash
curl -s -X POST http://127.0.0.1:8787/control \
  -H 'Content-Type: application/json' \
  -d '{"rods": 40, "pump_speed": 60, "valve": 55, "load": 30}'
```

```bash
curl -s -X POST http://127.0.0.1:8787/scenario \
  -H 'Content-Type: application/json' \
  -d '{"name":"running"}'
```

```bash
curl -s -X POST http://127.0.0.1:8787/fault \
  -H 'Content-Type: application/json' \
  -d '{"name":"pump_degraded","enabled":true}'
```

```bash
curl -s -X POST http://127.0.0.1:8787/sim \
  -H 'Content-Type: application/json' \
  -d '{"paused": false, "speed": 1.0}'
```

## Scenario Notes

- `cold_start`: rods fully inserted, pumps off, low power.
- `running`: mid-power steady state.

## Faults (UI-friendly)

- `pump_degraded`
- `coolant_leak`
- `valve_stuck`
- `pressure_spike`
- `sensor_drift`
- `fuel_quality_low`

## Files

- `integration_test/v0.0.9/reactor_sim.py` – simulation core
- `integration_test/v0.0.9/reactor_backend.py` – API server
- `integration_test/v0.0.9/README.md` – this file
