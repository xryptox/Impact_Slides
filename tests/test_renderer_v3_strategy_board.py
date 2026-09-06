"""Renderer v3 strategy_board composition (#295).

Seams under test:
- closed layout_type strategy_board (not hierarchy / layered_architecture /
  stakeholder_map / feature_cards)
- authored mission + 0–2 bands + 2–4 pillars + optional footer
- unique semantic ids; leftover hierarchy keys rejected
- plan freeze at 1920×1080 with existing card type floors
- fit/paint CSS parity for pad/font/gap/list indent
- non-strict sequential sections fallback keeps every authored string
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.migrate import INVENTORY_SIZE, LEGACY_INVENTORY, migrate_handoff
from impact_slides.renderer_v3.plan import (
    BLOCK_MARGIN_Y,
    CARD_FIXED_BODY_PX,
    CARD_FIXED_HEADING_PX,
    CARD_GAP,
    CARD_INNER_GAP,
    CARD_MARGIN,
    CARD_PAD,
    CARD_PANEL_BORDER_Y,
    LIST_INDENT_EM,
    SurfacePlan,
    _card_fit_detail,
    _line_box,
    plan_deck,
)
from impact_slides.renderer_v3.schema_export import check_schema

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/renderer_v3/strategy_board.json"


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
    assert [s.layout_type for s in result.deck.slides] == [
        "strategy_board",
        "strategy_board",
    ]
    plan = plan_deck(result.deck, strict=True)
    boards = [s for s in plan.surfaces if s.role == "strategy_board"]
    assert len(boards) == 2
    for sp in boards:
        assert sp.role_sizes["heading"] == CARD_FIXED_HEADING_PX
        assert sp.role_sizes["body"] == CARD_FIXED_BODY_PX
        assert sp.fallback is None


def test_minimal_board_paints_mission_and_two_pillars(tmp_path: Path):
    raw = _deck([_raw()["slides"][0]])
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(handoff, out, strict=True)["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-layout="strategy_board"' in html
    assert 'data-band-id="mission"' in html
    assert "Build a more sustainable, equitable company." in html
    assert 'data-pillar-id="dei"' in html
    assert html.index('data-pillar-id="dei"') < html.index('data-pillar-id="climate"')
    assert "Diversity, Equity and Inclusion" in html
    assert "Expand diverse representation." in html
    assert "Cut operational emissions." in html
    start = html.index('data-layout="strategy_board"')
    chunk = html[start : html.find('</section>', html.find('strategy-board', start) + 1) + 10]
    # CSS may mention .strategy-bands; the painted body must omit the row.
    assert 'class="strategy-bands"' not in chunk
    assert 'class="strategy-footer' not in chunk
    assert "Centurion" not in html
    assert "linear-connector" not in chunk


def test_full_board_paints_bands_pillars_and_footer(tmp_path: Path):
    raw = _deck([_raw()["slides"][1]])
    raw["slides"][0]["slide_number"] = 1
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(handoff, out, strict=True)["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    start = html.index('data-layout="strategy_board"')
    end = html.find('id="slide-2"', start)
    if end < 0:
        end = html.find("</main>", start)
    chunk = html[start:end]
    assert 'data-band-id="esg-mission"' in chunk
    assert "most respected service brand." in chunk
    assert "Serve customers, colleagues, and communities." in chunk
    assert chunk.index('data-band-id="stakeholders"') < chunk.index(
        'data-band-id="governance"'
    )
    assert "Colleagues, customers, communities, and shareholders." in chunk
    assert chunk.index('data-pillar-id="dei-full"') < chunk.index(
        'data-pillar-id="confidence"'
    )
    assert chunk.index('data-pillar-id="confidence"') < chunk.index(
        'data-pillar-id="climate-full"'
    )
    assert 'data-item-id="dei-a"' in chunk
    assert "Hire and promote diverse talent." in chunk
    assert 'data-stack-id="committees"' in chunk
    assert chunk.index('data-item-id="c-nom"') < chunk.index('data-item-id="c-audit"')
    assert "Nominating and Governance" in chunk
    assert "→" not in chunk
    assert "Centurion" not in chunk


def test_strict_rejects_one_pillar():
    raw = _raw()
    raw["slides"] = [raw["slides"][0]]
    raw["slides"][0]["payload"]["pillars"] = raw["slides"][0]["payload"]["pillars"][:1]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_empty_mission():
    raw = _raw()
    raw["slides"] = [raw["slides"][0]]
    raw["slides"][0]["payload"]["mission"]["heading"] = ""
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_duplicate_ids():
    raw = _raw()
    raw["slides"] = [raw["slides"][0]]
    raw["slides"][0]["payload"]["pillars"][1]["pillar_id"] = "dei"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


@pytest.mark.parametrize("key", ["nodes", "relationship"])
def test_strict_rejects_leftover_hierarchy_keys(key: str):
    raw = _raw()
    raw["slides"] = [raw["slides"][0]]
    raw["slides"][0]["payload"][key] = (
        "part_of" if key == "relationship" else [{"node_id": "n1"}]
    )
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_nonstrict_overflow_paints_sequential_fallback(tmp_path: Path):
    raw = _raw()
    slide = raw["slides"][1]
    slide["slide_number"] = 1
    long = "Word " * 80
    slide["payload"]["mission"]["heading"] = "Mission " + long
    slide["payload"]["mission"]["detail"] = "Detail " + long
    for band in slide["payload"]["bands"]:
        band["heading"] = "Band " + long
        band["detail"] = "Band detail " + long
    slide["payload"]["pillars"] = [
        {
            "pillar_id": f"p{i}",
            "heading": "Pillar " + long,
            "items": [
                {"item_id": f"p{i}-a", "text": "Item A " + long},
                {"item_id": f"p{i}-b", "text": "Item B " + long},
                {"item_id": f"p{i}-c", "text": "Item C " + long},
                {"item_id": f"p{i}-d", "text": "Item D " + long},
                {"item_id": f"p{i}-e", "text": "Item E " + long},
                {"item_id": f"p{i}-f", "text": "Item F " + long},
            ],
        }
        for i in range(4)
    ]
    slide["payload"]["footer"]["items"] = [
        {"item_id": f"f{i}", "text": "Committee " + long} for i in range(6)
    ]
    raw["slides"] = [slide]
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    with pytest.raises(RendererValidationError):
        render_deck(handoff, out, strict=True)
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["role"] == "strategy_board")
    assert plan["fallback"] == "accessible_sequential_sections"
    assert 'data-fallback="accessible_sequential_sections"' in html
    assert "Mission " in html
    assert "Detail " in html
    assert "Band " in html
    assert "Pillar " in html
    assert "Item A " in html and "Item F " in html
    assert "Committee " in html
    assert 'data-pillar-id="p0"' in html and 'data-pillar-id="p3"' in html
    assert 'data-item-id="f5"' in html
    assert "→" not in html.split("strategy_board", 1)[-1][:4000]
    assert result["status"] == "degraded"


def test_fit_height_budgets_painted_gap_pad_and_list_indent():
    heading = CARD_FIXED_HEADING_PX
    body = CARD_FIXED_BODY_PX
    mission = "Build a more sustainable company."
    pillar_h = "Climate"
    item = "Cut operational emissions."

    def board(n_items: int) -> SurfacePlan:
        return SurfacePlan(
            surface_id="t-board",
            role="strategy_board",
            slide_number=1,
            slide_index=0,
            layout_type="strategy_board",
            slot_order=10,
            design_stage_region=1,
            role_sizes={"heading": heading, "body": body},
            _box_w=1728,
            _box_h=10**9,
            _card_spec={
                "kind": "strategy_board",
                "mission": {"id": "mission", "heading": mission, "detail": None},
                "bands": [],
                "pillars": [
                    {
                        "id": "p0",
                        "heading": pillar_h,
                        "items": [item] * n_items,
                    },
                    {
                        "id": "p1",
                        "heading": pillar_h,
                        "items": [item],
                    },
                ],
                "footer": None,
            },
        )

    ok1, h1 = _card_fit_detail(board(1), body)
    ok2, h2 = _card_fit_detail(board(2), body)
    assert ok1 and ok2
    assert h2 - h1 == _line_box(body)
    assert h1 > 0


def test_painted_css_matches_fit_constants(tmp_path: Path):
    raw = _deck([_raw()["slides"][0]])
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert ".strategy-board{display:flex;flex-direction:column;gap:16px;" in html
    assert f"gap:{CARD_GAP}px" in html
    assert ".strategy-mission{padding:16px;" in html
    assert f"padding:{CARD_PAD}px" in html
    assert ".strategy-pillar ul,.strategy-footer ul{margin:0 0 4px;padding-left:0}" in html
    assert "li{margin:0;padding:0;margin-left:1.25em}" in html
    assert math.isclose(LIST_INDENT_EM, 1.25)
    assert CARD_MARGIN == 4
    assert CARD_INNER_GAP == 8
    assert CARD_PANEL_BORDER_Y == 2
    assert BLOCK_MARGIN_Y == 12


def test_strategy_board_has_inventory_line_without_v2_mapping(tmp_path: Path):
    """#295: kernel-native layout has no v2 mapping; D313 inventory stays 57."""
    assert "strategy_board" not in LEGACY_INVENTORY
    assert INVENTORY_SIZE == 57
    src = tmp_path / "in.json"
    src.write_text(
        json.dumps(
            {
                "presentation": {"title": "Legacy Deck", "subtitle": ""},
                "slides": [
                    {
                        "slide_number": 1,
                        "layout_type": "strategy_board",
                        "title": "ESG",
                        "speaker_notes": "Kernel-native; no v2 mapping.",
                    }
                ],
            }
        ),
        encoding="utf-8",
        newline="\n",
    )
    result = migrate_handoff(src, out_dir=tmp_path / "out", check=True)
    d = result.slide_dispositions[0]
    assert d.status == "unresolved"
    assert d.legacy_input == "strategy_board"
    assert d.target is None


def test_does_not_overload_existing_layouts():
    from impact_slides.renderer_v3.models import KERNEL_LAYOUTS, LAYOUT_TYPES

    assert "strategy_board" in LAYOUT_TYPES
    assert "strategy_board" in KERNEL_LAYOUTS
    for name in (
        "hierarchy",
        "layered_architecture",
        "stakeholder_map",
        "feature_cards",
    ):
        assert name in LAYOUT_TYPES
        assert name != "strategy_board"
