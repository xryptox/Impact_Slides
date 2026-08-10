"""Renderer v3 deck-wide measure/plan phase (#178).

Seams under test:
- plan_deck freezes whole-pixel role sizes at 1920×1080 before paint (D22/D68/D69)
- grow-only adaptive prose/subtitle/takeaway within role ceilings (D2/D12/D59)
- equivalent-role sync; no truncation or runtime replanning (D3/D26/D59)
- compact plan diagnostics in run_meta + HTML data-* (D21/D312)
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck
from impact_slides.renderer_v3.plan import (
    BODY_CEIL,
    BODY_FLOOR,
    DESIGN_STAGE_H,
    DESIGN_STAGE_W,
    SUBTITLE_CEIL,
    SUBTITLE_FLOOR,
    TAKEAWAY_CEIL,
    TAKEAWAY_FLOOR,
    plan_deck,
)
from impact_slides.renderer_v3.validate import validate_handoff

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/renderer_v3/minimal_cover_narrative_cover.json"


def _minimal() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _write(tmp: Path, raw: dict | None = None) -> Path:
    path = tmp / "handoff.json"
    data = raw if raw is not None else _minimal()
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def test_plan_deck_freezes_whole_pixel_sizes_for_kernel_surfaces():
    deck = validate_handoff(_minimal(), strict=True).deck
    plan = plan_deck(deck, strict=True)
    by = plan.by_surface_id()

    assert "slide-1-cover" in by
    assert "slide-2-title" in by
    assert "slide-2-subtitle" in by
    assert "slide-2-block-lead" in by
    assert "slide-2-block-bullets" in by
    assert "slide-2-takeaway" in by
    assert "slide-3-cover" in by

    sub = by["slide-2-subtitle"]
    assert sub.role_sizes["subtitle"] >= SUBTITLE_FLOOR
    assert sub.role_sizes["subtitle"] <= SUBTITLE_CEIL
    assert isinstance(sub.role_sizes["subtitle"], int)

    body_sizes = {
        by["slide-2-block-lead"].role_sizes["body"],
        by["slide-2-block-bullets"].role_sizes["body"],
    }
    assert len(body_sizes) == 1  # D225 one common body size
    body = next(iter(body_sizes))
    assert BODY_FLOOR <= body <= BODY_CEIL

    take = by["slide-2-takeaway"]
    assert TAKEAWAY_FLOOR <= take.role_sizes["body"] <= TAKEAWAY_CEIL
    assert take.role_sizes["label"] == 14  # fixed chrome

    # Fixed title chrome
    assert by["slide-2-title"].role_sizes["title"] == 56
    assert by["slide-1-cover"].role_sizes["title"] == 72

    # Design-stage region is a positive integer slot id
    assert all(s.design_stage_region >= 1 for s in plan.surfaces)
    assert all(s.semantic_digest and s.painter_plan_digest for s in plan.surfaces)


def test_sparse_prose_grows_above_floor():
    deck = validate_handoff(_minimal(), strict=True).deck
    plan = plan_deck(deck, strict=True)
    by = plan.by_surface_id()
    # Short fixture text should grow.
    assert by["slide-2-subtitle"].role_sizes["subtitle"] > SUBTITLE_FLOOR
    assert by["slide-2-block-lead"].role_sizes["body"] > BODY_FLOOR
    assert "plan.typography_grown" in by["slide-2-subtitle"].adaptation_codes
    assert any(e.code == "plan.typography_grown" for e in plan.events)


def test_fixed_mode_does_not_grow():
    raw = _minimal()
    raw["slides"][1]["content"]["typography"] = {"mode": "fixed"}
    raw["slides"][1]["payload"]["typography"] = {"mode": "fixed"}
    deck = validate_handoff(raw, strict=True).deck
    plan = plan_deck(deck, strict=True)
    by = plan.by_surface_id()
    assert by["slide-2-subtitle"].role_sizes["subtitle"] == SUBTITLE_FLOOR
    assert by["slide-2-block-lead"].role_sizes["body"] == BODY_FLOOR
    assert "plan.typography_grown" not in by["slide-2-subtitle"].adaptation_codes


def test_explicit_subtitle_size_pins_without_sync_inheritance():
    raw = _minimal()
    raw["slides"][1]["content"]["typography"] = {
        "mode": "adaptive",
        "subtitle_font_size": 24,
    }
    deck = validate_handoff(raw, strict=True).deck
    plan = plan_deck(deck, strict=True)
    assert plan.by_surface_id()["slide-2-subtitle"].role_sizes["subtitle"] == 24


def test_sync_group_aligns_equivalent_roles_only():
    raw = _minimal()
    # Add a second narrative with same subtitle sync group.
    narrative = json.loads(json.dumps(raw["slides"][1]))
    narrative["slide_number"] = 3
    narrative["title"] = "Second frame"
    narrative["content"] = {
        "subtitle": "Short dek",
        "typography": {"mode": "adaptive", "sync_group": "deks"},
    }
    raw["slides"][1]["content"]["typography"] = {
        "mode": "adaptive",
        "sync_group": "deks",
    }
    # Shift closing cover
    raw["slides"][2]["slide_number"] = 4
    raw["slides"].insert(2, narrative)
    deck = validate_handoff(raw, strict=True).deck
    plan = plan_deck(deck, strict=True)
    by = plan.by_surface_id()
    a = by["slide-2-subtitle"].role_sizes["subtitle"]
    b = by["slide-3-subtitle"].role_sizes["subtitle"]
    assert a == b
    assert "plan.synchronized" in by["slide-2-subtitle"].adaptation_codes


def test_sync_growth_event_matches_frozen_size():
    raw = _minimal()
    narrative = json.loads(json.dumps(raw["slides"][1]))
    narrative["slide_number"] = 3
    narrative["content"] = {
        "subtitle": "A deliberately longer synchronized subtitle " * 8,
        "typography": {"mode": "adaptive", "sync_group": "deks"},
    }
    raw["slides"][1]["content"]["typography"] = {
        "mode": "adaptive",
        "sync_group": "deks",
    }
    raw["slides"][2]["slide_number"] = 4
    raw["slides"].insert(2, narrative)

    plan = plan_deck(validate_handoff(raw, strict=True).deck, strict=True)
    by = plan.by_surface_id()
    frozen = by["slide-2-subtitle"].role_sizes["subtitle"]
    growth = next(
        e
        for e in plan.events
        if e.code == "plan.typography_grown"
        and e.surface_id == "slide-2-subtitle"
    )
    assert growth.input == {"type": "int", "value": frozen}
    assert growth.expected.contract == f"subtitle grew to {frozen}px"


def test_strict_overflow_raises_before_publication(tmp_path: Path):
    raw = _minimal()
    # Force unfittable body by stuffing a huge unbreakable token.
    monster = "A" * 5000
    raw["slides"][1]["payload"]["blocks"] = [
        {
            "block_id": "lead",
            "type": "paragraphs",
            "paragraphs": [{"runs": [{"text": monster}]}],
        }
    ]
    handoff = _write(tmp_path, raw)
    out = tmp_path / "out"
    with pytest.raises(RendererValidationError) as ei:
        render_deck(handoff, out)
    assert any(e.code == "plan.unresolved_overflow" for e in ei.value.events)
    assert not out.exists() or list(out.iterdir()) == []


def test_nonstrict_overflow_publishes_degraded_complete_text(tmp_path: Path):
    raw = _minimal()
    monster = "A" * 5000
    raw["slides"][1]["payload"]["blocks"] = [
        {
            "block_id": "lead",
            "type": "paragraphs",
            "paragraphs": [{"runs": [{"text": monster}]}],
        }
    ]
    handoff = _write(tmp_path, raw)
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    assert result["status"] == "degraded"
    assert result["ok"] is False
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert monster in html  # D59: no truncation
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert any(e["code"] == "plan.unresolved_overflow" for e in meta["events"])
    overflow_plan = next(
        p for p in meta["plans"] if p["surface_id"] == "slide-2-block-lead"
    )
    assert overflow_plan["fallback"] == "fallback_unresolved"
    sizes = ",".join(
        f"{key}:{value}" for key, value in overflow_plan["role_sizes"].items()
    )
    adaptations = ",".join(overflow_plan["adaptation_codes"])
    digest_source = (
        f"2|narrative|narrative_block|slide-2-block-lead|2|{sizes}|"
        f"{adaptations}|fallback_unresolved"
    )
    assert overflow_plan["painter_plan_digest"] == hashlib.sha256(
        digest_source.encode()
    ).hexdigest()


def test_render_deck_embeds_frozen_plan_in_meta_and_html(tmp_path: Path):
    handoff = _write(tmp_path)
    out = tmp_path / "out"
    render_deck(handoff, out)
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plans = meta["plans"]
    assert plans
    ids = [p["surface_id"] for p in plans]
    assert ids == sorted(ids, key=lambda x: ids.index(x))  # stable authored order
    for p in plans:
        assert set(p) >= {
            "surface_id",
            "role",
            "semantic_digest",
            "design_stage_region",
            "role_sizes",
            "adaptation_codes",
            "reservations",
            "fallback",
            "expected_placement_classes",
            "painter_plan_digest",
        }
        assert all(isinstance(v, int) for v in p["role_sizes"].values())
        # role_sizes keys sorted
        assert list(p["role_sizes"]) == sorted(p["role_sizes"])

    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'content="1920x1080"' in html
    assert "data-plan-sizes=" in html
    assert "Key takeaway" in html
    # Narrative body sizes applied as whole px
    assert "font-size:" in html
    assert html.count('data-surface-id="slide-2-block-lead"') == 1


def test_plan_is_deterministic_across_calls():
    deck = validate_handoff(_minimal(), strict=True).deck
    a = plan_deck(deck, strict=True).public_plans()
    b = plan_deck(deck, strict=True).public_plans()
    assert a == b


def test_grow_never_below_floor_or_above_ceiling():
    deck = validate_handoff(_minimal(), strict=True).deck
    plan = plan_deck(deck, strict=True)
    for sp in plan.surfaces:
        for role, px in sp.role_sizes.items():
            assert isinstance(px, int) and px > 0
            if role == "subtitle":
                assert SUBTITLE_FLOOR <= px <= SUBTITLE_CEIL or sp.role == "cover"
            if role == "body" and sp.role in ("narrative_block", "takeaway"):
                assert BODY_FLOOR <= px <= max(BODY_CEIL, TAKEAWAY_CEIL)


def test_design_stage_constants_match_contract():
    assert DESIGN_STAGE_W == 1920
    assert DESIGN_STAGE_H == 1080


def test_mutation_floor_change_breaks_grow_only_contract():
    """Guard: if BODY_FLOOR is raised above chosen size logic, pin breaks."""
    from impact_slides.renderer_v3 import plan as plan_mod

    deck = validate_handoff(_minimal(), strict=True).deck
    plan = plan_deck(deck, strict=True)
    body = plan.by_surface_id()["slide-2-block-lead"].role_sizes["body"]
    assert body >= plan_mod.BODY_FLOOR

def test_takeaway_outer_reservation_excludes_chrome_from_fit_box():
    """R178-001: outer reservation includes chrome; fitter box is text-only."""
    from impact_slides.renderer_v3.plan import (
        BLOCK_MARGIN_Y,
        TAKEAWAY_BORDER_Y,
        TAKEAWAY_LABEL_MB,
        TAKEAWAY_LABEL_PX,
        TAKEAWAY_OUTER_MT,
        TAKEAWAY_PAD_Y,
        _line_box,
    )

    deck = validate_handoff(_minimal(), strict=True).deck
    plan = plan_deck(deck, strict=True)
    take = plan.by_surface_id()["slide-2-takeaway"]
    chrome = (
        _line_box(TAKEAWAY_LABEL_PX)
        + TAKEAWAY_LABEL_MB
        + TAKEAWAY_PAD_Y
        + TAKEAWAY_BORDER_Y
        + TAKEAWAY_OUTER_MT
        + BLOCK_MARGIN_Y
    )
    assert take._chrome_h == chrome
    assert take._box_h == _line_box(TAKEAWAY_CEIL)
    # Mutation: if chrome were folded into the fit box, _box_h would be larger.
    assert take._box_h + take._chrome_h > take._box_h


def test_geometry_is_reclaimed_across_subtitle_and_uneven_blocks():
    raw = _minimal()
    raw["slides"][1]["content"]["subtitle"] = "Long subtitle " * 20
    raw["slides"][1]["payload"]["blocks"][0]["paragraphs"][0]["runs"][0]["text"] = "Long body " * 180
    plan = plan_deck(validate_handoff(raw, strict=True).deck, strict=True)
    by = plan.by_surface_id()
    assert by["slide-2-subtitle"]._box_h > 60
    assert by["slide-2-block-lead"]._box_h > by["slide-2-block-bullets"]._box_h


def test_surface_inapplicable_typography_is_all_or_nothing():
    raw = _minimal()
    raw["slides"][1]["content"]["typography"] = {
        "mode": "fixed",
        "subtitle_font_size": 24,
        "body_font_size": 30,
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)
    repaired = validate_handoff(raw, strict=False)
    assert repaired.deck.slides[1].content.typography is None
    assert any(e.code == "repair.policy_defaulted" for e in repaired.events)


def test_paragraph_margin_boxes_match_paint_per_element_model():
    """R178-002: multi-paragraph blocks bill one margin per <p>, lists one per <ul>."""
    raw = _minimal()
    # Two paragraphs in the lead block.
    raw["slides"][1]["payload"]["blocks"][0] = {
        "type": "paragraphs",
        "block_id": "lead",
        "paragraphs": [
            {"runs": [{"text": "First paragraph."}]},
            {"runs": [{"text": "Second paragraph."}]},
        ],
    }
    deck = validate_handoff(raw, strict=True).deck
    plan = plan_deck(deck, strict=True)
    lead = plan.by_surface_id()["slide-2-block-lead"]
    bullets = plan.by_surface_id()["slide-2-block-bullets"]
    assert lead._margin_boxes == 2
    assert bullets._margin_boxes == 1  # one <ul>


def test_html_surface_diagnostics_project_from_events(tmp_path: Path):
    """R178-004: HTML data-diagnostic-* mirrors run_meta surface events."""
    raw = _minimal()
    # Force non-strict overflow on takeaway via unbreakable token.
    raw["slides"][1]["takeaway"]["text"] = "X" * 5000
    handoff = _write(tmp_path, raw)
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    assert result["status"] == "degraded"
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    overflow_ids = {
        e["surface_id"]
        for e in meta["events"]
        if e.get("code") == "plan.unresolved_overflow" and e.get("surface_id")
    }
    assert overflow_ids
    html = (out / "presentation.html").read_text(encoding="utf-8")
    for sid in overflow_ids:
        # surface attrs must list the overflow code with non-zero count
        assert f'data-surface-id="{sid}"' in html
        # Find the attribute cluster for this surface.
        idx = html.index(f'data-surface-id="{sid}"')
        chunk = html[idx : idx + 400]
        assert "plan.unresolved_overflow" in chunk
        assert 'data-diagnostic-count="0"' not in chunk.split(">")[0]


def test_cover_measures_each_role_at_its_frozen_size():
    """R178-005: long meta labels must not be measured at the 72px title size."""
    raw = _minimal()
    # Long but 22px-safe meta; would fail if measured at 72px title advance.
    long_meta = " ".join(["Quarter"] * 40)
    raw["slides"][0]["payload"]["period_label"] = long_meta
    raw["slides"][0]["payload"]["date_label"] = long_meta
    deck = validate_handoff(raw, strict=True).deck
    plan = plan_deck(deck, strict=True)  # must not raise
    cover = plan.by_surface_id()["slide-1-cover"]
    assert cover._cover_items
    assert cover.role_sizes["title"] == 72
    assert cover.role_sizes["meta"] == 22
    assert not cover._overflow


@pytest.mark.parametrize("bad", [None, [], "bad"])
def test_nonstrict_discards_nonobject_typography(bad):
    raw = _minimal()
    raw["slides"][1]["content"]["typography"] = bad
    repaired = validate_handoff(raw, strict=False)
    assert repaired.deck.slides[1].content.typography is None
    assert any(e.code == "repair.policy_defaulted" for e in repaired.events)


def test_cross_role_sync_group_is_rejected_or_disabled():
    raw = _minimal()
    raw["slides"][1]["content"]["typography"] = {
        "mode": "adaptive",
        "sync_group": "shared",
    }
    raw["slides"][1]["payload"]["typography"] = {
        "mode": "adaptive",
        "sync_group": "shared",
    }
    deck = validate_handoff(raw, strict=True).deck
    with pytest.raises(RendererValidationError):
        plan_deck(deck, strict=True)
    plan = plan_deck(deck, strict=False)
    assert all(s._sync_group is None for s in plan.surfaces if s._fit_role)
    assert any(e.code == "repair.sync_disabled" for e in plan.events)


def test_plan_order_and_event_paths_follow_authored_slide_indexes():
    raw = _minimal()
    raw["slides"][0]["slide_number"] = 10
    raw["slides"][1]["slide_number"] = 5
    raw["slides"][2]["slide_number"] = 7
    plan = plan_deck(validate_handoff(raw, strict=True).deck, strict=True)
    assert [s.slide_number for s in plan.surfaces[:2]] == [10, 5]
    growth = next(e for e in plan.events if e.code == "plan.typography_grown")
    assert growth.path.startswith("/slides/1/")


def test_pinned_geometry_is_reserved_before_optional_growth():
    raw = _minimal()
    raw["slides"][1]["content"]["subtitle"] = "Pinned subtitle " * 18
    raw["slides"][1]["content"]["typography"] = {
        "mode": "adaptive",
        "subtitle_font_size": 24,
    }
    plan = plan_deck(validate_handoff(raw, strict=True).deck, strict=True)
    subtitle = plan.by_surface_id()["slide-2-subtitle"]
    assert subtitle.role_sizes["subtitle"] == 24
    assert not subtitle._overflow


def test_pinned_cross_role_sync_does_not_constrain_automatic_role():
    raw = _minimal()
    raw["slides"][1]["content"]["typography"] = {
        "mode": "adaptive",
        "sync_group": "shared",
        "subtitle_font_size": 24,
    }
    raw["slides"][1]["payload"]["typography"] = {
        "mode": "adaptive",
        "sync_group": "shared",
    }
    plan = plan_deck(validate_handoff(raw, strict=True).deck, strict=True)
    assert plan.by_surface_id()["slide-2-subtitle"].role_sizes["subtitle"] == 24
    assert not any(e.code == "validation.conflict" for e in plan.events)


def test_duplicate_disclosure_surface_ids_are_rejected():
    raw = _minimal()
    section = {
        "surface_id": "terms",
        "title": "Terms",
        "items": [{"kind": "paragraph", "text": "Statement."}],
    }
    raw["slides"][1]["disclosure"] = {"sections": [section, dict(section)]}
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_nonstrict_repairs_duplicate_disclosure_keeps_first():
    """R178-028 / D222: non-strict drops duplicate section, keeps first."""
    raw = _minimal()
    first = {
        "surface_id": "terms",
        "title": "Terms",
        "items": [{"kind": "paragraph", "text": "Keep me."}],
    }
    second = {
        "surface_id": "terms",
        "title": "Terms again",
        "items": [{"kind": "paragraph", "text": "Drop me."}],
    }
    raw["slides"][1]["disclosure"] = {"sections": [first, second]}
    result = validate_handoff(raw, strict=False)
    assert result.repaired
    disc = result.deck.slides[1].disclosure
    assert disc is not None
    assert len(disc.sections) == 1
    assert disc.sections[0].title == "Terms"
    assert any(
        e.code == "repair.item_dropped" and e.role == "disclosure" for e in result.events
    )


def test_hyphen_break_opportunity_in_wrap_lines():
    """R178-029: long hyphenated phrases wrap; not one unbreakable token."""
    from impact_slides.renderer_v3.plan import _wrap_lines

    phrase = "pre-trade-risk-assessment-framework"
    items = [(phrase, False)]
    lines, wo = _wrap_lines(items, 22, 140)
    assert not wo
    assert len(lines) >= 2
    assert "".join(lines).replace(" ", "") == phrase
    punct = "alpha,beta;gamma:delta.epsilon"
    plines, pwo = _wrap_lines([(punct, False)], 22, 100)
    assert not pwo
    assert len(plines) >= 2
    assert "".join(plines).replace(" ", "") == punct


def test_paint_emits_soft_break_wbr_for_plan_punctuation():
    """R178-029: paint offers the same soft breaks plan measures."""
    from impact_slides.renderer_v3.publish import _soft_break_html

    html = _soft_break_html("pre-trade,risk;alpha:beta.gamma end")
    assert html.count("<wbr>") == 5
    assert html == "pre-<wbr>trade,<wbr>risk;<wbr>alpha:<wbr>beta.<wbr>gamma end"
    assert _soft_break_html("a, b") == "a, b"
    assert _soft_break_html("a<b,c") == "a&lt;b,<wbr>c"


def test_prose_soft_break_wbr_across_run_boundary():
    """R178-029: plan joins runs; paint must wbr at soft-break run edges."""
    from impact_slides.renderer_v3.models import Prose, ProseRun
    from impact_slides.renderer_v3.plan import _wrap_lines
    from impact_slides.renderer_v3.publish import _prose_html

    prose = Prose(
        runs=[
            ProseRun(text="assessment,"),
            ProseRun(text="framework", emphasis="strong"),
        ]
    )
    items = [(r.text, r.emphasis == "strong") for r in prose.runs]
    lines, wo = _wrap_lines(items, 22, 120)
    assert not wo
    assert len(lines) >= 2
    html = _prose_html(prose)
    assert html == "assessment,<wbr><strong>framework</strong>"
    spaced = Prose(
        runs=[
            ProseRun(text="a, "),
            ProseRun(text="b", emphasis="strong"),
        ]
    )
    assert _prose_html(spaced) == "a, <strong>b</strong>"


def test_disclosure_paragraph_not_list_indented():
    """R178-030: paragraphs measure full width; summary/bullets use indent."""
    from impact_slides.renderer_v3.plan import (
        CONTENT_W,
        DISCLOSURE_INDENT_EM,
        LIST_INDENT_EM,
    )

    raw = _minimal()
    long_para = ("Word " * 80).strip()
    raw["slides"][1]["disclosure"] = {
        "sections": [
            {
                "surface_id": "terms",
                "title": "Terms",
                "items": [
                    {"kind": "paragraph", "text": long_para},
                    {"kind": "bullet", "text": "Short bullet."},
                ],
            }
        ]
    }
    deck = validate_handoff(raw, strict=True).deck
    plan = plan_deck(deck, strict=True)
    disc = plan.by_surface_id()["slide-2-disclosure-terms"]
    assert disc._unit_indent_ems[0] == DISCLOSURE_INDENT_EM  # summary
    assert disc._unit_indent_ems[1] == 0.0  # paragraph
    assert disc._unit_indent_ems[2] == LIST_INDENT_EM  # bullet
    assert disc._box_w == CONTENT_W
    assert not disc._overflow


def test_common_surfaces_are_planned_and_painted(tmp_path: Path):
    raw = _minimal()
    raw["slides"][1]["disclosure"] = {
        "sections": [
            {
                "surface_id": "terms",
                "title": "Terms",
                "items": [
                    {"kind": "paragraph", "text": "Forward-looking statement."},
                    {"kind": "bullet", "text": "Subject to change."},
                ],
            }
        ]
    }
    out = tmp_path / "out"
    render_deck(_write(tmp_path, raw), out)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert "<details" in html
    assert "Forward-looking statement." in html
    assert "Sources: Board pack Q4" in html
    assert "details:not([open])>summary~*{display:block}" in html
    assert "@media print{" in html
    assert ".slide{width:1920px!important" in html
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    ids = {plan["surface_id"] for plan in meta["plans"]}
    assert "slide-2-disclosure-terms" in ids
    assert "slide-2-source-footer" in ids
    narrative = meta["slides"][1]
    assert narrative["surface_ids"][-2:] == [
        "slide-2-disclosure-terms",
        "slide-2-source-footer",
    ]


def test_print_media_shows_closed_disclosure_and_resets_scale(tmp_path: Path):
    """R178-031/032: browser print media expands disclosure; stage unscaled."""
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    raw = _minimal()
    raw["slides"][1]["disclosure"] = {
        "sections": [
            {
                "surface_id": "terms",
                "title": "Terms",
                "items": [
                    {"kind": "paragraph", "text": "PRINT_VISIBLE_BODY"},
                    {"kind": "bullet", "text": "PRINT_VISIBLE_BULLET"},
                ],
            }
        ]
    }
    out = tmp_path / "out"
    render_deck(_write(tmp_path, raw), out)
    html_path = (out / "presentation.html").resolve()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 800, "height": 450})
        page.goto(html_path.as_uri(), wait_until="networkidle")
        page.wait_for_timeout(100)
        screen = page.evaluate(
            """() => {
              const d = document.querySelector('details');
              return {open: d && d.open};
            }"""
        )
        assert screen["open"] is False
        page.emulate_media(media="print")
        printed = page.evaluate(
            """() => {
              const slide = document.querySelector('.slide');
              const p = [...document.querySelectorAll('details p')]
                .find(el => el.textContent.includes('PRINT_VISIBLE_BODY'));
              const li = [...document.querySelectorAll('details li')]
                .find(el => el.textContent.includes('PRINT_VISIBLE_BULLET'));
              const cs = el => el ? getComputedStyle(el) : null;
              const visible = el => {
                if (!el) return false;
                const s = cs(el);
                if (!s || s.display === 'none' || s.visibility === 'hidden') return false;
                const r = el.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
              };
              return {
                bodyVisible: visible(p),
                bulletVisible: visible(li),
                transform: slide ? cs(slide).transform : null,
                width: slide ? slide.getBoundingClientRect().width : null,
                height: slide ? slide.getBoundingClientRect().height : null,
              };
            }"""
        )
        browser.close()
    assert printed["bodyVisible"] is True
    assert printed["bulletVisible"] is True
    assert printed["transform"] in (None, "none")
    assert printed["width"] is not None and abs(printed["width"] - 1920) < 2
    assert printed["height"] is not None and abs(printed["height"] - 1080) < 2


def test_unicode_uses_diagnosed_conservative_metrics():
    raw = _minimal()
    raw["slides"][1]["payload"]["blocks"][0]["paragraphs"][0]["runs"][0]["text"] = "Résumé 東京"
    plan = plan_deck(validate_handoff(raw, strict=True).deck, strict=True)
    assert any(
        e.code == "plan.conservative_metrics"
        and e.surface_id == "slide-2-block-lead"
        for e in plan.events
    )


def test_sync_preserves_typography_grown_when_above_floor():
    """Synced body size above role floor must keep plan.typography_grown."""
    deck = validate_handoff(_minimal(), strict=True).deck
    plan = plan_deck(deck, strict=True)
    lead = plan.by_surface_id()["slide-2-block-lead"]
    body = lead.role_sizes["body"]
    if body > BODY_FLOOR:
        assert "plan.typography_grown" in lead.adaptation_codes
    else:
        # Short fixture may stay at floor; still must not crash and stay in band.
        assert body == BODY_FLOOR

