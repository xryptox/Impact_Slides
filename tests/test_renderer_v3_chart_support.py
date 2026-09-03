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
    raw["slides"][1]["payload"]["chart"]["category_axis"]["visible"] = False
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
    # Single style attr: font + relative box (duplicate style= drops height in HTML).
    m = re.search(
        r'class="support-table category-aligned"[^>]*style="([^"]+)"',
        html,
    )
    assert m is not None
    style = m.group(1)
    assert "position:relative" in style and "height:" in style
    assert style.count("style=") == 0
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


def test_category_support_visible_cells_carry_table_chrome(tmp_path: Path):
    """#247: visible category cells get navy header band + hairline borders."""
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    from impact_slides.renderer_v3.theme import resolve_color

    raw = _with_support(_cat_support_table())
    # Hidden category axis keeps category alignment but paints the visual header.
    raw["slides"][1]["payload"]["chart"]["category_axis"]["visible"] = False
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(handoff, out, strict=True)["ok"] is True
    html_path = (out / "presentation.html").resolve()

    result = validate_handoff(raw, strict=True)
    plan = plan_deck(result.deck, strict=True)
    chart = next(s for s in plan.surfaces if s.surface_id == "vol-trend")
    cat_x = [c["x"] for c in chart.chart_paint["categories"]]
    navy = resolve_color("navy", role="band")
    ink = resolve_color("white", role="text_on_dark")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(html_path.as_uri(), wait_until="networkidle")
        styles = page.evaluate(
            """() => {
              const vis = (el) => {
                const r = el.getBoundingClientRect();
                return r.width > 1 && r.height > 1;
              };
              const cells = [...document.querySelectorAll(
                '.support-table.category-aligned .support-cat-cell'
              )].filter(vis);
              const heads = cells.filter(el => el.classList.contains('head'));
              const bodies = cells.filter(el => !el.classList.contains('head'));
              const stubs = [...document.querySelectorAll(
                '.support-table.category-aligned .support-cat-stub'
              )].filter(vis);
              const cs = (el) => getComputedStyle(el);
              const pack = (el) => {
                const s = cs(el);
                return {
                  bg: s.backgroundColor,
                  color: s.color,
                  weight: s.fontWeight,
                  borderTop: s.borderTopWidth,
                  borderRight: s.borderRightWidth,
                  borderBottom: s.borderBottomWidth,
                  borderLeft: s.borderLeftWidth,
                  borderColor: s.borderTopColor,
                  left: parseFloat(s.left),
                };
              };
              return {
                heads: heads.map(pack),
                bodies: bodies.map(pack),
                stubs: stubs.map(pack),
              };
            }"""
        )
        browser.close()

    def _rgb(hex_color: str) -> str:
        h = hex_color.lstrip("#")
        return f"rgb({int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)})"

    navy_rgb = _rgb(navy)
    ink_rgb = _rgb(ink)
    assert styles["heads"], "visible header cells must paint"
    assert styles["bodies"], "visible body cells must paint"
    assert styles["stubs"], "visible stub labels must paint"
    for head in styles["heads"]:
        assert head["bg"] == navy_rgb
        assert head["color"] == ink_rgb
        assert int(head["weight"]) >= 600
        assert head["borderTop"] == "1px"
        assert head["borderBottom"] == "1px"
    for body in styles["bodies"]:
        assert body["borderTop"] == "1px"
        assert body["borderRight"] == "1px"
        assert body["borderBottom"] == "1px"
        assert body["borderLeft"] == "1px"
        assert body["borderColor"] == navy_rgb
        assert body["bg"] != navy_rgb
    for stub in styles["stubs"]:
        assert stub["borderTop"] == "1px"
        assert stub["borderRight"] == "1px"
        assert stub["borderBottom"] == "1px"
        assert stub["borderLeft"] == "1px"
    painted_lefts = [h["left"] for h in styles["heads"]]
    for painted, frozen in zip(painted_lefts, cat_x):
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
    m = re.search(r'class="outlined-support"[^>]*style="([^"]+)"', html)
    assert m is not None
    style = m.group(1)
    assert "height:" in style
    # Boxes must paint a real border using a theme token that exists.
    assert (
        ".outlined-support-box" in html
        and "border:var(--border-width-hairline) solid var(--color-navy)" in html
    )
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

