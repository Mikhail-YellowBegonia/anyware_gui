# Anyware Plan

Anyware version: 0.0.6  
Target MVP version: 0.1.0  
GUI dependency baseline: `GUI_API_LEVEL >= 1`  
Doc role: planning/architecture (tutorial is `../GUI_TUTORIAL.md`, reference is `../DEV_GUIDE.md`)

## 0) Active Anyware Work Items
- ANY-PAGESTACK: PageStack runtime integration in AnywareApp. Status: Done (2026-02-15)
- ANY-TEMPLATE-RELOAD: Anyware template supports hot reload for layout params. Status: Done (2026-02-15)
- ANY-BUTTON-ALIGN: Button label alignment + multiline support. Status: Done (2026-02-15)
- ANY-DYNAMIC-COMPONENTS: flat reconcile-based dynamic component management. Status: Done (2026-02-15)
- ANY-SEGMENT-DEFAULTS: SegmentDisplay global defaults (size, spacing, colors). Status: Done (2026-02-16)
- ANY-SEGMENT-THEME: SegmentDisplay global theme or shared style defaults. Status: Done (2026-02-16)
- ANY-CHECKBOX-MENU: implement `CheckboxMenu` (MVP component). Status: Done (2026-02-16)
- ANY-LAYOUT-DSL: YAML layout DSL + loader (styles, bindings, slots). Status: In progress (2026-02-22)

## 1) Positioning
- Anyware is a high-level component layer above `core/GUI.py`.
- Using Anyware still means writing real Python code.
- Two paths remain valid:
  - raw path: app -> `core/GUI.py`
  - component path: app -> `core/anyware/*` -> `core/GUI.py`
- Design preference: grid-first composition, then local pixel tuning.

## 2) Layer Contract
1. `core/GUI.py` (engine):
- rendering primitives, coordinate conversion, focus/nav internals, draw queues, defaults.
- no business widget semantics.
- publishes compatibility via `GUI_API_LEVEL` and stable API contract.

2. `core/anyware` (components package):
- reusable widgets, page/scope composition helpers, interaction conventions.
- wraps `core/GUI.py`, no reverse dependency.
- validates dependency at startup via `require_api_level(...)`.
- compatibility entrypoint: `core/Anyware.py` (legacy import bridge).

### 2.1 App API Access Policy
- Default path: app code should call Anyware classes/context only.
- Text policy: Anyware app code should use `Label/Text` component or `ctx.label()/ctx.text()`, not `static/hstatic` directly.
- Escape hatch: raw `core/GUI.py` access is allowed only as explicit opt-in (debug/migration/specialized rendering).
- Enforce by runtime flag:
  - `allow_raw_gui=False` by default.
  - `ctx.raw_gui()` raises when raw access is not explicitly enabled.
- Long-term target:
  - keep raw access usage close to zero in production Anyware apps.

3. Use-case scripts (`app_*.py`):
- demos, template references, experimental integration.
- prototype place before promotion.

Promotion policy:
- app feature -> `core/GUI.py` only if at least 2/3:
  - repeated in multiple scenarios
  - low-level and domain-agnostic
  - does not significantly increase API complexity
- otherwise app feature -> `core/anyware`.

Out-of-scope:
- `core/Sound.py` stays independent placeholder; not part of Anyware v0.1.0 MVP.

## 3) Component Universe (Planning Inventory)
This is the full planning inventory, not the immediate MVP scope.

### A. Structure / Page
- `Page`
- `PageRouter` (simple switch)
- `Panel`
- `Modal`
- `Tabs`

### B. Core Controls
- `Label`
- `Button`
- `ButtonArray`
- `Button` supports optional status/lighting (StatusLight merged)
- `Checkbox`
- `CheckboxMenu`
- `RadioGroup`
- `Input` (post-MVP)

### C. Display / Instrument
- `ValueText`
- `MeterBar` (bar/segments)
- `DialGauge` (round/fan via config)
- `SegmentDisplay` (P0.5)
- `TrendLine` (post-MVP)

