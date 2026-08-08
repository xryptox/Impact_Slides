"""#150 — public auto-typography resolver and renderer integration."""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

import pytest

from impact_slides.renderer_v2 import render_deck
from impact_slides.renderer_v2.charts.auto_typography import (
    AUTO_X_LO,
    AUTO_Y_LO,
    _fit_x_labels,
    compute_auto_plan_for_slide,
    measure_label_box,
    resolve_auto_typography,
    sync_sibling_plans,
)

FIXTURES = Path(__file__).parent / "fixtures" / "renderer_v2"
from impact_slides.renderer_v2.charts.lines import _line_data
from impact_slides.renderer_v2.charts.typography import resolve_typography


def _handoff(slides):
    return {
        "meta": {"title": "t", "client": "c", "date": "2026-01-01"},
        "presentation": {"title": "t"},
        "slides": slides,
    }


def _pane(kind, labels, *, typography=None, short=False):
    cfg = {"point_labels": True, "series_names": ["Revenue"]}
    if typography is not None:
        cfg["typography"] = typography
    return {
        "type": kind,
        "chart_config": cfg,
        "steps_or_data": [
            {"label": label, "short_label": f"Q{i + 1}" if short else None, "value": i + 1}
            for i, label in enumerate(labels)
        ],
    }


def _configs(html):
    return [
        json.loads(raw)
        for raw in re.findall(
            r'<script type="application/json" class="chartjs-config"[^>]*>(.*?)</script>',
            html,
            re.S,
        )
    ]


def test_auto_mode_validates_raised_explicit_floors():
    with pytest.raises(ValueError, match="12"):
        resolve_typography({"typography": {"mode": "auto", "x_tick_font_size": 11}})
    with pytest.raises(ValueError, match="11"):
        resolve_typography({"typography": {"mode": "auto", "datalabel_font_size": 10}})
    assert resolve_typography({"typography": {"mode": "auto"}})["auto_mode"] == 1


def test_resolver_preserves_labels_before_ellipsis_and_keeps_endpoints():
    plan = resolve_auto_typography(
        chart_type="line_chart",
        host_w=80,
        host_h=180,
        categories=["Long reporting period alpha beta"] * 8,
        short_labels=[None] * 8,
        y_tick_values=[-10, -5, 0, 5, 10],
        y_tick_labels=["-10%", "-5%", "0%", "5%", "10%"],
    )
    assert plan.x_tick_font_size >= AUTO_X_LO
    assert plan.y_tick_font_size >= AUTO_Y_LO
    assert plan.x_labels is not None
    assert plan.x_labels.used_skip or plan.x_labels.used_ellipsis or plan.x_labels.used_wrap
    if plan.x_labels.used_skip:
        # Tick skipping keeps endpoints unless last-ditch ellipsis cannot fit.
        if not plan.x_labels.used_ellipsis:
            assert plan.x_labels.texts[0]
            assert plan.x_labels.texts[-1]


def test_sibling_sync_uses_common_auto_sizes_but_preserves_explicit_channel():
    wide = resolve_auto_typography(
        chart_type="grouped_bar_chart", host_w=900, host_h=480,
        categories=["Q1", "Q2"], y_tick_values=[0, 10], y_tick_labels=["0", "10"],
    )
    dense = resolve_auto_typography(
        chart_type="grouped_bar_chart", host_w=260, host_h=220,
        categories=[f"Long category {i}" for i in range(12)],
        y_tick_values=[0, 10], y_tick_labels=["0", "10"],
        x_explicit=18,
    )
    synced = sync_sibling_plans([wide, dense])
    assert synced[1].x_tick_font_size == 18
    assert synced[0].x_tick_font_size <= wide.x_tick_font_size
    assert synced[0].y_tick_font_size == synced[1].y_tick_font_size


def test_dual_chart_applies_synced_auto_plan_to_chartjs_svg_and_metadata(tmp_path):
    typo = {"mode": "auto"}
    slide = {
        "slide_number": 17,
        "title": "Auto", "layout_type": "dual_chart", "content": {"so_what": "x"},
        "visual_spec": {
            "primary_visual": _pane("grouped_bar_chart", [f"Period {i}" for i in range(8)], typography=typo),
            "secondary_visual": _pane("line_chart", [f"Long reporting period {i}" for i in range(8)], typography=typo),
        }, "evidence_sources": [],
    }
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(_handoff([slide])), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(path, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    configs = _configs(html)
    assert len(configs) == 2
    x_sizes = [c["options"]["scales"]["x"]["ticks"]["font"]["size"] for c in configs]
    y_sizes = [c["options"]["scales"]["y"]["ticks"]["font"]["size"] for c in configs]
    assert x_sizes[0] == x_sizes[1] and x_sizes[0] >= AUTO_X_LO
    assert y_sizes[0] == y_sizes[1] and y_sizes[0] >= AUTO_Y_LO
    assert html.count('data-auto-typo="1"') == 4  # Chart.js wrappers + SVG fallbacks
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert len(meta["auto_typography"]) == 2


def test_svg_and_chartjs_receive_the_same_auto_sizes(tmp_path):
    pane = _pane(
        "grouped_bar_chart", [f"Long period {i}" for i in range(7)],
        typography={"mode": "auto"},
    )
    slide = {
        "slide_number": 1, "title": "Auto", "layout_type": "grouped_bar_chart", "content": {},
        "visual_spec": {"primary_visual": pane}, "evidence_sources": [],
    }
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(_handoff([slide])), encoding="utf-8")
    chartjs_out, svg_out = tmp_path / "chartjs", tmp_path / "svg"
    render_deck(path, chartjs_out, strict=False)
    render_deck(path, svg_out, strict=False, suppress_features=["charts"])
    cfg = _configs((chartjs_out / "presentation.html").read_text(encoding="utf-8"))[0]
    chartjs_x = cfg["options"]["scales"]["x"]["ticks"]["font"]["size"]
    chartjs_y = cfg["options"]["scales"]["y"]["ticks"]["font"]["size"]
    svg = (svg_out / "presentation.html").read_text(encoding="utf-8")
    assert f'font-size="{chartjs_x}"' in svg
    assert f'font-size="{chartjs_y}"' in svg
    assert 'data-auto-typo="1"' in svg  # SVG wrapper carries the shared diagnostic.


