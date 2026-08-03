# Pass 01 — fresh current-renderer check (v9)

**Base:** v8 pass_03 handoff + three already-shipped levers (N8/R6-B measure_rule, N6 outlined_boxes, N5/F11 bar packing).
**Renderer:** current worktree `impact_slides.renderer_v2` (no production edits).
**Render:** 44 slides OK → `output/presentation.html`.
**Evidence:** `geometry.json` **85/90** (5 fail = N6 cell cx align); focus SBS `compare_{02,05,11,14,16,19,23,27}.png`; `verify_extras.json`.
**Method:** geometry (±4px core; lever tol 8–12px) + SBS reading. **No MAE %.**

## Handoff deltas vs v8 pass_03

| Slide | Change | Hypothesis | Geometry / SBS result |
|------:|--------|------------|------------------------|
| **17** (idx16, PDF p16) | primary callout `band` → `measure_rule` from0–to7, text `17%`, caption `% CAGR` | thin dual-ended rule; pill on rule; caption under | **PASS** — measure present, no band; h=25; left/right = bar0/barN; pill+caption centred |
| **15** (idx14, PDF p14) | `secondary_visual.skin: outlined_boxes` | unfilled gray-stroked plot-aligned boxes; no dup header | **PARTIAL** — skin+unfilled+no thead PASS; plot align FAIL (list-shaped primary labels → aligned=false). Contract miss recorded, no renderer edit |
| **28** (idx27, PDF p28) | both tiles `bar_percentage:0.58`, `category_percentage:1.0`, `fill_tile:true` | denser stacks; wider bars; tile fills wrap | **PASS** knobs — bar% 0.58, cat% 1.0, fill class, wrap/tile 0.878. Residual: badge ≠ tall side FDIC callout (B) |

## Core v8 contracts

All prior 57 v8 assertions re-run and **PASS** (included in 85/90). Failures are only the five new N6 align checks.

## Stop

No further handoff-tunable divergence. Freeze after pass_01. Report → `GAP_ANALYSIS.md`.
