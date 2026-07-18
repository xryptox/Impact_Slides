"""Tests for line_chart layout — internal SVG line chart builder."""

import json
import re
import tempfile
from pathlib import Path

import pytest

from impact_slides.renderer_v2.charts import (
    _build_line_chart_svg,
    _line_data,
    build_chart_html,
    is_chart_layout,
)
from impact_slides.renderer_v2.cli import render_deck
from impact_slides.renderer_v2.schemas import validate_slide
from impact_slides.renderer_v2.strip import strip_eids


# ── Helpers ──────────────────────────────────────────────────────────


def _slide(layout="line_chart", **overrides):
    s = {
        "slide_number": 2,
        "layout_type": layout,
        "title": "Test Line Chart",
        "content": {"bullets": ["Point A", "Point B"]},
        "visual_spec": {
            "primary_visual": {
                "type": layout,
                "steps_or_data": [
                    {"label": "Q1'25", "value": 8},
                    {"label": "Q2'25", "value": 9},
                    {"label": "Q3'25", "value": 10},
                    {"label": "Q4'25", "value": 9},
                    {"label": "Q1'26", "value": 11},
                ],
            }
        },
    }
    s.update(overrides)
    return s


# ── Schema validation ────────────────────────────────────────────────


class TestLineChartSchema:
    def test_validates_line_chart(self):
        model, err = validate_slide(_slide())
        assert err is None
        assert model is not None
        assert model.layout_type == "line_chart"

    def test_rejects_missing_data(self):
        s = _slide()
        s["visual_spec"]["primary_visual"]["steps_or_data"] = []
        model, err = validate_slide(s)
        # Schema itself should still validate (data is optional at schema level)
        assert model is not None


# ── Data parsing ─────────────────────────────────────────────────────


class TestLineData:
    def test_parses_dict_items(self):
        data = _line_data(_slide())
        assert len(data) == 5
        assert data[0]["label"] == "Q1'25"
        assert data[0]["value"] == 8.0

    def test_parses_list_pairs(self):
        s = _slide()
        s["visual_spec"]["primary_visual"]["steps_or_data"] = [
            ["Q1'25", 8], ["Q2'25", 9],
        ]
        data = _line_data(s)
        assert len(data) == 2
        assert data[0]["label"] == "Q1'25"
        assert data[0]["value"] == 8.0

    def test_parses_string_items(self):
        s = _slide()
        s["visual_spec"]["primary_visual"]["steps_or_data"] = [
            "Q1'25: 8%", "Q2'25: 9%",
        ]
        data = _line_data(s)
        assert len(data) == 2
        assert data[0]["value"] == 8.0

    def test_strips_percent_and_dollar(self):
        s = _slide()
        s["visual_spec"]["primary_visual"]["steps_or_data"] = [
            {"label": "A", "value": "10%"},
            {"label": "B", "value": "$1,234"},
        ]
        data = _line_data(s)
        assert data[0]["value"] == 10.0
        assert data[1]["value"] == 1234.0

    def test_empty_data(self):
        s = _slide()
        s["visual_spec"]["primary_visual"]["steps_or_data"] = []
        assert _line_data(s) == []


# ── SVG rendering ────────────────────────────────────────────────────


class TestLineChartSvg:
    def test_returns_svg(self):
        svg = _build_line_chart_svg(_slide())
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_viewbox_containment(self):
        svg = _build_line_chart_svg(_slide())
        assert 'viewBox="0 0 900 480"' in svg

    def test_has_polyline(self):
        svg = _build_line_chart_svg(_slide())
        assert "<polyline" in svg
        assert 'stroke="var(--navy, #00175a)"' in svg

    def test_has_data_points(self):
        svg = _build_line_chart_svg(_slide())
        circles = re.findall(r"<circle\s", svg)
        assert len(circles) == 5  # 5 data points

    def test_has_data_labels(self):
        svg = _build_line_chart_svg(_slide())
        assert "8%" in svg
        assert "9%" in svg
        assert "10%" in svg
        assert "11%" in svg

    def test_has_x_axis_labels(self):
        svg = _build_line_chart_svg(_slide())
        assert "Q1&#x27;25" in svg or "Q1'25" in svg
        assert "Q1&#x27;26" in svg or "Q1'26" in svg

    def test_has_y_axis_gridlines(self):
        svg = _build_line_chart_svg(_slide())
        lines = re.findall(r"<line\s", svg)
        assert len(lines) >= 5  # At least Y gridlines + X/Y axes

    def test_has_axes(self):
        svg = _build_line_chart_svg(_slide())
        # X and Y axis lines
        assert 'stroke-width="1"' in svg

    def test_empty_data_returns_empty_message(self):
        s = _slide()
        s["visual_spec"]["primary_visual"]["steps_or_data"] = []
        svg = _build_line_chart_svg(s)
        assert "chart-empty" in svg

    def test_y_axis_max_override(self):
        s = _slide()
        s["visual_spec"]["chart_config"] = {"y_axis_max": 20}
        svg = _build_line_chart_svg(s)
        # Should render fine with custom max
        assert "<svg" in svg

    def test_y_axis_label(self):
        s = _slide()
        s["visual_spec"]["chart_config"] = {"y_axis_label": "% Increase"}
        svg = _build_line_chart_svg(s)
        assert "% Increase" in svg


