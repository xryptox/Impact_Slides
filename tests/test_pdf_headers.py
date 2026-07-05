"""
Tests for PDF running-header/footer stripping (_strip_pdf_running_headers).

Covers:
  - running header (first line, appears on >= 30% of pages) is stripped
  - running footer (last line, appears on >= 30% of pages) is stripped
  - isolated page numbers (digits, F-33, roman numerals) in first/last 2 lines
    are stripped
  - body page-number references (e.g. "See Note 5") are preserved
  - < 3 pages is a no-op (too few to detect patterns)
  - pages with no running header are unchanged (no false positives)
  - OCR text is handled the same way
  - the 30% threshold works (a line on 2/10 pages is NOT stripped)
"""
from __future__ import annotations

import pytest

import step1_preprocessor_v4 as m


@pytest.fixture()
def preprocessor(tmp_path):
    inp = tmp_path / "input"
    out = tmp_path / "output"
    inp.mkdir()
    p = m.ImpactSlidePreprocessorV4(input_path=str(inp), output_dir=str(out))
    return p


def _page(num, text, ocr=False):
    return {"page": num, "text": text, "ocr_used": ocr}


# --------------------------------------------------------------------------- #
# Running header detection
# --------------------------------------------------------------------------- #
class TestRunningHeader:
    def test_strips_running_header(self, preprocessor):
        """A first line appearing on >= 30% of pages is stripped from all."""
        pages = [
            _page(i, f"Table of Contents\n{i}\nActual content on page {i}")
            for i in range(1, 11)
        ]
        result = preprocessor._strip_pdf_running_headers(pages)
        for pg in result:
            assert "Table of Contents" not in pg["text"]
            assert f"Actual content on page {pg['page']}" in pg["text"]

    def test_strips_running_footer(self, preprocessor):
        """A last line appearing on >= 30% of pages is stripped from all."""
        pages = [
            _page(i, f"Content on page {i}\nConfidential — Do Not Distribute")
            for i in range(1, 11)
        ]
        result = preprocessor._strip_pdf_running_headers(pages)
        for pg in result:
            assert "Confidential" not in pg["text"]
            assert f"Content on page {pg['page']}" in pg["text"]

    def test_header_on_83_percent_stripped(self, preprocessor):
        """Real-world pattern: header on 193/232 pages (83%)."""
        pages = []
        for i in range(1, 233):
            if i <= 193:
                text = f"Table of Contents\n{i}\nBody content {i}"
            else:
                text = f"Body content {i}\n{i}"
            pages.append(_page(i, text))
        result = preprocessor._strip_pdf_running_headers(pages)
        toc_count = sum(1 for pg in result if "Table of Contents" in pg["text"])
        assert toc_count == 0


# --------------------------------------------------------------------------- #
# Page number stripping
# --------------------------------------------------------------------------- #
class TestPageNumberStripping:
    def test_strips_numeric_page_numbers_at_top(self, preprocessor):
        pages = [
            _page(i, f"Header\n{i}\nBody content {i}")
            for i in range(1, 11)
        ]
        result = preprocessor._strip_pdf_running_headers(pages)
        for pg in result:
            # "Header" is a running header (10/10 = 100% >= 30%), stripped.
            # Page number (1, 2, ...) in first 2 lines is stripped.
            # Body content remains.
            assert f"Body content {pg['page']}" in pg["text"]
            assert "Header" not in pg["text"]

    def test_strips_f_prefixed_page_numbers(self, preprocessor):
        """Financial-statement page numbers like F-33, F-34 are stripped."""
        pages = [
            _page(i, f"Header\nF-{i}\nFinancial note content {i}")
            for i in range(1, 11)
        ]
        result = preprocessor._strip_pdf_running_headers(pages)
        for pg in result:
            assert f"Financial note content {pg['page']}" in pg["text"]
            assert f"F-{pg['page']}" not in pg["text"].split("\n")[0]

    def test_strips_roman_numeral_page_numbers(self, preprocessor):
        pages = [
            _page(i, f"Header\n{roman}\nContent {i}\nFooter")
            for i, roman in enumerate(["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"], 1)
        ]
        result = preprocessor._strip_pdf_running_headers(pages)
        for pg in result:
            assert f"Content {pg['page']}" in pg["text"]

    def test_body_page_references_preserved(self, preprocessor):
        """A page-number-like token in the body (not first/last 2 lines) is
        preserved — e.g. 'See Note 5' or 'Item 1A.' in the middle of a page."""
        pages = [
            _page(i, f"Header\n{i}\nFirst body line\nSee Note 5\nLast body line\nFooter")
            for i in range(1, 11)
        ]
        result = preprocessor._strip_pdf_running_headers(pages)
        for pg in result:
            assert "See Note 5" in pg["text"]

    def test_page_number_in_body_not_stripped(self, preprocessor):
        """A standalone '5' in the body (not at top/bottom) is preserved."""
        pages = [
            _page(i, f"Header\n{i}\nFirst line {i}\n5\nSecond line {i}\nFooter line")
            for i in range(1, 11)
        ]
        result = preprocessor._strip_pdf_running_headers(pages)
        for pg in result:
            # "5" is in the body (not first/last 2 lines), preserved.
            # "Header" and "Footer line" (running header/footer) are stripped.
            assert "5" in pg["text"].split("\n")
            assert f"First line {pg['page']}" in pg["text"]
            assert f"Second line {pg['page']}" in pg["text"]


