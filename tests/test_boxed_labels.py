"""#151 — category-aligned boxed bar labels (Chart.js + SVG)."""
from __future__ import annotations

import copy
import json
import re

import pytest

from impact_slides.renderer_v2.charts.bars import (
    _build_grouped_bar_svg,
    resolve_boxed_labels,
)
from impact_slides.renderer_v2.charts.chartjs import (
    _chartjs_bar_config,
    _build_chartjs_html,
)
from impact_slides.renderer_v2.charts.typography import (
    begin_render_warnings,
    reset_render_strict,
    set_render_strict,
    take_render_warnings,
)


def _slide(values=None, *, extra_cfg=None, bar_vals=None):
    vals = bar_vals or [4.2, 4.2, 4.5, 4.5, 4.7]
    labels = ["Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"]
    cfg = {
        "y_axis_min": 0,
        "y_axis_max": 6,
        "boxed_labels": {
            "label": "YoY Growth",
            "values": values
            if values is not None
            else ["11%", "12%", "12%", "12%", "12%"],
        },
    }
    if extra_cfg:
        cfg.update(extra_cfg)
    return {
        "slide_number": 18,
        "layout_type": "grouped_bar_chart",
        "title": "Premium Lending",
        "content": {},
        "visual_spec": {
            "primary_visual": {
                "type": "grouped_bar_chart",
                "steps_or_data": [
                    {"label": lab, "value": v} for lab, v in zip(labels, vals)
                ],
                "chart_config": cfg,
            }
        },
    }


def test_category_mismatch_strict():
    tok = set_render_strict(True)
    try:
        with pytest.raises(ValueError, match="boxed_labels"):
            resolve_boxed_labels(
                {"label": "YoY", "values": ["1%", "2%"]}, category_count=5
            )
    finally:
        reset_render_strict(tok)


def test_category_mismatch_non_strict_drops():
    tok = set_render_strict(False)
    wtok = begin_render_warnings()
    try:
        out = resolve_boxed_labels(
            {"label": "YoY", "values": ["1%"]}, category_count=5
        )
    finally:
        warnings = take_render_warnings(wtok)
        reset_render_strict(tok)
    assert out is None
    assert any("boxed_labels" in w for w in warnings)


def test_svg_in_bar_geometry():
    svg = _build_grouped_bar_svg(_slide())
    assert "boxed-label" in svg
    assert svg.count("boxed-label-box") == 5
    for v in ("11%", "12%"):
        assert v in svg
    assert 'data-boxed-placement="inside"' in svg


def test_svg_short_bar_outside_with_connector():
    # tiny bars so inside placement fails the readability floor
    svg = _build_grouped_bar_svg(
        _slide(bar_vals=[0.05, 0.05, 0.05, 0.05, 0.05], values=["11%"] * 5)
    )
    assert 'data-boxed-placement="outside"' in svg
    assert "boxed-label-connector" in svg
    assert svg.count('data-boxed-placement="outside"') == 5


def test_chartjs_plugin_payload():
    cfg = _chartjs_bar_config(_slide(), host_w=900, host_h=480)
    assert cfg is not None
    boxed = cfg["options"]["plugins"]["boxedLabels"]
    assert boxed["label"] == "YoY Growth"
    assert boxed["values"] == ["11%", "12%", "12%", "12%", "12%"]
    assert boxed["minFontSize"] >= 11


def test_chartjs_short_bar_outside_runtime(tmp_path):
    """Short bars: Chart.js paints outside boxed labels (dataset diagnose attrs)."""
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright
    from impact_slides.renderer_v2 import render_deck

    handoff = {
        "meta": {"title": "t", "client": "c", "date": "2026-01-01"},
        "presentation": {"title": "t"},
        "slides": [
            _slide(
                bar_vals=[0.05, 0.05, 0.05, 0.05, 0.05],
                values=["11%"] * 5,
            )
        ],
    }
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(path, out, strict=True)
    html_path = (out / "presentation.html").resolve()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(html_path.as_uri(), wait_until="networkidle")
        page.evaluate(
            """() => {
              const slide = document.querySelector('.slide[data-layout="grouped_bar_chart"]');
              if (!slide) return;
              document.querySelectorAll('.slide.active').forEach(s => s.classList.remove('active'));
              slide.classList.add('active');
              const stage = document.querySelector('.deck-stage');
              if (stage) stage.style.transform = 'none';
            }"""
        )
        page.wait_for_function(
            """() => {
              const slide = document.querySelector('.slide[data-layout="grouped_bar_chart"]');
              const c = slide && slide.querySelector('canvas');
              return !!(c && c.dataset && c.dataset.rv2BoxedLabels === '1');
            }""",
            timeout=15000,
        )
        stats = page.evaluate(
            """() => {
              const slide = document.querySelector('.slide[data-layout="grouped_bar_chart"]');
              const c = slide && slide.querySelector('canvas');
              if (!c) return null;
              return {
                painted: c.dataset.rv2BoxedLabelsPainted,
                outside: c.dataset.rv2BoxedLabelsOutside,
                attrOutside: c.getAttribute('data-boxed-outside'),
              };
            }"""
        )
        browser.close()
    assert stats is not None
    assert int(stats["painted"] or 0) == 5
    assert int(stats["outside"] or 0) == 5
    assert int(stats["attrOutside"] or 0) == 5


def test_chartjs_html_embeds_plugin_not_collision():
    html = _build_chartjs_html(_slide(), "grouped_bar_chart")
    assert "boxedLabels" in html
    assert "rv2BoxedLabels" in html
    # Plugin is dedicated furniture, not the ordinary datalabel collision helper.
    assert "suppress_colliding_labels" not in html

def test_independent_of_ordinary_collision_suppression():
    """Boxed labels still paint when ordinary datalabels would be suppressed."""
    from impact_slides.renderer_v2.charts import bars as bars_mod

    slide = _slide(
        extra_cfg={
            "point_labels": True,
            "typography": {"datalabel_font_size": 32},
        }
    )
    real = bars_mod.suppress_colliding_labels

    def _drop_all(labels, **kwargs):
        # suppress every ordinary label index; boxed furniture is separate.
        n = len(labels) if labels is not None else 0
        return list(range(n)), [{"series": 0, "category": i, "label": "x", "reason": "forced"} for i in range(n)]

    bars_mod.suppress_colliding_labels = _drop_all  # type: ignore[assignment]
    try:
        svg = _build_grouped_bar_svg(slide)
    finally:
        bars_mod.suppress_colliding_labels = real  # type: ignore[assignment]
    assert "boxed-label" in svg
    assert svg.count("boxed-label-box") == 5
    for v in ("11%", "12%"):
        assert v in svg

def test_readable_floor_constant():
    from impact_slides.renderer_v2.charts.bars import BOXED_LABEL_MIN_FS

    assert BOXED_LABEL_MIN_FS >= 11


def test_no_default_output_without_config():
    slide = _slide()
    del slide["visual_spec"]["primary_visual"]["chart_config"]["boxed_labels"]
    svg = _build_grouped_bar_svg(slide)
    assert "boxed-label" not in svg
    cfg = _chartjs_bar_config(slide)
    plugins = (cfg or {}).get("options", {}).get("plugins", {})
    assert "boxedLabels" not in plugins
