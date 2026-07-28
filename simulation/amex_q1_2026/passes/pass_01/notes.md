# Pass 01 — v7 first measure (post T1 #115 + T2 #116)

**Date:** 2026-04-26  
**Handoff:** frozen v6 pass_02 recipe + **T2 knobs declared** on slides 14 & 27  
**Render:** `python -m impact_slides.renderer_v2 --self-contained` → 44 slides OK  
**Mean MAE similarity:** **89.33%** (SSIM-approx **89.52%**)  
**vs v6 pass_02 final (89.31%):** **+0.02 pp** mean (noise)  
**vs v6 pass_01 (89.29%):** **+0.04 pp**

## Purpose

Fresh AFTER snapshot on the **current** renderer (T1 calloutGeometry + T2 exterior-name knobs landed on main). Verify whether the two round-4 fixes hold under a handoff that exercises them, and re-baseline the residual open list (F4+, N6, R4; R1/F12+/N2 accepted; R3 excluded).

## Handoff recipe

| Source | Change |
|--------|--------|
| v6 `pass_02/handoff.json` | base (elbow-only R2, provision exterior names, funding light) |
| slides **27** both tiles | declare T2: `segment_name_font_size=20`, `line_height=22`, `wrap_chars=11`, `max_lines=3`, `offset=27`, `gutter=117` |
| slide **14** | same T2 knobs (collateral A scrape) |
| slide **05** | leave elbow_arrow `from=0..to=4 value=11` + chevron `at=4 "Refresh"` — T1 is runtime geometry, no new JSON keys |

## Checklist scores (fresh vs v6 stop)

| Slide | Topic | p01 % | v6 p02 % | Δ pp | Primary read |
|------:|-------|------:|---------:|-----:|--------------|
| 00 | Cover | 82.18 | 82.18 | 0.00 | **R3 wontfix — excluded** |
| 02 | Summary Financial | 90.56 | 90.56 | 0.00 | **F4+** freestanding packing residual |
| 03 | Total Billed Business | 92.62 | 92.62 | 0.00 | **R1 accepted divergence** (D11) |
| 05 | Platinum | **76.77** | 75.90 | **+0.87** | **R2/T1** geometry engaged; chrome residual remains |
| 11 | New Acquisitions | 85.67 | 85.67 | 0.00 | **R4** hero % type scale residual |
| 14 | Total Provision | 86.07 | 86.07 | 0.00 | **N6** furniture residual (T2 knobs do not deliver boxed cells) |
| 19 | pills sibling | 91.86 | 91.86 | 0.00 | F4+ family |
| 27 | Funding and Deposits | **78.65** | 78.60 | **+0.05** | **N5/F11/T2** knobs live; packing MAE near-flat |

## DOM / geometry probes

### R2 / T1 (slide 05) — `slide05_geometry.json`

After slide activation + Chart.js layout:

| Node | left_px | top_px | w×h | style (post-plugin) |
|------|--------:|-------:|-----|---------------------|
| elbow capsule `+ ~6 percentage points` | 98 | 60 | 544×30 | `left:97.54px; top:60.45px; width:543.52px` (**px, not %**) |
| stem | 98 | 90 | 2×151 | `height:150.8px` from capsule bottom toward from-bar |
| chevron `Refresh` | 624 | 531 | 34×22 | `top:531.4px` ≈ wrap bottom (wrap_h=562) |

wrap ≈ 709×562. DOM counts deck-wide at load (pre-activation sparse): elbow=1, stem=1, chevron=1, band=0. `calloutGeometry` plugin present in shell (1 match).

**Structural read vs PDF (`compare_05.png`, `html_slide_05.png`):**

- **Geometry fix HOLDS:** capsule spans ~bar-centre-to-bar-centre in chartArea pixels; Y sits high on plot (~value 11 domain); stem drops from capsule left to from-bar top; chevron sits under category tick near chartArea.bottom. No more full-wrap `%` mid-plot float from v6.
- **Recipe / chrome still diverges from PDF (B residual):**
  1. PDF Refresh = **large centered navy chevron under entire category axis**; HTML = **small at=4 tip under Q1'26 only**.
  2. PDF L-elbow joins mid/left of Q1'25 **into** pill; HTML stem is a vertical hairline from capsule to bar top (correct T1 acceptance geometry, still not PDF silhouette).
  3. Board house chrome: PDF light-gray boards titles-only; HTML IR metric chips in head (`+ ~6 pp` / `94–97%`) + gridlines + dual legends.
  4. Right card: anniversary comparison geometry OK family; residual board packing not R2.

