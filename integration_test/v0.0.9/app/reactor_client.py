from __future__ import annotations

import json
import time
import urllib.error
import urllib.request


class ReactorClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8787",
        *,
        poll_interval_s: float = 3.0,
        timeout_s: float = 0.5,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.poll_interval_s = float(poll_interval_s)
        self.timeout_s = float(timeout_s)
        self._last_poll = 0.0

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
        return self._get_json("/state")

    def poll_and_log(self) -> None:
        try:
            payload = self.poll_state()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[REACTOR] {ts} ERROR: {exc}")
            return
        except Exception as exc:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[REACTOR] {ts} ERROR: {exc}")
            return

        if payload is None:
            return
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[REACTOR] {ts} GET /state")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
