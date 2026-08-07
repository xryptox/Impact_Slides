"""Contract tests for scripts/simulation_probe.py (#137, #146).

Catches the four bad-probe mutations from the v9 simulation:
1. off-by-one / missing data-slide-number target
2. wrong expected data-layout
3. zero-match selector treated as successful absence
4. pre-bind options.plugins.datalabels instead of painted model lines

Plus paint-ready Chart.js geometry (#146):
5. Chart object present with a 0×0 canvas
6. nonzero canvas with degenerate chartArea
7. degenerate dataset element geometry
8. capture before the next animation frame settles

Playwright is optional in CI (importorskip); must run locally when installed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from playwright.sync_api import sync_playwright  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from simulation_probe import (  # noqa: E402
    ProbeError,
    activate_slide,
    count_in_slide,
    painted_datalabel_lines,
    wait_for_paint_ready_charts,
)

# Runtime-assembled so gen_layout_index word-boundary search does not treat
# this file as a layout/recipe reference for the dual-metric hero layout.
_HERO = "chart_" + "hero_dual"
_LINE = "line_" + "chart"


_FIXTURE_HTML = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>probe contract</title></head>
<body>
<section class="slide active" data-slide-number="11" data-layout="{_LINE}">
  <h1>line slide 11</h1>
  <div class="gl-line-only">line body</div>
</section>
<section class="slide" data-slide-number="12" data-layout="{_HERO}">
  <h1>dual hero slide 12</h1>
  <div class="gl-hero-stack">hero frame</div>
  <canvas id="c12" width="200" height="100"></canvas>
</section>
<section class="slide" data-slide-number="20" data-layout="inset_demo">
  <div class="gl-inset">inset 20</div>
</section>
<section class="slide" data-slide-number="21" data-layout="bare_canvas">
  <canvas id="c21" width="200" height="100"></canvas>
</section>
<section class="slide" data-slide-number="22" data-layout="late_chart">
  <canvas id="c22" width="200" height="100"></canvas>
</section>
<section class="slide" data-slide-number="30" data-layout="geom_zero">
  <canvas id="c30" width="200" height="100"></canvas>
</section>
<section class="slide" data-slide-number="31" data-layout="geom_area">
  <canvas id="c31" width="200" height="100"></canvas>
</section>
<section class="slide" data-slide-number="32" data-layout="geom_elements">
  <canvas id="c32" width="200" height="100"></canvas>
</section>
<section class="slide" data-slide-number="33" data-layout="geom_raf">
  <canvas id="c33" width="200" height="100"></canvas>
</section>
<section class="slide" data-slide-number="34" data-layout="geom_late">
  <canvas id="c34" width="200" height="100"></canvas>
</section>
<section class="slide" data-slide-number="35" data-layout="geom_dead">
  <canvas id="c35" width="200" height="100"></canvas>
</section>
<section class="slide" data-slide-number="36" data-layout="geom_ready">
  <canvas id="c36" width="200" height="100"></canvas>
</section>
<script>
// Fake Chart registry: options.plugins.datalabels is display-only (pre-bind
// trap), while $datalabels._labels[*].model().lines holds painted strings.
window.Chart = {{
  getChart: function (canvas) {{
    return canvas && canvas.__fakeChart ? canvas.__fakeChart : null;
  }}
}};
function __paintMeta(hidden, elements) {{
  return {{
    hidden: !!hidden,
    data: elements,
  }};
}}
function __paintChart(opts) {{
  opts = opts || {{}};
  var w = ('width' in opts) ? opts.width : 200;
  var h = ('height' in opts) ? opts.height : 100;
  var area = opts.chartArea || {{ left: 10, top: 10, right: 190, bottom: 90, width: 180, height: 80 }};
  var elements = opts.elements || [{{ x: 20, y: 40, skip: false, width: 12, height: 30 }}];
  var hidden = !!opts.hidden;
  return {{
    width: w,
    height: h,
    chartArea: area,
    data: {{ datasets: [{{ data: [1, 2] }}] }},
    getDatasetMeta: function () {{ return __paintMeta(hidden, elements); }},
    options: {{ plugins: {{ datalabels: {{ display: true }} }} }},
    $datalabels: opts.$datalabels || {{
      _labels: [
        {{ model: function () {{ return {{ lines: ['$0.9'] }}; }} }},
        {{ model: function () {{ return {{ lines: ['$1.1'] }}; }} }}
      ]
    }}
  }};
}}
(function () {{
  var canvas = document.getElementById('c12');
  canvas.__fakeChart = __paintChart({{}});
  // Permanent degenerate: Chart object exists, geometry never settles.
  document.getElementById('c35').__fakeChart = __paintChart({{
    width: 0, height: 0,
    chartArea: {{ left: 0, top: 0, right: 0, bottom: 0, width: 0, height: 0 }},
    elements: [{{ x: 0, y: 0, skip: false }}]
  }});
  // Already paint-ready multi-check baseline.
  document.getElementById('c36').__fakeChart = __paintChart({{}});
}})();
</script>
</body></html>
"""


