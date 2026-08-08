"""#157 — Amex annex slides 33–37: restore all source table data.

Type (A) handoff correctness. PDF-source semantic-cell/cardinality probes
pass on the restored fixture and after apply_issue_157_annex_matrices; the
v10 broken handoff must fail the same probes. No renderer production change.

Identity-safe evidence uses data-slide-number + data-layout only.
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

from amex_handoff_mutations import apply_issue_157_annex_matrices  # noqa: E402
from impact_slides.renderer_v2 import render_deck  # noqa: E402
from impact_slides.renderer_v2.layout.dispatch import render_slide  # noqa: E402
from impact_slides.renderer_v2.schemas import validate_slide  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "renderer_v2"
RESTORED = FIXTURES / "amex_annex_33_37_restored_handoff.json"
BROKEN_V10 = FIXTURES / "amex_annex_33_37_v10_broken_handoff.json"

# Split layout token so gen_layout_index word-boundary search does not
# treat this file as a layout/recipe reference.
_ANNEX = "annex" + "_table"

# PDF-source matrices (Q1-2026-Earnings-Presentation.pdf pages 33–37).
# Empty string = intentionally blank source cell (not a missing period).
SOURCE_MATRICES: dict[int, list[list[str]]] = {
    33: [
        [
            "Metric",
            "Q1'19",
            "Q1'24",
            "Q2'24",
            "Q3'24",
            "Q4'24",
            "Q1'25",
            "Q2'25",
            "Q3'25",
            "Q4'25",
            "Q1'26",
        ],
        [
            "GAAP Total Balances",
            "$142",
            "$194",
            "$199",
            "$202",
            "$208",
            "$207",
            "$212",
            "$216",
            "$225",
            "$224",
        ],
        [
            "FX-Adjusted Total Balances*",
            "$140",
            "$193",
            "$200",
            "$202",
            "$211",
            "$209",
            "",
            "",
            "",
            "",
        ],
        [
            "YoY% Inc/(Dec) in GAAP Total Balances",
            "",
            "",
            "",
            "",
            "",
            "7%",
            "7%",
            "7%",
            "8%",
            "8%",
        ],
        [
            "YoY% Inc/(Dec) in FX-Adjusted Total Balances*",
            "",
            "",
            "",
            "",
            "",
            "7%",
            "6%",
            "7%",
            "7%",
            "7%",
        ],
        [
            "GAAP Total Balances (incl. Card Balances HFS) Q1'19 - Q1'26 CAGR",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "7%",
        ],
        [
            "FX-Adjusted Total Balances (incl. Card Balances HFS) Q1'19 - Q1'26 CAGR*",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "7%",
        ],
    ],
    34: [
        ["Item", "Q1'26", "Q1'25", "YoY% Inc/(Dec)"],
        ["Discount Revenue", "$9,512", "$8,743", "9%"],
        ["FX-Adjusted*", "", "$8,857", "7%"],
        ["Net Card Fees", "$2,752", "$2,333", "18%"],
        ["FX-Adjusted*", "", "$2,374", "16%"],
        ["Service Fees and Other Revenue", "$1,951", "$1,722", "13%"],
        ["FX-Adjusted*", "", "$1,783", "9%"],
        ["Net Interest Income", "$4,692", "$4,169", "13%"],
        ["FX-Adjusted*", "", "$4,196", "12%"],
        ["Revenues Net of Interest Expense", "$18,907", "$16,967", "11%"],
        ["FX-Adjusted*", "", "$17,210", "10%"],
    ],
    35: [
        [
            "Metric",
            "Q1'19",
            "Q1'23",
            "Q2'23",
            "Q3'23",
            "Q4'23",
            "Q1'24",
            "Q2'24",
            "Q3'24",
            "Q4'24",
            "Q1'25",
            "Q2'25",
            "Q3'25",
            "Q4'25",
            "Q1'26",
        ],
        [
            "GAAP Net Card Fees",
            "$0.9",
            "$1.7",
            "$1.8",
            "$1.8",
            "$1.9",
            "$2.0",
            "$2.1",
            "$2.2",
            "$2.2",
            "$2.3",
            "$2.5",
            "$2.6",
            "$2.6",
            "$2.8",
        ],
        [
            "FX-Adjusted Net Card Fees*",
            "$0.9",
            "$1.7",
            "$1.8",
            "$1.8",
            "$1.9",
            "$2.0",
            "$2.1",
            "$2.2",
            "$2.3",
            "$2.4",
            "",
            "",
            "",
            "",
        ],
        [
            "YoY% Inc/(Dec) in GAAP Net Card Fees",
            "",
            "",
            "",
            "",
            "",
            "15%",
            "15%",
            "18%",
            "18%",
            "18%",
            "20%",
            "18%",
            "17%",
            "18%",
        ],
        [
            "YoY% Inc/(Dec) in FX-Adjusted Net Card Fees*",
            "",
            "",
            "",
            "",
            "",
            "16%",
            "16%",
            "18%",
            "19%",
            "20%",
            "20%",
            "17%",
            "16%",
            "16%",
        ],
        [
            "GAAP Net Card Fees Q1'19 - Q1'26 CAGR",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "17%",
        ],
        [
            "FX-Adjusted Net Card Fees Q1'19 - Q1'26 CAGR*",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "17%",
        ],
    ],
    36: [
        [
            "Metric",
            "Q1'19",
            "Q1'24",
            "Q2'24",
            "Q3'24",
            "Q4'24",
            "Q1'25",
            "Q2'25",
            "Q3'25",
            "Q4'25",
            "Q1'26",
        ],
        [
            "GAAP Net Interest Income",
            "$2.1",
            "$3.8",
            "$3.7",
            "$4.0",
            "$4.0",
            "$4.2",
            "$4.2",
            "$4.5",
            "$4.5",
            "$4.7",
        ],
        [
            "FX-Adjusted Net Interest Income*",
            "$2.1",
            "$3.7",
            "$3.7",
            "$4.0",
            "$4.1",
            "$4.2",
            "",
            "",
            "",
            "",
        ],
        [
            "YoY% Inc/(Dec) in GAAP Net Interest Income",
            "",
            "",
            "",
            "",
            "",
            "11%",
            "12%",
            "12%",
            "12%",
            "13%",
        ],
        [
            "YoY% Inc/(Dec) in FX-Adjusted Net Interest Income*",
            "",
            "",
            "",
            "",
            "",
            "11%",
            "12%",
            "12%",
            "12%",
            "12%",
        ],
        [
            "GAAP Net Interest Income Q1'19 - Q1'26 CAGR",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "12%",
        ],
        [
            "FX-Adjusted Net Interest Income Q1'19 - Q1'26 CAGR*",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "13%",
        ],
    ],
    37: [
        [
            "Metric",
            "Q1'24",
            "Q2'24",
            "Q3'24",
            "Q4'24",
            "Q1'25",
            "Q2'25",
            "Q3'25",
            "Q4'25",
            "Q1'26",
        ],
        [
            "GAAP Revenues Net of Interest Expense",
            "$15.8",
            "$16.3",
            "$16.6",
            "$17.2",
            "$17.0",
            "$17.9",
            "$18.4",
            "$19.0",
            "$18.9",
        ],
        [
            "FX-Adjusted Revenues Net of Interest Expense*",
            "$15.7",
            "$16.4",
            "$16.7",
            "$17.3",
            "$17.2",
            "",
            "",
            "",
            "",
        ],
        [
            "YoY% Inc/(Dec) in GAAP Revenues Net of Interest Expense",
            "",
            "",
            "",
            "",
            "7%",
            "9%",
            "11%",
            "10%",
            "11%",
        ],
        [
            "YoY% Inc/(Dec) in FX-Adjusted Revenues Net of Interest Expense*",
            "",
            "",
            "",
            "",
            "8%",
            "9%",
            "11%",
            "9%",
            "10%",
        ],
    ],
}

# Required row-label substrings per slide (semantic presence, not exact string).
REQUIRED_ROW_MARKERS: dict[int, list[str]] = {
    33: [
        "GAAP Total Balances",
        "FX-Adjusted Total Balances",
        "YoY% Inc/(Dec) in GAAP Total Balances",
        "YoY% Inc/(Dec) in FX-Adjusted Total Balances",
        "CAGR",
    ],
    34: [
        "Discount Revenue",
        "Net Card Fees",
        "Service Fees and Other Revenue",
        "Net Interest Income",
        "Revenues Net of Interest Expense",
        "FX-Adjusted*",
    ],
    35: [
        "GAAP Net Card Fees",
        "FX-Adjusted Net Card Fees",
        "YoY% Inc/(Dec) in GAAP Net Card Fees",
        "YoY% Inc/(Dec) in FX-Adjusted Net Card Fees",
        "CAGR",
    ],
    36: [
        "GAAP Net Interest Income",
        "FX-Adjusted Net Interest Income",
        "YoY% Inc/(Dec) in GAAP Net Interest Income",
        "YoY% Inc/(Dec) in FX-Adjusted Net Interest Income",
        "CAGR",
    ],
    37: [
        "GAAP Revenues Net of Interest Expense",
        "FX-Adjusted Revenues Net of Interest Expense",
        "YoY% Inc/(Dec) in GAAP Revenues Net of Interest Expense",
        "YoY% Inc/(Dec) in FX-Adjusted Revenues Net of Interest Expense",
    ],
}

_UNITS = {
    33: "$ in billions",
    34: "$ in millions",
    35: "$ in billions",
    36: "$ in billions",
    37: "$ in billions",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _matrix(slide: dict) -> list[list[str]]:
    vs = slide.get("visual_spec") or {}
    pv = vs.get("primary_visual") or {}
    data = pv.get("steps_or_data") or []
    if not isinstance(data, list) or not data:
        return []
    out: list[list[str]] = []
    for row in data:
        if not isinstance(row, list):
            return []
        out.append(["" if c is None else str(c) for c in row])
    return out


def _by_number(handoff: dict) -> dict[int, dict]:
    return {int(s["slide_number"]): s for s in handoff["slides"]}


def _norm_cell(s: str) -> str:
    return re.sub(
        r"\s+", " ", (s or "").replace("\u2013", "-").replace("\u2014", "-")
    ).strip()


def _row_label(row: list[str]) -> str:
    return _norm_cell(row[0]) if row else ""


def _section_attrs(html: str, slide_number: int) -> dict[str, str]:
    pat = rf'<section\b[^>]*\bdata-slide-number="{slide_number}"[^>]*>'
    m = re.search(pat, html)
    assert m, f"no section data-slide-number={slide_number}"
    tag = m.group(0)
    layout = re.search(r'\bdata-layout="([^"]+)"', tag)
    assert layout, f"missing data-layout on slide {slide_number}: {tag}"
    return {"data-slide-number": str(slide_number), "data-layout": layout.group(1)}


def assert_semantic_matrix(slide_number: int, matrix: list[list[str]]) -> None:
    """PDF-to-handoff semantic-cell + cardinality probe.

    Fails on missing required rows, missing final period, missing FX-adjusted
    values, period-token pseudo-rows, or width/cardinality drift vs source.
    """
    expected = SOURCE_MATRICES[slide_number]
    assert matrix, f"slide {slide_number}: empty matrix"
    exp_head, got_head = expected[0], matrix[0]
    assert got_head == exp_head, (
        f"slide {slide_number}: header mismatch\n  expected={exp_head}\n  got={got_head}"
    )
    assert len(matrix) == len(expected), (
        f"slide {slide_number}: row cardinality {len(matrix)} != {len(expected)}"
    )
    period_tok = re.compile(r"^Q[1-4]'?\d{2}$")
    for r in matrix[1:]:
        lab = _row_label(r)
        assert not period_tok.match(lab), (
            f"slide {slide_number}: period token emitted as pseudo-row {lab!r}"
        )
        assert len(r) == len(got_head), (
            f"slide {slide_number}: ragged row width for {lab!r}: "
            f"{len(r)} != {len(got_head)}"
        )

    labels = [_row_label(r) for r in matrix[1:]]
    blob = " | ".join(labels)
    for marker in REQUIRED_ROW_MARKERS[slide_number]:
        assert marker in blob, (
            f"slide {slide_number}: missing required row marker {marker!r} in {labels}"
        )

    for ri, (erow, grow) in enumerate(zip(expected, matrix)):
        for ci, (e, g) in enumerate(zip(erow, grow)):
            assert _norm_cell(g) == _norm_cell(e), (
                f"slide {slide_number} cell[{ri},{ci}] "
                f"({erow[0]!r} / {exp_head[ci]!r}): expected {e!r}, got {g!r}"
            )

    final_ci = len(got_head) - 1
    final_vals = [r[final_ci] for r in matrix[1:] if r[final_ci]]
    assert final_vals, (
        f"slide {slide_number}: final period {got_head[final_ci]!r} has no values"
    )

    for erow in expected[1:]:
        lab = _row_label(erow)
        if "FX-Adjusted" not in lab:
            continue
        for ci, e in enumerate(erow[1:], start=1):
            if not e:
                continue
            assert any(_norm_cell(r[ci]) == _norm_cell(e) for r in matrix[1:]), (
                f"slide {slide_number}: FX-adjusted value {e!r} missing "
                f"in col {got_head[ci]!r}"
            )


# ---------------------------------------------------------------------------
# Restored fixture + mutation pass; v10 broken fails
# ---------------------------------------------------------------------------


class TestRestoredAnnexMatrices:
    def test_fixture_covers_slides_33_through_37(self):
        h = _load(RESTORED)
        nums = sorted(int(s["slide_number"]) for s in h["slides"])
        assert nums == [33, 34, 35, 36, 37]

    @pytest.mark.parametrize("slide_number", [33, 34, 35, 36, 37])
    def test_semantic_cells_match_pdf_source(self, slide_number: int):
        slide = _by_number(_load(RESTORED))[slide_number]
        assert_semantic_matrix(slide_number, _matrix(slide))

    def test_fx_footnote_and_units_preserved(self):
        h = _load(RESTORED)
        for s in h["slides"]:
            sn = int(s["slide_number"])
            disc = s.get("disclosure") or {}
            panels = disc.get("panels") or []
            bodies = " ".join(str(p.get("body") or "") for p in panels)
            assert "FX-adjusted" in bodies, f"slide {sn}: missing FX footnote"
            content = s.get("content") or {}
            units = content.get("body_text") or ""
            assert units == _UNITS[sn], f"slide {sn}: units {units!r}"
            # annex_table paints subtitle/dek, not body_text — units must live there.
            sub = content.get("subtitle") or ""
            assert _UNITS[sn] in sub, f"slide {sn}: units missing from painted subtitle {sub!r}"

    def test_mutation_matches_restored_fixture(self):
        broken = _load(BROKEN_V10)
        expected = _load(RESTORED)
        got = apply_issue_157_annex_matrices(copy.deepcopy(broken))
        for sn in (33, 34, 35, 36, 37):
            g, e = _by_number(got)[sn], _by_number(expected)[sn]
            assert g["layout_type"] == _ANNEX == e["layout_type"]
            assert _matrix(g) == _matrix(e) == SOURCE_MATRICES[sn]
            assert (g.get("content") or {}).get("body_text") == _UNITS[sn]
            assert _UNITS[sn] in ((g.get("content") or {}).get("subtitle") or "")
            assert g["title"] == e["title"]

    def test_mutation_is_idempotent(self):
        broken = _load(BROKEN_V10)
        once = apply_issue_157_annex_matrices(copy.deepcopy(broken))
        twice = apply_issue_157_annex_matrices(copy.deepcopy(once))
        for sn in (33, 34, 35, 36, 37):
            assert _matrix(_by_number(once)[sn]) == _matrix(_by_number(twice)[sn])

    def test_v10_broken_handoff_fails_probes(self):
        broken = _by_number(_load(BROKEN_V10))
        failures = []
        for sn in (33, 34, 35, 36, 37):
            try:
                assert_semantic_matrix(sn, _matrix(broken[sn]))
            except AssertionError as exc:
                failures.append((sn, str(exc).splitlines()[0]))
            else:
                pytest.fail(
                    f"v10 broken slide {sn} unexpectedly passed semantic probe"
                )
        assert len(failures) == 5


# ---------------------------------------------------------------------------
# Render surface: identity + complete matrices; no pseudo-token stubs
# ---------------------------------------------------------------------------


class TestAnnexRenderSurface:
    def test_render_identity_and_painted_values(self):
        handoff = apply_issue_157_annex_matrices(copy.deepcopy(_load(BROKEN_V10)))
        evidence: list[dict] = []
        painted_tokens = {
            33: (
                "FX-Adjusted Total Balances*",
                "$140",
                "$209",
                "8%",
                "$ in billions",
            ),
            34: (
                "Discount Revenue",
                "$9,512",
                "$18,907",
                "$17,210",
                "$ in millions",
            ),
            35: ("GAAP Net Card Fees", "$2.8", "18%", "$ in billions"),
            36: ("GAAP Net Interest Income", "$4.7", "13%", "$ in billions"),
            37: (
                "FX-Adjusted Revenues Net of Interest Expense*",
                "$15.7",
                "$18.9",
                "$ in billions",
            ),
        }
        for sn in (33, 34, 35, 36, 37):
            slide = _by_number(handoff)[sn]
            model, err = validate_slide(slide)
            assert model is not None, err
            html = render_slide(slide, total=44, notes="", active=True)
            attrs = _section_attrs(html, sn)
            assert attrs["data-layout"] == _ANNEX
            evidence.append(attrs)
            for token in painted_tokens[sn]:
                assert token in html, f"slide {sn}: missing painted token {token!r}"
            # Units must appear in the painted dek (not only handoff JSON).
            assert _UNITS[sn] in html, f"slide {sn}: units not painted"
            if sn == 34:
                assert "$ in millions" in html
                assert "$ in billions" not in html
            else:
                assert "$ in billions" in html
            stubs = re.findall(r'<td class="gl-annex-stub">([^<]*)</td>', html)
            period_only = [
                s for s in stubs if re.fullmatch(r"Q[1-4]'?\d{2}", s.strip())
            ]
            assert not period_only, f"slide {sn} period-token stubs: {period_only}"
            assert "annex-table" in html
            assert "FX-adjusted" in html or "FX-Adjusted" in html
        assert evidence == [
            {"data-slide-number": str(n), "data-layout": _ANNEX}
            for n in (33, 34, 35, 36, 37)
        ]

    def test_restored_deck_paints_all_values(self, tmp_path: Path):
        out = tmp_path / "out"
        render_deck(RESTORED, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        for token in (
            "FX-Adjusted Total Balances*",
            "$140",
            "$209",
            "Discount Revenue",
            "$9,512",
            "$18,907",
            "$17,210",
            "GAAP Net Card Fees",
            "$2.8",
            "Q1'26",
            "GAAP Net Interest Income",
            "$4.7",
            "FX-Adjusted Revenues Net of Interest Expense*",
            "$15.7",
            "$18.9",
            "$ in billions",
            "$ in millions",
            "gl-annex-stub",
            "annex-table",
        ):
            assert token in html, f"missing painted token {token!r}"
        stubs = re.findall(r'<td class="gl-annex-stub">([^<]*)</td>', html)
        period_only = [s for s in stubs if re.fullmatch(r"Q[1-4]'?\d{2}", s.strip())]
        assert not period_only, f"period-token pseudo-row stubs: {period_only}"

    def test_broken_v10_still_renders_but_lacks_fx_total_balances_row(
        self, tmp_path: Path
    ):
        out = tmp_path / "out"
        render_deck(BROKEN_V10, out, strict=False)
        html = (out / "presentation.html").read_text(encoding="utf-8")
        assert "FX-Adjusted Total Balances*" not in html
        assert "$140" not in html


# ---------------------------------------------------------------------------
# Mutation tests — each removal must fail the semantic probe
# ---------------------------------------------------------------------------


class TestAnnexMutations:
    def _mutate_and_probe(self, mutator, slide_number: int = 33):
        h = _load(RESTORED)
        mutator(h)
        slide = _by_number(h)[slide_number]
        with pytest.raises(AssertionError):
            assert_semantic_matrix(slide_number, _matrix(slide))

    def test_drop_value_row_fails(self):
        def drop_fx_row(h):
            m = _matrix(_by_number(h)[33])
            m = [r for r in m if "FX-Adjusted Total Balances" not in r[0]]
            _by_number(h)[33]["visual_spec"]["primary_visual"]["steps_or_data"] = m

        self._mutate_and_probe(drop_fx_row)

    def test_drop_final_period_fails(self):
        def drop_q126(h):
            m = _matrix(_by_number(h)[33])
            m = [r[:-1] for r in m]
            _by_number(h)[33]["visual_spec"]["primary_visual"]["steps_or_data"] = m

        self._mutate_and_probe(drop_q126)

    def test_drop_one_fx_value_fails(self):
        def blank_fx_value(h):
            m = copy.deepcopy(_matrix(_by_number(h)[33]))
            for r in m:
                if r[0].startswith("FX-Adjusted Total Balances"):
                    r[1] = ""  # blank $140 under Q1'19
                    break
            _by_number(h)[33]["visual_spec"]["primary_visual"]["steps_or_data"] = m

        self._mutate_and_probe(blank_fx_value)

    def test_mutations_also_fail_on_slide_34(self):
        h = _load(RESTORED)
        m = copy.deepcopy(_matrix(_by_number(h)[34]))
        m = [r for r in m if r[0] != "Net Card Fees"]
        _by_number(h)[34]["visual_spec"]["primary_visual"]["steps_or_data"] = m
        with pytest.raises(AssertionError):
            assert_semantic_matrix(34, _matrix(_by_number(h)[34]))


# ---------------------------------------------------------------------------
# Browser geometry — stub widths, numeric alignment, no clip at 1920×1080
# ---------------------------------------------------------------------------


def _deck_with_stable_slide_numbers(path: Path) -> dict:
    """Pad fillers so load_handoff keeps PDF page numbers 33–37.

    render_deck renumbers partial decks after injecting a cover; probes must
    address boards by data-slide-number + data-layout only.
    """
    handoff = _load(path)
    by = _by_number(handoff)
    slides: list[dict] = [
        {
            "slide_number": 1,
            "layout_type": "title_or_opening",
            "packing_mode": "cover-led",
            "title": "Cover",
            "content": {"headline": "Cover", "bullets": []},
            "visual_spec": {
                "primary_visual": {
                    "type": "other",
                    "steps_or_data": [],
                }
            },
        }
    ]
    for n in range(2, 33):
        slides.append(
            {
                "slide_number": n,
                "layout_type": "metric",
                "title": f"Pad {n}",
                "content": {"key_stats": [{"label": "n", "value": str(n)}]},
                "visual_spec": {
                    "primary_visual": {"type": "other", "steps_or_data": []}
                },
            }
        )
    for n in (33, 34, 35, 36, 37):
        slides.append(copy.deepcopy(by[n]))
    handoff = copy.deepcopy(handoff)
    handoff["slides"] = slides
    return handoff


class TestAnnexBrowserGeometry:
    def test_stub_and_numeric_cells_readable(self, tmp_path: Path):
        pytest.importorskip("playwright.sync_api")
        from playwright.sync_api import sync_playwright

        # Split so layout-index word search does not treat the JS string
        # as a layout reference in this test file.
        layout_attr = _ANNEX

        out = tmp_path / "out"
        deck_path = tmp_path / "padded_handoff.json"
        deck_path.write_text(
            json.dumps(_deck_with_stable_slide_numbers(RESTORED), indent=2),
            encoding="utf-8",
        )
        render_deck(deck_path, out, strict=False)
        html_path = (out / "presentation.html").resolve()

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            page.goto(html_path.as_uri())
            for sn in (33, 34, 35, 36, 37):
                metrics = page.evaluate(
                    """({sn, layout}) => {
                    const root = document.querySelector(
                        '.slide[data-slide-number="' + sn + '"][data-layout="' + layout + '"]'
                    );
                    if (!root) return {ok:false, reason:'missing slide '+sn};
                    document.querySelectorAll('.slide').forEach(
                        s => s.classList.remove('active')
                    );
                    root.classList.add('active');
                    const stubs = [...root.querySelectorAll('td.gl-annex-stub')];
                    const nums = [...root.querySelectorAll('td.gl-annex-cell.num')];
                    const heads = [...root.querySelectorAll('th.gl-annex-head')];
                    if (!stubs.length || !nums.length) {
                        return {ok:false, reason:'no cells', nStubs:stubs.length, nNums:nums.length};
                    }
                    const stubWs = stubs.map(e => e.getBoundingClientRect().width);
                    const numWs = nums.map(e => e.getBoundingClientRect().width);
                    const fs = parseFloat(getComputedStyle(nums[0]).fontSize) || 0;
                    const clip = stubs.concat(nums).some(e => {
                        const r = e.getBoundingClientRect();
                        return r.right > 1920 + 1 || r.bottom > 1080 + 1
                            || r.width < 1 || r.height < 1;
                    });
                    const aligns = nums.slice(0, 8).map(
                        e => getComputedStyle(e).textAlign
                    );
                    return {
                        ok: true,
                        nStubs: stubs.length,
                        nNums: nums.length,
                        nHeads: heads.length,
                        minStubW: Math.min(...stubWs),
                        maxStubW: Math.max(...stubWs),
                        minNumW: Math.min(...numWs),
                        fontSize: fs,
                        clip,
                        aligns,
                    };
                }""",
                    {"sn": sn, "layout": layout_attr},
                )
                assert metrics.get("ok"), f"slide {sn}: {metrics}"
                assert metrics["nStubs"] >= 4, metrics
                assert metrics["nNums"] >= 5, metrics
                assert metrics["minStubW"] >= 80, f"slide {sn} stub too narrow: {metrics}"
                assert metrics["minNumW"] >= 28, f"slide {sn} num too narrow: {metrics}"
                assert metrics["fontSize"] >= 9, f"slide {sn} type too small: {metrics}"
                assert not metrics["clip"], f"slide {sn} clips viewport: {metrics}"
                assert all(a in ("right", "end") for a in metrics["aligns"]), (
                    f"slide {sn} numeric alignment: {metrics['aligns']}"
                )
            browser.close()
