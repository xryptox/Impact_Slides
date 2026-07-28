# SPEC: Amex Q1'26 IR fidelity — round 4 (v6 residual gaps)

**Status:** DRAFT — alignment record proposed from the v6 sim results. Decisions marked
**(PROPOSED)** need a human lock before filing tickets; the measured diagnosis in §1 is fact.

**Evidence:** `wiki/baseline_v6_GAP_ANALYSIS.md` (v6 AFTER PR #114; 2 passes, mean MAE 89.31%
vs v5 89.38% — flat mean, structural wins). Full artifacts (passes, handoffs, compare shots)
on `origin/gnhf/objective-produce-a-03e1d0` under `simulation/amex_q1_2026/`.

**Predecessor:** round-3 epic (8 children, closed) + Phase B PRs #104, #105, #106, #108, #110,
#111, #112, #113, #114. v6 verified those: board fill lands (+2.00 pp slide 05, +2.67 pp slide 11
under a frozen handoff), band→elbow merge is clean, N2 chips and F4+ navy cells paint,
N1/N3/N4/F3/F10+ reconfirmed closed. **R2 is the only P0 left**; everything else is
"exists but weak" packing/furniture/type polish.

---

## 1. R2 root cause — measured, not inferred

The v6 worker reported "capsule + chevron paint but geometry is wrong" and proved it is
type (B) by declaring `elbow_arrow` alone (zero visual change). Fresh instrumentation of the
v6 pass_02 handoff on the current renderer (slide 05, Playwright + `Chart.getChart`):

| Quantity | Measured |
|----------|----------|
| `.chartjs-wrap` box | 709 × 562 |
| Chart.js `chartArea` | left **28**, top **34**, right 709, bottom **531** |
| Bar centers (x) / tops (y) | 97/183, 233/183, 369/84, 505/84, 641/34 |
| Capsule (`value: 11`, domain 0–12) | left **0**, top **47**, width **709** |
| True pixel for value 11 | `34 + (1 − 11/12) × 497` = **75** |
| Chevron (`at: 4`, `bottom: 6%`) | top **506** — i.e. **on** the tick labels (axis bottom 531) |

**Root cause:** `_build_callout_overlays` emits overlay positions as **percentages of the chart
wrap** (`left = from/n`, `width = (to−frm+1)/n`, `top = _value_anchor_pct(...)`, chevron
`left = (at+0.5)/n`), while every quantity the callout refers to lives in **Chart.js
`chartArea` pixel space**. Any axis gutter, legend band, or layout padding shifts the whole
overlay set. Hence: capsule 28 px too high, spanning the full wrap instead of bar-center to
bar-center, stem inheriting the same error, chevron landing over the tick row.

