# Developer Reference (Secondary Development)

Version: 0.4.0
Last Updated: 2026-02-15
Doc role: detailed secondary development reference. Planning lives in `GUI_FRAMEWORK.md` and `docs/anyware/anyware_plan.md`.

## Document Map
- Planning: `GUI_FRAMEWORK.md`, `docs/anyware/anyware_plan.md`
- Overview tutorial: `GUI_TUTORIAL.md`
- AI coding: `AI_ASSISTED_DESIGN_GUIDE.md`

## Architecture and Layer Contract
This project keeps two valid usage paths:
- Raw path: apps call `core/GUI.py` directly for low-level control.
- Anyware path: apps call `core/anyware/*` for high-level widgets and composition.

Layer responsibilities:
- `core/GUI.py` (engine layer)
- Owns rendering primitives, coordinate system, input-to-navigation mechanism, focus internals, draw queues, and global defaults.
- Should not own business-oriented widgets or page-level flow semantics.

- `core/anyware` (component layer)
- Owns reusable UI component abstractions (`Button`, `Checkbox`, gauges, arrays, page helpers).
- Wraps `core/GUI.py` and provides state->view mapping plus interaction conventions.
- `core/Anyware.py` is compatibility-only import bridge.

- Use-case collection (`app_*.py`)
- Owns demos, templates, and exploratory compositions.
- May prototype candidate components before promotion to Anyware.

Dependency rule:
- `core/anyware` depends on `core/GUI.py`.
- apps may depend on either/both.
- `core/GUI.py` must not depend on `core/anyware` or app scripts.

Feature intake policy:
- Promote code from app -> `core/GUI.py` only if at least two of these hold:
- used repeatedly in multiple scenarios/components
- semantically low-level and domain-agnostic
- adding it does not significantly increase GUI API complexity
- Otherwise, promote app code to `core/anyware`, not `core/GUI.py`.

## Coordinates and Scaling
- Text APIs: grid coordinates `(x, y)` in character cells.
- Poly APIs: absolute pixel anchor `(x_px, y_px)`.
- Use `grid_to_px(...)`, `gx(...)`, `gy(...)` to map grid -> pixel.
- Use `px(...)`, `py(...)` to map pixel -> grid.
- Poly vertices are in design pixels and scale by `current_font_height / base_font_height_px`.
- `PIXEL_SCALE` applies to final render pixels.

Quick mapping:
- `gx(n)`: grid x -> pixel x
- `gy(n)`: grid y -> pixel y
- `px(n)`: pixel x -> grid x
- `py(n)`: pixel y -> grid y

## Recommended Frame Flow
1. `begin_frame(clear_char=' ', clear_color=...)`
2. Write text (`static/hstatic/ani_char/sweep`)
3. Enqueue overlays (`draw_poly/draw_rect/draw_pattern_*`)
4. `finish_frame(surface)`
5. `pygame.display.flip()` (in app loop)
6. `clock.tick(target_fps)` (in app loop)

## Layout Mode (Palette Override)
- API: `GUI.set_layout_mode(True)` / `GUI.set_layout_mode(False)`
- Behavior:
  - background forced to `(200, 190, 180)`
  - all other colors forced to `(130, 159, 23)`
- Anyware template: toggle `LAYOUT_MODE` in `apps/anyware_template_layout.py` and it will hot-reload.

## GUI API Summary
Engine contract and versioning:
- `GUI_ENGINE_VERSION`, `GUI_API_LEVEL`
- `get_engine_manifest()`
- `require_api_level(min_api_level)`
- `get_api_contract()`

Display and window:
- `set_display_defaults(...)`
- `reset_display_defaults()`
- `get_display_defaults()`
- `get_window_size_px()`
- `get_window_flags(extra_flags=0)`
- `next_frame(step=1)`
- `begin_frame(...)`
- `finish_frame(surface, flip=False)`
- `GuiRuntime` / `create_runtime(...)`

