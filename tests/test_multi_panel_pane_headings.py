"""#158 — multi_panel chart tiles: shared pane heading/subtitle, no duplicate totals."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from impact_slides.renderer_v2 import render_deck
from impact_slides.renderer_v2.charts.typography import (
    chart_pane_headings_html,
    resolve_pane_heading,
    resolve_pane_subtitle,
)
from impact_slides.renderer_v2.layout.dispatch import render_slide
from impact_slides.renderer_v2.schemas import validate_slide

# Split layout tokens so gen_layout_index word-boundary search does not
# treat this file as a layout/recipe reference.
_MULTI = "multi" + "_panel"
_STACKED = "stacked_bar" + "_chart"
_COVER = "title_or_opening"


def _handoff(slides: list[dict]) -> dict:
    """Deck with a cover so normalize_handoff does not rewrite body layouts."""
    cover = {
        "slide_number": 1,
        "layout_type": _COVER,
        "title": "Cover",
        "content": {"headline": "Cover", "subtitle": ""},
    }
    body = [dict(s) for s in slides]
    out_slides = [cover]
    for i, s in enumerate(body, start=2):
        s["slide_number"] = i
        out_slides.append(s)
    return {
        "presentation": {"title": "multi_panel pane headings #158"},
        "slides": out_slides if body else [cover],
    }


def _write(tmp_path: Path, handoff: dict) -> Path:
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")
    return path


def _funding_steps() -> list:
    return [
        ["Quarter", "Deposits", "Unsecured", "Short-term"],
        ["Q4'25", "72", "21", "7"],
        ["Q1'26", "72", "21", "7"],
    ]


def _deposit_steps() -> list:
    return [
        ["Quarter", "Savings", "Third Party CDs", "Sweep", "Checking"],
        ["Q4'25", "81", "10", "7", "2"],
        ["Q1'26", "82", "10", "6", "2"],
    ]


def _side_callout_cfg(**extra) -> dict:
    cfg = {
        "stacked": True,
        "stack_totals": True,
        "stack_total_labels": ["$151", "$157"],
        "exterior_segment_names": True,
        "segment_name_gutter": 150,
        "show_legend": False,
        "show_y_axis": False,
        "side_callout": {
            "value": "92% FDIC",
            "label": ["insured at", "Q1'26"],
            "placement": "right",
            "skin": "tall",
        },
        **extra,
    }
    return cfg


def _slide28_corrected(*, with_top_total: bool = False) -> dict:
    """Canonical corrected Amex slide-28 shape (post-#158)."""
    funding = {
        "kind": "chart",
        "chart_type": _STACKED,
        "label": "Funding Mix",
        "subtitle": "$ in billions",
        "steps_or_data": _funding_steps(),
        "chart_config": {
            "stacked": True,
            "stack_totals": True,
            "stack_total_labels": ["$210", "$219"],
            "exterior_segment_names": True,
            "segment_name_gutter": 150,
            "show_legend": False,
            "show_y_axis": False,
            "series_names": ["Deposits", "Unsecured", "Short-term"],
            "series_colors": ["#00175A", "#006FCF", "#B8BFC9"],
        },
    }
    deposit = {
        "kind": "chart",
        "chart_type": _STACKED,
        "label": "Deposit Programs",
        "subtitle": "$ in billions",
        "badge": "92% of deposits FDIC insured*",
        "steps_or_data": _deposit_steps(),
        "chart_config": _side_callout_cfg(
            series_names=["Savings", "Third Party CDs", "Sweep", "Checking"],
            series_colors=["#00175A", "#006FCF", "#5B6B9A", "#B8BFC9"],
        ),
    }
    if with_top_total:
        funding["top_total"] = "$210B · $219B"
        deposit["top_total"] = "$151B · $157B"
    return {
        "slide_number": 28,
        "layout_type": _MULTI,
        "title": "Funding and Deposits",
        "content": {"subtitle": "$ in billions", "so_what": ""},
        "visual_spec": {
            "primary_visual": {
                "type": _MULTI,
                "tiles": [funding, deposit],
            }
        },
        "speaker_notes": "Funding mix + deposit programs.",
    }


def _multi_section(html: str) -> str:
    """Return the multi_panel section tag (identity via data-layout)."""
    m = re.search(
        rf'<section\b[^>]*\bdata-layout="{re.escape(_MULTI)}"[^>]*>',
        html,
    )
    assert m, f"no section data-layout={_MULTI}"
    return m.group(0)


def test_resolve_helpers_accept_tile_shape():
    tile = {"heading": "Funding Mix", "subtitle": "$ in billions", "label": "legacy"}
    assert resolve_pane_heading(tile) == "Funding Mix"
    assert resolve_pane_subtitle(tile) == "$ in billions"
    tile2 = {"label": "Deposit Programs", "subtitle": "$ in billions"}
    assert resolve_pane_heading(tile2) == "Deposit Programs"


def test_heading_beats_label_on_tile():
    tile = {"heading": "Funding Mix", "label": "WRONG"}
    assert resolve_pane_heading(tile) == "Funding Mix"


def test_schema_allows_tile_heading_subtitle_and_top_total():
    slide = _slide28_corrected(with_top_total=True)
    slide["visual_spec"]["primary_visual"]["tiles"][0]["heading"] = "Funding Mix"
    validated, err = validate_slide(slide)
    assert err is None and validated is not None
    raw = validated.model_dump()
    t0 = raw["visual_spec"]["primary_visual"]["tiles"][0]
    assert t0["heading"] == "Funding Mix"
    assert t0["subtitle"] == "$ in billions"
    assert t0["top_total"] == "$210B · $219B"


def test_slide28_renders_pane_heading_and_subtitle_only(tmp_path):
    path = _write(tmp_path, _handoff([_slide28_corrected()]))
    out = tmp_path / "out"
    render_deck(path, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")

    section = _multi_section(html)
    assert "data-slide-number=" in section

    assert html.count('class="gl-chart-pane-title"') == 2
    assert html.count("gl-chart-pane-subtitle") == 2
    assert ">Funding Mix</div>" in html
    assert ">Deposit Programs</div>" in html
    assert html.count(">$ in billions</div>") == 2

    # No pseudo-title totals
    assert "$210B · $219B" not in html
    assert "$151B · $157B" not in html
    assert 'class="gl-tile-top-total"' not in html
    assert 'class="gl-tile-ir-total"' not in html
    assert ">$210B · $219B<" not in html

    # Stack totals remain the dollar furniture (Chart.js path)
    assert '"$210"' in html and '"$219"' in html
    assert '"$151"' in html and '"$157"' in html

    # #138 callout + exterior names preserved
    assert "92% FDIC" in html
    assert "insured at" in html
    assert "Q1'26" in html
    assert 'class="gl-tile-badge"' not in html
    assert "92% of deposits FDIC insured*" not in html
    assert "chart-side-callout" in html


def test_slide28_svg_path_same_heading_subtitle_semantics(tmp_path):
    path = _write(tmp_path, _handoff([_slide28_corrected()]))
    out = tmp_path / "out_svg"
    render_deck(path, out, strict=False, suppress_features=["charts"])
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert html.count('class="gl-chart-pane-title"') == 2
    assert html.count("gl-chart-pane-subtitle") == 2
    assert "$210B · $219B" not in html
    assert "$151B · $157B" not in html
    # SVG stack totals (explicit stack_total_labels, Chart.js parity)
    assert html.count("vbar-stack-total") >= 4
    assert ">$210</text>" in html and ">$219</text>" in html
    assert ">$151</text>" in html and ">$157</text>" in html
    assert "92% FDIC" in html
    assert 'data-chartjs="1"' not in html


def test_legitimate_top_total_still_renders(tmp_path):
    """#90 slot must remain — this ticket must not globally delete top_total."""
    s = _slide28_corrected(with_top_total=True)
    # Drop callout so badge/top_total chrome is visible on a simple tall card.
    s["visual_spec"]["primary_visual"]["tiles"] = [
        {
            "kind": "chart",
            "chart_type": _STACKED,
            "label": "Funding Mix",
            "subtitle": "$ in billions",
            "top_total": "$148B",
            "steps_or_data": _funding_steps(),
            "chart_config": {
                "stacked": True,
                "stack_totals": True,
                "stack_total_labels": ["$210", "$219"],
                "show_legend": False,
            },
        }
    ]
    path = _write(tmp_path, _handoff([s]))
    out = tmp_path / "out"
    render_deck(path, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert "gl-tile-top-total" in html and "$148B" in html
    assert 'class="gl-chart-pane-title"' in html
    assert "gl-chart-pane-subtitle" in html
    assert "$148B ·" not in html  # not the slide-28 pseudo form


def test_heading_precedence_over_label(tmp_path):
    s = _slide28_corrected()
    s["visual_spec"]["primary_visual"]["tiles"][0]["heading"] = "Funding Mix"
    s["visual_spec"]["primary_visual"]["tiles"][0]["label"] = "IGNORE ME"
    html = render_slide(s, total=1, notes="", active=True)
    assert ">Funding Mix</div>" in html
    assert "IGNORE ME" not in html


def test_empty_subtitle_reserves_no_space():
    html = chart_pane_headings_html("Funding Mix", "")
    assert "gl-chart-pane-title" in html
    assert "gl-chart-pane-subtitle" not in html


def test_absent_fields_keep_legacy_compat(tmp_path):
    s = {
        "slide_number": 2,
        "layout_type": _MULTI,
        "title": "Legacy",
        "visual_spec": {
            "primary_visual": {
                "type": _MULTI,
                "tiles": [
                    {
                        "kind": "chart",
                        "chart_type": _STACKED,
                        "label": "Legacy Pane",
                        "steps_or_data": _funding_steps(),
                        "chart_config": {"stacked": True},
                    }
                ],
            }
        },
    }
    path = _write(tmp_path, _handoff([s]))
    out = tmp_path / "out"
    render_deck(path, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert ">Legacy Pane</div>" in html
    assert "gl-chart-pane-subtitle" not in html


@pytest.mark.parametrize("bad", [123, [], {"x": 1}])
def test_malformed_subtitle_non_strict_drops(tmp_path, bad, capsys):
    s = _slide28_corrected()
    s["visual_spec"]["primary_visual"]["tiles"][0]["subtitle"] = bad
    path = _write(tmp_path, _handoff([s]))
    out = tmp_path / "out"
    render_deck(path, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    # One valid deposit subtitle remains; funding drops bad subtitle.
    assert html.count("gl-chart-pane-subtitle") == 1
    err = capsys.readouterr().err
    assert "subtitle" in err.lower() or "must be a string" in err


def test_mutation_trap_removing_subtitle_emission_fails(tmp_path):
    """Adversarial: corrected slide must emit pane subtitles (not only titles)."""
    path = _write(tmp_path, _handoff([_slide28_corrected()]))
    out = tmp_path / "out"
    render_deck(path, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    # If multi_panel only used chart_pane_title_html, subtitles vanish.
    assert "gl-chart-pane-subtitle" in html
    assert html.count("$ in billions") >= 2
