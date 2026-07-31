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
    # Q3 sits on cumulative 5 after Q1+Q2, so its top is above Q1's top.
    assert tops[2] < tops[0]


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
