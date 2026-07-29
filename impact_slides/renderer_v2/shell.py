"""Deck shell: CSS concat, stage, JS, DECK_META."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .charts import chart_css
from .lib_inliner import DeliveryMode, InlineBundle, build_head_assets, coerce_delivery
from .sprite import sprite_svg
from .strip import esc

_CSS_DIR = Path(__file__).resolve().parent / "css"


def load_css(*, debug: bool = False) -> str:
    parts = []
    for name in ("tokens.css", "semantic-tokens.css", "viewport.css", "gridlines.css", "components.css"):
        parts.append((_CSS_DIR / name).read_text(encoding="utf-8"))
    parts.append(chart_css())
    if debug:
        parts.append("body.gl-debug .gl-slide { outline: 2px solid rgba(0,111,207,.35); }")
    return "\n\n".join(parts)


_JS = r"""
(function () {
  const stage = document.querySelector('.deck-stage');
  const slides = Array.from(document.querySelectorAll('.slide'));
  let idx = Math.max(0, slides.findIndex(s => s.classList.contains('active')));
  if (idx < 0) idx = 0;

  function fitStage() {
    if (!stage) return;
    const vw = window.innerWidth, vh = window.innerHeight;
    const sw = 1920, sh = 1080;
    const scale = Math.min(vw / sw, vh / sh);
    const x = (vw - sw * scale) / 2;
    const y = (vh - sh * scale) / 2;
    stage.style.transform = 'translate(' + x + 'px,' + y + 'px) scale(' + scale + ')';
  }

  function show(i) {
    if (!slides.length) return;
    idx = (i + slides.length) % slides.length;
    slides.forEach((s, n) => s.classList.toggle('active', n === idx));
    const counter = document.getElementById('deck-counter');
    if (counter) counter.textContent = (idx + 1) + ' / ' + slides.length;
  }

  window.addEventListener('resize', fitStage);
  window.addEventListener('load', fitStage);
  fitStage();

  document.getElementById('btn-prev')?.addEventListener('click', () => show(idx - 1));
  document.getElementById('btn-next')?.addEventListener('click', () => show(idx + 1));
  document.getElementById('btn-notes')?.addEventListener('click', () => {
    document.body.classList.toggle('show-notes');
  });

  window.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {
      e.preventDefault(); show(idx + 1);
    } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
      e.preventDefault(); show(idx - 1);
    } else if (e.key === 'Home') {
      e.preventDefault(); show(0);
    } else if (e.key === 'End') {
      e.preventDefault(); show(slides.length - 1);
    } else if (e.key === 'n' || e.key === 'N') {
      document.body.classList.toggle('show-notes');
    }
  });

  show(idx);

  // Chart.js init (P3) — configs are JSON next to each canvas; library inlined when charts on.
  function initCharts() {
    if (typeof Chart === 'undefined') return;
    // Datalabels plugin (#84): inlined after Chart.js when charts on. The UMD
    // build self-registers with a global Chart; register explicitly too
    // (Chart.js dedupes by plugin id) so ordering is not load-dependent.
    if (typeof ChartDataLabels !== 'undefined') {
      try { Chart.register(ChartDataLabels); } catch (e) { /* already registered */ }
    }
    // N5: exterior segment-name column for stacked bars. Config-driven
    // (options.plugins.segmentNames.items = [{label, color}]); draws each
    // series name in its segment color at the mid-height of that segment
    // on the LAST bar, in the right padding gutter. No-op without config.
    try {
      Chart.register({
        id: 'segmentNames',
        afterDatasetsDraw: function (chart) {
          var opts = chart.config.options.plugins && chart.config.options.plugins.segmentNames;
          if (!opts || !opts.items || !opts.items.length) return;
          var area = chart.chartArea;
          if (!area) return;
          var nCat = chart.data.labels ? chart.data.labels.length : 0;
          if (!nCat) return;
          var ctx = chart.ctx;
          ctx.save();
          // T2 knobs (all optional, defaults = original hardcodes).
          var num = function (v, d) { return typeof v === 'number' ? v : d; };
          var fontSize = num(opts.fontSize, 12), lh = num(opts.lineHeight, 13);
          var wrapChars = num(opts.wrapChars, 16), maxLines = num(opts.maxLines, 3);
          ctx.font = "600 " + fontSize + "px 'Source Sans 3', sans-serif";
          ctx.textAlign = 'left';
          ctx.textBaseline = 'middle';
          var x = area.right + num(opts.offset, 8);
          var wrap = function (text) {
            var words = String(text).split(/\s+/), lines = [''];
            words.forEach(function (w) {
              var cur = lines[lines.length - 1];
              if (cur && (cur + ' ' + w).length > wrapChars && lines.length < maxLines) lines.push(w);
              else lines[lines.length - 1] = cur ? cur + ' ' + w : w;
            });
            return lines;
          };
          var entries = [];
          opts.items.forEach(function (item, si) {
            var meta = chart.getDatasetMeta(si);
            if (!meta || meta.hidden || !meta.data || !meta.data.length) return;
            // last visible bar element for this series
            var bar = null;
            for (var i = nCat - 1; i >= 0; i--) {
              if (meta.data[i] && typeof meta.data[i].y === 'number') { bar = meta.data[i]; break; }
            }
            if (!bar) return;
            var midY = (bar.y + (typeof bar.base === 'number' ? bar.base : bar.y)) / 2;
            var lines = wrap(item.label);
            entries.push({ y: midY - ((lines.length - 1) * lh) / 2, h: lines.length * lh, lines: lines, color: item.color || '#00175a' });
          });
          // collision resolve top-to-bottom: thin adjacent segments would
          // otherwise print on top of each other (PDF spacing recipe)
          entries.sort(function (a, b) { return a.y - b.y; });
          // gap scales with line height so larger name fonts (T2 knob) keep
          // their separation; default lh=13 yields the original 2px.
          var gap = Math.max(2, Math.round(lh / 6));
          for (var k = 1; k < entries.length; k++) {
            var minY = entries[k - 1].y + entries[k - 1].h + gap;
            if (entries[k].y < minY) entries[k].y = minY;
          }
          // clamp the whole stack inside the plot area — uniform shifts only;
          // per-entry clamping crushes the collision spacing (T2: 100%-stack
          // boards push the top segment's name above chartArea.top)
          var overflow = entries.length ? entries[entries.length - 1].y + entries[entries.length - 1].h - (area.bottom - 4) : 0;
          var shift = Math.max(0, overflow);
          var topShift = entries.length ? Math.max(0, area.top + 6 - (entries[0].y - shift)) : 0;
          entries.forEach(function (e) {
            var y0 = e.y - shift + topShift;
            ctx.fillStyle = e.color;
            e.lines.forEach(function (ln, li) { ctx.fillText(ln, x, y0 + li * lh); });
          });
          ctx.restore();
        }
      });
    } catch (e) { /* plugin registration is best-effort */ }
    // R2/T1: callout geometry in chartArea pixels. The server emits callout
    // overlays positioned as % of the wrap (close, JS-off-safe); this plugin
    // overwrites left/top/width/height in exact pixels from the live chart.
    // Config-driven (options.plugins.callouts.items). No-op without config,
    // on a degenerate chartArea (hidden slides), and on horizontal bars.
    // Fail-closed: anything it cannot compute keeps the server-side style.
    try {
      Chart.register({
        id: 'calloutGeometry',
        afterLayout: function (chart) {
          var area = chart.chartArea;
          if (!area || !(area.right > area.left) || !(area.bottom > area.top)) return;
          var canvas = chart.canvas;
          var wrap = canvas && canvas.closest ? canvas.closest('.chartjs-wrap') : null;
          if (!wrap || !canvas.id) return;
          // canvas may be inset inside the wrap; offsetLeft/offsetTop are
          // layout-space, so the CSS deck transform cannot skew the math.
          var ox = 0, oy = 0, el = canvas;
          while (el && el !== wrap) { ox += el.offsetLeft; oy += el.offsetTop; el = el.offsetParent; }
          if (el !== wrap) return;
          var xs = chart.scales.x, ys = chart.scales.y;
          if (!xs || !ys) return;
          // Clearing the opposite edge matters: the CSS fallbacks anchor
          // some nodes with bottom/right, and top+bottom both set would
          // constrain the box height (measured: chevron pill crushed to 8px).
          var px = function (node, prop, v) {
            node.style[prop] = Math.round(v * 100) / 100 + 'px';
            if (prop === 'top') node.style.bottom = 'auto';
            if (prop === 'left') node.style.right = 'auto';
          };
          // T6/R5-A: axis-break // hatch on the axis at its origin. Unlike
          // callouts this DOES apply to horizontal bars (the -v variant,
          // break on the x axis). Fail-closed: unreadable break value keeps
          // the server-side fallback position.
          var brk = wrap.querySelector('.chartjs-axis-break[data-for="' + canvas.id + '"]');
          if (brk) {
            var bto = parseFloat(brk.getAttribute('data-break-to'));
            if (!isNaN(bto)) {
              if (brk.className.indexOf('chartjs-axis-break-v') >= 0) {
                var bx = xs.getPixelForValue(bto);
                if (typeof bx === 'number' && !isNaN(bx)) {
                  bx = Math.min(Math.max(bx, area.left), area.right);
                  px(brk, 'left', ox + bx - brk.offsetWidth / 2);
                  px(brk, 'top', oy + area.bottom);
                }
              } else {
                var by = ys.getPixelForValue(bto);
                if (typeof by === 'number' && !isNaN(by)) {
                  by = Math.min(Math.max(by, area.top), area.bottom);
                  px(brk, 'left', ox + area.left - brk.offsetWidth);
                  px(brk, 'top', oy + by - brk.offsetHeight / 2);
                }
              }
            }
          }
          // T9/R5-D: annotation boxes honour their declared x/y — pixel
          // offsets within chartArea (matching the SVG fallback painter),
          // clamped so the box stays inside the plot. Fail-closed: missing
          // or non-numeric x/y keeps the CSS fallback position.
          var anns = wrap.querySelectorAll('.chartjs-annotation[data-for="' + canvas.id + '"]');
          for (var ai = 0; ai < anns.length; ai++) {
            var an = anns[ai];
            var axv = parseFloat(an.getAttribute('data-x'));
            var ayv = parseFloat(an.getAttribute('data-y'));
            if (isNaN(axv) || isNaN(ayv)) continue;
            var maxAx = Math.max(0, (area.right - area.left) - an.offsetWidth);
            var maxAy = Math.max(0, (area.bottom - area.top) - an.offsetHeight);
            px(an, 'left', ox + area.left + Math.min(Math.max(axv, 0), maxAx));
            px(an, 'top', oy + area.top + Math.min(Math.max(ayv, 0), maxAy));
          }
          if (chart.options.indexAxis === 'y') return; // callouts: horizontal bars keep the approximation (Q7)
          var opts = chart.config.options.plugins && chart.config.options.plugins.callouts;
          if (!opts || !opts.items || !opts.items.length) return;
          // NB: at afterLayout the scales are final but dataset ELEMENTS are
          // not positioned yet (Chart.js positions them after layout), so all
          // geometry derives from the scales, not from meta.data elements.
          var centerX = function (i) { // category (= bar, single dataset) center
            var x = xs.getPixelForValue(i);
            return (typeof x === 'number' && !isNaN(x)) ? x : null;
          };
          var barTopY = function (i) { // top of the bar stack/tallest bar at category i
            var stacked = chart.options.scales && chart.options.scales.y && chart.options.scales.y.stacked;
            var vals = [];
            chart.data.datasets.forEach(function (ds, d) {
              var meta = chart.getDatasetMeta(d);
              if (meta && meta.hidden) return;
              var v = ds.data && ds.data[i];
              if (typeof v === 'number' && !isNaN(v)) vals.push(v);
            });
            if (!vals.length) return null;
            var top = stacked ? vals.reduce(function (a, b) { return a + b; }, 0)
                              : Math.max.apply(null, vals);
            var y = ys.getPixelForValue(top);
            return (typeof y === 'number' && !isNaN(y)) ? y : null;
          };
          var stems = wrap.querySelectorAll('.chartjs-callout-elbow-stem[data-for="' + canvas.id + '"]');
          var stemIdx = 0;
          opts.items.forEach(function (item) {
            var node;
            if (item.type === 'chevron') {
              // T7/R5-B: split nodes — triangle stacked above a separate
              // pill, both centred on the anchor, below chartArea.bottom.
              var cx = xs.getPixelForValue(item.at);
              if (typeof cx !== 'number' || isNaN(cx)) return;
              var sel = '[data-for="' + canvas.id + '"][data-at="' + item.at + '"]';
              var tip = wrap.querySelector('.chartjs-callout-chevron-tip' + sel);
              var pill = wrap.querySelector('.chartjs-callout-chevron-pill' + sel);
              // Below the tick-label row, not merely below the plot: the PDF puts the
          // whole Refresh marker clear of the category labels. xs.bottom includes
          // the tick row; fall back to area.bottom if the scale can't report it.
          var stackY = (typeof xs.bottom === 'number' && xs.bottom > area.bottom)
            ? xs.bottom : area.bottom;
              if (tip) {
                px(tip, 'left', ox + cx - tip.offsetWidth / 2);
                px(tip, 'top', oy + stackY);
                stackY += tip.offsetHeight + 2;
              }
              if (pill) {
                px(pill, 'left', ox + cx - pill.offsetWidth / 2);
                px(pill, 'top', oy + stackY);
              }
              return;
            }
            if (item.type !== 'elbow_arrow' && item.type !== 'band') return;
            var f = item.from | 0, t = (item.to != null ? item.to : item.from) | 0;
            node = wrap.querySelector('.chartjs-callout-' + (item.type === 'elbow_arrow' ? 'elbow' : 'band') +
              '[data-for="' + canvas.id + '"][data-from="' + f + '"][data-to="' + t + '"]');
            var x0 = centerX(f), x1 = centerX(t);
            if (!node || x0 == null || x1 == null) return;
            px(node, 'left', ox + x0);
            px(node, 'width', Math.max(0, x1 - x0));
            var capsuleBottom = null;
            if (item.type === 'elbow_arrow' && item.value != null) {
              var cy = ys.getPixelForValue(item.value);
              if (typeof cy === 'number' && !isNaN(cy)) {
                px(node, 'top', oy + cy - node.offsetHeight / 2);
                capsuleBottom = cy + node.offsetHeight / 2;
              }
            }
            if (item.type === 'elbow_arrow') {
              var stem = stemIdx < stems.length ? stems[stemIdx] : null;
              stemIdx++;
              // stem: capsule bottom -> from-bar top (stack top = min y)
              if (stem && capsuleBottom != null) {
                var topY = barTopY(f);
                if (topY != null && topY > capsuleBottom) {
                  px(stem, 'left', ox + x0);
                  px(stem, 'top', oy + capsuleBottom);
                  px(stem, 'height', topY - capsuleBottom);
                }
              }
            }
          });
        }
      });
    } catch (e) { /* plugin registration is best-effort */ }
    document.querySelectorAll('script.chartjs-config').forEach(function (el) {
      var id = el.getAttribute('data-for');
      var canvas = id ? document.getElementById(id) : null;
      if (!canvas) return;
      try {
        var cfg = JSON.parse(el.textContent || '{}');
        if (!cfg.options) cfg.options = {};
        cfg.options.animation = false;
        // JSON configs cannot carry functions; resolve the pre-formatted IR
        // label matrix (#84) into the datalabels formatter here.
        var dl = cfg.options.plugins && cfg.options.plugins.datalabels;
        var bindMatrix = function (target) {
          var labelMatrix = target._labels;
          delete target._labels;
          target.formatter = function (value, context) {
            var row = labelMatrix[context.datasetIndex];
            return row && row[context.dataIndex] ? row[context.dataIndex] : '';
          };
        };
        if (dl && dl._labels) {
          bindMatrix(dl);
        } else if (dl && dl.labels) {
          // N4: named label sets (dual paint, e.g. in-segment values plus
          // stack totals) — each named entry carries its own matrix.
          Object.keys(dl.labels).forEach(function (name) {
            if (dl.labels[name] && dl.labels[name]._labels) bindMatrix(dl.labels[name]);
          });
        }
        new Chart(canvas.getContext('2d'), cfg);
      } catch (err) {
        console.warn('chart init failed', id, err);
      }
    });
  }
  initCharts();
})();
"""


def _theme_style(theme: dict[str, str] | None) -> str:
    if not theme:
        return ""
    rules = "\n  ".join(f"{k}: {v};" for k, v in theme.items())
    return f"""<style>
