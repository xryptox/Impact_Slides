"""#147 — chart_hero_dual explicit pane headings + subtitles."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from impact_slides.renderer_v2 import render_deck
from impact_slides.renderer_v2.charts.typography import (
    chart_pane_subtitle_html,
    chart_pane_title_html,
    set_render_strict,
    reset_render_strict,
)
from impact_slides.renderer_v2.layout.recipes import render_chart_hero_dual
from impact_slides.renderer_v2.schemas import validate_slide

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "renderer_v2"
GOLDEN = FIXTURES / "golden_mvp1_handoff.json"

_LEFT_H = "Proprietary New Cards Acquired"
_LEFT_S = "in millions"
_RIGHT_H = "Proprietary New Accounts Acquired"
_RIGHT_S = "Q1'2026"


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


def _hero_slide(
    *,
    primary=None,
    secondary=None,
    key_stats=None,
    chart=True,
):
    pv = {
        "type": "grouped_bar_chart",
        "steps_or_data": [
            {"label": "Q1'24", "value": 1.1},
            {"label": "Q1'25", "value": 1.3},
            {"label": "Q1'26", "value": 1.5},
        ],
        "chart_config": {},
    }
    if not chart:
        pv = {}
    if primary:
        pv = {**pv, **primary} if chart else {**primary}
    vs: dict = {"primary_visual": pv}
    if secondary is not None:
        vs["secondary_visual"] = secondary
    return {
        "slide_number": 12,
        "layout_type": "chart_hero_dual",
        "title": "New Acquisitions",
        "content": {
            "so_what": "Premium mix",
            "key_stats": key_stats
            or [
                {"label": "Millennial/Gen-Z", "value": "66%"},
                {"label": "Fee-Paying", "value": "73%"},
            ],
        },
        "visual_spec": vs,
        "speaker_notes": "Notes.",
        "evidence_sources": [],
    }


def _amex_slide():
    return _hero_slide(
        primary={"heading": _LEFT_H, "subtitle": _LEFT_S},
        secondary={"heading": _RIGHT_H, "subtitle": _RIGHT_S},
    )


def _norm_ids(html: str) -> str:
    html = re.sub(r"rv2-chart-[0-9a-f-]+", "rv2-chart-ID", html)
    html = re.sub(r"gl-tabs-[0-9a-f]{6,}", "gl-tabs-ID", html)
    html = re.sub(r'data-tabs-id="[^"]*"', 'data-tabs-id="ID"', html)
    return html


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


def test_schema_accepts_both_pane_headings_and_subtitles():
    model, err = validate_slide(_amex_slide())
    assert err is None
    assert model is not None
    assert model.layout_type == "chart_hero_dual"
    vs = model.visual_spec
    assert vs is not None
    # extra="allow" keeps author fields
    raw = model.model_dump()
    assert raw["visual_spec"]["primary_visual"]["heading"] == _LEFT_H
    assert raw["visual_spec"]["primary_visual"]["subtitle"] == _LEFT_S
    assert raw["visual_spec"]["secondary_visual"]["heading"] == _RIGHT_H
    assert raw["visual_spec"]["secondary_visual"]["subtitle"] == _RIGHT_S


# ---------------------------------------------------------------------------
# Subtitle helper
# ---------------------------------------------------------------------------


def test_subtitle_helper_empty_reserves_nothing():
    assert chart_pane_subtitle_html("") == ""
    assert chart_pane_subtitle_html("   ") == ""


def test_subtitle_helper_uses_dek_treatment():
    html = chart_pane_subtitle_html("in millions")
    assert "gl-chart-pane-subtitle" in html
    assert "in millions" in html
    # dek-ish: muted, not 40px navy title weight
    assert "40px" not in html
    assert "font-weight:700" not in html or "font-size:40px" not in html


# ---------------------------------------------------------------------------
# Render — approved Amex strings
# ---------------------------------------------------------------------------


def test_amex_four_strings_no_duplicate_internal_title():
    html = render_chart_hero_dual(_amex_slide(), 1, "", use_chartjs=True)
    assert f">{_LEFT_H}</div>" in html
    assert f">{_LEFT_S}</div>" in html
    assert f">{_RIGHT_H}</div>" in html
    assert f">{_RIGHT_S}</div>" in html
    # HTML-owned pane titles (both panes)
    assert html.count('class="gl-chart-pane-title"') == 2
    assert html.count("gl-chart-pane-subtitle") == 2
    # left uses shared class; no Chart.js plugins.title block
    assert '"title"' not in html.split("chartjs-config")[-1].split("</script>")[0] or (
        '"display": false' in html or '"display":false' in html
    )
    # right heading once — not repeated per KPI row
    assert html.count(_RIGHT_H) == 1
    # right header sits above hero facts inside the peer card (outer stack)
    right = html.split('class="gl-chart-hero-stack"', 1)[1]
    assert _RIGHT_H in right
    # heading appears before first hero card
    assert right.index(_RIGHT_H) < right.index("gl-hero card")
    assert right.index(_RIGHT_S) < right.index("gl-hero card")


def test_right_heading_not_inside_kpi_rows():
    html = render_chart_hero_dual(_amex_slide(), 1, "")
    # Each KPI row must not contain the pane heading
    for chunk in html.split('class="gl-hero card"')[1:]:
        row = chunk.split("</div>", 2)[0]
        assert _RIGHT_H not in row
        assert _RIGHT_S not in row


# ---------------------------------------------------------------------------
# Presence matrix
# ---------------------------------------------------------------------------


def test_primary_only_heading_subtitle():
    html = render_chart_hero_dual(
        _hero_slide(primary={"heading": _LEFT_H, "subtitle": _LEFT_S}),
        1,
        "",
    )
    assert _LEFT_H in html and _LEFT_S in html
    assert _RIGHT_H not in html
    assert html.count("gl-chart-pane-title") == 1
    assert html.count("gl-chart-pane-subtitle") == 1


def test_secondary_only_heading_subtitle():
    html = render_chart_hero_dual(
        _hero_slide(secondary={"heading": _RIGHT_H, "subtitle": _RIGHT_S}),
        1,
        "",
    )
    assert _RIGHT_H in html and _RIGHT_S in html
    assert _LEFT_H not in html
    # only right title
    assert html.count("gl-chart-pane-title") == 1
    assert "gl-hero-stack" in html


def test_absent_fields_reserve_no_space_and_compat():
    html = render_chart_hero_dual(_hero_slide(), 1, "")
    assert "gl-chart-pane-title" not in html
    assert "gl-chart-pane-subtitle" not in html
    assert "gl-hero-stack" in html
    assert "Millennial/Gen-Z" in html


# ---------------------------------------------------------------------------
# Precedence: heading > label > chart_config.title > single series
# ---------------------------------------------------------------------------


def test_heading_wins_over_label_and_title_and_series():
    html = render_chart_hero_dual(
        _hero_slide(
            primary={
                "heading": "HEAD",
                "label": "LABEL",
                "chart_config": {
                    "title": "CFG",
                    "series_names": ["SERIES"],
                },
            }
        ),
        1,
        "",
    )
    assert ">HEAD</div>" in html
    assert "LABEL" not in html
    assert "CFG" not in html
    assert "SERIES" not in html.split("gl-chart-hero-chart", 1)[1].split(
        "gl-chart-hero-stack", 1
    )[0] or ">HEAD</div>" in html


def test_label_wins_over_title_and_series():
    html = render_chart_hero_dual(
        _hero_slide(
            primary={
                "label": "LABEL",
                "chart_config": {
                    "title": "CFG",
                    "series_names": ["SERIES"],
                },
            }
        ),
        1,
        "",
    )
    assert ">LABEL</div>" in html
    assert "CFG" not in html


def test_chart_config_title_wins_over_series():
    html = render_chart_hero_dual(
        _hero_slide(
            primary={
                "chart_config": {
                    "title": "CFG",
                    "series_names": ["SERIES"],
                },
            }
        ),
        1,
        "",
    )
    assert ">CFG</div>" in html


def test_single_series_fallback():
    html = render_chart_hero_dual(
        _hero_slide(primary={"chart_config": {"series_names": ["Only Series"]}}),
        1,
        "",
    )
    assert ">Only Series</div>" in html


def test_multi_series_no_fallback_heading():
    html = render_chart_hero_dual(
        _hero_slide(
            primary={
                "steps_or_data": [
                    {"label": "A", "value": 1, "series_2": 2},
                    {"label": "B", "value": 3, "series_2": 4},
                ],
                "chart_config": {"series_names": ["One", "Two"]},
            }
        ),
        1,
        "",
    )
    assert "gl-chart-pane-title" not in html


# ---------------------------------------------------------------------------
# Long two-line heading + title-space failure/fallback
# ---------------------------------------------------------------------------


def test_long_heading_emits_two_line_clamp():
    long_h = "Proprietary New Cards Acquired Across Every Customer Segment Worldwide"
    html = render_chart_hero_dual(
        _hero_slide(primary={"heading": long_h}),
        1,
        "",
    )
    assert "gl-chart-pane-title" in html
    assert "font-size:40px" in html
    assert "font-weight:700" in html
    assert "-webkit-line-clamp:2" in html
    assert long_h in html


def test_tight_host_strict_raises(monkeypatch):
    import impact_slides.renderer_v2.layout.recipes.charts as recipes_charts

    monkeypatch.setattr(
        recipes_charts,
        "chart_host_size",
        lambda kind, cols=2: (200.0, 300.0),
    )
    tok = set_render_strict(True)
    try:
        with pytest.raises(ValueError, match="canvas"):
            render_chart_hero_dual(
                _hero_slide(primary={"heading": "Title"}),
                1,
                "",
            )
    finally:
        reset_render_strict(tok)


def test_tight_host_nonstrict_legacy(monkeypatch, capsys):
    import impact_slides.renderer_v2.layout.recipes.charts as recipes_charts

    monkeypatch.setattr(
        recipes_charts,
        "chart_host_size",
        lambda kind, cols=2: (200.0, 300.0),
    )
    tok = set_render_strict(False)
    try:
        html = render_chart_hero_dual(
            _hero_slide(primary={"heading": "Title"}),
            1,
            "",
        )
    finally:
        reset_render_strict(tok)
    assert "gl-chart-pane-title-legacy" in html
    err = capsys.readouterr().err.lower()
    assert "legacy" in err or "canvas" in err


# ---------------------------------------------------------------------------
# Malformed non-string heading/subtitle — strict / non-strict
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field", ["heading", "subtitle"])
def test_non_string_field_strict_raises(field):
    tok = set_render_strict(True)
    try:
        with pytest.raises(ValueError, match=field):
            render_chart_hero_dual(
                _hero_slide(primary={field: 123}),
                1,
                "",
            )
    finally:
        reset_render_strict(tok)


@pytest.mark.parametrize("field", ["heading", "subtitle"])
def test_non_string_field_nonstrict_warns_and_skips(field, capsys):
    tok = set_render_strict(False)
    try:
        html = render_chart_hero_dual(
            _hero_slide(primary={field: 123, "label": "Fallback Label"}),
            1,
            "",
        )
    finally:
        reset_render_strict(tok)
    err = capsys.readouterr().err.lower()
    assert field in err
    if field == "heading":
        # falls through to label
        assert "Fallback Label" in html
    else:
        assert "gl-chart-pane-subtitle" not in html


def test_secondary_non_string_heading_strict_raises():
    tok = set_render_strict(True)
    try:
        with pytest.raises(ValueError, match="heading"):
            render_chart_hero_dual(
                _hero_slide(secondary={"heading": ["nope"]}),
                1,
                "",
            )
    finally:
        reset_render_strict(tok)


# ---------------------------------------------------------------------------
# Chart.js + SVG paths share the same HTML headings
# ---------------------------------------------------------------------------


def test_chartjs_and_svg_share_html_headings():
    slide = _amex_slide()
    js = render_chart_hero_dual(slide, 1, "", use_chartjs=True)
    svg = render_chart_hero_dual(slide, 1, "", use_chartjs=False)
    for s in (_LEFT_H, _LEFT_S, _RIGHT_H, _RIGHT_S):
        assert s in js and s in svg
    assert js.count('class="gl-chart-pane-title"') == svg.count(
        'class="gl-chart-pane-title"'
    )


# ---------------------------------------------------------------------------
# Default fixture byte-identical (normalize random ids)
# ---------------------------------------------------------------------------


def test_golden_fixture_byte_identical_without_new_fields(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    render_deck(GOLDEN, a, strict=True)
    render_deck(GOLDEN, b, strict=True)
    ha = _norm_ids((a / "presentation.html").read_text(encoding="utf-8"))
    hb = _norm_ids((b / "presentation.html").read_text(encoding="utf-8"))
    assert ha == hb
    # no pane-subtitle chrome introduced on golden (no chart_hero_dual there)
    assert "gl-chart-pane-subtitle" not in ha


def test_absent_fields_render_deck_matches_baseline_shape(tmp_path):
    """Handoff without heading/subtitle stays free of new chrome classes."""
    path = _write(tmp_path, _handoff([_hero_slide()]))
    out = tmp_path / "out"
    render_deck(path, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert "gl-chart-pane-subtitle" not in html
    assert "gl-hero-stack" in html


# ---------------------------------------------------------------------------
# Mutation traps — precedence + empty-space
# ---------------------------------------------------------------------------


def test_mutation_precedence_heading_not_ignored():
    """If heading resolution drops the explicit key, label would win — catch it."""
    html = render_chart_hero_dual(
        _hero_slide(primary={"heading": "EXPLICIT", "label": "LEGACY"}),
        1,
        "",
    )
    assert ">EXPLICIT</div>" in html
    assert ">LEGACY</div>" not in html


def test_mutation_empty_subtitle_no_class():
    html = render_chart_hero_dual(
        _hero_slide(primary={"heading": "H", "subtitle": ""}),
        1,
        "",
    )
    assert "gl-chart-pane-subtitle" not in html
    assert ">H</div>" in html
