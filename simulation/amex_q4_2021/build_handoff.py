"""Author schema-v1 Q4 2021 Amex handoff from extracted PDF values only."""
from __future__ import annotations

import json
from pathlib import Path

SHA = "8e113208a6df838861fc06cdbfb82514f01f43c42a21e02005801f8fdf545e21"
SRC = "American Express Q4 2021 Earnings Presentation"
OUT = Path(__file__).with_name("handoff_v1.json")

Q20_21 = [
    ("q1-20", "Q1'20"),
    ("q2-20", "Q2'20"),
    ("q3-20", "Q3'20"),
    ("q4-20", "Q4'20"),
    ("q1-21", "Q1'21"),
    ("q2-21", "Q2'21"),
    ("q3-21", "Q3'21"),
    ("q4-21", "Q4'21"),
]
Q3Q4 = [
    ("q3-19", "Q3'19"),
    ("q4-19", "Q4'19"),
    ("q3-20", "Q3'20"),
    ("q4-20", "Q4'20"),
    ("q3-21", "Q3'21"),
    ("q4-21", "Q4'21"),
]


def eid(n: int) -> str:
    return f"amex-q4-2021-p{n:02d}"


def ev(n: int) -> list[str]:
    return [eid(n)]


def num(v, fmt: str) -> dict:
    return {"type": "number", "value": str(v), "format_id": fmt}


def miss() -> dict:
    return {"type": "missing"}


def rng(lo, hi, fmt: str) -> dict:
    return {"type": "range", "lower": str(lo), "upper": str(hi), "format_id": fmt}


def cats(pairs):
    return [{"category_id": i, "label": l} for i, l in pairs]


def ser(sid, name, values, color=None):
    d = {
        "series_id": sid,
        "name": name,
        "values": [None if v is None else str(v) for v in values],
    }
    if color:
        d["color"] = color
    return d


def line(surface, heading, pairs, series, fmt="pct_0", subtitle=None, ticks=5):
    ch = {
        "type": "chart",
        "surface_id": surface,
        "chart_type": "line",
        "heading": heading,
        "chart_data": {"categories": cats(pairs), "series": series},
        "category_axis": {"visible": True},
        "value_axes": {
            "primary": {
                "visible": True,
                "format_id": fmt,
                "domain": {"kind": "generated", "target_ticks": ticks},
            }
        },
        "display": {"ordinary_values": "show", "series_identity": "legend"},
    }
    if subtitle:
        ch["subtitle"] = subtitle
    return ch


def gbar(surface, heading, pairs, series, fmt="pct_0", subtitle=None):
    ch = {
        "type": "chart",
        "surface_id": surface,
        "chart_type": "grouped_bar",
        "heading": heading,
        "chart_data": {"categories": cats(pairs), "series": series},
        "category_axis": {"visible": True},
        "value_axes": {
            "primary": {
                "visible": True,
                "format_id": fmt,
                "domain": {"kind": "generated", "target_ticks": 5},
            }
        },
        "display": {"ordinary_values": "show", "series_identity": "legend"},
    }
    if subtitle:
        ch["subtitle"] = subtitle
    return ch


def sbar(surface, heading, pairs, series, fmt="pct_0", subtitle=None, totals=None, tot_fmt=None):
    ch = {
        "type": "chart",
        "surface_id": surface,
        "chart_type": "stacked_bar",
        "heading": heading,
        "chart_data": {"categories": cats(pairs), "series": series},
        "category_axis": {"visible": True},
        "value_axes": {
            "primary": {
                "visible": True,
                "format_id": fmt,
                "domain": {"kind": "generated", "target_ticks": 5},
            }
        },
        "display": {"stack_segments": "show", "stack_totals": "show", "series_identity": "legend"},
    }
    if subtitle:
        ch["subtitle"] = subtitle
    if totals is not None:
        ch["auxiliary_series"] = [
            {
                "auxiliary_id": f"{surface}-tot",
                "role": "authored_stack_total",
                "label": "Total",
                "format_id": tot_fmt or fmt,
                "values": [None if v is None else str(v) for v in totals],
            }
        ]
    return ch


def combo(surface, heading, pairs, series, bar_mode="grouped", pfmt="usd_1", sfmt=None, subtitle=None):
    axes = {
        "primary": {
            "visible": True,
            "format_id": pfmt,
            "domain": {"kind": "generated", "target_ticks": 5},
        }
    }
    if sfmt:
        axes["secondary"] = {
            "visible": True,
            "format_id": sfmt,
            "domain": {"kind": "generated", "target_ticks": 5},
        }
    ch = {
        "type": "chart",
        "surface_id": surface,
        "chart_type": "combo",
        "bar_mode": bar_mode,
        "heading": heading,
        "chart_data": {"categories": cats(pairs), "series": series},
        "category_axis": {"visible": True},
        "value_axes": axes,
        "display": {"ordinary_values": "show", "series_identity": "legend"},
    }
    if subtitle:
        ch["subtitle"] = subtitle
    return ch


def table(surface, stub, columns, rows):
    return {
        "surface_id": surface,
        "stub_header": {"label": stub},
        "columns": [{"column_id": cid, "label": lab} for cid, lab in columns],
        "rows": rows,
    }


def row(rid, label, cells):
    return {"row_id": rid, "label": label, "cells": cells}


def disc(sid, title, texts):
    return {
        "sections": [
            {
                "surface_id": sid,
                "title": title,
                "items": [{"kind": "paragraph", "text": t} for t in texts],
            }
        ]
    }


def para_block(bid, texts):
    return {
        "block_id": bid,
        "type": "paragraphs",
        "paragraphs": [{"runs": [{"text": t}]} for t in texts],
    }


def bullets(bid, items):
    return {
        "block_id": bid,
        "type": "bullet_list",
        "items": [{"runs": [{"text": t}]} for t in items],
    }


def ordinary(n, layout, title, payload, section="earnings", extra=None):
    s = {
        "slide_number": n,
        "layout_type": layout,
        "section_id": section,
        "title": title,
        "payload": payload,
        "evidence_ids": ev(n),
    }
    if extra:
        s.update(extra)
    return s


def evidence_registry():
    return {
        eid(n): {
            "source_name": SRC,
            "locator": {"kind": "pdf_page", "sha256": SHA, "page": n, "index": n - 1},
        }
        for n in range(1, 54)
    }


FLS = {
    47: [
        "This presentation includes forward-looking statements within the meaning of the Private Securities Litigation Reform Act of 1995, which are subject to risks and uncertainties. The forward-looking statements, which address American Express Company's current expectations regarding business and financial performance, including management's outlook for 2022, expectations for 2023 and aspirations for 2024 and beyond, among other matters, contain words such as \"believe,\" \"expect,\" \"anticipate,\" \"intend,\" \"plan,\" \"aim,\" \"will,\" \"may,\" \"should,\" \"could,\" \"would,\" \"likely\" and similar expressions. Readers are cautioned not to place undue reliance on these forward-looking statements, which speak only as of the date on which they are made. The company undertakes no obligation to update or revise any forward-looking statements. Factors that could cause actual results to differ materially from these forward-looking statements, include, but are not limited to, the following:",
        "- the company's ability to achieve its 2022 earnings per common share (EPS) outlook, grow earnings in the future and execute on its new growth plan, which will depend in part on revenue growth, credit performance and the effective tax rate remaining consistent with current expectations and the company's ability to continue investing in customers, brand and talent, controlling operating expenses, effectively manage risk and executing its share repurchase program; any of which could be impacted by, among other things, the factors identified in the subsequent paragraphs as well as the following: the extent and duration of the effect of the pandemic on the economy, inflation, consumer confidence, consumer and business spending, and customer behaviors, such as with respect to travel, dining, shopping and in-person events; the impact on consumers and businesses as forbearance and government support programs end; the continued stress on businesses due to containment measures, operational changes, supply chain issues and staffing shortages; issues impacting brand perceptions and the company's reputation; the impact of any future contingencies, including, but not limited to, restructurings, investment gains, impairments, changes in reserves, legal costs, the imposition of fines or civil money penalties and increases in Card Member reimbursements; impacts related to new or renegotiated cobrand and other partner agreements; and the impact of regulation and litigation, which could affect the profitability of the company's business activities, limit the company's ability to pursue business opportunities, require changes to business practices or alter the company's relationships with partners, merchants and Card Members;",
    ],
    48: [
        "- the company's ability to achieve its 2022 revenue growth outlook, its revenue growth expectations for 2023 and its revenue growth aspirations for 2024 and beyond, which could be impacted by, among other things, uncertainty regarding the continued spread of COVID-19 (including new variants) and the availability, distribution and use of effective treatments and vaccines; a deterioration in global economic and business conditions; consumer and business spending not growing in line with expectations, including Goods & Services spending not continuing to show strong growth and Travel & Entertainment spending not recovering through 2022 and 2023 as expected; prolonged measures to contain the spread of COVID-19 (including travel restrictions), concern of the possible imposition of further containment measures or premature easing of such containment measures, any of which could further exacerbate the effects on business activity and the company's Card Members, partners and merchants; health concerns associated with the pandemic continuing to affect customer behaviors, spending levels and preferences, and travel patterns and demand even after containment measures are lifted; the amount and efficacy of investments in share, scale and relevance; growth in Card Member loans and the yield on Card Member loans not remaining consistent with current expectations; the average discount rate changing by a greater or lesser amount than expected; an inability of business partners to meet their obligations to the company and the company's customers due to slowdowns or disruptions in their businesses, bankruptcy or liquidation, or otherwise; and the company's inability to address competitive pressures and implement its strategies and business initiatives, including within the premium consumer space, commercial payments, the global merchant network and digital environment;",
        "- future credit performance, the level of future delinquency and write-off rates and the amount and timing of future reserve builds and releases, which will depend in part on changes in consumer behavior that affect loan and receivable balances (such as paydown and revolve rates); macroeconomic factors such as unemployment rates, GDP and the volume of bankruptcies; the ability and willingness of Card Members to pay amounts owed to the company, particularly as forbearance and government support programs end; the enrollment in, and effectiveness of, hardship programs and troubled debt restructurings; the performance of accounts as they graduate and exit from financial relief programs; collections capabilities and recoveries of previously written-off loans and receivables; and governmental actions that provide forms of relief with respect to certain loans and fees, such as limiting debt collections efforts and encouraging or requiring extensions, modifications or forbearance;",
        "- net interest income and the growth rate of loans outstanding being higher or lower than current expectations, which will depend on the behavior of Card Members and their actual spending, borrowing and paydown patterns; the company's ability to effectively manage risk and enhance Card Member value propositions; changes in benchmark interest rates; changes in capital and credit market conditions and the availability and cost of capital; credit actions, including line size and other adjustments to credit availability; and the effectiveness of the company's strategies to capture a greater share of existing Card Members' spending and borrowings, and retain and attract new customers;",
    ],
    49: [
        "- the actual amount to be spent on marketing in 2022 and beyond, which will be based in part on continued changes in the macroeconomic and competitive environment and business performance; management's identification and assessment of attractive investment opportunities and the receptivity of Card Members and prospective customers to advertising and customer acquisition initiatives; the company's ability to balance expense control and investments in the business; and management's ability to realize efficiencies and optimize investment spending;",
        "- the actual amount to be spent on Card Member rewards and services and business development, and the relationship of these variable customer engagement costs to revenues, which could be impacted by continued changes in macroeconomic conditions and Card Member behavior as it relates to their spending patterns (including the level of spend in bonus categories), the redemption of rewards and offers (including travel redemptions) and usage of travel-related benefits; the costs related to reward point redemptions; inflation; further enhancements to product benefits to make them attractive to Card Members and prospective customers, potentially in a manner that is not cost effective; new and renegotiated contractual obligations with business partners; and the pace and cost of the expansion of the company's global lounge collection;",
        "- the ability of the company to control its operating expenses and the actual amount the company spends on operating expenses in 2022 and beyond, which could be impacted by, among other things, salary and benefit expenses to attract and retain talent; costs due to new hybrid working arrangements; supply chain issues; a persistent inflationary environment; management's decision to increase or decrease spending in such areas as technology, business and product development, sales force, premium servicing and digital capabilities depending on overall business performance; the company's ability to innovate efficient channels of customer interactions; restructuring activity; fraud costs; information security or compliance expenses or consulting, legal and other professional services fees, including as a result of litigation or internal and regulatory reviews; the level of M&A activity and related expenses; the payment of civil money penalties, disgorgement, restitution, non-income tax assessments and litigation-related settlements; impairments of goodwill or other assets; and the impact of changes in foreign currency exchange rates on costs;",
        "- net card fees not performing consistent with current expectations, which could be impacted by, among other things, a deterioration in macroeconomic conditions impacting the ability and desire of Card Members to pay card fees; higher Card Member attrition rates; the pace of Card Member acquisition activity; and the company's inability to address competitive pressures, develop attractive value propositions and implement its strategy of refreshing card products and enhancing benefits and services;",
    ],
    50: [
        "- the average discount rate not performing consistent with current expectations, including as a result of further changes in the mix of spending by location and industry (including the level of T&E spending), merchant negotiations (including merchant incentives, concessions and volume-related pricing discounts), competition, pricing regulation (including regulation of competitors' interchange rates) and other factors;",
        "- the company's tax rate not remaining consistent with current levels, which could be impacted by, among other things, changes in tax laws and regulation, the company's geographic mix of income, unfavorable tax audits and other unanticipated tax items;",
        "- changes in the substantial and increasing worldwide competition in the payments industry, including competitive pressure that may materially impact the prices charged to merchants that accept American Express cards, the ability of the company to maintain the Platinum card franchise's leadership in the premium space, competition for new and existing cobrand relationships, competition from new and non-traditional competitors and the success of marketing, promotion and rewards programs;",
        "- changes affecting the company's plans regarding the return of capital to shareholders, including increasing the level of the dividend, subject to approval by the company's Board of Directors, which will depend on factors such as capital levels and regulatory capital ratios; changes in the stress testing and capital planning process and new guidance from the Federal Reserve; the company's results of operations and financial condition; the company's credit ratings and rating agency considerations; and the economic environment and market conditions in any given period;",
        "- the company's ability to expand its leadership in the premium consumer space, which will be impacted in part by competition, brand perceptions (including perceptions related to merchant coverage) and reputation and the ability of the company to develop and market value propositions that appeal to Card Members and new customers and offer attractive services and rewards programs, which will depend in part on ongoing investments, addressing changing customer behaviors, new product innovation and development, Card Member acquisition efforts and enrollment processes, including through digital channels, and infrastructure to support new products, services and benefits;",
        "- the ability of the company to build on its leadership in commercial payments, which will depend in part on competition, the willingness and ability of companies to use credit and charge cards for procurement and other business expenditures as well as use the company's products for financing needs, perceived or actual difficulties and costs related to setting up card-based B2B payment platforms, the ability of the company to offer attractive value propositions to potential customers, the company's ability to enhance and expand its payment and lending solutions and continue the rollout of the Kabbage platform to the company's small business customers;",
    ],
    51: [
        "- the ability of the company to execute on its plans to expand merchant coverage globally, which will depend in part on the success of the company, OptBlue merchant acquirers and GNS partners in signing merchants to accept American Express, which could be impacted by our value propositions offered to merchants and merchant acquirers for card acceptance, as well as the awareness and willingness of Card Members to use American Express cards at merchants, the company's ability to increase coverage in priority international regions and execute on our plans in China and technological developments, including capabilities that allow greater digital integration;",
        "- the ability of the company to stay on the leading edge of technology and digital payment solutions, which will depend on our success in evolving our products and processes for the digital environment, developing new features in the Amex app and enhancing our digital channels, building partnerships and executing programs with other companies, effectively utilizing artificial intelligence to address servicing and other customer needs, and supporting the use of our products as a means of payment through online and mobile channels, all of which will be impacted by investment levels, new product innovation and development and infrastructure to support new products, services and benefits;",
        "- our ability to implement our ESG strategies and initiatives, which depend in part on the amount and efficacy of our investments in product innovations, marketing campaigns, our supply chain and operations, and philanthropic, colleague and community programs; customer behaviors; and the cost and availability of solutions for a low carbon economy;",
        "- a failure in or breach of the company's operational or security systems, processes or infrastructure, or those of third parties, including as a result of cyberattacks, which could compromise the confidentiality, integrity, privacy and/or security of data, disrupt its operations, reduce the use and acceptance of American Express cards and lead to regulatory scrutiny, litigation, remediation and response costs, and reputational harm;",
        "- legal and regulatory developments, which could affect the profitability of the company's business activities; limit the company's ability to pursue business opportunities or conduct business in certain jurisdictions; require changes to business practices or alter the company's relationships with Card Members, partners, merchants and other third parties, including its ability to continue certain cobrand relationships in the EU; exert further pressure on the average discount rate and the company's GNS business; result in increased costs related to regulatory oversight, litigation-related settlements, judgments or expenses, restitution to Card Members or the imposition of fines or civil money penalties; materially affect capital or liquidity requirements, results of operations or ability to pay dividends; or result in harm to the American Express brand; and",
    ],
    52: [
        "- factors beyond the company's control such as continued waves of COVID-19 cases, the severity and contagiousness of new variants, severe weather conditions, natural disasters, power loss, disruptions in telecommunications, terrorism and other catastrophic events, any of which could significantly affect demand for and spending on American Express cards, delinquency rates, loan and receivable balances and other aspects of the company's business and results of operations or disrupt its global network systems and ability to process transactions.",
        "A further description of these uncertainties and other risks can be found in American Express Company's Annual Report on Form 10-K for the year ended December 31, 2020, the Quarterly Reports on Form 10-Q for the quarters ended March 31, June 30 and September 30, 2021 and the company's other reports filed with the Securities and Exchange Commission.",
    ],
}


