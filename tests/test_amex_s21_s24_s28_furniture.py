"""#230/#260 — restore s21 shares line + ROE, s24 braces + $486B, s28 FDIC.

Pins the live D314 corpus (not renderer defaults):
- s21 stacked combo: Common Shares Outstanding 702→682 + ROE 35/34/36/36/34/35
  plus display.stack_segments == show
- s24 six growth bars, group braces, $486B callout, %-of-total boxes
- s28 FDIC callout + on-stack % and $ totals (already stack_segments show)
- renderer does not invent the furniture
- strict render of the canonical corpus stays clean
"""

from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

from impact_slides.renderer_v3 import render_deck, validate_handoff
from impact_slides.renderer_v3.charts import _chartjs_combo_config
from impact_slides.renderer_v3.plan import plan_deck

FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "renderer_v3"
    / "canonical_amex_handoff_v1.json"
)

S21_CATS = ["q4-24", "q1-25", "q2-25", "q3-25", "q4-25", "q1-26"]
S21_DIV = ["0.5", "0.6", "0.6", "0.6", "0.6", "0.7"]
S21_REPO = ["1.1", "0.7", "1.4", "2.3", "0.9", "1.6"]
S21_SHARES = ["702", "701", "696", "689", "686", "682"]
S21_ROE = ["35", "34", "36", "36", "34", "35"]
S21_TOTALS = ["1.6", "1.3", "2.0", "2.9", "1.5", "2.3"]
S21_ROE_PAINT = ["35%", "34%", "36%"]

S24_CATS = [
    "u-s-consumer-services",
    "u-s-sme",
    "u-s-large-global-corp",
    "int-l-consumer",
    "int-l-sme-large-corp",
    "processed-volumes",
]
S24_GROWTH = ["10", "4", "4", "13", "12", "9"]
S24_SHARE = ["37", "22", "5", "15", "8", "12"]
S24_GROUPS = [
    ("us-consumer-services", "U.S. Consumer Services", ["u-s-consumer-services"]),
    ("commercial-services", "Commercial Services", ["u-s-sme", "u-s-large-global-corp"]),
    (
        "international-card-services",
        "International Card Services",
        ["int-l-consumer", "int-l-sme-large-corp"],
    ),
]
S24_CALLOUT = "$486B Total Network Volumes"
S24_AGGREGATES = ("Commercial Services (total)", "International Card Services")

S28_FUND_TOTALS = ["210", "219"]
S28_DEP_TOTALS = ["151", "157"]
S28_FDIC = "92% FDIC"
S28_SEGMENTS = ["72%", "21%", "7%", "81%", "82%", "10%", "6%", "2%"]


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


