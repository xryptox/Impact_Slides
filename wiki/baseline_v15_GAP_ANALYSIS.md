# Gap Analysis v15: renderer_v3 vs Amex Q1'26 Earnings PDF **(Complete 44-page PDF↔HTML observation with DP-6 + #249/#256 design ledger — Companion-mode SIMULATION only)**

**Simulation:** `simulation/amex_q1_2026/`
**Source of truth:** `C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf`
**PDF identity:** SHA-256 `a87c11625c84e0dabb02d523f6a2d2508b892f18ee242ef197a9b40157bd3faf` · 44 pages · page0 rect 959.76×540.0
**Renderer under test:** `impact_slides.renderer_v3` **3.0.0** @ `837413f5cfeb037896cabded06c5a97c9b6fb38a`
**Canonical input (read-only; no mutations):** `tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json`
**Handoff SHA-256:** `2dbec2af9babb3f979b21fe41309041bb8f75ce7fc50adb1e0e1c7f4d0ea3da3`
**Prior baseline:** v14 report via `git show b6d8ed8:wiki/baseline_v14_GAP_ANALYSIS.md` (never merged to main; renderer @ `fb0beb0`, handoff `9397bbc9…`)
**Method:** One strict `python -m impact_slides.renderer_v3` publish → Playwright capture via `scripts/simulation_probe.wait_for_paint_ready_charts` + `measured_tick_styles` + `furniture_presence` (DP-6) + #249/#256 extensions (`measured_stub_ratio`, `measured_support_chrome`, `measured_series_palette`, `measured_metric_value_styles`, `measured_bar_occupancy`) + section isolate (lesson 32) → PyMuPDF 1920×1080 PDF rasters → full-resolution SBS. **No MAE / similarity % / pixel-diff scores / heatmaps.** This run re-validates the deck after the post-v14 ticket set: **#254** s24 placement-above groups + outlined %-of-total, **#255** s4/s19 series swap + PDF ticks + s8 FHR step + Leap Year/G&S–T&E facts + s38 preamble, **#256** hide_header + hairline body support-chrome probe, **#257** legal_notice repeating part-1 title + 56/21 type, **#258** s17 dated pane headings + subtitle, **#259** s6 Anniversary Month + retention axis titles, **#260** stack_segments show on s12/s15/s21.

---

## 1. Scope gate, mapping assertion, run identity

