# Anyware Plan

Anyware version: 0.0.6  
Target MVP version: 0.2.0  
GUI dependency baseline: `GUI_API_LEVEL >= 1`  
Doc role: planning/architecture (primary). Deep technical reference: `anyware_reference.md`.

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
14. Integration Test Results (Closed Only)

## 0) Active Anyware Work Items
- ANY-PAGESTACK: PageStack runtime integration in AnywareApp. Status: Done (2026-02-15)
- ANY-TEMPLATE-RELOAD: Anyware template supports hot reload for layout params. Status: Done (2026-02-15)
- ANY-BUTTON-ALIGN: Button label alignment + multiline support. Status: Done (2026-02-15)
- ANY-DYNAMIC-COMPONENTS: flat reconcile-based dynamic component management. Status: Done (2026-02-15)
- ANY-SEGMENT-DEFAULTS: SegmentDisplay global defaults (size, spacing, colors). Status: Done (2026-02-16)
- ANY-SEGMENT-THEME: SegmentDisplay global theme or shared style defaults. Status: Done (2026-02-16)
- ANY-CHECKBOX-MENU: implement `CheckboxMenu` (MVP component). Status: Done (2026-02-16)
- ANY-LAYOUT-DSL: YAML layout DSL + loader (styles, bindings, slots). Status: In progress (2026-02-22)
- ANY-NONSTANDARD-LLM: nonstandard LLM adapter (streaming + tool-call placeholders, terminal-only test). Status: Prototype (2026-02-25)

## 1) Overview + Status
Anyware is the primary path for ongoing UI framework development. GUI changes are expected to be minimal and stable, while Anyware continues to evolve toward the 0.2.0 MVP target (see version block above).

Status and policy:
- Active development is focused on the YAML Layout DSL and pre-adaptation foundations.
- Integration test results are recorded in a dedicated section and **only updated after a test closes** (no real-time updates).
- Versioning discipline: avoid large behavior changes hiding behind small version increments.

Constraints (current):
- Limited palette: prefer disciplined color use and readability over arbitrary styling.
- Coordinate rules: text uses grid coordinates; shapes/rects/focus nodes use pixel coordinates (via `gx()/gy()`); convert back with `px()/py()` for text alignment.
- Mixed output pipeline: pygame is the default presenter; OpenGL path is in progress.
- Mixed authoring model: DSL is the default; Python layout is reserved for cases the DSL cannot express.

Active work items summary (see full list in section 0):
- YAML Layout DSL + loader is in progress (styles, bindings, slots).
- Nonstandard LLM adapter terminal prototype is available (streaming + tool-call placeholders).

Deep technical details are kept in `docs/anyware/anyware_reference.md` to keep this plan concise.

## 2) Layer Contract
Rationale: keep the engine stable and low-level, while Anyware absorbs most feature velocity. This separation prevents UI feature churn from destabilizing core rendering and focus logic.

1. `core/GUI.py` (engine):
- rendering primitives, coordinate conversion, focus/nav internals, draw queues, defaults.
- no business widget semantics.
- publishes compatibility via `GUI_API_LEVEL` and stable API contract.
- **must not depend on** `core/anyware` or app scripts.

2. `core/anyware` (components package):
- reusable widgets, page/scope composition helpers, interaction conventions.
- wraps `core/GUI.py`, no reverse dependency.
- validates dependency at startup via `require_api_level(...)`.
- compatibility entrypoint: `core/Anyware.py` (legacy import bridge).

App API access policy is documented in `docs/anyware/anyware_reference.md` to keep this plan concise.

3. Use-case scripts (`app_*.py`):
- demos, template references, experimental integration.
- prototype place before promotion.

Promotion policy:
- app feature -> `core/GUI.py` only if at least 2/3:
  - repeated in multiple scenarios
  - low-level and domain-agnostic
  - does not significantly increase API complexity
- otherwise app feature -> `core/anyware`.

Out-of-scope:
- `core/Sound.py` stays independent placeholder; not part of Anyware v0.2.0 MVP.

## 3) Component Universe (Planning Inventory)
This is the full planning inventory, not the immediate MVP scope.  
No MVP tagging is listed here; see Roadmap/Milestones for timing expectations.

### Structure & Page
- `Page`
- `PageRouter` (simple switch)
- `Panel`
- `Modal`
- `Tabs`

### Core Controls
- `Label`
- `Button`
- `ButtonArray`
- `Checkbox`
- `CheckboxMenu`
- `RadioGroup`
- `Input` (post-MVP)

