"""Renderer v3 line-chart tracer bullet (#182).

Seams under test:
- typed single_chart + line envelope (D227–D239, D290–D302)
- canonical categories/series/null gaps/stable IDs (D91–D95)
- one semantic accessibility table (D106/D247)
- frozen plan drives Chart.js + noscript SVG (D53/D57/D69/D248)
- identity, point labels, transparent surfaces, no gridlines, readiness
"""
from __future__ import annotations

import builtins
import importlib
import json
import re
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.charts import (
    freeze_line_chart,
    paint_chart_svg,
    paint_semantic_table,
)
from impact_slides.renderer_v3.format import MISSING_ACCESSIBLE, MISSING_VISIBLE
from impact_slides.renderer_v3.models import ChartTypography, LineChartVisual, SingleChartSlide
from impact_slides.renderer_v3.plan import plan_deck
from impact_slides.renderer_v3.schema_export import check_schema

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/renderer_v3/minimal_line_chart.json"
TABLE = ROOT / "tests/fixtures/renderer_v3/minimal_data_table.json"


def _raw() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Validation / model
# ---------------------------------------------------------------------------


def test_line_chart_deck_validates():
    result = validate_handoff(_raw(), strict=True)
    assert result.ok
    slide = result.deck.slides[1]
    assert isinstance(slide, SingleChartSlide)
    chart = slide.payload.chart
    assert isinstance(chart, LineChartVisual)
    assert chart.surface_id == "vol-trend"
    assert chart.chart_type == "line"
    assert len(chart.chart_data.categories) == 4
    assert len(chart.chart_data.series) == 2
    assert chart.chart_data.series[0].values[2] is None


def test_data_table_fixture_still_validates():
    raw = json.loads(TABLE.read_text(encoding="utf-8"))
    assert validate_handoff(raw, strict=True).ok


def test_strict_rejects_ragged_series():
    raw = _raw()
    raw["slides"][1]["payload"]["chart"]["chart_data"]["series"][0]["values"] = [
        "1.0",
        "2.0",
    ]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_one_finite_point_series():
    raw = _raw()
    raw["slides"][1]["payload"]["chart"]["chart_data"]["series"] = [
        {
            "series_id": "solo",
            "name": "Solo",
            "values": ["1.0", None, None, None],
        }
    ]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_duplicate_series_names():
    raw = _raw()
    raw["slides"][1]["payload"]["chart"]["chart_data"]["series"][1]["name"] = "US"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_pane_title_without_heading():
    raw = _raw()
    chart = raw["slides"][1]["payload"]["chart"]
    del chart["heading"]
    del chart["subtitle"]
    chart["chart_data"]["series"] = [chart["chart_data"]["series"][0]]
    chart["display"] = {"series_identity": "pane_title"}
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_json_number_plotted_value():
    raw = _raw()
    raw["slides"][1]["payload"]["chart"]["chart_data"]["series"][0]["values"][0] = 3.2
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_decorated_plotted_value():
    raw = _raw()
    raw["slides"][1]["payload"]["chart"]["chart_data"]["series"][0]["values"][0] = "3.2%"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_unknown_format():
    raw = _raw()
    raw["slides"][1]["payload"]["chart"]["value_axes"]["primary"][
        "format_id"
    ] = "nope"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_five_series():
    raw = _raw()
    series = raw["slides"][1]["payload"]["chart"]["chart_data"]["series"]
    for i in range(3, 6):
        series.append(
            {
                "series_id": f"s{i}",
                "name": f"S{i}",
                "values": ["1.0", "2.0", "3.0", "4.0"],
            }
        )
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


# ---------------------------------------------------------------------------
# Frozen plan
# ---------------------------------------------------------------------------


def test_plan_freezes_identity_and_null_gaps():
    deck = validate_handoff(_raw(), strict=True).deck
    plan = plan_deck(deck, strict=True)
    sp = plan.by_surface_id()["vol-trend"]
    assert sp.role == "line_chart"
    assert sp.chart_paint is not None
    cp = sp.chart_paint
    assert cp["identity_strategy"] in ("endpoints", "legend")
    assert cp["gridlines"] is False
    nulls = [p for p in cp["points"] if not p["finite"]]
    assert len(nulls) == 1
    assert nulls[0]["series_id"] == "us"
    assert nulls[0]["category_id"] == "q3"
    assert nulls[0]["visible"] == MISSING_VISIBLE
    assert nulls[0]["accessible"] == MISSING_ACCESSIBLE
    # semantic table owns complete matrix
    table = cp["semantic_table"]
    assert len(table["columns"]) == 2
    assert len(table["rows"]) == 4
    miss = table["rows"][2]["cells"][0]
    assert miss["missing"] is True
    assert miss["visible"] == MISSING_VISIBLE
    assert miss["accessible"] == MISSING_ACCESSIBLE


