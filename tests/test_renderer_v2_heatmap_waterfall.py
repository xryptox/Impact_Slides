"""Content-level tests for in-repo heatmap + waterfall painters.

These layouts used to reach only the external boardroom pack. With the pack
absent they rendered chart-empty while the suite stayed green. Assert real
structure with the pack stubbed out.
"""
from __future__ import annotations

import re

import pytest

from impact_slides.renderer_v2 import charts


def _stub_pack_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(charts, "_find_pack_path", lambda: None)
    monkeypatch.setattr(charts, "_PACK", None)
    monkeypatch.setattr(charts, "_PACK_CSS", "")


def _slide(layout: str, steps: list) -> dict:
    return {
        "slide_number": 1,
        "title": "T",
        "layout_type": layout,
        "visual_spec": {"primary_visual": {"steps_or_data": steps}},
        "content": {},
    }


STEPS_WF = [
    {"label": "Q1", "value": 10},
    {"label": "Q2", "value": -5},
    {"label": "Q3", "value": 20},
]
STEPS_HM = STEPS_WF


@pytest.mark.parametrize("use_chartjs", [False, True])
def test_heatmap_pack_independent(monkeypatch, use_chartjs):
    _stub_pack_absent(monkeypatch)
    html = charts.build_chart_html(_slide("heatmap", STEPS_HM), "heatmap", use_chartjs=use_chartjs)
    assert "chart-empty" not in html
    assert "heatmap-table" in html
    assert html.count("heatmap-cell") == 3
    assert "row-head" in html


@pytest.mark.parametrize("use_chartjs", [False, True])
def test_waterfall_pack_independent(monkeypatch, use_chartjs):
    _stub_pack_absent(monkeypatch)
    html = charts.build_chart_html(
        _slide("waterfall_chart", STEPS_WF), "waterfall_chart", use_chartjs=use_chartjs
    )
    assert "chart-empty" not in html
    assert "<svg" in html
    assert html.count("<rect") == 3
    assert "chart-legend" in html


def test_waterfall_running_total_and_fills(monkeypatch):
    _stub_pack_absent(monkeypatch)
    html = charts.build_chart_html(
        _slide("waterfall_chart", STEPS_WF), "waterfall_chart", use_chartjs=False
    )
    # Increases blue, decreases ink.
    assert 'class="chart-bar-blue" fill="#006FCF"' in html
    assert 'class="chart-bar-ink" fill="#63666A"' in html
    assert "+10" in html
    assert "-5" in html
    assert "+20" in html

    # Parse bar y/height — bridges must not all share one baseline.
    rects = re.findall(
        r'<rect class="chart-bar-(?:blue|ink|navy)"[^>]* y="([\d.]+)"[^>]* height="([\d.]+)"',
        html,
    )
    assert len(rects) == 3
    tops = [float(y) for y, _h in rects]
    heights = [float(h) for _y, h in rects]

    # The defining waterfall invariant: each bridge *starts where the previous
    # one ended*, so bar N's near edge meets bar N-1's far edge. Asserting only
    # that one top is above another is not enough -- with the cumulative offset
    # removed, Q3 (20) is still taller than Q1 (10) and such a check passes on
    # plain side-by-side bars. Verified by mutation: replacing
    # `start = level` with `start = 0.0` must fail this test.
    #
    # Q1 +10 -> level 10 : spans 0..10
    # Q2  -5 -> level  5 : spans 5..10, so its bottom == Q1's top
    # Q3 +20 -> level 25 : spans 5..25, so its bottom == Q2's top
    q1_top, q2_top, q3_top = tops
    q1_bot = q1_top + heights[0]
    q2_bot = q2_top + heights[1]
    q3_bot = q3_top + heights[2]

    # SVG y grows downward, so a larger data value means a *smaller* y.
    # Q2 falls 10 -> 5, spanning 5..10: its high edge is Q1's high edge (10).
    assert q2_top == pytest.approx(q1_top, abs=0.5), (
        f"Q2 must hang from Q1's level (cumulative bridge): "
        f"q2_top={q2_top} q1_top={q1_top}"
    )
    # Q3 rises 5 -> 25, spanning 5..25: its low edge rests on Q2's low edge (5).
    assert q3_bot == pytest.approx(q2_bot, abs=0.5), (
        f"Q3 must stand on Q2's resting level (cumulative bridge): "
        f"q3_bot={q3_bot} q2_bot={q2_bot}"
    )
    # Only Q1 is rooted at the zero baseline; the others float above it.
    assert q1_bot > q2_bot and q1_bot > q3_bot
    assert q1_bot > q3_top  # Q1 rooted at 0, Q3 floated well above it


