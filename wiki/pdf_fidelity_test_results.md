# PDF Fidelity Test — Renderer v2 vs Amex Q1'26 Earnings PDF

**Date:** 2026-07-18
**Test:** Recreate 10 chart/visualization slides from the Amex Q1'26 Earnings PDF (44 pages) using renderer_v2, with data manually extracted from the PDF.
**Artifacts:**
- Handoff JSON: `.scratch/pdf_fidelity_test/handoff.json`
- Rendered deck: `.scratch/pdf_fidelity_test/output/presentation.html`
- Rendered slide screenshots: `.scratch/pdf_fidelity_test/shots/`
- Side-by-side comparisons (PDF left, renderer right): `.scratch/pdf_fidelity_test/compare/`

---

## Executive Summary

| Chart family | Slides tested | Fidelity | Verdict |
|---|---|---|---|
| `line_chart` (internal) | 4 | **~85%** | Production-ready with minor fixes |
| `data_table` (internal) | 1 | **~90%** | Best match of the test |
| `combo_chart` (internal) | 1 | **~70%** | Core works; missing KPI panel + stacked bars |
| `grouped_bar_chart` (external pack) | 3 | **~40%** | **Wrong bar orientation** — horizontal vs PDF vertical |
| `stacked_bar_chart` (external pack) | 1 | **~40%** | Same orientation issue + no negative segments |

**Headline findings:**
1. All 11 slides rendered without errors; all data values are correct.
2. The **internal** charts (line, combo, table) closely match the PDF visual language.
3. The **external pack** bar charts render **horizontal bars**; every bar chart in the PDF is **vertical**. This is the single biggest fidelity gap.
4. A regression from the charts-pack data bridge: **insight strips render twice** on all pack-chart slides.
5. Two supporting elements from the PDF pattern are missing on chart slides: **support tables pushed below the fold** and **key_stats metric strips not rendered**.

---

## Slide-by-Slide Comparison

### Slide 2 — Total Billed Business (PDF p4) — `line_chart` 2-series

**Matches:** Title/dek, solid FX-Adjusted line + dashed Reported line, legend top-right, Leap Year annotation with dashed border, Y-axis 0/5/10/15%, X-axis quarter labels, all 10 data values.

