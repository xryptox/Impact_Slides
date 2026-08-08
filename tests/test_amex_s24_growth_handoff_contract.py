"""#154 — restore Amex PDF page 24 customer-type growth chart.

Type (A) handoff correction: existing grouped bars, bar-group brackets, and
outlined aligned support row express the source composition without a renderer
change. Identity-safe browser evidence addresses slide 24 by number + layout.
"""

from __future__ import annotations

import copy
import html as html_module
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from amex_handoff_mutations import apply_issue_154_slide24_growth  # noqa: E402
from impact_slides.renderer_v2 import render_deck  # noqa: E402
from impact_slides.renderer_v2.charts.chartjs import _chartjs_bar_config  # noqa: E402
from impact_slides.renderer_v2.layout.dispatch import render_slide  # noqa: E402
from impact_slides.renderer_v2.schemas import validate_slide  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "renderer_v2"
BROKEN = FIXTURES / "amex_s24_v10_broken.json"

_GROUPED = "grouped_bar" + "_chart"
_TABLE = "data" + "_table"
_CATEGORIES = [
    "U.S. Consumer",
    "U.S. SME",
    "U.S. Large & Global Corp.",
    "Int'l Consumer",
    "Int'l SME & Large Corp.",
    "Processed Volumes",
]
_GROWTH = [10, 4, 4, 13, 12, 9]
_GROUPS = [
    ("U.S. Consumer Services", 0, 0),
    ("Commercial Services", 1, 2),
    ("International Card Services", 3, 4),
]
_SUPPORT = ["37%", "22%", "5%", "15%", "8%", "12%"]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _slide(handoff: dict) -> dict:
    return next(s for s in handoff["slides"] if int(s["slide_number"]) == 24)


def _corrected() -> dict:
    return _slide(apply_issue_154_slide24_growth(copy.deepcopy(_load(BROKEN))))


def _assert_semantics(slide: dict) -> None:
    assert slide["layout_type"] == _GROUPED
    visual = slide["visual_spec"]["primary_visual"]
    assert visual["type"] == _GROUPED
    steps = visual["steps_or_data"]
    assert [p["label"] for p in steps] == _CATEGORIES
    assert [p["value"] for p in steps] == _GROWTH
    assert [g["label"] for g in visual["chart_config"]["bar_groups"]] == [
        g[0] for g in _GROUPS
    ]
    assert [
        (g["start"], g["end"]) for g in visual["chart_config"]["bar_groups"]
    ] == [(g[1], g[2]) for g in _GROUPS]
    support = slide["visual_spec"]["secondary_visual"]
    assert support["skin"] == "outlined_boxes"
    assert support["steps_or_data"] == [
        ["", *_CATEGORIES],
        ["% of Total Network Volumes", *_SUPPORT],
    ]
    assert "$486B Total Network Volumes" in slide["content"]["subtitle"]
    assert slide["content"]["key_stats"] == []
    assert "FX-adjusted" in slide["content"]["subtitle"]
    assert "9%" in slide["content"]["subtitle"]
    assert "Processed Volumes 12%" in slide["speaker_notes"]
    assert slide["disclosure"]["title"] == "FX-adjusted reporting note"
    assert slide["disclosure"]["default_open"] is True
    assert "See Annex 1 for reported rates" in slide["disclosure"]["body"]


def test_broken_fixture_still_documents_the_data_table_defect():
    broken = _slide(_load(BROKEN))
    assert broken["layout_type"] == _TABLE
    assert broken["visual_spec"]["primary_visual"]["type"] == _TABLE


def test_mutation_restores_source_semantics_and_is_idempotent():
    once = _corrected()
    _assert_semantics(once)
    twice = _slide(
        apply_issue_154_slide24_growth(
            {"slides": [copy.deepcopy(once)]}
        )
    )
    assert twice == once


@pytest.mark.parametrize("use_chartjs", [True, False], ids=["chartjs", "svg"])
def test_render_paints_exactly_six_growth_bars_and_support_context(use_chartjs: bool):
    slide = _corrected()
    model, err = validate_slide(slide)
    assert model is not None, err
    html = render_slide(slide, total=44, notes="", active=True, use_chartjs=use_chartjs)

    assert 'data-slide-number="24"' in html
    assert f'data-layout="{_GROUPED}"' in html
    assert _TABLE not in html
    painted = html_module.unescape(html)
    for token in [
        *_CATEGORIES,
        *_SUPPORT,
        "$486B Total Network Volumes",
        "9% FX-adjusted growth",
        "FX-adjusted reporting note",
        "See Annex 1 for reported rates",
    ]:
        assert token in painted
    assert '<details open>' in html
    assert "chart-support-outlined chart-table-aligned" in html
    assert 'data-rv2-chart-table-align="1"' in html

    if use_chartjs:
        config = _chartjs_bar_config(slide)
        assert config is not None
        assert config["options"]["plugins"]["barGroups"]["items"] == [
            {"label": name, "start": start, "end": end}
            for name, start, end in _GROUPS
        ]
        assert '"type": "bar"' in html or '"type":"bar"' in html
        assert '"data": [10.0, 4.0, 4.0, 13.0, 12.0, 9.0]' in html
    else:
        for name, _, _ in _GROUPS:
            assert html.count(name) == 1
        assert html.count("bar-group-bracket") == 3
        assert html.count('class="vbar"') == 6


