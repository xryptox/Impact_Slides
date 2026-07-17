"""Tests for Wave 3b: Data, Comparison & Process Layouts (T7 #15).

kpi_trend_cards, three_column_comparison, horizontal_process.
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


class TestKpiTrendCards:
    def test_renders_kpi_cards(self):
        slide = _make_slide(
            "kpi_trend_cards",
            content={"key_stats": [{"label": "Revenue", "value": "$1M", "trend": "up"}]},
        )
        html = render_slide(slide, total=1, notes="")
        assert "kpi-trend-card" in html
        assert "$1M" in html
        assert "▲" in html

    def test_trend_down_indicator(self):
        slide = _make_slide(
            "kpi_trend_cards",
            content={"key_stats": [{"label": "Cost", "value": "$500K", "trend": "down"}]},
        )
        html = render_slide(slide, total=1, notes="")
        assert "▼" in html

    def test_cards_have_card(self):
        slide = _make_slide(
            "kpi_trend_cards",
            content={"key_stats": [{"label": "A", "value": "1"}, {"label": "B", "value": "2"}]},
        )
        html = render_slide(slide, total=1, notes="")
        assert _count(html, "card") >= 2

    def test_schema_validates(self):
        slide = _make_slide("kpi_trend_cards", content={"key_stats": [{"label": "A", "value": "1"}]})
        model, err = validate_slide(slide)
        assert model is not None
        assert err is None


class TestThreeColumnComparison:
    def test_renders_three_columns(self):
        slide = _make_slide(
            "three_column_comparison",
            content={"bullets": ["Option A", "Option B", "Option C"]},
        )
        html = render_slide(slide, total=1, notes="")
        assert "gl-grid-3" in html
        assert "Option A" in html
        assert "Option B" in html
        assert "Option C" in html

    def test_pads_to_three(self):
        slide = _make_slide(
            "three_column_comparison",
            content={"bullets": ["Only one"]},
        )
        html = render_slide(slide, total=1, notes="")
        assert _count(html, "comparison-col") == 3

    def test_cards_have_card(self):
        slide = _make_slide(
            "three_column_comparison",
            content={"bullets": ["A", "B", "C"]},
        )
        html = render_slide(slide, total=1, notes="")
        assert _count(html, "card") == 3

    def test_schema_validates(self):
        slide = _make_slide("three_column_comparison", content={"bullets": ["A"]})
        model, err = validate_slide(slide)
        assert model is not None
        assert err is None


class TestHorizontalProcess:
    def test_renders_steps_and_arrows(self):
        slide = _make_slide(
            "horizontal_process",
            content={"bullets": ["Step 1", "Step 2", "Step 3"]},
        )
        html = render_slide(slide, total=1, notes="")
        assert "process-step" in html
        assert "process-arrow" in html
        assert html.count("process-arrow") == 2  # n-1 arrows

    def test_cards_have_card(self):
        slide = _make_slide(
            "horizontal_process",
            content={"bullets": ["A", "B", "C"]},
        )
        html = render_slide(slide, total=1, notes="")
        assert _count(html, "card") >= 3

    def test_schema_validates(self):
        slide = _make_slide("horizontal_process", content={"bullets": ["A"]})
        model, err = validate_slide(slide)
        assert model is not None
        assert err is None


class TestDispatchRouting:
    def test_wave3b_layouts_routed_correctly(self):
        for lt in ("kpi_trend_cards", "three_column_comparison", "horizontal_process"):
            slide = _make_slide(lt)
            html = render_slide(slide, total=1, notes="")
            assert f'data-layout="{lt}"' in html
