# Anyware Reference

Doc role: deep technical reference aligned with `docs/anyware/anyware_plan.md`.  
Section numbering mirrors the plan to avoid cross-indexing.

## Table of Contents
0. Active Anyware Work Items
1. Overview + Status
2. Layer Contract
3. Component Universe (Planning Inventory)
4. Capability Gap Review (GUI vs Anyware vs N/A)
5. MVP Scope for Anyware 0.2.0
5.1 Page Logic (FSM + Stack)
5.2 AI-Assisted Workflow (Merged)
5.3 Dynamic Component Management (Anyware-only)
5.4 Layout DSL (YAML, Declarative)
5.5 Open Questions (Post-0.2.0)
6. Milestones And Acceptance (0.2.0)
6.1 Pre-Adaptation Plan (v0.0.6 -> v0.1.9)
7. Change Log (Unified, Version-Tracked)
8. Layout DSL (Draft)
9. Demo Archive
10. Output Separation Rules (Pre-Adaptation)
11. SegmentDisplay Defaults (Reference)
12. Anyware Components Reference (Concise)
13. Nonstandard LLM Adapter (Planning Only)
13.1 Adapter Scope (Planning Only)
13.2 LLM UI Plan (Streaming Chat)
14. Integration Test Results (Closed Only)

## 0) Active Anyware Work Items
[To be written]

## 1) Overview + Status
[To be written]

## 2) Layer Contract
### App API Access Policy
- Default path: app code should call Anyware classes/context only.
- Text policy: Anyware app code should use `Label/Text` component or `ctx.label()/ctx.text()`, not `static/hstatic` directly.
- Escape hatch: raw `core/GUI.py` access is allowed only as explicit opt-in (debug/migration/specialized rendering).
- Enforce by runtime flag:
  - `allow_raw_gui=False` by default.
  - `ctx.raw_gui()` raises when raw access is not explicitly enabled.
- Long-term target:
  - keep raw access usage close to zero in production Anyware apps.

## 3) Component Universe (Planning Inventory)
### Instrument Consolidation Decisions
- MeterBar merges progress/battery/signal/level into one component (bar vs segments).
- DialGauge merges round/fan/arc gauges into one configurable component.
- StatusLight is modeled as a non-pressable `Button` with status/lighting.
- SegmentDisplay stays separate (design-driven logic, 7-seg baseline).
- TrendLine is deferred (state ownership + sampling policy).

## 4) Capability Gap Review (GUI vs Anyware vs N/A)
Method: define desired feature -> decide if current GUI can directly support -> locate missing responsibility.

### 4.1 Opening Animation Example: "shape draws gradually"
Feature definition:
- draw a line/poly progressively by `progress` in `[0, 1]`, not instant full draw.

Current status:
- can be approximated by manual frame logic, but no standard primitive for path-progress drawing.

Decision:
- missing capability is low-level and reusable -> should be in `core/GUI.py`.

Proposed GUI additions:
1. `draw_line_progress(p1, p2, progress, ...)`
2. `draw_poly_progress(shape_or_vertices, progress, mode='stroke', ...)`

Anyware responsibility:
- timeline/easing/sequence orchestration (`IntroSequence`, staged animation scripting).

### 4.2 Text-aware layout sizing
Need:
- estimate text size for predictable box/layout assembly.

Current status:
- no direct standard API for text pixel metrics.

Decision:
- add low-level metric API in `core/GUI.py`:
  - `measure_text(content, ...) -> (w_px, h_px)`
- Anyware uses this for auto-sized controls.

### 4.3 Local reveal/clipping effects
Need:
- clip drawing in rect for reveal transitions.

Decision:
- optional for v0.2.0; if implemented, belongs to `core/GUI.py` (render primitive).

### 4.4 Complex VFX (particle/3D-grade motion)
Decision:
- not in current project responsibility (N/A for v0.2.0).

### 4.5 Non-Loop Animation Split (Anyware Side)
Design statement:
- Non-loop animation is a finite sequence over time, not a special render mode.
- Anyware owns "what happens when"; GUI owns "how current frame is drawn".

Anyware requirements (proposed):
1. A-ANM-01 Timeline container (P0)
- `IntroSequence` supports ordered steps with `delay`, `duration`, `once`.
- can stop at final frame/state (non-loop by default).

2. A-ANM-02 Step model (P0)
- step receives normalized `progress` in `[0, 1]`.
- step can target component props (visibility, color level, gauge fill, text reveal length).

