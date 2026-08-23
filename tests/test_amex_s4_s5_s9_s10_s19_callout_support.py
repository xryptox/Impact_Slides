"""#226/#255/#256 — Leap-Year callouts, ticks, series identity, side facts.

Pins the live D314 corpus (not renderer defaults):
- s4/s19: explanation annotation + category-aligned support_table
- s4/s19 painted series match the PDF identity (names/styles kept, values swapped)
- s4/s19 D167 hide_header + hairline body (no required .head; #256)
- s5/s9/s10: independent support_table (s10 series values stay unswapped)
- s5/s9/s10/s11: Leap Year annotation; s5/s9/s10 G&S/T&E context_labels
- s4/s5/s9/s11/s19 ticks 0/5/10/15; s10 ticks 0/5/10/15/20/25; s19 domain fixed 0-15
- DOM on those sections shows the callout text / support rows / side facts
- strict render of the canonical corpus stays clean
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import render_deck, validate_handoff
from impact_slides.renderer_v3.plan import plan_deck

FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "renderer_v3"
    / "canonical_amex_handoff_v1.json"
)

LEAP = "Leap Year Approx. (1%)"
CATS = ["q1-25", "q2-25", "q3-25", "q4-25", "q1-26"]
S4_GS = ["7", "7", "9", "8", "8"]
S4_TE = ["6", "5", "8", "8", "9"]
S5_YOY = ["38", "13", "8", "4", "10"]
S5_SHARE = ["6", "30", "36", "28", "100"]
S9_YOY = ["4", "4", "4"]
S9_SHARE = ["81", "19", "100"]
S10_YOY = ["13", "12", "13"]
S10_SHARE = ["65", "35", "100"]
S19_USD = ["17.0", "17.9", "18.4", "19.0", "18.9"]
TICKS_0_15 = ["0", "5", "10", "15"]
TICKS_0_25 = ["0", "5", "10", "15", "20", "25"]
S4_REPORTED = ["6", "7", "9", "9", "10"]
S4_FX = ["6", "7", "8", "8", "9"]
S19_FX = ["8", "9", "11", "9", "10"]
S19_REPORTED = ["7", "9", "11", "10", "11"]
S10_FX = ["13", "12", "13", "12", "13"]
S10_REPORTED = ["9", "15", "14", "17", "20"]


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


def _cell_values(row: dict, col_ids: list[str]) -> list[str]:
    return [row["cells"][cid]["value"] for cid in col_ids]


def _series(chart: dict) -> dict[str, dict]:
    return {s["name"]: s for s in chart["chart_data"]["series"]}


def _domain(chart: dict) -> dict:
    return chart["value_axes"]["primary"]["domain"]


def _assert_leap(chart: dict) -> None:
    anns = chart["annotations"]
    leap = next(a for a in anns if a["text"] == LEAP)
    assert leap["role"] == "explanation"
    assert leap["anchor"] == {"type": "chart"}


def _assert_yoy_context(chart: dict, gs: str, te: str) -> None:
    by_id = {lab["context_id"]: lab for lab in chart["context_labels"]}
    assert by_id["gs-yoy"]["label"] == "G&S"
    assert by_id["gs-yoy"]["value"] == {"type": "text", "text": gs}
    assert by_id["te-yoy"]["label"] == "T&E"
    assert by_id["te-yoy"]["value"] == {"type": "text", "text": te}


def _assert_support(slide: dict, *, alignment: str, n_rows: int) -> dict:
    support = slide["payload"]["support"]
    assert support["support_type"] == "support_table"
    assert support["alignment"] == alignment
    rows = support["table"]["rows"]
    assert len(rows) == n_rows
    return support


def test_corpus_payloads_carry_callouts_and_support_tables() -> None:
    handoff = _load()

    s4 = _slide(handoff, 4)
    chart4 = s4["payload"]["chart"]
    _assert_leap(chart4)
    ser4 = _series(chart4)
    assert ser4["Reported"]["values"] == S4_REPORTED
    assert ser4["Reported"]["color"] == "neutral"
    assert ser4["Reported"]["style"]["line_style"] == "dashed"
    assert ser4["FX-adjusted"]["values"] == S4_FX
    assert ser4["FX-adjusted"]["color"] == "navy"
    assert ser4["FX-adjusted"]["style"]["line_style"] == "solid"
    assert _domain(chart4) == {
        "kind": "fixed",
        "min": "0",
        "max": "15",
        "ticks": TICKS_0_15,
    }
    sup4 = _assert_support(s4, alignment="category", n_rows=2)
    cols4 = [c["column_id"] for c in sup4["table"]["columns"]]
    assert cols4 == CATS
    assert [r["label"] for r in sup4["table"]["rows"]] == ["G&S", "T&E"]
    assert _cell_values(sup4["table"]["rows"][0], cols4) == S4_GS
    assert _cell_values(sup4["table"]["rows"][1], cols4) == S4_TE

    s5 = _slide(handoff, 5)
    chart5 = s5["payload"]["chart"]
    _assert_leap(chart5)
    _assert_yoy_context(chart5, "9% YoY", "11% YoY")
    assert _domain(chart5)["ticks"] == TICKS_0_15
    sup5 = _assert_support(s5, alignment="independent", n_rows=2)
    assert [c["label"] for c in sup5["table"]["columns"]] == [
        "Gen-Z",
        "Millennials",
        "Gen-X",
        "Baby Boomer +",
        "Total",
    ]
    assert [r["label"] for r in sup5["table"]["rows"]] == ["YoY", "% of Total"]
    cols5 = [c["column_id"] for c in sup5["table"]["columns"]]
    assert _cell_values(sup5["table"]["rows"][0], cols5) == S5_YOY
    assert _cell_values(sup5["table"]["rows"][1], cols5) == S5_SHARE

    s9 = _slide(handoff, 9)
    chart9 = s9["payload"]["chart"]
    _assert_leap(chart9)
    _assert_yoy_context(chart9, "3% YoY", "6% YoY")
    assert _domain(chart9)["ticks"] == TICKS_0_15
    sup9 = _assert_support(s9, alignment="independent", n_rows=2)
    assert [c["label"] for c in sup9["table"]["columns"]] == [
        "U.S. SME",
        "U.S. Large & Global Corp.",
        "Total",
    ]
    cols9 = [c["column_id"] for c in sup9["table"]["columns"]]
    assert _cell_values(sup9["table"]["rows"][0], cols9) == S9_YOY
    assert _cell_values(sup9["table"]["rows"][1], cols9) == S9_SHARE

    s10 = _slide(handoff, 10)
    chart10 = s10["payload"]["chart"]
    _assert_leap(chart10)
    _assert_yoy_context(chart10, "14% YoY", "10% YoY")
    ser10 = _series(chart10)
    assert ser10["FX-adjusted"]["values"] == S10_FX
    assert ser10["Reported"]["values"] == S10_REPORTED
    assert _domain(chart10) == {
        "kind": "fixed",
        "min": "0",
        "max": "25",
        "ticks": TICKS_0_25,
    }
    sup10 = _assert_support(s10, alignment="independent", n_rows=2)
    assert [c["label"] for c in sup10["table"]["columns"]] == [
        "Intl Consumer",
        "Intl SME & Large Corp.",
        "Total",
    ]
    cols10 = [c["column_id"] for c in sup10["table"]["columns"]]
    assert _cell_values(sup10["table"]["rows"][0], cols10) == S10_YOY
    assert _cell_values(sup10["table"]["rows"][1], cols10) == S10_SHARE

    s11 = _slide(handoff, 11)
    chart11 = s11["payload"]["chart"]
    _assert_leap(chart11)
    assert "context_labels" not in chart11
    assert _domain(chart11) == {
        "kind": "fixed",
        "min": "0",
        "max": "15",
        "ticks": TICKS_0_15,
    }

    s19 = _slide(handoff, 19)
    chart19 = s19["payload"]["chart"]
    _assert_leap(chart19)
    ser19 = _series(chart19)
    assert ser19["FX-adjusted"]["values"] == S19_FX
    assert ser19["FX-adjusted"]["color"] == "navy"
    assert ser19["FX-adjusted"]["style"]["line_style"] == "solid"
    assert ser19["Reported"]["values"] == S19_REPORTED
    assert ser19["Reported"]["color"] == "neutral"
    assert ser19["Reported"]["style"]["line_style"] == "dashed"
    assert _domain(chart19) == {
        "kind": "fixed",
        "min": "0",
        "max": "15",
        "ticks": TICKS_0_15,
    }
    sup19 = _assert_support(s19, alignment="category", n_rows=1)
    cols19 = [c["column_id"] for c in sup19["table"]["columns"]]
    assert cols19 == CATS
    assert _cell_values(sup19["table"]["rows"][0], cols19) == S19_USD
    assert all(
        sup19["table"]["rows"][0]["cells"][cid]["format_id"] == "usd_1" for cid in cols19
    )


def test_strict_render_shows_callout_text_and_support_rows(tmp_path: Path) -> None:
    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["status"] == "clean"
    assert meta["ok"] is True
    assert meta["severity_counts"].get("error", 0) == 0

    html = (out / "presentation.html").read_text(encoding="utf-8")
    s4 = _section(html, 4)
    assert LEAP in s4
    assert 'data-annotation-id="' in s4
    assert "support-table" in s4
    assert "G&amp;S" in s4 and "T&amp;E" in s4
    assert "7%" in s4 and "9%" in s4
    assert "support-cat-cell" in s4
    assert "support-cat-cell head" not in s4
    cfg4 = json.loads(re.search(r'id="cfg-s4-bb">(.*?)</script>', s4, re.S).group(1))
    by4 = {d["label"]: d for d in cfg4["data"]["datasets"]}
    assert by4["Reported"]["data"] == [6, 7, 9, 9, 10]
    assert by4["Reported"]["borderDash"] == [8, 6]
    assert by4["FX-adjusted"]["data"] == [6, 7, 8, 8, 9]
    assert by4["FX-adjusted"]["borderDash"] == []

    s5 = _section(html, 5)
    assert "support-table" in s5
    assert "Gen-Z" in s5 and "Millennials" in s5
    assert "38%" in s5 and "100%" in s5
    assert LEAP in s5
    assert 'data-context-id="gs-yoy"' in s5
    assert "9% YoY" in s5 and "11% YoY" in s5

    s9 = _section(html, 9)
    assert "support-table" in s9
    assert "U.S. SME" in s9
    assert "81%" in s9
    assert LEAP in s9
    assert "3% YoY" in s9 and "6% YoY" in s9

    s10 = _section(html, 10)
    assert "support-table" in s10
    assert "Intl Consumer" in s10
    assert "65%" in s10
    assert LEAP in s10
    assert 'data-annotation-id="' in s10
    assert "14% YoY" in s10 and "10% YoY" in s10
    cfg10 = json.loads(re.search(r'id="cfg-s10-ics">(.*?)</script>', s10, re.S).group(1))
    by10 = {d["label"]: d for d in cfg10["data"]["datasets"]}
    assert by10["FX-adjusted"]["data"] == [13, 12, 13, 12, 13]
    assert by10["Reported"]["data"] == [9, 15, 14, 17, 20]

    s11 = _section(html, 11)
    assert LEAP in s11
    assert "9% YoY" not in s11

    s19 = _section(html, 19)
    assert LEAP in s19
    assert "support-table" in s19
    assert "$17.0" in s19 and "$18.9" in s19
    assert "support-cat-cell" in s19
    assert "support-cat-cell head" not in s19
    cfg19 = json.loads(re.search(r'id="cfg-s19-rev">(.*?)</script>', s19, re.S).group(1))
    by19 = {d["label"]: d for d in cfg19["data"]["datasets"]}
    assert by19["FX-adjusted"]["data"] == [8, 9, 11, 9, 10]
    assert by19["FX-adjusted"]["borderDash"] == []
    assert by19["Reported"]["data"] == [7, 9, 11, 10, 11]
    assert by19["Reported"]["borderDash"] == [8, 6]

    planned = plan_deck(validate_handoff(_load(), strict=True).deck, strict=True)
    by_sid = planned.by_surface_id()
    assert by_sid["s4-bb"].chart_paint["domain"]["ticks"] == TICKS_0_15
    assert by_sid["s5-ucs"].chart_paint["domain"]["ticks"] == TICKS_0_15
    assert by_sid["s9-comm"].chart_paint["domain"]["ticks"] == TICKS_0_15
    assert by_sid["s11-txn"].chart_paint["domain"]["ticks"] == TICKS_0_15
    assert by_sid["s19-rev"].chart_paint["domain"]["ticks"] == TICKS_0_15
    assert by_sid["s10-ics"].chart_paint["domain"]["ticks"] == TICKS_0_25
    assert by_sid["s19-rev"].chart_paint["domain"]["kind"] == "fixed"
    assert float(by_sid["s19-rev"].chart_paint["domain"]["max"]) == 15.0


def test_design_ledger_support_chrome_accepts_s4_s19_hide_header(
    tmp_path: Path,
) -> None:
    """#256: v14 support-chrome probe is green on canonical hide_header body cells."""
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    repo = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo / "scripts"))
    from simulation_probe import measured_support_chrome

    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    html_path = (out / "presentation.html").resolve()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(html_path.as_uri(), wait_until="networkidle")
        try:
            for n in (4, 19):
                row = measured_support_chrome(page, n, "single_chart")
                assert row["ok"] is True
                assert row["hide_header"] is True
                assert row["head_count"] == 0
                assert row["body_count"] >= 1
                assert any(
                    cell[k] >= 1.0
                    for cell in row["bodies"]
                    for k in (
                        "border_top_px",
                        "border_right_px",
                        "border_bottom_px",
                        "border_left_px",
                    )
                )
        finally:
            browser.close()


