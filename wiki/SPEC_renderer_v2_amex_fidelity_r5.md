# SPEC: Amex Q1'26 IR fidelity — round 5 (v7 residuals: callout + axis-break chrome)

> **Superseded - historical. Round 5 is LOCKED and fully shipped (T6-T14). New fidelity tickets land in round 6 (`_r6`), not here.**

**Status:** LOCKED — user-directed from direct inspection of the v7 slide 05 render against
PDF page 6, locked 2026-07-28. The §1 diagnoses are measured fact.

**Locked decisions:** (L1) T6 fixes the axis-break output outright — today's mid-plot dashed
line is a bug, not a contract, so no opt-in flag preserves it. (L2) T6+T7+T9 ship **bundled**
as one callout-chrome PR since all three are the same coordinate-frame defect in the same
plugin and CSS block. (L3) **T8 is dropped** — the elbow bracket arm joins the accepted-
divergence list; R2 has had three verified-correct fixes (#97, #104, #115) and further work is
subjective PDF-matching of the kind R1/F12+ were closed for.

**Evidence:** `wiki/baseline_v7_GAP_ANALYSIS.md` (v7 AFTER round-4 T1/T2; 2 passes, best mean
MAE 89.49% vs v6 89.31%). Full artifacts on `origin/gnhf/objective-produce-a-845b83` under
`simulation/amex_q1_2026/`. Ground truth: PDF page 6 "U.S. Consumer Platinum Performance"
(deck slide 05), plus page 7 for the sibling elbow recipe.

**Predecessor:** round 4 (T1 #115, T2 #116). v7 verified T1's coordinate-frame fix holds live
(capsule `left=97.54px width=543.52px`, stem `h=150.8px`, chevron `top=531.4px` on a 709×562
wrap — matches the pre-merge measurement to the pixel) and that T2's knobs serialize as
declared. Slide 05 moved only +0.87 pp to 76.77% and is still the deck's worst board: the
remaining gap is **chrome recipe**, not coordinate math. This round attacks that recipe.

---

## 1. Measured diagnoses

### R5-A — axis-break glyph is a full-height mid-plot dashed line (bug)

`charts.py:1301-1308` emits `<div class="chartjs-axis-break">` whenever `y_axis_break` is set,
and `components.css:1528-1546` positions it at a **hardcoded `left: 30%` / `top: 30%` of the
chart wrap** with `height: 100%` (`width: 100%` in the horizontal case). Measured on the v7
slide 05 right tile: a 2px dashed line 561.6px tall at x≈1194.7, i.e. mid-plot at x-value
≈92.3 on a 90→100 axis.

This is the **same coordinate-frame class of bug T1 fixed** for callouts: a hardcoded wrap
percentage with no relation to the value it represents. Visually it reads as a data threshold
or target line — actively misleading on a retention chart.

**PDF recipe (page 6 right tile, confirmed at 170dpi):** a small **`//` double-slash hatch
glyph sitting *on* the axis line at its origin**, immediately left of the "90%" label —
roughly 14px tall, thin gray strokes, entirely **outside** the plot area. It marks "this axis
does not start at zero". There is no line crossing the plot at all.

### R5-B — Refresh chevron is fused to its pill and mis-anchored

Two separate problems, one renderer-side and one handoff-side:

1. **Renderer:** the chevron is a single node whose triangle is a CSS `border-top` on the same
   element as the label pill, so the triangle and pill are welded together as one 34×22px unit.
   The PDF draws a **downward navy triangle above a separate rounded navy pill** containing
   "Refresh" — two stacked elements, the pill fully below the tick labels.
2. **Handoff (not a renderer bug):** the v7 handoff declares `{"type": "chevron", "at": 4}`,
   putting it on Q1'26. The PDF anchors it to **Q3'25** (`at: 2`), the quarter the refresh
   actually landed. The renderer is faithfully honouring a wrong input — fix in the sim
   handoff, not in code.

### R5-D — annotation boxes silently discard their declared x/y (bug)

Found while auditing the sibling overlays for the same defect. `components.css:1512` pins
`.chartjs-annotation` at a hardcoded `top: 12%; left: 22%` of the chart wrap, and the handoff's
declared coordinates are **never read**. The v7 deck declares four of them:

| Slide | Text | Declared | Painted (measured) |
|---|---|---|---|
| 03 | Leap Year Approx. (1%) | `x:90, y:55` | 203.3px = **22.0%** of a 924px wrap |
| 09 | Reported | `x:520, y:70` | — same rule |
| 10 | Leap Year Approx. (1%) | `x:420, y:90` | 359.5px = **22.0%** of a 1634px wrap |
| 18 | Leap Year Approx. (1%) | `x:80, y:40` | — same rule |

Both measured slides land on exactly 22.0%/12.0% regardless of their declared `x`/`y`, so all
four boxes float in the same arbitrary spot. This is the **third instance** of the identical
coordinate-frame defect (callouts → T1, axis-break → R5-A, annotations → R5-D), and it is
why the round-4 spec deferred `chartjs-annotation` as "needs a data anchor" — the anchor was
already in the handoff all along.


### R5-E — canvas charts paint BLACK when the handoff omits `series_colors` (bug) — **fixed (T10)**

**Was:** `_series_colors` fell back to `_BAR_SERIES_COLORS` entries that were CSS custom-property
**strings** — `"var(--navy, #00175a)"`, `"var(--blue, #006fcf)"`. Chart.js paints to a `<canvas>`,
where **CSS variables do not resolve**; the string is invalid, so Chart.js silently fell back to
black. Nothing in `charts.py` or `shell.py` called `getComputedStyle`/`getPropertyValue`.

Measured on slide 16 pre-fix: `datasets[0].backgroundColor === "var(--navy, #00175a)"` and the
bars painted black (sibling line chart only worked because its color arrived as literal `#006fcf`).
**Blast radius was 13 charts in the v7 deck** with no `series_colors` — slides 05, 08, 10, 13 (x2),
16 (x2), 17, 20 (x2), 26 (x2), 27 — i.e. every deck whose Builder omits the optional key.

**Fix (T10):** `_BAR_SERIES_COLORS` is literal hex mirroring `css/tokens.css`
(`#00175a`/`#006fcf`/`#80c8ff`/`#63666a`). Handoff-declared `series_colors` still pass through
byte-identical (SC-COMPAT-1), including deliberate `var()` strings for the N5 segmentNames plugin.
SVG painter `var()` sites stay as-is (CSS resolves them). Regression:
`TestDefaultPaletteResolved`.

### R5-F — chart pane titles fall through to the Chart.js legend (bug) — **shipped (T11)**

PDF draws each pane's title as a **blue heading inside the card, above the plot** ("Net Card Fees
(Q1: 2019-2026)", "Net Card Fees YoY% (Q1'24-Q1'26)"). Pre-fix: `multi_panel` did this via
`gl-tile-label`, but `render_dual_chart` passed no label, so the series name surfaced as a Chart.js
legend swatch (slide 16: gray "Net Card Fees $B" where the PDF has a blue heading).

**Fix (T11):** `render_dual_chart` panes emit `gl-tile-label` from an explicit per-pane `label`,
else the pane's single series name. Single-series legends (dual panes and full-slide charts) are
suppressed via internal `chart_config.show_legend=False` (default True, SC-COMPAT-1). Multi-series
panes keep their legend. Regression: `test_dual_chart` heading/legend cases.

### R5-G — absolutely-positioned inset boxes collide with content (bug) — **fixed (T12)**

**Was:** `.gl-inset` used `position: absolute; top/right: var(--gap-md); z-index: 5` with no
layout reservation, so it floated over whatever was beneath. Measured on slide 19: the
"VCE of Revenue 44.7%" box spanned x=1604-1808 while the third pill column spanned x=1390-1824
— a **204px overlap** that hid the "YoY% Inc/(Dec)" header and the 12% value.

**Fix (T12):** `.gl-areas-table-inset` is a flex row-reverse gutter — the inset reserves real
width and the table shrinks beside it (not a z-index/opacity stack tweak). Playwright
bounding-box intersection across all 44 v7 slides: 2 slides emit `.gl-inset`, both 0 overlaps.


### R5-H — annex group banding alternates navy/blue decoratively (bug) — **fixed (T13)**

**Was:** `recipes.py` set `band = " gl-annex-group-alt" if gi % 2 else ""`, and
`components.css` painted `-alt` in `var(--blue)`. So every second header group was light blue
**purely because of its column index** — a decorative stripe with no semantic meaning.

**PDF ground truth (pages 33, 34 at 150dpi):** the annex header band is **uniformly navy across
every column**. There is no alternating blue anywhere in the annex family. The `-alt` banding
introduced by round-3 #94 was invented, not observed.

**Fix (T13):** drop index-parity alternation; every group cell paints navy. Keep the `-alt`
class/CSS available for a future *semantic* (handoff-declared) banding need. F12+ white-on-navy
sub-header contract stays green. Computed styles on annex group cells: all `rgb(0,23,90)`.

### R5-I — annex tables are structurally degenerate on slides 33-36 (handoff, not renderer)

Slides 33-36 declare a two-column `['Item', 'Detail']` header and then emit every PDF cell as
its own row with an empty second column:

```
['Item', 'Detail'] / ['$ in millions', ''] / ["Q1'26", ''] / ['Discount Revenue', ''] /
['$9,512', ''] / ['$8,743', ''] / ['FX-Adjusted*', ''] ...
```

The PDF (page 34) is a clean **4-column table** — row label, `Q1'26`, `Q1'25`, `YoY% Inc/(Dec)` —
with a paired unbolded `FX-Adjusted*` sub-row under each metric. The transcription flattened a
2-D table into a 1-D key/value list, losing the column structure entirely. Slide 32 has the
same class of problem in reverse: the PDF is **two stacked tables** (a values block Q1'19-Q1'26,
then a CAGR block) and the handoff merged them into one 10-column table with mostly-empty CAGR
rows.

**This is a transcription/handoff defect, not a renderer gap** — `render_annex_table` faithfully
renders the degenerate structure it was given. It cannot be fixed in renderer code, and no
renderer ticket should be filed for it. Two consequences to act on:

1. The **sim prompt** should require the worker to transcribe annex tables as real 2-D grids
   (row label + one column per period, sub-rows preserved) and to split a PDF page that shows
   two separate tables into two handoff visuals rather than merging them.
2. Annex MAE numbers for slides 33-36 are **not measuring the renderer** and should not be cited
   as renderer gaps in any GAP_ANALYSIS (this is the same trap as F12+, now closed under D11).

### R5-C — elbow lacks the PDF's left L-bracket arm — **DROPPED (L3)**

PDF page 6 (and page 7's `10x`/`2x` siblings) draw the capsule with a **vertical bracket arm
dropping from the left end down to the axis**, arrowhead on the right end. T1 built the left
stem (verified `h=150.8px` to the from-bar top) and the right arrowhead, so the silhouette is
close; the residual is that PDF's arm terminates at the **axis**, not the from-bar top, and
page 7 shows arms at **both** ends. Lowest-confidence item in this round — measure first.

---

## 2. Mechanism (shipped — T6/T7/T9 bundled)

**P1 — reuse the T1 plugin, do not invent a second one.** `calloutGeometry` already walks
`chartArea`/`scales` on `afterLayout` and writes wrap-relative pixels per node. The break glyph
and the split chevron are the same problem in the same frame, so they become additional node
types the existing plugin positions: break `//` hatch at the axis origin (top on
`chartArea.bottom`; on horizontal bars the `-v` variant also centres on
`scales.x.getPixelForValue(break.to)`); chevron triangle and pill stacked below
`scales.x.bottom` (tick row included; falls back to `chartArea.bottom`), both centred on
`scales.x.getPixelForValue(at)`. Annotation boxes use the same plugin with declared `x`/`y`
as pixel offsets inside `chartArea`.

**P2 — the break glyph is a `//` hatch, not a line.** Replaced the full-height dashed rule
with a small two-stroke glyph on the axis. Deliberate exception to byte-identical compat for
decks that declare `y_axis_break` (L1): the old mid-plot line was a bug, not a contract.

**P3 — split the chevron into triangle + pill nodes.** `_build_callout_overlays` emits two
sibling divs (`chartjs-callout-chevron-tip`, `chartjs-callout-chevron-pill`) instead of one.
`TestIrCalloutChrome` was updated deliberately for the split (no fused single-node chevron).

**P4 — no handoff schema change.** `y_axis_break {from,to}` and `callouts[] {type,at,text}`
stay as-is; SC-COMPAT-1 holds for every deck that does not use them.

---

## 3. Ticket map

| Ticket | Scope | Pri | Type |
|---|---|---|---|
| ~~**T6**~~ | ~~R5-A: axis-break `//` hatch on the axis, positioned from `scales` via the T1 plugin; delete the mid-plot dashed rule~~ — **shipped** (bundled with T7/T9) | ~~**P0**~~ | bug |
| ~~**T7**~~ | ~~R5-B(1): split chevron into stacked triangle + pill, both anchored below the tick row (`scales.x.bottom`)~~ — **shipped** (bundled with T6/T9) | ~~**P1**~~ | enhancement |
| ~~**T9**~~ | ~~R5-D: position annotation boxes from their declared `x`/`y` as pixel offsets inside `chartArea` via the T1 plugin; fail closed when unresolvable~~ — **shipped** (bundled with T6/T7) | ~~**P1**~~ | bug |
| ~~**T10**~~ | ~~R5-E: resolve the default palette to real hex before it reaches canvas~~ — **shipped** (`_BAR_SERIES_COLORS` → literal hex; `TestDefaultPaletteResolved`) | ~~**P0**~~ | bug |
| ~~**T11**~~ | ~~R5-F: chart pane titles as in-card headings for `dual_chart`~~ — **shipped** (`gl-tile-label` + `show_legend`; `test_dual_chart`) | ~~**P1**~~ | bug |
| ~~**T12**~~ | ~~R5-G: stop `.gl-inset` overlapping content — reserve gutter instead of floating~~ — **shipped** (flex gutter; 0 Playwright bbox overlaps on v7) | ~~**P1**~~ | bug |
| ~~**T13**~~ | ~~R5-H: annex group band uniformly navy; drop index-parity `-alt` banding~~ — **shipped** (all groups navy; `-alt` kept for semantic use) | ~~**P2**~~ | bug |
| — | R5-I: annex tables degenerate on 33-36 and merged on 32 — **handoff/transcription defect, no renderer ticket**; fix via sim-prompt rules | — | sim |
| ~~**T14**~~ | ~~R5-J/N9: non-stacked vertical bars silently drop `point_labels` on the Chart.js path~~ — **shipped** (`_fmt_value_label` shared helper; `test_bar_point_labels_t14`) | ~~**P2**~~ | bug |
| **F5** | follow-up: handoff theme cannot tint the default chart palette (T10 ceiling) — **do not pick up until the trigger below fires** | **P3** | enhancement |
| ~~T8~~ | ~~R5-C elbow bracket arm~~ — **dropped per L3**, accepted divergence | — | — |
| — | R5-B(2): chevron `at: 4` → `at: 2` — **sim handoff fix, no code**, apply in the next sim pass | — | handoff |

**T6 + T7 + T9 ship as one bundled PR** (L2): one plugin, one CSS block, three faces of the
same frame bug.

**T10 shipped alone first** (literal-hex default palette; independent of callout work). **T11
shipped** (dual_chart/`render_chart` headings + legend suppression). **T12 + T13 shipped** as
inset/annex layout fixes (not bundled with the callout PR). **T14 shipped** (grouped/plain bars
honour `point_labels` + `y_axis_unit` via shared `_fmt_value_label`; Chart.js/SVG parity).

Unchanged from round 4 and still open: F4+ pill packing (P1, slide 02 @ 90.56%), N6 provision
furniture (P2, slide 14 @ 86.45%), R4 hero type scale (P3, slide 11 @ 87.93%), N5 packing
density (P1, slide 27 @ 82.99%).

## 4. Acceptance criteria

**T6 (met):** `//` hatch glyph on the axis at its origin — top within ±4px of
`chartArea.bottom`, entirely outside the plot (no mid-plot dashed rule). On horizontal bars
the `-v` variant also centres on `scales.x.getPixelForValue(break.to)` (clamped to the plot
width). Omitted fail-closed when the break value is unreadable; decks without `y_axis_break`
byte-identical.

**T7 (met):** split `chartjs-callout-chevron-tip` + `chartjs-callout-chevron-pill` siblings;
triangle apex and pill centre within ±4px of `scales.x.getPixelForValue(at)`; stack top at/below
`scales.x.bottom` (tick row included; falls back to `chartArea.bottom`); pill top at/below the
triangle base; tip uses `box-sizing: content-box` so the CSS triangle is not a solid block;
pill uses a fixed radius (not `--radius-round` 50%). Both omitted fail-closed without a
resolvable anchor.

**T9 (met):** declared `x`/`y` are **pixel offsets within the plot area** (matching the SVG
fallback painter), applied as `chartArea` origin + `(x,y)` and clamped so the box stays inside
`chartArea`; omitted fail-closed when missing/non-numeric; decks declaring no annotation
byte-identical. (Judgment call locked at ship: not data-space — values like `x:520` on a
5-category axis are only coherent as pixels.)

**All:** `TestGeometricCallouts`, `TestCalloutBandElbowMerge`, `TestCalloutGeometryPlugin`
green; `TestIrCalloutChrome` updated deliberately for the chevron split; full suite green
(baseline 1215 passed, 15 skipped); geometry verified manually via Playwright with a
screenshot per D8, and the full-suite run done **before** claiming green (round-4 lesson: a
file-scoped run missed a token audit and landed main red).

**T10 (met):** default dataset colors reaching Chart.js are literal hex (never `var(...)`); slide
16 bars paint navy `#00175a`; handoff-declared `series_colors` pass through unchanged (SC-COMPAT-1);
`TestDefaultPaletteResolved` asserts no serialized Chart.js config contains `var(--`. Resolved
server-side in Python (not JS `getComputedStyle`) so the noscript SVG fallback matches.

**T11 (met):** `dual_chart` panes emit `gl-tile-label` from per-pane `label` (else single series
name); single-series legend suppressed via `chart_config.show_legend=False` (default True);
multi-series / overlay panes keep the legend; full-slide single-series charts likewise drop the
lone swatch (slide title is the heading). `test_dual_chart` covers heading + legend cases.

**T13 (met):** every `.gl-annex-group` cell paints `var(--navy)` (computed `rgb(0,23,90)`); no
cell paints `var(--blue)` by column parity; F12+ white-on-navy sub-header contract stays green;
index-parity `-alt` assertion removed (class may remain in CSS for future semantic use).

**T12 (met):** no `.gl-inset` box overlaps any sibling content box on any of the 44 v7 slides
(Playwright bounding-box intersection; 2 slides emit `.gl-inset`, both 0 overlaps); inset
reserves a flex gutter and the table shrinks beside it; slide 19 third column header + 12%
value fully visible.

## 4a. T14 — non-stacked vertical bars drop `point_labels` on the Chart.js path (R5-J / N9) — **shipped**

**Found by the v8 sim** (first run under the geometry+visual method, no MAE). Filed as N9 there
against a narrower symptom — "`y_axis_unit` `$` prefix does not reach dual_chart bar labels" —
but the measured defect is wider, so this ticket supersedes that framing.

### Diagnosis (was)

In `_chartjs_bar_config` **both** datalabel branches were nested inside `if stacked ...`:

- stacked gate held `stack_totals` / `point_labels` / `show_point_labels`, and with them the
  `y_axis_unit` / `y_axis_unit_position` formatting closure.
- N4 in-segment `point_labels` branch was likewise stacked-only.

So a **non-stacked** vertical bar chart declaring `point_labels: true` emitted **no datalabels
config at all** — not merely an unprefixed one. Reproduced directly:

| chart | declared | `_labels` emitted |
|---|---|---|
| vertical bar, `stacked=True` | `point_labels`, `y_axis_unit: "$"` prefix | `[["$0.9", "$2.8"]]` |
| vertical bar, grouped/plain | same | **`None`** |
| line chart | same | `[["$0.9", "$2.8"]]` |

**Painter parity was broken.** For the same handoff the noscript SVG painter *did* draw the value
labels (as `0.9`, `2.8` — itself missing the `$`), while Chart.js drew none. Which labels a
reader saw depended on whether JS ran.

Evidence: v8 slide 16 (Net Card Fees, PDF p17) declared
`{point_labels: true, y_axis_unit: "$", y_axis_unit_position: "prefix"}` and painted bare
`0.9 … 2.8`. The handoff asked correctly; the renderer dropped it.

### Fix (T14)

1. Lifted `point_labels` / `show_point_labels` out of the stacked-only gate for vertical bars —
   grouped/plain bars paint above-bar value labels (`anchor: end`, `align: top`, line-path
   recipe; in-segment white recipe stays stacked-specific).
2. Shared `_fmt_value_label` for stacked, grouped Chart.js, and SVG grouped-bar paths so
   `y_axis_unit` / `y_axis_unit_position` apply once (`$0.9` / `$0.9B`, `72%`, parenthesized
   negatives). Compound currency units split around the number (symbol leads, magnitude trails)
   matching axis-tick `_fmt_bar` — ticks and value labels cannot disagree on the same chart.
3. Number formatting follows the axis-tick rule (`:g` under 1000, comma thousands above).

**Deliberate output deltas vs pre-T14 stacked labels** (tick rule wins; no shipped deck hits
either): fractional values ≥1000 gain the thousands comma (`$1275.5` → `$1,276`); compound
`$B`/`$M` labels go `$B1,223` → `$1,223B` (the bug being fixed). `_fmt_bar(-73,'$')` still
returns `$-73` (sign inside currency prefix) — long-standing axis output, out of scope.

### Acceptance (met)

- A grouped/plain vertical bar with `point_labels` emits a datalabels config whose `_labels`
  match the declared unit and position.
- Chart.js and SVG painters produce the **same label text** for the same handoff.
- Decks that do not declare `point_labels` stay byte-identical (SC-COMPAT-1).
- Full suite green (**1296 passed, 15 skipped**); contract pinned by `test_bar_point_labels_t14`
  (unit placement, IR negatives, position overrides, `$B` SVG guard, tick≡label invariant).
- Verified live on v8 pass_03 Amex handoff slide 16 (`$0.9`…`$2.8` above bars); slide 14 stacked
  chart unchanged.

## 4b. F5 — themed default chart palette (filed, deliberately not scheduled)

**Note on the ID:** numbered **F5**, not F4, because `F4+` is already taken repo-wide (freestanding
pill-column packing, referenced in 7 wiki files and the sim prompt). Reusing `F4` would collide.

**Ceiling introduced by T10.** `_BAR_SERIES_COLORS` is now literal hex, because Chart.js paints to
a `<canvas>` where CSS custom properties never resolve. Consequence: a handoff-native theme (F13)
that overrides `--navy` / `--blue` / `--blue-sky` / `--ink-muted` **no longer tints charts that
rely on the default palette**. The token still themes every CSS-rendered surface; only the canvas
palette is now fixed.

**Why this is filed and not fixed — measured, not assumed:**

- The only real handoff that overrides a palette token is the v7 Amex deck, and it sets
  `"--navy": "#00175A"` — **byte-identical (case aside) to T10's default `#00175a`**. Zero pixels
  change on any deck that exists today.
- That theme does **not** override `--blue`, `--blue-sky` or `--ink-muted` at all, so even a
  themed deck was only ever tinting 1 of 4 palette slots.
- A real fix means threading `theme` from `render_deck` → `_paint_slides` → `build_chart_html`
  → 4 recipe call sites → the `_chartjs_*_config` builders → **9 `_series_colors` call sites**:
  a wide two-module signature change to alter colours on a deck that does not exist, to a value
  that is currently identical. Speculative generality of exactly the kind that produced the
  invented `-alt` annex banding deleted in T13.

**Escape hatch (already shipped, is the intended path):** any deck needing brand chart colours
declares `chart_config.series_colors`, which flows through untouched — this is how every Amex
chart that already rendered correctly was working.

**Trigger to pick this up:** a handoff ships a `presentation.theme` whose palette tokens differ
from the token defaults in `tokens.css`. Not before.

**When picked up:** prefer resolving theme tokens to hex in Python at render time (keeps the
`<noscript>` SVG path and the Chart.js path in agreement) over a browser `getComputedStyle` pass,
which would desync the two painters. Only the four palette entries need resolving, not every
`var()` in the file — SVG `fill=`/`stroke=`/`font-family=` sites resolve correctly via CSS and
must stay as tokens.

**Related standing guard:** `TestDefaultPaletteResolved::test_no_var_in_any_chartjs_config`
(added by T10) asserts no serialized Chart.js config contains `var(--`. That guard is the durable
protection for this whole bug family — the architectural rule is **CSS custom properties cannot
cross into canvas**, and it must keep passing regardless of how F5 is eventually implemented.

## 5. Out of scope

- **R3** Centurion seal — permanent wontfix (CONTEXT.md brand-asset rule).
- **R1**, **F12+**, **N2 chip weight** — accepted divergence per r4 spec D11; excluded in the
  sim prompt. Do not reopen.
- **R5-C / T8 elbow bracket arm** — accepted divergence per L3. Add to the sim-prompt exclusion
  block so future workers stop reporting the L-elbow silhouette as a gap.
- Canvas-drawn chrome — r4 D1 keeps callout/annotation chrome in themeable HTML/CSS.

## 6. Resolved at lock

1. **Fix outright** — no opt-in flag for the old dashed line (L1).
2. **Bundled** — T6+T7+T9 in one PR (L2).
3. **T8 dropped** — accepted divergence, added to the sim exclusion block (L3).
