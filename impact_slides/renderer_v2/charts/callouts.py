"""Callout overlay geometry for chart panes."""
from __future__ import annotations

import math
import sys
from typing import Any, Mapping
from ..strip import esc, strip_eids
from .geometry import chart_geometry

# N5/#138: shared-column side callout (plain HTML furniture, not a Chart.js plugin).
_SIDE_CALLOUT_LAYOUTS = frozenset({"stacked_bar_chart"})
_SIDE_CALLOUT_DEFAULT_SIZE = 24
_SIDE_CALLOUT_LEAD_SIZE = 26
# Quoted so token-audit treats this as a CSS string (ink).
_SIDE_CALLOUT_COLOR = "#53565A"
# PDF p28 Deposit Programs: callout top offset below tile top (stage px).
_SIDE_CALLOUT_TILE_TOP_PX = 49.8
# Gap between callout bottom and first exterior name (stage/canvas px).
_SIDE_CALLOUT_NAME_GAP_PX = 8
_SIDE_CALLOUT_MIN_PLOT_WIDTH = 240
_SIDE_CALLOUT_MAX_LINES = 4
_SIDE_CALLOUT_MIN_SIZE = 12
_SIDE_CALLOUT_MAX_SIZE = 32
_SIDE_CALLOUT_MAX_TEXT_LENGTH = 32
_SIDE_CALLOUT_CHAR_WIDTH = 0.45

# Opt-in only: patches shell segmentNames at Chart.register time so exterior
# names clear the callout. Emitted next to the aside — never in global shell.
_SIDE_CALLOUT_NAME_GAP_JS = """
<script data-side-callout-name-gap-boot="1">
(function () {
  if (typeof Chart === 'undefined' || Chart.__sideCalloutNameGap) return;
  Chart.__sideCalloutNameGap = 1;
  var reg = Chart.register;
  Chart.register = function () {
    for (var i = 0; i < arguments.length; i++) {
      var p = arguments[i];
      if (!p || p.id !== 'segmentNames' || p.__sideCalloutNameGap) continue;
      p.__sideCalloutNameGap = 1;
      var base = p.afterDatasetsDraw;
      if (typeof base !== 'function') continue;
      p.afterDatasetsDraw = function (chart) {
        var canvas = chart.canvas;
        var ctx = chart.ctx;
        var host = (canvas.closest && (canvas.closest('.gl-tile') || canvas.closest('.chartjs-wrap'))) || null;
        var callEl = host && host.querySelector && host.querySelector('aside.chart-side-callout');
        if (!callEl) return base.call(this, chart);
        var cbr = callEl.getBoundingClientRect();
        var ccr = canvas.getBoundingClientRect();
        var hbr = host.getBoundingClientRect();
        var offset = parseFloat(callEl.getAttribute('data-side-callout-offset') || '');
        var gutter = parseFloat(callEl.getAttribute('data-side-callout-gutter') || '');
        var hostScaleX = hbr.width / host.offsetWidth;
        if (!(ccr.height > 0) || !(hostScaleX > 0) || isNaN(offset) || isNaN(gutter)) return base.call(this, chart);
        callEl.style.left = ((ccr.right - hbr.left) / hostScaleX - gutter + offset) + 'px';
        callEl.style.width = (gutter - offset) + 'px';
        cbr = callEl.getBoundingClientRect();
        if (callEl.clientWidth <= 0 || callEl.scrollWidth > callEl.clientWidth ||
            cbr.left < ccr.left || cbr.right > ccr.right || cbr.bottom > ccr.bottom) {
          callEl.style.display = 'none';
          console.warn('[side_callout] omitted: callout does not fit the measured exterior-name lane');
          return base.call(this, chart);
        }
        var minWidth = parseFloat(callEl.getAttribute('data-side-callout-min-plot-width') || '');
        var area = chart.chartArea;
        if (!isNaN(minWidth) && area && area.right - area.left < minWidth) {
          callEl.style.display = 'none';
          console.warn('[side_callout] omitted: plot width below min_plot_width');
          return base.call(this, chart);
        }
        callEl.style.display = '';
        var opts = chart.config.options.plugins && chart.config.options.plugins.segmentNames;
        var lh = (opts && typeof opts.lineHeight === 'number') ? opts.lineHeight : 13;
        var gap = parseFloat(callEl.getAttribute('data-side-callout-name-gap') || '');
        if (isNaN(gap)) gap = 8;
        var nameMin = (cbr.bottom - ccr.top) * (chart.height / ccr.height) + gap + lh / 2;
        var batch = [];
        var orig = ctx.fillText;
        ctx.fillText = function (t, x, y) {
          batch.push({ t: t, x: x, y: y, c: ctx.fillStyle, f: ctx.font, a: ctx.textAlign, b: ctx.textBaseline });
        };
        try { base.call(this, chart); }
        finally { ctx.fillText = orig; }
        if (!batch.length) return;
        if (nameMin + (batch.length - 1) * lh + lh / 2 > chart.height) {
          callEl.style.display = 'none';
          console.warn('[side_callout] omitted: exterior names do not fit below callout');
          for (var j = 0; j < batch.length; j++) {
            var it = batch[j];
            ctx.fillStyle = it.c;
            ctx.font = it.f;
            ctx.textAlign = it.a;
            ctx.textBaseline = it.b;
            orig.call(ctx, it.t, it.x, it.y);
          }
          return;
        }
        var extra = Math.max(0, nameMin - batch[0].y);
        for (var j = 0; j < batch.length; j++) {
          var it = batch[j];
          ctx.fillStyle = it.c;
          ctx.font = it.f;
          ctx.textAlign = it.a;
          ctx.textBaseline = it.b;
          orig.call(ctx, it.t, it.x, it.y + extra);
        }
      };
    }
    return reg.apply(this, arguments);
  };
})();
</script>
"""



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


