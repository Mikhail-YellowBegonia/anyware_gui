# Anyware Plan

Anyware version: 0.0.1  
Target MVP version: 0.1.0  
Shared doc version: 0.3.8  
Doc role: planning/architecture (tutorial is `GUI_TUTORIAL.md`)

## 1) Positioning
- Anyware is a high-level component layer above `GUI.py`.
- Using Anyware still means writing real Python code.
- Two paths remain valid:
  - raw path: app -> `GUI.py`
  - component path: app -> `Anyware.py` -> `GUI.py`
- Design preference: grid-first composition, then local pixel tuning.

## 2) Layer Contract
1. `GUI.py` (engine):
- rendering primitives, coordinate conversion, focus/nav internals, draw queues, defaults.
- no business widget semantics.

2. `Anyware.py` (components):
- reusable widgets, page/scope composition helpers, interaction conventions.
- wraps `GUI.py`, no reverse dependency.

3. Use-case scripts (`app_*.py`):
- demos, template references, experimental integration.
- prototype place before promotion.

Promotion policy:
- app feature -> `GUI.py` only if at least 2/3:
  - repeated in multiple scenarios
  - low-level and domain-agnostic
  - does not significantly increase API complexity
- otherwise app feature -> `Anyware.py`.

Out-of-scope:
- `Sound.py` stays independent placeholder; not part of Anyware v0.1.0 MVP.

## 3) Component Universe (Planning Inventory)
This is the full planning inventory, not the immediate MVP scope.

### A. Structure / Page
- `Page`
- `PageStack` (`push/pop/replace`)
- `Panel`
- `Modal`
- `Tabs`

### B. Core Controls
- `Label`
- `Button`
- `ButtonArray`
- `Checkbox`
- `CheckboxMenu`
- `RadioGroup`
- `Input` (post-MVP)

### C. Display / Instrument
- `ValueText`
- `ProgressBar`
- `RoundGauge`
- `FanGauge`
- `StatusLight`
- `TrendLine` (post-MVP)

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
- missing capability is low-level and reusable -> should be in `GUI.py`.

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
- add low-level metric API in `GUI.py`:
  - `measure_text(content, ...) -> (w_px, h_px)`
- Anyware uses this for auto-sized controls.

### 4.3 Local reveal/clipping effects
Need:
- clip drawing in rect for reveal transitions.

Decision:
- optional for v0.1.0; if implemented, belongs to `GUI.py` (render primitive).

### 4.4 Complex VFX (particle/3D-grade motion)
Decision:
- not in current project responsibility (N/A for v0.1.0).

## 5) MVP Scope for Anyware 0.1.0
Minimum component set:
- `Button`
- `ButtonArray`
- `CheckboxMenu`
- `RoundGauge`
- `FanGauge`
- `PageStack` (minimal push/pop/replace only)

Minimum conventions:
- clear separation of focus vs select
- grid-first parameters where practical
- conservative defaults for AI template generation
- explicit scope integration hooks (optional, but consistent)

## 6) Milestones (0.0.1 -> 0.1.0)
M1. Baseline freeze (done in 0.0.1):
- architecture boundary confirmed
- component universe and gap map written

M2. GUI prerequisite patch:
- evaluate and implement `draw_*_progress` and/or `measure_text` if accepted
- update docs and one demo

M3. Anyware component implementation:
- implement MVP components with shared style/default model
- provide one medium-complexity page demo

M4. Workflow validation:
- run target workflow:
  - hand-drawn layout -> natural language + rough coordinates -> AI first-pass -> limited rework -> human tuning -> verification

## 7) Acceptance Criteria for Anyware 0.1.0
Must satisfy all:
1. A medium UI page can be assembled with fewer lines than raw GUI script.
2. AI-generated template is logically correct on first pass:
- coordinate type mostly correct
- navigation and state transitions correct
3. Remaining work is mainly human tuning/polish, not logic rewrite.
4. Documentation clearly explains:
- raw GUI path
- Anyware path
- grid/pixel conversion rules

## 8) Version Changelog (Anyware)
- 0.0.1 (2026-02-12):
  - formalized component universe
  - completed GUI capability gap review with ownership decisions
  - defined 0.1.0 MVP scope, milestones, and acceptance criteria
