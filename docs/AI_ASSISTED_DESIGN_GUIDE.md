# AI辅助设计指南

## 目的
- 让 AI 输出“逻辑正确、坐标正确”的 UI 首稿，然后由人类完成精细调参与抛光。
- 明确 AI 在本项目中的角色与工作边界，减少返工与测试噪音。

## 核心定位（从 GUI_TUTORIAL 与 Anyware 规划汇总）
Positioning:
- In this project, AI is mainly responsible for **logical implementation**, not perfect visual design.
- The player/developer performs detailed tuning, polish, and small bug fixing.

Why grid-first for AI:
- AI is weaker at exact spatial judgment in pixel-level layout.
- Most functions can still be driven by grid references, then converted at render boundaries.
- This provides "logically correct and principled" layout output, even before fine tuning.

Minimum acceptance for AI output:
- coordinate types are correct
- navigation logic is correct
- state transitions are correct
- visual perfection can be deferred to manual tuning

Minimum conventions (Anyware integration prep):
- clear separation of focus vs select
- grid-first parameters where practical
- conservative defaults for AI template generation
- explicit scope integration hooks (optional, but consistent)

## 新增固定要求（AI辅助设计的强制约束）
- **关键排版参数必须硬编码成显式数据结构**（默认使用 `layout.yaml`）。
- **布局标准为 YAML DSL**；仅在 DSL 无法表达时使用 Python 自定义渲染。
- **必须启用 reload 机制**，允许实时更新布局参数并即时反馈。
  - 目标体验：接近 `html + live server` 的实时调参。
  - 允许热更新失败时回退到上一次有效配置，并在屏幕提示错误。
- 标准模板 `apps/app_anyware_template.py` 已默认集成热重载（配套 `apps/layouts/anyware_template_layout.yaml`）。
- 调参期可启用“布局模式”（两色强制），减少颜色噪音：
  - API：`GUI.set_layout_mode(True/False)`
  - 模板：在 `apps/layouts/anyware_template_layout.yaml` 设置 `globals.layout_mode` 并热重载切换。

> 该要求用于削弱“AI 输出逻辑正确但排版瑕疵”的长期成本，让调参回路变成实时反馈。

## 坐标与渲染规则（AI 输出必须明确）
Prompt guidance for AI-generated templates:
- Explicitly request coordinate type per call:
  - "Text calls must use grid coordinates."
  - "Shape and node rect calls must use pixel coordinates converted from grid via gx/gy."
- Explicitly request state split:
  - "Focus rendering and select state update must be separate."
- Explicitly request conservative defaults:
  - "Prefer default parameters unless necessary."

坐标纪律（摘要）：
- 文本（Label/Text/ctx.label）必须使用 **网格坐标**。
- 形状/框体/节点矩形必须使用 **像素坐标**（由 `gx()/gy()` 转换）。
- 如果绘制 API 返回像素坐标，且需要对齐文本，必须通过 `px()/py()` 转回网格再绘制文本。

## AI 编码清单
Checklist (Instruments)
- Normalize numeric values to `[0, 1]` before rendering.
- Keep text APIs in grid units; shape APIs in pixel units.
- Use conservative defaults; avoid implicit magic values.
- Prefer clear, fixed geometry over dynamic auto-layout.
- Keep component rendering free of side effects.

Checklist (Buttons + Status)
- Use `pressable=False` for non-interactive indicators.
- Use `focusable=False` if the indicator should not capture focus.
- Prefer `status_color_map` for stable state visuals.
- Button text alignment and manual line breaks:
  - `label_align_h`, `label_align_v`, `label_line_step`, `label_orientation`.
  - Use `\\n` for explicit line breaks (no auto-wrap).

Checklist (SegmentDisplay sizing)
- Use a consistent baseline for all displays in the page.
- Default is `digit_w_px=14`, `digit_h_px=24`, `spacing_px=3`.
- Scale width/height/spacing together to preserve proportions.
- Provide `off_color` to keep inactive segments readable but subdued.

Demo Page Notes
- Add one minimal example per component.
- Avoid complex animation during integration tests.
  - Note: v0.0.9 integration tests are currently paused until the YAML Layout DSL is complete.

## 推荐工作流（AI -> 人类调参）
Recommended workflow:
1. Ask AI to output layout in grid coordinates first.
2. Keep text APIs in grid.
3. Convert only draw anchors/rects to pixel with `gx()/gy()`.
4. If a draw result returns pixel positions and you need labels, convert back with `px()/py()`.
5. Manually tune spacing/size/thickness after logic is confirmed.

## Live Reload 结构建议（参考用）
建议将布局参数抽成显式文件，并由运行时监视更新：

- 布局参数文件：`apps/<name>_layout.yaml`
- 运行时逻辑：
  - 记录 `mtime`，每帧或每 N 帧检查更新
  - 发生变更后重新解析 YAML
  - 出错则保留上次版本并在 UI 提示

示例结构（示意）：
```yaml
pages:
  demo:
    elements:
      - type: text
        rect: [2, 2, 22, 3]
        text: "CENTER\nBOX"
        align_h: center
        align_v: center
      - type: super_text
        gx: 2
        gy: 13
        text: "SUPER x2"
        scale: 2
```

## 接受标准（来自 Anyware 规划）
- AI 输出的模板在首轮 **逻辑正确**（坐标类型、导航、状态）。
- 剩余工作主要是 **人工调参与排版**，不是逻辑重写。
- 文档明确区分：
  - raw GUI 路径
  - Anyware 路径
  - grid/pixel 转换规则
  - demo archive 使用方式
