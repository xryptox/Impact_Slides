"""Reusable Playwright helpers for simulation geometry probes.

Address slides only by ``data-slide-number`` + expected ``data-layout``.
Zero selector matches and missing painted Chart.js labels are probe failures,
never successful empty observations. Screenshot callers must wait for
**paint-ready** Chart.js geometry via :func:`wait_for_paint_ready_charts`
(instance + nonzero size + chartArea + dataset elements, held across one rAF).

Usage (from a Playwright page that already loaded a deck HTML)::

    from simulation_probe import (
        activate_slide,
        count_in_slide,
        painted_datalabel_lines,
        wait_for_paint_ready_charts,
    )

    activate_slide(page, 12, "chart_hero_dual")
    wait_for_paint_ready_charts(page, 12, "chart_hero_dual")
    row = count_in_slide(page, 12, "chart_hero_dual", ".gl-hero-stack")
    labels = painted_datalabel_lines(page, 12, "chart_hero_dual")
"""
from __future__ import annotations

import time
from typing import Any

# JS body shared by readiness wait + measurement (resolves Chart on a canvas).
_CHART_FROM_CANVAS = """
  function chartFromCanvas(canvas) {
    if (!canvas) return null;
    if (typeof Chart !== 'undefined' && Chart.getChart) {
      const c = Chart.getChart(canvas);
      if (c) return c;
    }
    return canvas.__chart || canvas.chart || canvas.__fakeChart || null;
  }
"""

# Paint-ready predicates (#146). Each clause is mutation-tested in
# tests/test_simulation_probe_contract.py — do not collapse them.
_CHART_PAINT_READY = """
  function chartAreaSize(area) {
    if (!area) return {w: 0, h: 0};
    const w = (typeof area.width === 'number')
      ? area.width
      : (Number(area.right) - Number(area.left));
    const h = (typeof area.height === 'number')
      ? area.height
      : (Number(area.bottom) - Number(area.top));
    return {w: w, h: h};
  }
  function elementPainted(el) {
    if (!el || el.skip) return false;
    if (!Number.isFinite(el.x) || !Number.isFinite(el.y)) return false;
    const hasBox = (typeof el.width === 'number') || (typeof el.height === 'number');
    if (hasBox) {
      const w = Math.abs(Number(el.width) || 0);
      const h = Math.abs(Number(el.height) || 0);
      if (w <= 0 && h <= 0) return false;
    }
    return true;
  }
  function visibleDatasetsPainted(chart) {
    const datasets = (chart.data && chart.data.datasets) || [];
    if (!datasets.length) return false;
    for (let di = 0; di < datasets.length; di++) {
      if (typeof chart.isDatasetVisible === 'function') {
        if (!chart.isDatasetVisible(di)) continue;
      }
      const meta = chart.getDatasetMeta
        ? chart.getDatasetMeta(di)
        : null;
      if (!meta || meta.hidden) continue;
      const els = meta.data || [];
      let painted = 0;
      for (let i = 0; i < els.length; i++) {
        if (elementPainted(els[i])) painted += 1;
      }
      if (painted === 0) return false;
    }
    return true;
  }
  function chartPaintReady(chart) {
    if (!chart) return false;
    // Predicate A: nonzero chart bitmap size
    if (!(chart.width > 0 && chart.height > 0)) return false;
    // Predicate B: non-degenerate chartArea
    const area = chartAreaSize(chart.chartArea);
    if (!(area.w > 0 && area.h > 0)) return false;
    // Predicate C: every visible dataset has painted element geometry
    if (!visibleDatasetsPainted(chart)) return false;
    return true;
  }
  function slideChartsPaintReady(slide) {
    const canvases = slide.querySelectorAll('canvas');
    if (!canvases.length) return true; // non-chart slide
    for (let i = 0; i < canvases.length; i++) {
      const chart = chartFromCanvas(canvases[i]);
      if (!chartPaintReady(chart)) return false;
    }
    return true;
  }
"""


class ProbeError(RuntimeError):
    """Raised when a simulation probe cannot make a conclusive measurement."""


def _identity(slide_number: int, layout: str) -> dict[str, Any]:
    return {"slide_number": int(slide_number), "layout": layout}


def activate_slide(page: Any, slide_number: int, expected_layout: str) -> dict[str, Any]:
    """Select the unique slide by ``data-slide-number``, assert layout, activate it.

    Returns an identity dict ``{slide_number, layout}``. Raises :class:`ProbeError`
    if the target is missing, duplicated, or the layout does not match.
    Does not wait for Chart.js — non-chart probes stay cheap.
    """
    sn = int(slide_number)
    result = page.evaluate(
        """({sn, expected}) => {
          const sel = 'section.slide[data-slide-number="' + sn + '"]';
          const nodes = document.querySelectorAll(sel);
          if (nodes.length === 0) {
            return {ok: false, err: 'no slide with data-slide-number=' + sn};
          }
          if (nodes.length !== 1) {
            return {
              ok: false,
              err: 'expected 1 slide data-slide-number=' + sn + ', found ' + nodes.length,
            };
          }
          const el = nodes[0];
          const layout = el.getAttribute('data-layout') || '';
          if (layout !== expected) {
            return {
              ok: false,
              err: 'slide ' + sn + ' layout is ' + JSON.stringify(layout)
                + ', expected ' + JSON.stringify(expected),
              layout,
            };
          }
          document.querySelectorAll('section.slide').forEach((s) => {
            s.classList.remove('active');
          });
          el.classList.add('active');
          return {ok: true, layout};
        }""",
        {"sn": sn, "expected": expected_layout},
    )
    if not result or not result.get("ok"):
        err = (result or {}).get("err") or "activate_slide failed"
        raise ProbeError(err)
    return _identity(sn, result["layout"])


