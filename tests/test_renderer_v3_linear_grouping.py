"""Renderer v3 linear + grouping compositions (#192).

Seams under test:
- process_flow / timeline / layered_architecture / data_pipeline models
- authored order, grouping, chronology, transfer semantics preserved
- plan fixed D60 type + non-strict accessible fallbacks
- paint identity: cards, connectors omitted on fallback, no inferred edges
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.plan import (
    _line_box,
    _linear_fit_detail,
    _text_width,
    _wrap_label_lines,
    plan_deck,
)
from impact_slides.renderer_v3.schema_export import check_schema

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/renderer_v3/linear_grouping_compositions.json"


def _raw() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


# Published CSS box contract for linear compositions (publish.py stylesheet):
# card padding 16px, meta/h3/h4 margin-bottom 4px, step/stage column gap 8px,
# container + arch-components gap 16px, connectors 24px, layered gap 20px.
_L_PAD = 16
_L_MARGIN = 4
_L_GAP = 16
_L_CONN = 24
_L_INNER = 8
_L_LAYER = 20


def _deck(slides: list[dict]) -> dict:
    raw = _raw()
    return {
        "meta": raw["meta"],
        "sections": raw["sections"],
        "number_formats": raw["number_formats"],
        "evidence_registry": raw["evidence_registry"],
        "slides": slides,
    }


def _linear_surfaces(deck: dict, *, strict: bool) -> list:
    result = validate_handoff(deck, strict=strict)
    plan = plan_deck(result.deck, strict=strict)
    return [sp for sp in plan.surfaces if sp._linear_spec is not None]


def _painted_linear_height(sp) -> float:
    """Height the published CSS box model paints for a frozen linear plan."""
    spec = sp._linear_spec
    kind = spec["kind"]
    box_w = sp._box_w
    heading_px = sp.role_sizes["heading"]
    detail_px = sp.role_sizes["detail"]
    meta_px = sp.role_sizes["meta"]

    def lines(text: str, px: int, width: float, *, strong: bool = False) -> int:
        return len(_wrap_label_lines(text, px, width, strong=strong))

    def card(heading, detail, h_px, d_px, inner, meta=None) -> float:
        h = 2 * _L_PAD + _L_MARGIN + lines(heading, h_px, inner, strong=True) * _line_box(h_px)
        if meta is not None:
            h += _L_MARGIN + lines(str(meta), meta_px, inner, strong=True) * _line_box(meta_px)
        if detail:
            h += lines(detail, d_px, inner) * _line_box(d_px)
        return h

    if kind in ("process_flow", "timeline"):
        items = spec["items"]
        n = len(items)

        def item_card(it, inner) -> float:
            meta = str(it.get("ordinal", "")) if kind == "process_flow" else it.get("time_label")
            return card(it["heading"], it.get("detail"), heading_px, detail_px, inner, meta=meta)

        if spec.get("orientation", "horizontal") == "horizontal":
            step_w = (box_w - (n - 1) * (2 * _L_GAP + _L_CONN)) / n
            return max(item_card(it, step_w - 2 * _L_PAD) for it in items)
        inner = box_w - 2 * _L_PAD
        return sum(item_card(it, inner) for it in items) + (n - 1) * _L_CONN + (2 * n - 2) * _L_GAP

    if kind == "layered_architecture":
        layers = spec["layers"]
        total = 0.0
        for layer in layers:
            comps = layer["components"]
            col_w = (box_w - _L_GAP * (len(comps) - 1)) / len(comps)
            layer_h = lines(layer["heading"], heading_px, box_w, strong=True) * _line_box(heading_px)
            layer_h += _L_INNER
            layer_h += max(
                (card(c["heading"], c.get("detail"), heading_px, detail_px, col_w - 2 * _L_PAD)
                 for c in comps),
                default=0,
            )
            total += layer_h
        return total + (len(layers) - 1) * _L_LAYER

    stages = spec["stages"]
    k = len(stages)

    def stage(st, nxt, stage_w) -> float:
        h = lines(st["heading"], heading_px, stage_w, strong=True) * _line_box(heading_px)
        h += _L_MARGIN + _L_INNER
        for c in st["components"]:
            h += card(c["heading"], c.get("detail"), detail_px, detail_px, stage_w - 2 * _L_PAD)
        h += _L_INNER * max(0, len(st["components"]) - 1)
        if st.get("transfer_label"):
            text = f"{st['heading']} to {nxt}: {st['transfer_label']}"
            h += _L_INNER + _L_MARGIN + lines(text, meta_px, stage_w) * _line_box(meta_px)
        return h

    if spec.get("orientation", "horizontal") == "horizontal":
        stage_w = (box_w - (k - 1) * (2 * _L_GAP + _L_CONN)) / k
        return max(
            stage(st, stages[i + 1]["heading"] if i + 1 < k else "", stage_w)
            for i, st in enumerate(stages)
        )
    return (
        sum(stage(st, stages[i + 1]["heading"] if i + 1 < k else "", box_w)
            for i, st in enumerate(stages))
        + (k - 1) * _L_CONN
        + (2 * k - 2) * _L_GAP
    )


def test_linear_measure_reserves_painted_height_fixture_deck():
    surfaces = _linear_surfaces(_raw(), strict=True)
    seen = {sp.role: sp._linear_spec.get("orientation") for sp in surfaces}
    assert seen == {
        "process_flow": "horizontal",
        "timeline": "horizontal",
        "layered_architecture": None,
        "data_pipeline": "horizontal",
    }
    for sp in surfaces:
        ok, measured = _linear_fit_detail(sp)
        assert ok, sp.role
        assert measured >= _painted_linear_height(sp), sp.role


def test_linear_measure_reserves_painted_height_vertical_deck():
    slides = _raw()["slides"]
    by = {s["layout_type"]: s for s in slides}
    by["process_flow"]["payload"]["steps"] = [
        {"step_id": f"s{i}", "heading": f"Step {i}", "detail": "Short detail."}
        for i in range(6)
    ]
    by["timeline"]["payload"]["milestones"] = [
        {"milestone_id": f"m{i}", "time_label": f"Q{i}", "heading": f"Milestone {i}"}
        for i in range(6)
    ]
    by["data_pipeline"]["payload"]["stages"] = [
        {
            "stage_id": f"st{i}",
            "heading": f"Stage {i}",
            **({"transfer_label": "batch moves on"} if i < 4 else {}),
            "components": [
                {"component_id": f"c{i}", "heading": f"Component {i}", "detail": "Detail text."}
            ],
        }
        for i in range(5)
    ]
    surfaces = _linear_surfaces(_deck(slides), strict=False)
    seen = {sp.role: sp._linear_spec.get("orientation") for sp in surfaces}
    assert seen["process_flow"] == "vertical"
    assert seen["timeline"] == "vertical"
    assert seen["data_pipeline"] == "vertical"
    for sp in surfaces:
        _ok, measured = _linear_fit_detail(sp)
        assert measured >= _painted_linear_height(sp), sp.role


def test_pipeline_transfer_measure_uses_painted_string():
    heading_a = ("Ingest " + "alpha " * 10).rstrip()
    heading_b = ("Transform " + "beta " * 10).rstrip()
    label = ("batch " * 12).rstrip()
    slides = _raw()["slides"]
    dp = next(s for s in slides if s["layout_type"] == "data_pipeline")
    dp["payload"]["stages"] = [
        {
            "stage_id": "a",
            "heading": heading_a,
            "transfer_label": label,
            "components": [{"component_id": "c1", "heading": "Load"}],
        },
        {
            "stage_id": "b",
            "heading": heading_b,
            "transfer_label": "curated",
            "components": [{"component_id": "c2", "heading": "Cleanse"}],
        },
        {
            "stage_id": "c",
            "heading": "Serve",
            "components": [{"component_id": "c3", "heading": "Dash"}],
        },
    ]
    surfaces = _linear_surfaces(_deck(slides), strict=False)
    sp = next(p for p in surfaces if p.role == "data_pipeline")
    ok, _h = _linear_fit_detail(sp)
    assert ok is False
    assert sp.fallback == "accessible_ordered_flow"


def test_vertical_pipeline_components_measured_inside_card_padding():
    heading = ""
    while _text_width(heading + "x ", 16, strong=True) <= 1696:
        heading += "x "
    heading = (heading + "x ").rstrip()
    slides = _raw()["slides"]
    by = {s["layout_type"]: s for s in slides}
    by["data_pipeline"]["payload"]["stages"] = [
        {
            "stage_id": f"st{i}",
            "heading": f"Stage {i}",
            "components": [{"component_id": f"c{i}", "heading": heading}],
        }
        for i in range(5)
    ]
    surfaces = _linear_surfaces(_deck(slides), strict=False)
    sp = next(p for p in surfaces if p.role == "data_pipeline")
    assert sp._linear_spec["orientation"] == "vertical"
    _ok, measured = _linear_fit_detail(sp)
    assert measured >= _painted_linear_height(sp)


def test_schema_artifact_matches_models():
    check_schema(ROOT)


def test_fixture_validates_and_plans():
    result = validate_handoff(_raw(), strict=True)
    assert {s.layout_type for s in result.deck.slides} >= {
        "process_flow",
        "timeline",
        "layered_architecture",
        "data_pipeline",
    }
    plan = plan_deck(result.deck, strict=True)
    roles = {s.role for s in plan.surfaces}
    assert "process_flow" in roles
    assert "timeline" in roles
    assert "layered_architecture" in roles
    assert "data_pipeline" in roles


def test_process_flow_preserves_order_and_numbers(tmp_path: Path):
    out = tmp_path / "out"
    result = render_deck(FIXTURE, out, strict=True)
    assert result["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-layout="process_flow"' in html
    assert 'data-step-id="collect"' in html
    assert 'data-step-id="publish"' in html
    # Authored order: collect before publish in the HTML.
    assert html.index('data-step-id="collect"') < html.index('data-step-id="publish"')
    assert "Collect inputs" in html
    assert "Publish pack" in html
    assert "→" in html or "↓" in html  # renderer-owned connectors
    assert "Keep the sequence linear" in html


def test_timeline_preserves_authored_chronology(tmp_path: Path):
    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-layout="timeline"' in html
    assert "FY25 Q1" in html and "H2 FY25" in html
    assert html.index("FY25 Q1") < html.index("H2 FY25")
    assert 'data-milestone-id="m1"' in html
    assert "Pilot" in html and "Scale" in html


def test_layered_architecture_no_arrows(tmp_path: Path):
    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-layout="layered_architecture"' in html
    assert 'data-layer-id="experience"' in html
    assert 'data-component-id="web"' in html
    assert "Customer portal" in html
    # Layer block must not emit process/pipeline connectors.
    block_start = html.index('data-layout="layered_architecture"')
    block_end = html.index("</section>", block_start)
    # Find the slide section end more carefully.
    slide = html[block_start : html.index('data-layout="data_pipeline"')]
    assert "linear-connector" not in slide
    assert "→" not in slide and "↓" not in slide


def test_data_pipeline_transfer_labels(tmp_path: Path):
    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-layout="data_pipeline"' in html
    assert 'data-stage-id="ingest"' in html
    assert "Ingest to Transform: validated batch" in html
    assert "Transform to Serve: curated facts" in html
    # Final stage has no transfer label.
    serve_idx = html.index('data-stage-id="serve"')
    serve_block = html[serve_idx : serve_idx + 800]
    assert "pipeline-transfer" not in serve_block


def test_process_flow_rejects_duplicate_step_ids():
    raw = _raw()
    slide = next(s for s in raw["slides"] if s["layout_type"] == "process_flow")
    slide["payload"]["steps"][1]["step_id"] = "collect"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_timeline_rejects_single_milestone():
    raw = _raw()
    slide = next(s for s in raw["slides"] if s["layout_type"] == "timeline")
    slide["payload"]["milestones"] = slide["payload"]["milestones"][:1]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_pipeline_rejects_transfer_on_final_stage():
    raw = _raw()
    slide = next(s for s in raw["slides"] if s["layout_type"] == "data_pipeline")
    slide["payload"]["stages"][-1]["transfer_label"] = "should fail"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_layered_rejects_duplicate_component_ids_across_layers():
    raw = _raw()
    slide = next(s for s in raw["slides"] if s["layout_type"] == "layered_architecture")
    slide["payload"]["layers"][1]["components"][0]["component_id"] = "web"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_nonstrict_process_flow_ordered_list_fallback(tmp_path: Path):
    """Overflow → accessible ordered list; every step retained, no connectors."""
    raw = _raw()
    # Keep only process_flow with deliberately huge detail text.
    pf = next(s for s in raw["slides"] if s["layout_type"] == "process_flow")
    for step in pf["payload"]["steps"]:
        step["heading"] = "Step " + ("Heading " * 40)
        step["detail"] = "Detail " * 120
    raw["slides"] = [pf]
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "process_flow")
    body = html.split("<body>", 1)[1]
    assert 'data-fallback="accessible_ordered_list"' in body
    assert "<ol>" in body
    assert 'data-step-id="collect"' in body
    assert 'data-step-id="publish"' in body
    assert 'class="linear-connector"' not in body
    assert 'class="process-flow' not in body
    assert plan["fallback"] == "accessible_ordered_list"
    assert any(
        e["code"] == "plan.unresolved_overflow" and e.get("surface_id", "").endswith("process-flow")
        for e in meta["events"]
    )
    assert result["status"] == "degraded"


def test_nonstrict_timeline_chronological_list(tmp_path: Path):
    raw = _raw()
    tl = next(s for s in raw["slides"] if s["layout_type"] == "timeline")
    for m in tl["payload"]["milestones"]:
        m["heading"] = "Milestone " + ("Name " * 50)
        m["detail"] = "Notes " * 100
        m["time_label"] = "Period " + ("X" * 40)
    raw["slides"] = [tl]
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "timeline")
    assert 'data-fallback="accessible_chronological_list"' in html
    assert "FY25" in html or "Period" in html
    assert 'data-milestone-id="m1"' in html
    assert plan["fallback"] == "accessible_chronological_list"
    assert result["status"] == "degraded"


def test_nonstrict_layered_nested_outline(tmp_path: Path):
    raw = _raw()
    ly = next(s for s in raw["slides"] if s["layout_type"] == "layered_architecture")
    for layer in ly["payload"]["layers"]:
        layer["heading"] = "Layer " + ("Title " * 40)
        for c in layer["components"]:
            c["heading"] = "Comp " + ("Name " * 40)
            c["detail"] = "Detail " * 80
    raw["slides"] = [ly]
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "layered_architecture")
    assert 'data-fallback="accessible_nested_outline"' in html
    assert 'data-layer-id="experience"' in html
    assert 'data-component-id="web"' in html
    assert plan["fallback"] == "accessible_nested_outline"
    assert result["status"] == "degraded"


def test_nonstrict_pipeline_ordered_flow(tmp_path: Path):
    raw = _raw()
    dp = next(s for s in raw["slides"] if s["layout_type"] == "data_pipeline")
    for st in dp["payload"]["stages"]:
        st["heading"] = "Stage " + ("Name " * 40)
        if st.get("transfer_label"):
            st["transfer_label"] = "transfer " + ("x" * 60)
        for c in st["components"]:
            c["heading"] = "Comp " + ("Y" * 40)
            c["detail"] = "D " * 80
    raw["slides"] = [dp]
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "data_pipeline")
    assert 'data-fallback="accessible_ordered_flow"' in html
    assert " to " in html  # A to B: label wording retained
    assert 'data-stage-id="ingest"' in html
    assert plan["fallback"] == "accessible_ordered_flow"
    assert result["status"] == "degraded"


def test_nonstrict_repairs_drop_unknown_linear_fields():
    raw = _raw()
    for slide in raw["slides"]:
        if slide["layout_type"] not in {
            "process_flow",
            "timeline",
            "layered_architecture",
            "data_pipeline",
        }:
            continue
        slide["payload"]["unexpected"] = True
        slide["disclosure"] = {"sections": ["invalid"]}
    result = validate_handoff(raw, strict=False)
    assert result.repaired is True
    repaired = {s.layout_type: s for s in result.deck.slides}
    for lt in (
        "process_flow",
        "timeline",
        "layered_architecture",
        "data_pipeline",
    ):
        assert repaired[lt].disclosure is None
