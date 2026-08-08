"""Chart layout entry points and SVG fallback dispatch."""
from __future__ import annotations

from typing import Any, Mapping
from ..strip import esc, strip_eids
from ..layouts import CHART_LAYOUTS as _CHART_LAYOUTS
from ..layouts import CHARTJS_LAYOUTS as _CHARTJS_LAYOUTS
from ..slide_view import content as _sv_content
from ..slide_view import steps as _sv_steps



def is_chart_layout(layout_type: str) -> bool:
    return (layout_type or "").lower().strip() in _CHART_LAYOUTS



def _icon_svg(name: str, cls: str = "icon") -> str:
    # name may be "ic-growth" or "growth"
    href = name if name.startswith("#") else (
        name if name.startswith("ic-") else f"ic-{name}"
    )
    if not href.startswith("#"):
        href = "#" + href
    return (
        f'<svg class="{esc(cls)}" viewBox="0 0 24 24" aria-hidden="true">'
        f'<use href="{href}"/></svg>'
    )



def _steps(slide: Mapping[str, Any]) -> list[Any]:
    return _sv_steps(slide)



# ---------------------------------------------------------------------------
# Line chart (internal SVG, zero external dependency)
# ---------------------------------------------------------------------------


def _chart_config(slide: Mapping[str, Any]) -> dict[str, Any]:
    """Extract optional chart configuration from visual_spec.

    Chart_config may live at visual_spec.chart_config (legacy) or, as real
    handoffs author it, visual_spec.primary_visual.chart_config (#71/F15).
    The primary_visual block is the normative location; a top-level block
    overrides it key-by-key. This unblocks the path split where both painters
    silently ignored nested config.
    """
    vs = slide.get("visual_spec") or {}
    if not isinstance(vs, dict):
        return {}
    merged: dict[str, Any] = {}
    pv = vs.get("primary_visual")
    if isinstance(pv, dict) and isinstance(pv.get("chart_config"), dict):
        merged.update(pv["chart_config"])
    top = vs.get("chart_config")
    if isinstance(top, dict):
        merged.update(top)
    return merged



def build_icon_grid_html(slide: Mapping[str, Any]) -> str:
    return _fallback_icon_grid(slide)



def _fallback_icon_grid(slide: Mapping[str, Any]) -> str:
    tiles_src = _steps(slide)
    c = _sv_content(slide)
    if not tiles_src:
        tiles_src = c.get("bullets") or []
    tiles = []
    icons = ["growth", "globe", "users", "building", "chart-bar", "layers"]
    for i, raw in enumerate(tiles_src[:6]):
        if isinstance(raw, dict):
            title = strip_eids(raw.get("title") or raw.get("label") or "")
            # Per-step description is a body alias (#126). primary_visual-level
            # description remains a non-rendered human caption (spec).
            body = strip_eids(
                raw.get("body") or raw.get("text") or raw.get("description") or ""
            )
            ic = raw.get("icon") or icons[i % len(icons)]
        elif isinstance(raw, str) and ":" in raw:
            title, _, body = raw.partition(":")
            title, body, ic = title.strip(), body.strip(), icons[i % len(icons)]
        else:
            title, body, ic = strip_eids(raw), "", icons[i % len(icons)]
        tiles.append(
            f'<div class="icon-tile gl-card" style="padding:22px">'
            f"{_icon_svg(ic, 'icon ic')}"
            f'<div class="tile-title">{esc(title)}</div>'
            f'<div class="tile-body">{esc(body)}</div></div>'
        )
    cols = "gl-grid-3" if len(tiles) >= 3 else "gl-grid-2"
    if not tiles:
        return '<p class="chart-empty">No icon tiles</p>'
    return f'<div class="gl-grid {cols} layout-icon-grid">{"".join(tiles)}</div>'

from .bars import _build_grouped_bar_svg, _build_hbar_svg, _build_stacked_bar_svg
from .lines import _build_combo_chart_svg, _build_line_chart_svg
from .matrix import _build_heatmap_html, _build_waterfall_svg, _fallback_matrix_chart



def _svg_fallback_for_layout(
    slide: Mapping[str, Any],
    layout: str,
    *,
    record_diagnostic: bool = True,
    host_w: float | None = None,
    host_h: float | None = None,
) -> str:
    """Static SVG painter for a Chart.js MVP layout (JS-off / noscript path)."""
    from ..slide_view import primary_visual
    from .auto_typography import (
        chart_host_dimensions,
        compute_auto_plan_for_slide,
        plan_to_data_attrs,
        record_auto_diagnostic,
    )

    cfg = _chart_config(slide)
    default_w, default_h = chart_host_dimensions(layout)
    width = default_w if host_w is None else host_w
    height = default_h if host_h is None else host_h
    cfg["_auto_host_w"] = width
    cfg["_auto_host_h"] = height
    plan = compute_auto_plan_for_slide(
        slide, layout, host_w=width, host_h=height, chart_cfg=cfg
    )
    if plan is not None:
        cfg["_auto_typo_plan"] = plan
        primary = {**primary_visual(slide), "chart_config": cfg}
        visual_spec = dict(slide.get("visual_spec") or {})
        visual_spec["primary_visual"] = primary
        visual_spec["chart_config"] = cfg
        slide = {**slide, "visual_spec": visual_spec}
        if record_diagnostic:
            record_auto_diagnostic(
                {**plan.diagnostic_dict(), "slide_number": slide.get("slide_number")}
            )
    if layout == "line_chart":
        rendered = _build_line_chart_svg(slide)
    elif layout == "combo_chart":
        rendered = _build_combo_chart_svg(slide)
    elif layout == "grouped_bar_chart":
        rendered = _build_grouped_bar_svg(slide)
    elif layout == "stacked_bar_chart":
        rendered = _build_stacked_bar_svg(slide)
    elif layout == "horizontal_bar_chart":
        rendered = _build_hbar_svg(slide)
    elif layout == "heatmap":
        rendered = _build_heatmap_html(slide)
    elif layout == "waterfall_chart":
        rendered = _build_waterfall_svg(slide)
    else:
        rendered = ""
    value_axis_visible = cfg.get(
        "show_x_axis" if layout == "horizontal_bar_chart" else "show_y_axis"
    ) is not False
    return f'<div class="chart-svg-wrap"{plan_to_data_attrs(plan, value_axis_visible=value_axis_visible)}>{rendered}</div>' if plan else rendered

from .chartjs import _build_chartjs_html



def build_chart_html(
    slide: Mapping[str, Any],
    layout: str,
    *,
    use_chartjs: bool = False,
    host_w: float | None = None,
    host_h: float | None = None,
) -> str:
    lt = (layout or slide.get("layout_type") or "").lower()
    if use_chartjs and lt in _CHARTJS_LAYOUTS:
        js_html = _build_chartjs_html(slide, lt, host_w=host_w, host_h=host_h)
        if js_html:
            return js_html
        # Fall through to SVG if config could not be built
    # Internal SVG painters (also used as Chart.js noscript fallback).
    svg = _svg_fallback_for_layout(slide, lt, host_w=host_w, host_h=host_h)
    if svg:
        return svg
    if lt == "stacked_bar_chart":
        return _build_stacked_bar_svg(slide)
    return _fallback_matrix_chart(slide, lt)
