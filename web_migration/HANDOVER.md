# Web 迁移交接文档

更新日期：2026-03-02

## 1. 当前仓库状态（已确认）

### 旧仓库（历史 Pygame 项目）
- 本地路径：`/Users/Administrator/Desktop/kos/krpc`
- 当前分支：`web-migration`
- 远程：`git@github.com:Mikhail-YellowBegonia/anyware_gui.git`
- 作用：保留历史实现、迁移素材、设计决策记录

### 新仓库（Web 迁移项目）
- 本地路径：`/Users/Administrator/Desktop/kos/koyuu-web-migration`
- 当前分支：`main`
- 远程：`git@github.com:Mikhail-YellowBegonia/Koyuu_UI.git`
- 作用：承接 Web 端新项目的独立开发与版本管理

## 2. 现阶段共识（迁移原则）
- 不做“Pygame 逐行搬运”，而是基于 Web 原生能力重建。
- 默认废弃自定义 DSL / 双坐标体系 / 本地渲染耦合实现。
- 保留业务语义与可迁移算法思路（状态、通信、仿真逻辑）。
- 技术路线优先：React + TypeScript + Web 标准能力（DOM/CSS/SVG/Canvas）。

## 3. 为什么要转到上层目录协作
- 迁移期需要并行操作两个仓库（旧仓库查资料，新仓库落地实现）。
- 若仅在单仓库目录下工作，跨仓库协作成本高，且上下文容易断裂。
- 建议在父目录 `/Users/Administrator/Desktop/kos` 启动主会话进行编排。

## 4. 会话与目录绑定的工作约定（关键）
- 主会话目录：`/Users/Administrator/Desktop/kos`（负责规划、任务拆解、跨仓库决策）。
- 实施会话目录：
  - `.../krpc`：只做旧代码梳理、迁移提取、历史对照。
  - `.../koyuu-web-migration`：只做新项目实现、测试、提交。
- 每次切换仓库后，先执行并记录：
  - `pwd`
  - `git status -sb`
  - `git branch -vv`
  - `git remote -v`
- 任何阶段性结论都回写到本文件，避免会话切换造成信息丢失。

## 5. 已完成事项
- 新仓库已创建并连接远程。
- Sourcetree 已可识别新仓库。
- Web 迁移方向已形成初版文档：
  - `web_migration/WEB_PROJECT_REQUIREMENTS.md`
  - `docs/web_migration_aggressive_review.md`

## 6. 下一步（进入上层目录后的首批任务）
- 任务 A：在新仓库建立最小工程骨架（前端 + 示例后端通信）。
- 任务 B：冻结 MVP 清单（Must 项逐条验收标准化）。
- 任务 C：定义首版目录结构、代码规范、提交规范。
- 任务 D：整理“旧仓库可迁移资产清单”（逻辑可复用 vs 必须重写）。

## 7. 风险与防错
- 风险：两个仓库混改导致提交混乱。
  - 规避：每次提交前执行 `git rev-parse --show-toplevel`，确认目标仓库。
- 风险：需求在会话切换中丢失。
  - 规避：统一以本文件作为“单一交接真相源（SSOT）”。
- 风险：过早追求视觉效果导致延期。
  - 规避：先通信与组件闭环，再做风格强化。
