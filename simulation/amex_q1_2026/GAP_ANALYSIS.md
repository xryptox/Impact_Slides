# Gap Analysis: renderer_v2 vs Amex Q1'26 Earnings PDF

**Simulation:** `simulation/amex_q1_2026/`  
**Source of truth:** `C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf` (44 pages, 16:9)  
**Renderer under test:** `impact_slides.renderer_v2` (handoff → self-contained HTML only; **no production code changes**)  
**Method:** PyMuPDF rasterize (200 DPI) → vision/text transcription → ≤10 handoff-only comparison passes → Playwright 1920×1080 screenshots + side-by-side PDF/HTML diffs  

**Passes run:** 3 (stopped early — remaining divergences are type **(B)** capability gaps; further handoff churn would not close structural IR house style)

---

## Scoring caveats (read first)

| Caveat | Implication |
|--------|-------------|
| **Pixel MAE similarity is white-biased** | Mean ~86% across passes is inflated by shared white canvas. It is a *relative trend* metric within this run, **not** IR layout fidelity. |
| **Ground truth is visual side-by-sides** | Judge structure from `passes/pass_XX/screenshots/compare_YY.png` and `diff.png`, not mean %. |
| **Type (A) vs (B)** | **(A)** = fixable by editing handoff JSON only. **(B)** = no handoff expression exists (or exists but is too weak) without renderer changes. |
| **Chart path split** | Passes 01–02 used Chart.js (`charts` feature on). Pass 03 suppressed charts (`features_enabled: []`) to force the internal SVG painter. Several house-style cues work on SVG only. |

Evidence roots (relative to this folder):

- PDF rasters: `extracted/pdf_page_XX.png`
- Pass artifacts: `passes/pass_0N/{handoff.json,output/,screenshots/compare_XX.png,diff_scores.json,notes.md}`

---

## Per-pass summary table

| Pass | Chart path | Mean MAE sim. | Mean SSIM-approx | Top 3 divergences | Types |
|-----:|------------|--------------:|-----------------:|-------------------|-------|
| **01** | Chart.js (default) | **86.12%** | 85.71% | (1) IR line-chart house style missing (axis 0–15%, dashed series, on-point %, Leap Year box) — `compare_03.png`; (2) Pill-column financial comparison table rendered as row-grid — `compare_02.png`; (3) Full-width IR bullets + inline bold + brand cover seal missing — `compare_01.png`, `compare_00.png` | **B / B / B** (partial A for content layout choices later) |
| **02** | Chart.js | **86.24%** (+0.12) | 86.14% | (1) Chart.js ignores SVG-oriented `chart_config` (axis domain, series names, dashed, annotation, point labels) — `compare_03.png`; (2) Negative stacked provision segments absorbed above zero — `compare_14.png`; (3) Pill-column + brand cover/divider recipes still missing — `compare_02.png`, `compare_00/22/43.png` | **B / B / B** |
| **03** | Internal SVG (`--suppress-feature charts`) | **86.19%** (−0.05) | 86.12% | (1) SVG gains dashed + point labels but still lacks annotation + strict 0/5/10/15 rails — `compare_03.png`; (2) Negative stacked provision still absorbed on SVG path too — `compare_14.png`; (3) Pill tables + chart\|hero dual card + brand cover/dividers still missing — `compare_02/11/19/00/22/43.png` | **B / B / B** |

### Per-pass highlights (A closed vs B confirmed)

| Pass | Meaningful (A) closures | Confirmed / refined (B) |
|-----:|-------------------------|-------------------------|
| 01 | Baseline map of entire deck; content largely ingested | Opened D1–D12 catalog (cover seal, rich bullets, pill tables, IR charts, chart\|hero, guidance card, brand dividers, multi-panel/broken-axis, annex density, Boardroom shell, negative stacks candidate, theme CLI wiring) |
| 02 | Freeform Highlights (+5.0pp MAE); guidance freeform two-KPI; full Expense + key annex tables; true-negative provision data supplied; variance freeform | Chart.js ignores `chart_config`; negatives not below-axis on Chart.js stack; freeform cannot host charts or IR chrome; pill/brand still absent |
| 03 | SVG path probe; `y_axis_ticks` / unit enrichment; Expense `key_stats` 44.7% attempt | SVG honors dashed + on-point %; annotation still unpainted; forced ticks weak (rendered 0/3/6/9/12 not 0/5/10/15); negatives fail on SVG stack too; `key_stats` does not float VCE inset on `data_table` |

