# Third-party assets vendored by renderer_v2

Inventory of external assets embedded into generated decks. Keep one row per
vendored artifact; update whenever a file under `assets/` changes.

| Asset | Version | License | Source | Obtained via | Notes |
|-------|---------|---------|--------|--------------|-------|
| _(fonts land in P0.3 — see `fonts/`)_ | | | | | |

Process (per `wiki/SPEC_renderer_v2_p0_self_contained.md`):

1. Download from the official upstream release/CDN only.
2. Commit the upstream LICENSE beside the artifact.
3. Record version + source URL here.
4. Re-measure inlined byte size when bumping versions (P1 size matrix).
