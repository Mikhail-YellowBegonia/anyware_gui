# SegmentDisplay

Purpose
- Minimal 7-seg numeric display with decimal point for stylistic numeric readouts.

Core Features
- 7-seg glyphs (digits 0-9) with optional decimal point.
- Supports alignment, padding, and digit count.
- On/off colors for lit and unlit segments.
- Segment polygons are hardcoded by default; you can override them via `segment_polys`.

Key Parameters
- `gx`, `gy`: grid anchor.
- `text`: `str` or `callable(ctx)->str`.
- `digits`, `align`, `pad_char`: layout control.
- `digit_w_px`, `digit_h_px`, `spacing_px`: geometry control.
- `on_color`, `off_color`: visual control.
- `segment_polys`: override normalized segment polygons (0..1 box).

Behavior Notes
- `.` sets the decimal point on the previous digit when possible.
- Unknown characters render as blank segments.

Example
```python
SegmentDisplay(gx=2, gy=12, text="12.3", digits=4, on_color="CRT_Cyan", off_color="CRT_BlueDark")
```