@pytest.mark.parametrize(
    ("labels", "short_labels", "plot_w", "bottom", "expected"),
    [
        (["Q1 2026"] * 2, [None] * 2, 300, 80, (False, 0, False, False, False)),
        (["Long alpha beta gamma"] * 8, [None] * 8, 220, 80, (False, 0, False, True, False)), 
        (["AlphaBeta"] * 2, [None] * 2, 130, 70, (False, 30, False, False, False)),
        (["Long alpha beta"] * 2, [None] * 2, 140, 110, (False, 45, False, False, False)),
        (["Long alpha beta gamma"] * 8, [f"Q{i}" for i in range(8)], 160, 80, (False, 0, True, False, False)),
        (["Long alpha beta gamma"] * 8, [None] * 8, 220, 80, (False, 0, False, True, False)),
        (["Supercalifragilisticexpialidocious"] * 8, [None] * 8, 100, 80, (False, 0, False, False, True)),
    ],
)
def test_x_adaptation_stage_order_mutation_traps(labels, short_labels, plot_w, bottom, expected):
    """Each issue-mandated stage has a distinct fit case and ordering trap."""
    plan = _fit_x_labels(labels, short_labels, 12, plot_w, bottom)
    assert plan is not None
    assert (
        plan.used_wrap,
        plan.rotation_deg,
        plan.used_short,
        plan.used_skip,
        plan.used_ellipsis,
    ) == expected


def test_sibling_sync_mutation_trap_uses_smallest_non_explicit_size():
    wide = resolve_auto_typography(
        chart_type="line_chart", host_w=900, host_h=480, categories=["Q1", "Q2"],
        y_tick_values=[0, 50, 100], y_tick_labels=["0", "50", "100"],
        datalabel_texts=["100"], want_datalabels=True,
    )
    dense = resolve_auto_typography(
        chart_type="line_chart", host_w=220, host_h=180,
        categories=["Long reporting period alpha beta"] * 8,
        y_tick_values=[0, 50, 100], y_tick_labels=["0", "50", "100"],
        datalabel_texts=["100"], want_datalabels=True,
    )
    synced = sync_sibling_plans([wide, dense])
    assert synced[0].x_tick_font_size == synced[1].x_tick_font_size == dense.x_tick_font_size
    assert synced[0].y_tick_font_size == synced[1].y_tick_font_size == dense.y_tick_font_size
    assert synced[0].datalabel_font_size == synced[1].datalabel_font_size == dense.datalabel_font_size


def test_plan_suppresses_chartjs_and_svg_ordinary_datalabels(tmp_path):
    pane = _pane("grouped_bar_chart", [f"Category {i}" for i in range(80)], typography={"mode": "auto"})
    slide = {
        "slide_number": 1, "title": "Auto", "layout_type": "grouped_bar_chart", "content": {},
        "visual_spec": {"primary_visual": pane}, "evidence_sources": [],
    }
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(_handoff([slide])), encoding="utf-8")
    chartjs_out, svg_out = tmp_path / "chartjs", tmp_path / "svg"
    render_deck(path, chartjs_out, strict=False)
    render_deck(path, svg_out, strict=False, suppress_features=["charts"])
    config = _configs((chartjs_out / "presentation.html").read_text(encoding="utf-8"))[0]
    assert "datalabels" not in config["options"]["plugins"]
    svg = (svg_out / "presentation.html").read_text(encoding="utf-8")
    assert not re.search(r'<text x="[^>]+ font-weight="600"[^>]*>\d+</text>', svg)


def test_svg_receives_adapted_labels_and_datalabel_suppression(tmp_path):
    pane = _pane(
        "grouped_bar_chart",
        ["Supercalifragilisticexpialidocious"] * 8,
        typography={"mode": "auto"},
        short=True,
    )
    slide = {
        "slide_number": 1, "title": "Auto", "layout_type": "grouped_bar_chart", "content": {},
        "visual_spec": {"primary_visual": pane}, "evidence_sources": [],
    }
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(_handoff([slide])), encoding="utf-8")
    out = tmp_path / "svg"
    render_deck(path, out, strict=False, suppress_features=["charts"])
    html = (out / "presentation.html").read_text(encoding="utf-8")
    labels = re.findall(r'class="auto-x-label"[^>]*>(.*?)</text>', html)
    assert labels == [f"Q{i + 1}" for i in range(8)]


@pytest.mark.parametrize("font", ["Source Sans 3", "IBM Plex Sans"])
@pytest.mark.parametrize("size", [12, 18, 24])
@pytest.mark.parametrize("rotation", [0, 30, 45])
def test_calibrated_metrics_conservatively_contain_browser_bounds(font, size, rotation):
    """Chromium verifies the metric tables; Chromium is never deck runtime."""
    from playwright.sync_api import sync_playwright

    family = "source-sans-3-latin.woff2" if font == "Source Sans 3" else "ibm-plex-sans-latin.woff2"
    face = "SourceMetric" if font == "Source Sans 3" else "PlexMetric"
    font_data = base64.b64encode(
        (Path("impact_slides/renderer_v2/assets/fonts") / family).read_bytes()
    ).decode("ascii")
    samples = ["WWWWW", "mill", "Revenue", "Q1 2026", "111,222.50%", "M&A / FY-2026"]
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.set_content(
            f'<style>@font-face{{font-family:{face};src:url(data:font/woff2;base64,{font_data}) format("woff2")}}</style>'
        )
        actual = page.evaluate(
            """async ({face, size, rotation, samples}) => {
              await document.fonts.load(`600 ${size}px ${face}`, samples.join(""));
              const root = document.createElement("div");
              root.style.cssText = 'position:absolute;left:200px;top:200px;white-space:nowrap';
              document.body.append(root);
              return samples.map(text => {
                const el = document.createElement('span');
                el.textContent = text;
                el.style.cssText = `display:inline-block;font:600 ${size}px ${face};line-height:normal;transform:rotate(${rotation}deg)`;
                root.append(el);
                const r = el.getBoundingClientRect();
                el.remove();
                return {width:r.width, height:r.height};
              });
            }""",
            {"face": face, "size": size, "rotation": rotation, "samples": samples},
        )
        browser.close()
    for text, bounds in zip(samples, actual):
        estimated_w, estimated_h = measure_label_box(
            text, size, font=font, weight=600, rotation_deg=rotation
        )
        assert estimated_w >= bounds["width"], (font, size, rotation, text, estimated_w, bounds)
        assert estimated_h >= bounds["height"], (font, size, rotation, text, estimated_h, bounds)
        assert estimated_w <= bounds["width"] + max(bounds["width"] * 0.05, 2), (font, size, rotation, text, estimated_w, bounds)
        assert estimated_h <= bounds["height"] + max(bounds["height"] * 0.05, 2), (font, size, rotation, text, estimated_h, bounds)


