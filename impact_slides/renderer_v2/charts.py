"""Chart + icon_grid paint — soft-import live Boardroom pack, with pure fallbacks."""
from __future__ import annotations

import importlib.util
import math
import sys
import uuid
from pathlib import Path
from typing import Any, Mapping

from .strip import esc, strip_eids

_CHART_LAYOUTS = frozenset(
    {
        "grouped_bar_chart",
        "stacked_bar_chart",
        "waterfall_chart",
        "heatmap",
        "icon_grid",
        "line_chart",
        "combo_chart",
    }
)

_PACK = None
_PACK_CSS = ""


def _find_pack_path() -> Path | None:
    here = Path(__file__).resolve()
    # Prefer sibling live_sim relative to known realworld_test layout
    candidates = [
        Path.home()
        / "Documents"
        / "realworld_test"
        / "amex_thefork_acquisition"
        / "live_copilot_sim"
        / "_boardroom_charts_pack.py",
        here.parents[2]
        / "realworld_test"
        / "amex_thefork_acquisition"
        / "live_copilot_sim"
        / "_boardroom_charts_pack.py",
        Path(__file__).resolve().parent / "_vendor_charts_pack.py",
    ]
    # walk up for Impact_Slides parent
    for parent in [here.parents[i] for i in range(2, min(6, len(here.parents)))]:
        candidates.append(
            parent.parent
            / "realworld_test"
            / "amex_thefork_acquisition"
            / "live_copilot_sim"
            / "_boardroom_charts_pack.py"
        )
        candidates.append(
            parent
            / ".."
            / "realworld_test"
            / "amex_thefork_acquisition"
            / "live_copilot_sim"
            / "_boardroom_charts_pack.py"
        )
    for c in candidates:
        try:
            c = c.resolve()
        except OSError:
            continue
        if c.is_file():
            return c
    return None


def _load_pack():
    global _PACK, _PACK_CSS
    if _PACK is not None:
        return _PACK
    path = _find_pack_path()
    if not path:
        _PACK = False
        return None
    spec = importlib.util.spec_from_file_location("boardroom_charts_pack_v2", path)
    if not spec or not spec.loader:
        _PACK = False
        return None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["boardroom_charts_pack_v2"] = mod
    spec.loader.exec_module(mod)
    _PACK = mod
    _PACK_CSS = getattr(mod, "CHART_CSS", "") or ""
    return mod


def chart_css() -> str:
    _load_pack()
    return _PACK_CSS


def is_chart_layout(layout_type: str) -> bool:
    lt = (layout_type or "").lower().strip()
    if lt in _CHART_LAYOUTS:
        return True
    mod = _load_pack()
    if mod and hasattr(mod, "is_chart_layout"):
        try:
            return bool(mod.is_chart_layout(lt))
        except Exception:
            return False
    return False


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
    vs = slide.get("visual_spec") or {}
    if not isinstance(vs, dict):
        return []
    pv = vs.get("primary_visual") or {}
    if not isinstance(pv, dict):
        return []
    steps = pv.get("steps_or_data")
    return list(steps) if isinstance(steps, list) else []


# MVP Chart.js interactive set (P3). Other chart layouts stay on SVG/pack.
_CHARTJS_LAYOUTS = frozenset({"grouped_bar_chart", "line_chart", "combo_chart"})

# Boardroom series palette (semantic/brand — not Chart.js candy defaults).
_BOARDROOM_SERIES = (
    "#006fcf",  # blue / accent
    "#00175a",  # navy
    "#0a7d55",  # accent-2 success
    "#53565a",  # ink
    "#80c8ff",  # blue-sky
)


