# Button

Purpose
- Focusable and selectable button with optional lighting and status display.

Core Features
- Focusable by default, optional non-focusable mode.
- Pressable toggle behavior by default.
- Optional status fill (mapped by `status_color_map`) and optional lighting.

Key Parameters
- `gx`, `gy`, `width_px`, `height_px`: layout.
- `pressable`, `focusable`: interaction control.
- `lighted`, `light_color`: optional lighting fill.
- `status`, `status_color_map`, `status_default_color`: status display fill.
- `label`, `color`, `nav`, `scope`, `on_select`.

Behavior Notes
- Status fill has priority over lighting fill.
- Use `pressable=False` + `focusable=False` for StatusLight-style indicators.

Example
```python
Button("status_light", "STATUS", gx=10, gy=4, width_px=70, pressable=False, focusable=False,
       status=lambda b, ctx: "ok", status_color_map={"ok": "CRT_Green"})
```
