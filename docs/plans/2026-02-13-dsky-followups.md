# DSKY Follow-ups Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Finish DSKY follow-up fixes: focus scoring update, PageStack integration, combined Anyware demo, template hot reload, and doc cleanups.

**Architecture:** Update GUI focus scoring to weighted primary/secondary distances while keeping half-plane filtering and existing fallback. Replace AnywareApp’s PageRouter with PageStack plus a page registry. Provide a combined demo app that uses stack navigation. Add a reloadable layout file to the Anyware template. Update docs to reflect these changes.

**Tech Stack:** Python 3, pygame, core/GUI.py, core/anyware runtime/components, Anyware apps, Markdown docs.

---

### Task 1: Update Focus Scoring + Tests

**Files:**
- Modify: `core/GUI.py`
- Create: `integration_test/v0.4.0/test_gui_focus.py`

**Step 1: Write the failing test**

```python
# integration_test/v0.4.0/test_gui_focus.py
from core import GUI


def _reset():
    GUI.clear_focus_nodes()
    GUI.set_active_focus_scope("default")


def test_focus_score_prefers_low_weighted_secondary():
    _reset()
    GUI.add_focus_node("cur", (0, 0, 10, 10))
    GUI.add_focus_node("a", (30, 0, 10, 10))   # primary 30, secondary 0
    GUI.add_focus_node("b", (20, 12, 10, 10))  # primary 20, secondary 12
    GUI.set_focus("cur")
    # With score = primary + 2*secondary, "a" should win (30 vs 44)
    assert GUI.move_focus("right") == "a"


def test_focus_score_keeps_half_plane_filter():
    _reset()
    GUI.add_focus_node("cur", (0, 0, 10, 10))
    GUI.add_focus_node("left", (-30, 0, 10, 10))
    GUI.set_focus("cur")
    # Moving right should not choose a left-side candidate
    assert GUI.move_focus("right") == "cur"
```

**Step 2: Run test to verify it fails**

Run: `python3 integration_test/v0.4.0/test_gui_focus.py`
Expected: FAIL (current scoring does not use primary + 2*secondary).

**Step 3: Write minimal implementation**

```python
# core/GUI.py

def _focus_score(direction, cur_center, cand_center):
    dx = float(cand_center[0]) - float(cur_center[0])
    dy = float(cand_center[1]) - float(cur_center[1])
    eps = 1e-6
    if direction == "up":
        if dy >= -eps:
            return None
        primary = -dy
        secondary = abs(dx)
    elif direction == "down":
        if dy <= eps:
            return None
        primary = dy
        secondary = abs(dx)
    elif direction == "left":
        if dx >= -eps:
            return None
        primary = -dx
        secondary = abs(dy)
    elif direction == "right":
        if dx <= eps:
            return None
        primary = dx
        secondary = abs(dy)
    else:
        return None
    score = primary + 2.0 * secondary
    return (score, dx * dx + dy * dy)
```

**Step 4: Run test to verify it passes**

Run: `python3 integration_test/v0.4.0/test_gui_focus.py`
Expected: PASS

**Step 5: Commit**

```bash
git add integration_test/v0.4.0/test_gui_focus.py core/GUI.py
git commit -m "feat(gui): adjust focus scoring weights"
```

---

### Task 2: Wire PageStack into AnywareApp + Tests

**Files:**
- Modify: `core/anyware/runtime.py`
- Create: `integration_test/v0.4.0/test_anyware_page_stack.py`

**Step 1: Write the failing test**

```python
# integration_test/v0.4.0/test_anyware_page_stack.py
from core.anyware.page import Page, PageStack


class DummyPage(Page):
    def __init__(self, page_id: str, log: list[str]):
        super().__init__(page_id)
        self.log = log

    def on_enter(self, ctx) -> None:
        self.log.append(f"enter:{self.page_id}")

    def on_exit(self, ctx) -> None:
        self.log.append(f"exit:{self.page_id}")


def test_page_stack_push_pop_calls_hooks():
    ctx = object()
    stack = PageStack()
    log: list[str] = []
    p1 = DummyPage("p1", log)
    p2 = DummyPage("p2", log)

    stack.push(p1, ctx)
    stack.push(p2, ctx)
    stack.pop(ctx)

    assert log == ["enter:p1", "exit:p1", "enter:p2", "exit:p2", "enter:p1"]
```

**Step 2: Run test to verify it fails**

Run: `python3 integration_test/v0.4.0/test_anyware_page_stack.py`
Expected: PASS (baseline check for PageStack itself).

**Step 3: Write minimal implementation**

```python
# core/anyware/runtime.py
from .page import Page, PageStack

class AnywareApp:
    def __init__(...):
        ...
        self.page_stack = PageStack()
        self.page_registry: dict[str, Page] = {}
        ...

    def set_root_page(self, page: Page):
        self.page_registry[page.page_id] = page
        return self.page_stack.replace(page, self.ctx)

    def register_pages(self, pages: list[Page]):
        for page in pages:
            self.page_registry[page.page_id] = page
        return self

    def switch_page(self, page_id: str):
        page = self.page_registry.get(page_id)
        if page is None:
            return None
        return self.page_stack.replace(page, self.ctx)

    def push_page(self, page: Page):
        self.page_registry[page.page_id] = page
        return self.page_stack.push(page, self.ctx)

    def pop_page(self):
        return self.page_stack.pop(self.ctx)

    def _handle_event(self, event):
        ...
        return self.page_stack.handle_event(event, self.ctx)

    def run(self):
        ...
        self.page_stack.update(self.ctx, dt)
        self.page_stack.render(self.ctx)
        ...
        self.page_stack.clear(self.ctx)
```

