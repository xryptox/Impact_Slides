# impact_slides

## Purpose

Python package for the Impact_Slides hybrid pipeline: Step 1 preprocessor (v4) and shared support modules. Step 4 lives in the child `renderer_v2/`.

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
- Keep preprocessor concerns out of `renderer_v2/` and vice versa
- Domain language: root `CONTEXT.md`

## Verification

- `python -m pytest -q` (full suite)
- CI: `.github/workflows/ci.yml` via `requirements-ci.txt`

## Child DOX Index

- `renderer_v2/AGENTS.md` — Step 4 HTML renderer (layouts, charts, recipes, handoff → deck)