def test_corpus_payloads_carry_s21_s24_s28_furniture() -> None:
    handoff = _load()

    s21 = _slide(handoff, 21)
    chart = s21["payload"]["chart"]
    assert chart["chart_type"] == "combo"
    assert chart["bar_mode"] == "stacked"
    cats = [c["category_id"] for c in chart["chart_data"]["categories"]]
    assert cats == S21_CATS
    bars = [s for s in chart["chart_data"]["series"] if s["mark_type"] == "bar"]
    lines = [s for s in chart["chart_data"]["series"] if s["mark_type"] == "line"]
    assert len(bars) == 2
    assert len(lines) == 1
    assert bars[0]["values"] == S21_DIV
    assert bars[1]["values"] == S21_REPO
    assert lines[0]["name"] == "Common Shares Outstanding"
    assert lines[0]["values"] == S21_SHARES
    assert lines[0]["axis_key"] == "secondary"
    assert chart["value_axes"]["secondary"]["format_id"] == "num_0"
    aux = chart["auxiliary_series"][0]
    assert aux["role"] == "authored_stack_total"
    assert aux["values"] == S21_TOTALS
    assert chart["display"]["series_identity"] == "legend"
    assert chart["display"]["stack_segments"] == "show"
    roe = s21["payload"]["support"]
    assert roe["support_type"] == "outlined_support"
    assert roe["table"]["stub_header"]["label"] == "ROE"
    row = roe["table"]["rows"][0]
    assert row["label"] == "ROE"
    cols = [c["column_id"] for c in roe["table"]["columns"]]
    assert cols == S21_CATS
    assert [row["cells"][cid]["value"] for cid in cols] == S21_ROE

    s24 = _slide(handoff, 24)
    g = s24["payload"]["chart"]
    assert g["chart_type"] == "grouped_bar"
    assert [c["category_id"] for c in g["chart_data"]["categories"]] == S24_CATS
    assert g["chart_data"]["series"][0]["values"] == S24_GROWTH
    labels = [c["label"] for c in g["chart_data"]["categories"]]
    for agg in S24_AGGREGATES:
        assert agg not in labels
    groups = g["category_groups"]
    assert [(x["group_id"], x["label"], x["category_ids"]) for x in groups] == list(
        S24_GROUPS
    )
    anns = g["annotations"]
    assert any(a["text"] == S24_CALLOUT for a in anns)
    boxed = [a for a in g["auxiliary_series"] if a["role"] == "boxed_label"]
    assert len(boxed) == 1
    assert boxed[0]["values"] == S24_SHARE
    assert boxed[0]["format_id"] == "pct_0"

    s28 = _slide(handoff, 28)
    fund, dep = s28["payload"]["charts"]
    assert fund["value_axes"]["primary"]["format_id"] == "pct_0"
    assert dep["value_axes"]["primary"]["format_id"] == "pct_0"
    assert fund["display"]["stack_segments"] == "show"
    assert dep["display"]["stack_segments"] == "show"
    assert fund["auxiliary_series"][0]["role"] == "authored_stack_total"
    assert fund["auxiliary_series"][0]["values"] == S28_FUND_TOTALS
    assert fund["auxiliary_series"][0]["format_id"] == "usd_0"
    assert dep["auxiliary_series"][0]["values"] == S28_DEP_TOTALS
    assert any(a["text"].startswith(S28_FDIC) for a in dep["annotations"])
    fund_colors = {s["name"]: s["color"] for s in fund["chart_data"]["series"]}
    dep_colors = {s["name"]: s["color"] for s in dep["chart_data"]["series"]}
    assert fund_colors == {
        "Deposits": "navy",
        "Unsecured Funding**": "primary_blue",
        "Short-term Funding / Card ABS*": "sky_blue",
    }
    assert dep_colors == {
        "Savings and Direct CDs": "navy",
        "Third Party CDs": "primary_blue",
        "Third Party Sweep": "sky_blue",
        "Checking": "neutral",
    }
    assert "success" not in fund_colors.values()
    assert "success" not in dep_colors.values()


def test_corpus_has_no_nonsemantic_green_series() -> None:
    """#248: success green is reserved; default/generic series stay navy/blue/sky/gray."""
    handoff = _load()
    greens = []
    for slide in handoff["slides"]:
        payload = slide.get("payload") or {}
        charts = list(payload.get("charts") or [])
        if "chart" in payload:
            charts.append(payload["chart"])
        for chart in charts:
            data = (chart or {}).get("chart_data") or {}
            for series in data.get("series") or []:
                if series.get("color") == "success":
                    greens.append(
                        (slide["slide_number"], series.get("name"), chart.get("chart_type"))
                    )
    assert greens == []


def test_strict_render_shows_s21_s24_s28_furniture(tmp_path: Path) -> None:
    out = tmp_path / "out"
    render_deck(FIXTURE, out, strict=True)
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["status"] == "clean"
    assert meta["ok"] is True
    assert meta["severity_counts"].get("error", 0) == 0

    html = (out / "presentation.html").read_text(encoding="utf-8")

    s21 = unescape(_section(html, 21)).replace("<wbr>", "")
    assert 'data-chart-type="combo"' in s21
    assert "Common Shares Outstanding" in s21
    assert 'data-outlined-support="s21-roe"' in s21
    for token in S21_ROE_PAINT:
        assert token in s21
    assert "682" in s21
    deck = validate_handoff(_load(), strict=True).deck
    cp = plan_deck(deck, strict=True).by_surface_id()["s21-cap"].chart_paint
    cfg = _chartjs_combo_config(cp)
    line_ds = [d for d in cfg["data"]["datasets"] if d["type"] == "line"]
    assert len(line_ds) == 1
    assert line_ds[0]["data"] == [702.0, 701.0, 696.0, 689.0, 686.0, 682.0]
    assert line_ds[0]["yAxisID"] == "y1"
    segs = re.findall(r'data-placement="segment">([^<]*)</text>', s21)
    assert "$0.5" in segs and "$1.1" in segs
    tots = re.findall(r'data-placement="stack-total">([^<]*)</text>', s21)
    assert tots[:6] == ["$1.6", "$1.3", "$2.0", "$2.9", "$1.5", "$2.3"]

    s24 = unescape(_section(html, 24)).replace("<wbr>", "")
    assert "category-group" in s24
    assert 'data-annotation-id="' in s24
    assert S24_CALLOUT in s24
    for token in ("37%", "22%", "5%", "15%", "8%", "12%"):
        assert token in s24
    assert "Commercial Services (total)" not in s24
    assert "boxed-label" in s24

    s28 = unescape(_section(html, 28)).replace("<wbr>", "")
    assert 'data-annotation-id="' in s28
    assert S28_FDIC in s28
    assert "$210" in s28 and "$219" in s28
    assert "$151" in s28 and "$157" in s28
    for token in S28_SEGMENTS:
        assert token in s28
    from impact_slides.renderer_v3.theme import resolve_color

    assert resolve_color("sky_blue", role="series_identity").lower() in s28.lower()
    assert resolve_color("success", role="series_identity").lower() not in s28.lower()


