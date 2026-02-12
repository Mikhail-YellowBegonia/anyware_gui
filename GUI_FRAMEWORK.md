# GUI Framework Notes

Version: 0.3.8
Last Updated: 2026-02-12

## 1) Overview
- Core is a grid-based text renderer with overlay drawing.
- Text writes into `screen/screen_color`; each frame rasterizes to `screen_raw`.
- Overlay queues (`line_queue`, `fillpoly_queue`) are rendered after text.

## 2) Coordinates and Scaling
- Text APIs: grid coordinates `(x, y)` in character cells.
- Poly APIs: absolute pixel anchor `(x_px, y_px)`.
- Use `grid_to_px(...)`, `gx(...)`, `gy(...)` to map grid -> pixel.
- Use `px(...)`, `py(...)` to map pixel -> grid.
- Poly vertices are in design pixels and scale by:
  - `current_font_height / base_font_height_px`
- `PIXEL_SCALE` applies to final render pixels.

## 3) Recommended Frame Flow
1. `reset_overlays()`
2. `clear_screen(...)` (or `clear_row/clear_cell`)
3. Write text (`static/hstatic/ani_char/sweep`)
4. Enqueue overlays (`draw_poly/draw_rect/draw_pattern_*`)
5. `render(GUI.screen, GUI.screen_color)`
6. `draw_to_surface(surface)`

## 4) API Summary

### 4.1 Display / Window
- `set_display_defaults(...)`
- `reset_display_defaults()`
- `get_display_defaults()`
- `get_window_size_px()`
- `get_window_flags(extra_flags=0)`

Supported override keys:
- `fps`, `target_fps`
- `char_height`, `char_width`, `rows`, `cols`
- `char_block_spacing_px`, `line_block_spacing_px`, `border_padding_px`, `pixel_scale`
- `window_noframe`, `window_always_on_top`, `window_bg_color_rgb`

### 4.2 Text / Cell
- `static(x, y, color, content)`
- `hstatic(x, y, color, content, line_step=1)`
- `ani_char(x, y, color, animation, local_offset=None, global_offset=None, slowdown=None)`
- `sweep(row, col1, col2, color_start, color_end)`
- `clear_screen(char=' ', color=0)`
- `clear_row(y, char=' ', color=0)`
- `clear_cell(x, y, char=' ', color=0)`

### 4.3 Polygon / Pattern
- `add_poly(name, vertices_px, base_font_height_px=None)`
- `draw_poly(shape_or_vertices, color, x_px, y_px, filled=None, thickness=None, base_font_height_px=None)`
- `draw_rect(color, x_px, y_px, w_px, h_px, filled=None, thickness=None, base_font_height_px=None)`
- `draw_pattern_poly(shape_or_vertices, color, x_px, y_px, spacing=None, angle_deg=None, thickness=None, offset=None, base_font_height_px=None)`
- `draw_pattern_rect(color, x_px, y_px, w_px, h_px, spacing=None, angle_deg=None, thickness=None, offset=None, base_font_height_px=None)`

Pattern default values:
- `spacing=4.0`, `angle_deg=45.0`, `thickness=1.0`, `offset=0.0`
- Use `set_draw_defaults(pattern={...})` for global overrides.

### 4.3b Coordinate Helpers
- `grid_to_px(gx, gy, ox=0, oy=0)`
- `gx(grid_x)`, `gy(grid_y)` (grid -> pixel)
- `px(pixel_x)`, `py(pixel_y)` (pixel -> grid)

### 4.4 Poly Transform (New)
All transforms are around fixed origin `(0, 0)`.

- `transform_poly_vertices(shape_or_vertices, scale=1.0, scale_x=None, scale_y=None, angle_deg=0.0)`
  - Combined rescale + rotate.
- `rescale_poly_vertices(shape_or_vertices, scale=1.0, scale_x=None, scale_y=None)`
  - Rescale only.
- `rotate_poly_vertices(shape_or_vertices, angle_deg=0.0)`
  - Rotate only.
- `add_poly_transformed(name, source_shape_or_vertices, scale=1.0, scale_x=None, scale_y=None, angle_deg=0.0, base_font_height_px=None)`
  - Register transformed vertices as a new shape.

### 4.5 Focus / Arrow Navigation (Phase 1, Implemented)
- Node registry:
  - `add_focus_node(...)`, `update_focus_node(...)`, `remove_focus_node(...)`
  - `clear_focus_nodes()`, `list_focus_nodes()`, `get_focus_node(node_id)`
- Focus pointer:
  - `set_focus(node_id)`, `get_focus(default=None)`
  - `get_focus_scope(node_id=None, default=None)`
- Movement:
  - `move_focus(direction)`, `key_to_focus_direction(key)`, `move_focus_by_key(key)`
- Selection rendering:
  - `grid_rect_to_px(...)`, `draw_focus_frame(...)`
- Scope control:
  - `set_active_focus_scope(scope, pick_first=True)`
  - `get_active_focus_scope(default=None)`
  - `list_focus_scopes()`
- Blockers:
  - `add_focus_blocker(...)`, `update_focus_blocker(...)`, `remove_focus_blocker(...)`
  - `clear_focus_blockers(scope=None)`, `list_focus_blockers(scope=None)`, `draw_focus_blockers(...)`

Resolver order:
1. explicit `nav` link
2. coordinate directional nearest search
3. registration-order fallback

`nav` target forms:
- same-scope id: `"node_id"`
- explicit cross-scope: `{"scope": "popup", "id": "popup_btn_1"}` or `("popup", "popup_btn_1")`

### 4.5b Mechanism Notes (New)
State separation:
- Focus state: maintained by GUI focus pointer (`get_focus()`), means "cursor is on node".
- Select state: maintained by app logic, means "user confirmed action" (usually Enter/Space).
- Result: "focused" and "selected" are intentionally different states.

