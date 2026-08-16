# Gap Analysis v13: renderer_v3 vs Amex Q1'26 Earnings PDF **(Complete 44-page PDF↔HTML observation with DP-6 design ledger — Companion-mode SIMULATION only)**

**Simulation:** `simulation/amex_q1_2026/`
**Source of truth:** `C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf`
**PDF identity:** SHA-256 `a87c11625c84e0dabb02d523f6a2d2508b892f18ee242ef197a9b40157bd3faf` · 44 pages · page0 rect 959.76×540.0
**Renderer under test:** `impact_slides.renderer_v3` **3.0.0** @ `a76b65f27b678a72f789f459bf2b646831534c26`
**Canonical input (read-only; no mutations):** `tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json`
**Handoff SHA-256:** `dc7742a6f422869656b6497405a4a0cdfe32ff12204d2b7a5c35deb0c71288c8`
**Prior baseline:** `wiki/baseline_v12_GAP_ANALYSIS.md` (extracted for this run from git `3690942` → `simulation/amex_q1_2026/extracted_baseline_v12_GAP_ANALYSIS.md`; tip of this branch does not carry the wiki file)
**Method:** One strict `python -m impact_slides.renderer_v3` publish → Playwright capture via `scripts/simulation_probe.wait_for_paint_ready_charts` + `measured_tick_styles` + `furniture_presence` (DP-6) + section isolate (lesson 32) → PyMuPDF 1920×1080 PDF rasters → full-resolution SBS. **No MAE / similarity % / pixel-diff scores / heatmaps.**

---

## 1. Scope gate, mapping assertion, run identity

| Gate | Result |
|------|--------|
| Renderer commit | `a76b65f27b678a72f789f459bf2b646831534c26` |
| Renderer version | `3.0.0` |
| Production paths touched | **None** (only `simulation/amex_q1_2026/**` + final `wiki/baseline_v13_GAP_ANALYSIS.md`) |
| Handoff | Committed D314 corpus only — **no** `amex_handoff_mutations.py`, no hand edits |
| Render command | `python -m impact_slides.renderer_v3 --handoff tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json --out simulation/amex_q1_2026/passes/pass_01/renderer_v3_out` |
| Render outcome | **strict exit 0**, `run_meta.status=clean`, `ok=true`, `options.strict=true` |
| `run_meta` events | 73 × `info` · **0** warn/error |
| PDF pages | 44 |
| HTML `data-slide-number` | 44 unique values **1…44** |
| HTML `data-layout` vs corpus `layout_type` | **44/44 match** |
| Identity map | **HTML slide N → PDF index N−1 → physical page N** |
| Capture contract | viewport **1920×1080**, `deviceScaleFactor=1` (fit scale 1); isolate target `section.slide` (siblings `display:none`, stage/slide transform none); element screenshot; `wait_for_paint_ready_charts` before every chart-slide shot; DP-6 `measured_tick_styles` + `furniture_presence` after paint-ready; **no** `painted_datalabel_lines` (v3 paints labels via overlay chrome, not chartjs-plugin-datalabels); no nth selectors; no fixed sleeps |
| Comparison artifacts | 44 PDF + 44 HTML + 44 SBS @ exact 1920×1080 halves (SBS 3840×1080); contact sheet; `comparison_manifest.json` `missing_or_bad_size=[]` |
| Design ledger | **44/44 rows** in manifest; chart slides all `ok=true` with tick floors ≥20px/≥600; C1 furniture slides 4/5/6/8/9/10/12/15/17/18/19/21/24/28 all green |
| HTML PNG uniqueness | **44 distinct SHA-256** (no blank-duplicate cover class) |
| Console errors | `[]` |
| Image scoring | **forbidden / absent** |
| Scope-gate | **PASS** |

### Published artifact hashes (`passes/pass_01/renderer_v3_out/`)

| File | SHA-256 |
|------|---------|
| `presentation.html` | `217c51c1e3c06aa08897e6673fe21a70d3ec0d1d92b9d93fc4db8324bf67801a` |
| `run_meta.json` | `33c559567aac57f4e329fec61af42ae1f77c816c831fb401ff85b6842aa58672` |
| `evidence_manifest.json` | `6b8c217a8b2384a4d09c7b24d2b52b3d5472d3761867ef8d0b3cc0af0244e3c5` |
| `handoff_schema_v1.json` | `8a650ad61f5c8a4a1b97f0d16cf53c03f651b958bc23339a3f7b5824ea0622c1` |
| `slide_notes.md` | `78823a5fba725aa5deb5961399a066b9a6935af1cf724bc851f2a8b079b4ae8e` |

