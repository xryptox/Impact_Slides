"""Renderer v3 annex + comparison table compositions (#180).

Seams under test:
- annex_table / grouped_annex_table / period_comparison / comparison_cards models
- D255 table reuse + D256 groups where allowed
- plan floors (12px annex, 20px period/cards) + metric strip exterior lane
- paint identity: navy headers, roles, peer cards, disclosure, fallbacks
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.plan import plan_deck
from impact_slides.renderer_v3.schema_export import check_schema

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/renderer_v3/annex_and_comparison_tables.json"


def _raw() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_schema_artifact_matches_models():
    check_schema(ROOT)


def test_fixture_validates_and_plans():
    result = validate_handoff(_raw(), strict=True)
    assert {s.layout_type for s in result.deck.slides} >= {
        "annex_table",
        "grouped_annex_table",
        "period_comparison",
        "comparison_cards",
    }
    plan = plan_deck(result.deck, strict=True)
    roles = {s.role for s in plan.surfaces}
    assert "annex_table" in roles
    assert "grouped_annex_table" in roles
    assert "period_comparison" in roles
    assert "metric_strip" in roles
    assert "comparison_cards" in roles


def test_annex_table_preserves_groups_units_disclosure(tmp_path: Path):
    out = tmp_path / "out"
    result = render_deck(FIXTURE, out, strict=True)
    assert result["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-layout="annex_table"' in html
    assert 'data-table-surface="annex-main"' in html
    assert "FY 2025" in html
    assert "Q1" in html and "25" in html
    assert "$100.5" in html
    assert "12.5%" in html
    assert "\u2014" in html or "—" in html  # missing margin
    assert 'id="slide-2-annex-notes"' in html
    assert "Annex notes" in html
    # No takeaway on annex.
    assert html.count("Key takeaway") == 2  # period + cards only


def test_grouped_annex_side_by_side_and_sync(tmp_path: Path):
    result = validate_handoff(_raw(), strict=True)
    plan = plan_deck(result.deck, strict=True)
    peers = [s for s in plan.surfaces if s.role == "grouped_annex_table"]
    assert len(peers) == 2
    sizes = {p.role_sizes["table"] for p in peers}
    assert len(sizes) == 1
    assert min(sizes) >= 12
    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert "grouped-annex" in html
    assert "US Consumer" in html
    assert "International" in html
    assert "grouped-annex-divider" in html
    assert 'data-table-surface="peer-us"' in html
    assert 'data-table-surface="peer-intl"' in html


def test_period_comparison_roles_and_metric_strip(tmp_path: Path):
    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-layout="period_comparison"' in html
    assert "period-comparison" in html
    assert 'data-metric-strip="period-strip"' in html
    assert "EPS" in html
    assert "$2.5" in html
    assert "Diluted" in html
    assert 'id="period-main-h-current_period"' in html
    assert 'id="period-main-h-comparison_period"' in html
    assert 'id="period-main-h-variance"' in html
    assert "Q4" in html and "25" in html
    assert "Revenue growth leads the print." in html


def test_comparison_cards_paint_all_facts(tmp_path: Path):
    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-layout="comparison_cards"' in html
    assert "comparison-cards cols-3" in html
    assert 'data-row-id="amex"' in html
    assert 'data-row-id="visa"' in html
    assert 'data-row-id="mc"' in html
    assert "24.0%" in html
    assert "3.2" in html  # pp growth
    assert "Lead" in html
    assert "Watch" in html
    # Missing growth remains visible missing marker.
    assert html.count("—") + html.count("\u2014") >= 1
    # Ordinary 3-fact boards stay text; the circular recipe is shape-gated.
    cards_start = html.index('class="comparison-cards cols-3')
    cards_tag = html[cards_start : html.index(">", cards_start)]
    assert "circular-dual-metric" not in cards_tag
    body = html[cards_start : html.index("</div>", cards_start)]
    assert "metric-circle" not in body


def _dual_metric_handoff() -> dict:
    return {
        "meta": {"handoff_schema_version": 1},
        "sections": [{"section_id": "earnings", "label": "Earnings"}],
        "number_formats": {
            "pct_0": {
                "unit": "percent",
                "value_decimals": 0,
                "negative_style": "parentheses",
            }
        },
        "evidence_registry": {
            "src-board-pack": {"source_name": "Board pack Q4"}
        },
        "slides": [
            {
                "slide_number": 1,
                "layout_type": "opening_cover",
                "payload": {"title": "Dual metric"},
                "evidence_ids": ["src-board-pack"],
            },
            {
                "slide_number": 2,
                "layout_type": "comparison_cards",
                "section_id": "earnings",
                "title": "U.S. Consumer: Membership Model Engagement",
                "payload": {
                    "table": {
                        "surface_id": "s7-cards",
                        "stub_header": {"label": "Peer"},
                        "columns": [
                            {"column_id": "premium", "label": "Premium growth"},
                            {"column_id": "ucs", "label": "UCS benchmark"},
                            {"column_id": "mult", "label": "Multiplier"},
                        ],
                        "rows": [
                            {
                                "row_id": "lodging",
                                "label": "Lodging",
                                "cells": {
                                    "premium": {
                                        "type": "number",
                                        "value": "50",
                                        "format_id": "pct_0",
                                    },
                                    "ucs": {
                                        "type": "number",
                                        "value": "5",
                                        "format_id": "pct_0",
                                    },
                                    "mult": {"type": "text", "text": "10x"},
                                },
                            },
                            {
                                "row_id": "restaurants",
                                "label": "Restaurants",
                                "cells": {
                                    "premium": {
                                        "type": "number",
                                        "value": "20",
                                        "format_id": "pct_0",
                                    },
                                    "ucs": {
                                        "type": "number",
                                        "value": "10",
                                        "format_id": "pct_0",
                                    },
                                    "mult": {"type": "text", "text": "2x"},
                                },
                            },
                            {
                                "row_id": "airlines",
                                "label": "Airlines",
                                "cells": {
                                    "premium": {
                                        "type": "number",
                                        "value": "21",
                                        "format_id": "pct_0",
                                    },
                                    "ucs": {
                                        "type": "number",
                                        "value": "11",
                                        "format_id": "pct_0",
                                    },
                                    "mult": {"type": "text", "text": "2x"},
                                },
                            },
                        ],
                    }
                },
                "evidence_ids": ["src-board-pack"],
            },
        ],
    }


def test_circular_dual_metric_plan_and_paint(tmp_path: Path):
    raw = _dual_metric_handoff()
    result = validate_handoff(raw, strict=True)
    plan = plan_deck(result.deck, strict=True)
    cards = next(s for s in plan.surfaces if s.role == "comparison_cards")
    assert cards.table_paint["recipe"] == "circular_dual_metric"
    assert cards.role_sizes["heading"] >= 22
    assert cards.role_sizes["caption"] >= 14
    assert cards.role_sizes["value"] >= 22

    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    cards_start = html.index('class="comparison-cards cols-3 circular-dual-metric')
    cards_html = html[cards_start : html.index('class="sr-only"', cards_start)]
    assert cards_html.count("metric-circle") == 6
    assert cards_html.count("dual-metric-connector") == 3
    for token in ("50%", "5%", "10x", "20%", "10%", "2x", "21%", "11%"):
        assert token in html
    assert "Premium growth" in html
    assert "UCS benchmark" in html
    assert "Lodging" in html and "Restaurants" in html and "Airlines" in html
    assert 'aria-hidden="true"' in html
    assert "sr-only-table" in html


def test_circular_dual_metric_mutation_keeps_text_board(tmp_path: Path):
    raw = _dual_metric_handoff()
    raw["slides"][1]["payload"]["table"]["rows"][0]["cells"]["mult"] = {
        "type": "text",
        "text": "Lead",
    }
    result = validate_handoff(raw, strict=True)
    plan = plan_deck(result.deck, strict=True)
    cards = next(s for s in plan.surfaces if s.role == "comparison_cards")
    assert cards.table_paint.get("recipe") != "circular_dual_metric"

    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    cards_start = html.index('class="comparison-cards cols-3')
    cards_tag = html[cards_start : html.index(">", cards_start)]
    assert "circular-dual-metric" not in cards_tag
    body = html[cards_start : html.index('class="sr-only"', cards_start)]
    assert "metric-circle" not in body
    assert "Lead" in html
    assert "10x" not in html


def test_period_comparison_rejects_wrong_column_ids():
    raw = _raw()
    slide = next(s for s in raw["slides"] if s["layout_type"] == "period_comparison")
    slide["payload"]["table"]["columns"][0]["column_id"] = "this_year"
    with pytest.raises(RendererValidationError) as ei:
        validate_handoff(raw, strict=True)
    assert any("current_period" in (e.expected or "") or "period_comparison" in (e.path or "")
               or "current_period" in str(e.__dict__)
               for e in ei.value.events) or "current_period" in str(ei.value)


def test_comparison_cards_rejects_groups():
    raw = _raw()
    slide = next(s for s in raw["slides"] if s["layout_type"] == "comparison_cards")
    slide["payload"]["table"]["column_groups"] = [
        {
            "group_id": "g1",
            "label": "Facts",
            "column_ids": ["share", "growth"],
        }
    ]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_annex_forbids_takeaway():
    raw = _raw()
    slide = next(s for s in raw["slides"] if s["layout_type"] == "annex_table")
    slide["takeaway"] = {"text": "not allowed"}
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_period_fallback_keeps_strip_and_table(tmp_path: Path):
    """Non-strict overflow on period table keeps metric strip + full table."""
    raw = _raw()
    slide = next(s for s in raw["slides"] if s["layout_type"] == "period_comparison")
    slide["payload"]["table"]["typography"] = {
        "mode": "fixed",
        "table_font_size": 24,
    }
    for row in slide["payload"]["table"]["rows"]:
        row["label"] = "X" * 200
        for cell in row["cells"].values():
            if cell.get("type") == "number":
                cell["value"] = "9" * 40 + ".9"
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["surface_id"] == "period-main")
    assert 'data-metric-strip="period-strip"' in html
    assert '<table class="data-table table-overflow"' in html
    assert "EPS" in html and "XXX" in html and "$" in html
    assert plan["fallback"] == "ordinary_data_table"
    assert any(
        event["code"] == "plan.unresolved_overflow"
        and event["surface_id"] == "period-main"
        for event in meta["events"]
    )
    assert result["status"] == "degraded"


def test_comparison_cards_nonstrict_table_fallback(tmp_path: Path):
    raw = _raw()
    slide = next(s for s in raw["slides"] if s["layout_type"] == "comparison_cards")
    for row in slide["payload"]["table"]["rows"]:
        row["label"] = "Peer " + ("Name " * 40)
        for cell in row["cells"].values():
            if cell.get("type") == "text":
                cell["text"] = "Fact " * 80
            elif cell.get("type") == "number":
                cell["value"] = "123456789.1"
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    plan = next(p for p in meta["plans"] if p["surface_id"] == "cards-main")
    assert '<table class="data-table table-overflow"' in html
    assert "Peer Name" in html and "123" in html
    assert 'data-table-surface="cards-main"' in html
    assert 'class="comparison-cards' not in html
    assert plan["fallback"] == "ordinary_data_table"
    assert any(
        event["code"] == "plan.unresolved_overflow"
        and event["surface_id"] == "cards-main"
        for event in meta["events"]
    )
    assert result["status"] == "degraded"


def test_nonstrict_repairs_traverse_new_compositions():
    raw = _raw()
    new_layouts = {
        "annex_table",
        "grouped_annex_table",
        "period_comparison",
        "comparison_cards",
    }
    for slide in raw["slides"]:
        if slide["layout_type"] not in new_layouts:
            continue
        slide["payload"]["unexpected"] = True
        slide["disclosure"] = {"sections": ["invalid"]}
        payload = slide["payload"]
        tables = (
            [peer["table"] for peer in payload["tables"]]
            if slide["layout_type"] == "grouped_annex_table"
            else [payload["table"]]
        )
        for table in tables:
            table["typography"] = {"body_font_size": 99}
        if "metric_strip" in payload:
            payload["metric_strip"]["typography"] = {"table_font_size": 99}

    result = validate_handoff(raw, strict=False)

    assert result.repaired is True
    repaired = {slide.layout_type: slide for slide in result.deck.slides}
    for layout in new_layouts:
        slide = repaired[layout]
        assert slide.disclosure is None
        tables = (
            [peer.table for peer in slide.payload.tables]
            if layout == "grouped_annex_table"
            else [slide.payload.table]
        )
        assert all(table.typography is None for table in tables)
    assert repaired["period_comparison"].payload.metric_strip.typography is None
    assert {event.code for event in result.events} >= {
        "repair.field_dropped",
        "repair.item_dropped",
        "repair.policy_defaulted",
    }


def test_mutation_drop_variance_column_fails():
    raw = _raw()
    slide = next(s for s in raw["slides"] if s["layout_type"] == "period_comparison")
    cols = slide["payload"]["table"]["columns"]
    slide["payload"]["table"]["columns"] = [c for c in cols if c["column_id"] != "variance"]
    for row in slide["payload"]["table"]["rows"]:
        row["cells"].pop("variance", None)
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_nonstrict_table_repair_cells_and_groups():
    raw = _raw()
    slide = next(s for s in raw["slides"] if s["layout_type"] == "annex_table")
    table = slide["payload"]["table"]
    table["rows"][0]["cells"]["q1"] = {"type": "number"}
    table["rows"][0]["cells"]["q2"] = None
    table["rows"][0]["cells"]["not_a_column"] = {"type": "missing"}
    del table["rows"][1]["cells"]["q3"]
    table["column_groups"][0]["column_ids"].append("not_a_column")

    with pytest.raises(RendererValidationError):
        validate_handoff(deepcopy(raw), strict=True)
    result = validate_handoff(raw, strict=False)

    repaired = next(
        s for s in result.deck.slides if s.layout_type == "annex_table"
    ).payload.table
    assert repaired.column_groups is None
    assert [c.column_id for c in repaired.columns] == ["q1", "q2", "q3"]
    for row in repaired.rows:
        assert set(row.cells) == {"q1", "q2", "q3"}
    assert repaired.rows[0].cells["q1"].type == "missing"
    assert repaired.rows[0].cells["q2"].type == "missing"
    assert repaired.rows[0].cells["q3"].type != "missing"
    assert repaired.rows[1].cells["q3"].type == "missing"
    assert {e.code for e in result.events} >= {
        "repair.value_to_missing",
        "repair.field_dropped",
        "repair.structure_flattened",
    }


def test_nonstrict_table_repair_traverses_grouped_peers():
    raw = _raw()
    slide = next(
        s for s in raw["slides"] if s["layout_type"] == "grouped_annex_table"
    )
    slide["payload"]["tables"][1]["table"]["rows"][0]["cells"]["a"] = {
        "type": "text"
    }
    result = validate_handoff(raw, strict=False)
    peer = next(
        s for s in result.deck.slides if s.layout_type == "grouped_annex_table"
    ).payload.tables[1].table
    assert peer.rows[0].cells["a"].type == "missing"


def test_comparison_cards_a11y_and_print_contract(tmp_path: Path):
    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    container_start = html.index('class="comparison-cards cols-3')
    container_tag = html[container_start : html.index(">", container_start)]
    assert 'aria-hidden="true"' in container_tag
    assert "sr-only-table" in html
    print_block = html[html.index("@media print{") : html.index("</style>")]
    assert ".comparison-cards{display:none}" in print_block
    assert ".sr-only{position:static" in print_block
    assert "clip:auto" in print_block


def _heading_wrapping_lines(lines: int) -> str:
    from impact_slides.renderer_v3.plan import (
        CONTENT_W,
        GROUPED_ANNEX_GAP,
        GROUPED_ANNEX_HEADING_PX,
        _wrap_lines,
    )

    peer_w = (CONTENT_W - GROUPED_ANNEX_GAP) // 2
    heading = "Quarterly performance overview of the consumer business segment"
    while len(_wrap_lines([(heading, True)], GROUPED_ANNEX_HEADING_PX, peer_w)[0]) < lines:
        heading += " review"
    return heading


def test_grouped_annex_short_heading_only_after_fit_failure(tmp_path: Path):
    two_lines = _heading_wrapping_lines(2)
    raw = _raw()
    slide = next(
        s for s in raw["slides"] if s["layout_type"] == "grouped_annex_table"
    )
    slide["payload"]["tables"][0]["heading"] = two_lines
    slide["payload"]["tables"][0]["short_heading"] = "US"
    result = validate_handoff(deepcopy(raw), strict=True)
    plan = plan_deck(result.deck, strict=True)
    peer = next(s for s in plan.surfaces if s.surface_id == "peer-us")
    assert peer.table_paint["display_heading"] == two_lines

    three_lines = _heading_wrapping_lines(3)
    slide["payload"]["tables"][0]["heading"] = three_lines
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    peer_start = html.index('class="grouped-annex-peer"')
    heading_tag = html[peer_start : html.index("</h2>", peer_start)]
    assert f'title="{three_lines}"' in heading_tag
    assert f'aria-label="{three_lines}"' in heading_tag
    assert heading_tag.rsplit(">", 1)[1].startswith("US")


def test_sync_floor_never_below_member_floors():
    raw = _raw()
    annex = next(s for s in raw["slides"] if s["layout_type"] == "annex_table")
    cards = next(s for s in raw["slides"] if s["layout_type"] == "comparison_cards")
    annex["payload"]["table"]["typography"] = {
        "mode": "adaptive",
        "sync_group": "shared-x",
    }
    cards["payload"]["table"]["typography"] = {
        "mode": "adaptive",
        "sync_group": "shared-x",
    }
    table = annex["payload"]["table"]
    for i in range(6):
        table["columns"].append(
            {"column_id": f"x{i}", "label": f"Extended dimension {i}"}
        )
        for row in table["rows"]:
            row["cells"][f"x{i}"] = {
                "type": "number",
                "value": "1234567890123.45",
                "format_id": "usd_1",
            }
    for row in table["rows"]:
        for cell in row["cells"].values():
            if cell.get("type") == "number":
                cell["value"] = "1234567890123.45"

    result = validate_handoff(raw, strict=True)
    plan = plan_deck(result.deck, strict=False)
    sizes = {
        s.surface_id: s.role_sizes["table"]
        for s in plan.surfaces
        if s.surface_id in {"annex-main", "cards-main"}
    }
    assert sizes["cards-main"] >= 20
    assert sizes["annex-main"] == sizes["cards-main"]


def test_grouped_annex_single_peer_full_width(tmp_path: Path):
    raw = _raw()
    slide = next(s for s in raw["slides"] if s["layout_type"] == "grouped_annex_table")
    slide["payload"]["tables"] = slide["payload"]["tables"][:1]
    handoff = tmp_path / "handoff.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert "US Consumer" in html
    assert 'class="grouped-annex-divider"' not in html
    assert 'data-table-surface="peer-us"' in html
