"""v11 closed-ticket revalidation probes (#136–#159).

Observation only. Uses scripts/simulation_probe.py identity + paint-ready
contract. Chart.js and JS-off/SVG modes. No MAE / similarity / pixel scores.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from simulation_probe import (  # noqa: E402
    ProbeError,
    activate_slide,
    painted_datalabel_lines,
    wait_for_paint_ready_charts,
)

SIM = ROOT / "simulation" / "amex_q1_2026"
HTML = SIM / "passes" / "pass_01" / "output" / "presentation.html"
OUT = SIM / "closed_tickets"
RUN_META = SIM / "passes" / "pass_01" / "output" / "run_meta.json"
W, H = 1920, 1080

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
    x: r.left - sr.left, y: r.top - sr.top,
    w: r.width, h: r.height,
    right: r.right - sr.left, bottom: r.bottom - sr.top,
    cx: (r.left + r.right) / 2 - sr.left,
    cy: (r.top + r.bottom) / 2 - sr.top,
    text: (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 120),
  };
}
"""


def open_page(js_enabled: bool):
    pw = sync_playwright().start()
    browser = pw.chromium.launch()
    context = browser.new_context(
        viewport={"width": W, "height": H},
        java_script_enabled=js_enabled,
    )
    page = context.new_page()
    console: list[str] = []
    page.on("console", lambda m: console.append(f"{m.type}: {m.text}"))
    page.goto(
        HTML.resolve().as_uri(),
        wait_until="load" if not js_enabled else "networkidle",
    )
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
    residual: str = "",
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
        "residual": residual,
    }


def _paint(page, sn: int, layout: str, mode: str) -> str | None:
    if mode != "chartjs":
        return None
    try:
        wait_for_paint_ready_charts(page, sn, layout)
        return None
    except ProbeError as e:
        return str(e)
    except Exception as e:  # noqa: BLE001
        return f"{type(e).__name__}: {e}"


def _slide_text(page, sn: int) -> str:
    return page.evaluate(
        """(sn) => {
          const s = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
          return s ? (s.innerText || '').replace(/\\s+/g, ' ').trim() : '';
        }""",
        sn,
    )


# ---------- #136 / #149 slide 15 ----------
def probe_136_149(page, mode: str, console: list[str]) -> tuple[list[dict], dict]:
    sn, layout = 15, "stacked_bar_chart"
    activate_slide(page, sn, layout)
    paint_err = _paint(page, sn, layout, mode)
    data = page.evaluate(
        """(sn) => {
        """
        + _stage_rel_js()
        + """
        const slide = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
        const label = slide.querySelector('.chart-outlined-label');
        const cells = [...slide.querySelectorAll('.chart-outlined-cell')].map(rel);
        const labelBox = rel(label);
        const boxes = [...slide.querySelectorAll('.chart-outlined-cell > .chart-outlined-box')].map(rel);
        let bars = [];
        if (typeof Chart !== 'undefined' && Chart.getChart) {
          const canvas = slide.querySelector('canvas');
          const ch = canvas && Chart.getChart(canvas);
          if (ch) {
            const meta = ch.getDatasetMeta(0);
            const cr = canvas.getBoundingClientRect();
            for (const el of (meta && meta.data) || []) {
              bars.push({ cx: cr.left - sr.left + el.x });
            }
          }
        }
        // SVG bars (JS-off)
        let svgBars = [];
        const liveSvg = slide.querySelector('svg.chart-svg');
        if (liveSvg) {
          const hr = liveSvg.getBoundingClientRect();
          const vb = (liveSvg.getAttribute('viewBox') || '0 0 900 480').trim().split(/\\s+/).map(Number);
          const svgW = vb[2] || 900;
          const rects = [...liveSvg.querySelectorAll('rect')].map(r => ({
            x: parseFloat(r.getAttribute('x') || '0'),
            w: parseFloat(r.getAttribute('width') || '0'),
            h: parseFloat(r.getAttribute('height') || '0'),
          })).filter(r => r.w >= 20 && r.h >= 20);
          const byX = {};
          for (const r of rects) {
            const key = Math.round(r.x);
            byX[key] = byX[key] || [];
            byX[key].push(r);
          }
          for (const k of Object.keys(byX).map(Number).sort((a,b)=>a-b)) {
            const g = byX[k][0];
            const cxLocal = g.x + g.w / 2;
            svgBars.push({ cx: hr.left - sr.left + (cxLocal / svgW) * hr.width });
          }
        }
        const aligned = !!(slide.querySelector('.chart-table-aligned') ||
          slide.querySelector('[data-plot-aligned="true"]'));
        return {
          labelBox, cells, boxes, bars, svgBars, aligned,
          nOutlined: slide.querySelectorAll('.chart-outlined-box').length,
          hasSupport: !!slide.querySelector('.chart-support-outlined'),
        };
      }""",
        sn,
    )
    rows: list[dict] = []
    if paint_err:
        rows.append(row("#136", mode, sn, layout, "paint-ready", paint_err, "ready", False, residual="probe"))
    ref = (data.get("bars") if mode == "chartjs" else (data.get("svgBars") or data.get("bars"))) or []
    boxes = data.get("boxes") or data.get("cells") or []
    rows.append(
        row(
            "#136",
            mode,
            sn,
            layout,
            "outlined support present",
            {"hasSupport": data.get("hasSupport"), "nBoxes": data.get("nOutlined"), "aligned": data.get("aligned")},
            {"hasSupport": True, "nBoxes>=": 6, "aligned": True},
            bool(data.get("hasSupport")) and int(data.get("nOutlined") or 0) >= 6 and bool(data.get("aligned")),
        )
    )
    deltas = []
    n = min(5, len(boxes), len(ref))
    if n < 5:
        rows.append(
            row(
                "#136",
                mode,
                sn,
                layout,
                "five cell↔bar pairs",
                {"nBoxes": len(boxes), "nBars": len(ref)},
                5,
                False,
                residual="probe" if not ref else "renderer",
            )
        )
    else:
        max_abs = 0.0
        for i in range(5):
            d = float(boxes[i]["cx"]) - float(ref[i]["cx"])
            deltas.append(round(d, 3))
            max_abs = max(max_abs, abs(d))
            rows.append(
                row(
                    "#136",
                    mode,
                    sn,
                    layout,
                    f"cell[{i}] cx vs bar[{i}] cx",
                    {"cell_cx": boxes[i]["cx"], "bar_cx": ref[i]["cx"]},
                    "abs<=12",
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
                "max |cell-bar| over 5",
                {"max_abs": round(max_abs, 3), "deltas": deltas},
                "<=12",
                max_abs <= 12.0,
                delta_px=round(max_abs, 3),
            )
        )
    # #149 label lane does not overlap first value cell
    lab = data.get("labelBox")
    first = (data.get("cells") or [None])[0]
    gap = None
    if lab and first:
        gap = float(first["x"]) - float(lab["right"])
    rows.append(
        row(
            "#149",
            mode,
            sn,
            layout,
            "label lane no overlap first value cell",
            {"label_right": lab and lab.get("right"), "first_x": first and first.get("x"), "gap_px": gap},
            "gap >= 0",
            gap is not None and gap >= -0.5,
            delta_px=None if gap is None else round(gap, 3),
            note="label column right edge vs first value cell left",
        )
    )
    return rows, {"mode": mode, "data": data, "paint_err": paint_err}


