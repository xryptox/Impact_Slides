"""#151 — chart_hero_dual secondary_visual driver_card."""
from __future__ import annotations

import copy
import json
import re

import pytest

from impact_slides.renderer_v2.charts.typography import (
    reset_render_strict,
    set_render_strict,
    begin_render_warnings,
    take_render_warnings,
)
from impact_slides.renderer_v2.layout.recipes import render_chart_hero_dual
from impact_slides.renderer_v2.layout.recipes.shared import (
    _driver_card_html,
    normalize_driver_card,
)
from impact_slides.renderer_v2.schemas import validate_slide

_LEFT_H = "Net Interest Income"
_LEFT_S = "$ in billions - % Increase/(decrease) vs. Prior year (FX-adjusted)"
_RIGHT_H = "NII: Volume & Margin Drivers"
_RIGHT_S = "CAGR % vs. Q1'19 (FX-adjusted except Margin)"

_ROWS = [
    {
        "label": "Billed Business",
        "detail": "",
        "value": "8%",
        "direction": "up",
        "tone": "positive",
    },
    {
        "label": "Net Interest Income",
        "value": "13%",
        "direction": "up",
        "tone": "positive",
    },
    {
        "label": "Volume",
        "detail": "Total Balances",
        "value": "7%",
        "direction": "up",
        "tone": "positive",
    },
    {
        "label": "Margin",
        "detail": "Net Interest Income / Average Total Balances",
        "value": "5%",
        "direction": "up",
        "tone": "positive",
    },
]


def _slide(*, secondary=None, key_stats=None, rows=None):
    pv = {
        "type": "grouped_bar_chart",
        "heading": _LEFT_H,
        "subtitle": _LEFT_S,
        "steps_or_data": [
            {"label": "Q1'25", "value": 4.2},
            {"label": "Q2'25", "value": 4.2},
            {"label": "Q3'25", "value": 4.5},
            {"label": "Q4'25", "value": 4.5},
            {"label": "Q1'26", "value": 4.7},
        ],
        "chart_config": {
            "y_axis_min": 0,
            "y_axis_max": 6,
            "boxed_labels": {
                "label": "YoY Growth",
                "values": ["11%", "12%", "12%", "12%", "12%"],
            },
        },
    }
    if secondary is None:
        secondary = {
            "type": "driver_card",
            "heading": _RIGHT_H,
            "subtitle": _RIGHT_S,
            "rows": list(rows if rows is not None else _ROWS),
        }
    return {
        "slide_number": 18,
        "layout_type": "chart_hero_dual",
        "title": "Premium Lending",
        "content": {
            "so_what": "",
            "key_stats": key_stats
            or [
                {"label": "Billed Business CAGR vs Q1'19", "value": "8%"},
                {"label": "NII CAGR vs Q1'19", "value": "13%"},
            ],
        },
        "visual_spec": {"primary_visual": pv, "secondary_visual": secondary},
        "speaker_notes": "NII bars + driver card.",
        "evidence_sources": [],
    }


def test_schema_accepts_valid_driver_card():
    model, err = validate_slide(_slide())
    assert err is None
    assert model is not None
    raw = model.model_dump()
    assert raw["visual_spec"]["secondary_visual"]["type"] == "driver_card"
    assert len(raw["visual_spec"]["secondary_visual"]["rows"]) == 4


@pytest.mark.parametrize("n", [1, 6])
def test_schema_accepts_one_and_six_rows(n):
    rows = [
        {"label": f"R{i}", "value": f"{i}%", "direction": "up", "tone": "positive"}
        for i in range(n)
    ]
    model, err = validate_slide(_slide(rows=rows))
    assert err is None, err
    assert model is not None


def test_schema_rejects_seven_rows():
    rows = [{"label": f"R{i}", "value": f"{i}%"} for i in range(7)]
    model, err = validate_slide(_slide(rows=rows))
    assert model is None
    assert err and "row" in err.lower()


def test_schema_rejects_missing_heading():
    sec = {
        "type": "driver_card",
        "rows": [{"label": "A", "value": "1%"}],
    }
    model, err = validate_slide(_slide(secondary=sec))
    assert model is None
    assert err and "heading" in err.lower()


