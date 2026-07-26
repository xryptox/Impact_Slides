# Gap Analysis v5: renderer_v2 vs Amex Q1'26 Earnings PDF (AFTER v4 baseline)

**Simulation:** `simulation/amex_q1_2026/`
**Source of truth:** `C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf` (44 pages, 16:9)
**Renderer under test:** current `impact_slides.renderer_v2` in this worktree (post-v4; includes N4 dual label sets, N5 `exterior_segment_names` / `segmentNames` shell plugin, prior round-3 wires).
**Baseline (BEFORE / v4):**  
`C:/Users/Ag1Le/Documents/Impact_Slides-gnhf-worktrees/objective-produce-a-9c5007/simulation/amex_q1_2026/GAP_ANALYSIS.md`  
— v4 headline: F10+ and N1 RESOLVED; F11+/N2/N3 wires hold with visual polish residuals; R2 still weak; mean MAE ~89.15–89.19%.

**Method:** PyMuPDF rasters carried + verified (200 DPI) → vision-carried `extracted/slides.json` → ≤10 **handoff-only** comparison passes → Playwright 1920×1080 screenshots + side-by-side PDF/HTML MAE diffs.
**Hard constraint:** no production renderer/layout/CSS/schema/test edits; new files only under `simulation/amex_q1_2026/`.

**Passes run:** **3** (stopped early — all known pure-(A) levers for the v4 open list engaged; remaining divergences are type **(B)** capability / chrome residuals).

---

## Scoring caveats (read first)

| Caveat | Implication |
|--------|-------------|
| **Pixel MAE similarity is white-biased** | Mean ~89% is inflated by shared white canvas. Use as *relative trend* within this run and vs v4, **not** IR layout fidelity by itself. |
| **Ground truth is visual side-by-sides** | Judge structure from `passes/pass_XX/screenshots/compare_YY.png` and `diff.png`, not mean % alone. |
| **Type (A) vs (B)** | **(A)** = fixable by editing handoff JSON only. **(B)** = no handoff expression exists, or expression exists but is too weak to match the PDF recipe without renderer work. |
| **Chart path** | All three passes used the **Chart.js** path (`--self-contained`). |
| **Fresh verification** | Every v4 open/partial claim was re-tested on the **current** renderer with fresh DOM + screenshots. Status below is from **this** run, not inherited from v4 or PR titles. |
| **R3 brand-asset exclusion** | Centurion seal / third-party trademark art is **WONTFIX per CONTEXT.md**. Cover MAE is noted but **excluded from gap counts**, excluded from the delta table open list, and excluded from the future-feature list. Generic `seal_lockup` is the accepted by-design output. |
| **MAE vs structural story** | Best mean in this run is **pass_03 (89.38%)**. Funding MAE swung −2.45 pp (N5 engage under IR skin) then +3.38 pp (light cards). Structural closures (N3/N4 dual labels, N5 exterior names, N2 in-bar years) must be judged on side-by-sides + DOM, not mean alone. |

Evidence roots (relative to this folder):

- PDF rasters: `extracted/pdf_page_XX.png`
- Pass artifacts: `passes/pass_0N/{handoff.json,output/,screenshots/compare_XX.png,diff_scores.json,notes.md}`
- v4 BEFORE snapshot: absolute path above

---

## Per-pass summary table

