"""#335 — Q4 2021 s13 waterfall two-tone loans + receivables.

Seams under test:
- live Q4 handoff payload (`simulation/amex_q4_2021/handoff_v1.json`)
- authored WaterfallStep.components that foot each net
- frozen segment + structural placements on s13-rsv
- strict `render_deck` SVG overlay for slide 13
"""
from __future__ import annotations

import json
import re
from decimal import Decimal
from html import unescape
from pathlib import Path

from impact_slides.renderer_v3 import render_deck, validate_handoff
from impact_slides.renderer_v3.plan import plan_deck

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "simulation" / "amex_q4_2021" / "handoff_v1.json"

# PDF interiors; three nets foot via authored tenths that still paint as
# $5.6/$0.3, ($2.0)/($0.3), $3.4/$0.1.
S13_COMPONENTS = {
    "q1-20-beg": (("4.2", "0.1"), ("$4.2", "$0.1")),
    "to-q4-20": (("1.4", "0.1"), ("$1.4", "$0.1")),
    "q4-20-end": (("5.55", "0.25"), ("$5.6", "$0.3")),
    "to-q3-21": (("-1.95", "-0.25"), ("($2.0)", "($0.3)")),
    "q3-21-end": (("3.6", "0.0"), ("$3.6", "$0.0")),
    "q4-21-end": (("3.35", "0.05"), ("$3.4", "$0.1")),
}
S13_NETS = {
    "q1-20-beg": "4.3",
    "to-q4-20": "1.5",
    "q4-20-end": "5.8",
    "to-q3-21": "-2.2",
    "q3-21-end": "3.6",
    "to-q4-21": "-0.2",
    "q4-21-end": "3.4",
}
S13_SEG_LABELS = (
    "$4.2",
    "$0.1",
    "$1.4",
    "$5.6",
    "$0.3",
    "($2.0)",
    "($0.3)",
    "$3.6",
    "$0.0",
    "$3.4",
)
S13_STRUCTURAL = (
    "$4.3",
    "$1.5",
    "$5.8",
    "($2.2)",
    "$3.6",
    "($0.2)",
    "$3.4",
)


def _load() -> dict:
    return json.loads(HANDOFF.read_text(encoding="utf-8"))


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


def _box(p: dict, px: int) -> tuple[float, float, float, float]:
    w = max(20.0, len(str(p["text"])) * px * 0.55)
    return (
        p["x"] - w / 2,
        p["y"] - px / 2,
        p["x"] + w / 2,
        p["y"] + px / 2,
    )


def _assert_uncollided(cp: dict) -> None:
    lab_px = cp["role_sizes"]["structural_values"]
    cats = {
        p["category_id"]
        for p in cp["placements"]
        if p.get("kind") in {"segment", "structural"}
        and p.get("class") != "suppressed"
    }
    for cat in cats:
        col = [
            p
            for p in cp["placements"]
            if p.get("category_id") == cat
            and p.get("kind") in {"segment", "structural"}
            and p.get("class") != "suppressed"
        ]
        for i, a in enumerate(col):
            pa = _box(a, lab_px)
            for b in col[i + 1 :]:
                pb = _box(b, lab_px)
                assert not (
                    pa[0] < pb[2]
                    and pa[2] > pb[0]
                    and pa[1] < pb[3]
                    and pa[3] > pb[1]
                ), (cat, a.get("text"), a.get("class"), b.get("text"), b.get("class"))


def test_q4_s13_payload_authors_footing_components() -> None:
    chart = _slide(_load(), 13)["payload"]["chart"]
    assert chart["chart_type"] == "waterfall"
    steps = {s["category_id"]: s for s in chart["waterfall_data"]["steps"]}
    assert list(steps) == list(S13_NETS)
    for cid, net in S13_NETS.items():
        step = steps[cid]
        assert step["value"] == net
        assert step["role"] in {"total", "change"}
        if cid == "to-q4-21":
            assert not step.get("components")
            continue
        comps = step["components"]
        assert [c["series_id"] for c in comps] == ["loans", "receivables"]
        assert comps[0]["color"] == "primary_blue"
        assert comps[1]["color"] == "navy"
        loans, rec = S13_COMPONENTS[cid][0]
        assert comps[0]["value"] == loans
        assert comps[1]["value"] == rec
        assert Decimal(loans) + Decimal(rec) == Decimal(net)


def test_q4_s13_plan_paints_two_tone_and_uncollides() -> None:
    plan = plan_deck(validate_handoff(_load(), strict=True).deck, strict=True)
    sp = next(s for s in plan.surfaces if s.surface_id == "s13-rsv")
    cp = sp.chart_paint
    assert not cp.get("component_label_overflow")
    stacked = [b for b in cp["bars"] if b.get("components")]
    omitted = [b for b in cp["bars"] if not b.get("components")]
    assert len(stacked) == 6
    assert [b["category_id"] for b in omitted] == ["to-q4-21"]
    segs = [
        p["text"]
        for p in cp["placements"]
        if p.get("kind") == "segment" and p.get("class") != "suppressed"
    ]
    for token in S13_SEG_LABELS:
        assert token in segs
    assert segs.count("$0.1") == 3
    structs = [
        p["text"]
        for p in cp["placements"]
        if p.get("kind") == "structural"
    ]
    for token in S13_STRUCTURAL:
        assert token in structs
    _assert_uncollided(cp)


def test_q4_s13_strict_render_paints_two_tone(tmp_path: Path) -> None:
    out = tmp_path / "out"
    result = render_deck(HANDOFF, out, strict=True)
    assert result["ok"] is True
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["status"] == "clean"
    html = (out / "presentation.html").read_text(encoding="utf-8")
    s13 = unescape(_section(html, 13)).replace("<wbr>", "")
    assert 'data-chart-type="waterfall"' in s13
    assert s13.count('class="bar waterfall-segment"') == 12
    segs = re.findall(r'data-kind="segment"[^>]*>([^<]*)</text>', s13)
    for token in S13_SEG_LABELS:
        assert token in segs
    structs = re.findall(r'data-placement="structural"[^>]*>([^<]*)</text>', s13)
    for token in S13_STRUCTURAL:
        assert token in structs


def test_mutation_dropping_s13_components_returns_one_tone(tmp_path: Path) -> None:
    raw = _load()
    for step in _slide(raw, 13)["payload"]["chart"]["waterfall_data"]["steps"]:
        step.pop("components", None)
    src = tmp_path / "h.json"
    src.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    s13 = _section(html, 13)
    assert "waterfall-segment" not in s13
    assert "$0.1" not in re.findall(r'data-kind="segment"[^>]*>([^<]*)</text>', s13)
    structs = re.findall(r'data-placement="structural"[^>]*>([^<]*)</text>', s13)
    for token in S13_STRUCTURAL:
        assert token in structs
