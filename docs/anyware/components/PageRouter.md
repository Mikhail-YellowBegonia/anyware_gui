# PageRouter

Purpose
- Simple FSM-style page switching across a finite set of pages.

Core Features
- Register pages by `page_id`.
- Switch via `switch(page_id, ctx)` with `on_exit`/`on_enter`.
- No stack, no history, no transition effects.

Key Methods
- `add(page)`, `add_many(pages)`
- `set_current(page, ctx)`
- `switch(page_id, ctx)`

Behavior Notes
- Current page is unmounted on switch; target page is mounted before `on_enter`.