:root {{
  {rules}
}}
</style>
"""


def wrap_deck(
    slide_html: Sequence[str],
    *,
    meta: Mapping[str, Any],
    debug: bool = False,
    theme: dict[str, str] | None = None,
    chrome_level: str | None = None,
    delivery: DeliveryMode | str = DeliveryMode.SELF_CONTAINED,
    bundle: InlineBundle | None = None,
    features_enabled: Sequence[str] | None = None,
) -> str:
    delivery = coerce_delivery(delivery)
    if bundle is None:
        bundle = build_head_assets(delivery)
    title = esc(meta.get("title") or "Impact Slides")
    chrome_level = (chrome_level or "boardroom").strip().lower()
    chrome_cls = "gl-chrome-minimal" if chrome_level == "minimal" else ""
    body_cls = " ".join(x for x in (("gl-debug" if debug else ""), chrome_cls) if x)
    features = list(features_enabled if features_enabled is not None else [])
    deck_meta = {
        "style_preset": "BoardroomEarnings",
        "title": meta.get("title"),
        "total_slides": len(slide_html),
        "readiness_score": meta.get("readiness_score"),
        "quality_flags": meta.get("quality_flags") or [],
        "generator": "impact_slides.renderer_v2",
        "delivery": delivery.value,
        "chrome_level": chrome_level,
        "assets_inlined": list(bundle.meta.get("assets") or []),
        "features_enabled": features,
    }
    css = "\n\n".join(p for p in (bundle.font_css, load_css(debug=debug)) if p)
    theme_block = _theme_style(theme)
    slides = "\n".join(slide_html)
    # Minimal chrome omits the deck-controls markup entirely (not just CSS-hide),
    # so stage-only decks carry no product control chrome in the DOM (#83/F14).
    controls_html = (
        ""
        if chrome_level == "minimal"
        else """<div class="deck-controls" aria-label="Deck controls">
  <button type="button" id="btn-prev" title="Previous">←</button>
  <button type="button" id="btn-next" title="Next">→</button>
  <button type="button" id="btn-notes" title="Toggle notes">N</button>
  <span id="deck-counter" style="color:#fff;font:600 13px var(--font-body);align-self:center"></span>
</div>"""
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
{bundle.head_html}
<style>
{css}
</style>
{theme_block}
</head>
<body class="{body_cls}">
{sprite_svg()}
<div class="deck-viewport">
  <div class="deck-stage" id="deck-stage">
{slides}
  </div>
</div>
{controls_html}
<script type="application/json" id="DECK_META">{json.dumps(deck_meta, ensure_ascii=False)}</script>
<script>
{_JS}
</script>
</body>
</html>
"""
