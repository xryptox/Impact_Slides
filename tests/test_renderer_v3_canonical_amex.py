"""Canonical 44-slide Amex corpus (#196 / D54/D126/D314)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import render_deck, validate_handoff

FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "renderer_v3"
    / "canonical_amex_handoff_v1.json"
)

D314_LAYOUTS = {
    1: "opening_cover",
    2: "narrative",
    3: "period_comparison",
    4: "single_chart",
    5: "single_chart",
    6: "dual_chart",
    7: "comparison_cards",
    8: "single_chart",
    9: "single_chart",
    10: "single_chart",
    11: "single_chart",
    12: "chart_hero_dual",
    13: "single_chart",
    14: "dual_chart",
    15: "single_chart",
    16: "data_table",
    17: "dual_chart",
    18: "chart_hero_dual",
    19: "single_chart",
    20: "period_comparison",
    21: "chart_hero_dual",
    22: "metric_overview",
    23: "section_divider",
    24: "single_chart",
    25: "data_table",
    26: "data_table",
    27: "dual_chart",
    28: "dual_chart",
    29: "narrative",
    30: "narrative",
    31: "annex_table",
    32: "grouped_annex_table",
    33: "annex_table",
    34: "annex_table",
    35: "annex_table",
    36: "annex_table",
    37: "annex_table",
    38: "legal_notice",
    39: "legal_notice",
    40: "legal_notice",
    41: "legal_notice",
    42: "legal_notice",
    43: "legal_notice",
    44: "closing_cover",
}


@pytest.fixture(scope="module")
def handoff() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_exists_and_has_44_slides(handoff: dict) -> None:
    assert FIXTURE.is_file()
    assert len(handoff["slides"]) == 44
    assert handoff["meta"]["handoff_schema_version"] == 1


def test_d314_worksheet_compositions(handoff: dict) -> None:
    by_n = {s["slide_number"]: s for s in handoff["slides"]}
    assert set(by_n) == set(range(1, 45))
    for n, layout in D314_LAYOUTS.items():
        assert by_n[n]["layout_type"] == layout, n


def test_sections_evidence_and_no_operational_notes(handoff: dict) -> None:
    sec_ids = [s["section_id"] for s in handoff["sections"]]
    assert sec_ids == ["earnings", "appendix", "legal"]
    reg = handoff["evidence_registry"]
    assert len(reg) == 44
    assert all(k.startswith("amex-q1-2026-p") for k in reg)
    assert {e["source_name"] for e in reg.values()} == {
        "American Express Q1 2026 Earnings Presentation"
    }
    for s in handoff["slides"]:
        notes = s.get("speaker_notes")
        assert not notes, f"slide {s['slide_number']} must omit operational notes"
        assert s.get("evidence_ids"), s["slide_number"]


def test_slide6_source_claim_and_slide21_capital_summary(handoff: dict) -> None:
    s6 = next(s for s in handoff["slides"] if s["slide_number"] == 6)
    blob = json.dumps(s6)
    assert "6 percentage" in blob
    assert s6["layout_type"] == "dual_chart"

    s21 = next(s for s in handoff["slides"] if s["slide_number"] == 21)
    assert s21["layout_type"] == "chart_hero_dual"
    assert s21["payload"]["hero_visual"]["heading"] == "Capital Summary"


def test_strict_validate_clean(handoff: dict) -> None:
    result = validate_handoff(handoff, strict=True)
    assert result.deck is not None
    assert len(result.deck.slides) == 44
    assert not any(e.severity == "error" for e in result.events)


def test_strict_render_chartjs_and_svg_clean(tmp_path: Path) -> None:
    out_js = tmp_path / "chartjs"
    out_svg = tmp_path / "svg"
    out_js.mkdir()
    out_svg.mkdir()

    render_deck(FIXTURE, out_js, strict=True)
    meta_js = json.loads((out_js / "run_meta.json").read_text(encoding="utf-8"))
    assert meta_js["status"] == "clean"
    assert meta_js["ok"] is True
    assert meta_js["slide_count"] == 44
    assert meta_js["severity_counts"].get("error", 0) == 0
    assert meta_js["severity_counts"].get("warning", 0) == 0

    html = (out_js / "presentation.html").read_text(encoding="utf-8")
    assert html.count('data-slide-number="') == 44
    assert "Capital Summary" in html
    assert "6 percentage" in html

    # SVG-only via public CLI flag path used by publication options.
    from impact_slides.renderer_v3.cli import main as cli_main
    import sys

    rc = cli_main(
        [
            "--handoff",
            str(FIXTURE),
            "--out",
            str(out_svg),
            "--svg-only",
        ]
    )
    assert rc == 0
    meta_svg = json.loads((out_svg / "run_meta.json").read_text(encoding="utf-8"))
    assert meta_svg["status"] == "clean"
    assert meta_svg["ok"] is True
    assert meta_svg["slide_count"] == 44


def test_mutation_drops_capital_summary_heading(handoff: dict) -> None:
    """Adversarial: corpus identity requires authored Capital Summary on slide 21."""
    s21 = next(s for s in handoff["slides"] if s["slide_number"] == 21)
    assert s21["payload"]["hero_visual"]["heading"] == "Capital Summary"
    mutated = json.loads(json.dumps(handoff))
    m21 = next(s for s in mutated["slides"] if s["slide_number"] == 21)
    del m21["payload"]["hero_visual"]["heading"]
    from impact_slides.renderer_v3 import RendererValidationError

    with pytest.raises(RendererValidationError):
        validate_handoff(mutated, strict=True)


def test_mutation_wrong_slide_count_fails(handoff: dict) -> None:
    mutated = json.loads(json.dumps(handoff))
    mutated["slides"] = mutated["slides"][:40]
    # Dropping slides leaves unused evidence / sections.
    from impact_slides.renderer_v3 import RendererValidationError

    with pytest.raises(RendererValidationError):
        validate_handoff(mutated, strict=True)
