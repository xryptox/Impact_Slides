# Pass 01 notes — current renderer_v2 (post F-feature work)

**Goal:** AFTER baseline. Exercise every new IR layout / chart_config field against the Amex Q1'26 PDF and re-score v1 gaps F1–F15 with fresh evidence.  
**Chart path:** Chart.js default (`charts` feature on).  
**Chrome:** `presentation.chrome_level = "minimal"`.  
**Theme:** Amex token map via `presentation.theme` (F13).  
**Mean MAE similarity:** **89.16%** (v1 pass_03 was 86.19%) — still white-biased; judge from `screenshots/compare_XX.png`.  
**Slides rendered:** 44 (1:1 with PDF after keeping slide 1 as `title_or_opening` to avoid load.py cover injection).

## Method

1. Rasterized PDF → `extracted/pdf_page_*.png` (PyMuPDF dpi=200).
2. Reused vision transcription `extracted/slides.json` from v1 (content already verified).
3. Built handoff from v1 pass_03 content, remapped key slides onto new layouts (`_build_handoff.py`).
4. `python -m impact_slides.renderer_v2 --handoff … --self-contained`.
5. Playwright 1920×1080 per `.slide` + side-by-side PDF diffs (`_screenshot_and_diff.py`).

## Top structural outcomes (PDF vs HTML)

| Slide | PDF topic | MAE % | What matched | What diverged | Type |
|------:|-----------|------:|--------------|---------------|------|
| 00 | Cover | 89.5 | Two-tone navy/blue scaffold | Amex Centurion seal & ribbon lockup absent; title_or_opening cannot host `brand_mark_svg` (load forces layout) | **B** (load+cover recipe interaction); residual **A** copy placement only |
| 01 | Business Highlights | 93.1 | Full-width single column + `**bold**` → `<strong>` | Smaller IR typography; row hairlines; not large centered Amex bullets | **B** weak styling; structure **resolved** vs v1 freeform-only |
| 02 | Summary Financials | 91.4 | Pill column headers `gl-pill-col` | Not freestanding rounded statement columns; exterior labels inside grid card | **partial B / A** density |
| 03 | Total Billed Business | 90.4 | Dashed Reported series, Leap Year annotation box, ~0–15 domain, on-point %, G&S/T&E under-table | Domain visually starts mid-scale in shot (charts pad); Boardroom card chrome; thinner series styling vs IR house | **partial** — core F1/F2 cues **present** on Chart.js (was B in v1) |
| 05 | US Cons. Platinum | 74.0 (worst) | multi_panel hosts 2 charts + metric | PDF is dual **carded bar** board with refresh callout arrow + horizontal retention bars 90–100%; HTML lines + sparse empty card | **B** recipe fidelity; **A** chart type choice (bars vs lines) |
| 11 | New Acquisitions | 83.2 | `chart_hero_dual` left stack + right 66%/73% heroes | Hero type scale smaller; labels ordered Fee-Paying first then Millennial (PDF reverse semantics around those %); total labels on bars weaker | **partial resolve F5**; residual **A** label swap |
| 14 | Total Provision | 84.3 | Positive stack composition + KPI chips | Reserve **release below axis** still gone — Chart.js data shows `73`/`24` **absolute** not −73/−24; tops merge incorrectly | **B** still (F3) |
| 19 | Expense Performance | 91.7 | Pill headers + floating **44.7% VCE** inset | Not freestanding columns; inset overlays top-right of full-width grid | **partial resolve F4/F9** |
| 20 | Capital | 87.8 | multi_panel tiles | Not IR four-quadrant capital pack; still sparse | **partial F11** |
| 21 | 2026 Guidance | 91.8 | Navy bar statement card + two label→value rows + footnote | Full-width thin card vs centered IR guidance plaque | **partial resolve F8** |
| 22 | Appendix divider | **87.3** (v1 ~23.6) | Full-bleed two-tone + inlined mark | Mark is generic star SVG not Centurion seal; diagonal split not horizontal band | **major resolve F6 path**; residual cosmetic **A/B** mark art |
| 30 | Annex billings | 91.7 | `annex_table` micro density + header_groups | Still not PDF multi-header precision | **partial F12** |
| 43 | Trailing brand | **85.1** (v1 ~20.1) | brand_divider two-tone | Same generic mark / composition vs blankish PDF brand plate | **major resolve F6 path** |

