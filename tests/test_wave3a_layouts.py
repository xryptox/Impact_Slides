"""Tests for Wave 3a: Strategic & Structural Layouts (T6 #14).

risk_opportunity, recommendation_with_rationale, section_divider, before_after_detailed.
"""

from __future__ import annotations

import re

import pytest

from impact_slides.renderer_v2.layout.dispatch import render_slide
from impact_slides.renderer_v2.schemas import validate_slide


def _make_slide(layout_type: str, **overrides) -> dict:
    base = {
        "slide_number": 1,
        "layout_type": layout_type,
        "title": "Test",
        "content": {},
    }
    base.update(overrides)
    return base


def _count(html: str, token: str) -> int:
    pat = re.compile(rf'class="([^"]*)"')
    total = 0
    for m in pat.finditer(html):
        total += m.group(1).split().count(token)
    return total


class TestRiskOpportunity:
    def test_renders_two_columns(self):
        slide = _make_slide(
            "risk_opportunity",
            content={"risks": ["Risk 1", "Risk 2"], "opportunities": ["Opp 1", "Opp 2"]},
        )
        html = render_slide(slide, total=1, notes="")
        assert "risk-column" in html
        assert "opportunity-column" in html

    def test_cards_have_card(self):
        slide = _make_slide(
            "risk_opportunity",
            content={"risks": ["Risk 1"], "opportunities": ["Opp 1"]},
        )
        html = render_slide(slide, total=1, notes="")
        assert _count(html, "card") >= 2

    def test_schema_validates(self):
        slide = _make_slide("risk_opportunity", content={"bullets": ["A"]})
        model, err = validate_slide(slide)
        assert model is not None
        assert err is None

    def test_density_does_not_exceed_stage(self):
        slide = _make_slide(
            "risk_opportunity",
            content={"risks": ["R" + str(i) for i in range(6)], "opportunities": ["O" + str(i) for i in range(6)]},
        )
        html = render_slide(slide, total=1, notes="")
        # Should cap at 4 per side
        assert _count(html, "risk-card") <= 4
        assert _count(html, "opportunity-card") <= 4


class TestRecommendationWithRationale:
    def test_renders_recommendation_head(self):
        slide = _make_slide(
            "recommendation_with_rationale",
            content={"recommendation": "Invest now", "bullets": ["Reason 1", "Reason 2"]},
        )
        html = render_slide(slide, total=1, notes="")
        assert "Invest now" in html
        assert "recommendation-head" in html

    def test_evidence_cards_have_card(self):
        slide = _make_slide(
            "recommendation_with_rationale",
            content={"bullets": ["Reason 1", "Reason 2", "Reason 3"]},
        )
        html = render_slide(slide, total=1, notes="")
        assert _count(html, "card") >= 3

    def test_schema_validates(self):
        slide = _make_slide("recommendation_with_rationale", content={"headline": "H"})
        model, err = validate_slide(slide)
        assert model is not None
        assert err is None


class TestSectionDivider:
    def test_renders_message_and_accent(self):
        slide = _make_slide(
            "section_divider",
            content={"headline": "Section Title", "subtitle": "Sub"},
        )
        html = render_slide(slide, total=1, notes="")
        assert "Section Title" in html
        assert "accent-line" in html
        assert "section-subtitle" in html

    def test_falls_back_to_title(self):
        slide = _make_slide("section_divider", title="Fallback Title")
        html = render_slide(slide, total=1, notes="")
        assert "Fallback Title" in html

    def test_schema_validates(self):
        slide = _make_slide("section_divider")
        model, err = validate_slide(slide)
        assert model is not None
        assert err is None


class TestBeforeAfterDetailed:
    def test_renders_before_after_panels(self):
        slide = _make_slide(
            "before_after_detailed",
            content={"before": "Old", "after": "New", "steps": ["Step 1", "Step 2"]},
        )
        html = render_slide(slide, total=1, notes="")
        assert "before-panel" in html
        assert "after-panel" in html
        assert "transformation-steps" in html

    def test_panels_have_card(self):
        slide = _make_slide(
            "before_after_detailed",
            content={"before": "Old", "after": "New"},
        )
        html = render_slide(slide, total=1, notes="")
        assert _count(html, "card") >= 2

    def test_steps_capped_at_four(self):
        slide = _make_slide(
            "before_after_detailed",
            content={"steps": ["S" + str(i) for i in range(8)]},
        )
        html = render_slide(slide, total=1, notes="")
        # Count step elements (not the container "transformation-steps")
        assert html.count('class="transformation-step"') <= 4

    def test_schema_validates(self):
        slide = _make_slide("before_after_detailed", content={"bullets": ["A"]})
        model, err = validate_slide(slide)
        assert model is not None
        assert err is None


class TestDispatchRouting:
    def test_wave3a_layouts_routed_correctly(self):
        for lt in (
            "risk_opportunity",
            "recommendation_with_rationale",
            "section_divider",
            "before_after_detailed",
        ):
            slide = _make_slide(lt)
            html = render_slide(slide, total=1, notes="")
            assert f'data-layout="{lt}"' in html
