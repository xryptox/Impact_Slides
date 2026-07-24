"""Renderer v2 — gridlines foundation + Boardroom recipes (Phases 0–4)."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from impact_slides.renderer_v2 import __version__, render_deck
from impact_slides.renderer_v2.layout import recipes
from impact_slides.renderer_v2.manifest import face_eid_violations, validate_html
from impact_slides.renderer_v2.shell import load_css
from impact_slides.renderer_v2.strip import chosen_dek, clean_quote_body, esc, strip_eids

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "renderer_v2"


@pytest.fixture(scope="module")
def mini_handoff(tmp_path_factory) -> Path:
    """8-slide mini handoff covering core + chart layouts."""
    data = {
        "presentation": {
            "title": "Gridlines Mini Deck",
            "subtitle": "Boardroom v2 smoke",
            "audience": "IC",
            "primary_goal": "Validate renderer v2 primitives",
            "readiness_score": 40,
            "quality_flags": [],
        },
        "slides": [
            {
                "slide_number": 1,
                "layout_type": "title_or_opening",
                "packing_mode": "cover-led",
                "title": "Gridlines Mini Deck",
                "section": "Cover",
                "content": {
                    "headline": "Validate renderer v2 primitives",
                    "subtitle": "Boardroom v2 smoke",
                    "bullets": [],
                    "key_stats": [],
                    "body_text": "",
                    "so_what": "",
                    "narrative_bridge": "Proof lands next",
                },
                "evidence_sources": [],
                "speaker_notes": "Open with the thesis, not a readiness score.",
            },
            {
                "slide_number": 2,
                "layout_type": "metric_dashboard",
                "packing_mode": "stat-led",
                "title": "Deal markers",
                "content": {
                    "subtitle": "Four signals",
                    "headline": "$700M all-cash",
                    "key_stats": [
                        {"label": "Deal value", "value": "$700M"},
                        {"label": "Structure", "value": "All-cash"},
                        {"label": "Close", "value": "End 2026"},
                        {"label": "Form", "value": "Put-option"},
                    ],
                    "so_what": "Cash removes equity dilution risk.",
                    "narrative_bridge": "Scale still has to pencil.",
                },
                "evidence_sources": [{"id": "E0001", "source_file": "deal.pdf"}],
                "visual_spec": {"primary_visual": {"type": "dashboard", "steps_or_data": []}},
            },
            {
                "slide_number": 3,
                "layout_type": "split_text_visual",
                "packing_mode": "argument-led",
                "title": "Where dining fits",
                "content": {
                    "subtitle": "Engagement engine",
                    "bullets": [
                        "Dining is high frequency",
                        "Europe was the gap",
                        "TheFork closes the map",
                    ],
                    "body_text": "TheFork extends the closed loop into Europe.",
                    "so_what": "",
                    "supporting_points": [],
                },
                "visual_spec": {
                    "primary_visual": {
                        "type": "icon_grid",
                        "steps_or_data": [
                            "Dining = high-frequency engagement",
                            "50,000+ restaurants already live",
                            "Card spend follows discovery",
                        ],
                    }
                },
                "evidence_sources": [],
            },
            {
                "slide_number": 4,
                "layout_type": "comparison_grid",
                "packing_mode": "argument-led",
                "title": "Open risks",
                "content": {
                    "bullets": [
                        "Works council path is live",
                        "Antitrust clocks are open",
                        "Integration depth is still thin",
                        "Tripadvisor rails still run ops",
                    ],
                },
                "visual_spec": {
                    "primary_visual": {
                        "type": "comparison_grid",
                        "steps_or_data": [
                            "Consultation",
                            "Regulatory",
                            "Integration",
                            "Closing",
                        ],
                    }
                },
            },
            {
                "slide_number": 5,
                "layout_type": "timeline",
                "packing_mode": "sequence-led",
                "title": "Path to Close",
                "content": {"so_what": "Four gates separate announcement from close."},
                "visual_spec": {
                    "primary_visual": {
                        "type": "vertical_timeline",
                        "steps_or_data": [
                            "Put-option exercised",
                            "Labor consultation",
                            "Regulatory/antitrust approvals",
                            "Close before end 2026",
                        ],
                    }
                },
            },
            {
                "slide_number": 6,
                "layout_type": "quote_card",
                "packing_mode": "voice-led",
                "title": "Voices on the deal",
                "content": {"subtitle": "Three decision-makers", "so_what": "Shared thesis on dining."},
                "visual_spec": {
                    "primary_visual": {
                        "type": "quote_card",
                        "steps_or_data": [
                            {
                                "text": '"Dining is central," said Rafa Marquez, President of International Card Services',
                                "attribution": "E0135",
                            },
                            {
                                "text": '"We are deepening Tripadvisor," said Stephen Squeri, Chairman and CEO',
                                "attribution": "E0155",
                            },
                            {
                                "text": '"Restaurants thrive here," said Almir Ambeskovic, CEO of TheFork',
                                "attribution": "E0136",
                            },
                        ],
                    }
                },
            },
            {
                "slide_number": 7,
                "layout_type": "data_table",
                "packing_mode": "stat-led",
                "title": "European scale",
                "content": {"subtitle": "Fingerprint of the network"},
                "visual_spec": {
                    "primary_visual": {
                        "type": "data_table",
                        "steps_or_data": [
                            ["Metric", "Value"],
                            ["Countries", "11"],
                            ["Restaurants", "50,000+"],
                            ["Venues post-deal", "75,000"],
                            ["Announced", "June 15 2026"],
                        ],
                    }
                },
            },
            {
                "slide_number": 8,
                "layout_type": "grouped_bar_chart",
                "packing_mode": "stat-led",
                "title": "Engagement by cohort",
                "content": {"so_what": "Gen-Z density is the growth wedge."},
                "visual_spec": {
                    "primary_visual": {
                        "type": "grouped_bar_chart",
                        "steps_or_data": [
                            ["Cohort", "Index"],
                            ["Gen-Z", "55"],
                            ["Millennial", "42"],
                            ["Gen-X", "28"],
                        ],
                    }
                },
            },
        ],
    }
    root = tmp_path_factory.mktemp("rv2")
    path = root / "builder_handoff.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class TestStrip:
    def test_esc(self):
        out = esc('<x> & "y"')
        assert "&lt;x&gt;" in out
        assert "&amp;" in out
        assert "&quot;" in out

    def test_strip_eids(self):
        assert "deal" in strip_eids("big deal (E0140, E0141)").lower()
        assert "E0140" not in strip_eids("big deal (E0140)")

    def test_strip_eids_preserves_negative_numerals(self):
        # #87/F3: a leading minus on a string numeral is a numeric sign,
        # not a separator left over from EID removal.
        assert strip_eids("-73") == "-73"
        assert strip_eids("-24") == "-24"
        assert strip_eids("-$24") == "-$24"
        assert strip_eids("-1.5%") == "-1.5%"
        assert strip_eids("- 73") == "- 73"

    def test_strip_eids_still_strips_separator_dashes(self):
        assert strip_eids("Revenue -") == "Revenue"
        assert strip_eids("- Revenue") == "Revenue"
        assert strip_eids("Revenue (E0140) -") == "Revenue"
        assert strip_eids("-") == ""
        assert strip_eids("(E0140)") == ""

    def test_chosen_dek_prefers_subtitle(self):
        slide = {"content": {"subtitle": "Framing", "headline": "$700M all-cash"}}
        assert chosen_dek(slide) == "Framing"

    def test_clean_quote_body(self):
        text = '"Dining is central," said Rafa Marquez, President of X'
        body = clean_quote_body(text)
        assert "Dining is central" in body
        assert "said Rafa" not in body


class TestCssFoundation:
    def test_gl_primitives_present(self):
        css = load_css()
        for token in (
            ".gl-slide",
            ".gl-grid-2",
            ".gl-grid-dense-2x2",
            ".gl-areas-split",
            ".gl-areas-cover",
            ".gl-card-hat",
            "#00175a",
            "#006fcf",
        ):
            assert token.lower() in css.lower()


class TestRecipesUnit:
    def test_pair_comparison_steps_with_bullets(self):
        slide = {
            "content": {"bullets": ["A body", "B body"]},
            "visual_spec": {
                "primary_visual": {"steps_or_data": ["Alpha", "Beta"]}
            },
        }
        pairs = recipes.pair_comparison(slide)
        assert pairs[0] == ("Alpha", "A body")
        assert all("keep this open" not in b.lower() for _, b in pairs)

    def test_table_as_kpi(self):
        rows = [["Metric", "Value"], ["A", "1"], ["B", "2"], ["C", "3"], ["D", "4"]]
        assert recipes.table_as_kpi(rows)

    def test_split_step_copy_end_year(self):
        k, t = recipes.split_step_copy("Close before end 2026")
        assert "2026" in k
        assert "Close" in t

    def test_path_to_close_overrides(self):
        steps = recipes.apply_timeline_year_overrides(
            "Path to Close",
            ["Put-option exercised", "Labor consultation", "Regulatory", "Close"],
        )
        assert all(re.search(r"\d{4}", s) for s in steps)


class TestRenderDeck:
    def test_mini_deck(self, mini_handoff, tmp_path):
        out = tmp_path / "out"
        result = render_deck(mini_handoff, out, strict=False)
        assert result["total_slides"] == 8
        html = Path(result["presentation"]).read_text(encoding="utf-8")
        assert "BoardroomEarnings" in html
        assert "gl-slide" in html
        assert "gl-areas-cover" in html
        assert "dense-2x2" in html
        assert "gl-areas-split" in html
        assert "comparison-card" in html
        assert "quote-layout--stack" in html
        assert "process-flow--vertical" in html
        assert "layout-table-as-kpi" in html or "kpi-card" in html
        assert face_eid_violations(html) == []
        assert not re.search(r'<div class="(?:narrative|story)-bridge"', html)
        assert "fitStage" in html
        # notes + manifest artifacts
        assert Path(result["slide_notes"]).exists()
        man = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
        assert man["style_preset"] == "BoardroomEarnings"
        assert man["total_slides"] == 8

    def test_validate_html_tokens(self, mini_handoff, tmp_path):
        out = tmp_path / "out2"
        render_deck(mini_handoff, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        errs = validate_html(html)
        assert errs == [], errs

    def test_version(self):
        assert __version__.startswith("2.")
