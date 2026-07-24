# SPEC — renderer_v2 Amex IR Fidelity Round 2 (Epic Stub)

**Status:** locked by grill-with-docs session 2026-07-20; tickets are canonical for scope/ACs.
**Predecessor:** epic #70 (closed) — Amex Q1'26 IR fidelity F1–F15 round 1.
**Evidence:** `simulation/amex_q1_2026/GAP_ANALYSIS.md` (v2, post-F-feature) vs `simulation/amex_q1_2026_v1_pre_fixes/GAP_ANALYSIS.md` (v1 baseline). Compare shots cited per ticket from `simulation/amex_q1_2026/passes/pass_03/screenshots/`.

## v1 → v2 outcome

Round 1 closed F2/F5/F7/F8/F9/F13/F14 and largely resolved F1/F4/F6/F10/F11/F12/F15. Mean MAE 86.19% → 89.25% (white-biased; trend only). Brand dividers jumped ~20% → ~85%+.

**Key finding:** F3 (below-axis negative stacks) was misdiagnosed in both gap docs. Root cause: `strip_eids()` in `impact_slides/renderer_v2/strip.py` ends with `.strip(" ,;|-")`, which strips leading minus signs from **string** numerals (`"-73"` → `"73"`) on the `normalize_handoff` load path. The round-1 signed-stacking painter (#72) is correct — verified by rendering the raw slide: `[-73.0, 222.0, ...]` — but never receives signed data because real handoffs encode values as strings. Round-1 tests used numeric `-73`, which survives scrubbing.

## Locked decisions (grilling Q1–Q9)

1. **Q1:** F3 ships as a standalone `bug` ticket (data corruption on the load path, broader than charts), Wave 0.
2. **Q2:** Full catalog — all 10 remaining gap items (F3, R1, F10+, R2, F11+, F4+, F6+, R3, F12+, R4).
3. **Q3:** New epic with labels `fidelity`, `renderer-v2`, `bug`/`enhancement`, `ready-for-agent`; #70 referenced as predecessor.
4. **Q4:** 8 children — F3 / F10+ / R2 / F11+ / F4+ / F6+ / R3 / polish bundle (R1 + F12+ + R4). F10+ and R2 kept separate (painter vs chrome surfaces); polish items bundled to avoid tracker spam.
5. **Q5:** Only F3 is `bug`. All others `enhancement`, including F6+ (`normalize_handoff` behaves per documented design; `brand_cover` at index 0 is a new supported configuration).
6. **Q6:** Waves — W0: T1; W1: T2 ∥ T3; W2: T4; W3: T5; W4: T6 → T7; W5: T8. Edges: T2←T1, T3←T1, T4←T2, T5←T4, T6←T5, T7←T6, T8←T2. Frontier at filing: T1 only.
7. **Q7:** Done bar = automated contract tests (DOM/SVG/Chart-config markers) **plus a sim re-run of the affected Amex slides with the compare-shot delta recorded on the issue**. No CI MAE gate (white-bias caveat stands).
8. **Q8:** For horizontal bars, the SVG fallback paints basic horizontal geometry (orientation is geometry, not a cue); anniversary-window polish (discontinuous axis, inside-bar labels) is Chart.js-only. Chart.js stays canonical.
9. **Q9:** Horizontal bars are a new layout type `horizontal_bar_chart` (consistent with the chart taxonomy; feature detection via `is_chart_layout`). `chart_config` gains only `bar_labels_inside`; the existing `y_axis_break` field covers the discontinuous window.

## Ticket map

| # | Gap | Title | Label | Wave | Blocked by |
|---|-----|-------|-------|-----:|------------|
| T1 | F3 | Load path strips negative signs from string numerals | bug | 0 | — |
| T2 | F10+ | `horizontal_bar_chart` + anniversary retention window | enhancement | 1 | T1 |
| T3 | R2 | Geometric callout layer (elbow arrows, chevrons) | enhancement | 1 | T1 |
| T4 | F11+ | IR dual tall-card multi_panel recipe | enhancement | 2 | T2 |
| T5 | F4+ | Freestanding pill statement columns | enhancement | 3 | T4 |
| T6 | F6+ | Cover-seal load path (brand_cover at slide 1) | enhancement | 4 | T5 |
| T7 | R3 | First-class brand mark/seal asset pack | enhancement | 4 | T6 |
| T8 | R1/F12+/R4 | Fidelity polish bundle (stage chrome, annex headers, hero type scale) | enhancement | 5 | T2 |

Edges are priority gates (wave ordering), not hard code dependencies.

## Out of scope

- Re-litigating round-1 decisions (Chart.js canonical, chrome level, chart_config minimal surface).
- CI visual-regression / MAE gating.
- Amex-specific hardcoding — all capabilities ship as generic renderer features (IR-style recipes, not "Amex mode").
- Sim harness changes beyond what each ticket's re-run AC needs.
