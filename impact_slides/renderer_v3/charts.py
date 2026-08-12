"""Chart freeze + painters: axis charts (line/bars/waterfall/stacked) + native heatmap.

Covers D239/D240/D242–D243/D245/D247/D248/D302/D304/D307, shared D71–D73/D160
geometry, and D163/D246–D248/D308 semantic heatmaps.
"""
from __future__ import annotations

import html
import json
import math
from decimal import Decimal
from typing import Any, Mapping, Optional, Union

from .format import MISSING_ACCESSIBLE, MISSING_VISIBLE, format_semantic_value
from .models import (
    LINE_STYLE_PAIRS,
    ChartData,
    ComboChartVisual,
    GroupedBarChartVisual,
    HeatmapVisual,
    HorizontalBarChartVisual,
    LineChartVisual,
    MissingValue,
    NumberFormat,
    NumberValue,
    StackedBarChartVisual,
    WaterfallChartVisual,
)
from .theme import (
    chart_js_tokens,
    contrast_ratio,
    line_style_keys,
    marker_keys,
    resolve_color,
    resolve_series_colors,
)

AxisChartVisual = Union[
    LineChartVisual,
    GroupedBarChartVisual,
    HorizontalBarChartVisual,
    StackedBarChartVisual,
    ComboChartVisual,
    WaterfallChartVisual,
]
BarChartVisual = Union[
    GroupedBarChartVisual, HorizontalBarChartVisual, StackedBarChartVisual
]

# Theme-owned waterfall role fills (D162/D245/D307).
_WATERFALL_ROLE_COLOR = {
    "total": "navy",
    "computed_total": "navy",
    "increase": "primary_blue",
    "decrease": "neutral",
}
WATERFALL_SERIES_ID = "waterfall"
# Structural waterfall labels: 18–24px (D52/D307), not ordinary_values.
_WATERFALL_LABEL_BOUNDS = (18, 24)

# Heatmap sequential light → primary blue (D163/D246/D308) — theme palette only.
def _rgb(key: str, *, role: str) -> tuple[int, int, int]:
    h = resolve_color(key, role=role).lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


_HEAT_LIGHT = _rgb("sky_blue", role="fill")  # light end of sequential ramp
_HEAT_PRIMARY = _rgb("primary_blue", role="fill")
_HEAT_NAVY = resolve_color("navy", role="text_on_light")
_HEAT_WHITE = resolve_color("white", role="text_on_dark")

# Plot geometry on the 1920 content width (D68 stage; single_chart body region).
PLOT_W = 1400
PLOT_H = 620
PLOT_FLOOR_W = 320  # D47 absolute plot floor
PLOT_FLOOR_H = 240
PAD_L = 88
PAD_R = 160  # exterior identity/context lane
PAD_T = 28
PAD_B = 64
MARKER_R = 5
LABEL_CLEAR = MARKER_R + 4  # D53/D62 clearance
POINT_LABEL_CANDIDATES = ("above", "below", "left", "right", "leader")
# D160 theme-owned thickness bounds (px at 1920×1080).
BAR_MIN_THICKNESS = 12
BAR_MAX_THICKNESS = 56
BAR_CATEGORY_GAP_RATIO = 0.28
BAR_SERIES_GAP_RATIO = 0.12

# Chart typography floors / ceilings (D294).
_ROLE_BOUNDS: dict[str, tuple[int, int]] = {
    "category_ticks": (14, 24),
    "value_ticks": (14, 28),
    "ordinary_values": (14, 32),
    "segment_labels": (14, 24),  # stacked segments (D79/D304)
    "stack_totals": (14, 24),  # computed/authored totals (D79/D304)
    "legend": (16, 24),
    "series_labels": (16, 24),
    "axis_titles": (13, 24),
    "context_labels": (16, 24),
    "annotations": (13, 24),
}

_DASHARRAY = {
    "solid": None,
    "dashed": "8 6",
    "dotted": "2 4",
    "dash_dot": "10 4 2 4",
}


def freeze_line_chart(
    chart: LineChartVisual,
    formats: Mapping[str, NumberFormat],
    *,
    box_w: int = PLOT_W + PAD_L + PAD_R,
    box_h: int = PLOT_H + PAD_T + PAD_B + 80,
) -> dict[str, Any]:
    """Build one frozen painter-neutral chart plan (D69/D248/D302)."""
    fmt = formats[chart.value_axes.primary.format_id]
    data = chart.chart_data
    cats = list(data.categories)
    series_plans = _resolve_series(data)
    domain = _resolve_domain(chart, data)
    ticks = list(domain["ticks"])
    show_values = _ordinary_values_show(chart)

    # Geometry
    # D47 absolute plot floor; only surplus above may feed support.
    plot_w = max(PLOT_FLOOR_W, min(PLOT_W, box_w - PAD_L - PAD_R))
    plot_h = max(PLOT_FLOOR_H, min(PLOT_H, box_h - PAD_T - PAD_B - 40))
    n = len(cats)
    xs = [
        PAD_L + (plot_w * i / (n - 1) if n > 1 else plot_w / 2) for i in range(n)
    ]
    y_min = float(domain["min"])
    y_max = float(domain["max"])
    span = y_max - y_min or 1.0

    def y_of(v: float) -> float:
        return PAD_T + plot_h - ((v - y_min) / span) * plot_h

    points: list[dict[str, Any]] = []
    for s_i, sp in enumerate(series_plans):
        s = data.series[s_i]
        for c_i, cat in enumerate(cats):
            raw = s.values[c_i]
            if raw is None:
                points.append(
                    {
                        "series_id": sp["series_id"],
                        "category_id": cat.category_id,
                        "x": xs[c_i],
                        "y": None,
                        "value": None,
                        "visible": MISSING_VISIBLE,
                        "accessible": MISSING_ACCESSIBLE,
                        "finite": False,
                    }
                )
                continue
            num = float(Decimal(raw))
            fv = format_semantic_value(
                NumberValue(value=raw, format_id=chart.value_axes.primary.format_id),
                formats,
            )
            points.append(
                {
                    "series_id": sp["series_id"],
                    "category_id": cat.category_id,
                    "x": xs[c_i],
                    "y": y_of(num),
                    "value": raw,
                    "numeric": num,
                    "visible": fv.visible,
                    "accessible": fv.accessible,
                    "finite": True,
                }
            )

    role_sizes = _role_sizes(chart)
    # Endpoint lane fit: each series name must clear the right exterior pad (D15/D37).
    ser_px = role_sizes["series_labels"]
    endpoints_fit = all(
        len(sp["name"]) * ser_px * 0.55 <= PAD_R - 16 for sp in series_plans
    )
    identity = _identity_strategy(
        chart, series_plans, endpoints_fit=endpoints_fit
    )
    placements = _place_point_labels(
        points,
        series_plans,
        show_values=show_values,
        label_px=role_sizes["ordinary_values"],
        plot=(PAD_L, PAD_T, PAD_L + plot_w, PAD_T + plot_h),
        identity=identity,
    )

    tick_labels = [
        format_semantic_value(
            NumberValue(value=t, format_id=chart.value_axes.primary.format_id),
            formats,
        ).visible
        for t in ticks
    ]
    scale_label = fmt.scale_label

    table = _semantic_table(
        chart,
        formats,
        series_plans,
        domain,
        identity=identity,
        scale_label=scale_label,
    )

    return {
        "surface_id": chart.surface_id,
        "chart_type": "line",
        "heading": chart.heading,
        "subtitle": chart.subtitle,
        "categories": [
            {
                "category_id": c.category_id,
                "label": c.label,
                "short_label": c.short_label,
                "x": xs[i],
            }
            for i, c in enumerate(cats)
        ],
        "series": series_plans,
        "points": points,
        "placements": placements,
        "show_ordinary_values": show_values,
        "identity_strategy": identity,
        "role_sizes": role_sizes,
        "geometry": {
            "pad_l": PAD_L,
            "pad_r": PAD_R,
            "pad_t": PAD_T,
            "pad_b": PAD_B,
            "plot_w": plot_w,
            "plot_h": plot_h,
            "marker_r": MARKER_R,
            "view_w": PAD_L + plot_w + PAD_R,
            "view_h": PAD_T + plot_h + PAD_B,
        },
        "domain": domain,
        "tick_labels": tick_labels,
        "category_axis": {
            "visible": chart.category_axis.visible,
            "title": chart.category_axis.title,
        },
        "value_axis": {
            "visible": chart.value_axes.primary.visible,
            "title": chart.value_axes.primary.title,
            "format_id": chart.value_axes.primary.format_id,
            "leading_break": (
                chart.value_axes.primary.leading_break.to
                if chart.value_axes.primary.leading_break
                else None
            ),
            "scale_label": scale_label,
        },
        "semantic_table": table,
        "theme": chart_js_tokens(),
        "gridlines": False,  # D63
    }


def freeze_bar_chart(
    chart: BarChartVisual,
    formats: Mapping[str, NumberFormat],
    *,
    box_w: int = PLOT_W + PAD_L + PAD_R,
    box_h: int = PLOT_H + PAD_T + PAD_B + 80,
) -> dict[str, Any]:
    """Frozen painter-neutral plan for grouped/horizontal/stacked bars."""
    if chart.chart_type == "stacked_bar":
        return _freeze_stacked_bar_chart(
            chart, formats, box_w=box_w, box_h=box_h
        )
    return _freeze_grouped_bar_chart(chart, formats, box_w=box_w, box_h=box_h)


