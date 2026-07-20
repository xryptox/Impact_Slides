# Gap Analysis: renderer_v2 vs Amex Q1'26 Earnings PDF (AFTER F-feature work)

**Simulation:** `simulation/amex_q1_2026/`  
**Source of truth:** `C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf` (44 pages, 16:9)  
**Renderer under test:** current `impact_slides.renderer_v2` (post–F-feature work: brand cover/divider, broken y-axis, multi_panel, annex_table, handoff theme + chrome_level, IR datalabels, pill_comparison, chart_hero_dual, guidance_statement_card, etc.)  
**Baseline (BEFORE):** `simulation/amex_q1_2026_v1_pre_fixes/GAP_ANALYSIS.md` — v1 prioritized gaps **F1–F15**  
**Method:** PyMuPDF rasterize (200 DPI) → vision transcription → ≤10 **handoff-only** comparison passes → Playwright 1920×1080 screenshots + side-by-side PDF/HTML diffs  
**Hard constraint:** no production renderer/layout/CSS/schema/test edits; new files only under `simulation/amex_q1_2026/`

**Passes run:** **3** (stopped early — residual pure-(A) handoff items exhausted; remaining divergences are type **(B)** capability / recipe gaps)

---

## Scoring caveats (read first)

| Caveat | Implication |
|--------|-------------|
| **Pixel MAE similarity is white-biased** | Mean ~89% is inflated by shared white canvas. Use as *relative trend* within this run, **not** IR layout fidelity. |
| **Ground truth is visual side-by-sides** | Judge structure from `passes/pass_XX/screenshots/compare_YY.png` and `diff.png`, not mean % alone. |
| **Type (A) vs (B)** | **(A)** = fixable by editing handoff JSON only. **(B)** = no handoff expression exists, or expression exists but is too weak to match the PDF recipe without renderer work. |
| **Chart path** | All three v2 passes used the **Chart.js** path (`charts` feature on). v1 pass_03 forced SVG; that probe is not repeated here because Chart.js now honors much of `chart_config`. |
| **1:1 PDF index** | `load.normalize_handoff` forces slide 1 to `title_or_opening` and can inject an extra cover if layout differs. Handoffs kept slide 1 as opening to preserve 44-slide alignment. |

Evidence roots (relative to this folder):

- PDF rasters: `extracted/pdf_page_XX.png`
- Pass artifacts: `passes/pass_0N/{handoff.json,output/,screenshots/compare_XX.png,diff_scores.json,notes.md}`
- v1 baseline: `../amex_q1_2026_v1_pre_fixes/`

---

## Per-pass summary table

| Pass | Chart path | Mean MAE sim. | Mean SSIM-approx | Top 3 divergences | Types |
|-----:|------------|--------------:|-----------------:|-------------------|-------|
| **01** | Chart.js | **89.16%** | ~89.3% | (1) Platinum dual-card IR board (bars/horizontal retention/Refresh arrow) unmatched — `compare_05.png`; (2) Provision reserve releases still absolute above zero — `compare_14.png`; (3) Cover Centurion seal absent + brand_cover blocked as slide 1 — `compare_00.png` | **B / B / B** (+ residual A on chart-type choices, hero pairing) |
| **02** | Chart.js | **89.25%** (+0.09) | 89.43% | (1) Platinum geometry still fails after grouped_bar remap — `compare_05.png`; (2) Funding multi_panel cards sparse / segments weak vs PDF — `compare_27.png`; (3) Acquisitions hero **value↔label pairing still inverted** vs PDF — `compare_11.png` | **B / B / A** (s18 line+table **A closed**, +8.85 pp) |
| **03** | Chart.js | **89.25%** (0.00) | 89.43% | (1) Platinum IR recipe still unmatched — `compare_05.png` (72.8%); (2) Funding tall 100%-stack cards + side legends / top $ callouts still weak — `compare_27.png` (78.4%); (3) Provision F3 still B (`Reserve… [73…24]`) — `compare_14.png` | **B / B / B** (s11 pairing **A closed**; no material residual A) |

### Per-pass A closures vs B confirmations

