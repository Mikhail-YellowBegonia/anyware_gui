# Anyware Demo Archive

Last Updated: 2026-02-15

Purpose:
- Keep a temporary, runnable showcase of current Anyware capabilities.
- Serve as a migration reference from raw `GUI.py` scripts to Anyware classes.
- Provide one place to validate component interactions after each small release.

Current demo entries:
1. `apps/app_anyware_template.py`
- Minimal lifecycle + focus wiring + label-first rendering.
- Includes hot reload layout params from `apps/anyware_template_layout.py`.

2. `apps/app_anyware_demo.py`
- Combined demo archive page.
- Includes multi-page push/pop via PageStack.
- Includes dynamic component reconciliation page (press `D`).

Archived scratch apps:
- `apps/archive/app_anyware_dynamic_temp.py` (single-page dynamic reconcile check)

Archive policy:
1. Keep demos runnable under current `GUI_API_LEVEL`.
2. Prefer Anyware components over direct `GUI.py` calls.
3. If temporary workarounds need raw GUI access, mark them explicitly and remove later.