def test_auto_chartjs_uses_complete_formatted_tick_plan_and_reserves_default_legend(tmp_path):
    pane = _pane("line_chart", ["Q1", "Q2"], typography={"mode": "auto"})
    pane["chart_config"].update({"y_axis_unit": "USD", "y_axis_unit_position": "prefix"})
    slide = {
        "slide_number": 1, "title": "Auto", "layout_type": "line_chart", "content": {},
        "visual_spec": {"primary_visual": pane}, "evidence_sources": [],
    }
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(_handoff([slide])), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(path, out, strict=False)
    config = _configs((out / "presentation.html").read_text(encoding="utf-8"))[0]
    ticks = config["options"]["scales"]["y"]["ticks"]
    plan = compute_auto_plan_for_slide(slide, "line_chart", host_w=900, host_h=480)
    assert plan is not None
    assert ticks["_rv2Values"] == plan.y_tick_values
    assert ticks["_rv2Labels"] == plan.y_tick_labels
    assert config["options"]["scales"]["y"]["min"] == plan.y_tick_values[0]
    assert config["options"]["scales"]["y"]["max"] == plan.y_tick_values[-1]
    assert all(label.startswith("USD") for label in ticks["_rv2Labels"])
    assert config["options"]["plugins"]["legend"].get("display") is False
    svg_out = tmp_path / "svg"
    render_deck(path, svg_out, strict=False, suppress_features=["charts"])
    svg = (svg_out / "presentation.html").read_text(encoding="utf-8")
    assert all(f">{label}</text>" in svg for label in plan.y_tick_labels)
    explicit = json.loads(json.dumps(slide))
    explicit["visual_spec"]["primary_visual"]["chart_config"]["series_names"] = ["Revenue", "Margin"]
    explicit_plan = compute_auto_plan_for_slide(explicit, "line_chart", host_w=900, host_h=480)
    assert explicit_plan is not None
    assert plan.plot_h == explicit_plan.plot_h


