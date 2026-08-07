# v10 baseline verifier correction (#146)

> **Scope:** Corrects a false slide-12 diagnosis from the archived v10 full-deck comparison. Does **not** rewrite historical raw SBS/HTML/PDF artifacts under `gnhf/objective-produce-an-74065a`.

## False diagnosis

`wiki/baseline_v10_GAP_ANALYSIS.md` (archived commit `950515e`) ledger row for HTML slide **12** / `chart_hero_dual` / PDF P12 classified the left plot as a **source/content** residual:

> chart_hero_dual shows 66%/73% hero stats but left stacked NCA chart missing vs PDF dual-panel — handoff/source pairing residual

Evidence-backed residuals item 1 repeated the same claim ("handoff still omits left stacked NCA chart").

## Root cause (tooling, not handoff)

The v10 comparison helper (`simulation/amex_q1_2026/probes/build_full_comparison.py`) treated a canvas as ready when `Chart.getChart(canvas)` returned an instance. Immediately after activating a previously hidden slide that instance can still have **0×0** geometry. Capturing then produced blank plots that were misread as missing chart content.

Independent paint-ready reactivation of the **same** archived v10 `presentation.html` shows:

| slide | layout | paint-ready geometry |
|------:|--------|----------------------|
| 9 | `line_chart` | one canvas ≈925×652, non-degenerate `chartArea`, painted line elements |
| 12 | `chart_hero_dual` | one stacked-bar canvas ≈1140×755, non-degenerate `chartArea`, three visible series with bar geometry |
| 27 | `dual_chart` | two canvases ≈806×688 each (same readiness race; handoff content residuals for Upside / Q1'27–Q1'28 remain under #156) |

Fresh screenshots: `artifacts/issue_146_paint_ready/`.

## Corrected reading

- **Slide 9 blank plot in archived SBS:** capture race, not a renderer or source gap.
- **Slide 12 "missing left NCA chart" in archived SBS/report:** capture race. The archived handoff **does** include the left stacked NCA chart (`stacked_bar_chart` config with three series / five quarters). After paint-ready settle the plot is present. Withdraw the slide-12 **source/content** residual that was inferred solely from the blank capture.
- Any remaining slide-12 PDF↔HTML content deltas (hero pairing chrome, series labeling, etc.) need a fresh paint-ready comparison; they are not established by the blank v10 SBS alone.
- **Slide 27** blank dual cards in some v10 captures are the same race; #156 owns separate handoff corrections.

## Required tooling fix

Reusable helper: `scripts/simulation_probe.wait_for_paint_ready_charts` (this ticket). Future full-comparison screenshot paths must call it after `activate_slide`.