def _side_callout_line_height(size: int) -> int:
    return max(29, math.ceil(size * 1.115))


def _side_callout_lines(
    raw: Mapping[str, Any],
) -> tuple[list[dict[str, Any]] | None, str | None]:
    """Normalize bounded structured side_callout lines into paint lines."""
    lines_in = raw.get("lines")
    items: list[tuple[Any, Any]] = []
    if lines_in is not None:
        if not isinstance(lines_in, (list, tuple)) or not lines_in:
            return None, "lines must be a non-empty list"
        if len(lines_in) > _SIDE_CALLOUT_MAX_LINES:
            return None, f"lines exceed maximum of {_SIDE_CALLOUT_MAX_LINES}"
        for item in lines_in:
            if isinstance(item, Mapping):
                items.append((item.get("text", item.get("value")), item.get("size")))
            elif isinstance(item, str):
                items.append((item, None))
            else:
                return None, "each line must be text or an object"
    else:
        value = raw.get("value")
        label = raw.get("label")
        if value is not None:
            items.append((value, _SIDE_CALLOUT_LEAD_SIZE))
        if isinstance(label, (list, tuple)):
            items.extend((part, None) for part in label)
        elif label is not None:
            items.append((label, None))
    if not items or len(items) > _SIDE_CALLOUT_MAX_LINES:
        return None, f"lines exceed maximum of {_SIDE_CALLOUT_MAX_LINES}"
    out: list[dict[str, Any]] = []
    for index, (text_raw, size_raw) in enumerate(items):
        if not isinstance(text_raw, str):
            return None, "line text must be a string"
        text = strip_eids(text_raw).strip()
        if not text:
            return None, "line text must not be empty"
        if len(text) > _SIDE_CALLOUT_MAX_TEXT_LENGTH:
            return None, f"line text exceeds maximum of {_SIDE_CALLOUT_MAX_TEXT_LENGTH} characters"
        size = _SIDE_CALLOUT_LEAD_SIZE if index == 0 else _SIDE_CALLOUT_DEFAULT_SIZE
        if size_raw is not None:
            if (
                isinstance(size_raw, bool)
                or not isinstance(size_raw, (int, float))
                or not math.isfinite(size_raw)
                or not float(size_raw).is_integer()
                or not _SIDE_CALLOUT_MIN_SIZE <= size_raw <= _SIDE_CALLOUT_MAX_SIZE
            ):
                return None, (
                    f"line size must be a whole number from {_SIDE_CALLOUT_MIN_SIZE} "
                    f"to {_SIDE_CALLOUT_MAX_SIZE}"
                )
            size = int(size_raw)
        out.append({"text": text, "size": size, "line_height": _side_callout_line_height(size)})
    return out, None


def _side_column_geometry(
    chart_cfg: Mapping[str, Any], *, strict: bool = True
) -> tuple[int, int] | None:
    if strict:
        if chart_cfg.get("exterior_segment_names") is not True:
            return None
        offset = chart_cfg.get("segment_name_offset", 8)
        gutter = chart_cfg.get("segment_name_gutter", 120)
        if (
            isinstance(offset, bool)
            or isinstance(gutter, bool)
            or not isinstance(offset, (int, float))
            or not isinstance(gutter, (int, float))
            or not math.isfinite(offset)
            or not math.isfinite(gutter)
        ):
            return None
        offset, gutter = int(offset), int(gutter)
        return (offset, gutter) if 0 <= offset < gutter else None
    if not chart_cfg.get("exterior_segment_names"):
        return None
    return (
        int(chart_cfg.get("segment_name_offset", 8)),
        int(chart_cfg.get("segment_name_gutter", 120)),
    )


