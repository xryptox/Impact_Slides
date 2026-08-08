"""#159 grouped annex tables preserve independent peer table blocks."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from amex_handoff_mutations import apply_issue_159_grouped_annex  # noqa: E402
from impact_slides.renderer_v2 import render_deck
from impact_slides.renderer_v2.charts.typography import (
    begin_render_warnings,
    reset_render_strict,
    set_render_strict,
    take_render_warnings,
)
from impact_slides.renderer_v2.layout.dispatch import render_slide
from impact_slides.renderer_v2.schemas import validate_slide

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "renderer_v2"
FIXTURE = FIXTURES / "amex_slide32_grouped_annex.json"
_LAYOUT = "grouped" + "_annex_table"


def _slide() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _groups(slide: dict) -> list[dict]:
    return slide["visual_spec"]["primary_visual"]["groups"]


def _render(slide: dict) -> str:
    model, err = validate_slide(slide)
    assert model is not None, err
    return render_slide(slide, total=32, notes="")


def test_schema_and_renderer_support_one_group() -> None:
    slide = _slide()
    slide["visual_spec"]["primary_visual"]["groups"] = _groups(slide)[:1]
    html = _render(slide)
    assert html.count('class="gl-grouped-annex-block"') == 1
    assert "Commercial Services" in html
    assert "International Card Services" not in html


def test_two_groups_keep_unequal_rows_headers_and_hierarchy() -> None:
    slide = _slide()
    _groups(slide)[0]["rows"] = _groups(slide)[0]["rows"][:-1]
    html = _render(slide)
    assert html.count('class="gl-grouped-annex-block"') == 2
    assert html.count("Q1'26 Reported") == 2
    assert html.count("FX-Adj.*") == 2
    assert 'class="gl-annex-row gl-annex-row-aggregate"' in html
    assert 'class="gl-annex-row gl-annex-row-child"' in html
    assert 'class="gl-annex-stub gl-annex-indent-1"' in html
    assert "Commercial Services</h3>" in html
    assert "International Card Services</h3>" in html


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda s: _groups(s)[0].pop("heading"), id="drop-heading"),
        pytest.param(lambda s: _groups(s)[0].update(heading="   "), id="blank-heading"),
        pytest.param(
            lambda s: _groups(s)[0].update(headers=["Segment", " ", "FX-Adj.*"]),
            id="blank-header",
        ),
        pytest.param(lambda s: _groups(s)[1].update(rows=[]), id="empty-group"),
    ],
)
def test_group_schema_rejects_malformed_groups(mutate) -> None:
    slide = _slide()
    mutate(slide)
    model, err = validate_slide(slide)
    assert model is None
    assert "group" in (err or "").lower()


def test_group_schema_accepts_a_long_heading() -> None:
    slide = _slide()
    _groups(slide)[0]["heading"] = (
        "A very long commercial-services heading that should wrap instead of escaping its block"
    )
    assert "very long commercial-services heading" in _render(slide)


def test_default_annex_table_remains_the_same_surface() -> None:
    slide = {
        "slide_number": 1,
        "layout_type": "annex_table",
        "title": "Legacy annex",
        "content": {},
        "visual_spec": {
            "primary_visual": {
                "type": "annex_table",
                "steps_or_data": [["Metric", "Q1"], ["Revenue", "$1"]],
            }
        },
    }
    html = render_slide(slide, total=1, notes="")
    assert 'data-layout="annex_table"' in html
    assert "gl-grouped-annex" not in html
    assert "Revenue" in html and "$1" in html


def test_strict_narrow_host_fails_and_nonstrict_stacks_with_warning(monkeypatch) -> None:
    import impact_slides.renderer_v2.layout.recipes.metrics as metrics

    monkeypatch.setattr(metrics, "GROUPED_ANNEX_HOST_WIDTH", 800)
    with pytest.raises(ValueError, match="grouped annex"):
        _render(_slide())

    strict_token = set_render_strict(False)
    warnings_token = begin_render_warnings()
    try:
        html = _render(_slide())
    finally:
        warnings = take_render_warnings(warnings_token)
        reset_render_strict(strict_token)
    assert "gl-grouped-annex-1col" in html
    assert any("grouped annex" in warning for warning in warnings)


def test_amex_mutation_restores_source_groups_and_is_idempotent() -> None:
    expected = _groups(_slide())
    handoff = {"slides": [{"slide_number": 32, "layout_type": "annex_table"}]}
    apply_issue_159_grouped_annex(handoff)
    assert _groups(handoff["slides"][0]) == expected
    once = json.dumps(handoff, sort_keys=True)
    apply_issue_159_grouped_annex(handoff)
    assert json.dumps(handoff, sort_keys=True) == once


@pytest.mark.parametrize("mutate", ["drop-heading", "merge", "move-row"])
def test_adversarial_source_mutations_are_repaired(mutate: str) -> None:
    """Issue-shaped source defects must lose against the slide-32 contract."""
    expected = _groups(_slide())
    damaged = _slide()
    if mutate == "drop-heading":
        _groups(damaged)[0].pop("heading")
    elif mutate == "merge":
        _groups(damaged)[:] = [{
            "heading": "Commercial Services / International Card Services",
            "headers": _groups(damaged)[0]["headers"],
            "rows": _groups(damaged)[0]["rows"] + _groups(damaged)[1]["rows"],
        }]
    else:
        _groups(damaged)[0]["rows"].append(_groups(damaged)[1]["rows"].pop(0))
    handoff = {"slides": [damaged]}
    apply_issue_159_grouped_annex(handoff)
    assert _groups(handoff["slides"][0]) == expected


def test_fx_adjusted_footnote_is_rendered() -> None:
    assert "See Slide 3 for an explanation of FX-adjusted information." in _render(_slide())


def test_browser_keeps_peer_blocks_distinct_and_nonoverlapping(tmp_path: Path) -> None:
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    handoff = {
        "presentation": {"title": "Annex"},
        "slides": [
            {
                "slide_number": 1,
                "layout_type": "title_or_opening",
                "title": "Annex",
                "content": {"bullets": []},
            },
            _slide(),
        ],
    }
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(path, out, strict=False)

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto((out / "presentation.html").resolve().as_uri(), wait_until="networkidle")
        page.keyboard.press("ArrowRight")
        measured = page.evaluate(
            """() => {
              const root = document.querySelector('.slide.active');
              const blocks = [...root.querySelectorAll('.gl-grouped-annex-block')];
              const box = el => { const r = el.getBoundingClientRect(); return {l:r.left,r:r.right,t:r.top,b:r.bottom,w:r.width,h:r.height}; };
              return { stage: box(root), blocks: blocks.map(block => ({
                box: box(block),
                heading: block.querySelector('.gl-grouped-annex-heading')?.textContent.trim(),
                labelledBy: block.querySelector('table')?.getAttribute('aria-labelledby'),
                headers: [...block.querySelectorAll('th[scope="col"]')].map(h => h.textContent.trim()),
                childIndent: parseFloat(getComputedStyle(block.querySelector('.gl-annex-indent-1')).paddingLeft),
                aggregateWeight: getComputedStyle(block.querySelector('.gl-annex-row-aggregate .gl-annex-stub')).fontWeight,
                numericAlign: getComputedStyle(block.querySelector('.gl-annex-cell.num')).textAlign,
                rows: [...block.querySelectorAll('tbody tr')].map(row => [...row.cells].map(cell => cell.textContent.trim())),
              })) };
            }"""
        )
        browser.close()

    assert [block["heading"] for block in measured["blocks"]] == [
        "Commercial Services", "International Card Services"
    ]
    left, right = measured["blocks"]
    assert left["box"]["r"] <= right["box"]["l"] + 1
    assert min(left["box"]["w"], right["box"]["w"]) >= 400
    assert all(block["box"]["t"] >= measured["stage"]["t"] - 1 for block in measured["blocks"])
    assert all(block["box"]["b"] <= measured["stage"]["b"] + 1 for block in measured["blocks"])
    assert all(block["labelledBy"] for block in measured["blocks"])
    assert all(block["headers"] == ["Segment", "Q1'26 Reported", "FX-Adj.*"] for block in measured["blocks"])
    assert all(block["childIndent"] >= 16 for block in measured["blocks"])
    assert all(int(block["aggregateWeight"]) >= 700 for block in measured["blocks"])
    assert all(block["numericAlign"] in ("right", "end") for block in measured["blocks"])
    assert [block["rows"] for block in measured["blocks"]] == [
        [row["cells"] for row in group["rows"]] for group in _groups(_slide())
    ]
