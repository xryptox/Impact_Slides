"""Tests for runtime theme injection (T2 #10).

render_deck(..., theme={"--color-primary": "#1a3a6e"}) should emit a
self-contained <style> block after base CSS that overrides :root tokens.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from impact_slides.renderer_v2.cli import render_deck


MINI_HANDOFF = {
    "title": "Theme Test",
    "readiness_score": 0.85,
    "quality_flags": [],
    "slides": [
        {
            "slide_number": 1,
            "layout_type": "title_or_opening",
            "title": "Hello",
            "content": {"headline": "Theme Demo"},
            "speaker_notes": "Notes.",
        }
    ],
}


def _write_handoff(tmp_path: Path) -> Path:
    p = tmp_path / "handoff.json"
    p.write_text(json.dumps(MINI_HANDOFF), encoding="utf-8")
    return p


class TestThemeInjection:
    def test_default_no_theme_block(self, tmp_path):
        handoff = _write_handoff(tmp_path)
        render_deck(handoff, tmp_path / "out")
        html = (tmp_path / "out" / "presentation.html").read_text(encoding="utf-8")
        assert html.count("<style>") == 1  # only base CSS block

    def test_theme_override_block_present(self, tmp_path):
        handoff = _write_handoff(tmp_path)
        render_deck(handoff, tmp_path / "out", theme={"--color-primary": "#ff0000"})
        html = (tmp_path / "out" / "presentation.html").read_text(encoding="utf-8")
        assert html.count("<style>") == 2  # base CSS + theme override
        assert ":root {" in html
        assert "--color-primary: #ff0000;" in html

    def test_theme_multiple_tokens(self, tmp_path):
        handoff = _write_handoff(tmp_path)
        render_deck(
            handoff,
            tmp_path / "out",
            theme={"--color-primary": "#1a3a6e", "--font-display": "Inter, sans-serif"},
        )
        html = (tmp_path / "out" / "presentation.html").read_text(encoding="utf-8")
        assert "--color-primary: #1a3a6e;" in html
        assert "--font-display: Inter, sans-serif;" in html

    def test_theme_invalid_key_passed_through(self, tmp_path):
        """Unknown keys are emitted as-is — browser handles invalid CSS."""
        handoff = _write_handoff(tmp_path)
        render_deck(handoff, tmp_path / "out", theme={"--bogus": "red"})
        html = (tmp_path / "out" / "presentation.html").read_text(encoding="utf-8")
        assert "--bogus: red;" in html

    def test_theme_affects_card_color(self, tmp_path):
        """Theme override should appear after base CSS so it wins via cascade."""
        handoff = _write_handoff(tmp_path)
        render_deck(handoff, tmp_path / "out", theme={"--navy": "#123456"})
        html = (tmp_path / "out" / "presentation.html").read_text(encoding="utf-8")
        # Verify the theme block comes after base CSS
        base_css_end = html.find("</style>")
        theme_start = html.find("--navy: #123456")
        assert theme_start > base_css_end

    def test_backward_compatibility_no_theme_param(self, tmp_path):
        """render_deck without theme= should be identical to before."""
        handoff = _write_handoff(tmp_path)
        result = render_deck(handoff, tmp_path / "out")
        assert result["total_slides"] == 1
        assert result["ok"]  # validation passes