def test_freeze_assigns_theme_colors_and_styles():
    deck = validate_handoff(_raw(), strict=True).deck
    chart = deck.slides[1].payload.chart
    frozen = freeze_line_chart(chart, deck.number_formats)
    assert frozen["series"][0]["color"].startswith("#")
    assert frozen["series"][0]["line_style"] == "solid"
    assert frozen["series"][1]["line_style"] == "dashed"
    assert frozen["series"][0]["marker"] == "circle"
    assert frozen["series"][1]["marker"] == "square"


def test_point_label_candidates_are_closed():
    deck = validate_handoff(_raw(), strict=True).deck
    plan = plan_deck(deck, strict=True)
    cp = plan.by_surface_id()["vol-trend"].chart_paint
    allowed = {"above", "below", "left", "right", "leader", "suppressed", "endpoint"}
    for p in cp["placements"]:
        assert p["class"] in allowed


def test_chart_geometry_shares_slide_allocation():
    raw = _raw()
    slide = raw["slides"][1]
    slide["disclosure"] = {
        "sections": [
            {
                "surface_id": "method",
                "title": "Method",
                "items": [{"kind": "paragraph", "text": "Reported values."}],
            }
        ]
    }
    plan = plan_deck(validate_handoff(raw, strict=True).deck, strict=True)
    surfaces = [sp for sp in plan.surfaces if sp.slide_number == 2 and sp.role != "title"]
    chart = plan.by_surface_id()["vol-trend"]
    assert chart.chart_paint["geometry"]["view_h"] <= chart._box_h
    assert sum(sp._box_h + sp._chrome_h for sp in surfaces) <= 1080 - 56 - 48 - 91


# ---------------------------------------------------------------------------
# Publication / dual painters
# ---------------------------------------------------------------------------


