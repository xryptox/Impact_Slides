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
        ticks = cc["options"]["scales"]["y"]["ticks"]
        # effective domain is [to, max] — the break [from, to] is excluded
        assert ticks["min"] == 90
        assert ticks["max"] == 100
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
        assert cc["options"]["scales"]["y"]["ticks"]["min"] < 0

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
        # value axis is x in horizontal mode
        assert cc["options"]["scales"]["x"]["ticks"]["min"] == 90.0
        assert cc["options"]["scales"]["x"]["ticks"]["max"] == 100.0

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

    def test_no_callouts_unchanged(self, tmp_path):
        s = _slide("grouped_bar_chart", [{"label": "A", "value": 1}, {"label": "B", "value": 2}])
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # CSS is always bundled; assert no callout *markup* rendered
        assert 'class="chartjs-callout' not in html


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
