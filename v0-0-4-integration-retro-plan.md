# v0.0.4 Integration Test Retro and Plan

## Goal
Address DSKY integration test findings by closing layout, navigation, and documentation gaps in Anyware/GUI.

## Tasks
- [ ] Add text measurement helpers in GUI and AnywareContext for single-line and multi-line label sizing. → Verify: unit-level manual check by calling helper in a small script and confirming returned width/height for ASCII and CJK samples.
- [ ] Extend `Button` to support label alignment and multi-line rendering (with explicit line breaks) without breaking existing defaults. → Verify: update demo/app to show centered multi-line labels; confirm alignment visually.
- [ ] Introduce SegmentDisplay global defaults (size, spacing, colors) with per-instance override. → Verify: set defaults once and instantiate multiple displays with consistent sizing without passing per-instance size.
- [ ] Wire PageStack into AnywareApp and implement `pop_page` (push/pop/replace behavior). → Verify: minimal two-page app can push and pop while preserving lifecycle hooks.
- [ ] Add debug/layout mode toggle (grid overlay or simplified palette) to speed alignment work. → Verify: toggle flag changes overlay or palette without breaking normal rendering.
- [ ] Improve focus navigation scoring to reduce unexpected jumps on non-rect grids (e.g., keypad). → Verify: DSKY keypad navigation matches intended directional flow in the integration app.
- [ ] Update documentation to state Button label alignment/multiline limits and provide SegmentDisplay sizing guidance. → Verify: docs mention constraints and recommended ranges in `docs/anyware/components/Button.md` and `docs/anyware/components/SegmentDisplay.md`.
- [ ] Re-run DSKY integration app and update report/requirements notes if gaps remain. → Verify: `integration_test/v0.0.4/integration_test_report.md` updated with outcomes.

## Done When
- [ ] DSKY layout and navigation are materially closer to spec, and documentation reflects new capabilities and constraints.
