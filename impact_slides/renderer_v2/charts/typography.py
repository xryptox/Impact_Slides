"""Opt-in chart_config.typography + shared chart-pane title/subtitle (#139/#147)."""
from __future__ import annotations

import contextvars
import math
import sys
from typing import Any, Mapping, Sequence

# Render-path strict flag (render_deck sets it; recipe unit tests default True).
_RENDER_STRICT: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "rv2_render_strict", default=True
)
# Warnings collected during a render_deck call for run_meta.json.
_RENDER_WARNINGS: contextvars.ContextVar[list[str] | None] = contextvars.ContextVar(
    "rv2_render_warnings", default=None
)

# Chart.js legacy sizes when typography is absent (SC-COMPAT-1).
LEGACY_X_TICK = 13
LEGACY_Y_TICK = 13
LEGACY_DATALABEL = 11

_TYPO_BOUNDS = {
    "x_tick_font_size": (8, 24),
    "y_tick_font_size": (8, 28),
    "datalabel_font_size": (8, 32),
}
# Under mode=auto, explicit channel floors rise (#150).
_AUTO_TYPO_BOUNDS = {
    "x_tick_font_size": (12, 24),
    "y_tick_font_size": (12, 28),
    "datalabel_font_size": (11, 32),
}
_SUPPORTED_TYPO_FIELDS = frozenset(_TYPO_BOUNDS) | frozenset({"mode"})

# Pane title geometry (#139).
PANE_TITLE_FS = 40
PANE_TITLE_LH = 1.05
PANE_TITLE_GAP_PX = 8
PANE_TITLE_MAX_LINES = 2
# Estimated reserved height for a 2-line title + gap.
PANE_TITLE_RESERVE_PX = int(PANE_TITLE_FS * PANE_TITLE_LH * PANE_TITLE_MAX_LINES) + PANE_TITLE_GAP_PX
MIN_CANVAS_W = 320
MIN_CANVAS_H = 240

# Deterministic pre-render host geometry (1920×1080 stage tokens).
_STAGE_W = 1920
_STAGE_H = 1080
_PAD_X = 96
_PAD_TOP = 56
_PAD_BOTTOM = 48
_GAP_HEADER_MAIN = 40
_HEADER_BLOCK = 96  # title line + dek allowance
_FOOTER_BLOCK = 40
_INSIGHT_BLOCK = 48
_DUAL_GAP = 24  # --size-6 / dual-chart gap
_HERO_GAP = 18  # --gap-md
_TILE_GAP = 18
_TILE_PAD = 17
_CHARTJS_WRAP_H = 480  # components.css .chartjs-wrap height
# .chart-frame { padding: 18px 22px } — dual panes use this card chrome.
CHART_FRAME_PAD_X = 22
CHART_FRAME_PAD_Y = 18


def _main_band_h() -> float:
    return float(
        _STAGE_H
        - _PAD_TOP
        - _PAD_BOTTOM
        - _HEADER_BLOCK
        - _GAP_HEADER_MAIN
        - _FOOTER_BLOCK
        - _INSIGHT_BLOCK
    )


def chart_host_size(kind: str, *, cols: int = 2) -> tuple[float, float]:
    """Fixed host (title+plot) size for pane-title remaining-canvas check.

    kind: dual_chart | chart_hero_dual | multi_panel
    """
    content_w = float(_STAGE_W - 2 * _PAD_X)
    main_h = _main_band_h()
    if kind == "dual_chart":
        pane_w = (content_w - _DUAL_GAP) / 2.0
        return pane_w, main_h
    if kind == "chart_hero_dual":
        # grid 2fr 1fr + gap — chart column is 2/3 of remaining.
        chart_w = (content_w - _HERO_GAP) * 2.0 / 3.0
        return chart_w, main_h
    # multi_panel tile (matches recipes/charts.py tile_width).
    n = max(int(cols), 1)
    tile_w = (content_w - (n - 1) * _TILE_GAP) / n - 2 * _TILE_PAD
    # Tile plot host ≈ default chart wrap; title sits above it in the tile.
    tile_h = float(_CHARTJS_WRAP_H + PANE_TITLE_RESERVE_PX)
    return tile_w, tile_h

