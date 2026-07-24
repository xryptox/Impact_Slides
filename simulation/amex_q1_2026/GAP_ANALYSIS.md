# Gap Analysis v3: renderer_v2 vs Amex Q1'26 Earnings PDF (AFTER round-2 fidelity)

**Simulation:** `simulation/amex_q1_2026/`  
**Source of truth:** `C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf` (44 pages, 16:9)  
**Renderer under test:** current `impact_slides.renderer_v2` **after** round-2 fidelity work (negative-sign load path, horizontal_bar + anniversary retention window fields, geometric callout layer, IR dual tall-card multi_panel slots, freestanding pill statement columns, cover-seal load path, first-class brand seal asset pack hook, stage chrome / annex banding / hero scale polish).  
**Baseline (BEFORE / PRE-round-2):** `simulation/amex_q1_2026_v2_pre_round2/GAP_ANALYSIS.md` — v2 scored F1–F15 after the first F-feature wave; headline was 7 resolved, 7 partial, **1 hard gap (F3)**, plus residuals **R1–R4**.  
**Method:** PyMuPDF rasterize (200 DPI) → vision-carried `extracted/slides.json` → ≤10 **handoff-only** comparison passes → Playwright 1920×1080 screenshots + side-by-side PDF/HTML MAE diffs  
**Hard constraint:** no production renderer/layout/CSS/schema/test edits; new files only under `simulation/amex_q1_2026/`

**Passes run:** **3** (stopped early — residual pure-(A) handoff items exhausted; remaining divergences are type **(B)** capability / recipe gaps)

---

## Scoring caveats (read first)

| Caveat | Implication |
|--------|-------------|
| **Pixel MAE similarity is white-biased** | Mean ~89% is inflated by shared white canvas. Use as *relative trend* within this run and vs v2, **not** IR layout fidelity by itself. |
| **Ground truth is visual side-by-sides** | Judge structure from `passes/pass_XX/screenshots/compare_YY.png` and `diff.png`, not mean % alone. |
| **Type (A) vs (B)** | **(A)** = fixable by editing handoff JSON only. **(B)** = no handoff expression exists, or expression exists but is too weak / mis-wired to match the PDF recipe without renderer work. |
| **Chart path** | All three v3 passes used the **Chart.js** path (self-contained). |
| **Fresh verification** | Every v2 open/partial claim was re-tested on the **current** renderer. Status below is from **this** run's DOM + screenshots, not inherited from v2 conclusions. |
| **Best mean pass vs MAE story** | Best deck mean in this run is **pass_02 (89.17%)**. Pass_03 re-engaged tall multi_panel chrome and **regressed** Platinum MAE (−2.67 pp) while confirming B gates — structural closures (F3 paint, brand_cover load) must be judged on side-by-sides, not mean alone. |

Evidence roots (relative to this folder):

- PDF rasters: `extracted/pdf_page_XX.png`
- Pass artifacts: `passes/pass_0N/{handoff.json,output/,screenshots/compare_XX.png,diff_scores.json,notes.md}`
- v2 BEFORE snapshot: `../amex_q1_2026_v2_pre_round2/`
- v1 historical only: `../amex_q1_2026_v1_pre_fixes/` (do not use as primary baseline)

---

## Per-pass summary table