def _hero_with_support(support: dict) -> dict:
    raw = _raw()
    chart = deepcopy(raw["slides"][1]["payload"]["chart"])
    chart["surface_id"] = "hero-chart"
    raw["slides"][1] = {
        "slide_number": 2,
        "layout_type": "chart_hero_dual",
        "section_id": "trends",
        "title": "Hero support",
        "payload": {
            "chart": chart,
            "hero": {
                "hero_type": "metric_stack",
                "surface_id": "hero-stack",
                "heading": "Summary",
                "metrics": [
                    {
                        "metric_id": "m1",
                        "label": "Peak",
                        "value": {
                            "type": "number",
                            "value": "5.0",
                            "format_id": "pct_1",
                        },
                    }
                ],
            },
            "support": deepcopy(support),
        },
        "evidence_ids": ["src-board-pack"],
    }
    return raw


def _hero_with_outlined_support() -> dict:
    support = _outlined_support()
    support["table"]["surface_id"] = "hero-outlined"
    return _hero_with_support(support)


def test_hero_outlined_support_validates_and_plans():
    result = validate_handoff(_hero_with_outlined_support(), strict=True)
    plan = plan_deck(result.deck, strict=True)
    outlined = [s for s in plan.surfaces if s.role == "outlined_support"]
    assert len(outlined) == 1
    assert outlined[0]._table_spec["kind"] == "outlined_support"
    assert outlined[0]._table_spec.get("centers")


def test_hero_outlined_support_rejects_row_and_category_mismatches():
    raw = _hero_with_outlined_support()
    row = raw["slides"][1]["payload"]["support"]["table"]["rows"][0]
    raw["slides"][1]["payload"]["support"]["table"]["rows"].append(
        {**deepcopy(row), "row_id": "extra"}
    )
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)

    raw = _hero_with_outlined_support()
    cols = raw["slides"][1]["payload"]["support"]["table"]["columns"]
    cols[0], cols[1] = cols[1], cols[0]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_paint_hero_outlined_support_boxes(tmp_path: Path):
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(_hero_with_outlined_support()), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-outlined-support="hero-outlined"' in html
    assert "outlined-support-box" in html
    assert "support-table" not in html.split("chart-hero-dual")[1].split(
        "chart-hero-right"
    )[0] or "outlined-support" in html


def test_nonstrict_drops_unknown_hero_support_on_every_slide():
    raw = _hero_with_outlined_support()
    later = deepcopy(raw["slides"][1])
    later["slide_number"] = 3
    later["payload"]["chart"]["surface_id"] = "hero-chart-2"
    later["payload"]["hero"]["surface_id"] = "hero-stack-2"
    later["payload"]["support"]["table"]["surface_id"] = "hero-outlined-2"
    raw["slides"][1]["payload"]["support"]["legacy_note"] = "drop-me"
    later["payload"]["support"]["legacy_note"] = "drop-me-too"
    raw["slides"].insert(2, later)
    raw["slides"][-1]["slide_number"] = 4
    result = validate_handoff(raw, strict=False)
    assert result.ok
    dumped = result.deck.model_dump(mode="json", exclude_none=True)
    hero_supports = [
        s["payload"]["support"]
        for s in dumped["slides"]
        if s["layout_type"] == "chart_hero_dual"
    ]
    assert len(hero_supports) == 2
    assert all("legacy_note" not in support for support in hero_supports)
    paths = {e.path for e in result.events if e.code == "repair.field_dropped"}
    assert "/slides/1/payload/support/legacy_note" in paths
    assert "/slides/2/payload/support/legacy_note" in paths


def test_nonstrict_missing_slides_raises_validation_not_nameerror():
    with pytest.raises(RendererValidationError):
        validate_handoff({"meta": {"handoff_schema_version": 1}}, strict=False)


