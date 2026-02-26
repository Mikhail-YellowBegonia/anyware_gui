from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    api_key: str
    base_url: str
    model: str
    timeout_s: int
    stream: bool
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _resolve_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return _repo_root() / path


def load_config(config_path: str | None = None) -> LLMConfig:
    default_path = _repo_root() / "assets" / "_private" / "llm_config.local.json"
    path = _resolve_path(config_path) if config_path else default_path
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))

    api_key_file = raw.get("api_key_file")
    if not api_key_file:
        raise ValueError("config missing 'api_key_file'")

    api_key_path = _resolve_path(api_key_file)
    if not api_key_path.exists():
        raise FileNotFoundError(f"api_key_file not found: {api_key_path}")

    api_key = api_key_path.read_text(encoding="utf-8").strip()
    if not api_key:
        raise ValueError("api_key_file is empty")

    raw_max_tokens = raw.get("max_tokens")
    max_tokens = None if raw_max_tokens is None else int(raw_max_tokens)
    if max_tokens is not None and max_tokens < 2048:
        max_tokens = 2048

    return LLMConfig(
        provider=raw.get("provider", "deepseek"),
        api_key=api_key,
        base_url=raw.get("base_url", "https://api.deepseek.com"),
        model=raw.get("model", "deepseek-chat"),
        timeout_s=int(raw.get("timeout_s", 60)),
        stream=bool(raw.get("stream", True)),
        temperature=raw.get("temperature"),
        top_p=raw.get("top_p"),
        max_tokens=max_tokens,
    )