## F1–F15 quick re-test (this pass only)

| ID | v1 status | v2 pass_01 status | Evidence |
|----|-----------|-------------------|----------|
| F1 IR line house style | B (Chart.js ignored config) | **partial / largely resolved on Chart.js** | `compare_03.png`; config has min0 max15 stepSize5, dashed Reported, datalabels |
| F2 annotation layer | missing | **partial / resolved** | Leap Year box visible HTML (`chartjs-annotation`, `compare_03.png`) |
| F3 negative stacks | missing | **still gap** | handoff `−73/−24` → Chart data `[73…24]` abs; `compare_14.png` |
| F4 pill columns | missing | **partial** | `gl-pill` on `compare_02/19.png`; not IR freestanding columns |
| F5 chart\|hero dual | missing | **resolved (structure)** | `chart_hero_dual` `compare_11.png` |
| F6 brand cover/divider | missing | **partial**: dividers **resolved-ish**; **cover seal still gap** via forced `title_or_opening` | `compare_22/43.png` vs `compare_00.png` |
| F7 IR bullets + bold | geometry weak / bold missing | **resolved (capability)** | `<strong>` count 12; `compare_01.png` |
| F8 guidance card | weak freeform | **resolved (capability)** | `gl-guid-bar` `compare_21.png` |
| F9 floating table inset | no-op on data_table | **resolved on pill_comparison** | VCE 44.7% inset `compare_19.png` |
| F10 broken y-axis | missing | **partial** | retention Chart.js ticks min=90 max=100 + `chartjs-axis-break`; PDF still bar board not matched (`compare_05.png`) |
| F11 multi-panel host | missing | **partial** | `gl-multi-panel` on platinum/capital; recipe chrome weak (`compare_05/20.png`) |
| F12 dense annex | weak | **partial** | `annex_table` layouts in handoff; MAE ~91% annex slides |
| F13 handoff theme | unwired CLI | **resolved** | `--navy` / theme tokens in HTML; theme in presentation block |
| F14 IR chrome mode | missing | **resolved** | `<body class="gl-chrome-minimal">` |
| F15 chart_config parity | path-split | **largely resolved on Chart.js path** | annotation + axis + dash + labels paint without suppressing charts |

## Residual pure-(A) candidates for pass_02

1. **Acquisitions hero order / labels** (slide 11): swap/reorder key_stats so Millennial/Gen-Z pairs with PDF’s large 66% block semantics if desired; shorten hero labels.
2. **Platinum mapping** (slide 05): retarget multi_panel tile chart_types to **grouped_bar** (spend) + horizontal-ish retention representation; add Refresh callout as metric/annotation text (full arrow chrome may still be B).
3. **Billed business scale padding** (slide 03): try alternate `y_axis_min/max` / remove conflicting secondary visual crowding (may still be painter default = B).
4. **Guidance card content** complete (already good values); boast centering via subtitle/title only (A weak).
5. **Cover**: cannot switch to `brand_cover` without load.py inserting a 45th slide and breaking PDF index alignment — treat seal-on-cover as **B** unless future renderer stops forcing title remap.

## Confirmed capability gaps remaining (B) after pass_01

1. **F3 below-axis negative stacked segments** — absolutes wipe sign (`compare_14.png`).
2. **Cover brand_mark via forced title_or_opening** — `brand_cover` not usable as slide 1 without injection (`load.normalize_handoff`) (`compare_00.png`).
3. **IR freestanding pill column geometry** — headers exist; full statement-column IR look still short (`compare_02.png`).
4. **Specialized dual-card Platinum board** (refresh arrow band, anniversary horizontal bars) — multi_panel + broken axis insufficient fidelity (`compare_05.png`).
5. **Brand-mark art fidelity** — generic SVG star ≠ Centurion seal (expected: handoff can supply better SVG = residual **A** if we author better mark; true seal asset pack still product choice).

## Stop-gate note

Not stopping the loop yet — pass_01 proved many v1 B gaps are now expressible. Next passes should burn residual **A** items (platinum chart types, acquisitions label order, stronger brand_mark_svg) before declaring remaining-only-B.

## Artifacts

- `handoff.json` · `output/presentation.html` · `screenshots/html_slide_*.png` · `screenshots/compare_*.png` · `diff.png` · `diff_scores.json` · `_build_handoff.py` · `_screenshot_and_diff.py`