def test_full_44_slide_v10_auto_audit_chartjs_and_svg(tmp_path):
    """The archived v10 handoff renders every opted-in pane with contained text."""
    from playwright.sync_api import sync_playwright
    from scripts.amex_handoff_mutations import apply_all

    handoff = json.loads((FIXTURES / "amex_v10_44_slide_handoff.json").read_text(encoding="utf-8"))
    handoff = apply_all(handoff)
    supported = {
        "line_chart", "grouped_bar_chart", "stacked_bar_chart", "horizontal_bar_chart", "combo_chart", "waterfall_chart",
    }
    expected_by_slide = {}
    for slide in handoff["slides"]:
        visual = slide.get("visual_spec") or {}
        panes = [visual.get(key) for key in ("primary_visual", "secondary_visual")]
        primary = visual.get("primary_visual")
        if isinstance(primary, dict):
            panes.extend(tile for tile in primary.get("tiles") or [] if isinstance(tile, dict) and tile.get("kind") == "chart")
        expected = 0
        for pane in panes:
            if not isinstance(pane, dict):
                continue
            kind = pane.get("type") or pane.get("chart_type")
            if kind in supported:
                pane.setdefault("chart_config", {}).setdefault("typography", {})["mode"] = "auto"
                expected += 1
        expected_by_slide[slide["slide_number"]] = expected if slide.get("layout_type") != "metric_row_with_breakdown" else 0
    assert sum(expected_by_slide.values()) > 0
    path = tmp_path / "v10.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")
    for name, suppress in (("chartjs", []), ("svg", ["charts"])):
        out = tmp_path / name
        render_deck(path, out, strict=False, suppress_features=suppress)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert len(re.findall(r'<section class="slide[^>]*data-slide-number="', html)) == 44
        decisions = meta["auto_typography"]
        assert sum(len([d for d in decisions if d.get("slide_number") == number]) for number in expected_by_slide) == sum(expected_by_slide.values()), name
        assert all(
            len([d for d in decisions if d.get("slide_number") == number]) == expected
            for number, expected in expected_by_slide.items()
        ), (name, decisions)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            if name == "chartjs":
                page.add_init_script(
                    """(() => {
                      const original = CanvasRenderingContext2D.prototype.fillText;
                      const clear = CanvasRenderingContext2D.prototype.clearRect;
                      window.__rv2ChartText = [];
                      CanvasRenderingContext2D.prototype.clearRect = function() {
                        window.__rv2ChartText = window.__rv2ChartText.filter(item => item.canvas !== this.canvas.id);
                        return clear.apply(this, arguments);
                      };
                      CanvasRenderingContext2D.prototype.fillText = function(text, x, y, maxWidth) {
                        const metrics = this.measureText(String(text));
                        const m = this.getTransform();
                        window.__rv2ChartText.push({canvas: this.canvas.id, text: String(text), x, y,
                          width: metrics.width, ascent: metrics.actualBoundingBoxAscent || 12,
                          descent: metrics.actualBoundingBoxDescent || 4, align: this.textAlign,
                          matrix: [m.a, m.b, m.c, m.d, m.e, m.f]});
                        return original.call(this, text, x, y, maxWidth);
                      };
                    })()"""
                )
            page.goto((out / "presentation.html").resolve().as_uri(), wait_until="networkidle")
            page.evaluate("""async () => {
              for (const slide of document.querySelectorAll('.slide')) {
                slide.classList.add('active');
                await new Promise(resolve => requestAnimationFrame(resolve));
              }
              if (window.__rv2ChartText) {
                window.__rv2ChartText = [];
                Object.values(Chart.instances).forEach(chart => { chart.resize(); chart.update('none'); });
                await new Promise(resolve => requestAnimationFrame(resolve));
              }
            }""")
            audit = page.evaluate(
                """(chartjs) => {
                  const overlap = (a, b) => a.left < b.right - 1 && a.right > b.left + 1 &&
                    a.top < b.bottom - 1 && a.bottom > b.top + 1;
                  const within = (r, outer) => r.width >= 1 && r.height >= 1 &&
                    r.left >= outer.left - 1 && r.top >= outer.top - 1 &&
                    r.right <= outer.right + 1 && r.bottom <= outer.bottom + 1;
                  const chartBox = (canvas, item) => {
                    const r = canvas.getBoundingClientRect(), sx = r.width / canvas.width, sy = r.height / canvas.height;
                    const left = item.align === 'right' || item.align === 'end' ? item.x - item.width :
                      item.align === 'center' ? item.x - item.width / 2 : item.x;
                    const top = item.y - item.ascent, bottom = item.y + item.descent;
                    const [a, b, c, d, e, f] = item.matrix;
                    const points = [[left, top], [left + item.width, top], [left, bottom], [left + item.width, bottom]]
                      .map(([x, y]) => [a * x + c * y + e, b * x + d * y + f]);
                    const xs = points.map(p => r.left + p[0] * sx), ys = points.map(p => r.top + p[1] * sy);
                    return {left: Math.min(...xs), right: Math.max(...xs), top: Math.min(...ys), bottom: Math.max(...ys),
                      width: Math.max(...xs) - Math.min(...xs), height: Math.max(...ys) - Math.min(...ys)};
                  };
                  return [...document.querySelectorAll('.slide')].map((slide, index) => {
                    const outer = slide.getBoundingClientRect();
                    const panes = chartjs
                      ? [...slide.querySelectorAll('.chartjs-wrap[data-auto-typo="1"]')].map(wrap => {
                          const canvas = wrap.querySelector('canvas');
                          const raw = canvas ? (window.__rv2ChartText || []).filter(item => item.canvas === canvas.id) : [];
                          const boxes = raw.map(item => ({text: item.text, box: chartBox(canvas, item)}))
                            .filter(item => item.box.width >= 1 && item.box.height >= 1);
                          const chart = canvas && Chart.getChart(canvas), rect = canvas && canvas.getBoundingClientRect();
                          const x = chart && chart.scales.x, y = chart && chart.scales.y, y1 = chart && chart.scales.y1;
                          const valueAxis = chart && chart.options.indexAxis === 'y' ? x : y;
                          const categoryAxis = chart && chart.options.indexAxis === 'y' ? y : x;
                          const axisText = axis => (axis && axis.ticks || []).map(tick => String(tick.label));
                          const categoryLabels = JSON.parse(wrap.dataset.autoXLabels || '[]');
                          const valueLabels = axisText(valueAxis), y1Labels = axisText(y1);
                          const boxesFor = labels => {
                            const used = new Set();
                            return labels.map(label => {
                              const index = boxes.findIndex((item, i) => !used.has(i) &&
                                (item.text === label || (label === '0' && item.text === '0%')));
                              if (index < 0) return null;
                              used.add(index);
                              return boxes[index].box;
                            }).filter(Boolean);
                          };
                          const categoryBoxes = boxesFor(categoryLabels);
                          const yBoxes = boxesFor(valueLabels);
                          const y1Boxes = boxesFor(y1Labels);
                          const axisBoxes = categoryBoxes.concat(yBoxes, y1Boxes);
                          return {text_count: axisBoxes.length, raw_text_count: raw.length,
                            category_text_count: categoryBoxes.length, expected_category_ticks: categoryLabels.length,
                            y_text_count: yBoxes.length, y1_text_count: y1Boxes.length,
                            actual_y_ticks: valueAxis ? valueAxis.ticks.length : 0, actual_y1_ticks: y1 ? y1.ticks.length : 0,
                            expected_y_ticks: Number(wrap.dataset.autoYTicks || 0), expected_y1_ticks: Number(wrap.dataset.autoY1Ticks || 0),
                            clipped: axisBoxes.some(box => !within(box, outer)),
                            overlap: [categoryBoxes, yBoxes, y1Boxes].some(group => group.some((box, i) => group.slice(i + 1).some(other => overlap(box, other))))};
                        })
                      : [...slide.querySelectorAll('.chart-svg-wrap[data-auto-typo="1"]')].map(wrap => {
                          const boxes = [...wrap.querySelectorAll('svg text')].map(text => text.getBoundingClientRect());
                          const categoryBoxes = [...wrap.querySelectorAll('svg text.auto-x-label')].map(text => text.getBoundingClientRect());
                          const yBoxes = [...wrap.querySelectorAll('svg text.auto-y-label')].map(text => text.getBoundingClientRect());
                          const y1Boxes = [...wrap.querySelectorAll('svg text.auto-y1-label')].map(text => text.getBoundingClientRect());
                          const categoryGroups = [...wrap.querySelectorAll('svg text.auto-x-label')].reduce((groups, text) => {
                            const key = text.dataset.autoLabelIndex;
                            if (key !== undefined) {
                              if (!groups.has(key)) groups.set(key, []);
                              groups.get(key).push(text.getBoundingClientRect());
                            }
                            return groups;
                          }, new Map());
                          const collides = group => group.some((box, i) => group.slice(i + 1).some(other => overlap(box, other)));
                          const groups = [...categoryGroups.values()];
                          const categoryOverlap = groups.some((group, i) => groups.slice(i + 1).some(other =>
                            group.some(box => other.some(candidate => overlap(box, candidate)))));
                          return {text_count: categoryBoxes.length, y_text_count: yBoxes.length, y1_text_count: y1Boxes.length,
                            expected_y_ticks: Number(wrap.dataset.autoYTicks || 0), expected_y1_ticks: Number(wrap.dataset.autoY1Ticks || 0),
                            clipped: boxes.some(box => !within(box, outer)),
                            overlap: categoryOverlap || collides(yBoxes) || collides(y1Boxes)};
                        });
                    return {slide_number: index + 1, panes};
                  });
                }""",
                name == "chartjs",
            )
            browser.close()
        for row in audit:
            if expected_by_slide[row["slide_number"]]:
                assert len(row["panes"]) == expected_by_slide[row["slide_number"]], (name, row)
                if name == "svg":
                    assert all(
                        pane["text_count"] and pane["y_text_count"] == pane["expected_y_ticks"]
                        and pane["y1_text_count"] == pane["expected_y1_ticks"]
                        and not pane["clipped"] and not pane["overlap"]
                        for pane in row["panes"]
                    ), (name, row)
                else:
                    assert all(
                        pane["text_count"] and pane["category_text_count"] == pane["expected_category_ticks"] and (
                            pane["expected_y_ticks"] == 0 or (
                                pane["actual_y_ticks"] == pane["expected_y_ticks"]
                                and pane["y_text_count"] >= pane["actual_y_ticks"]
                            )
                        ) and (
                            pane["expected_y1_ticks"] == 0 or (
                                pane["actual_y1_ticks"] == pane["expected_y1_ticks"]
                                and pane["y1_text_count"] >= pane["actual_y1_ticks"]
                            )
                        )
                        and not pane["clipped"] and not pane["overlap"]
                        for pane in row["panes"]
                    ), (name, row)
        (out / "auto_typography_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")


