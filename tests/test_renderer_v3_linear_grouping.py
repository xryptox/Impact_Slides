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
from impact_slides.renderer_v3.plan import plan_deck
from impact_slides.renderer_v3.schema_export import check_schema

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/renderer_v3/linear_grouping_compositions.json"


def _raw() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


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
