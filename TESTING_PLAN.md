# Codebase Testing Plan — Impact Slides

**Scope:** Find bugs across all three Python modules in this project.
**Codebase under test (6,007 lines):**

| File | Lines | Role |
|------|------:|------|
| `step1_preprocessor.py` | 1,824 | Older Step 1 preprocessor (legacy) |
| `step1_preprocessor_v2_full.py` | 1,938 | **Current** Step 1: Excel/PPTX/PDF/DOCX → Evidence Register |
| `step4_builder_validator.py` | 2,245 | Step 4: Evidence Register → PPTX + HTML decks, validation |

**Existing test coverage:** Only an inline `test_preprocessor()` smoke test in `step1_preprocessor_v2_full.py`. No `pytest`, no `unittest`, no test fixtures committed. Step 4 has **no tests at all**.

---

## Phase 0 — Environment & Dependency Matrix

**Goal:** Guarantee tests run against a known, complete environment, and surface environment-coupled failures.

1. **Pin & verify the dependency matrix** (per `python_packages_Impact_Slides.md`):
   ```bash
   python -c "import pandas, openpyxl, fitz, docx, pptx, PIL, pytesseract, sklearn, pydantic, jsonschema; print('step1 deps ok')"
   python -c "import pptx, matplotlib, webcolors, jinja2; print('step4 deps ok')"
   ```
2. **Optional-dependency handling.** Every `try/except ImportError` block in both files must be exercised in **both** states (installed and missing). Mock-missing each optional dep (`fitz`, `docx`, `pytesseract`, `PIL`, `pptx`) and assert graceful degradation, not crashes.
3. **External binaries:**
   - Tesseract OCR — test with binary present, absent, and via `--tesseract-cmd`. (Already fixed & tested on Windows; repeat on Linux per cross-platform phase.)
   - Playwright (Step 4 `visual_validate_with_playwright`, `export_html_to_pdf`) — test with and without `playwright` installed.
4. **Reproducible temp workspace.** All tests use `tempfile.TemporaryDirectory()` and clean up. No writes to the repo or user Documents.

---

## Phase 1 — Static Analysis (fast, no execution)

**Goal:** Catch syntax/logic defects before runtime. All three files currently pass `py_compile`; go deeper.

1. **Lint:** `ruff check .` and `pyflakes *.py` — unused imports, undefined names, redefinitions.
2. **Type check:** `mypy step1_preprocessor_v2_full.py step4_builder_validator.py --ignore-missing-imports` — focus on `Optional` unwraps, `Dict` key access, `Any` returns.
3. **Control-flow / name-resolution audit (manual + automated):** Specifically hunt for variables used before assignment. **Already confirmed bug:**
   - `step1_preprocessor_v2_full.py:1346` — `classify_slide()` references `diagram_score` **before** it is defined (line 1377) in the section-divider branch. Reproducer:
     ```python
     classify_slide(title="Section Foo", slide_idx=3, total_slides=10, is_section_slide=False)
     # → UnboundLocalError: cannot access local variable 'diagram_score'
     ```
     This is called per-slide inside `extract_pptx`; the crash is swallowed by the broad `except` in `extract_pptx`, marking the **entire PPTX file as error** with no evidence. High-severity.
4. **Bare/broad exception audit:** `grep -n "except:" *.py` and `grep -n "except Exception" *.py`. Each must be reviewed: does it silently swallow a bug? (The OCR `except: pass` already hid a real failure — the pattern is dangerous.)
5. **Key-access audit:** Search for `dict["key"]` vs `dict.get("key")` on data sourced from optional libs (PPTX chart shapes, PDF tables). These raise `KeyError` on malformed inputs.
6. **Cross-check field names:** Producers and consumers of dicts must agree on keys. **Confirmed silent bug:**
   - `step1_preprocessor_v2_full.py:615,621` reads `finding.get("location", ...)`, but the `findings.append({...})` blocks (lines 400, 451) **never set `"location"`**. Result: Excel evidence always has `source_location: ""` and `column_name: None`. No crash, but the Evidence Register loses structural info for every Excel-derived entry.

---

## Phase 2 — Unit Tests (per-function, isolated)

**Goal:** Pure-function correctness. These are cheap and should cover the bulk of logic. Group by file.

