"""Chart.js config builders and HTML shell."""
from __future__ import annotations

import math
import uuid
from typing import Any, Mapping
from ..shell import _BAR_GROUP_PLUGIN_HTML
from ..strip import esc, strip_eids

from .format import _NAVY, _NAVY_SOFT, _WHITE, _fmt_unit, _fmt_value_label, _series_color, _series_colors
from .callouts import (
    _CALLOUT_TYPES,
    _align_overlay_to_labels,
    _build_callout_overlays,
    _build_side_callout_html,
    _merge_callout_bands,
    _side_column_geometry,
)
from .bars import _bar_matrix
from .lines import _combo_bar_data, _combo_line_data, _line_data
from .core import _chart_config, _svg_fallback_for_layout
from .auto_typography import (
    apply_plan_to_chartjs_options,
    chart_host_dimensions,
    full_label_aria_suffix,
    plan_to_data_attrs,
    record_auto_diagnostic,
    typography_with_auto,
)
from .typography import (
    DATALABEL_COLLISION_JS,
    LEGACY_X_TICK,
    LEGACY_Y_TICK,
    ordinary_datalabel_size,
    resolve_typography,
    uses_ordinary_datalabels,
)



def _datalabels_cfg(
    *,
    anchor: str,
    align: str,
    offset: int,
    color: str,
    size: int,
    labels: list[list[str]],
) -> dict[str, Any]:
    """datalabels plugin config; the shell formatter resolves ``_labels``
    per dataset/dataIndex (and strips the key before Chart.js sees it)."""
    return {
        "display": True,
        "anchor": anchor,
        "align": align,
        "offset": offset,
        "color": color,
        "font": {"weight": "bold", "size": size},
        "_labels": labels,
    }



def _next_chart_id() -> str:
    """Stable-enough unique canvas id (no process-global counter)."""
    return f"rv2-chart-{uuid.uuid4().hex[:12]}"



def _numeric_dataset_values(datasets: list[dict[str, Any]]) -> list[float]:
    """Flatten Chart.js dataset data entries to floats (skip non-numerics)."""
    out: list[float] = []
    for ds in datasets:
        for v in ds.get("data") or []:
            if isinstance(v, bool):
                continue
            if isinstance(v, (int, float)):
                out.append(float(v))
            elif isinstance(v, Mapping):
                for key in ("y", "x"):
                    n = v.get(key)
                    if isinstance(n, (int, float)) and not isinstance(n, bool):
                        out.append(float(n))
                        break
    return out



def _apply_semantic_zero_line(
    options: dict[str, Any],
    datasets: list[dict[str, Any]],
    *,
    axis: str = "y",
) -> None:
    """Enable shell zeroLine plugin when zero is a semantic interior baseline.

    Independent of scale grids (issue 152). Fires when data includes a negative
    value, or when an explicit scale domain straddles zero. No-op otherwise so
    all-positive charts keep only the axis edge.
    """
    vals = _numeric_dataset_values(datasets)
    needs = any(v < 0 for v in vals)
    if not needs:
        scale = (options.get("scales") or {}).get(axis) or {}
        lo, hi = scale.get("min"), scale.get("max")
        needs = (
            isinstance(lo, (int, float))
            and isinstance(hi, (int, float))
            and not isinstance(lo, bool)
            and not isinstance(hi, bool)
            and float(lo) < 0 < float(hi)
        )
    if not needs:
        return
    options.setdefault("plugins", {})["zeroLine"] = {
        "axis": axis,
        "color": _NAVY,
        "lineWidth": 1,
    }