### Display & Instruments
- `ValueText`
- `MeterBar` (bar/segments)
- `DialGauge` (round/fan via config)
- `SegmentDisplay` (P0.5)
- `TrendLine` (post-MVP)

### Feedback & Utility
- `Toast`
- `ConfirmDialog`
- `Loading`
- `CursorHint`

### Navigation Helpers
- `FocusGroup`
- `ScopeRouter`
- `ShortcutMap`

### Animation Wrappers
- `IntroSequence`
- `Blink`
- `SweepReveal`
- `Typewriter`
- `StrokeDraw`

Consolidation notes for instruments and status controls are maintained in `docs/anyware/anyware_reference.md`.

## 4) Capability Gap Review (GUI vs Anyware vs N/A)
This section is maintained in `docs/anyware/anyware_reference.md` to keep the plan concise.  
Use the reference doc for detailed capability gap analysis, proposed GUI additions, and animation split requirements.

## 5) MVP Scope for Anyware 0.2.0
This section is a **goal checklist**, not a schedule guarantee.

Component goals:
- `Label`
- `Button`
- `ButtonArray`
- `CheckboxMenu`
- `ValueText`
- `MeterBar`
- `DialGauge`
- `SegmentDisplay`

Page logic goals:
- `PageRouter` (finite switch only)
- `PageStack` (push/pop/replace)

Layout goals:
- YAML layout is the default path.
- Python layout is reserved for non-DSL cases.

Dynamic components:
- Flat, id-based reconcile (no DOM tree).

Integration constraints:
- Keep pygame presenter path for tests.
- Anyware apps must not call `pygame.display.*` or `GUI.draw_to_surface(...)`.

Out of scope:
- Complex VFX or large animation systems (post-MVP).

Detailed definitions live in `docs/anyware/anyware_reference.md`.

## 5.1 Page Logic (FSM + Stack)
High-level guidance:
- Use `PageStack` for multi-page flows (push/pop/replace).
- Use `PageRouter` only for simple FSM-style switching.

Integration test guidance:
- Keep stack depth shallow during early integration tests.
- Avoid hidden transitions and implicit back-stack changes.

## 5.2 AI-Assisted Workflow (Merged)
Purpose:
- Let AI output **logic-correct, coordinate-correct** UI first pass.
- Humans perform fine tuning, polish, and minor fixes.

Positioning:
- AI is responsible for **logical implementation**, not perfect visual design.
- Grid-first keeps outputs principled and reduces spatial errors.

Minimum acceptance for AI output:
- coordinate types are correct
- navigation logic is correct
- state transitions are correct
- visual perfection is deferred to manual tuning

Mandatory constraints:
- **Key layout parameters must be hard-coded in an explicit layout file** (default: `layout.yaml`).
- **YAML DSL is the standard layout path**; Python layout only when DSL cannot express a need.
- **Live reload must be enabled** to allow real-time tuning.
  - On parse failure: keep last valid layout and surface error in UI.
- Optional: enable **layout mode** (two-color palette) to reduce visual noise while tuning:
  - API: `GUI.set_layout_mode(True/False)`
  - DSL: toggle `globals.layout_mode` in `apps/layouts/anyware_template_layout.yaml`

Coordinate discipline (AI output must be explicit):
- Text (Label/Text/ctx.label) uses **grid** coordinates.
- Shapes/rects/focus nodes use **pixel** coordinates (convert from grid via `gx()/gy()`).
- If you need to align text to a pixel anchor, convert back via `px()/py()`.

Prompt guidance for AI templates:
- "Text calls must use grid coordinates."
- "Shape and node rect calls must use pixel coordinates converted with gx/gy."
- "Focus rendering and select state updates must be separate."
- "Prefer conservative defaults unless necessary."

AI checklist (Instruments):
- Normalize numeric values to `[0, 1]` before rendering.
- Keep text APIs in grid; shape APIs in pixel.
- Prefer fixed geometry over auto-layout.
- Avoid side effects in render paths.

AI checklist (Buttons + Status):
- `pressable=False` for non-interactive indicators.
- `focusable=False` if it should not capture focus.
- Prefer `status_color_map` for stable state visuals.
- Control label alignment explicitly (`label_align_h`, `label_align_v`, `label_line_step`, `label_orientation`).

AI checklist (SegmentDisplay sizing):
- Keep a consistent baseline across the page.
- Defaults: `digit_w_px=14`, `digit_h_px=24`, `spacing_px=3`.
- Scale width/height/spacing together.
- Provide `off_color` for readable inactive segments.