def test_mutation_dropping_s21_line_and_roe_omits_furniture(tmp_path: Path) -> None:
    """Renderer does not invent the shares line or varying ROE; corpus must carry them."""
    handoff = _load()
    chart = _slide(handoff, 21)["payload"]["chart"]
    chart["chart_data"]["series"] = [
        {k: v for k, v in s.items() if k not in ("mark_type", "axis_key")}
        for s in chart["chart_data"]["series"]
        if s.get("mark_type", "bar") == "bar"
    ]
    chart["chart_type"] = "stacked_bar"
    chart.pop("bar_mode", None)
    chart["value_axes"].pop("secondary", None)
    row = _slide(handoff, 21)["payload"]["support"]["table"]["rows"][0]
    for cell in row["cells"].values():
        cell["value"] = "35"
    src = tmp_path / "h.json"
    src.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    s21 = unescape(_section((out / "presentation.html").read_text(encoding="utf-8"), 21))
    assert 'data-chart-type="combo"' not in s21
    assert "34%" not in s21
    assert "36%" not in s21


def test_mutation_dropping_s21_stack_segments_omits_segment_labels(
    tmp_path: Path,
) -> None:
    """Renderer does not invent s21 segment dollars; corpus must opt in."""
    handoff = _load()
    _slide(handoff, 21)["payload"]["chart"]["display"].pop("stack_segments", None)
    src = tmp_path / "h.json"
    src.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    s21 = unescape(_section((out / "presentation.html").read_text(encoding="utf-8"), 21))
    assert 'data-placement="segment"' not in s21
    tots = re.findall(r'data-placement="stack-total">([^<]*)</text>', s21)
    assert tots[:6] == ["$1.6", "$1.3", "$2.0", "$2.9", "$1.5", "$2.3"]


def test_mutation_dropping_s24_braces_and_boxes_omits_furniture(tmp_path: Path) -> None:
    """Renderer does not invent braces, $486B, or %-of-total boxes."""
    handoff = _load()
    s24 = _slide(handoff, 24)
    s24["payload"]["chart"].pop("category_groups", None)
    s24["payload"]["chart"].pop("annotations", None)
    s24["payload"]["chart"].pop("auxiliary_series", None)
    src = tmp_path / "h.json"
    src.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    html = unescape(_section((out / "presentation.html").read_text(encoding="utf-8"), 24))
    assert "category-group" not in html
    assert 'data-annotation-id="' not in html
    assert "chart-annotation" not in html
    assert "boxed-label" not in html


def test_mutation_dropping_s28_fdic_and_totals_omits_furniture(tmp_path: Path) -> None:
    """Renderer does not invent the FDIC callout or dollar stack totals."""
    handoff = _load()
    for chart in _slide(handoff, 28)["payload"]["charts"]:
        chart.pop("annotations", None)
        chart.pop("auxiliary_series", None)
        chart["display"].pop("stack_segments", None)
    src = tmp_path / "h.json"
    src.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    html = unescape(_section((out / "presentation.html").read_text(encoding="utf-8"), 28))
    assert 'data-annotation-id="' not in html
    assert "chart-annotation" not in html
    assert "$210" not in html
    assert "$151" not in html
