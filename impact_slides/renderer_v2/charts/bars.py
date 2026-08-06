"""Grouped/stacked/horizontal bar SVG painters."""
from __future__ import annotations

import math
from typing import Any, Mapping
from ..strip import esc, strip_eids

from .format import _bar_num, _fmt_bar, _fmt_value_label, _nice_max, _nice_step, _series_colors
from .geometry import chart_geometry
from .core import _chart_config, _steps
from .callouts import (
    _SIDE_CALLOUT_NAME_GAP_PX,
    _SIDE_CALLOUT_TILE_TOP_PX,
    _build_side_callout_svg,
    _resolve_side_callout,
    _side_column_geometry,
)
from .typography import (
    estimate_label_box,
    resolve_typography,
    suppress_colliding_labels,
    _warn,
)



def _bar_matrix(
    slide: Mapping[str, Any],
) -> tuple[list[str], list[str], list[list[float | None]], list[str | None]]:
    """Parse steps_or_data into (labels, series_names, matrix, point_colors).

    Accepts ``{label, values:{s:v}}`` dicts, ``{label, k: v}`` positional
    dicts, ``{label, value}`` single-series dicts, or list-of-lists with an
    optional header row. Series capped at 4. Dict points may carry an
    optional ``color`` key — a per-category color override (primary use:
    highlighting/muting one bar in a single-series chart).
    """
    raw = _steps(slide)
    if not raw:
        return [], [], [], []
    labels: list[str] = []
    series: list[str] = []
    rows: list[list[float | None]] = []
    point_colors: list[str | None] = []

    if all(isinstance(x, dict) for x in raw):
        for x in raw:
            labels.append(str(x.get("label") or x.get("category") or x.get("name") or "\u2014"))
            point_colors.append(str(x["color"]) if x.get("color") else None)
            vals = x.get("values")
            if isinstance(vals, dict) and vals:
                if not series:
                    series = [str(k) for k in vals.keys()][:4]
                rows.append([_bar_num(vals.get(k)) for k in series])
            elif _bar_num(x.get("value")) is not None:
                if not series:
                    series = ["Value"]
                rows.append([_bar_num(x.get("value"))])
            else:
                nums = {
                    str(k): _bar_num(v)
                    for k, v in x.items()
                    if k not in ("label", "category", "name", "kind", "icon")
                    and _bar_num(v) is not None
                }
                if not series:
                    series = list(nums.keys())[:4]
                rows.append([nums.get(k) for k in series])
        return labels, series, rows, point_colors

    if all(isinstance(x, (list, tuple)) for x in raw):
        rows_raw = [list(x) for x in raw]
        first = rows_raw[0]
        second = rows_raw[1] if len(rows_raw) > 1 else []
        has_header = (
            len(rows_raw) > 1
            and all(isinstance(c, str) for c in first[1:])
            and any(_bar_num(c) is not None for c in second[1:])
        )
        if has_header:
            series = [str(c) for c in first[1:5]]
            body = rows_raw[1:]
        else:
            width = max(len(r) for r in rows_raw) - 1
            series = [f"S{i + 1}" for i in range(min(width, 4))]
            body = rows_raw
        for r in body:
            labels.append(str(r[0]))
            rows.append([_bar_num(v) for v in r[1 : len(series) + 1]])
        return labels, series, rows, [None] * len(labels)

    return [], [], [], []



def _bar_axes(
    cfg: dict[str, Any],
    data_max: float,
    data_min: float,
) -> tuple[float, float, list[float]]:
    """Compute (y_max, y_min, ticks) with nice-number rounding."""
    y_max = cfg.get("y_axis_max")
    if y_max is None:
        y_max = _nice_max(data_max * 1.05)
    y_max = float(y_max)
    y_min = cfg.get("y_axis_min")
    if y_min is None:
        y_min = -_nice_max(abs(data_min) * 1.05) if data_min < 0 else 0.0
    y_min = float(y_min)
    ticks = cfg.get("y_axis_ticks")
    if ticks is None:
        if y_min < 0 and abs(y_min) > 0.15 * y_max:
            step = _nice_step((y_max - y_min) / 4)
            lo = math.floor(y_min / step) * step
        else:
            # Small negative tail (e.g. reserve releases): tick from zero up
            step = _nice_step(y_max / 4)
            lo = 0.0
        hi = math.ceil(y_max / step) * step
        ticks = []
        t = lo
        while t <= hi + 1e-9:
            ticks.append(round(t, 6))
            t += step
    return y_max, y_min, [float(t) for t in ticks]



