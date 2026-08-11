# renderer_v3

## Purpose

Schema-v1 canonical rendering kernel for Impact Slide Renderer 3. Sibling of frozen legacy `renderer_v2`. Owns typed validation into one canonical deck model, deck-wide measure/plan freeze for kernel prose/chrome/tables/axis charts/heatmaps/linear+grouping + relationship/decision compositions, decimal-safe number formatting, deterministic five-artifact publication, the sole boardroom_amex theme manifest (CSS/Chart.js/SVG tokens), axis-chart painters for line + grouped/horizontal/stacked bars + waterfall (Chart.js + noscript SVG + D247 semantic table), native semantic heatmaps (D163/D246/D308), process/timeline/layered/pipeline compositions, decision_tree/feedback_loop/hierarchy/stakeholder_map/quadrant_matrix (D194–D200/D274–D280), and the offline legacy→v1 migration tool (D119/D313); remaining chart/card families land in later tickets.

## Ownership

- Closed schema-v1 handoff models (`models.py`) including D213 semantic values + D255 `table` + table compositions (`data_table`, `annex_table`, `grouped_annex_table`, `period_comparison`, `comparison_cards`) + linear/grouping compositions (`process_flow`, `timeline`, `layered_architecture`, `data_pipeline`) + relationship/decision compositions (`decision_tree`, `feedback_loop`, `hierarchy`, `stakeholder_map`, `quadrant_matrix`) + `single_chart` envelope for `line` / `grouped_bar` / `horizontal_bar` / `stacked_bar` / `waterfall` / `heatmap` (D162/D163/D194–D200/D227–D243/D245–D248/D272–D280/D290–D304/D307/D308) with optional `category_groups` + boxed-label / authored-stack-total `auxiliary_series` + stacked-only `coverage_callout`; waterfall uses `waterfall_data.steps` (not D228 series)
- Decimal-safe format registry (`format.py`) for D77/D78/D103/D214/D293
- Axis-chart freeze + dual painters + semantic table for line, grouped/horizontal/stacked bars, and waterfall (`ChartData` series max 6; line/grouped/hbar 1–4, stacked 2–6); heatmap freeze + native HTML painter (`charts.py`) (D53/D57/D63/D71–D73/D79/D106/D157/D160/D162/D163/D241–D243/D245–D248/D302/D304/D307/D308)
- Aggregating validation + allowlisted non-strict repairs (`validate.py`, `repairs.py`, `diagnostics.py`)
- Deck-wide adaptive measure/plan freeze (`plan.py`) for narrative prose, data tables, axis charts (incl. stacked bars), heatmaps, linear/grouping + relationship/decision compositions (fixed D60 type), subtitles, takeaways, disclosures, source footers, and fixed chrome (D1–D4, D22–D25, D44, D59, D60, D68–D70)
- Public `render_deck` + CLI publication (`render.py`, `publish.py`, `cli.py`)
- Generated JSON Schema artifact `schema/handoff_schema_v1.json` (D121)
- Canonical `boardroom_amex` theme manifest + generated CSS (`theme/`, `theme_export.py`) and self-contained licensed webfonts (`assets/fonts/`) (D127-D133)
- Vendored Chart.js UMD + license (`assets/libs/chart.umd.min.js`, `assets/libs/CHART_JS_LICENSE.md`) inlined into published decks
- Offline legacy→schema-v1 migrator (`migrate.py`) — D119/D313/D316 inventory, proof gates, `--check`, v1 marker withhold; never mutates sources or `renderer_v2`
- Does **not** own legacy v2 layouts, recipes, or charts; production `render_deck`/`validate_handoff` have no hidden legacy path

## Local Contracts

