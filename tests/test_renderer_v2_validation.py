"""Contract tests for renderer_v2 Pydantic validation layer."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from impact_slides.renderer_v2.schemas import (
    SplitTextVisualSlide,
    TitleSlide,
    ValidatedSlide,
    validate_handoff,
    validate_slide,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "renderer_v2"
MINI = FIXTURES / "mini_handoff.json"


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _load_mini() -> dict:
    return json.loads(MINI.read_text(encoding="utf-8"))


def _make_slide(layout_type: str, **overrides) -> dict:
    base = {
        "slide_number": 1,
        "layout_type": layout_type,
        "title": "Test",
        "content": {},
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Per-layout validation
# ---------------------------------------------------------------------------

class TestSlideValidation:
    """Each layout type validates against its discriminated-union model."""

    def test_title_or_opening(self):
        model, err = validate_slide(_make_slide("title_or_opening"))
        assert err is None
        assert isinstance(model, TitleSlide)

    def test_split_text_visual(self):
        model, err = validate_slide(_make_slide("split_text_visual"))
        assert err is None
        assert isinstance(model, SplitTextVisualSlide)

    def test_metric_dashboard(self):
        model, err = validate_slide(_make_slide("metric_dashboard"))
        assert err is None

    def test_metric_alias(self):
        model, err = validate_slide(_make_slide("metric"))
        assert err is None

    def test_data_table(self):
        model, err = validate_slide(_make_slide("data_table"))
        assert err is None

    def test_table_alias(self):
        model, err = validate_slide(_make_slide("table"))
        assert err is None

    def test_process_flow(self):
        model, err = validate_slide(_make_slide("full_process_flow"))
        assert err is None

    def test_timeline(self):
        model, err = validate_slide(_make_slide("timeline"))
        assert err is None

    def test_roadmap(self):
        model, err = validate_slide(_make_slide("roadmap"))
        assert err is None

    def test_comparison_grid(self):
        model, err = validate_slide(_make_slide("comparison_grid"))
        assert err is None

    def test_quote_card(self):
        model, err = validate_slide(_make_slide("quote_card"))
        assert err is None

    def test_icon_grid(self):
        model, err = validate_slide(_make_slide("icon_grid"))
        assert err is None

    def test_freeform_grid(self):
        model, err = validate_slide(_make_slide("freeform_grid"))
        assert err is None

    def test_chart_layouts(self):
        for lt in ("grouped_bar_chart", "stacked_bar_chart", "waterfall_chart", "heatmap"):
            model, err = validate_slide(_make_slide(lt))
            assert err is None, f"{lt}: {err}"

    def test_missing_layout_type(self):
        model, err = validate_slide({"slide_number": 1})
        assert model is None
        assert "missing layout_type" in err

    def test_unknown_layout_type(self):
        model, err = validate_slide(_make_slide("nonexistent_layout"))
        assert model is None
        assert "unknown layout_type" in err

    def test_malformed_slide_number(self):
        model, err = validate_slide(_make_slide("split_text_visual", slide_number="not_a_number"))
        assert model is None
        assert "validation error" in err

    def test_content_sub_model(self):
        model, err = validate_slide(
            _make_slide(
                "split_text_visual",
                content={"bullets": ["a", "b"], "body_text": "lead"},
            )
        )
        assert err is None
        assert model.content.bullets == ["a", "b"]

    def test_evidence_sources(self):
        model, err = validate_slide(
            _make_slide(
                "metric_dashboard",
                evidence_sources=[{"id": "E0001", "source_file": "deal.pdf"}],
            )
        )
        assert err is None


# ---------------------------------------------------------------------------
# Handoff-level validation
# ---------------------------------------------------------------------------

class TestHandoffValidation:
    def test_valid_mini_handoff(self):
        handoff = _load_mini()
        validated, errors = validate_handoff(handoff)
        assert errors == [], f"unexpected errors: {errors}"
        assert len(validated) == len(handoff["slides"])
        assert isinstance(validated[0], TitleSlide)

    def test_malformed_handoff_falls_back(self):
        handoff = {
            "slides": [
                {"slide_number": 1, "layout_type": "title_or_opening", "title": "Good"},
                {"slide_number": 2, "layout_type": "nonexistent", "title": "Bad"},
                {"slide_number": 3, "layout_type": "split_text_visual", "title": "Good"},
            ]
        }
        validated, errors = validate_handoff(handoff)
        assert len(errors) == 1
        assert "unknown layout_type" in errors[0]
        assert len(validated) == 3
        # Bad slide became fallback
        assert isinstance(validated[1], SplitTextVisualSlide)
        # Good slides preserved
        assert isinstance(validated[0], TitleSlide)
        assert isinstance(validated[2], SplitTextVisualSlide)

    def test_non_dict_slide_falls_back(self):
        handoff = {"slides": [{"slide_number": 1, "layout_type": "title_or_opening"}, "not_a_dict"]}
        validated, errors = validate_handoff(handoff)
        assert len(errors) == 1
        assert "not a dict" in errors[0]
        assert len(validated) == 2
        assert isinstance(validated[1], SplitTextVisualSlide)

    def test_empty_slides(self):
        validated, errors = validate_handoff({"slides": []})
        assert errors == []
        assert validated == []

    def test_no_slides_key(self):
        validated, errors = validate_handoff({})
        assert errors == []
        assert validated == []

    def test_fallback_preserves_content(self):
        handoff = {
            "slides": [
                {
                    "slide_number": 1,
                    "layout_type": "nonexistent",
                    "title": "Fallback Test",
                    "content": {"bullets": ["keep me"], "body_text": "preserve me"},
                }
            ]
        }
        validated, errors = validate_handoff(handoff)
        assert len(errors) == 1
        assert validated[0].title == "Fallback Test"
        assert validated[0].content.bullets == ["keep me"]


# ---------------------------------------------------------------------------
# Integration: render_deck with validation
# ---------------------------------------------------------------------------

class TestRenderDeckValidation:
    """render_deck should validate without crashing on malformed handoffs."""

    def test_render_mini_deck(self, tmp_path):
        from impact_slides.renderer_v2 import render_deck

        out = tmp_path / "out"
        result = render_deck(MINI, out, strict=False)
        assert result["ok"]
        assert (out / "presentation.html").exists()

    def test_render_malformed_handoff(self, tmp_path):
        from impact_slides.renderer_v2 import render_deck

        bad = tmp_path / "bad_handoff.json"
        bad.write_text(json.dumps({
            "presentation": {"title": "Bad Deck"},
            "slides": [
                {"slide_number": 1, "layout_type": "title_or_opening", "title": "OK"},
                {"slide_number": 2, "layout_type": "nonexistent", "title": "Bad"},
            ],
        }), encoding="utf-8")

        out = tmp_path / "out"
        result = render_deck(bad, out, strict=False)
        assert result["ok"]  # should not crash
        assert (out / "presentation.html").exists()

    def test_render_empty_handoff(self, tmp_path):
        from impact_slides.renderer_v2 import render_deck

        empty = tmp_path / "empty_handoff.json"
        empty.write_text(json.dumps({"slides": []}), encoding="utf-8")

        out = tmp_path / "out"
        # normalize_handoff raises on empty slides — this is expected
        with pytest.raises(ValueError, match="no slides"):
            render_deck(empty, out, strict=False)