### Capture contract detail

- Deck is a stacked scroll of all 44 `section.slide` nodes inside `.deck-stage` (no `.active` hide rule; resize-fit scales by `min(innerWidth/1920, innerHeight/1080)`).
- Capture forces transform/scale identity and screenshots the section node after paint-ready settle.
- Chart slides with paint-ready geometry (nonzero canvas, non-degenerate `chartArea`, painted dataset elements across one rAF): **4–6, 8–15, 17–19, 21, 24, 27–28**.
- Primary surface is JS-on Chart.js (SVG noscript fallback not used for comparison).
- DP-6 tick measurement uses **computed style** on overlay tick `<text>` (not presentation attributes alone). Furniture uses `DESIGN_LEDGER_FURNITURE` selectors + expected_text; zero matches = failure.

### Mapping assertion

| slide | layout_type (corpus = HTML) | pdf_index | physical_page |
|------:|-----------------------------|----------:|--------------:|
| 1 | `opening_cover` | 0 | 1 |
| 2 | `narrative` | 1 | 2 |
| 3 | `period_comparison` | 2 | 3 |
| 4 | `single_chart` | 3 | 4 |
| 5 | `single_chart` | 4 | 5 |
| 6 | `dual_chart` | 5 | 6 |
| 7 | `comparison_cards` | 6 | 7 |
| 8 | `single_chart` | 7 | 8 |
| 9 | `single_chart` | 8 | 9 |
| 10 | `single_chart` | 9 | 10 |
| 11 | `single_chart` | 10 | 11 |
| 12 | `chart_hero_dual` | 11 | 12 |
| 13 | `single_chart` | 12 | 13 |
| 14 | `dual_chart` | 13 | 14 |
| 15 | `single_chart` | 14 | 15 |
| 16 | `data_table` | 15 | 16 |
| 17 | `dual_chart` | 16 | 17 |
| 18 | `chart_hero_dual` | 17 | 18 |
| 19 | `single_chart` | 18 | 19 |
| 20 | `period_comparison` | 19 | 20 |
| 21 | `chart_hero_dual` | 20 | 21 |
| 22 | `metric_overview` | 21 | 22 |
| 23 | `section_divider` | 22 | 23 |
| 24 | `single_chart` | 23 | 24 |
| 25 | `data_table` | 24 | 25 |
| 26 | `data_table` | 25 | 26 |
| 27 | `dual_chart` | 26 | 27 |
| 28 | `dual_chart` | 27 | 28 |
| 29 | `narrative` | 28 | 29 |
| 30 | `narrative` | 29 | 30 |
| 31 | `annex_table` | 30 | 31 |
| 32 | `grouped_annex_table` | 31 | 32 |
| 33 | `annex_table` | 32 | 33 |
| 34 | `annex_table` | 33 | 34 |
| 35 | `annex_table` | 34 | 35 |
| 36 | `annex_table` | 35 | 36 |
| 37 | `annex_table` | 36 | 37 |
| 38 | `legal_notice` | 37 | 38 |
| 39 | `legal_notice` | 38 | 39 |
| 40 | `legal_notice` | 39 | 40 |
| 41 | `legal_notice` | 40 | 41 |
| 42 | `legal_notice` | 41 | 42 |
| 43 | `legal_notice` | 42 | 43 |
| 44 | `closing_cover` | 43 | 44 |

**HOLD** for all 44 rows.

---

## 2. DP-6 design ledger

Machine-readable twin: `comparison_manifest.json` → `design_ledgers[]` (one object per slide).

**Contract:** chart layouts run `measured_tick_styles` (computed font-size ≥ 20px, font-weight ≥ 600, tick_count > 0) and every `DESIGN_LEDGER_FURNITURE` entry for that slide via `furniture_presence`. Non-chart slides record `{ok: true, ticks: null, furniture: []}`. A `ProbeError` is recorded as failure — never invented green.

### Summary

