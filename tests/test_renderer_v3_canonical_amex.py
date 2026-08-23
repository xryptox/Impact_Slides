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
    assert s21["payload"]["hero"]["heading"] == "Capital Summary"


def test_strict_validate_clean(handoff: dict) -> None:
    result = validate_handoff(handoff, strict=True)
    assert result.deck is not None
    assert len(result.deck.slides) == 44
    assert not any(e.severity == "error" for e in result.events)


def test_strict_render_chartjs_and_svg_clean(tmp_path: Path, handoff: dict) -> None:
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
    s7 = html[html.index('data-slide-number="7"') : html.index('data-slide-number="8"')]
    assert "circular-dual-metric" in s7
    assert s7.count("metric-circle") == 6
    for token in ("50%", "5%", "10x", "20%", "10%", "2x", "21%", "11%"):
        assert token in s7
    from html import unescape

    visible = unescape(html).replace("<wbr>", "")
    s32 = html.split('id="slide-32"', 1)[1].split("<section", 1)[0]
    s32_vis = unescape(s32).replace("<wbr>", "")
    assert s32_vis.count("Q1'26 Reported") >= 2
    assert s32_vis.count("FX-Adj.*") >= 2
    assert "Q\u2026" not in s32_vis and "F\u2026" not in s32_vis
    from impact_slides.renderer_v3.plan import LEGAL_BODY_PX, LEGAL_TITLE_PX

    by_n = {s["slide_number"]: s for s in json.loads(FIXTURE.read_text(encoding="utf-8"))["slides"]}
    part1_title = by_n[38]["payload"]["title"]
    assert part1_title == "Cautionary Note Regarding Forward-Looking Statements"
    assert "\u2014 continued" not in html and "— continued" not in html
    for n in range(38, 44):
        chunk = html.split(f'id="slide-{n}"', 1)[1].split("<section", 1)[0]
        heading = chunk.split("<h1", 1)[1].split("</h1>", 1)[0]
        assert f"font-size:{LEGAL_TITLE_PX}px" in heading
        assert unescape(heading).replace("<wbr>", "").endswith(part1_title)
        body = chunk.split('legal-body">', 1)[1].split("</div>", 1)[0]
        paras = by_n[n]["payload"]["paragraphs"]
        assert body.count("<ul") == len(paras)
        assert body.count("<li") == len(paras)
        assert f"font-size:{LEGAL_BODY_PX}px" in body
        assert "<p" not in body

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

    from impact_slides.renderer_v3.plan import plan_deck

    planned = plan_deck(validate_handoff(handoff, strict=True).deck, strict=True)
    s3 = next(sp for sp in planned.surfaces if sp.slide_number == 3 and sp.table_paint)
    stub_w = s3.table_paint["col_widths"][0]
    table_w = sum(s3.table_paint["col_widths"])
    assert stub_w / table_w <= 0.45
    assert s3.table_paint["ellipsized"] is False
    assert not any(
        sp.table_paint.get("ellipsized")
        for sp in planned.surfaces
        if sp.table_paint
    )
    assert not any(e.severity != "info" for e in planned.events)
    for sn in (24, 28):
        for sp in planned.surfaces:
            if sp.slide_number != sn or not sp.chart_paint:
                continue
            geom = sp.chart_paint["geometry"]
            n_cat = len(sp.chart_paint.get("categories") or [])
            if n_cat > 6:
                continue
            assert geom["thickness"] / geom["category_pitch"] >= 0.50, (
                sn,
                sp.surface_id,
                geom["thickness"],
                geom["category_pitch"],
            )

    tick_roles = ("category_ticks", "value_ticks")
    value_roles = ("ordinary_values", "segment_labels", "stack_totals")
    for plan in meta_js["plans"]:
        sizes = plan.get("role_sizes") or {}
        if not any(role in sizes for role in tick_roles + value_roles):
            continue
        for role in tick_roles:
            if role in sizes:
                assert sizes[role] >= 20, (plan["surface_id"], role, sizes[role])
        for role in value_roles:
            if role in sizes:
                assert sizes[role] >= 18, (plan["surface_id"], role, sizes[role])


def test_mutation_drops_capital_summary_heading(handoff: dict) -> None:
    """Adversarial: corpus identity requires authored Capital Summary on slide 21."""
    s21 = next(s for s in handoff["slides"] if s["slide_number"] == 21)
    assert s21["payload"]["hero"]["heading"] == "Capital Summary"
    mutated = json.loads(json.dumps(handoff))
    m21 = next(s for s in mutated["slides"] if s["slide_number"] == 21)
    del m21["payload"]["hero"]["heading"]
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

