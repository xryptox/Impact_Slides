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
    document.querySelectorAll('script.chartjs-config').forEach(function (el) {
      var id = el.getAttribute('data-for');
      var canvas = id ? document.getElementById(id) : null;
      if (!canvas) return;
      try {
        var cfg = JSON.parse(el.textContent || '{}');
        if (!cfg.options) cfg.options = {};
        cfg.options.animation = false;
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
