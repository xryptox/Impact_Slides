"""Renderer v3 relationship + decision compositions (#193).

Seams under test:
- decision_tree / feedback_loop / hierarchy / stakeholder_map / quadrant_matrix
- graph and assignment invariants before plan
- no inferred relations; invalid structures preserve authored facts
- non-strict relationship-table / outline fallbacks
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.plan import plan_deck
from impact_slides.renderer_v3.schema_export import check_schema
from impact_slides.renderer_v3.validate import analyze_relationship_structure
from impact_slides.renderer_v3.models import (
    DecisionBranch,
    DecisionTreeNode,
    DecisionTreePayload,
    FeedbackLoopItem,
    FeedbackLoopPayload,
    HierarchyNode,
    HierarchyPayload,
    QuadrantAxis,
    QuadrantItem,
    QuadrantMatrixPayload,
    StakeholderEntity,
    StakeholderMapPayload,
    StakeholderSpoke,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/renderer_v3/relationship_compositions.json"


def _raw() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _deck(slides: list[dict]) -> dict:
    raw = _raw()
    return {
        "meta": raw["meta"],
        "sections": raw["sections"],
        "number_formats": raw["number_formats"],
        "evidence_registry": raw["evidence_registry"],
        "slides": slides,
    }


def test_schema_artifact_matches_models():
    check_schema(ROOT)


def test_valid_fixture_validates_and_plans():
    result = validate_handoff(_raw(), strict=True)
    assert result.relationship_defect_slides == frozenset()
    plan = plan_deck(result.deck, strict=True)
    roles = {sp.role for sp in plan.surfaces if sp._linear_spec}
    assert roles == {
        "decision_tree",
        "feedback_loop",
        "hierarchy",
        "stakeholder_map",
        "quadrant_matrix",
    }


def test_paint_preserves_ids_and_semantics(tmp_path: Path):
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(_raw()), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert result["status"] == "clean"
    assert 'data-node-id="d_risk"' in html
    assert 'data-node-kind="decision"' in html
    assert "Risk tier?" in html
    assert 'data-loop-kind="causal"' in html
    assert 'data-loop-class="balancing"' in html
    assert 'data-item-id="spend"' in html
    assert 'data-relationship="reports_to"' in html
    assert 'data-node-id="ceo"' in html
    assert 'data-entity-id="amex"' in html
    assert 'data-direction="to_focal"' in html
    assert 'data-x-band="high"' in html
    assert 'data-item-id="a"' in html
    assert "class=\"decision-tree" in html
    assert "class=\"feedback-loop" in html
    assert "class=\"hierarchy-tree" in html
    assert "class=\"stakeholder-map" in html
    assert "class=\"quadrant-matrix" in html


def test_decision_tree_rejects_shared_target_strict():
    slide = next(s for s in _raw()["slides"] if s["layout_type"] == "decision_tree")
    # Point both Low and High to the same outcome → shared target.
    slide["payload"]["nodes"] = [
        {
            "node_id": "d1",
            "kind": "decision",
            "heading": "Root?",
            "branches": [
                {"label": "A", "target_id": "o1"},
                {"label": "B", "target_id": "o1"},
            ],
        },
        {"node_id": "o1", "kind": "outcome", "heading": "One"},
        {"node_id": "o2", "kind": "outcome", "heading": "Orphan"},
    ]
    slide["payload"]["root_id"] = "d1"
    with pytest.raises(RendererValidationError) as ei:
        validate_handoff(_deck([slide]), strict=True)

    def _exp(e) -> str:
        ex = e.expected
        if ex is None:
            return ""
        return ex if isinstance(ex, str) else getattr(ex, "contract", "") or ""

    assert any("shared_target" in _exp(e) for e in ei.value.events)


def test_decision_tree_nonstrict_preserves_unresolved_without_reconnect(tmp_path: Path):
    slide = next(s for s in _raw()["slides"] if s["layout_type"] == "decision_tree")
    # Dangling target — keep authored branch label/target, mark unresolved.
    slide["payload"]["nodes"][0]["branches"][1]["target_id"] = "missing_node"
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(_deck([slide])), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "decision_tree")
    assert plan["fallback"] == "accessible_relationship_table"
    assert 'data-fallback="accessible_relationship_table"' in html
    assert "missing_node" in html
    assert "unresolved target" in html
    assert 'data-node-id="d_risk"' in html
    assert 'data-node-id="o_approve"' in html
    # Must not invent a replacement edge or drop the dangling label.
    assert ">High → missing_node<" in html or "High → missing_node" in html
    assert result["status"] == "degraded"


def test_hierarchy_rejects_cycle_strict():
    payload = HierarchyPayload(
        relationship="part_of",
        root_id="a",
        nodes=[
            HierarchyNode(node_id="a", heading="A", children=["b"]),
            HierarchyNode(node_id="b", heading="B", children=["c"]),
            HierarchyNode(node_id="c", heading="C", children=["b"]),
        ],
    )
    defects = analyze_relationship_structure("hierarchy", payload)
    assert any("cycle" in d or "shared" in d for d in defects)


def test_hierarchy_nonstrict_table_marks_dangling(tmp_path: Path):
    slide = next(s for s in _raw()["slides"] if s["layout_type"] == "hierarchy")
    slide["payload"]["nodes"][0]["children"] = ["cfo", "ghost"]
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(_deck([slide])), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-fallback="accessible_relationship_table"' in html
    assert "ghost" in html
    assert "unresolved child" in html
    assert 'data-node-id="ceo"' in html
    assert result["status"] == "degraded"


def test_feedback_loop_classification_balancing():
    payload = FeedbackLoopPayload(
        kind="causal",
        items=[
            FeedbackLoopItem(item_id="a", heading="A", effect="same_direction"),
            FeedbackLoopItem(item_id="b", heading="B", effect="opposite_direction"),
            FeedbackLoopItem(item_id="c", heading="C", effect="same_direction"),
        ],
    )
    assert payload.loop_classification == "balancing"
    assert analyze_relationship_structure("feedback_loop", payload) == []


def test_feedback_loop_missing_effect_nonstrict_table(tmp_path: Path):
    slide = next(s for s in _raw()["slides"] if s["layout_type"] == "feedback_loop")
    del slide["payload"]["items"][1]["effect"]
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(_deck([slide])), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-fallback="accessible_relationship_table"' in html
    assert "unresolved effect" in html
    assert 'data-item-id="spend"' in html
    assert 'data-item-id="rewards"' in html
    # Does not invent polarity for the missing edge.
    assert result["status"] == "degraded"


def test_feedback_loop_missing_effect_strict_fails():
    slide = next(s for s in _raw()["slides"] if s["layout_type"] == "feedback_loop")
    del slide["payload"]["items"][0]["effect"]
    with pytest.raises(RendererValidationError):
        validate_handoff(_deck([slide]), strict=True)


def test_stakeholder_map_rejects_duplicate_entity():
    with pytest.raises(Exception):
        StakeholderMapPayload(
            focal=StakeholderEntity(entity_id="hub", heading="Hub"),
            stakeholders=[
                StakeholderSpoke(
                    entity_id="hub",
                    heading="Dup",
                    relationship_label="link",
                    direction="undirected",
                ),
                StakeholderSpoke(
                    entity_id="other",
                    heading="Other",
                    relationship_label="link",
                    direction="to_focal",
                ),
            ],
        )


def test_quadrant_preserves_empty_quadrants(tmp_path: Path):
    slide = next(s for s in _raw()["slides"] if s["layout_type"] == "quadrant_matrix")
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(_deck([slide])), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    # low/high quadrant empty in fixture — still labelled.
    assert 'data-x-band="low"' in html and 'data-y-band="high"' in html
    assert "Low impact" in html and "High effort" in html


def test_nonstrict_overflow_decision_tree_outline(tmp_path: Path):
    slide = next(s for s in _raw()["slides"] if s["layout_type"] == "decision_tree")
    for n in slide["payload"]["nodes"]:
        n["heading"] = "Node " + ("Heading " * 40)
        if n.get("detail"):
            n["detail"] = "Detail " * 80
        if n.get("branches"):
            for i, b in enumerate(n["branches"]):
                b["label"] = f"Branch{i} " + ("L" * 40)
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(_deck([slide])), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "decision_tree")
    assert plan["fallback"] in {
        "accessible_nested_outline",
        "accessible_relationship_table",
    }
    assert 'data-node-id="d_risk"' in html
    assert result["status"] == "degraded"


def test_nonstrict_repairs_drop_unknown_relationship_fields():
    raw = _raw()
    for slide in raw["slides"]:
        slide["payload"]["unexpected"] = True
        slide["disclosure"] = {"sections": ["invalid"]}
    result = validate_handoff(raw, strict=False)
    assert result.repaired is True
    repaired = {s.layout_type: s for s in result.deck.slides}
    for lt in (
        "decision_tree",
        "feedback_loop",
        "hierarchy",
        "stakeholder_map",
        "quadrant_matrix",
    ):
        assert repaired[lt].disclosure is None


def test_semantics_not_blurred_across_kinds():
    """Shared card chrome must not erase kind-specific contracts."""
    dt = DecisionTreePayload(
        root_id="r",
        nodes=[
            DecisionTreeNode(
                node_id="r",
                kind="decision",
                heading="Root",
                branches=[
                    DecisionBranch(label="Y", target_id="a"),
                    DecisionBranch(label="N", target_id="b"),
                ],
            ),
            DecisionTreeNode(node_id="a", kind="outcome", heading="A"),
            DecisionTreeNode(node_id="b", kind="outcome", heading="B"),
        ],
    )
    fl = FeedbackLoopPayload(
        kind="procedural",
        items=[
            FeedbackLoopItem(item_id="i1", heading="One"),
            FeedbackLoopItem(item_id="i2", heading="Two"),
            FeedbackLoopItem(item_id="i3", heading="Three"),
        ],
    )
    assert analyze_relationship_structure("decision_tree", dt) == []
    assert analyze_relationship_structure("feedback_loop", fl) == []
    # Procedural forbids causal fields.
    with pytest.raises(Exception):
        FeedbackLoopPayload(
            kind="procedural",
            items=[
                FeedbackLoopItem(item_id="i1", heading="One", effect="same_direction"),
                FeedbackLoopItem(item_id="i2", heading="Two"),
                FeedbackLoopItem(item_id="i3", heading="Three"),
            ],
        )
    qm = QuadrantMatrixPayload(
        x_axis=QuadrantAxis(label="X", low_label="L", high_label="H"),
        y_axis=QuadrantAxis(label="Y", low_label="Lo", high_label="Hi"),
        items=[QuadrantItem(item_id="i", heading="I", x_band="low", y_band="high")],
    )
    assert analyze_relationship_structure("quadrant_matrix", qm) == []


def test_decision_tree_depth_limit():
    # depth 5 path: r -> a -> b -> c -> d (5 nodes) should fail.
    nodes = [
        DecisionTreeNode(
            node_id="r",
            kind="decision",
            heading="R",
            branches=[
                DecisionBranch(label="go", target_id="a"),
                DecisionBranch(label="stop", target_id="o1"),
            ],
        ),
        DecisionTreeNode(
            node_id="a",
            kind="decision",
            heading="A",
            branches=[
                DecisionBranch(label="go", target_id="b"),
                DecisionBranch(label="stop", target_id="o2"),
            ],
        ),
        DecisionTreeNode(
            node_id="b",
            kind="decision",
            heading="B",
            branches=[
                DecisionBranch(label="go", target_id="c"),
                DecisionBranch(label="stop", target_id="o3"),
            ],
        ),
        DecisionTreeNode(
            node_id="c",
            kind="decision",
            heading="C",
            branches=[
                DecisionBranch(label="go", target_id="d"),
                DecisionBranch(label="stop", target_id="o4"),
            ],
        ),
        DecisionTreeNode(node_id="d", kind="outcome", heading="D"),
        DecisionTreeNode(node_id="o1", kind="outcome", heading="O1"),
        DecisionTreeNode(node_id="o2", kind="outcome", heading="O2"),
        DecisionTreeNode(node_id="o3", kind="outcome", heading="O3"),
        DecisionTreeNode(node_id="o4", kind="outcome", heading="O4"),
    ]
    payload = DecisionTreePayload(root_id="r", nodes=nodes)
    defects = analyze_relationship_structure("decision_tree", payload)
    assert "decision_tree.depth_exceeded" in defects
