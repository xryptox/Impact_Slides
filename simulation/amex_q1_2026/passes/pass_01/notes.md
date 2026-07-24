# Pass 01 notes — v3 after round-2 fidelity work

**Goal:** Fresh re-test of every v2 residual/open gap against the **current** renderer using handoff-only upgrades on the gap slides.  
**Baseline handoff:** `simulation/amex_q1_2026_v2_pre_round2/passes/pass_03/handoff.json`  
**Chart path:** Chart.js (default CLI)  
**Scores:** `diff_scores.json` — mean MAE sim **89.03%** (v2 final 89.25%, **Δ −0.22 pp**)  
**N:** 44 HTML slides ↔ 44 PDF pages  

Artifact roots:

- handoff: `handoff.json` (from `_build_handoff.py`)
- HTML: `output/presentation.html`
- side-by-sides: `screenshots/compare_XX.png`
- PDF rasters: `../../extracted/pdf_page_XX.png`

## What this pass changed (handoff only)

| Slide | Change | Targets v2 residual |
|------:|--------|---------------------|
| 00 | `title_or_opening` → **`brand_cover`** + `brand_mark=seal_lockup` | F6+ load path, R3 seal pack |
| 05 | retention tile → **`horizontal_bar_chart`** + `bar_labels_inside` + elbow/chevron **`callouts`** + tall-card chrome | F10+, R2, F11+ |
| 14 | keep signed `Reserve Build/(Release)` series (`-73`…`-24`); stacked + `allow_negative` | **F3** negative stacks |
| 22 / 43 | dividers → `brand_mark=seal_lockup` (drop generic SVG) | R3 |
| 27 | multi_panel tiles add **`top_total` / `side_legend` / `badge`** (tall-card path) | F11+ |

All other slides carried forward from v2 pass_03 unchanged.

## Headline scores (key slides)