### `step1_preprocessor_v2_full.py` — pure helpers (no I/O)
| Function | Test cases |
|---|---|
| `clean_text` | NaN, None, "  x  ", 0, float, datetime |
| `get_column_letter` / `excel_addr` | 1→A, 26→Z, 27→AA, 702→ZZ |
| `safe_stat` | empty list, NaNs, single value, all-valid |
| `compact_value` | NaN, float (rounding), int, str |
| `extract_advanced_metrics` | percentages, currency $/€/£, multipliers, ranges, nested, empty, cap at 10 |
| `contains_insight_language` | 0 keywords→0.0, 4+→1.0, mixed casing |
| `make_unique_columns` | duplicates, empties, long names |
| `is_likely_identifier_column` | "S.No", "ID", sequential ints, non-sequential, text |
| `is_generic_system_column` | "created_at", "is_active", "Revenue" |
| `calculate_evidence_priority_score` | identifier→0.15, numeric, categorical high-cardinality penalty, clamping [0,1] |

### `step1_preprocessor_v2_full.py` — `classify_slide` (the buggy classifier)
Build a **table-driven test** covering every branch and its boundary conditions. This is where Phase 1 found a crash, so it deserves exhaustive coverage:
| Scenario | Expected `type` |
|---|---|
| First slide, <25 words, no visuals | `title` |
| Title "Agenda"/"Overview"/"Contents" | `agenda` |
| `is_section_slide=True` | `section` |
| **Title "Section X", non-first slide, `is_section_slide=False`** | `section` (currently **crashes** — fix then pin) |
| Last slide "Thank You"/"Q&A" | `thank_you` |
| "Summary"/"Recommendations" | `conclusion` |
| chart_count≥2 & table≥1 | `data_mixed` |
| chart_count≥1 | `data_chart` |
| table_count≥1 | `data_table` |
| diagram_score thresholds (3,4,6,8) | `diagram_process` + priority math |
| "vs"/"comparison" titles | `comparison` |
| <40 words, no visuals | `quote_callout` |
| <12 words, ≥4 pictures | `low_value` |
| ≥35 words | `content_insight` |
| default | `content_light` |
| priority clamping to ≤0.98 after boosts | numeric assertion |

### `step1_preprocessor_v2_full.py` — evidence post-processing
| Function | Test cases |
|---|---|
| `_deduplicate_evidence` | identical texts keep highest priority; near-dups (whitespace/case); empty; truncation at 120 chars |
| `_apply_boost_rules` | single match boosts once; no keywords = no-op; cap 0.98; case-insensitive |
| `_find_cross_file_relationships` | shared entity (north/south/…); shared numeric ≥5; no overlap; only-Excel or only-PPTX → empty |
| `_get_filter_thresholds` | all three levels return expected dict; unknown level → conservative default |

### `step4_builder_validator.py` — pure helpers
| Function | Test cases |
|---|---|
| `slugify` | unicode, empty (fallback), punctuation |
| `shorten` | short, long, None, non-str |
| `parse_hex_color` / `hex_to_rgb_tuple` | "#FFF", "#AABBCC", invalid, "rgb(...)" |
| `luminance` / `contrast_ratio` / `is_neutral_color` / `choose_text_color` / `lighten` / `darken` | black/white/gray; WCAG AA/BB boundaries |
| `html_escape` | `<`, `&`, quotes, None |
| `words` | empty, multiple spaces |
| `as_list` | None, str, list, scalar |
| `infer_layout_type` | each slide layout shape |
| `collect_slide_evidence_refs` / `collect_slide_asset_refs` | missing keys, nested, duplicates |
| `build_google_font_link` | missing fonts, multi-word fonts |
| `normalize_final_json` | missing fields, extra fields |

---

## Phase 3 — Integration / Pipeline Tests (real files, end-to-end)

**Goal:** Verify the full `run()` → output JSON contract. Use synthetic fixtures (deterministic) **and** the real scanned PDFs already on disk.

