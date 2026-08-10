"""Renderer v3 native semantic heatmaps (#187).

Seams under test:
- typed heatmap visual + shared format + generated/fixed scale (D163/D246/D308)
- one visible native HTML table (no canvas/SVG/duplicate) (D106/D247/D248)
- deterministic light→primary-blue fills + contrast-safe ink + scale key
- missing neutral em dash; uncolored complete-table non-strict fallback
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.charts import freeze_heatmap, paint_heatmap_html
from impact_slides.renderer_v3.format import MISSING_ACCESSIBLE, MISSING_VISIBLE
from impact_slides.renderer_v3.models import HeatmapVisual, SingleChartSlide
from impact_slides.renderer_v3.plan import plan_deck
from impact_slides.renderer_v3.schema_export import check_schema

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/renderer_v3/minimal_heatmap.json"
LINE = ROOT / "tests/fixtures/renderer_v3/minimal_line_chart.json"


def _raw() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Validation / model
# ---------------------------------------------------------------------------


def test_heatmap_deck_validates():
    result = validate_handoff(_raw(), strict=True)
    assert result.ok
    slide = result.deck.slides[1]
    assert isinstance(slide, SingleChartSlide)
    chart = slide.payload.primary_visual
    assert isinstance(chart, HeatmapVisual)
    assert chart.surface_id == "region-heat"
    assert chart.chart_type == "heatmap"
    assert chart.scale.mode == "generated"
    assert len(chart.table_data.rows) == 3
    assert len(chart.table_data.columns) == 3


def test_line_fixture_still_validates():
    raw = json.loads(LINE.read_text(encoding="utf-8"))
    assert validate_handoff(raw, strict=True).ok


def test_strict_rejects_text_cell():
    raw = _raw()
    cells = raw["slides"][1]["payload"]["primary_visual"]["table_data"]["rows"][0]["cells"]
    cells["q1"] = {"type": "text", "text": "n/a"}
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_mixed_formats():
    raw = _raw()
    raw["number_formats"]["usd_0"] = {
        "unit": "usd",
        "value_decimals": 0,
        "negative_style": "minus",
    }
    cells = raw["slides"][1]["payload"]["primary_visual"]["table_data"]["rows"][0]["cells"]
    cells["q1"]["format_id"] = "usd_0"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_all_missing():
    raw = _raw()
    for row in raw["slides"][1]["payload"]["primary_visual"]["table_data"]["rows"]:
        row["cells"] = {cid: {"type": "missing"} for cid in row["cells"]}
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_fixed_scale_out_of_range():
    raw = _raw()
    raw["slides"][1]["payload"]["primary_visual"]["scale"] = {
        "mode": "fixed",
        "min": "0.0",
        "max": "10.0",
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_axis_fields_on_heatmap():
    raw = _raw()
    raw["slides"][1]["payload"]["primary_visual"]["chart_data"] = {
        "categories": [{"category_id": "a", "label": "A"}, {"category_id": "b", "label": "B"}],
        "series": [{"series_id": "s", "name": "S", "values": ["1.0", "2.0"]}],
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_thirteen_columns():
    raw = _raw()
    table = raw["slides"][1]["payload"]["primary_visual"]["table_data"]
    for i in range(4, 14):
        cid = f"c{i}"
        table["columns"].append({"column_id": cid, "label": cid.upper()})
        for row in table["rows"]:
            row["cells"][cid] = {
                "type": "number",
                "value": "1.0",
                "format_id": "pct_1",
            }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_fixed_scale_containing_values_ok():
    raw = _raw()
    raw["slides"][1]["payload"]["primary_visual"]["scale"] = {
        "mode": "fixed",
        "min": "0.0",
        "max": "30.0",
    }
    assert validate_handoff(raw, strict=True).ok


# ---------------------------------------------------------------------------
# Freeze / paint
# ---------------------------------------------------------------------------


def test_freeze_assigns_fills_and_scale_key():
    deck = validate_handoff(_raw(), strict=True).deck
    chart = deck.slides[1].payload.primary_visual
    frozen = freeze_heatmap(chart, deck.number_formats)
    assert frozen["chart_type"] == "heatmap"
    assert frozen["colored"] is True
    stops = frozen["scale"]["key_stops"]
    assert len(stops) == 3
    assert stops[0]["role"] == "min"
    assert stops[-1]["role"] == "max"
    # Missing cell stays neutral / unfilled.
    miss = frozen["cells"][1][1]
    assert miss["missing"] is True
    assert miss["visible"] == MISSING_VISIBLE
    assert miss["accessible"] == MISSING_ACCESSIBLE
    assert miss["fill"] is None
    # Max finite cell is darkest (t=1).
    us_q3 = frozen["cells"][0][2]
    assert us_q3["t"] == 1 or float(us_q3["t"]) == 1.0
    assert us_q3["fill"].startswith("#")
    assert us_q3["ink"].startswith("#")


def test_equal_values_use_midpoint_key():
    raw = _raw()
    table = raw["slides"][1]["payload"]["primary_visual"]["table_data"]
    for row in table["rows"]:
        for cid in list(row["cells"]):
            row["cells"][cid] = {
                "type": "number",
                "value": "5.0",
                "format_id": "pct_1",
            }
    deck = validate_handoff(raw, strict=True).deck
    frozen = freeze_heatmap(deck.slides[1].payload.primary_visual, deck.number_formats)
    assert frozen["scale"]["equal"] is True
    assert len(frozen["scale"]["key_stops"]) == 1
    assert frozen["scale"]["key_stops"][0]["role"] == "shared"
    assert all(float(c["t"]) == 0.5 for row in frozen["cells"] for c in row if not c["missing"])


def test_paint_is_native_table_only(tmp_path: Path):
    result = render_deck(FIXTURE, tmp_path, strict=True)
    assert result["ok"] is True
    html = (tmp_path / "presentation.html").read_text(encoding="utf-8")
    assert 'data-chart-type="heatmap"' in html
    assert 'class="data-table heatmap-table"' in html
    assert 'data-heatmap-colored="true"' in html
    assert "heatmap-scale-key" in html
    assert "chart.umd" not in html
    assert "<canvas" not in html
    # Nested D255 table surface owns the DOM table (D308).
    assert html.count('data-table-surface="region-heat-table"') == 1
    assert 'data-chart-surface="region-heat"' in html
    assert MISSING_VISIBLE in html
    assert 'aria-label="Missing"' in html or f'aria-label="{MISSING_ACCESSIBLE}"' in html
    # Values stay visible.
    assert "22.5%" in html
    assert "12.5%" in html


def test_plan_freezes_heatmap_role_and_table_size():
    deck = validate_handoff(_raw(), strict=True).deck
    plan = plan_deck(deck, strict=True)
    sp = plan.by_surface_id()["region-heat"]
    assert sp.role == "heatmap"
    assert sp.chart_paint is not None
    assert sp.chart_paint["chart_type"] == "heatmap"
    assert HEATMAP_FLOOR_OK(sp.role_sizes["table"])
    assert sp.chart_paint["colored"] is True
    assert len(sp.chart_paint["cells"]) == 3


def HEATMAP_FLOOR_OK(px: int) -> bool:
    return 18 <= px <= 24


def test_readiness_has_semantic_table_no_painters(tmp_path: Path):
    result = render_deck(FIXTURE, tmp_path, strict=True)
    assert result["ok"] is True
    meta = json.loads((tmp_path / "run_meta.json").read_text(encoding="utf-8"))
    heat = next(r for r in meta["static_readiness"] if r["slide_number"] == 2)
    assert heat["semantic_table_present"] is True
    assert heat["chart_painters"] == []


def test_non_strict_invalid_scale_paints_uncolored_table(tmp_path: Path):
    raw = _raw()
    # Fixed scale that fails containment → repaired generated + uncolored paint.
    raw["slides"][1]["payload"]["primary_visual"]["scale"] = {
        "mode": "fixed",
        "min": "0.0",
        "max": "1.0",
    }
    handoff = tmp_path / "bad-scale.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    assert result["ok"] is False  # degraded
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-heatmap-colored="false"' in html
    # No painted scale-key element (class names still appear in CSS rules).
    assert 'class="heatmap-scale-key"' not in html
    assert 'class="heatmap-scale-stop"' not in html
    # Complete table retained.
    assert "22.5%" in html
    assert "US" in html
    assert MISSING_VISIBLE in html
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    codes = {e["code"] for e in meta["events"]}
    assert "repair.domain_replaced" in codes


def test_schema_export_includes_heatmap():
    check_schema()
    from impact_slides.renderer_v3.schema_export import generate_schema

    schema = generate_schema()
    blob = json.dumps(schema)
    assert "heatmap" in blob
    assert "HeatmapVisual" in blob or "chart_type" in blob


def test_paint_heatmap_html_unit():
    deck = validate_handoff(_raw(), strict=True).deck
    frozen = freeze_heatmap(deck.slides[1].payload.primary_visual, deck.number_formats)
    html = "\n".join(paint_heatmap_html(frozen))
    assert "heatmap-table" in html
    assert "heatmap-scale-key" in html
    assert re.search(r"background-color:#[0-9a-f]{6}", html)
    assert MISSING_VISIBLE in html


def test_uncolored_freeze_keeps_all_cells():
    deck = validate_handoff(_raw(), strict=True).deck
    frozen = freeze_heatmap(
        deck.slides[1].payload.primary_visual,
        deck.number_formats,
        colored=False,
    )
    assert frozen["colored"] is False
    assert frozen["scale"]["key_stops"] == []
    assert all(c["fill"] is None for row in frozen["cells"] for c in row)
    assert len(frozen["cells"]) == 3
    assert len(frozen["cells"][0]) == 3
