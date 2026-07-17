# Session Handoff — Impact Slide Preprocessor v4

> **Purpose:** Onboard a fresh session quickly. Read top-to-bottom; everything needed to continue work is here.
>
> **Last verified:** 2026-07-09 — HEAD `3213418` on `main`, clean tree, 469 passed + 8 skipped across 23 test files.

---

## 1. Project Overview

**Impact Slide Preprocessor v4** — a Python preprocessor that ingests business source files (Excel, PPTX, PDF, DOCX) and produces a source-backed, priority-ordered **Evidence Register** for the *Impact Slide Analyst GPT*, mapped to the **Why → What → How → Now** framework.

| | |
| --- | --- |
| **Repo** | `https://github.com/xryptox/Impact_Slides.git` (branch `main`) |
| **CWD** | `C:\Users\Ag1Le\Documents\Impact_Slides` |
| **Python** | 3.14.4 on Windows |
| **Tesseract** | `C:\Program Files\Tesseract-OCR\tesseract.exe` |
| **Test suite** | 469 passed + 8 skipped across 23 test files in `tests/` |
| **Git HEAD** | `3213418` on `main` (clean, all work pushed) |

### Current Status
All work is committed and pushed. No uncommitted changes. Three features shipped this session:

1. **Architecture SVG diagram** in README (replaced ASCII)
2. **Uniform `MAX_TEXT_LENGTH = 800`** on evidence `text` fields (Option A)
3. **PDF running-header/footer stripping** in `extract_pdf()`

---

## 2. Key Architecture Decisions

### 2.1 `MAX_TEXT_LENGTH = 800` — single uniform text cap (Option A)

**Problem:** Evidence `text` had inconsistent per-extractor caps — PDF page 150 chars, PPTX notes 300, DOCX para 200. The 150-char PDF cap discarded ~95% of page content.

**Decision:** One canonical constant `MAX_TEXT_LENGTH = 800` in `schemas.py` (schema = single source of truth). Applied uniformly at validation time in `_validate_evidence()`. User can lower via `--max-text-length` / YAML but **cannot exceed 800** (schema ceiling enforced).

**Why Option A over B/C:**
- Option A gives the GPT enough context per entry while keeping the register compact and the schema authoritative.
- Option B (raise PDF cap only) would leave inconsistency.
- Option C (no truncation, cap at schema only) risks huge registers on large PDFs.

**Implementation:**
- `schemas.py`: `MAX_TEXT_LENGTH = 800` constant; `EvidenceEntry.text` has `Field(max_length=MAX_TEXT_LENGTH, …)`.
- `config.py`: `max_text_length` in `CONFIG_DEFAULTS` (references schema constant); `validate_config()` rejects 0/negative/non-int/above-ceiling.
- `preprocessor.py`: `_validate_evidence()` truncates to `cap-1 + "…"` (U+2026) **before** schema validation — truncate, don't drop.
- `cli.py`: `--max-text-length` CLI flag; wired via `preprocessor.max_text_length = cfg["max_text_length"]`.
- Per-extractor caps **removed**: PDF `text[:150]`, PPTX `notes[:300]`, DOCX `para[:200]` → all store full text now; the uniform cap is the only cap.
- The 5000-char raw page-text storage cap (`text[:5000]` in `pages.append`) is **unchanged** — it's an intermediate processing limit, not an evidence-text limit.

### 2.2 PDF running-header/footer stripping

**Problem:** SSB 2024 10-K had "Table of Contents" as a running header on 83% of pages (193/232). 193/1050 evidence entries started with this boilerplate.

**Decision:** New `_strip_pdf_running_headers()` method in `extract_pdf()`, called after all pages are extracted but before evidence creation.

**Algorithm:**
- Collect first 2 + last 2 non-empty lines of each page.
- Any line appearing on ≥30% of pages (min 3) is a running header/footer → stripped from all pages.
- Also strip isolated page-number lines (digits, `F-33`, roman numerals, ≤6 chars) from first/last 2 lines only — body references like "See Note 5" preserved.
- Mirrors the existing v3 #11 PPTX deck-wide navigation filter.