| Pass | Chart path | Mean MAE sim. | Mean SSIM-approx | Top 3 divergences | Types | Δ vs prior / vs v2 final (89.25%) |
|-----:|------------|--------------:|-----------------:|-------------------|-------|-----------------------------------|
| **01** | Chart.js | **89.03%** | ~89.2% | (1) Platinum dual-card IR board / anniversary window — `compare_05.png` (71.2%); (2) Cover seal placement generic center vs Centurion watermark — `compare_00.png` (82.2%); (3) Funding dual stack card chrome — `compare_27.png` (80.9%) | **B / B / B** (F3 signed path **capability-closed** on this pass) | vs v2: **−0.22 pp** |
| **02** | Chart.js | **89.17%** (+0.14) | ~89.4% | (1) Platinum still 0→100 horizon + weak callout chrome despite titles — `compare_05.png` (75.0%); (2) Cover seal recipe — `compare_00.png` (82.1%); (3) Funding segment density/exterior labels — `compare_27.png` (81.1%) | **B / B / A→B** (titles/palette/3-band A closed; F10 ticks.min **B confirmed**) | vs v2: **−0.08 pp**; best mean this run |
| **03** | Chart.js | **89.10%** (−0.07) | ~89.3% | (1) Platinum tall re-engage adds chrome but still misses navy dual board / 90–100 window — `compare_05.png` (72.3%); (2) Funding still light Boardroom cards vs IR tall navy — `compare_27.png` (81.0%); (3) Cover residual seal/layout — `compare_00.png` (82.2%) | **B / B / B** (pure A exhausted; tall A engaged but silhouette penalty) | vs v2: **−0.15 pp** |

### Per-pass A closures vs B confirmations

| Pass | Meaningful (A) closures | Confirmed / refined (B) |
|-----:|-------------------------|-------------------------|
| 01 | Structural unlocks exercised: `brand_cover`+`seal_lockup` as slide 1 (44-slide map held), `horizontal_bar_chart`+callouts on platinum, **signed stacked provisions** (`data: [-73…-24]`), multi_panel tall-card fields | F10 window paint still 0–100; callout chrome weak; inside-bar labels = months; cover seal asset/placement; freestanding pill packing; dual navy IR card chrome |
| 02 | Platinum PDF card titles (+3.81 pp); provision cyan/navy palette + lean KPIs (+2.32 pp); funding 3-band collapse; stage=flat engaged on line residuals | **F10** `y_axis_min` under `ticks` ignored by Chart.js; `bar_labels_inside` hard-wires categories; emptying tall slots crushes multi_panel height; stage=flat MAE-neutral |
| 03 | Re-engaged `gl-tile-tall` via `top_total`+`side_legend` (DOM count=2 on platinum + funding); secondary_visual reserve-rate payload attached for gate probe | Tall chrome **exists but weak** vs PDF navy dual cards (MAE regression); **secondary_visual ignored** on `stacked_bar_chart` (line_chart-only gate); remaining list **all B** → **stop** |

**Stop rationale after pass 03:** Residual pure-(A) list from pass_02 was exhausted. Pass_03 confirmed tall engagement is A-tunable but IR dual-navy board chrome, hard 90–100 window, inside-year bar labels, geometric callout paint, freestanding pill packing, Centurion watermark, under-stacked secondary tables, and giant hero type scale all require renderer work. ≤10 budget preserved (3 used).

**Worst structural scores (pass_02 = best mean; pass_03 = final evidence pass):**

| Slide | PDF topic | p02 % | p03 % | Primary gap |
|------:|-----------|------:|------:|-------------|
| 05 | U.S. Consumer Platinum | 75.00 | 72.33 | F10+/R2/F11+ recipe (90–100 window, callout arrows, navy dual cards, inside-year labels) |
| 27 | Funding and Deposits | 81.07 | 81.04 | F11+ IR dual tall 100%-stack cards + exterior segment labels |
| 00 | Cover | 82.14 | 82.18 | F6+/R3 seal asset + left-title / lower-right watermark recipe |
| 11 | New Acquisitions | 83.55 | 83.05 | R4 hero type scale / companion card chrome |
| 14 | Total Provision | 86.81 | 86.83 | F3 **paint resolved**; residual IR tops + under-chart reserve-rate row + side legend |

### Mean MAE vs v2 final

| Snapshot | Mean MAE sim. | Δ vs v2 final |
|----------|--------------:|--------------:|
| v2 final (`amex_q1_2026_v2_pre_round2` pass_03) | **89.25%** | — |
| v3 pass_01 | 89.03% | −0.22 pp |
| v3 pass_02 (best mean) | 89.17% | −0.08 pp |
| v3 pass_03 (stop) | 89.10% | −0.15 pp |