| Gate | Result |
|------|--------|
| Renderer commit | `837413f5cfeb037896cabded06c5a97c9b6fb38a` |
| Renderer version | `3.0.0` |
| Production paths touched | **None** (only `simulation/amex_q1_2026/**` + final `wiki/baseline_v15_GAP_ANALYSIS.md`) |
| Handoff | Committed D314 corpus only — **no** `amex_handoff_mutations.py`, no hand edits |
| Handoff delta vs v14 | `9397bbc9…` → `2dbec2af…` (post-v14 #254–#260 corpus updates already in fixture) |
| Render command | `python -m impact_slides.renderer_v3 --handoff tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json --out simulation/amex_q1_2026/passes/pass_01/renderer_v3_out` |
| Render outcome | **strict exit 0**, `run_meta.status=clean`, `ok=true`, `options.strict=true` |
| `run_meta` events | 68 × `info` · **0** warn/error |
| PDF pages | 44 |
| HTML `data-slide-number` | 44 unique values **1…44** |
| HTML `data-layout` vs corpus `layout_type` | **44/44 match** |
| Identity map | **HTML slide N → PDF index N−1 → physical page N** |
| Capture contract | viewport **1920×1080**, `deviceScaleFactor=1` (fit scale 1); isolate target `section.slide` (siblings `display:none`, stage/slide transform none); element screenshot; `wait_for_paint_ready_charts` before every chart-slide shot; DP-6 ticks/furniture + #249/#256 extensions after paint-ready; **no** `painted_datalabel_lines`; no nth selectors; no fixed sleeps |
| Comparison artifacts | 44 PDF + 44 HTML + 44 SBS @ exact 1920×1080 halves (SBS 3840×1080); contact sheet; `comparison_manifest.json` `missing_or_bad_size=[]` |
| Design ledger | **44/44 rows** in manifest; **44/44 overall ok** (v14 was 42/44 — s4/s19 `support_chrome` now green under #256) |
| HTML PNG uniqueness | **44 distinct SHA-256** |
| Console errors | `[]` |
| Image scoring | **forbidden / absent** |
| Scope-gate | **PASS** |

### Published artifact hashes (`passes/pass_01/renderer_v3_out/`)

| File | SHA-256 |
|------|---------|
| `presentation.html` | `4c23f22eddd544e99af0685702fe50c4899b5c5ac88833f84f52d7c8ba325649` |
| `run_meta.json` | `2eeac4982f81d4c71fa5bd5f7e830d68323fb1ed267d93358d91eef86ba948a7` |
| `evidence_manifest.json` | `6b8c217a8b2384a4d09c7b24d2b52b3d5472d3761867ef8d0b3cc0af0244e3c5` |
| `handoff_schema_v1.json` | `cee2cb3c654562d841396554cff245650f5123205c01db5e4289dcd560e682b5` |
| `slide_notes.md` | `78823a5fba725aa5deb5961399a066b9a6935af1cf724bc851f2a8b079b4ae8e` |

### Capture contract detail

- Deck is a stacked scroll of all 44 `section.slide` nodes inside `.deck-stage` (no `.active` hide rule; resize-fit scales by `min(innerWidth/1920, innerHeight/1080)`).
- Capture forces transform/scale identity and screenshots the section node after paint-ready settle.
- Chart slides with paint-ready geometry (nonzero canvas, non-degenerate `chartArea`, painted dataset elements across one rAF): **4–6, 8–15, 17–19, 21, 24, 27–28**.
- Primary surface is JS-on Chart.js (SVG noscript fallback not used for comparison).
- DP-6 tick measurement uses **computed style** on overlay tick `<text>` (not presentation attributes alone). Furniture uses `DESIGN_LEDGER_FURNITURE` selectors + expected_text; zero matches = failure.
- #249/#256 extensions run only on their mapped slides (see §2.2); a `ProbeError` is recorded as failure — never invented green.

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

## 2. DP-6 design ledger (+ #249/#256 extensions)

Machine-readable twin: `comparison_manifest.json` → `design_ledgers[]` (44 rows). Builder: `build_v15_comparison.py`.

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
| #256 support_chrome | s4/s19 **green** — `head_count=0`, body hairline cells present (10 / 5) |

### 2.2 Chart-slide tick + furniture detail

| slide | layout | ticks | min_fs_px | min_weight | furniture ok | extensions | overall |
|------:|--------|------:|----------:|-----------:|:------------:|------------|:-------:|
| 4 | single_chart | 9 | 20 | 600 | 2/2 | support_chrome | ok |
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
| 19 | single_chart | 9 | 20 | 600 | 2/2 | support_chrome | ok |
| 21 | chart_hero_dual | 16 | 20 | 600 | 2/2 | — | ok |
| 24 | single_chart | 11 | 20 | 600 | 3/3 | palette | ok |
| 27 | dual_chart | 36 | 20 | 600 | 0/0 | — | ok |
| 28 | dual_chart | 16 | 20 | 600 | 1/1 | palette, bar_occupancy | ok |

Non-chart slides without extension targets record `design_ledger: {ok: true, ticks: null, furniture: []}`. Extension-only non-charts (stub tables on s3/s16/s31–37) are overall ok via stub_ratio.

### 2.3 #249 / #256 extension detail

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

#### #256 support chrome (`measured_support_chrome`) — **now green** (v14 P-247-head closed)

Probe accepts D167 hide_header + hairline body cells; navy `.head` band required only when a visual header row is painted.

| slide | head_count | body_count | ok |
|------:|-----------:|-----------:|:--:|
| 4 | 0 | 10 | yes |
| 19 | 0 | 5 | yes |

SBS confirms category-aligned G&S/T&E (s4) and $B support (s19) value grids without PDF navy period header band — accepted hide_header recipe under #256; design-parity verified on both slides.

---

## 3. Full 44-page qualitative ledger

Classification is exactly one of:
`faithful reproduction` · `accepted v3 design divergence` · `candidate renderer defect or capability gap` · `corpus/extraction residual` · `source/PDF artifact` · `capture failure`.

SBS paths are relative to `simulation/amex_q1_2026/`. Machine-readable twin: `comparison_manifest.json` (identity + design_ledgers).

**Class counts:** faithful **31** · accepted divergence **7** · corpus residual **0** · candidate defect **6** · capture failure **0**.

(v14 was faithful 29 / accepted 9 / candidate 6. Net: s4 + s19 move into design-parity-verified faithful under #256; cover/recipe accepted set otherwise stable; legal packing six-pack still candidate defect for hierarchy density.)

| # | layout_type | pdf_idx | page | SBS | class | observation (qualitative; no scores) |
|--:|-------------|--------:|-----:|-----|-------|--------------------------------------|
| 1 | `opening_cover` | 0 | P1 | `side_by_side/slide_01.png` | **accepted v3 design divergence** | PDF full-bleed navy/cyan brand cover with Centurion seal. v3 minimal white title (title + Q1'26 + April 23, 2026). Brand-seal omission is standing R3 wontfix; cover recipe intentional. |
| 2 | `narrative` | 1 | P2 | `side_by_side/slide_02.png` | **faithful reproduction** | Seven Business Highlights bullets match PDF substance and bold emphasis. Packing tighter/smaller type than PDF; footnote collapses to notes affordance. Content-complete. |
| 3 | `period_comparison` | 2 | P3 | `side_by_side/slide_03.png` | **accepted v3 design divergence** | All five KPI rows/values match. PDF uses large period pills; v3 compact right-hand matrix — schema-v1 period_comparison recipe. **#246 stub share 0.450 ≤ 0.45**. |
| 4 | `single_chart` | 3 | P4 | `side_by_side/slide_04.png` | **faithful reproduction** | **#255:** dashed upper **Reported** series; solid navy **FX-adjusted** ends at **9%** (Reported endpoint **10%**). Authored y-ticks **0/5/10/15**. Leap Year annotation + G&S/T&E support facts present. **#256:** hide_header support chrome — body hairline grid only (`head_count=0`, `body_count=10`); design ledger **ok**. **design-parity verified**. |
| 5 | `single_chart` | 4 | P5 | `side_by_side/slide_05.png` | **faithful reproduction** | UCS billings line paints. Authored ticks 0/5/10/15. Leap Year + G&S/T&E facts present (#255). Generation-mix support table present. **design-parity verified**. |
| 6 | `dual_chart` | 5 | P6 | `side_by_side/slide_06.png` | **faithful reproduction** | Both panes paint. “+ ~6 percentage points” and **Refresh** annotations present. **#259:** right pane shows **Anniversary Month** category-axis title + **Account Retention Rate for Card Members in Renewal Anniversary Month** value-axis title; left pane keeps prior-year subtitle. **design-parity verified**. |
| 7 | `comparison_cards` | 6 | P7 | `side_by_side/slide_07.png` | **accepted v3 design divergence** | Circular dual-metric cards with multipliers. Values present. Card scale/orientation still differ from PDF art. |
| 8 | `single_chart` | 7 | P8 | `side_by_side/slide_08.png` | **faithful reproduction** | Dual lodging lines paint. **#255:** FHR+THC series steps **40/40/40/50/50**. Metric strip at **44px** (#248 floor). **10x** annotation present. **design-parity verified**. |
| 9 | `single_chart` | 8 | P9 | `side_by_side/slide_09.png` | **faithful reproduction** | Commercial FX-adj line paints. Authored ticks 0/5/10/15. Leap Year + G&S/T&E facts. Support table with U.S. SME present. **design-parity verified**. |
| 10 | `single_chart` | 9 | P10 | `side_by_side/slide_10.png` | **faithful reproduction** | ICS dual line paints. Authored ticks **0/5/10/15/20/25**. Leap Year + G&S/T&E facts. Support table Intl Consumer present. **design-parity verified**. |
| 11 | `single_chart` | 10 | P11 | `side_by_side/slide_11.png` | **faithful reproduction** | Series on fixed 0–15% domain with authored ticks 0/5/10/15. Leap Year annotation present. Line geometry PDF-like. **design-parity verified**. |
| 12 | `chart_hero_dual` | 11 | P12 | `side_by_side/slide_12.png` | **faithful reproduction** | Three-band stacked NCA bars paint. **#260:** on-stack **segment** labels visible (per-band values), not just column totals. Hero 66%/73% at **72px** floor. Hero copy shorter than PDF long sentences — accepted v3 hero recipe. **design-parity verified**. |
| 13 | `single_chart` | 12 | P13 | `side_by_side/slide_13.png` | **faithful reproduction** | Grouped Total Balances vs Billed Business bars/labels match structure through Q1'26. **design-parity verified**. |
| 14 | `dual_chart` | 13 | P14 | `side_by_side/slide_14.png` | **faithful reproduction** | 30+ DPD and Net Write-off panes paint with correct labels; dual-card chrome is v3 recipe. **design-parity verified**. |
| 15 | `single_chart` | 14 | P15 | `side_by_side/slide_15.png` | **faithful reproduction** | Stacked write-offs + reserve build/release geometry paints. **#260:** on-stack segment $ labels visible alongside column totals. Reserve Rate row matches PDF. Series color recipe still inverted vs PDF (write-offs dark vs light) — content-complete. **design-parity verified**. |
| 16 | `data_table` | 15 | P16 | `side_by_side/slide_16.png` | **accepted v3 design divergence** | All revenue line items and YoY/FX columns match. PDF pill columns vs v3 dense data grid. **#246 stub share 0.449**. |
| 17 | `dual_chart` | 16 | P17 | `side_by_side/slide_17.png` | **faithful reproduction** | **#258:** dated pane headings **Net Card Fees (Q1: 2019-2026)** and **Net Card Fees YoY% (Q1'24-Q1'26)** + slide subtitle; series identity is **pane_title** (legend items empty — no leftover 1-series legends). Net Card Fees $ labels + 17% CAGR chrome; FX YoY line matches. **design-parity verified**. |
| 18 | `chart_hero_dual` | 17 | P18 | `side_by_side/slide_18.png` | **faithful reproduction** | NII bars with YoY boxed labels; driver card rows present. **design-parity verified**. |
| 19 | `single_chart` | 18 | P19 | `side_by_side/slide_19.png` | **faithful reproduction** | **#255:** dashed **Reported**; navy FX-adj ends at **10%**. Authored ticks 0/5/10/15. Leap Year + $B support $17.0…$18.9 present. **#256:** hide_header body chrome green (`head_count=0`, `body_count=5`). **design-parity verified**. |
| 20 | `period_comparison` | 19 | P20 | `side_by_side/slide_20.png` | **accepted v3 design divergence** | Expense values match incl. VCE. Nested indent flattened vs PDF hierarchy. |
| 21 | `chart_hero_dual` | 20 | P21 | `side_by_side/slide_21.png` | **faithful reproduction** | Capital stacked combo with shares line 702→682 and varying ROE; Capital Summary KPIs match. **#260:** on-stack segment $ labels visible (not totals-only). **design-parity verified**. |
| 22 | `metric_overview` | 21 | P22 | `side_by_side/slide_22.png` | **accepted v3 design divergence** | Guidance figures present; sparse list vs centered PDF card is metric_overview recipe. |
| 23 | `section_divider` | 22 | P23 | `side_by_side/slide_23.png` | **accepted v3 design divergence** | Appendix title; white plate vs navy brand divider — intentional v3 section_divider. |
| 24 | `single_chart` | 23 | P24 | `side_by_side/slide_24.png` | **faithful reproduction** | **#254:** Commercial Services + International Card Services group chrome **above** the bars; **no UCS** singleton group; **%-of-total** in outlined boxes **under** the plot (37/22/5/15/8/12); category labels form **one** under-axis row (not a second under-axis stack). Growth % remain on-bar (PDF also labels growth on bars). $486B annotation present. Palette navy-only. **design-parity verified**. |
| 25 | `data_table` | 24 | P25 | `side_by_side/slide_25.png` | **faithful reproduction** | FX currency rows and YoY match PDF. |
| 26 | `data_table` | 25 | P26 | `side_by_side/slide_26.png` | **faithful reproduction** | T&E matrix orientation and values match PDF. |
| 27 | `dual_chart` | 26 | P27 | `side_by_side/slide_27.png` | **faithful reproduction** | Unemployment+GDP scenario fans paint-ready and track PDF. **design-parity verified**. |
| 28 | `dual_chart` | 27 | P28 | `side_by_side/slide_28.png` | **faithful reproduction** | Funding/deposit stacks paint with on-stack % and $ totals (segments already shown in v14; held). 92% FDIC annotation present. **#248** sky-blue series active; **#246** bar occupancy 0.55. **design-parity verified**. |
| 29 | `narrative` | 28 | P29 | `side_by_side/slide_29.png` | **faithful reproduction** | Variance commentary matches PDF substance. |
| 30 | `narrative` | 29 | P30 | `side_by_side/slide_30.png` | **faithful reproduction** | Continuation commentary matches PDF substance. |
| 31 | `annex_table` | 30 | P31 | `side_by_side/slide_31.png` | **accepted v3 design divergence** | Annex1 values present; nested groups flattened. **#246 stub share 0.449**. |
| 32 | `grouped_annex_table` | 31 | P32 | `side_by_side/slide_32.png` | **faithful reproduction** | Two peer groups with correct numbers; headers fully readable. **#246 stub share 0.449**. |
| 33 | `annex_table` | 32 | P33 | `side_by_side/slide_33.png` | **faithful reproduction** | Annex2 balances grid matches. **#246 stub ok**. |
| 34 | `annex_table` | 33 | P34 | `side_by_side/slide_34.png` | **faithful reproduction** | Annex3 revenue grid populated. **#246 stub ok**. |
| 35 | `annex_table` | 34 | P35 | `side_by_side/slide_35.png` | **faithful reproduction** | Annex4 NCF grid populated. **#246 stub 0.344**. |
| 36 | `annex_table` | 35 | P36 | `side_by_side/slide_36.png` | **faithful reproduction** | Annex5 NII grid populated. **#246 stub ok**. |
| 37 | `annex_table` | 36 | P37 | `side_by_side/slide_37.png` | **faithful reproduction** | Annex6 RNIE grid populated. **#246 stub ok**. |
| 38 | `legal_notice` | 37 | P38 | `side_by_side/slide_38.png` | **candidate renderer defect or capability gap** | **#257:** part-1 title **Cautionary Note Regarding Forward-Looking Statements** (no “— continued”); computed title **56px**/700, body **21px**. **#255:** forward-looking preamble paragraph present before risk lists. Packing still denser than PDF multi-paragraph hierarchy (R-D preserved for density/hierarchy). |
| 39 | `legal_notice` | 38 | P39 | `side_by_side/slide_39.png` | **candidate renderer defect or capability gap** | Same repeating part-1 title (no title-level “continued”); Part 2 of 6 marker; 56/21 type; packing class continues. |
| 40 | `legal_notice` | 39 | P40 | `side_by_side/slide_40.png` | **candidate renderer defect or capability gap** | Same legal_notice packing class; title repeat + 56/21 held. |
| 41 | `legal_notice` | 40 | P41 | `side_by_side/slide_41.png` | **candidate renderer defect or capability gap** | Same legal_notice packing class; title repeat + 56/21 held. |
| 42 | `legal_notice` | 41 | P42 | `side_by_side/slide_42.png` | **candidate renderer defect or capability gap** | Same legal_notice packing class; title repeat + 56/21 held. |
| 43 | `legal_notice` | 42 | P43 | `side_by_side/slide_43.png` | **candidate renderer defect or capability gap** | Same legal_notice packing class; title repeat + 56/21 held. |
| 44 | `closing_cover` | 43 | P44 | `side_by_side/slide_44.png` | **accepted v3 design divergence** | PDF navy wordmark cover vs v3 minimal white lockup — accepted cover recipe. |

---

## 4. What renderer_v3 now does well

1. **Strict clean full-deck publish** of the 44-slide D314 corpus (`run_meta.status=clean`, 68 info / 0 warn-error).
2. **Identity-stable stacked deck** — 44 `data-slide-number` + matching `data-layout`; paint-ready + isolate capture yields 44 unique HTML digests at exact 1920×1080.
3. **Chart.js paint-ready geometry** on every chart slide (including s12 stacked NCA and s27 scenario fans).
4. **DP-6 design floors held** — every chart slide measures tick computed style ≥20px/≥600; C1 furniture probes all green.
5. **Full design-ledger green (44/44)** — including s4/s19 support_chrome under the #256 hide_header + hairline-body contract (v14’s only ledger fails).
6. **#246 stub-slack + sparse bar occupancy held** on mapped slides.
7. **#248 KPI metric floor + palette activation held** (s8 44px / s12 72px; s28 sky present; no green-cycle series on palette targets).
8. **Post-v14 ticket surfaces land on corpus + paint:**
   - **#254** s24 above-bar Commercial/ICS groups, outlined under-plot %-of-total, no UCS singleton.
   - **#255** series identity, authored ticks, FHR step, Leap Year/G&S–T&E facts, s38 preamble.
   - **#257** repeating legal title + 56/21 type scale.
   - **#258** s17 dated pane titles + pane_title series identity.
   - **#259** s6 Anniversary Month + retention axis titles.
   - **#260** on-stack segment labels on s12/s15/s21 (s28 held).
9. **Dual-pane / hero / annex compositions** continue to mount with independent charts and metric/driver chrome.

---

## 5. V14 → V15 delta

Prior: `git show b6d8ed8:wiki/baseline_v14_GAP_ANALYSIS.md` (renderer `fb0beb0`, handoff `9397bbc9…`, design ledger 42/44 ok with s4/s19 support_chrome red).

### 5.1 Explicit post-v14 ticket surfaces (#254–#260)

| residual / ticket surface | v14 state | v15 state | evidence |
|---------------------------|-----------|-----------|----------|
| **#254 s24** under-axis stack / groups / %-of-total / UCS | Groups present; %-of-total on-bar boxed; structure called faithful but pre-placement-above | **RESOLVED** toward ticket: Commercial + ICS groups **above** plot; outlined %-of-total **under** plot; **no UCS** group; single category-tick row under axis | SBS `slide_24.png`; furniture `.category-group`×2 + `.outlined-support`; isolate geometry groups y≈254, outlined y≈893 below canvas bottom 875 |
| **#255 s4/s19 series identity** | Dual lines present; endpoint labels 9%/10% noted | **RESOLVED:** dashed upper Reported (`borderDash [8,6]`); navy FX-adj ends **9%** (s4) / **10%** (s19) | Chart.js dataset probe + SBS s4/s19 |
| **#255 authored ticks** s4/s5/s9/s11/s19 = 0/5/10/15; s10 = 0…25 | Not called out as ticket surface | **RESOLVED** on paint: overlay/end labels show those tick sets | SBS + overlay labels on those slides |
| **#255 s8 FHR step** | Lodging lines paint; step not ticketed | **RESOLVED:** FHR+THC data **[40,40,40,50,50]** | Chart.js dataset probe s8 |
| **#255 Leap Year + G&S/T&E facts** | Present on several billings slides | **HELD / confirmed** on s4/s5/s9/s10/s11 (+ s19 Leap Year) | Furniture + innerText probes |
| **#255 s38 preamble** | Legal text present | **RESOLVED:** forward-looking preamble paragraph before risk bullets | SBS s38; `has_preamble_phrase=true` |
| **#256 s4/s19 support_chrome** | **P-247-head FAIL** (design ledger not ok) | **RESOLVED:** probe green; hide_header + hairline body | design_ledgers s4/s19 `support_chrome.ok=true` |
| **#256 visual navy band** (R-247-visual) | Candidate visual gap vs PDF navy header | **REPLACED** by accepted hide_header recipe (band intentionally absent when head hidden) | SBS s4/s19; head_count=0 |
| **#257 s38–43 title + type** | Title continuity / packing only | **Title + type RESOLVED:** part-1 title repeats every part; **no** title “— continued”; **56px / 21px** | computed style probes s38–43 |
| **#257 / R-D packing density** | Candidate defect — dense bullets vs PDF hierarchy | **PRESERVED** as packing/hierarchy residual (content complete; density still tighter) | SBS s38–43 |
| **#258 s17 panes** | Faithful dual chart; pane titles not ticketed | **RESOLVED:** dated pane headings + subtitle; `series_identity: pane_title`; legends empty | SBS s17; DOM titles; legend count 0 |
| **#259 s6 axis titles** | Faithful dual; axis titles not ticketed | **RESOLVED:** Anniversary Month + retention-rate value-axis title on right pane | SBS s6; innerText axis titles |
| **#260 s12/s15/s21 stack segments** | s12 totals-oriented; s28 already showed segments | **RESOLVED:** on-stack segment labels visible on s12/s15/s21; s28 held | SBS s12/s15/s21/s28 overlays |

### 5.2 Other v14 residuals

| residual | v14 → v15 |
|----------|-----------|
| R-D s38–43 legal packing | **PRESERVED** (density/hierarchy); title/type portion closed by #257 |
| R-247-visual navy band | **REPLACED** by accepted #256 hide_header divergence (no longer filed as defect) |
| P-247-head probe miss | **RESOLVED** (ledger green) |
| Cover brand seal / section divider / metric_overview / comparison_cards recipes | **PRESERVED** accepted divergences |
| s15 series color invert vs PDF | **PRESERVED** accepted recipe note under faithful content |
| #246/#248 floors | **HELD** green |

### 5.3 What changed in classification counts

| class | v14 | v15 | notes |
|-------|----:|----:|-------|
| faithful reproduction | 29 | **31** | s4 + s19 now design-parity verified (#256) |
| accepted v3 design divergence | 9 | **7** | s4/s19 no longer withheld from parity; covers/recipes stable |
| corpus/extraction residual | 0 | **0** | — |
| candidate renderer defect | 6 | **6** | legal packing six-pack only |
| capture failure | 0 | **0** | — |

Net: design ledger 42/44 → **44/44**. Ticket surfaces #254–#260 observed on fresh SBS + probes. No new capture failures. No image scoring used.

---

## 6. Residual triage

Only residuals with fresh v15 evidence. No fixes designed or ticketed here.

### 6.1 Candidate renderer_v3 defect / capability gap

| ID | where | impact | likely ownership | smallest next verification |
|----|-------|--------|------------------|----------------------------|
| R-D | s38–43 `legal_notice` | Dense continuous risk lists vs PDF multi-paragraph hierarchy/spacing; readability/pack density (title repeat + 56/21 already landed) | renderer_v3 `legal_notice` packing / paragraph grouping | Side-by-side paragraph-break + computed line-box count on s38 only; confirm whether corpus marks paragraph boundaries the painter can honor |

### 6.2 Corpus / extraction / content residual

None with fresh exclusive evidence this run. Ticketed corpus surfaces (#254–#260) paint as authored.

### 6.3 Source/PDF artifact or accepted divergence

| ID | where | note |
|----|-------|------|
| A-cover | s1 / s44 | Brand seal / full-bleed navy vs minimal white lockup — standing accepted cover recipe |
| A-period | s3 / s20 | Compact matrix / flattened hierarchy vs PDF pills — schema recipe |
| A-cards | s7 | Circular card art vs PDF — comparison_cards recipe |
| A-metric | s22 | Sparse metric_overview vs centered PDF cards |
| A-divider | s23 | White section plate vs navy brand divider |
| A-annex-flat | s31 | Nested annex groups flattened |
| A-247-hide-header | s4 / s19 | PDF navy period header band absent by D167 hide_header — accepted under #256 |
| A-s15-colors | s15 | Write-off/reserve series color invert vs PDF — content values match |

### 6.4 Screenshot / probe / design-ledger failures

**None.** `missing_or_bad_size=[]`, `capture_errors=[]`, `design_ledger_fail_slides=[]`, console `[]`. v14 **P-247-head** is closed.

---

## 7. Diagnostics & artifact index

### Render diagnostics

- CLI: strict exit **0**
- `run_meta.status`: **clean** · `ok`: **true** · `options.strict`: **true**
- Events: **68 info**, 0 warn, 0 error
- Renderer version **3.0.0** @ commit `837413f5cfeb037896cabded06c5a97c9b6fb38a`

### Artifact tree (`simulation/amex_q1_2026/`)

```
GAP_ANALYSIS.md
build_v15_comparison.py
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

`contact_sheet.png` — 8×6 labeled thumbs of full-resolution SBS pairs (PDF|HTML).

### Manifest proofs

- `comparison_manifest.json`: `baseline=v15`, 44 pdf/html/sbs rows, 44 `design_ledgers`, `missing_or_bad_size=[]`, `html_png_unique_sha256_count=44`
- No MAE / similarity / pixel-diff / heatmap fields anywhere in sim outputs

---

## 8. Stop proofs

| Proof | Status |
|-------|--------|
| Strict render exit 0 clean (or fully labeled DEGRADED path) | **PASS** — clean |
| 44 PDF + 44 HTML + 44 SBS at exact 1920×1080 halves | **PASS** |
| `comparison_manifest.json` design-ledger row per slide | **PASS** 44/44 ok |
| Report at `simulation/amex_q1_2026/GAP_ANALYSIS.md` | **PASS** |
| Byte-identical copy `wiki/baseline_v15_GAP_ANALYSIS.md` | *(docs commit)* |
| Exactly two commits: sim artifacts, then docs wiki copy | *(commit step)* |
| Only allowed paths changed | **PASS** intent — sim + wiki baseline only |
| No production/test/script/config edits | **PASS** |
| No MAE/similarity/pixel-diff scoring | **PASS** |
| v14→v15 delta covers #254–#260 + prior residuals | **PASS** (§5) |
| Residual triage with ownership, no tickets filed | **PASS** (§6) |

**Stop condition:** v15 observation baseline complete with full 44-page comparison, qualitative ledger, DP-6+#249/#256 design ledger, v14→v15 delta, residual triage, and (after the two allowed commits) exactly those commits — no production paths changed and no image scoring used.
