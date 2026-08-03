"""A non-dict `content` must degrade, never crash the render.

`render_deck(..., strict=False)` promises to survive bad input, but every consumer
that did `slide.get("content") or {}` still crashed on a *string* content: `or {}`
catches None and missing, not a wrong type. Measured before the fix: all 200
combinations of (49 routed layouts + 1 unknown) x (str, list, int, bool) raised
`AttributeError: 'str' object has no attribute 'get'`.

Fixing only the reported line (`notes.py`) was not enough -- the crash simply moved
to `strip.py`, then `charts/core.py`. All consumers now route through
`slide_view.content()`, which is the one guarded accessor.
"""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

import pytest

from impact_slides.renderer_v2 import render_deck
from impact_slides.renderer_v2.layout import dispatch
from impact_slides.renderer_v2.notes import build_spoken_notes
from impact_slides.renderer_v2.slide_view import content as sv_content

# Wrong types that `or {}` lets through. None/missing were always handled.
BAD_CONTENT = ["oops", [1, 2], 5, True]


def _render(tmp_path: Path, slide: dict) -> dict:
    handoff = {"presentation": {"title": "T"}, "slides": [slide]}
    p = tmp_path / "h.json"
    p.write_text(json.dumps(handoff), encoding="utf-8")
    with contextlib.redirect_stderr(io.StringIO()):  # validation warnings are expected
        return render_deck(p, tmp_path, strict=False)


class TestSlideViewContentGuard:
    @pytest.mark.parametrize("bad", BAD_CONTENT)
    def test_returns_empty_dict_for_wrong_type(self, bad):
        assert sv_content({"content": bad}) == {}

    def test_still_returns_real_content(self):
        assert sv_content({"content": {"bullets": ["a"]}}) == {"bullets": ["a"]}

    @pytest.mark.parametrize("missing", [{}, {"content": None}])
    def test_missing_or_none(self, missing):
        assert sv_content(missing) == {}


class TestRenderSurvivesMalformedContent:
    @pytest.mark.parametrize("bad", BAD_CONTENT)
    def test_render_deck_does_not_crash(self, tmp_path, bad):
        """The originally reported crash: AttributeError from notes.py."""
        res = _render(tmp_path, {
            "slide_number": 1,
            "layout_type": "split_text_visual",
            "title": "T",
            "content": bad,
        })
        assert res["html_bytes"] > 0

    @pytest.mark.parametrize("bad", BAD_CONTENT)
    def test_unknown_layout_with_bad_content(self, tmp_path, bad):
        """Unknown layout routes through the validation fallback as well."""
        res = _render(tmp_path, {
            "slide_number": 1,
            "layout_type": "bogus_unknown",
            "title": "T",
            "content": bad,
        })
        assert res["html_bytes"] > 0

    @pytest.mark.parametrize("layout", sorted(dispatch.LAYOUT_RECIPES))
    def test_every_routed_layout_survives(self, tmp_path, layout):
        """Guards the whole registry, not just the layout that happened to be
        reported. Fixing one consumer moved the crash to the next one, so the
        sweep is the actual regression test."""
        res = _render(tmp_path, {
            "slide_number": 1,
            "layout_type": layout,
            "title": "T",
            "content": "oops",
        })
        assert res["html_bytes"] > 0

    def test_bad_content_does_not_lose_other_slides(self, tmp_path):
        """One bad slide must not take the deck down with it."""
        handoff = {"presentation": {"title": "T"}, "slides": [
            {"slide_number": 1, "layout_type": "title_or_opening", "title": "Good one"},
            {"slide_number": 2, "layout_type": "split_text_visual", "title": "Bad",
             "content": "oops"},
            {"slide_number": 3, "layout_type": "split_text_visual", "title": "Good two",
             "content": {"bullets": ["kept"]}},
        ]}
        p = tmp_path / "h.json"
        p.write_text(json.dumps(handoff), encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()):
            render_deck(p, tmp_path, strict=False)
        html = next(tmp_path.glob("*.html")).read_text(encoding="utf-8")
        assert "Good one" in html
        assert "Good two" in html
        assert "kept" in html


class TestSpokenNotesGuard:
    @pytest.mark.parametrize("bad", BAD_CONTENT)
    def test_build_spoken_notes_direct(self, bad):
        """notes.py:build_spoken_notes was the reported crash site (line 77)."""
        out = build_spoken_notes({
            "slide_number": 2,
            "layout_type": "split_text_visual",
            "title": "Fallback",
            "content": bad,
        })
        assert isinstance(out, str)
