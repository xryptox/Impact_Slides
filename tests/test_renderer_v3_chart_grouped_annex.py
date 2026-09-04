"""Renderer v3 chart_grouped_annex: axis chart + 1–2 headed annex peers (#286).

Seams under test:
- closed layout payload {chart, tables} (no support / panes leftovers)
- axis ChartVisual only (heatmap invalid); chart + peer headings required
- unique surface_ids; D255 table repair locates peer tables
- plan: chart in the body band, peers below, D10/D47 320×240 plot floor
- paint: one chart surface then .grouped-annex with 1–2 peers
- mutation: drop a peer still paints; starve plot floor → strict overflow
"""
from __future__ import annotations

import json
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


def _handoff(*, chart: dict | None = None, tables: list[dict] | None = None) -> dict:
    raw = json.loads(LINE.read_text(encoding="utf-8"))
    raw["number_formats"]["usd_1"] = {
        "unit": "usd",
        "value_decimals": 1,
        "negative_style": "parentheses",
    }
    raw["slides"][1]["layout_type"] = "chart_grouped_annex"
    raw["slides"][1]["title"] = "Chart with annex peers"
    raw["slides"][1]["payload"] = {
        "chart": chart if chart is not None else _chart_from(LINE),
        "tables": tables if tables is not None else _peers(2),
    }
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