**Read carefully:** mean MAE did **not** advance past v2. Round-2 still delivered **structural** wins (especially **F3 below-axis stacks** and **cover load path**) that pixel-MAE on white canvases under-counts. Treat the before/after delta table as the headline, not the mean column.

---

## Before / after delta: v2 open-partial gaps → current renderer (v3)

Headline deliverable. Each row re-tested on the **current** renderer with fresh pass evidence.

| ID | v2 finding (summary + v2 slide/pass) | v3 status | v3 slide/pass evidence | Notes |
|----|--------------------------------------|-----------|------------------------|-------|
| **F3** Below-axis negative stacked bars | Hard gap: Chart.js absorbed signed reserve releases above zero (`Reserve… data: [73…24]`). PDF p15 / slide **14**; v2 `pass_03/compare_14.png` | **resolved (capability)** | v3 HTML slide 14 emits `data: [-73.0, 222.0, 125.0, 141.0, -24.0]` and `scales.y.min ≈ -80.3`; negatives paint below axis on `pass_01–03/screenshots/compare_14.png` | Round-2 signed load path **works**. Residual polish only: PDF `$1,150` category tops, side series legend, under-chart reserve-rate row (secondary_visual gate — see new residual). **Drops off hard-gap list.** |
| **F1 residual / R1** IR line-chart stage chrome | Chart.js honors domain/dash/datalabels; residual Boardroom card vs PDF flat IR stage. Slide **03 / 18** | **partial (weak residual)** | `chart_config.stage=flat` → `chartjs-flat` class count=9 in pass_02 HTML; MAE on slide 03 stays **90.42%** across p01–p03 (`compare_03.png`) — field engages, visual delta cosmetic | **Exists but weak** stage chrome. Not a missing field. |
| **F4+** Freestanding pill statement columns | Headers-only `gl-pill-col` vs PDF freestanding rounded columns + exterior row labels. Slides **02 / 19** | **partial (improved structure, packing still weak)** | Live DOM has `gl-pill-free` shells (slide 02 ~37 `gl-pill*` hits); `pass_0*/screenshots/compare_02.png` **89.71%** flat across passes | v2 "headers-only" claim is **outdated** — freestanding shell path landed. Residual = CSS/layout packing density vs three dense PDF vertical statement columns. **Exists but weak.** |
| **F6+** Cover seal path without index break | `brand_cover` blocked as slide 1 by `load.normalize_handoff` (force title_or_opening / injector). Cover pivot used title_or_opening. | **resolved (load path)** | v3 pass_01–03 handoffs set slide 0 `layout_type=brand_cover` and render **44 slides** 1:1 with PDF (no injected cover). `pass_03/screenshots/compare_00.png` | Load-path block from v2 is **gone**. Placement/layout of seal still fails IR recipe → folded into **R3** residual below. |
| **F10+** Horizontal bar + anniversary retention board | Field existed; multi_panel paint still tended 0→100 vertical/grouped; horizontal path incomplete. Slide **05** | **partial / still weak (critical residual)** | platinium right tile is true `horizontal_bar_chart` with grouped years; handoff sends `y_axis_min/max=90/100` + `y_axis_break`; HTML has `ticks.min:90` + `chartjs-axis-break-v`; **paint remains 0→100** with dashed mid-scale break (`pass_02–03/screenshots/compare_05.png`) | Renderer places min/max under `scales.x.ticks` rather than scale-root `min`/`max` (`charts.py`); Chart.js ignores. Also `bar_labels_inside` paints **category months**, not series years. **Exists but weak / mis-wired.** Worst structural slide. |
| **F11+** IR dual tall-card multi_panel | Host yes; IR dual tall navy cards + side legends + top $ slots weak. Slides **05 / 27** | **partial (slot path yes; recipe weak)** | `gl-tile-tall` engages when `top_total|badge|side_legend` non-empty (`recipes.py`; pass_03 DOM tall=2 on slides 05 & 27). Visual: light Boardroom cards + exterior legends, not PDF full-height navy-headed dual boards (`compare_05.png`, `compare_27.png`). pass_02 titles-only (no tall) MAE-better on platinum; pass_03 tall re-engage **−2.67 pp** | Slot machinery **landed**. Missing IR card skin (navy header band, exterior segment labels flush to card, denser 100% stack packing). **Exists but weak.** |
| **R2** Geometric callout layer (band / elbow / chevron) | Missing or non-paint relative to PDF blue pill arrow + Refresh chevron. Slide **05** | **partial (nodes paint; recipe weak)** | pass_02/03 handoff callouts `band`+`elbow_arrow`+`chevron` present; HTML nodes count band/elbow/chevron >0; PDF blue pill spanning bar tops + navy under-axis Refresh chevron **not** matched (`compare_05.png`) | Callout **layer exists**. Geometry/chrome recipe far from Amex IR arrows. **Exists but weak.** |
| **R3** First-class brand seal asset pack | Generic star-in-circle SVG; no Centurion + ribbon watermark. Slides **00 / 22 / 43** | **still gap (asset + placement)** | `brand_mark=seal_lockup` paints a **small centered generic badge** above centered title (`pass_03/screenshots/compare_00.png` 82.2%). PDF = large left white title + lower-right Centurion line-art watermark. Dividers still better than v1 but mark art residual | Named pack hook is not a trademark-quality Centurion lockup. **Missing as product asset** (schema can take SVG, not a true seal pack). |
| **R4** Hero dual type scale / companion card chrome | Structure via `chart_hero_dual`; giant % + multi-line narrative peer card residual. Slide **11** | **partial (structure held; chrome residual)** | 66% top / 73% bottom pairing correct; packing_mode metric-led probe no giant type liberation; `pass_03/compare_11.png` **83.05%** | **Exists but weak** after F5. |
| **F12+** Annex multi-level header stubs | annex_table large step; multi-header IR stubs still weaker than PDF. Annex **28–36** | **partial (unchanged residual)** | Annex MAE still commonly ~90–95% in pass_03 scores (`compare_28–36` area); no new A lever stripped residual | Not re-chased past pass_01 carriage; **exists but weak.** Not a regression. |

