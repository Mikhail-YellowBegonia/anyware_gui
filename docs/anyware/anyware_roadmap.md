# Anyware Roadmap

Doc role: global, longer-term plan and architecture questions for Anyware.
This document stays general. Versioned commitments live in `docs/anyware/anyware_plan.md`.

## Table of Contents
1. Purpose and Scope
2. Long-Range Goals (Post-0.2.0)
3. Strategic Tracks
4. Open Architecture Questions
5. Evidence and Prototypes to Collect
6. Update Policy

## 1) Purpose and Scope
This roadmap captures longer-term direction beyond the active Anyware plan.
It is intended for the core UI framework developers and should guide work
without creating conflicts with the near-term MVP plan.

## 2) Long-Range Goals (Post-0.2.0)
- Stabilize Anyware as the default UI authoring path with minimal GUI churn.
- Finalize mixed output pipeline support (pygame + OpenGL) with clear ownership
  of presentation vs offscreen rendering.
- Lock a stable Layout DSL with predictable binding, hot reload, and migration
  policies.
- Grow a consistent component library with shared defaults and strict focus
  behavior.
- Enable dependable text input and scrolling primitives to unlock richer UI
  (including future LLM/assistant experiences).

## 3) Strategic Tracks
Output and Presentation:
- Offscreen rendering + presenter separation.
- Output mode switching and surface lifecycle rules.

Layout DSL and Authoring Model:
- DSL schema stabilization and migration policy.
- Clear boundary between DSL vs Python for custom rendering.

Component Maturity:
- Shared defaults, theming, and alignment policies.
- Consolidated focus and selection behavior across components.

AI and LLM Experiences:
- Streaming text viewport primitives.
- Safe, testable integration paths that do not destabilize core rendering.

Testing and Quality:
- Integration tests for mixed output and DSL-driven layouts.
- Regression coverage for focus/navigation and layout determinism.

## 4) Open Architecture Questions
- How should mixed pipelines arbitrate ownership of the final surface?
- Should the presenter be a separate process or stay in-app for early phases?
- Where is the hard boundary between DSL and Python custom rendering?
- What guarantees should the DSL provide for deterministic layout and focus?
- How should text metrics be unified across pygame and OpenGL paths?
- What is the minimal input/focus model required for robust text input and
  scrollable panels?
- How do we expose extensibility for third-party components without bloating
  the core Anyware API?

## 5) Evidence and Prototypes to Collect
- Offscreen rendering proof-of-concepts for OpenGL presenter path.
- DSL hot-reload stability and rollback behavior under parse errors.
- Text viewport prototype performance with large histories.
- Integration test outcomes that validate separation of output vs logic.

## 6) Update Policy
- Update only when new long-range decisions are made.
- Keep this doc general; move versioned plans into `anyware_plan.md`.
- Record architectural questions even if answers are pending.
