"""Renderer v3 pie/donut ChartVisual (#287/#322).

Seams under test:
- typed pie/donut slice visual (2–8 slices, semantic values, no cartesian axes)
- single_chart + dual_chart envelopes (heatmap still forbidden on dual)
- Chart.js doughnut + noscript SVG radial + D247 semantic table
- D10/D47 320×240 plot floor; D304 navy ink on low-contrast slices
- same-slide slice_id color identity; names outside the ring at ordinary_values floor
- outside-name pad grows with type so the ring shrinks (#340); D47 floor still holds
- outside name/percent AABB must clear the frozen disk (#341); in-wedge percents stay inside
"""
from __future__ import annotations

import json
import math
from copy import deepcopy
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.charts import PAD_R, freeze_chart, paint_chart_svg
from impact_slides.renderer_v3.models import DonutChartVisual, PieChartVisual, SingleChartSlide
from impact_slides.renderer_v3.plan import plan_deck
from impact_slides.renderer_v3.schema_export import check_schema, generate_schema
from impact_slides.renderer_v3.theme import contrast_ratio, resolve_series_colors

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/renderer_v3/minimal_donut.json"
LINE = ROOT / "tests/fixtures/renderer_v3/minimal_line_chart.json"
HEAT = ROOT / "tests/fixtures/renderer_v3/minimal_heatmap.json"


def _raw() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _chart(raw: dict | None = None) -> dict:
    src = raw if raw is not None else _raw()
    return next(s for s in src["slides"] if s.get("layout_type") == "single_chart")[
        "payload"
    ]["chart"]


def _indep_support() -> dict:
    return {
        "support_type": "support_table",
        "alignment": "independent",
        "table": {
            "surface_id": "loan-notes",
            "stub_header": {"label": "Note"},
            "columns": [
                {"column_id": "a", "label": "A"},
                {"column_id": "b", "label": "B"},
            ],
            "rows": [
                {
                    "row_id": "r1",
                    "label": "Share",
                    "cells": {
                        "a": {"type": "text", "text": "Card-led"},
                        "b": {"type": "text", "text": "Stable"},
                    },
                }
            ],
        },
    }


def _cat_support() -> dict:
    return {
        "support_type": "support_table",
        "alignment": "category",
        "table": {
            "surface_id": "loan-cat",
            "stub_header": {"label": "Metric"},
            "columns": [
                {"column_id": "card", "label": "Card"},
                {"column_id": "consumer", "label": "Consumer"},
                {"column_id": "other", "label": "Other"},
            ],
            "rows": [
                {
                    "row_id": "mix",
                    "label": "Mix",
                    "cells": {
                        "card": {"type": "number", "value": "68", "format_id": "pct_0"},
                        "consumer": {"type": "number", "value": "12", "format_id": "pct_0"},
                        "other": {"type": "number", "value": "20", "format_id": "pct_0"},
                    },
                }
            ],
        },
    }


def _slice(slice_id: str, label: str, value: str, color: str | None = None) -> dict:
    rec = {
        "slice_id": slice_id,
        "label": label,
        "value": {"type": "number", "value": value, "format_id": "pct_0"},
    }
    if color is not None:
        rec["color"] = color
    return rec


def _dual_raw() -> dict:
    raw = _raw()
    left = deepcopy(_chart(raw))
    right = deepcopy(left)
    right["surface_id"] = "recv-mix"
    right["heading"] = "Receivables mix"
    right["slices"] = [
        _slice("consumer", "Consumer", "28"),
        _slice("small-biz", "Small biz", "14"),
        _slice("corp", "Corporate", "24"),
        _slice("other", "Other", "34"),
    ]
    raw["slides"][1]["layout_type"] = "dual_chart"
    raw["slides"][1]["title"] = "Mix pair"
    raw["slides"][1]["payload"] = {"charts": [left, right]}
    return raw


