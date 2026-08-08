"""#155 — restore Amex PDF page 21 capital-return chart composition.

Handoff correction plus the minimal combo capability extensions: stacked bars
with a dual-axis shares line, explicit stack totals, and a category-aligned
outlined ROE support row under a chart_hero_dual left pane. Identity-safe
browser evidence addresses slide 21 by number + layout.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from amex_handoff_mutations import (  # noqa: E402
    apply_all,
    apply_issue_155_slide21_capital,
)
from impact_slides.renderer_v2 import render_deck  # noqa: E402
from impact_slides.renderer_v2.charts.chartjs import (  # noqa: E402
    _chartjs_combo_config,
)
from impact_slides.renderer_v2.charts.lines import (  # noqa: E402
    _build_combo_chart_svg,
)
from impact_slides.renderer_v2.layout.dispatch import render_slide  # noqa: E402
from impact_slides.renderer_v2.schemas import validate_slide  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "renderer_v2"
BROKEN = FIXTURES / "amex_s21_v10_broken.json"

_HERO = "chart_hero" + "_dual"
_COMBO = "combo" + "_chart"
_QUARTERS = ["Q4'24", "Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"]
_STACK_TOTALS = ["$1.6", "$1.3", "$2.0", "$2.9", "$1.5", "$2.3"]
_SHARES = [702, 701, 696, 689, 686, 682]
_ROE = ["35%", "34%", "36%", "36%", "34%", "35%"]
_PANE_HEADING = "Capital Return & Common Shares Outstanding"
_PANE_SUB = "$ in billions; Common Shares Outstanding in millions"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _slide(handoff: dict) -> dict:
    return next(s for s in handoff["slides"] if int(s["slide_number"]) == 21)


def _corrected() -> dict:
    return _slide(apply_issue_155_slide21_capital(copy.deepcopy(_load(BROKEN))))


def _assert_semantics(slide: dict) -> None:
    assert slide["layout_type"] == _HERO
    pv = slide["visual_spec"]["primary_visual"]
    assert pv["type"] == _COMBO
    assert pv["heading"] == _PANE_HEADING
    assert pv["subtitle"] == _PANE_SUB
    steps = pv["steps_or_data"]
    assert steps[0] == ["Quarter", "Dividends", "Share Repurchases"]
    assert [r[0] for r in steps[1:]] == _QUARTERS
    assert [float(r[1]) for r in steps[1:]] == [0.5, 0.6, 0.6, 0.6, 0.6, 0.7]
    assert [float(r[2]) for r in steps[1:]] == [1.1, 0.7, 1.4, 2.3, 0.9, 1.6]
    cfg = pv["chart_config"]
    assert cfg["stack_totals"] is True
    assert cfg["stack_total_labels"] == _STACK_TOTALS
    overlay = slide["visual_spec"]["line_overlay"]
    assert overlay["label"] == "Common Shares Outstanding"
    assert overlay["y_axis_min"] == 670
    assert overlay["y_axis_max"] == 710
    assert overlay["y_axis_ticks"] == [670, 680, 690, 700, 710]
    assert [p["value"] for p in overlay["data"]] == _SHARES
    assert [p["label"] for p in overlay["data"]] == _QUARTERS
    support = slide["visual_spec"]["secondary_visual"]
    assert support["skin"] == "outlined_boxes"
    assert support["steps_or_data"] == [
        ["", *_QUARTERS],
        ["Return on Average Equity", *_ROE],
    ]
    stats = {s["label"]: s["value"] for s in slide["content"]["key_stats"]}
    assert stats["Dividend/share ↑ (3yr)"] == "58%"
    assert stats["NI Returned (3yr)"] == "74%"
    assert stats["CET1 Ratio Q1'26"] == "10.5%"
    assert stats["CET1 Target"] == "10–11%"
    # Left-panel facts must not reappear as detached KPIs.
    assert "Shares Outstanding" not in stats
    assert "ROE Q1'26" not in stats
    assert "Q1'26 Capital Returned" not in stats
    assert "682" not in json.dumps(slide["content"]["key_stats"])
    assert "35%" not in {s["value"] for s in slide["content"]["key_stats"]}


def test_broken_fixture_still_documents_v10_defect():
    broken = _slide(_load(BROKEN))
    assert broken["layout_type"] == "multi_panel"
    labels = {s["label"] for s in broken["content"]["key_stats"]}
    assert "Shares Outstanding" in labels
    assert "ROE Q1'26" in labels
    tiles = broken["visual_spec"]["primary_visual"]["tiles"]
    chart = next(t for t in tiles if t.get("kind") == "chart")
    assert chart["chart_type"] == "stacked_bar_chart"
    assert not chart.get("chart_config", {}).get("stack_total_labels")
    assert "line_overlay" not in broken["visual_spec"]


def test_mutation_restores_source_semantics_and_is_idempotent():
    once = _corrected()
    _assert_semantics(once)
    twice = _slide(
        apply_issue_155_slide21_capital(
            {"slides": [copy.deepcopy(once)]}
        )
    )
    assert twice == once
    model, err = validate_slide(once)
    assert err is None, err
    assert model is not None and model.layout_type == _HERO


def test_apply_all_includes_155():
    out = apply_all(copy.deepcopy(_load(BROKEN)))
    _assert_semantics(_slide(out))


def test_chartjs_combo_stacks_and_emits_stack_totals():
    slide = _corrected()
    # chartjs combo reads layout_type combo + visual_spec as-authored
    slide = {**slide, "layout_type": _COMBO}
    cfg = _chartjs_combo_config(slide)
    assert cfg is not None
    assert cfg["options"]["scales"]["x"]["stacked"] is True
    assert cfg["options"]["scales"]["y"]["stacked"] is True
    bar_ds = [d for d in cfg["data"]["datasets"] if d.get("type") == "bar"]
    line_ds = [d for d in cfg["data"]["datasets"] if d.get("type") == "line"]
    assert len(bar_ds) == 2
    assert all(d.get("stack") == "combo" for d in bar_ds)
    assert len(line_ds) == 1
    assert line_ds[0]["label"] == "Common Shares Outstanding"
    assert line_ds[0]["data"] == _SHARES
    assert "y1" in cfg["options"]["scales"]
    labels = cfg["options"]["plugins"]["datalabels"]["_labels"]
    flat = [cell for row in labels for cell in row if cell]
    assert flat == _STACK_TOTALS


def test_svg_combo_preserves_stack_totals_and_line():
    slide = {**_corrected(), "layout_type": _COMBO}
    svg = _build_combo_chart_svg(slide)
    assert "combo-chart" in svg
    assert svg.count("vbar-stack-total") == 6
    for total in _STACK_TOTALS:
        assert total in svg
    assert "polyline" in svg
    assert svg.count("<circle") >= 6
    assert "Common Shares Outstanding" in svg or "combo-bar-legend" in svg


def test_render_includes_support_row_and_right_kpis():
    slide = _corrected()
    html = render_slide(slide, total=44, notes="", active=True, use_chartjs=True)
    assert 'data-layout="chart_hero_dual"' in html or "chart_hero_dual" in html
    # Pane title escapes &; hero values split number/% spans.
    assert "Capital Return" in html and "Common Shares Outstanding" in html
    assert _PANE_SUB in html
    assert "chart-support-outlined" in html
    assert "Return on Average Equity" in html
    for roe in _ROE:
        assert roe in html
    assert 'gl-hero-value-num">58<' in html or ">58</span>" in html
    assert 'gl-hero-value-num">74<' in html or ">74</span>" in html
    assert "10.5" in html
    assert "CET1" in html
    # Detached left-panel KPIs must not reappear as right-panel labels.
    assert "Shares Outstanding" not in html.replace("Common Shares Outstanding", "")


def test_mismatched_line_cardinality_does_not_pad():
    slide = {**_corrected(), "layout_type": _COMBO}
    slide["visual_spec"] = copy.deepcopy(slide["visual_spec"])
    # Drop final share point — align-by-label leaves last category None.
    slide["visual_spec"]["line_overlay"]["data"] = slide["visual_spec"]["line_overlay"]["data"][:-1]
    cfg = _chartjs_combo_config(slide)
    assert cfg is not None
    line = next(d for d in cfg["data"]["datasets"] if d.get("type") == "line")
    assert line["data"][-1] is None
    assert line["data"][:5] == _SHARES[:5]


def test_mismatched_support_row_skips_alignment_without_crash():
    slide = copy.deepcopy(_corrected())
    slide["visual_spec"]["secondary_visual"]["steps_or_data"][1].pop()  # drop final ROE
    # Non-strict path: render must not raise; alignment is skipped.
    html = render_slide(slide, total=44, notes="", active=True, use_chartjs=False)
    assert "chart-support" in html
    # Cardinality mismatch → not plot-aligned.
    assert "chart-table-aligned" not in html or "chart-outlined-stacked" in html


def test_strict_outlined_support_with_matching_cardinality_aligns():
    slide = _corrected()
    html = render_slide(slide, total=44, notes="", active=True, use_chartjs=False)
    assert "chart-support-outlined" in html
    assert "chart-table-aligned" in html or "data-align-left" in html


def test_mutations_catch_dropped_line_support_totals_or_category():
    corrected = _corrected()

    def _must_fail(slide: dict) -> None:
        with pytest.raises((AssertionError, KeyError, IndexError)):
            _assert_semantics(slide)

    no_line = copy.deepcopy(corrected)
    no_line["visual_spec"].pop("line_overlay")
    _must_fail(no_line)

    no_support = copy.deepcopy(corrected)
    no_support["visual_spec"]["secondary_visual"]["steps_or_data"][1].pop()
    _must_fail(no_support)

    no_totals = copy.deepcopy(corrected)
    no_totals["visual_spec"]["primary_visual"]["chart_config"].pop("stack_total_labels")
    _must_fail(no_totals)

    drop_cat = copy.deepcopy(corrected)
    drop_cat["visual_spec"]["primary_visual"]["steps_or_data"].pop()
    _must_fail(drop_cat)

    # Detached KPI regression
    kpi_leak = copy.deepcopy(corrected)
    kpi_leak["content"]["key_stats"].append(
        {"label": "Shares Outstanding", "value": "682"}
    )
    _must_fail(kpi_leak)


def test_ordinary_combo_and_multi_panel_remain_compatible():
    """Absent new composition fields, existing surfaces stay unchanged."""
    ordinary = {
        "slide_number": 99,
        "layout_type": _COMBO,
        "title": "Ordinary combo",
        "content": {},
        "visual_spec": {
            "primary_visual": {
                "type": _COMBO,
                "steps_or_data": [
                    {"label": "A", "value": 1},
                    {"label": "B", "value": 2},
                ],
            },
            "line_overlay": {
                "label": "L",
                "data": [{"label": "A", "value": 10}, {"label": "B", "value": 20}],
            },
        },
    }
    cfg = _chartjs_combo_config(ordinary)
    assert cfg is not None
    # Single bar series → not stacked.
    assert "stacked" not in cfg["options"]["scales"].get("x", {})
    bar_ds = [d for d in cfg["data"]["datasets"] if d.get("type") == "bar"]
    assert len(bar_ds) == 1
    assert "stack" not in bar_ds[0]
    assert "datalabels" not in cfg["options"].get("plugins", {})

    multi = {
        "slide_number": 98,
        "layout_type": "multi_panel",
        "title": "Board",
        "content": {},
        "visual_spec": {
            "primary_visual": {
                "type": "multi_panel",
                "tiles": [
                    {
                        "kind": "chart",
                        "chart_type": "stacked_bar_chart",
                        "label": "Mix",
                        "steps_or_data": [
                            ["Q", "A", "B"],
                            ["Q1", "1", "2"],
                        ],
                        "chart_config": {},
                    },
                    {"kind": "metric", "label": "X", "value": "1"},
                ],
            }
        },
    }
    html = render_slide(multi, total=1, notes="", use_chartjs=False)
    assert "gl-multi-panel" in html or "gl-tile" in html


def test_1920x1080_line_bars_support_align_no_overlap(tmp_path: Path):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    from simulation_probe import painted_datalabel_lines, wait_for_paint_ready_charts

    fillers = [
        {
            "slide_number": n,
            "layout_type": "metric",
            "title": f"Pad {n}",
            "content": {"key_stats": [{"label": "n", "value": str(n)}]},
        }
        for n in range(2, 21)
    ]
    handoff = {
        "presentation": {"title": "Amex"},
        "slides": [
            {
                "slide_number": 1,
                "layout_type": "title_or_opening",
                "title": "Cover",
                "content": {"headline": "Cover"},
            },
            *fillers,
            _corrected(),
        ],
    }
    source = tmp_path / "handoff.json"
    source.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(source, out, strict=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto((out / "presentation.html").resolve().as_uri())
        wait_for_paint_ready_charts(page, 21, _HERO)
        page.wait_for_function(
            """() => {
              const slide = document.querySelector(
                'section.slide[data-slide-number="21"]'
              );
              const row = slide && slide.querySelector('.chart-support-outlined');
              const canvas = slide && slide.querySelector('canvas');
              const chart = canvas && Chart.getChart(canvas);
              if (!row || !chart) return false;
              const cells = [...row.querySelectorAll(
                '.chart-outlined-cell .chart-outlined-box'
              )];
              const barMeta = chart.getDatasetMeta(0);
              if (!barMeta || !barMeta.data || barMeta.data.length !== 6) return false;
              if (cells.length !== 6) return false;
              const lineMeta = chart.data.datasets.findIndex(d => d.type === 'line');
              if (lineMeta < 0) return false;
              const linePts = chart.getDatasetMeta(lineMeta).data || [];
              return linePts.filter(p => p && typeof p.x === 'number').length >= 6;
            }""",
            timeout=4000,
        )
        measured = page.evaluate(
            """() => {
              const slide = document.querySelector(
                'section.slide[data-slide-number="21"][data-layout="chart_hero_dual"]'
              );
              if (!slide) return {ok:false, reason:'identity missing'};
              slide.classList.add('active');
              const row = slide.querySelector('.chart-support-outlined');
              const label = row && row.querySelector('.chart-outlined-label');
              const cells = row && [...row.querySelectorAll('.chart-outlined-cell')];
              const canvas = slide.querySelector('canvas');
              const chart = canvas && Chart.getChart(canvas);
              if (!row || !label || !cells || cells.length !== 6 || !chart)
                return {ok:false, reason:'support or chart missing'};
              const labelBox = label.querySelector('.chart-outlined-box');
              const cellBoxes = cells.map(c => c.querySelector('.chart-outlined-box'));
              if (!labelBox || cellBoxes.some(b => !b))
                return {ok:false, reason:'boxes missing'};
              if (!labelBox.textContent.includes('Return on Average Equity'))
                return {ok:false, reason:'roe label missing'};
              const roe = cellBoxes.map(b => (b.textContent || '').trim());
              const canvasRect = canvas.getBoundingClientRect();
              const scale = canvasRect.width / chart.width;
              const barEls = chart.getDatasetMeta(0).data;
              if (barEls.length !== 6) return {ok:false, reason:'bar count'};
              const barCenters = barEls.map(el => canvasRect.left + el.x * scale);
              const barHeights = barEls.map((el, i) => {
                let h = 0;
                for (let di = 0; di < chart.data.datasets.length; di++) {
                  if (chart.data.datasets[di].type && chart.data.datasets[di].type !== 'bar') continue;
                  const pt = chart.getDatasetMeta(di).data[i];
                  if (!pt) continue;
                  const props = pt.getProps(['y', 'base'], true);
                  const base = props.base == null ? pt.base : props.base;
                  const y = props.y == null ? pt.y : props.y;
                  if (typeof base === 'number' && typeof y === 'number') h += Math.abs(base - y);
                }
                return h;
              });
              const lineIdx = chart.data.datasets.findIndex(d => d.type === 'line');
              const lineEls = chart.getDatasetMeta(lineIdx).data;
              const linePts = lineEls.filter(el => el && typeof el.x === 'number');
              if (linePts.length < 6) return {ok:false, reason:'line points'};
              // Degenerate geometry guards
              if (barHeights.some(h => !(h > 2))) return {ok:false, reason:'flat bars'};
              const lineYs = linePts.map(el => el.y);
              if (Math.max(...lineYs) - Math.min(...lineYs) < 2)
                return {ok:false, reason:'flat line'};
              const cr = cellBoxes.map(c => c.getBoundingClientRect());
              const lr = labelBox.getBoundingClientRect();
              const hero = [...slide.querySelectorAll('.gl-hero-value')]
                .map(el => (el.textContent || '').split(' ').join(''));
              return {
                ok: true,
                roe,
                labelRight: lr.right,
                firstLeft: cr[0].left,
                centers: cr.map(r => r.left + r.width / 2),
                barCenters,
                widths: cr.map(r => r.width),
                heights: cr.map(r => r.height),
                barHeights,
                lineCount: linePts.length,
                hero,
                heading: (slide.querySelector('.gl-chart-pane-title') || {}).textContent || '',
              };
            }"""
        )
        painted = painted_datalabel_lines(page, 21, _HERO)
        browser.close()

    assert measured["ok"], measured
    assert measured["roe"] == _ROE
    assert measured["lineCount"] >= 6
    assert measured["firstLeft"] >= measured["labelRight"] + 8 - 1  # 1px tol
    assert all(w > 0 and h > 0 for w, h in zip(measured["widths"], measured["heights"]))
    assert all(h > 2 for h in measured["barHeights"])
    assert all(
        abs(cell - bar) <= 4
        for cell, bar in zip(measured["centers"], measured["barCenters"])
    ), measured
    # Non-overlap between adjacent support cells
    centers = measured["centers"]
    widths = measured["widths"]
    for i in range(len(centers) - 1):
        right_i = centers[i] + widths[i] / 2
        left_j = centers[i + 1] - widths[i + 1] / 2
        assert right_i <= left_j + 1, (i, right_i, left_j)
    raw_lines = painted["lines"]
    # probe returns either flat strings or nested line groups
    if raw_lines and isinstance(raw_lines[0], (list, tuple)):
        painted_flat = [str(line) for group in raw_lines for line in group]
    else:
        painted_flat = [str(line) for line in raw_lines]
    assert set(_STACK_TOTALS).issubset(set(painted_flat)), painted
    hero_blob = " ".join(measured["hero"])
    assert "58" in hero_blob
    assert "74" in hero_blob
    assert "10.5" in hero_blob
    assert _PANE_HEADING in measured["heading"]
