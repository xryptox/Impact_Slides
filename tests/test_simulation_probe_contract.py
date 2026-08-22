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

Plus DP-6 design-ledger probes (#233):
9. computed tick font-size below the 20px floor
10. computed tick font-weight below 600 (incl. CSS override of a 600 attribute)
11. zero tick texts / zero furniture matches are failures

Plus DP-6 extensions (#249):
12. stub column share above 45% of table width
13. support header cells missing band background or hairline borders
    (incl. fully transparent computed fills reported as rgba(0,0,0,0))
14. forbidden #0A7D55 among non-semantic series colors / missing authored sky_blue
15. metric-strip value font-size below 40px
16. bar occupancy (bar width / category pitch) below 0.5

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
    DESIGN_LEDGER_BAR_OCCUPANCY_SLIDES,
    DESIGN_LEDGER_FURNITURE,
    DESIGN_LEDGER_METRIC_FLOOR_SLIDES,
    DESIGN_LEDGER_PALETTE_SLIDES,
    DESIGN_LEDGER_STUB_RATIO_SLIDES,
    DESIGN_LEDGER_SUPPORT_CHROME_SLIDES,
    FORBIDDEN_SERIES_HEX,
    SKY_BLUE_HEX,
    ProbeError,
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
<section class="slide" data-slide-number="40" data-layout="design_ok">
  <div class="chart-plot" style="position:relative;width:200px;height:100px">
    <div class="chart-label-overlay">
      <svg class="chart-svg" width="200" height="100">
        <text x="40" y="90" font-size="20" font-weight="600">Q1</text>
        <text x="10" y="40" font-size="20" font-weight="600" font-variant-numeric="tabular-nums">10</text>
        <text x="100" y="20" font-size="16">Axis title</text>
        <text x="80" y="30" font-size="18" font-weight="600" data-placement="outside">$1.1</text>
      </svg>
    </div>
    <div class="support-table">G&S 7%</div>
    <div class="chart-annotation" data-annotation-id="leap">Leap Year Approx. (1%)</div>
  </div>
</section>
<section class="slide" data-slide-number="41" data-layout="design_small">
  <div class="chart-plot">
    <div class="chart-label-overlay">
      <svg class="chart-svg">
        <text x="40" y="90" font-size="14" font-weight="600">Q1</text>
      </svg>
    </div>
  </div>
</section>
<section class="slide" data-slide-number="42" data-layout="design_thin">
  <div class="chart-plot">
    <div class="chart-label-overlay">
      <svg class="chart-svg">
        <text x="40" y="90" font-size="20" font-weight="400">Q1</text>
      </svg>
    </div>
  </div>
</section>
<section class="slide" data-slide-number="43" data-layout="design_empty">
  <div class="chart-plot">
    <div class="chart-label-overlay">
      <svg class="chart-svg"></svg>
    </div>
  </div>
</section>
<section class="slide" data-slide-number="44" data-layout="design_css">
  <style>#shrink-tick {{ font-size: 14px !important; font-weight: 400 !important; }}</style>
  <div class="chart-plot">
    <div class="chart-label-overlay">
      <svg class="chart-svg">
        <text id="shrink-tick" x="40" y="90" font-size="20" font-weight="600">Q1</text>
      </svg>
    </div>
  </div>
</section>
<section class="slide" data-slide-number="45" data-layout="design_s21">
  <div class="chart-body" data-chart-type="combo">
    <div class="band-title chart-pane-title">
      <span>Capital Return & Common Shares Outstanding</span>
    </div>
    <table class="chart-semantic-table" data-semantic-table="1">
      <thead><tr><th>Category</th><th>Dividends</th><th>Common Shares Outstanding</th></tr></thead>
      <tbody><tr><th>Q1</th><td>0.6</td><td>682</td></tr></tbody>
    </table>
    <div class="outlined-support">ROE 35%</div>
  </div>
</section>
<section class="slide" data-slide-number="46" data-layout="design_s21_noline">
  <div class="chart-body" data-chart-type="combo">
    <div class="band-title chart-pane-title">
      <span>Capital Return & Common Shares Outstanding</span>
    </div>
    <table class="chart-semantic-table" data-semantic-table="1">
      <thead><tr><th>Category</th><th>Dividends</th><th>Share Repurchases</th></tr></thead>
      <tbody><tr><th>Q1</th><td>0.6</td><td>1.6</td></tr></tbody>
    </table>
    <div class="outlined-support">ROE 35%</div>
  </div>
</section>
<section class="slide" data-slide-number="50" data-layout="stub_ok">
  <table class="data-table" style="width:400px;table-layout:fixed">
    <colgroup><col style="width:120px"/><col style="width:140px"/><col style="width:140px"/></colgroup>
    <thead><tr><th class="stub">Metric</th><th>Q1</th><th>Q2</th></tr></thead>
    <tbody><tr><td class="stub">Revenue</td><td>1</td><td>2</td></tr></tbody>
  </table>
</section>
<section class="slide" data-slide-number="51" data-layout="stub_wide">
  <table class="data-table" style="width:400px;table-layout:fixed">
    <colgroup><col style="width:240px"/><col style="width:80px"/><col style="width:80px"/></colgroup>
    <thead><tr><th class="stub">Metric</th><th>Q1</th><th>Q2</th></tr></thead>
    <tbody><tr><td class="stub">Revenue</td><td>1</td><td>2</td></tr></tbody>
  </table>
</section>
<section class="slide" data-slide-number="52" data-layout="chrome_ok">
  <div class="support-table category-aligned" style="position:relative;height:60px;width:400px">
    <div class="support-cat-cell head" style="position:absolute;left:40px;top:0;width:80px;height:24px;
      background:#1B3A6B;color:#fff;border:1px solid #1B3A6B;box-sizing:border-box">G&S</div>
    <div class="support-cat-stub head" style="position:absolute;left:0;top:0;width:36px;height:24px;
      background:#1B3A6B;color:#fff;border:1px solid #1B3A6B;box-sizing:border-box">%</div>
  </div>
</section>
<section class="slide" data-slide-number="53" data-layout="chrome_plain">
  <div class="support-table category-aligned" style="position:relative;height:60px;width:400px">
    <div class="support-cat-cell head" style="position:absolute;left:40px;top:0;width:80px;height:24px;
      background:#ffffff;color:#000;border:0;box-sizing:border-box">G&S</div>
  </div>
</section>
<section class="slide" data-slide-number="61" data-layout="chrome_transparent">
  <div class="support-table category-aligned" style="position:relative;height:60px;width:400px">
    <div class="support-cat-cell head" style="position:absolute;left:40px;top:0;width:80px;height:24px;
      background:transparent;color:#000;border:1px solid #1B3A6B;box-sizing:border-box">G&S</div>
  </div>
</section>
<section class="slide" data-slide-number="54" data-layout="palette_ok">
  <canvas id="c54" width="200" height="100"></canvas>
</section>
<section class="slide" data-slide-number="55" data-layout="palette_forbid">
  <canvas id="c55" width="200" height="100"></canvas>
</section>
<section class="slide" data-slide-number="56" data-layout="palette_no_sky">
  <canvas id="c56" width="200" height="100"></canvas>
</section>
<section class="slide" data-slide-number="57" data-layout="metric_ok">
  <div class="metric-strip">
    <div class="metric-cell"><p class="metric-value" style="font-size:44px">3,400+</p></div>
    <div class="metric-cell"><p class="metric-value" style="font-size:44px">300+</p></div>
  </div>
</section>
<section class="slide" data-slide-number="58" data-layout="metric_small">
  <div class="metric-strip">
    <div class="metric-cell"><p class="metric-value" style="font-size:28px">3,400+</p></div>
  </div>
</section>
<section class="slide" data-slide-number="59" data-layout="bar_ok">
  <canvas id="c59" width="200" height="100"></canvas>
</section>
<section class="slide" data-slide-number="60" data-layout="bar_thin">
  <canvas id="c60" width="200" height="100"></canvas>
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
  function __seriesChart(colors, elements) {{
    var chart = __paintChart({{ elements: elements }});
    chart.data = {{
      labels: ['Q1', 'Q2'],
      datasets: colors.map(function (c, i) {{
        return {{
          label: 's' + i,
          backgroundColor: c,
          borderColor: c,
          data: [1, 2],
        }};
      }})
    }};
    var els = elements || [{{ x: 20, y: 40, skip: false, width: 60, height: 30 }}];
    chart.getDatasetMeta = function () {{
      return __paintMeta(false, els);
    }};
    chart.config = {{ type: 'bar' }};
    return chart;
  }}
  document.getElementById('c54').__fakeChart = __seriesChart(
    ['#1B3A6B', '#80C8FF'],
    [{{ x: 20, y: 40, skip: false, width: 60, height: 30 }}]
  );
  document.getElementById('c55').__fakeChart = __seriesChart(
    ['#0A7D55', '#1B3A6B'],
    [{{ x: 20, y: 40, skip: false, width: 60, height: 30 }}]
  );
  document.getElementById('c56').__fakeChart = __seriesChart(
    ['#1B3A6B', '#006FCF'],
    [{{ x: 20, y: 40, skip: false, width: 60, height: 30 }}]
  );
  // pitch = 180/2 = 90; bar 60 => ratio 0.667 >= 0.5
  document.getElementById('c59').__fakeChart = __seriesChart(
    ['#1B3A6B'],
    [{{ x: 20, y: 40, skip: false, width: 60, height: 30 }}]
  );
  // bar 20 => ratio 0.222 < 0.5
  document.getElementById('c60').__fakeChart = __seriesChart(
    ['#1B3A6B'],
    [{{ x: 20, y: 40, skip: false, width: 20, height: 30 }}]
  );
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


def test_design_ledger_furniture_covers_dp2_slides():
    assert set(DESIGN_LEDGER_FURNITURE) == {
        4, 5, 6, 8, 9, 10, 11, 12, 15, 17, 18, 19, 21, 24, 28,
    }
    for specs in DESIGN_LEDGER_FURNITURE.values():
        assert specs
        for spec in specs:
            assert spec["selector"].strip()
            assert spec["expected_text"].strip()


def test_measured_tick_styles_happy_includes_identity(page):
    row = measured_tick_styles(page, 40, "design_ok")
    assert row["slide_number"] == 40
    assert row["layout"] == "design_ok"
    assert row["tick_count"] == 2
    assert row["min_font_size_px"] >= 20
    assert row["min_font_weight"] >= 600
    assert row["ok"] is True


def test_measured_tick_styles_rejects_subfloor_size(page):
    """Mutation 9: 14px ticks must fail, not report success."""
    with pytest.raises(ProbeError, match=r"font-size|floor|20"):
        measured_tick_styles(page, 41, "design_small")


def test_measured_tick_styles_rejects_regular_weight(page):
    """Mutation 10: weight 400 must fail even when size is at floor."""
    with pytest.raises(ProbeError, match=r"font-weight|600"):
        measured_tick_styles(page, 42, "design_thin")


def test_measured_tick_styles_zero_ticks_fails(page):
    """Mutation 11: empty overlay is a probe failure, never a green ledger."""
    with pytest.raises(ProbeError, match=r"0 tick|no tick|matched 0"):
        measured_tick_styles(page, 43, "design_empty")


def test_measured_tick_styles_uses_computed_style_not_attribute(page):
    """Attribute 20/600 with computed 14/400 must fail (v12 regression class)."""
    with pytest.raises(ProbeError, match=r"font-size|font-weight|floor|20|600"):
        measured_tick_styles(page, 44, "design_css")


def test_furniture_presence_happy_includes_identity(page):
    row = furniture_presence(
        page, 40, "design_ok", ".support-table", expected_text="G&S"
    )
    assert row["slide_number"] == 40
    assert row["layout"] == "design_ok"
    assert row["count"] >= 1
    assert row["ok"] is True
    leap = furniture_presence(
        page, 40, "design_ok", "[data-annotation-id]", expected_text="Leap Year"
    )
    assert leap["ok"] is True


def test_design_ledger_s4_map_matches_fixture(page):
    """DP-2 s4 selectors must hit the fixture; zero matches stay a failure."""
    for spec in DESIGN_LEDGER_FURNITURE[4]:
        row = furniture_presence(
            page,
            40,
            "design_ok",
            spec["selector"],
            expected_text=spec["expected_text"],
        )
        assert row["ok"] is True
        assert row["count"] >= 1


def test_furniture_presence_empty_selector_fails(page):
    with pytest.raises(ProbeError, match="selector"):
        furniture_presence(page, 40, "design_ok", "")


def test_furniture_presence_wrong_layout_fails(page):
    with pytest.raises(ProbeError, match="layout"):
        furniture_presence(page, 40, _HERO, ".support-table")


def test_furniture_presence_zero_matches_fails(page):
    with pytest.raises(ProbeError, match=r"matched 0|0 elements"):
        furniture_presence(page, 40, "design_ok", ".definitely-absent-furniture")


def test_furniture_presence_missing_expected_text_fails(page):
    with pytest.raises(ProbeError, match=r"NOT IN DOM|text"):
        furniture_presence(
            page, 40, "design_ok", ".support-table", expected_text="NOT IN DOM"
        )


def test_design_ledger_s21_shares_line_hits_semantic_table(page):
    spec = DESIGN_LEDGER_FURNITURE[21][0]
    row = furniture_presence(
        page,
        45,
        "design_s21",
        spec["selector"],
        expected_text=spec["expected_text"],
    )
    assert row["ok"] is True
    assert row["count"] >= 1


def test_design_ledger_s21_shares_line_not_heading(page):
    spec = DESIGN_LEDGER_FURNITURE[21][0]
    with pytest.raises(ProbeError, match=r"expected text|matched 0|0 elements"):
        furniture_presence(
            page,
            46,
            "design_s21_noline",
            spec["selector"],
            expected_text=spec["expected_text"],
        )


def test_design_ledger_extension_slide_maps():
    """#249 maps pin the V1–V3 fidelity slides the sim must probe."""
    assert DESIGN_LEDGER_STUB_RATIO_SLIDES == (3, 16, 31, 32, 33, 34, 35, 36, 37)
    assert DESIGN_LEDGER_SUPPORT_CHROME_SLIDES == (4, 19)
    assert DESIGN_LEDGER_PALETTE_SLIDES[24]["require_sky_blue"] is False
    assert DESIGN_LEDGER_PALETTE_SLIDES[28]["require_sky_blue"] is True
    assert DESIGN_LEDGER_METRIC_FLOOR_SLIDES == (8, 12)
    assert DESIGN_LEDGER_BAR_OCCUPANCY_SLIDES == (28,)
    assert FORBIDDEN_SERIES_HEX.upper() == "#0A7D55"
    assert SKY_BLUE_HEX.upper() == "#80C8FF"


def test_measured_stub_ratio_happy(page):
    row = measured_stub_ratio(page, 50, "stub_ok")
    assert row["slide_number"] == 50
    assert row["max_stub_share"] <= 0.45
    assert row["ok"] is True


def test_measured_stub_ratio_rejects_wide_stub(page):
    """Mutation 12: stub > 45% of table width must fail."""
    with pytest.raises(ProbeError, match=r"stub share|0\.45|cap"):
        measured_stub_ratio(page, 51, "stub_wide")


def test_measured_support_chrome_happy(page):
    row = measured_support_chrome(page, 52, "chrome_ok")
    assert row["head_count"] >= 1
    assert row["ok"] is True
    assert row["heads"][0]["border_top_px"] >= 1.0


def test_measured_support_chrome_rejects_plain_header(page):
    """Mutation 13: white header without hairline is not authored chrome."""
    with pytest.raises(ProbeError, match=r"band background|hairline|border"):
        measured_support_chrome(page, 53, "chrome_plain")


def test_measured_support_chrome_rejects_transparent_band(page):
    """Mutation 13b: transparent fill must not pass as a painted band."""
    with pytest.raises(ProbeError, match=r"band background"):
        measured_support_chrome(page, 61, "chrome_transparent")


def test_measured_series_palette_happy(page):
    row = measured_series_palette(page, 54, "palette_ok", require_sky_blue=True)
    assert row["has_sky_blue"] is True
    assert FORBIDDEN_SERIES_HEX.upper() not in row["colors"]
    assert row["ok"] is True


def test_measured_series_palette_rejects_forbidden_green(page):
    """Mutation 14a: #0A7D55 on a non-semantic series must fail."""
    with pytest.raises(ProbeError, match=r"forbidden|0A7D55|#0A7D55"):
        measured_series_palette(page, 55, "palette_forbid")


def test_measured_series_palette_requires_authored_sky(page):
    """Mutation 14b: missing authored sky_blue must fail when required."""
    with pytest.raises(ProbeError, match=r"sky_blue|80C8FF"):
        measured_series_palette(page, 56, "palette_no_sky", require_sky_blue=True)


def test_measured_metric_value_styles_happy(page):
    row = measured_metric_value_styles(page, 57, "metric_ok")
    assert row["min_font_size_px"] >= 40
    assert row["ok"] is True


def test_measured_metric_value_styles_rejects_subfloor(page):
    """Mutation 15: metric value below 40px must fail."""
    with pytest.raises(ProbeError, match=r"font-size|floor|40"):
        measured_metric_value_styles(page, 58, "metric_small")


def test_measured_bar_occupancy_happy(page):
    row = measured_bar_occupancy(page, 59, "bar_ok")
    assert row["min_occupancy"] >= 0.5
    assert row["ok"] is True


def test_measured_bar_occupancy_rejects_thin_bars(page):
    """Mutation 16: bar width / pitch below 0.5 must fail."""
    with pytest.raises(ProbeError, match=r"occupancy|0\.5|floor"):
        measured_bar_occupancy(page, 60, "bar_thin")