def test_mutation_dropping_s4_annotation_omits_callout_from_dom(tmp_path: Path) -> None:
    """Renderer does not invent the leap-year box; corpus must carry it."""
    handoff = _load()
    del _slide(handoff, 4)["payload"]["chart"]["annotations"]
    src = tmp_path / "h.json"
    src.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    s4 = _section((out / "presentation.html").read_text(encoding="utf-8"), 4)
    assert LEAP not in s4
    assert 'data-annotation-id="' not in s4
    assert "support-table" in s4  # table still paints; only the callout is gone


def test_mutation_dropping_s5_leap_and_context_omits_side_facts(tmp_path: Path) -> None:
    """Renderer does not invent Leap Year or G&S/T&E facts; corpus must carry them."""
    handoff = _load()
    chart = _slide(handoff, 5)["payload"]["chart"]
    del chart["annotations"]
    del chart["context_labels"]
    src = tmp_path / "h.json"
    src.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    s5 = _section((out / "presentation.html").read_text(encoding="utf-8"), 5)
    assert LEAP not in s5
    assert 'data-annotation-id="' not in s5
    assert 'data-context-id="' not in s5
    assert "9% YoY" not in s5
    assert "support-table" in s5


def test_mutation_dropping_s5_support_omits_generation_rows(tmp_path: Path) -> None:
    """Renderer does not invent the generation table; corpus must carry it."""
    handoff = _load()
    del _slide(handoff, 5)["payload"]["support"]
    src = tmp_path / "h.json"
    src.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    s5 = _section((out / "presentation.html").read_text(encoding="utf-8"), 5)
    assert "support-table" not in s5
    assert "Gen-Z" not in s5
    assert "38%" not in s5