### Step 1 pipeline (`run()` + `_save_outputs`)
1. **Excel-only input:** multi-sheet workbook (numeric, categorical, date, identifier, system, high-cardinality, empty sheet). Assert: `excel_profile.json` valid, `findings` populated, `column_name`/`source_location` non-empty (validates Phase-1 finding bug fix), `filtering_log.json` reasons correct per `filter_level`.
2. **PPTX input:** deck with one of each slide type (title, agenda, section, chart, table, mixed, conclusion, thank-you, low-value). Assert every slide classified; **section slides do not crash the run** (regression for Phase-1 bug). Assert `chart_details.series_data` populated.
3. **PDF — text-based:** assert `ocr_used=False` everywhere, evidence created.
4. **PDF — scanned, OCR ON:** (uses `PublicWaterMassMailing.pdf`, `Company-Profile-Strategicerp.pdf`) assert `ocr_used=True` on text-less pages, `insight_type=pdf_ocr_page_insight`, non-empty text.
5. **PDF — scanned, OCR OFF:** assert 0 evidence (regression — OCR must not run without flag).
6. **DOCX input:** paragraphs + tables extracted.
7. **Mixed input (Excel+PPTX+PDF+DOCX):** assert cross-file evidence appears; `evidence_register_seed.json` sorted by priority; dedup applied; boost keywords raise priority.
8. **Filter-level sweep:** same input under conservative/moderate/permissive — assert monotonic evidence count and threshold behavior.
9. **Empty / unreadable inputs:** empty dir; file with no read permission; zero-byte files; unknown extension. Must not crash; errors logged to `processing_errors.json`.
10. **Output contract test:** schema-validate every emitted JSON (`file_inventory`, `excel_profile`, `pptx_profile`, `evidence_register_seed`, `filtering_log`, `processing_errors`) against a JSON schema fixture. Assert required keys + types.

### Step 4 pipeline (`main()` → PPTX/HTML)
1. **Minimal valid `Final_Slide_Content.json`** → `--pptx` → open output PPTX with `python-pptx`, assert slide count, titles, layout types.
2. **Same input** → `--html` → assert HTML well-formed, slide count, asset embedding, CSS present, JS class `SlidePresentation` present.
3. **Brand theme** (`--brand`) → assert colors/fonts resolved, contrast checks run, Google Font link built.
4. **Asset manifest** (`--assets`, `--asset-root`) → assert data-URI embedding, missing-asset warnings.
5. **Layout coverage:** feed one slide of each layout type (title, default, metric, process, comparison, quote) → assert each `render_pptx_*` and `render_html_*` path executes and produces non-empty content.
6. **Malformed input:** missing required keys, bad colors, out-of-range numbers, empty slide list. Assert `BuildContext.error/warn` captures issues and exit code is non-zero on hard errors.
7. **Visual validation** (`--validate-visual`, `--export-html-pdf`): guard with `playwright` availability; skip-with-reason if absent. When present, assert screenshots captured and report MD generated.
8. **End-to-end Step1→Step4:** feed Step 1's `evidence_register_seed.json` (synthesized) into Step 4 input — verify the handoff contract holds.

---

## Phase 4 — Edge-Case & Adversarial Inputs

**Goal:** Break it on purpose. Feed pathological inputs.

- **Excel:** sheet with 1 row; 0 columns; merged cells; formulas returning errors; dates in mixed formats; numbers as text with commas; `#REF!`; 100k-row truncation at `max_sheet_rows`; `.xls` legacy; `.xlsm` macro file; password-protected.
- **PPTX:** slide with no shapes; chart with no series; table with merged cells; grouped shapes; shape with `shape_type` not in the handled set; empty presentation (0 slides); corrupted zip.
- **PDF:** encrypted/passworded; 0-page; page with text layer of whitespace only; mixed text+scanned pages in one file (assert OCR only on the scanned pages); very large page count; PDF with tables (`find_tables`) returning empty.
- **DOCX:** empty doc; doc with only a table (no paragraphs); nested tables; tracked changes.
- **Paths:** Unicode filenames; spaces; very long paths; symlinks; `..` traversal in `rglob`.
- **Evidence register:** two findings with identical normalized text (dedup keeps best); boost keyword matching its own evidence text; cross-file numeric collision on trivial value `1` (should be filtered by ≥5 rule).

---

## Phase 5 — Cross-Platform Tests (Windows + Linux)

**Goal:** Confirm portability (OCR path was just fixed; verify nothing else is Windows-coupled).

