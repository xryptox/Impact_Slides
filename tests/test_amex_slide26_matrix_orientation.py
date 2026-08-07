"""#153 Amex slide 26: Q1'26 period context + source matrix orientation.

Type (A) handoff correction only — no renderer production change.
Identity-safe: target slide via data-slide-number + data-layout, then assert
semantic table cells (not whole-HTML substring presence).
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path

import pytest

from impact_slides.renderer_v2 import render_deck

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "renderer_v2"
CORRECT_SLIDE = FIXTURES / "amex_slide26_te_billed_business.json"

SLIDE_NUM = "26"
LAYOUT = "data_table"

# PDF physical page 26 matrix (period-bearing header + category columns).
HEADER = ["Q1'26", "Restaurants", "Lodging", "Airlines", "Other", "Total T&E"]
ROWS = [
    ["YoY Growth", "9%", "6%", "8%", "13%", "9%"],
    ["% of Total Billed Business", "7%", "5%", "7%", "9%", "29%"],
]

# v10 handoff transposed the matrix and dropped Q1'26.
TRANSPOSED_V10 = [
    ["Category", "YoY Growth", "% of Total Billed Business"],
    ["Restaurants", "9%", "7%"],
    ["Lodging", "6%", "5%"],
    ["Airlines", "8%", "7%"],
    ["Other", "13%", "9%"],
    ["Total T&E", "9%", "29%"],
]


class _TableParser(HTMLParser):
    """Collect header/body cell text from the first data-table in scope."""

    def __init__(self) -> None:
        super().__init__()
        self._in_table = False
        self._in_cell = False
        self._cell_tag = ""
        self._buf: list[str] = []
        self.header: list[str] = []
        self.body: list[list[str]] = []
        self._row: list[str] = []
        self._in_thead = False
        self._in_tbody = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        cls = dict(attrs).get("class") or ""
        if tag == "table" and "data-table" in cls.split() and not self.header and not self.body:
            self._in_table = True
        if not self._in_table:
            return
        if tag == "thead":
            self._in_thead = True
        elif tag == "tbody":
            self._in_tbody = True
        elif tag == "tr":
            self._row = []
        elif tag in ("th", "td"):
            self._in_cell = True
            self._cell_tag = tag
            self._buf = []

    def handle_endtag(self, tag: str) -> None:
        if not self._in_table:
            return
        if tag in ("th", "td") and self._in_cell:
            text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            text = (
                text.replace("&amp;", "&")
                .replace("&#x27;", "'")
                .replace("&#39;", "'")
                .replace("&apos;", "'")
            )
            self._row.append(text)
            self._in_cell = False
        elif tag == "tr":
            if self._in_thead or (not self._in_tbody and self._row and self._cell_tag == "th"):
                if self._row:
                    self.header = self._row
            elif self._in_tbody or self._row:
                if self._row:
                    self.body.append(self._row)
            self._row = []
        elif tag == "thead":
            self._in_thead = False
        elif tag == "tbody":
            self._in_tbody = False
        elif tag == "table" and self._in_table:
            self._in_table = False

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._buf.append(data)


def _section_html(html: str, slide_number: str, layout: str) -> str:
    """Identity-safe extract: data-slide-number + data-layout."""
    pat = re.compile(
        rf'<section\b(?=[^>]*\bdata-slide-number="{re.escape(slide_number)}")'
        rf'(?=[^>]*\bdata-layout="{re.escape(layout)}")[^>]*>[\s\S]*?</section>',
        re.I,
    )
    m = pat.search(html)
    assert m is not None, (
        f"no slide section with data-slide-number={slide_number!r} "
        f"data-layout={layout!r}"
    )
    return m.group(0)


def _parse_table(section: str) -> tuple[list[str], list[list[str]]]:
    p = _TableParser()
    p.feed(section)
    assert p.header, "expected a data-table header row in the identity-matched section"
    return p.header, p.body


def _pad_to_slide_26(slide: dict) -> dict:
    """Cover + pads so normalize_handoff keeps the table at slide_number 26."""
    slides: list[dict] = [
        {
            "slide_number": 1,
            "layout_type": "title_or_opening",
            "packing_mode": "cover-led",
            "title": "Amex Q1'26 IR",
            "content": {"headline": "Fixture cover", "subtitle": "#153"},
            "speaker_notes": "cover",
        }
    ]
    for n in range(2, 26):
        slides.append(
            {
                "slide_number": n,
                "layout_type": "section_divider",
                "title": f"Pad {n:02d}",
                "content": {},
                "speaker_notes": "pad",
            }
        )
    target = deepcopy(slide)
    target["slide_number"] = 26
    slides.append(target)
    return {
        "presentation": {"title": "Amex Q1'26 — slide 26 T&E Billed Business (#153)"},
        "slides": slides,
    }


def _render(tmp_path: Path, handoff: dict) -> str:
    hp = tmp_path / "handoff.json"
    hp.write_text(json.dumps(handoff), encoding="utf-8")
    out = tmp_path / "out"
    render_deck(hp, out, strict=False)
    return (out / "presentation.html").read_text(encoding="utf-8")


def _assert_source_matrix(header: list[str], body: list[list[str]]) -> None:
    assert header == HEADER, f"header orientation/period mismatch: {header!r}"
    assert body == ROWS, f"body matrix mismatch: {body!r}"
    assert header[0] == "Q1'26"
    assert header[1:] == ["Restaurants", "Lodging", "Airlines", "Other", "Total T&E"]
    assert body[0][0] == "YoY Growth"
    assert body[0][1:] == ["9%", "6%", "8%", "13%", "9%"]
    assert body[1][0] == "% of Total Billed Business"
    assert body[1][1:] == ["7%", "5%", "7%", "9%", "29%"]


def test_corrected_handoff_preserves_period_and_matrix(tmp_path: Path) -> None:
    slide = json.loads(CORRECT_SLIDE.read_text(encoding="utf-8"))
    html = _render(tmp_path, _pad_to_slide_26(slide))
    section = _section_html(html, SLIDE_NUM, LAYOUT)
    header, body = _parse_table(section)
    _assert_source_matrix(header, body)

    assert "FX-adjusted" in section
    assert "See Slide 3" in section
    assert "Subtotals may not sum due to rounding" in section


def test_transposed_v10_matrix_fails_period_and_orientation(tmp_path: Path) -> None:
    """Regression guard: the v10 transposed matrix must not satisfy the contract."""
    slide = json.loads(CORRECT_SLIDE.read_text(encoding="utf-8"))
    slide["visual_spec"]["primary_visual"]["steps_or_data"] = TRANSPOSED_V10
    html = _render(tmp_path, _pad_to_slide_26(slide))
    section = _section_html(html, SLIDE_NUM, LAYOUT)
    header, body = _parse_table(section)

    with pytest.raises(AssertionError):
        _assert_source_matrix(header, body)

    assert "Q1'26" not in header
    assert header[0] == "Category"
    assert body[0][0] == "Restaurants"
