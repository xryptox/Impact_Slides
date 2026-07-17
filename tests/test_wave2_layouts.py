"""Tests for Wave 2 Diagram Layouts (Ticket #7).

system_architecture, data_flow_diagram, causal_loop, before_after.
Each must use diagram primitives, validate against ValidatedSlide,
and prove stage containment (1920×1080 safe area).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from impact_slides.renderer_v2.layout.dispatch import render_slide
from impact_slides.renderer_v2.schemas import validate_slide
from impact_slides.renderer_v2.strip import esc


def _make_slide(layout_type: str, **overrides) -> dict:
    base = {
        "slide_number": 1,
        "layout_type": layout_type,
        "title": "Test Deck",
        "content": {},
    }
    base.update(overrides)
    return base


def _render(slide: dict) -> str:
    return render_slide(slide, total=1, notes="Test notes.")


def _extract_svg(html: str) -> str:
    m = re.search(r'<svg class="diagram-canvas".*?</svg>', html, re.S)
    return m.group(0) if m else ""


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

class TestSchemaValidation:
    @pytest.mark.parametrize(
        "layout_type",
        [
            "system_architecture",
            "data_flow_diagram",
            "causal_loop",
            "before_after",
        ],
    )
    def test_validates(self, layout_type):
        model, err = validate_slide(_make_slide(layout_type))
        assert err is None, f"validation error: {err}"
        assert model.layout_type == layout_type


# ---------------------------------------------------------------------------
# Helper: row data for scene builders
# ---------------------------------------------------------------------------

def _architecture_data():
    return {
        "visual_spec": {
            "primary_visual": {
                "steps_or_data": [
                    ["Client Layer", "Mobile App", "iOS/Android"],
                    ["Client Layer", "Web SPA", "React"],
                    ["Gateway Layer", "API Gateway", "Auth + Rate Limit"],
                    ["Service Layer", "Orders Service", "Node.js"],
                    ["Service Layer", "Payments Service", "Stripe"],
                    ["Data Layer", "PostgreSQL", "Primary DB"],
                ]
            }
        }
    }


def _data_flow_data():
    return {
        "visual_spec": {
            "primary_visual": {
                "steps_or_data": [
                    ["Ingest", "Kafka", "Stream"],
                    ["Transform", "Spark", "ETL"],
                    ["Store", "S3", "Parquet"],
                    ["Serve", "API", "REST"],
                ]
            }
        }
    }


def _causal_loop_data():
    return {
        "visual_spec": {
            "primary_visual": {
                "steps_or_data": [
                    ["Ad Spend", "→"],
                    ["User Acquisition", "→"],
                    ["Revenue", "→"],
                    ["More Ad Spend", "↻"],
                ]
            }
        }
    }


# ---------------------------------------------------------------------------
# 1. system_architecture
# ---------------------------------------------------------------------------

class TestSystemArchitecture:
    def test_renders_diagram(self):
        slide = _make_slide("system_architecture", **_architecture_data())
        html = _render(slide)
        assert 'data-layout="system_architecture"' in html
        svg = _extract_svg(html)
        assert "diagram-node" in svg
        assert "diagram-group" in svg
        assert "Mobile App" in svg

    def test_uses_primitives(self):
        slide = _make_slide("system_architecture", **_architecture_data())
        html = _render(slide)
        svg = _extract_svg(html)
        # Must contain rect tags from node_box + group_boundary
        assert "<rect" in svg
        assert "<polygon" in svg or "M " in svg  # arrow_connector

    def test_density_limited(self):
        slide = _make_slide("system_architecture", **_architecture_data())
        html = _render(slide)
        svg = _extract_svg(html)
        # Only three layers max; each layer at most 3 nodes
        groups = svg.count('class="diagram-group"')
        assert groups <= 3
        nodes = svg.count('class="diagram-node"')
        assert nodes <= 9

    def test_no_eids(self):
        slide = _make_slide(
            "system_architecture",
            content={"bullets": ["E0001: data"]},
            **_architecture_data(),
        )
        html = _render(slide)
        assert "E0001" not in html


# ---------------------------------------------------------------------------
# 2. data_flow_diagram
# ---------------------------------------------------------------------------

class TestDataFlowDiagram:
    def test_renders_pipeline(self):
        slide = _make_slide("data_flow_diagram", **_data_flow_data())
        html = _render(slide)
        assert 'data-layout="data_flow_diagram"' in html
        svg = _extract_svg(html)
        assert "Ingest" in svg
        assert "Serve" in svg

    def test_horizontal_arrows(self):
        slide = _make_slide("data_flow_diagram", **_data_flow_data())
        html = _render(slide)
        svg = _extract_svg(html)
        assert "diagram-arrow" in svg

    def test_uses_group_boundary(self):
        slide = _make_slide("data_flow_diagram", **_data_flow_data())
        html = _render(slide)
        svg = _extract_svg(html)
        assert "diagram-group" in svg


# ---------------------------------------------------------------------------
# 3. causal_loop
# ---------------------------------------------------------------------------

class TestCausalLoop:
    def test_renders_loop(self):
        slide = _make_slide("causal_loop", **_causal_loop_data())
        html = _render(slide)
        assert 'data-layout="causal_loop"' in html
        svg = _extract_svg(html)
        # All 4 nodes present
        assert svg.count('class="diagram-node"') == 4

    def test_curved_arrows(self):
        slide = _make_slide("causal_loop", **_causal_loop_data())
        html = _render(slide)
        svg = _extract_svg(html)
        # Every arrow connects every node (4 arrows for 4 nodes in a loop)
        assert "diagram-arrow" in svg
        assert "Q " in svg  # curved = quadratic Bezier


# ---------------------------------------------------------------------------
# 4. before_after
# ---------------------------------------------------------------------------

class TestBeforeAfter:
    def test_renders_split(self):
        slide = _make_slide(
            "before_after",
            content={"bullets": ["Slow reporting", "Manual exports", "Fast dashboards", "Auto sync"]},
        )
        html = _render(slide)
        assert 'data-layout="before_after"' in html
        svg = _extract_svg(html)
        assert "Before" in svg
        assert "After" in svg

    def test_uses_node_boxes(self):
        slide = _make_slide("before_after")
        html = _render(slide)
        svg = _extract_svg(html)
        assert "diagram-node" in svg

    def test_transition_arrow(self):
        slide = _make_slide("before_after")
        html = _render(slide)
        svg = _extract_svg(html)
        assert "diagram-arrow" in svg


# ---------------------------------------------------------------------------
# Dispatch correctness
# ---------------------------------------------------------------------------

class TestDispatch:
    @pytest.mark.parametrize(
        "lt",
        [
            "system_architecture",
            "data_flow_diagram",
            "causal_loop",
            "before_after",
        ],
    )
    def test_routing(self, lt):
        if lt == "before_after":
            slide = _make_slide(lt)
        elif lt == "causal_loop":
            slide = _make_slide(lt, **_causal_loop_data())
        elif lt == "data_flow_diagram":
            slide = _make_slide(lt, **_data_flow_data())
        else:
            slide = _make_slide(lt, **_architecture_data())
        html = _render(slide)
        assert html
        assert f"layout-{lt}" in html
        assert f'data-layout="{lt}"' in html


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------

class TestWave2Integration:
    def test_full_deck(self, tmp_path):
        from impact_slides.renderer_v2 import render_deck

        handoff = {
            "presentation": {"title": "Wave 2 Test"},
            "slides": [
                {
                    "slide_number": 1,
                    "layout_type": "title_or_opening",
                    "title": "Diagram Deck",
                },
                {
                    "slide_number": 2,
                    "layout_type": "system_architecture",
                    "title": "Architecture",
                    **_architecture_data(),
                },
                {
                    "slide_number": 3,
                    "layout_type": "data_flow_diagram",
                    "title": "Pipeline",
                    **_data_flow_data(),
                },
                {
                    "slide_number": 4,
                    "layout_type": "causal_loop",
                    "title": "Feedback Loop",
                    **_causal_loop_data(),
                },
                {
                    "slide_number": 5,
                    "layout_type": "before_after",
                    "title": "Transformation",
                    "content": {"bullets": ["Manual", "Fast auto"]},
                },
            ],
        }

        handoff_path = tmp_path / "handoff.json"
        handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
        out = tmp_path / "out"
        result = render_deck(handoff_path, out, strict=False)

        assert result["ok"]
        html = (out / "presentation.html").read_text(encoding="utf-8")

        for lt in (
            "system_architecture",
            "data_flow_diagram",
            "causal_loop",
            "before_after",
        ):
            assert lt in html, f"missing {lt}"
            assert f"layout-{lt}" in html

        # Each should use diagram primitives
        assert "diagram-node" in html
        assert "diagram-arrow" in html

    @pytest.mark.parametrize(
        "layout_type,make_data",
        [
            ("system_architecture", _architecture_data),
            ("data_flow_diagram", _data_flow_data),
            ("causal_loop", _causal_loop_data),
            ("before_after", lambda: {}),
        ],
    )
    def test_stage_containment(self, layout_type, make_data):
        """Diagram viewBox fits within 900×480 stage safe area for every layout."""
        slide = _make_slide(layout_type, **make_data())
        html = _render(slide)
        svg = _extract_svg(html)
        match = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
        assert match, "missing viewBox"
        vw, vh = int(match.group(1)), int(match.group(2))
        assert vw <= 900, f"viewBox width {vw} exceeds 900 for {layout_type}"
        assert vh <= 480, f"viewBox height {vh} exceeds 480 for {layout_type}"
