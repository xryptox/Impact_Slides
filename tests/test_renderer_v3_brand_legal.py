"""Renderer v3 brand, section divider, and legal compositions (#191/#232/#238/#270).

Covers D178–D182, D215, D223, D225–D226, D268–D271, D287:
- cover/divider placement + renderer-owned chrome
- legal multipart sequence + exact paragraphs
- unmarked-only legal bodies paint as <p> blocks; marked lines stay <ul>
- invalid placement / fit → complete fallback without moving content
- legal wrapper-<li> indent matches plan on skipped/leading nests
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.models import (
    LegalNoticeSlide,
    SectionDividerSlide,
)
from impact_slides.renderer_v3.plan import (
    LEGAL_BODY_PX,
    LEGAL_TITLE_PX,
    LIST_INDENT_EM,
    plan_deck,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/renderer_v3/brand_divider_legal.json"
MINIMAL = ROOT / "tests/fixtures/renderer_v3/minimal_cover_narrative_cover.json"


def _brand() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _minimal() -> dict:
    return json.loads(MINIMAL.read_text(encoding="utf-8"))
_VOID_TAGS = {"br", "wbr", "meta", "link", "img", "hr", "input"}

_BRAND_SELECTOR_RULES = [
    ".cover .subtitle,.cover .period,.cover .date",
    ".section-divider .divider-meta",
    ".section-divider .divider-rule",
    ".legal-notice h1",
    ".legal-notice .legal-body p",
    ".legal-notice .legal-body li",
    ".legal-notice .legal-part",
]


def _emitted_rules(html: str) -> dict:
    """Parse the emitted <style> block into selector-list -> declarations."""
    style = html.split("<style>", 1)[1].split("</style>", 1)[0]
    return {
        m.group(1).strip(): m.group(2)
        for m in re.finditer(r"([^{}/]+)\{([^{}]*)\}", style)
    }


def _emitted_elements(html: str) -> list:
    """Collect (tag, classes, parent index) for every painted element."""

    class _Collector(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.elements = []
            self.stack = []

        def handle_starttag(self, tag, attrs):
            classes = set(dict(attrs).get("class", "").split())
            parent = self.stack[-1] if self.stack else None
            self.elements.append((tag, classes, parent))
            if tag not in _VOID_TAGS:
                self.stack.append(len(self.elements) - 1)

        def handle_endtag(self, tag):
            for i in range(len(self.stack) - 1, -1, -1):
                if self.elements[self.stack[i]][0] == tag:
                    del self.stack[i:]
                    break

    collector = _Collector()
    collector.feed(html)
    return collector.elements


def _simple_selector_matches(tag, classes, simple):
    parts = simple.split(".")
    if parts[0] and parts[0] != tag:
        return False
    return all(cls in classes for cls in parts[1:])


def _selector_matches(elements, index, selector):
    simple = selector.split()
    tag, classes, parent = elements[index]
    if not _simple_selector_matches(tag, classes, simple[-1]):
        return False
    remaining = simple[:-1]
    while remaining and parent is not None:
        a_tag, a_classes, parent = elements[parent]
        if _simple_selector_matches(a_tag, a_classes, remaining[-1]):
            remaining = remaining[:-1]
    return not remaining


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
    assert by["slide-5-legal"].role_sizes["title"] == LEGAL_TITLE_PX
    assert by["slide-5-legal"].role_sizes["body"] == LEGAL_BODY_PX
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
    assert html.count("Important disclosures") >= 2
    assert "\u2014 continued" not in html and "— continued" not in html
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


def test_legal_type_scale_is_largest_strict_pair():
    """#257: one fixed pair, largest that still strict-fits all six Amex parts."""
    assert (LEGAL_TITLE_PX, LEGAL_BODY_PX) == (56, 21)
    from impact_slides.renderer_v3 import plan as plan_mod

    amex = ROOT / "tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json"
    deck = validate_handoff(json.loads(amex.read_text(encoding="utf-8")), strict=True).deck
    plan_mod.LEGAL_BODY_PX = LEGAL_BODY_PX + 1
    try:
        with pytest.raises(RendererValidationError):
            plan_deck(deck, strict=True)
    finally:
        plan_mod.LEGAL_BODY_PX = LEGAL_BODY_PX


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


