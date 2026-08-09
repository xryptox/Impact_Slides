# impact_slides

## Purpose

Python package for the Impact_Slides hybrid pipeline: Step 1 preprocessor (v4) and shared support modules. Step 4 legacy renderer lives in `renderer_v2/`; schema-v1 kernel lives in sibling `renderer_v3/`.

## Ownership

- Preprocessor pipeline code and package CLI/config/logging
- Evidence schemas and text/analysis helpers used before handoff
- Does **not** own GPT prompt bodies (those live under `wiki/` as live Step 2/3 artifacts) or agent operating docs (`docs/agents/`)

## Local Contracts

- Public preprocessor entry: `step1_preprocessor_v4.py` → `impact_slides.preprocessor`
- Canonical evidence schema: `schemas.py`
- Logging: `logging_setup.py` — must write `run.log` under **both** stdlib and structlog backends (`_mirror_to_run_log`)
- Soft-optional deps stay soft; do not hard-require `structlog` at import time
- No machine-local paths (`Path.home()`, absolute user dirs) in package code

## Work Guidance

- Prefer extending existing modules over new top-level files
- Keep preprocessor concerns out of renderer packages
- Keep `renderer_v2/` frozen as the legacy renderer while `renderer_v3/` is built independently; share only genuinely immutable, version-neutral assets through a neutral module
- Domain language: root `CONTEXT.md`

## Verification

- `python -m pytest -q` (full suite)
- CI: `.github/workflows/ci.yml` via `requirements-ci.txt`

## Child DOX Index

- `renderer_v2/AGENTS.md` — legacy Step 4 HTML renderer (current layouts, charts, recipes, handoff → deck)
- `renderer_v3/AGENTS.md` — schema-v1 canonical kernel (typed validation, repairs, generated JSON Schema, deterministic five-artifact `render_deck` publication); full painting arrives in later tickets
