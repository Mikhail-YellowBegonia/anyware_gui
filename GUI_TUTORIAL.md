# GUI Tutorial

Version: 0.3.9
Last Updated: 2026-02-13
Doc role: tutorial/learning path (feature/planning doc is `GUI_FRAMEWORK.md`)

## 0) Before You Start
This tutorial is ordered from easy to advanced.  
Always check coordinate type first, then write code.

Coordinate rules (must remember):
- `static/hstatic/sweep/clear_*`: use **grid** coordinates.
- `draw_rect/draw_poly/draw_pattern_*`: use **pixel** coordinates.
- Convert grid -> pixel with `gx()/gy()` when passing grid values to draw APIs.
- Convert pixel -> grid with `px()/py()` when passing pixel values to text APIs.

Quick mapping:
- `gx(n)`: grid x -> pixel x
- `gy(n)`: grid y -> pixel y
- `px(n)`: pixel x -> grid x
- `py(n)`: pixel y -> grid y

## 1) Minimal Frame Loop
Goal: draw a text title and one rectangle.

Parameter standard:
- Text call: grid
- Rect call: pixel

```python
GUI.begin_frame(clear_color="Black")

GUI.static(1, 1, "CRT_Cyan", "Hello")  # grid
GUI.draw_rect("CRT_Cyan", GUI.gx(1), GUI.gy(3), 64, 18, filled=False, thickness=1)  # pixel

GUI.finish_frame(screen_surf)
```

Engine contract tip:
- For Anyware integration, prefer `runtime = GUI.create_runtime(min_api_level=1)` and call `runtime.begin_frame(...)` / `runtime.finish_frame(...)`.

## 2) Coordinate-Safe Text + Shape Composition
Goal: draw shape by pixel anchor, then label near center.

Parameter standard:
- Center `(cx, cy)` from drawing is pixel.
- Label call `static(...)` needs grid.

```python
cx = GUI.gx(12)   # pixel
cy = GUI.gy(10)   # pixel
GUI.draw_rect("CRT_Cyan", cx - 20, cy - 10, 40, 20, filled=False, thickness=1)

label_x = int(round(GUI.px(cx)))   # grid
label_y = int(round(GUI.py(cy)))   # grid
GUI.static(label_x, label_y, "CRT_Cyan", "CENTER")
```

When to use `px/py`:
- You already have pixel position (from gauge center, poly anchor, collision result) and now need text/grid API.

## 3) Patterns and Poly Transform
Goal: hatch fill and transformed needle/polygon.

Parameter standard:
- draw APIs use pixel anchor.
- poly vertices are design-space points around origin `(0, 0)`.

```python
needle = GUI.rotate_poly_vertices("gauge_needle", angle_deg=30)
GUI.draw_poly(needle, "CRT_Cyan", GUI.gx(10), GUI.gy(10), filled=False, thickness=1)
GUI.draw_pattern_rect("CRT_Cyan", GUI.gx(20), GUI.gy(8), 80, 24, thickness=1)
```

## 4) Focus vs Select
Goal: understand interaction states.

Definitions:
- Focus: cursor currently points to a node (`GUI.get_focus()`).
- Select: app-level confirmed action (usually Enter/Space pressed).

Best practice:
- Render focus by border/frame.
- Update app state on select only.
- Do not treat focus as select.

## 5) Scope-Based Navigation (Track A Core)
Goal: build multiple interaction zones.

Parameter standard:
- Node rect uses pixel `(x, y, w, h)`.
- Scope is string (`"main"`, `"popup"`, `"checklist"` etc.).

```python
GUI.add_focus_node("main_btn_1", (GUI.gx(4), GUI.gy(6), 64, 18), scope="main")
GUI.add_focus_node("popup_btn_1", (GUI.gx(30), GUI.gy(16), 64, 18), scope="popup")
GUI.set_active_focus_scope("main")
```

Cross-scope link example:

```python
GUI.update_focus_node(
    "main_btn_1",
    nav={"down": {"scope": "popup", "id": "popup_btn_1"}}
)
```

## 6) Blocker
Goal: reject illegal focus jumps by segment blocking.

Parameter standard:
- Blocker points are pixel points.

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

## 8) Next Learning Path
1. Read `app_template.py` for minimal structure.
2. Read `app_example.py` for API surface.
3. Read `app_gauges_example.py` for advanced composition (scope/blocker/checklist).
4. Read `app_anyware_template.py` and `app_anyware_gauges.py` for class-based Anyware path.
5. Read `app_anyware_demo.py` as temporary Anyware demo archive page.
6. Then decide:
- stay raw `GUI.py` for precise control, or
- move to Anyware components for faster assembly.

## 9) AI Coding Strategy (Grid-First)
Positioning:
- In this project, AI is mainly responsible for **logical implementation**, not perfect visual design.
- The player/developer performs detailed tuning, polish, and small bug fixing.

Why grid-first for AI:
- AI is weaker at exact spatial judgment in pixel-level layout.
- Most functions can still be driven by grid references, then converted at render boundaries.
- This provides "logically correct and principled" layout output, even before fine tuning.

Recommended workflow:
1. Ask AI to output layout in grid coordinates first.
2. Keep text APIs in grid.
3. Convert only draw anchors/rects to pixel with `gx()/gy()`.
4. If a draw result returns pixel positions and you need labels, convert back with `px()/py()`.
5. Manually tune spacing/size/thickness after logic is confirmed.

Prompt guidance for AI-generated templates:
- Explicitly request coordinate type per call:
  - "Text calls must use grid coordinates."
  - "Shape and node rect calls must use pixel coordinates converted from grid via gx/gy."
- Explicitly request state split:
  - "Focus rendering and select state update must be separate."
- Explicitly request conservative defaults:
  - "Prefer default parameters unless necessary."

Minimum acceptance for AI output:
- coordinate types are correct
- navigation logic is correct
- state transitions are correct
- visual perfection can be deferred to manual tuning
