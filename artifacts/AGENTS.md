# artifacts

## Purpose

Committed, reproducible evidence artifacts for source-fidelity and rendering claims.

## Ownership

- Issue-scoped capture/report directories.
- Versioned renderer-3 release evidence under `renderer_3_release/`.
- Package/file architecture diagrams: `renderer-v3-architecture.*` (package) and `renderer_v3_file_architecture/` (per-file).
- Artifacts must include their inputs or refer only to tracked repository inputs.

## Local Contracts

- Capture reports state viewport, source identity, slide/layout identity, and measured geometry.
- Screenshots use the repository's identity-safe probe helpers; never fixed sleeps.
- Do not add generated artifacts unless they prove an issue acceptance condition.

## Work Guidance


## Verification

- Run the capture script in the issue directory and validate its report.

## Child DOX Index

- `issue_156_slide27/AGENTS.md` — archived-v10 and corrected slide-27 paint-ready captures.
- `renderer_3_release/AGENTS.md` — immutable D315 versioned acceptance bundle (3.0.0).
- `renderer_v3_file_architecture/AGENTS.md` — Archify per-file renderer_v3 diagrams; package-level `renderer-v3-architecture.*` stays owned here.