def build_chart_html(
    slide: Mapping[str, Any],
    layout: str,
    *,
    use_chartjs: bool = False,
) -> str:
    lt = (layout or slide.get("layout_type") or "").lower()
    if use_chartjs and lt in _CHARTJS_LAYOUTS:
        js_html = _build_chartjs_html(slide, lt)
        if js_html:
            return js_html
        # Fall through to SVG if config could not be built
    # Internal SVG painters (also used as Chart.js noscript fallback).
    svg = _svg_fallback_for_layout(slide, lt)
    if svg:
        return svg
    if lt == "stacked_bar_chart":
        return _build_stacked_bar_svg(slide)
    mod = _load_pack()
    s = dict(slide)
    s["layout_type"] = lt
    # External pack reads steps_or_data / key_stats / so_what at the TOP level
    # of the slide dict; our handoff nests them under visual_spec / content.
    # Bridge the two shapes so the pack can find the data.
    if not s.get("steps_or_data"):
        vs = s.get("visual_spec") or {}
        pv = vs.get("primary_visual") or {}
        s["steps_or_data"] = pv.get("steps_or_data") or []
    if not s.get("key_stats"):
        s["key_stats"] = (s.get("content") or {}).get("key_stats") or []
    # NOTE: so_what is deliberately NOT bridged — render_chart appends
    # insight_strip() itself; bridging would make the pack render a duplicate.
    if mod and hasattr(mod, "build_main"):
        try:
            html = mod.build_main(s, esc=esc, icon=_icon_svg)
            # Pack may legitimately report empty; use matrix fallback when face is empty.
            if html and "chart-empty" not in html and "<svg" in html:
                return html
            if html and "chart-empty" not in html and "heatmap" in lt:
                return html
            if html and "chart-empty" not in html and "icon" not in lt:
                # might still be meaningful non-svg (table-like)
                if len(html) > 80:
                    return html
        except Exception as e:  # pragma: no cover
            return f'<p class="chart-empty">Chart pack error: {esc(e)}</p>'
    return _fallback_matrix_chart(slide, lt)


def build_icon_grid_html(slide: Mapping[str, Any]) -> str:
    mod = _load_pack()
    s = dict(slide)
    s["layout_type"] = "icon_grid"
    # External pack reads steps_or_data / bullets at the TOP level of the
    # slide dict; our renderer nests them under visual_spec / content.
    # Bridge the two shapes so the external pack can find the data.
    if not s.get("steps_or_data"):
        vs = s.get("visual_spec") or {}
        pv = vs.get("primary_visual") or {}
        s["steps_or_data"] = pv.get("steps_or_data") or []
    if not s.get("bullets"):
        s["bullets"] = (s.get("content") or {}).get("bullets") or []
    if mod and hasattr(mod, "build_icon_grid_main"):
        try:
            result = mod.build_icon_grid_main(s, esc=esc, icon=_icon_svg)
            if "No icon-grid items" not in result:
                return result
        except Exception:
            pass
    if mod and hasattr(mod, "build_main"):
        try:
            result = mod.build_main(s, esc=esc, icon=_icon_svg)
            if "No icon-grid items" not in result:
                return result
        except Exception:
            pass
    return _fallback_icon_grid(slide)


def _fallback_icon_grid(slide: Mapping[str, Any]) -> str:
    tiles_src = _steps(slide)
    c = slide.get("content") or {}
    if not tiles_src:
        tiles_src = c.get("bullets") or []
    tiles = []
    icons = ["growth", "globe", "users", "building", "chart-bar", "layers"]
    for i, raw in enumerate(tiles_src[:6]):
        if isinstance(raw, dict):
            title = strip_eids(raw.get("title") or raw.get("label") or "")
            body = strip_eids(raw.get("body") or raw.get("text") or "")
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


# ---------------------------------------------------------------------------
# Line chart (internal SVG, zero external dependency)
# ---------------------------------------------------------------------------


def _chart_config(slide: Mapping[str, Any]) -> dict[str, Any]:
    """Extract optional chart configuration from visual_spec."""
    vs = slide.get("visual_spec") or {}
    if not isinstance(vs, dict):
        return {}
    cfg = vs.get("chart_config")
    return dict(cfg) if isinstance(cfg, dict) else {}


def _next_chart_id() -> str:
    """Stable-enough unique canvas id (no process-global counter)."""
    return f"rv2-chart-{uuid.uuid4().hex[:12]}"


def _series_color(index: int) -> str:
    return _BOARDROOM_SERIES[index % len(_BOARDROOM_SERIES)]


def _chartjs_common_options() -> dict[str, Any]:
    """Calm Boardroom defaults: no animation, readable axes."""
    return {
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
                    "font": {"family": "'Source Sans 3', sans-serif", "size": 13},
                },
                "grid": {"color": "rgba(224, 228, 234, 0.8)"},
            },
            "y": {
                "ticks": {
                    "color": "#00175a",
                    "font": {"family": "'IBM Plex Sans', sans-serif", "size": 13},
                },
                "grid": {"color": "rgba(224, 228, 234, 0.8)"},
            },
        },
    }