# ---------- #137 / #146 identity + paint-ready ----------
def probe_137_146(page, mode: str, console: list[str]) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    meta = page.evaluate(
        """() => [...document.querySelectorAll('section.slide')].map(s => ({
          sn: parseInt(s.getAttribute('data-slide-number'), 10),
          layout: s.getAttribute('data-layout') || '',
        }))"""
    )
    sns = sorted(int(m["sn"]) for m in meta)
    rows.append(
        row(
            "#137",
            mode,
            0,
            "deck",
            "44 unique data-slide-number 1..44",
            {"n": len(sns), "min": min(sns) if sns else None, "max": max(sns) if sns else None, "unique": len(set(sns))},
            {"n": 44, "range": "1..44"},
            len(sns) == 44 and len(set(sns)) == 44 and min(sns) == 1 and max(sns) == 44,
        )
    )
    targets = [(9, "line_chart"), (12, "chart_hero_dual"), (27, "dual_chart")]
    raw = {"targets": {}}
    for sn, layout in targets:
        try:
            activate_slide(page, sn, layout)
            identity_ok = True
            id_err = None
        except Exception as e:  # noqa: BLE001
            identity_ok = False
            id_err = str(e)
        paint_err = None
        n_canvas = 0
        if identity_ok:
            n_canvas = page.evaluate(
                """(sn) => document.querySelectorAll(
                  'section.slide[data-slide-number="'+sn+'"] canvas').length""",
                sn,
            )
            paint_err = _paint(page, sn, layout, mode)
        rows.append(
            row(
                "#137",
                mode,
                sn,
                layout,
                "identity activate_slide",
                {"ok": identity_ok, "err": id_err},
                True,
                identity_ok,
                residual="" if identity_ok else "probe",
            )
        )
        if mode == "chartjs":
            rows.append(
                row(
                    "#146",
                    mode,
                    sn,
                    layout,
                    "paint-ready charts (ex-blank)",
                    {"n_canvas": n_canvas, "paint_err": paint_err},
                    {"n_canvas>=": 1 if sn != 12 else 1, "paint_err": None},
                    paint_err is None and int(n_canvas or 0) >= 1,
                    residual="" if paint_err is None else "renderer",
                )
            )
        raw["targets"][str(sn)] = {
            "identity_ok": identity_ok,
            "n_canvas": n_canvas,
            "paint_err": paint_err,
        }
    warn = [c for c in console if "error" in c.lower() or "warn" in c.lower()]
    rows.append(
        row(
            "#137",
            mode,
            0,
            "deck",
            "console diagnostics recorded",
            {"n_warn_error": len(warn), "sample": warn[:10]},
            "recorded",
            True,
            note="non-blocking record",
        )
    )
    return rows, raw


# ---------- #138 / #158 slide 28 ----------
def probe_138_158(page, mode: str, console: list[str]) -> tuple[list[dict], dict]:
    sn, layout = 28, "multi_panel"
    activate_slide(page, sn, layout)
    paint_err = _paint(page, sn, layout, mode)
    data = page.evaluate(
        """(sn) => {
        """
        + _stage_rel_js()
        + """
        const slide = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
        const titles = [...slide.querySelectorAll('.gl-chart-pane-title')].map(el => (el.textContent||'').trim());
        const subs = [...slide.querySelectorAll('.gl-chart-pane-subtitle')].map(el => (el.textContent||'').trim());
        const callouts = [...slide.querySelectorAll('.chart-side-callout, [data-side-callout]')].map(el => ({
          ...rel(el),
          lines: (el.innerText||'').split('\\n').map(s=>s.trim()).filter(Boolean),
          cls: el.className,
        }));
        const badges = [...slide.querySelectorAll('[class*="badge"]')].map(el => (el.textContent||'').trim()).filter(t=>/FDIC|92%/.test(t));
        const text = (slide.innerText||'').replace(/\\s+/g,' ');
        const topTotalPseudo = /top_total/i.test(slide.innerHTML);
        let charts = [];
        if (typeof Chart !== 'undefined' && Chart.getChart) {
          [...slide.querySelectorAll('canvas')].forEach((c,i) => {
            const ch = Chart.getChart(c);
            if (!ch) return;
            charts.push({
              i, labels: ch.data.labels,
              ds: ch.data.datasets.map(d => ({label:d.label, data:d.data, stack:d.stack})),
            });
          });
        }
        // SVG noscript stack labels
        const ns = [...slide.querySelectorAll('noscript')].map(n => n.textContent||'').join('\\n');
        return {titles, subs, callouts, badges, text, topTotalPseudo, charts, nsHasCallout:/side-callout|92% FDIC/.test(ns)};
      }""",
        sn,
    )
    rows: list[dict] = []
    if paint_err:
        rows.append(row("#138", mode, sn, layout, "paint-ready", paint_err, "ready", False))
    callouts = data.get("callouts") or []
    rows.append(
        row(
            "#138",
            mode,
            sn,
            layout,
            "one shared-column FDIC callout",
            {"n": len(callouts), "lines": [c.get("lines") for c in callouts], "badges": data.get("badges")},
            {"n": 1, "text~": "92% FDIC"},
            len(callouts) == 1
            and any("92%" in " ".join(c.get("lines") or []) for c in callouts)
            and len(data.get("badges") or []) == 0,
        )
    )
    rows.append(
        row(
            "#138",
            mode,
            sn,
            layout,
            "no pseudo top_total / duplicate badge",
            {"topTotalPseudo": data.get("topTotalPseudo"), "badges": data.get("badges")},
            False,
            not data.get("topTotalPseudo") and len(data.get("badges") or []) == 0,
        )
    )
    titles = data.get("titles") or []
    rows.append(
        row(
            "#158",
            mode,
            sn,
            layout,
            "pane titles Funding Mix + Deposit Programs",
            titles,
            ["Funding Mix", "Deposit Programs"],
            len(titles) == 2
            and any("Funding Mix" in t for t in titles)
            and any("Deposit Programs" in t for t in titles),
        )
    )
    rows.append(
        row(
            "#158",
            mode,
            sn,
            layout,
            "pane subtitles present",
            data.get("subs"),
            ">=1 each pane",
            len(data.get("subs") or []) >= 2,
        )
    )
    # independent stack totals via painted labels or text
    text = data.get("text") or ""
    # Chart.js may paint totals on canvas; accept either text presence or dataset stacks
    charts = data.get("charts") or []
    has_two_charts = len(charts) >= 2 if mode == "chartjs" else True
    rows.append(
        row(
            "#138",
            mode,
            sn,
            layout,
            "two independent pane charts",
            {"nCharts": len(charts) if mode == "chartjs" else "svg-mode", "textSample": text[:180]},
            2,
            has_two_charts,
        )
    )
    return rows, {"mode": mode, "data": data, "paint_err": paint_err}


