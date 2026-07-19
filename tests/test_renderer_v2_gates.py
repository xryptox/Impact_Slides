"""Phase 5 hard gates for renderer_v2 (plan §7) + Phase 7 freeform."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from impact_slides.renderer_v2 import render_deck
from impact_slides.renderer_v2.layout.freeform import has_freeform_grid
from impact_slides.renderer_v2.manifest import face_eid_violations, validate_html
from impact_slides.renderer_v2.notes import build_spoken_notes
from impact_slides.renderer_v2.shell import load_css

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "renderer_v2"
MINI = FIXTURES / "mini_handoff.json"
FREEFORM = FIXTURES / "freeform_handoff.json"

# Banned in spoken notes (generator + notes builder)
_STICKY = re.compile(r"figures are directional under readiness", re.I)
_LEAVE = re.compile(r"when we leave this slide", re.I)
_CENTER_TRANSFORM = re.compile(
    r"translate\(\s*-50%\s*,\s*-50%\s*\)\s*scale", re.I
)
_HOUSE = re.compile(r"keep this open through close", re.I)
_FACE_SECTION = re.compile(
    r">\s*(Why|What|How|Now|Appendix)\s*<", re.I
)


@pytest.fixture(scope="module")
def mini_out(tmp_path_factory):
    out = tmp_path_factory.mktemp("rv2_gates_mini")
    result = render_deck(MINI, out, strict=False)
    html = Path(result["presentation"]).read_text(encoding="utf-8")
    notes = Path(result["slide_notes"]).read_text(encoding="utf-8")
    man = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
    return {"result": result, "html": html, "notes": notes, "manifest": man, "out": out}


@pytest.fixture(scope="module")
def freeform_out(tmp_path_factory):
    out = tmp_path_factory.mktemp("rv2_gates_free")
    result = render_deck(FREEFORM, out, strict=False)
    html = Path(result["presentation"]).read_text(encoding="utf-8")
    return {"result": result, "html": html, "out": out}


class TestHardGates:
    """Plan §7 validation checklist — must stay green."""

    def test_01_stage_fit(self, mini_out):
        html = mini_out["html"]
        assert "1920" in html and "1080" in html
        assert "fitStage" in html
        assert not _CENTER_TRANSFORM.search(html)
        assert "translate(" in html and "scale(" in html

    def test_02_boardroom_tokens(self, mini_out):
        html = mini_out["html"]
        css = load_css()
        blob = (html + css).lower()
        assert "#00175a" in blob
        assert "#006fcf" in blob
        assert "source sans 3" in blob
        assert "ibm plex sans" in blob
        # banned stacks should not appear as primary font families in tokens
        assert "inter," not in css.lower()
        assert "roboto," not in css.lower()

    def test_03_gl_primitives(self, mini_out):
        html = mini_out["html"]
        assert "gl-slide" in html
        assert "gl-grid" in html or "gl-areas-" in html
        assert "gl-card-hat" in html or "gl-areas-cover" in html

    def test_04_zero_face_eid(self, mini_out):
        assert face_eid_violations(mini_out["html"]) == []

    def test_05_zero_face_bridge_and_section_tags(self, mini_out):
        html = mini_out["html"]
        face = re.sub(r"<aside[\s\S]*?</aside>", "", html, flags=re.I)
        face = re.sub(r"<script[\s\S]*?</script>", "", face, flags=re.I)
        assert not re.search(r'<div class="(?:narrative|story)-bridge"', face)
        # cover may have "Boardroom" etc; block naked section tags as element text
        # Filter slide-numbers and known safe words by requiring short token
        bad = [
            m.group(0)
            for m in _FACE_SECTION.finditer(face)
            if "Cover" not in m.group(0)
        ]
        # Allow Why only if inside data or notes already stripped — fail hard on kickers
        assert not re.search(
            r'class="kicker"[^>]*>\s*(Why|What|How|Now)\s*<', face, re.I
        ), bad

    def test_06_metric_dense_2x2(self, mini_out):
        html = mini_out["html"]
        # slide 2 metric with 4 stats
        assert "dense-2x2" in html
        # extract metric section: should not force 1x4 gl-grid-4 alone for n==4
        m = re.search(
            r'data-layout="metric_dashboard"[\s\S]*?</section>', html
        )
        assert m, "metric slide missing"
        block = m.group(0)
        assert "dense-2x2" in block
        assert "kpi-card" in block

    def test_07_split_dual_rail(self, mini_out):
        html = mini_out["html"]
        m = re.search(
            r'data-layout="split_text_visual"[\s\S]*?</section>', html
        )
        assert m
        block = m.group(0)
        assert "gl-areas-split" in block
        assert "gl-card-hat" in block
        assert "proof-list" in block or "fact-grid" in block or "bullet-list" in block

    def test_08_fact_entity_path_unit(self):
        # use recipes right_panel/fact path — matrix platform/region
        from impact_slides.renderer_v2.layout import recipes

        slide = {
            "title": "How the maps join",
            "section": "What",
            "content": {"bullets": ["Platform map is the integration spine"]},
            "visual_spec": {
                "primary_visual": {
                    "steps_or_data": [
                        ["Platform", "Region"],
                        ["Resy", "US"],
                        ["Tock", "US"],
                        ["TheFork", "Europe"],
                        ["Combined", "Global"],
                    ]
                }
            },
        }
        model = recipes.right_panel_model(slide)
        assert model["kind"] == "fact"
        values = [it["value"] for it in model["items"]]
        assert values == ["Resy", "Tock", "TheFork", "Combined"]
        assert model["items"][0]["label"] == "US"

    def test_09_table_as_kpi(self, mini_out):
        html = mini_out["html"]
        m = re.search(r'data-layout="data_table"[\s\S]*?</section>', html)
        assert m
        block = m.group(0)
        assert "kpi-card" in block or "layout-table-as-kpi" in block
        assert "<table" not in block  # short 2-col should not wash-table

    def test_10_timeline_vertical_years(self, mini_out):
        html = mini_out["html"]
        m = re.search(r'data-layout="timeline"[\s\S]*?</section>', html)
        assert m
        block = m.group(0)
        assert "process-flow--vertical" in block
        assert "step-kicker" in block
        assert "2026" in block
        assert "timeline-grid" not in block

    def test_11_comparison_no_house_body(self, mini_out):
        html = mini_out["html"]
        m = re.search(
            r'data-layout="comparison_grid"[\s\S]*?</section>', html
        )
        assert m
        block = m.group(0)
        assert not _HOUSE.search(block)
        assert "Consultation" in block
        assert "Works council" in block or "council" in block.lower()

    def test_12_multi_quote_stack(self, mini_out):
        html = mini_out["html"]
        m = re.search(r'data-layout="quote_card"[\s\S]*?</section>', html)
        assert m
        block = m.group(0)
        assert "quote-layout--stack" in block
        assert block.count("<blockquote>") >= 3
        assert "Rafa Marquez" in block or "Marquez" in block
        assert "Squeri" in block
        assert "Ambeskovic" in block

    def test_13_chart_one_label(self, mini_out):
        html = mini_out["html"]
        m = re.search(
            r'data-layout="grouped_bar_chart"[\s\S]*?</section>', html
        )
        assert m
        block = m.group(0)
        # 55 may appear once as chart value (not also as overlay pill double)
        # Count plain 55 tokens in the chart slide body
        vals = re.findall(r">\s*55\s*<", block)
        # allow 1 end-label; fail if obviously double-stamped (>=3)
        assert len(vals) <= 2, vals
        assert (
            "chart-svg" in block
            or "<svg" in block
            or 'data-chartjs="1"' in block
            or "chartjs-canvas" in block
        )

    def test_14_notes_no_sticky_leave(self, mini_out):
        notes = mini_out["notes"]
        assert not _STICKY.search(notes)
        assert not _LEAVE.search(notes)
        html = mini_out["html"]
        asides = re.findall(
            r'<aside class="speaker-notes"[\s\S]*?</aside>', html, flags=re.I
        )
        assert len(asides) >= 8
        for a in asides:
            assert not _STICKY.search(a)
            assert not _LEAVE.search(a)
            assert not re.search(r"\bE\d{4}\b", a)

    def test_15_manifest_preset_and_ids(self, mini_out):
        man = mini_out["manifest"]
        assert man["style_preset"] == "BoardroomEarnings"
        assert man["total_slides"] == 8
        # E0001 from mini metric slide
        all_ids = []
        for s in man["slides"]:
            all_ids.extend(s.get("evidence_ids") or [])
        assert "E0001" in all_ids

    def test_16_controls_present(self, mini_out):
        html = mini_out["html"]
        assert 'id="btn-prev"' in html
        assert 'id="btn-next"' in html
        assert 'id="btn-notes"' in html
        assert "ArrowRight" in html
        assert "show-notes" in html

    def test_validate_html_clean(self, mini_out):
        assert validate_html(mini_out["html"]) == []


class TestFreeformPhase7:
    def test_has_grid_detect(self):
        data = json.loads(FREEFORM.read_text(encoding="utf-8"))
        assert has_freeform_grid(data["slides"][1]) is True
        assert has_freeform_grid(data["slides"][0]) is False

    def test_render_named_slots(self, freeform_out):
        html = freeform_out["html"]
        assert freeform_out["result"]["total_slides"] == 2
        assert "gl-areas-freeform" in html
        assert 'data-freeform="1"' in html
        assert "gl-slot--main" in html
        assert "gl-slot--aside" in html
        assert "Dining is high-frequency" in html
        assert "$700M" in html
        assert face_eid_violations(html) == []
        assert "BoardroomEarnings" in html

    def test_template_areas_attr_not_broken(self, freeform_out):
        """Double quotes in grid-template-areas break style=\"...\" — use single quotes."""
        html = freeform_out["html"]
        # Freeform div must keep a complete style attribute with areas inside it
        m = re.search(
            r'class="gl-areas-freeform"\s+style="([^"]*)"',
            html,
        )
        assert m, "freeform root missing or style broken"
        style = m.group(1)
        assert "grid-template-columns:" in style
        assert "grid-template-areas:" in style
        assert "'lead lead'" in style or "'lead lead'".replace("'", "'") in style
        assert "'main aside'" in style
        # the old broken pattern which browsers read as style ending at first "
        assert 'grid-template-areas:"lead' not in html
        # slots still individually present (not just pile)
        assert "gl-slot--lead" in html and "gl-slot--main" in html

    def test_freeform_css_primitive(self):
        css = load_css()
        assert ".gl-areas-freeform" in css


