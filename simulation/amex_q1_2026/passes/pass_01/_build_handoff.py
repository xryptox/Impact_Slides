"""Author pass_01 handoff — maximal use of renderer_v2 features for Amex Q1'26."""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "handoff.json"

# Amex-ish theme overrides on Boardroom CSS variables (best-effort tokens).
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


def main():
    Q = ["Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"]
    slides = []

    def add(s):
        slides.append(s)

    # 1 Cover
    add(
        {
            "slide_number": 1,
            "layout_type": "title_or_opening",
            "packing_mode": "cover-led",
            "title": "American Express Earnings Conference Call",
            "section": "Cover",
            "content": {
                "headline": "American Express Earnings Conference Call",
                "subtitle": "Q1'26 · APRIL 23, 2026",
                "bullets": [],
                "key_stats": [],
                "body_text": "",
                "so_what": "",
                "narrative_bridge": "Open IR earnings call.",
            },
            "speaker_notes": "Cover — Amex Q1 2026 earnings conference call.",
        }
    )

    # 2 Business Highlights
    add(
        {
            "slide_number": 2,
            "layout_type": "split_text_visual",
            "packing_mode": "argument-led",
            "title": "Business Highlights",
            "section": "Highlights",
            "content": {
                "headline": "Business Highlights",
                "subtitle": "Q1 2026",
                "bullets": [
                    "Q1 2026 revenue growth of 11%, and EPS of $4.28, up 18% YoY",
                    "Named the Official Payments Partner of the NFL; multi-year NBA partnership extension incl. WNBA",
                    "Launched American Express Graphite Business Cash Unlimited Card — integrated solutions expansion",
                    "Announced Amex Agentic Commerce Experiences developer kit and Amex Agent Purchase Protection",
                    "Next phase of Resy dining platform; planned Resy and Tock venue network integration",
                    "Opened Las Vegas Sidecar and New Delhi Centurion Lounge; more spaces announced",
                    "Ranked #4 on Great Place to Work 2026 list of the 100 Best Companies to Work For in the U.S.",
                ],
                "so_what": "Revenue, EPS, partnerships, products, lounges, and culture headlines.",
                "narrative_bridge": "Financial summary next.",
            },
            "disclosure": {
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
            "speaker_notes": "Seven highlight bullets; footnoted IR terms live under disclosure.",
        }
    )

    # 3 Summary Financial Performance
    add(
        {
            "slide_number": 3,
            "layout_type": "data_table",
            "packing_mode": "stat-led",
            "title": "Summary Financial Performance",
            "section": "Financials",
            "content": {
                "subtitle": "$ in millions, except per share amounts; % Increase/(decrease) vs. Prior year",
                "so_what": "Revenue +11%, EPS +18%, shares down 2%.",
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
            "speaker_notes": "Three-column comparison; lead with revenue and EPS.",
        }
    )

    # 4 Total Billed Business — multi-line + secondary table
    add(
        {
            "slide_number": 4,
            "layout_type": "line_chart",
            "packing_mode": "chart-led",
            "title": "Total Billed Business",
            "section": "Billings",
            "content": {
                "subtitle": "% Increase/(decrease) vs. Prior year (FX-adjusted unless otherwise stated)",
                "so_what": "FX-adj billings at 9% in Q1'26; reported 10%.",
                "key_stats": [
                    {"label": "FX-adj Q1'26", "value": "9%"},
                    {"label": "Reported Q1'26", "value": "10%"},
                    {"label": "Leap Year approx.", "value": "(1%)"},
                ],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(Q, [6, 7, 8, 8, 9], [6, 7, 9, 9, 10]),
                    "chart_config": {
                        "series_names": ["FX-adjusted", "Reported"],
                        "series_styles": ["solid", "dashed"],
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
            "speaker_notes": "Solid FX-adj series vs dashed Reported; G&S/T&E table under chart.",
        }
    )

    # 5 US Consumer Services Billed Business
    add(
        {
            "slide_number": 5,
            "layout_type": "line_chart",
            "packing_mode": "chart-led",
            "title": "U.S. Consumer Services Billed Business",
            "section": "Billings",
            "content": {
                "subtitle": "% Increase/(decrease) vs. Prior year",
                "so_what": "UCS billings +10% in Q1'26; Gen-Z +38% YoY.",
                "key_stats": [
                    {"label": "T&E YoY", "value": "11%"},
                    {"label": "G&S YoY", "value": "9%"},
                    {"label": "Gen-Z YoY", "value": "38%"},
                    {"label": "Total YoY", "value": "10%"},
                ],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(Q, [7, 7, 9, 9, 10]),
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
            "speaker_notes": "Line + generation mix table.",
        }
    )

    # 6 US Consumer Platinum Performance — dualchart-ish via dual_chart
    add(
        {
            "slide_number": 6,
            "layout_type": "dual_chart",
            "packing_mode": "chart-led",
            "title": "U.S. Consumer Platinum Performance",
            "section": "US Consumer",
            "content": {
                "subtitle": "Spend Growth is Accelerating · Retention Rates Remain High and Very Stable",
                "so_what": "Spend accelerating post-refresh; retention high and stable (~+6pp callout).",
                "key_stats": [
                    {"label": "Retention callout", "value": "+~6 pp"},
                    {"label": "Retention band", "value": "90–100%"},
                ],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(Q, [7, 7, 9, 9, 10]),
                },
                "secondary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(
                        ["January", "February", "March"],
                        [94, 95, 95],
                        [96, 97, 97],
                    ),
                },
            },
            "speaker_notes": "Dual panel approximation of spend acceleration + retention bands.",
        }
    )

    # 7 Membership Model Engagement three columns
    add(
        {
            "slide_number": 7,
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
                    {"label": "Lodging UCS", "value": "5%"},
                    {"label": "Multiplier", "value": "10x"},
                    {"label": "Resy Restaurants", "value": "20%"},
                    {"label": "Member Airfares", "value": "21%"},
                ],
                "so_what": "Membership assets drive multiplies of category spend growth.",
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
            "speaker_notes": "Three category multipliers for membership model engagement.",
        }
    )

    # 8 Proprietary Lodging Assets
    add(
        {
            "slide_number": 8,
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
                    {"label": "Pre-Refresh Credit", "value": "$200"},
                    {"label": "FHR+THC YoY (end)", "value": "50%"},
                    {"label": "UCS Lodging YoY (end)", "value": "5%"},
                    {"label": "Multiplier", "value": "10x"},
                ],
                "bullets": [
                    "Program Benefits: Early check-in, Late check-out, Room upgrades, "
                    "Complimentary breakfast and Wi-Fi, Experience credits*",
                    "300+ new properties selected out of ~1,400 applications in 2026",
                ],
                "so_what": "Proprietary lodging network + $600 statement credit drive 10x spend growth.",
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(Q, [40, 42, 45, 48, 50], [5, 5, 5, 5, 5]),
                }
            },
            "speaker_notes": "KPI cards + lodging spend growth differential.",
        }
    )

    # 9 Commercial Services
    add(
        {
            "slide_number": 9,
            "layout_type": "line_chart",
            "packing_mode": "chart-led",
            "title": "Commercial Services Billed Business",
            "section": "Billings",
            "content": {
                "subtitle": "% Increase/(decrease) vs. Prior year (FX-adjusted)",
                "so_what": "Commercial billings +4% with SME 81% of mix.",
                "key_stats": [
                    {"label": "Total YoY", "value": "4%"},
                    {"label": "U.S. SME % of Total", "value": "81%"},
                    {"label": "T&E YoY", "value": "6%"},
                    {"label": "G&S YoY", "value": "3%"},
                ],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(Q, [2, 2, 4, 3, 4]),
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
            "speaker_notes": "Commercial line + mix table.",
        }
    )

    # 10 International Card Services
    add(
        {
            "slide_number": 10,
            "layout_type": "line_chart",
            "packing_mode": "chart-led",
            "title": "International Card Services Billed Business",
            "section": "Billings",
            "content": {
                "subtitle": "% Increase/(decrease) vs. Prior year (FX-adjusted unless otherwise stated)",
                "so_what": "ICS +13% FX-adj; reported series far more volatile.",
                "key_stats": [
                    {"label": "FX-adj Total", "value": "13%"},
                    {"label": "Intl Consumer", "value": "13%"},
                    {"label": "G&S YoY", "value": "14%"},
                    {"label": "T&E YoY", "value": "10%"},
                ],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(
                        Q, [13, 12, 13, 12, 13], [9, 15, 14, 17, 20]
                    ),
                    "chart_config": {
                        "series_names": ["FX-adjusted", "Reported"],
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
            "speaker_notes": "Dual series line + mix.",
        }
    )

    # 11 Transaction Growth
    add(
        {
            "slide_number": 11,
            "layout_type": "line_chart",
            "packing_mode": "chart-led",
            "title": "Transaction Growth",
            "section": "Volumes",
            "content": {
                "subtitle": "% Increase/(decrease) vs. Prior year",
                "so_what": "Transaction growth steady at ~9–10%.",
                "key_stats": [
                    {"label": "Q1'26", "value": "10%"},
                    {"label": "Leap Year approx.", "value": "(1%)"},
                ],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(Q, [9, 9, 10, 9, 10]),
                }
            },
            "speaker_notes": "Single series transaction growth.",
        }
    )

    # 12 New Acquisitions stacked bar
    add(
        {
            "slide_number": 12,
            "layout_type": "stacked_bar_chart",
            "packing_mode": "chart-led",
            "title": "New Acquisitions",
            "section": "Acquisitions",
            "content": {
                "subtitle": "Proprietary New Cards Acquired (in millions)",
                "so_what": "3.1M proprietary new cards in Q1'26; 73% Millennial/Gen-Z of consumer NAA.",
                "key_stats": [
                    {"label": "Q1'26 NCA total", "value": "3.1M"},
                    {"label": "Millennial/Gen-Z NAA", "value": "73%"},
                    {"label": "Fee-paying NAA*", "value": "66%"},
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
            "speaker_notes": "Stacked segment NCA + fee/age KPIs.",
        }
    )

    # 13 Total Balances and Billed Business
    add(
        {
            "slide_number": 13,
            "layout_type": "line_chart",
            "packing_mode": "chart-led",
            "title": "Total Balances and Billed Business",
            "section": "Balances",
            "content": {
                "subtitle": "% Increase/(decrease) vs. Prior year (FX-adjusted)",
                "so_what": "Balances mid-single-digit; billings accelerating to 9%.",
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(Q, [7, 6, 7, 7, 7], [6, 7, 8, 8, 9]),
                    "chart_config": {
                        "series_names": ["Total Balances", "Billed Business"],
                    },
                }
            },
            "speaker_notes": "Two series balances vs billings.",
        }
    )

    # 14 Credit Metrics
    add(
        {
            "slide_number": 14,
            "layout_type": "dual_chart",
            "packing_mode": "chart-led",
            "title": "Credit Metrics",
            "section": "Credit",
            "content": {
                "subtitle": "Net write-off rates and 30+ days past due",
                "so_what": "Write-offs flat 1.3%; delinquencies ~2.0%.",
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(Q, [1.3, 1.3, 1.3, 1.3, 1.3]),
                },
                "secondary_visual": {
                    "type": "line_chart",
                    "steps_or_data": line_points(Q, [2.1, 2.0, 1.9, 2.1, 2.0]),
                },
            },
            "speaker_notes": "Side-by-side credit metric lines.",
        }
    )

    # 15 Total Provision stacked
    add(
        {
            "slide_number": 15,
            "layout_type": "stacked_bar_chart",
            "packing_mode": "chart-led",
            "title": "Total Provision",
            "section": "Credit",
            "content": {
                "subtitle": "$ in millions",
                "so_what": "Q1'26 provision $1,251mm with small reserve release; reserve rate 2.8%.",
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
                            # Note: negative reserve release may render weakly — capability gap candidate
                            ["Q1'25", "1223", "0"],
                            ["Q2'25", "1183", "222"],
                            ["Q3'25", "1162", "125"],
                            ["Q4'25", "1273", "141"],
                            ["Q1'26", "1275", "0"],
                        ],
                    ),
                }
            },
            "speaker_notes": "Stacked provision; negative reserve release approximated (gap?).",
        }
    )

    # 16 Revenue Performance table
    add(
        {
            "slide_number": 16,
            "layout_type": "data_table",
            "packing_mode": "stat-led",
            "title": "Revenue Performance",
            "section": "Revenue",
            "content": {
                "subtitle": "$ in millions; % Increase/(decrease) vs. Prior year",
                "so_what": "Net card fees +18% reported / +16% FX-adj lead the mix.",
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
            "speaker_notes": "Four-column revenue table with reported and FX-adj YoY.",
        }
    )

    # 17 Net Card Fees dual
    add(
        {
            "slide_number": 17,
            "layout_type": "dual_chart",
            "packing_mode": "chart-led",
            "title": "Net Card Fees",
            "section": "Revenue",
            "content": {
                "subtitle": "$ in billions — % Increase/(decrease) vs. Prior year & CAGR (FX-adjusted)",
                "so_what": "17%/yr CAGR since Q1'19; Q1'26 NCF $2.8B.",
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
                },
            },
            "speaker_notes": "Long-run bars + recent YoY line.",
        }
    )

    # 18 Premium Lending / NII
    add(
        {
            "slide_number": 18,
            "layout_type": "combo_chart",
            "packing_mode": "chart-led",
            "title": "Premium Lending — Net Interest Income",
            "section": "Revenue",
            "content": {
                "subtitle": "NII: Volume & Margin Drivers · $ in billions",
                "so_what": "NII $4.7B in Q1'26 (+12% YoY); 13% CAGR vs Q1'19.",
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
                },
                "line_overlay": {
                    "label": "YoY Growth %",
                    "data": [
                        {"label": "Q1'25", "value": 11},
                        {"label": "Q2'25", "value": 12},
                        {"label": "Q3'25", "value": 12},
                        {"label": "Q4'25", "value": 12},
                        {"label": "Q1'26", "value": 12},
                    ],
                },
            },
            "speaker_notes": "NII bars with YoY overlay; CAGR KPI strip.",
        }
    )

    # 19 Total Revenues Net of Interest Expense
    add(
        {
            "slide_number": 19,
            "layout_type": "combo_chart",
            "packing_mode": "chart-led",
            "title": "Total Revenues Net of Interest Expense",
            "section": "Revenue",
            "content": {
                "subtitle": "$ in billions — % Increase/(decrease) vs. Prior year",
                "so_what": "Q1'26 revenue $18.9B; FX-adj growth 11%.",
                "key_stats": [
                    {"label": "Q1'26 $B", "value": "$18.9"},
                    {"label": "FX-adj YoY", "value": "11%"},
                    {"label": "Reported YoY", "value": "10%"},
                ],
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
                    "data": [
                        {"label": "Q1'25", "value": 7},
                        {"label": "Q2'25", "value": 9},
                        {"label": "Q3'25", "value": 11},
                        {"label": "Q4'25", "value": 10},
                        {"label": "Q1'26", "value": 11},
                    ],
                },
            },
            "speaker_notes": "Dollar bars + FX-adj growth overlay (reported second series is gap).",
        }
    )

    # 20 Expense Performance — table from raw text extraction of page 19
    add(
        {
            "slide_number": 20,
            "layout_type": "data_table_with_insight",
            "packing_mode": "stat-led",
            "title": "Expense Performance",
            "section": "Expenses",
            "content": {
                "subtitle": "$ in millions",
                "so_what": "Expense lines expand with rewards and operating leverage story.",
                "bullets": [
                    "See Variance Commentary in appendix for YoY drivers",
                    "Card Member Rewards is the largest single expense line",
                ],
            },
            "visual_spec": {
                "primary_visual": {
                    "type": "data_table",
                    "steps_or_data": [
                        ["Expense line", "Q1'26", "Q1'25", "YoY"],
                        ["Card Member Rewards", "see PDF", "see PDF", "~12%"],
                        ["Other operating expenses", "see PDF", "see PDF", "—"],
                    ],
                }
            },
            "speaker_notes": "Placeholder-aware table — full expense grid in appendix passes.",
        }
    )

    # 21 Capital
    add(
        {
            "slide_number": 21,
            "layout_type": "metric_dashboard",
            "packing_mode": "stat-led",
            "title": "Capital",
            "section": "Capital",
            "content": {
                "subtitle": "$ in billions; Common Shares Outstanding in millions",
                "headline": "Capital return with CET1 in target band",
                "key_stats": [
                    {"label": "CET1 Ratio Q1'26", "value": "10.5%"},
                    {"label": "CET1 Target", "value": "10–11%"},
                    {"label": "NI Returned (3yr)", "value": "74%"},
                    {"label": "Dividend/share ↑ (3yr)", "value": "58%"},
                    {"label": "Q1'26 Capital Returned", "value": "$2.3B"},
                    {"label": "Shares Outstanding", "value": "682"},
                    {"label": "ROE (recent)", "value": "~35%"},
                ],
                "so_what": "CET1 10.5% inside 10–11% target; 74% of NI returned over 3 years.",
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
            "speaker_notes": "Capital KPIs; multi-panel ROE/shares/CET1 weak under single layout.",
        }
    )

    # 22 Guidance
    add(
        {
            "slide_number": 22,
            "layout_type": "metric_dashboard",
            "packing_mode": "stat-led",
            "title": "2026 Guidance",
            "section": "Guidance",
            "content": {
                "headline": "2026 Guidance",
                "subtitle": "Subject to macroeconomic environment and contingencies",
                "key_stats": [
                    {"label": "Revenue Growth", "value": "9% – 10%"},
                    {"label": "EPS", "value": "$17.30 – $17.90"},
                ],
                "so_what": "Reaffirm roadmap: high-single to low-double-digit revenue and EPS band.",
            },
            "disclosure": {
                "pattern": "detail",
                "panels": [
                    {
                        "title": "Caution",
                        "body": (
                            "Ability to achieve 2026 guidance is subject to macro environment "
                            "and factors beyond control. See Cautionary Note Regarding "
                            "Forward-Looking Statements."
                        ),
                    }
                ],
            },
            "speaker_notes": "Two large guidance ranges.",
        }
    )

    # 23 Appendix divider
    add(
        {
            "slide_number": 23,
            "layout_type": "section_divider",
            "packing_mode": "cover-led",
            "title": "Appendix",
            "section": "Appendix",
            "content": {
                "headline": "Appendix",
                "subtitle": "Supporting detail, annex tables, and commentary",
            },
            "speaker_notes": "Section divider into appendix.",
        }
    )

    # 24-28 appendix content summaries
    appendix_simple = [
        (
            24,
            "Q1'26 Network Volumes Growth by Customer Type",
            "FX-adjusted network volumes by customer type.",
            [
                ["Customer Type", "YoY FX-adj"],
                ["U.S. Consumer", "see PNG"],
                ["Commercial", "see PNG"],
                ["International", "see PNG"],
            ],
        ),
        (
            25,
            "FX Impact on Billed Business",
            "Billed business by currency / FX impact.",
            [
                ["Segment", "Reported", "FX-Adj"],
                ["See PDF page 25", "—", "—"],
            ],
        ),
        (
            26,
            "Travel & Entertainment Billed Business",
            "T&E breakdown (FX-adjusted).",
            [
                ["Category", "YoY"],
                ["See PDF page 26", "—"],
            ],
        ),
        (
            27,
            "Credit Reserve Macroeconomic Scenarios: Select Variables",
            "Upside / Baseline / Downside macro variables.",
            [
                ["Variable", "Upside", "Baseline", "Downside"],
                ["See PDF page 27", "—", "—", "—"],
            ],
        ),
        (
            28,
            "Funding and Deposits",
            "Funding mix and deposit metrics.",
            [
                ["Item", "Value"],
                ["See PDF page 28", "—"],
            ],
        ),
    ]
    for num, title, so, table in appendix_simple:
        add(
            {
                "slide_number": num,
                "layout_type": "data_table",
                "packing_mode": "stat-led",
                "title": title,
                "section": "Appendix",
                "content": {"subtitle": so, "so_what": so},
                "visual_spec": {
                    "primary_visual": {"type": "data_table", "steps_or_data": table}
                },
                "speaker_notes": f"Appendix slide {(num)} — numeric fidelity via handoff tuning later.",
            }
        )

    # 29-30 variance commentary
    add(
        {
            "slide_number": 29,
            "layout_type": "split_text_visual",
            "packing_mode": "argument-led",
            "title": "Additional Commentary — Variance Analysis",
            "section": "Appendix",
            "content": {
                "headline": "Variance Analysis",
                "subtitle": "Selected Q1'26 vs Q1'25 commentary",
                "bullets": [
                    "See PDF page 29 for full variance narrative bullets",
                    "Revenue and provision bridges explained in IR prose",
                    "Non-GAAP references point to annex tables",
                ],
                "so_what": "Narrative variance support for financial tables.",
            },
            "speaker_notes": "Dense commentary bullets.",
        }
    )
    add(
        {
            "slide_number": 30,
            "layout_type": "split_text_visual",
            "packing_mode": "argument-led",
            "title": "Additional Commentary — Variance Analysis (cont.)",
            "section": "Appendix",
            "content": {
                "headline": "Variance Analysis (continued)",
                "bullets": [
                    "Card Member Rewards Expense: +12% vs Q1'25, driven by billed business and mix",
                    "Additional expense and revenue variance lines on PDF page 30",
                ],
                "so_what": "Rewards expense participates in operating leverage debate.",
            },
            "speaker_notes": "Continuation page.",
        }
    )

    # 31-37 annex wide tables
    for i, title in enumerate(
        [
            "Annex 1 (1 of 2) Billed Business and Processed Volumes — Reported & FX-Adjusted",
            "Annex 1 (2 of 2) Billed Business — Reported & FX-Adjusted",
            "Annex 2 Total Balances — Reported & FX-Adjusted",
            "Annex 3 Revenue — Reported & FX-Adjusted",
            "Annex 4 Net Card Fees — Reported & FX-Adjusted",
            "Annex 5 Net Interest Income — Reported & FX-Adjusted",
            "Annex 6 Revenues Net of Interest Expense — Reported & FX-Adjusted",
        ],
        start=31,
    ):
        add(
            {
                "slide_number": i,
                "layout_type": "data_table",
                "packing_mode": "stat-led",
                "title": title,
                "section": "Annex",
                "content": {
                    "subtitle": "Wide IR annex grid — full cells in PDF; handoff carries scaffold",
                    "so_what": "Annex supports non-GAAP reconciliations.",
                },
                "visual_spec": {
                    "primary_visual": {
                        "type": "data_table",
                        "steps_or_data": [
                            ["Line", "Q1'26 Reported", "Q1'26 FX-Adj", "YoY"],
                            ["See PDF", "—", "—", "—"],
                            ["Dense multi-column IR table", "—", "—", "—"],
                        ],
                    }
                },
                "speaker_notes": f"Annex table scaffold page {i}.",
            }
        )

    # 38-43 FLS bullets
    fls_chunks = [
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
    for i, bullets in enumerate(fls_chunks):
        add(
            {
                "slide_number": 38 + i,
                "layout_type": "split_text_visual",
                "packing_mode": "argument-led",
                "title": "Cautionary Note Regarding Forward-Looking Statements"
                + (" (cont.)" if i else ""),
                "section": "Legal",
                "content": {
                    "headline": "Cautionary Note Regarding Forward-Looking Statements",
                    "bullets": bullets,
                    "so_what": "Legal forward-looking risk inventory.",
                },
                "speaker_notes": "FLS legal page.",
            }
        )

    # 44 trailing
    add(
        {
            "slide_number": 44,
            "layout_type": "section_divider",
            "packing_mode": "cover-led",
            "title": "American Express",
            "section": "End",
            "content": {
                "headline": "American Express",
                "subtitle": "Q1'26 Earnings",
            },
            "speaker_notes": "Trailing/blank page scaffold.",
        }
    )

    assert len(slides) == 44, len(slides)

    handoff = {
        "presentation": {
            "title": "American Express Earnings Conference Call Q1'26",
            "subtitle": "Simulation handoff · pass_01 · renderer_v2 capability probe",
            "audience": "Investors / IR",
            "primary_goal": (
                "Probe renderer_v2 fidelity vs real Amex earnings PDF "
                "(observation only; no renderer edits)"
            ),
            "readiness_score": 55,
            "quality_flags": ["simulation", "amex_q1_2026", "pass_01"],
            "theme": THEME,
        },
        "slides": slides,
    }
    OUT.write_text(json.dumps(handoff, indent=2), encoding="utf-8")
    print(f"wrote {OUT} slides={len(slides)} bytes={OUT.stat().st_size}")


if __name__ == "__main__":
    main()
