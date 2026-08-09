# tests

## Purpose

Regression suite and fixtures for preprocessor, renderer_v2, and renderer_v3 kernel/publication/theme.

## Ownership

- `tests/test_*.py`, `conftest.py`, `fixtures/`
- Notes: `README.md`, `LEGACY_MIGRATION.md` (legacy v2/v3 baselines removed; v4 suite is the net)

## Local Contracts

- Runner: `pytest` via root `pytest.ini` (`testpaths=tests`)
- CI install set: root `requirements-ci.txt` (includes `structlog` and Playwright; excludes sentence-transformers); CI provisions Chromium for mandatory renderer audits
- Some real-world fixtures are machine-local — CI shows extra skips; local pass count can be higher
- Renderer layout index tests must not embed bare layout-name literals or search probes that match the test file itself (`test_gen_layout_index.py` pattern)
- Prefer tests that fail under mutation of the production guard they claim to pin

## Work Guidance

- Fixtures for renderer: `tests/fixtures/renderer_v2/`
- Amex #148 handoff contract: `test_amex_s13_s14_handoff_contract.py` + fixtures `amex_s13_s14_v10_broken.json` / `amex_s13_s14_corrected.json` (mutation via `scripts/amex_handoff_mutations.py`)
- Amex #153 handoff contract: `test_amex_slide26_matrix_orientation.py` + fixture `amex_slide26_te_billed_business.json` (Q1'26 period header + category-column matrix; identity-safe cell asserts + adversarial mutations; no renderer production change)
- Amex #155 handoff contract: `test_amex_s21_capital_handoff_contract.py` + fixture `amex_s21_v10_broken.json` (chart_hero_dual capital-return stacked combo + shares line + stack totals + outlined ROE support row + right summary KPIs; 1920×1080 identity-safe geometry + adversarial mutations; Chart.js multi-series combo stacks)
- Amex #154 handoff contract: `test_amex_s24_growth_handoff_contract.py` + fixture `amex_s24_v10_broken.json` (six grouped growth bars, semantic brackets, aligned outlined support row, and FX-adjusted reporting note; 1920×1080 identity-safe geometry + adversarial mutations; authorized minimal Chart.js bracket capability)
- Amex #156 slide-27 handoff contract: `test_amex_s27_scenarios.py` + fixtures `amex_s27_v10_broken.json` / `amex_s27_corrected.json` (`apply_issue_156_slide27_scenarios`; 13 quarterly categories, all three scenarios, E0026 PDF citation, source headings/SAAR note + #146 paint-ready dual-canvas geometry; no renderer production change)
- Amex #157 annex handoff contract: `test_amex_annex_33_37_handoff.py` + fixtures `amex_annex_33_37_v10_broken_handoff.json` / `amex_annex_33_37_restored_handoff.json` (`apply_issue_157_annex_matrices`; PDF-source semantic-cell probes + 1920×1080 browser geometry; no renderer production change)
- Amex #159 grouped annex composition: `test_grouped_annex_table.py` + `amex_slide32_grouped_annex.json` (`apply_issue_159_grouped_annex`; source-group mutation traps, schema/strict fallback, and 1920×1080 browser geometry)
- Renderer v3 kernel (#175): `test_renderer_v3_kernel.py` + fixture `renderer_v3/minimal_cover_narrative_cover.json` (typed Deck validation, allowlisted repairs, schema drift, v2 isolation + mutation traps)
- Renderer v3 publish (#176): `test_renderer_v3_publish.py` (five D250 artifacts, clean/degraded/failed + CLI exit codes, byte-identical reruns, failed-run preservation + mutation traps)
- Renderer v3 theme (#177): `test_renderer_v3_theme.py` (boardroom_amex manifest to CSS/Chart.js/SVG tokens, contrast-safe roles, no raw painter hex, transparent chart surfaces, CSS drift gate)
- Amex #158 handoff + multi_panel pane titles: `test_amex_s28_handoff_contract.py` + `test_multi_panel_pane_headings.py` + fixtures `amex_s28_v10_broken.json` / `amex_s28_corrected.json` (mutation drops slide-28 `top_total` pseudo-titles; renderer multi_panel tiles share #147 heading/subtitle chrome; SVG honors `stack_total_labels`)
- #151 driver_card + boxed bar labels: `test_driver_card.py` + `test_boxed_labels.py` (schema 1/6/7 rows, malformed direction/tone, overflow strict/non-strict, no-valid-row hero fallback, order/a11y; boxed category mismatch, in-bar/outside+connector, Chart.js+SVG, collision independence). Slide 18 target lives in `amex_v10_44_slide_handoff.json`
- When adding layout references, regenerate `wiki/renderer_v2_LAYOUTS.md` if the index test-column drifts
- Do not reintroduce legacy preprocessor baseline harnesses; see `LEGACY_MIGRATION.md`

## Verification

- `python -m pytest -q`
- Targeted: `pytest -q -k renderer_v2` or `pytest -q tests/test_renderer_v3_kernel.py tests/test_renderer_v3_publish.py tests/test_renderer_v3_theme.py`

## Child DOX Index

- No child AGENTS.md — fixtures stay under this boundary.