Instrument consolidation decisions:
- MeterBar merges progress/battery/signal/level into one component (bar vs segments).
- DialGauge merges round/fan/arc gauges into one configurable component.
- StatusLight is modeled as a non-pressable `Button` with status/lighting.
- SegmentDisplay stays separate (design-driven logic, 7-seg baseline).
- TrendLine is deferred (state ownership + sampling policy).

### D. Feedback / Utility
- `Toast`
- `ConfirmDialog`
- `Loading`
- `CursorHint`

### E. Navigation Helpers
- `FocusGroup`
- `ScopeRouter`
- `ShortcutMap`

### F. Animation Wrappers
- `IntroSequence`
- `Blink`
- `SweepReveal`
- `Typewriter`
- `StrokeDraw`

## 4) Capability Gap Review (GUI vs Anyware vs N/A)
Method: define desired feature -> decide if current GUI can directly support -> locate missing responsibility.

### 4.1 Opening Animation Example: "shape draws gradually"
Feature definition:
- draw a line/poly progressively by `progress` in `[0, 1]`, not instant full draw.

Current status:
- can be approximated by manual frame logic, but no standard primitive for path-progress drawing.

Decision:
- missing capability is low-level and reusable -> should be in `core/GUI.py`.

Proposed GUI additions:
1. `draw_line_progress(p1, p2, progress, ...)`
2. `draw_poly_progress(shape_or_vertices, progress, mode='stroke', ...)`

Anyware responsibility:
- timeline/easing/sequence orchestration (`IntroSequence`, staged animation scripting).

### 4.2 Text-aware layout sizing
Need:
- estimate text size for predictable box/layout assembly.

Current status:
- no direct standard API for text pixel metrics.

Decision:
- add low-level metric API in `core/GUI.py`:
  - `measure_text(content, ...) -> (w_px, h_px)`
- Anyware uses this for auto-sized controls.

### 4.3 Local reveal/clipping effects
Need:
- clip drawing in rect for reveal transitions.

Decision:
- optional for v0.1.0; if implemented, belongs to `core/GUI.py` (render primitive).

### 4.4 Complex VFX (particle/3D-grade motion)
Decision:
- not in current project responsibility (N/A for v0.1.0).

### 4.5 Non-Loop Animation Split (Anyware Side)
Design statement:
- Non-loop animation is a finite sequence over time, not a special render mode.
- Anyware owns "what happens when"; GUI owns "how current frame is drawn".

Anyware requirements (proposed):
1. A-ANM-01 Timeline container (P0)
- `IntroSequence` supports ordered steps with `delay`, `duration`, `once`.
- can stop at final frame/state (non-loop by default).

2. A-ANM-02 Step model (P0)
- step receives normalized `progress` in `[0, 1]`.
- step can target component props (visibility, color level, gauge fill, text reveal length).

3. A-ANM-03 Trigger/finish protocol (P0)
- explicit lifecycle: `idle -> running -> finished`.
- supports one-shot start for boot animation.

4. A-ANM-04 Easing and defaults (P1)
- built-in minimal easing set (`linear`, `ease_in`, `ease_out`).
- default should be conservative and predictable for AI-generated templates.

5. A-ANM-05 Interrupt and skip policy (P1)
- allow "skip animation" and jump to final stable state.
- required for practical UX and debugging.

6. A-ANM-06 Scope-safe interaction during animation (P1)
- define whether focus/navigation is disabled, limited, or fully enabled while intro plays.
- default policy should avoid ambiguous interaction states.

Dependencies on GUI requirements:
- A-ANM-01/02 depend on `G-ANM-01` and `G-ANM-02` for progressive drawing.
- A-ANM-02 depends on `G-ANM-03` for text-bound animation sizing.
- A-ANM-04/05 benefit from `G-ANM-05` stable timing helpers.
- A-ANM-06 can be implemented with existing focus/scope APIs.

