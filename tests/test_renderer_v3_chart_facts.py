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
from impact_slides.renderer_v3.charts import freeze_chart, paint_chart_svg, paint_semantic_table
from impact_slides.renderer_v3.schema_export import check_schema

ROOT = Path(__file__).resolve().parents[1]
LINE = ROOT / "tests/fixtures/renderer_v3/minimal_line_chart.json"
HEAT = ROOT / "tests/fixtures/renderer_v3/minimal_heatmap.json"
STACKED = ROOT / "tests/fixtures/renderer_v3/minimal_stacked_bar.json"


def _line() -> dict:
    return json.loads(LINE.read_text(encoding="utf-8"))


def _heat() -> dict:
    return json.loads(HEAT.read_text(encoding="utf-8"))


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


def test_schema_export_includes_fact_models():
    # Drift gate must stay green after model extension.
    check_schema()
    schema = json.loads(
        (ROOT / "impact_slides/renderer_v3/schema/handoff_schema_v1.json").read_text(
            encoding="utf-8"
        )
    )
    blob = json.dumps(schema)
    assert "context_labels" in blob
    assert "annotations" in blob
    assert "measurements" in blob
    assert "context_id" in blob
    assert "annotation_id" in blob
    assert "measurement_id" in blob
