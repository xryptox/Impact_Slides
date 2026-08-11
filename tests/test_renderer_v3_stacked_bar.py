"""Renderer v3 sign-separated stacked bar charts (#184).

Seams under test:
- typed single_chart stacked_bar (D242/D304)
- independent +/- accumulation, order, missing-aware totals (D79/D92/D161)
- authored totals + coverage callout (D235/D241/D236/D301)
- Chart.js/SVG geometry parity within 2px (D160)
- identity + semantic table completeness (D247)
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
    freeze_bar_chart,
    paint_chart_svg,
    paint_semantic_table,
)
from impact_slides.renderer_v3.format import MISSING_ACCESSIBLE, MISSING_VISIBLE
from impact_slides.renderer_v3.models import SingleChartSlide, StackedBarChartVisual
from impact_slides.renderer_v3.plan import plan_deck
from impact_slides.renderer_v3.schema_export import check_schema

ROOT = Path(__file__).resolve().parents[1]
STACKED = ROOT / "tests/fixtures/renderer_v3/minimal_stacked_bar.json"
GROUPED = ROOT / "tests/fixtures/renderer_v3/minimal_grouped_bar.json"


def _s() -> dict:
    return json.loads(STACKED.read_text(encoding="utf-8"))


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


def test_stacked_bar_deck_validates():
    result = validate_handoff(_s(), strict=True)
    assert result.ok
    slide = result.deck.slides[1]
    assert isinstance(slide, SingleChartSlide)
    chart = slide.payload.primary_visual
    assert isinstance(chart, StackedBarChartVisual)
    assert chart.chart_type == "stacked_bar"
    assert len(chart.chart_data.categories) == 4
    assert len(chart.chart_data.series) == 3
    assert chart.chart_data.series[0].values[3] is None
    assert chart.coverage_callout is not None
    assert chart.auxiliary_series and chart.auxiliary_series[0].role == "authored_stack_total"
    assert chart.display is not None
    assert chart.display.stack_segments == "show"
    assert chart.display.stack_totals == "show"


def test_grouped_fixture_still_validates():
    assert validate_handoff(json.loads(GROUPED.read_text(encoding="utf-8")), strict=True).ok


def test_strict_rejects_one_series_stack():
    raw = _s()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    vis["chart_data"]["series"] = [vis["chart_data"]["series"][0]]
    # Drop aux/coverage that may reference multi-series assumptions.
    del vis["auxiliary_series"]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_seven_series_stack():
    raw = _s()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    base = vis["chart_data"]["series"][0]
    extra = []
    for i in range(7):
        s = deepcopy(base)
        s["series_id"] = f"s{i}"
        s["name"] = f"Series {i}"
        extra.append(s)
    vis["chart_data"]["series"] = extra
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_leading_break_on_stack():
    raw = _s()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    vis["value_axes"]["primary"]["domain"] = {
        "kind": "generated",
        "min": "0",
        "target_ticks": 5,
    }
    vis["value_axes"]["primary"]["leading_break"] = {"to": "1"}
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_ordinary_values_display_on_stack():
    raw = _s()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    vis["display"] = {"ordinary_values": "show", "series_identity": "legend"}
    with pytest.raises(RendererValidationError) as excinfo:
        validate_handoff(raw, strict=True)
    assert any("ordinary_values" in c for c in _contracts(excinfo))


def test_strict_rejects_pane_title_identity_on_stack():
    raw = _s()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    vis["display"] = {"series_identity": "pane_title", "stack_totals": "show"}
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_boxed_label_on_stack():
    raw = _s()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
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


def test_strict_rejects_coverage_on_grouped():
    raw = json.loads(GROUPED.read_text(encoding="utf-8"))
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    vis["coverage_callout"] = {
        "callout_id": "c1",
        "label": "Cov",
        "value": "50",
        "format_id": "pct_1",
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_coverage_non_percent():
    raw = _s()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    vis["coverage_callout"]["format_id"] = "usd_0"
    with pytest.raises(RendererValidationError) as excinfo:
        validate_handoff(raw, strict=True)
    assert any("percent" in c for c in _contracts(excinfo))


def test_strict_rejects_coverage_out_of_range():
    raw = _s()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    vis["coverage_callout"]["value"] = "150"
    with pytest.raises(RendererValidationError) as excinfo:
        validate_handoff(raw, strict=True)
    assert any("0–100" in c or "0-100" in c for c in _contracts(excinfo))


def test_strict_rejects_authored_total_with_hide():
    raw = _s()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    vis["display"] = {"stack_totals": "hide", "series_identity": "legend"}
    with pytest.raises(RendererValidationError) as excinfo:
        validate_handoff(raw, strict=True)
    assert any("authored_stack_total" in c for c in _contracts(excinfo))


def test_strict_rejects_stack_domain_excluding_extent():
    raw = _s()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    # Q1 positive extent = 70; domain max 60 fails containment.
    vis["value_axes"]["primary"]["domain"] = {
        "kind": "fixed",
        "min": "-20",
        "max": "60",
        "ticks": ["-20", "0", "20", "40", "60"],
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_json_number_stack_value():
    raw = _s()
    _chart_slide(raw)["payload"]["primary_visual"]["chart_data"]["series"][0]["values"][
        0
    ] = 40
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


# ---------------------------------------------------------------------------
# Frozen plan — sign-separated geometry + totals
# ---------------------------------------------------------------------------


def test_stacked_plan_sign_separated_order_and_missing():
    deck = validate_handoff(_s(), strict=True).deck
    plan = plan_deck(deck, strict=True)
    sp = plan.by_surface_id()["dep-mix"]
    assert sp.role == "stacked_bar_chart"
    cp = sp.chart_paint
    assert cp["chart_type"] == "stacked_bar"
    assert cp["geometry"]["stacked"] is True
    assert cp["gridlines"] is False
    assert float(cp["domain"]["min"]) <= 0.0 <= float(cp["domain"]["max"])
    assert cp["identity_strategy"] == "legend"
    assert cp["show_segment_labels"] is True
    assert cp["show_stack_totals"] is True

    bars = cp["bars"]
    # 4 cats × 3 series
    assert len(bars) == 12
    by = {(b["series_id"], b["category_id"]): b for b in bars}

    # null retail@q4 preserves slot
    miss = by[("retail", "q4")]
    assert miss["missing"] is True
    assert miss["finite"] is False
    assert miss["visible"] == MISSING_VISIBLE
    assert miss["accessible"] == MISSING_ACCESSIBLE
    assert miss["height"] == 0.0

    # Q1: retail 40 + wholesale 30 stack above zero in author order bottom→top
    r = by[("retail", "q1")]
    w = by[("wholesale", "q1")]
    assert r["sign"] == 1 and w["sign"] == 1
    assert r["stack_base"] == 0.0
    assert r["stack_top"] == 40.0
    assert w["stack_base"] == 40.0
    assert w["stack_top"] == 70.0
    # higher stack_top → smaller y (above)
    assert w["y"] < r["y"]
    # same category x (stacked, not grouped)
    assert abs(r["x"] - w["x"]) <= 0.5

    # runoff negative stacks below zero
    n = by[("runoff", "q1")]
    assert n["sign"] == -1
    assert n["stack_base"] == 0.0
    assert n["stack_top"] == -10.0
    assert n["y"] + n["height"] >= cp["geometry"]["zero_y"] - 0.5

    # zero runoff@q3 is data without area (D304)
    z = by[("runoff", "q3")]
    assert z["finite"] is True
    assert z["numeric"] == 0.0
    assert z["sign"] == 0
    assert z["height"] == 0.0

    # series legend order is author order
    assert [s["series_id"] for s in cp["series"]] == [
        "retail",
        "wholesale",
        "runoff",
    ]

    # groups + coverage present
    assert len(cp["category_groups"]) == 2
    assert cp["coverage_callout"] is not None
    assert "72" in cp["coverage_callout"]["value_visible"]
    assert "FDIC" in cp["coverage_callout"]["label"]

    # Authored totals are separate facts; computed sides always recorded (D241/D247).
    totals = cp["stack_totals"]
    authored = [t for t in totals if t.get("source") == "authored"]
    assert len(authored) == 4
    q1_a = next(t for t in authored if t["category_id"] == "q1")
    assert q1_a["missing"] is False
    assert q1_a["visible"].startswith("$")
    q3_a = next(t for t in authored if t["category_id"] == "q3")
    assert q3_a["missing"] is True
    assert q3_a["visible"] == MISSING_VISIBLE

    # Q4 null retail withholds computed sides even with authored total present.
    q4_withheld = [
        t for t in totals if t["category_id"] == "q4" and t.get("withheld")
    ]
    assert q4_withheld
    q4_authored = next(t for t in authored if t["category_id"] == "q4")
    assert q4_authored["missing"] is False

    table = cp["semantic_table"]
    # 3 series + pos total + neg total + authored total
    assert len(table["columns"]) == 6
    assert len(table["rows"]) == 4
    assert table["rows"][3]["cells"][0]["missing"] is True
    # Q1 positive total column present
    col_ids = [c["series_id"] for c in table["columns"]]
    assert "_pos_total" in col_ids and "_neg_total" in col_ids
    pos_i = col_ids.index("_pos_total")
    assert "70" in table["rows"][0]["cells"][pos_i]["visible"]
    facts = " ".join(table["facts"])
    assert "stacked" in facts.lower() or "sign-separated" in facts.lower()
    assert "Coverage" in facts or "FDIC" in facts
    assert "withheld" in facts.lower() or "Missing" in facts


def test_null_withholds_computed_totals():
    raw = _s()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    del vis["auxiliary_series"]
    deck = validate_handoff(raw, strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["dep-mix"].chart_paint
    withheld = [
        t
        for t in cp["stack_totals"]
        if t["category_id"] == "q4" and t.get("withheld")
    ]
    assert withheld, "null contributor must withhold computed sign totals"
    facts = " ".join(cp["semantic_table"]["facts"])
    assert "withheld" in facts.lower()


def test_computed_totals_without_authored():
    raw = _s()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    del vis["auxiliary_series"]
    # Keep stack_totals show via display.
    deck = validate_handoff(raw, strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["dep-mix"].chart_paint
    totals = [t for t in cp["stack_totals"] if t.get("source") == "computed"]
    # Q1 positive = 70, negative = -10
    q1_pos = next(
        t
        for t in totals
        if t["category_id"] == "q1" and t["side"] == "positive" and not t.get("withheld")
    )
    assert "70" in q1_pos["visible"]
    q1_neg = next(
        t
        for t in totals
        if t["category_id"] == "q1" and t["side"] == "negative" and not t.get("withheld")
    )
    assert "10" in q1_neg["visible"]  # formatted magnitude with unit/sign


def test_default_labels_hidden():
    raw = _s()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    del vis["display"]
    del vis["auxiliary_series"]  # else totals implied show
    deck = validate_handoff(raw, strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["dep-mix"].chart_paint
    assert cp["show_segment_labels"] is False
    assert cp["show_stack_totals"] is False
    segs = [p for p in cp["placements"] if p.get("kind") == "segment"]
    assert segs and all(p["class"] == "suppressed" for p in segs)


def test_freeze_assigns_stack_theme_colors():
    deck = validate_handoff(_s(), strict=True).deck
    chart = deck.slides[1].payload.primary_visual
    frozen = freeze_bar_chart(chart, deck.number_formats)
    assert len(frozen["series"]) == 3
    colors = [s["color"] for s in frozen["series"]]
    assert all(c.startswith("#") for c in colors)
    assert len(set(colors)) == 3


# ---------------------------------------------------------------------------
# Publication / dual painters
# ---------------------------------------------------------------------------


def test_render_stacked_emits_chartjs_svg_table(tmp_path: Path):
    out = tmp_path / "out"
    result = render_deck(STACKED, out, strict=True)
    assert result["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-chart-type="stacked_bar"' in html
    assert 'data-chart-surface="dep-mix"' in html
    assert "chartjs-canvas" in html
    assert "chart-svg" in html
    assert 'data-semantic-table="1"' in html
    assert "coverage-callout" in html or "FDIC" in html
    # Legend lists all three series
    assert "Retail" in html and "Wholesale" in html and "Runoff" in html
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    readiness = meta.get("static_readiness") or meta.get("readiness") or []
    # Find chart slide readiness
    chart_ready = [
        r
        for r in readiness
        if r.get("layout_type") == "single_chart"
        or r.get("slide_number") == 2
    ]
    assert chart_ready
    assert "chartjs" in chart_ready[0].get("chart_painters", [])
    assert chart_ready[0].get("semantic_table_present") is True


def test_svg_and_semantic_table_parity():
    deck = validate_handoff(_s(), strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["dep-mix"].chart_paint
    svg = paint_chart_svg(cp)
    assert 'class="bar"' in svg
    assert svg.count('class="bar"') >= 8  # finite segments
    table = paint_semantic_table(cp)
    assert "Retail" in table and "Q1" in table
    assert MISSING_VISIBLE in table


def test_chartjs_stack_config_and_geometry_parity():
    from impact_slides.renderer_v3.charts import _chartjs_bar_config

    deck = validate_handoff(_s(), strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["dep-mix"].chart_paint
    cfg = _chartjs_bar_config(cp)
    assert cfg["type"] == "bar"
    assert cfg["options"]["scales"]["y"]["stacked"] is True
    assert cfg["v3"]["stacked"] is True
    datasets = cfg["data"]["datasets"]
    assert len(datasets) == 3
    assert all(ds.get("stack") == "stack" for ds in datasets)

    # Reconstruct stacked extents from datasets and compare to frozen bars ≤2px.
    g = cp["geometry"]
    plot_w = g["plot_w"]
    plot_h = g["plot_h"]
    pad_l = g["pad_l"]
    pad_t = g["pad_t"]
    v_min = float(cfg["options"]["scales"]["y"]["min"])
    v_max = float(cfg["options"]["scales"]["y"]["max"])
    v_span = (v_max - v_min) or 1.0
    n_cat = len(cp["categories"])
    pitch = plot_w / n_cat
    thick = datasets[0]["categoryPercentage"] * pitch * datasets[0]["barPercentage"]

    def value_y(v: float) -> float:
        return pad_t + plot_h - (v - v_min) / v_span * plot_h

    ser_idx = {s["series_id"]: i for i, s in enumerate(cp["series"])}
    cat_idx = {c["category_id"]: i for i, c in enumerate(cp["categories"])}
    # Per-category signed cursors mirror freeze order.
    checked = 0
    for c_i, cat in enumerate(cp["categories"]):
        pos_c = 0.0
        neg_c = 0.0
        origin = pad_l + c_i * pitch + (pitch - thick) / 2
        for s in cp["series"]:
            d_i = ser_idx[s["series_id"]]
            raw = datasets[d_i]["data"][c_i]
            b = next(
                bar
                for bar in cp["bars"]
                if bar["series_id"] == s["series_id"]
                and bar["category_id"] == cat["category_id"]
            )
            if raw is None:
                assert b.get("missing") is True
                continue
            v = float(raw)
            if v > 0:
                base, top = pos_c, pos_c + v
                pos_c = top
            elif v < 0:
                base, top = neg_c, neg_c + v
                neg_c = top
            else:
                # zero is data without area
                assert b["height"] == 0.0
                checked += 1
                continue
            y0, y1 = value_y(base), value_y(top)
            ry = min(y0, y1)
            rh = abs(y1 - y0)
            assert abs(origin - b["x"]) <= 2.0
            assert abs(ry - b["y"]) <= 2.0
            assert abs(thick - b["width"]) <= 2.0
            assert abs(rh - b["height"]) <= 2.0
            checked += 1
    assert checked >= 8


def test_byte_identical_rerun_stacked(tmp_path: Path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    render_deck(STACKED, a, strict=True)
    render_deck(STACKED, b, strict=True)
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


def test_mutation_drop_callout_id_fails():
    raw = _s()
    del _chart_slide(raw)["payload"]["primary_visual"]["coverage_callout"]["callout_id"]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_mutation_null_not_zero_filled():
    deck = validate_handoff(_s(), strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["dep-mix"].chart_paint
    cell = cp["semantic_table"]["rows"][3]["cells"][0]
    assert cell["missing"] is True
    assert cell["visible"] != "$0"
    assert cell["visible"] != "0"


def test_mutation_swap_series_order_changes_stack_bases():
    raw = _s()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    # Swap retail/wholesale — first positive series becomes wholesale.
    vis["chart_data"]["series"] = [
        vis["chart_data"]["series"][1],
        vis["chart_data"]["series"][0],
        vis["chart_data"]["series"][2],
    ]
    deck = validate_handoff(raw, strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["dep-mix"].chart_paint
    assert cp["series"][0]["series_id"] == "wholesale"
    by = {(b["series_id"], b["category_id"]): b for b in cp["bars"]}
    assert by[("wholesale", "q1")]["stack_base"] == 0.0
    assert by[("retail", "q1")]["stack_base"] == 30.0


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
    deck = validate_handoff(_s(), strict=True).deck
    assert charts.freeze_bar_chart(
        deck.slides[1].payload.primary_visual, deck.number_formats
    )