**Stop rationale after pass 03:** Pass 03 notes explicitly: only residual pure-(A) item was a New Acquisitions KPI **label swap** (content accuracy; does not create hero dual card). All structural IR divergences are **(B)**. Additional passes would burn the ≤10 budget without changing the capability picture.

**Worst structural scores (all passes, essentially unchanged):**

| Slide | PDF topic | MAE ~ |
|------:|-----------|------:|
| 43 | Blank / trailing brand page | ~20% |
| 22 | Appendix brand divider | ~24% |
| 05 | U.S. Consumer Platinum (multi-panel / broken axis) | ~77% |

---

## What renderer_v2 already does well

Credit where due — these behaviors successfully carried IR content without schema rejection and produced usable Boardroom slides:

1. **Self-contained 44-slide deck delivery**  
   `python -m impact_slides.renderer_v2 --handoff … --self-contained` produced a complete `presentation.html` for all 44 pages in every pass (`run_meta` slide count OK).

2. **Cover chromatic scaffold (directionally)**  
   `title_or_opening` approaches Amex navy-over-blue banding on PDF p1 / `compare_00.png` even without CLI theme injection. Colors land in the Amex neighborhood.

3. **Numeric intake for tables and charts**  
   Summary financials, billings FX lines, stacked NCA bars, provision stacks, guidance KPI ranges, and dense annex grids accept IR numbers without handoff schema failure.

4. **`line_chart` + `secondary_visual` under-chart table**  
   Real feature: Total Billed Business (`compare_03.png`) gets a G&S / T&E category table under the chart stage — matches IR’s chart-then-table *pattern* even when house styling diverges.

5. **Stacked bar segments (positive stacks)**  
   New Acquisitions UCS/Commercial/ICS stacks render on Chart.js and SVG (`compare_11.png`) — segment composition is directionally correct.

6. **Internal SVG painter honors richer series styling than Chart.js**  
   Pass 03 proved dashed secondary series (`stroke-dasharray`) and on-point % value labels on billings lines — so renderer_v2 is not a total blank slate for IR chart cues; the **SVG path** already has partial house-style support that Chart.js MVP lacks.

7. **Native disclosure footers**  
   Footnotes/detachable legal microcopy ride the disclosure pedestal off the main canvas — sound Boardroom pattern (not collapsible IR chrome, but a stable place for appendix caveats).

8. **`freeform_grid` as geometry escape hatch**  
   Pass 02/03: single-column Highlights, variance commentary, and guidance metric stacks escape forced `split_text_visual` two-card chrome. Best handoff-only lever for IR “quiet sheet” geometry.

9. **Guidance communication (content)**  
   2026 Guidance (`compare_21.png`) surfaces both headline ranges (~10–12% FX-adj billings; ≥$18 EPS) as large metrics — narrative content is recoverable even when single-card IR chrome is not.

10. **Feature gating probe surface**  
    `--suppress-feature charts` cleanly switches Chart.js → SVG without code edits (`features_enabled: []`), enabling the path-split experiments this gap analysis depends on.

---

## Prioritized future-feature list

Each entry must be closed in the **renderer** (schema, layout recipe, chart painter, or shell) — not by more handoff tuning. Priority = impact on end-to-end Amex IR replication × breadth across the 44-page pack.

### P0 — Blocks matching core IR story slides

