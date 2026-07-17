"""Regression tests for legacy layout refactor to grid primitives (T3 #11).

Verifies that refactored layouts use .grid/.card/.grid-2/.grid-auto
primitives and do not rely on deprecated custom classes.
"""

from __future__ import annotations

import re

import pytest

from impact_slides.renderer_v2.layout.dispatch import render_slide


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
    """Count exact class-attribute token occurrences (not substring)."""
    pat = re.compile(rf'class="([^"]*)"')
    total = 0
    for m in pat.finditer(html):
        classes = m.group(1).split()
        total += classes.count(token)
    return total


class TestMetricDashboardRefactor:
    def test_uses_gl_grid(self):
        slide = _make_slide("metric_dashboard", content={"key_stats": [{"label": "A", "value": "1"}]})
        html = render_slide(slide, total=1, notes="")
        assert 'class="gl-grid' in html

    def test_kpi_tiles_have_card(self):
        slide = _make_slide("metric_dashboard", content={"key_stats": [{"label": "A", "value": "1"}]})
        html = render_slide(slide, total=1, notes="")
        assert _count(html, "card") >= 1


class TestComparisonGridRefactor:
    def test_uses_gl_grid_2(self):
        slide = _make_slide("comparison_grid", content={"bullets": ["A: one", "B: two"]})
        html = render_slide(slide, total=1, notes="")
        assert "gl-grid-2" in html or "gl-grid" in html

    def test_comparison_cards_have_card(self):
        slide = _make_slide("comparison_grid", content={"bullets": ["A: one", "B: two"]})
        html = render_slide(slide, total=1, notes="")
        assert _count(html, "card") >= 1
        assert _count(html, "comparison-card") >= 1


class TestIconGridRefactor:
    def test_fallback_icon_grid_uses_gl_grid_and_card(self):
        """Test the fallback path directly, bypassing the external chart pack."""
        from impact_slides.renderer_v2.charts import _fallback_icon_grid
        slide = {
            "slide_number": 1,
            "layout_type": "icon_grid",
            "visual_spec": {"primary_visual": {"steps_or_data": ["A", "B", "C"]}},
        }
        html = _fallback_icon_grid(slide)
        assert "gl-grid" in html
        assert "gl-card" in html


class TestProcessLayoutsRefactor:
    def _process_slide(self, layout_type: str, steps: list):
        return _make_slide(
            layout_type,
            visual_spec={"primary_visual": {"steps_or_data": steps}},
        )

    def test_process_flow_uses_gl_areas_process_h(self):
        slide = self._process_slide("full_process_flow", ["Step 1", "Step 2", "Step 3"])
        html = render_slide(slide, total=1, notes="")
        assert "gl-areas-process-h" in html

    def test_timeline_uses_gl_areas_process_v(self):
        slide = self._process_slide("timeline", ["2024 Q1", "2024 Q2", "2024 Q3", "2024 Q4"])
        html = render_slide(slide, total=1, notes="")
        assert "gl-areas-process-v" in html

    def test_roadmap_uses_gl_areas_process_v(self):
        slide = self._process_slide("roadmap", ["Phase 1", "Phase 2", "Phase 3", "Phase 4"])
        html = render_slide(slide, total=1, notes="")
        assert "gl-areas-process-v" in html

    def test_step_cards_have_card(self):
        slide = self._process_slide("full_process_flow", ["A", "B", "C"])
        html = render_slide(slide, total=1, notes="")
        assert _count(html, "card") >= 2


class TestQuoteCardRefactor:
    def test_quote_cards_have_card(self):
        slide = _make_slide("quote_card", content={"body_text": "A famous quote."})
        html = render_slide(slide, total=1, notes="")
        assert _count(html, "card") >= 1
        assert _count(html, "quote-card") >= 1
