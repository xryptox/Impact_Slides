"""Unit tests for module-level pure helper functions in step1_preprocessor_v2_full."""
from __future__ import annotations

import math
import pytest
import pandas as pd

import step1_preprocessor_v2_full as m


# --------------------------------------------------------------------------- #
# clean_text
# --------------------------------------------------------------------------- #
class TestCleanText:
    def test_nan(self):
        assert m.clean_text(float("nan")) == ""

    def test_none(self):
        assert m.clean_text(None) == ""

    def test_strips_whitespace(self):
        assert m.clean_text("  hello  ") == "hello"

    def test_zero_is_kept(self):
        assert m.clean_text(0) == "0"

    def test_float(self):
        assert m.clean_text(3.5) == "3.5"

    def test_empty_string(self):
        assert m.clean_text("") == ""


# --------------------------------------------------------------------------- #
# get_column_letter / excel_addr
# --------------------------------------------------------------------------- #
class TestColumnLetter:
    @pytest.mark.parametrize("idx,letter", [
        (1, "A"), (2, "B"), (26, "Z"), (27, "AA"), (28, "AB"),
        (52, "AZ"), (53, "BA"), (702, "ZZ"), (703, "AAA"),
    ])
    def test_letter(self, idx, letter):
        assert m.get_column_letter(idx) == letter

    def test_excel_addr(self):
        assert m.excel_addr(1, 1) == "A1"
        assert m.excel_addr(10, 27) == "AA10"


# --------------------------------------------------------------------------- #
# safe_stat
# --------------------------------------------------------------------------- #
class TestSafeStat:
    def test_empty_returns_none(self):
        assert m.safe_stat([], min) is None

    def test_all_nan_returns_none(self):
        assert m.safe_stat([float("nan"), float("nan")], min) is None

    def test_single_value(self):
        assert m.safe_stat([5.0], min) == 5.0

    def test_min_max_mean(self):
        assert m.safe_stat([1, 2, 3], min) == 1.0
        assert m.safe_stat([1, 2, 3], max) == 3.0
        assert m.safe_stat([1, 2, 3], statistics_mean) == 2.0  # noqa

    def test_rounds_to_four(self):
        assert m.safe_stat([1.111111], lambda v: v[0]) == 1.1111

    def test_ignores_none(self):
        assert m.safe_stat([None, 2.0, None, 4.0], max) == 4.0


def statistics_mean(vals):
    import statistics
    return statistics.mean(vals)


# --------------------------------------------------------------------------- #
# compact_value
# --------------------------------------------------------------------------- #
class TestCompactValue:
    def test_nan(self):
        assert m.compact_value(float("nan")) is None

    def test_float_rounded(self):
        assert m.compact_value(3.14159265) == 3.1416

    def test_int_kept(self):
        assert m.compact_value(5) == 5

    def test_str_kept(self):
        assert m.compact_value("hello") == "hello"


# --------------------------------------------------------------------------- #
# extract_advanced_metrics
# --------------------------------------------------------------------------- #
class TestExtractAdvancedMetrics:
    def test_empty(self):
        assert m.extract_advanced_metrics("") == []

    def test_percentage(self):
        r = m.extract_advanced_metrics("Growth was +23% last year")
        assert any(x["type"] == "percentage" for x in r)

    def test_currency_variants(self):
        for cur in ["$4.2M", "€1,000", "£50K"]:
            r = m.extract_advanced_metrics(f"Revenue {cur}")
            assert any(x["type"] == "currency" for x in r), cur

    def test_multiplier(self):
        r = m.extract_advanced_metrics("3x increase and 2.5× growth")
        mults = [x for x in r if x["type"] == "multiplier"]
        assert len(mults) >= 2

    def test_range(self):
        r = m.extract_advanced_metrics("Margin between 12-18%")
        assert any(x["type"] == "range" for x in r)

    def test_cap_at_ten(self):
        text = "\n".join(f"{i}%" for i in range(20))
        assert len(m.extract_advanced_metrics(text)) <= 10


# --------------------------------------------------------------------------- #
# contains_insight_language
# --------------------------------------------------------------------------- #
class TestContainsInsightLanguage:
    def test_empty(self):
        assert m.contains_insight_language("") == 0.0

    def test_no_keywords(self):
        assert m.contains_insight_language("just some random words here") == 0.0

    def test_scales(self):
        assert 0 < m.contains_insight_language("a key risk") < 1.0
        assert m.contains_insight_language("recommend critical significant growth decline") == 1.0

    def test_case_insensitive(self):
        assert m.contains_insight_language("KEY RECOMMENDATION") > 0


# --------------------------------------------------------------------------- #
# make_unique_columns
# --------------------------------------------------------------------------- #
class TestMakeUniqueColumns:
    def test_dedups(self):
        cols = m.make_unique_columns(["A", "B", "A", "A", "C"])
        assert cols == ["A", "B", "A_2", "A_3", "C"]

    def test_empty_becomes_column_letter(self):
        cols = m.make_unique_columns(["", None, "X"])
        assert cols[0].startswith("Column ")
        assert cols[1].startswith("Column ")
        assert cols[2] == "X"

    def test_truncates_long(self):
        cols = m.make_unique_columns(["A" * 200])
        assert len(cols[0]) <= 80


