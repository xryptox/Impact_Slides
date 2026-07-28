# SPEC: Amex Q1'26 IR fidelity — round 5 (v7 residuals: callout + axis-break chrome)

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


### R5-E — canvas charts paint BLACK when the handoff omits `series_colors` (bug)

`_series_colors` (charts.py:2021) falls back to `_BAR_SERIES_COLORS`, whose entries are CSS
custom-property **strings** — `"var(--navy, #00175a)"`, `"var(--blue, #006fcf)"`. Chart.js paints
to a `<canvas>`, where **CSS variables do not resolve**; the string is invalid, so Chart.js
silently falls back to black. Nothing in `charts.py` or `shell.py` calls
`getComputedStyle`/`getPropertyValue`, so the vars are never resolved anywhere.

Measured on slide 16: `datasets[0].backgroundColor === "var(--navy, #00175a)"` and the bars paint
black, while the sibling line chart works only because its color arrived as a literal `#006fcf`.

**Blast radius: 13 charts in the v7 deck** declare no `series_colors` and therefore render black
— slides 05, 08, 10, 13 (x2), 16 (x2), 17, 20 (x2), 26 (x2), 27. This is not an Amex issue: it is
every deck whose Builder omits the optional key, i.e. the documented default path is broken.

### R5-F — chart pane titles fall through to the Chart.js legend (bug)

PDF draws each pane's title as a **blue heading inside the card, above the plot** ("Net Card Fees
(Q1: 2019-2026)", "Net Card Fees YoY% (Q1'24-Q1'26)"). `multi_panel` does this correctly via
`gl-tile-label` (recipes.py:1024/1102), but **`render_dual_chart` passes no label** (recipes.py
~1660-1700 builds only `title` + `build_chart_html`), so the series name surfaces as a Chart.js
legend swatch instead — slide 16 shows a gray box reading "Net Card Fees $B" where the PDF has a
blue heading. User reports the same header/sub-header mismapping across the deck's charts.

### R5-G — absolutely-positioned inset boxes collide with content (bug)

`.gl-inset` (components.css:1050) is `position: absolute; top/right: var(--gap-md); z-index: 5`
with no layout reservation, so it floats over whatever is beneath. Measured on slide 19: the
"VCE of Revenue 44.7%" box spans x=1604-1808 while the third pill column spans x=1390-1824 — a
**204px overlap** that hides the "YoY% Inc/(Dec)" header and the 12% value. User reports the same
collision on several slides.


### R5-H — annex group banding alternates navy/blue decoratively (bug)

`recipes.py:946` sets `band = " gl-annex-group-alt" if gi % 2 else ""`, and
`components.css:1363` paints `-alt` in `var(--blue)`. So the second, fourth, ... header group
is light blue **purely because of its column index** — a decorative stripe with no semantic
meaning. User reports it on slides 30 and 32: "Current/FX-Adj" renders light blue while
"Prior/Reported" is navy, implying a distinction the data does not have.

**PDF ground truth (pages 33, 34 at 150dpi):** the annex header band is **uniformly navy across
every column**. There is no alternating blue anywhere in the annex family. The `-alt` banding
introduced by round-3 #94 was invented, not observed.

Fix: drop the index-based alternation and paint all group cells navy. Keep the `-alt` class
available for a future *semantic* banding need, but do not apply it by column parity.

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

## 2. Proposed mechanism (PROPOSED — needs lock)

**P1 — reuse the T1 plugin, do not invent a second one.** `calloutGeometry` already walks
`chartArea`/`scales` on `afterLayout` and writes wrap-relative pixels per node. The break glyph
and the split chevron are the same problem in the same frame, so they become additional node
types the existing plugin positions: break glyph at `scales.x.getPixelForValue(break.to)`
clamped to the axis origin with its top on `chartArea.bottom`; chevron triangle and pill
stacked below `chartArea.bottom`, both centred on `scales.x.getPixelForValue(at)`.

**P2 — the break glyph becomes a `//` hatch, not a line.** Replace the full-height dashed rule
with a small two-stroke glyph on the axis. This is a **visual change to any existing deck that
declares `y_axis_break`**, so it is a deliberate exception to byte-identical compat: the current
output is a bug (a mid-plot threshold line), not a contract. Flag at review.

**P3 — split the chevron into triangle + pill nodes.** `_build_callout_overlays` emits two
sibling divs (`chartjs-callout-chevron-tip`, `chartjs-callout-chevron-pill`) instead of one.
The existing `TestIrCalloutChrome` regexes assert `border-top` navy + a navy label on the
single node, so that contract changes and must be updated deliberately.

**P4 — no handoff schema change.** `y_axis_break {from,to}` and `callouts[] {type,at,text}`
stay as-is; SC-COMPAT-1 holds for every deck that does not use them.

---

## 3. Ticket map

