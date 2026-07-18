"""Tests for bracket group annotations above bar charts (Fidelity T5/#33, gap #15).

chart_config.bar_groups: [{"label": str, "start": int, "end": int}] draws a
labeled bracket spanning the inclusive category range above the bars.
"""
from __future__ import annotations

import re

from impact_slides.renderer_v2.charts import (
    _build_grouped_bar_svg,
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


_SIX_BARS = [
    {"label": "US Cons", "value": 10},
    {"label": "US SME", "value": 4},
    {"label": "US L&G", "value": 4},
    {"label": "Int'l Cons", "value": 13},
    {"label": "Int'l SME", "value": 12},
    {"label": "Processed", "value": 9},
]


def _brackets(html: str) -> list[str]:
    return re.findall(r'<g class="bar-group-bracket">.*?</g>', html, re.S)


def test_bracket_renders_on_grouped():
    slide = _slide(
        "grouped_bar_chart",
        _SIX_BARS,
        bar_groups=[{"label": "Billed Business", "start": 0, "end": 4}],
    )
    html = _build_grouped_bar_svg(slide)
    assert 'class="bar-group-bracket"' in html
    assert ">Billed Business</text>" in html


def test_bracket_span_positioning():
    """Bracket spans from the first group's slot start to the last slot end."""
    slide = _slide(
        "grouped_bar_chart",
        _SIX_BARS,
        bar_groups=[{"label": "Billed Business", "start": 0, "end": 4}],
    )
    html = _build_grouped_bar_svg(slide)
    bracket = _brackets(html)[0]
    # plot: pad_l=70, pad_r=30 -> plot_w=800, slot=800/6=133.33
    x1, x2 = (float(v) for v in re.search(r'x1="([\d.]+)" y1="[\d.]+" x2="([\d.]+)"', bracket).groups())
    assert abs(x1 - 76.0) < 2.0          # 70 + 0*slot + 6
    assert abs(x2 - 730.7) < 2.0         # 70 + 5*slot - 6
    # label centered on the span
    lx = float(re.search(r'<text x="([\d.]+)"', bracket).group(1))
    assert abs(lx - (x1 + x2) / 2) < 1.0


def test_multiple_groups_side_by_side():
    slide = _slide(
        "grouped_bar_chart",
        _SIX_BARS,
        bar_groups=[
            {"label": "Billed Business", "start": 0, "end": 4},
            {"label": "Processed", "start": 5, "end": 5},
        ],
    )
    html = _build_grouped_bar_svg(slide)
    brackets = _brackets(html)
    assert len(brackets) == 2
    assert ">Processed</text>" in html


def test_bracket_on_stacked():
    slide = _slide(
        "stacked_bar_chart",
        [
            {"label": "Q1", "values": {"A": 100, "B": 50}},
            {"label": "Q2", "values": {"A": 100, "B": 50}},
        ],
        bar_groups=[{"label": "H1", "start": 0, "end": 1}],
    )
    html = _build_stacked_bar_svg(slide)
    assert 'class="bar-group-bracket"' in html
    assert ">H1</text>" in html


def test_no_groups_no_bracket_and_unchanged_layout():
    slide = _slide("grouped_bar_chart", _SIX_BARS)
    html = _build_grouped_bar_svg(slide)
    assert "bar-group-bracket" not in html
    # pad_t stays at the single-series default 40: top y-axis line at y=40
    assert 'y1="40" x2="70" y2="424"' in html or 'x1="70" y1="40"' in html


def test_bracket_expands_top_padding():
    """With groups present, the plot starts lower to make room (pad_t 68)."""
    slide = _slide(
        "grouped_bar_chart",
        _SIX_BARS,
        bar_groups=[{"label": "G", "start": 0, "end": 5}],
    )
    html = _build_grouped_bar_svg(slide)
    # y-axis vertical line must start at the expanded pad_t (40 + 28 = 68)
    assert re.search(r'<line x1="70" y1="68"', html)


def test_out_of_range_indices_clamped():
    slide = _slide(
        "grouped_bar_chart",
        _SIX_BARS,
        bar_groups=[{"label": "All", "start": -2, "end": 99}],
    )
    html = _build_grouped_bar_svg(slide)
    assert ">All</text>" in html
