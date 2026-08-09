# renderer_v3

## Purpose

Schema-v1 canonical rendering kernel for Impact Slide Renderer 3. Sibling of frozen legacy `renderer_v2`. This delivery owns typed validation into one canonical deck model; painting/planning land in later tickets.

## Ownership

- Closed schema-v1 handoff models (`models.py`)
- Aggregating validation + allowlisted non-strict repairs (`validate.py`, `repairs.py`, `diagnostics.py`)
- Generated JSON Schema artifact `schema/handoff_schema_v1.json` (D121)
- Does **not** own legacy v2 layouts, recipes, charts, or migration of unversioned handoffs (D119 is a later tool)

## Local Contracts

- Public API: `from impact_slides.renderer_v3 import validate_handoff, RendererValidationError`
- `validate_handoff(raw, *, strict=True) -> ValidationResult` with `.deck` as the only paint input (D122)
- Strict aggregates all detectable errors into `RendererValidationError.events` (D120/D309/D310)
- Non-strict applies only `repairs.REPAIR_REGISTRY` actions, then revalidates (D123/D311)
- Kernel compositions: `opening_cover`, `narrative`, `closing_cover` (D210/D251/D268/D270)
- Envelope: `meta`, `sections`, `number_formats`, `evidence_registry`, `slides` (D211)
- Must not import `impact_slides.renderer_v2` or mutate v2 behavior
- Schema artifact is generated: `python -m impact_slides.renderer_v3.schema_export` (write) or `--check` (CI)

## Work Guidance

- Extend typed models first; regenerate schema; never hand-edit the JSON Schema
- New compositions need payload models + discriminator entry + tests before paint
- Prefer root-cause validation in `Deck` / slide model validators over caller guards
- Diagnostics stay closed (D309 codes/actions/results); no free-form stderr interface
- Share only genuinely immutable, version-neutral assets through a neutral module — never reach into v2 implementation packages

## Verification

- `python -m pytest -q tests/test_renderer_v3_kernel.py`
- `python -m impact_slides.renderer_v3.schema_export --check`
- Full suite: `python -m pytest -q`
- CI: schema drift step + pytest in `.github/workflows/ci.yml`

## Child DOX Index

- No child AGENTS.md — `schema/` is a generated artifact directory, not an operating boundary.
