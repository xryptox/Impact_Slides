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

    def test_fallback_preserves_downstream_fields(self):
        """#133: fallback must not drop fields consumers read (manifest/notes/load)."""
        slide = {
            "slide_number": 2,
            "layout_type": "other",
            "title": "Keep me",
            "disclosure": "Confidential",
            "evidence_ids": ["E0100"],
            "evidence_sources": [{"id": "E0100", "source_file": "demo.docx"}],
            "kicker": "Key point",
            "packing_mode": "argument-led",
            "source_line": "Source: demo",
            "speaker_notes": "Say this out loud",
            "content": {
                "bullets": ["a"],
                "key_stats": [{"label": "Deal", "value": "$1"}],
                "so_what": "Matters because X",
            },
        }
        validated, errors = validate_handoff({"slides": [slide]})
        assert len(errors) == 1
        m = validated[0]
        assert isinstance(m, SplitTextVisualSlide)
        dumped = m.model_dump(exclude_none=True)
        for key in (
            "disclosure",
            "evidence_ids",
            "kicker",
            "packing_mode",
            "source_line",
            "speaker_notes",
        ):
            assert dumped.get(key) == slide[key], key
        assert dumped["evidence_sources"][0]["id"] == "E0100"
        assert dumped["evidence_sources"][0]["source_file"] == "demo.docx"
        assert dumped["content"]["key_stats"] == slide["content"]["key_stats"]
        assert dumped["content"]["so_what"] == slide["content"]["so_what"]

    @pytest.mark.parametrize(
        "label,slide",
        [
            ("missing slide_number", {"layout_type": "unknown_x", "title": "T"}),
            ("slide_number as str", {"slide_number": "3", "layout_type": "unknown_x"}),
            ("slide_number garbage", {"slide_number": "abc", "layout_type": "unknown_x"}),
            ("content not a dict", {"slide_number": 1, "layout_type": "unknown_x", "content": "oops"}),
            ("visual_spec not a dict", {"slide_number": 1, "layout_type": "unknown_x", "visual_spec": [1]}),
            ("content.bullets a str", {"slide_number": 1, "layout_type": "unknown_x", "content": {"bullets": "a,b"}}),
            ("slide is a str", "totally bogus"),
            ("slide is None", None),
        ],
    )
    def test_fallback_is_total_on_malformed_input(self, label, slide):
        """#133: the fallback must degrade, never raise.

        The non-lossy fix spreads the raw dict into the model, which pydantic
        rejects outright for these shapes -- so the try/except degrade path is
        load-bearing, not defensive decoration. Without this test, deleting that
        path entirely leaves the whole suite green (verified by mutation).
        """
        validated, errors = validate_handoff({"slides": [slide]})
        assert len(validated) == 1, label
        assert isinstance(validated[0], SplitTextVisualSlide), label
        assert validated[0].layout_type == "split_text_visual", label
        assert isinstance(validated[0].slide_number, int), label
        assert len(errors) == 1, label

    def test_bad_slide_number_does_not_cost_the_other_fields(self):
        """#133: a non-int slide_number must be coerced, not allowed to sink the slide.

        Without the coercion, pydantic rejects the spread dict and the degrade path
        runs, silently taking all 9 preserved fields with it -- i.e. the bug this
        issue fixed, re-entered through a different door.
        """
        slide = {
            "slide_number": "abc",  # invalid
            "layout_type": "unknown_x",
            "speaker_notes": "Say this",
            "packing_mode": "argument-led",
            "evidence_sources": [{"id": "E1"}],
            "kicker": "K",
        }
        validated, errors = validate_handoff({"slides": [slide]})
        m = validated[0]
        assert m.slide_number == 1, "bad slide_number should be replaced by position"
        d = m.model_dump(exclude_none=True)
        for key in ("speaker_notes", "packing_mode", "kicker"):
            assert d.get(key) == slide[key], key
        assert d["evidence_sources"][0]["id"] == "E1"

    def test_fallback_preserves_freeform_fixture_slide(self):
        freeform = FIXTURES / "freeform_handoff.json"
        handoff = json.loads(freeform.read_text(encoding="utf-8"))
        raw = handoff["slides"][1]  # layout_type: other
        validated, errors = validate_handoff(handoff)
        assert any("unknown layout_type" in e for e in errors)
        m = validated[1]
        d = m.model_dump(exclude_none=True)
        assert d["speaker_notes"] == raw["speaker_notes"]
        assert d["packing_mode"] == raw["packing_mode"]
        assert d["evidence_sources"][0]["id"] == raw["evidence_sources"][0]["id"]
        assert d["evidence_sources"][0]["source_file"] == raw["evidence_sources"][0]["source_file"]
        assert d["content"]["key_stats"] == raw["content"]["key_stats"]
        assert d["content"]["so_what"] == raw["content"]["so_what"]


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


class TestLayoutAliasDispatch:
    """Aliases schemas accepts must also route to the right recipe.

    Regression: schemas validated ``metric``/``table`` (TestSlideValidation
    above) but dispatch only matched the canonical names, so an alias slide
    validated and then fell through to render_split -- silently dropping
    key_stats. layouts.canonical() resolves aliases in one place.
    """

    def test_canonical_resolves_aliases(self):
        from impact_slides.renderer_v2.layouts import canonical

        assert canonical("metric") == "metric_dashboard"
        assert canonical("table") == "data_table"
        assert canonical("cover") == "title_or_opening"

    def test_canonical_passes_through_and_blanks_sentinels(self):
        from impact_slides.renderer_v2.layouts import canonical

        assert canonical("metric_dashboard") == "metric_dashboard"
        assert canonical("  METRIC  ") == "metric_dashboard"
        assert canonical("unknown_layout") == "unknown_layout"
        for sentinel in ("", "other", "default", None):
            assert canonical(sentinel) == ""

    def test_metric_alias_renders_key_stats(self):
        """The actual bug: $1M was dropped when layout_type was 'metric'."""
        from impact_slides.renderer_v2.layout.dispatch import render_slide

        slide = {
            "slide_number": 2,
            "layout_type": "metric",
            "title": "Metric alias",
            "content": {"key_stats": [{"label": "Rev", "value": "$1M"}]},
        }
        html = render_slide(slide, total=2, notes="")
        assert "$1M" in html

    def test_alias_and_canonical_paint_identically(self):
        from impact_slides.renderer_v2.layout.dispatch import render_slide

        for alias, canon in (("metric", "metric_dashboard"), ("table", "data_table")):
            base = {
                "slide_number": 2,
                "title": "T",
                "content": {"key_stats": [{"label": "A", "value": "1"}]},
            }
            a = render_slide({**base, "layout_type": alias}, total=2, notes="")
            b = render_slide({**base, "layout_type": canon}, total=2, notes="")
            assert a == b, f"{alias} must paint the same as {canon}"
