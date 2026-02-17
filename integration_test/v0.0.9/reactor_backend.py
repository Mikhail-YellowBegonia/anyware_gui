from __future__ import annotations

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from reactor_sim import FAULTS, SCENARIOS, ReactorSim


class ReactorServer(ThreadingHTTPServer):
    def __init__(self, server_address, RequestHandlerClass, sim: ReactorSim):
        super().__init__(server_address, RequestHandlerClass)
        self.sim = sim


class ReactorRequestHandler(BaseHTTPRequestHandler):
    server: ReactorServer  # type: ignore[assignment]

    def _set_headers(self, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _write_json(self, payload: dict, status: int = 200) -> None:
        self._set_headers(status)
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler naming)
        self._set_headers(204)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            self._write_json({"ok": True})
            return
        if path == "/state":
            self._write_json({"ok": True, "state": self.server.sim.get_state()})
            return
        if path == "/metrics":
            self._write_json({"ok": True, "metrics": self.server.sim.get_metrics()})
            return
        if path == "/catalog":
            self._write_json(
                {
                    "ok": True,
                    "scenarios": SCENARIOS,
                    "faults": FAULTS,
                    "controls": {
                        "rods": {"min": 0, "max": 100},
                        "pump_speed": {"min": 0, "max": 100},
                        "valve": {"min": 0, "max": 100},
                        "load": {"min": 0, "max": 100},
                        "scram": {"type": "bool"},
                        "emergency_inject": {"type": "bool"},
                    },
                }
            )
            return
        self._write_json({"ok": False, "error": "Not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        payload = self._read_json()

        if path == "/control":
            self.server.sim.set_controls(**payload)
            self._write_json({"ok": True, "state": self.server.sim.get_state()})
            return

        if path == "/scenario":
            name = payload.get("name")
            if name not in SCENARIOS:
                self._write_json({"ok": False, "error": "Unknown scenario"}, status=400)
                return
            self.server.sim.reset(name)
            self._write_json({"ok": True, "state": self.server.sim.get_state()})
            return

        if path == "/fault":
            name = payload.get("name")
            enabled = bool(payload.get("enabled", True))
            if name == "clear_all":
                for fault in list(self.server.sim.faults):
                    self.server.sim.set_fault(fault, False)
                self._write_json({"ok": True, "state": self.server.sim.get_state()})
                return
            if name not in FAULTS:
                self._write_json({"ok": False, "error": "Unknown fault"}, status=400)
                return
            self.server.sim.set_fault(name, enabled)
            self._write_json({"ok": True, "state": self.server.sim.get_state()})
            return

        if path == "/sim":
            paused = payload.get("paused")
            speed = payload.get("speed")
            self.server.sim.set_sim(paused=paused, speed=speed)
            self._write_json({"ok": True, "state": self.server.sim.get_state()})
            return

        self._write_json({"ok": False, "error": "Not found"}, status=404)

    def log_message(self, fmt: str, *args) -> None:
        # Keep server output clean for test runs.
        return


def run_sim_loop(sim: ReactorSim, tick_s: float) -> None:
    last = time.monotonic()
    while True:
        now = time.monotonic()
        dt = now - last
        last = now
        sim.step(dt * sim.sim_speed)
        time.sleep(tick_s)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Anyware v0.0.9 Reactor Backend")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8787, help="Bind port")
    parser.add_argument("--tick", type=float, default=0.2, help="Simulation tick seconds")
    parser.add_argument("--scenario", default="cold_start", choices=SCENARIOS.keys())
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sim = ReactorSim()
    sim.reset(args.scenario)

    thread = threading.Thread(target=run_sim_loop, args=(sim, args.tick), daemon=True)
    thread.start()

    server = ReactorServer((args.host, args.port), ReactorRequestHandler, sim)
    print(f"Reactor backend running on http://{args.host}:{args.port}")
    print(f"Scenario: {args.scenario} | Tick: {args.tick}s")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
