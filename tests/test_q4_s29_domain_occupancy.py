"""#344 — generated cartesian y-axis occupancy (s29 2.4% on 0-5, not 0-20).

Seams under test:
- live Q4 handoff payload (`simulation/amex_q4_2021/handoff_v1.json`)
- generated percent min-span floor 5 on the 0..<5 band
- freeze-time occupancy >= 0.40 on every cartesian generated axis
- authored `domain.kind=fixed` exempt; pie/donut exempt
- mutation restoring `_PCT_MIN_SPAN = 15` fails s29 occupancy
"""
from __future__ import annotations

import json
import re
from decimal import Decimal
from html import unescape
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import render_deck, validate_handoff
from impact_slides.renderer_v3 import charts as charts_mod
from impact_slides.renderer_v3.plan import plan_deck

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "simulation" / "amex_q4_2021" / "handoff_v1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "renderer_v3"

CARTESIAN = (
    ("minimal_line_chart.json", "vol-trend"),
    ("minimal_grouped_bar.json", "seg-growth"),
    ("minimal_horizontal_bar.json", "net-share"),
    ("minimal_stacked_bar.json", "dep-mix"),
    ("minimal_combo_chart.json", "cap-combo"),
    ("minimal_waterfall.json", "rev-bridge"),
)

MIX_STACKS = ("s04-mix", "s06-mix", "s07-mix", "s31-fund")
FIXED = ("s03-vol", "s11-loans")
S29_TICKS = ("0", "1", "2", "3", "4", "5")


def _load() -> dict:
    return json.loads(HANDOFF.read_text(encoding="utf-8"))


def _slide(handoff: dict, n: int) -> dict:
    for s in handoff["slides"]:
        if int(s["slide_number"]) == n:
            return s
    raise AssertionError(f"missing slide_number={n}")


def _section(html: str, n: int) -> str:
    pat = rf'<section\b[^>]*\bdata-slide-number="{n}"[^>]*>'
    m = re.search(pat, html)
    assert m, f"no section data-slide-number={n}"
    start = m.start()
    nxt = re.search(r"<section\b", html[m.end() :])
    end = m.end() + nxt.start() if nxt else len(html)
    return html[start:end]


def _occupancy(domain: dict) -> float:
    """Ticket formula: max(|source|)/max(|domain|) ; zero-based uses source_max/domain.max."""
    smin = abs(float(domain["source_min"]))
    smax = abs(float(domain["source_max"]))
    dmin = float(domain["min"])
    dmax = float(domain["max"])
    denom = max(abs(dmin), abs(dmax))
    assert denom > 0
    if dmin == 0:
        return smax / abs(dmax)
    return max(smin, smax) / denom


def _generated_domains(cp: dict) -> list[dict]:
    out: list[dict] = []
    for key in ("domain", "secondary_domain"):
        dom = cp.get(key)
        if not isinstance(dom, dict):
            continue
        if dom.get("kind") != "generated":
            continue
        out.append(dom)
    return out


def test_q4_s29_generated_domain_max_is_5() -> None:
    slide = _slide(_load(), 29)
    chart = slide["payload"]["chart"]
    assert chart["surface_id"] == "s29-gcp"
    assert chart["chart_type"] == "grouped_bar"
    assert chart["chart_data"]["series"][0]["values"] == [
        "2.4",
        "0.7",
        "0.4",
        "0.5",
        "0.2",
        "0.2",
    ]
    assert chart["value_axes"]["primary"]["domain"]["kind"] == "generated"

    plan = plan_deck(validate_handoff(_load(), strict=True).deck, strict=True)
    cp = plan.by_surface_id()["s29-gcp"].chart_paint
    domain = cp["domain"]
    assert domain["kind"] == "generated"
    assert float(domain["max"]) == 5.0
    ticks = [str(t) for t in domain["ticks"]]
    assert ticks == list(S29_TICKS)
    assert "10" not in ticks and "15" not in ticks and "20" not in ticks
    assert _occupancy(domain) >= 0.40
    bar = next(b for b in cp["bars"] if b["numeric"] == 2.4)
    assert bar["height"] / cp["geometry"]["plot_h"] >= 0.40


def test_q4_s32_nv_occupancy_at_least_40() -> None:
    plan = plan_deck(validate_handoff(_load(), strict=True).deck, strict=True)
    cp = plan.by_surface_id()["s32-nv"].chart_paint
    domain = cp["domain"]
    assert domain["kind"] == "generated"
    assert _occupancy(domain) >= 0.40
    assert float(domain["max"]) <= 6.0


