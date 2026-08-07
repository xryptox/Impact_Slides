"""Tests for plot-aligned chart support tables (Fidelity T8 / issue #36).

The key property is GEOMETRIC, not structural: when a support table's header
row matches the chart's category labels 1:1, each value column must be
centered under the chart's category position. Presence-only assertions
("chart-support-table" in html) are blind to this class of defect, so the
central test parses actual SVG point coordinates and colgroup widths and
compares them numerically.
"""

import json
import re
from pathlib import Path

import pytest

from impact_slides.renderer_v2 import render_deck
from impact_slides.renderer_v2.charts import (
    OUTLINED_LABEL_GAP_PX,
    OUTLINED_LABEL_MIN_PX,
    _build_line_chart_svg,
    chart_column_interval,
    chart_geometry,
    outlined_lane_layout,
)
from impact_slides.renderer_v2.charts.typography import (
    begin_render_warnings,
    reset_render_strict,
    set_render_strict,
    take_render_warnings,
)
from impact_slides.renderer_v2.layout.dispatch import render_slide

_ALIGN_JS_MARKER = 'data-rv2-chart-table-align="1"'
_GOLDEN = Path(__file__).resolve().parent / "fixtures" / "renderer_v2" / "golden_mvp1_handoff.json"


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


# ------------------------------------------- unconditional width sharing (#40)

def test_non_matching_table_shares_chart_width_context():
    """Segment-breakdown tables (no category relationship) must still render
    INSIDE the chart's width context — not at full card width."""
    secondary = {
        "type": "data_table",
        "steps_or_data": [
            ["Q1'26", "U.S. SME", "U.S. Large & Global Corp.", "Total"],
            ["YoY", "4%", "4%", "4%"],
            ["% of Total", "81%", "19%", "100%"],
        ],
    }
    html = _render(_slide(secondary=secondary))
    assert "chart-support-table" in html
    assert "chart-table-aligned" not in html        # no column relationship
    assert "<colgroup>" not in html
    # ...but the table is nested in the shared chart column
    assert '<div class="chart-col">' in html
    col = html.split('<div class="chart-col">', 1)[1]
    assert "chart-support-table" in col.split("</div>", 1)[0]
    assert "chart-svg-wrap chart-split" in html     # width-constrained wrap


def test_aligned_table_still_nested_after_40():
    """p4 case unchanged: aligned tables keep colgroup + nesting."""
    html = _render(_slide(secondary=_MATCHING_SECONDARY))
    assert "chart-table-aligned" in html
    assert '<div class="chart-col">' in html
    assert "chart-align-table" in html


# ------------------------------------------- N6 / #136 row-list primary labels

_ROW_LIST_PRIMARY = [
    ["Quarter", "Write-offs", "Reserve Build/(Release)"],
    ["Q1'25", "1223", "-73"],
    ["Q2'25", "1200", "-50"],
    ["Q3'25", "1100", "-40"],
    ["Q4'25", "1251", "-73"],
    ["Q1'26", "1251", "-24"],
]

_OUTLINED_MATCHING = {
    "type": "data_table",
    "skin": "outlined_boxes",
    "steps_or_data": [
        ["", "Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"],
        ["Reserve Rate for Total Balances", "2.9%", "2.8%", "2.8%", "2.8%", "2.8%"],
    ],
}


def _outlined_slide(primary_steps, secondary):
    return {
        "slide_number": 1,
        "title": "Provisions",
        "layout_type": "stacked_bar_chart",
        "content": {"bullets": [], "key_stats": []},
        "visual_spec": {
            "primary_visual": {
                "type": "stacked_bar_chart",
                "steps_or_data": primary_steps,
            },
            "secondary_visual": secondary,
        },
    }


def test_outlined_row_list_primary_aligns():
    """#136: row-list primary categories must pitch-match outlined cells."""
    html = _render(_outlined_slide(_ROW_LIST_PRIMARY, _OUTLINED_MATCHING))
    assert "chart-support-outlined chart-table-aligned" in html
    assert 'data-align-left="' in html
    assert 'data-align-right="' in html
    assert 'data-align-width="' in html
    # five pitch-matched value slots + one label slot
    cells = re.findall(
        r'<div class="chart-outlined-cell" style="width:([\d.]+)%"',
        html,
    )
    assert len(cells) == 5
    assert all(float(w) > 0 for w in cells)
    # equal pitch across the five period slots
    assert len({round(float(w), 2) for w in cells}) == 1


