"""Renderer v3 brand, section divider, and legal compositions (#191).

Covers D178–D182, D215, D223, D225–D226, D268–D271, D287:
- cover/divider placement + renderer-owned chrome
- legal multipart sequence + exact paragraphs
- invalid placement / fit → complete fallback without moving content
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.models import (
    LegalNoticeSlide,
    SectionDividerSlide,
)
from impact_slides.renderer_v3.plan import plan_deck

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/renderer_v3/brand_divider_legal.json"
MINIMAL = ROOT / "tests/fixtures/renderer_v3/minimal_cover_narrative_cover.json"


def _brand() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _minimal() -> dict:
    return json.loads(MINIMAL.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_brand_fixture_validates_typed_kernel():
    result = validate_handoff(_brand(), strict=True)
    assert result.ok
    layouts = [s.layout_type for s in result.deck.slides]
    assert layouts == [
        "opening_cover",
        "section_divider",
        "narrative",
        "section_divider",
        "legal_notice",
        "legal_notice",
        "closing_cover",
    ]
    assert isinstance(result.deck.slides[1], SectionDividerSlide)
    assert isinstance(result.deck.slides[4], LegalNoticeSlide)
    assert result.deck.slides[4].payload.title == "Important disclosures"
    assert result.deck.slides[5].payload.title is None
    assert result.deck.slides[5].payload.part == 2


def test_plan_emits_divider_and_legal_surfaces():
    deck = validate_handoff(_brand(), strict=True).deck
    plan = plan_deck(deck, strict=True)
    by = plan.by_surface_id()
    assert "slide-1-cover" in by
    assert "slide-2-divider" in by
    assert by["slide-2-divider"].role_sizes["title"] == 56
    assert "slide-5-legal" in by
    assert by["slide-5-legal"].role_sizes["body"] == 16
    assert "slide-6-legal" in by
    assert "slide-7-cover" in by


def test_fixed_surface_fit_reserves_renderer_chrome():
    raw = _brand()
    raw["sections"][0]["label"] = " ".join(["MMMMMMMMMM"] * 34)
    with pytest.raises(RendererValidationError):
        plan_deck(validate_handoff(raw, strict=True).deck, strict=True)


def test_legal_fit_preserves_hard_and_empty_lines():
    raw = _brand()
    raw["slides"][4]["payload"]["paragraphs"] = ["\n".join([""] * 51)]
    with pytest.raises(RendererValidationError):
        plan_deck(validate_handoff(raw, strict=True).deck, strict=True)


def test_publish_paints_registry_label_and_legal_continuation(tmp_path: Path):
    out = tmp_path / "out"
    result = render_deck(FIXTURE, out, strict=True)
    assert result["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-layout="section_divider"' in html
    assert "Overview" in html
    assert "Section 1" in html
    assert "Legal" in html
    assert "Section 2" in html
    assert "Important disclosures" in html
    assert "— continued" in html
    assert "This material is for informational purposes only" in html
    assert "Recipients may not redistribute without prior written consent." in html
    assert 'data-notice-id="disclaimer"' in html
    assert 'data-part="2"' in html
    assert 'data-total-parts="2"' in html
    # Cover chrome band present; no invented brand wording.
    assert "cover-band" in html
    assert "divider-rule" in html
    notes = (out / "slide_notes.md").read_text(encoding="utf-8")
    assert "Important disclosures" in notes
    assert "— continued" in notes
    assert "Overview" in notes  # divider notes heading uses registry label
    assert "Read the full notice aloud if asked." in notes


# ---------------------------------------------------------------------------
# Placement + sequence contracts
# ---------------------------------------------------------------------------


def test_divider_must_precede_first_ordinary_slide():
    raw = _brand()
    # Move overview divider after its narrative.
    div = raw["slides"][1]
    narr = raw["slides"][2]
    raw["slides"][1] = narr
    raw["slides"][2] = div
    with pytest.raises(RendererValidationError) as ei:
        validate_handoff(raw, strict=True)
    assert any("immediately precede" in (e.expected.contract if e.expected else "")
               or "immediately precede" in e.code
               or "immediately" in ((e.expected.contract if e.expected else "") + e.path)
               for e in ei.value.events) or any(
        "immediately" in str(e) for e in ei.value.events
    )


def test_duplicate_divider_for_section_fails():
    raw = _brand()
    raw["slides"].insert(
        3,
        {
            "slide_number": 99,
            "layout_type": "section_divider",
            "payload": {"section_id": "overview"},
        },
    )
    # renumber uniqueness
    for i, s in enumerate(raw["slides"], start=1):
        s["slide_number"] = i
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_divider_forbids_root_title_and_payload_prose():
    raw = _brand()
    raw["slides"][1]["title"] = "nope"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)
    raw = _brand()
    raw["slides"][1]["payload"]["label"] = "Override"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_legal_part1_requires_title_later_forbids():
    raw = _brand()
    del raw["slides"][4]["payload"]["title"]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)
    raw = _brand()
    raw["slides"][5]["payload"]["title"] = "cont"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_legal_parts_must_be_adjacent_complete_sequence():
    raw = _brand()
    # Gap: drop part 2
    raw["slides"] = [s for s in raw["slides"] if s["slide_number"] != 6]
    for i, s in enumerate(raw["slides"], start=1):
        s["slide_number"] = i
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_legal_forbids_takeaway_disclosure_footer():
    raw = _brand()
    raw["slides"][4]["takeaway"] = {"text": "nope"}
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


@pytest.mark.parametrize("slide_index", [0, 1, 4])
def test_all_evidence_bearing_compositions_reject_duplicate_ids(slide_index: int):
    raw = _brand()
    raw["slides"][slide_index]["evidence_ids"] = ["src-board-pack", "src-board-pack"]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_legal_preserves_exact_paragraph_boundaries(tmp_path: Path):
    raw = _brand()
    # Internal whitespace + punctuation must survive paint (exact, no rewrite).
    raw["slides"][4]["payload"]["paragraphs"] = [
        "Line one  has  double spaces.",
        "Em-dash --- and (parentheses) stay exact.",
    ]
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(path, out, strict=True)
    assert result["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    plain = html.replace("<wbr>", "")
    assert "Line one  has  double spaces." in plain
    assert "Em-dash --- and (parentheses) stay exact." in plain


# ---------------------------------------------------------------------------
# Non-strict / fallback
# ---------------------------------------------------------------------------


def test_nonstrict_drops_unknown_divider_fields():
    raw = _brand()
    raw["slides"][1]["payload"]["kicker"] = "nope"
    result = validate_handoff(raw, strict=False)
    assert result.ok
    assert result.repaired
    assert "kicker" not in result.deck.slides[1].payload.model_dump()


def test_misplaced_opening_cover_stays_failed_not_moved():
    """D268: misplaced covers are not reordered; stay invalid."""
    raw = _minimal()
    slides = raw["slides"]
    raw["slides"] = [slides[1], slides[0], slides[2]]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=False)


# ---------------------------------------------------------------------------
# Mutation traps
# ---------------------------------------------------------------------------


def test_mutation_swap_legal_part_order_fails():
    raw = _brand()
    p1 = raw["slides"][4]
    p2 = raw["slides"][5]
    raw["slides"][4] = p2
    raw["slides"][5] = p1
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_mutation_divider_unknown_section_fails():
    raw = _brand()
    raw["slides"][1]["payload"]["section_id"] = "missing"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_mutation_legal_section_mismatch_across_parts_fails():
    raw = _brand()
    # Point part 2 at overview while keeping legal section used by part 1 only
    # would break contiguity / matching — force mismatch on part 2.
    raw["slides"][5]["section_id"] = "overview"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_fixture_file_is_strict_valid():
    assert FIXTURE.is_file()
    assert validate_handoff(deepcopy(_brand()), strict=True).ok