def _chartjs_common_options(
    cfg: Mapping[str, Any] | None = None,
    *,
    typo: Mapping[str, int] | None = None,
    auto_plan: Any | None = None,
    horizontal: bool = False,
) -> dict[str, Any]:
    """Calm Boardroom defaults: no animation, readable axes, no plot gridlines.

    Plot gridlines are off by default (issue 152). Axis baselines, ticks, and
    semantic zero lines stay. Legacy show_gridlines / gridlines keys are
    ignored — there is no force-on hatch.

    Optional axis-chrome suppression (F11+, v4 sim):
      show_y_axis / show_x_axis: False -> hide that scale entirely
      show_legend: False -> hide the legend (recipes set this when a pane
        heading already carries a single series' name, so the swatch would
        only restate it). Defaults to True (Chart.js default).

    ``typo`` / ``auto_plan`` let callers inject the shared auto-resolved
    sizes so Chart.js and SVG share one plan.
    """
    if typo is None:
        typo = resolve_typography(cfg or {})
    x_size = int(typo.get("x_tick_font_size", LEGACY_X_TICK))
    y_size = int(typo.get("y_tick_font_size", LEGACY_Y_TICK))
    y_weight = "bold" if y_size != LEGACY_Y_TICK else None
    y_font: dict[str, Any] = {"family": "'IBM Plex Sans', sans-serif", "size": y_size}
    if y_weight:
        y_font["weight"] = y_weight
    options = {
        "responsive": True,
        "maintainAspectRatio": False,
        "animation": False,
        "plugins": {
            "legend": {
                "labels": {
                    "color": "#53565a",
                    "font": {"family": "'Source Sans 3', sans-serif", "size": 14},
                }
            },
            "tooltip": {"enabled": True},
        },
        "scales": {
            "x": {
                "ticks": {
                    "color": "#00175a",
                    "font": {"family": "'Source Sans 3', sans-serif", "size": x_size},
                },
                "grid": {"display": False},
            },
            "y": {
                "ticks": {
                    "color": "#00175a",
                    "font": y_font,
                },
                "grid": {"display": False},
            },
        },
    }
    if cfg:
        if cfg.get("show_legend") is False:
            options["plugins"]["legend"]["display"] = False
        if cfg.get("show_y_axis") is False:
            options["scales"]["y"]["display"] = False
        if cfg.get("show_x_axis") is False:
            options["scales"]["x"]["display"] = False
    if auto_plan is not None and getattr(auto_plan, "enabled", False):
        apply_plan_to_chartjs_options(options, auto_plan, horizontal=horizontal)
    return options



def _apply_bar_density_knobs(
    datasets: list[dict[str, Any]], cfg: Mapping[str, Any]
) -> None:
    # N5 density: opt-in bar width levers (Chart.js barPercentage /
    # categoryPercentage) onto every bar-type dataset. Absent keys keep
    # Chart.js defaults, so existing handoffs serialize byte-identical
    # (SC-COMPAT-1). Applied across vertical, horizontal, and combo bar
    # configs so the knobs are layout-agnostic as advertised.
    for knob, field in (
        ("bar_percentage", "barPercentage"),
        ("category_percentage", "categoryPercentage"),
    ):
        if cfg.get(knob) is not None:
            v = float(cfg[knob])
            for ds in datasets:
                if ds.get("type", "bar") == "bar":
                    ds[field] = v



