"""Renderer v3 explicit arithmetic waterfall charts (#186).

Seams under test:
- typed single_chart waterfall steps (D162/D245/D307)
- total resets level; computed_total paints known level; change bridges
- structural labels/connectors/semantic-table facts retained
- Chart.js floating-bar / SVG geometry parity within 2px (D160/D248)
- malformed sequence strict-fails; no role inference
"""
from __future__ import annotations

import builtins
import importlib
import json
import re
import sys
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.charts import (
    freeze_waterfall_chart,
    paint_chart_svg,
    paint_semantic_table,
)
from impact_slides.renderer_v3.models import SingleChartSlide, WaterfallChartVisual
from impact_slides.renderer_v3.plan import plan_deck
from impact_slides.renderer_v3.schema_export import check_schema

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / "tests/fixtures/renderer_v3/minimal_waterfall.json"


def _w() -> dict:
    return json.loads(WF.read_text(encoding="utf-8"))


def _chart_slide(raw: dict) -> dict:
    return next(s for s in raw["slides"] if s.get("layout_type") == "single_chart")


def _contracts(excinfo: pytest.ExceptionInfo) -> list[str]:
    return [
        ev.expected.contract
        for ev in excinfo.value.events
        if ev.expected is not None and ev.expected.contract
    ]


# ---------------------------------------------------------------------------
# Validation / model
# ---------------------------------------------------------------------------


def test_waterfall_deck_validates():
    result = validate_handoff(_w(), strict=True)
    assert result.ok
    slide = result.deck.slides[1]
    assert isinstance(slide, SingleChartSlide)
    chart = slide.payload.primary_visual
    assert isinstance(chart, WaterfallChartVisual)
    assert chart.chart_type == "waterfall"
    steps = chart.waterfall_data.steps
    assert len(steps) == 6
    assert steps[0].role == "total" and steps[0].value == "100"
    assert steps[-1].role == "computed_total" and steps[-1].value is None
    assert steps[1].role == "change" and steps[1].value == "20"


def test_strict_rejects_first_not_total():
    raw = _w()
    steps = _chart_slide(raw)["payload"]["primary_visual"]["waterfall_data"]["steps"]
    steps[0]["role"] = "change"
    with pytest.raises(RendererValidationError) as excinfo:
        validate_handoff(raw, strict=True)
    assert any("first" in c.lower() for c in _contracts(excinfo))


def test_strict_rejects_last_change():
    raw = _w()
    steps = _chart_slide(raw)["payload"]["primary_visual"]["waterfall_data"]["steps"]
    steps[-1] = {
        "category_id": "close",
        "label": "Closing",
        "role": "change",
        "value": "1",
    }
    with pytest.raises(RendererValidationError) as excinfo:
        validate_handoff(raw, strict=True)
    assert any("last" in c.lower() for c in _contracts(excinfo))


def test_strict_rejects_computed_total_with_value():
    raw = _w()
    steps = _chart_slide(raw)["payload"]["primary_visual"]["waterfall_data"]["steps"]
    steps[-1]["value"] = "120"
    with pytest.raises(RendererValidationError) as excinfo:
        validate_handoff(raw, strict=True)
    assert any("computed_total" in c for c in _contracts(excinfo))


def test_strict_rejects_change_without_value():
    raw = _w()
    steps = _chart_slide(raw)["payload"]["primary_visual"]["waterfall_data"]["steps"]
    del steps[1]["value"]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_chart_data_field():
    raw = _w()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    vis["chart_data"] = {
        "categories": [{"category_id": "a", "label": "A"}],
        "series": [{"series_id": "s", "name": "S", "values": ["1"]}],
    }
    with pytest.raises(RendererValidationError) as excinfo:
        validate_handoff(raw, strict=True)
    assert any("chart_data" in c for c in _contracts(excinfo))


def test_strict_rejects_display_field():
    raw = _w()
    _chart_slide(raw)["payload"]["primary_visual"]["display"] = {
        "ordinary_values": "hide"
    }
    with pytest.raises(RendererValidationError) as excinfo:
        validate_handoff(raw, strict=True)
    assert any("display" in c for c in _contracts(excinfo))