3. A-ANM-03 Trigger/finish protocol (P0)
- explicit lifecycle: `idle -> running -> finished`.
- supports one-shot start for boot animation.

4. A-ANM-04 Easing and defaults (P1)
- built-in minimal easing set (`linear`, `ease_in`, `ease_out`).
- default should be conservative and predictable for AI-generated templates.

5. A-ANM-05 Interrupt and skip policy (P1)
- allow "skip animation" and jump to final stable state.
- required for practical UX and debugging.

6. A-ANM-06 Scope-safe interaction during animation (P1)
- define whether focus/navigation is disabled, limited, or fully enabled while intro plays.
- default policy should avoid ambiguous interaction states.

Dependencies on GUI requirements:
- A-ANM-01/02 depend on `G-ANM-01` and `G-ANM-02` for progressive drawing.
- A-ANM-02 depends on `G-ANM-03` for text-bound animation sizing.
- A-ANM-04/05 benefit from `G-ANM-05` stable timing helpers.
- A-ANM-06 can be implemented with existing focus/scope APIs.

## 5) MVP Scope for Anyware 0.2.0
[To be written]

## 5.1) Page Logic (FSM + Stack)
[To be written]

## 5.2) AI-Assisted Workflow (Merged)
[To be written]

## 5.3) Dynamic Component Management (Anyware-only)
Goal: enable dynamic add/remove/replace of components without DOM/tree complexity.

Route (agreed):
- Use a flat, id-based reconcile list (no tree).
- Each component must have a unique `component_id` (string is allowed and preferred).
- If changes are large, switch pages instead of mass mutations.
- Anyware only: `core/GUI.py` stays unchanged.

Implementation contract:
- `ComponentGroup.reconcile_children(ctx, next_children)` handles mount/unmount and replacement.
- Focus fallback: if current focus id is no longer present, jump to any available focusable id.
- Use `visible/enabled` for per-frame animation-like changes; avoid per-frame structural reconcile.
- Id helper: use `stable_component_id(name, seed=...)` or `IdFactory.next(name)` to create stable, unique ids.

## 5.4) Layout DSL (YAML, Declarative)
[To be written]

## 5.5) Open Questions (Post-0.2.0)
These are long-term decision prompts. Keep them general here and refine only when a decision is imminent.

1. Binding model
- Do we formalize Bindable types or keep simple callables for dynamic values?

2. Hot reload scope
- Layout-only reload vs full page/module reload, and how to keep determinism.

3. DSL boundary
- What belongs in DSL long-term, and what remains Python-only?

4. Output pipeline contract
- How to define pygame and OpenGL presenter responsibilities and transition.

5. Animation ownership
- GUI primitives only vs a richer Anyware animation system.

6. Layout measurement
- Strict grid-first discipline vs text-aware sizing support.

7. Compatibility and versioning
- API levels, migration notes, and deprecation policy enforcement.

8. Theming strategy
- Global defaults vs per-page style systems, and how to avoid divergence.

## 6) Milestones And Acceptance (0.2.0)
[To be written]

## 6.1) Pre-Adaptation Plan (v0.0.6 -> v0.1.9)
[To be written]

## 7) Change Log (Unified, Version-Tracked)
[To be written]


## 8) Layout DSL (Draft)
This section merges the former `layout_dsl_plan.md`.

Goal: provide an HTML-like declarative layout file (page -> group -> element) for **static UI** components, improving development efficiency with **minimal code changes**. This is a **planning** section and is not required to be implemented immediately.

### Background & Motivation
- Current state: most layouts are written in Python (e.g., `reactor_ui_layout.py`), which is costly to modify and slows collaboration.
- Desired state: describe most static UI in a more declarative file, and only use small amounts of Python when needed.

### Goals
1. **Page-Group-Element structure**: HTML-like hierarchy, but lighter.
2. **Static-first, dynamic as needed**: static layout fully declarative; limited logic via Python callbacks.
3. **Minimal change**: reuse existing Anyware render flow; do not rewrite the renderer.
4. **Hot reload**: keep the current live-reload workflow.
5. **Project default**: YAML DSL is the default layout path; Python layout is a fallback.

### Non-Goals
- No full UI editor/visual builder.
- No redesign of Anyware layout/render core.
- No complex runtime expressions or scripting engine.
- Python layout should not be the default path (only for advanced custom cases).