### v2 F-status summary rollup → v3

| Bucket | v2 (pre-round-2) | v3 (this run, fresh) |
|--------|------------------|----------------------|
| **Hard gap** | **F3** | **none** from v2 hard list (F3 closed) |
| **Partial / weak** | F1/R1, F4, F6 cover, F10, F11, F12, R2, R3, R4 | R1, F4+, F10+, F11+, R2, R3, R4, F12+ (F6+ **load path closed**; asset → R3) |
| **Resolved since v2** | — | **F3** (signed stacks), **F6+ load path** (brand_cover as slide 1), horizontal_bar tile path (family exists; window still weak under F10+) |

### NEW residuals discovered in v3 (not named as open in v2 future list)

| ID | Finding | Evidence | Missing entirely vs exists-but-weak |
|----|---------|----------|-------------------------------------|
| **N1** | **`secondary_visual` data_table only attaches when `layout_type == line_chart`** — reserve-rate row under stacked provision cannot paint even when payload is present | handoff slide 14 carries secondary_visual; HTML `tables=0`, no `chart-split`; `pass_03/screenshots/compare_14.png` missing under-chart row that PDF has | **Exists but gated/weak** (works on line+table slides e.g. revenue patterns; missing for stacked_bar) |
| **N2** | **`bar_labels_inside` hard-wires category matrix, not `series_names`** — cannot express PDF year-inside-bar retention labels via handoff | Chart.js `_labels` = months; series 2025/2026 only exterior legend; `pass_02–03/compare_05.png` | **Exists but weak / wrong label source** |
| **N3** | **Category total callouts above stacked bars** (`$1,150`, `$1,405` …) — PDF paints sum tops + signed parentheses under axis; renderer in-bar series labels only | `pass_03/compare_14.png` | **Missing entirely** (or only via generic datalabels, not IR total-top recipe) |