def _chartjs_bar_config(slide: Mapping[str, Any], *, stacked: bool = False) -> dict[str, Any] | None:
    """Grouped or stacked bar Chart.js config.

    Stacked mode (#72) sets scales.stacked so signed segment values stack —
    negatives render below the zero baseline instead of being absorbed.
    """
    labels, series, rows, point_colors = _bar_matrix(slide)
    if not labels or not rows:
        return None
    cfg = _chart_config(slide)
    palette = _series_colors(cfg)
    datasets = []
    for si, name in enumerate(series):
        data = [row[si] if si < len(row) else None for row in rows]
        color = palette[si % len(palette)]
        ds: dict[str, Any] = {
            "label": name,
            "data": data,
            "backgroundColor": color,
            "borderColor": color,
            "borderWidth": 0,
        }
        # Per-category colors for single-series highlight
        if len(series) == 1 and any(point_colors):
            ds["backgroundColor"] = [
                point_colors[i] or color for i in range(len(labels))
            ]
        datasets.append(ds)
    _apply_bar_density_knobs(datasets, cfg)
    typo, auto_plan = typography_with_auto(
        slide,
        "stacked_bar_chart" if stacked else "grouped_bar_chart",
        chart_cfg=cfg,
        host_w=900,
        host_h=480,
    )
    options = _chartjs_common_options(cfg, typo=typo, auto_plan=auto_plan)
    if stacked:
        options["scales"]["x"]["stacked"] = True
        options["scales"]["y"]["stacked"] = True
        neg_min = min(
            (v for row in rows for v in row if isinstance(v, (int, float)) and v < 0),
            default=None,
        )
        # #96: domain clamps belong at scale ROOT — Chart.js 4 ignores
        # ticks.min/max. (Auto-domain previously masked this for negatives.)
        if auto_plan is None:
            if cfg.get("y_axis_min") is not None:
                options["scales"]["y"]["min"] = float(cfg["y_axis_min"])
            elif neg_min is not None:
                options["scales"]["y"]["min"] = float(neg_min) * 1.1
            if cfg.get("y_axis_max") is not None:
                options["scales"]["y"]["max"] = float(cfg["y_axis_max"])
        column = _side_column_geometry(cfg, strict="side_callout" in cfg)
        if cfg.get("exterior_segment_names") and column:
            # N5 (v4 sim): exterior segment-name column — series names in
            # their segment color, aligned to the last bar's segment
            # mid-heights right of the plot (PDF funding-board recipe).
            # Painted by the shell's segmentNames inline plugin (JSON can't
            # carry draw functions); the names replace the legend. Light
            # segment colors (e.g. #B8BFC9 gray) fall back to dark slate —
            # the PDF draws those names dark for readability.
            def _name_color(color: str) -> str:
                # palette entries may be CSS var() exprs — use the hex
                # fallback inside for the luminance check, keep the var()
                # for paint so theming still flows through.
                probe = color
                if "var(" in color and "#" in color:
                    probe = color[color.index("#"):].rstrip(") ").split(",")[0]
                h = probe.lstrip("#")[:6]
                try:
                    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
                except ValueError:
                    return _NAVY_SOFT
                # relative luminance; > 0.55 is too light on card backgrounds
                lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
                return color if lum <= 0.55 else _NAVY_SOFT

            options["plugins"]["legend"]["display"] = False
            # N5/T2: measured against the PDF (slide 27 board, 960pt deck):
            # bar width already matches (144px vs 140px-equiv) — the real
            # gap is the name column's typography (12px vs ~20px-equiv font,
            # 8px vs ~27px offset, 100px vs ~117px gutter). Opt-in knobs
            # below; absent keys keep today's shell hardcodes so existing
            # decks stay byte-identical (SC-COMPAT-1).
            _offset, gutter = column
            options["layout"] = {"padding": {"right": gutter}}
            seg_opts: dict[str, Any] = {}
            for key, knob in (
                ("fontSize", "segment_name_font_size"),
                ("lineHeight", "segment_name_line_height"),
                ("wrapChars", "segment_name_wrap_chars"),
                ("maxLines", "segment_name_max_lines"),
                ("offset", "segment_name_offset"),
            ):
                value = cfg.get(knob)
                if "side_callout" not in cfg:
                    if value is not None:
                        seg_opts[key] = int(value)
                elif (
                    value is not None
                    and not isinstance(value, bool)
                    and isinstance(value, (int, float))
                    and math.isfinite(value)
                ):
                    seg_opts[key] = int(value)
            options["plugins"]["segmentNames"] = {
                **seg_opts,
                "items": [
                    {
                        "label": str(name),
                        "color": _name_color(palette[si % len(palette)]),
                    }
                    for si, name in enumerate(series)
                ]
            }
    else:
        # Grouped bars honour the declared domain too (#96: scale root).
        # Without this the auto-domain drifts from y_axis_min/max and
        # value-anchored overlays (callouts) pin off-plot.
        groups = cfg.get("bar_groups")
        if isinstance(groups, (list, tuple)) and groups:
            items = []
            for group in groups:
                if not isinstance(group, Mapping):
                    items = []
                    break
                label = group.get("label")
                start = group.get("start")
                end = group.get("end")
                if (
                    not isinstance(label, str)
                    or not label.strip()
                    or isinstance(start, bool)
                    or isinstance(end, bool)
                    or not isinstance(start, int)
                    or not isinstance(end, int)
                    or start < 0
                    or end < start
                    or end >= len(labels)
                ):
                    items = []
                    break
                items.append({"label": label, "start": start, "end": end})
            if items:
                padding = options.setdefault("layout", {}).setdefault("padding", {})
                padding["top"] = max(int(padding.get("top") or 0), 28)
                options["plugins"]["barGroups"] = {"items": items}
        if cfg.get("y_axis_min") is not None:
            options["scales"]["y"]["min"] = float(cfg["y_axis_min"])
        if cfg.get("y_axis_max") is not None:
            options["scales"]["y"]["max"] = float(cfg["y_axis_max"])
    _apply_semantic_zero_line(options, datasets, axis="y")
    if stacked and (cfg.get("stack_totals") or cfg.get("point_labels") or cfg.get("show_point_labels")):
        # #101/N3: per-category signed totals painted above each stack via
        # the top segment's datalabel; negatives render parenthesized (IR).
        unit = str(cfg.get("y_axis_unit") or "")

        def _fmt_value(v: float) -> str:
            return _fmt_value_label(v, unit)

        total_matrix: list[list[str]] | None = None
        if cfg.get("stack_totals"):
            # F11+: explicit per-category total labels win over computed sums
            # — IR 100%-mix boards carry totals in a DIFFERENT unit than the
            # segments (PDF: 72/21/7 percents inside, $210/$219 above).
            explicit = cfg.get("stack_total_labels")
            if isinstance(explicit, (list, tuple)) and explicit:
                totals: list[Any] = [
                    str(explicit[ci]) if ci < len(explicit) else ""
                    for ci in range(len(labels))
                ]
            else:
                # rows are per-category lists of series values
                totals = [
                    sum(v for v in row if isinstance(v, (int, float))) for row in rows
                ]
            total_matrix = [[""] * len(labels) for _ in series]
            for ci, (row, total) in enumerate(zip(rows, totals)):
                # paint the total on the highest *positive* segment so it sits
                # at the stack top even when the top series is negative (RR).
                top_si = 0
                for si in range(len(series) - 1, -1, -1):
                    v = row[si] if si < len(row) else None
                    if isinstance(v, (int, float)) and v > 0:
                        top_si = si
                        break
                total_matrix[top_si][ci] = (
                    total if isinstance(total, str) else _fmt_value(total)
                )
        seg_matrix: list[list[str]] | None = None
        chip_matrix: list[list[str]] | None = None
        if cfg.get("point_labels") or cfg.get("show_point_labels"):
            # N4: in-segment per-series values, white centered inside each
            # segment — paintable simultaneously with totals (dual sets).
            #
            # N3 residual (IR signed-paren pairing): negatives that are THIN
            # in pixels can't host an inside label — the PDF moves those to a
            # navy chip just below the below-axis segment (thick negatives
            # keep the white-inside recipe). Estimated from the data domain;
            # ~16px is the smallest sliver that fits an 11px label.
            est_top = (
                float(cfg["y_axis_max"]) if cfg.get("y_axis_max") is not None
                else max(
                    (sum(v for v in row if isinstance(v, (int, float)) and v > 0)
                     for row in rows),
                    default=0.0,
                )
            )
            est_bottom = (
                float(cfg["y_axis_min"]) if cfg.get("y_axis_min") is not None
                else min(0.0, (neg_min or 0.0) * 1.1)
            )
            span = max(est_top - est_bottom, 1e-9)

            def _thin_negative(v: Any) -> bool:
                return (
                    isinstance(v, (int, float)) and v < 0
                    and abs(v) / span * 380 < 16
                )

            seg_matrix = [
                [
                    _fmt_value(row[si])
                    if si < len(row) and isinstance(row[si], (int, float))
                    and not _thin_negative(row[si])
                    else ""
                    for row in rows
                ]
                for si in range(len(series))
            ]
            chips = [
                [
                    _fmt_value(row[si])
                    if si < len(row) and _thin_negative(row[si])
                    else ""
                    for row in rows
                ]
                for si in range(len(series))
            ]
            if any(cell for chip_row in chips for cell in chip_row):
                chip_matrix = chips
        if total_matrix is not None:
            # F11+: totals paint ABOVE the stack — on 100%-domain boards the
            # stack top equals the axis max, so datalabels' default clip to
            # the plot area would hide them. Unclip and reserve headroom.
            layout = options.setdefault("layout", {})
            padding = layout.setdefault("padding", {})
            padding["top"] = max(int(padding.get("top") or 0), 22)
        if seg_matrix is not None and neg_min is not None:
            # N3 residual: below-axis signed labels (($73)/($24), IR) sit at
            # the negative segment's center — near the plot bottom on thin
            # releases, where the default clip cuts them off. Unclip and
            # reserve bottom headroom.
            layout = options.setdefault("layout", {})
            padding = layout.setdefault("padding", {})
            padding["bottom"] = max(int(padding.get("bottom") or 0), 20)
        value_set = _datalabels_cfg(
            anchor="center", align="center", offset=0,
            color=_WHITE, size=11, labels=seg_matrix,
        )
        if neg_min is not None:
            value_set = {**value_set, "clip": False}
        if chip_matrix is not None:
            chip_set = {
                **_datalabels_cfg(
                    anchor="end", align="bottom", offset=2,
                    color=_NAVY, size=11, labels=chip_matrix,
                ),
                "clip": False,
            }
        if total_matrix is not None and seg_matrix is not None:
            # N4 dual paint: named label sets so totals (navy, above) and
            # segment values (white, inside) render at once.
            label_sets: dict[str, Any] = {
                "value": value_set,
                "total": {
                    **_datalabels_cfg(
                        anchor="end", align="top", offset=2,
                        color=_NAVY, size=12, labels=total_matrix,
                    ),
                    "clip": False,
                },
            }
            if chip_matrix is not None:
                label_sets["negchip"] = chip_set
            options["plugins"]["datalabels"] = {
                "display": True,
                "labels": label_sets,
            }
        elif total_matrix is not None:
            options["plugins"]["datalabels"] = {
                **_datalabels_cfg(
                    anchor="end", align="top", offset=2, color=_NAVY, size=12,
                    labels=total_matrix,
                ),
                "clip": False,
            }
        elif chip_matrix is not None:
            options["plugins"]["datalabels"] = {
                "display": True,
                "labels": {
                    "value": value_set,
                    "negchip": chip_set,
                },
            }
        else:
            options["plugins"]["datalabels"] = value_set
    elif (
        not stacked
        and (cfg.get("point_labels") or cfg.get("show_point_labels"))
        and not (auto_plan is not None and auto_plan.datalabels_suppressed)
    ):
        # T14: grouped/plain bars honour point_labels too — above-bar value
        # labels (line-path recipe), same unit formatter as stacked/line.
        unit = str(cfg.get("y_axis_unit") or "")
        pos = str(cfg.get("y_axis_unit_position") or "")
        label_matrix = [
            [
                _fmt_value_label(row[si], unit, pos)
                if si < len(row) and isinstance(row[si], (int, float))
                else ""
                for row in rows
            ]
            for si in range(len(series))
        ]
        dl_size = ordinary_datalabel_size(typo)
        options["plugins"]["datalabels"] = _datalabels_cfg(
            anchor="end", align="top", offset=2, color=_NAVY_SOFT, size=dl_size,
            labels=label_matrix,
        )
    return {
        "type": "bar",
        "data": {"labels": labels, "datasets": datasets},
        "options": options,
    }



