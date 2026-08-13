"""Renderer v3 structured chart facts + collision-owned chrome (#188).

Seams under test:
- context_labels / annotations / measurements on chart envelopes (D29/D147/D148/D168/D232–D234/D296–D298)
- family gates (coverage/aux/groups already family-local; heatmap forbids measurements + data_point)
- frozen plan shared by Chart.js chrome overlay + noscript SVG (D248)
- D247 semantic-table facts retain complete authored semantics even when chrome is suppressed
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.plan import plan_deck
from impact_slides.renderer_v3.charts import (
    freeze_chart,
    freeze_heatmap,
    paint_chart_svg,
    paint_heatmap_html,
    paint_semantic_table,
)
from impact_slides.renderer_v3.schema_export import check_schema

ROOT = Path(__file__).resolve().parents[1]
LINE = ROOT / "tests/fixtures/renderer_v3/minimal_line_chart.json"
HEAT = ROOT / "tests/fixtures/renderer_v3/minimal_heatmap.json"
STACKED = ROOT / "tests/fixtures/renderer_v3/minimal_stacked_bar.json"
WATERFALL = ROOT / "tests/fixtures/renderer_v3/minimal_waterfall.json"
HBAR = ROOT / "tests/fixtures/renderer_v3/minimal_horizontal_bar.json"


def _line() -> dict:
    return json.loads(LINE.read_text(encoding="utf-8"))


def _heat() -> dict:
    return json.loads(HEAT.read_text(encoding="utf-8"))


def _waterfall() -> dict:
    return json.loads(WATERFALL.read_text(encoding="utf-8"))


def _hbar() -> dict:
    return json.loads(HBAR.read_text(encoding="utf-8"))


def _vis(raw: dict) -> dict:
    return next(
        s["payload"]["primary_visual"]
        for s in raw["slides"]
        if s.get("layout_type") == "single_chart"
    )


def _facts_on_line(raw: dict) -> None:
    vis = _vis(raw)
    vis["context_labels"] = [
        {
            "context_id": "gs-yoy",
            "label": "G&S",
            "value": {"type": "number", "value": "3.0", "format_id": "pct_1"},
            "short_label": "G&S",
        }
    ]
    vis["annotations"] = [
        {
            "annotation_id": "evt-q2",
            "role": "event",
            "text": "Promo wave",
            "anchor": {"type": "category", "category_id": "q2"},
        },
        {
            "annotation_id": "exp-all",
            "role": "explanation",
            "text": "Soft Q3 gap",
            "anchor": {"type": "chart"},
        },
    ]
    vis["measurements"] = [
        {
            "measurement_id": "chg-us",
            "role": "change",
            "series_id": "us",
            "from_category_id": "q1",
            "to_category_id": "q4",
            "value": "1.8",
            "format_id": "pct_1",
            "approximate": False,
        }
    ]


# ---------------------------------------------------------------------------
# Validation / family gates
# ---------------------------------------------------------------------------


def test_line_accepts_structured_facts():
    raw = _line()
    _facts_on_line(raw)
    result = validate_handoff(raw, strict=True)
    assert result.ok
    chart = result.deck.slides[1].payload.primary_visual
    assert chart.context_labels and chart.context_labels[0].context_id == "gs-yoy"
    assert len(chart.annotations) == 2
    assert chart.measurements[0].role == "change"


def test_strict_rejects_event_with_chart_anchor():
    raw = _line()
    _facts_on_line(raw)
    _vis(raw)["annotations"][0]["role"] = "event"
    _vis(raw)["annotations"][0]["anchor"] = {"type": "chart"}
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_unknown_annotation_category():
    raw = _line()
    _facts_on_line(raw)
    _vis(raw)["annotations"][0]["anchor"]["category_id"] = "nope"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_measurement_null_endpoint():
    raw = _line()
    _facts_on_line(raw)
    # us series has null at q3 — range q2→q3 has null endpoint for from? q2 is finite.
    # Use q3 as to_category where us is null.
    _vis(raw)["measurements"][0]["from_category_id"] = "q2"
    _vis(raw)["measurements"][0]["to_category_id"] = "q3"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_duplicate_measurement_key():
    raw = _line()
    _facts_on_line(raw)
    m = deepcopy(_vis(raw)["measurements"][0])
    m["measurement_id"] = "chg-us-2"
    _vis(raw)["measurements"].append(m)
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_unresolved_context_format():
    raw = _line()
    _facts_on_line(raw)
    _vis(raw)["context_labels"][0]["value"]["format_id"] = "missing-fmt"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_unresolved_measurement_format():
    raw = _line()
    _facts_on_line(raw)
    _vis(raw)["measurements"][0]["format_id"] = "missing-fmt"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_duplicate_identity_emits_plan_diagnostic():
    raw = _line()
    _facts_on_line(raw)
    _vis(raw)["context_labels"] = [
        {
            "context_id": "dup-us",
            "label": "US",
            "value": {"type": "text", "text": "US"},
        }
    ]
    result = validate_handoff(raw, strict=True)
    chart = result.deck.slides[1].payload.primary_visual
    plan = freeze_chart(chart, result.deck.number_formats)
    codes = [d["code"] for d in plan["fact_chrome"]["diagnostics"]]
    assert "plan.chrome_deduplicated" in codes


def test_heatmap_accepts_context_and_category_annotation():
    raw = _heat()
    vis = _vis(raw)
    # column ids from fixture
    cols = [c["column_id"] for c in vis["table_data"]["columns"]]
    vis["context_labels"] = [
        {
            "context_id": "note",
            "label": "Coverage",
            "value": {"type": "text", "text": "Board view"},
        }
    ]
    vis["annotations"] = [
        {
            "annotation_id": "col-note",
            "role": "explanation",
            "text": "Peak column",
            "anchor": {"type": "category", "category_id": cols[0]},
        }
    ]
    assert validate_handoff(raw, strict=True).ok


def test_heatmap_facts_paint_once_inside_surface():
    raw = _heat()
    vis = _vis(raw)
    cols = [c["column_id"] for c in vis["table_data"]["columns"]]
    vis["context_labels"] = [
        {
            "context_id": "note",
            "label": "Coverage",
            "value": {"type": "text", "text": "Board view"},
        }
    ]
    vis["annotations"] = [
        {
            "annotation_id": "col-note",
            "role": "explanation",
            "text": "Peak column",
            "anchor": {"type": "category", "category_id": cols[0]},
        }
    ]
    result = validate_handoff(raw, strict=True)
    chart = result.deck.slides[1].payload.primary_visual
    html = "".join(paint_heatmap_html(freeze_heatmap(chart, result.deck.number_formats)))
    body_open = html.find('data-chart-surface=')
    body_close = html.rfind("</div>")
    owned = html[body_open:body_close]
    leftover = html[body_close:]
    assert 'data-context-id="note"' in owned
    assert 'data-annotation-id="col-note"' in owned
    assert leftover.count("Board view") == 0
    assert leftover.count("Peak column") == 0
    bare = validate_handoff(_heat(), strict=True)
    bare_h = next(
        s._chrome_h for s in plan_deck(bare.deck, strict=True).surfaces if s.role == "heatmap"
    )
    fact_h = next(
        s._chrome_h for s in plan_deck(result.deck, strict=True).surfaces if s.role == "heatmap"
    )
    assert fact_h > bare_h
    assert html.count('data-context-id="note"') == 1
    assert html.count('data-annotation-id="col-note"') == 1
    ctx = html[html.find('data-context-id="note"') : html.find("</div>", html.find('data-context-id="note"'))]
    ann = html[html.find('data-annotation-id="col-note"') : html.find("</div>", html.find('data-annotation-id="col-note"'))]
    assert 'aria-hidden="true"' in ctx
    assert 'aria-hidden="true"' in ann
    assert 'class="chart-facts visually-hidden"' in owned


def test_heatmap_forbids_measurements():
    raw = _heat()
    vis = _vis(raw)
    cols = [c["column_id"] for c in vis["table_data"]["columns"]]
    vis["measurements"] = [
        {
            "measurement_id": "bad",
            "role": "change",
            "series_id": "waterfall",
            "from_category_id": cols[0],
            "to_category_id": cols[-1] if len(cols) > 1 else cols[0],
            "value": "1.0",
            "format_id": next(iter(raw["number_formats"])),
            "approximate": False,
        }
    ]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_heatmap_forbids_data_point_anchor():
    raw = _heat()
    vis = _vis(raw)
    cols = [c["column_id"] for c in vis["table_data"]["columns"]]
    rows = [r["row_id"] for r in vis["table_data"]["rows"]]
    vis["annotations"] = [
        {
            "annotation_id": "dp",
            "role": "event",
            "text": "cell",
            "anchor": {
                "type": "data_point",
                "series_id": rows[0],
                "category_id": cols[0],
            },
        }
    ]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_stacked_still_owns_coverage_only():
    raw = json.loads(STACKED.read_text(encoding="utf-8"))
    assert validate_handoff(raw, strict=True).ok
    vis = _vis(raw)
    assert "coverage_callout" in vis


# ---------------------------------------------------------------------------
# Freeze / paint / semantic table
# ---------------------------------------------------------------------------


def test_freeze_retains_facts_and_shared_chrome():
    raw = _line()
    _facts_on_line(raw)
    result = validate_handoff(raw, strict=True)
    chart = result.deck.slides[1].payload.primary_visual
    plan = freeze_chart(chart, result.deck.number_formats)

    assert len(plan["context_labels"]) == 1
    assert plan["context_labels"][0]["context_id"] == "gs-yoy"
    assert plan["context_labels"][0]["value_visible"]
    assert len(plan["annotations"]) == 2
    assert {a["annotation_id"] for a in plan["annotations"]} == {"evt-q2", "exp-all"}
    assert all("candidates" in a for a in plan["annotations"])
    assert len(plan["measurements"]) == 1
    m = plan["measurements"][0]
    assert m["measurement_id"] == "chg-us"
    assert m["value_visible"]
    # Authored value is never recomputed from endpoints (q1=3.2, q4=5.0 → 1.8 authored).
    assert m["text"] == plan["measurements"][0]["value_visible"] or m["text"].endswith(
        m["value_visible"]
    )

    facts = plan["semantic_table"]["facts"]
    assert any(f.startswith("Context G&S:") for f in facts)
    assert any("Promo wave" in f for f in facts)
    assert any(f.startswith("Change on us") for f in facts)

    svg = paint_chart_svg(plan)
    assert 'data-context-id="gs-yoy"' in svg
    assert 'data-annotation-id="evt-q2"' in svg
    assert 'data-measurement-id="chg-us"' in svg
    # Chart.js path uses the same chrome overlay plan (D248).
    chrome = paint_chart_svg(plan, marks=False)
    assert 'data-context-id="gs-yoy"' in chrome
    assert 'data-annotation-id="evt-q2"' in chrome

    table_html = paint_semantic_table(plan)
    assert "Context G&S" in table_html
    assert "Promo wave" in table_html


def test_duplicate_identity_context_suppresses_chrome_keeps_fact():
    raw = _line()
    _facts_on_line(raw)
    # Series name "US" duplicated as context label+text value → chrome only suppressed.
    _vis(raw)["context_labels"] = [
        {
            "context_id": "dup-us",
            "label": "US",
            "value": {"type": "text", "text": "US"},
        }
    ]
    result = validate_handoff(raw, strict=True)
    chart = result.deck.slides[1].payload.primary_visual
    plan = freeze_chart(chart, result.deck.number_formats)
    assert plan["context_labels"] == [] or all(
        p.get("suppressed") for p in plan.get("context_labels") or []
    )
    assert any(f.startswith("Context US:") for f in plan["semantic_table"]["facts"])
    svg = paint_chart_svg(plan)
    assert 'data-context-id="dup-us"' not in svg


def test_waterfall_data_point_annotation_anchors_to_step():
    raw = _waterfall()
    vis = _vis(raw)
    vis["annotations"] = [
        {
            "annotation_id": "price-note",
            "role": "explanation",
            "text": "Price lift",
            "anchor": {
                "type": "data_point",
                "series_id": "waterfall",
                "category_id": "price",
            },
        }
    ]
    result = validate_handoff(raw, strict=True)
    chart = result.deck.slides[1].payload.primary_visual
    plan = freeze_chart(chart, result.deck.number_formats)
    assert plan["points"], "waterfall freeze must emit anchor points"
    ann = next(a for a in plan["annotations"] if a["annotation_id"] == "price-note")
    pt = next(
        p
        for p in plan["points"]
        if p["series_id"] == "waterfall" and p["category_id"] == "price"
    )
    assert pt["finite"] is True
    assert ann["anchor_x"] == pytest.approx(float(pt["x"]))
    assert ann["anchor_y"] == pytest.approx(float(pt["y"]) - 16)
    svg = paint_chart_svg(plan)
    assert 'data-annotation-id="price-note"' in svg


def test_duplicate_identity_annotation_suppresses_chrome_keeps_fact():
    raw = _line()
    _facts_on_line(raw)
    # Series name "US" duplicated as annotation text → chrome only suppressed.
    _vis(raw)["annotations"] = [
        {
            "annotation_id": "dup-us-ann",
            "role": "explanation",
            "text": "US",
            "anchor": {"type": "chart"},
        }
    ]
    result = validate_handoff(raw, strict=True)
    chart = result.deck.slides[1].payload.primary_visual
    plan = freeze_chart(chart, result.deck.number_formats)
    assert all(a["annotation_id"] != "dup-us-ann" for a in plan.get("annotations") or [])
    assert any("Explanation: US" in f for f in plan["semantic_table"]["facts"])
    codes = [d["code"] for d in plan["fact_chrome"]["diagnostics"]]
    assert "plan.chrome_deduplicated" in codes
    svg = paint_chart_svg(plan)
    assert 'data-annotation-id="dup-us-ann"' not in svg


def test_context_with_distinct_value_not_duplicate():
    raw = _line()
    _facts_on_line(raw)
    _vis(raw)["context_labels"] = [
        {
            "context_id": "us-note",
            "label": "US",
            "value": {"type": "number", "value": "5.0", "format_id": "pct_1"},
        }
    ]
    result = validate_handoff(raw, strict=True)
    chart = result.deck.slides[1].payload.primary_visual
    plan = freeze_chart(chart, result.deck.number_formats)
    assert len(plan["context_labels"]) == 1
    assert plan["context_labels"][0]["suppressed"] is False


def test_render_deck_includes_fact_chrome(tmp_path: Path):
    raw = _line()
    _facts_on_line(raw)
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(str(handoff), str(out), strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-context-id="gs-yoy"' in html
    assert 'data-annotation-id="evt-q2"' in html
    assert 'data-measurement-id="chg-us"' in html
    assert "Context G&S" in html


def test_fact_chrome_diagnostics_reach_run_meta_and_dom(tmp_path: Path):
    raw = _line()
    _facts_on_line(raw)
    _vis(raw)["context_labels"] = [
        {
            "context_id": "dup-us",
            "label": "US",
            "value": {"type": "text", "text": "US"},
        }
    ]
    result = validate_handoff(raw, strict=True)
    deck_plan = plan_deck(result.deck, strict=True)
    assert any(e.code == "plan.chrome_deduplicated" for e in deck_plan.events)
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(str(handoff), str(out), strict=True)
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert any(e["code"] == "plan.chrome_deduplicated" for e in meta["events"])
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert "plan.chrome_deduplicated" in html


def test_d96_norm_dedupes_trailing_punct_identity():
    raw = _line()
    _facts_on_line(raw)
    _vis(raw)["annotations"] = [
        {
            "annotation_id": "us-colon",
            "role": "explanation",
            "text": "US:",
            "anchor": {"type": "chart"},
        }
    ]
    result = validate_handoff(raw, strict=True)
    chart = result.deck.slides[1].payload.primary_visual
    plan = freeze_chart(chart, result.deck.number_formats)
    assert all(a["annotation_id"] != "us-colon" for a in plan.get("annotations") or [])
    assert any("Explanation: US:" in f for f in plan["semantic_table"]["facts"])
    codes = [d["code"] for d in plan["fact_chrome"]["diagnostics"]]
    assert "plan.chrome_deduplicated" in codes
    svg = paint_chart_svg(plan)
    assert 'data-annotation-id="us-colon"' not in svg


def test_hbar_category_and_measurement_use_row_y():
    raw = _hbar()
    vis = _vis(raw)
    vis["annotations"] = [
        {
            "annotation_id": "uk-note",
            "role": "event",
            "text": "UK row",
            "anchor": {"type": "category", "category_id": "uk"},
        }
    ]
    vis["measurements"] = [
        {
            "measurement_id": "us-jp",
            "role": "change",
            "series_id": "share",
            "from_category_id": "us",
            "to_category_id": "jp",
            "value": "7.3",
            "format_id": "pct_1",
            "approximate": False,
        }
    ]
    result = validate_handoff(raw, strict=True)
    chart = result.deck.slides[1].payload.primary_visual
    plan = freeze_chart(chart, result.deck.number_formats)
    cats = {c["category_id"]: c for c in plan["categories"]}
    ann = next(a for a in plan["annotations"] if a["annotation_id"] == "uk-note")
    assert ann["anchor_y"] == pytest.approx(float(cats["uk"]["y"]))
    assert ann["anchor_y"] != pytest.approx(float(plan["geometry"]["pad_t"]) + 14)
    meas = next(m for m in plan["measurements"] if m["measurement_id"] == "us-jp")
    mid_y = (float(cats["us"]["y"]) + float(cats["jp"]["y"])) / 2
    assert meas["y1"] == pytest.approx(float(cats["us"]["y"]))
    assert meas["y2"] == pytest.approx(float(cats["jp"]["y"]))
    assert meas["y"] == pytest.approx(mid_y) or meas["class"] in (
        "exterior",
        "below_plot",
    )


def test_unplaceable_fact_omits_chrome_keeps_fact():
    raw = _line()
    vis = _vis(raw)
    vis.pop("context_labels", None)
    vis.pop("measurements", None)
    vis["annotations"] = [
        {
            "annotation_id": f"pile-{i}",
            "role": "explanation",
            "text": f"Note {i} extra long collision text",
            "anchor": {"type": "chart"},
        }
        for i in range(8)
    ]
    result = validate_handoff(raw, strict=True)
    chart = result.deck.slides[1].payload.primary_visual
    plan = freeze_chart(chart, result.deck.number_formats)
    placed = {a["annotation_id"] for a in plan["annotations"]}
    omitted = [f"pile-{i}" for i in range(8) if f"pile-{i}" not in placed]
    assert omitted
    facts = plan["semantic_table"]["facts"]
    for i in range(8):
        assert any(f"Note {i}" in f for f in facts)
    codes = [d["code"] for d in plan["fact_chrome"]["diagnostics"]]
    assert "plan.label_suppressed" in codes
    svg = paint_chart_svg(plan)
    for aid in omitted:
        assert f'data-annotation-id="{aid}"' not in svg


def test_context_labels_relocate_as_complete_block():
    raw = _line()
    vis = _vis(raw)
    vis.pop("annotations", None)
    vis.pop("measurements", None)
    vis["context_labels"] = [
        {
            "context_id": f"ctx-{i}",
            "label": f"Gross and Services Mix Extra {i}",
            "short_label": "WWWWWWWWWW",
            "value": {"type": "number", "value": "3.0", "format_id": "pct_1"},
        }
        for i in range(4)
    ]
    result = validate_handoff(raw, strict=True)
    chart = result.deck.slides[1].payload.primary_visual
    plan = freeze_chart(chart, result.deck.number_formats)
    placed = plan["context_labels"]
    assert {p["context_id"] for p in placed} == {f"ctx-{i}" for i in range(4)}
    classes = {p["class"] for p in placed}
    assert classes == {"below_plot"}
    codes = [d["code"] for d in plan["fact_chrome"]["diagnostics"]]
    assert "plan.label_suppressed" not in codes
    assert "plan.surface_relocated" in codes
    assert "plan.short_label_used" in codes
    ys = [float(p["y"]) for p in placed]
    assert len(set(ys)) == 4
    px = float(plan["role_sizes"]["context_labels"])
    bottoms = [float(p["y"]) + px * 1.35 for p in placed]
    g = plan["geometry"]
    assert max(bottoms) <= float(g["view_h"])
    assert float(g["view_h"]) == pytest.approx(
        float(g["pad_t"]) + float(g["plot_h"]) + float(g["pad_b"])
    )
    facts = plan["semantic_table"]["facts"]
    for i in range(4):
        assert any(f"Gross and Services Mix Extra {i}" in f for f in facts)
    svg = paint_chart_svg(plan)
    for i in range(4):
        assert f'data-context-id="ctx-{i}"' in svg


def test_schema_export_includes_fact_models():
    check_schema()
    schema = json.loads(
        (ROOT / "impact_slides/renderer_v3/schema/handoff_schema_v1.json").read_text(
            encoding="utf-8"
        )
    )
    defs = schema["$defs"]
    assert defs["ContextLabel"]["properties"]["context_id"]["type"] == "string"
    assert defs["ChartAnnotation"]["properties"]["annotation_id"]["type"] == "string"
    assert defs["ChartMeasurement"]["properties"]["measurement_id"]["type"] == "string"
    visuals = (
        "LineChartVisual",
        "GroupedBarChartVisual",
        "HorizontalBarChartVisual",
        "StackedBarChartVisual",
        "ComboChartVisual",
        "WaterfallChartVisual",
        "HeatmapVisual",
    )
    for name in visuals:
        props = defs[name]["properties"]
        ctx_items = props["context_labels"]["anyOf"][0]["items"]
        ann_items = props["annotations"]["anyOf"][0]["items"]
        assert ctx_items["$ref"] == "#/$defs/ContextLabel"
        assert ann_items["$ref"] == "#/$defs/ChartAnnotation"
        if name == "HeatmapVisual":
            assert "measurements" not in props
        else:
            meas_items = props["measurements"]["anyOf"][0]["items"]
            assert meas_items["$ref"] == "#/$defs/ChartMeasurement"
