"""layout_type → recipe dispatch (plus optional freeform grid override)."""
from __future__ import annotations

from typing import Any, Mapping

from ..charts import is_chart_layout
from . import freeform, recipes


def _primary_visual_type(slide: Mapping[str, Any]) -> str:
    vs = slide.get("visual_spec") or {}
    if not isinstance(vs, dict):
        return ""
    pv = vs.get("primary_visual") or {}
    if not isinstance(pv, dict):
        return ""
    return str(pv.get("type") or "").lower().strip()


def resolve_layout(slide: Mapping[str, Any]) -> str:
    lt = (slide.get("layout_type") or "split_text_visual").lower().strip()
    if lt in ("other", "", "default"):
        pvt = _primary_visual_type(slide)
        if pvt:
            return pvt
        return "split_text_visual"
    return lt


def render_slide(
    slide: Mapping[str, Any],
    *,
    total: int,
    notes: str,
    active: bool = False,
) -> str:
    # Phase 7: freeform visual_spec.grid wins over layout recipe body
    # (still uses gl-slide shell + gl-* slot chrome).
    if freeform.has_freeform_grid(slide):
        return recipes.render_freeform(slide, total, notes, active=active)

    lt = resolve_layout(slide)
    # chart pack (includes icon_grid)
    if is_chart_layout(lt) or lt in (
        "grouped_bar_chart",
        "stacked_bar_chart",
        "waterfall_chart",
        "heatmap",
    ):
        if lt == "icon_grid":
            return recipes.render_icon_grid(slide, total, notes, active=active)
        s = dict(slide)
        s["layout_type"] = lt
        return recipes.render_chart(s, total, notes, active=active)

    if lt == "dual_chart":
        return recipes.render_dual_chart(slide, total, notes, active=active)

    if lt == "icon_grid":
        return recipes.render_icon_grid(slide, total, notes, active=active)
    if lt in ("title_or_opening", "cover"):
        return recipes.render_title(slide, total, notes, active=active)
    if lt == "split_text_visual":
        return recipes.render_split(slide, total, notes, active=active)
    if lt == "metric_dashboard":
        return recipes.render_metric(slide, total, notes, active=active)
    if lt == "metric_row_with_breakdown":
        return recipes.render_metric_row_with_breakdown(slide, total, notes, active=active)
    if lt == "insight_with_evidence":
        return recipes.render_insight_with_evidence(slide, total, notes, active=active)
    if lt == "priority_matrix":
        return recipes.render_priority_matrix(slide, total, notes, active=active)
    if lt == "data_table":
        return recipes.render_table(slide, total, notes, active=active)
    if lt in ("full_process_flow", "timeline", "roadmap"):
        return recipes.render_process(slide, total, notes, active=active)
    if lt == "comparison_grid":
        return recipes.render_comparison(slide, total, notes, active=active)
    if lt == "evidence_cards":
        return recipes.render_evidence_cards(slide, total, notes, active=active)
    if lt == "data_table_with_insight":
        return recipes.render_data_table_with_insight(slide, total, notes, active=active)
    if lt == "comparison_with_metrics":
        return recipes.render_comparison_with_metrics(slide, total, notes, active=active)
    if lt == "system_architecture":
        return recipes.render_system_architecture(slide, total, notes, active=active)
    if lt == "data_flow_diagram":
        return recipes.render_data_flow_diagram(slide, total, notes, active=active)
    if lt == "causal_loop":
        return recipes.render_causal_loop(slide, total, notes, active=active)
    if lt == "before_after":
        return recipes.render_before_after(slide, total, notes, active=active)
    if lt == "quote_card":
        return recipes.render_quote(slide, total, notes, active=active)
    if lt == "risk_opportunity":
        return recipes.render_risk_opportunity(slide, total, notes, active=active)
    if lt == "recommendation_with_rationale":
        return recipes.render_recommendation_with_rationale(slide, total, notes, active=active)
    if lt == "section_divider":
        return recipes.render_section_divider(slide, total, notes, active=active)
    if lt == "before_after_detailed":
        return recipes.render_before_after_detailed(slide, total, notes, active=active)
    if lt == "kpi_trend_cards":
        return recipes.render_kpi_trend_cards(slide, total, notes, active=active)
    if lt == "three_column_comparison":
        return recipes.render_three_column_comparison(slide, total, notes, active=active)
    if lt == "horizontal_process":
        return recipes.render_horizontal_process(slide, total, notes, active=active)
    if lt == "decision_tree":
        return recipes.render_decision_tree(slide, total, notes, active=active)
    if lt == "hierarchy_tree":
        return recipes.render_hierarchy_tree(slide, total, notes, active=active)
    if lt == "ecosystem_map":
        return recipes.render_ecosystem_map(slide, total, notes, active=active)
    if lt == "process_with_decisions":
        return recipes.render_process_with_decisions(slide, total, notes, active=active)
    if lt == "source_deep_dive":
        return recipes.render_source_deep_dive(slide, total, notes, active=active)
    if lt == "circular_process":
        return recipes.render_circular_process(slide, total, notes, active=active)

    pvt = _primary_visual_type(slide)
    if is_chart_layout(pvt):
        s = dict(slide)
        s["layout_type"] = pvt
        if pvt == "icon_grid":
            return recipes.render_icon_grid(s, total, notes, active=active)
        return recipes.render_chart(s, total, notes, active=active)

    return recipes.render_split(slide, total, notes, active=active)
