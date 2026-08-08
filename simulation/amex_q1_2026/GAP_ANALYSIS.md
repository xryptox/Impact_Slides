# Gap Analysis v11: renderer_v2 vs Amex Q1'26 Earnings PDF

**(Closed-ticket revalidation #136–#159 + full 44-page PDF↔HTML comparison — observation only)**

**Simulation:** `simulation/amex_q1_2026/`  
**Source of truth:** `C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf`  
**PDF identity:** SHA-256 `a87c11625c84e0dabb02d523f6a2d2508b892f18ee242ef197a9b40157bd3faf` · 44 pages · page0 rect 959.76×540.0  
**Renderer under test:** `impact_slides.renderer_v2` @ `af3662b` (`af3662b1fac3954882ef25febda665143bcb588e`) — current main line; **no production edits this run**  
**Prior baseline:** `simulation/amex_q1_2026/extracted/baseline_v10_GAP_ANALYSIS.md` (from origin/gnhf/objective-produce-an-74065a) + `wiki/baseline_v10_VERIFIER_CORRECTION_146.md`  
**Handoff source:** `tests/fixtures/renderer_v2/amex_v10_44_slide_handoff.json` → `passes/pass_01/handoff.pre_mutations.json`  
**Handoff SHA-256 pre/post mutations:** `38af8acc02ac81d3e92d1d42267630bf016860496354c8bdcd12e74aaf9bd42e` / `14afc83eda1f0f27eeb9ab1d0db890d6a634c78bd621fd5584919cd226d76e8c`  
**Mutations:** `python scripts/amex_handoff_mutations.py` only — **no hand edits**.  
**Mutation changed slides:** [13, 14, 21, 24, 27, 28, 32, 33, 34, 35, 36, 37]  
**Method:** Playwright geometry via `scripts/simulation_probe.py` (`activate_slide`, `wait_for_paint_ready_charts`, `painted_datalabel_lines`) + 1920×1080 full-resolution PDF/HTML side-by-sides. House tol ±4px; #136 centres ≤12px.  
**No MAE / similarity percent / pixel-diff scores / heatmaps.**

---

## 1. Scope gate, mapping assertion, run identity

| Gate | Result |
|------|--------|
| Renderer commit | `af3662b` — main HEAD at sim start |
| Production paths touched | **None** (`impact_slides/`, tests, scripts, configs untouched) |
| Handoff | Single pass_01 from canonical fixture + `amex_handoff_mutations.py` only; no pass_02 |
| PDF pages | 44 |
| HTML `data-slide-number` unique values | 44 (1…44) |
| Identity map | **HTML slide N → PDF index N−1 → physical page N** |
| Mapping assertion | **HOLD** (`page_slide_mapping.json` ok=True; hard_mismatches=[]) |
| Recipe aliases | handoff `split_text_visual` → HTML `freeform_grid` on slides 29,30,38–43 (known alias, not identity break) |
| Capture contract | `activate_slide` + `wait_for_paint_ready_charts`; no nth selectors; no fixed sleeps |
| Comparison artifacts | 44 PDF + 44 HTML + 44 SBS @1920×1080; contact sheet; `all_artifacts_present=True` |
| Console warnings (comparison) | [] |
| Image scoring | **forbidden / absent** (`no_image_scoring=True`) |
| Scope-gate | PASS — only `simulation/amex_q1_2026/**` + final wiki report; no production edits |

### Handoff contract assertions (pre-capture)

| Contract | Pass | Notes |
|----------|------|-------|
| slide 12 pane headings (#147) | **FAIL** | Canonical amex_v10 fixture lacks explicit left/right pane headings (#147); mutations do not author them. |
| slide 17 typography.mode=auto both panes (#139/#150) | **PASS** | {"typography": {"primary_visual": {"y_tick_font_size": 24, "datalabel_font_size": 28, "mode": "auto"}, "secondary_visual": {"y_tick_font_size": 24, "datalabel_font_size": 28, "mode": "auto"}}} |
| slide 18 driver_card + boxed_labels (#151) | **PASS** | {"layout_type": "chart_hero_dual", "primary_type": "grouped_bar_chart", "has_boxed_labels": true, "boxed_labels": {"label": "YoY Growth", "values": ["11%", "12%", "12%", "12%", "12%"]}, "secondary_typ |
| slide 26 Q1'26 matrix orientation (#153) | **FAIL** | Canonical fixture still carries v10 transposed matrix; amex_handoff_mutations.py does not include #153. |

**all_required_contracts_pass:** `False` — fails are handoff/fixture gaps (#147, #153), not renderer defects.

### Mutation diff (exact changed slides)

Script-only changes on slides **[13, 14, 21, 24, 27, 28, 32, 33, 34, 35, 36, 37]**. Top-key diffs:

| Slide | Title | Diff top keys | layout_type |
|------:|-------|---------------|-------------|
| 13 | Total Balances and Billed Business | layout_type, speaker_notes, visual_spec | `grouped_bar_chart` |
| 14 | Credit Metrics | content, speaker_notes, visual_spec | `dual_chart` |
| 21 | Capital | content, layout_type, packing_mode, speaker_notes, visual_spec | `chart_hero_dual` |
| 24 | Q1'26 Network Volumes Growth by Customer Type | content, disclosure, layout_type, packing_mode, speaker_notes, visual_spec | `grouped_bar_chart` |
| 27 | Credit Reserve Macroeconomic Scenarios: Select Variables | content, disclosure, evidence_sources, speaker_notes, visual_spec | `dual_chart` |
| 28 | Funding and Deposits | visual_spec | `multi_panel` |
| 32 | Annex 1 (2 of 2) Billed Business — Reported & FX-Adjusted | layout_type, speaker_notes, visual_spec | `grouped_annex_table` |
| 33 | Annex 2 Total Balances — Reported & FX-Adjusted | content, speaker_notes, visual_spec | `annex_table` |
| 34 | Annex 3 Revenue — Reported & FX-Adjusted | content, speaker_notes, visual_spec | `annex_table` |
| 35 | Annex 4 Net Card Fees — Reported & FX-Adjusted | content, speaker_notes, visual_spec | `annex_table` |
| 36 | Annex 5 Net Interest Income — Reported & FX-Adjusted | content, speaker_notes, visual_spec | `annex_table` |
| 37 | Annex 6 Revenues Net of Interest Expense — Reported & FX-Adjusted | content, speaker_notes, visual_spec | `annex_table` |

### Page / slide mapping assertion

Numeric identity HTML slide N ↔ PDF index N−1 ↔ physical page N holds for all 44.  
Full row dump: `simulation/amex_q1_2026/page_slide_mapping.json`.  
Every artifact name and scorecard/ledger row carries `slide_number`, `expected_layout` (HTML `data-layout`), `pdf_page_index`, `pdf_physical_page`.

### #137 / #146 process compliance

| Requirement | Evidence |
|-------------|----------|
| `activate_slide(page, slide_number, expected_layout)` only | `probes/build_full_comparison.py`, `probes/v11_closed_ticket_probes.py` |
| No `section.slide[i]` / nth / scrollIntoView activation | Confirmed in probe sources |
| `wait_for_paint_ready_charts` before every chart screenshot | Full comparison + closed-ticket probes |
| `painted_datalabel_lines` for Chart.js datalabel evidence | #139/#150, #151 boxed labels, #154 brackets |
| Zero selector match / missing painted model / zero-size canvas = failure | ProbeError paths; no successful empty observations |
| Readiness across one animation frame | simulation_probe contract |
| JSON rows include slide identity | `comparison_manifest.json`, `closed_ticket_results_v11.json` |
| Console / run_meta with identity | manifest warnings=0; `passes/pass_01/output/run_meta.json` |
| Formerly blank 9 / 12 / 27 recheck | paint-ready 1 / 1 / 2 charts respectively |

**#137/#146 verdict: PASS (tooling + paint-ready capture contract on full deck).**

---

## 2. Closed-ticket scorecard (#136–#159)

Fresh rendered probes only. Closed GitHub issues are **not** proof. Supporting focused pytest: **279 passed in 28.75s** (`closed_tickets/focused_tests_summary.json`) — unit evidence only, not scorecard substitutes.

Probe totals: **148/154 pass**, **6 fail** (all six fails are #147×2 + #153×4 handoff residuals across chartjs+svg).

| Ticket | Title | Input | Assertion | Runtime(s) | Slides | Evidence | Result | Residual |
|--------|-------|-------|-----------|------------|--------|----------|--------|----------|
| #136/#149 | slide 15 outlined support + label lane | `presentation.html` pass_01 | DOM/geometry/content probes (16/16 pass) | chartjs+svg | slides 15 | `closed_tickets/closed_ticket_results_v11.json` | **PASS** | — |
| #137/#146 | identity-safe paint-ready capture | `presentation.html` pass_01 | DOM/geometry/content probes (13/13 pass) | chartjs+svg | slides 9, 12, 27 | `closed_tickets/closed_ticket_results_v11.json` | **PASS** | — |
| #138/#158 | slide 28 FDIC callout + pane titles | `presentation.html` pass_01 | DOM/geometry/content probes (10/10 pass) | chartjs+svg | slides 28 | `closed_tickets/closed_ticket_results_v11.json` | **PASS** | — |
| #139/#150 | slide 17 typography + auto sizes | `presentation.html` pass_01 | DOM/geometry/content probes (6/6 pass) | chartjs+svg | slides 17 | `closed_tickets/closed_ticket_results_v11.json` | **PASS** | — |
| #140 | slide 3 pill board + neg controls | `presentation.html` pass_01 | DOM/geometry/content probes (14/14 pass) | chartjs+svg | slides 3, 20, 24 | `closed_tickets/closed_ticket_results_v11.json` | **PASS** | — |
| #147 | slide 12 pane headings | `presentation.html` pass_01 | DOM/geometry/content probes (2/4 pass) | chartjs+svg | slides 12 | `closed_tickets/closed_ticket_results_v11.json` | **PARTIAL** | handoff |
| #148 | slides 13-14 vertical bars + pane order | `presentation.html` pass_01 | DOM/geometry/content probes (7/7 pass) | chartjs+svg | slides 13, 14 | `closed_tickets/closed_ticket_results_v11.json` | **PASS** | — |
| #151 | slide 18 boxed labels + driver card | `presentation.html` pass_01 | DOM/geometry/content probes (8/8 pass) | chartjs+svg | slides 18 | `closed_tickets/closed_ticket_results_v11.json` | **PASS** | — |
| #152 | gridlines default off | `presentation.html` pass_01 | DOM/geometry/content probes (10/10 pass) | chartjs+svg | slides 9, 13, 15, 18 | `closed_tickets/closed_ticket_results_v11.json` | **PASS** | — |
| #153 | slide 26 Q1'26 matrix orientation | `presentation.html` pass_01 | DOM/geometry/content probes (0/4 pass) | chartjs+svg | slides 26 | `closed_tickets/closed_ticket_results_v11.json` | **FAIL** | handoff |
| #154 | slide 24 growth brackets + $486B | `presentation.html` pass_01 | DOM/geometry/content probes (10/10 pass) | chartjs+svg | slides 24 | `closed_tickets/closed_ticket_results_v11.json` | **PASS** | — |
| #155 | slide 21 capital return composition | `presentation.html` pass_01 | DOM/geometry/content probes (7/7 pass) | chartjs+svg | slides 21 | `closed_tickets/closed_ticket_results_v11.json` | **PASS** | — |
| #156 | slide 27 macro scenarios | `presentation.html` pass_01 | DOM/geometry/content probes (9/9 pass) | chartjs+svg | slides 27 | `closed_tickets/closed_ticket_results_v11.json` | **PASS** | — |
| #157 | slides 33-37 annex matrices | `presentation.html` pass_01 | DOM/geometry/content probes (30/30 pass) | chartjs+svg | slides 33, 34, 35, 36, 37 | `closed_tickets/closed_ticket_results_v11.json` | **PASS** | — |
| #159 | slide 32 grouped annex heading IDs | `presentation.html` pass_01 | DOM/geometry/content probes (6/6 pass) | chartjs+svg | slides 32 | `closed_tickets/closed_ticket_results_v11.json` | **PASS** | — |

### Scorecard detail (key measurements)

#### #136 / #149 — slide 15 outlined support + label lane

- Input: mutated pass_01 HTML; list-of-lists primary retained.
- Chart.js max |cell_cx−bar_cx| over 5 bars: **0.188px** (≤12).
- Label lane vs first value cell: gap_px=**0.0** (no overlap).
- SVG mode: same checks PASS (see `closed_ticket_results_v11.json`).
- **Result: PASS** both modes.

#### #137 / #146 — identity-safe paint-ready capture

- 44 unique `data-slide-number` 1..44; identity activate_slide on 9/12/27.
- Paint-ready canvases: slide 9 → 1, slide 12 → 1, slide 27 → 2.
- Console warn/error count: 0.
- **Result: PASS**.

#### #138 / #158 — slide 28 FDIC callout + pane titles

- One shared-column FDIC callout lines: `92% FDIC` / `insured at` / `Q1'26`; badges=[].
- No pseudo top_total; pane titles Funding Mix + Deposit Programs; subtitles `$ in billions` ×2.
- Two independent pane charts; stack totals independent.
- SVG parity PASS.
- **Result: PASS**.

#### #139 / #150 — slide 17 typography + auto sizes

- Semantic pane titles @40px: Net Card Fees ($B), YoY Growth %.
- yTick=24 both panes; painted datalabels n=8/9; titlePlugin=false; clipping=false.
- Handoff `typography.mode=auto` both panes retained.
- **Result: PASS**.

#### #140 — slide 3 pill board + negative controls

- Five-row board geometry vs PDF targets within ±4px (board x/y/w/h).
- Class may include `gl-pill-free` + empty head stub; **geometry is authoritative**.
- Slide 20: pill layout exists but **not** fixed five-row board geometry.
- Slide 24: layout `grouped_bar_chart`, hasBoard=false.
- **Result: PASS**.

#### #147 — slide 12 pane headings

- paint-ready PASS; no duplicate internal chart title PASS.
- explicit left/right pane headings **FAIL** both modes: `paneTitles=[]`; heroes only (66%/73% copy).
- Ownership: **handoff** — canonical fixture lacks headings; mutations do not add them.
- SBS confirms PDF has dual titled panels; HTML has stacked bars + hero stats without those pane titles.
- **Result: PARTIAL** (renderer paints supplied content; heading content missing upstream).

#### #148 — slides 13–14 vertical bars + pane order

- Slide 13: indexAxis=x, series Total Balances + Billed Business.
- Slide 14: pane order 30+ Days Past Due then Net Write-Off Rates; both vertical.
- **Result: PASS**.

#### #151 — slide 18 boxed labels + driver card

- chart_hero_dual + driver_card (4 rows) including Margin 5%.
- Five boxed YoY labels painted 11/12/12/12/12%; nDS=1 bar; comboLine=false.
- **Result: PASS**.

#### #152 — gridlines default off

- Ordinary plot gridlines off on slides 9/13/15/18 Chart.js + SVG.
- Mixed-sign domain retains zero context (yMin negative, includesZero).
- Axes / support borders remain.
- **Result: PASS**.

#### #153 — slide 26 Q1'26 matrix orientation

- Heads observed: Category / YoY Growth / % of Total Billed Business; hasQ126=false.
- PDF expects period-as-column with Q1'26 header row orientation.
- Values numerically consistent with PDF but **transposed**.
- Ownership: **handoff** — fixture still v10 matrix; mutations lack #153.
- **Result: FAIL** (content/orientation; renderer faithful to bad input).

#### #154 — slide 24 growth brackets + $486B

- six bars; three painted semantic group brackets; aligned support % cells.
- exact `$486B Total Network Volumes`; FX-adjusted note present.
- **Result: PASS**.

#### #155 — slide 21 capital return composition

- stacked Dividends + Share Repurchases; shares line [702…682].
- ROE support 35/34/36/36/34/35%; four right-side KPIs.
- **Result: PASS**.

#### #156 — slide 27 macro scenarios

- two paint-ready panes; labels Q1'25–Q1'28; three scenarios each pane.
- titles Unemployment + GDP; E0026 source citation; SAAR in disclosure HTML.
- **Result: PASS**.

#### #157 — slides 33–37 annex matrices

- Each annex: matrix stubs present, correct unit strings, FX footnote/context.
- 30/30 checks PASS across chartjs+svg.
- **Result: PASS**.

#### #159 — slide 32 grouped annex heading IDs

- two peer tables; headings Commercial Services / International Card Services.
- deck-unique IDs `gl-grouped-annex-heading-32-0`, `…-32-1`.
- **Result: PASS**.

---

## 3. Full 44-page qualitative ledger

Each row links its SBS. Classifications are qualitative only (no image scores).

| # | layout | pdf_idx | physical | SBS | Class | Observation |
|--:|--------|--------:|----------|-----|-------|-------------|
| 1 | `brand_cover` | 0 | P1 | `comparison/sbs/sbs_slide01_P01_idx00_brand_cover.png` | **accepted divergence** | Brand cover uses generic seal_lockup + two-tone diagonal recipe vs PDF left-title + large Centurion watermark (brand-asset exclusion / wontfix). |
| 2 | `ir_bullet_sheet` | 1 | P2 | `comparison/sbs/sbs_slide02_P02_idx01_ir_bullet_sheet.png` | **accepted divergence** | IR bullet sheet denser line-items + disclosure chip vs PDF large bullets; content present, recipe weight differs (accepted IR density). |
| 3 | `pill_comparison` | 2 | P3 | `comparison/sbs/sbs_slide03_P03_idx02_pill_comparison.png` | **solved-ticket verification** | #140 five-row pill board: board geometry holds vs PDF targets (+/-4px); five stubs present; geometry PASS (class may include gl-pill-free; geometry is authoritative). |
| 4 | `line_chart` | 3 | P4 | `comparison/sbs/sbs_slide04_P04_idx03_line_chart.png` | **no material new finding** | Line chart series and labels track PDF; axis/label chrome differs slightly within house recipe. |
| 5 | `line_chart` | 4 | P5 | `comparison/sbs/sbs_slide05_P05_idx04_line_chart.png` | **no material new finding** | U.S. Consumer billed business line + callouts present; no new geometry residual beyond prior accepted callout silhouette locks. |
| 6 | `multi_panel` | 5 | P6 | `comparison/sbs/sbs_slide06_P06_idx05_multi_panel.png` | **no material new finding** | Multi-panel spend/performance tiles render; pane titles HTML-owned where configured. |
| 7 | `three_column_comparison` | 6 | P7 | `comparison/sbs/sbs_slide07_P07_idx06_three_column_comparison.png` | **no material new finding** | Three-column membership comparison furniture present; packing differs cosmetically from PDF. |
| 8 | `metric_row_with_breakdown` | 7 | P8 | `comparison/sbs/sbs_slide08_P08_idx07_metric_row_with_breakdown.png` | **no material new finding** | Metric row + breakdown renders; no new evidence-backed gap. |
| 9 | `line_chart` | 8 | P9 | `comparison/sbs/sbs_slide09_P09_idx08_line_chart.png` | **solved-ticket verification** | #137/#146 paint-ready: formerly blank risk — 1 canvas paint-ready under activate_slide; identity HOLD. |
| 10 | `line_chart` | 9 | P10 | `comparison/sbs/sbs_slide10_P10_idx09_line_chart.png` | **no material new finding** | ICS billed business line chart tracks PDF narrative. |
| 11 | `line_chart` | 10 | P11 | `comparison/sbs/sbs_slide11_P11_idx10_line_chart.png` | **no material new finding** | Transaction growth line chart tracks PDF narrative. |
| 12 | `chart_hero_dual` | 11 | P12 | `comparison/sbs/sbs_slide12_P12_idx11_chart_hero_dual.png` | **source/content residual** | #147 partial: chart_hero_dual paints 66%/73% heroes + stacked NCA bars paint-ready (ex-blank #146 PASS), but canonical handoff lacks explicit left/right pane headings/subtitles (PDF has 'Proprietary New Cards Acquired' / 'Proprietary New Accounts Acquired'); mutations do not author them. No duplicate Chart.js title plugin. |
| 13 | `grouped_bar_chart` | 12 | P13 | `comparison/sbs/sbs_slide13_P13_idx12_grouped_bar_chart.png` | **solved-ticket verification** | #148 vertical grouped bars (indexAxis=x) Total Balances + Billed Business after mutation; paint-ready. |
| 14 | `dual_chart` | 13 | P14 | `comparison/sbs/sbs_slide14_P14_idx13_dual_chart.png` | **solved-ticket verification** | #148 dual_chart pane order 30+ Days Past Due then Net Write-Off Rates; both panes vertical bars. |
| 15 | `stacked_bar_chart` | 14 | P15 | `comparison/sbs/sbs_slide15_P15_idx14_stacked_bar_chart.png` | **solved-ticket verification** | #136/#149 outlined_boxes: max |cell_cx-bar_cx|=0.188px Chart.js (<=12); label lane gap_px=0.0 vs first value cell; SVG parity. Source reserve-rate values still differ slightly from PDF (source). |
| 16 | `data_table` | 15 | P16 | `comparison/sbs/sbs_slide16_P16_idx15_data_table.png` | **no material new finding** | Revenue performance data table renders. |
| 17 | `dual_chart` | 16 | P17 | `comparison/sbs/sbs_slide17_P17_idx16_dual_chart.png` | **solved-ticket verification** | #139/#150: two HTML pane titles Net Card Fees ($B)/YoY Growth % @40px; y ticks 24; painted datalabels both panes; typography.mode=auto; no title-plugin duplicate; no clipping. |
| 18 | `chart_hero_dual` | 17 | P18 | `comparison/sbs/sbs_slide18_P18_idx17_chart_hero_dual.png` | **solved-ticket verification** | #151 chart_hero_dual: five boxed YoY labels 11/12/12/12/12%; four-row driver card includes Margin 5%; no synthetic combo YoY line (nDS=1 bar only). Cosmetic: PDF exterior boxed labels vs in-bar paint — accepted recipe. |
| 19 | `line_chart` | 18 | P19 | `comparison/sbs/sbs_slide19_P19_idx18_line_chart.png` | **no material new finding** | Total revenues net of interest expense line chart present. |
| 20 | `pill_comparison` | 19 | P20 | `comparison/sbs/sbs_slide20_P20_idx19_pill_comparison.png` | **solved-ticket verification** | #140 negative control: slide 20 pill path does not match fixed five-row board geometry selector. |
| 21 | `chart_hero_dual` | 20 | P21 | `comparison/sbs/sbs_slide21_P21_idx20_chart_hero_dual.png` | **solved-ticket verification** | #155 capital chart_hero_dual: stacked Dividends+Share Repurchases; shares line 702->682; ROE 35/34/36/36/34/35%; four right-side KPIs. Cosmetic stack color order / KPI wording vs PDF — content present, recipe chrome differs (accepted). |
| 22 | `guidance_statement_card` | 21 | P22 | `comparison/sbs/sbs_slide22_P22_idx21_guidance_statement_card.png` | **no material new finding** | 2026 guidance statement card present. |
| 23 | `brand_divider` | 22 | P23 | `comparison/sbs/sbs_slide23_P23_idx22_brand_divider.png` | **accepted divergence** | Appendix divider brand treatment differs from PDF full-bleed art (brand recipe). |
| 24 | `grouped_bar_chart` | 23 | P24 | `comparison/sbs/sbs_slide24_P24_idx23_grouped_bar_chart.png` | **solved-ticket verification** | #154 six bars + three painted group brackets + aligned support row + exact '$486B Total Network Volumes' + FX note; #140 neg control not fixed pill board. Bracket silhouette differs from PDF dashed callout boxes (accepted recipe). |
| 25 | `data_table` | 24 | P25 | `comparison/sbs/sbs_slide25_P25_idx24_data_table.png` | **no material new finding** | FX impact table present. |
| 26 | `data_table` | 25 | P26 | `comparison/sbs/sbs_slide26_P26_idx25_data_table.png` | **source/content residual** | #153 FAIL: handoff still category-row matrix (Category/YoY/% of Total) vs PDF period-column orientation with Q1'26 header; values match but matrix is transposed. amex_handoff_mutations.py does not include #153. Renderer correctly renders the supplied table. |
| 27 | `dual_chart` | 26 | P27 | `comparison/sbs/sbs_slide27_P27_idx26_dual_chart.png` | **solved-ticket verification** | #156 two paint-ready panes; Q1'25-Q1'28; three scenarios each; Unemployment+GDP titles; E0026/PDF page 27 citation; SAAR note in disclosure HTML (not above-fold innerText). #137/#146 ex-blank recheck PASS (2 charts). |
| 28 | `multi_panel` | 27 | P28 | `comparison/sbs/sbs_slide28_P28_idx27_multi_panel.png` | **solved-ticket verification** | #138/#158 one shared-column FDIC callout (92% FDIC / insured at / Q1'26); no pseudo top_total/duplicate badge; pane titles Funding Mix + Deposit Programs with $ in billions subtitles; independent stack totals. |
| 29 | `freeform_grid` | 28 | P29 | `comparison/sbs/sbs_slide29_P29_idx28_freeform_grid.png` | **source/content residual** | freeform_grid from split_text_visual handoff alias — variance commentary packing differs from PDF two-column art; content-driven. |
| 30 | `freeform_grid` | 29 | P30 | `comparison/sbs/sbs_slide30_P30_idx29_freeform_grid.png` | **source/content residual** | Continuation variance commentary; same freeform_grid alias note as s29. |
| 31 | `annex_table` | 30 | P31 | `comparison/sbs/sbs_slide31_P31_idx30_annex_table.png` | **no material new finding** | Annex 1 table navy headers; structure matches IR annex recipe. |
| 32 | `grouped_annex_table` | 31 | P32 | `comparison/sbs/sbs_slide32_P32_idx31_grouped_annex_table.png` | **solved-ticket verification** | #159 two peer grouped annex tables with deck-unique heading IDs gl-grouped-annex-heading-32-0/1 (Commercial Services / International Card Services). |
| 33 | `annex_table` | 32 | P33 | `comparison/sbs/sbs_slide33_P33_idx32_annex_table.png` | **solved-ticket verification** | #157 annex matrix present with stubs, units, FX footnote context. |
| 34 | `annex_table` | 33 | P34 | `comparison/sbs/sbs_slide34_P34_idx33_annex_table.png` | **solved-ticket verification** | #157 annex matrix present with stubs, units, FX footnote context. |
| 35 | `annex_table` | 34 | P35 | `comparison/sbs/sbs_slide35_P35_idx34_annex_table.png` | **solved-ticket verification** | #157 annex matrix present with stubs, units, FX footnote context. |
| 36 | `annex_table` | 35 | P36 | `comparison/sbs/sbs_slide36_P36_idx35_annex_table.png` | **solved-ticket verification** | #157 annex matrix present with stubs, units, FX footnote context. |
| 37 | `annex_table` | 36 | P37 | `comparison/sbs/sbs_slide37_P37_idx36_annex_table.png` | **solved-ticket verification** | #157 annex matrix present with stubs, units, FX footnote context. |
| 38 | `freeform_grid` | 37 | P38 | `comparison/sbs/sbs_slide38_P38_idx37_freeform_grid.png` | **accepted divergence** | Forward-looking statements freeform_grid vs PDF legal layout — content complete, packing recipe differs. |
| 39 | `freeform_grid` | 38 | P39 | `comparison/sbs/sbs_slide39_P39_idx38_freeform_grid.png` | **accepted divergence** | FLS continuation; same accepted packing divergence. |
| 40 | `freeform_grid` | 39 | P40 | `comparison/sbs/sbs_slide40_P40_idx39_freeform_grid.png` | **accepted divergence** | FLS continuation; same accepted packing divergence. |
| 41 | `freeform_grid` | 40 | P41 | `comparison/sbs/sbs_slide41_P41_idx40_freeform_grid.png` | **accepted divergence** | FLS continuation; same accepted packing divergence. |
| 42 | `freeform_grid` | 41 | P42 | `comparison/sbs/sbs_slide42_P42_idx41_freeform_grid.png` | **accepted divergence** | FLS continuation; same accepted packing divergence. |
| 43 | `freeform_grid` | 42 | P43 | `comparison/sbs/sbs_slide43_P43_idx42_freeform_grid.png` | **accepted divergence** | FLS continuation; same accepted packing divergence. |
| 44 | `brand_divider` | 43 | P44 | `comparison/sbs/sbs_slide44_P44_idx43_brand_divider.png` | **accepted divergence** | Closing brand divider vs PDF end card — seal_lockup generic mark (brand exclusion). |

### Manifest summary

- Viewport: 1920×1080
- all_artifacts_present: **True**
- contact_sheet: `comparison/contact_sheet.png`
- capture_contract: {"activate_slide": true, "wait_for_paint_ready_charts": true, "no_nth_selectors": true, "no_fixed_sleeps": true}
- no_image_scoring: **True**

---

## 4. v10 → v11 delta

| Area | v10 | v11 |
|------|-----|-----|
| Renderer commit | `00d4eb0` (v10 launcher era) | `af3662b` current main (includes #136–#159 ship + #173/#174) |
| Handoff | v9 archive + limited closed-ticket settings (#138/#139) | Canonical `amex_v10_44_slide_handoff.json` + full `amex_handoff_mutations.py` |
| Scorecard span | #136–#140 only | **#136–#159** complete |
| Capture | activate_slide + painted datalabels | + mandatory `wait_for_paint_ready_charts`; ex-blank 9/12/27 recheck |
| #148 13–14 | line/dual without forced vertical mutation story | **PASS** vertical bars + pane order after mutation |
| #151 slide 18 | combo_chart narrative | **PASS** chart_hero_dual + boxed labels + driver_card Margin 5% |
| #154 slide 24 | data_table / pill neg control only | **PASS** grouped_bar + 3 brackets + $486B support |
| #155 slide 21 | multi_panel capital tiles | **PASS** chart_hero_dual capital return composition |
| #156 slide 27 | dual_chart present | **PASS** full scenario/horizon/citation/SAAR checks; paint-ready |
| #157/#159 annex | structural presence | **PASS** units/FX + grouped heading IDs |
| #147 slide 12 | source residual (missing left stacked pairing called out) | Still **handoff residual** on pane headings; bars+heroes now paint-ready |
| #153 slide 26 | not in v10 closed set | **New explicit FAIL** — fixture matrix still transposed |
| Image scoring | none | none |

### Solved since v10 (evidence-backed)

- Paint-ready capture contract holds on formerly blank slides **9, 12, 27** (#146).
- Slide **13–14** vertical bar semantics after mutations (#148).
- Slide **18** Premium Lending driver_card + boxed YoY labels without combo line (#151).
- Slide **21** capital return stack + shares line + ROE + KPIs (#155 / #174).
- Slide **24** six-bar growth with three brackets + $486B support (#154).
- Slide **27** full macro scenario dual panes with citation (#156).
- Slide **28** FDIC shared callout + pane titles without badge chrome (#138/#158).
- Slides **32–37** annex grouping IDs + matrix units/FX (#157/#159).
- Default ordinary gridlines off with zero-line retention (#152).
- Slide **15** outlined support alignment still ≤12px; label lane non-overlap (#136/#149).
- Slide **17** auto typography + semantic pane titles (#139/#150).
- Slide **3** fixed pill-board geometry with 20/24 negative controls (#140).

---

## 5. Residual triage

Only residuals with **fresh v11 evidence**. No fixes designed or filed.

### 5.1 Still-open evidence-backed renderer residuals

**None proven in this run.**

Every closed-ticket geometry/DOM failure traced to missing or transposed handoff content (#147, #153). Cosmetic recipe differences (brand covers, FLS packing, bracket silhouette vs dashed PDF callouts, in-bar vs exterior YoY boxes) are accepted recipe divergence, not capability defects under the shipped contracts.

### 5.2 Still-open handoff / source residuals

| ID | Location | Impact | Likely ownership | Smallest next verification |
|----|----------|--------|------------------|----------------------------|
| H1 #147 | slide 12 / P12 `chart_hero_dual` | PDF pane titles/subtitles ('Proprietary New Cards/Accounts Acquired') absent in HTML; heroes 66%/73% present | Canonical fixture + `amex_handoff_mutations.py` (no #147 authoring) | Add left/right `heading`+`subtitle` on primary/secondary visuals in fixture or mutation; re-run #147 probe only |
| H2 #153 | slide 26 / P26 `data_table` | Matrix transposed: category rows vs PDF Q1'26 period columns; values match but orientation wrong | Canonical fixture still v10 matrix; mutations lack #153 | Replace slide 26 table with period-column orientation including visible Q1'26 context; re-run #153 probe |
| H3 historical pairing note | slide 12 | PDF left panel is titled stacked NCA; HTML supplies stacked bars without those titles (related to H1) | handoff content pairing | Covered by H1 verification |
| H4 freeform variance | slides 29–30 | freeform_grid packing vs PDF two-column variance art | handoff `split_text_visual` → recipe alias | Content completeness check only; not a renderer geometry ticket |

### 5.3 Accepted / non-actionable differences

- Brand covers / dividers (slides 1, 23, 44): generic seal_lockup vs Centurion/full-bleed art — brand-asset exclusion.
- IR bullet density (slide 2) and FLS freeform packing (38–43): recipe weight, content complete.
- Slide 18: exterior PDF YoY callout boxes vs in-plot boxed datalabels — shipped #151 contract met.
- Slide 21: stack series color order / KPI microcopy vs PDF — composition contract met.
- Slide 24: group bracket chrome vs PDF dashed multi-box callouts — three semantic brackets painted.
- Slide 15: minor reserve-rate source value drift vs PDF — source/content, alignment geometry PASS.
- Known layout alias `split_text_visual` → `freeform_grid` (29,30,38–43): not an identity break.

### 5.4 Screenshot / probe failures

**None.** All 44 comparison rows `artifacts_exist=true`, paint_ready.ok where charts present, manifest warnings=0. Closed-ticket fails are assertion failures on handoff content, not capture failures.

### 5.5 What renderer_v2 now does well

- Identity-safe, paint-ready Chart.js capture across a 44-slide IR deck, including dual-pane macros.
- Outlined support-cell ↔ bar centre alignment at sub-pixel error with non-overlapping label lanes.
- Shared-column side callouts without badge/top_total duplication.
- Auto typography on dual charts with HTML-owned pane titles (no Chart.js title-plugin fallback).
- chart_hero_dual compositions: driver cards, boxed bar labels, capital return stack+line+ROE+KPI.
- Grouped bar brackets + aligned footer support rows with exact total copy.
- Default gridline suppression while preserving axes, support borders, and semantic zero lines.
- Annex tables with units, FX footnotes, and deck-unique grouped heading IDs.
- JS-off/SVG parity on the closed-ticket geometry surface area exercised here.

---

## 6. Diagnostics & artifact index

| Artifact | Path |
|----------|------|
| GAP (simulation) | `simulation/amex_q1_2026/GAP_ANALYSIS.md` |
| GAP (wiki copy) | `wiki/baseline_v11_GAP_ANALYSIS.md` |
| Handoff pre | `passes/pass_01/handoff.pre_mutations.json` |
| Handoff post | `passes/pass_01/handoff.json` |
| Handoff assertion | `handoff_assertion.json` |
| Page/slide map | `page_slide_mapping.json` |
| Rendered HTML | `passes/pass_01/output/presentation.html` |
| run_meta | `passes/pass_01/output/run_meta.json` |
| Comparison manifest | `comparison_manifest.json` |
| PDF rasters (44) | `comparison/pdf/` |
| HTML shots (44) | `comparison/html/` |
| SBS (44) | `comparison/sbs/` |
| Contact sheet | `comparison/contact_sheet.png` |
| Qualitative ledger JSON | `comparison/qualitative_ledger_v11.json` |
| Scorecard | `closed_tickets/scorecard_136_159.json` |
| Probe results | `closed_tickets/closed_ticket_results_v11.json` |
| Probe raw | `closed_tickets/closed_ticket_raw_v11.json` |
| Focused tests | `closed_tickets/focused_tests_summary.json` |
| Probes | `probes/build_full_comparison.py`, `probes/v11_closed_ticket_probes.py` |
| Prior v10 extract | `extracted/baseline_v10_GAP_ANALYSIS.md` |

**run_meta:** generator=impact_slides.renderer_v2 v2.0.0; style=BoardroomEarnings; total_slides=44; html_bytes=754828; delivery=self-contained.

---

## 7. Stop proofs (pre-commit checklist)

| Proof | Status |
|-------|--------|
| 44 PDF + 44 HTML + 44 SBS exist | HOLD |
| comparison_manifest all_artifacts_present | HOLD |
| #136–#159 scorecard rows with fresh evidence | HOLD |
| No MAE/similarity/pixel-diff scoring | HOLD |
| No production/test/script/config path changed | HOLD (observation run) |
| Report byte-identical sim ↔ wiki | enforced at docs commit |
| Exactly two allowed commits | sim artifacts, then wiki report |

*End of v11 observation baseline. Companion-mode only — no fixes, no tickets filed.*
