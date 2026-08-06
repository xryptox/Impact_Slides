# Gap Analysis v9: renderer_v2 vs Amex Q1'26 Earnings PDF
**(AFTER v8 baseline + post-v8 handoff levers N8/N6/N5)** **Simulation:** `simulation/amex_q1_2026/`
**Source of truth:** `C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf`
**Renderer under test:** `impact_slides.renderer_v2` @ worktree `12ef950` (current main line; no production edits this run)
**Baseline (BEFORE / v8):** `wiki/baseline_v8_GAP_ANALYSIS.md`
**Method:** Playwright geometry assertions (±4px house tol; lever probes use ≤8–12px where noted) + 1920×1080 side-by-side visual reading.
**No MAE / similarity %** — pixel-diff scoring stays retired.

---

## Verifier audit (independent, post-run)

Checked by the host agent against the committed artifacts, not the run's summary.

**Reproducibility:** re-rendering `passes/pass_01/handoff.json` with current
`main` reproduces the committed `presentation.html` byte-for-byte once random
canvas/tab ids are normalised. Renderer diff vs `main` is empty, so no
production code was touched.

**Scope gate:** tracked changes are confined to `simulation/` plus this
baseline. `git diff main..HEAD` touches no `impact_slides/`, `tests/`,
`scripts/`, or CI path.

**Confirmed independently:**

- N8 `measure_rule`: live `.chartjs-callout-measure*` markup present; the two
  `chartjs-callout-band` hits are dormant CSS definitions with **zero** live
  elements, so "band gone" is accurate.
- N5 knobs: `barPercentage: 0.58` and `categoryPercentage: 1.0` on 7 datasets,
  3 `chartjs-fill` wraps.
- N6 root cause: re-derived. All four alignment conditions on the *table* side
  match, but `render_chart` builds `labels` only from `Mapping` steps
  (`layout/recipes/charts.py:93-104`); this chart's `steps_or_data` is
  list-of-lists, so `n == 0` and `aligned` is always False. The report's
  diagnosis is correct and the 5 failures are real.
- Geometry counts: recomputed from `geometry.json` as 85 pass / 5 fail,
  matching the stated summary.

**Corrections made by the verifier:**

1. **R4 was wrongly reported still-gap.** Its probe `R4_s11` targeted slide 11,
   which is a `line_chart` and holds no hero, returning `nCards: 0`; the cited
   `522×349` / "two stacked cards" figures appear in no evidence file.
   Re-measuring the real `chart_hero_dual` slide (**12**) shows one
   `.gl-hero-stack` frame 570×755 at grid `1140px 570px` (2:1) with borderless
   hero rows inside — i.e. #124 shipped and R4 is **resolved**. Rows 151, 178,
   200 and the recommended order were corrected.
2. `N10`'s cited `852×813` panes were also absent from the evidence files, but
   re-measurement confirms them exactly, so that verdict stands as written.

**Verifier follow-up:** all four deferred items (`N9`, `F4+`, `R6-A`, `R6-C`) have now been measured directly — see *Verifier measurement round 2* below. `N9`'s verdict was **wrong** and is corrected there.
were not independently re-measured beyond the committed probe output.


---

## Scoring caveats (read first)

| Rule | Meaning |
|------|---------|
| **Geometry first** | Objective evidence is bounding-box / chart-scale measured-vs-expected pairs. Failure counts beat impression. |
| **SBS second** | Side-by-sides name furniture, weight, recipe, and packing that numbers alone miss. |
| **Fresh verification** | Every checklist ID was re-tested under a fresh handoff this run. Status is **not** inherited from PR titles or v8 conclusions. |
| **A vs B** | (A) fixable by handoff JSON only · (B) no handoff can express it → renderer capability gap. |
| **R3 brand-asset exclusion** | Centurion seal / third-party marks are **wontfix** per CONTEXT.md. Generic `seal_lockup` is by-design. Not a gap. |
| **Accepted divergence lock (r4 SPEC D11)** | **R1**, **F12+**, **N2 chip weight** are closed accepted divergences — recorded once, not ranked. |
| **Accepted divergence lock (r5 SPEC L3)** | **R2 L-bracket arm silhouette** is closed accepted divergence. T1 placement is distinct and verified. |
| **Scope** | Simulation / observation only. No `impact_slides/` production edits. |

---

## Per-pass summary table

