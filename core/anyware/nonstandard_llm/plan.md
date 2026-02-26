# Nonstandard LLM Adapter Plan (Anyware)
Status: UI-integrated demo + middleware tool dispatch + auto-wrap (periodic monitoring pending)
Last Updated: 2026-02-26
Location: core/anyware/nonstandard_llm/

## Understanding Summary
- Build a nonstandard LLM adapter plan for early Anyware integration.
- Streaming responses are implemented (terminal harness + Anyware demo page).
- Tool/function calling hooks are reserved but not executed yet.
- Test provider is DeepSeek only; Gemini is reserved for later.
- API keys are loaded from a local config file that will be gitignored.
- Periodic monitoring requests are documented only, not implemented.

## Assumptions
- The adapter is UI-agnostic; UI binding is handled in Anyware pages.
- Demo usage is manual and low-frequency.

## Goals
- Define a minimal adapter shape to stream tokens from DeepSeek.
- Provide a stable place to evolve provider abstraction and tool-call stubs.
- Ensure config handling is simple and safe for local testing.
- Provide a working Anyware demo page for manual inspection.

## Non-Goals (This Phase)
- No background periodic monitoring loop implementation.
- No multi-provider runtime switching beyond placeholder structure.
- No production-grade auth or secret management.

## Constraints
- Streaming is required for the first capability.
- DeepSeek is the only active provider for tests.
- LLM UI is demo-only for now (not productized).

## Module Boundaries
- Adapter interface: minimal client abstraction for streaming chat (`adapter.py`).
- Provider implementation: DeepSeek-specific API wiring (`client.py`).
- Message model: basic chat message structure (role, content) (`types.py`).
- Stream parser: parse provider streaming response and yield text deltas (`client.py`).
- Terminal harness: CLI script to test streaming end-to-end (`terminal_test.py`).
- UI core: TextViewport + ChatInputLine + ChatDialogPanel (`core/anyware/llm_ui.py`).
- Demo integration: Anyware demo page (`apps/app_anyware_demo.py`) and UI demo (`apps/app_anyware_llm_ui_demo.py`).

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

## Tool/Function Calling (Middleware v1)
- Tool specs + tool calls are parsed and executed via middleware dispatcher.
- Provider-native tool_calls remain unsupported (still treated as placeholders).
- Tool results are injected back into the model for natural language response.

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

## UI Integration Notes (Implemented)
- UI core lives in `core/anyware/llm_ui.py`.
- Packaged page component: `core/anyware/llm_page.py` (`LLMPage`).
- LLM page is wired into `apps/app_anyware_demo.py` (press `L` to enter).
- Streaming to DeepSeek is supported via background thread in the demo page.
- TextViewport now auto-wraps lines to viewport width (CJK-safe).

## Manual Inspection Gates
1) TextViewport + ChatInputLine behavior check (scrolling, cursor, multiline) — Completed.
2) Stream-to-UI hook check (ChatDialogPanel.start_stream/poll_stream, tool-call placeholder status) — Completed.
3) Live LLM streaming in Anyware demo page — Completed.
4) Tool dispatch + follow-up response (get_time) — Completed.

## Periodic Monitoring Note
- Periodic monitoring requests will be documented only in this phase.
- Implementation to follow after tool/function calling is available.

## Tool/Function Calling Strategy (Planned)
- Preferred approach: Middleware dispatch (model emits intent; app executes tools).
- Rationale: higher control, better error handling, and safer automation than strict tool-call output.
- OpenAI-compatible tool_calls remain optional for later comparison.

## Middleware Prototype Design (Implemented - Skeleton)
Goal: minimal, reliable tool-call pipeline with strong guardrails and simple failure modes.
Status: parser/registry/dispatcher implemented; LLM demo uses dispatcher for tool calls.

### 1) Tool Registry (Core)
- Structure:
  - name: str
  - description: str
  - args_schema: dict (JSON-schema-like; minimal validation only)
  - handler: callable (args -> ToolResult)
- ToolResult:
  - ok: bool
  - output: str (human-readable)
  - data: dict | None (structured optional)
  - error: str | None
- Registry is static Python dict for v1; no dynamic discovery.

### 2) Intent Format (Model Output)
- Minimal format (single-line):
  - `[CALL] tool_name {"arg": "value"}`
- Rules:
  - Only one tool call per assistant message.
  - JSON payload must be an object.
  - If parse fails, treat as normal text.
- Optional alternate: fenced JSON block
  - ```tool
    {"name":"tool_name","args":{...}}
    ```

### 3) Parser & Validation
- Parse first matching intent line; ignore the rest of message.
- Strict JSON parse; if failure -> no tool call.
- Validate:
  - tool exists
  - required args present
  - basic type checks (str/number/bool/list/dict)
- On validation failure: return ToolResult(ok=False, error="...") without calling handler.

### 4) Dispatcher Loop
1. Send prompt/messages to LLM.
2. Receive assistant text.
3. Attempt intent parse:
   - If no tool call -> display assistant text.
   - If tool call -> execute handler.
4. Inject tool result back to LLM (optional second turn):
   - “Tool result: …”
5. Display final assistant response.

### 5) Safety & Controls
- Manual confirm hook (optional per tool).
- Rate limit per tool (simple counters).
- Tool allowlist per page/session.
- Hard timeout on tool execution.

### 6) UI Integration Plan
- LLMPage shows:
  - status: “tool-call placeholder” / “waiting for tool” / “tool error”
  - tool outputs as system message lines.

### 7) Periodic Monitoring Hook
- Timer injects system snapshot to LLM every N seconds.
- If intent is returned, run tool. Otherwise display suggestion/analysis.

### 8) Minimal Testing Targets
- Parser: valid/invalid intent lines.
- Validation: missing args, wrong types.
- Dispatcher: tool success + tool error.
- UI: tool result shown as system message.

## Remaining Work (Next)
- Periodic monitoring hook (timer-driven system snapshot + tool dispatch).
- Optional tool confirmation / rate limit controls.
- Evaluate provider-native tool_calls vs middleware (later).

## Ideas (Not Implemented)
- Idle/heartbeat assistant prompts to allow occasional proactive messages.
- Scripted tool stress tests for dispatch + follow-up response validation.

## Development & Maintenance Cost (Estimate)
Assumes one developer, low-frequency internal usage, DeepSeek only.
- Middleware v1 (intent format + parser + dispatcher + tool registry): 2–4 days.
- Tool result callback loop (return tool output to model): 1–2 days.
- Demo UI integration for tool events + safety prompts: 1 day.
- Tests (parser + tool dispatch + UI smoke): 0.5–1 day.
- Total expected dev effort: 4–8 days.

Maintenance (steady state):
- Prompt/format adjustments: 1–2 hours/month.
- Tool registry changes (new tool, param tweaks): 2–4 hours per tool.
- Provider/API changes (DeepSeek schema updates): 0.5–1 day when needed.

## Acceptance Criteria (Planning Phase)
- Plan document is complete and linked from Anyware main doc.
- Implementation scope and non-goals are explicit.
- Config and terminal test expectations are unambiguous.

## Decision Log
- D1: Use streaming as the first capability to match interactive needs.
- D2: Reserve tool/function calling with placeholders only.
- D3: Keep adapter UI-agnostic; bind via Anyware demo pages.
- D4: Use DeepSeek for testing now; Gemini reserved for later.
- D5: Use local config with gitignore for API keys.
- D6: Periodic monitoring noted but not implemented yet.
- D7: Prefer middleware dispatch for tool execution in future work.
