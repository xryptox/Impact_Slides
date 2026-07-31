"""Dispatch registry parity — every LAYOUT_RECIPES key routes to its recipe.

The old harness patched ``recipes.render_*`` and inspected which mock ran.
That works against an if-ladder (name resolved at call time) but not against
LAYOUT_RECIPES, which binds callables at import time. Patch the registry.
"""
from __future__ import annotations

import functools
import inspect
from unittest.mock import MagicMock

from impact_slides.renderer_v2.layout import dispatch
from impact_slides.renderer_v2.layout.dispatch import (
    LAYOUT_RECIPES,
    _PASSES_CHARTJS,
    render_slide,
)


def _base_name(fn) -> str:
    target = fn.func if isinstance(fn, functools.partial) else fn
    return target.__name__


# Ground truth captured from wiki/renderer_v2_LAYOUTS.md at 3d1fdc9 -- generated
# from the if-ladder *before* LAYOUT_RECIPES existed, so it is independent of the
# registry it checks. `cover` is absent deliberately: it is now resolved to
# `title_or_opening` by layouts.ALIASES rather than owning a registry entry.
_LADDER_PARITY = {
    "annex_table": "render_annex_table",
    "before_after": "render_before_after",
    "before_after_detailed": "render_before_after_detailed",
    "brand_cover": "render_brand_cover",
    "brand_divider": "render_brand_cover",
    "causal_loop": "render_causal_loop",
    "chart_hero_dual": "render_chart_hero_dual",
    "circular_process": "render_circular_process",
    "combo_chart": "render_chart",
    "comparison_grid": "render_comparison",
    "comparison_with_metrics": "render_comparison_with_metrics",
    "data_flow_diagram": "render_data_flow_diagram",
    "data_table": "render_table",
    "data_table_with_insight": "render_data_table_with_insight",
    "decision_tree": "render_decision_tree",
    "dual_chart": "render_dual_chart",
    "ecosystem_map": "render_ecosystem_map",
    "evidence_cards": "render_evidence_cards",
    "full_process_flow": "render_process",
    "grouped_bar_chart": "render_chart",
    "guidance_statement_card": "render_guidance_statement_card",
    "heatmap": "render_chart",
    "hierarchy_tree": "render_hierarchy_tree",
    "horizontal_bar_chart": "render_chart",
    "horizontal_process": "render_horizontal_process",
    "icon_grid": "render_icon_grid",
    "insight_with_evidence": "render_insight_with_evidence",
    "ir_bullet_sheet": "render_ir_bullet_sheet",
    "kpi_trend_cards": "render_kpi_trend_cards",
    "line_chart": "render_chart",
    "metric_dashboard": "render_metric",
    "metric_row_with_breakdown": "render_metric_row_with_breakdown",
    "multi_panel": "render_multi_panel",
    "pill_comparison": "render_pill_comparison",
    "priority_matrix": "render_priority_matrix",
    "process_with_decisions": "render_process_with_decisions",
    "quote_card": "render_quote",
    "recommendation_with_rationale": "render_recommendation_with_rationale",
    "risk_opportunity": "render_risk_opportunity",
    "roadmap": "render_process",
    "section_divider": "render_section_divider",
    "source_deep_dive": "render_source_deep_dive",
    "split_text_visual": "render_split",
    "stacked_bar_chart": "render_chart",
    "system_architecture": "render_system_architecture",
    "three_column_comparison": "render_three_column_comparison",
    "timeline": "render_process",
    "title_or_opening": "render_title",
    "waterfall_chart": "render_chart",
}


def test_registry_matches_pre_refactor_ladder():
    """Registry maps each layout to the same recipe the if-ladder did.

    This is the actual parity assertion. test_every_layout_routes_to_its_recipe
    below only proves the registry is *wired up* (it installs a mock at key X
    then renders X, so it cannot notice X pointing at the wrong recipe). Pinning
    against ladder-era ground truth is what catches a mis-mapped entry.
    """
    actual = {lt: _base_name(fn) for lt, fn in LAYOUT_RECIPES.items()}
    assert actual == _LADDER_PARITY


# Layouts that must reach their recipe with pre-bound kwargs. Pinned here rather
# than read off the registry entry, so deleting the partial fails the test.
_BOUND_KWARGS = {"brand_divider": {"divider": True}}


def test_bound_kwargs_are_pinned():
    """`brand_divider` must pass divider=True, else it renders as a plain cover."""
    for lt, expected in _BOUND_KWARGS.items():
        fn = LAYOUT_RECIPES[lt]
        assert isinstance(fn, functools.partial), f"{lt} must stay a partial"
        for key, value in expected.items():
            assert fn.keywords.get(key) == value, f"{lt}: expected {key}={value}"


def test_cover_alias_still_reaches_title():
    """`cover` lost its registry entry to ALIASES; it must still route."""
    assert "cover" not in LAYOUT_RECIPES
    assert dispatch.resolve_layout({"layout_type": "cover"}) == "title_or_opening"


def test_every_layout_routes_to_its_recipe():
    """Each registry entry is actually invoked, with bound partial kwargs.

    Wiring check only -- see test_registry_matches_pre_refactor_ladder for the
    mapping assertion.
    """
    original = dict(LAYOUT_RECIPES)
    try:
        for lt, fn in original.items():
            mock = MagicMock(return_value=f"<!--{lt}-->")
            if isinstance(fn, functools.partial):
                # Keep bound kwargs (e.g. divider=True).
                dispatch.LAYOUT_RECIPES[lt] = functools.partial(mock, **fn.keywords)
            else:
                dispatch.LAYOUT_RECIPES[lt] = mock

            slide = {"slide_number": 1, "layout_type": lt, "title": lt, "content": {}}
            render_slide(slide, total=1, notes="")
            assert mock.called, f"{lt} ({_base_name(fn)}): recipe not called"
            if isinstance(fn, functools.partial) and fn.keywords:
                _, kwargs = mock.call_args
                for k, v in fn.keywords.items():
                    assert kwargs.get(k) == v, f"{lt}: missing bound kwarg {k}={v}"
    finally:
        dispatch.LAYOUT_RECIPES.clear()
        dispatch.LAYOUT_RECIPES.update(original)


def test_passes_chartjs_matches_recipe_signatures():
    """_PASSES_CHARTJS must equal layouts whose recipe accepts use_chartjs=."""
    accepts: set[str] = set()
    for lt, fn in LAYOUT_RECIPES.items():
        target = fn.func if isinstance(fn, functools.partial) else fn
        if "use_chartjs" in inspect.signature(target).parameters:
            accepts.add(lt)
    assert _PASSES_CHARTJS == frozenset(accepts)
