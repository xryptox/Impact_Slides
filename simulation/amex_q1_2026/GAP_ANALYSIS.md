# Gap Analysis v10: renderer_v2 vs Amex Q1'26 Earnings PDF

**(Closed-ticket revalidation + full 44-page PDF↔HTML comparison — observation only)**

**Simulation:** `simulation/amex_q1_2026/`  
**Source of truth:** `C:\Users\Ag1Le\Downloads\Q1-2026-Earnings-Presentation.pdf`  
**PDF identity:** SHA-256 `a87c11625c84e0dabb02d523f6a2d2508b892f18ee242ef197a9b40157bd3faf` · 44 pages · page0 rect 959.76×540  
**Renderer under test:** `impact_slides.renderer_v2` @ `00d4eb0` (`00d4eb05a2bba47123f6deaef984b9722fdabe6b`) — current main line; **no production edits this run**  
**Prior baseline:** `wiki/baseline_v9_GAP_ANALYSIS.md`  
**Handoff source:** v9 archive `gnhf/objective-produce-a-2d5e02:simulation/amex_q1_2026/passes/pass_01/handoff.json`  
  → copied to `simulation/amex_q1_2026/passes/pass_01/handoff.json` then **only** closed-ticket settings applied (#138 side_callout, #139 typography; #136/#140 unchanged inputs).  
**Method:** Playwright geometry via `scripts/simulation_probe.py` (`activate_slide`, `painted_datalabel_lines`) + 1920×1080 full-resolution PDF/HTML side-by-sides. House tol ±4px; #136 centres ≤12px.  
**No MAE / similarity percent / pixel-diff scores / heatmaps.**

---

## 1. Scope gate, mapping assertion, run identity

| Gate | Result |
|------|--------|
| Renderer commit | `00d4eb0` — chore: add v10 Amex GNHF comparison launcher (main HEAD at sim start) |
| Production paths touched | **None** (`impact_slides/`, schemas, CSS, tests untouched) |
| Handoff | Single pass_01; no speculative pass_02 tuning |
| PDF pages | 44 |
| HTML `data-slide-number` unique values | 44 (1…44) |
| Identity map | **HTML slide N → PDF index N−1 → physical page N** |
| Mapping assertion | **HOLD** with recipe alias note below |
| Scope-gate | PASS — only `simulation/amex_q1_2026/**` artifacts written this run; no `impact_slides/` production edits; wiki report is the sole tracked doc add. |

### Page / slide mapping assertion

Handoff `layout_type=split_text_visual` renders as HTML `data-layout=freeform_grid` on slides [29, 30, 38, 39, 40, 41, 42, 43] — known recipe alias, not an identity break. Numeric identity HTML slide N ↔ PDF index N−1 ↔ physical page N holds for all 44.

Full row dump: `simulation/amex_q1_2026/page_slide_mapping.json`.

Every artifact name and scorecard row carries `slide_number`, `expected_layout` (HTML `data-layout`), `pdf_page_index`, `pdf_physical_page`.

### #137 process compliance

| Requirement | Evidence |
|-------------|----------|
| `activate_slide(page, slide_number, expected_layout)` only | `simulation/amex_q1_2026/probes/build_full_comparison.py`, `closed_ticket_probes.py` |
| No `section.slide[i]` / nth / scrollIntoView activation | Confirmed in probe sources |
| JSON rows include `slide_number` + `layout` | `closed_tickets/closed_ticket_results.json`, `comparison_manifest.json` |
| Zero selector match = probe failure | `ProbeError` paths; no successful empty observations |
| Painted datalabels via `painted_datalabel_lines` | #139 Chart.js panes |
| 1920×1080 readiness wait before shots | Full comparison + closed-ticket probes |
| Console / run_meta captured with identity | manifest `warnings` (0); run_meta at `passes/pass_01/output/run_meta.json` |

**#137 verdict: PASS (tooling contract).**

---

## 2. Closed-ticket scorecard (#136–#140)

### #136 — slide 15 / stacked_bar_chart / PDF P15 — outlined_boxes alignment

| Field | Detail |
|-------|--------|
| Settings applied | Unchanged list-of-lists primary `steps_or_data`; `secondary_visual.skin: outlined_boxes` retained (no mapping-object conversion). |
| Chart.js | Alignment marker `chart-table-aligned` **on**. Five outlined-box centres vs Chart.js bar centres; max \|Δ\| = **0.203px** (deltas [0.016, 0.062, 0.109, 0.156, 0.203]). Acceptance ≤12px → **PASS**. |
| JS-off/SVG | Live `svg.chart-svg` bar centres (JS-off). max \|Δ\| = **0.016px** (deltas [0.016, 0.005, 0.01, 0.0, 0.005]). ≤12px → **PASS**. |
| Artifacts | `closed_tickets/closed_ticket_results.json` · shots `closed_tickets/shots/chartjs_slide15_*.png`, `svg_slide15_*.png` · SBS `comparison/sbs/sbs_slide15_P15_idx14_stacked_bar_chart.png` |
| **Verdict** | **PASS both modes** |

### #137 — tooling / identity contract

| Field | Detail |
|-------|--------|
| Settings applied | N/A (no handoff knob) — probe contract only. |
| Chart.js | All Chart.js probes used `activate_slide` + identity fields. |
| JS-off/SVG | All SVG probes used same activation contract with `java_script_enabled=False`. |
| Artifacts | Probe sources under `simulation/amex_q1_2026/probes/` |
| **Verdict** | **PASS** |

### #138 — slide 28 / multi_panel / PDF P28 — Deposit Programs side_callout

| Field | Detail |
|-------|--------|
| Settings applied | Added `chart_config.side_callout: {"value":"92% FDIC","label":["insured at","Q1'26"],"placement":"right","skin":"tall"}` on Deposit Programs tile only; source badge string kept; exterior names, 150px gutter, density, `stack_total_labels: ["$151","$157"]` unchanged. |
| Chart.js | Exactly one unboxed three-line callout; no non-callout FDIC badge; exterior segmentNames items present; $151/$157 independent; tile-local top 50.80px (δ 0.997 vs 49.8); no callout↔plot overlap. **PASS** 7/7. |
| JS-off/SVG | Same DOM callout path under JS-off (HTML chrome). Exterior names recovered from embedded `chartjs-config` segmentNames. **PASS** 7/7. |
| Artifacts | `closed_tickets/shots/*_slide28_*.png` · SBS `comparison/sbs/sbs_slide28_P28_idx27_multi_panel.png` |
| **Verdict** | **PASS both modes** |

### #139 — slide 17 / dual_chart / PDF P17 — chart_config.typography

| Field | Detail |
|-------|--------|
| Settings applied | Both panes: `typography: {y_tick_font_size: 24, datalabel_font_size: 28}`; x ticks left at legacy. |
| Chart.js | Two HTML `.gl-chart-pane-title` @ 40px/700 navy; no Chart.js title plugin; y ticks 24 bold both panes; painted datalabel model font 28 on all labels (pane0 8 lines, pane1 9 lines); x autoSkip=true, rotation 0 recorded; no unsupported typography warnings; no clipping. **PASS** 11/11. |
| JS-off/SVG | HTML pane titles retained JS-off; SVG text audit recorded; no duplicate SVG titles matching pane titles. **PASS** 5/5. |
| Artifacts | `closed_tickets/shots/*_slide17_*.png` · SBS `comparison/sbs/sbs_slide17_P17_idx16_dual_chart.png` |
| **Verdict** | **PASS both modes** |

### #140 — slide 3 / pill_comparison / PDF P3 — five-row fixed board (no new knob)

| Field | Detail |
|-------|--------|
| Settings applied | No handoff knob. Merged CSS recipe on direct five-body-row board. |
| Chart.js | Board/shell/cap vs approved targets: board.x Δ=-0.015; board.y Δ=-0.008; board.w Δ=-0.005; board.h Δ=-0.015; first_shell.x Δ=-0.029; first_shell.y Δ=-0.008; first_shell.w Δ=-0.008; cap height Δ=-0.013. Five body label rows present; no slide overflow. Slide 20 & 24 negative controls: fixed-board selector **not** matched; legacy/inset paths retained. **PASS** 16/16. |
| JS-off/SVG | Same geometry JS-off (pure HTML/CSS): board.x Δ=-0.015; board.y Δ=-0.008; board.w Δ=-0.005; board.h Δ=-0.015; first_shell.x Δ=-0.029; first_shell.y Δ=-0.008; first_shell.w Δ=-0.008; cap height Δ=-0.013. Negative controls identical. **PASS** 16/16. |
| Artifacts | `closed_tickets/shots/*_slide03_*.png` · SBS `comparison/sbs/sbs_slide03_P03_idx02_pill_comparison.png` |
| **Verdict** | **PASS both modes** |

### Scorecard summary

| Ticket | Chart.js | SVG | Overall |
|--------|----------|-----|---------|
| #136 | PASS (max Δ 0.203px) | PASS (max Δ 0.016px) | **PASS** |
| #137 | contract used | contract used | **PASS** |
| #138 | PASS 7/7 | PASS 7/7 | **PASS** |
| #139 | PASS 11/11 | PASS 5/5 | **PASS** |
| #140 | PASS 16/16 | PASS 16/16 | **PASS** |

Raw checks: `78/78` passed · `closed_tickets/closed_ticket_results.json`.

---

## 3. Full 44-page PDF ↔ HTML qualitative ledger

**Rasterization:** every PDF page via PyMuPDF matrix `1920/page.rect.width` × `1080/page.rect.height` (native page size → exact 1920×1080, not screenshot-resize).  
**HTML:** every slide activated by identity contract at 1920×1080 after chart readiness.  
**SBS:** full-resolution PDF left | HTML right, header `PDF physical P (index I) | HTML slide N | layout` — no downscale of either half.  
**Contact sheet:** `comparison/contact_sheet.png`.  
**Manifest:** `comparison_manifest.json` — artifact existence only (**not** a score). `all_artifacts_present: True`.

| slide | layout | pdf_idx | physical | full-res SBS | category | qualitative note |
|------:|--------|--------:|----------|--------------|----------|------------------|
| 1 | brand_cover | 0 | P1 | `comparison/sbs/sbs_slide01_P01_idx00_brand_cover.png` | **accepted divergence** | Brand cover uses generic seal_lockup + two-tone diagonal recipe vs PDF left-title + large Centurion watermark (R3 brand-asset exclusion / wontfix). |
| 2 | ir_bullet_sheet | 1 | P2 | `comparison/sbs/sbs_slide02_P02_idx01_ir_bullet_sheet.png` | **accepted divergence** | IR bullet sheet denser line-items + disclosure chip vs PDF large bullets; content present, recipe weight differs (accepted IR density). |
| 3 | pill_comparison | 2 | P3 | `comparison/sbs/sbs_slide03_P03_idx02_pill_comparison.png` | **closed-ticket verification** | #140 five-row pill board: board/shell/cap deltas ≤0.03px vs approved PDF targets; YoY two-line cap retained; geometry PASS both modes. |
| 4 | line_chart | 3 | P4 | `comparison/sbs/sbs_slide04_P04_idx03_line_chart.png` | **no material new finding** | Line chart series and labels track PDF; axis/label chrome differs slightly within house recipe. |
| 5 | line_chart | 4 | P5 | `comparison/sbs/sbs_slide05_P05_idx04_line_chart.png` | **no material new finding** | U.S. Consumer billed business line + callouts present; no new geometry residual beyond prior accepted callout silhouette locks. |
| 6 | multi_panel | 5 | P6 | `comparison/sbs/sbs_slide06_P06_idx05_multi_panel.png` | **no material new finding** | Multi-panel Platinum performance tiles render; pane titles HTML-owned where configured. |
| 7 | three_column_comparison | 6 | P7 | `comparison/sbs/sbs_slide07_P07_idx06_three_column_comparison.png` | **no material new finding** | Three-column membership comparison furniture present; packing differs cosmetically from PDF. |
| 8 | metric_row_with_breakdown | 7 | P8 | `comparison/sbs/sbs_slide08_P08_idx07_metric_row_with_breakdown.png` | **no material new finding** | Metric row + breakdown renders; no new evidence-backed gap. |
| 9 | line_chart | 8 | P9 | `comparison/sbs/sbs_slide09_P09_idx08_line_chart.png` | **no material new finding** | Commercial Services line chart tracks PDF narrative. |
| 10 | line_chart | 9 | P10 | `comparison/sbs/sbs_slide10_P10_idx09_line_chart.png` | **no material new finding** | ICS billed business line chart tracks PDF narrative. |
| 11 | line_chart | 10 | P11 | `comparison/sbs/sbs_slide11_P11_idx10_line_chart.png` | **no material new finding** | Transaction growth line chart tracks PDF narrative. |
| 12 | chart_hero_dual | 11 | P12 | `comparison/sbs/sbs_slide12_P12_idx11_chart_hero_dual.png` | **source/content** | chart_hero_dual shows 66%/73% hero stats but left stacked NCA chart missing vs PDF dual-panel — handoff/source pairing residual (historical R4/N10 family), not a fresh closed-ticket miss. |
| 13 | line_chart | 12 | P13 | `comparison/sbs/sbs_slide13_P13_idx12_line_chart.png` | **no material new finding** | Balances and billed business line chart present. |
| 14 | dual_chart | 13 | P14 | `comparison/sbs/sbs_slide14_P14_idx13_dual_chart.png` | **no material new finding** | Credit metrics dual_chart with HTML pane titles; tracks PDF structure. |
| 15 | stacked_bar_chart | 14 | P15 | `comparison/sbs/sbs_slide15_P15_idx14_stacked_bar_chart.png` | **closed-ticket verification** | #136 outlined_boxes: chart-table-aligned marker on; max |cell_cx−bar_cx|=0.203px Chart.js / 0.016px SVG (≤12). List-of-lists primary retained. PDF reserve-rate source values differ slightly (source). |
| 16 | data_table | 15 | P16 | `comparison/sbs/sbs_slide16_P16_idx15_data_table.png` | **no material new finding** | Revenue performance data table renders. |
| 17 | dual_chart | 16 | P17 | `comparison/sbs/sbs_slide17_P17_idx16_dual_chart.png` | **closed-ticket verification** | #139 typography: two HTML pane titles 40px/700 navy; y ticks 24 bold; painted datalabels 28px both panes; no Chart title-plugin fallback. Measure-rule CAGR retained. |
| 18 | combo_chart | 17 | P18 | `comparison/sbs/sbs_slide18_P18_idx17_combo_chart.png` | **no material new finding** | Premium lending combo chart present. |
| 19 | line_chart | 18 | P19 | `comparison/sbs/sbs_slide19_P19_idx18_line_chart.png` | **no material new finding** | Total revenues line chart present. |
| 20 | pill_comparison | 19 | P20 | `comparison/sbs/sbs_slide20_P20_idx19_pill_comparison.png` | **closed-ticket verification** | #140 negative control: slide 20 inset/legacy pill path — does not match fixed five-row board selector; VCE callout retained as inset chrome. |
| 21 | multi_panel | 20 | P21 | `comparison/sbs/sbs_slide21_P21_idx20_multi_panel.png` | **no material new finding** | Capital multi_panel tiles present. |
| 22 | guidance_statement_card | 21 | P22 | `comparison/sbs/sbs_slide22_P22_idx21_guidance_statement_card.png` | **no material new finding** | 2026 guidance card present. |
| 23 | brand_divider | 22 | P23 | `comparison/sbs/sbs_slide23_P23_idx22_brand_divider.png` | **accepted divergence** | Appendix divider brand treatment differs from PDF full-bleed art (brand recipe). |
| 24 | data_table | 23 | P24 | `comparison/sbs/sbs_slide24_P24_idx23_data_table.png` | **closed-ticket verification** | #140 negative control: data_table with insets — not fixed pill-board selector; legacy table geometry retained. |
| 25 | data_table | 24 | P25 | `comparison/sbs/sbs_slide25_P25_idx24_data_table.png` | **no material new finding** | FX impact table present. |
| 26 | data_table | 25 | P26 | `comparison/sbs/sbs_slide26_P26_idx25_data_table.png` | **no material new finding** | T&E billed business table present. |
| 27 | dual_chart | 26 | P27 | `comparison/sbs/sbs_slide27_P27_idx26_dual_chart.png` | **no material new finding** | Credit reserve macro dual_chart present; exterior names where configured. |
| 28 | multi_panel | 27 | P28 | `comparison/sbs/sbs_slide28_P28_idx27_multi_panel.png` | **closed-ticket verification** | #138 Deposit Programs side_callout tall/right three-line unboxed; badge chrome suppressed; $151/$157 totals independent; tile-local top≈50.8px (δ0.997 to 49.8); exterior segment names via plugin config. |
| 29 | freeform_grid | 28 | P29 | `comparison/sbs/sbs_slide29_P29_idx28_freeform_grid.png` | **source/content** | freeform_grid from split_text_visual handoff alias — variance commentary packing differs from PDF two-column art; content-driven. |
| 30 | freeform_grid | 29 | P30 | `comparison/sbs/sbs_slide30_P30_idx29_freeform_grid.png` | **source/content** | Continuation variance commentary; same freeform_grid alias note as s29. |
| 31 | annex_table | 30 | P31 | `comparison/sbs/sbs_slide31_P31_idx30_annex_table.png` | **no material new finding** | Annex 1 table navy headers; structure matches IR annex recipe. |
| 32 | annex_table | 31 | P32 | `comparison/sbs/sbs_slide32_P32_idx31_annex_table.png` | **no material new finding** | Annex 1 cont. table present. |
| 33 | annex_table | 32 | P33 | `comparison/sbs/sbs_slide33_P33_idx32_annex_table.png` | **no material new finding** | Annex 2 table present. |
| 34 | annex_table | 33 | P34 | `comparison/sbs/sbs_slide34_P34_idx33_annex_table.png` | **no material new finding** | Annex 3 table present. |
| 35 | annex_table | 34 | P35 | `comparison/sbs/sbs_slide35_P35_idx34_annex_table.png` | **no material new finding** | Annex 4 table present. |
| 36 | annex_table | 35 | P36 | `comparison/sbs/sbs_slide36_P36_idx35_annex_table.png` | **no material new finding** | Annex 5 table present. |
| 37 | annex_table | 36 | P37 | `comparison/sbs/sbs_slide37_P37_idx36_annex_table.png` | **no material new finding** | Annex 6 table present. |
| 38 | freeform_grid | 37 | P38 | `comparison/sbs/sbs_slide38_P38_idx37_freeform_grid.png` | **accepted divergence** | Forward-looking statements freeform_grid vs PDF legal layout — content complete, packing recipe differs. |
| 39 | freeform_grid | 38 | P39 | `comparison/sbs/sbs_slide39_P39_idx38_freeform_grid.png` | **accepted divergence** | FLS continuation; same accepted packing divergence. |
| 40 | freeform_grid | 39 | P40 | `comparison/sbs/sbs_slide40_P40_idx39_freeform_grid.png` | **accepted divergence** | FLS continuation; same accepted packing divergence. |
| 41 | freeform_grid | 40 | P41 | `comparison/sbs/sbs_slide41_P41_idx40_freeform_grid.png` | **accepted divergence** | FLS continuation; same accepted packing divergence. |
| 42 | freeform_grid | 41 | P42 | `comparison/sbs/sbs_slide42_P42_idx41_freeform_grid.png` | **accepted divergence** | FLS continuation; same accepted packing divergence. |
| 43 | freeform_grid | 42 | P43 | `comparison/sbs/sbs_slide43_P43_idx42_freeform_grid.png` | **accepted divergence** | FLS continuation; same accepted packing divergence. |
| 44 | brand_divider | 43 | P44 | `comparison/sbs/sbs_slide44_P44_idx43_brand_divider.png` | **accepted divergence** | Closing brand divider vs PDF end card — seal_lockup generic mark (R3 exclusion). |

### Manifest summary

- Rows: 44
- All PDF+HTML+SBS present: **True**
- Viewport: 1920×1080
- Comparison root: `simulation/amex_q1_2026/comparison/{pdf,html,sbs}/`
- Closed-ticket runtime shots kept separate under `closed_tickets/shots/` (chartjs vs svg)

---

## 4. v9 → v10 delta

| Topic | v9 (historical) | v10 (fresh revalidation) |
|-------|-----------------|---------------------------|
| #136 / N6 outlined alignment | v9: list-shaped primary blocked plot-align (`aligned=false`); cell↔bar centres failed ≤12px | **PASS** both modes; `chart-table-aligned` on; max Δ 0.203px / 0.016px |
| #138 / N5 tall FDIC callout | v9: badge ≠ tall side callout residual | **PASS** structured `side_callout` paints; badge suppressed; totals independent |
| #139 / R6-A typography | v9: pane title ~13px gray residual | **PASS** 40px/700 navy HTML titles; 24px y ticks; 28px painted labels |
| #140 / F4+ pill board | v9: packing still weak vs PDF full board | **PASS** board/shell/cap within ±0.03px of approved targets |
| #137 probe contract | introduced post-v9 | **Used throughout** this baseline |
| Full 44 SBS | v9 focus-sample only | **Complete 44/44** full-res pairs + contact sheet + manifest |
| R3 brand seal | accepted / wontfix | unchanged accepted divergence (s1/s44) |
| R4 dual-metric / s12 hero chart | historical residual | **source/content** residual remains on s12 (left NCA chart absent in handoff) — not closed by #136–#140 |
| R1 / F12+ / N2 / R2 locks | accepted divergence locks | still accepted; not re-opened |

### Evidence-backed residuals only (not closed-ticket failures)

1. **s12 New Acquisitions** — handoff still omits left stacked NCA chart present in PDF (source/content / historical hero pairing).  
2. **Brand assets (s1/s44)** — generic `seal_lockup` vs Centurion art (R3 wontfix).  
3. **Legal/FLS freeform packing (s38–s43)** and **IR bullet density (s2)** — accepted recipe divergences, not new renderer defects.  
4. **s15 PDF reserve-rate source series** — PDF shows mostly 2.9% then 2.8%; handoff series is 2.9% + four×2.8% (source values), while **alignment geometry passes**.

No issues filed from this simulation.

---

## 5. #139 full-deck typography / pane-title audit

Ordinary Chart.js inspection (non-chart slides explicitly **not applicable**):

| slide | layout | pdf_idx | physical | pane_title_state | legacy_title_fallback | tick_rotation_skip | datalabel_suppression | unsupported_typography_warning | clipping |
|------:|--------|--------:|----------|------------------|----------------------|--------------------|----------------------|--------------------------------|----------|
| 1 | brand_cover | 0 | P1 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 2 | ir_bullet_sheet | 1 | P2 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 3 | pill_comparison | 2 | P3 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 4 | line_chart | 3 | P4 | none | pane0: plugin=False | pane0: rot=0 skip=True yTick=13 | pane0: painted=10 | none observed at probe time | False |
| 5 | line_chart | 4 | P5 | none | pane0: plugin=False | pane0: rot=0 skip=True yTick=13 | pane0: painted=5 | none observed at probe time | False |
| 6 | multi_panel | 5 | P6 | Spend Growth is Accelerating @ 40px/700 | pane0: plugin=False; pane1: plugin=False | pane0: rot=0 skip=True yTick=13; pane1: rot=0 skip=True yTick=13 | pane0: painted=5; pane1: painted=6 | none observed at probe time | False |
| 7 | three_column_comparison | 6 | P7 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 8 | metric_row_with_breakdown | 7 | P8 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 9 | line_chart | 8 | P9 | none | pane0: plugin=False | pane0: rot=0 skip=True yTick=13 | pane0: painted=5 | none observed at probe time | False |
| 10 | line_chart | 9 | P10 | none | pane0: plugin=False | pane0: rot=0 skip=True yTick=13 | pane0: painted=10 | none observed at probe time | False |
| 11 | line_chart | 10 | P11 | none | pane0: plugin=False | pane0: rot=0 skip=True yTick=13 | pane0: painted=5 | none observed at probe time | False |
| 12 | chart_hero_dual | 11 | P12 | none | pane0: plugin=False | pane0: rot=0 skip=True yTick=13 | pane0: painted=30 | none observed at probe time | False |
| 13 | line_chart | 12 | P13 | none | pane0: plugin=False | pane0: rot=0 skip=True yTick=13 | pane0: painted=10 | none observed at probe time | False |
| 14 | dual_chart | 13 | P14 | Net write-off rate @ 40px/700; 30+ days past due @ 40px/700 | pane0: plugin=False; pane1: plugin=False | pane0: rot=0 skip=True yTick=13; pane1: rot=0 skip=True yTick=13 | pane0: painted=5; pane1: painted=5 | none observed at probe time | False |
| 15 | stacked_bar_chart | 14 | P15 | none | pane0: plugin=False | pane0: rot=0 skip=True yTick=13 | pane0: painted=30 | none observed at probe time | False |
| 16 | data_table | 15 | P16 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 17 | dual_chart | 16 | P17 | Net Card Fees ($B) @ 40px/700; YoY Growth % @ 40px/700 | pane0: plugin=False; pane1: plugin=False | pane0: rot=0 skip=True yTick=24; pane1: rot=0 skip=True yTick=24 | pane0: painted=8; pane1: painted=9 | none observed at probe time | False |
| 18 | combo_chart | 17 | P18 | none | pane0: plugin=False | pane0: rot=0 skip=True yTick=13 | pane0: painted=10 | none observed at probe time | False |
| 19 | line_chart | 18 | P19 | none | pane0: plugin=False | pane0: rot=0 skip=True yTick=13 | pane0: painted=10 | none observed at probe time | False |
| 20 | pill_comparison | 19 | P20 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 21 | multi_panel | 20 | P21 | Capital composition @ 40px/700 | pane0: plugin=False | pane0: rot=0 skip=True yTick=13 | pane0: painted=12 | none observed at probe time | False |
| 22 | guidance_statement_card | 21 | P22 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 23 | brand_divider | 22 | P23 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 24 | data_table | 23 | P24 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 25 | data_table | 24 | P25 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 26 | data_table | 25 | P26 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 27 | dual_chart | 26 | P27 | none | pane0: plugin=False; pane1: plugin=False | pane0: rot=0 skip=True yTick=13; pane1: rot=0 skip=True yTick=13 | pane0: painted=16; pane1: painted=16 | none observed at probe time | False |
| 28 | multi_panel | 27 | P28 | Funding Mix @ 40px/700; Deposit Programs @ 40px/700 | pane0: plugin=False; pane1: plugin=False | pane0: rot=0 skip=True yTick=13; pane1: rot=0 skip=True yTick=13 | pane0: painted=12; pane1: painted=16 | none observed at probe time | False |
| 29 | freeform_grid | 28 | P29 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 30 | freeform_grid | 29 | P30 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 31 | annex_table | 30 | P31 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 32 | annex_table | 31 | P32 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 33 | annex_table | 32 | P33 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 34 | annex_table | 33 | P34 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 35 | annex_table | 34 | P35 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 36 | annex_table | 35 | P36 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 37 | annex_table | 36 | P37 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 38 | freeform_grid | 37 | P38 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 39 | freeform_grid | 38 | P39 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 40 | freeform_grid | 39 | P40 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 41 | freeform_grid | 40 | P41 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 42 | freeform_grid | 41 | P42 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 43 | freeform_grid | 42 | P43 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 44 | brand_divider | 43 | P44 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |

JS-off/SVG inspection (titles are HTML-owned; chart tick/datalabel fields n/a-js-off where Chart.js is absent):

| slide | layout | pdf_idx | physical | pane_title_state | legacy_title_fallback | tick_rotation_skip | datalabel_suppression | unsupported_typography_warning | clipping |
|------:|--------|--------:|----------|------------------|----------------------|--------------------|----------------------|--------------------------------|----------|
| 1 | brand_cover | 0 | P1 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 2 | ir_bullet_sheet | 1 | P2 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 3 | pill_comparison | 2 | P3 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 4 | line_chart | 3 | P4 | none | n/a-js-off | n/a-js-off | n/a-js-off | none observed at probe time | False |
| 5 | line_chart | 4 | P5 | none | n/a-js-off | n/a-js-off | n/a-js-off | none observed at probe time | False |
| 6 | multi_panel | 5 | P6 | Spend Growth is Accelerating @ 40px/700 | n/a-js-off | n/a-js-off | n/a-js-off | none observed at probe time | False |
| 7 | three_column_comparison | 6 | P7 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 8 | metric_row_with_breakdown | 7 | P8 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 9 | line_chart | 8 | P9 | none | n/a-js-off | n/a-js-off | n/a-js-off | none observed at probe time | False |
| 10 | line_chart | 9 | P10 | none | n/a-js-off | n/a-js-off | n/a-js-off | none observed at probe time | False |
| 11 | line_chart | 10 | P11 | none | n/a-js-off | n/a-js-off | n/a-js-off | none observed at probe time | False |
| 12 | chart_hero_dual | 11 | P12 | none | n/a-js-off | n/a-js-off | n/a-js-off | none observed at probe time | False |
| 13 | line_chart | 12 | P13 | none | n/a-js-off | n/a-js-off | n/a-js-off | none observed at probe time | False |
| 14 | dual_chart | 13 | P14 | Net write-off rate @ 40px/700; 30+ days past due @ 40px/700 | n/a-js-off | n/a-js-off | n/a-js-off | none observed at probe time | False |
| 15 | stacked_bar_chart | 14 | P15 | none | n/a-js-off | n/a-js-off | n/a-js-off | none observed at probe time | False |
| 16 | data_table | 15 | P16 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 17 | dual_chart | 16 | P17 | Net Card Fees ($B) @ 40px/700; YoY Growth % @ 40px/700 | n/a-js-off | n/a-js-off | n/a-js-off | none observed at probe time | False |
| 18 | combo_chart | 17 | P18 | none | n/a-js-off | n/a-js-off | n/a-js-off | none observed at probe time | False |
| 19 | line_chart | 18 | P19 | none | n/a-js-off | n/a-js-off | n/a-js-off | none observed at probe time | False |
| 20 | pill_comparison | 19 | P20 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 21 | multi_panel | 20 | P21 | Capital composition @ 40px/700 | n/a-js-off | n/a-js-off | n/a-js-off | none observed at probe time | False |
| 22 | guidance_statement_card | 21 | P22 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 23 | brand_divider | 22 | P23 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 24 | data_table | 23 | P24 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 25 | data_table | 24 | P25 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 26 | data_table | 25 | P26 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 27 | dual_chart | 26 | P27 | none | n/a-js-off | n/a-js-off | n/a-js-off | none observed at probe time | False |
| 28 | multi_panel | 27 | P28 | Funding Mix @ 40px/700; Deposit Programs @ 40px/700 | n/a-js-off | n/a-js-off | n/a-js-off | none observed at probe time | False |
| 29 | freeform_grid | 28 | P29 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 30 | freeform_grid | 29 | P30 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 31 | annex_table | 30 | P31 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 32 | annex_table | 31 | P32 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 33 | annex_table | 32 | P33 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 34 | annex_table | 33 | P34 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 35 | annex_table | 34 | P35 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 36 | annex_table | 35 | P36 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 37 | annex_table | 36 | P37 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 38 | freeform_grid | 37 | P38 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 39 | freeform_grid | 38 | P39 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 40 | freeform_grid | 39 | P40 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 41 | freeform_grid | 40 | P41 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 42 | freeform_grid | 41 | P42 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 43 | freeform_grid | 42 | P43 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |
| 44 | brand_divider | 43 | P44 | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable |

Focus slide 17 detail is in §2. Deck-wide: HTML pane titles appear on multi-pane layouts that emit `.gl-chart-pane-title` (s6, s14, s17, s21, s28, …). Single-series line charts correctly show **none** (title is slide H2 only). No slide showed Chart.js `plugins.title.display` legacy fallback. No clipping detected at probe time. x-tick `autoSkip=true`, rotation 0 on audited chart slides (native).

---

## 6. What renderer_v2 does well vs accepted/source divergences

### Does well (fresh evidence)

- **Identity-stable deck** — 44 unique `data-slide-number` values mapped 1:1 to PDF pages.
- **Outlined support row alignment (#136)** — runtime `chart-table-aligned` + sub-pixel cell↔bar centres in Chart.js and SVG.
- **Structured side callout (#138)** — tall/right unboxed three-line callout with badge suppression and independent stack totals.
- **Chart typography contract (#139)** — HTML pane titles + y-tick/datalabel font sizes from `chart_config.typography`, verified on painted models not options-only.
- **Pill board geometry (#140)** — five-row board matches approved PDF-normalized targets within house noise; negative controls keep inset/legacy paths off the fixed recipe.
- **Self-contained offline HTML** — run_meta delivery self-contained with inlined fonts/charts.
- **Annex tables** — uniform navy group headers retained (prior T13 lock).

### Accepted / source divergences (not scored as new renderer tickets)

- R3 brand Centurion / third-party marks → generic `seal_lockup`.
- R1 / F12+ / N2 chip weight / R2 L-bracket silhouette locks from prior baselines.
- IR bullet sheet and FLS legal pages: content-complete, density/packing recipe ≠ pixel PDF.
- s12 missing left NCA chart: **handoff/source** gap relative to PDF.
- Disclosure footers often collapse to chip+panel vs PDF fine-print paragraphs (recipe).

---

## Artifact index

| Path | Role |
|------|------|
| `passes/pass_01/handoff.json` | Closed-ticket handoff |
| `passes/pass_01/output/presentation.html` | Rendered deck |
| `passes/pass_01/output/run_meta.json` | Renderer run meta |
| `page_slide_mapping.json` | Identity assertion |
| `comparison/pdf/*.png` | 44× PDF rasters 1920×1080 |
| `comparison/html/*.png` | 44× HTML shots 1920×1080 |
| `comparison/sbs/*.png` | 44× full-res side-by-sides |
| `comparison/contact_sheet.png` | Contact sheet |
| `comparison_manifest.json` | Artifact manifest (no scores) |
| `closed_tickets/closed_ticket_results.json` | Scorecard rows + #139 deck audits |
| `closed_tickets/closed_ticket_raw.json` | Raw DOM measures |
| `closed_tickets/shots/` | Chart.js vs SVG focus screenshots |
| `probes/build_full_comparison.py` | #137-compliant full comparison |
| `probes/closed_ticket_probes.py` | #136–#140 probes both modes |

---

*End of v10 baseline. Simulation / observation only. No production renderer changes. No issues filed.*
