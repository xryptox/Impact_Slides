"""P2 token contract tests via render_deck.

Spec: wiki/SPEC_renderer_v2_p2_open_props_tokens.md
Owner: wiki/SPEC_renderer_v2_tokens_owner.md
"""
from __future__ import annotations

import json
from pathlib import Path

from impact_slides.renderer_v2 import render_deck

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "renderer_v2"
MINI = FIXTURES / "mini_handoff.json"

# Deliberately non-curated Open Props kitchen-sink names we do not ship.
_KITCHEN_SINK = (
    "--font-flat",
    "--ease-elastic-in-out",
    "--ease-elastic-out",
    "--gray-0",
    "--gray-12",
    "--size-content-1",
    "--size-header-1",
)


class TestTokenContract:
    def test_boardroom_brand_markers_present(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "#00175a" in html or "--navy" in html
        assert "#006fcf" in html or "--blue" in html
        assert "Source Sans 3" in html
        assert "IBM Plex Sans" in html

    def test_curated_primitive_scales_present(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "--size-1:" in html
        assert "--size-15:" in html
        assert "--radius-1:" in html
        assert "--radius-round:" in html
        assert "--shadow-1:" in html
        assert "--shadow-6:" in html

    def test_semantic_aliases_present(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "--color-primary:" in html
        assert "--space-md:" in html
        assert "--radius-sm:" in html
        assert "--shadow-sm:" in html

    def test_theme_override_still_works(self, tmp_path):
        out = tmp_path / "out"
        render_deck(
            MINI, out, strict=False, theme={"--color-primary": "#ff0000"}
        )
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert html.count("<style>") >= 2
        assert "--color-primary: #ff0000" in html

    def test_tokens_not_feature_gated(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False, suppress_features=["charts"])
        html = (out / "presentation.html").read_text(encoding="utf-8")
        run_meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert "charts" not in run_meta["features_enabled"]
        # Brand CSS still present when optional features off
        assert "--color-primary:" in html
        assert "--size-5:" in html

    def test_no_remote_token_css(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "fonts.googleapis.com" not in html
        assert "unpkg.com/open-props" not in html
        assert "open-props.min.css" not in html

    def test_kitchen_sink_props_absent(self, tmp_path):
        out = tmp_path / "out"
        render_deck(MINI, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        for name in _KITCHEN_SINK:
            assert name not in html, f"non-curated prop leaked: {name}"