| Pass | Meaningful (A) closures | Confirmed / refined (B) |
|-----:|-------------------------|-------------------------|
| 01 | Full deck remap onto new IR layouts (`pill_comparison`, `chart_hero_dual`, `ir_bullet_sheet`, `guidance_statement_card`, `brand_divider`, `multi_panel`, `annex_table`); theme + `chrome_level=minimal` live | F3 abs stack; cover seal + load force; freestanding pill geometry weak; specialized platinum board weak; generic brand mark |
| 02 | s18 combo→**line_chart** + `$B` under-table (+8.85 pp); platinum chart *families* → grouped_bar; funding structure → multi_panel stacks; denser brand_mark_svg | F3 remains; horizontal retention + Refresh chrome missing; multi_panel y-break weak; funding IR card recipe weak; acquisitions pairing still wrong |
| 03 | s11 **66% Millennial top / 73% Fee bottom**; funding 2-tile density + $-in-label; platinum PDF titles | Same B set; MAE flat; **stop** — only capability/recipe gaps remain |

**Stop rationale after pass 03:** Residual pure-(A) list from pass_02 was exhausted. Further handoff churn will not produce below-axis stacks, Centurion cover seals, freestanding IR pill columns, horizontal anniversary boards, or IR dual stack-card chrome. ≤10 budget preserved (3 used).

**Worst structural scores (pass_03):**

| Slide | PDF topic | MAE % | Primary gap |
|------:|-----------|------:|-------------|
| 05 | U.S. Consumer Platinum | 72.83 | F10/F11 residual recipe (horizontal bars, dual navy cards, Refresh callout) |
| 27 | Funding and Deposits | 78.37 | Multi-panel thin tiles vs IR tall 100% cards + side legends |
| 11 | New Acquisitions | 83.10 | content A closed; residual hero type scale / card chrome |
| 14 | Total Provision | 84.31 | **F3** below-axis negatives |
| 43 | Trailing brand | 85.11 | Brand plate / seal art (far better than v1 ~20%) |

---

## Before / after delta: v1 F1–F15 → current renderer

Headline deliverable. Status is from **fresh** v2 passes (not inherited from v1 conclusions).

| ID | v1 finding (summary + evidence) | v2 status | v2 evidence | Notes |
|----|----------------------------------|-----------|-------------|-------|
| **F1** IR line-chart house style (domain, dashed series, on-point %, stage) | Chart.js ignored config; SVG partial (forced ticks weak). PDF p4 / slide **03** | **largely resolved (partial)** | `pass_01–03/screenshots/compare_03.png`; Chart.js config honors: min0/max15, stepSize5, dashed Reported, datalabels %, series names | Residual weak: Boardroom card chrome vs PDF flat stage; visual zero-padding in some shots. **Capability exists on Chart.js path.** |
| **F2** Chart annotation / callout layer | Annotation field never painted (Chart.js + SVG). Slide **03** | **resolved (capability)** | Leap Year dashed box on `compare_03.png` / `compare_18.png`; HTML `chartjs-annotation` | Placement still coarse (A/weak B cosmetic); paint path works. |
| **F3** Below-axis negative stacked bars | True negatives absorbed above zero on Chart.js **and** SVG. PDF p15 / slide **14** | **still gap** | handoff signed values → Chart.js `Reserve Build/(Release)` `data: [73…24]` abs; `pass_03/screenshots/compare_14.png` tops wrong vs PDF `$1,150` / `($73)` geometry | **Highest-priority remaining P0.** KPI chips can show `($24)` but geometry cannot. |
| **F4** Pill-column comparison table | Missing entirely (row grid only). Slides **02**, **19** | **partial** | `gl-pill-col` headers on `pass_03/screenshots/compare_02.png` and expense `compare_19.png` | Headers exist; freestanding rounded statement columns + exterior row labels still short of PDF. |
| **F5** Chart \| hero-KPI dual card | Missing (`dual_chart` ≠ chart+metrics). PDF p12 / slide **11** | **resolved (structure)** | `chart_hero_dual` left stack + right 66%/73% heroes `compare_11.png`; pass_03 fixed pairing A | Residual weak: hero typography/card chrome scale vs PDF giant prose block. |
| **F6** Brand cover + section divider assets | Missing; dividers ~20–24% MAE white pages. Slides **00**, **22**, **43** | **partial** | brand_divider two-tone + inlined mark: `compare_22.png` **87.3%**, `compare_43.png` **85.1%** (was ~20–24%); cover still no Centurion seal `compare_00.png` | Dividers **major progress**. Cover seal still gap: `brand_cover` not usable as slide 1 without `load.normalize_handoff` title force/injection. Mark art = generic SVG ≠ Centurion. |
| **F7** IR bullet sheet + inline rich-text bold | Geometry weak / bold missing. PDF p2 / slide **01** | **resolved (capability)** | `ir_bullet_sheet` + `<strong>` (12 spans) `compare_01.png` **93.1%** | Residual weak styling: IR large centered type vs Boardroom scale. |
| **F8** IR guidance / statement card | Weak freeform only. PDF p22 / slide **21** | **resolved (capability)** | `guidance_statement_card` / `gl-guid-bar` rows `compare_21.png` **91.8%** | Residual weak: full-width thin card vs centered IR plaque. |
| **F9** Floating inset KPI on table slides | key_stats no-op on expense data_table. PDF p20 / slide **19** | **resolved on pill_comparison** | VCE **44.7%** inset paints on expense pill layout `compare_19.png` | Tied to pill_comparison recipe, not bare data_table. |
| **F10** Broken / discontinuous y-axis | Missing entirely. Platinum slide **05** | **partial / weak** | handoff `y_axis_break` + ymin90/­ymax100; HTML has `chartjs-axis-break` count 2; paint on multi_panel retention still tends 0→100 vertical grouped bars `compare_05.png` | Field exists but does not deliver PDF horizontal 90–100 anniversary board. |
| **F11** Multi-region / multi-panel IR dashboard host | Missing (no multi-chart freeform). Platinum/capital/funding | **partial** | `gl-multi-panel` host works (platinum, capital, funding) `compare_05/20/27.png` | Host **exists**; IR dual tall card chrome, side legends, packing density **weak**. |
| **F12** Dense widescreen annex table | Weak packing / headers. Annex slides **30–36** | **partial** | `annex_table` layouts + header_groups; annex MAE commonly ~90–95% (`compare_28–36` area) | Better density than v1; multi-level IR header stubs still not PDF-perfect. |
| **F13** Handoff-native theme through CLI | Theme JSON unwired on CLI path | **resolved** | `presentation.theme` Amex tokens applied via CLI render; navy CSS vars / theme in HTML (pass_01 notes) | No longer a blocker for Amex toning. |
| **F14** IR / pass-through chrome mode | Boardroom COVER eyebrow / foot chrome always on | **resolved** | `<body class="gl-chrome-minimal">` via `chrome_level=minimal` across passes | Residual on-slide slide numbers still present (product chrome, weak). |
| **F15** Chart.js ↔ SVG `chart_config` parity | Path-split (many fields Chart.js-only ignored) | **largely resolved on Chart.js path** | dashed, domain, datalabels, annotation paint without suppressing charts (`compare_03/18.png`) | Full bidirectional parity not re-probed via SVG suppress; F1 residual cosmetic differences remain. |