def _resolve_side_callout(
    chart_cfg: Mapping[str, Any] | None,
    layout: str,
    *,
    warn: bool = True,
    available_width: float | None = None,
) -> dict[str, Any] | None:
    """Return paint plan for opt-in side_callout, or None when inert/unsupported.

    Shared-column Recipe A (sign-off issue 138): callout sits at the top of the
    existing right text column — no second x-lane, no plot shrink. Over-budget
    fail-soft is preserved for an explicit ``min_plot_width`` gate only; the
    PDF/v9 shared-column case is not over-budget.
    """
    if not isinstance(chart_cfg, Mapping):
        return None
    if "side_callout" not in chart_cfg:
        return None
    raw = chart_cfg["side_callout"]
    if not isinstance(raw, Mapping):
        if warn:
            print(
                "[side_callout] ignored: side_callout must be an object",
                file=sys.stderr,
            )
        return None
    lt = (layout or "").lower().strip()
    if lt not in _SIDE_CALLOUT_LAYOUTS:
        if warn:
            print(
                f"[side_callout] ignored: unsupported layout {lt!r} "
                f"(supported: {sorted(_SIDE_CALLOUT_LAYOUTS)})",
                file=sys.stderr,
            )
        return None
    placement = str(raw.get("placement") or "right").lower().strip()
    skin = str(raw.get("skin") or "tall").lower().strip()
    if placement != "right" or skin != "tall":
        if warn:
            print(
                f"[side_callout] ignored: unsupported placement/skin "
                f"{placement!r}/{skin!r} (locked: right/tall)",
                file=sys.stderr,
            )
        return None
    lines, lines_error = _side_callout_lines(raw)
    if not lines:
        if warn:
            print(
                f"[side_callout] ignored: {lines_error or 'empty value/label/lines'}",
                file=sys.stderr,
            )
        return None
    column = _side_column_geometry(chart_cfg)
    if not column:
        if warn:
            print(
                "[side_callout] ignored: requires a valid exterior_segment_names column",
                file=sys.stderr,
            )
        return None
    offset, gutter = column
    geom = chart_geometry("stacked_bar_chart")
    plot_width = geom["width"] - geom["pad_l"] - gutter
    lane_width = gutter - offset
    required_lane_width = max(
        math.ceil(len(str(line["text"])) * int(line["size"]) * _SIDE_CALLOUT_CHAR_WIDTH)
        for line in lines
    )
    callout_height = sum(int(line["line_height"]) for line in lines)
    names_height = 12 + 3 * 16
    available_height = geom["height"] - _SIDE_CALLOUT_TILE_TOP_PX - _SIDE_CALLOUT_NAME_GAP_PX - names_height
    if plot_width <= 0:
        if warn:
            print("[side_callout] omitted: exterior-name gutter leaves no plot", file=sys.stderr)
        return None
    effective_lane_width = lane_width
    if available_width is not None:
        effective_lane_width = lane_width * available_width / geom["width"]
    if effective_lane_width < required_lane_width:
        if warn:
            print(
                f"[side_callout] omitted: exterior-name lane {effective_lane_width:.1f}px "
                f"< required callout width {required_lane_width}px",
                file=sys.stderr,
            )
        return None
    if callout_height > available_height:
        if warn:
            print(
                f"[side_callout] omitted: callout height {callout_height}px "
                f"> available column height {available_height:.1f}px",
                file=sys.stderr,
            )
        return None
    min_w = raw.get("min_plot_width")
    if min_w is not None and (
        isinstance(min_w, bool)
        or not isinstance(min_w, (int, float))
        or not math.isfinite(min_w)
        or min_w <= 0
    ):
        if warn:
            print("[side_callout] ignored: min_plot_width must be a positive number", file=sys.stderr)
        return None
    min_w = max(_SIDE_CALLOUT_MIN_PLOT_WIDTH, int(min_w or 0))
    if plot_width < min_w:
        if warn:
            print(
                f"[side_callout] omitted: plot width {plot_width}px < min_plot_width {min_w}px",
                file=sys.stderr,
            )
        return None
    aria = " ".join(str(ln["text"]) for ln in lines)
    return {
        "placement": placement,
        "skin": skin,
        "lines": lines,
        "aria": aria,
        "offset": offset,
        "gutter": gutter,
        "min_plot_width": min_w,
        "lane_width": lane_width,
    }


