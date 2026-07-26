# Gap Analysis v6: renderer_v2 vs Amex Q1'26 Earnings PDF (AFTER v5 baseline)

**Simulation:** `simulation/amex_q1_2026/`
**Source of truth:** `C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf` (44 pages, 16:9)
**Renderer under test:** current `impact_slides.renderer_v2` in this worktree (**post-PR #114**: board vertical fill `.gl-main` flex on board/chart layouts; R2 band+elbow canonical merge; N2 in-bar year chips 14px; F4+ 17px navy pill cells).
**Baseline (BEFORE / v5):** `wiki/baseline_v5_GAP_ANALYSIS.md`
— v5 headline: N2 + N3/N4 mostly resolved; N5 wire resolved (packing weak); R1 improved; **R2 still P0**; mean MAE **89.38%** final (pass_03). Companion full artifacts: `origin/gnhf/objective-produce-a-11b7c0` under `simulation/amex_q1_2026/`.

**Method:** Fresh PyMuPDF 200 DPI rasters → vision-carried `extracted/slides.json` → ≤10 **handoff-only** comparison passes → Playwright 1920×1080 screenshots + side-by-side PDF/HTML MAE diffs.
**Hard constraint:** no production renderer/layout/CSS/schema/test edits; new files only under `simulation/amex_q1_2026/`.

**Passes run:** **2** (stopped early — pure-(A) levers for the v5 open list exhausted; remaining divergences are type **(B)** capability / chrome residuals).

---

## Scoring caveats (read first)

| Caveat | Implication |
|--------|-------------|
| **Pixel MAE similarity is white-biased** | Mean ~89% is inflated by shared white canvas. Use as *relative trend* within this run and vs v5, **not** IR layout fidelity by itself. |
| **Ground truth is visual side-by-sides** | Judge structure from `passes/pass_XX/screenshots/compare_YY.png` and `diff.png`, not mean % alone. |
| **Type (A) vs (B)** | **(A)** = fixable by editing handoff JSON only. **(B)** = no handoff expression exists, or expression exists but is too weak to match the PDF recipe without renderer work. |
| **Chart path** | Both passes used the **Chart.js** path (`--self-contained`). |
| **Fresh verification** | Every v5 open/partial claim was re-tested on the **current** renderer with fresh DOM + screenshots. Status below is from **this** run, not inherited from v5 or PR titles. |
| **R3 brand-asset exclusion** | Centurion seal / third-party trademark art is **WONTFIX per CONTEXT.md**. Cover MAE is noted but **excluded from gap counts**, excluded from the delta table open list, and excluded from the future-feature list. Generic `seal_lockup` is the accepted by-design output. |
| **MAE vs structural story** | Best mean this run is **pass_02 (89.31%)**. Post-#114 board fill lifted slide **05** (+2.00 pp vs v5) and slide **11** (+2.67 pp) under a frozen handoff, but **R2 geometry is still wrong**. Mean −0.07 pp vs v5 final is white-canvas noise — trust `compare_XX.png`. |

Evidence roots (relative to this folder):

- PDF rasters: `extracted/pdf_page_XX.png`
- Pass artifacts: `passes/pass_0N/{handoff.json,output/,screenshots/compare_XX.png,diff_scores.json,notes.md}`
- v5 BEFORE snapshot: `wiki/baseline_v5_GAP_ANALYSIS.md`

---

## Per-pass summary table

| Pass | Chart path | Mean MAE sim. | Mean SSIM-approx | Top 3 divergences | Types | Δ vs prior / vs v5 p03 (89.38%) |
|-----:|------------|--------------:|-----------------:|-------------------|-------|----------------------------------|
| **01** | Chart.js (frozen v5 p03 handoff on post-#114 renderer) | **89.29%** | 89.48% | (1) Platinum R2 geometry — `compare_05.png` (**75.90%**); (2) Funding N5 packing — `compare_27.png` (78.60%); (3) Cover seal — `compare_00.png` (82.18%, **R3 excluded**) | **mixed** — board-fill MAE lift on 05/11; R2 still **B**; checklist re-tested fresh | vs v5 p03: **−0.09 pp** mean |
| **02** | Chart.js (A: R2 elbow-only declare; provision `exterior_segment_names`; funding skin hard-clear) | **89.31%** (+0.02) | 89.50% | (1) Platinum R2 geometry unchanged — `compare_05.png` (**75.90%**); (2) Funding packing residual — `compare_27.png` (78.60%); (3) Hero acq type scale — `compare_11.png` (85.67%) | **B / B / B** after A exhaust; provision +0.76 pp from exterior names (not N6 furniture) | vs v5 p03: **−0.07 pp** mean; **best mean this run** |

### Per-pass A closures vs B confirmations

| Pass | Meaningful (A) closures / observations | Confirmed / refined (B) |
|-----:|----------------------------------------|-------------------------|
| 01 | **Frozen v5 recipe on CURRENT renderer (post-#114):** dual boards visibly taller on 05/11/14/27; R2 band+elbow abstraction absorbs co-declared band (no double smear); N2 14px chips + F4+ 17px navy cells paint; N3/N4 dual + N5 exterior wire hold | R2 geometry still mid-plot capsule + axis-scale Refresh ≠ PDF L-elbow pill + large bottom chevron; N5 packing / F4+ / N6 / R4 / R1 / F12+ residuals; R3 cover excluded |
| 02 | **R2 pure-A:** declare **elbow_arrow alone** (drop band) — clean single elbow+stem+chevron DOM; **zero** visual geometry change → geometry is **B**. **N6 A-scrape:** `exterior_segment_names` on provision → `segmentNames` count 6; MAE **+0.76 pp** to 86.07% but labels ≠ freestanding boxed reserve cells / exterior legend furniture | R2 still B; N5 packing flat; F4+/R4 no A knobs; no remaining pure-A on checklist |

**Stop rationale after pass 02:** Pass_01 measured the post-#114 renderer walls under the v5 stop recipe. Pass_02 exhausted the remaining pure-A levers named in pass_01 (elbow-only R2, provision exterior names, funding skin clear). Further handoff micro-tunes will not produce PDF pill-arrow / large Refresh geometry, multi-line exterior name density, freestanding pill-column packing, or annex multi-level header precision. ≤10 budget preserved (**2 used**).

### Worst structural scores (pass_02 = decisive stop evidence)

| Slide | PDF topic | p01 % | p02 % | Primary gap after v6 |
|------:|-----------|------:|------:|----------------------|
| 05 | U.S. Consumer Platinum | 75.90 | **75.90** | **R2** callout chrome (boards taller; N2 years paint; IR heads hold; merge clean) |
| 27 | Funding and Deposits | 78.60 | **78.60** | N5 packing residual (wire closed; light cards) |
| 00 | Cover | 82.18 | 82.18 | **R3 wontfix — excluded** (generic seal_lockup) |
| 12 | (structural sibling) | 83.35 | 83.35 | residual house chrome (not primary checklist ID) |
| 11 | New Acquisitions | 85.67 | **85.67** | R4 hero type scale (boards taller vs v5; type still weak) |
| 14 | Total Provision | 85.31 | **86.07** | N6 furniture residual (N3/N4 dual family closed; exterior names A-landed) |

### Mean MAE vs v5 final

| Snapshot | Mean MAE sim. | Δ vs v5 pass_03 |
|----------|--------------:|----------------:|
| v5 pass_01 (frozen v4 handoff) | 89.36% | −0.02 pp (v5 internal) |
| v5 pass_03 (funding light + N5; BEFORE) | **89.38%** | — |
| **v6 pass_01** (frozen v5 p03 handoff, post-#114) | **89.29%** | **−0.09 pp** |
| **v6 pass_02** (A elbows-only + provision exterior; stop) | **89.31%** | **−0.07 pp** |

**Read carefully:** mean MAE is flat/noisy vs v5. Structural story that pixel-MAE under- and over-counts:
- **Board vertical fill (#114):** slide 05 **+2.00 pp** (75.90 vs v5 73.90) and slide 11 **+2.67 pp** (85.67 vs 83.00) under an **identical frozen handoff** — taller boards, not R2/R4 recipe closure.
- **R2 geometry unchanged** at the pixel-structure level (capsule still mid-plot; chevron still axis-scale).
- **Provision exterior names** +0.76 pp without delivering N6 furniture.

Treat the before/after delta table as the headline, not the mean column.

---

## Before / after delta: v5 open gaps → current renderer (v6)

**Headline deliverable.** Each required v5 ID re-tested on the **current** renderer with fresh pass evidence. Status is **not** inherited from PR titles or v5 conclusions.

| ID | v5 finding (summary + v5 slide/pass) | v6 status | v6 slide/pass evidence | Notes |
|----|--------------------------------------|-----------|------------------------|-------|
| **R2** IR geometric callout chrome (spanning blue pill arrow + large navy Refresh chevron) | Nodes painted; geometry wrong. Slide **05**; v5 `pass_03/compare_05.png` (73.90%) | **still-gap / weak** | p01–p02 DOM: `chartjs-callout-elbow` spanning `left:0 width:100 top:8.33%` + stem + `chartjs-callout-chevron` at Q1'26. p02 drops band co-declare → **clean absorption path** (single elbow, no smear). Visual `pass_02/screenshots/compare_05.png` (75.90%): floating mid-plot teal capsule over bar tops + small under-axis Refresh pill ≠ PDF left L-elbow into spanning blue capsule + **large bottom-center navy Refresh chevron** | **Exists but weak.** Board-fill MAE lift is real; **recipe/geometry still wrong**. Pure-A exhausted (elbow-only = band+elbow visually). Stays **P0**. |
| **N5 residual / F11 packing** multi-line exterior segment-name column density | Wire resolved; packing weak. Slide **27**; v5 `pass_03/compare_27.png` (78.81%) | **partial — wire holds; packing still weak** | p01–p02: funding light cards + `exterior_segment_names` → `segmentNames` on both boards; `compare_27.png` **78.60%** (−0.21 vs v5). Exterior colored names present; denser / less multi-line than PDF right column; FDIC not exterior-column furniture | **Exists but weak.** No new packing A lever after light-card recipe. |
| **F4+** freestanding pill packing | `gl-pill-free` path; packing residual. Slides **02/19**; v5 p03 90.82 / 92.04 | **still-gap / weak** | `gl-pill-free` present (3). Slide 02 **90.56%**, 19 **91.86%**. `compare_02.png`: exterior label rail + three navy-header shells exist (PR #114 17px navy cells) but packing / column separation still short of PDF freestanding statement columns | **Exists but weak.** No handoff density knob closed the recipe. |
| **N6** provision furniture (reserve-rate boxed cells + exterior series legend) | Values OK via N1/N4; furniture weak. Slide **14**; v5 `compare_14.png` 86.75% | **still-gap / weak** | p02 A: `exterior_segment_names` → Write-offs / Reserve Build as `segmentNames` (deck count 6). MAE **86.07%** (+0.76 vs p01; −0.68 vs v5 — silhouette). `compare_14.png`: series names near stacks, reserve-rate still under-chart sheet row — **not** freestanding bordered cells + right legend column | **Exists but weak** (wire reuse ≠ furniture). Dual-label N3/N4 family still closed. |
| **N2 weight polish** bolder year chips | Mostly resolved; soft polish. Slide **05**; v5 | **mostly resolved** (+ soft polish) | Right card year chips **2025/2026 inside bars** with series colors; 14px path engaged (`compare_05.png`). Slightly lighter/smaller than PDF bold chips | Family paints; residual = weight only → optional polish, not blocking. |
| **R1** flat stage residual | Improved; Boardroom pad residual. Slide **03**; v5 92.74% | **improved / weak residual** | `chartjs-flat` count 9; s03 **92.62%** holds v5 lift region. Stricter side-by-sides still show residual pad vs fully flat IR house | **Exists but weak** (improved retained). |
| **R4** hero % type scale | Structure holds; type scale short. Slide **11**; v5 83.00% | **partial improve / still weak** | s11 **85.67%** (**+2.67 pp** vs v5) from **board fill**, not type scale. `compare_11.png`: giant 66%/73% still under-scale vs PDF dual stack; right column packing still short | **Exists but weak.** MAE lift ≠ R4 closure. |
| **F12+** annex multi-level header precision | High white MAE; header stubs weak. Annex **28–36**; v5 | **weak residual** | Annex white-MAE still ~91–95% (e.g. 28 **95.73%**). Side-by-side multi-level header precision residual carries; not re-tuned (no A header chrome) | **Exists but weak.** |
| **R3** Centurion seal | Cover gap | **dropped: wontfix per CONTEXT.md brand-asset rule** | `compare_00.png` 82.18% flat — generic `seal_lockup`. **By design**; not a renderer gap | Excluded from gap counts, delta-open list, and future-feature list (recorded once here as dropped). |

### Also closed / carried from earlier baselines (reconfirmed, not reopened)

| ID | Status | Evidence |
|----|--------|----------|
| **F10+** scale-root 90–100 domain | **resolved** (reconfirmed) | Platinum retention high-90s window; `compare_05.png` |
| **N1** secondary_visual under stacked_bar | **resolved** (reconfirmed) | Provision under-chart reserve-rate row; `compare_14.png` |
| **F3** signed negative stacks | **resolved** (reconfirmed) | Provision `($73)` / thin negative bars still paint |
| **N3/N4** dual stack labels + negchips | **mostly resolved** (reconfirmed) | in-segment `$` + tops + paren chips together; `compare_14.png` |
| **N5 wire** (not packing) | **resolved** (reconfirmed) | `exterior_segment_names` → shell plugin on funding; p02 also on provision |
| **#114 board vertical fill** | **lands** (new since v5) | Taller dual boards on 05/11; MAE lift under frozen handoff |

### NEW residuals observed this run

| ID | Finding | Slide / evidence | Type |
|----|---------|------------------|------|
| *(none blocking)* | No new missing chart family or layout_type beyond the v5 checklist. p02 confirmed exterior-name wire generalizes to provision stacked bars without delivering N6 furniture — reinforces N6 as furniture/chrome, not missing plugin. | `pass_02/screenshots/compare_14.png` | refines **N6** B-weak |

*(N7 footnote/unit-suffix density from v5 not re-litigated; still absorbed under N5 packing residual on slide 27.)*

---

## Divergence catalog (compressed, v6)

| Div # | Theme | Primary IDs | v6 note |
|------:|-------|-------------|---------|
| D1 | Brand cover seal | R3 | **wontfix excluded** |
| D3 | Pill freestanding packing | F4+ | still weak |
| D4 | IR line stage chrome | R1 | improved retained, residual |
| D5 | Chart \| hero KPI dual | R4 | MAE up from board fill; type scale still weak |
| D8 | Multi-panel / broken-axis boards | F10+, F11+, R2, N2, N5 | **F10+/N2 mostly closed**; F11 skin + N5 wire; **R2/N5 pack residual**; boards taller |
| D9 | Dense annex tables | F12+ | weak residual |
| D13/D15 | Under-chart secondary | N1 | closed |
| D16 | Stacked dual labels + signed paren | N3/N4 | **mostly resolved** |
| D17 | Exterior segment name column | N5 | **wire resolved**; packing weak |
| D18 | Horizontal anniversary domain | F10+ | closed |
| D19 | Provision furniture | N6 | still weak (exterior names ≠ boxes+legend) |

---

## Prioritized future-feature list (still open AFTER this run)

Only items that remain open on fresh evidence. **Resolved / mostly-resolved family locks and R3 wontfix are omitted.** Each cites PDF slide + pass screenshot.

| Pri | Feature | What it enables | Motivating evidence | Missing vs weak |
|----:|---------|-----------------|---------------------|-----------------|
| **P0** | **R2 — true IR callout chrome recipe** | PDF-faithful spanning blue pill arrow over bar tops with left stem, plus **large** under-axis navy Refresh chevron (category-anchored geometry; not mid-plot capsule + axis-scale chip) | PDF p6 / slide **05**; `passes/pass_02/screenshots/compare_05.png` (75.90%; elbow+stem+chevron DOM present, geometry wrong; elbow-only A-confirm) | **Exists but weak** (overlay types + merge + stem exist; recipe/geometry wrong) |
| **P1** | **N5 residual / F11 packing — exterior segment-name column density** | Multi-line right-of-plot exterior segment names at IR density on 100%-stacked dual cards; light multi_panel packing parity with PDF rounded boards | PDF p28 / slide **27**; `passes/pass_02/screenshots/compare_27.png` (78.60%; `segmentNames` paints; packing short) | **Exists but weak** (first-class `exterior_segment_names` wire holds) |
| **P1** | **F4+ — freestanding pill-column packing finish** | Three navy-header freestanding statement columns at PDF density (not residual Boardroom spacing) | PDF p3 / slide **02**; `passes/pass_02/screenshots/compare_02.png` (90.56%); typography 17px navy engaged | **Exists but weak** (`gl-pill-free` path) |
| **P2** | **N6 — provision furniture polish** | Freestanding reserve-rate **boxed cells** + right exterior series legend matching PDF Total Provision furniture (values already correct via N1/N4; exterior names alone insufficient) | PDF p15 / slide **14**; `passes/pass_02/screenshots/compare_14.png` (86.07%) | **Exists but weak** |
| **P2** | **N2 weight polish** (optional) | Bolder IR-weight year-in-bar chips (family already paints at 14px) | PDF p6 / slide **05**; `compare_05.png` right card | **Exists but weak** |
| **P3** | **R1 — IR flat stage / line-house residual** | Fully flat IR stage field vs residual Boardroom pad on line boards | PDF line slides e.g. slide **03**; `compare_03.png`; MAE 92.62% | **Exists but weak** (improved retained) |
| **P3** | **R4 — hero dual % type scale** | Giant narrated % stack scale + dual narrative packing on acquisitions boards (board fill alone is not enough) | PDF p12 / slide **11**; `passes/pass_02/screenshots/compare_11.png` (85.67%) | **Exists but weak** |
| **P3** | **F12+ — annex multi-level header precision** | Dense IR table header stubs / multi-level columns in appendix | Annex slides **28–36**; high white MAE masking header weakness in side-by-sides | **Exists but weak** |

### Dropped since v5 (do not re-implement as open gaps)

| ID | Why dropped |
|----|-------------|
| F10+ | Resolved pre-v5; reconfirmed |
| N1 gate | Resolved pre-v5; reconfirmed |
| N3/N4 dual-set **capability** | Mostly resolved; only furniture polish remains (N6) |
| N2 **series wire / paint family** | Mostly resolved; only weight polish remains |
| N5 **missing wire** | Wire exists; residual packing only (kept above) |
| **R3** Centurion seal | **Wontfix** — CONTEXT.md brand-asset rule; not a gap |
| **#114 board vertical fill** | Lands on current renderer (taller boards on 05/11); not a gap |

### Recommended implementation order (future renderer track — not this sim)

1. **R2** true pill-arrow + large Refresh chevron geometry — finishes Platinum left recipe (still worst structural board).
2. **N5 residual packing** — multi-line exterior column density + dual-card light packing (Funding).
3. **F4+** freestanding pill packing finish.
4. **N6** provision furniture polish (boxed reserve cells + exterior series legend — not just segmentNames).
5. **R1 / R4 / F12+ / N2 weight** polish bucket.

---

## What renderer_v2 already does well

Credited on fresh pass evidence (pass_01–02), not cargo-culted:

- **44-slide self-contained Chart.js deck** with Boardroom tokens, stable 1:1 page map, usable MAE ~89.3% mean under white-canvas scoring.
- **#114 board vertical fill** — dual IR / light boards grow into the stage (slides 05/11 MAE lift under frozen handoff).
- **F10+ anniversary window** — scale-root 90–100 on horizontal retention bars (slide 05).
- **N1 under-chart tables** — `secondary_visual` data_table under stacked_bar (slide 14).
- **N2 series-in-bar labels** — year chips inside horizontal bars (slide 05 right; 14px path).
- **N3/N4 dual stack labeling** — in-segment values + category tops + signed paren `negchip`s (slide 14).
- **N5 exterior segment names** — opt-in wire draws colored names right of 100% stacks (slide 27; also generalizes to provision in p02).
- **R2 overlay types + band→elbow merge + stem** — DOM declares cleanly; geometry residual is recipe strength, not missing nodes.
- **F11 IR navy dual-card heads** + light tall cards when IR omitted (Platinum vs Funding).
- **F3 signed negative stacks** — reserve release bars below axis still correct.
- **R1 flat stage path** — holds v5 MAE region on line boards (slide 03 ~92.6%).
- **F4+ freestanding pill path** — exterior label rail + navy header shells + 17px navy cells (slide 02 structure present).
- **Pill / annex / section / cover load paths** — structural families present; cover generic seal accepted by design.

---

## Pass methodology (audit trail)

| Step | Location |
|------|----------|
| PDF rasters (primitive PyMuPDF 200 DPI, fresh this run) | `extracted/pdf_page_00.png` … `pdf_page_43.png` |
| Vision transcription (carried from v5 archive + shape-verified 44 slides) | `extracted/slides.json` |
| Pass 01 AFTER-#114 / frozen v5 p03 handoff (renderer walls) | `passes/pass_01/` |
| Pass 02 A: R2 elbow-only + provision exterior_segment_names + funding skin clear | `passes/pass_02/` |
| v5 BEFORE snapshot | `wiki/baseline_v5_GAP_ANALYSIS.md` |
| This document | `GAP_ANALYSIS.md` |

**Hard constraints honored:**

- ≤10 comparison passes (**2 used**)
- New files only under `simulation/amex_q1_2026/`
- No production `impact_slides/` renderer, layout, CSS, schema, or test edits
- Every remaining **(B)** claim cites a concrete PDF slide index and `pass_XX/screenshots/compare_YY.png`
- Features listed are **observed gaps**, re-verified on the current renderer
- **R3 excluded** everywhere as wontfix / by-design
- Resolved or mostly-resolved items dropped or demoted on the future list; wire-closed-but-weak items stay with updated labels
- Deliverable is **analysis only** — no renderer fixes in this run

---

## Conclusion

The **v6 AFTER** picture versus v5 is a **measured confirmation** that post-#114 renderer work **helps board stage geometry** without closing the P0 callout recipe:

| Lands / mostly resolved under fresh evidence | Wire landed, packing residual | Still open / weak (excl. R3) |
|----------------------------------------------|-------------------------------|------------------------------|
| **#114** taller boards (05/11 MAE lift) | **N5** exterior names (packing residual) | **R2** callout chrome (**still P0**) |
| **N2** in-bar years (weight polish only) | **F11** light vs IR packing | **F4+** pill packing finish |
| **N3/N4** dual labels + negchips | | **N6** provision furniture |
| **F10+ / N1 / F3** reconfirmed closed | | **R1 / R4 / F12+** polish |
| **R1** stage MAE region held | | |
| **R2 merge** clean elbow-only path | | geometry recipe still wrong |

**Mean MAE 89.31%** (−0.07 pp vs v5 final) is white-canvas noise. Headline for Phase B: **R2 remains the only P0**; packing furniture (N5/F4+/N6) is the P1–P2 band; type/stage polish is P3.