def _chartjs_hbar_config(slide: Mapping[str, Any]) -> dict[str, Any] | None:
    """Horizontal grouped bars — the anniversary retention board shape (#88).

    Chart.js canonical: ``indexAxis: "y"`` so bars run horizontally; the
    value axis is then ``x``. The anniversary window comes from the existing
    ``y_axis_break`` / ``y_axis_min`` / ``y_axis_max`` config (clamps the x
    domain, e.g. 90–100), and ``bar_labels_inside`` paints category
    labels (or, in ``"series"`` mode, series-name chips anchored at the
    bar's end edge) inside each bar via the datalabels plugin.
    """
    labels, series, rows, _pc = _bar_matrix(slide)
    if not labels or not rows:
        return None
    cfg = _chart_config(slide)
    palette = _series_colors(cfg)
    datasets = []
    for si, name in enumerate(series):
        color = palette[si % len(palette)]
        datasets.append(
            {
                "label": name,
                "data": [row[si] if si < len(row) else None for row in rows],
                "backgroundColor": color,
                "borderColor": color,
                "borderWidth": 0,
            }
        )
    _apply_bar_density_knobs(datasets, cfg)
    typo, auto_plan = typography_with_auto(
        slide, "horizontal_bar_chart", chart_cfg=cfg, host_w=960, host_h=540
    )
    options = _chartjs_common_options(cfg, typo=typo, auto_plan=auto_plan, horizontal=True)
    options["indexAxis"] = "y"
    x_scale = options["scales"]["x"]
    y_break = cfg.get("y_axis_break")
    # #96: scale-root min/max — tick-level values are ignored by Chart.js,
    # which is why the 90–100 anniversary window never painted in v3.
    if cfg.get("y_axis_min") is not None:
        x_scale["min"] = float(cfg["y_axis_min"])
    elif isinstance(y_break, dict) and y_break.get("to") is not None:
        # Discontinuous high window (e.g. 90–100): exclude the break band.
        x_scale["min"] = float(y_break["to"])
    if cfg.get("y_axis_max") is not None:
        x_scale["max"] = float(cfg["y_axis_max"])
    bli = cfg.get("bar_labels_inside")
    if bli:
        # #98/N2: "category" (== legacy true) paints the category matrix;
        # "series" paints each dataset's series name inside its bars
        # (PDF retention board years).
        source = "category" if bli is True else str(bli)
        if source == "category":
            label_matrix = [[str(lab) for lab in labels] for _ in series]
            dl_anchor, dl_align, dl_offset, dl_size = "start", "start", 4, 11
        elif source == "series":
            label_matrix = [[str(name)] * len(labels) for name in series]
            # N2 residual (v4 sim): PDF year chips sit at the RIGHT end,
            # inside the bar, at IR weight. anchor=end + align=start is
            # Chart.js-datalabels for "inside, at the bar's end edge".
            # V5/N2 weight polish: 14px — 13 still read light vs the PDF chips.
            dl_anchor, dl_align, dl_offset, dl_size = "end", "start", 6, 14
        else:
            raise ValueError(
                f"bar_labels_inside must be true, 'category', or 'series'; "
                f"got {bli!r}"
            )
        options["plugins"]["datalabels"] = _datalabels_cfg(
            anchor=dl_anchor, align=dl_align, offset=dl_offset, color=_WHITE,
            size=dl_size, labels=label_matrix,
        )
    _apply_semantic_zero_line(options, datasets, axis="x")
    return {
        "type": "bar",
        "data": {"labels": labels, "datasets": datasets},
        "options": options,
    }



