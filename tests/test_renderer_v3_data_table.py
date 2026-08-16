"""Renderer v3 data_table + semantic values (#179).

Seams under test:
- tagged SemanticValue + deck number_formats registry (D143/D144/D213/D214/D293)
- decimal-safe formatter (D70/D77/D78/D103)
- rectangular identity-safe table model (D141/D255/D256)
- data_table composition paint + a11y associations (D183/D257/D104/D105)
- one common fitted size + strict/non-strict overflow (D24/D25/D44)
"""
from __future__ import annotations

import json
import math
from copy import deepcopy
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.format import (
    MISSING_ACCESSIBLE,
    MISSING_VISIBLE,
    format_semantic_value,
)
from impact_slides.renderer_v3.models import (
    DataTableSlide,
    MissingValue,
    NumberFormat,
    NumberValue,
    RangeValue,
    TextValue,
)
from impact_slides.renderer_v3.plan import plan_deck
from impact_slides.renderer_v3.schema_export import check_schema

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/renderer_v3/minimal_data_table.json"
NARRATIVE = ROOT / "tests/fixtures/renderer_v3/minimal_cover_narrative_cover.json"


def _table_raw() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Formatter (D77/D78/D103/D293)
# ---------------------------------------------------------------------------


def test_format_usd_parentheses_and_grouping():
    fmt = {"usd": NumberFormat(unit="usd", value_decimals=1, negative_style="parentheses")}
    fv = format_semantic_value(NumberValue(value="-1234.56", format_id="usd"), fmt)
    assert fv.visible == "($1,234.6)"
    assert "negative" in fv.accessible
    assert "US dollars" in fv.accessible
    assert fv.role == "number"
    assert fv.align == "right"


def test_format_usd_minus_before_prefix_unit():
    """Minus-style USD places the sign before the unit (D293): -$1,234.6."""
    fmt = {"usd": NumberFormat(unit="usd", value_decimals=1, negative_style="minus")}
    fv = format_semantic_value(NumberValue(value="-1234.56", format_id="usd"), fmt)
    assert fv.visible == "-$1,234.6"
    assert not fv.visible.startswith("$")
    assert "negative" in fv.accessible
    assert "US dollars" in fv.accessible
    z = format_semantic_value(NumberValue(value="-0.04", format_id="usd"), fmt)
    assert z.visible == "$0.0"  # rounded zero stays unsigned
    assert "negative" not in z.accessible


def test_format_percent_minus_and_zero_unsigned():
    fmt = {"pct": NumberFormat(unit="percent", value_decimals=1, negative_style="minus")}
    assert format_semantic_value(NumberValue(value="-2.5", format_id="pct"), fmt).visible == "-2.5%"
    z = format_semantic_value(NumberValue(value="0", format_id="pct"), fmt)
    assert z.visible == "0.0%"
    assert "negative" not in z.accessible


def test_format_missing_is_em_dash_not_zero():
    fv = format_semantic_value(MissingValue(), {})
    assert fv.visible == MISSING_VISIBLE
    assert fv.accessible == MISSING_ACCESSIBLE
    assert fv.visible != "0"
    assert fv.visible != ""


def test_format_text_byte_for_byte():
    fv = format_semantic_value(TextValue(text="N/A source"), {})
    assert fv.visible == "N/A source"
    assert fv.align == "left"


def test_format_range_and_scale():
    fmt = {
        "pct": NumberFormat(unit="percent", value_decimals=1, negative_style="minus"),
        "m": NumberFormat(
            unit="usd",
            value_decimals=1,
            negative_style="minus",
            value_scale="0.000001",
            scale_label="USD millions",
        ),
    }
    r = format_semantic_value(
        RangeValue(lower="1.0", upper="2.5", format_id="pct"), fmt
    )
    assert r.visible == "1.0%\u20132.5%"
    assert "to" in r.accessible
    s = format_semantic_value(NumberValue(value="1500000", format_id="m"), fmt)
    assert s.visible == "$1.5"


