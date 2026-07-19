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