def _chartjs_line_config(slide: Mapping[str, Any]) -> dict[str, Any] | None:
    """Chart.js line config honoring the IR chart_config contract (#71).

    Chart.js is canonical for IR house style; honors the same fields the SVG
    painter reads (y_axis_*, series_names/styles/colors, annotation, point_labels)
    plus minimal additions force_ticks / point_labels. SVG stays static fallback.
    """
    points = _line_data(slide)
    if not points:
        return None
    cfg = _chart_config(slide)
    labels = [str(p.get("label") or "") for p in points]
    series_names = cfg.get("series_names") or []
    series_styles = cfg.get("series_styles") or []
    series_colors = cfg.get("series_colors")
    if not isinstance(series_colors, (list, tuple)):
        series_colors = None
    # primary series
    series_keys = ["value"]
    for p in points:
        for k in p:
            if k.startswith("series_") and k not in series_keys:
                series_keys.append(k)
    y_unit = cfg.get("y_axis_unit", "%")
    unit_pos = cfg.get("y_axis_unit_position", "suffix")
    point_labels = bool(cfg.get("point_labels"))

    def _style_for(si: int) -> str:
        """IR default: secondary series (si>=1) dashed unless 'solid'."""
        if si == 0:
            return "solid"
        if si < len(series_styles) and series_styles[si] == "solid":
            return "solid"
        return "dashed"

    datasets = []
    label_matrix: list[list[str]] = []
    for si, key in enumerate(series_keys):
        color = (
            str(series_colors[si])
            if series_colors and si < len(series_colors) and series_colors[si]
            else _series_color(si)
        )
        data = []
        for p in points:
            if key == "value":
                data.append(p.get("value"))
            else:
                data.append(p.get(key))
        name = (
            str(series_names[si])
            if si < len(series_names) and series_names[si]
            else ("Value" if key == "value" else key.replace("series_", "S"))
        )
        ds: dict[str, Any] = {
            "label": name,
            "data": data,
            "borderColor": color,
            "backgroundColor": color,
            "tension": 0.15,
            "pointRadius": 4,
            "fill": False,
        }
        if _style_for(si) == "dashed":
            ds["borderDash"] = [8, 4]
        if point_labels:
            # IR on-point labels (#84): pre-formatted label matrix consumed by
            # the vendored datalabels plugin via the shell's formatter wiring
            # (Chart.js's own `pointLabels` option is radial-scale-only and is
            # ignored on cartesian line charts, so it is deliberately NOT used).
            label_matrix.append(
                [
                    _fmt_unit(v, y_unit, unit_pos)
                    if isinstance(v, (int, float))
                    else ""
                    for v in data
                ]
            )
        datasets.append(ds)

    typo, auto_plan = typography_with_auto(
        slide, "line_chart", chart_cfg=cfg, host_w=900, host_h=480
    )
    options = _chartjs_common_options(cfg, typo=typo, auto_plan=auto_plan)
    y_scale = options["scales"]["y"]
    # Axis domain: explicit min/max, or forced ticks (0/5/10/15 rails).
    # A y_axis_break {from, to} (#79/F10) renders a discontinuous axis by
    # clamping the effective domain to [to, max] — the break band is excluded.
    y_break = cfg.get("y_axis_break")
    if cfg.get("force_ticks") and isinstance(cfg.get("y_axis_ticks"), list):
        ticks = [float(t) for t in cfg["y_axis_ticks"]]
        if len(ticks) >= 2:
            # #96: min/max at scale root; stepSize is a valid ticks option.
            y_scale["min"] = ticks[0]
            y_scale["max"] = ticks[-1]
            y_scale["ticks"]["stepSize"] = ticks[1] - ticks[0]
    else:
        if cfg.get("y_axis_min") is not None:
            y_scale["min"] = float(cfg["y_axis_min"])
        if cfg.get("y_axis_max") is not None:
            y_scale["max"] = float(cfg["y_axis_max"])
    if cfg.get("y_axis_label"):
        y_scale["title"] = {"display": True, "text": str(cfg["y_axis_label"])}
    if isinstance(y_break, dict) and y_break.get("to") is not None:
        # Exclude the break band from the effective domain (#96: scale root).
        y_scale["min"] = float(y_break["to"])
        if cfg.get("y_axis_max") is not None:
            y_scale["max"] = float(cfg["y_axis_max"])
        y_scale["axisBreak"] = {"from": float(y_break.get("from", 0)), "to": float(y_break["to"])}
    if auto_plan is not None:
        apply_plan_to_chartjs_options(options, auto_plan)
    if point_labels and not (auto_plan is not None and auto_plan.datalabels_suppressed):
        dl_size = ordinary_datalabel_size(typo)
        options["plugins"]["datalabels"] = _datalabels_cfg(
            anchor="end", align="top", offset=2, color=_NAVY_SOFT, size=dl_size,
            labels=label_matrix,
        )
    _apply_semantic_zero_line(options, datasets, axis="y")
    return {
        "type": "line",
        "data": {"labels": labels, "datasets": datasets},
        "options": options,
    }



