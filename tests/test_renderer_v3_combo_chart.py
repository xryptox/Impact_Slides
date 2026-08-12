"""Renderer v3 typed grouped/stacked combo charts (#185).

Seams under test:
- typed single_chart combo with bar_mode grouped|stacked (D136/D161/D244)
- bar+line layers, axis ownership, complete identity (D230/D244)
- Chart.js/SVG layer order + geometry, D247 semantic table
- malformed modes/axes/layers strict-fail (D102 complete-pane contract)
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.charts import (
    freeze_combo_chart,
    paint_chart_svg,
    paint_semantic_table,
)
from impact_slides.renderer_v3.format import MISSING_VISIBLE
from impact_slides.renderer_v3.models import ComboChartVisual, SingleChartSlide
from impact_slides.renderer_v3.plan import plan_deck
from impact_slides.renderer_v3.schema_export import check_schema

ROOT = Path(__file__).resolve().parents[1]
COMBO = ROOT / "tests/fixtures/renderer_v3/minimal_combo_chart.json"
STACKED = ROOT / "tests/fixtures/renderer_v3/minimal_stacked_bar.json"


def _s() -> dict:
    return json.loads(COMBO.read_text(encoding="utf-8"))


def _chart_slide(raw: dict, surface: str = "cap-combo") -> dict:
    for s in raw["slides"]:
        if s.get("layout_type") != "single_chart":
            continue
        vis = s.get("payload", {}).get("primary_visual", {})
        if vis.get("surface_id") == surface:
            return s
    raise KeyError(surface)


def _vis(raw: dict, surface: str = "cap-combo") -> dict:
    return _chart_slide(raw, surface)["payload"]["primary_visual"]


# ---------------------------------------------------------------------------
# Validation / model
# ---------------------------------------------------------------------------


def test_combo_deck_validates_grouped_and_stacked():
    result = validate_handoff(_s(), strict=True)
    assert result.ok
    g = result.deck.slides[1]
    assert isinstance(g, SingleChartSlide)
    gc = g.payload.primary_visual
    assert isinstance(gc, ComboChartVisual)
    assert gc.chart_type == "combo"
    assert gc.bar_mode == "grouped"
    assert gc.value_axes.secondary is not None
    marks = [s.mark_type for s in gc.chart_data.series]
    assert marks.count("bar") == 2 and marks.count("line") == 1

    sc = result.deck.slides[2].payload.primary_visual
    assert isinstance(sc, ComboChartVisual)
    assert sc.bar_mode == "stacked"
    assert sc.value_axes.secondary is None
    assert sc.auxiliary_series and sc.auxiliary_series[0].role == "authored_stack_total"


def test_schema_includes_combo_branch():
    check_schema()  # raises on drift after regenerate


def test_strict_rejects_missing_bar_mode():
    raw = _s()
    del _vis(raw)["bar_mode"]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_bars_only():
    raw = _s()
    vis = _vis(raw)
    vis["chart_data"]["series"] = [
        s for s in vis["chart_data"]["series"] if s["mark_type"] == "bar"
    ]
    del vis["value_axes"]["secondary"]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_lines_only():
    raw = _s()
    vis = _vis(raw)
    vis["chart_data"]["series"] = [
        s for s in vis["chart_data"]["series"] if s["mark_type"] == "line"
    ]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_mixed_line_axes():
    raw = _s()
    vis = _vis(raw)
    # Add a second line on primary while ROE stays secondary.
    vis["chart_data"]["series"].append(
        {
            "series_id": "eps",
            "name": "EPS",
            "mark_type": "line",
            "axis_key": "primary",
            "values": ["1", "2", "3", "4"],
        }
    )
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_secondary_without_secondary_lines():
    raw = _s()
    vis = _vis(raw)
    for s in vis["chart_data"]["series"]:
        if s["mark_type"] == "line":
            s["axis_key"] = "primary"
    # secondary axis still present
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_secondary_lines_without_axis():
    raw = _s()
    vis = _vis(raw)
    del vis["value_axes"]["secondary"]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_bar_on_secondary():
    raw = _s()
    vis = _vis(raw)
    vis["chart_data"]["series"][0]["axis_key"] = "secondary"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_pane_title_identity():
    raw = _s()
    _vis(raw)["display"] = {"series_identity": "pane_title"}
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_coverage_on_combo():
    raw = _s()
    _vis(raw)["coverage_callout"] = {
        "callout_id": "c1",
        "label": "Cov",
        "value": "50",
        "format_id": "pct_1",
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_leading_break():
    raw = _s()
    vis = _vis(raw)
    vis["value_axes"]["primary"]["domain"] = {
        "kind": "generated",
        "min": "0",
        "target_ticks": 5,
    }
    vis["value_axes"]["primary"]["leading_break"] = {"to": "1"}
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_stack_policies_on_grouped():
    raw = _s()
    _vis(raw)["display"] = {"stack_segments": "show", "series_identity": "legend"}
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_boxed_on_stacked_combo():
    raw = _s()
    vis = _vis(raw, "dep-combo")
    vis["auxiliary_series"] = [
        {
            "auxiliary_id": "box",
            "role": "boxed_label",
            "label": "Box",
            "format_id": "usd_0",
            "target_series_id": "retail",
            "values": ["1", "2", "3", "4"],
        }
    ]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_authored_total_on_grouped():
    raw = _s()
    vis = _vis(raw)
    vis["auxiliary_series"] = [
        {
            "auxiliary_id": "tot",
            "role": "authored_stack_total",
            "label": "Tot",
            "format_id": "usd_0",
            "values": ["1", "2", "3", "4"],
        }
    ]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_one_category():
    raw = _s()
    vis = _vis(raw)
    vis["chart_data"]["categories"] = [vis["chart_data"]["categories"][0]]
    for s in vis["chart_data"]["series"]:
        s["values"] = [s["values"][0]]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_line_style_on_bar():
    raw = _s()
    vis = _vis(raw)
    vis["chart_data"]["series"][0]["style"] = {
        "line_style": "dashed",
        "marker": "square",
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_non_combo_still_forbids_secondary_axis():
    raw = json.loads(STACKED.read_text(encoding="utf-8"))
    vis = next(
        s["payload"]["primary_visual"]
        for s in raw["slides"]
        if s.get("layout_type") == "single_chart"
    )
    vis["value_axes"]["secondary"] = {
        "visible": True,
        "format_id": "usd_0",
        "domain": {"kind": "generated"},
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


# ---------------------------------------------------------------------------
# Freeze / paint
# ---------------------------------------------------------------------------


def test_semantic_table_uses_secondary_format_for_line():
    deck = validate_handoff(_s(), strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["cap-combo"].chart_paint
    table = cp["semantic_table"]
    col_ids = [c["series_id"] for c in table["columns"]]
    roe_i = col_ids.index("roe")
    # ROE 12.0 on pct_1 must not look like usd (no leading $).
    cell = table["rows"][0]["cells"][roe_i]
    assert "$" not in cell["visible"]
    assert "12" in cell["visible"]


def test_auto_identity_endpoints_and_bar_legend():
    raw = _s()
    del _vis(raw)["display"]  # auto
    deck = validate_handoff(raw, strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["cap-combo"].chart_paint
    assert cp["identity_strategy"] in ("endpoints_and_bar_legend", "legend")
    if cp["identity_strategy"] == "endpoints_and_bar_legend":
        id_places = [p for p in cp["placements"] if p.get("kind") == "identity"]
        assert id_places
        assert all(
            next(s for s in cp["series"] if s["series_id"] == p["series_id"])[
                "mark_type"
            ]
            == "line"
            for p in id_places
        )


def test_freeze_grouped_layers_axes_and_identity():
    deck = validate_handoff(_s(), strict=True).deck
    chart = deck.slides[1].payload.primary_visual
    frozen = freeze_combo_chart(chart, deck.number_formats)
    assert frozen["chart_type"] == "combo"
    assert frozen["bar_mode"] == "grouped"
    assert frozen["geometry"]["stacked"] is False
    assert frozen["secondary_domain"] is not None
    marks = [s["mark_type"] for s in frozen["series"]]
    assert marks == ["bar", "bar", "line"]
    assert all(s["axis_key"] == "primary" for s in frozen["series"] if s["mark_type"] == "bar")
    assert frozen["series"][2]["axis_key"] == "secondary"
    # bars present; null dividend@q4 keeps slot
    bars = frozen["bars"]
    assert any(b["series_id"] == "dividends" and b["category_id"] == "q4" and b.get("missing") for b in bars)
    # line points on secondary
    line_pts = [p for p in frozen["points"] if p["mark_type"] == "line"]
    assert len(line_pts) == 4
    assert all(p["finite"] for p in line_pts)
    assert frozen["identity_strategy"] == "legend"
    facts = " ".join(frozen["semantic_table"]["facts"])
    assert "Bar mode: grouped" in facts
    assert "secondary" in facts.lower() or "Secondary" in facts
    # category groups preserved
    assert len(frozen["category_groups"]) == 2


def test_freeze_stacked_sign_order_and_totals():
    deck = validate_handoff(_s(), strict=True).deck
    chart = deck.slides[2].payload.primary_visual
    frozen = freeze_combo_chart(chart, deck.number_formats)
    assert frozen["bar_mode"] == "stacked"
    assert frozen["geometry"]["stacked"] is True
    by = {(b["series_id"], b["category_id"]): b for b in frozen["bars"]}
    r = by[("retail", "q1")]
    w = by[("wholesale", "q1")]
    assert r["stack_base"] == 0.0
    assert r["stack_top"] == 40.0
    assert w["stack_base"] == 40.0
    assert w["stack_top"] == 70.0
    # line overlays category centers
    line_pts = [p for p in frozen["points"] if p["mark_type"] == "line"]
    assert len(line_pts) == 4
    assert all(p["axis_key"] == "primary" for p in line_pts)
    authored = [t for t in frozen["stack_totals"] if t.get("source") == "authored"]
    assert len(authored) == 4
    table = frozen["semantic_table"]
    assert any(c["series_id"] == "share" for c in table["columns"])
    assert any("_pos_total" == c["series_id"] for c in table["columns"])


def test_plan_freezes_both_combo_surfaces():
    deck = validate_handoff(_s(), strict=True).deck
    plans = plan_deck(deck, strict=True).by_surface_id()
    assert "cap-combo" in plans and "dep-combo" in plans
    assert plans["cap-combo"].chart_paint["chart_type"] == "combo"
    assert plans["dep-combo"].chart_paint["bar_mode"] == "stacked"


def test_render_emits_chartjs_svg_table(tmp_path: Path):
    out = tmp_path / "out"
    result = render_deck(COMBO, out, strict=True)
    assert result["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-chart-type="combo"' in html
    assert 'data-chart-surface="cap-combo"' in html
    assert 'data-chart-surface="dep-combo"' in html
    assert "chartjs-canvas" in html
    assert "chart-svg" in html
    assert 'data-semantic-table="1"' in html
    assert "Buybacks" in html and "ROE" in html
    assert "Retail" in html and "Retail share" in html
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    readiness = meta.get("static_readiness") or []
    combo_ready = [r for r in readiness if r.get("slide_number") in (2, 3)]
    assert combo_ready
    assert all("chartjs" in (r.get("chart_painters") or []) for r in combo_ready)
    assert all(r.get("semantic_table_present") for r in combo_ready)


def test_svg_bars_behind_lines_and_table():
    deck = validate_handoff(_s(), strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["cap-combo"].chart_paint
    svg = paint_chart_svg(cp)
    assert 'class="bar"' in svg
    assert "combo-line" in svg or "polyline" in svg
    # bars appear before line polylines in SVG source (paint order).
    bar_i = svg.find('class="bar"')
    line_i = svg.find("polyline")
    assert bar_i != -1 and line_i != -1 and bar_i < line_i
    table = paint_semantic_table(cp)
    assert "Buybacks" in table and "ROE" in table and "Q1" in table
    assert MISSING_VISIBLE in table  # null dividend@q4


def test_chartjs_combo_config_order_and_axes():
    from impact_slides.renderer_v3.charts import _chartjs_combo_config

    deck = validate_handoff(_s(), strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["cap-combo"].chart_paint
    cfg = _chartjs_combo_config(cp)
    assert cfg["type"] == "bar"
    datasets = cfg["data"]["datasets"]
    assert [d["type"] for d in datasets] == ["bar", "bar", "line"]
    assert datasets[0].get("stack") is None
    assert datasets[2]["yAxisID"] == "y1"
    assert "y1" in cfg["options"]["scales"]
    assert cfg["v3"]["bar_mode"] == "grouped"

    scp = plan_deck(deck, strict=True).by_surface_id()["dep-combo"].chart_paint
    scfg = _chartjs_combo_config(scp)
    bar_ds = [d for d in scfg["data"]["datasets"] if d["type"] == "bar"]
    assert all(d.get("stack") == "combo" for d in bar_ds)
    assert scfg["options"]["scales"]["y"]["stacked"] is True
    line_ds = [d for d in scfg["data"]["datasets"] if d["type"] == "line"]
    assert line_ds and line_ds[0]["yAxisID"] == "y"


def test_mutation_flip_bar_mode_changes_geometry():
    """Discriminating probe: grouped vs stacked bar x positions differ."""
    deck = validate_handoff(_s(), strict=True).deck
    g = freeze_combo_chart(deck.slides[1].payload.primary_visual, deck.number_formats)
    # Mutate model to stacked on same data (rebuild via handoff).
    raw = _s()
    vis = _vis(raw)
    vis["bar_mode"] = "stacked"
    # Secondary lines + stacked bars still valid; drop ordinary stack conflict none.
    # Stacked forbids ordinary bar labels via display stack policies only.
    del vis["display"]
    vis["display"] = {"series_identity": "legend", "stack_totals": "show"}
    # Remove groups optional OK.
    deck2 = validate_handoff(raw, strict=True).deck
    s = freeze_combo_chart(deck2.slides[1].payload.primary_visual, deck2.number_formats)
    g_bars = [b for b in g["bars"] if b["series_id"] == "buybacks" and b["category_id"] == "q1"]
    s_bars = [b for b in s["bars"] if b["series_id"] == "buybacks" and b["category_id"] == "q1"]
    assert g_bars and s_bars
    # Grouped uses multi-series slot origins; stacked uses single cluster x.
    assert g["geometry"]["stacked"] is False and s["geometry"]["stacked"] is True
    # Two bar series at q1: grouped have different x; stacked share x.
    g_q1 = sorted(
        (b["x"] for b in g["bars"] if b["category_id"] == "q1" and b.get("finite")),
    )
    s_q1 = sorted(
        (b["x"] for b in s["bars"] if b["category_id"] == "q1" and b.get("finite")),
    )
    assert len(set(round(x, 1) for x in g_q1)) >= 2
    assert len(set(round(x, 1) for x in s_q1)) == 1
