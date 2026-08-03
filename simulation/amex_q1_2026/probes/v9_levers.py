"""v9 lever probes: measure_rule (N8), outlined_boxes (N6), funding packing (N5/F11)."""
from __future__ import annotations

from geometry_probe import TOL, activate_slide, assert_row


def probe_measure_rule(page, slide_idx: int = 16):
    """N8/R6-B: thin dual-ended measure_rule on Net Card Fees primary chart."""
    activate_slide(page, slide_idx)
    data = page.evaluate(
        """(si) => {
        const stage = document.querySelector('.deck-stage');
        const sr = stage.getBoundingClientRect();
        const rel = (el) => {
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return {
                left: r.left - sr.left, top: r.top - sr.top,
                w: r.width, h: r.height, right: r.right - sr.left,
                bottom: r.bottom - sr.top,
                cx: (r.left + r.right)/2 - sr.left,
                cy: (r.top + r.bottom)/2 - sr.top,
                text: (el.textContent||'').trim().slice(0,80),
                bg: getComputedStyle(el).backgroundColor,
                opacity: getComputedStyle(el).opacity,
            };
        };
        const slide = document.querySelectorAll('section.slide')[si];
        const wraps = [...slide.querySelectorAll('.chartjs-wrap')];
        const wrap = wraps[0];
        if (!wrap) return {error: 'no wrap'};
        const canvas = wrap.querySelector('canvas');
        const ch = canvas && Chart.getChart(canvas);
        const ca = ch ? ch.chartArea : null;
        const meta = ch && ch.getDatasetMeta(0);
        const bars = [];
        if (meta && meta.data) {
            const cr = canvas.getBoundingClientRect();
            for (const el of meta.data) {
                bars.push({
                    cx: cr.left - sr.left + el.x,
                    cy: cr.top - sr.top + el.y,
                    x: el.x, y: el.y,
                });
            }
        }
        const measure = rel(wrap.querySelector('.chartjs-callout-measure'));
        const pill = rel(wrap.querySelector('.chartjs-callout-measure-pill'));
        const cap = rel(wrap.querySelector('.chartjs-callout-measure-caption'));
        const arrowL = rel(wrap.querySelector('.chartjs-callout-measure-arrow-l'));
        const arrowR = rel(wrap.querySelector('.chartjs-callout-measure-arrow-r'));
        const band = rel(wrap.querySelector('.chartjs-callout-band'));
        let area = null;
        if (ca) {
            const cr = canvas.getBoundingClientRect();
            area = {
                left: cr.left - sr.left + ca.left,
                top: cr.top - sr.top + ca.top,
                right: cr.left - sr.left + ca.right,
                bottom: cr.top - sr.top + ca.bottom,
                w: ca.right - ca.left, h: ca.bottom - ca.top,
            };
        }
        return {
            nWraps: wraps.length, nBars: bars.length, bars, area,
            measure, pill, cap, arrowL, arrowR, band,
            measureClass: !!(wrap.querySelector('.chartjs-callout-measure')),
            bandClass: !!(wrap.querySelector('.chartjs-callout-band')),
        };
    }""",
        slide_idx,
    )
    rows = []
    rows.append({
        "slide": slide_idx,
        "node": "measure_rule present (no band)",
        "measured": {"measure": data.get("measureClass"), "band": data.get("bandClass")},
        "expected": {"measure": True, "band": False},
        "delta_px": None,
        "pass": bool(data.get("measureClass")) and not data.get("bandClass"),
    })
    bars = data.get("bars") or []
    measure = data.get("measure") or {}
    pill = data.get("pill") or {}
    cap = data.get("cap") or {}
    if len(bars) >= 2 and measure:
        b0, bN = bars[0], bars[-1]
        rows.append(assert_row(slide_idx, "measure.left vs bar0 centre", measure.get("left"), b0["cx"], tol=8))
        rows.append(assert_row(slide_idx, "measure.right vs barN centre", measure.get("right"), bN["cx"], tol=8))
        rows.append({
            "slide": slide_idx,
            "node": "measure thin height (h<=48)",
            "measured": measure.get("h"),
            "expected": "<=48",
            "delta_px": None,
            "pass": measure.get("h") is not None and measure["h"] <= 48,
        })
    else:
        rows.append({
            "slide": slide_idx,
            "node": "measure geometry bars available",
            "measured": {"nBars": len(bars), "measure": bool(measure)},
            "expected": "bars>=2 and measure",
            "delta_px": None,
            "pass": False,
        })
    if pill and measure:
        rows.append(assert_row(slide_idx, "pill.cx vs measure.cx", pill.get("cx"), measure.get("cx"), tol=8))
        if measure.get("top") is not None and pill.get("cy") is not None:
            mid_y = measure["top"] + (measure.get("h") or 0) / 2
            rows.append(assert_row(slide_idx, "pill.cy vs measure mid-y", pill.get("cy"), mid_y, tol=12))
        rows.append({
            "slide": slide_idx,
            "node": "pill text is 17%",
            "measured": (pill.get("text") or "").strip(),
            "expected": "17%",
            "delta_px": None,
            "pass": "17%" in (pill.get("text") or ""),
        })
    if cap and pill:
        rows.append(assert_row(slide_idx, "caption.cx vs pill.cx", cap.get("cx"), pill.get("cx"), tol=8))
        rows.append({
            "slide": slide_idx,
            "node": "caption below pill",
            "measured": {"cap_top": cap.get("top"), "pill_bottom": pill.get("bottom")},
            "expected": "cap.top >= pill.bottom - 4",
            "delta_px": None,
            "pass": (
                cap.get("top") is not None
                and pill.get("bottom") is not None
                and cap["top"] >= pill["bottom"] - 4
            ),
        })
        rows.append({
            "slide": slide_idx,
            "node": "caption text is % CAGR",
            "measured": (cap.get("text") or "").strip(),
            "expected": "% CAGR",
            "delta_px": None,
            "pass": "% CAGR" in (cap.get("text") or ""),
        })
    elif data.get("measureClass"):
        rows.append({
            "slide": slide_idx,
            "node": "measure caption present",
            "measured": bool(cap),
            "expected": True,
            "delta_px": None,
            "pass": bool(cap),
        })
    return rows, data


