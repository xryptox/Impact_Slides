"""#228/#260 — restore s12 three-band NCA stack (UCS / Commercial / ICS).

Pins the live D314 corpus (not renderer defaults):
- s12 left chart is stacked_bar with 3 series totaling ~3.x
- display.stack_segments == show paints Q1'25 1.5 / 0.8 / 1.1 plus totals
- pane headings stay Proprietary New Cards / New Accounts
- Chart.js dataset count = 3
- renderer does not invent the third band or segment labels
- strict render of the canonical corpus stays clean
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from impact_slides.renderer_v3 import render_deck, validate_handoff
from impact_slides.renderer_v3.charts import _chartjs_bar_config
from impact_slides.renderer_v3.plan import (
    HERO_BODY_PX,
    HERO_HEADING_PX,
    HERO_VALUE_PX,
    METRIC_STRIP_VALUE_PX,
    plan_deck,
)

FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "renderer_v3"
    / "canonical_amex_handoff_v1.json"
)

CATS = ["q1-25", "q2-25", "q3-25", "q4-25", "q1-26"]
SERIES = [
    ("U.S. Consumer Services", ["1.5", "1.5", "1.5", "1.3", "1.3"]),
    ("Commercial Services", ["0.8", "0.7", "0.7", "0.7", "0.8"]),
    ("International Card Services", ["1.1", "0.9", "1.0", "0.9", "1.0"]),
]
TOTALS = [3.4, 3.1, 3.2, 2.9, 3.1]
HEADING = "Proprietary New Cards Acquired"
HERO = "Proprietary New Accounts Acquired"


def _load() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


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


def _s12_datasets(handoff: dict) -> list:
    deck = validate_handoff(handoff, strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["s12-cards"].chart_paint
    return _chartjs_bar_config(cp)["data"]["datasets"]


def test_corpus_payload_is_three_band_nca_stack() -> None:
    s12 = _slide(_load(), 12)
    chart = s12["payload"]["chart"]
    assert chart["chart_type"] == "stacked_bar"
    assert chart["heading"] == HEADING
    assert chart["subtitle"] == "in millions"
    assert s12["payload"]["hero"]["heading"] == HERO
    cats = [c["category_id"] for c in chart["chart_data"]["categories"]]
    assert cats == CATS
    series = chart["chart_data"]["series"]
    assert len(series) == 3
    for got, (name, values) in zip(series, SERIES):
        assert got["name"] == name
        assert got["values"] == values
    for i, expected in enumerate(TOTALS):
        total = sum(float(s["values"][i]) for s in series)
        assert abs(total - expected) < 1e-9
    assert chart["display"]["series_identity"] == "legend"
    assert chart["display"]["stack_segments"] == "show"


def test_strict_render_s12_dataset_count_is_three(tmp_path: Path) -> None:
    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["status"] == "clean"
    assert meta["ok"] is True
    assert meta["severity_counts"].get("error", 0) == 0

    html = (out / "presentation.html").read_text(encoding="utf-8")
    s12 = _section(html, 12)
    assert 'data-chart-type="stacked_bar"' in s12
    assert HEADING in s12
    assert HERO in s12
    for name, _values in SERIES:
        assert name in s12

    datasets = _s12_datasets(_load())
    assert len(datasets) == 3
    assert all(ds.get("stack") == "stack" for ds in datasets)
    segs = re.findall(r'data-kind="segment">([^<]*)</text>', s12)
    assert segs[:3] == ["1.5", "0.8", "1.1"]
    tots = re.findall(r'data-kind="stack_total">([^<]*)</text>', s12)
    assert tots[:5] == ["3.4", "3.1", "3.2", "2.9", "3.1"]

    deck = validate_handoff(_load(), strict=True).deck
    hero = plan_deck(deck, strict=True).by_surface_id()["s12-hero"]
    assert hero.role_sizes["heading"] == HERO_HEADING_PX == 32
    assert hero.role_sizes["body"] == HERO_BODY_PX == 22
    assert hero.role_sizes["value"] == HERO_VALUE_PX == 72
    assert HERO_VALUE_PX > METRIC_STRIP_VALUE_PX


def test_mutation_collapsing_s12_stack_drops_dataset_count(tmp_path: Path) -> None:
    """Renderer does not invent UCS/Commercial/ICS bands; corpus must carry them."""
    handoff = _load()
    chart = _slide(handoff, 12)["payload"]["chart"]
    chart["chart_type"] = "grouped_bar"
    chart["chart_data"]["series"] = [chart["chart_data"]["series"][0]]
    chart.pop("auxiliary_series", None)
    chart.get("display", {}).pop("stack_segments", None)
    src = tmp_path / "h.json"
    src.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    s12 = _section((out / "presentation.html").read_text(encoding="utf-8"), 12)
    assert "Commercial Services" not in s12
    assert "International Card Services" not in s12
    assert len(_s12_datasets(handoff)) == 1


def test_mutation_dropping_s12_stack_segments_omits_segment_labels(
    tmp_path: Path,
) -> None:
    """Renderer does not invent on-stack segment labels; corpus must opt in."""
    handoff = _load()
    _slide(handoff, 12)["payload"]["chart"]["display"].pop("stack_segments", None)
    src = tmp_path / "h.json"
    src.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    s12 = _section((out / "presentation.html").read_text(encoding="utf-8"), 12)
    assert 'data-kind="segment"' not in s12
    tots = re.findall(r'data-kind="stack_total">([^<]*)</text>', s12)
    assert tots[:5] == ["3.4", "3.1", "3.2", "2.9", "3.1"]