def test_dual_and_hero_equal_band_and_stage_fit(handoff: dict) -> None:
    """Composite body surfaces enter geometry fit (equal dual panes; stage stack)."""
    from impact_slides.renderer_v3.plan import (
        DESIGN_STAGE_H,
        PAD_BOTTOM,
        PAD_TOP,
        plan_deck,
    )

    result = validate_handoff(handoff, strict=True)
    plan = plan_deck(result.deck, strict=True)
    stage = DESIGN_STAGE_H - PAD_TOP - PAD_BOTTOM
    by_slide: dict[int, list] = {}
    for sp in plan.surfaces:
        by_slide.setdefault(sp.slide_number, []).append(sp)

    dual_sns = [n for n, lt in D314_LAYOUTS.items() if lt == "dual_chart"]
    for sn in dual_sns:
        panes = [s for s in by_slide[sn] if s.role.endswith("_chart")]
        assert len(panes) == 2, sn
        assert panes[0]._box_h == panes[1]._box_h, (
            sn,
            panes[0]._box_h,
            panes[1]._box_h,
        )
        assert not any(s._overflow for s in by_slide[sn]), sn

    hero_sns = [n for n, lt in D314_LAYOUTS.items() if lt == "chart_hero_dual"]
    for sn in dual_sns + hero_sns:
        sps = by_slide[sn]
        fixed = sum(
            s._box_h + s._chrome_h
            for s in sps
            if s.role in {
                "title",
                "subtitle",
                "takeaway",
                "disclosure",
                "source_footer",
            }
        )
        if sn in dual_sns:
            panes = [s for s in sps if s.role.endswith("_chart")]
            band = max(s._box_h + s._chrome_h for s in panes)
        else:
            chart = next(s for s in sps if s.role.endswith("_chart"))
            hero = next(s for s in sps if s.role == "hero_card")
            support = [
                s
                for s in sps
                if s.role in {"support_table", "outlined_support", "metric_strip"}
            ]
            left = chart._box_h + chart._chrome_h + sum(
                s._box_h + s._chrome_h for s in support
            )
            right = hero._box_h + hero._chrome_h
            band = max(left, right)
        assert fixed + band <= stage, (sn, fixed + band, stage)


def test_slide11_pins_fixed_percent_domain_and_stays_near_flat(handoff: dict) -> None:
    """DP-3 / #225: s11 stays near-flat inside an authored 0–15 frame."""
    from impact_slides.renderer_v3.plan import plan_deck

    s11 = next(s for s in handoff["slides"] if s["slide_number"] == 11)
    domain = s11["payload"]["chart"]["value_axes"]["primary"]["domain"]
    assert domain["kind"] == "fixed"
    assert domain["min"] == "0"
    assert domain["max"] == "15"
    assert domain["ticks"][0] == "0"
    assert domain["ticks"][-1] == "15"
    assert s11["payload"]["chart"]["chart_data"]["series"][0]["values"] == [
        "9",
        "9",
        "10",
        "9",
        "10",
    ]

    deck = validate_handoff(handoff, strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["s11-txn"].chart_paint
    assert cp["domain"]["kind"] == "fixed"
    assert float(cp["domain"]["min"]) == 0.0
    assert float(cp["domain"]["max"]) == 15.0
    ys = [p["y"] for p in cp["points"] if p["finite"]]
    assert max(ys) - min(ys) < 0.15 * cp["geometry"]["plot_h"]

    mutated = json.loads(json.dumps(handoff))
    m11 = next(s for s in mutated["slides"] if s["slide_number"] == 11)
    m11["payload"]["chart"]["value_axes"]["primary"]["domain"] = {
        "kind": "generated",
        "target_ticks": 5,
    }
    # Guard still frames generated pct, but the corpus pin itself is gone.
    assert (
        mutated["slides"][10]["payload"]["chart"]["value_axes"]["primary"][
            "domain"
        ]["kind"]
        != "fixed"
    )


def test_slide21_outlined_support_geometry(handoff: dict, tmp_path: Path) -> None:
    """Capital Summary hero support paints outlined boxes, not a plain table."""
    result = validate_handoff(handoff, strict=True)
    from impact_slides.renderer_v3.plan import plan_deck

    plan = plan_deck(result.deck, strict=True)
    outlined = [
        s
        for s in plan.surfaces
        if s.slide_number == 21 and s.role == "outlined_support"
    ]
    assert len(outlined) == 1
    assert outlined[0]._table_spec is not None
    assert outlined[0]._table_spec.get("kind") == "outlined_support"
    assert outlined[0]._table_spec.get("centers")

    out = tmp_path / "s21"
    render_deck(FIXTURE, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert 'data-outlined-support="s21-roe"' in html
    assert "outlined-support-box" in html
    assert 'data-slide-number="21"' in html

