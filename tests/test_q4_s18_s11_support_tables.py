"""#346 — Q4 2021 s18 FY'21 inset + s11 30+/GCP strips as authored support.

Seams under test:
- live Q4 handoff payload (`simulation/amex_q4_2021/handoff_v1.json`)
- s18 independent FY'21 support_table (mirror s16-fy)
- s11 per-pane category support; NWO bars only; GCP Q2'21 (0.9)
- strict `render_deck` HTML chrome; drop-support mutations omit the tables
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

S11_CATS = ["q3-20", "q4-20", "q1-21", "q2-21", "q3-21", "q4-21"]
S11_LOANS_30 = ["1.2", "1.0", "0.9", "0.6", "0.7", "0.7"]
S11_REC_30 = ["0.9", "0.6", "0.6", "0.5", "0.5", "0.6"]
S11_GCP = ["2.4", "0.7", "0.4", "-0.9", "0.2", "0.2"]
S11_NWO = {
    "s11-loans": ["2.5", "1.9", "1.4", "1.0", "0.6", "0.6"],
    "s11-rec": ["2.0", "1.0", "0.5", "0.3", "0.2", "0.3"],
}
S18_YOY = [
    "10",
    "9",
    "9",
    "9",
    "1",
    "-28",
    "-20",
    "-18",
    "-13",
    "31",
    "24",
    "31",
]
S18_VS19 = [
    None,
    None,
    None,
    None,
    "-1",
    "-28",
    "-20",
    "-18",
    "-13",
    "-6",
    "-1",
    "7",
]


def _load() -> dict:
    return json.loads(HANDOFF.read_text(encoding="utf-8"))


def _slide(handoff: dict, n: int) -> dict:
    for s in handoff["slides"]:
        if int(s["slide_number"]) == n:
            return s
    raise AssertionError(f"missing slide_number={n}")


def _chart(pane: dict) -> dict:
    return pane["chart"] if "chart" in pane else pane


def _section(html: str, n: int) -> str:
    pat = rf'<section\b[^>]*\bdata-slide-number="{n}"[^>]*>'
    m = re.search(pat, html)
    assert m, f"no section data-slide-number={n}"
    start = m.start()
    nxt = re.search(r"<section\b", html[m.end() :])
    end = m.end() + nxt.start() if nxt else len(html)
    return html[start:end]


def _pane_html(section: str, idx: int) -> str:
    panes = section.split('class="dual-chart-pane"')[1:]
    assert len(panes) == 2, f"expected 2 dual panes, got {len(panes)}"
    return panes[idx]


def _cell_values(row: dict, col_ids: list[str]) -> list[str]:
    return [row["cells"][cid]["value"] for cid in col_ids]


def test_q4_s18_payload_authors_independent_fy_inset() -> None:
    slide = _slide(_load(), 18)
    assert slide["layout_type"] == "single_chart"
    payload = slide["payload"]
    chart = payload["chart"]
    assert chart["surface_id"] == "s18-rev"
    assert chart["chart_type"] == "line"
    series = {s["series_id"]: s["values"] for s in chart["chart_data"]["series"]}
    assert series["yoy"] == S18_YOY
    assert series["vs19"] == S18_VS19
    sup = payload["support"]
    assert sup["support_type"] == "support_table"
    assert sup["alignment"] == "independent"
    table = sup["table"]
    assert table["surface_id"] == "s18-fy"
    assert table["stub_header"]["label"] == "FY'21"
    assert [c["column_id"] for c in table["columns"]] == ["amt", "yoy", "vs19"]
    assert [c["label"] for c in table["columns"]] == ["$B", "YoY", "vs. '19"]
    row = table["rows"][0]
    assert row["label"] == "Revenue"
    assert row["cells"]["amt"]["value"] == "42.4"
    assert row["cells"]["yoy"]["value"] == "17"
    assert row["cells"]["vs19"]["value"] == "-3"


def test_q4_s11_payload_authors_category_strips_not_dq_bars() -> None:
    slide = _slide(_load(), 11)
    assert slide["layout_type"] == "dual_chart"
    payload = slide["payload"]
    assert "support" not in payload
    panes = payload["charts"]
    assert len(panes) == 2
    loans, rec = panes
    for pane, sid, nwo in (
        (loans, "s11-loans", S11_NWO["s11-loans"]),
        (rec, "s11-rec", S11_NWO["s11-rec"]),
    ):
        chart = _chart(pane)
        assert chart["surface_id"] == sid
        series = chart["chart_data"]["series"]
        assert [s["series_id"] for s in series] == ["nwo"]
        assert series[0]["values"] == nwo
        domain = chart["value_axes"]["primary"]["domain"]
        assert domain == {
            "kind": "fixed",
            "min": "0",
            "max": "5",
            "ticks": ["0", "1", "2", "3", "4", "5"],
        }
        sup = pane["support"]
        assert sup["support_type"] == "support_table"
        assert sup["alignment"] == "category"
        cols = [c["column_id"] for c in sup["table"]["columns"]]
        assert cols == S11_CATS
    loans_rows = {r["label"]: r for r in loans["support"]["table"]["rows"]}
    assert list(loans_rows) == ["30+ Days Past Due"]
    assert _cell_values(loans_rows["30+ Days Past Due"], S11_CATS) == S11_LOANS_30
    rec_rows = {r["label"]: r for r in rec["support"]["table"]["rows"]}
    assert list(rec_rows) == ["30+ Days Past Due*", "GCP Net Write-off Rates**"]
    assert _cell_values(rec_rows["30+ Days Past Due*"], S11_CATS) == S11_REC_30
    assert _cell_values(rec_rows["GCP Net Write-off Rates**"], S11_CATS) == S11_GCP
    gcp_q2 = rec_rows["GCP Net Write-off Rates**"]["cells"]["q2-21"]
    assert gcp_q2["value"] == "-0.9"
    assert gcp_q2["format_id"] == "pct_1p"


def test_q4_s18_s11_strict_render_paints_support(tmp_path: Path) -> None:
    out = tmp_path / "out"
    result = render_deck(HANDOFF, out, strict=True)
    assert result["ok"] is True
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["status"] == "clean"
    assert meta["severity_counts"].get("error", 0) == 0
    html = unescape((out / "presentation.html").read_text(encoding="utf-8"))
    s18 = _section(html, 18)
    assert 'data-layout="single_chart"' in s18
    assert 'data-table-surface="s18-fy"' in s18
    assert "FY'21" in s18
    assert "42.4" in s18
    assert "17%" in s18
    assert "(3%)" in s18
    s11 = _section(html, 11)
    assert 'data-layout="dual_chart"' in s11
    loans = unescape(_pane_html(s11, 0))
    rec = unescape(_pane_html(s11, 1))
    assert 'data-table-surface="s11-loans-tbl"' in loans
    assert "support-table category-aligned" in loans
    assert "30+ Days Past Due" in loans
    for token in ("1.2%", "1.0%", "0.9%", "0.6%", "0.7%"):
        assert token in loans
    assert 'data-table-surface="s11-rec-tbl"' in rec
    assert "support-table category-aligned" in rec
    assert "30+ Days Past Due*" in rec
    assert "GCP Net Write-off Rates**" in rec
    assert "(0.9%)" in rec
    assert "-0.9%" not in rec
    plan = plan_deck(validate_handoff(_load(), strict=True).deck, strict=True)
    loans_paint = plan.by_surface_id()["s11-loans"].chart_paint
    rec_paint = plan.by_surface_id()["s11-rec"].chart_paint
    assert [s["series_id"] for s in loans_paint["series"]] == ["nwo"]
    assert [s["series_id"] for s in rec_paint["series"]] == ["nwo"]
    assert len([b for b in loans_paint["bars"] if b.get("finite", True)]) == 6
    assert len([b for b in rec_paint["bars"] if b.get("finite", True)]) == 6
    assert loans_paint["domain"]["min"] == "0"
    assert loans_paint["domain"]["max"] == "5"
    assert rec_paint["domain"]["max"] == "5"
    assert "unresolved_overflow" not in {
        ev.get("code")
        for ev in (meta.get("events") or [])
        if isinstance(ev, dict)
    }


def test_mutation_dropping_s18_support_omits_fy_table(tmp_path: Path) -> None:
    raw = _load()
    _slide(raw, 18)["payload"].pop("support", None)
    src = tmp_path / "h.json"
    src.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    s18 = _section(html, 18)
    assert 'data-table-surface="s18-fy"' not in s18


def test_mutation_dropping_s11_pane_support_omits_strips(tmp_path: Path) -> None:
    raw = _load()
    for pane in _slide(raw, 11)["payload"]["charts"]:
        pane.pop("support", None)
    raw.get("number_formats", {}).pop("pct_1p", None)
    src = tmp_path / "h.json"
    src.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    s11 = _section(html, 11)
    assert 'data-table-surface="s11-loans-tbl"' not in s11
    assert 'data-table-surface="s11-rec-tbl"' not in s11
    assert "support-table category-aligned" not in s11
