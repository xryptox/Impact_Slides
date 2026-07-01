"""Table-driven tests for ImpactSlidePreprocessorV2.classify_slide.

Includes the regression for bug #1: classify_slide referenced `diagram_score`
before assignment in the section-divider branch, raising UnboundLocalError
(which was silently swallowed by extract_pptx, marking the whole deck as error).
"""
from __future__ import annotations

import pytest

import step1_preprocessor_v2_full as m


@pytest.fixture()
def classifier():
    return m.ImpactSlidePreprocessorV2(input_path=".", output_dir="./_unused")


# --------------------------------------------------------------------------- #
# Regression: bug #1 — UnboundLocalError on section title
# --------------------------------------------------------------------------- #
class TestSectionCrashRegression:
    def test_section_title_does_not_crash(self, classifier):
        """Previously: UnboundLocalError: cannot access local variable 'diagram_score'."""
        r = classifier.classify_slide(
            title="Section Foo", slide_idx=3, total_slides=10, is_section_slide=False,
        )
        assert r["type"] == "section"
        assert r["priority_for_evidence"] == 0.22

    def test_is_section_flag_short_circuits(self, classifier):
        r = classifier.classify_slide(title="Anything", slide_idx=3, is_section_slide=True)
        assert r["type"] == "section"

    def test_real_diagram_with_section_title_not_misclassified(self, classifier):
        """A genuine process diagram whose title happens to contain 'section' must
        NOT be collapsed to a section divider (the diagram_score<3 guard)."""
        r = classifier.classify_slide(
            title="Section", slide_idx=3, total_slides=10,
            has_process_diagram=True, shape_count=8, word_count=20,
        )
        assert r["type"] == "diagram_process"


# --------------------------------------------------------------------------- #
# Table-driven branch coverage
# --------------------------------------------------------------------------- #
BRANCH_CASES = [
    # (kwargs, expected_type)
    # Title slide
    (dict(title="Deck", slide_idx=1, total_slides=10, word_count=10), "title"),
    # Agenda
    (dict(title="Agenda", slide_idx=2, total_slides=10), "agenda"),
    (dict(title="Overview", slide_idx=2, total_slides=10), "agenda"),
    (dict(title="Table of Contents", slide_idx=2, total_slides=10), "agenda"),
    (dict(title="Roadmap", slide_idx=2, total_slides=10), "agenda"),
    # Section divider (flag)
    (dict(title="Part 1", slide_idx=3, total_slides=10, is_section_slide=True), "section"),
    # Thank you
    (dict(title="Thank You", slide_idx=10, total_slides=10), "thank_you"),
    (dict(title="Q&A", slide_idx=10, total_slides=10), "thank_you"),
    # Conclusion
    (dict(title="Summary", slide_idx=9, total_slides=10), "conclusion"),
    (dict(title="Key Recommendations", slide_idx=9, total_slides=10), "conclusion"),
    (dict(title="Next Steps", slide_idx=9, total_slides=10), "conclusion"),
    # Data-rich
    (dict(title="Metrics", slide_idx=5, total_slides=10, chart_count=2, table_count=1), "data_mixed"),
    (dict(title="Chart", slide_idx=5, total_slides=10, chart_count=1), "data_chart"),
    (dict(title="Table", slide_idx=5, total_slides=10, table_count=1), "data_table"),
    # Diagram/process
    (dict(title="Flow", slide_idx=5, total_slides=10, has_process_diagram=True), "diagram_process"),
    (dict(title="Flow", slide_idx=5, total_slides=10, has_diagram_like_shapes=True,
          has_arrows_connectors=True), "diagram_process"),
]


@pytest.mark.parametrize("kwargs,expected", BRANCH_CASES)
def test_classify_branches(classifier, kwargs, expected):
    r = classifier.classify_slide(**kwargs)
    assert r["type"] == expected, f"{kwargs} -> {r['type']}"


# --------------------------------------------------------------------------- #
# Structural / numeric assertions on the returned dict
# --------------------------------------------------------------------------- #
class TestClassificationShape:
    def test_returns_required_keys(self, classifier):
        r = classifier.classify_slide(title="X", slide_idx=2, total_slides=10)
        for k in ("type", "confidence", "evidence_tags", "recommended_evidence_types",
                  "position", "priority_for_evidence"):
            assert k in r

    def test_position_first(self, classifier):
        r = classifier.classify_slide(title="Deck", slide_idx=1, total_slides=10, word_count=40)
        assert r["position"] == "first"

    def test_position_last(self, classifier):
        r = classifier.classify_slide(title="End", slide_idx=10, total_slides=10, word_count=40)
        assert r["position"] == "last"

    def test_priority_within_unit_range(self, classifier):
        for kw in [
            dict(slide_idx=2, total_slides=10, word_count=40),
            dict(slide_idx=2, total_slides=10, chart_count=1),
            dict(slide_idx=5, total_slides=10, has_process_diagram=True),
        ]:
            r = classifier.classify_slide(title="t", **kw)
            assert 0.0 <= r["priority_for_evidence"] <= 1.0

    def test_low_value_visual_heavy(self, classifier):
        r = classifier.classify_slide(title="Pics", slide_idx=3, total_slides=10,
                                      word_count=5, picture_count=4)
        assert r["type"] == "low_value"
        assert r["priority_for_evidence"] == 0.15

    def test_content_insight_for_wordy_slide(self, classifier):
        r = classifier.classify_slide(title="Deep Dive", slide_idx=3, total_slides=10,
                                      word_count=40)
        assert r["type"] == "content_insight"

    def test_content_light_default(self, classifier):
        r = classifier.classify_slide(title="Sparse", slide_idx=3, total_slides=10, word_count=5)
        assert r["type"] == "content_light"
