"""Q4 2021 s24 re-author onto chart_grouped_annex (#321).

PDF page 24 (x-order + fill): share chips 35/27/12/5/6/14; signed vs-2019
bars 22/18/5/12/-33/3 (consumer/commercial/processed); two brace-grouped
peer tables. On-bar YoY% 37/29/32/31/34/15 is not a second series.
"""
from __future__ import annotations

import json
from copy import deepcopy
from html import unescape
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.plan import plan_deck

ROOT = Path(__file__).resolve().parents[1]
Q4 = ROOT / "simulation/amex_q4_2021/handoff_v1.json"

CATS = (
    "us-cons",
    "us-sme",
    "intl-cons",
    "intl-sme",
    "lg",
    "proc",
)
VS19 = {
    "consumer": ["22", None, "5", None, None, None],
    "commercial": [None, "18", None, "12", "-33", None],
    "processed": [None, None, None, None, None, "3"],
}
SHARES = {
    "us-cons": "35",
    "us-sme": "27",
    "intl-cons": "12",
    "intl-sme": "5",
    "lg": "6",
    "proc": "14",
}


def _q4() -> dict:
    return json.loads(Q4.read_text(encoding="utf-8"))


def _s24(raw: dict) -> dict:
    return next(s for s in raw["slides"] if s["slide_number"] == 24)


def _mini(raw: dict) -> dict:
    s24 = deepcopy(_s24(raw))
    s24["section_id"] = "appendix"
    return {
        "meta": {"handoff_schema_version": 1},
        "sections": [{"section_id": "appendix", "label": "Appendix"}],
        "number_formats": {
            k: v for k, v in raw["number_formats"].items() if k == "pct_0"
        },
        "evidence_registry": {
            eid: raw["evidence_registry"][eid]
            for eid in ("amex-q4-2021-p01", "amex-q4-2021-p24", "amex-q4-2021-p53")
        },
        "slides": [
            {
                "slide_number": 1,
                "layout_type": "opening_cover",
                "payload": {"title": "Q4 2021"},
                "evidence_ids": ["amex-q4-2021-p01"],
            },
            s24,
            {
                "slide_number": 53,
                "layout_type": "closing_cover",
                "payload": {"title": "American Express"},
                "evidence_ids": ["amex-q4-2021-p53"],
            },
        ],
    }


def test_q4_s24_is_chart_grouped_annex_not_data_table():
    s24 = _s24(_q4())
    assert s24["layout_type"] == "chart_grouped_annex"
    payload = s24["payload"]
    chart = payload["chart"]
    assert chart["chart_type"] == "grouped_bar"
    assert chart["display"]["ordinary_values"] == "show"
    assert [c["category_id"] for c in chart["chart_data"]["categories"]] == list(CATS)
    assert [c["label"] for c in chart["chart_data"]["categories"]] == [
        "US Consumer",
        "US SME",
        "Int'l Consumer*",
        "Int'l SME*",
        "Large & Global Corporate*",
        "Processed Volumes*",
    ]
    series = {s["series_id"]: s for s in chart["chart_data"]["series"]}
    assert set(series) == {"consumer", "commercial", "processed"}
    assert series["consumer"]["color"] == "primary_blue"
    assert series["commercial"]["color"] == "navy"
    assert series["processed"]["color"] == "neutral"
    for sid, values in VS19.items():
        assert series[sid]["values"] == values
    chips = {c["share_id"]: c for c in payload["share_chips"]["chips"]}
    assert list(chips) == list(SHARES)
    for sid, val in SHARES.items():
        assert chips[sid]["value"]["value"] == val
        assert chips[sid]["value"]["format_id"] == "pct_0"
    assert len(payload["tables"]) == 2
    us = payload["tables"][0]["table"]
    intl = payload["tables"][1]["table"]
    assert us["rows"][0]["cells"]["q3"]["value"] == "33"
    assert us["rows"][0]["cells"]["q4"]["value"] == "33"
    assert us["rows"][1]["cells"]["q3"]["value"] == "14"
    assert us["rows"][1]["cells"]["q4"]["value"] == "20"
    assert intl["rows"][0]["cells"]["q3"]["value"] == "25"
    assert intl["rows"][0]["cells"]["q4"]["value"] == "32"
    assert intl["rows"][1]["cells"]["q3"]["value"] == "-2"
    assert intl["rows"][1]["cells"]["q4"]["value"] == "8"


def test_q4_s24_strict_render_paints_bars_chips_peers(tmp_path: Path):
    raw = _mini(_q4())
    assert validate_handoff(raw, strict=True).ok
    plan_deck(validate_handoff(raw, strict=True).deck, strict=True)
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(handoff, out, strict=True)["ok"] is True
    html = unescape((out / "presentation.html").read_text(encoding="utf-8"))
    start = html.index('id="slide-24"')
    chunk = html[start : html.find("</section>", start)]
    assert 'data-layout="chart_grouped_annex"' in chunk
    assert chunk.count('class="chart-body"') == 1
    assert chunk.count("data-share-id=") == 6
    assert chunk.count("grouped-annex-peer") == 2
    assert "22%" in chunk and "(33%)" in chunk
    assert "35%" in chunk and "14%" in chunk
    assert "US Consumer" in chunk and "Int'l Consumer" in chunk


def test_mutation_empty_consumer_series_strict_rejects():
    raw = _mini(_q4())
    chart = raw["slides"][1]["payload"]["chart"]
    consumer = next(s for s in chart["chart_data"]["series"] if s["series_id"] == "consumer")
    consumer["values"] = [None] * 6
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)
