"""Tests for evidence post-processing methods:
_get_filter_thresholds, _deduplicate_evidence, _apply_boost_rules,
_find_cross_file_relationships.
"""
from __future__ import annotations

import pytest

import step1_preprocessor_v2_full as m


@pytest.fixture()
def pp():
    return m.ImpactSlidePreprocessorV2(input_path=".", output_dir="./_unused")


# --------------------------------------------------------------------------- #
# _get_filter_thresholds
# --------------------------------------------------------------------------- #
class TestFilterThresholds:
    def test_conservative_default(self, pp):
        t = pp._get_filter_thresholds()
        assert t["min_non_null_ratio"] == 0.10
        assert t["max_unique_ratio"] == 0.90
        assert t["min_priority"] == 0.25

    def test_moderate(self, pp):
        pp.filter_level = "moderate"
        t = pp._get_filter_thresholds()
        assert t["min_priority"] == 0.15

    def test_permissive(self, pp):
        pp.filter_level = "permissive"
        t = pp._get_filter_thresholds()
        assert t["min_non_null_ratio"] == 0.02

    def test_unknown_falls_back_conservative(self, pp):
        pp.filter_level = "bogus"
        t = pp._get_filter_thresholds()
        assert t["min_priority"] == 0.25


# --------------------------------------------------------------------------- #
# _deduplicate_evidence
# --------------------------------------------------------------------------- #
class TestDeduplicate:
    def _ev(self, text, prio=0.5):
        return {"evidence_id": "E0001", "insight_type": "x", "text": text, "priority_score": prio}

    def test_empty(self, pp):
        assert pp._deduplicate_evidence([]) == []

    def test_keeps_highest_priority_for_dup(self, pp):
        evs = [self._ev("same text", 0.5), self._ev("same text", 0.9)]
        out = pp._deduplicate_evidence(evs)
        assert len(out) == 1
        assert out[0]["priority_score"] == 0.9

    def test_case_and_whitespace_insensitive(self, pp):
        evs = [self._ev("  Hello   World  ", 0.5), self._ev("hello world", 0.7)]
        out = pp._deduplicate_evidence(evs)
        assert len(out) == 1

    def test_distinct_kept(self, pp):
        evs = [self._ev("alpha", 0.5), self._ev("beta", 0.5)]
        assert len(pp._deduplicate_evidence(evs)) == 2

    def test_empty_text_dropped(self, pp):
        evs = [self._ev("", 0.9), self._ev("real", 0.5)]
        assert len(pp._deduplicate_evidence(evs)) == 1


# --------------------------------------------------------------------------- #
# _apply_boost_rules
# --------------------------------------------------------------------------- #
class TestApplyBoost:
    def _ev(self, text, prio=0.5):
        return {"insight_type": "x", "text": text, "priority_score": prio}

    def test_no_keywords_noop(self, pp):
        pp.boost_keywords = []
        ev = self._ev("recommend growth", 0.5)
        pp._apply_boost_rules([ev])
        assert ev["priority_score"] == 0.5

    def test_boosts_once(self, pp):
        pp.boost_keywords = ["recommend"]
        ev = self._ev("we recommend this", 0.5)
        pp._apply_boost_rules([ev])
        assert ev["priority_score"] == 0.65
        assert ev.get("boosted_by_rule") == "recommend"

    def test_caps_at_098(self, pp):
        pp.boost_keywords = ["recommend"]
        ev = self._ev("recommend", 0.95)
        pp._apply_boost_rules([ev])
        assert ev["priority_score"] == 0.98

    def test_case_insensitive(self, pp):
        pp.boost_keywords = ["RECOMMEND"]
        ev = self._ev("We Recommend", 0.5)
        pp._apply_boost_rules([ev])
        assert ev["priority_score"] == 0.65


# --------------------------------------------------------------------------- #
# _find_cross_file_relationships
# --------------------------------------------------------------------------- #
class TestCrossFile:
    def _xlsx_ev(self, text, prio=0.5):
        return {"source_file": "data.xlsx", "insight_type": "x", "text": text, "priority_score": prio}

    def _pptx_ev(self, text, prio=0.5):
        return {"source_file": "deck.pptx", "insight_type": "x", "text": text, "priority_score": prio}

    def test_no_overlap_returns_empty(self, pp):
        out = pp._find_cross_file_relationships([self._xlsx_ev("alpha"), self._pptx_ev("beta")])
        assert out == []

    def test_shared_entity(self, pp):
        evs = [self._xlsx_ev("North region grew"), self._pptx_ev("North is key")]
        out = pp._find_cross_file_relationships(evs)
        assert any("North" in e["text"] for e in out)

    def test_shared_numeric_above_threshold(self, pp):
        """Distinctive numeric values (decimals or integers >= 100) that appear
        in both files are surfaced as cross-file evidence."""
        evs = [self._xlsx_ev("Revenue 1034 million"), self._pptx_ev("hit 1034 this quarter")]
        out = pp._find_cross_file_relationships(evs)
        assert any("1034" in e["text"] for e in out)

    def test_trivial_number_below_threshold_ignored(self, pp):
        """Bare small integers (e.g. 1, 42) must NOT produce cross-file matches —
        they collide constantly across unrelated files and create false
        positives (regression for the real-world supermarket vs Apache-deck case)."""
        evs = [self._xlsx_ev("count 42 items"), self._pptx_ev("42 things happened")]
        out = pp._find_cross_file_relationships(evs)
        assert out == []

    def test_decimal_numeric_is_distinctive(self, pp):
        """Decimal values are treated as distinctive metrics (not noise)."""
        evs = [self._xlsx_ev("margin 99.96 percent"), self._pptx_ev("reached 99.96")]
        out = pp._find_cross_file_relationships(evs)
        assert any("99.96" in e["text"] for e in out)

    def test_dynamic_entity_derived_from_excel_categorical_values(self, pp):
        """bug #12 fix: entity candidates are derived from the Excel's actual
        categorical column values, not just a hardcoded 7-word list. A city
        name that appears in both the Excel data and the PPTX narrative must be
        surfaced even though it isn't north/south/east/west/enterprise/smb/startup."""
        pp.excel_profiles = [{
            "status": "ok",
            "sheets": [{
                "categorical_profiles": [{
                    "column": "City",
                    "top_values": [{"value": "Yangon", "count": 5},
                                   {"value": "Mandalay", "count": 3}]
                }]
            }]
        }]
        evs = [self._xlsx_ev("Sheet1: 'City' has 3 unique values (Yangon, Mandalay, Naypyitaw)"),
               self._pptx_ev("Yangon branch showed strong growth")]
        out = pp._find_cross_file_relationships(evs)
        assert any("Yangon" in e["text"] for e in out), \
            "expected dynamically-derived entity 'Yangon' to be surfaced"

    def test_short_keyword_uses_word_boundary(self, pp):
        """Short keywords (<=4 chars) must match on word boundaries so 'east'
        doesn't fire inside 'yeast' or 'beast'."""
        evs = [self._xlsx_ev("yeast infection rates"), self._pptx_ev("yeast again")]
        out = pp._find_cross_file_relationships(evs)
        assert not any("'East'" in e["text"] for e in out)

    def test_only_excel_returns_empty(self, pp):
        out = pp._find_cross_file_relationships([self._xlsx_ev("North")])
        assert out == []

    def test_only_pptx_returns_empty(self, pp):
        out = pp._find_cross_file_relationships([self._pptx_ev("North")])
        assert out == []