---

## Prioritized future-feature list (still open after v3)

Only gaps that remain after **fresh** v3 verification. **F3 and F6+ load-path drop off.**  
Priority = impact on end-to-end Amex IR replication × residual severity observed in this run.

### P0 — Unblocks the worst structural slides

| # | Feature | What it enables | PDF slide + pass evidence | Missing entirely vs exists-but-weak |
|---|---------|-----------------|---------------------------|-------------------------------------|
| **F10+** | **Hard axis domain on horizontal_bar (scale-root min/max)** | True 90–100 anniversary retention window so bars read as high-90s clusters, not sparrow bars on 0–100 | PDF **p6** slide **05** right card; `pass_02/screenshots/compare_05.png`, `pass_03/screenshots/compare_05.png` (HTML `ticks.min=90` ignored) | **Exists but weak / mis-wired** (`y_axis_min` accepted in handoff; Chart.js options put min under `ticks`) |
| **R2** | **IR geometric callout chrome (pill band arrow + under-axis chevron)** | PDF `+ ~6 percentage points` blue pill spanning bar tops with elbow stems; navy **Refresh** chevron under Q1'26 | PDF **p6** slide **05** left card; `pass_02–03/screenshots/compare_05.png` | **Exists but weak** (band/elbow/chevron nodes paint; geometry ≠ IR recipe) |
| **N2** | **Inside-bar label source = series name (years)** | `2025` / `2026` digits painted **inside** each retention bar (PDF format) | PDF **p6** slide **05** right; `pass_03/screenshots/compare_05.png` | **Exists but weak** (`bar_labels_inside` uses categories) |

### P1 — Dual-card IR dashboards + provision polish

| # | Feature | What it enables | PDF slide + pass evidence | Missing entirely vs exists-but-weak |
|---|---------|-----------------|---------------------------|-------------------------------------|
| **F11+** | **IR dual tall navy card multi_panel skin** | Full-height navy header bands, flush exterior segment labels, denser 100% stack packing, top `$` totals integrated into card chrome (not Boardroom light tiles + side legend list) | PDF **p6 / p28** slides **05 / 27**; `pass_03/screenshots/compare_05.png`, `compare_27.png` (tall slots gather DOM class but silhouette fails) | **Exists but weak** (`gl-tile-tall` slot path works when fields non-empty) |
| **N1** | **secondary_visual under non-line chart layouts** | Reserve-rate (or any under-chart) table on stacked provision boards | PDF **p15** slide **14**; `pass_03/screenshots/compare_14.png` + HTML gate in `recipes.render_chart` | **Exists but gated** (line_chart only) |
| **N3** | **Stacked category total / signed parentheses tops** | `$1,150` above bar + `($73)` below axis as IR total callouts | PDF **p15** slide **14**; `pass_03/screenshots/compare_14.png` | **Missing entirely** as first-class IR recipe |

### P2 — Pill packing + brand seal finish

| # | Feature | What it enables | PDF slide + pass evidence | Missing entirely vs exists-but-weak |
|---|---------|-----------------|---------------------------|-------------------------------------|
| **F4+** | **Freestanding pill column packing density** | Three (or N) fully separated rounded statement columns with exterior left row labels matching summary/expense IR boards | PDF **p3 / p20** slides **02 / 19**; `pass_0*/screenshots/compare_02.png` (`gl-pill-free` present; packing short) | **Exists but weak** |
| **R3** | **First-class Centurion seal asset + cover placement recipe** | Large lower-right line-art watermark (or left locked title + seal WR) rather than tiny centered generic badge | PDF **cover p1** slide **00**; `pass_03/screenshots/compare_00.png` (also dividers **22 / 43**) | **Missing as product asset**; placement recipe weak even with `seal_lockup` |

### P3 — Density / type polish (lower urgency)

