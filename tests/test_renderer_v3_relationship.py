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
STRESS_FIXTURE = ROOT / "tests/fixtures/renderer_v3/relationship_routes_stress.json"

_DIR_ARROW = {
    "to_focal": "↑",
    "from_focal": "↓",
    "bidirectional": "↕",
    "undirected": "│",
}


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
    hierarchy = _slide_html(html, 3)
    assert "class=\"linear-connector\"" not in hierarchy


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
    # Fallback table must not invent recipe geometry or reconnect.
    assert 'class="linear-connector"' not in html
    assert 'class="decision-tree' not in html


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


def test_disconnected_mutual_cycle_is_structural_defect(tmp_path: Path):
    """Nodes in a disconnected mutual cycle must not pass as clean or vanish."""
    hierarchy = HierarchyPayload(
        relationship="part_of",
        root_id="root",
        nodes=[
            HierarchyNode(node_id="root", heading="Root", children=["leaf"]),
            HierarchyNode(node_id="leaf", heading="Leaf"),
            HierarchyNode(node_id="ghost_a", heading="GhostA", children=["ghost_b"]),
            HierarchyNode(node_id="ghost_b", heading="GhostB", children=["ghost_a"]),
        ],
    )
    h_defects = analyze_relationship_structure("hierarchy", hierarchy)
    assert any(d.startswith("hierarchy.unreachable:") for d in h_defects)
    assert "hierarchy.cycle" in h_defects

    decision = DecisionTreePayload(
        root_id="r",
        nodes=[
            DecisionTreeNode(
                node_id="r",
                kind="decision",
                heading="Root",
                branches=[
                    DecisionBranch(label="yes", target_id="o"),
                    DecisionBranch(label="no", target_id="o2"),
                ],
            ),
            DecisionTreeNode(node_id="o", kind="outcome", heading="Out"),
            DecisionTreeNode(node_id="o2", kind="outcome", heading="Out2"),
            DecisionTreeNode(
                node_id="ghost_a",
                kind="decision",
                heading="GhostA",
                branches=[
                    DecisionBranch(label="loop", target_id="ghost_b"),
                    DecisionBranch(label="alt", target_id="ghost_b"),
                ],
            ),
            DecisionTreeNode(
                node_id="ghost_b",
                kind="decision",
                heading="GhostB",
                branches=[
                    DecisionBranch(label="back", target_id="ghost_a"),
                    DecisionBranch(label="also", target_id="ghost_a"),
                ],
            ),
        ],
    )
    d_defects = analyze_relationship_structure("decision_tree", decision)
    assert any(d.startswith("decision_tree.unreachable:") for d in d_defects)
    assert "decision_tree.cycle" in d_defects

    slide = next(s for s in _raw()["slides"] if s["layout_type"] == "hierarchy")
    slide["payload"] = hierarchy.model_dump(mode="json", exclude_none=True)
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(_deck([slide])), encoding="utf-8")
    out = tmp_path / "out"
    with pytest.raises(RendererValidationError):
        render_deck(handoff, out, strict=True)
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert result["status"] == "degraded"
    assert "GhostA" in html
    assert "GhostB" in html
    assert 'data-fallback="accessible_relationship_table"' in html


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


_WRAP_CAUSAL_HEADINGS = (
    "Record the event, classify impact and urgency, and assign a resolver before restoration work begins",
    "Contain the incident, communicate status to users, and protect evidence for later problem review",
    "Restore the agreed service, confirm resolution with the user, and close the ITIL incident record",
    "Publish the known-error record so future incidents reuse the workaround instead of rediscovering it",
    "Measure restore time against the ITIL service-level target after each major incident review",
    "Feed problem-management output back into change so the failing component is actually removed",
    "Reassess residual risk under ISO 31000 after the change window closes",
    "Update the service-continuity plan when restore steps no longer match the runbook",
)


