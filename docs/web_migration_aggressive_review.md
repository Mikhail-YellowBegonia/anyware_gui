# Web 迁移激进评审（面向“更轻、更可靠、AI 友好”）

## 1. 目标重述
- 目标不是“把 Pygame 框架搬到 Web”，而是“在 Web 上实现同等或更好的 GUI 能力，并显著降低复杂度”。
- 判定标准优先级：
  1. 运行时复杂度更低
  2. 可维护性更高
  3. AI 可理解性更强（生成/修改代码成功率更高）
  4. 功能不退化（或可接受替代）

## 2. 结论（先给结论）
- **结论 A：默认废弃自定义 Layout DSL**，直接采用 HTML/JSX + CSS Grid/Flex + 组件库。
- **结论 B：废弃双坐标体系（grid/pixel）**，统一为浏览器原生布局模型；图形场景仅在 SVG/Canvas 局部坐标内处理。
- **结论 C：废弃自定义组件库实现**，保留“组件语义”，迁移到成熟 Web 组件体系（Radix/Headless + 自定义样式）。
- **结论 D：保留并迁移“非渲染核心能力”**（状态机、动态 reconcile 思路、Reactor 仿真后端、LLM 中间件）。

## 3. DSL 是否应保留？

## 3.1 激进判断
- 在 Web 端，DSL 的主要价值（声明式布局、层级组织、样式复用、热更新）已经被：
  - HTML/JSX
  - CSS（变量、容器查询、grid/flex）
  - 组件 Props/Slots
  - HMR（Vite/Next）
  完整覆盖。
- 因此继续保留 DSL 会新增一层翻译和心智负担，且 AI 对自定义 DSL 理解弱，回报很低。

## 3.2 唯一建议保留的“窄场景”
只有在以下条件同时满足时，才保留一个**极小配置层**（不是完整 DSL）：
- 需要让非前端开发者通过配置改页面结构；
- 需要运行时从后端下发布局；
- 需要严格受控的 schema（例如控制台模板）。

建议形式：
- 保留为 JSON Schema 驱动的 page config（仅描述数据绑定和模块开关），不描述底层绘制细节。
- UI 仍由 React/Vue 组件渲染，而非“DSL 编译器”渲染。

## 4. 坐标系统：是否保留 grid/pixel？
- **不保留**。
- Web 原生布局已经解决绝大多数问题：
  - 文本对齐：CSS
  - 响应式：媒体查询/容器查询
  - 组件定位：Grid/Flex
- 仅在图形模块（仪表盘、波形、箭头）中保留局部坐标（SVG viewBox 或 Canvas），且与页面布局解耦。

## 5. 组件库：保留“语义”，废弃“实现”
- 当前 Button/Meter/Gauge/SegmentDisplay 等语义可保留。
- 但实现应迁移为 Web 组件：
  - 交互组件：Radix/Headless UI + 设计系统封装
  - 可视化组件：SVG 组件或现成图表库（Recharts/ECharts/Visx）
- Focus/keyboard/nav 优先使用浏览器可访问性语义（ARIA + roving tabindex），不再自建全局 focus 引擎。

## 6. AI 友好性：Web 是否更好？
- **是，显著更好。**
- 原因：
  - HTML/CSS/React 是 LLM 高频训练语料，生成稳定性更高；
  - 生态工具成熟（eslint、storybook、playwright、a11y 工具）；
  - AI 对自定义 DSL、自定义坐标和私有渲染 API 的理解成本高、错误率高。

具体收益：
- Prompt 更短，约束更少；
- 代码审阅更标准化；
- 新成员上手更快。

## 7. 仓库功能去留建议（激进版）

## 7.1 直接废弃
- `core/GUI.py`（Pygame 渲染内核）
- `core/anyware/runtime.py`、`core/anyware/context.py`（强绑定 pygame 生命周期）
- `core/anyware/nonstandard_gl/*`（本地 OpenGL 特效链）
- 依赖本地渲染的 demo app 与对应测试

## 7.2 迁移思想，不迁移代码
- `core/anyware/layout_dsl.py`：保留“声明式配置”思路，不保留 DSL 编译器实现
- `core/anyware/instruments.py`：保留归一化/采样算法，重写为 TS + SVG/Canvas
- `core/anyware/llm_ui.py`：保留流式缓冲与简化 markdown 思路，重写 Web 组件

## 7.3 可直接复用（或低成本迁移）
- `integration_test/v0.0.9/reactor_sim.py`（仿真逻辑）
- `integration_test/v0.0.9/reactor_backend.py`（HTTP API）
- `core/anyware/nonstandard_llm/middleware/*`（工具调用解析/分发思路）
- `core/anyware/page.py`、`component.py`、`id.py`（状态管理思想；建议迁移到 TS）

## 8. 推荐的新 Web 架构（轻量优先）
- 前端：React + Vite + TypeScript
- UI：Tailwind + Headless/Radix（或 shadcn 体系）
- 状态：Zustand（轻）或 Redux Toolkit（重场景）
- 图形：SVG 优先，Canvas 仅用于高频图
- 后端：先复用现有 Reactor backend（可后续迁移 FastAPI/Node）
- 测试：Vitest + Playwright + axe

## 9. 迁移策略（建议）
1. 第一阶段：保留后端，重做前端页面（不引入 DSL）。
2. 第二阶段：把仪表、趋势、告警组件做成可复用 Web 组件。
3. 第三阶段：将 LLM 中间件迁移为服务层/前端 hook。
4. 第四阶段：若仍有“配置化布局”需求，再引入极简 JSON schema（不是 DSL）。

## 10. 最终建议（决策）
- 以“减法”为主：**停用 DSL、停用坐标体系、停用自研渲染引擎**。
- 以“语义迁移”为主：保留组件语义和业务模型，不保留渲染实现。
- 以“AI 成功率”为主：全面转向 Web 标准栈与通用组件范式。

这条路径最符合“更轻、可靠、AI 友好”的核心诉求。
