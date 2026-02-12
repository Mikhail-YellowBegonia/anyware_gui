# GUI Framework Notes

Version: 0.3.7
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

### 4.5 Focus / Arrow Navigation (Phase 1)
- Node registry:
  - `add_focus_node(...)`, `update_focus_node(...)`, `remove_focus_node(...)`
  - `clear_focus_nodes()`, `list_focus_nodes()`, `get_focus_node(node_id)`
- Focus pointer:
  - `set_focus(node_id)`, `get_focus(default=None)`
- Movement:
  - `move_focus(direction)`, `key_to_focus_direction(key)`, `move_focus_by_key(key)`
- Selection rendering:
  - `grid_rect_to_px(...)`, `draw_focus_frame(...)`

Resolver order:
1. explicit `nav` link
2. coordinate directional nearest search
3. registration-order fallback

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

## 6) Current Scope / Next
- Implemented: basic arrow-key navigation in single-scope mode.
- Not implemented yet: focus hierarchy switching, blocker segments, cross-scope navigation semantics.

## 7) Change Log
- 0.3.7 (2026-02-12): Kept version; cleaned docs; added poly transform APIs (`transform/rescale/rotate/add_poly_transformed`) and transform demo in `app_example.py`; added coordinate reverse helpers `px/py`; retained basic arrow-key navigation phase-1 APIs.
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
