"""#324/#343 — Q4 2021 s28/s31 stacked labels stay below the crown.

Seams under test:
- live Q4 handoff payload (`simulation/amex_q4_2021/handoff_v1.json`)
- frozen `_place_stack_labels` placements on s28-frp / s31-fund
- strict `render_deck` SVG overlay for those slides
- inside-navy on tall sky bands; $ totals own the above-stack lane
"""
from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

from impact_slides.renderer_v3 import render_deck, validate_handoff
from impact_slides.renderer_v3.plan import plan_deck
from impact_slides.renderer_v3.theme import resolve_color

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "simulation" / "amex_q4_2021" / "handoff_v1.json"

S28_SEGS = (
    "$2.1",
    "$0.7",
    "$0.0",
    "$2.0",
    "$0.9",
    "$8.5",
    "$1.0",
    "$3.0",
    "$0.8",
    "$1.5",
    "$0.9",
    "$1.3",
)
S28_TOTS = ("$2.8", "$11.5", "$4.0", "$2.3", "$2.2")
S31_SEGS = ("28%", "14%", "53%", "4%", "23%", "10%", "66%", "1%", "20%", "11%", "67%", "2%")
S31_TOTS = ("$138", "$132", "$126")


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


def _column_stack_top(cp: dict, cat: str) -> float:
    ys = [
        float(b["y"])
        for b in cp["bars"]
        if b.get("category_id") == cat
        and b.get("finite")
        and not b.get("missing")
        and float(b.get("height") or 0) > 0
    ]
    assert ys, cat
    return min(ys)


def _assert_crown_owned(cp: dict) -> None:
    seg_px = cp["role_sizes"]["segment_labels"]
    tot_px = cp["role_sizes"]["stack_totals"]
    cats = {
        p["category_id"]
        for p in cp["placements"]
        if p.get("kind") in {"segment", "stack_total"}
        and p.get("class") != "suppressed"
    }
    for cat in cats:
        crown = _column_stack_top(cp, cat)
        for p in cp["placements"]:
            if p.get("category_id") != cat or p.get("class") == "suppressed":
                continue
            if p.get("kind") == "segment":
                top = _box(p, seg_px)[1]
                assert top >= crown, (cat, p.get("text"), p.get("class"), top, crown)
            elif p.get("kind") == "stack_total":
                top = _box(p, tot_px)[1]
                assert top < crown, (cat, p.get("text"), top, crown)


def _assert_uncollided(cp: dict) -> None:
    seg_px = cp["role_sizes"]["segment_labels"]
    tot_px = cp["role_sizes"]["stack_totals"]
    cats = {
        p["category_id"]
        for p in cp["placements"]
        if p.get("kind") in {"segment", "stack_total"}
        and p.get("class") != "suppressed"
    }
    for cat in cats:
        col = [
            p
            for p in cp["placements"]
            if p.get("category_id") == cat
            and p.get("kind") in {"segment", "stack_total"}
            and p.get("class") != "suppressed"
        ]
        for i, a in enumerate(col):
            pa = _box(a, tot_px if a["kind"] == "stack_total" else seg_px)
            for b in col[i + 1 :]:
                pb = _box(b, tot_px if b["kind"] == "stack_total" else seg_px)
                assert not (
                    pa[0] < pb[2]
                    and pa[2] > pb[0]
                    and pa[1] < pb[3]
                    and pa[3] > pb[1]
                ), (cat, a.get("text"), a.get("class"), b.get("text"), b.get("class"))


def test_q4_s28_payload_keeps_stack_segments_show() -> None:
    chart = _slide(_load(), 28)["payload"]["chart"]
    assert chart["display"]["stack_segments"] == "show"
    assert chart["display"]["stack_totals"] == "show"
    series = chart["chart_data"]["series"]
    assert [s["series_id"] for s in series] == ["delinq", "frp", "cpr"]
    assert series[2]["values"] == ["0.0", "8.5", "0.0", "0.0", "0.0"]
    aux = chart["auxiliary_series"][0]["values"]
    assert aux == ["2.8", "11.5", "4.0", "2.3", "2.2"]