| Pass | What changed in handoff | Geometry | Top remaining divergences | Type |
|-----:|-------------------------|----------|-----------------------------|------|
| **01** | Fresh from v8 pass_03 + three shipped levers: s17 `measure_rule` CAGR (text `17%`, caption `% CAGR`); s15 `secondary_visual.skin: outlined_boxes`; s28 both tiles `bar_percentage:0.58`, `category_percentage:1.0`, `fill_tile:true` | **85/90** (5 fail: s15 outlined cell cx vs bar cx — alignment path not engaged) | (1) N6 plot-align for list-shaped primary steps (2) R4 dual-metric single-frame residual (3) N5 tall side FDIC callout / on-stack chrome | A exhausted + B |
| **02–04** | *not run* | — | Remaining items are B, accepted, or source-contract — not handoff-tunable | freeze |

**Stop rationale after pass_01:** The three required post-v8 levers were applied and freshly measured. N8/`measure_rule` and N5 packing knobs **hold**. N6 skin paints unfilled boxes without a duplicated thead, but plot-column alignment does not engage because `render_chart` only extracts category labels from **Mapping** primary steps — this handoff's stacked-bar `steps_or_data` is list-shaped, so `aligned=false` always. That is not fixable by further secondary JSON alone. No other residual is handoff-tunable without inventing new renderer knobs. **Handoff tuning frozen at pass_01** (1 of ≤4).

### Per-pass A closures vs B confirmations