def test_hero_support_table_category_validates_and_plans():
    support = _cat_support_table()
    support["table"]["surface_id"] = "hero-support"
    result = validate_handoff(_hero_with_support(support), strict=True)
    plan = plan_deck(result.deck, strict=True)
    chart = next(s for s in plan.surfaces if s.surface_id == "hero-chart")
    table = next(s for s in plan.surfaces if s.surface_id == "hero-support")
    assert table.role == "support_table"
    assert table.table_paint.get("alignment") == "category"
    assert table.table_paint.get("category_centered") is True
    assert table.table_paint.get("hide_header") is True
    centers = table.table_paint.get("centers") or []
    assert len(centers) == 4
    cat_x = {c["category_id"]: c["x"] for c in chart.chart_paint["categories"]}
    for c in centers:
        assert abs(c["x"] - cat_x[c["category_id"]]) <= 2.0


def test_paint_hero_support_table_uses_frozen_centers(tmp_path: Path):
    support = _cat_support_table()
    support["table"]["surface_id"] = "hero-support"
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(_hero_with_support(support)), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-table-surface="hero-support"' in html
    assert 'data-category-centered="true"' in html
    assert "support-cat-cell" in html
    lefts = [float(x) for x in re.findall(r"support-cat-cell[^>]*left:([0-9.]+)px", html)]
    assert len(lefts) == 4
    result = validate_handoff(_hero_with_support(support), strict=True)
    plan = plan_deck(result.deck, strict=True)
    chart = next(s for s in plan.surfaces if s.surface_id == "hero-chart")
    cat_x = [c["x"] for c in chart.chart_paint["categories"]]
    for painted, frozen in zip(lefts, cat_x):
        assert abs(painted - frozen) <= 2.0


def test_paint_hero_metric_strip_complete(tmp_path: Path):
    support = _metric_strip()
    support["surface_id"] = "hero-metrics"
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(_hero_with_support(support)), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-metric-strip="hero-metrics"' in html
    assert "Peak" in html
    assert "Gap" in html
    assert "—" in html


