# Pass 01 — frozen v5-final handoff on CURRENT renderer (post-PR #114)

**Date:** 2026-07-26  
**Handoff:** v5 `pass_03/handoff.json` frozen (Chart.js path, N5 engaged, funding light cards, platinum IR dual boards, R2 band+elbow+chevron declare on slide 05).  
**Render:** `python -m impact_slides.renderer_v2 --self-contained` → 44 slides OK.  
**Mean MAE similarity:** **89.29%** (SSIM-approx **89.48%**).  
**vs v5 pass_03 final (89.38%):** **−0.09 pp** mean (noise / white-canvas; structural story is per-slide).  
**vs v5 pass_01 frozen (89.36%):** −0.07 pp mean.

## Purpose

Measure the **current** renderer (worktree includes PR #114 board vertical fill, R2 band+elbow canonical merge, N2 14px chips, F4+ 17px navy pill cells) against the same recipe that stopped v5. Every v5 open-list ID is re-tested with fresh screenshots — status is not inherited.

## Artifacts

- `handoff.json` — frozen v5 stop recipe  
- `output/presentation.html`  
- `screenshots/html_slide_XX.png`, `compare_XX.png`  
- `diff_scores.json`, `diff.png`  
- `_screenshot_and_diff.py` (Playwright 1920×1080 + MAE)

PDF rasters: `extracted/pdf_page_*.png` (fresh PyMuPDF 200 DPI). Vision deck: `extracted/slides.json` (carried from v5 archive, shape verified 44 slides).

## Checklist scores (fresh)

| Slide | Topic | v6 p01 % | v5 p03 % | Δ pp | Primary read |
|------:|-------|---------:|---------:|-----:|--------------|
| 00 | Cover | 82.18 | 82.18 | 0.00 | **R3 wontfix — excluded** (generic seal_lockup) |
| 02 | Summary Financial (pills) | 90.56 | 90.82 | −0.26 | **F4+** still Boardroom freestanding strip vs PDF exterior labels + tight navy columns (`compare_02.png`) |
| 03 | Total Billed Business | 92.62 | 92.74 | −0.12 | **R1** flat path holds; residual Boardroom pad |
| 05 | Platinum | **75.90** | 73.90 | **+2.00** | **R2** geometry still wrong; boards taller / IR heads +N2 chips paint; chevron still pill-at-axis not bottom arrow (`compare_05.png`) |
| 11 | New Acquisitions | **85.67** | 83.00 | **+2.67** | Boards taller (**#114 gl-main fill**); **R4** hero % still under-scale vs PDF dual stack (`compare_11.png`) |
| 14 | Total Provision | 85.31 | 86.75 | −1.44 | N3/N4 dual labels + just under-table reserve rates; **N6** furniture (boxed cells + exterior series legend) still short (`compare_14.png`) |
| 19 | table/pills sibling | 91.86 | 92.04 | −0.18 | F4+ family stable |
| 27 | Funding and Deposits | 78.60 | 78.81 | −0.21 | **N5** exterior names + $ tops present; packing / multi-line exterior column still weak (`compare_27.png`) |

**Worst structural (excl. cover R3):** 05 (75.90), 27 (78.60), 12 (83.35), 43 (85.10), 17 (85.25), 14 (85.31), 11 (85.67).

## Per open-list ID (independent re-test)

| ID | Status this pass | Evidence | A or B |
|----|------------------|----------|--------|
| **R2** | **still-gap / weak** (MAE +2.00 on s05 but recipe still ≠ PDF) | DOM: `chartjs-callout-elbow` spanning left=0 width=100 top=8.33% + stem + `chartjs-callout-chevron` at Q1'26. Visual `compare_05.png`: floating mid-plot teal capsule over bar tops + small under-axis Refresh pill. PDF: left L-elbow into spanning blue pill + **large bottom-center navy Refresh chevron**. Band+elbow double-declare in handoff is absorbed (no double smear) — merge works; **geometry recipe still wrong**. | **B** geometry (handoff already declares elbow+chevron; no extra A type) |
| **N5 / F11 packing** | **partial** — wire holds, packing weak | `segmentNames` in HTML (5); funding light tall cards; exterior colored names right of stacks on `compare_27.png` but denser / less multi-line than PDF; FDIC callout not in right-card exterior column | **B residual packing**; wire was A-closed in v5 |
| **F4+** | **still-gap / weak** | `gl-pill-free` present; `compare_02.png` three navy-header columns exist but row labels sit outside narrow centered pills vs PDF exterior metric column + denser packing; cells look 17px navy (PR #114 typography) but packing residual remains | **B weak** (no new pack knob) |
| **N6** | **still-gap / weak** | `compare_14.png`: dual in-bar $ + tops + paren chips family OK; reserve-rate is under-table strip not freestanding bordered cells; series legend not exterior right column | **B furniture** |
| **N2 weight** | **mostly resolved** (+ soft polish) | Right card year chips **2025/2026 inside bars** with series colors; 14px path engaged. Slightly lighter/smaller than PDF bold chips | polish **B weak** only |
| **R1** | **improved / weak residual** | `chartjs-flat` count 9; s03 92.62% holds v5 lift | residual pad **B weak** |
| **R4** | **partial improve / still weak** | s11 +2.67 pp; taller boards fill stage; giant 66%/73% still smaller than PDF hero stack and right column packing wrong (stacked cards vs dual % column) | **B weak** type scale |
| **F12+** | **weak residual** (not re-tuned) | annex white-MAE high ~91–95%; side-by-side header precision residual carries | **B weak** |
| **R3** | **dropped wontfix** | cover 82.18 flat; generic seal — excluded from gap counts | — |

## DOM probes (presentation.html)

| Marker | Count | Note |
|--------|------:|------|
| `chartjs-callout-band` | 2 | residual bands elsewhere; platinum elbow-absorbs co-declared band |
| `elbow` | 6 | elbow overlays present |
| `chevron` | 3 | Refresh chips present |
| `gl-tile-ir` | 15 | IR navy heads |
| `gl-pill-free` | 3 | freestanding pills |
| `chartjs-flat` | 9 | flat stage |
| `segmentNames` | 5 | N5 shell plugin |

## Matched well

- 1:1 44-page map, Boardroom tokens, Chart.js self-contained.  
- F10+ 90–100 anniversary domain on retention.  
- N2 in-bar years paint.  
- N3/N4 dual label + negchip family on provision.  
- N5 exterior names wire on funding.  
- F11 IR dual-card heads on platinum; light cards on funding.  
- Board vertical fill visibly taller dual panels on 05/11 vs older short tiles (qualitative; MAE mixed).

## Divergences → next pass candidates (A only)

1. **R2 handoff micro:** declare **elbow_arrow alone** (drop explicit band) + try chevron `at` / text-only variants — expect little geometry change (B), confirm absorption path is clean.  
2. **Provision N6 A-scrapes:** secondary_visual / side_legend placement tweaks only.  
3. **Funding packing:** already light+N5; avoiding IR re-enable.  
4. Stop when A levers exhausted (likely ≤3 passes as v5).

## Type summary

| Class | Items |
|-------|-------|
| **(A) still worth one try** | R2 declare elbow-only cleanup; possible provision legend placement; hero layout_type/packing if schema allows |
| **(B) capability / chrome** | R2 geometry, N5 packing density, F4+ freestanding recipe, N6 furniture, R4 type scale, R1 flat residual, F12+ headers, N2 weight polish |
| **Excluded** | R3 seal |

**Mean alone** is white-biased; use `compare_XX.png` for structural calls. Pass_01 establishes AFTER-#114 baseline — not a stop.
