# GUI Framework Plan

Version: 0.4.0
Last Updated: 2026-02-15
Doc role: core planning and roadmap detail for the GUI engine + consolidated GUI reference.

## 0) Documentation Split
- Core docs: `GUI_FRAMEWORK.md`, `docs/anyware/anyware_plan.md`
- Planning: `GUI_FRAMEWORK.md`, `docs/anyware/anyware_plan.md`
- Consolidated reference: `GUI_FRAMEWORK.md`
- Anyware plan + AI workflow: `docs/anyware/anyware_plan.md`

## 1) Active GUI Work Items
- GUI-FOCUS-SCORING: weighted focus scoring (`primary + 2*secondary`). Status: Done (2026-02-15)
- GUI-TEXT-METRICS: text measurement helpers for sizing/alignment. Status: Done (2026-02-15)
- GUI-DEBUG-LAYOUT: layout mode (simplified palette) via `GUI.set_layout_mode(True)`. Status: Done (2026-02-15)
- GUI-DSKY-RETEST: re-run DSKY integration app and update report. Status: Done (2026-02-15)

## 2) GUI Roadmap (Historical Tracks)
Track A: Finish Current TODO (GUI Core)
- Status: Done (2026-02-12)
- active scope runtime control and scope-restricted navigation
- blocker segments and blocked jump rejection
- cross-scope nav contract with deterministic demo links
- checklist-style widget validation in `apps/app_gauges_example.py`

Track B: Software-Engineering Review + Docs Reorganization
- Status: Done
- architecture boundaries clarified
- docs split (`GUI_FRAMEWORK.md`, `anyware_plan.md`)
- AI-coding guidance consolidated into `docs/anyware/anyware_plan.md`

Track C: Anyware Reassessment and Early Implementation
- Freeze Anyware v0.1 scope (grid-first, minimal component set)
- Build minimal Anyware alpha on top of GUI
- Go/No-Go checkpoint (Anyware faster than raw GUI for non-trivial page)

Track D: Dependency Decoupling
- Freeze GUI stable API list for Anyware
- Require Anyware startup compatibility check via `require_api_level(...)`
- Keep GUI/Anyware changelogs independent
- Add migration notes when stable API behavior changes

## 3) Usage & Coordinate Discipline (Merged)
Coordinate rules (critical):
- `static/hstatic/sweep/clear_*`: use **grid** coordinates.
- `draw_rect/draw_poly/draw_pattern_*`: use **pixel** coordinates.
- Convert grid -> pixel with `gx()/gy()` when passing grid values to draw APIs.
- Convert pixel -> grid with `px()/py()` when passing pixel values to text APIs.

Quick mapping:
- `gx(n)`: grid x -> pixel x
- `gy(n)`: grid y -> pixel y
- `px(n)`: pixel x -> grid x
- `py(n)`: pixel y -> grid y

Scaling notes:
- Poly vertices are in design pixels and scale by `current_font_height / base_font_height_px`.
- `PIXEL_SCALE` applies to final render pixels.
- `dpi_scale` applies a device pixel ratio (e.g., Retina 2.0) without changing logical layout.
- `window_scale` scales the presented window size without changing render resolution.
  - `get_present_size_px()` returns logical window size.
  - `get_present_surface_size_px()` returns expected device-pixel size after DPI.

## 4) Minimal Frame Loop (pygame presenter)
Goal: draw a text title and one rectangle.

```python
GUI.begin_frame(clear_color="Black")

GUI.static(1, 1, "CRT_Cyan", "Hello")  # grid
GUI.draw_rect("CRT_Cyan", GUI.gx(1), GUI.gy(3), 64, 18, filled=False, thickness=1)  # pixel

GUI.finish_frame(screen_surf)
```

Engine contract tip:
- For Anyware integration, prefer `runtime = GUI.create_runtime(min_api_level=1)` and call
  `runtime.begin_frame(...)` / `runtime.finish_frame(...)`.

Recommended frame flow (pygame presenter):
1. `begin_frame(clear_char=' ', clear_color=...)`
2. Write text (`static/hstatic/ani_char/sweep`)
3. Enqueue overlays (`draw_poly/draw_rect/draw_pattern_*`)
4. `finish_frame(surface)`
5. `pygame.display.flip()`
6. `clock.tick(target_fps)`

## 5) Focus vs Select
Definitions:
- Focus: cursor currently points to a node (`GUI.get_focus()`).
- Select: app-level confirmed action (usually Enter/Space pressed).

Best practice:
- Render focus by border/frame.
- Update app state on select only.
- Do not treat focus as select.

