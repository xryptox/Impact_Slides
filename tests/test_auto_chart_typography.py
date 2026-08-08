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
    measure_label_box,
    resolve_auto_typography,
    sync_sibling_plans,
)

FIXTURES = Path(__file__).parent / "fixtures" / "renderer_v2"
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
        (["Long alpha beta gamma"] * 8, [None] * 8, 220, 80, (True, 0, False, True, False)), 
        (["AlphaBeta"] * 2, [None] * 2, 130, 70, (False, 30, False, False, False)),
        (["Long alpha beta"] * 2, [None] * 2, 140, 110, (False, 45, False, False, False)),
        (["Long alpha beta gamma"] * 8, [f"Q{i}" for i in range(8)], 160, 80, (False, 0, True, False, False)),
        (["Long alpha beta gamma"] * 8, [None] * 8, 220, 80, (True, 0, False, True, False)),
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
        ["Supercalifragilisticexpialidocious"] * 20,
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
    assert labels and all("Supercalifragilisticexpialidocious" not in label for label in labels)
    assert all("…" in label for label in labels)


@pytest.mark.parametrize("font", ["Source Sans 3", "IBM Plex Sans"])
@pytest.mark.parametrize("size", [12, 18, 24])
@pytest.mark.parametrize("rotation", [0, 30, 45])
def test_calibrated_metrics_conservatively_contain_browser_bounds(font, size, rotation):
    """Chromium verifies the metric tables; Chromium is never deck runtime."""
    pytest.importorskip("playwright.sync_api")
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


def test_full_44_slide_v10_auto_audit_chartjs_and_svg(tmp_path):
    """The archived v10 handoff renders both paths with recorded decisions and no viewport clips."""
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright
    from scripts.amex_handoff_mutations import apply_all

    handoff = json.loads((FIXTURES / "amex_v10_44_slide_handoff.json").read_text(encoding="utf-8"))
    handoff = apply_all(handoff)
    slide_17 = next(slide for slide in handoff["slides"] if slide["slide_number"] == 17)
    assert all(
        pane["chart_config"]["typography"].get("mode") == "auto"
        for pane in (slide_17["visual_spec"]["primary_visual"], slide_17["visual_spec"]["secondary_visual"])
    )
    supported = {
        "line_chart", "grouped_bar_chart", "stacked_bar_chart", "horizontal_bar_chart", "combo_chart", "waterfall_chart",
    }
    for slide in handoff["slides"]:
        visual = slide.get("visual_spec") or {}
        for key in ("primary_visual", "secondary_visual"):
            pane = visual.get(key)
            if isinstance(pane, dict) and pane.get("type") in supported:
                pane.setdefault("chart_config", {}).setdefault("typography", {})["mode"] = "auto"
        primary = visual.get("primary_visual")
        if isinstance(primary, dict):
            for tile in primary.get("tiles") or []:
                if isinstance(tile, dict) and tile.get("kind") == "chart" and tile.get("chart_type") in supported:
                    tile.setdefault("chart_config", {}).setdefault("typography", {})["mode"] = "auto"
    path = tmp_path / "v10.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")
    for name, suppress in (("chartjs", []), ("svg", ["charts"])):
        out = tmp_path / name
        render_deck(path, out, strict=False, suppress_features=suppress)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert len(re.findall(r'<section class="slide[^>]*data-slide-number="', html)) == 44
        assert meta["auto_typography"], name
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            page.goto((out / "presentation.html").resolve().as_uri(), wait_until="networkidle")
            clip = page.evaluate(
                """() => [...document.querySelectorAll('.slide')].map(slide => {
                    slide.classList.add('active');
                    const bad = [...slide.querySelectorAll('svg text, .chartjs-wrap, canvas')].some(el => {
                      const r = el.getBoundingClientRect();
                      return r.width < 1 || r.height < 1 || r.left < -1 || r.top < -1 || r.right > 1921 || r.bottom > 1081;
                    });
                    slide.classList.remove('active');
                    return bad;
                })"""
            )
            browser.close()
        audit = [
            {
                "slide_number": index + 1,
                "clipped": clipped,
                "decisions": [
                    decision for decision in meta["auto_typography"]
                    if decision.get("slide_number") == index + 1
                ],
                "warnings": [
                    warning for decision in meta["auto_typography"]
                    if decision.get("slide_number") == index + 1
                    for warning in decision.get("warnings", [])
                ],
            }
            for index, clipped in enumerate(clip)
        ]
        (out / "auto_typography_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
        assert len(audit) == 44 and not any(row["clipped"] for row in audit), (name, audit)


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
        for i in range(1, 20)
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
    assert labels == [("19", "Long reporting period alpha beta")]
    assert value_size and value_size.group(1) == "18"

    explicit = {**slide, "visual_spec": {"primary_visual": {
        **slide["visual_spec"]["primary_visual"],
        "chart_config": {"typography": {"mode": "auto", "datalabel_font_size": 22}},
    }}}
    explicit_html = charts.build_chart_html(explicit, "waterfall_chart", use_chartjs=False)
    explicit_value_size = re.search(
        r'class="chart-value"[^>]*font-size="(\d+)"', explicit_html
    )
    assert explicit_value_size and explicit_value_size.group(1) == "22"


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
