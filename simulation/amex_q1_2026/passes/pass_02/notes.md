# Pass 02 — A-only handoff micro-tunes (post-pass_01 freeze)

**Date:** 2026-07-26
**Handoff:** pass_01 + R2 elbow-only declare + provision `exterior_segment_names` + funding skin hard-clear
**Render:** `python -m impact_slides.renderer_v2 --self-contained` → 44 slides OK
**Mean MAE similarity:** **89.31%** (SSIM-approx **89.50%**)
**vs pass_01 (89.29%):** **+0.02 pp** mean (noise)
**vs v5 pass_03 final (89.38%):** **−0.07 pp** mean

## Purpose

Close remaining pure-(A) checklist levers named in pass_01 without touching renderer code. Confirm whether R2 finances geometry via elbow-only declare, and whether provision N6 can pull exterior series names through the existing segmentNames wire.

## Handoff deltas vs pass_01

| Slide | Change | Class hoped |
|------:|--------|-------------|
| 05 | Drop co-declared `band`; single `elbow_arrow` `from=0..to=4` `value=11` carrying `"+ ~6 percentage points"` + `chevron at=4 "Refresh"` | A → confirms B residual |
| 14 | `chart_config.exterior_segment_names=true` on provision stacked bar (secondary reserve-rate table unchanged) | A scrape for N6 legend |
| 02 | `packing_mode` left/explicit `stat-led` (no schema packing density knob beyond existing) | no-op A |
| 11 | keep `chart_hero_dual` + `metric-led` (no type-scale knob) | no-op A |
| 27 | hard-remove any `tile_skin` keys; keep light panels + N5 exterior + `$` stack totals | confirm light pack |

## Checklist scores (fresh)

| Slide | Topic | p02 % | p01 % | Δ pp | Primary read |
|------:|-------|------:|------:|-----:|--------------|
| 00 | Cover | 82.18 | 82.18 | 0.00 | **R3 wontfix — excluded** |
| 02 | Summary Financial | 90.56 | 90.56 | 0.00 | **F4+** still freestanding strip residual (`compare_02.png`) |
| 03 | Total Billed Business | 92.62 | 92.62 | 0.00 | **R1** flat holds |
| 05 | Platinum | **75.90** | 75.90 | 0.00 | **R2** DOM clean elbow+stem+chevron, geometry still ≠ PDF (`compare_05.png`) |
| 11 | New Acquisitions | 85.67 | 85.67 | 0.00 | **R4** hero % scale residual (`compare_11.png`) |
| 14 | Total Provision | **86.07** | 85.31 | **+0.76** | N5-style `segmentNames` now on provision; **N6 furniture** still under-table strip not boxed cells (`compare_14.png`) |
| 19 | pills sibling | 91.86 | 91.86 | 0.00 | F4+ family |
| 27 | Funding and Deposits | 78.60 | 78.60 | 0.00 | **N5 packing** residual (`compare_27.png`) |

## Per open-list ID

| ID | Status this pass | Evidence | A/B |
|----|------------------|----------|-----|
| **R2** | **still-gap / weak** (MAE flat) | HTML: one `chartjs-callout-elbow` `left:0 width:100 top:8.33%` + stem height 33.33% + chevron `at=4` — **no band** on platinum (merge path unnecessary when elbow declared alone). Visual still mid-plot teal capsule + small under-axis Refresh vs PDF L-elbow → spanning blue pill + large bottom navy Refresh chevron (`compare_05.png`). | **B geometry** — pure A exhausted |
| **N5 / F11 packing** | **partial** — wire holds | Funding still light + `segmentNames` items×2 boards; packing density / multi-line exterior column short of PDF (`compare_27.png`) | **B packing** |
| **F4+** | **still-gap / weak** | No packing density A knob; `compare_02.png` unchanged silhouette | **B weak** |
| **N6** | **still-gap / weak** (+ small MAE) | `exterior_segment_names` lands `segmentNames` Write-offs / Reserve Build on provision (`segmentNames` count 6 deck-wide, was 5). Series names paint as exterior stack labels, **not** a right legend column + freestanding boxed reserve-rate cells. Under-chart reserve table still sheet-style. | **B furniture**; A scrape proved wire reuse ≠ N6 chrome |
| **N2 weight** | **mostly resolved** | YOLO chips still paint dual board right card; no A weight lever | polish **B weak** |
| **R1** | **improved / weak residual** | s03 92.62 holds | **B weak** pad |
| **R4** | **still weak** | no font-scale handoff key; `compare_11.png` unchanged | **B weak** |
| **F12+** | **weak residual** | annex white-MAE high; not re-tuned | **B weak** |
| **R3** | **dropped wontfix** | cover flat 82.18 | excluded |

## DOM probes (pass_02 presentation.html)

| Marker | Count | Note |
|--------|------:|------|
| `chartjs-callout-band` | 2 | non-platinum residual only |
| `chartjs-callout-elbow` | 6 | platinum clean single elbow |
| `chartjs-callout-chevron` | 3 | Refresh present |
| `chartjs-callout-elbow-stem` | 2 | stem on vertical elbows |
| `gl-tile-ir` | 15 | platinum IR heads hold |
| `gl-pill-free` | 3 | freestanding pills |
| `chartjs-flat` | 9 | flat stage |
| `segmentNames` | **6** | +1 from provision exterior engage |
| `gl-tile-tall` | 7 | funding light tall family |

## A exhausted?

**Yes for the v5/v6 open checklist.** Remaining divergences are type **(B)** capability/chrome:

- R2 geometry fixed in CSS/layout math, not handoff fields (`from`/`to`/`value`/`at` already used).
- N5/F4+/N6 packing+furniture need renderer chrome, not JSON toggles.
- R4 type scale has no handoff knob.
- N2 weight / R1 pad / F12+ annex are polish residuals.

Stop after this pass for A-loop purposes. One optional freeze pass_03 is **not required** (would be handoff no-op). Proceed to `GAP_ANALYSIS.md` with **2** passes under budget (≤10).

## Type summary

| Class | Items |
|-------|-------|
| **(A) closed this pass** | R2 elbow-only declare confirmed clean; provision exterior_segment_names engaged (+0.76 pp MAE, no N6 furniture) |
| **(B) remain** | R2 geometry, N5 packing, F4+, N6 furniture, R4 scale, R1 residual, F12+, N2 weight polish |
| **Excluded** | R3 seal |
