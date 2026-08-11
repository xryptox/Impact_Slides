"""Renderer v3 category-aligned chart support surfaces (#189).

Seams under test:
- typed support_table / outlined_support / metric_strip on single_chart (D140/D252)
- category vs independent alignment (D167/D266)
- outlined label lane + centers ≤2px of chart categories (D166/D267)
- metric strip complete content (D165/D265)
- D10/D47 allocation preserves 320×240 plot floor
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.models import (
    MetricStripSupport,
    OutlinedSupportVisual,
    SupportTableVisual,
)
from impact_slides.renderer_v3.plan import plan_deck
from impact_slides.renderer_v3.schema_export import check_schema

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/renderer_v3/minimal_line_chart.json"


def _raw() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _with_support(support: dict) -> dict:
    raw = _raw()
    raw["slides"][1]["payload"]["support"] = support
    return raw


def _cat_support_table(*, alignment: str = "category") -> dict:
    return {
        "support_type": "support_table",
        "alignment": alignment,
        "table": {
            "surface_id": "vol-support",
            "stub_header": {"label": "Metric"},
            "columns": [
                {"column_id": "q1", "label": "Q1'24"},
                {"column_id": "q2", "label": "Q2'24"},
                {"column_id": "q3", "label": "Q3'24"},
                {"column_id": "q4", "label": "Q4'24"},
            ],
            "rows": [
                {
                    "row_id": "mix",
                    "label": "Mix",
                    "cells": {
                        "q1": {"type": "number", "value": "1.0", "format_id": "pct_1"},
                        "q2": {"type": "number", "value": "2.0", "format_id": "pct_1"},
                        "q3": {"type": "missing"},
                        "q4": {"type": "number", "value": "3.0", "format_id": "pct_1"},
                    },
                }
            ],
        },
    }


def _outlined_support() -> dict:
    return {
        "support_type": "outlined_support",
        "table": {
            "surface_id": "vol-outlined",
            "stub_header": {"label": "ROE"},
            "columns": [
                {"column_id": "q1", "label": "Q1'24"},
                {"column_id": "q2", "label": "Q2'24"},
                {"column_id": "q3", "label": "Q3'24"},
                {"column_id": "q4", "label": "Q4'24"},
            ],
            "rows": [
                {
                    "row_id": "roe",
                    "label": "ROE",
                    "cells": {
                        "q1": {"type": "number", "value": "12.0", "format_id": "pct_1"},
                        "q2": {"type": "number", "value": "13.0", "format_id": "pct_1"},
                        "q3": {"type": "number", "value": "11.5", "format_id": "pct_1"},
                        "q4": {"type": "number", "value": "14.0", "format_id": "pct_1"},
                    },
                }
            ],
        },
    }


def _metric_strip() -> dict:
    return {
        "support_type": "metric_strip",
        "surface_id": "vol-metrics",
        "metrics": [
            {
                "metric_id": "m1",
                "label": "Peak",
                "value": {"type": "number", "value": "5.0", "format_id": "pct_1"},
            },
            {"metric_id": "m2", "label": "Gap", "value": {"type": "missing"}},
        ],
    }


# ---------------------------------------------------------------------------
# Validation / models
# ---------------------------------------------------------------------------


def test_schema_artifact_current():
    check_schema()


def test_support_table_category_validates():
    result = validate_handoff(_with_support(_cat_support_table()), strict=True)
    assert result.ok
    support = result.deck.slides[1].payload.support
    assert isinstance(support, SupportTableVisual)
    assert support.alignment == "category"
    assert len(support.table.rows) == 1
    assert [c.column_id for c in support.table.columns] == ["q1", "q2", "q3", "q4"]


def test_outlined_support_validates():
    result = validate_handoff(_with_support(_outlined_support()), strict=True)
    assert result.ok
    support = result.deck.slides[1].payload.support
    assert isinstance(support, OutlinedSupportVisual)
    assert len(support.table.rows) == 1


def test_metric_strip_support_validates():
    result = validate_handoff(_with_support(_metric_strip()), strict=True)
    assert result.ok
    support = result.deck.slides[1].payload.support
    assert isinstance(support, MetricStripSupport)
    assert len(support.metrics) == 2


def test_strict_rejects_category_column_mismatch():
    raw = _with_support(_cat_support_table())
    raw["slides"][1]["payload"]["support"]["table"]["columns"][0]["column_id"] = "qx"
    # cells still keyed q1 — rectangular fail or category mismatch
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_outlined_without_visible_category_axis():
    raw = _with_support(_outlined_support())
    raw["slides"][1]["payload"]["primary_visual"]["category_axis"]["visible"] = False
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_outlined_multi_row():
    raw = _with_support(_outlined_support())
    table = raw["slides"][1]["payload"]["support"]["table"]
    table["rows"].append(deepcopy(table["rows"][0]))
    table["rows"][1]["row_id"] = "roe2"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_legacy_support_visual_key():
    raw = _raw()
    raw["slides"][1]["payload"]["support_visual"] = _metric_strip()
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_independent_support_allows_unrelated_columns():
    raw = _with_support(
        {
            "support_type": "support_table",
            "alignment": "independent",
            "table": {
                "surface_id": "vol-indep",
                "stub_header": {"label": "KPI"},
                "columns": [
                    {"column_id": "a", "label": "A"},
                    {"column_id": "b", "label": "B"},
                ],
                "rows": [
                    {
                        "row_id": "r1",
                        "label": "Row",
                        "cells": {
                            "a": {"type": "text", "text": "one"},
                            "b": {"type": "text", "text": "two"},
                        },
                    }
                ],
            },
        }
    )
    assert validate_handoff(raw, strict=True).ok


# ---------------------------------------------------------------------------
# Plan / allocation
# ---------------------------------------------------------------------------


def test_support_table_preserves_rows_and_plot_floor():
    result = validate_handoff(_with_support(_cat_support_table()), strict=True)
    plan = plan_deck(result.deck, strict=True)
    chart = next(s for s in plan.surfaces if s.surface_id == "vol-trend")
    support = next(s for s in plan.surfaces if s.surface_id == "vol-support")
    g = chart.chart_paint["geometry"]
    assert g["plot_w"] >= 320
    assert g["plot_h"] >= 240
    assert support.role == "support_table"
    assert support.table_paint is not None
    assert support.table_paint["n_rows"] == 1
    assert support.table_paint.get("hide_header") is True
    assert "—" in support.table_paint["cells_vis"][0]  # missing em dash preserved
    # Category alignment freezes centers + content cell width for paint (D167).
    centers = support.table_paint.get("centers") or []
    assert support.table_paint.get("category_centered") is True
    assert len(centers) == 4
    assert int(support.table_paint.get("cell_w") or 0) >= 24
    cat_x = {c["category_id"]: c["x"] for c in chart.chart_paint["categories"]}
    for c in centers:
        assert abs(c["x"] - cat_x[c["category_id"]]) <= 2.0


def test_outlined_centers_align_within_2px():
    result = validate_handoff(_with_support(_outlined_support()), strict=True)
    plan = plan_deck(result.deck, strict=True)
    chart = next(s for s in plan.surfaces if s.surface_id == "vol-trend")
    support = next(s for s in plan.surfaces if s.surface_id == "vol-outlined")
    cat_x = {c["category_id"]: c["x"] for c in chart.chart_paint["categories"]}
    centers = support.table_paint["centers"]
    assert len(centers) == 4
    for c in centers:
        assert abs(c["x"] - cat_x[c["category_id"]]) <= 2.0
    assert support.table_paint["label_lane_w"] > 0
    # Frozen geometry only — paint must not recompute (D69).
    assert "box_h" in support.table_paint and "row_h" in support.table_paint
    box_w = support.table_paint["box_w"]
    first_left = centers[0]["x"] - box_w / 2
    assert support.table_paint["label_lane_w"] <= first_left + 2


def test_metric_strip_plan_preserves_metrics_and_floor():
    result = validate_handoff(_with_support(_metric_strip()), strict=True)
    plan = plan_deck(result.deck, strict=True)
    chart = next(s for s in plan.surfaces if s.surface_id == "vol-trend")
    strip = next(s for s in plan.surfaces if s.surface_id == "vol-metrics")
    g = chart.chart_paint["geometry"]
    assert g["plot_w"] >= 320 and g["plot_h"] >= 240
    assert strip.role == "metric_strip"
    metrics = strip.table_paint["metrics"]
    assert [m["metric_id"] for m in metrics] == ["m1", "m2"]
    assert metrics[1]["visible"] == "—"


# ---------------------------------------------------------------------------
# Paint / publication
# ---------------------------------------------------------------------------


def test_paint_support_table_complete_rows(tmp_path: Path):
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(_with_support(_cat_support_table())), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-table-surface="vol-support"' in html
    assert "support-table" in html
    assert "Mix" in html
    assert "—" in html  # missing cell
    assert 'data-category-centered="true"' in html
    # Semantic table remains for a11y; visual cells are center-positioned.
    assert "support-cat-cell" in html
    lefts = [float(x) for x in re.findall(r'support-cat-cell[^>]*left:([0-9.]+)px', html)]
    assert len(lefts) == 4
    result = validate_handoff(_with_support(_cat_support_table()), strict=True)
    plan = plan_deck(result.deck, strict=True)
    chart = next(s for s in plan.surfaces if s.surface_id == "vol-trend")
    cat_x = [c["x"] for c in chart.chart_paint["categories"]]
    for painted, frozen in zip(lefts, cat_x):
        assert abs(painted - frozen) <= 2.0


def test_paint_outlined_support_alignment(tmp_path: Path):
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(_with_support(_outlined_support())), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-outlined-support="vol-outlined"' in html
    assert "outlined-support-label" in html
    assert "ROE" in html
    lefts = [float(x) for x in re.findall(r"outlined-support-box[^>]*left:([0-9.]+)px", html)]
    assert len(lefts) == 4
    # Pull frozen chart centers from run_meta plans via re-plan.
    result = validate_handoff(_with_support(_outlined_support()), strict=True)
    plan = plan_deck(result.deck, strict=True)
    chart = next(s for s in plan.surfaces if s.surface_id == "vol-trend")
    cat_x = [c["x"] for c in chart.chart_paint["categories"]]
    for painted, frozen in zip(lefts, cat_x):
        assert abs(painted - frozen) <= 2.0


def test_paint_metric_strip_complete(tmp_path: Path):
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(_with_support(_metric_strip())), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-metric-strip="vol-metrics"' in html
    assert "Peak" in html
    assert "Gap" in html
    assert "—" in html


def test_no_support_still_renders(tmp_path: Path):
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(_raw()), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-chart-surface="vol-trend"' in html
    assert "data-outlined-support=" not in html
    assert 'data-metric-strip="vol-metrics"' not in html



def test_strict_rejects_category_support_on_horizontal_bar():
    raw = json.loads((ROOT / "tests/fixtures/renderer_v3/minimal_horizontal_bar.json").read_text(encoding="utf-8"))
    raw["slides"][1]["payload"]["support"] = {
        "support_type": "support_table",
        "alignment": "category",
        "table": {
            "surface_id": "hbar-support",
            "stub_header": {"label": "Metric"},
            "columns": [
                {"column_id": "us", "label": "US"},
                {"column_id": "uk", "label": "UK"},
                {"column_id": "jp", "label": "JP"},
                {"column_id": "mx", "label": "MX"},
            ],
            "rows": [
                {
                    "row_id": "mix",
                    "label": "Mix",
                    "cells": {
                        "us": {"type": "number", "value": "1.0", "format_id": "pct_1"},
                        "uk": {"type": "number", "value": "2.0", "format_id": "pct_1"},
                        "jp": {"type": "number", "value": "3.0", "format_id": "pct_1"},
                        "mx": {"type": "number", "value": "4.0", "format_id": "pct_1"},
                    },
                }
            ],
        },
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_strict_rejects_outlined_support_on_horizontal_bar():
    raw = json.loads((ROOT / "tests/fixtures/renderer_v3/minimal_horizontal_bar.json").read_text(encoding="utf-8"))
    raw["slides"][1]["payload"]["support"] = {
        "support_type": "outlined_support",
        "table": {
            "surface_id": "hbar-outlined",
            "stub_header": {"label": "ROE"},
            "columns": [
                {"column_id": "us", "label": "US"},
                {"column_id": "uk", "label": "UK"},
                {"column_id": "jp", "label": "JP"},
                {"column_id": "mx", "label": "MX"},
            ],
            "rows": [
                {
                    "row_id": "roe",
                    "label": "ROE",
                    "cells": {
                        "us": {"type": "number", "value": "1.0", "format_id": "pct_1"},
                        "uk": {"type": "number", "value": "2.0", "format_id": "pct_1"},
                        "jp": {"type": "number", "value": "3.0", "format_id": "pct_1"},
                        "mx": {"type": "number", "value": "4.0", "format_id": "pct_1"},
                    },
                }
            ],
        },
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_non_strict_outlined_overflow_keeps_category():
    from impact_slides.renderer_v3 import plan as plan_mod

    result = validate_handoff(_with_support(_outlined_support()), strict=True)
    real = plan_mod._outlined_support_fit_detail

    def never_fits(sp, size):
        return False, True

    plan_mod._outlined_support_fit_detail = never_fits  # type: ignore[assignment]
    try:
        plan = plan_deck(result.deck, strict=False)
    finally:
        plan_mod._outlined_support_fit_detail = real  # type: ignore[assignment]
    support = next(s for s in plan.surfaces if s.surface_id == "vol-outlined")
    assert support.role == "support_table"
    assert support.fallback == "support_table"
    assert support.table_paint.get("alignment") == "category"
    assert support.table_paint.get("kind") == "support_table"
    centers = support.table_paint.get("centers") or []
    assert len(centers) == 4


def test_outlined_keep_cat_then_width_freeze_fail_demotes_independent():
    from impact_slides.renderer_v3 import plan as plan_mod

    result = validate_handoff(_with_support(_outlined_support()), strict=True)
    real_fit = plan_mod._outlined_support_fit_detail
    real_widths = plan_mod._apply_category_table_widths

    def never_fits(sp, size):
        return False, True

    def boom(spec, centers, box_w):
        spec.pop("category_centered", None)
        return False

    plan_mod._outlined_support_fit_detail = never_fits  # type: ignore[assignment]
    plan_mod._apply_category_table_widths = boom  # type: ignore[assignment]
    try:
        plan = plan_deck(result.deck, strict=False)
    finally:
        plan_mod._outlined_support_fit_detail = real_fit  # type: ignore[assignment]
        plan_mod._apply_category_table_widths = real_widths  # type: ignore[assignment]
    support = next(s for s in plan.surfaces if s.surface_id == "vol-outlined")
    assert support.role == "support_table"
    assert support.fallback == "independent_support_table"
    assert support.table_paint.get("alignment") == "independent"
    assert support.table_paint.get("category_centered") is not True
    assert "plan.support_alignment_independent" in support.adaptation_codes


def test_category_height_overflow_demotes_clears_category_centered():
    from impact_slides.renderer_v3 import plan as plan_mod

    result = validate_handoff(_with_support(_cat_support_table()), strict=True)
    real = plan_mod._table_fit_detail

    def never_fits(spec, px, box_w, box_h, **kwargs):
        return False, [], 10**9

    plan_mod._table_fit_detail = never_fits  # type: ignore[assignment]
    try:
        plan = plan_deck(result.deck, strict=False)
    finally:
        plan_mod._table_fit_detail = real  # type: ignore[assignment]
    support = next(s for s in plan.surfaces if s.surface_id == "vol-support")
    assert support.fallback == "independent_support_table"
    assert support.table_paint.get("alignment") == "independent"
    assert support.table_paint.get("category_centered") is not True
    assert "plan.support_alignment_independent" in support.adaptation_codes


def test_category_width_freeze_failure_demotes_non_strict():
    from impact_slides.renderer_v3 import plan as plan_mod

    result = validate_handoff(_with_support(_cat_support_table()), strict=True)
    real = plan_mod._apply_category_table_widths

    def boom(spec, centers, box_w):
        spec.pop("category_centered", None)
        return False

    plan_mod._apply_category_table_widths = boom  # type: ignore[assignment]
    try:
        with pytest.raises(RendererValidationError):
            plan_deck(result.deck, strict=True)
        plan = plan_deck(result.deck, strict=False)
        support = next(s for s in plan.surfaces if s.surface_id == "vol-support")
        assert support.table_paint.get("alignment") == "independent"
        assert support.table_paint.get("category_centered") is not True
        assert support.fallback == "independent_support_table"
        assert "plan.support_alignment_independent" in support.adaptation_codes
    finally:
        plan_mod._apply_category_table_widths = real  # type: ignore[assignment]



# ---------------------------------------------------------------------------
# Mutation traps
# ---------------------------------------------------------------------------


def test_mutation_drop_support_row_fails_validation():
    raw = _with_support(_cat_support_table())
    raw["slides"][1]["payload"]["support"]["table"]["rows"] = []
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_mutation_reorder_category_columns_fails():
    raw = _with_support(_cat_support_table())
    cols = raw["slides"][1]["payload"]["support"]["table"]["columns"]
    cols[0], cols[1] = cols[1], cols[0]
    # cells still keyed correctly but order wrong vs chart
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)