def _align_overlay_to_labels(
    bar_labels: list[str],
    line_points: list[dict[str, Any]],
) -> list[float | None]:
    """Map overlay points onto bar categories by label only (no silent index pad).

    When no labels match, fall back to positional values only if lengths match
    exactly; otherwise leave unmatched categories as None.
    """
    by_label = {str(p.get("label") or ""): p.get("value") for p in line_points}
    line_data = [by_label.get(lbl) for lbl in bar_labels]
    if any(v is not None for v in line_data):
        return line_data
    if len(line_points) == len(bar_labels):
        return [p.get("value") for p in line_points]
    # Lengths differ and no label hits — refuse to invent alignment.
    return [None] * len(bar_labels)


def _chartjs_bar_config(slide: Mapping[str, Any]) -> dict[str, Any] | None:
    labels, series, rows, point_colors = _bar_matrix(slide)
    if not labels or not rows:
        return None
    datasets = []
    for si, name in enumerate(series):
        data = [row[si] if si < len(row) else None for row in rows]
        color = _series_color(si)
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
    cfg = {"type": "bar", "data": {"labels": labels, "datasets": datasets}, "options": _chartjs_common_options()}
    return cfg


def _chartjs_line_config(slide: Mapping[str, Any]) -> dict[str, Any] | None:
    points = _line_data(slide)
    if not points:
        return None
    labels = [str(p.get("label") or "") for p in points]
    # primary series
    series_keys = ["value"]
    for p in points:
        for k in p:
            if k.startswith("series_") and k not in series_keys:
                series_keys.append(k)
    datasets = []
    for si, key in enumerate(series_keys):
        color = _series_color(si)
        data = []
        for p in points:
            if key == "value":
                data.append(p.get("value"))
            else:
                data.append(p.get(key))
        datasets.append(
            {
                "label": "Value" if key == "value" else key.replace("series_", "S"),
                "data": data,
                "borderColor": color,
                "backgroundColor": color,
                "tension": 0.15,
                "pointRadius": 4,
                "fill": False,
            }
        )
    return {
        "type": "line",
        "data": {"labels": labels, "datasets": datasets},
        "options": _chartjs_common_options(),
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
        datasets.append(
            {
                "type": "line",
                "label": line_label,
                "data": line_data,
                "borderColor": line_color,
                "backgroundColor": line_color,
                "tension": 0.15,
                "pointRadius": 4,
                "order": 1,
                "yAxisID": "y",
            }
        )
    options = _chartjs_common_options()
    return {
        "type": "bar",
        "data": {"labels": bar_labels, "datasets": datasets},
        "options": options,
    }


def _svg_fallback_for_layout(slide: Mapping[str, Any], layout: str) -> str:
    """Static SVG painter for a Chart.js MVP layout (JS-off / noscript path)."""
    if layout == "line_chart":
        return _build_line_chart_svg(slide)
    if layout == "combo_chart":
        return _build_combo_chart_svg(slide)
    if layout == "grouped_bar_chart":
        return _build_grouped_bar_svg(slide)
    return ""


def _build_chartjs_html(slide: Mapping[str, Any], layout: str) -> str:
    """Canvas + JSON config + noscript SVG fallback (library loaded in shell)."""
    import json as _json

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
    payload = _json.dumps(cfg, ensure_ascii=False)
    svg_fb = _svg_fallback_for_layout(slide, layout)
    noscript = f"<noscript>{svg_fb}</noscript>" if svg_fb else ""
    return (
        f'<div class="chartjs-wrap" data-chartjs="1" data-chart-layout="{esc(layout)}">'
        f'<canvas id="{esc(cid)}" class="chartjs-canvas" aria-label="{esc(layout)} chart"></canvas>'
        f'<script type="application/json" class="chartjs-config" data-for="{esc(cid)}">'
        f"{payload}</script>"
        f"{noscript}"
        f"</div>"
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


def _build_line_chart_svg(slide: Mapping[str, Any]) -> str:
    """Build an SVG line chart for the given slide.

    Single-series: solid navy line with circle data points and data labels.
    Uses viewBox 0 0 900 480 for stage containment.
    """
    points = _line_data(slide)
    if not points:
        return '<p class="chart-empty">No line chart data</p>'

    cfg = _chart_config(slide)
    show_grid = bool(cfg.get("gridlines", True))
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

    # Y-axis gridlines and tick labels
    for tick in y_ticks:
        ty = y_pos(tick)
        if show_grid:
            parts.append(
                f'<line x1="{pad_l}" y1="{ty:.1f}" x2="{W - pad_r}" y2="{ty:.1f}" '
                f'stroke="var(--panel-border, #d8dce3)" stroke-width="0.5"/>'
            )
        tick_label = _fmtu(tick)
        parts.append(
            f'<text x="{pad_l - 10}" y="{ty + 5:.1f}" text-anchor="end" '
            f'fill="var(--navy, #00175a)" font-size="14" font-weight="600" '
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
        parts.append(
            f'<text x="{x_pos(i):.1f}" y="{H - pad_b + 25}" text-anchor="middle" '
            f'fill="var(--navy, #00175a)" font-size="14" font-weight="600" '
            f'font-family="var(--font-body, sans-serif)">{esc(p["label"])}</text>'
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
        parts.append(
            f'<text x="{l_x:.1f}" y="{ly:.1f}" text-anchor="{l_anchor}" '
            f'fill="var(--navy, #00175a)" font-size="14" font-weight="600" '
            f'font-family="var(--font-body, sans-serif)">{esc(_fmtu(p["value"]))}</text>'
        )

    # Data labels for secondary series
    if len(all_series) > 1:
        for sk_entry in all_series[1:]:
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
                parts.append(
                    f'<text x="{l_x:.1f}" y="{ly:.1f}" text-anchor="{l_anchor}" '
                    f'fill="var(--ink-muted, #63666a)" font-size="12" '
                    f'font-family="var(--font-body, sans-serif)">{esc(_fmtu(p[sk]))}</text>'
                )

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
        ax = float(annotation.get("x", W * 0.25))
        ay = float(annotation.get("y", H * 0.2))
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
    show_grid = bool(cfg.get("gridlines", True))
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

    # Y-axis gridlines (based on bar axis)
    bar_ticks = cfg.get("y_axis_ticks")
    if bar_ticks is None:
        step = bar_max / 4
        if step >= 5:
            step = int(step)
        bar_ticks = [bar_min + i * step for i in range(5)]
    for tick in bar_ticks:
        ty = bar_y(float(tick))
        if show_grid:
            parts.append(
                f'<line x1="{pad_l}" y1="{ty:.1f}" x2="{W - pad_r}" y2="{ty:.1f}" '
                f'stroke="var(--panel-border, #d8dce3)" stroke-width="0.5"/>'
            )
        tick_label = _fmtb(float(tick))
        parts.append(
            f'<text x="{pad_l - 10}" y="{ty + 5:.1f}" text-anchor="end" '
            f'fill="var(--navy, #00175a)" font-size="14" font-weight="600" '
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
            ty = line_y(float(tick))
            tick_label = f"{tick:g}{line_unit}" if line_unit else f"{tick:g}"
            parts.append(
                f'<text x="{W - pad_r + 10}" y="{ty + 5:.1f}" text-anchor="start" '
                f'fill="var(--navy, #00175a)" font-size="14" font-weight="600" '
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
        parts.append(
            f'<text x="{x + bar_w/2:.1f}" y="{H - pad_b + 25}" text-anchor="middle" '
            f'fill="var(--navy, #00175a)" font-size="14" font-weight="600" '
            f'font-family="var(--font-body, sans-serif)">{esc(lab)}</text>'
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


# ----------------------------------------------------------------------
# Internal vertical bar charts (grouped + stacked)
# ----------------------------------------------------------------------

_BAR_SERIES_COLORS = [
    "var(--navy, #00175a)",
    "var(--blue, #006fcf)",
    "var(--blue-sky, #80c8ff)",
    "var(--ink-muted, #63666a)",
]


def _series_colors(cfg: Mapping[str, Any]) -> list[str]:
    """Series color palette: chart_config.series_colors or the defaults."""
    custom = cfg.get("series_colors")
    if isinstance(custom, (list, tuple)) and custom:
        return [str(c) for c in custom if c] or list(_BAR_SERIES_COLORS)
    return list(_BAR_SERIES_COLORS)


def _fmt_unit(v: float, unit: str, pos: str = "suffix") -> str:
    """Format a value with its unit.

    Currency shorthand: a unit starting with ``$`` renders as a prefix
    (``$`` -> ``$1.6``, ``$B`` -> ``$1.6B``) regardless of ``pos``.
    """
    if not unit:
        return f"{v:g}"
    if pos == "prefix":
        return f"{unit}{v:g}"
    if unit.startswith("$"):
        return f"${v:g}{unit[1:]}"
    return f"{v:g}{unit}"


def _bar_num(v: Any) -> float | None:
    try:
        return float(str(v).replace("%", "").replace(",", "").replace("$", "").strip())
    except (ValueError, TypeError):
        return None


def _fmt_bar(v: float, unit: str = "") -> str:
    s = f"{v:,.0f}" if abs(v) >= 1000 else f"{v:g}"
    if not unit:
        return s
    if unit.startswith("$"):
        return f"${s}{unit[1:]}"
    return f"{s}{unit}"


def _nice_max(raw: float) -> float:
    if raw <= 0:
        return 1.0
    exp = math.floor(math.log10(raw))
    base = 10**exp
    for m in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if raw <= m * base:
            return float(m * base)
    return float(10 * base)


def _nice_step(raw: float) -> float:
    """Round a tick step to a clean 1/2/2.5/5 number."""
    if raw <= 0:
        return 1.0
    exp = math.floor(math.log10(raw))
    base = 10**exp
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * base:
            return float(m * base)
    return float(10 * base)


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
) -> list[str]:
    """Emit SVG open + gridlines + axes + legend."""
    show_grid = bool(cfg.get("gridlines", True))
    geom = chart_geometry("_vertical_bar")
    W, H = geom["width"], geom["height"]
    pad_l, pad_r, pad_t, pad_b = geom["pad_l"], geom["pad_r"], _vbar_pad_t(cfg, series), 56
    plot_h = H - pad_t - pad_b
    unit = cfg.get("y_axis_unit", "")

    def y_pos(v: float) -> float:
        rng = y_max - y_min
        if rng == 0:
            return pad_t + plot_h / 2
        return pad_t + plot_h - ((v - y_min) / rng) * plot_h

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
            f'fill="var(--navy, #00175a)" font-size="14" font-weight="600" '
            f'font-family="var(--font-body, sans-serif)">{esc(_fmt_bar(tick, unit))}</text>'
        )
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

    parts.extend(_bar_group_brackets(cfg, labels, pad_l, slot, pad_t - 22))

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
            parts.append(
                f'<text x="{x + (bar_w - 4) / 2:.1f}" y="{label_y:.1f}" text-anchor="middle" '
                f'fill="var(--navy, #00175a)" font-size="14" font-weight="600" '
                f'font-family="var(--font-body, sans-serif)">{esc(_fmt_bar(v, unit))}</text>'
            )
        parts.append(
            f'<text x="{pad_l + i * slot + slot / 2:.1f}" y="{H - pad_b + 25}" '
            f'text-anchor="middle" fill="var(--navy, #00175a)" font-size="14" '
            f'font-weight="600" font-family="var(--font-body, sans-serif)">{esc(lab)}</text>'
        )

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
    pad_l, pad_r, pad_t, pad_b = geom["pad_l"], geom["pad_r"], _vbar_pad_t(cfg, series), 56
    plot_w = W - pad_l - pad_r
    plot_h = H - pad_t - pad_b
    unit = cfg.get("y_axis_unit", "")

    y_max, y_min, y_ticks = _bar_axes(cfg, max(pos_sums), min(neg_sums))

    def y_pos(v: float) -> float:
        rng = y_max - y_min
        if rng == 0:
            return pad_t + plot_h / 2
        return pad_t + plot_h - ((v - y_min) / rng) * plot_h

    parts = _vbar_frame("vbar-stacked", cfg, y_max, y_min, y_ticks, series)
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
        parts.append(
            f'<text x="{pad_l + i * slot + slot / 2:.1f}" y="{cat_y}" '
            f'text-anchor="middle" fill="var(--navy, #00175a)" font-size="14" '
            f'font-weight="600" font-family="var(--font-body, sans-serif)">{esc(lab)}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)