| # | Feature | What it enables | PDF slide + pass evidence | Missing entirely vs exists-but-weak |
|---|---------|-----------------|---------------------------|-------------------------------------|
| **R1** | **Flatter IR stage chrome for line charts** | Near-PDF flat canvas (less Boardroom card padding/shadow) even when `stage=flat` | PDF **p4** slide **03**; `pass_02–03/screenshots/compare_03.png` (MAE flat @ 90.4% after stage=flat) | **Exists but weak** |
| **R4** | **Hero dual giant type scale** | 66% / 73% multi-line narrative peer card in IR acquisitons right column | PDF **p12** slide **11**; `pass_03/screenshots/compare_11.png` | **Exists but weak** after `chart_hero_dual` |
| **F12+** | **Annex multi-level header stubs** | True IR multi-header annex precision at 1920×1080 | Annex slides **28–36**; pass_03 annex MAE high but header geometry still weaker than PDF | **Exists but weak** (`annex_table`) |

---

## What renderer_v2 already does well

Credit where due — verified on this Amex pack with the **post-round-2** renderer:

1. **Self-contained 44-slide IR deck delivery** — CLI `--handoff` → `--self-contained` HTML; Playwright 1920×1080рти clean `.slide` set (`pass_03/output/presentation.html`).
2. **Signed / below-axis stacked bars (F3)** — Chart.js now paints true negatives with y-domain below zero (`compare_14.png`; HTML `data: [-73…-24]`). This was v2's sole remaining hard gap and is the headline round-2 win.
3. **Cover load path (F6+ path)** — `brand_cover` is a valid deck index 0 without injector breaking 1:1 PDF mapping (44 slides held across all v3 passes).
4. **Horizontal bar family + callout layer hooks** — multi_panel can host `horizontal_bar_chart` tiles; band/elbow/chevron callout nodes emit (even if IR chrome recipe is weak).
5. **Tall multi_panel slots** — `top_total` / `badge` / `side_legend` engage `gl-tile-tall` (recipes path confirmed pass_03).
6. **Freestanding pill shells** — `gl-pill-free` path is live (v2 "headers-only" is outdated).
7. **Chart.js IR house cues** — dashed secondary series, forced domains/ticks, on-point datalabels, annotation boxes on line slides (`compare_03.png`, `compare_18.png` ~90%+).
8. **Layout catalog** — `chart_hero_dual`, `pill_comparison`, `ir_bullet_sheet`, `guidance_statement_card`, `brand_divider`, `multi_panel`, `annex_table`, handoff theme + `chrome_level=minimal` all carry usable structure for the majority of the 44-page pack.
9. **Mean floor ~89% MAE** with white-canvas bias — bulk KPI/line/annex slides already sit 90–95% once content is mapped (type-A lesson from prior runs still holds).

---

## Divergence catalog (stable IDs after v3)

| ID | Short name | Primary feature(s) | Settled type | Status vs v2 |
|----|------------|--------------------|--------------|--------------|
| D1 | Brand cover seal / lockup art + placement | R3 (F6+ path closed) | **B** | path **improved**; asset still open |
| D2 | IR bullets + inline bold | F7 | closed pre-v3 | unchanged |
| D3 | Pill-column freestanding packing | F4+ | **B weak** | structure improved (`gl-pill-free`); packing residual |
| D4 | IR line-chart house / stage chrome | F1/R1, F2, F15 | **largely closed**; R1 weak | stage=flat engages, cosmetic residual |
| D5 | Chart \| hero KPI dual | F5, R4 | structure closed; R4 weak | unchanged residual |
| D6 | Guidance statement card | F8 | closed capability | unchanged |
| D7 | Brand section / trailing divider | F6 dividers | mostly closed | mark art residual via R3 |
| D8 | Multi-panel / broken-axis boards | F10+, F11+, R2, N2 | **B** | host + horizontal + tall slots yes; window/callout/skin weak |
| D9 | Dense annex tables | F12+ | **B weak** | unchanged |
| D10 | Boardroom vs IR shell chrome | F14 | closed | unchanged |
| D11 | Negative stacked reserve release | **F3** | **closed capability** | **RESOLVED vs v2 hard gap** |
| D12 | Theme from handoff JSON | F13 | closed | unchanged |
| D13 | Revenue line + under-table | F1 | closed via line+secondary | secondary **still line-gated** (N1) |
| D14 | Acquisitions pair semantics | content A | closed | pairing holds in v3 |
| D15 | Under-chart secondary on stacked_bar | **N1** | **B gated** | **new residual** |
| D16 | Stacked category total tops | **N3** | **B missing** | **new residual** |