| Pass | Chart path | Mean MAE sim. | Mean SSIM-approx | Top 3 divergences | Types | Δ vs prior / vs v4 p02 (89.15%) |
|-----:|------------|--------------:|-----------------:|-------------------|-------|----------------------------------|
| **01** | Chart.js (frozen v4 p02 handoff) | **89.36%** | 89.52% | (1) Platinum R2 callout / dual IR board — `compare_05.png` (73.91%); (2) Funding exterior segment labels unengaged — `compare_27.png` (77.88%); (3) Cover seal — `compare_00.png` (82.18%, **R3 excluded**) | **mixed** — N2 paint + N3/N4 dual sets **resolved under frozen handoff**; N5 **A available**; R2 **B** | vs v4 p02: **+0.21 pp** |
| **02** | Chart.js (A-engage N5 + $ stack tops + R2 text de-dupe) | **89.30%** (−0.06) | 89.46% | (1) Platinum R2 still weakest — `compare_05.png` (73.90%); (2) Funding N5 wire lands but denser packing MAE hit — `compare_27.png` (75.43%); (3) Cover R3 excluded — 82.18% flat | **B / partial-B / excluded** — N5 **wire holds**; packing residual | vs v4 p02: **+0.15 pp** |
| **03** | Chart.js (funding light cards; keep N5) | **89.38%** (+0.08) | 89.54% | (1) Platinum R2 geometry — `compare_05.png` (73.90%); (2) Funding packing residual after light reclaim — `compare_27.png` (78.81%); (3) Hero acq type scale — `compare_11.png` (83.00%) | **B / B / B** after A exhaust | vs v4 p02: **+0.23 pp**; **best mean this run** |

### Per-pass A closures vs B confirmations

| Pass | Meaningful (A) closures / observations | Confirmed / refined (B) |
|-----:|----------------------------------------|-------------------------|
| 01 | **Frozen v4 recipe on current renderer:** N2 year chips **paint inside** retention bars (v4 was wire-only / weak); N3/N4 **dual** in-segment `$` + stack tops + `negchip` paren path on provision; F10 90–100 + N1 table still hold; R1 MAE lift on slide 03 (+2.29 pp vs v4) | R2 callout chrome still ≠ PDF pill/chevron; N5 exterior names **not engaged** (cannot call B yet); F4+/R4/F12+ residuals; R3 cover excluded |
| 02 | **A engage N5:** `exterior_segment_names` → shell `segmentNames` items on funding; `$210/$219` + `$151/$157` tops via `stack_total_labels`; R2 elbow text cleared (no geometry change) | N5 packing / multi-line column still weak; Funding MAE −2.45 under IR+ N5 density; R2 still B |
| 03 | **A packing:** drop funding `tile_skin=ir` → light `gl-tile-tall`; N5 kept → slide 27 **+3.38 pp** to 78.81% | Funding exterior density still short of PDF; R2 unchanged; no remaining pure-A on checklist |

**Stop rationale after pass 03:** Pass_01 measured renderer walls under the frozen v4 engaged recipe. Pass_02–03 exhausted the post-v4 A-levers (N5 exterior names, explicit $ stack tops, light vs IR funding skin, R2 text micro-tune). Residual checklist items are chrome/geometry **(B)** — further handoff micro-tunes will not produce PDF pill-band/Refresh chevron geometry, freestanding multi-line exterior name columns at PDF density, or annex multi-level header precision. ≤10 budget preserved (**3 used**).

**Worst structural scores (pass_03 = decisive stop evidence):**

| Slide | PDF topic | p01 % | p02 % | p03 % | Primary gap after v5 |
|------:|-----------|------:|------:|------:|----------------------|
| 05 | U.S. Consumer Platinum | 73.91 | 73.90 | **73.90** | **R2** callout chrome (F10 domain closed; N2 years paint; IR heads hold) |
| 27 | Funding and Deposits | 77.88 | 75.43 | **78.81** | N5 packing residual (wire closed; light-card packing better than IR) |
| 00 | Cover | 82.18 | 82.18 | 82.18 | **R3 wontfix — excluded** (generic seal_lockup by design) |
| 11 | New Acquisitions | 83.00 | 83.00 | 83.00 | R4 hero type scale residual |
| 14 | Total Provision | 86.75 | 86.75 | 86.75 | N3/N4 path **closed family**; freestanding reserve-rate cells + exterior legend polish residual |

### Mean MAE vs v4 final

| Snapshot | Mean MAE sim. | Δ vs v4 pass_02 |
|----------|--------------:|----------------:|
| v4 pass_01 (frozen) | 89.19% | +0.04 pp (v4 internal vs its p02) |
| v4 pass_02 (A engage / BEFORE) | **89.15%** | — |
| **v5 pass_01** (frozen v4 p02 handoff) | **89.36%** | **+0.21 pp** |
| **v5 pass_02** (N5 engage) | **89.30%** | **+0.15 pp** |
| **v5 pass_03** (funding light + N5; stop) | **89.38%** | **+0.23 pp** |

