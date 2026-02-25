from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path


def _bootstrap_repo_root() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


def _lazy_imports():
    from core.anyware.nonstandard_llm.client import DeepSeekClient, render_tool_event
    from core.anyware.nonstandard_llm.config import load_config
    from core.anyware.nonstandard_llm.types import ToolCallEvent

    return DeepSeekClient, ToolCallEvent, render_tool_event, load_config


def _build_messages(system_prompt: str | None, user_prompt: str) -> list[dict]:
    messages: list[dict] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    return messages


def _default_system_path() -> Path:
    return Path(__file__).resolve().parent / "prompts" / "system.txt"


def _prompts_dir() -> Path:
    return Path(__file__).resolve().parent / "prompts"


def _load_system_prompt(path: Path) -> str | None:
    if not path.exists():
        print(f"Warning: system prompt file not found: {path}", file=sys.stderr)
        return None
    content = path.read_text(encoding="utf-8").strip()
    return content or None


def _load_prompt_by_name(name: str) -> str:
    if not name:
        raise ValueError("prompt name is empty")
    filename = name if name.endswith(".txt") else f"{name}.txt"
    path = _prompts_dir() / filename
    if not path.exists():
        raise FileNotFoundError(f"prompt file not found: {path}")
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"prompt file is empty: {path}")
    return content


def _load_prompts_by_names(raw_names: str) -> str:
    names = [chunk.strip() for chunk in raw_names.split(",") if chunk.strip()]
    if not names:
        raise ValueError("no prompt names provided")
    parts = [_load_prompt_by_name(name) for name in names]
    return "\n".join(parts).strip()


def _show_help() -> None:
    print("Commands:", file=sys.stderr)
    print("  /help    Show commands", file=sys.stderr)
    print("  /exit    Exit session", file=sys.stderr)
    print("  /reset   Clear conversation history", file=sys.stderr)
    print("  /reload  Reload system prompt file", file=sys.stderr)
    print("  /system  Show current system prompt", file=sys.stderr)


def _stream_once(client, messages: list[dict], ToolCallEvent, render_tool_event, prefix: str | None = None) -> str:
    response_parts: list[str] = []
    tool_call_seen = False

    if prefix:
        print(prefix, end="", flush=True)
    for event in client.stream_chat(messages=messages):
        if isinstance(event, ToolCallEvent):
            render_tool_event(event)
            tool_call_seen = True
            break
        response_parts.append(event)
        sys.stdout.write(event)
        sys.stdout.flush()

    sys.stdout.write("\n")
    sys.stdout.flush()

    if tool_call_seen and not response_parts:
        return "[tool_call_placeholder]"
    return "".join(response_parts)


def _load_system_prompt_from_spec(prompt_spec: tuple[str, str] | None) -> str | None:
    if not prompt_spec:
        return None
    kind, value = prompt_spec
    if kind == "names":
        return _load_prompts_by_names(value)
    if kind == "file":
        return _load_system_prompt(Path(value))
    raise ValueError(f"Unknown prompt spec kind: {kind}")


def _run_repl(
    client,
    system_prompt: str | None,
    prompt_spec: tuple[str, str] | None,
    ToolCallEvent,
    render_tool_event,
) -> int:
    messages: list[dict] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    print("Enter message. Use /help for commands.", file=sys.stderr)
    while True:
        try:
            user_input = input(">> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("", file=sys.stderr)
            return 0

        if not user_input:
            continue

        if user_input.startswith("/"):
            command = user_input[1:].strip().lower()
            if command in {"exit", "quit"}:
                return 0
            if command == "help":
                _show_help()
                continue
            if command == "reset":
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                print("History cleared.", file=sys.stderr)
                continue
            if command == "reload":
                if not prompt_spec:
                    print("No prompt file configured to reload.", file=sys.stderr)
                    continue
                system_prompt = _load_system_prompt_from_spec(prompt_spec)
                if messages and messages[0].get("role") == "system":
                    if system_prompt:
                        messages[0]["content"] = system_prompt
                    else:
                        messages.pop(0)
                elif system_prompt:
                    messages.insert(0, {"role": "system", "content": system_prompt})
                print("System prompt reloaded.", file=sys.stderr)
                continue
            if command == "system":
                if system_prompt:
                    print(system_prompt, file=sys.stderr)
                else:
                    print("(no system prompt loaded)", file=sys.stderr)
                continue
            print(f"Unknown command: {user_input}", file=sys.stderr)
            continue

        messages.append({"role": "user", "content": user_input})
        assistant_text = _stream_once(client, messages, ToolCallEvent, render_tool_event, prefix="AI: ")
        messages.append({"role": "assistant", "content": assistant_text})


def main() -> int:
    _bootstrap_repo_root()
    DeepSeekClient, ToolCallEvent, render_tool_event, load_config = _lazy_imports()

    parser = argparse.ArgumentParser(description="DeepSeek streaming terminal test")
    parser.add_argument("--config", default=None, help="Path to config JSON")
    parser.add_argument("--prompt", default=None, help="User prompt (if omitted, read stdin)")
    parser.add_argument("--system", default=None, help="Optional system prompt")
    parser.add_argument(
        "--system-file",
        default=None,
        help="System prompt file path (default: prompts/system.txt)",
    )
    parser.add_argument(
        "--prompts",
        default=None,
        help="Comma-separated prompt names from prompts/ (e.g. plain,system)",
    )
    parser.add_argument("--model", default=None, help="Override model")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--base-url", default=None)
    args = parser.parse_args()

    if args.prompts:
        prompt_spec = ("names", args.prompts)
        system_prompt = _load_system_prompt_from_spec(prompt_spec)
    else:
        system_path = Path(args.system_file) if args.system_file else _default_system_path()
        prompt_spec = ("file", str(system_path))
        system_prompt = _load_system_prompt_from_spec(prompt_spec)

    if args.system:
        system_prompt = args.system
        prompt_spec = None

    config = load_config(args.config)
    if args.model:
        config = replace(config, model=args.model)
    if args.temperature is not None:
        config = replace(config, temperature=args.temperature)
    if args.max_tokens is not None:
        config = replace(config, max_tokens=args.max_tokens)
    if args.base_url is not None:
        config = replace(config, base_url=args.base_url)

    client = DeepSeekClient(config)

    try:
        if args.prompt is not None:
            messages = _build_messages(system_prompt, args.prompt)
            assistant_text = _stream_once(client, messages, ToolCallEvent, render_tool_event)
            messages.append({"role": "assistant", "content": assistant_text})
        elif sys.stdin.isatty():
            return _run_repl(client, system_prompt, prompt_spec, ToolCallEvent, render_tool_event)
        else:
            prompt = sys.stdin.read().strip()
            if not prompt:
                print("Prompt is required (use --prompt or stdin).", file=sys.stderr)
                return 1
            messages = _build_messages(system_prompt, prompt)
            assistant_text = _stream_once(client, messages, ToolCallEvent, render_tool_event)
            messages.append({"role": "assistant", "content": assistant_text})
    except Exception as exc:  # noqa: BLE001
        print(f"\nError: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
