# v0.4.0 Test Suite

Status: closed (2026-02-15)

## Scripts
- `test_gui_text.py` — GUI text primitives and alignment.
- `test_gui_focus.py` — focus scoring + fallback behavior.
- `test_anyware_text.py` — Anyware text + alignment integration.
- `test_anyware_page_stack.py` — PageStack lifecycle hooks.
- `test_layout_dsl.py` — YAML DSL compile/render sanity.

## Notes
- Run with `python3` from repo root.
- GUI tests set `SDL_VIDEODRIVER=dummy` internally.
