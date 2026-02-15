from __future__ import annotations

import uuid


_DEFAULT_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "krpc.anyware")


def _resolve_namespace(namespace) -> uuid.UUID:
    if namespace is None:
        return _DEFAULT_NAMESPACE
    if isinstance(namespace, uuid.UUID):
        return namespace
    return uuid.uuid5(uuid.NAMESPACE_DNS, str(namespace))


def stable_component_id(name: str, *, seed=None, namespace=None) -> str:
    """Return a stable component id.

    - If seed is None, returns name as-is.
    - If seed is provided, append a deterministic UUID5 suffix derived from name+seed.
    """
    base = str(name)
    if seed is None:
        return base
    ns = _resolve_namespace(namespace)
    key = f"{base}:{seed}"
    return f"{base}::{uuid.uuid5(ns, key)}"


class IdFactory:
    """Generate deterministic ids for repeated base names.

    The ids are stable as long as the call order per base name is stable.
    """

    def __init__(self, namespace: str | uuid.UUID | None = None):
        self._namespace = _resolve_namespace(namespace)
        self._counters: dict[str, int] = {}

    def next(self, name: str) -> str:
        base = str(name)
        idx = self._counters.get(base, 0)
        self._counters[base] = idx + 1
        return stable_component_id(base, seed=idx, namespace=self._namespace)
