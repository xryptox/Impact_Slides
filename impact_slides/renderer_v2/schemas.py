"""Pydantic validation layer for builder handoff slides.

Discriminated union on ``layout_type`` covering all existing renderer_v2
layout types.  The renderer validates before painting; malformed slides fall
back to ``split_text_visual`` with a logged error.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Shared sub-models
# ---------------------------------------------------------------------------

class VisualSpec(BaseModel):
    model_config = ConfigDict(extra="allow")
    primary_visual: Optional[Dict[str, Any]] = None
    grid: Optional[Dict[str, Any]] = None


class EvidenceSource(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    evidence_id: Optional[str] = None
    source_file: Optional[str] = None
    file: Optional[str] = None


class SlideContent(BaseModel):
    model_config = ConfigDict(extra="allow")
    headline: Optional[str] = None
    subtitle: Optional[str] = None
    bullets: Optional[List[str]] = None
    supporting_points: Optional[List[str]] = None
    key_stats: Optional[List[Dict[str, Any]]] = None
    body_text: Optional[str] = None
    so_what: Optional[str] = None
    narrative_bridge: Optional[str] = None


# ---------------------------------------------------------------------------
# Per-layout slide models (discriminated by layout_type)
# ---------------------------------------------------------------------------

class _BaseSlide(BaseModel):
    model_config = ConfigDict(extra="allow")
    slide_number: int
    title: Optional[str] = None
    section: Optional[str] = None
    purpose: Optional[str] = None
    audience_takeaway: Optional[str] = None
    packing_mode: Optional[str] = None
    content: Optional[SlideContent] = None
    evidence_sources: Optional[List[Union[str, EvidenceSource]]] = None
    visual_spec: Optional[VisualSpec] = None
    speaker_notes: Optional[str] = None
    synthesized: Optional[bool] = None
    confidence: Optional[str] = None


class TitleSlide(_BaseSlide):
    layout_type: Literal["title_or_opening"] = "title_or_opening"


class SplitTextVisualSlide(_BaseSlide):
    layout_type: Literal["split_text_visual"] = "split_text_visual"


class MetricDashboardSlide(_BaseSlide):
    layout_type: Literal["metric_dashboard", "metric"] = "metric_dashboard"


class DataTableSlide(_BaseSlide):
    layout_type: Literal["data_table", "table"] = "data_table"


class ProcessFlowSlide(_BaseSlide):
    layout_type: Literal["full_process_flow", "timeline", "roadmap"] = "full_process_flow"


class ComparisonGridSlide(_BaseSlide):
    layout_type: Literal["comparison_grid"] = "comparison_grid"


class QuoteCardSlide(_BaseSlide):
    layout_type: Literal["quote_card"] = "quote_card"


class IconGridSlide(_BaseSlide):
    layout_type: Literal["icon_grid"] = "icon_grid"


class MetricRowWithBreakdownSlide(_BaseSlide):
    layout_type: Literal["metric_row_with_breakdown"] = "metric_row_with_breakdown"


class InsightWithEvidenceSlide(_BaseSlide):
    layout_type: Literal["insight_with_evidence"] = "insight_with_evidence"


class PriorityMatrixSlide(_BaseSlide):
    layout_type: Literal["priority_matrix"] = "priority_matrix"


class EvidenceCardsSlide(_BaseSlide):
    layout_type: Literal["evidence_cards"] = "evidence_cards"


class DataTableWithInsightSlide(_BaseSlide):
    layout_type: Literal["data_table_with_insight"] = "data_table_with_insight"


class ComparisonWithMetricsSlide(_BaseSlide):
    layout_type: Literal["comparison_with_metrics"] = "comparison_with_metrics"


class SystemArchitectureSlide(_BaseSlide):
    layout_type: Literal["system_architecture"] = "system_architecture"


class DataFlowDiagramSlide(_BaseSlide):
    layout_type: Literal["data_flow_diagram"] = "data_flow_diagram"


class CausalLoopSlide(_BaseSlide):
    layout_type: Literal["causal_loop"] = "causal_loop"


class BeforeAfterSlide(_BaseSlide):
    layout_type: Literal["before_after"] = "before_after"


class RiskOpportunitySlide(_BaseSlide):
    layout_type: Literal["risk_opportunity"] = "risk_opportunity"


class RecommendationWithRationaleSlide(_BaseSlide):
    layout_type: Literal["recommendation_with_rationale"] = "recommendation_with_rationale"


class SectionDividerSlide(_BaseSlide):
    layout_type: Literal["section_divider"] = "section_divider"


class BeforeAfterDetailedSlide(_BaseSlide):
    layout_type: Literal["before_after_detailed"] = "before_after_detailed"


class KpiTrendCardsSlide(_BaseSlide):
    layout_type: Literal["kpi_trend_cards"] = "kpi_trend_cards"


class ThreeColumnComparisonSlide(_BaseSlide):
    layout_type: Literal["three_column_comparison"] = "three_column_comparison"


class HorizontalProcessSlide(_BaseSlide):
    layout_type: Literal["horizontal_process"] = "horizontal_process"


class DecisionTreeSlide(_BaseSlide):
    layout_type: Literal["decision_tree"] = "decision_tree"


class HierarchyTreeSlide(_BaseSlide):
    layout_type: Literal["hierarchy_tree"] = "hierarchy_tree"


class EcosystemMapSlide(_BaseSlide):
    layout_type: Literal["ecosystem_map"] = "ecosystem_map"


class ProcessWithDecisionsSlide(_BaseSlide):
    layout_type: Literal["process_with_decisions"] = "process_with_decisions"


class SourceDeepDiveSlide(_BaseSlide):
    layout_type: Literal["source_deep_dive"] = "source_deep_dive"


class CircularProcessSlide(_BaseSlide):
    layout_type: Literal["circular_process"] = "circular_process"


class FreeformGridSlide(_BaseSlide):
    layout_type: Literal["freeform_grid"] = "freeform_grid"


class PillComparisonSlide(_BaseSlide):
    layout_type: Literal["pill_comparison"] = "pill_comparison"


class ChartSlide(_BaseSlide):
    layout_type: Literal[
        "grouped_bar_chart",
        "stacked_bar_chart",
        "waterfall_chart",
        "heatmap",
    ] = "grouped_bar_chart"


class LineChartSlide(_BaseSlide):
    layout_type: Literal["line_chart"] = "line_chart"


class ComboChartSlide(_BaseSlide):
    layout_type: Literal["combo_chart"] = "combo_chart"


class DualChartSlide(_BaseSlide):
    layout_type: Literal["dual_chart"] = "dual_chart"


# ---------------------------------------------------------------------------
# Discriminated union
# ---------------------------------------------------------------------------

ValidatedSlide = Union[
    TitleSlide,
    SplitTextVisualSlide,
    MetricDashboardSlide,
    MetricRowWithBreakdownSlide,
    InsightWithEvidenceSlide,
    PriorityMatrixSlide,
    EvidenceCardsSlide,
    DataTableWithInsightSlide,
    ComparisonWithMetricsSlide,
    SystemArchitectureSlide,
    DataFlowDiagramSlide,
    CausalLoopSlide,
    BeforeAfterSlide,
    RiskOpportunitySlide,
    RecommendationWithRationaleSlide,
    SectionDividerSlide,
    BeforeAfterDetailedSlide,
    KpiTrendCardsSlide,
    ThreeColumnComparisonSlide,
    HorizontalProcessSlide,
    DecisionTreeSlide,
    HierarchyTreeSlide,
    EcosystemMapSlide,
    ProcessWithDecisionsSlide,
    SourceDeepDiveSlide,
    CircularProcessSlide,
    DataTableSlide,
    ProcessFlowSlide,
    ComparisonGridSlide,
    QuoteCardSlide,
    IconGridSlide,
    FreeformGridSlide,
    PillComparisonSlide,
    ChartSlide,
    LineChartSlide,
    ComboChartSlide,
    DualChartSlide,
]

# Layout types that map to the fallback when validation fails.
_FALLBACK_LAYOUT = "split_text_visual"


def validate_slide(raw: Dict[str, Any]) -> tuple[ValidatedSlide | None, str | None]:
    """Validate a single slide dict against the discriminated union.

    Returns (validated_model, error_message).  On failure the model is None
    and the error describes what went wrong.
    """
    lt = (raw.get("layout_type") or "").strip().lower()
    if not lt:
        return None, "missing layout_type"

    # Route to the correct model based on layout_type
    model_map: dict[str, type[_BaseSlide]] = {
        "title_or_opening": TitleSlide,
        "split_text_visual": SplitTextVisualSlide,
        "metric_dashboard": MetricDashboardSlide,
        "metric": MetricDashboardSlide,
        "metric_row_with_breakdown": MetricRowWithBreakdownSlide,
        "insight_with_evidence": InsightWithEvidenceSlide,
        "priority_matrix": PriorityMatrixSlide,
        "evidence_cards": EvidenceCardsSlide,
        "data_table_with_insight": DataTableWithInsightSlide,
        "comparison_with_metrics": ComparisonWithMetricsSlide,
        "system_architecture": SystemArchitectureSlide,
        "data_flow_diagram": DataFlowDiagramSlide,
        "causal_loop": CausalLoopSlide,
        "before_after": BeforeAfterSlide,
        "risk_opportunity": RiskOpportunitySlide,
        "recommendation_with_rationale": RecommendationWithRationaleSlide,
        "section_divider": SectionDividerSlide,
        "before_after_detailed": BeforeAfterDetailedSlide,
        "kpi_trend_cards": KpiTrendCardsSlide,
        "three_column_comparison": ThreeColumnComparisonSlide,
        "horizontal_process": HorizontalProcessSlide,
        "decision_tree": DecisionTreeSlide,
        "hierarchy_tree": HierarchyTreeSlide,
        "ecosystem_map": EcosystemMapSlide,
        "process_with_decisions": ProcessWithDecisionsSlide,
        "source_deep_dive": SourceDeepDiveSlide,
        "circular_process": CircularProcessSlide,
        "data_table": DataTableSlide,
        "table": DataTableSlide,
        "full_process_flow": ProcessFlowSlide,
        "timeline": ProcessFlowSlide,
        "roadmap": ProcessFlowSlide,
        "comparison_grid": ComparisonGridSlide,
        "quote_card": QuoteCardSlide,
        "icon_grid": IconGridSlide,
        "freeform_grid": FreeformGridSlide,
        "pill_comparison": PillComparisonSlide,
        "grouped_bar_chart": ChartSlide,
        "stacked_bar_chart": ChartSlide,
        "waterfall_chart": ChartSlide,
        "heatmap": ChartSlide,
        "line_chart": LineChartSlide,
        "combo_chart": ComboChartSlide,
        "dual_chart": DualChartSlide,
    }

    model_cls = model_map.get(lt)
    if model_cls is None:
        return None, f"unknown layout_type: {lt!r}"

    try:
        return model_cls.model_validate(raw), None
    except Exception as e:
        return None, f"validation error for {lt}: {e}"


def validate_handoff(raw: Dict[str, Any]) -> tuple[List[ValidatedSlide], List[str]]:
    """Validate all slides in a handoff dict.

    Returns (validated_slides, error_messages).  Slides that fail validation
    are replaced with a minimal fallback model; errors are collected for
    logging.
    """
    slides_raw = raw.get("slides") or []
    validated: List[ValidatedSlide] = []
    errors: List[str] = []

    for i, slide_raw in enumerate(slides_raw):
        if not isinstance(slide_raw, dict):
            errors.append(f"slide {i+1}: not a dict")
            # minimal fallback
            fallback = SplitTextVisualSlide(
                slide_number=i + 1,
                title=f"Slide {i+1}",
                content=SlideContent(bullets=["(validation fallback)"]),
            )
            validated.append(fallback)
            continue

        model, err = validate_slide(slide_raw)
        if model is not None:
            validated.append(model)
        else:
            errors.append(f"slide {i+1} ({slide_raw.get('layout_type', '?')}): {err}")
            fallback = SplitTextVisualSlide(
                slide_number=slide_raw.get("slide_number", i + 1),
                title=slide_raw.get("title", f"Slide {i+1}"),
                content=SlideContent(
                    bullets=slide_raw.get("content", {}).get("bullets", []),
                    body_text=slide_raw.get("content", {}).get("body_text", ""),
                ),
                visual_spec=slide_raw.get("visual_spec"),
            )
            validated.append(fallback)

    return validated, errors