def _s27_dual_raw() -> dict:
    """Q4 s27 mix: 3-slice loans + 4-slice receivables, shared us/intl/sb."""
    raw = _raw()
    left = deepcopy(_chart(raw))
    left["surface_id"] = "s27-loans"
    left["heading"] = "Q4'21 Total Loan Mix"
    left["slices"] = [
        _slice("us", "U.S. Consumer", "68"),
        _slice("intl", "Intl. Consumer", "12"),
        _slice("sb", "Small Business", "20"),
    ]
    right = deepcopy(left)
    right["surface_id"] = "s27-rec"
    right["heading"] = "Q4'21 Card Member Receivables Mix"
    right["slices"] = [
        _slice("us", "U.S. Consumer", "28"),
        _slice("intl", "Intl. Consumer", "14"),
        _slice("corp", "Corporate Card", "24"),
        _slice("sb", "Small Business", "34"),
    ]
    raw["slides"][1]["layout_type"] = "dual_chart"
    raw["slides"][1]["title"] = "Worldwide mix"
    raw["slides"][1]["payload"] = {"charts": [left, right]}
    return raw


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_single_chart_donut_validates():
    result = validate_handoff(_raw(), strict=True)
    assert result.ok
    slide = result.deck.slides[1]
    assert isinstance(slide, SingleChartSlide)
    chart = slide.payload.chart
    assert isinstance(chart, DonutChartVisual)
    assert chart.chart_type == "donut"
    assert len(chart.slices) == 3
    assert slide.payload.support is None


def test_single_chart_pie_with_independent_support_validates():
    raw = _raw()
    raw["slides"][1]["payload"]["chart"]["chart_type"] = "pie"
    raw["slides"][1]["payload"]["support"] = _indep_support()
    result = validate_handoff(raw, strict=True)
    assert result.ok
    chart = result.deck.slides[1].payload.chart
    assert isinstance(chart, PieChartVisual)
    assert chart.chart_type == "pie"
    assert result.deck.slides[1].payload.support.alignment == "independent"


def test_dual_two_donuts_no_support_validates():
    result = validate_handoff(_dual_raw(), strict=True)
    assert result.ok
    panes = result.deck.slides[1].payload.charts
    assert panes[0].chart.chart_type == "donut"
    assert panes[1].chart.chart_type == "donut"
    assert len(panes[0].chart.slices) == 3
    assert len(panes[1].chart.slices) == 4
    assert result.deck.slides[1].payload.support is None
    assert panes[0].support is None and panes[1].support is None