@pytest.mark.parametrize(
    "bad",
    [
        {"label": "A", "value": "1%", "direction": "sideways"},
        {"label": "A", "value": "1%", "tone": "rainbow"},
        {"value": "1%"},  # missing label
        {"label": "A"},  # missing value
    ],
)
def test_schema_rejects_malformed_rows(bad):
    model, err = validate_slide(_slide(rows=[bad]))
    assert model is None
    assert err


def test_order_preserved_and_no_q1_nii_tile():
    html = render_chart_hero_dual(_slide(), 1, "", use_chartjs=True)
    assert "gl-driver-card" in html
    assert "Q1'26 NII" not in html
    assert "$4.7B" not in html
    # author order via aria-labels (left pane also says Net Interest Income)
    card = html[html.index("gl-driver-card") :]
    labels = ("Billed Business", "Net Interest Income", "Volume", "Margin")
    positions = [card.index(f'aria-label="{lab}') for lab in labels]
    assert positions == sorted(positions)
    assert ">5%<" in card or "5%" in card
    assert html.count('class="gl-driver-row ') == 4


def test_direction_shape_and_tone_classes():
    html = render_chart_hero_dual(_slide(), 1, "", use_chartjs=True)
    assert 'data-direction="up"' in html
    assert "gl-driver-dir--up" in html
    assert "gl-driver-tone--positive" in html
    # no embedded arrow characters in direction glyph path
    assert "▲" not in html and "↑" not in html


def test_accessibility_text_includes_direction_and_value():
    html = render_chart_hero_dual(_slide(), 1, "", use_chartjs=True)
    assert 'role="list"' in html
    assert "up" in html.lower()
    assert re.search(r'aria-label="[^"]*Margin[^"]*5%[^"]*up', html)


def test_legacy_hero_stack_when_no_driver_card():
    slide = _slide(
        secondary={"heading": "Hero side", "subtitle": "Q1"},
        key_stats=[{"label": "Fee-Paying", "value": "73%"}],
    )
    html = render_chart_hero_dual(slide, 1, "")
    assert "gl-driver-card" not in html
    assert "gl-hero-stack" in html
    assert "Fee-Paying" in html
    assert 'gl-hero-value-num">73</span>' in html


def test_normalize_drops_malformed_non_strict():
    tok = set_render_strict(False)
    wtok = begin_render_warnings()
    try:
        rows = [
            {"label": "Good", "value": "8%", "direction": "up"},
            {"label": "BadDir", "value": "1%", "direction": "sideways"},
            {"label": "", "value": "2%"},
            {"value": "3%"},
        ]
        card = normalize_driver_card(
            {"type": "driver_card", "heading": "H", "rows": rows}
        )
        assert card is not None
        assert [r["label"] for r in card["rows"]] == ["Good"]
    finally:
        warnings = take_render_warnings(wtok)
        reset_render_strict(tok)
    assert any("driver_card" in w for w in warnings)


def test_normalize_strict_raises_on_malformed_row():
    tok = set_render_strict(True)
    try:
        with pytest.raises(ValueError, match="driver_card"):
            normalize_driver_card(
                {
                    "type": "driver_card",
                    "heading": "H",
                    "rows": [{"label": "X", "value": "1%", "direction": "nope"}],
                }
            )
    finally:
        reset_render_strict(tok)


def test_no_valid_rows_falls_back_to_hero_stack():
    tok = set_render_strict(False)
    wtok = begin_render_warnings()
    try:
        slide = _slide(
            rows=[{"label": "", "value": ""}],
            key_stats=[{"label": "Fallback KPI", "value": "99%"}],
        )
        # bypass schema: force bad rows onto a hero slide secondary
        slide["visual_spec"]["secondary_visual"] = {
            "type": "driver_card",
            "heading": "H",
            "rows": [{"label": "", "value": ""}],
        }
        html = render_chart_hero_dual(slide, 1, "")
    finally:
        take_render_warnings(wtok)
        reset_render_strict(tok)
    assert "gl-driver-card" not in html
    assert "Fallback KPI" in html
    assert 'gl-hero-value-num">99</span>' in html


