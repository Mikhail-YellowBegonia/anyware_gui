# Anyware Plan

Anyware version: 0.0.6  
Target MVP version: 0.1.0  
GUI dependency baseline: `GUI_API_LEVEL >= 1`  
Doc role: planning/architecture (tutorial is `../GUI_TUTORIAL.md`, reference is `../DEV_GUIDE.md`)

## 0) Active Anyware Work Items
- ANY-PAGESTACK: PageStack runtime integration in AnywareApp. Status: Done (2026-02-15)
- ANY-TEMPLATE-RELOAD: Anyware template supports hot reload for layout params. Status: Done (2026-02-15)
- ANY-BUTTON-ALIGN: Button label alignment + multiline support. Status: Done (2026-02-15)
- ANY-DYNAMIC-COMPONENTS: flat reconcile-based dynamic component management. Status: Done (2026-02-15)
- ANY-SEGMENT-DEFAULTS: SegmentDisplay global defaults (size, spacing, colors). Status: Done (2026-02-16)
- ANY-SEGMENT-THEME: SegmentDisplay global theme or shared style defaults. Status: Done (2026-02-16)
- ANY-CHECKBOX-MENU: implement `CheckboxMenu` (MVP component). Status: Done (2026-02-16)

## 1) Positioning
- Anyware is a high-level component layer above `core/GUI.py`.
- Using Anyware still means writing real Python code.
- Two paths remain valid:
  - raw path: app -> `core/GUI.py`
  - component path: app -> `core/anyware/*` -> `core/GUI.py`
- Design preference: grid-first composition, then local pixel tuning.

## 2) Layer Contract
1. `core/GUI.py` (engine):
- rendering primitives, coordinate conversion, focus/nav internals, draw queues, defaults.
- no business widget semantics.
- publishes compatibility via `GUI_API_LEVEL` and stable API contract.

2. `core/anyware` (components package):
- reusable widgets, page/scope composition helpers, interaction conventions.
- wraps `core/GUI.py`, no reverse dependency.
- validates dependency at startup via `require_api_level(...)`.
- compatibility entrypoint: `core/Anyware.py` (legacy import bridge).

### 2.1 App API Access Policy
- Default path: app code should call Anyware classes/context only.
- Text policy: Anyware app code should use `Label/Text` component or `ctx.label()/ctx.text()`, not `static/hstatic` directly.
- Escape hatch: raw `core/GUI.py` access is allowed only as explicit opt-in (debug/migration/specialized rendering).
- Enforce by runtime flag:
  - `allow_raw_gui=False` by default.
  - `ctx.raw_gui()` raises when raw access is not explicitly enabled.
- Long-term target:
  - keep raw access usage close to zero in production Anyware apps.

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
- `core/Sound.py` stays independent placeholder; not part of Anyware v0.1.0 MVP.

## 3) Component Universe (Planning Inventory)
This is the full planning inventory, not the immediate MVP scope.

### A. Structure / Page
- `Page`
- `PageRouter` (simple switch)
- `Panel`
- `Modal`
- `Tabs`

### B. Core Controls
- `Label`
- `Button`
- `ButtonArray`
- `Button` supports optional status/lighting (StatusLight merged)
- `Checkbox`
- `CheckboxMenu`
- `RadioGroup`
- `Input` (post-MVP)

### C. Display / Instrument
- `ValueText`
- `MeterBar` (bar/segments)
- `DialGauge` (round/fan via config)
- `SegmentDisplay` (P0.5)
- `TrendLine` (post-MVP)

Instrument consolidation decisions:
- MeterBar merges progress/battery/signal/level into one component (bar vs segments).
- DialGauge merges round/fan/arc gauges into one configurable component.
- StatusLight is modeled as a non-pressable `Button` with status/lighting.
- SegmentDisplay stays separate (design-driven logic, 7-seg baseline).
- TrendLine is deferred (state ownership + sampling policy).

### D. Feedback / Utility
- `Toast`
- `ConfirmDialog`
- `Loading`
- `CursorHint`

### E. Navigation Helpers
- `FocusGroup`
- `ScopeRouter`
- `ShortcutMap`

### F. Animation Wrappers
- `IntroSequence`
- `Blink`
- `SweepReveal`
- `Typewriter`
- `StrokeDraw`

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
- optional for v0.1.0; if implemented, belongs to `core/GUI.py` (render primitive).

### 4.4 Complex VFX (particle/3D-grade motion)
Decision:
- not in current project responsibility (N/A for v0.1.0).

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

## 5) MVP Scope for Anyware 0.1.0
Minimum component set:
- `Label`
- `Button`
- `ButtonArray`
- `CheckboxMenu`
- `ValueText`
- `MeterBar`
- `DialGauge`
- `SegmentDisplay` (P0.5)
- `PageRouter` (finite switch only)

## 5.1 Page Logic (FSM + Stack)
- AnywareApp now uses `PageStack` (push/pop/replace) for multi-page flows.
- `PageRouter` remains available for simple FSM-only page switching.
- Keep stack depth shallow during early integration tests; avoid hidden transitions.

## 5.2 AI Coding Tips (Integration Prep)
- See `../AI_ASSISTED_DESIGN_GUIDE.md` for the checklist before test runs.

