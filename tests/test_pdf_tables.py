"""
Tests for the v3 merged PDF table extraction (pdfplumber + PyMuPDF).

Covers:
  - pdfplumber is the preferred engine (auto), PyMuPDF the fallback
  - graceful degradation when pdfplumber is absent (falls back to PyMuPDF)
  - --pdf-table-engine flag forces a backend (pymupdf / pdfplumber / auto)
  - enriched table output (header, cols, engine, bbox) supersedes the old
    rows-only shape
  - new pdf_table_cell evidence is seeded from detected cells
  - ruled tables are detected with header + cell contents
"""
from __future__ import annotations

import json
from pathlib import Path

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


@pytest.fixture()
def ruled_table_pdf(tmp_workspace):
    """A PDF with a real 3x3 ruled table (lines + cell text) that pdfplumber
    detects cleanly."""
    import fitz
    inp = tmp_workspace / "input"
    inp.mkdir(parents=True, exist_ok=True)
    p = inp / "table.pdf"
    doc = fitz.open()
    page = doc.new_page()
    x0, y0, cw, ch = 72, 72, 120, 30
    for r in range(4):
        page.draw_line(fitz.Point(x0, y0 + r * ch), fitz.Point(x0 + 3 * cw, y0 + r * ch))
    for c in range(4):
        page.draw_line(fitz.Point(x0 + c * cw, y0), fitz.Point(x0 + c * cw, y0 + 3 * ch))
    data = [["Region", "Q1", "Q2"], ["North", "100", "150"], ["South", "200", "250"]]
    for ri, row in enumerate(data):
        for ci, val in enumerate(row):
            page.insert_text((x0 + ci * cw + 5, y0 + ri * ch + 18), val)
    doc.save(p)
    doc.close()
    return p


# --------------------------------------------------------------------------- #
# Engine selection
# --------------------------------------------------------------------------- #
class TestEngineSelection:
    def test_auto_prefers_pdfplumber(self, ruled_table_pdf, make_preprocessor):
        if m.pdfplumber is None:
            pytest.skip("pdfplumber not installed")
        p, inp, out = make_preprocessor()
        tabs = p._extract_pdf_tables(ruled_table_pdf, engine="auto")
        assert tabs
        assert all(t["engine"] == "pdfplumber" for t in tabs)

    def test_force_pymupdf(self, ruled_table_pdf, make_preprocessor):
        p, inp, out = make_preprocessor()
        tabs = p._extract_pdf_tables(ruled_table_pdf, engine="pymupdf")
        assert tabs
        assert all(t["engine"] == "pymupdf" for t in tabs)

    def test_force_pdfplumber(self, ruled_table_pdf, make_preprocessor):
        if m.pdfplumber is None:
            pytest.skip("pdfplumber not installed")
        p, inp, out = make_preprocessor()
        tabs = p._extract_pdf_tables(ruled_table_pdf, engine="pdfplumber")
        assert tabs
        assert all(t["engine"] == "pdfplumber" for t in tabs)

    def test_pdf_table_engine_attr_default(self, make_preprocessor):
        p, inp, out = make_preprocessor()
        assert p.pdf_table_engine == "auto"


# --------------------------------------------------------------------------- #
# Graceful degradation
# --------------------------------------------------------------------------- #
class TestGracefulDegradation:
    def test_falls_back_to_pymupdf_when_pdfplumber_absent(self, ruled_table_pdf,
                                                          make_preprocessor, monkeypatch):
        """When pdfplumber is unavailable, auto engine falls back to PyMuPDF."""
        p, inp, out = make_preprocessor()
        monkeypatch.setattr(m, "pdfplumber", None)
        tabs = p._extract_pdf_tables(ruled_table_pdf, engine="auto")
        assert tabs
        assert all(t["engine"] == "pymupdf" for t in tabs)


# --------------------------------------------------------------------------- #
# Enriched output + evidence
# --------------------------------------------------------------------------- #
class TestEnrichedOutput:
    def test_table_output_has_header_cols_engine(self, ruled_table_pdf, make_preprocessor):
        if m.pdfplumber is None:
            pytest.skip("pdfplumber not installed")
        p, inp, out = make_preprocessor()
        tabs = p._extract_pdf_tables(ruled_table_pdf, engine="auto")
        t = tabs[0]
        assert t["rows"] == 3
        assert t["cols"] == 3
        assert "Region" in t["header"]
        assert t["engine"] == "pdfplumber"
        # data carries actual cell values
        flat = [c for row in t["data"] for c in row]
        assert "North" in flat and "250" in flat

    def test_pdf_table_cell_evidence_seeded(self, ruled_table_pdf, make_preprocessor):
        if m.pdfplumber is None:
            pytest.skip("pdfplumber not installed")
        p, inp, out = make_preprocessor()
        p.run()
        ev = json.load(open(out / "evidence_register_seed.json"))
        cells = [e for e in ev if e["insight_type"] == "pdf_table_cell"]
        assert cells, "expected per-cell evidence from the detected table"
        blob = " ".join(e["text"] for e in cells)
        assert "North" in blob
        assert "250" in blob

    def test_table_summary_includes_header_and_dims(self, ruled_table_pdf, make_preprocessor):
        if m.pdfplumber is None:
            pytest.skip("pdfplumber not installed")
        p, inp, out = make_preprocessor()
        p.run()
        ev = json.load(open(out / "evidence_register_seed.json"))
        summaries = [e for e in ev if e["insight_type"] == "pdf_table_insight"]
        assert summaries
        text = summaries[0]["text"]
        assert "3 rows" in text and "3 cols" in text
        assert "Region" in text  # header preview
        # pdfplumber detection -> high confidence
        assert summaries[0]["confidence"] == "high"

    def test_pymupdf_engine_gives_medium_confidence(self, ruled_table_pdf, make_preprocessor):
        p, inp, out = make_preprocessor()
        p.pdf_table_engine = "pymupdf"
        p.run()
        ev = json.load(open(out / "evidence_register_seed.json"))
        summaries = [e for e in ev if e["insight_type"] == "pdf_table_insight"]
        assert summaries
        assert summaries[0]["confidence"] == "medium"