**Read carefully:** mean MAE ticked up modestly vs v4 (+0.15–0.23 pp). Structural wins that pixel-MAE under-counts: **N2 in-bar year paint**, **N3/N4 dual label + negchip sets**, **N5 exterior segment-name wire**, **R1 stage MAE lift**. Funding still shows MAE blind-spots when chrome silhouettes change (IR+N5 −2.45, light+N5 reclaim +3.38). Treat the before/after delta table as the headline, not the mean column.

---

## Before / after delta: v4 open gaps → current renderer (v5)

**Headline deliverable.** Each required v4 ID re-tested on the **current** renderer with fresh pass evidence. Status is **not** inherited from PR titles or v4 conclusions.

| ID | v4 finding (summary + v4 slide/pass) | v5 status | v5 slide/pass evidence | Notes |
|----|--------------------------------------|-----------|------------------------|-------|
| **R2** IR geometric callout chrome (pill band + under-axis chevron) | Nodes painted; PDF blue pill arrow + navy Refresh chevron not matched. Slide **05**; v4 `pass_02/compare_05.png` | **still gap / weak** | pass_03 DOM: `chartjs-callout-band` + `elbow` + `chevron` present on slide 5. Visual `pass_03/screenshots/compare_05.png` (= p01/p02 family): floating / mid-plot teal capsule over bars + tiny under-axis Refresh pill ≠ PDF left elbow into spanning blue capsule + large bottom navy chevron | **Exists but weak.** Pass_02 elbow-text de-dupe was pure-A cosmetic (no geometry change). Stays open. |
| **N2 residual** IR-weight year chips inside bars | Wire OK (`bar_labels_inside=series` → year matrix); visual low-contrast / not IR-weight. Slide **05**; v4 `pass_02/compare_05.png` | **mostly resolved** (soft residual polish) | Frozen handoff on current renderer: `compare_05.png` right card shows **2025/2026 chips painted inside** each horizontal bar with correct series colors; DOM year triples present. Weight still slightly lighter than PDF bold chips | Path that was “wire + weak paint” in v4 **now paints the family**. Residual = weight/padding polish only → keep as optional weak polish, **not** a blocking recipe gap. Drops from P0. |
| **F11+ residual / N5** exterior segment labels + denser dual-card packing | F11 `tile_skin=ir` navy heads work; exterior multi-color segment name column missing; Funding packing residual. Slides **05/27**; v4 `pass_02/compare_27.png` | **partial** — N5 **wire resolved**; packing **still weak** | p02–p03: `exterior_segment_names: true` → `plugins.segmentNames.items` on funding boards; `compare_02/27.png` and `compare_03/27.png` show exterior colored names. p03 drops funding IR skin → light `gl-tile-tall` count 2, MAE **78.81%** (+0.94 vs v4 p02 funding). Chromium packing still denser / less multi-line than PDF right-column recipe; Platinum IR heads still hold (`gl-tile-ir`=2 on p03) | N5 was **missing entirely** in v4 open list framing; current renderer has first-class opt-in. Residual = packing density / multi-line column chrome (**exists but weak**). |
| **N3 residual / N4** dual stack labels + signed paren chips | `stack_totals` tops path works but **replaced** in-segment series `$` labels; signed paren chips weak. Slide **14**; v4 `pass_02/compare_14.png` | **mostly resolved** | pass_01+ frozen/engaged: provision HTML datalabels label sets `value` + `total` + `negchip`; in-segment `$1,223`… **and** tops `$1,150`… **and** `($73)`/`($24)` chips together. `compare_14.png` dual-label family; MAE **86.75%** (**+1.15 pp** vs v4 85.60) | N4 dual paint path **lands**. Residual = freestanding boxed reserve-rate row layout + right-side exterior series legend column vs PDF (**weak polish**, not missing dual-set capability). |
| **F4+** pill packing finish | Density MAE improved in v4; freestanding navy-header columns still short of PDF. Slides **02/19**; v4 p01 | **still gap / weak residual** | `gl-pill-free` present (2). Slide 19 **92.04%** (+0.61 vs v4); slide 02 **90.82%** (−1.59 vs v4 p02 — silhouette swing). Side-by-side still Boardroom strip vs three freestanding navy-header PDF columns (`compare_02.png` family) | **Exists but weak.** No new A packing knob closed the freestanding column recipe. |
| **R1** IR line-chart house / stage chrome | `chartjs-flat` engages; Boardroom pad residual. Slide **03**; v4 | **improved / weak residual** | `chartjs-flat`=8; slide 03 **92.74%** (**+2.29 pp** vs v4 90.45). Stage path stronger; residual Boardroom pad vs fully flat IR house remains in stricter side-by-sides | **Exists but weak** (improved). |
| **R4** hero dual % type scale | `chart_hero_dual` structure; type scale short. Slide **11**; v4 `compare_11.png` 82.95% | **still gap / weak residual** | `compare_11.png` **83.00%** (+0.05). Structure holds; giant narrated % / dual packing still short of PDF | **Exists but weak.** |
| **F12+** dense annex header precision | High white-table MAE; multi-level IR header stubs weak. Annex **28–36**; v4 | **still gap / weak residual** | Annex 28–36 mean MAE **~92.8%** (white-biased). Multi-level header IR stubs still weaker than PDF in side-by-sides | **Exists but weak.** |
| **R3** Centurion seal asset + placement | Cover seal gap. Slide **00**; v4 82.18% | **dropped: wontfix per CONTEXT.md brand-asset rule** | `compare_00.png` 82.18% flat — generic centered `seal_lockup` vs PDF Centurion watermark. **By design**; not a renderer gap | **Do not implement.** Handoff escape hatch for customer marks. Excluded from future-feature list and open gap counts. |