| Slide | Topic | v2 final % | v3 p01 % | Δ pp | Reading |
|------:|-------|----------:|---------:|-----:|---------|
| 00 | Cover | 89.48 | **82.18** | −7.30 | Load path **works** (`data-layout="brand_cover"` #1); recipe/placement weaker than prior title_or_opening |
| 02 | Summary pill | 91.39 | 89.71 | −1.68 | `gl-pill-free` freestanding shells now in DOM (capability); packing/CSS still weak vs PDF |
| 05 | Platinum dual board | 72.83 | **71.19** | −1.64 | Horizontal bars **paint**; domain clamp + callout chrome still weak → worst slide |
| 11 | Acquisitions dual | 83.10 | 83.50 | +0.40 | Structure still OK; hero chrome residual |
| 14 | Total Provision | 84.31 | **84.49** | +0.18 | **Below-axis negatives paint** (F3 capability resolved) |
| 19 | Expense pill | 91.72 | 89.35 | −2.37 | Same freestanding path as s02 |
| 22 | Appendix divider | 87.32 | 87.35 | +0.03 | Named seal present; bracketing vs Centurion watermark residual |
| 27 | Funding multi_panel | 78.37 | **80.94** | **+2.57** | Tall-card `top_total`/`badge`/`side_legend` engage; PDF side-legend packing still weaker |
| 43 | Trailing brand | 85.11 | 85.10 | −0.01 | Stable |

**Worst structural (this pass):** 05 (71.2), 27 (80.9), 00 (82.2), 11 (83.5), 14 (84.5).

## Per residual: verified status after pass_01

### F3 — Below-axis negative stacked bars → **RESOLVED (capability)**

- **Evidence:** `screenshots/compare_14.png`; HTML Chart.js config contains  
  `"Reserve Build/(Release)", "data": [-73.0, 222.0, 125.0, 141.0, -24.0]` with `scales.y.stacked=true` and `ticks.min ≈ -80.3`.
- **Visual:** PDF left shows `($73)` / `($24)` below the axis under Q1'25 / Q1'26; HTML right shows the same small negative stubs under the zero line (write-offs above).
- **Type:** previously **(B)** hard gap in v2; **closed by round-2 paint path** when handoff carries true negatives (no abs() absorb).
- **Residual weak (not capability-block):** PDF uses solid IR colors + total labels above stacks + under-table Reserve Rate chips; HTML uses Boardroom card chrome + KPI chips below chart. Packing = weak **(A/B cosmetic)**, not missing geometry.

### F6+ — Cover seal path without index break → **RESOLVED (load path) / residual recipe**

- **Evidence:** `compare_00.png`; first slide tag `data-layout="brand_cover"` `data-slide-number="1"`; deck stays **44** slides (no injected cover).
- **Type:** v2 "exists but blocked" → load path **unblocked**.
- **Residual (B weak / product art):** named `seal_lockup` is a small centered generic badge, not the large right-edge Centurion watermark + left stacked title/date of the PDF. MAE fell because recipe placement differs from v2's `title_or_opening` + inline SVG.

### R3 — First-class brand seal asset pack → **PARTIAL**

- Named mark path works (`brand_mark=seal_lockup` inlined; count seal/lockup references in HTML).
- **Not** trademark-quality Centurion ribbon lockup. Still stronger than inventing SVG per handoff, weaker than PDF brand system. Evidence: `compare_00.png`, `compare_22.png`, `compare_43.png`.

### F10+ — Horizontal bar + anniversary retention window → **PARTIAL (capability exists, clamp weak)**

- **Evidence:** `compare_05.png` right card is true **horizontal** bars (months as rows, 2025/2026 series) — this did **not** work in v2 (vertical 0–100 bars).
- **Still wrong vs PDF:** domain still paints ~0–100 with a dashed guide rather than a hard 90–100 anniversary window; year labels not inside bars like PDF; dual navy header cards missing.
- Type mix: capability of `horizontal_bar_chart` **exists**; anniversary window / IR card recipe **still weak (B)**.

### R2 — Geometric callout elbow / chevron → **PARTIAL (paints, placement weak)**

- HTML includes `chartjs-callout` elbow + chevron nodes (counts in presentation.html).
- On `compare_05.png` the elbow/chevron do **not** reproduce PDF's clean "+ ~6 percentage points" band arrow over bars + navy Refresh pill under Q1'26. Residual = geometry exists but IR placement/chrome weak (**B weak**).

### F11+ — IR dual tall-card multi_panel → **PARTIAL (improved)**

- **Evidence:** `compare_27.png` + HTML `gl-tile-tall`, `gl-tile-top-total` (`$210B / $219B`, `$151B / $157B`), `gl-tile-badge`, `gl-tile-legend`.
- MAE +2.57 pp vs v2.
- Still short of PDF: exterior right-side legends with segment labels, per-column freestanding `$` tops, dual equal soft-gray IR cards. **Exists but weak.**

### F4+ — Freestanding pill statement columns → **LARGELY RESOLVED (structure) / packing residual**

- DOM now emits `gl-pill-free` + exterior `gl-pill-labels` rail + per-column `gl-pill-shell` (see HTML around Summary Financial Performance).
- v2 claimed "headers only"; **round-2 grew freestanding shells**.
- `compare_02.png` / packing density still not PDF-perfect (row alignment/spacing, footnote band). Score slightly down vs v2 — hard-number pixel metric does not fully reflect structural win.

### F1 residual / R1 — IR line stage chrome → **still residual weak** (unchanged handoff)

- Not re-tuned this pass. `compare_03.png` / `compare_18.png` still Boardroom card stage vs PDF flat stage. Capability of dashed lines / domain / annotation remains.

### R4 — Hero dual type scale → **still residual weak**

- `compare_11.png` 83.5% (+0.4). Structure from v2 intact; giant % + narrative chrome still short.

### F12+ — Annex multi-level headers → **still residual weak**

- Annex slides 28–36 remain high-90s MAE; not a focus this pass.

## Matched well (carry-forward)

- Full 44-slide self-contained HTML.
- IR bullets (`compare_01` 93.1%), guidance card (`compare_21` 91.8%), line house on billed business (`compare_03` 90.4%), annex packing, theme + `chrome_level=minimal`.
- **New this pass structural unlocks:** signed stacked negatives, horizontal_bar type, callout nodes, brand_cover as #1, tall-card multi_panel slots, freestanding pill shells.

## Divergences still open (for pass_02+)

| ID | Observation | Type A vs B | Pass_02 plan |
|----|-------------|-------------|--------------|
| D-cover-recipe | brand_cover center seal vs PDF left-title + large watermark | mostly **B** (asset/layout recipe); minor A: headline/date content fields | Try tone/content packing; do not expect Centurion fidelity without asset work |
| D-plat-window | hbar domain not 90–100 hard window; labels not inside | **B weak** (config fields exist but clamp incomplete) + residual A on series orientation | Probe `y_axis_min/max` / categories swap months↔years as PDF |
| D-plat-callout | elbow/chevron not IR band | **B weak** placement | Tune callout `from`/`to`/`value` (A) then stop |
| D-fund-legend | side legend exists but not PDF exterior labels | **B weak** | already using API; residual B |
| D-pill-pack | freestanding shells OK; density/CSS | **B weak** | limited A left |
| D-stage | Boardroom card chrome on charts | **B weak** (R1) | leave |

## Stop rule progress

- F3 is no longer a hard gap (major v2 P0 closed on evidence).
- Residual pure-(A) list still has: platinum callout tuning, possible retention series reshape, cover content packing.
- Pass budget: **1 / 10 used**.

## Mean MAE caveat

White-canvas bias still inflates means. Cover MAE drop is a **recipe trade** (exercising brand_cover path), not a renderer regression on fixed handoff. Judge gap closures from side-by-sides for F3 / F10 / F11 / F4 / F6, not deck-mean alone.