def _freeze_grouped_bar_chart(
    chart: Union[GroupedBarChartVisual, HorizontalBarChartVisual],
    formats: Mapping[str, NumberFormat],
    *,
    box_w: int = PLOT_W + PAD_L + PAD_R,
    box_h: int = PLOT_H + PAD_T + PAD_B + 80,
) -> dict[str, Any]:
    """Frozen painter-neutral plan for grouped/horizontal bars (D240/D243)."""
    horizontal = chart.chart_type == "horizontal_bar"
    fmt = formats[chart.value_axes.primary.format_id]
    data = chart.chart_data
    cats = list(data.categories)
    series_plans = _resolve_series(data, family="grouped_bar")
    domain = _resolve_domain(chart, data, include_zero=True)
    ticks = list(domain["ticks"])
    show_values = _ordinary_values_show(chart)
    leading = (
        chart.value_axes.primary.leading_break.to
        if chart.value_axes.primary.leading_break
        else None
    )
    break_to = float(Decimal(leading)) if leading is not None else None

    # Groups need extra category-axis chrome clearance.
    group_pad = 28 if chart.category_groups else 0
    if horizontal:
        pad_l = max(PAD_L, 120)  # category labels on left
        pad_r = max(PAD_R, 96)  # exterior value labels
        pad_t = PAD_T
        pad_b = PAD_B + group_pad
    else:
        pad_l = PAD_L
        pad_r = max(PAD_R // 2, 48)
        pad_t = max(PAD_T, 40)  # outside value headroom
        pad_b = PAD_B + group_pad

    # D47 absolute plot floor; only surplus above may feed support.
    plot_w = max(PLOT_FLOOR_W, min(PLOT_W, box_w - pad_l - pad_r))
    plot_h = max(PLOT_FLOOR_H, min(PLOT_H, box_h - pad_t - pad_b - 40))
    n_cat = len(cats)
    n_ser = len(series_plans)
    geom = _bar_slot_geometry(
        plot_w=plot_w,
        plot_h=plot_h,
        n_cat=n_cat,
        n_ser=n_ser,
        horizontal=horizontal,
        pad_l=pad_l,
        pad_t=pad_t,
    )

    v_min = float(domain["min"])
    v_max = float(domain["max"])
    # Visible domain starts at break target when leading break omits baseline.
    vis_min = break_to if break_to is not None else v_min
    vis_max = v_max
    span = (vis_max - vis_min) or 1.0

    def value_to_y(v: float) -> float:
        return pad_t + plot_h - ((v - vis_min) / span) * plot_h

    def value_to_x(v: float) -> float:
        return pad_l + ((v - vis_min) / span) * plot_w

    zero_v = 0.0 if break_to is None else break_to
    zero_y = value_to_y(zero_v)
    zero_x = value_to_x(zero_v)

    bars: list[dict[str, Any]] = []
    points: list[dict[str, Any]] = []
    for c_i, cat in enumerate(cats):
        slot = geom["slots"][c_i]
        for s_i, sp in enumerate(series_plans):
            raw = data.series[s_i].values[c_i]
            bar_origin = slot["origins"][s_i]
            thick = geom["thickness"]
            if raw is None:
                point = {
                    "series_id": sp["series_id"],
                    "category_id": cat.category_id,
                    "x": zero_x if horizontal else bar_origin + thick / 2,
                    "y": (bar_origin + thick / 2) if horizontal else zero_y,
                    "value": None,
                    "visible": MISSING_VISIBLE,
                    "accessible": MISSING_ACCESSIBLE,
                    "finite": False,
                }
                points.append(point)
                bars.append(
                    {
                        **point,
                        "missing": True,
                        "x": bar_origin if not horizontal else zero_x,
                        "y": zero_y if not horizontal else bar_origin,
                        "width": 0.0,
                        "height": 0.0,
                        "thickness": thick,
                        "sign": 0,
                    }
                )
                continue
            num = float(Decimal(raw))
            fv = format_semantic_value(
                NumberValue(
                    value=raw, format_id=chart.value_axes.primary.format_id
                ),
                formats,
            )
            if horizontal:
                x0 = zero_x
                x1 = value_to_x(num)
                left, right = (x0, x1) if x1 >= x0 else (x1, x0)
                width = abs(x1 - x0)
                # Zero-height real mark still owns a 2px stub for visibility.
                if width < 0.5 and num == 0.0 and break_to is None:
                    width = 2.0
                    left = zero_x
                y = bar_origin
                bar = {
                    "series_id": sp["series_id"],
                    "category_id": cat.category_id,
                    "x": left,
                    "y": y,
                    "width": width,
                    "height": thick,
                    "thickness": thick,
                    "value": raw,
                    "numeric": num,
                    "visible": fv.visible,
                    "accessible": fv.accessible,
                    "finite": True,
                    "missing": False,
                    "sign": 0 if num == 0 else (1 if num > 0 else -1),
                    "end_x": x1,
                    "end_y": y + thick / 2,
                }
                point = {
                    "series_id": sp["series_id"],
                    "category_id": cat.category_id,
                    "x": x1,
                    "y": y + thick / 2,
                    "value": raw,
                    "numeric": num,
                    "visible": fv.visible,
                    "accessible": fv.accessible,
                    "finite": True,
                }
            else:
                y0 = zero_y
                y1 = value_to_y(num)
                top, bot = (y1, y0) if y1 <= y0 else (y0, y1)
                height = abs(y1 - y0)
                if height < 0.5 and num == 0.0:
                    height = 2.0
                    top = zero_y - 1.0
                x = bar_origin
                bar = {
                    "series_id": sp["series_id"],
                    "category_id": cat.category_id,
                    "x": x,
                    "y": top,
                    "width": thick,
                    "height": height,
                    "thickness": thick,
                    "value": raw,
                    "numeric": num,
                    "visible": fv.visible,
                    "accessible": fv.accessible,
                    "finite": True,
                    "missing": False,
                    "sign": 0 if num == 0 else (1 if num > 0 else -1),
                    "end_x": x + thick / 2,
                    "end_y": y1,
                }
                point = {
                    "series_id": sp["series_id"],
                    "category_id": cat.category_id,
                    "x": x + thick / 2,
                    "y": y1,
                    "value": raw,
                    "numeric": num,
                    "visible": fv.visible,
                    "accessible": fv.accessible,
                    "finite": True,
                }
            bars.append(bar)
            points.append(point)

    role_sizes = _role_sizes(chart)
    # Multi-series always legend; single-series may use pane_title (D240/D243).
    identity = _bar_identity_strategy(chart, series_plans)
    placements = _place_bar_labels(
        bars,
        series_plans,
        show_values=show_values,
        label_px=role_sizes["ordinary_values"],
        plot=(pad_l, pad_t, pad_l + plot_w, pad_t + plot_h),
        horizontal=horizontal,
    )

    # Boxed labels (D235/D146) — structural, never suppressed.
    boxed_plan = _freeze_boxed_labels(
        chart, formats, bars, cats, role_sizes, horizontal=horizontal
    )
    placements.extend(boxed_plan["placements"])

    groups_plan = _freeze_category_groups(
        chart, cats, geom, pad_l, pad_t, plot_w, plot_h, horizontal=horizontal
    )

    tick_labels = [
        format_semantic_value(
            NumberValue(value=t, format_id=chart.value_axes.primary.format_id),
            formats,
        ).visible
        for t in ticks
    ]
    # Category centers for axis ticks.
    cat_centers = []
    for c_i, cat in enumerate(cats):
        slot = geom["slots"][c_i]
        if horizontal:
            cat_centers.append(
                {
                    "category_id": cat.category_id,
                    "label": cat.label,
                    "short_label": cat.short_label,
                    "x": pad_l - 10,
                    "y": slot["center"],
                }
            )
        else:
            cat_centers.append(
                {
                    "category_id": cat.category_id,
                    "label": cat.label,
                    "short_label": cat.short_label,
                    "x": slot["center"],
                    "y": pad_t + plot_h + 22,
                }
            )

    table = _semantic_table(
        chart,
        formats,
        series_plans,
        domain,
        identity=identity,
        scale_label=fmt.scale_label,
        chart_type=chart.chart_type,
        groups=groups_plan,
        boxed=boxed_plan.get("facts") or [],
    )

    return {
        "surface_id": chart.surface_id,
        "chart_type": chart.chart_type,
        "heading": chart.heading,
        "subtitle": chart.subtitle,
        "categories": cat_centers,
        "series": series_plans,
        "points": points,
        "bars": bars,
        "placements": placements,
        "show_ordinary_values": show_values,
        "show_segment_labels": False,
        "show_stack_totals": False,
        "identity_strategy": identity,
        "role_sizes": role_sizes,
        "geometry": {
            "pad_l": pad_l,
            "pad_r": pad_r,
            "pad_t": pad_t,
            "pad_b": pad_b,
            "plot_w": plot_w,
            "plot_h": plot_h,
            "marker_r": 0,
            "view_w": pad_l + plot_w + pad_r,
            "view_h": pad_t + plot_h + pad_b,
            "thickness": geom["thickness"],
            "category_pitch": geom["category_pitch"],
            "series_gap": geom["series_gap"],
            "horizontal": horizontal,
            "stacked": False,
            "zero_x": zero_x,
            "zero_y": zero_y,
        },
        "domain": domain,
        "tick_labels": tick_labels,
        "category_axis": {
            "visible": chart.category_axis.visible,
            "title": chart.category_axis.title,
        },
        "value_axis": {
            "visible": chart.value_axes.primary.visible,
            "title": chart.value_axes.primary.title,
            "format_id": chart.value_axes.primary.format_id,
            "leading_break": leading,
            "scale_label": fmt.scale_label,
        },
        "category_groups": groups_plan,
        "boxed_labels": boxed_plan.get("labels") or [],
        "stack_totals": [],
        "coverage_callout": None,
        "semantic_table": table,
        "theme": chart_js_tokens(),
        "gridlines": False,
    }


def _freeze_stacked_bar_chart(
    chart: StackedBarChartVisual,
    formats: Mapping[str, NumberFormat],
    *,
    box_w: int = PLOT_W + PAD_L + PAD_R,
    box_h: int = PLOT_H + PAD_T + PAD_B + 80,
) -> dict[str, Any]:
    """Sign-separated vertical stacks (D242/D304)."""
    fmt = formats[chart.value_axes.primary.format_id]
    fmt_id = chart.value_axes.primary.format_id
    data = chart.chart_data
    cats = list(data.categories)
    series_plans = _resolve_series(data, family="stacked_bar")
    domain = _resolve_domain(
        chart, data, include_zero=True, stack_extents=True
    )
    ticks = list(domain["ticks"])
    show_segments = _stack_segments_show(chart)
    show_totals = _stack_totals_show(chart)

    group_pad = 28 if chart.category_groups else 0
    cov = chart.coverage_callout
    cov_pad = 36 if cov is not None else 0
    pad_l = PAD_L
    pad_r = max(PAD_R // 2, 48)
    pad_t = max(PAD_T, 48) + cov_pad  # totals + coverage headroom
    pad_b = PAD_B + group_pad + 16  # negative totals footroom

    plot_w = max(200, min(PLOT_W, box_w - pad_l - pad_r))
    plot_h = max(160, min(PLOT_H, box_h - pad_t - pad_b - 40))
    n_cat = len(cats)
    # One bar cluster per category (series stack inside).
    geom = _bar_slot_geometry(
        plot_w=plot_w,
        plot_h=plot_h,
        n_cat=n_cat,
        n_ser=1,
        horizontal=False,
        pad_l=pad_l,
        pad_t=pad_t,
    )

    v_min = float(domain["min"])
    v_max = float(domain["max"])
    span = (v_max - v_min) or 1.0

    def value_to_y(v: float) -> float:
        return pad_t + plot_h - ((v - v_min) / span) * plot_h

    zero_y = value_to_y(0.0)
    zero_x = pad_l  # unused for vertical stacks

    bars: list[dict[str, Any]] = []
    points: list[dict[str, Any]] = []
    stack_totals: list[dict[str, Any]] = []

    for c_i, cat in enumerate(cats):
        slot = geom["slots"][c_i]
        thick = geom["thickness"]
        x = slot["origins"][0]
        cx = x + thick / 2
        pos_cursor = 0.0
        neg_cursor = 0.0
        pos_missing = False
        neg_missing = False
        pos_sum = Decimal(0)
        neg_sum = Decimal(0)
        # Author order = bottom-to-top within each sign (D242/D304).
        for s_i, sp in enumerate(series_plans):
            raw = data.series[s_i].values[c_i]
            if raw is None:
                # Null preserves slot; no area; invalidates that sign's total.
                points.append(
                    {
                        "series_id": sp["series_id"],
                        "category_id": cat.category_id,
                        "x": cx,
                        "y": zero_y,
                        "value": None,
                        "visible": MISSING_VISIBLE,
                        "accessible": MISSING_ACCESSIBLE,
                        "finite": False,
                    }
                )
                bars.append(
                    {
                        "series_id": sp["series_id"],
                        "category_id": cat.category_id,
                        "x": x,
                        "y": zero_y,
                        "width": thick,
                        "height": 0.0,
                        "thickness": thick,
                        "value": None,
                        "visible": MISSING_VISIBLE,
                        "accessible": MISSING_ACCESSIBLE,
                        "finite": False,
                        "missing": True,
                        "sign": 0,
                        "stack_base": 0.0,
                        "stack_top": 0.0,
                        "end_x": cx,
                        "end_y": zero_y,
                    }
                )
                # D92: any missing contributor withholds computed stack totals.
                # Null has no sign, so both sign-side totals are incomplete (D242/D304).
                pos_missing = True
                neg_missing = True
                continue
            num_d = Decimal(raw)
            num = float(num_d)
            fv = format_semantic_value(
                NumberValue(value=raw, format_id=fmt_id), formats
            )
            if num > 0:
                base = pos_cursor
                top = pos_cursor + num
                pos_cursor = top
                pos_sum += num_d
                y0 = value_to_y(base)
                y1 = value_to_y(top)
                top_y = min(y0, y1)
                height = abs(y1 - y0)
                sign = 1
                end_y = y1
            elif num < 0:
                base = neg_cursor
                top = neg_cursor + num  # more negative
                neg_cursor = top
                neg_sum += num_d
                y0 = value_to_y(base)
                y1 = value_to_y(top)
                top_y = min(y0, y1)
                height = abs(y1 - y0)
                sign = -1
                end_y = y1
            else:
                # Zero is data without area — zero-height anchor only (D304).
                base = 0.0
                top = 0.0
                height = 0.0
                top_y = zero_y
                sign = 0
                end_y = zero_y
            bar = {
                "series_id": sp["series_id"],
                "category_id": cat.category_id,
                "x": x,
                "y": top_y,
                "width": thick,
                "height": height,
                "thickness": thick,
                "value": raw,
                "numeric": num,
                "visible": fv.visible,
                "accessible": fv.accessible,
                "finite": True,
                "missing": False,
                "sign": sign,
                "stack_base": base,
                "stack_top": top,
                "end_x": cx,
                "end_y": end_y,
                "mid_y": top_y + height / 2 if height else zero_y,
            }
            bars.append(bar)
            points.append(
                {
                    "series_id": sp["series_id"],
                    "category_id": cat.category_id,
                    "x": cx,
                    "y": end_y,
                    "value": raw,
                    "numeric": num,
                    "visible": fv.visible,
                    "accessible": fv.accessible,
                    "finite": True,
                }
            )

        pos_ext = float(pos_sum)
        neg_ext = float(neg_sum)
        aux = chart.auxiliary_series or []
        authored = aux[0].values[c_i] if aux else None

        def _total_entry(
            *,
            side: str,
            raw_val: Optional[str],
            numeric: float,
            source: str,
            withheld: bool,
            fmt_for: str,
        ) -> dict[str, Any]:
            if withheld or raw_val is None:
                return {
                    "category_id": cat.category_id,
                    "side": side,
                    "value": None,
                    "numeric": None,
                    "visible": MISSING_VISIBLE,
                    "accessible": MISSING_ACCESSIBLE,
                    "missing": True,
                    "withheld": withheld,
                    "source": source,
                    "x": cx,
                    "y": value_to_y(numeric) if side != "authored" else zero_y,
                    "format_id": fmt_for,
                }
            fv_t = format_semantic_value(
                NumberValue(value=raw_val, format_id=fmt_for), formats
            )
            # D241: authored totals anchor on completed stack outer signed edge
            # (never authored value on scale). Empty extents → zero edge.
            if side == "authored":
                if numeric < 0:
                    anchor_v = neg_ext if neg_ext < 0 else 0.0
                    y = value_to_y(anchor_v) + 14
                else:
                    anchor_v = pos_ext if pos_ext > 0 else 0.0
                    y = value_to_y(anchor_v) - 8
            elif side == "negative":
                anchor_v = neg_ext if neg_ext < 0 else numeric
                y = value_to_y(anchor_v) + 14
            else:
                anchor_v = pos_ext if pos_ext > 0 else numeric
                y = value_to_y(anchor_v) - 8
            return {
                "category_id": cat.category_id,
                "side": side,
                "value": raw_val,
                "numeric": numeric,
                "visible": fv_t.visible,
                "accessible": fv_t.accessible,
                "missing": False,
                "withheld": False,
                "source": source,
                "x": cx,
                "y": y,
                "format_id": fmt_for,
            }

        # Always record both computed sign-side totals for D247 (D304), including
        # plain 0 when a side has no non-zero contributors. Withhold only when any
        # contributor is missing (D92). Authored is a separate fact (D241).
        if pos_missing:
            stack_totals.append(
                _total_entry(
                    side="positive",
                    raw_val=None,
                    numeric=pos_ext,
                    source="computed",
                    withheld=True,
                    fmt_for=fmt_id,
                )
            )
        else:
            stack_totals.append(
                _total_entry(
                    side="positive",
                    raw_val=_plain_decimal(pos_sum),
                    numeric=pos_ext,
                    source="computed",
                    withheld=False,
                    fmt_for=fmt_id,
                )
            )
        if neg_missing:
            stack_totals.append(
                _total_entry(
                    side="negative",
                    raw_val=None,
                    numeric=neg_ext,
                    source="computed",
                    withheld=True,
                    fmt_for=fmt_id,
                )
            )
        else:
            stack_totals.append(
                _total_entry(
                    side="negative",
                    raw_val=_plain_decimal(neg_sum),
                    numeric=neg_ext,
                    source="computed",
                    withheld=False,
                    fmt_for=fmt_id,
                )
            )
        if aux:
            if authored is None:
                stack_totals.append(
                    _total_entry(
                        side="authored",
                        raw_val=None,
                        numeric=0.0,
                        source="authored",
                        withheld=False,
                        fmt_for=aux[0].format_id,
                    )
                )
            else:
                stack_totals.append(
                    _total_entry(
                        side="authored",
                        raw_val=authored,
                        numeric=float(Decimal(authored)),
                        source="authored",
                        withheld=False,
                        fmt_for=aux[0].format_id,
                    )
                )

    role_sizes = _role_sizes(chart)
    identity = "legend"

    placements = _place_stack_labels(
        bars,
        series_plans,
        stack_totals,
        show_segments=show_segments,
        show_totals=show_totals,
        segment_px=role_sizes["segment_labels"],
        total_px=role_sizes["stack_totals"],
        plot=(pad_l, pad_t, pad_l + plot_w, pad_t + plot_h),
    )

    groups_plan = _freeze_category_groups(
        chart, cats, geom, pad_l, pad_t, plot_w, plot_h, horizontal=False
    )

    coverage_plan = _freeze_coverage_callout(chart, formats, pad_l, pad_t, plot_w)

    tick_labels = [
        format_semantic_value(
            NumberValue(value=t, format_id=fmt_id), formats
        ).visible
        for t in ticks
    ]
    cat_centers = []
    for c_i, cat in enumerate(cats):
        slot = geom["slots"][c_i]
        cat_centers.append(
            {
                "category_id": cat.category_id,
                "label": cat.label,
                "short_label": cat.short_label,
                "x": slot["center"],
                "y": pad_t + plot_h + 22,
            }
        )

    extra_facts: list[str] = []
    for t in stack_totals:
        if t.get("source") == "authored":
            if t.get("missing"):
                extra_facts.append(
                    f"Authored stack total {t['category_id']}: {MISSING_ACCESSIBLE}"
                )
            else:
                extra_facts.append(
                    f"Authored stack total {t['category_id']}: {t['accessible']}"
                )
        elif t.get("withheld"):
            extra_facts.append(
                f"Computed {t['side']} total {t['category_id']}: withheld "
                f"(missing contributor)"
            )
        elif not t.get("missing"):
            extra_facts.append(
                f"Computed {t['side']} total {t['category_id']}: {t['accessible']}"
            )
    if coverage_plan is not None:
        extra_facts.append(coverage_plan["fact"])

    table = _semantic_table(
        chart,
        formats,
        series_plans,
        domain,
        identity=identity,
        scale_label=fmt.scale_label,
        chart_type="stacked_bar",
        groups=groups_plan,
        boxed=extra_facts,
        stack_totals=stack_totals,
    )

    return {
        "surface_id": chart.surface_id,
        "chart_type": "stacked_bar",
        "heading": chart.heading,
        "subtitle": chart.subtitle,
        "categories": cat_centers,
        "series": series_plans,
        "points": points,
        "bars": bars,
        "placements": placements,
        "show_ordinary_values": False,
        "show_segment_labels": show_segments,
        "show_stack_totals": show_totals,
        "identity_strategy": identity,
        "role_sizes": role_sizes,
        "geometry": {
            "pad_l": pad_l,
            "pad_r": pad_r,
            "pad_t": pad_t,
            "pad_b": pad_b,
            "plot_w": plot_w,
            "plot_h": plot_h,
            "marker_r": 0,
            "view_w": pad_l + plot_w + pad_r,
            "view_h": pad_t + plot_h + pad_b,
            "thickness": geom["thickness"],
            "category_pitch": geom["category_pitch"],
            "series_gap": 0.0,
            "horizontal": False,
            "stacked": True,
            "zero_x": zero_x,
            "zero_y": zero_y,
        },
        "domain": domain,
        "tick_labels": tick_labels,
        "category_axis": {
            "visible": chart.category_axis.visible,
            "title": chart.category_axis.title,
        },
        "value_axis": {
            "visible": chart.value_axes.primary.visible,
            "title": chart.value_axes.primary.title,
            "format_id": fmt_id,
            "leading_break": None,
            "scale_label": fmt.scale_label,
        },
        "category_groups": groups_plan,
        "boxed_labels": [],
        "stack_totals": stack_totals,
        "coverage_callout": coverage_plan,
        "semantic_table": table,
        "theme": chart_js_tokens(),
        "gridlines": False,
    }


def freeze_waterfall_chart(
    chart: WaterfallChartVisual,
    formats: Mapping[str, NumberFormat],
    *,
    box_w: int = PLOT_W + PAD_L + PAD_R,
    box_h: int = PLOT_H + PAD_T + PAD_B + 80,
) -> dict[str, Any]:
    """Frozen painter-neutral plan for explicit arithmetic waterfalls (D245/D307)."""
    fmt = formats[chart.value_axes.primary.format_id]
    steps = list(chart.waterfall_data.steps)
    resolved = _resolve_waterfall_steps(steps, formats, fmt_id=chart.value_axes.primary.format_id)
    domain = _resolve_waterfall_domain(chart, resolved)
    ticks = list(domain["ticks"])

    pad_l = PAD_L
    pad_r = max(PAD_R // 2, 48)
    pad_t = max(PAD_T, 40)
    pad_b = PAD_B
    plot_w = max(200, min(PLOT_W, box_w - pad_l - pad_r))
    plot_h = max(160, min(PLOT_H, box_h - pad_t - pad_b - 40))
    n = len(resolved)
    geom = _bar_slot_geometry(
        plot_w=plot_w,
        plot_h=plot_h,
        n_cat=n,
        n_ser=1,
        horizontal=False,
        pad_l=pad_l,
        pad_t=pad_t,
    )

    v_min = float(domain["min"])
    v_max = float(domain["max"])
    span = (v_max - v_min) or 1.0

    def value_to_y(v: float) -> float:
        return pad_t + plot_h - ((v - v_min) / span) * plot_h

    zero_y = value_to_y(0.0)
    bars: list[dict[str, Any]] = []
    connectors: list[dict[str, Any]] = []
    placements: list[dict[str, Any]] = []
    role_sizes = _waterfall_role_sizes(chart)
    lab_px = role_sizes["structural_values"]
    thick = geom["thickness"]

    prev_end_level: Optional[float] = None
    for i, step in enumerate(resolved):
        slot = geom["slots"][i]
        x = slot["origins"][0]
        cx = slot["center"]
        y0 = float(step["y0"])
        y1 = float(step["y1"])
        top = value_to_y(max(y0, y1))
        bot = value_to_y(min(y0, y1))
        height = max(2.0, abs(bot - top))
        color_key = step["color_role"]
        color = resolve_color(_WATERFALL_ROLE_COLOR[color_key], role="fill")
        bar = {
            "series_id": WATERFALL_SERIES_ID,
            "category_id": step["category_id"],
            "role": step["role"],
            "color_role": color_key,
            "color": color,
            "x": x,
            "y": top,
            "width": thick,
            "height": height,
            "thickness": thick,
            "value": step["display_value"],
            "numeric": float(step["display_numeric"]),
            "level": float(step["level"]),
            "y0": y0,
            "y1": y1,
            "visible": step["visible"],
            "accessible": step["accessible"],
            "finite": True,
            "missing": False,
            "sign": step["sign"],
            "end_x": cx,
            "end_y": top,
            "resets_level": step["role"] == "total",
        }
        bars.append(bar)
        # Connector from previous step end level to this bar start (continuity only).
        if prev_end_level is not None and step["role"] == "change":
            cy = value_to_y(prev_end_level)
            prev_cx = geom["slots"][i - 1]["center"]
            connectors.append(
                {
                    "from_category_id": resolved[i - 1]["category_id"],
                    "to_category_id": step["category_id"],
                    "y": cy,
                    "x1": prev_cx + thick / 2,
                    "x2": x,
                }
            )
        # Structural label above bar (mandatory; never suppressed).
        placements.append(
            {
                "kind": "structural",
                "class": "above",
                "series_id": WATERFALL_SERIES_ID,
                "category_id": step["category_id"],
                "text": step["visible"],
                "x": cx,
                "y": top - 8,
                "priority": "structural",
            }
        )
        prev_end_level = float(step["level"])

    cat_centers = []
    for i, step in enumerate(resolved):
        slot = geom["slots"][i]
        cat_centers.append(
            {
                "category_id": step["category_id"],
                "label": step["label"],
                "short_label": step["short_label"],
                "x": slot["center"],
                "y": pad_t + plot_h + 22,
                "role": step["role"],
            }
        )

    tick_labels = [
        format_semantic_value(
            NumberValue(value=t, format_id=chart.value_axes.primary.format_id),
            formats,
        ).visible
        for t in ticks
    ]
    table = _waterfall_semantic_table(chart, resolved, domain, formats, fmt)
    series_plans = [
        {
            "series_id": WATERFALL_SERIES_ID,
            "name": "Waterfall",
            "color": resolve_color("navy", role="series_identity"),
            "line_style": "solid",
            "marker": "circle",
            "values": [s["display_value"] for s in resolved],
        }
    ]

    return {
        "surface_id": chart.surface_id,
        "chart_type": "waterfall",
        "heading": chart.heading,
        "subtitle": chart.subtitle,
        "categories": cat_centers,
        "series": series_plans,
        "steps": resolved,
        "points": [],
        "bars": bars,
        "connectors": connectors,
        "placements": placements,
        "show_ordinary_values": False,
        "identity_strategy": "roles",
        "role_sizes": role_sizes,
        "geometry": {
            "pad_l": pad_l,
            "pad_r": pad_r,
            "pad_t": pad_t,
            "pad_b": pad_b,
            "plot_w": plot_w,
            "plot_h": plot_h,
            "marker_r": 0,
            "view_w": pad_l + plot_w + pad_r,
            "view_h": pad_t + plot_h + pad_b,
            "thickness": thick,
            "category_pitch": geom["category_pitch"],
            "series_gap": geom["series_gap"],
            "horizontal": False,
            "zero_x": pad_l,
            "zero_y": zero_y,
        },
        "domain": domain,
        "tick_labels": tick_labels,
        "category_axis": {
            "visible": chart.category_axis.visible,
            "title": chart.category_axis.title,
        },
        "value_axis": {
            "visible": chart.value_axes.primary.visible,
            "title": chart.value_axes.primary.title,
            "format_id": chart.value_axes.primary.format_id,
            "leading_break": None,
            "scale_label": fmt.scale_label,
        },
        "category_groups": [],
        "boxed_labels": [],
        "semantic_table": table,
        "theme": chart_js_tokens(),
        "gridlines": False,
        "structural_label_px": lab_px,
    }


def freeze_combo_chart(
    chart: ComboChartVisual,
    formats: Mapping[str, NumberFormat],
    *,
    box_w: int = PLOT_W + PAD_L + PAD_R,
    box_h: int = PLOT_H + PAD_T + PAD_B + 80,
) -> dict[str, Any]:
    """Grouped/stacked bars behind line layers on one category model (D136/D244)."""
    stacked = chart.bar_mode == "stacked"
    primary = chart.value_axes.primary
    secondary = chart.value_axes.secondary
    p_fmt = formats[primary.format_id]
    p_fmt_id = primary.format_id
    data = chart.chart_data
    cats = list(data.categories)
    bar_series = [s for s in data.series if s.mark_type == "bar"]
    line_series = [s for s in data.series if s.mark_type == "line"]
    line_axis_key = (
        "secondary"
        if any(s.axis_key == "secondary" for s in line_series)
        else "primary"
    )

    # Resolve colors in authored series order across the whole combo (D99/D132).
    defaults = resolve_series_colors("combo", count=len(data.series))
    series_plans: list[dict[str, Any]] = []
    bar_plans: list[dict[str, Any]] = []
    line_plans: list[dict[str, Any]] = []
    for i, s in enumerate(data.series):
        color = (
            resolve_color(s.color, role="series_identity")
            if s.color is not None
            else defaults[i]
        )
        if s.mark_type == "line":
            if s.style is not None:
                line_style, marker = s.style.line_style, s.style.marker
            else:
                # Line-layer style index among line series only.
                li = sum(1 for p in series_plans if p["mark_type"] == "line")
                line_style, marker = LINE_STYLE_PAIRS[li % len(LINE_STYLE_PAIRS)]
            axis_key = "secondary" if s.axis_key == "secondary" else "primary"
        else:
            line_style, marker = "solid", "circle"
            axis_key = "primary"
        plan_s = {
            "series_id": s.series_id,
            "name": s.name,
            "color": color,
            "line_style": line_style,
            "marker": marker,
            "values": list(s.values),
            "mark_type": s.mark_type,
            "axis_key": axis_key,
        }
        series_plans.append(plan_s)
        if s.mark_type == "bar":
            bar_plans.append(plan_s)
        else:
            line_plans.append(plan_s)

    # Domains: primary always owns bars (+ primary lines); secondary owns secondary lines.
    primary_domain = _resolve_combo_domain(
        primary,
        bar_series if stacked or line_axis_key == "secondary" else list(data.series),
        categories=cats,
        include_zero=True,
        stack_extents=stacked,
        bar_only=stacked or line_axis_key == "secondary",
        all_series=list(data.series),
        line_axis_key=line_axis_key,
        axis_key="primary",
    )
    secondary_domain = None
    if secondary is not None:
        secondary_domain = _resolve_combo_domain(
            secondary,
            line_series,
            categories=cats,
            include_zero=False,
            stack_extents=False,
            bar_only=False,
            all_series=list(data.series),
            line_axis_key=line_axis_key,
            axis_key="secondary",
        )

    show_values = _ordinary_values_show(chart)
    show_segments = _stack_segments_show(chart) if stacked else False
    show_totals = _stack_totals_show(chart) if stacked else False

    group_pad = 28 if chart.category_groups else 0
    pad_l = PAD_L
    pad_r = PAD_R if secondary is not None else max(PAD_R // 2, 48)
    if secondary is not None:
        pad_r = max(pad_r, PAD_L)  # room for secondary tick labels
    pad_t = max(PAD_T, 48 if stacked else 40)
    pad_b = PAD_B + group_pad + (16 if stacked else 0)

    plot_w = max(PLOT_FLOOR_W, min(PLOT_W, box_w - pad_l - pad_r))
    plot_h = max(PLOT_FLOOR_H, min(PLOT_H, box_h - pad_t - pad_b - 40))
    n_cat = len(cats)
    n_bar = len(bar_plans)
    geom = _bar_slot_geometry(
        plot_w=plot_w,
        plot_h=plot_h,
        n_cat=n_cat,
        n_ser=1 if stacked else n_bar,
        horizontal=False,
        pad_l=pad_l,
        pad_t=pad_t,
    )

    p_min = float(primary_domain["min"])
    p_max = float(primary_domain["max"])
    p_span = (p_max - p_min) or 1.0

    def p_y(v: float) -> float:
        return pad_t + plot_h - ((v - p_min) / p_span) * plot_h

    s_min = s_max = s_span = 0.0

    def s_y(v: float) -> float:
        return pad_t + plot_h - ((v - s_min) / s_span) * plot_h

    if secondary_domain is not None:
        s_min = float(secondary_domain["min"])
        s_max = float(secondary_domain["max"])
        s_span = (s_max - s_min) or 1.0

    zero_y = p_y(0.0)
    bars: list[dict[str, Any]] = []
    points: list[dict[str, Any]] = []
    stack_totals: list[dict[str, Any]] = []

    # --- bar layer (always primary) ---
    for c_i, cat in enumerate(cats):
        slot = geom["slots"][c_i]
        thick = geom["thickness"]
        if stacked:
            x = slot["origins"][0]
            cx = x + thick / 2
            pos_cursor = 0.0
            neg_cursor = 0.0
            pos_missing = False
            neg_missing = False
            pos_sum = Decimal(0)
            neg_sum = Decimal(0)
            for s_i, sp in enumerate(bar_plans):
                raw = bar_series[s_i].values[c_i]
                if raw is None:
                    points.append(
                        {
                            "series_id": sp["series_id"],
                            "category_id": cat.category_id,
                            "x": cx,
                            "y": zero_y,
                            "value": None,
                            "visible": MISSING_VISIBLE,
                            "accessible": MISSING_ACCESSIBLE,
                            "finite": False,
                            "mark_type": "bar",
                            "axis_key": "primary",
                        }
                    )
                    bars.append(
                        {
                            "series_id": sp["series_id"],
                            "category_id": cat.category_id,
                            "x": x,
                            "y": zero_y,
                            "width": thick,
                            "height": 0.0,
                            "thickness": thick,
                            "value": None,
                            "visible": MISSING_VISIBLE,
                            "accessible": MISSING_ACCESSIBLE,
                            "finite": False,
                            "missing": True,
                            "sign": 0,
                            "stack_base": 0.0,
                            "stack_top": 0.0,
                            "end_x": cx,
                            "end_y": zero_y,
                            "mark_type": "bar",
                            "axis_key": "primary",
                        }
                    )
                    pos_missing = True
                    neg_missing = True
                    continue
                num_d = Decimal(raw)
                num = float(num_d)
                fv = format_semantic_value(
                    NumberValue(value=raw, format_id=p_fmt_id), formats
                )
                if num > 0:
                    base, top = pos_cursor, pos_cursor + num
                    pos_cursor = top
                    pos_sum += num_d
                    sign = 1
                elif num < 0:
                    base, top = neg_cursor, neg_cursor + num
                    neg_cursor = top
                    neg_sum += num_d
                    sign = -1
                else:
                    base = top = 0.0
                    sign = 0
                y0, y1 = p_y(base), p_y(top)
                top_y = min(y0, y1) if sign != 0 else zero_y
                height = abs(y1 - y0) if sign != 0 else 0.0
                end_y = y1 if sign != 0 else zero_y
                bars.append(
                    {
                        "series_id": sp["series_id"],
                        "category_id": cat.category_id,
                        "x": x,
                        "y": top_y,
                        "width": thick,
                        "height": height,
                        "thickness": thick,
                        "value": raw,
                        "numeric": num,
                        "visible": fv.visible,
                        "accessible": fv.accessible,
                        "finite": True,
                        "missing": False,
                        "sign": sign,
                        "stack_base": base,
                        "stack_top": top,
                        "end_x": cx,
                        "end_y": end_y,
                        "mid_y": top_y + height / 2 if height else zero_y,
                        "mark_type": "bar",
                        "axis_key": "primary",
                    }
                )
                points.append(
                    {
                        "series_id": sp["series_id"],
                        "category_id": cat.category_id,
                        "x": cx,
                        "y": end_y,
                        "value": raw,
                        "numeric": num,
                        "visible": fv.visible,
                        "accessible": fv.accessible,
                        "finite": True,
                        "mark_type": "bar",
                        "axis_key": "primary",
                    }
                )
            pos_ext, neg_ext = float(pos_sum), float(neg_sum)
            aux = chart.auxiliary_series or []
            authored = (
                aux[0].values[c_i]
                if aux and getattr(aux[0], "role", None) == "authored_stack_total"
                else None
            )

            def _total_entry(
                *,
                side: str,
                raw_val: Optional[str],
                numeric: float,
                source: str,
                withheld: bool,
                fmt_for: str,
            ) -> dict[str, Any]:
                if withheld or raw_val is None:
                    return {
                        "category_id": cat.category_id,
                        "side": side,
                        "value": None,
                        "numeric": None,
                        "visible": MISSING_VISIBLE,
                        "accessible": MISSING_ACCESSIBLE,
                        "missing": True,
                        "withheld": withheld,
                        "source": source,
                        "x": cx,
                        "y": p_y(numeric) if side != "authored" else zero_y,
                        "format_id": fmt_for,
                    }
                fv_t = format_semantic_value(
                    NumberValue(value=raw_val, format_id=fmt_for), formats
                )
                if side == "authored":
                    if numeric < 0:
                        anchor_v = neg_ext if neg_ext < 0 else 0.0
                        y = p_y(anchor_v) + 14
                    else:
                        anchor_v = pos_ext if pos_ext > 0 else 0.0
                        y = p_y(anchor_v) - 8
                elif side == "negative":
                    anchor_v = neg_ext if neg_ext < 0 else numeric
                    y = p_y(anchor_v) + 14
                else:
                    anchor_v = pos_ext if pos_ext > 0 else numeric
                    y = p_y(anchor_v) - 8
                return {
                    "category_id": cat.category_id,
                    "side": side,
                    "value": raw_val,
                    "numeric": numeric,
                    "visible": fv_t.visible,
                    "accessible": fv_t.accessible,
                    "missing": False,
                    "withheld": False,
                    "source": source,
                    "x": cx,
                    "y": y,
                    "format_id": fmt_for,
                }

            if pos_missing:
                stack_totals.append(
                    _total_entry(
                        side="positive",
                        raw_val=None,
                        numeric=pos_ext,
                        source="computed",
                        withheld=True,
                        fmt_for=p_fmt_id,
                    )
                )
            else:
                stack_totals.append(
                    _total_entry(
                        side="positive",
                        raw_val=_plain_decimal(pos_sum),
                        numeric=pos_ext,
                        source="computed",
                        withheld=False,
                        fmt_for=p_fmt_id,
                    )
                )
            if neg_missing:
                stack_totals.append(
                    _total_entry(
                        side="negative",
                        raw_val=None,
                        numeric=neg_ext,
                        source="computed",
                        withheld=True,
                        fmt_for=p_fmt_id,
                    )
                )
            else:
                stack_totals.append(
                    _total_entry(
                        side="negative",
                        raw_val=_plain_decimal(neg_sum),
                        numeric=neg_ext,
                        source="computed",
                        withheld=False,
                        fmt_for=p_fmt_id,
                    )
                )
            if aux and getattr(aux[0], "role", None) == "authored_stack_total":
                if authored is None:
                    stack_totals.append(
                        _total_entry(
                            side="authored",
                            raw_val=None,
                            numeric=0.0,
                            source="authored",
                            withheld=False,
                            fmt_for=aux[0].format_id,
                        )
                    )
                else:
                    stack_totals.append(
                        _total_entry(
                            side="authored",
                            raw_val=authored,
                            numeric=float(Decimal(authored)),
                            source="authored",
                            withheld=False,
                            fmt_for=aux[0].format_id,
                        )
                    )
        else:
            # grouped bars
            for s_i, sp in enumerate(bar_plans):
                raw = bar_series[s_i].values[c_i]
                bar_origin = slot["origins"][s_i]
                if raw is None:
                    point = {
                        "series_id": sp["series_id"],
                        "category_id": cat.category_id,
                        "x": bar_origin + thick / 2,
                        "y": zero_y,
                        "value": None,
                        "visible": MISSING_VISIBLE,
                        "accessible": MISSING_ACCESSIBLE,
                        "finite": False,
                        "mark_type": "bar",
                        "axis_key": "primary",
                    }
                    points.append(point)
                    bars.append(
                        {
                            **point,
                            "missing": True,
                            "x": bar_origin,
                            "y": zero_y,
                            "width": 0.0,
                            "height": 0.0,
                            "thickness": thick,
                            "sign": 0,
                        }
                    )
                    continue
                num = float(Decimal(raw))
                fv = format_semantic_value(
                    NumberValue(value=raw, format_id=p_fmt_id), formats
                )
                y1 = p_y(num)
                top, bot = (y1, zero_y) if y1 <= zero_y else (zero_y, y1)
                height = abs(y1 - zero_y)
                if height < 0.5 and num == 0.0:
                    height = 2.0
                    top = zero_y - 1.0
                bars.append(
                    {
                        "series_id": sp["series_id"],
                        "category_id": cat.category_id,
                        "x": bar_origin,
                        "y": top,
                        "width": thick,
                        "height": height,
                        "thickness": thick,
                        "value": raw,
                        "numeric": num,
                        "visible": fv.visible,
                        "accessible": fv.accessible,
                        "finite": True,
                        "missing": False,
                        "sign": 0 if num == 0 else (1 if num > 0 else -1),
                        "end_x": bar_origin + thick / 2,
                        "end_y": y1,
                        "mark_type": "bar",
                        "axis_key": "primary",
                    }
                )
                points.append(
                    {
                        "series_id": sp["series_id"],
                        "category_id": cat.category_id,
                        "x": bar_origin + thick / 2,
                        "y": y1,
                        "value": raw,
                        "numeric": num,
                        "visible": fv.visible,
                        "accessible": fv.accessible,
                        "finite": True,
                        "mark_type": "bar",
                        "axis_key": "primary",
                    }
                )

    # --- line layer (on category centers; bars paint behind) ---
    line_xs = [geom["slots"][c_i]["center"] for c_i in range(n_cat)]
    for s_i, sp in enumerate(line_plans):
        src = line_series[s_i]
        axis_key = sp["axis_key"]
        fmt_id = (
            secondary.format_id
            if axis_key == "secondary" and secondary is not None
            else p_fmt_id
        )
        y_of = s_y if axis_key == "secondary" else p_y
        for c_i, cat in enumerate(cats):
            raw = src.values[c_i]
            if raw is None:
                points.append(
                    {
                        "series_id": sp["series_id"],
                        "category_id": cat.category_id,
                        "x": line_xs[c_i],
                        "y": None,
                        "value": None,
                        "visible": MISSING_VISIBLE,
                        "accessible": MISSING_ACCESSIBLE,
                        "finite": False,
                        "mark_type": "line",
                        "axis_key": axis_key,
                    }
                )
                continue
            num = float(Decimal(raw))
            fv = format_semantic_value(
                NumberValue(value=raw, format_id=fmt_id), formats
            )
            points.append(
                {
                    "series_id": sp["series_id"],
                    "category_id": cat.category_id,
                    "x": line_xs[c_i],
                    "y": y_of(num),
                    "value": raw,
                    "numeric": num,
                    "visible": fv.visible,
                    "accessible": fv.accessible,
                    "finite": True,
                    "mark_type": "line",
                    "axis_key": axis_key,
                }
            )

    role_sizes = _role_sizes(chart)
    # Auto identity: line endpoint labels + bar legend when endpoints fit; else full legend (D244).
    ser_px = role_sizes["series_labels"]
    endpoints_fit = all(
        len(sp["name"]) * ser_px * 0.55 <= pad_r - 16 for sp in line_plans
    )
    if chart.display is not None and chart.display.series_identity == "legend":
        identity = "legend"
    elif endpoints_fit:
        identity = "endpoints_and_bar_legend"
    else:
        identity = "legend"

    placements: list[dict[str, Any]] = []
    if stacked:
        placements.extend(
            _place_stack_labels(
                bars,
                bar_plans,
                stack_totals,
                show_segments=show_segments,
                show_totals=show_totals,
                segment_px=role_sizes["segment_labels"],
                total_px=role_sizes["stack_totals"],
                plot=(pad_l, pad_t, pad_l + plot_w, pad_t + plot_h),
            )
        )
    else:
        # Ordinary bar values (grouped).
        placements.extend(
            _place_bar_labels(
                bars,
                bar_plans,
                show_values=show_values,
                label_px=role_sizes["ordinary_values"],
                plot=(pad_l, pad_t, pad_l + plot_w, pad_t + plot_h),
                horizontal=False,
            )
        )
    boxed_plan = {"placements": [], "labels": [], "facts": []}
    if not stacked:
        boxed_plan = _freeze_boxed_labels(
            chart, formats, bars, cats, role_sizes, horizontal=False
        )
        placements.extend(boxed_plan["placements"])
    # Line point labels + endpoint identities.
    line_points = [p for p in points if p.get("mark_type") == "line"]
    placements.extend(
        _place_point_labels(
            line_points,
            line_plans,
            show_values=show_values,
            label_px=role_sizes["ordinary_values"],
            plot=(pad_l, pad_t, pad_l + plot_w, pad_t + plot_h),
            identity=("endpoints" if identity == "endpoints_and_bar_legend" else identity),
        )
    )

    groups_plan = _freeze_category_groups(
        chart, cats, geom, pad_l, pad_t, plot_w, plot_h, horizontal=False
    )

    tick_labels = [
        format_semantic_value(
            NumberValue(value=t, format_id=p_fmt_id), formats
        ).visible
        for t in primary_domain["ticks"]
    ]
    secondary_tick_labels: list[str] = []
    if secondary_domain is not None and secondary is not None:
        secondary_tick_labels = [
            format_semantic_value(
                NumberValue(value=t, format_id=secondary.format_id), formats
            ).visible
            for t in secondary_domain["ticks"]
        ]

    cat_centers = []
    for c_i, cat in enumerate(cats):
        slot = geom["slots"][c_i]
        cat_centers.append(
            {
                "category_id": cat.category_id,
                "label": cat.label,
                "short_label": cat.short_label,
                "x": slot["center"],
                "y": pad_t + plot_h + 22,
            }
        )

    # Semantic table: all series columns; stacked adds computed totals.
    table_type = "combo_stacked" if stacked else "combo_grouped"
    extra_facts: list[str] = [f"Bar mode: {chart.bar_mode}"]
    if secondary is not None:
        s_fmt = formats[secondary.format_id]
        extra_facts.append(
            f"Secondary axis format: {s_fmt.unit or 'unitless'}, "
            f"{s_fmt.value_decimals} decimal places"
        )
        if secondary_domain is not None:
            extra_facts.append(
                f"Secondary domain from {secondary_domain['min']} to {secondary_domain['max']}"
            )
    for sp in series_plans:
        extra_facts.append(
            f"Series {sp['name']}: mark={sp['mark_type']} axis={sp['axis_key']}"
        )
    if stacked:
        for t in stack_totals:
            if t.get("source") == "authored":
                if t.get("missing"):
                    extra_facts.append(
                        f"Authored stack total {t['category_id']}: {MISSING_ACCESSIBLE}"
                    )
                else:
                    extra_facts.append(
                        f"Authored stack total {t['category_id']}: {t['accessible']}"
                    )
            elif t.get("withheld"):
                extra_facts.append(
                    f"Computed {t['side']} total {t['category_id']}: withheld "
                    f"(missing contributor)"
                )

    # Build a chart-like object for _semantic_table primary format path.
    table = _semantic_table(
        chart,
        formats,
        series_plans,
        primary_domain,
        identity=identity,
        scale_label=p_fmt.scale_label,
        chart_type=table_type if not stacked else "stacked_bar",
        groups=groups_plan,
        boxed=extra_facts,
        stack_totals=stack_totals if stacked else None,
    )
    # Force combo type wording even when reusing stacked table columns.
    if stacked:
        table["facts"] = [
            f.replace("sign-separated stacked vertical bars", "stacked combo bars with line layers")
            if isinstance(f, str)
            else f
            for f in table["facts"]
        ]
        if not any("Bar mode" in f for f in table["facts"]):
            table["facts"].insert(1, f"Bar mode: {chart.bar_mode}")

    boxed_labels = boxed_plan.get("labels") or []

    return {
        "surface_id": chart.surface_id,
        "chart_type": "combo",
        "bar_mode": chart.bar_mode,
        "heading": chart.heading,
        "subtitle": chart.subtitle,
        "categories": cat_centers,
        "series": series_plans,
        "points": points,
        "bars": bars,
        "placements": placements,
        "show_ordinary_values": show_values,
        "show_segment_labels": show_segments,
        "show_stack_totals": show_totals,
        "identity_strategy": identity,
        "role_sizes": role_sizes,
        "geometry": {
            "pad_l": pad_l,
            "pad_r": pad_r,
            "pad_t": pad_t,
            "pad_b": pad_b,
            "plot_w": plot_w,
            "plot_h": plot_h,
            "marker_r": MARKER_R,
            "view_w": pad_l + plot_w + pad_r,
            "view_h": pad_t + plot_h + pad_b,
            "thickness": geom["thickness"],
            "category_pitch": geom["category_pitch"],
            "series_gap": 0.0 if stacked else geom["series_gap"],
            "horizontal": False,
            "stacked": stacked,
            "zero_x": pad_l,
            "zero_y": zero_y,
        },
        "domain": primary_domain,
        "secondary_domain": secondary_domain,
        "tick_labels": tick_labels,
        "secondary_tick_labels": secondary_tick_labels,
        "category_axis": {
            "visible": chart.category_axis.visible,
            "title": chart.category_axis.title,
        },
        "value_axis": {
            "visible": primary.visible,
            "title": primary.title,
            "format_id": p_fmt_id,
            "leading_break": None,
            "scale_label": p_fmt.scale_label,
        },
        "secondary_value_axis": (
            {
                "visible": secondary.visible,
                "title": secondary.title,
                "format_id": secondary.format_id,
                "leading_break": None,
                "scale_label": formats[secondary.format_id].scale_label,
            }
            if secondary is not None
            else None
        ),
        "category_groups": groups_plan,
        "boxed_labels": boxed_labels,
        "stack_totals": stack_totals,
        "coverage_callout": None,
        "semantic_table": table,
        "theme": chart_js_tokens(),
        "gridlines": False,
    }


def _resolve_combo_domain(
    axis: Any,
    series_for_domain: list[Any],
    *,
    categories: list[Any],
    include_zero: bool,
    stack_extents: bool,
    bar_only: bool,
    all_series: list[Any],
    line_axis_key: str,
    axis_key: str,
) -> dict[str, Any]:
    """Domain for one combo value axis from the series that plot on it."""
    finite: list[Decimal] = []
    if axis_key == "primary":
        # Bars always primary; primary lines when lines share primary.
        bar_s = [s for s in all_series if getattr(s, "mark_type", None) == "bar"]
        line_s = [
            s
            for s in all_series
            if getattr(s, "mark_type", None) == "line"
            and line_axis_key == "primary"
        ]
        use = bar_s + line_s
        if stack_extents:
            n = len(categories)
            for c_i in range(n):
                pos = Decimal(0)
                neg = Decimal(0)
                for s in bar_s:
                    raw = s.values[c_i]
                    if raw is None:
                        continue
                    dv = Decimal(raw)
                    if dv > 0:
                        pos += dv
                    elif dv < 0:
                        neg += dv
                finite.extend((pos, neg))
            for s in line_s:
                for v in s.values:
                    if v is not None:
                        finite.append(Decimal(v))
        else:
            for s in use:
                for v in s.values:
                    if v is not None:
                        finite.append(Decimal(v))
    else:
        for s in series_for_domain:
            for v in s.values:
                if v is not None:
                    finite.append(Decimal(v))
    if not finite:
        finite = [Decimal(0), Decimal(1)]
    data_min = min(finite)
    data_max = max(finite)
    if axis.domain.kind == "fixed":
        return {
            "kind": "fixed",
            "min": axis.domain.min,
            "max": axis.domain.max,
            "ticks": list(axis.domain.ticks),
        }
    lo = Decimal(axis.domain.min) if axis.domain.min is not None else data_min
    hi = Decimal(axis.domain.max) if axis.domain.max is not None else data_max
    if include_zero:
        if lo > 0:
            lo = Decimal(0)
        if hi < 0:
            hi = Decimal(0)
    if lo == hi:
        lo -= Decimal("1")
        hi += Decimal("1")
    pad = (hi - lo) * Decimal("0.08")
    lo_f = lo if (include_zero and lo == 0) else lo - pad
    hi_f = hi + pad
    if include_zero:
        if lo_f > 0:
            lo_f = Decimal(0)
        if hi_f < 0:
            hi_f = Decimal(0)
    target = axis.domain.target_ticks or 5
    ticks = _nice_ticks(float(lo_f), float(hi_f), target)
    return {
        "kind": "generated",
        "min": _plain_decimal(ticks[0]),
        "max": _plain_decimal(ticks[-1]),
        "ticks": [_plain_decimal(t) for t in ticks],
    }


def freeze_chart(
    chart: AxisChartVisual,
    formats: Mapping[str, NumberFormat],
    *,
    box_w: int = PLOT_W + PAD_L + PAD_R,
    box_h: int = PLOT_H + PAD_T + PAD_B + 80,
) -> dict[str, Any]:
    """Dispatch freeze by chart_type (D238)."""
    if isinstance(chart, LineChartVisual):
        return freeze_line_chart(chart, formats, box_w=box_w, box_h=box_h)
    if isinstance(chart, ComboChartVisual):
        return freeze_combo_chart(chart, formats, box_w=box_w, box_h=box_h)
    if isinstance(chart, WaterfallChartVisual):
        return freeze_waterfall_chart(chart, formats, box_w=box_w, box_h=box_h)
    return freeze_bar_chart(chart, formats, box_w=box_w, box_h=box_h)


def paint_chart_html(
    plan: dict[str, Any],
    *,
    plan_attrs: str = "",
    svg_only: bool = False,
) -> list[str]:
    """Emit Chart.js canvas + noscript SVG + one D247 semantic table."""
    sid = plan["surface_id"]
    ctype = plan.get("chart_type", "line")
    out: list[str] = []
    out.append(
        f'<div class="chart-body" data-chart-surface="{_e(sid)}" '
        f'data-chart-type="{_e(ctype)}" {plan_attrs}>'
    )
    if plan.get("heading"):
        out.append(
            f'<div class="band-title chart-pane-title">'
            f"<span>{_e(plan['heading'])}</span>"
        )
        if plan.get("subtitle"):
            out.append(
                f'<span class="chart-pane-subtitle">{_e(plan["subtitle"])}</span>'
            )
        out.append("</div>")

    legend_html = _legend_html(plan)
    if legend_html and plan["identity_strategy"] in (
        "legend",
        "endpoints_and_bar_legend",
    ):
        out.append(legend_html)

    g = plan["geometry"]
    vw, vh = g["view_w"], g["view_h"]
    svg = paint_chart_svg(plan)
    table_html = paint_semantic_table(plan)

    # Label/axis chrome SVG shares frozen plan with both painters (D248/D53).
    chrome_svg = paint_chart_svg(plan, marks=False)
    marks_svg = paint_chart_svg(plan, marks=True, chrome=False)
    if svg_only:
        out.append(
            f'<div class="chart-plot" style="width:{vw}px;height:{vh}px" aria-hidden="true">'
            f"{svg}</div>"
        )
    else:
        cfg = _chartjs_config(plan)
        payload = json.dumps(cfg, ensure_ascii=False).replace("<", "\\u003c")
        # Chart.js paints series marks; frozen SVG chrome+labels overlay for parity.
        out.append(
            f'<div class="chart-plot" style="position:relative;width:{vw}px;height:{vh}px">'
            f'<canvas id="cjs-{_e(sid)}" class="chartjs-canvas" width="{vw}" height="{vh}" '
            f'style="position:absolute;inset:0;width:{vw}px;height:{vh}px" '
            f'aria-hidden="true" data-chart-ready="pending"></canvas>'
            f'<div class="chart-label-overlay" style="position:absolute;inset:0;pointer-events:none" '
            f'aria-hidden="true">{chrome_svg}</div>'
            f"<script type=\"application/json\" id=\"cfg-{_e(sid)}\">{payload}</script>"
            f"<noscript>{svg}</noscript>"
            f"</div>"
        )
        _ = marks_svg  # reserved if canvas fails; noscript carries full SVG
    out.append(table_html)
    out.append("</div>")
    return out


def paint_line_chart_html(
    plan: dict[str, Any],
    *,
    plan_attrs: str = "",
    svg_only: bool = False,
) -> list[str]:
    """Back-compat alias for line-chart HTML paint."""
    return paint_chart_html(plan, plan_attrs=plan_attrs, svg_only=svg_only)


def paint_chart_svg(
    plan: dict[str, Any],
    *,
    marks: bool = True,
    chrome: bool = True,
) -> str:
    """No-JS SVG painter consuming the frozen plan (D57/D248).

    ``marks`` = series paths/markers/bars; ``chrome`` = axes/ticks/labels.
    Chart.js path overlays chrome SVG on the canvas for placement parity.
    """
    ctype = plan.get("chart_type", "line")
    if ctype == "waterfall":
        return _paint_waterfall_svg(plan, marks=marks, chrome=chrome)
    if ctype == "combo":
        return _paint_combo_svg(plan, marks=marks, chrome=chrome)
    if ctype in ("grouped_bar", "horizontal_bar", "stacked_bar"):
        return _paint_bar_svg(plan, marks=marks, chrome=chrome)
    return _paint_line_svg(plan, marks=marks, chrome=chrome)


def paint_line_chart_svg(
    plan: dict[str, Any],
    *,
    marks: bool = True,
    chrome: bool = True,
) -> str:
    """Back-compat alias."""
    return paint_chart_svg(plan, marks=marks, chrome=chrome)


def _paint_combo_svg(
    plan: dict[str, Any],
    *,
    marks: bool = True,
    chrome: bool = True,
) -> str:
    """Bars behind lines; primary (+ optional secondary) chrome (D136/D244/D248)."""
    g = plan["geometry"]
    vw, vh = g["view_w"], g["view_h"]
    pl, pt, pw, ph = g["pad_l"], g["pad_t"], g["plot_w"], g["plot_h"]
    ink = resolve_color("navy", role="text_on_light")
    border = resolve_color("navy", role="border")
    parts = [
        f'<svg class="chart-svg" viewBox="0 0 {vw} {vh}" width="{vw}" height="{vh}" '
        f'role="img" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">'
        f'<rect class="chart-plot-bg" x="0" y="0" width="{vw}" height="{vh}" fill="none"/>'
    ]
    if chrome:
        if plan["category_axis"]["visible"] or plan["value_axis"]["visible"]:
            parts.append(
                f'<line x1="{pl}" y1="{pt + ph}" x2="{pl + pw}" y2="{pt + ph}" '
                f'stroke="{_e(border)}" stroke-width="1"/>'
            )
            parts.append(
                f'<line x1="{pl}" y1="{pt}" x2="{pl}" y2="{pt + ph}" '
                f'stroke="{_e(border)}" stroke-width="1"/>'
            )
        d_min = float(Decimal(plan["domain"]["min"]))
        d_max = float(Decimal(plan["domain"]["max"]))
        if d_min < 0 < d_max:
            zy = g["zero_y"]
            parts.append(
                f'<line class="zero-line" x1="{pl}" y1="{zy:.1f}" '
                f'x2="{pl + pw}" y2="{zy:.1f}" stroke="{_e(border)}" '
                f'stroke-width="1" stroke-dasharray="4 3"/>'
            )
        cat_px = plan["role_sizes"]["category_ticks"]
        val_px = plan["role_sizes"]["value_ticks"]
        if plan["category_axis"]["visible"]:
            for cat in plan["categories"]:
                parts.append(
                    f'<text x="{cat["x"]:.1f}" y="{cat["y"]:.1f}" text-anchor="middle" '
                    f'font-size="{cat_px}" fill="{_e(ink)}">{_e(cat["label"])}</text>'
                )
        if plan["value_axis"]["visible"]:
            span = (d_max - d_min) or 1.0
            for tick, label in zip(plan["domain"]["ticks"], plan["tick_labels"]):
                tv = float(Decimal(tick))
                y = pt + ph - ((tv - d_min) / span) * ph
                parts.append(
                    f'<text x="{pl - 10}" y="{y + 4:.1f}" text-anchor="end" '
                    f'font-size="{val_px}" font-variant-numeric="tabular-nums" '
                    f'fill="{_e(ink)}">{_e(label)}</text>'
                )
        sec = plan.get("secondary_value_axis")
        sec_dom = plan.get("secondary_domain")
        if sec and sec.get("visible") and sec_dom:
            # Right-side secondary axis line + ticks.
            parts.append(
                f'<line x1="{pl + pw}" y1="{pt}" x2="{pl + pw}" y2="{pt + ph}" '
                f'stroke="{_e(border)}" stroke-width="1"/>'
            )
            s_min = float(Decimal(sec_dom["min"]))
            s_max = float(Decimal(sec_dom["max"]))
            s_span = (s_max - s_min) or 1.0
            for tick, label in zip(
                sec_dom["ticks"], plan.get("secondary_tick_labels") or []
            ):
                tv = float(Decimal(tick))
                y = pt + ph - ((tv - s_min) / s_span) * ph
                parts.append(
                    f'<text x="{pl + pw + 10}" y="{y + 4:.1f}" text-anchor="start" '
                    f'font-size="{val_px}" font-variant-numeric="tabular-nums" '
                    f'fill="{_e(ink)}">{_e(label)}</text>'
                )
            if sec.get("title"):
                cy = pt + ph / 2
                tx = pl + pw + g["pad_r"] - 12
                parts.append(
                    f'<text x="{tx}" y="{cy}" text-anchor="middle" '
                    f'font-size="{plan["role_sizes"]["axis_titles"]}" '
                    f'transform="rotate(90 {tx} {cy})" fill="{_e(ink)}">'
                    f'{_e(sec["title"])}</text>'
                )
        title_px = plan["role_sizes"]["axis_titles"]
        cat_title = plan["category_axis"].get("title")
        val_title = plan["value_axis"].get("title")
        if plan["category_axis"]["visible"] and cat_title:
            parts.append(
                f'<text x="{pl + pw / 2}" y="{pt + ph + 52}" text-anchor="middle" '
                f'font-size="{title_px}" fill="{_e(ink)}">{_e(cat_title)}</text>'
            )
        if plan["value_axis"]["visible"] and val_title:
            cy = pt + ph / 2
            parts.append(
                f'<text x="16" y="{cy}" text-anchor="middle" font-size="{title_px}" '
                f'transform="rotate(-90 16 {cy})" fill="{_e(ink)}">{_e(val_title)}</text>'
            )
        for grp in plan.get("category_groups") or []:
            x1, y1, x2, y2 = grp["x1"], grp["y1"], grp["x2"], grp["y2"]
            parts.append(
                f'<g class="category-group" data-group-id="{_e(grp["group_id"])}">'
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="{_e(border)}" stroke-width="1.5"/>'
                f'<text x="{(x1 + x2) / 2:.1f}" y="{y2 + 14:.1f}" text-anchor="middle" '
                f'font-size="{cat_px}" fill="{_e(ink)}">{_e(grp["label"])}</text>'
                f"</g>"
            )

    series_by_id = {s["series_id"]: s for s in plan["series"]}
    if marks:
        # Bars first (behind lines).
        for bar in plan.get("bars") or []:
            if bar.get("missing") or not bar.get("finite"):
                continue
            color = series_by_id[bar["series_id"]]["color"]
            parts.append(
                f'<rect class="bar" data-series="{_e(bar["series_id"])}" '
                f'data-category="{_e(bar["category_id"])}" '
                f'x="{bar["x"]:.1f}" y="{bar["y"]:.1f}" '
                f'width="{bar["width"]:.1f}" height="{bar["height"]:.1f}" '
                f'fill="{_e(color)}"/>'
            )
        # Line polylines + markers.
        by_series: dict[str, list[dict[str, Any]]] = {}
        for p in plan["points"]:
            if p.get("mark_type") != "line":
                continue
            by_series.setdefault(p["series_id"], []).append(p)
        for sp in plan["series"]:
            if sp.get("mark_type") != "line":
                continue
            pts = by_series.get(sp["series_id"]) or []
            color = sp["color"]
            dash = _DASHARRAY.get(sp["line_style"])
            dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
            segment: list[str] = []
            for p in pts:
                if not p["finite"]:
                    if len(segment) >= 2:
                        parts.append(
                            f'<polyline class="combo-line" fill="none" '
                            f'stroke="{_e(color)}" stroke-width="2.5" '
                            f'points="{" ".join(segment)}"{dash_attr}/>'
                        )
                    segment = []
                    continue
                segment.append(f'{p["x"]:.1f},{p["y"]:.1f}')
            if len(segment) >= 2:
                parts.append(
                    f'<polyline class="combo-line" fill="none" '
                    f'stroke="{_e(color)}" stroke-width="2.5" '
                    f'points="{" ".join(segment)}"{dash_attr}/>'
                )
            for p in pts:
                if not p["finite"]:
                    continue
                parts.append(_marker_svg(p["x"], p["y"], sp["marker"], color))

    if chrome:
        lab_px = plan["role_sizes"]["ordinary_values"]
        ser_px = plan["role_sizes"]["series_labels"]
        point_lookup = {
            (p["series_id"], p["category_id"]): p for p in plan["points"]
        }
        for place in plan["placements"]:
            if place["class"] == "suppressed":
                continue
            kind = place.get("kind")
            if kind == "value":
                # Bar ordinary / line ordinary share this kind.
                series_color = series_by_id[place["series_id"]]["color"]
                mark = series_by_id[place["series_id"]].get("mark_type")
                show = plan["show_ordinary_values"] if mark == "line" or not plan.get(
                    "geometry", {}
                ).get("stacked") else False
                if mark == "bar" and plan.get("geometry", {}).get("stacked"):
                    continue
                if not show and mark == "line":
                    continue
                if mark == "bar" and not plan["show_ordinary_values"]:
                    continue
                label_color = series_color if place["class"] == "leader" or mark == "line" else ink
                tx, ty = place["x"], place["y"]
                text = place.get("text")
                if text is None:
                    p = point_lookup.get((place["series_id"], place["category_id"]))
                    text = p["visible"] if p else ""
                if place["class"] == "leader":
                    parts.append(
                        f'<line x1="{place.get("anchor_x", tx):.1f}" '
                        f'y1="{place.get("anchor_y", ty):.1f}" '
                        f'x2="{tx:.1f}" y2="{ty:.1f}" '
                        f'stroke="{_e(series_color)}" stroke-width="1" opacity="0.7"/>'
                    )
                parts.append(
                    f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" '
                    f'font-size="{lab_px}" font-variant-numeric="tabular-nums" '
                    f'fill="{_e(label_color)}" data-placement="{place["class"]}">'
                    f"{_e(text)}</text>"
                )
            elif kind == "boxed_label":
                tx, ty = place["x"], place["y"]
                tw = place.get("box_w", 40)
                th = place.get("box_h", lab_px + 8)
                surface = resolve_color("white", role="surface")
                parts.append(
                    f'<g class="boxed-label" data-series="{_e(place["series_id"])}" '
                    f'data-category="{_e(place["category_id"])}">'
                    f'<rect x="{tx - tw / 2:.1f}" y="{ty - th / 2:.1f}" '
                    f'width="{tw:.1f}" height="{th:.1f}" '
                    f'fill="{_e(surface)}" stroke="{_e(border)}" stroke-width="1" rx="2"/>'
                    f'<text x="{tx:.1f}" y="{ty + lab_px * 0.35:.1f}" text-anchor="middle" '
                    f'font-size="{lab_px}" font-variant-numeric="tabular-nums" '
                    f'fill="{_e(ink)}" data-placement="boxed">{_e(place["text"])}</text>'
                    f"</g>"
                )
            elif kind == "segment" and plan.get("show_segment_labels"):
                tx, ty = place["x"], place["y"]
                series_color = series_by_id[place["series_id"]]["color"]
                parts.append(
                    f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" '
                    f'font-size="{plan["role_sizes"]["segment_labels"]}" '
                    f'font-variant-numeric="tabular-nums" fill="{_e(series_color)}" '
                    f'data-placement="segment">{_e(place["text"])}</text>'
                )
            elif kind == "stack_total" and plan.get("show_stack_totals"):
                tx, ty = place["x"], place["y"]
                parts.append(
                    f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" '
                    f'font-size="{plan["role_sizes"]["stack_totals"]}" '
                    f'font-variant-numeric="tabular-nums" fill="{_e(ink)}" '
                    f'data-placement="stack-total">{_e(place["text"])}</text>'
                )
            elif kind == "identity" and plan["identity_strategy"] in (
                "endpoints",
                "endpoints_and_bar_legend",
            ):
                p = point_lookup.get((place["series_id"], place["category_id"]))
                if p is None or not p.get("finite"):
                    continue
                tx, ty = place["x"], place["y"]
                name = series_by_id[p["series_id"]]["name"]
                parts.append(
                    f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="start" '
                    f'font-size="{ser_px}" '
                    f'fill="{_e(series_by_id[p["series_id"]]["color"])}" '
                    f'data-placement="endpoint">{_e(name)}</text>'
                )

    parts.append("</svg>")
    return "".join(parts)


def _paint_line_svg(
    plan: dict[str, Any],
    *,
    marks: bool = True,
    chrome: bool = True,
) -> str:
    g = plan["geometry"]
    vw, vh = g["view_w"], g["view_h"]
    pl, pt, pw, ph = g["pad_l"], g["pad_t"], g["plot_w"], g["plot_h"]
    parts = [
        f'<svg class="chart-svg" viewBox="0 0 {vw} {vh}" width="{vw}" height="{vh}" '
        f'role="img" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">'
        f'<rect class="chart-plot-bg" x="0" y="0" width="{vw}" height="{vh}" fill="none"/>'
    ]
    if chrome:
        # Axes only — no gridlines (D63).
        if plan["category_axis"]["visible"] or plan["value_axis"]["visible"]:
            parts.append(
                f'<line x1="{pl}" y1="{pt + ph}" x2="{pl + pw}" y2="{pt + ph}" '
                f'stroke="{_e(resolve_color("navy", role="border"))}" stroke-width="1"/>'
            )
            parts.append(
                f'<line x1="{pl}" y1="{pt}" x2="{pl}" y2="{pt + ph}" '
                f'stroke="{_e(resolve_color("navy", role="border"))}" stroke-width="1"/>'
            )

        cat_px = plan["role_sizes"]["category_ticks"]
        val_px = plan["role_sizes"]["value_ticks"]
        if plan["category_axis"]["visible"]:
            for cat in plan["categories"]:
                parts.append(
                    f'<text x="{cat["x"]:.1f}" y="{pt + ph + 22}" text-anchor="middle" '
                    f'font-size="{cat_px}" fill="{_e(resolve_color("navy", role="text_on_light"))}">'
                    f'{_e(cat["label"])}</text>'
                )
        if plan["value_axis"]["visible"]:
            y_min = float(plan["domain"]["min"])
            y_max = float(plan["domain"]["max"])
            span = y_max - y_min or 1.0
            for tick, label in zip(plan["domain"]["ticks"], plan["tick_labels"]):
                tv = float(Decimal(tick))
                y = pt + ph - ((tv - y_min) / span) * ph
                parts.append(
                    f'<text x="{pl - 10}" y="{y + 4:.1f}" text-anchor="end" '
                    f'font-size="{val_px}" font-variant-numeric="tabular-nums" '
                    f'fill="{_e(resolve_color("navy", role="text_on_light"))}">'
                    f"{_e(label)}</text>"
                )
        title_px = plan["role_sizes"]["axis_titles"]
        ink = resolve_color("navy", role="text_on_light")
        cat_title = plan["category_axis"].get("title")
        if plan["category_axis"]["visible"] and cat_title:
            parts.append(
                f'<text x="{pl + pw / 2}" y="{pt + ph + 52}" text-anchor="middle" '
                f'font-size="{title_px}" fill="{_e(ink)}">{_e(cat_title)}</text>'
            )
        val_title = plan["value_axis"].get("title")
        if plan["value_axis"]["visible"] and val_title:
            cy = pt + ph / 2
            parts.append(
                f'<text x="16" y="{cy}" text-anchor="middle" font-size="{title_px}" '
                f'transform="rotate(-90 16 {cy})" fill="{_e(ink)}">{_e(val_title)}</text>'
            )

    by_series: dict[str, list[dict[str, Any]]] = {}
    for p in plan["points"]:
        by_series.setdefault(p["series_id"], []).append(p)

    if marks:
        for sp in plan["series"]:
            pts = by_series[sp["series_id"]]
            color = sp["color"]
            dash = _DASHARRAY.get(sp["line_style"])
            dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
            # Break path on nulls (D92).
            segment: list[str] = []
            for p in pts:
                if not p["finite"]:
                    if len(segment) >= 2:
                        parts.append(
                            f'<polyline fill="none" stroke="{_e(color)}" stroke-width="2.5" '
                            f'points="{" ".join(segment)}"{dash_attr}/>'
                        )
                    segment = []
                    continue
                segment.append(f'{p["x"]:.1f},{p["y"]:.1f}')
            if len(segment) >= 2:
                parts.append(
                    f'<polyline fill="none" stroke="{_e(color)}" stroke-width="2.5" '
                    f'points="{" ".join(segment)}"{dash_attr}/>'
                )
            for p in pts:
                if not p["finite"]:
                    continue
                parts.append(_marker_svg(p["x"], p["y"], sp["marker"], color))

    if chrome:
        # Point labels + endpoint identities from frozen placements (D53).
        lab_px = plan["role_sizes"]["ordinary_values"]
        ser_px = plan["role_sizes"]["series_labels"]
        series_by_id = {s["series_id"]: s for s in plan["series"]}
        point_lookup = {
            (p["series_id"], p["category_id"]): p for p in plan["points"]
        }
        for place in plan["placements"]:
            if place["class"] == "suppressed":
                continue
            p = point_lookup.get((place["series_id"], place["category_id"]))
            if p is None or not p.get("finite"):
                continue
            if place.get("kind") == "value" and plan["show_ordinary_values"]:
                tx, ty = place["x"], place["y"]
                if place["class"] == "leader":
                    parts.append(
                        f'<line x1="{p["x"]:.1f}" y1="{p["y"]:.1f}" '
                        f'x2="{tx:.1f}" y2="{ty:.1f}" '
                        f'stroke="{_e(series_by_id[p["series_id"]]["color"])}" '
                        f'stroke-width="1" opacity="0.7"/>'
                    )
                parts.append(
                    f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" '
                    f'font-size="{lab_px}" font-variant-numeric="tabular-nums" '
                    f'fill="{_e(series_by_id[p["series_id"]]["color"])}" '
                    f'data-placement="{place["class"]}">{_e(p["visible"])}</text>'
                )
            if (
                place.get("kind") == "identity"
                and plan["identity_strategy"] == "endpoints"
            ):
                tx, ty = place["x"], place["y"]
                name = series_by_id[p["series_id"]]["name"]
                parts.append(
                    f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="start" '
                    f'font-size="{ser_px}" '
                    f'fill="{_e(series_by_id[p["series_id"]]["color"])}" '
                    f'data-placement="endpoint">{_e(name)}</text>'
                )

    parts.append("</svg>")
    return "".join(parts)


def _paint_bar_svg(
    plan: dict[str, Any],
    *,
    marks: bool = True,
    chrome: bool = True,
) -> str:
    g = plan["geometry"]
    vw, vh = g["view_w"], g["view_h"]
    pl, pt, pw, ph = g["pad_l"], g["pad_t"], g["plot_w"], g["plot_h"]
    horizontal = bool(g.get("horizontal"))
    ink = resolve_color("navy", role="text_on_light")
    border = resolve_color("navy", role="border")
    parts = [
        f'<svg class="chart-svg" viewBox="0 0 {vw} {vh}" width="{vw}" height="{vh}" '
        f'role="img" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">'
        f'<rect class="chart-plot-bg" x="0" y="0" width="{vw}" height="{vh}" fill="none"/>'
    ]
    if chrome:
        if plan["category_axis"]["visible"] or plan["value_axis"]["visible"]:
            # Baseline axes.
            parts.append(
                f'<line x1="{pl}" y1="{pt + ph}" x2="{pl + pw}" y2="{pt + ph}" '
                f'stroke="{_e(border)}" stroke-width="1"/>'
            )
            parts.append(
                f'<line x1="{pl}" y1="{pt}" x2="{pl}" y2="{pt + ph}" '
                f'stroke="{_e(border)}" stroke-width="1"/>'
            )
        # Semantic zero line only when zero is inside the visible domain (D84/D157).
        leading = plan["value_axis"].get("leading_break")
        d_min = float(Decimal(plan["domain"]["min"]))
        d_max = float(Decimal(plan["domain"]["max"]))
        if leading is None and d_min < 0 < d_max:
            if horizontal:
                zx = g["zero_x"]
                parts.append(
                    f'<line class="zero-line" x1="{zx:.1f}" y1="{pt}" '
                    f'x2="{zx:.1f}" y2="{pt + ph}" stroke="{_e(border)}" '
                    f'stroke-width="1" stroke-dasharray="4 3"/>'
                )
            else:
                zy = g["zero_y"]
                parts.append(
                    f'<line class="zero-line" x1="{pl}" y1="{zy:.1f}" '
                    f'x2="{pl + pw}" y2="{zy:.1f}" stroke="{_e(border)}" '
                    f'stroke-width="1" stroke-dasharray="4 3"/>'
                )
        if leading is not None:
            # Break chrome at the disclosed boundary (D157/D243).
            if horizontal:
                bx = g["zero_x"]
                parts.append(
                    f'<g class="leading-break" data-break-to="{_e(leading)}">'
                    f'<line x1="{bx:.1f}" y1="{pt}" x2="{bx:.1f}" y2="{pt + ph}" '
                    f'stroke="{_e(border)}" stroke-width="1.5"/>'
                    f'<path d="M{bx - 6:.1f},{pt + ph / 2 - 8} l6,8 l-6,8" '
                    f'fill="none" stroke="{_e(border)}" stroke-width="1.5"/>'
                    f"</g>"
                )
            else:
                by = g["zero_y"]
                parts.append(
                    f'<g class="leading-break" data-break-to="{_e(leading)}">'
                    f'<line x1="{pl}" y1="{by:.1f}" x2="{pl + pw}" y2="{by:.1f}" '
                    f'stroke="{_e(border)}" stroke-width="1.5"/>'
                    f"</g>"
                )

        cat_px = plan["role_sizes"]["category_ticks"]
        val_px = plan["role_sizes"]["value_ticks"]
        if plan["category_axis"]["visible"]:
            for cat in plan["categories"]:
                if horizontal:
                    parts.append(
                        f'<text x="{cat["x"]:.1f}" y="{cat["y"] + 4:.1f}" text-anchor="end" '
                        f'font-size="{cat_px}" fill="{_e(ink)}">{_e(cat["label"])}</text>'
                    )
                else:
                    parts.append(
                        f'<text x="{cat["x"]:.1f}" y="{cat["y"]:.1f}" text-anchor="middle" '
                        f'font-size="{cat_px}" fill="{_e(ink)}">{_e(cat["label"])}</text>'
                    )
        if plan["value_axis"]["visible"]:
            vis_min = float(Decimal(leading)) if leading is not None else d_min
            vis_max = d_max
            span = (vis_max - vis_min) or 1.0
            for tick, label in zip(plan["domain"]["ticks"], plan["tick_labels"]):
                tv = float(Decimal(tick))
                if leading is not None and tv < vis_min - 1e-12:
                    continue
                if horizontal:
                    x = pl + ((tv - vis_min) / span) * pw
                    parts.append(
                        f'<text x="{x:.1f}" y="{pt + ph + 22}" text-anchor="middle" '
                        f'font-size="{val_px}" font-variant-numeric="tabular-nums" '
                        f'fill="{_e(ink)}">{_e(label)}</text>'
                    )
                else:
                    y = pt + ph - ((tv - vis_min) / span) * ph
                    parts.append(
                        f'<text x="{pl - 10}" y="{y + 4:.1f}" text-anchor="end" '
                        f'font-size="{val_px}" font-variant-numeric="tabular-nums" '
                        f'fill="{_e(ink)}">{_e(label)}</text>'
                    )
        title_px = plan["role_sizes"]["axis_titles"]
        cat_title = plan["category_axis"].get("title")
        val_title = plan["value_axis"].get("title")
        if plan["category_axis"]["visible"] and cat_title:
            if horizontal:
                cy = pt + ph / 2
                parts.append(
                    f'<text x="18" y="{cy}" text-anchor="middle" font-size="{title_px}" '
                    f'transform="rotate(-90 18 {cy})" fill="{_e(ink)}">{_e(cat_title)}</text>'
                )
            else:
                parts.append(
                    f'<text x="{pl + pw / 2}" y="{pt + ph + 52}" text-anchor="middle" '
                    f'font-size="{title_px}" fill="{_e(ink)}">{_e(cat_title)}</text>'
                )
        if plan["value_axis"]["visible"] and val_title:
            if horizontal:
                parts.append(
                    f'<text x="{pl + pw / 2}" y="{pt + ph + 52}" text-anchor="middle" '
                    f'font-size="{title_px}" fill="{_e(ink)}">{_e(val_title)}</text>'
                )
            else:
                cy = pt + ph / 2
                parts.append(
                    f'<text x="16" y="{cy}" text-anchor="middle" font-size="{title_px}" '
                    f'transform="rotate(-90 16 {cy})" fill="{_e(ink)}">{_e(val_title)}</text>'
                )

        # Category group brackets (D155/D237).
        for grp in plan.get("category_groups") or []:
            x1, y1, x2, y2 = grp["x1"], grp["y1"], grp["x2"], grp["y2"]
            parts.append(
                f'<g class="category-group" data-group-id="{_e(grp["group_id"])}">'
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="{_e(border)}" stroke-width="1.5"/>'
                f'<text x="{(x1 + x2) / 2:.1f}" y="{y2 + 14:.1f}" text-anchor="middle" '
                f'font-size="{cat_px}" fill="{_e(ink)}">{_e(grp["label"])}</text>'
                f"</g>"
            )

    series_by_id = {s["series_id"]: s for s in plan["series"]}
    if marks:
        for bar in plan.get("bars") or []:
            if bar.get("missing") or not bar.get("finite"):
                continue
            color = series_by_id[bar["series_id"]]["color"]
            parts.append(
                f'<rect class="bar" data-series="{_e(bar["series_id"])}" '
                f'data-category="{_e(bar["category_id"])}" '
                f'x="{bar["x"]:.1f}" y="{bar["y"]:.1f}" '
                f'width="{bar["width"]:.1f}" height="{bar["height"]:.1f}" '
                f'fill="{_e(color)}"/>'
            )

    if chrome:
        lab_px = plan["role_sizes"]["ordinary_values"]
        for place in plan["placements"]:
            if place["class"] == "suppressed":
                continue
            kind = place.get("kind")
            if kind == "value" and plan["show_ordinary_values"]:
                # D80/D303: ordinary bar values are navy; leaders may use series color.
                series_color = series_by_id[place["series_id"]]["color"]
                label_color = series_color if place["class"] == "leader" else ink
                tx, ty = place["x"], place["y"]
                if place["class"] == "leader":
                    parts.append(
                        f'<line x1="{place.get("anchor_x", tx):.1f}" '
                        f'y1="{place.get("anchor_y", ty):.1f}" '
                        f'x2="{tx:.1f}" y2="{ty:.1f}" '
                        f'stroke="{_e(series_color)}" stroke-width="1" opacity="0.7"/>'
                    )
                parts.append(
                    f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" '
                    f'font-size="{lab_px}" font-variant-numeric="tabular-nums" '
                    f'fill="{_e(label_color)}" data-placement="{place["class"]}">'
                    f'{_e(place["text"])}</text>'
                )
            elif kind == "boxed_label":
                tx, ty = place["x"], place["y"]
                tw = place.get("box_w", 40)
                th = place.get("box_h", lab_px + 8)
                surface = resolve_color("white", role="surface")
                parts.append(
                    f'<g class="boxed-label" data-series="{_e(place["series_id"])}" '
                    f'data-category="{_e(place["category_id"])}">'
                    f'<rect x="{tx - tw / 2:.1f}" y="{ty - th / 2:.1f}" '
                    f'width="{tw:.1f}" height="{th:.1f}" '
                    f'fill="{_e(surface)}" stroke="{_e(border)}" stroke-width="1" rx="2"/>'
                    f'<text x="{tx:.1f}" y="{ty + lab_px * 0.35:.1f}" text-anchor="middle" '
                    f'font-size="{lab_px}" font-variant-numeric="tabular-nums" '
                    f'fill="{_e(ink)}" data-placement="boxed">{_e(place["text"])}</text>'
                    f"</g>"
                )
            elif kind == "segment" and plan.get("show_segment_labels"):
                tx, ty = place["x"], place["y"]
                seg_px = plan["role_sizes"].get("segment_labels", lab_px)
                color = place.get("color") or ink
                if place["class"] == "leader":
                    parts.append(
                        f'<line x1="{place.get("anchor_x", tx):.1f}" '
                        f'y1="{place.get("anchor_y", ty):.1f}" '
                        f'x2="{tx:.1f}" y2="{ty:.1f}" '
                        f'stroke="{_e(place.get("connector_color") or color)}" '
                        f'stroke-width="1" opacity="0.7"/>'
                    )
                parts.append(
                    f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" '
                    f'font-size="{seg_px}" font-variant-numeric="tabular-nums" '
                    f'fill="{_e(color)}" data-placement="{place["class"]}" '
                    f'data-kind="segment">{_e(place["text"])}</text>'
                )
            elif kind == "stack_total" and plan.get("show_stack_totals"):
                tx, ty = place["x"], place["y"]
                tot_px = plan["role_sizes"].get("stack_totals", lab_px)
                parts.append(
                    f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" '
                    f'font-size="{tot_px}" font-weight="700" '
                    f'font-variant-numeric="tabular-nums" '
                    f'fill="{_e(place.get("color") or ink)}" '
                    f'data-placement="{place["class"]}" data-kind="stack_total">'
                    f'{_e(place["text"])}</text>'
                )

        # Coverage callout chrome (D50/D301) — value then label/period; aria-hidden.
        cov = plan.get("coverage_callout")
        if cov:
            vx, vy = cov["x"], cov["y"]
            v_px = cov["value_px"]
            t_px = cov["text_px"]
            label_parts = [cov["label"]]
            if cov.get("period"):
                label_parts.append(cov["period"])
            label_text = " · ".join(label_parts)
            parts.append(
                f'<g class="coverage-callout" data-callout-id="{_e(cov["callout_id"])}" '
                f'aria-hidden="true">'
                f'<text x="{vx - 4:.1f}" y="{vy:.1f}" text-anchor="end" '
                f'font-size="{v_px}" font-weight="700" '
                f'fill="{_e(ink)}">{_e(cov["value_visible"])}</text>'
                f'<text x="{vx + 4:.1f}" y="{vy:.1f}" text-anchor="start" '
                f'font-size="{t_px}" font-weight="700" '
                f'fill="{_e(ink)}">{_e(label_text)}</text>'
                f"</g>"
            )

    parts.append("</svg>")
    return "".join(parts)


def paint_semantic_table(plan: dict[str, Any]) -> str:
    """One D106/D247 table — visually hidden unless fallback."""
    t = plan["semantic_table"]
    sid = plan["surface_id"]
    tid = f"{sid}-semantic-table"
    hidden = t.get("visible") is not True
    cls = "chart-semantic-table" + ("" if not hidden else " visually-hidden")
    rows = []
    # header
    ths = ['<th scope="col">Category</th>']
    for col in t["columns"]:
        ths.append(f'<th scope="col">{_e(col["label"])}</th>')
    rows.append(f"<tr>{''.join(ths)}</tr>")
    for row in t["rows"]:
        cells = [f'<th scope="row">{_e(row["label"])}</th>']
        for cell in row["cells"]:
            aria = (
                f' aria-label="{_e(cell["accessible"])}"'
                if cell["accessible"] != cell["visible"]
                else ""
            )
            cells.append(
                f'<td class="num"{aria}>{_e(cell["visible"])}</td>'
            )
        rows.append(f"<tr>{''.join(cells)}</tr>")
    facts = "".join(
        f"<li>{_e(f)}</li>" for f in t.get("facts") or []
    )
    facts_block = (
        f'<div class="chart-facts{" visually-hidden" if hidden else ""}"><ul>{facts}</ul></div>'
        if facts
        else ""
    )
    return (
        f'<table id="{_e(tid)}" class="{cls}" data-semantic-table="1" '
        f'data-chart-surface="{_e(sid)}">'
        f"<thead>{rows[0]}</thead><tbody>{''.join(rows[1:])}</tbody>"
        f"</table>{facts_block}"
    )


def _paint_waterfall_svg(
    plan: dict[str, Any],
    *,
    marks: bool = True,
    chrome: bool = True,
) -> str:
    """No-JS SVG for waterfall bars + connectors + structural labels (D245/D248)."""
    g = plan["geometry"]
    vw, vh = g["view_w"], g["view_h"]
    pl, pt, pw, ph = g["pad_l"], g["pad_t"], g["plot_w"], g["plot_h"]
    ink = resolve_color("navy", role="text_on_light")
    border = resolve_color("navy", role="border")
    connector_c = resolve_color("ink_faint", role="fill")
    parts = [
        f'<svg class="chart-svg" viewBox="0 0 {vw} {vh}" width="{vw}" height="{vh}" '
        f'role="img" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">'
        f'<rect class="chart-plot-bg" x="0" y="0" width="{vw}" height="{vh}" fill="none"/>'
    ]
    if chrome:
        if plan["category_axis"]["visible"] or plan["value_axis"]["visible"]:
            parts.append(
                f'<line x1="{pl}" y1="{pt + ph}" x2="{pl + pw}" y2="{pt + ph}" '
                f'stroke="{_e(border)}" stroke-width="1"/>'
            )
            parts.append(
                f'<line x1="{pl}" y1="{pt}" x2="{pl}" y2="{pt + ph}" '
                f'stroke="{_e(border)}" stroke-width="1"/>'
            )
        d_min = float(Decimal(plan["domain"]["min"]))
        d_max = float(Decimal(plan["domain"]["max"]))
        # Waterfall bridging requires zero; draw when zero is in the domain (D84/D245).
        if d_min <= 0 <= d_max:
            zy = g["zero_y"]
            parts.append(
                f'<line class="zero-line" x1="{pl}" y1="{zy:.1f}" '
                f'x2="{pl + pw}" y2="{zy:.1f}" stroke="{_e(border)}" '
                f'stroke-width="1" stroke-dasharray="4 3"/>'
            )
        cat_px = plan["role_sizes"]["category_ticks"]
        val_px = plan["role_sizes"]["value_ticks"]
        if plan["category_axis"]["visible"]:
            for cat in plan["categories"]:
                parts.append(
                    f'<text x="{cat["x"]:.1f}" y="{cat["y"]:.1f}" text-anchor="middle" '
                    f'font-size="{cat_px}" fill="{_e(ink)}">{_e(cat["label"])}</text>'
                )
        if plan["value_axis"]["visible"]:
            span = (d_max - d_min) or 1.0
            for tick, label in zip(plan["domain"]["ticks"], plan["tick_labels"]):
                tv = float(Decimal(tick))
                y = pt + ph - ((tv - d_min) / span) * ph
                parts.append(
                    f'<text x="{pl - 10}" y="{y + 4:.1f}" text-anchor="end" '
                    f'font-size="{val_px}" font-variant-numeric="tabular-nums" '
                    f'fill="{_e(ink)}">{_e(label)}</text>'
                )
        title_px = plan["role_sizes"]["axis_titles"]
        cat_title = plan["category_axis"].get("title")
        val_title = plan["value_axis"].get("title")
        if plan["category_axis"]["visible"] and cat_title:
            parts.append(
                f'<text x="{pl + pw / 2}" y="{pt + ph + 52}" text-anchor="middle" '
                f'font-size="{title_px}" fill="{_e(ink)}">{_e(cat_title)}</text>'
            )
        if plan["value_axis"]["visible"] and val_title:
            cy = pt + ph / 2
            parts.append(
                f'<text x="16" y="{cy}" text-anchor="middle" font-size="{title_px}" '
                f'transform="rotate(-90 16 {cy})" fill="{_e(ink)}">{_e(val_title)}</text>'
            )
        # Connectors + structural labels ride the chrome overlay so settled
        # Chart.js path retains bridges/labels (D245/D248/D307); bars stay on marks.
        for conn in plan.get("connectors") or []:
            parts.append(
                f'<line class="waterfall-connector" '
                f'data-from="{_e(conn["from_category_id"])}" '
                f'data-to="{_e(conn["to_category_id"])}" '
                f'x1="{conn["x1"]:.1f}" y1="{conn["y"]:.1f}" '
                f'x2="{conn["x2"]:.1f}" y2="{conn["y"]:.1f}" '
                f'stroke="{_e(connector_c)}" stroke-width="1.5"/>'
            )
        lab_px = plan["role_sizes"].get(
            "structural_values", plan.get("structural_label_px", 18)
        )
        for place in plan["placements"]:
            if place.get("kind") != "structural":
                continue
            parts.append(
                f'<text class="waterfall-value" x="{place["x"]:.1f}" y="{place["y"]:.1f}" '
                f'text-anchor="middle" font-size="{lab_px}" font-weight="700" '
                f'font-variant-numeric="tabular-nums" fill="{_e(ink)}" '
                f'data-placement="structural" data-category="{_e(place["category_id"])}">'
                f'{_e(place["text"])}</text>'
            )

    if marks:
        for bar in plan.get("bars") or []:
            parts.append(
                f'<rect class="bar waterfall-bar" data-series="{_e(bar["series_id"])}" '
                f'data-category="{_e(bar["category_id"])}" data-role="{_e(bar["role"])}" '
                f'x="{bar["x"]:.1f}" y="{bar["y"]:.1f}" '
                f'width="{bar["width"]:.1f}" height="{bar["height"]:.1f}" '
                f'fill="{_e(bar["color"])}"/>'
            )
        # Full SVG (noscript) still needs connectors/labels when chrome=False.
        if not chrome:
            for conn in plan.get("connectors") or []:
                parts.append(
                    f'<line class="waterfall-connector" '
                    f'data-from="{_e(conn["from_category_id"])}" '
                    f'data-to="{_e(conn["to_category_id"])}" '
                    f'x1="{conn["x1"]:.1f}" y1="{conn["y"]:.1f}" '
                    f'x2="{conn["x2"]:.1f}" y2="{conn["y"]:.1f}" '
                    f'stroke="{_e(connector_c)}" stroke-width="1.5"/>'
                )
            lab_px = plan["role_sizes"].get(
                "structural_values", plan.get("structural_label_px", 18)
            )
            for place in plan["placements"]:
                if place.get("kind") != "structural":
                    continue
                parts.append(
                    f'<text class="waterfall-value" x="{place["x"]:.1f}" y="{place["y"]:.1f}" '
                    f'text-anchor="middle" font-size="{lab_px}" font-weight="700" '
                    f'font-variant-numeric="tabular-nums" fill="{_e(ink)}" '
                    f'data-placement="structural" data-category="{_e(place["category_id"])}">'
                    f'{_e(place["text"])}</text>'
                )

    parts.append("</svg>")
    return "".join(parts)


def chart_boot_script() -> str:
    """Boot Chart.js from embedded configs; mark capture readiness (D108/D109)."""
    return (
        "<script>(function(){"
        "if(typeof Chart==='undefined')return;"
        "function markReady(c){c.dataset.chartReady='ready';c.setAttribute('data-chart-ready','ready');"
        "requestAnimationFrame(function(){c.setAttribute('data-chart-frame','1');});}"
        "function boot(){"
        "document.querySelectorAll('script[id^=\"cfg-\"]').forEach(function(el){"
        "var sid=el.id.slice(4);"
        "var canvas=document.getElementById('cjs-'+sid);"
        "if(!canvas||canvas.dataset.chartReady==='ready')return;"
        "try{"
        "var cfg=JSON.parse(el.textContent);"
        "cfg.options=cfg.options||{};"
        "cfg.options.animation=false;"
        "cfg.options.responsive=false;"
        "cfg.options.maintainAspectRatio=false;"
        "/* ticks/labels come from frozen SVG overlay — hide Chart.js tick text */"
        "if(cfg.options.scales){['x','y'].forEach(function(ax){"
        "if(cfg.options.scales[ax]&&cfg.options.scales[ax].ticks)"
        "{cfg.options.scales[ax].ticks.display=false;cfg.options.scales[ax].border={display:false};"
        "cfg.options.scales[ax].grid={display:false};}});}"
        "new Chart(canvas.getContext('2d'),cfg);"
        "markReady(canvas);"
        "}catch(e){canvas.dataset.chartReady='error';}"
        "});"
        "}"
        "if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);"
        "else boot();"
        "})();</script>"
    )


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _e(text: Any) -> str:
    return html.escape(str(text), quote=True)


def _ordinary_values_show(chart: AxisChartVisual) -> bool:
    if getattr(chart, "chart_type", None) == "stacked_bar":
        return False  # stacked uses stack_segments (D231/D295)
    if (
        getattr(chart, "chart_type", None) == "combo"
        and getattr(chart, "bar_mode", None) == "stacked"
    ):
        # Stacked combo: ordinary_values govern line points only (D231/D244).
        pass
    if chart.display is None or chart.display.ordinary_values is None:
        return True
    return chart.display.ordinary_values == "show"


def _stack_segments_show(chart: Any) -> bool:
    if chart.display is None or chart.display.stack_segments is None:
        return False
    return chart.display.stack_segments == "show"


def _stack_totals_show(chart: Any) -> bool:
    aux = getattr(chart, "auxiliary_series", None) or []
    if any(getattr(a, "role", None) == "authored_stack_total" for a in aux):
        return True
    if chart.display is None or chart.display.stack_totals is None:
        return False
    return chart.display.stack_totals == "show"


def _identity_strategy(
    chart: LineChartVisual,
    series_plans: list[dict[str, Any]],
    *,
    endpoints_fit: bool = True,
) -> str:
    if chart.display is not None and chart.display.series_identity is not None:
        pol = chart.display.series_identity
        if pol == "pane_title":
            return "pane_title"
        if pol == "legend":
            return "legend"
    # auto (D15/D37): all endpoint labels only when every series endpoint fits;
    # otherwise one complete legend — never a partial mix.
    if endpoints_fit:
        return "endpoints"
    return "legend"


def _role_sizes(chart: AxisChartVisual) -> dict[str, int]:
    sizes = {k: lo for k, (lo, _hi) in _ROLE_BOUNDS.items()}
    typo = chart.typography
    if typo is None:
        return sizes
    mode = typo.mode
    for key in _ROLE_BOUNDS:
        val = getattr(typo, key, None)
        if val is not None:
            sizes[key] = val
        elif mode == "adaptive":
            # Grow ordinary values modestly when adaptive (tracer default mid).
            lo, hi = _ROLE_BOUNDS[key]
            sizes[key] = min(hi, lo + 2)
    return sizes


def _waterfall_role_sizes(chart: WaterfallChartVisual) -> dict[str, int]:
    sizes = _role_sizes(chart)  # type: ignore[arg-type]
    lo, hi = _WATERFALL_LABEL_BOUNDS
    # Structural labels own 18–24px; ordinary_values is inapplicable (D52/D307).
    sizes["structural_values"] = lo
    typo = chart.typography
    if typo is not None and typo.mode == "adaptive":
        sizes["structural_values"] = min(hi, lo + 2)
    return sizes


def _resolve_waterfall_steps(
    steps: list[Any],
    formats: Mapping[str, NumberFormat],
    *,
    fmt_id: str,
) -> list[dict[str, Any]]:
    """Placement arithmetic only — authored totals stay authoritative (D307)."""
    level = Decimal(0)
    out: list[dict[str, Any]] = []
    for step in steps:
        role = step.role
        if role == "total":
            authored = Decimal(step.value)
            y0, y1 = Decimal(0), authored
            level = authored
            display_num = authored
            display_raw = step.value
            color_role = "total"
            sign = 0 if authored == 0 else (1 if authored > 0 else -1)
        elif role == "change":
            authored = Decimal(step.value)
            start = level
            level = level + authored
            y0, y1 = start, level
            display_num = authored
            display_raw = step.value
            color_role = "increase" if authored >= 0 else "decrease"
            sign = 0 if authored == 0 else (1 if authored > 0 else -1)
        else:  # computed_total
            y0, y1 = Decimal(0), level
            display_num = level
            # Keep canonical decimal text — never float-round (D70/D77/D307).
            display_raw = format(level, "f")
            color_role = "computed_total"
            sign = 0 if level == 0 else (1 if level > 0 else -1)
        fv = format_semantic_value(
            NumberValue(value=display_raw, format_id=fmt_id), formats
        )
        # Change direction chrome: keep sign in accessibility wording.
        accessible = fv.accessible
        if role == "change" and sign > 0 and not accessible.startswith("+"):
            accessible = f"increase {accessible}"
        elif role == "change" and sign < 0:
            accessible = f"decrease {accessible}"
        elif role == "computed_total":
            accessible = f"computed total {accessible}"
        elif role == "total":
            accessible = f"total {accessible}"
        out.append(
            {
                "category_id": step.category_id,
                "label": step.label,
                "short_label": step.short_label,
                "role": role,
                "authored_value": step.value,
                "display_value": display_raw,
                "display_numeric": display_num,
                "level": level,
                "y0": y0,
                "y1": y1,
                "color_role": color_role,
                "sign": sign,
                "visible": fv.visible,
                "accessible": accessible,
            }
        )
    return out


def _resolve_waterfall_domain(
    chart: WaterfallChartVisual, resolved: list[dict[str, Any]]
) -> dict[str, Any]:
    axis = chart.value_axes.primary
    levels: list[Decimal] = [Decimal(0)]
    for step in resolved:
        levels.append(Decimal(step["y0"]))
        levels.append(Decimal(step["y1"]))
        levels.append(Decimal(step["level"]))
    data_min = min(levels)
    data_max = max(levels)
    if axis.domain.kind == "fixed":
        return {
            "kind": "fixed",
            "min": axis.domain.min,
            "max": axis.domain.max,
            "ticks": list(axis.domain.ticks),
            "source_min": _plain_decimal(float(data_min)),
            "source_max": _plain_decimal(float(data_max)),
        }
    lo = Decimal(axis.domain.min) if axis.domain.min is not None else data_min
    hi = Decimal(axis.domain.max) if axis.domain.max is not None else data_max
    if lo > 0:
        lo = Decimal(0)
    if hi < 0:
        hi = Decimal(0)
    if lo == hi:
        lo -= Decimal("1")
        hi += Decimal("1")
    pad = (hi - lo) * Decimal("0.08")
    lo_f = Decimal(0) if lo == 0 else lo - pad
    hi_f = hi + pad
    if lo_f > 0:
        lo_f = Decimal(0)
    if hi_f < 0:
        hi_f = Decimal(0)
    target = axis.domain.target_ticks or 5
    ticks = _nice_ticks(float(lo_f), float(hi_f), target)
    if 0.0 not in ticks and ticks[0] <= 0 <= ticks[-1]:
        ticks = sorted(set(ticks + [0.0]))
    return {
        "kind": "generated",
        "min": _plain_decimal(ticks[0]),
        "max": _plain_decimal(ticks[-1]),
        "ticks": [_plain_decimal(t) for t in ticks],
        "source_min": _plain_decimal(float(data_min)),
        "source_max": _plain_decimal(float(data_max)),
    }


def _waterfall_semantic_table(
    chart: WaterfallChartVisual,
    resolved: list[dict[str, Any]],
    domain: dict[str, Any],
    formats: Mapping[str, NumberFormat],
    fmt: NumberFormat,
) -> dict[str, Any]:
    """D247 columns: step, role, authored/computed value, running level."""
    fmt_id = chart.value_axes.primary.format_id
    columns = [
        {"series_id": "role", "label": "Role"},
        {"series_id": "value", "label": "Value"},
        {"series_id": "level", "label": "Running level"},
    ]
    rows = []
    for step in resolved:
        role_vis = {
            "change": "Change",
            "total": "Total",
            "computed_total": "Computed total",
        }[step["role"]]
        if step["authored_value"] is None:
            val_vis = step["visible"]
            val_acc = step["accessible"]
            missing = False
        else:
            fv = format_semantic_value(
                NumberValue(value=step["authored_value"], format_id=fmt_id),
                formats,
            )
            val_vis, val_acc, missing = fv.visible, step["accessible"], False
        level_raw = (
            step["authored_value"]
            if step["role"] == "total" and step["authored_value"] is not None
            else format(Decimal(step["level"]), "f")
        )
        lv = format_semantic_value(
            NumberValue(value=level_raw, format_id=fmt_id),
            formats,
        )
        rows.append(
            {
                "category_id": step["category_id"],
                "label": step["label"],
                "cells": [
                    {
                        "series_id": "role",
                        "visible": role_vis,
                        "accessible": role_vis,
                        "missing": False,
                    },
                    {
                        "series_id": "value",
                        "visible": val_vis,
                        "accessible": val_acc,
                        "missing": missing,
                    },
                    {
                        "series_id": "level",
                        "visible": lv.visible,
                        "accessible": lv.accessible,
                        "missing": False,
                    },
                ],
            }
        )
    unit_words = {
        "usd": "US dollars",
        "percent": "percent",
        "percentage_points": "percentage points",
        "basis_points": "basis points",
    }.get(fmt.unit or "", "unitless")
    facts = [
        "Chart type: waterfall",
        "Series identity: step roles",
        f"Values in {unit_words}, {fmt.value_decimals} decimal places",
        f"Value domain from {domain['min']} to {domain['max']}",
        "Structural labels mandatory; ordinary value display inapplicable",
    ]
    if chart.heading:
        facts.insert(0, f"Chart: {chart.heading}")
    if chart.value_axes.primary.title:
        facts.append(f"Value axis title: {chart.value_axes.primary.title}")
    if chart.category_axis.title:
        facts.append(f"Category axis title: {chart.category_axis.title}")
    if fmt.scale_label:
        facts.append(f"Display scale: {fmt.scale_label}")
    for step in resolved:
        fact_level = (
            step["authored_value"]
            if step["role"] == "total" and step["authored_value"] is not None
            else format(Decimal(step["level"]), "f")
        )
        facts.append(
            f"Step {step['label']}: {step['role']} value {step['visible']} "
            f"level {fact_level}"
        )
    return {
        "columns": columns,
        "rows": rows,
        "facts": facts,
        "visible": False,
    }


def _resolve_series(
    data: ChartData, *, family: str = "line"
) -> list[dict[str, Any]]:
    defaults = resolve_series_colors(family, count=len(data.series))
    out: list[dict[str, Any]] = []
    for i, s in enumerate(data.series):
        if s.color is not None:
            color = resolve_color(s.color, role="series_identity")
        else:
            color = defaults[i]
        if family == "line":
            if s.style is not None:
                line_style, marker = s.style.line_style, s.style.marker
            else:
                line_style, marker = LINE_STYLE_PAIRS[i % len(LINE_STYLE_PAIRS)]
        else:
            line_style, marker = "solid", "circle"
        out.append(
            {
                "series_id": s.series_id,
                "name": s.name,
                "color": color,
                "line_style": line_style,
                "marker": marker,
                "values": list(s.values),
            }
        )
    return out


def _resolve_domain(
    chart: AxisChartVisual,
    data: ChartData,
    *,
    include_zero: bool = False,
    stack_extents: bool = False,
) -> dict[str, Any]:
    axis = chart.value_axes.primary
    finite: list[Decimal] = []
    for s in data.series:
        for v in s.values:
            if v is not None:
                finite.append(Decimal(v))
    if stack_extents:
        # Domain must cover completed signed stacks, not only segments (D83/D242).
        n = len(data.categories)
        for c_i in range(n):
            pos = Decimal(0)
            neg = Decimal(0)
            for s in data.series:
                raw = s.values[c_i]
                if raw is None:
                    continue
                dv = Decimal(raw)
                if dv > 0:
                    pos += dv
                elif dv < 0:
                    neg += dv
            finite.append(pos)
            finite.append(neg)
    if not finite:
        finite = [Decimal(0), Decimal(1)]
    data_min = min(finite)
    data_max = max(finite)
    leading = axis.leading_break
    if axis.domain.kind == "fixed":
        ticks = list(axis.domain.ticks)
        return {
            "kind": "fixed",
            "min": axis.domain.min,
            "max": axis.domain.max,
            "ticks": ticks,
        }
    # generated
    lo = Decimal(axis.domain.min) if axis.domain.min is not None else data_min
    hi = Decimal(axis.domain.max) if axis.domain.max is not None else data_max
    if leading is not None:
        # Visible domain starts at break target; source min retained for D106.
        lo = Decimal(leading.to)
        if hi <= lo:
            hi = lo + Decimal("1")
    elif include_zero:
        if lo > 0:
            lo = Decimal(0)
        if hi < 0:
            hi = Decimal(0)
    if lo == hi:
        lo -= Decimal("1")
        hi += Decimal("1")
    # headroom ~8% (label clearance D72)
    pad = (hi - lo) * Decimal("0.08")
    lo_f = lo if (include_zero and lo == 0) or leading is not None else lo - pad
    hi_f = hi + pad
    if include_zero and leading is None:
        if lo_f > 0:
            lo_f = Decimal(0)
        if hi_f < 0:
            hi_f = Decimal(0)
    target = axis.domain.target_ticks or 5
    ticks = _nice_ticks(float(lo_f), float(hi_f), target)
    source_min = float(data_min)
    source_max = float(data_max)
    if leading is not None:
        # First visible tick equals break target (D157/D230).
        br = float(Decimal(leading.to))
        ticks = [t for t in ticks if t >= br - 1e-12]
        if not ticks or abs(ticks[0] - br) > 1e-9:
            ticks = [br] + [t for t in ticks if t > br + 1e-12]
        if len(ticks) < 2:
            ticks.append(br + max(1.0, abs(br) * 0.25))
    if include_zero and leading is None and 0.0 not in ticks:
        # Keep zero when analytically inside span.
        if ticks[0] <= 0 <= ticks[-1]:
            ticks = sorted(set(ticks + [0.0]))
    return {
        "kind": "generated",
        "min": _plain_decimal(ticks[0]),
        "max": _plain_decimal(ticks[-1]),
        "ticks": [_plain_decimal(t) for t in ticks],
        "source_min": _plain_decimal(source_min),
        "source_max": _plain_decimal(source_max),
    }


def _bar_identity_strategy(
    chart: BarChartVisual, series_plans: list[dict[str, Any]]
) -> str:
    if chart.display is not None and chart.display.series_identity is not None:
        pol = chart.display.series_identity
        if pol == "pane_title":
            return "pane_title"
        if pol == "legend":
            return "legend"
    # Multi-series always complete legend; single-series one-item legend (D240).
    return "legend"


def _bar_slot_geometry(
    *,
    plot_w: float,
    plot_h: float,
    n_cat: int,
    n_ser: int,
    horizontal: bool,
    pad_l: float = 0.0,
    pad_t: float = 0.0,
) -> dict[str, Any]:
    """Renderer-owned bar thickness + pitch (D160). Absolute plot coords."""
    n_cat = max(1, n_cat)
    n_ser = max(1, n_ser)
    axis_span = plot_h if horizontal else plot_w
    pitch = axis_span / n_cat
    cat_gap = pitch * BAR_CATEGORY_GAP_RATIO
    inner = max(1.0, pitch - cat_gap)
    ser_gap = inner * BAR_SERIES_GAP_RATIO / max(1, n_ser)
    raw_thick = (inner - ser_gap * max(0, n_ser - 1)) / n_ser
    thick = max(BAR_MIN_THICKNESS, min(BAR_MAX_THICKNESS, raw_thick))
    cluster = n_ser * thick + max(0, n_ser - 1) * ser_gap
    slots: list[dict[str, Any]] = []
    ser_slot = cluster / n_ser
    for c_i in range(n_cat):
        base = c_i * pitch + (pitch - cluster) / 2
        origins = [
            base + s_i * ser_slot + (ser_slot - thick) / 2 for s_i in range(n_ser)
        ]
        if horizontal:
            # Categories top → bottom along Y.
            slots.append(
                {
                    "center": pad_t + c_i * pitch + pitch / 2,
                    "origins": [pad_t + o for o in origins],
                }
            )
        else:
            # Categories left → right along X.
            slots.append(
                {
                    "center": pad_l + c_i * pitch + pitch / 2,
                    "origins": [pad_l + o for o in origins],
                }
            )
    return {
        "thickness": thick,
        "category_pitch": pitch,
        "series_gap": ser_gap,
        "slots": slots,
        "horizontal": horizontal,
    }


def _place_stack_labels(
    bars: list[dict[str, Any]],
    series_plans: list[dict[str, Any]],
    stack_totals: list[dict[str, Any]],
    *,
    show_segments: bool,
    show_totals: bool,
    segment_px: int,
    total_px: int,
    plot: tuple[float, float, float, float],
) -> list[dict[str, Any]]:
    """Segment + total labels for stacked bars (D79/D242/D304). Never fit-drop."""
    placements: list[dict[str, Any]] = []
    series_by_id = {s["series_id"]: s for s in series_plans}
    navy = resolve_color("navy", role="text_on_light")
    white = resolve_color("white", role="text_on_dark")

    for b in bars:
        if b.get("missing") or not b.get("finite"):
            continue
        text = b["visible"]
        if not show_segments:
            placements.append(
                {
                    "series_id": b["series_id"],
                    "category_id": b["category_id"],
                    "kind": "segment",
                    "class": "suppressed",
                    "x": b["end_x"],
                    "y": b.get("mid_y", b["end_y"]),
                    "text": text,
                    "priority": "hidden_policy",
                }
            )
            continue
        # Prefer inside when tall enough AND white-on-fill contrast holds (D304).
        h = float(b["height"])
        w_est = max(20.0, len(text) * segment_px * 0.55)
        fill = series_by_id[b["series_id"]]["color"]
        contrast_ok = contrast_ratio(white, fill) >= 3.0
        inside_ok = (
            h >= segment_px + 6 and b.get("sign", 0) != 0 and contrast_ok
        )
        cx = b["end_x"]
        if inside_ok:
            placements.append(
                {
                    "series_id": b["series_id"],
                    "category_id": b["category_id"],
                    "kind": "segment",
                    "class": "inside",
                    "x": cx,
                    "y": b.get("mid_y", b["y"] + h / 2) + segment_px * 0.35,
                    "text": text,
                    "color": white,
                    "priority": "segment",
                }
            )
        else:
            # Outside + series connector; navy text (D79/D304).
            sign = b.get("sign", 0)
            if sign < 0:
                y = b["y"] + h + segment_px + 4
                cls = "outside_below"
            elif sign > 0:
                y = b["y"] - 4
                cls = "outside_above"
            else:
                y = b.get("end_y", b["y"]) - 4
                cls = "outside_zero"
            # Lateral nudge if label wider than bar.
            x = cx
            if w_est > b["width"]:
                x = cx + b["width"] / 2 + w_est / 2 + 6
                cls = "leader"
            placements.append(
                {
                    "series_id": b["series_id"],
                    "category_id": b["category_id"],
                    "kind": "segment",
                    "class": cls,
                    "x": x,
                    "y": y,
                    "text": text,
                    "color": navy,
                    "anchor_x": cx,
                    "anchor_y": b.get("mid_y", b["end_y"]),
                    "connector_color": series_by_id[b["series_id"]]["color"],
                    "priority": "segment",
                }
            )

    # D241/D299/D304: finite authored total replaces computed total labels for
    # that category only. D247 still keeps computed sides in stack_totals.
    authored_override = {
        t["category_id"]
        for t in stack_totals
        if t.get("source") == "authored"
        and not t.get("missing")
        and t.get("value") is not None
    }
    for t in stack_totals:
        if t.get("missing") or t.get("withheld"):
            # Withheld/missing stay in D106 only — no visual label.
            continue
        if t.get("source") == "computed" and t["category_id"] in authored_override:
            continue
        if not show_totals and t.get("source") != "authored":
            continue
        # Authored implies show; computed follows policy.
        text = t["visible"]
        placements.append(
            {
                "series_id": None,
                "category_id": t["category_id"],
                "kind": "stack_total",
                "class": f"total_{t['side']}",
                "x": t["x"],
                "y": t["y"],
                "text": text,
                "color": navy,
                "priority": "total",
                "source": t.get("source"),
                "side": t.get("side"),
            }
        )
    return placements


def _freeze_coverage_callout(
    chart: StackedBarChartVisual,
    formats: Mapping[str, NumberFormat],
    pad_l: float,
    pad_t: float,
    plot_w: float,
) -> Optional[dict[str, Any]]:
    cov = chart.coverage_callout
    if cov is None:
        return None
    if cov.format_id not in formats:
        return None
    fv = format_semantic_value(
        NumberValue(value=cov.value, format_id=cov.format_id), formats
    )
    # D50/D301 fixed chrome: value (26/700) then label/period (24/700); top exterior.
    y = max(22.0, pad_t - 30)
    x = pad_l + plot_w / 2
    return {
        "callout_id": cov.callout_id,
        "value_visible": fv.visible,
        "value_accessible": fv.accessible,
        "label": cov.label,
        "period": cov.period,
        "x": x,
        "y": y,
        "value_px": 26,
        "text_px": 24,
        "fact": (
            f"Coverage {cov.label}"
            + (f" ({cov.period})" if cov.period else "")
            + f": {fv.accessible}"
        ),
    }


def _place_bar_labels(
    bars: list[dict[str, Any]],
    series_plans: list[dict[str, Any]],
    *,
    show_values: bool,
    label_px: int,
    plot: tuple[float, float, float, float],
    horizontal: bool,
) -> list[dict[str, Any]]:
    """Outside-end ordinary bar values (D71–D73); first/last retained."""
    placements: list[dict[str, Any]] = []
    occupied: list[tuple[float, float, float, float]] = []
    finite_bars = [b for b in bars if b.get("finite") and not b.get("missing")]
    # Priority: first/last category per series, extrema, then authored order.
    by_series: dict[str, list[dict[str, Any]]] = {}
    for b in finite_bars:
        by_series.setdefault(b["series_id"], []).append(b)
    ordered: list[dict[str, Any]] = []
    for sp in series_plans:
        pts = by_series.get(sp["series_id"]) or []
        if not pts:
            continue
        for i, p in enumerate(pts):
            p = dict(p)
            if i == 0 or i == len(pts) - 1:
                p["_edge"] = True
                p["_rank"] = "edge"
            else:
                p["_rank"] = "coverage"
            ordered.append(p)
        # Extrema next
        nums = [(abs(p["numeric"]), p) for p in pts]
        nums.sort(key=lambda t: t[0], reverse=True)
        for _, p in nums[:2]:
            if not any(
                o["series_id"] == p["series_id"]
                and o["category_id"] == p["category_id"]
                for o in ordered
                if o.get("_rank") == "extrema"
            ):
                ep = dict(p)
                ep["_rank"] = "extrema"
                ordered.append(ep)
    # De-dupe preserving first rank assignment.
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, Any]] = []
    for p in ordered:
        key = (p["series_id"], p["category_id"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(p)

    for p in unique:
        if not show_values:
            placements.append(
                {
                    "series_id": p["series_id"],
                    "category_id": p["category_id"],
                    "kind": "value",
                    "class": "suppressed",
                    "x": p.get("end_x", p["x"]),
                    "y": p.get("end_y", p["y"]),
                    "text": p["visible"],
                    "priority": "hidden_policy",
                }
            )
            continue
        w = max(24.0, len(p["visible"]) * label_px * 0.55)
        h = float(label_px + 4)
        end_x = p.get("end_x", p["x"])
        end_y = p.get("end_y", p["y"])
        sign = p.get("sign", 1)
        if horizontal:
            # Beyond terminal edge in value direction (D71); zero just past baseline.
            if sign == 0:
                x = end_x + w / 2 + 6
                cls = "beyond_zero"
            elif sign < 0:
                x = end_x - w / 2 - 6
                cls = "beyond_neg"
            else:
                x = end_x + w / 2 + 6
                cls = "beyond_pos"
            y = end_y + label_px * 0.35
            box = (x - w / 2, y - h, x + w / 2, y)
        else:
            if sign == 0:
                # Zero label just above the zero baseline (D78/D240).
                x = end_x
                y = end_y - 4
                cls = "above_zero"
            elif sign < 0:
                x = end_x
                y = end_y + h + 4
                cls = "below"
            else:
                x = end_x
                y = end_y - 4
                cls = "above"
            box = (x - w / 2, y - h, x + w / 2, y)
        # Prefer in-plot labels; edges may extend slightly for outside values (D71).
        if not _fits(box, plot) and not p.get("_edge") and sign != 0:
            # Nudge inward once before collision handling.
            if horizontal:
                x = min(max(x, plot[0] + w / 2), plot[2] - w / 2)
            else:
                y = min(max(y, plot[1] + h), plot[3])
            box = (x - w / 2, y - h, x + w / 2, y)
        if _overlaps(box, occupied) and not p.get("_edge"):
            # Small lateral stagger then leader (D72).
            if horizontal:
                y2 = y + h + 2
                box2 = (box[0], y2 - h, box[2], y2)
                if not _overlaps(box2, occupied):
                    y, box, cls = y2, box2, "leader"
                else:
                    placements.append(
                        {
                            "series_id": p["series_id"],
                            "category_id": p["category_id"],
                            "kind": "value",
                            "class": "suppressed",
                            "x": end_x,
                            "y": end_y,
                            "text": p["visible"],
                            "priority": p.get("_rank", "coverage"),
                        }
                    )
                    continue
            else:
                x2 = x + (w * 0.35 if sign >= 0 else -w * 0.35)
                box2 = (x2 - w / 2, box[1], x2 + w / 2, box[3])
                if not _overlaps(box2, occupied):
                    x, box, cls = x2, box2, "leader"
                else:
                    placements.append(
                        {
                            "series_id": p["series_id"],
                            "category_id": p["category_id"],
                            "kind": "value",
                            "class": "suppressed",
                            "x": end_x,
                            "y": end_y,
                            "text": p["visible"],
                            "priority": p.get("_rank", "coverage"),
                        }
                    )
                    continue
        occupied.append(box)
        placements.append(
            {
                "series_id": p["series_id"],
                "category_id": p["category_id"],
                "kind": "value",
                "class": cls,
                "x": x,
                "y": y,
                "text": p["visible"],
                "anchor_x": end_x,
                "anchor_y": end_y,
                "priority": p.get("_rank", "coverage"),
            }
        )
    return placements


def _freeze_boxed_labels(
    chart: BarChartVisual,
    formats: Mapping[str, NumberFormat],
    bars: list[dict[str, Any]],
    cats: list[Any],
    role_sizes: dict[str, int],
    *,
    horizontal: bool,
) -> dict[str, Any]:
    aux = getattr(chart, "auxiliary_series", None) or []
    boxed = [a for a in aux if a.role == "boxed_label"]
    if not boxed:
        return {"placements": [], "labels": [], "facts": []}
    b = boxed[0]
    # format_id is validated at deck level; missing → leave for validate_handoff.
    if b.format_id not in formats:
        return {"placements": [], "labels": [], "facts": []}
    bar_by = {(bar["series_id"], bar["category_id"]): bar for bar in bars}
    # Boxed labels fit 12–24px (D52); clamp from ordinary/annotation roles.
    px = max(12, min(24, role_sizes.get("annotations", role_sizes["ordinary_values"])))
    placements: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []
    facts: list[str] = []
    for c_i, cat in enumerate(cats):
        raw = b.values[c_i]
        if raw is None:
            labels.append(
                {
                    "category_id": cat.category_id,
                    "value": None,
                    "visible": MISSING_VISIBLE,
                    "accessible": MISSING_ACCESSIBLE,
                    "missing": True,
                }
            )
            continue
        fv = format_semantic_value(
            NumberValue(value=raw, format_id=b.format_id), formats
        )
        bar = bar_by.get((b.target_series_id, cat.category_id))
        if bar is None or not bar.get("finite"):
            # Still a D106 fact; no paint when target bar missing.
            labels.append(
                {
                    "category_id": cat.category_id,
                    "value": raw,
                    "visible": fv.visible,
                    "accessible": fv.accessible,
                    "missing": False,
                }
            )
            continue
        tw = max(28.0, len(fv.visible) * px * 0.55 + 12)
        th = float(px + 10)
        if horizontal:
            x = bar["x"] + bar["width"] / 2
            y = bar["y"] + bar["height"] / 2
        else:
            # Inside bar when tall enough, else outside above/below (D52).
            if bar["height"] >= th + 4 and bar.get("sign", 1) >= 0:
                x = bar["x"] + bar["width"] / 2
                y = bar["y"] + bar["height"] / 2
            elif bar.get("sign", 1) < 0:
                x = bar["x"] + bar["width"] / 2
                y = bar["y"] + bar["height"] + th / 2 + 4
            else:
                x = bar["x"] + bar["width"] / 2
                y = bar["y"] - th / 2 - 4
        place = {
            "series_id": b.target_series_id,
            "category_id": cat.category_id,
            "kind": "boxed_label",
            "class": "boxed",
            "x": x,
            "y": y,
            "text": fv.visible,
            "box_w": tw,
            "box_h": th,
            "priority": "structural",
        }
        placements.append(place)
        labels.append(
            {
                "category_id": cat.category_id,
                "value": raw,
                "visible": fv.visible,
                "accessible": fv.accessible,
                "missing": False,
                "x": x,
                "y": y,
            }
        )
    facts.append(f"Boxed labels: {b.label} on series {b.target_series_id}")
    return {"placements": placements, "labels": labels, "facts": facts}


def _freeze_category_groups(
    chart: BarChartVisual,
    cats: list[Any],
    geom: dict[str, Any],
    pad_l: float,
    pad_t: float,
    plot_w: float,
    plot_h: float,
    *,
    horizontal: bool,
) -> list[dict[str, Any]]:
    groups = getattr(chart, "category_groups", None) or []
    if not groups:
        return []
    cat_pos = {c.category_id: i for i, c in enumerate(cats)}
    out: list[dict[str, Any]] = []
    for g in groups:
        idxs = [cat_pos[cid] for cid in g.category_ids]
        first, last = idxs[0], idxs[-1]
        s0 = geom["slots"][first]
        s1 = geom["slots"][last]
        if horizontal:
            y1 = s0["origins"][0]
            y2 = s1["origins"][-1] + geom["thickness"]
            x = pad_l + plot_w + 8
            out.append(
                {
                    "group_id": g.group_id,
                    "label": g.label,
                    "short_label": g.short_label,
                    "category_ids": list(g.category_ids),
                    "x1": x,
                    "y1": y1,
                    "x2": x,
                    "y2": y2,
                }
            )
        else:
            x1 = s0["origins"][0]
            x2 = s1["origins"][-1] + geom["thickness"]
            y = pad_t + plot_h + 36
            out.append(
                {
                    "group_id": g.group_id,
                    "label": g.label,
                    "short_label": g.short_label,
                    "category_ids": list(g.category_ids),
                    "x1": x1,
                    "y1": y,
                    "x2": x2,
                    "y2": y,
                }
            )
    return out


def _plain_decimal(value: float) -> str:
    """Canonical decimal text without scientific notation (D77/D291).

    ``:.6g`` switches to '1.25e+06' for |value| >= 1e6, which CanonicalDecimal
    rejects; format with fixed decimals and strip trailing zeros instead.
    """
    text = f"{value:.10f}".rstrip("0").rstrip(".")
    if text in ("", "-0"):
        return "0"
    return text


def _nice_ticks(lo: float, hi: float, target: int) -> list[float]:
    if hi <= lo:
        hi = lo + 1.0
    span = hi - lo
    raw = span / max(2, target - 1)
    exp = math.floor(math.log10(raw)) if raw > 0 else 0
    base = 10**exp
    step = base * 100
    for mult in (1, 2, 2.5, 5, 10, 20, 25, 50, 100):
        cand = base * mult
        if cand < raw * 0.8:
            continue
        c_start = math.floor(lo / cand) * cand
        c_end = math.ceil(hi / cand) * cand
        if round((c_end - c_start) / cand) + 1 <= 8:
            step = cand
            break
    start = math.floor(lo / step) * step
    end = math.ceil(hi / step) * step
    ticks: list[float] = []
    x = start
    # guard loop
    for _ in range(16):
        ticks.append(round(x, 10))
        if x >= end - step * 1e-9:
            break
        x += step
    if ticks[-1] < hi:
        ticks.append(round(end, 10))
    return ticks


def _place_point_labels(
    points: list[dict[str, Any]],
    series_plans: list[dict[str, Any]],
    *,
    show_values: bool,
    label_px: int,
    plot: tuple[float, float, float, float],
    identity: str = "endpoints",
) -> list[dict[str, Any]]:
    """Deterministic D7/D36/D53 placement; first/last never suppressed."""
    placements: list[dict[str, Any]] = []
    occupied: list[tuple[float, float, float, float]] = []
    by_series: dict[str, list[dict[str, Any]]] = {}
    for p in points:
        by_series.setdefault(p["series_id"], []).append(p)

    # Priority: first/last finite, extrema, even coverage (D36).
    ordered: list[dict[str, Any]] = []
    for sp in series_plans:
        pts = [p for p in by_series[sp["series_id"]] if p["finite"]]
        if not pts:
            continue
        ranked = _rank_points(pts)
        ordered.extend(ranked)

    for p in ordered:
        if not show_values:
            placements.append(
                {
                    "series_id": p["series_id"],
                    "category_id": p["category_id"],
                    "kind": "value",
                    "class": "suppressed",
                    "x": p["x"],
                    "y": p["y"],
                    "priority": "hidden_policy",
                }
            )
            continue
        w = max(24.0, len(p["visible"]) * label_px * 0.55)
        h = float(label_px + 4)
        chosen = None
        for cls in POINT_LABEL_CANDIDATES:
            x, y = _candidate_xy(p["x"], p["y"], cls, w, h)
            box = (x - w / 2, y - h, x + w / 2, y)
            if cls == "leader":
                box = (x - w / 2, y - h - 12, x + w / 2, y - 12)
                y = y - 12
            if _fits(box, plot) and not _overlaps(box, occupied):
                chosen = (cls, x, y, box)
                break
        is_edge = p.get("_edge")
        if chosen is None and is_edge:
            # First/last never suppress — force above even if tight.
            x, y = p["x"], p["y"] - LABEL_CLEAR - h / 2
            box = (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
            chosen = ("above", x, y, box)
        if chosen is None:
            placements.append(
                {
                    "series_id": p["series_id"],
                    "category_id": p["category_id"],
                    "kind": "value",
                    "class": "suppressed",
                    "x": p["x"],
                    "y": p["y"],
                    "priority": p.get("_rank", "coverage"),
                }
            )
            continue
        cls, x, y, box = chosen
        occupied.append(box)
        placements.append(
            {
                "series_id": p["series_id"],
                "category_id": p["category_id"],
                "kind": "value",
                "class": cls,
                "x": x,
                "y": y,
                "priority": p.get("_rank", "coverage"),
            }
        )

    # Endpoint identity labels only under complete-endpoint strategy (D15/D37).
    if identity == "endpoints":
        for sp in series_plans:
            pts = [p for p in by_series[sp["series_id"]] if p["finite"]]
            if not pts:
                continue
            last = pts[-1]
            placements.append(
                {
                    "series_id": sp["series_id"],
                    "category_id": last["category_id"],
                    "kind": "identity",
                    "class": "endpoint",
                    "x": last["x"] + MARKER_R + 8,
                    "y": last["y"] + label_px / 3,
                    "priority": "identity",
                }
            )
    return placements


def _rank_points(pts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not pts:
        return []
    first, last = pts[0], pts[-1]
    first = {**first, "_edge": True, "_rank": "first"}
    last = {**last, "_edge": True, "_rank": "last"}
    mids = pts[1:-1]
    if mids:
        nums = [(p, p["numeric"]) for p in mids]
        mn = min(nums, key=lambda t: t[1])[0]
        mx = max(nums, key=lambda t: t[1])[0]
        rest = []
        for p in mids:
            if p is mn:
                rest.append({**p, "_rank": "min"})
            elif p is mx:
                rest.append({**p, "_rank": "max"})
            else:
                rest.append({**p, "_rank": "coverage"})
        # even coverage: keep author order among coverage
        return [first] + ([last] if last is not first else []) + rest
    return [first] if first is last else [first, last]


def _candidate_xy(
    px: float, py: float, cls: str, w: float, h: float
) -> tuple[float, float]:
    if cls == "above":
        return px, py - LABEL_CLEAR - h / 2
    if cls == "below":
        return px, py + LABEL_CLEAR + h / 2
    if cls == "left":
        return px - LABEL_CLEAR - w / 2, py
    if cls == "right":
        return px + LABEL_CLEAR + w / 2, py
    # leader
    return px, py - LABEL_CLEAR - h / 2 - 10


def _fits(box: tuple[float, float, float, float], plot: tuple[float, float, float, float]) -> bool:
    x0, y0, x1, y1 = box
    pl, pt, pr, pb = plot
    # allow slight exterior for side candidates
    return x0 >= pl - 40 and x1 <= pr + 80 and y0 >= pt - 20 and y1 <= pb + 20


def _overlaps(
    box: tuple[float, float, float, float],
    occupied: list[tuple[float, float, float, float]],
) -> bool:
    a0, b0, a1, b1 = box
    for c0, d0, c1, d1 in occupied:
        if a0 < c1 and a1 > c0 and b0 < d1 and b1 > d0:
            return True
    return False


def _marker_svg(x: float, y: float, marker: str, color: str) -> str:
    r = MARKER_R
    c = _e(color)
    if marker == "square":
        return (
            f'<rect x="{x - r:.1f}" y="{y - r:.1f}" width="{2 * r}" height="{2 * r}" '
            f'fill="{c}" stroke="{c}"/>'
        )
    if marker == "triangle":
        return (
            f'<polygon points="{x:.1f},{y - r:.1f} {x + r:.1f},{y + r:.1f} '
            f'{x - r:.1f},{y + r:.1f}" fill="{c}" stroke="{c}"/>'
        )
    if marker == "diamond":
        return (
            f'<polygon points="{x:.1f},{y - r:.1f} {x + r:.1f},{y:.1f} '
            f'{x:.1f},{y + r:.1f} {x - r:.1f},{y:.1f}" fill="{c}" stroke="{c}"/>'
        )
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{c}" stroke="{c}"/>'


def _legend_html(plan: dict[str, Any]) -> str:
    items = []
    leg_px = plan["role_sizes"].get("legend", 16)
    identity = plan.get("identity_strategy")
    series_list = plan["series"]
    # Combo auto: bar legend only when line endpoints carry line identity (D244).
    if identity == "endpoints_and_bar_legend":
        series_list = [s for s in series_list if s.get("mark_type") == "bar"]
    for s in series_list:
        mark = s.get("mark_type")
        if mark == "bar" or (
            plan.get("chart_type") in ("grouped_bar", "horizontal_bar", "stacked_bar")
        ):
            swatch = (
                f'<svg width="28" height="12" aria-hidden="true">'
                f'<rect x="4" y="2" width="20" height="8" fill="{_e(s["color"])}"/>'
                f"</svg>"
            )
        else:
            # Swatch approximates line+marker pair (D99).
            dash = _DASHARRAY.get(s["line_style"]) or ""
            swatch = (
                f'<svg width="28" height="12" aria-hidden="true">'
                f'<line x1="0" y1="6" x2="28" y2="6" stroke="{_e(s["color"])}" '
                f'stroke-width="2"'
                f'{f" stroke-dasharray=\"{dash}\"" if dash else ""}/>'
                f'{_marker_svg(14, 6, s["marker"], s["color"])}'
                f"</svg>"
            )
        items.append(
            f'<li class="legend-item" data-series-id="{_e(s["series_id"])}" '
            f'style="font-size:{leg_px}px">'
            f"{swatch}"
            f'<span class="legend-label">{_e(s["name"])}</span></li>'
        )
    if not items:
        return ""
    return f'<ul class="chart-legend" aria-hidden="true">{"".join(items)}</ul>'


def _semantic_table(
    chart: AxisChartVisual,
    formats: Mapping[str, NumberFormat],
    series_plans: list[dict[str, Any]],
    domain: dict[str, Any],
    *,
    identity: str,
    scale_label: Optional[str],
    chart_type: str = "line",
    groups: Optional[list[dict[str, Any]]] = None,
    boxed: Optional[list[str]] = None,
    stack_totals: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    fmt_id = chart.value_axes.primary.format_id
    columns = [{"series_id": s["series_id"], "label": s["name"]} for s in series_plans]
    # D247 stacked: series columns then positive/negative computed totals + authored.
    if chart_type == "stacked_bar":
        columns.extend(
            [
                {"series_id": "_pos_total", "label": "Positive total"},
                {"series_id": "_neg_total", "label": "Negative total"},
            ]
        )
        if any(
            t.get("source") == "authored" for t in (stack_totals or [])
        ):
            columns.append(
                {"series_id": "_authored_total", "label": "Authored total"}
            )
    rows = []
    totals_by_cat: dict[str, dict[str, dict[str, Any]]] = {}
    for t in stack_totals or []:
        totals_by_cat.setdefault(t["category_id"], {})[t["side"]] = t
    for c_i, cat in enumerate(chart.chart_data.categories):
        cells = []
        for s_i, s in enumerate(chart.chart_data.series):
            raw = s.values[c_i]
            if raw is None:
                fv = format_semantic_value(MissingValue(), formats)
            else:
                fv = format_semantic_value(
                    NumberValue(value=raw, format_id=fmt_id), formats
                )
            cells.append(
                {
                    "series_id": s.series_id,
                    "visible": fv.visible,
                    "accessible": fv.accessible,
                    "missing": raw is None,
                }
            )
        if chart_type == "stacked_bar":
            sides = totals_by_cat.get(cat.category_id) or {}
            for side_key, col_id in (
                ("positive", "_pos_total"),
                ("negative", "_neg_total"),
                ("authored", "_authored_total"),
            ):
                if not any(c["series_id"] == col_id for c in columns):
                    continue
                t = sides.get(side_key)
                if t is None:
                    cells.append(
                        {
                            "series_id": col_id,
                            "visible": MISSING_VISIBLE,
                            "accessible": MISSING_ACCESSIBLE,
                            "missing": True,
                        }
                    )
                else:
                    cells.append(
                        {
                            "series_id": col_id,
                            "visible": t["visible"],
                            "accessible": t["accessible"],
                            "missing": bool(t.get("missing") or t.get("withheld")),
                        }
                    )
        rows.append(
            {
                "category_id": cat.category_id,
                "label": cat.label,
                "cells": cells,
            }
        )
    fmt = formats[fmt_id]
    unit_words = {
        "usd": "US dollars",
        "percent": "percent",
        "percentage_points": "percentage points",
        "basis_points": "basis points",
    }.get(fmt.unit or "", "unitless")
    type_words = {
        "line": "line trend",
        "grouped_bar": "grouped vertical bars",
        "horizontal_bar": "horizontal grouped bars",
        "stacked_bar": "sign-separated stacked vertical bars",
        "combo": "combo bar and line layers",
        "combo_grouped": "grouped combo bars with line layers",
        "combo_stacked": "stacked combo bars with line layers",
    }.get(chart_type, chart_type)
    facts = [
        f"Chart type: {type_words}",
        f"Series identity: {identity.replace('_', ' ')}",
        f"Values in {unit_words}, {fmt.value_decimals} decimal places",
        f"Value domain from {domain['min']} to {domain['max']}",
    ]
    if chart.heading:
        facts.insert(0, f"Chart: {chart.heading}")
    if chart.value_axes.primary.title:
        facts.append(f"Value axis title: {chart.value_axes.primary.title}")
    if chart.category_axis.title:
        facts.append(f"Category axis title: {chart.category_axis.title}")
    if scale_label:
        facts.append(f"Display scale: {scale_label}")
    if chart.value_axes.primary.leading_break:
        facts.append(
            f"Leading axis break omits values below "
            f"{chart.value_axes.primary.leading_break.to}"
        )
    for g in groups or []:
        members = ", ".join(g.get("category_ids") or [])
        facts.append(f"Category group {g['label']}: {members}")
    for fact in boxed or []:
        facts.append(fact)
    return {
        "columns": columns,
        "rows": rows,
        "facts": facts,
        "visible": False,
    }


def _chartjs_config(plan: dict[str, Any]) -> dict[str, Any]:
    """Settled Chart.js config — animation off, no gridlines (D63/D108)."""
    ctype = plan.get("chart_type", "line")
    if ctype == "waterfall":
        return _chartjs_waterfall_config(plan)
    if ctype == "combo":
        return _chartjs_combo_config(plan)
    if ctype in ("grouped_bar", "horizontal_bar", "stacked_bar"):
        return _chartjs_bar_config(plan)
    return _chartjs_line_config(plan)


def _chartjs_waterfall_config(plan: dict[str, Any]) -> dict[str, Any]:
    """Floating bars via [base, tip] pairs so Chart.js matches freeze (D160/D245)."""
    labels = [c["label"] for c in plan["categories"]]
    g = plan["geometry"]
    pitch = g.get("category_pitch") or 1.0
    thick = g.get("thickness") or BAR_MIN_THICKNESS
    category_pct = min(1.0, max(0.1, thick / pitch))
    bar_pct = 1.0
    data = []
    colors = []
    for bar in plan.get("bars") or []:
        # Chart.js bar [start, end] on the value axis.
        data.append([float(bar["y0"]), float(bar["y1"])])
        colors.append(bar["color"])
    d_min = float(Decimal(plan["domain"]["min"]))
    d_max = float(Decimal(plan["domain"]["max"]))
    return {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "label": "Waterfall",
                    "data": data,
                    "backgroundColor": colors,
                    "borderColor": colors,
                    "borderWidth": 0,
                    "barPercentage": bar_pct,
                    "categoryPercentage": category_pct,
                    "clip": False,
                    "indexAxis": "x",
                }
            ],
        },
        "options": {
            "indexAxis": "x",
            "animation": False,
            "responsive": False,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {"display": False},
                "tooltip": {"enabled": True},
            },
            "scales": {
                "x": {
                    "display": False,
                    "grid": {"display": False, "drawBorder": True},
                    "ticks": {
                        "font": {"size": plan["role_sizes"]["category_ticks"]},
                        "color": resolve_color("navy", role="text_on_light"),
                    },
                    "title": {
                        "display": bool(plan["category_axis"].get("title")),
                        "text": plan["category_axis"].get("title") or "",
                    },
                },
                "y": {
                    "display": False,
                    "min": d_min,
                    "max": d_max,
                    "grid": {"display": False, "drawBorder": True},
                    "stacked": False,
                    "ticks": {
                        "font": {"size": plan["role_sizes"]["value_ticks"]},
                        "color": resolve_color("navy", role="text_on_light"),
                    },
                    "title": {
                        "display": bool(plan["value_axis"].get("title")),
                        "text": plan["value_axis"].get("title") or "",
                    },
                },
            },
            "layout": {
                "padding": {
                    "left": g["pad_l"],
                    "right": g["pad_r"],
                    "top": g["pad_t"],
                    "bottom": g["pad_b"],
                }
            },
        },
        "v3": {
            "tick_labels": plan["tick_labels"],
            "domain_ticks": plan["domain"]["ticks"],
            "surface_id": plan["surface_id"],
            "identity_strategy": plan["identity_strategy"],
            "chart_type": "waterfall",
            "bars": [
                {
                    "series_id": b["series_id"],
                    "category_id": b["category_id"],
                    "role": b["role"],
                    "x": b["x"],
                    "y": b["y"],
                    "width": b["width"],
                    "height": b["height"],
                    "y0": b["y0"],
                    "y1": b["y1"],
                    "level": b["level"],
                }
                for b in plan.get("bars") or []
            ],
            "connectors": plan.get("connectors") or [],
            "thickness": g.get("thickness"),
        },
    }


def _chartjs_combo_config(plan: dict[str, Any]) -> dict[str, Any]:
    """Mixed bar+line Chart.js config; bars first so lines paint above (D244)."""
    labels = [c["label"] for c in plan["categories"]]
    stacked = bool(plan["geometry"].get("stacked")) or plan.get("bar_mode") == "stacked"
    g = plan["geometry"]
    n_bar = max(1, sum(1 for s in plan["series"] if s.get("mark_type") == "bar"))
    pitch = g.get("category_pitch") or 1.0
    thick = g.get("thickness") or BAR_MIN_THICKNESS
    if stacked:
        category_pct = min(1.0, max(0.1, thick / pitch))
        bar_pct = 1.0
    else:
        ser_gap = g.get("series_gap")
        if ser_gap is None:
            ser_gap = thick * BAR_SERIES_GAP_RATIO
        cluster = n_bar * thick + max(0, n_bar - 1) * ser_gap
        category_pct = min(1.0, max(0.1, cluster / pitch))
        slot = (cluster / n_bar) if n_bar else thick
        bar_pct = min(1.0, max(0.1, thick / slot)) if slot else 0.9

    datasets: list[dict[str, Any]] = []
    # Bars first (behind), then lines — Chart.js order / z.
    ordered = [s for s in plan["series"] if s.get("mark_type") == "bar"] + [
        s for s in plan["series"] if s.get("mark_type") == "line"
    ]
    for s in ordered:
        data = [None if v is None else float(Decimal(v)) for v in s["values"]]
        if s.get("mark_type") == "bar":
            ds: dict[str, Any] = {
                "type": "bar",
                "label": s["name"],
                "data": data,
                "backgroundColor": s["color"],
                "borderColor": s["color"],
                "borderWidth": 0,
                "barPercentage": bar_pct,
                "categoryPercentage": category_pct,
                "clip": False,
                "order": 2,
                "yAxisID": "y",
            }
            if stacked:
                ds["stack"] = "combo"
            else:
                ds["base"] = 0.0
            datasets.append(ds)
        else:
            border_dash = {
                "solid": [],
                "dashed": [8, 6],
                "dotted": [2, 4],
                "dash_dot": [10, 4, 2, 4],
            }[s["line_style"]]
            point_style = {
                "circle": "circle",
                "square": "rect",
                "triangle": "triangle",
                "diamond": "rectRot",
            }[s["marker"]]
            y_id = "y1" if s.get("axis_key") == "secondary" else "y"
            datasets.append(
                {
                    "type": "line",
                    "label": s["name"],
                    "data": data,
                    "borderColor": s["color"],
                    "backgroundColor": s["color"],
                    "borderWidth": 2.5,
                    "borderDash": border_dash,
                    "pointStyle": point_style,
                    "pointRadius": MARKER_R,
                    "pointHoverRadius": MARKER_R,
                    "spanGaps": False,
                    "tension": 0,
                    "fill": False,
                    "clip": False,
                    "order": 1,
                    "yAxisID": y_id,
                }
            )

    d_min = float(Decimal(plan["domain"]["min"]))
    d_max = float(Decimal(plan["domain"]["max"]))
    scales: dict[str, Any] = {
        "x": {
            "display": False,
            "grid": {"display": False, "drawBorder": True},
            "stacked": stacked,
            "ticks": {
                "font": {"size": plan["role_sizes"]["category_ticks"]},
                "color": resolve_color("navy", role="text_on_light"),
            },
            "title": {
                "display": bool(plan["category_axis"].get("title")),
                "text": plan["category_axis"].get("title") or "",
            },
        },
        "y": {
            "display": False,
            "position": "left",
            "min": d_min,
            "max": d_max,
            "grid": {"display": False, "drawBorder": True},
            "stacked": stacked,
            "ticks": {
                "font": {"size": plan["role_sizes"]["value_ticks"]},
                "color": resolve_color("navy", role="text_on_light"),
            },
            "title": {
                "display": bool(plan["value_axis"].get("title")),
                "text": plan["value_axis"].get("title") or "",
            },
        },
    }
    sec = plan.get("secondary_value_axis")
    sec_dom = plan.get("secondary_domain")
    if sec is not None and sec_dom is not None:
        scales["y1"] = {
            "display": False,
            "position": "right",
            "min": float(Decimal(sec_dom["min"])),
            "max": float(Decimal(sec_dom["max"])),
            "grid": {"display": False, "drawBorder": False},
            "stacked": False,
            "ticks": {
                "font": {"size": plan["role_sizes"]["value_ticks"]},
                "color": resolve_color("navy", role="text_on_light"),
            },
            "title": {
                "display": bool(sec.get("title")),
                "text": sec.get("title") or "",
            },
        }
    return {
        "type": "bar",  # mixed; per-dataset type overrides
        "data": {"labels": labels, "datasets": datasets},
        "options": {
            "animation": False,
            "responsive": False,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {"display": False},
                "tooltip": {"enabled": True},
            },
            "scales": scales,
            "layout": {
                "padding": {
                    "left": g["pad_l"],
                    "right": g["pad_r"],
                    "top": g["pad_t"],
                    "bottom": g["pad_b"],
                }
            },
        },
        "v3": {
            "tick_labels": plan["tick_labels"],
            "domain_ticks": plan["domain"]["ticks"],
            "surface_id": plan["surface_id"],
            "identity_strategy": plan["identity_strategy"],
            "chart_type": "combo",
            "bar_mode": plan.get("bar_mode"),
            "stacked": stacked,
            "bars": [
                {
                    "series_id": b["series_id"],
                    "category_id": b["category_id"],
                    "x": b["x"],
                    "y": b["y"],
                    "width": b["width"],
                    "height": b["height"],
                    "missing": b.get("missing", False),
                    "stack_base": b.get("stack_base"),
                    "stack_top": b.get("stack_top"),
                    "sign": b.get("sign"),
                }
                for b in plan.get("bars") or []
            ],
            "thickness": g.get("thickness"),
            "secondary_domain": sec_dom,
        },
    }


def _chartjs_line_config(plan: dict[str, Any]) -> dict[str, Any]:
    labels = [c["label"] for c in plan["categories"]]
    datasets = []
    for s in plan["series"]:
        data = []
        for v in s["values"]:
            data.append(None if v is None else float(Decimal(v)))
        border_dash = {
            "solid": [],
            "dashed": [8, 6],
            "dotted": [2, 4],
            "dash_dot": [10, 4, 2, 4],
        }[s["line_style"]]
        point_style = {
            "circle": "circle",
            "square": "rect",
            "triangle": "triangle",
            "diamond": "rectRot",
        }[s["marker"]]
        datasets.append(
            {
                "label": s["name"],
                "data": data,
                "borderColor": s["color"],
                "backgroundColor": s["color"],
                "borderWidth": 2.5,
                "borderDash": border_dash,
                "pointStyle": point_style,
                "pointRadius": MARKER_R,
                "pointHoverRadius": MARKER_R,
                "spanGaps": False,
                "tension": 0,
                "fill": False,
                "clip": False,
            }
        )
    g = plan["geometry"]
    y_min = float(Decimal(plan["domain"]["min"]))
    y_max = float(Decimal(plan["domain"]["max"]))
    return {
        "type": "line",
        "data": {"labels": labels, "datasets": datasets},
        "options": {
            "animation": False,
            "responsive": False,
            "maintainAspectRatio": False,
            "plugins": {
                # HTML owns legend; frozen SVG overlay owns labels (D248/D53).
                "legend": {"display": False},
                "tooltip": {"enabled": True},
            },
            "scales": {
                "x": {
                    "display": False,
                    "grid": {"display": False, "drawBorder": True},
                    "ticks": {
                        "font": {"size": plan["role_sizes"]["category_ticks"]},
                        "color": resolve_color("navy", role="text_on_light"),
                    },
                    "title": {
                        "display": bool(plan["category_axis"].get("title")),
                        "text": plan["category_axis"].get("title") or "",
                    },
                },
                "y": {
                    "display": False,
                    "min": y_min,
                    "max": y_max,
                    "grid": {"display": False, "drawBorder": True},
                    "ticks": {
                        "font": {"size": plan["role_sizes"]["value_ticks"]},
                        "color": resolve_color("navy", role="text_on_light"),
                        "callback": None,  # formatted client-side via labels map
                    },
                    "title": {
                        "display": bool(plan["value_axis"].get("title")),
                        "text": plan["value_axis"].get("title") or "",
                    },
                },
            },
            "layout": {
                "padding": {
                    "left": g["pad_l"],
                    "right": g["pad_r"],
                    "top": g["pad_t"],
                    "bottom": g["pad_b"],
                }
            },
        },
        "v3": {
            "tick_labels": plan["tick_labels"],
            "domain_ticks": plan["domain"]["ticks"],
            "surface_id": plan["surface_id"],
            "identity_strategy": plan["identity_strategy"],
        },
    }


# ---------------------------------------------------------------------------
# Heatmap (D163/D246/D247/D308) — native HTML only, no canvas/SVG painter
# ---------------------------------------------------------------------------


def freeze_heatmap(
    chart: HeatmapVisual,
    formats: Mapping[str, NumberFormat],
    *,
    box_w: int = PLOT_W + PAD_L + PAD_R,
    box_h: int | None = None,
    colored: bool = True,
    table_floor: int = 18,
) -> dict[str, Any]:
    """Build one frozen native-heatmap plan (D69/D246/D308)."""
    table = chart.table_data
    fmt_id = chart.shared_format_id
    fmt = formats[fmt_id]
    columns = list(table.columns)
    rows = list(table.rows)
    col_ids = [c.column_id for c in columns]
    table_sid = table.surface_id

    finite: list[Decimal] = []
    for row in rows:
        for cid in col_ids:
            cell = row.cells[cid]
            if getattr(cell, "type", None) == "number":
                finite.append(Decimal(cell.value))

    if chart.scale.mode == "fixed":
        lo = Decimal(chart.scale.min)
        hi = Decimal(chart.scale.max)
        equal = False
    else:
        lo = min(finite)
        hi = max(finite)
        equal = lo == hi

    cells: list[list[dict[str, Any]]] = []
    cells_vis: list[list[str]] = []
    cells_acc: list[list[str]] = []
    for row in rows:
        vis_row: list[str] = []
        acc_row: list[str] = []
        cell_row: list[dict[str, Any]] = []
        for cid in col_ids:
            cell = row.cells[cid]
            fv = format_semantic_value(cell, formats)
            entry: dict[str, Any] = {
                "visible": fv.visible,
                "accessible": fv.accessible,
                "role": fv.role,
                "missing": fv.role == "missing",
                "fill": None,
                "ink": None,
                "t": None,
            }
            if fv.role == "number" and colored:
                val = Decimal(cell.value)
                t = _heatmap_t(val, lo, hi, equal=equal)
                fill = _heatmap_fill(t)
                ink = _heatmap_ink(fill)
                entry.update({"fill": fill, "ink": ink, "t": t, "value": cell.value})
            cell_row.append(entry)
            vis_row.append(fv.visible)
            acc_row.append(fv.accessible)
        cells.append(cell_row)
        cells_vis.append(vis_row)
        cells_acc.append(acc_row)

    # Scale key samples: min / mid / max (or one shared value when equal).
    key_stops: list[dict[str, Any]] = []
    if colored and finite:
        if equal:
            mid_vis = format_semantic_value(
                NumberValue(value=format(lo, "f"), format_id=fmt_id), formats
            ).visible
            fill = _heatmap_fill(Decimal("0.5"))
            key_stops.append(
                {
                    "label": mid_vis,
                    "fill": fill,
                    "ink": _heatmap_ink(fill),
                    "role": "shared",
                }
            )
        else:
            mid = (lo + hi) / 2
            for role, val, t in (
                ("min", lo, Decimal(0)),
                ("mid", mid, Decimal("0.5")),
                ("max", hi, Decimal(1)),
            ):
                # Prefer an authored finite cell label when it matches the stop.
                vis = format_semantic_value(
                    NumberValue(value=format(val, "f"), format_id=fmt_id), formats
                ).visible
                fill = _heatmap_fill(t)
                key_stops.append(
                    {
                        "label": vis,
                        "fill": fill,
                        "ink": _heatmap_ink(fill),
                        "role": role,
                    }
                )

    header_full = [table.stub_header.label] + [c.label for c in columns]
    header_short = [
        table.stub_header.short_label or table.stub_header.label
    ] + [c.short_label or c.label for c in columns]
    row_labels_full = [r.label for r in rows]
    row_labels_short = [r.short_label or r.label for r in rows]

    scale_label = fmt.scale_label
    unit_note = _heatmap_unit_note(fmt)
    all_texts = (
        header_full
        + header_short
        + row_labels_full
        + row_labels_short
        + [v for row in cells_vis for v in row]
        + [s["label"] for s in key_stops]
        + ([scale_label] if scale_label else [])
        + ([unit_note] if unit_note else [])
        + ([MISSING_VISIBLE, MISSING_ACCESSIBLE] if any(
            c["missing"] for row in cells for c in row
        ) else [])
    )
    if chart.heading:
        all_texts.append(chart.heading)
    if chart.subtitle:
        all_texts.append(chart.subtitle)

    # Geometry is the native table itself — view_h is fitted later in plan.
    return {
        "surface_id": chart.surface_id,
        "table_surface_id": table_sid,
        "chart_type": "heatmap",
        "heading": chart.heading,
        "subtitle": chart.subtitle,
        "colored": bool(colored and finite),
        "format_id": fmt_id,
        "scale": {
            "mode": chart.scale.mode,
            "min": format(lo, "f"),
            "max": format(hi, "f"),
            "equal": equal,
            "key_stops": key_stops,
            "scale_label": scale_label,
            "unit_note": unit_note,
            "missing_visible": MISSING_VISIBLE,
            "missing_accessible": MISSING_ACCESSIBLE,
        },
        "col_ids": col_ids,
        "row_ids": [r.row_id for r in rows],
        "n_cols": len(col_ids),
        "n_rows": len(rows),
        "header_full": header_full,
        "header_short": header_short,
        "row_labels_full": row_labels_full,
        "row_labels_short": row_labels_short,
        "cells": cells,
        "cells_vis": cells_vis,
        "cells_acc": cells_acc,
        "all_texts": all_texts,
        "display_headers": list(header_full),
        "display_row_labels": list(row_labels_full),
        "col_widths": [],
        "short_label_used": False,
        "ellipsized": False,
        "role_sizes": {"table": table_floor},
        "geometry": {
            "view_w": box_w,
            "view_h": box_h if box_h is not None else 400,
        },
        "identity_strategy": None,
        "placements": [],
        "gridlines": False,
    }


def paint_heatmap_html(
    plan: dict[str, Any],
    *,
    plan_attrs: str = "",
) -> list[str]:
    """Emit one visible native heatmap table + scale key (D246/D247/D308)."""
    chart_sid = plan["surface_id"]
    # D255/D308: table DOM uses the nested table surface_id when distinct.
    table_sid = plan.get("table_surface_id") or chart_sid
    px = plan.get("role_sizes", {}).get("table", 18)
    style = f' style="font-size:{int(px)}px"' if px else ""
    out: list[str] = []
    out.append(
        f'<div class="chart-body heatmap-body" data-chart-surface="{_e(chart_sid)}" '
        f'data-chart-type="heatmap" {plan_attrs}>'
    )
    if plan.get("heading"):
        out.append(
            f'<div class="band-title chart-pane-title">'
            f"<span>{_e(plan['heading'])}</span>"
        )
        if plan.get("subtitle"):
            out.append(
                f'<span class="chart-pane-subtitle">{_e(plan["subtitle"])}</span>'
            )
        out.append("</div>")

    headers = list(plan["display_headers"])
    row_labels = list(plan["display_row_labels"])
    full_headers = list(plan["header_full"])
    full_row_labels = list(plan["row_labels_full"])
    widths = list(plan.get("col_widths") or [])
    col_ids = list(plan["col_ids"])
    row_ids = list(plan["row_ids"])
    stub_hid = f"{table_sid}-h-stub"
    leaf_hids = [f"{table_sid}-h-{cid}" for cid in col_ids]
    colored = bool(plan.get("colored"))

    out.append(
        f'<table class="data-table heatmap-table"{style} '
        f'id="{_e(table_sid)}-table" data-table-surface="{_e(table_sid)}" '
        f'data-heatmap-colored="{"true" if colored else "false"}">'
    )
    if widths:
        out.append("<colgroup>")
        for w in widths:
            out.append(f'<col style="width:{int(w)}px"/>')
        out.append("</colgroup>")
    out.append("<thead><tr>")
    out.append(
        f'<th id="{_e(stub_hid)}" scope="col" '
        f'class="band-table-header align-left stub" '
        f'title="{_e(full_headers[0])}">{_e(headers[0])}</th>'
    )
    for i, hid in enumerate(leaf_hids):
        out.append(
            f'<th id="{_e(hid)}" scope="col" '
            f'class="band-table-header align-right" '
            f'title="{_e(full_headers[i + 1])}">{_e(headers[i + 1])}</th>'
        )
    out.append("</tr></thead><tbody>")

    for r_i, rid_raw in enumerate(row_ids):
        out.append("<tr>")
        rid = f"{table_sid}-r-{rid_raw}"
        out.append(
            f'<th id="{_e(rid)}" scope="row" class="stub align-left" '
            f'title="{_e(full_row_labels[r_i])}">{_e(row_labels[r_i])}</th>'
        )
        for c_i, cid in enumerate(col_ids):
            cell = plan["cells"][r_i][c_i]
            visible = cell["visible"]
            accessible = cell["accessible"]
            hrefs = f"{rid} {leaf_hids[c_i]}"
            aria = (
                f' aria-label="{_e(accessible)}"'
                if accessible != visible
                else ""
            )
            fill = cell.get("fill") if colored else None
            ink = cell.get("ink") if colored else None
            style_bits: list[str] = []
            if fill:
                style_bits.append(f"background-color:{fill}")
            if ink:
                style_bits.append(f"color:{ink}")
            cell_style = f' style="{";".join(style_bits)}"' if style_bits else ""
            miss_cls = " heatmap-missing" if cell.get("missing") else ""
            out.append(
                f'<td headers="{_e(hrefs)}" '
                f'class="align-right num{miss_cls}"{aria}{cell_style}>'
                f"{_e(visible)}</td>"
            )
        out.append("</tr>")
    out.append("</tbody></table>")

    # Mandatory scale key when finite colored data exists (D163/D246/D308).
    scale = plan.get("scale") or {}
    stops = scale.get("key_stops") or []
    if colored and stops:
        out.append(
            f'<div class="heatmap-scale-key"{style} '
            f'role="group" aria-label="Color scale">'
        )
        for stop in stops:
            out.append(
                f'<span class="heatmap-scale-stop" '
                f'style="background-color:{stop["fill"]};color:{stop["ink"]}">'
                f'{_e(stop["label"])}</span>'
            )
        notes: list[str] = []
        if scale.get("unit_note"):
            notes.append(scale["unit_note"])
        if scale.get("scale_label"):
            notes.append(scale["scale_label"])
        notes.append(f"Missing: {scale.get('missing_visible', MISSING_VISIBLE)}")
        out.append(
            f'<span class="heatmap-scale-note">{_e(" · ".join(notes))}</span>'
        )
        out.append("</div>")
    out.append("</div>")
    return out


def _heatmap_t(
    value: Decimal, lo: Decimal, hi: Decimal, *, equal: bool
) -> Decimal:
    if equal:
        return Decimal("0.5")
    span = hi - lo
    if span == 0:
        return Decimal("0.5")
    t = (value - lo) / span
    if t < 0:
        return Decimal(0)
    if t > 1:
        return Decimal(1)
    return t


def _heatmap_fill(t: Decimal) -> str:
    """Monotonic light→primary-blue sequential (D163)."""
    tt = float(t)
    r = int(round(_HEAT_LIGHT[0] + (_HEAT_PRIMARY[0] - _HEAT_LIGHT[0]) * tt))
    g = int(round(_HEAT_LIGHT[1] + (_HEAT_PRIMARY[1] - _HEAT_LIGHT[1]) * tt))
    b = int(round(_HEAT_LIGHT[2] + (_HEAT_PRIMARY[2] - _HEAT_LIGHT[2]) * tt))
    return f"#{r:02x}{g:02x}{b:02x}"


def _heatmap_ink(fill_hex: str) -> str:
    """Contrast-safe navy/white text on the fill (D246/D308).

    White only for dark fills (relative L <= 0.18); navy otherwise.
    Navy reaches WCAG AA 4.5:1 near L >= 0.236; white only near L <= 0.183.
    """
    h = fill_hex.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))

    def lin(c: int) -> float:
        x = c / 255.0
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4

    L = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
    return _HEAT_WHITE if L <= 0.18 else _HEAT_NAVY


