"""Tests for combo_chart layout — bar chart with line overlay."""

import json
import re

import pytest

from impact_slides.renderer_v2.charts import (
    _build_combo_chart_svg,
    _combo_bar_data,
    _combo_line_data,
    build_chart_html,
    is_chart_layout,
)
from impact_slides.renderer_v2.cli import render_deck
from impact_slides.renderer_v2.schemas import validate_slide


def _slide(**overrides):
    s = {
        "slide_number": 2,
        "layout_type": "combo_chart",
        "title": "Capital Return",
        "content": {"bullets": []},
        "visual_spec": {
            "primary_visual": {
                "type": "combo_chart",
                "steps_or_data": [
                    {"label": "Q4'24", "value": 1.6},
                    {"label": "Q1'25", "value": 1.3},
                    {"label": "Q2'25", "value": 2.0},
                    {"label": "Q3'25", "value": 2.9},
                    {"label": "Q4'25", "value": 1.5},
                    {"label": "Q1'26", "value": 2.3},
                ],
            },
            "chart_config": {"y_axis_unit": "$B", "y_axis_max": 4},
            "line_overlay": {
                "data": [
                    {"label": "Q4'24", "value": 702},
                    {"label": "Q1'25", "value": 701},
                    {"label": "Q2'25", "value": 696},
                    {"label": "Q3'25", "value": 689},
                    {"label": "Q4'25", "value": 686},
                    {"label": "Q1'26", "value": 682},
                ],
                "color": "var(--ink-muted, #63666a)",
                "label": "Common Shares Outstanding",
                "style": "solid",
                "y_axis_max": 720,
                "y_axis_min": 660,
                "y_axis_unit": "",
                "dual_axis": True,
            },
        },
    }
    s.update(overrides)
    return s


class TestComboSchema:
    def test_validates(self):
        model, err = validate_slide(_slide())
        assert err is None
        assert model.layout_type == "combo_chart"


class TestComboBarData:
    def test_parses_bars(self):
        labels, values, _colors = _combo_bar_data(_slide())
        assert len(labels) == 6
        assert labels[0] == "Q4'24"
        assert values[0] == 1.6


class TestComboLineData:
    def test_parses_line(self):
        pts = _combo_line_data(_slide())
        assert len(pts) == 6
        assert pts[0]["value"] == 702


class TestComboSvg:
    def test_returns_svg(self):
        svg = _build_combo_chart_svg(_slide())
        assert "<svg" in svg
        assert "combo-chart" in svg

    def test_has_bars(self):
        svg = _build_combo_chart_svg(_slide())
        rects = re.findall(r"<rect\s", svg)
        assert len(rects) == 6

    def test_has_line_overlay(self):
        svg = _build_combo_chart_svg(_slide())
        assert "<polyline" in svg

    def test_has_line_circles(self):
        svg = _build_combo_chart_svg(_slide())
        circles = re.findall(r"<circle\s", svg)
        assert len(circles) == 6

    def test_dual_axis(self):
        svg = _build_combo_chart_svg(_slide())
        # Right axis labels should be present (line values like 660, 675, etc.)
        assert "720" in svg or "660" in svg

    def test_overlay_legend(self):
        svg = _build_combo_chart_svg(_slide())
        assert "Common Shares Outstanding" in svg

    def test_bar_labels(self):
        svg = _build_combo_chart_svg(_slide())
        assert "1.6" in svg
        assert "2.9" in svg

    def test_x_axis_labels(self):
        svg = _build_combo_chart_svg(_slide())
        assert "Q4&#x27;24" in svg or "Q4'24" in svg

    def test_viewbox(self):
        svg = _build_combo_chart_svg(_slide())
        assert 'viewBox="0 0 900 480"' in svg

    def test_empty_bars(self):
        s = _slide()
        s["visual_spec"]["primary_visual"]["steps_or_data"] = []
        svg = _build_combo_chart_svg(s)
        assert "chart-empty" in svg

    def test_no_line_overlay(self):
        s = _slide()
        del s["visual_spec"]["line_overlay"]
        svg = _build_combo_chart_svg(s)
        assert "<rect" in svg
        assert "<polyline" not in svg


class TestComboIntegration:
    def test_is_chart_layout(self):
        assert is_chart_layout("combo_chart")

    def test_build_chart_html(self):
        html = build_chart_html(_slide(), "combo_chart")
        assert "combo-chart" in html

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
                _slide(),
            ],
        }
        hpath = tmp_path / "handoff.json"
        hpath.write_text(json.dumps(handoff), encoding="utf-8")
        out = tmp_path / "out"
        render_deck(hpath, out)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "combo-chart" in html
        assert 'data-layout="combo_chart"' in html
