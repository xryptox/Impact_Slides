"""Renderer v3 pie/donut ChartVisual (#287).

Seams under test:
- typed pie/donut slice visual (2–8 slices, semantic values, no cartesian axes)
- single_chart + dual_chart envelopes (heatmap still forbidden on dual)
- Chart.js doughnut + noscript SVG radial + D247 semantic table
- D10/D47 320×240 plot floor; D304 navy ink on low-contrast slices
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.charts import freeze_chart
from impact_slides.renderer_v3.models import DonutChartVisual, PieChartVisual, SingleChartSlide
from impact_slides.renderer_v3.plan import plan_deck
from impact_slides.renderer_v3.schema_export import check_schema, generate_schema
from impact_slides.renderer_v3.theme import contrast_ratio

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


def _slice(slice_id: str, label: str, value: str) -> dict:
    return {
        "slice_id": slice_id,
        "label": label,
        "value": {"type": "number", "value": value, "format_id": "pct_0"},
    }


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
