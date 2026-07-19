"""Build vision-assisted slides.json for Amex Q1'26 earnings PDF (simulation only)."""
from __future__ import annotations

import json
from pathlib import Path

import fitz

OUT = Path(__file__).resolve().parent / "slides.json"
PDF = Path(r"C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf")

BRAND = {
    "primary_navy": "#00175A",
    "accent_blue": "#006FCF",
    "text_navy": "#001B4D",
    "body_navy": "#1A2B5F",
    "white": "#FFFFFF",
    "table_header": "#00175A",
    "light_gray_rule": "#E0E3EB",
    "annotation_box": "#5B6B9A",
    "fonts": {
        "title": "sans-serif geometric/neo-grotesque bold (Amex corporate)",
        "body": "sans-serif clean (similar to Helvetica Neue / Amex Sans)",
        "numbers": "tabular sans-serif medium/bold",
    },
    "layout_cues": [
        "widescreen 16:9 (960x540 pt)",
        "centered navy titles on white content slides",
        "small gray footnote band at bottom with page number bottom-right",
        "cover and section dividers use two-tone navy/bright-blue with centurion seal watermark right",
        "charts use navy solid + gray dashed multi-series lines with value labels on points",
        "financial summary uses 3-column pill-header comparison table",
        "many earnings chart slides = chart + compact dark-header data table beneath",
    ],
}

CATS_Q = ["Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"]


def S(
    n: int,
    title: str,
    section: str,
    layout_hint: str,
    *,
    bullets=None,
    metrics=None,
    table=None,
    charts=None,
    notes: str = "",
    speaker: str = "",
    extra=None,
):
    d = {
        "slide_index": n,
        "pdf_page": n,
        "pdf_page_image": f"extracted/pdf_page_{n:02d}.png",
        "title": title,
        "section": section,
        "layout_hint": layout_hint,
        "bullets": bullets or [],
        "metrics": metrics or [],
        "table": table,
        "charts": charts or [],
        "footer_notes": notes,
        "speaker_notes": speaker,
        "brand": BRAND,
    }
    if extra:
        d.update(extra)
    return d


