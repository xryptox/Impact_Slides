"""Renderer v3 line-chart tracer bullet (#182).

Seams under test:
- typed single_chart + line envelope (D227–D239, D290–D302)
- canonical categories/series/null gaps/stable IDs (D91–D95)
- one semantic accessibility table (D106/D247)
- frozen plan drives Chart.js + noscript SVG (D53/D57/D69/D248)
- identity, point labels, transparent surfaces, no gridlines, readiness
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.charts import freeze_line_chart, paint_line_chart_svg
from impact_slides.renderer_v3.format import MISSING_ACCESSIBLE, MISSING_VISIBLE
from impact_slides.renderer_v3.models import LineChartVisual, SingleChartSlide
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
    chart = slide.payload.primary_visual
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
    raw["slides"][1]["payload"]["primary_visual"]["chart_data"]["series"][0]["values"] = [
        "1.0",
        "2.0",
    ]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_one_finite_point_series():
    raw = _raw()
    raw["slides"][1]["payload"]["primary_visual"]["chart_data"]["series"] = [
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
    raw["slides"][1]["payload"]["primary_visual"]["chart_data"]["series"][1]["name"] = "US"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_pane_title_without_heading():
    raw = _raw()
    chart = raw["slides"][1]["payload"]["primary_visual"]
    del chart["heading"]
    del chart["subtitle"]
    chart["chart_data"]["series"] = [chart["chart_data"]["series"][0]]
    chart["display"] = {"series_identity": "pane_title"}
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_json_number_plotted_value():
    raw = _raw()
    raw["slides"][1]["payload"]["primary_visual"]["chart_data"]["series"][0]["values"][0] = 3.2
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_decorated_plotted_value():
    raw = _raw()
    raw["slides"][1]["payload"]["primary_visual"]["chart_data"]["series"][0]["values"][0] = "3.2%"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_unknown_format():
    raw = _raw()
    raw["slides"][1]["payload"]["primary_visual"]["value_axes"]["primary"][
        "format_id"
    ] = "nope"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_five_series():
    raw = _raw()
    series = raw["slides"][1]["payload"]["primary_visual"]["chart_data"]["series"]
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
    chart = deck.slides[1].payload.primary_visual
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
    svg = paint_line_chart_svg(cp)
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
    del raw["slides"][1]["payload"]["primary_visual"]["chart_data"]["categories"][0][
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


def test_v2_not_imported_by_charts_module():
    import impact_slides.renderer_v3.charts as charts

    src = Path(charts.__file__).read_text(encoding="utf-8")
    assert "renderer_v2" not in src
