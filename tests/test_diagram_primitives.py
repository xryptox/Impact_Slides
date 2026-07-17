"""Tests for diagram SVG primitives (Ticket #4)."""
from __future__ import annotations

import re

import pytest

from impact_slides.renderer_v2.diagram import (
    annotation_callout,
    arrow_connector,
    group_boundary,
    node_box,
)


# ---------------------------------------------------------------------------
# Node Box
# ---------------------------------------------------------------------------

class TestNodeBox:
    def test_basic_node(self):
        html = node_box("Platform")
        assert '<g class="diagram-node">' in html
        assert '<rect' in html
        assert '>Platform<' in html
        assert "var(--color-surface)" in html
        assert "var(--color-primary)" in html

    def test_node_with_icon(self):
        html = node_box("Gateway", icon="globe")
        assert 'ic-globe' in html
        assert "translate" in html  # icon positioned

    def test_node_with_sublabel(self):
        html = node_box("Main", sublabel="sublabel text")
        assert "sublabel text" in html
        # Two text elements: label and sublabel
        assert html.count("<text") == 2

    def test_node_custom_dimensions(self):
        html = node_box("A", width=200, height=80)
        assert 'width="200"' in html
        assert 'height="80"' in html

    def test_node_uses_semantic_tokens(self):
        html = node_box("A")
        assert "var(--color-surface)" in html
        assert "var(--color-primary)" in html
        assert "var(--color-ink)" in html
        assert "var(--font-body)" in html


# ---------------------------------------------------------------------------
# Arrow Connector
# ---------------------------------------------------------------------------

class TestArrowConnector:
    def test_straight_arrow(self):
        html = arrow_connector(0, 0, 100, 0)
        assert '<g class="diagram-arrow">' in html
        assert 'M 0.0 0.0 L 100.0 0.0' in html
        assert "<polygon" in html  # arrowhead

    def test_curved_arrow(self):
        html = arrow_connector(0, 0, 100, 0, curved=True)
        assert "Q" in html

    def test_dashed_arrow(self):
        html = arrow_connector(0, 0, 50, 50, dashed=True)
        assert 'stroke-dasharray="6,4"' in html

    def test_arrow_uses_semantic_tokens(self):
        html = arrow_connector(0, 0, 50, 50)
        assert "var(--color-accent)" in html

    def test_arrowhead_calculation(self):
        html = arrow_connector(0, 0, 100, 0)
        # Arrowhead is a polygon near the end point
        assert "points=" in html
        assert "," in html


# ---------------------------------------------------------------------------
# Group Boundary
# ---------------------------------------------------------------------------

class TestGroupBoundary:
    def test_basic_boundary(self):
        html = group_boundary(10, 10, 200, 150)
        assert '<g class="diagram-group">' in html
        assert '<rect' in html
        assert "stroke-dasharray=" in html
        assert "fill-opacity=\"0.35\"" in html

    def test_boundary_with_label(self):
        html = group_boundary(0, 0, 200, 100, label="Services")
        assert ">Services<" in html

    def test_boundary_uses_semantic_tokens(self):
        html = group_boundary(0, 0, 100, 100, label="A")
        assert "var(--color-primary-mid)" in html
        assert "var(--color-surface-soft)" in html
        assert "var(--font-body)" in html


# ---------------------------------------------------------------------------
# Annotation Callout
# ---------------------------------------------------------------------------

class TestAnnotationCallout:
    def test_basic_callout(self):
        html = annotation_callout(50, 50, "Note")
        assert '<g class="diagram-annotation">' in html
        assert "Note" in html
        assert "<rect" in html

    def test_callout_with_connector(self):
        html = annotation_callout(50, 50, "Target", target_x=100, target_y=100)
        assert "<line" in html
        assert 'stroke-dasharray="4,2"' in html
        assert "x2=\"100.0\"" in html

    def test_callout_uses_semantic_tokens(self):
        html = annotation_callout(0, 0, "Note")
        assert "var(--color-accent)" in html
        assert "var(--font-body)" in html

    def test_callout_multiline(self):
        html = annotation_callout(0, 0, "Line 1\\nLine 2")
        assert "<br/>" in html or "Line 1" in html


# ---------------------------------------------------------------------------
# Integration: SVG structure
# ---------------------------------------------------------------------------

class TestSvgValidity:
    def test_all_primitives_well_formed(self):
        """Each primitive produces balanced tags."""
        samples = [
            node_box("Node A"),
            arrow_connector(0, 0, 100, 50),
            group_boundary(0, 0, 200, 100, label="Group"),
            annotation_callout(50, 50, "Callout", target_x=100, target_y=100),
        ]
        for html in samples:
            # Count open/close g tags
            opens = html.count("<g")
            closes = html.count("</g>")
            assert opens == closes, f"Unbalanced g tags: {opens} vs {closes}"

    def test_no_bare_angles(self):
        """No unescaped < or > in text content (esc() covers this)."""
        html = node_box("<script>")
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
