"""Handoff contract for Amex slides 13–14 vertical-bar semantics (#148).

Pins the bounded handoff mutation (not renderer defaults):
- slide 13 = grouped vertical bars (not line_chart)
- slide 14 = dual vertical-bar panes in PDF order
  left  = 30+ Days Past Due @ ~1.3%
  right = Net Write-Off Rates @ ~2%

Identity-safe evidence uses data-slide-number + data-layout only.
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from amex_handoff_mutations import apply_issue_148_bar_semantics  # noqa: E402
from impact_slides.renderer_v2.layout.dispatch import render_slide  # noqa: E402
from impact_slides.renderer_v2.schemas import validate_slide  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "renderer_v2"
BROKEN = FIXTURES / "amex_s13_s14_v10_broken.json"
CORRECTED = FIXTURES / "amex_s13_s14_corrected.json"

# Split layout tokens so gen_layout_index word-boundary search does not
# treat this file as a layout/recipe reference.
_GROUPED = "grouped_bar" + "_chart"
_DUAL = "dual" + "_chart"
_LINE = "line" + "_chart"

_S13_VALUES = {
    "Q1'25": {"Total Balances": 7.0, "Billed Business": 6.0},
    "Q2'25": {"Total Balances": 6.0, "Billed Business": 7.0},
    "Q3'25": {"Total Balances": 7.0, "Billed Business": 8.0},
    "Q4'25": {"Total Balances": 7.0, "Billed Business": 8.0},
    "Q1'26": {"Total Balances": 7.0, "Billed Business": 9.0},
}
_S14_LEFT = [1.3, 1.3, 1.3, 1.3, 1.3]
_S14_RIGHT = [2.1, 2.0, 1.9, 2.1, 2.0]
_S14_LEFT_HEADING = "30+ Days Past Due"
_S14_RIGHT_HEADING = "Net Write-Off Rates"
_CATEGORIES = ["Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _by_number(handoff: dict, n: int) -> dict:
    for s in handoff["slides"]:
        if int(s["slide_number"]) == n:
            return s
    raise AssertionError(f"missing slide_number={n}")


def _section_attrs(html: str, slide_number: int) -> dict[str, str]:
    pat = rf'<section\b[^>]*\bdata-slide-number="{slide_number}"[^>]*>'
    m = re.search(pat, html)
    assert m, f"no section data-slide-number={slide_number}"
    tag = m.group(0)
    layout = re.search(r'\bdata-layout="([^"]+)"', tag)
    assert layout, f"missing data-layout on slide {slide_number}: {tag}"
    return {"data-slide-number": str(slide_number), "data-layout": layout.group(1)}


def _chartjs_dataset_values(html: str) -> list[list[float]]:
    """Pull numeric dataset data arrays from embedded Chart.js configs."""
    out: list[list[float]] = []
    for m in re.finditer(r'"data"\s*:\s*\[([^\]]*)\]', html):
        raw = m.group(1).strip()
        if not raw:
            continue
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        try:
            vals = [float(p) for p in parts]
        except ValueError:
            continue
        if vals:
            out.append(vals)
    return out


def _assert_no_line_marks(html: str) -> None:
    assert _LINE not in html
    assert '"type": "line"' not in html
    assert '"type":"line"' not in html
    assert "polyline" not in html.lower()


def test_broken_fixture_still_documents_v10_defect():
    """Guard: the v10 baseline fixture must keep the defect we correct."""
    broken = _load(BROKEN)
    s13, s14 = _by_number(broken, 13), _by_number(broken, 14)
    assert s13["layout_type"] == _LINE
    assert s13["visual_spec"]["primary_visual"]["type"] == _LINE
    assert s14["layout_type"] == _DUAL
    assert s14["visual_spec"]["primary_visual"]["type"] == _LINE
    assert s14["visual_spec"]["secondary_visual"]["type"] == _LINE
    # Swapped pane semantics in v10.
    assert "write-off" in s14["visual_spec"]["primary_visual"]["chart_config"][
        "series_names"
    ][0].lower()
    assert "past due" in s14["visual_spec"]["secondary_visual"]["chart_config"][
        "series_names"
    ][0].lower()


def test_mutation_matches_corrected_fixture_and_pdf_semantics():
    broken = _load(BROKEN)
    expected = _load(CORRECTED)
    got = apply_issue_148_bar_semantics(copy.deepcopy(broken))

    s13, e13 = _by_number(got, 13), _by_number(expected, 13)
    s14, e14 = _by_number(got, 14), _by_number(expected, 14)

    assert s13["layout_type"] == _GROUPED == e13["layout_type"]
    assert s13["visual_spec"]["primary_visual"]["type"] == _GROUPED
    assert s13["layout_type"] != _LINE

    assert s14["layout_type"] == _DUAL == e14["layout_type"]
    pv, sv = s14["visual_spec"]["primary_visual"], s14["visual_spec"]["secondary_visual"]
    assert pv["type"] == _GROUPED
    assert sv["type"] == _GROUPED
    assert pv["heading"] == _S14_LEFT_HEADING
    assert sv["heading"] == _S14_RIGHT_HEADING
    assert pv["heading"] != sv["heading"]

    # Values + category order unchanged vs PDF/source series.
    steps13 = s13["visual_spec"]["primary_visual"]["steps_or_data"]
    assert [p["label"] for p in steps13] == _CATEGORIES
    for p in steps13:
        assert p["values"] == _S13_VALUES[p["label"]]

    left_vals = [float(p["value"]) for p in pv["steps_or_data"]]
    right_vals = [float(p["value"]) for p in sv["steps_or_data"]]
    assert [p["label"] for p in pv["steps_or_data"]] == _CATEGORIES
    assert [p["label"] for p in sv["steps_or_data"]] == _CATEGORIES
    assert left_vals == _S14_LEFT
    assert right_vals == _S14_RIGHT
    # Heading/value semantics: left is the flat 1.3% series, not ~2%.
    assert left_vals != right_vals
    assert all(v == pytest.approx(1.3) for v in left_vals)
    assert max(right_vals) < 2.5 and min(right_vals) > 1.5

    # Colors preserved / attached.
    assert s13["visual_spec"]["primary_visual"]["chart_config"]["series_colors"] == [
        "#00175A",
        "#006FCF",
    ]
    assert pv["chart_config"]["series_colors"] == ["#00175A"]
    assert sv["chart_config"]["series_colors"] == ["#006FCF"]

    assert s13 == e13
    assert s14 == e14


def test_mutation_is_idempotent():
    broken = _load(BROKEN)
    once = apply_issue_148_bar_semantics(copy.deepcopy(broken))
    twice = apply_issue_148_bar_semantics(copy.deepcopy(once))
    assert once == twice


@pytest.mark.parametrize("use_chartjs", [True, False], ids=["chartjs", "svg"])
def test_render_identity_and_bar_marks(use_chartjs: bool):
    handoff = apply_issue_148_bar_semantics(copy.deepcopy(_load(BROKEN)))
    evidence: list[dict] = []

    for n, expected_layout in ((13, _GROUPED), (14, _DUAL)):
        slide = _by_number(handoff, n)
        model, err = validate_slide(slide)
        assert model is not None, err
        html = render_slide(
            slide, total=44, notes="", active=True, use_chartjs=use_chartjs
        )
        attrs = _section_attrs(html, n)
        assert attrs["data-layout"] == expected_layout
        evidence.append(attrs)
        _assert_no_line_marks(html)

        if use_chartjs:
            assert '"type": "bar"' in html or '"type":"bar"' in html
            datasets = _chartjs_dataset_values(html)
            assert datasets, f"no chart datasets on slide {n}"
            if n == 13:
                # Two series × five quarters.
                assert len(datasets) >= 2
                flat = {round(v, 5) for ds in datasets[:2] for v in ds}
                assert flat == {6.0, 7.0, 8.0, 9.0}
            else:
                assert len(datasets) >= 2
                assert datasets[0] == _S14_LEFT
                assert datasets[1] == _S14_RIGHT
                assert _S14_LEFT_HEADING in html
                assert _S14_RIGHT_HEADING in html
                assert html.find(_S14_LEFT_HEADING) < html.find(_S14_RIGHT_HEADING)
        else:
            # SVG vertical bars are <rect>; connecting line paths must not dominate.
            assert html.count("<rect") >= (10 if n == 13 else 10)
            if n == 14:
                assert _S14_LEFT_HEADING in html
                assert _S14_RIGHT_HEADING in html
                assert html.find(_S14_LEFT_HEADING) < html.find(_S14_RIGHT_HEADING)

    # Required evidence fields for #148 acceptance.
    assert evidence == [
        {"data-slide-number": "13", "data-layout": _GROUPED},
        {"data-slide-number": "14", "data-layout": _DUAL},
    ]


def test_regression_line_chart_or_swapped_panes_fail_contract():
    """Mutation-style proof: bad authoring is rejected by the contract checks."""
    handoff = apply_issue_148_bar_semantics(copy.deepcopy(_load(BROKEN)))
    s13 = _by_number(handoff, 13)
    s14 = _by_number(handoff, 14)

    bad_line = copy.deepcopy(s13)
    bad_line["layout_type"] = _LINE
    bad_line["visual_spec"]["primary_visual"]["type"] = _LINE
    html = render_slide(bad_line, total=44, notes="", use_chartjs=True)
    attrs = _section_attrs(html, 13)
    assert attrs["data-layout"] == _LINE  # renderer faithfully paints bad handoff
    with pytest.raises(AssertionError):
        assert attrs["data-layout"] == _GROUPED

    swapped = copy.deepcopy(s14)
    swapped["visual_spec"]["primary_visual"], swapped["visual_spec"]["secondary_visual"] = (
        copy.deepcopy(s14["visual_spec"]["secondary_visual"]),
        copy.deepcopy(s14["visual_spec"]["primary_visual"]),
    )
    html = render_slide(swapped, total=44, notes="", use_chartjs=True)
    assert html.find(_S14_RIGHT_HEADING) < html.find(_S14_LEFT_HEADING)
    with pytest.raises(AssertionError):
        assert html.find(_S14_LEFT_HEADING) < html.find(_S14_RIGHT_HEADING)

    mismatched = copy.deepcopy(s14)
    mismatched["visual_spec"]["primary_visual"]["heading"] = _S14_LEFT_HEADING
    mismatched["visual_spec"]["primary_visual"]["steps_or_data"] = [
        {"label": lab, "value": v} for lab, v in zip(_CATEGORIES, _S14_RIGHT)
    ]
    html = render_slide(mismatched, total=44, notes="", use_chartjs=True)
    ds = _chartjs_dataset_values(html)
    with pytest.raises(AssertionError):
        assert ds[0] == _S14_LEFT
