"""Tests for the dual_chart layout (Fidelity T7/#35, gap #9).

visual_spec.primary_visual + secondary_visual each carry their own chart
type/data/config and render side by side in a two-column grid (PDF p17:
bar chart left, YoY% line chart right).
"""
from __future__ import annotations

import json
import re

from impact_slides.renderer_v2.layout.dispatch import render_slide
from impact_slides.renderer_v2.layout.recipes import render_dual_chart
from impact_slides.renderer_v2.schemas import validate_slide


def _legend_displays(html: str) -> list[bool | None]:
    """Legend.display per embedded Chart.js config (None = Chart.js default on)."""
    out: list[bool | None] = []
    for m in re.finditer(
        r'<script type="application/json" class="chartjs-config"[^>]*>(.*?)</script>',
        html,
        re.S,
    ):
        conf = json.loads(m.group(1))
        leg = (conf.get("options") or {}).get("plugins", {}).get("legend", {})
        out.append(leg.get("display"))
    return out


def _slide(**over):
    slide = {
        "slide_number": 8,
        "title": "Net Card Fees",
        "section": "Financials",
        "layout_type": "dual_chart",
        "content": {
            "so_what": "Card fees grew 17% per year since Q1'19.",
            "bullets": [],
            "key_stats": [],
        },
        "visual_spec": {
            "primary_visual": {
                "type": "grouped_bar_chart",
                "chart_config": {"y_axis_unit": "$"},
                "steps_or_data": [
                    {"label": "Q1'19", "value": 0.9},
                    {"label": "Q1'20", "value": 1.1},
                    {"label": "Q1'21", "value": 1.3},
                ],
            },
            "secondary_visual": {
                "type": "line_chart",
                "chart_config": {"y_axis_unit": "%"},
                "steps_or_data": [
                    {"label": "Q1'24", "value": 16},
                    {"label": "Q2'24", "value": 16},
                    {"label": "Q3'24", "value": 18},
                ],
            },
        },
        "evidence_sources": [],
    }
    slide.update(over)
    return slide


def test_renders_both_charts_side_by_side():
    html = render_dual_chart(_slide(), 1, "", active=True)
    assert "dual-chart" in html
    assert html.count("dual-chart-pane") == 2
    assert "vbar-chart" in html      # grouped bar in pane 1
    assert "line-chart" in html      # line chart in pane 2
    assert html.count("chart-svg") == 2


def test_per_pane_chart_config():
    html = render_dual_chart(_slide(), 1, "")
    assert "$0.9" in html            # primary pane currency format
    assert ">16%</text>" in html     # secondary pane percent format


def test_dispatch_routes_dual_chart():
    html = render_slide(_slide(), total=1, notes="", active=True)
    assert 'data-layout="dual_chart"' in html
    assert "dual-chart-pane" in html


def test_schema_validates():
    model, err = validate_slide(_slide())
    assert err is None
    assert model.layout_type == "dual_chart"


def test_so_what_insight_strip_renders():
    html = render_dual_chart(_slide(), 1, "")
    assert "insight" in html
    assert "17% per year" in html


def test_missing_secondary_renders_single_pane():
    slide = _slide()
    del slide["visual_spec"]["secondary_visual"]
    html = render_dual_chart(slide, 1, "")
    assert html.count("dual-chart-pane") == 1
    assert "vbar-chart" in html


def test_single_series_pane_gets_heading_and_legend_suppressed():
    # R5-F/T11 + #139: pane title renders as in-card gl-chart-pane-title heading
    # (sourced from the pane's single series name) and the Chart.js legend
    # that would restate it is suppressed.
    slide = _slide()
    slide["visual_spec"]["primary_visual"]["chart_config"]["series_names"] = [
        "Net Card Fees $B"
    ]
    html = render_dual_chart(slide, 1, "", use_chartjs=True)
    assert 'class="gl-chart-pane-title"' in html and ">Net Card Fees $B</div>" in html
    assert False in _legend_displays(html)


def test_multi_series_pane_keeps_legend_and_no_heading():
    # A legend distinguishing 2+ series is information, not chrome.
    slide = _slide()
    slide["visual_spec"]["primary_visual"] = {
        "type": "line_chart",
        "chart_config": {"series_names": ["Baseline UE", "Downside UE"]},
        "steps_or_data": [
            {"label": "Q1'25", "value": 4.0, "series_2": 4.2},
            {"label": "Q2'25", "value": 4.1, "series_2": 4.3},
        ],
    }
    html = render_dual_chart(slide, 1, "", use_chartjs=True)
    assert "gl-chart-pane-title" not in html
    assert "gl-tile-label" not in html
    assert False not in _legend_displays(html)


def test_value_plus_series_n_keeps_legend_with_pane_label():
    # value + series_2 is multi-series even without series_names; a pane
    # label must not force legend suppression.
    slide = _slide()
    slide["visual_spec"]["primary_visual"] = {
        "type": "line_chart",
        "label": "Unemployment",
        "steps_or_data": [
            {"label": "Q1'25", "value": 4.0, "series_2": 4.2},
            {"label": "Q2'25", "value": 4.1, "series_2": 4.3},
        ],
    }
    html = render_dual_chart(slide, 1, "", use_chartjs=True)
    assert 'class="gl-chart-pane-title"' in html and ">Unemployment</div>" in html
    assert False not in _legend_displays(html)


def test_explicit_pane_label_renders_as_heading():
    slide = _slide()
    slide["visual_spec"]["primary_visual"]["label"] = "Fees (Q1: 2019-2026)"
    slide["visual_spec"]["primary_visual"]["chart_config"]["series_names"] = ["Fees"]
    html = render_dual_chart(slide, 1, "")
    assert 'class="gl-chart-pane-title"' in html and ">Fees (Q1: 2019-2026)</div>" in html


def test_combo_pane_with_overlay():
    slide = _slide()
    slide["visual_spec"]["secondary_visual"] = {
        "type": "combo_chart",
        "steps_or_data": [{"label": "Q1", "value": 1.6}],
        "line_overlay": {"data": [{"label": "Q1", "value": 702}], "dual_axis": False},
    }
    html = render_dual_chart(slide, 1, "")
    assert "combo-chart" in html
    assert "<polyline" in html  # overlay honored through per-pane config