| # | Feature | What it enables | PDF slide + pass evidence | Missing entirely vs exists-but-weak |
|---|---------|-----------------|---------------------------|-------------------------------------|
| **F1** | **IR line-chart house style (unified Chart.js + SVG)** | Fixed % domain (e.g. 0/5/10/15), honoring `y_axis_min/max/ticks/unit`, **dashed secondary series**, **on-point value labels**, end-series name callouts, stage-dominant chart with minimal Boardroom card chrome | PDF **p4 Total Billed Business** (0-index slide **03**); pass_01/02 Chart.js fails all cues (`pass_02/screenshots/compare_03.png`); pass_03 SVG gets dashed + point labels but **not** forced 0/5/10/15 (renders 0/3/6/9/12) (`pass_03/screenshots/compare_03.png`) | **Exists but weak / path-split:** SVG partial; Chart.js largely ignores `chart_config`. Need parity + strict tick domain. |
| **F2** | **Chart annotation / callout layer** | Dashed “Leap Year Approx. (1%)” boxes, event bands, on-plot text anchors from handoff `chart_config.annotation` | Same **slide 03**; handoff carried annotation every pass; HTML grep `Leap Year` = **0** on pass_03 SVG and Chart.js (`pass_03/notes.md`, `compare_03.png`) | **Missing entirely** (schema field accepted or ignored; nothing painted) |
| **F3** | **Below-axis negative stacked bars (reserve release)** | Provision expense stacks with positive net-write-offs / reserve builds **and** negative reserve-release segments drawn **below** zero; stack tops match IR ($1,150 / $1,251) not absorbed totals (~1,296) | PDF **p15 Total Provision** (slide **14**); pass_02 Chart.js + pass_03 SVG with true negatives `(-73)/(-24)` both absorb negatives upward (`pass_02|03/screenshots/compare_14.png`) | **Missing entirely** on both chart paths (KPI text can show `($24)`; geometry cannot) |
| **F4** | **Pill-column comparison table layout** | Exterior row labels + vertical **pill/rounded column** headers (Q1'26 / Q1'25 / YoY) for statement-style financial summaries and expense lines — not a row-striped spreadsheet grid | PDF **p3 Summary Financial Performance** (slide **02**) `pass_*/screenshots/compare_02.png`; PDF **p20 Expense Performance** (slide **19**) still row-grid after full cell fill + `key_stats` attempt (`pass_03/compare_19.png`) | **Missing entirely** as a first-class layout (only conventional `data_table` grid) |
| **F5** | **Chart \| hero-KPI dual card layout** | Left chart card + right **giant % callout stack** (e.g. 66% Millennial/Gen-Z, 73% Fee-Paying) as peer cards — not under-chart chips and not `dual_chart` (two charts) | PDF **p12 New Acquisitions** (slide **11**) `pass_*/screenshots/compare_11.png`; freeform cannot embed charts (pass_02/03 notes) | **Missing entirely** (`dual_chart` ≠ chart+metrics; freeform has no chart host) |

### P1 — Blocks brand / IR sheet chrome fidelity