def _vbar_pad_t(cfg: Mapping[str, Any], series: list[str]) -> int:
    """Top padding for internal bar charts: room for legend + bar_groups."""
    base = 56 if len(series) > 1 else 40
    if cfg.get("bar_groups"):
        base += 28
    return base



def _bar_group_brackets(
    cfg: Mapping[str, Any],
    labels: list[str],
    pad_l: float,
    slot: float,
    bracket_y: float,
) -> list[str]:
    """Emit labeled bracket annotations spanning category ranges.

    chart_config.bar_groups: [{"label": str, "start": int, "end": int}]
    (inclusive category indices). Each bracket is a horizontal line with
    vertical end ticks and a centered label above it.
    """
    groups = cfg.get("bar_groups")
    if not isinstance(groups, (list, tuple)) or not groups or not labels:
        return []
    parts: list[str] = []
    for g in groups:
        if not isinstance(g, Mapping):
            continue
        try:
            start = int(g.get("start", 0))
            end = int(g.get("end", start))
        except (TypeError, ValueError):
            continue
        start = max(0, min(start, len(labels) - 1))
        end = max(start, min(end, len(labels) - 1))
        x1 = pad_l + start * slot + 6
        x2 = pad_l + (end + 1) * slot - 6
        label = str(g.get("label") or "")
        parts.append(
            f'<g class="bar-group-bracket">'
            f'<line x1="{x1:.1f}" y1="{bracket_y:.1f}" x2="{x2:.1f}" y2="{bracket_y:.1f}" '
            f'stroke="var(--ink-muted, #63666a)" stroke-width="1.5"/>'
            f'<line x1="{x1:.1f}" y1="{bracket_y:.1f}" x2="{x1:.1f}" y2="{bracket_y + 6:.1f}" '
            f'stroke="var(--ink-muted, #63666a)" stroke-width="1.5"/>'
            f'<line x1="{x2:.1f}" y1="{bracket_y:.1f}" x2="{x2:.1f}" y2="{bracket_y + 6:.1f}" '
            f'stroke="var(--ink-muted, #63666a)" stroke-width="1.5"/>'
            f'<text x="{(x1 + x2) / 2:.1f}" y="{bracket_y - 8:.1f}" text-anchor="middle" '
            f'fill="var(--navy, #00175a)" font-size="14" font-weight="600" '
            f'font-family="var(--font-body, sans-serif)">{esc(label)}</text></g>'
        )
    return parts