# Inline styles (not global CSS) so decks without pane titles stay byte-identical
# and token-audit does not see bare px literals in a stylesheet string.
_PANE_TITLE_STYLE = (
    "font-family:var(--font-display,'IBM Plex Sans',sans-serif);"
    f"font-size:{PANE_TITLE_FS}px;font-weight:700;color:var(--navy,#00175a);"
    f"line-height:{PANE_TITLE_LH};margin:0 0 {PANE_TITLE_GAP_PX}px 0;"
    "display:-webkit-box;-webkit-box-orient:vertical;"
    f"-webkit-line-clamp:{PANE_TITLE_MAX_LINES};"
    "overflow:hidden;text-overflow:ellipsis;flex:none"
)
_PANE_TITLE_LEGACY_STYLE = (
    "white-space:nowrap;overflow:hidden;text-overflow:ellipsis"
)
# Pane subtitle / dek treatment (#147) — emission-scoped like the title.
PANE_SUBTITLE_FS = 22
PANE_SUBTITLE_LH = 1.3
PANE_SUBTITLE_MAX_LINES = 2
# Estimated reserved height for a 2-line subtitle + gap (only when subtitle present).
PANE_SUBTITLE_RESERVE_PX = (
    int(PANE_SUBTITLE_FS * PANE_SUBTITLE_LH * PANE_SUBTITLE_MAX_LINES) + PANE_TITLE_GAP_PX
)
_PANE_SUBTITLE_STYLE = (
    "font-family:var(--font-body,'Source Sans 3',sans-serif);"
    f"font-size:var(--fs-sub,{PANE_SUBTITLE_FS}px);font-weight:600;"
    f"color:var(--ink-muted,#53565a);line-height:{PANE_SUBTITLE_LH};"
    f"margin:0 0 {PANE_TITLE_GAP_PX}px 0;"
    "display:-webkit-box;-webkit-box-orient:vertical;"
    f"-webkit-line-clamp:{PANE_SUBTITLE_MAX_LINES};"
    "overflow:hidden;text-overflow:ellipsis;flex:none"
)

# Collision: only when datalabel_font_size supplied.
COLLISION_MARGIN_PX = 2
# ponytail: fixed avg glyph width; measureText in browser path if SVG audits drift
_AVG_CHAR_EM = 0.55


def set_render_strict(strict: bool) -> contextvars.Token:
    return _RENDER_STRICT.set(bool(strict))


def reset_render_strict(token: contextvars.Token) -> None:
    _RENDER_STRICT.reset(token)


def begin_render_warnings() -> contextvars.Token:
    return _RENDER_WARNINGS.set([])


def take_render_warnings(token: contextvars.Token) -> list[str]:
    warnings = list(_RENDER_WARNINGS.get() or [])
    _RENDER_WARNINGS.reset(token)
    return warnings


def _warn(msg: str) -> None:
    print(f"[typography] {msg}", file=sys.stderr)
    bucket = _RENDER_WARNINGS.get()
    if bucket is not None:
        bucket.append(msg)


def _is_whole_in_range(value: Any, lo: int, hi: int) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if not math.isfinite(value) or not float(value).is_integer():
        return False
    return lo <= int(value) <= hi


