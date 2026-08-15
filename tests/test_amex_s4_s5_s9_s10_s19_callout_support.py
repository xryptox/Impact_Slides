"""#226 — restore Leap-Year callouts + support tables on Amex slides 4/5/9/10/19.

Pins the live D314 corpus (not renderer defaults):
- s4/s19: explanation annotation + category-aligned support_table
- s5/s9/s10: independent support_table (s10 has no duplicate Reported callout)
- DOM on those sections shows the callout text / support rows
- strict render of the canonical corpus stays clean
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from impact_slides.renderer_v3 import render_deck

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
    anns = s4["payload"]["chart"]["annotations"]
    assert len(anns) == 1
    assert anns[0]["role"] == "explanation"
    assert anns[0]["text"] == LEAP
    assert anns[0]["anchor"] == {"type": "chart"}
    sup4 = _assert_support(s4, alignment="category", n_rows=2)
    cols4 = [c["column_id"] for c in sup4["table"]["columns"]]
    assert cols4 == CATS
    assert [r["label"] for r in sup4["table"]["rows"]] == ["G&S", "T&E"]
    assert _cell_values(sup4["table"]["rows"][0], cols4) == S4_GS
    assert _cell_values(sup4["table"]["rows"][1], cols4) == S4_TE

    s5 = _slide(handoff, 5)
    assert "annotations" not in s5["payload"]["chart"]
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
    assert "annotations" not in s9["payload"]["chart"]
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
    assert "annotations" not in s10["payload"]["chart"]
    sup10 = _assert_support(s10, alignment="independent", n_rows=2)
    assert [c["label"] for c in sup10["table"]["columns"]] == [
        "Intl Consumer",
        "Intl SME & Large Corp.",
        "Total",
    ]
    cols10 = [c["column_id"] for c in sup10["table"]["columns"]]
    assert _cell_values(sup10["table"]["rows"][0], cols10) == S10_YOY
    assert _cell_values(sup10["table"]["rows"][1], cols10) == S10_SHARE

    s19 = _slide(handoff, 19)
    anns19 = s19["payload"]["chart"]["annotations"]
    assert anns19[0]["text"] == LEAP
    assert anns19[0]["role"] == "explanation"
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

    s5 = _section(html, 5)
    assert "support-table" in s5
    assert "Gen-Z" in s5 and "Millennials" in s5
    assert "38%" in s5 and "100%" in s5
    assert LEAP not in s5

    s9 = _section(html, 9)
    assert "support-table" in s9
    assert "U.S. SME" in s9
    assert "81%" in s9

    s10 = _section(html, 10)
    assert "support-table" in s10
    assert "Intl Consumer" in s10
    assert "65%" in s10
    assert 'data-annotation-id="' not in s10

    s19 = _section(html, 19)
    assert LEAP in s19
    assert "support-table" in s19
    assert "$17.0" in s19 and "$18.9" in s19


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