def test_strict_rejects_leading_break():
    raw = _w()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    vis["value_axes"]["primary"]["domain"] = {
        "kind": "generated",
        "min": "0",
        "target_ticks": 5,
    }
    vis["value_axes"]["primary"]["leading_break"] = {"to": "10"}
    with pytest.raises(RendererValidationError) as excinfo:
        validate_handoff(raw, strict=True)
    assert any("leading_break" in c for c in _contracts(excinfo))


def test_strict_rejects_duplicate_category_ids():
    raw = _w()
    steps = _chart_slide(raw)["payload"]["primary_visual"]["waterfall_data"]["steps"]
    steps[2]["category_id"] = steps[1]["category_id"]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_domain_excluding_level():
    raw = _w()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    vis["value_axes"]["primary"]["domain"] = {
        "kind": "fixed",
        "min": "0",
        "max": "50",
        "ticks": ["0", "25", "50"],
    }
    with pytest.raises(RendererValidationError) as excinfo:
        validate_handoff(raw, strict=True)
    assert any("level" in c.lower() or "domain" in c.lower() for c in _contracts(excinfo))


# ---------------------------------------------------------------------------
# Arithmetic / freeze
# ---------------------------------------------------------------------------


def test_total_resets_and_computed_follows_level():
    deck = validate_handoff(_w(), strict=True).deck
    chart = deck.slides[1].payload.primary_visual
    cp = freeze_waterfall_chart(chart, deck.number_formats)
    by_id = {s["category_id"]: s for s in cp["steps"]}
    assert by_id["open"]["level"] == Decimal("100")
    assert by_id["price"]["level"] == Decimal("120")
    assert by_id["volume"]["level"] == Decimal("110")
    # Mid-year authored total 115 resets (does not need to equal prior 110).
    assert by_id["mid"]["level"] == Decimal("115")
    assert by_id["mid"]["role"] == "total"
    assert by_id["fx"]["level"] == Decimal("120")
    assert by_id["close"]["role"] == "computed_total"
    assert by_id["close"]["level"] == Decimal("120")
    assert by_id["close"]["authored_value"] is None
    # Change y0/y1 bridge from prior level.
    assert float(by_id["price"]["y0"]) == 100.0
    assert float(by_id["price"]["y1"]) == 120.0
    assert float(by_id["volume"]["y0"]) == 120.0
    assert float(by_id["volume"]["y1"]) == 110.0
    # Totals paint from zero.
    assert float(by_id["open"]["y0"]) == 0.0
    assert float(by_id["close"]["y0"]) == 0.0