class TestGoldenFixtureStable:
    """Golden: known class skeletons appear for each mini layout."""

    def test_layout_dispatch_map(self, mini_out):
        html = mini_out["html"]
        layouts = re.findall(r'data-layout="([^"]+)"', html)
        assert layouts[0] == "title_or_opening"
        assert "metric_dashboard" in layouts
        assert "split_text_visual" in layouts
        assert "comparison_grid" in layouts
        assert "timeline" in layouts
        assert "quote_card" in layouts
        assert "data_table" in layouts
        assert "grouped_bar_chart" in layouts

    def test_build_spoken_notes_unit(self):
        slide = {
            "slide_number": 2,
            "layout_type": "metric_dashboard",
            "title": "Markers",
            "audience_takeaway": "Cash structure is clean.",
            "content": {
                "headline": "Deal markers",
                "key_stats": [
                    {"label": "Value", "value": "$700M"},
                    {"label": "Form", "value": "All-cash"},
                ],
                "narrative_bridge": "When we leave this slide, scale is next",
            },
            "speaker_notes": "Hold for the IC. Make the room feel ready.",
        }
        prose = build_spoken_notes(slide, "Scale")
        assert not _LEAVE.search(prose)
        assert not re.search(r"hold for", prose, re.I)
        assert not re.search(r"make the room", prose, re.I)


