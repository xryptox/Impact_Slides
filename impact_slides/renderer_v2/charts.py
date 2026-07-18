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

    # Primary line (solid blue)
    line_pts = " ".join(f"{x_pos(i):.1f},{y_pos(p['value']):.1f}" for i, p in enumerate(points))
    parts.append(
        f'<polyline points="{line_pts}" fill="none" '
        f'stroke="var(--blue, #006fcf)" stroke-width="3" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
    )

    # Data points and labels for primary series
    for i, p in enumerate(points):
        cx, cy = x_pos(i), y_pos(p["value"])
        parts.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" '
            f'fill="var(--blue, #006fcf)"/>'
        )
        label_text = f"{p['value']:g}{y_unit}" if y_unit else f"{p['value']:g}"
        parts.append(
            f'<text x="{cx:.1f}" y="{cy - 12:.1f}" text-anchor="middle" '
            f'fill="var(--ink, #53565a)" font-size="14" font-weight="600" '
            f'font-family="var(--font-body, sans-serif)">{esc(label_text)}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)
