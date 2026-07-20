# Pass 02 notes — residual type-(A) handoff tuning

**Goal:** Close pass_01 residual **A** candidates only (no renderer edits).  
**Base:** `passes/pass_01/handoff.json` remapped slides 03/05/11/18/27 + brand marks on 00/22/43.  
**Mean MAE similarity:** **89.25%** (pass_01 **89.16%**, Δ +0.09 pp). Still white-biased; judge from `screenshots/compare_XX.png`.  
**Slides:** 44 (1:1 PDF alignment preserved).

## What changed in handoff

| Slide | Change | Intent |
|------:|--------|--------|
| 05 | multi_panel tiles → **grouped_bar** spend + **grouped_bar** retention (ymin 90 + y_axis_break); drop empty metric tile; Refresh as annotation/so_what | Fix chart-type A gap from pass_01 lines |
| 11 | key_stats reorder + total point_labels flags | Match PDF hero column order |
| 18 | **combo_chart → line_chart** dual YoY (FX solid / Reported dashed) + `$B` secondary under-table + Leap Year annotation | Match PDF composition (was bar-primary combo) |
| 27 | **metric_dashboard → multi_panel** dual stacked 100% bars (Funding Mix + Deposit Programs) + deduct counters | Match dual board structure |
| 03 | annotation xy polish only | minor |
| 00/22/43 | denser geometric `brand_mark_svg` | still not Centurion seal |

## Score deltas (select)

| Slide | Topic | p01 % | p02 % | Δ | Read |
|------:|-------|------:|------:|--:|------|
| 18 | Total Revenues Net of IE | 80.45 | **89.30** | **+8.85** | Large A win — dual lines + under-table now present |
| 05 | Platinum | 74.03 | 72.80 | −1.23 | Chart types fixed; geometry still fails MAE (B-dominant) |
| 27 | Funding | 81.83 | 78.36 | −3.47 | Structure right; sparse multi_panel vs dense PDF cards hurts MAE |
| 11 | Acquisitions | 83.15 | 83.15 | 0 | Order change visible in heroes but labels still mismatched to PDF pairing |
| 03 | Billed Business | 90.42 | 90.42 | 0 | Already strong; polish no MAE move |
| 14 | Provision | 84.31 | 84.31 | 0 | F3 still B (Chart.js data still abs: `73…24`) |
| Mean | — | 89.16 | 89.25 | +0.09 | — |

## Per-target visual judgment

### Slide 18 — Total Revenues (**A largely closed**)
- **Matched:** dual YoY lines; dashed Reported vs solid FX; Leap Year box; `$B` under-band values (`$17.0`…`$18.9`); 0–15-ish IR frame (`compare_18.png`).
- **Residual B:** PDF paints flat stage with free-floating annotation + full-width navy header band above `$B` row; HTML keeps chart card, complex stacked under-table in card footer, slightly compressed Y zero origin in shot.
- **Classification:** primary fix was **A** (wrong layout choice in p01). Remaining styling = **weak B** / cosmetic.

### Slide 05 — Platinum (**A partial; B dominant**)
- **Matched vs p01:** spend is **bars** not lines; two tile titles; dual-board multi_panel host retained (`compare_05.png`).
- **Diverged:**
  1. Retention still **vertical grouped bars** from 0 — `y_axis_break` / ymin·90 **did not produce** a 90–100 IR horizontal anniversary board (Chart.js config in HTML shows B labels `2025`/`2026` from matrix headers; visual y still 0→100 with tiny mid bars). Treat **horizontal bar + broken-axis fidelity on multi_panel tiles as B / weak**.
  2. No navy dual **card shells**, no **Refresh** chevron under Q2/Q3, no elbow **+~6 pp** callout arrow — annotation text only.
  3. Lots of whitespace lower half (multi_panel packing).
- **MAE drop** despite correct chart families confirms pixel metric rewards dense filled PDF cards more than sparse-but-righter charts.

