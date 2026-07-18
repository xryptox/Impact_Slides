"""Tests for plot-aligned chart support tables (Fidelity T8 / issue #36).

The key property is GEOMETRIC, not structural: when a support table's header
row matches the chart's category labels 1:1, each value column must be
centered under the chart's category position. Presence-only assertions
("chart-support-table" in html) are blind to this class of defect, so the
central test parses actual SVG point coordinates and colgroup widths and
compares them numerically.
"""

import re

from impact_slides.renderer_v2.charts import (
    _build_line_chart_svg,
    chart_column_interval,
    chart_geometry,
)
from impact_slides.renderer_v2.layout.dispatch import render_slide


def _slide(secondary=None, **vs_extra):
    vs = {
        "primary_visual": {
            "type": "line_chart",
            "steps_or_data": [
                {"label": "Q1'25", "value": 6},
                {"label": "Q2'25", "value": 7},
                {"label": "Q3'25", "value": 8},
                {"label": "Q4'25", "value": 8},
                {"label": "Q1'26", "value": 9},
            ],
        },
    }
    if secondary is not None:
        vs["secondary_visual"] = secondary
    vs.update(vs_extra)
    return {
        "slide_number": 1,
        "title": "Total Billed Business",
        "layout_type": "line_chart",
        "content": {"bullets": [], "key_stats": []},
        "visual_spec": vs,
    }


_MATCHING_SECONDARY = {
    "type": "data_table",
    "steps_or_data": [
        ["Segment", "Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"],
        ["G&S", "7%", "7%", "9%", "8%", "8%"],
        ["T&E", "6%", "5%", "8%", "8%", "9%"],
    ],
}


def _render(slide):
    return render_slide(slide, total=1, notes="", active=True)


# ------------------------------------------------------------- geometry contract


def test_chart_geometry_single_source():
    # line-chart insets are n-dependent (#39): pad_l = 72 + 414/n, pad_r = 414/n
    geom = chart_geometry("line_chart", n=5)
    assert geom["width"] == 900
    assert abs(geom["pad_l"] - 154.8) < 0.01
    assert abs(geom["pad_r"] - 82.8) < 0.01
    # builder actually reads the contract: first point sits at pad_l
    svg = _build_line_chart_svg(_slide())
    first_cx = float(re.search(r'<circle cx="([\d.]+)"', svg).group(1))
    assert abs(first_cx - geom["pad_l"]) < 0.5


def test_column_interval_line_chart_exact_bounds():
    # with the n-dependent insets, the aligned interval spans [72, 900]
    # exactly: 8% label zone + equal columns, no overflow either side
    left, right, w = chart_column_interval("line_chart", 5)
    assert abs(left - 72.0) < 0.01
    assert abs(right - 900.0) < 0.01
    assert w == 900.0


def test_column_interval_bars_span_plot_exactly():
    left, right, _ = chart_column_interval("grouped_bar_chart", 5)
    assert (left, right) == (70.0, 870.0)


# ------------------------------------------------------------- aligned rendering


def test_aligned_table_when_header_matches_categories():
    html = _render(_slide(secondary=_MATCHING_SECONDARY))
    assert "chart-table-aligned" in html
    assert "<colgroup>" in html
    assert "chart-align-table" in html          # nested in the SVG width context
    assert 'data-align-left="' in html          # geometric metadata exposed


def test_table_columns_center_on_chart_categories():
    """The geometric core: value column centers == mapped SVG point positions."""
    html = _render(_slide(secondary=_MATCHING_SECONDARY))

    # chart category x-positions (single series => unique cx values in order)
    svg = html.split("<svg", 1)[1]
    cxs = sorted({float(m) for m in re.findall(r'<circle cx="([\d.]+)"', svg)})
    assert len(cxs) == 5

    # table column geometry
    label_w, *col_ws = [
        float(m) for m in re.findall(r'<col style="width:([\d.]+)%"', html)
    ]
    left, right = (float(v) for v in re.search(
        r'data-align-left="([\d.-]+)" data-align-right="([\d.-]+)" data-align-width="[\d.-]+"',
        html,
    ).groups())

    col_centers = []
    edge = label_w
    for w_ in col_ws:
        col_centers.append(edge + w_ / 2)
        edge += w_

    # THE alignment invariant: the table shares the SVG's width context, so
    # a column's ABSOLUTE center (colgroup pct scaled by table width) must
    # equal the category point's position in the SVG (cx / 900).
    table_w = float(re.search(
        r'<table class="chart-support-table chart-table-aligned" style="width:([\d.]+)%"',
        html,
    ).group(1))
    for cx, center in zip(cxs, col_centers):
        absolute_center = center * table_w / 100.0
        point_pct = cx / 900.0 * 100.0
        assert abs(absolute_center - point_pct) < 0.2, (
            f"column off by {abs(absolute_center - point_pct):.2f}% of slide width"
        )


def test_non_matching_table_stays_full_width_unaligned():
    secondary = {
        "type": "data_table",
        "steps_or_data": [
            ["Metric", "Value"],
            ["G&S", "7%"],
            ["T&E", "6%"],
        ],
    }
    html = _render(_slide(secondary=secondary))
    assert "chart-table-aligned" not in html
    assert "<colgroup>" not in html
    assert "chart-align-table" not in html
    assert "chart-support-table" in html          # table still renders


def test_no_table_without_secondary_visual():
    html = _render(_slide())
    assert "chart-support-table" not in html
    assert "chart-align-table" not in html


def test_label_column_present_and_narrow():
    html = _render(_slide(secondary=_MATCHING_SECONDARY))
    first_col = float(re.search(r'<col style="width:([\d.]+)%"', html).group(1))
    assert 5.0 <= first_col <= 15.0               # y-axis margin zone, not a data column


def test_first_point_label_clears_y_axis():
    """The i==0 data label must not straddle the y-axis line (#39)."""
    svg = _build_line_chart_svg(_slide())
    first_label = re.search(
        r'<text x="([\d.]+)" y="[\d.]+" text-anchor="(start|middle)"[^>]*>6%</text>',
        svg,
    )
    assert first_label is not None
    geom = chart_geometry("line_chart", n=5)
    if first_label.group(2) == "middle":
        # a centered label must sit fully right of the axis
        assert float(first_label.group(1)) - 14 > geom["pad_l"]
    else:
        assert float(first_label.group(1)) >= geom["pad_l"]


def test_aligned_table_spans_to_svg_right_edge():
    html = _render(_slide(secondary=_MATCHING_SECONDARY))
    table_w = float(re.search(
        r'chart-table-aligned" style="width:([\d.]+)%"', html,
    ).group(1))
    assert abs(table_w - 100.0) < 0.5  # right edge == SVG right edge (900/900)