def build_slides():
    slides = []

    slides.append(
        S(
            0,
            "American Express Earnings Conference Call Q1'26",
            "Cover",
            "full_bleed_brand_cover_two_tone",
            metrics=[{"label": "Date", "value": "APRIL 23, 2026"}],
            speaker="Open IR earnings call cover.",
            extra={
                "layout_cues": (
                    "Dark navy upper ~60%, bright blue lower band, large white title left, "
                    "Amex centurion seal watermark lower-right with AMEX ribbon banner."
                )
            },
        )
    )

    slides.append(
        S(
            1,
            "Business Highlights",
            "Highlights",
            "centered_title_bullet_list",
            bullets=[
                "Q1 2026 revenue growth of 11%, and EPS of $4.28, up 18% YoY",
                "Named the Official Payments Partner of the NFL and announced a multi-year partnership extension with the NBA across league platforms, including the WNBA",
                "Launched the American Express Graphite Business Cash Unlimited Card, kicking off a major expansion of integrated solutions for businesses of all sizes",
                "Announced the Amex Agentic Commerce Experiences developer kit and industry-first Amex Agent Purchase Protection",
                "Unveiled next phase of the Resy dining platform, including the planned integration of Resy and Tock venue networks",
                "Opened Las Vegas Sidecar and New Delhi Centurion Lounge and announced upcoming new or expanded spaces in three other locations",
                "Ranked #4 on Great Place to Work 2026 list of the 100 Best Companies to Work For in the U.S.",
            ],
            notes=(
                "Refer to the Statistical Tables for the first-quarter 2026 "
                "(the Statistical Tables), available on the American Express Investor Relations "
                "website at ir.americanexpress.com"
            ),
            speaker="Walk 7 business headlines; bold key partnerships and product names",
            extra={"dense_bullets": True, "inline_bold_on_key_phrases": True},
        )
    )

    slides.append(
        S(
            2,
            "Summary Financial Performance",
            "Financials",
            "labeled_comparison_table_3col_pill_headers",
            metrics=[
                {"label": "Total Revenues Net of Interest Expense Q1'26", "value": "$18,907"},
                {"label": "Total Revenues Net of Interest Expense Q1'25", "value": "$16,967"},
                {"label": "Revenue YoY", "value": "11%"},
                {"label": "FX-Adjusted prior", "value": "$17,210"},
                {"label": "FX-Adjusted YoY", "value": "10%"},
                {"label": "Net Income Q1'26", "value": "$2,971"},
                {"label": "Net Income Q1'25", "value": "$2,584"},
                {"label": "Net Income YoY", "value": "15%"},
                {"label": "Diluted EPS Q1'26", "value": "$4.28"},
                {"label": "Diluted EPS Q1'25", "value": "$3.64"},
                {"label": "EPS YoY", "value": "18%"},
                {"label": "Avg Diluted Shares Q1'26", "value": "686"},
                {"label": "Avg Diluted Shares Q1'25", "value": "702"},
                {"label": "Shares YoY", "value": "(2%)"},
            ],
            table={
                "columns": ["Metric", "Q1'26", "Q1'25", "YoY% Inc/(Dec)"],
                "rows": [
                    ["Total Revenues Net of Interest Expense", "$18,907", "$16,967", "11%"],
                    ["FX-Adjusted*", "", "$17,210", "10%"],
                    ["Net Income", "$2,971", "$2,584", "15%"],
                    ["Diluted EPS**", "$4.28", "$3.64", "18%"],
                    ["Average Diluted Shares Outstanding", "686", "702", "(2%)"],
                ],
                "style": "three_pill_header_columns navy headers rounded tops white body row labels left",
            },
            notes="* FX-adjusted non-GAAP. ** Attributable to common shareholders.",
            speaker="Lead with revenue + EPS; note FX-adjusted and share count decline.",
        )
    )

    slides.append(
        S(
            3,
            "Total Billed Business",
            "Billings",
            "multi_series_line_chart_with_bottom_table",
            charts=[
                {
                    "type": "multi_line",
                    "title": "Total Billed Business",
                    "subtitle": "% Increase/(decrease) vs. Prior year (FX-adjusted unless otherwise stated)",
                    "categories": CATS_Q,
                    "series": [
                        {
                            "name": "FX-adjusted",
                            "values": [6, 7, 8, 8, 9],
                            "style": "solid navy markers with value labels",
                        },
                        {
                            "name": "Reported",
                            "values": [6, 7, 9, 9, 10],
                            "style": "dashed light-gray markers with end label 'Reported'",
                        },
                    ],
                    "y_axis": {"min": 0, "max": 15, "unit": "%"},
                    "annotations": [
                        {
                            "text": "Leap Year\nApprox.\n(1%)",
                            "style": "dashed rounded box upper-left",
                        }
                    ],
                    "value_labels_on_points": True,
                }
            ],
            table={
                "columns": ["", "Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"],
                "rows": [
                    ["G&S", "7%", "7%", "9%", "8%", "8%"],
                    ["T&E", "6%", "5%", "8%", "8%", "9%"],
                ],
                "style": "dark_navy_header_band white cells thin borders",
            },
            notes=(
                "See Annex 1 for reported billings growth rates. "
                "G&S = Goods & Services billed business. T&E = Travel & Entertainment billed business."
            ),
        )
    )

    slides.append(
        S(
            4,
            "U.S. Consumer Services Billed Business",
            "Billings",
            "line_chart_plus_generation_mix_table",
            charts=[
                {
                    "type": "line",
                    "categories": CATS_Q,
                    "series": [{"name": "YoY FX-adj", "values": [7, 7, 9, 9, 10]}],
                    "callouts": ["T&E, 11% YoY", "G&S, 9% YoY"],
                    "annotations": [{"text": "Leap Year Approx. (1%)"}],
                    "value_labels_on_points": True,
                }
            ],
            table={
                "columns": [
                    "Q1'26",
                    "Gen-Z",
                    "Millennials",
                    "Gen-X",
                    "Baby Boomer +",
                    "Total",
                ],
                "rows": [
                    ["YoY", "38%", "13%", "8%", "4%", "10%"],
                    ["% of Total", "6%", "30%", "36%", "28%", "100%"],
                ],
            },
        )
    )

    slides.append(
        S(
            5,
            "U.S. Consumer Platinum Performance",
            "US Consumer",
            "dual_panel_specialized_charts",
            charts=[
                {
                    "type": "multi_panel_spend_acceleration",
                    "title": "Spend Growth is Accelerating",
                    "note": "Contains Refresh callout and multi-series panels — complex dual visual",
                },
                {
                    "type": "retention_rate_broken_axis",
                    "title": "Account Retention Rate for Card Members in Renewal Anniversary Month",
                    "subtitle": "Retention Rates Remain High and Very Stable",
                    "y_window": ["90%", "100%"],
                    "callout": "+ ~6 percentage points",
                    "categories": ["January", "February", "March"],
                    "series_pairs": ["2025", "2026"],
                },
            ],
            extra={
                "complex_layout": (
                    "two-column specialized charts with broken-axis retention panels "
                    "and anniversary-month labels"
                )
            },
        )
    )

    slides.append(
        S(
            6,
            "U.S. Consumer: Membership Model Engagement",
            "US Consumer",
            "three_column_multiplier_cards",
            metrics=[
                {
                    "col": "Lodging",
                    "primary": "50%",
                    "compare": "5%",
                    "multiplier": "10x",
                    "labels": [
                        "Fine Hotels + Resorts and The Hotel Collection",
                        "U.S. Consumer Services Lodging",
                    ],
                },
                {
                    "col": "Restaurants",
                    "primary": "20%",
                    "compare": "10%",
                    "multiplier": "2x",
                    "labels": [
                        "U.S. Resy Restaurants",
                        "U.S. Consumer Services Restaurants",
                    ],
                },
                {
                    "col": "Airlines",
                    "primary": "21%",
                    "compare": "11%",
                    "multiplier": "2x",
                    "labels": [
                        "Member Airfares*",
                        "U.S. Consumer Services Airlines",
                    ],
                },
            ],
            notes=(
                "* Member Airfares offers Platinum and Centurion Card Members reduced fares "
                "on select premium tickets..."
            ),
            extra={"subtitle": "Card Member Spend Growth Rates; % Increase/(decrease) vs. Prior year"},
        )
    )

    slides.append(
        S(
            7,
            "Membership Model Engagement: Proprietary Lodging Assets",
            "US Consumer",
            "split_chart_and_kpi_cards",
            charts=[
                {
                    "type": "line",
                    "title": "Lodging Spend Growth",
                    "categories": ["Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"],
                    "series": [
                        {"name": "Fine Hotels + Resorts and The Hotel Collection", "end_value": "50%"},
                        {"name": "U.S. Consumer Services", "end_value": "5%"},
                    ],
                    "callout": "10x",
                }
            ],
            metrics=[
                {"label": "Premium Global Properties", "value": "3,400+"},
                {
                    "label": "New Properties Selected out of ~1,400 Applications in 2026",
                    "value": "300+",
                },
                {"label": "Average Card Member Value for 2-Night Stay*", "value": "$550"},
                {
                    "label": "Annual U.S. Platinum Statement Credit",
                    "value": "$600",
                    "sub": "100% Partner-Funded; Pre-Refresh Credit: $200",
                },
            ],
            bullets=[
                "Program Benefits: Early check-in, Late check-out, Room upgrades, "
                "Complimentary breakfast and Wi-Fi, Experience credits*"
            ],
        )
    )

    slides.append(
        S(
            8,
            "Commercial Services Billed Business",
            "Billings",
            "line_chart_plus_mix_table",
            charts=[
                {
                    "type": "line",
                    "categories": CATS_Q,
                    "series": [{"name": "YoY", "values": [2, 2, 4, 3, 4]}],
                    "callouts": ["T&E, 6% YoY", "G&S, 3% YoY"],
                    "annotations": [{"text": "Leap Year Approx. (1%)"}],
                }
            ],
            table={
                "columns": ["Q1'26", "U.S. SME", "U.S. Large & Global Corp.", "Total"],
                "rows": [
                    ["YoY", "4%", "4%", "4%"],
                    ["% of Total", "81%", "19%", "100%"],
                ],
            },
            notes="SME refers to small and mid-sized businesses with less than $300MM in annual revenues.",
        )
    )

    slides.append(
        S(
            9,
            "International Card Services Billed Business",
            "Billings",
            "dual_line_chart_plus_mix_table",
            charts=[
                {
                    "type": "multi_line",
                    "categories": CATS_Q,
                    "series": [
                        {"name": "FX-adjusted", "values": [13, 12, 13, 12, 13]},
                        {"name": "Reported", "values": [9, 15, 14, 17, 20]},
                    ],
                    "callouts": ["G&S, 14% YoY", "T&E, 10% YoY"],
                    "annotations": [{"text": "Leap Year Approx. (1%)"}],
                }
            ],
            table={
                "columns": ["Q1'26", "Intl Consumer", "Intl SME & Large Corp.", "Total"],
                "rows": [
                    ["YoY", "13%", "12%", "13%"],
                    ["% of Total", "65%", "35%", "100%"],
                ],
            },
        )
    )

    slides.append(
        S(
            10,
            "Transaction Growth",
            "Volumes",
            "single_line_chart",
            charts=[
                {
                    "type": "line",
                    "categories": CATS_Q,
                    "series": [{"name": "Transactions YoY", "values": [9, 9, 10, 9, 10]}],
                    "annotations": [{"text": "Leap Year Approx. (1%)"}],
                    "value_labels_on_points": True,
                }
            ],
            notes=(
                "Transactions represent global merchant transactions "
                "(excluding ATM transactions and balance transfers) on cards issued by American Express, "
                "net of returns."
            ),
        )
    )

    slides.append(
        S(
            11,
            "New Acquisitions",
            "Acquisitions",
            "stacked_bar_with_kpi_callouts",
            charts=[
                {
                    "type": "stacked_bar",
                    "title": "Proprietary New Cards Acquired (in millions)",
                    "categories": CATS_Q,
                    "series": [
                        {"name": "U.S. Consumer Services", "values": [1.5, 1.5, 1.5, 1.3, 1.3]},
                        {"name": "Commercial Services", "values": [0.8, 0.7, 0.7, 0.7, 0.8]},
                        {"name": "International Card Services", "values": [1.1, 0.9, 1.0, 0.9, 1.0]},
                    ],
                    "totals": [3.4, 3.1, 3.2, 2.9, 3.1],
                }
            ],
            metrics=[
                {
                    "label": "Global Consumer New Accounts Acquired from Millennial / Gen-Z",
                    "value": "73%",
                },
                {
                    "label": "Global New Accounts Acquired on Fee-Paying Products*",
                    "value": "66%",
                },
            ],
            notes=(
                "Proprietary new cards acquired (NCA) / proprietary new accounts acquired (NAA) definitions. "
                "*Excludes Corporate."
            ),
        )
    )

    slides.append(
        S(
            12,
            "Total Balances and Billed Business",
            "Balances",
            "dual_line_chart",
            charts=[
                {
                    "type": "multi_line",
                    "categories": CATS_Q,
                    "series": [
                        {"name": "Total Balances", "values": [7, 6, 7, 7, 7]},
                        {"name": "Billed Business", "values": [6, 7, 8, 8, 9]},
                    ],
                    "subtitle": "% Increase/(decrease) vs. Prior year (FX-adjusted)",
                }
            ],
            notes="Total Balances includes Card Balances held for investment and Other Loans.",
        )
    )

    slides.append(
        S(
            13,
            "Credit Metrics",
            "Credit",
            "side_by_side_line_charts",
            charts=[
                {
                    "type": "line",
                    "title": "Net Write-off Rates",
                    "categories": CATS_Q,
                    "series": [{"values": [1.3, 1.3, 1.3, 1.3, 1.3]}],
                    "subtitle": "% of Average Card Balances",
                },
                {
                    "type": "line",
                    "title": "30+ Days Past Due",
                    "categories": CATS_Q,
                    "series": [{"values": [2.1, 2.0, 1.9, 2.1, 2.0]}],
                    "subtitle": "% of Card Balances",
                },
            ],
            notes=(
                "Net write-off rates based on principal losses only; Consumer and Small Business "
                "Services Card Balances (unavailable for Corporate)."
            ),
        )
    )

    slides.append(
        S(
            14,
            "Total Provision",
            "Credit",
            "stacked_bar_with_reserve_rate_row",
            charts=[
                {
                    "type": "stacked_bar",
                    "unit": "$mm",
                    "categories": CATS_Q,
                    "series": [
                        {"name": "Write-offs", "values": [1223, 1183, 1162, 1273, 1275]},
                        {
                            "name": "Reserve Build/(Release)",
                            "values": [-73, 222, 125, 141, -24],
                        },
                    ],
                    "totals": [1150, 1405, 1287, 1414, 1251],
                }
            ],
            metrics=[
                {
                    "label": "Reserve Rate for Total Balances",
                    "values_by_quarter": ["2.9%", "2.9%", "2.9%", "2.9%", "2.8%"],
                }
            ],
        )
    )

    slides.append(
        S(
            15,
            "Revenue Performance",
            "Revenue",
            "labeled_comparison_table_4col_pill_headers",
            table={
                "columns": [
                    "Line",
                    "Q1'26",
                    "Q1'25",
                    "Reported YoY% Inc/(Dec)",
                    "FX-Adjusted* YoY% Inc/(Dec)",
                ],
                "rows": [
                    ["Discount Revenue", "$9,512", "$8,743", "9%", "7%"],
                    ["Net Card Fees", "$2,752", "$2,333", "18%", "16%"],
                    ["Service Fees and Other Revenue", "$1,951", "$1,722", "13%", "9%"],
                    ["Net Interest Income", "$4,692", "$4,169", "13%", "12%"],
                    ["Revenues Net of Interest Expense", "$18,907", "$16,967", "11%", "10%"],
                ],
                "style": "pill_header_columns like summary financials",
            },
            notes="See Variance Commentary in appendix. * FX-adjusted non-GAAP.",
        )
    )

    slides.append(
        S(
            16,
            "Net Card Fees",
            "Revenue",
            "dual_panel_bar_and_line",
            charts=[
                {
                    "type": "bar",
                    "title": "Net Card Fees (Q1: 2019-2026)",
                    "categories": [
                        "Q1'19",
                        "Q1'20",
                        "Q1'21",
                        "Q1'22",
                        "Q1'23",
                        "Q1'24",
                        "Q1'25",
                        "Q1'26",
                    ],
                    "series": [{"values": [0.9, 1.1, 1.3, 1.4, 1.7, 2.0, 2.3, 2.8]}],
                    "callout": "17% / Year CAGR",
                    "unit": "$B",
                },
                {
                    "type": "line",
                    "title": "Net Card Fees YoY% (Q1'24-Q1'26)",
                    "categories": [
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
                    "series": [{"values": [16, 16, 18, 19, 20, 20, 17, 16, 16]}],
                    "y_axis": {"min": 0, "max": 30, "unit": "%"},
                },
            ],
            notes="YoY growth rates and CAGR adjusted for FX are non-GAAP measures. See Annex 4.",
        )
    )

    slides.append(
        S(
            17,
            "Premium Lending / Net Interest Income",
            "Revenue",
            "kpi_cagr_with_nii_trend",
            metrics=[
                {"label": "Billed Business CAGR vs Q1'19", "value": "8%"},
                {"label": "NII CAGR vs Q1'19", "value": "13%"},
                {"label": "Total Balances CAGR vs Q1'19", "value": "7%"},
                {"label": "Margin (NII / Avg Total Balances) CAGR context", "value": "5%"},
            ],
            charts=[
                {
                    "type": "bar_with_yoy_labels",
                    "title": "Net Interest Income",
                    "categories": CATS_Q,
                    "values": [4.2, 4.2, 4.5, 4.5, 4.7],
                    "yoy": [11, 12, 12, 12, 12],
                    "unit": "$B",
                }
            ],
            notes="Volume & Margin driver decomposition alongside NII bars.",
        )
    )

    slides.append(
        S(
            18,
            "Total Revenues Net of Interest Expense",
            "Revenue",
            "combo_dollar_bars_and_growth_lines",
            charts=[
                {
                    "type": "bar",
                    "title": "Revenue $B levels",
                    "categories": CATS_Q,
                    "values": [17.0, 17.9, 18.4, 19.0, 18.9],
                },
                {
                    "type": "multi_line",
                    "title": "YoY growth %",
                    "categories": CATS_Q,
                    "series": [
                        {"name": "FX Adjusted", "values": [7, 9, 11, 10, 11]},
                        {"name": "Reported", "values": [8, 9, 11, 9, 10]},
                    ],
                    "annotations": [{"text": "Leap Year Approx. (1%)"}],
                },
            ],
        )
    )

    slides.append(
        S(
            19,
            "Expense Performance",
            "Expenses",
            "multi_row_expense_table_with_yoy",
            extra={
                "content_note": (
                    "Expense lines (Card Member Rewards and others) with $mm and YoY; "
                    "vision: table-/card-led expense walk. Full numbers in raw_text."
                )
            },
        )
    )

    slides.append(
        S(
            20,
            "Capital",
            "Capital",
            "multi_panel_capital_return",
            metrics=[
                {
                    "label": "Return on Average Equity (quarters)",
                    "values": ["35%", "34%", "36%", "36%", "34%", "35%"],
                },
                {
                    "label": "CET1 Ratio Q1'26",
                    "value": "10.5%",
                    "target": "10-11%",
                    "regulatory_min": "7%",
                },
                {
                    "label": "Net Income Returned to Common Shareholders (3 Year)",
                    "value": "74%",
                },
                {
                    "label": "Increase in Quarterly Dividend per Common Share (3 Year)",
                    "value": "58%",
                },
            ],
            charts=[
                {
                    "type": "stacked_bar",
                    "title": "Capital returned — Share Repurchases + Dividends ($B)",
                    "categories": [
                        "Q4'24",
                        "Q1'25",
                        "Q2'25",
                        "Q3'25",
                        "Q4'25",
                        "Q1'26",
                    ],
                    "series": [
                        {
                            "name": "Dividends",
                            "values": [0.5, 0.6, 0.6, 0.6, 0.6, 0.7],
                        },
                        {
                            "name": "Share Repurchases",
                            "values": [1.1, 0.7, 1.4, 2.3, 0.9, 1.7],
                        },
                    ],
                    "totals": [1.6, 1.3, 2.0, 2.9, 1.5, 2.3],
                },
                {
                    "type": "line",
                    "title": "Common Shares Outstanding (millions)",
                    "values": [702, 701, 696, 689, 686, 682],
                },
            ],
        )
    )

    slides.append(
        S(
            21,
            "2026 Guidance",
            "Guidance",
            "two_big_guidance_kpis",
            metrics=[
                {"label": "Revenue Growth", "value": "9% - 10%"},
                {"label": "EPS", "value": "$17.30 - $17.90"},
            ],
            notes=(
                "Our ability to achieve our 2026 guidance is subject to the macroeconomic environment, "
                "as well as contingencies and other factors beyond our control. "
                "Refer to Cautionary Note Regarding Forward-Looking Statements."
            ),
        )
    )

    slides.append(
        S(
            22,
            "Appendix",
            "Appendix",
            "section_divider_brand",
            extra={
                "layout_cues": "Same two-tone navy/blue cover style with centered 'Appendix' title"
            },
        )
    )

    appendix = [
        (23, "Q1'26 Network Volumes Growth by Customer Type", "grouped_bars_or_table"),
        (24, "FX Impact on Billed Business", "fx_impact_table"),
        (25, "Travel & Entertainment Billed Business", "breakdown_table_chart"),
        (
            26,
            "Credit Reserve Macroeconomic Scenarios: Select Variables",
            "multi_scenario_variable_table",
        ),
        (27, "Funding and Deposits", "funding_charts_tables"),
        (28, "Additional Commentary — Variance Analysis", "dense_bullet_commentary"),
        (29, "Additional Commentary — Variance Analysis (cont.)", "dense_bullet_commentary"),
        (
            30,
            "Annex 1 (1 of 2) Billed Business and Processed Volumes — Reported & FX-Adjusted",
            "wide_data_table",
        ),
        (
            31,
            "Annex 1 (2 of 2) Billed Business — Reported & FX-Adjusted",
            "wide_data_table",
        ),
        (32, "Annex 2 Total Balances — Reported & FX-Adjusted", "wide_data_table"),
        (33, "Annex 3 Revenue — Reported & FX-Adjusted", "wide_data_table"),
        (34, "Annex 4 Net Card Fees — Reported & FX-Adjusted", "wide_data_table"),
        (35, "Annex 5 Net Interest Income — Reported & FX-Adjusted", "wide_data_table"),
        (
            36,
            "Annex 6 Revenues Net of Interest Expense — Reported & FX-Adjusted",
            "wide_data_table",
        ),
    ]
    for n, title, lh in appendix:
        slides.append(
            S(
                n,
                title,
                "Appendix",
                lh,
                notes="Dense IR annex / appendix numeric grid — see raw_text and page PNG.",
            )
        )

    slides.append(
        S(
            37,
            "Cautionary Note Regarding Forward-Looking Statements",
            "Legal",
            "dense_legal_prose_multi_page",
            bullets=[
                "Forward-looking statements within the meaning of the Private Securities Litigation Reform Act",
                "Long risk-factor enumeration begins on this page",
            ],
        )
    )
    for n in range(38, 43):
        slides.append(
            S(
                n,
                "Cautionary Note Regarding Forward-Looking Statements (cont.)",
                "Legal",
                "dense_legal_bullet_continuation",
                bullets=["Continuation of forward-looking risk factors — see raw_text"],
            )
        )
    slides.append(
        S(
            43,
            "(Blank / trailing page)",
            "End",
            "blank_or_back_cover",
            extra={"note": "No substantial text extracted from final page"},
        )
    )

    return slides


def main():
    doc = fitz.open(str(PDF))
    slides = build_slides()
    assert len(slides) == len(doc) == 44, (len(slides), len(doc))

    for s in slides:
        i = s["slide_index"]
        s["raw_text"] = doc[i].get_text("text").strip()
        # printed page number often bottom-right; Amex content pages show 2..N
        s["image_exists"] = (Path(__file__).parent / f"pdf_page_{i:02d}.png").exists()

    out = {
        "source_pdf": str(PDF),
        "page_count": 44,
        "extraction_method": (
            "vision_read_of_pdf_page_png_plus_pdf_text_layer_assist "
            "(PyMuPDF used only for rasterize + raw text assist; no preprocessor)"
        ),
        "brand_system": BRAND,
        "slides": slides,
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {len(slides)} slides)")


if __name__ == "__main__":
    main()