def test_zero_change_is_real_not_computed():
    raw = _w()
    steps = _chart_slide(raw)["payload"]["primary_visual"]["waterfall_data"]["steps"]
    steps[1]["value"] = "0"
    deck = validate_handoff(raw, strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["rev-bridge"].chart_paint
    price = next(s for s in cp["steps"] if s["category_id"] == "price")
    assert price["role"] == "change"
    assert float(price["display_numeric"]) == 0.0
    assert price["color_role"] == "increase"  # zero change uses increase chrome


def test_structural_labels_and_connectors_present():
    deck = validate_handoff(_w(), strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["rev-bridge"].chart_paint
    places = [p for p in cp["placements"] if p.get("kind") == "structural"]
    assert len(places) == 6
    assert all(p["class"] != "suppressed" for p in places)
    # Connectors only into change steps (not into totals).
    to_ids = {c["to_category_id"] for c in cp["connectors"]}
    assert to_ids == {"price", "volume", "fx"}
    assert "mid" not in to_ids and "close" not in to_ids


def test_semantic_table_records_role_value_level():
    deck = validate_handoff(_w(), strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["rev-bridge"].chart_paint
    table = cp["semantic_table"]
    assert [c["label"] for c in table["columns"]] == [
        "Role",
        "Value",
        "Running level",
    ]
    rows = {r["category_id"]: r for r in table["rows"]}
    assert rows["open"]["cells"][0]["visible"] == "Total"
    assert rows["price"]["cells"][0]["visible"] == "Change"
    assert rows["close"]["cells"][0]["visible"] == "Computed total"
    assert "waterfall" in " ".join(table["facts"]).lower()
    html = paint_semantic_table(cp)
    assert "rev-bridge-semantic-table" in html
    assert "Computed total" in html


def test_role_colors_theme_owned():
    deck = validate_handoff(_w(), strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["rev-bridge"].chart_paint
    by_id = {b["category_id"]: b for b in cp["bars"]}
    assert by_id["open"]["color_role"] == "total"
    assert by_id["price"]["color_role"] == "increase"
    assert by_id["volume"]["color_role"] == "decrease"
    assert by_id["close"]["color_role"] == "computed_total"
    # Navy totals, blue increase, neutral decrease — distinct hex.
    assert by_id["open"]["color"] != by_id["price"]["color"]
    assert by_id["price"]["color"] != by_id["volume"]["color"]


# ---------------------------------------------------------------------------
# Paint / parity
# ---------------------------------------------------------------------------


def test_render_waterfall_html(tmp_path: Path):
    out = tmp_path / "out"
    result = render_deck(WF, out, strict=True)
    assert result["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-chart-type="waterfall"' in html
    assert "rev-bridge-semantic-table" in html
    # Settled Chart.js path overlays connectors/labels outside <noscript> (D245/D248).
    before_noscript = html.split("<noscript>", 1)[0]
    assert "waterfall-connector" in before_noscript
    assert "waterfall-value" in before_noscript
    assert "zero-line" in before_noscript  # semantic zero even for all-positive
    m = re.search(
        r'<script type="application/json" id="cfg-rev-bridge">(.*?)</script>',
        html,
        re.S,
    )
    assert m is not None
    cfg = json.loads(m.group(1))
    assert cfg["type"] == "bar"
    assert cfg["v3"]["chart_type"] == "waterfall"
    # Floating [y0, y1] pairs
    data = cfg["data"]["datasets"][0]["data"]
    assert data[0] == [0.0, 100.0]
    assert data[1] == [100.0, 120.0]
    assert data[2] == [120.0, 110.0]
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    chart_ready = [
        r
        for r in meta.get("static_readiness", meta.get("readiness", []))
        if r.get("layout_type") == "single_chart"
    ]
    if not chart_ready:
        plans = meta.get("plans") or []
        assert any(p.get("chart_type") == "waterfall" for p in plans)
    else:
        assert "chartjs" in chart_ready[0]["chart_painters"]
        assert "svg" in chart_ready[0]["chart_painters"]


def test_computed_total_stays_decimal_safe():
    raw = _w()
    steps = _chart_slide(raw)["payload"]["primary_visual"]["waterfall_data"]["steps"]
    steps[0]["value"] = "10.1"
    steps[1]["value"] = "0.2"
    steps[2]["value"] = "0.3"
    steps[3]["value"] = "10.6"  # authored reset
    steps[4]["value"] = "0.05"
    # last is computed_total of 10.65
    deck = validate_handoff(raw, strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["rev-bridge"].chart_paint
    close = next(s for s in cp["steps"] if s["category_id"] == "close")
    assert close["display_value"] == "10.65"
    assert Decimal(close["display_value"]) == Decimal("10.65")


def test_svg_geometry_matches_frozen_plan():
    deck = validate_handoff(_w(), strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["rev-bridge"].chart_paint
    svg = paint_chart_svg(cp)
    assert svg.count("waterfall-bar") == len(cp["bars"])
    assert svg.count("waterfall-connector") == len(cp["connectors"])
    assert svg.count("waterfall-value") == 6
    for b in cp["bars"]:
        assert f'data-category="{b["category_id"]}"' in svg
        assert f'x="{b["x"]:.1f}"' in svg
        assert f'width="{b["width"]:.1f}"' in svg


def test_chartjs_floating_bars_within_2px(tmp_path: Path):
    out = tmp_path / "out"
    render_deck(WF, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    deck = validate_handoff(_w(), strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["rev-bridge"].chart_paint
    g = cp["geometry"]
    m = re.search(
        r'<script type="application/json" id="cfg-rev-bridge">(.*?)</script>',
        html,
        re.S,
    )
    assert m is not None
    cfg = json.loads(m.group(1))
    cm = re.search(
        r'<canvas id="cjs-rev-bridge"[^>]*width="(\d+)" height="(\d+)"', html
    )
    assert cm is not None
    canvas_w, canvas_h = int(cm.group(1)), int(cm.group(2))
    pad = cfg["options"]["layout"]["padding"]
    plot_x0, plot_y0 = pad["left"], pad["top"]
    plot_w = canvas_w - pad["left"] - pad["right"]
    plot_h = canvas_h - pad["top"] - pad["bottom"]
    n_cat = len(cfg["data"]["labels"])
    val_scale = cfg["options"]["scales"]["y"]
    v_min, v_max = val_scale["min"], val_scale["max"]
    v_span = (v_max - v_min) or 1.0
    pitch = plot_w / n_cat
    ds = cfg["data"]["datasets"][0]
    cluster = ds["categoryPercentage"] * pitch
    bar_w = ds["barPercentage"] * cluster

    def value_px(v: float) -> float:
        return plot_y0 + plot_h - (v - v_min) / v_span * plot_h

    checked = 0
    for i, b in enumerate(cp["bars"]):
        pair = ds["data"][i]
        y0, y1 = float(pair[0]), float(pair[1])
        top, bot = value_px(max(y0, y1)), value_px(min(y0, y1))
        height = abs(bot - top)
        origin = plot_x0 + i * pitch + (pitch - cluster) / 2 + (cluster - bar_w) / 2
        assert abs(origin - b["x"]) <= 2.0
        assert abs(top - b["y"]) <= 2.0
        assert abs(bar_w - b["width"]) <= 2.0
        assert abs(height - b["height"]) <= 2.0
        checked += 1
    assert checked == 6


def test_byte_identical_rerun(tmp_path: Path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    render_deck(WF, a, strict=True)
    render_deck(WF, b, strict=True)
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


def test_mutation_drop_role_fails():
    raw = _w()
    del _chart_slide(raw)["payload"]["primary_visual"]["waterfall_data"]["steps"][1][
        "role"
    ]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_mutation_infer_total_from_sign_not_allowed():
    """Roles are never inferred from sign — a negative total is still a total."""
    raw = _w()
    steps = _chart_slide(raw)["payload"]["primary_visual"]["waterfall_data"]["steps"]
    steps[0]["value"] = "-50"
    # Keep domain wide enough.
    _chart_slide(raw)["payload"]["primary_visual"]["value_axes"]["primary"][
        "domain"
    ] = {"kind": "generated", "target_ticks": 5}
    # Shrink later values so levels stay coherent for domain.
    steps[1]["value"] = "10"
    steps[2]["value"] = "5"
    steps[3]["value"] = "-30"
    steps[4]["value"] = "2"
    deck = validate_handoff(raw, strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["rev-bridge"].chart_paint
    open_bar = next(b for b in cp["bars"] if b["category_id"] == "open")
    assert open_bar["role"] == "total"
    assert open_bar["color_role"] == "total"
    assert float(open_bar["y0"]) == 0.0


def test_mutation_swap_step_order_changes_levels():
    raw = _w()
    steps = _chart_slide(raw)["payload"]["primary_visual"]["waterfall_data"]["steps"]
    # Swap price and volume changes.
    steps[1], steps[2] = steps[2], steps[1]
    deck = validate_handoff(raw, strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["rev-bridge"].chart_paint
    by_id = {s["category_id"]: s for s in cp["steps"]}
    # Opening 100, volume -10 first → 90, then price +20 → 110
    assert by_id["volume"]["level"] == Decimal("90")
    assert by_id["price"]["level"] == Decimal("110")


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
    deck = validate_handoff(_w(), strict=True).deck
    assert charts.freeze_waterfall_chart(
        deck.slides[1].payload.primary_visual, deck.number_formats
    )


def test_identity_strategy_is_roles_not_legend():
    deck = validate_handoff(_w(), strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["rev-bridge"].chart_paint
    assert cp["identity_strategy"] == "roles"
    # No legend chrome in paint path when identity is roles.
    html_parts = __import__(
        "impact_slides.renderer_v3.charts", fromlist=["paint_chart_html"]
    ).paint_chart_html(cp, svg_only=True)
    joined = "".join(html_parts)
    assert "chart-legend" not in joined
