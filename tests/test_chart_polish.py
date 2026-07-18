"""Tests for line/combo chart polish (Fidelity T3, issue #31).

- Per-point label side selection so converging 2-series labels never collide
- Currency unit formatting ($ prefix, $B style)
- Multi-line annotation callouts (real newlines AND escaped \\n)
"""
from __future__ import annotations

import re

from impact_slides.renderer_v2.charts import (
    _build_combo_chart_svg,
    _build_grouped_bar_svg,
    _build_line_chart_svg,
)


def _labels(html: str) -> list[tuple[float, float, str]]:
    """Extract (x, y, text) from SVG text elements."""
    return [
        (float(m.group(1)), float(m.group(2)), m.group(3))
        for m in re.finditer(
            r'<text x="([\d.-]+)" y="([\d.-]+)"[^>]*>([^<]+)</text>', html
        )
    ]


def _two_series_slide(primary: float, secondary: float, **over):
    slide = {
        "slide_number": 1,
        "title": "Test",
        "layout_type": "line_chart",
        "content": {},
        "visual_spec": {
            "primary_visual": {
                "type": "line_chart",
                "steps_or_data": [
                    {"label": "Q1'25", "value": primary, "series_2": secondary},
                ],
            },
            "chart_config": {"y_axis_unit": "%"},
        },
        "evidence_sources": [],
    }
    slide.update(over)
    return slide


# ------------------------------------------------------- label collisions


def test_secondary_higher_labels_flip_sides():
    """When series_2 is the higher line, its label goes above and the
    primary label goes below (old fixed-side code collided here)."""
    html = _build_line_chart_svg(_two_series_slide(8, 9))
    labels = _labels(html)
    p8 = [y for x, y, t in labels if t == "8%"]
    p9 = [y for x, y, t in labels if t == "9%"]
    assert p8 and p9
    # 9% is the higher line -> its label must be above (smaller y)
    assert p9[0] < p8[0]
    # and comfortably separated (no overlap)
    assert p8[0] - p9[0] > 20


def test_primary_higher_keeps_default_sides():
    """When the primary series is higher, primary stays above / secondary
    below (same as before)."""
    html = _build_line_chart_svg(_two_series_slide(9, 8))
    labels = _labels(html)
    p8 = [y for x, y, t in labels if t == "8%"]
    p9 = [y for x, y, t in labels if t == "9%"]
    assert p9[0] < p8[0]
    assert p8[0] - p9[0] > 20


def test_close_series_labels_do_not_overlap():
    """Converging series (8 vs 9) must have well-separated labels."""
    slide = _two_series_slide(8, 9)
    slide["visual_spec"]["primary_visual"]["steps_or_data"] = [
        {"label": "Q1'25", "value": 8, "series_2": 9},
        {"label": "Q2'25", "value": 9, "series_2": 8},
    ]
    html = _build_line_chart_svg(slide)
    labels = [(x, y, t) for x, y, t in _labels(html) if t in ("8%", "9%")]
    # group by x position
    xs = sorted({round(x) for x, _, _ in labels})
    assert len(xs) == 2
    for xv in xs:
        ys = sorted(y for x, y, _ in labels if round(x) == xv)
        assert len(ys) == 2
        assert ys[1] - ys[0] > 20


# ------------------------------------------------------- currency units


def test_line_chart_dollar_unit_prefix():
    slide = _two_series_slide(8, 9)
    slide["visual_spec"]["chart_config"] = {"y_axis_unit": "$"}
    html = _build_line_chart_svg(slide)
    assert ">$8</text>" in html
    assert "8$" not in html


def test_combo_chart_dollar_billions_unit():
    slide = {
        "slide_number": 1,
        "title": "Capital",
        "layout_type": "combo_chart",
        "content": {},
        "visual_spec": {
            "primary_visual": {
                "type": "combo_chart",
                "steps_or_data": [
                    {"label": "Q4'24", "value": 1.6},
                    {"label": "Q1'25", "value": 1.3},
                ],
            },
            "chart_config": {"y_axis_unit": "$B"},
            "line_overlay": {
                "data": [{"label": "Q4'24", "value": 702}],
                "dual_axis": False,
            },
        },
        "evidence_sources": [],
    }
    html = _build_combo_chart_svg(slide)
    assert "$1.6B" in html
    assert "1.6$B" not in html


def test_grouped_bar_currency_unit():
    slide = {
        "slide_number": 1,
        "title": "T",
        "layout_type": "grouped_bar_chart",
        "content": {},
        "visual_spec": {
            "primary_visual": {
                "type": "grouped_bar_chart",
                "steps_or_data": [{"label": "Q1", "value": 1600}],
            },
            "chart_config": {"y_axis_unit": "$"},
        },
        "evidence_sources": [],
    }
    html = _build_grouped_bar_svg(slide)
    assert "$1,600" in html


def test_percent_unit_unchanged():
    html = _build_line_chart_svg(_two_series_slide(8, 9))
    assert ">8%</text>" in html


# ------------------------------------------------------- annotations


def _annotation_slide(text: str):
    slide = _two_series_slide(8, 9)
    slide["visual_spec"]["chart_config"]["annotation"] = {
        "text": text,
        "x": 300,
        "y": 150,
    }
    return slide


def test_annotation_splits_on_real_newlines():
    html = _build_line_chart_svg(_annotation_slide("Leap Year\nApprox.\n(1%)"))
    assert ">Leap Year</text>" in html
    assert ">Approx.</text>" in html
    assert ">(1%)</text>" in html


def test_annotation_splits_on_escaped_newlines():
    html = _build_line_chart_svg(_annotation_slide("Line A\\nLine B"))
    assert ">Line A</text>" in html
    assert ">Line B</text>" in html