def count_in_slide(
    page: Any,
    slide_number: int,
    expected_layout: str,
    selector: str,
) -> dict[str, Any]:
    """Count ``selector`` matches inside the identified slide.

    Zero matches raise :class:`ProbeError` (inconclusive / probe failure).
    Never returns a successful observation of ``0``.
    """
    if not selector or not str(selector).strip():
        raise ProbeError("selector must be non-empty")
    identity = activate_slide(page, slide_number, expected_layout)
    sn = identity["slide_number"]
    result = page.evaluate(
        """({sn, selector}) => {
          const slide = document.querySelector(
            'section.slide[data-slide-number="' + sn + '"]'
          );
          if (!slide) {
            return {ok: false, err: 'slide disappeared: data-slide-number=' + sn};
          }
          let nodes;
          try {
            nodes = slide.querySelectorAll(selector);
          } catch (e) {
            return {ok: false, err: 'invalid selector: ' + String(e)};
          }
          if (nodes.length === 0) {
            return {
              ok: false,
              err: 'selector matched 0 elements in slide ' + sn
                + ' (selector=' + JSON.stringify(selector) + ')',
            };
          }
          return {ok: true, count: nodes.length};
        }""",
        {"sn": sn, "selector": selector},
    )
    if not result or not result.get("ok"):
        err = (result or {}).get("err") or "count_in_slide failed"
        raise ProbeError(err)
    out = dict(identity)
    out["count"] = int(result["count"])
    out["selector"] = selector
    return out


def painted_datalabel_lines(
    page: Any,
    slide_number: int,
    expected_layout: str,
    *,
    chart_index: int = 0,
    timeout_ms: int = 5000,
) -> dict[str, Any]:
    """Read painted Chart.js datalabel model lines from the target slide.

    After activation, waits until the target canvas has a Chart instance and a
    nonempty ``chart.$datalabels._labels`` list, then inspects
    ``_labels[*].model().lines`` (rendered plugin state), not
    ``options.plugins.datalabels``. Missing chart/plugin state/labels or a
    readiness timeout raise :class:`ProbeError`.
    """
    identity = activate_slide(page, slide_number, expected_layout)
    sn = identity["slide_number"]
    idx = int(chart_index)
    ready_js = (
        "({sn, idx}) => {"
        + _CHART_FROM_CANVAS
        + """
        const slide = document.querySelector(
          'section.slide[data-slide-number="' + sn + '"]'
        );
        if (!slide) return false;
        const canvases = slide.querySelectorAll('canvas');
        if (idx < 0 || idx >= canvases.length) return false;
        const chart = chartFromCanvas(canvases[idx]);
        return !!(chart && chart.$datalabels
          && Array.isArray(chart.$datalabels._labels)
          && chart.$datalabels._labels.length > 0);
      }"""
    )
    try:
        page.wait_for_function(
            ready_js, arg={"sn": sn, "idx": idx}, timeout=int(timeout_ms)
        )
    except Exception as exc:
        raise ProbeError(
            f"painted labels did not become ready on slide {sn} "
            f"chart_index={idx} within {int(timeout_ms)}ms"
        ) from exc

    measure_js = (
        "({sn, idx}) => {"
        + _CHART_FROM_CANVAS
        + """
        const slide = document.querySelector(
          'section.slide[data-slide-number="' + sn + '"]'
        );
        if (!slide) {
          return {ok: false, err: 'slide disappeared: data-slide-number=' + sn};
        }
        const canvases = slide.querySelectorAll('canvas');
        if (!canvases.length) {
          return {ok: false, err: 'no canvas in slide ' + sn};
        }
        if (idx < 0 || idx >= canvases.length) {
          return {
            ok: false,
            err: 'chart_index ' + idx + ' out of range (0..' + (canvases.length - 1)
              + ') on slide ' + sn,
          };
        }
        const chart = chartFromCanvas(canvases[idx]);
        if (!chart) {
          return {ok: false, err: 'no Chart instance on canvas index ' + idx
            + ' of slide ' + sn};
        }
        const plugin = chart.$datalabels;
        if (!plugin || !Array.isArray(plugin._labels)) {
          return {
            ok: false,
            err: 'chart.$datalabels._labels missing on slide ' + sn
              + ' chart_index=' + idx
              + ' (do not read options.plugins.datalabels)',
          };
        }
        if (plugin._labels.length === 0) {
          return {
            ok: false,
            err: 'chart.$datalabels._labels is empty on slide ' + sn
              + ' chart_index=' + idx,
          };
        }
        const lines = [];
        for (let i = 0; i < plugin._labels.length; i++) {
          const lab = plugin._labels[i];
          if (!lab || typeof lab.model !== 'function') {
            return {
              ok: false,
              err: 'datalabel[' + i + '] has no model() on slide ' + sn,
            };
          }
          const model = lab.model();
          if (!model || !Array.isArray(model.lines)) {
            return {
              ok: false,
              err: 'datalabel[' + i + '].model().lines missing on slide ' + sn,
            };
          }
          for (const line of model.lines) {
            lines.push(String(line));
          }
        }
        if (lines.length === 0) {
          return {
            ok: false,
            err: 'painted datalabel lines empty on slide ' + sn
              + ' chart_index=' + idx,
          };
        }
        const optDl = chart.options
          && chart.options.plugins
          && chart.options.plugins.datalabels;
        return {
          ok: true,
          lines,
          options_datalabels_keys: optDl ? Object.keys(optDl) : [],
        };
      }"""
    )
    result = page.evaluate(measure_js, {"sn": sn, "idx": idx})
    if not result or not result.get("ok"):
        err = (result or {}).get("err") or "painted_datalabel_lines failed"
        raise ProbeError(err)
    out = dict(identity)
    out["chart_index"] = idx
    out["lines"] = list(result["lines"])
    out["options_datalabels_keys"] = list(result.get("options_datalabels_keys") or [])
    return out


