# Nonstandard LLM Adapter Plan (Anyware)
Status: Terminal prototype (no UI)
Last Updated: 2026-02-25
Location: core/anyware/nonstandard_llm/

## Understanding Summary
- Build a nonstandard LLM adapter plan for early Anyware integration, without UI.
- Initial capability is streaming responses for terminal-based testing.
- Reserve tool/function calling hooks but do not execute tools yet.
- Test provider is DeepSeek only; Gemini is reserved for later.
- API keys are loaded from a local config file that will be gitignored.
- Periodic monitoring requests are documented only, not implemented.

## Assumptions
- The adapter is code-adjacent to Anyware but not a UI component yet.
- Terminal testing should be low-frequency, manual usage.

## Goals
- Define a minimal adapter shape to stream tokens from DeepSeek.
- Provide a stable place to evolve provider abstraction and tool-call stubs.
- Ensure config handling is simple and safe for local testing.

## Non-Goals (This Phase)
- No Anyware UI integration until scrollable dialog UI is ready.
- No background periodic monitoring loop implementation.
- No multi-provider runtime switching beyond placeholder structure.
- No production-grade auth or secret management.

## Constraints
- Streaming is required for the first capability.
- Terminal-only testing; no UI surface yet.
- DeepSeek is the only active provider for tests.

## Module Boundaries
- Adapter interface: minimal client abstraction for streaming chat (`adapter.py`).
- Provider implementation: DeepSeek-specific API wiring (`client.py`).
- Message model: basic chat message structure (role, content) (`types.py`).
- Stream parser: parse provider streaming response and yield text deltas (`client.py`).
- Terminal harness: CLI script to test streaming end-to-end (`terminal_test.py`).

## Configuration Strategy
- Local config file: `assets/_private/llm_config.local.json`
- `assets/_private/` is gitignored to keep secrets out of git history.
- Example template: `docs/anyware/llm_config.example.json`
- Example fields (current):
  - provider
  - api_key_file
  - base_url
  - model
  - timeout_s
  - stream
  - temperature
  - top_p
  - max_tokens

## Provider Strategy
- Define a small provider-agnostic interface, then implement DeepSeek first.
- Keep Gemini as a reserved placeholder with no active code yet.
- Avoid provider-specific logic leaking into terminal test harness.

## Streaming Strategy
- Follow DeepSeek streaming response format as defined in official docs.
- Emit incremental text deltas as they arrive.
- Provide a clear end-of-stream signal and error surface.
- Handle connection errors and malformed chunks gracefully.
- SSE parser accepts multiline `data:` events and ignores keepalive comments.

## Tool/Function Calling Placeholder
- Define a structured placeholder for tool specs and tool calls.
- Do not execute tools; only surface tool-call events to the caller.
- If the provider emits a tool-call, log it and exit the stream cleanly.

## Terminal Test Harness (Implemented)
- Location: `core/anyware/nonstandard_llm/terminal_test.py`
- Reads local config, accepts a prompt, streams output to stdout.
- Optional flags: model override, temperature, max tokens, system prompt.
- No UI dependencies.
- Run example:
  - `python3 core/anyware/nonstandard_llm/terminal_test.py --prompt "hello"`
- REPL mode:
  - Run without `--prompt` in a TTY to enter multi-turn chat.
  - Commands: `/help`, `/exit`, `/reset`, `/reload`, `/system`.

## Prompt Management (Implemented)
- System prompt file: `core/anyware/nonstandard_llm/prompts/system.txt`
- Loaded at startup; manual reload supported in REPL via `/reload`.
- Prompt file is tracked in git for versioned iteration.
- Multi-prompt selection:
  - `--prompts plain,system` loads `plain.txt` then `system.txt` from `prompts/`.
  - Prompt contents are concatenated in order, separated by a newline.

## Logging and Safety
- Do not print API keys.
- Print minimal request metadata for debugging.
- Keep streaming output clean for visual inspection.

## Future UI Integration Notes
- UI integration will wait for a scrollable dialog/chat component.
- Adapter should remain UI-agnostic to allow later Anyware binding.

## Periodic Monitoring Note
- Periodic monitoring requests will be documented only in this phase.
- Implementation to follow after tool/function calling is available.

## Acceptance Criteria (Planning Phase)
- Plan document is complete and linked from Anyware main doc.
- Implementation scope and non-goals are explicit.
- Config and terminal test expectations are unambiguous.

## Decision Log
- D1: Use streaming as the first capability to match interactive needs.
- D2: Reserve tool/function calling with placeholders only.
- D3: Terminal-only testing until the chat UI is built.
- D4: Use DeepSeek for testing now; Gemini reserved for later.
- D5: Use local config with gitignore for API keys.
- D6: Periodic monitoring noted but not implemented yet.