def _chartjs_combo_config(slide: Mapping[str, Any]) -> dict[str, Any] | None:
    bar_labels, bar_series, bar_rows, _bar_colors = _combo_bar_data(slide)
    if not bar_rows:
        return None
    datasets: list[dict[str, Any]] = []
    for si, name in enumerate(bar_series):
        color = _series_color(si)
        data = [row[si] if si < len(row) else None for row in bar_rows]
        datasets.append(
            {
                "type": "bar",
                "label": name,
                "data": data,
                "backgroundColor": color,
                "borderColor": color,
                "order": 2,
            }
        )
    line_points = _combo_line_data(slide)
    if line_points:
        line_data = _align_overlay_to_labels(bar_labels, line_points)
        vs = slide.get("visual_spec") or {}
        overlay = vs.get("line_overlay") or {}
        line_label = str(overlay.get("label") or "Overlay") if isinstance(overlay, dict) else "Overlay"
        line_color = (
            str(overlay.get("color")) if isinstance(overlay, dict) and overlay.get("color") else "#00175a"
        )
        # CSS vars not valid in canvas — coerce common Boardroom vars
        if line_color.startswith("var("):
            line_color = "#00175a"
        line_dataset: dict[str, Any] = {
            "type": "line",
            "label": line_label,
            "data": line_data,
            "borderColor": line_color,
            "backgroundColor": line_color,
            "tension": 0.15,
            "pointRadius": 4,
            "order": 1,
        }
        if not isinstance(overlay, Mapping) or overlay.get("dual_axis", True) is not False:
            line_dataset["yAxisID"] = "y1"
        datasets.append(line_dataset)
    cfg = _chart_config(slide)
    _apply_bar_density_knobs(datasets, cfg)
    typo, auto_plan = typography_with_auto(
        slide, "combo_chart", chart_cfg=cfg, host_w=900, host_h=480
    )
    options = _chartjs_common_options(cfg, typo=typo, auto_plan=auto_plan)
    if line_points:
        vs = slide.get("visual_spec") or {}
        overlay = vs.get("line_overlay") or {}
        if not isinstance(overlay, Mapping) or overlay.get("dual_axis", True) is not False:
            y1: dict[str, Any] = {
                "position": "right",
                "grid": {"display": False},
                "ticks": {
                    "color": "#00175a",
                    "font": {"family": "'Source Sans 3', sans-serif", "size": typo["y_tick_font_size"]},
                },
            }
            if isinstance(overlay, Mapping):
                if overlay.get("y_axis_min") is not None:
                    y1["min"] = float(overlay["y_axis_min"])
                if overlay.get("y_axis_max") is not None:
                    y1["max"] = float(overlay["y_axis_max"])
                if isinstance(overlay.get("y_axis_ticks"), list) and len(overlay["y_axis_ticks"]) >= 2:
                    ticks = [float(tick) for tick in overlay["y_axis_ticks"]]
                    y1["min"] = ticks[0]
                    y1["max"] = ticks[-1]
                    y1["ticks"]["stepSize"] = ticks[1] - ticks[0]
            options["scales"]["y1"] = y1
            if auto_plan is not None:
                apply_plan_to_chartjs_options(options, auto_plan)
    _apply_semantic_zero_line(options, datasets, axis="y")
    return {
        "type": "bar",
        "data": {"labels": bar_labels, "datasets": datasets},
        "options": options,
    }



