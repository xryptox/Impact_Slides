"""Bounded Amex handoff mutations applied before a fidelity simulation pass.

These correct authoring defects in archived handoffs. They do **not** change
renderer defaults. Each mutation is issue-scoped and idempotent.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

# Issue #148 — PDF physical pages / deck slides 13–14.
# v10 handoff requested line marks and swapped credit-pane semantics.
_S13 = 13
_S14 = 14

_S13_STEPS = [
    {"label": "Q1'25", "values": {"Total Balances": 7, "Billed Business": 6}},
    {"label": "Q2'25", "values": {"Total Balances": 6, "Billed Business": 7}},
    {"label": "Q3'25", "values": {"Total Balances": 7, "Billed Business": 8}},
    {"label": "Q4'25", "values": {"Total Balances": 7, "Billed Business": 8}},
    {"label": "Q1'26", "values": {"Total Balances": 7, "Billed Business": 9}},
]

_S14_LEFT_STEPS = [
    {"label": "Q1'25", "value": 1.3},
    {"label": "Q2'25", "value": 1.3},
    {"label": "Q3'25", "value": 1.3},
    {"label": "Q4'25", "value": 1.3},
    {"label": "Q1'26", "value": 1.3},
]

_S14_RIGHT_STEPS = [
    {"label": "Q1'25", "value": 2.1},
    {"label": "Q2'25", "value": 2.0},
    {"label": "Q3'25", "value": 1.9},
    {"label": "Q4'25", "value": 2.1},
    {"label": "Q1'26", "value": 2.0},
]

# Issue #156 — PDF page / deck slide 27 macroeconomic scenarios.
# Values transcribed from Q1-2026-Earnings-Presentation.pdf, PDF page 27.
_S27 = 27
_S27_PERIODS = [
    "Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26", "Q2'26", "Q3'26",
    "Q4'26", "Q1'27", "Q2'27", "Q3'27", "Q4'27", "Q1'28",
]
_S27_SERIES = ["Q1 Upside Scenario", "Q1 Baseline Scenario", "Q1 Downside Scenario"]
_S27_UNEMPLOYMENT = [
    [4.1, 4.2, 4.3, 4.5, 4.5, 4.0, 3.6, 3.5, 3.4, 3.4, 3.5, 3.7, 3.8],
    [4.1, 4.2, 4.3, 4.5, 4.5, 4.5, 4.5, 4.5, 4.4, 4.4, 4.4, 4.4, 4.4],
    [4.1, 4.2, 4.3, 4.5, 4.5, 6.1, 7.2, 8.0, 8.4, 8.4, 8.3, 8.0, 7.6],
]
_S27_GDP = [
    [-0.6, 3.9, 4.4, 2.9, 3.1, 4.8, 3.3, 3.2, 3.2, 2.6, 1.8, 2.2, 1.6],
    [-0.6, 3.9, 4.4, 2.9, 3.1, 2.6, 2.0, 1.8, 1.7, 1.7, 1.8, 1.9, 1.9],
    [-0.6, 3.9, 4.4, 2.9, 3.1, -3.5, -3.2, -3.8, 0.5, 1.0, 1.3, 1.6, 1.6],
]

# Issue #157 — PDF pages / deck slides 33–37 annex matrices.
# v10 handoff lost FX rows, value cells, and period associations.
_FX_NOTE = "* See Slide 3 for an explanation of FX-adjusted information."
# annex_table paints subtitle via chosen_dek; body_text is not rendered.
# Put units first so slide 34 ($ in millions) is visibly distinct from
# 33/35–37 ($ in billions) without a renderer production change.
_ANNEX_FRAME = "% Increase/(decrease) vs. Prior year"


def _annex_subtitle(units: str) -> str:
    return f"{units} · {_ANNEX_FRAME}"


_ANNEX_33_37: dict[int, dict[str, Any]] = {
    33: {
        "title": "Annex 2 Total Balances — Reported & FX-Adjusted",
        "units": "$ in billions",
        "rows": [
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
    },
    34: {
        "title": "Annex 3 Revenue — Reported & FX-Adjusted",
        "units": "$ in millions",
        "rows": [
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
    },
    35: {
        "title": "Annex 4 Net Card Fees — Reported & FX-Adjusted",
        "units": "$ in billions",
        "rows": [
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
    },
    36: {
        "title": "Annex 5 Net Interest Income — Reported & FX-Adjusted",
        "units": "$ in billions",
        "rows": [
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
    },
    37: {
        "title": "Annex 6 Revenues Net of Interest Expense — Reported & FX-Adjusted",
        "units": "$ in billions",
        "rows": [
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
    },
}


def _slide(handoff: dict[str, Any], number: int) -> dict[str, Any]:
    for s in handoff.get("slides") or []:
        if int(s.get("slide_number", -1)) == number:
            return s
    raise KeyError(f"handoff missing slide_number={number}")


def _has_slide(handoff: dict[str, Any], number: int) -> bool:
    return any(int(s.get("slide_number", -1)) == number for s in handoff.get("slides") or [])


def apply_issue_148_bar_semantics(handoff: dict[str, Any]) -> dict[str, Any]:
    """Restore vertical bars + PDF pane order on Amex slides 13 and 14.

    - Slide 13: grouped vertical bar chart (Total Balances / Billed Business).
    - Slide 14: dual_chart of vertical bars; left = 30+ Days Past Due (~1.3%),
      right = Net Write-Off Rates (~2%).
    Missing either slide is a no-op for that slide (partial handoffs ok).
    """
    out = handoff  # caller may pass an already-copied dict
    try:
        s13 = _slide(out, _S13)
    except KeyError:
        s13 = None
    if s13 is not None:
        s13["layout_type"] = "grouped_bar_chart"
        s13["visual_spec"] = {
            "primary_visual": {
                "type": "grouped_bar_chart",
                "steps_or_data": deepcopy(_S13_STEPS),
                "chart_config": {
                    "series_names": ["Total Balances", "Billed Business"],
                    "series_colors": ["#00175A", "#006FCF"],
                    "y_axis_min": 0,
                    "y_axis_max": 15,
                    "y_axis_ticks": [0, 5, 10, 15],
                    "y_axis_unit": "%",
                    "y_axis_label": "%",
                },
            }
        }
        s13["speaker_notes"] = "Grouped vertical bars: balances vs billed business."

    try:
        s14 = _slide(out, _S14)
    except KeyError:
        s14 = None
    if s14 is not None:
        s14["layout_type"] = "dual_chart"
        s14["content"] = dict(s14.get("content") or {})
        s14["content"]["subtitle"] = "30+ days past due and net write-off rates"
        s14["visual_spec"] = {
            "primary_visual": {
                "type": "grouped_bar_chart",
                "heading": "30+ Days Past Due",
                "steps_or_data": deepcopy(_S14_LEFT_STEPS),
                "chart_config": {
                    "series_names": ["30+ Days Past Due"],
                    "series_colors": ["#00175A"],
                    "y_axis_min": 0,
                    "y_axis_max": 3,
                    "y_axis_unit": "%",
                },
            },
            "secondary_visual": {
                "type": "grouped_bar_chart",
                "heading": "Net Write-Off Rates",
                "steps_or_data": deepcopy(_S14_RIGHT_STEPS),
                "chart_config": {
                    "series_names": ["Net Write-Off Rates"],
                    "series_colors": ["#006FCF"],
                    "y_axis_min": 0,
                    "y_axis_max": 3,
                    "y_axis_unit": "%",
                },
            },
        }
        s14["speaker_notes"] = (
            "PDF pane order: 30+ DPD left (~1.3%), net write-offs right (~2%)."
        )
    return out


def _s27_steps(values: list[list[float]]) -> list[dict[str, float | str]]:
    return [
        {"label": label, "value": values[0][i], "series_2": values[1][i], "series_3": values[2][i]}
        for i, label in enumerate(_S27_PERIODS)
    ]


def apply_issue_156_slide27_scenarios(handoff: dict[str, Any]) -> dict[str, Any]:
    """Restore slide 27's PDF periods, scenarios, pane headings, and note.

    Type (A) handoff fix only. The paint-ready capture guard is already shared
    in ``simulation_probe`` (#146); no renderer behavior changes here.
    """
    out = handoff
    try:
        slide = _slide(out, _S27)
    except KeyError:
        return out
    slide["layout_type"] = "dual_chart"
    slide["packing_mode"] = "chart-led"
    content = dict(slide.get("content") or {})
    content.update({"subtitle": "", "so_what": ""})
    slide["content"] = content
    slide["visual_spec"] = {
        "primary_visual": {
            "type": "line_chart",
            "heading": "U.S. Unemployment Rate %",
            "steps_or_data": _s27_steps(_S27_UNEMPLOYMENT),
            "chart_config": {
                "series_names": list(_S27_SERIES),
                "series_colors": ["#7F7F7F", "#006FCF", "#002060"],
                "series_styles": ["solid", "solid", "solid"],
                "y_axis_min": 0,
                "y_axis_max": 10,
                "y_axis_unit": "%",
            },
        },
        "secondary_visual": {
            "type": "line_chart",
            "heading": "U.S. GDP Growth* %",
            "steps_or_data": _s27_steps(_S27_GDP),
            "chart_config": {
                "series_names": list(_S27_SERIES),
                "series_colors": ["#7F7F7F", "#006FCF", "#002060"],
                "series_styles": ["solid", "solid", "solid"],
                "y_axis_min": -5,
                "y_axis_max": 6,
                "y_axis_unit": "%",
            },
        },
    }
    slide["evidence_sources"] = [
        {"id": "E0026", "source_file": "Q1-2026-Earnings-Presentation.pdf, PDF page 27"}
    ]
    slide["disclosure"] = {
        "pattern": "detail",
        "panels": [{
            "title": "Scenario note",
            "body": "Reflects the range of variables available as of March 31, 2026. "
            "Forecast assumptions are from an independent third party and represent the range "
            "of forecasts from the macroeconomic scenarios used during the quarter without "
            "applying a weight to those scenarios. * Real GDP QoQ % Change Seasonally Adjusted "
            "to Annualized Rates (SAAR).",
        }],
    }
    slide["speaker_notes"] = "PDF scenario paths restored for all three Q1 scenarios through Q1'28 (#156)."
    return out


# Issue #159 — PDF physical page / deck slide 32 grouped annex tables.
_S32 = 32
_S32_GROUPS = [
    {
        "heading": "Commercial Services",
        "headers": ["Segment", "Q1'26 Reported", "FX-Adj.*"],
        "rows": [
            {"cells": ["U.S. Large and Global Corp.", "4%", "4%"], "role": "child", "indent": 1},
            {"cells": ["Total Billed Business", "4%", "4%"], "role": "aggregate"},
            {"cells": ["G&S", "3%", "3%"], "role": "child", "indent": 1},
            {"cells": ["T&E", "7%", "6%"], "role": "child", "indent": 1},
        ],
    },
    {
        "heading": "International Card Services",
        "headers": ["Segment", "Q1'26 Reported", "FX-Adj.*"],
        "rows": [
            {"cells": ["International Consumer", "21%", "13%"], "role": "child", "indent": 1},
            {"cells": ["International SME & Large Corp.", "19%", "12%"], "role": "child", "indent": 1},
            {"cells": ["Total Billed Business", "20%", "13%"], "role": "aggregate"},
            {"cells": ["G&S", "21%", "14%"], "role": "child", "indent": 1},
            {"cells": ["T&E", "18%", "10%"], "role": "child", "indent": 1},
        ],
    },
]


def apply_issue_159_grouped_annex(handoff: dict[str, Any]) -> dict[str, Any]:
    """Restore slide 32's two peer PDF annex blocks without flattening them."""
    out = handoff
    try:
        slide = _slide(out, _S32)
    except KeyError:
        return out
    slide["layout_type"] = "grouped_annex_table"
    slide["packing_mode"] = "stat-led"
    slide["title"] = "Annex 1 (2 of 2) Billed Business — Reported & FX-Adjusted"
    slide["section"] = "Annex"
    content = dict(slide.get("content") or {})
    content["subtitle"] = "% Increase/(decrease) vs. Prior year · $ where noted"
    content.setdefault("so_what", "")
    slide["content"] = content
    slide["visual_spec"] = {
        "primary_visual": {
            "type": "grouped_annex_table",
            "groups": deepcopy(_S32_GROUPS),
        }
    }
    slide["disclosure"] = {
        "pattern": "detail",
        "panels": [{"title": "FX-adjusted note", "body": _FX_NOTE}],
    }
    slide["speaker_notes"] = "Slide 32 retains Commercial Services and International Card Services as peer source tables (#159)."
    return out


# Issue #158 — PDF physical page / deck slide 28 multi_panel pane titles.
# v10 handoff put dollar stack totals in tile top_total pseudo-titles.
_S28 = 28
_S28_SUBTITLE = "$ in billions"
_S28_TILES = (
    ("Funding Mix", ["$210", "$219"]),
    ("Deposit Programs", ["$151", "$157"]),
)


def apply_issue_158_slide28_pane_titles(handoff: dict[str, Any]) -> dict[str, Any]:
    """Drop slide-28 top_total pseudo-titles; add pane subtitles.

    Keeps Funding Mix / Deposit Programs as pane headings (via label),
    explicit stack_total_labels as the only dollar totals, and the #138
    FDIC side_callout + exterior segment names unchanged. Does not remove
    legitimate top_total on other slides.
    """
    out = handoff
    try:
        s28 = _slide(out, _S28)
    except KeyError:
        return out
    if str(s28.get("layout_type") or "") != "multi_panel":
        return out
    vs = s28.get("visual_spec") or {}
    pv = vs.get("primary_visual") if isinstance(vs, dict) else None
    tiles = pv.get("tiles") if isinstance(pv, dict) else None
    if not isinstance(tiles, list):
        return out
    known = {name for name, _ in _S28_TILES}
    for tile in tiles:
        if not isinstance(tile, dict) or str(tile.get("kind") or "") != "chart":
            continue
        heading = str(tile.get("heading") or "").strip()
        label = str(tile.get("label") or heading or "").strip()
        # Only the two funding board panes; leave unrelated multi_panel tiles.
        if label not in known and heading not in known:
            continue
        tile.pop("top_total", None)
        tile["subtitle"] = _S28_SUBTITLE
        # Prefer stable label heading; do not invent parallel keys if label set.
        if not str(tile.get("label") or "").strip() and heading:
            tile["label"] = heading
        cfg = tile.get("chart_config")
        if not isinstance(cfg, dict):
            cfg = {}
            tile["chart_config"] = cfg
        # Preserve existing stack_total_labels when present; fill known defaults.
        if not cfg.get("stack_total_labels"):
            for name, totals in _S28_TILES:
                if label == name or heading == name:
                    cfg["stack_totals"] = True
                    cfg["stack_total_labels"] = list(totals)
                    break
    return out


def apply_issue_157_annex_matrices(handoff: dict[str, Any]) -> dict[str, Any]:
    """Restore complete PDF annex matrices on Amex slides 33–37.

    Type (A) handoff fix only: full GAAP / FX-adjusted / YoY / CAGR rows with
    source periods. Does not change renderer defaults. No-op when none of the
    annex slides are present (partial fixture handoffs).
    """
    out = handoff
    if not any(_has_slide(out, n) for n in _ANNEX_33_37):
        return out
    for number, meta in _ANNEX_33_37.items():
        if not _has_slide(out, number):
            continue
        slide = _slide(out, number)
        slide["layout_type"] = "annex_table"
        slide["packing_mode"] = "stat-led"
        slide["title"] = meta["title"]
        slide["section"] = "Annex"
        content = dict(slide.get("content") or {})
        units = str(meta["units"])
        content["subtitle"] = _annex_subtitle(units)
        content["body_text"] = units
        content.setdefault("so_what", "")
        slide["content"] = content
        slide["visual_spec"] = {
            "primary_visual": {
                "type": "annex_table",
                "steps_or_data": deepcopy(meta["rows"]),
            }
        }
        slide["disclosure"] = {
            "pattern": "detail",
            "panels": [{"title": "FX-adjusted note", "body": _FX_NOTE}],
        }
        slide["speaker_notes"] = (
            f"Annex slide {number} restored from PDF source matrix (#157). "
            "All GAAP, FX-adjusted, YoY, and CAGR rows preserved."
        )
    return out


def apply_all(handoff: dict[str, Any]) -> dict[str, Any]:
    """Apply every bounded Amex handoff mutation known to this module."""
    out = apply_issue_148_bar_semantics(handoff)
    out = apply_issue_156_slide27_scenarios(out)
    out = apply_issue_157_annex_matrices(out)
    out = apply_issue_159_grouped_annex(out)
    return apply_issue_158_slide28_pane_titles(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path, help="Source handoff JSON")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Destination handoff JSON (all known Amex mutations applied)",
    )
    args = p.parse_args(argv)
    data = json.loads(args.input.read_text(encoding="utf-8"))
    apply_all(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
