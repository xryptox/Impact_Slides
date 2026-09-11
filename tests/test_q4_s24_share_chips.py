"""#345 — Q4 2021 s24 share-chip stub + ≥20px type on bar centers.

Seams under test:
- live Q4 handoff (`simulation/amex_q4_2021/handoff_v1.json`)
- optional ShareChips.stub + frozen share_chips plan geometry
- strict `render_deck` HTML for slide 24 (not screenshots)
"""
from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

from impact_slides.renderer_v3 import render_deck, validate_handoff
from impact_slides.renderer_v3.plan import plan_deck

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "simulation" / "amex_q4_2021" / "handoff_v1.json"

STUB = "% of Total Network Volumes"
SHARES = {
    "us-cons": "35",
    "us-sme": "27",
    "intl-cons": "12",
    "intl-sme": "5",
    "lg": "6",
    "proc": "14",
}


def _load() -> dict:
    return json.loads(HANDOFF.read_text(encoding="utf-8"))


def _s24(handoff: dict) -> dict:
    for s in handoff["slides"]:
        if int(s["slide_number"]) == 24:
            return s
    raise AssertionError("missing slide_number=24")


def _section(html: str, n: int) -> str:
    pat = rf'<section\b[^>]*\bdata-slide-number="{n}"[^>]*>'
    m = re.search(pat, html)
    assert m, f"no section data-slide-number={n}"
    start = m.start()
    nxt = re.search(r"<section\b", html[m.end() :])
    end = m.end() + nxt.start() if nxt else len(html)
    return html[start:end]


def test_q4_s24_payload_authors_share_chip_stub() -> None:
    chips = _s24(_load())["payload"]["share_chips"]
    assert chips["surface_id"] == "s24-shares"
    assert chips["stub"] == STUB
    assert [c["share_id"] for c in chips["chips"]] == list(SHARES)
    for chip in chips["chips"]:
        assert chip["value"]["value"] == SHARES[chip["share_id"]]


def test_q4_s24_plan_freezes_stub_type_and_bar_centers() -> None:
    plan = plan_deck(validate_handoff(_load(), strict=True).deck, strict=True)
    by = plan.by_surface_id()
    chart = by["s24-nv"]
    chips = by["s24-shares"]
    paint = chips.table_paint
    assert chips.role_sizes["label"] >= 20
    assert chips.role_sizes["value"] >= 20
    assert chips.role_sizes["label"] == chips.role_sizes["value"]
    assert paint["stub"] == STUB
    assert paint["category_centered"] is True
    g = chart.chart_paint["geometry"]
    assert g["plot_w"] >= 320
    assert g["plot_h"] >= 240
    cat_x = {c["category_id"]: c["x"] for c in chart.chart_paint["categories"]}
    cell_w = int(paint["cell_w"])
    lane = int(paint["stub_lane_w"])
    centers = list(paint["centers"])
    assert [c["category_id"] for c in centers] == list(SHARES)
    prev_right = float(lane)
    for c in centers:
        assert abs(c["x"] - cat_x[c["category_id"]]) <= 2.0
        left = c["x"] - cell_w / 2.0
        right = c["x"] + cell_w / 2.0
        assert left >= prev_right - 0.01
        prev_right = right
    assert not any(s._overflow for s in plan.surfaces if s.slide_number == 24)


def test_q4_s24_strict_render_paints_visible_stub_and_peers(tmp_path: Path) -> None:
    out = tmp_path / "out"
    result = render_deck(HANDOFF, out, strict=True)
    assert result["ok"] is True
    html = unescape((out / "presentation.html").read_text(encoding="utf-8"))
    section = _section(html, 24)
    assert 'data-layout="chart_grouped_annex"' in section
    vis = section.split('class="share-chips', 1)[1].split('class="grouped-annex"', 1)[0]
    visible = re.sub(r'<span class="sr-only">.*?</span>', "", vis)
    assert STUB in visible
    assert "share-chip-stub" in vis
    for sid, val in SHARES.items():
        assert f'data-share-id="{sid}"' in vis
        assert f"{val}%" in vis
    assert "s24-us" in section
    assert "s24-intl" in section
    assert section.count("grouped-annex-peer") == 2
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["status"] == "clean"


def test_mutation_share_chip_ceil_14_fails_type_assert(monkeypatch) -> None:
    import impact_slides.renderer_v3.plan as plan_mod

    monkeypatch.setattr(plan_mod, "SHARE_CHIP_CEIL", 14)
    plan = plan_deck(validate_handoff(_load(), strict=True).deck, strict=True)
    chips = plan.by_surface_id()["s24-shares"]
    assert chips.role_sizes["label"] < 20
    assert chips.role_sizes["value"] < 20
