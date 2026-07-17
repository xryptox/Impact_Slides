"""Tests for Wave 4b: Process, Deep Dive & Circular Layouts (T9 #17).

process_with_decisions, source_deep_dive, circular_process.
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


class TestProcessWithDecisions:
    def test_renders_steps_and_decisions(self):
        slide = _make_slide(
            "process_with_decisions",
            content={"steps": ["Step 1", "Step 2"], "decisions": ["Go?", "Continue?"]},
        )
        html = render_slide(slide, total=1, notes="")
        assert "process-step" in html
        assert "decision-node" in html

    def test_cards_have_card(self):
        slide = _make_slide(
            "process_with_decisions",
            content={"steps": ["A", "B"], "decisions": ["D1"]},
        )
        html = render_slide(slide, total=1, notes="")
        assert _count(html, "card") >= 3  # 2 steps + 1 decision

    def test_schema_validates(self):
        slide = _make_slide("process_with_decisions", content={"bullets": ["A"]})
        model, err = validate_slide(slide)
        assert model is not None
        assert err is None


class TestSourceDeepDive:
    def test_renders_source_cards(self):
        slide = _make_slide(
            "source_deep_dive",
            content={"bullets": ["Source 1", "Source 2", "Source 3"]},
        )
        html = render_slide(slide, total=1, notes="")
        assert "source-card" in html
        assert "Source 1" in html

    def test_cards_have_card(self):
        slide = _make_slide(
            "source_deep_dive",
            content={"bullets": ["A", "B", "C", "D"]},
        )
        html = render_slide(slide, total=1, notes="")
        assert _count(html, "card") == 4

    def test_capped_at_eight(self):
        slide = _make_slide(
            "source_deep_dive",
            content={"bullets": ["S" + str(i) for i in range(12)]},
        )
        html = render_slide(slide, total=1, notes="")
        assert _count(html, "source-card") == 8

    def test_schema_validates(self):
        slide = _make_slide("source_deep_dive", content={"bullets": ["A"]})
        model, err = validate_slide(slide)
        assert model is not None
        assert err is None


class TestCircularProcess:
    def test_renders_svg_loop(self):
        slide = _make_slide(
            "circular_process",
            visual_spec={"primary_visual": {"steps_or_data": ["Plan", "Do", "Check", "Act"]}},
        )
        html = render_slide(slide, total=1, notes="")
        assert "<svg" in html
        assert "Plan" in html

    def test_schema_validates(self):
        slide = _make_slide("circular_process", visual_spec={"primary_visual": {"steps_or_data": ["A"]}})
        model, err = validate_slide(slide)
        assert model is not None
        assert err is None


class TestDispatchRouting:
    def test_wave4b_layouts_routed_correctly(self):
        for lt in ("process_with_decisions", "source_deep_dive", "circular_process"):
            slide = _make_slide(lt)
            html = render_slide(slide, total=1, notes="")
            assert f'data-layout="{lt}"' in html