### Summary counts (F1–F15)

| Status | IDs |
|--------|-----|
| **Resolved (capability)** | F2, F5 (structure), F7, F8, F9 (on pill), F13, F14 |
| **Largely resolved / partial** | F1, F4, F6 (dividers yes / cover seal no), F10, F11, F12, F15 |
| **Still a hard gap** | **F3** |

Mean MAE trend: v1 final **86.19%** → v2 **89.25%** (+3.06 pp). Brand dividers alone moved from ~20–24% to ~85–87% MAE.

---

## Prioritized future-feature list (still open)

Only gaps that remain after v2 verification. **Resolved F2/F5/F7/F8/F9/F13/F14 drop off.**  
Priority = impact on end-to-end Amex IR replication × residual severity observed in this run.

### P0 — Blocks matching core credit / story geometry

| # | Feature | What it enables | PDF slide + pass evidence | Missing entirely vs exists-but-weak |
|---|---------|-----------------|---------------------------|-------------------------------------|
| **F3** | **Below-axis negative stacked bars (signed reserve release)** | Provision stacks with write-offs above zero and **reserve releases drawn below** the axis; stack tops match IR (`$1,150` with `($73)`, `$1,251` with `($24)`) instead of absolute absorb | PDF **p15 Total Provision** (slide **14**); `pass_03/screenshots/compare_14.png`; Chart.js config still `data: [73.0…24.0]` absolute | **Exists but broken / missing geometry:** schema accepts negative-ish series but Chart.js path absolute-values stack segments. Closest remaining **missing-entirely on paint**. |
| **R1** *(new residual from F1)* | **IR line-chart stage chrome (lighter card / zero-locked frame)** | PDF-flat chart stage + navy domain rails without heavy Boardroom card padding eating vertical zero | PDF **p4 / p19** slides **03 / 18**; `pass_03/screenshots/compare_03.png`, `compare_18.png` (Leap Year + dual lines + `$B` work; stage chrome still Boardroom) | **Exists but weak** after F1 work. |

### P1 — Blocks specialized multi-panel IR boards

