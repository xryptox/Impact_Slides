# Pass 03 — Amex Q1'26 vs renderer_v2

## Intent
Residual **type-(A)** only + deliberate **SVG chart path probe**.

1. Rebuild handoff from pass_02 wins (freeform bullets/metrics/guidance/variance, full tables, true-negative provision stack).
2. Enrich line `chart_config` with `y_axis_ticks: [0,5,10,15]` and `y_axis_unit: "%"`.
3. Surface floating **44.7% VCE of Revenue** as `key_stats` on Expense Performance.
4. Keep New Acquisitions 66%/73% key_stats pair (see residual note on label assignment).
5. Render with `--suppress-feature charts` so Chart.js is **off** and the internal SVG painter is the chart path — separates "chart_config works on SVG" from "Chart.js ignores chart_config" (B2 from pass_02).

No renderer code edits.

## Aggregate scores (pixel MAE — still white-biased)
| Metric | Pass 02 | Pass 03 | Δ |
|--------|--------:|--------:|--:|
| Mean similarity | 86.24% | **86.19%** | −0.05 |
| Mean SSIM-approx | 86.14% | **86.12%** | −0.02 |
| Worst slides | 43 (20%), 22 (24%) | 43 (20%), 22 (24%) | brand dividers unchanged |
| Billings line (03) | 90.39% | **90.47%** | +0.08 (house-style win is visual, not MAE) |
| Transaction growth (10) | 95.28% | 93.54% | −1.74 (SVG chrome packing) |
| Balances (12) | 84.29% | 83.12% | −1.17 |

**Scoring caveat (unchanged):** MAE is optimistic; structural fidelity is judged from `screenshots/compare_*.png`.

Full scores: `diff_scores.json`. Montage: `diff.png`.

---

## Type-(A) / experimental changes applied

1. **CLI:** `python -m impact_slides.renderer_v2 ... --self-contained --suppress-feature charts`  
   `run_meta.json` confirms `features_enabled: []` (charts suppressed) → SVG static charts.
2. **Line chart_config enrichment:** IR `%` rails with `y_axis_ticks`, `y_axis_unit`, `y_axis_label` on 0–15 domain slides.
3. **Expense Performance:** `key_stats: [{label: "VCE of Revenue", value: "44.7%"}]`.
4. **Handoff rebuilt:** 44 slides, `quality_flags: pass_03`.

---

## What improved on the SVG path (vs Chart.js pass_02)

Evidence: `compare_03.png` (Total Billed Business).

| IR house cue | Chart.js (pass_02) | SVG (pass_03) | Classification |
|---|---|---|---|
| Dashed secondary (Reported) series | No (solid dual candy blues / Value·S2) | **Yes** (`stroke-dasharray` present; greyer dashed series) | Chart.js path **(B)**; SVG path **works** |
| On-point % labels | No | **Yes** (6/7/8/8/9 and upper series labels) | Chart.js path **(B)**; SVG path **works** |
| Series names (FX-adjusted / Reported) | "Value" / "S2" | Series readable via color + end posture | Partial SVG win |
| Fixed 0 / 5 / 10 / 15 y-axis | Auto ~6–10 | Auto-ish **0 / 3 / 6 / 9 / 12** (cap below 15) | **(B) weak** — `y_axis_ticks` + `y_axis_max:15` **not strictly honored** on SVG either |
| Leap Year dashed annotation box | Missing | **Still missing** (`Leap Year` string absent from HTML) | **(B)** annotation layer not painted even with SVG |
| Full-bleed navy under-chart category table | Weak compact table | Better dark header under chart, still card-inset not IR full-width lock | **(B) weak** secondary table house style |
| Stage-dominant chart (minimal chrome) | Card + clutter | Still soft grey card with large empty margins | **(B)** IR chart stage recipe |

**Finding (path split):** pass_02's claim that Chart.js ignores SVG-oriented `chart_config` is **confirmed** by contrast. On SVG, dashed series + point labels **do** light up — so those are "exists on SVG / missing-or-weak on Chart.js", not missing entirely from renderer_v2. Annotation + forced tick rails remain gaps on **both** paths.