def resolve_typography(
    chart_cfg: Mapping[str, Any] | None,
    *,
    strict: bool | None = None,
) -> dict[str, int]:
    """Return effective tick/datalabel sizes.

    Absent/invalid group → legacy 13/13/11. Invalid under strict raises.
    Unsupported keys warn and are ignored (supported keys still apply).

    ``mode: "auto"`` marks the group for the shared auto resolver;
    explicit channel overrides remain optional and are never silently resized.
    Without a density context this returns legacy defaults for unset channels
    plus ``auto_mode=1`` so painters can run ``resolve_auto_typography``.
    """
    if strict is None:
        strict = _RENDER_STRICT.get()
    out = {
        "x_tick_font_size": LEGACY_X_TICK,
        "y_tick_font_size": LEGACY_Y_TICK,
        "datalabel_font_size": LEGACY_DATALABEL,
        # Markers: 1 only when the author supplied that field validly.
        "x_tick_font_size_set": 0,
        "y_tick_font_size_set": 0,
        "datalabel_font_size_set": 0,
        "auto_mode": 0,
    }
    if not isinstance(chart_cfg, Mapping):
        return out
    # Internal renderer handoff from the shared #150 resolver. It is never a
    # public chart_config key and lets all SVG painters consume the same plan.
    stashed = chart_cfg.get("_auto_typo_plan")
    if stashed is not None:
        try:
            from .auto_typography import AutoTypoPlan, merge_plan_into_typo

            if isinstance(stashed, AutoTypoPlan):
                return merge_plan_into_typo(out, stashed)
        except ImportError as exc:
            raise RuntimeError("auto typography resolver is unavailable") from exc
    raw = chart_cfg.get("typography")
    if raw is None:
        return out
    if not isinstance(raw, Mapping):
        msg = "typography must be an object"
        if strict:
            raise ValueError(f"chart_config.typography: {msg}")
        _warn(f"ignored entire group: {msg}")
        return out

    # Unsupported keys → warn, continue.
    for key in raw:
        if key not in _SUPPORTED_TYPO_FIELDS:
            _warn(f"unsupported field ignored: {key}")

    mode_raw = raw.get("mode")
    auto_mode = False
    if mode_raw is not None:
        if not isinstance(mode_raw, str) or mode_raw.strip().lower() != "auto":
            msg = "mode must be 'auto' (or omitted)"
            if strict:
                raise ValueError(f"chart_config.typography: {msg}")
            _warn(f"ignored entire group: {msg}")
            return out
        auto_mode = mode_raw.strip().lower() == "auto"

    bounds = _AUTO_TYPO_BOUNDS if auto_mode else _TYPO_BOUNDS

    # Validate supported size fields; one bad field drops the WHOLE group (non-strict).
    resolved: dict[str, int] = {}
    for field, (lo, hi) in bounds.items():
        if field not in raw:
            continue
        value = raw[field]
        if not _is_whole_in_range(value, lo, hi):
            msg = f"{field} must be a whole number from {lo} to {hi}"
            if strict:
                raise ValueError(f"chart_config.typography: {msg}")
            _warn(f"ignored entire group: {msg}")
            return out
        resolved[field] = int(value)

    out.update(resolved)
    for field in resolved:
        out[f"{field}_set"] = 1
    if auto_mode:
        out["auto_mode"] = 1
    return out


def typography_from_slide(slide: Mapping[str, Any], *, strict: bool | None = None) -> dict[str, int]:
    from .core import _chart_config

    return resolve_typography(_chart_config(slide), strict=strict)


def ordinary_datalabel_size(typo: Mapping[str, int], *, default: int = LEGACY_DATALABEL) -> int:
    """Size for ordinary point/value labels only (not totals/segments/chips)."""
    if typo.get("datalabel_font_size_set"):
        return int(typo["datalabel_font_size"])
    return default


def uses_ordinary_datalabels(layout: str, chart_cfg: Mapping[str, Any] | None) -> bool:
    """True when this layout paints ordinary above-bar / on-point value labels.

    Collision and datalabel_font_size only apply on that path — not stacked
    in-segment/totals, hbar inside chips, or combo dual-paint.
    """
    if not isinstance(chart_cfg, Mapping):
        return False
    if not (chart_cfg.get("point_labels") or chart_cfg.get("show_point_labels")):
        return False
    return layout in ("grouped_bar_chart", "line_chart")


def _optional_str_field(
    visual: Mapping[str, Any] | None,
    key: str,
    *,
    strict: bool | None = None,
) -> str | None:
    """Return stripped string, None if absent, raise/warn on non-string.

    None → field absent (caller may fall through). "" → present but empty.
    """
    if not isinstance(visual, Mapping) or key not in visual:
        return None
    val = visual[key]
    if val is None:
        return None
    if not isinstance(val, str):
        msg = f"{key} must be a string"
        if strict is None:
            strict = _RENDER_STRICT.get()
        if strict:
            raise ValueError(msg)
        _warn(msg)
        return None
    from ..strip import strip_eids

    return strip_eids(val).strip()


def resolve_pane_heading(
    visual: Mapping[str, Any] | None,
    *,
    series_names: Sequence[str] | None = None,
    strict: bool | None = None,
) -> str:
    """heading > label > chart_config.title > single series name (#147)."""
    if not isinstance(visual, Mapping):
        return ""
    for key in ("heading", "label"):
        got = _optional_str_field(visual, key, strict=strict)
        if got:
            return got
    cfg = visual.get("chart_config") if isinstance(visual.get("chart_config"), Mapping) else {}
    title = cfg.get("title") if isinstance(cfg, Mapping) else None
    if title is not None and not isinstance(title, str):
        msg = "chart_config.title must be a string"
        if strict is None:
            strict = _RENDER_STRICT.get()
        if strict:
            raise ValueError(msg)
        _warn(msg)
    elif isinstance(title, str):
        from ..strip import strip_eids

        t = strip_eids(title).strip()
        if t:
            return t
    names = list(series_names or [])
    if len(names) == 1 and names[0]:
        return str(names[0]).strip()
    return ""


