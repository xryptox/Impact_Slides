"""Callout overlay geometry for chart panes."""
from __future__ import annotations

from typing import Any, Mapping
from ..strip import esc, strip_eids



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



_CALLOUT_TYPES = frozenset({"elbow_arrow", "chevron", "band", "measure_rule"})



def _value_anchor_pct(
    cfg: Mapping[str, Any],
    chart_cfg: Mapping[str, Any],
    value: Any,
    layout: str,
) -> float | None:
    """Map a data value to a % offset along the value axis (#89).

    Domain comes from the built Chart.js config's effective ticks when set
    (explicit min/max, forced ticks, or break-clamped), falling back to the
    handoff's explicit y_axis_min/y_axis_max (grouped bars don't clamp the
    scale ticks). For horizontal bars the value axis is x, so the offset is
    horizontal — the caller applies it as left%. None when no anchor works.
    """
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    scales = ((cfg.get("options") or {}).get("scales") or {})
    axis = scales.get("x") if layout == "horizontal_bar_chart" else scales.get("y")
    ticks = (axis or {}).get("ticks") or {}
    lo = ticks.get("min")
    hi = ticks.get("max")
    if lo is None or hi is None:
        lo = chart_cfg.get("y_axis_min")
        hi = chart_cfg.get("y_axis_max")
    if lo is None or hi is None:
        return None
    rng = float(hi) - float(lo)
    if rng <= 0:
        return None
    frac = (v - float(lo)) / rng
    frac = max(0.0, min(1.0, frac))
    # Vertical charts: larger values sit higher => smaller top offset.
    # Horizontal bars: value axis is x (left=lo), so left offset grows.
    if layout == "horizontal_bar_chart":
        return frac * 100.0
    return (1.0 - frac) * 100.0



def _merge_callout_bands(callouts: Any) -> Any:
    """Canonicalize the legacy band+elbow double-declare (#114).

    Handoffs predating PR 104 paired a translucent band (to carry the label)
    with an elbow_arrow (for chrome) over the SAME span; the elbow is the full
    spanning recipe, so the band is absorbed — its label migrates to the
    elbow when the elbow has none — instead of double-painting. Idempotent.
    """
    if not isinstance(callouts, list):
        return callouts
    elbow_span_idx: dict[tuple[int, int], int] = {}
    for i, c in enumerate(callouts):
        if isinstance(c, dict) and c.get("type") == "elbow_arrow":
            f_ = max(0, int(c.get("from") or 0))
            t_ = max(f_, int(c.get("to") if c.get("to") is not None else f_))
            elbow_span_idx.setdefault((f_, t_), i)
    if not elbow_span_idx:
        return callouts
    migrated: dict[int, str] = {}  # original elbow index -> band label
    kept: list[tuple[int, Any]] = []
    for i, c in enumerate(callouts):
        if isinstance(c, dict) and c.get("type") == "band":
            f_ = max(0, int(c.get("from") or 0))
            t_ = max(f_, int(c.get("to") if c.get("to") is not None else f_))
            ei = elbow_span_idx.get((f_, t_))
            if ei is not None:
                band_text = str(c.get("text") or "").strip()
                if band_text:
                    migrated[ei] = band_text
                continue  # absorbed by the elbow over the same span
        kept.append((i, c))
    return [
        ({**c, "text": migrated[i]} if i in migrated
         and isinstance(c, dict)
         and not str(c.get("text") or "").strip() else c)
        for i, c in kept
    ]



def _elbow_stem_html(
    cfg: Mapping[str, Any],
    chart_cfg: Mapping[str, Any],
    frm: int,
    n: int,
    anchor: float | None,
    layout: str,
    cid: str = "",
) -> str:
    """Vertical stem from the elbow capsule down to the from-bar top (R2).

    The PDF recipe drops a stem from the capsule's left end to the top of
    the first spanned bar. Bar-top height comes from the built Chart.js
    datasets at the ``from`` category — stacked sums the signed segments,
    grouped takes the tallest bar — mapped through the same domain math as
    the capsule anchor. Fails closed ("") when geometry can't be computed.
    """
    datasets = ((cfg.get("data") or {}).get("datasets")) or []
    vals: list[float] = []
    for ds in datasets:
        data = (ds or {}).get("data") or []
        if frm < len(data):
            v = data[frm]
            if isinstance(v, (int, float)):
                vals.append(float(v))
    if not vals:
        return ""
    stacked = bool(
        ((((cfg.get("options") or {}).get("scales") or {}).get("y") or {}).get("stacked"))
    )
    bar_val = sum(vals) if stacked else max(vals)
    bar_top = _value_anchor_pct(cfg, chart_cfg, bar_val, layout)
    if bar_top is None:
        return ""
    stem_top = anchor if anchor is not None else 10.0
    height = bar_top - stem_top
    if height <= 0:
        return ""
    left = ((frm + 0.5) / max(int(n or 1), 1)) * 100
    return (
        f'<div class="chartjs-callout-elbow-stem" '
        f'style="left:{left:.2f}%;top:{stem_top:.2f}%;height:{height:.2f}%" '
        f'data-for="{esc(cid)}"></div>'
    )