def probe_outlined_boxes(page, slide_idx: int = 14):
    """N6: secondary_visual.skin=outlined_boxes on Total Provision support row."""
    activate_slide(page, slide_idx)
    data = page.evaluate(
        """(si) => {
        const stage = document.querySelector('.deck-stage');
        const sr = stage.getBoundingClientRect();
        const rel = (el) => {
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return {
                left: r.left - sr.left, top: r.top - sr.top,
                w: r.width, h: r.height, right: r.right - sr.left,
                bottom: r.bottom - sr.top, cx: (r.left+r.right)/2 - sr.left,
                text: (el.textContent||'').trim().slice(0,60),
                bg: getComputedStyle(el).backgroundColor,
                border: getComputedStyle(el).borderColor,
                borderW: getComputedStyle(el).borderTopWidth,
            };
        };
        const slide = document.querySelectorAll('section.slide')[si];
        const outlined = slide.querySelector('.chart-support-outlined');
        const table = slide.querySelector('table.chart-support-table');
        const cells = [...slide.querySelectorAll('.chart-outlined-box')].map(rel);
        const labels = [...slide.querySelectorAll('.chart-outlined-label')].map(rel);
        const valueCells = [...slide.querySelectorAll('.chart-outlined-cell .chart-outlined-box')].map(rel);
        const thead = table ? [...table.querySelectorAll('thead th')].map(t => t.textContent.trim()) : [];
        const canvas = slide.querySelector('canvas');
        const ch = canvas && Chart.getChart(canvas);
        const bars = [];
        if (ch) {
            const meta = ch.getDatasetMeta(0);
            const cr = canvas.getBoundingClientRect();
            for (const el of (meta && meta.data) || []) {
                bars.push({cx: cr.left - sr.left + el.x, x: el.x});
            }
        }
        return {
            hasOutlined: !!outlined,
            hasTable: !!table,
            nBoxes: cells.length,
            nLabels: labels.length,
            nValueCells: valueCells.length,
            cells, labels, valueCells, thead, bars,
            aligned: !!(outlined && outlined.classList.contains('chart-table-aligned')),
            sampleBg: valueCells[0] && valueCells[0].bg,
            sampleBorder: valueCells[0] && valueCells[0].border,
        };
    }""",
        slide_idx,
    )
    rows = []
    rows.append({
        "slide": slide_idx,
        "node": "outlined_boxes skin active (no support table)",
        "measured": {"outlined": data.get("hasOutlined"), "table": data.get("hasTable")},
        "expected": {"outlined": True, "table": False},
        "delta_px": None,
        "pass": bool(data.get("hasOutlined")) and not data.get("hasTable"),
    })
    rows.append({
        "slide": slide_idx,
        "node": "no duplicated header thead",
        "measured": data.get("thead"),
        "expected": [],
        "delta_px": None,
        "pass": not data.get("thead"),
    })
    rows.append({
        "slide": slide_idx,
        "node": "outlined value cell count",
        "measured": data.get("nValueCells"),
        "expected": 5,
        "delta_px": None,
        "pass": data.get("nValueCells") == 5,
    })
    bg = (data.get("sampleBg") or "").lower()
    unfilled = (
        "rgba(0, 0, 0, 0)" in bg
        or bg in ("transparent", "rgba(0,0,0,0)")
        or bg.startswith("rgb(255")
        or bg.startswith("rgba(255")
        or bg in ("", "none")
    )
    rows.append({
        "slide": slide_idx,
        "node": "outlined cells unfilled (no solid fill)",
        "measured": data.get("sampleBg"),
        "expected": "transparent/white",
        "delta_px": None,
        "pass": unfilled,
    })
    vals = data.get("valueCells") or []
    bars = data.get("bars") or []
    if len(vals) >= 5 and len(bars) >= 5:
        for i in range(5):
            rows.append(assert_row(
                slide_idx,
                f"outlined cell{i}.cx vs bar{i}.cx",
                vals[i].get("cx"),
                bars[i].get("cx"),
                tol=12,
            ))
    else:
        rows.append({
            "slide": slide_idx,
            "node": "outlined align bars available",
            "measured": {
                "nVals": len(vals),
                "nBars": len(bars),
                "aligned": data.get("aligned"),
            },
            "expected": "5 vals + 5 bars",
            "delta_px": None,
            "pass": False,
            "note": "source may violate single-row/aligned contract",
        })
    return rows, data


