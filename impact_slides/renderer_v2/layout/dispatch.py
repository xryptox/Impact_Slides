"""layout_type → recipe dispatch (plus optional freeform grid override)."""
from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any, Mapping

from ..charts import is_chart_layout
from ..disclosure import inject_disclosure
from ..layouts import CHART_LAYOUTS, FALLBACK_LAYOUT, canonical
from ..slide_view import visual_type as _sv_visual_type
from . import freeform, recipes

# Recipes that take ``use_chartjs=`` (see recipes.render_chart et al.).
_PASSES_CHARTJS = frozenset(CHART_LAYOUTS - {"icon_grid"}) | frozenset(
    {"dual_chart", "chart_hero_dual", "multi_panel"}
)

# Single map: layout_type → recipe. Aliases resolve in ``resolve_layout`` before
# lookup. ``brand_divider`` reuses brand_cover via partial (stdlib).
LAYOUT_RECIPES: dict[str, Callable[..., str]] = {
    "grouped_bar_chart": recipes.render_chart,
    "stacked_bar_chart": recipes.render_chart,
    "horizontal_bar_chart": recipes.render_chart,
    "waterfall_chart": recipes.render_chart,
    "heatmap": recipes.render_chart,
    "line_chart": recipes.render_chart,
    "combo_chart": recipes.render_chart,
    "icon_grid": recipes.render_icon_grid,
    "dual_chart": recipes.render_dual_chart,
    "title_or_opening": recipes.render_title,
    "split_text_visual": recipes.render_split,
    "metric_dashboard": recipes.render_metric,
    "metric_row_with_breakdown": recipes.render_metric_row_with_breakdown,
    "insight_with_evidence": recipes.render_insight_with_evidence,
    "priority_matrix": recipes.render_priority_matrix,
    "data_table": recipes.render_table,
    "pill_comparison": recipes.render_pill_comparison,
    "chart_hero_dual": recipes.render_chart_hero_dual,
    "ir_bullet_sheet": recipes.render_ir_bullet_sheet,
    "guidance_statement_card": recipes.render_guidance_statement_card,
    "brand_cover": recipes.render_brand_cover,
    "brand_divider": partial(recipes.render_brand_cover, divider=True),
    "annex_table": recipes.render_annex_table,
    "grouped_annex_table": recipes.render_grouped_annex_table,
    "multi_panel": recipes.render_multi_panel,
    "full_process_flow": recipes.render_process,
    "timeline": recipes.render_process,
    "roadmap": recipes.render_process,
    "comparison_grid": recipes.render_comparison,
    "evidence_cards": recipes.render_evidence_cards,
    "data_table_with_insight": recipes.render_data_table_with_insight,
    "comparison_with_metrics": recipes.render_comparison_with_metrics,
    "system_architecture": recipes.render_system_architecture,
    "data_flow_diagram": recipes.render_data_flow_diagram,
    "causal_loop": recipes.render_causal_loop,
    "before_after": recipes.render_before_after,
    "quote_card": recipes.render_quote,
    "risk_opportunity": recipes.render_risk_opportunity,
    "recommendation_with_rationale": recipes.render_recommendation_with_rationale,
    "section_divider": recipes.render_section_divider,
    "before_after_detailed": recipes.render_before_after_detailed,
    "kpi_trend_cards": recipes.render_kpi_trend_cards,
    "three_column_comparison": recipes.render_three_column_comparison,
    "horizontal_process": recipes.render_horizontal_process,
    "decision_tree": recipes.render_decision_tree,
    "hierarchy_tree": recipes.render_hierarchy_tree,
    "ecosystem_map": recipes.render_ecosystem_map,
    "process_with_decisions": recipes.render_process_with_decisions,
    "source_deep_dive": recipes.render_source_deep_dive,
    "circular_process": recipes.render_circular_process,
}


def _primary_visual_type(slide: Mapping[str, Any]) -> str:
    return _sv_visual_type(slide)


def resolve_layout(slide: Mapping[str, Any]) -> str:
    """Canonical layout_type for a slide.

    Aliases resolve here (via ``layouts.canonical``) rather than per-recipe, so a
    spelling schemas accepts cannot fall through to the fallback and silently
    drop content — which is what ``metric`` and ``table`` used to do.
    """
    lt = canonical(slide.get("layout_type"))
    if not lt:
        return _primary_visual_type(slide) or FALLBACK_LAYOUT
    return lt


def render_slide(
    slide: Mapping[str, Any],
    *,
    total: int,
    notes: str,
    active: bool = False,
    use_chartjs: bool = False,
    disclosure_html: str | None = None,
) -> str:
    html = _render_slide_body(
        slide, total=total, notes=notes, active=active, use_chartjs=use_chartjs
    )
    return inject_disclosure(html, slide, prebuilt=disclosure_html)


def _render_slide_body(
    slide: Mapping[str, Any],
    *,
    total: int,
    notes: str,
    active: bool = False,
    use_chartjs: bool = False,
) -> str:
    # Phase 7: freeform visual_spec.grid wins over layout recipe body
    # (still uses gl-slide shell + gl-* slot chrome).
    if freeform.has_freeform_grid(slide):
        return recipes.render_freeform(slide, total, notes, active=active)

    lt = resolve_layout(slide)
    fn = LAYOUT_RECIPES.get(lt)
    if fn is None:
        # Unknown layout_type: only chart primary_visual may still route;
        # everything else falls back to split (same as the old ladder tail).
        pvt = _primary_visual_type(slide)
        if is_chart_layout(pvt):
            lt = pvt
            fn = LAYOUT_RECIPES.get(lt)
        if fn is None:
            return recipes.render_split(slide, total, notes, active=active)

    # Chart pack reads slide["layout_type"] — stamp the resolved name when the
    # type was inferred (unspecified layout / primary_visual fallback).
    if lt in CHART_LAYOUTS:
        slide = {**slide, "layout_type": lt}

    if lt in _PASSES_CHARTJS:
        return fn(slide, total, notes, active=active, use_chartjs=use_chartjs)
    return fn(slide, total, notes, active=active)
