"""Tests for internal vertical bar chart builders (grouped + stacked).

Fidelity T1 (issue #29): grouped_bar_chart and stacked_bar_chart must render
vertical columns via internal SVG builders, without the external charts pack.
"""
from __future__ import annotations

from impact_slides.renderer_v2.charts import (
    _build_grouped_bar_svg,
    _build_stacked_bar_svg,
    build_chart_html,
)
from impact_slides.renderer_v2.layout.dispatch import render_slide
from impact_slides.renderer_v2.schemas import validate_slide


def _grouped_slide(**over):
    slide = {
        "slide_number": 1,
        "title": "Total Balances and Billed Business",
        "section": "Results",
        "layout_type": "grouped_bar_chart",
        "content": {"bullets": [], "so_what": "Billed Business outpaced Balances."},
        "visual_spec": {
            "primary_visual": {
                "type": "grouped_bar_chart",
                "steps_or_data": [
                    {"label": "Q1'25", "values": {"Total Balances": 7, "Billed Business": 6}},
                    {"label": "Q2'25", "values": {"Total Balances": 6, "Billed Business": 7}},
                    {"label": "Q3'25", "values": {"Total Balances": 7, "Billed Business": 8}},
                ],
            },
            "chart_config": {"y_axis_unit": "%"},
        },
        "evidence_sources": [],
    }
    slide.update(over)
    return slide


def _stacked_slide(**over):
    slide = {
        "slide_number": 1,
        "title": "Total Provision",
        "section": "Credit",
        "layout_type": "stacked_bar_chart",
        "content": {"bullets": [], "so_what": "Reserve Rate held at 2.8-2.9%."},
        "visual_spec": {
            "primary_visual": {
                "type": "stacked_bar_chart",
                "steps_or_data": [
                    {"label": "Q1'25", "values": {"Write-offs": 1223, "Reserve Build/(Release)": -73}},
                    {"label": "Q2'25", "values": {"Write-offs": 1183, "Reserve Build/(Release)": 222}},
                    {"label": "Q1'26", "values": {"Write-offs": 1275, "Reserve Build/(Release)": -24}},
                ],
            },
            "chart_config": {"y_axis_unit": ""},
        },
        "evidence_sources": [],
    }
    slide.update(over)
    return slide


def _validated(slide_dict):
    model, err = validate_slide(slide_dict)
    assert model is not None, err
    return model


def test_grouped_bar_schema_validates():
    model = _validated(_grouped_slide())
    assert model.layout_type == "grouped_bar_chart"


def test_stacked_bar_schema_validates():
    model = _validated(_stacked_slide())
    assert model.layout_type == "stacked_bar_chart"


# ---------------------------------------------------------------- grouped


def test_grouped_bar_renders_vertical_columns():
    html = _build_grouped_bar_svg(_grouped_slide())
    assert '<svg class="chart-svg vbar-chart' in html
    assert "<rect" in html


def test_grouped_bar_two_bars_per_category():
    html = _build_grouped_bar_svg(_grouped_slide())
    # 3 categories x 2 series = 6 bar rects
    assert html.count('class="vbar"') == 6


def test_grouped_bar_value_labels_with_percent_unit():
    html = _build_grouped_bar_svg(_grouped_slide())
    assert ">7%</text>" in html
    assert ">8%</text>" in html


def test_grouped_bar_legend_series_names():
    html = _build_grouped_bar_svg(_grouped_slide())
    assert "Total Balances" in html
    assert "Billed Business" in html
    assert "vbar-legend" in html


def test_grouped_bar_series_colors_navy_then_blue():
    html = _build_grouped_bar_svg(_grouped_slide())
    assert "var(--navy" in html
    assert "var(--blue)" in html or "var(--blue," in html


def test_grouped_bar_category_labels():
    html = _build_grouped_bar_svg(_grouped_slide())
    assert "Q1&#x27;25" in html or "Q1'25" in html


def test_grouped_bar_list_of_lists_with_header():
    slide = _grouped_slide()
    slide["visual_spec"]["primary_visual"]["steps_or_data"] = [
        ["Quarter", "Total Balances", "Billed Business"],
        ["Q1'25", 7, 6],
        ["Q2'25", 6, 7],
    ]
    html = _build_grouped_bar_svg(slide)
    assert html.count('class="vbar"') == 4
    assert "Total Balances" in html


def test_grouped_bar_single_series_no_legend():
    slide = _grouped_slide()
    slide["visual_spec"]["primary_visual"]["steps_or_data"] = [
        {"label": "Q1'25", "value": 7},
        {"label": "Q2'25", "value": 6},
    ]
    html = _build_grouped_bar_svg(slide)
    assert html.count('class="vbar"') == 2
    assert "vbar-legend" not in html


# ---------------------------------------------------------------- stacked


def test_stacked_bar_renders_segments():
    html = _build_stacked_bar_svg(_stacked_slide())
    assert '<svg class="chart-svg vbar-chart vbar-stacked' in html
    # 3 categories x 2 series = 6 segments (positives are "vbar-seg",
    # negatives are "vbar-seg vbar-neg" — count the shared prefix)
    assert html.count("vbar-seg") == 6


def test_stacked_bar_negative_segment_below_zero_axis():
    html = _build_stacked_bar_svg(_stacked_slide())
    # Negative segment must exist and be positioned below the zero baseline.
    # The builder marks negative segments with a dedicated class.
    assert "vbar-neg" in html


def test_stacked_bar_totals_label():
    html = _build_stacked_bar_svg(_stacked_slide())
    # Q1'25: 1223 + (-73) = 1150
    assert ">1,150</text>" in html
    # Q2'25: 1183 + 222 = 1405
    assert ">1,405</text>" in html


def test_stacked_bar_thousands_formatting():
    html = _build_stacked_bar_svg(_stacked_slide())
    assert "1,223" in html


def test_stacked_bar_axis_ticks_are_nice_numbers():
    html = _build_stacked_bar_svg(_stacked_slide())
    # With data_max 1414 and a small negative tail, ticks should be clean
    # 500-multiples from zero — not odd values like 315 or 1,105
    assert ">1,000</text>" in html
    assert ">500</text>" in html
    assert "315" not in html


def test_stacked_bar_legend():
    html = _build_stacked_bar_svg(_stacked_slide())
    assert "Write-offs" in html
    assert "Reserve Build/(Release)" in html


# ---------------------------------------------------------------- routing


def test_build_chart_html_routes_grouped_internally():
    html = build_chart_html(_grouped_slide(), "grouped_bar_chart")
    assert "vbar-chart" in html


def test_build_chart_html_routes_stacked_internally():
    html = build_chart_html(_stacked_slide(), "stacked_bar_chart")
    assert "vbar-chart" in html


def test_dispatch_grouped_bar_slide():
    html = render_slide(_grouped_slide(), total=1, notes="", active=True)
    assert 'data-layout="grouped_bar_chart"' in html
    assert "vbar-chart" in html


def test_dispatch_stacked_bar_slide():
    html = render_slide(_stacked_slide(), total=1, notes="", active=True)
    assert 'data-layout="stacked_bar_chart"' in html
    assert "vbar-chart" in html


def test_empty_data_returns_chart_empty():
    slide = _grouped_slide()
    slide["visual_spec"]["primary_visual"]["steps_or_data"] = []
    html = _build_grouped_bar_svg(slide)
    assert "chart-empty" in html


def test_no_duplicate_insight_strip_on_chart_slide():
    html = render_slide(_grouped_slide(), total=1, notes="", active=True)
    assert html.count("Billed Business outpaced Balances.") == 1