def _build_chartjs_html(slide: Mapping[str, Any], layout: str) -> str:
    """Canvas + JSON config + noscript SVG fallback (library loaded in shell)."""
    import json as _json

    if layout == "stacked_bar_chart":
        cfg = _chartjs_bar_config(slide, stacked=True)
    elif layout == "horizontal_bar_chart":
        cfg = _chartjs_hbar_config(slide)
    else:
        builders = {
            "grouped_bar_chart": _chartjs_bar_config,
            "line_chart": _chartjs_line_config,
            "combo_chart": _chartjs_combo_config,
        }
        builder = builders.get(layout)
        if not builder:
            return ""
        cfg = builder(slide)
    if not cfg:
        return ""
    cid = _next_chart_id()
    chart_cfg = _chart_config(slide)
    # D4: serialize the callout geometry the calloutGeometry plugin needs,
    # built from the SAME post-merge list the DOM overlays render from, so
    # the two copies cannot drift.
    callouts = _merge_callout_bands(chart_cfg.get("callouts"))
    if isinstance(callouts, list) and callouts:
        items = [
            {k: c[k] for k in ("type", "from", "to", "at", "value")
             if c.get(k) is not None}
            for c in callouts
            if isinstance(c, dict) and str(c.get("type") or "") in _CALLOUT_TYPES
        ]
        if items:
            cfg.setdefault("options", {}).setdefault("plugins", {})["callouts"] = {
                "items": items
            }
    # N5/#138: shared-column side callout (HTML furniture, not a plugin).
    # Multi-panel hosts it on the tile (tile-local PDF offset); flag skips embed.
    side_callout_html = (
        ""
        if chart_cfg.get("_side_callout_external")
        else _build_side_callout_html(chart_cfg, layout)
    )
    payload = _json.dumps(cfg, ensure_ascii=False).replace("<", "\\u003c")
    bar_group_js = (
        _BAR_GROUP_PLUGIN_HTML
        if cfg.get("options", {}).get("plugins", {}).get("barGroups")
        else ""
    )
    svg_fb = _svg_fallback_for_layout(slide, layout, record_diagnostic=False)
    noscript = (
        f'<noscript>{"<style>[data-side-callout-html=wrap]{display:none}</style>" if side_callout_html else ""}{svg_fb}</noscript>'
        if svg_fb
        else ""
    )
    # Annotation callout marker (#71/F2): painted as a positioned div so the
    # text is present even if Chart.js annotation plugin is absent.
    ann_html = ""
    ann = chart_cfg.get("annotation")
    if isinstance(ann, dict) and ann.get("text"):
        a_text = str(ann["text"]).replace("\\n", "\n").replace("\n", " ")
        # T9/R5-D: declared x/y are PIXEL offsets within the plot area
        # (matching the SVG fallback painter's 960x540 frame, charts.py
        # _svg_* annotation block) — serialized for the calloutGeometry
        # plugin, which clamps the box inside chartArea. Non-numeric values
        # are dropped (fail closed: CSS fallback position).
        xy = ""
        ax, ay = ann.get("x"), ann.get("y")
        if isinstance(ax, (int, float)) and isinstance(ay, (int, float)):
            xy = f' data-x="{ax}" data-y="{ay}"'
        ann_html = (
            f'<div class="chartjs-annotation" data-for="{esc(cid)}"{xy}>'
            f"{esc(a_text)}</div>"
        )
    # Broken-axis glyph marker (#79/F10): present when y_axis_break is set.
    # On horizontal bars the break is on the x axis — vertical glyph (#88).
    break_html = ""
    yb = chart_cfg.get("y_axis_break")
    if isinstance(yb, dict) and yb.get("to") is not None:
        orient = " chartjs-axis-break-v" if layout == "horizontal_bar_chart" else ""
        break_html = (
            f'<div class="chartjs-axis-break{orient}" data-for="{esc(cid)}" '
            f'data-break-to="{esc(str(yb.get("to")))}"></div>'
        )
    # Geometric callouts (#89/R2): elbow arrows / chevrons / bands.
    callouts_html = _build_callout_overlays(
        callouts,
        len((cfg.get("data") or {}).get("labels") or []),
        cid,
        cfg,
        layout,
        chart_cfg,
    )
    # R1 (#94): chart_config.stage "flat" drops the Boardroom stage chrome so
    # the chart sits flatter against the canvas (IR stage-dominant style).
    flat = " chartjs-flat" if chart_cfg.get("stage") == "flat" else ""
    # N5: opt-in flex-fill so the wrap grows into the tile's dead space
    # (multi_panel tiles are flex columns; without this the plot height is
    # bounded by Chart.js' intrinsic sizing, leaving unused card below).
    fill = " chartjs-fill" if chart_cfg.get("fill_tile") else ""
    # #139: collision only on ordinary-label layouts when datalabel_font_size
    # is set; stacked/in-segment and named value sets stay untouched.
    host_w, host_h = chart_host_dimensions(layout)
    typo, auto_plan = typography_with_auto(
        slide, layout, chart_cfg=chart_cfg, host_w=host_w, host_h=host_h
    )
    collision = bool(typo.get("datalabel_font_size_set")) and uses_ordinary_datalabels(
        layout, chart_cfg
    )
    coll_attr = ' data-rv2-collision="1"' if collision else ""
    coll_js = DATALABEL_COLLISION_JS if collision else ""
    value_axis_visible = chart_cfg.get(
        "show_x_axis" if layout == "horizontal_bar_chart" else "show_y_axis"
    ) is not False
    auto_attrs = (
        plan_to_data_attrs(auto_plan, value_axis_visible=value_axis_visible)
        if auto_plan is not None
        else ""
    )
    if auto_plan is not None:
        record_auto_diagnostic(
            {**auto_plan.diagnostic_dict(), "slide_number": slide.get("slide_number")}
        )
    aria_label = f"{layout} chart{full_label_aria_suffix(auto_plan)}"
    return (
        f'<div class="chartjs-wrap{flat}{fill}" data-chartjs="1" '
        f'data-chart-layout="{esc(layout)}"{coll_attr}{auto_attrs}>'
        f'<canvas id="{esc(cid)}" class="chartjs-canvas" aria-label="{esc(aria_label)}"></canvas>'
        f'<script type="application/json" class="chartjs-config" data-for="{esc(cid)}">'
        f"{payload}</script>"
        f"{bar_group_js}"
        f"{ann_html}"
        f"{break_html}"
        f"{callouts_html}"
        f"{side_callout_html}"
        f"{noscript}"
        f"{coll_js}"
        f"</div>"
    )
