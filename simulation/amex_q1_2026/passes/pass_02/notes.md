# Pass 02 — pure-A scrape (legend/chrome knobs)

**Date:** 2026-04-26  
**Base:** pass_01 handoff (T1 geometry + T2 knobs)  
**Render:** `python -m impact_slides.renderer_v2 --self-contained` → 44 slides OK  
**Mean MAE similarity:** **89.49%** (SSIM-approx **89.69%**)  
**vs pass_01 (89.33%):** **+0.16 pp**  
**vs v6 final (89.31%):** **+0.18 pp**

## Purpose

Exercise remaining **type (A)** handoff knobs only — no renderer edits. Target:

1. Slide 27 double-legend chrome (Chart.js legend + `side_legend` + `exterior_segment_names`)
2. Slide 11 exterior segment names (PDF right-of-stack recipe) + grid suppress
3. Slide 14 axis/grid chrome vs freestanding reserve furniture (A scrape only)
4. Hold slide 05 R2 recipe identical to p01 so T1 geometry result stays frozen

## Handoff deltas vs pass_01

| Slide | Change | Intent |
|------:|--------|--------|
| **27** Funding | Drop both tiles' `side_legend`; set `show_gridlines=false`, `show_y_axis=false` | Remove dual exterior columns; float exterior names alone |
| **11** New Acquisitions | `exterior_segment_names=true` + T2-ish knobs (18/22/14/3/20/140); `show_gridlines=false`, `stack_totals=true` | Match PDF series-name column on stack |
| **14** Total Provision | `show_gridlines=false`, `show_y_axis=false` | Cleaner board chrome (furniture still missing) |
| **05** Platinum | **unchanged from p01** | After failed A trial (drop `side_legend` + empty `top_total` → 71.5%; restore `top_total` bare of legend → 74.3%), freeze p01 recipe at **76.77%** |

**Failed A on s05 (reverted):** IR `tile_skin` body layout widens the chart wrap when `side_legend` is stripped (709→853 px). Capsule elementary geometry still repositions correctly (`calloutGeometry`), but histogram silhouette + IR head packing diverge harder from the PDF light board. No pure-A path to PDF-title-only boards with calling geometry silicone simultaneously.

## Checklist scores

| Slide | Topic | p01 % | p02 % | Δ pp | Read |
|------:|-------|------:|------:|-----:|------|
| 00 | Cover | 82.18 | 82.18 | 0.00 | **R3 wontfix — excluded** |
| 02 | Summary Financial | 90.56 | 90.56 | 0.00 | **F4+** packing residual (no A knob) |
| 03 | Total Billed Business | 92.62 | 92.62 | 0.00 | **R1 accepted divergence** (D11) |
| 05 | Platinum | 76.77 | **76.77** | 0.00 | **R2/T1** frozen; geometry holds (`slide05_geometry.json` px matches p01) |
| 11 | New Acquisitions | 85.67 | **87.93** | **+2.26** | Exterior names **on**; hero % packing still short (**R4** residual) |
| 14 | Total Provision | 86.07 | **86.45** | **+0.38** | Grid/Y off helps chrome slightly; **N6** boxed reserve cells still missing |
| 19 | pills sibling | 91.86 | 91.86 | 0.00 | F4+ family |
| 27 | Funding and Deposits | 78.65 | **82.99** | **+4.34** | Double-legend purge is the biggest A win; packing density residual remains |

## DOM / geometry

- Deck probes: elbow=1, stem=1, chevron=1, band=0; `segmentNames` scripts=7; `calloutGeometry` present.
- Slide 05 geometry (post-freeze, equals p01): capsule `left=97.54px width=543.52px`, stem h=150.8px, chevron `top=531.4px` on wrap 709×562.

## Per open-list ID

| ID | Status this pass | Evidence | A/B |
|----|------------------|----------|-----|
| **R2** | **partial** — T1 geometry holds (p01 verified, held here); PDF chrome residual | `compare_05.png` 76.77%; geometry JSON px | geometry **resolved by T1**; chrome **B** (large center Refresh, L-elbow silhouette, IR head chips vs PDF title-only) |
| **N5 / F11 packing** | **partial ↑** — A double-legend fix landed; packing still weak | `compare_27.png` **82.99%** (+4.34 vs p01; +4.39 vs v6 78.60). Exterior names sole right column; bars still narrower / cards less rounded / totals in head band not on-stack | packing **B weak**; pure double-legend was **A done** |
| **F4+** | **still-gap / weak** | `compare_02.png` 90.56 unchanged | **B** — no packing A keys |
| **N6** | **still-gap / weak** | `compare_14.png` 86.45 (+0.38 chrome only). Under-chart is a dense sheet row + KPI footer, not freestanding `2.9%` boxes + left label chip + exterior series legend | **B furniture** |
| **R4** | **still-gap / weak** (chart side improved) | `compare_11.png` **87.93%**. Exterior names paint; right hero cards still dual stack of 66/73 not co-card giant type with title clique | hero type **B**; exterior stack names **A done** |
| **R1** | **closed: accepted divergence per r4 D11** | s03 92.62 | excluded |
| **F12+** | **closed: accepted divergence per r4 D11** | annex white MAE | excluded |
| **N2 chip weight** | **closed: accepted divergence per r4 D11** | YOLO chips | excluded |
| **R3** | **dropped: wontfix per CONTEXT.md** | cover 82.18 | excluded |

## Type summary

| Class | Items |
|-------|-------|
| **(A) closed this pass** | s27 drop `side_legend` (+ axis chrome); s11 `exterior_segment_names` + grids off; s14 grids/Y off |
| **(A) tried & failed / no lift** | s05 strip `side_legend` / empty `top_total` — MAE **down** 5+ pp; reverted |
| **(B) remaining** | R2 chevron/L-elbow/IR board recipe; N5 multi_panel card/bar packing after legend fix; F4+ pill packing; N6 freestanding reserve furniture; R4 dual-card hero type scale |

## Next

Remaining divergences are **capability (B)** (or accepted/wontfix). No further high-confidence pure-A levers on the open checklist.  
Candidates for a short pass_03 only if desired: micro-tune s27 T2 font/offset (expect noise-band), leave R2/N6/F4+/R4 alone.

Likely stop after documenting B residuals + GAP_ANALYSIS once one more optional tune is ruled flat, or proceed to GAP_ANALYSIS now with 2 passes of evidence.

## Artifacts

- `handoff.json`, `output/presentation.html`
- `screenshots/compare_XX.png`, `html_slide_XX.png`
- `diff_scores.json`, `diff.png`
- `dom_probes.json`, `slide05_geometry.json`
- `_screenshot_and_diff.py`
