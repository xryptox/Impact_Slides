# Pass 01 — v5 baseline (current renderer, frozen v4 pass_02 handoff)

**Date:** 2026-03-26
**Handoff:** verbatim copy of v4 sim `passes/pass_02/handoff.json` (44 slides, Chart.js, A-levers already engaged: `tile_skin=ir`, `bar_labels_inside=series`, `stack_totals`)
**Render:** `python -m impact_slides.renderer_v2 --handoff …/handoff.json --out …/output --self-contained` → 44 slides OK
**Compare:** Playwright 1920×1080 + MAE vs `extracted/pdf_page_XX.png`
**Mean MAE similarity:** **89.36%** (SSIM-approx **89.52%**)
**vs v4 pass_02:** 89.15% (**+0.21 pp**)
**vs v4 pass_01:** 89.19% (**+0.17 pp**)

## Scoring caveats

- White-canvas MAE inflates absolute scores; structural judgment is side-by-side (`screenshots/compare_XX.png`).
- Handoff frozen at v4's best engaged recipe so deltas are **renderer walls** vs v4 (plus any new levers not used yet).
- **R3 Centurion seal:** by-design wontfix per CONTEXT.md brand-asset rule — cover MAE recorded but excluded from gap counts.

## Overall scores

| Metric | Value |
|--------|------:|
| n_slides | 44 |
| mean MAE sim. | **89.36%** |
| mean SSIM-approx | 89.52% |
| Δ vs v4 pass_02 | **+0.21 pp** |

### Worst structural slides

| Slide | PDF topic | MAE % | Primary observation |
|------:|-----------|------:|---------------------|
| 05 | U.S. Consumer Platinum | **73.91** | R2 callout geometry still weak (band over plot + tiny under-axis Refresh ≠ PDF mid-plot blue pill + large navy Refresh chevron); N2 years **do paint inside bars** now; F10 90–100 holds; IR heads hold |
| 27 | Funding and Deposits | **77.88** | IR navy heads hold; PDF light cards + **exterior multicolor segment name column** missing (N5 A-lever exists in current renderer but not engaged); in-bar % OK |
| 00 | Cover | **82.18** | R3 wontfix — generic seal_lockup vs Centurion (excluded) |
| 11 | New Acquisitions | **83.00** | R4 hero type scale residual |
| 12 | companion | 84.31 | packing residual |
| 14 | Total Provision | **86.75** | **N3/N4 dual labels + N1 table land**; +1.15 pp vs v4; exterior-style segment legend column vs PDF still cosmetic residual |

### Material movers vs v4 pass_02

| Slide | v4 p02 | v5 p01 | Δ pp | Driver |
|------:|-------:|-------:|-----:|--------|
| 03 | 90.45 | **92.74** | **+2.29** | stage/line chrome polish (R1 path stronger) |
| 18 | 89.31 | **91.95** | **+2.64** | related |
| 14 Provision | 85.60 | **86.75** | **+1.15** | N3 dual value+total+negchip path |
| 19 pills | 91.43 | **92.04** | **+0.61** | F4+ residual polish |
| 05 Platinum | 73.93 | 73.91 | −0.02 | flat |
| 27 Funding | 77.87 | 77.88 | +0.01 | flat (N5 not engaged) |
| 02 pills | 92.41 | 90.82 | **−1.59** | packing silhouette swing |
| 00 Cover | 82.18 | 82.18 | 0.00 | R3 excluded flat |

## v4 open-list re-test (fresh DOM + screenshot)

| ID | Pass_01 status | Evidence | A vs B |
|----|----------------|----------|--------|
| **R2** | **still gap / weak** | Slide 5: band+elbow+chevron nodes present; `compare_05.png` HTML has mid-plot teal capsule + tiny under-Q1 Refresh ≠ PDF left elbow into pill + large bottom navy chevron | Residual **(B)** geometry; micro-copy A only cosmetic |
| **N2 residual** | **mostly resolved visually** (stronger than v4) | `compare_05.png` right: years **2025/2026 chips inside bars**; DOM `_labels` triple years; weight still slightly light vs PDF bold but recipe family matches | residual polish **(B) weak** only |
| **F11+ residual / N5** | F11 skin **holds**; N5 **A available unengaged** | `gl-tile-ir`=4; `compare_27.png` navy heads OK, no exterior name column. charts.py/shell now support `exterior_segment_names` | **(A)** engage N5 next pass; residual packing may remain B |
| **N3 residual / N4** | **mostly resolved** | Provision HTML: datalabels `value` + `total` + `negchip` sets; in-segment `$1,223` + tops `$1,150`… + `($73)`/`($24)` chips; `compare_14.png` dual-label recipe family; MAE +1.15 pp | path **closed**; freestanding reserve-rate cells + right exterior legend residual **(B) weak** |
| **F4+** | **partial / weak residual** | `gl-pill-free`=2; slide 19 +0.61 pp; slide 02 −1.59 pp swing; freestanding navy-header PDF columns still denser | **(B)** residual |
| **R1** | **improved / weak residual** | `chartjs-flat`=8; slide 03 **+2.29 pp** — stage chrome stronger than v4 | **(B)** weak residual |
| **R4** | **partial / weak residual** | `compare_11.png` 83.00% (+0.05); hero dual % structure | **(B)** weak |
| **F12+** | **partial / weak residual** | annex high MAE on white; multi-level IR header stubs | **(B)** weak |
| **R3** | **dropped: wontfix** | `compare_00.png` 82.18% — generic seal_lockup accepted by CONTEXT.md brand-asset rule | excluded |

### DOM probes

| Probe | Result |
|-------|--------|
| `.gl-tile-ir` | 4 |
| callout band/elbow/chevron on slide 5 | 1 each |
| F10 min:90 / max:100 | present |
| N2 year triples in datalabels | present |
| N3/N4 value+total+negchip | present on provision |
| N5 segmentNames | **not engaged** (no exterior_segment_names in handoff) |
| N1 under-chart table | present on slide 14 |

## Match vs diverge

### Matched / improved under frozen handoff
- F10+ anniversary domain (carried)
- N1 secondary_visual under stacked_bar (carried)
- N2 in-bar year chips now **visually paint** (v4 wire-only → v5 paint)
- N3/N4 dual stack labels + signed paren chips (new vs v4 "totals replace segments")
- IR tile skin path, Chart.js self-contained deck, F3 signed stacks
- R1 stage MAE lift on several line slides

### Type (A) remaining for pass_02
1. Funding tiles: `exterior_segment_names: true` + explicit `stack_total_labels` ($210/$219, $151/$157) — N5 + $ tops on 100%-mix boards
2. Optional R2 callout text de-dupe (elbow empty, band keeps label) — expect still B after

### Type (B) confirmed
- R2 geometry recipe
- F4+ / R1 residual / R4 / F12+ polish
- N2 weight polish (minor)
- Cover R3 excluded

## Artifact index

- `handoff.json`, `output/presentation.html`
- `screenshots/html_slide_XX.png`, `compare_XX.png`
- `diff_scores.json`, `diff.png`
- `_screenshot_and_diff.py` (PASS_NUM=1)
