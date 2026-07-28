# SPEC: Amex Q1'26 IR fidelity — round 5 (v7 residuals: callout + axis-break chrome)

**Status:** DRAFT — user-directed from direct inspection of the v7 slide 05 render against
PDF page 6. The §1 diagnoses are measured fact; mechanisms are PROPOSED pending a lock.

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

### R5-C — elbow lacks the PDF's left L-bracket arm

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
| **T8** | R5-C: elbow bracket arm to the axis (and optional right-end arm) — **measure PDF vs render first**, may close as already-close | **P2** | enhancement |
| — | R5-B(2): chevron `at: 4` → `at: 2` — **sim handoff fix, no code**, apply in the next sim pass | — | handoff |

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

**Both:** `TestGeometricCallouts`, `TestCalloutBandElbowMerge`, `TestCalloutGeometryPlugin`
green; `TestIrCalloutChrome` updated deliberately for the chevron split; full suite green
(baseline 1215 passed, 15 skipped); geometry verified manually via Playwright with a
screenshot per D8, and the full-suite run done **before** claiming green (round-4 lesson: a
file-scoped run missed a token audit and landed main red).

## 5. Out of scope

- **R3** Centurion seal — permanent wontfix (CONTEXT.md brand-asset rule).
- **R1**, **F12+**, **N2 chip weight** — accepted divergence per r4 spec D11; excluded in the
  sim prompt. Do not reopen.
- Canvas-drawn chrome — r4 D1 keeps callout/annotation chrome in themeable HTML/CSS.

## 6. Open questions for the lock

1. Confirm P2: is changing existing `y_axis_break` output acceptable as a bug fix, or does it
   need an opt-in flag to preserve today's dashed line?
2. T6 alone first (it is the P0 bug), or bundle T6+T7 as one "callout chrome" PR given both
   touch the same plugin and CSS block?
3. Is T8 worth doing at all, or does it join the accepted-divergence list? R2 has had three
   verified-correct fixes (#97, #104, #115) and slide 05 still sits at 76.77% — at some point
   the residual is PDF-matching of the kind R1/F12+ were closed for.
