"""
Tests for v3 #22 — always-on time profiling.

Covers:
  - structured self.timing dict populated after run()
  - total_seconds recorded and ≈ wall-clock
  - per-file durations are independent (NOT cumulative since run start — the
    old bug); the slowest file's duration doesn't inflate the fast file's
  - every processed file has a timing entry (incl. PDF/DOCX, the old gap)
  - error files still record a duration + status=error
  - timing shown by default (not verbose-gated) on stdout
  - preprocessor_summary.md contains a Processing Time section + per-file table
  - per-file table sorted by duration descending
"""
from __future__ import annotations

import time
from io import StringIO
from contextlib import redirect_stdout
from pathlib import Path

import pandas as pd
import pytest

import step1_preprocessor_v3 as m


@pytest.fixture()
def make_preprocessor(tmp_workspace):
    """Build a v3 preprocessor (overrides conftest's v2 fixture)."""
    def _make(filter_level="permissive"):
        inp = tmp_workspace / "input"
        out = tmp_workspace / "output"
        inp.mkdir(parents=True, exist_ok=True)
        p = m.ImpactSlidePreprocessorV2(
            input_path=str(inp), output_dir=str(out), filter_level=filter_level,
        )
        return p, inp, out
    return _make


def _ev(out):
    import json
    return json.load(open(out / "evidence_register_seed.json"))


# --------------------------------------------------------------------------- #
# Structured timing data
# --------------------------------------------------------------------------- #
class TestTimingStructure:
    def test_timing_dict_populated(self, make_excel, make_pptx, make_preprocessor):
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"M": [1, 2, 3], "V": [10, 20, 30]}))
        make_pptx(slides=[{"title": "T1"}, {"title": "T2", "body": "Some body text"}])
        p.run()
        t = p.timing
        assert "files" in t and "stages" in t and "total_seconds" in t
        assert t["total_seconds"] > 0
        for stage in ("discovery", "extraction", "evidence_build", "output"):
            assert stage in t["stages"]

    def test_all_processed_files_have_timing_entry(self, make_excel, make_pptx, make_preprocessor):
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}), name="a.xlsx")
        make_excel(df=pd.DataFrame({"M": [3, 4], "V": [30, 40]}), name="b.xlsx")
        make_pptx(slides=[{"title": "T"}], name="d.pptx")
        p.run()
        timed_files = {f["file"] for f in p.timing["files"]}
        assert "a.xlsx" in timed_files
        assert "b.xlsx" in timed_files
        assert "d.pptx" in timed_files
        assert len(p.timing["files"]) == 3

    def test_pdf_and_docx_timed(self, tmp_workspace, make_preprocessor):
        """Regression for the gap where only xlsx/pptx printed timing."""
        p, inp, out = make_preprocessor()
        # minimal PDF + DOCX
        import fitz
        doc = fitz.open()
        doc.new_page().insert_text((72, 72), "hello pdf world")
        doc.save(inp / "r.pdf")
        doc.close()
        from docx import Document
        Document().save(inp / "n.docx")
        p.run()
        timed_files = {f["file"]: f for f in p.timing["files"]}
        assert "r.pdf" in timed_files and timed_files["r.pdf"]["category"] == "pdf"
        assert "n.docx" in timed_files and timed_files["n.docx"]["category"] == "docx"


# --------------------------------------------------------------------------- #
# Per-file duration correctness (the cumulative-time bug fix)
# --------------------------------------------------------------------------- #
class TestPerFileDuration:
    def test_duration_not_cumulative(self, make_excel, make_preprocessor, monkeypatch):
        """The old bug: per-file 'Time' showed elapsed-since-run-start, so file
        #2's time included file #1's. Fix: each file gets its own delta. We
        force one file to be slow (sleep during extraction) and assert the
        other file's duration is small and independent."""
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}), name="slow.xlsx")
        make_excel(df=pd.DataFrame({"M": [3, 4], "V": [30, 40]}), name="fast.xlsx")

        original = p.extract_spreadsheet

        def slow_if_slow_file(path, item):
            # slow ONLY the file named slow.xlsx (processing order is
            # alphabetical, so we can't rely on call count)
            if "slow" in str(path).lower():
                time.sleep(0.3)
            return original(path, item)

        monkeypatch.setattr(p, "extract_spreadsheet", slow_if_slow_file)
        p.run()
        by_file = {f["file"]: f["duration_s"] for f in p.timing["files"]}
        # fast file's duration must NOT include the slow file's 0.3s sleep
        assert by_file["fast.xlsx"] < 0.25, (
            f"fast file duration {by_file['fast.xlsx']} looks cumulative "
            f"(includes slow file's sleep)"
        )
        assert by_file["slow.xlsx"] >= 0.25

    def test_per_file_sum_le_extraction_stage(self, make_excel, make_pptx, make_preprocessor):
        """Sum of per-file durations ≤ extraction-stage duration ≤ total
        (sanity: no double-counting, stages don't overlap)."""
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}))
        make_pptx(slides=[{"title": "T", "body": "body"}])
        p.run()
        per_file_sum = sum(f["duration_s"] for f in p.timing["files"])
        extraction = p.timing["stages"]["extraction"]
        assert per_file_sum <= extraction + 0.5  # allow small overhead
        assert extraction <= p.timing["total_seconds"]


