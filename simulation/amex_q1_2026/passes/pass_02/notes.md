# Pass 02 — Amex Q1'26 vs renderer_v2

## Intent
Close **type-(A)** handoff gaps only (freeform layout, axis/name config, filled tables, true negative stacks, strip invented `so_what`). No renderer code changes.

## Aggregate scores (pixel MAE — still white-biased)
| Metric | Pass 01 | Pass 02 | Δ |
|--------|--------:|--------:|--:|
| Mean similarity | 86.12% | **86.24%** | +0.12 |
| Mean SSIM-approx | 85.71% | **86.14%** | +0.43 |
| Worst slides | 43 (20%), 22 (24%) | 43 (20%), 22 (24%) | unchanged brand dividers |
| Biggest A wins | — | Highlights +5.0pp; variance freeform +3.7–3.9pp; macro dual +4.8pp | |

**Scoring caveat (unchanged):** MAE is optimistic; structural fidelity is judged from `screenshots/compare_*.png`.

Full scores: `diff_scores.json`. Montage: `diff.png`.

---

## Type-(A) changes applied

1. **Business Highlights** → `visual_spec.grid` freeform single-column bullets (no split two-card chrome).
2. **Line charts** → `chart_config.y_axis_min/max`, `series_names`, `series_colors`, `series_styles`, `annotation` (Leap Year / Reported), dropped decorative KPI chips on billings slides.
3. **Guidance** → freeform `metric_stack` two KPIs; removed Boardroom `so_what` sentence.
4. **Total Provision** → true negative reserve release `(-73)` / `(-24)` in stack data + reserve-rate secondary table.
5. **Expense Performance** → full 7-line grid from PDF p19 text (was placeholder).
6. **Appendix tables** (network volumes, FX impact, T&E) + **Annex 1–2** key rows filled from PDF / `slides.json` raw_text.
7. **Variance commentary + FLS** → freeform bullet columns parsed from raw_text.
8. **New Acquisitions** → only two hero % KPIs retained under stacked chart (still no true right-rail layout).

---

## What improved (visual / content)

| Slide | Evidence | Result |
|------:|----------|--------|
| 01 Highlights | `compare_01.png` | Freeform removed "The case / In the evidence" dual cards; single column of all 7 bullets. Typographic weight still far weaker than PDF (muted small body). **+5.0pp**. |
| 19 Expenses | `compare_19.png` | Correct $ / YoY values across lines. Still row-grid not pill columns; missing floating **44.7% VCE of Revenue** callout card. Content A mostly closed; chrome B remains. |
| 28–29 Variance | `compare_28/29` | Dense freeform bullets from IR commentary — much closer narrative than pass_01 placeholders. **+3.7–3.9pp**. |
| 03 Billings line | `compare_03.png` | Secondary G&S/T&E table still present; KPI chip clutter gone. **Chart house style did NOT respond to handoff axis/names/annotation** (see below). |

---

## Capability confirmations (type B) — pass_02 evidence

### B1 — Chart.js path ignores SVG-oriented chart_config (extends D4)
- **Evidence:** `compare_03.png` — handoff set `y_axis_min:0`, `y_axis_max:15`, `series_names: [FX-adjusted, Reported]`, gray/navy colors, `annotation: Leap Year Approx. (1%)`.
- **HTML:** still auto domain ~6.0–10.0, legend **Value / S2**, candy default blues, **no dashed series, no point % labels, no leap-year callout box**.
- **Finding:** `chart_config` fields that work on the internal SVG painter are **not wired through the Chart.js MVP configs** (`_chartjs_line_config`). For interactive charts, IR house style is **exists-but-weak / missing entirely on Chart.js path**.

### B2 — Stacked Chart.js cannot render below-axis negative reserve release (confirms D11)
- **Evidence:** `compare_14.png` (Total Provision).
- **PDF:** Q1'25 shows **($73)** and Q1'26 **($24)** as dark segments **below** the zero line; tops of stacks show $1,150 / $1,251 totals.
- **HTML:** Q1'25 draws a **positive** top segment totaling ~1,296 (write-offs + |−73| mis-stacked upward); Q1'26 has **no** below-axis ($24). KPI strip shows "($24)" as text only.
- **Finding:** negative stacked segments = **capability gap / Chart.js stacked path failure**. Handoff correctly supplied negatives; renderer cannot express IR provision stacks.

### B3 — Freeform improves structure but not IR typography / emphasis (extends D2)
- **Evidence:** `compare_01.png`.
- **Match:** one column of bullets, correct seven items.
- **Miss:** PDF large navy body + **selective bold** partner/product phrases; HTML small muted bullets, no rich spans, left Boardroom title (not centered).
- **Finding:** freeform_grid is the right A lever for geometry; **inline rich text** and IR bullet-sheet recipe remain B.

### B4 — No chart|hero dual card (confirms D5)
- **Evidence:** `compare_11.png`.
- **PDF:** left stacked bars card + right giant 66% / 73% callout card.
- **HTML:** full-width Chart.js stack + thin under-chart KPI chips (and labels are still not hero-scale; also easy to swap 66/73 assignment the way chips compress wrap).
- **Finding:** freeform cannot embed charts; `dual_chart` is two charts not chart+metrics. **Missing layout**.

### B5 — Guidance freeform ≠ single IR statement card (confirms D6)
- **Evidence:** `compare_21.png`.
- **PDF:** centered navy-header rounded card, underlined label/value pairs.
- **HTML:** two separate pale metric tiles top-of-stage, disclosure rail.
- **Finding:** values correct (A done); chrome recipe B.

### B6 — Pill-column comparison tables still absent (confirms D3)
- **Evidence:** `compare_02.png` (unchanged structure), `compare_19.png` expense.
- Row-grid `data_table` cannot become exterior row-labels + pill header columns + floating VCE inset.

### B7 — Brand section / trailing dividers unchanged (confirms D7)
- **Evidence:** slides 22 & 43 still ~20–24% (near-white HTML vs navy/blue bleed PDF).

### B8 — Secondary table under line chart not full-width category-aligned IR house style
- **Evidence:** `compare_03.png` — compact dark row under chart vs PDF full-bleed navy header table locked to category axis.

---

## Type-(A) residual (could try later passes)

1. Swap New Acquisitions 66%/73% labels if reversed relative to PDF hero rail (content accuracy).
2. Add floating **44.7% VCE** as a `key_stats` chip beside expense table (won't place as PDF inset but may communicate).
3. Try forcing **SVG** chart path if any handoff/feature flag exists without code edits — if none, treat Chart.js-defaulting as B.
4. Further annex 3–6 cell fill from PNG vision (raw_text thin).
5. Capital multi-panel: freeform metric_stack of ROE quarterly nums (won't draw multi-chart board).

Most remaining divergences on product chrome / house style / multi-panel IR recipes are now **(B)**.

---

## Top 3 divergences (for GAP_ANALYSIS table)

1. **Chart.js line house style** ignores axis domain, series names, dashed secondary, annotations, on-point labels — **(B)** — `compare_03.png`.
2. **Negative stacked provision segments** dropped/absorbed — **(B)** — `compare_14.png`.
3. **Pill-column + brand cover/divider recipes** still missing — **(B)** — `compare_02.png`, `compare_00/22/43.png`.

---

## Files
- `handoff.json` (from `_build_handoff.py`)
- `output/presentation.html`
- `screenshots/html_slide_XX.png`, `compare_XX.png`
- `diff.png`, `diff_scores.json`
