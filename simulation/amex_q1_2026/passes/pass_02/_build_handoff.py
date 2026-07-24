"""v3 pass_02 handoff — residual (A) tuning after pass_01 structural unlocks.

Starts from pass_01 handoff. Handoff-only; no renderer edits.

Targets (A where possible, reconfirm B where not):
  * slide 05  PDF card titles; band callout; series labels = year inside bars;
              stage flat; top totals as $ only (not%)
  * slide 00  Title includes Q1'26; date subtitle matches PDF
  * slide 11  key_stats narrative prose for giant heroes + stage flat chart
  * slide 14  PDF palette (write-offs cyan, reserve dark) + stage flat +
              reserve-rate row kept; drop bottom KPI strip dominance via
              leaner key_stats
  * slide 03/18 stage=flat (R1 residual probe)
  * slide 27  PDF exterior segment names via side_legend; top_total $ only;
              FDIC as content key_stat not card chrome thrash
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
P01_HANDOFF = (
    REPO
    / "simulation"
    / "amex_q1_2026"
    / "passes"
    / "pass_01"
    / "handoff.json"
)
OUT = Path(__file__).resolve().parent / "handoff.json"


def _fix_cover(s: dict) -> dict:
    out = deepcopy(s)
    out["layout_type"] = "brand_cover"
    out["title"] = "American Express Earnings Conference Call\nQ1'26"
    c = dict(out.get("content") or {})
    c["headline"] = "American Express Earnings Conference Call Q1'26"
    c["subtitle"] = "APRIL 23, 2026"
    c["brand_tone"] = "two-tone"
    c["brand_mark"] = "seal_lockup"
    c.pop("brand_mark_svg", None)
    c["key_stats"] = [{"label": "Date", "value": "APRIL 23, 2026"}]
    out["content"] = c
    out["speaker_notes"] = (
        "v3 pass_02: cover title pack includes Q1'26; subtitle is date only. "
        "Seal remains named seal_lockup (asset/placement still B)."
    )
    return out


def _fix_platinum(s: dict) -> dict:
    out = deepcopy(s)
    out["layout_type"] = "multi_panel"
    out["packing_mode"] = "chart-led"
    out["title"] = "U.S. Consumer Platinum Performance"
    out["content"] = {
        "subtitle": "",
        "so_what": "",
        "key_stats": [],
    }
    out["visual_spec"] = {
        "primary_visual": {
            "type": "multi_panel",
            "tiles": [
                {
                    "kind": "chart",
                    "chart_type": "grouped_bar_chart",
                    # PDF left card title
                    "label": "Spend Growth is Accelerating",
                    "top_total": "",
                    "badge": "",
                    "steps_or_data": [
                        ["Quarter", "Spend growth %"],
                        ["Q1'25", "7"],
                        ["Q2'25", "7"],
                        ["Q3'25", "9"],
                        ["Q4'25", "9"],
                        ["Q1'26", "10"],
                    ],
                    "chart_config": {
                        "y_axis_min": 0,
                        "y_axis_max": 12,
                        "y_axis_ticks": [0, 2, 4, 6, 8, 10, 12],
                        "force_ticks": True,
                        "y_axis_unit": "%",
                        "show_point_labels": False,
                        "point_labels": False,
                        "series_names": ["Spend growth"],
                        "series_colors": ["#00175A"],
                        "stage": "flat",
                        "callouts": [
                            {
                                "type": "band",
                                "from": 0,
                                "to": 4,
                                "text": "+ ~6 percentage points",
                            },
                            {
                                "type": "elbow_arrow",
                                "from": 0,
                                "to": 4,
                                "value": 11,
                                "text": "+ ~6 percentage points",
                            },
                            {
                                "type": "chevron",
                                "at": 4,
                                "text": "Refresh",
                            },
                        ],
                    },
                },
                {
                    "kind": "chart",
                    "chart_type": "horizontal_bar_chart",
                    # PDF right card title
                    "label": "Retention Rates Remain High and Very Stable",
                    "top_total": "",
                    "badge": "",
                    "side_legend": [],
                    "steps_or_data": [
                        # series names become the values painted by bar_labels_inside
                        ["Month", "2025", "2026"],
                        ["January", "94", "96"],
                        ["February", "95", "97"],
                        ["March", "95", "97"],
                    ],
                    "chart_config": {
                        "y_axis_break": {"from": 0, "to": 90},
                        "y_axis_min": 90,
                        "y_axis_max": 100,
                        "y_axis_ticks": [90, 92, 94, 96, 98, 100],
                        "force_ticks": True,
                        "y_axis_unit": "%",
                        "bar_labels_inside": True,
                        "show_point_labels": True,
                        "point_labels": True,
                        "series_names": ["2025", "2026"],
                        "series_colors": ["#006FCF", "#00175A"],
                        "stage": "flat",
                    },
                },
            ],
        }
    }
    out["speaker_notes"] = (
        "v3 pass_02: PDF card titles; band+elbow+chevron callouts; year-only "
        "series labels for inside-bar labels; stage flat. Anniversary 90–100 "
        "window still depends on Chart.js ticks.min/max clamp (B if paint fails)."
    )
    return out


def _fix_line(s: dict) -> dict:
    out = deepcopy(s)
    pv = ((out.get("visual_spec") or {}).get("primary_visual") or {})
    cfg = dict(pv.get("chart_config") or {})
    cfg["stage"] = "flat"
    out["visual_spec"] = {
        **(out.get("visual_spec") or {}),
        "primary_visual": {**pv, "chart_config": cfg},
    }
    notes = out.get("speaker_notes") or ""
    out["speaker_notes"] = notes + " | v3 pass_02: chart_config.stage=flat (R1)."
    return out


def _fix_acquisitions(s: dict) -> dict:
    out = deepcopy(s)
    # Canonical verbiage matched to PDF hero blocks.
    out["content"] = {
        "subtitle": "Proprietary New Cards / New Accounts — Q1'2026",
        "so_what": "",
        "key_stats": [
            {
                "label": "Global Consumer New Accounts Acquired from Millennial / Gen-Z",
                "value": "66%",
            },
            {
                "label": "Global New Accounts Acquired on Fee-Paying Products*",
                "value": "73%",
            },
        ],
    }
    pv = ((out.get("visual_spec") or {}).get("primary_visual") or {})
    cfg = dict(pv.get("chart_config") or {})
    cfg["stage"] = "flat"
    cfg["show_point_labels"] = True
    cfg["point_labels"] = True
    out["visual_spec"] = {
        **(out.get("visual_spec") or {}),
        "primary_visual": {**pv, "chart_config": cfg},
    }
    out["speaker_notes"] = (
        "v3 pass_02: full PDF hero narrative labels + stage=flat; "
        "pairing remains 66% top / 73% bottom. Hero type-scale chrome still B."
    )
    return out


def _fix_provision(s: dict) -> dict:
    out = deepcopy(s)
    out["layout_type"] = "stacked_bar_chart"
    out["packing_mode"] = "chart-led"
    c = dict(out.get("content") or {})
    c["subtitle"] = "$ in millions"
    # Short KPI stack so chart owns the canvas more (metrics still carried).
    c["key_stats"] = [
        {"label": "Q1'26 Total Provision", "value": "$1,251"},
        {"label": "Reserve Rate Q1'26", "value": "2.8%"},
    ]
    out["content"] = c
    pv = ((out.get("visual_spec") or {}).get("primary_visual") or {})
    cfg = dict(pv.get("chart_config") or {})
    # PDF palette: write-offs bright blue, reserve navy, above/below axis.
    cfg.update(
        {
            "series_names": ["Write-offs", "Reserve Build/(Release)"],
            "series_colors": ["#006FCF", "#00175A"],
            "allow_negative": True,
            "stacked": True,
            "show_point_labels": True,
            "point_labels": True,
            "stage": "flat",
        }
    )
    out["visual_spec"] = {
        **(out.get("visual_spec") or {}),
        "primary_visual": {
            **pv,
            "type": "stacked_bar_chart",
            "steps_or_data": [
                ["Quarter", "Write-offs", "Reserve Build/(Release)"],
                ["Q1'25", "1223", "-73"],
                ["Q2'25", "1183", "222"],
                ["Q3'25", "1162", "125"],
                ["Q4'25", "1273", "141"],
                ["Q1'26", "1275", "-24"],
            ],
            "chart_config": cfg,
        },
    }
    # Keep/explicity secondary reserve-rate table under chart if present.
    vs = out["visual_spec"]
    if not vs.get("secondary_visual"):
        vs["secondary_visual"] = {
            "type": "data_table",
            "steps_or_data": [
                ["", "Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"],
                ["Reserve Rate for Total Balances", "2.9%", "2.9%", "2.9%", "2.9%", "2.8%"],
            ],
        }
    out["speaker_notes"] = (
        "v3 pass_02: PDF cyan/navy palette; leaner key_stats; stage flat. "
        "F3 signed path retained from pass_01."
    )
    return out


def _fix_funding(s: dict) -> dict:
    out = deepcopy(s)
    out["layout_type"] = "multi_panel"
    out["packing_mode"] = "chart-led"
    out["content"] = {
        "subtitle": "$ in billions",
        "so_what": "92% FDIC insured at Q1'26",
        "key_stats": [{"label": "FDIC insured (Q1'26)", "value": "92%"}],
    }
    out["visual_spec"] = {
        "primary_visual": {
            "type": "multi_panel",
            "tiles": [
                {
                    "kind": "chart",
                    "chart_type": "stacked_bar_chart",
                    "label": "Funding Mix",
                    "top_total": "$210 · $219",
                    "badge": "",
                    "side_legend": [
                        {"label": "Deposits", "color": "#00175A"},
                        {"label": "Unsecured Funding**", "color": "#006FCF"},
                        {"label": "Short-term Funding / Card ABS*", "color": "#B8BFC9"},
                    ],
                    "steps_or_data": [
                        [
                            "Quarter",
                            "Deposits",
                            "Unsecured Funding**",
                            "Short-term Funding / Card ABS*",
                        ],
                        ["Q4'25", "72", "21", "7"],
                        ["Q1'26", "72", "21", "7"],
                    ],
                    "chart_config": {
                        "stacked": True,
                        "y_axis_min": 0,
                        "y_axis_max": 100,
                        "y_axis_ticks": [0, 25, 50, 75, 100],
                        "y_axis_unit": "%",
                        "force_ticks": True,
                        "show_point_labels": True,
                        "point_labels": True,
                        "stage": "flat",
                        "series_names": [
                            "Deposits",
                            "Unsecured Funding**",
                            "Short-term Funding / Card ABS*",
                        ],
                        "series_colors": ["#00175A", "#006FCF", "#B8BFC9"],
                    },
                },
                {
                    "kind": "chart",
                    "chart_type": "stacked_bar_chart",
                    "label": "Deposit Programs",
                    "top_total": "$151 · $157",
                    "badge": "",
                    "side_legend": [
                        {"label": "Savings and Direct CDs", "color": "#00175A"},
                        {"label": "Third Party CDs", "color": "#006FCF"},
                        {"label": "Third Party Sweep", "color": "#5B6B9A"},
                        {"label": "Checking", "color": "#B8BFC9"},
                    ],
                    "steps_or_data": [
                        [
                            "Quarter",
                            "Savings and Direct CDs",
                            "Third Party CDs",
                            "Third Party Sweep",
                            "Checking",
                        ],
                        ["Q4'25", "81", "10", "7", "2"],
                        ["Q1'26", "82", "10", "6", "2"],
                    ],
                    "chart_config": {
                        "stacked": True,
                        "y_axis_min": 0,
                        "y_axis_max": 100,
                        "y_axis_ticks": [0, 25, 50, 75, 100],
                        "y_axis_unit": "%",
                        "force_ticks": True,
                        "show_point_labels": True,
                        "point_labels": True,
                        "stage": "flat",
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
            ],
        }
    }
    out["speaker_notes"] = (
        "v3 pass_02: collapse Card ABS into Short-term Funding per PDF 3-band; "
        "side_legend uses exterior segment names; drop badges; stage flat."
    )
    return out


def main() -> None:
    base = json.loads(P01_HANDOFF.read_text(encoding="utf-8"))
    slides = base["slides"]
    assert len(slides) == 44, len(slides)

    slides[0] = _fix_cover(slides[0])
    slides[3] = _fix_line(slides[3])
    slides[5] = _fix_platinum(slides[5])
    slides[11] = _fix_acquisitions(slides[11])
    slides[14] = _fix_provision(slides[14])
    slides[18] = _fix_line(slides[18])
    slides[27] = _fix_funding(slides[27])

    for i, s in enumerate(slides, 1):
        s["slide_number"] = i

    base["slides"] = slides
    OUT.write_text(json.dumps(base, indent=2), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
    print(
        "touched:",
        {
            i: slides[i]["layout_type"]
            for i in (0, 3, 5, 11, 14, 18, 27)
        },
    )


if __name__ == "__main__":
    main()