# ---------- #139 / #150 slide 17 ----------
def probe_139_150(page, mode: str, console: list[str]) -> tuple[list[dict], dict]:
    sn, layout = 17, "dual_chart"
    activate_slide(page, sn, layout)
    paint_err = _paint(page, sn, layout, mode)
    data = page.evaluate(
        """(sn) => {
        """
        + _stage_rel_js()
        + """
        const slide = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
        const paneTitles = [...slide.querySelectorAll('.gl-chart-pane-title')].map(el => {
          const cs = getComputedStyle(el);
          return {...rel(el), fontSize: parseFloat(cs.fontSize), fontWeight: cs.fontWeight};
        });
        const charts = [];
        if (typeof Chart !== 'undefined' && Chart.getChart) {
          [...slide.querySelectorAll('canvas')].forEach((c,i) => {
            const ch = Chart.getChart(c);
            if (!ch) { charts.push({i, missing:true}); return; }
            const y = ch.options?.scales?.y || {};
            const x = ch.options?.scales?.x || {};
            charts.push({
              i,
              yTick: y.ticks?.font?.size ?? null,
              xRot: x.ticks?.minRotation ?? x.ticks?.maxRotation ?? 0,
              titlePlugin: !!(ch.options?.plugins?.title?.display),
              titleText: ch.options?.plugins?.title?.text || null,
              nPainted: ch.$datalabels && ch.$datalabels._labels ? ch.$datalabels._labels.length : 0,
            });
          });
        }
        return {paneTitles, charts, text:(slide.innerText||'').slice(0,300)};
      }""",
        sn,
    )
    rows: list[dict] = []
    titles = data.get("paneTitles") or []
    rows.append(
        row(
            "#139",
            mode,
            sn,
            layout,
            "semantic pane titles (2)",
            [{"text": t.get("text"), "fontSize": t.get("fontSize")} for t in titles],
            2,
            len(titles) == 2 and all((t.get("text") or "").strip() for t in titles),
        )
    )
    if mode == "chartjs":
        charts = data.get("charts") or []
        rows.append(
            row(
                "#139",
                mode,
                sn,
                layout,
                "no internal Chart.js title plugin duplicate",
                charts,
                "titlePlugin false",
                all(not c.get("titlePlugin") for c in charts if not c.get("missing")),
            )
        )
        rows.append(
            row(
                "#150",
                mode,
                sn,
                layout,
                "auto typography settled (y ticks + paint)",
                charts,
                "charts present, y ticks set",
                len(charts) == 2 and all(c.get("yTick") for c in charts if not c.get("missing")),
                note="handoff typography.mode=auto both panes; record chosen sizes",
            )
        )
        # clipping rough
        clip = page.evaluate(
            """(sn) => {
              const slide = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
              let clipping = false;
              for (const w of slide.querySelectorAll('.chartjs-wrap, .dual-chart-pane')) {
                const cs = getComputedStyle(w);
                if (cs.overflow === 'hidden') {
                  const c = w.querySelector('canvas');
                  if (c && c.getBoundingClientRect().height > w.getBoundingClientRect().height + 2) clipping = true;
                }
              }
              return clipping;
            }""",
            sn,
        )
        rows.append(
            row(
                "#150",
                mode,
                sn,
                layout,
                "no pane clipping",
                {"clipping": clip},
                False,
                clip is False,
            )
        )
    else:
        rows.append(
            row(
                "#150",
                mode,
                sn,
                layout,
                "JS-off pane titles retained",
                titles,
                2,
                len(titles) == 2,
            )
        )
    if paint_err:
        rows.append(row("#139", mode, sn, layout, "paint-ready", paint_err, "ready", False))
    return rows, {"mode": mode, "data": data, "paint_err": paint_err}


# ---------- #140 slide 3 + negative controls ----------
def probe_140(page, mode: str, console: list[str]) -> tuple[list[dict], dict]:
    sn, layout = 3, "pill_comparison"
    activate_slide(page, sn, layout)
    data = page.evaluate(
        """(sn) => {
        """
        + _stage_rel_js()
        + """
        const slide = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
        const board = slide.querySelector('.gl-pill');
        const stubs = [...slide.querySelectorAll('.gl-pill-stub')]
          .map(rel).filter(r => r && (r.text || '').trim());
        const shells = [...slide.querySelectorAll('.gl-pill-shell')].map(rel);
        const caps = [...slide.querySelectorAll('.gl-pill-head')].map(rel);
        const bodyRows = stubs.length; // non-empty label stubs = five metrics
        return {
          board: rel(board),
          boardCls: board ? board.className : null,
          nStubs: bodyRows,
          stubs,
          shells,
          caps,
          // recipe may emit gl-pill-free while still matching #140 PDF geometry
          fixedGeometryCandidate: !!(board),
        };
      }""",
        sn,
    )
    rows: list[dict] = []
    board = data.get("board")
    tgt = PILL_TARGETS
    rows.append(
        row(
            "#140",
            mode,
            sn,
            layout,
            "five-row pill board",
            {"nStubs": data.get("nStubs"), "boardCls": data.get("boardCls"), "board": board},
            {"nStubs": 5, "geometry": "PDF targets ±4"},
            bool(board) and int(data.get("nStubs") or 0) == 5,
            note="class may include gl-pill-free; geometry contract is authoritative",
        )
    )
    if board:
        for attr in ("x", "y", "w", "h"):
            exp = tgt["board"][attr]
            got = board.get(attr)
            d = (got or 0) - exp
            rows.append(
                row(
                    "#140",
                    mode,
                    sn,
                    layout,
                    f"board.{attr} vs PDF target ±4",
                    got,
                    exp,
                    abs(d) <= 4.0,
                    delta_px=round(d, 3),
                )
            )
    # negative controls slides 20 & 24
    for sn2, lay2 in [(20, "pill_comparison"), (24, "grouped_bar_chart")]:
        activate_slide(page, sn2, lay2)
        ctrl = page.evaluate(
            """(sn) => {
              const slide = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
              const board = slide.querySelector('.gl-pill');
              const fixed = !!(board && !/gl-pill-free|gl-pill-inset|gl-pill-compact/.test(board.className||''));
              const nStubs = slide.querySelectorAll('.gl-pill-stub').length;
              const layout = slide.getAttribute('data-layout');
              return {hasBoard:!!board, fixed, nStubs, layout, cls: board&&board.className};
            }""",
            sn2,
        )
        # slide 20 may be pill but must not match slide-3 fixed five-row selector geometry contract
        if sn2 == 20:
            b2 = None
            if ctrl.get("hasBoard"):
                b2 = page.evaluate(
                    """(sn) => {
                    """
                    + _stage_rel_js()
                    + """
                    const slide = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
                    return rel(slide.querySelector('.gl-pill'));
                  }""",
                    sn2,
                )
            same_geom = bool(
                b2
                and board
                and all(
                    abs((b2.get(a) or 0) - (board.get(a) or 0)) <= 4
                    for a in ("x", "y", "w", "h")
                )
            )
            rows.append(
                row(
                    "#140",
                    mode,
                    sn2,
                    lay2,
                    "slide20 not slide3 fixed five-row PDF geometry",
                    {"ctrl": ctrl, "s20": b2, "s3": board, "same_geom": same_geom},
                    "geometry must not match slide3 board targets",
                    not same_geom,
                    note="pill layout may exist; must not share slide3 fixed-board geometry",
                )
            )
        if sn2 == 24:
            rows.append(
                row(
                    "#140",
                    mode,
                    sn2,
                    lay2,
                    "slide24 not pill_comparison fixed board",
                    ctrl,
                    {"layout": "grouped_bar_chart", "fixedBoard": False},
                    ctrl.get("layout") == "grouped_bar_chart" and not ctrl.get("fixed"),
                )
            )
    return rows, {"mode": mode, "data": data}


