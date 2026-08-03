# wiki

## Purpose

Archive of historical prompts, plans, research, and specs. Not the live engineering contract.

## Ownership

- Historical and draft markdown under `wiki/`
- Generated current index: `renderer_v2_LAYOUTS.md` (owned operationally by renderer_v2 + `scripts/gen_layout_index.py`)

## Local Contracts

- Live agent entry remains root `AGENTS.md`, `CONTEXT.md`, `docs/agents/`, and code under `impact_slides/`
- Stale docs carry `> **Superseded - historical...**` immediately under the H1 (see `README.md` policy)
- Do **not** mark without cause: live GPT prompts (`Impact Slide *`), `SPEC_renderer_v2_amex_fidelity_r6.md` (draft), current baseline gap docs, normative shipped p0–p5/token specs, generated `renderer_v2_LAYOUTS.md`
- Repo-wide `rg` will not read `README.md` — per-file markers matter

## Work Guidance

- Prefer code + root/docs AGENTS over wiki plans when they disagree
- Do not implement from superseded specs

## Verification

- `python scripts/gen_layout_index.py --check` if touching the generated layouts index or its generator inputs

## Child DOX Index

- No child AGENTS.md.
