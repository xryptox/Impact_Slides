"""Chart freeze + painters: line tracer + native heatmap (D163/D239/D246–D248/D302/D308)."""
from __future__ import annotations

import html
import json
import math
from decimal import Decimal
from typing import Any, Mapping, Optional

from .format import MISSING_ACCESSIBLE, MISSING_VISIBLE, format_semantic_value
from .models import (
    LINE_STYLE_PAIRS,
    ChartData,
    HeatmapVisual,
    LineChartVisual,
    MissingValue,
    NumberFormat,
    NumberValue,
)
from .theme import (
    chart_js_tokens,
    line_style_keys,
    marker_keys,
    resolve_color,
    resolve_series_colors,
)

# Heatmap sequential light → primary blue (D163/D246/D308); RGB endpoints only.
_HEAT_LIGHT = (232, 242, 252)  # soft sky wash on white
_HEAT_PRIMARY = tuple(
    int(resolve_color("primary_blue", role="fill").lstrip("#")[i : i + 2], 16)
    for i in (0, 2, 4)
)
_HEAT_NAVY = resolve_color("navy", role="text_on_light")
_HEAT_WHITE = resolve_color("white", role="text_on_dark")
HEATMAP_TABLE_FLOOR = 18
HEATMAP_TABLE_CEIL = 24

# Plot geometry on the 1920 content width (D68 stage; single_chart body region).
PLOT_W = 1400
PLOT_H = 620
PAD_L = 88
PAD_R = 160  # exterior identity/context lane
PAD_T = 28
PAD_B = 64
MARKER_R = 5
LABEL_CLEAR = MARKER_R + 4  # D53/D62 clearance
POINT_LABEL_CANDIDATES = ("above", "below", "left", "right", "leader")

