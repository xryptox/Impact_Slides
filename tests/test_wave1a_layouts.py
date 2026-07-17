"""Tests for Wave 1a layout recipes (Ticket #6).

evidence_cards, data_table_with_insight, comparison_with_metrics.
Also tests metric_dashboard .card refactor.
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
        "title": "Test",
        "content": {},
    }
    base.update(overrides)
    return base


def _render(slide: dict) -> str:
    return render_slide(slide, total=1, notes="Test notes.")


def _count(html: str, cls: str) -> int:
    """Count occurrences of `cls` as a standalone token in class attributes."""
    tokens: list[str] = []
    for attr in re.findall(r'class="([^"]*)"', html):
        tokens.extend(attr.split())
    return tokens.count(cls)


# ---------------------------------------------------------------------------
# metric_dashboard .card refactor (inline change)
# ---------------------------------------------------------------------------

class TestMetricDashboardCard:
    def test_kpi_cards_have_card_class(self):
        slide = _make_slide(
            "metric_dashboard",
            content={
                "key_stats": [
                    {"label": "Revenue", "value": "$1B"},
                    {"label": "EBITDA", "value": "$300M"},
                ]
            },
        )
        html = _render(slide)
        cards = re.findall(r'class="[^"]*kpi-card[^"]*"', html)
        assert cards, "no kpi-cards found"
        for card_cls in cards:
            assert "card" in card_cls, f"kpi-card missing .card: {card_cls}"

    def test_kpi_render_unchanged(self):
        """Existing metric_dashboard output still has same structure."""
        slide = _make_slide(
            "metric_dashboard",
            content={"key_stats": [{"label": "A", "value": "1"}, {"label": "B", "value": "2"}]},
        )
        html = _render(slide)
        assert "kpi-label" in html
        assert "kpi-value" in html


# ---------------------------------------------------------------------------
# evidence_cards
# ---------------------------------------------------------------------------

class TestEvidenceCards:
    def test_basic_render(self):
        slide = _make_slide(
            "evidence_cards",
            content={"bullets": ["E0001: Stripe thesis", "E0002: Adyen margin"]},
        )
        html = _render(slide)
        assert "evidence-card" in html
        assert "Stripe thesis" in html

    def test_evidence_from_sources(self):
        slide = _make_slide(
            "evidence_cards",
            evidence_sources=[
                {"id": "E0001", "source_file": "deal_memo.pdf"},
                {"id": "E0002", "source_file": "model.xlsx"},
            ],
        )
        html = _render(slide)
        assert "deal_memo.pdf" in html
        assert "model.xlsx" in html
        assert _count(html, "evidence-card") == 2

    def test_supporting_points(self):
        slide = _make_slide(
            "evidence_cards",
            content={
                "supporting_points": [
                    "Point 1: Description A",
                    "Point 2: Description B",
                ]
            },
        )
        html = _render(slide)
        assert "Point 1" in html
        assert "Description A" in html
        assert _count(html, "evidence-card") == 2

    def test_density_2_items(self):
        slide = _make_slide("evidence_cards", content={"bullets": ["A", "B"]})
        html = _render(slide)
        assert "gl-grid-2" in html

    def test_density_3_items(self):
        slide = _make_slide("evidence_cards", content={"bullets": ["A", "B", "C"]})
        html = _render(slide)
        assert "gl-grid-3" in html

    def test_density_4_items(self):
        slide = _make_slide("evidence_cards", content={"bullets": ["A", "B", "C", "D"]})
        html = _render(slide)
        assert "gl-grid-dense-2x2" in html

    def test_density_6_items(self):
        slide = _make_slide("evidence_cards", content={"bullets": ["A", "B", "C", "D", "E", "F"]})
        html = _render(slide)
        assert "gl-grid-3" in html
        assert _count(html, "evidence-card") == 6

    def test_eids_scrubbed(self):
        slide = _make_slide(
            "evidence_cards",
            content={"bullets": ["E0005: data source"]},
        )
        html = _render(slide)
        assert "E0005" not in html

    def test_schema_validates(self):
        model, err = validate_slide(_make_slide("evidence_cards"))
        assert err is None
        assert model.layout_type == "evidence_cards"


# ---------------------------------------------------------------------------
# data_table_with_insight
# ---------------------------------------------------------------------------

class TestDataTableWithInsight:
    def test_table_render(self):
        slide = _make_slide(
            "data_table_with_insight",
            visual_spec={
                "primary_visual": {
                    "steps_or_data": [
                        ["Qtr", "Revenue", "Margin"],
                        ["Q1", "$100M", "18%"],
                        ["Q2", "$120M", "20%"],
                    ]
                }
            },
        )
        html = _render(slide)
        assert "table-frame" in html
        assert "Revenue" in html
        assert "$120M" in html

    def test_insight_strip(self):
        slide = _make_slide(
            "data_table_with_insight",
            visual_spec={
                "primary_visual": {
                    "steps_or_data": [["A", "1"], ["B", "2"]]
                }
            },
            content={"so_what": "Margins expanding"},
        )
        html = _render(slide)
        assert "Margins expanding" in html

    def test_fallback_to_kpi(self):
        """2-column data should render as KPI layout instead of table."""
        slide = _make_slide(
            "data_table_with_insight",
            visual_spec={
                "primary_visual": {
                    "steps_or_data": [
                        ["Metric", "Value"],
                        ["Revenue", "$1B"],
                        ["Growth", "18%"],
                    ]
                }
            },
        )
        html = _render(slide)
        # Should render KPI cards, not table
        assert "kpi-card" in html
        assert "kpi-label" in html

    def test_schema_validates(self):
        model, err = validate_slide(_make_slide("data_table_with_insight"))
        assert err is None
        assert model.layout_type == "data_table_with_insight"

    def test_eids_scrubbed(self):
        slide = _make_slide(
            "data_table_with_insight",
            content={"bullets": ["E0001: data"]},
        )
        html = _render(slide)
        assert "E0001" not in html


# ---------------------------------------------------------------------------
# comparison_with_metrics
# ---------------------------------------------------------------------------

class TestComparisonWithMetrics:
    def test_basic_render(self):
        slide = _make_slide(
            "comparison_with_metrics",
            visual_spec={
                "primary_visual": {
                    "steps_or_data": [
                        ["Risk A", "Description of risk A"],
                        ["Risk B", "Description of risk B"],
                    ]
                }
            },
        )
        html = _render(slide)
        assert "comparison-card" in html
        assert "Risk A" in html

    def test_metric_strip(self):
        slide = _make_slide(
            "comparison_with_metrics",
            content={
                "key_stats": [
                    {"label": "Revenue", "value": "$1B"},
                    {"label": "Growth", "value": "18%"},
                ]
            },
            visual_spec={
                "primary_visual": {
                    "steps_or_data": [["A", "desc"]]
                }
            },
        )
        html = _render(slide)
        assert "metric-strip" in html
        assert "Revenue" in html

    def test_no_metrics_no_strip(self):
        slide = _make_slide(
            "comparison_with_metrics",
            visual_spec={
                "primary_visual": {
                    "steps_or_data": [["A", "desc"]]
                }
            },
        )
        html = _render(slide)
        assert "metric-strip" not in html

    def test_insight_strip(self):
        slide = _make_slide(
            "comparison_with_metrics",
            content={"so_what": "Margins expanding fast"},
            visual_spec={
                "primary_visual": {
                    "steps_or_data": [["A", "desc"]]
                }
            },
        )
        html = _render(slide)
        assert "Margins expanding fast" in html

    def test_schema_validates(self):
        model, err = validate_slide(_make_slide("comparison_with_metrics"))
        assert err is None
        assert model.layout_type == "comparison_with_metrics"

    def test_eids_scrubbed(self):
        slide = _make_slide(
            "comparison_with_metrics",
            content={"bullets": ["Fix E0009"]},
        )
        html = _render(slide)
        assert "E0009" not in html


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------

class TestWave1aIntegration:
    def test_full_deck(self, tmp_path):
        from impact_slides.renderer_v2 import render_deck

        handoff = {
            "presentation": {"title": "Wave 1a Test"},
            "slides": [
                {
                    "slide_number": 1,
                    "layout_type": "title_or_opening",
                    "title": "Test Deck",
                },
                {
                    "slide_number": 2,
                    "layout_type": "evidence_cards",
                    "title": "Evidence",
                    "content": {
                        "bullets": ["Item A", "Item B", "Item C"],
                    },
                },
                {
                    "slide_number": 3,
                    "layout_type": "data_table_with_insight",
                    "title": "Data",
                    "visual_spec": {
                        "primary_visual": {
                            "steps_or_data": [
                                ["Qtr", "Revenue"],
                                ["Q1", "$100M"],
                                ["Q2", "$120M"],
                            ]
                        }
                    },
                    "content": {"so_what": "Growing fast"},
                },
                {
                    "slide_number": 4,
                    "layout_type": "comparison_with_metrics",
                    "title": "Compare",
                    "visual_spec": {
                        "primary_visual": {
                            "steps_or_data": [
                                ["Option A", "Pros: speed"],
                                ["Option B", "Pros: cost"],
                            ]
                        }
                    },
                    "content": {"key_stats": [{"label": "Speed", "value": "fast"}]},
                },
                {
                    "slide_number": 5,
                    "layout_type": "metric_dashboard",
                    "title": "Metrics",
                    "content": {
                        "key_stats": [
                            {"label": "Rev", "value": "$1B"},
                            {"label": "EBITDA", "value": "$300M"},
                        ]
                    },
                },
            ],
        }

        handoff_path = tmp_path / "handoff.json"
        handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
        out = tmp_path / "out"
        result = render_deck(handoff_path, out, strict=False)

        assert result["ok"]
        html = (out / "presentation.html").read_text(encoding="utf-8")

        # All layout types present
        assert "evidence_cards" in html
        assert "data_table_with_insight" in html
        assert "comparison_with_metrics" in html
        assert "metric_dashboard" in html

        # Recipe-specific output
        assert "evidence-card" in html
        assert "table-frame" in html
        assert "comparison-card" in html
        assert "kpi-card" in html

    def test_render_slide_dispatch(self):
        """Verify dispatch routes the new layout types correctly."""
        for lt in ("evidence_cards", "data_table_with_insight", "comparison_with_metrics"):
            if lt == "evidence_cards":
                slide = _make_slide(lt, content={"bullets": ["A"]})
            elif lt == "data_table_with_insight":
                slide = _make_slide(
                    lt, content={}, visual_spec={"primary_visual": {"steps_or_data": [["X", "Y"]]}}
                )
            else:
                slide = _make_slide(
                    lt, content={}, visual_spec={"primary_visual": {"steps_or_data": [["X", "Y"]]}}
                )
            html = _render(slide)
            assert html, f"empty render for {lt}"
            assert f"layout-{lt}" in html, f"missing layout-{lt}"
            assert f'data-layout="{lt}"' in html, f"missing data-layout for {lt}"
