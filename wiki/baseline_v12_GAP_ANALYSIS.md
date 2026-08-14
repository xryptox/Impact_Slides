# Gap Analysis v12: renderer_v3 vs Amex Q1'26 Earnings PDF

**(First complete 44-page PDF↔HTML observation of schema-v1 / renderer 3.0.0 from the canonical D314 corpus — Companion-mode SIMULATION only)**

**Simulation:** `simulation/amex_q1_2026/`
**Source of truth:** `C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf`
**PDF identity:** SHA-256 `a87c11625c84e0dabb02d523f6a2d2508b892f18ee242ef197a9b40157bd3faf` · 44 pages · page0 rect 959.76×540.0
**Renderer under test:** `impact_slides.renderer_v3` **3.0.0** @ `a7abe1150299709b209789be6aa04175344012b1`
**Canonical input (read-only; no mutations):** `tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json`
**Handoff SHA-256:** `24cda2dbb2c5ce14ee80f0dbec45f4c3c0c0f7002344d2524218bdbf3ba12b8d`
**Prior baselines:** `wiki/baseline_v11_GAP_ANALYSIS.md` is **not on this branch tip** (present only in git history `42f620c`); residual delta uses that historical text plus `wiki/baseline_v9_GAP_ANALYSIS.md` / `wiki/baseline_v10_VERIFIER_CORRECTION_146.md`. Extracted copy for this run: `simulation/amex_q1_2026/extracted_baseline_v11_GAP_ANALYSIS.md`.
**Method:** One strict `python -m impact_slides.renderer_v3` publish → Playwright capture via `scripts/simulation_probe.wait_for_paint_ready_charts` + section isolate (lesson 32) → PyMuPDF 1920×1080 PDF rasters → full-resolution SBS. **No MAE / similarity % / pixel-diff scores / heatmaps.**

---

## 1. Scope gate, mapping assertion, run identity

| Gate | Result |
|------|--------|
| Renderer commit | `a7abe1150299709b209789be6aa04175344012b1` |
| Renderer version | `3.0.0` |
| Production paths touched | **None** (only `simulation/amex_q1_2026/**` + final `wiki/baseline_v12_GAP_ANALYSIS.md`) |
| Handoff | Committed D314 corpus only — **no** `amex_handoff_mutations.py`, no hand edits |
| Render command | `python -m impact_slides.renderer_v3 --handoff tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json --out simulation/amex_q1_2026/passes/pass_01/renderer_v3_out` |
| Render outcome | **strict exit 0**, `run_meta.status=clean`, `ok=true`, `options.strict=true` |
| `run_meta` events | 67 × `info` · **0** warn/error |
| PDF pages | 44 |
| HTML `data-slide-number` | 44 unique values **1…44** |
| HTML `data-layout` vs corpus `layout_type` | **44/44 match** |
| Identity map | **HTML slide N → PDF index N−1 → physical page N** |
| Capture contract | viewport **1920×1080**, `deviceScaleFactor=1` (fit scale 1); isolate target `section.slide` (siblings `display:none`, stage/slide transform none); element screenshot; `wait_for_paint_ready_charts` before every chart-slide shot; **no** `painted_datalabel_lines` (v3 paints labels via overlay chrome, not chartjs-plugin-datalabels); no nth selectors; no fixed sleeps |
| Comparison artifacts | 44 PDF + 44 HTML + 44 SBS @ exact 1920×1080 halves (SBS 3840×1080); contact sheet; `comparison_manifest.json` `missing_or_bad_size=[]` |
| HTML PNG uniqueness | **44 distinct SHA-256** (no blank-duplicate cover class) |
| Console errors | `[]` |
| Image scoring | **forbidden / absent** |
| Scope-gate | **PASS** |

### Published artifact hashes (`passes/pass_01/renderer_v3_out/`)