def wait_for_paint_ready_charts(
    page: Any,
    slide_number: int,
    expected_layout: str,
    *,
    timeout_ms: int = 8000,
) -> dict[str, Any]:
    """Activate slide and wait until every Chart.js canvas is paint-ready.

    A canvas is paint-ready only when all hold:

    - a Chart instance exists;
    - ``chart.width`` / ``chart.height`` are nonzero;
    - ``chart.chartArea`` has non-degenerate width and height;
    - every visible dataset has at least one non-degenerate painted element;
    - the above remains true across at least one ``requestAnimationFrame``.

    Slides with no ``canvas`` succeed immediately after identity activation.
    Timeouts raise :class:`ProbeError` carrying ``slide_number`` and layout.
    """
    identity = activate_slide(page, slide_number, expected_layout)
    sn = identity["slide_number"]
    layout = identity["layout"]

    # Predicate D: readiness must survive one animation frame (no fixed sleep).
    # Playwright wait_for_function treats any resolved Promise as success — even
    # Promise.resolve(false) — so poll via evaluate, which returns the boolean.
    ready_js = (
        "({sn}) => new Promise((resolve) => {"
        + _CHART_FROM_CANVAS
        + _CHART_PAINT_READY
        + """
        const slide = document.querySelector(
          'section.slide[data-slide-number="' + sn + '"]'
        );
        if (!slide) { resolve(false); return; }
        if (!slideChartsPaintReady(slide)) { resolve(false); return; }
        requestAnimationFrame(() => {
          resolve(!!slideChartsPaintReady(slide));
        });
      })"""
    )
    deadline = time.monotonic() + (int(timeout_ms) / 1000.0)
    settled = False
    while time.monotonic() < deadline:
        try:
            if page.evaluate(ready_js, {"sn": sn}):
                settled = True
                break
        except Exception:
            pass
        # Yield to the browser event loop so rAF / layout can progress.
        page.evaluate("() => new Promise((r) => requestAnimationFrame(() => r()))")
    if not settled:
        raise ProbeError(
            f"paint-ready charts did not settle on slide {sn} "
            f"layout={layout!r} within {int(timeout_ms)}ms"
        )

    # Measurement only — settle loop already enforced paint-ready predicates.
    measure_js = (
        "({sn}) => {"
        + _CHART_FROM_CANVAS
        + _CHART_PAINT_READY
        + """
        const slide = document.querySelector(
          'section.slide[data-slide-number="' + sn + '"]'
        );
        if (!slide) {
          return {ok: false, err: 'slide disappeared: data-slide-number=' + sn};
        }
        const canvases = slide.querySelectorAll('canvas');
        const charts = [];
        for (let i = 0; i < canvases.length; i++) {
          const chart = chartFromCanvas(canvases[i]);
          if (!chart) {
            return {ok: false, err: 'no Chart on canvas ' + i + ' of slide ' + sn};
          }
          const ca = chart.chartArea || {};
          const area = chartAreaSize(ca);
          charts.push({
            index: i,
            width: Number(chart.width) || 0,
            height: Number(chart.height) || 0,
            chart_area: {
              width: area.w,
              height: area.h,
              left: ca.left,
              top: ca.top,
              right: ca.right,
              bottom: ca.bottom,
            },
          });
        }
        return {ok: true, charts};
      }"""
    )
    result = page.evaluate(measure_js, {"sn": sn})
    if not result or not result.get("ok"):
        err = (result or {}).get("err") or "wait_for_paint_ready_charts failed"
        raise ProbeError(err)
    out = dict(identity)
    charts = list(result.get("charts") or [])
    out["charts"] = charts
    out["chart_count"] = len(charts)
    return out