def _heatmap_unit_note(fmt: NumberFormat) -> str | None:
    unit = fmt.unit
    if unit is None:
        return None
    return {
        "usd": "USD",
        "percent": "Percent",
        "percentage_points": "Percentage points",
        "basis_points": "Basis points",
    }.get(unit)


def _chartjs_bar_config(plan: dict[str, Any]) -> dict[str, Any]:
    """Grouped / horizontal / stacked bar Chart.js config (D160/D242)."""
    labels = [c["label"] for c in plan["categories"]]
    horizontal = bool(plan["geometry"].get("horizontal"))
    stacked = bool(plan["geometry"].get("stacked")) or plan.get("chart_type") == "stacked_bar"
    g = plan["geometry"]
    n_ser = max(1, len(plan["series"]))
    # Mirror freeze thickness/gap → Chart.js category/bar percentages (D160).
    pitch = g.get("category_pitch") or 1.0
    thick = g.get("thickness") or BAR_MIN_THICKNESS
    if stacked:
        # One bar per category; thickness is the full cluster.
        category_pct = min(1.0, max(0.1, thick / pitch))
        bar_pct = 1.0
    else:
        ser_gap = g.get("series_gap")
        if ser_gap is None:
            ser_gap = thick * BAR_SERIES_GAP_RATIO
        cluster = n_ser * thick + max(0, n_ser - 1) * ser_gap
        category_pct = min(1.0, max(0.1, cluster / pitch))
        slot = (cluster / n_ser) if n_ser else thick
        bar_pct = min(1.0, max(0.1, thick / slot)) if slot else 0.9
    datasets = []
    for s in plan["series"]:
        data = [None if v is None else float(Decimal(v)) for v in s["values"]]
        ds: dict[str, Any] = {
            "label": s["name"],
            "data": data,
            "backgroundColor": s["color"],
            "borderColor": s["color"],
            "borderWidth": 0,
            "barPercentage": bar_pct,
            "categoryPercentage": category_pct,
            "clip": False,
        }
        if stacked:
            # Chart.js stacks + and − independently when stack id is shared.
            ds["stack"] = "stack"
        datasets.append(ds)
    d_min = float(Decimal(plan["domain"]["min"]))
    d_max = float(Decimal(plan["domain"]["max"]))
    leading = plan["value_axis"].get("leading_break")
    vis_min = float(Decimal(leading)) if leading is not None else d_min
    vis_max = d_max
    value_scale = {
        "display": False,
        "min": vis_min,
        "max": vis_max,
        "grid": {"display": False, "drawBorder": True},
        "stacked": stacked,
        "ticks": {
            "font": {"size": plan["role_sizes"]["value_ticks"]},
            "color": resolve_color("navy", role="text_on_light"),
        },
        "title": {
            "display": bool(plan["value_axis"].get("title")),
            "text": plan["value_axis"].get("title") or "",
        },
    }
    cat_scale = {
        "display": False,
        "grid": {"display": False, "drawBorder": True},
        "stacked": stacked,
        "ticks": {
            "font": {"size": plan["role_sizes"]["category_ticks"]},
            "color": resolve_color("navy", role="text_on_light"),
        },
        "title": {
            "display": bool(plan["category_axis"].get("title")),
            "text": plan["category_axis"].get("title") or "",
        },
    }
    if horizontal:
        scales = {"x": value_scale, "y": cat_scale}
        index_axis = "y"
    else:
        scales = {"x": cat_scale, "y": value_scale}
        index_axis = "x"
    base_v = vis_min if leading is not None else 0.0
    for ds in datasets:
        ds["indexAxis"] = index_axis
        if not stacked:
            ds["base"] = base_v
    return {
        "type": "bar",
        "data": {"labels": labels, "datasets": datasets},
        "options": {
            "indexAxis": index_axis,
            "animation": False,
            "responsive": False,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {"display": False},
                "tooltip": {"enabled": True},
            },
            "scales": scales,
            "layout": {
                "padding": {
                    "left": g["pad_l"],
                    "right": g["pad_r"],
                    "top": g["pad_t"],
                    "bottom": g["pad_b"],
                }
            },
        },
        "v3": {
            "tick_labels": plan["tick_labels"],
            "domain_ticks": plan["domain"]["ticks"],
            "surface_id": plan["surface_id"],
            "identity_strategy": plan["identity_strategy"],
            "stacked": stacked,
            "bars": [
                {
                    "series_id": b["series_id"],
                    "category_id": b["category_id"],
                    "x": b["x"],
                    "y": b["y"],
                    "width": b["width"],
                    "height": b["height"],
                    "missing": b.get("missing", False),
                    "stack_base": b.get("stack_base"),
                    "stack_top": b.get("stack_top"),
                    "sign": b.get("sign"),
                }
                for b in plan.get("bars") or []
            ],
            "thickness": g.get("thickness"),
            "leading_break": leading,
        },
    }