def resolve_pane_subtitle(
    visual: Mapping[str, Any] | None,
    *,
    strict: bool | None = None,
) -> str:
    """Explicit pane subtitle only; empty when absent/invalid (#147)."""
    got = _optional_str_field(visual, "subtitle", strict=strict)
    return got or ""


def _pane_chrome_reserve_px(*, title: str, subtitle: str) -> int:
    """Combined title+subtitle height reserved from the plot host."""
    n = 0
    if title:
        n += PANE_TITLE_RESERVE_PX
    if subtitle:
        n += PANE_SUBTITLE_RESERVE_PX
    return n


def chart_frame_content_box(host_w: float, host_h: float) -> tuple[float, float]:
    """Inner box of a .chart-frame pane after CSS padding (22x / 18y)."""
    return (
        max(0.0, float(host_w) - 2 * CHART_FRAME_PAD_X),
        max(0.0, float(host_h) - 2 * CHART_FRAME_PAD_Y),
    )


def chart_pane_canvas_size(
    host_w: float,
    host_h: float,
    *,
    title: str = "",
    subtitle: str = "",
    frame_padded: bool = False,
) -> tuple[float, float]:
    """Return a chart pane's plot host after frame pad (opt) + heading chrome."""
    w, h = float(host_w), float(host_h)
    if frame_padded:
        w, h = chart_frame_content_box(w, h)
    return w, max(0.0, h - _pane_chrome_reserve_px(
        title=title.strip(), subtitle=subtitle.strip()
    ))


def chart_pane_title_html(
    text: str,
    *,
    available_w: float | None = None,
    available_h: float | None = None,
    strict: bool | None = None,
) -> str:
    """HTML-owned pane/tile/card heading. Empty string when text absent.

    Large title is default. If remaining canvas would fall under 320x240,
    strict fails; non-strict falls back to legacy one-line tile-label class.
    Title-only path — use chart_pane_headings_html when a subtitle is present.
    """
    return chart_pane_headings_html(
        text,
        "",
        available_w=available_w,
        available_h=available_h,
        strict=strict,
    )


def chart_pane_subtitle_html(text: str) -> str:
    """HTML-owned pane subtitle (dek treatment). Empty when text absent."""
    from ..strip import esc

    sub = (text or "").strip()
    if not sub:
        return ""
    return (
        f'<div class="gl-chart-pane-subtitle" style="{_PANE_SUBTITLE_STYLE}">'
        f"{esc(sub)}</div>"
    )


def chart_pane_headings_html(
    title: str = "",
    subtitle: str = "",
    *,
    available_w: float | None = None,
    available_h: float | None = None,
    strict: bool | None = None,
) -> str:
    """Title + optional subtitle with one remaining-canvas decision (#147).

    Reserves title and/or subtitle height together before the 320×240 check.
    Empty fields reserve nothing. Strict fails when remaining canvas is short;
    non-strict falls the title back to legacy tile-label and still emits the
    subtitle (when present).
    """
    from ..strip import esc

    head = (title or "").strip()
    sub = (subtitle or "").strip()
    if not head and not sub:
        return ""
    if strict is None:
        strict = _RENDER_STRICT.get()

    legacy = False
    if available_w is not None and available_h is not None:
        reserve = _pane_chrome_reserve_px(title=head, subtitle=sub)
        remain_w = float(available_w)
        remain_h = float(available_h) - reserve
        if remain_w < MIN_CANVAS_W or remain_h < MIN_CANVAS_H:
            msg = (
                f"pane title would leave canvas {remain_w:.0f}x{remain_h:.0f} "
                f"(min {MIN_CANVAS_W}x{MIN_CANVAS_H}); using legacy title"
            )
            if strict:
                raise ValueError(msg)
            _warn(msg)
            legacy = True

    parts: list[str] = []
    if head:
        if legacy:
            parts.append(
                f'<div class="gl-tile-label gl-chart-pane-title-legacy" '
                f'style="{_PANE_TITLE_LEGACY_STYLE}">{esc(head)}</div>'
            )
        else:
            parts.append(
                f'<div class="gl-chart-pane-title" style="{_PANE_TITLE_STYLE}">'
                f"{esc(head)}</div>"
            )
    if sub:
        parts.append(
            f'<div class="gl-chart-pane-subtitle" style="{_PANE_SUBTITLE_STYLE}">'
            f"{esc(sub)}</div>"
        )
    return "".join(parts)


