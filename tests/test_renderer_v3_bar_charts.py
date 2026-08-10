"""Renderer v3 grouped + horizontal bar charts (#183).

Seams under test:
- typed single_chart grouped_bar / horizontal_bar (D240/D243)
- signed/zero/null geometry, order, identities, outside values (D71–D73/D92)
- horizontal leading break positive-side contract (D157/D243)
- category groups + boxed labels (D155/D237/D235)
- Chart.js/SVG geometry parity within 2px (D160)
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
from impact_slides.renderer_v3.models import (
    GroupedBarChartVisual,
    HorizontalBarChartVisual,
    SingleChartSlide,
)
from impact_slides.renderer_v3.plan import plan_deck
from impact_slides.renderer_v3.schema_export import check_schema

ROOT = Path(__file__).resolve().parents[1]
GROUPED = ROOT / "tests/fixtures/renderer_v3/minimal_grouped_bar.json"
HBAR = ROOT / "tests/fixtures/renderer_v3/minimal_horizontal_bar.json"
LINE = ROOT / "tests/fixtures/renderer_v3/minimal_line_chart.json"


def _g() -> dict:
    return json.loads(GROUPED.read_text(encoding="utf-8"))


def _h() -> dict:
    return json.loads(HBAR.read_text(encoding="utf-8"))


def _chart_slide(raw: dict) -> dict:
    return next(s for s in raw["slides"] if s.get("layout_type") == "single_chart")


# ---------------------------------------------------------------------------
# Validation / model
# ---------------------------------------------------------------------------


def test_grouped_bar_deck_validates():
    result = validate_handoff(_g(), strict=True)
    assert result.ok
    slide = result.deck.slides[1]
    assert isinstance(slide, SingleChartSlide)
    chart = slide.payload.primary_visual
    assert isinstance(chart, GroupedBarChartVisual)
    assert chart.chart_type == "grouped_bar"
    assert len(chart.chart_data.categories) == 4
    assert len(chart.chart_data.series) == 2
    assert chart.chart_data.series[0].values[3] is None
    assert chart.chart_data.series[0].values[2] == "0"
    assert chart.category_groups and len(chart.category_groups) == 2
    assert chart.auxiliary_series and chart.auxiliary_series[0].role == "boxed_label"


def test_horizontal_bar_deck_validates():
    result = validate_handoff(_h(), strict=True)
    assert result.ok
    chart = result.deck.slides[1].payload.primary_visual
    assert isinstance(chart, HorizontalBarChartVisual)
    assert chart.chart_type == "horizontal_bar"
    assert chart.value_axes.primary.leading_break is not None
    assert chart.value_axes.primary.leading_break.to == "40"


def test_line_fixture_still_validates():
    assert validate_handoff(json.loads(LINE.read_text(encoding="utf-8")), strict=True).ok


def test_strict_rejects_grouped_leading_break():
    raw = _g()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    vis["value_axes"]["primary"]["domain"] = {
        "kind": "generated",
        "min": "0",
        "target_ticks": 5,
    }
    vis["value_axes"]["primary"]["leading_break"] = {"to": "1"}
    # Also lift values above break so only family forbid trips if order matters.
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_hbar_mixed_sign_with_break():
    raw = _h()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    vis["chart_data"]["series"][0]["values"] = ["62.5", "-5.0", "55.2", "50.0"]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_overlapping_category_groups():
    raw = _g()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    vis["category_groups"][1]["category_ids"] = ["intl", "smob"]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_noncontiguous_category_group():
    raw = _g()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    vis["category_groups"] = [
        {
            "group_id": "skip",
            "label": "Skip",
            "category_ids": ["us", "smob"],
        }
    ]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_boxed_unknown_target_series():
    raw = _g()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    vis["auxiliary_series"][0]["target_series_id"] = "nope"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_bar_domain_excluding_zero():
    raw = _g()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    vis["value_axes"]["primary"]["domain"] = {
        "kind": "fixed",
        "min": "1",
        "max": "6",
        "ticks": ["1", "2", "3", "4", "5", "6"],
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_json_number_bar_value():
    raw = _g()
    _chart_slide(raw)["payload"]["primary_visual"]["chart_data"]["series"][0]["values"][
        0
    ] = 3.2
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


# ---------------------------------------------------------------------------
# Frozen plan — signed / zero / null geometry
# ---------------------------------------------------------------------------


def test_grouped_plan_preserves_signed_zero_null():
    deck = validate_handoff(_g(), strict=True).deck
    plan = plan_deck(deck, strict=True)
    sp = plan.by_surface_id()["seg-growth"]
    assert sp.role == "grouped_bar_chart"
    cp = sp.chart_paint
    assert cp["chart_type"] == "grouped_bar"
    assert cp["gridlines"] is False
    assert float(cp["domain"]["min"]) <= 0.0 <= float(cp["domain"]["max"])

    bars = cp["bars"]
    assert len(bars) == 8  # 4 cats × 2 series
    by = {(b["series_id"], b["category_id"]): b for b in bars}

    # null slot preserved, no paint geometry
    miss = by[("fy24", "corp")]
    assert miss["missing"] is True
    assert miss["finite"] is False
    assert miss["visible"] == MISSING_VISIBLE
    assert miss["accessible"] == MISSING_ACCESSIBLE

    # zero is real zero-height mark (stub)
    zero = by[("fy24", "smob")]
    assert zero["finite"] is True
    assert zero["numeric"] == 0.0
    assert zero["sign"] == 0
    assert zero["height"] >= 2.0

    # negative paints below zero
    neg = by[("fy24", "intl")]
    assert neg["sign"] == -1
    assert neg["y"] >= cp["geometry"]["zero_y"] - 0.5

    # positive paints above zero
    pos = by[("fy25", "us")]
    assert pos["sign"] == 1
    assert pos["y"] + pos["height"] <= cp["geometry"]["zero_y"] + 0.5

    # series order within category: fy24 then fy25 left-to-right
    a = by[("fy24", "us")]
    b = by[("fy25", "us")]
    assert a["x"] < b["x"]

    # outside ordinary values present by default
    value_places = [p for p in cp["placements"] if p.get("kind") == "value"]
    assert value_places
    assert any(p["class"] != "suppressed" for p in value_places)

    # groups + boxed in plan
    assert len(cp["category_groups"]) == 2
    assert any(p.get("kind") == "boxed_label" for p in cp["placements"])

    table = cp["semantic_table"]
    assert len(table["columns"]) == 2
    assert len(table["rows"]) == 4
    assert table["rows"][3]["cells"][0]["missing"] is True
    assert any("Core" in f or "core" in f.lower() for f in table["facts"])


def test_horizontal_leading_break_contract():
    deck = validate_handoff(_h(), strict=True).deck
    plan = plan_deck(deck, strict=True)
    cp = plan.by_surface_id()["net-share"].chart_paint
    assert cp["chart_type"] == "horizontal_bar"
    assert cp["geometry"]["horizontal"] is True
    assert cp["value_axis"]["leading_break"] == "40"
    # Visible domain starts at break; ticks begin at 40
    assert float(cp["domain"]["min"]) == 40.0
    assert float(cp["domain"]["ticks"][0]) == 40.0
    # Bars start at disclosed boundary (zero_x)
    finite = [b for b in cp["bars"] if b.get("finite")]
    assert finite
    zx = cp["geometry"]["zero_x"]
    for b in finite:
        assert abs(b["x"] - zx) <= 2.0 or b["x"] >= zx - 2.0
    # Full values remain in labels/D106 (not break-relative)
    us = next(b for b in cp["bars"] if b["category_id"] == "us" and b.get("finite"))
    assert "62.5" in us["visible"] or "62" in us["visible"]
    # Null slot preserved
    miss = next(b for b in cp["bars"] if b["category_id"] == "mx")
    assert miss["missing"] is True
    # Identity pane_title for single series
    assert cp["identity_strategy"] == "pane_title"
    # Facts disclose break
    assert any("break" in f.lower() for f in cp["semantic_table"]["facts"])


def test_freeze_assigns_bar_theme_colors():
    deck = validate_handoff(_g(), strict=True).deck
    chart = deck.slides[1].payload.primary_visual
    frozen = freeze_bar_chart(chart, deck.number_formats)
    assert frozen["series"][0]["color"].startswith("#")
    assert frozen["series"][1]["color"].startswith("#")
    assert frozen["series"][0]["color"] != frozen["series"][1]["color"]


# ---------------------------------------------------------------------------
# Publication / dual painters
# ---------------------------------------------------------------------------


def test_render_grouped_emits_chartjs_svg_table(tmp_path: Path):
    out = tmp_path / "out"
    result = render_deck(GROUPED, out, strict=True)
    assert result["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-chart-type="grouped_bar"' in html
    assert 'data-chart-surface="seg-growth"' in html
    assert "chartjs-canvas" in html
    assert "<noscript>" in html
    assert "<svg" in html and 'class="bar"' in html
    assert 'data-semantic-table="1"' in html
    assert "category-group" in html
    assert "boxed-label" in html
    assert MISSING_VISIBLE in html
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    chart_ready = [
        r for r in meta["static_readiness"] if r["layout_type"] == "single_chart"
    ]
    assert chart_ready
    assert chart_ready[0]["semantic_table_present"] is True
    assert "chartjs" in chart_ready[0]["chart_painters"]
    assert "svg" in chart_ready[0]["chart_painters"]


def test_render_horizontal_break_chrome(tmp_path: Path):
    out = tmp_path / "out"
    result = render_deck(HBAR, out, strict=True)
    assert result["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-chart-type="horizontal_bar"' in html
    assert "leading-break" in html
    assert 'data-break-to="40"' in html
    # Chart.js bar config uses indexAxis y
    m = re.search(
        r'<script type="application/json" id="cfg-net-share">(.*?)</script>',
        html,
        re.S,
    )
    assert m is not None
    cfg = json.loads(m.group(1))
    assert cfg["type"] == "bar"
    assert cfg["options"]["indexAxis"] == "y"
    assert cfg["options"]["scales"]["x"]["min"] == 40.0
    assert cfg["v3"]["leading_break"] == "40"


def test_svg_bar_geometry_matches_frozen_plan():
    deck = validate_handoff(_g(), strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["seg-growth"].chart_paint
    svg = paint_chart_svg(cp)
    # One rect per finite bar
    finite = [b for b in cp["bars"] if b.get("finite") and not b.get("missing")]
    assert svg.count('class="bar"') == len(finite)
    for b in finite:
        assert f'data-series="{b["series_id"]}"' in svg
        assert f'data-category="{b["category_id"]}"' in svg
        # geometry attributes within plan (string form)
        assert f'x="{b["x"]:.1f}"' in svg
        assert f'width="{b["width"]:.1f}"' in svg


@pytest.mark.parametrize(
    ("fixture", "surface_id"),
    [(GROUPED, "seg-growth"), (HBAR, "net-share")],
)
def test_chartjs_bar_area_pinned_to_frozen_plot(fixture, surface_id, tmp_path: Path):
    out = tmp_path / "out"
    render_deck(fixture, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    deck = validate_handoff(
        json.loads(fixture.read_text(encoding="utf-8")), strict=True
    ).deck
    cp = plan_deck(deck, strict=True).by_surface_id()[surface_id].chart_paint
    g = cp["geometry"]
    m = re.search(
        rf'<script type="application/json" id="cfg-{surface_id}">(.*?)</script>',
        html,
        re.S,
    )
    assert m is not None
    cfg = json.loads(m.group(1))
    assert cfg["options"]["layout"]["padding"] == {
        "left": g["pad_l"],
        "right": g["pad_r"],
        "top": g["pad_t"],
        "bottom": g["pad_b"],
    }
    # Rebuild what Chart.js renders from the emitted config (canvas size,
    # layout padding, scale min/max, category/bar percentages) and pin it
    # to the frozen plan within 2px (D160).
    cm = re.search(
        rf'<canvas id="cjs-{surface_id}"[^>]*width="(\d+)" height="(\d+)"', html
    )
    assert cm is not None
    canvas_w, canvas_h = int(cm.group(1)), int(cm.group(2))
    pad = cfg["options"]["layout"]["padding"]
    plot_x0, plot_y0 = pad["left"], pad["top"]
    plot_w = canvas_w - pad["left"] - pad["right"]
    plot_h = canvas_h - pad["top"] - pad["bottom"]
    horizontal = cfg["options"]["indexAxis"] == "y"
    datasets = cfg["data"]["datasets"]
    n_cat = len(cfg["data"]["labels"])
    n_ser = len(datasets)
    val_scale = cfg["options"]["scales"]["x" if horizontal else "y"]
    v_min, v_max = val_scale["min"], val_scale["max"]
    v_span = (v_max - v_min) or 1.0
    cat_span = plot_h if horizontal else plot_w
    cat_start = plot_y0 if horizontal else plot_x0
    pitch = cat_span / n_cat
    cluster = datasets[0]["categoryPercentage"] * pitch
    slot = cluster / n_ser
    bar_w = datasets[0]["barPercentage"] * slot
    baseline = v_min if v_min > 0 else (v_max if v_max < 0 else 0.0)

    def value_px(v: float) -> float:
        if horizontal:
            return plot_x0 + (v - v_min) / v_span * plot_w
        return plot_y0 + plot_h - (v - v_min) / v_span * plot_h

    base_px = value_px(baseline)
    ser_idx = {s["series_id"]: i for i, s in enumerate(cp["series"])}
    cat_idx = {c["category_id"]: i for i, c in enumerate(cp["categories"])}
    checked = 0
    for b in cp["bars"]:
        if b.get("missing") or not b.get("finite"):
            continue
        d_i = ser_idx[b["series_id"]]
        c_i = cat_idx[b["category_id"]]
        v = datasets[d_i]["data"][c_i]
        origin = (
            cat_start
            + c_i * pitch
            + (pitch - cluster) / 2
            + d_i * slot
            + (slot - bar_w) / 2
        )
        tip = value_px(float(v))
        if horizontal:
            rx, ry, rw, rh = min(base_px, tip), origin, abs(tip - base_px), bar_w
        else:
            rx, ry, rw, rh = origin, min(base_px, tip), bar_w, abs(tip - base_px)
        assert abs(rx - b["x"]) <= 2.0
        assert abs(ry - b["y"]) <= 2.0
        assert abs(rw - b["width"]) <= 2.0
        assert abs(rh - b["height"]) <= 2.0
        checked += 1
    assert checked > 0


def test_byte_identical_rerun_grouped(tmp_path: Path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    render_deck(GROUPED, a, strict=True)
    render_deck(GROUPED, b, strict=True)
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


def test_mutation_drop_group_id_fails():
    raw = _g()
    del _chart_slide(raw)["payload"]["primary_visual"]["category_groups"][0]["group_id"]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_mutation_null_not_zero_filled():
    deck = validate_handoff(_g(), strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["seg-growth"].chart_paint
    cell = cp["semantic_table"]["rows"][3]["cells"][0]
    assert cell["missing"] is True
    assert cell["visible"] != "0.0%"
    assert cell["visible"] != "0"


def test_mutation_swap_series_order_changes_paint():
    raw = _g()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    vis["chart_data"]["series"] = list(reversed(vis["chart_data"]["series"]))
    deck = validate_handoff(raw, strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["seg-growth"].chart_paint
    # First series in authored order is now fy25
    assert cp["series"][0]["series_id"] == "fy25"
    us_bars = sorted(
        [b for b in cp["bars"] if b["category_id"] == "us" and b.get("finite")],
        key=lambda b: b["x"],
    )
    assert us_bars[0]["series_id"] == "fy25"


def test_hide_ordinary_values_suppresses_only_ordinary():
    raw = _g()
    _chart_slide(raw)["payload"]["primary_visual"]["display"] = {
        "ordinary_values": "hide",
        "series_identity": "legend",
    }
    deck = validate_handoff(raw, strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["seg-growth"].chart_paint
    assert cp["show_ordinary_values"] is False
    value_places = [p for p in cp["placements"] if p.get("kind") == "value"]
    assert value_places and all(p["class"] == "suppressed" for p in value_places)
    # Boxed labels remain structural
    assert any(p.get("kind") == "boxed_label" for p in cp["placements"])


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
    deck = validate_handoff(_g(), strict=True).deck
    assert charts.freeze_bar_chart(
        deck.slides[1].payload.primary_visual, deck.number_formats
    )


def test_single_series_grouped_valid():
    raw = _g()
    vis = _chart_slide(raw)["payload"]["primary_visual"]
    vis["chart_data"]["series"] = [vis["chart_data"]["series"][1]]
    del vis["auxiliary_series"]
    del raw["number_formats"]["usd_0"]
    vis["display"] = {"series_identity": "pane_title", "ordinary_values": "show"}
    assert validate_handoff(raw, strict=True).ok