**Step 4: Run test to verify it passes**

Run: `python3 integration_test/v0.4.0/test_anyware_page_stack.py`
Expected: PASS

**Step 5: Commit**

```bash
git add core/anyware/runtime.py integration_test/v0.4.0/test_anyware_page_stack.py
git commit -m "feat(anyware): integrate PageStack into runtime"
```

---

### Task 3: Combine Demo + Gauges into One PageStack App

**Files:**
- Modify: `apps/app_anyware_demo.py`
- Delete: `apps/app_anyware_gauges.py`

**Step 1: Write the failing test**

No automated test. This is a manual smoke test.

**Step 2: Run manual test to verify current behavior**

Run: `python3 apps/app_anyware_demo.py`
Expected: Single-page demo only.

**Step 3: Write minimal implementation**

```python
# apps/app_anyware_demo.py (sketch)
class DemoArchivePage(Page):
    def __init__(self, app, gauges_page):
        ...
        self._app = app
        self._gauges_page = gauges_page
        self.add(Label(... text="G: Gauges" ...))

    def handle_event(self, event, ctx):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_g:
            self._app.push_page(self._gauges_page)
            return True
        ...

class GaugesPage(Page):
    def __init__(self, app):
        ...
        self._app = app
        self.add(Label(... text="H: Home" ...))

    def handle_event(self, event, ctx):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
            self._app.pop_page()
            return True
        ...

# main()
app = AnywareApp(...)
 gauges = GaugesPage(app)
 demo = DemoArchivePage(app, gauges)
app.set_root_page(demo)
```

**Step 4: Run manual test to verify it works**

Run: `python3 apps/app_anyware_demo.py`
Expected: G pushes Gauges page, H pops back to Demo.

**Step 5: Commit**

```bash
git add apps/app_anyware_demo.py apps/app_anyware_gauges.py
git commit -m "feat(apps): combine demo pages with PageStack"
```

---

### Task 4: Add Hot Reload to Anyware Template

**Files:**
- Modify: `apps/app_anyware_template.py`
- Create: `apps/anyware_template_layout.py`

**Step 1: Write the failing test**

No automated test. This is a manual smoke test.

**Step 2: Run manual test to verify current behavior**

Run: `python3 apps/app_anyware_template.py`
Expected: No layout reload support.

**Step 3: Write minimal implementation**

```python
# apps/anyware_template_layout.py
TEXT_BOXES = [
    {"gx": 2, "gy": 1, "gw": 56, "gh": 2, "text": "ANYWARE TEMPLATE", "align_h": "left", "align_v": "top"},
    {"gx": 2, "gy": 3, "gw": 56, "gh": 2, "text": "ARROWS: focus  G: gauges  H: back", "align_h": "left", "align_v": "top"},
]
BUTTONS = [
    {"id": "demo_btn_1", "gx": 4, "gy": 8, "gw": 12, "gh": 2},
    {"id": "demo_btn_2", "gx": 19, "gy": 8, "gw": 12, "gh": 2},
]
```

```python
# apps/app_anyware_template.py (sketch)
class LayoutReloader:
    ...

class HomePage(Page):
    def __init__(self, layout):
        ...
        self._layout = layout

    def on_enter(self, ctx):
        for btn in self._layout.module.BUTTONS:
            x = ctx.gx(btn["gx"]) 
            y = ctx.gy(btn["gy"]) 
            w = ctx.gx(btn["gx"] + btn["gw"]) - x
            h = ctx.gy(btn["gy"] + btn["gh"]) - y
            ctx.add_focus_node(btn["id"], (x, y, w, h), scope="main")
        ...

    def render(self, ctx):
        for box in self._layout.module.TEXT_BOXES:
            ctx.draw_text_box(...)
        ...
```

**Step 4: Run manual test to verify it works**

Run: `python3 apps/app_anyware_template.py`
Expected: Editing `apps/anyware_template_layout.py` updates text/button positions live.

**Step 5: Commit**

```bash
git add apps/app_anyware_template.py apps/anyware_template_layout.py
git commit -m "feat(apps): add hot reload to Anyware template"
```

---

### Task 5: Update Docs + Cleanups

**Files:**
- Modify: `docs/AI_ASSISTED_DESIGN_GUIDE.md`
- Modify: `docs/ROADMAP.md`
- Modify: `docs/anyware/anyware_plan.md`

**Step 1: Write the failing test**

No automated test.

**Step 2: Update documentation**

```markdown
# docs/AI_ASSISTED_DESIGN_GUIDE.md
- Add a note under “新增固定要求” that the standard Anyware template now ships with hot reload enabled by default.

# docs/anyware/anyware_plan.md
- Update 5.1 to reflect PageStack support in AnywareApp and demo usage.

# docs/ROADMAP.md
- Mark PageStack integration, focus scoring update, and template hot reload as done.
```

**Step 3: Commit**

```bash
git add docs/AI_ASSISTED_DESIGN_GUIDE.md docs/anyware/anyware_plan.md docs/ROADMAP.md
git commit -m "docs: update DSKY follow-up notes"
```

---

## Manual Verification Checklist
- `python3 apps/app_anyware_demo.py` push/pop works (G/H).
- `python3 apps/app_anyware_template.py` reload works when editing layout file.
- DSKY integration app still runs (optional): `python3 apps/app_integration_dsky.py`.
