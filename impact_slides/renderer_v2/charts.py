"""Chart + icon_grid paint — soft-import live Boardroom pack, with pure fallbacks."""
from __future__ import annotations

import importlib.util
import sys
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


def build_chart_html(slide: Mapping[str, Any], layout: str) -> str:
    lt = (layout or slide.get("layout_type") or "").lower()
    # Line charts are built internally (external pack has no line chart)
    if lt == "line_chart":
        return _build_line_chart_svg(slide)
    # Combo charts (bar + line overlay) are built internally
    if lt == "combo_chart":
        return _build_combo_chart_svg(slide)
    mod = _load_pack()
    s = dict(slide)
    s["layout_type"] = lt
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


def _build_line_chart_svg(slide: Mapping[str, Any]) -> str:
    """Build an SVG line chart for the given slide.

    Single-series: solid blue line with circle data points and data labels.
    Uses viewBox 0 0 900 480 for stage containment.
    """
    points = _line_data(slide)
    if not points:
        return '<p class="chart-empty">No line chart data</p>'

    cfg = _chart_config(slide)
    W, H = 900, 480
    pad_l, pad_r, pad_t, pad_b = 80, 40, 40, 60

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
        parts.append(
            f'<line x1="{pad_l}" y1="{ty:.1f}" x2="{W - pad_r}" y2="{ty:.1f}" '
            f'stroke="var(--panel-border, #d8dce3)" stroke-width="0.5"/>'
        )
        tick_label = f"{tick:g}{y_unit}" if y_unit else f"{tick:g}"
        parts.append(
            f'<text x="{pad_l - 10}" y="{ty + 5:.1f}" text-anchor="end" '
            f'fill="var(--ink-muted, #63666a)" font-size="14" '
            f'font-family="var(--font-body, sans-serif)">{esc(tick_label)}</text>'
        )

    # Y-axis line
    parts.append(
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{H - pad_b}" '
        f'stroke="var(--ink-muted, #63666a)" stroke-width="1"/>'
    )

    # X-axis line
    parts.append(
        f'<line x1="{pad_l}" y1="{H - pad_b}" x2="{W - pad_r}" y2="{H - pad_b}" '
        f'stroke="var(--ink-muted, #63666a)" stroke-width="1"/>'
    )

    # X-axis labels
    for i, p in enumerate(points):
        parts.append(
            f'<text x="{x_pos(i):.1f}" y="{H - pad_b + 25}" text-anchor="middle" '
            f'fill="var(--ink, #53565a)" font-size="14" font-weight="600" '
            f'font-family="var(--font-body, sans-serif)">{esc(p["label"])}</text>'
        )

    # Y-axis label (rotated)
    if y_label:
        parts.append(
            f'<text x="20" y="{pad_t + plot_h / 2:.0f}" text-anchor="middle" '
            f'transform="rotate(-90 20 {pad_t + plot_h / 2:.0f})" '
            f'fill="var(--ink-muted, #63666a)" font-size="13" '
            f'font-family="var(--font-body, sans-serif)">{esc(y_label)}</text>'
        )

    # -- Series definitions -----------------------------------------------
    # series_keys was collected above; build full series list
    all_series: list[dict[str, Any]] = [
        {"key": "value", "color": "var(--blue, #006fcf)", "dash": "", "width": 3},
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

    # Data labels for primary series only (avoid clutter)
    for i, p in enumerate(points):
        cx, cy = x_pos(i), y_pos(p["value"])
        label_text = f"{p['value']:g}{y_unit}" if y_unit else f"{p['value']:g}"
        parts.append(
            f'<text x="{cx:.1f}" y="{cy - 12:.1f}" text-anchor="middle" '
            f'fill="var(--ink, #53565a)" font-size="14" font-weight="600" '
            f'font-family="var(--font-body, sans-serif)">{esc(label_text)}</text>'
        )

    # Data labels for secondary series (below the line, muted)
    if len(all_series) > 1:
        for sk_entry in all_series[1:]:
            sk = sk_entry["key"]
            for i, p in enumerate(points):
                if sk not in p:
                    continue
                cx, cy = x_pos(i), y_pos(p[sk])
                label_text = f"{p[sk]:g}{y_unit}" if y_unit else f"{p[sk]:g}"
                parts.append(
                    f'<text x="{cx:.1f}" y="{cy + 18:.1f}" text-anchor="middle" '
                    f'fill="var(--ink-muted, #63666a)" font-size="12" '
                    f'font-family="var(--font-body, sans-serif)">{esc(label_text)}</text>'
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
        # Estimate box size from text length
        lines = a_text.split("\\n")
        box_w = max(len(l) for l in lines) * 7.5 + 20
        box_h = len(lines) * 18 + 16
        parts.append(
            f'<rect x="{ax - box_w/2:.0f}" y="{ay - box_h/2:.0f}" '
            f'width="{box_w:.0f}" height="{box_h:.0f}" rx="4" '
            f'fill="var(--panel, #eef0f0)" '
            f'stroke="var(--ink-muted, #63666a)" stroke-width="1" '
            f'stroke-dasharray="4,3"/>'
        )
        for li, line in enumerate(lines):
            parts.append(
                f'<text x="{ax:.0f}" y="{ay + (li - len(lines)/2 + 0.5) * 18 + 5:.0f}" '
                f'text-anchor="middle" fill="var(--ink, #53565a)" font-size="13" '
                f'font-family="var(--font-body, sans-serif)">{esc(line)}</text>'
            )

    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Combo chart (bar + line overlay, internal SVG)
# ---------------------------------------------------------------------------


def _combo_bar_data(slide: Mapping[str, Any]) -> tuple[list[str], list[float]]:
    """Parse bar chart labels and values from steps_or_data."""
    raw = _steps(slide)
    labels: list[str] = []
    values: list[float] = []
    for item in raw:
        if isinstance(item, dict):
            label = str(item.get("label") or item.get("x") or "")
            try:
                v = float(str(item.get("value") or item.get("y") or 0).replace("%", "").replace(",", "").replace("$", ""))
            except (ValueError, TypeError):
                continue
            labels.append(label)
            values.append(v)
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            try:
                v = float(str(item[1]).replace("%", "").replace(",", "").replace("$", ""))
            except (ValueError, TypeError):
                continue
            labels.append(str(item[0]))
            values.append(v)
        elif isinstance(item, str) and ":" in item:
            a, _, b = item.partition(":")
            try:
                v = float(b.replace("%", "").replace(",", "").replace("$", "").strip())
            except ValueError:
                continue
            labels.append(a.strip())
            values.append(v)
    return labels, values


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
    bar_labels, bar_values = _combo_bar_data(slide)
    line_points = _combo_line_data(slide)
    if not bar_values:
        return '<p class="chart-empty">No combo chart data</p>'

    vs = slide.get("visual_spec") or {}
    overlay_cfg = vs.get("line_overlay") or {}
    overlay_color = overlay_cfg.get("color", "var(--ink-muted, #63666a)")
    overlay_label = overlay_cfg.get("label", "")
    overlay_style = overlay_cfg.get("style", "solid")

    cfg = _chart_config(slide)
    W, H = 900, 480
    pad_l, pad_r, pad_t, pad_b = 80, 80 if line_points else 40, 40, 60

    bar_max = float(cfg.get("y_axis_max", max(bar_values) * 1.15 if bar_values else 10))
    bar_min = 0.0

    line_values = [p["value"] for p in line_points] if line_points else []
    line_max = float(overlay_cfg.get("y_axis_max", max(line_values) * 1.15 if line_values else 10))
    line_min = float(overlay_cfg.get("y_axis_min", 0))
    use_dual_axis = bool(line_points) and overlay_cfg.get("dual_axis", True)

    plot_w = W - pad_l - pad_r
    plot_h = H - pad_t - pad_b
    n_bars = len(bar_values)

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
        parts.append(
            f'<line x1="{pad_l}" y1="{ty:.1f}" x2="{W - pad_r}" y2="{ty:.1f}" '
            f'stroke="var(--panel-border, #d8dce3)" stroke-width="0.5"/>'
        )
        tick_label = f"{tick:g}{bar_unit}" if bar_unit else f"{tick:g}"
        parts.append(
            f'<text x="{pad_l - 10}" y="{ty + 5:.1f}" text-anchor="end" '
            f'fill="var(--ink-muted, #63666a)" font-size="14" '
            f'font-family="var(--font-body, sans-serif)">{esc(tick_label)}</text>'
        )

    # Left Y-axis
    parts.append(
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{H - pad_b}" '
        f'stroke="var(--ink-muted, #63666a)" stroke-width="1"/>'
    )

    # Right Y-axis (dual axis)
    if use_dual_axis and line_points:
        parts.append(
            f'<line x1="{W - pad_r}" y1="{pad_t}" x2="{W - pad_r}" y2="{H - pad_b}" '
            f'stroke="var(--ink-muted, #63666a)" stroke-width="1"/>'
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
                f'fill="var(--ink-muted, #63666a)" font-size="14" '
                f'font-family="var(--font-body, sans-serif)">{esc(tick_label)}</text>'
            )

    # X-axis line
    parts.append(
        f'<line x1="{pad_l}" y1="{H - pad_b}" x2="{W - pad_r}" y2="{H - pad_b}" '
        f'stroke="var(--ink-muted, #63666a)" stroke-width="1"/>'
    )

    # Bars
    for i, (lab, val) in enumerate(zip(bar_labels, bar_values)):
        x = pad_l + i * bar_slot + (bar_slot - bar_w) / 2
        y = bar_y(val)
        bh = H - pad_b - y
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" '
            f'fill="var(--blue, #006fcf)" rx="2"/>'
        )
        val_text = f"{val:g}{bar_unit}" if bar_unit else f"{val:g}"
        parts.append(
            f'<text x="{x + bar_w/2:.1f}" y="{y - 8:.1f}" text-anchor="middle" '
            f'fill="var(--ink, #53565a)" font-size="14" font-weight="600" '
            f'font-family="var(--font-body, sans-serif)">{esc(val_text)}</text>'
        )
        parts.append(
            f'<text x="{x + bar_w/2:.1f}" y="{H - pad_b + 25}" text-anchor="middle" '
            f'fill="var(--ink, #53565a)" font-size="14" font-weight="600" '
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
                    f'fill="var(--ink-muted, #63666a)" font-size="12" '
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