Recommended workflow (AI -> human tuning):
1. Ask AI to output layout in grid coordinates first.
2. Keep text APIs in grid.
3. Convert draw anchors/rects to pixel with `gx()/gy()`.
4. If a draw result returns pixel positions and you need labels, convert back with `px()/py()`.
5. Manually tune spacing/size/thickness after logic is confirmed.

Integration test note:
- Avoid complex animation during integration tests; keep updates slow and stable.

## 5.3 Dynamic Component Management (Anyware-only)
Detailed rules are maintained in `docs/anyware/anyware_reference.md` to keep this plan concise.

## 5.4 Layout DSL (YAML, Declarative)
Goal: allow most static UI to be described in a "page -> group -> element" YAML file, with minimal code changes.

Compatibility notes:
- Keeps `core/GUI.py` unchanged (loader translates YAML -> existing layout structures).
- Aligns with grid-first design and hot reload requirements.
- Dynamic components remain **flat, id-based reconcile**; DSL provides only slots/templates.
- Bindings refresh at app logic FPS (decoupled from backend polling).
- YAML is the default layout path; Python layout is reserved for complex custom rendering.

Reference:
- See `docs/anyware/anyware_reference.md` section 8 for detailed rules and draft spec.

## 5.5 Open Questions (Post-0.2.0, Decision Prompts)
These are intentionally general and long-term. Detailed discussion lives in `docs/anyware/anyware_reference.md`.

1. What is the long-term binding model for dynamic values (simple callables vs structured Bindable types)?
2. How should hot reload evolve (layout-only vs full page/module reload) without breaking determinism?
3. What is the boundary between DSL capabilities and Python layout extensions over time?
4. What is the long-term output pipeline contract (pygame vs OpenGL presenter split and transition)?
5. How should animation ownership be split between GUI primitives and Anyware orchestration (minimal vs full system)?
6. What is the long-term approach to layout measurement and auto-sizing (strict grid-first vs text-aware sizing)?
7. How should compatibility and versioning be enforced as Anyware evolves (API levels, migration notes, deprecation policy)?
8. What is the long-term strategy for component theming (global defaults vs per-page style systems)?

## 6) Milestones and Acceptance (0.2.0)
M1. Baseline freeze (done in 0.0.1):
- architecture boundary confirmed
- component universe and gap map written

M2. GUI prerequisite patch (done in GUI v0.4.0):
- text measurement helpers
- text box + super text primitives

M3. Anyware component implementation (in progress):
- implement MVP components with shared style/default model
- provide one medium-complexity demo that uses the MVP set
- DSL progress checkpoint (scope and dates TBD)
- OpenGL presenter shift checkpoint (early, scope TBD)

Acceptance criteria (must satisfy all):
1. A medium UI page can be assembled with fewer lines than raw GUI script.
2. AI-generated template is logically correct on first pass:
- coordinate types mostly correct
- navigation and state transitions correct
3. Remaining work is mainly human tuning/polish, not logic rewrite.
4. Documentation clearly explains:
- Anyware path
- grid/pixel conversion rules
- demo archive usage (see section 9)

## 6.1) Pre-Adaptation Plan (v0.0.6 -> v0.1.9)
Goal: focus on pre-adaptation for the mixed pipeline (GUI -> image/texture -> OpenGL output) while improving robustness and keeping the pygame path as default.

1. v0.0.6 (baseline hardening): tighten Anyware app discipline (no direct screen output); document render/output separation; confirm all demos run under the pygame presenter path.
2. v0.0.7 (contract draft): introduce a presenter/output contract in docs; add config placeholders for `output_mode`, `logic_fps`, and `present_fps` without behavior change. Status: Done (2026-02-16).
3. v0.0.8 (pre-adaptation hooks): add offscreen render target plumbing and optional "frame export" hooks; keep CI on pygame path; add guardrails against direct `pygame.display` usage in Anyware apps. Status: Done (2026-02-16).
4. v0.0.9 (integration test): **Active** (2026-02-24).
   - Focus: AI prompt/brief quality, layout tuning loop, error recovery, and human-AI handoff.
   - Constraints remain: keep pygame presenter path for tests; validate no direct screen output in Anyware apps.
5. v0.1.9 (freeze pre-adaptation): finalize the output separation contract and presenter interface in docs; keep OpenGL path optional and off by default; record acceptance results.

