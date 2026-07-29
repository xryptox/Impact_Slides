"""T14: non-stacked vertical bars honour point_labels (Chart.js + SVG parity)."""
import re

from impact_slides.renderer_v2.charts import (
    _build_grouped_bar_svg,
    _chartjs_bar_config,
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