| metric | result |
|--------|--------|
| Design-ledger rows | **44/44** |
| Overall ok | **44/44** |
| Chart slides measured | 4–6, 8–15, 17–19, 21, 24, 27–28 |
| Min tick font-size (all chart slides) | **20.0 px** (floor met) |
| Min tick font-weight (all chart slides) | **600** (floor met) |
| C1 furniture slides green | **4, 5, 6, 8, 9, 10, 12, 15, 17, 18, 19, 21, 24, 28** |
| Design-ledger failures | **none** |
| Capture/probe failures | **none** (`capture_errors=[]`, `console_errors=[]`) |

### Chart-slide tick + furniture detail

| # | layout | tick_count | min_px | min_wt | furniture rows (all ok) |
|--:|--------|----------:|-------:|-------:|-------------------------|
| 4 | `single_chart` | 10 | 20 | 600 | `[data-annotation-id]` “Leap Year Approx. (1%)”; `.support-table` “G&S” |
| 5 | `single_chart` | 10 | 20 | 600 | `.support-table` “Gen-Z” |
| 6 | `dual_chart` | 18 | 20 | 600 | `[data-annotation-id]` “+ ~6 percentage points” |
| 8 | `single_chart` | 10 | 20 | 600 | `.metric-strip` “3,400+” |
| 9 | `single_chart` | 10 | 20 | 600 | `.support-table` “U.S. SME” |
| 10 | `single_chart` | 10 | 20 | 600 | `.support-table` “Intl Consumer” |
| 11 | `single_chart` | 10 | 20 | 600 | *(none expected)* |
| 12 | `chart_hero_dual` | 10 | 20 | 600 | `[data-chart-type="stacked_bar"]` “International Card Services” |
| 13 | `single_chart` | 10 | 20 | 600 | *(none expected)* |
| 14 | `dual_chart` | 20 | 20 | 600 | *(none expected)* |
| 15 | `single_chart` | 11 | 20 | 600 | `.outlined-support` “Reserve Rate for Total Balances” |
| 17 | `dual_chart` | 28 | 20 | 600 | `[data-measurement-id][data-role="cagr"]` “17%” |
| 18 | `chart_hero_dual` | 9 | 20 | 600 | `.boxed-label` “11%”; `[data-hero-type="driver_card"]` “Billed Business” |
| 19 | `single_chart` | 11 | 20 | 600 | `[data-annotation-id]` “Leap Year Approx. (1%)”; `.support-table` “$17.0” |
| 21 | `chart_hero_dual` | 16 | 20 | 600 | combo semantic table “Common Shares Outstanding”; `.outlined-support` “ROE” |
| 24 | `single_chart` | 11 | 20 | 600 | `.category-group` “Commercial Services”; annotation “$486B Total Network Volumes”; `.boxed-label` “37%” |
| 27 | `dual_chart` | 36 | 20 | 600 | *(none expected)* |
| 28 | `dual_chart` | 16 | 20 | 600 | `[data-annotation-id]` “92% FDIC” |

**C2 typography collapse (v12: 14px/400):** **RESOLVED** on every measured chart slide — computed ticks are 20px/600.

**C1 furniture backfills (slides 4/5/6/8/9/10/12/15/17/18/19/21/24/28):** **RESOLVED** — every `DESIGN_LEDGER_FURNITURE` selector matched with expected text.

---

## 3. Full 44-page qualitative ledger

Classification is exactly one of:
`faithful reproduction` · `accepted v3 design divergence` · `candidate renderer defect or capability gap` · `corpus/extraction residual` · `source/PDF artifact` · `capture failure`.

SBS paths are relative to `simulation/amex_q1_2026/`. Machine-readable twin: `qualitative_ledger_v13.json`.

**Class counts:** faithful 28 · accepted divergence 9 · corpus residual 1 · candidate defect 6 · capture failure 0.