| File | SHA-256 |
|------|---------|
| `presentation.html` | `fe2c4b0a2ff9134e02373cc0b6005970c3e87b38608961679d6a9caec691744d` |
| `run_meta.json` | `cc48c5935401a9f6d5abf355d334d17ee480bfc49fac815d32c02afec00207a7` |
| `evidence_manifest.json` | `6b8c217a8b2384a4d09c7b24d2b52b3d5472d3761867ef8d0b3cc0af0244e3c5` |
| `handoff_schema_v1.json` | `86fd45455dcc2ee8e99b8b546b36118ede283dad0349427328724702ce215414` |
| `slide_notes.md` | `78823a5fba725aa5deb5961399a066b9a6935af1cf724bc851f2a8b079b4ae8e` |

### Capture contract detail

- Deck is a stacked scroll of all 44 `section.slide` nodes inside `.deck-stage` (no `.active` hide rule; resize-fit scales by `min(innerWidth/1920, innerHeight/1080)`).
- Capture forces transform/scale identity and screenshots the section node after paint-ready settle.
- Chart slides with paint-ready geometry (nonzero canvas, non-degenerate `chartArea`, painted dataset elements across one rAF): **4–6, 8–15, 17–19, 21, 24, 27–28** (counts in `comparison_manifest.json`).
- Primary surface is JS-on Chart.js (SVG noscript fallback not used for comparison).

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

## 2. Full 44-page qualitative ledger

Classification is exactly one of:
`faithful reproduction` · `accepted v3 design divergence` · `candidate renderer defect or capability gap` · `corpus/extraction residual` · `source/PDF artifact` · `capture failure`.

SBS paths are relative to `simulation/amex_q1_2026/`. Machine-readable twin: `qualitative_ledger_v12.json`.