### Design Principles
- **Declarative**: layout files describe *what* to render, not how.
- **Readable**: clear structure suitable for hand-editing and review.
- **Mappable**: easy to map to existing Python data structures and draw calls.
- **Safe**: logic only via whitelisted callbacks, no arbitrary code execution.

### File Format (Confirmed)
- Use **YAML** for readability and hand editing.

### File Organization (Confirmed)
- **One page per file**: `integration_test/v0.0.9/app/layouts/<page>.yaml`
- Page registration and routing remain in Python (DSL only describes layout).

### Structure Draft (Styles, Relative Coordinates, Bindings)
- `globals`: grid, palette, constants
- `styles`: named styles (lightweight CSS-like)
- `pages`: page collection
- `groups`: group containers
- `elements`: concrete elements (panel/text/button/arrow/...)

Example (YAML):
```yaml
globals:
  grid: { cols: 128, rows: 48, cell_w: 8, cell_h: 16 }
  palette:
    bg: "#fdf6f0"
    default: "#586e75"
    special: "#78cd26"

styles:
  default:
    text_color: "default"
    line_color: "default"
    fill: null
  nav_button:
    text_color: "default"
    line_color: "default"
    fill: null
  nav_button_active:
    text_color: "bg"
    line_color: "special"
    fill: "special"

pages:
  diagram:
    groups:
      - id: nav
        rect: [0, 0, 128, 6]
        elements:
          - id: btn_state
            type: button
            rect: [0, 0, 20, 6]   # relative to nav top-left
            label: "STATUS"
            style: nav_button
            on_click: go_page.state
          - id: btn_diagram
            type: button
            rect: [20, 0, 20, 6]
            label: "DIAGRAM"
            style: nav_button_active
            on_click: go_page.diagram

      - id: body
        elements:
          - id: panel_main
            type: panel
            rect: [0, 6, 128, 38]
            style: default
          - id: core_box
            type: box
            rect: [10, 12, 20, 10]
            label: "Core"
            style: default

      - id: footer
        elements:
          - id: footer_block_1
            type: rect
            rect: [0, 44, 20, 4]
            fill: "default"
            style: default

          - id: latency_text
            type: text
            rect: [92, 2, 24, 3]
            text: "LATENCY: --"
            bind: "net.latency_ms"
            style: default
```

### Element Type Mapping (Suggested)
To minimize changes, element types should map to existing draw functions:
- `panel` -> existing panel render
- `text` -> `super_text` / `draw_text`
- `button` -> Anyware `Button`
- `rect` / `box` -> `draw_rect` / `draw_box`
- `arrow` -> `draw_arrow`
- `poly` -> `draw_poly`

### Logic & Data Binding (Limited Python)
Avoid code in layout files; use **callback mapping**:
- Layout: `on_click: go_page.diagram`
- Python: `actions = {"go_page.diagram": lambda: ...}`

Bindings are declarative only (no execution in YAML):
- `bind: "net.latency_ms"` indicates a read path
- Resolved by Python-side `bindings`
- Empty values show placeholders (e.g., `"--"`)

### Dynamic Component Management (DSL <-> Anyware)
Goal: remain consistent with Anyware's **flat, id-based** reconcile; no DOM tree.

Recommended integration:
- DSL provides **slots** and optional **templates**
- Python generates `next_children` (flat list, stable ids) and calls `ComponentGroup.reconcile_children(ctx, next_children)`
- Structural changes should be low frequency; use `visible/enabled/text/color` for per-frame changes

Example:
```yaml
groups:
  - id: alarms
    type: slot
    rect: [0, 20, 64, 20]
```
```python
next_children = [
  {"type": "text", "component_id": "alarm.1", "rect": [0,0,64,2], "text": "..."},
  {"type": "text", "component_id": "alarm.2", "rect": [0,2,64,2], "text": "..."},
]
group.reconcile_children(ctx, next_children)
```

### Coordinate System (Confirmed)
- **Relative coordinates**: element `rect` is relative to parent group top-left.
- **No percentages**: all values are in grid units.
- **Anchors**: not supported directly; use nested empty groups as anchors.

### Style System (Confirmed)
Two cases:
1. **Element specifies `style`**: apply that style.
2. **Element omits `style`**: compute defaults by precedence:
   `element-local > group styles > global default > system default`

Explicit element fields always override computed style.

### Z-Index (Confirmed)
- `z_index` inherits from parent group by default.
- Can be overridden per element.
- When `z_index` ties occur, use a **stable pseudo-random** order:
  - Recommend hash ordering by `component_id`/`id` for stability across frames.