| # | layout_type | pdf_idx | page | SBS | class | observation (qualitative; no scores) |
|--:|-------------|--------:|-----:|-----|-------|--------------------------------------|
| 1 | `opening_cover` | 0 | P1 | `side_by_side/slide_01.png` | **accepted v3 design divergence** | PDF full-bleed navy/cyan brand cover with Centurion seal. v3 minimal white title (title + Q1'26 + April 23, 2026). Brand-seal omission is standing R3 wontfix; cover recipe intentional. |
| 2 | `narrative` | 1 | P2 | `side_by_side/slide_02.png` | **faithful reproduction** | Seven Business Highlights bullets match PDF substance and bold emphasis. Packing tighter/smaller type than PDF; footnote collapses to notes affordance. Content-complete. |
| 3 | `period_comparison` | 2 | P3 | `side_by_side/slide_03.png` | **accepted v3 design divergence** | All five KPI rows/values match. PDF uses large period pills; v3 compact right-hand matrix — schema-v1 period_comparison recipe, not a value error. |
| 4 | `single_chart` | 3 | P4 | `side_by_side/slide_04.png` | **faithful reproduction** | Dual FX-adj + Reported lines with endpoint labels 9%/10%. Leap Year Approx. (1%) annotation and bottom G&S/T&E support table both present (v12 residual resolved). Minor axis tick density vs PDF only. **design-parity verified**. |
| 5 | `single_chart` | 4 | P5 | `side_by_side/slide_05.png` | **faithful reproduction** | UCS billings line 7→10% paints. Generation-mix support table (Gen-Z…) present (v12 residual resolved). Side G&S/T&E callout styling differs slightly from PDF but content present via support. **design-parity verified**. |
| 6 | `dual_chart` | 5 | P6 | `side_by_side/slide_06.png` | **faithful reproduction** | Both panes paint with titles. “+ ~6 percentage points” annotation present (v12 residual resolved). PDF “Refresh” chip under spend bars still absent — minor chrome gap, not content loss. Retention y-window readable. **design-parity verified**. |
| 7 | `comparison_cards` | 6 | P7 | `side_by_side/slide_07.png` | **accepted v3 design divergence** | v13 paints circular dual-metric cards with 10x/2x multipliers (v12 was plain text columns). Values 50/5, 20/10, 21/11 present. Left/right premium-vs-benchmark orientation and card scale still differ from PDF art; no longer a missing-capability blank. |
| 8 | `single_chart` | 7 | P8 | `side_by_side/slide_08.png` | **faithful reproduction** | Dual lodging lines (FHR+THC 40→50%, UCS 5%) paint. Metric strip 3,400+ / 300+ / $600 / $550 present (v12 residual resolved). PDF vertical 10x callout between lines still absent — accepted chrome difference. **design-parity verified**. |
| 9 | `single_chart` | 8 | P9 | `side_by_side/slide_09.png` | **faithful reproduction** | Commercial FX-adj line paints. Support table with U.S. SME present (v12 residual resolved). **design-parity verified**. |
| 10 | `single_chart` | 9 | P10 | `side_by_side/slide_10.png` | **faithful reproduction** | ICS dual line paints with markers. Support table Intl Consumer present (v12 residual resolved). **design-parity verified**. |
| 11 | `single_chart` | 10 | P11 | `side_by_side/slide_11.png` | **faithful reproduction** | Series 9/9/10/9/10 on fixed 0–15% domain — v12 false-V domain collapse resolved. Leap Year box present on PDF only; line geometry now matches PDF frame. **design-parity verified**. |
| 12 | `chart_hero_dual` | 11 | P12 | `side_by_side/slide_12.png` | **faithful reproduction** | Three-band stacked NCA bars (UCS/Commercial/ICS totaling ~3.x) paint with segment legend (v12 single-series residual resolved). Hero 66%/73% shares present. Hero copy shorter than PDF long sentences — accepted v3 hero recipe. **design-parity verified**. |
| 13 | `single_chart` | 12 | P13 | `side_by_side/slide_13.png` | **faithful reproduction** | Grouped Total Balances vs Billed Business bars and labels match PDF structure/values through Q1'26. **design-parity verified**. |
| 14 | `dual_chart` | 13 | P14 | `side_by_side/slide_14.png` | **faithful reproduction** | 30+ DPD ~1.3% and Net Write-off panes paint with correct labels; dual-card chrome is v3 recipe. **design-parity verified**. |
| 15 | `single_chart` | 14 | P15 | `side_by_side/slide_15.png` | **corpus/extraction residual** | Stacked write-offs + reserve build/release geometry paints; Reserve Rate outlined row present (v12 furniture residual resolved). Remaining: mid-quarter reserve-rate cells show 2.8% for Q2–Q4 vs PDF 2.9%/2.9%/2.9%/2.9%/2.8%; series color recipe inverted vs PDF (write-offs dark vs light). **design-parity verified**. |
| 16 | `data_table` | 15 | P16 | `side_by_side/slide_16.png` | **accepted v3 design divergence** | All revenue line items and YoY/FX columns match. PDF pill columns vs v3 dense data grid is table recipe difference. |
| 17 | `dual_chart` | 16 | P17 | `side_by_side/slide_17.png` | **faithful reproduction** | Both panes paint. Left Net Card Fees bars correctly labeled $0.9…$2.8 (v12 pct_0 mislabel resolved). 17% CAGR measurement chrome present. Right FX YoY line matches. Qualification disclosure collapsed to notes affordance. **design-parity verified**. |
| 18 | `chart_hero_dual` | 17 | P18 | `side_by_side/slide_18.png` | **faithful reproduction** | NII bars $4.2…$4.7 with under-bar YoY boxed labels 11–12%. Driver card rows Billed Business 8% / NII 13% / Volume 7% / Margin 5% present (v12 residual resolved). Driver chrome is list not green-arrow table — accepted recipe. **design-parity verified**. |
| 19 | `single_chart` | 18 | P19 | `side_by_side/slide_19.png` | **faithful reproduction** | Dual revenue line paints. Leap Year annotation and $B support row $17.0…$18.9 present (v12 residual resolved). **design-parity verified**. |
| 20 | `period_comparison` | 19 | P20 | `side_by_side/slide_20.png` | **accepted v3 design divergence** | Expense values match incl. VCE. Nested indent flattened vs PDF hierarchy — recipe difference with matching numbers. |
| 21 | `chart_hero_dual` | 20 | P21 | `side_by_side/slide_21.png` | **faithful reproduction** | Capital stacked combo with Common Shares Outstanding line 702→682 and ROE row 35/34/36/36/34/35% present (v12 residual resolved). Right Capital Summary KPIs match. **design-parity verified**. |
| 22 | `metric_overview` | 21 | P22 | `side_by_side/slide_22.png` | **accepted v3 design divergence** | Guidance figures present; sparse list vs centered PDF card is metric_overview recipe. |
| 23 | `section_divider` | 22 | P23 | `side_by_side/slide_23.png` | **accepted v3 design divergence** | Appendix title; white plate vs navy brand divider — intentional v3 section_divider. |
| 24 | `single_chart` | 23 | P24 | `side_by_side/slide_24.png` | **faithful reproduction** | Six growth bars with category-group braces (UCS/Commercial/ICS), $486B Total Network Volumes annotation, and on-bar %-of-total boxed labels present (v12 residual resolved). **design-parity verified**. |
| 25 | `data_table` | 24 | P25 | `side_by_side/slide_25.png` | **faithful reproduction** | FX currency rows and YoY match PDF. |
| 26 | `data_table` | 25 | P26 | `side_by_side/slide_26.png` | **faithful reproduction** | T&E matrix orientation and values match PDF. |
| 27 | `dual_chart` | 26 | P27 | `side_by_side/slide_27.png` | **faithful reproduction** | Unemployment+GDP scenario fans paint-ready and track PDF. **design-parity verified**. |
| 28 | `dual_chart` | 27 | P28 | `side_by_side/slide_28.png` | **faithful reproduction** | Funding/deposit stacks paint with on-stack % and $ totals. 92% FDIC annotation present (v12 residual resolved). **design-parity verified**. |
| 29 | `narrative` | 28 | P29 | `side_by_side/slide_29.png` | **faithful reproduction** | Variance commentary matches PDF substance. |
| 30 | `narrative` | 29 | P30 | `side_by_side/slide_30.png` | **faithful reproduction** | Continuation commentary matches PDF substance. |
| 31 | `annex_table` | 30 | P31 | `side_by_side/slide_31.png` | **accepted v3 design divergence** | Annex1 values present; nested groups flattened to metric names vs PDF grouping chrome. |
| 32 | `grouped_annex_table` | 31 | P32 | `side_by_side/slide_32.png` | **faithful reproduction** | Two peer groups with correct numbers. Column headers fully readable (Q1'26 Reported / FX-Adj.*) — v12 header-clip residual resolved. |
| 33 | `annex_table` | 32 | P33 | `side_by_side/slide_33.png` | **faithful reproduction** | Annex2 balances grid matches. |
| 34 | `annex_table` | 33 | P34 | `side_by_side/slide_34.png` | **faithful reproduction** | Annex3 revenue grid populated. |
| 35 | `annex_table` | 34 | P35 | `side_by_side/slide_35.png` | **faithful reproduction** | Annex4 NCF grid populated. |
| 36 | `annex_table` | 35 | P36 | `side_by_side/slide_36.png` | **faithful reproduction** | Annex5 NII grid populated. |
| 37 | `annex_table` | 36 | P37 | `side_by_side/slide_37.png` | **faithful reproduction** | Annex6 RNIE grid populated. |
| 38 | `legal_notice` | 37 | P38 | `side_by_side/slide_38.png` | **candidate renderer defect or capability gap** | Full cautionary text present as dense continuous bullets; PDF multi-paragraph hierarchy/spacing largely collapsed. Same legal_notice packing class as v12 (R-D preserved). |
| 39 | `legal_notice` | 38 | P39 | `side_by_side/slide_39.png` | **candidate renderer defect or capability gap** | Continuation of legal packing class (dense wall vs PDF hierarchy). |
| 40 | `legal_notice` | 39 | P40 | `side_by_side/slide_40.png` | **candidate renderer defect or capability gap** | Same legal_notice packing class. |
| 41 | `legal_notice` | 40 | P41 | `side_by_side/slide_41.png` | **candidate renderer defect or capability gap** | Same legal_notice packing class. |
| 42 | `legal_notice` | 41 | P42 | `side_by_side/slide_42.png` | **candidate renderer defect or capability gap** | Same legal_notice packing class. |
| 43 | `legal_notice` | 42 | P43 | `side_by_side/slide_43.png` | **candidate renderer defect or capability gap** | Same legal_notice packing class. |
| 44 | `closing_cover` | 43 | P44 | `side_by_side/slide_44.png` | **accepted v3 design divergence** | PDF navy wordmark cover vs v3 minimal white lockup — accepted cover recipe. |

---

## 4. What renderer_v3 now does well

1. **Strict clean full-deck publish** of the 44-slide D314 corpus with zero non-info `run_meta` events.
2. **Identity-stable stacked deck** — 44 `data-slide-number` + matching `data-layout`; paint-ready + isolate capture yields 44 unique HTML digests.
3. **Chart.js paint-ready geometry** on every chart slide (including s12 stacked NCA and s27 scenario fans).
4. **DP-6 design floors held** — every chart slide measures tick computed style ≥20px/≥600; C1 furniture probes all green.
5. **Corpus furniture backfills landed visually** — Leap Year / support tables / metric strip / stacked NCA / reserve-rate row / $B+CAGR / YoY boxes+drivers / shares line+ROE / braces+$486B+%-boxes / FDIC callout all appear on SBS.
6. **Fixed domain on s11** — 0–15% frame restores PDF-like flat transaction-growth geometry.
7. **Dual-pane and hero compositions** mount with independent charts and metric/driver chrome.
8. **Annex grids and grouped peer tables** populate with readable headers (s32 clip fixed).
9. **comparison_cards** now emits circular dual-metric cards with multipliers (no longer a text-only board).

---

## 5. V12 → V13 delta

Source: extracted v12 gap analysis (`simulation/amex_q1_2026/extracted_baseline_v12_GAP_ANALYSIS.md` from git `3690942`) vs fresh v13 SBS + design ledger. Evidence cites v13 paths only.

### 5.1 Explicit C2 / C1 checks

| residual | v12 state | v13 state | evidence |
|----------|-----------|-----------|----------|
| **C2 typography collapse** (14px/400 vs 20px/600) | every chart slide measured small/light ticks | **RESOLVED** — all chart slides min 20px / 600 | design ledger rows s4–6,8–15,17–19,21,24,27–28; `comparison_manifest.json` |
| **C1 furniture s4** Leap Year + G&S table | missing | **RESOLVED** | SBS `side_by_side/slide_04.png`; furniture ok |
| **C1 furniture s5** Gen-Z support | missing | **RESOLVED** | SBS s05; furniture ok |
| **C1 furniture s6** +6pp elbow | missing | **RESOLVED** | SBS s06; furniture ok |
| **C1 furniture s8** 3,400+ KPI strip | missing | **RESOLVED** | SBS s08; furniture ok |
| **C1 furniture s9** U.S. SME support | missing | **RESOLVED** | SBS s09; furniture ok |
| **C1 furniture s10** Intl Consumer support | missing | **RESOLVED** | SBS s10; furniture ok |
| **C1 furniture s12** 3-band NCA stack | single-series 1.5 bars | **RESOLVED** stacked ~3.x | SBS s12; stacked_bar furniture ok |
| **C1 furniture s15** reserve-rate row | missing | **RESOLVED** (values partially diverge — see residual) | SBS s15; outlined-support ok |
| **C1 furniture s17** $B + CAGR | pct_0 mislabel; no CAGR | **RESOLVED** $0.9…$2.8 + 17% rule | SBS s17; cagr furniture ok |
| **C1 furniture s18** YoY boxes + drivers | missing / wrong format | **RESOLVED** | SBS s18; boxed-label + driver_card ok |
| **C1 furniture s19** Leap Year + $B row | missing | **RESOLVED** | SBS s19; furniture ok |
| **C1 furniture s21** shares line + ROE | missing / constant 35% | **RESOLVED** 702→682 + varying ROE | SBS s21; furniture ok |
| **C1 furniture s24** braces + $486B + %-boxes | missing | **RESOLVED** | SBS s24; furniture ok |
| **C1 furniture s28** FDIC + stack totals | missing | **RESOLVED** | SBS s28; furniture ok |

### 5.2 Per v12 residual ID

| v12 ID | where | v13 disposition | notes |
|--------|-------|-----------------|-------|
| R-A | s11 domain | **RESOLVED** | Fixed 0–15 domain; line nearly flat like PDF |
| R-B | s7 comparison_cards | **REPLACED** with accepted divergence | Circles+multipliers now paint; orientation/scale still ≠ PDF art |
| R-C | s32 header clip | **RESOLVED** | Headers fully readable |
| R-D | s38–43 legal packing | **PRESERVED** | Dense bullet wall vs PDF hierarchy |
| C-A | s12 stack | **RESOLVED** | Three-band stack present |
| C-B | s17 format/CAGR | **RESOLVED** | $ labels + CAGR chrome |
| C-C | s18 format/drivers/YoY | **RESOLVED** | $ NII + boxes + driver rows |
| C-D | s4/5/9/10/19 callouts+tables | **RESOLVED** | Furniture green |
| C-E | s5/8/9/10 side KPIs | **RESOLVED** (via support/metric furniture) | s8 strip present |
| C-F | s8 KPI stack | **RESOLVED** | metric-strip green |
| C-G | s15 reserve-rate | **PARTIALLY RESOLVED** | Row present; Q2–Q4 values 2.8% vs PDF 2.9% |
| C-H | s21 shares+ROE | **RESOLVED** | Line + varying ROE |
| C-I | s24 braces/$486B/% | **RESOLVED** | All three furniture classes green |
| C-J | s28 FDIC+totals | **RESOLVED** | Annotation + stack labels |
| C-K | s6 +6pp | **RESOLVED** | Annotation present; Refresh chip still absent (minor) |
| A-1..A-3 | covers / recipe chrome | **PRESERVED** accepted divergences | Unchanged class |

---

## 6. Residual triage

Only items with **fresh v13 SBS + design-ledger / corpus evidence**. No fixes designed; no tickets filed.

### 6.1 Candidate renderer_v3 defect / capability gap

| ID | where | impact | likely ownership | smallest next verification |
|----|-------|--------|------------------|----------------------------|
| R-D | s38–43 `legal_notice` | Continuous dense text loses PDF multi-paragraph hierarchy and spacing | legal_notice block packing / list emission | Diff payload list structure vs painted DOM list nodes; check whether paragraph breaks exist in schema but flatten in publish |
| R-E (soft) | s7 `comparison_cards` | Circles present but premium/benchmark left-right order and card scale still diverge from PDF | comparison_cards layout recipe | Measure circle diameter and column order vs PDF; classify whether further recipe work is wanted (currently accepted divergence, not defect) |

### 6.2 Corpus / extraction / content residual

| ID | where | impact | likely ownership | smallest next verification |
|----|-------|--------|------------------|----------------------------|
| C-G′ | s15 reserve-rate cells | Q2–Q4 show 2.8% vs PDF 2.9%; Q1 and Q1'26 match | corpus outlined_support values (furniture DOM present) | Diff payload reserve-rate series vs PDF cells on SBS s15 |
| C-color | s15 series colors | Write-offs dark navy vs PDF light blue; reserve band inverted visual weight | theme/series color authorship | Compare series color tokens in corpus vs PDF swatches (observation only) |
| C-chip | s6 Refresh chip | PDF “Refresh” under-bar chip absent | corpus annotation/chrome not in DESIGN_LEDGER_FURNITURE | Confirm whether a chip object exists in schema for s6; visual-only residual |
| C-10x | s8 10x vertical callout | PDF double-arrow 10x between lines absent (KPI strip present) | corpus annotation optional | Visual-only; metric values already on strip |

### 6.3 Source/PDF artifact or accepted divergence

| ID | where | notes |
|----|-------|-------|
| A-1 | s1, s23, s44 | Brand seal / full-bleed navy covers — R3 wontfix + v3 minimal cover recipe |
| A-2 | s3, s16, s20, s22, s31 | Pill/board PDF furniture vs v3 matrix/metric/annex recipes with matching numbers |
| A-3 | dual_chart / hero card chrome | Navy pane headers, legends, list-style drivers — intentional v3 skin |
| A-4 | s7 card art | Circles present; remaining orientation/scale differences accepted |

### 6.4 Screenshot / probe / design-ledger failures

**None.** `capture_errors=[]`, `console_errors=[]`, `missing_or_bad_size=[]`, `design_ledger_fail_slides=[]`, 44 unique HTML digests, 44/44 design ledgers ok.

---

## 7. Diagnostics & artifact index

| artifact | path |
|----------|------|
| Strict render out | `simulation/amex_q1_2026/passes/pass_01/renderer_v3_out/` |
| `run_meta.json` | `…/run_meta.json` (status=clean) |
| `presentation.html` | `…/presentation.html` |
| PDF pages 01–44 | `simulation/amex_q1_2026/pdf_pages/slide_XX.png` |
| HTML slides 01–44 | `simulation/amex_q1_2026/html_slides/slide_XX.png` |
| SBS 01–44 | `simulation/amex_q1_2026/side_by_side/slide_XX.png` |
| Contact sheet | `simulation/amex_q1_2026/contact_sheet.png` |
| Manifest (incl. design ledgers) | `simulation/amex_q1_2026/comparison_manifest.json` |
| Capture log | `simulation/amex_q1_2026/capture_log.json` |
| Ledger JSON | `simulation/amex_q1_2026/qualitative_ledger_v13.json` |
| Build scripts (sim-only) | `simulation/amex_q1_2026/build_v13_comparison.py`, `build_v13_ledger.py` |
| Extracted v12 text | `simulation/amex_q1_2026/extracted_baseline_v12_GAP_ANALYSIS.md` |
| Wiki report (byte copy) | `wiki/baseline_v13_GAP_ANALYSIS.md` |

---

## 8. Stop proofs

| proof | result |
|-------|--------|
| Strict render exit 0 clean | **PASS** |
| 44 PDF @ 1920×1080 | **PASS** (`comparison_manifest.pdf_pages`) |
| 44 HTML @ 1920×1080 | **PASS** |
| 44 SBS @ 3840×1080 | **PASS** |
| Identity 1…44 + layout match | **PASS** |
| Design-ledger row per slide | **PASS** (44/44 ok) |
| C2 ticks ≥20px/≥600 | **PASS** |
| C1 furniture 4/5/6/8/9/10/12/15/17/18/19/21/24/28 | **PASS** |
| No MAE/similarity/pixel scores | **PASS** (qualitative ledger only) |
| No production/test/script/config edits | **PASS** (sim + wiki report only) |
| Report byte-identical to wiki copy | enforced at docs commit |
| Exactly two commits (artifacts, then docs) | enforced at closeout |

---

*End of v13 observation baseline. Companion-mode only — no renderer fixes, no corpus edits, no tickets.*
