"""Tests for profile_dataframe and Excel profiling, including the bug #2
regression: findings never carried 'location'/'column', so Excel evidence had
empty source_location and None column_name.
"""
from __future__ import annotations

import pytest
import pandas as pd

import step1_preprocessor_v2_full as m


@pytest.fixture()
def pp():
    return m.ImpactSlidePreprocessorV2(input_path=".", output_dir="./_unused", filter_level="permissive")


def _profile(pp, df, sheet="Sheet1"):
    # profile_dataframe expects a header-less frame (as produced by
    # pd.read_excel(header=None)). Convert a normal labelled DataFrame into
    # that format so tests can build inputs with named columns.
    raw = pd.DataFrame([df.columns.tolist()] + df.astype(object).values.tolist())
    return pp.profile_dataframe(raw, sheet, "excel")


# --------------------------------------------------------------------------- #
# Bug #2 regression: findings carry location + column
# --------------------------------------------------------------------------- #
class TestFindingsCarryLocation:
    def test_findings_carry_location_and_column(self, pp):
        df = pd.DataFrame({"Revenue": [100, 200, 300, 400], "Region": ["N", "S", "E", "W"]})
        prof = _profile(pp, df)
        for f in prof["findings"]:
            assert "location" in f and f["location"] == "Sheet1"
            assert "column" in f and f["column"] in ("Revenue", "Region")

    def test_evidence_register_has_column_and_source_location(self, pp, make_excel, make_preprocessor):
        p, inp, out = make_preprocessor(filter_level="permissive")
        make_excel(df=pd.DataFrame({"Revenue": [100, 200, 300, 400],
                                    "Region": ["N", "S", "E", "W"]}))
        p.run()
        import json
        ev = json.load(open(out / "evidence_register_seed.json"))
        excel_ev = [e for e in ev if e["source_file"].endswith(".xlsx")]
        assert excel_ev, "expected Excel-derived evidence"
        for e in excel_ev:
            if e["insight_type"] in ("numeric_range", "categorical_distribution"):
                assert e["source_location"] == "Sheet1"
                assert e["column_name"] in ("Revenue", "Region")


# --------------------------------------------------------------------------- #
# Empty / header detection
# --------------------------------------------------------------------------- #
class TestProfileDataframe:
    def test_empty_dataframe(self, pp):
        assert _profile(pp, pd.DataFrame())["status"] == "empty"

    def test_numeric_profile(self, pp):
        df = pd.DataFrame({"Rev": [10, 20, 30, 40, 50], "Region": ["N", "S", "N", "S", "E"]})
        prof = _profile(pp, df)
        assert any(c["column"] == "Rev" for c in prof["numeric_profiles"])
        n = [c for c in prof["numeric_profiles"] if c["column"] == "Rev"][0]
        assert n["min"] == 10.0 and n["max"] == 50.0

    def test_categorical_profile(self, pp):
        df = pd.DataFrame({"Region": ["N", "S", "N", "S", "E", "W"],
                           "Flag": ["a", "b", "a", "b", "a", "b"]})
        prof = _profile(pp, df)
        assert any(c["column"] == "Region" for c in prof["categorical_profiles"])

    def test_identifier_column_low_priority(self, pp):
        df = pd.DataFrame({"S.No": list(range(1, 21)), "Rev": [i * 10 for i in range(1, 21)]})
        prof = _profile(pp, df)
        # Identifier column should not produce a normal numeric range finding
        cols = [f.get("column") for f in prof["findings"]]
        assert "S.No" not in cols

    def test_header_row_detection(self, pp):
        # First row is junk, second row is the real header
        raw = pd.DataFrame([
            ["junk", "junk", "junk"],
            ["Revenue", "Region", "Status"],
            [100, "N", "Active"],
            [200, "S", "Inactive"],
            [300, "E", "Active"],
            [400, "W", "Active"],
        ])
        prof = pp.profile_dataframe(raw, "Sheet1", "excel")
        # Real header should be picked up; numeric 'Revenue' found
        assert any(c["column"] == "Revenue" for c in prof["numeric_profiles"])

    def test_multi_column_insight(self, pp):
        df = pd.DataFrame({"Rev": [10, 20, 30, 40, 50, 60],
                           "Region": ["N", "S", "N", "S", "E", "W"]})
        prof = _profile(pp, df)
        assert prof["multi_column_insights"], "expected a category-by-metric suggestion"

    def test_top3_pct_correct_for_low_cardinality(self, pp):
        """Regression for bug #11: columns with <3 unique values reported
        'Top 3 account for 0.0%' instead of the real coverage."""
        df = pd.DataFrame({"Gender": ["F", "M", "F", "M"],
                           "Region": ["N", "S", "N", "S"]})
        prof = _profile(pp, df)
        for f in prof["findings"]:
            if f.get("column") == "Gender":
                assert "100.0%" in f["text"], f["text"]
            if f.get("column") == "Region":
                assert "100.0%" in f["text"], f["text"]