def test_q4_mix_stacks_keep_100_headroom_occupancy() -> None:
    plan = plan_deck(validate_handoff(_load(), strict=True).deck, strict=True)
    by = plan.by_surface_id()
    for sid in MIX_STACKS:
        domain = by[sid].chart_paint["domain"]
        assert domain["kind"] == "generated"
        assert float(domain["max"]) >= 100.0
        assert _occupancy(domain) >= 0.40


def test_q4_authored_fixed_s03_s11_unchanged() -> None:
    raw = _load()
    s03 = _slide(raw, 3)["payload"]["chart"]["value_axes"]["primary"]["domain"]
    assert s03 == {
        "kind": "fixed",
        "min": "-40",
        "max": "20",
        "ticks": ["-40", "-30", "-20", "-10", "0", "10", "20"],
    }
    s11 = _slide(raw, 11)["payload"]["charts"]
    for pane in s11:
        ch = pane["chart"] if "chart" in pane and "chart_type" not in pane else pane
        domain = ch["value_axes"]["primary"]["domain"]
        assert domain["kind"] == "fixed"
        assert domain["min"] == "0"
        assert domain["max"] == "5"
        assert domain["ticks"] == list(S29_TICKS)

    plan = plan_deck(validate_handoff(raw, strict=True).deck, strict=True)
    by = plan.by_surface_id()
    assert by["s03-vol"].chart_paint["domain"]["kind"] == "fixed"
    assert float(by["s03-vol"].chart_paint["domain"]["max"]) == 20.0
    assert by["s11-loans"].chart_paint["domain"]["kind"] == "fixed"
    assert float(by["s11-loans"].chart_paint["domain"]["max"]) == 5.0


@pytest.mark.parametrize("fixture, surface_id", CARTESIAN)
def test_cartesian_generated_occupancy_at_least_40(fixture: str, surface_id: str) -> None:
    raw = json.loads((FIXTURES / fixture).read_text(encoding="utf-8"))
    plan = plan_deck(validate_handoff(raw, strict=True).deck, strict=True)
    cp = plan.by_surface_id()[surface_id].chart_paint
    assert cp["chart_type"] != "pie" and cp["chart_type"] != "donut"
    domains = _generated_domains(cp)
    assert domains, (surface_id, cp.get("domain"))
    for domain in domains:
        assert _occupancy(domain) >= 0.40
    assert not cp.get("domain_occupancy_overflow")


def test_pie_donut_exempt_from_occupancy_rule() -> None:
    raw = json.loads((FIXTURES / "minimal_donut.json").read_text(encoding="utf-8"))
    plan = plan_deck(validate_handoff(raw, strict=True).deck, strict=True)
    cp = next(sp.chart_paint for sp in plan.surfaces if sp.chart_paint)
    assert cp["chart_type"] in {"pie", "donut"}
    assert "source_min" not in (cp.get("domain") or {})
    assert not cp.get("domain_occupancy_overflow")


def test_mutation_restoring_15pt_floor_fails_s29_occupancy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(charts_mod, "_PCT_MIN_SPAN", Decimal("15"))
    deck = validate_handoff(_load(), strict=True).deck
    chart = next(
        s.payload.chart
        for s in deck.slides
        if getattr(getattr(s, "payload", None), "chart", None) is not None
        and s.payload.chart.surface_id == "s29-gcp"
    )
    cp = charts_mod.freeze_chart(chart, deck.number_formats)
    assert _occupancy(cp["domain"]) < 0.40
    assert float(cp["domain"]["max"]) >= 15.0


def test_q4_s29_strict_render_ticks_stop_at_5(tmp_path: Path) -> None:
    out = tmp_path / "out"
    result = render_deck(HANDOFF, out, strict=True)
    assert result["ok"] is True
    html = unescape((out / "presentation.html").read_text(encoding="utf-8"))
    s29 = _section(html, 29)
    assert 'data-layout="single_chart"' in s29
    assert 'data-chart-type="grouped_bar"' in s29
    ticks = re.findall(r'data-tick="([^"]+)"', s29)
    if ticks:
        assert "10" not in ticks and "15" not in ticks and "20" not in ticks
        assert "5" in ticks
