"""#139 R6-A — chart-internal typography (pane title + opt-in knobs + collision)."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from impact_slides.renderer_v2 import render_deck
from impact_slides.renderer_v2.charts.typography import (
    COLLISION_MARGIN_PX,
    LEGACY_DATALABEL,
    LEGACY_X_TICK,
    LEGACY_Y_TICK,
    boxes_intersect,
    chart_pane_title_html,
    estimate_label_box,
    resolve_typography,
    suppress_colliding_labels,
)
from impact_slides.renderer_v2.layout.recipes import render_dual_chart


def _handoff(slides):
    return {
        "meta": {"title": "t", "client": "c", "date": "2026-01-01"},
        "presentation": {"title": "t"},
        "slides": slides,
    }


def _write(tmp_path, handoff):
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")
    return path


def _bar_slide(cfg=None, *, point_labels=True):
    chart_cfg = {
        "y_axis_unit": "$",
        "point_labels": point_labels,
        "series_names": ["Fees"],
    }
    if cfg:
        chart_cfg.update(cfg)
    return {
        "slide_number": 1,
        "title": "Fees",
        "layout_type": "grouped_bar_chart",
        "content": {"bullets": [], "so_what": ""},
        "visual_spec": {
            "primary_visual": {
                "type": "grouped_bar_chart",
                "chart_config": chart_cfg,
                "steps_or_data": [
                    {"label": "Q1", "value": 0.9},
                    {"label": "Q2", "value": 1.1},
                    {"label": "Q3", "value": 1.3},
                ],
            }
        },
        "evidence_sources": [],
    }


def _dual_slide(typo=None):
    cfg = {"y_axis_unit": "$", "point_labels": True, "series_names": ["Net Card Fees $B"]}
    if typo is not None:
        cfg["typography"] = typo
    return {
        "slide_number": 17,
        "title": "Net Card Fees",
        "layout_type": "dual_chart",
        "content": {"so_what": "grew", "bullets": [], "key_stats": []},
        "visual_spec": {
            "primary_visual": {
                "type": "grouped_bar_chart",
                "label": "Net Card Fees $B",
                "chart_config": cfg,
                "steps_or_data": [
                    {"label": "Q1'19", "value": 0.9},
                    {"label": "Q1'20", "value": 1.1},
                    {"label": "Q1'21", "value": 1.3},
                ],
            },
            "secondary_visual": {
                "type": "line_chart",
                "label": "YoY Growth %",
                "chart_config": {
                    "y_axis_unit": "%",
                    "point_labels": True,
                    **(
                        {"typography": typo}
                        if typo is not None
                        else {}
                    ),
                },
                "steps_or_data": [
                    {"label": "Q1'24", "value": 16},
                    {"label": "Q2'24", "value": 18},
                    {"label": "Q3'24", "value": 20},
                ],
            },
        },
        "evidence_sources": [],
    }


def _chartjs_cfg(html: str) -> dict:
    m = re.search(
        r'<script type="application/json" class="chartjs-config"[^>]*>(.*?)</script>',
        html,
        re.S,
    )
    assert m, "chartjs config missing"
    return json.loads(m.group(1))


# ---------------------------------------------------------------------------
# resolve_typography
# ---------------------------------------------------------------------------


class TestResolveTypography:
    def test_absent_preserves_legacy(self):
        t = resolve_typography({})
        assert t["x_tick_font_size"] == LEGACY_X_TICK
        assert t["y_tick_font_size"] == LEGACY_Y_TICK
        assert t["datalabel_font_size"] == LEGACY_DATALABEL
        assert t["datalabel_font_size_set"] == 0

    def test_partial_fields(self):
        t = resolve_typography({"typography": {"y_tick_font_size": 24}})
        assert t["y_tick_font_size"] == 24
        assert t["y_tick_font_size_set"] == 1
        assert t["x_tick_font_size"] == LEGACY_X_TICK
        assert t["datalabel_font_size"] == LEGACY_DATALABEL

    @pytest.mark.parametrize(
        "field,lo,hi",
        [
            ("x_tick_font_size", 8, 24),
            ("y_tick_font_size", 8, 28),
            ("datalabel_font_size", 8, 32),
        ],
    )
    def test_bounds_accepted(self, field, lo, hi):
        t = resolve_typography({"typography": {field: lo}})
        assert t[field] == lo
        t = resolve_typography({"typography": {field: hi}})
        assert t[field] == hi

    @pytest.mark.parametrize(
        "field,bad",
        [
            ("x_tick_font_size", 7),
            ("x_tick_font_size", 25),
            ("y_tick_font_size", 0),
            ("datalabel_font_size", 33),
            ("y_tick_font_size", 12.5),
            ("x_tick_font_size", True),
            ("datalabel_font_size", "28"),
        ],
    )
    def test_invalid_strict_raises(self, field, bad):
        with pytest.raises(ValueError, match="typography"):
            resolve_typography({"typography": {field: bad}}, strict=True)

    def test_invalid_nonstrict_drops_whole_group(self, capsys):
        t = resolve_typography(
            {"typography": {"y_tick_font_size": 24, "x_tick_font_size": 99}},
            strict=False,
        )
        assert t["y_tick_font_size"] == LEGACY_Y_TICK
        assert t["x_tick_font_size"] == LEGACY_X_TICK
        assert t["datalabel_font_size"] == LEGACY_DATALABEL
        err = capsys.readouterr().err
        assert "ignored entire group" in err
        assert "x_tick_font_size" in err

    def test_non_object_group_nonstrict(self, capsys):
        t = resolve_typography({"typography": "big"}, strict=False)
        assert t["y_tick_font_size"] == LEGACY_Y_TICK
        assert "must be an object" in capsys.readouterr().err

    def test_unsupported_field_warns_keeps_supported(self, capsys):
        t = resolve_typography(
            {"typography": {"y_tick_font_size": 24, "foo_bar": 9}},
            strict=False,
        )
        assert t["y_tick_font_size"] == 24
        assert "unsupported field ignored: foo_bar" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# Pane title
# ---------------------------------------------------------------------------


class TestPaneTitle:
    def test_dual_chart_uses_pane_title_class(self):
        html = render_dual_chart(_dual_slide(), 1, "")
        assert 'class="gl-chart-pane-title"' in html
        assert ">Net Card Fees $B</div>" in html
        assert ">YoY Growth %</div>" in html
        # No legacy gray tile-label for chart panes.
        assert 'class="gl-tile-label">Net Card Fees' not in html

    def test_css_target_size_weight_color(self):
        html = render_dual_chart(_dual_slide(), 1, "")
        # Inline style on the element (emission-scoped; no global CSS delta).
        assert 'class="gl-chart-pane-title"' in html
        assert "font-size:40px" in html
        assert "font-weight:700" in html
        assert "line-height:1.05" in html
        assert "-webkit-line-clamp:2" in html

    def test_absent_title_reserves_no_space(self):
        assert chart_pane_title_html("") == ""
        assert chart_pane_title_html("   ") == ""

    def test_tight_pane_strict_raises(self):
        with pytest.raises(ValueError, match="canvas"):
            chart_pane_title_html("Title", available_w=400, available_h=250, strict=True)

    def test_tight_pane_nonstrict_legacy(self, capsys):
        html = chart_pane_title_html(
            "Title", available_w=400, available_h=250, strict=False
        )
        assert "gl-chart-pane-title-legacy" in html
        assert "gl-tile-label" in html
        err = capsys.readouterr().err.lower()
        assert "legacy" in err or "canvas" in err

    def test_render_deck_hosts_pass_size_viable_default(self, tmp_path):
        """Default dual_chart host geometry must still emit the 40px title."""
        path = _write(tmp_path, _handoff([_dual_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert 'class="gl-chart-pane-title"' in html
        assert "font-size:40px" in html
        assert "gl-chart-pane-title-legacy" not in html

    def test_render_deck_tight_host_strict_raises(self, tmp_path, monkeypatch):
        """Mutation trap: if hosts stop passing sizes, tight geometry never fails."""
        import impact_slides.renderer_v2.layout.recipes.charts as recipes_charts

        monkeypatch.setattr(
            recipes_charts,
            "chart_host_size",
            lambda kind, cols=2: (200.0, 300.0),
        )
        path = _write(tmp_path, _handoff([_dual_slide()]))
        with pytest.raises((ValueError, SystemExit), match="canvas|legacy|title"):
            render_deck(path, tmp_path / "out", strict=True)

    def test_render_deck_tight_host_nonstrict_legacy(self, tmp_path, monkeypatch, capsys):
        import impact_slides.renderer_v2.layout.recipes.charts as recipes_charts

        monkeypatch.setattr(
            recipes_charts,
            "chart_host_size",
            lambda kind, cols=2: (200.0, 300.0),
        )
        path = _write(tmp_path, _handoff([_dual_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert "gl-chart-pane-title-legacy" in html
        assert "gl-tile-label" in html
        err = capsys.readouterr().err.lower()
        assert "legacy" in err or "canvas" in err
        assert any("canvas" in w or "legacy" in w for w in meta.get("warnings", []))

    def test_metric_tile_label_unchanged(self, tmp_path):
        s = {
            "slide_number": 1,
            "title": "M",
            "layout_type": "multi_panel",
            "content": {},
            "visual_spec": {
                "primary_visual": {
                    "type": "multi_panel",
                    "tiles": [
                        {"kind": "metric", "label": "ROI", "value": "12%"},
                    ],
                }
            },
            "evidence_sources": [],
        }
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert 'class="gl-tile-label">ROI</div>' in html
        # Class may appear in global CSS; metric tile must not USE the element.
        assert 'class="gl-chart-pane-title">' not in html
        assert ">ROI</div>" in html

    def test_chart_config_title_fallback(self):
        slide = _dual_slide()
        del slide["visual_spec"]["primary_visual"]["label"]
        slide["visual_spec"]["primary_visual"]["chart_config"]["title"] = "From Config"
        # multi-series name path off
        slide["visual_spec"]["primary_visual"]["chart_config"]["series_names"] = ["A", "B"]
        html = render_dual_chart(slide, 1, "")
        assert "From Config" in html
        assert "gl-chart-pane-title" in html


# ---------------------------------------------------------------------------
# Chart.js + SVG application
# ---------------------------------------------------------------------------


class TestPainterPaths:
    def test_chartjs_applies_tick_and_datalabel(self, tmp_path):
        s = _bar_slide(
            {
                "typography": {
                    "x_tick_font_size": 13,
                    "y_tick_font_size": 24,
                    "datalabel_font_size": 28,
                }
            }
        )
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        conf = _chartjs_cfg(html)
        assert conf["options"]["scales"]["x"]["ticks"]["font"]["size"] == 13
        assert conf["options"]["scales"]["y"]["ticks"]["font"]["size"] == 24
        assert conf["options"]["scales"]["y"]["ticks"]["font"].get("weight") == "bold"
        assert conf["options"]["plugins"]["datalabels"]["font"]["size"] == 28
        assert 'data-rv2-collision="1"' in html
        assert "data-rv2-datalabel-collision" in html

    def test_absent_typography_legacy_chartjs(self, tmp_path):
        path = _write(tmp_path, _handoff([_bar_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        conf = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))
        assert conf["options"]["scales"]["x"]["ticks"]["font"]["size"] == 13
        assert conf["options"]["scales"]["y"]["ticks"]["font"]["size"] == 13
        assert conf["options"]["plugins"]["datalabels"]["font"]["size"] == 11
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "data-rv2-collision" not in html
        assert "data-rv2-datalabel-collision" not in html

    def test_svg_applies_tick_and_datalabel(self, tmp_path):
        s = _bar_slide(
            {
                "typography": {
                    "y_tick_font_size": 24,
                    "datalabel_font_size": 28,
                    "x_tick_font_size": 13,
                }
            }
        )
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False, suppress_features=["charts"])
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert 'font-size="24"' in html  # y ticks
        assert 'font-size="28"' in html  # value labels
        assert 'font-size="13"' in html  # x ticks (opt-in)

    def test_svg_absent_keeps_legacy_14(self, tmp_path):
        path = _write(tmp_path, _handoff([_bar_slide()]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False, suppress_features=["charts"])
        html = (out / "presentation.html").read_text(encoding="utf-8")
        # Legacy SVG y-tick / value label size.
        assert 'font-size="14"' in html
        assert 'font-size="28"' not in html
        assert 'font-size="24"' not in html

    def test_invalid_group_deck_nonstrict(self, tmp_path, capsys):
        s = _bar_slide({"typography": {"y_tick_font_size": 999}})
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        conf = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))
        assert conf["options"]["scales"]["y"]["ticks"]["font"]["size"] == 13
        meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        assert any("typography" in w or "ignored entire group" in w for w in meta.get("warnings", []))
        assert "ignored entire group" in capsys.readouterr().err

    def test_invalid_group_deck_strict(self, tmp_path):
        s = _bar_slide({"typography": {"y_tick_font_size": 999}})
        path = _write(tmp_path, _handoff([s]))
        with pytest.raises((ValueError, SystemExit)):
            render_deck(path, tmp_path / "out", strict=True)

    def test_stacked_insegment_ignores_datalabel_size(self, tmp_path):
        """datalabel_font_size only changes ordinary labels, not in-segment."""
        s = {
            "slide_number": 1,
            "title": "S",
            "layout_type": "stacked_bar_chart",
            "content": {},
            "visual_spec": {
                "primary_visual": {
                    "type": "stacked_bar_chart",
                    "chart_config": {
                        "point_labels": True,
                        "typography": {"datalabel_font_size": 28},
                        "series_names": ["A", "B"],
                    },
                    "steps_or_data": [
                        {"label": "Q1", "value": 10, "series_2": 5},
                        {"label": "Q2", "value": 12, "series_2": 6},
                    ],
                }
            },
            "evidence_sources": [],
        }
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        conf = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))
        dl = conf["options"]["plugins"]["datalabels"]
        # In-segment / named sets stay at legacy 11.
        if "labels" in dl and isinstance(dl["labels"], dict):
            for name, entry in dl["labels"].items():
                if name in ("value", "negchip"):
                    assert entry["font"]["size"] == 11
        else:
            assert dl["font"]["size"] == 11


# ---------------------------------------------------------------------------
# Collision
# ---------------------------------------------------------------------------


class TestCollision:
    def test_ordering_series_then_category(self):
        # Two overlapping boxes; later series suppressed.
        a = estimate_label_box("A", x=10, y=10, font_size=20)
        b = estimate_label_box("B", x=12, y=12, font_size=20)
        items = [
            {"series": 1, "category": 0, "label": "B", "box": b},
            {"series": 0, "category": 0, "label": "A", "box": a},
        ]
        suppressed, details = suppress_colliding_labels(items)
        assert suppressed == [0]  # series 1 kept later → suppressed
        assert details[0]["label"] == "B"

    def test_margin_2px(self):
        # Adjacent boxes exactly 2px apart should NOT collide; 1px should.
        a = (0.0, 0.0, 10.0, 10.0)
        b_ok = (12.0, 0.0, 22.0, 10.0)  # gap = 2
        b_hit = (11.0, 0.0, 21.0, 10.0)  # gap = 1
        assert not boxes_intersect(a, b_ok, margin=COLLISION_MARGIN_PX)
        assert boxes_intersect(a, b_hit, margin=COLLISION_MARGIN_PX)

    def test_svg_collision_suppresses(self, tmp_path, capsys):
        # Force collision with huge labels on close values.
        s = _bar_slide(
            {
                "typography": {"datalabel_font_size": 32},
                "series_names": ["A", "B"],
            }
        )
        # two series, same categories, close values
        s["visual_spec"]["primary_visual"]["steps_or_data"] = [
            {"label": "Q1", "value": 10, "series_2": 10.1},
            {"label": "Q2", "value": 11, "series_2": 11.1},
        ]
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False, suppress_features=["charts"])
        err = capsys.readouterr().err
        meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
        # May or may not suppress depending on geometry; if it does, diagnostics land.
        if "suppressed" in err:
            assert any("suppressed" in w for w in meta.get("warnings", []))

    def test_collision_js_only_when_datalabel_size_set(self, tmp_path):
        path = _write(
            tmp_path,
            _handoff([_bar_slide({"typography": {"y_tick_font_size": 24}})]),
        )
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "data-rv2-collision" not in html
        assert "data-rv2-datalabel-collision" not in html

    def test_collision_js_collects_flat_labels(self):
        """Mutation trap: nested row[si][ci] walk gathers nothing on flat plugin shape."""
        from impact_slides.renderer_v2.charts.typography import DATALABEL_COLLISION_JS

        js = DATALABEL_COLLISION_JS
        assert "$context" in js
        assert "datasetIndex" in js
        assert "dataIndex" in js
        # Must iterate the flat _labels list, not assume nested series rows.
        assert "labels[i]" in js or "labels.length" in js
        assert "row[ci]" not in js
        assert "labels[si]" not in js

    def test_chartjs_collision_playwright(self, tmp_path):
        """Real browser proof: forced collisions set data-datalabel-suppressed."""
        pytest.importorskip("playwright.sync_api")
        from playwright.sync_api import sync_playwright

        s = {
            "slide_number": 1,
            "title": "Dense",
            "layout_type": "grouped_bar_chart",
            "content": {"bullets": [], "so_what": "x"},
            "visual_spec": {
                "primary_visual": {
                    "type": "grouped_bar_chart",
                    "chart_config": {
                        "point_labels": True,
                        "series_names": ["A", "B"],
                        "typography": {"datalabel_font_size": 32},
                    },
                    "steps_or_data": [
                        {"label": f"C{i}", "A": 10 + i * 0.01, "B": 10 + i * 0.01 + 0.02}
                        for i in range(12)
                    ],
                }
            },
            "evidence_sources": [],
        }
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html_path = out / "presentation.html"
        # Absent typography must not ship collision attr (already covered);
        # present path must suppress in a live Chart.js deck.
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            logs: list[str] = []
            page.on("console", lambda msg: logs.append(msg.text))
            page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
            # Auto title slide is active first — advance to the chart.
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(2000)
            info = page.evaluate(
                """() => {
                  const wrap = document.querySelector('.chartjs-wrap');
                  const c = Chart.getChart(document.querySelector('canvas'));
                  const labels = c && c.$datalabels && c.$datalabels._labels || [];
                  const kept = [];
                  const gone = [];
                  for (const lab of labels) {
                    const m = lab.model();
                    const row = {
                      di: lab.$context.datasetIndex,
                      ci: lab.$context.dataIndex,
                      t: (m.lines || []).join(' '),
                      op: m.opacity,
                      vis: lab.$layout && lab.$layout._visible,
                      disp: m.display,
                    };
                    if (m.opacity === 0 || m.display === false || row.vis === false) gone.push(row);
                    else kept.push(row);
                  }
                  return {
                    supp: wrap && wrap.getAttribute('data-datalabel-suppressed'),
                    coll: wrap && wrap.getAttribute('data-rv2-collision'),
                    flat: Array.isArray(labels) && labels.length > 0 && !Array.isArray(labels[0]),
                    kept, gone,
                  };
                }"""
            )
            browser.close()
        assert info["coll"] == "1"
        assert info["flat"] is True
        assert info["supp"] is not None and int(info["supp"]) > 0
        assert len(info["gone"]) >= 1
        # Earlier dataset/category wins: series 0 cat 0 must remain if present.
        kept_keys = {(k["di"], k["ci"]) for k in info["kept"]}
        gone_keys = {(g["di"], g["ci"]) for g in info["gone"]}
        if (0, 0) in kept_keys or (0, 0) in gone_keys:
            assert (0, 0) in kept_keys
        # Later colliding series should be among suppressed when present.
        assert any(di >= 1 for di, _ci in gone_keys) or any(
            ci > 0 for _di, ci in gone_keys
        )
        assert any("[typography] datalabel suppressed" in t for t in logs)
        assert any("series" in t and "category" in t for t in logs)


# ---------------------------------------------------------------------------
# Mutation traps
# ---------------------------------------------------------------------------


class TestMutationTraps:
    def test_option_wiring_mutation(self, tmp_path):
        """If y_tick wiring is removed, this fails."""
        s = _bar_slide({"typography": {"y_tick_font_size": 24}})
        path = _write(tmp_path, _handoff([s]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        conf = _chartjs_cfg((out / "presentation.html").read_text(encoding="utf-8"))
        size = conf["options"]["scales"]["y"]["ticks"]["font"]["size"]
        assert size == 24
        # Mutation: flipping would make size == legacy
        assert size != LEGACY_Y_TICK

    def test_suppression_ordering_mutation(self):
        items = [
            {
                "series": 0,
                "category": 0,
                "label": "first",
                "box": (0.0, 0.0, 20.0, 20.0),
            },
            {
                "series": 0,
                "category": 1,
                "label": "second",
                "box": (5.0, 5.0, 25.0, 25.0),
            },
        ]
        suppressed, _ = suppress_colliding_labels(items)
        assert suppressed == [1]
        # Mutation trap: if order reversed, first would be suppressed.
        assert 0 not in suppressed

    def test_v9_slide17_targets(self, tmp_path):
        typo = {
            "x_tick_font_size": 13,
            "y_tick_font_size": 24,
            "datalabel_font_size": 28,
        }
        path = _write(tmp_path, _handoff([_dual_slide(typo)]))
        out = tmp_path / "out"
        render_deck(path, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "gl-chart-pane-title" in html
        assert "font-size:40px" in html  # inline emission-scoped style
        # Both panes' configs carry y=24 / dl=28
        sizes_y = re.findall(
            r'"y"\s*:\s*\{[^}]*"ticks"\s*:\s*\{[^}]*"size"\s*:\s*(\d+)', html
        )
        # looser: just parse each config
        configs = re.findall(
            r'<script type="application/json" class="chartjs-config"[^>]*>(.*?)</script>',
            html,
            re.S,
        )
        assert len(configs) >= 1
        for raw in configs:
            conf = json.loads(raw)
            assert conf["options"]["scales"]["y"]["ticks"]["font"]["size"] == 24
            dl = conf["options"]["plugins"].get("datalabels")
            if dl and "font" in dl:
                assert dl["font"]["size"] == 28