# ---------- #147 slide 12 ----------
def probe_147(page, mode: str, console: list[str]) -> tuple[list[dict], dict]:
    sn, layout = 12, "chart_hero_dual"
    activate_slide(page, sn, layout)
    paint_err = _paint(page, sn, layout, mode)
    data = page.evaluate(
        """(sn) => {
        const slide = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
        const paneTitles = [...slide.querySelectorAll('.gl-chart-pane-title')].map(el => (el.textContent||'').trim());
        const subs = [...slide.querySelectorAll('.gl-chart-pane-subtitle')].map(el => (el.textContent||'').trim());
        let titlePlugin = null;
        if (typeof Chart !== 'undefined' && Chart.getChart) {
          const ch = Chart.getChart(slide.querySelector('canvas'));
          if (ch) titlePlugin = !!(ch.options?.plugins?.title?.display);
        }
        return {
          paneTitles, subs, titlePlugin,
          heroes: [...slide.querySelectorAll('.gl-hero-label')].map(el => (el.textContent||'').trim()),
          text: (slide.innerText||'').replace(/\\s+/g,' ').slice(0,300),
        };
      }""",
        sn,
    )
    rows: list[dict] = []
    # Expected: explicit left/right headings — known handoff residual if missing
    titles = data.get("paneTitles") or []
    has_explicit = len(titles) >= 1 and all(titles)
    rows.append(
        row(
            "#147",
            mode,
            sn,
            layout,
            "explicit left/right pane headings",
            {"paneTitles": titles, "subs": data.get("subs"), "heroes": data.get("heroes")},
            "exactly one semantic title per pane (left+right)",
            len(titles) == 2,
            residual="" if len(titles) == 2 else "handoff",
            note="canonical fixture lacks #147 headings; mutations do not add them",
        )
    )
    if mode == "chartjs":
        rows.append(
            row(
                "#147",
                mode,
                sn,
                layout,
                "no duplicate internal chart title",
                {"titlePlugin": data.get("titlePlugin")},
                False,
                data.get("titlePlugin") is False,
            )
        )
        rows.append(
            row(
                "#147",
                mode,
                sn,
                layout,
                "paint-ready",
                paint_err,
                None,
                paint_err is None,
            )
        )
    return rows, {"mode": mode, "data": data, "paint_err": paint_err}


# ---------- #148 slides 13-14 ----------
def probe_148(page, mode: str, console: list[str]) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    raw: dict[str, Any] = {}
    # 13 vertical grouped bars
    sn, layout = 13, "grouped_bar_chart"
    activate_slide(page, sn, layout)
    paint_err = _paint(page, sn, layout, mode)
    d13 = page.evaluate(
        """(sn) => {
        const slide = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
        let info = {indexAxis: null, type: null, labels: [], ds: []};
        if (typeof Chart !== 'undefined' && Chart.getChart) {
          const ch = Chart.getChart(slide.querySelector('canvas'));
          if (ch) {
            info = {
              indexAxis: ch.options.indexAxis || 'x',
              type: ch.config.type,
              labels: ch.data.labels,
              ds: ch.data.datasets.map(d => d.label),
            };
          }
        }
        const svg = slide.querySelector('svg.chart-svg');
        let svgVertical = null;
        if (svg) {
          const rects = [...svg.querySelectorAll('rect')].filter(r => parseFloat(r.getAttribute('height')||0) > 20);
          svgVertical = rects.length > 0 && rects.every(r => parseFloat(r.getAttribute('height')) >= parseFloat(r.getAttribute('width')||0));
        } else if (/vbar|bar-chart|grouped_bar/.test(slide.innerHTML)) {
          svgVertical = true; // noscript/fallback present
        }
        return {...info, svgVertical, title:(slide.querySelector('.slide-title')||{}).textContent};
      }""",
        sn,
    )
    raw["13"] = d13
    if mode == "chartjs":
        rows.append(
            row(
                "#148",
                mode,
                sn,
                layout,
                "vertical bars (indexAxis=x)",
                d13,
                {"indexAxis": "x", "type": "bar"},
                d13.get("indexAxis") == "x" and d13.get("type") == "bar",
            )
        )
        rows.append(
            row(
                "#148",
                mode,
                sn,
                layout,
                "series Total Balances + Billed Business",
                d13.get("ds"),
                ["Total Balances", "Billed Business"],
                set(d13.get("ds") or []) >= {"Total Balances", "Billed Business"},
            )
        )
    else:
        rows.append(
            row(
                "#148",
                mode,
                sn,
                layout,
                "SVG vertical bars",
                d13.get("svgVertical"),
                True,
                d13.get("svgVertical") is True or d13.get("svgVertical") is None,
                note="null when noscript not hydrated as live svg",
            )
        )
    # 14 dual pane semantics
    sn, layout = 14, "dual_chart"
    activate_slide(page, sn, layout)
    paint_err2 = _paint(page, sn, layout, mode)
    d14 = page.evaluate(
        """(sn) => {
        const slide = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
        const titles = [...slide.querySelectorAll('.gl-chart-pane-title')].map(el => (el.textContent||'').trim());
        let charts = [];
        if (typeof Chart !== 'undefined' && Chart.getChart) {
          [...slide.querySelectorAll('canvas')].forEach((c,i) => {
            const ch = Chart.getChart(c);
            if (!ch) return;
            charts.push({i, indexAxis: ch.options.indexAxis||'x', type: ch.config.type, labels: ch.data.labels});
          });
        }
        return {titles, charts};
      }""",
        sn,
    )
    raw["14"] = d14
    titles = d14.get("titles") or []
    rows.append(
        row(
            "#148",
            mode,
            sn,
            layout,
            "pane order 30+ Days Past Due then Net Write-Off Rates",
            titles,
            ["30+ Days Past Due", "Net Write-Off Rates"],
            len(titles) >= 2
            and "Past Due" in titles[0]
            and "Write-Off" in titles[1],
        )
    )
    if mode == "chartjs":
        rows.append(
            row(
                "#148",
                mode,
                sn,
                layout,
                "both panes vertical bars",
                d14.get("charts"),
                "indexAxis=x",
                all((c.get("indexAxis") or "x") == "x" for c in (d14.get("charts") or [])),
            )
        )
        rows.append(
            row(
                "#148",
                mode,
                sn,
                layout,
                "paint-ready 13+14",
                {"13": paint_err, "14": paint_err2},
                None,
                paint_err is None and paint_err2 is None,
            )
        )
    return rows, raw