def test_outlined_mapping_primary_still_aligns():
    primary = [
        {"label": "Q1'25", "values": {"NCO": 1223, "RR": -73}},
        {"label": "Q2'25", "values": {"NCO": 1200, "RR": -50}},
        {"label": "Q3'25", "values": {"NCO": 1100, "RR": -40}},
        {"label": "Q4'25", "values": {"NCO": 1251, "RR": -73}},
        {"label": "Q1'26", "values": {"NCO": 1251, "RR": -24}},
    ]
    html = _render(_outlined_slide(primary, _OUTLINED_MATCHING))
    assert "chart-support-outlined chart-table-aligned" in html
    assert html.count('<div class="chart-outlined-cell" style="width:') == 5


def test_outlined_mismatched_headers_stay_unaligned():
    secondary = {
        "type": "data_table",
        "skin": "outlined_boxes",
        "steps_or_data": [
            ["", "FY24", "FY25"],
            ["Reserve Rate", "2.9%", "2.8%"],
        ],
    }
    html = _render(_outlined_slide(_ROW_LIST_PRIMARY, secondary))
    assert "chart-support-outlined" in html
    assert "chart-table-aligned" not in html
    assert "data-align-left" not in html
    # cells still render, but without pitch widths
    assert html.count('<div class="chart-outlined-cell"') == 2
    assert 'chart-outlined-cell" style="width:' not in html
    assert _ALIGN_JS_MARKER not in html


# ------------------------------------------- #136 Chart.js runtime re-pitch


def test_runtime_align_script_on_aligned_table_skin():
    html = _render(_slide(secondary=_MATCHING_SECONDARY))
    assert _ALIGN_JS_MARKER in html
    assert "chart-table-aligned" in html
    assert 'data-align-left="' in html
    assert "<colgroup>" in html


def test_runtime_align_script_on_aligned_outlined_skin():
    html = _render(_outlined_slide(_ROW_LIST_PRIMARY, _OUTLINED_MATCHING))
    assert _ALIGN_JS_MARKER in html
    assert "chart-support-outlined chart-table-aligned" in html
    assert 'data-align-left="' in html
    assert 'data-align-right="' in html
    assert 'data-align-width="' in html


def test_runtime_align_script_absent_when_unaligned():
    secondary = {
        "type": "data_table",
        "steps_or_data": [
            ["Metric", "Value"],
            ["G&S", "7%"],
        ],
    }
    html = _render(_slide(secondary=secondary))
    assert "chart-support-table" in html
    assert "chart-table-aligned" not in html
    assert _ALIGN_JS_MARKER not in html


def test_runtime_align_script_absent_without_secondary():
    html = _render(_slide())
    assert _ALIGN_JS_MARKER not in html


