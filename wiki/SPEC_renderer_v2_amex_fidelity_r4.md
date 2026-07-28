# SPEC: Amex Q1'26 IR fidelity — round 4 (v6 residual gaps)

**Status:** LOCKED — alignment record from the 2026-07-26 grilling session (D1–D11 below).
The measured diagnosis in §1 is fact; §3 records the locked mechanism.

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

## 3. Locked decisions (grilling D1–D11)

1. **D1 — DOM-reposition, not canvas-draw.** Keep the HTML/CSS callout chrome (Boardroom
   tokens, CSS `::after` arrowhead, token-themed pill) and add a config-driven Chart.js inline
   plugin that overwrites the overlay nodes' geometry. Canvas-draw was rejected: it
   reimplements rounded rects/triangles/fonts in `ctx`, loses token theming, and invalidates
   the #89/#97/#104/#114 DOM+CSS contracts. Noted asymmetry: the `segmentNames` precedent
   (#108) *is* canvas-draw, so this is a deliberate second pattern.
2. **D2 — better static approximation + plugin refinement.** The renderer emits improved
   server-side positions (span from bar-center fractions rather than raw category edges) so
   overlays are close without JS; the plugin then writes exact pixels. Rejected
   hide-until-positioned (would drop callout text entirely with JS off, and the `<noscript>`
   SVG fallback carries no callouts).
3. **D3 — T1 covers the three callout types only** (`elbow_arrow` + stem, `chevron`, `band`):
   one code path (`_build_callout_overlays`), one test surface. `chartjs-annotation` (#71) and
   `chartjs-axis-break` (#79) share the same frame bug but have **no data anchor in the
   handoff** — anchoring them is a feature, filed separately.
4. **D4 — geometry travels both ways.** Add `data-value` to the elbow and `data-for` to the
   stem, **and** serialize `options.plugins.callouts` items. The config is built **after** the
   #114 band-absorption merge so the two copies cannot drift.
5. **D5 — per-node pixel writes** (`style.left/top/width/height`). Rejected plot-area CSS
   variables + `calc()`: it would rewrite every callout rule and re-trip the token-discipline
   audits (`test_no_literal_px_spacing_outside_tokens`, hardcoded-radius audit) that already
   bit this file twice.
6. **D6 — `afterLayout` only**, and the plugin **no-ops on a zero-size `chartArea`**. The deck
   scales by CSS transform on `.deck-stage`, so the wrap's layout box is stable at 1920×1080
   and only Chart.js re-layout moves `chartArea`; hidden (`display:none`) slides can lay out
   degenerate first, which must not produce garbage pixels.
7. **D7 — vertical orientation only.** The plugin no-ops on `horizontal_bar_chart`, which keeps
   today's approximation. No real handoff has a horizontal-bar callout (v6 deck: exactly one
   callout set, on a vertical grouped bar in a `multi_panel` tile), so there is no PDF recipe
   and no testable target; adding it later is ~20 lines.
8. **D8 — verification is manual Playwright + a screenshot on the PR** (round-3 Q5 done bar);
   automated tests stay pure-Python. An opt-in browser-driven geometry test is filed as a
   **follow-up**, deliberately not bundled: it would be the repo's first browser test (no CI is
   configured) and would swamp a ~60-line fix. Acknowledged risk: #97 and #104 both passed
   regex contracts while being visually wrong — that is why the follow-up exists.
9. **D9 — T1 ships alone**, gated and merged before anything else starts.
10. **D10 — T2 (N5 packing) is scheduled next**; T3/T4 are filed with evidence but unscheduled,
    and each requires a pixel-measurement step before pickup.
11. **D11 — R1, F12+, and N2-weight are closed as accepted divergence** (see §6), with a
    sim-prompt exclusion note so future workers stop reporting them. R4 stays open as P3.

## 4. Ticket map

| Ticket | Gap ID | Pri | Type | Blocked by |
|--------|--------|----:|------|-----------|
| T1 | **R2** callout geometry in chartArea pixels (plugin reposition) | **P0** | bug | — |
| T2 | **N5 residual / F11 packing** — exterior segment-name column density + light dual-card packing (slide 27, 78.60%) | P1 | enhancement | — |
| T3 | **F4+** freestanding pill-column packing finish (slide 02, 90.56%) | P1 | enhancement | — |
| T4 | **N6** provision furniture — freestanding boxed reserve-rate cells + right exterior series legend (slide 14, 86.07%) | P2 | enhancement | — |
| T5 | **R4** hero % type scale (slide 11, 85.67%) — specific target: giant ~110px digits, smaller unit glyph, caption right | P3 | enhancement | — |
| F1 | follow-up: `chartjs-annotation` data anchor (needs new handoff keys) | P2 | enhancement | after T1 |
| F2 | follow-up: `chartjs-axis-break` glyph anchored to the break value | P3 | enhancement | after T1 |
| F3 | follow-up: opt-in Playwright geometry test (repo's first browser test) | P2 | test | after T1 |

**Schedule:** T1 → T2. T3/T4 filed-not-scheduled (measurement step first). T5/F1–F3 backlog.

T1 is the only ticket with a diagnosed root cause. Per D10, T2–T4 each start with a
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
- **R1** (flat-stage residual, 92.62%), **F12+** (annex multi-level headers, ~91–95%), and
  **N2 chip weight** — **closed as accepted divergence (D11)**. All three were fixed once
  (#113, #114) and returned as "exists but weak". R1 and F12+ sit inside the noise band of a
  white-biased metric, so a fix is unfalsifiable; N2 chips are already bold/14px and going
  heavier risks looking wrong on non-Amex decks. Excluded in the sim prompt like R3.
- **Chasing mean MAE.** It is white-canvas biased (89.3% mean while slide 05 sits at 75.9%);
  the delta table and side-by-side compares are the metric.
- Amex-specific code paths. Every fix stays a general, handoff-driven opt-in capability tuned
  to IR house style through Boardroom tokens (the Phase B rule).
- Renderer edits inside a sim run — sims are MEASURE-ONLY; fixes land on gated branches.

## 7. Provenance

Locked in the 2026-07-26 grilling session (11 decisions, one branch at a time). Facts checked
during grilling that changed proposals: the `segmentNames` precedent is canvas-draw not
DOM-reposition (D1 taken anyway, deliberately); the stem div carries no `data-for` and the
elbow no `data-value` (D4); no repo test uses Playwright and no CI is configured (D8); only
one slide in the 44-slide v6 deck declares callouts, on a vertical chart (D7).