def test_chartjs_bar_groups_are_opt_in():
    configured = _chartjs_bar_config(_corrected())
    assert configured is not None
    assert configured["options"]["layout"]["padding"]["top"] >= 28

    malformed = _corrected()
    malformed["visual_spec"]["primary_visual"]["chart_config"]["bar_groups"] = [
        {"label": "bad", "start": "nope", "end": 2}
    ]
    ignored = _chartjs_bar_config(malformed)
    assert ignored is not None
    assert "barGroups" not in ignored["options"]["plugins"]

    without_groups = _corrected()
    without_groups["visual_spec"]["primary_visual"]["chart_config"].pop("bar_groups")
    default = _chartjs_bar_config(without_groups)
    assert default is not None
    assert "barGroups" not in default["options"]["plugins"]
    assert "layout" not in default["options"]


def test_mutations_catch_data_table_missing_context_and_aggregate_bars():
    corrected = _corrected()

    data_table = copy.deepcopy(corrected)
    data_table["layout_type"] = _TABLE
    data_table["visual_spec"]["primary_visual"]["type"] = _TABLE
    with pytest.raises(AssertionError):
        _assert_semantics(data_table)

    missing_support = copy.deepcopy(corrected)
    missing_support["visual_spec"]["secondary_visual"]["steps_or_data"][1].pop()
    with pytest.raises(AssertionError):
        _assert_semantics(missing_support)

    aggregate_bar = copy.deepcopy(corrected)
    aggregate_bar["visual_spec"]["primary_visual"]["steps_or_data"].insert(
        1, {"label": "Commercial Services", "value": 4}
    )
    with pytest.raises(AssertionError):
        _assert_semantics(aggregate_bar)


def test_1920x1080_support_cells_align_and_do_not_overlap_label_lane(tmp_path: Path):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright
    from simulation_probe import wait_for_paint_ready_charts

    fillers = [
        {
            "slide_number": n,
            "layout_type": "metric",
            "title": f"Pad {n}",
            "content": {"key_stats": [{"label": "n", "value": str(n)}]},
        }
        for n in range(2, 24)
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
        wait_for_paint_ready_charts(page, 24, _GROUPED)
        page.wait_for_function(
            """() => {
              const slide = document.querySelector('section.slide[data-slide-number="24"]');
              const row = slide && slide.querySelector('.chart-support-outlined');
              const canvas = slide && slide.querySelector('canvas');
              const chart = canvas && Chart.getChart(canvas);
              const groups = chart && chart.options.plugins && chart.options.plugins.barGroups;
              const labels = groups && groups.items && groups.items.map(group => group.label).join('|');
              if (!row || !chart || !groups || labels !== 'U.S. Consumer Services|Commercial Services|International Card Services' || canvas.dataset.rv2BarGroupsPainted !== '3') return false;
              const cells = [...row.querySelectorAll('.chart-outlined-cell .chart-outlined-box')];
              const canvasRect = canvas.getBoundingClientRect();
              const scale = canvasRect.width / chart.width;
              return cells.length === 6 && cells.every((cell, i) => {
                const rect = cell.getBoundingClientRect();
                return Math.abs(rect.left + rect.width / 2 - (
                  canvasRect.left + chart.getDatasetMeta(0).data[i].x * scale
                )) <= 4;
              });
            }""",
            timeout=2000,
        )
        measured = page.evaluate(
            """() => {
              const slide = document.querySelector(
                'section.slide[data-slide-number="24"][data-layout="grouped_bar_chart"]'
              );
              if (!slide) return {ok:false, reason:'identity missing'};
              slide.classList.add('active');
              const bars = [...slide.querySelectorAll('canvas')];
              const row = slide.querySelector('.chart-support-outlined');
              const label = row && row.querySelector('.chart-outlined-label');
              const cells = row && [...row.querySelectorAll('.chart-outlined-cell')];
              if (!row || !label || !cells || cells.length !== 6)
                return {ok:false, reason:'support row missing'};
              const labelBox = label.querySelector('.chart-outlined-box');
              const cellBoxes = cells.map(c => c.querySelector('.chart-outlined-box'));
              const canvas = slide.querySelector('canvas');
              const chart = canvas && Chart.getChart(canvas);
              const groups = chart && chart.options.plugins && chart.options.plugins.barGroups;
              if (!labelBox || cellBoxes.some(b => !b) || !chart || !chart.scales.x ||
                  !groups || groups.items.length !== 3 ||
                  canvas.dataset.rv2BarGroupsPainted !== '3')
                return {ok:false, reason:'support row, chart, or group brackets missing'};
              const lr = labelBox.getBoundingClientRect();
              const cr = cellBoxes.map(c => c.getBoundingClientRect());
              const canvasRect = canvas.getBoundingClientRect();
              const scale = canvasRect.width / chart.width;
              const elements = chart.getDatasetMeta(0).data;
              if (elements.length !== 6) return {ok:false, reason:'bar count'};
              const barCenters = elements.map(el => canvasRect.left + el.x * scale);
              return {ok:true, labelRight:lr.right, firstLeft:cr[0].left,
                groupLabels: groups.items.map(group => group.label),
                paintedGroups: canvas.dataset.rv2BarGroupsPainted,
                centers:cr.map(r => r.left + r.width / 2), barCenters,
                widths:cr.map(r => r.width)};
            }"""
        )
        browser.close()

    assert measured["ok"], measured
    assert measured["firstLeft"] >= measured["labelRight"] + 8
    assert measured["groupLabels"] == [group[0] for group in _GROUPS]
    assert measured["paintedGroups"] == "3"
    assert measured["centers"] == sorted(measured["centers"])
    assert all(width > 0 for width in measured["widths"])
    assert all(
        abs(cell - bar) <= 4
        for cell, bar in zip(measured["centers"], measured["barCenters"])
    ), measured