# Chart typography floors / ceilings (D294).
_ROLE_BOUNDS: dict[str, tuple[int, int]] = {
    "category_ticks": (14, 24),
    "value_ticks": (14, 28),
    "ordinary_values": (14, 32),
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
    plot_w = max(200, min(PLOT_W, box_w - PAD_L - PAD_R))
    plot_h = max(160, min(PLOT_H, box_h - PAD_T - PAD_B - 40))
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


def paint_line_chart_html(
    plan: dict[str, Any],
    *,
    plan_attrs: str = "",
    svg_only: bool = False,
) -> list[str]:
    """Emit Chart.js canvas + noscript SVG + one D247 semantic table."""
    sid = plan["surface_id"]
    out: list[str] = []
    out.append(
        f'<div class="chart-body" data-chart-surface="{_e(sid)}" '
        f'data-chart-type="line" {plan_attrs}>'
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
    if legend_html and plan["identity_strategy"] == "legend":
        out.append(legend_html)

    g = plan["geometry"]
    vw, vh = g["view_w"], g["view_h"]
    svg = paint_line_chart_svg(plan)
    table_html = paint_semantic_table(plan)

    # Label/axis chrome SVG shares frozen plan with both painters (D248/D53).
    chrome_svg = paint_line_chart_svg(plan, marks=False)
    marks_svg = paint_line_chart_svg(plan, marks=True, chrome=False)
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


def paint_line_chart_svg(
    plan: dict[str, Any],
    *,
    marks: bool = True,
    chrome: bool = True,
) -> str:
    """No-JS SVG painter consuming the frozen plan (D57/D248).

    ``marks`` = series paths/markers; ``chrome`` = axes/ticks/labels/identities.
    Chart.js path overlays chrome SVG on the canvas for placement parity.
    """
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


def _ordinary_values_show(chart: LineChartVisual) -> bool:
    if chart.display is None or chart.display.ordinary_values is None:
        return True
    return chart.display.ordinary_values == "show"


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


def _role_sizes(chart: LineChartVisual) -> dict[str, int]:
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


def _resolve_series(data: ChartData) -> list[dict[str, Any]]:
    defaults = resolve_series_colors("line", count=len(data.series))
    out: list[dict[str, Any]] = []
    for i, s in enumerate(data.series):
        if s.color is not None:
            color = resolve_color(s.color, role="series_identity")
        else:
            color = defaults[i]
        if s.style is not None:
            line_style, marker = s.style.line_style, s.style.marker
        else:
            line_style, marker = LINE_STYLE_PAIRS[i % len(LINE_STYLE_PAIRS)]
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


def _resolve_domain(chart: LineChartVisual, data: ChartData) -> dict[str, Any]:
    axis = chart.value_axes.primary
    finite: list[Decimal] = []
    for s in data.series:
        for v in s.values:
            if v is not None:
                finite.append(Decimal(v))
    if not finite:
        finite = [Decimal(0), Decimal(1)]
    data_min = min(finite)
    data_max = max(finite)
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
    if lo == hi:
        lo -= Decimal("1")
        hi += Decimal("1")
    # headroom ~5%
    pad = (hi - lo) * Decimal("0.08")
    lo_f = lo - pad
    hi_f = hi + pad
    target = axis.domain.target_ticks or 5
    ticks = _nice_ticks(float(lo_f), float(hi_f), target)
    return {
        "kind": "generated",
        "min": _plain_decimal(ticks[0]),
        "max": _plain_decimal(ticks[-1]),
        "ticks": [_plain_decimal(t) for t in ticks],
    }


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
    for s in plan["series"]:
        # Swatch approximates line+marker pair (D99).
        dash = _DASHARRAY.get(s["line_style"]) or ""
        items.append(
            f'<li class="legend-item" data-series-id="{_e(s["series_id"])}" '
            f'style="font-size:{leg_px}px">'
            f'<svg width="28" height="12" aria-hidden="true">'
            f'<line x1="0" y1="6" x2="28" y2="6" stroke="{_e(s["color"])}" '
            f'stroke-width="2"'
            f'{f" stroke-dasharray=\"{dash}\"" if dash else ""}/>'
            f'{_marker_svg(14, 6, s["marker"], s["color"])}'
            f"</svg>"
            f'<span class="legend-label">{_e(s["name"])}</span></li>'
        )
    return f'<ul class="chart-legend" aria-hidden="true">{"".join(items)}</ul>'


def _semantic_table(
    chart: LineChartVisual,
    formats: Mapping[str, NumberFormat],
    series_plans: list[dict[str, Any]],
    domain: dict[str, Any],
    *,
    identity: str,
    scale_label: Optional[str],
) -> dict[str, Any]:
    fmt_id = chart.value_axes.primary.format_id
    columns = [{"series_id": s["series_id"], "label": s["name"]} for s in series_plans]
    rows = []
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
    facts = [
        "Chart type: line trend",
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
    return {
        "columns": columns,
        "rows": rows,
        "facts": facts,
        "visible": False,
    }


def _chartjs_config(plan: dict[str, Any]) -> dict[str, Any]:
    """Settled Chart.js config — animation off, no gridlines (D63/D108)."""
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
) -> dict[str, Any]:
    """Build one frozen native-heatmap plan (D69/D246/D308)."""
    table = chart.table_data
    fmt_id = chart.shared_format_id
    fmt = formats[fmt_id]
    columns = list(table.columns)
    rows = list(table.rows)
    col_ids = [c.column_id for c in columns]

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
                NumberValue(value=str(lo), format_id=fmt_id), formats
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
                    NumberValue(value=str(val), format_id=fmt_id), formats
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
        "chart_type": "heatmap",
        "heading": chart.heading,
        "subtitle": chart.subtitle,
        "colored": bool(colored and finite),
        "format_id": fmt_id,
        "scale": {
            "mode": chart.scale.mode,
            "min": str(lo),
            "max": str(hi),
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
        "role_sizes": {"table": HEATMAP_TABLE_FLOOR},
        "geometry": {
            "view_w": box_w,
            "view_h": box_h if box_h is not None else 400,
        },
        # Line-chart fields absent on heatmap (painters/readiness branch on type).
        "identity_strategy": None,
        "placements": [],
        "series": [],
        "points": [],
        "categories": [],
        "gridlines": False,
        "semantic_table": {
            "surface_id": chart.surface_id,
            "stub": table.stub_header.label,
            "columns": [
                {"column_id": c.column_id, "label": c.label} for c in columns
            ],
            "rows": [
                {
                    "row_id": r.row_id,
                    "label": r.label,
                    "cells": [
                        {
                            "column_id": cid,
                            "visible": cells[ri][ci]["visible"],
                            "accessible": cells[ri][ci]["accessible"],
                            "missing": cells[ri][ci]["missing"],
                        }
                        for ci, cid in enumerate(col_ids)
                    ],
                }
                for ri, r in enumerate(rows)
            ],
        },
    }


def paint_heatmap_html(
    plan: dict[str, Any],
    *,
    plan_attrs: str = "",
) -> list[str]:
    """Emit one visible native heatmap table + scale key (D246/D247/D308)."""
    sid = plan["surface_id"]
    px = plan.get("role_sizes", {}).get("table", HEATMAP_TABLE_FLOOR)
    style = f' style="font-size:{int(px)}px"' if px else ""
    out: list[str] = []
    out.append(
        f'<div class="chart-body heatmap-body" data-chart-surface="{_e(sid)}" '
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
    stub_hid = f"{sid}-h-stub"
    leaf_hids = [f"{sid}-h-{cid}" for cid in col_ids]
    colored = bool(plan.get("colored"))

    out.append(
        f'<table class="data-table heatmap-table"{style} '
        f'id="{_e(sid)}-table" data-table-surface="{_e(sid)}" '
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
        rid = f"{sid}-r-{rid_raw}"
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
    """Contrast-safe navy/white text on the fill (D246/D308)."""
    h = fill_hex.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    # Relative luminance (sRGB) — navy on light, white on dark blue.
    def lin(c: int) -> float:
        x = c / 255.0
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4

    L = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
    return _HEAT_NAVY if L > 0.45 else _HEAT_WHITE


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