## 7) Change Log (Unified, Version-Tracked)
Policy:
- Track shipped changes by version (not by date).
- Legacy entries that only recorded dates preserve their original date inside the bullet.
- GUI changes are labeled with [GUI].

### v0.4.0 (GUI)
- [GUI] (2026-02-18) GUI draw order adjusted so filled polys render before grid text, ensuring text remains visible over filled shapes (fixes lit button labels).

### v0.0.6 (Anyware)
- (2026-02-18) [Anyware] Button label rendering switched to grid-aligned super-text overlay to avoid fill-layer occlusion while keeping text alignment consistent.
- (2026-02-18) [Anyware] Button label color now auto-contrasts against filled status color (Black/White) to preserve readability when lit.
- (2026-02-16) [Anyware] Archived DSKY integration artifacts; SegmentDisplay defaults verified manually; CheckboxMenu shipped in demo.

### v0.0.4 (Anyware)
- (2026-02-13) [Anyware] Introduced text componentization: Label, Text (supports orientation + color).
- (2026-02-13) [Anyware] Added Anyware text drawing aliases: ctx.label() / ctx.text(); ctx.static()/ctx.hstatic() kept as compatibility path.
- (2026-02-13) [Anyware] Migrated current Anyware demos to label-first usage.
- (2026-02-13) [Anyware] Added apps/app_anyware_demo.py as temporary Anyware demo archive page.
- (2026-02-13) [Anyware] Merged StatusLight into Button (non-pressable status button + optional lighting).
- (2026-02-13) [Anyware] Implemented P0/P0.5 instruments, added per-component docs, and wired them into the demo page.
- (2026-02-13) [Anyware] Added PageRouter for FSM-style page switching and documented page logic constraints.

### v0.0.3 (Anyware)
- (2026-02-13) [Anyware] Introduced class-based Anyware runtime skeleton: AnywareApp, AnywareContext, Page, PageStack, Component, ComponentGroup.
- (2026-02-13) [Anyware] Added first reusable controls: Button, ButtonArray.
- (2026-02-13) [Anyware] Enforced GUI stable API dependency check inside AnywareContext (REQUIRED_GUI_STABLE_API).
- (2026-02-13) [Anyware] Added migration demos: apps/app_anyware_template.py, apps/app_anyware_demo.py (combined demo archive).
- (2026-02-13) [Anyware] Kept raw GUI access as explicit opt-in only (allow_raw_gui, ctx.raw_gui()).

### v0.0.2 (Anyware)
- (2026-02-13) [Anyware] Switched from shared GUI/Anyware doc versioning to dependency contract mode.
- (2026-02-13) [Anyware] Anyware now targets GUI compatibility by GUI_API_LEVEL and stable API tier.

### v0.0.1 (Anyware)
- (2026-02-12) [Anyware] Formalized component universe.
- (2026-02-12) [Anyware] Completed GUI capability gap review with ownership decisions.
- (2026-02-12) [Anyware] Added detailed non-loop animation split (A-ANM-*) and dependency mapping to GUI-side requirements (G-ANM-*).
- (2026-02-12) [Anyware] Defined MVP scope, milestones, and acceptance criteria (target now 0.2.0).

## 8) Layout DSL (Draft)
Detailed DSL rules, examples, and migration notes live in `docs/anyware/anyware_reference.md` section 8.

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

Implementation notes and runtime placeholder hooks live in
`docs/anyware/anyware_reference.md` section 10.

## 11) SegmentDisplay Defaults (Reference)
Defaults and override rules are documented in
`docs/anyware/anyware_reference.md` section 11.

## 12) Anyware Components Reference (Concise)
Core components summary:
- Button (focusable/selectable button with optional lighting/status).
- ButtonArray (grid of Buttons with local navigation).
- ValueText (label + formatted numeric value).
- MeterBar (linear bar/segment meter).
- DialGauge (arc gauge with needle/fill styles).
- SegmentDisplay (multi-segment digital display).
- PageRouter (FSM page switching).
- PageStack (push/pop/replace flows).

Full parameter lists and behavior notes live in
`docs/anyware/anyware_reference.md` section 12.

## 13) Nonstandard LLM Adapter (Prototype, Terminal-Only)
Planning doc: `core/anyware/nonstandard_llm/plan.md`.
Detailed scope and UI planning live in
`docs/anyware/anyware_reference.md` section 13.

## 14) Integration Test Results (Closed Only)
Policy:
- Record results only after a test closes (no real-time updates).
- Track by version number, newest first.

Closed test results:
- None recorded yet.