| Ticket | Scope | Pri | Type |
|---|---|---|---|
| **T6** | R5-A: axis-break `//` hatch on the axis, positioned from `scales` via the T1 plugin; delete the mid-plot dashed rule | **P0** | bug |
| **T7** | R5-B(1): split chevron into stacked triangle + pill, both anchored below `chartArea.bottom` | **P1** | enhancement |
| **T9** | R5-D: position annotation boxes from their declared `x`/`y` in data space via the T1 plugin; fail closed when unresolvable | **P1** | bug |
| **T10** | R5-E: resolve the default palette to real hex before it reaches canvas (13 charts render black today) | **P0** | bug |
| **T11** | R5-F: chart pane titles as in-card headings for `dual_chart` (and any recipe falling through to the legend); audit header/sub-header mapping deck-wide | **P1** | bug |
| **T12** | R5-G: stop `.gl-inset` overlapping content — reserve space (shrink table columns / gutter) instead of floating | **P1** | bug |
| **T13** | R5-H: annex group band uniformly navy; drop index-parity `-alt` banding (PDF has no alternating blue) | **P2** | bug |
| — | R5-I: annex tables degenerate on 33-36 and merged on 32 — **handoff/transcription defect, no renderer ticket**; fix via sim-prompt rules | — | sim |
| ~~T8~~ | ~~R5-C elbow bracket arm~~ — **dropped per L3**, accepted divergence | — | — |
| — | R5-B(2): chevron `at: 4` → `at: 2` — **sim handoff fix, no code**, apply in the next sim pass | — | handoff |

**T6 + T7 + T9 ship as one bundled PR** (L2): one plugin, one CSS block, three faces of the
same frame bug.

**T10 ships alone and first.** It is a one-line-class fix with the widest blast radius (13 charts,
every non-Amex deck that omits `series_colors`) and is independent of the callout work. **T11 and
T12** are layout/CSS work on different files and should not be bundled with either.

Unchanged from round 4 and still open: F4+ pill packing (P1, slide 02 @ 90.56%), N6 provision
furniture (P2, slide 14 @ 86.45%), R4 hero type scale (P3, slide 11 @ 87.93%), N5 packing
density (P1, slide 27 @ 82.99%).

## 4. Acceptance criteria

**T6:** glyph centre within ±4px of `scales.x.getPixelForValue(break.to)` (horizontal) or the
y equivalent, clamped to the axis origin; glyph top within ±4px of `chartArea.bottom`; no node
paints inside the plot area; omitted fail-closed when the break value is unreadable; decks
without `y_axis_break` byte-identical.

**T7:** triangle apex and pill centre within ±4px of `scales.x.getPixelForValue(at)`; pill top
at/below the triangle base; triangle top at/below `chartArea.bottom`; both omitted fail-closed
without a resolvable anchor.

**T9:** box anchor within ±4px of `scales.x.getPixelForValue(x)` / `scales.y.getPixelForValue(y)`
when the declared values are in data space, clamped inside `chartArea`; omitted fail-closed when
unresolvable; decks declaring no annotation byte-identical. Note the four v7 declarations look
like **pixel** guesses, not data values (`x:520` on a 5-category axis) — resolve which space
`x`/`y` mean as step one, and treat out-of-domain values as a fail-closed case.

**All:** `TestGeometricCallouts`, `TestCalloutBandElbowMerge`, `TestCalloutGeometryPlugin`
green; `TestIrCalloutChrome` updated deliberately for the chevron split; full suite green
(baseline 1215 passed, 15 skipped); geometry verified manually via Playwright with a
screenshot per D8, and the full-suite run done **before** claiming green (round-4 lesson: a
file-scoped run missed a token audit and landed main red).

**T10:** every dataset color reaching Chart.js is a literal color (hex/rgb), never a `var(...)`
string; slide 16 bars paint navy `#00175a`; charts that DO declare `series_colors` are unchanged;
a regression test asserts no serialized Chart.js config contains `var(--`. Prefer resolving the
token at render time in Python (tokens are known) over a JS `getComputedStyle` pass, so the
`<noscript>` SVG path benefits too — confirm which at implementation.

**T11:** `dual_chart` panes emit an in-card heading element from the handoff's pane label/title;
the Chart.js legend is suppressed when a heading carries the same text (no duplicate); decks
relying on the legend today keep it when no heading text exists. Deck-wide audit of which
recipes map `label`/`top_total`/sub-header vs which drop them is step one — report the table
before changing recipes.

**T13:** every `.gl-annex-group` cell paints `var(--navy)` on slides 30/31/32; no cell paints
`var(--blue)` by column parity; the existing F12+ contract test that asserts the white-on-navy
sub-header stays green, and any test pinning `-alt` by index is updated deliberately.

**T12:** no `.gl-inset` box overlaps any sibling content box on any of the 44 v7 slides (assert
by measuring bounding-box intersection in Playwright, not by eye); the inset either reserves a
column/gutter or the table shrinks to fit; verify slide 19's third column header and 12% value
are fully visible.

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