---

## Pass methodology (audit trail)

| Step | Location |
|------|----------|
| PDF rasters (primitive PyMuPDF only) | `extracted/pdf_page_00.png` … `pdf_page_43.png` |
| Vision transcription (carried + verified) | `extracted/slides.json` |
| Pass 01 AFTER unlocks (signed stacks, brand_cover, hbar+callouts, multi_panel) | `passes/pass_01/` |
| Pass 02 residual A (PDF titles, palette, 3-band funding, stage=flat) | `passes/pass_02/` |
| Pass 03 last A (tall re-engage, secondary gate probe, cover micro-tweak) | `passes/pass_03/` |
| v2 BEFORE snapshot (primary baseline) | `../amex_q1_2026_v2_pre_round2/GAP_ANALYSIS.md` |
| v1 historical only | `../amex_q1_2026_v1_pre_fixes/GAP_ANALYSIS.md` |
| This document | `GAP_ANALYSIS.md` |

**Hard constraints honored:**

- ≤10 comparison passes (**3 used**)
- New files only under `simulation/amex_q1_2026/`
- No production `impact_slides/` renderer, layout, CSS, schema, or test edits
- Every remaining **(B)** claim cites a concrete PDF slide index and `pass_XX/screenshots/compare_YY.png`
- Features listed are **observed gaps**, re-verified on the current renderer (not cargo-culted from v2)
- Resolved v2 items (**F3**, **F6+ load path**) dropped from the future-feature list

---

## Recommended implementation order (future renderer track)

Not in scope for this simulation — recorded only so the remaining list is actionable:

1. **F10+** scale-root min/max (and force_ticks) on horizontal_bar — unblocks anniversary window on worst slide  
2. **R2 + N2** IR callout chrome + series-name inside-bar labels — finishes Platinum left/right recipe  
3. **F11+** IR dual navy tall-card skin for multi_panel — unblocks Platinum + Funding boards  
4. **N1 + N3** secondary_visual on stacked layouts + category total tops — finishes Provision IR furniture (F3 paint already works)  
5. **F4+** freestanding pill packing density  
6. **R3** Centurion seal asset pack + cover placement recipe  
7. **R1 / R4 / F12+** stage chrome, hero type scale, annex header precision (polish)

---

## Conclusion

The **v3 AFTER** picture versus `amex_q1_2026_v2_pre_round2` is a **structural** round-2 win led by **F3 below-axis signed stacks** (v2's only hard gap → capability closed with live negative Chart.js data and below-axis paint) and **F6+ cover load path** (`brand_cover` as slide 1 without breaking 1:1 mapping). Horizontal_bar tiles, callout nodes, tall multi_panel slots, and freestanding pill shells all **exist** where v2 marked them missing or blocked.

What still blocks **end-to-end visual replication** of this Amex PDF is no longer a single hard negative-path failure. It is a **shorter recipe list**: hard horizontal axis clamp (F10+), IR callout/inside-year label chrome (R2/N2), dual navy tall-card skin (F11+), under-stack secondary + category totals (N1/N3), pill packing (F4+), and Centurion seal art/placement (R3). Mean MAE was essentially flat vs v2 (−0.08 pp at best) — as in prior runs, white-canvas MAE under-reports structural closures and over-penalizes chrome-silhouette experiments (pass_03 tall re-engage).

After three handoff-only passes, remaining divergences are **capability/recipe gaps (B)**. This document is the deliverable; closing the Open list requires a separate renderer implementation track outside this simulation.