def _build_callout_overlays(
    callouts: Any,
    n_labels: int,
    cid: str,
    cfg: Mapping[str, Any] | None = None,
    layout: str = "",
    chart_cfg: Mapping[str, Any] | None = None,
) -> str:
    """Geometric callout overlays for the Chart.js wrap (#89/R2).

    Drawable chrome — elbow arrows spanning bar tops, chevrons under the
    category axis, event bands — positioned as HTML/CSS overlays from
    category-index anchors, with an optional ``value`` data anchor pinning
    the elbow along the value axis. Unknown callout types fail closed
    (ValueError).
    """
    if not callouts:
        return ""
    if not isinstance(callouts, list):
        raise ValueError("chart_config.callouts must be a list")
    callouts = _merge_callout_bands(callouts)
    n = max(int(n_labels or 0), 1)
    parts: list[str] = []
    for c in callouts:
        if not isinstance(c, dict):
            raise ValueError("chart_config.callouts entries must be objects")
        ctype = str(c.get("type") or "")
        if ctype not in _CALLOUT_TYPES:
            raise ValueError(
                f"unknown callout type {ctype!r}: "
                f"expected one of {sorted(_CALLOUT_TYPES)}"
            )
        text = esc(str(c.get("text") or ""))
        if ctype == "chevron":
            at = max(0, int(c.get("at") or 0))
            left = ((at + 0.5) / n) * 100
            # T7/R5-B: two sibling nodes — a navy down-triangle above a
            # separate navy pill (PDF Refresh marker), not a fused unit.
            parts.append(
                f'<div class="chartjs-callout chartjs-callout-chevron-tip" '
                f'data-for="{esc(cid)}" data-at="{at}" '
                f'style="left:{left:.2f}%"></div>'
                f'<div class="chartjs-callout chartjs-callout-chevron-pill" '
                f'data-for="{esc(cid)}" data-at="{at}" '
                f'style="left:{left:.2f}%">{text}</div>'
            )
            continue
        # elbow_arrow and band share the span geometry; only the CSS class,
        # the value-anchor dimension, and data attrs differ.
        frm = max(0, int(c.get("from") or 0))
        to = max(frm, int(c.get("to") if c.get("to") is not None else frm))
        # D2: span from bar-center fractions, not raw category edges, so the
        # JS-off fallback lands close; the calloutGeometry plugin writes
        # exact chartArea pixels on top.
        left = ((frm + 0.5) / n) * 100
        width = ((to - frm) / n) * 100
        style = f"left:{left:.2f}%;width:{width:.2f}%"
        if ctype == "measure_rule":
            # N8: thin dual-ended rule from first to last bar centre with a
            # blue pill interrupting it at the midpoint and an optional gray
            # sub-caption under the pill (PDF slide-16 CAGR recipe). Pill
            # text is rendered as declared; the sub-caption is a separate
            # opt-in ``caption`` key — no text-splitting heuristics.
            cap = esc(str(c.get("caption") or ""))
            cap_html = (
                f'<span class="chartjs-callout-measure-caption">{cap}</span>'
                if cap
                else ""
            )
            parts.append(
                f'<div class="chartjs-callout chartjs-callout-measure" '
                f'data-for="{esc(cid)}" data-from="{frm}" data-to="{to}" '
                f'style="{style}">'
                f'<i class="chartjs-callout-measure-arrow '
                f'chartjs-callout-measure-arrow-l"></i>'
                f'<i class="chartjs-callout-measure-arrow '
                f'chartjs-callout-measure-arrow-r"></i>'
                f'<span class="chartjs-callout-measure-pill">{text}</span>'
                f"{cap_html}</div>"
            )
            continue
        anchor: float | None = None
        if ctype == "elbow_arrow" and c.get("value") is not None and cfg:
            anchor = _value_anchor_pct(cfg, chart_cfg or {}, c.get("value"), layout)
            if anchor is not None:
                # Vertical chart: pin vertically; horizontal bar: pin on x.
                dim = "left" if layout == "horizontal_bar_chart" else "top"
                style += f";{dim}:{anchor:.2f}%"
        suffix = "elbow" if ctype == "elbow_arrow" else "band"
        # R2: opt-in line-art elbow (thin rule + mid pill) vs the default
        # thick capsule. Declarative ``style: "line"``; default unchanged.
        variant = (
            " chartjs-callout-elbow-line"
            if ctype == "elbow_arrow" and str(c.get("style") or "") == "line"
            else ""
        )
        dv = (
            f' data-value="{esc(str(c.get("value")))}"'
            if ctype == "elbow_arrow" and c.get("value") is not None else ""
        )
        parts.append(
            f'<div class="chartjs-callout chartjs-callout-{suffix}{variant}" '
            f'data-for="{esc(cid)}" data-from="{frm}" data-to="{to}"{dv} '
            f'style="{style}">'
            f'<span class="chartjs-callout-label">{text}</span></div>'
        )
        # IR stem (R2): computed drop from the capsule to the from-bar top,
        # a sibling of the pill so % resolve against the chart wrap.
        if ctype == "elbow_arrow" and layout != "horizontal_bar_chart" and cfg:
            stem = _elbow_stem_html(cfg, chart_cfg or {}, frm, n, anchor, layout, cid)
            if stem:
                parts.append(stem)
    return "".join(parts)
