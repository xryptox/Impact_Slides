# Pass 01 — v8 baseline on post-round-5 renderer

**Date:** 2026-07-29  
**Renderer:** `origin/main` @ `a72e7bb` (includes PR #117 T10, #120 T6/T7/T9, #119 T11, #118 T12/T13).  
**Base handoff:** v7 pass_02 + r5 verification knobs.  
**Render:** `python -m impact_slides.renderer_v2` → 44 slides OK.  
**Evidence:** `geometry.json` (**56/57 pass**, 1 fail), `side_by_side/compare_XX.png`, `screenshots/html_slide_XX.png`.  
**Method:** geometry assertions (±4px) + side-by-side visual reading. **No MAE %.**

## Worktree note

GNHF worktree initially sat on `5e1320f` (launcher retarget) **before** PR #118 merge. Fast-forwarded to `origin/main` (`a72e7bb`) so T12/T13 are actually present before measuring. Without that FF, T12/T13 falsely FAIL.

## Handoff deltas vs v7 pass_02

| Slide | Change | Intent |
|------:|--------|--------|
| **05** | chevron `at: 2` (PDF Q3'25) | T7 anchor correct vs v7's at:4 |
| **03, 09, 10, 18** | annotation `x`/`y` declared as plot-area px offsets | T9 verify |
| **13, 16, 20, 26** | strip explicit `series_colors` | T10 default palette path |
| **16** | `label` on both panes (`Net Card Fees ($B)`, `YoY Growth %`) | T11 pane headings |
| **27 / 14** | keep exterior_segment_names + T2 knobs; no side_legend | N5 clean single source |

## Geometry summary

| Bucket | Result |
|--------|--------|
| Total assertions | **57** |
| Passed | **56** |
| Failed | **1** — s05 tile0 Chart.js legend still `display:true` with nDS=1 (multi_panel path does not auto-suppress; dual_chart T11 does) |

### Round-5 verification (fresh numbers)

| ID | Status | Evidence |
|----|--------|----------|
| **T10 palette** | **resolved** | All T10 slides paint hex navy/blue; zero `var(--` in chart scripts. s16 default → `#00175a`/`#006fcf`. Correct colour **does** change reading vs v7 black charts — packing/furniture gaps remain, but colour is no longer confounding them. |
| **T6 axis-break** | **resolved** | s05 right tile: break box `top=531.39` vs `chartArea.bottom=531.4` (Δ −0.01px); size 10×14 hatch, **not** a mid-plot line. |
| **T7 chevron split** | **resolved** (anchor fixed) | tip+pill separate, no fused node; tip centre = bar2 centre **369.30** (Δ 0); tip top 561 ≥ area.bottom 531.4; pill stacked under tip (Δ +2px). |
| **T9 annotations** | **resolved** | s03/s09/s10/s18 all land at `chartArea + (x,y)` within 0.01px. |
| **T11 pane headings** | **resolved** on dual_chart | s16: two `.gl-tile-label` headings; both single-series legends `display:false`. |
| **T12 insets** | **resolved** | s19/s23 inset↔cell overlap **0**; deck-wide sweep **dades0**. Layout is flex row-reverse gutter. |
| **T13 annex banding** | **resolved** | s30/s31/s32 group headers both `rgb(0,23,90)`; white-on-navy heads remain. |

### T1 callout geometry (still holds)

| Assertion | Measured | Expected | Δ | Pass |
|-----------|---------:|---------:|--:|:----:|
| elbow.left vs bar0 centre | 97.53 | 97.54 | −0.01 | ✓ |
| elbow.width bar0→bar4 | 543.52 | 543.52 | 0.00 | ✓ |
| stem.left vs bar0 | 97.53 | 97.54 | −0.01 | ✓ |

### Open structural residuals (geometry + SBS)

| ID | Type | Finding |
|----|------|---------|
| **R2 chrome** | **B** (geometry A-done; silhouette accepted L3) | SBS `compare_05.png`: capsule is full-width blue bar with right arrowhead — PDF is short mid-span pill with **left L-bracket**. Chevron under Q3'25 is correct but small vs PDF. IR tile **top_total + dual legend chrome** vs PDF title-only boards. Multi_panel single-series legend suppression not automatic (fail #1) — **partial A** via `show_legend:false`. |
| **R2 L-bracket** | **closed accepted r5 L3** | Do not re-open. |
| **F4+** | **B weak** | s02: 3 shells, widths ~434px, cellH ~135px, board/slide frac **0.673**. SBS denser PDF labels/borders; Boardroom spacing still airy. No packing A knobs left. |
| **N6** | **B weak** | `compare_14.png`: reserve-rate is under-chart dense row, not freestanding label + five boxed % cells. Exterior names paint but wrap mid-token ("Build/(Reli"). Values/negchips OK. |
| **N5/F11** | **partial / B weak** | `compare_27.png`: sole segmentNames column (padRight=117, fontSize=20, offset=27); side_legend=0. Names readable but multi-line packing + FDIC callout placement + bar aspect still short of PDF card density. |
| **R4** | **B weak** | `compare_11.png`: exterior names land; hero **66%/73%** are ~boardroom scale, not PDF ~110px digits with caption beside. |
| **T11 multi_panel** | **partial A** | dual_chart suppresses single-series legend; multi_panel tile0 on s05 still shows legend swatch restating heading. |
| **s16 CAGR furniture** | **mixed** | headings OK / colours OK; PDF CAGR arrow + per-bar $ labels + separate dual cards missing — mostly **B** (+ handoff missing CAGR callout **A** try next). |

## Side-by-side visual readings (focus slides)

- **05 Platinum:** Geometry perfect; chrome recipe wrong (L-elbow, IR head band, in-bar % labels present vs PDF clean bars, right tile axis footprint). Colour now correct navy — v7 black-chart reads invalidated.
- **16 Net Card Fees:** Pane headings + default palette navy/blue. Missing CAGR spanning arrow, dual rounded cards as separate tile skins, large $ tops.
- **19 Expense:** Inset gutter works (no overlap). Inset is solid navy pill; PDF is outlined boxed "Q1'26 VCE % of Revenue / 44.7%". Cosmetic **B** skin, not collision.
- **02 Summary:** Structure matches; weights/borders/padding lighter than PDF.
- **11 Acquisitions:** Chart+names good; hero type under-scaled.
- **14 Provision:** Series correct with negchips; reserve-rate furniture wrong recipe.
- **27 Funding:** Clean single legend source; density/wrap residual.

## A vs B after pass_01

| Class | Items |
|-------|-------|
| **(A) to try next** | s05 `show_legend:false` on single-series tile; s16 CAGR elbow/callout + point $ labels; s14/s27 micro T2 wrap_chars; s11 hero no pure type knob expected |
| **(B) confirmed** | R2 IR board chrome recipe; F4+ packing finish; N6 boxed reserve-rate cells; N5 multi_panel density; R4 hero type scale |
| **Resolved / excluded** | T6 T7 T9 T10 T11(dual) T12 T13; R1/F12+/N2 D11; R2 L3 silhouette; R3 wontfix |

## Artifacts

- `handoff.json`, `output/presentation.html`
- `geometry.json` (57 assertions)
- `screenshots/html_slide_XX.png`, `side_by_side/compare_XX.png` (focus 00,02,03,05,09–11,14,16,18,19,23,27,30–32)
- Probes: `simulation/amex_q1_2026/probes/{geometry_probe,screenshot_sbs}.py`
