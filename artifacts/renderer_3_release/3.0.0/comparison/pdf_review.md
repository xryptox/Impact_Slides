# Qualitative PDF review — renderer 3.0.0

Review method: identity-safe 1920×1080 captures plus the user-approved D55/D314
record. Contract probes only; no whole-slide image scoring.

Status: **approved**

## Approved D55 divergences

### DIV-001 — Slide 21 Capital Summary heading
- slide: 21
- contract: D170 / D314 / approval record
- reason: Neutral structural heading `Capital Summary` is authored wording
  required by the schema-v1 hero card; it is not copied from the PDF.
- approval: explicit specification approval

### DIV-002 — Slide 6 approximate six-percentage-point claim
- slide: 6
- contract: D298 / D314 / approval record
- reason: Authored approximate `6` percentage-point measurement is retained as
  a source claim and is not recomputed from displayed endpoints.
- approval: explicit specification approval

### DIV-003 — Adaptive typography and renderer-owned geometry
- slides: 1–44
- contract: D1 / D2 / D10 / D47 / D55
- reason: Role sizes grow only from floors; plot/support allocation and
  collision placement are renderer-owned. Visual scale may differ from the PDF
  wherever fitting rules require it.
- approval: D55 reference-not-pixel-target

### DIV-004 — Transparent flat chart bodies
- slides: chart slides
- contract: D5 / D6
- reason: Chart plot/body fills, decorative borders, and shadows are removed.
  Semantic chrome (title bands, axes, outlined support) remains.
- approval: D5 / D6

## Completeness

All 44 slides were reviewed in both modes. Required facts, identities, units,
precision, notes placeholders, evidence ownership, and disclosure content are
present. No unapproved whole-slide visual scoring was used.
