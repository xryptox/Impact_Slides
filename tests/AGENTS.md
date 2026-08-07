# tests

## Purpose

Regression suite and fixtures for preprocessor + renderer_v2.

## Ownership

- `tests/test_*.py`, `conftest.py`, `fixtures/`
- Notes: `README.md`, `LEGACY_MIGRATION.md` (legacy v2/v3 baselines removed; v4 suite is the net)

## Local Contracts

- Runner: `pytest` via root `pytest.ini` (`testpaths=tests`)
- CI install set: root `requirements-ci.txt` (includes `structlog`; excludes playwright/sentence-transformers)
- Some real-world fixtures are machine-local — CI shows extra skips; local pass count can be higher
- Renderer layout index tests must not embed bare layout-name literals or search probes that match the test file itself (`test_gen_layout_index.py` pattern)
- Prefer tests that fail under mutation of the production guard they claim to pin

## Work Guidance

- Fixtures for renderer: `tests/fixtures/renderer_v2/`
- Amex #148 handoff contract: `test_amex_s13_s14_handoff_contract.py` + fixtures `amex_s13_s14_v10_broken.json` / `amex_s13_s14_corrected.json` (mutation via `scripts/amex_handoff_mutations.py`; no renderer production change)
- When adding layout references, regenerate `wiki/renderer_v2_LAYOUTS.md` if the index test-column drifts
- Do not reintroduce legacy preprocessor baseline harnesses; see `LEGACY_MIGRATION.md`

## Verification

- `python -m pytest -q`
- Targeted: `pytest -q -k renderer_v2` (or narrower)

## Child DOX Index

- No child AGENTS.md — fixtures stay under this boundary.