**MAE lift +0.87 pp is real but small** — exact geometry moved pixels; white-canvas + house-chrome dominate remaining 23+ pp gap. T1 is **verification=partial-resolved on geometry acceptance criteria**, **still-gap on PDF recipe chrome** (chevron scale/place recipe, not position math).

### N5 / F11 / T2 (slide 27) — HTML segmentNames configs

```
segmentNames: {fontSize:20, lineHeight:22, wrapChars:11, maxLines:3, offset:27, items:[...]}
```

on provision + both funding boards (3 configs with fontSize 20). Knobs **serialize and paint**.

**Structural read (`compare_27.png`):**

- Exterior names larger/wrapped vs v6 defaults — visual density improved on Deposit Programs labels.
- MAE **+0.05 pp only** (78.65 vs 78.60) — white-biased noise band; packing silhouette still dominated by:
  - residual Chart.js **in-card legend** dots (PDF has pure exterior name column, no legend)
  - light multi_panel card packing vs PDF rounded dense boards
  - stack total placement ($210B title-cluster vs on-bar)
- **Verdict:** T2 knobs **work as declared** (not a false landing); residual is still **exists-but-weak packing / multi_panel skin**, not missing wire.

## Per open-list ID (pass_01)

| ID | Status this pass | Evidence | A/B |
|----|------------------|----------|-----|
| **R2** | **partial** — T1 geometry holds; PDF chrome residual | `slide05_geometry.json` px placement; `compare_05.png` 76.77% (+0.87) | geometry **resolved by T1**; remaining **B chrome** |
| **N5 / F11 packing** | **partial** — T2 knobs live; packing MAE flat | HTML `fontSize:20…`; `compare_27.png` 78.65% (+0.05) | knobs **A done**; packing **B weak** |
| **F4+** | **still-gap / weak** | `compare_02.png` 90.56 unchanged; freestanding cols paint navy 17px but row-label-out packing ≠ PDF compact strip | **B weak** |
| **N6** | **still-gap / weak** | `compare_14.png` 86.07; under-chart sheet header + segmentNames ≠ freestanding boxed reserve cells + exterior legend | **B furniture** |
| **R4** | **still-gap / weak** | `compare_11.png` 85.67; 66%/73% hero present, dual-card giant type packing short | **B weak** |
| **R1** | **closed: accepted divergence per r4 D11** | s03 92.62 in noise band | excluded from open ranking |
| **F12+** | **closed: accepted divergence per r4 D11** | annex high white MAE | excluded |
| **N2 chip weight** | **closed: accepted divergence per r4 D11** | YOLO 14px chips paint on s05 right | excluded |
| **R3** | **dropped: wontfix per CONTEXT.md** | cover 82.18 | excluded |

## Type summary

| Class | Items |
|-------|-------|
| **(A) exercised this pass** | T2 knob declare on 14/27 (serialized correctly); R2 no new A keys needed |
| **(B) remaining** | R2 chevron/size/IR-board recipe after geometry fix; N5 multi_panel packing; F4+; N6 furniture; R4 type scale |

## Next-pass candidates (pure A only)

1. Slide 27: try suppressing dual legend if handoff has a key (`show_legend: false` / series legend off) — may already be default-false elsewhere; scrape.
2. Slide 05: chevron text/`at` already set — no A path to "large exterior under whole axis" without renderer.
3. Slide 11/02/14: no known A knobs for type scale / pill packing / boxed reserve.

Likely **B-only after one more A-scrape pass** on legend/suppression keys for N5 skin. Stop will remain ≤10.

## Artifacts

- `handoff.json`, `output/presentation.html`
- `screenshots/compare_XX.png`, `html_slide_XX.png`
- `diff_scores.json`, `diff.png`
- `dom_probes.json`, `slide05_geometry.json`
- `_screenshot_and_diff.py`
