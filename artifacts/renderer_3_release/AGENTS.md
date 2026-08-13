# renderer_3_release

## Purpose

Immutable versioned acceptance evidence for Impact Slide Renderer 3. D315 owns the tree; 3.0.0 is the first shipped directory.

## Ownership

- `3.0.0/` — hash-pinned 3.0.0 bundle: inputs, both D250 render roots, contracts, comparison, checksums
- Does **not** own renderer code; `scripts/renderer_3_release.py` builds and verifies this tree

## Local Contracts

- Layout is exactly D315. `chartjs/render/` and `svg/render/` each contain only the five D250 files.
- `acceptance_manifest.json`, `README.md`, and `checksums.sha256` are the only unlisted files.
- Required gates must be `passed`. No whole-slide MAE/SSIM/similarity scoring.
- Evidence is immutable; a correction is a new renderer-version directory.

## Work Guidance

- Rebuild with `python scripts/renderer_3_release.py --pdf PATH --build`
- Do not hand-edit hashes, screenshots, or run_meta

## Verification

- `python scripts/renderer_3_release.py --verify`
- `pytest -q tests/test_renderer_v3_release_evidence.py`

## Child DOX Index

- No child AGENTS.md — `3.0.0/` is a version payload, not a separate operating boundary.
