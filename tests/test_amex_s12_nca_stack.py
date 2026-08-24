"""#228/#260/#268/#273 — restore s12 three-band NCA stack (UCS / Commercial / ICS).

Pins the live D314 corpus (not renderer defaults):
- s12 left chart is stacked_bar with 3 series totaling ~3.x
- display.stack_segments == show paints Q1'25 1.5 / 0.8 / 1.1 plus totals
- pane headings stay Proprietary New Cards / New Accounts
- hero KPI labels are the PDF sentences (not shortened share lines)
- hero/`metric_overview` body is 27 with wrapping KPI labels
- Chart.js dataset count = 3
- renderer does not invent the third band, segment labels, or KPI copy
- strict render of the canonical corpus stays clean
"""

from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

from impact_slides.renderer_v3 import render_deck, validate_handoff
from impact_slides.renderer_v3.charts import _chartjs_bar_config
from impact_slides.renderer_v3.plan import (
    HERO_BODY_PX,
    HERO_HEADING_PX,
    HERO_VALUE_PX,
    METRIC_STRIP_VALUE_PX,
    _wrap_label_lines,
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
HERO_SUB = "Q1'2026"
HERO_LABELS = (
    "Global Consumer New Accounts Acquired from Millennial / Gen-Z",
    "Global New Accounts Acquired on Fee-Paying Products*",
)
SHORT_SHARE = (
    "Proprietary new cards share",
    "Proprietary new accounts share",
)


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
    hero = s12["payload"]["hero"]
    assert hero["heading"] == HERO
    assert hero["subtitle"] == HERO_SUB
    assert hero["hero_type"] == "metric_stack"
    metrics = hero["metrics"]
    assert [m["label"] for m in metrics] == list(HERO_LABELS)
    assert [m["value"]["value"] for m in metrics] == ["66", "73"]
    assert [m["value"]["format_id"] for m in metrics] == ["pct_0", "pct_0"]
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
    s12_vis = unescape(s12).replace("<wbr>", "")
    assert 'data-chart-type="stacked_bar"' in s12
    assert HEADING in s12_vis
    assert HERO in s12_vis
    assert HERO_SUB in s12_vis
    for label in HERO_LABELS:
        assert label in s12_vis
    for short in SHORT_SHARE:
        assert short not in s12_vis
    assert re.search(r'data-metric-id="share-66".*?>66%<', s12, re.S)
    assert re.search(r'data-metric-id="share-73".*?>73%<', s12, re.S)
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
    by = plan_deck(deck, strict=True).by_surface_id()
    hero = by["s12-hero"]
    assert hero.role_sizes["heading"] == HERO_HEADING_PX == 32
    assert hero.role_sizes["body"] == HERO_BODY_PX == 27
    assert hero.role_sizes["value"] == HERO_VALUE_PX == 72
    assert by["s18-driver"].role_sizes["body"] == HERO_BODY_PX == 27
    assert by["s18-driver"].role_sizes["value"] == HERO_VALUE_PX == 72
    assert by["s21-summary"].role_sizes["body"] == HERO_BODY_PX == 27
    assert by["s21-summary"].role_sizes["value"] == HERO_VALUE_PX == 72
    assert by["s22-guide"].role_sizes["body"] == HERO_BODY_PX == 27
    assert by["s22-guide"].role_sizes["value"] == HERO_VALUE_PX == 72
    assert METRIC_STRIP_VALUE_PX == 44
    assert HERO_VALUE_PX > METRIC_STRIP_VALUE_PX
    html_b = html.encode("utf-8")
    wrap = (
        b".metric-label,.driver-label,.metric-detail,.driver-detail"
        b"{display:block;white-space:normal;max-width:100%}"
    )
    assert html_b.count(wrap) == 1
    assert html_b.count(b"white-space:nowrap") == html_b.count(
        b"white-space:nowrap;border:0"
    )
    inner_w = max(40, hero._box_w - 32)
    long_label = (
        "This long proprietary new-cards sentence must wrap inside the "
        "hero card instead of crowding the 72px number."
    )
    assert len(_wrap_label_lines(long_label, HERO_BODY_PX, inner_w)) >= 2


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


def test_mutation_shortening_s12_hero_labels_drops_pdf_sentences(
    tmp_path: Path,
) -> None:
    """Renderer paints hero.metrics[].label as-is; corpus must carry the PDF sentences."""
    for idx, short in enumerate(SHORT_SHARE):
        handoff = _load()
        metrics = _slide(handoff, 12)["payload"]["hero"]["metrics"]
        metrics[idx]["label"] = short
        src = tmp_path / f"h{idx}.json"
        src.write_text(json.dumps(handoff), encoding="utf-8")
        out = tmp_path / f"out{idx}"
        render_deck(src, out, strict=True)
        painted = unescape(
            _section((out / "presentation.html").read_text(encoding="utf-8"), 12)
        ).replace("<wbr>", "")
        assert HERO_LABELS[idx] not in painted
        assert short in painted
        assert HERO_LABELS[1 - idx] in painted