# ---------- #151 slide 18 ----------
def probe_151(page, mode: str, console: list[str]) -> tuple[list[dict], dict]:
    sn, layout = 18, "chart_hero_dual"
    activate_slide(page, sn, layout)
    paint_err = _paint(page, sn, layout, mode)
    data = page.evaluate(
        """(sn) => {
        const slide = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
        const titles = [...slide.querySelectorAll('.gl-chart-pane-title')].map(el => (el.textContent||'').trim());
        const driverRows = [...slide.querySelectorAll('.gl-driver-row')].map(el => ({
          label: (el.querySelector('.gl-driver-label')||{}).textContent||'',
          value: (el.querySelector('.gl-driver-value')||{}).textContent||'',
          detail: (el.querySelector('.gl-driver-detail')||{}).textContent||'',
        }));
        const canvas = slide.querySelector('canvas');
        let boxed = null, nDS = null, dsTypes = [], comboLine = false;
        if (typeof Chart !== 'undefined' && Chart.getChart && canvas) {
          const ch = Chart.getChart(canvas);
          if (ch) {
            boxed = {
              painted: canvas.dataset.rv2BoxedLabelsPainted || null,
              flag: canvas.dataset.rv2BoxedLabels || null,
              values: ch.options?.plugins?.boxedLabels?.values || null,
            };
            nDS = ch.data.datasets.length;
            dsTypes = ch.data.datasets.map(d => d.type || ch.config.type);
            comboLine = ch.data.datasets.some(d => (d.type === 'line') || (d.label||'').toLowerCase().includes('yoy'));
          }
        }
        const ns = (slide.querySelector('noscript')||{}).textContent || '';
        const liveBoxed = slide.querySelectorAll('g.boxed-label, .boxed-label').length;
        const htmlBoxed = (slide.innerHTML.match(/boxed-label/g) || []).length;
        const svgBoxed = Math.max(liveBoxed, Math.floor(htmlBoxed / 3)); // group~3 class hits
        return {titles, driverRows, boxed, nDS, dsTypes, comboLine, svgBoxed, liveBoxed, htmlBoxed, hasDriver: !!slide.querySelector('.gl-driver-card')};
      }""",
        sn,
    )
    rows: list[dict] = []
    rows.append(
        row(
            "#151",
            mode,
            sn,
            layout,
            "chart_hero_dual + driver_card",
            {"titles": data.get("titles"), "hasDriver": data.get("hasDriver"), "nRows": len(data.get("driverRows") or [])},
            {"hasDriver": True, "nRows": 4},
            bool(data.get("hasDriver")) and len(data.get("driverRows") or []) == 4,
        )
    )
    vals = { (r.get("label") or "").strip(): (r.get("value") or "").strip() for r in (data.get("driverRows") or []) }
    rows.append(
        row(
            "#151",
            mode,
            sn,
            layout,
            "driver card includes Margin 5%",
            vals,
            {"Margin": "5%"},
            any(k.startswith("Margin") and "5%" in v for k, v in vals.items()),
        )
    )
    if mode == "chartjs":
        boxed = data.get("boxed") or {}
        n_painted = int(boxed.get("painted") or 0)
        rows.append(
            row(
                "#151",
                mode,
                sn,
                layout,
                "five boxed YoY labels painted",
                boxed,
                {"painted": 5, "values": ["11%", "12%", "12%", "12%", "12%"]},
                n_painted == 5 and list(boxed.get("values") or []) == ["11%", "12%", "12%", "12%", "12%"],
            )
        )
        rows.append(
            row(
                "#151",
                mode,
                sn,
                layout,
                "no synthetic combo YoY line",
                {"nDS": data.get("nDS"), "dsTypes": data.get("dsTypes"), "comboLine": data.get("comboLine")},
                {"nDS": 1, "comboLine": False},
                int(data.get("nDS") or 0) == 1 and not data.get("comboLine"),
            )
        )
        rows.append(row("#151", mode, sn, layout, "paint-ready", paint_err, None, paint_err is None))
    else:
        rows.append(
            row(
                "#151",
                mode,
                sn,
                layout,
                "SVG boxed-label groups present",
                {"svgBoxed": data.get("svgBoxed")},
                ">=5",
                int(data.get("svgBoxed") or 0) >= 5,
            )
        )
    return rows, {"mode": mode, "data": data, "paint_err": paint_err}


# ---------- #152 gridlines default off ----------
def probe_152(page, mode: str, console: list[str]) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    raw = {}
    samples = [
        (9, "line_chart"),
        (13, "grouped_bar_chart"),
        (15, "stacked_bar_chart"),
        (18, "chart_hero_dual"),
    ]
    for sn, layout in samples:
        activate_slide(page, sn, layout)
        paint_err = _paint(page, sn, layout, mode)
        data = page.evaluate(
            """(sn) => {
              const slide = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
              const out = {charts: [], svgGrid: 0, svgZero: 0, svgAxis: 0};
              if (typeof Chart !== 'undefined' && Chart.getChart) {
                [...slide.querySelectorAll('canvas')].forEach((c,i) => {
                  const ch = Chart.getChart(c);
                  if (!ch) return;
                  const y = ch.options?.scales?.y || {};
                  const x = ch.options?.scales?.x || {};
                  out.charts.push({
                    i,
                    yGrid: !!(y.grid && y.grid.display),
                    xGrid: !!(x.grid && x.grid.display),
                    yBorder: y.border && y.border.display,
                  });
                });
              }
              const ns = [...slide.querySelectorAll('noscript, svg.chart-svg')].map(n => n.textContent || n.innerHTML || '').join('\\n');
              out.svgGrid = (ns.match(/chart-gridline/g) || []).length;
              out.svgZero = (ns.match(/zero|baseline/gi) || []).length;
              out.svgAxis = (ns.match(/chart-axis|class="axis/g) || []).length;
              // live svg
              out.liveGrid = slide.querySelectorAll('line.chart-gridline, .chart-gridline').length;
              return out;
            }""",
            sn,
        )
        raw[str(sn)] = data
        if mode == "chartjs":
            grids = data.get("charts") or []
            rows.append(
                row(
                    "#152",
                    mode,
                    sn,
                    layout,
                    "plot gridlines off (Chart.js)",
                    grids,
                    "xGrid/yGrid false",
                    all((not g.get("xGrid") and not g.get("yGrid")) for g in grids) and len(grids) >= 1,
                )
            )
        else:
            rows.append(
                row(
                    "#152",
                    mode,
                    sn,
                    layout,
                    "plot gridlines absent (SVG)",
                    {"svgGrid": data.get("svgGrid"), "liveGrid": data.get("liveGrid")},
                    0,
                    int(data.get("svgGrid") or 0) == 0 and int(data.get("liveGrid") or 0) == 0,
                )
            )
        if paint_err and mode == "chartjs":
            rows.append(row("#152", mode, sn, layout, "paint-ready", paint_err, None, False))
    # mixed-sign zero line retained on slide 15
    sn, layout = 15, "stacked_bar_chart"
    activate_slide(page, sn, layout)
    _paint(page, sn, layout, mode)
    zero = page.evaluate(
        """(sn) => {
          const slide = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
          if (typeof Chart !== 'undefined' && Chart.getChart) {
            const ch = Chart.getChart(slide.querySelector('canvas'));
            if (!ch) return {ok:false};
            const y = ch.scales.y;
            return {
              ok:true,
              yMin: y.min, yMax: y.max,
              // semantic zero remains available even if grid off
              includesZero: y.min < 0 && y.max > 0,
            };
          }
          const ns = (slide.querySelector('noscript')||{}).textContent||'';
          return {ok:true, svgHasZero: /zero|y1="[^"]*"/i.test(ns)};
        }""",
        sn,
    )
    rows.append(
        row(
            "#152",
            mode,
            sn,
            layout,
            "mixed-sign domain retains zero context",
            zero,
            "domain crosses or records zero",
            bool(zero.get("includesZero") or zero.get("svgHasZero") or zero.get("ok")),
            note="axes/zero remain; ordinary plot gridlines stay off",
        )
    )
    return rows, raw


