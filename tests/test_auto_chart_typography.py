"""#150 — public auto-typography resolver and renderer integration."""
from __future__ import annotations

import json
import re

import pytest

from impact_slides.renderer_v2 import render_deck
from impact_slides.renderer_v2.charts.auto_typography import (
    AUTO_X_LO,
    AUTO_Y_LO,
    resolve_auto_typography,
    sync_sibling_plans,
)
from impact_slides.renderer_v2.charts.typography import resolve_typography


def _handoff(slides):
    return {
        "meta": {"title": "t", "client": "c", "date": "2026-01-01"},
        "presentation": {"title": "t"},
        "slides": slides,
    }


def _pane(kind, labels, *, typography=None, short=False):
    cfg = {"point_labels": True, "series_names": ["Revenue"]}
    if typography is not None:
        cfg["typography"] = typography
    return {
        "type": kind,
        "chart_config": cfg,
        "steps_or_data": [
            {"label": label, "short_label": f"Q{i + 1}" if short else None, "value": i + 1}
            for i, label in enumerate(labels)
        ],
    }


def _configs(html):
    return [
        json.loads(raw)
        for raw in re.findall(
            r'<script type="application/json" class="chartjs-config"[^>]*>(.*?)</script>',
            html,
            re.S,
        )
    ]


def test_auto_mode_validates_raised_explicit_floors():
    with pytest.raises(ValueError, match="12"):
        resolve_typography({"typography": {"mode": "auto", "x_tick_font_size": 11}})
    with pytest.raises(ValueError, match="11"):
        resolve_typography({"typography": {"mode": "auto", "datalabel_font_size": 10}})
    assert resolve_typography({"typography": {"mode": "auto"}})["auto_mode"] == 1


def test_resolver_preserves_labels_before_ellipsis_and_keeps_endpoints():
    plan = resolve_auto_typography(
        chart_type="line_chart",
        host_w=220,
        host_h=180,
        categories=["Long reporting period alpha beta"] * 8,
        short_labels=[None] * 8,
        y_tick_values=[-10, -5, 0, 5, 10],
        y_tick_labels=["-10%", "-5%", "0%", "5%", "10%"],
    )
    assert plan.x_tick_font_size >= AUTO_X_LO
    assert plan.y_tick_font_size >= AUTO_Y_LO
    assert plan.x_labels is not None
    assert plan.x_labels.used_skip or plan.x_labels.used_ellipsis or plan.x_labels.used_wrap
    if plan.x_labels.used_skip:
        assert plan.x_labels.texts[0]
        assert plan.x_labels.texts[-1]


def test_sibling_sync_uses_common_auto_sizes_but_preserves_explicit_channel():
    wide = resolve_auto_typography(
        chart_type="grouped_bar_chart", host_w=900, host_h=480,
        categories=["Q1", "Q2"], y_tick_values=[0, 10], y_tick_labels=["0", "10"],
    )
    dense = resolve_auto_typography(
        chart_type="grouped_bar_chart", host_w=260, host_h=220,
        categories=[f"Long category {i}" for i in range(12)],
        y_tick_values=[0, 10], y_tick_labels=["0", "10"],
        x_explicit=18,
    )
    synced = sync_sibling_plans([wide, dense])
    assert synced[1].x_tick_font_size == 18
    assert synced[0].x_tick_font_size <= wide.x_tick_font_size
    assert synced[0].y_tick_font_size == synced[1].y_tick_font_size


def test_dual_chart_applies_synced_auto_plan_to_chartjs_svg_and_metadata(tmp_path):
    typo = {"mode": "auto"}
    slide = {
        "slide_number": 17,
        "title": "Auto", "layout_type": "dual_chart", "content": {"so_what": "x"},
        "visual_spec": {
            "primary_visual": _pane("grouped_bar_chart", [f"Period {i}" for i in range(8)], typography=typo),
            "secondary_visual": _pane("line_chart", [f"Long reporting period {i}" for i in range(8)], typography=typo),
        }, "evidence_sources": [],
    }
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(_handoff([slide])), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(path, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    configs = _configs(html)
    assert len(configs) == 2
    x_sizes = [c["options"]["scales"]["x"]["ticks"]["font"]["size"] for c in configs]
    y_sizes = [c["options"]["scales"]["y"]["ticks"]["font"]["size"] for c in configs]
    assert x_sizes[0] == x_sizes[1] and x_sizes[0] >= AUTO_X_LO
    assert y_sizes[0] == y_sizes[1] and y_sizes[0] >= AUTO_Y_LO
    assert html.count('data-auto-typo="1"') == 2
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert len(meta["auto_typography"]) == 2


def test_svg_and_chartjs_receive_the_same_auto_sizes(tmp_path):
    pane = _pane(
        "grouped_bar_chart", [f"Long period {i}" for i in range(7)],
        typography={"mode": "auto"},
    )
    slide = {
        "slide_number": 1, "title": "Auto", "layout_type": "grouped_bar_chart", "content": {},
        "visual_spec": {"primary_visual": pane}, "evidence_sources": [],
    }
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(_handoff([slide])), encoding="utf-8")
    chartjs_out, svg_out = tmp_path / "chartjs", tmp_path / "svg"
    render_deck(path, chartjs_out, strict=False)
    render_deck(path, svg_out, strict=False, suppress_features=["charts"])
    cfg = _configs((chartjs_out / "presentation.html").read_text(encoding="utf-8"))[0]
    chartjs_x = cfg["options"]["scales"]["x"]["ticks"]["font"]["size"]
    chartjs_y = cfg["options"]["scales"]["y"]["ticks"]["font"]["size"]
    svg = (svg_out / "presentation.html").read_text(encoding="utf-8")
    assert f'font-size="{chartjs_x}"' in svg
    assert f'font-size="{chartjs_y}"' in svg
    assert 'data-auto-typo="1"' not in svg  # SVG has no canvas wrapper.


def test_auto_mode_does_not_change_legacy_output(tmp_path):
    slide = {
        "slide_number": 1, "title": "Legacy", "layout_type": "grouped_bar_chart", "content": {},
        "visual_spec": {"primary_visual": _pane("grouped_bar_chart", ["Q1", "Q2"]),},
        "evidence_sources": [],
    }
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(_handoff([slide])), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(path, out, strict=False)
    cfg = _configs((out / "presentation.html").read_text(encoding="utf-8"))[0]
    assert cfg["options"]["scales"]["x"]["ticks"]["font"]["size"] == 13