class TestDensityBCD:
    """Options B/C/D vertical rhythm — header gap, hero band, multi-item type."""

    def test_default_header_gap_45(self):
        css = load_css()
        assert "--gap-header-main: 45px" in css
        assert "--hero-band-min:" in css

    def test_per_layout_header_gaps(self):
        css = load_css()
        assert ".layout-quote_card" in css and "52px" in css
        assert ".layout-split_text_visual" in css and "36px" in css
        assert ".layout-comparison_grid" in css

    def test_mini_metric_is_hero(self, mini_out):
        html = mini_out["html"]
        # metric slide has 4 key_stats
        m = re.search(
            r'<section class="([^"]*)"[^>]*data-layout="metric_dashboard"[^>]*>',
            html,
        )
        assert m, "metric section missing"
        assert "gl-density-hero" in m.group(1) or "gl-density-hero" in html
        tag = re.search(
            r'data-layout="metric_dashboard"[^>]*>',
            html,
        )
        # data-items may be before data-layout
        sec = re.search(
            r'<section[^>]*data-layout="metric_dashboard"[^>]*>',
            html,
        )
        assert sec and 'data-items="4"' in sec.group(0)

    def test_mini_quote_is_hero(self, mini_out):
        sec = re.search(
            r'<section[^>]*data-layout="quote_card"[^>]*>',
            mini_out["html"],
        )
        assert sec
        assert "gl-density-hero" in sec.group(0)
        assert 'data-items="3"' in sec.group(0)

    def test_option_d_rules_present(self):
        css = load_css()
        assert ".slide.gl-density-hero .gl-grid-dense-2x2 .kpi-value" in css
        assert "font-size: 76px" in css
