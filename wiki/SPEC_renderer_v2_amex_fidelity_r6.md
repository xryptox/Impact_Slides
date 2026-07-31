# Renderer v2 — Amex fidelity round 6 (DRAFT — mechanisms PROPOSED, pending human lock)

Status: **DRAFT.** Diagnoses are measured and trustworthy; mechanisms are
proposals and must not be implemented before a human lock. Round 5 is LOCKED and
fully shipped (T6–T14), so new tickets land here rather than reopening it.

Baseline: `wiki/baseline_v8_GAP_ANALYSIS.md`. Artifacts branch:
`origin/gnhf/objective-produce-a-b7e827`.

Shipped since the v8 sim (all merged to `main`, full suite **1310 passed, 15
skipped**):

| PR | ticket | what shipped |
|---|---|---|
| #122 | N5/F11 | opt-in `bar_percentage` / `category_percentage` / `fill_tile` |
| #123 | N8, R2 | `measure_rule` callout type; `elbow_arrow` `style:"line"` variant |
| #124 | N10, R4 | `dual_chart` two separate cards; hero as ONE framed panel (2:1) |
| #125 | F4+, N6 | pill type scale to PDF 28px; opt-in `skin:"outlined_boxes"` |

---

## R6-A — chart-internal typography is roughly half PDF scale (slide 16, PDF p16)

**Type B (renderer capability). Priority P1.**

This is the residual visible in the slide-16 side-by-side after #123/#124
landed. It is **pre-existing, not a regression**: verified identical on
`origin/main` before PR #124 by rendering both and comparing crops. It sat
unfiled because every previous round scoped slide 16 to callout chrome
(N8) or card structure (N10), never to the type inside the plot.

### Measured, PDF (`get_text("dict")`, sizes ×2.001 to our 1920×1080 stage) vs live render

| element | PDF | ours | how ours is set |
|---|---:|---:|---|
| pane title | **40px bold** | **13px**, weight 600, gray `rgb(99,102,106)` | `.gl-tile-label` (CSS) |
| bar value label | **28px bold** | **11px bold** | Chart.js `plugins.datalabels.font.size` |
| x tick | — | **13px** | `scales.x.ticks.font.size` |
| y tick | **24px bold** | **13px** | `scales.y.ticks.font.size` |
| line value label | **28px bold** | 11px bold | datalabels |
| CAGR pill | 24px | (n/a — see R6-B) | — |
| `% CAGR` caption | 24px | (n/a — see R6-B) | — |

So three independent scales are all far too small: the CSS pane heading
(13 vs 40), the Chart.js tick fonts (13 vs 24), and the datalabel font
(11 vs 28). The pane title is additionally the **wrong colour and weight** —
gray 600 where the PDF is navy bold, reading as a caption rather than a heading.

Note this is the *same* underlying complaint as F4+ (#125), which found
`pill_comparison` text at 15–17px against a PDF 28px. F4+ fixed one recipe's
CSS; R6-A is the chart-internal equivalent and covers **every chart**, not just
slide 16 — so its blast radius is much larger than F4+'s.

### Proposed mechanism (NOT locked)

Two candidate shapes, and the choice is a real trade-off:

1. **Raise the defaults.** Honest about the fact that 11–13px type on a
   1920×1080 stage viewed as a slide is simply too small, and fixes every deck
   at once. But it is an unconditional restyle of every chart in every existing
   deck, and several pinned tests assert current sizes.
2. **Opt-in `chart_config` font-scale knobs** (e.g. `tick_font_size`,
   `label_font_size`, plus a `gl-tile-label` scale) defaulting to today's
   values, preserving SC-COMPAT-1 byte-identity.

**Recommendation: (1) for the pane title specifically** — 13px gray 600 vs 40px
navy bold is not a taste difference, and T11 (#119) introduced that heading only
last round, so little depends on its current size. **(2) for the Chart.js tick
and datalabel sizes**, because those are read by every chart on every slide and
an unconditional bump risks overflow/collision on dense boards (the annex tables
and multi-panel tiles are the obvious hazards).

A measurement step is mandatory before implementing, per r4 D4/D10 — three
tickets on this deck (R4, N5, F4+) had their filed framing disproved by
measurement, and R4 was specifically mis-scoped as a type-scale gap **twice**.
Do not assume this one is right either: confirm against the PDF first, and check
whether raising tick sizes forces Chart.js to drop or rotate tick labels.

### Acceptance (proposed)

- Pane title within ±2px of PDF 40px, navy, bold.
- Tick and value-label sizes within ±2px of the PDF figures above.
- No clipped/dropped/rotated ticks on any of the 44 v8 slides — enumerate and
  eyeball, do not sample.
- SC-COMPAT-1 stated explicitly per sub-change: which are unconditional and
  which are opt-in.
- Full suite green (baseline **1310 passed, 15 skipped**) — the FULL suite, not a
  file-scoped subset; token-audit tests have twice landed failures on `main`
  because only chart tests were run.

---

## R6-B — slide 16 still declares `band`, not the shipped `measure_rule`

**Type A (handoff lever). Not a renderer gap. No implementation ticket.**

The live slide-16 render shows the CAGR chrome as a translucent full-height box
(`.chartjs-callout-band`, measured **666×642**, `rgba(0,23,90,0.06)`) because the
v8 pass_03 handoff declares `callouts: [{type: "band", from: 0, to: 7, text:
"17% CAGR"}]`.

PR #123 shipped `measure_rule` precisely to replace this, and it is verified
working (thin navy rule spanning bar centres, arrowheads both ends, blue pill,
gray caption). The frozen sim handoff simply predates it.

**Action: none in the renderer.** The next sim run should declare
`measure_rule` (with `text` and `caption`) on slide 16 instead of `band`. Recorded
here only so the next run does not re-file it as a renderer gap — the same trap
that had R3 and the annex transcription defect scored as renderer bugs for
several rounds.

---

## R6-C — `.gl-inset` outlined-box skin

**Type B. Priority P3 (cosmetic). Carried forward from v8, still unverified.**

Ours: `.gl-inset card` 200×90, solid navy `rgb(0,23,90)`. The PDF's VCE box
appears to be an outlined box, not a solid navy pill.

**Blocked on measurement, deliberately.** Neither I nor the round-6 worker could
extract a matching vector rect from PDF p19 to establish the recipe with
confidence. T12 (#118) already fixed the collision (zero overlaps deck-wide);
only the skin is open, and only slides 19 and 23 emit `.gl-inset`.

Do not restyle this on assumption. Either establish the PDF recipe first, or
leave it as accepted divergence. An unverified restyle is worse than a known
cosmetic divergence.

---

## Still-open backlog after round 6 (for the next sim baseline)

| Pri | item | type | note |
|---:|---|---|---|
| **P1** | R6-A chart-internal typography | B | this spec; largest remaining visual gap |
| **P3** | R6-C inset outlined skin | B | blocked on measurement |
| **P3** | F5 theme cannot tint default chart palette | B | r5 spec; do not pick up until its trigger fires |

Closed as accepted divergence (do **not** re-file): R1 flat-stage residual,
F12+ annex multi-level headers, N2 chip weight (r4 D11); R2 elbow L-bracket arm
(r5 L3); R3 Centurion seal (permanent wontfix, r3 Q6 — original artwork only).

Known non-renderer defect: annex slides 33–36 are a **vision transcription**
failure (real 4-column tables flattened to Item/Detail key-value pairs), not a
renderer gap. `scripts/run_amex_simulation.sh` carries mandatory table
transcription rules for this.