def test_heatmap_alpha_scales_with_value(monkeypatch):
    _stub_pack_absent(monkeypatch)
    html = charts.build_chart_html(_slide("heatmap", STEPS_HM), "heatmap")
    alphas = [float(a) for a in re.findall(r"rgba\(0, 111, 207, ([\d.]+)\)", html)]
    assert len(alphas) == 3
    # Q2=-5 min, Q3=20 max
    assert alphas[1] < alphas[0] < alphas[2]
    assert alphas[1] == pytest.approx(0.15, abs=0.001)
    assert alphas[2] == pytest.approx(0.90, abs=0.001)


def test_heatmap_all_equal_no_divzero(monkeypatch):
    _stub_pack_absent(monkeypatch)
    steps = [{"label": "A", "value": 5}, {"label": "B", "value": 5}]
    html = charts.build_chart_html(_slide("heatmap", steps), "heatmap")
    assert "chart-empty" not in html
    alphas = [float(a) for a in re.findall(r"rgba\(0, 111, 207, ([\d.]+)\)", html)]
    assert alphas == [pytest.approx(0.15)] * 2


def test_heatmap_single_row(monkeypatch):
    _stub_pack_absent(monkeypatch)
    html = charts.build_chart_html(
        _slide("heatmap", [{"label": "Only", "value": 42}]), "heatmap"
    )
    assert html.count("heatmap-cell") == 1
    assert "42" in html


def test_waterfall_zero_and_negative(monkeypatch):
    _stub_pack_absent(monkeypatch)
    steps = [
        {"label": "Start", "value": 0},
        {"label": "Drop", "value": -10},
        {"label": "Up", "value": 4},
    ]
    html = charts.build_chart_html(_slide("waterfall_chart", steps), "waterfall_chart")
    assert "chart-empty" not in html
    assert html.count("<rect") == 3
    assert "chart-bar-ink" in html
    assert "chart-bar-blue" in html
    # Zero line present when range crosses 0.
    assert "chart-gridline" in html


@pytest.mark.parametrize("lt", ["heatmap", "waterfall_chart"])
def test_empty_steps_chart_empty(monkeypatch, lt):
    _stub_pack_absent(monkeypatch)
    html = charts.build_chart_html(_slide(lt, []), lt)
    assert "chart-empty" in html
    assert lt in html or "No chart data" in html


def test_waterfall_total_bars_are_navy_and_absolute(monkeypatch):
    """`kind: "total"` bars are anchored at zero, not floated on the running level.

    Covers the branch a mutation exposed: breaking the `kind == "total"` check
    left every previous test green, because none of them declared a total bar.
    A closing total with value 0 is also auto-filled from the running level,
    which is the idiom for "close at whatever we ended on".
    """
    _stub_pack_absent(monkeypatch)
    steps = [
        {"label": "Open", "value": 100, "kind": "total"},
        {"label": "Up", "value": 50},
        {"label": "Down", "value": -30},
        {"label": "Close", "value": 0, "kind": "total"},
    ]
    html = charts.build_chart_html(
        _slide("waterfall_chart", steps), "waterfall_chart", use_chartjs=False
    )

    # Totals navy, movements blue/ink, in declaration order.
    assert re.findall(r'class="chart-bar-(\w+)"', html) == [
        "navy",
        "blue",
        "ink",
        "navy",
    ]

    # Closing total auto-computes from the running level: 100 + 50 - 30 = 120,
    # and totals print bare (no +/- sign) unlike movement bars.
    values = re.findall(r'class="chart-value"[^>]*>([^<]+)<', html)
    assert values == ["100", "+50", "-30", "120"]

    rects = re.findall(
        r'<rect class="chart-bar-(?:blue|ink|navy)"[^>]* y="([\d.]+)"[^>]* height="([\d.]+)"',
        html,
    )
    tops = [float(y) for y, _h in rects]
    heights = [float(h) for _y, h in rects]
    # Both totals are rooted at the zero baseline, so they share a bottom edge.
    assert tops[0] + heights[0] == pytest.approx(tops[3] + heights[3], abs=0.5)
    # The 120 close is taller than the 100 open.
    assert heights[3] > heights[0]
