"""Line and combo chart SVG painters."""
from __future__ import annotations

from typing import Any, Mapping
from ..strip import esc, strip_eids

from .format import _fmt_unit, _series_colors
from .geometry import chart_geometry
from .bars import _bar_matrix
from .core import _chart_config, _steps
from .auto_typography import compute_auto_plan_for_slide, svg_auto_axis_view, svg_label_transform
from .typography import (
    estimate_label_box,
    resolve_typography,
    suppress_colliding_labels,
    _warn,
)



def _line_data(slide: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Parse line chart data from steps_or_data.

    Accepts list of dicts: [{"label": "Q1'25", "value": 8}, ...]
    Also tolerates [label, value] pairs and "label: value" strings.
    """
    raw = _steps(slide)
    points: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict):
            label = str(item.get("label") or item.get("x") or "")
            try:
                value = float(str(item.get("value") or item.get("y") or 0).replace("%", "").replace(",", "").replace("$", ""))
            except (ValueError, TypeError):
                continue
            pt: dict[str, Any] = {"label": label, "value": value}
            if item.get("short_label") is not None:
                pt["short_label"] = item["short_label"]
            # Multi-series keys
            for k, v in item.items():
                if k.startswith("series_") and k != "series_1":
                    try:
                        pt[k] = float(str(v).replace("%", "").replace(",", "").replace("$", ""))
                    except (ValueError, TypeError):
                        pass
            points.append(pt)
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            try:
                value = float(str(item[1]).replace("%", "").replace(",", "").replace("$", ""))
            except (ValueError, TypeError):
                continue
            points.append({"label": str(item[0]), "value": value})
        elif isinstance(item, str) and ":" in item:
            a, _, b = item.partition(":")
            try:
                value = float(b.replace("%", "").replace(",", "").replace("$", "").strip())
            except ValueError:
                continue
            points.append({"label": a.strip(), "value": value})
    return points



# ---------------------------------------------------------------------------
# Combo chart (bar + line overlay, internal SVG)
# ---------------------------------------------------------------------------


def _combo_bar_data(
    slide: Mapping[str, Any],
) -> tuple[list[str], list[str], list[list[float | None]], list[str | None]]:
    """Parse combo bar data into (labels, series, rows, point_colors).

    Reuses the shared bar matrix parser (dict multi/single-series and
    list-of-lists). String ``"label: value"`` rows are normalized first.
    """
    raw = list(_steps(slide))
    # Normalize "label: value" strings so _bar_matrix can consume them.
    normalized: list[Any] = []
    for item in raw:
        if isinstance(item, str) and ":" in item:
            a, _, b = item.partition(":")
            try:
                v = float(b.replace("%", "").replace(",", "").replace("$", "").strip())
            except ValueError:
                continue
            normalized.append({"label": a.strip(), "value": v})
        else:
            normalized.append(item)
    if not normalized:
        return [], [], [], []
    # Temporarily present normalized steps via a shallow slide copy.
    slide_view = dict(slide)
    vs = dict(slide.get("visual_spec") or {})
    pv = dict(vs.get("primary_visual") or {})
    pv["steps_or_data"] = normalized
    vs["primary_visual"] = pv
    slide_view["visual_spec"] = vs
    if "steps_or_data" in slide_view:
        slide_view["steps_or_data"] = normalized
    return _bar_matrix(slide_view)



def _combo_line_data(slide: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Parse line overlay data from visual_spec.line_overlay."""
    vs = slide.get("visual_spec") or {}
    if not isinstance(vs, dict):
        return []
    overlay = vs.get("line_overlay") or {}
    if not isinstance(overlay, dict):
        return []
    raw = overlay.get("data") or []
    points: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict):
            label = str(item.get("label") or "")
            try:
                v = float(str(item.get("value") or 0).replace("%", "").replace(",", "").replace("$", ""))
            except (ValueError, TypeError):
                continue
            points.append({"label": label, "value": v})
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            try:
                v = float(str(item[1]).replace("%", "").replace(",", "").replace("$", ""))
            except (ValueError, TypeError):
                continue
            points.append({"label": str(item[0]), "value": v})
    return points



