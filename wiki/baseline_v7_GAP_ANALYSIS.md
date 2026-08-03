# Gap Analysis v7: renderer_v2 vs Amex Q1'26 Earnings PDF (AFTER v6 baseline + round-4 T1/T2)

> **Superseded - historical. Point-in-time gap analysis; see `baseline_v8_GAP_ANALYSIS.md` for the latest baseline.**

**Simulation:** `simulation/amex_q1_2026/`
**Source of truth:** `C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf` (44 pages, 16:9)
**Renderer under test:** current `impact_slides.renderer_v2` in this worktree (**post-PR #115 T1 calloutGeometry + #116 T2 exterior-name knobs**).
**Baseline (BEFORE / v6):** `wiki/baseline_v6_GAP_ANALYSIS.md` — v6 headline: #114 board-fill lift on 05/11; **R2 geometry still wrong** (mid-plot %), N5 packing weak, mean MAE **89.31%** final (pass_02). Companion full artifacts: `origin/gnhf/objective-produce-a-03e1d0` under `simulation/amex_q1_2026/`.
**Method:** Fresh PyMuPDF 200 DPI rasters → vision-carried `extracted/slides.json` → ≤10 **handoff-only** comparison passes → Playwright 1920×1080 screenshots + side-by-side PDF/HTML MAE diffs.
**Hard constraint:** no production renderer/layout/CSS/schema/test edits; new files only under `simulation/amex_q1_2026/`.
**Passes run:** **2** (stopped early — pure-(A) levers for the v7 open checklist exhausted; remaining divergences are type **(B)** capability / chrome residuals).

---

## Scoring caveats (read first)

| Caveat | Implication |
|--------|-------------|
| **Pixel MAE similarity is white-biased** | Mean ~89% is inflated by shared white canvas. Use as *relative trend* within this run and vs v6, **not** IR layout fidelity by itself. |
| **Ground truth is visual side-by-sides** | Judge structure from `passes/pass_XX/screenshots/compare_YY.png` and `diff.png`, not mean % alone. |
| **Type (A) vs (B)** | **(A)** = fixable by editing handoff JSON only. **(B)** = no handoff expression exists, or expression exists but is too weak to match the PDF recipe without renderer work. |
| **Chart path** | Both passes used the **Chart.js** path (`--self-contained`). |
| **Fresh verification** | Every required checklist ID was re-tested on the **current** renderer with fresh DOM + screenshots. Status below is from **this** run, not inherited from v6 or PR titles. T1/T2 are treated as **verify**, not rediscovery. |
| **R3 brand-asset exclusion** | Centurion seal / third-party trademark art is **WONTFIX per CONTEXT.md**. Cover MAE is noted but **excluded from gap counts**, excluded from the delta table open list, and excluded from the future-feature list. Generic `seal_lockup` is the accepted by-design output. |
| **Accepted divergence lock (r4 SPEC D11)** | **R1**, **F12+**, and **N2 chip weight** are **CLOSED — accepted divergence**. Fixed once (#113/#114), returned exists-but-weak inside white-MAE noise; heavier N2 chips would look wrong on non-Amex decks. Recorded once as closed; **not** open gaps, **not** in future-feature list or recommended order. Slide MAE may be noted without inflating rankings. |
| **MAE vs structural story** | Best mean this run is **pass_02 (89.49%)** (+0.18 pp vs v6 final 89.31%). T1 exact geometry holds under live `calloutGeometry` but only moved Platinum MAE **+0.87 pp** — remaining R2 gap is chrome recipe, not coordinate math. T2 knobs serialize; the big N5 lift was an **(A) double-legend purge**, not packing density. Trust `compare_XX.png`. |

Evidence roots (relative to this folder):

- PDF rasters: `extracted/pdf_page_XX.png`
- Pass artifacts: `passes/pass_0N/{handoff.json,output/,screenshots/compare_XX.png,diff_scores.json,notes.md,slide05_geometry.json}`
- v6 BEFORE snapshot: `wiki/baseline_v6_GAP_ANALYSIS.md`

---

## Per-pass summary table

| Pass | Chart path | Mean MAE sim. | Mean SSIM-approx | Top 3 divergences | Types | Δ vs prior / vs v6 p02 (89.31%) |
|-----:|------------|--------------:|-----------------:|-------------------|-------|----------------------------------|
| **01** | Chart.js (v6 p02 handoff + T2 knobs on 14/27; R2 elbow frozen for T1) | **89.33%** | 89.52% | (1) Platinum R2 chrome after T1 — `compare_05.png` (**76.77%**, +0.87 vs v6); (2) Funding N5 packing — `compare_27.png` (78.65%); (3) Cover seal — `compare_00.png` (82.18%, **R3 excluded**) | **mixed** — T1 geometry px holds; T2 knobs land flat on MAE; residual checklist **B** | vs v6 p02: **+0.02 pp** mean |
| **02** | Chart.js (A: s27 drop side_legend + axis chrome; s11 exterior_segment_names; s14 grid/Y off; s05 frozen) | **89.49%** (+0.16) | 89.69% | (1) Platinum R2 chrome held — `compare_05.png` (**76.77%**); (2) Funding packing residual after legend purge — `compare_27.png` (**82.99%**); (3) Hero acq type scale — `compare_11.png` (**87.93%**) | **B residual after A exhaust** on N5 double-legend / s11 exterior names | vs v6 p02: **+0.18 pp** mean; **best mean this run** |

### Per-pass A closures vs B confirmations

| Pass | Meaningful (A) closures / observations | Confirmed / refined (B) |
|-----:|----------------------------------------|-------------------------|
| 01 | **T1 verify:** `calloutGeometry` rewrites elbow/stem/chevron to live chartArea px (capsule `left=97.54px width=543.52px`, stem h=150.8px, chevron `top=531.4px` on 709×562 wrap) — no new JSON keys. **T2 verify:** knobs serialize (`fontSize:20`, `offset:27`, `wrapChars:11`, `gutter:117`) on funding + provision | T1 geometry acceptance holds but PDF chrome residual (large axis-centered Refresh, L-elbow silhouette, IR head chips). T2 knobs alone **+0.05 pp** on s27 — packing still weak. F4+/N6/R4 unchanged |
| 02 | **N5 A:** strip funding `side_legend` + grid/Y off → sole exterior name column, **+4.34 pp** to 82.99%. **R4 A-scrape:** s11 `exterior_segment_names` + stack_totals + grid off → **+2.26 pp** to 87.93%. **N6 A-scrape:** s14 grid/Y off **+0.38 pp** chrome only | s05 strip `side_legend` **failed A** (wrap 709→853, MAE down → reverted). R2 chrome, N5 packing, F4+, N6 furniture, R4 hero type remain **B** |

**Stop rationale after pass 02:** Pass_01 verified landed T1/T2 under a fresh handoff. Pass_02 exhausted remaining pure-A levers (legend/chrome suppression, exterior names on dual-hero). Failed A on Platinum IR legend strip shows no pure-A path to PDF title-only boards without recipe loss. Further handoff micro-tunes will not produce PDF pill-arrow / large Refresh chrome, multi_panel dense packing, freestanding pill-column packing, freestanding reserve-rate furniture, or giant dual-card hero type. ≤10 budget preserved (**2 used**).

### Worst structural scores (pass_02 = decisive stop evidence)

| Slide | PDF topic | p01 % | p02 % | Primary gap after v7 |
|------:|-----------|------:|------:|----------------------|
| 05 | U.S. Consumer Platinum | **76.77** | **76.77** | **R2** chrome residual (T1 geometry holds; chevron/L-elbow/IR-head recipe) |
| 00 | Cover | 82.18 | 82.18 | **R3 wontfix — excluded** (generic seal_lockup) |
| 27 | Funding and Deposits | 78.65 | **82.99** | **N5 packing** residual after double-legend A purge |
| 12 | (structural sibling) | 83.35 | 83.35 | residual house chrome (not primary checklist ID) |
| 14 | Total Provision | 86.07 | **86.45** | **N6** furniture residual |
| 11 | New Acquisitions | 85.67 | **87.93** | **R4** hero type scale (exterior stack names A-landed) |
| 02 | Summary Financial | 90.56 | 90.56 | **F4+** packing residual |

### Mean MAE vs v6 final

| Snapshot | Mean MAE sim. | Notes |
|----------|--------------:|-------|
| v6 pass_01 (post-#114 frozen) | 89.29% | BEFORE snapshot companion |
| v6 pass_02 final | **89.31%** | v6 stop / wiki baseline |
| **v7 pass_01** (T1+T2 declared) | **89.33%** | +0.02 vs v6 final |
| **v7 pass_02** (A scrape) | **89.49%** | **+0.18 vs v6 final**; best this run |

---

## Before / after delta: v6 open gaps → current renderer (v7)

**Headline deliverable.** Each required ID re-tested on the **current** renderer with fresh pass evidence. Round-4 T1/T2 rows are **verification**, not discovery. Status is **not** inherited from PR titles or v6 conclusions.

| ID | v6 finding (summary + v6 slide/pass) | v7 status | v7 slide/pass evidence | Notes |
|----|--------------------------------------|-----------|------------------------|-------|
| **R2** IR geometric callout chrome (spanning blue pill arrow + large navy Refresh chevron) | Nodes painted; **geometry wrong** (mid-plot % capsule). Slide **05**; v6 `pass_02/compare_05.png` (**75.90%**). P0 | **partial** — **T1 geometry resolved**; PDF chrome **still-gap / weak** | p01–p02 DOM: `calloutGeometry` present; capsule spanning bar-centre→bar-centre in **px** (`left=97.54 width=543.52`), stem bar-top drop, chevron under axis (`top=531.4px`) — see `pass_01/slide05_geometry.json` / `pass_02/slide05_geometry.json`. Visual `pass_02/screenshots/compare_05.png` (**76.77%**, **+0.87 pp** vs v6): correct elementary placement but ≠ PDF left L-elbow into spanning blue capsule + **large bottom-center navy Refresh chevron**; IR heads/legend chrome also diverge | **T1 holds under fresh handoff** (6 acceptance-class geometry checks observed live). Exact geometry **did** move slide MAE, but only **+0.87 pp** — remaining gap is **chrome recipe (B)**, not coordinate-frame. Not full R2 close. |
| **N5 residual / F11 packing** multi-line exterior segment-name column density | Wire resolved; packing weak. Slide **27**; v6 `pass_02/compare_27.png` (**78.60%**) | **partial ↑** — **T2 knobs land**; double-legend **(A) closed**; packing **still weak** | p01: T2 knobs serialize on both funding tiles (`segment_name_font_size=20` … `gutter=117`) → MAE **78.65%** (+0.05). p02: drop both `side_legend` + axis chrome → sole exterior name column → **`compare_27.png` 82.99%** (**+4.39 pp** vs v6). Bars still narrower / cards less rounded / totals head-band not on-stack vs PDF | **T2 opt-in works as declared.** Typography knobs alone ≈ noise; real v7 A win was legend conflict removal. Residual = **multi_panel packing density (B weak)**. |
| **F4+** freestanding pill packing | `gl-pill-free` path; packing residual. Slides **02/19**; v6 p02 90.56 / 91.86 | **still-gap / weak** | Slide 02 **90.56%**, 19 **91.86%** flat p01–p02. `pass_02/screenshots/compare_02.png`: exterior label rail + three navy-header shells (17px) exist but packing / column separation still short of PDF freestanding statement columns | **Exists but weak.** No handoff density knob. Unchanged since v6. |
| **N6** provision furniture (reserve-rate boxed cells + exterior series legend) | Values OK via N1/N4; furniture weak. Slide **14**; v6 `compare_14.png` **86.07%** | **still-gap / weak** | p01 held 86.07% with T2 knobs (no furniture). p02 grid/Y off → **86.45%** (+0.38 chrome). `pass_02/screenshots/compare_14.png`: under-chart dense sheet row + KPI footer — **not** freestanding bordered `2.9%` cells + left label chip + exterior series legend | **Exists but weak** (wire reuse ≠ furniture). T2 irrelevant to boxed cells. |
| **R4** hero % type scale | Structure holds; type scale short. Slide **11**; v6 **85.67%** | **partial ↑ / still weak** | p02 A: `exterior_segment_names` + `stack_totals` on chart_hero_dual → **`compare_11.png` 87.93%** (**+2.26 pp** vs v6). Stack name column improved; right hero cards still dual stack of 66/73 not co-card giant type with title clique | Exterior stack names were **(A)**; **hero type scale remains B weak**. |
| **R1** flat stage residual | v6 improved/weak on slide **03** ~92.6% | **closed: accepted divergence per r4 spec D11** | s03 **92.62%** flat p01–p02 (`compare_03.png`) | **Not a gap.** Locked accepted divergence; do not rank or re-open. |
| **F12+** annex multi-level header precision | v6 weak residual; annex white MAE ~91–95% | **closed: accepted divergence per r4 spec D11** | Annex white-MAE still ~91–95% band (e.g. slide 28 region) | **Not a gap.** Unfalsifiable under white-biased MAE. |
| **N2 chip weight** bolder year chips | v6 mostly resolved + soft polish; slide **05** | **closed: accepted divergence per r4 spec D11** | Right-card year chips paint at 14px bold path (`compare_05.png`) | **Not a gap.** Heavier would wrong non-Amex decks. |
| **R3** Centurion seal | Cover gap | **dropped: wontfix per CONTEXT.md brand-asset rule** | `compare_00.png` 82.18% flat — generic `seal_lockup`. **By design** | Excluded from gap counts, delta-open list, and future-feature list (recorded once here as dropped). |

### Also closed / carried from earlier baselines (reconfirmed, not reopened)

| ID | Status | Evidence |
|----|--------|----------|
| **F10+** scale-root 90–100 domain | **resolved** (reconfirmed) | Platinum retention high-90s window; `compare_05.png` |
| **N1** secondary_visual under stacked_bar | **resolved** (reconfirmed) | Provision under-chart reserve-rate row; `compare_14.png` |
| **F3** signed negative stacks | **resolved** (reconfirmed) | Provision thin negative bars still paint |
| **N3/N4** dual stack labels + negchips | **mostly resolved** (reconfirmed) | in-segment `$` + tops + paren chips; `compare_14.png` |
| **N5 wire** (not packing) | **resolved** (reconfirmed) | `exterior_segment_names` + T2 knobs paint on funding |
| **#114 board vertical fill** | **lands** (reconfirmed) | Dual boards still tall on 05/11 |
| **T1 calloutGeometry (#115)** | **lands** (first measured this run) | Live px reposition; `slide05_geometry.json` |
| **T2 exterior-name knobs (#116)** | **lands** (first measured this run) | Serialized segmentNames config; packing still separate |

### NEW residuals observed this run

| ID | Finding | Slide / evidence | Type |
|----|---------|------------------|------|
| *(none new ID)* | No new missing chart family or layout_type. p02 confirmed: (1) **IR `side_legend` is load-bearing** for Platinum wrap width — stripping it regresses MAE even with correct calloutGeometry; (2) **funding double-legend** (Chart.js + side_legend + exterior names) was a pure-A conflict, now closed | `pass_02/notes.md`; `compare_05.png` / `compare_27.png` | refines **R2 chrome** and **N5 packing** as remaining B |

*(N7 footnote/unit-suffix density from earlier baselines not re-litigated; still absorbed under N5 packing residual on slide 27.)*

---

## Divergence catalog (compressed, v7)

| Div # | Theme | Primary IDs | v7 note |
|------:|-------|-------------|---------|
| D1 | Brand cover seal | R3 | **wontfix excluded** |
| D3 | Pill freestanding packing | F4+ | still weak |
| D4 | IR line stage chrome | R1 | **closed accepted D11** |
| D5 | Chart \| hero KPI dual | R4 | exterior names A↑; type scale still weak |
| D8 | Multi-panel / broken-axis boards | F10+, F11+, R2, N2, N5 | **F10+ closed**; **N2 weight closed D11**; **T1 geometry lands**; R2 chrome + N5 pack residual; double-legend A closed |
| D9 | Dense annex tables | F12+ | **closed accepted D11** |
| D13/D15 | Under-chart secondary | N1 | closed |
| D16 | Stacked dual labels + signed paren | N3/N4 | **mostly resolved** |
| D17 | Exterior segment name column | N5 | **wire + T2 knobs resolved**; packing weak |
| D18 | Horizontal anniversary domain | F10+ | closed |
| D19 | Provision furniture | N6 | still weak (no boxed cells / series legend furniture) |
| D20 *(carry)* | Callout coordinate frame | R2/T1 | **resolved by #115** — residual is recipe chrome, not frame |

---

## Prioritized future-feature list (still open AFTER this run)

Only items that remain open on fresh evidence. **Resolved geometry-frame (T1 math), accepted D11 locks, and R3 wontfix are omitted.** Each cites PDF slide + pass screenshot.

| Pri | Feature | What it enables | Motivating evidence | Missing vs weak |
|----:|---------|-----------------|---------------------|-----------------|
| **P0** | **R2 — true IR callout chrome recipe** (post-T1) | PDF-faithful L-elbow stem into spanning blue pill + **large** under-axis navy Refresh chevron silhouette/scale/weight; IR board title-only head chrome without destroying chart wrap | PDF p6 / slide **05**; `passes/pass_02/screenshots/compare_05.png` (**76.77%**); geometry JSON shows correct bar-centre px but chrome ≠ PDF; failed A strip of `side_legend` | **Exists but weak** (T1 placement OK; recipe/chrome wrong) |
| **P1** | **N5 residual / F11 packing — multi_panel card + exterior column density** | Dense multi-line exterior names + light rounded dual-card packing parity after legend conflict is gone (T2 knobs already deliver type size/offset) | PDF p28 / slide **27**; `passes/pass_02/screenshots/compare_27.png` (**82.99%**; +4.39 vs v6 after legend purge; packing short) | **Exists but weak** (wire + T2 + sole-name column A-done) |
| **P1** | **F4+ — freestanding pill-column packing finish** | Three navy-header freestanding statement columns at PDF density (not residual Boardroom spacing) | PDF p3 / slide **02**; `passes/pass_02/screenshots/compare_02.png` (**90.56%**); typography 17px navy engaged | **Exists but weak** (`gl-pill-free` path) |
| **P2** | **N6 — provision furniture polish** | Freestanding reserve-rate **boxed cells** + exterior series legend matching PDF Total Provision furniture (values already correct via N1/N4; exterior names / T2 insufficient) | PDF p15 / slide **14**; `passes/pass_02/screenshots/compare_14.png` (**86.45%**) | **Exists but weak** |
| **P3** | **R4 — hero dual % type scale** | Giant narrated % stack scale + dual narrative packing on acquisitions boards (exterior names A-done; board fill alone not enough) | PDF p12 / slide **11**; `passes/pass_02/screenshots/compare_11.png` (**87.93%**) | **Exists but weak** |

### Dropped since v6 (do not re-implement as open gaps)

| ID | Why dropped |
|----|-------------|
| F10+ | Resolved pre-v6; reconfirmed |
| N1 gate | Resolved pre-v6; reconfirmed |
| N3/N4 dual-set **capability** | Mostly resolved; only furniture polish remains (N6) |
| N5 **missing wire** + **T2 missing knobs** | Wire + knobs exist; residual packing only (kept above) |
| **T1 callout coordinate-frame / geometry math** | **Resolved by #115** — verified live px this run; residual chrome kept as R2 P0 recipe |
| **R1** flat stage | **Accepted divergence** per r4 SPEC D11 |
| **F12+** annex header precision | **Accepted divergence** per r4 SPEC D11 |
| **N2 chip weight** | **Accepted divergence** per r4 SPEC D11 |
| **R3** Centurion seal | **Wontfix** — CONTEXT.md brand-asset rule; not a gap |
| **#114 board vertical fill** | Lands; not a gap |

### Recommended implementation order (future renderer track — not this sim)

1. **R2 chrome recipe** — large Refresh chevron + L-elbow silhouette + IR head/title packing that coexists with calloutGeometry (still worst structural board at 76.77%).
2. **N5 residual packing** — multi_panel card/bar density + multi-line exterior column (Funding; legend conflict already handoff-fixed).
3. **F4+** freestanding pill packing finish.
4. **N6** provision furniture polish (boxed reserve cells + exterior series legend).
5. **R4** hero dual % type scale polish.

---

## What renderer_v2 already does well

Credited on fresh pass evidence (pass_01–02), not cargo-culted:

- **44-slide self-contained Chart.js deck** with Boardroom tokens, stable 1:1 page map, mean MAE **89.49%** best this run (+0.18 pp vs v6).
- **T1 calloutGeometry (#115)** — live chartArea px reposition of elbow/stem/chevron; bar-centre capsule span and under-axis chevron placement hold under fresh handoff (`slide05_geometry.json`).
- **T2 exterior-name knobs (#116)** — opt-in font/offset/gutter/wrap serialize and paint (`segmentNames` scripts=7 on p02 deck).
- **#114 board vertical fill** — dual IR / light boards still grow into the stage (slides 05/11).
- **F10+ anniversary window** — scale-root 90–100 on horizontal retention bars (slide 05).
- **N1 under-chart tables** — `secondary_visual` data_table under stacked_bar (slide 14).
- **N2 series-in-bar labels** — year chips inside horizontal bars (slide 05 right; 14px path; weight locked accepted).
- **N3/N4 dual stack labeling** — in-segment values + category tops + signed paren `negchip`s (slide 14).
- **N5 exterior segment names** — opt-in wire + sole-column recipe after dropping competing `side_legend` (slide 27 **82.99%**).
- **R2 overlay types + stem + chevron DOM** — paint cleanly; residual is chrome strength, not missing nodes.
- **F11 IR navy dual-card heads** + light tall cards when IR omitted (Platinum vs Funding).
- **F3 signed negative stacks** — reserve release bars below axis still correct.
- **R1 flat stage path** — holds ~92.6% on line boards (accepted residual).
- **F4+ freestanding pill path** — exterior label rail + navy header cells paint (packing residual only).
- **chart_hero_dual exterior names** — first-class A lever on acquisitions (+2.26 pp when enabled).

---

## Pass methodology (audit trail)

| Step | What happened |
|------|----------------|
| Workspace | `simulation/amex_q1_2026/{extracted,passes}/`; PDF → 44× `pdf_page_XX.png` @ 200 DPI (PyMuPDF primitive); `slides.json` restored from v6 archive |
| Pass 01 | Handoff = v6 p02 + T2 knobs on 14/27; R2 elbow_arrow frozen. Render `--self-contained`. Playwright 1920×1080 + MAE/SSIM + `slide05_geometry.json`. Mean **89.33%**. |
| Pass 02 | Pure-A: s27 drop `side_legend`/axes; s11 exterior names + totals; s14 grid/Y off; s05 freeze after failed legend-strip trial. Mean **89.49%**. |
| Stop | Remaining open-list items are type **(B)** (or accepted/wontfix). 2/10 passes used. |
| Deliverable | This file → also copied to `wiki/baseline_v7_GAP_ANALYSIS.md` for tracked baseline. |

Harness notes: screenshots via Playwright Chromium; similarity = 100×(1−mean abs pixel delta/255) vs PDF raster (resized); SSIM-approx companion score in `diff_scores.json`. DOM probes: elbow/stem/chevron counts, `calloutGeometry` presence, `segmentNames` script count.

---

## Conclusion

**v7 AFTER picture:** Round-4 **T1 geometry holds** (live px, bar-centre capsule, under-axis chevron) and **T2 knobs land**, but neither fully closes its parent visual gap under white-biased MAE. R2’s open question is answered: **exact geometry moved Platinum only +0.87 pp** — the unpaid debt is **chrome recipe**, not coordinate math. N5’s biggest fidelity win this run was **handoff hygiene** (kill double legends; **+4.39 pp** vs v6), leaving **packing density** as the true residual. F4+, N6, and R4 hero type remain exists-but-weak. R1 / F12+ / N2 weight stay **accepted D11**; R3 stays **wontfix**. Best mean **89.49%** (+0.18 pp vs v6) with **2** handoff-only passes and no renderer edits.

**Next (human Phase B, not this sim):** renderer track in recommended order starting at R2 chrome recipe, then N5 packing, F4+, N6, R4 — measure-only complete.