| # | Feature | What it enables | PDF slide + pass evidence | Missing entirely vs exists-but-weak |
|---|---------|-----------------|---------------------------|-------------------------------------|
| **F6** | **Brand cover + section divider assets** | Full-bleed two-tone Amex covers with **Centurion seal / ribbon lockup**, appendix openers, trailing brand plates — not empty/`section_divider` near-white Boardroom slides | Cover PDF **p1** slide **00** `compare_00.png` (no seal); Appendix PDF **p23** slide **22** ~24% MAE; trailing slide **43** ~20% MAE (`pass_*/html_slide_22|43` white_frac ~0.97) | **Missing entirely** for brand-mark assets; `section_divider` **exists but weak** (not brand-parameterizable / not full-bleed IR recipe) |
| **F7** | **IR bullet sheet + inline rich-text spans** | Centered title, full-width single column, **selective bold** on partner/product phrases inside bullets (not dual “case/evidence” cards, not plain strings only) | PDF **p2 Business Highlights** (slide **01**); pass_01 `split_text_visual` two-card chrome; pass_02 freeform fixes geometry (+5pp) but **bold spans still impossible** (`pass_02/screenshots/compare_01.png`) | Geometry: **exists but weak** via freeform; **inline rich text: missing entirely** in handoff bullet model |
| **F8** | **IR guidance / statement card recipe** | Single bordered card, navy title bar, two underlined label→value rows centered, micro footnotes under card — not two loose Boardroom metric tiles | PDF **p22 2026 Guidance** (slide **21**) `pass_*/screenshots/compare_21.png`; freeform metric_stack improves values layout but not IR statement chrome (pass_02/03) | **Exists but weak** (metric cards / freeform approximate content; no first-class IR guidance chrome) |
| **F9** | **Floating inset KPI on table slides** | Navy inset “44.7% VCE of Revenue” callout beside / over expense table — `key_stats` must compose into the table/stage recipe, not disappear | PDF **p20 Expense Performance** (slide **19**); pass_03 set `key_stats: [{VCE of Revenue, 44.7%}]` — **no floating inset** (`pass_03/screenshots/compare_19.png`, notes B4) | **Exists but weak** (`key_stats` real elsewhere; no-op / wrong placement on `data_table` expense recipe) |

### P2 — Blocks specialized multi-panel IR boards

| # | Feature | What it enables | PDF slide + pass evidence | Missing entirely vs exists-but-weak |
|---|---------|-----------------|---------------------------|-------------------------------------|
| **F10** | **Broken / discontinuous y-axis** | Platinum retention charts that plot 90–100% with a visual break (PDF house style) instead of 0-based auto scale that flattens signal | PDF **p6 U.S. Consumer Platinum Performance** (slide **05**, worst non-brand MAE ~77%) `pass_*/screenshots/compare_05.png` | **Missing entirely** |
| **F11** | **Multi-region IR dashboard / multi-chart freeform host** | Capital page tiles (ROE trend + stacked returns + share repo + CET1) and Platinum multi-panel boards as one slide recipes; allow freeform (or new layout) to **embed charts** beside metrics | PDF **p21 Capital** (slide **20**); PDF **p6** multi-panel; pass notes D8 / B6 — `metric_dashboard` / `dual_chart` only approximate (`pass_01/notes.md` D8) | **Missing entirely** for true multi-tile IR boards; freeform **exists but weak** (no chart widgets) |
| **F12** | **Dense widescreen annex table packing** | 10+ column billed-business / FX annex grids at 1920×1080 with multi-level headers, stub columns, micro type — without clipping or Boardroom card padding eating width | PDF annex **p31–p37** (slides **30–36**); pass_02 filled key rows — density/header stubs still weaker than PDF IR grids (`pass_02/notes.md` annex discussion; compare_30+) | **Exists but weak** (`data_table` works for moderate grids; not IR annex density) |

### P3 — Product shell / plumbing (replication hygiene)

| # | Feature | What it enables | PDF slide + pass evidence | Missing entirely vs exists-but-weak |
|---|---------|-----------------|---------------------------|-------------------------------------|
| **F13** | **Handoff-native theme / token map through CLI** | `presentation.theme` (or equivalent) applied on `python -m impact_slides.renderer_v2 --handoff` load path — not only `render_deck(theme=)` Python kwarg | Pass_01 put Amex CSS variables in handoff; tokens **not** injected via CLI (`pass_01/notes.md` D12). Even with tokens, seal asset still needed (F6). | **Exists but weak** (theme kwarg in API; handoff JSON path undocumented / unwired) |
| **F14** | **IR / pass-through delivery chrome mode** | Optional shell without Boardroom “COVER” eyebrow, “Boardroom Earnings” foot brand, and on-slide control chrome that fight pixel parity | Visible on **every** `compare_XX.png` (pass_01 D10) | **Missing entirely** as an IR viewer / bare stage mode (Boardroom chrome is the product default) |
| **F15** | **Chart.js ↔ SVG `chart_config` parity** | One handoff contract: series_names, series_styles, y_axis_*, annotation, point labels behave identically regardless of `charts` feature flag | Pass_02 (Chart.js) vs pass_03 (SVG) billings `compare_03.png` path split documented in both notes | **Exists but weak** (two painters, divergent feature surface) |