def _vbar_frame(
    cls: str,
    cfg: dict[str, Any],
    y_max: float,
    y_min: float,
    y_ticks: list[float],
    series: list[str],
    *,
    pad_r: float | None = None,
) -> list[str]:
    show_grid = bool(cfg.get("gridlines", True))
    geom = chart_geometry("_vertical_bar")
    W, H = geom["width"], geom["height"]
    pad_l, default_pad_r, pad_t, pad_b = geom["pad_l"], geom["pad_r"], _vbar_pad_t(cfg, series), 56
    pad_r = default_pad_r if pad_r is None else pad_r
    plot_h = H - pad_t - pad_b
    unit = cfg.get("y_axis_unit", "")

    def y_pos(v: float) -> float:
        rng = y_max - y_min
        if rng == 0:
            return pad_t + plot_h / 2
        return pad_t + plot_h - ((v - y_min) / rng) * plot_h

    typo = resolve_typography(cfg)
    # SVG legacy y-tick is 14; only override when the knob is explicitly set.
    y_tick_fs = (
        int(typo["y_tick_font_size"]) if typo.get("y_tick_font_size_set") else 14
    )
    y_tick_wt = "700" if typo.get("y_tick_font_size_set") else "600"
    x_tick_fs = (
        int(typo["x_tick_font_size"]) if typo.get("x_tick_font_size_set") else 14
    )
    parts: list[str] = [
        f'<svg class="chart-svg vbar-chart {cls}" viewBox="0 0 {W} {H}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;height:auto">'
    ]
    for tick in y_ticks:
        ty = y_pos(tick)
        if show_grid:
            parts.append(
                f'<line x1="{pad_l}" y1="{ty:.1f}" x2="{W - pad_r}" y2="{ty:.1f}" '
                f'stroke="var(--panel-border, #d8dce3)" stroke-width="0.5"/>'
            )
        parts.append(
            f'<text x="{pad_l - 10}" y="{ty + 5:.1f}" text-anchor="end" '
            f'fill="var(--navy, #00175a)" font-size="{y_tick_fs}" font-weight="{y_tick_wt}" '
            f'font-family="var(--font-body, sans-serif)">{esc(_fmt_bar(tick, unit))}</text>'
        )
    # Stash sizes on cfg for value/x label painters in the same call.
    cfg["_typo_x_tick_fs"] = x_tick_fs
    cfg["_typo_dl_fs"] = (
        int(typo["datalabel_font_size"]) if typo.get("datalabel_font_size_set") else 14
    )
    cfg["_typo_dl_set"] = int(typo.get("datalabel_font_size_set") or 0)
    parts.append(
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{H - pad_b}" '
        f'stroke="var(--navy, #00175a)" stroke-width="1"/>'
    )
    # X-axis at zero (or plot bottom when all values positive)
    zero_y = y_pos(0) if y_min < 0 else float(H - pad_b)
    parts.append(
        f'<line x1="{pad_l}" y1="{zero_y:.1f}" x2="{W - pad_r}" y2="{zero_y:.1f}" '
        f'stroke="var(--navy, #00175a)" stroke-width="1"/>'
    )
    # Legend (multi-series only)
    if len(series) > 1:
        palette = _series_colors(cfg)
        lx = pad_l + 4
        for i, name in enumerate(series):
            color = palette[i % len(palette)]
            parts.append(
                f'<g class="vbar-legend-item">'
                f'<rect x="{lx}" y="18" width="12" height="12" rx="2" fill="{color}"/>'
                f'<text x="{lx + 18}" y="28" fill="var(--ink, #53565a)" font-size="13" '
                f'font-family="var(--font-body, sans-serif)">{esc(name)}</text></g>'
            )
            lx += 18 + len(name) * 7 + 28
        parts.append('<!-- vbar-legend -->')
    return parts



def _build_grouped_bar_svg(slide: Mapping[str, Any]) -> str:
    """Build a vertical grouped bar chart (internal replacement for the pack)."""
    labels, series, matrix, point_colors = _bar_matrix(slide)
    if not labels or not series:
        return '<p class="chart-empty">No bar chart data</p>'
    all_vals = [v for row in matrix for v in row if v is not None]
    if not all_vals:
        return '<p class="chart-empty">No bar chart data</p>'

    cfg = _chart_config(slide)
    show_grid = bool(cfg.get("gridlines", True))
    geom = chart_geometry("_vertical_bar")
    W, H = geom["width"], geom["height"]
    pad_l, pad_r, pad_t, pad_b = geom["pad_l"], geom["pad_r"], _vbar_pad_t(cfg, series), 56
    plot_w = W - pad_l - pad_r
    plot_h = H - pad_t - pad_b
    unit = cfg.get("y_axis_unit", "")

    y_max, y_min, y_ticks = _bar_axes(cfg, max(all_vals), min(all_vals))

    def y_pos(v: float) -> float:
        rng = y_max - y_min
        if rng == 0:
            return pad_t + plot_h / 2
        return pad_t + plot_h - ((v - y_min) / rng) * plot_h

    parts = _vbar_frame("vbar-grouped", cfg, y_max, y_min, y_ticks, series)
    zero_y = y_pos(0) if y_min < 0 else float(H - pad_b)

    n = len(labels)
    slot = plot_w / n
    group_w = slot * 0.65
    bar_w = group_w / len(series)
    palette = _series_colors(cfg)
    dl_fs = int(cfg.get("_typo_dl_fs") or 14)
    x_fs = int(cfg.get("_typo_x_tick_fs") or 14)
    dl_set = bool(cfg.get("_typo_dl_set"))

    parts.extend(_bar_group_brackets(cfg, labels, pad_l, slot, pad_t - 22))

    # Collect ordinary value labels for optional collision suppression (#139).
    label_items: list[dict[str, Any]] = []
    label_markup: list[str] = []

    for i, lab in enumerate(labels):
        gx = pad_l + i * slot + (slot - group_w) / 2
        for j in range(len(series)):
            v = matrix[i][j] if j < len(matrix[i]) else None
            if v is None:
                continue
            x = gx + j * bar_w
            color = point_colors[i] or palette[j % len(palette)]
            if v >= 0:
                y = y_pos(v)
                bh = zero_y - y
                label_y = y - 8
            else:
                y = zero_y
                bh = y_pos(v) - zero_y
                label_y = y_pos(v) + 18
            parts.append(
                f'<rect class="vbar" x="{x:.1f}" y="{y:.1f}" width="{bar_w - 4:.1f}" '
                f'height="{max(bh, 0):.1f}" fill="{color}" rx="2"/>'
            )
            txt = _fmt_value_label(
                v, str(unit or ""), str(cfg.get("y_axis_unit_position") or "")
            )
            cx = x + (bar_w - 4) / 2
            label_items.append(
                {
                    "series": j,
                    "category": i,
                    "label": txt,
                    "box": estimate_label_box(txt, x=cx, y=label_y, font_size=dl_fs),
                }
            )
            label_markup.append(
                f'<text x="{cx:.1f}" y="{label_y:.1f}" text-anchor="middle" '
                f'fill="var(--navy, #00175a)" font-size="{dl_fs}" font-weight="600" '
                f'font-family="var(--font-body, sans-serif)">{esc(txt)}</text>'
            )
        parts.append(
            f'<text x="{pad_l + i * slot + slot / 2:.1f}" y="{H - pad_b + 25}" '
            f'text-anchor="middle" fill="var(--navy, #00175a)" font-size="{x_fs}" '
            f'font-weight="600" font-family="var(--font-body, sans-serif)">{esc(lab)}</text>'
        )

    if dl_set and label_items:
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

    parts.append("</svg>")
    return "".join(parts)