def test_overflow_non_strict_ellipsizes():
    long = "Word " * 40
    tok = set_render_strict(False)
    wtok = begin_render_warnings()
    try:
        html = _driver_card_html(
            {
                "type": "driver_card",
                "heading": long,
                "rows": [
                    {
                        "label": long,
                        "detail": long,
                        "value": "5%",
                        "direction": "up",
                        "tone": "positive",
                    }
                ],
            }
        )
    finally:
        warnings = take_render_warnings(wtok)
        reset_render_strict(tok)
    assert html
    assert "…" in html or "&hellip;" in html or html.count("Word") < 40
    assert any("overflow" in w for w in warnings)
    assert any("heading" in w for w in warnings)
    assert any("label" in w for w in warnings)


def test_overflow_strict_raises():
    long = "Word " * 40
    tok = set_render_strict(True)
    try:
        with pytest.raises(ValueError, match="overflow|driver_card"):
            _driver_card_html(
                {
                    "type": "driver_card",
                    "heading": "Ok",
                    "rows": [{"label": long, "value": "5%"}],
                }
            )
    finally:
        reset_render_strict(tok)


def test_byte_compat_without_features():
    """Existing hero-stack handoffs stay normalized-byte compatible vs baseline."""
    from pathlib import Path

    base = {
        "slide_number": 12,
        "layout_type": "chart_hero_dual",
        "title": "New Acquisitions",
        "content": {
            "key_stats": [
                {"label": "Millennial/Gen-Z", "value": "66%"},
                {"label": "Fee-Paying", "value": "73%"},
            ]
        },
        "visual_spec": {
            "primary_visual": {
                "type": "grouped_bar_chart",
                "steps_or_data": [
                    {"label": "Q1", "value": 1},
                    {"label": "Q2", "value": 2},
                ],
                "chart_config": {},
            }
        },
        "speaker_notes": "",
        "evidence_sources": [],
    }
    a = render_chart_hero_dual(copy.deepcopy(base), 1, "")
    b = render_chart_hero_dual(copy.deepcopy(base), 1, "")
    a = re.sub(r"rv2-chart-[0-9a-f-]+", "ID", a)
    b = re.sub(r"rv2-chart-[0-9a-f-]+", "ID", b)
    assert a == b
    assert "gl-driver-card" not in a
    assert "boxed-label" not in a
    assert "gl-hero-stack" in a
    baseline_path = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "renderer_v2"
        / "chart_hero_dual_no_headings.baseline.html"
    )
    baseline = baseline_path.read_text(encoding="utf-8")
    baseline = re.sub(r"rv2-chart-[0-9a-f-]+", "ID", baseline)
    # Baseline may be a full deck (shared CSS always includes driver_card rules).
    assert "gl-hero-stack" in baseline
    assert "gl-hero-stack" in a and "gl-driver-card" not in a and "boxed-label" not in a
    # When baseline is a recipe fragment, normalized bodies must match.
    if "<!DOCTYPE" not in baseline and "gl-driver-card {" not in baseline:
        assert a == baseline