### Minimal Landing Plan (Suggested)
**Key principle**: do not change the renderer; add a layout loader.

1. Add a loader:
   - `integration_test/v0.0.9/app/layout_loader.py`
   - parse `layouts/*.yaml` and convert into existing layout structures
2. Keep existing render code:
   - `render_layout(layout_dict)` stays unchanged
3. Config flag:
   - `USE_DSL_LAYOUT = True` or CLI param
4. Fallback:
   - if YAML is missing or fails to parse, fall back to `reactor_ui_layout.py`

### Hot Reload Strategy (Suggested)
- Monitor layout file mtime
- Check every N frames (consistent with current hot reload)
- On parse error: keep last valid layout and surface error in UI

### Migration Path (Suggested)
1. Pilot on `diagram` page (DSL + Python in parallel)
2. Migrate remaining pages after stabilizing
3. End state: DSL + minimal Python only

### Binding Refresh Frequency (Confirmed)
- Refresh bindings on **App logic frames**
- Decouple from backend polling frequency
  - Example: backend polls every 2s, UI can still render at 60fps with last value

## 9) Demo Archive
Purpose: keep a runnable showcase of current Anyware capabilities and a migration reference.

Current demo entries:
1. `apps/app_anyware_template.py`
2. `apps/app_anyware_demo.py`

Archive policy:
1. Keep demos runnable under current `GUI_API_LEVEL`.
2. Prefer Anyware components over direct `GUI.py` calls.
3. If temporary workarounds need raw GUI access, mark them explicitly and remove later.

## 10) Output Separation Rules (Pre-Adaptation)
Goal: keep Anyware apps output-agnostic so mixed-pipeline output can be added later.

Rules:
- Anyware apps must not call `pygame.display.*` or `GUI.draw_to_surface(...)`.
- Apps should only render through `AnywareContext` (or `GUI` APIs if using raw path).
- Screen presentation is handled by the runner/presenter layer (pygame path today, OpenGL path later).

Runtime placeholders (no behavior change yet):
- `AnywareApp(output_mode="pygame")` defaults to direct pygame presentation.
- `output_mode != "pygame"` enables offscreen rendering (pre-adaptation hook).
- `logic_fps` / `present_fps` reserved for decoupling logic vs presentation rates.
- `frame_exporter(surface, ctx)` optional hook called after each logic frame.

## 11) SegmentDisplay Defaults (Reference)
- Global defaults live on `SegmentDisplay.DEFAULTS`.
- Override with `SegmentDisplay.set_defaults(...)`.
- Supported `segment_style`: `classic` (default), `rect`.
- 7-seg only (DP supported). 16-seg deferred.

## 12) Anyware Components Reference (Concise)
Button:
- Focusable and selectable button with optional lighting and status display.
- Key parameters: `gx`, `gy`, `width_px`, `height_px`, `pressable`, `focusable`, `lighted`, `status`,
  `status_color_map`, `label_align_h`, `label_align_v`, `label_line_step`, `label_orientation`.

ButtonArray:
- Grid collection of `Button` with deterministic local nav.
- Key parameters: `labels`, `gx`, `gy`, `cols`, `rows`, `gx_spacing`, `gy_spacing`, `scope`.

ValueText:
- Label + formatted numeric value.
- Key parameters: `label`, `value`, `fmt`, `gx`, `gy`, `color`.

MeterBar:
- Linear meter (bar or segments).
- Key parameters: `value`, `min_value`, `max_value`, `mode`, `segments`, `width_px`, `height_px`.

DialGauge:
- Arc gauge with needle/fill styles.
- Key parameters: `center_gx`, `center_gy`, `radius_px`, `start_angle_deg`, `end_angle_deg`, `style`.

SegmentDisplay:
- Multi-segment digital tube display (7-seg default).
- Key parameters: `digits`, `align`, `pad_char`, `digit_w_px`, `digit_h_px`, `spacing_px`,
  `on_color`, `off_color`.

PageRouter and PageStack:
- `PageRouter` is finite state switching.
- `PageStack` supports push/pop/replace for multi-page flows.

## 13) Nonstandard LLM Adapter (Planning Only)
### 13.1 Adapter Scope (Planning Only)
Planning doc: `core/anyware/nonstandard_llm/plan.md`