def test_auto_axis_break_plans_and_renders_only_effective_domain(tmp_path):
    line = _pane("line_chart", ["2024", "2025"], typography={"mode": "auto"})
    hbar = _pane("horizontal_bar_chart", ["2024", "2025"], typography={"mode": "auto"})
    for pane in (line, hbar):
        pane["chart_config"].update({"y_axis_break": {"from": 0, "to": 90}, "y_axis_max": 100})
        for point, value in zip(pane["steps_or_data"], (92, 98)):
            point["value"] = value
    slides = [
        {"slide_number": 1, "title": "Line", "layout_type": "line_chart", "content": {},
         "visual_spec": {"primary_visual": line}, "evidence_sources": []},
        {"slide_number": 2, "title": "Bars", "layout_type": "horizontal_bar_chart", "content": {},
         "visual_spec": {"primary_visual": hbar}, "evidence_sources": []},
    ]
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(_handoff(slides)), encoding="utf-8")
    chartjs_out = tmp_path / "chartjs"
    render_deck(path, chartjs_out, strict=False)
    configs = _configs((chartjs_out / "presentation.html").read_text(encoding="utf-8"))
    for config, scale_name in zip(configs, ("y", "x")):
        scale = config["options"]["scales"][scale_name]
        planned = scale["ticks"]["_rv2Values"]
        assert planned[0] == scale["min"] == 90
        assert planned[-1] == scale["max"] == 100
        assert all(90 <= tick <= 100 for tick in planned)
    svg_out = tmp_path / "svg"
    render_deck(path, svg_out, strict=False, suppress_features=["charts"])
    svg = (svg_out / "presentation.html").read_text(encoding="utf-8")
    assert ">0%</text>" not in svg
    assert ">0</text>" not in svg


def test_auto_stacked_chartjs_preserves_stack_total_domain():
    pane = {
        "type": "stacked_bar_chart",
        "chart_config": {"typography": {"mode": "auto"}},
        "steps_or_data": [{"label": "Q1", "values": {"A": -60, "B": -60}}],
    }
    slide = {
        "slide_number": 1, "title": "Stacked", "layout_type": "stacked_bar_chart", "content": {},
        "visual_spec": {"primary_visual": pane}, "evidence_sources": [],
    }
    from impact_slides.renderer_v2.charts.chartjs import _chartjs_bar_config

    config = _chartjs_bar_config(slide, stacked=True)
    assert config is not None
    scale = config["options"]["scales"]["y"]
    assert scale["min"] == scale["ticks"]["_rv2Values"][0] <= -120


def test_svg_show_legend_false_omits_multiseries_legend(tmp_path):
    pane = _pane("grouped_bar_chart", ["Q1", "Q2"], typography={"mode": "auto"})
    pane["chart_config"].update({"show_legend": False, "series_names": ["Revenue", "Margin"]})
    for point in pane["steps_or_data"]:
        point["values"] = {"Revenue": point.pop("value"), "Margin": 2}
    slide = {
        "slide_number": 1, "title": "Bars", "layout_type": "grouped_bar_chart", "content": {},
        "visual_spec": {"primary_visual": pane}, "evidence_sources": [],
    }
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(_handoff([slide])), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(path, out, strict=False, suppress_features=["charts"])
    assert "vbar-legend-item" not in (out / "presentation.html").read_text(encoding="utf-8")


def test_svg_waterfall_honors_hidden_legend(tmp_path):
    pane = _pane("waterfall_chart", ["Q1", "Q2"], typography={"mode": "auto"})
    pane["chart_config"]["show_legend"] = False
    slide = {
        "slide_number": 1, "title": "Waterfall", "layout_type": "waterfall_chart", "content": {},
        "visual_spec": {"primary_visual": pane}, "evidence_sources": [],
    }
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(_handoff([slide])), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(path, out, strict=False, suppress_features=["charts"])
    assert '<div class="chart-legend">' not in (out / "presentation.html").read_text(encoding="utf-8")


def test_shared_axis_combo_svg_bars_start_at_zero_baseline():
    combo = {
        "layout_type": "combo_chart",
        "visual_spec": {
            "primary_visual": {
                "chart_config": {"typography": {"mode": "auto"}},
                "steps_or_data": [{"label": "Q1", "value": 10}],
            },
            "line_overlay": {"dual_axis": False, "data": [{"label": "Q1", "value": -100}]},
        },
    }
    from impact_slides.renderer_v2.charts.core import _svg_fallback_for_layout

    svg = _svg_fallback_for_layout(combo, "combo_chart")
    match = re.search(r'<rect x="[\d.]+" y="([\d.]+)" width="[\d.]+" height="([\d.]+)"[^>]*fill="', svg)
    assert match is not None
    y, height = map(float, match.groups())
    assert y >= 40 and 0 < height < 100


