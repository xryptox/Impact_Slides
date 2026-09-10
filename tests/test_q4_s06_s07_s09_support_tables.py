"""#316/#336 — Q4 2021 s06/s07/s09 under-plot tables are independent navy grids.

Seams under test:
- live Q4 handoff payload (`simulation/amex_q4_2021/handoff_v1.json`)
- strict `render_deck` HTML chrome on those four supports
- both per-pane independent tables freeze the larger type (24px)
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

TARGETS = (
    (6, 1, "s06-age-tbl", ["millennial", "gen-x", "boomer"]),
    (7, 1, "s07-sme-tbl", ["sme-gs", "sme-tot", "lg-tot"]),
    (9, 0, "s09-us-tbl", ["us", "intl", "total"]),
    (9, 1, "s09-gs-tbl", ["us-gs", "intl-gs", "tot-gs", "us-te", "intl-te", "tot-te"]),
)
LEFT_INDEP = (
    (6, 0, "s06-mix-tbl"),
    (7, 0, "s07-mix-tbl"),
)
S06_AGE = {
    "vs. '19": ["50", "17", "0"],
    "YoY": ["51", "34", "26"],
    "% of Total": ["28", "39", "33"],
}
S07_SME = {
    "vs. '19": ["25", "17", "-33"],
    "YoY": ["21", "29", "34"],
    "% of Total": ["74", "85", "15"],
}
S09_US = {
    "vs. '19": ["16", "-1", "12"],
    "YoY": ["33", "32", "33"],
    "% of Total": ["78", "22", "100"],
}
S09_GS = {
    "vs. '19": ["26", "19", "24", "-10", "-36", "-18"],
    "YoY": ["20", "17", "19", "134", "127", "132"],
    "% of Total": ["62", "17", "79", "15", "5", "21"],
}
FIGURES = {
    "s06-age-tbl": S06_AGE,
    "s07-sme-tbl": S07_SME,
    "s09-us-tbl": S09_US,
    "s09-gs-tbl": S09_GS,
}


def _load() -> dict:
    return json.loads(HANDOFF.read_text(encoding="utf-8"))


def _slide(handoff: dict, n: int) -> dict:
    for s in handoff["slides"]:
        if int(s["slide_number"]) == n:
            return s
    raise AssertionError(f"missing slide_number={n}")


def _pane(slide: dict, idx: int) -> dict:
    return slide["payload"]["charts"][idx]


def _support(slide: dict, idx: int) -> dict:
    return _pane(slide, idx)["support"]


def _cell_values(row: dict, col_ids: list[str]) -> list[str]:
    return [row["cells"][cid]["value"] for cid in col_ids]


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


def test_q4_s06_s07_s09_payload_is_independent_navy_grid() -> None:
    handoff = _load()
    for n, idx, sid, cols in TARGETS:
        sup = _support(_slide(handoff, n), idx)
        assert sup["support_type"] == "support_table"
        assert sup["alignment"] == "independent", sid
        table = sup["table"]
        assert table["surface_id"] == sid
        assert table["stub_header"]["label"] == "Q4'21"
        assert [c["column_id"] for c in table["columns"]] == cols
        by_label = {r["label"]: r for r in table["rows"]}
        assert list(by_label) == ["vs. '19", "YoY", "% of Total"]
        for label, expected in FIGURES[sid].items():
            assert _cell_values(by_label[label], cols) == expected
    for n, idx, sid in LEFT_INDEP:
        sup = _support(_slide(handoff, n), idx)
        assert sup["alignment"] == "independent", sid
        assert sup["table"]["surface_id"] == sid


def test_q4_s06_s07_s09_strict_render_paints_connected_navy_tables(
    tmp_path: Path,
) -> None:
    out = tmp_path / "out"
    result = render_deck(HANDOFF, out, strict=True)
    assert result["ok"] is True
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["status"] == "clean"
    assert meta["severity_counts"].get("error", 0) == 0
    html = (out / "presentation.html").read_text(encoding="utf-8")
    for n, idx, sid, _cols in TARGETS:
        pane = unescape(_pane_html(_section(html, n), idx))
        assert f'data-table-surface="{sid}"' in pane
        assert "support-table category-aligned" not in pane
        assert 'data-category-centered="true"' not in pane
        assert 'class="band-table-header align-left stub"' in pane
        assert "Q4'21" in pane
        assert "vs. '19" in pane and "YoY" in pane and "% of Total" in pane
    s06_left = _pane_html(_section(html, 6), 0)
    s07_left = _pane_html(_section(html, 7), 0)
    assert 'data-table-surface="s06-mix-tbl"' in s06_left
    assert "support-table category-aligned" not in s06_left
    assert 'class="band-table-header align-left stub"' in s06_left
    assert 'data-table-surface="s07-mix-tbl"' in s07_left
    assert "support-table category-aligned" not in s07_left
    assert "50%" in _section(html, 6)
    assert "(33%)" in _section(html, 7)
    assert "(1%)" in _section(html, 9)
    assert "(36%)" in _section(html, 9)


PAIRS = (
    (6, "s06-mix-tbl", "s06-age-tbl"),
    (7, "s07-mix-tbl", "s07-sme-tbl"),
    (9, "s09-us-tbl", "s09-gs-tbl"),
)


def test_q4_s06_s07_s09_independent_tables_freeze_larger_type(
    tmp_path: Path,
) -> None:
    plan = plan_deck(validate_handoff(_load(), strict=True).deck, strict=True)
    by = plan.by_surface_id()
    for _n, left_id, right_id in PAIRS:
        left = by[left_id]
        right = by[right_id]
        assert left.role_sizes["table"] == right.role_sizes["table"] == 24
        assert left.table_paint["alignment"] == "independent"
        assert right.table_paint["alignment"] == "independent"
        assert left.table_paint["col_widths"] != right.table_paint["col_widths"]
    out = tmp_path / "out"
    result = render_deck(HANDOFF, out, strict=True)
    assert result["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    for n, left_id, right_id in PAIRS:
        section = _section(html, n)
        left = _pane_html(section, 0)
        right = _pane_html(section, 1)
        assert f'data-table-surface="{left_id}"' in left
        assert f'data-table-surface="{right_id}"' in right
        left_tbl = re.search(
            rf'<table[^>]*data-table-surface="{re.escape(left_id)}"[^>]*>',
            left,
        ).group(0)
        right_tbl = re.search(
            rf'<table[^>]*data-table-surface="{re.escape(right_id)}"[^>]*>',
            right,
        ).group(0)
        assert "font-size:24px" in left_tbl
        assert "font-size:24px" in right_tbl
        assert "font-size:14px" not in left_tbl
        assert "font-size:14px" not in right_tbl


def test_mutation_category_alignment_paints_boxes_not_navy_grid(
    tmp_path: Path,
) -> None:
    raw = _load()
    for n, idx, _sid, _cols in TARGETS:
        _support(_slide(raw, n), idx)["alignment"] = "category"
    src = tmp_path / "h.json"
    src.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    for n, idx, sid, _cols in TARGETS:
        pane = _pane_html(_section(html, n), idx)
        assert f'data-table-surface="{sid}"' in pane
        assert "support-table category-aligned" in pane
        assert 'data-category-centered="true"' in pane
