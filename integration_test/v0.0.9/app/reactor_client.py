from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse


class ReactorClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8787",
        *,
        poll_interval_s: float = 3.0,
        timeout_s: float = 0.5,
        comms_timeout_s: float | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.poll_interval_s = float(poll_interval_s)
        self.timeout_s = float(timeout_s)
        self.comms_timeout_s = (
            float(comms_timeout_s)
            if comms_timeout_s is not None
            else max(2.0, self.poll_interval_s * 2.5)
        )
        self._last_poll = 0.0
        self._last_success = 0.0
        self._last_latency_ms: float | None = None
        self._last_error: str | None = None
        self._last_payload: dict | None = None

        parsed = urlparse(self.base_url)
        if parsed.port is not None:
            self.port = int(parsed.port)
        else:
            self.port = 443 if parsed.scheme == "https" else 80

    def _get_json(self, path: str) -> dict:
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
            data = resp.read().decode("utf-8", errors="replace")
        return json.loads(data)

    def poll_state(self) -> dict | None:
        now = time.time()
        if now - self._last_poll < self.poll_interval_s:
            return None
        self._last_poll = now
        start = time.perf_counter()
        payload = self._get_json("/state")
        self._last_latency_ms = (time.perf_counter() - start) * 1000.0
        self._last_success = time.time()
        self._last_error = None
        self._last_payload = payload
        return payload

    def health_check(self) -> bool:
        try:
            start = time.perf_counter()
            payload = self._get_json("/health")
            self._last_latency_ms = (time.perf_counter() - start) * 1000.0
            self._last_success = time.time()
            self._last_error = None
            self._last_payload = payload
            return bool(payload.get("ok", True))
        except Exception as exc:
            self.mark_error(exc)
            return False

    def mark_error(self, exc: Exception) -> None:
        self._last_error = str(exc)

    def comms_ok(self, now: float | None = None) -> bool:
        if self._last_success <= 0:
            return False
        now = time.time() if now is None else now
        return (now - self._last_success) <= self.comms_timeout_s

    @property
    def last_latency_ms(self) -> float | None:
        return self._last_latency_ms

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def poll_and_log(self) -> None:
        try:
            payload = self.poll_state()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            self.mark_error(exc)
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[REACTOR] {ts} ERROR: {exc}")
            return
        except Exception as exc:
            self.mark_error(exc)
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[REACTOR] {ts} ERROR: {exc}")
            return

        if payload is None:
            return
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[REACTOR] {ts} GET /state")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