def test_half_away_from_zero_rounding():
    fmt = {"u": NumberFormat(value_decimals=0, negative_style="minus")}
    assert format_semantic_value(NumberValue(value="1.5", format_id="u"), fmt).visible == "2"
    assert format_semantic_value(NumberValue(value="-1.5", format_id="u"), fmt).visible == "-2"


# ---------------------------------------------------------------------------
# Validation / model
# ---------------------------------------------------------------------------


def test_data_table_deck_validates():
    result = validate_handoff(_table_raw(), strict=True)
    assert result.ok
    slide = result.deck.slides[1]
    assert isinstance(slide, DataTableSlide)
    assert slide.payload.table.surface_id == "seg-perf"
    assert len(slide.payload.table.rows) == 3
    assert "usd_1" in result.deck.number_formats


def test_narrative_fixture_still_validates():
    raw = json.loads(NARRATIVE.read_text(encoding="utf-8"))
    assert validate_handoff(raw, strict=True).ok


def test_strict_rejects_missing_cell():
    raw = _table_raw()
    del raw["slides"][1]["payload"]["table"]["rows"][0]["cells"]["note"]
    with pytest.raises(RendererValidationError) as ei:
        validate_handoff(raw, strict=True)
    assert ei.value.events


def test_strict_rejects_extra_cell():
    raw = _table_raw()
    raw["slides"][1]["payload"]["table"]["rows"][0]["cells"]["ghost"] = {
        "type": "text",
        "text": "x",
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_unresolved_format():
    raw = _table_raw()
    raw["slides"][1]["payload"]["table"]["rows"][0]["cells"]["rev"]["format_id"] = "nope"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_unused_format():
    raw = _table_raw()
    raw["number_formats"]["orphan"] = {
        "value_decimals": 0,
        "negative_style": "minus",
    }
    with pytest.raises(RendererValidationError) as ei:
        validate_handoff(raw, strict=True)
    joined = " ".join(
        (e.expected.contract if e.expected else "") + e.code for e in ei.value.events
    )
    assert "unused" in joined and "validation.reference" in joined


def test_strict_rejects_overlapping_groups():
    raw = _table_raw()
    raw["slides"][1]["payload"]["table"]["column_groups"] = [
        {
            "group_id": "a",
            "label": "A",
            "column_ids": ["rev", "growth"],
        },
        {
            "group_id": "b",
            "label": "B",
            "column_ids": ["growth", "note"],
        },
    ]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_primitive_cell():
    raw = _table_raw()
    raw["slides"][1]["payload"]["table"]["rows"][0]["cells"]["rev"] = 12.5
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_schema_artifact_current():
    check_schema(ROOT)


# ---------------------------------------------------------------------------
# Plan + paint
# ---------------------------------------------------------------------------


def test_plan_freezes_one_table_size(tmp_path: Path):
    deck = validate_handoff(_table_raw(), strict=True).deck
    plan = plan_deck(deck, strict=True)
    table_plans = [s for s in plan.surfaces if s.role == "data_table"]
    assert len(table_plans) == 1
    sp = table_plans[0]
    assert sp.surface_id == "seg-perf"
    assert "table" in sp.role_sizes
    assert TABLE_FLOOR_OK(sp.role_sizes["table"])
    assert not sp._overflow
    # All rows/cols preserved in fit spec.
    assert sp._table_spec is not None
    assert sp._table_spec["n_rows"] == 3
    assert sp._table_spec["n_cols"] == 3
    assert len(sp._table_spec["cells_vis"]) == 3


def TABLE_FLOOR_OK(px: int) -> bool:
    return 20 <= px <= 24


def test_render_data_table_html_identity_and_a11y(tmp_path: Path):
    result = render_deck(FIXTURE, tmp_path, strict=True)
    assert result["ok"] is True
    html = (tmp_path / "presentation.html").read_text(encoding="utf-8")
    # Navy header band class + transparent body (theme tokens, not raw hex).
    assert "band-table-header" in html or "data-table" in html
    assert "data-table" in html
    assert 'scope="col"' in html
    assert 'scope="row"' in html
    assert "headers=" in html
    # Values present — no row/col loss.
    assert "$1,234.6" in html
    assert "($89.1)" in html
    assert "2.5%" in html
    assert "0.0%" in html
    assert MISSING_VISIBLE in html
    assert MISSING_ACCESSIBLE in html
    assert "Core" in html
    assert "Watch" in html
    assert "$1.5" in html  # scaled
    assert "USD millions" in html  # scale disclosure once
    assert "1.0%" in html and "2.5%" in html  # range
    # Tabular numerals + alignment CSS target cells, not the table element.
    assert "td.num" in html or "td.num,table.data-table th.num" in html
    assert "td.align-right" in html or "th.align-right,table.data-table td.align-right" in html
    assert 'class="align-left' in html  # text column body
    assert "align-left" in html and "Note" in html
    # No raw theme hex in painter output beyond generated CSS vars.
    body = html.split("<main", 1)[1] if "<main" in html else html
    assert "#00175A" not in body
    # Plan attrs on table surface.
    assert 'data-surface-id="seg-perf"' in html
    assert "data-plan-sizes=" in html
    # Non-strict overflow marker class present in CSS.
    assert "table-overflow" in html


def test_render_minus_usd_prefix_and_scale_at_table_size(tmp_path: Path):
    raw = _table_raw()
    raw["number_formats"]["usd_1"]["negative_style"] = "minus"
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    result = render_deck(path, tmp_path / "out", strict=True)
    assert result["ok"] is True
    html = (tmp_path / "out" / "presentation.html").read_text(encoding="utf-8")
    assert "-$89.1" in html
    assert "$-89.1" not in html
    assert 'aria-label="negative 89.1 US dollars"' in html
    # Scale disclosure inherits the resolved table font size (inline style).
    assert "USD millions" in html
    deck = validate_handoff(raw, strict=True).deck
    px = next(
        s.role_sizes["table"]
        for s in plan_deck(deck, strict=True).surfaces
        if s.role == "data_table"
    )
    assert f'class="table-scale" style="font-size:{px}px"' in html


def test_render_preserves_row_column_count(tmp_path: Path):
    render_deck(FIXTURE, tmp_path, strict=True)
    html = (tmp_path / "presentation.html").read_text(encoding="utf-8")
    # 3 body rows
    assert html.count('scope="row"') == 3
    # stub + 3 leaf headers at minimum
    assert html.count('scope="col"') + html.count('scope="colgroup"') >= 4


def _force_height_overflow(raw: dict, n_rows: int = 80) -> dict:
    """Clone first data row many times so the table cannot fit at 20px floor."""
    table = raw["slides"][1]["payload"]["table"]
    # Drop groups/scale complexity; keep one simple format so extras stay referenced.
    table.pop("column_groups", None)
    proto = deepcopy(table["rows"][0])
    # Use only usd_1 + pct_1 + text so dropping scaled formats is fine.
    raw["number_formats"] = {
        "usd_1": raw["number_formats"]["usd_1"],
        "pct_1": raw["number_formats"]["pct_1"],
    }
    rows = []
    for i in range(n_rows):
        row = deepcopy(proto)
        row["row_id"] = f"r{i:03d}"
        row["label"] = f"Row label {i} with enough words to wrap twice maybe"
        row["cells"] = {
            "rev": {"type": "number", "value": "1234.56", "format_id": "usd_1"},
            "growth": {"type": "number", "value": "2.5", "format_id": "pct_1"},
            "note": {"type": "text", "text": "Core"},
        }
        rows.append(row)
    table["rows"] = rows
    return raw


def test_strict_overflow_fails(tmp_path: Path):
    raw = _force_height_overflow(_table_raw(), n_rows=80)
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(RendererValidationError) as ei:
        render_deck(path, tmp_path / "out", strict=True)
    assert any(e.code == "plan.unresolved_overflow" for e in ei.value.events)


def test_nonstrict_overflow_paints_complete(tmp_path: Path):
    raw = _force_height_overflow(_table_raw(), n_rows=80)
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    result = render_deck(path, tmp_path / "out", strict=False)
    assert result["ok"] is False
    html = (tmp_path / "out" / "presentation.html").read_text(encoding="utf-8")
    # Every authored row still present — no silent deletion (D25).
    assert html.count('scope="row"') == 80
    assert "$1,234.6" in html
    assert "2.5%" in html
    assert "plan.unresolved_overflow" in result["errors"]


def test_mutation_drop_row_keeps_remaining_identity():
    raw = _table_raw()
    # Drop middle row so every format remains referenced by survivors.
    raw["slides"][1]["payload"]["table"]["rows"].pop(1)
    deck = validate_handoff(raw, strict=True).deck
    assert len(deck.slides[1].payload.table.rows) == 2
    ids = [r.row_id for r in deck.slides[1].payload.table.rows]
    assert ids == ["cards", "nna"]


def test_mutation_value_meaning_unchanged_by_fit(tmp_path: Path):
    """Fitting must not change numeric meaning (D70)."""
    deck = validate_handoff(_table_raw(), strict=True).deck
    plan = plan_deck(deck, strict=True)
    sp = next(s for s in plan.surfaces if s.role == "data_table")
    # Spot-check formatted values equal direct formatter output.
    fmt = deck.number_formats
    expected = format_semantic_value(
        deck.slides[1].payload.table.rows[0].cells["rev"], fmt
    ).visible
    assert sp._table_spec["cells_vis"][0][0] == expected


def test_byte_identical_rerun(tmp_path: Path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    render_deck(FIXTURE, a, strict=True)
    render_deck(FIXTURE, b, strict=True)
    for name in ("presentation.html", "slide_notes.md", "evidence_manifest.json"):
        assert (a / name).read_bytes() == (b / name).read_bytes()


def test_table_slack_is_shared_not_dumped_into_stub():
    """Leftover box width must not all land in the stub column (#246)."""
    from impact_slides.renderer_v3.plan import (
        CONTENT_W,
        TABLE_CELL_PAD_X,
        _table_fit_detail,
        _text_width,
    )

    px = 20
    stub = "Metric"
    headers = ["Q1'26", "Q1'25", "YoY"]
    values = ["$17.9B", "$16.6B", "8%"]
    spec = {
        "n_cols": 3,
        "n_rows": 1,
        "header_full": [stub] + headers,
        "header_short": [stub] + headers,
        "row_labels_full": ["Revenue"],
        "row_labels_short": ["Revenue"],
        "cells_vis": [list(values)],
        "cells_acc": [list(values)],
        "cells_role": [["metric"] * 3],
        "cells_align": [["right"] * 3],
        "col_ids": ["cur", "prior", "yoy"],
        "groups": None,
        "scale_labels": [],
        "col_widths": [],
        "display_headers": None,
        "display_row_labels": None,
        "display_groups": None,
        "ellipsized": False,
        "short_label_used": False,
        "all_texts": [],
    }
    ok, codes, _h = _table_fit_detail(spec, px, CONTENT_W, 10**9)
    assert ok, codes
    widths = spec["col_widths"]
    assert len(widths) == 4
    assert sum(widths) == CONTENT_W
    assert widths[0] / CONTENT_W <= 0.45
    value_mins = [_text_width(v, px) + TABLE_CELL_PAD_X for v in values]
    for c, vmin in enumerate(value_mins):
        assert widths[c + 1] >= math.ceil(vmin)
        assert widths[c + 1] > math.ceil(vmin)
    assert spec["ellipsized"] is False
    assert "plan.label_ellipsized" not in codes


def test_ellipsis_pack_keeps_value_ceil_widths_when_float_mins_fit():
    """Value-feasible tables must not false-overflow after integer packing."""
    from impact_slides.renderer_v3.plan import CONTENT_W, TABLE_CELL_PAD_X, _table_fit_detail, _text_width

    px = 20
    n = 18
    cell = "$100,000"
    # Float value mins fit CONTENT_W; ceil leftover is smaller than total_cols.
    assert sum(_text_width(cell, px) + TABLE_CELL_PAD_X for _ in range(n)) <= CONTENT_W
    spec = {
        "n_cols": n,
        "n_rows": 1,
        "header_full": ["S"] + [f"C{i}" for i in range(n)],
        "header_short": ["S"] + [f"C{i}" for i in range(n)],
        "row_labels_full": ["R"],
        "row_labels_short": ["R"],
        "cells_vis": [[cell] * n],
        "cells_acc": [[cell] * n],
        "cells_role": [["metric"] * n],
        "cells_align": [["right"] * n],
        "col_ids": [f"c{i}" for i in range(n)],
        "groups": None,
        "scale_labels": [],
        "col_widths": [],
        "display_headers": None,
        "display_row_labels": None,
        "display_groups": None,
        "ellipsized": False,
        "short_label_used": False,
        "all_texts": [],
    }
    ok, codes, _h = _table_fit_detail(spec, px, CONTENT_W, 10**9)
    assert ok, codes
    assert len(spec["col_widths"]) == n + 1
    assert sum(spec["col_widths"]) == CONTENT_W
    for c in range(n):
        assert _text_width(cell, px) <= spec["col_widths"][c + 1] - TABLE_CELL_PAD_X


def test_label_line_budget_falls_through_to_short():
    """Full labels that wrap past 2 lines must try short/ellipsis before overflow."""
    from impact_slides.renderer_v3.plan import CONTENT_W, _table_fit_detail

    spec = {
        "n_cols": 3,
        "n_rows": 2,
        "header_full": [
            "Segment",
            "RevenueGrowthVersusPriorYearPeriodWithoutBreaksXXXXXX",
            "NetIncomeMarginPercentageWithoutBreaksXXXXXXXXXXXX",
            "OperatingExpenseRatioTrendWithoutBreaksXXXXXXXXXXXX",
        ],
        "header_short": ["Seg", "Rev", "NIM", "Opex"],
        "row_labels_full": ["Card Member Loans", "Auto Finance Book"],
        "row_labels_short": ["Cards", "Auto"],
        "cells_vis": [["$1,234.6", "2.5%", "12.0%"], ["$980.1", "1.8%", "11.2%"]],
        "cells_acc": [["$1,234.6", "2.5%", "12.0%"], ["$980.1", "1.8%", "11.2%"]],
        "cells_role": [["metric"] * 3] * 2,
        "cells_align": [["right"] * 3] * 2,
        "col_ids": ["a", "b", "c"],
        "groups": None,
        "scale_labels": [],
        "col_widths": [],
        "display_headers": None,
        "display_row_labels": None,
        "display_groups": None,
        "ellipsized": False,
        "short_label_used": False,
        "all_texts": [],
    }
    for px in (20, 22, 24):
        s = dict(spec)
        s["cells_vis"] = [list(r) for r in spec["cells_vis"]]
        ok, codes, _h = _table_fit_detail(s, px, CONTENT_W, 10**9)
        assert ok, (px, codes, s.get("display_headers"))
        assert s["short_label_used"] is True
        assert s["display_headers"] == ["Seg", "Rev", "NIM", "Opex"]
        assert "plan.short_label_used" in codes


def test_scale_line_reserves_full_resolved_table_size():
    """Scale disclosure height must match painted table px, not px-4 (D22/D44/D257)."""
    from impact_slides.renderer_v3.plan import (
        BLOCK_MARGIN_Y,
        CONTENT_W,
        _line_box,
        _table_fit_detail,
    )

    def _spec(scale_labels: list[str]) -> dict:
        return {
            "n_cols": 1,
            "n_rows": 1,
            "header_full": ["S", "A"],
            "header_short": ["S", "A"],
            "row_labels_full": ["R"],
            "row_labels_short": ["R"],
            "cells_vis": [["1"]],
            "cells_acc": [["1"]],
            "cells_role": [["metric"]],
            "cells_align": [["right"]],
            "col_ids": ["a"],
            "groups": None,
            "scale_labels": list(scale_labels),
            "col_widths": [],
            "display_headers": None,
            "display_row_labels": None,
            "display_groups": None,
            "ellipsized": False,
            "short_label_used": False,
            "all_texts": [],
        }

    for px in (20, 22, 24):
        full_scale_h = _line_box(px) + BLOCK_MARGIN_Y
        old_scale_h = _line_box(max(12, px - 4)) + BLOCK_MARGIN_Y
        assert full_scale_h > old_scale_h

        with_scale = _spec(["$ in millions"])
        ok, _, h_with = _table_fit_detail(
            with_scale, px, CONTENT_W, 10**9, allow_short=False, allow_ellipsis=False
        )
        assert ok
        bare = _spec([])
        ok_bare, _, h_bare = _table_fit_detail(
            bare, px, CONTENT_W, 10**9, allow_short=False, allow_ellipsis=False
        )
        assert ok_bare
        assert h_with - h_bare == full_scale_h

        # Tight box: full scale overflows; shrunken old reserve would still "fit".
        tight = h_with - 1
        assert h_bare + old_scale_h <= tight < h_with
        fail_spec = _spec(["$ in millions"])
        ok_fail, _, _ = _table_fit_detail(
            fail_spec, px, CONTENT_W, tight, allow_short=False, allow_ellipsis=False
        )
        assert not ok_fail
        pass_spec = _spec(["$ in millions"])
        ok_pass, _, _ = _table_fit_detail(
            pass_spec, px, CONTENT_W, h_with, allow_short=False, allow_ellipsis=False
        )
        assert ok_pass


def test_stub_labels_use_emphasis_metrics():
    from impact_slides.renderer_v3.plan import (
        TABLE_CELL_PAD_X,
        _table_fit_detail,
        _text_width,
    )

    label = "MMMMMMMM"
    cell = "1"
    spec = {
        "n_cols": 1,
        "n_rows": 1,
        "header_full": ["S", "A"],
        "header_short": ["S", "A"],
        "row_labels_full": [label],
        "row_labels_short": [label],
        "cells_vis": [[cell]],
        "cells_acc": [[cell]],
        "cells_role": [["metric"]],
        "cells_align": [["right"]],
        "col_ids": ["a"],
        "groups": None,
        "scale_labels": [],
        "col_widths": [],
        "display_headers": None,
        "display_row_labels": None,
        "display_groups": None,
        "ellipsized": False,
        "short_label_used": False,
        "all_texts": [],
    }
    regular_only_width = math.ceil(
        _text_width(label, 20) + TABLE_CELL_PAD_X
    ) + math.ceil(_text_width(cell, 20) + TABLE_CELL_PAD_X)
    assert _text_width(label, 20, strong=True) + TABLE_CELL_PAD_X > math.ceil(
        _text_width(label, 20) + TABLE_CELL_PAD_X
    )

    ok, _, _ = _table_fit_detail(
        spec,
        20,
        regular_only_width,
        10**9,
        allow_short=False,
        allow_ellipsis=False,
    )
    assert not ok

    wrapped = dict(spec)
    wrapped["row_labels_full"] = ["Premium Card Members"]
    wrapped["row_labels_short"] = ["Premium Card Members"]
    ok, codes, _ = _table_fit_detail(wrapped, 20, 174, 10**9)
    assert ok
    assert wrapped["display_row_labels"] == ["Premium Ca…"]
    assert "plan.label_ellipsized" in codes


def test_table_sync_group_uses_grid_fit_not_prose():
    """Synced tables must share a size every grid can fit (D69/D70)."""
    raw = _table_raw()
    # Compact table that can grow independently.
    raw["slides"][1]["payload"]["table"]["typography"] = {
        "mode": "adaptive",
        "sync_group": "tables",
    }
    # Wide sibling: many fat numeric columns force a lower independent size.
    wide_cols = [
        {"column_id": f"c{i}", "label": f"Metric {i}", "short_label": f"M{i}"}
        for i in range(12)
    ]
    wide_cells = {
        f"c{i}": {"type": "number", "value": "1234567.8", "format_id": "usd_1"}
        for i in range(12)
    }
    wide_slide = {
        "slide_number": 3,
        "layout_type": "data_table",
        "section_id": "overview",
        "title": "Wide metrics",
        "payload": {
            "table": {
                "surface_id": "wide-perf",
                "typography": {"mode": "adaptive", "sync_group": "tables"},
                "stub_header": {"label": "Segment", "short_label": "Seg"},
                "columns": wide_cols,
                "rows": [
                    {
                        "row_id": "r0",
                        "label": "Card Member",
                        "short_label": "Cards",
                        "cells": wide_cells,
                    }
                ],
            }
        },
        "evidence_ids": ["src-board-pack"],
        "source_footer": ["src-board-pack"],
    }
    # Keep closing cover after the pair.
    raw["slides"].insert(2, wide_slide)
    raw["slides"][3]["slide_number"] = 4

    deck = validate_handoff(raw, strict=True).deck
    from impact_slides.renderer_v3.plan import _table_fit_detail

    # Independent measure: compact fits 24; 12 fat cols fail grid at 24, fit at 20+.
    compact_only = validate_handoff(_table_raw(), strict=True).deck
    compact_plan = plan_deck(compact_only, strict=True)
    compact_sp = next(s for s in compact_plan.surfaces if s.role == "data_table")
    compact_indep = compact_sp.role_sizes["table"]
    assert compact_indep == 24

    wide_only_raw = _table_raw()
    wide_only_raw["number_formats"] = {
        k: v
        for k, v in wide_only_raw["number_formats"].items()
        if k == "usd_1"
    }
    wide_only_raw["slides"][1] = {
        **wide_slide,
        "slide_number": 2,
        "payload": {
            "table": {
                **wide_slide["payload"]["table"],
                "typography": {"mode": "adaptive"},
            }
        },
    }
    wide_only = validate_handoff(wide_only_raw, strict=True).deck
    wide_plan = plan_deck(wide_only, strict=True)
    wide_sp = next(s for s in wide_plan.surfaces if s.role == "data_table")
    wide_indep = wide_sp.role_sizes["table"]
    assert wide_indep < compact_indep
    assert not _table_fit_detail(
        dict(wide_sp.table_paint), compact_indep, wide_sp._box_w, wide_sp._box_h
    )[0]
    assert _table_fit_detail(
        dict(wide_sp.table_paint), wide_indep, wide_sp._box_w, wide_sp._box_h
    )[0]

    plan = plan_deck(deck, strict=True)
    tables = [s for s in plan.surfaces if s.role == "data_table"]
    assert len(tables) == 2
    sizes = {s.surface_id: s.role_sizes["table"] for s in tables}
    assert sizes["seg-perf"] == sizes["wide-perf"] == wide_indep
    for sp in tables:
        assert not sp._overflow
        assert sp.table_paint is not None
        assert sp.table_paint["col_widths"]
        # Frozen paint widths must still hold every value at the synced size.
        px = sp.role_sizes["table"]
        ok, _, _ = _table_fit_detail(
            dict(sp.table_paint), px, sp._box_w, sp._box_h
        )
        assert ok
        assert "plan.synchronized" in sp.adaptation_codes
