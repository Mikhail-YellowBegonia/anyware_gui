# Roadmap

This is the canonical forward-looking plan. Other documents should link here instead of duplicating plan sections.

## Current Versions
- GUI Engine: `0.4.0`
- Anyware: `0.0.5`

## Integration Follow-ups (v0.0.4 DSKY)
Status note: GUI text primitives are done in v0.4.0; Anyware alignment + live reload are in place. The remaining items below are still open unless noted in recent commits.

- Add text measurement helpers in GUI and AnywareContext for single-line and multi-line label sizing. → Verify: unit-level test for ASCII/CJK sizing.
- Extend `Button` to support label alignment and multi-line rendering (explicit line breaks). → Verify: demo shows centered multiline labels.
- Introduce SegmentDisplay global defaults (size, spacing, colors) with per-instance override. → Verify: multiple instances share defaults without per-instance size.
- Wire PageStack into AnywareApp and implement `pop_page` (push/pop/replace behavior). → Verify: two-page app push/pop preserves lifecycle hooks.
- Add debug/layout mode toggle (grid overlay or simplified palette) for alignment tuning. → Verify: toggle flips overlay/palette without breaking normal rendering.
- Improve focus navigation scoring for non-rect grids (keypad). → Verify: DSKY keypad navigation matches intended flow.
- Update documentation to state Button label alignment/multiline limits and provide SegmentDisplay sizing guidance. → Verify: docs updated.
- Re-run DSKY integration app and update report if gaps remain. → Verify: updated report in integration_test.

## GUI Roadmap (from GUI_FRAMEWORK plan)
### Track A: Finish Current TODO (GUI Core)
Status: Done (2026-02-12)
- active scope runtime control and scope-restricted navigation
- blocker segments and blocked jump rejection
- cross-scope nav contract with deterministic demo links
- checklist-style widget validation in `apps/app_gauges_example.py`

### Track B: Software-Engineering Review + Docs Reorganization
Status: Done
- architecture boundaries clarified
- docs split (`GUI_FRAMEWORK.md`, `GUI_TUTORIAL.md`, `anyware_plan.md`)
- AI-coding guidance added to tutorial

### Track C: Anyware Reassessment and Early Implementation
- Freeze Anyware v0.1 scope (grid-first, minimal component set)
- Build minimal Anyware alpha on top of GUI
- Go/No-Go checkpoint (Anyware faster than raw GUI for non-trivial page)

### Track D: Dependency Decoupling
- Freeze GUI stable API list for Anyware
- Require Anyware startup compatibility check via `require_api_level(...)`
- Keep GUI/Anyware changelogs independent
- Add migration notes when stable API behavior changes

## Anyware MVP Plan (0.1.0)
### MVP Scope (initial component set)
- `Label`
- `Button`
- `ButtonArray`
- `CheckboxMenu`
- `ValueText`
- `MeterBar`
- `DialGauge`
- `SegmentDisplay` (P0.5)
- `PageRouter` (finite switch only)

### Milestones
M1. Baseline freeze (done in 0.0.1):
- architecture boundary confirmed
- component universe and gap map written

M2. GUI prerequisite patch:
- evaluate and implement `draw_*_progress` and/or `measure_text` if accepted
- update docs and one demo
Exit criteria:
- at least one progress draw primitive available
- one boot-style reveal demo proves non-loop timeline feasibility

M3. Anyware component implementation:
- implement MVP components with shared style/default model
- provide one medium-complexity page demo
Exit criteria:
- `IntroSequence` one-shot flow usable with component states
- animation can end in stable interactive page state

M4. Workflow validation:
- run target workflow:
  - hand-drawn layout -> natural language + rough coordinates -> AI first-pass -> limited rework -> human tuning -> verification
Exit criteria:
- AI output is logically correct before manual polish
- manual work is primarily spacing/style tuning, not behavior rewrite

### Acceptance Criteria
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
- demo archive usage (`demo_archive.md`)
