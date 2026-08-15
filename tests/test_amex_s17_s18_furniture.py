"""#229 — restore s17/s18 $B formats, CAGR rule, YoY boxes, driver rows.

Pins the live D314 corpus (not renderer defaults):
- s17 Net Card Fees uses usd_1; labels read $0.9…$2.8; CAGR rule paints; Qualification disclosure
- s18 NII uses usd_1; labels read $4.2…; five boxed YoY labels; PDF driver rows
- renderer does not invent the furniture
- strict render of the canonical corpus stays clean
"""

from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

from impact_slides.renderer_v3 import render_deck

FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "renderer_v3"
    / "canonical_amex_handoff_v1.json"
)

S17_CATS = [
    "q1-19",
    "q1-20",
    "q1-21",
    "q1-22",
    "q1-23",
    "q1-24",
    "q1-25",
    "q1-26",
]
S17_VALS = ["0.9", "1.1", "1.3", "1.4", "1.7", "2.0", "2.3", "2.8"]
S17_LABELS = ["$0.9", "$1.1", "$1.3", "$1.4", "$1.7", "$2.0", "$2.3", "$2.8"]
S18_CATS = ["q1-25", "q2-25", "q3-25", "q4-25", "q1-26"]
S18_VALS = ["4.2", "4.2", "4.5", "4.5", "4.7"]
S18_LABELS = ["$4.2", "$4.5", "$4.7"]
S18_YOY = ["11", "12", "12", "12", "12"]
S18_ROWS = [
    ("billed", "Billed Business", "8", None),
    ("nii", "Net Interest Income", "13", None),
    ("volume", "Volume", "7", "Total Balances"),
    ("margin", "Margin", "5", "Net Interest Income / Average Total Balances"),
]


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


def test_corpus_payloads_carry_s17_s18_furniture() -> None:
    handoff = _load()

    s17 = _slide(handoff, 17)
    ncf = s17["payload"]["charts"][0]
    assert ncf["value_axes"]["primary"]["format_id"] == "usd_1"
    cats = [c["category_id"] for c in ncf["chart_data"]["categories"]]
    assert cats == S17_CATS
    assert ncf["chart_data"]["series"][0]["values"] == S17_VALS
    meas = ncf["measurements"]
    assert len(meas) == 1
    assert meas[0]["role"] == "cagr"
    assert meas[0]["series_id"] == "net-card-fees"
    assert meas[0]["from_category_id"] == "q1-19"
    assert meas[0]["to_category_id"] == "q1-26"
    assert meas[0]["value"] == "17"
    assert meas[0]["format_id"] == "pct_0"
    fx = s17["payload"]["charts"][1]
    assert fx["value_axes"]["primary"]["format_id"] == "pct_0"
    assert "measurements" not in fx
    disc = s17["disclosure"]["sections"][0]
    assert disc["surface_id"] == "s17-disc"
    assert disc["title"] == "Qualification"
    assert disc["items"][0]["text"] == (
        "Authored 17% CAGR measurement is a source claim retained in disclosure."
    )

    s18 = _slide(handoff, 18)
    nii = s18["payload"]["chart"]
    assert nii["value_axes"]["primary"]["format_id"] == "usd_1"
    assert [c["category_id"] for c in nii["chart_data"]["categories"]] == S18_CATS
    assert nii["chart_data"]["series"][0]["values"] == S18_VALS
    boxed = [a for a in nii["auxiliary_series"] if a["role"] == "boxed_label"]
    assert len(boxed) == 1
    assert boxed[0]["label"] == "YoY Growth"
    assert boxed[0]["format_id"] == "pct_0"
    assert boxed[0]["target_series_id"] == "nii"
    assert boxed[0]["values"] == S18_YOY
    hero = s18["payload"]["hero"]
    assert hero["hero_type"] == "driver_card"
    assert hero["heading"] == "NII: Volume & Margin Drivers"
    assert hero["subtitle"] == "CAGR % vs. Q1'19 (FX-adjusted except Margin)"
    assert len(hero["rows"]) == 4
    for row, (rid, label, value, detail) in zip(hero["rows"], S18_ROWS):
        assert row["row_id"] == rid
        assert row["label"] == label
        assert row["value"] == {"type": "number", "value": value, "format_id": "pct_0"}
        assert row["direction"] == "up"
        assert row["tone"] == "positive"
        if detail is None:
            assert "detail" not in row
        else:
            assert row["detail"] == detail


def test_strict_render_shows_s17_s18_furniture(tmp_path: Path) -> None:
    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["status"] == "clean"
    assert meta["ok"] is True
    assert meta["severity_counts"].get("error", 0) == 0

    html = (out / "presentation.html").read_text(encoding="utf-8")

    s17 = unescape(_section(html, 17)).replace("<wbr>", "")
    for token in S17_LABELS:
        assert token in s17
    assert 'data-measurement-id="' in s17
    assert 'data-role="cagr"' in s17
    assert "17%" in s17
    assert (
        "Authored 17% CAGR measurement is a source claim retained in disclosure."
        in s17
    )

    s18 = unescape(_section(html, 18)).replace("<wbr>", "")
    for token in S18_LABELS:
        assert token in s18
    boxed_cats = re.findall(
        r'class="boxed-label"[^>]*data-category="([^"]+)"', s18
    )
    assert set(boxed_cats) == set(S18_CATS)
    assert "11%" in s18 and "12%" in s18
    assert 'data-hero-type="driver_card"' in s18
    for _rid, label, value, detail in S18_ROWS:
        assert label in s18
        assert f"{value}%" in s18
        if detail:
            assert detail in s18


def test_mutation_dropping_s17_cagr_omits_rule(tmp_path: Path) -> None:
    """Renderer does not invent the CAGR rule; corpus must carry it."""
    handoff = _load()
    del _slide(handoff, 17)["payload"]["charts"][0]["measurements"]
    src = tmp_path / "h.json"
    src.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    s17 = _section((out / "presentation.html").read_text(encoding="utf-8"), 17)
    assert 'data-measurement-id="' not in s17
    assert "chart-measurement" not in s17
    assert 'data-role="cagr"' not in s17


def test_mutation_dropping_s18_boxes_and_rows_omits_furniture(tmp_path: Path) -> None:
    """Renderer does not invent YoY boxes or PDF driver rows; corpus must carry them."""
    handoff = _load()
    s18 = _slide(handoff, 18)
    s18["payload"]["chart"].pop("auxiliary_series", None)
    s18["payload"]["hero"]["rows"] = [
        {
            "row_id": "vol",
            "label": "Loan growth",
            "value": {"type": "number", "value": "7", "format_id": "pct_0"},
            "direction": "up",
            "tone": "positive",
        }
    ]
    s18["payload"]["hero"].pop("subtitle", None)
    src = tmp_path / "h.json"
    src.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    html = unescape(
        _section((out / "presentation.html").read_text(encoding="utf-8"), 18)
    )
    assert "boxed-label" not in html
    assert "Billed Business" not in html
    assert "Loan growth" in html
