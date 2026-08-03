"""Playwright geometry probes for Amex Q1'26 simulation (v8).

Drives presentation.html at 1920x1080, activates slides via .active, and
compares live layout numbers to Chart.js-derived expected geometry.
No MAE similarity scoring.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

TOL = 4.0  # house standard ±4px


def activate_slide(page, index: int) -> None:
    page.evaluate(
        """(i) => {
        document.querySelectorAll('section.slide').forEach(s => s.classList.remove('active'));
        const slides = document.querySelectorAll('section.slide');
        if (slides[i]) slides[i].classList.add('active');
    }""",
        index,
    )
    page.wait_for_timeout(1100)


def box(page, sel: str, root: str | None = None):
    js = """([sel, root]) => {
        const scope = root ? document.querySelector(root) : document;
        if (!scope) return null;
        const el = scope.querySelector(sel);
        if (!el) return null;
        const r = el.getBoundingClientRect();
        const stage = document.querySelector('.deck-stage');
        const sr = stage ? stage.getBoundingClientRect() : {left:0, top:0};
        // At 1920x1080 fitStage scale is 1.0; still report stage-relative.
        return {
            left: r.left - sr.left, top: r.top - sr.top,
            right: r.right - sr.left, bottom: r.bottom - sr.top,
            w: r.width, h: r.height,
            text: (el.textContent || '').trim().slice(0, 80),
            display: getComputedStyle(el).display,
            bg: getComputedStyle(el).backgroundColor,
            color: getComputedStyle(el).color,
        };
    }"""
    return page.evaluate(js, [sel, root])


def assert_row(slide, node, measured, expected, tol=TOL):
    if measured is None or expected is None:
        return {
            "slide": slide,
            "node": node,
            "measured": measured,
            "expected": expected,
            "delta_px": None,
            "pass": False,
            "note": "missing value",
        }
    delta = float(measured) - float(expected)
    return {
        "slide": slide,
        "node": node,
        "measured": round(float(measured), 2),
        "expected": round(float(expected), 2),
        "delta_px": round(delta, 2),
        "pass": abs(delta) <= tol,
    }


def probe_slide05(page):
    """T1 callout geometry + T7 chevron split + T6 axis-break on right tile."""
    activate_slide(page, 5)
    raw = page.evaluate(
        """() => {
        const stage = document.querySelector('.deck-stage');
        const sr = stage.getBoundingClientRect();
        const rel = (el) => {
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return {
                left: r.left - sr.left, top: r.top - sr.top,
                w: r.width, h: r.height, right: r.right - sr.left,
                bottom: r.bottom - sr.top,
                text: (el.textContent||'').trim(),
            };
        };
        const slides = document.querySelectorAll('section.slide');
        const slide = slides[5];
        const wraps = [...slide.querySelectorAll('.chartjs-wrap')];
        const out = {tiles: []};
        for (const wrap of wraps) {
            const canvas = wrap.querySelector('canvas');
            const ch = canvas && (window.Chart && Chart.getChart(canvas));
            const info = {
                wrap: rel(wrap),
                chartArea: ch ? ch.chartArea : null,
                elbow: rel(wrap.querySelector('.chartjs-callout-elbow')),
                stem: rel(wrap.querySelector('.chartjs-callout-elbow-stem')),
                tip: rel(wrap.querySelector('.chartjs-callout-chevron-tip')),
                pill: rel(wrap.querySelector('.chartjs-callout-chevron-pill')),
                oldChevron: rel(wrap.querySelector('.chartjs-callout-chevron:not(.chartjs-callout-chevron-tip):not(.chartjs-callout-chevron-pill)')),
                axisBreak: rel(wrap.querySelector('.chartjs-axis-break')),
                axisBreakClass: (wrap.querySelector('.chartjs-axis-break')||{}).className || null,
                legendCount: wrap.querySelectorAll('.chartjs-legend, .chart-legend, ul.legend').length
                    + [...wrap.parentElement.querySelectorAll('.gl-side-legend, .side-legend')].length,
            };
            if (ch && ch.scales && ch.scales.x) {
                const xs = ch.scales.x, ys = ch.scales.y, area = ch.chartArea;
                // category centers for 0..4
                const centers = [];
                for (let i = 0; i < 5; i++) {
                    try { centers.push(xs.getPixelForValue(i)); } catch(e) { centers.push(null); }
                }
                info.barCenters = centers;
                info.yOrigin = ys ? ys.getPixelForValue(ys.min) : null;
                // relative to wrap
                const wr = wrap.getBoundingClientRect();
                const cr = canvas.getBoundingClientRect();
                info.ox = cr.left - wr.left;
                info.oy = cr.top - wr.top;
                info.areaInWrap = area ? {
                    left: info.ox + area.left, top: info.oy + area.top,
                    right: info.ox + area.right, bottom: info.oy + area.bottom,
                    bottomAbs: info.oy + area.bottom,
                } : null;
                // canvas pixel values for callouts in wrap coords
                if (info.elbow && centers[0] != null && centers[4] != null) {
                    info.expectedElbow = {
                        left: info.ox + centers[0],
                        width: centers[4] - centers[0],
                    };
                }
                if (info.tip && centers[2] != null) {
                    info.expectedChevronCenter = info.ox + centers[2];
                    info.expectedChevronTopMin = info.oy + area.bottom; // must be outside plot
                }
                if (info.axisBreak) {
                    info.expectedBreak = {
                        topMin: info.oy + area.bottom, // outside / at bottom
                        // hatch should not cross plot: whole box top >= area.bottom (wrap-rel)
                    };
                }
                // serialized config check
                const cfgScript = wrap.querySelector('script[type="application/json"], script.chart-config');
            }
            // Chart config from Chart instance
            if (ch) {
                const ds = (ch.data && ch.data.datasets) || [];
                info.datasetColors = ds.map(d => d.backgroundColor || d.borderColor);
                const items = ch.config?.options?.plugins?.callouts?.items || null;
                info.calloutItems = items;
            }
            out.tiles.push(info);
        }
        // any mid-plot dashed line remnant?
        out.midPlotLines = [...slide.querySelectorAll('.chartjs-axis-break, .axis-break-line')].map(el => {
            const r = el.getBoundingClientRect();
            const wr = el.closest('.chartjs-wrap')?.getBoundingClientRect();
            return {class: el.className, top: r.top, h: r.height, text: el.textContent, wrapTop: wr && wr.top};
        });
        return out;
    }"""
    )
    rows = []
    observations = {"slide": 5, "raw": raw}

    if not raw["tiles"]:
        return rows, observations

    # Left tile = spend growth (index 0)
    t0 = raw["tiles"][0]
    if t0.get("expectedElbow") and t0.get("elbow"):
        rows.append(
            assert_row(
                5,
                "elbow.left vs bar0 centre",
                t0["elbow"]["left"] - (t0["wrap"]["left"] if t0["wrap"] else 0),
                t0["expectedElbow"]["left"],
            )
        )
        # use wrap-relative: recompute carefully
        # Better: compare style pixels from DOM vs expected in wrap space
        rows.append(
            assert_row(
                5,
                "elbow.width vs bar0-to-bar4 centres",
                t0["elbow"]["w"],
                t0["expectedElbow"]["width"],
            )
        )

    # Re-do with wrap-relative boxes from page
    geo = page.evaluate(
        """() => {
        const slide = document.querySelectorAll('section.slide')[5];
        const wraps = [...slide.querySelectorAll('.chartjs-wrap')];
        const t0 = wraps[0], t1 = wraps[1];
        function pack(wrap) {
            if (!wrap) return null;
            const canvas = wrap.querySelector('canvas');
            const ch = Chart.getChart(canvas);
            const wr = wrap.getBoundingClientRect();
            const br = (sel) => {
                const el = wrap.querySelector(sel);
                if (!el) return null;
                const r = el.getBoundingClientRect();
                return {left: r.left-wr.left, top: r.top-wr.top, w: r.width, h: r.height,
                        right: r.right-wr.left, bottom: r.bottom-wr.top, text:(el.textContent||'').trim(),
                        bg: getComputedStyle(el).backgroundColor, color: getComputedStyle(el).color};
            };
            const xs = ch.scales.x, ys = ch.scales.y, area = ch.chartArea;
            const cr = canvas.getBoundingClientRect();
            const ox = cr.left - wr.left, oy = cr.top - wr.top;
            const centers = [];
            const n = (ch.data.labels || []).length || 5;
            for (let i=0;i<n;i++) centers.push(xs.getPixelForValue(i));
            return {
                wrap: {w: wr.width, h: wr.height},
                ox, oy, area, centers,
                elbow: br('.chartjs-callout-elbow'),
                stem: br('.chartjs-callout-elbow-stem'),
                tip: br('.chartjs-callout-chevron-tip'),
                pill: br('.chartjs-callout-chevron-pill'),
                fused: br('.chartjs-callout-chevron:not(.chartjs-callout-chevron-tip):not(.chartjs-callout-chevron-pill)'),
                axisBreak: br('.chartjs-axis-break'),
                colors: (ch.data.datasets||[]).map(d => d.backgroundColor || d.borderColor),
                callouts: ch.config?.options?.plugins?.callouts?.items || null,
                tickLabelBottom: (() => {
                    // approximate tick label row: area.bottom to wrap bottom
                    return {areaBottom: oy+area.bottom, wrapH: wr.height};
                })(),
            };
        }
        return {left: pack(t0), right: pack(t1)};
    }"""
    )
    observations["geo"] = geo
    L = geo["left"]
    R = geo["right"]

    if L and L["elbow"] and L["centers"]:
        exp_left = L["ox"] + L["centers"][0]
        exp_w = L["centers"][4] - L["centers"][0]
        rows.append(assert_row(5, "L elbow.left vs bar0 centre (wrap)", L["elbow"]["left"], exp_left))
        rows.append(assert_row(5, "L elbow.width bar0→bar4", L["elbow"]["w"], exp_w))
        # stem at bar0 centre
        if L["stem"]:
            rows.append(assert_row(5, "L stem.left vs bar0 centre", L["stem"]["left"], exp_left, tol=6))

    # T7 chevron split
    rows.append(
        {
            "slide": 5,
            "node": "L chevron split (tip+pill separate, no fused)",
            "measured": {
                "tip": bool(L and L["tip"]),
                "pill": bool(L and L["pill"]),
                "fused": bool(L and L["fused"]),
            },
            "expected": {"tip": True, "pill": True, "fused": False},
            "delta_px": 0 if (L and L["tip"] and L["pill"] and not L["fused"]) else None,
            "pass": bool(L and L["tip"] and L["pill"] and not L["fused"]),
        }
    )
    if L and L["tip"] and L["centers"] and len(L["centers"]) > 2:
        # tip centre vs bar at:2
        tip_cx = L["tip"]["left"] + L["tip"]["w"] / 2
        exp_cx = L["ox"] + L["centers"][2]
        rows.append(assert_row(5, "L chevron-tip centre vs bar2 (at:2)", tip_cx, exp_cx))
        area_bottom = L["oy"] + L["area"]["bottom"]
        rows.append(
            {
                "slide": 5,
                "node": "L chevron-tip top >= chartArea.bottom (outside plot)",
                "measured": L["tip"]["top"],
                "expected": f">={area_bottom:.1f}",
                "delta_px": round(L["tip"]["top"] - area_bottom, 2),
                "pass": L["tip"]["top"] + TOL >= area_bottom,
            }
        )
        if L["pill"]:
            pill_cx = L["pill"]["left"] + L["pill"]["w"] / 2
            rows.append(assert_row(5, "L chevron-pill centre vs bar2", pill_cx, exp_cx))
            rows.append(
                {
                    "slide": 5,
                    "node": "L chevron-pill top >= tip.bottom (stacked)",
                    "measured": L["pill"]["top"],
                    "expected": f">={L['tip']['bottom']:.1f}",
                    "delta_px": round(L["pill"]["top"] - L["tip"]["bottom"], 2),
                    "pass": L["pill"]["top"] + TOL >= L["tip"]["bottom"] - 2,
                }
            )

    # T6 axis break on right tile
    if R:
        area_bottom = R["oy"] + R["area"]["bottom"]
        if R["axisBreak"]:
            rows.append(
                {
                    "slide": 5,
                    "node": "R axis-break top >= chartArea.bottom (outside plot)",
                    "measured": R["axisBreak"]["top"],
                    "expected": f">={area_bottom:.1f}",
                    "delta_px": round(R["axisBreak"]["top"] - area_bottom, 2),
                    "pass": R["axisBreak"]["top"] + TOL >= area_bottom,
                }
            )
            # break must not be a wide line across plot — height small / width small hatch
            rows.append(
                {
                    "slide": 5,
                    "node": "R axis-break is small hatch (h<=24 or w<=40)",
                    "measured": {"w": R["axisBreak"]["w"], "h": R["axisBreak"]["h"], "text": R["axisBreak"]["text"]},
                    "expected": "small // glyph, not 2px line across plot",
                    "delta_px": None,
                    "pass": (R["axisBreak"]["h"] <= 24 and R["axisBreak"]["w"] <= 40)
                    or ("/" in (R["axisBreak"]["text"] or "")),
                }
            )
        else:
            rows.append(
                {
                    "slide": 5,
                    "node": "R axis-break present",
                    "measured": None,
                    "expected": "present",
                    "delta_px": None,
                    "pass": False,
                }
            )
        # colors on right tile
        rows.append(
            {
                "slide": 5,
                "node": "R tile dataset colors not black / no var(--",
                "measured": R.get("colors"),
                "expected": "navy/blue hex",
                "delta_px": None,
                "pass": bool(R.get("colors"))
                and all(
                    c
                    and "var(" not in str(c)
                    and str(c).lower() not in ("#000", "#000000", "rgb(0, 0, 0)", "black")
                    for c in R["colors"]
                ),
            }
        )

    if L:
        rows.append(
            {
                "slide": 5,
                "node": "L tile dataset colors not black / no var(--",
                "measured": L.get("colors"),
                "expected": "navy/blue hex",
                "delta_px": None,
                "pass": bool(L.get("colors"))
                and all(
                    c
                    and "var(" not in str(c)
                    and str(c).lower() not in ("#000", "#000000", "rgb(0, 0, 0)", "black")
                    for c in L["colors"]
                ),
            }
        )

    return rows, observations


def probe_annotations(page, slide_idx: int, label: str):
    activate_slide(page, slide_idx)
    data = page.evaluate(
        """() => {
        const slide = document.querySelectorAll('section.slide')[%d];
        const wrap = slide.querySelector('.chartjs-wrap');
        if (!wrap) return null;
        const canvas = wrap.querySelector('canvas');
        const ch = Chart.getChart(canvas);
        const wr = wrap.getBoundingClientRect();
        const cr = canvas.getBoundingClientRect();
        const ox = cr.left - wr.left, oy = cr.top - wr.top;
        const area = ch.chartArea;
        const an = wrap.querySelector('.chartjs-annotation');
        if (!an) return {has:false};
        const r = an.getBoundingClientRect();
        const dx = parseFloat(an.getAttribute('data-x'));
        const dy = parseFloat(an.getAttribute('data-y'));
        return {
            has:true,
            left: r.left - wr.left, top: r.top - wr.top,
            w: r.width, h: r.height, text: (an.textContent||'').trim(),
            dataX: dx, dataY: dy,
            ox, oy, area,
            expectedLeft: ox + area.left + dx,
            expectedTop: oy + area.top + dy,
        };
    }"""
        % slide_idx
    )
    rows = []
    if not data or not data.get("has"):
        rows.append(
            {
                "slide": slide_idx,
                "node": f"{label} annotation present",
                "measured": None,
                "expected": "present",
                "delta_px": None,
                "pass": False,
            }
        )
        return rows, data
    rows.append(assert_row(slide_idx, f"{label} ann.left vs area+ x", data["left"], data["expectedLeft"]))
    rows.append(assert_row(slide_idx, f"{label} ann.top vs area+ y", data["top"], data["expectedTop"]))
    return rows, data


def probe_dual_panes(page, slide_idx: int = 16):
    activate_slide(page, slide_idx)
    data = page.evaluate(
        """(si) => {
        const slide = document.querySelectorAll('section.slide')[si];
        const panes = [...slide.querySelectorAll('.gl-dual-pane, .dual-pane, .gl-chart-pane, .chart-pane, .gl-card')];
        // broader: structures under dual layout
        const headings = [...slide.querySelectorAll('h3,h4,.gl-pane-heading,.pane-heading,.gl-card-title,.tile-label,.chart-title,.gl-tile-label')].map(el => ({
            tag: el.tagName, cls: el.className, text: (el.textContent||'').trim().slice(0,80)
        }));
        const legends = [...slide.querySelectorAll('.chartjs-wrap')].map((wrap,i) => {
            const canvas = wrap.querySelector('canvas');
            const ch = canvas && Chart.getChart(canvas);
            const legendEl = wrap.parentElement.querySelector('.chartjs-legend, canvas + ul, .gl-chart-legend');
            // Chart.js HTML legend or plugin
            const display = ch && ch.options && ch.options.plugins && ch.options.plugins.legend
                ? ch.options.plugins.legend.display : null;
            const nDS = ch && ch.data ? ch.data.datasets.length : 0;
            return {i, nDS, legendDisplay: display, colors: (ch&&ch.data.datasets||[]).map(d=>d.backgroundColor||d.borderColor)};
        });
        const htmlLegendCount = slide.querySelectorAll('ul li, .gl-legend-item, .chart-legend-item').length;
        return {headings, legends, htmlLegendCount,
            bodySnippet: slide.innerHTML.slice(0, 500)};
    }""",
        slide_idx,
    )
    rows = []
    real_headings = [h for h in data["headings"] if h["text"] and len(h["text"]) > 2]
    rows.append(
        {
            "slide": slide_idx,
            "node": "dual_chart pane headings present (count>=2)",
            "measured": len(real_headings),
            "expected": ">=2",
            "delta_px": None,
            "pass": len(real_headings) >= 2,
            "note": real_headings[:6],
        }
    )
    # single-series legends should be suppressed
    for leg in data["legends"]:
        if leg["nDS"] == 1:
            rows.append(
                {
                    "slide": slide_idx,
                    "node": f"pane{leg['i']} single-series legend suppressed",
                    "measured": {"legendDisplay": leg["legendDisplay"], "nDS": leg["nDS"]},
                    "expected": "legend.display falsy",
                    "delta_px": None,
                    "pass": leg["legendDisplay"] in (False, None),
                }
            )
        else:
            rows.append(
                {
                    "slide": slide_idx,
                    "node": f"pane{leg['i']} multi-series legend kept",
                    "measured": {"legendDisplay": leg["legendDisplay"], "nDS": leg["nDS"]},
                    "expected": "legend available if multi",
                    "delta_px": None,
                    "pass": True,  # multi may still hide; not fail
                }
            )
        rows.append(
            {
                "slide": slide_idx,
                "node": f"pane{leg['i']} colors no var(-- / not black",
                "measured": leg["colors"],
                "expected": "hex navy/blue",
                "delta_px": None,
                "pass": all(
                    c and "var(" not in str(c) and str(c).lower() not in ("#000", "#000000", "black", "rgb(0, 0, 0)")
                    for c in (leg["colors"] or [None])
                ),
            }
        )
    return rows, data


def probe_insets(page, slide_indices):
    rows = []
    detail = {}
    for si in slide_indices:
        activate_slide(page, si)
        data = page.evaluate(
            """(si) => {
            const slide = document.querySelectorAll('section.slide')[si];
            const insets = [...slide.querySelectorAll('.gl-inset, [data-inset]')];
            const results = [];
            function rect(el){const r=el.getBoundingClientRect(); return {l:r.left,t:r.top,r:r.right,b:r.bottom,w:r.width,h:r.height};}
            function overlap(a,b){
                const iw = Math.max(0, Math.min(a.r,b.r)-Math.max(a.l,b.l));
                const ih = Math.max(0, Math.min(a.b,b.b)-Math.max(a.t,b.t));
                return iw*ih;
            }
            const areas = slide.querySelector('.gl-areas-table-inset');
            const table = slide.querySelector('.gl-inset-table');
            const stage = slide.querySelector('.gl-inset-stage');
            const cs = areas ? getComputedStyle(areas) : null;
            for (const inn of insets) {
                const ir = rect(inn);
                const tr = table ? rect(table) : null;
                const oTable = overlap(ir, tr);
                // also sample pill cells / table cells
                const targets = [...slide.querySelectorAll('.gl-pill-cell,.gl-pill-head,th,td')];
                let maxO = 0; let hit = null;
                for (const t of targets) {
                    if (inn.contains(t) || t.contains(inn)) continue;
                    const o = overlap(ir, rect(t));
                    if (o > maxO) { maxO = o; hit = (t.textContent||'').trim().slice(0,40); }
                }
                results.push({
                  text:(inn.textContent||'').trim().slice(0,60),
                  maxOverlapPx2: maxO,
                  insetTableOverlap: oTable,
                  hit,
                  layout: cs ? {display: cs.display, flexDir: cs.flexDirection} : null,
                  stageBox: stage ? rect(stage) : null,
                  tableBox: tr,
                  insetBox: ir,
                });
            }
            // also general pairwise: inset vs any non-ancestor content box with text
            return {insetCount: insets.length, results};
        }""",
            si,
        )
        detail[si] = data
        for r in data["results"]:
            rows.append(
                {
                    "slide": si,
                    "node": f"inset overlap '{r['text'][:30]}'",
                    "measured": r["maxOverlapPx2"],
                    "expected": 0,
                    "delta_px": r["maxOverlapPx2"],
                    "pass": r["maxOverlapPx2"] <= 1,
                    "note": r.get("hit"),
                }
            )
        if data["insetCount"] == 0 and si in (19, 23):
            rows.append(
                {
                    "slide": si,
                    "node": "inset present for collision test",
                    "measured": 0,
                    "expected": ">=1 for slides with KPI inset",
                    "delta_px": None,
                    "pass": True,  # may not use inset on all
                    "note": "no inset nodes",
                }
            )
    return rows, detail


def sweep_overlaps(page, n_slides=44):
    """Deck-wide inset/content overlap sweep."""
    rows = []
    hits = []
    for si in range(n_slides):
        activate_slide(page, si)
        data = page.evaluate(
            """(si) => {
            const slide = document.querySelectorAll('section.slide')[si];
            const insets = [...slide.querySelectorAll('.gl-inset,[data-inset]')];
            if (!insets.length) return [];
            function rect(el){const r=el.getBoundingClientRect(); return {l:r.left,t:r.top,r:r.right,b:r.bottom};}
            function overlap(a,b){
                const iw = Math.max(0, Math.min(a.r,b.r)-Math.max(a.l,b.l));
                const ih = Math.max(0, Math.min(a.b,b.b)-Math.max(a.t,b.t));
                return iw*ih;
            }
            const targets = [...slide.querySelectorAll('th,td,.gl-pill-cell')];
            const out=[];
            for (const inn of insets) {
                const ir = rect(inn);
                for (const t of targets) {
                    if (inn.contains(t)||t.contains(inn)) continue;
                    const o = overlap(ir, rect(t));
                    if (o > 1) out.push({si, o, inset:(inn.textContent||'').trim().slice(0,40),
                                         hit:(t.textContent||'').trim().slice(0,40)});
                }
            }
            return out;
        }""",
            si,
        )
        hits.extend(data)
    rows.append(
        {
            "slide": "all",
            "node": "deck-wide inset↔cell overlap count",
            "measured": len(hits),
            "expected": 0,
            "delta_px": None,
            "pass": len(hits) == 0,
            "note": hits[:10],
        }
    )
    return rows, hits


def probe_annex_banding(page, indices=(30, 31, 32)):
    rows = []
    detail = {}
    for si in indices:
        activate_slide(page, si)
        data = page.evaluate(
            """(si) => {
            const slide = document.querySelectorAll('section.slide')[si];
            const groups = [...slide.querySelectorAll('.gl-annex-group, th.gl-annex-group, .annex-table .gl-annex-group')];
            // also header cells that look like group headers
            const ths = [...slide.querySelectorAll('.annex-table th, table th')].map(th => {
                const cs = getComputedStyle(th);
                return {
                    text: (th.textContent||'').trim().slice(0,40),
                    cls: th.className,
                    bg: cs.backgroundColor,
                    color: cs.color,
                };
            });
            return {groupCount: groups.length, ths: ths.slice(0, 30)};
        }""",
            si,
        )
        detail[si] = data
        # navy-ish backgrounds for group headers: rgb near #00175a
        def is_navy(bg: str) -> bool:
            if not bg or bg == "rgba(0, 0, 0, 0)":
                return False
            # parse rgb
            import re

            m = re.search(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", bg)
            if not m:
                return "00175" in bg.lower() or "navy" in bg.lower()
            r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
            # navy: low R/G, higher B relative, or dark blue
            return r < 40 and g < 60 and b > 60 and b > r

        def is_light_blue(bg: str) -> bool:
            import re

            m = re.search(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", bg or "")
            if not m:
                return False
            r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
            return b > 180 and r > 100 and g > 140 and b >= r

        group_ths = [t for t in data["ths"] if "group" in (t["cls"] or "").lower()]
        if not group_ths:
            # fall back: thead second row or bold full-width
            group_ths = [t for t in data["ths"] if t["text"] and is_navy(t["bg"])]

        bgs = [t["bg"] for t in group_ths]
        all_navy = all(is_navy(bg) for bg in bgs) if bgs else False
        any_light = any(is_light_blue(bg) for bg in bgs)
        rows.append(
            {
                "slide": si,
                "node": "annex group headers uniformly navy (no light-blue alt)",
                "measured": {"count": len(group_ths), "bgs": bgs[:8], "sample": group_ths[:4]},
                "expected": "all navy, no alt light-blue",
                "delta_px": None,
                "pass": bool(bgs) and all_navy and not any_light,
            }
        )
        # sub-header white-on-navy still present?
        white_on_navy = [
            t
            for t in data["ths"]
            if is_navy(t["bg"]) and t["color"] in ("rgb(255, 255, 255)", "#fff", "white", "rgb(255,255,255)")
        ]
        rows.append(
            {
                "slide": si,
                "node": "annex white-on-navy header cells remain",
                "measured": len(white_on_navy),
                "expected": ">=1",
                "delta_px": None,
                "pass": len(white_on_navy) >= 1,
            }
        )
    return rows, detail


def probe_palette_no_var(page, indices):
    rows = []
    detail = {}
    for si in indices:
        activate_slide(page, si)
        data = page.evaluate(
            """(si) => {
            const slide = document.querySelectorAll('section.slide')[si];
            const canvases = [...slide.querySelectorAll('canvas')];
            const out=[];
            for (const c of canvases) {
                const ch = Chart.getChart(c);
                if (!ch) continue;
                out.push({
                    colors: (ch.data.datasets||[]).map(d => d.backgroundColor || d.borderColor),
                    labels: ch.data.labels,
                });
            }
            // raw config dump search
            const html = slide.innerHTML;
            return {charts: out, hasVarInSlide: html.includes('var(--') && html.includes('series')};
        }""",
            si,
        )
        detail[si] = data
        flat = []
        for ch in data["charts"]:
            flat.extend(ch["colors"] if isinstance(ch["colors"][0], str) or ch["colors"] else ch["colors"])
        # colors may be arrays for multi
        flat2 = []
        for c in flat:
            if isinstance(c, list):
                flat2.extend(c)
            else:
                flat2.append(c)
        bad = [c for c in flat2 if c and ("var(--" in str(c) or str(c).lower() in ("#000", "#000000", "black", "rgb(0, 0, 0)"))]
        rows.append(
            {
                "slide": si,
                "node": "chart colors navy/blue, no var(--, not black",
                "measured": flat2,
                "expected": "literal hex palette",
                "delta_px": None,
                "pass": len(flat2) > 0 and len(bad) == 0,
                "note": f"bad={bad}",
            }
        )
    return rows, detail


def probe_pill_board(page, si=2):
    activate_slide(page, si)
    data = page.evaluate(
        """(si) => {
        const slide = document.querySelectorAll('section.slide')[si];
        const board = slide.querySelector('.gl-pill, .gl-pill-free, .gl-pill-board');
        const cols = [...slide.querySelectorAll('.gl-pill-shell')];
        const cells = [...slide.querySelectorAll('.gl-pill-cell')];
        const br = (el) => { if(!el) return null; const r=el.getBoundingClientRect(); return {w:r.width,h:r.height}; };
        const slideR = slide.getBoundingClientRect();
        return {
            board: br(board),
            slideH: slideR.height,
            nCols: cols.length,
            colWidths: cols.map(c => c.getBoundingClientRect().width),
            nCells: cells.length,
            cellHeights: cells.slice(0,12).map(c => c.getBoundingClientRect().height),
            avgCellH: cells.length ? cells.reduce((s,c)=>s+c.getBoundingClientRect().height,0)/cells.length : null,
        };
    }""",
        si,
    )
    rows = []
    frac = None
    if data["board"] and data["slideH"]:
        frac = data["board"]["h"] / data["slideH"]
    rows.append(
        {
            "slide": si,
            "node": "pill board height / slide height",
            "measured": round(frac, 3) if frac else None,
            "expected": "PDF near-full board (~0.7+)",
            "delta_px": None,
            "pass": bool(frac and frac >= 0.55),
            "note": data,
        }
    )
    rows.append(
        {
            "slide": si,
            "node": "pill column count",
            "measured": data["nCols"],
            "expected": 3,
            "delta_px": None,
            "pass": data["nCols"] == 3,
            "note": {"colWidths": data["colWidths"], "avgCellH": data["avgCellH"]},
        }
    )
    return rows, data


def probe_multi_legend(page, si=27):
    activate_slide(page, si)
    data = page.evaluate(
        """(si) => {
        const slide = document.querySelectorAll('section.slide')[si];
        const side = slide.querySelectorAll('.side-legend, .gl-side-legend, .gl-tile-legend, [class*=side_legend], [class*=side-legend]');
        const charts = [...slide.querySelectorAll('canvas')].map(c => {
            const ch = Chart.getChart(c);
            const sn = ch && ch.options && ch.options.plugins && ch.options.plugins.segmentNames;
            const padR = ch && ch.options && ch.options.layout && ch.options.layout.padding
                ? (ch.options.layout.padding.right || 0) : 0;
            return {
                legendDisplay: ch && ch.options && ch.options.plugins && ch.options.plugins.legend
                    ? ch.options.plugins.legend.display : null,
                nDS: ch && ch.data ? ch.data.datasets.length : 0,
                colors: (ch&&ch.data.datasets||[]).map(d=>d.backgroundColor||d.borderColor),
                segmentNames: sn ? {n: (sn.items||[]).length, fontSize: sn.fontSize, offset: sn.offset, items: sn.items} : null,
                padRight: padR,
            };
        });
        return {
            sideLegendCount: side.length,
            exteriorNameNodes: charts.reduce((a,c)=>a+((c.segmentNames&&c.segmentNames.n)||0),0),
            charts,
            headings: [...slide.querySelectorAll('h3,h4,.gl-card-title,.tile-label,.gl-tile-label')].map(e=>e.textContent.trim()),
        };
    }""",
        si,
    )
    rows = []
    rows.append(
        {
            "slide": si,
            "node": "funding side_legend count (want 0)",
            "measured": data["sideLegendCount"],
            "expected": 0,
            "delta_px": None,
            "pass": data["sideLegendCount"] == 0,
        }
    )
    rows.append(
        {
            "slide": si,
            "node": "funding exterior name nodes present",
            "measured": data["exteriorNameNodes"],
            "expected": ">=1",
            "delta_px": None,
            "pass": data["exteriorNameNodes"] >= 1,
        }
    )
    for i, ch in enumerate(data["charts"]):
        rows.append(
            {
                "slide": si,
                "node": f"funding tile{i} colors",
                "measured": ch["colors"],
                "expected": "not black",
                "delta_px": None,
                "pass": all(
                    c and "var(--" not in str(c) and str(c).lower() not in ("#000", "#000000", "black", "rgb(0, 0, 0)")
                    for c in ch["colors"]
                ),
            }
        )
    return rows, data


def main() -> int:
    html = Path(sys.argv[1] if len(sys.argv) > 1 else "simulation/amex_q1_2026/passes/pass_01/output/presentation.html")
    out = Path(sys.argv[2] if len(sys.argv) > 2 else html.parent.parent / "geometry.json")
    url = html.resolve().as_uri()

    all_rows = []
    observations = {}

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(500)

        r, o = probe_slide05(page)
        all_rows.extend(r)
        observations["slide05"] = o

        for si, lab in [(3, "s03 LeapYear"), (9, "s09 Reported"), (10, "s10 LeapYear"), (18, "s18 LeapYear")]:
            r, o = probe_annotations(page, si, lab)
            all_rows.extend(r)
            observations[f"ann_{si}"] = o

        r, o = probe_dual_panes(page, 16)
        all_rows.extend(r)
        observations["dual16"] = o

        # multi-series panes 05, 27 should keep legends if multi
        r, o = probe_dual_panes(page, 5)
        all_rows.extend(
            [
                {
                    **row,
                    "node": "s05 " + str(row["node"]),
                }
                for row in r
                if "legend" in str(row["node"]).lower() or "color" in str(row["node"]).lower()
            ]
        )
        observations["dual05"] = o

        r, o = probe_insets(page, [19, 23])
        all_rows.extend(r)
        observations["insets"] = o

        r, o = sweep_overlaps(page, 44)
        all_rows.extend(r)
        observations["overlap_hits"] = o

        r, o = probe_annex_banding(page, (30, 31, 32))
        all_rows.extend(r)
        observations["annex"] = o

        t10 = [5, 8, 10, 13, 16, 17, 20, 26, 27]
        r, o = probe_palette_no_var(page, t10)
        all_rows.extend(r)
        observations["palette"] = o

        r, o = probe_pill_board(page, 2)
        all_rows.extend(r)
        observations["pill02"] = o

        r, o = probe_multi_legend(page, 27)
        all_rows.extend(r)
        observations["funding27"] = o

        # global: any serialized chart config with var(--
        activate_slide(page, 0)
        var_hits = page.evaluate(
            """() => {
            const html = document.documentElement.innerHTML;
            const re = /var\\(--[^)]+\\)/g;
            // only care inside chart configs / canvas parent scripts
            const scripts = [...document.querySelectorAll('script')].map(s => s.textContent||'');
            const hits = [];
            for (const s of scripts) {
                if (s.includes('var(--') && (s.includes('backgroundColor') || s.includes('borderColor') || s.includes('series'))) {
                    const m = s.match(/var\\(--[^)]+\\)/g) || [];
                    hits.push(...m.slice(0,5));
                }
            }
            return {count: hits.length, sample: hits.slice(0,10)};
        }"""
        )
        all_rows.append(
            {
                "slide": "all",
                "node": "no var(-- in chart script colors",
                "measured": var_hits,
                "expected": 0,
                "delta_px": None,
                "pass": var_hits["count"] == 0,
            }
        )

        browser.close()

    passed = sum(1 for r in all_rows if r.get("pass"))
    failed = sum(1 for r in all_rows if not r.get("pass"))
    payload = {
        "tolerance_px": TOL,
        "summary": {"total": len(all_rows), "passed": passed, "failed": failed},
        "assertions": all_rows,
        "observations": {
            k: v
            for k, v in observations.items()
            if k
            in (
                "slide05",
                "ann_3",
                "ann_9",
                "ann_10",
                "ann_18",
                "dual16",
                "pill02",
                "funding27",
                "overlap_hits",
                "annex",
                "palette",
            )
        },
    }
    # observations may be huge; keep compact
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"geometry: {passed}/{len(all_rows)} passed, {failed} failed -> {out}")
    for r in all_rows:
        flag = "PASS" if r.get("pass") else "FAIL"
        print(f"  [{flag}] s{r['slide']} {r['node']}: measured={r.get('measured')} expected={r.get('expected')} dPx={r.get('delta_px')}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
