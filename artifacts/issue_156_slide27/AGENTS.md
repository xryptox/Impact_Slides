# issue_156_slide27

## Purpose

Reproducible evidence for issue #156: the archived v10 slide 27 paints after #146's readiness gate, and the corrected source handoff paints with all scenarios.

## Ownership

- `archived_v10_handoff.json` — archived 44-slide v10 input used by both captures.
- `evidence_e0026.json` — PDF-page-27 Evidence Register entry cited by the corrected slide.
- `recapture_corrected_slide27.py` — renders archived and corrected inputs at 1920×1080, waits via `wait_for_paint_ready_charts`, and writes the report/screenshots.
- PNGs and `recapture_report.json` — committed visual and geometry evidence.

## Local Contracts

- Capture slide 27 only as `dual_chart` through the identity-safe readiness helper.
- Report two charts with nonzero canvas and chart-area geometry for each input.
- The corrected capture is produced only by `apply_issue_156_slide27_scenarios` on the archived input.

## Work Guidance


## Verification

- `python artifacts/issue_156_slide27/recapture_corrected_slide27.py`
- `python -m pytest -q tests/test_amex_s27_scenarios.py`

## Child DOX Index

- No child AGENTS.md.