## 5) MVP Scope for Anyware 0.1.0
Minimum component set:
- `Label`
- `Button`
- `ButtonArray`
- `CheckboxMenu`
- `ValueText`
- `MeterBar`
- `DialGauge`
- `SegmentDisplay` (P0.5)
- `PageRouter` (finite switch only)

## 5.1 Page Logic (FSM + Stack)
- AnywareApp now uses `PageStack` (push/pop/replace) for multi-page flows.
- `PageRouter` remains available for simple FSM-only page switching.
- Keep stack depth shallow during early integration tests; avoid hidden transitions.

## 5.2 AI Coding Tips (Integration Prep)
- See `../AI_ASSISTED_DESIGN_GUIDE.md` for the checklist before test runs.

Minimum conventions:
- clear separation of focus vs select
- grid-first parameters where practical
- conservative defaults for AI template generation
- explicit scope integration hooks (optional, but consistent)

## 5.3 Dynamic Component Management (Anyware-only)
Goal: enable dynamic add/remove/replace of components without DOM/tree complexity.

Route (agreed):
- Use a flat, id-based reconcile list (no tree).
- Each component must have a unique `component_id` (string is allowed and preferred).
- If changes are large, switch pages instead of mass mutations.
- Anyware only: `core/GUI.py` stays unchanged.

Implementation contract:
- `ComponentGroup.reconcile_children(ctx, next_children)` handles mount/unmount and replacement.
- Focus fallback: if current focus id is no longer present, jump to any available focusable id.
- Use `visible/enabled` for per-frame animation-like changes; avoid per-frame structural reconcile.
- Id helper: use `stable_component_id(name, seed=...)` or `IdFactory.next(name)` to create stable, unique ids.

## 5.4 Layout DSL (YAML, Declarative)
Goal: allow most static UI to be described in a “page → group → element” YAML file, with minimal code changes.

Compatibility notes:
- Keeps `core/GUI.py` unchanged (loader translates YAML → existing layout structures).
- Aligns with grid-first design and hot reload requirements.
- Dynamic components remain **flat, id-based reconcile**; DSL provides only slots/templates.
- Bindings refresh at app logic FPS (decoupled from backend polling).
- YAML is the default layout path; Python layout is reserved for complex custom rendering.

Reference:
- See §9 “Layout DSL (Draft)” below.

## 5.5 Open Questions (Post-0.1.0)
Dynamic content model / bindings:
- Do we standardize `Bindable[T] = T | Callable[[ctx], T]` for common props (text/color/visible/enabled)?
- Or move toward a DOM-like tree with reconcile (higher effort, different authoring model)?

Live reload scope:
- Keep hot reload limited to layout params (current), or
- Allow full page module reload + UI tree rebuild?

## 6) Milestones and Acceptance (0.1.0)
M1. Baseline freeze (done in 0.0.1):
- architecture boundary confirmed
- component universe and gap map written

M2. GUI prerequisite patch (done in GUI v0.4.0):
- text measurement helpers
- text box + super text primitives

M3. Anyware component implementation (in progress):
- implement MVP components with shared style/default model
- provide one medium-complexity demo that uses the MVP set

Acceptance criteria (must satisfy all):
1. A medium UI page can be assembled with fewer lines than raw GUI script.
2. AI-generated template is logically correct on first pass:
- coordinate types mostly correct
- navigation and state transitions correct
3. Remaining work is mainly human tuning/polish, not logic rewrite.
4. Documentation clearly explains:
- raw GUI path
- Anyware path
- grid/pixel conversion rules
- demo archive usage (see §10)

## 6.1) Pre-Adaptation Plan (v0.0.6 → v0.1.0)
Goal: focus on pre-adaptation for the mixed pipeline (GUI -> image/texture -> OpenGL output) while improving robustness and keeping the pygame path as default.