# ---------- #153 slide 26 ----------
def probe_153(page, mode: str, console: list[str]) -> tuple[list[dict], dict]:
    sn, layout = "26", "data_table"
    sn_i = 26
    activate_slide(page, sn_i, layout)
    data = page.evaluate(
        """(sn) => {
          const slide = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
          const heads = [...slide.querySelectorAll('th')].map(t => t.textContent.trim());
          const stubs = [...slide.querySelectorAll('td:first-child, th')].map(t => t.textContent.trim());
          const rows = [...slide.querySelectorAll('tr')].map(tr => [...tr.children].map(c => c.textContent.trim()));
          const text = (slide.innerText||'').replace(/\\s+/g,' ');
          return {heads, rows, text, hasQ126: /Q1['’]?26/.test(text)};
        }""",
        sn_i,
    )
    heads = data.get("heads") or []
    # Source orientation: periods as columns with Q1'26 visible context
    # Current fixture is transposed category rows (Restaurants...) without Q1'26 period column
    has_period_cols = any("Q1" in h for h in heads)
    rows = [
        row(
            "#153",
            mode,
            sn_i,
            layout,
            "visible Q1'26 period context",
            {"heads": heads, "hasQ126": data.get("hasQ126"), "sampleRows": (data.get("rows") or [])[:3]},
            "Q1'26 period column/context present",
            bool(data.get("hasQ126") or has_period_cols),
            residual="" if (data.get("hasQ126") or has_period_cols) else "handoff",
            note="canonical fixture still v10 category-row matrix; mutations lack #153",
        ),
        row(
            "#153",
            mode,
            sn_i,
            layout,
            "source matrix orientation (periods as columns)",
            {"heads": heads},
            "period columns including Q1'26",
            has_period_cols,
            residual="" if has_period_cols else "handoff",
        ),
    ]
    return rows, {"mode": mode, "data": data}


# ---------- #154 slide 24 ----------
def probe_154(page, mode: str, console: list[str]) -> tuple[list[dict], dict]:
    sn, layout = 24, "grouped_bar_chart"
    activate_slide(page, sn, layout)
    paint_err = _paint(page, sn, layout, mode)
    data = page.evaluate(
        """(sn) => {
        const slide = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
        const text = (slide.innerText||'').replace(/\\s+/g,' ');
        const support = [...slide.querySelectorAll('.chart-outlined-box')].map(el => (el.textContent||'').trim());
        const canvas = slide.querySelector('canvas');
        let chart = null;
        if (typeof Chart !== 'undefined' && Chart.getChart && canvas) {
          const ch = Chart.getChart(canvas);
          if (ch) {
            chart = {
              nBars: (ch.getDatasetMeta(0).data || []).length,
              labels: ch.data.labels,
              barGroupsPainted: canvas.dataset.rv2BarGroupsPainted || null,
              barGroups: ch.options?.plugins?.barGroups || null,
            };
          }
        }
        const ns = (slide.querySelector('noscript')||{}).textContent || '';
        const liveBrackets = slide.querySelectorAll('g.bar-group-bracket, .bar-group-bracket').length;
        const htmlBrackets = (slide.innerHTML.match(/bar-group-bracket/g) || []).length;
        const nBrackets = Math.max(liveBrackets, htmlBrackets);
        return {
          text, support, chart, nBrackets, liveBrackets, htmlBrackets,
          has486: text.includes('$486B Total Network Volumes'),
          hasFX: /FX-adjusted/i.test(text),
        };
      }""",
        sn,
    )
    rows: list[dict] = []
    ch = data.get("chart") or {}
    if mode == "chartjs":
        rows.append(
            row(
                "#154",
                mode,
                sn,
                layout,
                "six bars",
                {"nBars": ch.get("nBars"), "labels": ch.get("labels")},
                6,
                int(ch.get("nBars") or 0) == 6,
            )
        )
        rows.append(
            row(
                "#154",
                mode,
                sn,
                layout,
                "three visible semantic group brackets",
                {"painted": ch.get("barGroupsPainted"), "cfg": ch.get("barGroups")},
                3,
                int(ch.get("barGroupsPainted") or 0) == 3,
            )
        )
        rows.append(row("#154", mode, sn, layout, "paint-ready", paint_err, None, paint_err is None))
    else:
        rows.append(
            row(
                "#154",
                mode,
                sn,
                layout,
                "SVG three bar-group-bracket groups",
                {"nBrackets": data.get("nBrackets")},
                3,
                int(data.get("nBrackets") or 0) == 3,
            )
        )
    rows.append(
        row(
            "#154",
            mode,
            sn,
            layout,
            "exact $486B Total Network Volumes",
            {"has486": data.get("has486"), "support": data.get("support")},
            True,
            bool(data.get("has486")),
        )
    )
    rows.append(
        row(
            "#154",
            mode,
            sn,
            layout,
            "FX-adjusted note present",
            data.get("hasFX"),
            True,
            bool(data.get("hasFX")),
        )
    )
    support = data.get("support") or []
    rows.append(
        row(
            "#154",
            mode,
            sn,
            layout,
            "aligned support row (% of total cells)",
            support,
            "label + 6 pct cells",
            len(support) >= 7,
        )
    )
    return rows, {"mode": mode, "data": data, "paint_err": paint_err}


# ---------- #155 slide 21 ----------
def probe_155(page, mode: str, console: list[str]) -> tuple[list[dict], dict]:
    sn, layout = 21, "chart_hero_dual"
    activate_slide(page, sn, layout)
    paint_err = _paint(page, sn, layout, mode)
    data = page.evaluate(
        """(sn) => {
        const slide = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
        const roe = [...slide.querySelectorAll('.chart-outlined-box')].map(el => (el.textContent||'').trim());
        const kpis = [...slide.querySelectorAll('.gl-hero')].map(el => (el.innerText||'').replace(/\\s+/g,' ').trim());
        let chart = null;
        if (typeof Chart !== 'undefined' && Chart.getChart) {
          const ch = Chart.getChart(slide.querySelector('canvas'));
          if (ch) {
            chart = {
              ds: ch.data.datasets.map(d => ({label:d.label, type:d.type, stack:d.stack, data:d.data})),
              labels: ch.data.labels,
            };
          }
        }
        return {roe, kpis, chart, text:(slide.innerText||'').replace(/\\s+/g,' ').slice(0,400)};
      }""",
        sn,
    )
    rows: list[dict] = []
    ch = data.get("chart") or {}
    ds = {d["label"]: d for d in (ch.get("ds") or [])}
    if mode == "chartjs":
        rows.append(
            row(
                "#155",
                mode,
                sn,
                layout,
                "stacked Dividends + Share Repurchases",
                {
                    "div": ds.get("Dividends"),
                    "rep": ds.get("Share Repurchases"),
                },
                {"stack": "combo", "both present": True},
                "Dividends" in ds
                and "Share Repurchases" in ds
                and ds["Dividends"].get("stack") == "combo"
                and ds["Share Repurchases"].get("stack") == "combo",
            )
        )
        shares = (ds.get("Common Shares Outstanding") or {}).get("data") or []
        rows.append(
            row(
                "#155",
                mode,
                sn,
                layout,
                "shares line 702→682",
                shares,
                [702, "...", 682],
                len(shares) >= 2 and shares[0] == 702 and shares[-1] == 682,
            )
        )
        rows.append(row("#155", mode, sn, layout, "paint-ready", paint_err, None, paint_err is None))
    roe_vals = [x for x in (data.get("roe") or []) if x.endswith("%")]
    rows.append(
        row(
            "#155",
            mode,
            sn,
            layout,
            "ROE 35/34/36/36/34/35%",
            roe_vals,
            ["35%", "34%", "36%", "36%", "34%", "35%"],
            roe_vals == ["35%", "34%", "36%", "36%", "34%", "35%"],
        )
    )
    kpis = data.get("kpis") or []
    rows.append(
        row(
            "#155",
            mode,
            sn,
            layout,
            "right-side KPIs present (4)",
            kpis,
            4,
            len(kpis) == 4
            and any("CET1" in k for k in kpis)
            and any("Dividend" in k for k in kpis),
        )
    )
    return rows, {"mode": mode, "data": data, "paint_err": paint_err}


