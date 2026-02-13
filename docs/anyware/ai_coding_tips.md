# Anyware AI Coding Tips (Pre-Integration)

Purpose
- Reduce test noise by keeping component output deterministic and layout-consistent.

Checklist (Instruments)
- Normalize numeric values to `[0, 1]` before rendering.
- Keep text APIs in grid units; shape APIs in pixel units.
- Use conservative defaults; avoid implicit magic values.
- Prefer clear, fixed geometry over dynamic auto-layout.
- Keep component rendering free of side effects.

Checklist (Buttons + Status)
- Use `pressable=False` for non-interactive indicators.
- Use `focusable=False` if the indicator should not capture focus.
- Prefer `status_color_map` for stable state visuals.

Demo Page Notes
- Add one minimal example per component.
- Avoid complex animation during integration tests.
