# ValueText

Purpose
- Single-line numeric or string readout with optional label and unit.

Core Features
- Accepts raw value or `callable(ctx)->value`.
- Optional `label` and `unit` formatting.
- Uses Anyware text policy (`ctx.label()`).

Key Parameters
- `gx`, `gy`: grid anchor.
- `value`: `object` or `callable(ctx)->object`.
- `label`, `unit`, `fmt`: formatting options (`fmt` can be format string or callable).
- `color`, `orientation`, `line_step`: text rendering controls.

Behavior Notes
- If `value` resolves to `None`, renders empty string.
- Formatting is conservative and deterministic.

Example
```python
ValueText(gx=2, gy=1, label="SPEED", value=lambda c: c.frame.frame, unit="km/h")
```