| # | Feature | What it enables | PDF slide + pass evidence | Missing entirely vs exists-but-weak |
|---|---------|-----------------|---------------------------|-------------------------------------|
| **F10+** | **Horizontal bar chart + anniversary retention board** | Grouped *horizontal* bars in a 90–100% window with year labels inside bars (Platinum right card) | PDF **p6** slide **05**; `pass_03/screenshots/compare_05.png` (HTML stays vertical 0–100 grouped bars despite ymin/break config) | **Missing entirely** for true horizontal bars; **y_axis_break exists but weak** on multi_panel Chart.js. |
| **R2** | **Callout arrow / elbow annotation + band chrome** | `+ ~6 percentage points` elbow arrow spanning bar tops; Refresh chevron under category axis | Same **slide 05**; `pass_03/compare_05.png` text-only annotation vs PDF geometric callout | **Missing entirely** as drawable chrome (text annotation ≠ geometry). |
| **F11+** | **IR dual tall card multi_panel recipe** | Equal tall gray cards, exterior side legends, freestanding top `$` totals, badge callouts (Funding Mix / Deposit Programs) | PDF **p28** slide **27**; `pass_03/screenshots/compare_27.png` (2-tile host works; thin tiles, tiny secondary segments, labels-in-title hack for $) | **Exists but weak** (multi_panel host present; IR card packing/legends weak). |
| **F4+** | **Freestanding pill statement columns** | Exterior row labels + fully separated rounded column shells (not header-pills over spreadsheet body) | PDF **p3 / p20** slides **02 / 19**; `pass_03/screenshots/compare_02.png` | **Exists but weak** (`gl-pill-col` headers only). |

### P2 — Brand seal / cover path

| # | Feature | What it enables | PDF slide + pass evidence | Missing entirely vs exists-but-weak |
|---|---------|-----------------|---------------------------|-------------------------------------|
| **F6+** | **Cover seal path without index break** | Allow `brand_cover` (or seal inject) as slide 1 **without** `load.normalize_handoff` forcing `title_or_opening` / inserting an extra cover that breaks 1:1 PDF mapping | PDF **cover p1** slide **00**; `pass_03/screenshots/compare_00.png` (two-tone OK, Centurion+ribbon absent); pass_01 notes on load force | **Exists but blocked** (`brand_cover` layout exists; load path prevents safe use as deck index 0). |
| **R3** | **First-class Brand mark / seal asset pack** | Trademark-quality Centurion + ribbon lockup (not generic star-in-circle SVG handoff authors invent) | Cover **00** + appendix divider **22** + trailing **43** (`compare_00/22/43.png`) | **Missing as product asset**; schema accepts `brand_mark_svg` (A can supply better paths, not true seal). |

### P3 — Density polish (lower urgency)

| # | Feature | What it enables | PDF slide + pass evidence | Missing entirely vs exists-but-weak |
|---|---------|-----------------|---------------------------|-------------------------------------|
| **F12+** | **Annex multi-level header stubs** | True IR multi-header annex precision / stub columns at 1920×1080 | Annex slides **30–36**; `pass_03` annex MAE high but header geometry still weaker than PDF | **Exists but weak** (`annex_table` already large step from v1). |
| **R4** | **Hero dual type scale / companion card chrome** | Giant % + multi-line narrative block as peer soft-gray card matching PDF acquisitions right column | PDF **p12** slide **11**; `pass_03/compare_11.png` (structure resolved; scale/chrome residual) | **Exists but weak** after F5. |

---

## What renderer_v2 already does well

Credit where due — verified on this Amex pack with the current renderer:

1. **Self-contained 44-slide IR deck delivery** — CLI `--handoff` → `--self-contained` HTML; Playwright 1920×1080巡査 clean `.slide` set (`pass_03/output/presentation.html`).
2. **Chart.js IR house cues now live** — dashed secondary series, 0–15 domains with forced ticks, on-point datalabels, Leap Year annotation boxes (`compare_03.png`, `compare_18.png`). This was the core v1 P0 failure.
3. **New layout recipes unblocked major pages** — `chart_hero_dual` (acquisitions), `pill_comparison` + VCE inset (summary/expense), `ir_bullet_sheet` + bold spans (highlights), `guidance_statement_card` (2026 guidance), `brand_divider` full-bleed two-tone (appendix openers — MAE ~85–87% vs v1 ~20%), `multi_panel` multi-chart host, `annex_table` density.
4. **Handoff theme + minimal chrome** — Amex token map from presentation JSON; `gl-chrome-minimal` strips heavy Boardroom product chrome (v1 F13/F14).
5. **Native disclosure / speaker notes / 1:1 content carriage** — full numerical story of the pack can be carried in handoff and rendered without schema collapse once layouts are chosen correctly (pass_02 s18 remap is the type-A lesson).

