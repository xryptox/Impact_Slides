"""T14: non-stacked vertical bars honour point_labels (Chart.js + SVG parity)."""
import re

import pytest

from impact_slides.renderer_v2.charts import (
    _build_grouped_bar_svg,
    _chartjs_bar_config,
    _fmt_bar,
    _fmt_value_label,
)


def _slide(cfg, data):
    return {
        "visual_spec": {
            "layout_type": "x",
            "primary_visual": {
                "chart_type": "x",
                "steps_or_data": data,
                "chart_config": cfg,
            },
        }
    }


def _datalabels(conf):
    return conf["options"]["plugins"]["datalabels"]


def test_grouped_point_labels_with_unit_prefix():
    sl = _slide(
        {"point_labels": True, "y_axis_unit": "$", "y_axis_unit_position": "prefix"},
        [["Q1", 0.9], ["Q2", 2.8]],
    )
    dl = _datalabels(_chartjs_bar_config(sl))
    assert dl["_labels"] == [["$0.9", "$2.8"]]
    assert dl["anchor"] == "end" and dl["align"] == "top"


def test_grouped_point_labels_no_unit():
    sl = _slide({"point_labels": True}, [["Q1", 1251], ["Q2", 219]])
    assert _datalabels(_chartjs_bar_config(sl))["_labels"] == [["1,251", "219"]]


def test_grouped_point_labels_percent_suffix():
    sl = _slide({"point_labels": True, "y_axis_unit": "%"}, [["A", 72], ["B", 21]])
    assert _datalabels(_chartjs_bar_config(sl))["_labels"] == [["72%", "21%"]]


def test_grouped_point_labels_negative_parenthesized():
    sl = _slide({"point_labels": True, "y_axis_unit": "$"}, [["A", 0.7], ["B", -73]])
    assert _datalabels(_chartjs_bar_config(sl))["_labels"] == [["$0.7", "($73)"]]


def test_grouped_without_point_labels_has_no_datalabels():
    sl = _slide({"y_axis_unit": "$"}, [["Q1", 0.9], ["Q2", 2.8]])
    assert "datalabels" not in _chartjs_bar_config(sl)["options"]["plugins"]


def test_stacked_output_unchanged():
    # Stacked recipe must stay the white in-segment set, not the new above-bar one.
    sl = _slide(
        {"point_labels": True, "y_axis_unit": "$", "y_axis_unit_position": "prefix"},
        [["Q1", 0.9], ["Q2", 2.8]],
    )
    dl = _datalabels(_chartjs_bar_config(sl, stacked=True))
    assert dl["_labels"] == [["$0.9", "$2.8"]]
    assert dl["anchor"] == "center" and dl["align"] == "center"


def test_svg_painter_parity():
    # Same handoff → same label text in Chart.js config and noscript SVG.
    sl = _slide(
        {"point_labels": True, "y_axis_unit": "$", "y_axis_unit_position": "prefix"},
        [["Q1", 0.9], ["Q2", 2.8]],
    )
    chartjs = _datalabels(_chartjs_bar_config(sl))["_labels"][0]
    svg_texts = re.findall(r">([^<]+)</text>", _build_grouped_bar_svg(sl))
    for label in chartjs:
        assert label in svg_texts


# --- Formatter contract (T14 review) ----------------------------------------
# The first cut of T14 pointed the SVG painter at the new formatter, which
# silently reformatted existing decks ($0.9B -> $B0.9) and left axis ticks and
# value labels disagreeing on the SAME chart. Nothing pinned _fmt_bar, so the
# suite stayed green. These tests pin the contract that regression violated.


@pytest.mark.parametrize(
    ("value", "unit", "expected"),
    [
        # Compound currency units split around the number, symbol leading.
        (0.9, "$B", "$0.9B"),
        (12, "$B", "$12B"),
        (1223, "$B", "$1,223B"),
        (4.5, "$M", "$4.5M"),
        # Bare currency.
        (0.9, "$", "$0.9"),
        (1251, "$", "$1,251"),
        # Non-currency units trail.
        (72, "%", "72%"),
        (9, "bps", "9bps"),
        (2.5, "x", "2.5x"),
        # No unit; small magnitudes keep their precision.
        (0.05, "", "0.05"),
        (1251, "", "1,251"),
    ],
)
def test_fmt_value_label_unit_placement(value, unit, expected):
    assert _fmt_value_label(value, unit) == expected


@pytest.mark.parametrize(
    ("unit", "expected"),
    [("", "(73)"), ("$", "($73)"), ("%", "(73%)"), ("$B", "($73B)")],
)
def test_fmt_value_label_negatives_are_ir_parenthesized(unit, expected):
    assert _fmt_value_label(-73, unit) == expected


def test_fmt_value_label_explicit_position_overrides_default():
    assert _fmt_value_label(12, "$", "suffix") == "12$"
    assert _fmt_value_label(12, "%", "prefix") == "%12"


@pytest.mark.parametrize("unit", ["", "$", "%", "$B", "$M", "bps"])
@pytest.mark.parametrize("value", [0, 0.05, 0.9, 12, 72, 1223, 15000])
def test_axis_ticks_and_value_labels_never_disagree(unit, value):
    """A chart must not label a bar differently from its own axis tick.

    Negatives are the one intended divergence (ticks stay signed, value
    labels take IR parentheses) and are covered separately above.
    """
    assert _fmt_bar(value, unit) == _fmt_value_label(value, unit)


def test_svg_value_labels_match_axis_ticks_on_compound_unit():
    """End-to-end guard for the regression: $B must not paint as $B0.9."""
    sl = _slide(
        {"point_labels": True, "y_axis_unit": "$B", "series_names": ["A", "B"]},
        [["Q1", 0.9, 1.4], ["Q2", 2.8, 3.1]],
    )
    svg = _build_grouped_bar_svg(sl)
    assert "$0.9B" in svg and "$B0.9" not in svg
    assert _datalabels(_chartjs_bar_config(sl))["_labels"][0][0] == "$0.9B"
