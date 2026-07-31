"""Guards after deleting the machine-local Boardroom charts pack."""
from __future__ import annotations

import inspect
import re

from impact_slides.renderer_v2 import charts
from impact_slides.renderer_v2.layouts import CHART_LAYOUTS


def test_charts_has_no_pack_loader():
    src = inspect.getsource(charts)
    assert "_find_pack_path" not in src
    assert "_load_pack" not in src
    assert "Path.home" not in src
    assert "chart_css" not in src
    assert re.search(r"\b_PACK\b", src) is None


def test_is_chart_layout_covers_catalog_only():
    for lt in CHART_LAYOUTS:
        assert charts.is_chart_layout(lt) is True
        assert charts.is_chart_layout(lt.upper()) is True
    assert charts.is_chart_layout("not_a_chart") is False
    assert charts.is_chart_layout("") is False


def test_icon_grid_uses_gl_fallback_tiles():
    slide = {
        "slide_number": 1,
        "title": "T",
        "layout_type": "icon_grid",
        "visual_spec": {
            "primary_visual": {
                "steps_or_data": [
                    {"label": "Growth", "body": "up"},
                    {"label": "Globe", "body": "wide"},
                    {"label": "Users", "body": "many"},
                ]
            }
        },
        "content": {},
    }
    html = charts.build_icon_grid_html(slide)
    assert "chart-empty" not in html
    assert "gl-grid" in html
    assert "gl-card" in html
    assert html.count("icon-tile") == 3
    assert 'href="#ic-growth"' in html
    assert 'href="#ic-globe"' in html
    assert 'href="#ic-users"' in html
    assert "tile-title" in html
    # pack markup must not return
    assert "icon-grid cols-" not in html


def test_icon_grid_per_step_description_renders_in_tile_body():
    """#126 option 1: per-step description is a body alias."""
    slide = {
        "slide_number": 1,
        "title": "T",
        "layout_type": "icon_grid",
        "visual_spec": {
            "primary_visual": {
                "steps_or_data": [
                    {"label": "Speed", "description": "fast delivery"},
                ]
            }
        },
        "content": {},
    }
    html = charts.build_icon_grid_html(slide)
    assert "fast delivery" in html
    assert '<div class="tile-body">fast delivery</div>' in html


def test_icon_grid_primary_visual_description_not_rendered():
    """Spec: primary_visual.description is a human caption Step 4 must ignore."""
    caption = "PV-LEVEL CAPTION MUST NOT APPEAR"
    slide = {
        "slide_number": 1,
        "title": "T",
        "layout_type": "icon_grid",
        "visual_spec": {
            "primary_visual": {
                "description": caption,
                "steps_or_data": [
                    {"label": "Speed", "body": "from body"},
                ],
            }
        },
        "content": {},
    }
    html = charts.build_icon_grid_html(slide)
    assert caption not in html
    assert "from body" in html


class TestSlideViewGuards:
    """The isinstance guards are why malformed handoffs degrade instead of
    raising. They were uncovered before slide_view.py centralised them; pin them
    here so the shared accessors cannot lose a guard silently."""

    def test_non_dict_visual_spec_degrades(self):
        from impact_slides.renderer_v2 import slide_view

        for bad in ("string", 42, [], ["a"]):
            assert slide_view.primary_visual({"visual_spec": bad}) == {}
            assert slide_view.steps({"visual_spec": bad}) == []
            assert slide_view.visual_type({"visual_spec": bad}) == ""

    def test_non_dict_primary_visual_degrades(self):
        from impact_slides.renderer_v2 import slide_view

        for bad in ("string", 42, ["a"]):
            slide = {"visual_spec": {"primary_visual": bad}}
            assert slide_view.primary_visual(slide) == {}
            assert slide_view.steps(slide) == []
            assert slide_view.visual_type(slide) == ""

    def test_non_list_steps_or_data_degrades(self):
        from impact_slides.renderer_v2 import slide_view

        for bad in ("string", 42, {"a": 1}):
            slide = {"visual_spec": {"primary_visual": {"steps_or_data": bad}}}
            assert slide_view.steps(slide) == []

    def test_non_dict_content_degrades(self):
        from impact_slides.renderer_v2 import slide_view

        for bad in ("string", 42, ["a"]):
            assert slide_view.content({"content": bad}) == {}

    def test_missing_keys_and_none(self):
        from impact_slides.renderer_v2 import slide_view

        for slide in ({}, {"visual_spec": None}, {"content": None}):
            assert slide_view.primary_visual(slide) == {}
            assert slide_view.steps(slide) == []
            assert slide_view.visual_type(slide) == ""
            assert slide_view.content(slide) == {}
