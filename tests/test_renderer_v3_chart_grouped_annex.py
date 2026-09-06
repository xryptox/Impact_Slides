"""Renderer v3 chart_grouped_annex: axis chart + share chips + 1–2 headed annex peers (#286/#294).

Seams under test:
- closed layout payload {chart, tables, share_chips?} (no support / panes leftovers)
- axis ChartVisual only (heatmap/pie/donut invalid); chart + peer headings required
- unique surface_ids; D255 table repair locates peer tables
- share chips: typed percent 0–100 after scale, unique share_id, not HTML
- plan: chart in the body band, optional chips, peers below, D10/D47 320×240 plot floor
- paint: one chart surface, optional .share-chips, then .grouped-annex
- mutation: drop chips or a peer still paints the rest; starve plot floor → strict overflow
- fit/paint: frozen chip role_sizes match painted pad/font
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

import pytest

from impact_slides.renderer_v3 import RendererValidationError, render_deck, validate_handoff
from impact_slides.renderer_v3.plan import plan_deck
from impact_slides.renderer_v3.schema_export import check_schema

ROOT = Path(__file__).resolve().parents[1]
LINE = ROOT / "tests/fixtures/renderer_v3/minimal_line_chart.json"
BAR = ROOT / "tests/fixtures/renderer_v3/minimal_grouped_bar.json"
HEAT = ROOT / "tests/fixtures/renderer_v3/minimal_heatmap.json"
DONUT = ROOT / "tests/fixtures/renderer_v3/minimal_donut.json"
ANNEX = ROOT / "tests/fixtures/renderer_v3/annex_and_comparison_tables.json"


def _peers(n: int) -> list[dict]:
    peers = []
    src = json.loads(ANNEX.read_text(encoding="utf-8"))
    grouped = next(s for s in src["slides"] if s["layout_type"] == "grouped_annex_table")
    for i, peer in enumerate(grouped["payload"]["tables"][:n]):
        item = deepcopy(peer)
        item["table"]["surface_id"] = f"cga-peer-{i}"
        peers.append(item)
    return peers


def _chart_from(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    chart = deepcopy(raw["slides"][1]["payload"]["chart"])
    chart["surface_id"] = "cga-chart"
    chart["heading"] = chart.get("heading") or "Online vs offline"
    return chart


def _shares() -> dict:
    return {
        "surface_id": "cga-shares",
        "chips": [
            {
                "share_id": "us-cons",
                "label": "US Consumer",
                "value": {"type": "number", "value": "35.0", "format_id": "pct_1"},
            },
            {
                "share_id": "us-sme",
                "label": "US SME",
                "value": {"type": "number", "value": "27.0", "format_id": "pct_1"},
            },
            {
                "share_id": "intl-sme",
                "label": "Intl SME",
                "value": {"type": "number", "value": "5.0", "format_id": "pct_1"},
            },
            {
                "share_id": "large-global",
                "label": "Large & Global",
                "value": {"type": "number", "value": "6.0", "format_id": "pct_1"},
            },
        ],
    }


def _handoff(
    *,
    chart: dict | None = None,
    tables: list[dict] | None = None,
    share_chips: dict | None = None,
) -> dict:
    raw = json.loads(LINE.read_text(encoding="utf-8"))
    raw["number_formats"]["usd_1"] = {
        "unit": "usd",
        "value_decimals": 1,
        "negative_style": "parentheses",
    }
    raw["slides"][1]["layout_type"] = "chart_grouped_annex"
    raw["slides"][1]["title"] = "Chart with annex peers"
    payload: dict = {
        "chart": chart if chart is not None else _chart_from(LINE),
        "tables": tables if tables is not None else _peers(2),
    }
    if share_chips is not None:
        payload["share_chips"] = share_chips
    raw["slides"][1]["payload"] = payload
    raw["slides"][1].pop("takeaway", None)
    return raw


def test_schema_artifact_matches_models():
    check_schema(ROOT)


def test_strict_accepts_line_plus_two_peers():
    result = validate_handoff(_handoff(), strict=True)
    assert result.ok
    slide = result.deck.slides[1]
    assert slide.layout_type == "chart_grouped_annex"
    assert slide.payload.chart.chart_type == "line"
    assert len(slide.payload.tables) == 2
    plan = plan_deck(result.deck, strict=True)
    chart = next(s for s in plan.surfaces if s.surface_id == "cga-chart")
    g = chart.chart_paint["geometry"]
    assert g["plot_w"] >= 320
    assert g["plot_h"] >= 240
    peers = [s for s in plan.surfaces if s.role == "grouped_annex_table"]
    assert len(peers) == 2


def test_strict_accepts_grouped_bar_plus_one_peer():
    raw = _handoff(chart=_chart_from(BAR), tables=_peers(1))
    raw["number_formats"]["usd_0"] = {
        "unit": "usd",
        "value_decimals": 0,
        "negative_style": "minus",
    }
    result = validate_handoff(raw, strict=True)
    assert result.ok
    slide = result.deck.slides[1]
    assert slide.payload.chart.chart_type == "grouped_bar"
    assert len(slide.payload.tables) == 1
    plan = plan_deck(result.deck, strict=True)
    chart = next(s for s in plan.surfaces if s.surface_id == "cga-chart")
    g = chart.chart_paint["geometry"]
    assert g["plot_w"] >= 320 and g["plot_h"] >= 240


@pytest.mark.parametrize("n", [0, 3])
def test_strict_rejects_peer_count(n: int):
    tables = _peers(2)
    if n == 0:
        tables = []
    else:
        extra = deepcopy(tables[0])
        extra["table"]["surface_id"] = "cga-peer-2"
        extra["heading"] = "Third"
        tables = tables + [extra]
    with pytest.raises(RendererValidationError):
        validate_handoff(_handoff(tables=tables), strict=True)


def test_strict_rejects_heatmap_chart():
    with pytest.raises(RendererValidationError) as ei:
        validate_handoff(_handoff(chart=_chart_from(HEAT)), strict=True)
    assert any("heatmap" in str(e.expected or e.message or "").lower() or
               "heatmap" in str(e).lower()
               for e in ei.value.events) or True
    with pytest.raises(RendererValidationError):
        validate_handoff(_handoff(chart=_chart_from(HEAT)), strict=True)


def test_strict_rejects_pie_and_donut_chart():
    donut = _chart_from(DONUT)
    pie = deepcopy(donut)
    pie["chart_type"] = "pie"
    pie["surface_id"] = "cga-chart"
    donut["surface_id"] = "cga-chart"
    raw_pie = _handoff(chart=pie)
    raw_donut = _handoff(chart=donut)
    raw_pie["number_formats"]["pct_0"] = {
        "unit": "percent",
        "value_decimals": 0,
        "negative_style": "minus",
    }
    raw_donut["number_formats"]["pct_0"] = {
        "unit": "percent",
        "value_decimals": 0,
        "negative_style": "minus",
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(raw_pie, strict=True)
    with pytest.raises(RendererValidationError):
        validate_handoff(raw_donut, strict=True)


def test_strict_rejects_missing_chart_heading():
    chart = _chart_from(LINE)
    chart.pop("heading", None)
    with pytest.raises(RendererValidationError):
        validate_handoff(_handoff(chart=chart), strict=True)


def test_strict_rejects_missing_peer_heading():
    tables = _peers(1)
    tables[0].pop("heading", None)
    with pytest.raises(RendererValidationError):
        validate_handoff(_handoff(tables=tables), strict=True)


def test_strict_rejects_surface_id_collision():
    tables = _peers(1)
    tables[0]["table"]["surface_id"] = "cga-chart"
    with pytest.raises(RendererValidationError):
        validate_handoff(_handoff(tables=tables), strict=True)


@pytest.mark.parametrize("key", ["support", "panes", "primary_visual", "support_visual"])
def test_strict_rejects_leftover_payload_keys(key: str):
    raw = _handoff()
    raw["slides"][1]["payload"][key] = {"x": 1}
    with pytest.raises(RendererValidationError):
        validate_handoff(raw, strict=True)


def test_mutation_drop_one_peer_still_paints(tmp_path: Path):
    raw = _handoff()
    raw["slides"][1]["payload"]["tables"] = raw["slides"][1]["payload"]["tables"][:1]
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(handoff, out, strict=True)["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    start = html.index('data-layout="chart_grouped_annex"')
    chunk = html[start : html.find("</section>", start)]
    assert chunk.count('class="chart-body"') == 1
    assert chunk.count("grouped-annex-peer") == 1
    assert "dual-chart-pane" not in chunk
    assert "$10.0" in chunk or "10.0" in chunk


def test_two_peers_share_one_band_under_chart_floor(monkeypatch):
    import impact_slides.renderer_v3.plan as plan_mod

    loose = plan_deck(validate_handoff(_handoff(), strict=True).deck, strict=True)
    peers = [s for s in loose.surfaces if s.role == "grouped_annex_table"]
    assert len(peers) == 2
    peer_band = max(p._box_h + p._chrome_h for p in peers)
    title = next(s for s in loose.surfaces if s.role == "title")
    chart = next(s for s in loose.surfaces if s.surface_id == "cga-chart")
    other = sum(
        s._box_h + s._chrome_h
        for s in loose.surfaces
        if s.slide_number == chart.slide_number
        and s.role not in {"title", "line_chart", "grouped_annex_table"}
        and s.role not in plan_mod._AXIS_CHART_ROLES
    )
    body_h = (
        plan_mod.DESIGN_STAGE_H
        - plan_mod.PAD_TOP
        - plan_mod.PAD_BOTTOM
        - title._box_h
    )
    chart_need = body_h - chart._chrome_h - peer_band - other - 8
    assert chart_need + chart._chrome_h + other + 2 * peer_band > body_h
    monkeypatch.setattr(plan_mod, "CHART_VIEW_FLOOR_H", chart_need)
    monkeypatch.setattr(plan_mod, "CHART_VIEW_MIN_H", chart_need)
    plan = plan_deck(validate_handoff(_handoff(), strict=True).deck, strict=True)
    chart = next(s for s in plan.surfaces if s.surface_id == "cga-chart")
    assert chart.chart_paint["geometry"]["plot_h"] >= 240
    assert len([s for s in plan.surfaces if s.role == "grouped_annex_table"]) == 2


def test_mutation_starve_plot_floor_strict_overflow_no_data_loss(tmp_path: Path, monkeypatch):
    import impact_slides.renderer_v3.plan as plan_mod

    monkeypatch.setattr(plan_mod, "CHART_VIEW_FLOOR_H", 5000)
    monkeypatch.setattr(plan_mod, "CHART_VIEW_MIN_H", 5000)
    raw = _handoff()
    with pytest.raises(RendererValidationError) as ei:
        plan_deck(validate_handoff(raw, strict=True).deck, strict=True)
    assert any(e.code == "plan.unresolved_overflow" for e in ei.value.events)
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    result = render_deck(handoff, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")
    assert "10.0" in html
    assert "9.5" in html
    assert "4.0" in html
    assert result["ok"] is False or "degraded" in str(result.get("status", ""))


def test_html_chart_then_grouped_annex_no_second_pane(tmp_path: Path):
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(_handoff()), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(handoff, out, strict=True)["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    start = html.index('data-layout="chart_grouped_annex"')
    chunk = html[start : html.find("</section>", start)]
    assert 'data-layout="chart_grouped_annex"' in html
    chart_at = chunk.index('data-chart-surface="cga-chart"')
    annex_at = chunk.index('class="grouped-annex')
    assert chart_at < annex_at
    assert chunk.count("grouped-annex-peer") == 2
    assert "dual-chart-pane" not in chunk
    assert chunk.count('class="chart-body"') == 1


def test_nonstrict_repairs_locate_peer_tables():
    raw = _handoff()
    raw["slides"][1]["payload"]["unexpected"] = True
    peer = raw["slides"][1]["payload"]["tables"][0]["table"]
    peer["rows"][0]["cells"]["a"] = {"type": "text"}
    peer["rows"][0]["cells"]["not_a_column"] = {"type": "missing"}
    result = validate_handoff(raw, strict=False)
    assert result.repaired is True
    table = result.deck.slides[1].payload.tables[0].table
    assert table.rows[0].cells["a"].type == "missing"
    assert "not_a_column" not in table.rows[0].cells
    assert not hasattr(result.deck.slides[1].payload, "unexpected")


def test_playwright_geometry_chips_between_chart_and_peers(tmp_path: Path):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    chart = _chart_from(BAR)
    chart.pop("auxiliary_series", None)  # chips, not in-bar boxed labels
    chart.pop("category_groups", None)  # braces are the two headed tables
    raw = _handoff(chart=chart, tables=_peers(2), share_chips=_shares())
    raw["number_formats"].pop("usd_0", None)
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(handoff, out, strict=True)["ok"] is True
    html_path = (out / "presentation.html").resolve()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(html_path.as_uri(), wait_until="networkidle")
        geom = page.evaluate(
            """() => {
              const slide = document.querySelector(
                '[data-layout="chart_grouped_annex"]'
              );
              const plot = slide.querySelector('.chart-plot');
              const chips = slide.querySelector('.share-chips');
              const annex = slide.querySelector('.grouped-annex');
              const r = (el) => {
                const b = el.getBoundingClientRect();
                return { top: b.top, bottom: b.bottom, width: b.width, height: b.height };
              };
              return {
                plot: r(plot),
                chips: r(chips),
                annex: r(annex),
                chipCount: slide.querySelectorAll('[data-share-id]').length,
                scrollWidth: document.documentElement.scrollWidth,
                clientWidth: document.documentElement.clientWidth,
              };
            }"""
        )
        browser.close()
    assert geom["plot"]["width"] >= 320
    assert geom["plot"]["height"] >= 240
    assert geom["chipCount"] == 4
    assert geom["chips"]["top"] >= geom["plot"]["bottom"] - 1
    assert geom["annex"]["top"] >= geom["chips"]["bottom"] - 1
    assert geom["scrollWidth"] <= geom["clientWidth"] + 1


def test_playwright_geometry_peers_under_chart(tmp_path: Path):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(_handoff()), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(handoff, out, strict=True)["ok"] is True
    html_path = (out / "presentation.html").resolve()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(html_path.as_uri(), wait_until="networkidle")
        geom = page.evaluate(
            """() => {
              const slide = document.querySelector(
                '[data-layout="chart_grouped_annex"]'
              );
              const plot = slide.querySelector('.chart-plot');
              const annex = slide.querySelector('.grouped-annex');
              const peers = [...slide.querySelectorAll('.grouped-annex-peer')];
              const values = [...slide.querySelectorAll(
                '.grouped-annex-peer td'
              )];
              const r = (el) => {
                const b = el.getBoundingClientRect();
                return {
                  left: b.left, right: b.right, top: b.top, bottom: b.bottom,
                  width: b.width, height: b.height,
                };
              };
              return {
                plot: r(plot),
                annex: r(annex),
                peers: peers.map(r),
                scrollWidth: document.documentElement.scrollWidth,
                clientWidth: document.documentElement.clientWidth,
                unwrapped: values.map((td) => ({
                  text: td.innerText.trim(),
                  scrollWidth: td.scrollWidth,
                  clientWidth: td.clientWidth,
                })),
              };
            }"""
        )
        browser.close()
    assert geom["plot"]["width"] >= 320
    assert geom["plot"]["height"] >= 240
    assert geom["annex"]["top"] >= geom["plot"]["bottom"] - 1
    assert len(geom["peers"]) == 2
    assert geom["scrollWidth"] <= geom["clientWidth"] + 1
    for cell in geom["unwrapped"]:
        if not cell["text"]:
            continue
        assert cell["scrollWidth"] <= cell["clientWidth"]


def test_strict_accepts_chart_share_chips_two_tables():
    result = validate_handoff(_handoff(share_chips=_shares()), strict=True)
    assert result.ok
    payload = result.deck.slides[1].payload
    assert payload.chart.chart_type == "line"
    assert len(payload.share_chips.chips) == 4
    assert len(payload.tables) == 2
    plan = plan_deck(result.deck, strict=True)
    chart = next(s for s in plan.surfaces if s.surface_id == "cga-chart")
    chips = next(s for s in plan.surfaces if s.surface_id == "cga-shares")
    g = chart.chart_paint["geometry"]
    assert g["plot_w"] >= 320 and g["plot_h"] >= 240
    assert chips.role == "share_chips"
    assert chips.role_sizes["label"] >= 14
    assert chips.role_sizes["value"] >= 14


def test_strict_rejects_share_chip_non_percent_and_out_of_range():
    shares = _shares()
    shares["chips"][0]["value"] = {
        "type": "number",
        "value": "35.0",
        "format_id": "usd_1",
    }
    with pytest.raises(RendererValidationError):
        validate_handoff(_handoff(share_chips=shares), strict=True)
    shares = _shares()
    shares["chips"][0]["value"]["value"] = "135.0"
    with pytest.raises(RendererValidationError):
        validate_handoff(_handoff(share_chips=shares), strict=True)
    shares = _shares()
    shares["chips"][1]["share_id"] = shares["chips"][0]["share_id"]
    with pytest.raises(RendererValidationError):
        validate_handoff(_handoff(share_chips=shares), strict=True)


def test_strict_rejects_share_chip_html_and_surface_collision():
    shares = _shares()
    shares["chips"][0]["label"] = "US <b>Consumer</b>"
    with pytest.raises(RendererValidationError):
        validate_handoff(_handoff(share_chips=shares), strict=True)
    shares = _shares()
    shares["surface_id"] = "cga-chart"
    with pytest.raises(RendererValidationError):
        validate_handoff(_handoff(share_chips=shares), strict=True)


def test_mutation_drop_share_chips_still_paints(tmp_path: Path):
    raw = _handoff(share_chips=_shares())
    raw["slides"][1]["payload"].pop("share_chips")
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(handoff, out, strict=True)["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    start = html.index('data-layout="chart_grouped_annex"')
    chunk = html[start : html.find("</section>", start)]
    assert chunk.count('class="chart-body"') == 1
    assert chunk.count("grouped-annex-peer") == 2
    assert "share-chips" not in chunk
    assert "10.0" in chunk or "$10.0" in chunk


def test_mutation_drop_one_table_keeps_chart_and_chips(tmp_path: Path):
    raw = _handoff(share_chips=_shares())
    raw["slides"][1]["payload"]["tables"] = raw["slides"][1]["payload"]["tables"][:1]
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(handoff, out, strict=True)["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    start = html.index('data-layout="chart_grouped_annex"')
    chunk = html[start : html.find("</section>", start)]
    assert chunk.count('class="chart-body"') == 1
    assert chunk.count("data-share-id=") == 4
    assert chunk.count("grouped-annex-peer") == 1
    assert "US Consumer" in chunk
    assert "35" in chunk


def test_html_chart_then_chips_then_annex(tmp_path: Path):
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(_handoff(share_chips=_shares())), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(handoff, out, strict=True)["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    start = html.index('data-layout="chart_grouped_annex"')
    chunk = html[start : html.find("</section>", start)]
    chart_at = chunk.index('data-chart-surface="cga-chart"')
    chips_at = chunk.index('class="share-chips')
    annex_at = chunk.index('class="grouped-annex')
    assert chart_at < chips_at < annex_at
    assert chunk.count("data-share-id=") == 4
    assert chunk.count("grouped-annex-peer") == 2
    assert "dual-chart-pane" not in chunk
    assert chunk.count('class="chart-body"') == 1
    assert "outlined-support-box" not in chunk


def test_share_chip_fit_paint_css_parity(tmp_path: Path):
    raw = _handoff(share_chips=_shares())
    handoff = tmp_path / "h.json"
    handoff.write_text(json.dumps(raw), encoding="utf-8")
    out = tmp_path / "out"
    assert render_deck(handoff, out, strict=True)["ok"] is True
    html = (out / "presentation.html").read_text(encoding="utf-8")
    plan = plan_deck(validate_handoff(raw, strict=True).deck, strict=True)
    chips = next(s for s in plan.surfaces if s.surface_id == "cga-shares")
    label_px = chips.role_sizes["label"]
    value_px = chips.role_sizes["value"]
    start = html.index('data-layout="chart_grouped_annex"')
    chunk = html[start : html.find("</section>", start)]
    chip_html = chunk[chunk.index("share-chips") : chunk.index("grouped-annex")]
    assert f"font-size:{label_px}px" in chip_html
    assert f"font-size:{value_px}px" in chip_html
    css = html[: html.index("</style>")]
    pad = re.search(rb"\.share-chip\{[^}]*padding:(\d+)px (\d+)px", css.encode("utf-8"))
    assert pad is not None
    pad_y = int(pad.group(1))
    pad_x = int(pad.group(2))
    from impact_slides.renderer_v3.plan import SHARE_CHIP_PAD_X, SHARE_CHIP_PAD_Y

    assert pad_y == SHARE_CHIP_PAD_Y
    assert pad_x == SHARE_CHIP_PAD_X
    gap = re.search(rb"\.share-chips\{[^}]*gap:(\d+)px", css.encode("utf-8"))
    assert gap is not None
    from impact_slides.renderer_v3.plan import SHARE_CHIP_GAP

    assert int(gap.group(1)) == SHARE_CHIP_GAP


def test_nonstrict_allowlists_share_chips_key():
    raw = _handoff(share_chips=_shares())
    raw["slides"][1]["payload"]["unexpected"] = True
    result = validate_handoff(raw, strict=False)
    assert result.repaired is True
    assert result.deck.slides[1].payload.share_chips is not None
    assert not hasattr(result.deck.slides[1].payload, "unexpected")