Scope mechanism:
- Active scope controls normal directional search domain.
- `set_active_focus_scope(scope, pick_first=True)` switches domain and can auto-pick first valid node.
- `set_focus(node_id, activate_scope=True)` can switch active scope to the target node's scope.

Directional move resolve order:
1. explicit `nav` target (supports cross-scope)
2. nearest directional candidate in active scope
3. registration-order fallback in active scope

Blocker mechanism:
- Blocker is a line segment in a specific scope.
- If jump segment (current-center -> candidate-center) intersects blocker segment, that candidate is rejected.
- When all candidates are blocked/invalid, pointer stays or falls back by resolver rules.

### 4.6 Dynamic Offsets
- `get_dynamic_offset(channel='default', default=0.0)`
- `set_dynamic_offset(channel='default', value=0.0, wrap=None)`
- `step_dynamic_offset(channel='default', speed=0.0, wrap=None)`
- `reset_dynamic_offsets(channel=None)`

### 4.7 Palette
- `refresh_palette_cache()`

## 5) Example Script
- `app_example.py` includes:
  - text APIs
  - clear APIs
  - pattern APIs
  - focus navigation demo
  - poly transform demo (rescale + rotate)
- `app_gauges_example.py` includes:
  - multi-scope focus switching (`main/popup/checklist`)
  - blocker demonstration
  - explicit cross-scope `nav` links
  - checkbox menu interaction demo (toggle by Enter/Space)

## 6) Current Scope / Next
- Track A status: completed and validated in testplace.
- Implemented: arrow-key navigation core + active scope + blockers + cross-scope nav target format.
- New validation case:
  - Added a minimal checkbox menu (`checklist` scope) in `app_gauges_example.py`.
  - Verified mixed-widget navigation route: `main -> popup -> checklist` and back with explicit cross-scope links.
- Page management (draft):
  - Prefer lightweight page list/router over viewport system for this project phase.
  - Target model: browser-like page stack (`push/pop/replace`) with full-screen scene switching.
  - Keep this as a lightweight orchestration layer above GUI core.

## 7) v0.3.8 -> v0.4.0 Mini Plan
Goal: close current TODOs, re-evaluate architecture with Anyware in scope, and ship a usable Anyware alpha entry.

### Track A: Finish Current TODO (GUI Core)
Status: Done (2026-02-12)
- [x] active scope runtime control and scope-restricted navigation
- [x] blocker segments and blocked jump rejection
- [x] cross-scope nav contract with deterministic demo links
- [x] checklist-style widget validation in `app_gauges_example.py`

### Track B: Software-Engineering Review + Docs Reorganization
1. Re-audit project boundaries
- Reconfirm responsibilities of `GUI.py`, app scripts, and future Anyware layer.
- Decide what remains function-level vs what is elevated to Anyware components.

2. Reorganize docs (md only)
- Keep `GUI_FRAMEWORK.md` as core reference.
- Make `subproject_anyware/anyware_plan.md` the Anyware product/architecture note.
- Add a concise migration note for users: "raw GUI API" vs "Anyware API".

3. Add anti-error guidance focused on real mistakes
- Coordinate mixing checklist (grid vs pixel), focus vs select state, draw order checklist.
- Acceptance:
  - At least 3 common mistakes have "symptom -> cause -> fix" entries.

### Track C: Anyware Reassessment and Early Implementation
1. Freeze Anyware v0.1 scope
- Keep fixed-grid philosophy.
- Start with a minimal component set:
  - `Button`, `ButtonArray`, `RoundGauge`, `FanGauge`.

2. Build minimal Anyware alpha
- Implement class-based wrappers on top of current `GUI.py` without forcing a full core refactor.
- Provide one demo script showing page assembly with those components.

3. Go/No-Go checkpoint before v0.4.0
- Go criteria:
  - Core TODOs in Track A are complete.
  - Anyware alpha can assemble one non-trivial page faster than raw GUI scripting.
  - Docs reflect both paths clearly (raw API + Anyware API).
- Otherwise: keep Anyware as design/prototype and release only core improvements in v0.4.0.

## 8) Change Log
- 0.3.8 (2026-02-12): Track A marked complete after validation; documented focus/select state separation, active scope behavior, blocker rejection rules, and directional resolve order; synchronized examples section with `app_gauges_example.py` multi-scope + checklist demo.
- 0.3.7 (2026-02-12): Kept version; cleaned docs; added poly transform APIs (`transform/rescale/rotate/add_poly_transformed`) and transform demo in `app_example.py`; added coordinate reverse helpers `px/py`; started Track A implementation with active scope, blocker APIs, and cross-scope nav target support (validated in `app_gauges_example.py` testplace); added minimal checkbox menu test (`checklist` scope) to validate mixed widgets under scope routing.
- 0.3.6 (2026-02-12): Added AI-coding assessment and navigation pre-design notes.
- 0.3.5 (2026-02-12): Added global dynamic offset channels and `app_example.py` showcase.
- 0.3.4 (2026-02-12): Added display/window override APIs and pattern thickness fix.
- 0.3.3 (2026-02-12): Added `hstatic`; added `draw_pattern_poly/draw_pattern_rect`.
- 0.3.2 (2026-02-12): Fixed wide-char overwrite/continuation issues; added clear APIs.
- 0.3.1 (2026-02-11): Added ASCII/CJK split font loading and no-upscale glyph behavior.
- 0.3.0 (2026-02-11): Switched to FreeType; added full-width/half-width handling.
- 0.2.0 (2026-02-11): Added default-priority rules and optional parameters.
- 0.1.1 (2026-02-11): Documented coordinate orientation.
- 0.1.0 (2026-02-11): Initial documentation.