@pytest.mark.parametrize("n", [1, 9])
def test_strict_rejects_slice_count(n: int):
    raw = _raw()
    slices = [_slice(f"s{i}", f"S{i}", "1") for i in range(n)]
    raw["slides"][1]["payload"]["chart"]["slices"] = slices
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_negative_value():
    raw = _raw()
    raw["slides"][1]["payload"]["chart"]["slices"][0]["value"]["value"] = "-1"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_heatmap_fields_on_pie():
    raw = _raw()
    chart = _chart(raw)
    chart["chart_type"] = "pie"
    chart["table_data"] = {
        "surface_id": "loan-heat",
        "columns": [{"column_id": "q1", "label": "Q1"}],
        "rows": [
            {
                "row_id": "us",
                "label": "US",
                "cells": {
                    "q1": {"type": "number", "value": "1", "format_id": "pct_0"}
                },
            }
        ],
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_category_aligned_support_on_pie():
    raw = _raw()
    raw["slides"][1]["payload"]["chart"]["chart_type"] = "pie"
    raw["slides"][1]["payload"]["support"] = _cat_support()
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_outlined_support_on_donut():
    raw = _raw()
    raw["slides"][1]["payload"]["support"] = {
        "support_type": "outlined_support",
        "table": {
            "surface_id": "loan-outlined",
            "stub_header": {"label": "ROE"},
            "columns": [
                {"column_id": "card", "label": "Card"},
                {"column_id": "consumer", "label": "Consumer"},
                {"column_id": "other", "label": "Other"},
            ],
            "rows": [
                {
                    "row_id": "roe",
                    "label": "ROE",
                    "cells": {
                        "card": {"type": "number", "value": "1", "format_id": "pct_0"},
                        "consumer": {"type": "number", "value": "2", "format_id": "pct_0"},
                        "other": {"type": "number", "value": "3", "format_id": "pct_0"},
                    },
                }
            ],
        },
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_pie_as_heatmap_table_data_standin():
    heat = json.loads(HEAT.read_text(encoding="utf-8"))
    heat["slides"][1]["payload"]["chart"]["chart_type"] = "pie"
    with pytest.raises(RendererValidationError):
        validate_handoff(heat, strict=True)


def test_strict_rejects_cartesian_fields_on_donut():
    raw = _raw()
    chart = _chart(raw)
    chart["category_axis"] = {"visible": True}
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)
    raw = _raw()
    _chart(raw)["chart_data"] = {
        "categories": [{"category_id": "a", "label": "A"}],
        "series": [{"series_id": "s", "name": "S", "values": ["1"]}],
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_measurements_on_donut():
    raw = _raw()
    _chart(raw)["measurements"] = [
        {
            "measurement_id": "m1",
            "role": "change",
            "series_id": "s",
            "from_category_id": "a",
            "to_category_id": "b",
            "value": "1",
            "format_id": "pct_0",
            "approximate": False,
        }
    ]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_line_fixture_still_validates():
    assert validate_handoff(json.loads(LINE.read_text(encoding="utf-8")), strict=True).ok


# ---------------------------------------------------------------------------
# Freeze / paint / mutations
# ---------------------------------------------------------------------------


def test_freeze_donut_cutout_and_pie_zero():
    donut = validate_handoff(_raw(), strict=True).deck.slides[1].payload.chart
    frozen = freeze_chart(donut, validate_handoff(_raw(), strict=True).deck.number_formats)
    assert frozen["chart_type"] == "donut"
    assert frozen["cutout"] != 0
    assert frozen["geometry"]["plot_w"] >= 320
    assert frozen["geometry"]["plot_h"] >= 240
    raw = _raw()
    raw["slides"][1]["payload"]["chart"]["chart_type"] = "pie"
    pie_deck = validate_handoff(raw, strict=True).deck
    pie = freeze_chart(pie_deck.slides[1].payload.chart, pie_deck.number_formats)
    assert pie["chart_type"] == "pie"
    assert pie["cutout"] == 0
    for sl in frozen["slices"]:
        assert contrast_ratio(sl["ink"], sl["color"]) >= 4.5


def test_mutation_donut_to_pie_still_renders(tmp_path: Path):
    raw = _raw()
    raw["slides"][1]["payload"]["chart"]["chart_type"] = "pie"
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(handoff, out, strict=True)["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-chart-type="pie"' in html
    assert '"cutout": 0' in html or '"cutout":0' in html
    assert "chartjs-canvas" in html
    assert "<noscript>" in html and "<svg" in html
    assert 'data-semantic-table="1"' in html
    assert "Card" in html and "68%" in html


def test_mutation_dual_no_support_paints_both(tmp_path: Path):
    raw = _dual_raw()
    assert "support" not in raw["slides"][1]["payload"]
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(handoff, out, strict=True)["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert html.count('class="dual-chart-pane"') == 2
    assert 'data-chart-surface="loan-mix"' in html
    assert 'data-chart-surface="recv-mix"' in html
    assert html.count("chartjs-canvas") == 2
    assert html.count('data-semantic-table="1"') == 2


def test_html_dual_stays_two_panes(tmp_path: Path):
    raw = _dual_raw()
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert html.count('class="dual-chart-pane"') == 2
    assert "category_axis" not in html
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    ready = next(r for r in meta["static_readiness"] if r["slide_number"] == 2)
    assert ready["semantic_table_present"] is True
    assert "chartjs" in ready["chart_painters"]
    assert "svg" in ready["chart_painters"]


def test_plan_preserves_plot_floor_on_dual():
    plan = plan_deck(validate_handoff(_dual_raw(), strict=True).deck, strict=True)
    charts = [s for s in plan.surfaces if s.surface_id in {"loan-mix", "recv-mix"}]
    assert len(charts) == 2
    for s in charts:
        g = s.chart_paint["geometry"]
        assert g["plot_w"] >= 320
        assert g["plot_h"] >= 240


def test_category_annotation_anchors_on_slice():
    raw = _raw()
    _chart(raw)["annotations"] = [
        {
            "annotation_id": "card-note",
            "role": "event",
            "text": "Card-led",
            "anchor": {"type": "category", "category_id": "card"},
        }
    ]
    result = validate_handoff(raw, strict=True)
    chart = result.deck.slides[1].payload.chart
    plan = freeze_chart(chart, result.deck.number_formats)
    assert plan["categories"] == []
    card = next(s for s in plan["slices"] if s["slice_id"] == "card")
    ann = next(a for a in plan["annotations"] if a["annotation_id"] == "card-note")
    assert ann["anchor_x"] == pytest.approx(card["lx"])
    g = plan["geometry"]
    assert ann["anchor_x"] != pytest.approx(g["pad_l"] + g["plot_w"] / 2)


def test_schema_export_includes_pie_donut():
    check_schema()
    schema = generate_schema()
    mapping = schema["$defs"]["SingleChartPayload"]["properties"]["chart"][
        "discriminator"
    ]["mapping"]
    assert mapping["pie"] == "#/$defs/PieChartVisual"
    assert mapping["donut"] == "#/$defs/DonutChartVisual"
    for name in ("PieChartVisual", "DonutChartVisual"):
        slices = schema["$defs"][name]["properties"]["slices"]
        assert slices["minItems"] == 2
        assert slices["maxItems"] == 8


def test_playwright_dual_donuts_equal_panes(tmp_path: Path):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(_dual_raw()), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(handoff, out, strict=True)["ok"] is True
    html_path = (out / "presentation.html").resolve()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(html_path.as_uri(), wait_until="networkidle")
        geom = page.evaluate(
            """() => {
              const panes = [...document.querySelectorAll('.dual-chart-pane')];
              const canvases = [...document.querySelectorAll('.chartjs-canvas')];
              const labels = [...document.querySelectorAll('.chart-svg text, .chart-label-overlay text')]
                .map((t) => (t.textContent || '').trim())
                .filter(Boolean);
              const axes = document.querySelectorAll('.chart-svg line.zero-line, .chart-svg .value-tick');
              const r = (el) => {
                const b = el.getBoundingClientRect();
                return {left: b.left, width: b.width, height: b.height};
              };
              return {
                paneCount: panes.length,
                canvasCount: canvases.length,
                panes: panes.map(r),
                plots: [...document.querySelectorAll('.chart-plot')].map(r),
                labels,
                axisCount: axes.length,
              };
            }"""
        )
        browser.close()
    assert geom["paneCount"] == 2
    assert geom["canvasCount"] == 2
    assert abs(geom["panes"][0]["width"] - geom["panes"][1]["width"]) <= 2
    for plot in geom["plots"]:
        assert plot["width"] >= 320
        assert plot["height"] >= 240
    joined = " ".join(geom["labels"])
    assert "Card" in joined or "68" in joined
    assert geom["axisCount"] == 0


def _slice_by_id(plan: dict, slice_id: str) -> dict:
    return next(s for s in plan["slices"] if s["slice_id"] == slice_id)


def _label_aabb(x: float, y: float, text: str, px: float, anchor: str) -> tuple[float, float, float, float]:
    """Same 0.55em width heuristic freeze_pie_donut uses for overflow."""
    w = max(20.0, len(text) * px * 0.55)
    if anchor == "start":
        left, right = x, x + w
    elif anchor == "end":
        left, right = x - w, x
    else:
        left, right = x - w / 2.0, x + w / 2.0
    return left, y - px / 2.0, right, y + px / 2.0


def _aabb_clears_disk(
    box: tuple[float, float, float, float], cx: float, cy: float, radius: float
) -> bool:
    left, top, right, bottom = box
    qx = min(max(cx, left), right)
    qy = min(max(cy, top), bottom)
    return math.hypot(qx - cx, qy - cy) >= radius


def test_dual_shared_slice_id_reuses_fill_across_panes():
    result = validate_handoff(_s27_dual_raw(), strict=True)
    assert result.ok
    plan = plan_deck(result.deck, strict=True)
    left = next(s for s in plan.surfaces if s.surface_id == "s27-loans").chart_paint
    right = next(s for s in plan.surfaces if s.surface_id == "s27-rec").chart_paint
    for sid in ("us", "intl", "sb"):
        assert _slice_by_id(left, sid)["color"] == _slice_by_id(right, sid)["color"]
    assert _slice_by_id(left, "sb")["color"] != _slice_by_id(right, "corp")["color"]


def test_identity_matches_slice_id_not_label():
    raw = _s27_dual_raw()
    left = raw["slides"][1]["payload"]["charts"][0]
    right = raw["slides"][1]["payload"]["charts"][1]
    left["slices"][2]["label"] = "Small Business"
    right["slices"][3]["slice_id"] = "sb-right"
    right["slices"][3]["label"] = "Small Business"
    result = validate_handoff(raw, strict=True)
    plan = plan_deck(result.deck, strict=True)
    left_p = next(s for s in plan.surfaces if s.surface_id == "s27-loans").chart_paint
    right_p = next(s for s in plan.surfaces if s.surface_id == "s27-rec").chart_paint
    assert _slice_by_id(left_p, "sb")["color"] != _slice_by_id(right_p, "sb-right")["color"]


def test_authored_slice_color_wins_sibling_omit():
    raw = _s27_dual_raw()
    right = raw["slides"][1]["payload"]["charts"][1]
    for sl in right["slices"]:
        if sl["slice_id"] == "sb":
            sl["color"] = "neutral"
    result = validate_handoff(raw, strict=True)
    plan = plan_deck(result.deck, strict=True)
    left = next(s for s in plan.surfaces if s.surface_id == "s27-loans").chart_paint
    right_p = next(s for s in plan.surfaces if s.surface_id == "s27-rec").chart_paint
    assert _slice_by_id(left, "sb")["color"] == _slice_by_id(right_p, "sb")["color"]
    cycle = resolve_series_colors("bar", count=3)
    assert _slice_by_id(left, "sb")["color"] != cycle[2]


def test_strict_rejects_conflicting_authored_slice_colors():
    raw = _s27_dual_raw()
    left = raw["slides"][1]["payload"]["charts"][0]
    right = raw["slides"][1]["payload"]["charts"][1]
    for sl in left["slices"]:
        if sl["slice_id"] == "sb":
            sl["color"] = "neutral"
    for sl in right["slices"]:
        if sl["slice_id"] == "sb":
            sl["color"] = "sky_blue"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_unknown_slice_color():
    raw = _raw()
    raw["slides"][1]["payload"]["chart"]["slices"][0]["color"] = "not-a-token"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_omit_color_single_donut_keeps_ordinal_cycle():
    result = validate_handoff(_raw(), strict=True)
    frozen = freeze_chart(result.deck.slides[1].payload.chart, result.deck.number_formats)
    cycle = resolve_series_colors("bar", count=3)
    assert [s["color"] for s in frozen["slices"]] == cycle
    schema = generate_schema()
    assert "color" in schema["$defs"]["ChartSlice"]["properties"]


def test_slice_names_paint_outside_ring():
    result = validate_handoff(_raw(), strict=True)
    frozen = freeze_chart(result.deck.slides[1].payload.chart, result.deck.number_formats)
    g = frozen["geometry"]
    radius = g["radius"]
    assert g["pad_l"] == PAD_R
    assert g["pad_r"] == PAD_R
    for sl in frozen["slices"]:
        dist = ((sl["name_x"] - g["cx"]) ** 2 + (sl["name_y"] - g["cy"]) ** 2) ** 0.5
        assert dist > radius + 1
        classes = {p["class"] for p in frozen["placements"] if p.get("slice_id") == sl["slice_id"]}
        assert "slice_name" in classes
    svg = paint_chart_svg(frozen)
    assert 'class="slice-name"' in svg
    assert 'class="slice-value"' in svg
    assert "Card 68%" not in svg
    assert ">Card<" in svg or ">Card</text>" in svg


def test_small_wedge_keeps_ordinary_values_floor():
    result = validate_handoff(_raw(), strict=True)
    frozen = freeze_chart(result.deck.slides[1].payload.chart, result.deck.number_formats)
    floor = frozen["role_sizes"]["ordinary_values"]
    assert floor >= 18
    intl = _slice_by_id(frozen, "consumer") if any(
        s["slice_id"] == "consumer" for s in frozen["slices"]
    ) else _slice_by_id(frozen, frozen["slices"][1]["slice_id"])
    # 12% Consumer wedge: name lives outside; type stays at the floor.
    g = frozen["geometry"]
    name_r = ((intl["name_x"] - g["cx"]) ** 2 + (intl["name_y"] - g["cy"]) ** 2) ** 0.5
    assert name_r > g["radius"]
    assert intl["value_inside"] is False
    card = _slice_by_id(frozen, "card")
    assert card["value_inside"] is True
    svg = paint_chart_svg(frozen)
    assert f'font-size="{floor}"' in svg
    assert 'font-size="12"' not in svg
    assert 'font-size="10"' not in svg


def test_small_upper_wedge_percent_stays_outside_with_name():
    raw = _raw()
    raw["slides"][1]["payload"]["chart"]["slices"] = [
        _slice("intl", "Intl. Consumer", "12"),
        _slice("us", "U.S. Consumer", "68"),
        _slice("sb", "Small Business", "20"),
    ]
    result = validate_handoff(raw, strict=True)
    frozen = freeze_chart(result.deck.slides[1].payload.chart, result.deck.number_formats)
    intl = _slice_by_id(frozen, "intl")
    g = frozen["geometry"]
    assert intl["value_inside"] is False
    val_r = ((intl["value_x"] - g["cx"]) ** 2 + (intl["value_y"] - g["cy"]) ** 2) ** 0.5
    name_r = ((intl["name_x"] - g["cx"]) ** 2 + (intl["name_y"] - g["cy"]) ** 2) ** 0.5
    pair = ((intl["value_x"] - intl["name_x"]) ** 2 + (intl["value_y"] - intl["name_y"]) ** 2) ** 0.5
    assert name_r > g["radius"]
    assert val_r > g["radius"]
    assert pair <= frozen["role_sizes"]["ordinary_values"] * 1.5


def test_long_24px_names_shrink_ring_instead_of_overflow():
    raw = _s27_dual_raw()
    for pane in raw["slides"][1]["payload"]["charts"]:
        pane["typography"] = {"ordinary_values": 24}
    result = validate_handoff(raw, strict=True)
    plan = plan_deck(result.deck, strict=True)
    for sid in ("s27-loans", "s27-rec"):
        frozen = next(s for s in plan.surfaces if s.surface_id == sid).chart_paint
        g = frozen["geometry"]
        assert frozen["role_sizes"]["ordinary_values"] == 24
        assert not frozen.get("slice_label_overflow")
        assert g["pad_l"] == g["pad_r"]
        assert g["pad_l"] > PAD_R
        assert g["plot_w"] >= 320
        assert g["plot_h"] >= 240
        for sl in frozen["slices"]:
            dist = ((sl["name_x"] - g["cx"]) ** 2 + (sl["name_y"] - g["cy"]) ** 2) ** 0.5
            assert dist > g["radius"] + 1
    omit = plan_deck(validate_handoff(_s27_dual_raw(), strict=True).deck, strict=True)
    omit_r = next(s for s in omit.surfaces if s.surface_id == "s27-loans").chart_paint["geometry"]["radius"]
    pin_r = next(s for s in plan.surfaces if s.surface_id == "s27-loans").chart_paint["geometry"]["radius"]
    assert pin_r < omit_r


def test_outside_name_aabb_does_not_intersect_ring():
    """#341: Corporate Card AABB must clear the disk even when the anchor is outside."""
    raw = _s27_dual_raw()
    for pane in raw["slides"][1]["payload"]["charts"]:
        pane["typography"] = {"ordinary_values": 24}
    plan = plan_deck(validate_handoff(raw, strict=True).deck, strict=True)
    frozen = next(s for s in plan.surfaces if s.surface_id == "s27-rec").chart_paint
    g = frozen["geometry"]
    px = frozen["role_sizes"]["ordinary_values"]
    assert px == 24
    assert not frozen.get("slice_label_overflow")
    painted_r = min(g["plot_w"], g["plot_h"]) / 2.0
    assert g["radius"] == painted_r
    corp = _slice_by_id(frozen, "corp")
    dist = math.hypot(corp["name_x"] - g["cx"], corp["name_y"] - g["cy"])
    assert dist > g["radius"] + 1
    box = _label_aabb(corp["name_x"], corp["name_y"], corp["label"], px, corp["name_anchor"])
    # Live SVG ink overshoots the 0.55em AABB by ~6px; require that much extra.
    assert _aabb_clears_disk(box, g["cx"], g["cy"], painted_r + 6)
    for sl in frozen["slices"]:
        name_box = _label_aabb(sl["name_x"], sl["name_y"], sl["label"], px, sl["name_anchor"])
        assert _aabb_clears_disk(name_box, g["cx"], g["cy"], painted_r)
        if sl["value_inside"]:
            val_r = math.hypot(sl["value_x"] - g["cx"], sl["value_y"] - g["cy"])
            assert val_r < g["radius"]
        else:
            val_box = _label_aabb(
                sl["value_x"], sl["value_y"], sl["visible"], px, sl["value_anchor"]
            )
            assert _aabb_clears_disk(val_box, g["cx"], g["cy"], painted_r)


def test_floor_hit_still_colliding_is_overflow():
    """#341: D47 floor + still overlapping the disk is slice_label_overflow, not a type shrink."""
    raw = _s27_dual_raw()
    rec = raw["slides"][1]["payload"]["charts"][1]
    rec["typography"] = {"ordinary_values": 24}
    rec["slices"] = [
        _slice("us", "X" * 80, "28"),
        _slice("intl", "Y" * 80, "14"),
        _slice("corp", "Z" * 80, "24"),
        _slice("sb", "W" * 80, "34"),
    ]
    result = validate_handoff(raw, strict=True)
    frozen = freeze_chart(
        result.deck.slides[1].payload.charts[1].chart,
        result.deck.number_formats,
        box_w=852,
        box_h=700,
    )
    g = frozen["geometry"]
    assert frozen["role_sizes"]["ordinary_values"] == 24
    assert g["plot_w"] >= 320
    assert g["plot_h"] >= 240
    assert frozen.get("slice_label_overflow") is True