def test_feedback_loop_eight_wrapping_causal_items_paint_cycle(tmp_path: Path):
    """Max-cardinality wrapping causal items stay the cycle recipe at type floors (#355)."""
    slide = next(s for s in _raw()["slides"] if s["layout_type"] == "feedback_loop")
    slide["title"] = "Wrapping causal cycle"
    slide["payload"] = {
        "kind": "causal",
        "items": [
            {
                "item_id": f"i{i}",
                "heading": heading,
                "effect": (
                    "same_direction" if i % 2 else "opposite_direction"
                ),
            }
            for i, heading in enumerate(_WRAP_CAUSAL_HEADINGS, start=1)
        ],
    }
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(_deck([slide])), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "feedback_loop")
    assert result["status"] == "clean"
    assert plan["fallback"] is None
    assert plan["role_sizes"]["heading"] == 22
    assert 'data-fallback=' not in html
    assert 'class="feedback-loop cycle-wrap' in html
    assert 'data-loop-class="reinforcing"' in html
    assert "reinforcing loop" in html
    painted = html.replace("<wbr>", "")
    for i, heading in enumerate(_WRAP_CAUSAL_HEADINGS, start=1):
        assert f'data-item-id="i{i}"' in html
        assert heading in painted
    assert "↻" in html
    assert "accessible_ordered_relationship_list" not in html


def test_feedback_loop_six_wrapping_causal_items_still_overflow(tmp_path: Path):
    """Wrap packing is 7–8 only; six wrapping causal items stay leftover overflow (#355)."""
    slide = next(s for s in _raw()["slides"] if s["layout_type"] == "feedback_loop")
    slide["payload"] = {
        "kind": "causal",
        "items": [
            {
                "item_id": f"i{i}",
                "heading": heading,
                "effect": "same_direction" if i % 2 else "opposite_direction",
            }
            for i, heading in enumerate(_WRAP_CAUSAL_HEADINGS[:6], start=1)
        ],
    }
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(_deck([slide])), encoding="utf-8")
    out = tmp_path / "out"
    with pytest.raises(RendererValidationError):
        render_deck(handoff, out, strict=True)
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "feedback_loop")
    assert result["status"] == "degraded"
    assert plan["fallback"] == "accessible_ordered_relationship_list"
    assert 'class="feedback-loop cycle-wrap' not in html
    assert 'data-item-id="i1"' in html and 'data-item-id="i6"' in html


def test_feedback_loop_eight_short_procedural_stays_one_row(tmp_path: Path):
    """Already-fitting 8-item procedural cycle keeps one-row geometry (#355)."""
    slide = next(s for s in _raw()["slides"] if s["layout_type"] == "feedback_loop")
    slide["title"] = "Short procedural cycle"
    slide["payload"] = {
        "kind": "procedural",
        "items": [
            {"item_id": "s", "heading": "Scan", "detail": "ITIL continual improvement."},
            {"item_id": "p", "heading": "Plan"},
            {"item_id": "d", "heading": "Do"},
            {"item_id": "c", "heading": "Check"},
            {"item_id": "a", "heading": "Act"},
            {"item_id": "r", "heading": "Report"},
            {"item_id": "g", "heading": "Govern"},
            {"item_id": "l", "heading": "Learn", "detail": "Close the CSI register."},
        ],
    }
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(_deck([slide])), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "feedback_loop")
    assert result["status"] == "clean"
    assert plan["fallback"] is None
    assert 'class="feedback-loop' in html
    assert 'class="feedback-loop cycle-wrap' not in html
    assert 'data-item-id="s"' in html and 'data-item-id="l"' in html
    assert "↻" in html


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


def test_long_branch_label_overflows_at_painted_edge_width(tmp_path: Path):
    """A label that wraps past .rel-edge max-width falls back; freeze is not fit-ok."""
    slide = next(s for s in _raw()["slides"] if s["layout_type"] == "decision_tree")
    long_label = (
        "Continue with enhanced documentation review before proceeding to underwriting"
    )
    slide["payload"]["nodes"][0]["branches"][0]["label"] = long_label
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(_deck([slide])), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "decision_tree")
    assert plan["fallback"] == "accessible_nested_outline"
    assert 'data-node-id="d_risk"' in html
    assert long_label in html
    assert result["status"] == "degraded"


