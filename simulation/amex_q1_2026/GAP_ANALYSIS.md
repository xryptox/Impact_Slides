# Gap Analysis v16: renderer_v3 vs Amex Q1'26 Earnings PDF **(Complete 44-page PDF↔HTML observation with DP-6 + #249/#256/#269 design ledger — Companion-mode SIMULATION only)**

**Simulation:** `simulation/amex_q1_2026/`
**Source of truth:** `C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf`
**PDF identity:** SHA-256 `a87c11625c84e0dabb02d523f6a2d2508b892f18ee242ef197a9b40157bd3faf` · 44 pages · page0 rect 959.76×540.0
**Renderer under test:** `impact_slides.renderer_v3` **3.0.0** @ `9c2acd1683ccc8fe047213f01f0726596d62c909`
**Canonical input (read-only; no mutations):** `tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json`
**Handoff SHA-256:** `17141456a5bd2c9ce395a90c6c011782738581c9c84b77abb03ab0fb92ef018f`
**Prior baseline:** v15 report via `git show 0f67fb3:wiki/baseline_v15_GAP_ANALYSIS.md` (never merged to main; renderer @ `837413f`, handoff `2dbec2af…`)
**Method:** One strict `python -m impact_slides.renderer_v3` publish → Playwright capture via `scripts/simulation_probe.wait_for_paint_ready_charts` + `measured_tick_styles` + `furniture_presence` (DP-6) + #249/#256/#269 extensions (`measured_stub_ratio`, `measured_support_chrome` on remaining category-aligned hide_header fixtures — Amex s4/s19 **not** in that map, `measured_series_palette`, `measured_metric_value_styles`, `measured_bar_occupancy`) + section isolate (lesson 32) → PyMuPDF 1920×1080 PDF rasters → full-resolution SBS. **No MAE / similarity % / pixel-diff scores / heatmaps.** This run re-validates the deck after the post-v15 ticket set: **#268** s12 PDF hero KPI sentences, **#269** s4/s19 independent navy-header support tables, **#270** unmarked legal continuations as `<p>`, **#271** s18 folded Volume/Margin driver labels, **#272** s15 reserve navy + uncollide stack totals, **#273** hero/`metric_overview` body 27px + wrapping KPI labels, **#274** independent support-table thead stub navy.

---

## 1. Scope gate, mapping assertion, run identity