@pytest.fixture(scope="module")
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 1280, "height": 720})
        pg.set_content(_FIXTURE_HTML)
        yield pg
        browser.close()


def test_activate_happy_path_includes_identity(page):
    row = activate_slide(page, 12, _HERO)
    assert row["slide_number"] == 12
    assert row["layout"] == _HERO


def test_missing_slide_number_fails(page):
    """Mutation 1: off-by-one / missing target must not silently measure elsewhere."""
    with pytest.raises(ProbeError, match="no slide|data-slide-number"):
        activate_slide(page, 99, _HERO)


def test_wrong_expected_layout_fails(page):
    """Mutation 2: slide 12 is hero, not line — wrong layout is a probe failure."""
    with pytest.raises(ProbeError, match="layout"):
        activate_slide(page, 12, _LINE)


def test_zero_match_selector_fails_not_zero_count(page):
    """Mutation 3: zero matches are inconclusive failure, never count==0 success."""
    with pytest.raises(ProbeError, match="matched 0|0 elements"):
        count_in_slide(page, 12, _HERO, ".definitely-absent-probe-node")


def test_count_in_slide_happy_includes_identity(page):
    row = count_in_slide(page, 12, _HERO, ".gl-hero-stack")
    assert row["count"] == 1
    assert row["slide_number"] == 12
    assert row["layout"] == _HERO


def test_painted_datalabels_not_options_only(page):
    """Mutation 4: must read painted model lines, not options.plugins.datalabels."""
    row = painted_datalabel_lines(page, 12, _HERO)
    assert row["slide_number"] == 12
    assert row["layout"] == _HERO
    assert "$0.9" in row["lines"]
    assert "$1.1" in row["lines"]
    # Options-only trap still present on the fake chart — helper must not
    # have used it as the label source (options has no label strings).
    assert row["options_datalabels_keys"] == ["display"]
    assert "$0.9" not in row["options_datalabels_keys"]


def test_painted_datalabels_waits_for_late_chart(page):
    """Readiness wait must survive labels arriving after activation."""
    page.evaluate(
        """() => setTimeout(() => {
          document.getElementById('c22').__fakeChart = {
            $datalabels: {_labels: [{model: () => ({lines: ['$2.2']})}]}
          };
        }, 100)"""
    )
    assert painted_datalabel_lines(page, 22, "late_chart", timeout_ms=1000)["lines"] == ["$2.2"]


def test_painted_datalabels_timeout_is_probe_error(page):
    """Readiness wait must fail clearly when Chart labels never appear."""
    with pytest.raises(ProbeError, match=r"painted labels did not become ready on slide 21.*chart_index=0"):
        painted_datalabel_lines(page, 21, "bare_canvas", timeout_ms=300)


def test_paint_ready_rejects_zero_geometry(page):
    """#146 mutation: Chart instance alone with 0×0 canvas is not ready.

    chartArea + elements stay non-degenerate so only the width/height
    predicate rejects (mutation A).
    """
    page.evaluate(
        """() => {
          document.getElementById('c30').__fakeChart = __paintChart({
            width: 0, height: 0,
            chartArea: {left:10,top:10,right:190,bottom:90,width:180,height:80},
            elements: [{x:20,y:40,skip:false,width:12,height:30}]
          });
        }"""
    )
    with pytest.raises(ProbeError, match=r"paint-ready.*slide 30.*geom_zero"):
        wait_for_paint_ready_charts(page, 30, "geom_zero", timeout_ms=300)


