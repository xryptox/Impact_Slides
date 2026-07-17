"""Tests for Wave 4a: Tree, Hierarchy & Ecosystem Diagrams (T8 #16).

decision_tree, hierarchy_tree, ecosystem_map.
"""

from __future__ import annotations

import re

import pytest

from impact_slides.renderer_v2.layout.dispatch import render_slide
from impact_slides.renderer_v2.schemas import validate_slide


def _make_slide(layout_type: str, **overrides) -> dict:
    base = {
        "slide_number": 1,
        "layout_type": layout_type,
        "title": "Test",
        "content": {},
    }
    base.update(overrides)
    return base


def _extract_svg(html: str) -> str:
    m = re.search(r'<svg class="diagram-canvas".*?</svg>', html, re.S)
    return m.group(0) if m else ""


class TestDecisionTree:
    def test_renders_svg_with_diamond(self):
        slide = _make_slide(
            "decision_tree",
            visual_spec={"primary_visual": {"steps_or_data": [["Root", "decision"], ["Branch A"], ["Branch B"]]}},
        )
        html = render_slide(slide, total=1, notes="")
        svg = _extract_svg(html)
        assert svg
        assert "<polygon" in svg  # diamond decision node
        assert "Root" in svg

    def test_schema_validates(self):
        slide = _make_slide("decision_tree", visual_spec={"primary_visual": {"steps_or_data": [["Root"]]}})
        model, err = validate_slide(slide)
        assert model is not None
        assert err is None

    def test_stage_containment(self):
        slide = _make_slide(
            "decision_tree",
            visual_spec={"primary_visual": {"steps_or_data": [["A", "decision"], ["B"], ["C"], ["D"], ["E"]]}},
        )
        html = render_slide(slide, total=1, notes="")
        svg = _extract_svg(html)
        assert 'viewBox="0 0 900 480"' in svg


class TestHierarchyTree:
    def test_renders_group_boundaries(self):
        slide = _make_slide(
            "hierarchy_tree",
            visual_spec={"primary_visual": {"steps_or_data": [["Root", "Child 1"], ["Root", "Child 2"]]}},
        )
        html = render_slide(slide, total=1, notes="")
        svg = _extract_svg(html)
        assert svg
        assert "diagram-group" in svg  # group_boundary emits diagram-group

    def test_schema_validates(self):
        slide = _make_slide("hierarchy_tree", visual_spec={"primary_visual": {"steps_or_data": [["Root", "Child"]]}})
        model, err = validate_slide(slide)
        assert model is not None
        assert err is None

    def test_stage_containment(self):
        slide = _make_slide(
            "hierarchy_tree",
            visual_spec={"primary_visual": {"steps_or_data": [["A", "B"], ["A", "C"], ["D", "E"]]}},
        )
        html = render_slide(slide, total=1, notes="")
        svg = _extract_svg(html)
        assert 'viewBox="0 0 900 480"' in svg


class TestEcosystemMap:
    def test_renders_nodes_and_connections(self):
        slide = _make_slide(
            "ecosystem_map",
            visual_spec={"primary_visual": {"steps_or_data": [
                ["Partner A", "supplies", "Partner B"],
                ["Partner B", "integrates", "Partner C"],
            ]}},
        )
        html = render_slide(slide, total=1, notes="")
        svg = _extract_svg(html)
        assert svg
        assert "Partner A" in svg
        assert "Partner B" in svg
        assert "Partner C" in svg

    def test_schema_validates(self):
        slide = _make_slide("ecosystem_map", visual_spec={"primary_visual": {"steps_or_data": [["A", "→", "B"]]}})
        model, err = validate_slide(slide)
        assert model is not None
        assert err is None

    def test_stage_containment(self):
        slide = _make_slide(
            "ecosystem_map",
            visual_spec={"primary_visual": {"steps_or_data": [
                ["A", "→", "B"], ["B", "→", "C"], ["C", "→", "D"],
            ]}},
        )
        html = render_slide(slide, total=1, notes="")
        svg = _extract_svg(html)
        assert 'viewBox="0 0 900 480"' in svg


class TestDispatchRouting:
    def test_wave4a_layouts_routed_correctly(self):
        for lt in ("decision_tree", "hierarchy_tree", "ecosystem_map"):
            slide = _make_slide(lt, visual_spec={"primary_visual": {"steps_or_data": [["Root", "Child"]]}})
            html = render_slide(slide, total=1, notes="")
            assert f'data-layout="{lt}"' in html