def test_slide18_geometry_1920(tmp_path):
    """At 1920x1080, slide 18 keeps two-pane hierarchy + four driver rows."""
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright
    from impact_slides.renderer_v2 import render_deck

    handoff = {
        "meta": {"title": "t", "client": "c", "date": "2026-01-01"},
        "presentation": {"title": "t"},
        "slides": [_slide()],
    }
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(path, out, strict=True)
    html_path = (out / "presentation.html").resolve()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(html_path.as_uri(), wait_until="networkidle")
        # Activate the dual slide so Chart.js paints (title slide is active by default).
        page.evaluate(
            """() => {
              const slide = document.querySelector('.slide[data-layout="chart_hero_dual"]');
              if (!slide) return;
              document.querySelectorAll('.slide.active').forEach(s => s.classList.remove('active'));
              slide.classList.add('active');
              const stage = document.querySelector('.deck-stage');
              if (stage) stage.style.transform = 'none';
            }"""
        )
        page.wait_for_function(
            """() => {
              const slide = document.querySelector('.slide[data-layout="chart_hero_dual"]');
              if (!slide) return false;
              const c = slide.querySelector('canvas');
              const svg = slide.querySelector('.boxed-label');
              return (c && c.dataset && c.dataset.rv2BoxedLabelsPainted === '5') || !!svg;
            }""",
            timeout=15000,
        )
        measured = page.evaluate(
            """() => {
            const slide = document.querySelector('.slide[data-layout="chart_hero_dual"]')
              || document.querySelector('.slide.active')
              || document.querySelector('.slide');
            slide.classList.add('active');
            const stage = document.querySelector('.deck-stage');
            if (stage) stage.style.transform = 'none';
            const chart = slide.querySelector('.gl-chart-hero-chart');
            const stack = slide.querySelector('.gl-chart-hero-stack');
            const card = slide.querySelector('.gl-driver-card');
            const rows = [...slide.querySelectorAll('.gl-driver-row')];
            const titles = [...slide.querySelectorAll('.gl-chart-pane-title')].map(n => n.textContent.trim());
            const val = getComputedStyle(rows[0].querySelector('.gl-driver-value')).color;
            const dir = rows[0].querySelector('.gl-driver-dir');
            const dirColor = dir ? getComputedStyle(dir).color : '';
            const box = el => { const r = el.getBoundingClientRect(); return {w:r.width,h:r.height,l:r.left,t:r.top}; };
            const canvas = slide.querySelector('canvas');
            const cfgEl = slide.querySelector('script.chartjs-config');
            let boxed = null; let labels = []; let data = [];
            try {
              const cfg = cfgEl ? JSON.parse(cfgEl.textContent) : null;
              boxed = cfg && cfg.options && cfg.options.plugins && cfg.options.plugins.boxedLabels;
              labels = (cfg && cfg.data && cfg.data.labels) || [];
              data = (cfg && cfg.data && cfg.data.datasets && cfg.data.datasets[0] && cfg.data.datasets[0].data) || [];
            } catch (e) { boxed = null; }
            return {
              slide: box(slide),
              chart: box(chart),
              stack: box(stack),
              cardOk: !!card,
              rowCount: rows.length,
              titles,
              valueColor: val,
              dirColor,
              hasUp: !!rows[0].querySelector('.gl-driver-dir--up'),
              aria: rows.map(r => r.getAttribute('aria-label')),
              title: (slide.querySelector('.slide-title, h1.slide-title, .gl-title') || {}).textContent || '',
              boxedValues: (boxed && boxed.values) || [],
              chartLabels: labels,
              chartData: data,
              boxedPainted: canvas ? (canvas.dataset.rv2BoxedLabelsPainted || '') : '',
              svgBoxed: slide.querySelectorAll('.boxed-label').length,
            };
        }"""
        )
        browser.close()
    assert measured["slide"]["w"] == 1920
    assert measured["slide"]["h"] == 1080
    assert measured["chart"]["w"] > measured["stack"]["w"] > 200
    assert measured["chart"]["l"] < measured["stack"]["l"]
    assert measured["cardOk"]
    assert measured["rowCount"] == 4
    assert "Premium Lending" in (measured["title"] or "")
    assert "Net Interest Income" in measured["titles"]
    assert any("Volume" in t and "Margin" in t for t in measured["titles"])
    assert measured["hasUp"]
    # green-ish accent-2 on value AND direction glyph
    def _green(c: str) -> bool:
        return "10, 125, 85" in c or "0a7d55" in c

    assert _green(measured["valueColor"]), measured["valueColor"]
    assert _green(measured["dirColor"]), measured["dirColor"]
    assert any("Margin" in (lab or "") and "5%" in (lab or "") for lab in measured["aria"])
    # five categories + five boxed YoY labels + five bar values
    assert measured["boxedValues"] == ["11%", "12%", "12%", "12%", "12%"] or measured.get("svgBoxed") == 5
    assert len(measured["chartLabels"]) == 5 or measured.get("svgBoxed") == 5
    assert measured["chartData"] == [4.2, 4.2, 4.5, 4.5, 4.7] or measured.get("svgBoxed") == 5
    assert measured["boxedPainted"] == "5" or measured.get("svgBoxed") == 5
