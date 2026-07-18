"""Tests for chart series & bar color styling (Fidelity T4/#32, gaps #13+#14).

- chart_config.series_colors: per-series color override (line/bar/combo)
- per-point "color" key: per-bar color override (internal bar builders)
"""
from __future__ import annotations

from impact_slides.renderer_v2.charts import (
    _build_combo_chart_svg,
    _build_grouped_bar_svg,
    _build_line_chart_svg,
    _build_stacked_bar_svg,
)


def _slide(layout: str, data, **cfg):
    return {
        "slide_number": 1,
        "title": "T",
        "layout_type": layout,
        "content": {},
        "visual_spec": {
            "primary_visual": {"type": layout, "steps_or_data": data},
            "chart_config": cfg,
        },
        "evidence_sources": [],
    }


# ------------------------------------------------------- series_colors


def test_series_colors_grouped_bar():
    slide = _slide(
        "grouped_bar_chart",
        [
            {"label": "Q1", "values": {"A": 7, "B": 6}},
            {"label": "Q2", "values": {"A": 8, "B": 7}},
        ],
        series_colors=["#111111", "#222222"],
    )
    html = _build_grouped_bar_svg(slide)
    assert 'fill="#111111"' in html
    assert 'fill="#222222"' in html
    assert "var(--navy" not in html


def test_series_colors_line_chart():
    slide = _slide(
        "line_chart",
        [
            {"label": "Q1", "value": 8, "series_2": 9},
            {"label": "Q2", "value": 9, "series_2": 10},
        ],
        series_names=["FX Adj", "Reported"],
        series_colors=["#111111", "#222222"],
    )
    html = _build_line_chart_svg(slide)
    assert 'stroke="#111111"' in html
    assert 'stroke="#222222"' in html


def test_series_colors_stacked_bar_and_legend():
    slide = _slide(
        "stacked_bar_chart",
        [{"label": "Q1", "values": {"A": 100, "B": 50}}],
        series_colors=["#abcabc", "#defdef"],
    )
    html = _build_stacked_bar_svg(slide)
    assert 'fill="#abcabc"' in html
    assert 'fill="#defdef"' in html


def test_series_colors_combo_bar():
    slide = _slide("combo_chart", [{"label": "Q1", "value": 1.6}], series_colors=["#333333"])
    html = _build_combo_chart_svg(slide)
    assert 'fill="#333333"' in html
    assert "var(--blue" not in html.split("<rect", 1)[1].split("/>", 1)[0]


def test_series_colors_defaults_unchanged():
    slide = _slide(
        "grouped_bar_chart",
        [{"label": "Q1", "values": {"A": 7, "B": 6}}],
    )
    html = _build_grouped_bar_svg(slide)
    assert "var(--navy" in html
    assert "var(--blue" in html


# ------------------------------------------------------- per-bar color


def test_per_bar_color_grouped_single_series():
    slide = _slide(
        "grouped_bar_chart",
        [
            {"label": "US Consumer", "value": 10},
            {"label": "Processed", "value": 9, "color": "#898a89"},
        ],
    )
    html = _build_grouped_bar_svg(slide)
    assert 'fill="#898a89"' in html


def test_per_bar_color_leaves_other_bars_default():
    slide = _slide(
        "grouped_bar_chart",
        [
            {"label": "US Consumer", "value": 10},
            {"label": "Processed", "value": 9, "color": "#898a89"},
        ],
    )
    html = _build_grouped_bar_svg(slide)
    # first bar keeps the default series color
    assert html.count("var(--navy") >= 1
    assert html.count('fill="#898a89"') == 1


def test_per_bar_color_stacked():
    slide = _slide(
        "stacked_bar_chart",
        [
            {"label": "Q1", "values": {"A": 100, "B": 50}},
            {"label": "Q2", "values": {"A": 100, "B": 50}, "color": "#898a89"},
        ],
    )
    html = _build_stacked_bar_svg(slide)
    assert html.count('fill="#898a89"') == 2  # both segments of Q2


def test_per_bar_color_combo():
    slide = _slide(
        "combo_chart",
        [
            {"label": "Q1", "value": 1.6},
            {"label": "Q2", "value": 1.3, "color": "#898a89"},
        ],
    )
    html = _build_combo_chart_svg(slide)
    assert 'fill="#898a89"' in html