| # | layout_type | pdf_idx | page | SBS | class | observation (qualitative; no scores) |
|--:|-------------|--------:|-----:|-----|-------|--------------------------------------|
| 1 | `opening_cover` | 0 | P1 | `side_by_side/slide_01.png` | **accepted v3 design divergence** | PDF is full-bleed navy/cyan brand cover with Centurion seal art. v3 emits a minimal white title slide (title + Q1'26 + date). Brand-seal omission is the standing R3 wontfix; remaining cover recipe is intentional v3 opening chrome, not a capture miss. |
| 2 | `narrative` | 1 | P2 | `side_by_side/slide_02.png` | **faithful reproduction** | Seven Business Highlights bullets match PDF substance and bold emphasis pattern. Packing is tighter/smaller type than PDF but content-complete; footnote collapses to a notes affordance. |
| 3 | `period_comparison` | 2 | P3 | `side_by_side/slide_03.png` | **accepted v3 design divergence** | All five KPI rows and values match (`$18,907` / `$16,967` / 11% … shares 686/702/(2%)). PDF uses three large period pills; v3 uses a compact right-hand matrix with stub labels — schema-v1 period_comparison recipe, not a value error. |
| 4 | `single_chart` | 3 | P4 | `side_by_side/slide_04.png` | **corpus/extraction residual** | Dual line (FX-adj + Reported) paints with correct endpoint labels (9%/10%). Missing vs PDF: Leap Year callout box; bottom G&S/T&E support table. Corpus payload is chart-only (no support table / annotation objects). |
| 5 | `single_chart` | 4 | P5 | `side_by_side/slide_05.png` | **corpus/extraction residual** | Main UCS billings line (7→10%) paints. Missing: Leap Year box; right-side G&S 9% / T&E 11% callouts; bottom generation mix table (Gen-Z…Total). Payload is single series + fixed 0–15 domain only. |
| 6 | `dual_chart` | 5 | P6 | `side_by_side/slide_06.png` | **corpus/extraction residual** | Both panes paint (spend bars + retention grouped bars) with pane titles. Missing PDF elbow “+ ~6 percentage points” callout and “Refresh” chip; retention y-window starts at 90% in PDF vs full 0–100% style in v3 (readable but different). No callout object in corpus charts payload. |
| 7 | `comparison_cards` | 6 | P7 | `side_by_side/slide_07.png` | **candidate renderer defect or capability gap** | Numbers 50/5/10×, 20/10/2×, 21/11/2× are present as a three-column text board. PDF’s circular dual-metric cards, connector arrows, and category captions do not appear. Payload is a plain `table`; `comparison_cards` does not promote that table into the PDF card/circle recipe — layout capability gap relative to the source art. |
| 8 | `single_chart` | 7 | P8 | `side_by_side/slide_08.png` | **corpus/extraction residual** | Dual line (FHR+THC 40→50%, UCS lodging flat 5%) paints. Entire right KPI stack from PDF (3,400+ properties, 300+ new, $600 credit, $550 value) and 10× vertical callout are absent — payload is chart-only. |
| 9 | `single_chart` | 8 | P9 | `side_by_side/slide_09.png` | **corpus/extraction residual** | Commercial FX-adj line (2→4%) paints. Missing Leap Year box, G&S/T&E side labels, and SME/Large Corp support table. |
| 10 | `single_chart` | 9 | P10 | `side_by_side/slide_10.png` | **corpus/extraction residual** | ICS dual line (FX-adj + Reported) paints with correct markers. Missing Leap Year box, G&S/T&E side labels, Int’l Consumer/SME support table. |
| 11 | `single_chart` | 10 | P11 | `side_by_side/slide_11.png` | **candidate renderer defect or capability gap** | Values are the flat 9/9/10/9/10 series, but **generated** y-domain collapses to ~9–10% so the line reads as a dramatic V. PDF keeps a 0–15% frame and looks nearly flat. Corpus did not pin a fixed domain; renderer auto-domain for low-variance % series is misleading. Next check: pin `domain.kind=fixed` 0–15 **or** enforce a minimum domain pad for pct series. |
| 12 | `chart_hero_dual` | 11 | P12 | `side_by_side/slide_12.png` | **corpus/extraction residual** | Paint-ready single canvas + hero stack (66% / 73%) — **not** the v10 blank-plot class. But left chart is a **single-series** navy bar (1.5…1.3) rather than PDF’s three-band stacked NCA (UCS/Commercial/ICS totaling ~3.x). Corpus `chart_type=grouped_bar` with one series and those values; hero metric labels are short share labels vs PDF long sentences. Headings (“Proprietary New Cards/Accounts Acquired”) **are** authored (improves v11 #147). |
| 13 | `single_chart` | 12 | P13 | `side_by_side/slide_13.png` | **faithful reproduction** | Grouped Total Balances vs Billed Business bars and labels match PDF structure and values (through Q1'26 7%/9%). Minor legend placement / color-swap vs PDF is cosmetic. |
| 14 | `dual_chart` | 13 | P14 | `side_by_side/slide_14.png` | **faithful reproduction** | 30+ DPD flat 1.3% and Net Write-off ~2.1→2.0% both paint with correct labels; dual-card chrome is the v3 recipe. |
| 15 | `single_chart` | 14 | P15 | `side_by_side/slide_15.png` | **corpus/extraction residual** | Stacked write-offs + reserve build/release geometry paints (including negatives). Missing: on-bar total provision callouts ($1,150…), series color recipe vs PDF (PDF write-offs light blue), and bottom “Reserve Rate for Total Balances” outlined row (2.9%…2.8%). Payload has the two series only. |
| 16 | `data_table` | 15 | P16 | `side_by_side/slide_16.png` | **accepted v3 design divergence** | All revenue line items and YoY/FX columns match. PDF pill columns vs v3 dense data grid is the table recipe difference. |
| 17 | `dual_chart` | 16 | P17 | `side_by_side/slide_17.png` | **corpus/extraction residual** | Both panes paint with titles. Left Net Card Fees bars use corpus `format_id: pct_0` so labels read `1%…3%` instead of PDF `$0.9…$2.8`; CAGR measure-rule chrome absent. Right FX YoY line shape matches 16→20→16. Wrong format_id / missing measure annotation are corpus (and format-registry application) issues, not blank capture. |
| 18 | `chart_hero_dual` | 17 | P18 | `side_by_side/slide_18.png` | **corpus/extraction residual** | Bars paint but NII series is authored with `format_id: pct_0`, so `$4.2` becomes `4%` and the axis is 0–6% rather than $ billions. YoY growth boxes under bars missing. Driver card shows different rows (Loan growth / Net yield / …) than PDF’s Billed Business / NII / Volume / Margin CAGR arrows — payload content divergence. |
| 19 | `single_chart` | 18 | P19 | `side_by_side/slide_19.png` | **corpus/extraction residual** | Dual revenue line paints. Missing Leap Year box and bottom $B absolute row ($17.0…$18.9). Series styling (solid vs dashed assignment) differs slightly from PDF. |
| 20 | `period_comparison` | 19 | P20 | `side_by_side/slide_20.png` | **accepted v3 design divergence** | Expense rows and values match including VCE 44.7% callout (top banner vs PDF side pill). Nested “Variable Customer Engagement Expenses” indent is flattened to a peer row — recipe/leveling choice with complete numbers. |
| 21 | `chart_hero_dual` | 20 | P21 | `side_by_side/slide_21.png` | **corpus/extraction residual** | Dividends + buyback stack paints with totals. Missing PDF line overlay for Common Shares Outstanding (702→682). Outlined ROE support in corpus is constant **35%** all periods vs PDF 35/34/36/36/34/35 — extraction error. Hero summary (58/74/10.5/10–11) present as driver_card. |
| 22 | `metric_overview` | 21 | P22 | `side_by_side/slide_22.png` | **accepted v3 design divergence** | Guidance figures present (9%–10% revenue; $17.30–$17.90 EPS) but as a sparse left-aligned metric list rather than PDF’s single centered card. Content complete; recipe differs. |
| 23 | `section_divider` | 22 | P23 | `side_by_side/slide_23.png` | **accepted v3 design divergence** | “Appendix” title present; v3 white section plate vs PDF navy/cyan brand divider with seal (R3). |
| 24 | `single_chart` | 23 | P24 | `side_by_side/slide_24.png` | **corpus/extraction residual** | Category bars paint with % labels. Missing: $486B network volumes callout; brace groups (UCS/Commercial/ICS); bottom “% of Total Network Volumes” boxes; PDF gray “Processed Volumes” treatment. HTML also plots aggregate category bars the PDF keeps as group labels only — category model in corpus. |
| 25 | `data_table` | 24 | P25 | `side_by_side/slide_25.png` | **faithful reproduction** | FX impact currency rows and YoY values match; v3 grid vs PDF column headers is cosmetic. |
| 26 | `data_table` | 25 | P26 | `side_by_side/slide_26.png` | **faithful reproduction** | T&E matrix orientation matches PDF (categories as columns; YoY / % of Total as rows) with matching 9/6/8/13/9 and 7/5/7/9/29 figures. (v11 #153 residual was a different handoff matrix on this page number under v2 layouts — not reproduced here.) |
| 27 | `dual_chart` | 26 | P27 | `side_by_side/slide_27.png` | **faithful reproduction** | Unemployment + GDP scenario fans paint with three series each; shapes track PDF (upside/baseline/downside). Marker/dash recipe differs slightly (accepted chrome). Paint-ready **2** canvases — #146 class cleared. |
| 28 | `dual_chart` | 27 | P28 | `side_by_side/slide_28.png` | **corpus/extraction residual** | Funding Mix + Deposit Programs stacks paint with legends. Missing: on-segment % labels, stack total $ callouts ($210/$219, $151/$157), and tall “92% FDIC insured…” side callout. Structure is present; annotation density is not. |
| 29 | `narrative` | 28 | P29 | `side_by_side/slide_29.png` | **faithful reproduction** | Variance commentary bullets match PDF content; bold lead-ins preserved. |
| 30 | `narrative` | 29 | P30 | `side_by_side/slide_30.png` | **faithful reproduction** | Continuation commentary complete and aligned with PDF. |
| 31 | `annex_table` | 30 | P31 | `side_by_side/slide_31.png` | **accepted v3 design divergence** | Annex 1 (1 of 2) values present as flat metric rows (Billed Business Reported/FX-Adj, G&S, T&E, Processed Volumes, CAGRs). PDF nested row-group labels become prefixed metric names — readable, recipe-different. Some Processed Volumes cells show `—` where PDF is blank/partial. |
| 32 | `grouped_annex_table` | 31 | P32 | `side_by_side/slide_32.png` | **candidate renderer defect or capability gap** | Two segment groups paint with correct underlying numbers, but column headers clip to `Q…` / `F…` instead of `Q1'26 Reported` / `FX-Adj.*`. Narrow grouped-annex header fit is a renderer table packing gap. |
| 33 | `annex_table` | 32 | P33 | `side_by_side/slide_33.png` | **faithful reproduction** | Annex 2 balances grid values match PDF ($142…$224, YoY, CAGRs) under flat metric naming. |
| 34 | `annex_table` | 33 | P34 | `side_by_side/slide_34.png` | **faithful reproduction** | Annex 3 revenue rows present with matching Q1'26/$ prior figures (spot-checked via DOM + SBS). |
| 35 | `annex_table` | 34 | P35 | `side_by_side/slide_35.png` | **faithful reproduction** | Annex 4 Net Card Fees multi-period grid populated (DOM text_len>700; SBS consistent with sister annexes). |
| 36 | `annex_table` | 35 | P36 | `side_by_side/slide_36.png` | **faithful reproduction** | Annex 5 NII multi-period grid populated. |
| 37 | `annex_table` | 36 | P37 | `side_by_side/slide_37.png` | **faithful reproduction** | Annex 6 RNIE multi-period grid populated. |
| 38 | `legal_notice` | 37 | P38 | `side_by_side/slide_38.png` | **candidate renderer defect or capability gap** | Full cautionary text is present but painted as a dense continuous wall without PDF’s bullet hierarchy / paragraph rhythm, harming scanability on a 1920×1080 slide. legal_notice packing/structure gap. |
| 39 | `legal_notice` | 38 | P39 | `side_by_side/slide_39.png` | **candidate renderer defect or capability gap** | Continuation legal text present; same dense single-stream packing as s38. |
| 40 | `legal_notice` | 39 | P40 | `side_by_side/slide_40.png` | **candidate renderer defect or capability gap** | Same legal_notice packing class. |
| 41 | `legal_notice` | 40 | P41 | `side_by_side/slide_41.png` | **candidate renderer defect or capability gap** | Same legal_notice packing class. |
| 42 | `legal_notice` | 41 | P42 | `side_by_side/slide_42.png` | **candidate renderer defect or capability gap** | Same legal_notice packing class. |
| 43 | `legal_notice` | 42 | P43 | `side_by_side/slide_43.png` | **candidate renderer defect or capability gap** | Same legal_notice packing class; final continued block. |
| 44 | `closing_cover` | 43 | P44 | `side_by_side/slide_44.png` | **accepted v3 design divergence** | PDF full-bleed navy “AMERICAN EXPRESS” wordmark vs v3 minimal white lockup — parallel to s1 opening recipe / R3 brand treatment. |

### Ledger tally

| class | count | slides |
|-------|------:|--------|
| faithful reproduction | 13 | 2, 13, 14, 25–27, 29, 30, 33–37 |
| accepted v3 design divergence | 8 | 1, 3, 16, 20, 22, 23, 31, 44 |
| corpus/extraction residual | 14 | 4–6, 8–10, 12, 15, 17–19, 21, 24, 28 |
| candidate renderer defect or capability gap | 9 | 7, 11, 32, 38–43 |
| source/PDF artifact | 0 | — |
| capture failure | 0 | — |

---

## 3. v2 → v3 delta

Baseline reference: historical `wiki/baseline_v11_GAP_ANALYSIS.md` @ `42f620c` (renderer_v2 + mutated amex_v10 handoff). v11 is **not** present on this branch tip; delta is from that extracted text, not from re-running v2.

### Named v11 residuals → v12

| v11 residual | v11 class | v12 (renderer_v3 + D314) | evidence |
|--------------|-----------|---------------------------|----------|
| #146 blank plots on 9/12/27 | capture tooling (corrected in v10 note) | **Resolved** as capture class | paint-ready charts 1/1/2; unique HTML hashes; SBS shows geometry |
| #147 s12 pane headings | handoff residual | **Mostly resolved** as heading authorship; **replaced** by deeper corpus gap | D314 payload has chart/hero headings; SBS shows titles — but left chart is single-series 1.5 bars, not 3-band stack |
| #153 s26 matrix orientation | handoff residual | **Not reproduced** on this corpus page | v12 s26 is T&E category-column matrix matching PDF; different payload than v2 amex_v10 s26 |
| #136/#149 s15 outlined support align | solved on v2 | **Not carried** — support row absent | D314 s15 has no reserve-rate support object; stack paints without outlined boxes |
| #138/#158 s28 FDIC callout | solved on v2 | **Regressed as content** | stacks paint; FDIC tall callout + % labels missing from D314/v3 chrome |
| #139/#150 s17 typography | solved on v2 | **Replaced** | pane titles exist; left series `format_id=pct_0` mislabels $B as %; no CAGR rule |
| #151 s18 boxed labels / driver | solved on v2 | **Replaced** | driver_card present but different rows; NII formatted as pct; no under-bar YoY boxes |
| #154 s24 brackets + $486B | solved on v2 | **Regressed as content** | bars only; braces/$486B/%-of-total boxes absent from payload |
| #155 s21 capital composition | solved on v2 | **Partial** | stack+hero present; shares line missing; ROE row wrong constants |
| #156 s27 macro scenarios | solved on v2 | **Holds** | dual scenario fans faithful |
| #157 s33–37 annex matrices | solved on v2 | **Holds** | annex grids populated |
| #159 s32 grouped annex IDs | solved on v2 | **Partial** | two groups present; header text clips |
| R3 seal / brand covers | accepted | **Preserved** accepted divergence | s1/s23/s44 |
| R1 / F12+ / N2 / R2 L3 locks | accepted on v2 | **N/A or absorbed** into v3 recipe notes | v3 does not use v2 callout class names; no new claim they “broke” |

### What renderer_v3 now does well (fresh SBS)

1. **Strict clean full-deck publish** of the 44-slide D314 corpus with zero non-info `run_meta` events.
2. **Identity-stable stacked deck** — 44 `data-slide-number` + matching `data-layout`; no active-slide blank class when captured with paint-ready + isolate.
3. **Chart.js paint-ready geometry** on every chart slide (non-zero canvases, chartArea, dataset elements) including former trouble slides 12 and 27.
4. **Dual-pane compositions** (s6, s14, s17, s27, s28) render as two titled cards with independent charts.
5. **Hero compositions** mount (s12/s18/s21) with metric_stack / driver_card chrome beside the plot.
6. **Core narrative + several chart/table slides** are content-faithful (s2, s13–14, s25–27, s29–30, s33–37).
7. **Schema-v1 tables** (data_table / annex_table) consistently show stub+column matrices without the v2 freeform_grid alias confusion on commentary pages (s29–30 are true `narrative`).

---

## 4. Residual triage

Only items with **fresh v12 SBS + corpus/payload evidence**. No fixes designed; no tickets filed.

### 4.1 Candidate renderer_v3 defect / capability gap

| ID | where | impact | likely ownership | smallest next verification |
|----|-------|--------|------------------|----------------------------|
| R-A | s11 `single_chart` | Low-variance % line auto-domain (~9–10%) creates false drama vs PDF 0–15% frame | renderer domain defaults (corpus also omitted fixed domain) | Re-render s11 with fixed 0–15 domain **or** inspect generated-domain padding rules on pct formats; compare SBS slope |
| R-B | s7 `comparison_cards` | PDF circle/arrow card recipe absent; values only as text columns | `comparison_cards` layout capability vs table payload | Confirm whether schema-v1 defines a circular dual-metric card surface; if yes, probe DOM for missing card primitives on s7 |
| R-C | s32 `grouped_annex_table` | Column headers clip (`Q…`/`F…`) | annex header fit/ellipsis | Measure header cell scrollWidth vs clientWidth on both groups; try longer header strings in a throwaway fixture (observation only) |
| R-D | s38–43 `legal_notice` | Continuous dense text loses PDF bullet hierarchy | legal_notice block packing / list emission | Diff payload list structure vs painted DOM list nodes; check whether bullets exist in schema but flatten in publish |

### 4.2 Corpus / extraction / content residual

| ID | where | impact | likely ownership | smallest next verification |
|----|-------|--------|------------------|----------------------------|
| C-A | s12 | Single-series 1.5 bars vs PDF 3-band stack totals ~3.x; hero copy shortened | D314 chart_data series incomplete | Diff PDF segment values vs payload series list; confirm stacked_bar + 3 series authorship |
| C-B | s17 left pane | `$B` series tagged `pct_0` → labels `1%…3%` not `$0.9…$2.8`; no CAGR rule | format_id + missing measure annotation in corpus | Flip format_id to usd/billions in a side inspection of format registry; do not mutate canonical file in-repo |
| C-C | s18 | NII `$` values as `pct_0`; driver rows ≠ PDF CAGR card; no under-bar YoY boxes | corpus format + hero content | Same format check as C-B; compare driver_card rows to PDF |
| C-D | s4,5,9,10,19 | Leap Year callouts + bottom support tables missing | corpus annotations/support omitted | List PDF callout/support per slide vs payload keys |
| C-E | s5,8,9,10 | Side KPI / generation / segment supports missing | corpus | same |
| C-F | s8 | Right property/credit KPI stack missing | corpus | same |
| C-G | s15 | Reserve-rate outlined row + stack total labels missing | corpus support | same |
| C-H | s21 | Shares-outstanding line missing; ROE support constant 35% | corpus auxiliary_series / support values | Compare PDF ROE row to payload support cells |
| C-I | s24 | $486B, braces, %-of-total boxes missing; extra aggregate bars | corpus category model | Map PDF categories vs payload categories |
| C-J | s28 | FDIC callout + on-stack % and $ totals missing | corpus annotations | same |
| C-K | s6 | +6pp elbow callout missing | corpus | same |

### 4.3 Source/PDF artifact or accepted divergence

| ID | where | notes |
|----|-------|-------|
| A-1 | s1, s23, s44 | Brand seal / full-bleed navy covers — R3 wontfix + v3 minimal cover recipe |
| A-2 | s3, s16, s20, s22, s25, s31 | Pill/board PDF furniture vs v3 matrix/metric recipes with matching numbers |
| A-3 | dual_chart card chrome | Navy pane headers, legends, gridless plots — intentional v3 skin |

### 4.4 Screenshot / probe failures

**None.** `capture_errors=[]`, `console_errors=[]`, `missing_or_bad_size=[]`, 44 unique HTML digests.

---

## 5. Diagnostics & artifact index

| artifact | path |
|----------|------|
| Strict render out | `simulation/amex_q1_2026/passes/pass_01/renderer_v3_out/` |
| `run_meta.json` | `…/run_meta.json` (status=clean) |
| `presentation.html` | `…/presentation.html` |
| PDF pages 01–44 | `simulation/amex_q1_2026/pdf_pages/slide_XX.png` |
| HTML slides 01–44 | `simulation/amex_q1_2026/html_slides/slide_XX.png` |
| SBS 01–44 | `simulation/amex_q1_2026/side_by_side/slide_XX.png` |
| Contact sheet | `simulation/amex_q1_2026/contact_sheet.png` |
| Manifest | `simulation/amex_q1_2026/comparison_manifest.json` |
| Capture log | `simulation/amex_q1_2026/capture_log.json` |
| Ledger JSON | `simulation/amex_q1_2026/qualitative_ledger_v12.json` |
| Build script (sim-only) | `simulation/amex_q1_2026/build_v12_comparison.py` |
| Extracted v11 text | `simulation/amex_q1_2026/extracted_baseline_v11_GAP_ANALYSIS.md` |
| Wiki report (byte copy) | `wiki/baseline_v12_GAP_ANALYSIS.md` |

---

## 6. Stop proofs

| proof | result |
|-------|--------|
| Strict render exit 0 clean | **PASS** |
| 44 PDF @ 1920×1080 | **PASS** (`comparison_manifest.pdf_pages`) |
| 44 HTML @ 1920×1080 | **PASS** |
| 44 SBS @ 3840×1080 | **PASS** |
| Identity 1…44 + layout match | **PASS** |
| No MAE/similarity/pixel scores | **PASS** (qualitative ledger only) |
| No production/test/script/config edits | **PASS** (sim + wiki report only) |
| Report byte-identical to wiki copy | enforced at docs commit |
| Exactly two commits (artifacts, then docs) | enforced at closeout |

---

*End of v12 observation baseline. Companion-mode only — no renderer fixes, no corpus edits, no tickets.*
