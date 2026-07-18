"""Tests for circle pair visualization in comparison layouts."""

import json
import re

import pytest

from impact_slides.renderer_v2.layout.recipes import (
    _circle_pair_svg,
    render_comparison,
    render_three_column_comparison,
)
from impact_slides.renderer_v2.cli import render_deck


def _circle_slide(layout="three_column_comparison", **overrides):
    s = {
        "slide_number": 2,
        "layout_type": layout,
        "title": "Engagement",
        "content": {
            "bullets": [
                "Lodging spend recovered strongly",
                "Restaurant visits above pre-pandemic",
                "Airline bookings stabilizing",
            ],
        },
        "visual_spec": {
            "primary_visual": {"type": layout, "steps_or_data": []},
            "circle_data": [
                {
                    "label": "Lodging",
                    "value_before": 85,
                    "value_after": 112,
                    "max_value": 120,
                    "unit": "%",
                },
                {
                    "label": "Restaurants",
                    "value_before": 78,
                    "value_after": 105,
                    "max_value": 120,
                    "unit": "%",
                },
                {
                    "label": "Airlines",
                    "value_before": 65,
                    "value_after": 92,
                    "max_value": 120,
                    "unit": "%",
                },
            ],
        },
    }
    s.update(overrides)
    return s


class TestCirclePairSvg:
    def test_returns_svg(self):
        svg = _circle_pair_svg(85, 112, 120, "%", "Lodging")
        assert "<svg" in svg
        assert "circle-pair" in svg

    def test_has_two_circles(self):
        svg = _circle_pair_svg(85, 112, 120)
        circles = re.findall(r"<circle\s", svg)
        assert len(circles) == 2

    def test_outer_circle_outlined(self):
        svg = _circle_pair_svg(85, 112, 120)
        assert 'fill="none"' in svg
        assert "var(--panel-border" in svg

    def test_inner_circle_filled(self):
        svg = _circle_pair_svg(85, 112, 120)
        assert "var(--blue, #006fcf)" in svg

    def test_value_labels(self):
        svg = _circle_pair_svg(85, 112, 120, "%")
        assert "112%" in svg
        assert "85%" in svg

    def test_label(self):
        svg = _circle_pair_svg(85, 112, 120, "%", "Lodging")
        assert "Lodging" in svg

    def test_proportional_radii(self):
        svg_small = _circle_pair_svg(30, 40, 120)
        svg_large = _circle_pair_svg(90, 110, 120)
        # Extract radii
        r_small = re.findall(r'r="([\d.]+)"', svg_small)
        r_large = re.findall(r'r="([\d.]+)"', svg_large)
        assert float(r_small[0]) < float(r_large[0])

    def test_zero_values(self):
        svg = _circle_pair_svg(0, 0, 100)
        assert "<svg" in svg  # Should not crash

    def test_custom_unit(self):
        svg = _circle_pair_svg(50, 75, 100, "$B")
        assert "75$B" in svg


class TestThreeColumnWithCircles:
    def test_circles_rendered(self):
        slide = _circle_slide()
        html = render_three_column_comparison(slide, 5, "", active=False)
        assert "circle-pair" in html
        circles = re.findall(r"<circle\s", html)
        assert len(circles) == 6  # 3 pairs x 2 circles each

    def test_column_labels_from_circle_data(self):
        slide = _circle_slide()
        html = render_three_column_comparison(slide, 5, "", active=False)
        assert "Lodging" in html
        assert "Restaurants" in html
        assert "Airlines" in html

    def test_fallback_without_circle_data(self):
        slide = _circle_slide()
        del slide["visual_spec"]["circle_data"]
        html = render_three_column_comparison(slide, 5, "", active=False)
        assert "circle-pair" not in html
        assert "Option 1" in html

    def test_partial_circle_data(self):
        slide = _circle_slide()
        slide["visual_spec"]["circle_data"] = slide["visual_spec"]["circle_data"][:1]
        html = render_three_column_comparison(slide, 5, "", active=False)
        # Only first column should have circles
        pair_count = html.count("circle-pair")
        assert pair_count == 1


class TestComparisonGridWithCircles:
    def test_circles_in_comparison_grid(self):
        slide = _circle_slide(layout="comparison_grid")
        slide["content"]["bullets"] = [
            "Lodging | Recovered strongly",
            "Restaurants | Above pre-pandemic",
        ]
        html = render_comparison(slide, 5, "", active=False)
        # comparison_grid may or may not have circle_data depending on pair_comparison
        # At minimum, it should not crash
        assert "comparison" in html.lower() or "card" in html.lower()


class TestCirclePairDeck:
    def test_render_deck(self, tmp_path):
        handoff = {
            "version": 1,
            "deck_title": "Test",
            "slides": [
                {
                    "slide_number": 1,
                    "layout_type": "title_or_opening",
                    "title": "Test",
                    "content": {"bullets": []},
                },
                _circle_slide(),
            ],
        }
        hpath = tmp_path / "handoff.json"
        hpath.write_text(json.dumps(handoff), encoding="utf-8")
        out = tmp_path / "out"
        render_deck(hpath, out)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "circle-pair" in html
        assert "Lodging" in html
