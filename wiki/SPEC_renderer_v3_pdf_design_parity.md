# SPEC: renderer_v3 PDF Design & Data Parity (Amex Q1'26)

**Status:** proposed — DP-1..DP-5 shipped in #224–#232; DP-6 helpers + `scripts/run_amex_simulation_v13.sh` are in-repo (#233); #249 extends the DP-6 design-ledger probes (stub ratio, support chrome, series palette, metric-value floor, bar occupancy). DP-7 stub-slack cap + sparse bar occupancy shipped in #246. #256 formally accepts D167 hide_header + hairline body on s4/s19 (no duplicate navy period band). #257 repeats the part-1 legal title on every part and raises fixed legal type to 56/21. The v13 observation sim itself is still unrun.
**Scope:** renderer_v3 (schema-v1, 3.0.0) + canonical D314 corpus, full 44-page Amex Q1'26 deck.
**Extends, does not replace:** `SPEC_renderer_v3_full_deck_density_and_chart_fidelity.md` (still the binding v3 contract). Brand-seal art stays R3-wontfix.

## 1. Evidence base

| source | identity |
|--------|----------|
| PDF (source of truth) | `Q1-2026-Earnings-Presentation.pdf`, SHA-256 `a87c1162…`, 44 pages, 960×540pt |
| v11 baseline (v2 peak) | `wiki/baseline_v11_GAP_ANALYSIS.md` @ `42f620c` / branch `gnhf/objective-produce-th-5765a4` |
| v12 baseline (v3 first) | `wiki/baseline_v12_GAP_ANALYSIS.md` @ branch `gnhf/objective-produce-th-dae3cb` |
| PDF type scale (PyMuPDF spans, ×2 to 1920px) | axis ticks **12pt ≈ 24px**; data labels **14pt ≈ 28px**; footnotes 8pt ≈ 16px; slide titles 28pt ≈ 56px (sampled pages 4, 13) |

## 2. Root-cause analysis: how design parity was lost v11 → v12

The regression has **four independent causes**. Only C4 is renderer defect; the rest are corpus, calibration, and verification gaps.

### C1 — Corpus backfill never happened (14 slides; largest slice)

The D314 canonical corpus was built from corrected fixtures + worksheet *before* the v2 mutation-pass authoring matured, and v12 rendered it strictly with no mutation pass. Furniture that v2 carried on slides 4–6, 8–10, 12, 15, 17–19, 21, 24, 28 was never ported into the v1 payloads — even though schema-v1 **already owns every needed construct** (`support_table`, `outlined_support`, `metric_strip`, `context_labels`, `annotations`, `measurements`, boxed-label / authored-stack-total `auxiliary_series`, `coverage_callout`, `category_groups`). Lost: Leap-Year callouts + bottom support tables (s4/5/9/10/19), side KPI stacks (s8), 3-band NCA stack (s12), reserve-rate outlined row (s15), `$B` format + CAGR rule (s17), YoY boxes + driver rows (s18), shares line + correct ROE row (s21), braces + `$486B` + %-of-total boxes (s24), FDIC callout + stack totals (s28). Plus two outright extraction errors: s17/s18 `format_id: pct_0` on `$B` series; s21 ROE row constant 35%.

### C2 — Typography calibration collapsed to floors (every chart slide)

v3 chart role bounds (`charts.py::_ROLE_BOUNDS`, D294) floor at 13–16px with **no weight policy**; the deck-wide adaptive plan froze **all 23 Amex chart surfaces at 14px** (measured `run_meta.plans`: every surface `(category_ticks=14, value_ticks=14)`, zero adaptations). Contrast:

| surface | PDF (grounded) | v2 @ v11 (measured) | v3 @ v12 (measured) |
|---------|----------------|---------------------|---------------------|
| axis ticks | 12pt ≈ **24px** | **24px, bold** (`y_weight="bold"`) | **14px, weight 400** |
| data/segment labels | 14pt ≈ **28px** | painted datalabels (plugin) | 14px-floor roles, weight 400 |
| pane titles | — | 40px | authored headings — OK |

Ticks render at ~58% of source size and lose the bold treatment. This is the user-visible "small, thin axis labels" regression. It slipped through because no verification axis measured it (C3).

### C3 — No design-parity verification axis existed (v11/v12)

The v11/v12 sims verified identity, paint-readiness, geometry alignment, and content — but nothing asserted rendered px size / computed weight against PDF-derived minimums. The qualitative ledger classified content, not type scale. A 14px-vs-24px regression was invisible to that QA loop by construction. #233 shipped the DP-6 helpers and v13 launcher (see DP-6); the observation sim is still unrun.

### C4 — Four genuine renderer gaps (small slice)

