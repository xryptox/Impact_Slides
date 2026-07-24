"""v3 pass_03 handoff — pure-(A) tall multi_panel re-engagement + residual probes.

Starts from pass_02 handoff. Handoff-only; no renderer edits.

Targets:
  * slide 05  Re-enable gl-tile-tall via non-empty top_total + side_legend while
              KEEP PDF card titles. Left: top_total '+~6 pp'; badge ''; right:
              top_total ''; badge ''; side_legend year series + colors.
              Callouts retained (band/elbow/chevron).
  * slide 14  Probe secondary_visual reserve-rate table under stacked_bar:
              if renderer only attaches secondary on line_chart → B confirmed.
              Also try packing_mode chart-led + drop residual KPI if needed.
  * slide 27  Already has top_total+side_legend tall chrome; minor: denser
              so_what/legend alignment copy only.
  * slide 00  One last cover content micro-tweak (title/deck match) then stop
              if stagnant.
  * slide 11  Try packing_mode metric-led with giant key_stats only (hero
              type-scale residual likely still B).
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
P02_HANDOFF = (
    REPO
    / "simulation"
    / "amex_q1_2026"
    / "passes"
    / "pass_02"
    / "handoff.json"
)
OUT = Path(__file__).resolve().parent / "handoff.json"


def _fix_cover(s: dict) -> dict:
    out = deepcopy(s)
    out["layout_type"] = "brand_cover"
    # PDF: large left-legible white title stack + April date + large seal WR.
    out["title"] = "American Express\nEarnings Conference Call"
    c = dict(out.get("content") or {})
    c["headline"] = "American Express Earnings Conference Call"
    c["subtitle"] = "Q1'26  ·  APRIL 23, 2026"
    c["brand_tone"] = "two-tone"
    c["brand_mark"] = "seal_lockup"
    c.pop("brand_mark_svg", None)
    c["key_stats"] = []
    out["content"] = c
    out["speaker_notes"] = (
        "v3 pass_03: drop Q1'26 from title line into subtitle pack; empty "
        "key_stats. Seal placement/Centurion watermark still B if paint fails."
    )
    return out


def _fix_platinum(s: dict) -> dict:
    """Re-engage gl-tile-tall without abandoning PDF card titles."""
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
                    "label": "Spend Growth is Accelerating",
                    # Non-empty top_total engages gl-tile-tall (recipes.py).
                    "top_total": "+ ~6 pp",
                    "badge": "",
                    "side_legend": [
                        {
                            "label": "Spend growth %",
                            "color": "#00175A",
                        }
                    ],
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
                    "label": "Retention Rates Remain High and Very Stable",
                    "top_total": "94–97%",
                    "badge": "",
                    "side_legend": [
                        {"label": "2025", "color": "#006FCF"},
                        {"label": "2026", "color": "#00175A"},
                    ],
                    "steps_or_data": [
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
        "v3 pass_03: re-engage gl-tile-tall via top_total+side_legend while "
        "keeping PDF card titles. Anniversary 90–100 + inside-year labels "
        "still B if paint fails."
    )
    return out


def _fix_provision(s: dict) -> dict:
    """Keep signed stack; lean KPI; secondary reserve-rate as B probe."""
    out = deepcopy(s)
    out["layout_type"] = "stacked_bar_chart"
    out["packing_mode"] = "chart-led"
    c = dict(out.get("content") or {})
    c["subtitle"] = "$ in millions"
    # Even leaner: one headline chip; reserve rate lives in secondary attempt.
    c["key_stats"] = [
        {"label": "Total Provision Expense", "value": "$1,251"},
    ]
    out["content"] = c
    pv = ((out.get("visual_spec") or {}).get("primary_visual") or {})
    cfg = dict(pv.get("chart_config") or {})
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
        # recipes.render_chart only attaches secondary when layout==line_chart.
        # Keep payload so if that gate loosens it works; otherwise notes = B.
        "secondary_visual": {
            "type": "data_table",
            "steps_or_data": [
                ["", "Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"],
                [
                    "Reserve Rate for Total Balances",
                    "2.9%",
                    "2.9%",
                    "2.9%",
                    "2.9%",
                    "2.8%",
                ],
            ],
        },
    }
    out["speaker_notes"] = (
        "v3 pass_03: single KPI chip; secondary_visual reserve-rate table "
        "attached for B-probe (stacked_bar gate)."
    )
    return out


def _fix_acquisitions(s: dict) -> dict:
    out = deepcopy(s)
    out["packing_mode"] = "metric-led"
    out["content"] = {
        "subtitle": "",
        "so_what": "",
        "key_stats": [
            {
                "label": (
                    "of Global Consumer New Accounts Acquired "
                    "from Millennial and Gen Z Customers"
                ),
                "value": "66%",
            },
            {
                "label": "of Global New Accounts Acquired on Fee-Paying Products*",
                "value": "73%",
            },
        ],
    }
    # Keep a quiet line chart if present; hero remains metric-led.
    pv = ((out.get("visual_spec") or {}).get("primary_visual") or {})
    cfg = dict(pv.get("chart_config") or {})
    cfg["stage"] = "flat"
    out["visual_spec"] = {
        **(out.get("visual_spec") or {}),
        "primary_visual": {**pv, "chart_config": cfg},
    }
    out["speaker_notes"] = (
        "v3 pass_03: metric-led packing + PDF ownership prose on 66%/73%. "
        "Hero dual giant type-scale still expected B."
    )
    return out


def _fix_funding(s: dict) -> dict:
    out = deepcopy(s)
    # Tall already engaged; polish titles to PDF casing and drop chart point labels
    # noise if stacked percentages should read cleaner.
    vs = out.get("visual_spec") or {}
    pv = vs.get("primary_visual") or {}
    tiles = list(pv.get("tiles") or [])
    for t in tiles:
        cfg = dict(t.get("chart_config") or {})
        cfg["show_point_labels"] = True
        cfg["point_labels"] = True
        cfg["stage"] = "flat"
        t["chart_config"] = cfg
        t["badge"] = ""
    if tiles:
        tiles[0]["label"] = "Funding Mix"
        tiles[0]["top_total"] = "$210B  ·  $219B"
        tiles[1]["label"] = "Deposit Programs"
        tiles[1]["top_total"] = "$151B  ·  $157B"
    out["visual_spec"] = {
        "primary_visual": {**pv, "type": "multi_panel", "tiles": tiles}
    }
    c = dict(out.get("content") or {})
    c["subtitle"] = "$ in billions"
    c["so_what"] = "92% of deposits FDIC insured*"
    out["content"] = c
    out["speaker_notes"] = (
        "v3 pass_03: B-suffix totals; FDIC so_what; tall chrome retained."
    )
    return out


def main() -> None:
    base = json.loads(P02_HANDOFF.read_text(encoding="utf-8"))
    slides = base["slides"]
    assert len(slides) == 44, len(slides)

    slides[0] = _fix_cover(slides[0])
    slides[5] = _fix_platinum(slides[5])
    slides[11] = _fix_acquisitions(slides[11])
    slides[14] = _fix_provision(slides[14])
    slides[27] = _fix_funding(slides[27])

    for i, s in enumerate(slides, 1):
        s["slide_number"] = i

    base["slides"] = slides
    OUT.write_text(json.dumps(base, indent=2), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
    print(
        "touched:",
        {i: slides[i]["layout_type"] for i in (0, 5, 11, 14, 27)},
    )


if __name__ == "__main__":
    main()
