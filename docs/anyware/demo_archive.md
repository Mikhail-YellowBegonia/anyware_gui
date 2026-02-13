# Anyware Demo Archive

Last Updated: 2026-02-13

Purpose:
- Keep a temporary, runnable showcase of current Anyware capabilities.
- Serve as a migration reference from raw `GUI.py` scripts to Anyware classes.
- Provide one place to validate component interactions after each small release.

Current demo entries:
1. `apps/app_anyware_template.py`
- Minimal lifecycle + focus wiring + label-first rendering.

2. `apps/app_anyware_gauges.py`
- Dynamic values + `ButtonArray` + label-first text usage under Anyware runtime.

3. `apps/app_anyware_demo.py`
- Temporary integrated archive page for stable components (`Label/Text`, `ButtonArray`, focus frame).

Archive policy:
1. Keep demos runnable under current `GUI_API_LEVEL`.
2. Prefer Anyware components over direct `GUI.py` calls.
3. If temporary workarounds need raw GUI access, mark them explicitly and remove later.
