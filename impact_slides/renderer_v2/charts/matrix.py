"""Heatmap and waterfall painters + matrix fallback."""
from __future__ import annotations

from typing import Any, Mapping
from ..strip import esc, strip_eids

from .format import _fmt_chart_num
from .bars import _bar_matrix
from .core import _chart_config, _steps
from .auto_typography import compute_auto_plan_for_slide, svg_auto_axis_view, svg_label_transform
from .typography import resolve_typography



def _fallback_matrix_chart(slide: Mapping[str, Any], lt: str) -> str:
    """Minimal SVG grouped bar when pack is unavailable."""
    steps = _steps(slide)
    labels: list[str] = []
    values: list[float] = []
    for st in steps:
        if isinstance(st, (list, tuple)) and len(st) >= 2:
            try:
                labels.append(str(st[0]))
                values.append(float(str(st[1]).replace("%", "").replace(",", "")))
            except ValueError:
                continue
        elif isinstance(st, str) and ":" in st:
            a, _, b = st.partition(":")
            try:
                labels.append(a.strip())
                values.append(float(b.replace("%", "").strip()))
            except ValueError:
                continue
    if not values:
        return f'<p class="chart-empty">No chart data for {esc(lt)}</p>'
    w, h = 1200, 520
    pad_l, pad_b, pad_t = 80, 60, 30
    max_v = max(values) or 1
    bw = (w - pad_l - 40) / max(len(values), 1) * 0.6
    gap = (w - pad_l - 40) / max(len(values), 1)
    parts = [
        f'<svg class="chart-svg" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
    ]
    for i, (lab, val) in enumerate(zip(labels, values)):
        bh = (val / max_v) * (h - pad_t - pad_b)
        x = pad_l + i * gap + (gap - bw) / 2
        y = h - pad_b - bh
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
            f'fill="#006FCF"/>'
        )
        parts.append(
            f'<text class="chart-value" x="{x + bw/2:.1f}" y="{y - 8:.1f}" '
            f'text-anchor="middle" fill="#00175A" font-size="18" font-weight="700">'
            f"{val:g}</text>"
        )
        parts.append(
            f'<text class="chart-axis-label" x="{x + bw/2:.1f}" y="{h - 20}" '
            f'text-anchor="middle" fill="#63666A" font-size="16">{esc(lab)}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)



def _build_heatmap_html(slide: Mapping[str, Any]) -> str:
    """In-repo heatmap: HTML table with alpha-scaled blue cells (pack parity)."""
    labels, series, rows, _pc = _bar_matrix(slide)
    if not labels or not series or not rows:
        return '<p class="chart-empty">No chart data for heatmap</p>'
    vals = [v for r in rows for v in r if v is not None]
    if not vals:
        return '<p class="chart-empty">No chart data for heatmap</p>'
    vmin, vmax = min(vals), max(vals)
    span = (vmax - vmin) or 1.0  # all-equal: avoid /0, flat low alpha

    def cell_style(v: float) -> str:
        alpha = 0.15 + 0.75 * ((v - vmin) / span)
        return f"background: rgba(0, 111, 207, {alpha:.3f});"

    ths = "".join(f"<th>{esc(c[:14])}</th>" for c in series)
    body: list[str] = []
    for i, rlab in enumerate(labels):
        row = rows[i] if i < len(rows) else []
        cells: list[str] = []
        for j in range(len(series)):
            v = row[j] if j < len(row) else None
            if v is None:
                cells.append('<td class="heatmap-cell is-null">—</td>')
            else:
                cells.append(
                    f'<td class="heatmap-cell" style="{cell_style(v)}">'
                    f"{esc(_fmt_chart_num(v))}</td>"
                )
        body.append(
            f'<tr><th class="row-head">{esc(str(rlab)[:22])}</th>'
            + "".join(cells)
            + "</tr>"
        )
    table = (
        f'<table class="heatmap-table"><thead><tr><th></th>{ths}</tr></thead>'
        f"<tbody>{''.join(body)}</tbody></table>"
    )
    return f'<div class="chart-frame heatmap-wrap">{table}</div>'




def _build_waterfall_svg(slide: Mapping[str, Any]) -> str:
    """In-repo waterfall: running-total bridge bars (pack geometry parity)."""
    cfg = _chart_config(slide)
    typo = resolve_typography(cfg)
    x_tick_fs = int(typo["x_tick_font_size"]) if typo.get("x_tick_font_size_set") else 16
    dl_fs = int(typo["datalabel_font_size"]) if typo.get("datalabel_font_size_set") else 18
    labels, series, rows, _pc = _bar_matrix(slide)
    auto_plan = compute_auto_plan_for_slide(slide, "waterfall_chart", chart_cfg=cfg)
    label_lines, _value_ticks = svg_auto_axis_view(
        auto_plan, labels=labels, ticks=[], format_tick=lambda _tick: ""
    )
    if not labels or not series or not rows:
        return '<p class="chart-empty">No chart data for waterfall_chart</p>'

    # Single-series bridges from first column; optional kind on steps_or_data.
    raw = _steps(slide)
    bridges: list[tuple[str, float, str]] = []  # label, value, kind
    for i, lab in enumerate(labels):
        row = rows[i] if i < len(rows) else []
        v = row[0] if row else None
        if v is None:
            continue
        kind = ""
        if i < len(raw) and isinstance(raw[i], dict):
            kind = str(raw[i].get("kind") or "").lower().strip()
        if not kind:
            kind = "up" if v >= 0 else "down"
        bridges.append((str(lab), float(v), kind))
    if not bridges:
        return '<p class="chart-empty">No chart data for waterfall_chart</p>'

    # Running total: up/down float from prior level; total is absolute from 0.
    level = 0.0
    centers: list[tuple[str, float, float, str, float]] = []
    for lab, val, kind in bridges:
        if kind == "total":
            if abs(val) < 1e-9 and level:
                val = level
            y0, y1 = (0.0, val) if val >= 0 else (val, 0.0)
            centers.append((lab, y0, y1 - y0, "total", val))
            level = val
        else:
            start = level
            level = level + val
            y0, y1 = min(start, level), max(start, level)
            k = "up" if val >= 0 else "down"
            centers.append((lab, y0, y1 - y0, k, val))

    vals_ext = [c[1] for c in centers] + [c[1] + c[2] for c in centers] + [0.0]
    vmin, vmax = min(vals_ext), max(vals_ext)
    if abs(vmax - vmin) < 1e-6:
        vmax = vmin + 1.0
    pad = (vmax - vmin) * 0.08
    vmin -= pad
    vmax += pad

    width, height = 1200, 520
    left, right, top, bottom = 60, 40, 40, 70
    plot_w = width - left - right
    plot_h = height - top - bottom
    n = len(centers)
    slot = plot_w / max(n, 1)
    bar_w = min(72.0, slot * 0.55)

    def y_scale(v: float) -> float:
        return top + plot_h * (1 - (v - vmin) / (vmax - vmin))

    navy, blue, ink = "#00175A", "#006FCF", "#63666A"
    fill_for = {"total": navy, "up": blue, "down": ink}
    cls_for = {
        "total": "chart-bar-navy",
        "up": "chart-bar-blue",
        "down": "chart-bar-ink",
    }

    parts = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Waterfall chart">'
    ]
    if vmin < 0 < vmax:
        yz = y_scale(0.0)
        parts.append(
            f'<line class="chart-gridline" x1="{left}" y1="{yz:.1f}" '
            f'x2="{width - right}" y2="{yz:.1f}" stroke="#E0E4EA" '
            f'stroke-width="1" stroke-dasharray="4 4"/>'
        )

    for i, (lab, y0, h, kind, val) in enumerate(centers):
        cx = left + slot * i + slot / 2
        x = cx - bar_w / 2
        y_top = y_scale(y0 + h)
        y_bot = y_scale(y0)
        bh = max(2.0, y_bot - y_top)
        cls = cls_for[kind]
        fill = fill_for[kind]
        parts.append(
            f'<rect class="{cls}" fill="{fill}" x="{x:.1f}" y="{y_top:.1f}" '
            f'width="{bar_w:.1f}" height="{bh:.1f}" rx="4"/>'
        )
        vlab = _fmt_chart_num(val)
        if kind != "total" and val > 0:
            vlab = "+" + vlab
        parts.append(
            f'<text class="chart-value" x="{cx:.1f}" y="{y_top - 8:.1f}" '
            f'text-anchor="middle" fill="{navy}" font-size="{dl_fs}" '
            f'font-weight="700">{esc(vlab)}</text>'
        )
        lines = label_lines[i] if i < len(label_lines) else [lab]
        for line_i, line in enumerate(lines):
            parts.append(
                f'<text class="chart-axis-label auto-x-label" data-auto-label-index="{i}" '
                f'x="{cx:.1f}" y="{height - 28 + line_i * x_tick_fs}"'
                f'{svg_label_transform(auto_plan, cx, height - 28 + line_i * x_tick_fs)} '
                f'text-anchor="middle" fill="{ink}" font-size="{x_tick_fs}">'
                f"{esc(line)}</text>"
            )

    parts.append("</svg>")
    legend = (
        '<div class="chart-legend">'
        '<span><i class="swatch swatch-navy"></i>Total</span>'
        '<span><i class="swatch swatch-blue"></i>Increase</span>'
        '<span><i class="swatch swatch-ink"></i>Decrease</span>'
        "</div>"
    )
    return '<div class="chart-frame">' + ''.join(parts) + legend + '</div>'
