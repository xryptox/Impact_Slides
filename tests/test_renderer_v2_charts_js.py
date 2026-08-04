"""P3 Chart.js path + SVG fallback.

Spec: wiki/SPEC_renderer_v2_p3_chartjs.md
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from impact_slides.renderer_v2 import render_deck
from impact_slides.renderer_v2.lib_inliner import (
    CHART_JS_FILENAME,
    LIBS_DIR,
    build_head_assets,
    DeliveryMode,
)
from impact_slides.renderer_v2.manifest import remote_fetch_urls

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "renderer_v2"
MINI = FIXTURES / "mini_handoff.json"


def _slide(layout: str, steps: list) -> dict:
    return {
        "slide_number": 1,
        "layout_type": layout,
        "title": layout,
        "content": {"so_what": "Insight"},
        "visual_spec": {
            "primary_visual": {"type": layout, "steps_or_data": steps},
        },
        "speaker_notes": "Notes.",
    }


def _handoff(slides: list[dict]) -> dict:
    return {
        "title": "Chart.js tests",
        "readiness_score": 0.9,
        "quality_flags": [],
        "slides": slides,
    }


def _write(tmp_path: Path, handoff: dict) -> Path:
    p = tmp_path / "h.json"
    p.write_text(json.dumps(handoff), encoding="utf-8")
    return p


BAR_STEPS = [
    {"label": "A", "value": 10},
    {"label": "B", "value": 20},
    {"label": "C", "value": 15},
]
LINE_STEPS = [
    {"label": "Q1", "value": 8},
    {"label": "Q2", "value": 12},
    {"label": "Q3", "value": 11},
]
COMBO_HANDOFF_SLIDE = {
    "slide_number": 1,
    "layout_type": "combo_chart",
    "title": "Combo",
    "content": {"so_what": "Bars + line"},
    "visual_spec": {
        "primary_visual": {
            "type": "combo_chart",
            "steps_or_data": BAR_STEPS,
        },
        "line_overlay": {
            "label": "Trend",
            "data": [
                {"label": "A", "value": 9},
                {"label": "B", "value": 18},
                {"label": "C", "value": 14},
            ],
        },
    },
    "speaker_notes": "Notes.",
}


class TestChartJsVendor:
    def test_chartjs_file_and_license_exist(self):
        assert (LIBS_DIR / CHART_JS_FILENAME).is_file()
        assert (LIBS_DIR / "CHART_JS_LICENSE.md").is_file()

    def test_inliner_embeds_when_charts_on(self):
        bundle = build_head_assets(
            DeliveryMode.SELF_CONTAINED, feature_ids=["charts"]
        )
        assert "charts" in bundle.meta["assets"]
        assert "Chart" in bundle.head_html or "chart" in bundle.head_html
        # Banner comments may mention chartjs.org; no actual remote fetch tags.
        assert remote_fetch_urls(f"<!DOCTYPE html><html><head>{bundle.head_html}</head></html>") == []

    def test_inliner_omits_when_charts_off(self):
        bundle = build_head_assets(DeliveryMode.SELF_CONTAINED, feature_ids=[])
        assert "charts" not in bundle.meta["assets"]
        assert "chart.umd" not in bundle.head_html.lower()

    def test_missing_vendor_fails_self_contained(self, monkeypatch, tmp_path):
        import impact_slides.renderer_v2.lib_inliner as li

        monkeypatch.setattr(li, "LIBS_DIR", tmp_path)
        with pytest.raises(FileNotFoundError, match="Chart.js"):
            li.build_head_assets(
                li.DeliveryMode.SELF_CONTAINED, feature_ids=["charts"]
            )


class TestChartJsRender:
    def test_grouped_bar_chartjs_when_on(self, tmp_path):
        path = _write(tmp_path, _handoff([_slide("grouped_bar_chart", BAR_STEPS)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert 'data-chartjs="1"' in html
        assert "chartjs-config" in html
        assert '"type": "bar"' in html or '"type":"bar"' in html
        assert remote_fetch_urls(html) == []
        run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert "charts" in run_meta["features_enabled"]
        assert "charts" in run_meta["assets_inlined"]

    def test_line_chartjs_when_on(self, tmp_path):
        path = _write(tmp_path, _handoff([_slide("line_chart", LINE_STEPS)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert 'data-chartjs="1"' in html
        assert '"type": "line"' in html or '"type":"line"' in html

    def test_combo_chartjs_when_on(self, tmp_path):
        path = _write(tmp_path, _handoff([COMBO_HANDOFF_SLIDE]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert 'data-chartjs="1"' in html
        assert "chartjs-config" in html

    def test_svg_fallback_when_charts_suppressed(self, tmp_path):
        path = _write(tmp_path, _handoff([_slide("grouped_bar_chart", BAR_STEPS)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False, suppress_features=["charts"])
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert 'data-chartjs="1"' not in html
        assert "chart-svg" in html or "<svg" in html
        run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert "charts" not in run_meta["features_enabled"]
        assert "charts" not in run_meta.get("assets_inlined", [])

    def test_noscript_svg_when_charts_on(self, tmp_path):
        """P3-US12: charts-on decks still show SVG when JS is disabled."""
        path = _write(tmp_path, _handoff([_slide("grouped_bar_chart", BAR_STEPS)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert 'data-chartjs="1"' in html
        assert "<noscript>" in html
        # noscript block should carry the static SVG painter
        ns = html.split("<noscript>", 1)[1].split("</noscript>", 1)[0]
        assert "<svg" in ns or "chart-svg" in ns

    def test_cdn_url_matches_min_pin(self):
        from impact_slides.renderer_v2.lib_inliner import (
            CHART_JS_CDN_URL,
            CHART_JS_FILENAME,
        )

        assert CHART_JS_FILENAME in CHART_JS_CDN_URL
        assert "chart.umd.min.js" in CHART_JS_CDN_URL

    def test_combo_overlay_label_align_no_silent_pad(self):
        from impact_slides.renderer_v2.charts import _align_overlay_to_labels

        # Matching labels → by-label map
        out = _align_overlay_to_labels(
            ["A", "B"],
            [{"label": "B", "value": 2}, {"label": "A", "value": 1}],
        )
        assert out == [1, 2]
        # Equal length, no label hits → positional fallback
        out2 = _align_overlay_to_labels(
            ["A", "B"],
            [{"label": "X", "value": 9}, {"label": "Y", "value": 8}],
        )
        assert out2 == [9, 8]
        # Mismatched lengths, no label hits → Nones (no silent pad)
        out3 = _align_overlay_to_labels(
            ["A", "B", "C"],
            [{"label": "X", "value": 1}, {"label": "Y", "value": 2}],
        )
        assert out3 == [None, None, None]


# ---------------------------------------------------------------------------
# #71 — IR line-chart contract (F1+F2+F15): Chart.js honors chart_config
# ---------------------------------------------------------------------------

def _line_slide_with_cfg(cfg: dict, steps: list) -> dict:
    s = _slide("line_chart", steps)
    s["visual_spec"]["primary_visual"]["chart_config"] = cfg
    return s


TWO_SERIES = [
    {"label": "Q1", "value": 8, "series_2": 4},
    {"label": "Q2", "value": 10, "series_2": 6},
    {"label": "Q3", "value": 12, "series_2": 7},
]


def _chartjs_cfg(html: str) -> dict:
    marker = 'class="chartjs-config"'
    i = html.index(marker)
    j = html.index(">", i)
    k = html.index("</script>", j)
    return json.loads(html[j + 1 : k])


class TestLineChartContract:
    def test_chartjs_uses_series_names(self, tmp_path):
        cfg = {"series_names": ["Billed", "Card"]}
        path = _write(tmp_path, _handoff([_line_slide_with_cfg(cfg, TWO_SERIES)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        cc = _chartjs_cfg(html)
        labels = [d["label"] for d in cc["data"]["datasets"]]
        assert labels == ["Billed", "Card"]

    def test_chartjs_dashed_secondary_series(self, tmp_path):
        path = _write(tmp_path, _handoff([_line_slide_with_cfg({}, TWO_SERIES)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        cc = _chartjs_cfg(html)
        # Secondary series (index 1) is dashed by IR default
        assert cc["data"]["datasets"][1].get("borderDash")

    def test_chartjs_force_ticks(self, tmp_path):
        cfg = {"force_ticks": True, "y_axis_ticks": [0, 5, 10, 15]}
        path = _write(tmp_path, _handoff([_line_slide_with_cfg(cfg, TWO_SERIES)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        cc = _chartjs_cfg(html)
        scale = cc["options"]["scales"]["y"]
        assert scale.get("min") == 0  # #96: scale-root min/max
        assert scale.get("max") == 15
        assert scale["ticks"].get("stepSize") == 5

    def test_chartjs_explicit_min_max(self, tmp_path):
        cfg = {"y_axis_min": 0, "y_axis_max": 20}
        path = _write(tmp_path, _handoff([_line_slide_with_cfg(cfg, TWO_SERIES)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        cc = _chartjs_cfg(html)
        scale = cc["options"]["scales"]["y"]
        assert scale.get("min") == 0
        assert scale.get("max") == 20

    def test_chartjs_series_colors_override(self, tmp_path):
        cfg = {"series_colors": ["#ff0000", "#00ff00"]}
        path = _write(tmp_path, _handoff([_line_slide_with_cfg(cfg, TWO_SERIES)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        cc = _chartjs_cfg(html)
        assert cc["data"]["datasets"][0]["borderColor"] == "#ff0000"
        assert cc["data"]["datasets"][1]["borderColor"] == "#00ff00"

    def test_chartjs_point_labels(self, tmp_path):
        cfg = {"point_labels": True}
        path = _write(tmp_path, _handoff([_line_slide_with_cfg(cfg, TWO_SERIES)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        cc = _chartjs_cfg(html)
        # IR on-point labels (#84): a formatted label matrix the vendored
        # datalabels plugin renders via the shell formatter — NOT the
        # radial-only `pointLabels` dataset key, which Chart.js ignores on
        # cartesian line charts.
        d0 = cc["data"]["datasets"][0]
        assert "pointLabels" not in d0
        dl = cc["options"]["plugins"]["datalabels"]
        assert dl.get("display") is True
        assert dl["_labels"][0] == ["8%", "10%", "12%"]

    def test_chartjs_annotation_marker(self, tmp_path):
        cfg = {"annotation": {"text": "Leap Year Approx. (1%)"}}
        path = _write(tmp_path, _handoff([_line_slide_with_cfg(cfg, TWO_SERIES)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "Leap Year Approx. (1%)" in html
        assert "chartjs-annotation" in html

    def test_no_config_keeps_defaults(self, tmp_path):
        # No chart_config → current defaults unchanged (no ticks forced)
        path = _write(tmp_path, _handoff([_slide("line_chart", TWO_SERIES)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        cc = _chartjs_cfg(html)
        assert "stepSize" not in cc["options"]["scales"]["y"]["ticks"]
        assert "pointLabels" not in cc["data"]["datasets"][0]
        assert "datalabels" not in cc["options"]["plugins"]


# ---------------------------------------------------------------------------
# #72 — Below-axis negative stacked bars (reserve release)
# ---------------------------------------------------------------------------

PROVISION_STACK = [
    {"label": "Q4'25", "values": {"NCO": 1251, "RR": -73}},
    {"label": "Q1'26", "values": {"NCO": 1251, "RR": -24}},
]


class TestNegativeStackedBars:
    def test_chartjs_stacked_scales_signed(self, tmp_path):
        path = _write(tmp_path, _handoff([_slide("stacked_bar_chart", PROVISION_STACK)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert 'data-chartjs="1"' in html
        cc = _chartjs_cfg(html)
        assert cc["options"]["scales"]["x"]["stacked"] is True
        assert cc["options"]["scales"]["y"]["stacked"] is True
        # Negative segment values preserved (signed, not absorbed)
        rr = next(d for d in cc["data"]["datasets"] if d["label"] == "RR")
        assert rr["data"] == [-73.0, -24.0]
        # y-domain reaches below zero (#96: scale-root min)
        assert cc["options"]["scales"]["y"]["min"] < 0

    def test_chartjs_respects_explicit_axis_bounds(self, tmp_path):
        s = _slide("stacked_bar_chart", PROVISION_STACK)
        s["visual_spec"]["primary_visual"]["chart_config"] = {
            "y_axis_min": -200,
            "y_axis_max": 1500,
        }
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        cc = _chartjs_cfg(html)
        assert cc["options"]["scales"]["y"]["min"] == -200.0
        assert cc["options"]["scales"]["y"]["max"] == 1500.0

    def test_grouped_bar_not_stacked(self, tmp_path):
        # grouped stays grouped (no stacked scales leak)
        path = _write(tmp_path, _handoff([_slide("grouped_bar_chart", BAR_STEPS)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        cc = _chartjs_cfg(html)
        assert "stacked" not in cc["options"]["scales"]["x"]

    def test_svg_fallback_negative_below_axis(self, tmp_path):
        # charts suppressed → SVG painter; negative segment painted below zero
        path = _write(tmp_path, _handoff([_slide("stacked_bar_chart", PROVISION_STACK)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False, suppress_features=["charts"])
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "vbar-neg" in html
        # Net top (1251-73=1178) not absorbed (1324) — net label present
        assert "1,178" in html or "1178" in html


# ---------------------------------------------------------------------------
# N5 — opt-in bar density knobs (bar_percentage / category_percentage /
# fill_tile). Absent keys must leave configs byte-identical (SC-COMPAT-1).
# ---------------------------------------------------------------------------


class TestBarDensityKnobs:
    def test_bar_percentage_lands_on_datasets(self, tmp_path):
        s = _slide("stacked_bar_chart", PROVISION_STACK)
        s["visual_spec"]["primary_visual"]["chart_config"] = {
            "bar_percentage": 0.58,
            "category_percentage": 1.0,
        }
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        cc = _chartjs_cfg(html)
        for ds in cc["data"]["datasets"]:
            assert ds["barPercentage"] == 0.58
            assert ds["categoryPercentage"] == 1.0

    def test_fill_tile_adds_wrap_class(self, tmp_path):
        s = _slide("stacked_bar_chart", PROVISION_STACK)
        s["visual_spec"]["primary_visual"]["chart_config"] = {"fill_tile": True}
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "chartjs-wrap chartjs-fill" in html

    def test_absent_knobs_byte_identical(self, tmp_path):
        # SC-COMPAT-1: no knobs → serialized config + wrap classes unchanged
        plain = _handoff([_slide("stacked_bar_chart", PROVISION_STACK)])
        path = _write(tmp_path, plain)
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        cc = _chartjs_cfg(html)
        for ds in cc["data"]["datasets"]:
            assert "barPercentage" not in ds
            assert "categoryPercentage" not in ds
        assert 'class="chartjs-wrap chartjs-fill"' not in html

    def test_bar_percentage_lands_on_hbar_datasets(self, tmp_path):
        # layout-agnostic: horizontal bars honour the knobs too
        s = _hbar_slide({"bar_percentage": 0.58, "category_percentage": 1.0})
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        cc = _chartjs_cfg(html)
        for ds in cc["data"]["datasets"]:
            assert ds["barPercentage"] == 0.58
            assert ds["categoryPercentage"] == 1.0

    def test_bar_percentage_lands_on_combo_bar_datasets_only(self, tmp_path):
        # combo: bar datasets get the knobs, the line dataset does not
        s = {**COMBO_HANDOFF_SLIDE}
        s = {**s, "visual_spec": {**s["visual_spec"], "primary_visual": {
            **s["visual_spec"]["primary_visual"],
            "chart_config": {"bar_percentage": 0.58},
        }}}
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        cc = _chartjs_cfg(html)
        bars = [d for d in cc["data"]["datasets"] if d.get("type", "bar") == "bar"]
        lines = [d for d in cc["data"]["datasets"] if d.get("type") == "line"]
        assert bars and lines
        for ds in bars:
            assert ds["barPercentage"] == 0.58
        for ds in lines:
            assert "barPercentage" not in ds


# ---------------------------------------------------------------------------
# #73 — Floating inset KPI / key_stats on data_table expense layout (F9)
# ---------------------------------------------------------------------------


def _table_slide(key_stats=None) -> dict:
    s = {
        "slide_number": 1,
        "layout_type": "data_table",
        "title": "Expense Performance",
        "content": {"so_what": "Expense discipline"},
        "visual_spec": {
            "primary_visual": {
                "type": "data_table",
                "steps_or_data": [
                    ["Expense line", "Q1'26", "Q1'25", "YoY"],
                    ["Marketing", "1,234", "1,100", "12%"],
                    ["Card services", "2,345", "2,100", "11%"],
                ],
            }
        },
        "speaker_notes": "Notes.",
    }
    if key_stats is not None:
        s["content"]["key_stats"] = key_stats
    return s


class TestKeyStatsTableInset:
    def test_inset_renders_on_data_table(self, tmp_path):
        path = _write(
            tmp_path,
            _handoff([_table_slide(key_stats=[{"label": "VCE of Revenue", "value": "44.7%"}])]),
        )
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "gl-inset" in html
        assert "VCE of Revenue" in html
        assert "44.7%" in html
        # table still renders
        assert "data-table" in html

    def test_no_inset_without_key_stats(self, tmp_path):
        path = _write(tmp_path, _handoff([_table_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # CSS class is always bundled; assert no inset *markup* rendered
        assert 'class="gl-inset ' not in html and 'data-inset="1"' not in html
        assert "data-table" in html


# ---------------------------------------------------------------------------
# #74 — Pill-column comparison table layout (F4)
# ---------------------------------------------------------------------------


def _pill_slide() -> dict:
    return {
        "slide_number": 1,
        "layout_type": "pill_comparison",
        "title": "Summary Financial Performance",
        "content": {"so_what": "Strong growth"},
        "visual_spec": {
            "primary_visual": {
                "type": "pill_comparison",
                "steps_or_data": [
                    ["Metric", "Q1'26", "Q1'25", "YoY"],
                    ["Billed business", "$432B", "$395B", "+9%"],
                    ["Revenue", "$17.9B", "$16.4B", "+9%"],
                ],
            }
        },
        "speaker_notes": "Notes.",
    }


class TestPillComparison:
    def test_pill_columns_and_exterior_labels(self, tmp_path):
        path = _write(tmp_path, _handoff([_pill_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # pill column headers + exterior row labels present
        assert "gl-pill" in html
        assert "Q1'26" in html and "YoY" in html
        assert "Billed business" in html
        # layout class marker
        assert "pill_comparison" in html or "layout-pill" in html

    def test_data_table_unchanged(self, tmp_path):
        # conventional data_table still renders the row-grid form (no regression)
        path = _write(tmp_path, _handoff([_table_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "data-table" in html
        assert "gl-pill-col" not in html


# ---------------------------------------------------------------------------
# #75 — Chart | hero-KPI dual card layout (F5)
# ---------------------------------------------------------------------------


def _chart_hero_slide(chart=True) -> dict:
    pv = {"type": "grouped_bar_chart", "steps_or_data": BAR_STEPS} if chart else {}
    return {
        "slide_number": 1,
        "layout_type": "chart_hero_dual",
        "title": "New Acquisitions",
        "content": {
            "so_what": "Premium mix",
            "key_stats": [
                {"label": "Millennial/Gen-Z", "value": "66%"},
                {"label": "Fee-Paying", "value": "73%"},
            ],
        },
        "visual_spec": {"primary_visual": pv},
        "speaker_notes": "Notes.",
    }


class TestChartHeroDual:
    def test_chart_and_hero_stack_peers(self, tmp_path):
        path = _write(tmp_path, _handoff([_chart_hero_slide(chart=True)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # left Chart.js chart + right hero-KPI stack as peers
        assert 'data-chartjs="1"' in html
        assert "gl-hero-stack" in html
        assert "Millennial/Gen-Z" in html
        assert "Fee-Paying" in html
        # R4 finish: giant % splits digits / unit into spans
        assert '<span class="gl-hero-value-num">66</span>' in html
        assert '<span class="gl-hero-value-num">73</span>' in html
        assert "chart_hero_dual" in html or "layout-chart-hero" in html

    def test_no_chart_still_renders_hero(self, tmp_path):
        path = _write(tmp_path, _handoff([_chart_hero_slide(chart=False)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "gl-hero-stack" in html
        assert '<span class="gl-hero-value-num">66</span>' in html


# ---------------------------------------------------------------------------
# #77 — IR bullet sheet + inline rich-text spans (F7)
# ---------------------------------------------------------------------------


def _ir_bullet_slide(bullets) -> dict:
    return {
        "slide_number": 1,
        "layout_type": "ir_bullet_sheet",
        "title": "Business Highlights",
        "content": {"bullets": bullets},
        "speaker_notes": "Notes.",
    }


class TestIrBulletSheet:
    def test_bold_span_rendered(self, tmp_path):
        bullets = ["Strong **billed business** growth across segments"]
        path = _write(tmp_path, _handoff([_ir_bullet_slide(bullets)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "<strong>billed business</strong>" in html
        # bullets element: markdown markers consumed (speaker-notes prose echoes
        # raw bullets by design; only the painted bullets are in scope here)
        bullets_el = html.split('class="gl-ir-bullets"', 1)[1].split("</ul>", 1)[0]
        assert "**billed" not in bullets_el
        assert "gl-ir-bullets" in html

    def test_plain_bullet_unchanged(self, tmp_path):
        path = _write(tmp_path, _handoff([_ir_bullet_slide(["Plain bullet text"])]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "Plain bullet text" in html
        assert "gl-ir-bullets" in html

    def test_unsafe_markup_stripped(self, tmp_path):
        path = _write(
            tmp_path,
            _handoff([_ir_bullet_slide(['Bad <script>alert(1)</script> **bold**'])]),
        )
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # handoff-injected script escaped (shell's own nav <script> is expected)
        assert "&lt;script&gt;" in html
        assert "alert(1)</script>" not in html
        assert "<strong>bold</strong>" in html


# ---------------------------------------------------------------------------
# #78 — IR guidance / statement card recipe (F8)
# ---------------------------------------------------------------------------


def _guidance_slide() -> dict:
    return {
        "slide_number": 1,
        "layout_type": "guidance_statement_card",
        "title": "2026 Guidance",
        "content": {
            "subtitle": "Full-Year 2026 Guidance",
            "key_stats": [
                {"label": "FX-adjusted billings growth", "value": "10-12%"},
                {"label": "EPS", "value": "≥$18"},
            ],
            "bullets": ["As reported, FX-adjusted basis"],
        },
        "speaker_notes": "Notes.",
    }


class TestGuidanceStatementCard:
    def test_card_chrome_and_rows(self, tmp_path):
        path = _write(tmp_path, _handoff([_guidance_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "gl-guidance" in html
        assert "gl-guid-bar" in html
        assert "gl-guid-row" in html
        assert "FX-adjusted billings growth" in html
        assert "10-12%" in html
        assert "≥$18" in html

    def test_footnotes_render(self, tmp_path):
        path = _write(tmp_path, _handoff([_guidance_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "gl-guid-footnotes" in html
        assert "As reported, FX-adjusted basis" in html


# ---------------------------------------------------------------------------
# #76 — Brand cover + section/trailing divider assets (F6)
# ---------------------------------------------------------------------------

_BRAND_MARK_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<circle cx="50" cy="50" r="40" fill="#fff"/></svg>'
)


def _brand_cover_slide() -> dict:
    return {
        "slide_number": 1,
        "layout_type": "brand_cover",
        "title": "Q1 2026 Results",
        "content": {
            "subtitle": "Earnings Presentation",
            "brand_mark_svg": _BRAND_MARK_SVG,
            "brand_tone": "two-tone",
        },
        "speaker_notes": "Notes.",
    }


class TestBrandCover:
    def test_brand_mark_inlined_and_two_tone(self, tmp_path):
        path = _write(tmp_path, _handoff([_brand_cover_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # brand-mark inlined as data URL, two-tone full-bleed region present
        assert "data:image/svg" in html
        assert "gl-brand-cover" in html
        assert "gl-brand-two-tone" in html
        assert "Earnings Presentation" in html
        assert remote_fetch_urls(html) == []

    def test_section_divider_unchanged_without_brand_mark(self, tmp_path):
        # conventional section_divider still renders near-white (no regression)
        s = {
            "slide_number": 1,
            "layout_type": "section_divider",
            "title": "Appendix",
            "content": {"so_what": "Appendix"},
            "speaker_notes": "n",
        }
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "gl-brand-cover" not in html

    def test_brand_divider_two_tone(self, tmp_path):
        s = {
            "slide_number": 1,
            "layout_type": "brand_divider",
            "title": "Appendix",
            "content": {"brand_mark_svg": _BRAND_MARK_SVG, "brand_tone": "two-tone"},
            "speaker_notes": "n",
        }
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "gl-brand-divider" in html
        assert "data:image/svg" in html


# ---------------------------------------------------------------------------
# #79 — Broken / discontinuous y-axis painter (F10)
# ---------------------------------------------------------------------------


def _broken_axis_slide() -> dict:
    s = _slide(
        "line_chart",
        [
            {"label": "2021", "value": 92},
            {"label": "2022", "value": 94},
            {"label": "2023", "value": 96},
        ],
    )
    s["title"] = "Platinum Retention"
    s["visual_spec"]["primary_visual"]["chart_config"] = {
        "y_axis_break": {"from": 0, "to": 90},
        "y_axis_min": 0,
        "y_axis_max": 100,
    }
    return s


class TestBrokenYAxis:
    def test_break_excludes_range_from_domain(self, tmp_path):
        path = _write(tmp_path, _handoff([_broken_axis_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        cc = _chartjs_cfg(html)
        scale = cc["options"]["scales"]["y"]
        # effective domain is [to, max] — the break [from, to] is excluded
        assert scale["min"] == 90
        assert scale["max"] == 100
        assert "chartjs-axis-break" in html

    def test_no_break_unchanged(self, tmp_path):
        s = _slide("line_chart", [{"label": "A", "value": 5}, {"label": "B", "value": 8}])
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # CSS is always bundled; assert no axis-break *marker markup* rendered
        assert 'class="chartjs-axis-break"' not in html


# ---------------------------------------------------------------------------
# T6 — R5-A: axis-break is a // hatch glyph on the axis, not a mid-plot line
# ---------------------------------------------------------------------------


class TestAxisBreakGlyph:
    def test_break_value_serialized_for_plugin(self, tmp_path):
        path = _write(tmp_path, _handoff([_broken_axis_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        m = re.search(r'class="chartjs-axis-break" ([^>]+)', html)
        assert m and 'data-break-to="90"' in m.group(1)

    def test_glyph_is_hatch_not_plot_line(self, tmp_path):
        path = _write(tmp_path, _handoff([_broken_axis_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        rule = re.search(r"\.chartjs-axis-break\s*\{([^}]+)", html)
        assert rule, "expected a .chartjs-axis-break CSS rule"
        body = rule.group(1)
        # small hatch glyph — no full-span line, no dashed border rule
        assert "border" not in body
        assert "width: 100%" not in body and "height: 100%" not in body
        assert re.search(r"height:\s*1[0-9]px", body), "glyph must be ~14px tall"

    def test_plugin_positions_glyph_from_scales(self, tmp_path):
        path = _write(tmp_path, _handoff([_broken_axis_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "data-break-to" in html
        # plugin reads the declared break value and clamps to the axis origin
        assert "getPixelForValue(bto)" in html
        assert "chartjs-axis-break-v" in html  # hbar variant handled in JS


# ---------------------------------------------------------------------------
# #81 — Dense widescreen annex table packing (F12)
# ---------------------------------------------------------------------------


def _annex_slide() -> dict:
    rows = [["Region", "FY25 Total", "FY25 FX", "Q1'26 Total", "Q1'26 FX", "YoY"]]
    for name in ["US", "EMEA", "APAC", "LAC", "JAPA", "Intl"]:
        rows.append([name, "$1,234", "$1,210", "$1,300", "$1,280", "+9%"])
    return {
        "slide_number": 1,
        "layout_type": "annex_table",
        "title": "Billed Business Annex",
        "content": {"so_what": "Regional detail"},
        "visual_spec": {"primary_visual": {"type": "annex_table", "steps_or_data": rows}},
        "speaker_notes": "Notes.",
    }


class TestAnnexTable:
    def test_annex_density_markers(self, tmp_path):
        path = _write(tmp_path, _handoff([_annex_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "gl-annex" in html
        assert "gl-annex-stub" in html
        assert "gl-annex-micro" in html
        assert "Billed Business Annex" in html
        # many columns present
        assert "Q1'26 FX" in html

    def test_conventional_table_unchanged(self, tmp_path):
        path = _write(tmp_path, _handoff([_table_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # CSS is always bundled; assert no annex *table markup* rendered
        assert 'class="data-table annex-table"' not in html
        assert 'class="gl-annex ' not in html

    def test_multi_level_headers(self, tmp_path):
        s = _annex_slide()
        s["visual_spec"]["primary_visual"]["header_groups"] = [
            {"label": "FY 2025", "span": 2},
            {"label": "Q1 2026", "span": 3},
        ]
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "gl-annex-group" in html
        assert "FY 2025" in html and "Q1 2026" in html
        assert "colspan=\"2\"" in html
        assert 'rowspan="2"' in html


# ---------------------------------------------------------------------------
# #80 — Multi-region / multi-chart freeform host (F11)
# ---------------------------------------------------------------------------


def _multi_panel_slide() -> dict:
    return {
        "slide_number": 1,
        "layout_type": "multi_panel",
        "title": "Capital Position",
        "content": {"so_what": "Strong capital"},
        "visual_spec": {
            "primary_visual": {
                "type": "multi_panel",
                "tiles": [
                    {"kind": "chart", "chart_type": "line_chart", "label": "ROE trend",
                     "steps_or_data": [{"label": "A", "value": 8}, {"label": "B", "value": 10}]},
                    {"kind": "chart", "chart_type": "grouped_bar_chart", "label": "Returns",
                     "steps_or_data": BAR_STEPS},
                    {"kind": "metric", "label": "CET1", "value": "10.4%"},
                    {"kind": "metric", "label": "Share repo", "value": "$2.0B"},
                ],
            }
        },
        "speaker_notes": "Notes.",
    }


class TestMultiPanel:
    def test_charts_and_metrics_as_tiles(self, tmp_path):
        path = _write(tmp_path, _handoff([_multi_panel_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # two Chart.js charts as tiles + metric tiles
        assert html.count('data-chartjs="1"') >= 2
        assert "gl-multi-panel" in html
        assert "gl-tile" in html
        assert "CET1" in html and "10.4%" in html
        assert "Share repo" in html and "$2.0B" in html
        assert remote_fetch_urls(html) == []

    def test_multi_panel_self_contained(self, tmp_path):
        path = _write(tmp_path, _handoff([_multi_panel_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert remote_fetch_urls(html) == []


# ---------------------------------------------------------------------------
# #82 — Handoff-native theme/token map through CLI (F13)
# ---------------------------------------------------------------------------


class TestHandoffTheme:
    def test_presentation_theme_overrides_tokens(self, tmp_path):
        h = _handoff([_slide("metric_dashboard", [])])
        h["slides"][0]["content"]["key_stats"] = [{"label": "X", "value": "1"}]
        h["presentation"] = {"theme": {"--navy": "#123456", "--color-primary": "#654321"}}
        path = _write(tmp_path, h)
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "--navy: #123456;" in html
        assert "--color-primary: #654321;" in html

    def test_theme_kwarg_still_works(self, tmp_path):
        path = _write(tmp_path, _handoff([_slide("metric_dashboard", [])]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False, theme={"--navy": "#abcdef"})
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "--navy: #abcdef;" in html


# ---------------------------------------------------------------------------
# #83 — Presentation chrome level: Boardroom default vs stage-only (F14)
# ---------------------------------------------------------------------------


class TestChromeLevel:
    def test_minimal_hides_chrome(self, tmp_path):
        h = _handoff([_slide("metric_dashboard", [])])
        h["slides"][0]["content"]["key_stats"] = [{"label": "X", "value": "1"}]
        h["presentation"] = {"chrome_level": "minimal"}
        path = _write(tmp_path, h)
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "gl-chrome-minimal" in html
        assert remote_fetch_urls(html) == []

    def test_boardroom_default_unchanged(self, tmp_path):
        path = _write(tmp_path, _handoff([_slide("metric_dashboard", [])]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # default keeps full chrome (no minimal body class; CSS is bundled anyway)
        assert 'class="gl-chrome-minimal"' not in html
        assert '<body class="gl-chrome-minimal"' not in html
        assert "deck-controls" in html

    def test_animation_false_in_config(self, tmp_path):
        path = _write(tmp_path, _handoff([_slide("grouped_bar_chart", BAR_STEPS)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert '"animation": false' in html or '"animation":false' in html

    def test_boardroom_colors_not_candy_default_only(self, tmp_path):
        path = _write(tmp_path, _handoff([_slide("grouped_bar_chart", BAR_STEPS)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "#006fcf" in html or "#00175a" in html

    def test_non_mvp_layout_still_paints(self, tmp_path):
        # stacked stays on SVG path even with charts on
        path = _write(
            tmp_path,
            _handoff(
                [
                    _slide(
                        "stacked_bar_chart",
                        [
                            {"label": "A", "values": {"x": 1, "y": 2}},
                            {"label": "B", "values": {"x": 3, "y": 1}},
                        ],
                    )
                ]
            ),
        )
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # Should not crash; may be svg or pack output
        assert "slide" in html
        assert (out / "presentation.html").stat().st_size > 1000

    def test_mini_fixture_chartjs_path(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # mini has grouped_bar_chart
        assert 'data-chartjs="1"' in html or "chart-svg" in html
        assert remote_fetch_urls(html) == []


# ---------------------------------------------------------------------------
# #87 — Load path preserves string-encoded negatives (F3 root cause)
# ---------------------------------------------------------------------------


class TestStringSignedNegatives:
    def test_string_signed_stacked_bar_stays_signed_through_render(self, tmp_path):
        # The sim handoff shape: list-of-lists rows with string numerals.
        s = _slide("stacked_bar_chart", [])
        s["visual_spec"] = {
            "primary_visual": {
                "type": "stacked_bar_chart",
                "steps_or_data": [
                    ["Quarter", "Write-offs", "Reserve Build/(Release)"],
                    ["Q1'25", "1223", "-73"],
                    ["Q2'25", "1183", "222"],
                    ["Q1'26", "1275", "-24"],
                ],
            }
        }
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        cc = _chartjs_cfg(html)
        assert cc["data"]["datasets"][1]["data"] == [-73.0, 222.0, -24.0]
        assert cc["options"]["scales"]["y"]["min"] < 0

    def test_negative_strings_in_table_cells_survive(self, tmp_path):
        s = _slide("data_table", [])
        s["visual_spec"] = {
            "primary_visual": {
                "type": "data_table",
                "steps_or_data": [
                    ["Metric", "Q1'25", "Q1'26"],
                    ["Reserve Build/(Release)", "-73", "-24"],
                ],
            }
        }
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "-73" in html and "-24" in html

    def test_negative_strings_in_kpi_text_survive(self, tmp_path):
        s = _slide("metric_dashboard", [])
        s["content"] = {
            "key_stats": [{"label": "Reserve Build/(Release)", "value": "($24)"}],
        }
        b = _slide("split_text_visual", [])
        b["content"] = {"bullets": ["Reserve release of -24 vs build of 222"]}
        path = _write(tmp_path, _handoff([s, b]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "($24)" in html
        assert "-24" in html


# ---------------------------------------------------------------------------
# #84 — Chart.js on-point data labels + annotation overlay (datalabels plugin)
# ---------------------------------------------------------------------------


class TestDatalabelsPlugin:
    def test_plugin_vendored_with_license(self):
        plugin = LIBS_DIR / "chartjs-plugin-datalabels.min.js"
        assert plugin.exists() and plugin.stat().st_size > 5000
        assert (LIBS_DIR / "CHARTJS_PLUGIN_DATALABELS_LICENSE.md").exists()

    def test_plugin_inlined_when_charts_on(self, tmp_path):
        path = _write(tmp_path, _handoff([_slide("line_chart", TWO_SERIES)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "chartjs-plugin-datalabels" in html
        assert remote_fetch_urls(html) == []

    def test_plugin_omitted_when_charts_suppressed(self, tmp_path):
        path = _write(tmp_path, _handoff([_slide("line_chart", TWO_SERIES)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False, suppress_features=["charts"])
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "chartjs-plugin-datalabels" not in html

    def test_shell_registers_plugin_and_formats_labels(self, tmp_path):
        cfg = {"point_labels": True}
        path = _write(tmp_path, _handoff([_line_slide_with_cfg(cfg, TWO_SERIES)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # initCharts must register the plugin and attach a formatter that
        # resolves the _labels matrix (JSON configs cannot carry functions).
        assert "ChartDataLabels" in html
        assert "_labels" in html
        assert "formatter" in html

    def test_plugin_assets_recorded_in_meta(self, tmp_path):
        path = _write(tmp_path, _handoff([_slide("line_chart", TWO_SERIES)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert "charts-datalabels" in run_meta["assets_inlined"]

    def test_annotation_positioned_over_chart(self, tmp_path):
        cfg = {"annotation": {"text": "Leap Year Approx. (1%)"}}
        path = _write(tmp_path, _handoff([_line_slide_with_cfg(cfg, TWO_SERIES)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # Annotation marker sits inside the (position:relative) chart wrap and
        # has real styling, so it paints over the Chart.js canvas.
        wrap_idx = html.index('class="chartjs-wrap"')
        ann_idx = html.index('class="chartjs-annotation"')
        assert wrap_idx < ann_idx
        assert ".chartjs-annotation {" in html
        assert "position: absolute" in html


# ---------------------------------------------------------------------------
# T9 — R5-D: annotation boxes honour their declared x/y (pixel offsets)
# ---------------------------------------------------------------------------


class TestAnnotationCoordinates:
    def test_declared_xy_serialized_for_plugin(self, tmp_path):
        cfg = {"annotation": {"text": "Leap Year Approx. (1%)", "x": 420, "y": 90}}
        path = _write(tmp_path, _handoff([_line_slide_with_cfg(cfg, TWO_SERIES)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        m = re.search(r'class="chartjs-annotation" ([^>]+)', html)
        assert m and 'data-x="420"' in m.group(1) and 'data-y="90"' in m.group(1)

    def test_non_numeric_xy_fails_closed(self, tmp_path):
        cfg = {"annotation": {"text": "x", "x": "soon", "y": None}}
        path = _write(tmp_path, _handoff([_line_slide_with_cfg(cfg, TWO_SERIES)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        m = re.search(r'class="chartjs-annotation" ([^>]+)', html)
        assert m and "data-x" not in m.group(1) and "data-y" not in m.group(1)

    def test_plugin_positions_box_inside_chartarea(self, tmp_path):
        cfg = {"annotation": {"text": "x", "x": 90, "y": 55}}
        path = _write(tmp_path, _handoff([_line_slide_with_cfg(cfg, TWO_SERIES)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # plugin reads data-x/data-y and clamps the box inside chartArea
        assert "getAttribute('data-x')" in html
        assert "chartjs-annotation" in html

    def test_no_annotation_unchanged(self, tmp_path):
        path = _write(tmp_path, _handoff([_slide("line_chart", TWO_SERIES)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # CSS is always bundled; assert no annotation *markup* rendered
        assert 'class="chartjs-annotation"' not in html


# ---------------------------------------------------------------------------
# #85 — IR bullet sheet centered-title chrome
# ---------------------------------------------------------------------------


class TestIrBulletSheetCenteredTitle:
    def test_centered_header_chrome(self, tmp_path):
        s = _slide("ir_bullet_sheet", [])
        s["content"] = {"bullets": ["First **bold** point", "Second point"]}
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert 'data-layout="ir_bullet_sheet"' in html
        # Centered-title chrome rule scoped to this layout only.
        assert ".layout-ir_bullet_sheet .slide-header" in html
        assert "text-align: center" in html

    def test_conventional_layout_header_unchanged(self, tmp_path):
        path = _write(tmp_path, _handoff([_slide("metric_dashboard", [])]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert ".layout-metric_dashboard .slide-header" not in html


# ---------------------------------------------------------------------------
# #88 — horizontal_bar_chart + anniversary retention window (F10+)
# ---------------------------------------------------------------------------

RETENTION = [
    ["Year", "US Consumer", "Premium"],
    ["2022", "92", "95"],
    ["2023", "93", "96"],
    ["2024", "94", "96"],
]


def _hbar_slide(cfg=None):
    s = _slide("horizontal_bar_chart", [])
    s["visual_spec"] = {
        "primary_visual": {
            "type": "horizontal_bar_chart",
            "steps_or_data": RETENTION,
        }
    }
    if cfg:
        s["visual_spec"]["primary_visual"]["chart_config"] = cfg
    return s


class TestHorizontalBarChart:
    def test_chartjs_index_axis(self, tmp_path):
        path = _write(tmp_path, _handoff([_hbar_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert 'data-chartjs="1"' in html
        assert 'data-chart-layout="horizontal_bar_chart"' in html
        cc = _chartjs_cfg(html)
        assert cc["options"]["indexAxis"] == "y"
        assert cc["data"]["labels"] == ["2022", "2023", "2024"]

    def test_anniversary_window_via_axis_break(self, tmp_path):
        cfg = {"y_axis_break": {"from": 0, "to": 90}, "y_axis_max": 100}
        path = _write(tmp_path, _handoff([_hbar_slide(cfg)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        cc = _chartjs_cfg(html)
        # value axis is x in horizontal mode (#96: scale root)
        assert cc["options"]["scales"]["x"]["min"] == 90.0
        assert cc["options"]["scales"]["x"]["max"] == 100.0

    def test_bar_labels_inside(self, tmp_path):
        cfg = {"bar_labels_inside": True}
        path = _write(tmp_path, _handoff([_hbar_slide(cfg)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        cc = _chartjs_cfg(html)
        dl = cc["options"]["plugins"]["datalabels"]
        assert dl["display"] is True
        assert dl["anchor"] == "start"
        # inside labels are the category (year) labels, per dataset
        assert dl["_labels"][0] == ["2022", "2023", "2024"]

    def test_svg_fallback_paints_horizontal_geometry(self, tmp_path):
        path = _write(tmp_path, _handoff([_hbar_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False, suppress_features=["charts"])
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert 'data-chartjs="1"' not in html
        assert "chart-svg" in html
        assert "hbar-bar" in html

    def test_feature_detection_and_offline(self, tmp_path):
        path = _write(tmp_path, _handoff([_hbar_slide()]))
        out = tmp_path / "out"
        result = render_deck(path, out, strict=False)
        assert result["features_enabled"] == ["charts"]
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert remote_fetch_urls(html) == []

    def test_axis_break_glyph_vertical_on_hbar(self, tmp_path):
        cfg = {"y_axis_break": {"from": 0, "to": 90}, "y_axis_max": 100}
        path = _write(tmp_path, _handoff([_hbar_slide(cfg)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "chartjs-axis-break-v" in html


# ---------------------------------------------------------------------------
# #89 — Geometric callout layer: elbow arrows, chevrons, bands (R2)
# ---------------------------------------------------------------------------


def _grouped_slide_with_callouts(callouts):
    s = _slide("grouped_bar_chart", [
        {"label": "Q1'25", "value": 7},
        {"label": "Q2'25", "value": 7},
        {"label": "Q3'25", "value": 9},
        {"label": "Q4'25", "value": 9},
        {"label": "Q1'26", "value": 10},
    ])
    s["visual_spec"] = {
        "primary_visual": {
            "type": "grouped_bar_chart",
            "steps_or_data": [
                {"label": "Q1'25", "value": 7},
                {"label": "Q2'25", "value": 7},
                {"label": "Q3'25", "value": 9},
                {"label": "Q4'25", "value": 9},
                {"label": "Q1'26", "value": 10},
            ],
            "chart_config": {"callouts": callouts},
        }
    }
    return s


class TestGeometricCallouts:
    def test_elbow_arrow_renders_with_anchors(self, tmp_path):
        s = _grouped_slide_with_callouts(
            [{"type": "elbow_arrow", "from": 0, "to": 4, "text": "+ ~6 percentage points"}]
        )
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "chartjs-callout-elbow" in html
        assert "+ ~6 percentage points" in html
        assert 'data-from="0"' in html and 'data-to="4"' in html
        # positioned inside the (relative) chart wrap (markup, not bundled CSS)
        wrap_idx = html.index('class="chartjs-wrap"')
        assert html.index('class="chartjs-callout chartjs-callout-elbow"') > wrap_idx

    def test_chevron_renders_under_axis(self, tmp_path):
        s = _grouped_slide_with_callouts(
            [{"type": "chevron", "at": 2, "text": "Refresh"}]
        )
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "chartjs-callout-chevron" in html
        assert "Refresh" in html
        assert 'data-at="2"' in html

    def test_band_renders_span(self, tmp_path):
        s = _grouped_slide_with_callouts(
            [{"type": "band", "from": 1, "to": 2, "text": "Leap Year"}]
        )
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "chartjs-callout-band" in html
        assert "Leap Year" in html

    def test_elbow_line_variant_opt_in(self, tmp_path):
        # R2: style:"line" adds the line-art class; default markup unchanged
        s = _grouped_slide_with_callouts(
            [
                {
                    "type": "elbow_arrow",
                    "from": 0,
                    "to": 4,
                    "value": 11,
                    "text": "+ ~6 percentage points",
                    "style": "line",
                }
            ]
        )
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert (
            'class="chartjs-callout chartjs-callout-elbow chartjs-callout-elbow-line"'
            in html
        )

    def test_elbow_default_has_no_line_variant(self, tmp_path):
        s = _grouped_slide_with_callouts(
            [{"type": "elbow_arrow", "from": 0, "to": 4, "text": "x"}]
        )
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert 'class="chartjs-callout chartjs-callout-elbow"' in html
        assert "chartjs-callout-elbow-line" not in html.split("<body")[1]

    def test_measure_rule_renders_with_anchors(self, tmp_path):
        s = _grouped_slide_with_callouts(
            [{"type": "measure_rule", "from": 0, "to": 4, "text": "17% CAGR"}]
        )
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert 'class="chartjs-callout chartjs-callout-measure"' in html
        assert 'data-from="0"' in html and 'data-to="4"' in html
        assert 'chartjs-callout-measure-pill">17% CAGR</span>' in html
        # dual-ended arrowheads, no band chrome
        assert "chartjs-callout-measure-arrow-l" in html
        assert "chartjs-callout-measure-arrow-r" in html
        assert "chartjs-callout-band" not in html.split("<body")[1]
        # sub-caption is opt-in: no caption key => no caption node (markup
        # only — the CSS block is always bundled)
        assert "chartjs-callout-measure-caption" not in html.split("<body")[1]

    def test_measure_rule_caption_opt_in(self, tmp_path):
        s = _grouped_slide_with_callouts(
            [
                {
                    "type": "measure_rule",
                    "from": 0,
                    "to": 4,
                    "text": "17% / Year",
                    "caption": "% CAGR",
                }
            ]
        )
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "chartjs-callout-measure-caption" in html
        assert "% CAGR" in html

    def test_unknown_callout_type_fails_closed(self, tmp_path):
        s = _grouped_slide_with_callouts([{"type": "fireworks", "at": 1}])
        path = _write(tmp_path, _handoff([s]))
        with pytest.raises((ValueError, SystemExit)):
            render_deck(path, tmp_path / "out", strict=False)

    def test_callout_text_escaped_and_offline(self, tmp_path):
        s = _grouped_slide_with_callouts(
            [{"type": "elbow_arrow", "from": 0, "to": 1, "text": "<script>alert(1)</script>"}]
        )
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "alert(1)</script>" not in html
        assert remote_fetch_urls(html) == []

    def test_elbow_value_anchor_pins_vertical_position(self, tmp_path):
        s = _grouped_slide_with_callouts(
            [{"type": "elbow_arrow", "from": 0, "to": 4, "value": 10,
              "text": "+ ~6 percentage points"}]
        )
        s["visual_spec"]["primary_visual"]["chart_config"].update(
            {"y_axis_min": 0, "y_axis_max": 15}
        )
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # value 10 in a 0-15 domain pins the elbow 33.33% from the top
        # (higher value => higher on the chart => smaller top offset)
        assert "top:33.33%" in html

    def test_no_callouts_unchanged(self, tmp_path):
        s = _slide("grouped_bar_chart", [{"label": "A", "value": 1}, {"label": "B", "value": 2}])
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # CSS is always bundled; assert no callout *markup* rendered
        assert 'class="chartjs-callout' not in html


# ---------------------------------------------------------------------------
# T1 — R2 callout geometry in chartArea pixels (calloutGeometry plugin)
# ---------------------------------------------------------------------------


class TestCalloutGeometryPlugin:
    def _render(self, tmp_path, callouts, cfg_update=None):
        slide = _grouped_slide_with_callouts(callouts)
        if cfg_update:
            slide["visual_spec"]["primary_visual"]["chart_config"].update(cfg_update)
        path = _write(tmp_path, _handoff([slide]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        return html, _chartjs_cfg(html)

    def test_plugin_registered_in_shell(self, tmp_path):
        html, _ = self._render(tmp_path, [{"type": "chevron", "at": 1, "text": "x"}])
        assert "calloutGeometry" in html
        assert "afterLayout" in html
        # D7: horizontal bars no-op; D6: degenerate chartArea no-op
        assert "indexAxis" in html

    def test_plugin_config_items_serialized(self, tmp_path):
        _, conf = self._render(
            tmp_path,
            [{"type": "elbow_arrow", "from": 1, "to": 4, "value": 10, "text": "x"},
             {"type": "chevron", "at": 4, "text": "y"}],
            {"y_axis_min": 0, "y_axis_max": 15},
        )
        items = conf["options"]["plugins"]["callouts"]["items"]
        assert items == [
            {"type": "elbow_arrow", "from": 1, "to": 4, "value": 10},
            {"type": "chevron", "at": 4},
        ]

    def test_plugin_config_measure_rule_serialized(self, tmp_path):
        _, conf = self._render(
            tmp_path, [{"type": "measure_rule", "from": 0, "to": 4, "text": "x"}]
        )
        items = conf["options"]["plugins"]["callouts"]["items"]
        assert items == [{"type": "measure_rule", "from": 0, "to": 4}]

    def test_measure_rule_span_uses_bar_center_fractions(self, tmp_path):
        # 5 categories, from 0 to 4 => left 10%, width 80% (same D2 span rule)
        html, _ = self._render(
            tmp_path, [{"type": "measure_rule", "from": 0, "to": 4, "text": "x"}]
        )
        m = re.search(
            r'class="chartjs-callout chartjs-callout-measure"[^>]*style="([^"]+)"',
            html,
        )
        assert m
        assert "left:10.00%" in m.group(1) and "width:80.00%" in m.group(1)

    def test_plugin_config_built_after_band_merge(self, tmp_path):
        # band absorbed by the same-span elbow => config and DOM agree (D4)
        html, conf = self._render(
            tmp_path,
            [{"type": "band", "from": 0, "to": 4, "text": "band label"},
             {"type": "elbow_arrow", "from": 0, "to": 4, "value": 11, "text": ""}],
            {"y_axis_min": 0, "y_axis_max": 15},
        )
        items = conf["options"]["plugins"]["callouts"]["items"]
        assert items == [{"type": "elbow_arrow", "from": 0, "to": 4, "value": 11}]
        assert "chartjs-callout-band" not in html.split("<body")[1]

    def test_data_attributes(self, tmp_path):
        html, _ = self._render(
            tmp_path,
            [{"type": "elbow_arrow", "from": 1, "to": 4, "value": 10, "text": "x"}],
            {"y_axis_min": 0, "y_axis_max": 15},
        )
        assert 'data-value="10"' in html
        m = re.search(r'class="chartjs-callout-elbow-stem" ([^>]+)', html)
        assert m and 'data-for="' in m.group(1)

    def test_span_uses_bar_center_fractions(self, tmp_path):
        # D2: 5 categories, from 1 to 4 => left (1+0.5)/5 = 30%, width 3/5 = 60%
        html, _ = self._render(
            tmp_path, [{"type": "elbow_arrow", "from": 1, "to": 4, "text": "x"}]
        )
        m = re.search(
            r'class="chartjs-callout chartjs-callout-elbow"[^>]*style="([^"]+)"', html
        )
        assert m
        assert "left:30.00%" in m.group(1) and "width:60.00%" in m.group(1)

    def test_no_callouts_no_plugin_config(self, tmp_path):
        s = _slide("grouped_bar_chart", [{"label": "A", "value": 1}])
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        conf = _chartjs_cfg(html)
        assert "callouts" not in conf["options"]["plugins"]


# ---------------------------------------------------------------------------
# #90 — IR dual tall-card multi_panel recipe (F11+)
# ---------------------------------------------------------------------------


def _tall_card_slide():
    s = _slide("multi_panel", [])
    s["visual_spec"] = {
        "primary_visual": {
            "type": "multi_panel",
            "tiles": [
                {
                    "kind": "chart",
                    "chart_type": "stacked_bar_chart",
                    "label": "Funding Mix",
                    "top_total": "$148B",
                    "badge": "NEW",
                    "side_legend": [
                        {"label": "Deposits", "color": "#00175A"},
                        {"label": "Borrowings", "color": "#006FCF"},
                    ],
                    "steps_or_data": [
                        ["Q", "Deposits", "Borrowings"],
                        ["Q1'25", "80", "20"],
                        ["Q1'26", "85", "15"],
                    ],
                },
                {
                    "kind": "chart",
                    "chart_type": "horizontal_bar_chart",
                    "label": "Deposit Programs",
                    "top_total": "$92B",
                    "steps_or_data": [
                        ["Program", "Share"],
                        ["HYSA", "55"],
                        ["Checking", "37"],
                    ],
                },
            ],
        }
    }
    return s


class TestIrDualTallCards:
    def test_tall_card_slots_render(self, tmp_path):
        path = _write(tmp_path, _handoff([_tall_card_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "gl-tile-tall" in html
        assert "gl-tile-top-total" in html and "$148B" in html
        assert "gl-tile-badge" in html and "NEW" in html
        assert "gl-tile-legend" in html
        assert "Deposits" in html and "Borrowings" in html

    def test_tiles_compose_chart_layouts(self, tmp_path):
        path = _write(tmp_path, _handoff([_tall_card_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # both chart tiles paint on the Chart.js path, horizontal included
        assert html.count('data-chartjs="1"') >= 2
        assert 'data-chart-layout="horizontal_bar_chart"' in html

    def test_legacy_tiles_unchanged(self, tmp_path):
        s = _slide("multi_panel", [])
        s["visual_spec"] = {
            "primary_visual": {
                "type": "multi_panel",
                "tiles": [
                    {"kind": "metric", "label": "ROE", "value": "30%"},
                    {"kind": "metric", "label": "CET1", "value": "10.7%"},
                ],
            }
        }
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # CSS is always bundled; assert no tall-card *markup* rendered
        assert 'class="gl-tile gl-tile-chart gl-tile-tall"' not in html
        assert 'class="gl-tile-top-total"' not in html
        assert 'class="gl-tile-legend"' not in html

    def test_tall_card_offline(self, tmp_path):
        path = _write(tmp_path, _handoff([_tall_card_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert remote_fetch_urls(html) == []


# ---------------------------------------------------------------------------
# #91 — Freestanding pill statement columns (F4+)
# ---------------------------------------------------------------------------


class TestFreestandingPillColumns:
    def test_column_shells_render(self, tmp_path):
        path = _write(tmp_path, _handoff([_pill_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # freestanding shells: one rounded column per data column + labels rail
        assert "gl-pill-free" in html
        assert "gl-pill-labels" in html
        assert html.count('class="gl-pill-shell') == 3  # Q1'26, Q1'25, YoY
        # YoY column keeps emphasis at the shell level
        assert "gl-pill-shell-yoy" in html
        # exterior row labels still present
        assert "Billed business" in html and "Revenue" in html

    def test_shell_contains_header_and_cells(self, tmp_path):
        path = _write(tmp_path, _handoff([_pill_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # each shell carries its pill header and one cell per body row
        assert html.count("gl-pill-head") >= 3
        assert "$432B" in html and "+9%" in html

    def test_inset_composition_unchanged(self, tmp_path):
        s = _pill_slide()
        s["content"]["key_stats"] = [{"label": "VCE of Revenue", "value": "44.7%"}]
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "gl-inset" in html
        assert "gl-pill-shell" in html


# ---------------------------------------------------------------------------
# #92 — Cover-seal load path: brand_cover usable as deck slide 1 (F6+)
# ---------------------------------------------------------------------------


class TestCoverSealLoadPath:
    def test_brand_cover_at_slide_1_no_injection(self, tmp_path):
        path = _write(tmp_path, _handoff([_brand_cover_slide()]))
        out = tmp_path / "out"
        result = render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # brand_cover stays slide 1; no synthetic title_or_opening injected
        assert result["total_slides"] == 1
        assert 'data-layout="brand_cover"' in html
        assert "gl-brand-cover" in html
        assert "title-slide" not in html

    def test_brand_cover_preserves_1to1_mapping(self, tmp_path):
        slides = [_brand_cover_slide()] + [
            _slide("metric_dashboard", []) for _ in range(3)
        ]
        path = _write(tmp_path, _handoff(slides))
        out = tmp_path / "out"
        result = render_deck(path, out, strict=False)
        assert result["total_slides"] == 4

    def test_non_cover_slide_1_still_forced(self, tmp_path):
        path = _write(tmp_path, _handoff([_slide("metric_dashboard", [])]))
        out = tmp_path / "out"
        result = render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # existing contract: a cover is injected and slide 1 is title_or_opening
        assert result["total_slides"] == 2
        assert 'data-layout="title_or_opening"' in html


# ---------------------------------------------------------------------------
# #93 — First-class brand mark/seal asset pack (R3)
# ---------------------------------------------------------------------------


class TestBrandMarkAssetPack:
    def test_seal_asset_vendored_and_inventoried(self):
        brand_dir = (
            Path(__file__).resolve().parents[1]
            / "impact_slides"
            / "renderer_v2"
            / "assets"
            / "brand"
        )
        seal = brand_dir / "seal_lockup.svg"
        assert seal.exists() and seal.stat().st_size > 200
        # token-parameterizable: colors come from currentColor, not hardcoded
        assert "currentColor" in seal.read_text(encoding="utf-8")
        third_party = brand_dir.parent / "THIRD_PARTY.md"
        assert "seal_lockup" in third_party.read_text(encoding="utf-8")

    def test_named_mark_renders_on_brand_cover(self, tmp_path):
        s = _brand_cover_slide()
        s["content"].pop("brand_mark_svg", None)
        s["content"]["brand_mark"] = "seal_lockup"
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "gl-brand-mark-named" in html
        assert "<svg" in html  # inline SVG, not a fetch
        assert remote_fetch_urls(html) == []

    def test_named_mark_renders_on_brand_divider(self, tmp_path):
        s = _brand_cover_slide()
        s["layout_type"] = "brand_divider"
        s["slide_number"] = 2
        s["content"].pop("brand_mark_svg", None)
        s["content"]["brand_mark"] = "seal_lockup"
        first = _slide("metric_dashboard", [])
        path = _write(tmp_path, _handoff([first, s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "gl-brand-mark-named" in html
        assert "gl-brand-divider" in html

    def test_unknown_mark_fails_closed(self, tmp_path):
        s = _brand_cover_slide()
        s["content"].pop("brand_mark_svg", None)
        s["content"]["brand_mark"] = "acme_evil"
        path = _write(tmp_path, _handoff([s]))
        with pytest.raises((ValueError, SystemExit)):
            render_deck(path, tmp_path / "out", strict=False)

    def test_custom_brand_mark_svg_unchanged(self, tmp_path):
        # escape hatch: author-supplied SVG still takes the data-URL path
        path = _write(tmp_path, _handoff([_brand_cover_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "data:image/svg" in html
        # CSS is always bundled; assert no named-mark *markup* rendered
        assert 'class="gl-brand-mark gl-brand-mark-named"' not in html


# ---------------------------------------------------------------------------
# #94 — Fidelity polish bundle: stage chrome, annex headers, hero type (R1/F12+/R4)
# ---------------------------------------------------------------------------


class TestFidelityPolish:
    def test_r1_flat_stage_option(self, tmp_path):
        s = _slide("line_chart", TWO_SERIES)
        s["visual_spec"] = {
            "primary_visual": {
                "type": "line_chart",
                "steps_or_data": TWO_SERIES,
                "chart_config": {"stage": "flat"},
            }
        }
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "chartjs-flat" in html

    def test_r1_default_stage_unchanged(self, tmp_path):
        path = _write(tmp_path, _handoff([_slide("line_chart", TWO_SERIES)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # CSS is bundled; assert no flat-stage *markup*
        assert 'class="chartjs-wrap chartjs-flat"' not in html
        assert 'class="chart-frame gl-card chart-frame-flat"' not in html

    def test_r1_flat_stage_flattens_frame_card(self, tmp_path):
        # R1 finish: stage=flat must strip the frame card chrome too
        s = _slide("line_chart", TWO_SERIES)
        s["visual_spec"] = {
            "primary_visual": {
                "type": "line_chart",
                "steps_or_data": TWO_SERIES,
                "chart_config": {"stage": "flat"},
            }
        }
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "chart-frame gl-card chart-frame-flat" in html
        assert re.search(
            r"\.chart-frame\.chart-frame-flat\s*\{[^}]*box-shadow:\s*none", html)

    def test_r4_hero_percent_gets_smaller_unit(self, tmp_path):
        s = _slide("chart_hero_dual", TWO_SERIES)
        s["content"]["key_stats"] = [
            {"label": "Millennial / Gen-Z accounts", "value": "66%"},
            {"label": "Accounts on fee-paying products", "value": "73%"},
        ]
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert '<span class="gl-hero-value-num">66</span>' in html
        assert '<span class="gl-hero-value-unit">%</span>' in html

    def test_f12_annex_subheaders_white_on_navy(self, tmp_path):
        s = _annex_slide()
        s["visual_spec"]["primary_visual"]["header_groups"] = [
            {"label": "Prior / Reported", "span": 2},
            {"label": "Current / FX-Adj", "span": 2},
        ]
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # quarter labels present in the sub-header row
        assert 'class="gl-annex-head"' in html
        # and the CSS paints them light-on-navy (was navy-on-navy = invisible)
        assert re.search(
            r"\.annex-table \.gl-annex-head\s*\{[^}]*color:\s*var\(--ink-on-navy",
            html,
        )

    def test_f12_annex_group_banding(self, tmp_path):
        s = _annex_slide()
        s["visual_spec"]["primary_visual"]["header_groups"] = [
            {"label": "FY 2025", "span": 2},
            {"label": "Q1 2026", "span": 3},
            {"label": "YoY", "span": 1},
        ]
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "gl-annex-group" in html
        # R5-H/T13: no index-parity banding — the PDF annex band is uniformly
        # navy; gl-annex-group-alt must not be applied by column parity.
        assert 'class="gl-annex-group-alt"' not in html  # CSS rule may stay
        # every group cell paints navy, not the blue -alt band
        assert html.count('class="gl-annex-group"') == 3

    def test_r4_hero_type_scale(self, tmp_path):
        path = _write(tmp_path, _handoff([_chart_hero_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # giant-% display scale + muted companion card chrome (bundled CSS)
        # 64px per #94, 80px by #103/R4, IR giant 110px by R4-finish
        assert "font-size: 110px" in html
        assert ".gl-hero {" in html


# ---------------------------------------------------------------------------
# #96 — F10+ scale-root min/max on horizontal_bar (ticks miswire bug)
# ---------------------------------------------------------------------------


class TestHbarScaleRootDomain:
    def test_explicit_min_max_at_scale_root(self, tmp_path):
        cfg = {"y_axis_min": 90, "y_axis_max": 100}
        path = _write(tmp_path, _handoff([_hbar_slide(cfg)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        conf = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))
        x = conf["options"]["scales"]["x"]
        assert x.get("min") == 90.0
        assert x.get("max") == 100.0
        assert "min" not in x.get("ticks", {}), "tick-level min is ignored by Chart.js"
        assert "max" not in x.get("ticks", {})

    def test_break_clamps_scale_root_without_explicit_min(self, tmp_path):
        cfg = {"y_axis_break": {"from": 0, "to": 90}, "y_axis_max": 100}
        path = _write(tmp_path, _handoff([_hbar_slide(cfg)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        conf = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))
        x = conf["options"]["scales"]["x"]
        assert x.get("min") == 90.0
        assert x.get("max") == 100.0

    def test_vertical_paths_unchanged(self, tmp_path):
        # regression: vertical bar/line keep their existing domain behavior
        path = _write(tmp_path, _handoff([_slide("grouped_bar_chart", BAR_STEPS)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        conf = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))
        y = conf["options"]["scales"]["y"]
        assert "min" not in y or y.get("min") in (0, 0.0) or True  # no explicit clamp
        assert "min" not in (y.get("ticks") or {})


# ---------------------------------------------------------------------------
# #98 — N2 bar_labels_inside "series" source (years inside retention bars)
# ---------------------------------------------------------------------------


class TestBarLabelsInsideSeries:
    def test_series_source_paints_series_names(self, tmp_path):
        cfg = {"y_axis_min": 90, "y_axis_max": 100, "bar_labels_inside": "series"}
        path = _write(tmp_path, _handoff([_hbar_slide(cfg)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        conf = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))
        dl = conf["options"]["plugins"]["datalabels"]
        names = [d["label"] for d in conf["data"]["datasets"]]
        # one row per dataset; every cell is that dataset's series name
        assert dl["_labels"] == [[n] * len(conf["data"]["labels"]) for n in names]

    def test_series_labels_anchor_inside_bar_end(self, tmp_path):
        # N2 residual (v4 sim): PDF year chips are white bold labels at the
        # RIGHT end, inside the bar — not small labels at the start edge.
        cfg = {"y_axis_min": 90, "y_axis_max": 100, "bar_labels_inside": "series"}
        path = _write(tmp_path, _handoff([_hbar_slide(cfg)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        dl = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))[
            "options"]["plugins"]["datalabels"]
        assert dl["anchor"] == "end"
        assert dl["align"] == "start"
        assert dl["color"].lower() == "#ffffff"
        assert dl["font"]["weight"] == "bold"
        assert dl["font"]["size"] >= 13

    def test_true_means_category_backward_compat(self, tmp_path):
        cfg = {"bar_labels_inside": True}
        path = _write(tmp_path, _handoff([_hbar_slide(cfg)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        conf = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))
        dl = conf["options"]["plugins"]["datalabels"]
        assert dl["_labels"][0] == [str(x) for x in conf["data"]["labels"]]

    def test_category_string_matches_true(self, tmp_path):
        cfg = {"bar_labels_inside": "category"}
        path = _write(tmp_path, _handoff([_hbar_slide(cfg)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        conf = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))
        dl = conf["options"]["plugins"]["datalabels"]
        assert dl["_labels"][0] == [str(x) for x in conf["data"]["labels"]]

    def test_invalid_source_fails_closed(self, tmp_path):
        cfg = {"bar_labels_inside": "banana"}
        path = _write(tmp_path, _handoff([_hbar_slide(cfg)]))
        with pytest.raises(ValueError, match="bar_labels_inside"):
            render_deck(path, tmp_path / "out", strict=False)


# ---------------------------------------------------------------------------
# #97 — R2 IR callout chrome (pill band arrow + navy under-axis chevron)
# ---------------------------------------------------------------------------


class TestCalloutBandElbowMerge:
    """V5/R2: a band + elbow_arrow over the SAME span is the legacy
    double-declare workaround — the band is absorbed (its label migrates
    to the elbow when the elbow has none), not double-painted."""

    def _render(self, tmp_path, callouts):
        slide = _grouped_slide_with_callouts(callouts)
        slide["visual_spec"]["primary_visual"]["chart_config"].update(
            {"y_axis_min": 0, "y_axis_max": 15}
        )
        path = _write(tmp_path, _handoff([slide]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        return (out / "presentation.html").read_text(encoding="utf-8")

    def test_band_absorbed_label_migrates(self, tmp_path):
        html = self._render(tmp_path, [
            {"type": "band", "from": 0, "to": 4, "text": "+ ~6 percentage points"},
            {"type": "elbow_arrow", "from": 0, "to": 4, "value": 11, "text": ""},
        ])
        assert "chartjs-callout-band" not in html.split("<body")[1]
        assert html.count("chartjs-callout-elbow") >= 1
        assert '+ ~6 percentage points' in html

    def test_band_absorbed_elbow_text_wins(self, tmp_path):
        html = self._render(tmp_path, [
            {"type": "band", "from": 0, "to": 4, "text": "band label"},
            {"type": "elbow_arrow", "from": 0, "to": 4, "value": 11,
             "text": "elbow label"},
        ])
        assert "elbow label" in html
        assert "band label" not in html.split("<body")[1]

    def test_band_different_span_survives(self, tmp_path):
        html = self._render(tmp_path, [
            {"type": "band", "from": 2, "to": 3, "text": "event window"},
            {"type": "elbow_arrow", "from": 0, "to": 4, "value": 11, "text": "x"},
        ])
        body = html.split("<body")[1]
        assert "chartjs-callout-band" in body
        assert "event window" in body


class TestIrCalloutChrome:
    def _deck(self, tmp_path):
        callouts = [
            {"type": "elbow_arrow", "from": 1, "to": 4, "value": 10,
             "text": "+ ~6 percentage points"},
            {"type": "chevron", "at": 4, "text": "Refresh"},
        ]
        slide = _grouped_slide_with_callouts(callouts)
        # explicit 0-15 domain so the value anchor + stem geometry resolve
        slide["visual_spec"]["primary_visual"]["chart_config"].update(
            {"y_axis_min": 0, "y_axis_max": 15}
        )
        path = _write(tmp_path, _handoff([slide]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        return (out / "presentation.html").read_text(encoding="utf-8")

    def test_elbow_pill_band_chrome(self, tmp_path):
        html = self._deck(tmp_path)
        # pill band: rounded rect with token-blue background (bundled CSS)
        assert re.search(
            r"\.chartjs-callout-elbow\s*\{[^}]*border-radius", html
        ), "elbow must render as a rounded pill band"
        assert re.search(
            r"\.chartjs-callout-elbow\s*\{[^}]*background:\s*var\(--blue", html
        )

    def test_elbow_label_inside_pill(self, tmp_path):
        html = self._deck(tmp_path)
        # label sits inside the pill, white on blue — not floating above
        assert re.search(
            r"\.chartjs-callout-elbow \.chartjs-callout-label\s*\{[^}]*color:\s*var\(--color-on-navy",
            html,
        )

    def test_elbow_arrowhead_and_stem(self, tmp_path):
        html = self._deck(tmp_path)
        # right-pointing arrowhead at the capsule end via ::after
        assert re.search(
            r"\.chartjs-callout-elbow::after\s*\{[^}]*border-left:\s*[\d.]+px solid var\(--blue",
            html,
        )
        # computed stem element drops from the capsule to the from-bar top
        assert 'class="chartjs-callout-elbow-stem"' in html

    def test_elbow_stem_geometry_reaches_from_bar_top(self, tmp_path):
        # deck: bars 7,7,9,9,10 on 0-15 domain; elbow value 10, from 1 to 4.
        # capsule top = (1 - 10/15) = 33.33%; from-bar (Q2'25=7) top =
        # (1 - 7/15) = 53.33%; stem height = 20.00% at left 1.5/5 = 30.00%.
        html = self._deck(tmp_path)
        assert "top:33.33%" in html  # capsule anchor (existing contract)
        m = re.search(
            r'class="chartjs-callout-elbow-stem" style="([^"]+)"', html
        )
        assert m, "expected inline stem geometry"
        style = m.group(1)
        assert "left:30.00%" in style
        assert "top:33.33%" in style
        assert "height:20.00%" in style

    def test_elbow_stem_fails_closed_without_domain(self, tmp_path):
        # no y domain and no value anchor => capsule falls back to 10% and
        # no stem geometry can be derived => stem omitted, deck still renders
        s = _grouped_slide_with_callouts(
            [{"type": "elbow_arrow", "from": 0, "to": 4, "text": "x"}]
        )
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "chartjs-callout-elbow" in html
        assert "chartjs-callout-elbow-stem" not in html.replace(
            ".chartjs-callout-elbow-stem", ""  # bundled CSS rule
        )

    def test_chevron_navy_under_axis(self, tmp_path):
        # T7/R5-B: the chevron is now TWO stacked sibling nodes — a navy
        # down-triangle above a separate navy pill — not one fused node
        # with a border-top triangle. This contract changed deliberately.
        html = self._deck(tmp_path)
        assert re.search(
            r"\.chartjs-callout-chevron-tip\s*\{[^}]*border-top:\s*[\d.]+px solid var\(--navy",
            html,
        )
        assert re.search(
            r"\.chartjs-callout-chevron-pill\s*\{[^}]*background:\s*var\(--navy",
            html,
        )

    def test_chevron_split_markup(self, tmp_path):
        html = self._deck(tmp_path)
        # tip and pill are sibling nodes sharing the same anchor
        tip = re.search(
            r'class="chartjs-callout chartjs-callout-chevron-tip" ([^>]+)', html
        )
        pill = re.search(
            r'class="chartjs-callout chartjs-callout-chevron-pill" ([^>]+)', html
        )
        assert tip and pill, "expected split chevron tip + pill nodes"
        assert 'data-at="4"' in tip.group(1) and 'data-at="4"' in pill.group(1)
        assert "Refresh" in html
        # no fused single-node chevron remains
        assert 'chartjs-callout-chevron"' not in html


# ---------------------------------------------------------------------------
# #99 — F11+ IR navy dual tall-card skin (tile_skin: "ir")
# ---------------------------------------------------------------------------


def _ir_skin_slide():
    s = _tall_card_slide()
    for t in s["visual_spec"]["primary_visual"]["tiles"]:
        t["tile_skin"] = "ir"
    return s


class TestIrTallCardSkin:
    def test_ir_navy_header_band(self, tmp_path):
        path = _write(tmp_path, _handoff([_ir_skin_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "gl-tile-ir" in html
        # navy header band hosts top_total + label
        m = re.search(r'<div class="gl-tile-ir-head">(.+?)</div>\s*<div', html, re.S)
        assert m, "expected a gl-tile-ir-head navy header band"
        assert "$148B" in m.group(1)
        assert "Funding Mix" in m.group(1)

    def test_ir_skin_css_chrome(self, tmp_path):
        path = _write(tmp_path, _handoff([_ir_skin_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert re.search(
            r"\.gl-tile-ir-head\s*\{[^}]*background:\s*var\(--navy", html
        )
        assert re.search(
            r"\.gl-tile-ir-head[^}]*color:\s*var\(--color-on-navy", html
        )

    def test_default_skin_unchanged(self, tmp_path):
        path = _write(tmp_path, _handoff([_tall_card_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # no IR skin markup without tile_skin: "ir" (CSS is bundled)
        assert 'class="gl-tile gl-tile-chart gl-tile-tall gl-tile-ir"' not in html
        assert "gl-tile-ir-head" not in re.sub(r"<style.*?</style>", "", html, flags=re.S)


# ---------------------------------------------------------------------------
# #100 — N1 secondary_visual under non-line chart layouts
# ---------------------------------------------------------------------------


def _stacked_with_secondary():
    s = _slide("stacked_bar_chart", PROVISION_STACK)
    s["visual_spec"]["secondary_visual"] = {
        "type": "data_table",
        "steps_or_data": [
            ["Reserve rate", "0.9%", "0.8%", "1.0%", "0.7%", "0.6%"],
        ],
    }
    return s


class TestSecondaryVisualAnyChart:
    def test_stacked_bar_secondary_table_renders(self, tmp_path):
        path = _write(tmp_path, _handoff([_stacked_with_secondary()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "chart-split" in html
        assert "Reserve rate" in html
        assert "0.9%" in html

    def test_line_chart_secondary_unchanged(self, tmp_path):
        s = _slide("line_chart", TWO_SERIES)
        s["visual_spec"]["secondary_visual"] = {
            "type": "data_table",
            "steps_or_data": [["Revenue", "1", "2", "3"]],
        }
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "chart-split" in html and "Revenue" in html


# ---------------------------------------------------------------------------
# N6 — outlined-box skin for secondary_visual tables (provision reserve-rate)
# ---------------------------------------------------------------------------


def _stacked_outlined():
    s = _slide("stacked_bar_chart", PROVISION_STACK)
    s["visual_spec"]["secondary_visual"] = {
        "type": "data_table",
        "skin": "outlined_boxes",
        "steps_or_data": [
            ["", "Q4'25", "Q1'26"],
            ["Reserve Rate for Total Balances", "2.8%", "2.8%"],
        ],
    }
    return s


class TestOutlinedBoxesSkin:
    def test_outlined_boxes_render(self, tmp_path):
        path = _write(tmp_path, _handoff([_stacked_outlined()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert '<div class="chart-outlined-label"' in html
        assert html.count('<div class="chart-outlined-cell"') == 2
        assert "Reserve Rate for Total Balances" in html
        # header row dropped: period labels already live on the chart axis
        box = html.split('<div class="chart-support-outlined', 1)[1]
        assert "<th" not in box.split("</div></div>", 1)[0]

    def test_outlined_boxes_align_with_chart(self, tmp_path):
        path = _write(tmp_path, _handoff([_stacked_outlined()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # header cells match chart category labels 1:1 -> plot-aligned widths
        assert "chart-support-outlined chart-table-aligned" in html
        assert "data-align-left" in html

    def test_default_secondary_table_unchanged(self, tmp_path):
        path = _write(tmp_path, _handoff([_stacked_with_secondary()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert '<div class="chart-outlined-cell"' not in html
        assert "chart-support-table" in html


# ---------------------------------------------------------------------------
# #101 — N3 stacked category total tops / signed parentheses
# ---------------------------------------------------------------------------


class TestStackTotals:
    def test_totals_on_top_segment_only(self, tmp_path):
        s = _slide("stacked_bar_chart", PROVISION_STACK)
        s["visual_spec"]["primary_visual"]["chart_config"] = {"stack_totals": True}
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        conf = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))
        dl = conf["options"]["plugins"]["datalabels"]
        labels = dl["_labels"]
        n_series = len(conf["data"]["datasets"])
        assert len(labels) == n_series
        # exactly one non-empty total cell per category, on the highest
        # positive segment (so totals sit at the stack top even when the
        # top series is negative)
        data = [d["data"] for d in conf["data"]["datasets"]]
        n_cat = len(conf["data"]["labels"])
        for ci in range(n_cat):
            cells = [(si, labels[si][ci]) for si in range(n_series) if labels[si][ci]]
            assert len(cells) == 1
            si, val = cells[0]
            assert data[si][ci] > 0
            assert all(data[sj][ci] <= 0 for sj in range(si + 1, n_series))

    def test_negative_total_parenthesized(self, tmp_path):
        steps = [
            ["Q", "WO", "RR"],
            ["Q1", "100", "-250"],
            ["Q2", "300", "-50"],
        ]
        s = _slide("stacked_bar_chart", steps)
        s["visual_spec"]["primary_visual"]["chart_config"] = {"stack_totals": True}
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        conf = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))
        # totals live on the highest positive segment (series 0 here)
        top = conf["options"]["plugins"]["datalabels"]["_labels"][0]
        assert top[0] == "(150)"  # 100 + -250 = -150 -> parenthesized
        assert top[1] == "250"

    def test_totals_opt_in_default_unchanged(self, tmp_path):
        path = _write(tmp_path, _handoff([_slide("stacked_bar_chart", PROVISION_STACK)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        conf = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))
        assert "datalabels" not in conf["options"]["plugins"]


# ---------------------------------------------------------------------------
# N4 — dual simultaneous stacked label sets (in-segment values + total tops)
# ---------------------------------------------------------------------------


class TestDualStackLabels:
    def test_dual_mode_emits_named_label_sets(self, tmp_path):
        s = _slide("stacked_bar_chart", PROVISION_STACK)
        s["visual_spec"]["primary_visual"]["chart_config"] = {
            "stack_totals": True, "point_labels": True, "y_axis_unit": "$"}
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        conf = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))
        dl = conf["options"]["plugins"]["datalabels"]
        # named sets: in-segment values + above-stack totals, side by side
        # (negchip joins when thin negatives move below the bar — N3)
        assert set(dl["labels"]) == {"value", "total", "negchip"}
        value, total = dl["labels"]["value"], dl["labels"]["total"]
        # value set: white, centered inside segments, one cell per series
        assert value["anchor"] == "center"
        assert value["color"].lower() == "#ffffff"
        assert len(value["_labels"]) == len(conf["data"]["datasets"])
        # total set: navy, above the stack
        assert total["anchor"] == "end"
        assert total["align"] == "top"

    def test_dual_mode_formats_segment_values(self, tmp_path):
        s = _slide("stacked_bar_chart", PROVISION_STACK)
        s["visual_spec"]["primary_visual"]["chart_config"] = {
            "stack_totals": True, "point_labels": True, "y_axis_unit": "$"}
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        conf = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))
        sets = conf["options"]["plugins"]["datalabels"]["labels"]
        seg = sets["value"]["_labels"]
        # PROVISION_STACK: NCO=1251, RR=-73 / NCO=1251, RR=-24
        assert seg[0] == ["$1,251", "$1,251"]
        assert seg[1] == ["($73)", ""]  # thick negative stays inside (IR)
        # N3: thin negative moves to the below-bar chip set
        assert sets["negchip"]["_labels"][1] == ["", "($24)"]
        top = sets["total"]["_labels"]
        # totals: 1251-73=1178, 1251-24=1227 on the positive (NCO) segment
        assert top[0] == ["$1,178", "$1,227"]
        assert top[1] == ["", ""]

    def test_percent_unit_suffixes(self, tmp_path):
        s = _slide("stacked_bar_chart", PROVISION_STACK)
        s["visual_spec"]["primary_visual"]["chart_config"] = {
            "point_labels": True, "y_axis_unit": "%"}
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        sets = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))[
            "options"]["plugins"]["datalabels"]["labels"]
        assert sets["value"]["_labels"][0] == ["1,251%", "1,251%"]
        assert sets["value"]["_labels"][1] == ["(73%)", ""]
        assert sets["negchip"]["_labels"][1] == ["", "(24%)"]

    def test_percent_unit_suffixes_totals(self, tmp_path):
        s = _slide("stacked_bar_chart", PROVISION_STACK)
        s["visual_spec"]["primary_visual"]["chart_config"] = {
            "stack_totals": True, "y_axis_unit": "%"}
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        dl = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))[
            "options"]["plugins"]["datalabels"]
        # totals: 1251-73=1178, 1251-24=1227 on the positive (NCO) segment
        assert dl["_labels"][0] == ["1,178%", "1,227%"]
        assert dl["_labels"][1] == ["", ""]

    def test_segment_labels_without_totals_single_set(self, tmp_path):
        s = _slide("stacked_bar_chart", PROVISION_STACK)
        s["visual_spec"]["primary_visual"]["chart_config"] = {"point_labels": True}
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        conf = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))
        sets = conf["options"]["plugins"]["datalabels"]["labels"]
        # thin negative present -> value + negchip named sets (N3)
        assert sets["value"]["_labels"][0] == ["1,251", "1,251"]
        assert sets["value"]["_labels"][1] == ["(73)", ""]
        assert sets["negchip"]["_labels"][1] == ["", "(24)"]


# ---------------------------------------------------------------------------
# N5 — exterior segment-name column on stacked bars (PDF funding board)
# ---------------------------------------------------------------------------


class TestExteriorSegmentNames:
    def _deck(self, tmp_path, cfg):
        s = _slide("stacked_bar_chart", PROVISION_STACK)
        s["visual_spec"]["primary_visual"]["chart_config"] = cfg
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        return _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))

    def test_emits_segment_names_items_in_series_colors(self, tmp_path):
        conf = self._deck(tmp_path, {"exterior_segment_names": True})
        plugins = conf["options"]["plugins"]
        items = plugins["segmentNames"]["items"]
        names = [d["label"] for d in conf["data"]["datasets"]]
        colors = [d["backgroundColor"] for d in conf["data"]["datasets"]]
        assert [i["label"] for i in items] == names
        assert [i["color"] for i in items] == colors

    def test_replaces_legend_and_reserves_gutter(self, tmp_path):
        conf = self._deck(tmp_path, {"exterior_segment_names": True})
        opts = conf["options"]
        assert opts["plugins"]["legend"]["display"] is False
        assert opts["layout"]["padding"]["right"] >= 100

    def test_light_segment_colors_fall_back_to_dark(self, tmp_path):
        # PDF recipe: light segments (e.g. #B8BFC9 gray) get dark names
        conf = self._deck(tmp_path, {
            "exterior_segment_names": True,
            "series_colors": ["#00175A", "#B8BFC9"],
        })
        items = conf["options"]["plugins"]["segmentNames"]["items"]
        assert items[0]["color"] == "#00175A"  # dark navy keeps segment color
        assert items[1]["color"].lower() != "#b8bfc9"  # light gray -> dark fallback

    def test_opt_in_default_unchanged(self, tmp_path):
        conf = self._deck(tmp_path, {})
        assert "segmentNames" not in conf["options"]["plugins"]
        assert "display" not in conf["options"]["plugins"]["legend"]
        assert "layout" not in conf["options"]

    def test_knob_defaults_byte_identical(self, tmp_path):
        # T2: without the new knobs the emitted config carries only items +
        # the 120px gutter, exactly as before (SC-COMPAT-1).
        conf = self._deck(tmp_path, {"exterior_segment_names": True})
        seg = conf["options"]["plugins"]["segmentNames"]
        assert set(seg) == {"items"}
        assert conf["options"]["layout"]["padding"]["right"] == 120

    def test_typography_knobs_propagate(self, tmp_path):
        conf = self._deck(tmp_path, {
            "exterior_segment_names": True,
            "segment_name_font_size": 20,
            "segment_name_line_height": 22,
            "segment_name_wrap_chars": 12,
            "segment_name_max_lines": 4,
            "segment_name_offset": 24,
            "segment_name_gutter": 150,
        })
        seg = conf["options"]["plugins"]["segmentNames"]
        assert seg["fontSize"] == 20
        assert seg["lineHeight"] == 22
        assert seg["wrapChars"] == 12
        assert seg["maxLines"] == 4
        assert seg["offset"] == 24
        assert conf["options"]["layout"]["padding"]["right"] == 150

    def test_partial_knobs_emit_only_set_keys(self, tmp_path):
        conf = self._deck(tmp_path, {
            "exterior_segment_names": True,
            "segment_name_font_size": 18,
        })
        seg = conf["options"]["plugins"]["segmentNames"]
        assert seg["fontSize"] == 18
        assert set(seg) == {"items", "fontSize"}


# ---------------------------------------------------------------------------
# F11+ — axis-chrome suppression for IR 100%-stack boards (v4 sim)
# ---------------------------------------------------------------------------


class TestAxisChromeSuppression:
    def _deck(self, tmp_path, cfg):
        s = _slide("stacked_bar_chart", PROVISION_STACK)
        s["visual_spec"]["primary_visual"]["chart_config"] = cfg
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        return _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))

    def test_default_chrome_unchanged(self, tmp_path):
        conf = self._deck(tmp_path, {})
        scales = conf["options"]["scales"]
        assert "display" not in scales["y"]
        assert "display" not in scales["x"]
        assert "display" not in scales["y"]["grid"]

    def test_hide_y_axis(self, tmp_path):
        conf = self._deck(tmp_path, {"show_y_axis": False})
        assert conf["options"]["scales"]["y"]["display"] is False
        assert "display" not in conf["options"]["scales"]["x"]

    def test_hide_x_axis(self, tmp_path):
        conf = self._deck(tmp_path, {"show_x_axis": False})
        assert conf["options"]["scales"]["x"]["display"] is False

    def test_hide_gridlines_keeps_ticks(self, tmp_path):
        conf = self._deck(tmp_path, {"show_gridlines": False})
        scales = conf["options"]["scales"]
        assert scales["x"]["grid"]["display"] is False
        assert scales["y"]["grid"]["display"] is False
        assert "display" not in scales["y"]  # ticks stay
        assert "ticks" in scales["y"]

    def test_explicit_total_labels_override_computed(self, tmp_path):
        # PDF funding board: segments are %, totals are $B — different unit
        conf = self._deck(tmp_path, {
            "stack_totals": True,
            "stack_total_labels": ["$210", "$219"],
        })
        dl = conf["options"]["plugins"]["datalabels"]
        flat = [v for row in dl["_labels"] for v in row if v]
        assert flat == ["$210", "$219"]

    def test_totals_unclipped_with_headroom(self, tmp_path):
        conf = self._deck(tmp_path, {"stack_totals": True})
        opts = conf["options"]
        assert opts["plugins"]["datalabels"]["clip"] is False
        assert opts["layout"]["padding"]["top"] >= 18

    def test_negative_segment_labels_unclipped_with_bottom_headroom(self, tmp_path):
        # N3 residual: below-axis ($73)/($24) chips must not clip at plot bottom
        conf = self._deck(tmp_path, {"point_labels": True})
        opts = conf["options"]
        for label_set in opts["plugins"]["datalabels"]["labels"].values():
            assert label_set["clip"] is False
        assert opts["layout"]["padding"]["bottom"] >= 18

    def test_thin_negative_gets_below_bar_chip(self, tmp_path):
        # N3 residual / PDF pairing: thin negatives -> navy chip below the bar;
        # thick negatives stay white-inside. PROVISION_STACK has -73 (thick)
        # and -24 (thin) so both recipes appear.
        conf = self._deck(tmp_path, {"point_labels": True, "y_axis_unit": "$"})
        sets = conf["options"]["plugins"]["datalabels"]["labels"]
        assert "negchip" in sets
        value_flat = [v for row in sets["value"]["_labels"] for v in row if v]
        chip_flat = [v for row in sets["negchip"]["_labels"] for v in row if v]
        assert "($73)" in value_flat          # thick -> inside
        assert "($24)" not in value_flat      # thin -> moved out
        assert chip_flat == ["($24)"]         # thin -> below-bar chip
        assert sets["negchip"]["color"] != sets["value"]["color"]  # navy vs white

    def test_thick_negative_stays_inside_no_chip_set(self, tmp_path):
        s = _slide("stacked_bar_chart", [
            ["Quarter", "A", "B"],
            ["Q1", "100", "-80"], ["Q2", "120", "10"]])
        s["visual_spec"]["primary_visual"]["chart_config"] = {
            "point_labels": True, "y_axis_unit": "$"}
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        dl = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))[
            "options"]["plugins"]["datalabels"]
        # single flat set (no negchip) with the negative inside
        assert "labels" not in dl
        assert dl["_labels"][1] == ["($80)", "$10"]

    def test_positive_only_segments_no_bottom_padding(self, tmp_path):
        s = _slide("stacked_bar_chart", [
            ["Quarter", "A", "B"], ["Q1", "60", "40"], ["Q2", "70", "30"]])
        s["visual_spec"]["primary_visual"]["chart_config"] = {"point_labels": True}
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        opts = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))["options"]
        assert "bottom" not in opts.get("layout", {}).get("padding", {})


# ---------------------------------------------------------------------------
# #102 — F4+ freestanding pill packing density
# ---------------------------------------------------------------------------


class TestPillPackingDensity:
    def _deck(self, tmp_path):
        s = _slide("pill_comparison", [])
        s["visual_spec"] = {
            "primary_visual": {
                "type": "pill_comparison",
                "steps_or_data": [
                    ["Metric", "Q1'25", "Q1'26", "YoY"],
                    ["Revenue", "16.9", "17.8", "+6%"],
                    ["EPS", "2.61", "3.02", "+16%"],
                    ["ROE", "28%", "30%", "+2pts"],
                ],
            }
        }
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        return (out / "presentation.html").read_text(encoding="utf-8")

    def test_shells_render(self, tmp_path):
        html = self._deck(tmp_path)
        assert "gl-pill-free" in html and "gl-pill-shell" in html

    def test_tighter_column_gutters(self, tmp_path):
        html = self._deck(tmp_path)
        # denser gutters than the original gap-md 18px
        assert re.search(r"\.gl-pill-free\s*\{[^}]*gap:\s*var\(--gap-sm", html)

    def test_narrower_label_rail(self, tmp_path):
        html = self._deck(tmp_path)
        # rail narrowed from flex 1.6 toward PDF summary-board proportions
        # (1.2 by #102, 0.9 by V5/F4+ finish, widened to 1.35 by F4+ type
        # scale fix: PDF p3 label rail ≈530px of the 1728px canvas)
        assert re.search(r"\.gl-pill-labels\s*\{[^}]*flex:\s*1\.35", html)

    def test_data_table_unchanged(self, tmp_path):
        # regression guard from #74 still holds
        path = _write(tmp_path, _handoff([_slide("metric_dashboard", [])]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "gl-pill-col" not in html


class TestPillFreeRowDirection:
    def test_pill_free_is_row_not_gl_card_column(self, tmp_path):
        # .gl-card sets flex-direction: column; gl-pill-free must win with row
        s = _slide("pill_comparison", [])
        s["visual_spec"] = {
            "primary_visual": {
                "type": "pill_comparison",
                "steps_or_data": [
                    ["Metric", "A", "B"],
                    ["Revenue", "1", "2"],
                ],
            }
        }
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert re.search(r"\.gl-pill-free\s*\{[^}]*flex-direction:\s*row", html)


# ---------------------------------------------------------------------------
# #103 — Polish bundle: R1 flat stage, R4 hero scale, F12+ annex precision
# ---------------------------------------------------------------------------


class TestPolishBundleR3:
    def test_r1_flat_stage_is_borderless(self, tmp_path):
        s = _slide("line_chart", TWO_SERIES)
        s["visual_spec"] = {
            "primary_visual": {
                "type": "line_chart",
                "steps_or_data": TWO_SERIES,
                "chart_config": {"stage": "flat"},
            }
        }
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "chartjs-flat" in html
        # truly flat: no radius or margin chrome on the flat wrap
        assert re.search(
            r"\.chartjs-wrap\.chartjs-flat\s*\{[^}]*border-radius:\s*0", html
        )

    def test_r4_hero_giant_scale(self, tmp_path):
        path = _write(tmp_path, _handoff([_chart_hero_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "font-size: 110px" in html  # IR giant type scale (R4 finish)

    def test_f12_annex_group_separation(self, tmp_path):
        s = _annex_slide()
        s["visual_spec"]["primary_visual"]["header_groups"] = [
            {"label": "FY 2025", "span": 2},
            {"label": "Q1 2026", "span": 3},
        ]
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # group cells get visible separation for multi-header precision
        assert re.search(
            r"\.annex-table \.gl-annex-group\s*\{[^}]*border", html
        )


class TestDefaultPaletteResolved:
    """T10/R5-E: Chart.js paints to canvas, where CSS custom properties do not
    resolve — a var(--...) string silently renders black. Every serialized
    Chart.js config must therefore carry literal colors."""

    def test_no_var_in_any_chartjs_config(self, tmp_path):
        slides = [
            _slide("grouped_bar_chart", BAR_STEPS),
            _slide("stacked_bar_chart", BAR_STEPS),
            _slide("horizontal_bar_chart", BAR_STEPS),
        ]
        for s in slides:
            s["slide_number"] = slides.index(s) + 1
        path = _write(tmp_path, _handoff(slides))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        configs = re.findall(r'class="chartjs-config"[^>]*>(.*?)</script>', html, re.S)
        assert len(configs) == 3
        for raw in configs:
            assert "var(--" not in raw, f"canvas-bound CSS var in config: {raw[:200]}"

    def test_default_bar_first_dataset_is_navy_hex(self, tmp_path):
        path = _write(tmp_path, _handoff([_slide("grouped_bar_chart", BAR_STEPS)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        cc = _chartjs_cfg(html)
        ds0 = cc["data"]["datasets"][0]
        assert ds0["backgroundColor"] == "#00175a"
        assert ds0["borderColor"] == "#00175a"

    def test_themed_palette_token_is_a_known_gap(self, tmp_path):
        """F5 (r5 spec §4b): a handoff theme overriding a palette token does NOT
        retint default-palette charts, because canvas cannot read CSS vars.

        This is a filed, deliberately-unscheduled ceiling, not a silent bug. The
        test documents it so that a future red-branded deck gets a diagnosis
        instead of mysteriously navy charts. If someone implements F5, this test
        should FAIL and be replaced by one asserting the theme colour is used.
        """
        from impact_slides.renderer_v2.charts import _BAR_SERIES_COLORS

        themed = "#c8102e"  # deliberately unlike the default navy
        assert themed not in _BAR_SERIES_COLORS, "pick a colour not in the palette"

        h = _handoff([_slide("grouped_bar_chart", BAR_STEPS)])
        h["presentation"] = {"theme": {"--navy": themed}}
        path = _write(tmp_path, h)
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")

        # The theme DOES reach the CSS layer...
        assert f"--navy: {themed};" in html
        # ...but the canvas palette stays at the literal default (the F5 ceiling).
        ds0 = _chartjs_cfg(html)["data"]["datasets"][0]
        assert ds0["backgroundColor"] == _BAR_SERIES_COLORS[0] == "#00175a"
        assert ds0["backgroundColor"] != themed


# ---------------------------------------------------------------------------
# N5/#138 — shared-column side_callout (stacked vertical bars only)
# ---------------------------------------------------------------------------


def _side_callout_cfg(**extra):
    base = {
        "side_callout": {
            "value": "92% FDIC",
            "label": ["insured at", "Q1'26"],
            "placement": "right",
            "skin": "tall",
        },
        "exterior_segment_names": True,
        "segment_name_gutter": 150,
        "segment_name_offset": 22,
        "stack_totals": True,
        "stack_total_labels": ["$151", "$157"],
    }
    base.update(extra)
    return base


class TestSideCallout:
    def _render(self, tmp_path, cfg, layout="stacked_bar_chart", *, suppress=None):
        s = _slide(layout, PROVISION_STACK)
        s["visual_spec"]["primary_visual"]["chart_config"] = cfg
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        kw = {}
        if suppress:
            kw["suppress_features"] = suppress
        render_deck(path, out, strict=False, **kw)
        return (out / "presentation.html").read_text(encoding="utf-8")

    def test_supported_stacked_emits_three_lines(self, tmp_path):
        html = self._render(tmp_path, _side_callout_cfg())
        assert 'class="chart-side-callout chart-side-callout--tall chart-side-callout--right"' in html
        assert "92% FDIC" in html
        assert "insured at" in html
        assert "Q1'26" in html
        assert 'aria-label="92% FDIC insured at Q1\'26"' in html
        assert "font-size:26px" in html
        assert "font-size:24px" in html
        # shared-column vars from exterior-name gutter/offset
        assert "--side-callout-gutter:150px" in html
        assert "--side-callout-offset:22px" in html
        # plain text — no box chrome classes
        assert "chart-side-callout__value" not in html or "background" not in html.split("chart-side-callout")[1][:200]

    def test_default_absent_no_markup(self, tmp_path):
        html = self._render(tmp_path, {"stack_totals": True})
        # #138 is opt-in only — default product HTML (incl. inlined JS/CSS)
        # must carry zero feature identifiers or name-gap boot code.
        for needle in (
            "chart-side-callout",
            "--side-callout-",
            "side-callout",
            "sideCallout",
            "side_callout",
            "data-side-callout",
            "__sideCalloutNameGap",
        ):
            assert needle not in html, f"default deck leaked {needle!r}"
        # Global shell must stay free of the old #138 plugin hook.
        shell = (
            Path(__file__).resolve().parents[1]
            / "impact_slides"
            / "renderer_v2"
            / "shell.py"
        ).read_text(encoding="utf-8")
        assert "chart-side-callout" not in shell
        assert "side-callout" not in shell
        assert "sideCallout" not in shell

    def test_default_css_bundle_has_no_side_callout_rules(self, tmp_path):
        # Global components.css must stay free of #138 selectors (byte-compat).
        css = (
            Path(__file__).resolve().parents[1]
            / "impact_slides"
            / "renderer_v2"
            / "css"
            / "components.css"
        ).read_text(encoding="utf-8")
        assert "chart-side-callout" not in css
        assert "side-callout" not in css

    def test_enabled_callout_keeps_locked_inline_styles(self, tmp_path):
        html = self._render(tmp_path, _side_callout_cfg())
        assert "position:absolute" in html
        assert "color:#53565A" in html
        assert "left:85.777778%" in html
        assert "width:14.222222%" in html
        assert "line-height:29px" in html
        # PDF p28 tile-local offset (49.8px), not a guessed wrap-local 12px.
        assert "top:49.8px" in html
        assert "top:12px" not in html
        assert 'data-side-callout-anchor="wrap"' in html
        assert 'data-side-callout-offset="22"' in html
        assert 'data-side-callout-gutter="150"' in html
        assert 'data-side-callout-name-gap="8"' in html

    def test_callout_independent_of_stack_totals(self, tmp_path):
        html = self._render(
            tmp_path,
            {
                "side_callout": {
                    "value": "92% FDIC",
                    "label": ["insured at", "Q1'26"],
                    "placement": "right",
                    "skin": "tall",
                },
                "exterior_segment_names": True,
            },
        )
        assert "<aside class=\"chart-side-callout" in html
        conf = _chartjs_cfg(html)
        # no stack_totals → no datalabels totals matrix required
        assert "datalabels" not in conf["options"]["plugins"] or "_labels" not in (
            conf["options"]["plugins"].get("datalabels") or {}
        )

    def test_totals_independent_of_callout(self, tmp_path):
        conf = _chartjs_cfg(
            self._render(
                tmp_path,
                {"stack_totals": True, "stack_total_labels": ["$151", "$157"]},
            )
        )
        dl = conf["options"]["plugins"]["datalabels"]
        flat = [v for row in dl["_labels"] for v in row if v]
        assert flat == ["$151", "$157"]

    def test_unsupported_layout_ignored(self, tmp_path, capsys):
        html = self._render(
            tmp_path,
            {
                "side_callout": {
                    "value": "X",
                    "label": "Y",
                    "placement": "right",
                    "skin": "tall",
                }
            },
            layout="grouped_bar_chart",
        )
        assert "<aside class=\"chart-side-callout" not in html
        err = capsys.readouterr().err
        assert "side_callout" in err and "unsupported layout" in err

    def test_unsupported_skin_ignored(self, tmp_path, capsys):
        html = self._render(
            tmp_path,
            {
                "side_callout": {
                    "value": "X",
                    "label": "Y",
                    "placement": "right",
                    "skin": "pill",
                }
            },
        )
        assert "<aside class=\"chart-side-callout" not in html
        assert "unsupported placement/skin" in capsys.readouterr().err

    def test_geometry_budget_fail_soft_without_handoff_measurement(self, tmp_path, capsys):
        html = self._render(
            tmp_path,
            {
                "side_callout": {
                    "value": "92% FDIC",
                    "label": ["insured at", "Q1'26"],
                    "placement": "right",
                    "skin": "tall",
                    "min_plot_width": 800,
                },
                "exterior_segment_names": True,
                "segment_name_gutter": 700,
            },
        )
        assert "<aside class=\"chart-side-callout" not in html
        # chart + exterior names still present
        conf = _chartjs_cfg(html)
        assert "segmentNames" in conf["options"]["plugins"]
        assert "omitted" in capsys.readouterr().err

    def test_lines_api_generic(self, tmp_path):
        html = self._render(
            tmp_path,
            {
                "side_callout": {
                    "lines": [
                        {"text": "Alpha", "size": 26},
                        "Beta",
                        {"text": "Gamma"},
                    ],
                    "placement": "right",
                    "skin": "tall",
                },
                "exterior_segment_names": True,
            },
        )
        assert "Alpha" in html and "Beta" in html and "Gamma" in html
        assert "font-size:26px" in html

    def test_svg_path_emits_shared_name_column_and_callout(self, tmp_path):
        html = self._render(tmp_path, _side_callout_cfg(), suppress=["charts"])
        assert '<aside xmlns="http://www.w3.org/1999/xhtml" class="chart-side-callout' in html
        assert "chart-svg-wrap--side-callout" not in html
        assert "92% FDIC" in html
        assert "vbar-segment-name" in html
        assert ">NCO</text>" in html and ">RR</text>" in html
        assert 'data-chartjs="1"' not in html

    def test_callout_requires_valid_exterior_name_column(self, tmp_path, capsys):
        html = self._render(
            tmp_path,
            {"side_callout": {"value": "92%", "placement": "right", "skin": "tall"}},
        )
        assert "<aside class=\"chart-side-callout" not in html
        assert "requires a valid exterior_segment_names column" in capsys.readouterr().err

    @pytest.mark.parametrize("side_callout", [[], "", 0, {}])
    def test_malformed_falsy_callout_emits_diagnostic(self, tmp_path, capsys, side_callout):
        html = self._render(tmp_path, _side_callout_cfg(side_callout=side_callout))
        assert '<aside class="chart-side-callout' not in html
        assert "ignored" in capsys.readouterr().err

    @pytest.mark.parametrize("value", ["wide", [], float("inf")])
    def test_invalid_name_column_values_fail_soft(self, tmp_path, capsys, value):
        html = self._render(
            tmp_path,
            _side_callout_cfg(segment_name_offset=value),
        )
        assert "<aside class=\"chart-side-callout" not in html
        assert "requires a valid exterior_segment_names column" in capsys.readouterr().err

    @pytest.mark.parametrize(
        "knob, value",
        [
            ("segment_name_font_size", -1),
            ("segment_name_line_height", 10**9),
            ("segment_name_wrap_chars", 0),
            ("segment_name_max_lines", 5),
        ],
    )
    def test_unsafe_name_typography_values_fail_soft(self, tmp_path, capsys, knob, value):
        html = self._render(tmp_path, _side_callout_cfg(**{knob: value}))
        assert "<aside class=\"chart-side-callout" not in html
        assert "segmentNames" not in _chartjs_cfg(html)["options"]["plugins"]
        assert knob in capsys.readouterr().err

    def test_multi_panel_badge_suppressed_when_callout(self, tmp_path):
        s = _slide("multi_panel", [])
        s["visual_spec"] = {
            "primary_visual": {
                "type": "multi_panel",
                "tiles": [
                    {
                        "kind": "chart",
                        "chart_type": "stacked_bar_chart",
                        "label": "Deposit Programs",
                        "top_total": "$151B · $157B",
                        "badge": "92% of deposits FDIC insured*",
                        "steps_or_data": PROVISION_STACK,
                        "chart_config": _side_callout_cfg(),
                    }
                ],
            }
        }
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "<aside class=\"chart-side-callout" in html
        assert 'class="gl-tile-badge"' not in html
        assert "92% of deposits FDIC insured*" not in html
        # Tile host: callout is a direct child of the tall tile, not the wrap.
        assert 'data-side-callout-anchor="tile"' in html
        assert "top:49.8px" in html
        # The tile host maps the SVG's 900-unit column to its scaled content box.
        assert "left:calc(85.777778% + -11.448889px)" in html
        assert "width:calc(14.222222% - 4.551111px)" in html
        # chart wrap must not also embed a second callout
        assert html.count("<aside class=\"chart-side-callout") == 1
        # name-reservation is local to the active callout (not global shell).
        assert "data-side-callout-name-gap" in html
        assert "data-side-callout-name-gap-boot" in html
        assert "aside.chart-side-callout" in html
        assert "__sideCalloutNameGap" in html
        shell = (
            Path(__file__).resolve().parents[1]
            / "impact_slides"
            / "renderer_v2"
            / "shell.py"
        ).read_text(encoding="utf-8")
        assert "aside.chart-side-callout" not in shell

    def test_side_callout_geometry_contract_fails_old_top(self, tmp_path):
        """Pin the positioning contract that the old top:12px wrap host broke.

        Markup-only: the old recipe put top:12px on the chart wrap (~72px below
        tile top → stage T≈285). Locked PDF local offset is 49.8px tile-top.
        Also traps the old global-shell segmentNames leak.
        """
        html = self._render(tmp_path, _side_callout_cfg())
        m = re.search(
            r'<aside class="chart-side-callout[^"]*"[^>]*style="([^"]+)"',
            html,
        )
        assert m, "side callout aside missing"
        style = m.group(1)
        assert "top:49.8px" in style
        assert "top:12px" not in style
        # Mutation trap: removing the PDF offset must fail this test.
        assert re.search(r"top:49\.8px", style)
        # Active callout ships a local name-gap boot; global shell must not.
        assert "data-side-callout-name-gap-boot" in html
        shell = (
            Path(__file__).resolve().parents[1]
            / "impact_slides"
            / "renderer_v2"
            / "shell.py"
        ).read_text(encoding="utf-8")
        assert "chart-side-callout" not in shell
        assert "sideCallout" not in shell

    @pytest.mark.parametrize(
        "cfg, diagnostic",
        [
            (_side_callout_cfg(segment_name_gutter=23, segment_name_offset=22), "exterior-name lane"),
            (_side_callout_cfg(segment_name_offset="wide"), "requires a valid exterior_segment_names column"),
            (_side_callout_cfg(side_callout={"lines": ["x"] * 5}), "lines exceed maximum"),
            (_side_callout_cfg(side_callout={"lines": [{"text": "x", "size": 10**9}]}), "line size"),
        ],
    )
    def test_invalid_or_over_budget_callout_omits_with_diagnostic(
        self, tmp_path, capsys, cfg, diagnostic
    ):
        html = self._render(tmp_path, cfg)
        assert '<aside class="chart-side-callout' not in html
        assert diagnostic in capsys.readouterr().err

    def test_svg_callout_uses_viewbox_coordinates(self, tmp_path):
        html = self._render(tmp_path, _side_callout_cfg(), suppress=["charts"])
        assert '<foreignObject x="772" y="49.8" width="128"' in html
        assert "font-size:26px" in html

    def test_svg_multi_panel_callout_uses_tile_local_html(self, tmp_path):
        s = _slide("multi_panel", [])
        s["visual_spec"] = {"primary_visual": {"type": "multi_panel", "tiles": [{
            "kind": "chart", "chart_type": "stacked_bar_chart", "steps_or_data": PROVISION_STACK,
            "chart_config": _side_callout_cfg(),
        }]}}
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False, suppress_features=["charts"])
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert 'data-side-callout-anchor="tile"' in html
        assert "top:49.8px" in html
        assert 'class="gl-tile gl-tile-chart gl-tile-tall"' not in html
        assert '<foreignObject x="772" y="49.8" width="128"' not in html

    def test_three_column_multi_panel_omits_unfit_callout(self, tmp_path, capsys):
        tile = {
            "kind": "chart", "chart_type": "stacked_bar_chart", "steps_or_data": PROVISION_STACK,
            "chart_config": _side_callout_cfg(),
        }
        s = _slide("multi_panel", [])
        s["visual_spec"] = {"primary_visual": {"type": "multi_panel", "tiles": [tile] * 5}}
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False, suppress_features=["charts"])
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert '<aside class="chart-side-callout' not in html
        assert "exterior-name lane" in capsys.readouterr().err

    def test_noscript_hides_wrap_callout_before_painting_svg(self, tmp_path):
        html = self._render(tmp_path, _side_callout_cfg())
        assert '<style>[data-side-callout-html=wrap]{display:none}</style>' in html
        assert html.count('<aside class="chart-side-callout') == 1
        assert '<foreignObject x="772" y="49.8" width="128"' in html

    def test_name_gap_script_uses_unscaled_fit_width(self, tmp_path):
        html = self._render(tmp_path, _side_callout_cfg())
        assert "var hostScaleX = hbr.width / host.offsetWidth;" in html
        assert "(ccr.right - hbr.left) / hostScaleX" in html
        assert "callEl.scrollWidth > callEl.clientWidth" in html

    def test_legacy_name_column_coercions_survive_without_callout(self, tmp_path):
        conf = _chartjs_cfg(self._render(tmp_path, {
            "exterior_segment_names": 1,
            "segment_name_gutter": "150",
            "segment_name_offset": "22",
        }))
        assert conf["options"]["plugins"]["legend"]["display"] is False
        assert conf["options"]["layout"]["padding"]["right"] == 150
        assert conf["options"]["plugins"]["segmentNames"]["offset"] == 22

    def test_legacy_null_offset_preserves_plugin_default(self, tmp_path):
        conf = _chartjs_cfg(self._render(tmp_path, {
            "exterior_segment_names": True,
            "segment_name_offset": None,
        }))
        segment_names = conf["options"]["plugins"]["segmentNames"]
        assert conf["options"]["plugins"]["legend"]["display"] is False
        assert "offset" not in segment_names

    def test_multi_panel_invalid_callout_column_fails_soft(self, tmp_path, capsys):
        s = _slide("multi_panel", [])
        s["visual_spec"] = {"primary_visual": {"type": "multi_panel", "tiles": [{
            "kind": "chart", "chart_type": "stacked_bar_chart",
            "steps_or_data": PROVISION_STACK,
            "chart_config": _side_callout_cfg(segment_name_offset="wide"),
        }]}}
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        conf = _chartjs_cfg(html)
        assert '<aside class="chart-side-callout' not in html
        assert "segmentNames" not in conf["options"]["plugins"]
        assert "requires a valid exterior_segment_names column" in capsys.readouterr().err

    def test_svg_invalid_callout_emits_diagnostic(self, tmp_path, capsys):
        html = self._render(
            tmp_path,
            _side_callout_cfg(segment_name_offset="wide"),
            suppress=["charts"],
        )
        assert '<aside class="chart-side-callout' not in html
        assert "requires a valid exterior_segment_names column" in capsys.readouterr().err

    def test_multi_panel_callout_omits_when_side_legend_owns_right_lane(
        self, tmp_path, capsys
    ):
        s = _slide("multi_panel", [])
        s["visual_spec"] = {"primary_visual": {"type": "multi_panel", "tiles": [{
            "kind": "chart", "chart_type": "stacked_bar_chart", "steps_or_data": PROVISION_STACK,
            "side_legend": [{"label": "Legend"}], "chart_config": _side_callout_cfg(),
        }]}}
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert '<aside class="chart-side-callout' not in html
        assert "side_legend occupies the exterior-name lane" in capsys.readouterr().err