### Also closed / carried from earlier baselines (reconfirmed, not reopened)

| ID | Status | Evidence |
|----|--------|----------|
| **F10+** scale-root 90–100 domain | **resolved** (reconfirmed) | Platinum retention `scales` min 90 / max 100; `compare_05.png` high-90s window |
| **N1** secondary_visual under stacked_bar | **resolved** (reconfirmed) | Provision under-chart table + “Reserve Rate for Total Balances”; `compare_14.png` |
| **F3** signed negative stacks | **resolved** (reconfirmed) | Provision `($73)` / thin negative bars still paint |

### NEW residuals observed this run (optional numbering)

| ID | Finding | Slide / evidence | Type |
|----|---------|------------------|------|
| **N6** | Provision freestanding reserve-rate **boxed cell row** + right exterior series color legend (Write-offs / Reserve Build) still not PDF-layout-faithful even with N1 table + N4 labels | `pass_03/screenshots/compare_14.png` | **B weak** (layout furniture; values present) |
| **N7** | Funding / dual-stack **B unit suffix** on exterior names (`Card ABS*` / `Funding**`) and footnote block packing under multi_panel still denser / less IR-annex than PDF | `pass_03/screenshots/compare_27.png` | **B weak** / content |

*(No new missing chart family or layout_type was required beyond the v4 checklist plus N5 wire verification.)*

---

## Divergence catalog (compressed, v5)

| Div # | Theme | Primary IDs | v5 note |
|------:|-------|-------------|---------|
| D1 | Brand cover seal | R3 | **wontfix excluded** |
| D3 | Pill freestanding packing | F4+ | still weak |
| D4 | IR line stage chrome | R1 | improved, residual |
| D5 | Chart \| hero KPI dual | R4 | weak residual |
| D8 | Multi-panel / broken-axis boards | F10+, F11+, R2, N2, N5 | **F10+/N2 mostly closed**; F11 skin + N5 wire; R2/N5 pack residual |
| D9 | Dense annex tables | F12+ | weak residual |
| D13 | Revenue line + under-table | N1 | gate closed |
| D15 | Under-chart secondary on stacked_bar | N1 | closed |
| D16 | Stacked dual labels + signed paren | N3/N4 | **mostly resolved** |
| D17 | Exterior segment name column | N5 | **wire resolved**; packing weak |
| D18 | Horizontal anniversary domain | F10+ | closed |