R-A s11: low-variance % series auto-domain collapses to ~9–10% → false drama (PDF frames 0–15%). R-B s7: `comparison_cards` has no circular dual-metric card recipe. R-C s32: grouped-annex column headers clip (`Q…`/`F…`). R-D s38–43: `legal_notice` paints a dense wall, losing bullet hierarchy.

## 3. Design-parity contract (DP-1 … DP-7)

### DP-1 Chart typography floors & weights (C2)

Grounded targets (PDF pages 4/13, ×2 scale). All values are plan floors; ceilings unchanged.

| role | current (floor, ceil) | required floor | weight |
|------|----------------------|----------------|--------|
| `category_ticks` | (14, 24) | **20** | **600** (`--font-weight-emphasis`) |
| `value_ticks` | (14, 28) | **20** | **600** |
| `ordinary_values` / `segment_labels` / `stack_totals` | (14, 24–32) | **18** | **600** for authored values |
| `legend` / `series_labels` | (16, 24) | 16 (hold) | 400 (hold) |
| `axis_titles` / `annotations` | (13, 24) | 16 | 600 for axis titles |
| `metric_strip` values | 28 (D265) | **44** (painted floor ≥ **40** on s8) | 600 |
| hero / `metric_overview` heading / body / value | 22 / 16 / 44 | **32 / 22 / 72** (s12/s18/s21/s22; strip stays 44) | 700 on values |

#248 palette override (D43/D131): default cycles are bar `primary_blue, navy, sky_blue, neutral, warning` and line `navy, primary_blue, sky_blue, neutral, warning`. `success` is reserved for semantic increase/decrease. `sky_blue` may identify a series as a fill accent. Direct labels on a series that fails 4.5:1 on white use navy ink + series-color connectors (D304; line/combo/bar/stack).

Chart.js options must emit `font.weight` for ticks and painted values (both painters: Chart.js config + SVG `font-weight`); the SVG painter currently sets no weight on tick `<text>`. Acceptance: computed-style probes per chart slide (presentation attributes alone are not evidence).

### DP-2 Chart furniture parity (C1; per-slide mapping)

Every PDF furniture element must map to an existing schema-v1 construct — new constructs only if a gap is proven. Canonical mapping:

