# KRPC GUI + Anyware

Grid-based text UI engine with a lightweight component layer (Anyware) for assembling cockpit-style interfaces. Designed for fast, deterministic layouts, strict grid/pixel discipline, and AI-assisted first-pass UI generation with human tuning.

## Key Features
- Grid-first text rendering with overlay drawing primitives.
- Pixel-level shape rendering, focus navigation, and scoped focus routing.
- Anyware component layer (`Button`, `ButtonArray`, `Label`, `SegmentDisplay`, gauges).
- Stable GUI contract with dependency checks and API tiers.
- AI-assisted workflow support with live reload layout tuning.

## Current Versions
- **GUI Engine**: `0.4.0` (`core/GUI.py`)
- **Anyware**: `0.0.5` (`docs/anyware/anyware_plan.md`)

## Tech Stack
- **Language**: Python 3.12+ (tested with 3.13)
- **Rendering**: pygame + pygame.freetype
- **Numerics**: numpy

## Repository Layout
- `core/GUI.py` — engine layer (rendering, focus, draw queues, coordinate conversion, API contract)
- `core/anyware/` — component layer (Anyware widgets + app runtime)
- `apps/` — runnable demos and templates
- `assets/fonts/` — bundled fonts (ASCII + CJK)
- `docs/` — architecture notes, tutorial, AI design guide
- `integration_test/` — integration/unit test scripts

## Prerequisites
- Python 3.12+ (3.13 works)
- SDL (usually bundled with pygame)
- `pip` or `uv`

## Install Dependencies
```bash
pip install pygame numpy
```

## Quick Start
Run a GUI demo:
```bash
python3 apps/app_main.py
```

Run an Anyware demo:
```bash
python3 apps/app_anyware_demo.py
```

## Live Reload Layout Demo (AI-assisted tuning)
This demo loads layout parameters from a separate file and hot-reloads on save.

Run:
```bash
python3 apps/app_anyware_text_layout_demo.py
```

Edit layout parameters while it runs:
```bash
apps/text_layout_demo_layout.py
```

## Integration Tests
Headless tests use `SDL_VIDEODRIVER=dummy` inside the scripts.

GUI text primitives:
```bash
python3 integration_test/v0.4.0/test_gui_text.py
```

Anyware text + button/label integration:
```bash
python3 integration_test/v0.4.0/test_anyware_text.py
```

## Fonts
Default ASCII font is now **DEM-MOMono-300.otf**. CJK font is **wqy-zenhei.ttc**. Both live under:
- `assets/fonts/DEM-MO typeface/Mono/`
- `assets/fonts/wqy-zenhei/`

## Architecture Notes
This project keeps two valid usage paths:
- **Raw GUI path**: call `core/GUI.py` directly for low-level control.
- **Anyware path**: use `core/anyware/*` for higher-level components.

Layer responsibility (summary):
- `core/GUI.py`: rendering primitives, coordinate conversion, focus/navigation, queues, global defaults.
- `core/anyware`: reusable widgets + app composition semantics.
- `apps/`: demos, templates, and integration experiments.

## Coordinate Discipline
- Text APIs use **grid coordinates**.
- Shape and focus rect APIs use **pixel coordinates** (convert via `gx()/gy()` or `grid_to_px()`).
- If you need to place text based on pixel positions, convert back with `px()/py()`.

## AI-Assisted Design Workflow
See `docs/AI_ASSISTED_DESIGN_GUIDE.md` for the full guide.

Key constraints:
- AI outputs **grid-first** layouts with strict coordinate discipline.
- **Critical layout parameters must be hard-coded** in a layout file.
- **Live reload is required** to enable real-time tuning without restarts.

## Development Tips
- Use `apps/_bootstrap.py` to keep repo root on `sys.path`.
- Avoid auto-layout and implicit sizing for deterministic tests.
- Keep focus and select states separate (focus is GUI-level, select is app-level).

## Documentation Map
- `docs/GUI_TUTORIAL.md` — usage tutorial and grid/pixel rules
- `docs/GUI_FRAMEWORK.md` — architecture/roadmap notes
- `docs/anyware/anyware_plan.md` — Anyware roadmap + version
- `docs/AI_ASSISTED_DESIGN_GUIDE.md` — AI workflow + live reload rule

## Deployment
This project is currently designed for local runtime and iterative UI development. No production deployment pipeline is defined yet.
