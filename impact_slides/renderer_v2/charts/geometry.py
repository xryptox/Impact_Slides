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
