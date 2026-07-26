# Pass 02 — engage N5 exterior segment names + funding $ stack tops

**Date:** 2026-03-26
**Handoff:** pass_01 + type-(A) diffs only
**Render:** Chart.js `--self-contained` → 44 slides OK
**Mean MAE similarity:** **89.30%** (−0.06 vs p01)
**vs v4 pass_02:** 89.15% (**+0.15 pp**)

## Handoff diffs vs pass_01

| Slide | Change | Lever |
|------:|--------|-------|
| 27 both tiles | `exterior_segment_names: true` | N5 |
| 27 Funding Mix | `stack_totals` + `stack_total_labels: ["$210","$219"]` | F11+ $ tops on % mix |
| 27 Deposit Programs | `stack_totals` + `stack_total_labels: ["$151","$157"]` | same |
| 05 spend callouts | elbow `text: ""` (band keeps label) | R2 micro de-dupe |
| various | mojibake top_total fix (en-dash / middot) | A content |

## Scores

| Metric | Value |
|--------|------:|
| mean MAE | **89.30%** |
| mean SSIM-approx | 89.46% |
| Δ vs pass_01 | **−0.06 pp** |
| slide 27 | 77.88 → **75.43** (−2.45) — N5 column packs denser; wire holds |
| slide 05 | 73.91 → 73.90 flat — R2 still B |

## Checklist (engaged evidence)

| ID | Status | Evidence |
|----|--------|----------|
| **N5** | **partial — wire resolved, packing weak** | DOM `plugins.segmentNames.items` on slide 27; `compare_27.png` colored exterior names right of last bar (Deposits / Unsecured / Short-term…). PDF multi-line column recipe only partly matched; light-card packing + B unit suffix residual | residual **(B) weak** |
| **F11+ residual** | skin path + N5 wire; packing residual | navy heads still (IR on); exterior labels now paint; PDF light rounded cards not selected this pass | packing **(B)** / light-skin is A for p03 |
| **R2** | **still gap** | elbow text cleared; geometry still ≠ PDF pill+chevron (`compare_05.png`) | **(B)** |
| **N2** | mostly resolved (carried) | years inside bars | weak residual only |
| **N3/N4** | mostly resolved (carried) | dual sets on provision | weak residual |
| **R3** | dropped wontfix | cover 82.18 | excluded |

## Type (A) left
- Funding drop `tile_skin: ir` → light Boardroom cards matching PDF gray-card chrome (pass_03). Expect MAE reclaim; N5 stays on.

## Type (B)
- R2 geometry, F4+/R1/R4/F12+ polish, N5 packing density finish, N2 weight polish

## Artifacts
`handoff.json`, `output/`, `screenshots/`, `diff_scores.json`, `diff.png`
