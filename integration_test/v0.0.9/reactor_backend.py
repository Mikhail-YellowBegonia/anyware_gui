from __future__ import annotations

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from reactor_sim import ACTIONS, FAULTS, SCENARIOS, ReactorSim


CONTROL_NUMERIC_KEYS = ("rods", "pump_speed", "valve", "load")
CONTROL_BOOLEAN_KEYS = ("scram", "emergency_inject")
SIM_SPEED_MIN = 0.1
SIM_SPEED_MAX = 5.0


class ReactorBackend:
    def __init__(self, *, scenario: str = "cold_start", tick_s: float = 0.2) -> None:
        if scenario not in SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario}")
        self._lock = threading.RLock()
        self._sim = ReactorSim()
        self._sim.reset(scenario)
        self._tick_s = max(0.01, float(tick_s))
        self._stop_event = threading.Event()
        self._worker: threading.Thread | None = None

    def start(self) -> None:
        if self._worker is not None and self._worker.is_alive():
            return
        self._stop_event.clear()
        self._worker = threading.Thread(target=self._tick_loop, name="reactor-sim-loop", daemon=True)
        self._worker.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._worker is not None and self._worker.is_alive():
            self._worker.join(timeout=1.0)
        self._worker = None

    def _tick_loop(self) -> None:
        last_ts = time.monotonic()
        while True:
            if self._stop_event.wait(self._tick_s):
                return
            now_ts = time.monotonic()
            dt = max(0.0, now_ts - last_ts)
            last_ts = now_ts
            self.tick(dt)

    def tick(self, dt: float | None = None) -> None:
        step_dt = self._tick_s if dt is None else max(0.0, float(dt))
        with self._lock:
            sim_dt = step_dt * float(self._sim.sim_speed)
            self._sim.step(sim_dt)

    def _state_payload(self) -> tuple[dict, int]:
        with self._lock:
            state = self._sim.get_state()
        return {"ok": True, "state": state}, 200

    def get_health(self) -> tuple[dict, int]:
        return {"ok": True}, 200

    def get_state(self) -> tuple[dict, int]:
        return self._state_payload()

    def get_metrics(self) -> tuple[dict, int]:
        with self._lock:
            metrics = self._sim.get_metrics()
        return {"ok": True, "metrics": metrics}, 200

    def get_catalog(self) -> tuple[dict, int]:
        return (
            {
                "ok": True,
                "catalog": {
                    "scenarios": dict(SCENARIOS),
                    "faults": dict(FAULTS),
                    "controls": {
                        "rods": {"type": "number", "min": 0.0, "max": 100.0},
                        "pump_speed": {"type": "number", "min": 0.0, "max": 100.0},
                        "valve": {"type": "number", "min": 0.0, "max": 100.0},
                        "load": {"type": "number", "min": 0.0, "max": 100.0},
                        "scram": {"type": "boolean"},
                        "emergency_inject": {"type": "boolean"},
                    },
                    "sim": {
                        "speed": {"type": "number", "min": SIM_SPEED_MIN, "max": SIM_SPEED_MAX},
                        "paused": {"type": "boolean"},
                    },
                    "actions": dict(ACTIONS),
                },
            },
            200,
        )

    def get_events(self, *, limit: int = 30, severity: str | None = None) -> tuple[dict, int]:
        with self._lock:
            events = self._sim.get_events(limit=limit, severity=severity)
        return {"ok": True, "events": events}, 200

    def get_history(self, *, limit: int = 120) -> tuple[dict, int]:
        with self._lock:
            history = self._sim.get_history(limit=limit)
        return {"ok": True, "history": history}, 200

    def post_control(self, payload: dict) -> tuple[dict, int]:
        updates: dict[str, float | bool] = {}
        for key in CONTROL_NUMERIC_KEYS:
            if key in payload:
                value = payload[key]
                if not isinstance(value, (int, float)):
                    return {"ok": False, "error": f"control.{key} must be number"}, 400
                updates[key] = float(value)

        for key in CONTROL_BOOLEAN_KEYS:
            if key in payload:
                value = payload[key]
                if not isinstance(value, bool):
                    return {"ok": False, "error": f"control.{key} must be boolean"}, 400
                updates[key] = value

        with self._lock:
            self._sim.set_controls(**updates)
            self._sim.step(0.0)
        return self._state_payload()

    def post_scenario(self, payload: dict) -> tuple[dict, int]:
        name = payload.get("name")
        if not isinstance(name, str) or name not in SCENARIOS:
            return {"ok": False, "error": f"Invalid scenario: {name!r}"}, 400
        with self._lock:
            self._sim.reset(name)
        return self._state_payload()

    def post_fault(self, payload: dict) -> tuple[dict, int]:
        name = payload.get("name")
        if not isinstance(name, str):
            return {"ok": False, "error": "fault.name is required"}, 400
        if name == "clear_all":
            with self._lock:
                self._sim.faults.clear()
                self._sim.step(0.0)
            return self._state_payload()

        if name not in FAULTS:
            return {"ok": False, "error": f"Unknown fault: {name}"}, 400

        enabled = payload.get("enabled", True)
        if not isinstance(enabled, bool):
            return {"ok": False, "error": "fault.enabled must be boolean"}, 400

        with self._lock:
            self._sim.set_fault(name, enabled)
            self._sim.step(0.0)
        return self._state_payload()

    def post_sim(self, payload: dict) -> tuple[dict, int]:
        paused = payload.get("paused", None)
        speed = payload.get("speed", None)

        if paused is not None and not isinstance(paused, bool):
            return {"ok": False, "error": "sim.paused must be boolean"}, 400
        if speed is not None and not isinstance(speed, (int, float)):
            return {"ok": False, "error": "sim.speed must be number"}, 400

        with self._lock:
            self._sim.set_sim(
                paused=paused if isinstance(paused, bool) else None,
                speed=float(speed) if isinstance(speed, (int, float)) else None,
            )
        return self._state_payload()

    def post_action(self, payload: dict) -> tuple[dict, int]:
        name = payload.get("name")
        if not isinstance(name, str):
            return {"ok": False, "error": "action.name is required"}, 400
        with self._lock:
            ok, message = self._sim.execute_action(name)
            self._sim.step(0.0)
            state = self._sim.get_state()
        status = 200 if ok else 400
        return {"ok": ok, "message": message, "state": state}, status


class ReactorServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        RequestHandlerClass: type[BaseHTTPRequestHandler],
        backend: ReactorBackend,
    ) -> None:
        self.backend = backend
        super().__init__(server_address, RequestHandlerClass)


class ReactorRequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    @property
    def backend(self) -> ReactorBackend:
        return self.server.backend  # type: ignore[attr-defined]

    def _read_json(self) -> tuple[dict, str | None]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}, None
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}, "Invalid JSON body"
        if not isinstance(data, dict):
            return {}, "JSON body must be object"
        return data, None

    def _write_json(self, payload: dict, status: int = 200) -> None:
        self._set_headers(status)
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler naming)
        self._set_headers(204)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        def _query_int(name: str, default: int, lo: int, hi: int) -> int:
            raw = query.get(name, [str(default)])[0]
            try:
                value = int(raw)
            except ValueError:
                return default
            return max(lo, min(hi, value))

        if path == "/health":
            payload, status = self.backend.get_health()
            self._write_json(payload, status=status)
            return
        if path == "/state":
            payload, status = self.backend.get_state()
            self._write_json(payload, status=status)
            return
        if path == "/metrics":
            payload, status = self.backend.get_metrics()
            self._write_json(payload, status=status)
            return
        if path == "/catalog":
            payload, status = self.backend.get_catalog()
            self._write_json(payload, status=status)
            return
        if path == "/events":
            limit = _query_int("limit", default=30, lo=1, hi=200)
            severity = query.get("severity", [None])[0]
            payload, status = self.backend.get_events(limit=limit, severity=severity)
            self._write_json(payload, status=status)
            return
        if path == "/history":
            limit = _query_int("limit", default=120, lo=1, hi=240)
            payload, status = self.backend.get_history(limit=limit)
            self._write_json(payload, status=status)
            return
        self._write_json({"ok": False, "error": "Not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        payload, error = self._read_json()
        if error is not None:
            self._write_json({"ok": False, "error": error}, status=400)
            return

        if path == "/control":
            result, status = self.backend.post_control(payload)
            self._write_json(result, status=status)
            return
        if path == "/scenario":
            result, status = self.backend.post_scenario(payload)
            self._write_json(result, status=status)
            return
        if path == "/fault":
            result, status = self.backend.post_fault(payload)
            self._write_json(result, status=status)
            return
        if path == "/sim":
            result, status = self.backend.post_sim(payload)
            self._write_json(result, status=status)
            return
        if path == "/action":
            result, status = self.backend.post_action(payload)
            self._write_json(result, status=status)
            return
        self._write_json({"ok": False, "error": "Not found"}, status=404)

    def log_message(self, fmt: str, *args) -> None:
        return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Anyware v0.0.9 Reactor Backend")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8787, help="Bind port")
    parser.add_argument(
        "--scenario",
        default="cold_start",
        choices=sorted(SCENARIOS.keys()),
        help="Initial reactor scenario",
    )
    parser.add_argument("--tick", type=float, default=0.2, help="Simulation tick interval in seconds")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    backend = ReactorBackend(scenario=args.scenario, tick_s=args.tick)
    backend.start()
    server = ReactorServer((args.host, args.port), ReactorRequestHandler, backend)
    print(
        f"Reactor backend running on http://{args.host}:{args.port} "
        f"(scenario={args.scenario}, tick={backend._tick_s:.2f}s)"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        backend.stop()


if __name__ == "__main__":
    main()
