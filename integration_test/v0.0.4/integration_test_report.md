# DSKY Integration Test Report (v0.0.4)

## 1) Human -> AI Requirement Guidance and UI Tradeoffs

### How humans should describe requirements to AI
- Specify the coordinate system explicitly (grid vs pixel) and provide any aspect‑ratio compensation rule.
- Give a bounded reference frame (panel width/height and origin), even if rough.
- Provide a minimal set of anchor coordinates for each major block (status, display, keypad) rather than every element.
- Clarify what must be exact (e.g., text breaks, element ordering) vs what can be approximate (spacing, padding, micro‑alignment).
- State interaction intent separately from visuals (focus flow, selectable items, dummy placeholders).
- Provide one reference image and call out only the critical deltas that must match.
- Tell AI which components are allowed/preferred and which are optional.
- Confirm whether multi‑line labels must be hard line‑breaks or can be auto‑wrapped.

### AI UI implementation tradeoffs for fastest “logically correct” layout
- Choose grid‑first placement; convert to pixels only when required by drawing APIs.
- Prefer explicit constants over implicit/derived transforms when manual tuning is expected.
- Keep logic minimal and deterministic (no animation or random values) for integration tests.
- Use placeholders for stateful values; defer real behavior until layout is stable.
- Use consistent default sizes for repeated components, then adjust only after blocks align.
- Separate “focus” vs “select” behaviors in event handling to avoid UX coupling.
- Use the fewest component types needed to express the layout reliably.

## 2) Anyware/GUI/Docs Issues Observed (Needs and Friction)

- Button text is not centered and does not support multiline labels, which makes instrument UIs harder to reproduce.
- No built‑in text measurement or alignment helper, so centering and alignment are manual and error‑prone.
- SegmentDisplay has no global size/theme configuration, so scaling readability requires per‑instance edits.
- PageStack exists but is not wired into AnywareApp, and pop/stack navigation is missing at the app level.
- Lack of a debug/layout mode (e.g., grid overlay or simplified palette) slows visual tuning.
- Documentation does not state the limitations of Button label alignment or multiline handling.
- Documentation lacks recommended SegmentDisplay sizing ranges for readability.
- Focus navigation algorithm favors primary‑axis proximity (dy/dx) over angle or “down‑hemisphere” nearest, causing unexpected keypad navigation.

## Appendix: Test Artifacts
- App script: app_integration_dsky.py
- Prompt: integration_test_dsky_prompt.txt
- Layout spec: DSKY_layout.md
- Requirements list: dsky_integration_requirements.md