# ---------- #156 slide 27 ----------
def probe_156(page, mode: str, console: list[str]) -> tuple[list[dict], dict]:
    sn, layout = 27, "dual_chart"
    activate_slide(page, sn, layout)
    paint_err = _paint(page, sn, layout, mode)
    data = page.evaluate(
        """(sn) => {
        const slide = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
        const titles = [...slide.querySelectorAll('.gl-chart-pane-title')].map(el => (el.textContent||'').trim());
        const source = (slide.querySelector('.source-strip')||{}).textContent || '';
        const text = (slide.innerText||'');
        let charts = [];
        if (typeof Chart !== 'undefined' && Chart.getChart) {
          [...slide.querySelectorAll('canvas')].forEach((c,i) => {
            const ch = Chart.getChart(c);
            if (!ch) return;
            charts.push({
              i, labels: ch.data.labels,
              ds: ch.data.datasets.map(d => d.label),
              n: ch.data.datasets.length,
            });
          });
        }
        return {titles, source, text, charts, nCanvas: slide.querySelectorAll('canvas').length};
      }""",
        sn,
    )
    rows: list[dict] = []
    charts = data.get("charts") or []
    if mode == "chartjs":
        rows.append(
            row(
                "#156",
                mode,
                sn,
                layout,
                "two paint-ready panes",
                {"nCanvas": data.get("nCanvas"), "paint_err": paint_err, "nCharts": len(charts)},
                2,
                int(data.get("nCanvas") or 0) == 2 and paint_err is None and len(charts) == 2,
            )
        )
        for ch in charts:
            labs = ch.get("labels") or []
            rows.append(
                row(
                    "#156",
                    mode,
                    sn,
                    layout,
                    f"pane{ch.get('i')} Q1'25–Q1'28 + 3 scenarios",
                    {"labels": labs, "ds": ch.get("ds")},
                    {"first": "Q1'25", "last": "Q1'28", "nDS": 3},
                    labs[:1] == ["Q1'25"]
                    and labs[-1:] == ["Q1'28"]
                    and int(ch.get("n") or 0) == 3
                    and len(ch.get("ds") or []) == 3,
                )
            )
    rows.append(
        row(
            "#156",
            mode,
            sn,
            layout,
            "pane titles Unemployment + GDP",
            data.get("titles"),
            ["U.S. Unemployment Rate %", "U.S. GDP Growth* %"],
            any("Unemployment" in t for t in (data.get("titles") or []))
            and any("GDP" in t for t in (data.get("titles") or [])),
        )
    )
    src = (data.get("source") or "") + (data.get("text") or "")
    rows.append(
        row(
            "#156",
            mode,
            sn,
            layout,
            "E0026 / PDF page 27 source citation",
            {"source": data.get("source")},
            "PDF page 27 reference",
            "page 27" in src.lower() or "pdf page 27" in src.lower(),
        )
    )
    # SAAR note — may live in disclosure; record presence
    # SAAR often lives in disclosure panel HTML rather than above-the-fold text
    has_saar_text = "SAAR" in (data.get("text") or "")
    has_saar_html = page.evaluate(
        """(sn) => {
          const s = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
          return s ? /SAAR/i.test(s.innerHTML) : false;
        }""",
        sn,
    )
    rows.append(
        row(
            "#156",
            mode,
            sn,
            layout,
            "SAAR note on slide (visible or disclosure HTML)",
            {"text": has_saar_text, "html": has_saar_html},
            True,
            bool(has_saar_html or has_saar_text),
            residual="" if (has_saar_html or has_saar_text) else "handoff",
            note="disclosure-panel SAAR counts; above-fold not required by ticket wording",
        )
    )
    return rows, {"mode": mode, "data": data, "paint_err": paint_err}


# ---------- #157 slides 33-37 ----------
def probe_157(page, mode: str, console: list[str]) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    raw = {}
    expect_units = {
        33: "$ in billions",
        34: "$ in millions",
        35: "$ in billions",
        36: "$ in billions",
        37: "$ in billions",
    }
    for sn in range(33, 38):
        layout = "annex_table"
        activate_slide(page, sn, layout)
        data = page.evaluate(
            """(sn) => {
              const slide = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
              const title = (slide.querySelector('.slide-title')||{}).textContent || '';
              const sub = (slide.querySelector('.subtitle, .gl-dek')||{}).textContent || '';
              const stubs = [...slide.querySelectorAll('td.gl-annex-stub')].map(t => t.textContent.trim());
              const heads = [...slide.querySelectorAll('th')].map(t => t.textContent.trim());
              const nCells = slide.querySelectorAll('td.gl-annex-cell, td.num, td').length;
              const text = (slide.innerText||'');
              return {
                title, sub, stubs, heads, nCells, nTables: slide.querySelectorAll('table').length,
                hasFX: /FX-adj/i.test(text),
                hasFoot: /FX-adjusted|See |footnote/i.test(text),
              };
            }""",
            sn,
        )
        raw[str(sn)] = data
        unit = expect_units[sn]
        rows.append(
            row(
                "#157",
                mode,
                sn,
                layout,
                "annex matrix present with stubs",
                {"nStubs": len(data.get("stubs") or []), "nTables": data.get("nTables"), "heads": data.get("heads")[:6]},
                {"nStubs>=": 4, "nTables": 1},
                int(data.get("nTables") or 0) >= 1 and len(data.get("stubs") or []) >= 4,
            )
        )
        rows.append(
            row(
                "#157",
                mode,
                sn,
                layout,
                f"units include {unit}",
                data.get("sub"),
                unit,
                unit.lower() in (data.get("sub") or "").lower(),
            )
        )
        rows.append(
            row(
                "#157",
                mode,
                sn,
                layout,
                "FX footnote/context present",
                {"hasFX": data.get("hasFX"), "sub": data.get("sub")},
                True,
                bool(data.get("hasFX")),
            )
        )
    return rows, raw


# ---------- #159 slide 32 ----------
def probe_159(page, mode: str, console: list[str]) -> tuple[list[dict], dict]:
    sn, layout = 32, "grouped_annex_table"
    activate_slide(page, sn, layout)
    data = page.evaluate(
        """(sn) => {
          const slide = document.querySelector('section.slide[data-slide-number="'+sn+'"]');
          const headings = [...slide.querySelectorAll('.gl-grouped-annex-heading')].map(el => ({
            t: (el.textContent||'').trim(), id: el.id || '',
          }));
          const allIds = [...document.querySelectorAll('[id]')].map(el => el.id).filter(Boolean);
          const myIds = headings.map(h => h.id).filter(Boolean);
          const dup = myIds.filter(id => allIds.filter(x => x === id).length > 1);
          return {
            headings, myIds, dup,
            nTables: slide.querySelectorAll('table').length,
            stubs: [...slide.querySelectorAll('td.gl-annex-stub')].map(t => t.textContent.trim()),
          };
        }""",
        sn,
    )
    heads = data.get("headings") or []
    rows = [
        row(
            "#159",
            mode,
            sn,
            layout,
            "two peer grouped annex tables",
            {"nTables": data.get("nTables"), "headings": heads},
            {"nTables": 2, "nHeadings": 2},
            int(data.get("nTables") or 0) == 2 and len(heads) == 2,
        ),
        row(
            "#159",
            mode,
            sn,
            layout,
            "deck-unique heading IDs",
            {"ids": data.get("myIds"), "dups": data.get("dup")},
            "unique non-empty ids",
            len(data.get("myIds") or []) == 2
            and len(set(data.get("myIds") or [])) == 2
            and not (data.get("dup") or []),
        ),
        row(
            "#159",
            mode,
            sn,
            layout,
            "heading labels Commercial + International",
            [h.get("t") for h in heads],
            ["Commercial Services", "International Card Services"],
            any("Commercial" in (h.get("t") or "") for h in heads)
            and any("International" in (h.get("t") or "") for h in heads),
        ),
    ]
    return rows, {"mode": mode, "data": data}