**Why frequency-based over layout-based:** PyMuPDF's `get_text()` doesn't reliably separate headers from body text without bounding-box analysis, which is more complex and fragile. Frequency-based detection is robust and handles the common case. AmEx and Chubb PDFs have no running headers → filter is a no-op (verified).

### 2.3 `gather_files()` single-file input fix

**Bug:** `gather_files()` used `input_path.rglob("*")` unconditionally, which returns empty when `input_path` is a single file. Every prior test pointed `--input` at a folder.

**Fix:** `input_path.is_file()` → return `[input_path]`; otherwise rglob as before.

---

## 3. Important Constraints & Rules

- **v2/v3 are frozen regression baselines** — never modify `step1_preprocessor_v2_full.py` or `step1_preprocessor_v3.py`.
- **v4 shim:** `step1_preprocessor_v4.py` is a 55-line PEP 562 `__getattr__` forwarding shim → `impact_slides.preprocessor` / `impact_slides.cli`. 469 tests import via this shim unchanged.
- **Schema = single source of truth:** `schemas.py` is canonical for output shapes; README/code/GPT-prompt all derive from it.
- **Pydantic optional at runtime:** if not installed, validation skipped but pipeline runs.
- **Graceful degradation:** all optional deps (pydantic, rapidfuzz, pdfplumber, PyMuPDF, structlog) use try/except ImportError.
- **Git helpers are read-only** — never commit/stage/push via tools (user does git operations).
- **`_console_safe()`** in `cli.py` handles non-cp1252 Unicode on Windows console.
- **Per-type caps:** bullet ≤20, pptx_slide ≤15, table_cell ≤12, categorical ≤12, outlier ≤10, correlation ≤8, period_trend ≤10.
- **CLI > YAML > default** precedence for all config.
- **`MAX_TEXT_LENGTH = 800`** is the hard schema ceiling — user can lower but not raise via config.

---

## 4. Key File Paths

| File | Role |
| --- | --- |
| `step1_preprocessor_v4.py` | 55-line shim → `impact_slides/` package |
| `impact_slides/preprocessor.py` | Trunk class `ImpactSlidePreprocessorV4` (~3,260 LOC) |
| `impact_slides/cli.py` | `main()` / `test_preprocessor()` / `inspect_register()` (~315 LOC) |
| `impact_slides/schemas.py` | Pydantic contracts + `MAX_TEXT_LENGTH=800` |
| `impact_slides/config.py` | `CONFIG_DEFAULTS` + `validate_config()` |
| `impact_slides/analyst_briefing.py` | `NarrativeScorer` + `AnalystBriefingGenerator` |
| `impact_slides/text_utils.py`, `heuristics.py`, `text_analysis.py`, `dedup.py`, `cross_file.py`, `stage_mapping.py`, `pptx_extract.py`, `logging_setup.py` | Leaf modules |
| `config.example.yaml` | YAML config with `briefing:` + `max_text_length` sections |
| `docs/images/architecture_v4.svg` | Excalidraw SVG architecture diagram |
| `tests/test_max_text_length.py` | 23 tests for uniform text cap |
| `tests/test_pdf_headers.py` | 16 tests for running-header stripping |

---

## 5. Recently Changed Files (this session)

### `impact_slides/schemas.py`
- Added `MAX_TEXT_LENGTH = 800` constant (canonical source of truth).
- `EvidenceEntry.text` now has `Field(max_length=MAX_TEXT_LENGTH, …)`.
- Exported `MAX_TEXT_LENGTH` in `__all__`.

### `impact_slides/config.py`
- Added `"max_text_length": _SCHEMA_MAX_TEXT_LENGTH` to `CONFIG_DEFAULTS`.
- `validate_config()` now validates: positive int, ≤ schema ceiling.