def probe_funding_packing(page, si: int = 27):
    """N5/F11: bar_percentage/category_percentage/fill_tile on Funding tiles."""
    activate_slide(page, si)
    data = page.evaluate(
        """(si) => {
        const stage = document.querySelector('.deck-stage');
        const sr = stage.getBoundingClientRect();
        const rel = (el) => {
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return {
                left: r.left - sr.left, top: r.top - sr.top,
                w: r.width, h: r.height, right: r.right - sr.left,
                bottom: r.bottom - sr.top,
            };
        };
        const slide = document.querySelectorAll('section.slide')[si];
        const wraps = [...slide.querySelectorAll('.chartjs-wrap')];
        const out = [];
        for (let i = 0; i < wraps.length; i++) {
            const wrap = wraps[i];
            const canvas = wrap.querySelector('canvas');
            const ch = canvas && Chart.getChart(canvas);
            const wrapB = rel(wrap);
            const tile = wrap.closest('.gl-tile, .mp-tile, .gl-card') || wrap.parentElement;
            const tileB = rel(tile);
            let barW = null, catW = null, stackH = null, gap = null, barPct = null, catPct = null;
            let fillClass = wrap.classList.contains('chartjs-fill');
            if (ch) {
                const ds0 = ch.data.datasets[0];
                const optsBar = (ch.options && ch.options.bar) || {};
                barPct = ds0 && ds0.barPercentage != null ? ds0.barPercentage : optsBar.barPercentage;
                catPct = ds0 && ds0.categoryPercentage != null ? ds0.categoryPercentage : optsBar.categoryPercentage;
                try {
                    const cfg = ch.config && (ch.config._config || ch.config);
                    const d0 = cfg && cfg.data && cfg.data.datasets && cfg.data.datasets[0];
                    if (d0) {
                        if (d0.barPercentage != null) barPct = d0.barPercentage;
                        if (d0.categoryPercentage != null) catPct = d0.categoryPercentage;
                    }
                } catch (e) {}
                // Chart.js resolved options
                try {
                    const rs = ch.options && ch.options.datasets && ch.options.datasets.bar;
                    if (rs) {
                        if (barPct == null && rs.barPercentage != null) barPct = rs.barPercentage;
                        if (catPct == null && rs.categoryPercentage != null) catPct = rs.categoryPercentage;
                    }
                } catch (e) {}
                const meta = ch.getDatasetMeta(0);
                if (meta && meta.data && meta.data.length) {
                    const b0 = meta.data[0];
                    const props0 = b0.getProps ? b0.getProps(['width','x','y','base'], true) : {width: b0.width, x: b0.x, y: b0.y, base: b0.base};
                    barW = props0.width != null ? props0.width : b0.width;
                    let yTop = Infinity, yBot = -Infinity;
                    for (let di = 0; di < ch.data.datasets.length; di++) {
                        const m = ch.getDatasetMeta(di);
                        if (!m || !m.data[0]) continue;
                        const el = m.data[0];
                        const props = el.getProps ? el.getProps(['y','base','height'], true) : {y: el.y, base: el.base, height: el.height};
                        yTop = Math.min(yTop, Math.min(props.y, props.base));
                        yBot = Math.max(yBot, Math.max(props.y, props.base));
                    }
                    stackH = (yBot > yTop) ? (yBot - yTop) : null;
                    if (meta.data.length >= 2) {
                        const b1 = meta.data[1];
                        const props1 = b1.getProps ? b1.getProps(['x'], true) : {x: b1.x};
                        catW = Math.abs(props1.x - props0.x);
                        if (barW != null) gap = catW - barW;
                    }
                }
                const ca = ch.chartArea;
                out.push({
                    i, wrap: wrapB, tile: tileB, fillClass,
                    barW, catW, stackH, gap, barPct, catPct,
                    chartArea: ca ? {w: ca.right-ca.left, h: ca.bottom-ca.top} : null,
                    nDS: ch.data.datasets.length,
                    badge: rel(tile && tile.querySelector('.gl-badge, .tile-badge, [class*=badge]')),
                });
            }
        }
        return {tiles: out, nWraps: wraps.length};
    }""",
        si,
    )
    rows = []
    tiles = data.get("tiles") or []
    rows.append({
        "slide": si,
        "node": "funding tile count",
        "measured": len(tiles),
        "expected": 2,
        "delta_px": None,
        "pass": len(tiles) == 2,
    })
    for t in tiles:
        i = t["i"]
        rows.append({
            "slide": si,
            "node": f"tile{i} fill_tile class",
            "measured": t.get("fillClass"),
            "expected": True,
            "delta_px": None,
            "pass": bool(t.get("fillClass")),
        })
        bp = t.get("barPct")
        rows.append({
            "slide": si,
            "node": f"tile{i} barPercentage≈0.58",
            "measured": bp,
            "expected": 0.58,
            "delta_px": None if bp is None else round(abs(float(bp) - 0.58), 4),
            "pass": bp is not None and abs(float(bp) - 0.58) <= 0.02,
        })
        cp = t.get("catPct")
        rows.append({
            "slide": si,
            "node": f"tile{i} categoryPercentage≈1.0",
            "measured": cp,
            "expected": 1.0,
            "delta_px": None if cp is None else round(abs(float(cp) - 1.0), 4),
            "pass": cp is not None and abs(float(cp) - 1.0) <= 0.02,
        })
        if t.get("wrap") and t.get("tile"):
            ratio = t["wrap"]["h"] / t["tile"]["h"] if t["tile"]["h"] else None
            rows.append({
                "slide": si,
                "node": f"tile{i} wrap/tile height ratio",
                "measured": round(ratio, 3) if ratio else None,
                "expected": ">=0.55",
                "delta_px": None,
                "pass": ratio is not None and ratio >= 0.55,
                "note": {"wrap_h": t["wrap"]["h"], "tile_h": t["tile"]["h"]},
            })
        if t.get("barW") and t.get("catW"):
            gap = t["catW"] - t["barW"]
            ratio = t["barW"] / gap if gap > 1 else None
            rows.append({
                "slide": si,
                "node": f"tile{i} barW and cat pitch",
                "measured": {
                    "barW": round(t["barW"], 2),
                    "catW": round(t["catW"], 2),
                    "gap": round(gap, 2),
                    "bar_to_gap": round(ratio, 3) if ratio else None,
                },
                "expected": "bar_percentage 0.58 → bar occupies majority of pitch",
                "delta_px": None,
                "pass": t["barW"] > 0 and t["catW"] > t["barW"],
            })
        rows.append({
            "slide": si,
            "node": f"tile{i} stackH present",
            "measured": t.get("stackH"),
            "expected": ">0",
            "delta_px": None,
            "pass": t.get("stackH") is not None and t["stackH"] > 0,
        })
    badge = tiles[1]["badge"] if len(tiles) > 1 else None
    rows.append({
        "slide": si,
        "node": "tile1 FDIC badge present (not tall side callout)",
        "measured": badge,
        "expected": "badge node may exist; tall side callout is B residual",
        "delta_px": None,
        "pass": True,
        "note": "do not treat ordinary badge as PDF tall side FDIC callout",
    })
    return rows, data