# --------------------------------------------------------------------------- #
# Error files still timed
# --------------------------------------------------------------------------- #
class TestErrorFileTiming:
    def test_error_file_recorded_with_error_status(self, make_excel, make_preprocessor, monkeypatch):
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}), name="good.xlsx")

        def boom(path):
            return {"status": "error", "file": str(path), "error": "synthetic"}

        # make the pptx extraction blow up
        monkeypatch.setattr(p, "extract_pptx", boom)
        from pptx import Presentation
        Presentation().save(inp / "d.pptx")
        p.run()
        err_entry = next(f for f in p.timing["files"] if f["file"] == "d.pptx")
        assert err_entry["status"] == "error"
        assert err_entry["duration_s"] >= 0
        assert err_entry["category"] == "pptx"


# --------------------------------------------------------------------------- #
# Console output by default
# --------------------------------------------------------------------------- #
class TestConsoleOutput:
    def test_timing_shown_by_default_not_verbose(self, make_excel, make_preprocessor):
        """Timing must appear on stdout even when verbose=False (the new
        always-on behavior)."""
        p, inp, out = make_preprocessor()
        assert p.verbose is False
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}))
        buf = StringIO()
        with redirect_stdout(buf):
            p.run()
        out_str = buf.getvalue()
        assert "[Timing]" in out_str
        assert "Total:" in out_str
        assert "Per file:" in out_str

    def test_verbose_does_not_duplicate_old_lines(self, make_excel, make_preprocessor):
        """The old [Verbose] timing lines are gone; the always-on block is the
        single source. verbose=True still shows the [Timing] block."""
        p, inp, out = make_preprocessor()
        p.verbose = True
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}))
        buf = StringIO()
        with redirect_stdout(buf):
            p.run()
        out_str = buf.getvalue()
        assert "[Timing]" in out_str
        assert "[Verbose] Total processing time" not in out_str  # old line removed


# --------------------------------------------------------------------------- #
# Persisted to preprocessor_summary.md
# --------------------------------------------------------------------------- #
class TestSummaryReport:
    def test_summary_contains_processing_time_section(self, make_excel, make_preprocessor):
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}))
        p.run()
        summary = (out / "preprocessor_summary.md").read_text(encoding="utf-8")
        assert "## Processing Time" in summary
        assert "Total runtime:" in summary
        assert "Discovery:" in summary
        assert "Extraction:" in summary
        assert "Evidence register build:" in summary
        assert "Output & report:" in summary

    def test_summary_contains_per_file_table(self, make_excel, make_pptx, make_preprocessor):
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}), name="data.xlsx")
        make_pptx(slides=[{"title": "T"}], name="deck.pptx")
        p.run()
        summary = (out / "preprocessor_summary.md").read_text(encoding="utf-8")
        assert "### Per-File Timing" in summary
        assert "| File | Category | Duration | Status |" in summary
        assert "data.xlsx" in summary
        assert "deck.pptx" in summary
        assert "| ok |" in summary

    def test_summary_total_matches_console(self, make_excel, make_preprocessor):
        """The persisted summary total must equal the console total (no drift
        between the two sources)."""
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}))
        buf = StringIO()
        with redirect_stdout(buf):
            p.run()
        # extract console total
        import re
        console_match = re.search(r"Total:\s*([\d.]+)s", buf.getvalue())
        assert console_match
        console_total = float(console_match.group(1))
        summary = (out / "preprocessor_summary.md").read_text(encoding="utf-8")
        summary_match = re.search(r"Total runtime:.*?([\d.]+)s", summary)
        assert summary_match
        summary_total = float(summary_match.group(1))
        assert abs(console_total - summary_total) < 0.01

    def test_per_file_table_sorted_desc(self, make_excel, make_preprocessor, monkeypatch):
        """The per-file table must be sorted by duration descending so the
        slowest file is first."""
        p, inp, out = make_preprocessor()
        make_excel(df=pd.DataFrame({"M": [1, 2], "V": [10, 20]}), name="fast.xlsx")
        make_excel(df=pd.DataFrame({"M": [3, 4], "V": [30, 40]}), name="slow.xlsx")
        original = p.extract_spreadsheet
        state = {"n": 0}

        def slow_second(path, item):
            state["n"] += 1
            if state["n"] == 2:
                time.sleep(0.3)
            return original(path, item)

        monkeypatch.setattr(p, "extract_spreadsheet", slow_second)
        p.run()
        summary = (out / "preprocessor_summary.md").read_text(encoding="utf-8")
        # slow.xlsx row should appear before fast.xlsx row in the table
        slow_pos = summary.find("| slow.xlsx")
        fast_pos = summary.find("| fast.xlsx")
        assert 0 < slow_pos < fast_pos, "slowest file must be listed first"