---

## Prioritized future-feature list (still open AFTER this run)

Only items that remain open on fresh evidence. **Resolved v4 items and R3 wontfix are omitted.** Each cites PDF slide + pass screenshot.

| Pri | Feature | What it enables | Motivating evidence | Missing vs weak |
|----:|---------|-----------------|---------------------|-----------------|
| **P0** | **R2 — true IR callout chrome recipe** | PDF-faithful spanning blue pill arrow over bar tops + large under-axis navy Refresh chevron (category-anchored geometry, not floating band + tiny pill) | PDF p6 / slide **05**; `passes/pass_03/screenshots/compare_05.png` (73.90%; band+elbow+chevron DOM present but wrong geometry) | **Exists but weak** (overlay types exist; recipe/geometry wrong) |
| **P1** | **N5 residual / F11 packing — exterior segment-name column density** | Multi-line right-of-plot exterior segment names at IR density on 100%-stacked dual cards; light-card multi_panel packing parity with PDF rounded boards | PDF p28 / slide **27**; `passes/pass_03/screenshots/compare_27.png` (78.81%; `segmentNames` paints but packing short) | **Exists but weak** (first-class `exterior_segment_names` wire holds) |
| **P1** | **F4+ — freestanding pill-column packing finish** | Three navy-header freestanding statement columns (not joined Boardroom strip) | PDF p3 / slide **02**; `passes/pass_01/screenshots/compare_02.png` family; p03 MAE 90.82% | **Exists but weak** (`gl-pill-free` path) |
| **P2** | **N6 — provision furniture polish** (optional name) | Freestanding reserve-rate boxed cells + right exterior series legend matching PDF Total Provision furniture (values already correct via N1/N4) | PDF p15 / slide **14**; `passes/pass_03/screenshots/compare_14.png` (86.75%) | **Exists but weak** |
| **P2** | **N2 weight polish** (optional) | Bolder IR-weight year-in-bar chips (family already paints) | PDF p6 / slide **05**; `compare_05.png` right card | **Exists but weak** |
| **P3** | **R1 — IR flat stage / line-house residual** | Fully flat IR stage field vs residual Boardroom pad on line boards | PDF line slides e.g. slide **03**; `compare_03.png`; MAE improved to 92.74% but residual remains | **Exists but weak** (improved this run) |
| **P3** | **R4 — hero dual % type scale** | Giant narrated % stack scale + dual narrative packing on acquisitions boards | PDF p12 / slide **11**; `passes/pass_03/screenshots/compare_11.png` (83.00%) | **Exists but weak** |
| **P3** | **F12+ — annex multi-level header precision** | Dense IR table header stubs / multi-level columns in appendix | Annex slides **28–36**; high white MAE ~92.8% masking header weakness in side-by-sides | **Exists but weak** |

### Dropped since v4 (do not re-implement as open gaps)

| ID | Why dropped |
|----|-------------|
| F10+ | Resolved pre-v5; reconfirmed |
| N1 gate | Resolved pre-v5; reconfirmed |
| N3/N4 dual-set **capability** | Mostly resolved on current renderer (N4 label sets + negchip); only furniture polish remains (N6) |
| N2 **series wire / paint family** | Mostly resolved (years inside bars); only weight polish remains |
| N5 **missing wire** | Wire now exists; residual packing only (kept above as N5 residual) |
| **R3** Centurion seal | **Wontfix** — CONTEXT.md brand-asset rule; not a gap |

### Recommended implementation order (future renderer track — not this sim)

1. **R2** true pill-band + Refresh chevron geometry — finishes Platinum left recipe (still worst structural board).
2. **N5 residual packing** — multi-line exterior column density + dual-card light packing (Funding).
3. **F4+** freestanding pill packing finish.
4. **N6** provision furniture polish (reserve cells + exterior series legend).
5. **R1 / R4 / F12+ / N2 weight** polish bucket.

---

## What renderer_v2 already does well

Credited on fresh pass evidence (pass_01–03), not cargo-culted:

- **44-slide self-contained Chart.js deck** with Boardroom tokens, stable 1:1 page map, and usable MAE ~89.4% mean under white-canvas scoring.
- **F10+ anniversary window** — scale-root `min/max` 90–100 on horizontal retention bars (slide 05).
- **N1 under-chart tables** — `secondary_visual` data_table paints under stacked_bar (slide 14 reserve-rate row).
- **N2 series-in-bar labels** — `bar_labels_inside: "series"` paints year chips inside horizontal bars (slide 05 right).
- **N3/N4 dual stack labeling** — simultaneous in-segment values, category `$` tops, and signed paren `negchip`s (slide 14).
- **N5 exterior segment names** — opt-in `exterior_segment_names` + shell `segmentNames` plugin draws colored names right of 100% stacks (slide 27).
- **F11 IR navy dual-card heads** — `tile_skin: "ir"` with `top_total` KPI heads (Platinum); light tall cards available when IR is omitted (Funding p03).
- **F3 signed negative stacks** — reserve release bars below axis still correct.
- **R1 flat stage path** — measurable MAE lift on several line boards vs v4 (slide 03 +2.29 pp).
- **Pill comparison + annex tables + section/cover load paths** — structural families present; brand cover load path clean with accepted generic seal.

---

## Pass methodology (audit trail)

| Step | Location |
|------|----------|
| PDF rasters (primitive PyMuPDF only; carried from v4 sim + verified) | `extracted/pdf_page_00.png` … `pdf_page_43.png` |
| Vision transcription (carried + verified) | `extracted/slides.json` |
| Pass 01 AFTER v4 / frozen v4 p02 handoff (renderer walls) | `passes/pass_01/` |
| Pass 02 A-engage N5 + $ stack_total_labels + R2 text de-dupe | `passes/pass_02/` |
| Pass 03 funding light cards (drop IR skin; keep N5) | `passes/pass_03/` |
| v4 BEFORE snapshot | baseline worktree `GAP_ANALYSIS.md` (absolute path in header) |
| This document | `GAP_ANALYSIS.md` |

**Hard constraints honored:**

- ≤10 comparison passes (**3 used**)
- New files only under `simulation/amex_q1_2026/`
- No production `impact_slides/` renderer, layout, CSS, schema, or test edits
- Every remaining **(B)** claim cites a concrete PDF slide index and `pass_XX/screenshots/compare_YY.png`
- Features listed are **observed gaps**, re-verified on the current renderer
- **R3 excluded** everywhere as wontfix / by-design
- Resolved or mostly-resolved items dropped or demoted on the future list; wire-closed-but-weak items stay with updated labels

---

## Conclusion

The **v5 AFTER** picture versus v4 (`objective-produce-a-9c5007`) is a **measured** win on **label/paint paths**, not a blank mean-MAE leap:

| Resolved / mostly resolved under fresh evidence | Wire landed, packing residual | Still open / weak (excl. R3) |
|-------------------------------------------------|-------------------------------|------------------------------|
| **N2** in-bar year paint family | **N5** exterior segment names | **R2** callout chrome |
| **N3/N4** dual stack labels + negchips | **F11** light vs IR dual-card packing | **F4+** pill packing finish |
| **F10+ / N1 / F3** reconfirmed closed | | **R1 / R4 / F12+** polish |
| **R1** stage MAE improved | | **N6** provision furniture polish |

Mean MAE best **89.38%** vs v4 stop **89.15%** (**+0.23 pp**). White-canvas MAE again under-reports structural closures (N2 paint, N4 dual sets, N5 wire) and over-penalizes chrome-silhouette experiments (Funding N5 packing swings).

What still blocks **end-to-end visual replication** of this Amex PDF is now a **shorter chrome/recipe list** headed by **R2 callout geometry**, then exterior-column packing (**N5 residual**), freestanding pill columns (**F4+**), and polish (R1/R4/F12+/N6). **R3 Centurion art is not on that list** — it is a permanent brand-asset wontfix.

After three handoff-only passes, remaining divergences are **capability/chrome gaps (B)**. This document is the deliverable; closing the open list requires a separate renderer implementation track outside this simulation (Phase B).
