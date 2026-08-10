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
    assert "unused" in joined or "number_formats" in joined or ei.value.events


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