def test_paint_ready_rejects_degenerate_chart_area(page):
    """#146 mutation: nonzero canvas with degenerate chartArea is not ready."""
    page.evaluate(
        """() => {
          document.getElementById('c31').__fakeChart = __paintChart({
            width: 200, height: 100,
            chartArea: {left:5,top:5,right:5,bottom:5,width:0,height:0},
            elements: [{x:5,y:5,skip:false,width:10,height:20}]
          });
        }"""
    )
    with pytest.raises(ProbeError, match=r"paint-ready.*slide 31.*geom_area"):
        wait_for_paint_ready_charts(page, 31, "geom_area", timeout_ms=300)


def test_paint_ready_rejects_degenerate_dataset_elements(page):
    """#146 mutation: visible dataset with only degenerate elements is not ready."""
    page.evaluate(
        """() => {
          document.getElementById('c32').__fakeChart = __paintChart({
            width: 200, height: 100,
            chartArea: {left:10,top:10,right:190,bottom:90,width:180,height:80},
            elements: [{x:20,y:40,skip:false,width:0,height:0}]
          });
        }"""
    )
    with pytest.raises(ProbeError, match=r"paint-ready.*slide 32.*geom_elements"):
        wait_for_paint_ready_charts(page, 32, "geom_elements", timeout_ms=300)


def test_paint_ready_requires_animation_frame_settle(page):
    """#146 mutation D: readiness must hold across one animation frame.

    Chart looks ready on the first synchronous observation of each poll, then
    collapses on the rAF recheck. A single-check waiter would falsely succeed;
    the real helper must keep failing / time out.
    """
    page.evaluate(
        """() => {
          var chart = __paintChart({});
          var good = chart.chartArea;
          var bad = {left:0,top:0,right:0,bottom:0,width:0,height:0};
          // First chartArea read in a turn is good; subsequent reads are bad
          // until the next macrotask. Sync check passes, rAF recheck fails.
          var seen = 0;
          Object.defineProperty(chart, 'chartArea', {
            configurable: true,
            get: function () {
              seen += 1;
              return (seen % 2 === 1) ? good : bad;
            }
          });
          document.getElementById('c33').__fakeChart = chart;
        }"""
    )
    with pytest.raises(ProbeError, match=r"paint-ready.*slide 33.*geom_raf"):
        wait_for_paint_ready_charts(page, 33, "geom_raf", timeout_ms=600)


def test_paint_ready_waits_for_delayed_geometry(page):
    """Delayed 0×0 → settled geometry must transition to ready."""
    page.evaluate(
        """() => {
          document.getElementById('c34').__fakeChart = __paintChart({
            width: 0, height: 0,
            chartArea: {left:0,top:0,right:0,bottom:0,width:0,height:0},
            elements: [{x:0,y:0,skip:false}]
          });
          setTimeout(() => {
            document.getElementById('c34').__fakeChart = __paintChart({});
          }, 120);
        }"""
    )
    row = wait_for_paint_ready_charts(page, 34, "geom_late", timeout_ms=2000)
    assert row["slide_number"] == 34
    assert row["layout"] == "geom_late"
    assert row["charts"][0]["width"] > 0
    assert row["charts"][0]["height"] > 0
    assert row["charts"][0]["chart_area"]["width"] > 0


def test_paint_ready_timeout_includes_identity(page):
    """Permanently degenerate chart times out with identity-rich ProbeError."""
    with pytest.raises(ProbeError, match=r"paint-ready.*slide 35.*geom_dead"):
        wait_for_paint_ready_charts(page, 35, "geom_dead", timeout_ms=300)


def test_paint_ready_happy_includes_identity(page):
    row = wait_for_paint_ready_charts(page, 36, "geom_ready")
    assert row["slide_number"] == 36
    assert row["layout"] == "geom_ready"
    assert row["chart_count"] == 1
    assert row["charts"][0]["width"] > 0
    assert row["charts"][0]["chart_area"]["width"] > 0
