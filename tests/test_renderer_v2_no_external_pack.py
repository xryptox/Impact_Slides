"""Guards after deleting the machine-local Boardroom charts pack."""
from __future__ import annotations

import inspect
import re

from impact_slides.renderer_v2 import charts
from impact_slides.renderer_v2.layouts import CHART_LAYOUTS


def test_charts_has_no_pack_loader():
    src = inspect.getsource(charts)
    assert "_find_pack_path" not in src
    assert "_load_pack" not in src
    assert "Path.home" not in src
    assert "chart_css" not in src
    assert re.search(r"\b_PACK\b", src) is None


def test_is_chart_layout_covers_catalog_only():
    for lt in CHART_LAYOUTS:
        assert charts.is_chart_layout(lt) is True
        assert charts.is_chart_layout(lt.upper()) is True
    assert charts.is_chart_layout("not_a_chart") is False
    assert charts.is_chart_layout("") is False


def test_icon_grid_uses_gl_fallback_tiles():
    slide = {
        "slide_number": 1,
        "title": "T",
        "layout_type": "icon_grid",
        "visual_spec": {
            "primary_visual": {
                "steps_or_data": [
                    {"label": "Growth", "body": "up"},
                    {"label": "Globe", "body": "wide"},
                    {"label": "Users", "body": "many"},
                ]
            }
        },
        "content": {},
    }
    html = charts.build_icon_grid_html(slide)
    assert "chart-empty" not in html
    assert "gl-grid" in html
    assert "gl-card" in html
    assert html.count("icon-tile") == 3
    assert 'href="#ic-growth"' in html
    assert 'href="#ic-globe"' in html
    assert 'href="#ic-users"' in html
    assert "tile-title" in html
    # pack markup must not return
    assert "icon-grid cols-" not in html