1. v0.0.6 (baseline hardening): tighten Anyware app discipline (no direct screen output); document render/output separation; confirm all demos run under the pygame presenter path.
2. v0.0.7 (contract draft): introduce a presenter/output contract in docs; add config placeholders for `output_mode`, `logic_fps`, and `present_fps` without behavior change. Status: Done (2026-02-16).
3. v0.0.8 (pre-adaptation hooks): add offscreen render target plumbing and optional “frame export” hooks; keep CI on pygame path; add guardrails against direct `pygame.display` usage in Anyware apps. Status: Done (2026-02-16).
4. v0.0.9 (integration test): **Paused**.
   - Reason: prioritize YAML Layout DSL to improve development efficiency before resuming integration tests.
   - Resume target: after DSL lands, likely in v0.1.0 or v0.2.0.
   - When resumed: focus on AI prompt/brief quality, layout tuning loop, error recovery, and human-AI handoff.
   - Constraints remain: keep pygame presenter path for tests; validate no direct screen output in Anyware apps.
5. v0.1.0 (freeze pre-adaptation): finalize the output separation contract and presenter interface in docs; keep OpenGL path optional and off by default; record acceptance results.

## 7) Change Log
- 2026-02-13: Merged `StatusLight` into `Button` (non-pressable status button + optional lighting), implemented P0/P0.5 instruments, added per-component docs, and wired them into the demo page.
- 2026-02-13: Added `PageRouter` for FSM-style page switching and documented page logic constraints.
- 2026-02-16: Archived DSKY integration artifacts; SegmentDisplay defaults verified manually; CheckboxMenu shipped in demo.
- 2026-02-18: Anyware `Button` label rendering switched to grid-aligned super-text overlay to avoid fill-layer occlusion while keeping text alignment consistent.
- 2026-02-18: Anyware `Button` label color now auto-contrasts against filled status color (Black/White) to preserve readability when lit.
- 2026-02-18: GUI draw order adjusted so filled polys render before grid text, ensuring text remains visible over filled shapes (fixes lit button labels).

## 8) Version Changelog (Anyware)
- 0.0.4 (2026-02-13):
  - introduced text componentization: `Label`, `Text` (supports `orientation` + `color`)
  - added Anyware text drawing aliases: `ctx.label()` / `ctx.text()`; `ctx.static()`/`ctx.hstatic()` kept as compatibility path
  - migrated current Anyware demos to label-first usage
  - added `apps/app_anyware_demo.py` as temporary Anyware demo archive page
- 0.0.3 (2026-02-13):
  - introduced class-based Anyware runtime skeleton: `AnywareApp`, `AnywareContext`, `Page`, `PageStack`, `Component`, `ComponentGroup`
  - added first reusable controls: `Button`, `ButtonArray`
  - enforced GUI stable API dependency check inside `AnywareContext` (`REQUIRED_GUI_STABLE_API`)
  - added migration demos: `apps/app_anyware_template.py`, `apps/app_anyware_demo.py` (combined demo archive)
  - kept raw GUI access as explicit opt-in only (`allow_raw_gui`, `ctx.raw_gui()`)
- 0.0.2 (2026-02-13):
  - switched from shared GUI/Anyware doc versioning to dependency contract mode
  - Anyware now targets GUI compatibility by `GUI_API_LEVEL` and stable API tier
- 0.0.1 (2026-02-12):
  - formalized component universe
  - completed GUI capability gap review with ownership decisions
  - added detailed non-loop animation split (`A-ANM-*`) and dependency mapping to GUI-side requirements (`G-ANM-*`)
  - defined 0.1.0 MVP scope, milestones, and acceptance criteria

## 9) Layout DSL (Draft)
This section merges the former `layout_dsl_plan.md`.

目标：为 UI 的**静态组件**提供类似 HTML 的声明式布局文件（页面 → 组 → 元素），在**尽量少改动现有代码**的前提下，提高开发效率。该方案为**规划文档**，不要求立即实现。

### 背景与动机
- 现状：布局主要写在 Python 中（如 `reactor_ui_layout.py`），修改成本高，协作效率低。
- 期望：用更“去代码化”的文件描述大部分静态 UI，必要时仍可通过少量 Python 代码补充逻辑。

