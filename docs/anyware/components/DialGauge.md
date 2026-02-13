# DialGauge

Purpose
- General dial/arc gauge (speed, RPM, pressure, compass).

Core Features
- `style="needle"|"fill"|"both"`.
- Configurable angle span with `start_angle_deg` and `end_angle_deg`.
- Uses consistent normalization with `min_value` / `max_value`.

Key Parameters
- `center_gx`, `center_gy`: grid anchor of dial center.
- `radius_px`: gauge radius in design pixels.
- `value`, `min_value`, `max_value`: normalization.
- `style`, `needle_width_px`, `fill_steps`: visual control.

Behavior Notes
- Arc fill is a polygon fan; needle is a thin polygon line.
- Same component covers round and fan gauges by config.

Example
```python
DialGauge(center_gx=20, center_gy=10, radius_px=40, value=0.7, style="both")
```
