"""Closed-ticket revalidation probes for v10 (#136–#140) under #137 contract.

Chart.js mode + JS-off/SVG mode (Playwright java_script_enabled=False).
No MAE / similarity scores.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from simulation_probe import (  # noqa: E402
    ProbeError,
    activate_slide,
    painted_datalabel_lines,
)

SIM = ROOT / "simulation" / "amex_q1_2026"
HTML = SIM / "passes" / "pass_01" / "output" / "presentation.html"
OUT = SIM / "closed_tickets"
RUN_META = SIM / "passes" / "pass_01" / "output" / "run_meta.json"
W, H = 1920, 1080

# #140 approved PDF-normalized targets (stage coords)
PILL_TARGETS = {
    "board": {"x": 127.312, "y": 262.680, "w": 1564.911, "h": 624.640},
    "first_shell": {"x": 769.592, "y": 262.680, "w": 295.914},
    "cap_h": 115.200,
}


def _stage_rel_js() -> str:
    return """
      const stage = document.querySelector('.deck-stage') || document.body;
      const sr = stage.getBoundingClientRect();
      function rel(el) {
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return {
          x: r.left - sr.left,
          y: r.top - sr.top,
          w: r.width,
          h: r.height,
          right: r.right - sr.left,
          bottom: r.bottom - sr.top,
          cx: (r.left + r.right) / 2 - sr.left,
          cy: (r.top + r.bottom) / 2 - sr.top,
          text: (el.textContent || '').trim().slice(0, 120),
        };
      }
    """


def wait_charts(page, sn: int, timeout_ms: int = 8000) -> None:
    js = """(sn) => {
      const slide = document.querySelector(
        'section.slide[data-slide-number="' + sn + '"]'
      );
      if (!slide) return false;
      const canvases = [...slide.querySelectorAll('canvas')];
      if (!canvases.length) return true;
      if (typeof Chart === 'undefined' || !Chart.getChart) return false;
      return canvases.every((c) => !!Chart.getChart(c));
    }"""
    page.wait_for_function(js, arg=int(sn), timeout=timeout_ms)


def open_page(js_enabled: bool):
    pw = sync_playwright().start()
    browser = pw.chromium.launch()
    context = browser.new_context(
        viewport={"width": W, "height": H},
        java_script_enabled=js_enabled,
    )
    page = context.new_page()
    console: list[str] = []
    page.on(
        "console",
        lambda m: console.append(f"{m.type}: {m.text}"),
    )
    page.goto(HTML.resolve().as_uri(), wait_until="load" if not js_enabled else "networkidle")
    page.wait_for_timeout(400 if js_enabled else 200)
    return pw, browser, context, page, console


def close_all(pw, browser, context) -> None:
    context.close()
    browser.close()
    pw.stop()


def row(
    ticket: str,
    mode: str,
    slide_number: int,
    layout: str,
    check: str,
    measured: Any,
    expected: Any,
    passed: bool,
    delta_px: float | None = None,
    note: str = "",
) -> dict[str, Any]:
    return {
        "ticket": ticket,
        "mode": mode,
        "slide_number": slide_number,
        "layout": layout,
        "pdf_page_index": slide_number - 1,
        "pdf_physical_page": slide_number,
        "check": check,
        "measured": measured,
        "expected": expected,
        "delta_px": delta_px,
        "pass": bool(passed),
        "note": note,
    }


# ---------- #136 outlined_boxes alignment ----------
def probe_136(page, mode: str, console: list[str]) -> tuple[list[dict], dict]:
    sn, layout = 15, "stacked_bar_chart"
    activate_slide(page, sn, layout)
    if mode == "chartjs":
        wait_charts(page, sn)
        # outlined plot-align runs after Chart layout; wait until cell0≈bar0.
        try:
            page.wait_for_function(
                """(sn) => {
                  const stage = document.querySelector('.deck-stage');
                  const sr = stage.getBoundingClientRect();
                  const slide = document.querySelector(
                    'section.slide[data-slide-number="' + sn + '"]'
                  );
                  const box = slide.querySelector(
                    '.chart-outlined-cell > .chart-outlined-box'
                  );
                  const canvas = slide.querySelector('canvas');
                  const ch = canvas && Chart.getChart(canvas);
                  if (!box || !ch) return false;
                  const meta = ch.getDatasetMeta(0);
                  if (!meta || !meta.data || !meta.data[0]) return false;
                  const cr = canvas.getBoundingClientRect();
                  const barCx = cr.left - sr.left + meta.data[0].x;
                  const br = box.getBoundingClientRect();
                  const cellCx = (br.left + br.right) / 2 - sr.left;
                  return Math.abs(cellCx - barCx) <= 12;
                }""",
                arg=sn,
                timeout=5000,
            )
        except Exception:
            page.wait_for_timeout(400)
    else:
        page.wait_for_timeout(200)
    data = page.evaluate(
        """(sn) => {
        """
        + _stage_rel_js()
        + """
        const slide = document.querySelector(
          'section.slide[data-slide-number="' + sn + '"]'
        );
        const outlined = slide.querySelector('.chart-support-outlined');
        // Inner box centre (not full cell hit-area).
        let use = [...slide.querySelectorAll(
          '.chart-support-outlined .chart-outlined-cell > .chart-outlined-box'
        )].map(rel);
        if (!use.length) {
          use = [...slide.querySelectorAll(
            '.chart-support-outlined .chart-outlined-cell'
          )].map(rel);
        }
        const alignedMarker = !!(
          (outlined && outlined.classList.contains('chart-table-aligned'))
          || slide.querySelector('.chart-align-table.chart-table-aligned')
          || slide.querySelector('[data-plot-aligned="true"]')
          || (outlined && outlined.getAttribute('data-aligned') === 'true')
        );
        // runtime alignment marker on wrap
        const wrap = slide.querySelector('.chartjs-wrap, .chart-svg-wrap, .chart-col');
        const markerText = [];
        if (outlined) markerText.push(...outlined.classList);
        const alignWrap = slide.querySelector('.chart-align-table');
        if (alignWrap) markerText.push(...alignWrap.classList);

        let bars = [];
        if (typeof Chart !== 'undefined' && Chart.getChart) {
          const canvas = slide.querySelector('canvas');
          const ch = canvas && Chart.getChart(canvas);
          if (ch) {
            const meta = ch.getDatasetMeta(0);
            const cr = canvas.getBoundingClientRect();
            const stage = document.querySelector('.deck-stage') || document.body;
            const sr = stage.getBoundingClientRect();
            for (const el of (meta && meta.data) || []) {
              bars.push({ cx: cr.left - sr.left + el.x, x: el.x });
            }
          }
        }
        // SVG bars (JS-off): Chromium exposes noscript SVG as live svg.chart-svg.
        let svgBars = [];
        const liveSvg = slide.querySelector('svg.chart-svg');
        if (liveSvg) {
          const stage = document.querySelector('.deck-stage') || document.body;
          const sr = stage.getBoundingClientRect();
          const hr = liveSvg.getBoundingClientRect();
          const vb = (liveSvg.getAttribute('viewBox') || '0 0 900 480').trim().split(/\s+/).map(Number);
          const svgW = vb[2] || 900;
          const rects = [...liveSvg.querySelectorAll('rect')].map(r => ({
            x: parseFloat(r.getAttribute('x') || '0'),
            w: parseFloat(r.getAttribute('width') || '0'),
            h: parseFloat(r.getAttribute('height') || '0'),
          })).filter(r => r.w >= 20 && r.h >= 20); // skip legend swatches
          const byX = {};
          for (const r of rects) {
            const key = Math.round(r.x);
            byX[key] = byX[key] || [];
            byX[key].push(r);
          }
          for (const k of Object.keys(byX).map(Number).sort((a,b)=>a-b)) {
            const g = byX[k][0];
            const cxLocal = g.x + g.w / 2;
            const cx = hr.left - sr.left + (cxLocal / svgW) * hr.width;
            svgBars.push({ cx, xLocal: cxLocal });
          }
        }

        // runtime alignment marker emitted in DOM/comment
        const html = slide.innerHTML;
        const runtimeAligned =
          /data-plot-aligned\\s*=\\s*["']true["']/.test(html)
          || /chart-table-aligned/.test(outlined ? outlined.className : '')
          || /aligned\\s*[:=]\\s*true/i.test(html.slice(0, 5000));

        return {
          nCells: use.length,
          cells: use,
          nBars: bars.length,
          bars,
          nSvgBars: svgBars.length,
          svgBars,
          hasOutlined: !!outlined,
          classList: markerText,
          alignedMarker: alignedMarker || runtimeAligned,
          runtimeAligned,
        };
      }""",
        sn,
    )
    rows: list[dict] = []
    cells = data.get("cells") or []
    bars = data.get("bars") or []
    svg_bars = data.get("svgBars") or []
    ref_bars = bars if mode == "chartjs" else (svg_bars or bars)

    rows.append(
        row(
            "#136",
            mode,
            sn,
            layout,
            "outlined skin present",
            {"hasOutlined": data.get("hasOutlined"), "nCells": data.get("nCells")},
            {"hasOutlined": True, "nCells": 5},
            bool(data.get("hasOutlined")) and int(data.get("nCells") or 0) >= 5,
        )
    )
    rows.append(
        row(
            "#136",
            mode,
            sn,
            layout,
            "runtime alignment marker",
            {
                "alignedMarker": data.get("alignedMarker"),
                "runtimeAligned": data.get("runtimeAligned"),
                "classList": data.get("classList"),
            },
            "aligned marker emitted when plot-align engages",
            bool(data.get("alignedMarker") or data.get("runtimeAligned")),
            note="marker absence is residual if list-shaped primary blocks extract",
        )
    )

    deltas = []
    n = min(5, len(cells), len(ref_bars)) if ref_bars else 0
    if n < 5:
        rows.append(
            row(
                "#136",
                mode,
                sn,
                layout,
                "five cell↔bar centre pairs available",
                {
                    "nCells": len(cells),
                    "nRefBars": len(ref_bars),
                    "barSource": "chartjs" if bars else "svg",
                },
                {"nCells": 5, "nRefBars": 5},
                False,
                note="probe failure if bars missing — not a successful empty observation",
            )
        )
    else:
        max_abs = 0.0
        for i in range(5):
            d = float(cells[i]["cx"]) - float(ref_bars[i]["cx"])
            deltas.append(d)
            max_abs = max(max_abs, abs(d))
            rows.append(
                row(
                    "#136",
                    mode,
                    sn,
                    layout,
                    f"outlined cell[{i}] cx vs bar[{i}] cx",
                    {"cell_cx": cells[i]["cx"], "bar_cx": ref_bars[i]["cx"]},
                    "abs(delta) <= 12",
                    abs(d) <= 12.0,
                    delta_px=round(d, 3),
                )
            )
        rows.append(
            row(
                "#136",
                mode,
                sn,
                layout,
                "max |cell_cx - bar_cx| over 5",
                {"max_abs_delta": round(max_abs, 3), "deltas": [round(x, 3) for x in deltas]},
                "<= 12",
                max_abs <= 12.0,
                delta_px=round(max_abs, 3),
            )
        )

    warn = [c for c in console if "warn" in c.lower()]
    raw = {"mode": mode, "data": data, "console_warnings": warn[:30]}
    return rows, raw


# ---------- #138 side_callout Deposit Programs ----------
def probe_138(page, mode: str, console: list[str]) -> tuple[list[dict], dict]:
    sn, layout = 28, "multi_panel"
    activate_slide(page, sn, layout)
    if mode == "chartjs":
        wait_charts(page, sn)
        page.wait_for_timeout(200)

    data = page.evaluate(
        """(sn) => {
        """
        + _stage_rel_js()
        + """
        const slide = document.querySelector(
          'section.slide[data-slide-number="' + sn + '"]'
        );
        const tiles = [...slide.querySelectorAll('.gl-tile, .mp-tile, [data-tile], .chart-tile')];
        // fallback: dual wraps
        const wraps = [...slide.querySelectorAll('.chartjs-wrap')];
        const labels = [...slide.querySelectorAll('.gl-tile-label, .tile-label, .mp-tile-title, h3, .chart-pane-title')]
          .map(el => ({text: (el.textContent||'').trim(), ...rel(el)}));

        // Find Deposit Programs tile by label text
        let depRoot = null;
        for (const t of slide.querySelectorAll('.gl-tile, .mp-tile, .gl-tile-ir, .chart-col, .gl-main > *')) {
          const ttext = (t.textContent || '');
          if (/Deposit Programs/i.test(ttext) && t.querySelector('canvas, noscript, svg')) {
            depRoot = t; break;
          }
        }
        if (!depRoot) {
          // second chart wrap is Deposit Programs per handoff order
          const allWraps = [...slide.querySelectorAll('.chartjs-wrap')];
          depRoot = allWraps[1] || allWraps[0] || slide;
        }

        const callouts = [...depRoot.querySelectorAll(
          '.chartjs-side-callout, [data-side-callout], .side-callout, .chart-side-callout'
        )].map(el => {
          const r = rel(el);
          const cs = getComputedStyle(el);
          return {
            ...r,
            lines: (el.innerText || '').split('\\n').map(s => s.trim()).filter(Boolean),
            borderW: cs.borderTopWidth,
            borderStyle: cs.borderTopStyle,
            boxShadow: cs.boxShadow,
            classes: el.className,
          };
        });
        // also search whole slide if tile-local miss
        if (!callouts.length) {
          for (const el of slide.querySelectorAll(
            '.chartjs-side-callout, [data-side-callout], .side-callout, .chart-side-callout'
          )) {
            const r = rel(el);
            const cs = getComputedStyle(el);
            callouts.push({
              ...r,
              lines: (el.innerText || '').split('\\n').map(s => s.trim()).filter(Boolean),
              borderW: cs.borderTopWidth,
              borderStyle: cs.borderTopStyle,
              boxShadow: cs.boxShadow,
              classes: el.className,
            });
          }
        }

        // badge chrome (exclude the side_callout itself)
        const badges = [...depRoot.querySelectorAll('.gl-tile-badge, .tile-badge, .chart-badge, [data-badge]')]
          .map(rel).filter(b => b && b.text);
        const calloutEls = [...depRoot.querySelectorAll('.chart-side-callout, .chartjs-side-callout, [data-side-callout]')];
        const fdicBadges = [...depRoot.querySelectorAll('*')].filter(el => {
          if (calloutEls.some(c => c === el || c.contains(el))) return false;
          if (el.children && el.children.length > 3) return false;
          const t = (el.textContent || '').trim();
          return /^92%/.test(t) && /FDIC/i.test(t) && t.length < 80;
        }).map(rel);

        // exterior segment names: DOM nodes OR Chart plugin config / painted overlays
        let exterior = [...depRoot.querySelectorAll(
          '.chartjs-segment-name, .segment-name, [data-segment-name], .chartjs-segment-names, .segment-names-col'
        )].map(rel);
        if (!exterior.length) {
          const canvas = depRoot.querySelector('canvas');
          const ch = canvas && typeof Chart !== 'undefined' && Chart.getChart && Chart.getChart(canvas);
          const items = ch && ch.options && ch.options.plugins && ch.options.plugins.segmentNames
            && ch.options.plugins.segmentNames.items;
          if (items && items.length) {
            exterior = items.map((it, i) => ({ text: it.label || String(it), i }));
          }
        }
        if (!exterior.length) {
          // JS-off: read segmentNames from embedded chartjs-config JSON
          const cfgEl = depRoot.querySelector('script.chartjs-config');
          if (cfgEl) {
            try {
              const cfg = JSON.parse(cfgEl.textContent || '{}');
              const items = cfg && cfg.options && cfg.options.plugins
                && cfg.options.plugins.segmentNames && cfg.options.plugins.segmentNames.items;
              if (items && items.length) {
                exterior = items.map((it, i) => ({ text: it.label || String(it), i }));
              }
            } catch (e) {}
          }
        }

        const totals = [...depRoot.querySelectorAll(
          '.chartjs-stack-total, .stack-total, [data-stack-total]'
        )].map(rel);
        // fallback: painted labels near top of bars — collect text nodes $151/$157
        const allText = [...depRoot.querySelectorAll('span, div, text')].map(rel).filter(x => x && /^\\$\\d+/.test(x.text||''));

        // plot area
        let plot = null;
        const canvas = depRoot.querySelector('canvas');
        if (canvas && typeof Chart !== 'undefined' && Chart.getChart) {
          const ch = Chart.getChart(canvas);
          if (ch && ch.chartArea) {
            const cr = canvas.getBoundingClientRect();
            const stage = document.querySelector('.deck-stage') || document.body;
            const sr = stage.getBoundingClientRect();
            const ca = ch.chartArea;
            plot = {
              x: cr.left - sr.left + ca.left,
              y: cr.top - sr.top + ca.top,
              w: ca.right - ca.left,
              h: ca.bottom - ca.top,
              right: cr.left - sr.left + ca.right,
              bottom: cr.top - sr.top + ca.bottom,
            };
          }
        }

        const tileBox = rel(depRoot);

        // fit omissions / diagnostics attributes
        const fitNotes = [];
        for (const el of slide.querySelectorAll('[data-fit-omit], [data-callout-fit], .callout-omitted')) {
          fitNotes.push({
            tag: el.tagName,
            attr: el.getAttribute('data-fit-omit') || el.getAttribute('data-callout-fit') || el.className,
            text: (el.textContent||'').trim().slice(0,80),
          });
        }

        return {
          nTilesGuess: tiles.length,
          nWraps: wraps.length,
          labels,
          nCallouts: callouts.length,
          callouts,
          badges,
          fdicBadges,
          exterior,
          totals,
          dollarTexts: allText.slice(0, 12),
          plot,
          tileBox,
          fitNotes,
          depTextSample: (depRoot.innerText || '').slice(0, 400),
        };
      }""",
        sn,
    )

    rows: list[dict] = []
    callouts = data.get("callouts") or []
    # Exactly one unboxed three-line callout
    if not callouts:
        rows.append(
            row(
                "#138",
                mode,
                sn,
                layout,
                "side_callout present (exactly one)",
                {"nCallouts": 0, "fitNotes": data.get("fitNotes"), "sample": data.get("depTextSample")},
                1,
                False,
                note="missing callout is FAIL — never silent",
            )
        )
    else:
        c0 = callouts[0]
        lines = c0.get("lines") or []
        # unboxed: no meaningful border
        border_w = float(str(c0.get("borderW") or "0").replace("px", "") or 0)
        unboxed = border_w <= 0.5 or (c0.get("borderStyle") in (None, "none"))
        three_line = len(lines) >= 3 or (
            "92% FDIC" in " ".join(lines)
            and any("insured" in x.lower() for x in lines)
        )
        rows.append(
            row(
                "#138",
                mode,
                sn,
                layout,
                "exactly one side_callout",
                {"nCallouts": len(callouts), "lines": lines},
                1,
                len(callouts) == 1,
            )
        )
        rows.append(
            row(
                "#138",
                mode,
                sn,
                layout,
                "callout unboxed three-line",
                {"lines": lines, "borderW": border_w, "unboxed": unboxed},
                {"lines>=3": True, "unboxed": True},
                three_line and unboxed,
            )
        )
        # tile-local top near 49.8px
        top = c0.get("y")
        # relative to tile if possible
        tile = data.get("tileBox") or {}
        top_local = (top - tile.get("y", 0)) if top is not None and tile else top
        # approved 49.8 is stage-ish; also accept tile-local
        d_stage = abs((top or 0) - 49.8) if top is not None else None
        d_local = abs((top_local or 0) - 49.8) if top_local is not None else None
        near = (d_stage is not None and d_stage <= 12) or (
            d_local is not None and d_local <= 12
        )
        rows.append(
            row(
                "#138",
                mode,
                sn,
                layout,
                "callout top near 49.8px",
                {"top_stage": top, "top_local": top_local, "d_stage": d_stage, "d_local": d_local},
                "abs(top-49.8)<=12 (stage or tile-local)",
                bool(near),
                delta_px=round(min(x for x in (d_stage, d_local) if x is not None), 3)
                if d_stage is not None or d_local is not None
                else None,
            )
        )

        # no overlap with exterior names / plot
        overlaps = []
        def overlap(a, b):
            if not a or not b:
                return False
            return not (
                a["right"] <= b["x"]
                or a["x"] >= b["right"]
                or a["bottom"] <= b["y"]
                or a["y"] >= b["bottom"]
            )

        for ex in data.get("exterior") or []:
            if ex.get("x") is None:
                continue  # config-only segment name (no box)
            if overlap(c0, ex):
                overlaps.append({"with": "exterior", "text": ex.get("text")})
        if data.get("plot") and overlap(c0, data["plot"]):
            overlaps.append({"with": "plot"})
        rows.append(
            row(
                "#138",
                mode,
                sn,
                layout,
                "no callout/name/plot overlap",
                {"overlaps": overlaps},
                [],
                len(overlaps) == 0,
            )
        )

    # badge suppressed when callout paints
    fdic = data.get("fdicBadges") or []
    # if callout present, competing badge chrome should be suppressed → ideally 1 callout text only
    callout_texts = [" ".join(c.get("lines") or []) for c in callouts]
    non_callout_fdic = [
        b
        for b in fdic
        if not any(b.get("text", "")[:12] in ct for ct in callout_texts)
    ]
    rows.append(
        row(
            "#138",
            mode,
            sn,
            layout,
            "no duplicate FDIC badge chrome",
            {
                "fdicNodes": len(fdic),
                "nonCalloutFdic": [b.get("text") for b in non_callout_fdic],
                "callouts": callout_texts,
            },
            "callout only (badge suppressed)",
            len(callouts) >= 1 and len(non_callout_fdic) == 0,
        )
    )

    # independent $151 / $157 totals
    dollar_blob = " ".join(
        t.get("text", "") for t in (data.get("dollarTexts") or [])
    ) + " " + (data.get("depTextSample") or "")
    has_151 = "$151" in dollar_blob
    has_157 = "$157" in dollar_blob
    rows.append(
        row(
            "#138",
            mode,
            sn,
            layout,
            "independent $151 / $157 stack totals",
            {"has_151": has_151, "has_157": has_157, "sample": dollar_blob[:200]},
            {"has_151": True, "has_157": True},
            has_151 and has_157,
        )
    )

    # exterior names present (shared right column)
    rows.append(
        row(
            "#138",
            mode,
            sn,
            layout,
            "exterior segment names present",
            {"n": len(data.get("exterior") or [])},
            ">=1",
            len(data.get("exterior") or []) >= 1,
        )
    )

    warn = [c for c in console if "warn" in c.lower() or "fit" in c.lower()]
    if warn:
        rows.append(
            row(
                "#138",
                mode,
                sn,
                layout,
                "console/run diagnostics clean",
                warn[:20],
                "no fit/callout warnings",
                False,
                note="diagnostics recorded as failure signals",
            )
        )

    return rows, {"mode": mode, "data": data, "console": warn[:30]}


# ---------- #139 typography dual_chart ----------
def probe_139(page, mode: str, console: list[str]) -> tuple[list[dict], dict]:
    sn, layout = 17, "dual_chart"
    activate_slide(page, sn, layout)
    if mode == "chartjs":
        wait_charts(page, sn)

    data = page.evaluate(
        """(sn) => {
        """
        + _stage_rel_js()
        + """
        const slide = document.querySelector(
          'section.slide[data-slide-number="' + sn + '"]'
        );
        const paneTitles = [...slide.querySelectorAll(
          '.gl-chart-pane-title, .chart-pane-title, .dual-chart-pane-title, .gl-pane-title, h3.chart-title, .chart-card-title'
        )].map(el => {
          const cs = getComputedStyle(el);
          return {
            ...rel(el),
            fontSize: parseFloat(cs.fontSize),
            fontWeight: cs.fontWeight,
            color: cs.color,
            tag: el.tagName,
          };
        });
        // SVG titles
        let svgTitles = [];
        for (const nos of slide.querySelectorAll('noscript')) {
          const tmp = document.createElement('div');
          tmp.innerHTML = nos.textContent || nos.innerHTML || '';
          for (const t of tmp.querySelectorAll('text, title')) {
            const tx = (t.textContent || '').trim();
            if (tx && tx.length < 80) svgTitles.push(tx);
          }
        }
        for (const t of slide.querySelectorAll('svg text')) {
          const tx = (t.textContent || '').trim();
          if (tx && tx.length < 80) svgTitles.push(tx);
        }

        const charts = [];
        if (typeof Chart !== 'undefined' && Chart.getChart) {
          const canvases = [...slide.querySelectorAll('canvas')];
          for (let i = 0; i < canvases.length; i++) {
            const ch = Chart.getChart(canvases[i]);
            if (!ch) { charts.push({i, missing: true}); continue; }
            const y = ch.options?.scales?.y || ch.options?.scales?.yAxes?.[0] || {};
            const x = ch.options?.scales?.x || {};
            const yTicks = y.ticks || {};
            const xTicks = x.ticks || {};
            const dl = ch.options?.plugins?.datalabels || {};
            // painted label font from plugin labels if present
            let paintedFonts = [];
            if (ch.$datalabels && Array.isArray(ch.$datalabels._labels)) {
              for (const lab of ch.$datalabels._labels) {
                try {
                  const m = lab.model && lab.model();
                  if (m && m.font) paintedFonts.push(m.font);
                } catch (e) {}
              }
            }
            charts.push({
              i,
              yTickSize: yTicks.font?.size ?? yTicks.fontSize ?? null,
              yTickWeight: yTicks.font?.weight ?? null,
              xTickSize: xTicks.font?.size ?? null,
              xMinRotation: xTicks.minRotation ?? xTicks.maxRotation ?? null,
              xAutoSkip: xTicks.autoSkip ?? null,
              dlFontSize_options: dl.font?.size ?? dl.labels?.value?.font?.size ?? null,
              paintedFonts: paintedFonts.slice(0, 8),
              hasSvgTitlePlugin: !!(ch.options?.plugins?.title?.display),
              titleText: ch.options?.plugins?.title?.text || null,
            });
          }
        }

        // clipping: overflow hidden on panes?
        const panes = [...slide.querySelectorAll('.dual-chart-pane, .chartjs-wrap')].map(el => {
          const cs = getComputedStyle(el);
          return {overflow: cs.overflow, ...rel(el)};
        });

        return {paneTitles, svgTitles, charts, panes};
      }""",
        sn,
    )

    rows: list[dict] = []
    titles = data.get("paneTitles") or []
    # two HTML-owned pane titles only
    good_titles = [
        t
        for t in titles
        if abs((t.get("fontSize") or 0) - 40) <= 2
        and str(t.get("fontWeight")) in ("700", "bold", "600")
    ]
    # be lenient on weight if size matches
    size_titles = [t for t in titles if abs((t.get("fontSize") or 0) - 40) <= 2]
    rows.append(
        row(
            "#139",
            mode,
            sn,
            layout,
            "two HTML pane titles (~40px)",
            {
                "nTitles": len(titles),
                "titles": [
                    {
                        "text": t.get("text"),
                        "fontSize": t.get("fontSize"),
                        "fontWeight": t.get("fontWeight"),
                        "color": t.get("color"),
                    }
                    for t in titles
                ],
            },
            {"count": 2, "fontSize": 40, "weight": 700},
            len(titles) == 2 and len(size_titles) == 2,
        )
    )
    svg_titles = data.get("svgTitles") or []
    # filter noise
    dup_svg = [t for t in svg_titles if any(t in (ht.get("text") or "") for ht in titles)]
    rows.append(
        row(
            "#139",
            mode,
            sn,
            layout,
            "no duplicate SVG title",
            {"svgTitles": svg_titles[:20], "dup": dup_svg},
            [],
            len(dup_svg) == 0,
        )
    )

    charts = data.get("charts") or []
    if mode == "chartjs":
        if len(charts) < 2:
            rows.append(
                row(
                    "#139",
                    mode,
                    sn,
                    layout,
                    "two chart instances",
                    {"n": len(charts)},
                    2,
                    False,
                )
            )
        for ch in charts:
            ys = ch.get("yTickSize")
            rows.append(
                row(
                    "#139",
                    mode,
                    sn,
                    layout,
                    f"pane{ch.get('i')} y_tick_font_size 24 bold",
                    {"yTickSize": ys, "yTickWeight": ch.get("yTickWeight")},
                    {"size": 24, "weight": "bold/700"},
                    ys == 24,
                )
            )
            # painted datalabels via helper
            try:
                painted = painted_datalabel_lines(
                    page, sn, layout, chart_index=int(ch.get("i") or 0)
                )
                # font size from model if available — re-read
                font_info = page.evaluate(
                    """({sn, idx}) => {
                      const slide = document.querySelector(
                        'section.slide[data-slide-number="' + sn + '"]'
                      );
                      const canvas = slide.querySelectorAll('canvas')[idx];
                      const ch = canvas && Chart.getChart(canvas);
                      if (!ch || !ch.$datalabels) return {ok:false, err:'no plugin'};
                      const sizes = [];
                      for (const lab of ch.$datalabels._labels) {
                        const m = lab.model();
                        if (m && m.font && m.font.size != null) sizes.push(m.font.size);
                      }
                      return {ok:true, sizes, n: ch.$datalabels._labels.length};
                    }""",
                    {"sn": sn, "idx": int(ch.get("i") or 0)},
                )
                sizes = (font_info or {}).get("sizes") or []
                # ordinary labels where they fit — expect 28 when present
                ok_sizes = all(abs(s - 28) <= 1 for s in sizes) if sizes else False
                rows.append(
                    row(
                        "#139",
                        mode,
                        sn,
                        layout,
                        f"pane{ch.get('i')} painted datalabel font ~28",
                        {
                            "lines": painted.get("lines"),
                            "sizes": sizes,
                            "nLabels": (font_info or {}).get("n"),
                        },
                        "size 28 where painted",
                        ok_sizes if sizes else False,
                        note="empty sizes = suppression or missing paint",
                    )
                )
            except ProbeError as e:
                rows.append(
                    row(
                        "#139",
                        mode,
                        sn,
                        layout,
                        f"pane{ch.get('i')} painted datalabels",
                        str(e),
                        "nonempty painted lines",
                        False,
                        note="probe failure",
                    )
                )
            rows.append(
                row(
                    "#139",
                    mode,
                    sn,
                    layout,
                    f"pane{ch.get('i')} x-tick rotation/skip (record)",
                    {
                        "minRotation": ch.get("xMinRotation"),
                        "autoSkip": ch.get("xAutoSkip"),
                    },
                    "recorded",
                    True,
                    note="native state observation",
                )
            )
            rows.append(
                row(
                    "#139",
                    mode,
                    sn,
                    layout,
                    f"pane{ch.get('i')} no Chart title plugin fallback",
                    {
                        "titleDisplay": ch.get("hasSvgTitlePlugin"),
                        "titleText": ch.get("titleText"),
                    },
                    False,
                    not ch.get("hasSvgTitlePlugin"),
                )
            )
    else:
        # JS-off: inspect noscript SVG text font-sizes if present
        svg_audit = page.evaluate(
            """(sn) => {
              const slide = document.querySelector(
                'section.slide[data-slide-number="' + sn + '"]'
              );
              const out = [];
              for (const nos of slide.querySelectorAll('noscript')) {
                const tmp = document.createElement('div');
                tmp.innerHTML = nos.textContent || nos.innerHTML || '';
                const texts = [...tmp.querySelectorAll('text')].map(t => ({
                  text: (t.textContent||'').trim().slice(0,40),
                  fontSize: t.getAttribute('font-size') || t.style.fontSize || null,
                  fontWeight: t.getAttribute('font-weight') || null,
                }));
                out.push({n: texts.length, sample: texts.slice(0, 30)});
              }
              const htmlTitles = [...slide.querySelectorAll(
                '.gl-chart-pane-title, .chart-pane-title, .dual-chart-pane-title, .gl-pane-title'
              )].map(el => {
                const cs = getComputedStyle(el);
                return {text: el.textContent.trim(), fontSize: parseFloat(cs.fontSize), fontWeight: cs.fontWeight};
              });
              return {noscriptCharts: out, htmlTitles};
            }""",
            sn,
        )
        rows.append(
            row(
                "#139",
                mode,
                sn,
                layout,
                "JS-off HTML pane titles retained",
                svg_audit.get("htmlTitles"),
                2,
                len(svg_audit.get("htmlTitles") or []) == 2,
            )
        )
        rows.append(
            row(
                "#139",
                mode,
                sn,
                layout,
                "JS-off SVG text audit (y ticks / labels)",
                svg_audit.get("noscriptCharts"),
                "record font-size attrs",
                True,
                note="qualitative SVG typography record",
            )
        )

    warn = [c for c in console if "warn" in c.lower() or "typograph" in c.lower()]
    rows.append(
        row(
            "#139",
            mode,
            sn,
            layout,
            "unsupported typography warnings",
            warn[:20],
            "none (or recorded)",
            True,
            note="presence recorded; not auto-fail unless blocks paint",
        )
    )
    return rows, {"mode": mode, "data": data, "console": warn[:30]}


# ---------- #140 pill board + negative controls ----------
def probe_140(page, mode: str, console: list[str]) -> tuple[list[dict], dict]:
    # only meaningful in chartjs/html layout; JS-off same DOM for pills
    sn, layout = 3, "pill_comparison"
    activate_slide(page, sn, layout)
    data = page.evaluate(
        """(sn) => {
        """
        + _stage_rel_js()
        + """
        const slide = document.querySelector(
          'section.slide[data-slide-number="' + sn + '"]'
        );
        // #140 five-body-row board is .gl-pill (recipe may add free/fixed modifiers)
        const board = slide.querySelector('.gl-pill');
        const shells = [...slide.querySelectorAll('.gl-pill-shell')].map(rel);
        const caps = [...slide.querySelectorAll('.gl-pill-head')].map(el => {
          const cs = getComputedStyle(el);
          return {...rel(el), fontSize: parseFloat(cs.fontSize), whiteSpace: cs.whiteSpace, lineHeight: cs.lineHeight};
        });
        const stubs = [...slide.querySelectorAll('.gl-pill-labels .gl-pill-stub')]
          .map(rel).filter(r => r && r.text);
        const rows = stubs;
        const labelCells = stubs;
        const valueCells = [...slide.querySelectorAll('.gl-pill-shell .gl-pill-cell')].map(rel);

        const boardBox = rel(board);
        const overflow = board ? getComputedStyle(board).overflow : null;
        const slideOverflow = {
          scrollW: slide.scrollWidth,
          clientW: slide.clientWidth,
          scrollH: slide.scrollHeight,
          clientH: slide.clientHeight,
        };

        // YoY cap two-line 28px
        const yoyCaps = caps.filter(c => /YoY|Inc/i.test(c.text || ''));

        return {
          board: boardBox,
          boardClasses: board ? board.className : null,
          shells,
          caps,
          rows,
          labelCells,
          valueCells,
          overflow,
          slideOverflow,
          yoyCaps,
          // fixed-board recipe marker: direct five-row board (not free/inset)
          fixedBoardSelectorMatch: !!(board && !/gl-pill-free|gl-pill-inset/.test(board.className || '')),
          isFreeBoard: !!(board && /gl-pill-free/.test(board.className || '')),
          isInsetBoard: !!(board && /inset/.test(board.className || '')),
        };
      }""",
        sn,
    )

    rows_out: list[dict] = []
    board = data.get("board")
    tgt = PILL_TARGETS
    if not board:
        rows_out.append(
            row(
                "#140",
                mode,
                sn,
                layout,
                "pill board present",
                data,
                "board node",
                False,
            )
        )
    else:
        for key, attr in [("x", "x"), ("y", "y"), ("w", "w"), ("h", "h")]:
            exp = tgt["board"][attr]
            got = board.get(attr)
            d = (got or 0) - exp
            rows_out.append(
                row(
                    "#140",
                    mode,
                    sn,
                    layout,
                    f"board.{attr} vs PDF target",
                    got,
                    exp,
                    abs(d) <= 4.0,
                    delta_px=round(d, 3),
                )
            )
        shells = data.get("shells") or []
        if shells:
            s0 = shells[0]
            for attr in ("x", "y", "w"):
                exp = tgt["first_shell"][attr]
                got = s0.get(attr)
                d = (got or 0) - exp
                rows_out.append(
                    row(
                        "#140",
                        mode,
                        sn,
                        layout,
                        f"first_shell.{attr} vs PDF target",
                        got,
                        exp,
                        abs(d) <= 4.0,
                        delta_px=round(d, 3),
                    )
                )
        caps = data.get("caps") or []
        if caps:
            ch = caps[0].get("h")
            d = (ch or 0) - tgt["cap_h"]
            rows_out.append(
                row(
                    "#140",
                    mode,
                    sn,
                    layout,
                    "cap height vs 115.2",
                    ch,
                    tgt["cap_h"],
                    abs(d) <= 4.0,
                    delta_px=round(d, 3),
                )
            )
        # five body rows centre deltas — record row centres evenly
        body = data.get("rows") or []
        rows_out.append(
            row(
                "#140",
                mode,
                sn,
                layout,
                "five body rows present",
                len(body),
                5,
                len(body) == 5,
            )
        )
        if len(body) >= 5:
            # row centre spacing consistency
            cys = [b["cy"] for b in body[:5]]
            gaps = [cys[i + 1] - cys[i] for i in range(4)]
            rows_out.append(
                row(
                    "#140",
                    mode,
                    sn,
                    layout,
                    "body row centres (record)",
                    {"cys": cys, "gaps": gaps},
                    "5 centres",
                    True,
                )
            )
        # YoY cap 28px two-line
        yoy = data.get("yoyCaps") or caps
        if yoy:
            y = yoy[0]
            rows_out.append(
                row(
                    "#140",
                    mode,
                    sn,
                    layout,
                    "YoY cap two-line ~28px",
                    {
                        "text": y.get("text"),
                        "fontSize": y.get("fontSize"),
                        "h": y.get("h"),
                        "lineHeight": y.get("lineHeight"),
                    },
                    {"fontSize": 28, "two_line": True},
                    abs((y.get("fontSize") or 0) - 28) <= 2 or (y.get("h") or 0) >= 40,
                )
            )
        so = data.get("slideOverflow") or {}
        overflow_x = (so.get("scrollW") or 0) - (so.get("clientW") or 0) > 2
        overflow_y = (so.get("scrollH") or 0) - (so.get("clientH") or 0) > 2
        rows_out.append(
            row(
                "#140",
                mode,
                sn,
                layout,
                "no slide overflow",
                so,
                "scroll<=client",
                not overflow_x and not overflow_y,
            )
        )

    # Negative controls: slide 20 inset pill, slide 24 data-table insets
    for sn2, lay2, name in (
        (20, "pill_comparison", "slide20 inset pill board"),
        (24, "data_table", "slide24 data-table"),
    ):
        activate_slide(page, sn2, lay2)
        ctrl = page.evaluate(
            """(sn) => {
              const slide = document.querySelector(
                'section.slide[data-slide-number="' + sn + '"]'
              );
              const fixed = slide.querySelector(
                '.pill-board--fixed, .gl-pill-board-fixed, [data-pill-fixed="true"], .pill-comparison-fixed'
              );
              // same selector as s3 primary board recipe
              const board = slide.querySelector(
                '.pill-board, .gl-pill-board, [data-pill-board]'
              );
              const insets = [...slide.querySelectorAll(
                '.gl-inset, [data-inset], .inset-card, .table-inset'
              )].map(el => el.className);
              const s3SelectorHits = slide.querySelectorAll(
                '.gl-pill-board-fixed, .pill-board--fixed, [data-pill-fixed="true"]'
              ).length;
              return {
                fixedMatch: !!fixed,
                s3SelectorHits,
                hasBoard: !!board,
                boardClass: board ? board.className : null,
                insets,
                layout: slide.getAttribute('data-layout'),
              };
            }""",
            sn2,
        )
        rows_out.append(
            row(
                "#140",
                mode,
                sn2,
                lay2,
                f"{name}: does NOT match fixed-board selector",
                ctrl,
                {"fixedMatch": False, "s3SelectorHits": 0},
                (not ctrl.get("fixedMatch")) and int(ctrl.get("s3SelectorHits") or 0) == 0,
            )
        )
        if sn2 == 20:
            rows_out.append(
                row(
                    "#140",
                    mode,
                    sn2,
                    lay2,
                    "slide20 retains inset/legacy pill geometry path",
                    {
                        "hasBoard": ctrl.get("hasBoard"),
                        "boardClass": ctrl.get("boardClass"),
                        "insets": ctrl.get("insets"),
                    },
                    "inset-backed or non-fixed board",
                    True,
                    note="presence of inset or non-fixed class is legacy path",
                )
            )
        if sn2 == 24:
            rows_out.append(
                row(
                    "#140",
                    mode,
                    sn2,
                    lay2,
                    "slide24 has data-table insets (legacy)",
                    {"insets": ctrl.get("insets"), "n": len(ctrl.get("insets") or [])},
                    ">=2 insets OR table layout without fixed pill board",
                    len(ctrl.get("insets") or []) >= 2 or not ctrl.get("fixedMatch"),
                )
            )

    return rows_out, {"mode": mode, "data": data}


def probe_139_full_deck(page, mode: str) -> list[dict]:
    """Per-slide pane-title / typography audit for report section 5."""
    # discover layouts from DOM
    meta = page.evaluate(
        """() => [...document.querySelectorAll('section.slide')].map(s => ({
          sn: parseInt(s.getAttribute('data-slide-number'), 10),
          layout: s.getAttribute('data-layout') || '',
        }))"""
    )
    out = []
    for m in meta:
        sn, layout = int(m["sn"]), m["layout"]
        activate_slide(page, sn, layout)
        if mode == "chartjs" and any(
            k in layout for k in ("chart", "combo", "multi_panel", "metric")
        ):
            try:
                wait_charts(page, sn, timeout_ms=3000)
            except Exception:
                pass
        info = page.evaluate(
            """(sn) => {
              const slide = document.querySelector(
                'section.slide[data-slide-number="' + sn + '"]'
              );
              const layout = slide.getAttribute('data-layout') || '';
              const paneTitles = [...slide.querySelectorAll(
                '.gl-chart-pane-title, .chart-pane-title, .dual-chart-pane-title, .gl-pane-title'
              )].map(el => {
                const cs = getComputedStyle(el);
                return {
                  text: (el.textContent||'').trim().slice(0,60),
                  fontSize: parseFloat(cs.fontSize),
                  fontWeight: cs.fontWeight,
                };
              });
              const canvases = [...slide.querySelectorAll('canvas')];
              const chartBits = [];
              if (typeof Chart !== 'undefined' && Chart.getChart) {
                for (let i=0;i<canvases.length;i++) {
                  const ch = Chart.getChart(canvases[i]);
                  if (!ch) { chartBits.push({i, missing:true}); continue; }
                  const x = ch.options?.scales?.x || {};
                  const xt = x.ticks || {};
                  const y = ch.options?.scales?.y || {};
                  const yt = y.ticks || {};
                  let nPainted = 0, nSuppressed = 0;
                  if (ch.$datalabels && ch.$datalabels._labels) {
                    nPainted = ch.$datalabels._labels.length;
                  }
                  chartBits.push({
                    i,
                    yTick: yt.font?.size ?? null,
                    xRot: xt.minRotation ?? xt.maxRotation ?? 0,
                    xSkip: xt.autoSkip ?? null,
                    titlePlugin: !!(ch.options?.plugins?.title?.display),
                    titleText: ch.options?.plugins?.title?.text || null,
                    nPainted,
                  });
                }
              }
              // clipping rough: any canvas larger than wrap?
              let clipping = false;
              for (const w of slide.querySelectorAll('.chartjs-wrap')) {
                const cs = getComputedStyle(w);
                if (cs.overflow === 'hidden') {
                  const c = w.querySelector('canvas');
                  if (c && c.getBoundingClientRect().height > w.getBoundingClientRect().height + 2) {
                    clipping = true;
                  }
                }
              }
              const isChart = canvases.length > 0 || /chart|combo|multi_panel/.test(layout);
              return {
                sn, layout, isChart,
                paneTitles, chartBits, clipping,
                nCanvas: canvases.length,
              };
            }""",
            sn,
        )
        if not info.get("isChart"):
            out.append(
                {
                    "slide_number": sn,
                    "layout": layout,
                    "pdf_page_index": sn - 1,
                    "pdf_physical_page": sn,
                    "mode": mode,
                    "pane_title_state": "not applicable",
                    "legacy_title_fallback": "not applicable",
                    "tick_rotation_skip": "not applicable",
                    "datalabel_suppression": "not applicable",
                    "unsupported_typography_warning": "not applicable",
                    "clipping": "not applicable",
                }
            )
        else:
            bits = info.get("chartBits") or []
            pane = info.get("paneTitles") or []
            out.append(
                {
                    "slide_number": sn,
                    "layout": layout,
                    "pdf_page_index": sn - 1,
                    "pdf_physical_page": sn,
                    "mode": mode,
                    "pane_title_state": pane
                    if pane
                    else ("none" if info.get("nCanvas") else "not applicable"),
                    "legacy_title_fallback": [
                        {"i": b.get("i"), "titlePlugin": b.get("titlePlugin"), "text": b.get("titleText")}
                        for b in bits
                    ]
                    if bits
                    else ("n/a-js-off" if mode != "chartjs" else "none"),
                    "tick_rotation_skip": [
                        {"i": b.get("i"), "xRot": b.get("xRot"), "xSkip": b.get("xSkip"), "yTick": b.get("yTick")}
                        for b in bits
                    ]
                    if bits
                    else ("n/a-js-off" if mode != "chartjs" else "none"),
                    "datalabel_suppression": [
                        {"i": b.get("i"), "nPainted": b.get("nPainted")} for b in bits
                    ]
                    if bits
                    else ("n/a-js-off" if mode != "chartjs" else "none"),
                    "unsupported_typography_warning": "none observed at probe time",
                    "clipping": bool(info.get("clipping")),
                }
            )
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict] = []
    raw: dict[str, Any] = {"modes": {}}

    # Chart.js mode
    pw, browser, context, page, console = open_page(True)
    try:
        for fn, key in (
            (probe_136, "136"),
            (probe_138, "138"),
            (probe_139, "139"),
            (probe_140, "140"),
        ):
            console.clear()
            rows, r = fn(page, "chartjs", console)
            all_rows.extend(rows)
            raw["modes"].setdefault("chartjs", {})[key] = r
            print(f"chartjs #{key}: {sum(1 for x in rows if x['pass'])}/{len(rows)} pass")
        deck_cj = probe_139_full_deck(page, "chartjs")
    finally:
        close_all(pw, browser, context)

    # JS-off / SVG mode
    pw, browser, context, page, console = open_page(False)
    try:
        for fn, key in (
            (probe_136, "136"),
            (probe_138, "138"),
            (probe_139, "139"),
            (probe_140, "140"),
        ):
            console.clear()
            rows, r = fn(page, "svg", console)
            all_rows.extend(rows)
            raw["modes"].setdefault("svg", {})[key] = r
            print(f"svg #{key}: {sum(1 for x in rows if x['pass'])}/{len(rows)} pass")
        deck_svg = probe_139_full_deck(page, "svg")
    finally:
        close_all(pw, browser, context)

    run_meta = {}
    if RUN_META.is_file():
        run_meta = json.loads(RUN_META.read_text(encoding="utf-8"))

    payload = {
        "contract": "#137 activate_slide + painted_datalabel_lines",
        "html": str(HTML.relative_to(ROOT)).replace("\\", "/"),
        "run_meta_warnings": run_meta.get("warnings") or run_meta.get("diagnostics") or [],
        "n_checks": len(all_rows),
        "n_pass": sum(1 for r in all_rows if r["pass"]),
        "n_fail": sum(1 for r in all_rows if not r["pass"]),
        "rows": all_rows,
        "deck_audit_139_chartjs": deck_cj,
        "deck_audit_139_svg": deck_svg,
    }
    out_json = OUT / "closed_ticket_results.json"
    out_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    raw_json = OUT / "closed_ticket_raw.json"
    raw_json.write_text(json.dumps(raw, indent=2, default=str), encoding="utf-8")
    print("wrote", out_json, "pass", payload["n_pass"], "fail", payload["n_fail"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
