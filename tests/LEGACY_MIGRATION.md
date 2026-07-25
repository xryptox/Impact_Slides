# Legacy preprocessor baseline removal — migration record

Completes PR #107 (which deleted `wiki/legacy/step1_preprocessor{,_v2_full,_v3}.py`
but left the root shims and all dependent tests, turning main red with 20
collection errors). User decision: **complete** the deletion, not revert.

Deleted entry shims: `step1_preprocessor.py`, `step1_preprocessor_v2_full.py`,
`step1_preprocessor_v3.py`. Canonical entry `step1_preprocessor_v4.py` (→
`impact_slides/` package) is unchanged.

Result: full suite green — **1190 passed, 15 skipped, 0 errors** (before: 804
collected + 20 collection errors on main).

## Per-file disposition

| File | Disposition | Notes |
|---|---|---|
| test_analytics.py | REPOINTED | import alias + V3→V4 class rename |
| test_classify_slide.py | REPOINTED | same |
| test_cross_file_entities.py | REPOINTED | same |
| test_evidence_post.py | **PARTIAL** | repointed; **deleted `test_short_keyword_uses_word_boundary`** — see below |
| test_helpers.py | REPOINTED | import alias only |
| test_intent.py | REPOINTED | same |
| test_logging.py | PARTIAL | repointed; `m._LOG = None` → `ls._LOG = None` (cache lives in `logging_setup`); version pin `3.0.0` → `4.0.0` |
| test_my_files.py | REPOINTED | import alias only |
| test_ocr.py | REPOINTED | same |
| test_pdf_tables.py | REPOINTED | same |
| test_pipeline.py | REPOINTED | same |
| test_pptx_extraction.py | REPOINTED | same |
| test_profiling.py | REPOINTED | same |
| test_realworld.py | REPOINTED | same |
| test_schemas.py | PARTIAL | repointed; emit-schema subprocess target `step1_preprocessor_v3.py` → `step1_preprocessor_v4.py` |
| test_semantic_dedup.py | PARTIAL | repointed; monkeypatch `m._SENTENCE_MODEL` → `dedup_mod._SENTENCE_MODEL`; `m.main` → `cli.main` |
| test_stage_mapping.py | REPOINTED | import alias only (passes after production fix #1 below) |
| test_timing.py | REPOINTED | import alias only |
| test_v3.py | REPOINTED | import alias only |
| test_yaml_config.py | PARTIAL | import → `impact_slides.config as m` + `impact_slides.cli as cli`; `m.main` → `cli.main` (monkeypatch of `_HAS_YAML`/`yaml` must target the config module) |
| conftest.py | PARTIAL | fixture import `step1_preprocessor_v2_full` → `impact_slides.preprocessor.ImpactSlidePreprocessorV4` |

## Production bugs found by the migration (fixed, not test-side)

1. **Dead stage-rule validation** — `impact_slides/preprocessor.py
   _validate_stage_rules` did `from schemas import NARRATIVE_STAGES`, a
   monolith-decomposition leftover that always ImportErrors (silently skipping
   ALL stage-rule validation). Every other import in the file uses the
   `impact_slides.` prefix. Fixed to `from impact_slides.schemas import
   NARRATIVE_STAGES`, restoring v4's own documented fail-fast validation.
   (Caught by test_stage_mapping.py TestValidation.)

2. **Logger singleton reset was a no-op** — `run()` set `preprocessor._LOG =
   None` ("reset singleton so each run() gets a fresh logger") but the real
   cache lives in `logging_setup._LOG`; the preprocessor binding is vestigial
   (set, never read). Any second `run()` in one process reused the stale
   logger and never wrote `run.log`. Fixed: `run()` now also resets
   `_logging_setup._LOG`. (Caught by test_logging.py TestRunLogFile.)

Doc-only (no behavior): `config.example.yaml`, `impact_slides/schemas.py`,
`impact_slides/preprocessor.py` docstrings now reference
`step1_preprocessor_v4.py`.

## Deleted test — flagged for review

**`test_evidence_post.py::TestCrossFile::test_short_keyword_uses_word_boundary`**
pinned v2 word-boundary-only entity matching: `East` must not fire inside
"yeast". v3 deliberately added fuzzy near-spelling entity matching
(`cross_file.py`, "v3 #17–#19", threshold 0.88) which v4 kept;
`similarity("east","yeast") = 0.889 ≥ 0.88` so the entity `East` now surfaces
from "yeast infection rates" **by design**. The test contradicts a documented
v3 feature, so it was deleted rather than repointed.

⚠️ **Judgment call for the user:** that fuzzy tradeoff means any 4+-char
entity can fire on an unrelated token one edit away (region/entity false
positives like `East`~"yeast"). If that is considered a product bug (not an
accepted tradeoff), the fix is a separate ticket — e.g. raise
`fuzzy_threshold` (0.88 → ~0.92) or require a first-letter match in the fuzzy
path. Not changed in this migration.
