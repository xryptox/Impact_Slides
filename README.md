# Impact Slide Preprocessor — Step 1

This project ships **two versions** of the Step 1 preprocessor:

| Version | File | Status |
|---------|------|--------|
| **v2** | `step1_preprocessor_v2_full.py` | Stable, fully tested (201 tests). The bug-fix baseline. |
| **v3** | `step1_preprocessor_v3.py` | **Active development.** Adds five insight-quality enhancements over v2 (29 dedicated tests). |

Both produce the same Evidence Register handoff for the Impact Slide Analyst
GPT; v3 emits a richer register. Use v3 going forward; v2 remains for
reference/regression.

> **Role in the Impact Slides workflow:** Step 1 — Python preprocessor.
> Ingests business source files (Excel, PowerPoint, PDF, Word) and produces a
> clean, **source-backed, priority-ordered Evidence Register** that the
> **Impact Slide Analyst GPT** (Step 2) treats as its source of truth when
> building a slide narrative around the *Why → What → How → Now* framework.

---

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [The Processing Pipeline (what `run()` does)](#the-processing-pipeline-what-run-does)
4. [Functionality & Capabilities](#functionality--capabilities)
5. [Supported File Types](#supported-file-types)
6. [Outputs Produced](#outputs-produced)
7. [The Evidence Register](#outputs-produced)
8. [CLI Reference](#cli-reference)
9. [Installation & Dependencies](#installation--dependencies)
10. [Quick Start](#quick-start)
11. [Inspecting Insight Quality](#inspecting-insight-quality)
12. [Testing](#testing)
13. [Design Notes & Quality Guardrails](#design-notes--quality-guardrails)

---

## Overview

This preprocessor is the **measurement and extraction layer** of the Impact
Slides hybrid workflow. Per the project's tool split, Python is responsible for
*extraction, measurement, validation, exact references, and chart data* — while
the GPTs handle *interpretation, storyline, and messaging*.

Given a folder of source files, it:
- inventories every file,
- profiles spreadsheets (numeric ranges, categorical distributions, dates),
- classifies and audits PPTX slides (charts, tables, bullets, notes),
- extracts text + tables from PDFs (with OCR fallback for scanned pages),
- extracts paragraphs/tables from DOCX,
- assembles everything into a single **priority-ranked Evidence Register**
  where every insight carries an `E####` ID, a source file, a source location,
  a priority score (0–1), a confidence level, and a `suggested_narrative_use`
  mapping to the Why/What/How/Now framework.

The Analyst GPT then *preserves those Evidence IDs* and only adds new ones when
clearly supported — so insights stay traceable from source file → slide.

---

## Architecture

```
                ┌─────────────────────────────────────────────┐
   source files │  .xlsx .pptx .pdf .docx  (+.csv/.xls/.xlsm) │
                └──────────────────────┬──────────────────────┘
                                       │  gather_files() + build_file_inventory()
                                       ▼
                ┌─────────────────────────────────────────────┐
                │            ImpactSlidePreprocessorV2         │
                │                                             │
                │  ┌─────────────┐  ┌──────────────────────┐  │
                │  │  EXTRACTORS │  │   SCORING / FILTERING│  │
                │  │             │  │                      │  │
                │  │ extract_    │  │ classify_slide()     │  │
                │  │  spreadsheet│  │ calculate_evidence_  │  │
                │  │ extract_pptx│  │  priority_score()    │  │
                │  │ extract_pdf │  │ is_likely_identifier_│  │
                │  │ extract_docx│  │  column()            │  │
                │  │             │  │ _looks_like_noise_   │  │
                │  └──────┬──────┘  │  cell()              │  │
                │         │         │ _get_filter_         │  │
                │         │         │  thresholds()        │  │
                │         ▼         └──────────┬───────────┘  │
                │  ┌──────────────────────────▼────────────┐  │
                │  │     build_evidence_register()         │  │
                │  │  • per-source evidence extraction     │  │
                │  │  • cross-file relationship detection  │  │
                │  │  • priority sort                      │  │
                │  │  • deduplication                      │  │
                │  │  • boost-keyword application          │  │
                │  └──────────────────┬────────────────────┘  │
                └─────────────────────┼───────────────────────┘
                                      ▼
                ┌─────────────────────────────────────────────┐
                │            OUTPUT FILES (JSON + MD)         │
                │  evidence_register_seed.json  ← main handoff│
                │  file_inventory.json  excel_profile.json    │
                │  pptx_profile.json  filtering_log.json      │
                │  processing_errors.json  preprocessor_*.md  │
                └─────────────────────────────────────────────┘
```

### Key components

| Component | Responsibility |
|-----------|----------------|
| `ImpactSlidePreprocessorV2` | Main orchestrator class. Holds config, runs the 5-step pipeline, owns all state. |
| `gather_files()` / `build_file_inventory()` | Recursively discover files; classify by extension; check readability. |
| `extract_spreadsheet()` → `profile_dataframe()` | Per-sheet profiling with header-row detection, column typing, findings generation. |
| `extract_pptx()` → `classify_slide()` | Per-slide shape analysis, classification into 17 slide types, rich detail extraction. |
| `extract_pdf()` + `_ensure_tesseract()` | PDF text extraction with OCR fallback for scanned pages. |
| `extract_docx()` | Word document paragraph + table extraction. |
| `build_evidence_register()` | Assembles, scores, sorts, deduplicates, and boosts all evidence. |
| `_find_cross_file_relationships()` | Detects shared entities/values between Excel and PPTX. |
| `_save_outputs()` + `_generate_summary_report()` | Emits all JSON + a human-readable Markdown summary. |
| `inspect_register()` | Console pretty-printer for quick manual review (`--inspect`). |

### Optional dependencies (graceful degradation)
PDF (`fitz`/PyMuPDF), DOCX (`python-docx`), and OCR (`pytesseract` + `PIL`) are
imported in `try/except ImportError` blocks. If a library is missing, the
relevant extractor simply reports `"error"` status for that file type instead
of crashing — the rest of the pipeline still runs.

---

## The Processing Pipeline (what `run()` does)

`run()` executes 5 logged steps:

```
[1/5] Discovered N files (M readable)
[2/5] Processing spreadsheet: <name>      → per-sheet profiling
[3/5] Processing PPTX / PDF / DOCX: <name>→ per-slide/page extraction
[4/5] Building Evidence Register ...
[5/5] Complete. Evidence entries: N
```

### Step 1 — File discovery & inventory
- `gather_files()` recursively lists all files under `--input` (skips dotfiles).
- `build_file_inventory()` classifies each by extension into `spreadsheet` /
  `pdf` / `docx` / `other` (PPTX falls under `other` and is detected by name),
  checks readability, and assigns a stable `F####` file ID.

### Step 2 — Spreadsheet profiling
For each Excel/CSV file, every sheet is read **header-less** and profiled by
`profile_dataframe()`:
1. **Header-row detection** (`_detect_header_row`): scores the first 15 rows to
   find the real header (favours text-heavy, distinct-value rows — fixes a bug
   where junk rows could beat real headers on ties).
2. **Column typing** per column: identifier, numeric, date, or categorical.
3. **Filtering** per `filter_level`: drops high-missing, generic-system
   (`created_at`, `is_active`, …), and high-cardinality-free-text columns.
4. **Findings** are emitted for numeric ranges (`Unit price 10.53–99.96`) and
   categorical distributions (`Branch has 3 unique values (C, A, B). Top 3
   account for 100.0%`) — each finding carries `location`, `column`, and a
   `priority_score`.
5. **Multi-column insights** suggest category-by-metric analyses.

### Step 3 — Document extraction (PPTX / PDF / DOCX)

**PPTX** (`extract_pptx` + `classify_slide`): for each slide it counts charts,
tables, pictures, shapes, connectors; extracts chart data (categories + series
values), table cells, bullets, bold/emphasized text, speaker notes, and theme
colors. `classify_slide()` then assigns one of 17 types — `title`, `agenda`,
`section`, `conclusion`, `data_chart`, `data_table`, `data_mixed`,
`diagram_process`, `comparison`, `quote_callout`, `content_insight`,
`content_light`, `low_value`, `thank_you`, … — each with a confidence and a
`priority_for_evidence` score.

**PDF** (`extract_pdf`): extracts the text layer per page via PyMuPDF. If
`--enable-ocr` is on and a page has <30 chars of text, it renders the page at
300 DPI and runs Tesseract OCR, keeping the longer text. Also extracts tables.
Each page is tagged `ocr_used: true/false`.

**DOCX** (`extract_docx`): extracts paragraphs and tables.

### Step 4 — Evidence Register assembly (`build_evidence_register`)
1. Walks every profile and converts findings/details into typed evidence
   entries (`numeric_range`, `chart_data_insight`, `table_cell`,
   `bullet_insight`, `speaker_notes_insight`, `pdf_page_insight`, etc.).
2. **Cross-file relationships** (`_find_cross_file_relationships`): detects
   shared entities (derived dynamically from Excel categorical values) and
   distinctive shared numbers (decimals or integers ≥100) between Excel and
   PPTX; caps matches to avoid flooding.
3. **Sorts** by `priority_score` descending.
4. **Deduplicates** (`_deduplicate_evidence`): near-identical texts (normalized,
   first 120 chars) collapse to the highest-priority version.
5. **Applies boost keywords** (`_apply_boost_rules`): evidence whose text
   contains a `--boost-keywords` term gets +0.15 priority (capped at 0.98).

### Step 5 — Output (`_save_outputs`)
Writes all JSON outputs, the Markdown summary report, optional Markdown/CSV
exports, and (if `--inspect`) prints the console summary.

---

## Functionality & Capabilities

### Spreadsheet intelligence
- **Identifier detection** — `S.No`, `ID`, `Serial`, `Row`, `Key`, `Index`,
  `Number`, `Seq`, `UUID`, `GUID` by name; unnamed columns that form a
  contiguous `0..N` / `1..N` row index by value. A named business column that
  merely increments by 1 is **not** misfiltered as an ID.
- **System-column filtering** — `created_at`, `modified_by`, `is_active`,
  `has_flag`, `guid`, `uuid`, `hash`, `checksum`, …
- **Numeric profiling** — min/max/mean/median per numeric column.
- **Categorical profiling** — unique count, top-6 values with counts, top-3
  coverage % (correct for <3-value columns), actual value names included in
  the finding text (enables cross-file entity matching).
- **Date detection**, **header-row detection**, **multi-column suggestions**.
- **Configurable filtering** via 3 levels (see `--filter-level`).

### PPTX intelligence
- **17-way slide classification** with confidence + evidence priority.
- **Chart data extraction** — categories + per-series values, surfaced as
  `chart_data_insight` evidence.
- **Table cell extraction** — every cell scored; **noise cells** (IPs, URLs,
  user-agents, HTTP requests, log timestamps) are demoted so they don't
  outrank real insights.
- **Bullet capture** — both bulleted lines (`•`/`-`/`–`/`▪`/`*`) **and**
  substantive plain-text lines (≥4 words) so text-heavy decks are seeded.
- **Speaker notes**, **bold/emphasized text**, **theme colors**, **process
  steps** from diagram shapes.
- **Title-capture guard** — a leading numeric-only (page-number) textbox is no
  longer used as the slide title.

### PDF intelligence
- **Text-layer extraction** via PyMuPDF.
- **OCR fallback** for scanned pages via Tesseract (300 DPI).
- **Tesseract auto-detection** — honors `--tesseract-cmd`, then probes `PATH`
  and common Windows/Linux install locations; warns clearly if missing.
- **Table extraction**.
- **Correct `ocr_used` flagging** per page.

### Evidence register intelligence
- **Priority scoring** (0.0–1.0) per evidence, with insight-language boosting
  (keywords like *recommend, critical, growth, risk, record* raise priority).
- **Why → What → How → Now mapping** — every entry carries
  `suggested_narrative_use`; conclusion/recommendation bullets are tagged with
  `Now` (the call-to-action stage).
- **Cross-file relationships** — entity-based (dynamic, from Excel values) and
  distinctive-numeric, with word-boundary matching for short keywords.
- **Deduplication**, **boost keywords**, **priority sort**.
- **Source-backing** — every entry traces to a real file + sheet/slide/page.

---

## Supported File Types

| Extension(s) | Category | Handler | Notes |
|---------------|----------|---------|-------|
| `.xlsx` `.xls` `.xlsm` `.csv` | spreadsheet | `extract_spreadsheet` | pandas-based |
| `.pptx` | other (by name) | `extract_pptx` | python-pptx |
| `.pdf` | pdf | `extract_pdf` | PyMuPDF + optional Tesseract OCR |
| `.docx` `.doc` | docx | `extract_docx` | python-docx (`.doc` legacy limited) |
| other | other | — | inventoried but not deeply parsed |

---

## Outputs Produced

All written to `--output`. (The **Evidence Register** — the main Analyst handoff — is documented in detail at the end of this section.)

| File | When | Contents |
|------|------|----------|
| `file_inventory.json` | always | List of discovered files: `file_id`, `file_name`, `absolute_path`, `category`, `access_status`. |
| `excel_profile.json` | always | Per-file → per-sheet: numeric/categorical/date profiles, findings, multi-column insights, priority scores. |
| `pptx_profile.json` | if PPTX input | Per-file → per-slide: classification, visual counts, chart/table/bullet/notes details. |
| **`evidence_register_seed.json`** | if evidence found | **The main handoff to the Analyst GPT.** Priority-sorted list of evidence entries. |
| `filtering_log.json` | if items filtered | Why each column/insight was dropped (reason + thresholds) — useful for debugging. |
| `processing_errors.json` | if errors | Per-file error messages (e.g. missing Tesseract, unreadable file). |
| `preprocessor_summary.md` | always | Human-readable report: inventory, Excel/PPTX summaries, evidence breakdown, top-5, classification table. |
| `evidence_register.md` | `--export-md` | Evidence register as Markdown. |
| `evidence_register.csv` | `--export-csv` | Evidence register as CSV (evidence_id, insight_type, text, priority_score, confidence, suggested_narrative_use, source_location). |

### `evidence_register_seed.json` entry shape

```jsonc
{
  "evidence_id": "E0006",                 // unique, preserved by the Analyst GPT
  "source_file": "supermarket_sales.xlsx",
  "sheet_name": "January",                // or null for non-Excel
  "column_name": "Unit price",            // Excel-derived only
  "insight_type": "numeric_range",        // see "insight types" below
  "text": "January: 'Unit price' ranges from 10.53 to 99.96.",
  "priority_score": 0.85,                 // 0.0–1.0, sorted descending
  "confidence": "high",                   // high | medium
  "suggested_narrative_use": ["What","How"], // subset of Why/What/How/Now
  "source_location": "January",           // sheet / "Slide N" / "Page N" / "Cross-file"
  "ocr_used": false                       // PDF pages only
}
```

### Evidence `insight_type` values
`numeric_range`, `categorical_distribution`, `multi_column_suggestion`,
`pptx_slide_insight`, `chart_insight`, `chart_data_insight`, `table_cell`,
`table_insight`, `text_metric`, `bullet_insight`, `process_step`,
`speaker_notes_insight`, `emphasized_text`, `section_divider`,
`pdf_page_insight`, `pdf_ocr_page_insight`, `pdf_table_insight`,
`docx_insight`, `cross_file_metric`.

---

## CLI Reference

```
python step1_preprocessor_v2_full.py --input <folder> --output <folder> [options]
```

Run with no `--input`/`--output` to execute the built-in smoke test.

### Core arguments

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--input` | path | — | **Required.** Folder of source files (searched recursively). |
| `--output` | path | — | **Required.** Folder where outputs are written (created if missing). |
| `--filter-level` | choice | `conservative` | Filtering strictness. `conservative` = strict (min priority 0.25, ≥10% non-null, ≤90% unique); `moderate` = balanced (0.15 / 5% / 92%); `permissive` = minimal (0.05 / 2% / 98%). Lower levels retain more evidence. |
| `--boost-keywords` | list | `[]` | Keywords that bump an evidence entry's priority by +0.15 (capped at 0.98), case-insensitive. Example: `--boost-keywords recommend critical growth`. |
| `--verbose` | flag | off | Detailed console logging (boost keywords, export options, per-file timing, OCR errors). |

### OCR arguments

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--enable-ocr` | flag | off | Enable OCR fallback for scanned PDFs. Without it, scanned pages yield no text. |
| `--tesseract-cmd` | path | auto | Path to the Tesseract binary. Auto-detected (`PATH` + common Windows/Linux locations) if omitted. |

### Export arguments

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--export-md` | flag | off | Also write `evidence_register.md` (Markdown). |
| `--export-csv` | flag | off | Also write `evidence_register.csv`. |

### Inspection argument

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--inspect` | flag | off | Print a readable top-N Evidence Register summary to the console after running. |
| `--inspect-top` | int | 15 | Number of top-priority entries to show with `--inspect`. |

---

## Installation & Dependencies

**Python 3.10+** (tested on 3.14).

```bash
python -m pip install pandas openpyxl python-pptx PyMuPDF python-docx Pillow pytesseract
```

| Package | Purpose |
|---------|---------|
| `pandas` + `openpyxl` | Excel/CSV profiling (required) |
| `python-pptx` | PPTX extraction (required for `.pptx`) |
| `PyMuPDF` (`fitz`) | PDF text/table extraction (required for `.pdf`) |
| `python-docx` | DOCX extraction (required for `.docx`) |
| `Pillow` + `pytesseract` | OCR for scanned PDFs (only needed with `--enable-ocr`) |

**External binary for OCR:** Tesseract OCR.
- **Windows:** `winget install UB-Mannheim.TesseractOCR` (lands in
  `C:\Program Files\Tesseract-OCR\`, auto-detected).
- **Linux:** `sudo apt install tesseract-ocr tesseract-ocr-eng`
  (auto-detected via `PATH` / `/usr/bin/tesseract`).
- Verify: `tesseract --version`.

Without Tesseract, the pipeline still runs; scanned PDFs simply yield no text
(and `processing_errors.json` records a clear warning).

---

## Quick Start

```bash
# 1. Basic run (v3 — recommended)
python step1_preprocessor_v3.py \
  --input "C:/path/to/source_files" \
  --output "C:/path/to/output"

# 2. Permissive filtering + boost key terms + console review
python step1_preprocessor_v3.py \
  --input ./files --output ./out \
  --filter-level permissive \
  --boost-keywords recommend critical growth \
  --inspect --inspect-top 20

# 3. Scanned PDFs included
python step1_preprocessor_v3.py \
  --input ./files --output ./out \
  --enable-ocr \
  --inspect

# 4. Export register as Markdown + CSV for sharing
python step1_preprocessor_v3.py \
  --input ./files --output ./out \
  --export-md --export-csv
```

> Swap `step1_preprocessor_v3.py` for `step1_preprocessor_v2_full.py` to run
> the v2 baseline. Both accept the same CLI flags.

**What to open first:** `output/preprocessor_summary.md` — the human-readable
overview. Then `evidence_register_seed.json` — the Analyst handoff. v3 also
writes `coverage_map.json` — a per-stage / per-source coverage summary.

---

## Inspecting Insight Quality

The `--inspect` flag prints a quick console summary after a run:

- **Header** — total entry count + average priority.
- **Framework coverage** — which Why/What/How/Now stages have evidence, and
  which are missing (e.g. flags `Now` as missing when there's no
  conclusion/recommendation content).
- **Breakdown by source file** and **by insight type**.
- **Top-N evidence** — ID, priority, type, source location, narrative stages,
  text preview.
- **Quality flags** — automatically surfaces known anti-patterns:
  - noise (IPs/URLs/user-agents) ranking in the top 5,
  - numeric cross-file false positives flooding the register (>3 entries),
  - framework stages with zero evidence,
  - a high share of high-priority entries that are only "medium" confidence.

For automated validation of the register's structure against the Analyst's
contracts, see the test suite (next section).

---

## Testing

The test suite lives in `tests/` and uses `pytest`.

```bash
python -m pip install pytest pytest-mock
python -m pytest                 # full suite (~67s; 230 passed + 8 skipped = 238 collected)
python -m pytest tests/ -v       # verbose
python -m pytest -k ocr -v       # just OCR-regression tests
```

### Test modules

| File | Covers |
|------|--------|
| `conftest.py` | Shared fixtures: temp dir, Excel/PPTX/PDF builders, preprocessor factory. |
| `test_helpers.py` | Pure-function unit tests (clean_text, column letters, safe_stat, metrics, identifier/system/noise detection, priority scoring). |
| `test_classify_slide.py` | Table-driven classifier tests + the `diagram_score` crash regression. |
| `test_evidence_post.py` | Dedup, boost, cross-file relationships, filter thresholds, dynamic entity derivation. |
| `test_profiling.py` | `profile_dataframe` numeric/categorical/date/identifier behavior + `location`/`column` field fix + `top_3_pct` fix. |
| `test_pipeline.py` | End-to-end `run()`: Excel, PPTX (incl. section-slide crash regression), PDF, output contract, plain-text bullets, page-number-title fix. |
| `test_ocr.py` | `_ensure_tesseract` auto-detection + `extract_pdf` OCR path (skips if Tesseract absent). |
| `test_intent.py` | **Specification tests** verifying the codebase goal: source-backed, priority-ordered register mapped to Why→What→How→Now. |
| `test_realworld.py` | **Real-data regressions** using downloaded files (supermarket_sales.xlsx + Performance.pptx); skips if absent. |
| `test_v3.py` | **v3 enhancement regressions** — trends, cross-sheet consolidation, per-bullet ranking, coverage map, aggregates (synthetic + real-data). |
| `test_my_files.py` | **Template** to validate the preprocessor against *your own* files — set `MY_FILES` env var or edit `MY_FILES_DIR`, then run. |

### Running tests against your own files (`tests/test_my_files.py`)

This is a **template** that validates the preprocessor's output contracts
against *any* folder of your own source files — the same contracts the
Analyst GPT relies on. It builds a fresh Evidence Register from your files
and runs 8 checks:

| # | Test | What it validates |
|---|------|-------------------|
| 1 | `test_runs_without_error_and_emits_handoff_files` | `run()` doesn't crash; `file_inventory.json`, `evidence_register_seed.json`, `preprocessor_summary.md` all exist. |
| 2 | `test_register_is_nonempty_list` | The register is a non-empty JSON list (your files actually produced evidence). |
| 3 | `test_evidence_source_backed` | Every entry has a `source_file` and non-empty `source_location` (traceability). |
| 4 | `test_evidence_ids_unique_and_well_formed` | IDs are unique and match `E####` (the Analyst preserves these). |
| 5 | `test_register_priority_sorted` | Entries are sorted by `priority_score` descending. |
| 6 | `test_narrative_use_within_framework` | Every `suggested_narrative_use` is within `{Why, What, How, Now}`. |
| 7 | `test_no_numeric_cross_file_flooding` | No more than 3 numeric `cross_file_metric` entries (the bug-#11a false-positive guard). |
| 8 | `test_noise_not_at_top` | No IP/URL/user-agent noise in the top-5 entries (the bug-#11b guard). |

**Usage:**
```bash
# Point it at a folder of .xlsx/.pptx/.pdf/.docx files, one of two ways:
set MY_FILES=C:/path/to/your_files            # (a) env var
#   ...or edit MY_FILES_DIR at the top of tests/test_my_files.py  (b)

python -m pytest tests/test_my_files.py -v
```

It skips cleanly (all 8 tests skipped with a clear message) if the folder is
empty or missing, so the full suite stays green anywhere. It only activates
when `MY_FILES` points at real files. Note: it's a *structural/contract* test,
not a semantic correctness oracle — it confirms the register is well-formed
and the known anti-patterns don't recur, but can't judge whether your specific
insights are "right" (use `--inspect` for that manual review).

---

## v3 Enhancements (over v2)

`step1_preprocessor_v3.py` adds five insight-quality improvements, each pinned
by tests in `tests/test_v3.py`. Validated against the real-world files
(supermarket_sales.xlsx + Performance.pptx):

| # | Enhancement | Before (v2) | After (v3) |
|---|-------------|-------------|------------|
| 1 | **Trend insights across time-ordered sheets** — when sheets look time-ordered (month/quarter/year), per-column deltas are computed and emitted as `trend_insight` (What/How/Why, high priority). | 0 trend insights | **8** trends (e.g. "Total: decrease of 4.0% from January to March") |
| 2 | **Cross-sheet consolidation** — repeated per-sheet `numeric_range` entries for trended columns collapse to 1 representative + the trend. | 23 numeric_range (7 cols × 3 sheets) | **3** (only non-trend / representative) |
| 3 | **Per-bullet insight ranking** — individual bullets are scored by insight-language density via `insight_priority_boost()`, so "Recommendation: expand" outranks "LogLevel: …". | all 61 bullets flat at 0.75 | insight bullets boosted up to 0.94; generic stay at 0.75 |
| 4 | **Coverage map handoff** — a new `coverage_map.json` summarizes evidence per Why/What/How/Now stage and per source file, flagging stages with no evidence (e.g. `Now` empty). | no coverage signal | `coverage_map.json` + summary-report section |
| 5 | **Computed aggregate insights** — numeric×categorical group-bys are actually computed (not just suggested) and emitted as `aggregate_insight` with per-group totals. | 1 suggestion only | **18** concrete aggregates (e.g. "Unit price by Branch: A=6349, B=6544, C=6860") |

New module-level helpers: `sheet_time_rank()`, `insight_priority_boost()`,
`_parse_numeric_token()`. New evidence types: `trend_insight`,
`aggregate_insight`. New output file: `coverage_map.json`.

---


These are the bugs and anti-patterns found during testing and the guardrails
now in place (each pinned by a regression test):

- **OCR flag plumbing** — `--enable-ocr` actually flows through `run()` to
  `extract_pdf`; Tesseract is auto-located; `ocr_used` reflects real OCR.
- **Classifier crash fix** — `classify_slide` no longer raises
  `UnboundLocalError` on section-divider titles (the whole PPTX was silently
  marked as error before).
- **Excel traceability** — findings carry `location` + `column`, so Excel
  evidence has non-empty `source_location`/`column_name`.
- **"Now" framework stage** — conclusion/recommendation/next-step bullets are
  tagged with `Now` (previously the framework's call-to-action stage had no
  evidence feeding it).
- **Cross-file entity derivation** — entity candidates come from the Excel's
  actual categorical values (not a hardcoded 7-word list), with word-boundary
  matching for short keywords.
- **Cross-file numeric false positives** — only distinctive numbers (decimals
  or integers ≥100) match, and matches are capped at 3.
- **Table-cell noise** — IP/URL/user-agent/HTTP/log-timestamp cells are
  demoted below real insights.
- **`top_3_pct` correctness** — columns with <3 unique values report real
  coverage (100.0%, not 0.0%).
- **Text-heavy decks** — plain-text lines (not just bulleted ones) are seeded
  as bullet insights.
- **Page-number-as-title** — a leading numeric-only textbox is skipped as a
  title candidate.
- **Identifier heuristic** — a real metric that increments by exactly 1 is not
  misfiltered as an ID (only unnamed contiguous `0..N`/`1..N` indices are).
- **Header-row ties** — real headers (distinct values) beat junk rows on ties.

See `tests/README.md` for the full bug-fix regression index and
`realworld_test/INSIGHT_QUALITY_ASSESSMENT.md` for the real-world quality study.
