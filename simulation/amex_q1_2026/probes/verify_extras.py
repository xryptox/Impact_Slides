"""One-shot verify probes for N9/R2/N10/R4/F4+/R6-A/R6-C/F5 (v9 pass_01)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def activate(page, i: int) -> None:
    page.evaluate(
        """(i) => {
        document.querySelectorAll('section.slide').forEach(s => s.classList.remove('active'));
        const ss = document.querySelectorAll('section.slide');
        if (ss[i]) ss[i].classList.add('active');
    }""",
        i,
    )
    page.wait_for_timeout(1100)


def main() -> int:
    html = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else "simulation/amex_q1_2026/passes/pass_01/output/presentation.html"
    )
    dest = Path(
        sys.argv[2]
        if len(sys.argv) > 2
        else html.parent.parent / "verify_extras.json"
    )
    url = html.resolve().as_uri()
    out: dict = {}

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(400)

        # N9: grouped-bar $ labels on Net Card Fees primary
        activate(page, 16)
        out["N9_s16"] = page.evaluate(
            """() => {
            const slide = document.querySelectorAll('section.slide')[16];
            const wraps = [...slide.querySelectorAll('.chartjs-wrap')];
            return wraps.map((w, i) => {
                const c = w.querySelector('canvas');
                const ch = c && Chart.getChart(c);
                if (!ch) return null;
                const opts = ch.options || {};
                const dl = opts.plugins && opts.plugins.datalabels;
                const domLabels = [...w.querySelectorAll(
                    '.chartjs-datalabel, .bar-label, [class*=point-label], [class*=datalabel]'
                )].map(e => e.textContent.trim());
                return {
                    i,
                    nDS: ch.data.datasets.length,
                    type: ch.config.type,
                    datalabels: dl ? {display: dl.display} : null,
                    domLabels: domLabels.slice(0, 12),
                    sampleValues: (ch.data.datasets[0] && ch.data.datasets[0].data || []).slice(0, 3),
                    // inspect serialized script near canvas for $ prefix formatter
                };
            });
        }"""
        )
        # Also scrape script text for formatter / unit prefix on this slide
        out["N9_s16_script"] = page.evaluate(
            """() => {
            const slide = document.querySelectorAll('section.slide')[16];
            const scripts = [...slide.querySelectorAll('script')].map(s => s.textContent || '');
            const hits = [];
            for (const s of scripts) {
                if (s.includes('formatter') || s.includes('y_axis_unit') || s.includes("'$'") || s.includes('prefix')) {
                    hits.push(s.slice(0, 400));
                }
            }
            // global scripts that reference this canvas id
            const all = [...document.querySelectorAll('script')].map(s => s.textContent || '');
            let dollarFmt = false;
            let sample = '';
            for (const s of all) {
                if (s.includes('$') && (s.includes('datalabel') || s.includes('formatter') || s.includes('pointLabel'))) {
                    dollarFmt = true;
                    sample = s.match(/.{0,40}\\$.{0,40}/)?.[0] || s.slice(0, 120);
                    break;
                }
            }
            return {slideScriptHits: hits.length, dollarFmt, sample};
        }"""
        )

        # R2 line-style elbow on s05
        activate(page, 5)
        out["R2_s05"] = page.evaluate(
            """() => {
            const slide = document.querySelectorAll('section.slide')[5];
            const elbows = [...slide.querySelectorAll('.chartjs-callout-elbow')].map(e => ({
                cls: e.className,
                w: e.getBoundingClientRect().width,
                h: e.getBoundingClientRect().height,
                hasLine: e.className.includes('line'),
            }));
            const stems = slide.querySelectorAll('.chartjs-callout-elbow-stem').length;
            return {elbows, stems, nElbow: elbows.length};
        }"""
        )

        # N10 dual_chart two framed cards
        activate(page, 16)
        out["N10_s16"] = page.evaluate(
            """() => {
            const slide = document.querySelectorAll('section.slide')[16];
            const panes = [...slide.querySelectorAll(
                '.gl-dual-pane, .dual-pane, .gl-chart-pane, .chart-pane'
            )].map(e => ({
                cls: e.className.slice(0, 100),
                w: Math.round(e.getBoundingClientRect().width),
                h: Math.round(e.getBoundingClientRect().height),
                border: getComputedStyle(e).border,
                radius: getComputedStyle(e).borderRadius,
                bg: getComputedStyle(e).backgroundColor,
            }));
            return {nPanes: panes.length, panes, nCanvas: slide.querySelectorAll('canvas').length};
        }"""
        )

        # R4 dual-metric hero s11
        activate(page, 11)
        out["R4_s11"] = page.evaluate(
            """() => {
            const slide = document.querySelectorAll('section.slide')[11];
            const cards = [...slide.querySelectorAll('.gl-card')].map(e => ({
                cls: e.className.slice(0, 80),
                w: Math.round(e.getBoundingClientRect().width),
                h: Math.round(e.getBoundingClientRect().height),
                text: (e.textContent || '').trim().slice(0, 60),
            }));
            const nums = [...slide.querySelectorAll(
                '.gl-hero-value, .metric-value, [class*=hero-value], [class*=big-number]'
            )].map(e => ({
                text: e.textContent.trim(),
                fs: getComputedStyle(e).fontSize,
                fw: getComputedStyle(e).fontWeight,
            }));
            const labels = [...slide.querySelectorAll('.gl-hero-label, .metric-label')].map(e => ({
                text: e.textContent.trim().slice(0, 40),
                fs: getComputedStyle(e).fontSize,
            }));
            return {nCards: cards.length, cards: cards.slice(0, 8), nums, labels};
        }"""
        )

        # F4+ pill comparison s02
        activate(page, 2)
        out["F4_s02"] = page.evaluate(
            """() => {
            const slide = document.querySelectorAll('section.slide')[2];
            const stage = document.querySelector('.deck-stage').getBoundingClientRect();
            const board = slide.querySelector(
                '.pill-board, .gl-pill-board, [class*=pill-board], [class*=comparison-board]'
            );
            let boardInfo = null;
            if (board) {
                const r = board.getBoundingClientRect();
                boardInfo = {
                    cls: board.className.slice(0, 80),
                    w: Math.round(r.width),
                    h: Math.round(r.height),
                    hRatio: +(r.height / stage.height).toFixed(3),
                    cols: getComputedStyle(board).gridTemplateColumns,
                };
            }
            const fs28 = [];
            for (const e of slide.querySelectorAll('*')) {
                if (getComputedStyle(e).fontSize === '28px' && (e.textContent || '').trim()) {
                    fs28.push({
                        cls: (e.className || '').toString().slice(0, 40),
                        text: (e.textContent || '').trim().slice(0, 30),
                    });
                    if (fs28.length >= 8) break;
                }
            }
            const rail = slide.querySelector('[class*=rail], .pill-rail, .gl-rail');
            const railBox = rail ? rail.getBoundingClientRect() : null;
            return {
                board: boardInfo,
                fs28count: fs28.length,
                fs28: fs28,
                rail: railBox && {w: Math.round(railBox.width), h: Math.round(railBox.height)},
            };
        }"""
        )

        # R6-A pane title / tick / datalabel s16
        activate(page, 16)
        out["R6A_s16"] = page.evaluate(
            """() => {
            const slide = document.querySelectorAll('section.slide')[16];
            const titles = [...slide.querySelectorAll(
                'h3,h4,.gl-tile-label,.gl-pane-heading,.pane-heading,.chart-title'
            )].map(e => ({
                text: e.textContent.trim(),
                fs: getComputedStyle(e).fontSize,
                fw: getComputedStyle(e).fontWeight,
                color: getComputedStyle(e).color,
                cls: e.className.slice(0, 60),
            }));
            const charts = [...slide.querySelectorAll('.chartjs-wrap')].map((w, i) => {
                const c = w.querySelector('canvas');
                const ch = c && Chart.getChart(c);
                if (!ch) return null;
                const x = ch.options.scales && ch.options.scales.x;
                const y = ch.options.scales && ch.options.scales.y;
                const tickFont = (t) => t && t.ticks && t.ticks.font && (t.ticks.font.size || t.ticks.font);
                return {
                    i,
                    xTickFS: tickFont(x),
                    yTickFS: tickFont(y),
                    xTickColor: x && x.ticks && x.ticks.color,
                    xMaxRotation: x && x.ticks && x.ticks.maxRotation,
                    area: ch.chartArea && {
                        w: Math.round(ch.chartArea.right - ch.chartArea.left),
                        h: Math.round(ch.chartArea.bottom - ch.chartArea.top),
                    },
                };
            });
            return {titles, charts};
        }"""
        )

        # R6-C inset skin s19 / s23
        for si in (19, 23):
            activate(page, si)
            out[f"R6C_s{si}"] = page.evaluate(
                """(si) => {
                const slide = document.querySelectorAll('section.slide')[si];
                const candidates = [...slide.querySelectorAll(
                    '.inset, .gl-inset, [class*=inset], .callout-inset, .chart-inset'
                )];
                const insets = candidates.map(e => {
                    const r = e.getBoundingClientRect();
                    return {
                        cls: e.className.slice(0, 80),
                        text: (e.textContent || '').trim().slice(0, 60),
                        w: Math.round(r.width), h: Math.round(r.height),
                        bg: getComputedStyle(e).backgroundColor,
                        border: getComputedStyle(e).border,
                        color: getComputedStyle(e).color,
                        fs: getComputedStyle(e).fontSize,
                    };
                });
                return {nInsets: insets.length, insets: insets.slice(0, 8)};
            }""",
                si,
            )

        # F5 theme palette override — only if theme tries to tint defaults
        out["F5_theme"] = page.evaluate(
            """() => {
            const root = getComputedStyle(document.documentElement);
            const keys = ['--color-primary', '--chart-1', '--series-1', '--amex-navy', '--gl-navy'];
            const vals = {};
            for (const k of keys) vals[k] = root.getPropertyValue(k).trim();
            return {vals, triggered: false, note: 'no theme override attempt in this handoff'};
        }"""
        )

        # N6 contract diagnosis
        activate(page, 14)
        out["N6_contract_s14"] = page.evaluate(
            """() => {
            const slide = document.querySelectorAll('section.slide')[14];
            const outlined = slide.querySelector('.chart-support-outlined');
            return {
                cls: outlined && outlined.className,
                aligned: !!(outlined && outlined.classList.contains('chart-table-aligned')),
                hasWidthStyle: !!(outlined && outlined.getAttribute('style')),
                nCells: slide.querySelectorAll('.chart-outlined-cell').length,
                headerRowInSource: 'Q1\\'25' // documented: header is period row; primary labels are Quarter column
            };
        }"""
        )

        browser.close()

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"wrote {dest}")
    for k, v in out.items():
        print(k, ":", json.dumps(v, default=str)[:240])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
