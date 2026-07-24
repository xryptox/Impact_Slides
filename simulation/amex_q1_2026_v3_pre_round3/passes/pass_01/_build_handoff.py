"""v3 pass_01 handoff — re-test round-2 fidelity features vs Amex Q1'26 PDF.

Starts from v2 final handoff (pass_03) and upgrades only the residual gap slides
with new handoff expressions that existed AFTER round-2 renderer work:

  * slide 00  brand_cover + brand_mark=seal_lockup (F6+ / R3)
  * slide 05  horizontal_bar retention + elbow/chevron callouts (F10+ / R2)
  * slide 14  signed stacked negatives kept explicit (F3)
  * slide 22/43 brand_mark=seal_lockup on dividers (R3)
  * slide 27  multi_panel tall-card slots: top_total / side_legend / badge (F11+)

No production renderer edits — handoff-only.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # simulation/
# Worktree root is parents[4]? Path: simulation/amex_q1_2026/passes/pass_01
# parents[0]=pass_01, [1]=passes, [2]=amex_q1_2026, [3]=simulation, [4]=repo
REPO = Path(__file__).resolve().parents[4]
V2_HANDOFF = (
    REPO
    / "simulation"
    / "amex_q1_2026_v2_pre_round2"
    / "passes"
    / "pass_03"
    / "handoff.json"
)
OUT = Path(__file__).resolve().parent / "handoff.json"


def _fix_cover(s: dict) -> dict:
    """Use brand_cover with named seal lockup — load path now permits it as slide 1."""
    out = deepcopy(s)
    out["layout_type"] = "brand_cover"
    out["packing_mode"] = "cover-led"
    out["title"] = "American Express Earnings Conference Call"
    out["section"] = "Cover"
    c = dict(out.get("content") or {})
    c["headline"] = "American Express Earnings Conference Call"
    c["subtitle"] = "Q1'26  ·  APRIL 23, 2026"
    c["brand_tone"] = "two-tone"
    c["brand_mark"] = "seal_lockup"
    # Drop generic inline SVG so named pack path is exercised.
    c.pop("brand_mark_svg", None)
    c.setdefault("bullets", [])
    c.setdefault("key_stats", [{"label": "Date", "value": "APRIL 23, 2026"}])
    c.setdefault("so_what", "")
    out["content"] = c
    out["speaker_notes"] = (
        "v3 pass_01: brand_cover + brand_mark=seal_lockup as slide 1 "
        "(round-2 F6+ load path + R3 named seal)."
    )
    return out


def _fix_divider(s: dict, *, title: str | None = None) -> dict:
    out = deepcopy(s)
    out["layout_type"] = "brand_divider"
    c = dict(out.get("content") or {})
    c["brand_tone"] = "two-tone"
    c["brand_mark"] = "seal_lockup"
    c.pop("brand_mark_svg", None)
    if title:
        out["title"] = title
        c.setdefault("subtitle", title)
    out["content"] = c
    out["speaker_notes"] = (
        (out.get("speaker_notes") or "")
        + " | v3 pass_01: brand_mark=seal_lockup (R3 named asset)."
    )
    return out


def _fix_platinum(s: dict) -> dict:
    """Dual-card: spend grouped bars + horizontal anniversary retention + callouts."""
    out = deepcopy(s)
    out["layout_type"] = "multi_panel"
    out["packing_mode"] = "chart-led"
    out["title"] = "U.S. Consumer Platinum Performance"
    out["content"] = {
        "subtitle": "Platinum Refresh · spend growth bars + retention 90–100% cohorts",
        "so_what": (
            "Refresh cohort shows ~+6 pp spend acceleration with stable "
            "anniversary retention"
        ),
        "key_stats": [{"label": "Refresh lift (spend)", "value": "+~6 pp"}],
    }
    out["visual_spec"] = {
        "primary_visual": {
            "type": "multi_panel",
            "tiles": [
                {
                    "kind": "chart",
                    "chart_type": "grouped_bar_chart",
                    "label": "Accelerated U.S. Consumer Platinum Spend Growth",
                    "top_total": "+~6 pp",
                    "badge": "Refresh",
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
                        "y_axis_max": 15,
                        "y_axis_ticks": [0, 5, 10, 15],
                        "force_ticks": True,
                        "y_axis_unit": "%",
                        "show_point_labels": True,
                        "point_labels": True,
                        "series_names": ["Spend growth"],
                        "series_colors": ["#00175A"],
                        "callouts": [
                            {
                                "type": "elbow_arrow",
                                "from": 0,
                                "to": 4,
                                "value": 10,
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
                    "label": "U.S. Consumer Platinum Retention (anniversary cohorts)",
                    "top_total": "90–100%",
                    "badge": "Anniversary",
                    "side_legend": [
                        {"label": "2025 (pre-refresh year)", "color": "#006FCF"},
                        {"label": "2026 (post-refresh)", "color": "#00175A"},
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
                        "series_names": [
                            "2025 (pre-refresh year)",
                            "2026 (post-refresh)",
                        ],
                        "series_colors": ["#006FCF", "#00175A"],
                    },
                },
            ],
        }
    }
    out["speaker_notes"] = (
        "v3 pass_01: horizontal_bar_chart retention + elbow/chevron callouts "
        "+ tall-card chrome (round-2 F10+/R2/F11+)."
    )
    return out


def _fix_provision(s: dict) -> dict:
    """Keep signed reserve-release series explicit for below-axis stack geometry."""
    out = deepcopy(s)
    out["layout_type"] = "stacked_bar_chart"
    out["packing_mode"] = "chart-led"
    c = dict(out.get("content") or {})
    c["subtitle"] = "$ in millions · write-offs above / reserve release below axis"
    out["content"] = c
    pv = ((out.get("visual_spec") or {}).get("primary_visual") or {})
    cfg = dict(pv.get("chart_config") or {})
    cfg.update(
        {
            "series_names": ["Write-offs", "Reserve Build/(Release)"],
            "series_colors": ["#00175A", "#006FCF"],
            "allow_negative": True,
            "stacked": True,
            "show_point_labels": True,
            "point_labels": True,
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
    out["speaker_notes"] = (
        "v3 pass_01: signed stacked reserve release re-tested on current "
        "renderer negative-sign load path (F3 after round-2)."
    )
    return out


def _fix_funding(s: dict) -> dict:
    """Engage IR dual tall-card slots: top_total + side_legend + badge."""
    out = deepcopy(s)
    out["layout_type"] = "multi_panel"
    out["packing_mode"] = "chart-led"
    out["content"] = {
        "subtitle": "$ in billions · 92% FDIC insured at Q1'26",
        "so_what": "Customer Deposits remain ~72% of funding mix",
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
                    "top_total": "$210B / $219B",
                    "badge": "Funding",
                    "side_legend": [
                        {"label": "Deposits", "color": "#00175A"},
                        {"label": "Long-term Debt / Unsecured**", "color": "#006FCF"},
                        {"label": "Card ABS*", "color": "#5B6B9A"},
                        {"label": "Other / ST", "color": "#B8BFC9"},
                    ],
                    "steps_or_data": [
                        [
                            "Quarter",
                            "Deposits",
                            "Long-term Debt / Unsecured**",
                            "Card ABS*",
                            "Other / ST",
                        ],
                        ["Q4'25", "72", "21", "6", "1"],
                        ["Q1'26", "72", "21", "6", "1"],
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
                    "top_total": "$151B / $157B",
                    "badge": "Deposits",
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
        "v3 pass_01: multi_panel tall-card top_total + side_legend + badge (F11+)."
    )
    return out


def main() -> None:
    base = json.loads(V2_HANDOFF.read_text(encoding="utf-8"))
    slides = base["slides"]
    assert len(slides) == 44, len(slides)

    slides[0] = _fix_cover(slides[0])
    slides[5] = _fix_platinum(slides[5])
    slides[14] = _fix_provision(slides[14])
    slides[22] = _fix_divider(slides[22], title=slides[22].get("title") or "Appendix")
    slides[27] = _fix_funding(slides[27])
    slides[43] = _fix_divider(
        slides[43], title=slides[43].get("title") or "American Express"
    )

    # Ensure contiguous slide_number 1..44
    for i, s in enumerate(slides, 1):
        s["slide_number"] = i

    base["slides"] = slides
    # Tag presentation for this simulation run
    pres = dict(base.get("presentation") or {})
    pres.setdefault("title", "American Express Earnings Conference Call Q1'26")
    pres["chrome_level"] = pres.get("chrome_level") or "minimal"
    base["presentation"] = pres

    OUT.write_text(json.dumps(base, indent=2), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
    print(
        "upgraded slides:",
        {
            0: slides[0]["layout_type"],
            5: slides[5]["layout_type"],
            14: slides[14]["layout_type"],
            22: slides[22]["layout_type"],
            27: slides[27]["layout_type"],
            43: slides[43]["layout_type"],
        },
    )


if __name__ == "__main__":
    main()
