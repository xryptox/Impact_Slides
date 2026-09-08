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
ANNEX_12 = [
    ("q3-18", "Q3'18"),
    ("q4-18", "Q4'18"),
    ("fy-18", "FY'18"),
    ("q3-19", "Q3'19"),
    ("q4-19", "Q4'19"),
    ("fy-19", "FY'19"),
    ("q3-20", "Q3'20"),
    ("q4-20", "Q4'20"),
    ("fy-20", "FY'20"),
    ("q3-21", "Q3'21"),
    ("q4-21", "Q4'21"),
    ("fy-21", "FY'21"),
]
ANNEX_10 = [
    ("q1-19", "Q1'19"),
    ("q2-19", "Q2'19"),
    ("q3-19", "Q3'19"),
    ("q4-19", "Q4'19"),
    ("fy-19", "FY'19"),
    ("q1-21", "Q1'21"),
    ("q2-21", "Q2'21"),
    ("q3-21", "Q3'21"),
    ("q4-21", "Q4'21"),
    ("fy-21", "FY'21"),
]
Q21 = [
    ("q1-21", "Q1'21"),
    ("q2-21", "Q2'21"),
    ("q3-21", "Q3'21"),
    ("q4-21", "Q4'21"),
]
ANNEX_18 = [
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
    ("fy-21", "FY'21"),
    ("q1-vs19", "Q1 vs '19"),
    ("q2-vs19", "Q2 vs '19"),
    ("q3-vs19", "Q3 vs '19"),
    ("q4-vs19", "Q4 vs '19"),
    ("fy-vs19", "FY vs '19"),
]
ANNEX_14 = [
    ("q1-20", "Q1'20"),
    ("q2-20", "Q2'20"),
    ("q3-20", "Q3'20"),
    ("q4-20", "Q4'20"),
    ("q1-21", "Q1'21"),
    ("q2-21", "Q2'21"),
    ("q3-21", "Q3'21"),
    ("q4-21", "Q4'21"),
    ("fy-21", "FY'21"),
    ("q1-vs19", "Q1 vs '19"),
    ("q2-vs19", "Q2 vs '19"),
    ("q3-vs19", "Q3 vs '19"),
    ("q4-vs19", "Q4 vs '19"),
    ("fy-vs19", "FY vs '19"),
]
ANNEX_20 = [
    ("q1-18", "Q1'18"),
    ("q2-18", "Q2'18"),
    ("q3-18", "Q3'18"),
    ("q4-18", "Q4'18"),
    ("fy-18", "FY'18"),
    ("q1-19", "Q1'19"),
    ("q2-19", "Q2'19"),
    ("q3-19", "Q3'19"),
    ("q4-19", "Q4'19"),
    ("fy-19", "FY'19"),
    ("q1-20", "Q1'20"),
    ("q2-20", "Q2'20"),
    ("q3-20", "Q3'20"),
    ("q4-20", "Q4'20"),
    ("fy-20", "FY'20"),
    ("q1-21", "Q1'21"),
    ("q2-21", "Q2'21"),
    ("q3-21", "Q3'21"),
    ("q4-21", "Q4'21"),
    ("fy-21", "FY'21"),
]
YEAR_Q3Q4_GROUPS = [
    {
        "group_id": "y19",
        "label": "2019",
        "category_ids": ["q3-19", "q4-19"],
        "placement": "above",
    },
    {
        "group_id": "y20",
        "label": "2020",
        "category_ids": ["q3-20", "q4-20"],
        "placement": "above",
    },
    {
        "group_id": "y21",
        "label": "2021",
        "category_ids": ["q3-21", "q4-21"],
        "placement": "above",
    },
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


def boxed(aux_id, label, fmt, target, values):
    return {
        "auxiliary_id": aux_id,
        "role": "boxed_label",
        "label": label,
        "format_id": fmt,
        "target_series_id": target,
        "values": [None if v is None else str(v) for v in values],
    }


def gbar(
    surface,
    heading,
    pairs,
    series,
    fmt="pct_0",
    subtitle=None,
    groups=None,
    boxed_label=None,
    identity="legend",
):
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
        "display": {"ordinary_values": "show", "series_identity": identity},
    }
    if subtitle:
        ch["subtitle"] = subtitle
    if groups is not None:
        ch["category_groups"] = groups
    if boxed_label is not None:
        ch["auxiliary_series"] = [boxed_label]
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


def combo(
    surface,
    heading,
    pairs,
    series,
    bar_mode="grouped",
    pfmt="usd_1",
    sfmt=None,
    subtitle=None,
    groups=None,
    boxed_label=None,
):
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
    if groups is not None:
        ch["category_groups"] = groups
    if boxed_label is not None:
        ch["auxiliary_series"] = [boxed_label]
    return ch


def fy_support(surface, stub, row_id, row_label, amt, yoy, vs19, amt_fmt="usd_1"):
    return {
        "support_type": "support_table",
        "alignment": "independent",
        "table": table(
            surface,
            stub,
            [("amt", "$B"), ("yoy", "YoY"), ("vs19", "vs. '19")],
            [
                row(
                    row_id,
                    row_label,
                    {
                        "amt": num(amt, amt_fmt),
                        "yoy": num(yoy, "pct_0"),
                        "vs19": num(vs19, "pct_0"),
                    },
                )
            ],
        ),
    }


def wstep(cid, label, role, value=None):
    d = {"category_id": cid, "label": label, "role": role}
    if value is not None:
        d["value"] = str(value)
    return d


