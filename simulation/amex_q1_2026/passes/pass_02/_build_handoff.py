"""Pass 02 handoff — close residual type-(A) divergences from pass_01.

Inputs: pass_01 handoff (already mapped onto IR layouts). This pass only
retunes JSON expressive fields; no production renderer edits.

Targets (pass_01 residual A candidates + worst MAE slides):
  * slide 05 Platinum — grouped_bar + multi_panel 2-chart (no empty metric tile)
  * slide 11 Acquisitions — PDF metric order (73% Millennial first, then 66%)
  * slide 18 Total Rev — line_chart (FX/Reported YoY) + $B under-table
  * slide 27 Funding — multi_panel dual stacked mix boards from raw %s
  * slide 03 Billed Business — annotation n/text polish; keep table/line
  * brand_mark_svg — denser Centurion-ish geometric mark on dividers
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

PASS = Path(__file__).resolve().parent
SRC = PASS.parent / "pass_01" / "handoff.json"
OUT = PASS / "handoff.json"

# Denser seal-ish mark (still generic geometric stand-in; not trademark art).
BRAND_MARK_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">'
    '<circle cx="60" cy="60" r="56" fill="#00175A"/>'
    '<circle cx="60" cy="60" r="50" fill="none" stroke="#FFFFFF" stroke-width="3"/>'
    '<circle cx="60" cy="60" r="42" fill="none" stroke="#FFFFFF" stroke-width="1.5"/>'
    '<circle cx="60" cy="60" r="34" fill="none" stroke="#FFFFFF" stroke-width="1"/>'
    '<polygon points="60,18 68,42 94,44 74,60 80,86 60,72 40,86 46,60 26,44 52,42" '
    'fill="#FFFFFF"/>'
    '<path d="M30,96 Q60,108 90,96" fill="none" stroke="#FFFFFF" stroke-width="2"/>'
    "</svg>"
)


def _fix_platinum(s: dict) -> dict:
    """PDF: left accelerated spend BAR card + right retention HORIZONTAL bars."""
    prev = s
    pvs = prev.get("visual_spec") or {}
    # Prefer original data shapes if present on pass_01 multi_panel tiles
    tiles_in = ((pvs.get("primary_visual") or {}).get("tiles")) or []
    spend_sod = []
    ret_sod = []
    for t in tiles_in:
        lab = (t.get("label") or "").lower()
        if "spend" in lab or t.get("chart_type") == "line_chart" and not spend_sod:
            if "spend" in lab:
                spend_sod = t.get("steps_or_data") or spend_sod
        if "retention" in lab:
            ret_sod = t.get("steps_or_data") or ret_sod
    if not spend_sod:
        for t in tiles_in:
            if t.get("kind") == "chart" and not spend_sod:
                spend_sod = t.get("steps_or_data") or []
            elif t.get("kind") == "chart" and spend_sod and not ret_sod:
                ret_sod = t.get("steps_or_data") or []
    if not spend_sod:
        spend_sod = [
            {"label": "Q1'25", "value": 7},
            {"label": "Q2'25", "value": 7},
            {"label": "Q3'25", "value": 9},
            {"label": "Q4'25", "value": 9},
            {"label": "Q1'26", "value": 10},
        ]
    if not ret_sod:
        ret_sod = [
            {"label": "January", "value": 94, "series_2": 96},
            {"label": "February", "value": 95, "series_2": 97},
            {"label": "March", "value": 95, "series_2": 97},
        ]

    spend_cfg = {
        "y_axis_min": 0,
        "y_axis_max": 15,
        "y_axis_ticks": [0, 5, 10, 15],
        "force_ticks": True,
        "y_axis_unit": "%",
        "show_point_labels": True,
        "point_labels": True,
        "series_names": ["Spend growth"],
        "series_colors": ["#00175A"],
        # A/B callout text where dedicated arrow chrome is missing
        "annotation": {"text": "+ ~6 percentage points  ·  Refresh", "x": 120, "y": 40},
    }
    # True horizontal bars not available; grouped_bar + broken axis is best
    # approximation for retention (PDF is 90–100% horizontal anniversary bars).
    ret_cfg = {
        "y_axis_break": {"from": 0, "to": 90},
        "y_axis_min": 90,
        "y_axis_max": 100,
        "y_axis_ticks": [90, 92, 94, 96, 98, 100],
        "force_ticks": True,
        "y_axis_unit": "%",
        "show_point_labels": True,
        "point_labels": True,
        "series_names": ["2025 (pre-refresh year)", "2026 (post-refresh)"],
        "series_colors": ["#006FCF", "#00175A"],
    }
    # Convert retention dict points into matrix rows for grouped bar
    ret_matrix = [
        ["Month", "2025", "2026"],
    ]
    for pt in ret_sod:
        if isinstance(pt, dict):
            ret_matrix.append(
                [
                    str(pt.get("label") or ""),
                    str(pt.get("value") if pt.get("value") is not None else ""),
                    str(pt.get("series_2") if pt.get("series_2") is not None else ""),
                ]
            )

    spend_matrix = [["Quarter", "Spend growth %"]]
    for pt in spend_sod:
        if isinstance(pt, dict):
            spend_matrix.append(
                [str(pt.get("label") or ""), str(pt.get("value") if pt.get("value") is not None else "")]
            )

    out = {
        "slide_number": prev.get("slide_number") or 6,
        "layout_type": "multi_panel",
        "packing_mode": "chart-led",
        "title": prev.get("title") or "U.S. Consumer Platinum Performance",
        "section": prev.get("section") or "US Consumer",
        "content": {
            "subtitle": "Spend Growth is Accelerating · Retention Rates Remain High and Very Stable",
            "so_what": "Refresh cohort shows ~+6 pp spend acceleration with stable anniversary retention",
            "key_stats": [
                {"label": "Refresh lift (spend)", "value": "+~6 pp"},
            ],
        },
        "visual_spec": {
            "primary_visual": {
                "type": "multi_panel",
                "tiles": [
                    {
                        "kind": "chart",
                        "chart_type": "grouped_bar_chart",
                        "label": "Spend Growth is Accelerating",
                        "steps_or_data": spend_matrix,
                        "chart_config": spend_cfg,
                    },
                    {
                        "kind": "chart",
                        "chart_type": "grouped_bar_chart",
                        "label": "Retention Rates Remain High and Very Stable",
                        "steps_or_data": ret_matrix,
                        "chart_config": ret_cfg,
                    },
                ],
            }
        },
        "speaker_notes": (
            "v2 pass_02: multi_panel dual grouped_bar; spend as bars not lines; "
            "retention ymin=90 + y_axis_break (F10); omitted empty metric tile. "
            "True horizontal anniversary bars + Refresh arrow band still type B."
        ),
    }
    return out


def _fix_acquisitions(s: dict) -> dict:
    out = deepcopy(s)
    # PDF metrics order: Millennial/Gen-Z 73% (top) then Fee-Paying 66%.
    out["content"] = dict(out.get("content") or {})
    out["content"]["key_stats"] = [
        {
            "label": "Global Consumer New Accounts Acquired from Millennial / Gen-Z",
            "value": "73%",
        },
        {
            "label": "Global New Accounts Acquired on Fee-Paying Products*",
            "value": "66%",
        },
    ]
    # Stack totals as point labels when supported
    pv = ((out.get("visual_spec") or {}).get("primary_visual") or {})
    cfg = dict(pv.get("chart_config") or {})
    cfg.update(
        {
            "show_point_labels": True,
            "point_labels": True,
            "stacked": True,
            "series_names": cfg.get("series_names")
            or [
                "U.S. Consumer Services",
                "Commercial Services",
                "International Card Services",
            ],
            "series_colors": cfg.get("series_colors")
            or ["#00175A", "#006FCF", "#8A93A6"],
        }
    )
    out["visual_spec"] = {
        **(out.get("visual_spec") or {}),
        "primary_visual": {**pv, "chart_config": cfg},
    }
    out["speaker_notes"] = (
        "v2 pass_02: hero key_stats reordered to PDF (73% Millennial, 66% Fee-Paying) (A)."
    )
    return out


def _fix_total_revenues(s: dict) -> dict:
    """PDF is dual YoY lines + $B band table — not a bar-driven combo."""
    return {
        "slide_number": s.get("slide_number") or 19,
        "layout_type": "line_chart",
        "packing_mode": "chart-led",
        "title": s.get("title") or "Total Revenues Net of Interest Expense",
        "section": s.get("section") or "Revenue",
        "content": {
            "subtitle": "$ in billions — % Increase/(decrease) vs. Prior year",
            "so_what": "",
            "key_stats": [],
        },
        "visual_spec": {
            "primary_visual": {
                "type": "line_chart",
                "steps_or_data": [
                    # value = FX Adjusted; series_2 = Reported (matches PDF roles)
                    {"label": "Q1'25", "value": 7, "series_2": 8},
                    {"label": "Q2'25", "value": 9, "series_2": 9},
                    {"label": "Q3'25", "value": 11, "series_2": 11},
                    {"label": "Q4'25", "value": 10, "series_2": 9},
                    {"label": "Q1'26", "value": 11, "series_2": 10},
                ],
                "chart_config": {
                    "series_names": ["FX Adjusted", "Reported"],
                    "series_styles": ["solid", "dashed"],
                    "series_colors": ["#00175A", "#8A93A6"],
                    "y_axis_min": 0,
                    "y_axis_max": 15,
                    "y_axis_ticks": [0, 5, 10, 15],
                    "force_ticks": True,
                    "y_axis_unit": "%",
                    "y_axis_label": "%",
                    "gridlines": True,
                    "show_point_labels": True,
                    "point_labels": True,
                    "annotation": {
                        "text": "Leap Year Approx. (1%)",
                        "x": 80,
                        "y": 40,
                    },
                },
            },
            "secondary_visual": {
                "type": "data_table",
                "steps_or_data": [
                    ["", "Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"],
                    ["$B", "$17.0", "$17.9", "$18.4", "$19.0", "$18.9"],
                ],
            },
        },
        "disclosure": s.get("disclosure"),
        "speaker_notes": (
            "v2 pass_02: switched combo→line_chart with dual YoY series + $B under-table "
            "(A). PDF navy under-band styling still type B residual."
        ),
    }


def _fix_funding(s: dict) -> dict:
    """PDF page 28: Funding Mix + Deposit Programs paired stacked compositions."""
    funding_mix = [
        ["Quarter", "Deposits", "Long-term Debt / Unsecured**", "Card ABS*", "Other / ST"],
        ["Q4'25", "72", "21", "6", "1"],
        ["Q1'26", "72", "21", "6", "1"],
    ]
    # approximate deposit program mix from vision dump: Savings/Direct CDs dominate,
    # with Third Party CDs / Sweep / Checking remaining.
    deposit_prog = [
        [
            "Quarter",
            "Savings and Direct CDs",
            "Third Party CDs",
            "Third Party Sweep",
            "Checking",
        ],
        # shares that roughly reconstitute ~$210B / $219B with direct ~81-82%
        ["Q4'25", "81", "10", "7", "2"],
        ["Q1'26", "82", "10", "6", "2"],
    ]
    return {
        "slide_number": s.get("slide_number") or 28,
        "layout_type": "multi_panel",
        "packing_mode": "chart-led",
        "title": s.get("title") or "Funding and Deposits",
        "section": s.get("section") or "Appendix",
        "content": {
            "subtitle": "$ in billions",
            "so_what": "",
            "key_stats": [
                {"label": "Customer Deposits Q1'26", "value": "72%"},
                {"label": "Deposit Balances", "value": "$219B"},
                {"label": "Direct Deposits share", "value": "82%"},
                {"label": "FDIC insured (Q1'26)", "value": "92%"},
            ],
        },
        "visual_spec": {
            "primary_visual": {
                "type": "multi_panel",
                "tiles": [
                    {
                        "kind": "chart",
                        "chart_type": "stacked_bar_chart",
                        "label": "Funding Mix",
                        "steps_or_data": funding_mix,
                        "chart_config": {
                            "stacked": True,
                            "y_axis_min": 0,
                            "y_axis_max": 100,
                            "y_axis_unit": "%",
                            "force_ticks": True,
                            "series_names": [
                                "Deposits",
                                "Long-term Debt / Unsecured**",
                                "Card ABS*",
                                "Other / ST",
                            ],
                            "series_colors": [
                                "#00175A",
                                "#006FCF",
                                "#5B6B9A",
                                "#B8BFC9",
                            ],
                        },
                    },
                    {
                        "kind": "chart",
                        "chart_type": "stacked_bar_chart",
                        "label": "Deposit Programs",
                        "steps_or_data": deposit_prog,
                        "chart_config": {
                            "stacked": True,
                            "y_axis_min": 0,
                            "y_axis_max": 100,
                            "y_axis_unit": "%",
                            "force_ticks": True,
                            "series_names": [
                                "Savings and Direct CDs",
                                "Third Party CDs",
                                "Third Party Sweep",
                                "Checking",
                            ],
                            "series_colors": [
                                "#00175A",
                                "#006FCF",
                                "#5B6B9A",
                                "#B8BFC9",
                            ],
                        },
                    },
                    {
                        "kind": "metric",
                        "label": "Deposit Balances Q1'26",
                        "value": "$219B",
                    },
                    {
                        "kind": "metric",
                        "label": "92% FDIC insured at Q1'26",
                        "value": "92%",
                    },
                ],
            }
        },
        "disclosure": s.get("disclosure"),
        "speaker_notes": (
            "v2 pass_02: multi_panel Funding Mix + Deposit Programs stacked 100% boards "
            "(A layout remapping from metric_dashboard)."
        ),
    }


def _polish_billed(s: dict) -> dict:
    out = deepcopy(s)
    pv = ((out.get("visual_spec") or {}).get("primary_visual") or {})
    cfg = dict(pv.get("chart_config") or {})
    cfg.update(
        {
            "annotation": {
                "text": "Leap Year Approx. (1%)",
                "x": 90,
                "y": 55,
            },
            "force_ticks": True,
            "show_point_labels": True,
            "point_labels": True,
            "y_axis_min": 0,
            "y_axis_max": 15,
            "y_axis_ticks": [0, 5, 10, 15],
        }
    )
    out["visual_spec"] = {
        **(out.get("visual_spec") or {}),
        "primary_visual": {**pv, "chart_config": cfg},
    }
    out["content"] = dict(out.get("content") or {})
    out["content"]["subtitle"] = (
        "% Increase/(decrease) vs. Prior year (FX-adjusted unless otherwise stated)"
    )
    out["speaker_notes"] = (
        (out.get("speaker_notes") or "")
        + " | v2 pass_02: annotation placement polish (A)."
    ).strip(" |")
    return out


def _apply_brand_mark(s: dict) -> dict:
    out = deepcopy(s)
    c = dict(out.get("content") or {})
    c["brand_mark_svg"] = BRAND_MARK_SVG
    c["brand_tone"] = c.get("brand_tone") or "two-tone"
    out["content"] = c
    return out


def transform(slides: list[dict]) -> list[dict]:
    s = deepcopy(slides)
    assert len(s) == 44

    s[3] = _polish_billed(s[3])
    s[5] = _fix_platinum(s[5])
    s[11] = _fix_acquisitions(s[11])
    s[18] = _fix_total_revenues(s[18])
    s[27] = _fix_funding(s[27])

    # Refresh brand mark on cover attempt + dividers
    s[0] = _apply_brand_mark(s[0])
    s[22] = _apply_brand_mark(s[22])
    s[43] = _apply_brand_mark(s[43])

    # Ensure consecutive slide numbers
    for i, sl in enumerate(s):
        sl["slide_number"] = i + 1
    return s


def main() -> None:
    src = json.loads(SRC.read_text(encoding="utf-8"))
    slides = transform(src["slides"])
    handoff = {
        "presentation": {
            **(src.get("presentation") or {}),
            "subtitle": "Simulation handoff · v2 pass_02 · residual A tuning",
            "quality_flags": [
                "simulation",
                "amex_q1_2026",
                "pass_02",
                "v2_post_fixes",
                "type_a_tuning",
            ],
            "primary_goal": (
                "Close residual handoff-tuning gaps: platinum bar types, revenue "
                "line+under-table, acquisitions hero order, funding multi_panel"
            ),
        },
        "slides": slides,
    }
    OUT.write_text(json.dumps(handoff, indent=2), encoding="utf-8")
    print(f"wrote {OUT} slides={len(slides)} bytes={OUT.stat().st_size}")
    for i in (0, 3, 5, 11, 18, 22, 27, 43):
        print(f"  [{i:02d}] {slides[i].get('layout_type')} · {slides[i].get('title')}")


if __name__ == "__main__":
    main()