## 6) Scope Navigation + Blockers
Scope example:

```python
GUI.add_focus_node("main_btn_1", (GUI.gx(4), GUI.gy(6), 64, 18), scope="main")
GUI.add_focus_node("popup_btn_1", (GUI.gx(30), GUI.gy(16), 64, 18), scope="popup")
GUI.set_active_focus_scope("main")
```

Cross-scope link:

```python
GUI.update_focus_node(
    "main_btn_1",
    nav={"down": {"scope": "popup", "id": "popup_btn_1"}}
)
```

Blocker example:

```python
GUI.add_focus_blocker(
    "main_mid",
    (GUI.gx(20), GUI.gy(5)),
    (GUI.gx(20), GUI.gy(20)),
    scope="main"
)
GUI.draw_focus_blockers("blink10", scope="main", thickness=1)
```

## 7) Common Mistakes (Coordinate-Critical)
1. Symptom: text drawn at wrong place after gauge draw.
- Cause: directly using pixel center in `static(...)`.
- Fix: convert with `px()/py()` first.

2. Symptom: rectangle appears far away from expected grid location.
- Cause: passing grid values directly to `draw_rect(...)`.
- Fix: convert with `gx()/gy()` for x/y anchor.

3. Symptom: focus box does not match visual button.
- Cause: node rect provided in grid units by mistake.
- Fix: node rect must be pixel; use `gx()/gy()` when defining rect.

## 8) Learning Path (Reference)
1. `apps/app_template.py` for minimal structure.
2. `apps/app_example.py` for API surface.
3. `apps/app_gauges_example.py` for advanced composition (scope/blocker/checklist).
4. `apps/app_anyware_template.py` + `apps/layouts/anyware_template_layout.yaml` for Anyware + DSL hot reload.
5. `apps/app_anyware_text_layout_demo.py` + `apps/layouts/text_layout_demo_layout.yaml` for DSL + custom overlays.
6. (Optional) `apps/app_anyware_demo.py` for a complex Python-driven demo archive.

## 9) Layout Mode (Palette Override)
- API: `GUI.set_layout_mode(True)` / `GUI.set_layout_mode(False)`
- Behavior:
  - background forced to `(200, 190, 180)`
  - all other colors forced to `(130, 159, 23)`

## 10) GUI API Summary (Reference)
Engine contract and versioning:
`GUI_ENGINE_VERSION`, `GUI_API_LEVEL`, `get_engine_manifest()`, `require_api_level(min_api_level)`, `get_api_contract()`

Display and window:
`set_display_defaults(...)`, `reset_display_defaults()`, `get_display_defaults()`, `get_render_size_px()`,
`get_present_size_px()`, `get_present_surface_size_px()`, `get_window_size_px()`, `get_window_flags(...)`,
`get_dpi_scale()`, `detect_display_dpi_scale(...)`, `apply_display_dpi_from_surface(...)`, `init_pygame_display(...)`,
`next_frame(...)`, `begin_frame(...)`,
`finish_frame(...)`, `GuiRuntime`, `create_runtime(...)`

Text and cell:
`static(...)`, `hstatic(...)`, `ani_char(...)`, `sweep(...)`, `clear_screen(...)`, `clear_row(...)`, `clear_cell(...)`

Polygon and pattern:
`add_poly(...)`, `draw_poly(...)`, `draw_rect(...)`, `draw_pattern_poly(...)`, `draw_pattern_rect(...)`

Coordinate helpers:
`grid_to_px(...)`, `gx(...)`, `gy(...)`, `px(...)`, `py(...)`

Focus and navigation:
`add_focus_node(...)`, `update_focus_node(...)`, `remove_focus_node(...)`, `clear_focus_nodes()`, `list_focus_nodes()`,
`get_focus_node(...)`, `set_focus(...)`, `get_focus(...)`, `get_focus_scope(...)`, `move_focus(...)`,
`key_to_focus_direction(...)`, `move_focus_by_key(...)`, `grid_rect_to_px(...)`, `draw_focus_frame(...)`,
`set_active_focus_scope(...)`, `get_active_focus_scope(...)`, `list_focus_scopes()`,
`add_focus_blocker(...)`, `update_focus_blocker(...)`, `remove_focus_blocker(...)`, `clear_focus_blockers(...)`,
`list_focus_blockers(...)`, `draw_focus_blockers(...)`

Dynamic offsets:
`get_dynamic_offset(...)`, `set_dynamic_offset(...)`, `step_dynamic_offset(...)`, `reset_dynamic_offsets(...)`
