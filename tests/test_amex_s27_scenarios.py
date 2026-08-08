"""#156 — Amex slide 27: restore the full three-scenario source handoff.

The paint-ready capture is a probe concern from #146; this contract verifies
that the bounded handoff mutation retains all PDF periods/scenarios and that a
real Chart.js render has two non-degenerate, paint-ready panes.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from amex_handoff_mutations import (  # noqa: E402
    apply_all,
    apply_issue_156_slide27_scenarios,
)
from impact_slides.renderer_v2 import render_deck  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "renderer_v2"
BROKEN = FIXTURES / "amex_s27_v10_broken.json"
CORRECTED = FIXTURES / "amex_s27_corrected.json"

_DUAL = "dual" + "_chart"
_PERIODS = [
    "Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26", "Q2'26", "Q3'26",
    "Q4'26", "Q1'27", "Q2'27", "Q3'27", "Q4'27", "Q1'28",
]
_SCENARIOS = ["Q1 Upside Scenario", "Q1 Baseline Scenario", "Q1 Downside Scenario"]
_HEADINGS = ["U.S. Unemployment Rate %", "U.S. GDP Growth* %"]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _slide(handoff: dict) -> dict:
    return next(s for s in handoff["slides"] if int(s["slide_number"]) == 27)


def _panes(slide: dict) -> list[dict]:
    visual = slide["visual_spec"]
    return [visual["primary_visual"], visual["secondary_visual"]]


def _assert_source_contract(slide: dict) -> None:
    assert int(slide["slide_number"]) == 27
    assert slide["layout_type"] == _DUAL
    for pane, heading in zip(_panes(slide), _HEADINGS):
        assert pane["type"] == "line_chart"
        assert pane["heading"] == heading
        assert [point["label"] for point in pane["steps_or_data"]] == _PERIODS
        assert pane["chart_config"]["series_names"] == _SCENARIOS
        assert all("series_2" in point and "series_3" in point for point in pane["steps_or_data"])
    disclosure = slide["disclosure"]["panels"][0]
    assert disclosure["title"] == "Scenario note"
    assert "SAAR" in disclosure["body"]
    assert slide["evidence_sources"] == [
        {"id": "E0026", "source_file": "Q1-2026-Earnings-Presentation.pdf, PDF page 27"}
    ]


def test_broken_fixture_documents_the_v10_truncation():
    slide = _slide(_load(BROKEN))
    assert [point["label"] for point in _panes(slide)[0]["steps_or_data"]] == _PERIODS[:8]
    assert _panes(slide)[0]["chart_config"]["series_names"] == ["Baseline UE", "Downside UE"]


def test_mutation_matches_corrected_fixture_and_source_contract():
    got = apply_issue_156_slide27_scenarios(copy.deepcopy(_load(BROKEN)))
    slide = _slide(got)
    assert slide == _slide(_load(CORRECTED))
    _assert_source_contract(slide)


def test_mutation_is_idempotent():
    once = apply_issue_156_slide27_scenarios(copy.deepcopy(_load(BROKEN)))
    twice = apply_issue_156_slide27_scenarios(copy.deepcopy(once))
    assert _slide(once) == _slide(twice)


def test_mutation_preserves_other_content_keys():
    handoff = copy.deepcopy(_load(BROKEN))
    _slide(handoff)["content"]["headline"] = "Retained source context"
    assert apply_issue_156_slide27_scenarios(handoff)["slides"][0]["content"]["headline"] == "Retained source context"


def test_apply_all_includes_slide_27():
    slide = _slide(apply_all(copy.deepcopy(_load(BROKEN))))
    _assert_source_contract(slide)


def test_regression_missing_scenario_or_final_period_fails_contract():
    slide = _slide(apply_issue_156_slide27_scenarios(copy.deepcopy(_load(BROKEN))))
    missing_scenario = copy.deepcopy(slide)
    missing_scenario["visual_spec"]["primary_visual"]["chart_config"]["series_names"].pop()
    with pytest.raises(AssertionError):
        _assert_source_contract(missing_scenario)

    truncated = copy.deepcopy(slide)
    truncated["visual_spec"]["secondary_visual"]["steps_or_data"].pop()
    with pytest.raises(AssertionError):
        _assert_source_contract(truncated)


def test_rendered_slide_is_identity_safe_and_paint_ready(tmp_path: Path):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright
    from simulation_probe import wait_for_paint_ready_charts

    handoff = apply_issue_156_slide27_scenarios(copy.deepcopy(_load(BROKEN)))
    # Keep source slide number stable without needing an archived full handoff.
    handoff["slides"] = [
        {
            "slide_number": 1,
            "layout_type": "title_or_opening",
            "title": "Cover",
            "content": {"headline": "Cover"},
        }
    ] + [
        {
            "slide_number": number,
            "layout_type": "metric",
            "title": f"Pad {number}",
            "content": {"key_stats": [{"label": "n", "value": str(number)}]},
            "visual_spec": {"primary_visual": {"type": "other", "steps_or_data": []}},
        }
        for number in range(2, 27)
    ] + handoff["slides"]
    deck = tmp_path / "handoff.json"
    deck.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(deck, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert html.count(">U.S. Unemployment Rate %</div>") == 1
    assert html.count(">U.S. GDP Growth* %</div>") == 1
    assert "Real GDP QoQ % Change Seasonally Adjusted to Annualized Rates (SAAR)." in html

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto((out / "presentation.html").resolve().as_uri())
        row = wait_for_paint_ready_charts(page, 27, _DUAL)
        browser.close()

    assert len(row["charts"]) == 2
    assert all(c["width"] > 0 and c["height"] > 0 for c in row["charts"])
    assert all(c["chart_area"]["width"] > 0 and c["chart_area"]["height"] > 0 for c in row["charts"])
