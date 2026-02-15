# GUI Framework Plan

Version: 0.4.0
Last Updated: 2026-02-15
Doc role: planning and roadmap detail for the GUI engine. Developer reference is in `DEV_GUIDE.md`.

## 0) Documentation Split
- Planning: `GUI_FRAMEWORK.md`, `docs/anyware/anyware_plan.md`
- Secondary dev reference: `DEV_GUIDE.md`
- Overview tutorial: `GUI_TUTORIAL.md`
- AI coding: `AI_ASSISTED_DESIGN_GUIDE.md`

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
- docs split (`GUI_FRAMEWORK.md`, `GUI_TUTORIAL.md`, `anyware_plan.md`)
- AI-coding guidance added to tutorial (now consolidated in `AI_ASSISTED_DESIGN_GUIDE.md`)

Track C: Anyware Reassessment and Early Implementation
- Freeze Anyware v0.1 scope (grid-first, minimal component set)
- Build minimal Anyware alpha on top of GUI
- Go/No-Go checkpoint (Anyware faster than raw GUI for non-trivial page)

Track D: Dependency Decoupling
- Freeze GUI stable API list for Anyware
- Require Anyware startup compatibility check via `require_api_level(...)`
- Keep GUI/Anyware changelogs independent
- Add migration notes when stable API behavior changes