1. Run Phase 3 on a Linux VM/CI with `tesseract-ocr` + `tesseract-ocr-eng` installed, **no** `--tesseract-cmd` → assert auto-detection via `shutil.which` / `/usr/bin/tesseract`.
2. Run Phase 3 on Windows → assert `C:\Program Files\Tesseract-OCR\` auto-detection.
3. Audit all path operations: `grep -n "\\\\\\\\" *.py` for hardcoded backslash paths; `os.path.expandvars("%LOCALAPPDATA%")` is harmless on Linux but verify. `grep -n "C:\\\\" *.py`.
4. Audit `subprocess` calls (Step 4 Playwright/PDF export) for shell-injection and cross-platform arg handling.
5. Line-ending & encoding: open all `open(..., "w")` calls and confirm `encoding="utf-8"` is set (some are missing — audit and fix).

---

## Phase 6 — Regression & Non-Regression

1. **Pin every bug found** with a failing→passing test. Already on the list:
   - `classify_slide` `UnboundLocalError` (Phase 1 #3)
   - `--enable-ocr` dead flag + Tesseract auto-detect + `ocr_used` mis-flag (already fixed — add regression tests)
   - `finding["location"]` never set (Phase 1 #6)
2. **Golden-output regression:** for a fixed synthetic input, snapshot `evidence_register_seed.json` and diff on each run to catch unintended behavior changes.
3. **Performance smoke:** 50-file mixed input completes in <N seconds; flag >2× regressions. Watch OCR (≈2 s/page at 300 DPI) doesn't blow up on large PDFs.

---

## Phase 7 — Test Infrastructure to Create

```
tests/
  conftest.py                      # shared fixtures: tmp dirs, sample files, monkeypatch optional deps
  fixtures/
    sample.xlsx, sample.pptx, sample.docx, text.pdf, scanned.pdf
    final_slide_content.json, brand_style_summary.json, asset_manifest.json
  test_step1_helpers.py            # Phase 2 unit tests
  test_step1_classify_slide.py     # table-driven classifier tests (incl. crash regression)
  test_step1_pipeline.py           # Phase 3 Step 1 integration
  test_step1_edge_cases.py         # Phase 4
  test_step4_helpers.py            # Phase 2 Step 4 units
  test_step4_pipeline.py           # Phase 3 Step 4 integration
  test_cross_platform.py           # Phase 5 (skipped on missing deps)
  test_regression.py               # Phase 6 golden + bug pins
  schemas/                         # JSON schemas for output contract tests
```
- Framework: `pytest` + `pytest-mock` (for optional-dep mocking).
- CI matrix: Python 3.11/3.12/3.14 × {windows-latest, ubuntu-latest}, with Tesseract installed via apt/winget.

---

## Execution Order (recommended)

1. **Phase 1 (static)** — fastest wins, finds the crashes. Fix `classify_slide` immediately.
2. **Phase 2 units** for `step1` helpers + `classify_slide` — establishes a safety net.
3. **Phase 3 Step 1 integration** — validates the main pipeline + output contract.
4. **Phase 2/3 Step 4** — currently zero coverage; build fixtures and integration tests.
5. **Phase 4 edge cases** — stress after happy path is green.
6. **Phase 5 cross-platform** — last, once logic is verified.
7. **Phase 6 regression** — ongoing; every fixed bug adds a pinned test.

---

## Definition of Done

- All Phase 1 findings resolved or documented as accepted-risk.
- Phase 2 unit coverage ≥ 80% line coverage on pure helpers and `classify_slide`.
- Phase 3 integration tests green for Step 1 (all input types) and Step 4 (PPTX + HTML + all layouts).
- Every previously confirmed bug has a pinned regression test that fails without the fix.
- Suite passes on Windows and Linux CI with the documented dependency matrix.

---

## Appendix — Confirmed Bugs Found During Plan Preparation

| # | File:Line | Severity | Bug | Status |
|---|---|---|---|---|
| 1 | `step1_v2:1346` | **High (crash)** | `classify_slide` uses `diagram_score` before assignment in section-divider branch → `UnboundLocalError`, swallowed by `extract_pptx` except → whole PPTX marked error | Open |
| 2 | `step1_v2:615,621` | Medium (silent data loss) | Excel findings never set `"location"`, so `source_location`/`column_name` always empty/None | Open |
| 3 | `step1_v2:run()` | High (feature broken) | `extract_pdf(path)` called without `use_ocr=self.enable_ocr` → `--enable-ocr` ignored | **Fixed** |
| 4 | `step1_v2:extract_pdf` | High (feature broken) | Tesseract binary never located; bare `except: pass` hid failure | **Fixed** |
| 5 | `step1_v2:extract_pdf` | Medium (wrong metadata) | `ocr_used` computed after OCR fills text → successful OCR pages reported `ocr_used=False` | **Fixed** |

Bugs 3–5 were found and fixed during the earlier OCR investigation; bug 1 and 2 are newly identified during this planning pass and should be the first items addressed.
