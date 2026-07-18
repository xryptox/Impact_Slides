"""Tests for stacked-bar combo charts (Fidelity T6/#34, gap #10).

combo_chart bar data accepts multi-series dicts {label, values:{s: v}} and
renders stacked segments + legend + per-stack net total; the line overlay
and dual axis work unchanged. Single-series combos are pixel-identical.
"""
from __future__ import annotations

import re

from impact_slides.renderer_v2.charts import _build_combo_chart_svg


def _slide(bar_data, overlay=None, **cfg):
    vs = {
        "primary_visual": {"type": "combo_chart", "steps_or_data": bar_data},
        "chart_config": cfg,
    }
    if overlay is not None:
        vs["line_overlay"] = overlay
    return {
        "slide_number": 1,
        "title": "Capital",
        "layout_type": "combo_chart",
        "content": {},
        "visual_spec": vs,
        "evidence_sources": [],
    }


_STACKED = [
    {"label": "Q4'24", "values": {"Dividends": 0.5, "Share Repurchases": 1.1}},
    {"label": "Q1'25", "values": {"Dividends": 0.6, "Share Repurchases": 0.7}},
    {"label": "Q2'25", "values": {"Dividends": 0.6, "Share Repurchases": 1.4}},
]

_OVERLAY = {
    "data": [
        {"label": "Q4'24", "value": 702},
        {"label": "Q1'25", "value": 701},
        {"label": "Q2'25", "value": 696},
    ],
    "label": "Shares Outstanding",
    "dual_axis": True,
}


def test_multi_series_renders_stacked_segments():
    html = _build_combo_chart_svg(_slide(_STACKED))
    # 3 categories x 2 series = 6 segments
    assert html.count('class="combo-seg"') == 6


def test_stacked_net_totals_above_stacks():
    html = _build_combo_chart_svg(_slide(_STACKED, chart_config={}) if False else _slide(_STACKED))
    assert ">1.6</text>" in html  # 0.5 + 1.1
    assert ">1.3</text>" in html  # 0.6 + 0.7
    assert ">2</text>" in html    # 0.6 + 1.4


def test_stacked_legend_renders_series_names():
    html = _build_combo_chart_svg(_slide(_STACKED))
    assert "combo-bar-legend" in html
    assert ">Dividends</text>" in html
    assert ">Share Repurchases</text>" in html


def test_segment_values_inside_segments():
    html = _build_combo_chart_svg(_slide(_STACKED))
    # segment values labeled inside (segments are tall with these scales)
    assert ">0.5</text>" in html
    assert ">1.1</text>" in html


def test_line_overlay_aligns_with_stacked_categories():
    html = _build_combo_chart_svg(_slide(_STACKED, overlay=_OVERLAY))
    assert "<polyline" in html
    # 3 overlay points
    assert len(re.findall(r"<circle ", html)) == 3
    # overlay point for Q1'25 must sit at that category's slot center:
    # pad_l=80, pad_r=80 (line points) -> plot_w=740, slot=740/3
    slot = 740 / 3
    expected_x = 80 + 1 * slot + slot / 2
    circles = re.findall(r'<circle cx="([\d.]+)"', html)
    assert any(abs(float(cx) - expected_x) < 1.0 for cx in circles)


def test_dual_axis_with_stacked_bars():
    html = _build_combo_chart_svg(_slide(_STACKED, overlay=_OVERLAY))
    # right-side axis line at x = W - pad_r = 820
    assert 'x1="820"' in html


def test_single_series_combo_unchanged():
    slide = _slide(
        [{"label": "Q4'24", "value": 1.6}, {"label": "Q1'25", "value": 1.3}],
        overlay=_OVERLAY,
    )
    html = _build_combo_chart_svg(slide)
    assert "combo-seg" not in html
    assert "combo-bar-legend" not in html
    assert ">1.6</text>" in html  # plain value labels as before


def test_series_colors_apply_to_stacked_segments():
    html = _build_combo_chart_svg(_slide(_STACKED, series_colors=["#111111", "#222222"]))
    assert 'fill="#111111"' in html
    assert 'fill="#222222"' in html
