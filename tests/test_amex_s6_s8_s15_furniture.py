"""#227 — restore s8 KPI strip, s15 reserve-rate row, s6 +6pp elbow.

Pins the live D314 corpus (not renderer defaults):
- s6 left chart: PDF elbow annotation "+ ~6 percentage points"
- s8: metric_strip with 3,400+ / 300+ / $600 / $550
- s15: outlined reserve-rate row + authored stack totals
- DOM on those sections shows the furniture; renderer does not invent it
- strict render of the canonical corpus stays clean
"""

from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

from impact_slides.renderer_v3 import render_deck, validate_handoff
from impact_slides.renderer_v3.plan import plan_deck

FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "renderer_v3"
    / "canonical_amex_handoff_v1.json"
)

ELBOW = "+ ~6 percentage points"
CATS = ["q1-25", "q2-25", "q3-25", "q4-25", "q1-26"]
S8_VALUES = ("3,400+", "300+", "$600", "$550")
S15_RATES = ["2.9", "2.8", "2.8", "2.8", "2.8"]
S15_TOTALS = ["1150", "1405", "1287", "1414", "1251"]
S15_LABEL = "Reserve Rate for Total Balances"


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


def test_corpus_payloads_carry_s6_s8_s15_furniture() -> None:
    handoff = _load()

    s6 = _slide(handoff, 6)
    left = s6["payload"]["charts"][0]
    anns = left["annotations"]
    assert len(anns) == 1
    assert anns[0]["role"] == "explanation"
    assert anns[0]["text"] == ELBOW
    assert anns[0]["anchor"] == {
        "type": "category_range",
        "from_category_id": "q1-25",
        "to_category_id": "q1-26",
    }
    assert "annotations" not in s6["payload"]["charts"][1]

    s8 = _slide(handoff, 8)
    strip = s8["payload"]["support"]
    assert strip["support_type"] == "metric_strip"
    assert len(strip["metrics"]) == 4
    visibles = []
    for m in strip["metrics"]:
        val = m["value"]
        if val["type"] == "text":
            visibles.append(val["text"])
        else:
            visibles.append(val["value"])
    assert visibles == ["3,400+", "300+", "600", "550"]
    assert strip["metrics"][2]["value"]["format_id"] == "usd_0"
    assert strip["metrics"][3]["value"]["format_id"] == "usd_0"

    s15 = _slide(handoff, 15)
    support = s15["payload"]["support"]
    assert support["support_type"] == "outlined_support"
    cols = [c["column_id"] for c in support["table"]["columns"]]
    assert cols == CATS
    row = support["table"]["rows"][0]
    assert support["table"]["stub_header"]["label"] == S15_LABEL
    assert row["label"] == S15_LABEL
    assert [row["cells"][cid]["value"] for cid in cols] == S15_RATES
    assert all(row["cells"][cid]["format_id"] == "pct_1" for cid in cols)
    aux = s15["payload"]["chart"]["auxiliary_series"]
    assert aux[0]["role"] == "authored_stack_total"
    assert aux[0]["values"] == S15_TOTALS


def test_strict_render_shows_s6_s8_s15_furniture(tmp_path: Path) -> None:
    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["status"] == "clean"
    assert meta["ok"] is True
    assert meta["severity_counts"].get("error", 0) == 0

    html = (out / "presentation.html").read_text(encoding="utf-8")

    s6 = _section(html, 6)
    assert ELBOW in s6
    assert 'data-annotation-id="' in s6

    s8 = _section(html, 8)
    assert "metric-strip" in s8
    assert 'data-metric-strip="' in s8
    for token in S8_VALUES:
        assert token in s8

    s15 = _section(html, 15)
    s15_vis = unescape(s15).replace("<wbr>", "")
    assert 'data-outlined-support="' in s15
    assert S15_LABEL in s15_vis
    assert "2.9%" in s15 and "2.8%" in s15
    assert "$1,150" in s15 and "$1,251" in s15

    result = validate_handoff(_load(), strict=True)
    plan = plan_deck(result.deck, strict=True)
    chart = next(s for s in plan.surfaces if s.surface_id == "s15-prov")
    cat_x = [c["x"] for c in chart.chart_paint["categories"]]
    lefts = [
        float(x)
        for x in re.findall(r"outlined-support-box[^>]*left:([0-9.]+)px", s15)
    ]
    assert len(lefts) == 5
    for painted, frozen in zip(lefts, cat_x):
        assert abs(painted - frozen) <= 2.0


def test_mutation_dropping_s6_annotation_omits_elbow(tmp_path: Path) -> None:
    """Renderer does not invent the +6pp elbow; corpus must carry it."""
    handoff = _load()
    del _slide(handoff, 6)["payload"]["charts"][0]["annotations"]
    src = tmp_path / "h.json"
    src.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    s6 = _section((out / "presentation.html").read_text(encoding="utf-8"), 6)
    assert 'data-annotation-id="' not in s6
    assert "chart-annotation" not in s6


def test_mutation_dropping_s8_strip_omits_kpi_stack(tmp_path: Path) -> None:
    """Renderer does not invent the lodging KPI strip; corpus must carry it."""
    handoff = _load()
    del _slide(handoff, 8)["payload"]["support"]
    src = tmp_path / "h.json"
    src.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    s8 = _section((out / "presentation.html").read_text(encoding="utf-8"), 8)
    assert "metric-strip" not in s8
    assert 'data-metric-strip="' not in s8


def test_mutation_dropping_s15_support_omits_reserve_row(tmp_path: Path) -> None:
    """Renderer does not invent the reserve-rate row; corpus must carry it."""
    handoff = _load()
    del _slide(handoff, 15)["payload"]["support"]
    src = tmp_path / "h.json"
    src.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    s15 = _section((out / "presentation.html").read_text(encoding="utf-8"), 15)
    assert "outlined-support" not in s15
    assert S15_LABEL not in s15