### `impact_slides/preprocessor.py`
- `gather_files()`: fixed single-file input — `if self.input_path.is_file(): return [self.input_path]`.
- `__init__`: added `self.max_text_length = MAX_TEXT_LENGTH` (from schemas).
- `_validate_evidence()`: now truncates `text` to `cap-1 + "…"` before schema validation.
- `extract_pdf()`: calls `self._strip_pdf_running_headers(pages)` after `doc.close()`.
- New method `_strip_pdf_running_headers()`: frequency-based header/footer + page-number stripping.
- Removed per-extractor caps: PDF `text[:150]`, PPTX `notes[:300]`, DOCX `para[:200]`.
- `_PAGE_NUM_RE` regex for page-number detection.

### `impact_slides/cli.py`
- Added `--max-text-length` CLI flag (type=int, default=None for `_cli_was_set` detection).
- Wired `preprocessor.max_text_length = cfg["max_text_length"]`.

### `README.md`
- Architecture section: ASCII diagram replaced with `![...](docs/images/architecture_v4.svg)` + collapsible `<details>` ASCII fallback.
- CLI Reference: added `--max-text-length` row.
- YAML config section: added `# max_text_length: 800` comment.

### `config.example.yaml`
- Added `# max_text_length: 800` under the briefing section.

### `docs/images/architecture_v4.svg`
- New file: Excalidraw SVG export of the v4 architecture diagram.

### Test files
- `tests/test_max_text_length.py` (new, 23 tests)
- `tests/test_pdf_headers.py` (new, 16 tests)

---

## 6. Open Tasks / Next Steps

1. `pptx_profile.json` → `pptx_slide_audit.json` naming mismatch for GPT handoff compatibility (deferred).
2. Add `semantic_type` field mapping `insight_type` → GPT-friendly types (`Metric`/`Claim`/`Quote`/`Risk`) (deferred).
3. Update GPT prompt's Source Priority list to include `analyst_briefing.md/.json`, `coverage_map.json`, `run_metadata.json`, `entities_summary.json` (deferred per user).
4. Consider `brand_style_summary.json`, `image_ocr_summary.json`, `extracted_documents.md` (deferred).
5. Consider further trunk decomposition: `build_evidence_register` (520 LOC) → `evidence_builder.py` (deferred).
6. Consider deleting root `step1_preprocessor.py` (v1) and `step1_preprocessor_v2_full.py` if no longer needed as baselines.

---

## 7. Rejected Approaches

- **Option B (raise PDF page-insight cap only):** Rejected — would leave the per-extractor inconsistency (150/200/300) intact; only addressed one symptom.
- **Option C (no truncation, cap at schema only):** Rejected — risk of very large `evidence_register_seed.json` on 300-page PDFs; unpredictable GPT token budget.
- **Layout-based header detection (PyMuPDF bounding boxes):** Not explicitly rejected but not chosen — more complex and fragile than frequency-based; frequency handles the common case robustly.

---

## 8. Critical Context for New Session

- **Real-world test artifacts** in `C:\Users\Ag1Le\Documents\realworld_test\` — each has `input/`, `output/`, `COMMANDS.md`:
  - `nyse_ssb_2024/` — SSB 10-K 2024 (232 pages, 1050 entries, 33s, readiness 22/100)
  - `amex_v4/` — AmEx 14-page slice
  - `amex_full/` — AmEx full 192-page
  - `nyse_cb_2024/` — Chubb full 304-page
- **Single-source PDF readiness scores are stage-coverage-driven, not volume-driven** — all entries land in "What" stage; Why/How/Now empty. This is expected behavior; the briefing flags it via `missing_*_stage` + `single_source`.
- **The `gather_files()` single-file fix was found via the SSB test** — prior tests always used directory input; the bug was latent.
- **`_validate_evidence()` is the single chokepoint** for text truncation — all evidence passes through it before the register is returned; this is where to add any future uniform text transformations.
