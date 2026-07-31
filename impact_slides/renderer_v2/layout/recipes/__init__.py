"""Boardroom layout recipes composed from gl-* primitives.

Package facade: family modules hold the implementations; this module
re-exports every name so ``from ...layout.recipes import X`` and
``recipes.X`` keep working (same object identity for mock.patch).
"""
from __future__ import annotations

from .shared import _DATE_LEAD, _END_YEAR, _LABEL_COLON, _CLOSED_LOOP, _REGIONISH, _content, _vs_steps, _so_what, _source_names, argument_kicker, panel_kicker, split_step_copy, apply_timeline_year_overrides, pair_comparison, _is_matrix, right_panel_model, near, _bullets_html, _proof_html, _fact_html, _kpi_cards, _stat_label_value, _table_inset, _circle_pair_svg, _table_matrix, table_as_kpi, _hero_stack, _sequential_grid, _is_series_num, _visual_series_names
from .metrics import render_metric, render_table, render_metric_row_with_breakdown, render_data_table_with_insight, render_annex_table, render_kpi_trend_cards, render_ir_bullet_sheet, render_guidance_statement_card
from .covers import render_title, render_brand_cover, render_section_divider, render_quote
from .comparison import render_pill_comparison, render_comparison, render_comparison_with_metrics, render_three_column_comparison, render_before_after, render_before_after_detailed, render_split
from .timeline import render_process, render_horizontal_process, render_circular_process, render_process_with_decisions
from .charts import render_chart, render_dual_chart, render_chart_hero_dual, render_icon_grid, render_multi_panel, render_priority_matrix
from .cards import render_evidence_cards, render_insight_with_evidence, render_risk_opportunity, render_recommendation_with_rationale, render_source_deep_dive
from .diagrams import render_system_architecture, render_data_flow_diagram, render_causal_loop, render_decision_tree, render_hierarchy_tree, render_ecosystem_map, render_freeform

__all__ = [
    '_CLOSED_LOOP',
    '_DATE_LEAD',
    '_END_YEAR',
    '_LABEL_COLON',
    '_REGIONISH',
    '_bullets_html',
    '_circle_pair_svg',
    '_content',
    '_fact_html',
    '_hero_stack',
    '_is_matrix',
    '_is_series_num',
    '_kpi_cards',
    '_proof_html',
    '_sequential_grid',
    '_so_what',
    '_source_names',
    '_stat_label_value',
    '_table_inset',
    '_table_matrix',
    '_visual_series_names',
    '_vs_steps',
    'apply_timeline_year_overrides',
    'argument_kicker',
    'near',
    'pair_comparison',
    'panel_kicker',
    'render_annex_table',
    'render_before_after',
    'render_before_after_detailed',
    'render_brand_cover',
    'render_causal_loop',
    'render_chart',
    'render_chart_hero_dual',
    'render_circular_process',
    'render_comparison',
    'render_comparison_with_metrics',
    'render_data_flow_diagram',
    'render_data_table_with_insight',
    'render_decision_tree',
    'render_dual_chart',
    'render_ecosystem_map',
    'render_evidence_cards',
    'render_freeform',
    'render_guidance_statement_card',
    'render_hierarchy_tree',
    'render_horizontal_process',
    'render_icon_grid',
    'render_insight_with_evidence',
    'render_ir_bullet_sheet',
    'render_kpi_trend_cards',
    'render_metric',
    'render_metric_row_with_breakdown',
    'render_multi_panel',
    'render_pill_comparison',
    'render_priority_matrix',
    'render_process',
    'render_process_with_decisions',
    'render_quote',
    'render_recommendation_with_rationale',
    'render_risk_opportunity',
    'render_section_divider',
    'render_source_deep_dive',
    'render_split',
    'render_system_architecture',
    'render_table',
    'render_three_column_comparison',
    'render_title',
    'right_panel_model',
    'split_step_copy',
    'table_as_kpi',
]
