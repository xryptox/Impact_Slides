"""#323 — Q4 2021 s28 two-row category support boxes keep a readable row gap.

Seams under test:
- live Q4 handoff payload (`simulation/amex_q4_2021/handoff_v1.json`)
- strict `render_deck` HTML + frozen plan geometry for s28-boxes
"""
from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

from impact_slides.renderer_v3 import render_deck, validate_handoff
from impact_slides.renderer_v3.plan import CATEGORY_SUPPORT_ROW_GAP, plan_deck

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "simulation" / "amex_q4_2021" / "handoff_v1.json"

LOANS = ["1.9", "7.1", "3.0", "1.7", "1.6"]
RECV = ["0.9", "4.4", "1.0", "0.6", "0.6"]
COLS = ["dec-19", "apr-20", "dec-20", "sep-21", "dec-21"]


def _load() -> dict:
    return json.loads(HANDOFF.read_text(encoding="utf-8"))


def _s28(handoff: dict) -> dict:
    for s in handoff["slides"]:
        if int(s["slide_number"]) == 28:
            return s
    raise AssertionError("missing slide_number=28")


def _section(html: str, n: int) -> str:
    pat = rf'<section\b[^>]*\bdata-slide-number="{n}"[^>]*>'
    m = re.search(pat, html)
    assert m, f"no section data-slide-number={n}"
    start = m.start()
    nxt = re.search(r"<section\b", html[m.end() :])
    end = m.end() + nxt.start() if nxt else len(html)
    return html[start:end]


def _cell_values(row: dict) -> list[str]:
    return [row["cells"][cid]["value"] for cid in COLS]


def test_q4_s28_payload_keeps_category_two_row_boxes() -> None:
    sup = _s28(_load())["payload"]["support"]
    assert sup["support_type"] == "support_table"
    assert sup["alignment"] == "category"
    table = sup["table"]
    assert table["surface_id"] == "s28-boxes"
    rows = {r["label"]: r for r in table["rows"]}
    assert list(rows) == ["Total Loans", "Card Member Receivables"]
    assert _cell_values(rows["Total Loans"]) == LOANS
    assert _cell_values(rows["Card Member Receivables"]) == RECV


def test_q4_s28_plan_freezes_two_row_category_gap() -> None:
    result = validate_handoff(_load(), strict=True)
    plan = plan_deck(result.deck, strict=True)
    chart = next(s for s in plan.surfaces if s.surface_id == "s28-frp")
    support = next(s for s in plan.surfaces if s.surface_id == "s28-boxes")
    assert support.table_paint["n_rows"] == 2
    assert support.table_paint["category_centered"] is True
    assert support.table_paint["alignment"] == "category"
    assert support.table_paint["row_gap"] == CATEGORY_SUPPORT_ROW_GAP
    assert support.table_paint["row_gap"] >= 8
    # Wrapped "Card Member Receivables" must own its own row box, not the loans row.
    assert int(support.table_paint["row_h"]) >= 2 * int(support.role_sizes["table"])
    cat_x = {c["category_id"]: c["x"] for c in chart.chart_paint["categories"]}
    for c in support.table_paint["centers"]:
        assert abs(c["x"] - cat_x[c["category_id"]]) <= 2.0


def test_q4_s28_strict_render_separates_support_rows(tmp_path: Path) -> None:
    out = tmp_path / "out"
    result = render_deck(HANDOFF, out, strict=True)
    assert result["ok"] is True
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["status"] == "clean"
    html = (out / "presentation.html").read_text(encoding="utf-8")
    section = unescape(_section(html, 28)).replace("<wbr>", "")
    assert 'data-table-surface="s28-boxes"' in section
    assert "support-table category-aligned" in section
    assert 'data-category-centered="true"' in section
    vis = section.split('class="support-table category-aligned"', 1)[1]
    assert re.search(r'class="support-cat-cell[^"]*\bhead\b', vis) is None
    assert "Total Loans" in section
    assert "Card Member Receivables" in section
    for token in ("$1.9", "$7.1", "$3.0", "$1.7", "$1.6", "$0.9", "$4.4", "$1.0", "$0.6"):
        assert token in section
    tops = [
        int(t)
        for t in re.findall(r'class="support-cat-cell(?: num)?"[^>]*top:(\d+)px', vis)
    ]
    assert len(tops) == 10
    row0, row1 = set(tops[:5]), set(tops[5:])
    assert len(row0) == 1 and len(row1) == 1
    delta = next(iter(row1)) - next(iter(row0))
    plan = plan_deck(validate_handoff(_load(), strict=True).deck, strict=True)
    support = next(s for s in plan.surfaces if s.surface_id == "s28-boxes")
    assert delta == int(support.table_paint["row_h"]) + int(support.table_paint["row_gap"])
    assert int(support.table_paint["row_gap"]) == CATEGORY_SUPPORT_ROW_GAP


def test_mutation_independent_alignment_paints_navy_grid_not_boxes(
    tmp_path: Path,
) -> None:
    raw = _load()
    _s28(raw)["payload"]["support"]["alignment"] = "independent"
    src = tmp_path / "h.json"
    src.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    section = _section(html, 28)
    assert 'data-table-surface="s28-boxes"' in section
    assert "support-table category-aligned" not in section
    assert 'data-category-centered="true"' not in section
    assert 'class="band-table-header align-left stub"' in section