def _build_stacked_bar_svg(slide: Mapping[str, Any]) -> str:
    """Build a vertical stacked bar chart with negative-segment support."""
    labels, series, matrix, point_colors = _bar_matrix(slide)
    if not labels or not series:
        return '<p class="chart-empty">No stacked bar data</p>'
    pos_sums = [sum(v for v in row if v is not None and v > 0) for row in matrix]
    neg_sums = [sum(v for v in row if v is not None and v < 0) for row in matrix]
    if not any(pos_sums) and not any(neg_sums):
        return '<p class="chart-empty">No stacked bar data</p>'

    cfg = _chart_config(slide)
    show_grid = bool(cfg.get("gridlines", True))
    geom = chart_geometry("_vertical_bar")
    W, H = geom["width"], geom["height"]
    side_plan = _resolve_side_callout(cfg, "stacked_bar_chart")
    column = _side_column_geometry(cfg) if side_plan else None
    pad_l, pad_r, pad_t, pad_b = (
        geom["pad_l"],
        column[1] if column else geom["pad_r"],
        _vbar_pad_t(cfg, series),
        56,
    )
    plot_w = W - pad_l - pad_r
    plot_h = H - pad_t - pad_b
    unit = cfg.get("y_axis_unit", "")

    y_max, y_min, y_ticks = _bar_axes(cfg, max(pos_sums), min(neg_sums))

    def y_pos(v: float) -> float:
        rng = y_max - y_min
        if rng == 0:
            return pad_t + plot_h / 2
        return pad_t + plot_h - ((v - y_min) / rng) * plot_h

    parts = _vbar_frame("vbar-stacked", cfg, y_max, y_min, y_ticks, series, pad_r=pad_r)
    zero_y = y_pos(0) if y_min < 0 else float(H - pad_b)

    n = len(labels)
    slot = plot_w / n
    bar_w = slot * 0.5
    palette = _series_colors(cfg)

    parts.extend(_bar_group_brackets(cfg, labels, pad_l, slot, pad_t - 22))

    for i, lab in enumerate(labels):
        x = pad_l + i * slot + (slot - bar_w) / 2
        # Positive stack grows upward from zero
        cursor = 0.0
        for j in range(len(series)):
            v = matrix[i][j] if j < len(matrix[i]) else None
            if v is None or v <= 0:
                continue
            y_bottom = y_pos(cursor)
            cursor += v
            y_top = y_pos(cursor)
            color = point_colors[i] or palette[j % len(palette)]
            parts.append(
                f'<rect class="vbar-seg" x="{x:.1f}" y="{y_top:.1f}" width="{bar_w:.1f}" '
                f'height="{max(y_bottom - y_top, 0):.1f}" fill="{color}"/>'
            )
            # Segment value label inside (if tall enough)
            if y_bottom - y_top > 20:
                parts.append(
                    f'<text x="{x + bar_w / 2:.1f}" y="{(y_top + y_bottom) / 2 + 5:.1f}" '
                    f'text-anchor="middle" fill="#fff" font-size="13" font-weight="600" '
                    f'font-family="var(--font-body, sans-serif)">{esc(_fmt_bar(v, unit))}</text>'
                )
        # Negative stack grows downward from zero
        cursor = 0.0
        for j in range(len(series)):
            v = matrix[i][j] if j < len(matrix[i]) else None
            if v is None or v >= 0:
                continue
            y_top = y_pos(cursor)
            cursor += v
            y_bottom = y_pos(cursor)
            color = point_colors[i] or palette[j % len(palette)]
            parts.append(
                f'<rect class="vbar-seg vbar-neg" x="{x:.1f}" y="{y_top:.1f}" width="{bar_w:.1f}" '
                f'height="{max(y_bottom - y_top, 0):.1f}" fill="{color}"/>'
            )
        # Net total above the positive stack (or above zero)
        net = pos_sums[i] + neg_sums[i]
        total_y = y_pos(pos_sums[i]) - 8 if pos_sums[i] > 0 else zero_y - 8
        parts.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{total_y:.1f}" text-anchor="middle" '
            f'fill="var(--navy, #00175a)" font-size="14" font-weight="700" '
            f'font-family="var(--font-body, sans-serif)">{esc(_fmt_bar(net, unit))}</text>'
        )
        # Negative total below the negative stack, in parentheses; clamped
        # so it never collides with the category label row.
        if neg_sums[i] < 0:
            neg_label_y = min(y_pos(neg_sums[i]) + 16, H - pad_b + 18)
            parts.append(
                f'<text x="{x + bar_w / 2:.1f}" y="{neg_label_y:.1f}" '
                f'text-anchor="middle" fill="var(--navy, #00175a)" font-size="13" '
                f'font-family="var(--font-body, sans-serif)">'
                f'({esc(_fmt_bar(abs(neg_sums[i]), unit))})</text>'
            )
        # Category labels sit lower when negative totals occupy the usual row
        cat_y = H - 12 if any(neg_sums) else H - pad_b + 25
        x_fs = int(cfg.get("_typo_x_tick_fs") or 14)
        parts.append(
            f'<text x="{pad_l + i * slot + slot / 2:.1f}" y="{cat_y}" '
            f'text-anchor="middle" fill="var(--navy, #00175a)" font-size="{x_fs}" '
            f'font-weight="600" font-family="var(--font-body, sans-serif)">{esc(lab)}</text>'
        )

    if column:
        offset, gutter = column
        names: list[tuple[float, str, str]] = []
        for j, name in enumerate(series):
            last = next(
                (
                    i for i in range(n - 1, -1, -1)
                    if j < len(matrix[i])
                    and isinstance(matrix[i][j], (int, float))
                    and matrix[i][j]
                ),
                None,
            )
            if last is None:
                continue
            value = matrix[last][j]
            if not isinstance(value, (int, float)):
                continue
            prior = matrix[last][:j + 1]
            mid = (
                sum(v for v in prior if isinstance(v, (int, float)) and v > 0) - value / 2
                if value > 0
                else sum(v for v in prior if isinstance(v, (int, float)) and v < 0) - value / 2
            )
            names.append((y_pos(mid), str(name), palette[j % len(palette)]))
        min_y = (
            _SIDE_CALLOUT_TILE_TOP_PX
            + _SIDE_CALLOUT_NAME_GAP_PX
            + sum(int(line["line_height"]) for line in side_plan["lines"])
        )
        names.sort()
        for i, (y, name, color) in enumerate(names):
            y = max(y, min_y if i == 0 else names[i - 1][0] + 16)
            names[i] = (y, name, color)
            parts.append(
                f'<text class="vbar-segment-name" x="{W - gutter + offset:.1f}" y="{y:.1f}" '
                f'fill="{color}" font-size="12" font-weight="600" '
                f'font-family="var(--font-body, sans-serif)">{esc(name)}</text>'
            )
    if side_plan and not cfg.get("_side_callout_external"):
        parts.append(_build_side_callout_svg(cfg, "stacked_bar_chart", warn=False))
    parts.append("</svg>")
    return "".join(parts)



