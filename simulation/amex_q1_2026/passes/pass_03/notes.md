# Pass 03 — funding light-card packing (drop IR skin) + keep N5

**Date:** 2026-03-26
**Handoff:** pass_02 + funding tiles drop `tile_skin: "ir"` only (N5 + stack_total_labels retained). Platinum keeps IR.
**Render:** Chart.js `--self-contained` → 44 slides OK
**Mean MAE similarity:** **89.38%** (SSIM-approx **89.54%**) — best mean this run
**vs pass_02:** +0.08 pp; **vs pass_01:** +0.02 pp; **vs v4 pass_02:** **+0.23 pp**

## Handoff diffs vs pass_02

| Slide | Change | Lever |
|------:|--------|-------|
| 27 both tiles | remove `tile_skin: ir` → light tall Boardroom cards | F11 packing A |
| 27 | keep `exterior_segment_names` + `$` stack_total_labels | N5 / $ tops |

## Scores

| Metric | Value |
|--------|------:|
| mean MAE | **89.38%** |
| slide 27 | 75.43 → **78.81** (**+3.38**) — light cards reclaim silhouette; still short of PDF exterior column density |
| slide 05 | 73.90 flat — R2 unchanged |
| other checklist slides | flat vs p01/p02 |

## Checklist conclusive after A engage

| ID | Final status (this pass) | Evidence | Further A? |
|----|--------------------------|----------|------------|
| **N5** | **partial — wire resolved, packing weak** | `segmentNames` on funding; light `gl-tile-tall` (no ir); `compare_27.png` exterior names present but multi-line right column + card radius denser packing still short | **no material A** |
| **F11+ residual** | skin path holds on Platinum; Funding light packing better | `gl-tile-ir`=2 (platinum only); funding light cards closer family to PDF | residual packing **B weak** |
| **R2** | **still gap / weak** | `compare_05.png` still band-over-plot + small Refresh | **B** |
| **N2** | **mostly resolved** | years in bars on `compare_05.png` | weight polish only |
| **N3/N4** | **mostly resolved** | dual labels + negchips on `compare_14.png` | freestanding reserve cells residual |
| **F4+** | partial | tablets 02/19 | residual packing |
| **R1/R4/F12+** | weak residual | s03 lift carried;Hero 11/annex | polish |
| **R3** | dropped wontfix | cover excluded | — |

## Stop A-spiral

Remaining divergences are capability/chrome **(B)**. No pure-A checklist levers left that change status rows. Proceed to GAP_ANALYSIS.md.

## Artifacts
`handoff.json`, `output/`, `screenshots/`, `diff_scores.json`, `diff.png`