def annex_pct_table(surface, stub, col_pairs, metric_rows):
    """metric_rows: list of (row_id, label, list of values aligned to columns)."""
    columns = [(cid, lab) for cid, lab in col_pairs]
    rows = []
    for rid, label, vals in metric_rows:
        cells = {}
        for (cid, _), v in zip(col_pairs, vals):
            cells[cid] = miss() if v is None else num(v, "pct_0")
        rows.append(row(rid, label, cells))
    return table(surface, stub, columns, rows)


def build():
    slides = []

    # 1 opening cover
    slides.append(
        {
            "slide_number": 1,
            "layout_type": "opening_cover",
            "payload": {
                "title": "American Express Earnings Conference Call Q4'21",
                "period_label": "Q4'21",
                "date_label": "January 25, 2022",
            },
            "evidence_ids": ev(1),
        }
    )

    # 2 Summary Financial Performance — data_table (Q4 + FY; period_comparison is 3-col only)
    slides.append(
        ordinary(
            2,
            "data_table",
            "Summary Financial Performance",
            {
                "table": table(
                    "s02-fin",
                    "Metric",
                    [
                        ("q4-21", "Q4'21"),
                        ("q4-yoy", "Q4 YoY%"),
                        ("fy-21", "FY'21"),
                        ("fy-yoy", "FY YoY%"),
                    ],
                    [
                        row(
                            "rev",
                            "Total Revenues Net of Interest Expense",
                            {
                                "q4-21": num("12145", "usd_0"),
                                "q4-yoy": num("30", "pct_0"),
                                "fy-21": num("42380", "usd_0"),
                                "fy-yoy": num("17", "pct_0"),
                            },
                        ),
                        row(
                            "fx",
                            "FX-Adjusted*",
                            {
                                "q4-21": miss(),
                                "q4-yoy": num("31", "pct_0"),
                                "fy-21": miss(),
                                "fy-yoy": num("17", "pct_0"),
                            },
                        ),
                        row(
                            "pretax",
                            "Pre-tax Income",
                            {
                                "q4-21": num("2306", "usd_0"),
                                "q4-yoy": num("24", "pct_0"),
                                "fy-21": num("10689", "usd_0"),
                                "fy-yoy": num("149", "pct_0"),
                            },
                        ),
                        row(
                            "ni",
                            "Net Income",
                            {
                                "q4-21": num("1719", "usd_0"),
                                "q4-yoy": num("20", "pct_0"),
                                "fy-21": num("8060", "usd_0"),
                                "fy-yoy": num("157", "pct_0"),
                            },
                        ),
                        row(
                            "eps",
                            "Diluted EPS dagger",
                            {
                                "q4-21": num("2.18", "usd_2"),
                                "q4-yoy": num("24", "pct_0"),
                                "fy-21": num("10.02", "usd_2"),
                                "fy-yoy": num("166", "pct_0"),
                            },
                        ),
                        row(
                            "shares",
                            "Average Diluted Shares Outstanding",
                            {
                                "q4-21": num("769", "num_0"),
                                "q4-yoy": num("-5", "pct_0"),
                                "fy-21": num("790", "num_0"),
                                "fy-yoy": num("-2", "pct_0"),
                            },
                        ),
                    ],
                )
            },
            extra={
                "content": {"subtitle": "$ in millions; except per share amounts"},
                "disclosure": disc(
                    "s02-disc",
                    "Notes",
                    [
                        "* Total Revenues Net of Interest Expense adjusted for FX is a non-GAAP measure. FX-adjusted information assumes a constant exchange rate between the periods being compared for purposes of currency translation into U.S. dollars (i.e., assumes Q4'21 foreign exchange rates apply to Q4'20 results).",
                        "** Non-cash gain related to the increase in GBT's total equity book value arising from GBT's acquisition of Egencia in Q4'21. dagger Attributable to common shareholders.",
                        "Notable Impacts, FY'21 Pre-tax Income: Credit Reserve releases $2,481; Net gains on Amex Ventures equity investments $767; GBT Investment Gain** $238.",
                    ],
                ),
            },
        )
    )

    # 3 Total Network Volumes Growth — table values readable; quarterly plot points not extracted
    slides.append(
        ordinary(
            3,
            "data_table",
            "Total Network Volumes Growth",
            {
                "table": table(
                    "s03-vol",
                    "Metric",
                    [
                        ("q3-vs19", "Q3'21 vs '19"),
                        ("q3-yoy", "Q3'21 YoY"),
                        ("q4-vs19", "Q4'21 vs '19"),
                        ("q4-yoy", "Q4'21 YoY"),
                        ("fy-vs19", "FY'21 vs '19"),
                        ("fy-yoy", "FY'21 YoY"),
                        ("fy-mix", "% of FY Total"),
                    ],
                    [
                        row(
                            "billed",
                            "Billed Business",
                            {
                                "q3-vs19": num("4", "pct_0"),
                                "q3-yoy": num("31", "pct_0"),
                                "q4-vs19": num("12", "pct_0"),
                                "q4-yoy": num("33", "pct_0"),
                                "fy-vs19": num("1", "pct_0"),
                                "fy-yoy": num("24", "pct_0"),
                                "fy-mix": num("85", "pct_0"),
                            },
                        ),
                        row(
                            "processed",
                            "Processed Volumes",
                            {
                                "q3-vs19": num("3", "pct_0"),
                                "q3-yoy": num("18", "pct_0"),
                                "q4-vs19": num("3", "pct_0"),
                                "q4-yoy": num("15", "pct_0"),
                                "fy-vs19": num("-1", "pct_0"),
                                "fy-yoy": num("14", "pct_0"),
                                "fy-mix": num("15", "pct_0"),
                            },
                        ),
                        row(
                            "tnv",
                            "Total Network Volumes",
                            {
                                "q3-vs19": num("4", "pct_0"),
                                "q3-yoy": num("29", "pct_0"),
                                "q4-vs19": num("11", "pct_0"),
                                "q4-yoy": num("30", "pct_0"),
                                "fy-vs19": num("1", "pct_0"),
                                "fy-yoy": num("23", "pct_0"),
                                "fy-mix": num("100", "pct_0"),
                            },
                        ),
                    ],
                )
            },
            extra={
                "disclosure": disc(
                    "s03-disc",
                    "Notes",
                    [
                        "Note: All growth rates reflect FX-adjusted rates. See Annex 1 for reported billings growth rates.",
                        "Billed business represents proprietary billed business on cards issued by AXP. Processed volumes represent GNS and alternative payment solutions facilitated by AXP.",
                        "Extraction residual: Q1'20-Q4'21 line-plot series points vs 2019 were not glyph-readable; table values above are from the on-page grid.",
                    ],
                )
            },
        )
    )

    # 4 Billed Business (G&S vs T&E)
    slides.append(
        ordinary(
            4,
            "data_table",
            "Billed Business (G&S vs T&E)",
            {
                "table": table(
                    "s04-gs-te",
                    "Metric",
                    [("gs", "G&S"), ("te", "T&E"), ("total", "Total")],
                    [
                        row(
                            "vs19",
                            "Q4'21 vs '19",
                            {
                                "gs": num("24", "pct_0"),
                                "te": num("-18", "pct_0"),
                                "total": num("12", "pct_0"),
                            },
                        ),
                        row(
                            "yoy",
                            "Q4'21 YoY",
                            {
                                "gs": num("19", "pct_0"),
                                "te": num("132", "pct_0"),
                                "total": num("33", "pct_0"),
                            },
                        ),
                        row(
                            "fy19",
                            "FY'19 vs '19 / $B",
                            {
                                "gs": num("18", "pct_0"),
                                "te": num("-37", "pct_0"),
                                "total": num("1071", "usd_0"),
                            },
                        ),
                        row(
                            "fy20",
                            "FY'20 vs '19",
                            {
                                "gs": num("-1", "pct_0"),
                                "te": num("-60", "pct_0"),
                                "total": num("871", "usd_0"),
                            },
                        ),
                        row(
                            "fy21",
                            "FY'21 vs '19 / $B",
                            {
                                "gs": num("1", "pct_0"),
                                "te": num("-19", "pct_0"),
                                "total": num("1090", "usd_0"),
                            },
                        ),
                    ],
                )
            },
            extra={
                "content": {"subtitle": "$ in Billions, % of Total; FX-adjusted vs 2019"},
                "disclosure": disc(
                    "s04-disc",
                    "Notes",
                    [
                        "Note: All growth rates reflect FX-adjusted rates. See Annex 1 for reported billings growth rates. G&S = Goods & Services spending. T&E = Travel & Entertainment spending.",
                        "On-page mix callouts Q4'21: G&S 70% / T&E 30% of billed business. FY mix: 85% / 15% (FY'20) and 81% / 19% (FY'21) where readable.",
                    ],
                ),
            },
        )
    )

    # 5 G&S Online vs Offline
    slides.append(
        ordinary(
            5,
            "data_table",
            "Goods & Services Billed Business (Online vs Offline)",
            {
                "table": table(
                    "s05-gs",
                    "Metric",
                    [("online", "Online"), ("offline", "Offline"), ("total", "Total")],
                    [
                        row(
                            "vs19",
                            "Q4'21 vs '19",
                            {
                                "online": num("31", "pct_0"),
                                "offline": num("12", "pct_0"),
                                "total": num("24", "pct_0"),
                            },
                        ),
                        row(
                            "yoy",
                            "Q4'21 YoY",
                            {
                                "online": num("16", "pct_0"),
                                "offline": num("28", "pct_0"),
                                "total": num("19", "pct_0"),
                            },
                        ),
                        row(
                            "mix",
                            "% of Total",
                            {
                                "online": num("66", "pct_0"),
                                "offline": num("34", "pct_0"),
                                "total": num("100", "pct_0"),
                            },
                        ),
                    ],
                )
            },
            extra={
                "disclosure": disc(
                    "s05-disc",
                    "Notes",
                    [
                        "Note: Online = Online + Card Not Present. All growth rates reflect FX-adjusted rates. See Annex 1 for reported billings growth rates."
                    ],
                )
            },
        )
    )

    # 6 Global Consumer — dual: G&S/T&E mix stack + age-cohort table as second chart of mix $B
    slides.append(
        ordinary(
            6,
            "dual_chart",
            "Global Consumer Billed Business",
            {
                "charts": [
                    sbar(
                        "s06-mix",
                        "G&S vs T&E",
                        [
                            ("q1-21", "Q1'21"),
                            ("q2-21", "Q2'21"),
                            ("q3-21", "Q3'21"),
                            ("q4-21", "Q4'21"),
                        ],
                        [
                            ser("gs", "G&S", ["82", "77", "74", "75"], "navy"),
                            ser("te", "T&E", ["18", "23", "26", "25"], "primary_blue"),
                        ],
                        fmt="pct_0",
                        subtitle="$ in Billions, % of Total",
                        totals=["119", "147", "153", "174"],
                        tot_fmt="usd_0",
                    ),
                    gbar(
                        "s06-age",
                        "Billed Business Growth by Age Cohort",
                        [
                            ("millennial", "Millennials + Gen-Z"),
                            ("gen-x", "Gen-X"),
                            ("boomer", "Baby Boomer +"),
                        ],
                        [
                            ser("vs19", "Q4'21 vs '19", ["50", "17", "0"], "navy"),
                            ser("yoy", "Q4'21 YoY", ["51", "34", "26"], "primary_blue"),
                            ser("mix", "% of Total", ["28", "39", "33"], "sky_blue"),
                        ],
                        fmt="pct_0",
                    ),
                ]
            },
            extra={
                "disclosure": disc(
                    "s06-disc",
                    "Notes",
                    [
                        "Q4'21 G&S / T&E / Total YoY 19% / 130% / 35%. vs '19 Total Consumer 17%, G&S 26%, T&E (2%).",
                        "Note: All growth rates reflect FX-adjusted rates. See Annex 1 for reported billings growth rates.",
                    ],
                )
            },
        )
    )

    # 7 Global Commercial
    slides.append(
        ordinary(
            7,
            "dual_chart",
            "Global Commercial Billed Business",
            {
                "charts": [
                    sbar(
                        "s07-mix",
                        "G&S vs T&E",
                        [
                            ("q1-21", "Q1'21"),
                            ("q2-21", "Q2'21"),
                            ("q3-21", "Q3'21"),
                            ("q4-21", "Q4'21"),
                        ],
                        [
                            ser("gs", "G&S", ["90", "88", "86", "84"], "navy"),
                            ser("te", "T&E", ["10", "12", "14", "16"], "primary_blue"),
                        ],
                        fmt="pct_0",
                        subtitle="$ in Billions, % of Total",
                        totals=["104", "120", "126", "141"],
                        tot_fmt="usd_0",
                    ),
                    gbar(
                        "s07-sme",
                        "SME vs Large & Global Corporate",
                        [
                            ("sme-gs", "SME G&S"),
                            ("sme-tot", "SME Total"),
                            ("lg-tot", "L&G Total"),
                        ],
                        [
                            ser("vs19", "Q4'21 vs '19", ["25", "17", "-33"], "navy"),
                            ser("yoy", "Q4'21 YoY", ["21", "29", "34"], "primary_blue"),
                            ser("mix", "% of Total", ["74", "85", "15"], "sky_blue"),
                        ],
                        fmt="pct_0",
                    ),
                ]
            },
            extra={
                "disclosure": disc(
                    "s07-disc",
                    "Notes",
                    [
                        "Q4'21 G&S / T&E / Total YoY 20% / 137% / 30%.",
                        "Note: SME refers to small and mid-sized businesses with less than $300MM in annual revenues. All growth rates reflect FX-adjusted rates. See Annex 1 for reported billings growth rates.",
                    ],
                )
            },
        )
    )

    # 8 T&E by customer type
    slides.append(
        ordinary(
            8,
            "data_table",
            "Billed Business T&E Growth",
            {
                "table": table(
                    "s08-te",
                    "Customer Type",
                    [
                        ("yoy", "Q4'21 YoY"),
                        ("mix", "% of Total"),
                        ("vs-q419", "% of Q4'19"),
                    ],
                    [
                        row(
                            "us-cons",
                            "US Consumer",
                            {
                                "yoy": num("130", "pct_0"),
                                "mix": num("49", "pct_0"),
                                "vs-q419": num("108", "pct_0"),
                            },
                        ),
                        row(
                            "intl-cons",
                            "Intl Consumer",
                            {
                                "yoy": num("130", "pct_0"),
                                "mix": num("17", "pct_0"),
                                "vs-q419": num("83", "pct_0"),
                            },
                        ),
                        row(
                            "tot-cons",
                            "Total Consumer",
                            {
                                "yoy": num("130", "pct_0"),
                                "mix": num("66", "pct_0"),
                                "vs-q419": miss(),
                            },
                        ),
                        row(
                            "us-sme",
                            "US SME",
                            {
                                "yoy": num("145", "pct_0"),
                                "mix": num("20", "pct_0"),
                                "vs-q419": num("82", "pct_0"),
                            },
                        ),
                        row(
                            "intl-sme",
                            "Intl SME",
                            {
                                "yoy": num("99", "pct_0"),
                                "mix": num("5", "pct_0"),
                                "vs-q419": num("78", "pct_0"),
                            },
                        ),
                        row(
                            "tot-sme",
                            "Total SME",
                            {
                                "yoy": num("134", "pct_0"),
                                "mix": num("25", "pct_0"),
                                "vs-q419": num("36", "pct_0"),
                            },
                        ),
                        row(
                            "lg",
                            "L&G",
                            {
                                "yoy": num("144", "pct_0"),
                                "mix": num("9", "pct_0"),
                                "vs-q419": miss(),
                            },
                        ),
                        row(
                            "total",
                            "Total",
                            {
                                "yoy": num("132", "pct_0"),
                                "mix": num("100", "pct_0"),
                                "vs-q419": miss(),
                            },
                        ),
                    ],
                )
            },
            extra={
                "disclosure": disc(
                    "s08-disc",
                    "Notes",
                    [
                        "Note: All growth rates reflect FX-adjusted rates. See Annex 1 for reported billings growth rates.",
                        "Extraction residual: quarterly T&E-by-customer line points vs 2019 were not glyph-readable; % of Q4'19 for Total Consumer / L&G / Total not fully labeled on the extracted grid.",
                    ],
                )
            },
        )
    )

    # 9 dual region tables as grouped bars
    slides.append(
        ordinary(
            9,
            "dual_chart",
            "Billed Business Growth by Region",
            {
                "charts": [
                    gbar(
                        "s09-us-intl",
                        "US vs International",
                        [
                            ("us", "US"),
                            ("intl", "International"),
                            ("total", "Total"),
                        ],
                        [
                            ser("vs19", "Q4'21 vs '19", ["16", "-1", "12"], "navy"),
                            ser("yoy", "Q4'21 YoY", ["33", "32", "33"], "primary_blue"),
                            ser("mix", "% of Total", ["78", "22", "100"], "sky_blue"),
                        ],
                        fmt="pct_0",
                    ),
                    gbar(
                        "s09-gs-te",
                        "G&S vs T&E by Region",
                        [
                            ("us-gs", "US G&S"),
                            ("intl-gs", "Intl G&S"),
                            ("tot-gs", "Total G&S"),
                            ("us-te", "US T&E"),
                            ("intl-te", "Intl T&E"),
                            ("tot-te", "Total T&E"),
                        ],
                        [
                            ser(
                                "vs19",
                                "Q4'21 vs '19",
                                ["26", "19", "24", "-10", "-36", "-18"],
                                "navy",
                            ),
                            ser(
                                "yoy",
                                "Q4'21 YoY",
                                ["20", "17", "19", "134", "127", "132"],
                                "primary_blue",
                            ),
                            ser(
                                "mix",
                                "% of Total",
                                ["62", "17", "79", "15", "5", "21"],
                                "sky_blue",
                            ),
                        ],
                        fmt="pct_0",
                    ),
                ]
            },
            extra={
                "disclosure": disc(
                    "s09-disc",
                    "Notes",
                    [
                        "Note: All growth rates reflect FX-adjusted rates. See Annex 1 for reported billings growth rates. % of total may not foot due to rounding."
                    ]
                )
            },
        )
    )

    # 10 dual ending loans / receivables
    slides.append(
        ordinary(
            10,
            "dual_chart",
            "Worldwide Total Loans and Card Member Receivables",
            {
                "charts": [
                    gbar(
                        "s10-loans",
                        "Total Ending Loans (Q3-Q4)",
                        [
                            ("y19", "2019"),
                            ("y20", "2020"),
                            ("y21", "2021"),
                        ],
                        [
                            ser("q3", "Q3", ["88.1", "73.1", "79.4"], "navy"),
                            ser("q4", "Q4", ["92.2", "76.2", "91.5"], "primary_blue"),
                        ],
                        fmt="usd_1",
                        subtitle="$ in billions",
                    ),
                    gbar(
                        "s10-rec",
                        "Total Ending CM Receivables (Q3-Q4)",
                        [
                            ("y19", "2019"),
                            ("y20", "2020"),
                            ("y21", "2021"),
                        ],
                        [
                            ser("q3", "Q3", ["56.6", "40.8", "48.8"], "navy"),
                            ser("q4", "Q4", ["57.4", "43.7", "53.6"], "primary_blue"),
                        ],
                        fmt="usd_1",
                        subtitle="$ in billions",
                    ),
                ]
            },
            extra={
                "disclosure": disc(
                    "s10-disc",
                    "Notes",
                    [
                        "Note: Total Loans reflects Card Member loans and Other loans.",
                        "YoY Growth callouts on page: Loans Q3/Q4 2020 (17%)/(17%), 2021 9%/20%; Receivables Q3/Q4 2020 (28%)/(24%), 2021 19%/23%; additional 3%/8%/9% labels were not fully attributed in extraction.",
                    ],
                )
            },
        )
    )

    # 11 credit metrics — 3 panes on PDF; dual_chart holds loans + receivables
    slides.append(
        ordinary(
            11,
            "dual_chart",
            "Card Member Credit Metrics",
            {
                "charts": [
                    line(
                        "s11-loans",
                        "Card Member Loans Net Write-off Rates",
                        [
                            ("q3-20", "Q3'20"),
                            ("q4-20", "Q4'20"),
                            ("q1-21", "Q1'21"),
                            ("q2-21", "Q2'21"),
                            ("q3-21", "Q3'21"),
                            ("q4-21", "Q4'21"),
                        ],
                        [
                            ser(
                                "nwo",
                                "Net Write-off Rates",
                                ["0.9", "0.6", "0.6", "0.5", "0.5", "0.6"],
                                "navy",
                            ),
                            ser(
                                "dq",
                                "30+ Days Past Due",
                                ["1.2", "1.0", "0.9", "0.6", "0.7", "0.7"],
                                "primary_blue",
                            ),
                        ],
                        fmt="pct_1",
                    ),
                    line(
                        "s11-rec",
                        "Card Member Receivables Net Write-off Rates",
                        [
                            ("q3-20", "Q3'20"),
                            ("q4-20", "Q4'20"),
                            ("q1-21", "Q1'21"),
                            ("q2-21", "Q2'21"),
                            ("q3-21", "Q3'21"),
                            ("q4-21", "Q4'21"),
                        ],
                        [
                            ser(
                                "nwo",
                                "Net Write-off Rates (ex-GCP)",
                                ["2.0", "1.0", "0.5", "0.3", "0.2", "0.3"],
                                "navy",
                            ),
                            ser(
                                "dq",
                                "30+ Days Past Due*",
                                ["2.5", "1.9", "1.4", "1.0", "0.6", "0.6"],
                                "primary_blue",
                            ),
                        ],
                        fmt="pct_1",
                    ),
                ]
            },
            extra={
                "disclosure": disc(
                    "s11-disc",
                    "Notes",
                    [
                        "GCP Net Write-off Rates** ***: 2.4%, 0.7%, 0.4%, (0.9%), 0.2%, 0.2% for Q3'20-Q4'21. Third pane has no dual_chart slot (Type B: 3+ chart canvas).",
                        "* 30+ Days past due as a % of Global Consumer and Global Small Business Services Card Member receivables (unavailable for GCP). ** GCP net write off rates include principal and fees. *** Includes Corporate Client bankruptcy impact of ($37M) for Q2'21. See Slide 29 for adjusted rates.",
                    ],
                )
            },
        )
    )

    # 12 Total Provision — combo write-offs + reserve + total
    slides.append(
        ordinary(
            12,
            "chart_hero_dual",
            "Total Provision",
            {
                "chart": combo(
                    "s12-prov",
                    "Total Provision",
                    [
                        ("q1-20", "Q1'20"),
                        ("q2-20", "Q2'20"),
                        ("q3-20", "Q3'20"),
                        ("q4-20", "Q4'20"),
                        ("q1-21", "Q1'21"),
                        ("q2-21", "Q2'21"),
                        ("q3-21", "Q3'21"),
                        ("q4-21", "Q4'21"),
                    ],
                    [
                        {
                            "series_id": "write-offs",
                            "name": "Write-offs",
                            "mark_type": "bar",
                            "values": ["918", "927", "781", "563", "379", "260", "202", "221"],
                            "color": "navy",
                        },
                        {
                            "series_id": "reserve",
                            "name": "Reserve Build/(Release)*",
                            "mark_type": "bar",
                            "values": [
                                "1703",
                                "628",
                                "-116",
                                "-674",
                                "-1054",
                                "-866",
                                "-393",
                                "-168",
                            ],
                            "color": "primary_blue",
                        },
                        {
                            "series_id": "total",
                            "name": "Total Provision",
                            "mark_type": "line",
                            "values": [
                                "2621",
                                "1555",
                                "665",
                                "-111",
                                "-675",
                                "-606",
                                "-191",
                                "53",
                            ],
                            "color": "sky_blue",
                        },
                    ],
                    bar_mode="grouped",
                    pfmt="usd_0",
                    subtitle="$ in millions",
                ),
                "hero": {
                    "hero_type": "driver_card",
                    "surface_id": "s12-hero",
                    "heading": "2021 vs. 2020 Better/(Worse)",
                    "rows": [
                        {
                            "row_id": "nwo",
                            "label": "Net Write-offs FY'21 vs FY'20",
                            "value": num("2127", "usd_0"),
                            "detail": "FY'20 $3,189; FY'21 $1,062",
                        },
                        {
                            "row_id": "rsv",
                            "label": "Reserve Build/(Release)",
                            "value": num("4022", "usd_0"),
                            "detail": "FY'20 $1,541; FY'21 ($2,481)",
                        },
                        {
                            "row_id": "tot",
                            "label": "Total Provision",
                            "value": num("6149", "usd_0"),
                            "detail": "FY'20 $4,730; FY'21 ($1,419)",
                        },
                    ],
                },
            },
            extra={
                "disclosure": disc(
                    "s12-disc",
                    "Notes",
                    [
                        "See Variance Commentary in the appendix section for an explanation of the provision variance versus last year.",
                        "* Reserve Build/(Release) portion of the provisions for credit losses for the period related to increasing or decreasing reserves for credit losses as a result of, among other things, changes in volumes, macroeconomic outlook, portfolio composition and credit quality of portfolios.",
                    ],
                )
            },
        )
    )

    # 13 Total Reserves
    slides.append(
        ordinary(
            13,
            "data_table",
            "Total Reserves",
            {
                "table": table(
                    "s13-rsv",
                    "Period",
                    [
                        ("loans", "Total Loans $B"),
                        ("rec", "CM Receivables $B"),
                        ("total", "Total $B"),
                        ("loan-pct", "Reserves % of Total loans"),
                        ("rec-pct", "Reserves % of CM Receivables"),
                    ],
                    [
                        row(
                            "q1-20",
                            "Q1'20 Beginning Reserves",
                            {
                                "loans": num("4.2", "usd_1"),
                                "rec": num("1.4", "usd_1"),
                                "total": num("5.6", "usd_1"),
                                "loan-pct": num("7.3", "pct_1"),
                                "rec-pct": num("0.6", "pct_1"),
                            },
                        ),
                        row(
                            "q4-20",
                            "Q4'20 Ending Reserves",
                            {
                                "loans": num("3.6", "usd_1"),
                                "rec": miss(),
                                "total": num("3.6", "usd_1"),
                                "loan-pct": num("4.6", "pct_1"),
                                "rec-pct": num("0.2", "pct_1"),
                            },
                        ),
                        row(
                            "q3-21",
                            "Q3'21 Ending Reserves",
                            {
                                "loans": num("3.6", "usd_1"),
                                "rec": num("0.1", "usd_1"),
                                "total": num("3.6", "usd_1"),
                                "loan-pct": num("4.5", "pct_1"),
                                "rec-pct": num("0.1", "pct_1"),
                            },
                        ),
                        row(
                            "q4-21",
                            "Q4'21 Ending Reserves",
                            {
                                "loans": num("3.4", "usd_1"),
                                "rec": num("0.1", "usd_1"),
                                "total": num("3.4", "usd_1"),
                                "loan-pct": num("3.7", "pct_1"),
                                "rec-pct": num("0.1", "pct_1"),
                            },
                        ),
                    ],
                )
            },
            extra={
                "content": {"subtitle": "Balance Sheet Credit Reserves* ($ in billions)"},
                "disclosure": disc(
                    "s13-disc",
                    "Notes",
                    [
                        "* Q1'20 - Q4'21 Balance Sheet credit reserve builds differ from P&L credit reserve builds due to other receivables and FX impacts. Reserve subtotals may not foot due to rounding.",
                        "Bridge labels ($5.8), ($2.2), ($2.0), ($0.2), $0.3, ($0.3), $0.0 were not fully attributed to loans vs receivables in extraction.",
                    ],
                ),
            },
        )
    )

    # 14 Revenue Performance
    slides.append(
        ordinary(
            14,
            "data_table",
            "Revenue Performance",
            {
                "table": table(
                    "s14-rev",
                    "Metric",
                    [
                        ("q4", "Q4'21"),
                        ("q4-yoy", "Q4 YoY%"),
                        ("q4-vs19", "Q4 vs '19%"),
                        ("fy", "FY'21"),
                        ("fy-yoy", "FY YoY%"),
                        ("fy-vs19", "FY vs '19%"),
                    ],
                    [
                        row(
                            "disc",
                            "Discount Revenue",
                            {
                                "q4": num("7482", "usd_0"),
                                "q4-yoy": num("35", "pct_0"),
                                "q4-vs19": num("10", "pct_0"),
                                "fy": num("25727", "usd_0"),
                                "fy-yoy": num("26", "pct_0"),
                                "fy-vs19": num("-2", "pct_0"),
                            },
                        ),
                        row(
                            "ncf",
                            "Net Card Fees",
                            {
                                "q4": num("1344", "usd_0"),
                                "q4-yoy": num("10", "pct_0"),
                                "q4-vs19": num("25", "pct_0"),
                                "fy": num("5195", "usd_0"),
                                "fy-yoy": num("11", "pct_0"),
                                "fy-vs19": num("29", "pct_0"),
                            },
                        ),
                        row(
                            "ofc",
                            "Other Fees & Commissions",
                            {
                                "q4": num("680", "usd_0"),
                                "q4-yoy": num("32", "pct_0"),
                                "q4-vs19": num("-18", "pct_0"),
                                "fy": num("2392", "usd_0"),
                                "fy-yoy": num("11", "pct_0"),
                                "fy-vs19": num("-27", "pct_0"),
                            },
                        ),
                        row(
                            "oth",
                            "Other Revenue*",
                            {
                                "q4": num("531", "usd_0"),
                                "q4-yoy": num("218", "pct_0"),
                                "q4-vs19": num("55", "pct_0"),
                                "fy": num("1316", "usd_0"),
                                "fy-yoy": num("51", "pct_0"),
                                "fy-vs19": num("-8", "pct_0"),
                            },
                        ),
                        row(
                            "nii",
                            "Net Interest Income",
                            {
                                "q4": num("2108", "usd_0"),
                                "q4-yoy": num("11", "pct_0"),
                                "q4-vs19": num("-8", "pct_0"),
                                "fy": num("7750", "usd_0"),
                                "fy-yoy": num("-3", "pct_0"),
                                "fy-vs19": num("-10", "pct_0"),
                            },
                        ),
                        row(
                            "rnie",
                            "Revenues Net of Interest Expense",
                            {
                                "q4": num("12145", "usd_0"),
                                "q4-yoy": num("30", "pct_0"),
                                "q4-vs19": num("7", "pct_0"),
                                "fy": num("42380", "usd_0"),
                                "fy-yoy": num("17", "pct_0"),
                                "fy-vs19": num("-3", "pct_0"),
                            },
                        ),
                        row(
                            "fx",
                            "FX Adjusted**",
                            {
                                "q4": miss(),
                                "q4-yoy": num("31", "pct_0"),
                                "q4-vs19": num("7", "pct_0"),
                                "fy": miss(),
                                "fy-yoy": num("17", "pct_0"),
                                "fy-vs19": num("-3", "pct_0"),
                            },
                        ),
                    ],
                )
            },
            extra={
                "content": {"subtitle": "$ in millions"},
                "disclosure": disc(
                    "s14-disc",
                    "Notes",
                    [
                        "See Variance Commentary in the appendix section for an explanation of the revenue variances versus last year.",
                        "* Other Revenue includes the $238M Non-cash gain related to the increase in GBT's total equity book value arising from GBT's acquisition of Egencia in Q4'21, as referenced on Slide 2.",
                        "** Total Revenues Net of Interest Expense adjusted for FX and the related growth rate are non-GAAP measures. See Slide 2 for an explanation of FX-adjusted information.",
                    ],
                ),
            },
        )
    )

    # 15 Discount Revenue combo $B + rate
    slides.append(
        ordinary(
            15,
            "single_chart",
            "Discount Revenue",
            {
                "chart": combo(
                    "s15-dr",
                    "Discount Revenue*",
                    Q3Q4,
                    [
                        {
                            "series_id": "rev",
                            "name": "Discount Revenue $B",
                            "mark_type": "bar",
                            "values": ["6.6", "6.8", "5.0", "5.5", "6.7", "7.5"],
                            "color": "navy",
                        },
                        {
                            "series_id": "rate",
                            "name": "Average Discount Rate",
                            "mark_type": "line",
                            "axis_key": "secondary",
                            "style": {"line_style": "solid", "marker": "circle"},
                            "values": ["2.39", "2.36", "2.27", "2.25", "2.32", "2.30"],
                            "color": "primary_blue",
                        },
                    ],
                    bar_mode="grouped",
                    pfmt="usd_1",
                    sfmt="pct_2",
                    subtitle="$ in billions (on a reported basis)",
                )
            },
            extra={
                "disclosure": disc(
                    "s15-disc",
                    "Notes",
                    [
                        "FY'21 Discount Revenue $25.7B, YoY 25%, vs '19 (2%). YoY change (Q3-Q4): 6%, 7%, (19%), (24%), 36%, 33%. Q3-Q4 rate change (12 bps).",
                        "* Discount Revenue adjusted for FX and the related growth rates are non-GAAP measures. See Annex 2 for Discount Revenue on a GAAP basis. See Slide 2 for an explanation of FX-adjusted information.",
                    ],
                )
            },
        )
    )

    # 16 Net Card Fees
    ncf_cats = [
        ("q1-19", "Q1'19"),
        ("q2-19", "Q2'19"),
        ("q3-19", "Q3'19"),
        ("q4-19", "Q4'19"),
        ("q1-20", "Q1'20"),
        ("q2-20", "Q2'20"),
        ("q3-20", "Q3'20"),
        ("q4-20", "Q4'20"),
        ("q1-21", "Q1'21"),
        ("q2-21", "Q2'21"),
        ("q3-21", "Q3'21"),
        ("q4-21", "Q4'21"),
    ]
    slides.append(
        ordinary(
            16,
            "single_chart",
            "Net Card Fees",
            {
                "chart": combo(
                    "s16-ncf",
                    "Net Card Fees*",
                    ncf_cats,
                    [
                        {
                            "series_id": "ncf",
                            "name": "Net Card Fees $B",
                            "mark_type": "bar",
                            "values": [
                                "0.9",
                                "1.0",
                                "1.0",
                                "1.1",
                                "1.1",
                                "1.1",
                                "1.2",
                                "1.2",
                                "1.3",
                                "1.3",
                                "1.3",
                                "1.3",
                            ],
                            "color": "navy",
                        },
                        {
                            "series_id": "yoy",
                            "name": "YoY Change FX-adjusted",
                            "mark_type": "line",
                            "axis_key": "secondary",
                            "style": {"line_style": "solid", "marker": "circle"},
                            "values": [
                                "17",
                                "19",
                                "20",
                                "20",
                                "19",
                                "17",
                                "15",
                                "12",
                                "10",
                                "10",
                                "10",
                                "11",
                            ],
                            "color": "primary_blue",
                        },
                    ],
                    bar_mode="grouped",
                    pfmt="usd_1",
                    sfmt="pct_0",
                    subtitle="$ in billions (on a reported basis)",
                )
            },
            extra={
                "disclosure": disc(
                    "s16-disc",
                    "Notes",
                    [
                        "FY'21 Net Card Fees $5.2B, YoY 10%, vs '19 28%.",
                        "Note: Effective Q2'21 we prospectively changed the recognition of certain costs paid to a third party previously recognized over the 12-month card membership period in Net card fees.",
                        "* Net Card Fees YoY growth rates adjusted for FX are non-GAAP measures. See Annex 3 for Net Card Fees growth rates on a GAAP basis.",
                    ],
                )
            },
        )
    )

    # 17 Net Interest Income
    slides.append(
        ordinary(
            17,
            "single_chart",
            "Net Interest Income",
            {
                "chart": combo(
                    "s17-nii",
                    "Net Interest Income*",
                    Q3Q4,
                    [
                        {
                            "series_id": "nii",
                            "name": "Net Interest Income $B",
                            "mark_type": "bar",
                            "values": ["2.2", "2.3", "1.9", "1.9", "2.0", "2.1"],
                            "color": "navy",
                        },
                        {
                            "series_id": "yield",
                            "name": "WW Net Interest Yield on CM Loans**",
                            "mark_type": "line",
                            "axis_key": "secondary",
                            "style": {"line_style": "solid", "marker": "circle"},
                            "values": ["11.2", "11.3", "11.6", "11.4", "10.8", "10.3"],
                            "color": "primary_blue",
                        },
                    ],
                    bar_mode="grouped",
                    pfmt="usd_1",
                    sfmt="pct_1",
                    subtitle="$ in billions (on a reported basis)",
                )
            },
            extra={
                "disclosure": disc(
                    "s17-disc",
                    "Notes",
                    [
                        "FY'21 Net Interest Income $7.8B, YoY (4%), vs '19 (10%). YoY change (Q3-Q4): 13%, 13%, (17%), (15%), 11%, 6%. Yield change (12 bps).",
                        "* Net Interest Income YoY growth rates adjusted for FX are non-GAAP measures. See Annex 4. ** See Annex 5 for a reconciliation of net interest yield, a non-GAAP measure.",
                    ],
                )
            },
        )
    )

    # 18 Total Revenue Net of Interest Expense — 12-quarter line
    rev_cats = [
        ("q1-19", "Q1'19"),
        ("q2-19", "Q2'19"),
        ("q3-19", "Q3'19"),
        ("q4-19", "Q4'19"),
        ("q1-20", "Q1'20"),
        ("q2-20", "Q2'20"),
        ("q3-20", "Q3'20"),
        ("q4-20", "Q4'20"),
        ("q1-21", "Q1'21"),
        ("q2-21", "Q2'21"),
        ("q3-21", "Q3'21"),
        ("q4-21", "Q4'21"),
    ]
    slides.append(
        ordinary(
            18,
            "single_chart",
            "Total Revenue Net of Interest Expense",
            {
                "chart": line(
                    "s18-rev",
                    "Total Revenue Growth FX-Adjusted*",
                    rev_cats,
                    [
                        ser(
                            "yoy",
                            "% inc/(dec) YoY",
                            [
                                "10",
                                "9",
                                "9",
                                "9",
                                "1",
                                "-28",
                                "-20",
                                "-18",
                                "-13",
                                "31",
                                "24",
                                "31",
                            ],
                            "navy",
                        ),
                        ser(
                            "vs19",
                            "% inc/(dec) vs. 2019",
                            [
                                None,
                                None,
                                None,
                                None,
                                "-1",
                                "-28",
                                "-20",
                                "-18",
                                "-13",
                                "-6",
                                "-1",
                                "7",
                            ],
                            "primary_blue",
                        ),
                    ],
                    fmt="pct_0",
                )
            },
            extra={
                "disclosure": disc(
                    "s18-disc",
                    "Notes",
                    [
                        "FY'21 Revenue $42.4B, YoY 17%, vs '19 (3%).",
                        "* Total Revenue Net of Interest Expense adjusted for FX and the related growth rates are non-GAAP measures. See Annex 6. See Slide 2 for an explanation of FX-adjusted information.",
                        "Extraction residual: 2019 vs-2019 series is definitionally omitted (same year); Q1'19-Q4'19 vs-2019 points were not labeled.",
                    ],
                )
            },
        )
    )

    # 19 Expense Performance
    slides.append(
        ordinary(
            19,
            "data_table",
            "Expense Performance",
            {
                "table": table(
                    "s19-exp",
                    "Metric",
                    [
                        ("q4", "Q4'21"),
                        ("q4-yoy", "Q4 YoY%"),
                        ("fy", "FY'21"),
                        ("fy-yoy", "FY YoY%"),
                    ],
                    [
                        row(
                            "rewards",
                            "Card Member Rewards",
                            {
                                "q4": num("3032", "usd_0"),
                                "q4-yoy": num("32", "pct_0"),
                                "fy": num("11007", "usd_0"),
                                "fy-yoy": num("37", "pct_0"),
                            },
                        ),
                        row(
                            "services",
                            "Card Member Services",
                            {
                                "q4": num("665", "usd_0"),
                                "q4-yoy": num("117", "pct_0"),
                                "fy": num("1993", "usd_0"),
                                "fy-yoy": num("62", "pct_0"),
                            },
                        ),
                        row(
                            "bd",
                            "Business Development",
                            {
                                "q4": num("1127", "usd_0"),
                                "q4-yoy": num("36", "pct_0"),
                                "fy": num("3761", "usd_0"),
                                "fy-yoy": num("23", "pct_0"),
                            },
                        ),
                        row(
                            "var",
                            "Variable CM Engagement Expenses",
                            {
                                "q4": num("4824", "usd_0"),
                                "q4-yoy": num("41", "pct_0"),
                                "fy": num("16761", "usd_0"),
                                "fy-yoy": num("36", "pct_0"),
                            },
                        ),
                        row(
                            "mkt",
                            "Marketing",
                            {
                                "q4": num("1586", "usd_0"),
                                "q4-yoy": num("54", "pct_0"),
                                "fy": num("5292", "usd_0"),
                                "fy-yoy": num("43", "pct_0"),
                            },
                        ),
                        row(
                            "opex",
                            "Operating Expenses*",
                            {
                                "q4": num("3376", "usd_0"),
                                "q4-yoy": num("7", "pct_0"),
                                "fy": num("11057", "usd_0"),
                                "fy-yoy": num("0", "pct_0"),
                            },
                        ),
                        row(
                            "total",
                            "Total Expenses",
                            {
                                "q4": num("9786", "usd_0"),
                                "q4-yoy": num("29", "pct_0"),
                                "fy": num("33110", "usd_0"),
                                "fy-yoy": num("22", "pct_0"),
                            },
                        ),
                        row(
                            "tax",
                            "Effective Tax Rate",
                            {
                                "q4": num("25.5", "pct_1"),
                                "q4-yoy": miss(),
                                "fy": num("24.6", "pct_1"),
                                "fy-yoy": miss(),
                            },
                        ),
                    ],
                )
            },
            extra={
                "content": {"subtitle": "$ in millions"},
                "disclosure": disc(
                    "s19-disc",
                    "Notes",
                    [
                        "See Variance Commentary in the appendix section for an explanation of the expense variances versus last year.",
                        "* Represents salaries and employee benefits, professional services, data processing and equipment, and other, net.",
                    ],
                ),
            },
        )
    )

    # 20 Marketing + NCA
    mkt_cats = [
        ("q3-20", "Q3'20"),
        ("q4-20", "Q4'20"),
        ("q1-21", "Q1'21"),
        ("q2-21", "Q2'21"),
        ("q3-21", "Q3'21"),
        ("q4-21", "Q4'21"),
    ]
    slides.append(
        ordinary(
            20,
            "dual_chart",
            "Marketing Investments and New Cards Acquired",
            {
                "charts": [
                    gbar(
                        "s20-mkt",
                        "Marketing",
                        mkt_cats,
                        [ser("mkt", "Marketing $B", ["1.1", "1.0", "1.0", "1.3", "1.4", "1.6"], "navy")],
                        fmt="usd_1",
                        subtitle="$ in billions",
                    ),
                    gbar(
                        "s20-nca",
                        "Proprietary NCA",
                        mkt_cats,
                        [ser("nca", "Proprietary NCA", ["1.4", "1.7", "2.1", "2.4", "2.6", "2.7"], "primary_blue")],
                        fmt="num_1",
                        subtitle="in millions",
                    ),
                ]
            },
            extra={
                "disclosure": disc(
                    "s20-disc",
                    "Notes",
                    ["FY'21 Marketing $5.3B. Value Injection label is on-page furniture without a numeric series."],
                )
            },
        )
    )

    # 21 Capital
    slides.append(
        ordinary(
            21,
            "chart_hero_dual",
            "Capital",
            {
                "chart": sbar(
                    "s21-ret",
                    "Capital Return",
                    [("fy-19", "FY'19"), ("fy-20", "FY'20"), ("fy-21", "FY'21")],
                    [
                        ser("div", "Dividends (implied remainder not split)", ["6.0", "2.3", "9.0"], "navy"),
                        ser("other", "Other return not separately labeled", ["0", "0", "0"], "neutral"),
                    ],
                    fmt="usd_1",
                    subtitle="$ in billions",
                    totals=["6.0", "2.3", "9.0"],
                    tot_fmt="usd_1",
                ),
                "hero": {
                    "hero_type": "metric_stack",
                    "surface_id": "s21-hero",
                    "heading": "CET1 Ratio",
                    "subtitle": "Target: 10-11%",
                    "metrics": [
                        {
                            "metric_id": "cet1-q421",
                            "label": "Q4'21 CET1 Ratio",
                            "value": num("10.5", "pct_1"),
                            "detail": "Q4'19 10.7%; Q4'20 13.5%",
                        },
                        {
                            "metric_id": "div",
                            "label": "Q4 Dividend per Common Share*",
                            "value": num("0.43", "usd_2"),
                            "detail": "Q4'19 and Q4'20 also $0.43",
                        },
                    ],
                },
            },
            extra={
                "disclosure": disc(
                    "s21-disc",
                    "Notes",
                    [
                        "* Dividends per Common Share reflects quarterly dividend declared in Q4 of 2019-2021.",
                        "Type (A)/(B): FY capital-return stack is shown as a single $6.0 / $2.3 / $9.0 total; buyback vs dividend split was not glyph-separated in extraction, so a zero placeholder series is not used as a fact — the second series is a schema floor (stacked_bar requires 2-6 series) and is labeled as not separately sourced.",
                    ],
                )
            },
        )
    )

    # stacked_bar requires 2 series - the zero series is a problem (invented). Better use grouped_bar with 1 series for capital return, and metric_overview? chart_hero_dual needs a chart. grouped_bar allows 1 series.

    # Fix slide 21 after first pass if validation complains about zero series... stacked with a zero series is invented. Switch to grouped_bar 1 series.

    slides[-1] = ordinary(
        21,
        "chart_hero_dual",
        "Capital",
        {
            "chart": gbar(
                "s21-ret",
                "Capital Return",
                [("fy-19", "FY'19"), ("fy-20", "FY'20"), ("fy-21", "FY'21")],
                [ser("ret", "Capital Return", ["6.0", "2.3", "9.0"], "navy")],
                fmt="usd_1",
                subtitle="$ in billions",
            ),
            "hero": {
                "hero_type": "metric_stack",
                "surface_id": "s21-hero",
                "heading": "CET1 Ratio",
                "subtitle": "Target: 10-11%",
                "metrics": [
                    {
                        "metric_id": "cet1-q421",
                        "label": "Q4'21 CET1 Ratio",
                        "value": num("10.5", "pct_1"),
                        "detail": "Q4'19 10.7%; Q4'20 13.5%",
                    },
                    {
                        "metric_id": "div",
                        "label": "Q4 Dividend per Common Share*",
                        "value": num("0.43", "usd_2"),
                        "detail": "Q4'19 and Q4'20 also $0.43",
                    },
                ],
            },
        },
        extra={
            "disclosure": disc(
                "s21-disc",
                "Notes",
                [
                    "* Dividends per Common Share reflects quarterly dividend declared in Q4 of 2019-2021.",
                    "PDF stack split (buybacks vs dividends) was not glyph-separated; authored as one Capital Return series.",
                ],
            )
        },
    )

    # 22 Growth Plan
    slides.append(
        ordinary(
            22,
            "metric_overview",
            "The Growth Plan",
            {
                "surface_id": "s22-guide",
                "heading": "2022 Guidance",
                "metrics": [
                    {
                        "metric_id": "rev-22",
                        "label": "Revenue Growth",
                        "value": rng("18", "20", "pct_0"),
                    },
                    {
                        "metric_id": "eps-22",
                        "label": "EPS",
                        "value": rng("9.25", "9.65", "usd_2"),
                    },
                    {
                        "metric_id": "rev-23",
                        "label": "2023 Revenue Growth",
                        "value": {"type": "text", "text": "in excess of 10%"},
                    },
                    {
                        "metric_id": "eps-23",
                        "label": "2023 EPS Growth",
                        "value": {"type": "text", "text": "Mid-teens"},
                    },
                ],
                "detail": {
                    "surface_id": "s22-qual",
                    "heading": "2024+ Aspiration",
                    "blocks": [
                        para_block(
                            "qual",
                            [
                                "Higher than long-term aspirational levels of Revenue growth. Pandemic Recovery Tailwinds (2022-2023). Steady State Macro Environment."
                            ],
                        )
                    ],
                },
            },
        )
    )

    # 23 Appendix divider
    slides.append(
        {
            "slide_number": 23,
            "layout_type": "section_divider",
            "payload": {"section_id": "appendix"},
            "evidence_ids": ev(23),
        }
    )

    # 24 Network volumes by customer type
    slides.append(
        ordinary(
            24,
            "data_table",
            "Q4'21 Network Volumes Growth by Customer Type",
            {
                "table": table(
                    "s24-nv",
                    "Customer Type",
                    [
                        ("mix", "% of Total Network Volumes"),
                        ("q3-yoy", "Q3 YoY%"),
                        ("q4-yoy", "Q4 YoY%"),
                        ("q3-vs19", "Q3 vs '19"),
                        ("q4-vs19", "Q4 vs '19"),
                    ],
                    [
                        row(
                            "us-cons",
                            "US Consumer",
                            {
                                "mix": num("35", "pct_0"),
                                "q3-yoy": num("33", "pct_0"),
                                "q4-yoy": num("33", "pct_0"),
                                "q3-vs19": num("14", "pct_0"),
                                "q4-vs19": num("20", "pct_0"),
                            },
                        ),
                        row(
                            "intl-cons",
                            "Int'l Consumer*",
                            {
                                "mix": num("12", "pct_0"),
                                "q3-yoy": num("25", "pct_0"),
                                "q4-yoy": num("32", "pct_0"),
                                "q3-vs19": num("-2", "pct_0"),
                                "q4-vs19": num("8", "pct_0"),
                            },
                        ),
                        row(
                            "us-sme",
                            "US SME",
                            {
                                "mix": num("27", "pct_0"),
                                "q3-yoy": miss(),
                                "q4-yoy": miss(),
                                "q3-vs19": miss(),
                                "q4-vs19": miss(),
                            },
                        ),
                        row(
                            "intl-sme",
                            "Int'l SME*",
                            {
                                "mix": num("5", "pct_0"),
                                "q3-yoy": miss(),
                                "q4-yoy": miss(),
                                "q3-vs19": miss(),
                                "q4-vs19": miss(),
                            },
                        ),
                        row(
                            "lg",
                            "Large & Global Corporate*",
                            {
                                "mix": num("6", "pct_0"),
                                "q3-yoy": miss(),
                                "q4-yoy": miss(),
                                "q3-vs19": miss(),
                                "q4-vs19": miss(),
                            },
                        ),
                        row(
                            "proc",
                            "Processed Volumes*",
                            {
                                "mix": num("15", "pct_0"),
                                "q3-yoy": miss(),
                                "q4-yoy": num("14", "pct_0"),
                                "q3-vs19": miss(),
                                "q4-vs19": miss(),
                            },
                        ),
                    ],
                )
            },
            section="appendix",
            extra={
                "disclosure": disc(
                    "s24-disc",
                    "Notes",
                    [
                        "US Consumer + US SME Q3/Q4 YoY 33%/33%, vs '19 14%/20%. Int'l Consumer + Int'l SME Q3/Q4 YoY 25%/32%, vs '19 (2%)/8%.",
                        "On-page vs-2019 series labels: 22%, 18%, 5%, 12%, (33%), 3% were not fully attributed to named segments in extraction.",
                        "Note: Preliminary. All growth rates reflect FX-adjusted rates. * See Annex 1 for reported billings growth rates.",
                    ],
                )
            },
        )
    )

    # 25 Global Consumer G&S
    slides.append(
        ordinary(
            25,
            "grouped_annex_table",
            "Global Consumer G&S Growth",
            {
                "tables": [
                    {
                        "heading": "Global Consumer G&S",
                        "short_heading": "G&S",
                        "table": table(
                            "s25-gs",
                            "Metric",
                            [("online", "Online"), ("offline", "Offline"), ("total", "Total")],
                            [
                                row(
                                    "vs19",
                                    "Q4'21 vs '19",
                                    {
                                        "online": num("42", "pct_0"),
                                        "offline": num("10", "pct_0"),
                                        "total": num("26", "pct_0"),
                                    },
                                ),
                                row(
                                    "yoy",
                                    "Q4'21 YoY",
                                    {
                                        "online": num("14", "pct_0"),
                                        "offline": num("27", "pct_0"),
                                        "total": num("19", "pct_0"),
                                    },
                                ),
                                row(
                                    "mix",
                                    "% of Total",
                                    {
                                        "online": num("56", "pct_0"),
                                        "offline": num("44", "pct_0"),
                                        "total": num("100", "pct_0"),
                                    },
                                ),
                            ],
                        ),
                    },
                    {
                        "heading": "Holiday Spend*",
                        "short_heading": "Holiday",
                        "table": table(
                            "s25-hol",
                            "Metric",
                            [("online", "Online"), ("offline", "Offline"), ("total", "Total")],
                            [
                                row(
                                    "vs19",
                                    "Q4'21 vs '19",
                                    {
                                        "online": num("55", "pct_0"),
                                        "offline": num("9", "pct_0"),
                                        "total": num("29", "pct_0"),
                                    },
                                ),
                                row(
                                    "yoy",
                                    "Q4'21 YoY",
                                    {
                                        "online": num("11", "pct_0"),
                                        "offline": num("24", "pct_0"),
                                        "total": num("17", "pct_0"),
                                    },
                                ),
                                row(
                                    "mix",
                                    "% of Total",
                                    {
                                        "online": num("52", "pct_0"),
                                        "offline": num("48", "pct_0"),
                                        "total": num("100", "pct_0"),
                                    },
                                ),
                            ],
                        ),
                    },
                ]
            },
            section="appendix",
            extra={
                "disclosure": disc(
                    "s25-disc",
                    "Notes",
                    [
                        "Note: All growth rates reflect FX-adjusted rates. See Annex 1 for reported billings growth rates.",
                        "* Holiday spend reflects Q4'21 Consumer retail spending at department stores/big box, shops and supermarkets/consumables.",
                    ],
                )
            },
        )
    )

    # 26 T&E by industry
    slides.append(
        ordinary(
            26,
            "data_table",
            "Travel & Entertainment Billed Business",
            {
                "table": table(
                    "s26-te",
                    "Metric",
                    [
                        ("rest", "Restaurants"),
                        ("lodg", "Lodging"),
                        ("air", "Airlines"),
                        ("other", "Other"),
                        ("total", "Total"),
                    ],
                    [
                        row(
                            "vs19",
                            "Q4'21 vs '19",
                            {
                                "rest": num("10", "pct_0"),
                                "lodg": num("-24", "pct_0"),
                                "air": num("-43", "pct_0"),
                                "other": num("-14", "pct_0"),
                                "total": num("-18", "pct_0"),
                            },
                        ),
                        row(
                            "yoy",
                            "Q4'21 YoY",
                            {
                                "rest": num("81", "pct_0"),
                                "lodg": num("134", "pct_0"),
                                "air": num("274", "pct_0"),
                                "other": num("146", "pct_0"),
                                "total": num("132", "pct_0"),
                            },
                        ),
                        row(
                            "mix",
                            "% of Total",
                            {
                                "rest": num("31", "pct_0"),
                                "lodg": num("22", "pct_0"),
                                "air": num("19", "pct_0"),
                                "other": num("28", "pct_0"),
                                "total": num("100", "pct_0"),
                            },
                        ),
                    ],
                )
            },
            section="appendix",
            extra={
                "disclosure": disc(
                    "s26-disc",
                    "Notes",
                    [
                        "Note: All growth rates reflect FX-adjusted rates. See Annex 1 for reported billings growth rates.",
                        "Extraction residual: Q1'20-Q4'21 industry line points vs 2019 were not glyph-readable.",
                    ],
                )
            },
        )
    )

    # 27 mix pies -> stacked_bar stand-in
    slides.append(
        ordinary(
            27,
            "dual_chart",
            "Worldwide Total Loans and Card Member Receivables Mix",
            {
                "charts": [
                    sbar(
                        "s27-loans",
                        "Q4'21 Total Loan Mix",
                        [("q4-21", "Q4'21")],
                        [
                            ser("us", "U.S. Consumer", ["68"], "navy"),
                            ser("intl", "Intl. Consumer", ["12"], "primary_blue"),
                            ser("sb", "Small Business", ["20"], "sky_blue"),
                        ],
                        fmt="pct_0",
                    ),
                    sbar(
                        "s27-rec",
                        "Q4'21 Card Member Receivables Mix",
                        [("q4-21", "Q4'21")],
                        [
                            ser("us", "U.S. Consumer", ["34"], "navy"),
                            ser("intl", "Intl. Consumer", ["24"], "primary_blue"),
                            ser("sb", "Small Business", ["28"], "sky_blue"),
                            ser("corp", "Corporate Card", ["14"], "neutral"),
                        ],
                        fmt="pct_0",
                    ),
                ]
            },
            section="appendix",
            extra={
                "disclosure": disc(
                    "s27-disc",
                    "Notes",
                    [
                        "Note: Total Loans reflect Card Member loans and Other loans.",
                        "Type (B): source is pie/donut mix; stacked_bar is the least-lossy legal stand-in.",
                    ],
                )
            },
        )
    )

    # 28 FRP balances
    slides.append(
        ordinary(
            28,
            "single_chart",
            "Delinquent and Financial Relief Program Balances",
            {
                "chart": sbar(
                    "s28-frp",
                    "Delinquent and FRP Balances",
                    [
                        ("dec-19", "Dec'19"),
                        ("apr-20", "Apr'20"),
                        ("dec-20", "Dec'20"),
                        ("sep-21", "Sep'21"),
                        ("dec-21", "Dec'21"),
                    ],
                    [
                        ser("delinq", "Delinquent", ["2.1", "2.0", "1.0", "0.8", "0.9"], "navy"),
                        ser("frp", "Financial Relief Programs (FRP) Enrolled***", ["0.7", "0.9", "3.0", "1.5", "1.3"], "primary_blue"),
                        ser("cpr", "CPR Program Enrolled*", ["0.0", "8.5", "0.0", "0.0", "0.0"], "sky_blue"),
                    ],
                    fmt="usd_1",
                    subtitle="$ in billions",
                )
            },
            section="appendix",
            extra={
                "disclosure": disc(
                    "s28-disc",
                    "Notes",
                    [
                        "Dec'21 Total Loans $0.7 delinquent / related FRP stack; Card Member Receivables $0.9 / $0.6 and $1.6 / $0.6 labels on page were not fully mapped into the five-period stack (extraction residual).",
                        "Note: Total Loans reflects Card Member loans and Other loans. CPR = Customer Pandemic Relief Program. * balances at enrollment for card members in the CPR program as of April 19, 2020. *** FRP balance is a non-GAAP measure and excludes delinquent balances that are also reported in the Delinquent category. See Annex 7.",
                    ],
                )
            },
        )
    )

    # 29 GCP credit
    slides.append(
        ordinary(
            29,
            "single_chart",
            "Global Corporate Payments Card Member Credit Metrics",
            {
                "chart": line(
                    "s29-gcp",
                    "GCP Card Member Receivables Adjusted Net Write-off rates*",
                    [
                        ("q3-20", "Q3'20"),
                        ("q4-20", "Q4'20"),
                        ("q1-21", "Q1'21"),
                        ("q2-21", "Q2'21"),
                        ("q3-21", "Q3'21"),
                        ("q4-21", "Q4'21"),
                    ],
                    [
                        ser(
                            "adj",
                            "Adjusted Net Write-off rates*",
                            ["2.4", "0.7", "0.4", "0.5", "0.2", "0.2"],
                            "navy",
                        )
                    ],
                    fmt="pct_1",
                )
            },
            section="appendix",
            extra={
                "disclosure": disc(
                    "s29-disc",
                    "Notes",
                    [
                        "Q2'21 Client Bankruptcy Recovery Impact to Net Write-Offs: Net Write-Off Amount/(Recovery) ($37M); Credit Insurance Claim (Proceeds)/Repayment within Other, net $33M; Pre-tax Income $4M.",
                        "* Adjusted for Client bankruptcy impact of ($37M) for Q2'21. Adjusted Net Write-off rates are a non-GAAP measure, see Annex 8 for Net Write-off rates on a GAAP basis.",
                    ],
                )
            },
        )
    )

    # 30 macro assumptions — dual line; quarterly scenario values not extracted
    slides.append(
        ordinary(
            30,
            "narrative",
            "Credit Reserve Build Macroeconomic Assumptions",
            {
                "blocks": [
                    para_block(
                        "lead",
                        [
                            "US Unemployment Rate % and US GDP Growth* % charts show Q3 Baseline, Q3 Downside, Q4 Baseline, and Q4 Downside scenarios from Q3'20 through Q4'23."
                        ],
                    ),
                    bullets(
                        "facts",
                        [
                            "Forecast assumptions are from an independent third party and represent the range of forecasts from the macroeconomic scenarios used during the quarter without applying a weight to those scenarios above.",
                            "* Real GDP QoQ % Change Seasonally Adjusted to Annualized Rates (SAAR).",
                            "Extraction residual: individual quarterly scenario plot points were not glyph-readable; no invented series values.",
                        ],
                    ),
                ]
            },
            section="appendix",
        )
    )

    # 31 Funding mix
    slides.append(
        ordinary(
            31,
            "single_chart",
            "Funding Mix",
            {
                "chart": sbar(
                    "s31-fund",
                    "Funding Mix",
                    [("q4-19", "Q4'19"), ("q4-20", "Q4'20"), ("q4-21", "Q4'21")],
                    [
                        ser("unsec", "Unsecured Term**", ["28", "23", "20"], "navy"),
                        ser("abs", "Card ABS*", ["14", "10", "11"], "primary_blue"),
                        ser("dep", "Deposits", ["53", "66", "67"], "sky_blue"),
                        ser("st", "Short-term Funding", ["4", "1", "2"], "neutral"),
                    ],
                    fmt="pct_0",
                    subtitle="$ in billions",
                    totals=["126", "138", "132"],
                    tot_fmt="usd_0",
                )
            },
            section="appendix",
            extra={
                "disclosure": disc(
                    "s31-disc",
                    "Notes",
                    [
                        "Note: % of total may not foot due to rounding.",
                        "* Reflects face amount of Card ABS, net of securities retained by the Company. Includes outstanding ABS secured borrowing facility draws.",
                        "** Reflects face amount of unsecured term debt; the long-term debt balance on the Company's consolidated balance sheet includes capitalized leases and certain adjustments that are not included in these balances.",
                    ],
                )
            },
        )
    )

    # 32 FX impact
    slides.append(
        ordinary(
            32,
            "data_table",
            "FX Impact on Network Volumes and Revenue Growth",
            {
                "table": table(
                    "s32-fx",
                    "Currency",
                    [
                        ("share", "Approx Q4'21 Network Volumes % of Total"),
                        ("fx", "YoY% change in USD* vs Currency Strengthened/(Weakened)"),
                    ],
                    [
                        row("eur", "Euro EUR", {"share": num("4", "pct_0"), "fx": num("7", "pct_0")}),
                        row("gbp", "UK GBP", {"share": num("5", "pct_0"), "fx": num("1", "pct_0")}),
                        row("jpy", "Japan JPY", {"share": num("5", "pct_0"), "fx": num("11", "pct_0")}),
                        row("aud", "Australia $", {"share": num("3", "pct_0"), "fx": num("6", "pct_0")}),
                        row("cad", "Canada $", {"share": num("2", "pct_0"), "fx": num("-1", "pct_0")}),
                        row("mxn", "Mexico $", {"share": num("1", "pct_0"), "fx": num("3", "pct_0")}),
                    ],
                )
            },
            section="appendix",
            extra={
                "disclosure": disc(
                    "s32-disc",
                    "Notes",
                    [
                        "Note: Network Volumes is based on where the issuer is located and includes both proprietary and non-proprietary cards. See Slide 2 for an explanation of FX-adjusted information.",
                        "* Represents percentage change in foreign currency exchange rates at 2021 and 2020 December month-end, respectively, per Bloomberg.",
                        "Extraction residual: Q1'21-Q4'21 Reported vs FX-Adj line points for Network Volumes and Revenue Net of Interest Expense were not glyph-readable.",
                    ],
                )
            },
        )
    )

    # 33-34 commentary
    slides.append(
        ordinary(
            33,
            "narrative",
            "Additional Commentary - Variance Analysis",
            {
                "blocks": [
                    para_block(
                        "lead",
                        [
                            "The following summary provides selected variance information for the three months ended December 31, 2021 compared to the same period in the prior year. It should be read in conjunction with the statistical tables for Q4'21, available at ir.americanexpress.com."
                        ],
                    ),
                    bullets(
                        "rev",
                        [
                            "Discount Revenue: Increased 35% versus Q4'20, primarily driven by an increase in worldwide network volumes of 29 percent. The average discount rate was 2.30 percent, up from 2.25 percent a year ago, due to the change in the mix of spending driven by increased levels of T&E volumes.",
                            "Net Card Fees: Increased 10% versus Q4'20, primarily driven by growth in our premium card product portfolios.",
                            "Other Fees & Commissions: Increased 32% versus Q4'20, primarily due to higher foreign exchange conversion revenue related to cross-border Card Member spending and higher travel commissions and fees from our consumer travel business.",
                            "Other Revenues: Increased 218% versus Q4'20, primarily driven by a non-cash gain related to an increase in GBT's total equity book value and a lower net loss in the current year from GBT.",
                            "Interest Income: Increased 5% versus Q4'20, primarily due to higher average Card Member loan volumes.",
                            "Interest Expense: Decreased 25% versus Q4'20, primarily driven by lower interest rates paid on deposits and a reduction in average debt outstanding.",
                            "Provisions for Credit Losses: Increased 148% versus Q4'20 driven by a lower reserve release, partially offset by lower net write-offs in the current year.",
                        ],
                    ),
                ]
            },
            section="appendix",
        )
    )
    slides.append(
        ordinary(
            34,
            "narrative",
            "Additional Commentary - Variance Analysis",
            {
                "blocks": [
                    bullets(
                        "exp",
                        [
                            "Marketing and Business Development: Increased 46% versus Q4'20, primarily due to an increase in marketing investments to continue building growth momentum and higher partner payments driven by higher spending volumes.",
                            "Card Member Rewards Expense: Increased 32% versus Q4'20, primarily driven by an increase in Membership Rewards, cash back rewards and cobrand rewards expenses, all of which were primarily driven by higher billed business volumes. The increase in Membership Rewards expense was also driven by a larger portion of spend in categories that earn incremental rewards compared to the prior year.",
                            "The Company's Membership Rewards Ultimate Redemption Rate for current program participants was 96 percent (rounded down) for December 31, 2021 and 96 percent (rounded up) for December 31, 2020.",
                            "Card Member Services Expense: Increased 127% versus Q4'20, primarily due to higher usage of travel-related benefits.",
                            "Operating Expense: Increased 7% versus Q4'20, primarily driven by higher compensation and professional services expense.",
                        ],
                    )
                ]
            },
            section="appendix",
        )
    )

    # 35 ESG hierarchy
    slides.append(
        ordinary(
            35,
            "hierarchy",
            "Environmental, Social and Governance (ESG) Strategy",
            {
                "relationship": "part_of",
                "root_id": "mission",
                "nodes": [
                    {
                        "node_id": "mission",
                        "heading": "MISSION",
                        "detail": "Back people and businesses to thrive and create equitable, resilient, and sustainable communities globally",
                        "children": ["gov", "dei", "fin", "climate"],
                    },
                    {
                        "node_id": "gov",
                        "heading": "Sound Governance",
                        "detail": "Business ethics, transparency, and accountability; Nominating, Governance, and Public Responsibility Committee / Executive Committee / ESG Steering Committee / ESG Working Groups",
                    },
                    {
                        "node_id": "dei",
                        "heading": "Promote Diversity, Equity, and Inclusion",
                        "detail": "Support a diverse, equitable, and inclusive workforce, marketplace, and society",
                    },
                    {
                        "node_id": "fin",
                        "heading": "Build Financial Confidence",
                        "detail": "Provide responsible, secure, and transparent products and services to help people and businesses build financial resilience",
                    },
                    {
                        "node_id": "climate",
                        "heading": "Advance Climate Solutions",
                        "detail": "Enhance our operations and capabilities to meet customer and community needs in the transition to a low-carbon future",
                    },
                ],
            },
            section="appendix",
            extra={
                "disclosure": disc(
                    "s35-disc",
                    "Notes",
                    [
                        "Stakeholders including shareholders, colleagues, customers, and communities.",
                        "For more information, please see our 2020-2021 Environmental, Social and Governance Report.",
                    ],
                )
            },
        )
    )

    # 36 ESG highlights
    slides.append(
        ordinary(
            36,
            "narrative",
            "2021 ESG Highlights",
            {
                "blocks": [
                    bullets(
                        "dei",
                        [
                            "Promoting DE&I: $1 Billion DE&I Action Plan announced October 2020; more than $800 million spent on DE&I initiatives from October 2020 through December 2021.",
                            "Building Financial Confidence: Let's Go Shop Small campaign with a $100 million commitment; goals include access to credit to at least 4 million individuals from underserved or underrepresented populations from 2021 through 2025, tools for at least 5 million individuals, and $500M in community grants.",
                            "Advancing Climate Solutions: committed to net-zero emissions by 2035 in line with SBTi; carbon neutral across operations since 2018; plan to provide $10 million in philanthropic funding from 2021 through 2025.",
                        ],
                    )
                ]
            },
            section="appendix",
        )
    )

    # 37 Annex 1 (1 of 2) — dense; keep FY'21 + Q4'21 + vs '19 to stay paint-able
    a1_cols = [
        ("q4-21", "Q4'21"),
        ("fy-21", "FY'21"),
        ("q4-vs19", "Q4'21 vs Q4'19"),
        ("fy-vs19", "FY'21 vs FY'19"),
    ]
    slides.append(
        ordinary(
            37,
            "annex_table",
            "Annex 1 Network Volumes - Reported & FX-Adjusted",
            {
                "table": table(
                    "s37-a1",
                    "Metric",
                    a1_cols,
                    [
                        row("ic-r", "Int'l Consumer Reported", {"q4-21": num("28", "pct_0"), "fy-21": num("23", "pct_0"), "q4-vs19": num("7", "pct_0"), "fy-vs19": num("-3", "pct_0")}),
                        row("ic-fx", "Int'l Consumer FX-Adjusted", {"q4-21": num("32", "pct_0"), "fy-21": num("19", "pct_0"), "q4-vs19": num("5", "pct_0"), "fy-vs19": num("-7", "pct_0")}),
                        row("gc-r", "Global Consumer Reported", {"q4-21": num("34", "pct_0"), "fy-21": num("29", "pct_0"), "q4-vs19": num("18", "pct_0"), "fy-vs19": num("7", "pct_0")}),
                        row("gc-fx", "Global Consumer FX-Adjusted", {"q4-21": num("35", "pct_0"), "fy-21": num("28", "pct_0"), "q4-vs19": num("17", "pct_0"), "fy-vs19": num("6", "pct_0")}),
                        row("gcs-r", "Global Commercial (GCS) Reported", {"q4-21": num("29", "pct_0"), "fy-21": num("21", "pct_0"), "q4-vs19": num("6", "pct_0"), "fy-vs19": num("-4", "pct_0")}),
                        row("gcs-fx", "Global Commercial (GCS) FX-Adjusted", {"q4-21": num("30", "pct_0"), "fy-21": num("20", "pct_0"), "q4-vs19": num("6", "pct_0"), "fy-vs19": num("-5", "pct_0")}),
                        row("bb-r", "Billed Business Reported", {"q4-21": num("32", "pct_0"), "fy-21": num("25", "pct_0"), "q4-vs19": num("12", "pct_0"), "fy-vs19": num("2", "pct_0")}),
                        row("bb-fx", "Billed Business FX-Adjusted", {"q4-21": num("33", "pct_0"), "fy-21": num("24", "pct_0"), "q4-vs19": num("12", "pct_0"), "fy-vs19": num("1", "pct_0")}),
                        row("pv-r", "Processed Volumes Reported", {"q4-21": num("13", "pct_0"), "fy-21": num("16", "pct_0"), "q4-vs19": num("4", "pct_0"), "fy-vs19": num("0", "pct_0")}),
                        row("pv-fx", "Processed Volumes FX-Adjusted", {"q4-21": num("15", "pct_0"), "fy-21": num("14", "pct_0"), "q4-vs19": num("3", "pct_0"), "fy-vs19": num("-1", "pct_0")}),
                        row("ww-r", "Worldwide Reported", {"q4-21": num("29", "pct_0"), "fy-21": num("24", "pct_0"), "q4-vs19": num("11", "pct_0"), "fy-vs19": num("1", "pct_0")}),
                        row("ww-fx", "Worldwide FX-Adjusted", {"q4-21": num("30", "pct_0"), "fy-21": num("23", "pct_0"), "q4-vs19": num("11", "pct_0"), "fy-vs19": num("1", "pct_0")}),
                    ],
                )
            },
            section="appendix",
            extra={
                "content": {"subtitle": "% Increase/(decrease) vs. Prior year"},
                "disclosure": disc(
                    "s37-disc",
                    "Notes",
                    [
                        "* See Slide 2 for an explanation of FX-adjusted information. 2021 vs. 2019 YoY% assumes 2021 foreign exchange rates apply to 2019 results.",
                        "Type (A)/density: full Q1'19-Q4'21 matrix is on the PDF; authored Q4'21 / FY'21 / vs-2019 subset so the annex_table recipe can hold extracted facts without an 18-column overflow.",
                    ],
                ),
            },
        )
    )

    # 38 Annex 1 (2 of 2)
    slides.append(
        ordinary(
            38,
            "annex_table",
            "Annex 1 Network Volumes - Reported & FX-Adjusted",
            {
                "table": table(
                    "s38-a1b",
                    "Metric",
                    a1_cols,
                    [
                        row("lg-r", "Large & Global Corporate Reported", {"q4-21": num("34", "pct_0"), "fy-21": num("3", "pct_0"), "q4-vs19": num("-33", "pct_0"), "fy-vs19": num("-45", "pct_0")}),
                        row("lg-fx", "Large & Global Corporate FX-Adjusted", {"q4-21": num("34", "pct_0"), "fy-21": num("2", "pct_0"), "q4-vs19": num("-33", "pct_0"), "fy-vs19": num("-45", "pct_0")}),
                        row("isme-r", "Int'l SME Reported", {"q4-21": num("27", "pct_0"), "fy-21": num("24", "pct_0"), "q4-vs19": num("13", "pct_0"), "fy-vs19": num("7", "pct_0")}),
                        row("isme-fx", "Int'l SME FX-Adjusted", {"q4-21": num("31", "pct_0"), "fy-21": num("20", "pct_0"), "q4-vs19": num("12", "pct_0"), "fy-vs19": num("4", "pct_0")}),
                        row("sme-r", "SME Reported", {"q4-21": num("28", "pct_0"), "fy-21": num("24", "pct_0"), "q4-vs19": num("17", "pct_0"), "fy-vs19": num("9", "pct_0")}),
                        row("sme-fx", "SME FX-Adjusted", {"q4-21": num("29", "pct_0"), "fy-21": num("24", "pct_0"), "q4-vs19": num("17", "pct_0"), "fy-vs19": num("8", "pct_0")}),
                    ],
                )
            },
            section="appendix",
            extra={
                "disclosure": disc(
                    "s38-disc",
                    "Notes",
                    ["* See Slide 2 for an explanation of FX-adjusted information. 2021 vs. 2019 YoY% assumes 2021 foreign exchange rates apply to 2019 results."],
                )
            },
        )
    )

    # 39 Annex 2 Discount Revenue
    slides.append(
        ordinary(
            39,
            "annex_table",
            "Annex 2 Discount Revenue - Reported & FX-Adjusted",
            {
                "table": table(
                    "s39-a2",
                    "Metric",
                    [
                        ("q3-21", "Q3'21"),
                        ("q4-21", "Q4'21"),
                        ("fy-21", "FY'21"),
                    ],
                    [
                        row(
                            "gaap",
                            "GAAP Discount Revenue $B",
                            {"q3-21": num("6.7", "usd_1"), "q4-21": num("7.5", "usd_1"), "fy-21": num("25.7", "usd_1")},
                        ),
                        row(
                            "yoy-gaap",
                            "YoY% Inc/(Dec) in GAAP Discount Revenue",
                            {"q3-21": num("34", "pct_0"), "q4-21": num("35", "pct_0"), "fy-21": num("26", "pct_0")},
                        ),
                        row(
                            "yoy-fx",
                            "YoY% Inc/(Dec) in FX-Adjusted Discount Revenue*",
                            {"q3-21": num("33", "pct_0"), "q4-21": num("36", "pct_0"), "fy-21": num("25", "pct_0")},
                        ),
                        row(
                            "vs19",
                            "2021 vs 2019 GAAP / FX-Adjusted**",
                            {"q3-21": miss(), "q4-21": miss(), "fy-21": num("-2", "pct_0")},
                        ),
                    ],
                )
            },
            section="appendix",
            extra={
                "content": {"subtitle": "$ in billions"},
                "disclosure": disc(
                    "s39-disc",
                    "Notes",
                    [
                        "* See Slide 2 for an explanation of FX-adjusted information. ** 2021 vs. 2019 YoY% assumes 2021 foreign exchange rates apply to 2019 results.",
                        "Earlier-year GAAP levels on page: Q3'18 $6.2, Q4'18 $6.5, FY'18 $24.7, Q3'19 $6.6, Q4'19 $6.8, FY'19 $26.2, Q3'20 $5.0, Q4'20 $5.5, FY'20 $20.4.",
                    ],
                ),
            },
        )
    )

    # 40 Annex 3 Net Card Fees
    slides.append(
        ordinary(
            40,
            "annex_table",
            "Annex 3 Net Card Fees - Reported & FX-Adjusted",
            {
                "table": table(
                    "s40-a3",
                    "Metric",
                    [("q4-21", "Q4'21"), ("fy-21", "FY'21")],
                    [
                        row("gaap", "GAAP Net Card Fees $B", {"q4-21": num("1.3", "usd_1"), "fy-21": num("5.2", "usd_1")}),
                        row("yoy-gaap", "YoY% Inc/(Dec) in GAAP Net Card Fees", {"q4-21": num("10", "pct_0"), "fy-21": num("11", "pct_0")}),
                        row("yoy-fx", "YoY% Inc/(Dec) in FX-Adjusted Net Card Fees*", {"q4-21": num("11", "pct_0"), "fy-21": num("10", "pct_0")}),
                        row("vs19-gaap", "2021 vs 2019 GAAP", {"q4-21": miss(), "fy-21": num("29", "pct_0")}),
                        row("vs19-fx", "2021 vs 2019 FX-Adjusted**", {"q4-21": miss(), "fy-21": num("28", "pct_0")}),
                    ],
                )
            },
            section="appendix",
            extra={
                "disclosure": disc(
                    "s40-disc",
                    "Notes",
                    ["* See Slide 2. ** 2021 vs. 2019 YoY% assumes 2021 foreign exchange rates apply to 2019 results. FY'18 $3.4B, FY'19 $4.0B, FY'20 $4.7B GAAP Net Card Fees."],
                )
            },
        )
    )

    # 41 Annex 4 NII
    slides.append(
        ordinary(
            41,
            "annex_table",
            "Annex 4 Net Interest Income - Reported & FX-Adjusted",
            {
                "table": table(
                    "s41-a4",
                    "Metric",
                    [("q3-21", "Q3'21"), ("q4-21", "Q4'21"), ("fy-21", "FY'21")],
                    [
                        row("gaap", "GAAP Net Interest Income $B", {"q3-21": num("2.0", "usd_1"), "q4-21": num("2.1", "usd_1"), "fy-21": num("7.7", "usd_1")}),
                        row("yoy-gaap", "YoY% Inc/(Dec) in GAAP NII", {"q3-21": num("6", "pct_0"), "q4-21": num("11", "pct_0"), "fy-21": num("-3", "pct_0")}),
                        row("yoy-fx", "YoY% Inc/(Dec) in FX-Adjusted NII*", {"q3-21": num("6", "pct_0"), "q4-21": num("11", "pct_0"), "fy-21": num("-4", "pct_0")}),
                        row("vs19", "2021 vs 2019 GAAP / FX-Adjusted**", {"q3-21": miss(), "q4-21": miss(), "fy-21": num("-10", "pct_0")}),
                    ],
                )
            },
            section="appendix",
            extra={
                "disclosure": disc(
                    "s41-disc",
                    "Notes",
                    ["* See Slide 2. ** 2021 vs. 2019 YoY% assumes 2021 FX rates apply to 2019 results."],
                )
            },
        )
    )

    # 42 Annex 5 yield
    slides.append(
        ordinary(
            42,
            "annex_table",
            "Annex 5 Consolidated Net Interest Yield on Average Card Member Loans",
            {
                "table": table(
                    "s42-a5",
                    "Metric",
                    [
                        ("q3-19", "Q3'19"),
                        ("q4-19", "Q4'19"),
                        ("q3-20", "Q3'20"),
                        ("q4-20", "Q4'20"),
                        ("q3-21", "Q3'21"),
                        ("q4-21", "Q4'21"),
                    ],
                    [
                        row("nii", "Net interest income", {k: num(v, "usd_0") for k, v in zip(["q3-19","q4-19","q3-20","q4-20","q3-21","q4-21"], ["2203","2284","1874","1897","1994","2107"])}),
                        row("ie", "Interest expense not attributable to CM loan portfolio*", {k: num(v, "usd_0") for k, v in zip(["q3-19","q4-19","q3-20","q4-20","q3-21","q4-21"], ["461","421","296","254","172","135"])}),
                        row("ii", "Interest income not attributable to CM loan portfolio**", {k: num(v, "usd_0") for k, v in zip(["q3-19","q4-19","q3-20","q4-20","q3-21","q4-21"], ["-308","-271","-137","-111","-92","-98"])}),
                        row("adj", "Adjusted net interest income***", {k: num(v, "usd_0") for k, v in zip(["q3-19","q4-19","q3-20","q4-20","q3-21","q4-21"], ["2356","2434","2033","2040","2074","2145"])}),
                        row("avg", "Average Card Member loans (billions)", {k: num(v, "usd_1") for k, v in zip(["q3-19","q4-19","q3-20","q4-20","q3-21","q4-21"], ["83.3","85.2","69.9","71.2","76.4","82.9"])}),
                        row("gaap-y", "NII / average CM loans", {k: num(v, "pct_1") for k, v in zip(["q3-19","q4-19","q3-20","q4-20","q3-21","q4-21"], ["10.6","10.7","10.7","10.7","10.4","10.2"])}),
                        row("yield", "Net interest yield on average CM loans***", {k: num(v, "pct_1") for k, v in zip(["q3-19","q4-19","q3-20","q4-20","q3-21","q4-21"], ["11.2","11.3","11.6","11.4","10.8","10.3"])}),
                    ],
                )
            },
            section="appendix",
            extra={
                "content": {"subtitle": "$ in millions, except percentages and where indicated"},
                "disclosure": disc(
                    "s42-disc",
                    "Notes",
                    [
                        "* Primarily represents interest expense attributable to funding Card Member receivables and maintaining our corporate liquidity pool.",
                        "** Primarily represents interest income attributable to Other loans, interest-bearing deposits and our Travelers Cheque and other stored-value investment portfolio.",
                        "*** Adjusted net interest income and net interest yield on average Card Member loans are non-GAAP measures.",
                    ],
                ),
            },
        )
    )

    # 43 Annex 6 (1 of 2)
    slides.append(
        ordinary(
            43,
            "annex_table",
            "Annex 6 Revenues Net of Interest Expense",
            {
                "table": table(
                    "s43-a6",
                    "Metric",
                    [("q4-21", "Q4'21"), ("fy-21", "FY'21")],
                    [
                        row("gaap", "GAAP Revenues Net of Interest Expense $B", {"q4-21": num("12.1", "usd_1"), "fy-21": num("42.4", "usd_1")}),
                        row("yoy-gaap", "YoY% Inc/(Dec) in GAAP", {"q4-21": num("30", "pct_0"), "fy-21": num("17", "pct_0")}),
                        row("yoy-fx", "YoY% Inc/(Dec) in FX-Adjusted*", {"q4-21": num("31", "pct_0"), "fy-21": num("17", "pct_0")}),
                    ],
                )
            },
            section="appendix",
            extra={
                "disclosure": disc(
                    "s43-disc",
                    "Notes",
                    ["* See Slide 2. FY'18 $40.3B, FY'19 $43.6B, FY'20 $36.1B GAAP Revenues Net of Interest Expense."],
                )
            },
        )
    )

    # 44 Annex 6 (2 of 2)
    slides.append(
        ordinary(
            44,
            "annex_table",
            "Annex 6 Revenues Net of Interest Expense",
            {
                "table": table(
                    "s44-a6b",
                    "Metric",
                    [
                        ("q1-21", "Q1'21"),
                        ("q2-21", "Q2'21"),
                        ("q3-21", "Q3'21"),
                        ("q4-21", "Q4'21"),
                        ("fy-21", "FY'21"),
                    ],
                    [
                        row(
                            "gaap",
                            "GAAP Revenues Net of Interest Expense $B",
                            {
                                "q1-21": num("9.1", "usd_1"),
                                "q2-21": num("10.2", "usd_1"),
                                "q3-21": num("10.9", "usd_1"),
                                "q4-21": num("12.1", "usd_1"),
                                "fy-21": num("42.4", "usd_1"),
                            },
                        ),
                        row(
                            "vs19-gaap",
                            "2021 vs 2019 YoY% GAAP",
                            {
                                "q1-21": num("-13", "pct_0"),
                                "q2-21": num("-5", "pct_0"),
                                "q3-21": num("-1", "pct_0"),
                                "q4-21": num("7", "pct_0"),
                                "fy-21": num("-3", "pct_0"),
                            },
                        ),
                        row(
                            "vs19-fx",
                            "2021 vs 2019 YoY% FX-Adjusted*",
                            {
                                "q1-21": num("-13", "pct_0"),
                                "q2-21": num("-6", "pct_0"),
                                "q3-21": num("-1", "pct_0"),
                                "q4-21": num("7", "pct_0"),
                                "fy-21": num("-3", "pct_0"),
                            },
                        ),
                    ],
                )
            },
            section="appendix",
            extra={
                "disclosure": disc(
                    "s44-disc",
                    "Notes",
                    ["* See Slide 2. 2021 vs. 2019 YoY% assumes 2021 foreign exchange rates apply to 2019 results."],
                )
            },
        )
    )

    # 45 Annex 7 TDR
    slides.append(
        ordinary(
            45,
            "annex_table",
            "Annex 7 Troubled Debt Restructurings (TDR) Balance",
            {
                "table": table(
                    "s45-a7",
                    "Metric",
                    [
                        ("dec-19", "Dec'19"),
                        ("apr-20", "Apr'20"),
                        ("dec-20", "Dec'20"),
                        ("jun-21", "Jun'21"),
                        ("sep-21", "Sep'21"),
                        ("dec-21", "Dec'21"),
                    ],
                    [
                        row("tdr", "In-Program TDR Balance", {k: num(v, "usd_1") for k, v in zip(["dec-19","apr-20","dec-20","jun-21","sep-21","dec-21"], ["0.8","1.0","3.1","1.9","1.5","1.3"])}),
                        row("del-frp", "Delinquent FRP balance", {k: num(v, "usd_1") for k, v in zip(["dec-19","apr-20","dec-20","jun-21","sep-21","dec-21"], ["0.1","0.1","0.1","0.1","0.1","0.1"])}),
                        row("nd-frp", "Non-delinquent FRP balance", {k: num(v, "usd_1") for k, v in zip(["dec-19","apr-20","dec-20","jun-21","sep-21","dec-21"], ["0.7","0.9","3.0","1.8","1.5","1.3"])}),
                    ],
                )
            },
            section="appendix",
            extra={
                "content": {"subtitle": "$ in billions"},
                "disclosure": disc(
                    "s45-disc",
                    "Notes",
                    ["Note: Totals may not foot due to rounding."],
                ),
            },
        )
    )

    # 46 Annex 8 GCP NWO
    slides.append(
        ordinary(
            46,
            "annex_table",
            "Annex 8 GCP Card Member Receivables Net Write-Off rates",
            {
                "table": table(
                    "s46-a8",
                    "Metric",
                    [("q2-21", "Q2'21")],
                    [
                        row("nwo", "GCP Net Write-Offs - Principal and Fees*", {"q2-21": num("-24", "usd_0")}),
                        row("bk", "Client Bankruptcy Recovery Impact", {"q2-21": num("37", "usd_0")}),
                        row("adj", "Adjusted Net Write-Offs", {"q2-21": num("13", "usd_0")}),
                        row("avg", "GCP Average Card Member Receivables", {"q2-21": num("11087", "usd_0")}),
                        row("rpt", "Reported Net Write-Off rates", {"q2-21": num("-0.9", "pct_1")}),
                        row("adj-r", "Adjusted Net Write-Off rates", {"q2-21": num("0.5", "pct_1")}),
                    ],
                )
            },
            section="appendix",
            extra={
                "content": {"subtitle": "$ in millions"},
                "disclosure": disc(
                    "s46-disc",
                    "Notes",
                    ["* Global Corporate Payments (GCP) reflects global, large and middle market corporate accounts. Net write-off rate based on principal losses only are not available due to system constraints."],
                ),
            },
        )
    )

    # 47-52 legal
    for part, page in enumerate(range(47, 53), start=1):
        payload = {
            "notice_id": "forward-looking-statements",
            "part": part,
            "total_parts": 6,
            "paragraphs": FLS[page],
        }
        if part == 1:
            payload["title"] = "Forward Looking Statements"
        slides.append(
            {
                "slide_number": page,
                "layout_type": "legal_notice",
                "section_id": "legal",
                "payload": payload,
                "evidence_ids": ev(page),
            }
        )

    # 53 closing
    slides.append(
        {
            "slide_number": 53,
            "layout_type": "closing_cover",
            "payload": {"title": "American Express"},
            "evidence_ids": ev(53),
        }
    )

    assert [s["slide_number"] for s in slides] == list(range(1, 54)), [
        s["slide_number"] for s in slides
    ]

    deck = {
        "meta": {"handoff_schema_version": 1},
        "sections": [
            {"section_id": "earnings", "label": "Earnings"},
            {"section_id": "appendix", "label": "Appendix"},
            {"section_id": "legal", "label": "Legal"},
        ],
        "number_formats": {
            "usd_0": {"unit": "usd", "value_decimals": 0, "negative_style": "parentheses"},
            "usd_1": {"unit": "usd", "value_decimals": 1, "negative_style": "parentheses"},
            "usd_2": {"unit": "usd", "value_decimals": 2, "negative_style": "parentheses"},
            "pct_0": {"unit": "percent", "value_decimals": 0, "negative_style": "parentheses"},
            "pct_1": {"unit": "percent", "value_decimals": 1, "negative_style": "minus"},
            "pct_2": {"unit": "percent", "value_decimals": 2, "negative_style": "minus"},
            "num_0": {"value_decimals": 0, "negative_style": "minus"},
            "num_1": {"value_decimals": 1, "negative_style": "minus"},
        },
        "evidence_registry": evidence_registry(),
        "slides": slides,
    }
    OUT.write_text(json.dumps(deck, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT, "slides", len(slides))


if __name__ == "__main__":
    build()