Current scope (planning only):
- streaming response support (terminal-only test, no UI)
- DeepSeek provider only for testing; Gemini reserved
- tool/function calling placeholders (no execution)
- config-based API key loading, with local config gitignored

Explicit non-goals (for this phase):
- no Anyware UI integration until scrollable dialog UI exists
- no periodic monitoring loop implementation yet (documented only)

### 13.2 LLM UI Plan (Streaming Chat)
Status: planning only. No code changes in this phase.

Understanding summary:
- Build a streaming chat dialog component for Anyware.
- Component is embedded in a page (panel/component), not modal or separate page.
- Keyboard input with virtual cursor and basic editing (insert/backspace/left/right).
- Ctrl+Enter sends; Enter inserts newline.
- IME behavior is system-managed only; component must handle full-width chars.
- Streaming output auto-scrolls; user scroll pauses auto-follow until back at bottom.
- Single-column left-aligned layout; simple Markdown via color-coded spans.
- No explicit performance target; follow Anyware defaults.
- No history limit (for now).

Assumptions:
- Text measurement uses GUI/Anyware text metrics if available; otherwise fixed-width assumptions.
- LLM adapter is UI-agnostic and provides streaming deltas.

Goals:
- Reusable text viewport core for streaming display.
- Chat dialog composition for output + input.
- Clear focus, scrolling, and input behavior.

Non-goals:
- No full IME composition UI (candidates/underlines).
- No rich text beyond color-coded spans.
- No persistence to disk.
- No multi-user or multi-session support.

Proposed architecture (TextViewport core):
1. TextViewport (core)
   - Responsibilities: text layout, scroll state, auto-follow, visible-area rendering.
   - Input model: `TextLine[]` with `TextSpan[]`.
   - State: `scroll_offset`, `auto_follow`, `view_height_px`, `line_height_px`.
   - Ops: `set_lines(lines)`, `append_lines(lines)`, `scroll(delta_lines)`,
     `jump_to_bottom()`, `is_at_bottom()`.
2. ChatStreamBuffer
   - Accept streaming deltas, append to current assistant message.
   - Emit incremental `TextLine` updates for TextViewport.
   - Markdown parsing: re-parse only the current line per delta.
3. Markdown Simplifier
   - Minimal tokens, color-only semantics:
     - `**bold**`, `` `code` ``, `> quote`, `- list`
   - Output: `TextSpan(text, color, style_tag)`.
4. ChatInputLine
   - Single buffer + cursor index.
   - Edits: insert, backspace, left/right.
   - Input: Enter inserts newline; Ctrl+Enter sends.
   - Full-width chars treated as single positions.
5. ChatDialogPanel
   - Composition of TextViewport + ChatInputLine + StatusLine.
   - API: `on_send(text)`, `append_user(text)`, `append_assistant_delta(text)`.
   - StatusLine shows auto-scroll paused or errors.

Interaction and focus:
- Input area captures text input and cursor edits.
- Viewport handles scrolling and focus traversal.
- Use FocusGroup (or equivalent) for Tab-based switching.
- Auto-scroll: user scroll sets `auto_follow=false` and shows "Paused"; returning
  to bottom or pressing End restores `auto_follow=true`.

Data flow (streaming):
1. User types -> ChatInputLine buffer.
2. Ctrl+Enter -> `on_send` -> LLM adapter streaming call.
3. Each delta -> ChatStreamBuffer -> `TextViewport.append_lines()`.
4. If `auto_follow` is true, `jump_to_bottom()`.
5. Errors insert a system message with error color.

Edge cases:
- Large history: render only visible lines; avoid full re-layout each frame.
- Streaming + Markdown: avoid full-document parse on every delta.
- IME: accept committed text only; no composition display.

Testing plan:
- Input editing: insert, backspace, cursor move, newline, Ctrl+Enter send.
- Scroll behavior: auto-follow pause/resume, bottom detection.
- Stream behavior: incremental deltas, partial Markdown tokens.
- Rendering: long text, full-width chars, color spans.

Decision log:
- D1: Reusable TextViewport core for layout/scroll/viewport logic.
- D2: Chat dialog is a panel/component, not modal or page.
- D3: Auto-scroll pauses on user scroll, resumes at bottom.
- D4: Basic keyboard editing only; Ctrl+Enter sends.
- D5: IME is system-managed only; handle full-width chars.
- D6: Minimal Markdown via color-coded spans only.

## 14) Integration Test Results (Closed Only)
[To be written]
