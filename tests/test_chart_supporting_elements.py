"""Tests for chart slide supporting elements (Fidelity T2, issue #30).

- Support table must be visible in a split layout (chart ~60% / table ~40%)
  instead of being pushed below the viewport.
- content.key_stats must render as a metric strip on chart layouts.
"""
from __future__ import annotations

from impact_slides.renderer_v2.layout.dispatch import render_slide


def _line_slide(**over):
    slide = {
        "slide_number": 2,
        "title": "Total Billed Business",
        "section": "Results",
        "layout_type": "line_chart",
        "content": {"bullets": [], "so_what": "Growth accelerated."},
        "visual_spec": {
            "primary_visual": {
                "type": "line_chart",
                "steps_or_data": [
                    {"label": "Q1'25", "value": 6},
                    {"label": "Q2'25", "value": 7},
                    {"label": "Q3'25", "value": 8},
                ],
            },
            "chart_config": {"y_axis_unit": "%"},
        },
        "evidence_sources": [],
    }
    slide.update(over)
    return slide


def _with_table(slide):
    slide["visual_spec"]["secondary_visual"] = {
        "type": "data_table",
        "steps_or_data": [
            ["", "Q1'25", "Q2'25", "Q3'25"],
            ["G&S", "7%", "7%", "9%"],
            ["T&E", "6%", "5%", "8%"],
        ],
    }
    return slide


def _with_stats(slide, n=3):
    slide["content"]["key_stats"] = [
        {"label": f"Metric {i}", "value": f"{i}%"} for i in range(1, n + 1)
    ]
    return slide


# ------------------------------------------------------------- split layout


def test_split_class_when_secondary_table_present():
    html = render_slide(_with_table(_line_slide()), total=1, notes="")
    assert "chart-svg-wrap" in html
    assert "chart-split" in html


def test_support_table_renders_inside_chart_frame():
    html = render_slide(_with_table(_line_slide()), total=1, notes="")
    frame = html.split('class="chart-frame', 1)[1]
    assert "chart-support-table" in frame
    assert "G&amp;S" in frame or "G&S" in frame


def test_no_split_class_without_secondary():
    html = render_slide(_line_slide(), total=1, notes="")
    assert "chart-split" not in html


# ------------------------------------------------------------- metric strip


def test_key_stats_render_metric_strip_on_chart_slide():
    html = render_slide(_with_stats(_line_slide()), total=1, notes="")
    assert "metric-strip" in html
    assert "Metric 1" in html
    assert "3%" in html


def test_key_stats_capped_at_six_tiles():
    html = render_slide(_with_stats(_line_slide(), n=8), total=1, notes="")
    assert html.count('class="metric-tile"') == 6
    assert "Metric 7" not in html


def test_no_metric_strip_without_key_stats():
    html = render_slide(_line_slide(), total=1, notes="")
    assert "metric-strip" not in html


def test_metric_strip_on_bar_chart_slide():
    slide = _line_slide()
    slide["layout_type"] = "grouped_bar_chart"
    slide["visual_spec"]["primary_visual"]["type"] = "grouped_bar_chart"
    _with_stats(slide, n=2)
    html = render_slide(slide, total=1, notes="")
    assert "metric-strip" in html
    assert "vbar-chart" in html


def test_stats_shrink_class_applied():
    html = render_slide(_with_stats(_line_slide()), total=1, notes="")
    assert "chart-with-stats" in html


def test_both_table_and_stats_get_split_and_stats_classes():
    slide = _with_stats(_with_table(_line_slide()))
    html = render_slide(slide, total=1, notes="")
    assert "chart-split" in html
    assert "chart-with-stats" in html
    assert "chart-support-table" in html
    assert "metric-strip" in html


# ------------------------------------------------------- white surface (T9/#37)

def test_white_surface_class_when_configured():
    slide = _with_table(_line_slide())
    slide["visual_spec"]["chart_config"]["surface"] = "white"
    html = render_slide(slide, total=1, notes="", active=True)
    assert "chart-frame gl-card chart-surface-white" in html


def test_no_white_surface_by_default():
    slide = _with_table(_line_slide())
    html = render_slide(slide, total=1, notes="", active=True)
    assert "chart-surface-white" not in html


def test_white_surface_css_rule_exists():
    from pathlib import Path
    css = (Path(__file__).parent.parent / "impact_slides" / "renderer_v2" / "css" / "components.css").read_text(encoding="utf-8")
    assert ".chart-frame.chart-surface-white" in css