def test_hbar_svg_honors_hidden_value_axis(tmp_path):
    pane = _pane("horizontal_bar_chart", ["Q1", "Q2"], typography={"mode": "auto"})
    pane["chart_config"]["show_x_axis"] = False
    slide = {
        "slide_number": 1, "title": "Bars", "layout_type": "horizontal_bar_chart", "content": {},
        "visual_spec": {"primary_visual": pane}, "evidence_sources": [],
    }
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(_handoff([slide])), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(path, out, strict=False, suppress_features=["charts"])
    assert "hbar-xtick" not in (out / "presentation.html").read_text(encoding="utf-8")


def test_hbar_broken_axis_svg_bars_use_effective_domain_baseline(tmp_path):
    pane = _pane("horizontal_bar_chart", ["2024", "2025"], typography={"mode": "auto"})
    pane["chart_config"].update({"y_axis_break": {"from": 0, "to": 90}, "y_axis_max": 100})
    for point, value in zip(pane["steps_or_data"], (92, 98)):
        point["value"] = value
    slide = {
        "slide_number": 1, "title": "Bars", "layout_type": "horizontal_bar_chart", "content": {},
        "visual_spec": {"primary_visual": pane}, "evidence_sources": [],
    }
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(_handoff([slide])), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(path, out, strict=False, suppress_features=["charts"])
    svg = (out / "presentation.html").read_text(encoding="utf-8")
    bars = re.findall(r'<rect class="hbar-bar" x="([\d.]+)"[^>]* width="([\d.]+)"', svg)
    assert bars and all(float(x) >= 140 and 0 < float(width) < 796 for x, width in bars)


def test_auto_break_ignores_insufficient_forced_ticks(tmp_path):
    pane = _pane("line_chart", ["2024", "2025"], typography={"mode": "auto"})
    pane["chart_config"].update({
        "force_ticks": True, "y_axis_ticks": [0, 50, 100],
        "y_axis_break": {"from": 0, "to": 90},
    })
    for point, value in zip(pane["steps_or_data"], (92, 98)):
        point["value"] = value
    slide = {
        "slide_number": 1, "title": "Line", "layout_type": "line_chart", "content": {},
        "visual_spec": {"primary_visual": pane}, "evidence_sources": [],
    }
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(_handoff([slide])), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(path, out, strict=False)
    scale = _configs((out / "presentation.html").read_text(encoding="utf-8"))[0]["options"]["scales"]["y"]
    assert scale["ticks"]["_rv2Values"][-1] == scale["max"] > 100
    assert "stepSize" not in scale["ticks"]


def test_hbar_broken_axis_auto_ticks_stay_within_nonround_maximum(tmp_path):
    pane = _pane("horizontal_bar_chart", ["2024", "2025"], typography={"mode": "auto"})
    pane["chart_config"].update({"y_axis_break": {"from": 0, "to": 90}, "y_axis_max": 99})
    for point, value in zip(pane["steps_or_data"], (92, 98)):
        point["value"] = value
    slide = {
        "slide_number": 1, "title": "Bars", "layout_type": "horizontal_bar_chart", "content": {},
        "visual_spec": {"primary_visual": pane}, "evidence_sources": [],
    }
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(_handoff([slide])), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(path, out, strict=False)
    scale = _configs((out / "presentation.html").read_text(encoding="utf-8"))[0]["options"]["scales"]["x"]
    assert scale["ticks"]["_rv2Values"][-1] == scale["max"] == 99


def test_unknown_font_uses_reduced_confidence_metrics():
    plan = resolve_auto_typography(
        chart_type="line_chart", host_w=900, host_h=480, categories=["Q1"],
        font_x="Unrecognized Theme Font",
    )
    assert plan.used_fallback_font and plan.confidence == "reduced"


def test_wrapper_diagnostics_include_wrap_and_y_tick_reduction():
    plan = resolve_auto_typography(
        chart_type="line_chart", host_w=120, host_h=80,
        categories=["Long reporting period alpha beta"] * 8,
        y_tick_values=list(range(0, 101, 10)),
        y_tick_labels=[str(value) for value in range(0, 101, 10)],
    )
    from impact_slides.renderer_v2.charts.auto_typography import plan_to_data_attrs

    attrs = plan_to_data_attrs(plan)
    assert "data-auto-x-wrap=" in attrs and "data-auto-y-reduced=" in attrs


def test_adaptation_prefers_short_labels_before_skipping_categories():
    labels = ["Long reporting period alpha beta"] * 8
    plan = _fit_x_labels(labels, [f"Q{i}" for i in range(8)], 12, 160, 80)
    assert plan is not None
    assert plan.used_short
    assert not plan.used_skip
    assert not plan.used_ellipsis
    assert plan.texts == [f"Q{i}" for i in range(8)]


def test_waterfall_auto_uses_renderable_category_label_and_legacy_value_typography():
    steps = [{"label": "Skipped category", "value": None}]
    steps.extend(
        {
            "label": "Long reporting period alpha beta",
            "short_label": f"Q{i}",
            "value": i,
        }
        for i in range(1, 9)
    )
    slide = {
        "slide_number": 1,
        "title": "Waterfall",
        "layout_type": "waterfall_chart",
        "content": {},
        "visual_spec": {
            "primary_visual": {
                "chart_config": {"typography": {"mode": "auto"}},
                "steps_or_data": steps,
            }
        },
        "evidence_sources": [],
    }
    from impact_slides.renderer_v2 import charts

    html = charts.build_chart_html(slide, "waterfall_chart", use_chartjs=False)
    labels = re.findall(
        r'class="chart-axis-label auto-x-label" data-auto-label-index="(\d+)"[^>]*>(.*?)</text>',
        html,
    )
    value_size = re.search(r'class="chart-value"[^>]*font-size="(\d+)"', html)
    assert labels == [("8", "Long reporting period alpha beta")]
    assert value_size and value_size.group(1) == "18"

    explicit = {**slide, "visual_spec": {"primary_visual": {
        **slide["visual_spec"]["primary_visual"],
        "chart_config": {"typography": {"mode": "auto", "datalabel_font_size": 22}},
    }}}
    explicit_html = charts.build_chart_html(explicit, "waterfall_chart", use_chartjs=False)
    explicit_value_size = re.search(
        r'class="chart-value"[^>]*font-size="(\d+)"', explicit_html
    )
    assert explicit_value_size and explicit_value_size.group(1) == "18"


