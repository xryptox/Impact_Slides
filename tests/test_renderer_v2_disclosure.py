"""P5 native progressive disclosure.

Spec: wiki/SPEC_renderer_v2_p5_native_disclosure.md
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from impact_slides.renderer_v2 import render_deck
from impact_slides.renderer_v2.disclosure import (
    DisclosureError,
    build_disclosure_html,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "renderer_v2"
DISCLOSURE = FIXTURES / "disclosure_handoff.json"
MINI = FIXTURES / "mini_handoff.json"


def _base_slide(**kwargs):
    s = {
        "slide_number": 1,
        "layout_type": "split_text_visual",
        "title": "T",
        "content": {"headline": "H"},
        "speaker_notes": "N",
    }
    s.update(kwargs)
    return s


class TestDisclosureUnit:
    def test_detail_emits_details_summary(self):
        html = build_disclosure_html(
            _base_slide(
                disclosure={
                    "pattern": "detail",
                    "panels": [{"title": "More", "body": "Body text"}],
                }
            )
        )
        assert 'data-disclosure="detail"' in html
        assert "<details" in html
        assert "<summary>More</summary>" in html
        assert "Body text" in html

    def test_accordion_multi_section(self):
        html = build_disclosure_html(
            _base_slide(
                disclosure={
                    "pattern": "accordion",
                    "panels": [
                        {"title": "A", "body": "one"},
                        {"title": "B", "body": "two"},
                    ],
                }
            )
        )
        assert 'data-disclosure="accordion"' in html
        assert html.count("<details") == 2
        assert "<summary>A</summary>" in html
        assert "<summary>B</summary>" in html

    def test_tabs_radio_css(self):
        html = build_disclosure_html(
            _base_slide(
                disclosure={
                    "pattern": "tabs",
                    "default_index": 1,
                    "panels": [
                        {"title": "One", "body": "first"},
                        {"title": "Two", "body": "second"},
                    ],
                }
            )
        )
        assert 'data-disclosure="tabs"' in html
        assert 'type="radio"' in html
        assert "checked" in html
        assert "first" in html and "second" in html
        assert "alpine" not in html.lower()
        assert "swiper" not in html.lower()

    def test_escapes_author_text(self):
        html = build_disclosure_html(
            _base_slide(
                disclosure={
                    "pattern": "detail",
                    "panels": [{"title": "<b>X</b>", "body": "<script>alert(1)</script>"}],
                }
            )
        )
        assert "<script>" not in html
        assert "&lt;script&gt;" in html or "&lt;b&gt;" in html

    def test_unknown_pattern_fails_closed(self):
        with pytest.raises(DisclosureError, match="unknown disclosure pattern"):
            build_disclosure_html(
                _base_slide(disclosure={"pattern": "carousel", "panels": [{"body": "x"}]})
            )


class TestDisclosureRender:
    def test_fixture_all_three_patterns(self, tmp_path):
        out = tmp_path / "out"
        render_deck(DISCLOSURE, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert 'data-disclosure="detail"' in html
        assert 'data-disclosure="accordion"' in html
        assert 'data-disclosure="tabs"' in html
        assert "gl-disclosure" in html
        # No third-party disclosure runtimes (avoid matching CSS comments).
        assert "alpinejs" not in html.lower()
        assert "cdn.jsdelivr" not in html.lower() or "swiper" not in html.lower()
        assert "x-data" not in html
        assert "fonts.googleapis.com" not in html

    def test_no_disclosure_unchanged_compat(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "data-disclosure=" not in html

    def test_unknown_pattern_render_fails(self, tmp_path):
        handoff = {
            "title": "Bad",
            "slides": [
                _base_slide(disclosure={"pattern": "wizard", "panels": [{"body": "x"}]})
            ],
        }
        path = tmp_path / "h.json"
        path.write_text(json.dumps(handoff), encoding="utf-8")
        with pytest.raises(ValueError, match="unknown disclosure pattern"):
            render_deck(path, tmp_path / "out", strict=False)

    def test_css_chrome_present(self, tmp_path):
        out = tmp_path / "out"
        render_deck(DISCLOSURE, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert ".gl-disclosure" in html
        assert ".gl-tab-list" in html
