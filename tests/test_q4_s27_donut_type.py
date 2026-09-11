"""#339/#340 — Q4 2021 s27 dual donuts pin ordinary_values 24 on a smaller ring.

Seams under test:
- live Q4 handoff payload (`simulation/amex_q4_2021/handoff_v1.json`)
- authored ChartTypography.ordinary_values on both donuts
- freeze_pie_donut pad-from-name so names fit at 24 without slice_label_overflow
- strict `render_deck` SVG overlay for slide 27
"""
from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

from impact_slides.renderer_v3 import render_deck, validate_handoff
from impact_slides.renderer_v3.charts import PAD_R
from impact_slides.renderer_v3.plan import plan_deck

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "simulation" / "amex_q4_2021" / "handoff_v1.json"

S27_MIX = {
    "s27-loans": (("us", "68"), ("intl", "12"), ("sb", "20")),
    "s27-rec": (("us", "28"), ("intl", "14"), ("corp", "24"), ("sb", "34")),
}
S27_NAMES = (
    "U.S. Consumer",
    "Intl. Consumer",
    "Small Business",
    "Corporate Card",
)
S27_PCTS = ("68%", "12%", "20%", "28%", "14%", "24%", "34%")


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


def test_q4_s27_payload_pins_ordinary_values_24() -> None:
    slide = _slide(_load(), 27)
    assert slide["layout_type"] == "dual_chart"
    panes = slide["payload"]["charts"]
    assert len(panes) == 2
    for pane, (sid, mix) in zip(panes, S27_MIX.items()):
        chart = pane["chart"]
        assert chart["surface_id"] == sid
        assert chart["chart_type"] == "donut"
        assert chart["typography"]["ordinary_values"] == 24
        slices = {s["slice_id"]: s for s in chart["slices"]}
        for slice_id, value in mix:
            assert slices[slice_id]["value"]["value"] == value


def test_q4_s27_plan_freezes_24_without_overflow() -> None:
    plan = plan_deck(validate_handoff(_load(), strict=True).deck, strict=True)
    by = plan.by_surface_id()
    for sid, mix in S27_MIX.items():
        sp = by[sid]
        cp = sp.chart_paint
        assert cp["role_sizes"]["ordinary_values"] == 24
        assert not cp.get("slice_label_overflow")
        g = cp["geometry"]
        assert g["pad_l"] == g["pad_r"]
        assert g["pad_l"] > PAD_R
        by_id = {s["slice_id"]: s for s in cp["slices"]}
        for slice_id, value in mix:
            sl = by_id[slice_id]
            dist = ((sl["name_x"] - g["cx"]) ** 2 + (sl["name_y"] - g["cy"]) ** 2) ** 0.5
            assert dist > g["radius"] + 1
            frac = int(value) / 100
            if frac < 0.20:
                assert sl["value_inside"] is False
            else:
                assert sl["value_inside"] is True


def test_q4_s27_strict_render_paints_24px(tmp_path: Path) -> None:
    out = tmp_path / "out"
    result = render_deck(HANDOFF, out, strict=True)
    assert result["ok"] is True
    html = unescape((out / "presentation.html").read_text(encoding="utf-8"))
    s27 = _section(html, 27)
    assert 'data-layout="dual_chart"' in s27
    assert s27.count('data-chart-type="donut"') == 2
    names = re.findall(r'<text class="slice-name"[^>]*>', s27)
    values = re.findall(r'<text class="slice-value"[^>]*>', s27)
    assert len(names) == 14  # overlay + noscript, 7 slices
    assert len(values) == 14
    for tag in names + values:
        assert 'font-size="24"' in tag
        assert 'font-size="18"' not in tag
    for token in S27_NAMES:
        assert token in s27
    for token in S27_PCTS:
        assert token in s27


def test_mutation_dropping_s27_typography_returns_floor(tmp_path: Path) -> None:
    raw = _load()
    for pane in _slide(raw, 27)["payload"]["charts"]:
        pane["chart"].pop("typography", None)
    src = tmp_path / "h.json"
    src.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(src, out, strict=True)
    html = unescape((out / "presentation.html").read_text(encoding="utf-8"))
    s27 = _section(html, 27)
    names = re.findall(r'<text class="slice-name"[^>]*>', s27)
    values = re.findall(r'<text class="slice-value"[^>]*>', s27)
    assert names and values
    for tag in names + values:
        assert 'font-size="18"' in tag
        assert 'font-size="24"' not in tag