- Public API: `from impact_slides.renderer_v3 import render_deck, validate_handoff, RendererValidationError, RendererConfigurationError, RendererPublicationError`
- CLI: `python -m impact_slides.renderer_v3 --handoff PATH --out DIR` (strict default; `--no-strict`, `--debug`, `--svg-only`); `schema --check` / bare `--check` retain the D121 drift gate
- Migrator CLI: `python -m impact_slides.renderer_v3.migrate --handoff PATH --out DIR` or `--check` (writes nothing; exit 0 only when all slides resolve and candidate validates). Emits `migration_report.json` always on write; `handoff_v1.json` only when unmarked decisions are zero and validation is clean; otherwise unmarked `handoff_candidate.json`. All 57 D313 inputs get one inventory disposition; failed proofs and human layouts are unresolved decisions (D119/D313)
- `validate_handoff(raw, *, strict=True) -> ValidationResult` with `.deck` as the only paint input (D122)
- `plan_deck(deck, *, strict=True) -> DeckPlan` freezes whole-pixel role sizes at 1920×1080 before paint; strict overflow → `RendererValidationError` / `plan.unresolved_overflow`; non-strict paints complete floor-size text degraded (D59/D69/D312); typography sync never freezes a member below the highest member role floor
- `render_deck(handoff_path, out_dir, *, strict=True, ...)` validates → plans → publishes exactly five UTF-8/LF artifacts: `presentation.html`, `slide_notes.md`, `evidence_manifest.json`, `run_meta.json`, `handoff_schema_v1.json` (D250)
- Clean → exit 0 / `ok: true`; degraded non-strict → exit 2 / `ok: false`; failed → typed error, exit 1, prior output untouched (D112/D312)
- HTML surfaces carry compact `data-plan-sizes` / `data-plan-adaptations` plus projected `data-diagnostic-codes` / `data-diagnostic-count` from `DiagnosticEvent.surface_id`; `run_meta.plans` holds one entry per planned surface (D21/D312)
- Speaker notes are exact root plain text (D173/D221): no trim/synthesis; whitespace-only rejected; HTML `<aside class="notes">` matches `slide_notes.md` after unescape; notes CSS is `display:none;white-space:pre-wrap` (off-slide)
- Evidence registry + slide `evidence_ids` / optional `source_footer` (D175–D176/D216–D217): manifest keeps full registry + nested key-sorted locators; visible footers paint authored-order `source_name` only (never IDs/locators); strict rejects normalized-duplicate footer names; non-strict `repair_source_footer_names` keeps first
- Disclosure is native `<details>` accordion (D174/D222/D289): deterministic `slide-{n}-{surface_id}` IDs, initially closed, print CSS expands bodies; no-JS markup remains complete
- Takeaway outer reservation includes label/pad/border/outer margin; text fitter uses the inner box only. Cover elements measure at their own frozen role sizes. Paragraph/list margins match paint per CSS block box. Planning uses calibrated Source Sans 3 metrics, diagnoses conservative unsupported-glyph fallback, and publication embeds the vendored font.
- Strict aggregates all detectable errors into `RendererValidationError.events` (D120/D309/D310)
- Non-strict applies only `repairs.REPAIR_REGISTRY` actions, then revalidates (D123/D311); `repair_disclosure_sections` drops malformed/duplicate D222 sections (keep first); `repair_source_footer_names` drops later duplicate visible footer names; `repair_table_data` converts missing/malformed cells to diagnosed missing, drops cell keys for unknown columns, and flattens malformed `column_groups` while retaining leaf data before TableData validation; `repair_uncontained_fixed_domains` replaces a fixed domain that fails to contain every finite value (stacked bars: zero + signed stack extents, D83/D242) with a diagnosed safe generated domain and drops authored generated `min`/`max` bounds that fail containment so the domain regenerates from data (strict rejects both, D230); `repair_invalid_heatmap_scales` replaces missing/malformed/out-of-range heatmap scales with generated so freeze paints the complete uncolored diagnosed table (strict rejects, D163/D308).
- Non-strict `drop_unknown_fields` may strip noise keys only: on brand/legal layouts it **retains** forbidden D287 ordinary semantic roots (`title`/`content`/`takeaway`/`disclosure`/`source_footer`, and `section_id` on covers/dividers) so revalidation fails without deleting authored content; typed D180 unresolved-slide fallback is not yet implemented
- `_wrap_lines` breaks at spaces and after `-,:;.` when more content follows; paint inserts matching `<wbr>` via `_soft_break_html` (R178-029). Disclosure units measure summary/list indent separately from full-width paragraphs
- Print media expands closed disclosures and resets viewport stage scale to fixed 1920×1080
- Kernel compositions: `opening_cover`, `section_divider`, `closing_cover`, `narrative`, `legal_notice`, `data_table`, `annex_table`, `grouped_annex_table`, `period_comparison`, `comparison_cards`, `process_flow`, `timeline`, `layered_architecture`, `data_pipeline`, `decision_tree`, `feedback_loop`, `hierarchy`, `stakeholder_map`, `quadrant_matrix`, `single_chart` (`line` / `grouped_bar` / `horizontal_bar` / `stacked_bar` / `waterfall` / `heatmap`) (D178–D187/D192–D200/D208/D210/D215/D223/D226/D251/D257–D261/D268–D280/D287/D302/D304/D307/D308)
- Brand slides: covers share one `CoverPayload` (title + optional subtitle/period/date); divider payload is only `section_id` with registry-derived label + section ordinal; renderer owns bands/rules/chrome (descendant CSS + per-type `*-overflow` outline classes); no root title/section/takeaway/disclosure/source_footer
- `legal_notice`: multipart `notice_id` + adjacent `part`/`total_parts`, plain paragraphs only; part 1 owns title, later parts paint renderer `— continued` + part-of-total; fixed 28/16px type, no adaptive growth or common takeaway/disclosure/footer
- `single_chart` axis charts: one frozen `chart_paint` drives Chart.js canvas + noscript SVG + one D247 semantic table; line nulls break paths; grouped/horizontal bars preserve signed/zero/null slots with outside values, optional D237 groups + D235 boxed labels, and D157 leading break (horizontal_bar additionally enforces the D243 positive-side contract); stacked bars accumulate positive/negative segments independently from zero in authored series order, with independent segment/total display policies, missing-aware computed totals, D235/D241 authored totals, and optional D236/D301 coverage callout; waterfall uses ordered `change`/`total`/`computed_total` steps (first total, last total/computed_total), total resets level, computed paints known level, mandatory structural labels + connectors, theme increase/decrease/total colors, D247 role/value/level columns, no legend/display/chart_data (D162/D245/D307); no gridlines; transparent plot/body; readiness flags `semantic_table_present` + `chart_painters`
- `single_chart` heatmap: one visible native HTML D255 table + mandatory scale key when finite data exists; shared format; generated/fixed scale; renderer-owned light→primary-blue fills + contrast-safe ink; no canvas/SVG/duplicate table; non-strict overflow paints complete uncolored table (D163/D246/D308)
- Envelope: `meta`, `sections`, `number_formats`, `evidence_registry`, `slides` (D211); `number_formats` uses closed unit vocabulary (`usd`/`percent`/`percentage_points`/`basis_points`)
- `data_table` paints one full-width D255 table: navy headers, transparent body, native `scope`/`headers`, one common 20–24px fit, em-dash missing, no row/column/value loss (D24–D25/D103–D105)
- `annex_table` reuses the table surface at 12–24px with disclosure-only notes (no takeaway); `grouped_annex_table` paints 1–2 equal-width headed peers with shared annex size and sequential flat-table non-strict fallback (D184/D185/D258/D259); peer `short_heading` is used only after an actual full-heading fit failure and the full heading stays the accessible name
- `period_comparison` enforces ordered `current_period`/`comparison_period`/`variance` columns, optional exterior `metric_strip` (1–3 metrics), and ordinary-table non-strict fallback that keeps the strip (D186/D260/D265)
- `comparison_cards` derives equal-rank cards from 2–4 peer rows × 2–4 fact columns; visual cards are `aria-hidden` and the sr-only D255 table is the single accessibility source; print hides cards and restores the table; non-strict falls back to the complete accessible table (D187/D208/D261)
- `process_flow` / `timeline`: 2–6 / 2–8 author-ordered items; renderer owns orientation, step numbers, connectors; never infers branches/dates/durations; non-strict paints complete accessible ordered/chronological lists without connectors (D192/D193/D272/D273)
- `layered_architecture`: 2–4 layers × 1–4 components; order is grouping/stack only — no arrows; non-strict nested outline (D196/D276)
- `data_pipeline`: 2–6 stages × 1–3 components; optional `transfer_label` on non-final stages only; non-strict ordered flow keeps `A to B: label` wording (D197/D277)
- `decision_tree`: 3–15 nodes, authored root, max depth 4; decision 2–3 labeled branches / outcome leaves; graph invariants in `validate.analyze_relationship_structure`; non-strict unresolved → relationship table (no reconnect), unfittable valid → nested outline (D194/D274)
- `feedback_loop`: 3–8 ordered cycle items; `procedural` or `causal` (authored polarities; derived reinforcing/balancing only); non-strict missing effect → relationship table without invented links; unfittable valid → ordered list (D195/D275)
- `hierarchy`: 3–20 nodes, one root, one uniform `reports_to`/`part_of`/`is_a`; max depth 4; non-strict defects → relationship table; unfittable valid → nested outline (D198/D278)
- `stakeholder_map`: one focal + 2–8 spokes with exact label + direction; hub-spoke only; non-strict list/table preserves entities (D199/D279)
- `quadrant_matrix`: two binary axes + 1–16 items with explicit low/high bands; empty quadrants stay labelled; non-strict four-group fallback (D200/D280)
- Must not import `impact_slides.renderer_v2` or mutate v2 behavior
- Schema artifact is generated: `python -m impact_slides.renderer_v3.schema_export` (write) or `--check` (CI)
- Theme CSS artifact is generated from the Python manifest: `python -m impact_slides.renderer_v3.theme_export` (write) or `--check` (CI); painters resolve colors via `theme.resolve_color` / CSS `var(--color-*)` only (D129-D131)
- Chart plot/body surfaces stay transparent and flat via generated `.chart-plot`/`.chart-body` rules (D5/D6)

