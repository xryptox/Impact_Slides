# Pass 03 notes — pure-(A) tall multi_panel re-engagement + residual B probes

**Baseline:** `passes/pass_02/handoff.json`  
**Chart path:** Chart.js (self-contained)  
**Scores:** mean MAE sim **89.10%** (pass_02 89.17% **Δ −0.07 pp**; pass_01 89.03%; v2 final 89.25% **Δ −0.15 pp**)  
**N:** 44 HTML slides ↔ 44 PDF pages  

## What this pass changed (handoff only)

| Slide | Change | Intent |
|------:|--------|--------|
| 00 | Title without inline `Q1'26`; subtitle = `Q1'26 · APRIL 23, 2026`; empty key_stats | Cover A micro-tweak |
| 05 | Re-enable `gl-tile-tall` via non-empty `top_total` + `side_legend` while **keeping PDF card titles**; retain band/elbow/chevron | F11+ height A |
| 11 | `packing_mode=metric-led` + full PDF ownership prose on 66%/73% | R4 A probe |
| 14 | Single KPI chip; keep signed stack; attach `secondary_visual` reserve-rate table | B-probe secondary gate |
| 27 | `$210B · $219B` tops; FDIC so_what; tall chrome retained | F11+ polish A |

## Headline key-slide deltas (pass_02 → pass_03)

| Slide | Topic | p02 % | p03 % | Δ pp |
|------:|-------|------:|------:|-----:|
| 00 | Cover | 82.14 | 82.18 | +0.04 |
| 05 | Platinum | **75.00** | **72.33** | **−2.67** |
| 11 | Acquisitions | 83.55 | 83.05 | −0.50 |
| 14 | Total Provision | 86.81 | 86.83 | +0.02 |
| 27 | Funding | 81.07 | 81.04 | −0.03 |
| 03 | Billed business | 90.42 | 90.42 | 0.00 |

**Worst structural (this pass):** 05 (72.3), 27 (81.0), 00 (82.2), 11 (83.1), 14 (86.8).

Evidence: `screenshots/compare_XX.png`, `diff_scores.json`, `diff.png`.

## DOM / paint toggles verified

| Probe | Result | Evidence |
|-------|--------|----------|
| Platinum `gl-tile-tall` | **engaged (count=2)** after top_total + side_legend | HTML slide 05; compare_05 shows taller light cards than pass_02 ribbons |
| `y_axis_min=90` on retention | still under `ticks.min`; paint **0→100** with mid break dashed line | compare_05 right; Chart.js config present |
| Provision signed data | `data: [-73.0, 222.0, 125.0, 141.0, -24.0]`; `y.min ≈ -80.3` | HTML slide 14; negatives paint below axis (compare_14) |
| `secondary_visual` reserve-rate | **not painted** on stacked_bar (`tables=0`, no `chart-split`) | HTML confirm + compare_14 missing under-chart row |
| Cover `brand_cover` + `seal_lockup` | load path OK (44 slides); seal is **center tiny generic star badge** | compare_00 |
| Funding tall | 2× `gl-tile-tall` + B-suffix tops | compare_27 |

## A closures vs B confirmations

### Closed / improved (A)

1. **Tall multi_panel engagement is pure A** — recipes.py only adds `gl-tile-tall` when `top_total | badge | side_legend` is non-empty. Confirmed for platinum + funding.
2. **F3 remains capability-closed** — reconfirmed with leaner KPI; negatives still paint.

### Confirmed (B) — residual pure-(A) exhausted

1. **F10+ hard 90–100 window still broken (B)** — min/max live under `ticks`, Chart.js ignores; bars paint 0→100 (`compare_05.png`).
2. **R2 callout chrome still weak (B)** — band/elbow/chevron nodes present but do not form PDF blue pill arrow + navy Refresh chevron under axis (`compare_05.png`). Inside callout text nearly invisible against bars.
3. **`bar_labels_inside` = category months, not series years (B weak)** — HTML retention shows exterior Chart.js legend 2025/2026; PDF wants year digits **inside** each bar (`compare_05.png`).
4. **F11+ IR dual navy card chrome (B weak)** — tall host engages but tiles remain light Boardroom cards with exterior legends; PDF is full-height navy-headed dual cards with exterior segment labels and top $ totals flush to cards (`compare_05.png`, `compare_27.png`). Re-engaging tall **lowered** MAE vs pass_02 titles-only because extra chrome (top_total + side legend stack) fights the PDF silhouette more than bare short tiles did.
5. **F4 freestanding pills (B weak)** — untouched; `gl-pill-free` shells exist (~37 gl-pill hits on slide 02) but packing ≠ PDF three vertical columns + exterior left labels (`compare_02.png` 89.7%).
6. **F6+/R3 cover seal (B)** — `brand_cover` allowed as slide 1 without injection (v2 load-path block is **gone**). Remaining gap is **asset + placement recipe**: tiny centered generic seal vs PDF left white title stack + large lower-right Centurion watermark (`compare_00.png` 82.2%).
7. **secondary_visual under stacked_bar missing entirely for non-line layouts (B)** — `render_chart` gate `layout == "line_chart"` confirmed; reserve-rate row cannot ride under provision (`compare_14.png`).
8. **R1 stage=flat residual (B weak)** — class engages; MAE unchanged on KPI line slides.
9. **R4 hero type scale (B weak)** — metric-led packing did not liberate giant 66%/73% prose blocks; still side KPI cards (`compare_11.png` 83.0%, slight regression).
10. **IR bar total callouts / $ tops above stacks (B weak)** — provision PDF shows `$1,150` / `$1,405` category tops + side series legend; renderer paints Chart.js tops as in-bar numbers only (`compare_14.png`).

## Stop decision

- Pass budget: **3 / 10 used**.
- Pure handoff-(A) list from pass_02 **exhausted** and pass_03 probes **regressed** the worst structural slides (Platinum −2.67 pp) while confirming B gates.
- Best mean in this v3 run = **pass_02 89.17%** (still −0.08 pp vs v2 final 89.25%); **do not chase mean** — structural F-status is the deliverable.
- Remaining divergences are **all type (B)** capability / recipe gaps → **stop adjusting**, write `GAP_ANALYSIS.md`.

## Mean MAE caveat

Pass_03 mean drift (−0.07 pp) is a chrome-silhouette penalty, not a reverse of F3/F6-path wins. Side-by-sides remain the ground truth.