### 目标
1. **页面-组-元素结构**：类似 HTML 的层级结构，但更轻量。
2. **静态为主，动态为辅**：静态布局可完全声明，少量逻辑可引用 Python 回调。
3. **最小改动**：尽量复用现有 Anyware 渲染流程，不重写核心渲染器。
4. **可热更新**：保持目前布局热更新习惯（修改文件后可即时生效）。
5. **项目默认**：YAML DSL 成为布局标准来源，Python layout 仅作为兼容/回退。

### 非目标
- 不做完整 UI 编辑器/可视化编排器。
- 不重新设计 Anyware 的布局与渲染核心。
- 不引入复杂运行时表达式或脚本引擎。
- 不把 Python 布局作为默认路径（仅用于复杂自定义）。

### 设计原则
- **声明式**：布局文件只描述“是什么”，不直接执行渲染逻辑。
- **可读**：结构清晰，适合手写与审阅。
- **可映射**：易于映射到现有 Python 结构与绘制函数。
- **安全可控**：逻辑通过白名单回调绑定，避免执行任意代码。

### 文件格式（确认）
使用 **YAML**，便于阅读与手写。

### 文件组织（确认）
- **一页一文件**：`integration_test/archive/v0.0.9/app/layouts/<page>.yaml`
- 页面注册与切换逻辑仍由 Python 负责（DSL 只描述布局）

### 结构草案（补充样式、相对坐标、绑定）
- `globals`：网格、颜色、常量
- `styles`：默认样式与样式索引（简化版 CSS）
- `pages`：页面集合
- `groups`：自定义组
- `elements`：具体元素（panel/text/button/arrow/...）

示例（YAML）：
```yaml
globals:
  grid: { cols: 128, rows: 48, cell_w: 8, cell_h: 16 }
  palette:
    bg: "#fdf6f0"
    default: "#586e75"
    special: "#78cd26"

styles:
  default:
    text_color: "default"
    line_color: "default"
    fill: null
  nav_button:
    text_color: "default"
    line_color: "default"
    fill: null
  nav_button_active:
    text_color: "bg"
    line_color: "special"
    fill: "special"

pages:
  diagram:
    groups:
      - id: nav
        rect: [0, 0, 128, 6]
        elements:
          - id: btn_state
            type: button
            rect: [0, 0, 20, 6]   # 相对 nav 左上角
            label: "STATUS"
            style: nav_button
            on_click: go_page.state
          - id: btn_diagram
            type: button
            rect: [20, 0, 20, 6]
            label: "DIAGRAM"
            style: nav_button_active
            on_click: go_page.diagram

      - id: body
        elements:
          - id: panel_main
            type: panel
            rect: [0, 6, 128, 38]
            style: default
          - id: core_box
            type: box
            rect: [10, 12, 20, 10]
            label: "Core"
            style: default

      - id: footer
        elements:
          - id: footer_block_1
            type: rect
            rect: [0, 44, 20, 4]
            fill: "default"
            style: default

          - id: latency_text
            type: text
            rect: [92, 2, 24, 3]
            text: "LATENCY: --"
            bind: "net.latency_ms"
            style: default
```

### 元素类型与映射（建议）
为减少改动，元素类型应直接映射到现有绘制函数：
- `panel` → 现有 panel 渲染
- `text` → `super_text` / `draw_text`
- `button` → Anyware Button
- `rect` / `box` → 现有 `draw_rect` / `draw_box`
- `arrow` → 现有 `draw_arrow`
- `poly` → 现有 `draw_poly`

### 逻辑与数据绑定（少量 Python）
避免在布局文件里写代码，用 **回调映射**：
- 布局文件：`on_click: go_page.diagram`
- Python：`actions = {"go_page.diagram": lambda: ...}`

数据绑定（只声明，不执行）：
- `bind: "net.latency_ms"` 仅表示读取路径
- 由 Python 侧的 `bindings` 进行解析与刷新
- 绑定值为空时显示占位（例如 `"--"`）

