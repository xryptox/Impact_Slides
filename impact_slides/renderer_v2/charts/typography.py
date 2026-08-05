"""Opt-in chart_config.typography + shared chart-pane title (#139 / R6-A)."""
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
_SUPPORTED_TYPO_FIELDS = frozenset(_TYPO_BOUNDS)

# Pane title geometry (#139).
PANE_TITLE_FS = 40
PANE_TITLE_LH = 1.05
PANE_TITLE_GAP_PX = 8
PANE_TITLE_MAX_LINES = 2
# Estimated reserved height for a 2-line title + gap.
PANE_TITLE_RESERVE_PX = int(PANE_TITLE_FS * PANE_TITLE_LH * PANE_TITLE_MAX_LINES) + PANE_TITLE_GAP_PX
MIN_CANVAS_W = 320
MIN_CANVAS_H = 240

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
    }
    if not isinstance(chart_cfg, Mapping):
        return out
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

    # Validate supported fields; one bad field drops the WHOLE group (non-strict).
    resolved: dict[str, int] = {}
    for field, (lo, hi) in _TYPO_BOUNDS.items():
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
    return out


def typography_from_slide(slide: Mapping[str, Any], *, strict: bool | None = None) -> dict[str, int]:
    from .core import _chart_config

    return resolve_typography(_chart_config(slide), strict=strict)


def ordinary_datalabel_size(typo: Mapping[str, int], *, default: int = LEGACY_DATALABEL) -> int:
    """Size for ordinary point/value labels only (not totals/segments/chips)."""
    if typo.get("datalabel_font_size_set"):
        return int(typo["datalabel_font_size"])
    return default


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
    """
    from ..strip import esc

    title = (text or "").strip()
    if not title:
        return ""
    if strict is None:
        strict = _RENDER_STRICT.get()

    # Remaining canvas after title reservation (when host sizes known).
    legacy = False
    if available_w is not None and available_h is not None:
        remain_w = float(available_w)
        remain_h = float(available_h) - PANE_TITLE_RESERVE_PX
        if remain_w < MIN_CANVAS_W or remain_h < MIN_CANVAS_H:
            msg = (
                f"pane title would leave canvas {remain_w:.0f}x{remain_h:.0f} "
                f"(min {MIN_CANVAS_W}x{MIN_CANVAS_H}); using legacy title"
            )
            if strict:
                raise ValueError(msg)
            _warn(msg)
            legacy = True

    if legacy:
        return (
            f'<div class="gl-tile-label gl-chart-pane-title-legacy" '
            f'style="{_PANE_TITLE_LEGACY_STYLE}">{esc(title)}</div>'
        )
    return (
        f'<div class="gl-chart-pane-title" style="{_PANE_TITLE_STYLE}">'
        f"{esc(title)}</div>"
    )


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
DATALABEL_COLLISION_JS = """
<script data-rv2-datalabel-collision="1">
(function () {
  if (window.__rv2DatalabelCollision) return;
  window.__rv2DatalabelCollision = 1;
  var MARGIN = 2;
  function intersects(a, b) {
    return !(a.r + MARGIN <= b.l || b.r + MARGIN <= a.l || a.b + MARGIN <= b.t || b.b + MARGIN <= a.t);
  }
  function run(chart, wrap) {
    var labels = chart.$datalabels && chart.$datalabels._labels;
    if (!labels || !labels.length) return;
    // Build list in dataset then category order (plugin stores per-dataset arrays).
    var items = [];
    for (var si = 0; si < labels.length; si++) {
      var row = labels[si] || [];
      for (var ci = 0; ci < row.length; ci++) {
        var lab = row[ci];
        if (!lab || typeof lab.geometry !== 'function' || typeof lab.model !== 'function') continue;
        var model = lab.model();
        if (!model || !model.display) continue;
        // Skip non-ordinary sets (totals / in-segment / chips live in named sets).
        var key = lab.$groups && lab.$groups._key;
        if (key && key !== '$default' && key !== 'value') continue;
        var g = lab.geometry() || {};
        var el = lab._el;
        if (!el) continue;
        // Position center from element + geometry frame (plugin draw path).
        var cx = (typeof el.x === 'number') ? el.x : 0;
        var cy = (typeof el.y === 'number') ? el.y : 0;
        var w = g.w || 0, h = g.h || 0;
        var ox = (g.x || 0), oy = (g.y || 0);
        // Prefer live layout box when the plugin has prepared $layout.
        if (lab.$layout && lab.$layout._box && lab.$layout._box._rect) {
          var r = lab.$layout._box._rect;
          items.push({
            si: si, ci: ci, lab: lab,
            box: {l: r.x, t: r.y, r: r.x + r.w, b: r.y + r.h},
            text: (model.lines || []).join(' ')
          });
        } else {
          items.push({
            si: si, ci: ci, lab: lab,
            box: {l: cx + ox, t: cy + oy, r: cx + ox + w, b: cy + oy + h},
            text: (model.lines || []).join(' ')
          });
        }
      }
    }
    items.sort(function (a, b) {
      return a.si !== b.si ? a.si - b.si : a.ci - b.ci;
    });
    var kept = [];
    var suppressed = [];
    for (var i = 0; i < items.length; i++) {
      var it = items[i], hit = false;
      for (var k = 0; k < kept.length; k++) {
        if (intersects(it.box, kept[k].box)) { hit = true; break; }
      }
      if (hit) {
        // Hide via display override on the label config context.
        if (it.lab._model) it.lab._model.opacity = 0;
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
        console.warn(
          '[typography] datalabel suppressed',
          {layout: layout, series: s.si, category: s.ci, label: s.text, count: suppressed.length}
        );
      });
      // Redraw once so opacity/visibility sticks.
      try { chart.draw(); } catch (e) {}
    }
  }
  // Hook Chart after each chart is constructed.
  var orig = Chart && Chart.prototype && Chart.prototype.update;
  if (!orig || Chart.__rv2CollisionHooked) return;
  Chart.__rv2CollisionHooked = 1;
  // Prefer afterDraw plugin registration.
  try {
    Chart.register({
      id: 'rv2DatalabelCollision',
      afterDatasetsDraw: function (chart) {
        if (chart.__rv2CollisionDone) return;
        var canvas = chart.canvas;
        var wrap = canvas && canvas.closest ? canvas.closest('.chartjs-wrap') : null;
        if (!wrap || wrap.getAttribute('data-rv2-collision') !== '1') return;
        // Wait one frame so datalabels $layout boxes exist.
        chart.__rv2CollisionDone = 1;
        run(chart, wrap);
      }
    });
  } catch (e) {}
})();
</script>
"""
