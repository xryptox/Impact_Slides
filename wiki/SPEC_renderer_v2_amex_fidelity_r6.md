# Renderer v2 — Amex fidelity round 6

Status: **partially shipped.** Diagnoses remain measured fact. **R6-A is
decision-locked and shipped** (issue #139). R6-B is a handoff lever (no renderer
work). R6-C stays open/blocked. Round 5 is LOCKED and fully shipped (T6–T14).

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

## R6-A — chart-internal typography — **shipped (#139)**

**Type B (renderer capability). Priority P1. Locked on issue #139; implemented.**

Live operating contract: `impact_slides/renderer_v2/AGENTS.md` (pane titles +
`chart_config.typography`). Owner module: `charts/typography.py`. Tests:
`tests/test_chart_typography_r6a.py`. Synthetic audit note (not full archived-v9):
`artifacts/r6a_typography_v9_audit.md`.

### Pre-fix measured residual (PDF p16 / deck slide 17)

| element | PDF | pre-fix | how it was set |
|---|---:|---:|---|
| pane title | **40px bold navy** | **13px**, weight 600, gray | `.gl-tile-label` (CSS) |
| bar/line value label | **28px bold** | **11px bold** | Chart.js datalabels |
| x tick | — | **13px** | `scales.x.ticks.font.size` |
| y tick | **24px bold** | **13px** | `scales.y.ticks.font.size` |

### Locked mechanism (shipped)

1. **Unconditional shared pane title** on hosts that already emit a distinct
   pane/tile/card heading (`dual_chart`, `chart_hero_dual`, `multi_panel`):
   HTML-owned `.gl-chart-pane-title` at 40px/700/navy. Ordinary non-chart
   `.gl-tile-label` stays 13px gray. Hosts pass `chart_host_size(...)`; if
   remaining canvas would fall under 320×240, `strict=True` fails and
   `strict=False` keeps legacy one-line title + warning.
2. **Opt-in `chart_config.typography`** (`x_tick_font_size` 8–24,
   `y_tick_font_size` 8–28, `datalabel_font_size` 8–32). Absent group → legacy
   Chart.js 13/13/11 (SC-COMPAT-1). Invalid group: strict raises; non-strict
   drops whole group + warns. Ticks on Chart.js + SVG painters;
   `datalabel_font_size` + collision only on ordinary-label layouts
   (`grouped_bar_chart` / `line_chart` with `point_labels`).
3. **Opt-in collision suppression** when `datalabel_font_size` is set: keep
   earlier series then category; 2px margin; Chart.js actual bounds +
   `data-datalabel-suppressed`; SVG estimated boxes + stderr/`run_meta.warnings`.

### Acceptance (locked)

- Pane hosts emit 40px/700/navy `.gl-chart-pane-title` (legacy fallback path covered).
- Opt-in typography bounds/invalid/unsupported + both painter paths covered by tests.
- Collision ordering/diagnostics covered; boot only when `datalabel_font_size` set.
- Full suite + `gen_layout_index.py --check` green.
- **Outstanding (explicit):** full 44-slide **archived v9** audit on real Amex
  handoff/deck — synthetic contract audit only so far
  (`artifacts/r6a_typography_v9_audit.md`).

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
| — | ~~R6-A chart-internal typography~~ | B | **shipped #139** (archived-v9 full audit still outstanding) |
| **P3** | R6-C inset outlined skin | B | blocked on measurement |
| **P3** | F5 theme cannot tint default chart palette | B | r5 spec; do not pick up until its trigger fires |

Closed as accepted divergence (do **not** re-file): R1 flat-stage residual,
F12+ annex multi-level headers, N2 chip weight (r4 D11); R2 elbow L-bracket arm
(r5 L3); R3 Centurion seal (permanent wontfix, r3 Q6 — original artwork only).

Closed handoff defect (do **not** re-file as renderer): annex slides 33–37 were a
**vision transcription** failure (real multi-column tables flattened to
Item/Detail key-value pairs). Restored by type-(A) handoff mutation
`apply_issue_157_annex_matrices` (#157); contract
`tests/test_amex_annex_33_37_handoff.py`. Next fidelity pass must run
`amex_handoff_mutations.apply_all` (see `scripts/AGENTS.md`).
`scripts/run_amex_simulation.sh` still carries mandatory table transcription
rules so new handoffs do not regress.