def estimate_label_box(
    text: str,
    *,
    x: float,
    y: float,
    font_size: float,
    anchor: str = "middle",
) -> tuple[float, float, float, float]:
    """Return (left, top, right, bottom) estimated text box centered on (x, y)."""
    w = max(len(text), 1) * font_size * _AVG_CHAR_EM
    h = font_size * 1.2
    if anchor == "start":
        left = x
    elif anchor == "end":
        left = x - w
    else:
        left = x - w / 2
    top = y - h / 2
    return left, top, left + w, top + h


def boxes_intersect(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
    *,
    margin: float = COLLISION_MARGIN_PX,
) -> bool:
    al, at, ar, ab = a
    bl, bt, br, bb = b
    return not (
        ar + margin <= bl
        or br + margin <= al
        or ab + margin <= bt
        or bb + margin <= at
    )


def suppress_colliding_labels(
    items: Sequence[Mapping[str, Any]],
) -> tuple[list[int], list[dict[str, Any]]]:
    """Deterministic collision: series then category order; keep earlier.

    Each item: {series, category, label, box=(l,t,r,b)}.
    Returns (suppressed_indices, detail dicts).
    """
    order = sorted(range(len(items)), key=lambda i: (items[i]["series"], items[i]["category"]))
    kept_boxes: list[tuple[float, float, float, float]] = []
    suppressed: list[int] = []
    details: list[dict[str, Any]] = []
    for idx in order:
        item = items[idx]
        box = item["box"]
        hit = False
        for kb in kept_boxes:
            if boxes_intersect(box, kb):
                hit = True
                break
        if hit:
            suppressed.append(idx)
            details.append(
                {
                    "series": item["series"],
                    "category": item["category"],
                    "label": item["label"],
                }
            )
        else:
            kept_boxes.append(box)
    return suppressed, details


