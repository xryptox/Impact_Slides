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
