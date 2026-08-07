"""Shared chart pane geometry constants and helpers."""
from __future__ import annotations



# ---------------------------------------------------------------------------
# Chart geometry contract (Fidelity T8 / #36)
#
# Single source of truth for plot insets. Chart builders read their insets
# from chart_geometry(), and any co-located element that must align with the
# plot (e.g. a plot-aligned support table) derives its own geometry from the
# same values via chart_column_interval() — so spatial relationships between
# composed elements hold by construction, not by accident.
_CHART_GEOMETRY: dict[str, dict[str, int]] = {
    "line_chart": {"width": 900, "height": 480, "pad_l": 80, "pad_r": 40},
    "grouped_bar_chart": {"width": 900, "height": 480, "pad_l": 70, "pad_r": 30},
    "stacked_bar_chart": {"width": 900, "height": 480, "pad_l": 70, "pad_r": 30},
    # pad_r widens to 80 when a dual right-side axis is active (has_overlay)
    "combo_chart": {"width": 900, "height": 480, "pad_l": 80, "pad_r": 40},
    # shared insets used by the common vertical-bar frame
    "_vertical_bar": {"width": 900, "height": 480, "pad_l": 70, "pad_r": 30},
}



def chart_geometry(
    layout_type: str, *, n: int | None = None, has_overlay: bool = False
) -> dict[str, float]:
    """Plot insets (SVG units) for ``layout_type`` — the geometry contract
    between chart builders and elements composed around them."""
    geom: dict[str, float] = dict(
        _CHART_GEOMETRY.get(layout_type, _CHART_GEOMETRY["_vertical_bar"])
    )
    if layout_type == "combo_chart" and has_overlay:
        geom["pad_r"] = 80
    if layout_type == "line_chart":
        # n-dependent insets (Fidelity T11 / #39): with points placed at the
        # plot edges (pad_l + i*slot), equal table columns centered on those
        # points require pad_l - slot/2 >= 0 on the left and plot_r + slot/2
        # <= 900 on the right. Solving both exactly gives pad_l = 72 + 414/n
        # and pad_r = 414/n: the aligned table then spans [0, 900] with an
        # 8% label column and value columns centered EXACTLY under each
        # category point (and the plot gains the PDF's generous margins).
        count = n if n and n > 1 else 5
        geom["pad_l"] = 72 + 414 / count
        geom["pad_r"] = 414 / count
    return geom



def chart_column_interval(
    layout_type: str, n: int, *, has_overlay: bool = False
) -> tuple[float, float, float]:
    """SVG x-interval ``(left, right, width)`` that ``n`` equal table columns
    should span so that column ``i`` is centered exactly under the chart's
    category ``i`` position.

    Line charts place points at the plot edges (pad_l + i*plot_w/(n-1)), so
    edge columns need a half-slot overhang beyond the plot; bar charts place
    categories at slot centers, so columns span the plot exactly. Mapping the
    returned interval linearly onto the table's value region makes every
    column center exact for any margins.
    """
    geom = chart_geometry(layout_type, n=n, has_overlay=has_overlay)
    w = geom["width"]
    plot_l = float(geom["pad_l"])
    plot_r = float(w - geom["pad_r"])
    if layout_type == "line_chart" and n > 1:
        slot = (plot_r - plot_l) / (n - 1)
        return plot_l - slot / 2, plot_r + slot / 2, float(w)
    return plot_l, plot_r, float(w)


# Outlined support-row lane contract (#149). CSS twin: .chart-outlined-label
# min-width 200px and .chart-outlined-cell box at 40% of pitch. Shared by the
# static SVG path and the Chart.js runtime re-pitch script.
OUTLINED_LABEL_MIN_PX = 200.0
OUTLINED_LABEL_GAP_PX = 8.0
OUTLINED_CELL_BOX_FRAC = 0.4
# 1920×1080 stage, gl-main inset 96/side, chart-frame pad 22/side, chart-split 55%.
OUTLINED_HOST_WIDTH_PX = (1920.0 - 2 * 96.0 - 2 * 22.0) * 0.55  # 926.2
# How far the wrap may extend left of .chart-col into the frame (measured ~400).
OUTLINED_MAX_LEFT_EXTEND_PX = 400.0


def outlined_lane_layout(
    plot_left: float,
    plot_right: float,
    svg_width: float,
    n: int,
    *,
    host_px: float | None = None,
    label_min_px: float | None = None,
    gap_px: float | None = None,
    box_frac: float | None = None,
    max_left_extend_px: float | None = None,
    has_label: bool = True,
) -> dict[str, float | bool | str]:
    """Pixel lane model for an outlined support row under a chart column.

    Coordinates are px relative to the chart-col left edge (0). Value slots
    still start at the plot-scaled left edge so cell centers track bar
    centers; the label lane grows left when the natural y-axis gutter is
    narrower than ``label_min_px``.

    Separation: label box is contained in the label column; first value box
    sits at ``box_frac`` of the pitch centered in slot 0, so clear space is
    ``(1 - box_frac) / 2 * pitch`` (must be >= gap_px).
    """
    # Resolve module constants at call time so tests can monkeypatch them.
    if host_px is None:
        host_px = OUTLINED_HOST_WIDTH_PX
    if label_min_px is None:
        label_min_px = OUTLINED_LABEL_MIN_PX
    if gap_px is None:
        gap_px = OUTLINED_LABEL_GAP_PX
    if box_frac is None:
        box_frac = OUTLINED_CELL_BOX_FRAC
    if max_left_extend_px is None:
        max_left_extend_px = OUTLINED_MAX_LEFT_EXTEND_PX

    empty = {
        "ok": False,
        "mode": "stacked",
        "shift_px": 0.0,
        "wrap_w_px": 0.0,
        "label_col_w_px": 0.0,
        "label_box_w_px": 0.0,
        "pitch_px": 0.0,
        "left_px": 0.0,
        "right_px": 0.0,
        "sep_px": 0.0,
    }
    if n < 1 or host_px <= 0 or svg_width <= 0 or plot_right <= plot_left:
        return empty

    scale = host_px / svg_width
    left_px = float(plot_left) * scale
    right_px = float(plot_right) * scale
    pitch = (right_px - left_px) / n
    if not (pitch > 0):
        return empty

    # Cell box centered in slot → left padding inside the first value slot.
    sep = (1.0 - float(box_frac)) / 2.0 * pitch
    want_min = float(label_min_px) if has_label else 0.0
    label_col_w = max(left_px, want_min) if want_min > 0 else max(0.0, left_px)
    shift = max(0.0, label_col_w - left_px)
    wrap_w = label_col_w + pitch * n

    ok = (
        shift <= max_left_extend_px + 1e-6
        and wrap_w <= host_px + max_left_extend_px + 1e-6
        and (not has_label or want_min <= 0 or sep + 1e-6 >= float(gap_px))
    )
    return {
        "ok": bool(ok),
        "mode": "aligned" if ok else "stacked",
        "shift_px": float(shift),
        "wrap_w_px": float(wrap_w),
        "label_col_w_px": float(label_col_w),
        "label_box_w_px": float(want_min if want_min > 0 else label_col_w),
        "pitch_px": float(pitch),
        "left_px": float(left_px),
        "right_px": float(right_px),
        "sep_px": float(sep),
    }
