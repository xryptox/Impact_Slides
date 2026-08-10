# renderer_v3

## Purpose

Schema-v1 canonical rendering kernel for Impact Slide Renderer 3. Sibling of frozen legacy `renderer_v2`. Owns typed validation into one canonical deck model, deck-wide measure/plan freeze for kernel prose/chrome, deterministic five-artifact publication, and the sole boardroom_amex theme manifest (CSS/Chart.js/SVG tokens); full chart painting lands in later tickets.

## Ownership

- Closed schema-v1 handoff models (`models.py`)
- Aggregating validation + allowlisted non-strict repairs (`validate.py`, `repairs.py`, `diagnostics.py`)
- Deck-wide adaptive measure/plan freeze (`plan.py`) for narrative prose, subtitles, takeaways, disclosures, source footers, and fixed chrome (D1–D4, D22, D59, D68–D70)
- Public `render_deck` + CLI publication (`render.py`, `publish.py`, `cli.py`)
- Generated JSON Schema artifact `schema/handoff_schema_v1.json` (D121)
- Canonical `boardroom_amex` theme manifest + generated CSS (`theme/`, `theme_export.py`) and self-contained licensed webfonts (`assets/fonts/`) (D127-D133)
- Does **not** own legacy v2 layouts, recipes, charts, or migration of unversioned handoffs (D119 is a later tool)

## Local Contracts

- Public API: `from impact_slides.renderer_v3 import render_deck, validate_handoff, RendererValidationError, RendererConfigurationError, RendererPublicationError`
- CLI: `python -m impact_slides.renderer_v3 --handoff PATH --out DIR` (strict default; `--no-strict`, `--debug`, `--svg-only`); `schema --check` / bare `--check` retain the D121 drift gate
- `validate_handoff(raw, *, strict=True) -> ValidationResult` with `.deck` as the only paint input (D122)
- `plan_deck(deck, *, strict=True) -> DeckPlan` freezes whole-pixel role sizes at 1920×1080 before paint; strict overflow → `RendererValidationError` / `plan.unresolved_overflow`; non-strict paints complete floor-size text degraded (D59/D69/D312)
- `render_deck(handoff_path, out_dir, *, strict=True, ...)` validates → plans → publishes exactly five UTF-8/LF artifacts: `presentation.html`, `slide_notes.md`, `evidence_manifest.json`, `run_meta.json`, `handoff_schema_v1.json` (D250)
- Clean → exit 0 / `ok: true`; degraded non-strict → exit 2 / `ok: false`; failed → typed error, exit 1, prior output untouched (D112/D312)
- HTML surfaces carry compact `data-plan-sizes` / `data-plan-adaptations` plus projected `data-diagnostic-codes` / `data-diagnostic-count` from `DiagnosticEvent.surface_id`; `run_meta.plans` holds one entry per planned surface (D21/D312)
- Speaker notes are exact root plain text (D173/D221): no trim/synthesis; whitespace-only rejected; HTML `<aside class="notes">` matches `slide_notes.md` after unescape; notes CSS is `display:none;white-space:pre-wrap` (off-slide)
- Evidence registry + slide `evidence_ids` / optional `source_footer` (D175–D176/D216–D217): manifest keeps full registry + nested key-sorted locators; visible footers paint authored-order `source_name` only (never IDs/locators); strict rejects normalized-duplicate footer names; non-strict `repair_source_footer_names` keeps first
- Disclosure is native `<details>` accordion (D174/D222/D289): deterministic `slide-{n}-{surface_id}` IDs, initially closed, print CSS expands bodies; no-JS markup remains complete
- Takeaway outer reservation includes label/pad/border/outer margin; text fitter uses the inner box only. Cover elements measure at their own frozen role sizes. Paragraph/list margins match paint per CSS block box. Planning uses calibrated Source Sans 3 metrics, diagnoses conservative unsupported-glyph fallback, and publication embeds the vendored font.
- Strict aggregates all detectable errors into `RendererValidationError.events` (D120/D309/D310)
- Non-strict applies only `repairs.REPAIR_REGISTRY` actions, then revalidates (D123/D311); `repair_disclosure_sections` drops malformed/duplicate D222 sections (keep first); `repair_source_footer_names` drops later duplicate visible footer names
- `_wrap_lines` breaks at spaces and after `-,:;.` when more content follows; paint inserts matching `<wbr>` via `_soft_break_html` (R178-029). Disclosure units measure summary/list indent separately from full-width paragraphs
- Print media expands closed disclosures and resets viewport stage scale to fixed 1920×1080
- Kernel compositions: `opening_cover`, `narrative`, `closing_cover` (D210/D251/D268/D270)
- Envelope: `meta`, `sections`, `number_formats`, `evidence_registry`, `slides` (D211)
- Must not import `impact_slides.renderer_v2` or mutate v2 behavior
- Schema artifact is generated: `python -m impact_slides.renderer_v3.schema_export` (write) or `--check` (CI)
- Theme CSS artifact is generated from the Python manifest: `python -m impact_slides.renderer_v3.theme_export` (write) or `--check` (CI); painters resolve colors via `theme.resolve_color` / CSS `var(--color-*)` only (D129-D131)
- Chart plot/body surfaces stay transparent and flat via generated `.chart-plot`/`.chart-body` rules (D5/D6)

## Work Guidance

- Extend typed models first; regenerate schema; never hand-edit the JSON Schema
- New compositions need payload models + discriminator entry + plan roles + tests before paint
- Prefer root-cause validation in `Deck` / slide model validators over caller guards
- All adaptive sizing goes through `plan.py`; painters consume frozen `role_sizes` only — no runtime replanning
- Diagnostics stay closed (D309 codes/actions/results); no free-form stderr interface
- Publication stages all five artifacts then replaces; never partial writes to `out_dir`
- Share only genuinely immutable, version-neutral assets through a neutral module — never reach into v2 implementation packages
- Theme tokens change only in `theme/` manifest; regenerate CSS; never hand-edit `boardroom_amex.tokens.css` or put raw theme hex in painters

## Verification

- `python -m pytest -q tests/test_renderer_v3_kernel.py tests/test_renderer_v3_publish.py tests/test_renderer_v3_theme.py tests/test_renderer_v3_plan.py`
- `python -m impact_slides.renderer_v3.schema_export --check`
- `python -m impact_slides.renderer_v3.theme_export --check`
- Full suite: `python -m pytest -q`
- CI: schema + theme CSS drift steps + pytest in `.github/workflows/ci.yml`

## Child DOX Index

- No child AGENTS.md — `schema/` is a generated artifact directory; `theme/` is the theme package (manifest + generated CSS), not a separate operating boundary.