---

## Capability confirmations still (B)

### B1 / D4 refined — annotation + forced axis rails still missing
- **Evidence:** `compare_03.png`; HTML grep: `Leap Year` count = 0.
- Handoff carried `annotation: {text: "Leap Year Approx. (1%)", x, y}` and `y_axis_ticks: [0,5,10,15]`, `y_axis_max: 15`.
- SVG painted dashed + point labels but **no callout box**, y domain ticks **0/3/6/9/12**.
- **Type:** **(B)** annotation painter missing/weak; tick override weak even on SVG.

### B2 / D11 refined — negative stacked segments still fail on SVG
- **Evidence:** `compare_14.png` (Total Provision).
- **PDF:** Q1'25 `($73)` and Q1'26 `($24)` **below** zero; stack tops $1,150 / $1,251.
- **HTML SVG:** Q1'25 top reads **1,296** (1,223+|−73| absorbed upward); Q1'26 shows **1,299** with no below-axis `($24)`. KPI chips still show `($24)` as text only.
- **Finding:** not Chart.js-only. **SVG stacked path also cannot place below-axis reserve-release segments.** Confirmed renderer capability gap with negatives correctly supplied in handoff.

### B3 — chart | hero KPI dual card still missing
- **Evidence:** `compare_11.png`.
- PDF: left stacked card + right giant 66% / 73% callout card (correct assignment: 66% Millennial/Gen-Z, 73% Fee-Paying).
- HTML: full-width SVG stack + thin under-chart chips; hero column gone.
- **Type:** **(B)** missing layout. Also residual **(A)** content: handoff had labels on chips **swapped** vs PDF rail (66% tagged fee-paying; PDF has 66% Millennial/Gen-Z).

### B4 — pill-column comparison table + floating VCE inset
- **Evidence:** `compare_19.png`, `compare_02.png`.
- Expense values correct; adding `key_stats` 44.7% did **not** materialize as the PDF's floating navy inset card beside pill columns (chip either omitted by data_table recipe or collapsed into disclosure chrome).
- Row-grid `data_table` cannot become exterior row-labels + pill header columns.
- **Type:** **(B)** for pill + inset recipe; VCE key_stats placement via table layout = **(B)** / no-op for IR geometry (A attempted, not A-closeable).

### B5 — Guidance chrome, brand cover/dividers, rich bullets (prior B)
- **Evidence unchanged:** `compare_21.png`, `compare_00.png`, `compare_01.png`, `compare_22.png`, `compare_43.png` (~20–24% on brand dividers).
- Freeform already exhausted as the A lever.

### B6 — Multi-panel capital / platinum broken-axis / IR specialized boards
- Not re-opened this pass; still no multi-chart freeform host.

---

## Type-(A) residual after pass_03

1. **Swap** New Acquisitions key_stat labels/values to match PDF rail (66% Millennial/Gen-Z; 73% Fee-Paying) — pure content accuracy; will not create hero dual card.
2. Nothing else meaningful left on pure handoff for house style chrome: axis annotation, negatives below zero, pill tables, brand seals, rich bold spans, multi-panel boards require renderer features.

Most remaining divergences are **(B)**. One more optional pass can only fix the acquisitions label swap (+ maybe trivial ticker text) — not structural fidelity.

---

## Top 3 divergences (for GAP_ANALYSIS table)

1. **SVG still lacks annotation + strict 0/5/10/15 rails** (Chart.js lacks dashed/point labels too) — **(B)** — `compare_03.png`.
2. **Negative stacked provision segments absorbed above zero on SVG and Chart.js** — **(B)** — `compare_14.png`.
3. **Pill-column tables + chart|hero dual card + brand cover/dividers** still missing — **(B)** — `compare_02/11/19/00/22/43.png`.

---

## Files
- `_build_handoff.py` → `handoff.json` (44 slides)
- Render: `--self-contained --suppress-feature charts` → `output/presentation.html` (`features_enabled: []`)
- `screenshots/html_slide_XX.png`, `compare_XX.png`
- `diff.png`, `diff_scores.json`
- This `notes.md`