def _build_line_chart_svg(slide: Mapping[str, Any]) -> str:
    """Build an SVG line chart for the given slide.

    Single-series: solid navy line with circle data points and data labels.
    Uses viewBox 0 0 900 480 for stage containment.
    """
    points = _line_data(slide)
    if not points:
        return '<p class="chart-empty">No line chart data</p>'

    cfg = _chart_config(slide)
    typo = resolve_typography(cfg)
    y_tick_fs = (
        int(typo["y_tick_font_size"]) if typo.get("y_tick_font_size_set") else 14
    )
    y_tick_wt = "700" if typo.get("y_tick_font_size_set") else "600"
    x_tick_fs = (
        int(typo["x_tick_font_size"]) if typo.get("x_tick_font_size_set") else 14
    )
    dl_fs_primary = (
        int(typo["datalabel_font_size"]) if typo.get("datalabel_font_size_set") else 14
    )
    dl_fs_secondary = (
        int(typo["datalabel_font_size"]) if typo.get("datalabel_font_size_set") else 12
    )
    dl_set = bool(typo.get("datalabel_font_size_set"))
    geom = chart_geometry("line_chart", n=len(points))
    W, H = geom["width"], geom["height"]
    pad_l, pad_r, pad_t, pad_b = geom["pad_l"], geom["pad_r"], 40, 60

    values = [p["value"] for p in points]
    # Collect multi-series values for Y scale
    series_keys: list[str] = []
    for p in points:
        for k in p:
            if k.startswith("series_") and k not in series_keys:
                series_keys.append(k)
    for k in series_keys:
        values.extend(p[k] for p in points if k in p)

    y_max = cfg.get("y_axis_max")
    if y_max is None:
        raw_max = max(values) if values else 10
        # Round up to next nice number
        if raw_max <= 5:
            y_max = 5
        elif raw_max <= 10:
            y_max = int(raw_max) + 2
        elif raw_max <= 20:
            y_max = 20
        elif raw_max <= 50:
            y_max = int(raw_max) + 5
        else:
            y_max = int(raw_max * 1.15)
    y_max = float(y_max)
    y_min = float(cfg.get("y_axis_min", 0))

    y_ticks = cfg.get("y_axis_ticks")
    if y_ticks is None:
        # Auto-generate ~5 ticks
        step = (y_max - y_min) / 4
        if step >= 5:
            step = int(step)
        y_ticks = [y_min + i * step for i in range(5)]
    y_ticks = [float(t) for t in y_ticks]

    y_unit = cfg.get("y_axis_unit", "%")
    y_label = cfg.get("y_axis_label", "")

    def _fmtu(v: float) -> str:
        return _fmt_unit(v, y_unit, cfg.get("y_axis_unit_position", "suffix"))

    plot_w = W - pad_l - pad_r
    plot_h = H - pad_t - pad_b
    n = len(points)

    def x_pos(i: int) -> float:
        if n <= 1:
            return pad_l + plot_w / 2
        return pad_l + (i / (n - 1)) * plot_w

    def y_pos(v: float) -> float:
        rng = y_max - y_min
        if rng == 0:
            return pad_t + plot_h / 2
        return pad_t + plot_h - ((v - y_min) / rng) * plot_h

    parts: list[str] = [
        f'<svg class="chart-svg line-chart" viewBox="0 0 {W} {H}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;height:auto">',
        # Marker def for potential future use
        '<defs></defs>',
    ]

    auto_plan = compute_auto_plan_for_slide(
        slide, "line_chart", host_w=W, host_h=H, chart_cfg=cfg
    )
    if auto_plan is not None:
        x_tick_fs = auto_plan.x_tick_font_size
        y_tick_fs = auto_plan.y_tick_font_size
        y_tick_wt = "700"
        if auto_plan.datalabel_font_size_set:
            dl_fs_primary = auto_plan.datalabel_font_size
            dl_fs_secondary = auto_plan.datalabel_font_size
            dl_set = True
    label_lines, value_ticks = svg_auto_axis_view(
        auto_plan, labels=[str(p["label"]) for p in points], ticks=y_ticks, format_tick=_fmtu
    )
    # Y-axis tick labels only — plot gridlines default off (#152).
    for tick, tick_label in value_ticks:
        ty = y_pos(tick)
        parts.append(
            f'<text x="{pad_l - 10}" y="{ty + 5:.1f}" text-anchor="end" '
            f'fill="var(--navy, #00175a)" font-size="{y_tick_fs}" font-weight="{y_tick_wt}" '
            f'font-family="var(--font-body, sans-serif)">{esc(tick_label)}</text>'
        )

    # Y-axis line
    parts.append(
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{H - pad_b}" '
        f'stroke="var(--navy, #00175a)" stroke-width="1"/>'
    )

    # X-axis line
    parts.append(
        f'<line x1="{pad_l}" y1="{H - pad_b}" x2="{W - pad_r}" y2="{H - pad_b}" '
        f'stroke="var(--navy, #00175a)" stroke-width="1"/>'
    )

    # X-axis labels
    for i, p in enumerate(points):
        lines = label_lines[i] if i < len(label_lines) else [str(p["label"])]
        for line_i, line in enumerate(lines):
            parts.append(
                f'<text class="auto-x-label" data-auto-label-index="{i}" '
                f'x="{x_pos(i):.1f}" y="{H - pad_b + 25 + line_i * x_tick_fs}"'
                f'{svg_label_transform(auto_plan, x_pos(i), H - pad_b + 25 + line_i * x_tick_fs)} text-anchor="middle" '
                f'fill="var(--navy, #00175a)" font-size="{x_tick_fs}" font-weight="600" '
                f'font-family="var(--font-body, sans-serif)">{esc(line)}</text>'
            )

    # Y-axis label (rotated)
    if y_label:
        parts.append(
            f'<text x="20" y="{pad_t + plot_h / 2:.0f}" text-anchor="middle" '
            f'transform="rotate(-90 20 {pad_t + plot_h / 2:.0f})" '
            f'fill="var(--navy, #00175a)" font-size="13" '
            f'font-family="var(--font-body, sans-serif)">{esc(y_label)}</text>'
        )

    # -- Series definitions -----------------------------------------------
    # series_keys was collected above; build full series list
    all_series: list[dict[str, Any]] = [
        {"key": "value", "color": "var(--navy, #00175a)", "dash": "", "width": 3},
    ]
    series_names = cfg.get("series_names", [])
    series_styles = cfg.get("series_styles", [])
    for si, sk in enumerate(series_keys):
        idx = si + 1  # series_2 is index 1 in all_series
        if idx == 1:
            color = "var(--ink-muted, #63666a)"
            dash = 'stroke-dasharray="8,4"'
            width = 2
        else:
            color = "var(--navy, #00175a)"
            dash = ""
            width = 2
        # Allow override from config (series_styles[0] is primary, [1] is series_2, ...)
        if idx < len(series_styles) and series_styles[idx] == "solid":
            dash = ""
        all_series.append({"key": sk, "color": color, "dash": dash, "width": width})

    # Per-series color override from chart_config.series_colors (indexed by
    # series position: 0 = primary, 1 = series_2, ...)
    custom_colors = cfg.get("series_colors")
    if isinstance(custom_colors, (list, tuple)):
        for ci, entry in enumerate(all_series):
            if ci < len(custom_colors) and custom_colors[ci]:
                entry["color"] = str(custom_colors[ci])

    # -- Draw each series --------------------------------------------------
    for s_entry in all_series:
        sk = s_entry["key"]
        pts_for_series = [
            (i, p[sk]) for i, p in enumerate(points) if sk in p
        ]
        if not pts_for_series:
            continue
        line_pts = " ".join(
            f"{x_pos(i):.1f},{y_pos(v):.1f}" for i, v in pts_for_series
        )
        dash_attr = f' {s_entry["dash"]}' if s_entry["dash"] else ""
        parts.append(
            f'<polyline points="{line_pts}" fill="none" '
            f'stroke="{s_entry["color"]}" stroke-width="{s_entry["width"]}"'
            f'{dash_attr} stroke-linejoin="round" stroke-linecap="round"/>'
        )
        # Data points
        for i, v in pts_for_series:
            cx, cy = x_pos(i), y_pos(v)
            parts.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" '
                f'fill="{s_entry["color"]}"/>'
            )

    # -- Data labels ------------------------------------------------------
    # 2-series: per-point side selection — the higher line's label goes
    # above its point, the lower line's below — so labels never collide
    # when series converge or cross (PDF earnings-deck convention).
    # 3+ series keeps fixed sides (primary above, others below).
    two_series = len(all_series) == 2
    label_items: list[dict] = []
    label_markup: list[str] = []
    for i, p in enumerate(points):
        cx, cy = x_pos(i), y_pos(p["value"])
        above = True
        if two_series:
            sk2 = all_series[1]["key"]
            if sk2 in p:
                above = p["value"] >= p[sk2]
        ly = cy - 12 if above else cy + 18
        # First point sits ON the y-axis line — anchor its label start-side
        # so the text clears the axis instead of straddling it (#39).
        l_anchor, l_x = ("start", cx + 4) if i == 0 else ("middle", cx)
        txt = _fmtu(p["value"])
        label_items.append(
            {
                "series": 0,
                "category": i,
                "label": txt,
                "box": estimate_label_box(
                    txt, x=l_x, y=ly, font_size=dl_fs_primary, anchor=l_anchor
                ),
            }
        )
        label_markup.append(
            f'<text x="{l_x:.1f}" y="{ly:.1f}" text-anchor="{l_anchor}" '
            f'fill="var(--navy, #00175a)" font-size="{dl_fs_primary}" font-weight="600" '
            f'font-family="var(--font-body, sans-serif)">{esc(txt)}</text>'
        )

    # Data labels for secondary series
    if len(all_series) > 1:
        for s_i, sk_entry in enumerate(all_series[1:], start=1):
            sk = sk_entry["key"]
            for i, p in enumerate(points):
                if sk not in p:
                    continue
                cx, cy = x_pos(i), y_pos(p[sk])
                above = False
                if two_series:
                    above = p[sk] > p["value"]
                ly = cy - 12 if above else cy + 18
                l_anchor, l_x = ("start", cx + 4) if i == 0 else ("middle", cx)
                txt = _fmtu(p[sk])
                label_items.append(
                    {
                        "series": s_i,
                        "category": i,
                        "label": txt,
                        "box": estimate_label_box(
                            txt, x=l_x, y=ly, font_size=dl_fs_secondary, anchor=l_anchor
                        ),
                    }
                )
                label_markup.append(
                    f'<text x="{l_x:.1f}" y="{ly:.1f}" text-anchor="{l_anchor}" '
                    f'fill="var(--ink-muted, #63666a)" font-size="{dl_fs_secondary}" '
                    f'font-family="var(--font-body, sans-serif)">{esc(txt)}</text>'
                )

    if auto_plan is not None and auto_plan.datalabels_suppressed:
        pass
    elif dl_set and label_items:
        suppressed, details = suppress_colliding_labels(label_items)
        keep = set(range(len(label_items))) - set(suppressed)
        for i in sorted(keep):
            parts.append(label_markup[i])
        if suppressed:
            _warn(
                f"svg datalabel suppressed count={len(suppressed)} "
                + "; ".join(
                    f"series={d['series']} category={d['category']} label={d['label']!r}"
                    for d in details
                )
            )
    else:
        parts.extend(label_markup)

    # -- Legend -------------------------------------------------------------
    if len(all_series) > 1 and series_names:
        legend_x = W - pad_r - 10
        legend_y = pad_t + 10
        for li, s_entry in enumerate(all_series):
            name = series_names[li] if li < len(series_names) else f"Series {li + 1}"
            ly = legend_y + li * 22
            dash_attr = f' {s_entry["dash"]}' if s_entry["dash"] else ""
            parts.append(
                f'<line x1="{legend_x - 60}" y1="{ly}" x2="{legend_x - 30}" y2="{ly}" '
                f'stroke="{s_entry["color"]}" stroke-width="{s_entry["width"]}"'
                f'{dash_attr}/>'
            )
            parts.append(
                f'<text x="{legend_x - 20}" y="{ly + 4}" text-anchor="start" '
                f'fill="var(--ink, #53565a)" font-size="12" '
                f'font-family="var(--font-body, sans-serif)">{esc(name)}</text>'
            )

    # -- Annotation callout --------------------------------------------------
    annotation = cfg.get("annotation") or (slide.get("visual_spec") or {}).get("annotation")
    if isinstance(annotation, dict) and annotation.get("text"):
        # Fail closed (T9): unreadable x/y fall back to the default anchor.
        try:
            ax = float(annotation.get("x", W * 0.25))
            ay = float(annotation.get("y", H * 0.2))
        except (TypeError, ValueError):
            ax, ay = W * 0.25, H * 0.2
        a_text = str(annotation["text"])
        # Accept both real newlines and escaped \n sequences
        lines = a_text.replace("\\n", "\n").split("\n")
        box_w = max(len(l) for l in lines) * 7.5 + 20
        box_h = len(lines) * 18 + 16
        parts.append(
            f'<rect x="{ax - box_w/2:.0f}" y="{ay - box_h/2:.0f}" '
            f'width="{box_w:.0f}" height="{box_h:.0f}" rx="4" '
            f'fill="var(--panel, #eef0f0)" '
            f'stroke="var(--navy, #00175a)" stroke-width="1" '
            f'stroke-dasharray="4,3"/>'
        )
        for li, line in enumerate(lines):
            parts.append(
                f'<text x="{ax:.0f}" y="{ay + (li - len(lines)/2 + 0.5) * 18 + 5:.0f}" '
                f'text-anchor="middle" fill="var(--navy, #00175a)" font-size="13" '
                f'font-family="var(--font-body, sans-serif)">{esc(line)}</text>'
            )

    parts.append("</svg>")
    return "".join(parts)