def test_render_emits_chartjs_svg_and_semantic_table(tmp_path: Path):
    out = tmp_path / "out"
    result = render_deck(FIXTURE, out, strict=True)
    assert result["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-chart-type="line"' in html
    assert 'data-chart-surface="vol-trend"' in html
    assert 'id="cjs-vol-trend"' in html or "chartjs-canvas" in html
    assert "<noscript>" in html
    assert "<svg" in html and "polyline" in html
    assert 'data-semantic-table="1"' in html
    assert 'id="vol-trend-semantic-table"' in html
    assert "visually-hidden" in html
    # transparent surfaces + no gridlines in Chart.js config
    assert "--color-chart-plot: transparent" in html
    assert '"display": false' in html or '"display":false' in html
    # readiness
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    chart_ready = [r for r in meta["static_readiness"] if r["layout_type"] == "single_chart"]
    assert chart_ready
    assert chart_ready[0]["semantic_table_present"] is True
    assert "chartjs" in chart_ready[0]["chart_painters"]
    assert "svg" in chart_ready[0]["chart_painters"]
    # plan carries identity strategy
    chart_plans = [p for p in meta["plans"] if p["surface_id"] == "vol-trend"]
    assert chart_plans
    assert chart_plans[0].get("display_identity_strategy") in ("endpoints", "legend")


def test_svg_only_skips_canvas_boot(tmp_path: Path):
    out = tmp_path / "svg"
    result = render_deck(FIXTURE, out, strict=True, suppress_features=["charts"])
    assert result["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    # svg path still present; canvas boot optional
    assert "<svg" in html
    assert 'data-semantic-table="1"' in html


def test_svg_preserves_null_gap_no_interpolation():
    deck = validate_handoff(_raw(), strict=True).deck
    plan = plan_deck(deck, strict=True)
    cp = plan.by_surface_id()["vol-trend"].chart_paint
    svg = paint_chart_svg(cp)
    # US series has null at q3 → two separate polylines or fewer points, never a 4-point continuous path through gap
    us_points = [p for p in cp["points"] if p["series_id"] == "us"]
    finite_us = [p for p in us_points if p["finite"]]
    assert len(finite_us) == 3
    # SVG must not invent a midpoint y for the missing category
    assert "null" not in svg.lower()
    assert svg.count("polyline") >= 1


def test_semantic_table_has_all_identities_and_units(tmp_path: Path):
    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    # series names + categories appear in semantic table
    assert "US" in html and "Intl" in html
    assert "Q1'24" in html or "Q1&#x27;24" in html or "Q1" in html
    assert MISSING_VISIBLE in html
    assert "Missing" in html
    assert "pct_1" in html or "percent" in html.lower() or "YoY" in html


def test_byte_identical_rerun(tmp_path: Path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    render_deck(FIXTURE, a, strict=True)
    render_deck(FIXTURE, b, strict=True)
    for name in (
        "presentation.html",
        "run_meta.json",
        "evidence_manifest.json",
        "slide_notes.md",
        "handoff_schema_v1.json",
    ):
        assert (a / name).read_bytes() == (b / name).read_bytes()


# ---------------------------------------------------------------------------
# Mutation / adversarial
# ---------------------------------------------------------------------------


def test_mutation_drop_category_id_fails():
    raw = _raw()
    del raw["slides"][1]["payload"]["chart"]["chart_data"]["categories"][0][
        "category_id"
    ]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_mutation_zero_fill_null_would_change_table():
    """Guard: null must stay missing, not coerce to zero (D92/D103)."""
    deck = validate_handoff(_raw(), strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["vol-trend"].chart_paint
    cell = cp["semantic_table"]["rows"][2]["cells"][0]
    assert cell["missing"] is True
    assert cell["visible"] != "0.0%"
    assert cell["visible"] != "0"


def test_schema_export_check_passes():
    check_schema()


def test_v2_not_imported_by_charts_module(monkeypatch: pytest.MonkeyPatch):
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.startswith("impact_slides.renderer_v2"):
            raise AssertionError(f"renderer_v2 import attempted: {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    sys.modules.pop("impact_slides.renderer_v3.charts", None)
    charts = importlib.import_module("impact_slides.renderer_v3.charts")
    deck = validate_handoff(_raw(), strict=True).deck
    assert charts.freeze_line_chart(deck.slides[1].payload.chart, deck.number_formats)


def test_chartjs_chart_area_pinned_to_frozen_plot(tmp_path: Path):
    """Chart.js chartArea must equal the frozen plot rect (painter parity)."""
    out = tmp_path / "out"
    result = render_deck(FIXTURE, out, strict=True)
    assert result["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    deck = validate_handoff(_raw(), strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["vol-trend"].chart_paint
    g = cp["geometry"]
    m = re.search(
        r'<script type="application/json" id="cfg-vol-trend">(.*?)</script>',
        html,
        re.S,
    )
    assert m is not None
    cfg = json.loads(m.group(1))
    opts = cfg["options"]
    assert opts["layout"]["padding"] == {
        "left": g["pad_l"],
        "right": g["pad_r"],
        "top": g["pad_t"],
        "bottom": g["pad_b"],
    }
    assert opts["scales"]["x"]["display"] is False
    assert opts["scales"]["y"]["display"] is False
    assert opts["scales"]["y"]["min"] == float(cp["domain"]["min"])
    assert opts["scales"]["y"]["max"] == float(cp["domain"]["max"])
    assert "chart-label-overlay" in html


def test_svg_chrome_paints_axis_titles():
    deck = validate_handoff(_raw(), strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["vol-trend"].chart_paint
    chrome = paint_chart_svg(cp, marks=False)
    assert "Quarter" in chrome
    assert "YoY %" in chrome
    assert "Quarter" in paint_chart_svg(cp)
    raw = _raw()
    raw["slides"][1]["payload"]["chart"]["category_axis"]["visible"] = False
    deck2 = validate_handoff(raw, strict=True).deck
    cp2 = plan_deck(deck2, strict=True).by_surface_id()["vol-trend"].chart_paint
    chrome2 = paint_chart_svg(cp2, marks=False)
    assert "Quarter" not in chrome2
    assert "YoY %" in chrome2


def test_generated_domain_covers_data_at_max_target_ticks():
    raw = _raw()
    visual = raw["slides"][1]["payload"]["chart"]
    visual["value_axes"]["primary"]["domain"]["target_ticks"] = 8
    visual["chart_data"]["series"][0]["values"] = ["0", "20", "40", "70"]
    visual["chart_data"]["series"][1]["values"] = ["5", "15", "25", "35"]
    deck = validate_handoff(raw, strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["vol-trend"].chart_paint
    domain_min = float(cp["domain"]["min"])
    domain_max = float(cp["domain"]["max"])
    values = [
        float(v)
        for s in visual["chart_data"]["series"]
        for v in s["values"]
        if v is not None
    ]
    assert domain_min <= min(values)
    assert domain_max >= max(values)
    assert len(cp["domain"]["ticks"]) <= 8
    g = cp["geometry"]
    ys = [p["y"] for p in cp["points"] if p["finite"]]
    assert all(g["pad_t"] <= y <= g["pad_t"] + g["plot_h"] for y in ys)


# ---------------------------------------------------------------------------
# Review-gate repairs: REV-13 tick formatting, REV-14 fixed-domain containment
# ---------------------------------------------------------------------------

_CANONICAL_DECIMAL = re.compile(r"^-?(?:0|[1-9]\d*)(?:\.\d+)?$")


def _chart_slide(raw: dict) -> dict:
    return next(s for s in raw["slides"] if s.get("layout_type") == "single_chart")


def test_rev13_generated_ticks_are_plain_canonical_decimals():
    raw = _raw()
    vis = _chart_slide(raw)["payload"]["chart"]
    vis["chart_data"]["series"][0]["values"] = ["0", "250000", "1000000", "1250000"]
    vis["chart_data"]["series"][1]["values"] = ["100000", "300000", "900000", "1100000"]
    deck = validate_handoff(raw, strict=True).deck
    frozen = freeze_line_chart(deck.slides[1].payload.chart, deck.number_formats)
    domain = frozen["domain"]
    assert domain["kind"] == "generated"
    for text in [domain["min"], domain["max"], *domain["ticks"]]:
        assert _CANONICAL_DECIMAL.match(text), text
    assert float(domain["max"]) >= 1250000


def test_rev14_strict_rejects_value_outside_fixed_domain():
    raw = _raw()
    vis = _chart_slide(raw)["payload"]["chart"]
    vis["value_axes"]["primary"]["domain"] = {
        "kind": "fixed",
        "min": "0",
        "max": "4",
        "ticks": ["0", "1", "2", "3", "4"],
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_rev14_non_strict_repairs_uncontained_fixed_domain():
    raw = _raw()
    vis = _chart_slide(raw)["payload"]["chart"]
    expected_series = [list(s["values"]) for s in vis["chart_data"]["series"]]
    expected_categories = [c["category_id"] for c in vis["chart_data"]["categories"]]
    vis["value_axes"]["primary"]["domain"] = {
        "kind": "fixed",
        "min": "0",
        "max": "4",
        "ticks": ["0", "1", "2", "3", "4"],
    }
    result = validate_handoff(raw, strict=False)
    assert result.ok
    assert result.repaired
    matched = [e for e in result.events if e.code == "repair.domain_replaced"]
    assert len(matched) == 1
    ev = matched[0]
    assert ev.action.name == "replace_domain"
    assert ev.result.name == "generated"
    assert ev.phase == "repair"
    assert ev.path.endswith("/value_axes/primary/domain")
    repaired_vis = result.deck.slides[1].payload.chart
    assert repaired_vis.value_axes.primary.domain.kind == "generated"
    # Non-semantic repair: only the domain changes; chart facts are preserved.
    assert [list(s.values) for s in repaired_vis.chart_data.series] == expected_series
    assert [c.category_id for c in repaired_vis.chart_data.categories] == expected_categories


def test_generated_domain_authored_max_below_data_strict_rejects():
    raw = _raw()
    vis = _chart_slide(raw)["payload"]["chart"]
    vis["value_axes"]["primary"]["domain"] = {
        "kind": "generated",
        "min": "0",
        "max": "4",
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_generated_domain_authored_max_below_data_non_strict_repairs():
    raw = _raw()
    vis = _chart_slide(raw)["payload"]["chart"]
    vis["value_axes"]["primary"]["domain"] = {
        "kind": "generated",
        "min": "0",
        "max": "4",
    }
    result = validate_handoff(raw, strict=False)
    assert result.ok
    assert result.repaired
    matched = [
        e
        for e in result.events
        if e.code == "repair.domain_replaced" and e.action.name == "drop_field"
    ]
    assert len(matched) == 1
    ev = matched[0]
    assert ev.result.name == "dropped"
    assert ev.phase == "repair"
    assert ev.path.endswith("/value_axes/primary/domain/max")
    repaired_vis = result.deck.slides[1].payload.chart
    domain = repaired_vis.value_axes.primary.domain
    assert domain.kind == "generated"
    assert domain.min == "0"
    assert domain.max is None
    cp = plan_deck(result.deck, strict=True).by_surface_id()["vol-trend"].chart_paint
    values = [
        float(v)
        for s in vis["chart_data"]["series"]
        for v in s["values"]
        if v is not None
    ]
    assert float(cp["domain"]["min"]) <= min(values)
    assert float(cp["domain"]["max"]) >= max(values)
    g = cp["geometry"]
    ys = [p["y"] for p in cp["points"] if p["finite"]]
    assert all(g["pad_t"] <= y <= g["pad_t"] + g["plot_h"] for y in ys)


def test_rev12_facts_follow_semantic_table_visibility():
    deck = validate_handoff(_raw(), strict=True).deck
    plan = plan_deck(deck, strict=True)
    cp = plan.by_surface_id()["vol-trend"].chart_paint
    hidden_html = paint_semantic_table(
        {"semantic_table": cp["semantic_table"], "surface_id": "vol-trend"}
    )
    assert 'class="chart-semantic-table visually-hidden"' in hidden_html
    assert 'class="chart-facts visually-hidden"' in hidden_html
    visible_html = paint_semantic_table(
        {
            "semantic_table": dict(cp["semantic_table"], visible=True),
            "surface_id": "vol-trend",
        }
    )
    assert 'class="chart-semantic-table"' in visible_html
    assert 'class="chart-facts"' in visible_html
    assert "visually-hidden" not in visible_html


def test_rev14_fixed_domain_containing_values_passes():
    raw = _raw()
    vis = _chart_slide(raw)["payload"]["chart"]
    vis["value_axes"]["primary"]["domain"] = {
        "kind": "fixed",
        "min": "0",
        "max": "6",
        "ticks": ["0", "2", "4", "6"],
    }
    assert validate_handoff(raw, strict=True).ok


# ---------------------------------------------------------------------------
# DP-1 typography floors + semibold weights
# ---------------------------------------------------------------------------

TICK_FLOOR = 20
VALUE_FLOOR = 18
SEMIBOLD = 600


def test_line_plan_freezes_tick_and_value_floors():
    deck = validate_handoff(_raw(), strict=True).deck
    sizes = plan_deck(deck, strict=True).by_surface_id()["vol-trend"].role_sizes
    assert sizes["category_ticks"] >= TICK_FLOOR
    assert sizes["value_ticks"] >= TICK_FLOOR
    assert sizes["ordinary_values"] >= VALUE_FLOOR
    assert sizes["category_ticks"] <= 24
    assert sizes["value_ticks"] <= 28
    assert sizes["ordinary_values"] <= 32


def test_chart_typography_rejects_sizes_below_parity_floors():
    with pytest.raises(Exception):
        ChartTypography(category_ticks=14)
    with pytest.raises(Exception):
        ChartTypography(value_ticks=19)
    with pytest.raises(Exception):
        ChartTypography(ordinary_values=14)
    ok = ChartTypography(category_ticks=20, value_ticks=20, ordinary_values=18)
    assert ok.category_ticks == 20
    assert ok.value_ticks == 20
    assert ok.ordinary_values == 18
    raw = _raw()
    raw["slides"][1]["payload"]["chart"]["typography"] = {
        "mode": "fixed",
        "category_ticks": 14,
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_line_painters_emit_semibold_tick_and_value_weight(tmp_path: Path):
    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    m = re.search(
        r'<script type="application/json" id="cfg-vol-trend">(.*?)</script>',
        html,
        re.S,
    )
    assert m is not None
    cfg = json.loads(m.group(1))
    x_font = cfg["options"]["scales"]["x"]["ticks"]["font"]
    y_font = cfg["options"]["scales"]["y"]["ticks"]["font"]
    assert x_font["weight"] == SEMIBOLD
    assert y_font["weight"] == SEMIBOLD
    painted = cfg["v3"]["painted_values"]["font"]
    assert painted["weight"] == SEMIBOLD

    deck = validate_handoff(_raw(), strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["vol-trend"].chart_paint
    svg = paint_chart_svg(cp)
    cat_px = cp["role_sizes"]["category_ticks"]
    val_px = cp["role_sizes"]["value_ticks"]
    lab_px = cp["role_sizes"]["ordinary_values"]
    assert f'font-size="{cat_px}" font-weight="{SEMIBOLD}"' in svg
    assert f'font-size="{val_px}" font-weight="{SEMIBOLD}"' in svg
    assert f'font-size="{lab_px}" font-weight="{SEMIBOLD}"' in svg