def test_auto_plan_includes_line_series_and_combo_overlay_axes():
    line = {
        "layout_type": "line_chart",
        "visual_spec": {"primary_visual": {
            "chart_config": {"typography": {"mode": "auto"}},
            "steps_or_data": [
                {
                    "label": "Long reporting period alpha beta",
                    "short_label": f"Q{i}",
                    "value": i,
                    "series_2": i * 1000,
                }
                for i in range(1, 9)
            ],
        }},
    }
    points = _line_data(line)
    short_plan = _fit_x_labels(
        [point["label"] for point in points],
        [point.get("short_label") for point in points],
        12,
        160,
        80,
    )
    line_plan = compute_auto_plan_for_slide(line, "line_chart", host_w=200, host_h=240)
    assert short_plan is not None and short_plan.used_short
    assert line_plan is not None and line_plan.x_labels is not None
    assert line_plan.x_labels.used_short and max(line_plan.y_tick_values) >= 2000

    percent_line = {
        "layout_type": "line_chart",
        "visual_spec": {"primary_visual": {
            "chart_config": {"typography": {"mode": "auto"}},
            "steps_or_data": [{"label": "Q1", "value": 100}],
        }},
    }
    percent_plan = compute_auto_plan_for_slide(
        percent_line, "line_chart", host_w=900, host_h=480
    )
    assert percent_plan is not None and percent_plan.y_tick_labels[-1].endswith("%")

    stacked = {
        "layout_type": "stacked_bar_chart",
        "visual_spec": {"primary_visual": {
            "chart_config": {"typography": {"mode": "auto"}},
            "steps_or_data": [{"label": "Q1", "values": {"A": 60, "B": 60}}],
        }},
    }
    stacked_plan = compute_auto_plan_for_slide(
        stacked, "stacked_bar_chart", host_w=900, host_h=480
    )
    assert stacked_plan is not None and max(stacked_plan.y_tick_values) >= 120

    combo = {
        "layout_type": "combo_chart",
        "visual_spec": {
            "primary_visual": {
                "chart_config": {"typography": {"mode": "auto"}},
                "steps_or_data": [{"label": "Q1", "value": 1}, {"label": "Q2", "value": 2}],
            },
            "line_overlay": {
                "data": [{"label": "Q1", "value": 10000}, {"label": "Q2", "value": 20000}],
                "y_axis_max": 20000,
                "y_axis_unit": " users",
            },
        },
    }
    combo_plan = compute_auto_plan_for_slide(combo, "combo_chart", host_w=900, host_h=480)
    assert combo_plan is not None
    assert 20000 in combo_plan.secondary_y_tick_values
    assert "20000 users" in combo_plan.secondary_y_tick_labels
    from impact_slides.renderer_v2.charts.core import _svg_fallback_for_layout

    svg = _svg_fallback_for_layout(combo, "combo_chart")
    assert "<polyline" in svg and 'x1="820"' in svg


def test_auto_planning_matches_unrotated_hbar_and_line_svg_axes():
    hbar = {
        "layout_type": "horizontal_bar_chart",
        "visual_spec": {"primary_visual": {
            "chart_config": {"typography": {"mode": "auto"}},
            "steps_or_data": [
                {"label": "Long reporting period alpha beta", "short_label": "Q1", "value": 1}
                for _ in range(8)
            ],
        }},
    }
    hbar_plan = compute_auto_plan_for_slide(hbar, "horizontal_bar_chart", host_w=960, host_h=540)
    assert hbar_plan is not None and hbar_plan.x_labels is not None
    assert hbar_plan.x_labels.rotation_deg == 0

    line = {
        "layout_type": "line_chart",
        "visual_spec": {"primary_visual": {
            "chart_config": {"typography": {"mode": "auto"}},
            "steps_or_data": [{"label": "Q1", "value": 9}],
        }},
    }
    line_plan = compute_auto_plan_for_slide(line, "line_chart", host_w=900, host_h=480)
    from impact_slides.renderer_v2.charts.lines import _build_line_chart_svg

    svg = _build_line_chart_svg(line)
    assert line_plan is not None
    assert line_plan.y_tick_values == [0.0, 2.75, 5.5, 8.25, 11.0]
    assert all(f">{tick:g}%</text>" in svg for tick in line_plan.y_tick_values)


def test_combo_reduces_each_svg_axis_independently():
    ticks = list(range(40))
    combo = {
        "layout_type": "combo_chart",
        "visual_spec": {
            "primary_visual": {
                "chart_config": {"typography": {"mode": "auto", "y_tick_font_size": 12}, "y_axis_ticks": ticks},
                "steps_or_data": [{"label": "Q1", "value": 1}],
            },
            "line_overlay": {
                "data": [{"label": "Q1", "value": 39}],
                "y_axis_ticks": ticks,
            },
        },
    }
    plan = compute_auto_plan_for_slide(combo, "combo_chart", host_w=900, host_h=480)
    from impact_slides.renderer_v2.charts.core import _svg_fallback_for_layout

    svg = _svg_fallback_for_layout(combo, "combo_chart")
    assert plan is not None and plan.secondary_y_ticks_reduced
    assert plan.y_tick_values[0] == 0
    assert plan.secondary_y_tick_values[0] == 0
    assert plan.secondary_y_tick_values[-1] == 39
    assert svg.count('font-size="12"') < len(ticks) * 2


def test_auto_skip_uses_actual_retained_tick_spacing():
    labels = ["Moderately long category"] * 8
    kept = [0, 5, 7]
    from impact_slides.renderer_v2.charts.auto_typography import _try_x_fit

    assert _try_x_fit(
        [labels[i] for i in kept], 12, 340, 80,
        font="source_sans_3", rotation=0, wrap=True,
    )[0]
    assert not _try_x_fit(
        [labels[i] for i in kept], 12, 340, 80,
        font="source_sans_3", rotation=0, wrap=True,
        positions=kept, total_slots=len(labels),
    )[0]


