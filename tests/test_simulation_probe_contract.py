"""Contract tests for scripts/simulation_probe.py (#137).

Catches the four bad-probe mutations from the v9 simulation:
1. off-by-one / missing data-slide-number target
2. wrong expected data-layout
3. zero-match selector treated as successful absence
4. pre-bind options.plugins.datalabels instead of painted model lines

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
<script>
// Fake Chart registry: options.plugins.datalabels is display-only (pre-bind
// trap), while $datalabels._labels[*].model().lines holds painted strings.
window.Chart = {{
  getChart: function (canvas) {{
    return canvas && canvas.__fakeChart ? canvas.__fakeChart : null;
  }}
}};
(function () {{
  var canvas = document.getElementById('c12');
  canvas.__fakeChart = {{
    options: {{ plugins: {{ datalabels: {{ display: true }} }} }},
    $datalabels: {{
      _labels: [
        {{ model: function () {{ return {{ lines: ['$0.9'] }}; }} }},
        {{ model: function () {{ return {{ lines: ['$1.1'] }}; }} }}
      ]
    }}
  }};
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


def test_painted_datalabels_timeout_is_probe_error(page):
    """Readiness wait must fail clearly when Chart labels never appear."""
    with pytest.raises(ProbeError, match=r"painted labels did not become ready on slide 21.*chart_index=0"):
        painted_datalabel_lines(page, 21, "bare_canvas", timeout_ms=300)