def _build_hbar_svg(slide: Mapping[str, Any]) -> str:
    """Basic horizontal grouped bars — geometry-parity SVG fallback (#88).

    Orientation is geometry, not a cue: the noscript/export path keeps bars
    horizontal. Anniversary-window polish (discontinuous axis, inside-bar
    labels) is Chart.js-only per the locked painter split.
    """
    labels, series, rows, _pc = _bar_matrix(slide)
    if not labels or not series:
        return '<p class="chart-empty">No bar chart data</p>'
    vals = [v for r in rows for v in r if v is not None]
    if not vals:
        return '<p class="chart-empty">No bar chart data</p>'
    cfg = _chart_config(slide)
    palette = _series_colors(cfg)
    typo = resolve_typography(cfg)
    # indexAxis=y: category labels sit on y; value ticks on x.
    cat_fs = (
        int(typo["y_tick_font_size"]) if typo.get("y_tick_font_size_set") else 13
    )
    cat_wt = "700" if typo.get("y_tick_font_size_set") else "600"
    x_tick_fs = (
        int(typo["x_tick_font_size"]) if typo.get("x_tick_font_size_set") else 13
    )
    x_tick_wt = "700" if typo.get("x_tick_font_size_set") else "600"
    W, H = 960, 540
    pad_l, pad_r, pad_t, pad_b = 140.0, 24.0, 16.0, 40.0
    plot_w = W - pad_l - pad_r
    plot_h = H - pad_t - pad_b
    x_max = _nice_max(max(vals) * 1.05)
    x_min = min(0.0, min(vals))
    rng = (x_max - x_min) or 1.0

    def x_pos(v: float) -> float:
        return pad_l + ((v - x_min) / rng) * plot_w

    zero_x = x_pos(0.0)
    n = len(labels)
    m = len(series)
    row_h = plot_h / max(n, 1)
    bar_h = min(28.0, (row_h * 0.7) / max(m, 1))
    parts = [
        f'<svg class="chart-svg hbar" viewBox="0 0 {W} {H}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img">'
    ]
    # Value-axis tick labels (x) when opt-in typography is set.
    if typo.get("x_tick_font_size_set"):
        n_ticks = 5
        for ti in range(n_ticks):
            tv = x_min + (rng * ti / (n_ticks - 1))
            tx = x_pos(tv)
            parts.append(
                f'<text class="hbar-xtick" x="{tx:.1f}" y="{H - pad_b + 18:.1f}" '
                f'text-anchor="middle" fill="var(--navy, #00175a)" '
                f'font-size="{x_tick_fs}" font-weight="{x_tick_wt}" '
                f'font-family="var(--font-body, sans-serif)">'
                f'{esc(_fmt_bar(tv, ""))}</text>'
            )
    for i, lab in enumerate(labels):
        cy = pad_t + row_h * i + row_h / 2
        parts.append(
            f'<text class="hbar-cat" x="{pad_l - 8:.1f}" y="{cy + 4:.1f}" '
            f'text-anchor="end" fill="var(--navy, #00175a)" font-size="{cat_fs}" '
            f'font-weight="{cat_wt}">{esc(lab)}</text>'
        )
        for si in range(m):
            v = rows[i][si] if si < len(rows[i]) else None
            if v is None:
                continue
            x0 = min(zero_x, x_pos(v))
            w = abs(x_pos(v) - zero_x)
            by = cy - (bar_h * m) / 2 + si * bar_h
            color = palette[si % len(palette)]
            parts.append(
                f'<rect class="hbar-bar" x="{x0:.1f}" y="{by:.1f}" '
                f'width="{w:.1f}" height="{bar_h - 3:.1f}" '
                f'fill="{color}" rx="2"/>'
            )
    parts.append(
        f'<line class="hbar-zero" x1="{zero_x:.1f}" y1="{pad_t:.1f}" '
        f'x2="{zero_x:.1f}" y2="{H - pad_b:.1f}" '
        f'stroke="var(--ink, #53565a)" stroke-width="1"/>'
    )
    parts.append("</svg>")
    return "".join(parts)
