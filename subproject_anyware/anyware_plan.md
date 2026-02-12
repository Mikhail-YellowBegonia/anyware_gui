# Anyware Plan (v0.3.7 -> v0.4.0)

## Positioning
- Anyware is a higher-level UI toolbox built on top of `GUI.py`.
- Using Anyware is still standard Python programming, not a no-code layer.
- Layout philosophy remains fixed-grid first (not HTML-like flexible layout).

## Why Anyware
- Reduce repetitive wiring in raw GUI scripts:
  - focus node registration
  - navigation links
  - selected/focused rendering
  - component-local state handling
- Improve "template-first" development for AI-assisted coding.

## Scope for v0.4.0 Window

### 1) Prerequisite from GUI Core
Anyware implementation is gated by these core capabilities:
- active focus scope switching
- blocker-aware directional navigation
- cross-scope navigation semantics

If these are incomplete, Anyware remains prototype-only in this window.

### 2) Anyware v0.1 Candidate Components
- `Button`
- `ButtonArray`
- `RoundGauge`
- `FanGauge` (N1-like indicator)

Each component should provide:
- constructor-time style defaults
- explicit `update(state)` and `draw()` flow
- optional keyboard-focus integration

### 3) Minimal Architecture (No Large Core Refactor)
- Keep `GUI.py` as rendering and primitive drawing backend.
- Add Anyware as a separate layer (class-based wrappers).
- Avoid breaking existing function-based scripts.

## Documentation Reorganization Rules
- `GUI_FRAMEWORK.md`: core rendering/navigation API reference.
- `subproject_anyware/anyware_plan.md`: Anyware goals, architecture, and milestone status.
- Add one short migration note in docs:
  - when to stay on raw `GUI.py`
  - when to choose Anyware components

## Milestones
- M1: Core TODO closure status reviewed (scope/blocker/cross-scope).
- M2: Anyware v0.1 API draft frozen.
- M3: Anyware alpha demo page implemented.
- M4: Release decision for v0.4.0 (Go/No-Go).

## Go/No-Go Criteria for Anyware in v0.4.0
- Go:
  - alpha demo is stable
  - developer can assemble a medium UI page with fewer lines than raw GUI script
  - docs are clear enough for template-based AI generation
- No-Go:
  - keep Anyware as design/prototype notes
  - ship only GUI core improvements in v0.4.0