---

## Divergence catalog (stable IDs → features)

Carried from pass notes for cross-reference:

| ID | Short name | Primary feature(s) | Settled type |
|----|------------|--------------------|--------------|
| D1 | Brand cover seal / lockup | F6, F14 | **B** |
| D2 | IR bullets + inline bold | F7 | **B** (geometry mitigated by freeform = residual A exhausted) |
| D3 | Pill-column comparison table | F4 | **B** |
| D4 | IR line-chart house style | F1, F2, F15 | **B** (SVG partial on dash/labels) |
| D5 | Chart \| hero KPI dual card | F5 | **B** |
| D6 | Guidance statement card | F8 | **B** |
| D7 | Brand section / trailing divider | F6 | **B** |
| D8 | Multi-panel / broken-axis boards | F10, F11 | **B** |
| D9 | Dense annex tables | F12 | **B** weak after content fill |
| D10 | Boardroom vs IR shell chrome | F14 | **B** (product choice) |
| D11 | Negative stacked reserve release | F3 | **B** (confirmed Chart.js **and** SVG) |
| D12 | Theme from handoff JSON | F13 | **B** weak |
| — | Floating VCE inset on expense | F9 | **B** (A attempted via key_stats; no-op) |

---

## Pass methodology (audit trail)

| Step | Location |
|------|----------|
| PDF rasters (primitive PyMuPDF only) | `extracted/pdf_page_00.png` … `pdf_page_43.png` |
| Vision/text transcription | `extracted/slides.json` (+ `pdf_text_dump.txt`) |
| Pass 01 handoff → render → diffs | `passes/pass_01/` |
| Pass 02 handoff-only A fixes (Chart.js) | `passes/pass_02/` |
| Pass 03 SVG probe + residual A | `passes/pass_03/` |
| This document | `GAP_ANALYSIS.md` |

**Hard constraints honored:**

- ≤10 comparison passes (**3 used**)
- New files only under `simulation/amex_q1_2026/`
- No production `impact_slides/` renderer, layout, CSS, schema, or test edits
- Every **(B)** claim above cites a concrete PDF slide index and `pass_XX/screenshots/compare_YY.png` (or pass notes with that path)
- Features listed are **observed gaps**, not invented roadmap wishes beyond what the Amex deck demonstrated

---

## Recommended implementation order (for a future renderer track)

Not in scope for this simulation — recorded only so the gap list is actionable:

1. **F3** negative stacks + **F1/F2/F15** IR line house style + annotation (unblocks billings + credit story)  
2. **F4** pill-column table + **F9** floating table insets (unblocks summary + expense statement pages)  
3. **F5** chart\|hero dual card (unblocks acquisitions / marketing KPI pages)  
4. **F6/F7/F8** brand + bullet + guidance chrome (unblocks narrative pack)  
5. **F10/F11/F12** specialized boards + annex density  
6. **F13/F14** theme plumbing + optional IR shell (parity hygiene)

---

## Conclusion

`renderer_v2` can already **ingest and present** a full Amex-sized earnings deck as Boardroom HTML: tables, stacked/line charts, disclosures, freeform escapes, and KPI metrics all fire. It **cannot yet end-to-end visually replicate** the PDF as standalone IR HTML because the Amex house system depends on specialized chart coloring/annotation, below-axis stacks, pill statement tables, chart+hero compositions, brand seal covers, and rich single-column sheets — none of which are expressible (or fully honored) from handoff JSON today.

After three handoff-only passes, remaining gaps are **capability gaps (B)**. This document is the deliverable; closing F1–F15 requires a separate renderer implementation track outside this simulation.
