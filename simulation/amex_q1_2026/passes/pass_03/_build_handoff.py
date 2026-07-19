"""Author pass_03 handoff — residual type-(A) + SVG chart path probe.

Pass_03 intent (vs pass_02):
1. Keep pass_02 content/layout wins (freeform highlights/guidance/variance, full tables,
   true-negative provision stack, chart_config axis/name/annotation/style fields).
2. Line-chart house style: pin y_axis_ticks 0/5/10/15 and y_axis_unit "%" so the SVG
   painter (enabled via CLI --suppress-feature charts) can hit IR 0–15% rails.
3. Expense Performance: surface floating 44.7% VCE-of-Revenue as key_stats (content
   probe; pill inset placement remains B).
4. New Acquisitions: keep 66%/73% key_stats order matching PDF hero rail (fee-paying
   66% then Millennial/Gen-Z 73%).
5. Do NOT claim Chart.js was fixed — SVG path is a deliberate feature-gate experiment
   to separate "chart_config works on SVG" from "Chart.js ignores chart_config" (B).

Changes inherited from pass_02 (handoff tuning):
1. Business Highlights → freeform_grid single-column bullets (drop split chrome + so_what).
2. Line charts: y_axis_min/max 0–15, series_names/colors, annotation callouts, drop extra KPI chips.
3. New Acquisitions → freeform_grid chart slot is not supported; use stacked_bar + large key_stats only
   and try freeform with metric_stack for hero % (no embedded chart in freeform) — dual attempt via
   stacked_bar keep + oversized key_stats (layout stays chart-led).
4. Guidance → freeform_grid two-metric centered card, no invented so_what.
5. Total Provision → true negative reserve release values.
6. Expense performance filled from PDF text; appendix / annex / variance filled from slides.json raw_text.
7. Cover subtitle clean date; strip narrative so_what on IR pure-data slides.
8. FLS pages → freeform single-column denser bullets.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent / "handoff.json"
EXTRACTED = Path(__file__).resolve().parents[2] / "extracted" / "slides.json"

THEME = {
    "--color-bg": "#ffffff",
    "--color-surface": "#ffffff",
    "--color-ink": "#001B4D",
    "--color-ink-muted": "#3A4A6B",
    "--color-accent": "#006FCF",
    "--color-accent-2": "#00175A",
    "--color-border": "#E0E3EB",
    "--color-stage-bg": "#00175A",
}


def ir_pct_line_cfg(extra=None):
    """IR billings-style % line defaults (SVG painter honors these; Chart.js may not)."""
    cfg = {
        "y_axis_min": 0,
        "y_axis_max": 15,
        "y_axis_ticks": [0, 5, 10, 15],
        "y_axis_unit": "%",
        "y_axis_label": "%",
        "y_label": "%",  # alternate key seen in some handoffs
        "gridlines": True,
    }
    if extra:
        cfg.update(extra)
    return cfg


def line_points(labels, values, series2=None):
    pts = []
    for i, lab in enumerate(labels):
        p = {"label": lab, "value": values[i]}
        if series2 is not None:
            p["series_2"] = series2[i]
        pts.append(p)
    return pts


def bar_matrix(header, rows):
    return [header] + rows


def freeform_bullets(title, section, bullets, *, subtitle="", disclosure=None, notes=""):
    slide = {
        "slide_number": 0,
        "layout_type": "split_text_visual",
        "packing_mode": "argument-led",
        "title": title,
        "section": section,
        "content": {
            "headline": title,
            "subtitle": subtitle,
            "bullets": bullets,
            "body_text": "",
            "so_what": "",
            "key_stats": [],
        },
        "visual_spec": {
            "grid": {
                "template_areas": ["main"],
                "columns": "1fr",
                "rows": "1fr",
                "gap": "16px",
                "slots": {"main": {"kind": "bullets"}},
            }
        },
        "speaker_notes": notes or title,
    }
    if disclosure:
        slide["disclosure"] = disclosure
    return slide


def freeform_metrics(title, section, stats, *, subtitle="", disclosure=None, notes=""):
    slide = {
        "slide_number": 0,
        "layout_type": "metric_dashboard",
        "packing_mode": "stat-led",
        "title": title,
        "section": section,
        "content": {
            "headline": title,
            "subtitle": subtitle,
            "key_stats": stats,
            "bullets": [],
            "so_what": "",
        },
        "visual_spec": {
            "grid": {
                "template_areas": ["metrics"],
                "columns": "1fr",
                "rows": "1fr",
                "gap": "24px",
                "slots": {"metrics": {"kind": "metric_stack"}},
            }
        },
        "speaker_notes": notes or title,
    }
    if disclosure:
        slide["disclosure"] = disclosure
    return slide


def freeform_acquisitions_hero(title, section, stats, chart_note, disclosure=None):
    """Hero KPI stack + supporting proof bullets (freeform cannot embed chart)."""
    slide = {
        "slide_number": 0,
        "layout_type": "metric_dashboard",
        "packing_mode": "stat-led",
        "title": title,
        "section": section,
        "content": {
            "headline": title,
            "subtitle": "Proprietary New Cards Acquired (in millions)",
            "key_stats": stats,
            "bullets": [
                chart_note,
                "Stacked NCA by UCS / Commercial / ICS — chart geometry is B-gap if not co-located",
            ],
            "so_what": "",
            "supporting_points": [
                "Q1'26 total proprietary NCA ≈ 3.1M",
                "UCS / CS / ICS stack: ~1.3 / 0.8 / 1.0",
            ],
        },
        "visual_spec": {
            "grid": {
                "template_areas": ["kpis kpis", "note note"],
                "columns": "1fr 1fr",
                "rows": "auto auto",
                "gap": "28px",
                "slots": {
                    "kpis": {"kind": "metric_stack"},
                    "note": {"kind": "proof"},
                },
            }
        },
        "speaker_notes": "Pass_02 hero KPI attempt; stacked chart remains on separate layout in other variants.",
    }
    if disclosure:
        slide["disclosure"] = disclosure
    return slide


def bullets_from_raw(raw: str) -> list[str]:
    if not raw:
        return []
    # Prefer explicit bullet lines
    lines = []
    for ln in raw.splitlines():
        t = ln.strip().lstrip("•").strip()
        if not t:
            continue
        if t.startswith("•"):
            t = t[1:].strip()
        lines.append(t)
    # Reconstruct.pdf often puts • on own line then text on next
    joined: list[str] = []
    i = 0
    raw_lines = [ln.strip() for ln in raw.splitlines()]
    # Parse "•" then following paragraph until next bullet-ish marker
    buf = []
    collecting = False
    body_start = False
    for ln in raw_lines:
        if ln in {"•", "·", "-"}:
            if buf:
                joined.append(" ".join(buf))
                buf = []
            collecting = True
            body_start = True
            continue
        if ln.startswith("•"):
            if buf:
                joined.append(" ".join(buf))
            buf = [ln.lstrip("•").strip()]
            collecting = True
            body_start = True
            continue
        # Skip recurring slide titles / page numbers
        if re.fullmatch(r"\d{1,2}", ln):
            continue
        if "Additional Commentary" in ln or ln.startswith("Annex "):
            continue
        if collecting:
            # stop if another section header style all-caps short
            buf.append(ln)
    if buf:
        joined.append(" ".join(buf))
    # Fallback: split on · patterns "Label: text"
    if len(joined) < 2:
        chunks = re.split(r"(?=\b[A-Z][^:]{3,40}:\s)", raw.replace("\n", " "))
        joined = [c.strip() for c in chunks if ":" in c and len(c.strip()) > 20]
    # Clean whitespace
    out = []
    for j in joined:
        j = re.sub(r"\s+", " ", j).strip()
        if len(j) > 12:
            out.append(j)
    return out[:12]


def main():
    slides_meta = json.loads(EXTRACTED.read_text(encoding="utf-8"))
    by_idx = {s["slide_index"]: s for s in slides_meta["slides"]}

    Q = ["Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"]
    slides = []

    def add(s):
        s = dict(s)
        s["slide_number"] = len(slides) + 1
        slides.append(s)

    # ---------- 1 Cover ----------
    add(
        {
            "layout_type": "title_or_opening",
            "packing_mode": "cover-led",
            "title": "American Express Earnings Conference Call",
            "section": "Cover",
            "content": {
                "headline": "American Express Earnings Conference Call",
                "subtitle": "Q1'26  ·  APRIL 23, 2026",
                "bullets": [],
                "key_stats": [],
                "body_text": "",
                "so_what": "",
                "narrative_bridge": "",
            },
            "speaker_notes": "Cover — Amex Q1 2026. Seal watermark remains capability gap (B).",
        }
    )

    # ---------- 2 Business Highlights (A: freeform single column) ----------
    bh = by_idx[1].get("bullets") or []
    if len(bh) < 5:
        bh = [
            "Q1 2026 revenue growth of 11%, and EPS of $4.28, up 18% YoY",
            "Named the Official Payments Partner of the NFL and announced a multi-year partnership extension with the NBA across league platforms, including the WNBA",
            "Launched the American Express Graphite Business Cash Unlimited Card, kicking off a major expansion of integrated solutions for businesses of all sizes",
            "Announced the Amex Agentic Commerce Experiences developer kit and industry-first Amex Agent Purchase Protection",
            "Unveiled next phase of the Resy dining platform, including the planned integration of Resy and Tock venue networks",
            "Opened Las Vegas Sidecar and New Delhi Centurion Lounge and announced upcoming new or expanded spaces in three other locations",
            "Ranked #4 on Great Place to Work 2026 list of the 100 Best Companies to Work For in the U.S.",
        ]
    add(
        freeform_bullets(
            "Business Highlights",
            "Highlights",
            bh,
            disclosure={
                "pattern": "detail",
                "panels": [
                    {
                        "title": "Statistical Tables reference",
                        "body": (
                            "Refer to the Statistical Tables for Q1 2026 on "
                            "ir.americanexpress.com for defined terms."
                        ),
                    }
                ],
            },
            notes="Freeform single-column bullets; inline bold spans still B-gap.",
        )
    )

    # ---------- 3 Summary Financial Performance ----------
    add(
        {
            "layout_type": "data_table",
            "packing_mode": "stat-led",
            "title": "Summary Financial Performance",
            "section": "Financials",
            "content": {
                "subtitle": "$ in millions, except per share amounts; % Increase/(decrease) vs. Prior year",
                "so_what": "",
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "data_table",
                    "steps_or_data": [
                        ["Metric", "Q1'26", "Q1'25", "YoY% Inc/(Dec)"],
                        [
                            "Total Revenues Net of Interest Expense",
                            "$18,907",
                            "$16,967",
                            "11%",
                        ],
                        ["FX-Adjusted*", "—", "$17,210", "10%"],
                        ["Net Income", "$2,971", "$2,584", "15%"],
                        ["Diluted EPS**", "$4.28", "$3.64", "18%"],
                        ["Average Diluted Shares Outstanding", "686", "702", "(2%)"],
                    ],
                }
            },
            "disclosure": {
                "pattern": "detail",
                "panels": [
                    {
                        "title": "Non-GAAP / footnotes",
                        "body": (
                            "* Total Revenues Net of Interest Expense adjusted for FX is non-GAAP. "
                            "** Attributable to common shareholders."
                        ),
                    }
                ],
            },
            "speaker_notes": "Row-grid table; pill columns remain B-gap.",
        }
    )

    # ---------- 4 Total Billed Business ----------
    add(
        {
            "layout_type": "line_chart",
            "packing_mode": "chart-led",
            "title": "Total Billed Business",
            "section": "Billings",
            "content": {
                "subtitle": "% Increase/(decrease) vs. Prior year (FX-adjusted unless otherwise stated)",
                "so_what": "",
                "key_stats": [],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(Q, [6, 7, 8, 8, 9], [6, 7, 9, 9, 10]),
                    "chart_config": {
                        "series_names": ["FX-adjusted", "Reported"],
                        "series_styles": ["solid", "dashed"],
                        "series_colors": ["#00175A", "#8A93A6"],
                        "y_axis_min": 0,
                        "y_axis_max": 15,
                        "y_axis_ticks": [0, 5, 10, 15],
                        "y_axis_unit": "%",
                        "y_axis_label": "%",
                        "y_label": "%",
                        "annotation": {
                            "text": "Leap Year Approx. (1%)",
                            "x": 420,
                            "y": 90,
                        },
                    },
                },
                "secondary_visual": {
                    "type": "data_table",
                    "steps_or_data": [
                        ["", "Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"],
                        ["G&S", "7%", "7%", "9%", "8%", "8%"],
                        ["T&E", "6%", "5%", "8%", "8%", "9%"],
                    ],
                },
            },
            "speaker_notes": "A: axis 0–15 + ticks + unit + names/colors/annotation for SVG path; Chart.js house style remains B if enabled.",
        }
    )

    # ---------- 5 UCS Billed ----------
    add(
        {
            "layout_type": "line_chart",
            "packing_mode": "chart-led",
            "title": "U.S. Consumer Services Billed Business",
            "section": "Billings",
            "content": {
                "subtitle": "% Increase/(decrease) vs. Prior year",
                "so_what": "",
                "key_stats": [],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(Q, [7, 7, 9, 9, 10]),
                    "chart_config": {
                        "series_names": ["UCS Billings"],
                        "series_colors": ["#00175A"],
                        "y_axis_min": 0,
                        "y_axis_max": 15,
                        "y_axis_ticks": [0, 5, 10, 15],
                        "y_axis_unit": "%",
                        "y_axis_label": "%",
                        "y_label": "%",
                    },
                },
                "secondary_visual": {
                    "type": "data_table",
                    "steps_or_data": [
                        [
                            "Q1'26",
                            "Gen-Z",
                            "Millennials",
                            "Gen-X",
                            "Baby Boomer +",
                            "Total",
                        ],
                        ["YoY", "38%", "13%", "8%", "4%", "10%"],
                        ["% of Total", "6%", "30%", "36%", "28%", "100%"],
                    ],
                },
            },
            "speaker_notes": "Line + generation mix; chips removed.",
        }
    )

    # ---------- 6 Platinum dual ----------
    add(
        {
            "layout_type": "dual_chart",
            "packing_mode": "chart-led",
            "title": "U.S. Consumer Platinum Performance",
            "section": "US Consumer",
            "content": {
                "subtitle": "Spend Growth is Accelerating · Retention Rates Remain High and Very Stable",
                "so_what": "",
                "key_stats": [
                    {"label": "Retention lift callout", "value": "+~6 pp"},
                ],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(Q, [7, 7, 9, 9, 10]),
                    "chart_config": {
                        "series_names": ["Spend growth"],
                        "y_axis_min": 0,
                        "y_axis_max": 15,
                        "y_axis_ticks": [0, 5, 10, 15],
                        "y_axis_unit": "%",
                        "y_axis_label": "%",
                    },
                },
                "secondary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(
                        ["January", "February", "March"],
                        [94, 95, 95],
                        [96, 97, 97],
                    ),
                    "chart_config": {
                        "series_names": ["Pre-refresh", "Post-refresh"],
                        "y_axis_min": 90,
                        "y_axis_max": 100,
                    },
                },
            },
            "speaker_notes": "y 90–100 attempt for retention panel; broken-axis still B.",
        }
    )

    # ---------- 7 Membership engagement ----------
    add(
        {
            "layout_type": "three_column_comparison",
            "packing_mode": "stat-led",
            "title": "U.S. Consumer: Membership Model Engagement",
            "section": "US Consumer",
            "content": {
                "subtitle": "Card Member Spend Growth Rates; % Increase/(decrease) vs. Prior year",
                "bullets": [
                    "Lodging: Fine Hotels + Resorts / Hotel Collection 50% vs UCS Lodging 5% · 10x",
                    "Restaurants: U.S. Resy Restaurants 20% vs UCS Restaurants 10% · 2x",
                    "Airlines: Member Airfares 21% vs UCS Airlines 11% · 2x",
                ],
                "key_stats": [
                    {"label": "Lodging FHR+THC", "value": "50%"},
                    {"label": "UCS Lodging", "value": "5%"},
                    {"label": "Multiplier", "value": "10x"},
                    {"label": "Resy Restaurants", "value": "20%"},
                    {"label": "UCS Restaurants", "value": "10%"},
                    {"label": "Member Airfares", "value": "21%"},
                ],
                "so_what": "",
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "comparison_grid",
                    "steps_or_data": [
                        "Lodging · 50% vs 5% · 10x",
                        "Restaurants · 20% vs 10% · 2x",
                        "Airlines · 21% vs 11% · 2x",
                    ],
                }
            },
            "disclosure": {
                "pattern": "detail",
                "panels": [
                    {
                        "title": "Member Airfares footnote",
                        "body": (
                            "Member Airfares offers Platinum and Centurion Card Members reduced "
                            "fares on select premium international and domestic tickets booked "
                            "through American Express Travel."
                        ),
                    }
                ],
            },
            "speaker_notes": "Three category multipliers.",
        }
    )

    # ---------- 8 Proprietary lodging ----------
    add(
        {
            "layout_type": "metric_row_with_breakdown",
            "packing_mode": "stat-led",
            "title": "Membership Model Engagement: Proprietary Lodging Assets",
            "section": "US Consumer",
            "content": {
                "subtitle": "Lodging Spend Growth · Fine Hotels + Resorts and The Hotel Collection",
                "key_stats": [
                    {"label": "Premium Global Properties", "value": "3,400+"},
                    {"label": "New Properties Selected (2026)", "value": "300+"},
                    {"label": "Avg CM Value 2-Night Stay", "value": "$550"},
                    {"label": "Annual U.S. Plat Statement Credit", "value": "$600"},
                    {"label": "Partner-Funded", "value": "100%"},
                    {"label": "FHR+THC YoY", "value": "50%"},
                    {"label": "UCS Lodging YoY", "value": "5%"},
                    {"label": "Multiplier", "value": "10x"},
                ],
                "bullets": [
                    "Program Benefits: Early check-in, Late check-out, Room upgrades, "
                    "Complimentary breakfast and Wi-Fi, Experience credits",
                    "300+ new properties selected out of ~1,400 applications in 2026",
                ],
                "so_what": "",
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(Q, [40, 42, 45, 48, 50], [5, 5, 5, 5, 5]),
                    "chart_config": {
                        "series_names": ["FHR+THC", "UCS Lodging"],
                        "series_colors": ["#00175A", "#8A93A6"],
                        "y_axis_min": 0,
                        "y_axis_max": 60,
                    },
                }
            },
            "speaker_notes": "KPI + dual line lodging differential.",
        }
    )

    # ---------- 9 Commercial ----------
    add(
        {
            "layout_type": "line_chart",
            "packing_mode": "chart-led",
            "title": "Commercial Services Billed Business",
            "section": "Billings",
            "content": {
                "subtitle": "% Increase/(decrease) vs. Prior year (FX-adjusted)",
                "so_what": "",
                "key_stats": [],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(Q, [2, 2, 4, 3, 4]),
                    "chart_config": {
                        "series_names": ["Commercial FX-adj"],
                        "y_axis_min": 0,
                        "y_axis_max": 15,
                        "y_axis_ticks": [0, 5, 10, 15],
                        "y_axis_unit": "%",
                        "y_axis_label": "%",
                    },
                },
                "secondary_visual": {
                    "type": "data_table",
                    "steps_or_data": [
                        ["Q1'26", "U.S. SME", "U.S. Large & Global Corp.", "Total"],
                        ["YoY", "4%", "4%", "4%"],
                        ["% of Total", "81%", "19%", "100%"],
                    ],
                },
            },
            "speaker_notes": "Commercial line + mix.",
        }
    )

    # ---------- 10 ICS ----------
    add(
        {
            "layout_type": "line_chart",
            "packing_mode": "chart-led",
            "title": "International Card Services Billed Business",
            "section": "Billings",
            "content": {
                "subtitle": "% Increase/(decrease) vs. Prior year (FX-adjusted unless otherwise stated)",
                "so_what": "",
                "key_stats": [],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(
                        Q, [13, 12, 13, 12, 13], [9, 15, 14, 17, 20]
                    ),
                    "chart_config": {
                        "series_names": ["FX-adjusted", "Reported"],
                        "series_styles": ["solid", "dashed"],
                        "series_colors": ["#00175A", "#8A93A6"],
                        "y_axis_min": 0,
                        "y_axis_max": 25,
                        "annotation": {"text": "Reported", "x": 520, "y": 70},
                    },
                },
                "secondary_visual": {
                    "type": "data_table",
                    "steps_or_data": [
                        ["Q1'26", "Intl Consumer", "Intl SME & Large Corp.", "Total"],
                        ["YoY", "13%", "12%", "13%"],
                        ["% of Total", "65%", "35%", "100%"],
                    ],
                },
            },
            "speaker_notes": "Dual series ICS.",
        }
    )

    # ---------- 11 Transaction Growth ----------
    add(
        {
            "layout_type": "line_chart",
            "packing_mode": "chart-led",
            "title": "Transaction Growth",
            "section": "Volumes",
            "content": {
                "subtitle": "% Increase/(decrease) vs. Prior year",
                "so_what": "",
                "key_stats": [],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(Q, [9, 9, 10, 9, 10]),
                    "chart_config": {
                        "series_names": ["Transactions"],
                        "y_axis_min": 0,
                        "y_axis_max": 15,
                        "y_axis_ticks": [0, 5, 10, 15],
                        "y_axis_unit": "%",
                        "y_axis_label": "%",
                        "annotation": {
                            "text": "Leap Year Approx. (1%)",
                            "x": 420,
                            "y": 90,
                        },
                    },
                }
            },
            "speaker_notes": "Single series + leap-year annotation.",
        }
    )

    # ---------- 12 New Acquisitions ----------
    # Keep stacked bars (IR needs the chart) AND oversized hero key_stats for 66%/73%.
    # freeform cannot host Chart.js — use stacked_bar_chart as primary capability probe.
    add(
        {
            "layout_type": "stacked_bar_chart",
            "packing_mode": "chart-led",
            "title": "New Acquisitions",
            "section": "Acquisitions",
            "content": {
                "subtitle": "Proprietary New Cards Acquired (in millions)",
                "so_what": "",
                "key_stats": [
                    {
                        "label": "Global New Accounts Acquired on Fee-Paying Products*",
                        "value": "66%",
                    },
                    {
                        "label": "Global Consumer New Accounts Acquired from Millennial / Gen-Z",
                        "value": "73%",
                    },
                ],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "stacked_bar_chart",
                    "steps_or_data": bar_matrix(
                        [
                            "Quarter",
                            "U.S. Consumer Services",
                            "Commercial Services",
                            "International Card Services",
                        ],
                        [
                            ["Q1'25", "1.5", "0.8", "1.1"],
                            ["Q2'25", "1.5", "0.7", "0.9"],
                            ["Q3'25", "1.5", "0.7", "1.0"],
                            ["Q4'25", "1.3", "0.7", "0.9"],
                            ["Q1'26", "1.3", "0.8", "1.0"],
                        ],
                    ),
                    "chart_config": {
                        "series_names": [
                            "U.S. Consumer Services",
                            "Commercial Services",
                            "International Card Services",
                        ],
                        "series_colors": ["#00175A", "#006FCF", "#8A93A6"],
                    },
                }
            },
            "disclosure": {
                "pattern": "detail",
                "panels": [
                    {
                        "title": "NCA / NAA definitions",
                        "body": (
                            "NCA = new cards issued net of replacements. "
                            "NAA = new Card Member accounts opened, excludes supplemental cards. "
                            "*Fee-paying excludes Corporate."
                        ),
                    }
                ],
            },
            "speaker_notes": "Stacked NCA + two giant % chips; chart|hero card pair still B.",
        }
    )

    # ---------- 13 Balances vs Billings ----------
    add(
        {
            "layout_type": "line_chart",
            "packing_mode": "chart-led",
            "title": "Total Balances and Billed Business",
            "section": "Balances",
            "content": {
                "subtitle": "% Increase/(decrease) vs. Prior year (FX-adjusted)",
                "so_what": "",
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(Q, [7, 6, 7, 7, 7], [6, 7, 8, 8, 9]),
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
            },
            "speaker_notes": "Two series balances vs billings.",
        }
    )

    # ---------- 14 Credit Metrics ----------
    add(
        {
            "layout_type": "dual_chart",
            "packing_mode": "chart-led",
            "title": "Credit Metrics",
            "section": "Credit",
            "content": {
                "subtitle": "Net write-off rates and 30+ days past due",
                "so_what": "",
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(Q, [1.3, 1.3, 1.3, 1.3, 1.3]),
                    "chart_config": {
                        "series_names": ["Net write-off rate"],
                        "y_axis_min": 0,
                        "y_axis_max": 3,
                    },
                },
                "secondary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(Q, [2.1, 2.0, 1.9, 2.1, 2.0]),
                    "chart_config": {
                        "series_names": ["30+ days past due"],
                        "y_axis_min": 0,
                        "y_axis_max": 3,
                    },
                },
            },
            "speaker_notes": "Side-by-side credit lines with fixed axis.",
        }
    )

    # ---------- 15 Total Provision (A: true negatives) ----------
    add(
        {
            "layout_type": "stacked_bar_chart",
            "packing_mode": "chart-led",
            "title": "Total Provision",
            "section": "Credit",
            "content": {
                "subtitle": "$ in millions",
                "so_what": "",
                "key_stats": [
                    {"label": "Q1'26 Total Provision", "value": "$1,251"},
                    {"label": "Write-offs", "value": "$1,275"},
                    {"label": "Reserve Build/(Release)", "value": "($24)"},
                    {"label": "Reserve Rate", "value": "2.8%"},
                ],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "stacked_bar_chart",
                    "steps_or_data": bar_matrix(
                        ["Quarter", "Write-offs", "Reserve Build/(Release)"],
                        [
                            ["Q1'25", "1223", "-73"],
                            ["Q2'25", "1183", "222"],
                            ["Q3'25", "1162", "125"],
                            ["Q4'25", "1273", "141"],
                            ["Q1'26", "1275", "-24"],
                        ],
                    ),
                    "chart_config": {
                        "series_names": ["Write-offs", "Reserve Build/(Release)"],
                        "series_colors": ["#00175A", "#006FCF"],
                    },
                },
                "secondary_visual": {
                    "type": "data_table",
                    "steps_or_data": [
                        ["", "Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"],
                        ["Reserve Rate", "2.9%", "2.9%", "2.9%", "2.9%", "2.8%"],
                        ["Total Provision", "1150", "1405", "1287", "1414", "1251"],
                    ],
                },
            },
            "speaker_notes": "True negative reserve release — tests D11 capability.",
        }
    )

    # ---------- 16 Revenue Performance ----------
    add(
        {
            "layout_type": "data_table",
            "packing_mode": "stat-led",
            "title": "Revenue Performance",
            "section": "Revenue",
            "content": {
                "subtitle": "$ in millions; % Increase/(decrease) vs. Prior year",
                "so_what": "",
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "data_table",
                    "steps_or_data": [
                        [
                            "Line",
                            "Q1'26",
                            "Q1'25",
                            "Reported YoY%",
                            "FX-Adj YoY%",
                        ],
                        ["Discount Revenue", "$9,512", "$8,743", "9%", "7%"],
                        ["Net Card Fees", "$2,752", "$2,333", "18%", "16%"],
                        ["Service Fees and Other Revenue", "$1,951", "$1,722", "13%", "9%"],
                        ["Net Interest Income", "$4,692", "$4,169", "13%", "12%"],
                        [
                            "Revenues Net of Interest Expense",
                            "$18,907",
                            "$16,967",
                            "11%",
                            "10%",
                        ],
                    ],
                }
            },
            "disclosure": {
                "pattern": "detail",
                "panels": [
                    {
                        "title": "FX-adjusted note",
                        "body": "* FX-adjusted YoY rates are non-GAAP. See Annex 3.",
                    }
                ],
            },
            "speaker_notes": "Revenue table filled.",
        }
    )

    # ---------- 17 Net Card Fees dual ----------
    add(
        {
            "layout_type": "dual_chart",
            "packing_mode": "chart-led",
            "title": "Net Card Fees",
            "section": "Revenue",
            "content": {
                "subtitle": "$ in billions — % Increase/(decrease) vs. Prior year & CAGR (FX-adjusted)",
                "so_what": "",
                "key_stats": [
                    {"label": "CAGR", "value": "17%/yr"},
                    {"label": "Q1'26", "value": "$2.8B"},
                    {"label": "Q1'26 YoY", "value": "16%"},
                ],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "grouped_bar_chart",
                    "steps_or_data": bar_matrix(
                        ["Quarter", "Net Card Fees $B"],
                        [
                            ["Q1'19", "0.9"],
                            ["Q1'20", "1.1"],
                            ["Q1'21", "1.3"],
                            ["Q1'22", "1.4"],
                            ["Q1'23", "1.7"],
                            ["Q1'24", "2.0"],
                            ["Q1'25", "2.3"],
                            ["Q1'26", "2.8"],
                        ],
                    ),
                },
                "secondary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(
                        [
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
                        [16, 16, 18, 19, 20, 20, 17, 16, 16],
                    ),
                    "chart_config": {
                        "series_names": ["YoY %"],
                        "y_axis_min": 0,
                        "y_axis_max": 25,
                    },
                },
            },
            "speaker_notes": "Long-run bars + recent YoY line.",
        }
    )

    # ---------- 18 Premium Lending / NII ----------
    add(
        {
            "layout_type": "combo_chart",
            "packing_mode": "chart-led",
            "title": "Premium Lending — Net Interest Income",
            "section": "Revenue",
            "content": {
                "subtitle": "NII: Volume & Margin Drivers · $ in billions",
                "so_what": "",
                "key_stats": [
                    {"label": "Billed Business CAGR vs Q1'19", "value": "8%"},
                    {"label": "NII CAGR vs Q1'19", "value": "13%"},
                    {"label": "Total Balances CAGR", "value": "7%"},
                    {"label": "Q1'26 NII", "value": "$4.7B"},
                ],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "combo_chart",
                    "steps_or_data": [
                        {"label": "Q1'25", "value": 4.2},
                        {"label": "Q2'25", "value": 4.2},
                        {"label": "Q3'25", "value": 4.5},
                        {"label": "Q4'25", "value": 4.5},
                        {"label": "Q1'26", "value": 4.7},
                    ],
                    "chart_config": {"y_axis_min": 0, "y_axis_max": 6},
                },
                "line_overlay": {
                    "label": "YoY Growth %",
                    "style": "dashed",
                    "data": [
                        {"label": "Q1'25", "value": 11},
                        {"label": "Q2'25", "value": 12},
                        {"label": "Q3'25", "value": 12},
                        {"label": "Q4'25", "value": 12},
                        {"label": "Q1'26", "value": 12},
                    ],
                },
            },
            "speaker_notes": "NII combo bars + dashed YoY overlay.",
        }
    )

    # ---------- 19 Total revenues combo ----------
    add(
        {
            "layout_type": "combo_chart",
            "packing_mode": "chart-led",
            "title": "Total Revenues Net of Interest Expense",
            "section": "Revenue",
            "content": {
                "subtitle": "$ in billions — % Increase/(decrease) vs. Prior year",
                "so_what": "",
                "key_stats": [],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "combo_chart",
                    "steps_or_data": [
                        {"label": "Q1'25", "value": 17.0},
                        {"label": "Q2'25", "value": 17.9},
                        {"label": "Q3'25", "value": 18.4},
                        {"label": "Q4'25", "value": 19.0},
                        {"label": "Q1'26", "value": 18.9},
                    ],
                },
                "line_overlay": {
                    "label": "FX-Adj YoY %",
                    "style": "solid",
                    "data": [
                        {"label": "Q1'25", "value": 7},
                        {"label": "Q2'25", "value": 9},
                        {"label": "Q3'25", "value": 11},
                        {"label": "Q4'25", "value": 10},
                        {"label": "Q1'26", "value": 11},
                    ],
                },
            },
            "speaker_notes": "Dollar bars + FX-adj growth overlay.",
        }
    )

    # ---------- 20 Expense Performance (A: fill table) ----------
    add(
        {
            "layout_type": "data_table",
            "packing_mode": "stat-led",
            "title": "Expense Performance",
            "section": "Expenses",
            "content": {
                "subtitle": "$ in millions",
                "so_what": "",
                "key_stats": [
                    {
                        "label": "VCE of Revenue",
                        "value": "44.7%",
                    }
                ],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "data_table",
                    "steps_or_data": [
                        ["Expense line", "Q1'26", "Q1'25", "YoY% Inc/(Dec)"],
                        ["Card Member Rewards", "$4,891", "$4,378", "12%"],
                        ["Business Development", "$1,591", "$1,529", "4%"],
                        ["Card Member Services", "$1,975", "$1,328", "49%"],
                        [
                            "Variable Customer Engagement Expenses",
                            "$8,457",
                            "$7,235",
                            "17%",
                        ],
                        ["Marketing", "$1,480", "$1,486", "0%"],
                        ["Operating Expenses", "$3,941", "$3,766", "5%"],
                        ["Total Expenses", "$13,878", "$12,487", "11%"],
                    ],
                }
            },
            "disclosure": {
                "pattern": "detail",
                "panels": [
                    {
                        "title": "VCE & variance",
                        "body": (
                            "Q1'26 VCE % of Revenue noted on PDF. See Variance Commentary for "
                            "expense drivers. Card Member Services +49% from Platinum benefits usage."
                        ),
                    }
                ],
            },
            "speaker_notes": "Full expense grid from PDF page 19 text + 44.7% VCE chip (placement/inset still B).",
        }
    )

    # ---------- 21 Capital ----------
    add(
        {
            "layout_type": "metric_dashboard",
            "packing_mode": "stat-led",
            "title": "Capital",
            "section": "Capital",
            "content": {
                "subtitle": "$ in billions; Common Shares Outstanding in millions",
                "headline": "Capital",
                "key_stats": [
                    {"label": "CET1 Ratio Q1'26", "value": "10.5%"},
                    {"label": "CET1 Target", "value": "10–11%"},
                    {"label": "NI Returned (3yr)", "value": "74%"},
                    {"label": "Dividend/share ↑ (3yr)", "value": "58%"},
                    {"label": "Q1'26 Capital Returned", "value": "$2.3B"},
                    {"label": "Shares Outstanding", "value": "682"},
                    {"label": "ROE Q1'26", "value": "35%"},
                ],
                "so_what": "",
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "stacked_bar_chart",
                    "steps_or_data": bar_matrix(
                        ["Quarter", "Dividends", "Share Repurchases"],
                        [
                            ["Q4'24", "0.5", "1.1"],
                            ["Q1'25", "0.6", "0.7"],
                            ["Q2'25", "0.6", "1.4"],
                            ["Q3'25", "0.6", "2.3"],
                            ["Q4'25", "0.6", "0.9"],
                            ["Q1'26", "0.7", "1.6"],
                        ],
                    ),
                }
            },
            "speaker_notes": "Capital KPIs; multi-panel ROE/CET1 board still B.",
        }
    )

    # ---------- 22 Guidance (A: freeform metrics) ----------
    add(
        freeform_metrics(
            "2026 Guidance",
            "Guidance",
            [
                {"label": "Revenue Growth", "value": "9% – 10%"},
                {"label": "EPS", "value": "$17.30 – $17.90"},
            ],
            subtitle="Subject to the macroeconomic environment and other factors beyond the Company's control",
            disclosure={
                "pattern": "detail",
                "panels": [
                    {
                        "title": "Caution",
                        "body": (
                            "Ability to achieve 2026 guidance is subject to the macro environment "
                            "and factors beyond control. See Cautionary Note Regarding "
                            "Forward-Looking Statements."
                        ),
                    }
                ],
            },
            notes="Freeform two-KPI card; single bordered IR guidance chrome still B.",
        )
    )

    # ---------- 23 Appendix divider ----------
    add(
        {
            "layout_type": "section_divider",
            "packing_mode": "cover-led",
            "title": "Appendix",
            "section": "Appendix",
            "content": {
                "headline": "Appendix",
                "subtitle": "",
                "body_text": "",
            },
            "speaker_notes": "Appendix divider — full-bleed brand still B.",
        }
    )

    # ---------- 24 Network volumes ----------
    add(
        {
            "layout_type": "data_table",
            "packing_mode": "stat-led",
            "title": "Q1'26 Network Volumes Growth by Customer Type",
            "section": "Appendix",
            "content": {
                "subtitle": "% Increase/(decrease) vs. Prior Year (FX-adjusted)",
                "so_what": "",
                "key_stats": [
                    {"label": "U.S. Consumer % of NV", "value": "37%"},
                    {"label": "U.S. SME % of NV", "value": "22%"},
                    {"label": "Processed Volumes", "value": "$486B"},
                ],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "data_table",
                    "steps_or_data": [
                        ["Segment", "YoY Growth", "% of Network Volumes"],
                        ["U.S. Consumer Services", "10%", "37%"],
                        ["U.S. SME", "4%", "22%"],
                        ["U.S. Large & Global Corp.", "4%", "5%"],
                        ["Commercial Services (total)", "4%", "—"],
                        ["Int'l Consumer", "13%", "15%"],
                        ["Int'l SME & Large Corp.", "12%", "8%"],
                        ["International Card Services", "13%", "—"],
                        ["Processed Volumes", "12% report / 9% FX-adj", "$486B"],
                    ],
                }
            },
            "speaker_notes": "Network volumes table from PDF p23.",
        }
    )

    # ---------- 25 FX Impact ----------
    add(
        {
            "layout_type": "data_table",
            "packing_mode": "stat-led",
            "title": "FX Impact on Billed Business",
            "section": "Appendix",
            "content": {
                "subtitle": "Billed Business by currency (location of card issuance)",
                "so_what": "",
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "data_table",
                    "steps_or_data": [
                        [
                            "Currency",
                            "Q1'26 Billed Business % of Total",
                            "YoY Change in USD vs Currency Strengthened/(Weakened)",
                        ],
                        ["Euro €", "5%", "(10%)"],
                        ["UK £", "6%", "(6%)"],
                        ["Japan ¥", "4%", "3%"],
                        ["Australia $", "4%", "(10%)"],
                        ["Canada $", "3%", "(4%)"],
                        ["Mexico $", "2%", "(15%)"],
                        ["Top 6 Intl. Currencies", "24%", "(7%)"],
                        ["All Other Intl. Currencies", "3%", "—"],
                    ],
                }
            },
            "disclosure": {
                "pattern": "detail",
                "panels": [
                    {
                        "title": "FX notes",
                        "body": (
                            "* Represents percentage change in FX rates Q1'26 vs Q1'25. "
                            "** Reflects weighted average based on Billed Business mix."
                        ),
                    }
                ],
            },
            "speaker_notes": "FX impact table filled.",
        }
    )

    # ---------- 26 T&E ----------
    add(
        {
            "layout_type": "data_table",
            "packing_mode": "stat-led",
            "title": "Travel & Entertainment Billed Business",
            "section": "Appendix",
            "content": {
                "subtitle": "All growth rates FX-adjusted",
                "so_what": "",
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "data_table",
                    "steps_or_data": [
                        ["Category", "YoY Growth", "% of Total Billed Business"],
                        ["Restaurants", "9%", "7%"],
                        ["Lodging", "6%", "5%"],
                        ["Airlines", "8%", "7%"],
                        ["Other", "13%", "9%"],
                        ["Total T&E", "9%", "29%"],
                    ],
                }
            },
            "speaker_notes": "T&E breakdown table.",
        }
    )

    # ---------- 27 Macro scenarios (table scaffold — charts on PDF are multi line) ----------
    add(
        {
            "layout_type": "dual_chart",
            "packing_mode": "chart-led",
            "title": "Credit Reserve Macroeconomic Scenarios: Select Variables",
            "section": "Appendix",
            "content": {
                "subtitle": "U.S. Unemployment Rate % · U.S. GDP Growth % (SAAR)",
                "so_what": "",
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(
                        [
                            "Q1'25",
                            "Q2'25",
                            "Q3'25",
                            "Q4'25",
                            "Q1'26",
                            "Q2'26",
                            "Q3'26",
                            "Q4'26",
                        ],
                        [4.0, 4.1, 4.2, 4.2, 4.3, 4.2, 4.1, 4.0],
                        [4.2, 4.3, 4.5, 4.6, 4.7, 4.8, 4.9, 5.0],
                    ),
                    "chart_config": {
                        "series_names": ["Baseline UE", "Downside UE"],
                        "y_axis_min": 0,
                        "y_axis_max": 10,
                    },
                },
                "secondary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(
                        [
                            "Q1'25",
                            "Q2'25",
                            "Q3'25",
                            "Q4'25",
                            "Q1'26",
                            "Q2'26",
                            "Q3'26",
                            "Q4'26",
                        ],
                        [2.0, 2.1, 2.0, 1.9, 1.8, 1.9, 2.0, 2.1],
                        [1.0, 0.5, 0.0, -0.5, -1.0, -0.5, 0.0, 0.5],
                    ),
                    "chart_config": {
                        "series_names": ["Baseline GDP", "Downside GDP"],
                        "y_axis_min": -5,
                        "y_axis_max": 6,
                    },
                },
            },
            "disclosure": {
                "pattern": "detail",
                "panels": [
                    {
                        "title": "Scenario note",
                        "body": (
                            "Reflects range of variables available as of March 31, 2026 from an "
                            "independent third party without applying scenario weights. GDP is "
                            "Real GDP QoQ % SAAR. Numeric series are approx. from chart bands — not PDF OCR."
                        ),
                    }
                ],
            },
            "speaker_notes": "Approx. dual scenario lines; triple-scenario exact path still weak/B.",
        }
    )

    # ---------- 28 Funding ----------
    add(
        {
            "layout_type": "metric_dashboard",
            "packing_mode": "stat-led",
            "title": "Funding and Deposits",
            "section": "Appendix",
            "content": {
                "subtitle": "$ in billions",
                "so_what": "",
                "key_stats": [
                    {"label": "Customer Deposits Q1'26", "value": "72%"},
                    {"label": "Long-term Debt", "value": "21%"},
                    {"label": "Card ABS*", "value": "6%"},
                    {"label": "Other", "value": "1%"},
                    {"label": "Deposit Balances (approx)", "value": "$219B"},
                    {"label": "Direct Deposits share", "value": "82%"},
                ],
            },
            "disclosure": {
                "pattern": "detail",
                "panels": [
                    {
                        "title": "Funding footnotes",
                        "body": (
                            "* Face amount of Card ABS, net of securities retained; includes ABS "
                            "facility draws. ** Face amount of unsecured term debt."
                        ),
                    }
                ],
            },
            "speaker_notes": "Funding mix KPIs — stacked % bars of funding mix still prefer chart layout.",
        }
    )

    # ---------- 29-30 Variance commentary ----------
    for idx, title in [
        (28, "Additional Commentary — Variance Analysis"),
        (29, "Additional Commentary — Variance Analysis (cont.)"),
    ]:
        raw = by_idx[idx].get("raw_text") or ""
        bl = bullets_from_raw(raw)
        if not bl:
            bl = [
                "See PDF for full variance narrative bullets",
                "Revenue and provision bridges explained in IR prose",
            ]
        add(
            freeform_bullets(
                title,
                "Appendix",
                bl,
                subtitle="Selected Q1'26 vs Q1'25 commentary",
                notes="Dense freeform bullets from PDF raw_text.",
            )
        )

    # ---------- 31-37 Annex tables ----------
    annex_tables = {
        30: [
            ["Metric", "Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"],
            ["Billed Business Reported", "6%", "7%", "9%", "9%", "10%"],
            ["Billed Business FX-Adj*", "6%", "7%", "8%", "8%", "9%"],
            ["G&S Reported", "6%", "8%", "9%", "9%", "10%"],
            ["G&S FX-Adj*", "7%", "7%", "9%", "8%", "8%"],
            ["T&E Reported", "5%", "6%", "8%", "9%", "12%"],
            ["T&E FX-Adj*", "6%", "5%", "8%", "8%", "9%"],
            ["Processed Volumes Reported", "—", "—", "—", "—", "12%"],
            ["Processed Volumes FX-Adj*", "—", "—", "—", "—", "9%"],
            ["BB CAGR Q1'19–Q1'26 Reported", "5%", "", "", "", ""],
            ["BB CAGR Q1'19–Q1'26 FX-Adj*", "8%", "", "", "", ""],
        ],
        31: [
            ["Segment", "Q1'26 Reported", "Q1'26 FX-Adj*"],
            ["International Consumer", "21%", "13%"],
            ["International SME & Large Corp.", "19%", "12%"],
            ["ICS Total Billed Business", "20%", "13%"],
            ["ICS G&S", "21%", "14%"],
            ["ICS T&E", "18%", "10%"],
            ["U.S. Large and Global Corp.", "4%", "4%"],
            ["Commercial Services Total", "4%", "4%"],
            ["Commercial G&S", "3%", "3%"],
            ["Commercial T&E", "7%", "6%"],
        ],
        32: [
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
                "GAAP Total Balances $B",
                "142",
                "194",
                "199",
                "202",
                "208",
                "207",
                "212",
                "216",
                "225",
                "224",
            ],
            [
                "YoY GAAP Tot. Balances",
                "—",
                "—",
                "—",
                "—",
                "—",
                "7%",
                "7%",
                "7%",
                "8%",
                "8%",
            ],
            [
                "YoY FX-Adj Tot. Balances*",
                "—",
                "—",
                "—",
                "—",
                "—",
                "7%",
                "6%",
                "7%",
                "7%",
                "7%",
            ],
            ["CAGR GAAP Q1'19–Q1'26", "7%", "", "", "", "", "", "", "", "", ""],
            ["CAGR FX-Adj Q1'19–Q1'26*", "7%", "", "", "", "", "", "", "", "", ""],
        ],
    }

    # Pull remaining annex from raw_text where possible
    def table_from_placeholder(title_key: str):
        return [
            ["Line", "Q1'26 Reported", "Q1'26 FX-Adj", "YoY"],
            [title_key[:40], "see PDF", "see PDF", "—"],
        ]

    annex_titles = [
        (30, "Annex 1 (1 of 2) Billed Business and Processed Volumes — Reported & FX-Adjusted"),
        (31, "Annex 1 (2 of 2) Billed Business — Reported & FX-Adjusted"),
        (32, "Annex 2 Total Balances — Reported & FX-Adjusted"),
        (33, "Annex 3 Revenue — Reported & FX-Adjusted"),
        (34, "Annex 4 Net Card Fees — Reported & FX-Adjusted"),
        (35, "Annex 5 Net Interest Income — Reported & FX-Adjusted"),
        (36, "Annex 6 Revenues Net of Interest Expense — Reported & FX-Adjusted"),
    ]
    # Fill annex 3-6 with better rows from raw when present
    for aidx in (33, 34, 35, 36):
        rt = (by_idx.get(aidx) or {}).get("raw_text") or ""
        if "Annex" in rt:
            # keep simple structured extraction of percent lines
            rows = [["Item", "Detail"]]
            for ln in rt.splitlines():
                ln = ln.strip()
                if not ln or ln.isdigit() or ln.startswith("Annex") or ln.startswith("%"):
                    continue
                if len(ln) > 2:
                    rows.append([ln[:48], ln[48:96] if len(ln) > 48 else ""])
            if len(rows) > 2:
                annex_tables[aidx] = rows[:14]

    for idx, title in annex_titles:
        table = annex_tables.get(idx) or table_from_placeholder(title)
        add(
            {
                "layout_type": "data_table",
                "packing_mode": "stat-led",
                "title": title,
                "section": "Annex",
                "content": {
                    "subtitle": "% Increase/(decrease) vs. Prior year · $ where noted",
                    "so_what": "",
                },
                "visual_spec": {
                    "primary_visual": {"type": "data_table", "steps_or_data": table}
                },
                "disclosure": {
                    "pattern": "detail",
                    "panels": [
                        {
                            "title": "FX-adjusted note",
                            "body": "* See Slide 3 for an explanation of FX-adjusted information.",
                        }
                    ],
                },
                "speaker_notes": f"Annex filled/scaffold page index {idx}.",
            }
        )

    # ---------- 38-43 FLS ----------
    fls_from_raw = []
    for i in range(37, 43):
        raw = (by_idx.get(i) or {}).get("raw_text") or ""
        bl = bullets_from_raw(raw)
        fls_from_raw.append(bl)

    fls_fallback = [
        [
            "This presentation includes forward-looking statements within the meaning of the PSLRA",
            "Actual results may differ materially from those expressed or implied",
            "Factors include macroscopic, competitive, credit, regulatory, and operational risks",
        ],
        [
            "Net card fee revenues may not grow consistent with 2026 expectations",
            "Card Member engagement, attrition, and spend mix can diverge from plan",
            "Competition may pressure fee and lend economics",
        ],
        [
            "Actual Card Member rewards and services spend may differ from plan",
            "Business development and partnership costs are uncertain",
            "Technology and cyber incidents could disrupt operations",
        ],
        [
            "Tax rate may not remain consistent with expectations",
            "Changes in tax law, audits, and valuation allowances",
            "Capital and liquidity requirements may constrain returns",
        ],
        [
            "Commercial payments leadership and product rollout execution risk",
            "Integration and scaling of new commercial solutions",
            "Third-party and network partner dependencies",
        ],
        [
            "Dining strategy and platform growth (Resy/Tock) execution risk",
            "Regulatory, litigation, and reputational matters",
            "Other risks detailed in Amex SEC filings",
        ],
    ]
    for i in range(6):
        bl = fls_from_raw[i] if i < len(fls_from_raw) and fls_from_raw[i] else fls_fallback[i]
        cont = " (cont.)" if i else ""
        add(
            freeform_bullets(
                "Cautionary Note Regarding Forward-Looking Statements" + cont,
                "Legal",
                bl,
                notes="FLS legal freeform page.",
            )
        )

    # ---------- 44 trailing ----------
    add(
        {
            "layout_type": "section_divider",
            "packing_mode": "cover-led",
            "title": "American Express",
            "section": "End",
            "content": {
                "headline": "American Express",
                "subtitle": "Q1'26 Earnings",
            },
            "speaker_notes": "Trailing page — PDF is blankish / back cover.",
        }
    )

    assert len(slides) == 44, len(slides)

    handoff = {
        "presentation": {
            "title": "American Express Earnings Conference Call Q1'26",
            "subtitle": "Simulation handoff · pass_03 · SVG chart path + residual A",
            "audience": "Investors / IR",
            "primary_goal": (
                "Probe SVG path via --suppress-feature charts; residual A (ticks, VCE chip); document B"
            ),
            "readiness_score": 60,
            "quality_flags": ["simulation", "amex_q1_2026", "pass_03"],
            "theme": THEME,
        },
        "slides": slides,
    }
    OUT.write_text(json.dumps(handoff, indent=2), encoding="utf-8")
    print(f"wrote {OUT} slides={len(slides)} bytes={OUT.stat().st_size}")


if __name__ == "__main__":
    main()