| Pass | A result | B confirmation |
|-----:|----------|----------------|
| 01 | **N8** measure_rule: thin h=25 rule, left/right on bar0/barN centres (δ≈0), pill+caption centred; **N5** bar%/cat%/fill_tile land (0.58/1.0/true, wrap/tile h ratio 0.878); **N6** skin active, 5 unfilled cells, no thead | **N6** column alignment requires list-format category extraction (or equivalent) — source header would match periods if labels extracted; **R4** still two stacked hero cards; **N5** badge ≠ tall side FDIC callout; **R6-A** pane title 13px gray residual *(then; shipped #139 post-v9)*; **F4+** packing still weak vs PDF full board |

---

## Geometry results table

**Tolerance:** house ±4px (core v8 contracts); measure_rule endpoints ±8px; outlined cell centres ±12px; packing ratios qualitative thresholds as noted.
**Summary:** 85/90 passed, 5 failed.

| Slide | Node | Measured | Expected | Δpx | Pass/Fail |
|------:|------|----------|----------|-----:|-----------|
| 5 | elbow.left vs bar0 centre | 108.73 | 108.74 | -0.01 | PASS |
| 5 | elbow.width vs bar0-to-bar4 centres | 633.11 | 633.12 | -0.01 | PASS |
| 5 | L elbow.left vs bar0 centre (wrap) | 108.73 | 108.74 | -0.01 | PASS |
| 5 | L elbow.width bar0→bar4 | 633.11 | 633.12 | -0.01 | PASS |
| 5 | L stem.left vs bar0 centre | 108.73 | 108.74 | -0.01 | PASS |
| 5 | L chevron split (tip+pill separate, no fused) | {"tip": true, "pill": true, "fused": false} | {"tip": true, "pill": true, "fused": false} | 0 | PASS |
| 5 | L chevron-tip centre vs bar2 (at:2) | 425.3 | 425.3 | -0.0 | PASS |
| 5 | L chevron-tip top >= chartArea.bottom (outside plot) | 561 | >=531.4 | 29.6 | PASS |
| 5 | L chevron-pill centre vs bar2 | 425.44 | 425.3 | 0.14 | PASS |
| 5 | L chevron-pill top >= tip.bottom (stacked) | 578 | >=576.0 | 2 | PASS |
| 5 | R axis-break top >= chartArea.bottom (outside plot) | 531.390625 | >=531.4 | -0.01 | PASS |
| 5 | R axis-break is small hatch (h<=24 or w<=40) | {"w": 10, "h": 14, "text": ""} | small // glyph, not 2px line across plot |  | PASS |
| 5 | R tile dataset colors not black / no var(-- | ["#006FCF", "#00175A"] | navy/blue hex |  | PASS |
| 5 | L tile dataset colors not black / no var(-- | ["#00175A"] | navy/blue hex |  | PASS |
| 3 | s03 LeapYear ann.left vs area+ x | 570.86 | 570.86 | -0.0 | PASS |
| 3 | s03 LeapYear ann.top vs area+ y | 64.0 | 64.0 | 0.0 | PASS |
| 9 | s09 Reported ann.left vs area+ x | 509.59 | 509.6 | -0.01 | PASS |
| 9 | s09 Reported ann.top vs area+ y | 74.0 | 74.0 | 0.0 | PASS |
| 10 | s10 LeapYear ann.left vs area+ x | 472.0 | 472.0 | 0.0 | PASS |
| 10 | s10 LeapYear ann.top vs area+ y | 60.8 | 60.8 | -0.0 | PASS |
| 18 | s18 LeapYear ann.left vs area+ x | 550.86 | 550.86 | -0.0 | PASS |
| 18 | s18 LeapYear ann.top vs area+ y | 64.0 | 64.0 | 0.0 | PASS |
| 16 | dual_chart pane headings present (count>=2) | 2 | >=2 |  | PASS |
| 16 | pane0 single-series legend suppressed | {"legendDisplay": false, "nDS": 1} | legend.display falsy |  | PASS |
| 16 | pane0 colors no var(-- / not black | ["#00175A"] | hex navy/blue |  | PASS |
| 16 | pane1 single-series legend suppressed | {"legendDisplay": false, "nDS": 1} | legend.display falsy |  | PASS |
| 16 | pane1 colors no var(-- / not black | ["#006fcf"] | hex navy/blue |  | PASS |
| 5 | s05 pane0 single-series legend suppressed | {"legendDisplay": false, "nDS": 1} | legend.display falsy |  | PASS |
| 5 | s05 pane0 colors no var(-- / not black | ["#00175A"] | hex navy/blue |  | PASS |
| 5 | s05 pane1 multi-series legend kept | {"legendDisplay": true, "nDS": 2} | legend available if multi |  | PASS |
| 5 | s05 pane1 colors no var(-- / not black | ["#006FCF", "#00175A"] | hex navy/blue |  | PASS |
| 19 | inset overlap 'VCE of Revenue44.7%' | 0 | 0 | 0 | PASS |
| 23 | inset overlap 'U.S. Consumer % of NV37%' | 0 | 0 | 0 | PASS |
| 23 | inset overlap 'U.S. SME % of NV22%' | 0 | 0 | 0 | PASS |
| all | deck-wide inset↔cell overlap count | 0 | 0 |  | PASS |
| 30 | annex group headers uniformly navy (no light-blue alt) | {"count": 2, "bgs": ["rgb(0, 23, 90)", "rgb(0, 23, 90)"], "sample": [{"text":... | all navy, no alt light-blue |  | PASS |
| 30 | annex white-on-navy header cells remain | 5 | >=1 |  | PASS |
| 31 | annex group headers uniformly navy (no light-blue alt) | {"count": 2, "bgs": ["rgb(0, 23, 90)", "rgb(0, 23, 90)"], "sample": [{"text":... | all navy, no alt light-blue |  | PASS |
| 31 | annex white-on-navy header cells remain | 2 | >=1 |  | PASS |
| 32 | annex group headers uniformly navy (no light-blue alt) | {"count": 2, "bgs": ["rgb(0, 23, 90)", "rgb(0, 23, 90)"], "sample": [{"text":... | all navy, no alt light-blue |  | PASS |
| 32 | annex white-on-navy header cells remain | 10 | >=1 |  | PASS |
| 5 | chart colors navy/blue, no var(--, not black | ["#00175A", "#006FCF", "#00175A"] | literal hex palette |  | PASS |
| 8 | chart colors navy/blue, no var(--, not black | ["#006fcf"] | literal hex palette |  | PASS |
| 10 | chart colors navy/blue, no var(--, not black | ["#006fcf"] | literal hex palette |  | PASS |
| 13 | chart colors navy/blue, no var(--, not black | ["#006fcf", "#006fcf"] | literal hex palette |  | PASS |
| 16 | chart colors navy/blue, no var(--, not black | ["#00175A", "#006fcf"] | literal hex palette |  | PASS |
| 17 | chart colors navy/blue, no var(--, not black | ["#006fcf", "#00175a"] | literal hex palette |  | PASS |
| 20 | chart colors navy/blue, no var(--, not black | ["#00175a", "#006fcf"] | literal hex palette |  | PASS |
| 26 | chart colors navy/blue, no var(--, not black | ["#006fcf", "#00175a", "#006fcf", "#00175a"] | literal hex palette |  | PASS |
| 27 | chart colors navy/blue, no var(--, not black | ["#00175A", "#006FCF", "#B8BFC9", "#00175A", "#006FCF", "#5B6B9A", "#B8BFC9"] | literal hex palette |  | PASS |
| 2 | pill board height / slide height | 0.673 | PDF near-full board (~0.7+) |  | PASS |
| 2 | pill column count | 3 | 3 |  | PASS |
| 27 | funding side_legend count (want 0) | 0 | 0 |  | PASS |
| 27 | funding exterior name nodes present | 7 | >=1 |  | PASS |
| 27 | funding tile0 colors | ["#00175A", "#006FCF", "#B8BFC9"] | not black |  | PASS |
| 27 | funding tile1 colors | ["#00175A", "#006FCF", "#5B6B9A", "#B8BFC9"] | not black |  | PASS |
| 16 | measure_rule present (no band) | {"measure": true, "band": false} | {"measure": true, "band": false} |  | PASS |
| 16 | measure.left vs bar0 centre | 200.44 | 200.44 | -0.0 | PASS |
| 16 | measure.right vs barN centre | 876.69 | 876.7 | -0.01 | PASS |
| 16 | measure thin height (h<=48) | 25 | <=48 |  | PASS |
| 16 | pill.cx vs measure.cx | 538.56 | 538.56 | 0.0 | PASS |
| 16 | pill.cy vs measure mid-y | 273.8 | 273.8 | 0.0 | PASS |
| 16 | pill text is 17% | 17% | 17% |  | PASS |
| 16 | caption.cx vs pill.cx | 538.56 | 538.56 | 0.0 | PASS |
| 16 | caption below pill | {"cap_top": 290.296875, "pill_bottom": 286.296875} | cap.top >= pill.bottom - 4 |  | PASS |
| 16 | caption text is % CAGR | % CAGR | % CAGR |  | PASS |
| 14 | outlined_boxes skin active (no support table) | {"outlined": true, "table": false} | {"outlined": true, "table": false} |  | PASS |
| 14 | no duplicated header thead | [] | [] |  | PASS |
| 14 | outlined value cell count | 5 | 5 |  | PASS |
| 14 | outlined cells unfilled (no solid fill) | rgba(0, 0, 0, 0) | transparent/white |  | PASS |
| 14 | outlined cell0.cx vs bar0.cx | 947.41 | 640.84 | 306.56 | FAIL |
| 14 | outlined cell1.cx vs bar1.cx | 1043.41 | 762.84 | 280.56 | FAIL |
| 14 | outlined cell2.cx vs bar2.cx | 1139.41 | 884.84 | 254.56 | FAIL |
| 14 | outlined cell3.cx vs bar3.cx | 1235.41 | 1006.84 | 228.56 | FAIL |
| 14 | outlined cell4.cx vs bar4.cx | 1331.41 | 1128.84 | 202.56 | FAIL |
| 27 | funding tile count | 2 | 2 |  | PASS |
| 27 | tile0 fill_tile class | True | True |  | PASS |
| 27 | tile0 barPercentage≈0.58 | 0.58 | 0.58 | 0.0 | PASS |
| 27 | tile0 categoryPercentage≈1.0 | 1 | 1.0 | 0.0 | PASS |
| 27 | tile0 wrap/tile height ratio | 0.878 | >=0.55 |  | PASS |
| 27 | tile0 barW and cat pitch | {"barW": 194.59, "catW": 335.5, "gap": 140.91, "bar_to_gap": 1.381} | bar_percentage 0.58 → bar occupies majority of pitch |  | PASS |
| 27 | tile0 stackH present | 586.4 | >0 |  | PASS |
| 27 | tile1 fill_tile class | True | True |  | PASS |
| 27 | tile1 barPercentage≈0.58 | 0.58 | 0.58 | 0.0 | PASS |
| 27 | tile1 categoryPercentage≈1.0 | 1 | 1.0 | 0.0 | PASS |
| 27 | tile1 wrap/tile height ratio | 0.878 | >=0.55 |  | PASS |
| 27 | tile1 barW and cat pitch | {"barW": 194.59, "catW": 335.5, "gap": 140.91, "bar_to_gap": 1.381} | bar_percentage 0.58 → bar occupies majority of pitch |  | PASS |
| 27 | tile1 stackH present | 586.4 | >0 |  | PASS |
| 27 | tile1 FDIC badge present (not tall side callout) | {"left": 1639.125, "top": 212.1875, "w": 173.875, "h": 19, "right": 1813, "bo... | badge node may exist; tall side callout is B residual |  | PASS |
| all | no var(-- in chart script colors | {"count": 0, "sample": []} | 0 |  | PASS |

### Supplement live probes (pass_01 `verify_extras.json`, not all in geometry.json)

| Slide | Finding |
|------:|---------|
| **16** N8 | `.chartjs-callout-measure` present; **no** `.chartjs-callout-band`; rule thin h=25; pill `17%`; caption `% CAGR` under pill; endpoints on bar0/barN |
| **14** N6 | `.chart-support-outlined` without `chart-table-aligned`; cells unfilled `rgba(0,0,0,0)`; cell0.cx−bar0.cx ≈ **+307px** (flex row, not plot-pitched) |
| **14** N6 contract | Primary `steps_or_data` is list-of-lists; alignment code only reads Mapping labels → `n=0` → `aligned=false`. Secondary header periods would match cats **if** labels extracted. **Record as source/renderer contract miss, not a missing skin.** |
| **27** N5 | barPercentage 0.58, categoryPercentage 1.0, `chartjs-fill` on; barW≈194.6 catW≈335.5; stackH≈586; FDIC **badge** w≈174 h≈19 top-right — **not** PDF tall side callout |
| **17** N9 | datalabels **do** carry the `$` prefix. Painted label models read `$0.9 … $2.8` (bar pane) and `16% … 20%` (line pane). The earlier “no `$` prefix” reading came from inspecting `options.plugins.datalabels` before the shell bound `_labels` into a formatter. |
| **16** N10 | **two** `.dual-chart-pane.chart-frame.gl-card` (852×813 each) under `.gl-grid-2.dual-chart` — separate framed cards **do** paint |
| **12** R4 | `chart_hero_dual` **does** paint ONE `.gl-hero-stack` frame (570×755, radius 14px, filled) at grid `1140px 570px` (**2:1**); the two `.gl-hero.card` (522×349) inside are borderless/transparent rows, not separate cards; digits **110px** / unit **46.2px**. Verifier note: `verify_extras.json` `R4_s11` probed slide **11** (a `line_chart`) and returned `nCards:0`, so the original 'two stacked cards' reading was unevidenced. |
| **05** R2 | one `.chartjs-callout-elbow` w≈633 h=30 + stem; not `elbow-line` class on this handoff (default continuum). L3 silhouette remains accepted |
| **02** F4+ | 28px type present on `.gl-pill-stub`/cells (8+ nodes); board h/slide = **0.673** (geometry); freestanding packing still short of PDF full-bleed board |
| **16** R6-A | **v9 measure (historical):** pane titles `.gl-tile-label` **13px / 600 / rgb(99,102,106)**; x ticks 13px. **Post-v9:** shipped #139 — `.gl-chart-pane-title` 40/700/navy + opt-in `chart_config.typography` (see `SPEC_renderer_v2_amex_fidelity_r6.md` / renderer AGENTS) |
| **19/23** R6-C | inset cards navy `gl-inset card` 200×90, value 34px; deck-wide inset↔cell overlap **0** (geometry). Cosmetic recipe vs PDF still open; collision closed |
| **F5** | theme override **not triggered** this handoff (`--color-primary:#00175A` only; no attempt to retint default chart palette) |

---

## Before / after delta: v8 open list → current renderer (v9)

| ID | v8 status | v9 fresh evidence | v9 status | Notes |
|----|-----------|-------------------|-----------|-------|
| **T1** callout geometry | resolved (holds) | s05 elbow left/width vs bars δ≈0; chevron tip+pill at bar2 | **resolved** | reconfirmed |
| **T2** exterior-name knobs | resolved (packing residual) | s27 exterior name nodes = 7 | **resolved** (wire) | packing separate |
| **T6** axis-break | resolved | s05 R hatch outside plot, small | **resolved** | reconfirmed |
| **T7** chevron split | resolved | tip+pill separate, at:2 | **resolved** | reconfirmed |
| **T9** annotation x/y | resolved | s03/09/10/18 δ≈0 | **resolved** | reconfirmed |
| **T10** default palette | resolved | all probed tiles hex navy/blue; 0 `var(--` | **resolved** | reconfirmed |
| **T11** pane headings / legend | resolved | dual_chart headings ≥2; single-series legend off | **resolved** | reconfirmed |
| **T12** inset collisions | resolved | deck-wide overlap 0 | **resolved** | reconfirmed |
| **T13** annex banding | resolved | s30–32 uniform navy headers | **resolved** | reconfirmed |
| **N8 / R6-B** CAGR chrome | still-gap (elbow/band wrong) | measure_rule thin h=25; endpoints on bar centres; pill+`% CAGR` caption centred | **resolved** | lever applied pass_01 |
| **N6** outlined reserve-rate | still-gap (sheet not boxes) | skin paints 5 unfilled stroked boxes, no thead; **cx not plot-aligned** (aligned path off) | **partial** | skin A works; align B (list-label extract) |
| **N5 / F11** funding packing | still-gap density | bar% 0.58 / cat% 1.0 / fill_tile true measured; wrap/tile 0.878 | **partial** | knobs A work; tall FDIC callout + on-stack $ chrome still B |
| **N9** grouped-bar `$` labels | still-gap | painted datalabel models read `$0.9…$2.8`; `_fmt_value_label(0.9,'$','prefix')` → `$0.9`; shell `bindMatrix` resolves `_labels` at init | **resolved** (corrected by verifier) | v9 draft misread pre-bind config; unit prefix path works |
| **N10** dual_chart two cards | still-gap (weak) | two separate `.dual-chart-pane.chart-frame.gl-card` 852×813 | **resolved** | fresh DOM structure |
| **R4** dual-metric hero frame | type scale OK; frame residual | slide **12**: one `.gl-hero-stack` 570×755 frame, grid `1140px 570px` = 2:1, heroes borderless inside | **resolved** (corrected by verifier) | v9 draft said still-gap citing slide 11, which holds no hero; re-measured on slide 12 |
| **F4+** pill packing | still weak | 28px type present; board/slide h 0.673 | **still-gap** (weak B) | type partial hold |
| **R2** elbow geometry / line recipe | T1 holds; L3 accepted; chrome residual | default elbow continuum on s05 (not line-class) | **partial / accepted L3** | line-style not exercised this handoff |
| **R6-A** s17 pane title/ticks/labels | open (possible B) | titles 13px gray 600; ticks 13; rotation 50 | **shipped #139** (post-v9) | capability closed; archived-v9 full audit outstanding |
| **R6-C** inset skin s19/s23 | cosmetic open; collision closed | navy inset cards + 34px values; overlap 0 | **partial** | collision resolved; recipe cosmetic |
| **F5** theme palette tint | not assumed | no theme override in handoff | **not triggered** | |
| **R1** | accepted D11 | not reopened | **accepted** | |
| **F12+** | accepted D11 | not reopened | **accepted** | |
| **N2** chip weight | accepted D11 | not reopened | **accepted** | |
| **R2 L-bracket arm** | accepted L3 | not reopened | **accepted** | |
| **R3** Centurion | wontfix | not reopened | **wontfix** | |
| Annex 33–36 vision defect | excluded | not refiled | **excluded** | source-transcription, not renderer |

---

## Prioritized future-feature list (still open AFTER this run)

Each item tied to PDF page + v9 evidence path. Marked **missing** vs **weak**, **A** vs **B**.

| Pri | ID | Need | PDF | Evidence | Miss/Weak | A/B |
|----:|----|------|-----|----------|-----------|-----|
| 1 | **N6 align** | Extract category labels from list-shaped `steps_or_data` (or document required Mapping shape) so `outlined_boxes` gets `chart-table-aligned` pitch | p14 / slide 15 | `passes/pass_01/geometry.json` fails cell0–4 cx; `verify_extras.json` N6_contract; `side_by_side/compare_14.png` | **missing** align path for list primary | **B** |
| ~~2~~ | ~~**R4 frame**~~ | **WITHDRAWN by verifier** — already shipped (#124). Re-measured slide 12: single 2:1 `.gl-hero-stack` frame present | p11 / slide **12** | verifier Playwright re-measure (stack 570×755, grid 1140px 570px) | — | — |
| 3 | **N5 callout** | Tall multi-line side FDIC callout (badge is not a substitute) + on-stack total chrome | p28 / slide 28 | `geometry.json` packing rows; badge box in observations; `compare_27.png` | **missing** callout recipe | **B** |
| ~~4~~ | ~~**N9 $ labels**~~ | **WITHDRAWN by verifier** — `$` prefix already painted (`$0.9…$2.8` on slide 17) | p16 / slide **17** | verifier read of `Chart.$datalabels._labels` model lines | — | — |
| 5 | **F4+ pack** | Near-full-bleed freestanding pill board packing (28px type already present) | p2 / slide 02 | geometry pill h ratio 0.673; `compare_02.png` | **weak** packing | **B** |
| ~~6~~ | ~~**R6-A type**~~ | **SHIPPED #139** (post-v9) — HTML pane title + opt-in `chart_config.typography`; live contract in renderer AGENTS | p16 / slide 17 | historical R6A_s16 13px gray | — | — |
| 7 | **R6-C inset** | PDF inset card recipe polish (collision already 0) | p19/p23 | R6C_s19/s23; `compare_19.png` `compare_23.png` | **weak** cosmetic | **B** |
| 8 | **R2 line elbow** | Opt-in line-style elbow continuum where PDF wants thin rule (L3 arm accepted closed) | p5 / slide 05 | R2_s05 default elbow; `compare_05.png` | **weak** recipe | **B** (knob may exist; not proven this deck) |

### Dropped / closed this run (do not re-implement as open gaps)

| ID | Status |
|----|--------|
| **N8 / measure_rule CAGR** | **Resolved** — thin dual-ended rule + mid pill + caption |
| **N10 dual cards** | **Resolved** — two framed dual-chart panes |
| **T6 T7 T9 T10 T11 T12 T13 T1 T2** | **Resolved** — reconfirmed under fresh handoff |
| **R1 / F12+ / N2 / R2 L3 / R3** | **Accepted / wontfix** — not reopened |
| **F5** | **Not triggered** |

### Recommended implementation order (future renderer track — not this sim)

1. N6 list-label alignment for `outlined_boxes` (unblocks provision boards already skinned).
2. ~~R4 single dual-metric frame recipe~~ — withdrawn: verified already shipped.
3. ~~N9 `$` datalabel prefix on dual_chart/grouped bars~~ — withdrawn: verified already working.
4. N5 tall side callout (distinct from badge).
5. F4+ / R6-C polish (R6-A shipped #139).

---

## What renderer_v2 already does well

- **Geometric callouts that match math:** T1 elbow/chevron centres lock to bar centres within house tol; new **measure_rule** pins first/last bar centres with a thin rule, centred pill, and separate caption — the PDF CAGR recipe on Net Card Fees.
- **Chart.js packing knobs that actually land:** `bar_percentage` / `category_percentage` / `fill_tile` show up in resolved dataset options and wrap geometry (Funding tiles).
- **Outlined support skin:** opt-in `secondary_visual.skin: outlined_boxes` drops thead, paints unfilled gray-stroked cells — correct furniture family even when pitch align is off.
- **Dual-chart card chrome:** two separate framed panes with in-pane titles and suppressed single-series legends (N10/T11).
- **Palette integrity:** literal navy/blue hex across probed charts; zero `var(--` leakage in chart scripts (T10).
- **Inset collision discipline:** deck-wide inset↔cell overlap stays 0 (T12) while inset cards still render.
- **Annex header banding:** uniform navy group headers on s30–32 (T13).
- **Annotation pin math:** LeapYear/Reported callouts hit chartArea+(x,y) within 0.01px (T9).
- **Hero type scale:** dual-metric digits hold 110px / 46.2px unit with labels beside values.
- **Pill type ramp:** 28px comparison type is present on the Q1 board stubs/cells.

---

## Artifacts index

| Path | Role |
|------|------|
| `simulation/amex_q1_2026/passes/pass_01/handoff.json` | v9 pass_01 handoff (v8 p03 + 3 levers) |
| `simulation/amex_q1_2026/passes/pass_01/output/presentation.html` | rendered deck (44 slides) |
| `simulation/amex_q1_2026/passes/pass_01/geometry.json` | 90 geometry assertions |
| `simulation/amex_q1_2026/passes/pass_01/verify_extras.json` | N9/R2/N10/R4/F4+/R6/F5/N6 extras |
| `simulation/amex_q1_2026/passes/pass_01/screenshots/` | HTML 1920×1080 focus slides |
| `simulation/amex_q1_2026/passes/pass_01/side_by_side/` | PDF‖HTML compares `02,05,11,14,16,19,23,27` |
| `simulation/amex_q1_2026/probes/geometry_probe.py` | v8 contracts + main runner |
| `simulation/amex_q1_2026/probes/v9_levers.py` | measure_rule / outlined_boxes / packing probes |
| `simulation/amex_q1_2026/probes/verify_extras.py` | supplemental verify probes |
| `simulation/amex_q1_2026/probes/screenshot_sbs.py` | SBS generator |
| `simulation/amex_q1_2026/extracted/` | PDF page rasters (from v8 archive) |
| `simulation/amex_q1_2026/_ref/v8/` | frozen v8 pass archive |
| `wiki/baseline_v9_GAP_ANALYSIS.md` | tracked copy of this report |

---

*End v9 baseline. Simulation only — no production renderer changes.*

---

## Verifier measurement round 2 (N9, F4+, R6-A, R6-C)

The four items the run left un-remeasured were measured directly against the
committed deck with Playwright at 1920x1080. Slide numbers below are
`data-slide-number` (the run's probe keys used stale indices).

### Method note that changed a verdict

Chart configs are emitted as inert JSON (`script.chartjs-config`) because JSON
cannot carry functions. The shell's `bindMatrix` (`shell.py:330-345`) *deletes*
`_labels` and installs `formatter` at init. So:

- reading `options.plugins.datalabels.formatter` after init shows **nothing**
- the painted text lives in the plugin's own models: `Chart.$datalabels._labels[i].model().lines`

Reading the wrong one is what produced the v9 draft's false N9 gap.

### N9 - RESOLVED (was reported still-gap)

Slide 17 `dual_chart`. Handoff sets `y_axis_unit: "$"`,
`y_axis_unit_position: "prefix"`.

| Pane | Layout | Painted datalabel models |
|---|---|---|
| 0 | `grouped_bar_chart` | `$0.9 $1.1 $1.3 $1.4 $1.7 $2 $2.3 $2.8` |
| 1 | `line_chart` | `16% 16% 17% 20% 20% 19% 18% 16%` |

Confirmed at the unit level too: `_fmt_value_label(0.9, "$", "prefix")` returns
`$0.9`, and `_chartjs_bar_config` emits
`_labels: [["$0.9", ..., "$2.8"]]`. **The `$` prefix path works. Not a gap.**

### R6-A - was CONFIRMED still-gap at v9 measure; **shipped #139** (post-v9)

Slide 17, measured against the PDF figures in `wiki/SPEC_renderer_v2_amex_fidelity_r6.md`
(the spec labels this slide 16 by PDF page; it is `data-slide-number` 17):

| Element | Measured (v9) | PDF target | Delta then |
|---|---|---|---|
| Pane title | **13px** / 600 / `rgb(99,102,106)` gray | 40px bold (navy) | ~3x + colour + weight |
| Y ticks | **13px** | 24px bold | ~1.8x + weight |
| X ticks | **13px** | not measured in spec | — |
| Datalabels | **11px** bold | 28px bold | ~2.5x |

That measure locked the #139 contract. **Capability is now shipped:** shared
`.gl-chart-pane-title` + opt-in `chart_config.typography` (owner:
`impact_slides/renderer_v2/AGENTS.md`, `charts/typography.py`). Do not re-file
the pre-fix 13px gray residual as an open renderer gap. Archived-v9 full-deck
audit remains outstanding (`artifacts/r6a_typography_v9_audit.md`).

### F4+ - CONFIRMED weak (packing, not type)

Slide 3 `pill_comparison`: board `.gl-pill.gl-pill-free.gl-card` is
1728x726.8 at y=201.2, so **h/slide = 0.673**, w/slide = 0.900, transparent
background, 16px radius, `display:flex`. Type is already correct at **28px**
(stubs 600, heads 700 on navy, cells). 6 stubs / 15 cells.
So the residual is purely vertical packing, matching the run's read.

### R6-C - CONFIRMED partial (cosmetic only)

Insets are on slides **20** and **24** (not 19/23):

| Slide | Count | Box | Skin |
|---|---|---|---|
| 20 | 1 | 200x89.7 @ x=1624 | navy `rgb(0,23,90)`, 14px radius, no border, 16px text |
| 24 | 2 | 200x89.7 @ y=196.2 / 303.9 | same |

Still a solid navy card, not the suspected outlined PDF treatment. Consistent
with the run: collisions closed, cosmetic recipe open, and per the v8 note it
should **not** be restyled on assumption until the PDF treatment is measured.

### Net effect

Two of the eight prioritized items were false at measure time. Withdrawn: **R4**
(round 1) and **N9** (here). **R6-A shipped #139** after this baseline; remaining
open items are N6 align, N5 callout, F4+ pack, R6-C inset, R2 line elbow.