Text and cell:
- `static(x, y, color, content)`
- `hstatic(x, y, color, content, line_step=1)`
- `ani_char(x, y, color, animation, local_offset=None, global_offset=None, slowdown=None)`
- `sweep(row, col1, col2, color_start, color_end)`
- `clear_screen(char=' ', color=0)`
- `clear_row(y, char=' ', color=0)`
- `clear_cell(x, y, char=' ', color=0)`

Polygon and pattern:
- `add_poly(name, vertices_px, base_font_height_px=None)`
- `draw_poly(shape_or_vertices, color, x_px, y_px, filled=None, thickness=None, base_font_height_px=None)`
- `draw_rect(color, x_px, y_px, w_px, h_px, filled=None, thickness=None, base_font_height_px=None)`
- `draw_pattern_poly(shape_or_vertices, color, x_px, y_px, spacing=None, angle_deg=None, thickness=None, offset=None, base_font_height_px=None)`
- `draw_pattern_rect(color, x_px, y_px, w_px, h_px, spacing=None, angle_deg=None, thickness=None, offset=None, base_font_height_px=None)`

Coordinate helpers:
- `grid_to_px(gx, gy, ox=0, oy=0)`
- `gx(grid_x)`, `gy(grid_y)`
- `px(pixel_x)`, `py(pixel_y)`

Focus and navigation:
- `add_focus_node(...)`, `update_focus_node(...)`, `remove_focus_node(...)`
- `clear_focus_nodes()`, `list_focus_nodes()`, `get_focus_node(node_id)`
- `set_focus(node_id)`, `get_focus(default=None)`
- `get_focus_scope(node_id=None, default=None)`
- `move_focus(direction)`, `key_to_focus_direction(key)`, `move_focus_by_key(key)`
- `grid_rect_to_px(...)`, `draw_focus_frame(...)`
- `set_active_focus_scope(scope, pick_first=True)`
- `get_active_focus_scope(default=None)`
- `list_focus_scopes()`
- `add_focus_blocker(...)`, `update_focus_blocker(...)`, `remove_focus_blocker(...)`
- `clear_focus_blockers(scope=None)`, `list_focus_blockers(scope=None)`, `draw_focus_blockers(...)`

Dynamic offsets:
- `get_dynamic_offset(channel='default', default=0.0)`
- `set_dynamic_offset(channel='default', value=0.0, wrap=None)`
- `step_dynamic_offset(channel='default', speed=0.0, wrap=None)`
- `reset_dynamic_offsets(channel=None)`

## Anyware Components Reference
Button:
- Focusable and selectable button with optional lighting and status display.
- Key parameters: `gx`, `gy`, `width_px`, `height_px`, `pressable`, `focusable`, `lighted`, `status`, `status_color_map`, `label_align_h`, `label_align_v`, `label_line_step`, `label_orientation`.

ButtonArray:
- Grid collection of `Button` with deterministic local nav.
- Key parameters: `labels`, `gx`, `gy`, `cols`, `rows`, `gx_spacing`, `gy_spacing`, `scope`.

ValueText:
- Label + formatted numeric value.
- Key parameters: `label`, `value`, `fmt`, `gx`, `gy`, `color`.

MeterBar:
- Linear meter (bar or segments).
- Key parameters: `value`, `min_value`, `max_value`, `mode`, `segments`, `width_px`, `height_px`.

DialGauge:
- Arc gauge with needle/fill styles.
- Key parameters: `center_gx`, `center_gy`, `radius_px`, `start_angle_deg`, `end_angle_deg`, `style`.

SegmentDisplay:
- Multi-segment digital tube display (7-seg default).
- Key parameters: `digits`, `align`, `pad_char`, `digit_w_px`, `digit_h_px`, `spacing_px`, `on_color`, `off_color`.

PageRouter and PageStack:
- `PageRouter` is finite state switching.
- `PageStack` supports push/pop/replace for multi-page flows.

## Demo Archive Policy
- Keep demos runnable under current `GUI_API_LEVEL`.
- Prefer Anyware components over direct `GUI.py` calls.
- If temporary workarounds need raw GUI access, mark them explicitly and remove later.
- `apps/app_anyware_demo.py` is the combined demo archive entry.