Minimum conventions:
- clear separation of focus vs select
- grid-first parameters where practical
- conservative defaults for AI template generation
- explicit scope integration hooks (optional, but consistent)

## 5.3 Dynamic Component Management (Anyware-only)
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

## 5.4 Open Questions (Post-0.1.0)
Dynamic content model / bindings:
- Do we standardize `Bindable[T] = T | Callable[[ctx], T]` for common props (text/color/visible/enabled)?
- Or move toward a DOM-like tree with reconcile (higher effort, different authoring model)?

Live reload scope:
- Keep hot reload limited to layout params (current), or
- Allow full page module reload + UI tree rebuild?

## 6) Milestones and Acceptance (0.1.0)
M1. Baseline freeze (done in 0.0.1):
- architecture boundary confirmed
- component universe and gap map written

M2. GUI prerequisite patch (done in GUI v0.4.0):
- text measurement helpers
- text box + super text primitives

M3. Anyware component implementation (in progress):
- implement MVP components with shared style/default model
- provide one medium-complexity demo that uses the MVP set

Acceptance criteria (must satisfy all):
1. A medium UI page can be assembled with fewer lines than raw GUI script.
2. AI-generated template is logically correct on first pass:
- coordinate types mostly correct
- navigation and state transitions correct
3. Remaining work is mainly human tuning/polish, not logic rewrite.
4. Documentation clearly explains:
- raw GUI path
- Anyware path
- grid/pixel conversion rules
- demo archive usage (`demo_archive.md`)

## 6.1) Pre-Adaptation Plan (v0.0.6 → v0.1.0)
Goal: focus on pre-adaptation for the mixed pipeline (GUI -> image/texture -> OpenGL output) while improving robustness and keeping the pygame path as default.

1. v0.0.6 (baseline hardening): tighten Anyware app discipline (no direct screen output); document render/output separation; confirm all demos run under the pygame presenter path.
2. v0.0.7 (contract draft): introduce a presenter/output contract in docs; add config placeholders for `output_mode`, `logic_fps`, and `present_fps` without behavior change. Status: Done (2026-02-16).
3. v0.0.8 (pre-adaptation hooks): add offscreen render target plumbing and optional “frame export” hooks; keep CI on pygame path; add guardrails against direct `pygame.display` usage in Anyware apps. Status: Done (2026-02-16).
4. v0.0.9 (integration test): run integration tests focused on AI-assisted UI second-pass development; evaluate AI coding friendliness and collaboration workflow; verify pre-adaptation constraints are respected.
   - Approach: different from v0.0.4; to be discussed and documented before execution.
   - Focus topics: AI prompt/brief quality, layout tuning loop, error recovery, and human-AI handoff.
   - Constraints: keep pygame presenter path for tests; validate no direct screen output in Anyware apps.
5. v0.1.0 (freeze pre-adaptation): finalize the output separation contract and presenter interface in docs; keep OpenGL path optional and off by default; record acceptance results.

## 7) Change Log
- 2026-02-13: Merged `StatusLight` into `Button` (non-pressable status button + optional lighting), implemented P0/P0.5 instruments, added per-component docs, and wired them into the demo page.
- 2026-02-13: Added `PageRouter` for FSM-style page switching and documented page logic constraints.
- 2026-02-16: Archived DSKY integration artifacts; SegmentDisplay defaults verified manually; CheckboxMenu shipped in demo.
- 2026-02-18: Anyware `Button` label rendering switched to grid-aligned super-text overlay to avoid fill-layer occlusion while keeping text alignment consistent.

## 8) Version Changelog (Anyware)
- 0.0.4 (2026-02-13):
  - introduced text componentization: `Label`, `Text` (supports `orientation` + `color`)
  - added Anyware text drawing aliases: `ctx.label()` / `ctx.text()`; `ctx.static()`/`ctx.hstatic()` kept as compatibility path
  - migrated current Anyware demos to label-first usage
  - added `apps/app_anyware_demo.py` as temporary Anyware demo archive page
- 0.0.3 (2026-02-13):
  - introduced class-based Anyware runtime skeleton: `AnywareApp`, `AnywareContext`, `Page`, `PageStack`, `Component`, `ComponentGroup`
  - added first reusable controls: `Button`, `ButtonArray`
  - enforced GUI stable API dependency check inside `AnywareContext` (`REQUIRED_GUI_STABLE_API`)
  - added migration demos: `apps/app_anyware_template.py`, `apps/app_anyware_demo.py` (combined demo archive)
  - kept raw GUI access as explicit opt-in only (`allow_raw_gui`, `ctx.raw_gui()`)
- 0.0.2 (2026-02-13):
  - switched from shared GUI/Anyware doc versioning to dependency contract mode
  - Anyware now targets GUI compatibility by `GUI_API_LEVEL` and stable API tier
- 0.0.1 (2026-02-12):
  - formalized component universe
  - completed GUI capability gap review with ownership decisions
  - added detailed non-loop animation split (`A-ANM-*`) and dependency mapping to GUI-side requirements (`G-ANM-*`)
  - defined 0.1.0 MVP scope, milestones, and acceptance criteria
