"""Handoff contract for Amex slide 28 pane titles (#158).

Pins the bounded handoff mutation (not a global top_total deletion):
- Funding Mix / Deposit Programs remain the only pane headings
- each pane has subtitle `$ in billions`
- remove redundant tile top_total pseudo-titles
- keep stack_total_labels + #138 side_callout / exterior names
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from amex_handoff_mutations import (  # noqa: E402
    apply_all,
    apply_issue_158_slide28_pane_titles,
)
from impact_slides.renderer_v2 import render_deck  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "renderer_v2"
BROKEN = FIXTURES / "amex_s28_v10_broken.json"
CORRECTED = FIXTURES / "amex_s28_corrected.json"

_MULTI = "multi" + "_panel"
_STACKED = "stacked_bar" + "_chart"
_SUB = "$ in billions"
_PSEUDO_FUNDING = "$210B · $219B"
_PSEUDO_DEPOSIT = "$151B · $157B"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _by_number(handoff: dict, n: int) -> dict:
    for s in handoff["slides"]:
        if int(s["slide_number"]) == n:
            return s
    raise AssertionError(f"missing slide_number={n}")


def _tiles(slide: dict) -> list[dict]:
    return list(slide["visual_spec"]["primary_visual"]["tiles"])


def test_broken_fixture_still_documents_v10_defect():
    broken = _load(BROKEN)
    s28 = _by_number(broken, 28)
    assert s28["layout_type"] == _MULTI
    tiles = _tiles(s28)
    assert tiles[0]["label"] == "Funding Mix"
    assert tiles[0]["top_total"] == _PSEUDO_FUNDING
    assert tiles[1]["label"] == "Deposit Programs"
    assert tiles[1]["top_total"] == _PSEUDO_DEPOSIT
    assert "subtitle" not in tiles[0] or not tiles[0].get("subtitle")
    assert tiles[0]["chart_config"]["stack_total_labels"] == ["$210", "$219"]
    assert tiles[1]["chart_config"]["stack_total_labels"] == ["$151", "$157"]
    assert tiles[1]["chart_config"]["side_callout"]["value"] == "92% FDIC"


def test_mutation_matches_corrected_fixture():
    broken = _load(BROKEN)
    expected = _load(CORRECTED)
    got = apply_issue_158_slide28_pane_titles(copy.deepcopy(broken))
    assert _by_number(got, 28) == _by_number(expected, 28)


def test_mutation_idempotent():
    broken = _load(BROKEN)
    once = apply_issue_158_slide28_pane_titles(copy.deepcopy(broken))
    twice = apply_issue_158_slide28_pane_titles(copy.deepcopy(once))
    assert _by_number(once, 28) == _by_number(twice, 28)


def test_mutation_semantics():
    s28 = _by_number(
        apply_issue_158_slide28_pane_titles(copy.deepcopy(_load(BROKEN))), 28
    )
    tiles = _tiles(s28)
    assert len(tiles) == 2
    for t, name, totals in (
        (tiles[0], "Funding Mix", ["$210", "$219"]),
        (tiles[1], "Deposit Programs", ["$151", "$157"]),
    ):
        assert t["label"] == name
        assert t.get("heading") in (None, "", name) or t["label"] == name
        assert t["subtitle"] == _SUB
        assert "top_total" not in t
        assert t["chart_config"]["stack_total_labels"] == totals
        assert t["chart_type"] == _STACKED
    assert tiles[1]["chart_config"]["side_callout"]["value"] == "92% FDIC"
    assert tiles[1]["chart_config"]["exterior_segment_names"] is True
    assert tiles[0]["chart_config"]["exterior_segment_names"] is True
    # Slide-level subtitle may remain; pane subtitle is authoritative.
    assert s28["content"].get("subtitle") == _SUB


def test_apply_all_includes_158():
    broken = _load(BROKEN)
    # Minimal handoff with only s28 still gets 158 mutation via apply_all.
    out = apply_all(copy.deepcopy(broken))
    t0 = _tiles(_by_number(out, 28))[0]
    assert "top_total" not in t0
    assert t0["subtitle"] == _SUB


def test_render_corrected_identity_and_no_duplicate_totals(tmp_path):
    handoff = _load(CORRECTED)
    # Prepend a cover so normalize keeps multi_panel as a body slide.
    cover = {
        "slide_number": 1,
        "layout_type": "title_or_opening",
        "title": "Cover",
        "content": {"headline": "Cover"},
    }
    slides = [cover] + list(handoff["slides"])
    for i, s in enumerate(slides, 1):
        s["slide_number"] = i
    handoff = {**handoff, "slides": slides}
    path = tmp_path / "handoff.json"
    path.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(path, out, strict=False)
    html = (out / "presentation.html").read_text(encoding="utf-8")

    m = re.search(
        r'<section\b[^>]*\bdata-layout="' + re.escape(_MULTI) + r'"[^>]*>',
        html,
    )
    assert m, "multi_panel section missing"
    assert "data-slide-number=" in m.group(0)

    assert ">Funding Mix</div>" in html
    assert ">Deposit Programs</div>" in html
    assert html.count("gl-chart-pane-subtitle") == 2
    assert html.count(_SUB) >= 2
    assert _PSEUDO_FUNDING not in html
    assert _PSEUDO_DEPOSIT not in html
    assert 'class="gl-tile-top-total"' not in html
    assert '"$210"' in html and '"$219"' in html
    assert '"$151"' in html and '"$157"' in html
    assert "92% FDIC" in html
    assert "insured at" in html


def test_mutation_trap_reintroducing_top_total_fails():
    """Adversarial: corrected fixture must not carry pseudo-title top_total."""
    s28 = _by_number(_load(CORRECTED), 28)
    for t in _tiles(s28):
        assert "top_total" not in t
        assert t.get("subtitle") == _SUB