def test_golden_mvp1_byte_inert_no_align_script(tmp_path):
    """Decks without an aligned support table must not emit the runtime script."""
    out = tmp_path / "out"
    render_deck(_GOLDEN, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert _ALIGN_JS_MARKER not in html
    assert "__rv2ChartTableAlignInstalled" not in html


# ------------------------------------------- #149 label-lane reservation


def _quarters(n: int) -> list[str]:
    # Synthetic labels that still match primary/secondary 1:1.
    return [f"P{i}" for i in range(n)]


def _outlined_n(n: int, *, label: str = "Reserve Rate for Total Balances"):
    cats = _quarters(n)
    primary = [["Quarter", "A", "B"]] + [[c, "100", "-10"] for c in cats]
    secondary = {
        "type": "data_table",
        "skin": "outlined_boxes",
        "steps_or_data": [["", *cats], [label, *(["2.8%"] * n)]],
    }
    return _outlined_slide(primary, secondary)


def test_outlined_lane_layout_reserves_min_label():
    left, right, width = chart_column_interval("stacked_bar_chart", 5)
    lane = outlined_lane_layout(left, right, width, 5)
    assert lane["ok"] is True
    assert lane["label_col_w_px"] >= OUTLINED_LABEL_MIN_PX - 1e-6
    assert lane["sep_px"] >= OUTLINED_LABEL_GAP_PX - 1e-6
    assert lane["shift_px"] > 0  # natural gutter < 200px on chart-split host


@pytest.mark.parametrize("n", [1, 2, 5, 12])
def test_outlined_lane_ok_for_common_counts(n):
    left, right, width = chart_column_interval("stacked_bar_chart", n)
    lane = outlined_lane_layout(left, right, width, n)
    assert lane["ok"] is True
    assert lane["label_col_w_px"] >= OUTLINED_LABEL_MIN_PX - 1e-6


def test_outlined_lane_very_dense_fails_sep():
    # pitch shrinks with n; cell-box side pad eventually < 8px gap.
    left, right, width = chart_column_interval("stacked_bar_chart", 40)
    lane = outlined_lane_layout(left, right, width, 40)
    assert lane["ok"] is False
    assert lane["sep_px"] < OUTLINED_LABEL_GAP_PX


def test_outlined_lane_missing_label_no_min():
    left, right, width = chart_column_interval("stacked_bar_chart", 5)
    lane = outlined_lane_layout(left, right, width, 5, has_label=False)
    assert lane["ok"] is True
    assert lane["shift_px"] == 0.0
    assert lane["label_col_w_px"] == pytest.approx(lane["left_px"])


def test_outlined_lane_dense_or_narrow_fails_closed():
    left, right, width = chart_column_interval("stacked_bar_chart", 5)
    # Force an impossible host: cannot fit 200px label + 5 pitches.
    lane = outlined_lane_layout(
        left, right, width, 5, host_px=120.0, max_left_extend_px=10.0
    )
    assert lane["ok"] is False
    assert lane["mode"] == "stacked"


def test_outlined_static_emits_label_shift_attrs():
    html = _render(_outlined_n(5))
    assert "chart-support-outlined chart-table-aligned" in html
    assert 'data-label-shift="' in html
    assert 'data-label-col="' in html
    shift = float(re.search(r'data-label-shift="([\d.]+)"', html).group(1))
    lab_col = float(re.search(r'data-label-col="([\d.]+)"', html).group(1))
    assert shift > 0
    assert lab_col >= OUTLINED_LABEL_MIN_PX - 1.0
    # label slot is the reserved lane, not the collapsed y-gutter
    lab_pct = float(
        re.search(
            r'<div class="chart-outlined-label" style="width:([\d.]+)%"',
            html,
        ).group(1)
    )
    assert lab_pct > 15.0


def test_outlined_long_label_still_aligned():
    html = _render(
        _outlined_n(5, label="Reserve Rate for Total Card Member Loans and Balances")
    )
    assert "chart-table-aligned" in html
    assert "Reserve Rate for Total Card Member Loans and Balances" in html


def test_outlined_missing_label_still_aligns_cells():
    html = _render(_outlined_n(5, label=""))
    assert "chart-table-aligned" in html
    assert html.count('<div class="chart-outlined-cell" style="width:') == 5
    # empty label slot present
    assert '<div class="chart-outlined-label"' in html


def test_outlined_mapping_primary_label_lane():
    cats = ["Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"]
    primary = [{"label": c, "values": {"NCO": 1, "RR": -1}} for c in cats]
    secondary = {
        "type": "data_table",
        "skin": "outlined_boxes",
        "steps_or_data": [
            ["", *cats],
            ["Reserve Rate for Total Balances", *(["2.8%"] * 5)],
        ],
    }
    html = _render(_outlined_slide(primary, secondary))
    assert "chart-support-outlined chart-table-aligned" in html
    assert 'data-label-shift="' in html


def test_outlined_narrow_host_strict_raises(monkeypatch):
    from impact_slides.renderer_v2.charts import geometry as geom

    monkeypatch.setattr(geom, "OUTLINED_HOST_WIDTH_PX", 80.0)
    monkeypatch.setattr(geom, "OUTLINED_MAX_LEFT_EXTEND_PX", 5.0)
    tok = set_render_strict(True)
    try:
        with pytest.raises(ValueError, match="label lane"):
            _render(_outlined_n(5))
    finally:
        reset_render_strict(tok)


def test_outlined_narrow_host_nonstrict_stacks_and_warns(monkeypatch):
    from impact_slides.renderer_v2.charts import geometry as geom

    monkeypatch.setattr(geom, "OUTLINED_HOST_WIDTH_PX", 80.0)
    monkeypatch.setattr(geom, "OUTLINED_MAX_LEFT_EXTEND_PX", 5.0)
    st = set_render_strict(False)
    wt = begin_render_warnings()
    try:
        html = _render(_outlined_n(5))
    finally:
        warnings = take_render_warnings(wt)
        reset_render_strict(st)
    assert "chart-outlined-stacked" in html
    assert "chart-table-aligned" not in html
    assert _ALIGN_JS_MARKER not in html
    assert any("label lane" in w for w in warnings)


def test_runtime_js_contains_label_lane_constants():
    html = _render(_outlined_n(5))
    assert "LABEL_MIN = 200" in html
    assert "LABEL_GAP = 8" in html
    assert "chart-outlined-stacked" in html  # class name referenced for fallback
    # Runtime live-geometry stack must diagnose (parity with static non-strict).
    assert "cannot reserve label lane" in html
    assert "console.warn" in html


def test_outlined_geometry_playwright_center_and_separation(tmp_path):
    """#149: bar/cell centers AND label/first-cell separation together."""
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    slide = _outlined_n(5)
    handoff = {
        "meta": {"deck_title": "t", "source": "t"},
        "slides": [slide],
    }
    hp = tmp_path / "h.json"
    hp.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(hp, out, strict=False)
    html_path = out / "presentation.html"

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(html_path.resolve().as_uri(), wait_until="domcontentloaded")
        # render_deck may inject a title slide; activate the outlined row's slide.
        page.evaluate(
            """() => {
              const target = document.querySelector('.chart-support-outlined')
                ?.closest('.slide');
              document.querySelectorAll('.slide').forEach(s => {
                const on = s === target;
                s.classList.toggle('active', on);
                s.style.display = on ? 'block' : 'none';
              });
            }"""
        )
        page.wait_for_timeout(1000)
        measured = page.evaluate(
            """() => {
              const box = el => {
                const b = el.getBoundingClientRect();
                return {l:b.left, r:b.right, cx:(b.left+b.right)/2, w:b.width, t:b.top, btm:b.bottom};
              };
              const root = document.querySelector('.slide.active') || document;
              const lab = root.querySelector('.chart-outlined-label .chart-outlined-box');
              const cells = [...root.querySelectorAll(
                '.chart-outlined-cell .chart-outlined-box')];
              const canvas = root.querySelector('canvas');
              const chart = canvas && typeof Chart !== 'undefined' && Chart.getChart(canvas);
              if (!lab || !cells.length || !chart || !chart.scales || !chart.scales.x) {
                return {err: 'no chart', hasLab: !!lab, nCells: cells.length};
              }
              const cr = canvas.getBoundingClientRect();
              const k = cr.width / (chart.width || cr.width || 1);
              const bars = cells.map((_, i) => {
                const tx = chart.scales.x.getPixelForTick(i);
                return cr.left + tx * k;
              });
              const stage = root.getBoundingClientRect();
              return {
                lab: box(lab),
                cells: cells.map(box),
                bars,
                sep: cells[0].getBoundingClientRect().left - lab.getBoundingClientRect().right,
                labText: lab.textContent || '',
                stage: {l: stage.left, r: stage.right, t: stage.top, b: stage.bottom},
                wrapBottom: root.querySelector('.chart-support-outlined')
                  .getBoundingClientRect().bottom,
              };
            }"""
        )
        browser.close()

    assert "err" not in measured
    assert measured["sep"] >= 8.0 - 0.5
    assert measured["lab"]["w"] >= 199.0
    for bar, cell in zip(measured["bars"], measured["cells"]):
        assert abs(cell["cx"] - bar) <= 12.0
    # label fully visible on stage; support row within stage bottom
    assert measured["lab"]["l"] >= measured["stage"]["l"] - 1
    assert measured["lab"]["r"] <= measured["stage"]["r"] + 1
    assert measured["wrapBottom"] <= measured["stage"]["b"] + 1
    assert measured["labText"].strip()


def test_outlined_svg_path_lane_invariants():
    """Static SVG path shares the same lane model as Chart.js (#149)."""
    html_body = render_slide(
        _outlined_n(5), total=1, notes="", active=True, use_chartjs=False
    )
    left = float(re.search(r'data-align-left="([\d.]+)"', html_body).group(1))
    right = float(re.search(r'data-align-right="([\d.]+)"', html_body).group(1))
    width = float(re.search(r'data-align-width="([\d.]+)"', html_body).group(1))
    shift = float(re.search(r'data-label-shift="([\d.]+)"', html_body).group(1))
    lab_col = float(re.search(r'data-label-col="([\d.]+)"', html_body).group(1))
    cell_pcts = [
        float(m)
        for m in re.findall(
            r'<div class="chart-outlined-cell" style="width:([\d.]+)%"', html_body
        )
    ]
    assert len(cell_pcts) == 5
    assert lab_col >= OUTLINED_LABEL_MIN_PX - 1.0
    assert shift > 0
    lane = outlined_lane_layout(left, right, width, 5)
    assert lane["ok"]
    assert abs(lane["shift_px"] - shift) < 1.0
    assert abs(lane["label_col_w_px"] - lab_col) < 1.0
    for i in range(5):
        bar_cx = lane["left_px"] + (i + 0.5) * lane["pitch_px"]
        cell_left = (
            -lane["shift_px"] + lane["label_col_w_px"] + i * lane["pitch_px"]
        )
        cell_cx = cell_left + lane["pitch_px"] / 2
        assert abs(cell_cx - bar_cx) < 0.5
    assert lane["sep_px"] >= OUTLINED_LABEL_GAP_PX - 1e-6