def test_bushy_edge_row_wrap_overflows_when_labels_fill_max_width(tmp_path: Path):
    """Nine max-width edge labels wrap to a second row and must not freeze as fit-ok."""
    wrap_label = "Named owner signs residual risk today"
    heading = (
        "Please record the event, classify impact and urgency, assign a named "
        "resolver, and freeze restoration work before processing resumes today"
    )
    detail = (
        "Please document the rationale, residual risk, compensating controls, "
        "named owner, and restoration path before any processing resumes under "
        "the written policy."
    )
    nodes = [
        {
            "node_id": "d1",
            "kind": "decision",
            "heading": heading,
            "detail": detail,
            "branches": [
                {"label": "A", "target_id": "d2"},
                {"label": "B", "target_id": "d3"},
                {"label": "C", "target_id": "d4"},
            ],
        },
        {
            "node_id": "d2",
            "kind": "decision",
            "heading": heading,
            "detail": detail,
            "branches": [
                {"label": f"{wrap_label} one", "target_id": "o1"},
                {"label": f"{wrap_label} two", "target_id": "o2"},
                {"label": f"{wrap_label} three", "target_id": "o3"},
            ],
        },
        {
            "node_id": "d3",
            "kind": "decision",
            "heading": heading,
            "detail": detail,
            "branches": [
                {"label": f"{wrap_label} four", "target_id": "o4"},
                {"label": f"{wrap_label} five", "target_id": "o5"},
                {"label": f"{wrap_label} six", "target_id": "o6"},
            ],
        },
        {
            "node_id": "d4",
            "kind": "decision",
            "heading": heading,
            "detail": detail,
            "branches": [
                {"label": f"{wrap_label} seven", "target_id": "o7"},
                {"label": f"{wrap_label} eight", "target_id": "o8"},
                {"label": f"{wrap_label} nine", "target_id": "o9"},
            ],
        },
    ]
    for i in range(1, 10):
        nodes.append(
            {
                "node_id": f"o{i}",
                "kind": "outcome",
                "heading": heading,
                "detail": detail,
            }
        )
    slide = next(s for s in _raw()["slides"] if s["layout_type"] == "decision_tree")
    slide["payload"] = {"root_id": "d1", "nodes": nodes}
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(_deck([slide])), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "decision_tree")
    assert plan["fallback"] == "accessible_nested_outline"
    assert 'data-node-id="d1"' in html
    assert 'data-node-id="o9"' in html
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


def _slide_html(html: str, slide_number: int) -> str:
    marker = f'data-slide-number="{slide_number}"'
    start = html.index(marker)
    nxt = html.find('class="slide"', start + 1)
    return html[start:] if nxt < 0 else html[start:nxt]


def test_decision_tree_paints_branch_connectors_not_in_card_text(tmp_path: Path):
    """D274: branch labels sit on renderer-owned edges, not inside parent cards."""
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(_raw()), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    tree = _slide_html(html, 1)
    assert result["status"] == "clean"
    assert 'class="decision-tree' in tree
    assert 'class="linear-connector"' in tree
    assert 'aria-hidden="true"' in tree
    assert tree.count('class="linear-connector"') == 4  # authored branches only
    assert "Low" in tree and "High" in tree and "Yes" in tree and "No" in tree
    # In-card "label → child heading" is not the route.
    assert "Low → Docs complete?" not in tree
    assert "High → Decline" not in tree
    assert "Yes → Approve" not in tree
    assert "No → Hold for docs" not in tree
    assert 'data-node-id="d_risk"' in tree
    assert 'data-node-id="o_approve"' in tree


def test_stakeholder_map_paints_directed_spokes_and_wording(tmp_path: Path):
    """D279: hub/spoke arrows follow authored direction; wording is not arrows alone."""
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(_raw()), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    m = _slide_html(html, 4)
    assert result["status"] == "clean"
    assert 'class="stakeholder-map' in m
    assert m.count('class="linear-connector"') == 3
    assert 'data-direction="to_focal"' in m
    assert 'data-direction="from_focal"' in m
    assert 'data-direction="bidirectional"' in m
    assert _DIR_ARROW["to_focal"] in m
    assert _DIR_ARROW["from_focal"] in m
    assert _DIR_ARROW["bidirectional"] in m
    assert "accepts network" in m
    assert "membership" in m
    assert "partnership" in m
    assert "to focal" in m
    assert "from focal" in m
    assert "bidirectional" in m
    assert 'data-entity-id="amex"' in m
    assert 'data-entity-id="merchants"' in m