This is a **coordinate-frame bug**, not a missing feature — which is why three rounds of CSS
restyling (#97, #104) never closed it.

---

## 2. R2 target recipe (PDF p6 / slide 05, left board)

1. Blue capsule spanning **from-bar center → to-bar center** (not the full plot width).
2. Capsule pinned vertically to its `value` in **scale pixels** (`scales.y.getPixelForValue`).
3. Left **stem** dropping from capsule bottom to the **from-bar top** (element `y`), in pixels.
4. Right-pointing arrowhead at the capsule end (already correct in CSS).
5. **Large** navy chevron **below** `chartArea.bottom`, centered on the category tick
   (`scales.x.getPixelForValue(at)`), clear of the tick labels.

## 3. Proposed mechanism

**(PROPOSED, D1)** Keep the HTML/CSS overlay chrome and add a config-driven Chart.js inline
plugin that **repositions** the existing overlay nodes from live geometry
(`afterLayout` + `afterDraw`/resize), exactly like the existing `segmentNames` plugin in
`shell.py` (precedent from #108). The renderer keeps emitting the same DOM with its current
percentage styles as a **fail-closed approximation**; the plugin overwrites `left/top/width`
(and the stem's `top/height`) in pixels when it can read scales and bar elements.

Rejected alternative: canvas-draw the callouts inside a plugin. Pixel-exact, but it
reimplements pill/arrowhead/label styling in canvas code, loses Boardroom token theming, and
invalidates the DOM/CSS test contracts from #89/#97/#104.

**(PROPOSED, D2)** No handoff schema change. `callouts` keys (`type`, `from`, `to`, `at`,
`value`, `text`) stay as-is; SC-COMPAT-1 holds and existing decks improve silently.

**(PROPOSED, D3)** The SVG painter path keeps today's percentage approximation. Chart.js is
the IR path; dual-painting exact geometry twice is not worth it.

---

## 4. Ticket map

| Ticket | Gap ID | Pri | Type | Blocked by |
|--------|--------|----:|------|-----------|
| T1 | **R2** callout geometry in chartArea pixels (plugin reposition) | **P0** | bug | — |
| T2 | **N5 residual / F11 packing** — exterior segment-name column density + light dual-card packing (slide 27, 78.60%) | P1 | enhancement | — |
| T3 | **F4+** freestanding pill-column packing finish (slide 02, 90.56%) | P1 | enhancement | — |
| T4 | **N6** provision furniture — freestanding boxed reserve-rate cells + right exterior series legend (slide 14, 86.07%) | P2 | enhancement | — |
| T5 | polish bucket — **R1** flat-stage residual, **R4** hero % type scale, **F12+** annex multi-level headers, **N2** chip weight | P3 | enhancement | — |

T1 is the only ticket with a diagnosed root cause. **(PROPOSED, D4)** T2–T4 each start with a
measurement step (PDF vs render geometry in pixels, like §1) before any CSS is written — the
v6 evidence says "packing short" without numbers, and F11 packing was already once rescoped
after measurement showed bar width was fine (it was axis chrome).

## 5. Acceptance criteria

**T1 (R2)**
- Capsule left/right edges land within ±4 px of the from/to bar centers.
- Capsule vertical center lands within ±4 px of `scales.y.getPixelForValue(value)`.
- Stem spans capsule bottom → from-bar top within ±4 px; omitted (not guessed) when the value
  or domain is unreadable (fail-closed, as today).
- Chevron center within ±4 px of the category tick x, and its top **≥** `chartArea.bottom`.
- Plugin is a no-op without callouts; decks without callouts are byte-identical (SC-COMPAT-1).
- Existing `TestGeometricCallouts` / `TestIrCalloutChrome` / `TestCalloutBandElbowMerge`
  contracts still pass; new geometry assertions driven through Playwright, not regex-only.

**T2–T5** — per-ticket, but each carries: opt-in only (no default visual change unless the
gap is a bug), full-suite green, and the round-3 Q5 done bar: **contract tests plus a fresh
Playwright screenshot of the affected slide** attached to the issue.

## 6. Out of scope

- **R3** Centurion seal / any third-party mark — permanent wontfix (CONTEXT.md brand-asset
  rule, r3 spec Q6). Not a gap, excluded from all counts.
- **Chasing mean MAE.** It is white-canvas biased (89.3% mean while slide 05 sits at 75.9%);
  the delta table and side-by-side compares are the metric.
- Amex-specific code paths. Every fix stays a general, handoff-driven opt-in capability tuned
  to IR house style through Boardroom tokens (the Phase B rule).
- Renderer edits inside a sim run — sims are MEASURE-ONLY; fixes land on gated branches.

## 7. Open questions for the human lock

1. D1 — plugin-reposition vs canvas-draw for R2: confirm plugin-reposition?
2. Ticket granularity: one PR per ticket (Phase B pattern, 9 PRs so far) or bundle T2+T3 as one
   "packing" PR?
3. Is T5 worth doing at all, or should the P3 bucket be closed as accepted divergence? Three
   rounds have each left it "exists but weak" with ~92–95% MAE.
4. Should the next sim (v7) run **before** T2–T4 to get pixel measurements from a fresh pass,
   or do the measuring inside each ticket?