---

## Divergence catalog (stable IDs after v2)

| ID | Short name | Primary feature(s) | Settled type | Status vs v1 |
|----|------------|--------------------|--------------|--------------|
| D1 | Brand cover seal / lockup | F6+, R3 | **B** | still open (cover path) |
| D2 | IR bullets + inline bold | F7 | **A exhausted** | **capability resolved** |
| D3 | Pill-column freestanding geometry | F4+ | **B weak** | partial (headers yes) |
| D4 | IR line-chart house style | F1/R1, F2, F15 | **largely closed** | much improved; stage chrome residual |
| D5 | Chart \| hero KPI dual | F5, R4 | **structure closed** | residual chrome weak |
| D6 | Guidance statement card | F8 | **closed capability** | residual plaque centering weak |
| D7 | Brand section / trailing divider | F6 | **mostly closed** | mark art residual |
| D8 | Multi-panel / broken-axis boards | F10+, F11+, R2 | **B** | host yes; recipe weak |
| D9 | Dense annex tables | F12+ | **B weak** | improved |
| D10 | Boardroom vs IR shell chrome | F14 | **closed** | minimal mode works |
| D11 | Negative stacked reserve release | **F3** | **B hard** | **unchanged / still broken** |
| D12 | Theme from handoff JSON | F13 | **closed** | wired |
| D13 | Revenue line + under-table | F1/R1 | closed via A layout | pass_02 s18 |
| D14 | Acquisitions pair semantics | content A | **closed pass_03** | — |

---

## Pass methodology (audit trail)

| Step | Location |
|------|----------|
| PDF rasters (primitive PyMuPDF only) | `extracted/pdf_page_00.png` … `pdf_page_43.png` |
| Vision/text transcription | `extracted/slides.json` |
| Pass 01 AFTER baseline (new IR layouts) | `passes/pass_01/` |
| Pass 02 residual A (platinum bars, s18 line, funding multi_panel, hero order attempt) | `passes/pass_02/` |
| Pass 03 last A (acquisitions pairing, funding 2-tile, titles) | `passes/pass_03/` |
| v1 BEFORE snapshot (reference only) | `../amex_q1_2026_v1_pre_fixes/GAP_ANALYSIS.md` |
| This document | `GAP_ANALYSIS.md` |

**Hard constraints honored:**

- ≤10 comparison passes (**3 used**)
- New files only under `simulation/amex_q1_2026/`
- No production `impact_slides/` renderer, layout, CSS, schema, or test edits
- Every remaining **(B)** claim cites a concrete PDF slide index and `pass_XX/screenshots/compare_YY.png`
- Features listed are **observed gaps**, re-verified on the current renderer (not cargo-culted from v1)

---

## Recommended implementation order (future renderer track)

Not in scope for this simulation — recorded only so the remaining list is actionable:

1. **F3** signed / below-axis stacked segments (unblocks provision credit story — sole remaining hard P0 from v1)  
2. **F10+ / R2** horizontal bars + anniversary window + geometric callouts (unblocks Platinum — worst MAE slide)  
3. **F11+** IR dual tall card multi_panel packing + side legends + top `$` total slots (unblocks Funding / Capital boards)  
4. **F4+** freestanding pill statement columns (summary + expense presentation fidelity)  
5. **F6+ / R3** cover-seal load path + brand asset pack (finish brand system after divider win)  
6. **F12+ / R1 / R4** annex header precision + stage chrome + hero type scale (polish)

---

## Conclusion

The **AFTER** picture versus `amex_q1_2026_v1_pre_fixes` is a real capability expansion: Chart.js now paints the IR line house (F1/F2/F15), new layouts cover bullets, guidance, pill headers + VCE inset, chart\|hero dual, brand dividers, multi_panel, annex density, handoff theme, and minimal chrome. Mean MAE rose ~3 pp, and brand divider slides jumped from ~20% to ~85%+.

What still blocks **end-to-end visual replication** of this Amex PDF as standalone HTML is a shorter, sharper list led by **F3 below-axis signed stacks**, then specialist multi-panel IR recipes (horizontal retention boards, dual funding cards, geometric callouts), freestanding pill geometry polish, and cover seal path/assets. After three handoff-only passes, remaining divergences are **capability/recipe gaps (B)**. This document is the deliverable; closing the Open list requires a separate renderer implementation track outside this simulation.