def test_hero_support_table_rejects_column_mismatch():
    support = _cat_support_table()
    support["table"]["surface_id"] = "hero-support"
    raw = _hero_with_support(support)
    cols = raw["slides"][1]["payload"]["support"]["table"]["columns"]
    cols[0], cols[1] = cols[1], cols[0]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_hero_rejects_category_support_on_horizontal_bar():
    raw = json.loads(
        (ROOT / "tests/fixtures/renderer_v3/minimal_horizontal_bar.json").read_text(
            encoding="utf-8"
        )
    )
    chart = deepcopy(raw["slides"][1]["payload"]["chart"])
    raw["slides"][1]["layout_type"] = "chart_hero_dual"
    raw["slides"][1]["payload"] = {
        "chart": chart,
        "hero": {
            "hero_type": "metric_stack",
            "surface_id": "hero-stack",
            "heading": "Summary",
            "metrics": [
                {
                    "metric_id": "m1",
                    "label": "Peak",
                    "value": {
                        "type": "number",
                        "value": "5.0",
                        "format_id": "pct_1",
                    },
                }
            ],
        },
        "support": {
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
        },
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def _dual_raw(support: dict | None = None) -> dict:
    raw = _raw()
    chart = deepcopy(raw["slides"][1]["payload"]["chart"])
    peer = deepcopy(chart)
    peer["surface_id"] = "vol-peer"
    peer["heading"] = "Peer billed"
    payload: dict = {"charts": [chart, peer]}
    if support is not None:
        payload["support"] = deepcopy(support)
    raw["slides"][1]["layout_type"] = "dual_chart"
    raw["slides"][1]["payload"] = payload
    return raw


def _indep_support_table() -> dict:
    return {
        "support_type": "support_table",
        "alignment": "independent",
        "table": {
            "surface_id": "dual-support",
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


def test_dual_omitted_support_validates():
    result = validate_handoff(_dual_raw(), strict=True)
    assert result.ok
    assert result.deck.slides[1].payload.support is None


def test_dual_independent_support_table_validates():
    result = validate_handoff(_dual_raw(_indep_support_table()), strict=True)
    assert result.ok
    support = result.deck.slides[1].payload.support
    assert isinstance(support, SupportTableVisual)
    assert support.alignment == "independent"


def test_dual_metric_strip_validates():
    support = _metric_strip()
    support["surface_id"] = "dual-metrics"
    result = validate_handoff(_dual_raw(support), strict=True)
    assert result.ok
    strip = result.deck.slides[1].payload.support
    assert isinstance(strip, MetricStripSupport)
    assert strip.surface_id == "dual-metrics"


def test_dual_rejects_category_aligned_shared_table():
    with pytest.raises(RendererValidationError):
        validate_handoff(_dual_raw(_cat_support_table()), strict=True)


def test_dual_rejects_outlined_shared_support():
    with pytest.raises(RendererValidationError):
        validate_handoff(_dual_raw(_outlined_support()), strict=True)


def test_dual_rejects_support_id_collision_with_chart():
    support = _indep_support_table()
    support["table"]["surface_id"] = "vol-trend"
    with pytest.raises(RendererValidationError):
        validate_handoff(_dual_raw(support), strict=True)
    strip = _metric_strip()
    strip["surface_id"] = "vol-peer"
    with pytest.raises(RendererValidationError):
        validate_handoff(_dual_raw(strip), strict=True)


def test_dual_rejects_heatmap_and_panes():
    heat = json.loads(
        (ROOT / "tests/fixtures/renderer_v3/minimal_heatmap.json").read_text(
            encoding="utf-8"
        )
    )["slides"][1]["payload"]["chart"]
    raw = _dual_raw()
    raw["slides"][1]["payload"]["charts"][0] = heat
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)
    raw = _dual_raw()
    raw["slides"][1]["payload"]["panes"] = raw["slides"][1]["payload"]["charts"]
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_dual_mutation_drop_support_still_renders_two_charts(tmp_path: Path):
    raw = _dual_raw(_indep_support_table())
    assert validate_handoff(raw, strict=True).ok
    del raw["slides"][1]["payload"]["support"]
    result = validate_handoff(raw, strict=True)
    assert result.ok
    assert result.deck.slides[1].payload.support is None
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-chart-surface="vol-trend"' in html
    assert 'data-chart-surface="vol-peer"' in html
    assert 'data-table-surface="dual-support"' not in html


def test_dual_mutation_category_alignment_fails_typed_validation():
    raw = _dual_raw(_indep_support_table())
    raw["slides"][1]["payload"]["support"]["alignment"] = "category"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_dual_support_plans_preserve_plot_floor():
    result = validate_handoff(_dual_raw(_indep_support_table()), strict=True)
    plan = plan_deck(result.deck, strict=True)
    charts = [s for s in plan.surfaces if s.surface_id in {"vol-trend", "vol-peer"}]
    support = next(s for s in plan.surfaces if s.surface_id == "dual-support")
    assert len(charts) == 2
    heights = {s.chart_paint["geometry"]["plot_h"] for s in charts}
    assert len(heights) == 1
    for s in charts:
        g = s.chart_paint["geometry"]
        assert g["plot_w"] >= 320
        assert g["plot_h"] >= 240
    assert support.role == "support_table"
    assert support.table_paint.get("alignment") == "independent"


def test_paint_dual_shared_support_under_both_panes(tmp_path: Path):
    raw = _dual_raw(_indep_support_table())
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert html.count('class="dual-chart-pane"') == 2
    assert html.count('data-table-surface="dual-support"') == 1
    last_pane = html.rfind('class="dual-chart-pane"')
    support_at = html.find('data-table-surface="dual-support"')
    assert last_pane != -1 and support_at != -1
    assert support_at > last_pane
    for sid in ("vol-trend", "vol-peer"):
        assert f'data-chart-surface="{sid}"' in html
        assert f'id="{sid}-semantic-table"' in html
        assert f'id="cjs-{sid}"' in html or "chartjs-canvas" in html
    assert "<noscript>" in html
    assert "<svg" in html
    assert "support-table" in html
    assert "one" in html and "two" in html


def test_paint_dual_metric_strip_under_both_panes(tmp_path: Path):
    support = _metric_strip()
    support["surface_id"] = "dual-metrics"
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(_dual_raw(support)), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(handoff, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert html.count('data-metric-strip="dual-metrics"') == 1
    last_pane = html.rfind('class="dual-chart-pane"')
    strip_at = html.find('data-metric-strip="dual-metrics"')
    assert last_pane != -1 and strip_at != -1
    assert strip_at > last_pane


def test_nonstrict_drops_unknown_dual_support_fields():
    raw = _dual_raw(_indep_support_table())
    raw["slides"][1]["payload"]["support"]["legacy_note"] = "drop-me"
    result = validate_handoff(raw, strict=False)
    assert result.ok
    dumped = result.deck.model_dump(mode="json", exclude_none=True)
    support = dumped["slides"][1]["payload"]["support"]
    assert "legacy_note" not in support
    paths = {e.path for e in result.events if e.code == "repair.field_dropped"}
    assert "/slides/1/payload/support/legacy_note" in paths


def test_dual_support_surface_ids_are_deck_unique():
    raw = _dual_raw(_indep_support_table())
    extra = deepcopy(raw["slides"][1])
    extra["slide_number"] = 4
    extra["payload"]["charts"][0]["surface_id"] = "vol-trend-b"
    extra["payload"]["charts"][1]["surface_id"] = "vol-peer-b"
    extra["payload"]["charts"][0]["heading"] = "Other billed"
    extra["payload"]["charts"][1]["heading"] = "Other peer"
    raw["slides"].insert(2, extra)
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)
    strip = _metric_strip()
    strip["surface_id"] = "dual-metrics"
    raw = _dual_raw(strip)
    extra = deepcopy(raw["slides"][1])
    extra["slide_number"] = 4
    extra["payload"]["charts"][0]["surface_id"] = "vol-trend-b"
    extra["payload"]["charts"][1]["surface_id"] = "vol-peer-b"
    extra["payload"]["charts"][0]["heading"] = "Other billed"
    extra["payload"]["charts"][1]["heading"] = "Other peer"
    raw["slides"].insert(2, extra)
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_dual_support_table_format_ids_are_accounted():
    raw = _dual_raw(_indep_support_table())
    raw["number_formats"]["usd_1"] = {
        "unit": "usd",
        "value_decimals": 1,
        "negative_style": "minus",
    }
    raw["slides"][1]["payload"]["support"]["table"]["rows"][0]["cells"]["a"] = {
        "type": "number",
        "value": "1.0",
        "format_id": "usd_1",
    }
    assert validate_handoff(raw, strict=True).ok
    raw["slides"][1]["payload"]["support"]["table"]["rows"][0]["cells"]["a"][
        "format_id"
    ] = "nope"
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_nonstrict_repairs_dual_support_table_cells():
    raw = _dual_raw(_indep_support_table())
    table = raw["slides"][1]["payload"]["support"]["table"]
    table["rows"][0]["cells"]["a"] = {"type": "number"}
    table["rows"][0]["cells"]["ghost"] = {"type": "text", "text": "x"}
    del table["rows"][0]["cells"]["b"]
    with pytest.raises(RendererValidationError):
        validate_handoff(deepcopy(raw), strict=True)
    result = validate_handoff(raw, strict=False)
    assert result.ok
    cells = result.deck.slides[1].payload.support.table.rows[0].cells
    assert set(cells) == {"a", "b"}
    assert cells["a"].type == "missing"
    assert cells["b"].type == "missing"
    assert {e.code for e in result.events} >= {
        "repair.value_to_missing",
        "repair.field_dropped",
    }


def test_playwright_dual_support_sits_under_both_panes(tmp_path: Path):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(_dual_raw(_indep_support_table())), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(handoff, out, strict=True)["ok"] is True
    html_path = (out / "presentation.html").resolve()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(html_path.as_uri(), wait_until="networkidle")
        geom = page.evaluate(
            """() => {
              const row = document.querySelector('.dual-chart');
              const support = document.querySelector(
                '[data-table-surface="dual-support"]'
              );
              const panes = [...document.querySelectorAll('.dual-chart-pane')];
              const r = (el) => {
                const b = el.getBoundingClientRect();
                return {left: b.left, right: b.right, top: b.top, bottom: b.bottom, width: b.width};
              };
              return {
                row: r(row),
                support: r(support),
                panes: panes.map(r),
                insidePane: panes.some((p) => p.contains(support)),
              };
            }"""
        )
        browser.close()
    assert len(geom["panes"]) == 2
    assert geom["insidePane"] is False
    assert geom["support"]["top"] >= geom["row"]["bottom"] - 1
    assert abs(geom["support"]["left"] - geom["row"]["left"]) <= 2
    assert abs(geom["support"]["width"] - geom["row"]["width"]) <= 2

