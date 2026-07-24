"""Pass 03 handoff — close last residual type-(A) items from pass_02.

Targets:
  * slide 11 Acquisitions — correct PDF top/bottom pairing
      TOP 66% Millennial/Gen-Z · BOTTOM 73% Fee-Paying (short labels)
  * slide 27 Funding — 2-tile multi_panel only; $ totals on tile labels
  * slide 05 Platinum — PDF-exact card titles/subtitles (cosmetic A)
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

PASS = Path(__file__).resolve().parent
SRC = PASS.parent / "pass_02" / "handoff.json"
OUT = PASS / "handoff.json"


def _fix_acquisitions(s: dict) -> dict:
    """PDF page 12: TOP 66% Millennial / Gen-Z; BOTTOM 73% Fee-Paying."""
    out = deepcopy(s)
    out["content"] = dict(out.get("content") or {})
    # Short hero labels so dual-hero layout can paint both cleanly.
    out["content"]["key_stats"] = [
        {
            "label": "Millennial / Gen-Z new accounts",
            "value": "66%",
        },
        {
            "label": "Fee-Paying Products* new accounts",
            "value": "73%",
        },
    ]
    # Keep subtitle clarifying the full metric wording.
    out["content"]["subtitle"] = (
        "Global Consumer New Accounts — Millennial/Gen-Z 66% (top) · "
        "Fee-Paying Products* 73% (bottom)"
    )
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
        "v2 pass_03: corrected hero pairing — 66% Millennial top, 73% Fee bottom (A)."
    )
    return out


def _fix_funding(s: dict) -> dict:
    """2 equal chart tiles only; encode $ totals into labels (no metric tiles)."""
    funding_mix = [
        ["Quarter", "Deposits", "Long-term Debt / Unsecured**", "Card ABS*", "Other / ST"],
        ["Q4'25", "72", "21", "6", "1"],
        ["Q1'26", "72", "21", "6", "1"],
    ]
    deposit_prog = [
        [
            "Quarter",
            "Savings and Direct CDs",
            "Third Party CDs",
            "Third Party Sweep",
            "Checking",
        ],
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
            "subtitle": "$ in billions · 92% FDIC insured at Q1'26",
            "so_what": "Customer Deposits remain ~72% of funding mix",
            # Keep key_stats sparse so multi_panel prefers 2 tall chart tiles.
            "key_stats": [
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
                        "label": "Funding Mix  ·  $210B (Q4'25) / $219B (Q1'26)",
                        "steps_or_data": funding_mix,
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
                        "label": "Deposit Programs  ·  $151B (Q4'25) / $157B (Q1'26)",
                        "steps_or_data": deposit_prog,
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
        },
        "disclosure": s.get("disclosure"),
        "speaker_notes": (
            "v2 pass_03: funding multi_panel reduced to 2 chart tiles; "
            "$210/$219 and $151/$157 encoded in tile labels (A density)."
        ),
    }


def _polish_platinum(s: dict) -> dict:
    """Tighten PDF-like card titles (A cosmetic). Charts already correct families."""
    out = deepcopy(s)
    pv = ((out.get("visual_spec") or {}).get("primary_visual") or {})
    tiles = list(pv.get("tiles") or [])
    fixed = []
    for t in tiles:
        t = dict(t)
        lab = (t.get("label") or "").lower()
        if "spend" in lab or t.get("chart_type") == "grouped_bar" and "retention" not in lab:
            if "retent" not in lab:
                t["label"] = "Accelerated U.S. Consumer Platinum Spend Growth"
        if "retent" in lab:
            t["label"] = "U.S. Consumer Platinum Retention (anniversary cohorts)"
        fixed.append(t)
    # If labels didn't match by keyword, force dual titles when 2 chart tiles.
    chart_tiles = [t for t in fixed if t.get("kind") == "chart"]
    if len(chart_tiles) >= 2:
        # First chart = spend, second = retention (pass_02 ordering).
        ordered = []
        charts_applied = 0
        for t in fixed:
            if t.get("kind") == "chart":
                t = dict(t)
                if charts_applied == 0:
                    t["label"] = "Accelerated U.S. Consumer Platinum Spend Growth"
                elif charts_applied == 1:
                    t["label"] = "U.S. Consumer Platinum Retention (anniversary cohorts)"
                charts_applied += 1
            ordered.append(t)
        fixed = ordered

    out["content"] = dict(out.get("content") or {})
    out["content"]["subtitle"] = (
        "Platinum Refresh · spend growth bars + retention 90–100% cohorts"
    )
    out["content"]["so_what"] = out["content"].get("so_what") or (
        "Refresh lifted spend ~+6 pp; retention higher across Jan–Mar cohorts"
    )
    out["visual_spec"] = {
        **(out.get("visual_spec") or {}),
        "primary_visual": {**pv, "tiles": fixed},
    }
    out["speaker_notes"] = (
        (out.get("speaker_notes") or "")
        + " | v2 pass_03: PDF-aligned platinum tile titles (A cosmetic)."
    ).strip(" |")
    return out


def transform(slides: list[dict]) -> list[dict]:
    s = deepcopy(slides)
    assert len(s) == 44
    s[5] = _polish_platinum(s[5])
    s[11] = _fix_acquisitions(s[11])
    s[27] = _fix_funding(s[27])
    for i, sl in enumerate(s):
        sl["slide_number"] = i + 1
    return s


def main() -> None:
    src = json.loads(SRC.read_text(encoding="utf-8"))
    slides = transform(src["slides"])
    handoff = {
        "presentation": {
            **(src.get("presentation") or {}),
            "subtitle": "Simulation handoff · v2 pass_03 · last residual A",
            "quality_flags": [
                "simulation",
                "amex_q1_2026",
                "pass_03",
                "v2_post_fixes",
                "type_a_tuning",
            ],
            "primary_goal": (
                "Close last residual A: acquisitions 66/73 pairing, funding 2-tile "
                "density, platinum card titles"
            ),
        },
        "slides": slides,
    }
    OUT.write_text(json.dumps(handoff, indent=2), encoding="utf-8")
    print(f"wrote {OUT} slides={len(slides)} bytes={OUT.stat().st_size}")
    for i in (5, 11, 27):
        sl = slides[i]
        ks = (sl.get("content") or {}).get("key_stats") or []
        tiles = ((sl.get("visual_spec") or {}).get("primary_visual") or {}).get("tiles")
        print(f"  [{i:02d}] {sl.get('layout_type')} · {sl.get('title')}")
        if ks:
            print("       key_stats:", [(k.get("value"), k.get("label")[:40]) for k in ks])
        if tiles:
            print("       tiles:", [(t.get("kind"), (t.get("label") or "")[:50]) for t in tiles])


if __name__ == "__main__":
    main()