### Slide 11 — Acquisitions (**A still open on labels**)
- Heroes show **73% then 66%** top→bottom (`compare_11.png`).
- Vision/PDF pairing is actually:
  - **TOP 66%** = Millennial / Gen-Z  
  - **BOTTOM 73%** = Fee-Paying Products*
- Pass_01 notes inverted that pairing; pass_02 wrongly put 73% Millennial on top. Correct handoff A fix for pass_03:  
  `[{66%, Millennial/Gen-Z}, {73%, Fee-Paying}]` with short labels. MAE flat because structure already chart_hero_dual.

### Slide 27 — Funding (**A layout remap partial / B chrome**)
- Handoff now carries correct Universe(s): Funding Mix 72/21/6/1 and Deposit Programs ~82/10/6/2 (`chartjs-config` verified).
- Screenshot shows only the **dominant** deposit-like segment painted large; upper stack segments effectively invisible (tiny %) + multi_panel four-tile grid dilutes the PDF’s two tall equal cards.
- PDF extras absent: `$210/$219` and `$151/$157` tops, side legends, FDIC callout badge on deposit card, paired card frame.
- **A remaining:** try 2-tile only multi_panel; put $ totals in tile labels; drop metric tiles that steal space.  
- **B remaining:** stacked-bar IR “tall 100% card with external side legend + total callout” recipe.

### Brand marks 22/43/00
- Denser SVG still generic star-in-circle, not Centurion+ribbon (`compare_22/43/00`). Cover still `title_or_opening` (load forces). Residual B on cover path; A exhausted for seal fidelity without an asset pack / brand_cover on slide 1.

## F1–F15 re-score movements this pass

| ID | p01 | p02 | Notes |
|----|-----|-----|-------|
| F1 line house | partial | partial (reinforced on s18) | s18 now line path not combo |
| F2 annotation | partial | **stronger** on s18 + curiosity s05 | Leap Year paints |
| F3 negative stack | **still B** | **still B** | HTML Chart.js reserve series still absolute |
| F5 hero dual | resolved struct | resolved; **label pairing A remains** | |
| F10 broken axis | partial | **still weak on multi_panel grouped bars** | ymin/break not bottoming retention @90 in paint |
| F11 multi_panel | partial | **exercised harder** (plat/funding) | host works; IR card recipe weak |
| others | as p01 | as p01 | no regression of brand_divider / pill / guidance / chrome |

## Residual pure-(A) for pass_03 (if any)

1. **Acquisitions heroes (s11):** correct value↔label pairs and PDF order (66% Millennial top, 73% Fee bottom); shorter hero labels.
2. **Funding (s27):** 2-tile multi_panel only (drop metric tiles); encode `$210/$219` and `$151/$157` into tile labels / key_stats carefully so stage density rises without stealing chart height.
3. Optional: Platinum tile labels/subtitles echo PDF card titles exactly; keep so_what short (likely cosmetic).

## Confirmed B (do not expect handoff to fix)

1. **F3 signed stack → Chart.js absolutes** (`compare_14.png`, data `[73…24]`).
2. **Cover brand_cover blocked** by `load.normalize_handoff` title force (`compare_00.png`).
3. **Horizontal bar / anniversary retention board + Refresh arrow chrome** (`compare_05.png`).
4. **y_axis_break impact on multi_panel Chart.js bars** appears weak vs PDF 90–100 window (`compare_05.png`).
5. **IR dense funding 100%-stack cards** with side legends + top $ callouts (`compare_27.png`).
6. **Freestanding pill columns / Centurion seal art** (unchanged).

## Artifacts

- `handoff.json` · `_build_handoff.py` · `_screenshot_and_diff.py`
- `output/presentation.html` · `screenshots/html_slide_*.png` · `screenshots/compare_*.png`
- `diff.png` · `diff_scores.json`

## Decision

Continue to **pass_03** for the remaining short A list (acquisitions pairing + funding 2-tile density). If those map out and deltas are cosmetic, stop early and write `GAP_ANALYSIS.md`.
