# Pass 03 notes — last residual type-(A) handoff tuning

**Goal:** Close the short residual **A** list from pass_02, then stop if only **B** remains.  
**Base:** `passes/pass_02/handoff.json` retuned slides 05 / 11 / 27.  
**Mean MAE similarity:** **89.25%** (pass_02 **89.25%**, Δ 0.00). Still white-biased; judge from `screenshots/compare_XX.png`.  
**Slides:** 44 (1:1 PDF alignment preserved).

## What changed in handoff

| Slide | Change | Intent |
|------:|--------|--------|
| 11 | key_stats → **66% Millennial top**, **73% Fee-Paying bottom**; short labels + clarifying subtitle | Fix inverted PDF pairing (was 73/66 Millennial-first) |
| 27 | multi_panel **2 chart tiles only**; drop metric tiles; put `$210/$219` and `$151/$157` in tile labels; enable point labels | Raise funding board density |
| 05 | PDF-aligned dual tile titles (“Accelerated…Spend…”, “…Retention (anniversary cohorts)”) | Cosmetic A polish |

## Score deltas (select)

| Slide | Topic | p02 % | p03 % | Δ | Read |
|------:|-------|------:|------:|--:|------|
| 11 | Acquisitions | 83.15 | **83.10** | −0.05 | **Content A closed** (66 top / 73 bottom), structure already chart_hero_dual; MAE flat |
| 27 | Funding | 78.36 | **78.37** | +0.01 | 2-tile host better; IR tall cards + floating $ tops + side legends still B → MAE stuck |
| 05 | Platinum | 72.80 | **72.83** | +0.03 | Titles only; geometry/callout recipe still B |
| 14 | Provision | 84.31 | 84.31 | 0 | F3 still B (`Reserve… data: [73…24]` abs in HTML Chart.js) |
| Mean | — | 89.25 | **89.25** | 0.00 | — |

## Visual judgment (targets)

### Slide 11 — Acquisitions (**A closed**)
- HTML heroes now **66% Millennial / Gen-Z** (top) and **73% Fee-Paying** (bottom) — matches PDF pairing (`compare_11.png`).
- Residual **B/weak**: oversized dual-card panel chrome on PDF (soft gray companion card, giant type scale with prose) vs thinner Boardroom hero chips; left stacked bars lack masa totals + exterior series legend; disclosure footer band differs.

### Slide 27 — Funding (**A exhausted; B dominant**)
- 2 side-by-side stacked 100% charts with $ totals in labels (`compare_27.png`).
- Still short of PDF: tall equal gray cards, exterior side legends with blue series names, top `$210/$219` and `$151/$157` freestanding callouts, FDIC badge on deposit card, full segment paint of small % slices (Chart.js tiles compress height / upper segments nearly invisible).

### Slide 05 — Platinum (**B residual**)
- Correct chart families retained (spend bars + retention grouped bars); titles closer.
- Still missing: horizontal anniversary bars 90–100%, navy dual card shells, elbow **+~6 pp** refresh arrow, Refresh chevron under Q2/Q3, y break painting as PDF window (HTML retention still 0→100).

### F3 / cover reaffirmed
- Provision Chart.js config still absolute reserve series (`73…24`) — below-axis geometry absent (`compare_14.png`).
- Cover still `title_or_opening` two-tone without Centurion seal (`compare_00.png`); generic brand_mark on dividers only.

## Residual pure-(A)
**None material.** Remaining misses require renderer recipe/capability work.

## Confirmed B (final for this run)
1. **F3 signed stack → Chart.js absolutes** (`compare_14.png`).
2. **Cover brand_cover blocked / seal recipe** (`compare_00.png` + load title force).
3. **IR freestanding multi-column pill statement geometry** (`compare_02.png` — pill headers exist, exterior row labels + freestanding columns weak).
4. **Horizontal bar + anniversary retention board + Refresh callout chrome** (`compare_05.png`).
5. **y_axis_break / ymin impact weak on multi_panel Chart.js bars** (`compare_05.png`).
6. **IR dense dual 100%-stack funding cards** (side legends + top $ callouts) (`compare_27.png`).
7. **Centurion seal asset / brand plate fidelity** on cover and brand_divider (`compare_00/22/43.png`).

## Decision
**Stop handoff iteration.** Write `simulation/amex_q1_2026/GAP_ANALYSIS.md` with per-pass table, v1 F1–F15 before/after delta, and remaining future-feature list only for still-open/partial gaps.

## Artifacts
- `handoff.json` · `_build_handoff.py` · `_screenshot_and_diff.py`
- `output/presentation.html` · `screenshots/html_slide_*.png` · `screenshots/compare_*.png`
- `diff.png` · `diff_scores.json`