def _build_combo_chart_svg(slide: Mapping[str, Any]) -> str:
    """Build a combo chart: bars + line overlay in a single SVG."""
    bar_labels, bar_series, bar_rows, bar_colors = _combo_bar_data(slide)
    line_points = _combo_line_data(slide)
    if not bar_rows:
        return '<p class="chart-empty">No combo chart data</p>'
    stacked = len(bar_series) > 1
    # Per-category totals drive the bar axis (single-series rows have 1 cell)
    bar_totals = [sum(v for v in row if v is not None and v > 0) for row in bar_rows]

    vs = slide.get("visual_spec") or {}
    overlay_cfg = vs.get("line_overlay") or {}
    overlay_color = overlay_cfg.get("color", "var(--navy, #00175a)")
    overlay_label = overlay_cfg.get("label", "")
    overlay_style = overlay_cfg.get("style", "solid")

    cfg = _chart_config(slide)
    typo = resolve_typography(cfg)
    y_tick_fs = (
        int(typo["y_tick_font_size"]) if typo.get("y_tick_font_size_set") else 14
    )
    y_tick_wt = "700" if typo.get("y_tick_font_size_set") else "600"
    x_tick_fs = (
        int(typo["x_tick_font_size"]) if typo.get("x_tick_font_size_set") else 14
    )
    geom = chart_geometry("combo_chart", has_overlay=bool(line_points))
    W, H = geom["width"], geom["height"]
    pad_l, pad_r, pad_t, pad_b = geom["pad_l"], geom["pad_r"], 56 if stacked else 40, 60

    bar_max = float(cfg.get("y_axis_max", max(bar_totals) * 1.15 if bar_totals else 10))
    bar_min = 0.0

    line_values = [p["value"] for p in line_points] if line_points else []
    line_max = float(overlay_cfg.get("y_axis_max", max(line_values) * 1.15 if line_values else 10))
    line_min = float(overlay_cfg.get("y_axis_min", 0))
    use_dual_axis = bool(line_points) and overlay_cfg.get("dual_axis", True)

    plot_w = W - pad_l - pad_r
    plot_h = H - pad_t - pad_b
    n_bars = len(bar_rows)

    def bar_y(v: float) -> float:
        rng = bar_max - bar_min
        if rng == 0:
            return pad_t + plot_h / 2
        return pad_t + plot_h - ((v - bar_min) / rng) * plot_h

    def line_y(v: float) -> float:
        if use_dual_axis:
            rng = line_max - line_min
            if rng == 0:
                return pad_t + plot_h / 2
            return pad_t + plot_h - ((v - line_min) / rng) * plot_h
        return bar_y(v)

    bar_slot = plot_w / max(n_bars, 1)
    bar_w = bar_slot * 0.6
    bar_unit = cfg.get("y_axis_unit", "")
    bar_unit_pos = cfg.get("y_axis_unit_position", "suffix")

    def _fmtb(v: float) -> str:
        return _fmt_unit(v, bar_unit, bar_unit_pos)

    parts: list[str] = [
        f'<svg class="chart-svg combo-chart" viewBox="0 0 {W} {H}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;height:auto">',
    ]

    auto_plan = compute_auto_plan_for_slide(
        slide, "combo_chart", host_w=W, host_h=H, chart_cfg=cfg
    )
    if auto_plan is not None:
        x_tick_fs = auto_plan.x_tick_font_size
        y_tick_fs = auto_plan.y_tick_font_size
        y_tick_wt = "700"
    label_lines, _value_ticks = svg_auto_axis_view(
        auto_plan, labels=bar_labels, ticks=[], format_tick=lambda _tick: ""
    )
    # Y-axis tick labels only (bar axis) — plot gridlines default off (#152).
    bar_ticks = cfg.get("y_axis_ticks")
    if bar_ticks is None:
        step = bar_max / 4
        if step >= 5:
            step = int(step)
        bar_ticks = [bar_min + i * step for i in range(5)]
    for tick in bar_ticks:
        tick = float(tick)
        tick_label = _fmtb(tick)
        ty = bar_y(tick)
        parts.append(
            f'<text x="{pad_l - 10}" y="{ty + 5:.1f}" text-anchor="end" '
            f'fill="var(--navy, #00175a)" font-size="{y_tick_fs}" font-weight="{y_tick_wt}" '
            f'font-family="var(--font-body, sans-serif)">{esc(tick_label)}</text>'
        )

    # Left Y-axis
    parts.append(
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{H - pad_b}" '
        f'stroke="var(--navy, #00175a)" stroke-width="1"/>'
    )

    # Right Y-axis (dual axis)
    if use_dual_axis and line_points:
        parts.append(
            f'<line x1="{W - pad_r}" y1="{pad_t}" x2="{W - pad_r}" y2="{H - pad_b}" '
            f'stroke="var(--navy, #00175a)" stroke-width="1"/>'
        )
        line_ticks = overlay_cfg.get("y_axis_ticks")
        if line_ticks is None:
            step = (line_max - line_min) / 4
            if step >= 5:
                step = int(step)
            line_ticks = [line_min + i * step for i in range(5)]
        line_unit = overlay_cfg.get("y_axis_unit", "")
        for tick in line_ticks:
            tick = float(tick)
            tick_label = f"{tick:g}{line_unit}" if line_unit else f"{tick:g}"
            ty = line_y(tick)
            parts.append(
                f'<text x="{W - pad_r + 10}" y="{ty + 5:.1f}" text-anchor="start" '
                f'fill="var(--navy, #00175a)" font-size="{y_tick_fs}" font-weight="{y_tick_wt}" '
                f'font-family="var(--font-body, sans-serif)">{esc(tick_label)}</text>'
            )

    # X-axis line
    parts.append(
        f'<line x1="{pad_l}" y1="{H - pad_b}" x2="{W - pad_r}" y2="{H - pad_b}" '
        f'stroke="var(--navy, #00175a)" stroke-width="1"/>'
    )

    # Bar legend (multi-series stacked mode only)
    if stacked:
        combo_palette = _series_colors(cfg)
        lx = pad_l + 4
        for si, name in enumerate(bar_series):
            color = combo_palette[si % len(combo_palette)]
            parts.append(
                f'<g class="combo-bar-legend-item">'
                f'<rect x="{lx}" y="18" width="12" height="12" rx="2" fill="{color}"/>'
                f'<text x="{lx + 18}" y="28" fill="var(--ink, #53565a)" font-size="13" '
                f'font-family="var(--font-body, sans-serif)">{esc(name)}</text></g>'
            )
            lx += 18 + len(name) * 7 + 28
        parts.append("<!-- combo-bar-legend -->")

    # Bars
    combo_palette = _series_colors(cfg)
    default_bar_color = combo_palette[0] if cfg.get("series_colors") else "var(--blue, #006fcf)"
    for i, lab in enumerate(bar_labels):
        x = pad_l + i * bar_slot + (bar_slot - bar_w) / 2
        if stacked:
            cursor = 0.0
            for si in range(len(bar_series)):
                v = bar_rows[i][si] if si < len(bar_rows[i]) else None
                if v is None or v <= 0:
                    continue
                y_bottom = bar_y(cursor)
                cursor += v
                y_top = bar_y(cursor)
                seg_color = bar_colors[i] or combo_palette[si % len(combo_palette)]
                parts.append(
                    f'<rect class="combo-seg" x="{x:.1f}" y="{y_top:.1f}" width="{bar_w:.1f}" '
                    f'height="{max(y_bottom - y_top, 0):.1f}" fill="{seg_color}"/>'
                )
                if y_bottom - y_top > 20:
                    parts.append(
                        f'<text x="{x + bar_w / 2:.1f}" y="{(y_top + y_bottom) / 2 + 5:.1f}" '
                        f'text-anchor="middle" fill="#fff" font-size="13" font-weight="600" '
                        f'font-family="var(--font-body, sans-serif)">{esc(_fmtb(v))}</text>'
                    )
            total = bar_totals[i]
            parts.append(
                f'<text x="{x + bar_w / 2:.1f}" y="{bar_y(total) - 8:.1f}" text-anchor="middle" '
                f'fill="var(--navy, #00175a)" font-size="14" font-weight="700" '
                f'font-family="var(--font-body, sans-serif)">{esc(_fmtb(total))}</text>'
            )
        else:
            val = bar_rows[i][0] or 0.0
            y = bar_y(val)
            bh = H - pad_b - y
            bar_color = bar_colors[i] or default_bar_color
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" '
                f'fill="{bar_color}" rx="2"/>'
            )
            val_text = _fmtb(val)
            parts.append(
                f'<text x="{x + bar_w/2:.1f}" y="{y - 8:.1f}" text-anchor="middle" '
                f'fill="var(--navy, #00175a)" font-size="14" font-weight="600" '
                f'font-family="var(--font-body, sans-serif)">{esc(val_text)}</text>'
            )
        lines = label_lines[i] if i < len(label_lines) else [lab]
        for line_i, line in enumerate(lines):
            parts.append(
                f'<text class="auto-x-label" data-auto-label-index="{i}" '
                f'x="{x + bar_w/2:.1f}" y="{H - pad_b + 25 + line_i * x_tick_fs}"'
                f'{svg_label_transform(auto_plan, x + bar_w / 2, H - pad_b + 25 + line_i * x_tick_fs)} text-anchor="middle" '
                f'fill="var(--navy, #00175a)" font-size="{x_tick_fs}" font-weight="600" '
                f'font-family="var(--font-body, sans-serif)">{esc(line)}</text>'
            )

    # Line overlay
    if line_points:
        line_coords: list[tuple[float, float]] = []
        for lp in line_points:
            try:
                idx = bar_labels.index(lp["label"])
            except ValueError:
                idx = len(line_coords)
            if idx < n_bars:
                lx = pad_l + idx * bar_slot + bar_slot / 2
            else:
                lx = pad_l + (len(line_coords) / max(len(line_points) - 1, 1)) * plot_w
            ly = line_y(lp["value"])
            line_coords.append((lx, ly))

        if line_coords:
            dash = 'stroke-dasharray="8,4"' if overlay_style == "dashed" else ""
            pts_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in line_coords)
            parts.append(
                f'<polyline points="{pts_str}" fill="none" '
                f'stroke="{overlay_color}" stroke-width="2" '
                f'{dash} stroke-linejoin="round" stroke-linecap="round"/>'
            )
            for lx, ly in line_coords:
                parts.append(
                    f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="4" '
                    f'fill="{overlay_color}"/>'
                )
            line_unit = overlay_cfg.get("y_axis_unit", "")
            for (lx, ly), lp in zip(line_coords, line_points):
                label_text = f"{lp['value']:g}{line_unit}" if line_unit else f"{lp['value']:g}"
                parts.append(
                    f'<text x="{lx:.1f}" y="{ly - 12:.1f}" text-anchor="middle" '
                    f'fill="var(--navy, #00175a)" font-size="12" '
                    f'font-family="var(--font-body, sans-serif)">{esc(label_text)}</text>'
                )

        if overlay_label:
            parts.append(
                f'<text x="{W - pad_r - 10}" y="{pad_t + 10}" text-anchor="end" '
                f'fill="{overlay_color}" font-size="13" font-weight="600" '
                f'font-family="var(--font-body, sans-serif)">{esc(overlay_label)}</text>'
            )

    parts.append("</svg>")
    return "".join(parts)