| Gate | Result |
|------|--------|
| Renderer commit | `9c2acd1683ccc8fe047213f01f0726596d62c909` |
| Renderer version | `3.0.0` |
| Production paths touched | **None** (only `simulation/amex_q1_2026/**` + final `wiki/baseline_v16_GAP_ANALYSIS.md`) |
| Handoff | Committed D314 corpus only — **no** `amex_handoff_mutations.py`, no hand edits |
| Handoff delta vs v15 | `2dbec2af…` → `17141456…` (post-v15 #268–#274 corpus updates already in fixture) |
| Render command | `python -m impact_slides.renderer_v3 --handoff tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json --out simulation/amex_q1_2026/passes/pass_01/renderer_v3_out` |
| Render outcome | **strict exit 0**, `run_meta.status=clean`, `ok=true`, `options.strict=true` |
| `run_meta` events | 67 × `info` · **0** warn/error |
| PDF pages | 44 |
| HTML `data-slide-number` | 44 unique values **1…44** |
| HTML `data-layout` vs corpus `layout_type` | **44/44 match** |
| Identity map | **HTML slide N → PDF index N−1 → physical page N** |
| Capture contract | viewport **1920×1080**, `deviceScaleFactor=1` (fit scale 1); isolate target `section.slide` (siblings `display:none`, stage/slide transform none); element screenshot; `wait_for_paint_ready_charts` before every chart-slide shot; DP-6 ticks/furniture + #249/#256/#269 extensions after paint-ready; **no** `painted_datalabel_lines`; no nth selectors; no fixed sleeps |
| Comparison artifacts | 44 PDF + 44 HTML + 44 SBS @ exact 1920×1080 halves (SBS 3840×1080); contact sheet; `comparison_manifest.json` `missing_or_bad_size=[]` |
| Design ledger | **44/44 rows** in manifest; **44/44 overall ok** (`DESIGN_LEDGER_SUPPORT_CHROME_SLIDES` empty — s4/s19 not probed as hide_header) |
| HTML PNG uniqueness | **44 distinct SHA-256** |
| Console errors | `[]` |
| Image scoring | **forbidden / absent** |
| Scope-gate | **PASS** |

### Published artifact hashes (`passes/pass_01/renderer_v3_out/`)

| File | SHA-256 |
|------|---------|
| `presentation.html` | `16fa454b3bbde3c139bd1e92b5fa8d23ce6173bcefb9216fc772d480145bf9e6` |
| `run_meta.json` | `3bf113e67b7dfda7158fb67b9db4f34388bc986483deac6b7be439c8c0ab23b9` |
| `evidence_manifest.json` | `6b8c217a8b2384a4d09c7b24d2b52b3d5472d3761867ef8d0b3cc0af0244e3c5` |
| `handoff_schema_v1.json` | `cee2cb3c654562d841396554cff245650f5123205c01db5e4289dcd560e682b5` |
| `slide_notes.md` | `78823a5fba725aa5deb5961399a066b9a6935af1cf724bc851f2a8b079b4ae8e` |

### Capture contract detail

- Deck is a stacked scroll of all 44 `section.slide` nodes inside `.deck-stage` (no `.active` hide rule; resize-fit scales by `min(innerWidth/1920, innerHeight/1080)`).
- Capture forces transform/scale identity and screenshots the section node after paint-ready settle.
- Chart slides with paint-ready geometry (nonzero canvas, non-degenerate `chartArea`, painted dataset elements across one rAF): **4–6, 8–15, 17–19, 21, 24, 27–28**.
- Primary surface is JS-on Chart.js (SVG noscript fallback not used for comparison).
- DP-6 tick measurement uses **computed style** on overlay tick `<text>` (not presentation attributes alone). Furniture uses `DESIGN_LEDGER_FURNITURE` selectors + expected_text; zero matches = failure.
- #249/#256/#269 extensions run only on their mapped slides (see §2.2); a `ProbeError` is recorded as failure — never invented green. `DESIGN_LEDGER_SUPPORT_CHROME_SLIDES` is the empty tuple: Amex s4/s19 are independent navy-header tables per #269.

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

---

## 2. DP-6 design ledger (+ #249/#256/#269 extensions)

Machine-readable twin: `comparison_manifest.json` → `design_ledgers[]` (44 rows). Builder: `build_v16_comparison.py`.

### 2.1 Summary

| Metric | Result |
|--------|--------|
| Design-ledger rows | **44/44** |
| Overall `ok` | **44/44** |
| Chart-slide tick floors (≥20px, weight ≥600, ≥1 tick) | **all chart slides green** |
| Furniture (`DESIGN_LEDGER_FURNITURE`) | **all expected rows green** |
| #246 stub_ratio (≤0.45) | s3/s16/s31–37 **all green** (max shares ≈0.450 / 0.449 / 0.344) |
| #246 bar_occupancy (≥0.5) | s28 **0.55 / 0.55** green |
| #248 metric_floor (≥40px) | s8 **44px**, s12 **72px** green |
| #248 palette | s24 navy-only (no sky required); s28 sky `#80C8FF` present; **no** `#0A7D55` series |
| #256/#269 support_chrome | **not probed** on Amex s4/s19 (`DESIGN_LEDGER_SUPPORT_CHROME_SLIDES` empty). Independent navy-header tables paint (`band-table-header` period columns + thead stub navy). Tick/furniture rows on s4/s19 still green. |

### 2.2 Chart-slide tick + furniture detail

| slide | layout | ticks | min_fs_px | min_weight | furniture ok | extensions | overall |
|------:|--------|------:|----------:|-----------:|:------------:|------------|:-------:|
| 4 | single_chart | 9 | 20 | 600 | 2/2 | — | ok |
| 5 | single_chart | 9 | 20 | 600 | 4/4 | — | ok |
| 6 | dual_chart | 18 | 20 | 600 | 2/2 | — | ok |
| 8 | single_chart | 10 | 20 | 600 | 2/2 | metric_floor | ok |
| 9 | single_chart | 9 | 20 | 600 | 4/4 | — | ok |
| 10 | single_chart | 11 | 20 | 600 | 4/4 | — | ok |
| 11 | single_chart | 9 | 20 | 600 | 1/1 | — | ok |
| 12 | chart_hero_dual | 10 | 20 | 600 | 1/1 | metric_floor | ok |
| 13 | single_chart | 10 | 20 | 600 | 0/0 | — | ok |
| 14 | dual_chart | 20 | 20 | 600 | 0/0 | — | ok |
| 15 | single_chart | 11 | 20 | 600 | 1/1 | — | ok |
| 17 | dual_chart | 28 | 20 | 600 | 1/1 | — | ok |
| 18 | chart_hero_dual | 9 | 20 | 600 | 2/2 | — | ok |
| 19 | single_chart | 9 | 20 | 600 | 2/2 | — | ok |
| 21 | chart_hero_dual | 16 | 20 | 600 | 2/2 | — | ok |
| 24 | single_chart | 11 | 20 | 600 | 3/3 | palette | ok |
| 27 | dual_chart | 36 | 20 | 600 | 0/0 | — | ok |
| 28 | dual_chart | 16 | 20 | 600 | 1/1 | palette, bar_occupancy | ok |

Non-chart slides without extension targets record `design_ledger: {ok: true, ticks: null, furniture: []}`. Extension-only non-charts (stub tables on s3/s16/s31–37) are overall ok via stub_ratio.

### 2.3 #249 / #256 / #269 extension detail

#### #246 stub-slack cap (`measured_stub_ratio`, share ≤ 0.45)

| slide | max_stub_share | ok |
|------:|---------------:|:--:|
| 3 | 0.450 | yes |
| 16 | 0.449 | yes |
| 31 | 0.449 | yes |
| 32 | 0.449 | yes |
| 33 | 0.449 | yes |
| 34 | 0.449 | yes |
| 35 | 0.344 | yes |
| 36 | 0.449 | yes |
| 37 | 0.449 | yes |

#### #246 bar occupancy (`measured_bar_occupancy`, bar width / category pitch ≥ 0.5)

| slide | canvas ratios | ok |
|------:|---------------|:--:|
| 28 | 0.55, 0.55 | yes |

#### #248 KPI metric floor (`measured_metric_value_styles`, ≥ 40px)

| slide | min_font_size_px | value_count | ok |
|------:|-----------------:|------------:|:--:|
| 8 | 44 | 4 | yes |
| 12 | 72 | 2 | yes |

#### #248 series palette (`measured_series_palette`)

| slide | colors | has_sky_blue | require_sky | ok |
|------:|--------|:------------:|:-----------:|:--:|
| 24 | `#00175A` | no | no | yes |
| 28 | `#00175A`, `#006FCF`, `#63666A`, `#80C8FF` | yes | yes | yes |

#### #269 support chrome (`measured_support_chrome`) — **not targeted**

`DESIGN_LEDGER_SUPPORT_CHROME_SLIDES` is empty. Amex s4/s19 paint independent navy-header `support-table`s (`<thead>` `band-table-header` period columns visible; thead stub `Metric` stays on the navy band; tbody stubs transparent). Do **not** expect hide_header / `.support-cat-cell.head` chrome on those slides. Tick + furniture rows remain green (`Leap Year` + `G&S` on s4; `Leap Year` + `$17.0` on s19).

---

## 3. Full 44-page qualitative ledger

Classification is exactly one of:
`faithful reproduction` · `accepted v3 design divergence` · `candidate renderer defect or capability gap` · `corpus/extraction residual` · `source/PDF artifact` · `capture failure`.

SBS paths are relative to `simulation/amex_q1_2026/`. Machine-readable twin: `comparison_manifest.json` (identity + design_ledgers).

**Class counts:** faithful **29** · accepted divergence **15** · corpus residual **0** · candidate defect **0** · capture failure **0**.

(v15 table was faithful 29 / accepted 9 / candidate 6. Net: s38–43 leave the R-D packing six-pack and become accepted leftover air/type after #270 paints unmarked bodies as `<p>`; cover/recipe accepted set otherwise stable; s4/s19 stay faithful with #269 navy-header tables replacing the v15 A-247 hide-header acceptance.)

| # | layout_type | pdf_idx | page | SBS | class | observation (qualitative; no scores) |
|--:|-------------|--------:|-----:|-----|-------|--------------------------------------|
| 1 | `opening_cover` | 0 | P1 | `side_by_side/slide_01.png` | **accepted v3 design divergence** | PDF full-bleed navy/cyan brand cover with Centurion seal. v3 minimal white title (title + Q1'26 + April 23, 2026). Brand-seal omission is standing R3 wontfix; cover recipe intentional. |
| 2 | `narrative` | 1 | P2 | `side_by_side/slide_02.png` | **faithful reproduction** | Seven Business Highlights bullets match PDF substance and bold emphasis. Packing tighter/smaller type than PDF; footnote collapses to notes affordance. Content-complete. |
| 3 | `period_comparison` | 2 | P3 | `side_by_side/slide_03.png` | **accepted v3 design divergence** | All five KPI rows/values match. PDF uses large period pills; v3 compact right-hand matrix — schema-v1 period_comparison recipe. **#246 stub share 0.450 ≤ 0.45**. |
| 4 | `single_chart` | 3 | P4 | `side_by_side/slide_04.png` | **faithful reproduction** | **#255 held:** dashed upper **Reported**; solid navy **FX-adjusted** ends at **9%** (Reported **10%**). Authored y-ticks **0/5/10/15**. Leap Year + G&S/T&E facts. **#269:** independent navy-header support table — `band-table-header` period columns **Q1'25…Q1'26** visible (not hide_header). **#274:** thead stub **Metric** stays on the navy band; tbody G&S/T&E stubs transparent. **design-parity verified**. |
| 5 | `single_chart` | 4 | P5 | `side_by_side/slide_05.png` | **faithful reproduction** | UCS billings line paints. Authored ticks 0/5/10/15. Leap Year + G&S/T&E facts present (#255). Generation-mix support table present. **design-parity verified**. |
| 6 | `dual_chart` | 5 | P6 | `side_by_side/slide_06.png` | **faithful reproduction** | Both panes paint. “+ ~6 percentage points” and **Refresh** annotations present. **#259 held:** right pane **Anniversary Month** + retention-rate value-axis title; left pane prior-year subtitle. **design-parity verified**. |
| 7 | `comparison_cards` | 6 | P7 | `side_by_side/slide_07.png` | **accepted v3 design divergence** | Circular dual-metric cards with multipliers. Values present. Card scale/orientation still differ from PDF art. |
| 8 | `single_chart` | 7 | P8 | `side_by_side/slide_08.png` | **faithful reproduction** | Dual lodging lines paint. **#255 held:** FHR+THC steps. Metric strip at **44px** (#248 floor). **10x** annotation present. **design-parity verified**. |
| 9 | `single_chart` | 8 | P9 | `side_by_side/slide_09.png` | **faithful reproduction** | Commercial FX-adj line paints. Authored ticks 0/5/10/15. Leap Year + G&S/T&E facts. **#274:** independent support-table thead stub **Q1'26** keeps the navy band; tbody YoY / % of Total stubs transparent. U.S. SME columns present. **design-parity verified**. |
| 10 | `single_chart` | 9 | P10 | `side_by_side/slide_10.png` | **faithful reproduction** | ICS dual line paints. Authored ticks **0/5/10/15/20/25**. Leap Year + G&S/T&E facts. **#274:** thead stub **Q1'26** navy; Intl Consumer support present. **design-parity verified**. |
| 11 | `single_chart` | 10 | P11 | `side_by_side/slide_11.png` | **faithful reproduction** | Series on fixed 0–15% domain with authored ticks 0/5/10/15. Leap Year annotation present. Line geometry PDF-like. **design-parity verified**. |
| 12 | `chart_hero_dual` | 11 | P12 | `side_by_side/slide_12.png` | **faithful reproduction** | Three-band stacked NCA bars paint. **#260 held:** on-stack segment labels. **#268:** hero KPI labels are the PDF sentences **“Global Consumer New Accounts Acquired from Millennial / Gen-Z”** (66%) and **“Global New Accounts Acquired on Fee-Paying Products*”** (73%); short share labels gone. **#273:** `data-plan-sizes="body:27,heading:32,value:72"`; labels wrap at **27px**; values **72px**. **design-parity verified**. |
| 13 | `single_chart` | 12 | P13 | `side_by_side/slide_13.png` | **faithful reproduction** | Grouped Total Balances vs Billed Business bars/labels match structure through Q1'26. **design-parity verified**. |
| 14 | `dual_chart` | 13 | P14 | `side_by_side/slide_14.png` | **faithful reproduction** | 30+ DPD and Net Write-off panes paint with correct labels; dual-card chrome is v3 recipe. **design-parity verified**. |
| 15 | `single_chart` | 14 | P15 | `side_by_side/slide_15.png` | **faithful reproduction** | **#272:** Reserve Build/(Release) paints **navy** (`#00175a`); write-offs stay **primary_blue** (`#006fcf`); two series only (no third). Stack totals **$1,405 / $1,287 / $1,414** sit above Q2'25–Q4'25 navy caps and do not collide with category labels. Reserve Rate row 2.9%/2.8% matches PDF. v15 color-invert note **closed**. **design-parity verified**. |
| 16 | `data_table` | 15 | P16 | `side_by_side/slide_16.png` | **accepted v3 design divergence** | All revenue line items and YoY/FX columns match. PDF pill columns vs v3 dense data grid. **#246 stub share 0.449**. |
| 17 | `dual_chart` | 16 | P17 | `side_by_side/slide_17.png` | **faithful reproduction** | **#258 held:** dated pane headings + slide subtitle; `pane_title` series identity. Net Card Fees $ labels + 17% CAGR chrome; FX YoY line matches. **design-parity verified**. |
| 18 | `chart_hero_dual` | 17 | P18 | `side_by_side/slide_18.png` | **faithful reproduction** | NII bars with YoY boxed labels. **#271:** Volume/Margin folded into one driver label each — **“Volume - Total Balances”** (7%) and **“Margin - Net Interest Income / Average Total Balances”** (5%); **zero** leftover `driver-detail` spans. **#273:** driver labels **27px**, values **72px**, heading **32px**. **design-parity verified**. |
| 19 | `single_chart` | 18 | P19 | `side_by_side/slide_19.png` | **faithful reproduction** | **#255 held:** dashed **Reported**; navy FX-adj ends at **10%**. Authored ticks 0/5/10/15. Leap Year + $B support $17.0…$18.9. **#269:** independent navy-header support table (period columns visible). **#274:** thead stub **Metric** navy; tbody `$B` stub transparent. **design-parity verified**. |
| 20 | `period_comparison` | 19 | P20 | `side_by_side/slide_20.png` | **accepted v3 design divergence** | Expense values match incl. VCE. Nested indent flattened vs PDF hierarchy. |
| 21 | `chart_hero_dual` | 20 | P21 | `side_by_side/slide_21.png` | **faithful reproduction** | Capital stacked combo with shares line 702→682 and varying ROE; Capital Summary KPIs match. **#260 held:** on-stack segment $ labels. **design-parity verified**. |
| 22 | `metric_overview` | 21 | P22 | `side_by_side/slide_22.png` | **accepted v3 design divergence** | Guidance figures present (9%–10% / $17.30–$17.90). **#273:** `data-plan-sizes="body:27,heading:32,value:72"` — body labels 27px, values 72px. Sparse list vs centered PDF card remains the metric_overview recipe. |
| 23 | `section_divider` | 22 | P23 | `side_by_side/slide_23.png` | **accepted v3 design divergence** | Appendix title; white plate vs navy brand divider — intentional v3 section_divider. |
| 24 | `single_chart` | 23 | P24 | `side_by_side/slide_24.png` | **faithful reproduction** | **#254 held:** Commercial + ICS groups **above** the bars; **no UCS** singleton; outlined %-of-total under the plot; $486B annotation; navy-only palette. **design-parity verified**. |
| 25 | `data_table` | 24 | P25 | `side_by_side/slide_25.png` | **faithful reproduction** | FX currency rows and YoY match PDF. |
| 26 | `data_table` | 25 | P26 | `side_by_side/slide_26.png` | **faithful reproduction** | T&E matrix orientation and values match PDF. |
| 27 | `dual_chart` | 26 | P27 | `side_by_side/slide_27.png` | **faithful reproduction** | Unemployment+GDP scenario fans paint-ready and track PDF. **design-parity verified**. |
| 28 | `dual_chart` | 27 | P28 | `side_by_side/slide_28.png` | **faithful reproduction** | Funding/deposit stacks paint with on-stack % and $ totals. 92% FDIC annotation present. **#248** sky-blue series active; **#246** bar occupancy 0.55. **design-parity verified**. |
| 29 | `narrative` | 28 | P29 | `side_by_side/slide_29.png` | **faithful reproduction** | Variance commentary matches PDF substance. |
| 30 | `narrative` | 29 | P30 | `side_by_side/slide_30.png` | **faithful reproduction** | Continuation commentary matches PDF substance. |
| 31 | `annex_table` | 30 | P31 | `side_by_side/slide_31.png` | **accepted v3 design divergence** | Annex1 values present; nested groups flattened. **#246 stub share 0.449**. |
| 32 | `grouped_annex_table` | 31 | P32 | `side_by_side/slide_32.png` | **faithful reproduction** | Two peer groups with correct numbers; headers fully readable. **#246 stub share 0.449**. |
| 33 | `annex_table` | 32 | P33 | `side_by_side/slide_33.png` | **faithful reproduction** | Annex2 balances grid matches. **#246 stub ok**. |
| 34 | `annex_table` | 33 | P34 | `side_by_side/slide_34.png` | **faithful reproduction** | Annex3 revenue grid populated. **#246 stub ok**. |
| 35 | `annex_table` | 34 | P35 | `side_by_side/slide_35.png` | **faithful reproduction** | Annex4 NCF grid populated. **#246 stub 0.344**. |
| 36 | `annex_table` | 35 | P36 | `side_by_side/slide_36.png` | **faithful reproduction** | Annex5 NII grid populated. **#246 stub ok**. |
| 37 | `annex_table` | 36 | P37 | `side_by_side/slide_37.png` | **faithful reproduction** | Annex6 RNIE grid populated. **#246 stub ok**. |
| 38 | `legal_notice` | 37 | P38 | `side_by_side/slide_38.png` | **accepted v3 design divergence** | **#257 held:** part-1 title (no “— continued”); **56px / 21px**. **#255 held:** forward-looking preamble. **#270:** preamble paints as **one `<p>`** + **two marked `<ul>`** (2 `<li>`). Markup matches the marked-list contract. Leftover vs PDF is air/type (tighter packing of the two long bullets), not unmarked-as-list. |
| 39 | `legal_notice` | 38 | P39 | `side_by_side/slide_39.png` | **accepted v3 design divergence** | **#270:** unmarked-only body paints as **`<p>`** — **4 `<p>`, 0 `<ul>`/`<li>`** (3 risk paragraphs + Part 2 of 6). Repeating part-1 title + 56/21 held. PDF still uses bullets; HTML paragraphs are the authored unmarked continuation. Leftover is air/type. |
| 40 | `legal_notice` | 39 | P40 | `side_by_side/slide_40.png` | **accepted v3 design divergence** | Unmarked body as **`<p>`** (**4 `<p>`, 0 `<ul>`/`<li>`**). Title repeat + 56/21 held. Leftover air/type vs PDF bullets. |
| 41 | `legal_notice` | 40 | P41 | `side_by_side/slide_41.png` | **accepted v3 design divergence** | Unmarked body as **`<p>`** (**5 `<p>`, 0 `<ul>`/`<li>`**). Title repeat + 56/21 held. Leftover air/type vs PDF bullets. |
| 42 | `legal_notice` | 41 | P42 | `side_by_side/slide_42.png` | **accepted v3 design divergence** | Unmarked body as **`<p>`** (**4 `<p>`, 0 `<ul>`/`<li>`**). Title repeat + 56/21 held. Leftover air/type vs PDF bullets. |
| 43 | `legal_notice` | 42 | P43 | `side_by_side/slide_43.png` | **accepted v3 design divergence** | Unmarked body as **`<p>`** (**5 `<p>`, 0 `<ul>`/`<li>`**). Title repeat + 56/21 held. Leftover air/type vs PDF bullets. |
| 44 | `closing_cover` | 43 | P44 | `side_by_side/slide_44.png` | **accepted v3 design divergence** | PDF navy wordmark cover vs v3 minimal white lockup — accepted cover recipe. |

---

## 4. What renderer_v3 now does well

1. **Strict clean full-deck publish** of the 44-slide D314 corpus (`run_meta.status=clean`, 67 info / 0 warn-error).
2. **Identity-stable stacked deck** — 44 `data-slide-number` + matching `data-layout`; paint-ready + isolate capture yields 44 unique HTML digests at exact 1920×1080.
3. **Chart.js paint-ready geometry** on every chart slide (including s12 stacked NCA and s27 scenario fans).
4. **DP-6 design floors held** — every chart slide measures tick computed style ≥20px/≥600; C1 furniture probes all green.
5. **Full design-ledger green (44/44)** — s4/s19 no longer hide_header chrome targets; independent navy-header tables + tick/furniture rows green.
6. **#246 stub-slack + sparse bar occupancy held** on mapped slides.
7. **#248 KPI metric floor + palette activation held** (s8 44px / s12 72px; s28 sky present; no green-cycle series on palette targets).
8. **Post-v15 ticket surfaces land on corpus + paint:**
   - **#268** s12 hero KPI labels are the PDF sentences (66% / 73%); short share labels gone.
   - **#269** s4/s19 independent navy-header support tables with visible period columns.
   - **#270** s38 preamble `<p>` + two marked `<ul>`s; s39–43 unmarked bodies as `<p>` (zero lists).
   - **#271** s18 Volume/Margin folded into one driver label each; no leftover detail spans.
   - **#272** s15 reserve navy / write-offs primary_blue; stack totals clear of Q2'25–Q4'25 category labels; two series only.
   - **#273** hero/`metric_overview` body 27px with wrapping KPI labels; heading 32 / value 72 held (metric strip 44 held on s8).
   - **#274** independent support-table thead stubs (s4/s9/s10/s19) stay on the navy band; tbody stubs transparent.
9. **Dual-pane / hero / annex compositions** continue to mount with independent charts and metric/driver chrome.

---

## 5. V15 → V16 delta

Prior: `git show 0f67fb3:wiki/baseline_v15_GAP_ANALYSIS.md` (renderer `837413f`, handoff `2dbec2af…`, design ledger 44/44 ok with s4/s19 classified under #256 hide_header).

### 5.1 Explicit post-v15 ticket surfaces (#268–#274)

| residual / ticket surface | v15 state | v16 state | evidence |
|---------------------------|-----------|-----------|----------|
| **#268 s12** hero KPI sentences | Faithful NCA stack; hero copy **shorter than PDF long sentences** (accepted recipe note) | **RESOLVED:** labels are **“Global Consumer New Accounts Acquired from Millennial / Gen-Z”** (66%) and **“Global New Accounts Acquired on Fee-Paying Products*”** (73%); short share labels gone | SBS `slide_12.png`; DOM `.metric-label` at 27px with those sentences; values 72px |
| **#269 s4/s19** independent navy-header tables | **A-247-hide-header accepted** — `head_count=0`, body hairline only; no PDF navy period band | **RESOLVED / FLIPS A-247:** `support-table` thead `band-table-header` period columns visible (Q1'25…Q1'26); not hide_header; `DESIGN_LEDGER_SUPPORT_CHROME_SLIDES` empty so hide_header chrome is **not** expected | SBS `slide_04.png` / `slide_19.png`; DOM thead `band-table-header` × period cols; `hide_header` count 0; `.support-cat-cell` count 0 |
| **#270 s38–43** unmarked legal as `<p>` | **R-D candidate defect** — dense continuous risk **lists** vs PDF multi-paragraph hierarchy | **RESOLVED markup / FLIPS R-D:** s38 = preamble `<p>` + **2 marked `<ul>`**; s39–43 = **N `<p>`, 0 `<ul>`/`<li>`**. Remainder shrinks to leftover air/type vs PDF bullets | DOM p/ul/li counts; SBS `slide_38.png`…`slide_43.png` |
| **#271 s18** folded Volume/Margin labels | Faithful NII + driver card rows (detail spans not called out as closed) | **RESOLVED:** **“Volume - Total Balances”**, **“Margin - Net Interest Income / Average Total Balances”**; `driver-detail` / `class="detail"` count **0** | SBS `slide_18.png`; DOM `.driver-label` texts |
| **#272 s15** reserve navy + uncollide totals | Faithful content with **accepted color invert** (write-offs dark vs light) | **RESOLVED colors + collision:** reserve **navy** `#00175a`; write-offs **primary_blue** `#006fcf`; totals sit above Q2–Q4 caps, not on category labels; two series only | SBS `slide_15.png`; dataset fills; overlay totals $1,405 / $1,287 / $1,414 |
| **#273** hero/`metric_overview` 27px wrap | s12 values 72px; hero copy called short; s22 accepted recipe without 27px callout | **RESOLVED type:** s12/s18/s22 `data-plan-sizes="body:27,heading:32,value:72"`; wrapping KPI/driver labels at 27px; HERO_HEADING 32 / HERO_VALUE 72 / METRIC_STRIP_VALUE 44 **held** (s8 strip 44px) | DOM plan-sizes + inline font-size; SBS s12/s18/s22 |
| **#274** independent thead stub navy | s9/s10 faithful support tables; s4/s19 hide_header (no thead band) | **RESOLVED:** s4/s9/s10/s19 thead stub (`Metric` / `Q1'26`) class `band-table-header … stub` on the navy band; tbody stubs `stub align-left` without the band class | DOM th classes; SBS s4/s9/s10/s19 |

### 5.2 Other v15 residuals

| residual | v15 → v16 |
|----------|-----------|
| R-D s38–43 legal packing | **FLIPPED** to leftover air/type (accepted divergence). Markup portion closed by #270; title/type still held from #257 |
| A-247-hide-header s4/s19 | **FLIPPED** — independent navy-header tables per #269; no longer an accepted hide_header miss |
| A-s15-colors write-off/reserve invert | **RESOLVED** by #272 (navy reserve / primary_blue write-offs match PDF) |
| Cover brand seal / section divider / metric_overview / comparison_cards / period pills / annex flatten | **PRESERVED** accepted divergences |
| #246/#248 floors | **HELD** green |
| s24 navy Processed Volumes / #254 above-groups | **HELD** faithful (parked/accepted; no fresh evidence to reclass) |
| P-247-head probe miss | **stayed closed** (v15); map emptied under #269 rather than hide_header-green |

### 5.3 What changed in classification counts

| class | v15 table | v16 | notes |
|-------|----------:|----:|-------|
| faithful reproduction | 29 | **29** | s4/s19 stay faithful (observation updates only); ticket surfaces land inside existing faithful rows |
| accepted v3 design divergence | 9 | **15** | s38–43 join leftover air/type after #270; covers/recipes stable |
| corpus/extraction residual | 0 | **0** | — |
| candidate renderer defect | 6 | **0** | legal packing six-pack flipped |
| capture failure | 0 | **0** | — |

Net: design ledger stays **44/44**. Ticket surfaces #268–#274 observed on fresh SBS + DOM/probes. No new capture failures. No image scoring used. v15 summary line that said faithful 31 / accepted 7 disagrees with that report’s own 44-row table (29 / 9 / 6); this delta uses the table.

---

## 6. Residual triage

Only residuals with fresh v16 evidence. No fixes designed or ticketed here.

### 6.1 Candidate renderer_v3 defect / capability gap

**None.** v15 **R-D** (s38–43 packing/hierarchy) is closed as a candidate: unmarked continuations paint as `<p>` per #270; remaining tightness is leftover air/type under the accepted legal recipe.

### 6.2 Corpus / extraction / content residual

None with fresh exclusive evidence this run. Ticketed corpus surfaces (#268–#274) paint as authored.

### 6.3 Source/PDF artifact or accepted divergence

| ID | where | note |
|----|-------|------|
| A-cover | s1 / s44 | Brand seal / full-bleed navy vs minimal white lockup — standing accepted cover recipe |
| A-period | s3 / s20 | Compact matrix / flattened hierarchy vs PDF pills — schema recipe |
| A-cards | s7 | Circular card art vs PDF — comparison_cards recipe |
| A-metric | s22 | Sparse metric_overview vs centered PDF cards (#273 type held) |
| A-divider | s23 | White section plate vs navy brand divider |
| A-annex-flat | s31 | Nested annex groups flattened |
| A-legal-air | s38–43 | Leftover air/type vs PDF list/paragraph spacing after #270 markup lands (s38 keeps two marked `<ul>`s; s39–43 are `<p>`) |

### 6.4 Screenshot / probe / design-ledger failures

**None.** `missing_or_bad_size=[]`, `capture_errors=[]`, `design_ledger_fail_slides=[]`, console `[]`.

---

## 7. Diagnostics & artifact index

### Render diagnostics

- CLI: strict exit **0**
- `run_meta.status`: **clean** · `ok`: **true** · `options.strict`: **true**
- Events: **67 info**, 0 warn, 0 error
- Renderer version **3.0.0** @ commit `9c2acd1683ccc8fe047213f01f0726596d62c909`

### Artifact tree (`simulation/amex_q1_2026/`)

```
GAP_ANALYSIS.md
build_v16_comparison.py
capture_log.json
comparison_manifest.json
contact_sheet.png
html_slides/slide_01.png … slide_44.png          (1920×1080)
pdf_pages/slide_01.png … slide_44.png            (1920×1080)
side_by_side/slide_01.png … slide_44.png         (3840×1080)
passes/pass_01/renderer_v3_out/
  presentation.html
  run_meta.json
  evidence_manifest.json
  handoff_schema_v1.json
  slide_notes.md
```

### Contact sheet

`contact_sheet.png` — 8×6 labeled thumbs of full-resolution SBS pairs (PDF|HTML), 3840×954.

### Manifest proofs

- `comparison_manifest.json`: `baseline=v16`, 44 pdf/html/sbs rows, 44 `design_ledgers`, `missing_or_bad_size=[]`, `html_png_unique_sha256_count=44`
- No MAE / similarity / pixel-diff / heatmap fields anywhere in sim outputs (builder docstring forbids them; `handoff_schema_v1.json` may mention heatmap as a schema keyword — not a scored artifact)

---

## 8. Stop proofs

| Proof | Status |
|-------|--------|
| Strict render exit 0 clean (or fully labeled DEGRADED path) | **PASS** — clean |
| 44 PDF + 44 HTML + 44 SBS at exact 1920×1080 halves | **PASS** |
| `comparison_manifest.json` design-ledger row per slide | **PASS** 44/44 ok |
| Report at `simulation/amex_q1_2026/GAP_ANALYSIS.md` | **PASS** |
| Byte-identical copy `wiki/baseline_v16_GAP_ANALYSIS.md` | *(docs commit)* |
| Exactly two commits: sim artifacts, then docs wiki copy | *(commit step)* |
| Only allowed paths changed | **PASS** intent — sim + wiki baseline only |
| No production/test/script/config edits | **PASS** |
| No MAE/similarity/pixel-diff scoring | **PASS** |
| v15→v16 delta covers #268–#274 + prior residuals | **PASS** (§5) |
| Residual triage with ownership, no tickets filed | **PASS** (§6) |

**Stop condition:** v16 observation baseline complete with full 44-page comparison, qualitative ledger, DP-6+#249/#256/#269 design ledger, v15→v16 delta, residual triage, and (after the two allowed commits) exactly those commits — no production paths changed and no image scoring used.
