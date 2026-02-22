# Anyware Integration Test v0.0.9

Purpose:
- Validate AI-assisted UI second-pass development with a multi-stage, human-AI collaboration workflow.
- Cover most Anyware features (page management, dynamic component management) while keeping low visual requirements.
- Confirm pre-adaptation constraints (output separation, stable ids, no direct screen output).

Definition (Panel):
- A "panel" is a design-only grouping of components or a page region.
- It has no runtime logic or special component type. It can be represented by a simple box for layout preference.

## Test Process (Multi-Stage Interaction)

Stage 1: Page skeleton + empty panels
- User provides page-level structure and panel intents.
- AI builds page logic and empty panels (boxes) to mark intended regions.
- Panels are only visual placeholders and can be moved later by the user.
- Acceptance:
  - PageStack navigation works.
  - No direct screen output calls in Anyware apps.
  - Output is still via pygame presenter path.

Stage 2: Coarse layout + full component generation
- User adjusts panel positions roughly.
- AI generates all components and implements dynamic component management logic.
- Acceptance:
  - Components use stable `component_id` values.
  - `reconcile_children` is used for structural changes.
  - Focus fallback works when components are removed.

Stage 3: Fine tuning + AI initial beautification
- User performs manual layout tuning to near-final geometry.
- AI applies low-risk visual polish (colors, alignment, mild pattern fills).
- Acceptance:
  - No layout logic changes by AI during beautification.
  - Visual output remains readable; aesthetics are secondary.

Stage 4: Final manual beautification and packaging
- User performs final layout and style adjustments.
- Deliverable is a polished, stable UI.
- Acceptance:
  - No logic changes; only visual refinement.

## Key Mechanism Index

Page management:
- PageStack push/pop/replace lifecycle: `core/anyware/page.py`
- AnywareApp routing helpers: `core/anyware/runtime.py`

Dynamic component management:
- `ComponentGroup.reconcile_children(...)`: `core/anyware/component.py`
- Stable id helpers: `core/anyware/id.py`

Output separation (pre-adaptation):
- Anyware runtime placeholders: `core/anyware/runtime.py`
- Output rules and constraints: `docs/DEV_GUIDE.md`

AI-assisted workflow constraints:
- Avoid complex animation in integration tests
- Keep logic correct; let humans do fine tuning
- Reference: `docs/AI_ASSISTED_DESIGN_GUIDE.md`

## Key Code Index

Runtime and context:
- AnywareApp runtime: `core/anyware/runtime.py`
- AnywareContext API surface: `core/anyware/context.py`

Components:
- Base components and reconcile: `core/anyware/component.py`
- Page/PageStack: `core/anyware/page.py`
- Widget set (Button/CheckboxMenu/etc.): `core/anyware/widgets.py`
- Instruments (ValueText/MeterBar/DialGauge/SegmentDisplay): `core/anyware/instruments.py`

Demos (reference only):
- Anyware demo archive: `apps/app_anyware_demo.py`
- Anyware template: `apps/app_anyware_template.py`

## Constraints Checklist

- Anyware apps must not call `pygame.display.*` or `GUI.draw_to_surface(...)`.
- Use stable `component_id` values for all dynamically managed components.
- Do not rebuild component trees every frame; prefer `visible/enabled` for per-frame changes.
- Keep pygame presenter path for v0.0.9 tests.