def test_layout_stress_s023_and_s065_paint_routes_at_floors(tmp_path: Path):
    """#357 proof: s023 7-node tree and s065 6 mixed spokes freeze with visible routes."""
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    out = tmp_path / "out"
    result = render_deck(STRESS_FIXTURE, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert result["ok"] is True
    assert result["status"] == "clean"
    assert meta["severity_counts"].get("error", 0) == 0

    tree = _slide_html(html, 23)
    assert 'class="decision-tree' in tree
    assert "linear-fallback" not in tree
    assert tree.count('class="linear-connector"') == 6
    assert "Yes" in tree and "No" in tree
    assert "Yes → Authorized?" not in tree
    assert "Yes → Use under HIPAA" not in tree
    assert 'data-node-id="d-phi"' in tree
    assert 'data-node-id="o-use"' in tree

    spoke = _slide_html(html, 65)
    assert 'class="stakeholder-map' in spoke
    assert "linear-fallback" not in spoke
    assert spoke.count('class="linear-connector"') == 6
    for direction, glyph in _DIR_ARROW.items():
        assert f'data-direction="{direction}"' in spoke
        assert glyph in spoke
    assert "facilitates PI" in spoke
    assert "undirected" in spoke
    assert "to focal" in spoke
    assert "from focal" in spoke
    assert "bidirectional" in spoke

    html_path = (out / "presentation.html").resolve()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(html_path.as_uri(), wait_until="networkidle")
        try:
            for sn, sel, n_conn in (
                (23, ".decision-tree .linear-connector", 6),
                (65, ".stakeholder-map .linear-connector", 6),
            ):
                box = page.evaluate(
                    """({sn, sel, n}) => {
                      const slide = document.querySelector(
                        'section.slide[data-slide-number="' + sn + '"]'
                      );
                      slide.scrollIntoView();
                      const conns = [...slide.querySelectorAll(sel)];
                      const slideBox = slide.getBoundingClientRect();
                      const rects = conns.map((el) => {
                        const r = el.getBoundingClientRect();
                        const s = getComputedStyle(el);
                        return {
                          w: r.width, h: r.height,
                          vis: s.visibility, display: s.display,
                          text: (el.textContent || '').trim(),
                          hidden: el.getAttribute('aria-hidden'),
                          inside: r.top >= slideBox.top - 1
                            && r.bottom <= slideBox.bottom + 1
                            && r.left >= slideBox.left - 1
                            && r.right <= slideBox.right + 1,
                        };
                      });
                      return {
                        n: conns.length,
                        expected: n,
                        overflow: slide.classList.contains('linear-overflow')
                          || !!slide.querySelector('.linear-overflow'),
                        slideW: slideBox.width,
                        slideH: slideBox.height,
                        rects,
                      };
                    }""",
                    {"sn": sn, "sel": sel, "n": n_conn},
                )
                assert box["n"] == n_conn, box
                assert box["overflow"] is False, box
                assert box["slideW"] == 1920 and box["slideH"] == 1080, box
                for r in box["rects"]:
                    assert r["hidden"] == "true", r
                    assert r["display"] != "none", r
                    assert r["vis"] != "hidden", r
                    assert r["w"] > 0 and r["h"] > 0, r
                    assert r["inside"] is True, r
                    assert r["text"], r
        finally:
            browser.close()


def test_layout_stress_tree_and_map_families_still_freeze_at_floors(tmp_path: Path):
    """s021–s030 and s061–s070 stay at type floors; adding routes must not overflow."""
    out = tmp_path / "out"
    result = render_deck(STRESS_FIXTURE, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert result["ok"] is True, meta.get("severity_counts")
    assert result["status"] == "clean"
    overflows = [
        p
        for p in meta["plans"]
        if p.get("role") in {"decision_tree", "stakeholder_map"} and p.get("fallback")
    ]
    assert overflows == []
    for sn in list(range(21, 31)) + list(range(61, 71)):
        block = _slide_html(html, sn)
        assert "linear-overflow" not in block, sn
        assert "linear-fallback" not in block, sn
        assert "class=\"linear-connector\"" in block, sn
