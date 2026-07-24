# Pass 02 notes — residual (A) tuning after pass_01 unlocks

**Baseline:** `passes/pass_01/handoff.json`  
**Chart path:** Chart.js (self-contained)  
**Scores:** mean MAE sim **89.17%** (pass_01 89.03%, **Δ +0.14 pp**; v2 final 89.25%, **Δ −0.08 pp**)  
**N:** 44 HTML slides ↔ 44 PDF pages  

## What this pass changed (handoff only)

| Slide | Change | Intent |
|------:|--------|--------|
| 00 | Title pack adds `Q1'26`; subtitle = `APRIL 23, 2026` only | Cover content A |
| 03 / 18 | `chart_config.stage=flat` | R1 stage chrome A/B probe |
| 05 | PDF card titles; `band`+`elbow`+`chevron` callouts; series years `2025`/`2026`; clear tall-card badges/% tops | Platinum recipe A |
| 11 | Full PDF hero narrative labels; stage flat | R4 chrome A |
| 14 | PDF cyan/navy palette; leaner key_stats (2 chips); stage flat; signed stack retained | F3 cosmetic A |
| 27 | 3-band Funding Mix per PDF; exterior segment legend names; `$210 · $219` tops; no badges; stage flat | F11+ density A |

## Headline key-slide deltas (pass_01 → pass_02)

| Slide | Topic | p01 % | p02 % | Δ pp |
|------:|-------|------:|------:|-----:|
| 00 | Cover | 82.18 | 82.14 | −0.04 |
| 05 | Platinum | 71.19 | **75.00** | **+3.81** |
| 11 | Acquisitions | 83.50 | 83.55 | +0.05 |
| 14 | Total Provision | 84.49 | **86.81** | **+2.32** |
| 27 | Funding | 80.94 | 81.07 | +0.13 |
| 03 | Billed business | 90.42 | 90.42 | 0.00 |

**Worst structural (this pass):** 05 (75.0), 27 (81.1), 00 (82.1), 11 (83.5), 14 (86.8).

Evidence: `screenshots/compare_XX.png`, `diff_scores.json`, `diff.png`.

## A closures vs B confirmations

### Closed / improved (A)

1. **Platinum titles (A)** — PDF strings `Spend Growth is Accelerating` / `Retention Rates Remain High and Very Stable` now label tiles (`compare_05.png`). Contributed to +3.81 pp.
2. **Provision palette + KPI lean (A)** — Write-offs `#006FCF` / Reserve `#00175A` match PDF cold-cyan above / navy reserve; below-axis negatives still paint (`compare_14.png`, HTML `data: [-73.0, …, -24.0]`). MAE +2.32 pp.
3. **Funding 3-band collapse (A)** — Card ABS + ST merged into one light band like PDF ∪ exterior legend labels (`compare_27.png`). Small MAE lift.

### Confirmed (B) / weak-B after fresh evidence

1. **F10+ anniversary hard window still broken (B)** — Chart.js config **does** emit `"scales":{"x":{"ticks":{"min":90.0,"max":100.0}}}` and `chartjs-axis-break-v` for retention, but **paint is still 0→100** with mid-scale dashed break (`compare_05.png` right panel). Root cause observed: renderer places min/max under `ticks` rather than scale root `min`/`max`; Chart.js ignores and `beginAtZero` wins. **Exists but weak** — handoff cannot force a hard 90–100 domain today.
2. **R2 callout chrome still weak (B weak)** — `chartjs-callout-band` / elbow / chevron nodes present (counts: band3, elbow2, chevron3), but they do not form the PDF blue pill arrow spanning bar tops + navy Refresh chevron under Q1'26. Band text sits as a thin legend-style strip; chevron barely visible under axis (`compare_05.png`).
3. **`bar_labels_inside` paints category months, not year series (B weak)** — datalabels `_labels` matrix is `[["January","February","March"], …]` even when series_names are `2025`/`2026`. PDF wants year digits inside each bar. Handoff cannot redirect the label source.
4. **F11+ tall-card packing SSI regression when slots emptied (learning / A for p03)** — pass_02 cleared `top_total` / `badge` / `side_legend` on platinum tiles to match PDF card titles-only chrome. That dropped `gl-tile-tall` engagement, producing **very short multi_panel bands** (look at `compare_05.png` right: charts crushed into thin ribbons with huge white). PDF dual full-height navy cards cannot be recovered without either (a) re-engaging tall slots (A next) or (b) denser multi_panel default chrome (B). MAE still rose thanks to titles/callouts, but height is worse than p01.
5. **F4 freestanding pills** — untouched; same `gl-pill-free` shells as p01 (`compare_02.png` 89.7%). Structure present; packing still not PDF three vertical columns with exterior left labels. **B weak** (CSS/layout packing).
6. **F6+/R3 cover seal recipe** — `brand_cover` + `seal_lockup` still center tiny generic star-badge vs PDF left white title + large lower-right Centurion watermark (`compare_00.png` 82.1%). Load path works; **asset + layout recipe gap**.
7. **R1 stage=flat** — `chartjs-flat` class count = 9 in HTML; MAE on slide 03/18 **unchanged** at 90.4 / 89.3. Field engages; visual delta vs PDF flat IR stage is residual/cosmetic (**weak B**).
8. **R4 hero dual** — longer narrative labels present; type scale still Boardroom cards not PDF giant 66%/73% prose blocks (`compare_11.png` 83.5%, ~flat).
9. **F3 capability** — remains **resolved** (signed stacks paint). Residual is IR label density ($1,150 tops, bottom reserve-rate **row under axis**, side legend band) — polish, not negative-path failure.

## Residual pure-(A) list for pass_03 (small)

| Item | Plan |
|------|------|
| Platinum height | Re-enable `top_total`/`side_legend` (even empty-looking) **or** a non-empty side_legend so `gl-tile-tall` engages without changing PDF-ish labels |
| Provision secondary table | Ensure reserve-rate row secondary_visual is actually painted under chart (may need layout support check — if secondary ignored → B) |
| Cover | Limited A left (already on brand_cover); stop after one more content tweak if MAE stagnant |

Everything else for F10 window, callout IR band recipe, bar inside-year labels, pill packing, Centurion watermark, and dual navy IR card chrome is **(B)**.

## Stop-rule progress

- Pass budget: **2 / 10 used**.
- F3 remains capability-closed (reconfirmed this pass with palette polish).
- Platinum still worst slide; pure A left primarily = re-engage tall multi_panel height without undoing title wins.
- Do **not** yet write final GAP_ANALYSIS — at least one more A pass on tall chrome, then stop if only B remains.

## Mean MAE caveat

Deck mean +0.14 pp hides the structural story: Platinum +3.8 and Provision +2.3 are the meaningful ticks. Cover still drags mean vs v2's title_or_opening recipe. Judge F-status from side-by-sides, not mean alone.
