"""P3 Chart.js path + SVG fallback.

Spec: wiki/SPEC_renderer_v2_p3_chartjs.md
"""
from __future__ import annotations

import json
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
        ticks = cc["options"]["scales"]["y"]["ticks"]
        assert ticks.get("min") == 0
        assert ticks.get("max") == 15
        assert ticks.get("stepSize") == 5

    def test_chartjs_explicit_min_max(self, tmp_path):
        cfg = {"y_axis_min": 0, "y_axis_max": 20}
        path = _write(tmp_path, _handoff([_line_slide_with_cfg(cfg, TWO_SERIES)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        cc = _chartjs_cfg(html)
        ticks = cc["options"]["scales"]["y"]["ticks"]
        assert ticks.get("min") == 0
        assert ticks.get("max") == 20

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
        d0 = cc["data"]["datasets"][0]
        assert d0.get("pointLabels") == ["8%", "10%", "12%"]
        assert cc["options"]["plugins"]["datalabels"].get("display") is True

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
        # y-domain reaches below zero
        assert cc["options"]["scales"]["y"]["ticks"]["min"] < 0

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
        assert cc["options"]["scales"]["y"]["ticks"]["min"] == -200.0
        assert cc["options"]["scales"]["y"]["ticks"]["max"] == 1500.0

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
        assert "Millennial/Gen-Z" in html and "66%" in html
        assert "Fee-Paying" in html and "73%" in html
        assert "chart_hero_dual" in html or "layout-chart-hero" in html

    def test_no_chart_still_renders_hero(self, tmp_path):
        path = _write(tmp_path, _handoff([_chart_hero_slide(chart=False)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "gl-hero-stack" in html
        assert "66%" in html


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