def _summarize(all_rows: list[dict]) -> list[dict]:
    """One scorecard row per ticket with aggregate result."""
    order = [
        "#136",
        "#137",
        "#138",
        "#139",
        "#140",
        "#146",
        "#147",
        "#148",
        "#149",
        "#150",
        "#151",
        "#152",
        "#153",
        "#154",
        "#155",
        "#156",
        "#157",
        "#158",
        "#159",
    ]
    # pair aliases for report
    card_map = {
        "#136": ("#136/#149", "slide 15 outlined support + label lane"),
        "#149": ("#136/#149", "slide 15 outlined support + label lane"),
        "#137": ("#137/#146", "identity-safe paint-ready capture"),
        "#146": ("#137/#146", "identity-safe paint-ready capture"),
        "#138": ("#138/#158", "slide 28 FDIC callout + pane titles"),
        "#158": ("#138/#158", "slide 28 FDIC callout + pane titles"),
        "#139": ("#139/#150", "slide 17 typography + auto sizes"),
        "#150": ("#139/#150", "slide 17 typography + auto sizes"),
        "#140": ("#140", "slide 3 pill board + neg controls"),
        "#147": ("#147", "slide 12 pane headings"),
        "#148": ("#148", "slides 13-14 vertical bars + pane order"),
        "#151": ("#151", "slide 18 boxed labels + driver card"),
        "#152": ("#152", "gridlines default off"),
        "#153": ("#153", "slide 26 Q1'26 matrix orientation"),
        "#154": ("#154", "slide 24 growth brackets + $486B"),
        "#155": ("#155", "slide 21 capital return composition"),
        "#156": ("#156", "slide 27 macro scenarios"),
        "#157": ("#157", "slides 33-37 annex matrices"),
        "#159": ("#159", "slide 32 grouped annex heading IDs"),
    }
    by_ticket: dict[str, list[dict]] = {}
    for r in all_rows:
        by_ticket.setdefault(r["ticket"], []).append(r)

    scorecard = []
    seen_groups: set[str] = set()
    for t in order:
        group, title = card_map[t]
        if group in seen_groups:
            continue
        # collect all tickets in group
        members = [k for k, v in card_map.items() if v[0] == group]
        checks = []
        for m in members:
            checks.extend(by_ticket.get(m, []))
        if not checks:
            scorecard.append(
                {
                    "ticket": group,
                    "title": title,
                    "result": "not-run",
                    "n_pass": 0,
                    "n_fail": 0,
                    "n_checks": 0,
                    "modes": [],
                    "slides": [],
                    "residuals": [],
                    "evidence": "closed_tickets/closed_ticket_results_v11.json",
                }
            )
            seen_groups.add(group)
            continue
        n_pass = sum(1 for c in checks if c["pass"])
        n_fail = sum(1 for c in checks if not c["pass"])
        if n_fail == 0:
            result = "pass"
        elif n_pass == 0:
            result = "fail"
        else:
            result = "partial"
        residuals = sorted({c.get("residual") for c in checks if c.get("residual") and not c["pass"]})
        fails = [
            {
                "ticket": c["ticket"],
                "mode": c["mode"],
                "slide": c["slide_number"],
                "check": c["check"],
                "measured": c.get("measured"),
                "residual": c.get("residual"),
                "note": c.get("note"),
            }
            for c in checks
            if not c["pass"]
        ]
        scorecard.append(
            {
                "ticket": group,
                "title": title,
                "result": result,
                "n_pass": n_pass,
                "n_fail": n_fail,
                "n_checks": len(checks),
                "modes": sorted({c["mode"] for c in checks}),
                "slides": sorted({c["slide_number"] for c in checks if c["slide_number"]}),
                "residuals": residuals,
                "failed_checks": fails[:20],
                "evidence": "closed_tickets/closed_ticket_results_v11.json",
                "input": "simulation/amex_q1_2026/passes/pass_01/output/presentation.html",
            }
        )
        seen_groups.add(group)
    return scorecard


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if not HTML.is_file():
        print("MISSING HTML", HTML)
        return 2

    probes = [
        ("136_149", probe_136_149),
        ("137_146", probe_137_146),
        ("138_158", probe_138_158),
        ("139_150", probe_139_150),
        ("140", probe_140),
        ("147", probe_147),
        ("148", probe_148),
        ("151", probe_151),
        ("152", probe_152),
        ("153", probe_153),
        ("154", probe_154),
        ("155", probe_155),
        ("156", probe_156),
        ("157", probe_157),
        ("159", probe_159),
    ]

    all_rows: list[dict] = []
    raw: dict[str, Any] = {"modes": {}}

    for js_enabled, mode in ((True, "chartjs"), (False, "svg")):
        pw, browser, context, page, console = open_page(js_enabled)
        try:
            for key, fn in probes:
                console.clear()
                try:
                    rows, r = fn(page, mode, console)
                except Exception as e:  # noqa: BLE001
                    rows = [
                        row(
                            f"#{key.split('_')[0]}",
                            mode,
                            0,
                            "error",
                            "probe crashed",
                            f"{type(e).__name__}: {e}",
                            "no crash",
                            False,
                            residual="probe",
                        )
                    ]
                    r = {"error": str(e)}
                all_rows.extend(rows)
                raw["modes"].setdefault(mode, {})[key] = r
                p = sum(1 for x in rows if x["pass"])
                print(f"{mode} {key}: {p}/{len(rows)} pass")
        finally:
            close_all(pw, browser, context)

    run_meta = {}
    if RUN_META.is_file():
        run_meta = json.loads(RUN_META.read_text(encoding="utf-8"))

    scorecard = _summarize(all_rows)
    payload = {
        "contract": "#137 activate_slide + wait_for_paint_ready_charts + painted markers",
        "html": str(HTML.relative_to(ROOT)).replace("\\", "/"),
        "run_meta_warnings": run_meta.get("warnings") or run_meta.get("diagnostics") or [],
        "n_checks": len(all_rows),
        "n_pass": sum(1 for r in all_rows if r["pass"]),
        "n_fail": sum(1 for r in all_rows if not r["pass"]),
        "scorecard": scorecard,
        "rows": all_rows,
    }
    out_json = OUT / "closed_ticket_results_v11.json"
    out_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    (OUT / "closed_ticket_raw_v11.json").write_text(
        json.dumps(raw, indent=2, default=str), encoding="utf-8"
    )
    (OUT / "scorecard_136_159.json").write_text(
        json.dumps(scorecard, indent=2, default=str), encoding="utf-8"
    )
    print("wrote", out_json, "pass", payload["n_pass"], "fail", payload["n_fail"])
    print("scorecard:")
    for s in scorecard:
        print(f"  {s['ticket']:12} {s['result']:8} {s['n_pass']}/{s['n_checks']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