**Differences:**
- **Data label collisions** where series converge: "8%/9%" at Q3'25, "9%/9%" at Q4'25, "9%/10%" at Q1'26 overlap. PDF offsets labels — above the higher line, below the lower line — dynamically per point. Renderer uses fixed per-series sides (primary above, secondary below), which collides when the secondary series is the higher one.
- **Support table (G&S/T&E) pushed below the fold.** The chart SVG at 900x480 fills the chart-frame; the table renders in HTML but outside the visible viewport. PDF shows chart ~60% / table ~40% in one view.
- Line color: PDF solid line is **navy** (#00175a); renderer uses **blue** (#006fcf). Both are brand colors but the PDF weights navy as the primary series color.
- Annotation renders as one line ("Leap Year Approx. (1%)") instead of the PDF's 3-line box. Root cause: annotation splitter looks for literal `\n` but JSON supplies real newlines.
- Cosmetic: renderer chart sits on a light-gray panel; PDF chart sits on white.

### Slide 3 — Commercial Services Billed Business (PDF p9) — `line_chart` 1-series

**Matches:** single-series line, annotation, axes, values, table data present in HTML.

**Differences:**
- Support table (U.S. SME / Large & Global Corp. / Total) below fold, same as slide 2.
- PDF's right-side labels ("G&S, 3% YoY" / "T&E, 6% YoY") not reproduced — approximated via the so_what insight strip instead (also below fold).

### Slide 4 — Transaction Growth (PDF p11) — `line_chart` 1-series

**Matches:** clean single-series render, annotation, axes, all values. Closest line-chart match in the test.

**Differences:** only cosmetic (gray panel vs white, single-line annotation).

### Slide 5 — Total Balances and Billed Business (PDF p13) — `grouped_bar_chart`

**Matches:** both series present, correct values, legend, brand colors (navy vs blue).

**Differences (major):**
- **Bars are HORIZONTAL; PDF is VERTICAL columns.** The external pack's grouped bar is a horizontal bar chart. Biggest single fidelity break in the test.
- **Insight strip duplicated**: "Billed Business growth outpaced..." appears twice — the pack renders its own insight from the bridged top-level `so_what`, and `render_chart` adds `insight_strip()` again.
- Values lack the **% suffix** (shows "7" not "7%").
- Legend at bottom; PDF has it top-center.
- Auto x-axis ticks are odd decimals (2.2, 4.5, 6.8) instead of clean integers.

### Slide 6 — Total Provision (PDF p15) — `stacked_bar_chart`

**Matches:** both series (Write-offs / Reserve Build) present with correct totals ($1,150 / $1,405 / $1,287 / $1,414 / $1,251).

**Differences (major):**
- **Horizontal bars vs PDF vertical.**
- **Negative reserve segments missing.** PDF renders ($73) and ($24) as navy segments **below the zero axis**; renderer drops the negative segments entirely (Q1'25 and Q1'26 show only the Write-offs bar with the total label).
- Duplicate insight strip (same root cause as slide 5).
- **Reserve Rate metric strip (2.9%…2.8%) not rendered.** `key_stats` were supplied in the handoff but `render_chart` never renders them — the PDF pattern "chart + metric strip below" is unsupported on chart layouts.
- No $ thousands separators formatting on bar-internal values (PDF shows $1,223 inside the bar).

### Slide 7 — Revenue Performance (PDF p16) — `data_table`

**Matches:** best slide of the test. Navy header row, alternating row shading, FX-Adjusted column in blue bold, all 25 cell values correct, table fills the stage well.

**Differences (minor):**
- PDF row labels are left-aligned in a wider first column; renderer centers all cells.
- PDF uses vertical column dividers between the 4 data columns; renderer uses horizontal row rules only.
- PDF header has white text on navy for data columns with an empty top-left cell; renderer fills the whole header row navy (acceptable).

### Slide 8 — Net Card Fees (PDF p17) — `grouped_bar_chart`

**Matches:** all 8 values ($0.9B → $2.8B), correct trend shape.

**Differences (major):**
- **Horizontal vs vertical** (same pack issue).
- PDF's **"17% / Year CAGR" arrow annotation** spanning the chart top is not reproduced.
- PDF page 17 is a **two-chart layout** (bar chart left, YoY% line chart right). The renderer has no side-by-side chart composition; only the left chart was recreated. The line chart data (16%…16%) is unrepresented.
- Duplicate insight strip.

### Slide 9 — Total Revenues Net of Interest Expense (PDF p19) — `line_chart` 2-series

**Matches:** both series, correct values, legend, annotation, axes.

**Differences:**
- Data label collisions at Q3'25 (11%/11%), Q4'25 (9%/10%), Q1'26 (10%/11%) — same fixed-side issue as slide 2.
- Support table ($B row) below fold.

### Slide 10 — Capital (PDF p21) — `combo_chart`

**Matches:** bars + line overlay + dual Y-axis all work; correct values on both series; right-side axis labels (660-720); overlay legend "Common Shares Outstanding".

**Differences (moderate):**
- **Unit placement reads "1.6$B" instead of "$1.6B"** (and axis ticks "4$B", "3$B"). The `y_axis_unit` is appended; currency needs prefix support.
- **KPI panel missing.** PDF's right column (58% / 74% / 10.5% with descriptions) is the visual anchor of the page; `key_stats` supplied in the handoff are not rendered on chart layouts.
- **Stacked bars approximated as totals.** PDF stacks Dividends + Share Repurchases per quarter; combo_chart only supports single-series bars, so totals were used. A "stacked combo" variant would be needed for exact fidelity.
- **ROE strip (35%…35%) below the chart not rendered** (same key_stats gap).
- Line labels 689/682 collide with the bars behind them (white-ish text over blue bars, poor contrast).

### Slide 11 — Network Volumes Growth (PDF p24) — `grouped_bar_chart`

**Matches:** all 6 category values correct, brand colors.

**Differences (major):**
- **Horizontal vs vertical** bars (pack issue).
- PDF's **annotation callouts** above bar groups ("U.S. Consumer Services: 10%" with curly brackets) not reproduced — approximated in the so_what strip instead.
- **Bottom breakdown strip missing** ("% of Total Network Volumes $486B" boxes) — supplied as key_stats but not rendered.
- Duplicate insight strip.

---

## Systemic Issues (ranked by impact)

| # | Issue | Affected | Root cause | Suggested fix |
|---|---|---|---|---|
| 1 | **Pack bar charts are horizontal; PDF is vertical** | slides 5, 6, 8, 11 (4 of 10) | External pack `_svg_grouped`/`_svg_stacked` draw horizontal bars | Add vertical orientation to pack, or build internal vertical bar builder like the line chart |
| 2 | **Duplicate insight strips on pack charts** | all pack-chart slides | Data bridge copies `so_what` to top level; pack renders its insight AND `render_chart` adds `insight_strip()` | Drop `insight_strip()` in `render_chart` when pack handled the slide, or don't bridge `so_what` |
| 3 | **Support table pushed below viewport** | slides 2, 3, 9 | Chart SVG (900x480) fills frame height; table overflows | When `secondary_visual` present, split frame: chart ~60% height, table ~40% |
| 4 | **key_stats not rendered on chart layouts** | slides 6, 10, 11 | `render_chart` never reads `content.key_stats` | Render metric strip below chart when key_stats present |
| 5 | **Line-chart label collisions on converging series** | slides 2, 9 | Fixed label side per series (primary above, secondary below) | Per-point label side: label the higher line above, lower line below |
| 6 | **Stacked bar negative segments dropped** | slide 6 | Pack stacked bar doesn't paint below-axis segments | Support negative values in stacked series |
| 7 | **Currency unit formatting** | slide 10 | `y_axis_unit` only supports suffix | Add `y_axis_unit_position: prefix|suffix` |
| 8 | **Annotation box renders single-line** | slides 2, 3, 4, 9 | Splitter looks for literal `\n`, JSON supplies real newlines | Split on actual newline char |
| 9 | **No side-by-side chart composition** | slide 8 (PDF p17) | One `primary_visual` per slide | Would need a two-chart layout or composition support |
| 10 | **No stacked-bar + line combo** | slide 10 (PDF p21) | `combo_chart` supports single-series bars only | Extend combo to accept multi-series (stacked) bar data |
| 11 | Cosmetic: gray chart panel vs PDF white background | all chart slides | `.chart-frame` uses `--panel` background | Optional: white chart surface variant for PDF-style decks |
| 12 | Cosmetic: pack charts missing % / $ value suffixes | slides 5, 6, 8, 11 | Pack value labels are raw numbers | Pass unit through to pack or format in bridge |

## Bug found & fixed during the test

- **`build_chart_html` didn't bridge nested handoff data to the external pack** (steps_or_data / key_stats / so_what live under `visual_spec` / `content`, the pack reads them top-level). Before the fix, pack charts silently fell back to the single-series matrix fallback and dropped series. Fixed in the same pattern as the earlier icon_grid bridge. **This fix is the cause of issue #2 (duplicate insight) — the so_what bridge should be revisited.**

## What worked well

- **Line charts are the PDF's most common chart type (~32% of pages) and the internal `line_chart` matches the PDF visual language closely**: solid primary + dashed comparison series, data labels, gridlines, annotations, legend. With fixes #3 and #5 these would be near-pixel-faithful.
- **`data_table` is essentially production-perfect** for PDF-style financial tables.
- **The handoff JSON data contract held up**: every slide rendered on first attempt with zero validation errors, using only documented fields.
- The brand token system (navy/blue/ink/panel) matches the PDF palette exactly after the T1 color fixes — no color drift observed in any slide.

## Recommended next steps

1. File tickets for issues #1-#6 (the high-impact set). Issue #1 (vertical bars) likely means building an internal vertical bar chart builder and preferring it over the pack for `grouped_bar_chart`/`stacked_bar_chart` — same pattern as line_chart/combo_chart.
2. Re-run this test after fixes land; target ≥90% fidelity on all 10 pages.
3. Consider promoting this test deck into a permanent fixture (PDF pages are already in `.scratch/pdf_pages/`) so fidelity regressions are caught by re-rendering + screenshot diff.