def test_auto_full_labels_are_retained_in_chart_accessibility(tmp_path):
    labels = ["Long reporting period alpha beta"] * 8
    slide = {
        "slide_number": 1, "title": "Accessible", "layout_type": "line_chart", "content": {},
        "visual_spec": {"primary_visual": _pane("line_chart", labels, typography={"mode": "auto"}, short=True)},
        "evidence_sources": [],
    }
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(_handoff([slide])), encoding="utf-8")
    chartjs_out, svg_out = tmp_path / "chartjs", tmp_path / "svg"
    render_deck(path, chartjs_out, strict=False)
    render_deck(path, svg_out, strict=False, suppress_features=["charts"])
    for output in (chartjs_out, svg_out):
        html = (output / "presentation.html").read_text(encoding="utf-8")
        assert "categories: Long reporting period alpha beta" in html


def test_auto_tick_view_preserves_authored_axis_domain():
    slide = {
        "layout_type": "line_chart",
        "visual_spec": {"primary_visual": {
            "chart_config": {
                "typography": {"mode": "auto"}, "y_axis_min": 0,
                "y_axis_max": 100, "y_axis_ticks": [45, 50, 55],
            },
            "steps_or_data": [{"label": "Q1", "value": 0}, {"label": "Q2", "value": 100}],
        }},
    }
    from impact_slides.renderer_v2.charts.chartjs import _chartjs_line_config

    config = _chartjs_line_config(slide)
    assert config is not None
    scale = config["options"]["scales"]["y"]
    assert (scale["min"], scale["max"]) == (0.0, 100.0)
    assert scale["ticks"]["_rv2Values"] == [45.0, 55.0]


def test_auto_combo_primary_domain_includes_negative_bar_totals():
    combo = {
        "layout_type": "combo_chart",
        "visual_spec": {
            "primary_visual": {
                "chart_config": {"typography": {"mode": "auto"}},
                "steps_or_data": [{"label": "Q1", "value": -100}],
            },
            "line_overlay": {"dual_axis": False, "data": [{"label": "Q1", "value": 10}]},
        },
    }
    from impact_slides.renderer_v2.charts.chartjs import _chartjs_combo_config

    config = _chartjs_combo_config(combo)
    assert config is not None
    scale = config["options"]["scales"]["y"]
    assert scale["min"] <= -100


def test_auto_y_ticks_fit_against_their_scale_domain():
    slide = {
        "layout_type": "line_chart",
        "visual_spec": {"primary_visual": {
            "chart_config": {
                "typography": {"mode": "auto"}, "y_axis_min": 0,
                "y_axis_max": 100, "y_axis_ticks": [45, 50, 55],
            },
            "steps_or_data": [{"label": "Q1", "value": 0}, {"label": "Q2", "value": 100}],
        }},
    }
    from impact_slides.renderer_v2.charts.auto_typography import compute_auto_plan_for_slide

    plan = compute_auto_plan_for_slide(slide, "line_chart", host_w=900, host_h=480)
    assert plan is not None
    assert plan.y_domain_min == 0 and plan.y_domain_max == 100
    assert plan.y_tick_font_size < 28


def test_auto_bar_ticks_stay_in_the_svg_scale_domain():
    slide = {
        "layout_type": "grouped_bar_chart",
        "visual_spec": {"primary_visual": {
            "chart_config": {"typography": {"mode": "auto"}},
            "steps_or_data": [{"label": "Q1", "value": -60}, {"label": "Q2", "value": 60}],
        }},
    }
    from impact_slides.renderer_v2.charts.auto_typography import compute_auto_plan_for_slide

    plan = compute_auto_plan_for_slide(slide, "grouped_bar_chart", host_w=900, host_h=480)
    assert plan is not None
    assert (plan.y_domain_min, plan.y_domain_max) == (-80, 80)
    assert all(-80 <= tick <= 80 for tick in plan.y_tick_values)


def test_auto_combo_secondary_ticks_preserve_overlay_domain():
    combo = {
        "layout_type": "combo_chart",
        "visual_spec": {
            "primary_visual": {
                "chart_config": {"typography": {"mode": "auto"}},
                "steps_or_data": [{"label": "Q1", "value": 1}, {"label": "Q2", "value": 2}],
            },
            "line_overlay": {
                "data": [{"label": "Q1", "value": 0}, {"label": "Q2", "value": 100}],
                "y_axis_min": 0, "y_axis_max": 100, "y_axis_ticks": [45, 50, 55],
            },
        },
    }
    from impact_slides.renderer_v2.charts.chartjs import _chartjs_combo_config

    config = _chartjs_combo_config(combo)
    assert config is not None
    scale = config["options"]["scales"]["y1"]
    assert (scale["min"], scale["max"]) == (0, 100)
    assert scale["ticks"]["_rv2Values"] == [45.0, 55.0]


def test_auto_bar_ticks_include_explicit_nonround_domain_bound():
    slide = {
        "layout_type": "grouped_bar_chart",
        "visual_spec": {"primary_visual": {
            "chart_config": {"typography": {"mode": "auto"}, "y_axis_max": 99},
            "steps_or_data": [{"label": "Q1", "value": 98}],
        }},
    }
    from impact_slides.renderer_v2.charts.chartjs import _chartjs_bar_config

    config = _chartjs_bar_config(slide)
    assert config is not None
    scale = config["options"]["scales"]["y"]
    assert scale["max"] == 99
    assert scale["ticks"]["_rv2Values"][-1] == 99


def test_auto_mode_does_not_change_legacy_output(tmp_path):
    slide = {
        "slide_number": 1, "title": "Legacy", "layout_type": "grouped_bar_chart", "content": {},
        "visual_spec": {"primary_visual": _pane("grouped_bar_chart", ["Q1", "Q2"]),},
        "evidence_sources": [],
    }
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(_handoff([slide])), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(path, out, strict=False)
    cfg = _configs((out / "presentation.html").read_text(encoding="utf-8"))[0]
    assert cfg["options"]["scales"]["x"]["ticks"]["font"]["size"] == 13
