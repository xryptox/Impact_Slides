# wiki

## Purpose

Archive of historical prompts, plans, research, and specs. Not the live engineering contract.

## Ownership

- Historical and draft markdown under `wiki/`
- Reference snapshot: `DELEGATED_WORKFLOW_DETERMINISM.md` (non-binding assessment; live contract remains under `docs/agents/`)
- Research archive: `DELEGATED_WORKFLOW_TOKEN_AUDIT.md` (token-leak findings and fixes for the ticket-wave setup; live contract in root `AGENTS.md` + `docs/agents/delegated-delivery.md`)
- Final active specification: `SPEC_renderer_v3_full_deck_density_and_chart_fidelity.md` (user-approved renderer-v3/schema-v1 contract; implementation tickets may be derived from it; renderer_v2 remains legacy)
- Active parity specification: `SPEC_renderer_v3_pdf_design_parity.md` (proposed; v11→v12 design-regression root-cause analysis + DP-1..DP-6 typography/furniture/domain/verification contract and corpus backfill manifest for the 44-page Amex deck; extends the density spec)
- Generated current index: `renderer_v2_LAYOUTS.md` (owned operationally by renderer_v2 + `scripts/gen_layout_index.py`)
- Operational learnings: `AGENT_LEARNINGS.md` (live document; updated after each wave; pointer in root `AGENTS.md`)

## Local Contracts

- Live agent entry remains root `AGENTS.md`, `CONTEXT.md`, `docs/agents/`, and code under `impact_slides/`
- `AGENT_LEARNINGS.md` is live and binding for delegated-wave work despite living in the archive; do not stale-mark it
- Stale docs carry `> **Superseded - historical...**` immediately under the H1 (see `README.md` policy)
- Do **not** mark without cause: live GPT prompts (`Impact Slide *`), `SPEC_renderer_v2_amex_fidelity_r6.md` (R6-A shipped #139; R6-C still open), current baseline gap docs, verifier corrections (e.g. `baseline_v10_VERIFIER_CORRECTION_146.md`), normative shipped p0–p5/token specs, generated `renderer_v2_LAYOUTS.md`
- Repo-wide `rg` will not read `README.md` — per-file markers matter

## Work Guidance

- Prefer code + root/docs AGENTS over wiki plans when they disagree
- Do not implement from superseded specs

## Verification

- `python scripts/gen_layout_index.py --check` if touching the generated layouts index or its generator inputs

## Child DOX Index

- No child AGENTS.md.