# Chart.js collision boot — emission-scoped (only when datalabel_font_size set).
# Live plugin shape: chart.$datalabels._labels is a FLAT list of label objects
# with $context.{datasetIndex,dataIndex}; not nested per-series rows.
DATALABEL_COLLISION_JS = """
<script data-rv2-datalabel-collision="1">
(function () {
  if (window.__rv2DatalabelCollision) return;
  window.__rv2DatalabelCollision = 1;
  var MARGIN = 2;
  function intersects(a, b) {
    return !(a.r + MARGIN <= b.l || b.r + MARGIN <= a.l || a.b + MARGIN <= b.t || b.b + MARGIN <= a.t);
  }
  function absBox(lab, chart) {
    var ctx = lab.$context || {};
    var si = ctx.datasetIndex | 0, ci = ctx.dataIndex | 0;
    var meta = chart.getDatasetMeta(si);
    var el = meta && meta.data && meta.data[ci];
    // Element pixel coords are authoritative once the chart has real layout.
    // Plugin $layout._box._rect is often still 0×0 at afterDatasetsDraw.
    if (!el || typeof el.x !== 'number' || typeof el.y !== 'number') return null;
    var g = (typeof lab.geometry === 'function' && lab.geometry()) || {};
    var w = g.w || 0, h = g.h || 0;
    if (!(w > 0 && h > 0)) return null;
    return {
      l: el.x + (g.x || 0), t: el.y + (g.y || 0),
      r: el.x + (g.x || 0) + w, b: el.y + (g.y || 0) + h,
      si: si, ci: ci
    };
  }
  function chartReady(chart) {
    if (!chart || chart.width < 10 || chart.height < 10) return false;
    var area = chart.chartArea;
    if (!area || area.right - area.left < 10 || area.bottom - area.top < 10) return false;
    // Inactive slides keep zeroed bar geometry (x≈0 for all points).
    var meta = chart.getDatasetMeta(0);
    var pts = meta && meta.data || [];
    if (!pts.length) return false;
    var minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (var i = 0; i < pts.length; i++) {
      var p = pts[i];
      if (typeof p.x === 'number') { if (p.x < minX) minX = p.x; if (p.x > maxX) maxX = p.x; }
      if (typeof p.y === 'number') { if (p.y < minY) minY = p.y; if (p.y > maxY) maxY = p.y; }
    }
    return (maxX - minX > 2) || (maxY - minY > 2);
  }
  function run(chart, wrap) {
    if (!chartReady(chart)) return false;
    var labels = chart.$datalabels && chart.$datalabels._labels;
    if (!labels || !labels.length) return false;
    // Flat label list (chartjs-plugin-datalabels prepare() output).
    var items = [];
    for (var i = 0; i < labels.length; i++) {
      var lab = labels[i];
      if (!lab || typeof lab.model !== 'function') continue;
      var model = lab.model();
      if (!model || model.display === false) continue;
      var key = lab.$groups && lab.$groups._key;
      if (key && key !== '$default' && key !== 'value') continue;
      var box = absBox(lab, chart);
      if (!box) continue;
      items.push({
        si: box.si, ci: box.ci, lab: lab, box: box,
        text: (model.lines || []).join(' ')
      });
    }
    if (!items.length) return false;
    items.sort(function (a, b) {
      return a.si !== b.si ? a.si - b.si : a.ci - b.ci;
    });
    var kept = [];
    var suppressed = [];
    for (var j = 0; j < items.length; j++) {
      var it = items[j], hit = false;
      for (var k = 0; k < kept.length; k++) {
        if (intersects(it.box, kept[k].box)) { hit = true; break; }
      }
      if (hit) {
        if (it.lab._model) { it.lab._model.opacity = 0; it.lab._model.display = false; }
        if (it.lab.$layout) it.lab.$layout._visible = false;
        suppressed.push(it);
      } else {
        kept.push(it);
      }
    }
    if (suppressed.length && wrap) {
      wrap.setAttribute('data-datalabel-suppressed', String(suppressed.length));
      var layout = wrap.getAttribute('data-chart-layout') || '';
      suppressed.forEach(function (s) {
        console.warn('[typography] datalabel suppressed', {
          layout: layout, series: s.si, category: s.ci, label: s.text, count: suppressed.length
        });
      });
      try { chart.draw(); } catch (e) {}
    } else if (wrap && !wrap.getAttribute('data-datalabel-suppressed')) {
      wrap.setAttribute('data-datalabel-suppressed', '0');
    }
    return true;
  }
  function processWrap(wrap) {
    if (!wrap || wrap.getAttribute('data-rv2-collision') !== '1') return;
    var canvas = wrap.querySelector('canvas');
    if (!canvas || typeof Chart === 'undefined' || !Chart.getChart) return;
    var chart = Chart.getChart(canvas);
    if (!chart || chart.__rv2CollisionDone) return;
    // Ensure layout when slide just became visible.
    if (chart.width < 2) {
      try { chart.resize(); chart.update('none'); } catch (e) {}
    }
    if (run(chart, wrap)) chart.__rv2CollisionDone = 1;
  }
  function processAll() {
    document.querySelectorAll('.chartjs-wrap[data-rv2-collision="1"]').forEach(processWrap);
  }
  if (typeof Chart === 'undefined' || Chart.__rv2CollisionHooked) return;
  Chart.__rv2CollisionHooked = 1;
  try {
    Chart.register({
      id: 'rv2DatalabelCollision',
      afterDatasetsDraw: function (chart) {
        if (chart.__rv2CollisionDone) return;
        var canvas = chart.canvas;
        var wrap = canvas && canvas.closest ? canvas.closest('.chartjs-wrap') : null;
        if (!wrap || wrap.getAttribute('data-rv2-collision') !== '1') return;
        if (run(chart, wrap)) chart.__rv2CollisionDone = 1;
      }
    });
  } catch (e) {}
  // Inactive slides are display:none at init (zero geometry). Re-run when a
  // slide becomes .active and on a short rAF budget after load.
  try {
    var mo = new MutationObserver(function () { processAll(); });
    document.querySelectorAll('.slide').forEach(function (s) {
      mo.observe(s, { attributes: true, attributeFilter: ['class'] });
    });
  } catch (e) {}
  var tries = 0;
  function tick() {
    processAll();
    if (++tries < 45) requestAnimationFrame(tick);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { requestAnimationFrame(tick); });
  } else {
    requestAnimationFrame(tick);
  }
})();
</script>
"""