def test_legal_notice_paints_payload_list_hierarchy(tmp_path: Path):
    """R-D: legal payload bullets paint as <ul> hierarchy, not a paragraph wall."""
    raw = _brand()
    raw["slides"][4]["payload"]["paragraphs"] = [
        "Intro sentence stays a paragraph.",
        "- ability to grow EPS",
        "- ability to grow revenue",
    ]
    raw["slides"][5]["payload"]["paragraphs"] = [
        "- net card fees",
        "  - including premium cards",
        "Closing paragraph after the list.",
    ]
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(path, out, strict=True)["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    s5 = html.split('id="slide-5"', 1)[1].split("<section", 1)[0]
    s6 = html.split('id="slide-6"', 1)[1].split("<section", 1)[0]
    assert "<ul" in s5 and "<li" in s5
    assert "ability to grow EPS" in s5.replace("<wbr>", "")
    assert "ability to grow revenue" in s5.replace("<wbr>", "")
    assert s5.count("<li") == 2
    assert "<p" in s5 and "Intro sentence stays a paragraph." in s5.replace("<wbr>", "")
    assert s5.count("<ul") == 2
    assert "<ul" in s6 and s6.count("<ul") == 2
    assert "net card fees" in s6.replace("<wbr>", "")
    assert "including premium cards" in s6.replace("<wbr>", "")
    assert "Closing paragraph after the list." in s6.replace("<wbr>", "")
    compact = s6.replace("\n", "")
    assert "</li><ul" not in compact
    assert "net card fees<ul" in compact.replace("<wbr>", "")


def test_legal_plan_margin_boxes_match_painted_blocks():
    from impact_slides.renderer_v3.plan import _legal_body_blocks

    unmarked = ["grow EPS", "grow revenue"]
    mixed = ["Intro.", "- grow EPS", "- grow revenue", "Close."]
    assert _legal_body_blocks(unmarked) == [
        ("p", "grow EPS"),
        ("p", "grow revenue"),
    ]
    kinds = [kind for kind, _ in _legal_body_blocks(mixed)]
    assert kinds == ["p", "ul", "ul", "p"]

    deck = validate_handoff(_brand(), strict=True).deck
    plan = plan_deck(deck, strict=True)
    legal = next(s for s in plan.surfaces if s.surface_id == "slide-5-legal")
    assert legal._margin_boxes == len(_legal_body_blocks(deck.slides[4].payload.paragraphs))


def test_legal_notice_skipped_nest_wraps_lists(tmp_path: Path):
    raw = _brand()
    raw["slides"][4]["payload"]["paragraphs"] = [
        "    - leading grandchild",
        "- parent",
        "    - skipped grandchild",
    ]
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(path, out, strict=True)["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    s5 = html.split('id="slide-5"', 1)[1].split("<section", 1)[0]
    compact = s5.replace("\n", "").replace("<wbr>", "")
    assert "<ul><ul" not in compact
    assert "</li><ul" not in compact
    assert compact.count("<ul") == compact.count("</ul")
    assert compact.count("<li") == compact.count("</li")
    assert "leading grandchild" in compact
    assert "skipped grandchild" in compact
    assert ">parent<ul" in compact


@pytest.mark.parametrize(
    "paragraphs",
    [
        ["  - grandchild"],  # leading nest 0→1 (2 spaces)
        ["- parent", "  - grandchild"],  # adjacent 0→1 (regression)
        ["    - grandchild"],  # skipped 0→2 (4 spaces)
        ["- parent", "    - grandchild"],  # skipped 0→2 after a parent
    ],
    ids=[
        "leading-nest",
        "adjacent-0-1",
        "skipped-0-2",
        "parent-then-skip",
    ],
)
def test_legal_wrapper_li_indent_matches_planned_em(paragraphs, tmp_path: Path):
    """#238: wrapper <li>s resolve 1.25em at LEGAL_BODY_PX, not --text-body."""
    raw = _brand()
    raw["slides"][4]["payload"]["paragraphs"] = paragraphs
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    # strict render_deck plans via _cover_fits then paints; overflow would fail.
    assert render_deck(path, out, strict=True)["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    body = html.split('id="slide-5"', 1)[1].split("<section", 1)[0]
    body = body.split('legal-body">', 1)[1].split("</div>", 1)[0]
    # Every painted <li> (text + skipped-level wrappers) must carry the 16px
    # inline size the planner uses for em indent. Bare <li> inherits 22px.
    assert "<li>" not in body
    assert body.count("<li ") == body.count("</li>")
    for m in re.finditer(r"<li([^>]*)>", body):
        assert f"font-size:{LEGAL_BODY_PX}px" in m.group(1)


def test_legal_list_items_keep_only_authored_newlines(tmp_path: Path):
    raw = _brand()
    raw["slides"][4]["payload"]["paragraphs"] = [
        "- grow EPS",
        "- grow\nrevenue",
        "  - nested child",
    ]
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(path, out, strict=True)["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    s5 = html.split('id="slide-5"', 1)[1].split("<section", 1)[0]
    body = s5.split('legal-body">', 1)[1].split("</div>", 1)[0].strip()
    assert body.startswith("<ul")
    # Sibling <ul>s may sit on their own lines; each painted list stays compact.
    for block in re.split(r"(?<=</ul>)\s*(?=<ul)", body):
        assert block.startswith("<ul")
        assert ">\n" not in block
        assert "\n<" not in block
    assert "grow\nrevenue" in body.replace("<wbr>", "")


def test_unmarked_legal_paragraphs_paint_as_blocks(tmp_path: Path):
    """#270: unmarked-only legal bodies are paragraphs, never fake lists."""
    raw = _brand()
    raw["slides"][4]["payload"]["paragraphs"] = [
        "the company's ability to grow EPS",
        "the company's ability to grow revenue",
    ]
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(path, out, strict=True)["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    s5 = html.split('id="slide-5"', 1)[1].split("<section", 1)[0]
    body = s5.split('legal-body">', 1)[1].split("</div>", 1)[0]
    assert body.count("<p") == 2
    assert "<ul" not in body
    assert "<li" not in body
    # Mutation trap: flattening two unmarked paragraphs into one block must fail.
    assert "</p><p" in body.replace("\n", "")


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


@pytest.mark.parametrize(
    "slide_index,field,value",
    [
        (0, "title", "nope"),  # cover
        (1, "takeaway", {"text": "nope"}),  # divider
        (4, "source_footer", ["src-board-pack"]),  # legal
        (4, "content", {"blocks": []}),
        (5, "disclosure", {"sections": []}),
    ],
)
def test_nonstrict_keeps_forbidden_semantic_fields(slide_index, field, value):
    """D287/D180: non-strict must not silently delete forbidden semantic content."""
    raw = _brand()
    raw["slides"][slide_index][field] = value
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=False)
    # And the repair pass alone must leave the field in place.
    from impact_slides.renderer_v3.repairs import apply_allowlisted_repairs

    repaired, _events = apply_allowlisted_repairs(raw)
    assert field in repaired["slides"][slide_index]


def test_publish_css_selectors_match_brand_markup(tmp_path: Path):
    """Every brand selector alternative must resolve against painted markup."""
    out = tmp_path / "out"
    assert render_deck(FIXTURE, out, strict=True)["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    elements = _emitted_elements(html)
    rules = _emitted_rules(html)
    for selector_list in _BRAND_SELECTOR_RULES:
        assert selector_list in rules, selector_list
        for alternative in selector_list.split(","):
            matched = any(
                _selector_matches(elements, i, alternative)
                for i in range(len(elements))
            )
            assert matched, alternative
    assert "white-space:pre-wrap" in rules[".legal-notice .legal-body p"]
    assert "white-space:pre-wrap" in rules[".legal-notice .legal-body li"]
    assert rules[".legal-notice .legal-body ul ul"] == "margin:0"
    overflow_rule = ".legal-overflow,.cover-overflow,.divider-overflow"
    assert overflow_rule in rules
    assert "outline" in rules[overflow_rule]


def test_overflow_fallback_gets_visible_diagnosed_class():
    """Fallback surfaces get an overflow class covered by the outline rule."""
    from impact_slides.renderer_v3.publish import build_presentation_html

    raw = _brand()
    raw["sections"][0]["label"] = " ".join(["MMMMMMMMMM"] * 34)
    deck = validate_handoff(raw, strict=True).deck
    plan = plan_deck(deck, strict=False)
    assert any(s.fallback for s in plan.surfaces)
    html = build_presentation_html(deck, deck_plan=plan)
    elements = _emitted_elements(html)
    overflow_classes = {"legal-overflow", "cover-overflow", "divider-overflow"}
    overflowed = [i for i in range(len(elements)) if elements[i][1] & overflow_classes]
    assert overflowed
    rules = _emitted_rules(html)
    overflow_rule = ".legal-overflow,.cover-overflow,.divider-overflow"
    assert overflow_rule in rules
    assert "outline" in rules[overflow_rule]
    assert any(
        _selector_matches(elements, i, alternative)
        for i in overflowed
        for alternative in overflow_rule.split(",")
    )


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
