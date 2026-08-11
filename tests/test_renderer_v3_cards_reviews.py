"""Renderer v3 cards, reviews, quotations, state transitions (#194/#215).

Seams under test:
- feature_cards / quotation / evidence_review / risk_opportunity_review /
  recommendation_case / state_transition models
- exact authored roles, provenance, ordering, D224 emphasis
- D287 applicability (no source_footer on evidence_review; no takeaway on recommendation)
- plan fixed/adaptive type + non-strict complete sequential fallbacks
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.plan import (
    BLOCK_MARGIN_Y,
    CARD_FIXED_BODY_PX,
    CARD_FIXED_HEADING_PX,
    CARD_GAP,
    CARD_MARGIN,
    CARD_PAD,
    CARD_PANEL_BORDER_Y,
    FEATURE_BODY_FLOOR,
    LIST_INDENT_EM,
    RISK_GROUP_GAP,
    SurfacePlan,
    _card_fit_detail,
    _finalize_composition_roles,
    _line_box,
    _synchronize,
    plan_deck,
)
from impact_slides.renderer_v3.schema_export import check_schema

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/renderer_v3/cards_reviews_compositions.json"


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


def test_fixture_validates_and_plans():
    result = validate_handoff(_raw(), strict=True)
    assert {s.layout_type for s in result.deck.slides} == {
        "feature_cards",
        "quotation",
        "evidence_review",
        "risk_opportunity_review",
        "recommendation_case",
        "state_transition",
    }
    plan = plan_deck(result.deck, strict=True)
    roles = {s.role for s in plan.surfaces}
    assert {
        "feature_cards",
        "quotation",
        "evidence_review",
        "risk_opportunity_review",
        "recommendation_case",
        "state_transition",
    } <= roles


def test_feature_cards_order_icons_and_chrome(tmp_path: Path):
    out = tmp_path / "out"
    result = render_deck(FIXTURE, out, strict=True)
    assert result["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-layout="feature_cards"' in html
    assert 'data-card-id="grow"' in html
    assert html.index('data-card-id="grow"') < html.index('data-card-id="guide"')
    assert 'data-icon="growth"' in html
    assert 'aria-hidden="true"' in html
    assert "Grow share" in html and "Guide teams" in html
    assert "card-panel" in html


def test_quotation_preserves_attribution_and_order(tmp_path: Path):
    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-layout="quotation"' in html
    assert 'data-quote-id="q1"' in html
    assert html.index('data-quote-id="q1"') < html.index('data-quote-id="q2"')
    assert "A. Rivera" in html and "COO" in html and "North Region" in html
    assert "We need one operating rhythm" in html
    assert "<blockquote>" in html and "<cite" in html


def test_evidence_review_source_names_not_ids(tmp_path: Path):
    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    block_start = html.index('data-layout="evidence_review"')
    block_end = html.index('data-layout="risk_opportunity_review"')
    block = html[block_start:block_end]
    assert "Field interviews" in block and "Ops ledger" in block
    assert "src-a" not in block and "src-b" not in block
    assert "<strong>softened</strong>" in block
    assert "source-footer" not in block


def test_risk_opportunity_independent_groups(tmp_path: Path):
    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-layout="risk_opportunity_review"' in html
    assert ">Risks<" in html and ">Opportunities<" in html
    assert 'data-item-id="r1"' in html and 'data-item-id="o1"' in html
    assert html.index('data-group="risks"') < html.index('data-group="opportunities"')
    assert "Vendor concentration" in html
    assert "Cross-<wbr>sell" in html or "Cross-sell" in html


def test_recommendation_case_no_takeaway(tmp_path: Path):
    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    block_start = html.index('data-layout="recommendation_case"')
    block_end = html.index('data-layout="state_transition"')
    block = html[block_start:block_end]
    assert "Recommendation" in block
    assert "Rationale 1" in block and "Rationale 2" in block
    assert "Stand up a single weekly" in block
    assert "Key takeaway" not in block
    assert 'data-rationale-id="ra1"' in block


def test_state_transition_reading_order(tmp_path: Path):
    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-layout="state_transition"' in html
    assert 'data-role="before"' in html and 'data-role="after"' in html
    assert html.index("Fragmented forums") < html.index("Consolidate owners")
    assert html.index("Consolidate owners") < html.index("One cadence")
    assert 'data-step-id="ts1"' in html
    assert "Before" in html and "After" in html and "Transition" in html


def test_feature_cards_rejects_unknown_icon():
    raw = _raw()
    slide = next(s for s in raw["slides"] if s["layout_type"] == "feature_cards")
    slide["payload"]["cards"][0]["icon_key"] = "not-a-real-icon"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_evidence_review_rejects_source_footer():
    raw = _raw()
    slide = next(s for s in raw["slides"] if s["layout_type"] == "evidence_review")
    slide["source_footer"] = ["src-a"]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_recommendation_rejects_takeaway():
    raw = _raw()
    slide = next(s for s in raw["slides"] if s["layout_type"] == "recommendation_case")
    slide["takeaway"] = {"text": "should fail"}
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_quotation_rejects_evidence_outside_slide():
    raw = _raw()
    slide = next(s for s in raw["slides"] if s["layout_type"] == "quotation")
    slide["payload"]["quotes"][0]["evidence_id"] = "src-b"
    # src-b not on slide evidence_ids
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_state_transition_rejects_duplicate_block_ids():
    raw = _raw()
    slide = next(s for s in raw["slides"] if s["layout_type"] == "state_transition")
    slide["payload"]["after"]["blocks"][0]["block_id"] = "bb1"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_nonstrict_drops_unknown_icon_keeps_text(tmp_path: Path):
    raw = _raw()
    fc = next(s for s in raw["slides"] if s["layout_type"] == "feature_cards")
    fc["payload"]["cards"][0]["icon_key"] = "totally-unknown"
    raw["slides"] = [fc]
    # Drop unused evidence so deck validates after repair.
    raw["evidence_registry"] = {"src-a": raw["evidence_registry"]["src-a"]}
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert "Grow share" in html
    assert 'data-icon="totally-unknown"' not in html
    assert result["ok"] is True or result["status"] in {"ok", "degraded"}


def test_nonstrict_evidence_bad_ref_source_unavailable(tmp_path: Path):
    raw = _raw()
    er = next(s for s in raw["slides"] if s["layout_type"] == "evidence_review")
    er["payload"]["findings"] = [
        {
            "finding_id": "f-bad",
            "statement": {"runs": [{"text": "Unsupported claim remains visible."}]},
            "evidence_ids": ["not-on-slide"],
        }
    ]
    er["evidence_ids"] = ["src-a"]
    raw["slides"] = [er]
    raw["evidence_registry"] = {"src-a": raw["evidence_registry"]["src-a"]}
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert "Unsupported claim remains visible." in html
    assert "Source unavailable" in html
    assert "not-on-slide" not in html
    assert result["status"] in {"ok", "degraded"}


def test_nonstrict_recommendation_empty_support(tmp_path: Path):
    raw = _raw()
    rc = next(s for s in raw["slides"] if s["layout_type"] == "recommendation_case")
    rc["payload"]["rationales"] = [{"rationale_id": "bad"}]
    raw["slides"] = [rc]
    raw["evidence_registry"] = {"src-b": raw["evidence_registry"]["src-b"]}
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert "Stand up a single weekly" in html
    assert "Support unavailable" in html
    assert result["status"] in {"ok", "degraded"}


def test_nonstrict_risk_empty_group_marked(tmp_path: Path):
    raw = _raw()
    rr = next(s for s in raw["slides"] if s["layout_type"] == "risk_opportunity_review")
    rr["payload"]["opportunities"] = [{"item_id": "bad"}]
    raw["slides"] = [rr]
    raw["evidence_registry"] = {"src-a": raw["evidence_registry"]["src-a"]}
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert "Vendor concentration" in html
    assert "Opportunities unresolved" in html
    assert result["status"] in {"ok", "degraded"}


def test_nonstrict_feature_cards_sequential_fallback(tmp_path: Path):
    raw = _raw()
    fc = next(s for s in raw["slides"] if s["layout_type"] == "feature_cards")
    for c in fc["payload"]["cards"]:
        c["heading"] = "Heading " + ("Word " * 40)
        c["detail"] = "Detail " * 80
    # Six long cards force overflow.
    fc["payload"]["cards"] = [
        {
            "card_id": f"c{i}",
            "heading": "Heading " + ("Word " * 40),
            "detail": "Detail " * 80,
            "icon_key": "growth",
        }
        for i in range(6)
    ]
    raw["slides"] = [fc]
    raw["evidence_registry"] = {"src-a": raw["evidence_registry"]["src-a"]}
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "feature_cards")
    assert 'data-fallback="accessible_sequential_cards"' in html
    assert 'data-card-id="c0"' in html and 'data-card-id="c5"' in html
    assert plan["fallback"] == "accessible_sequential_cards"
    assert result["status"] == "degraded"


def test_strict_rejects_empty_finding_refs():
    raw = _raw()
    er = next(s for s in raw["slides"] if s["layout_type"] == "evidence_review")
    er["payload"]["findings"][0]["evidence_ids"] = []
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_empty_finding_refs_with_repair_marker():
    raw = _raw()
    er = next(s for s in raw["slides"] if s["layout_type"] == "evidence_review")
    er["payload"]["findings"][0]["evidence_ids"] = []
    er["payload"]["findings"][0]["refs_repaired"] = True
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_empty_risk_group():
    raw = _raw()
    rr = next(s for s in raw["slides"] if s["layout_type"] == "risk_opportunity_review")
    rr["payload"]["risks"] = []
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_empty_risk_group_with_repair_marker():
    raw = _raw()
    rr = next(s for s in raw["slides"] if s["layout_type"] == "risk_opportunity_review")
    rr["payload"]["risks"] = []
    rr["payload"]["groups_repaired"] = True
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_empty_rationales():
    raw = _raw()
    rc = next(s for s in raw["slides"] if s["layout_type"] == "recommendation_case")
    rc["payload"]["rationales"] = []
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_empty_rationales_with_repair_marker():
    raw = _raw()
    rc = next(s for s in raw["slides"] if s["layout_type"] == "recommendation_case")
    rc["payload"]["rationales"] = []
    rc["payload"]["support_repaired"] = True
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_nonstrict_quote_provenance_unavailable(tmp_path: Path):
    raw = _raw()
    q = next(s for s in raw["slides"] if s["layout_type"] == "quotation")
    q["payload"]["quotes"][0]["evidence_id"] = "not-on-slide"
    raw["slides"] = [q]
    raw["evidence_registry"] = {"src-a": raw["evidence_registry"]["src-a"]}
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert "We need one operating rhythm" in html
    assert "A. Rivera" in html
    assert "Provenance unavailable" in html


def test_nonstrict_quote_provenance_survives_overflow_fallback(tmp_path: Path):
    raw = _raw()
    q = next(s for s in raw["slides"] if s["layout_type"] == "quotation")
    q["payload"]["quotes"] = [
        {
            "quote_id": f"q{i}",
            "paragraphs": [("Long quote body " * 40).strip()],
            "attribution": {
                "name": f"Speaker {i}",
                "role": "Operator",
                "organization": "Field Ops",
            },
            "evidence_id": "not-on-slide",
        }
        for i in range(3)
    ]
    raw["slides"] = [q]
    raw["evidence_registry"] = {"src-a": raw["evidence_registry"]["src-a"]}
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "quotation")
    assert plan["fallback"]
    assert "card-comp-fallback" in html
    assert html.count("Provenance unavailable") >= 3
    assert "Speaker 0" in html and "Speaker 2" in html
    assert result["status"] == "degraded"


def test_recommendation_multi_row_rationales_overflow(tmp_path: Path):
    raw = _raw()
    rc = next(s for s in raw["slides"] if s["layout_type"] == "recommendation_case")
    rc["payload"]["rationales"] = [
        {
            "rationale_id": f"r{i}",
            "statement": {
                "runs": [{"text": ("Tall rationale statement " * 30).strip()}]
            },
            "detail": {
                "runs": [{"text": ("Extra detail lines " * 20).strip()}]
            },
        }
        for i in range(6)
    ]
    raw["slides"] = [rc]
    raw["evidence_registry"] = {"src-b": raw["evidence_registry"]["src-b"]}
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "recommendation_case")
    assert plan["fallback"]
    assert "card-comp-fallback" in html
    assert 'data-rationale-id="r0"' in html and 'data-rationale-id="r5"' in html
    assert result["status"] == "degraded"


def test_recommendation_four_rationales_use_three_col_grid(tmp_path: Path):
    raw = _raw()
    rc = next(s for s in raw["slides"] if s["layout_type"] == "recommendation_case")
    rc["payload"]["rationales"] = [
        {
            "rationale_id": f"r{i}",
            "statement": {"runs": [{"text": f"Rationale statement {i}."}]},
        }
        for i in range(4)
    ]
    raw["slides"] = [rc]
    raw["evidence_registry"] = {"src-b": raw["evidence_registry"]["src-b"]}
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "recommendation_case")
    assert 'class="rationale-row cols-3"' in html
    assert 'data-rationale-id="r0"' in html and 'data-rationale-id="r3"' in html
    assert plan["fallback"] is None
    assert 'data-fallback=' not in html
    assert result["status"] == "clean"


def test_state_transition_near_overflow_uses_sequential_fallback(tmp_path: Path):
    raw = _raw()
    st = next(s for s in raw["slides"] if s["layout_type"] == "state_transition")
    long_para = {
        "runs": [
            {
                "text": (
                    "Near-overflow state copy that wraps tightly across the column. "
                    * 18
                ).strip()
            }
        ]
    }
    st["payload"]["before"]["blocks"] = [
        {
            "type": "paragraphs",
            "block_id": "bb1",
            "paragraphs": [long_para, long_para],
        }
    ]
    st["payload"]["after"]["blocks"] = [
        {
            "type": "paragraphs",
            "block_id": "ab1",
            "paragraphs": [long_para, long_para],
        }
    ]
    st["payload"]["transition_steps"] = [
        {
            "step_id": f"s{i}",
            "heading": f"Step {i} heading with extra words",
            "detail": (
                "Transition detail that also wraps in the middle column. " * 8
            ).strip(),
        }
        for i in range(4)
    ]
    raw["slides"] = [st]
    raw["evidence_registry"] = {"src-a": raw["evidence_registry"]["src-a"]}
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "state_transition")
    assert plan["fallback"]
    assert "card-comp-fallback" in html
    assert "Before" in html and "After" in html and "Transition" in html
    assert 'data-step-id="s0"' in html and 'data-step-id="s3"' in html
    assert result["status"] == "degraded"


def test_state_transition_step_tall_triggers_sequential_fallback(tmp_path: Path):
    """Steps column is the tall path; fit must match paint padding/gaps."""
    raw = _raw()
    st = next(s for s in raw["slides"] if s["layout_type"] == "state_transition")
    short = {"runs": [{"text": "Short state."}]}
    st["payload"]["before"]["blocks"] = [
        {"type": "paragraphs", "block_id": "bb1", "paragraphs": [short]}
    ]
    st["payload"]["after"]["blocks"] = [
        {"type": "paragraphs", "block_id": "ab1", "paragraphs": [short]}
    ]
    st["payload"]["transition_steps"] = [
        {
            "step_id": f"s{i}",
            "heading": f"Step {i} " + ("heading words " * 6).strip(),
            "detail": (
                "Step detail that fills the middle column and forces overflow. " * 10
            ).strip(),
        }
        for i in range(4)
    ]
    raw["slides"] = [st]
    raw["evidence_registry"] = {"src-a": raw["evidence_registry"]["src-a"]}
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "state_transition")
    assert plan["fallback"]
    assert "card-comp-fallback" in html
    assert 'data-step-id="s0"' in html and 'data-step-id="s3"' in html
    assert "Short state." in html
    assert result["status"] == "degraded"


def test_nonstrict_drops_forbidden_common_fields():
    raw = _raw()
    er = next(s for s in raw["slides"] if s["layout_type"] == "evidence_review")
    er["source_footer"] = ["src-a"]
    rc = next(s for s in raw["slides"] if s["layout_type"] == "recommendation_case")
    rc["takeaway"] = {"text": "drop me"}
    result = validate_handoff(raw, strict=False)
    assert result.repaired is True
    by = {s.layout_type: s for s in result.deck.slides}
    assert not hasattr(by["evidence_review"], "source_footer") or getattr(
        by["evidence_review"], "source_footer", None
    ) is None
    assert getattr(by["recommendation_case"], "takeaway", None) is None

def _risk_surface(items, box_h=10**9):
    return SurfacePlan(
        surface_id="t-risk",
        role="risk_opportunity_review",
        slide_number=1,
        slide_index=0,
        layout_type="risk_opportunity_review",
        slot_order=10,
        design_stage_region=1,
        role_sizes={"heading": 22, "body": 18},
        _box_w=1728,
        _box_h=box_h,
        _card_spec={
            "kind": "risk_opportunity_review",
            "risks": items,
            "opportunities": items,
        },
    )


def test_item_statement_trailing_margin_in_fit_height():
    """`.item-statement` always paints mb 4; statement-only items must budget it."""
    stmt = "Short statement."
    one = [{"item_id": "r0", "statement": stmt}]
    with_detail = [{"item_id": "r0", "statement": stmt, "detail": "Detail."}]
    ok1, h_stmt = _card_fit_detail(_risk_surface(one), 18)
    ok2, h_both = _card_fit_detail(_risk_surface(with_detail), 18)
    assert ok1 and ok2
    # detail adds exactly one body line; statement margin applies in both cases
    assert h_both - h_stmt == _line_box(CARD_FIXED_BODY_PX)


def test_recommendation_statement_margin_always_counted():
    stmt = "Rationale statement."
    def rec(detail=None):
        r = {"statement": stmt}
        if detail is not None:
            r["detail"] = detail
        return SurfacePlan(
            surface_id="t-rec",
            role="recommendation_case",
            slide_number=1,
            slide_index=0,
            layout_type="recommendation_case",
            slot_order=10,
            design_stage_region=1,
            role_sizes={"heading": 22, "body": 18},
            _box_w=1728,
            _box_h=10**9,
            _card_spec={
                "kind": "recommendation_case",
                "recommendation": "Do the thing.",
                "rationales": [r],
                "cols": 1,
                "rows": 1,
            },
        )
    ok_a, h_a = _card_fit_detail(rec(), 18)
    ok_b, h_b = _card_fit_detail(rec("Extra."), 18)
    assert ok_a and ok_b
    assert h_b - h_a == _line_box(CARD_FIXED_BODY_PX)


def test_state_list_indent_uses_list_indent_em():
    """Bullet measure width shrinks by ceil(body_px * LIST_INDENT_EM), not hard-coded 20."""
    import math
    import impact_slides.renderer_v3.plan as plan_mod

    body_px = CARD_FIXED_BODY_PX
    expected_indent = math.ceil(body_px * LIST_INDENT_EM)
    assert expected_indent == 23  # body 18 * 1.25

    # 65× "ab" wraps 3 lines at indent 23 and 2 at indent 20 (max_lines=3).
    long_item = " ".join(["ab"] * 65)
    sp = SurfacePlan(
        surface_id="t-st",
        role="state_transition",
        slide_number=1,
        slide_index=0,
        layout_type="state_transition",
        slot_order=10,
        design_stage_region=1,
        role_sizes={"heading": 22, "body": body_px, "meta": 14},
        _box_w=1728,
        _box_h=10**9,
        _card_spec={
            "kind": "state_transition",
            "before": {
                "heading": "Before",
                "blocks": [
                    {
                        "type": "bullet_list",
                        "items": [long_item, long_item],
                    }
                ],
            },
            "after": {
                "heading": "After",
                "blocks": [{"type": "paragraphs", "paragraphs": ["Short."]}],
            },
            "steps": [],
        },
    )
    ok, h = _card_fit_detail(sp, body_px)
    assert ok
    # Simulate hard-coded 20px indent via LIST_INDENT_EM so ceil(body*em)=20
    real = plan_mod.LIST_INDENT_EM
    plan_mod.LIST_INDENT_EM = 20 / body_px
    try:
        ok2, h20 = _card_fit_detail(sp, body_px)
    finally:
        plan_mod.LIST_INDENT_EM = real
    assert ok2
    assert h > h20, f"paint indent must wrap more than 20px (h={h} h20={h20})"


def test_state_panel_css_single_list_indent(tmp_path: Path):
    """Emitted paint: state-panel ul uses padding-left:0; li keep one global indent."""
    raw = _raw()
    st = next(s for s in raw["slides"] if s["layout_type"] == "state_transition")
    st["payload"]["before"]["blocks"] = [
        {
            "block_id": "b-bullets",
            "type": "bullet_list",
            "items": [
                {"runs": [{"text": "First before bullet"}]},
                {"runs": [{"text": "Second before bullet"}]},
            ],
        }
    ]
    raw["slides"] = [st]
    raw["evidence_registry"] = {"src-a": raw["evidence_registry"]["src-a"]}
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    # Public HTML contract: bullets under state-panel, single list indent in CSS.
    assert 'class="state-panel' in html
    assert "<ul>" in html
    assert "First before bullet" in html
    assert ".state-panel ul{margin:0 0 4px;padding-left:0}" in html
    assert ".state-panel ul{margin:0 0 4px;padding-left:1.25em}" not in html
    # Global li indent remains exactly once (not also on the ul).
    assert "li{margin:0;padding:0;margin-left:1.25em}" in html


def test_evidence_review_near_overflow_uses_sequential_fallback(tmp_path: Path):
    raw = _raw()
    er = next(s for s in raw["slides"] if s["layout_type"] == "evidence_review")
    long_stmt = {
        "runs": [{"text": ("Evidence finding statement that wraps and stacks. " * 20).strip()}]
    }
    er["payload"]["findings"] = [
        {
            "finding_id": f"f{i}",
            "statement": long_stmt,
            "evidence_ids": ["src-a"],
        }
        for i in range(6)
    ]
    er["evidence_ids"] = ["src-a"]
    raw["slides"] = [er]
    raw["evidence_registry"] = {"src-a": raw["evidence_registry"]["src-a"]}
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "evidence_review")
    assert plan["fallback"]
    assert "card-comp-fallback" in html
    assert result["status"] == "degraded"


def test_risk_opportunity_near_overflow_uses_sequential_fallback(tmp_path: Path):
    raw = _raw()
    risk = next(s for s in raw["slides"] if s["layout_type"] == "risk_opportunity_review")
    long_stmt = {
        "runs": [{"text": ("Risk or opportunity statement that fills the column. " * 16).strip()}]
    }
    long_detail = {
        "runs": [{"text": ("Supporting detail that also wraps in the card. " * 10).strip()}]
    }
    items = [
        {"item_id": f"x{i}", "statement": long_stmt, "detail": long_detail}
        for i in range(5)
    ]
    risk["payload"]["risks"] = items
    risk["payload"]["opportunities"] = [
        {**it, "item_id": f"o{i}"} for i, it in enumerate(items)
    ]
    raw["slides"] = [risk]
    raw["evidence_registry"] = {"src-a": raw["evidence_registry"]["src-a"]}
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "risk_opportunity_review")
    assert plan["fallback"]
    assert "card-comp-fallback" in html
    assert result["status"] == "degraded"


def test_state_bullet_list_budgets_one_ul_margin():
    """Paint applies one ul margin-bottom; fit must not charge CARD_MARGIN per li."""
    body = CARD_FIXED_BODY_PX

    def st(n: int) -> SurfacePlan:
        return SurfacePlan(
            surface_id="t-st",
            role="state_transition",
            slide_number=1,
            slide_index=0,
            layout_type="state_transition",
            slot_order=10,
            design_stage_region=1,
            role_sizes={"heading": 22, "body": body, "meta": 14},
            _box_w=1728,
            _box_h=10**9,
            _card_spec={
                "kind": "state_transition",
                "before": {
                    "heading": "Before",
                    "blocks": [
                        {"type": "bullet_list", "items": ["Short bullet."] * n}
                    ],
                },
                "after": {
                    "heading": "After",
                    "blocks": [{"type": "paragraphs", "paragraphs": ["S"]}],
                },
                "steps": [],
            },
        )

    _, h1 = _card_fit_detail(st(1), body)
    _, h4 = _card_fit_detail(st(4), body)
    assert h4 - h1 == 3 * _line_box(body)


def test_card_panel_hairline_border_budgeted_in_fit_height():
    """Each .card-panel box budgets CARD_PANEL_BORDER_Y (theme hairline top+bottom)."""
    body = CARD_FIXED_BODY_PX
    stmt = "Short statement."

    def risk(n_items: int) -> SurfacePlan:
        items = [{"item_id": f"r{i}", "statement": stmt} for i in range(n_items)]
        return SurfacePlan(
            surface_id="t-risk-border",
            role="risk_opportunity_review",
            slide_number=1,
            slide_index=0,
            layout_type="risk_opportunity_review",
            slot_order=10,
            design_stage_region=1,
            role_sizes={"heading": 22, "body": body},
            _box_w=1728,
            _box_h=10**9,
            _card_spec={
                "kind": "risk_opportunity_review",
                "risks": items,
                "opportunities": items,
            },
        )

    _, h1 = _card_fit_detail(risk(1), body)
    _, h2 = _card_fit_detail(risk(2), body)
    # Second stacked item adds: RISK_GROUP_GAP(12) + pad*2 + border + stmt line + CARD_MARGIN
    from impact_slides.renderer_v3.plan import CARD_PAD, RISK_GROUP_GAP

    delta = h2 - h1
    expected = (
        RISK_GROUP_GAP
        + CARD_PAD
        + CARD_PANEL_BORDER_Y
        + _line_box(body)
        + CARD_MARGIN
        + CARD_PAD
    )
    assert delta == expected


def test_empty_marker_card_panel_border_budgeted():
    """Empty group-unresolved / support-unavailable markers budget panel border, not p margin."""
    body = CARD_FIXED_BODY_PX
    heading = CARD_FIXED_HEADING_PX

    empty_only = SurfacePlan(
        surface_id="t-empty-only",
        role="risk_opportunity_review",
        slide_number=1,
        slide_index=0,
        layout_type="risk_opportunity_review",
        slot_order=10,
        design_stage_region=1,
        role_sizes={"heading": heading, "body": body},
        _box_w=1728,
        _box_h=10**9,
        _card_spec={
            "kind": "risk_opportunity_review",
            "risks": [],
            "opportunities": [],
        },
    )
    ok, h_empty = _card_fit_detail(empty_only, body)
    assert ok
    marker = RISK_GROUP_GAP + CARD_PAD + CARD_PANEL_BORDER_Y + _line_box(body) + CARD_PAD
    assert h_empty == _line_box(heading) + marker + BLOCK_MARGIN_Y

    no_support = SurfacePlan(
        surface_id="t-no-support",
        role="recommendation_case",
        slide_number=1,
        slide_index=0,
        layout_type="recommendation_case",
        slot_order=10,
        design_stage_region=1,
        role_sizes={"heading": heading, "body": body},
        _box_w=1728,
        _box_h=10**9,
        _card_spec={
            "kind": "recommendation_case",
            "recommendation": "Do it.",
            "rationales": [],
            "cols": 0,
            "rows": 0,
        },
    )
    ok_n, h_n = _card_fit_detail(no_support, body)
    assert ok_n
    # recommendation-panel + support-unavailable marker, each with hairline border.
    expected = (
        CARD_PAD
        + CARD_PANEL_BORDER_Y
        + _line_box(heading)
        + CARD_MARGIN
        + _line_box(body)
        + CARD_PAD
        + CARD_GAP
        + CARD_PAD
        + CARD_PANEL_BORDER_Y
        + _line_box(body)
        + CARD_PAD
        + BLOCK_MARGIN_Y
    )
    assert h_n == expected


def test_quote_card_figure_margin_reset_in_emitted_css(tmp_path: Path):
    """Public HTML zeros figure/figcaption UA margin on .quote-card."""
    raw = _raw()
    q = next(s for s in raw["slides"] if s["layout_type"] == "quotation")
    raw["slides"] = [q]
    raw["evidence_registry"] = {"src-a": raw["evidence_registry"]["src-a"]}
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'class="quote-card card-panel"' in html
    assert ".quote-card{flex:1 1 0;min-width:0;margin:0;padding:16px;box-sizing:border-box}" in html
    assert ".quote-card figcaption{margin:0}" in html
    assert ".group-unresolved{margin:0;padding:16px;font-style:italic}" in html
    assert ".support-unavailable{margin:0;padding:16px;font-style:italic}" in html


def test_feature_cards_sync_finalizes_detail_size():
    """_synchronize re-finalizes every member so feature detail tracks synced heading."""

    def fc(sid: str, heading_size: int) -> SurfacePlan:
        return SurfacePlan(
            surface_id=sid,
            role="feature_cards",
            slide_number=1,
            slide_index=0,
            layout_type="feature_cards",
            slot_order=10,
            design_stage_region=1,
            role_sizes={"heading": heading_size, "detail": FEATURE_BODY_FLOOR},
            _box_w=1728,
            _box_h=10**9,
            _fit_role="heading",
            _mode="adaptive",
            _default_size=FEATURE_BODY_FLOOR,
            _maximum_size=28,
            _sync_group="feature-sync",
            _card_spec={
                "kind": "feature_cards",
                "cards": [{"id": "c0", "heading": "H", "detail": "D"}],
                "cols": 1,
                "rows": 1,
            },
        )

    low = fc("t-fc-low", FEATURE_BODY_FLOOR)
    high = fc("t-fc-high", 28)
    events: list = []
    _synchronize([low, high], events)
    for sp in (low, high):
        assert sp.role_sizes["heading"] == 28
        assert sp.role_sizes["detail"] == 28