def waterfall(surface, heading, steps, fmt="usd_1", subtitle=None):
    ch = {
        "type": "chart",
        "surface_id": surface,
        "chart_type": "waterfall",
        "heading": heading,
        "waterfall_data": {"steps": steps},
        "category_axis": {"visible": True},
        "value_axes": {
            "primary": {
                "visible": True,
                "format_id": fmt,
                "domain": {"kind": "generated", "target_ticks": 5},
            }
        },
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


def mixed_row(rid, label, col_pairs, vals, fmt):
    cells = {}
    for (cid, _), v in zip(col_pairs, vals):
        cells[cid] = miss() if v is None else num(v, fmt)
    return row(rid, label, cells)


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


def pane(chart, support=None):
    d = {"chart": chart}
    if support is not None:
        d["support"] = support
    return d


def cat_support(surface, stub, pairs, rows):
    return {
        "support_type": "support_table",
        "alignment": "category",
        "table": table(surface, stub, pairs, rows),
    }


def indep_support(surface, stub, pairs, rows):
    return {
        "support_type": "support_table",
        "alignment": "independent",
        "table": table(surface, stub, pairs, rows),
    }


def metric_strip(surface, metrics):
    return {"support_type": "metric_strip", "surface_id": surface, "metrics": metrics}


def donut(surface, heading, slices):
    return {
        "type": "chart",
        "surface_id": surface,
        "chart_type": "donut",
        "heading": heading,
        "slices": [
            {
                "slice_id": sid,
                "label": lab,
                "value": num(val, "pct_0"),
            }
            for sid, lab, val in slices
        ],
    }


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

    # 3 Total Network Volumes Growth — PDF visual: 8-quarter vs-2019 lines; only Q3'21/Q4'21
    # vs '19 are labeled (table = line endpoints). Q1'20-Q2'21 interiors unlabeled.
    # Axis ticks are labeled (40%)…20%; pin domain.kind=fixed (#315). Do not digitize interiors.
    s03_chart = line(
        "s03-vol",
        "Total Network Volumes",
        Q20_21,
        [
            ser(
                "billed",
                "Billed Business",
                [None, None, None, None, None, None, "4", "12"],
                "primary_blue",
            ),
            ser(
                "tnv",
                "Total Network Volumes",
                [None, None, None, None, None, None, "4", "11"],
                "navy",
            ),
            ser(
                "processed",
                "Processed Volumes",
                [None, None, None, None, None, None, "3", "3"],
                "neutral",
            ),
        ],
        fmt="pct_0",
        subtitle="% Increase/(decrease) vs. 2019",
    )
    s03_chart["value_axes"]["primary"]["domain"] = {
        "kind": "fixed",
        "min": "-40",
        "max": "20",
        "ticks": ["-40", "-30", "-20", "-10", "0", "10", "20"],
    }
    slides.append(
        ordinary(
            3,
            "single_chart",
            "Total Network Volumes Growth",
            {
                "chart": s03_chart,
                "support": {
                    "support_type": "support_table",
                    "alignment": "independent",
                    "table": table(
                        "s03-tbl",
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
                    ),
                },
            },
            extra={
                "disclosure": disc(
                    "s03-disc",
                    "Notes",
                    [
                        "Note: All growth rates reflect FX-adjusted rates. See Annex 1 for reported billings growth rates.",
                        "Billed business represents proprietary billed business on cards issued by AXP. Processed volumes represent GNS and alternative payment solutions facilitated by AXP.",
                        "Line holds labeled Q3'21/Q4'21 vs '19 endpoints from the on-page grid. Axis ticks pinned to PDF (40%)..20% (#315). Q1'20-Q2'21 interiors are unlabeled.",
                    ],
                )
            },
        )
    )

    # 4 Billed Business (G&S vs T&E) -- FY stacked mix + Q4 vs-'19 endpoints + shared table.
    # Line interiors Q1'20-Q3'21 unlabeled (one labeled point per series), so pane 2 is
    # grouped_bar of the labeled Q4 endpoints, not a line. Shared independent support.
    s04_fy_cats = [("fy-19", "FY'19"), ("fy-20", "FY'20"), ("fy-21", "FY'21")]
    s04_q4_cats = [("gs", "G&S"), ("te", "T&E"), ("total", "Total")]
    slides.append(
        ordinary(
            4,
            "dual_chart",
            "Billed Business (G&S vs T&E)",
            {
                "charts": [
                    pane(
                        sbar(
                            "s04-mix",
                            "G&S vs. T&E",
                            s04_fy_cats,
                            [
                                ser("gs", "G&S", ["70", "85", "81"], "navy"),
                                ser("te", "T&E", ["30", "15", "19"], "neutral"),
                            ],
                            fmt="pct_0",
                            subtitle="$ in Billions, % of Total",
                            totals=["1071", "871", "1090"],
                            tot_fmt="usd_0",
                        )
                    ),
                    pane(
                        gbar(
                            "s04-growth",
                            "G&S vs. T&E Growth",
                            s04_q4_cats,
                            [
                                ser("vs19", "Q4'21 vs '19", ["24", "-18", "12"], "navy"),
                            ],
                            fmt="pct_0",
                            subtitle="% Increase/(decrease) vs. 2019 (FX-adjusted)",
                            identity="pane_title",
                        )
                    ),
                ],
                "support": indep_support(
                    "s04-tbl",
                    "Q4'21",
                    s04_q4_cats,
                    [
                        row(
                            "vs19",
                            "vs. '19",
                            {
                                "gs": num("24", "pct_0"),
                                "te": num("-18", "pct_0"),
                                "total": num("12", "pct_0"),
                            },
                        ),
                        row(
                            "yoy",
                            "YoY",
                            {
                                "gs": num("19", "pct_0"),
                                "te": num("132", "pct_0"),
                                "total": num("33", "pct_0"),
                            },
                        ),
                    ],
                ),
            },
            extra={
                "disclosure": disc(
                    "s04-disc",
                    "Notes",
                    [
                        "Note: All growth rates reflect FX-adjusted rates. See Annex 1 for reported billings growth rates. G&S = Goods & Services spending. T&E = Travel & Entertainment spending.",
                        "Q1'20-Q3'21 vs-2019 line interiors unlabeled; each series has one labeled Q4'21 point (G&S 24, T&E (18), Total 12), so the growth pane is a grouped_bar of those endpoints, not a line.",
                    ],
                ),
            },
        )
    )

    # 5 G&S Online vs Offline — PDF visual: 8-quarter vs-2019 Online/Total/Offline line
    # plus Q4 table. Only Q4'21 vs '19 (31/24/12) are labeled. Line requires at least two
    # finite values per series, so a Q4-only endpoint line is illegal; interiors unread.
    slides.append(
        ordinary(
            5,
            "data_table",
            "Goods & Services Billed Business (Online vs Offline)",
            {
                "table": table(
                    "s05-gs",
                    "Q4'21",
                    [("online", "Online"), ("offline", "Offline"), ("total", "Total")],
                    [
                        row(
                            "vs19",
                            "vs. '19",
                            {
                                "online": num("31", "pct_0"),
                                "offline": num("12", "pct_0"),
                                "total": num("24", "pct_0"),
                            },
                        ),
                        row(
                            "yoy",
                            "YoY",
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
                        "Note: Online = Online + Card Not Present. All growth rates reflect FX-adjusted rates. See Annex 1 for reported billings growth rates.",
                        "Line omitted: Q1'20-Q3'21 vs-2019 interiors unlabeled. Line requires at least two finite values per series; Q4'21 endpoints 31/24/12 alone are illegal.",
                    ],
                )
            },
        )
    )

    # 6 Global Consumer — stacked mix + age-cohort grouped bar, each with under-plot table.
    # Geometric vs-2019 callouts on the stack have no recipe; omit them.
    # Age-cohort 8-quarter vs-2019 interiors unlabeled (#301 leftover).
    s06_mix_cats = [
        ("q1-21", "Q1'21"),
        ("q2-21", "Q2'21"),
        ("q3-21", "Q3'21"),
        ("q4-21", "Q4'21"),
    ]
    s06_age_cats = [
        ("millennial", "Millennials + Gen-Z"),
        ("gen-x", "Gen-X"),
        ("boomer", "Baby Boomer +"),
    ]
    slides.append(
        ordinary(
            6,
            "dual_chart",
            "Global Consumer Billed Business",
            {
                "charts": [
                    pane(
                        sbar(
                            "s06-mix",
                            "G&S vs. T&E",
                            s06_mix_cats,
                            [
                                ser("gs", "G&S", ["82", "77", "74", "75"], "navy"),
                                ser("te", "T&E", ["18", "23", "26", "25"], "primary_blue"),
                            ],
                            fmt="pct_0",
                            subtitle="$ in Billions, % of Total",
                            totals=["119", "147", "153", "174"],
                            tot_fmt="usd_0",
                        ),
                        indep_support(
                            "s06-mix-tbl",
                            "Q4'21",
                            [("gs", "G&S"), ("te", "T&E"), ("total", "Total")],
                            [
                                row(
                                    "yoy",
                                    "YoY",
                                    {
                                        "gs": num("19", "pct_0"),
                                        "te": num("130", "pct_0"),
                                        "total": num("35", "pct_0"),
                                    },
                                ),
                            ],
                        ),
                    ),
                    pane(
                        gbar(
                            "s06-age",
                            "Billed Business Growth by Age Cohort",
                            s06_age_cats,
                            [
                                ser("vs19", "vs. '19", ["50", "17", "0"], "navy"),
                            ],
                            fmt="pct_0",
                            subtitle="% Increase/(decrease) vs. 2019 (FX-adjusted)",
                            identity="pane_title",
                        ),
                        cat_support(
                            "s06-age-tbl",
                            "Q4'21",
                            s06_age_cats,
                            [
                                row(
                                    "vs19",
                                    "vs. '19",
                                    {
                                        "millennial": num("50", "pct_0"),
                                        "gen-x": num("17", "pct_0"),
                                        "boomer": num("0", "pct_0"),
                                    },
                                ),
                                row(
                                    "yoy",
                                    "YoY",
                                    {
                                        "millennial": num("51", "pct_0"),
                                        "gen-x": num("34", "pct_0"),
                                        "boomer": num("26", "pct_0"),
                                    },
                                ),
                                row(
                                    "mix",
                                    "% of Total",
                                    {
                                        "millennial": num("28", "pct_0"),
                                        "gen-x": num("39", "pct_0"),
                                        "boomer": num("33", "pct_0"),
                                    },
                                ),
                            ],
                        ),
                    ),
                ]
            },
            extra={
                "disclosure": disc(
                    "s06-disc",
                    "Notes",
                    [
                        "Note: All growth rates reflect FX-adjusted rates. See Annex 1 for reported billings growth rates.",
                        "Q4'21 vs '19 Total Consumer 17%, G&S 26%, T&E (2%). Geometric vs-2019 callouts on the mix stack have no recipe and are omitted.",
                        "Age-cohort 8-quarter interiors unlabeled (#301 leftover). Page-6 glyphs: axis ticks (50)/(30)/(10)/10/30/50, quarter labels, series names, Q4 table vs-'19 50/17/(0). No second labeled plot point. Line requires two finite values per series; authored Q4'21 vs '19 endpoints as a grouped bar plus the under-plot table.",
                    ],
                )
            },
        )
    )

    # 7 Global Commercial — stacked mix + SME vs L&G snapshot, each with under-plot table.
    # SME 8-quarter vs-2019 interiors unlabeled (#301 leftover).
    s07_mix_cats = [
        ("q1-21", "Q1'21"),
        ("q2-21", "Q2'21"),
        ("q3-21", "Q3'21"),
        ("q4-21", "Q4'21"),
    ]
    s07_sme_cats = [
        ("sme-gs", "SME G&S"),
        ("sme-tot", "SME Total"),
        ("lg-tot", "L&G Total"),
    ]
    slides.append(
        ordinary(
            7,
            "dual_chart",
            "Global Commercial Billed Business",
            {
                "charts": [
                    pane(
                        sbar(
                            "s07-mix",
                            "G&S vs. T&E",
                            s07_mix_cats,
                            [
                                ser("gs", "G&S", ["90", "88", "86", "84"], "navy"),
                                ser("te", "T&E", ["10", "12", "14", "16"], "primary_blue"),
                            ],
                            fmt="pct_0",
                            subtitle="$ in Billions, % of Total",
                            totals=["104", "120", "126", "141"],
                            tot_fmt="usd_0",
                        ),
                        indep_support(
                            "s07-mix-tbl",
                            "Q4'21",
                            [("gs", "G&S"), ("te", "T&E"), ("total", "Total")],
                            [
                                row(
                                    "yoy",
                                    "YoY",
                                    {
                                        "gs": num("20", "pct_0"),
                                        "te": num("137", "pct_0"),
                                        "total": num("30", "pct_0"),
                                    },
                                ),
                            ],
                        ),
                    ),
                    pane(
                        gbar(
                            "s07-sme",
                            "SME vs. Large & Global Corporate",
                            s07_sme_cats,
                            [
                                ser("vs19", "vs. '19", ["25", "17", "-33"], "navy"),
                            ],
                            fmt="pct_0",
                            subtitle="% Increase/(decrease) vs. 2019 (FX-adjusted)",
                            identity="pane_title",
                        ),
                        cat_support(
                            "s07-sme-tbl",
                            "Q4'21",
                            s07_sme_cats,
                            [
                                row(
                                    "vs19",
                                    "vs. '19",
                                    {
                                        "sme-gs": num("25", "pct_0"),
                                        "sme-tot": num("17", "pct_0"),
                                        "lg-tot": num("-33", "pct_0"),
                                    },
                                ),
                                row(
                                    "yoy",
                                    "YoY",
                                    {
                                        "sme-gs": num("21", "pct_0"),
                                        "sme-tot": num("29", "pct_0"),
                                        "lg-tot": num("34", "pct_0"),
                                    },
                                ),
                                row(
                                    "mix",
                                    "% of Total",
                                    {
                                        "sme-gs": num("74", "pct_0"),
                                        "sme-tot": num("85", "pct_0"),
                                        "lg-tot": num("15", "pct_0"),
                                    },
                                ),
                            ],
                        ),
                    ),
                ]
            },
            extra={
                "disclosure": disc(
                    "s07-disc",
                    "Notes",
                    [
                        "Note: SME refers to small and mid-sized businesses with less than $300MM in annual revenues. All growth rates reflect FX-adjusted rates. See Annex 1 for reported billings growth rates.",
                        "Geometric vs-2019 callouts on the mix stack have no recipe and are omitted. SME 8-quarter interiors unlabeled (#301 leftover). Page-7 glyphs: axis ticks (80)/(60)/(40)/(20)/0/20/40, quarter labels, series names, Q4 table vs-'19 25/17/(33). No second labeled plot point. Line requires two finite values per series; authored Q4'21 vs '19 endpoints as a grouped bar plus the under-plot table.",
                    ],
                )
            },
        )
    )

    # 8 T&E by customer type — PDF visual: 5-series vs-2019 line (US Consumer / Total SME /
    # Total T&E / Intl Consumer / L&G) plus Q4 YoY/% of Total table. Line max is 4 series;
    # Q4'21 % of Q4'19 callouts (108/83/82/78/36) are not vs-2019 glyphs and interiors are
    # unlabeled, so the line cannot be authored (#297 leftover). Table matches the page.
    slides.append(
        ordinary(
            8,
            "data_table",
            "Billed Business T&E Growth",
            {
                "table": table(
                    "s08-te",
                    "Q4'21",
                    [
                        ("us-cons", "US Consumer"),
                        ("intl-cons", "Intl Consumer"),
                        ("tot-cons", "Total Consumer"),
                        ("us-sme", "US SME"),
                        ("intl-sme", "Intl SME"),
                        ("tot-sme", "Total SME"),
                        ("lg", "L&G"),
                        ("total", "Total"),
                    ],
                    [
                        row(
                            "yoy",
                            "YoY",
                            {
                                "us-cons": num("130", "pct_0"),
                                "intl-cons": num("130", "pct_0"),
                                "tot-cons": num("130", "pct_0"),
                                "us-sme": num("145", "pct_0"),
                                "intl-sme": num("99", "pct_0"),
                                "tot-sme": num("134", "pct_0"),
                                "lg": num("144", "pct_0"),
                                "total": num("132", "pct_0"),
                            },
                        ),
                        row(
                            "mix",
                            "% of Total",
                            {
                                "us-cons": num("49", "pct_0"),
                                "intl-cons": num("17", "pct_0"),
                                "tot-cons": num("66", "pct_0"),
                                "us-sme": num("20", "pct_0"),
                                "intl-sme": num("5", "pct_0"),
                                "tot-sme": num("25", "pct_0"),
                                "lg": num("9", "pct_0"),
                                "total": num("100", "pct_0"),
                            },
                        ),
                        row(
                            "vs-q419",
                            "Q4'21 % of Q4'19",
                            {
                                "us-cons": num("108", "pct_0"),
                                "intl-cons": num("78", "pct_0"),
                                "tot-cons": miss(),
                                "us-sme": miss(),
                                "intl-sme": miss(),
                                "tot-sme": num("83", "pct_0"),
                                "lg": num("36", "pct_0"),
                                "total": num("82", "pct_0"),
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
                        "Q4'21 % of Q4'19 callouts from the plot: US Consumer 108%, Total SME 83%, Total T&E 82%, Intl Consumer 78%, Large & Global Corporate 36%. Line omitted: 5 series exceeds line max 4, and vs-2019 interiors are unlabeled.",
                    ],
                )
            },
        )
    )

    # 9 dual region Q4 snapshots + per-pane tables. 8-quarter interiors unlabeled (#301 leftover).
    s09_us_cats = [("us", "US"), ("intl", "International"), ("total", "Total")]
    s09_gs_cats = [
        ("us-gs", "US G&S"),
        ("intl-gs", "Intl G&S"),
        ("tot-gs", "Total G&S"),
        ("us-te", "US T&E"),
        ("intl-te", "Intl T&E"),
        ("tot-te", "Total T&E"),
    ]
    slides.append(
        ordinary(
            9,
            "dual_chart",
            "Billed Business Growth by Region",
            {
                "charts": [
                    pane(
                        gbar(
                            "s09-us-intl",
                            "US vs. International",
                            s09_us_cats,
                            [
                                ser("vs19", "Q4'21 vs '19", ["16", "-1", "12"], "navy"),
                            ],
                            fmt="pct_0",
                            identity="pane_title",
                        ),
                        cat_support(
                            "s09-us-tbl",
                            "Q4'21",
                            s09_us_cats,
                            [
                                row(
                                    "vs19",
                                    "vs. '19",
                                    {
                                        "us": num("16", "pct_0"),
                                        "intl": num("-1", "pct_0"),
                                        "total": num("12", "pct_0"),
                                    },
                                ),
                                row(
                                    "yoy",
                                    "YoY",
                                    {
                                        "us": num("33", "pct_0"),
                                        "intl": num("32", "pct_0"),
                                        "total": num("33", "pct_0"),
                                    },
                                ),
                                row(
                                    "mix",
                                    "% of Total",
                                    {
                                        "us": num("78", "pct_0"),
                                        "intl": num("22", "pct_0"),
                                        "total": num("100", "pct_0"),
                                    },
                                ),
                            ],
                        ),
                    ),
                    pane(
                        gbar(
                            "s09-gs-te",
                            "G&S vs. T&E by Region",
                            s09_gs_cats,
                            [
                                ser(
                                    "vs19",
                                    "Q4'21 vs '19",
                                    ["26", "19", "24", "-10", "-36", "-18"],
                                    "navy",
                                ),
                            ],
                            fmt="pct_0",
                            identity="pane_title",
                        ),
                        cat_support(
                            "s09-gs-tbl",
                            "Q4'21",
                            s09_gs_cats,
                            [
                                row(
                                    "vs19",
                                    "vs. '19",
                                    {
                                        "us-gs": num("26", "pct_0"),
                                        "intl-gs": num("19", "pct_0"),
                                        "tot-gs": num("24", "pct_0"),
                                        "us-te": num("-10", "pct_0"),
                                        "intl-te": num("-36", "pct_0"),
                                        "tot-te": num("-18", "pct_0"),
                                    },
                                ),
                                row(
                                    "yoy",
                                    "YoY",
                                    {
                                        "us-gs": num("20", "pct_0"),
                                        "intl-gs": num("17", "pct_0"),
                                        "tot-gs": num("19", "pct_0"),
                                        "us-te": num("134", "pct_0"),
                                        "intl-te": num("127", "pct_0"),
                                        "tot-te": num("132", "pct_0"),
                                    },
                                ),
                                row(
                                    "mix",
                                    "% of Total",
                                    {
                                        "us-gs": num("62", "pct_0"),
                                        "intl-gs": num("17", "pct_0"),
                                        "tot-gs": num("79", "pct_0"),
                                        "us-te": num("15", "pct_0"),
                                        "intl-te": num("5", "pct_0"),
                                        "tot-te": num("21", "pct_0"),
                                    },
                                ),
                            ],
                        ),
                    ),
                ]
            },
            extra={
                "disclosure": disc(
                    "s09-disc",
                    "Notes",
                    [
                        "Note: All growth rates reflect FX-adjusted rates. See Annex 1 for reported billings growth rates. % of total may not foot due to rounding.",
                        "8-quarter interiors unlabeled (#301 leftover). Page-9 glyphs: axis ticks (100)/(80)/(60)/(40)/(20)/0/20, quarter labels, series names, Q4 tables vs-'19 16/(1)/12 and 26/19/24/(10)/(36)/(18). No second labeled plot point. Line requires two finite values per series; authored grouped bars of the labeled Q4 points plus per-pane tables.",
                    ],
                )
            },
        )
    )

    # 10 dual ending loans / receivables — PDF visual: six Q3/Q4 bars per pane,
    # year separators above, in-bar YoY on each bar (not year-grouped Q3 vs Q4).
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
                        Q3Q4,
                        [
                            ser(
                                "loans",
                                "Total Ending Loans",
                                ["88.1", "92.2", "73.1", "76.2", "79.4", "91.5"],
                                "primary_blue",
                            ),
                        ],
                        fmt="usd_1",
                        subtitle="$ in billions",
                        groups=YEAR_Q3Q4_GROUPS,
                        boxed_label=boxed(
                            "s10-loans-yoy",
                            "YoY Growth",
                            "pct_0",
                            "loans",
                            ["9", "8", "-17", "-17", "9", "20"],
                        ),
                        identity="pane_title",
                    ),
                    gbar(
                        "s10-rec",
                        "Total Ending CM Receivables (Q3-Q4)",
                        Q3Q4,
                        [
                            ser(
                                "rec",
                                "Total Ending CM Receivables",
                                ["56.6", "57.4", "40.8", "43.7", "48.8", "53.6"],
                                "navy",
                            ),
                        ],
                        fmt="usd_1",
                        subtitle="$ in billions",
                        groups=YEAR_Q3Q4_GROUPS,
                        boxed_label=boxed(
                            "s10-rec-yoy",
                            "YoY Growth",
                            "pct_0",
                            "rec",
                            ["2", "3", "-28", "-24", "19", "23"],
                        ),
                        identity="pane_title",
                    ),
                ]
            },
            extra={
                "disclosure": disc(
                    "s10-disc",
                    "Notes",
                    [
                        "Note: Total Loans reflects Card Member loans and Other loans.",
                    ],
                )
            },
        )
    )

    # 11 credit metrics — PDF visual: loan NWO bars 2.5%..0.6%, rec NWO 2.0%..0.3%;
    # 30+ strips under each pane; GCP strip has no dual_chart slot (Type B secondary).
    # Extraction reading order swapped loan NWO onto rec 30+; use PDF coordinates.
    slides.append(
        ordinary(
            11,
            "dual_chart",
            "Card Member Credit Metrics",
            {
                "charts": [
                    gbar(
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
                                ["2.5", "1.9", "1.4", "1.0", "0.6", "0.6"],
                                "primary_blue",
                            ),
                            ser(
                                "dq",
                                "30+ Days Past Due",
                                ["1.2", "1.0", "0.9", "0.6", "0.7", "0.7"],
                                "navy",
                            ),
                        ],
                        fmt="pct_1",
                    ),
                    gbar(
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
                                "Net Write-off Rates (excluding GCP)",
                                ["2.0", "1.0", "0.5", "0.3", "0.2", "0.3"],
                                "navy",
                            ),
                            ser(
                                "dq",
                                "30+ Days Past Due*",
                                ["0.9", "0.6", "0.6", "0.5", "0.5", "0.6"],
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
                    bar_mode="stacked",
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

    # 13 Total Reserves — PDF visual: total walk $4.3 / +$1.5 / $5.8 / ($2.2) / $3.6 / ($0.2) / $3.4.
    # Loan vs receivable interiors of the signed bridges are unlabeled as a split series; waterfall is the total flow.
    # Percent boxes sit under the four totals (Q1'20 4.6%/0.2%, not the extraction swap onto Q4'20).
    slides.append(
        ordinary(
            13,
            "single_chart",
            "Total Reserves",
            {
                "chart": waterfall(
                    "s13-rsv",
                    "Balance Sheet Credit Reserves*",
                    [
                        wstep("q1-20-beg", "Q1'20 Beginning Reserves", "total", "4.3"),
                        wstep("to-q4-20", "Change to Q4'20", "change", "1.5"),
                        wstep("q4-20-end", "Q4'20 Ending Reserves", "total", "5.8"),
                        wstep("to-q3-21", "Change to Q3'21", "change", "-2.2"),
                        wstep("q3-21-end", "Q3'21 Ending Reserves", "total", "3.6"),
                        wstep("to-q4-21", "Change to Q4'21", "change", "-0.2"),
                        wstep("q4-21-end", "Q4'21 Ending Reserves", "total", "3.4"),
                    ],
                    fmt="usd_1",
                    subtitle="$ in billions",
                ),
                "support": {
                    "support_type": "support_table",
                    "alignment": "independent",
                    "table": table(
                        "s13-pct",
                        "Reserves %",
                        [
                            ("q1-20", "Q1'20 Beginning"),
                            ("q4-20", "Q4'20 Ending"),
                            ("q3-21", "Q3'21 Ending"),
                            ("q4-21", "Q4'21 Ending"),
                        ],
                        [
                            row(
                                "loan-pct",
                                "Reserves as a % of Total loans",
                                {
                                    "q1-20": num("4.6", "pct_1"),
                                    "q4-20": num("7.3", "pct_1"),
                                    "q3-21": num("4.5", "pct_1"),
                                    "q4-21": num("3.7", "pct_1"),
                                },
                            ),
                            row(
                                "rec-pct",
                                "Reserves as a % of CM Receivables",
                                {
                                    "q1-20": num("0.2", "pct_1"),
                                    "q4-20": num("0.6", "pct_1"),
                                    "q3-21": num("0.1", "pct_1"),
                                    "q4-21": num("0.1", "pct_1"),
                                },
                            ),
                        ],
                    ),
                },
            },
            extra={
                "disclosure": disc(
                    "s13-disc",
                    "Notes",
                    [
                        "* Q1'20 - Q4'21 Balance Sheet credit reserve builds differ from P&L credit reserve builds due to other receivables and FX impacts. Reserve subtotals may not foot due to rounding.",
                        "Waterfall is the labeled total walk. Loan vs receivable interiors of the $1.5 / ($2.2) / ($0.2) stacks are not a second waterfall series.",
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

    # 15 Discount Revenue combo $B + rate; PDF visual: YoY boxes 7/6/(24)/(19)/33/36
    # (extraction listed 6/7/(19)/(24)/36/33). FY inset $25.7 / 25% / (2%).
    slides.append(
        ordinary(
            15,
            "single_chart",
            "Discount Revenue",
            {
                "chart": combo(
                    "s15-dr",
                    "Discount Revenue* (Q3-Q4)",
                    Q3Q4,
                    [
                        {
                            "series_id": "rev",
                            "name": "Discount Revenue $B",
                            "mark_type": "bar",
                            "values": ["6.6", "6.8", "5.0", "5.5", "6.7", "7.5"],
                            "color": "primary_blue",
                        },
                        {
                            "series_id": "rate",
                            "name": "Average Discount Rate",
                            "mark_type": "line",
                            "axis_key": "secondary",
                            "style": {"line_style": "solid", "marker": "circle"},
                            "values": ["2.39", "2.36", "2.27", "2.25", "2.32", "2.30"],
                            "color": "navy",
                        },
                    ],
                    bar_mode="grouped",
                    pfmt="usd_1",
                    sfmt="pct_2",
                    subtitle="$ in billions (on a reported basis) - % Increase/(decrease) vs. Prior year (FX-adjusted)",
                    groups=YEAR_Q3Q4_GROUPS,
                    boxed_label=boxed(
                        "s15-yoy",
                        "YoY Change",
                        "pct_0",
                        "rev",
                        ["7", "6", "-24", "-19", "33", "36"],
                    ),
                ),
                "support": fy_support(
                    "s15-fy", "FY'21", "dr", "Discount Revenue", "25.7", "25", "-2"
                ),
            },
            extra={
                "disclosure": disc(
                    "s15-disc",
                    "Notes",
                    [
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
                "chart": gbar(
                    "s16-ncf",
                    "Net Card Fees*",
                    ncf_cats,
                    [
                        ser(
                            "ncf",
                            "Net Card Fees $B",
                            [
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
                            "primary_blue",
                        ),
                    ],
                    fmt="usd_1",
                    subtitle="$ in billions (on a reported basis) - % Increase/(decrease) vs. Prior year (FX-adjusted)",
                    boxed_label=boxed(
                        "s16-yoy",
                        "YoY Change",
                        "pct_0",
                        "ncf",
                        [
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
                    ),
                    identity="pane_title",
                ),
                "support": fy_support(
                    "s16-fy", "FY'21", "ncf", "Net Card Fees", "5.2", "10", "28"
                ),
            },
            extra={
                "disclosure": disc(
                    "s16-disc",
                    "Notes",
                    [
                        "Note: Effective Q2'21 we prospectively changed the recognition of certain costs paid to a third party previously recognized over the 12-month card membership period in Net card fees.",
                        "* Net Card Fees YoY growth rates adjusted for FX are non-GAAP measures. See Annex 3 for Net Card Fees growth rates on a GAAP basis. See Slide 2 for an explanation of FX-adjusted information.",
                    ],
                )
            },
        )
    )

    # 17 Net Interest Income; PDF visual: YoY boxes 13/13/(15)/(17)/6/11
    # (extraction listed 13/13/(17)/(15)/11/6). FY inset $7.8 / (4%) / (10%).
    slides.append(
        ordinary(
            17,
            "single_chart",
            "Net Interest Income",
            {
                "chart": combo(
                    "s17-nii",
                    "Net Interest Income* (Q3-Q4)",
                    Q3Q4,
                    [
                        {
                            "series_id": "nii",
                            "name": "Net Interest Income $B",
                            "mark_type": "bar",
                            "values": ["2.2", "2.3", "1.9", "1.9", "2.0", "2.1"],
                            "color": "primary_blue",
                        },
                        {
                            "series_id": "yield",
                            "name": "WW Net Interest Yield on CM Loans**",
                            "mark_type": "line",
                            "axis_key": "secondary",
                            "style": {"line_style": "solid", "marker": "circle"},
                            "values": ["11.2", "11.3", "11.6", "11.4", "10.8", "10.3"],
                            "color": "navy",
                        },
                    ],
                    bar_mode="grouped",
                    pfmt="usd_1",
                    sfmt="pct_1",
                    subtitle="$ in billions (on a reported basis) - % Increase/(decrease) vs. Prior year (FX-adjusted)",
                    groups=YEAR_Q3Q4_GROUPS,
                    boxed_label=boxed(
                        "s17-yoy",
                        "YoY Change",
                        "pct_0",
                        "nii",
                        ["13", "13", "-15", "-17", "6", "11"],
                    ),
                ),
                "support": fy_support(
                    "s17-fy", "FY'21", "nii", "Net Interest Income", "7.8", "-4", "-10"
                ),
            },
            extra={
                "disclosure": disc(
                    "s17-disc",
                    "Notes",
                    [
                        "* Net Interest Income YoY growth rates adjusted for FX are non-GAAP measures. See Annex 4 for Net Interest Income growth rates on a GAAP basis. See Slide 2 for an explanation of FX-adjusted information. ** See Annex 5 for a reconciliation of net interest yield, a non-GAAP measure.",
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

    # 20 Marketing + NCA — PDF visual: dual grouped_bar plus unlabeled Value Injection
    # hatch on Marketing and a FY'21 $5.3 inset. Page-20 glyphs have no hatch-split
    # dollars, so Marketing stays one total series (#298 leftover). Hatch fill recipe
    # is out of scope. FY $5.3 inset is optional on shared dual support.
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
                    [
                        "FY'21 Marketing $5.3B. Value Injection hatch has no numeric labels on the PDF (#298 leftover); hatch dollars were not glyph-readable, so Marketing stays one total series ($1.1 / $1.0 / $1.0 / $1.3 / $1.4 / $1.6). Do not invent hatch split dollars. FY $5.3 inset is optional on shared dual support.",
                    ],
                )
            },
        )
    )

    # 21 Capital — CET1 bars + Capital Return bars + shared Q4 dividend strip. Not 3-pane.
    slides.append(
        ordinary(
            21,
            "dual_chart",
            "Capital",
            {
                "charts": [
                    pane(
                        gbar(
                            "s21-cet1",
                            "Common Equity Tier 1",
                            [("q4-19", "Q4'19"), ("q4-20", "Q4'20"), ("q4-21", "Q4'21")],
                            [ser("cet1", "CET1 Ratio", ["10.7", "13.5", "10.5"], "navy")],
                            fmt="pct_1",
                            subtitle="CET1 Ratio Target: 10-11%",
                            identity="pane_title",
                        )
                    ),
                    pane(
                        gbar(
                            "s21-ret",
                            "Capital Return",
                            [("fy-19", "FY'19"), ("fy-20", "FY'20"), ("fy-21", "FY'21")],
                            [ser("ret", "Capital Return", ["6.0", "2.3", "9.0"], "primary_blue")],
                            fmt="usd_1",
                            subtitle="$ in billions",
                            identity="pane_title",
                        )
                    ),
                ],
                "support": metric_strip(
                    "s21-div",
                    [
                        {
                            "metric_id": "div-q419",
                            "label": "Q4'19 Dividend per Common Share*",
                            "value": num("0.43", "usd_2"),
                        },
                        {
                            "metric_id": "div-q420",
                            "label": "Q4'20 Dividend per Common Share*",
                            "value": num("0.43", "usd_2"),
                        },
                        {
                            "metric_id": "div-q421",
                            "label": "Q4'21 Dividend per Common Share*",
                            "value": num("0.43", "usd_2"),
                        },
                    ],
                ),
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
    )

    # 22 Growth Plan — three horizon cards. PDF timeline bars have no recipe; omit.
    slides.append(
        ordinary(
            22,
            "feature_cards",
            "The Growth Plan",
            {
                "cards": [
                    {
                        "card_id": "guide-2022",
                        "heading": "2022 Guidance",
                        "detail": "Revenue Growth 18-20%. EPS $9.25-$9.65.",
                    },
                    {
                        "card_id": "expect-2023",
                        "heading": "2023 Expectations",
                        "detail": "Higher than long-term aspirational levels of Revenue growth.",
                    },
                    {
                        "card_id": "aspire-2024",
                        "heading": "2024+ Aspiration",
                        "detail": "Revenue Growth in excess of 10%. EPS Growth Mid-teens.",
                    },
                ]
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

    # 25 Global Consumer G&S — 8-quarter Online/Offline/G&S line + two Q4 annex peers.
    # Interiors unlabeled (#301 leftover); Q4'21 endpoints 42/26/10 are one finite value per series.
    # Grouped bar of those labeled Q4 points plus the two Q4 tables.
    s25_cats = [("online", "Online"), ("gs", "G&S"), ("offline", "Offline")]
    slides.append(
        ordinary(
            25,
            "chart_grouped_annex",
            "Global Consumer G&S Growth",
            {
                "chart": gbar(
                    "s25-line",
                    "G&S: Online vs. Offline",
                    s25_cats,
                    [
                        ser("vs19", "Q4'21 vs '19", ["42", "26", "10"], "navy"),
                    ],
                    fmt="pct_0",
                    subtitle="% Increase/(decrease) vs. 2019 (FX-adjusted)",
                    identity="pane_title",
                ),
                "tables": [
                    {
                        "heading": "Global Consumer G&S",
                        "short_heading": "G&S",
                        "table": table(
                            "s25-gs",
                            "Q4'21",
                            [("online", "Online"), ("offline", "Offline"), ("total", "Total")],
                            [
                                row(
                                    "vs19",
                                    "vs. '19",
                                    {
                                        "online": num("42", "pct_0"),
                                        "offline": num("10", "pct_0"),
                                        "total": num("26", "pct_0"),
                                    },
                                ),
                                row(
                                    "yoy",
                                    "YoY",
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
                            "Q4'21",
                            [("online", "Online"), ("offline", "Offline"), ("total", "Total")],
                            [
                                row(
                                    "vs19",
                                    "vs. '19",
                                    {
                                        "online": num("55", "pct_0"),
                                        "offline": num("9", "pct_0"),
                                        "total": num("29", "pct_0"),
                                    },
                                ),
                                row(
                                    "yoy",
                                    "YoY",
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
                ],
            },
            section="appendix",
            extra={
                "disclosure": disc(
                    "s25-disc",
                    "Notes",
                    [
                        "Note: All growth rates reflect FX-adjusted rates. See Annex 1 for reported billings growth rates.",
                        "* Holiday spend reflects Q4'21 Consumer retail spending at department stores/big box, shops and supermarkets/consumables.",
                        "8-quarter Online/Offline/G&S interiors unlabeled (#301 leftover). Page-25 glyphs: axis ticks (40)/(30)/(20)/(10)/0/10/20/30/40/50, quarter labels, series names, Q4 tables vs-'19 42/10/26 and Holiday 55/9/29. No second labeled plot point. Line requires two finite values per series; authored grouped bar of Q4'21 vs '19 endpoints 42/26/10 plus the two Q4 tables.",
                    ],
                )
            },
        )
    )

    # 26 T&E by industry — PDF visual: 8-quarter vs-2019 5-series line plus Q4 table.
    # Only Q4'21 vs '19 (10/-24/-43/-14/-18) are labeled. Line requires at least two
    # finite values per series, so a Q4-only endpoint line is illegal; interiors unread.
    # Total T&E is a 5th series (line max 4) even if interiors were readable (#299 leftover).
    slides.append(
        ordinary(
            26,
            "data_table",
            "Travel & Entertainment Billed Business",
            {
                "table": table(
                    "s26-te",
                    "Q4'21",
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
                            "vs. '19",
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
                            "YoY",
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
                        "Line omitted: Q1'20-Q3'21 vs-2019 interiors unlabeled. Line requires at least two finite values per series; Q4'21 endpoints 10/(24)/(43)/(14)/(18) alone are illegal. Total T&E is also a 5th series (line max 4).",
                    ],
                )
            },
        )
    )

    # 27 two mix donuts. Loan 68/12/20; Receivables 28/14/24/34. Do not kernel-enforce sum-to-100.
    slides.append(
        ordinary(
            27,
            "dual_chart",
            "Worldwide Total Loans and Card Member Receivables Mix",
            {
                "charts": [
                    pane(
                        donut(
                            "s27-loans",
                            "Q4'21 Total Loan Mix",
                            [
                                ("us", "U.S. Consumer", "68"),
                                ("intl", "Intl. Consumer", "12"),
                                ("sb", "Small Business", "20"),
                            ],
                        )
                    ),
                    pane(
                        donut(
                            "s27-rec",
                            "Q4'21 Card Member Receivables Mix",
                            [
                                ("us", "U.S. Consumer", "28"),
                                ("intl", "Intl. Consumer", "14"),
                                ("corp", "Corporate Card", "24"),
                                ("sb", "Small Business", "34"),
                            ],
                        )
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
                    ],
                )
            },
        )
    )

    # 28 FRP balances — PDF visual: stacked Delinquent / FRP / CPR plus below-plot Total Loans and CM Receivables boxes.
    s28_cats = [
        ("dec-19", "Dec'19"),
        ("apr-20", "Apr'20"),
        ("dec-20", "Dec'20"),
        ("sep-21", "Sep'21"),
        ("dec-21", "Dec'21"),
    ]
    slides.append(
        ordinary(
            28,
            "single_chart",
            "Delinquent and Financial Relief Program Balances",
            {
                "chart": sbar(
                    "s28-frp",
                    "Delinquent and FRP Balances",
                    s28_cats,
                    [
                        ser("delinq", "Delinquent", ["2.1", "2.0", "1.0", "0.8", "0.9"], "navy"),
                        ser("frp", "Financial Relief Programs (FRP) Enrolled***", ["0.7", "0.9", "3.0", "1.5", "1.3"], "primary_blue"),
                        ser("cpr", "CPR Program Enrolled*", ["0.0", "8.5", "0.0", "0.0", "0.0"], "sky_blue"),
                    ],
                    fmt="usd_1",
                    subtitle="$ in billions",
                    totals=["2.8", "11.5", "4.0", "2.3", "2.2"],
                    tot_fmt="usd_1",
                ),
                "support": {
                    "support_type": "support_table",
                    "alignment": "category",
                    "table": table(
                        "s28-boxes",
                        "Balances $B",
                        s28_cats,
                        [
                            row(
                                "loans",
                                "Total Loans",
                                {
                                    "dec-19": num("1.9", "usd_1"),
                                    "apr-20": num("7.1", "usd_1"),
                                    "dec-20": num("3.0", "usd_1"),
                                    "sep-21": num("1.7", "usd_1"),
                                    "dec-21": num("1.6", "usd_1"),
                                },
                            ),
                            row(
                                "rec",
                                "Card Member Receivables",
                                {
                                    "dec-19": num("0.9", "usd_1"),
                                    "apr-20": num("4.4", "usd_1"),
                                    "dec-20": num("1.0", "usd_1"),
                                    "sep-21": num("0.6", "usd_1"),
                                    "dec-21": num("0.6", "usd_1"),
                                },
                            ),
                        ],
                    ),
                },
            },
            section="appendix",
            extra={
                "disclosure": disc(
                    "s28-disc",
                    "Notes",
                    [
                        "Note: Total Loans reflects Card Member loans and Other loans. CPR = Customer Pandemic Relief Program. * Represents the balances at enrollment for card members in the CPR program as of April 19, 2020. *** FRP balance is a non-GAAP measure and excludes delinquent balances that are also reported in the Delinquent category. See Annex 7.",
                    ],
                )
            },
        )
    )

    # 29 GCP credit — PDF visual: grouped bars 2.4/0.7/0.4/0.5/0.2/0.2 plus Q2'21 bankruptcy side table.
    slides.append(
        ordinary(
            29,
            "single_chart",
            "Global Corporate Payments Card Member Credit Metrics",
            {
                "chart": gbar(
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
                    identity="pane_title",
                ),
                "support": {
                    "support_type": "support_table",
                    "alignment": "independent",
                    "table": table(
                        "s29-bk",
                        "Client Bankruptcy Recovery Impact to Net Write-Offs Increase/(Decrease) $M",
                        [("q2-21", "Q2'21")],
                        [
                            row(
                                "nwo",
                                "Net Write-Off Amount/(Recovery)",
                                {"q2-21": num("-37", "usd_0")},
                            ),
                            row(
                                "ins",
                                "Credit Insurance Claim (Proceeds)/Repayment within Other, net",
                                {"q2-21": num("33", "usd_0")},
                            ),
                            row(
                                "pti",
                                "Pre-tax Income",
                                {"q2-21": num("4", "usd_0")},
                            ),
                        ],
                    ),
                },
            },
            section="appendix",
            extra={
                "disclosure": disc(
                    "s29-disc",
                    "Notes",
                    [
                        "* Adjusted for Client bankruptcy impact of ($37M) for Q2'21. Adjusted Net Write-off rates are a non-GAAP measure, see Annex 8 for Net Write-off rates on a GAAP basis.",
                    ],
                )
            },
        )
    )

    # 30 macro assumptions — PDF visual: two 4-series lines (US Unemployment Rate %,
    # US GDP Growth* %) Q3'20-Q4'23 (Q3/Q4 Baseline and Downside). No labeled
    # endpoints (#300 leftover); axis ticks only. dual_chart line is legal but each
    # series needs at least two finite values; interiors unlabeled, so the charts
    # cannot be authored. Keep narrative; do not invent series values.
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
                            "Lines omitted: no labeled endpoints (#300 leftover). Q3'20-Q4'23 quarterly glyphs unlabeled on both panes. dual_chart line requires at least two finite values per series; axis ticks (Unemployment 0-18%, GDP (10%)-40%) are not series values. Do not invent series.",
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
                    totals=["138", "132", "126"],
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

    # 32 FX — Q1'21-Q4'21 Reported vs FX-Adj interiors unlabeled (#301 leftover);
    # grouped bars of labeled currency points + shared table.
    s32_fx_cats = [
        ("eur", "Euro EUR"),
        ("gbp", "UK GBP"),
        ("jpy", "Japan JPY"),
        ("aud", "Australia $"),
        ("cad", "Canada $"),
        ("mxn", "Mexico $"),
    ]
    slides.append(
        ordinary(
            32,
            "dual_chart",
            "FX Impact on Network Volumes and Revenue Growth",
            {
                "charts": [
                    pane(
                        gbar(
                            "s32-nv",
                            "Network Volumes",
                            s32_fx_cats,
                            [
                                ser(
                                    "share",
                                    "Approx Q4'21 Network Volumes % of Total",
                                    ["4", "5", "5", "3", "2", "1"],
                                    "navy",
                                ),
                            ],
                            fmt="pct_0",
                            identity="pane_title",
                        )
                    ),
                    pane(
                        gbar(
                            "s32-rev",
                            "Revenue Net of Interest Expense",
                            s32_fx_cats,
                            [
                                ser(
                                    "fx",
                                    "YoY% change in USD* vs Currency",
                                    ["7", "1", "11", "6", "-1", "3"],
                                    "primary_blue",
                                ),
                            ],
                            fmt="pct_0",
                            identity="pane_title",
                        )
                    ),
                ],
                "support": indep_support(
                    "s32-fx",
                    "Metric",
                    s32_fx_cats,
                    [
                        row(
                            "share",
                            "Approx Q4'21 Network Volumes % of Total",
                            {
                                "eur": num("4", "pct_0"),
                                "gbp": num("5", "pct_0"),
                                "jpy": num("5", "pct_0"),
                                "aud": num("3", "pct_0"),
                                "cad": num("2", "pct_0"),
                                "mxn": num("1", "pct_0"),
                            },
                        ),
                        row(
                            "fx",
                            "YoY% change in USD* vs Currency Strengthened/(Weakened)",
                            {
                                "eur": num("7", "pct_0"),
                                "gbp": num("1", "pct_0"),
                                "jpy": num("11", "pct_0"),
                                "aud": num("6", "pct_0"),
                                "cad": num("-1", "pct_0"),
                                "mxn": num("3", "pct_0"),
                            },
                        ),
                    ],
                ),
            },
            section="appendix",
            extra={
                "disclosure": disc(
                    "s32-disc",
                    "Notes",
                    [
                        "Note: Network Volumes is based on where the issuer is located and includes both proprietary and non-proprietary cards. See Slide 2 for an explanation of FX-adjusted information.",
                        "* Represents percentage change in foreign currency exchange rates at 2021 and 2020 December month-end, respectively, per Bloomberg.",
                        "Q1'21-Q4'21 Reported vs FX-Adj interiors unlabeled (#301 leftover). Page-32 glyphs: axis ticks (15%)/50%, quarter labels, Reported/FX Adj. series names, 6-currency table 4/5/5/3/2/1 and 7/1/11/6/(1)/3. No labeled plot endpoints. Line requires two finite values per series; axis ticks are not observations. Authored grouped bars of the labeled 6-currency points plus the shared independent currency table.",
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

    # 36 ESG highlights — full nested PDF bullets as three lists (schema has no nested lists).
    # Hyphenation artifacts from extraction ("w orkforce") restored from the PDF page.
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
                            "Promoting Diversity, Equity, and Inclusion (DE&I): We are committed to supporting a diverse, equitable, and inclusive workforce, marketplace, and society.",
                            "We announced a $1 Billion DE&I Action Plan in October 2020, which outlined our initiatives to promote DE&I for our colleagues, customers, and communities. From October 2020 through December 2021, we spent more than $800 million on DE&I initiatives. Spending includes payments to diverse suppliers, financial assistance for minority-owned businesses, colleague education and training, investments in pay equity, and philanthropic contributions.",
                            "In our 2020-2021 ESG Report, we provided greater transparency on our progress, building on the enhanced disclosures and 2020 U.S. EEO-1 data published in our 2021 Interim ESG update earlier in 2021. We added new disclosures related to median pay gap, promotion, recruitment and retention of colleagues and shared our new ESG goal to maintain 100% pay equity.",
                            "We released our inaugural standalone DE&I Report in 2021, which spotlights our DE&I efforts, including the diversity data disclosed in our ESG report, and provides an overview of our history, the culture we've built, and our commitment to creating an equitable future.",
                        ],
                    ),
                    bullets(
                        "confidence",
                        [
                            "Building Financial Confidence: We are committed to providing products and services to help people and businesses build financial resilience including those that have been negatively affected by the economic impacts of the pandemic.",
                            "We launched our Let's Go Shop Small campaign during summer 2021 with a $100 million commitment to promote spending with small businesses globally as part of our year-round Shop Small initiative.",
                            "We announced new goals, including providing access to credit to at least 4 million individuals from underserved or underrepresented populations from 2021 through 2025, providing at least 5 million individuals with tools, resources, and educational content to improve financial well-being from 2021 through 2025 and contributing $500M in community grants to support resilient and equitable communities.",
                        ],
                    ),
                    bullets(
                        "climate",
                        [
                            "Advancing Climate Solutions: We are enhancing our efforts to help customers and communities transition to a low-carbon future. Recently announced goals include:",
                            "We have committed to net-zero emissions by 2035 in line with the Science Based Targets initiative (SBTi) and became a Task Force on Climate Related Financial Disclosures (TCFD) supporter to help enhance management of our climate risks. As a carbon neutral company across our operations since 2018, we will now also work with suppliers to reduce their impact on our value chain by inviting them to track, reduce, and eventually neutralize their own operational greenhouse gas emissions. We will also pilot low carbon production innovations, including carbon tracking and offset solutions by the end of 2022.",
                            "We plan to provide $10 million in philanthropic funding to support initiatives, partnerships, and programs that address the adverse effects of climate change on communities from 2021 through 2025 and made our first climate-focused grant to support youth-led climate initiatives and adaptation projects in parts of Africa and Asia. Additionally, we will continue to engage colleagues in sustainability initiatives through the Green2Gether program and have joined coalitions, such as the World Economic Forum's Clean Skies for Tomorrow coalition to complement our other efforts.",
                        ],
                    ),
                ]
            },
            section="appendix",
        )
    )

    # 37 Annex 1 (1 of 2) — full 18-col compact period matrix from the PDF.
    slides.append(
        ordinary(
            37,
            "annex_table",
            "Annex 1 Network Volumes - Reported & FX-Adjusted",
            {
                "density": "compact",
                "table": annex_pct_table(
                    "s37-a1",
                    "Metric",
                    ANNEX_18,
                    [
                        ("ic-r", "Int'l Consumer Reported", ["8", "10", "10", "11", "-6", "-41", "-21", "-17", "-10", "59", "27", "28", "23", "-16", "-6", "0", "7", "-3"]),
                        ("ic-fx", "Int'l Consumer FX-Adjusted", ["16", "15", "14", "11", "-2", "-39", "-23", "-20", "-17", "46", "24", "32", "19", "-19", "-11", "-4", "5", "-7"]),
                        ("gc-r", "Global Consumer Reported", ["7", "8", "9", "8", "-3", "-35", "-17", "-12", "-4", "62", "34", "34", "29", "-7", "6", "11", "18", "7"]),
                        ("gc-fx", "Global Consumer FX-Adjusted", ["9", "10", "10", "8", "-2", "-34", "-18", "-13", "-6", "58", "34", "35", "28", "-8", "4", "9", "17", "6"]),
                        ("gcs-r", "Global Commercial (GCS) Reported", ["7", "6", "5", "5", "-6", "-36", "-23", "-18", "-10", "45", "28", "29", "21", "-16", "-8", "-1", "6", "-4"]),
                        ("gcs-fx", "Global Commercial (GCS) FX-Adjusted", ["8", "7", "5", "5", "-5", "-36", "-23", "-19", "-12", "43", "28", "30", "20", "-16", "-8", "-1", "6", "-5"]),
                        ("bb-r", "Billed Business Reported", ["7", "7", "6", "7", "-4", "-35", "-20", "-15", "-7", "53", "31", "32", "25", "-11", "-1", "5", "12", "2"]),
                        ("bb-fx", "Billed Business FX-Adjusted", ["9", "8", "7", "7", "-3", "-35", "-20", "-16", "-9", "51", "31", "33", "24", "-12", "-2", "4", "12", "1"]),
                        ("pv-r", "Processed Volumes Reported", ["-9", "-6", "-6", "-4", "-11", "-25", "-14", "-8", "3", "33", "20", "13", "16", "-9", "0", "4", "4", "0"]),
                        ("pv-fx", "Processed Volumes FX-Adjusted", ["-3", "-2", "-3", "-2", "-8", "-22", "-13", "-10", "-1", "26", "18", "15", "14", "-9", "-2", "3", "3", "-1"]),
                        ("ww-r", "Worldwide Reported", ["4", "5", "4", "5", "-5", "-34", "-19", "-14", "-6", "50", "29", "29", "24", "-11", "-1", "5", "11", "1"]),
                        ("ww-fx", "Worldwide FX-Adjusted", ["7", "7", "6", "5", "-4", "-33", "-19", "-15", "-8", "46", "29", "30", "23", "-11", "-2", "4", "11", "1"]),
                    ],
                ),
            },
            section="appendix",
            extra={
                "content": {"subtitle": "% Increase/(decrease) vs. Prior year"},
                "disclosure": disc(
                    "s37-disc",
                    "Notes",
                    [
                        "* See Slide 2 for an explanation of FX-adjusted information. 2021 vs. 2019 YoY% assumes 2021 foreign exchange rates apply to 2019 results.",
                    ],
                ),
            },
        )
    )

    # 38 Annex 1 (2 of 2) — full 14-col compact period matrix from the PDF.
    slides.append(
        ordinary(
            38,
            "annex_table",
            "Annex 1 Network Volumes - Reported & FX-Adjusted",
            {
                "density": "compact",
                "table": annex_pct_table(
                    "s38-a1b",
                    "Metric",
                    ANNEX_14,
                    [
                        ("lg-r", "Large & Global Corporate Reported", ["-20", "-64", "-54", "-50", "-43", "37", "26", "34", "3", "-54", "-51", "-42", "-33", "-45"]),
                        ("lg-fx", "Large & Global Corporate FX-Adjusted", ["-19", "-64", "-54", "-51", "-44", "34", "25", "34", "2", "-54", "-51", "-43", "-33", "-45"]),
                        ("isme-r", "Int'l SME Reported", ["2", "-29", "-16", "-10", "-1", "50", "28", "27", "24", "0", "5", "6", "13", "7"]),
                        ("isme-fx", "Int'l SME FX-Adjusted", ["7", "-26", "-17", "-13", "-9", "38", "27", "31", "20", "-3", "1", "3", "12", "4"]),
                        ("sme-r", "SME Reported", ["-1", "-27", "-13", "-8", "-1", "46", "28", "28", "24", "-2", "7", "12", "17", "9"]),
                        ("sme-fx", "SME FX-Adjusted", ["0", "-26", "-13", "-9", "-3", "44", "28", "29", "24", "-3", "6", "11", "17", "8"]),
                    ],
                ),
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

    # 39 Annex 2 Discount Revenue — PDF visual: 12 period columns Q3'18-FY'21.
    slides.append(
        ordinary(
            39,
            "annex_table",
            "Annex 2 Discount Revenue - Reported & FX-Adjusted",
            {
                "table": table(
                    "s39-a2",
                    "Metric",
                    ANNEX_12,
                    [
                        mixed_row(
                            "gaap",
                            "GAAP Discount Revenue",
                            ANNEX_12,
                            ["6.2", "6.5", "24.7", "6.6", "6.8", "26.2", "5.0", "5.5", "20.4", "6.7", "7.5", "25.7"],
                            "usd_1",
                        ),
                        mixed_row(
                            "fx",
                            "FX-Adjusted Discount Revenue*",
                            ANNEX_12,
                            ["6.1", "6.4", "24.5", "6.6", "6.9", "26.1", "5.0", "5.5", "20.5", None, None, None],
                            "usd_1",
                        ),
                        mixed_row(
                            "fx19",
                            "FX-Adjusted Discount Revenue**",
                            ANNEX_12,
                            [None, None, None, None, None, "26.3", None, None, None, None, None, None],
                            "usd_1",
                        ),
                        mixed_row(
                            "yoy-gaap",
                            "YoY% Inc/(Dec) in GAAP Discount Revenue",
                            ANNEX_12,
                            [None, None, None, "6", "6", "6", "-24", "-19", "-22", "34", "35", "26"],
                            "pct_0",
                        ),
                        mixed_row(
                            "yoy-fx",
                            "YoY% Inc/(Dec) in FX-Adjusted Discount Revenue*",
                            ANNEX_12,
                            [None, None, None, "7", "6", "7", "-24", "-19", "-22", "33", "36", "25"],
                            "pct_0",
                        ),
                        mixed_row(
                            "vs19-gaap",
                            "2021 vs 2019 GAAP Discount Revenue",
                            ANNEX_12,
                            [None, None, None, None, None, None, None, None, None, None, None, "-2"],
                            "pct_0",
                        ),
                        mixed_row(
                            "vs19-fx",
                            "2021 vs 2019 FX-Adjusted Discount Revenue**",
                            ANNEX_12,
                            [None, None, None, None, None, None, None, None, None, None, None, "-2"],
                            "pct_0",
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
                    ],
                ),
            },
        )
    )

    # 40 Annex 3 Net Card Fees — full 20-col compact matrix from the PDF.
    slides.append(
        ordinary(
            40,
            "annex_table",
            "Annex 3 Net Card Fees - Reported & FX-Adjusted",
            {
                "density": "compact",
                "table": table(
                    "s40-a3",
                    "Metric",
                    ANNEX_20,
                    [
                        mixed_row(
                            "gaap",
                            "GAAP Revenues Net Card Fees",
                            ANNEX_20,
                            ["0.8", "0.8", "0.9", "0.9", "3.4", "0.9", "1.0", "1.0", "1.1", "4.0", "1.1", "1.1", "1.2", "1.2", "4.7", "1.3", "1.3", "1.3", "1.3", "5.2"],
                            "usd_1",
                        ),
                        mixed_row(
                            "fx",
                            "FX-Adjusted Net Card Fees*",
                            ANNEX_20,
                            ["0.8", "0.8", "0.9", "0.9", "3.4", "0.9", "1.0", "1.0", "1.1", "4.0", "1.1", "1.2", "1.2", "1.2", "4.7", None, None, None, None, None],
                            "usd_1",
                        ),
                        mixed_row(
                            "fx19",
                            "FX-Adjusted Net Card Fees**",
                            ANNEX_20,
                            [None, None, None, None, None, None, None, None, None, "4.1", None, None, None, None, None, None, None, None, None, None],
                            "usd_1",
                        ),
                        mixed_row(
                            "yoy-gaap",
                            "YoY% Inc/(Dec) in GAAP Net Card Fees",
                            ANNEX_20,
                            [None, None, None, None, None, "14", "17", "19", "20", "17", "18", "15", "15", "13", "15", "13", "13", "10", "10", "11"],
                            "pct_0",
                        ),
                        mixed_row(
                            "yoy-fx",
                            "YoY% Inc/(Dec) in FX-Adjusted Net Card Fees*",
                            ANNEX_20,
                            [None, None, None, None, None, "17", "19", "20", "20", "19", "19", "17", "15", "12", "16", "10", "10", "10", "11", "10"],
                            "pct_0",
                        ),
                        mixed_row(
                            "vs19-gaap",
                            "2021 vs 2019 YoY% Inc/(Dec) in GAAP Net Card Fees",
                            ANNEX_20,
                            [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, "29"],
                            "pct_0",
                        ),
                        mixed_row(
                            "vs19-fx",
                            "2021 vs 2019 YoY% Inc/(Dec) in FX-Adjusted Net Card Fees**",
                            ANNEX_20,
                            [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, "28"],
                            "pct_0",
                        ),
                    ],
                ),
            },
            section="appendix",
            extra={
                "content": {"subtitle": "$ in billions"},
                "disclosure": disc(
                    "s40-disc",
                    "Notes",
                    ["* See Slide 2 for an explanation of FX-adjusted information. ** 2021 vs. 2019 YoY% assumes 2021 foreign exchange rates apply to 2019 results."],
                )
            },
        )
    )

    # 41 Annex 4 NII — PDF visual: 12 period columns Q3'18-FY'21.
    slides.append(
        ordinary(
            41,
            "annex_table",
            "Annex 4 Net Interest Income - Reported & FX-Adjusted",
            {
                "table": table(
                    "s41-a4",
                    "Metric",
                    ANNEX_12,
                    [
                        mixed_row(
                            "gaap",
                            "GAAP Net Interest Income",
                            ANNEX_12,
                            ["2.0", "2.0", "7.7", "2.2", "2.3", "8.6", "1.9", "1.9", "8.0", "2.0", "2.1", "7.7"],
                            "usd_1",
                        ),
                        mixed_row(
                            "fx",
                            "FX-Adjusted Net Interest Income*",
                            ANNEX_12,
                            ["1.9", "2.0", "7.6", "2.2", "2.3", "8.6", "1.9", "1.9", "8.0", None, None, None],
                            "usd_1",
                        ),
                        mixed_row(
                            "fx19",
                            "FX-Adjusted Net Interest Income**",
                            ANNEX_12,
                            [None, None, None, None, None, "8.6", None, None, None, None, None, None],
                            "usd_1",
                        ),
                        mixed_row(
                            "yoy-gaap",
                            "YoY% Inc/(Dec) in GAAP Net Interest Income",
                            ANNEX_12,
                            [None, None, None, "12", "12", "12", "-15", "-17", "-7", "6", "11", "-3"],
                            "pct_0",
                        ),
                        mixed_row(
                            "yoy-fx",
                            "YoY% Inc/(Dec) in FX-Adjusted Net Interest Income*",
                            ANNEX_12,
                            [None, None, None, "13", "13", "13", "-15", "-17", "-7", "6", "11", "-4"],
                            "pct_0",
                        ),
                        mixed_row(
                            "vs19-gaap",
                            "2021 vs 2019 GAAP Net Interest Income",
                            ANNEX_12,
                            [None, None, None, None, None, None, None, None, None, None, None, "-10"],
                            "pct_0",
                        ),
                        mixed_row(
                            "vs19-fx",
                            "2021 vs 2019 FX-Adjusted Net Interest Income**",
                            ANNEX_12,
                            [None, None, None, None, None, None, None, None, None, None, None, "-10"],
                            "pct_0",
                        ),
                    ],
                )
            },
            section="appendix",
            extra={
                "content": {"subtitle": "$ in billions"},
                "disclosure": disc(
                    "s41-disc",
                    "Notes",
                    ["* See Slide 2 for an explanation of FX-adjusted information. ** 2021 vs. 2019 YoY% assumes 2021 foreign exchange rates apply to 2019 results."],
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

    # 43 Annex 6 (1 of 2) — full 20-col compact matrix from the PDF.
    slides.append(
        ordinary(
            43,
            "annex_table",
            "Annex 6 Revenues Net of Interest Expense",
            {
                "density": "compact",
                "table": table(
                    "s43-a6",
                    "Metric",
                    ANNEX_20,
                    [
                        mixed_row(
                            "gaap",
                            "GAAP Revenues Net of Interest Expense",
                            ANNEX_20,
                            ["9.7", "10.0", "10.1", "10.5", "40.3", "10.3", "10.8", "11.0", "11.4", "43.6", "10.3", "7.7", "8.8", "9.4", "36.1", "9.1", "10.2", "10.9", "12.1", "42.4"],
                            "usd_1",
                        ),
                        mixed_row(
                            "fx",
                            "FX-Adjusted Revenues Net of Interest*",
                            ANNEX_20,
                            ["9.5", "9.9", "10.0", "10.5", "39.9", "10.2", "10.7", "11.0", "11.4", "43.4", "10.5", "7.8", "8.8", "9.3", "36.3", None, None, None, None, None],
                            "usd_1",
                        ),
                        mixed_row(
                            "yoy-gaap",
                            "YoY% Inc/(Dec) in GAAP Revenue Net of Interest",
                            ANNEX_20,
                            [None, None, None, None, None, "7", "8", "8", "9", "8", "-1", "-29", "-20", "-18", "-17", "-12", "33", "25", "30", "17"],
                            "pct_0",
                        ),
                        mixed_row(
                            "yoy-fx",
                            "YoY% Inc/(Dec) in FX-Adjusted Revenues Net of Interest*",
                            ANNEX_20,
                            [None, None, None, None, None, "9", "10", "9", "9", "9", "1", "-28", "-20", "-18", "-17", "-13", "31", "24", "31", "17"],
                            "pct_0",
                        ),
                    ],
                ),
            },
            section="appendix",
            extra={
                "content": {"subtitle": "$ in billions"},
                "disclosure": disc(
                    "s43-disc",
                    "Notes",
                    ["* See Slide 2 for an explanation of FX-adjusted information."],
                )
            },
        )
    )

    # 44 Annex 6 (2 of 2) — PDF visual: 10 period columns Q1'19-FY'19 + Q1'21-FY'21.
    slides.append(
        ordinary(
            44,
            "annex_table",
            "Annex 6 Revenues Net of Interest Expense",
            {
                "table": table(
                    "s44-a6b",
                    "Metric",
                    ANNEX_10,
                    [
                        mixed_row(
                            "gaap",
                            "GAAP Revenues Net of Interest Expense",
                            ANNEX_10,
                            ["10.3", "10.8", "11.0", "11.4", "43.6", "9.1", "10.2", "10.9", "12.1", "42.4"],
                            "usd_1",
                        ),
                        mixed_row(
                            "fx",
                            "FX-Adjusted Revenues Net of Interest*",
                            ANNEX_10,
                            ["10.4", "10.9", "11.1", "11.4", "43.7", None, None, None, None, None],
                            "usd_1",
                        ),
                        mixed_row(
                            "vs19-gaap",
                            "2021 vs 2019 YoY% GAAP Revenue Net of Interest",
                            ANNEX_10,
                            [None, None, None, None, None, "-13", "-5", "-1", "7", "-3"],
                            "pct_0",
                        ),
                        mixed_row(
                            "vs19-fx",
                            "2021 vs 2019 YoY% FX-Adjusted Revenues Net of Interest",
                            ANNEX_10,
                            [None, None, None, None, None, "-13", "-6", "-1", "7", "-3"],
                            "pct_0",
                        ),
                    ],
                )
            },
            section="appendix",
            extra={
                "content": {"subtitle": "$ in billions"},
                "disclosure": disc(
                    "s44-disc",
                    "Notes",
                    ["* See Slide 2 for an explanation of FX-adjusted information. 2021 vs. 2019 YoY% assumes 2021 foreign exchange rates apply to 2019 results."],
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
