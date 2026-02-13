# MeterBar

Purpose
- Linear meter for progress, battery, signal, and usage bars.

Core Features
- `mode="bar"` for continuous fill.
- `mode="segments"` for discrete steps.
- Supports horizontal and vertical orientations.

Key Parameters
- `gx`, `gy`: grid anchor for the meter box.
- `width_px`, `height_px`: size in design pixels.
- `value`, `min_value`, `max_value`: normalization.
- `segments`, `gap_px`: only used in segment mode.
- `color`, `empty_color`, `border_color`: visual control.

Behavior Notes
- Normalizes value into `[0, 1]` and clamps.
- Segment fill uses deterministic thresholds.

Example
```python
MeterBar(gx=2, gy=4, width_px=120, height_px=10, value=lambda c: 0.62)
MeterBar(gx=2, gy=6, width_px=120, height_px=10, mode="segments", segments=8, value=5, max_value=8)
```