| PDF furniture | schema-v1 construct |
|---------------|---------------------|
| side callout boxes (Leap Year, elbow, FDIC) | `annotations` / `context_labels` (+ `coverage_callout` for stacks) |
| bottom support tables / outlined rows | `support.support_table` / `support.outlined_support` |
| category-aligned support chrome (#247/#256) | visible body `.support-cat-cell` / `.support-cat-stub` carry hairline borders. When the chart already owns categories (D167 `hide_header`, s4/s19), no `.head` / navy period band is required or treated as a chrome defect. When a visual header row is painted (hidden-axis / independent header), `.head` still asserts navy band + hairlines. Decorative navy band without category labels is parked. sr-only semantic twin and frozen category centers stay byte-identical |
| side KPI stacks | `support.metric_strip` |
| under-bar YoY boxes | boxed-label `auxiliary_series` |
| braces / group labels (s24) | `category_groups` |
| line overlay on bars (s21 shares) | combo `mark_type: line` series |
| on-stack segment dollars / values (s12 / s15 / s21 / s28) | `display.stack_segments: "show"` (#260; s28 already authored) |
| CAGR rules | `measurements` |

### DP-3 Domain policy (R-A)

Percent series with low variance must not auto-collapse: pin `domain.kind=fixed` from corpus **or** renderer enforces a minimum domain span/pad for pct formats. Acceptance: s11 re-render reads near-flat inside a 0–15-style frame.

### DP-4 Recipe gaps (R-B/R-C/R-D)

- `comparison_cards`: add the circular dual-metric card recipe (or document an accepted divergence with numbers complete).
- `grouped_annex_table`: header cells must fit full text (no `Q…` ellipsis) — measure `scrollWidth ≤ clientWidth` on both groups.
- `legal_notice`: preserve payload list hierarchy as painted `<ul>` structure, not a flattened stream. Unmarked-only payloads paint one `<ul>` per paragraph so logical groups keep `--space-sm` spacing (#247 R-D). Every part of a `notice_id` paints the part-1 authored title (continuations still forbid `title`); never `— continued`. Fixed type is 56/21px — the largest pair that strict-renders Amex s38–43 (#257 R-D remainder).

### DP-5 Brand art exclusion

s1/s23/s44 seal/full-bleed covers remain R3-wontfix; recipe chrome is accepted divergence, not a parity target.

### DP-6 Parity verification axis (C3)

Every future sim adds a **design ledger** beside the content ledger: per chart slide, measured-px assertions (tick px ≥ floor, computed `font-weight`, furniture DOM presence per DP-2 map) recorded in the manifest. Helpers in `scripts/simulation_probe.py` (unique `data-slide-number` + `data-layout`; zero matches / `ProbeError` = failure):
- `#233`: `measured_tick_styles`, `furniture_presence`, `DESIGN_LEDGER_FURNITURE`
- `#249`/`#256` extensions (slide maps + floors live next to the helpers): `measured_stub_ratio` (`DESIGN_LEDGER_STUB_RATIO_SLIDES` s3/s16/s31–37, stub ≤45%), `measured_support_chrome` (s4/s19 accept hide_header + hairline body cells; a missing body frame still fails; painted `.head` still asserts navy band + hairlines), `measured_series_palette` (s24/s28; no non-semantic `#0A7D55`; sky_blue where authored), `measured_metric_value_styles` (s8/s12 ≥40px), `measured_bar_occupancy` (s28 ≥0.5)

Launcher: `scripts/run_amex_simulation_v13.sh` (prompt wires the #249/#256 rows into the design-ledger manifest). Geometry/px measurement is evidence, not image scoring — MAE/similarity/pixel-diff remain forbidden. The v13 sim report (`wiki/baseline_v13_GAP_ANALYSIS.md`) is produced by that launcher, not this ticket.

### DP-7 Table stub-slack cap & sparse bar occupancy (#246)

Renderer-owned geometry overrides (density-spec requirements unchanged; this spec carries the DP override):

- Semantic tables (`data_table`, `annex_table`, `grouped_annex_table`, `period_comparison`): leftover box width is not dumped into the stub. Stub share ≤ 45% unless the stub’s own minimum exceeds that; remaining slack goes to value columns (evenly). D25/D70 (never wrap/ellipsize values) and D69/D167 category-center contracts stay as written.
- Bar families with ≤6 categories: painted thickness occupies ≥50% of category pitch (target 55%). Theme `BAR_MAX_THICKNESS` (56px) remains the dense-chart cap. Chart.js `categoryPercentage` follows freeze geometry (D160).

## 4. Data-layer parity: corpus backfill manifest

Owner: corpus authoring (build_canonical_amex_v1 inputs); schema already supports every construct.

| slide | missing payload | construct | acceptance probe |
|------:|-----------------|-----------|------------------|
| 4, 5, 9, 10, 19 | Leap-Year callout; bottom support table; s4/s19 series identity; PDF ticks | `annotations` + `support_table` + authored ticks | DOM: callout text + support rows; Chart.js series/ticks |
| 5, 9, 10 | generation / segment supports + G&S/T&E side facts | `support_table` + `context_labels` | DOM: KPI values + YoY facts present |
| 11 | Leap-Year callout + PDF ticks (no support table / no side pair) | `annotations` + authored ticks | DOM: callout text; Chart.js ticks |
| 8 | FHR+THC Q3-flat then Q4 step | authored series values | Chart.js FHR data 40/40/40/50/50 |
| 38 | PDF legal preamble then two risk bullets | first unmarked paragraph + marked lists | DOM: `<p>` then two `<ul>`s |
| 17 | shipped #229/#258 | see D314 worksheet; dated pane headings + subtitle | `tests/test_amex_s17_s18_furniture.py` |
| 18 | shipped #229 | see D314 worksheet | `tests/test_amex_s17_s18_furniture.py` |
| 12 | shipped #228 / #260 | 3-band NCA stack + `stack_segments: show` | `tests/test_amex_s12_nca_stack.py` |
| 15 | shipped #227 / #260 | reserve-rate row + authored totals + `stack_segments: show` | `tests/test_amex_s6_s8_s15_furniture.py` |
| 21 | shipped #230 / #260 | combo line + `outlined_support` values + `stack_segments: show` | `tests/test_amex_s21_s24_s28_furniture.py` |
| 24 | shipped #230 | `category_groups` + `$486B` annotation + boxed %-of-total | `tests/test_amex_s21_s24_s28_furniture.py` |
| 28 | shipped #230 | `annotations` + authored $ totals + on-stack % | `tests/test_amex_s21_s24_s28_furniture.py` |

## 5. Acceptance & verification

1. Unit tests per change batch in `tests/` (renderer roles/weights; corpus fixture contracts like the existing `test_amex_*_handoff_contract.py` pattern).
2. `python -m impact_slides.renderer_v3` strict render of the updated corpus: exit 0 clean.
3. Observation sim (v13, `scripts/run_amex_simulation_v13.sh`; user-triggered, not part of #233/#249/#256): full 44-page SBS re-run **with the DP-6 design ledger** (including the DP-6 extension probes); classification adds `design-parity verified` per slide; the same no-image-scoring rule applies.
4. Definition of done: 44/44 slides classified faithful reproduction or accepted v3 design divergence **with the design ledger green**; R-A…R-D closed or explicitly re-accepted.

## 6. Out of scope

- renderer_v2 changes (frozen legacy).
- Brand-seal / full-bleed cover art (R3).
- Image-similarity scoring of any kind.
- Preprocessor/extraction pipeline changes beyond corpus authoring inputs.