def test_q4_s31_payload_keeps_stack_segments_show() -> None:
    chart = _slide(_load(), 31)["payload"]["chart"]
    assert chart["display"]["stack_segments"] == "show"
    assert chart["display"]["stack_totals"] == "show"
    series = chart["chart_data"]["series"]
    assert [s["series_id"] for s in series] == ["unsec", "abs", "dep", "st"]
    assert series[3]["values"] == ["4", "1", "2"]
    aux = chart["auxiliary_series"][0]["values"]
    assert aux == ["138", "132", "126"]


def test_q4_s28_s31_plan_uncollides_column_labels() -> None:
    plan = plan_deck(validate_handoff(_load(), strict=True).deck, strict=True)
    s28 = next(s for s in plan.surfaces if s.surface_id == "s28-frp")
    s31 = next(s for s in plan.surfaces if s.surface_id == "s31-fund")
    segs28 = [
        p["text"]
        for p in s28.chart_paint["placements"]
        if p.get("kind") == "segment" and p.get("class") != "suppressed"
    ]
    tots28 = [
        p["text"]
        for p in s28.chart_paint["placements"]
        if p.get("kind") == "stack_total"
    ]
    for token in S28_SEGS:
        assert token in segs28
    for token in S28_TOTS:
        assert token in tots28
    segs31 = [
        p["text"]
        for p in s31.chart_paint["placements"]
        if p.get("kind") == "segment" and p.get("class") != "suppressed"
    ]
    tots31 = [
        p["text"]
        for p in s31.chart_paint["placements"]
        if p.get("kind") == "stack_total"
    ]
    for token in S31_SEGS:
        assert token in segs31
    for token in S31_TOTS:
        assert token in tots31
    navy = resolve_color("navy", role="text_on_light")
    sky_inside = [
        p
        for p in s31.chart_paint["placements"]
        if p.get("kind") == "segment" and p.get("text") in {"53%", "66%", "67%"}
    ]
    assert len(sky_inside) == 3
    for p in sky_inside:
        assert p["class"] == "inside", p
        assert p["color"] == navy, p
    cpr = next(
        p
        for p in s28.chart_paint["placements"]
        if p.get("kind") == "segment" and p.get("text") == "$8.5"
    )
    assert cpr["class"] == "inside"
    assert cpr["color"] == navy
    zeros = [
        p
        for p in s28.chart_paint["placements"]
        if p.get("kind") == "segment" and p.get("text") == "$0.0"
    ]
    assert zeros
    for p in zeros:
        assert p["class"] != "suppressed"
        assert p["class"] != "outside_above"
    _assert_uncollided(s28.chart_paint)
    _assert_uncollided(s31.chart_paint)
    _assert_crown_owned(s28.chart_paint)
    _assert_crown_owned(s31.chart_paint)


def test_q4_s28_s31_strict_render_paints_uncollided_labels(tmp_path: Path) -> None:
    out = tmp_path / "out"
    result = render_deck(HANDOFF, out, strict=True)
    assert result["ok"] is True
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["status"] == "clean"
    html = (out / "presentation.html").read_text(encoding="utf-8")
    s28 = unescape(_section(html, 28)).replace("<wbr>", "")
    s31 = unescape(_section(html, 31)).replace("<wbr>", "")
    assert 'data-chart-type="stacked_bar"' in s28
    assert 'data-chart-type="stacked_bar"' in s31
    segs28 = re.findall(r'data-kind="segment">([^<]*)</text>', s28)
    tots28 = re.findall(r'data-kind="stack_total">([^<]*)</text>', s28)
    for token in S28_SEGS:
        assert token in segs28
    for token in S28_TOTS:
        assert token in tots28
    segs31 = re.findall(r'data-kind="segment">([^<]*)</text>', s31)
    tots31 = re.findall(r'data-kind="stack_total">([^<]*)</text>', s31)
    for token in S31_SEGS:
        assert token in segs31
    for token in ("1%", "2%", "4%"):
        assert token in segs31
    for token in S31_TOTS:
        assert token in tots31


def test_mutation_hiding_s28_segments_omits_visual_labels(tmp_path: Path) -> None:
    raw = _load()
    _slide(raw, 28)["payload"]["chart"]["display"]["stack_segments"] = "hide"
    src = tmp_path / "h.json"
    src.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    s28 = _section(html, 28)
    segs = re.findall(r'data-kind="segment">([^<]*)</text>', s28)
    assert "$0.7" not in segs and "$8.5" not in segs
    tots = re.findall(r'data-kind="stack_total">([^<]*)</text>', s28)
    assert "$11.5" in tots
