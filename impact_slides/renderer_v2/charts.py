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
    mod = _load_pack()
    lt = (layout or slide.get("layout_type") or "").lower()
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
