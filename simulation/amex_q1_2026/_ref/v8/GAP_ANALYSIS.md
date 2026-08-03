# Gap Analysis v8: renderer_v2 vs Amex Q1'26 Earnings PDF
**(AFTER v7 baseline + round-5 T6/T7/T9/T10/T11/T12/T13)**

**Simulation:** `simulation/amex_q1_2026/`
**Source of truth:** `C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf`
**Renderer under test:** `impact_slides.renderer_v2` @ `origin/main` `a72e7bb`
  (PR #117 T10, #120 T6/T7/T9, #119 T11, #118 T12/T13, plus round-4 T1 #115 / T2 #116)
**Baseline (BEFORE / v7):** `wiki/baseline_v7_GAP_ANALYSIS.md`
**Method:** Playwright geometry assertions (±4px house tol) + side-by-side visual reading.
**No MAE / similarity %** — pixel-diff scoring retired (v8 measurement change).

---

## Scoring caveats (read first)

| Rule | Meaning |
|------|---------|
| **Geometry first** | Objective evidence is bounding-box / chart-scale measured-vs-expected pairs. Failure counts beat impression. |
| **SBS second** | Side-by-sides name furniture, weight, recipe, and packing that numbers alone miss. |
| **Fresh verification** | Every checklist ID was re-tested under a fresh handoff this run. Status is **not** inherited from PR titles or v7 conclusions. |
| **A vs B** | (A) fixable by handoff JSON only · (B) no handoff can express it → renderer capability gap. |
| **R3 brand-asset exclusion** | Centurion seal / third-party marks are **wontfix** per CONTEXT.md. Generic `seal_lockup` is by-design. Not a gap. |
| **Accepted divergence lock (r4 SPEC D11)** | **R1**, **F12+**, **N2 chip weight** are closed accepted divergences — recorded once, not ranked. |
| **Accepted divergence lock (r5 SPEC L3)** | **R2 L-bracket arm silhouette** is closed accepted divergence. T1 placement is distinct and verified; residual full-span elbow *recipe* can still be open. |
| **Worktree note** | GNHF launcher commit sat behind `origin/main` until FF — measuring T12/T13 without the FF falsely marks them still-gap. |

---

## Per-pass summary table

| Pass | What changed in handoff | Geometry | Top 3 remaining divergences | Type |
|-----:|-------------------------|----------|-----------------------------|------|
| **01** | Fresh handoff from v7 p02 + r5 knobs: s05 chevron `at:2`; s03/09/10/18 ann `x`/`y`; strip explicit series_colors on 13/16/20/26 for T10 default path; s16 pane labels; s14/27 exterior names clean single source | **56/57** (1 fail: multi_panel s05 tile0 single-series legend still on) | (1) multi_panel legend not auto-suppressed (2) F4+/N5/N6 packing-furniture (3) Mont-style CAGR / IR chrome residual | A + B |
| **02** | A-only: s05 `show_legend:false` + clear side_legend on single-series tile; s16 CAGR `elbow_arrow` + point labels; s14/s27 T2 wrap/gutter; s11 exterior tighten | **57/57** | (1) s16 CAGR elbow = thick full-span continuum ≠ PDF thin rule (2) R4 misread as scale — digits already 110px / residual card recipe (3) N6 still under-chart sheet | mostly B |
| **03** | A-only freeze pass: s05 clear `top_total` + force labels off left; s16 `$` prefix unit + CAGR type `band`; s27 FDIC `badge` on-card | **57/57** | (1) s16 band CAGR worse mass (678×413) / `$` labels still missing on dual_chart bars (2) N5 density + badge ≠ tall side callout (3) F4+/N6/R4 dual-metric frame residual | **B freeze** |

**Stop rationale after pass_03:** Remaining openings are all type **B** (or A levers exhausted/regressed). Further handoff passes cannot invent freestanding rate cells, thin CAGR dual-ended rules, IR L-elbow art continuum, dual-metric single-frame heros, or denser freestanding pills. **Handoff tuning frozen at pass_03** (3 of ≤10).

### Per-pass A closures vs B confirmations

| Pass | A result | B confirmation |
|-----:|----------|----------------|
| 01 | Round-5 verify rows all HOLD under fresh handoff (T6–T13, T10). Sole fail = multi_panel T11 path needs explicit `show_legend:false`. | F4+, N5 packing, N6 boxed cells, R2 chrome recipe, mis-scoped R4 type reading |
| 02 | multi_panel legend closed; s16 YoY % labels; s14 mid-token wrap; funding Chart.js legend off | CAGR elbow wrong silhouette; N6 sheet-not-boxes; R4 digit scale already 110px — residual layout recipe |
| 03 | s05 IR head chips (`top_total`) removed | `band` CAGR worse than elbow; dual_chart `$` prefix lever does not reach bar datalabels; s27 badge lands but not PDF tall side callout; R4 caption-beside already true — residual = two stacked cards vs one dual-metric frame |

---

## Geometry results table

Source of truth: `passes/pass_03/geometry.json` (tol ±4px). All **57/57 PASS**.

| Slide | Node | Measured | Expected | Δ px | P/F |
|------:|------|----------|----------|-----:|:---:|
| 05 | elbow.left vs bar0 centre | 108.73 | 108.74 | −0.01 | PASS |
| 05 | elbow.width vs bar0→bar4 centres | 633.11 | 633.12 | −0.01 | PASS |
| 05 | L elbow.left vs bar0 centre (wrap) | 108.73 | 108.74 | −0.01 | PASS |
| 05 | L elbow.width bar0→bar4 | 633.11 | 633.12 | −0.01 | PASS |
| 05 | L stem.left vs bar0 centre | 108.73 | 108.74 | −0.01 | PASS |
| 05 | L chevron split (tip+pill separate, no fused) | tip✓ pill✓ fused✗ | tip✓ pill✓ fused✗ | 0 | PASS |
| 05 | L chevron-tip centre vs bar2 (`at:2`) | 425.30 | 425.30 | 0.00 | PASS |
| 05 | L chevron-tip top ≥ chartArea.bottom | 561 | ≥531.4 | +29.6 | PASS |
| 05 | L chevron-pill centre vs bar2 | 425.44 | 425.30 | +0.14 | PASS |
| 05 | L chevron-pill top ≥ tip.bottom (stacked) | 585 | ≥583.0 | +2 | PASS |
| 05 | R axis-break top ≥ chartArea.bottom | 531.39 | ≥531.4 | −0.01 | PASS |
| 05 | R axis-break is small hatch (not mid-plot line) | w=10 h=14 | small `//` glyph | — | PASS |
| 05 | R tile colors navy/blue hex, no `var(--` | `#006FCF`,`#00175A` | hex navy/blue | — | PASS |
| 05 | L tile colors navy/blue hex, no `var(--` | `#00175A` | hex navy/blue | — | PASS |
| 03 | LeapYear ann.left vs area+x | 570.86 | 570.86 | 0.00 | PASS |
| 03 | LeapYear ann.top vs area+y | 64.00 | 64.00 | 0.00 | PASS |
| 09 | Reported ann.left vs area+x | 509.59 | 509.60 | −0.01 | PASS |
| 09 | Reported ann.top vs area+y | 74.00 | 74.00 | 0.00 | PASS |
| 10 | LeapYear ann.left vs area+x | 472.00 | 472.00 | 0.00 | PASS |
| 10 | LeapYear ann.top vs area+y | 60.80 | 60.80 | 0.00 | PASS |
| 18 | LeapYear ann.left vs area+x | 550.86 | 550.86 | 0.00 | PASS |
| 18 | LeapYear ann.top vs area+y | 64.00 | 64.00 | 0.00 | PASS |
| 16 | dual_chart pane headings count | 2 | ≥2 | — | PASS |
| 16 | pane0 single-series legend suppressed | display=false nDS=1 | falsy | — | PASS |
| 16 | pane0 colors no `var(--` / not black | `#00175A` | hex | — | PASS |
| 16 | pane1 single-series legend suppressed | display=false nDS=1 | falsy | — | PASS |
| 16 | pane1 colors no `var(--` / not black | `#006fcf` | hex | — | PASS |
| 05 | s05 pane0 single-series legend suppressed | display=false nDS=1 | falsy | — | PASS |
| 05 | s05 pane0 colors no `var(--` / not black | `#00175A` | hex | — | PASS |
| 05 | s05 pane1 multi-series legend kept | display=true nDS=2 | multi kept | — | PASS |
| 05 | s05 pane1 colors no `var(--` / not black | `#006FCF`,`#00175A` | hex | — | PASS |
| 19 | inset↔cell overlap `VCE of Revenue 44.7%` | 0 | 0 | 0 | PASS |
| 23 | inset↔cell overlap `U.S. Consumer % of NV 37%` | 0 | 0 | 0 | PASS |
| 23 | inset↔cell overlap `U.S. SME % of NV 22%` | 0 | 0 | 0 | PASS |
| all | deck-wide inset↔cell overlap count | 0 | 0 | — | PASS |
| 30 | annex group headers uniformly navy | 2× `rgb(0,23,90)` | all navy | — | PASS |
| 30 | annex white-on-navy header cells remain | 5 | ≥1 | — | PASS |
| 31 | annex group headers uniformly navy | 2× navy | all navy | — | PASS |
| 31 | annex white-on-navy header cells remain | 2 | ≥1 | — | PASS |
| 32 | annex group headers uniformly navy | 2× navy | all navy | — | PASS |
| 32 | annex white-on-navy header cells remain | 10 | ≥1 | — | PASS |
| 05 | T10 palette (post-black charts) | navy/blue hex | literal hex | — | PASS |
| 08 | T10 palette | `#006fcf` | hex | — | PASS |
| 10 | T10 palette | `#006fcf` | hex | — | PASS |
| 13 | T10 palette | `#006fcf`×2 | hex | — | PASS |
| 16 | T10 palette | `#00175A`,`#006fcf` | hex | — | PASS |
| 17 | T10 palette | `#006fcf`,`#00175a` | hex | — | PASS |
| 20 | T10 palette | `#00175a`,`#006fcf` | hex | — | PASS |
| 26 | T10 palette | hex pairs | hex | — | PASS |
| 27 | T10 palette | multi hex stacks | hex | — | PASS |
| 02 | pill board height / slide height | 0.673 | PDF denser (~0.7+) | — | PASS |
| 02 | pill column count | 3 | 3 | — | PASS |
| 27 | funding side_legend count | 0 | 0 | — | PASS |
| 27 | funding exterior name nodes | 7 | ≥1 | — | PASS |
| 27 | funding tile0 colors | navy/blue/grey | not black | — | PASS |
| 27 | funding tile1 colors | navy/blue/mutes | not black | — | PASS |
| all | no `var(--` in chart script colors | count=0 | 0 | — | PASS |

> Typo guard: board-height row is observational (PASS relative to structure), not a tol failure — F4+ residual is packing density, not missing columns. See delta table.

### Supplement live probes (pass_03, not all in shared geometry.json)

| Slide | Probe | Result |
|------:|-------|--------|
| 11 | `.gl-hero-value-num` font-size | **110px** / weight 700 |
| 11 | `.gl-hero-value-unit` `%` | **46.2px** |
| 11 | `.gl-hero-label` placement | **beside** number (not under) inside each card |
| 16 | CAGR `band` callout box | **≈678×413** (full-height span — wrong recipe) |
| 16 | dual_chart bar labels with `y_axis_unit:"$"` + prefix | still `0.9`…`2.8` — **no `$`** |
| 05 | `.gl-tile-ir-total` after clearing `top_total` | **absent** (A closed) |
| 27 | tile badge `92% of deposits FDIC…` | present, ~174×19 top-right; ≠ PDF tall side callout |
| 14 | reserve-rate furniture | under-chart dense `data_table` row, **not** freestanding boxed cells |
| 02 | pill col widths / cellH | ~434px × 3; cellH ~135px; board/slide **0.673** |

Reusable probes: `simulation/amex_q1_2026/probes/{geometry_probe,screenshot_sbs}.py`.

---

## Before / after delta: v7 open list → current renderer (v8)

**Headline deliverable.** Each required ID re-tested on the **current** renderer with **fresh** pass evidence. Round-5 rows are **verification**. No MAE columns.

| ID | v7 finding (summary + slide) | v8 status | Fresh evidence (geometry and/or SBS) | Notes |
|----|------------------------------|-----------|--------------------------------------|-------|
| **T10** default palette (was-black charts 05/08/10/13/16/17/20/26/27) | Not in v7 open list as landed r5; v7 measured against BLACK charts | **resolved** | Pass_03: all listed slides paint hex navy/blue; deck assertion `no var(-- in chart script colors` count=0. s16 default path → `#00175A`/`#006fcf`. SBS `compare_05/16/27.png` | Correct colour **does** change the reading — packing/furniture residuals remain real, but colour no longer confounds them. v7 black-chart SBS conclusions on those tiles are unreliable. |
| **T6** axis-break glyph (s05 right) | n/a (landed r5) | **resolved** | Break box top=531.39 vs chartArea.bottom=531.4 (Δ −0.01); size 10×14 hatch; **no mid-plot line** (`midPlotLines` empty) | Outside plot at axis origin as designed. |
| **T7** chevron split (s05 left) | n/a (landed r5) | **resolved** | tip+pill separate, fused=false; tip centre = bar2 centre 425.30 (Δ 0) with handoff `at:2`; tip top 561 ≥ area.bottom 531.4; pill stacked under tip (+2px) | v7's `at:4` was handoff error; PDF anchors Refresh at Q3'25 = `at:2`. |
| **T9** annotation anchoring (s03/10/18 Leap Year; s09 Reported) | n/a (landed r5) | **resolved** | All four boxes land at chartArea+(x,y) within 0.01px (see geometry table) | Declare x/y as plot-area px offsets; they are honoured. |
| **T11** pane headings (s16 Net Card Fees) | n/a (landed r5) | **resolved** (dual_chart) + **A-closed** multi_panel | s16: 2× `.gl-tile-label`; both single-series legends display=false. s05 multi_panel tile0 needed explicit `show_legend:false` (pass_01 FAIL → pass_02 PASS). Multi-series s05 tile1 legend kept (nDS=2). | Auto-suppress is **dual_chart-only**. multi_panel single-series is an A lever, not a missing capability once known. |
| **T12** inset collisions (s19/23 + deck sweep) | n/a (landed r5) | **resolved** | s19/s23 overlap = 0; deck-wide inset↔cell hits = **[]** / count 0. Layout is flex row-reverse gutter. | Remaining inset gap is cosmetic skin (solid navy pill vs PDF outlined VCE box) — not collision. |
| **T13** annex banding (s30/31/32) | n/a (landed r5) | **resolved** | Group headers both `rgb(0,23,90)` on 30/31/32; white-on-navy head cells remain (counts 5/2/10). | No light-blue column-index alternation. |
| **F4+** freestanding pill packing (s02) | still-gap / weak | **still-gap / weak** | Geometry: 3 cols, widths ~434, cellH ~135, board/slide **0.673**. SBS `pass_03/side_by_side/compare_02.png`: structure matches; PDF denser borders/row rhythm/stub weight. No packing A knobs left after r5. | **Exists but weak.** Type B. |
| **N6** provision furniture (s14) | still-gap / weak | **still-gap / weak** | Engaged exterior names + under-chart `data_table` + T2 wrap (A improved mid-token). SBS `compare_14.png`: still dense navy sheet row + footer KPI — **not** freestanding left label + five bordered white `%` cells. | Wire reuse ≠ furniture. **B.** |
| **N5 / F11 residual** funding density (s27) | partial — packing weak after legend A win | **partial / still-gap weak** | side_legend=0; exterior names=7; T2 knobs (wrap 16 / gutter 150 / font 16); badge A-partial for FDIC. SBS `compare_27.png`: cleaner than v7 triple-legend, but card density, on-stack `$` totals, and tall side FDIC callout still short of PDF. | Legend conflict remains A-fixed. Residual packing **B weak**. |
| **R4** hero dual % (s11) | partial — type scale weak | **reclassified → partial (card recipe)** — **digit scale resolved** | Live CSS: num **110px**, unit **46.2px**, label **beside** number. SBS `compare_11.png`: residual is **two stacked cards** vs PDF **one framed dual-metric panel** + missing in-card chart title. | Not a type-scale gap on current main. Future feature = dual-metric frame recipe. **B weak.** |
| **R2 chrome residual** (s05, post-T1) | partial — T1 geo OK; chrome recipe still-gap | **partial** — geo held; chrome **still-gap / weak** | Elbow/stem at bar centres Δ≤0.01; chevron split+anchor OK. SBS `pass_03/side_by_side/compare_05.png`: full-span blue continuum + right arrowhead ≠ PDF short L-elbow into mid-span pill. Head chips A-removed. Dual legend on multi-series right tile kept by design. | **T1 holds.** L-bracket silhouette **closed accepted r5 L3** — do not reopen. Residual = elbow **recipe / IR board chrome (B)**. |
| **R2 L-bracket silhouette** | open-ish residual art in v7 future list | **closed: accepted divergence per r5 spec L3** | T1 placement ±0.1px class; vertical bracket-arm silhouette matching is subjective and locked | Recorded once; not a gap. |
| **R1** flat stage residual | closed D11 | **closed: accepted divergence per r4 spec D11** | not reopened | Not a gap. |
| **F12+** annex multi-level header precision | closed D11 | **closed: accepted divergence per r4 spec D11** | not reopened | Not a gap. |
| **N2 chip weight** | closed D11 | **closed: accepted divergence per r4 spec D11** | right-card year chips remain 14px bold path | Not a gap. Heavier wrong on non-Amex decks. |
| **R3** Centurion seal | dropped wontfix | **dropped: wontfix per CONTEXT.md brand-asset rule** | cover uses generic `seal_lockup` by design | Excluded from gap counts, future list, recommended order. |

### NEW residuals / reclassifications this run

| ID | Finding | Slide / evidence | Type |
|----|---------|------------------|------|
| **N8** | CAGR thin dual-ended rule + mid pill + end ticks — neither `elbow_arrow` nor `band` is the PDF recipe (`band` paints ~678×413 full-height span; elbow is thick continuum capsule) | PDF p17 / slide **16**; `pass_03/side_by_side/compare_16.png`; live band box probe | **B** missing chrome recipe (callout types exist but wrong art) |
| **N9** | dual_chart bar point-label `$` prefix — `y_axis_unit:"$"` + `y_axis_unit_position:"prefix"` does not reach bar datalabel formatter (live still `0.9`…`2.8`) | slide **16** left; pass_03 notes | **B** weak / path gap (lever exists, dual_chart bars ignore) |
| **N10** | dual_chart linked single enclosure vs PDF **two separate rounded cards** with in-card titles | slide **16**; `compare_16.png` | **B** weak (headings via T11 OK; card skin residual) |
| **R4 reclass** | Digit scale + caption-beside already correct; residual is **single dual-metric hero frame** + missing in-card chart title | slide **11**; live CSS + `compare_11.png` | **B** weak (layout recipe, not type scale) |
| **R2-IR board** | Right tile dual legend (side_legend + Chart.js) + title packing still diverges from PDF title-only boards even after clearing `top_total` | slide **05** right; `compare_05.png` | refines **R2 chrome B** |

Carry-forward from earlier baselines (reconfirmed, not gaps): F10+ anniversary domain, N1 under-chart tables, F3 signed stacks, N3/N4 dual labels+negchips, N5 wire + T2 knobs, #114 board vertical fill, T1 calloutGeometry.

### Divergence catalog (compressed, v8)

| Div # | Theme | Primary IDs | v8 note |
|------:|-------|-------------|---------|
| D1 | Brand cover seal | R3 | **wontfix excluded** |
| D3 | Pill freestanding packing | F4+ | still weak |
| D4 | IR line stage chrome | R1 | **closed accepted D11** |
| D5 | Chart / hero KPI dual | R4 | **type scale resolved**; dual-metric frame residual |
| D8 | Multi-panel / broken-axis boards | F10+, F11+, R2, N2, N5, T6/T7 | **F10+/N2/T6/T7 closed**; T1 geo holds; R2 chrome + N5 pack residual |
| D9 | Dense annex tables | F12+, T13 | **F12+ accepted D11**; **T13 banding resolved** |
| D13/D15 | Under-chart secondary | N1, T12 | N1 closed; **T12 collision resolved**; inset skin cosmetic |
| D16 | Stacked dual labels + signed paren | N3/N4 | mostly resolved |
| D17 | Exterior segment name column | N5, T2 | wire + knobs + single-source A-done; packing weak |
| D18 | Horizontal anniversary domain | F10+ | closed |
| D19 | Provision furniture | N6 | still weak (no boxed cells) |
| D20 | Callout coordinate frame | R2/T1 | **resolved**; residual recipe chrome |
| D21 *(new)* | CAGR thin-rule chrome | N8 | elbow/band wrong recipe |
| D22 *(new)* | dual_chart `$` bar labels + dual cards | N9/N10 | path weak / skin residual |

---

## Prioritized future-feature list (still open AFTER this run)

Only items open on fresh evidence. **Resolved round-5 verifies (T6–T13, T10), accepted D11/L3 locks, and R3 wontfix are omitted.** Ranked by visual severity + structural weight — **not** by any percentage. Each cites PDF slide + pass evidence.

| Pri | Feature | What it enables | Motivating evidence | Missing vs weak | A/B |
|----:|---------|-----------------|---------------------|-----------------|-----|
| **P0** | **R2 — IR callout / board chrome recipe** (post-T1) | Short L-elbow into mid-span blue pill (art continuum, not coordinate frame); IR title-only head chrome that coexists with multi-series legend needs; chevron scale closer to PDF | PDF p6 / slide **05**; `passes/pass_03/side_by_side/compare_05.png`; geometry elbow/stem Δ≤0.01 but SBS chrome ≠ PDF | **Exists but weak** (T1 placement OK; recipe wrong). L3 silhouette lock stays closed. | **B** |
| **P1** | **N8 — CAGR thin dual-ended rule chrome** | Thin rule from first→last bar, mid `% CAGR` pill, end ticks, under-label — not full-span elbow capsule or full-height band | PDF p17 / slide **16**; `compare_16.png`; band box ≈678×413; elbow thick continuum | **Exists but wrong recipe** (`elbow_arrow` / `band` both miss) | **B** |
| **P1** | **N5 residual / F11 — multi_panel card + exterior column density** | Dense multi-line exterior names + rounded dual-card packing + on-stack dollar totals + tall on-card FDIC callout after legend conflict is gone | PDF p28 / slide **27**; `compare_27.png`; geometry side_legend=0, names=7 | **Exists but weak** (wire + T2 + sole-name A-done) | **B** |
| **P1** | **F4+ — freestanding pill-column packing finish** | Three navy-header freestanding statement columns at PDF density (tighter row rhythm, stronger stub/border weight) | PDF p3 / slide **02**; `compare_02.png`; board/slide 0.673, cols 3×~434, cellH~135 | **Exists but weak** (`gl-pill-free`) | **B** |
| **P2** | **N6 — provision furniture polish** | Freestanding reserve-rate **boxed period cells** + left label chip (+ exterior series legend furniture). Values already correct via N1/N4. | PDF p15 / slide **14**; `compare_14.png` | **Exists but weak** (under-chart sheet ≠ boxes) | **B** |
| **P2** | **N9 — dual_chart `$` prefix on bar point labels** | `$0.9`…`$2.8` tops matching PDF Net Card Fees left board | slide **16**; pass_03 unit-prefix attempt failed live | **Exists but weak / path gap** (schema lever ignored on dual_chart bars) | **B** |
| **P2** | **N10 — dual_chart separate rounded cards** | Two visually separate in-card boards (not one linked dual enclosure) while keeping T11 pane headings | slide **16**; `compare_16.png` | **Exists but weak** (skin/frame) | **B** |
| **P3** | **R4 — dual-metric hero frame recipe** | One framed panel carrying both giant % metrics with captions beside (not two stacked hug cards); optional in-card chart title | PDF p12 / slide **11**; `compare_11.png`; digits already 110px / label beside | **Exists but weak** (was mis-scoped as type scale in v7) | **B** |
| **P3** | **Inset skin polish** (post-T12) | Outlined boxed KPI inset (e.g. VCE % of Revenue) vs solid navy pill — collision already zero | PDF slides **19/23**; geometry overlap 0; SBS residual cosmetic | **Exists but weak** (cosmetic) | **B** |

### Dropped / closed this run (do not re-implement as open gaps)

| ID | Why dropped |
|----|-------------|
| **T10** default palette | **Resolved** — hex navy/blue; zero `var(--` in chart scripts |
| **T6** axis-break | **Resolved** — outside-plot `//` hatch |
| **T7** chevron split | **Resolved** — separate tip+pill, `at:2` |
| **T9** annotation x/y | **Resolved** — chartArea+(x,y) within 0.01px |
| **T11** pane headings | **Resolved** dual_chart; multi_panel via A `show_legend:false` |
| **T12** inset collisions | **Resolved** — deck-wide overlap 0 |
| **T13** annex banding | **Resolved** — uniform navy group headers |
| **T1** callout geometry | Still holds (reconfirmed); residual is R2 recipe |
| **T2** exterior-name knobs | Still land; residual packing only |
| R4 **digit scale / caption-under** as originally framed | Digit scale + caption-beside already correct; reframed above |
| **R1 / F12+ / N2 chip weight** | **Accepted divergence** r4 SPEC D11 |
| **R2 L-bracket silhouette** | **Accepted divergence** r5 SPEC L3 |
| **R3** Centurion seal | **Wontfix** CONTEXT.md brand-asset rule |
| F10+, N1, F3, N3/N4 capability, N5 wire | Prior resolutions reconfirmed |

### Recommended implementation order (future renderer track — not this sim)

1. **R2 chrome recipe** — short L-elbow art continuum + IR title packing (worst structural board remaining; geometry already right).
2. **N8 CAGR thin-rule chrome** — only honest fix for slide 16 span furniture after elbow/`band` exhaustion.
3. **N5 residual packing** — multi_panel density + on-stack totals + tall side callout (Funding).
4. **F4+** freestanding pill packing finish (Summary).
5. **N6** provision boxed reserve-rate cells.
6. **N9/N10** dual_chart `$` labels + separate card skins.
7. **R4** dual-metric single-frame hero recipe (not another type-size knob).
8. Inset outlined-box skin (lowest severity cosmetic).

---

## What renderer_v2 already does well

Credited on fresh pass_01–03 evidence (geometry + SBS), not cargo-culted from PR titles:

- **44-slide self-contained Chart.js deck** with Boardroom tokens and stable 1:1 page map; pass_03 geometry **57/57**.
- **T1 calloutGeometry** — elbow/stem/chevron live px vs bar centres and chartArea (±0.1px class) still holds under a fresh handoff (`pass_03/geometry.json` s05).
- **T2 exterior-name knobs** — font/offset/gutter/wrap serialize and paint (funding + provision exterior stacks).
- **T10 default palette** — literal hex navy/blue; turns off the v7 black-chart confounder entirely.
- **T6 axis-break** — small outside-plot `//` hatch at origin; no false mid-plot threshold line.
- **T7 chevron** — separate triangle + pill, under tick row, category-anchored (`at:N`).
- **T9 annotations** — honour plot-area (x,y) offsets (Leap Year / Reported boxes).
- **T11 pane headings** — dual_chart real in-card headings + single-series legend suppress; multi-series legends kept.
- **T12 inset gutter** — zero bounding-box collisions deck-wide (s19/s23 and sweep).
- **T13 annex banding** — uniform navy group headers; white-on-navy subheads retained.
- **F10+ anniversary window**, **N1 under-chart tables**, **F3 signed stacks**, **N3/N4 dual labels + negchips**, **#114 board vertical fill** — all still land.
- **Handoff surface rich enough** that three A-only passes closed every remaining non-structural miss (multi_panel legend, IR head chips, name wrap, YoY point labels) before freezing on pure B residuals.

---

## Artifacts index

| Path | Role |
|------|------|
| `extracted/pdf_page_*.png` | PDF rasters (PyMuPDF dpi=200) |
| `extracted/slides.json` | Vision transcription |
| `probes/geometry_probe.py` | Playwright geometry assertions |
| `probes/screenshot_sbs.py` | 1920×1080 shots + SBS composites |
| `passes/pass_0{1,2,3}/handoff.json` | Builder handoffs (frozen at p03) |
| `passes/pass_0{1,2,3}/output/` | Rendered HTML decks |
| `passes/pass_0{1,2,3}/geometry.json` | Measured assertion sets |
| `passes/pass_0{1,2,3}/side_by_side/` | Focus SBS PNGs |
| `passes/pass_0{1,2,3}/notes.md` | Per-pass A/B journals |
| `GAP_ANALYSIS.md` | This deliverable |

**Companion:** copy to `wiki/baseline_v8_GAP_ANALYSIS.md` as the tracked before-snapshot for the next run.