# --------------------------------------------------------------------------- #
# is_likely_identifier_column
# --------------------------------------------------------------------------- #
class TestIsIdentifierColumn:
    def test_sno(self):
        assert m.is_likely_identifier_column("S.No", pd.Series([1, 2, 3])) is True

    def test_serial(self):
        assert m.is_likely_identifier_column("Serial Number", pd.Series(range(20))) is True

    def test_id_name_match_overrides_values(self):
        # Name match is a strong signal regardless of the value pattern.
        assert m.is_likely_identifier_column("ID", pd.Series([5, 4, 3, 2, 1])) is True

    def test_metric_incrementing_by_one_not_identifier(self):
        # The false positive this heuristic now prevents: a real metric that
        # happens to increment by exactly 1 must NOT be filtered as an ID.
        assert m.is_likely_identifier_column("Revenue", pd.Series([1, 2, 3, 4, 5])) is False
        assert m.is_likely_identifier_column("Count", pd.Series([10, 11, 12, 13])) is False

    def test_descending_business_column_not_identifier(self):
        assert m.is_likely_identifier_column("Score", pd.Series([5, 4, 3, 2, 1])) is False

    def test_generic_unnamed_row_index_is_identifier(self):
        # An unlabeled column that is exactly 1..N is a row-number column.
        assert m.is_likely_identifier_column("Column A", pd.Series([1, 2, 3, 4, 5])) is True

    def test_generic_zero_based_row_index_is_identifier(self):
        assert m.is_likely_identifier_column("Column A", pd.Series([0, 1, 2, 3, 4])) is True

    def test_generic_float_integers_treated_as_row_index(self):
        assert m.is_likely_identifier_column("Column A", pd.Series([1.0, 2.0, 3.0, 4.0])) is True

    def test_generic_non_contiguous_not_identifier(self):
        # Gap in the sequence -> not a row index.
        assert m.is_likely_identifier_column("Column A", pd.Series([1, 2, 4, 5])) is False

    def test_generic_descending_not_identifier(self):
        assert m.is_likely_identifier_column("Column A", pd.Series([5, 4, 3, 2, 1])) is False

    def test_generic_starting_above_one_not_identifier(self):
        # 5..9 is contiguous but doesn't start at 0/1 -> not a row index.
        assert m.is_likely_identifier_column("Column A", pd.Series([5, 6, 7, 8, 9])) is False

    def test_generic_with_duplicates_not_identifier(self):
        assert m.is_likely_identifier_column("Column A", pd.Series([1, 2, 2, 3])) is False

    def test_not_identifier(self):
        assert m.is_likely_identifier_column("Revenue", pd.Series([100, 200, 150])) is False

    def test_text_not_identifier(self):
        assert m.is_likely_identifier_column("Region", pd.Series(["N", "S", "E"])) is False


# --------------------------------------------------------------------------- #
# is_generic_system_column
# --------------------------------------------------------------------------- #
class TestIsGenericSystemColumn:
    @pytest.mark.parametrize("name", ["created_at", "modified_by", "is_active", "has_flag",
                                       "internal_id", "guid", "uuid", "checksum"])
    def test_generic(self, name):
        assert m.is_generic_system_column(name) is True

    @pytest.mark.parametrize("name", ["Revenue", "Region", "Status", "Customer Name"])
    def test_business(self, name):
        assert m.is_generic_system_column(name) is False


# --------------------------------------------------------------------------- #
# _looks_like_noise_cell (table-cell noise detection — bug #11 fix)
# --------------------------------------------------------------------------- #
class TestLooksLikeNoiseCell:
    @pytest.mark.parametrize("val", [
        "222.127.111.234",                         # IPv4
        "2001:0db8:85a3::8a2e:0370:7334",          # IPv6
        "https://example.com/path",
        "http://people.apache.org/gallery.html",
        "www.example.com",
        "/usr/local/bin/tesseract",
        "C:\\Users\\Ag1Le\\file.txt",
        "GET /sander/SanderMugshot2.jpg HTTP/1.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1) Gecko/20080311 Firefox/2.0.0.13",
        "[09/Apr/2008:07:46:54 +0000]",
        "/cgi-bin/blosxom.cgi/index",
    ])
    def test_noise(self, val):
        assert m._looks_like_noise_cell(val) is True, val

    @pytest.mark.parametrize("val", [
        "Client IP",                  # header text
        "Revenue",
        "North region grew strongly",
        "1000",                       # genuine number
        "Q3 Impact Review",
        "",
    ])
    def test_not_noise(self, val):
        assert m._looks_like_noise_cell(val) is False, val


# --------------------------------------------------------------------------- #
# calculate_evidence_priority_score
# --------------------------------------------------------------------------- #
class TestCalculateEvidencePriorityScore:
    def test_identifier_low(self):
        assert m.calculate_evidence_priority_score("ID", "numeric", is_identifier=True) == 0.15

    def test_numeric_boosted(self):
        s = m.calculate_evidence_priority_score("Revenue", "numeric", non_null_ratio=1.0)
        assert s > 0.6

    def test_categorical_high_cardinality_penalized(self):
        s_low = m.calculate_evidence_priority_score("Cat", "categorical", unique_ratio=0.2,
                                                     non_null_ratio=1.0, has_business_name=True)
        s_high = m.calculate_evidence_priority_score("Cat", "categorical", unique_ratio=0.9,
                                                      non_null_ratio=1.0, has_business_name=True)
        assert s_low > s_high

    def test_no_business_name_penalized(self):
        with_name = m.calculate_evidence_priority_score("Revenue", "numeric",
                                                        non_null_ratio=1.0, has_business_name=True)
        without_name = m.calculate_evidence_priority_score("Column A", "numeric",
                                                            non_null_ratio=1.0, has_business_name=False)
        assert without_name < with_name
        assert 0.0 <= without_name <= 1.0

    def test_clamped_to_unit(self):
        s = m.calculate_evidence_priority_score("X", "numeric", non_null_ratio=1.0)
        assert 0.0 <= s <= 1.0
