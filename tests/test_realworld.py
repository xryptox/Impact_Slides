"""
Real-world regression tests using actual files downloaded from the internet.

These pin the three insight-quality fixes validated against real data
(see realworld_test/INSIGHT_QUALITY_ASSESSMENT.md):

- bug #11a: cross-file numeric false positives (10 spurious entries between
  UNRELATED files -> 0). Uses supermarket_sales.xlsx + Performance.pptx,
  which share no real metrics.
- bug #11b: table-cell scoring ranked IP/URL/user-agent log noise at the very
  top of the register. Such cells must now be demoted below real insights.
- bug #11c: "Top 3 account for 0.0%" for <3-value categorical columns.

The files live in C:/Users/Ag1Le/Documents/realworld_test/input/. If they are
absent the tests skip (they require the one-time download documented in the
assessment), so the suite still runs anywhere.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import step1_preprocessor_v2_full as m

REAL_DIR = Path(r"C:\Users\Ag1Le\Documents\realworld_test\input")
XLSX = REAL_DIR / "supermarket_sales.xlsx"
PPTX = REAL_DIR / "Performance.pptx"


def _have_real_files():
    return XLSX.is_file() and PPTX.is_file()


@pytest.fixture(scope="module")
def real_register(tmp_path_factory):
    if not _have_real_files():
        pytest.skip("real-world test files not downloaded (see realworld_test/INSIGHT_QUALITY_ASSESSMENT.md)")
    out = tmp_path_factory.mktemp("realworld_out")
    p = m.ImpactSlidePreprocessorV2(input_path=str(REAL_DIR), output_dir=str(out),
                                    filter_level="permissive")
    p.run()
    return json.load(open(out / "evidence_register_seed.json"))


# --------------------------------------------------------------------------- #
# Cross-file false-positive regression (bug #11a)
# --------------------------------------------------------------------------- #
class TestCrossFileNoFalsePositives:
    def test_no_spurious_numeric_cross_file_between_unrelated_files(self, real_register):
        """supermarket_sales.xlsx and Performance.pptx share no real metrics.
        Previously 10 spurious 'Numeric value N appears in both...' entries
        (for 5,6,10,13,17,33,36,42,48) were emitted at p=0.88. Must now be 0."""
        numeric_cross = [e for e in real_register
                         if e["insight_type"] == "cross_file_metric"
                         and "Numeric value" in e["text"]]
        assert numeric_cross == [], \
            f"expected no numeric cross-file false positives, got {len(numeric_cross)}"


# --------------------------------------------------------------------------- #
# Table-cell noise demotion regression (bug #11b)
# --------------------------------------------------------------------------- #
class TestTableCellNoiseDemoted:
    def test_ip_address_not_top_evidence(self, real_register):
        """The Apache log-format table contains '222.127.111.234' (an IP).
        Previously it was the #1 evidence overall at p=0.92. It must no longer
        outrank genuine Excel insights at the top of the register."""
        top = real_register[:5]
        for e in top:
            assert "222.127.111.234" not in e["text"], \
                f"IP noise ranked in top 5: {e['evidence_id']} p={e['priority_score']}"

    def test_noise_cells_scored_below_real_insights(self, real_register):
        excel = [e for e in real_register if e["source_file"] == "supermarket_sales.xlsx"
                 and e["insight_type"] == "numeric_range"]
        cells = [e for e in real_register if e["insight_type"] == "table_cell"]
        assert excel and cells
        best_excel = max(e["priority_score"] for e in excel)
        # Any surviving noise-looking cell must be below real Excel insights.
        noise = [c for c in cells if any(s in c["text"] for s in
                  ("222.127", "Mozilla", "GET /", "HTTP/1.1"))]
        for n in noise:
            assert n["priority_score"] < best_excel, \
                f"noise cell {n['text'][:40]!r} (p={n['priority_score']}) >= real insight ({best_excel})"

    def test_noise_helper_catches_known_noise(self):
        """Direct unit check on the noise detector."""
        assert m._looks_like_noise_cell("222.127.111.234") is True
        assert m._looks_like_noise_cell("GET /sander/SanderMugshot2.jpg HTTP/1.1") is True
        assert m._looks_like_noise_cell("Mozilla/5.0 (Windows; U;) Firefox/2.0.0.13") is True
        assert m._looks_like_noise_cell("Client IP") is False
        assert m._looks_like_noise_cell("1000") is False


# --------------------------------------------------------------------------- #
# top_3_pct correctness regression (bug #11c)
# --------------------------------------------------------------------------- #
class TestTop3PctCorrect:
    def test_low_cardinality_columns_report_full_coverage(self, real_register):
        """Customer type / Gender have 2 unique values; they must report
        100.0% coverage, not 0.0%."""
        low = [e for e in real_register
               if e["insight_type"] == "categorical_distribution"
               and e.get("column_name") in ("Customer type", "Gender")]
        assert low, "expected low-cardinality categorical evidence"
        for e in low:
            assert "100.0%" in e["text"], e["text"]
            # The old bug printed 'account for 0.0%'; the fix prints '100.0%'.
            # ('100.0%' happens to contain '0.0%' as a substring, so check the
            # full buggy phrase instead.)
            assert "account for 0.0%" not in e["text"], e["text"]


# --------------------------------------------------------------------------- #
# Sanity: real insights still present (no regression in core seeding)
# --------------------------------------------------------------------------- #
class TestRealInsightsStillPresent:
    def test_excel_numeric_ranges_present(self, real_register):
        ranges = [e for e in real_register
                  if e["source_file"] == "supermarket_sales.xlsx"
                  and e["insight_type"] == "numeric_range"]
        assert ranges, "expected Excel numeric-range evidence"
        blob = " ".join(e["text"] for e in ranges)
        for col in ("Unit price", "Total", "Rating", "gross income"):
            assert col in blob, f"missing real column insight: {col}"

    def test_pptx_speaker_notes_present(self, real_register):
        notes = [e for e in real_register if e["insight_type"] == "speaker_notes_insight"]
        assert notes, "expected PPTX speaker-notes evidence"

    def test_register_is_priority_sorted(self, real_register):
        scores = [e["priority_score"] for e in real_register]
        assert scores == sorted(scores, reverse=True)