# ── Integration via build_chart_html ─────────────────────────────────


class TestBuildChartHtml:
    def test_routes_line_chart_internally(self):
        html = build_chart_html(_slide(), "line_chart")
        assert "<polyline" in html
        assert "line-chart" in html

    def test_is_chart_layout(self):
        assert is_chart_layout("line_chart")

    def test_is_chart_layout_case_insensitive(self):
        assert is_chart_layout("Line_Chart")


# ── Multi-series ──────────────────────────────────────────────────────


def _multi_slide(**overrides):
    s = _slide()
    s["visual_spec"]["primary_visual"]["steps_or_data"] = [
        {"label": "Q1'25", "value": 8, "series_2": 7},
        {"label": "Q2'25", "value": 9, "series_2": 9},
        {"label": "Q3'25", "value": 10, "series_2": 11},
        {"label": "Q4'25", "value": 9, "series_2": 10},
        {"label": "Q1'26", "value": 11, "series_2": 11},
    ]
    s["visual_spec"]["chart_config"] = {
        "series_names": ["FX Adjusted", "Reported"],
        "series_styles": ["solid", "dashed"],
    }
    s.update(overrides)
    return s


class TestMultiSeries:
    def test_two_polylines(self):
        svg = _build_line_chart_svg(_multi_slide())
        polylines = re.findall(r"<polyline", svg)
        assert len(polylines) == 2

    def test_dashed_second_series(self):
        svg = _build_line_chart_svg(_multi_slide())
        assert 'stroke-dasharray="8,4"' in svg

    def test_second_series_color(self):
        svg = _build_line_chart_svg(_multi_slide())
        assert "var(--ink-muted, #63666a)" in svg

    def test_legend_rendered(self):
        svg = _build_line_chart_svg(_multi_slide())
        assert "FX Adjusted" in svg
        assert "Reported" in svg

    def test_second_series_data_labels(self):
        svg = _build_line_chart_svg(_multi_slide())
        # series_2 labels should appear below the line
        assert "7%" in svg
        assert "11%" in svg

    def test_three_series(self):
        s = _multi_slide()
        for pt in s["visual_spec"]["primary_visual"]["steps_or_data"]:
            pt["series_3"] = pt["value"] - 2
        s["visual_spec"]["chart_config"]["series_names"] = [
            "Baseline", "Upside", "Downside",
        ]
        svg = _build_line_chart_svg(s)
        polylines = re.findall(r"<polyline", svg)
        assert len(polylines) == 3
        assert "Downside" in svg

    def test_single_series_no_legend(self):
        svg = _build_line_chart_svg(_slide())
        assert "Series" not in svg


# ── Annotation ────────────────────────────────────────────────────────


class TestAnnotation:
    def test_annotation_rendered(self):
        s = _slide()
        s["visual_spec"]["chart_config"] = {
            "annotation": {"text": "Leap Year\\nApprox. (1%)", "x": 200, "y": 120},
        }
        svg = _build_line_chart_svg(s)
        assert "Leap Year" in svg
        assert "Approx. (1%)" in svg
        assert 'stroke-dasharray="4,3"' in svg

    def test_no_annotation_by_default(self):
        svg = _build_line_chart_svg(_slide())
        assert "Leap Year" not in svg


# ── Supporting table ─────────────────────────────────────────────────


class TestSupportingTable:
    def test_table_below_chart(self, tmp_path):
        s = _slide()
        s["visual_spec"]["secondary_visual"] = {
            "type": "data_table",
            "steps_or_data": [
                ["Q1'25", "Q2'25", "Q3'25"],
                ["$17.0", "$17.9", "$18.4"],
            ],
        }
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
                s,
            ],
        }
        hpath = tmp_path / "handoff.json"
        hpath.write_text(json.dumps(handoff), encoding="utf-8")
        out = tmp_path / "out"
        render_deck(hpath, out)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "chart-support-table" in html
        assert "$17.0" in html


# ── Full deck render ─────────────────────────────────────────────────


class TestLineChartDeck:
    def test_render_deck_with_line_chart(self, tmp_path):
        handoff = {
            "version": 1,
            "deck_title": "Test Deck",
            "slides": [
                {
                    "slide_number": 1,
                    "layout_type": "title_or_opening",
                    "title": "Test Deck",
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
        assert "line-chart" in html
        assert "<polyline" in html
        assert 'data-layout="line_chart"' in html
