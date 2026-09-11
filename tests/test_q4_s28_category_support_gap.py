"""#323/#342 — Q4 2021 s28 two-row category support boxes.

Seams under test:
- live Q4 handoff payload (`simulation/amex_q4_2021/handoff_v1.json`)
- strict `render_deck` HTML + frozen plan geometry for s28-boxes
- #342: 24px row gap, stub-safe grow-to-max cell_w, borderless stubs
"""
from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

from impact_slides.renderer_v3 import render_deck, validate_handoff
from impact_slides.renderer_v3.plan import (
    CATEGORY_SUPPORT_ROW_GAP,
    OUTLINED_BOX_GAP,
    OUTLINED_BOX_MAX,
    plan_deck,
)

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
    assert support.table_paint["row_gap"] == 24
    # Wrapped "Card Member Receivables" must own its own row box, not the loans row.
    assert int(support.table_paint["row_h"]) >= 2 * int(support.role_sizes["table"])
    cat_x = {c["category_id"]: c["x"] for c in chart.chart_paint["categories"]}
    for c in support.table_paint["centers"]:
        assert abs(c["x"] - cat_x[c["category_id"]]) <= 2.0
    cell_w = int(support.table_paint["cell_w"])
    lane_w = int(support.table_paint["label_lane_w"])
    first_x = float(support.table_paint["centers"][0]["x"])
    first_left = first_x - cell_w / 2.0
    assert cell_w > 43
    assert cell_w <= OUTLINED_BOX_MAX
    assert first_left >= lane_w + OUTLINED_BOX_GAP - 1e-6


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
    assert int(support.table_paint["row_gap"]) == 24
    assert re.search(
        r'class="support-cat-cell(?: num)?"[^>]*text-align:center',
        vis,
    )
    assert re.search(
        r'class="support-cat-cell(?: num)?"[^>]*justify-content:center',
        vis,
    )


def test_q4_s28_stub_safe_boxes_do_not_intersect_lane() -> None:
    result = validate_handoff(_load(), strict=True)
    plan = plan_deck(result.deck, strict=True)
    chart = next(s for s in plan.surfaces if s.surface_id == "s28-frp")
    support = next(s for s in plan.surfaces if s.surface_id == "s28-boxes")
    cell_w = int(support.table_paint["cell_w"])
    lane_w = int(support.table_paint["label_lane_w"])
    first_x = float(support.table_paint["centers"][0]["x"])
    first_left = first_x - cell_w / 2.0
    stub_clear = lane_w + OUTLINED_BOX_GAP
    pitch = min(
        float(c["x"]) - float(p["x"])
        for p, c in zip(
            support.table_paint["centers"], support.table_paint["centers"][1:]
        )
    )
    pitch_cap = int(pitch - OUTLINED_BOX_GAP)
    stub_cap = int(2 * (first_x - stub_clear))
    expected = min(OUTLINED_BOX_MAX, pitch_cap, stub_cap)
    assert cell_w == expected
    assert first_left >= stub_clear - 1e-6
    cat0 = chart.chart_paint["categories"][0]
    assert abs(first_x - float(cat0["x"])) <= 2.0


def test_q4_s28_computed_stub_borderless_and_centered_dollars(tmp_path: Path) -> None:
    import pytest

    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    out = tmp_path / "out"
    assert render_deck(HANDOFF, out, strict=True)["ok"] is True
    html_path = (out / "presentation.html").resolve()
    plan = plan_deck(validate_handoff(_load(), strict=True).deck, strict=True)
    support = next(s for s in plan.surfaces if s.surface_id == "s28-boxes")
    cell_w = int(support.table_paint["cell_w"])
    lane_w = int(support.table_paint["label_lane_w"])

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(html_path.as_uri(), wait_until="networkidle")
        styles = page.evaluate(
            """() => {
              const slide = document.querySelector(
                'section.slide[data-slide-number="28"]'
              );
              const vis = (el) => {
                const r = el.getBoundingClientRect();
                return r.width > 1 && r.height > 1;
              };
              const pack = (el) => {
                const s = getComputedStyle(el);
                const r = el.getBoundingClientRect();
                return {
                  borderTop: s.borderTopWidth,
                  borderRight: s.borderRightWidth,
                  borderBottom: s.borderBottomWidth,
                  borderLeft: s.borderLeftWidth,
                  textAlign: s.textAlign,
                  justify: s.justifyContent,
                  left: r.left,
                  right: r.right,
                  top: r.top,
                  bottom: r.bottom,
                };
              };
              const visRoot = slide.querySelector(
                '.support-table.category-aligned'
              );
              const stubs = [...visRoot.querySelectorAll('.support-cat-stub')].filter(vis);
              const cells = [...visRoot.querySelectorAll('.support-cat-cell')].filter(
                (el) => vis(el) && !el.classList.contains('head')
              );
              return {stubs: stubs.map(pack), cells: cells.map(pack)};
            }"""
        )
        browser.close()

    assert len(styles["stubs"]) == 2
    assert len(styles["cells"]) == 10
    for stub in styles["stubs"]:
        assert stub["borderTop"] == "0px"
        assert stub["borderRight"] == "0px"
        assert stub["borderBottom"] == "0px"
        assert stub["borderLeft"] == "0px"
    for cell in styles["cells"]:
        assert cell["borderTop"] == "1px"
        assert cell["borderRight"] == "1px"
        assert cell["borderBottom"] == "1px"
        assert cell["borderLeft"] == "1px"
        assert cell["textAlign"] == "center"
        assert cell["justify"] == "center"
    stub_right = max(s["right"] for s in styles["stubs"])
    first_col = sorted(styles["cells"], key=lambda c: c["left"])[:2]
    for cell in first_col:
        assert cell["left"] >= stub_right
    assert abs(first_col[0]["right"] - first_col[0]["left"] - cell_w) <= 2.0
    assert lane_w > 0


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
