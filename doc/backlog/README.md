# Backlog

This folder contains the phase-based delivery plan for the Interview Practice App.

Phase mapping:
- Phase 1: MVP base interview loop
- Phase 2: Personalisation and adaptation
- Phase 3: Advanced evaluation and reporting
- Phase 4: Growth and extensions

## Priority Key

- High: must be done first for the current phase
- Medium: important, but can follow the high-priority items
- Low: useful polish or post-phase work

## Workstream Prefixes

- `frontend:` marks user interface, Streamlit, and screen-flow tasks.
- `backend:` marks API, data-processing, validation, and model-integration tasks.
- Use the prefix on every backlog item so ownership is clear at a glance.

## Frontend Design Rule

- Before writing frontend code, check the matching mock-up in `doc/product_requirement/mock_ups` and match its layout, hierarchy, labels, and visible actions as closely as possible.

## Reusable Component Rule

- Build frontend screens with reusable Streamlit layout and style helpers first, then provide screen-specific content and actions.
- Keep shared styling in one place so welcome, setup, feedback, and summary screens can reuse the same shell and spacing rules.

## Phase Files

- `phase-1-mvp.md`
- `phase-2-personalisation.md`
- `phase-3-advanced-evaluation.md`
- `phase-4-growth-and-extensions.md`

## Living Documentation

These files must stay up to date after every code change:

- `doc/manual.md` for users
- `doc/developer-manual.md` for developers
- `doc/test-manual.md` for manual UI testing

## Documentation Rule

- Update `doc/manual.md` only with what is currently available to users.
- Update `doc/developer-manual.md` with the actual implemented behaviour, code structure, and technical details.
- Update `doc/test-manual.md` with the exact manual test steps that match the current implementation.
- Treat both files as required follow-up work whenever functionality changes.
