# tests

## Purpose

Regression suite and fixtures for preprocessor, renderer_v2, and renderer_v3 kernel/publication/theme/plan/data_table/brand-legal/annex-comparison/line_chart/heatmap/bar_charts/stacked_bar/waterfall/chart_support/linear_grouping/relationship/cards_reviews/migrate/canonical_amex.

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
- Renderer v3 notes/evidence/disclosure (#181): `test_renderer_v3_publish.py` + `test_renderer_v3_kernel.py` (exact notes HTML↔MD, hidden notes CSS, nested locator sort, names-only footers, native details IDs/print, whitespace notes reject, duplicate footer-name strict/non-strict)
- Renderer v3 theme (#177): `test_renderer_v3_theme.py` (boardroom_amex manifest to CSS/Chart.js/SVG tokens, contrast-safe roles, no raw painter hex, transparent chart surfaces, CSS drift gate)
- Renderer v3 plan (#178): `test_renderer_v3_plan.py` (deck-wide measure/plan freeze, grow-only prose/subtitle/takeaway, sync groups, strict/non-strict overflow, frozen plan in run_meta + HTML data-*)
- Renderer v3 data_table (#179): `test_renderer_v3_data_table.py` + fixture `renderer_v3/minimal_data_table.json` (semantic values + format registry, rectangular table identity, navy headers/a11y associations, one common fitted size, strict/non-strict overflow without data loss)
- Renderer v3 brand/divider/legal (#191): `test_renderer_v3_brand_legal.py` + fixture `renderer_v3/brand_divider_legal.json` (cover/divider placement + registry labels, multipart legal sequence + exact paragraphs, forbidden fields, mutation traps)
- Renderer v3 annex/comparison tables (#180): `test_renderer_v3_annex_comparison.py` + fixture `renderer_v3/annex_and_comparison_tables.json` (`annex_table`/`grouped_annex_table`/`period_comparison`/`comparison_cards`; grouped headers + disclosure; fixed period roles + metric strip; peer cards; non-strict complete-data fallbacks; pre-validation table cell/group repair; cards a11y/print contract; peer-heading fit threshold; sync floor bound; mutation traps)
- Renderer v3 line chart (#182): `test_renderer_v3_line_chart.py` + fixture `renderer_v3/minimal_line_chart.json` (typed single_chart line envelope, null gaps, frozen plan, Chart.js + noscript SVG parity, one semantic table, identity/point labels, no gridlines, readiness payloads, mutation traps)
- Renderer v3 heatmap (#187): `test_renderer_v3_heatmap.py` + fixture `renderer_v3/minimal_heatmap.json` (typed heatmap visual + shared format + generated/fixed scale, one visible native table, scale key, no canvas/SVG, missing neutral, readiness without chart painters, mutation traps)
- Renderer v3 grouped/horizontal bars (#183): `test_renderer_v3_bar_charts.py` + fixtures `renderer_v3/minimal_grouped_bar.json` / `minimal_horizontal_bar.json` (signed/zero/null geometry, outside values, D237 groups + boxed labels, horizontal leading-break contract, Chart.js/SVG ≤2px parity, identity/order, mutation traps)
- Renderer v3 stacked bars (#184): `test_renderer_v3_stacked_bar.py` + fixture `renderer_v3/minimal_stacked_bar.json` (sign-separated +/- stacks, independent segment/total policies, missing-aware computed totals, authored totals, coverage callout, Chart.js/SVG ≤2px parity, identity/order, mutation traps)
- Renderer v3 waterfall (#186): `test_renderer_v3_waterfall.py` + fixture `renderer_v3/minimal_waterfall.json` (typed change/total/computed_total steps, total reset + computed level, structural labels/connectors, D247 role/value/level table, Chart.js floating-bar/SVG ≤2px parity, malformed sequence strict-fail, mutation traps)
- Renderer v3 linear/grouping (#192): `test_renderer_v3_linear_grouping.py` + fixture `renderer_v3/linear_grouping_compositions.json` (`process_flow`/`timeline`/`layered_architecture`/`data_pipeline`; authored order/grouping/chronology/transfer preserved, fixed D60 geometry, layers without inferred connectors, non-strict accessible fallbacks without connectors, mutation traps)
- Renderer v3 relationship/decision (#193): `test_renderer_v3_relationship.py` + fixture `renderer_v3/relationship_compositions.json` (`decision_tree`/`feedback_loop`/`hierarchy`/`stakeholder_map`/`quadrant_matrix`; graph/assignment invariants, no inferred relations, non-strict relationship-table/outline/four-group fallbacks preserving authored facts, mutation traps)
- Renderer v3 cards/reviews (#194/#215): `test_renderer_v3_cards_reviews.py` + fixture `renderer_v3/cards_reviews_compositions.json` (`feature_cards`/`quotation`/`evidence_review`/`risk_opportunity_review`/`recommendation_case`/`state_transition`; closed icons + D287 field bans; fit/paint CSS parity incl. list indent + step pad + statement trailing margin; per-composition near-overflow sequential fallbacks; mutation traps)
- Renderer v3 offline migrator (#195): `test_renderer_v3_migrate.py` (D119/D313 57-input inventory, `--check` non-writing, source immutability, failed-proof → unresolved, v1 marker withhold, clean narrative/table conversion + validation, authored disclosure preservation, deck-unique surface ids + referenced-only number_formats, no render/validate import of migrate)
- Renderer v3 chart support surfaces (#189): `test_renderer_v3_chart_support.py` (typed `support_table`/`outlined_support`/`metric_strip` on `single_chart`; category/independent alignment; outlined centers ≤2px; D47 320×240 plot floor; complete rows/metrics; mutation traps)
- Amex #158 handoff + multi_panel pane titles: `test_amex_s28_handoff_contract.py` + `test_multi_panel_pane_headings.py` + fixtures `amex_s28_v10_broken.json` / `amex_s28_corrected.json` (mutation drops slide-28 `top_total` pseudo-titles; renderer multi_panel tiles share #147 heading/subtitle chrome; SVG honors `stack_total_labels`)
- #151 driver_card + boxed bar labels: `test_driver_card.py` + `test_boxed_labels.py` (schema 1/6/7 rows, malformed direction/tone, overflow strict/non-strict, no-valid-row hero fallback, order/a11y; boxed category mismatch, in-bar/outside+connector, Chart.js+SVG, collision independence). Slide 18 target lives in `amex_v10_44_slide_handoff.json`
- When adding layout references, regenerate `wiki/renderer_v2_LAYOUTS.md` if the index test-column drifts
- Do not reintroduce legacy preprocessor baseline harnesses; see `LEGACY_MIGRATION.md`

## Verification

- `python -m pytest -q`
- Targeted: `pytest -q -k renderer_v2` or `pytest -q tests/test_renderer_v3_kernel.py tests/test_renderer_v3_publish.py tests/test_renderer_v3_theme.py tests/test_renderer_v3_plan.py tests/test_renderer_v3_data_table.py tests/test_renderer_v3_brand_legal.py tests/test_renderer_v3_annex_comparison.py tests/test_renderer_v3_line_chart.py tests/test_renderer_v3_heatmap.py tests/test_renderer_v3_bar_charts.py tests/test_renderer_v3_stacked_bar.py tests/test_renderer_v3_waterfall.py tests/test_renderer_v3_chart_support.py tests/test_renderer_v3_linear_grouping.py tests/test_renderer_v3_relationship.py tests/test_renderer_v3_cards_reviews.py tests/test_renderer_v3_migrate.py tests/test_renderer_v3_canonical_amex.py`

## Child DOX Index

- No child AGENTS.md — fixtures stay under this boundary.
