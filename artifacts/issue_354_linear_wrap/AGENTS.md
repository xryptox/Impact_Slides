# issue_354_linear_wrap

## Purpose

1920×1080 HTML recapture of layout-stress 14x10 process_flow / timeline / data_pipeline slides after kernel wrap packing (#354).

## Ownership

- `recapture_linear_wrap.py` — strict-renders the extracted 30-slide fixture and writes named PNGs plus `recapture_report.json`.
- `html/*.png` — identity-safe 1920×1080 screenshots of s001–s006, s011–s020, s051–s060.
- `recapture_report.json` — viewport, source hashes, layout identity, wrap vs overflow classification.

## Local Contracts

- Source fixture is `tests/fixtures/renderer_v3/linear_wrap_stress.json` (extracted from `gnhf/objective-stress-tes-430fd8` layout-stress 14x10; no D314 rewrite).
- Capture uses Playwright at 1920×1080, `deviceScaleFactor=1`; no image scoring.
- s005 / s016 / s017 / s020 / s055 / s059 must paint the recipe (not list fallback). s056 may wrap or remain overflow.

## Work Guidance


## Verification

- `python artifacts/issue_354_linear_wrap/recapture_linear_wrap.py`
- `python -m pytest -q tests/test_renderer_v3_linear_grouping.py`

## Child DOX Index

- No child AGENTS.md.
