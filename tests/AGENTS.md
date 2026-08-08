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
- Amex #148 handoff contract: `test_amex_s13_s14_handoff_contract.py` + fixtures `amex_s13_s14_v10_broken.json` / `amex_s13_s14_corrected.json` (mutation via `scripts/amex_handoff_mutations.py`)
- Amex #153 handoff contract: `test_amex_slide26_matrix_orientation.py` + fixture `amex_slide26_te_billed_business.json` (Q1'26 period header + category-column matrix; identity-safe cell asserts + adversarial mutations; no renderer production change)
- Amex #156 slide-27 handoff contract: `test_amex_s27_scenarios.py` + fixtures `amex_s27_v10_broken.json` / `amex_s27_corrected.json` (`apply_issue_156_slide27_scenarios`; 13 quarterly categories, all three scenarios, E0270 PDF citation, source headings/SAAR note + #146 paint-ready dual-canvas geometry; no renderer production change)
- Amex #157 annex handoff contract: `test_amex_annex_33_37_handoff.py` + fixtures `amex_annex_33_37_v10_broken_handoff.json` / `amex_annex_33_37_restored_handoff.json` (`apply_issue_157_annex_matrices`; PDF-source semantic-cell probes + 1920×1080 browser geometry; no renderer production change)
- Amex #158 handoff + multi_panel pane titles: `test_amex_s28_handoff_contract.py` + `test_multi_panel_pane_headings.py` + fixtures `amex_s28_v10_broken.json` / `amex_s28_corrected.json` (mutation drops slide-28 `top_total` pseudo-titles; renderer multi_panel tiles share #147 heading/subtitle chrome; SVG honors `stack_total_labels`)
- When adding layout references, regenerate `wiki/renderer_v2_LAYOUTS.md` if the index test-column drifts
- Do not reintroduce legacy preprocessor baseline harnesses; see `LEGACY_MIGRATION.md`

## Verification

- `python -m pytest -q`
- Targeted: `pytest -q -k renderer_v2` (or narrower)

## Child DOX Index

- No child AGENTS.md — fixtures stay under this boundary.