def _build_side_callout_svg(
    chart_cfg: Mapping[str, Any] | None,
    layout: str,
    *,
    warn: bool = True,
) -> str:
    """HTML callout embedded in the SVG coordinate system for JS-off charts."""
    plan = _resolve_side_callout(chart_cfg, layout, warn=warn)
    if not plan:
        return ""
    geom = chart_geometry("stacked_bar_chart")
    x = geom["width"] - plan["gutter"] + plan["offset"]
    lines = "".join(
        f'<div style="font-size:{line["size"]}px;font-weight:700;color:{_SIDE_CALLOUT_COLOR};line-height:{line["line_height"]}px">{esc(str(line["text"]))}</div>'
        for line in plan["lines"]
    )
    return (
        f'<foreignObject x="{x}" y="{_SIDE_CALLOUT_TILE_TOP_PX}" '
        f'width="{plan["lane_width"]}" height="{geom["height"] - _SIDE_CALLOUT_TILE_TOP_PX}">'
        f'<aside xmlns="http://www.w3.org/1999/xhtml" class="chart-side-callout chart-side-callout--{esc(plan["skin"])} chart-side-callout--{esc(plan["placement"])}" '
        f'style="margin:0;padding:0;background:transparent;border:0;border-radius:0;box-shadow:none;color:{_SIDE_CALLOUT_COLOR};font-family:var(--font-display,\'IBM Plex Sans\',sans-serif);font-weight:700;text-align:left;width:{plan["lane_width"]}px" aria-label="{esc(plan["aria"])}">'
        f"{lines}</aside></foreignObject>"
    )


def _build_side_callout_html(
    chart_cfg: Mapping[str, Any] | None,
    layout: str,
    *,
    warn: bool = True,
    host: str = "wrap",
    tile_pad_px: int = 16,
    available_width: float | None = None,
) -> str:
    """Plain HTML/CSS side callout furniture (Chart.js + JS-off paths).

    Styles are inline so global CSS stays byte-neutral when side_callout is off.

    host="tile": multi-panel tile coords (PDF local top offset). host="wrap":
    chart wrap is the containing block (standalone).
    """
    plan = _resolve_side_callout(
        chart_cfg, layout, warn=warn, available_width=available_width
    )
    if not plan:
        return ""
    ink = _SIDE_CALLOUT_COLOR  # '#53565A' — quoted CSS string for token-audit
    # PDF p28 tile-local top; keep Npx only inside style="..." (token-audit).
    top_css = f"top:{_SIDE_CALLOUT_TILE_TOP_PX}px"
    line_html = []
    for ln in plan["lines"]:
        size = int(ln["size"])
        line_height = int(ln["line_height"])
        line_html.append(
            f'<div class="chart-side-callout__line" style="font-size:{size}px;font-weight:700;color:{ink};line-height:{line_height}px">{esc(str(ln["text"]))}</div>'
        )
    geom = chart_geometry("stacked_bar_chart")
    x_pct = 100 * (geom["width"] - plan["gutter"] + plan["offset"]) / geom["width"]
    lane_pct = 100 * plan["lane_width"] / geom["width"]
    if host == "tile":
        pad = max(0, int(tile_pad_px))
        left = f"calc({x_pct:.6f}% + {pad * (1 - 2 * x_pct / 100):.6f}px)"
        width = f"width:calc({lane_pct:.6f}% - {2 * pad * lane_pct / 100:.6f}px)"
    else:
        left = f"{x_pct:.6f}%"
        width = f"width:{lane_pct:.6f}%"
    anchor = "tile" if host == "tile" else "wrap"
    aside = (
        f'<aside class="chart-side-callout chart-side-callout--{esc(plan["skin"])} '
        f'chart-side-callout--{esc(plan["placement"])}" '
        f'data-side-callout-html="{anchor}" data-side-callout-anchor="{anchor}" '
        f'data-side-callout-offset="{plan["offset"]}" data-side-callout-gutter="{plan["gutter"]}" '
        f'data-side-callout-name-gap="{_SIDE_CALLOUT_NAME_GAP_PX}" '
        f'data-side-callout-min-plot-width="{plan["min_plot_width"] or ""}" '
        f'style="--side-callout-offset:{plan["offset"]}px;--side-callout-gutter:{plan["gutter"]}px;position:absolute;{top_css};margin:0;padding:0;background:transparent;border:0;border-radius:0;box-shadow:none;color:{ink};font-family:var(--font-display,\'IBM Plex Sans\',sans-serif);font-weight:700;font-size:24px;line-height:29px;text-align:left;pointer-events:none;z-index:2;{width};left:{left};right:auto" '
        f'aria-label="{esc(plan["aria"])}">'
        f'{ "".join(line_html) }'
        f"</aside>"
    )
    # Local Chart.js name-gap boot (active callout only). No-op when charts off.
    return aside + _SIDE_CALLOUT_NAME_GAP_JS


def side_callout_active(
    chart_cfg: Mapping[str, Any] | None,
    layout: str = "stacked_bar_chart",
    *,
    available_width: float | None = None,
    warn: bool = False,
) -> bool:
    """True when side_callout will paint (suppresses competing tile badge)."""
    return _resolve_side_callout(
        chart_cfg, layout, warn=warn, available_width=available_width
    ) is not None
