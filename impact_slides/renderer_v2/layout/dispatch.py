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

    if lt == "icon_grid":
        return recipes.render_icon_grid(slide, total, notes, active=active)
    if lt in ("title_or_opening", "cover"):
        return recipes.render_title(slide, total, notes, active=active)
    if lt == "split_text_visual":
        return recipes.render_split(slide, total, notes, active=active)
    if lt == "metric_dashboard":
        return recipes.render_metric(slide, total, notes, active=active)
    if lt == "data_table":
        return recipes.render_table(slide, total, notes, active=active)
    if lt in ("full_process_flow", "timeline", "roadmap"):
        return recipes.render_process(slide, total, notes, active=active)
    if lt == "comparison_grid":
        return recipes.render_comparison(slide, total, notes, active=active)
    if lt == "quote_card":
        return recipes.render_quote(slide, total, notes, active=active)

    pvt = _primary_visual_type(slide)
    if is_chart_layout(pvt):
        s = dict(slide)
        s["layout_type"] = pvt
        if pvt == "icon_grid":
            return recipes.render_icon_grid(s, total, notes, active=active)
        return recipes.render_chart(s, total, notes, active=active)

    return recipes.render_split(slide, total, notes, active=active)
