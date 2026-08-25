# wiki

## Purpose

Archive of historical prompts, plans, research, and specs. Not the live engineering contract.

## Ownership

- Historical and draft markdown under `wiki/`
- Reference snapshot: `DELEGATED_WORKFLOW_DETERMINISM.md` (non-binding assessment; live contract remains under `docs/agents/`)
- Research archive: `DELEGATED_WORKFLOW_TOKEN_AUDIT.md` (token-leak findings and fixes for the ticket-wave setup; live contract in root `AGENTS.md` + `docs/agents/delegated-delivery.md`)
- Final active specification: `SPEC_renderer_v3_full_deck_density_and_chart_fidelity.md` (user-approved renderer-v3/schema-v1 contract; implementation tickets may be derived from it; renderer_v2 remains legacy)
- Active parity specification: `SPEC_renderer_v3_pdf_design_parity.md` (proposed; v11→v12 design-regression root-cause analysis + DP-1..DP-7 typography/furniture/domain/verification/geometry contract and corpus backfill manifest for the 44-page Amex deck; extends the density spec; DP-6 helpers + v13 launcher shipped in #233; #249 extends DP-6 ledger probes; DP-7 stub-slack + sparse occupancy shipped in #246; observation sim still unrun; #247 records the category-aligned support chrome override and unmarked legal paragraph grouping; #256 accepted D167 hide_header + hairline body on remaining category-aligned fixtures; #269 retargets Amex s4/s19 to independent navy-header tables; #257 repeats the part-1 legal title and raises fixed legal type to 56/21; #260 authors s12/s15/s21 `stack_segments: show`; #255 records s4/s19 series identity, PDF ticks, s8 FHR step, Leap Year/G&S–T&E facts, and the s38 preamble; #254 records s24 `placement: above` groups + outlined %-of-total; #273 lands hero/`metric_overview` body at 27px with wrapping KPI labels; #271 folds s18 Volume/Margin into one driver label)
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
