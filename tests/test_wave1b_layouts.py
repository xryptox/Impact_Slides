"""Tests for Wave 1b layout recipes (Ticket #5).

Tests metric_row_with_breakdown, insight_with_evidence, priority_matrix.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from impact_slides.renderer_v2.layout.dispatch import render_slide
from impact_slides.renderer_v2.schemas import validate_slide
from impact_slides.renderer_v2.strip import esc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_slide(layout_type: str, **overrides) -> dict:
    base = {
        "slide_number": 1,
        "layout_type": layout_type,
        "title": "Test",
        "content": {},
    }
    base.update(overrides)
    return base


def _render(slide: dict) -> str:
    return render_slide(slide, total=1, notes="Test notes.")


def _count(html: str, cls: str) -> int:
    # Match the class name anywhere inside a class attribute
    return len(re.findall(rf'class="[^"]*{re.escape(cls)}[^"]*"', html))


# ---------------------------------------------------------------------------
# metric_row_with_breakdown
# ---------------------------------------------------------------------------

class TestMetricRowWithBreakdown:
    def test_basic_render(self):
        slide = _make_slide(
            "metric_row_with_breakdown",
            content={
                "key_stats": [
                    {"label": "Revenue", "value": "$1.2B", "source": "10-K"},
                    {"label": "EBITDA", "value": "$340M", "source": "10-K"},
                    {"label": "Growth", "value": "18%", "source": "Model"},
                ],
                "bullets": ["Q1: $280M", "Q2: $310M"],
            },
        )
        html = _render(slide)
        assert "kpi-card" in html
        assert "Revenue" in html
        assert "$1.2B" in html
        assert "Breakdown" in html

    def test_kpi_count_density(self):
        for n in (1, 2, 3, 4):
            stats = [{"label": f"K{i}", "value": f"V{i}"} for i in range(n)]
            slide = _make_slide("metric_row_with_breakdown", content={"key_stats": stats})
            html = _render(slide)
            assert _count(html, "kpi-card") == n, f"expected {n} kpi-cards"

    def test_breakdown_band(self):
        slide = _make_slide(
            "metric_row_with_breakdown",
            content={
                "key_stats": [{"label": "A", "value": "1"}],
                "supporting_points": ["Q1: $100M", "Q2: $200M"],
            },
        )
        html = _render(slide)
        assert "breakdown-row" in html
        assert "Q1" in html
        assert "$100M" in html
        assert "Q2" in html
        assert "$200M" in html

    def test_no_breakdown_falls_back(self):
        slide = _make_slide(
            "metric_row_with_breakdown",
            content={"key_stats": [{"label": "A", "value": "1"}]},
        )
        html = _render(slide)
        assert "kpi-card" in html
        # breakdown-card not rendered when no supporting/bullets
        assert "breakdown-card" not in html

    def test_fallback_to_metric_when_no_stats(self):
        slide = _make_slide(
            "metric_row_with_breakdown",
            visual_spec={"primary_visual": {"steps_or_data": [["Revenue", "$1B"]]}},
        )
        html = _render(slide)
        # Falls back to metric recipe which shows kpi-card
        assert "kpi-card" in html

    def test_schema_validates(self):
        slide = _make_slide("metric_row_with_breakdown")
        model, err = validate_slide(slide)
        assert err is None
        assert model.layout_type == "metric_row_with_breakdown"

    def test_eids_scrubbed(self):
        slide = _make_slide(
            "metric_row_with_breakdown",
            content={"key_stats": [{"label": "Rev E0001", "value": "$1B"}]},
        )
        html = _render(slide)
        assert "E0001" not in html


# ---------------------------------------------------------------------------
# insight_with_evidence
# ---------------------------------------------------------------------------

class TestInsightWithEvidence:
    def test_basic_render(self):
        slide = _make_slide(
            "insight_with_evidence",
            content={
                "headline": "Payments infra consolidating",
                "so_what": "Platform play wins",
                "bullets": ["E0001: Stripe thesis", "E0002: Adyen margin"],
            },
        )
        html = _render(slide)
        assert "insight-hero" in html
        assert "Platform play wins" in html

    def test_evidence_cards(self):
        slide = _make_slide(
            "insight_with_evidence",
            content={"bullets": ["A", "B", "C", "D", "E", "F"]},
        )
        html = _render(slide)
        assert _count(html, "evidence-card") == 6

    def test_evidence_from_sources(self):
        slide = _make_slide(
            "insight_with_evidence",
            evidence_sources=[
                {"id": "E0001", "source_file": "deal_memo.pdf"},
                {"id": "E0002", "source_file": "model.xlsx"},
            ],
        )
        html = _render(slide)
        assert "deal_memo.pdf" in html
        assert "model.xlsx" in html

    def test_no_insight_no_hero(self):
        slide = _make_slide("insight_with_evidence", content={"bullets": ["A"]})
        html = _render(slide)
        assert "insight-hero" not in html

    def test_density_columns(self):
        # 4 items → 2×2 dense grid
        slide = _make_slide(
            "insight_with_evidence",
            content={"bullets": ["A", "B", "C", "D"]},
        )
        html = _render(slide)
        assert "gl-grid-dense-2x2" in html

    def test_schema_validates(self):
        model, err = validate_slide(_make_slide("insight_with_evidence"))
        assert err is None
        assert model.layout_type == "insight_with_evidence"


# ---------------------------------------------------------------------------
# priority_matrix
# ---------------------------------------------------------------------------

class TestPriorityMatrix:
    def test_basic_render(self):
        slide = _make_slide(
            "priority_matrix",
            visual_spec={
                "primary_visual": {
                    "steps_or_data": [
                        ["High / High", "Item A", "Item B"],
                        ["High / Low", "Item C"],
                        ["Low / High", "Item D"],
                        ["Low / Low", "Item E"],
                    ],
                },
            },
        )
        html = _render(slide)
        assert "priority-quadrant" in html
        assert "High / High" in html
        assert "Item A" in html

    def test_four_quadrants_always(self):
        slide = _make_slide(
            "priority_matrix",
            content={"bullets": ["X", "Y"]},
        )
        html = _render(slide)
        assert _count(html, "priority-quadrant") == 4

    def test_fallback_from_bullets(self):
        slide = _make_slide(
            "priority_matrix",
            content={"bullets": ["Task 1", "Task 2", "Task 3", "Task 4"]},
        )
        html = _render(slide)
        assert "Task 1" in html
        assert _count(html, "priority-quadrant") == 4

    def test_quadrant_labels(self):
        slide = _make_slide("priority_matrix")
        html = _render(slide)
        assert "High Priority / High Impact" in html
        assert "Lower Priority / Lower Impact" in html

    def test_density_grid_class(self):
        slide = _make_slide("priority_matrix")
        html = _render(slide)
        assert "gl-grid-dense-2x2" in html

    def test_schema_validates(self):
        model, err = validate_slide(_make_slide("priority_matrix"))
        assert err is None
        assert model.layout_type == "priority_matrix"

    def test_eids_scrubbed(self):
        slide = _make_slide(
            "priority_matrix",
            content={"bullets": ["Fix bug E0003"]},
        )
        html = _render(slide)
        assert "E0003" not in html


# ---------------------------------------------------------------------------
# Integration: all three in one deck
# ---------------------------------------------------------------------------

class TestWave1bIntegration:
    def test_full_deck(self, tmp_path):
        from impact_slides.renderer_v2 import render_deck

        handoff = {
            "presentation": {"title": "Wave 1b Test"},
            "slides": [
                {
                    "slide_number": 1,
                    "layout_type": "title_or_opening",
                    "title": "Test Deck",
                },
                {
                    "slide_number": 2,
                    "layout_type": "metric_row_with_breakdown",
                    "title": "Metrics",
                    "content": {
                        "key_stats": [
                            {"label": "Rev", "value": "$1B"},
                            {"label": "EBITDA", "value": "$300M"},
                        ],
                        "supporting_points": ["Q1: $250M", "Q2: $300M"],
                    },
                },
                {
                    "slide_number": 3,
                    "layout_type": "insight_with_evidence",
                    "title": "Insight",
                    "content": {
                        "headline": "Key finding",
                        "so_what": "This matters",
                        "bullets": ["Evidence A", "Evidence B"],
                    },
                },
                {
                    "slide_number": 4,
                    "layout_type": "priority_matrix",
                    "title": "Priorities",
                    "content": {"bullets": ["P1", "P2", "P3", "P4"]},
                },
            ],
        }

        handoff_path = tmp_path / "handoff.json"
        handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
        out = tmp_path / "out"
        result = render_deck(handoff_path, out, strict=False)

        assert result["ok"]
        html = (out / "presentation.html").read_text(encoding="utf-8")

        assert "metric_row_with_breakdown" in html
        assert "insight_with_evidence" in html
        assert "priority_matrix" in html

        assert "kpi-card" in html
        assert "insight-hero" in html
        assert "priority-quadrant" in html

    def test_render_slide_dispatch(self):
        """Verify dispatch routes the new layout types correctly."""
        for lt in ("metric_row_with_breakdown", "insight_with_evidence", "priority_matrix"):
            if lt == "metric_row_with_breakdown":
                # Need content to avoid fallback to render_metric
                slide = _make_slide(lt, content={"key_stats": [{"label": "X", "value": "1"}]})
            else:
                slide = _make_slide(lt)
            html = _render(slide)
            assert html, f"empty render for {lt}"
            assert f"layout-{lt}" in html, f"missing layout-{lt}"
            assert f'data-layout="{lt}"' in html, f"missing data-layout for {lt}"