# --------------------------------------------------------------------------- #
# Threshold & edge cases
# --------------------------------------------------------------------------- #
class TestThresholdAndEdgeCases:
    def test_below_threshold_not_stripped(self, preprocessor):
        """A line on 2/10 pages (20% < 30%) is NOT a running header."""
        pages = []
        for i in range(1, 11):
            if i in (1, 2):
                text = f"Rare header\nContent {i}"
            else:
                text = f"Content {i}"
            pages.append(_page(i, text))
        result = preprocessor._strip_pdf_running_headers(pages)
        # "Rare header" was on 2/10 = 20% < 30%, so it's NOT stripped.
        assert "Rare header" in result[0]["text"]

    def test_fewer_than_3_pages_noop(self, preprocessor):
        """< 3 pages: no running-header detection (too few)."""
        pages = [
            _page(1, "Header\nContent 1"),
            _page(2, "Header\nContent 2"),
        ]
        result = preprocessor._strip_pdf_running_headers(pages)
        # Unchanged — no detection with < 3 pages.
        assert result[0]["text"] == "Header\nContent 1"
        assert result[1]["text"] == "Header\nContent 2"

    def test_no_running_header_unchanged(self, preprocessor):
        """Pages with unique first/last lines are unchanged."""
        pages = [
            _page(i, f"Unique title {i}\nContent line A\nContent line B")
            for i in range(1, 11)
        ]
        result = preprocessor._strip_pdf_running_headers(pages)
        for orig, res in zip(pages, result):
            assert orig["text"] == res["text"]

    def test_empty_pages_handled(self, preprocessor):
        """Empty/blank pages don't crash the filter."""
        pages = [
            _page(1, ""),
            _page(2, "Header\nContent"),
            _page(3, "Header\nContent 3"),
            _page(4, "Header\nContent 4"),
        ]
        # Should not crash.
        result = preprocessor._strip_pdf_running_headers(pages)
        assert len(result) == 4

    def test_ocr_text_handled(self, preprocessor):
        """OCR-extracted text gets the same header/footer treatment."""
        pages = [
            _page(i, f"Scanned Header\n{i}\nOCR content {i}", ocr=True)
            for i in range(1, 11)
        ]
        result = preprocessor._strip_pdf_running_headers(pages)
        for pg in result:
            assert "Scanned Header" not in pg["text"]
            assert f"OCR content {pg['page']}" in pg["text"]

    def test_text_truncated_to_5000(self, preprocessor):
        """After stripping, the result is still capped at 5000 chars."""
        pages = [
            _page(i, f"Header\n{i}\n" + "X" * 6000)
            for i in range(1, 11)
        ]
        result = preprocessor._strip_pdf_running_headers(pages)
        for pg in result:
            assert len(pg["text"]) <= 5000

    def test_both_header_and_footer_stripped(self, preprocessor):
        """Both a running header AND a running footer on the same pages."""
        pages = [
            _page(i, f"Running Header\n{i}\nBody content {i}\nRunning Footer")
            for i in range(1, 11)
        ]
        result = preprocessor._strip_pdf_running_headers(pages)
        for pg in result:
            assert "Running Header" not in pg["text"]
            assert "Running Footer" not in pg["text"]
            assert f"Body content {pg['page']}" in pg["text"]

    def test_min_threshold_3_pages(self, preprocessor):
        """The minimum threshold is 3 (not just 30% of a small set).
        With 5 pages and a header on 2 (40% >= 30%), it should NOT be stripped
        because 2 < 3 (the min threshold)."""
        pages = [
            _page(1, "Header\nContent 1"),
            _page(2, "Header\nContent 2"),
            _page(3, "Content 3"),
            _page(4, "Content 4"),
            _page(5, "Content 5"),
        ]
        result = preprocessor._strip_pdf_running_headers(pages)
        # "Header" on 2/5 = 40%, but 2 < 3 (min threshold), so NOT stripped.
        assert "Header" in result[0]["text"]
