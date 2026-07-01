# Impact Slides — Test Suite

Pytest suite for `step1_preprocessor_v2_full.py` (Step 4 coverage to be added later).

## Run

```bash
# from the Impact_Slides repo root
python -m pip install pytest pytest-mock
python -m pytest tests/ -v
```

## What's here

| File | Covers |
|------|--------|
| `conftest.py` | Shared fixtures: temp dir (Windows-cleanup-safe), sample Excel/PPTX/PDF builders, preprocessor factory |
| `test_helpers.py` | Pure-function unit tests for all module-level helpers |
| `test_classify_slide.py` | Table-driven classifier tests + the `diagram_score` UnboundLocalError regression |
| `test_evidence_post.py` | `_deduplicate_evidence`, `_apply_boost_rules`, `_find_cross_file_relationships`, `_get_filter_thresholds` |
| `test_profiling.py` | `profile_dataframe` numeric/categorical/date/identifier/system-column behavior + the `location`/`column` field fix |
| `test_pipeline.py` | End-to-end `run()` integration: Excel, PPTX (incl. section-slide crash regression), PDF text vs scanned-OCR, output JSON contract |
| `test_ocr.py` | `_ensure_tesseract` auto-detection + `extract_pdf` OCR path (skips if Tesseract binary absent) |
| `test_intent.py` | **Specification tests** verifying the codebase goal: source-backed, priority-ordered Evidence Register mapped to the Why→What→How→Now framework for the Analyst GPT |
| `test_realworld.py` | **Real-data regression tests** using downloaded files (supermarket_sales.xlsx + Performance.pptx); skips if those files aren't present |

## Bug-fix regressions pinned

- `test_classify_slide.py::test_section_title_does_not_crash` — was `UnboundLocalError` (bug #1)
- `test_profiling.py::test_findings_carry_location_and_column` — `location`/`column` were never set (bug #2)
- `test_ocr.py::test_enable_ocr_flag_actually_triggers_ocr` — `--enable-ocr` was dead (bug #3)
- `test_ocr.py::test_tesseract_autodetection` — Tesseract binary was never located (bug #4)
- `test_ocr.py::test_ocr_used_flag_reflects_actual_ocr` — `ocr_used` was mis-reported (bug #5)
- `test_evidence_post.py::TestApplyBoost::test_case_insensitive` — boost keywords weren't re-lowercased (bug #6)
- `test_profiling.py::test_header_row_detection` — junk row beat real header on ties (bug #7)
- `test_intent.py::TestFrameworkMapping::test_conclusion_evidence_is_tagged_with_now` — conclusion/recommendation content never mapped to the "Now" stage (bug #8)
- `test_intent.py::TestCrossFile::test_shared_entity_surfaced_across_excel_and_pptx` — categorical findings omitted actual values so cross-file entity detection couldn't fire (bug #9)
- `test_intent.py::TestSourceBacked::test_every_evidence_has_required_handoff_fields` — `cross_file_metric` evidence had no `source_file`/real filenames, breaking Analyst traceability (bug #10)
- `test_realworld.py::TestCrossFileNoFalsePositives` — cross-file numeric detection matched bare integers (5,6,10,17,42…) between unrelated files (bug #11a)
- `test_realworld.py::TestTableCellNoiseDemoted` — table-cell scoring ranked IP/URL/user-agent log noise at the top of the register (bug #11b)
- `test_realworld.py::TestTop3PctCorrect` / `test_profiling.py::test_top3_pct_correct_for_low_cardinality` — "Top 3 account for 0.0%" for <3-value categorical columns (bug #11c)
- `test_evidence_post.py::TestCrossFile::test_dynamic_entity_derived_from_excel_categorical_values` — cross-file entity vocabulary was hardcoded; now derived from the Excel's actual categorical values (bug #12)
- `test_pipeline.py::test_plain_text_bullets_are_captured` — text-heavy decks without bullet glyphs seeded no bullet insights (bug #13)
- `test_pipeline.py::test_page_number_textbox_not_used_as_title` — leading page-number textboxes were used as slide titles (bug #6)
