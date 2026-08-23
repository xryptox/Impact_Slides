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
        furniture_presence,
        measured_bar_occupancy,
        measured_metric_value_styles,
        measured_series_palette,
        measured_stub_ratio,
        measured_support_chrome,
        measured_tick_styles,
        painted_datalabel_lines,
        wait_for_paint_ready_charts,
    )

    activate_slide(page, 12, "chart_hero_dual")
    wait_for_paint_ready_charts(page, 12, "chart_hero_dual")
    row = count_in_slide(page, 12, "chart_hero_dual", ".gl-hero-stack")
    labels = painted_datalabel_lines(page, 12, "chart_hero_dual")
    ticks = measured_tick_styles(page, 12, "chart_hero_dual")
    furn = furniture_presence(page, 12, "chart_hero_dual", ".support-table")
"""
from __future__ import annotations

import re
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


# DP-1 / DP-6 design-ledger floors. Tick probes measure computed style on the
# painted SVG overlay (Chart.js scale ticks are display:false).
TICK_FONT_SIZE_FLOOR_PX = 20
TICK_FONT_WEIGHT_FLOOR = 600
# DP-6 extensions (#249): V1–V3 fidelity properties that must not regress silently.
TABLE_STUB_MAX_SHARE = 0.45
METRIC_VALUE_FLOOR_PX = 40
BAR_OCCUPANCY_FLOOR = 0.5
# Theme success green is semantic-only (#248); never a non-semantic series fill.
FORBIDDEN_SERIES_HEX = "#0A7D55"
SKY_BLUE_HEX = "#80C8FF"
# Table slides that must keep stub ≤ 45% (s29–30 are narrative; annex starts 31).
DESIGN_LEDGER_STUB_RATIO_SLIDES: tuple[int, ...] = (
    3, 16, 31, 32, 33, 34, 35, 36, 37,
)
# s4/s19: D167 hide_header + hairline body cells. Missing body frame fails;
# navy .head band is only required when a visual header row is painted.
DESIGN_LEDGER_SUPPORT_CHROME_SLIDES: tuple[int, ...] = (4, 19)
# s28 authors sky_blue stacks; s24 is a single navy series (no sky required).
DESIGN_LEDGER_PALETTE_SLIDES: dict[int, dict[str, bool]] = {
    24: {"require_sky_blue": False},
    28: {"require_sky_blue": True},
}
DESIGN_LEDGER_METRIC_FLOOR_SLIDES: tuple[int, ...] = (8, 12)
DESIGN_LEDGER_BAR_OCCUPANCY_SLIDES: tuple[int, ...] = (28,)


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


# DP-2 furniture probes for the design ledger. The sim records one presence
# row per entry; helpers still require unique slide identity + ≥1 match.
DESIGN_LEDGER_FURNITURE: dict[int, tuple[dict[str, str], ...]] = {
    4: (
        {
            "selector": "[data-annotation-id]",
            "expected_text": "Leap Year Approx. (1%)",
        },
        {"selector": ".support-table", "expected_text": "G&S"},
    ),
    5: (
        {"selector": ".support-table", "expected_text": "Gen-Z"},
        {
            "selector": "[data-annotation-id]",
            "expected_text": "Leap Year Approx. (1%)",
        },
        {"selector": "[data-context-id=\"gs-yoy\"]", "expected_text": "9% YoY"},
        {"selector": "[data-context-id=\"te-yoy\"]", "expected_text": "11% YoY"},
    ),
    6: (
        {
            "selector": "[data-annotation-id]",
            "expected_text": "+ ~6 percentage points",
        },
        {
            "selector": "[data-annotation-id]",
            "expected_text": "Refresh",
        },
    ),
    8: (
        {"selector": ".metric-strip", "expected_text": "3,400+"},
        {
            "selector": "[data-annotation-id]",
            "expected_text": "10x",
        },
    ),
    9: (
        {"selector": ".support-table", "expected_text": "U.S. SME"},
        {
            "selector": "[data-annotation-id]",
            "expected_text": "Leap Year Approx. (1%)",
        },
        {"selector": "[data-context-id=\"gs-yoy\"]", "expected_text": "3% YoY"},
        {"selector": "[data-context-id=\"te-yoy\"]", "expected_text": "6% YoY"},
    ),
    10: (
        {"selector": ".support-table", "expected_text": "Intl Consumer"},
        {
            "selector": "[data-annotation-id]",
            "expected_text": "Leap Year Approx. (1%)",
        },
        {"selector": "[data-context-id=\"gs-yoy\"]", "expected_text": "14% YoY"},
        {"selector": "[data-context-id=\"te-yoy\"]", "expected_text": "10% YoY"},
    ),
    11: (
        {
            "selector": "[data-annotation-id]",
            "expected_text": "Leap Year Approx. (1%)",
        },
    ),
    12: (
        {
            "selector": '[data-chart-type="stacked_bar"]',
            "expected_text": "International Card Services",
        },
    ),
    15: (
        {
            "selector": ".outlined-support",
            "expected_text": "Reserve Rate for Total Balances",
        },
    ),
    17: (
        {
            "selector": '[data-measurement-id][data-role="cagr"]',
            "expected_text": "17%",
        },
    ),
    18: (
        {"selector": ".boxed-label", "expected_text": "11%"},
        {
            "selector": '[data-hero-type="driver_card"]',
            "expected_text": "Billed Business",
        },
    ),
    19: (
        {
            "selector": "[data-annotation-id]",
            "expected_text": "Leap Year Approx. (1%)",
        },
        {"selector": ".support-table", "expected_text": "$17.0"},
    ),
    21: (
        {
            "selector": '[data-chart-type="combo"] [data-semantic-table]',
            "expected_text": "Common Shares Outstanding",
        },
        {"selector": ".outlined-support", "expected_text": "ROE"},
    ),
    24: (
        {"selector": ".category-group", "expected_text": "Commercial Services"},
        {
            "selector": "[data-annotation-id]",
            "expected_text": "$486B Total Network Volumes",
        },
        {"selector": ".outlined-support", "expected_text": "% of Total Network Volumes"},
    ),
    28: (
        {"selector": "[data-annotation-id]", "expected_text": "92% FDIC"},
    ),
}


def _parse_font_weight(raw: Any) -> int | None:
    if raw is None:
        return None
    text = str(raw).strip().lower()
    if text == "normal":
        return 400
    if text == "bold":
        return 700
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return None


def measured_tick_styles(
    page: Any,
    slide_number: int,
    expected_layout: str,
    *,
    size_floor_px: int = TICK_FONT_SIZE_FLOOR_PX,
    weight_floor: int = TICK_FONT_WEIGHT_FLOOR,
) -> dict[str, Any]:
    """Measure computed tick font-size/weight on the painted SVG overlay.

    Ticks are overlay ``<text>`` nodes that carry ``font-weight`` and do not
    have ``data-placement`` (value labels) or live inside furniture groups.
    Computed style is authoritative — presentation attributes alone are not.
    Zero ticks, size below *size_floor_px*, or weight below *weight_floor*
    raise :class:`ProbeError`.
    """
    identity = activate_slide(page, slide_number, expected_layout)
    sn = identity["slide_number"]
    result = page.evaluate(
        """({sn}) => {
          const slide = document.querySelector(
            'section.slide[data-slide-number="' + sn + '"]'
          );
          if (!slide) {
            return {ok: false, err: 'slide disappeared: data-slide-number=' + sn};
          }
          const svgs = slide.querySelectorAll('.chart-label-overlay svg.chart-svg');
          if (svgs.length === 0) {
            return {
              ok: false,
              err: '0 tick texts in overlay on slide ' + sn
                + ' (no chart-label-overlay svg)',
            };
          }
          const skip = '.category-group, .boxed-label, .context-label,'
            + ' .chart-annotation, .chart-measurement, .coverage-callout';
          const ticks = [];
          svgs.forEach((svg) => {
            svg.querySelectorAll('text').forEach((el) => {
              if (el.closest(skip)) return;
              if (el.hasAttribute('data-placement')) return;
              if (!el.hasAttribute('font-weight')) return;
              const cs = getComputedStyle(el);
              ticks.push({
                text: (el.textContent || '').trim(),
                font_size_px: parseFloat(cs.fontSize),
                font_weight: cs.fontWeight,
              });
            });
          });
          if (ticks.length === 0) {
            return {ok: false, err: '0 tick texts in overlay on slide ' + sn};
          }
          return {ok: true, ticks};
        }""",
        {"sn": sn},
    )
    if not result or not result.get("ok"):
        err = (result or {}).get("err") or "measured_tick_styles failed"
        raise ProbeError(err)
    ticks: list[dict[str, Any]] = []
    for raw in result["ticks"]:
        size = float(raw.get("font_size_px") or 0)
        weight = _parse_font_weight(raw.get("font_weight"))
        if weight is None or not (size > 0):
            raise ProbeError(
                f"unreadable tick computed style on slide {sn}: "
                f"font-size={raw.get('font_size_px')!r} "
                f"font-weight={raw.get('font_weight')!r}"
            )
        ticks.append(
            {
                "text": raw.get("text") or "",
                "font_size_px": size,
                "font_weight": weight,
            }
        )
    min_size = min(t["font_size_px"] for t in ticks)
    min_weight = min(t["font_weight"] for t in ticks)
    if min_size < float(size_floor_px):
        raise ProbeError(
            f"tick font-size {min_size}px below floor {int(size_floor_px)} "
            f"on slide {sn}"
        )
    if min_weight < int(weight_floor):
        raise ProbeError(
            f"tick font-weight {min_weight} below floor {int(weight_floor)} "
            f"on slide {sn}"
        )
    out = dict(identity)
    out["ticks"] = ticks
    out["tick_count"] = len(ticks)
    out["min_font_size_px"] = min_size
    out["min_font_weight"] = min_weight
    out["ok"] = True
    return out


def furniture_presence(
    page: Any,
    slide_number: int,
    expected_layout: str,
    selector: str,
    *,
    expected_text: str | None = None,
) -> dict[str, Any]:
    """Assert furniture *selector* is present inside the identified slide.

    Zero matches raise :class:`ProbeError`. When *expected_text* is set, at
    least one matched node's ``textContent`` must contain it.
    """
    if not selector or not str(selector).strip():
        raise ProbeError("selector must be non-empty")
    identity = activate_slide(page, slide_number, expected_layout)
    sn = identity["slide_number"]
    result = page.evaluate(
        """({sn, selector, expected}) => {
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
          if (expected) {
            let hit = false;
            for (let i = 0; i < nodes.length; i++) {
              if ((nodes[i].textContent || '').includes(expected)) {
                hit = true;
                break;
              }
            }
            if (!hit) {
              return {
                ok: false,
                err: 'expected text ' + JSON.stringify(expected)
                  + ' not in matched furniture on slide ' + sn,
              };
            }
          }
          return {ok: true, count: nodes.length};
        }""",
        {"sn": sn, "selector": selector, "expected": expected_text or ""},
    )
    if not result or not result.get("ok"):
        err = (result or {}).get("err") or "furniture_presence failed"
        raise ProbeError(err)
    out = dict(identity)
    out["selector"] = selector
    if expected_text:
        out["expected_text"] = expected_text
    out["count"] = int(result["count"])
    out["ok"] = True
    return out


def _normalize_hex_color(raw: Any) -> str | None:
    """Normalize #rgb / #rrggbb / rgb()/rgba() to uppercase #RRGGBB.

    Fully transparent colors (``transparent``, ``rgba(*,*,*,0)``, ``#RRGGBB00``)
    return None so support-chrome band checks cannot treat empty fills as paint.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or text.lower() in {"transparent", "inherit", "initial", "none"}:
        return None
    if text.startswith("#"):
        h = text[1:]
        if len(h) == 3 and re.fullmatch(r"[0-9a-fA-F]{3}", h):
            h = "".join(ch * 2 for ch in h)
        if len(h) == 6 and re.fullmatch(r"[0-9a-fA-F]{6}", h):
            return f"#{h.upper()}"
        if len(h) == 8 and re.fullmatch(r"[0-9a-fA-F]{8}", h):
            # #RRGGBBAA — alpha 00 is unpainted, not a band fill.
            if h[6:8].lower() == "00":
                return None
            return f"#{h[:6].upper()}"
        return None
    m = re.fullmatch(
        r"rgba?\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)(?:\s*,\s*([0-9.]+))?\s*\)",
        text,
        flags=re.I,
    )
    if not m:
        return None
    if m.group(4) is not None and float(m.group(4)) <= 0.0:
        return None
    r, g, b = (max(0, min(255, int(float(m.group(i))))) for i in (1, 2, 3))
    return f"#{r:02X}{g:02X}{b:02X}"


def measured_stub_ratio(
    page: Any,
    slide_number: int,
    expected_layout: str,
    *,
    max_share: float = TABLE_STUB_MAX_SHARE,
) -> dict[str, Any]:
    """Assert painted stub column width ≤ *max_share* of table width (DP-7).

    Measures the first visible ``th.stub``/``td.stub`` (or annex stub) against
    its table's bounding box. Zero tables / zero stub cells fail.
    """
    identity = activate_slide(page, slide_number, expected_layout)
    sn = identity["slide_number"]
    result = page.evaluate(
        """({sn}) => {
          const slide = document.querySelector(
            'section.slide[data-slide-number="' + sn + '"]'
          );
          if (!slide) {
            return {ok: false, err: 'slide disappeared: data-slide-number=' + sn};
          }
          const tables = [...slide.querySelectorAll(
            'table.data-table, table.period-comparison, table.annex-table,'
            + ' table.support-table, table.grouped-annex-table, .grouped-annex table'
          )].filter((t) => {
            const r = t.getBoundingClientRect();
            return r.width > 1 && r.height > 1;
          });
          if (!tables.length) {
            return {ok: false, err: '0 painted tables on slide ' + sn};
          }
          const rows = [];
          for (const table of tables) {
            const tr = table.getBoundingClientRect();
            const stub = table.querySelector(
              'th.stub, td.stub, th.gl-annex-stub, td.gl-annex-stub,'
              + ' .gl-annex-stub, colgroup col:first-child'
            );
            if (!stub) {
              return {
                ok: false,
                err: '0 stub cells in table on slide ' + sn,
              };
            }
            let stubW;
            if (stub.tagName === 'COL') {
              stubW = parseFloat(String(stub.style.width || '').replace('px', '')) || 0;
              if (!(stubW > 0)) {
                const cell = table.querySelector('th.stub, td.stub, th.gl-annex-stub, td.gl-annex-stub');
                stubW = cell ? cell.getBoundingClientRect().width : 0;
              }
            } else {
              stubW = stub.getBoundingClientRect().width;
            }
            if (!(tr.width > 0) || !(stubW > 0)) {
              return {
                ok: false,
                err: 'unreadable stub/table width on slide ' + sn
                  + ' (stub=' + stubW + ', table=' + tr.width + ')',
              };
            }
            rows.push({
              table_width_px: tr.width,
              stub_width_px: stubW,
              share: stubW / tr.width,
            });
          }
          return {ok: true, tables: rows};
        }""",
        {"sn": sn},
    )
    if not result or not result.get("ok"):
        err = (result or {}).get("err") or "measured_stub_ratio failed"
        raise ProbeError(err)
    tables = list(result["tables"] or [])
    max_observed = max(float(t["share"]) for t in tables)
    if max_observed > float(max_share) + 1e-9:
        raise ProbeError(
            f"stub share {max_observed:.3f} exceeds cap {float(max_share):.2f} "
            f"on slide {sn}"
        )
    out = dict(identity)
    out["tables"] = tables
    out["table_count"] = len(tables)
    out["max_stub_share"] = max_observed
    out["max_share"] = float(max_share)
    out["ok"] = True
    return out


def measured_support_chrome(
    page: Any,
    slide_number: int,
    expected_layout: str,
) -> dict[str, Any]:
    """Assert category-aligned support chrome that actually ships.

    Visible body cells (``.support-cat-cell`` without ``.head``) must exist
    and carry a ≥1px hairline. s4/s19 hide the visual header (D167:
    chart-owned categories) and pass on that body frame alone. When a
    visual header row *is* painted (``.head``), keep the navy-band +
    hairline assertion from #250. A missing body frame fails either way.
    """
    identity = activate_slide(page, slide_number, expected_layout)
    sn = identity["slide_number"]
    result = page.evaluate(
        """({sn}) => {
          const slide = document.querySelector(
            'section.slide[data-slide-number="' + sn + '"]'
          );
          if (!slide) {
            return {ok: false, err: 'slide disappeared: data-slide-number=' + sn};
          }
          const vis = (el) => {
            const r = el.getBoundingClientRect();
            return r.width > 1 && r.height > 1;
          };
          const pack = (el) => {
            const s = getComputedStyle(el);
            return {
              bg: s.backgroundColor,
              borderTop: s.borderTopWidth,
              borderRight: s.borderRightWidth,
              borderBottom: s.borderBottomWidth,
              borderLeft: s.borderLeftWidth,
            };
          };
          const heads = [...slide.querySelectorAll(
            '.support-table.category-aligned .support-cat-cell.head,'
            + ' .support-table.category-aligned .support-cat-stub.head'
          )].filter(vis);
          const bodies = [...slide.querySelectorAll(
            '.support-table.category-aligned .support-cat-cell'
          )].filter((el) => vis(el) && !el.classList.contains('head'));
          if (!bodies.length) {
            return {
              ok: false,
              err: '0 visible support body cells on slide ' + sn,
            };
          }
          return {ok: true, heads: heads.map(pack), bodies: bodies.map(pack)};
        }""",
        {"sn": sn},
    )
    if not result or not result.get("ok"):
        err = (result or {}).get("err") or "measured_support_chrome failed"
        raise ProbeError(err)

    def _border_px(v: str) -> float:
        try:
            return float(v.replace("px", "").strip() or 0)
        except ValueError:
            return 0.0

    def _pack_borders(raw: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
        borders = [
            str(raw.get("borderTop") or ""),
            str(raw.get("borderRight") or ""),
            str(raw.get("borderBottom") or ""),
            str(raw.get("borderLeft") or ""),
        ]
        packed = {
            "background": _normalize_hex_color(raw.get("bg")),
            "border_top_px": _border_px(borders[0]),
            "border_right_px": _border_px(borders[1]),
            "border_bottom_px": _border_px(borders[2]),
            "border_left_px": _border_px(borders[3]),
        }
        return borders, packed

    bodies: list[dict[str, Any]] = []
    for raw in result["bodies"]:
        borders, packed = _pack_borders(raw)
        if not any(packed[k] >= 1.0 for k in (
            "border_top_px", "border_right_px",
            "border_bottom_px", "border_left_px",
        )):
            raise ProbeError(
                f"support body missing hairline border on slide {sn}: "
                f"borders={borders!r}"
            )
        bodies.append(packed)

    heads: list[dict[str, Any]] = []
    for raw in result["heads"]:
        bg = _normalize_hex_color(raw.get("bg"))
        if bg is None or bg == "#FFFFFF":
            raise ProbeError(
                f"support header missing band background on slide {sn}: "
                f"bg={raw.get('bg')!r}"
            )
        borders, packed = _pack_borders(raw)
        packed["background"] = bg
        if not any(packed[k] >= 1.0 for k in (
            "border_top_px", "border_right_px",
            "border_bottom_px", "border_left_px",
        )):
            raise ProbeError(
                f"support header missing hairline border on slide {sn}: "
                f"borders={borders!r}"
            )
        heads.append(packed)
    out = dict(identity)
    out["heads"] = heads
    out["head_count"] = len(heads)
    out["bodies"] = bodies
    out["body_count"] = len(bodies)
    out["hide_header"] = len(heads) == 0
    out["ok"] = True
    return out


def measured_series_palette(
    page: Any,
    slide_number: int,
    expected_layout: str,
    *,
    forbid_hex: str = FORBIDDEN_SERIES_HEX,
    require_sky_blue: bool = False,
    sky_hex: str = SKY_BLUE_HEX,
) -> dict[str, Any]:
    """Assert non-semantic series colors avoid *forbid_hex*; optional sky presence.

    Reads Chart.js dataset ``backgroundColor`` / ``borderColor`` after paint.
    Zero datasets fail. *forbid_hex* among series colors is a probe failure.
    """
    identity = activate_slide(page, slide_number, expected_layout)
    sn = identity["slide_number"]
    measure_js = (
        "({sn}) => {"
        + _CHART_FROM_CANVAS
        + """
          const slide = document.querySelector(
            'section.slide[data-slide-number="' + sn + '"]'
          );
          if (!slide) {
            return {ok: false, err: 'slide disappeared: data-slide-number=' + sn};
          }
          const colors = [];
          const canvases = slide.querySelectorAll('canvas');
          if (!canvases.length) {
            return {ok: false, err: '0 chart canvases on slide ' + sn};
          }
          for (let i = 0; i < canvases.length; i++) {
            const chart = chartFromCanvas(canvases[i]);
            if (!chart || !chart.data || !chart.data.datasets) {
              return {
                ok: false,
                err: 'missing chart datasets on slide ' + sn + ' canvas ' + i,
              };
            }
            const datasets = chart.data.datasets;
            if (!datasets.length) {
              return {ok: false, err: '0 datasets on slide ' + sn + ' canvas ' + i};
            }
            for (let di = 0; di < datasets.length; di++) {
              const ds = datasets[di];
              const bag = [];
              const push = (c) => {
                if (c == null) return;
                if (Array.isArray(c)) c.forEach(push);
                else bag.push(String(c));
              };
              push(ds.backgroundColor);
              push(ds.borderColor);
              if (!bag.length) {
                return {
                  ok: false,
                  err: 'dataset ' + di + ' has no series colors on slide ' + sn,
                };
              }
              colors.push({
                canvas: i,
                dataset: di,
                label: ds.label || '',
                colors: bag,
              });
            }
          }
          return {ok: true, series: colors};
        }"""
    )
    result = page.evaluate(measure_js, {"sn": sn})
    if not result or not result.get("ok"):
        err = (result or {}).get("err") or "measured_series_palette failed"
        raise ProbeError(err)
    forbid = (_normalize_hex_color(forbid_hex) or str(forbid_hex).upper())
    sky = (_normalize_hex_color(sky_hex) or str(sky_hex).upper())
    series_out: list[dict[str, Any]] = []
    all_hex: list[str] = []
    for raw in result["series"]:
        norms: list[str] = []
        for c in raw.get("colors") or []:
            hx = _normalize_hex_color(c)
            if hx is None:
                raise ProbeError(
                    f"unreadable series color on slide {sn}: {c!r}"
                )
            norms.append(hx)
            all_hex.append(hx)
            if hx == forbid:
                raise ProbeError(
                    f"forbidden series color {forbid} on slide {sn} "
                    f"(dataset={raw.get('label')!r})"
                )
        series_out.append(
            {
                "canvas": raw.get("canvas"),
                "dataset": raw.get("dataset"),
                "label": raw.get("label") or "",
                "colors": norms,
            }
        )
    if not all_hex:
        raise ProbeError(f"0 series colors on slide {sn}")
    if require_sky_blue and sky not in all_hex:
        raise ProbeError(
            f"authored sky_blue {sky} missing from series colors on slide {sn}"
        )
    out = dict(identity)
    out["series"] = series_out
    out["colors"] = sorted(set(all_hex))
    out["has_sky_blue"] = sky in all_hex
    out["ok"] = True
    return out


def measured_metric_value_styles(
    page: Any,
    slide_number: int,
    expected_layout: str,
    *,
    size_floor_px: int = METRIC_VALUE_FLOOR_PX,
) -> dict[str, Any]:
    """Assert metric-strip / hero metric values meet the painted px floor.

    Targets ``.metric-strip .metric-value`` and hero ``.metric-value`` /
    ``.driver-value``. Zero matches fail. Computed font-size is authoritative.
    """
    identity = activate_slide(page, slide_number, expected_layout)
    sn = identity["slide_number"]
    result = page.evaluate(
        """({sn}) => {
          const slide = document.querySelector(
            'section.slide[data-slide-number="' + sn + '"]'
          );
          if (!slide) {
            return {ok: false, err: 'slide disappeared: data-slide-number=' + sn};
          }
          const nodes = slide.querySelectorAll(
            '.metric-strip .metric-value, .metric-value, .driver-value'
          );
          if (!nodes.length) {
            return {ok: false, err: '0 metric values on slide ' + sn};
          }
          const values = [];
          nodes.forEach((el) => {
            const cs = getComputedStyle(el);
            values.push({
              text: (el.textContent || '').trim(),
              font_size_px: parseFloat(cs.fontSize),
            });
          });
          return {ok: true, values};
        }""",
        {"sn": sn},
    )
    if not result or not result.get("ok"):
        err = (result or {}).get("err") or "measured_metric_value_styles failed"
        raise ProbeError(err)
    values: list[dict[str, Any]] = []
    for raw in result["values"]:
        size = float(raw.get("font_size_px") or 0)
        if not (size > 0):
            raise ProbeError(
                f"unreadable metric value font-size on slide {sn}: "
                f"{raw.get('font_size_px')!r}"
            )
        values.append({"text": raw.get("text") or "", "font_size_px": size})
    min_size = min(v["font_size_px"] for v in values)
    if min_size < float(size_floor_px):
        raise ProbeError(
            f"metric value font-size {min_size}px below floor "
            f"{int(size_floor_px)} on slide {sn}"
        )
    out = dict(identity)
    out["values"] = values
    out["value_count"] = len(values)
    out["min_font_size_px"] = min_size
    out["ok"] = True
    return out


def measured_bar_occupancy(
    page: Any,
    slide_number: int,
    expected_layout: str,
    *,
    min_ratio: float = BAR_OCCUPANCY_FLOOR,
) -> dict[str, Any]:
    """Assert painted bar width / category pitch ≥ *min_ratio* (DP-7 sparse).

    Uses Chart.js element geometry after paint-ready. Zero bar elements fail.
    """
    identity = activate_slide(page, slide_number, expected_layout)
    sn = identity["slide_number"]
    measure_js = (
        "({sn}) => {"
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
            return {ok: false, err: '0 chart canvases on slide ' + sn};
          }
          const charts = [];
          for (let i = 0; i < canvases.length; i++) {
            const chart = chartFromCanvas(canvases[i]);
            if (!chart) {
              return {ok: false, err: 'missing chart on slide ' + sn + ' canvas ' + i};
            }
            const area = chart.chartArea || {};
            const areaW = (typeof area.width === 'number')
              ? area.width
              : (Number(area.right) - Number(area.left));
            const labels = (chart.data && chart.data.labels) || [];
            const nCat = labels.length;
            if (!(nCat > 0) || !(areaW > 0)) {
              return {
                ok: false,
                err: 'unreadable category pitch on slide ' + sn
                  + ' (nCat=' + nCat + ', areaW=' + areaW + ')',
              };
            }
            const pitch = areaW / nCat;
            let maxBar = 0;
            let barCount = 0;
            const datasets = (chart.data && chart.data.datasets) || [];
            for (let di = 0; di < datasets.length; di++) {
              if (typeof chart.isDatasetVisible === 'function'
                  && !chart.isDatasetVisible(di)) continue;
              const meta = chart.getDatasetMeta
                ? chart.getDatasetMeta(di) : null;
              if (!meta || meta.hidden) continue;
              const t = (meta.type || (chart.config && chart.config.type) || '')
                .toString().toLowerCase();
              // Stacked/grouped bars only; skip pure line datasets on combos.
              if (t && t !== 'bar') continue;
              const els = meta.data || [];
              for (let ei = 0; ei < els.length; ei++) {
                const el = els[ei];
                if (!el || el.skip) continue;
                const w = Math.abs(Number(el.width) || 0);
                const h = Math.abs(Number(el.height) || 0);
                // Vertical bars: width is thickness; horizontal: height.
                const thick = Math.max(w, 0);
                if (thick > 0 || h > 0) {
                  barCount += 1;
                  if (thick > maxBar) maxBar = thick;
                }
              }
            }
            if (barCount === 0 || !(maxBar > 0)) {
              return {
                ok: false,
                err: '0 painted bars on slide ' + sn + ' canvas ' + i,
              };
            }
            charts.push({
              canvas: i,
              n_cat: nCat,
              category_pitch: pitch,
              bar_width: maxBar,
              ratio: maxBar / pitch,
              bar_count: barCount,
            });
          }
          return {ok: true, charts};
        }"""
    )
    result = page.evaluate(measure_js, {"sn": sn})
    if not result or not result.get("ok"):
        err = (result or {}).get("err") or "measured_bar_occupancy failed"
        raise ProbeError(err)
    charts = list(result["charts"] or [])
    min_observed = min(float(c["ratio"]) for c in charts)
    if min_observed + 1e-9 < float(min_ratio):
        raise ProbeError(
            f"bar occupancy {min_observed:.3f} below floor {float(min_ratio):.2f} "
            f"on slide {sn}"
        )
    out = dict(identity)
    out["charts"] = charts
    out["chart_count"] = len(charts)
    out["min_occupancy"] = min_observed
    out["min_ratio"] = float(min_ratio)
    out["ok"] = True
    return out
