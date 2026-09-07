"""Renderer v3 geometric vs-2019 callouts on axis charts (#302).

Seams under test:
- closed kind enum + unique callout_id (fail closed)
- anchors reuse category / data_point / category_range (no pixels)
- stacked_bar elbow spanning two categories + chevron under one
- omit remains valid (dual_chart without callouts still strict-clean)
- pie/donut/heatmap reject the field
- plan freeze owns collision with stack totals (strict overflow, no overlap-and-ship)
- Chart.js overlay + SVG fallback share frozen geometry; face text escaped
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.charts import freeze_chart, paint_chart_svg
from impact_slides.renderer_v3.plan import plan_deck
from impact_slides.renderer_v3.schema_export import check_schema

ROOT = Path(__file__).resolve().parents[1]
STACKED = ROOT / "tests/fixtures/renderer_v3/minimal_stacked_bar.json"
LINE = ROOT / "tests/fixtures/renderer_v3/minimal_line_chart.json"
HEAT = ROOT / "tests/fixtures/renderer_v3/minimal_heatmap.json"
DONUT = ROOT / "tests/fixtures/renderer_v3/minimal_donut.json"
FIXTURE = ROOT / "tests/fixtures/renderer_v3/minimal_geometric_callouts.json"


def _s() -> dict:
    return json.loads(STACKED.read_text(encoding="utf-8"))


def _line() -> dict:
    return json.loads(LINE.read_text(encoding="utf-8"))


def _vis(raw: dict) -> dict:
    return next(
        s["payload"]["chart"]
        for s in raw["slides"]
        if s.get("layout_type") == "single_chart"
    )


def _elbow(*, callout_id: str = "vs-2019") -> dict:
    return {
        "callout_id": callout_id,
        "kind": "elbow_arrow",
        "text": "+6pp vs 2019",
        "anchor": {
            "type": "category_range",
            "from_category_id": "q1",
            "to_category_id": "q2",
        },
    }


def _chevron(*, callout_id: str = "refresh") -> dict:
    return {
        "callout_id": callout_id,
        "kind": "chevron",
        "text": "Refresh",
        "anchor": {"type": "category", "category_id": "q3"},
    }


def _quiet_stack(raw: dict) -> dict:
    """Hide in-plot labels so the happy-path elbow has a clear bar-top lane."""
    vis = _vis(raw)
    vis["display"] = {"stack_segments": "hide", "stack_totals": "hide", "series_identity": "legend"}
    vis.pop("auxiliary_series", None)
    return raw


def _dual_omit() -> dict:
    raw = _line()
    chart = deepcopy(raw["slides"][1]["payload"]["chart"])
    peer = deepcopy(chart)
    peer["surface_id"] = "vol-peer"
    peer["heading"] = "Peer billed"
    raw["slides"][1]["layout_type"] = "dual_chart"
    raw["slides"][1]["payload"] = {"charts": [chart, peer]}
    return raw


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_stacked_accepts_elbow_and_chevron():
    raw = _quiet_stack(_s())
    _vis(raw)["geometric_callouts"] = [_elbow(), _chevron()]
    result = validate_handoff(raw, strict=True)
    assert result.ok
    chart = result.deck.slides[1].payload.chart
    assert [c.callout_id for c in chart.geometric_callouts] == ["vs-2019", "refresh"]
    assert chart.geometric_callouts[0].kind == "elbow_arrow"
    assert chart.geometric_callouts[0].anchor.type == "category_range"
    assert chart.geometric_callouts[1].kind == "chevron"


def test_omit_callouts_dual_chart_still_clean(tmp_path: Path):
    raw = _dual_omit()
    assert "geometric_callouts" not in json.dumps(raw)
    result = validate_handoff(raw, strict=True)
    assert result.ok
    plan_deck(result.deck, strict=True)
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(str(handoff), str(out), strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert html.count('class="dual-chart-pane"') == 2
    assert "geometric-callout" not in html


def test_strict_rejects_unknown_kind():
    raw = _quiet_stack(_s())
    bad = _elbow()
    bad["kind"] = "fireworks"
    _vis(raw)["geometric_callouts"] = [bad]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_colliding_ids():
    raw = _quiet_stack(_s())
    _vis(raw)["geometric_callouts"] = [_elbow(), _chevron(callout_id="vs-2019")]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_callout_on_donut():
    raw = json.loads(DONUT.read_text(encoding="utf-8"))
    vis = _vis(raw)
    vis["geometric_callouts"] = [
        {
            "callout_id": "mix-chip",
            "kind": "chevron",
            "text": "Card",
            "anchor": {"type": "category", "category_id": "card"},
        }
    ]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_callout_on_heatmap():
    raw = json.loads(HEAT.read_text(encoding="utf-8"))
    vis = _vis(raw)
    vis["geometric_callouts"] = [_chevron()]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_elbow_without_range():
    raw = _quiet_stack(_s())
    bad = _elbow()
    bad["anchor"] = {"type": "category", "category_id": "q1"}
    _vis(raw)["geometric_callouts"] = [bad]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_fixture_validates_and_renders(tmp_path: Path):
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    result = validate_handoff(raw, strict=True)
    assert result.ok
    out = tmp_path / "out"
    render_deck(str(FIXTURE), str(out), strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-callout-id="vs-2019"' in html
    assert 'data-kind="elbow_arrow"' in html
    assert 'data-callout-id="refresh"' in html
    assert 'data-kind="chevron"' in html
    assert "+6pp vs 2019" in html
    assert "Refresh" in html


# ---------------------------------------------------------------------------
# Freeze / paint / collision
# ---------------------------------------------------------------------------


def test_freeze_paints_elbow_span_and_chevron():
    raw = _quiet_stack(_s())
    _vis(raw)["geometric_callouts"] = [_elbow(), _chevron()]
    result = validate_handoff(raw, strict=True)
    chart = result.deck.slides[1].payload.chart
    frozen = freeze_chart(chart, result.deck.number_formats)
    placed = {c["callout_id"]: c for c in frozen["geometric_callouts"]}
    elbow = placed["vs-2019"]
    chev = placed["refresh"]
    assert elbow["kind"] == "elbow_arrow"
    assert elbow["from_category_id"] == "q1"
    assert elbow["to_category_id"] == "q2"
    assert elbow["x1"] > elbow["x0"]
    assert chev["kind"] == "chevron"
    assert chev["category_id"] == "q3"
    assert frozen.get("geometric_callout_overflow") is not True

    svg = paint_chart_svg(frozen)
    assert 'data-callout-id="vs-2019"' in svg
    assert 'data-kind="elbow_arrow"' in svg
    assert 'data-callout-id="refresh"' in svg
    assert "+6pp vs 2019" in svg
    assert "Refresh" in svg


def test_collision_with_stack_totals_strict_overflows():
    raw = _s()
    _vis(raw)["geometric_callouts"] = [_elbow()]
    result = validate_handoff(raw, strict=True)
    with pytest.raises(RendererValidationError) as excinfo:
        plan_deck(result.deck, strict=True)
    codes = [e.code for e in excinfo.value.events]
    assert "plan.unresolved_overflow" in codes


def test_face_text_escaped(tmp_path: Path):
    raw = _quiet_stack(_s())
    evil = _elbow()
    evil["text"] = '<script>alert(1)</script>'
    _vis(raw)["geometric_callouts"] = [evil]
    result = validate_handoff(raw, strict=True)
    frozen = freeze_chart(result.deck.slides[1].payload.chart, result.deck.number_formats)
    svg = paint_chart_svg(frozen)
    assert "<script>alert(1)</script>" not in svg
    assert "&lt;script&gt;" in svg


def test_omit_does_not_emit_callout_chrome():
    raw = _s()
    result = validate_handoff(raw, strict=True)
    frozen = freeze_chart(result.deck.slides[1].payload.chart, result.deck.number_formats)
    assert frozen.get("geometric_callouts") in (None, [])
    svg = paint_chart_svg(frozen)
    assert "geometric-callout" not in svg


def test_schema_export_includes_geometric_callout():
    check_schema()
    schema = json.loads(
        (ROOT / "impact_slides/renderer_v3/schema/handoff_schema_v1.json").read_text(
            encoding="utf-8"
        )
    )
    defs = schema["$defs"]
    assert "GeometricCallout" in defs
    kinds = defs["GeometricCallout"]["properties"]["kind"]
    enum = kinds.get("enum") or kinds.get("const")
    if "anyOf" in kinds:
        enum = [item["const"] for item in kinds["anyOf"] if "const" in item]
    assert set(enum) == {"elbow_arrow", "chevron", "band"}
    stacked = defs["StackedBarChartVisual"]["properties"]
    items = stacked["geometric_callouts"]["anyOf"][0]["items"]
    assert items["$ref"] == "#/$defs/GeometricCallout"
    for excluded in ("PieChartVisual", "DonutChartVisual", "HeatmapVisual"):
        assert "geometric_callouts" not in defs[excluded]["properties"]