### 动态组件管理（参考 Anyware 规划）
目标：与 `anyware_plan.md` 中“动态组件管理（简化 DOM 思路）”一致，保持**扁平、id-based**的 reconcile，不引入树形 DOM。

建议对接方式：
- DSL 只提供 **挂载点（slot）** 与 **静态模板（template，可选）**
- Python 侧生成 `next_children`（扁平列表，稳定 id）并调用 `ComponentGroup.reconcile_children(ctx, next_children)`
- 结构性变更尽量低频（避免每帧结构变化），小变化用 `visible/enabled/text/color` 绑定实现

示意：
```yaml
groups:
  - id: alarms
    type: slot
    rect: [0, 20, 64, 20]
```
```python
next_children = [
  {"type": "text", "component_id": "alarm.1", "rect": [0,0,64,2], "text": "..."},
  {"type": "text", "component_id": "alarm.2", "rect": [0,2,64,2], "text": "..."},
]
group.reconcile_children(ctx, next_children)
```

### 坐标系统（确认）
- **相对坐标**：元素 `rect` 永远以父组左上角为原点
- **不支持百分比**：全部使用网格单位
- **锚点**：不在 DSL 中单独支持，可通过嵌套空组实现

### 样式系统（确认）
两种情况：
1. **元素指定 `style` 索引**：直接使用该样式
2. **元素未指定 `style`**：按以下覆盖链计算默认样式  
   `元素局部样式 > 各级组样式 > 全局默认样式 > 系统固定默认`

确认：无论是否指定 `style`，**元素显式字段都可覆盖**最终样式

### Z-Index（确认）
- `z_index` 默认继承父组
- 允许单独指定以覆盖
- **重复 `z_index` 时允许“稳定但伪随机”顺序**
  - 建议：按 `component_id`/`id` 做 hash 排序，保证跨帧稳定

### 最小改动落地方案（建议）
**关键原则**：不改渲染器，只新增一个“布局加载器”。

1. 新增一个加载器：
   - `integration_test/archive/v0.0.9/app/layout_loader.py`
   - 读取 `layouts/*.yaml` 并转换为当前 Python 布局结构
2. 现有渲染代码保持不变：
   - `render_layout(layout_dict)` 继续使用
3. 可配置开关：
   - `USE_DSL_LAYOUT = True` 或命令行参数
4. 若 YAML 缺失或解析失败：
   - 回退到 `reactor_ui_layout.py`

### 热更新策略（建议）
- 监控布局文件改动时间戳
- 每 N 帧检查一次（与现有热更新一致）
- 解析失败时输出错误并保持旧布局

### 迁移路径（建议）
1. 先在 `diagram` 页面试点，双轨运行（DSL + Python）
2. 稳定后逐步迁移其他页面
3. 最终仅保留 DSL + 少量 Python 逻辑

### 数据绑定刷新频率（确认）
- 绑定刷新应与 **App 逻辑帧** 一致
- 与后端轮询频率解耦
  - 例如：后端 2s 轮询，UI 仍可 60fps 渲染并显示最后一次数据

## 10) Demo Archive
Last Updated: 2026-02-22

Purpose:
- Keep a temporary, runnable showcase of current Anyware capabilities.
- Serve as a migration reference from raw `GUI.py` scripts to Anyware classes.
- Provide one place to validate component interactions after each small release.

Current demo entries:
1. `apps/app_anyware_template.py`
- Minimal lifecycle + focus wiring + label-first rendering.
- Includes hot reload layout params from `apps/layouts/anyware_template_layout.yaml`.

2. `apps/app_anyware_demo.py`
- Combined demo archive page.
- Includes multi-page push/pop via PageStack.
- Includes dynamic component reconciliation page (press `D`).
- Includes `CheckboxMenu` multi-state toggle.
- Note: This demo is intentionally Python-driven for complex custom behavior.

Archive policy:
1. Keep demos runnable under current `GUI_API_LEVEL`.
2. Prefer Anyware components over direct `GUI.py` calls.
3. If temporary workarounds need raw GUI access, mark them explicitly and remove later.