## Work Guidance

- Extend typed models first; regenerate schema; never hand-edit the JSON Schema
- New compositions need payload models + discriminator entry + plan roles + tests before paint
- Prefer root-cause validation in `Deck` / slide model validators over caller guards
- All adaptive sizing goes through `plan.py`; painters consume frozen `role_sizes` only — no runtime replanning
- Diagnostics stay closed (D309 codes/actions/results); no free-form stderr interface
- Publication stages all five artifacts then replaces; never partial writes to `out_dir`
- Share only genuinely immutable, version-neutral assets through a neutral module — never reach into v2 implementation packages
- Theme tokens change only in `theme/` manifest; regenerate CSS; never hand-edit `boardroom_amex.tokens.css` or put raw theme hex in painters

## Verification

- `python -m pytest -q tests/test_renderer_v3_kernel.py tests/test_renderer_v3_publish.py tests/test_renderer_v3_theme.py tests/test_renderer_v3_plan.py tests/test_renderer_v3_data_table.py tests/test_renderer_v3_brand_legal.py tests/test_renderer_v3_annex_comparison.py tests/test_renderer_v3_line_chart.py tests/test_renderer_v3_heatmap.py tests/test_renderer_v3_bar_charts.py tests/test_renderer_v3_stacked_bar.py tests/test_renderer_v3_waterfall.py tests/test_renderer_v3_linear_grouping.py tests/test_renderer_v3_relationship.py tests/test_renderer_v3_migrate.py`
- `python -m impact_slides.renderer_v3.schema_export --check`
- `python -m impact_slides.renderer_v3.theme_export --check`
- Full suite: `python -m pytest -q`
- CI: schema + theme CSS drift steps + pytest in `.github/workflows/ci.yml`

## Child DOX Index

- No child AGENTS.md — `schema/` is a generated artifact directory; `theme/` is the theme package (manifest + generated CSS), not a separate operating boundary.
