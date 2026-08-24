#!/usr/bin/env python3
"""Build the D314 canonical Amex schema-v1 handoff from fixtures + D314 worksheet.

Writes tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json
(#226/#269: s4/s19 leap-year annotations + independent navy-header support; s5/s9/s10 independent support;
#227: s6 +6pp elbow annotation; s8 lodging metric_strip; s15 reserve-rate outlined row + stack totals;
#228/#268: s12 three-band NCA stacked_bar UCS/Commercial/ICS totaling ~3.x + PDF hero KPI sentences;
#225: s11 Transaction Growth pins domain.kind=fixed 0–15;
#229: s17 usd_1 + CAGR measurements + Qualification disclosure; s18 usd_1 + boxed YoY labels + PDF driver-card rows;
#271: s18 folds Volume/Margin detail into one driver label (` - `) and drops those detail fields;
#258: s17 dated pane headings + slide subtitle + pane_title identity;
#230/#254: s21 stacked combo shares line 702→682 + exact ROE row; s24 above groups + $486B + outlined %-of-total; s28 FDIC callout + stack totals;
#248: sky_blue cycle + authored s8/s15/s28 colors; s6 Refresh; s8 10x; s15 Q2–Q4 2.9%;
#259: s6 left pane subtitle + right-pane Anniversary Month / retention axis titles;
#260: s12/s15/s21 display.stack_segments show;
#272: s15 reserve navy (write-offs stay primary_blue);
#255: s4/s19 series swap + s19 fixed 0–15; PDF ticks; s8 FHR step; s5/s9/s10/s11 Leap Year + s5/s9/s10 G&S/T&E facts; s38 preamble).
Does not rewrite artifacts/renderer_3_release/3.0.0/.
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "renderer_v2"
OUT = ROOT / "tests" / "fixtures" / "renderer_v3" / "canonical_amex_handoff_v1.json"

def _clean(s: str) -> str:
    """Normalize common mojibake / fancy punctuation from archived fixtures."""
    if not isinstance(s, str):
        return s
    reps = {
        "â€”": "—",
        "â€“": "—",
        "â€™": "'",
        "â€œ": '"',
        "â€": '"',
        "â€¢": "•",
        "Â·": "·",
        "â€”": "—",
        "â€”": "—",
        "â€“": "–",
        "â€™": "'",
        "â€œ": '"',
        "â€": '"',
        "Â·": "·",
        " ": " ",
    }
    for a,b in reps.items():
        s=s.replace(a,b)
    # latin-1 mojibake roundtrip for common cases
    try:
        s2=s.encode('latin-1').decode('utf-8')
        if 'â' not in s2:
            s=s2
    except Exception:
        pass
    return s


def _clean_obj(o):
    if isinstance(o, str):
        return _clean(o)
    if isinstance(o, list):
        return [_clean_obj(x) for x in o]
    if isinstance(o, dict):
        return {k: _clean_obj(v) for k,v in o.items()}
    return o


# D314 evidence: amex-q1-2026-p01..p44
SOURCE_NAME = "American Express Q1 2026 Earnings Presentation"
# Opaque PDF hash pinned by release evidence (#198 / D315).
PDF_HASH = "a87c11625c84e0dabb02d523f6a2d2508b892f18ee242ef197a9b40157bd3faf"


def ev_id(n: int) -> str:
    return f"amex-q1-2026-p{n:02d}"


def evidence_registry() -> dict:
    reg = {}
    for n in range(1, 45):
        # Opaque locator object (D175); renderer never opens sources.
        reg[ev_id(n)] = {
            "source_name": SOURCE_NAME,
            "locator": {
                "kind": "pdf_page",
                "sha256": PDF_HASH,
                "page": n,
                "index": n - 1,
            },
        }
    return reg


def nfmt() -> dict:
    """Minimal D293 formats used by the deck."""
    return {
        "usd_0": {"unit": "usd", "value_decimals": 0, "negative_style": "parentheses"},
        "usd_1": {"unit": "usd", "value_decimals": 1, "negative_style": "parentheses"},
        "usd_2": {"unit": "usd", "value_decimals": 2, "negative_style": "parentheses"},
        "pct_0": {"unit": "percent", "value_decimals": 0, "negative_style": "parentheses"},
        "pct_1": {"unit": "percent", "value_decimals": 1, "negative_style": "minus"},
        "pp_0": {
            "unit": "percentage_points",
            "value_decimals": 0,
            "negative_style": "minus",
        },
        "pp_1": {
            "unit": "percentage_points",
            "value_decimals": 1,
            "negative_style": "minus",
        },
        # Unitless: omit unit key (null rejected).
        "num_0": {"value_decimals": 0, "negative_style": "minus"},
        "num_1": {"value_decimals": 1, "negative_style": "minus"},
        "num_2": {"value_decimals": 2, "negative_style": "minus"},
    }


def _parse_cell(raw: str | None, *, default_fmt: str = "num_0") -> dict:
    if raw is None:
        return {"type": "missing"}
    s = str(raw).strip()
    if s in {"", "—", "–", "-", "–", "â€”", "\u2014", "n/a", "N/A", "â€“"}:
        return {"type": "missing"}
    # strip currency/commas/approx
    t = s.replace(",", "").replace("$", "").replace("~", "").replace("%", "")
    t = t.replace("(", "-").replace(")", "")
    t = t.replace("\u2212", "-")
    if t in {"", "â€”", "—"}:
        return {"type": "missing"}
    # ranges like 9-10 or 10–11
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)[–\-](-?\d+(?:\.\d+)?)", t)
    if m:
        lo, hi = m.group(1), m.group(2)
        fmt = "pct_0" if "%" in s else default_fmt
        if "$" in s:
            fmt = "usd_2" if "." in lo or "." in hi else "usd_0"
        return {"type": "range", "lower": lo, "upper": hi, "format_id": fmt}
    try:
        float(t)
    except ValueError:
        return {"type": "text", "text": s}
    fmt = default_fmt
    if "%" in s:
        fmt = "pct_1" if "." in t else "pct_0"
    elif "$" in s:
        fmt = "usd_2" if "." in t else "usd_0"
    elif "(" in s and ")" in s:
        fmt = "pct_0" if "%" in s else default_fmt
    # normalize -0
    if t.startswith("-"):
        val = t
    else:
        val = t
    # drop leading zeros issues: keep as canonical
    if "." in val:
        val = val.rstrip("0").rstrip(".") if False else val  # keep authored decimals
    return {"type": "number", "value": val, "format_id": fmt}


def _slug(text: str, used: set[str], fallback: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48] or fallback
    if not base[0].isalpha():
        base = f"x-{base}"
    cand = base
    i = 2
    while cand in used:
        cand = f"{base}-{i}"
        i += 1
    used.add(cand)
    return cand


def matrix_table(
    surface_id: str,
    header_row: list,
    data_rows: list[list],
    *,
    stub_header: str = "Metric",
    col_fmt_hint: dict[int, str] | None = None,
) -> dict:
    used: set[str] = set()
    cols = []
    for i, h in enumerate(header_row[1:]):
        cid = _slug(str(h), used, f"c{i}")
        cols.append({"column_id": cid, "label": str(h)})
    rows = []
    rused: set[str] = set()
    for ri, row in enumerate(data_rows):
        label = str(row[0])
        rid = _slug(label, rused, f"r{ri}")
        cells = {}
        for ci, col in enumerate(cols):
            raw = row[ci + 1] if ci + 1 < len(row) else None
            hint = (col_fmt_hint or {}).get(ci, "num_1")
            cells[col["column_id"]] = _parse_cell(raw, default_fmt=hint)
        rows.append({"row_id": rid, "label": label, "cells": cells})
    return {
        "surface_id": surface_id,
        "stub_header": {"label": stub_header},
        "columns": cols,
        "rows": rows,
    }


TICKS_0_15 = ["0", "5", "10", "15"]
TICKS_0_25 = ["0", "5", "10", "15", "20", "25"]
S38_PREAMBLE = (
    "This presentation includes forward-looking statements within the meaning of "
    "the Private Securities Litigation Reform Act of 1995, which are subject to "
    "risks and uncertainties. The forward-looking statements, which address "
    "American Express Company's current expectations regarding business and "
    "financial performance, including management's guidance for 2026, among "
    "other matters, contain words such as \"believe,\" \"expect,\" \"anticipate,\" "
    "\"intend,\" \"plan,\" \"aim,\" \"will,\" \"may,\" \"should,\" \"could,\" \"would,\" "
    "\"likely,\" \"continue\" and similar expressions. Readers are cautioned not "
    "to place undue reliance on these forward-looking statements, which speak "
    "only as of the date on which they are made. The company undertakes no "
    "obligation to update or revise any forward-looking statements. Factors "
    "that could cause actual results to differ materially from these "
    "forward-looking statements, include, but are not limited to, the following:"
)


def leap_year_ann() -> list[dict]:
    return [
        {
            "annotation_id": "leap-year",
            "role": "explanation",
            "text": "Leap Year Approx. (1%)",
            "anchor": {"type": "chart"},
        }
    ]


def spend_elbow_ann() -> list[dict]:
    return [
        {
            "annotation_id": "spend-elbow",
            "role": "explanation",
            "text": "+ ~6 percentage points",
            "anchor": {
                "type": "category_range",
                "from_category_id": "q1-25",
                "to_category_id": "q1-26",
            },
        }
    ]


def refresh_chip_ann() -> dict:
    return {
        "annotation_id": "s6-refresh",
        "role": "event",
        "text": "Refresh",
        "anchor": {"type": "category", "category_id": "q3-25"},
    }


def yoy_context(gs: str, te: str) -> list[dict]:
    return [
        {
            "context_id": "gs-yoy",
            "label": "G&S",
            "value": {"type": "text", "text": gs},
        },
        {
            "context_id": "te-yoy",
            "label": "T&E",
            "value": {"type": "text", "text": te},
        },
    ]


def tenx_callout_ann() -> dict:
    return {
        "annotation_id": "s8-10x",
        "role": "explanation",
        "text": "10x",
        "anchor": {"type": "chart"},
    }


def _s18_nii(labs: list, vals: list) -> dict:
    chart = grouped_bar(
        "s18-nii",
        labs,
        [("NII", vals, "navy")],
        heading="Net Interest Income",
        fmt="usd_1",
    )
    chart["auxiliary_series"] = [
        {
            "auxiliary_id": "s18-yoy",
            "role": "boxed_label",
            "label": "YoY Growth",
            "format_id": "pct_0",
            "target_series_id": chart["chart_data"]["series"][0]["series_id"],
            "values": ["11", "12", "12", "12", "12"],
        }
    ]
    return chart


def _s21_combo(labs: list, bar_series: list, shares: list, totals: list) -> dict:
    used: set[str] = set()
    cats = [
        {"category_id": _slug(str(c), used, f"cat{i}"), "label": str(c)}
        for i, c in enumerate(labs)
    ]
    sused: set[str] = set()
    colors = ["navy", "primary_blue"]
    series = []
    for si, (name, values) in enumerate(bar_series):
        series.append(
            {
                "series_id": _slug(name, sused, f"s{si}"),
                "name": name,
                "mark_type": "bar",
                "values": [None if v is None else str(v) for v in values],
                "color": colors[si % len(colors)],
            }
        )
    series.append(
        {
            "series_id": _slug("Common Shares Outstanding", sused, "shares"),
            "name": "Common Shares Outstanding",
            "mark_type": "line",
            "axis_key": "secondary",
            "values": [str(v) for v in shares],
            "color": "neutral",
        }
    )
    return {
        "type": "chart",
        "surface_id": "s21-cap",
        "chart_type": "combo",
        "bar_mode": "stacked",
        "heading": "Capital Return & Common Shares Outstanding",
        "chart_data": {"categories": cats, "series": series},
        "category_axis": {"visible": True},
        "value_axes": {
            "primary": {
                "visible": True,
                "format_id": "usd_1",
                "domain": {"kind": "generated", "target_ticks": 5},
            },
            "secondary": {
                "visible": True,
                "format_id": "num_0",
                "domain": {
                    "kind": "fixed",
                    "min": "670",
                    "max": "710",
                    "ticks": ["670", "680", "690", "700", "710"],
                },
            },
        },
        "display": {"series_identity": "legend", "stack_segments": "show"},
        "auxiliary_series": [
            {
                "auxiliary_id": "s21-cap-totals",
                "role": "authored_stack_total",
                "label": "Total",
                "format_id": "usd_1",
                "values": [None if v is None else str(v) for v in totals],
            }
        ],
    }


def _s18_driver() -> dict:
    rows = [
        ("billed", "Billed Business", "8", None),
        ("nii", "Net Interest Income", "13", None),
        ("volume", "Volume - Total Balances", "7", None),
        (
            "margin",
            "Margin - Net Interest Income / Average Total Balances",
            "5",
            None,
        ),
    ]
    out_rows = []
    for rid, label, value, detail in rows:
        row = {
            "row_id": rid,
            "label": label,
            "value": {"type": "number", "value": value, "format_id": "pct_0"},
            "direction": "up",
            "tone": "positive",
        }
        if detail:
            row["detail"] = detail
        out_rows.append(row)
    return {
        "hero_type": "driver_card",
        "surface_id": "s18-driver",
        "heading": "NII: Volume & Margin Drivers",
        "subtitle": "CAGR % vs. Q1'19 (FX-adjusted except Margin)",
        "rows": out_rows,
    }


def support_from_v2(
    surface_id: str,
    steps: list[list],
    *,
    alignment: str,
    fmt: str = "pct_0",
) -> dict:
    header, *rows = steps
    n_cols = max(0, len(header) - 1)
    stub = str(header[0]).strip() or "Metric"
    table = matrix_table(
        surface_id,
        header,
        rows,
        stub_header=stub,
        col_fmt_hint={i: fmt for i in range(n_cols)},
    )
    for row in table["rows"]:
        for cell in row["cells"].values():
            if cell.get("type") == "number":
                cell["format_id"] = fmt
    return {
        "support_type": "support_table",
        "alignment": alignment,
        "table": table,
    }


def outlined_from_v2(surface_id: str, steps: list[list], *, fmt: str = "pct_1") -> dict:
    table = support_from_v2(surface_id, steps, alignment="category", fmt=fmt)["table"]
    if table["rows"]:
        # Painter uses stub_header, not the row label (D166).
        table["stub_header"] = {"label": table["rows"][0]["label"]}
    return {"support_type": "outlined_support", "table": table}


def period_table(surface_id: str, steps: list[list], *, labels: tuple[str, str, str]) -> dict:
    """steps: [header, ...rows] with 4 cols Metric + 3 periods."""
    # remap columns to fixed role ids
    data_rows = steps[1:]
    rows = []
    rused: set[str] = set()
    for ri, row in enumerate(data_rows):
        label = str(row[0])
        rid = _slug(label, rused, f"r{ri}")
        cells = {
            "current_period": _parse_cell(row[1] if len(row) > 1 else None, default_fmt="usd_0"),
            "comparison_period": _parse_cell(row[2] if len(row) > 2 else None, default_fmt="usd_0"),
            "variance": _parse_cell(row[3] if len(row) > 3 else None, default_fmt="pct_0"),
        }
        # EPS needs 2 decimals
        if "EPS" in label:
            for k in ("current_period", "comparison_period"):
                if cells[k].get("type") == "number":
                    cells[k]["format_id"] = "usd_2"
        if "Shares" in label:
            for k in ("current_period", "comparison_period"):
                if cells[k].get("type") == "number":
                    cells[k]["format_id"] = "num_0"
        rows.append({"row_id": rid, "label": label, "cells": cells})
    return {
        "surface_id": surface_id,
        "stub_header": {"label": "Metric"},
        "columns": [
            {"column_id": "current_period", "label": labels[0]},
            {"column_id": "comparison_period", "label": labels[1]},
            {"column_id": "variance", "label": labels[2]},
        ],
        "rows": rows,
    }


def line_chart(
    surface_id: str,
    categories: list[str],
    series: list[tuple[str, list, str | None]],
    *,
    heading: str | None = None,
    fmt: str = "pct_0",
    domain: tuple[str, str] | None = None,
    styles: list[str] | None = None,
    ticks: list[str] | None = None,
) -> dict:
    used: set[str] = set()
    cats = []
    for i, c in enumerate(categories):
        cid = _slug(str(c), used, f"cat{i}")
        cats.append({"category_id": cid, "label": str(c)})
    ser = []
    sused: set[str] = set()
    colors = ["navy", "primary_blue", "sky_blue", "neutral"]
    for si, (name, values, color) in enumerate(series):
        sid = _slug(name, sused, f"s{si}")
        style = None
        if styles and si < len(styles):
            style = {"line_style": styles[si], "marker": "circle"}
        ser.append(
            {
                "series_id": sid,
                "name": name,
                "values": [None if v is None else str(v) for v in values],
                "color": color or colors[si % len(colors)],
                **({"style": style} if style else {}),
            }
        )
    if domain:
        if ticks is None:
            lo, hi = float(domain[0]), float(domain[1])
            # 5 inclusive ticks spanning fixed domain
            step = (hi - lo) / 4
            ticks = [
                str(
                    int(lo + step * i)
                    if step == int(step) and lo == int(lo)
                    else round(lo + step * i, 4)
                )
                for i in range(5)
            ]
            ticks = [
                str(int(float(t))) if float(t) == int(float(t)) else t for t in ticks
            ]
        else:
            ticks = [str(t) for t in ticks]
        dom = {"kind": "fixed", "min": domain[0], "max": domain[1], "ticks": ticks}
    else:
        dom = {"kind": "generated", "target_ticks": 5}
    visual = {
        "type": "chart",
        "surface_id": surface_id,
        "chart_type": "line",
        "chart_data": {"categories": cats, "series": ser},
        "category_axis": {"visible": True},
        "value_axes": {
            "primary": {
                "visible": True,
                "format_id": fmt,
                "domain": dom,
            }
        },
        "display": {"ordinary_values": "show", "series_identity": "auto"},
    }
    if heading:
        visual["heading"] = heading
    return visual


def grouped_bar(
    surface_id: str,
    categories: list[str],
    series: list[tuple[str, list, str | None]],
    *,
    heading: str | None = None,
    fmt: str = "pct_0",
    domain: tuple[str, str] | None = None,
    groups: list[dict] | None = None,
) -> dict:
    used: set[str] = set()
    cats = []
    for i, c in enumerate(categories):
        cid = _slug(str(c), used, f"cat{i}")
        cats.append({"category_id": cid, "label": str(c)})
    ser = []
    sused: set[str] = set()
    colors = ["navy", "primary_blue", "sky_blue", "neutral"]
    for si, (name, values, color) in enumerate(series):
        sid = _slug(name, sused, f"s{si}")
        ser.append(
            {
                "series_id": sid,
                "name": name,
                "values": [None if v is None else str(v) for v in values],
                "color": color or colors[si % len(colors)],
            }
        )
    if domain:
        lo, hi = float(domain[0]), float(domain[1])
        step = (hi - lo) / 4
        ticks = []
        for i in range(5):
            v = lo + step * i
            ticks.append(str(int(v)) if v == int(v) else str(round(v, 4)))
        dom = {"kind": "fixed", "min": domain[0], "max": domain[1], "ticks": ticks}
    else:
        dom = {"kind": "generated", "target_ticks": 5}
    visual = {
        "type": "chart",
        "surface_id": surface_id,
        "chart_type": "grouped_bar",
        "chart_data": {"categories": cats, "series": ser},
        "category_axis": {"visible": True},
        "value_axes": {
            "primary": {"visible": True, "format_id": fmt, "domain": dom}
        },
        "display": {"ordinary_values": "show", "series_identity": "auto"},
    }
    if heading:
        visual["heading"] = heading
    if groups:
        visual["category_groups"] = groups
    return visual


def hbar(
    surface_id: str,
    categories: list[str],
    series: list[tuple[str, list, str | None]],
    *,
    heading: str | None = None,
    fmt: str = "pct_0",
    leading_break: str | None = None,
    domain: tuple[str, str] | None = None,
) -> dict:
    used: set[str] = set()
    cats = []
    for i, c in enumerate(categories):
        cid = _slug(str(c), used, f"cat{i}")
        cats.append({"category_id": cid, "label": str(c)})
    ser = []
    sused: set[str] = set()
    colors = ["primary_blue", "navy"]
    for si, (name, values, color) in enumerate(series):
        sid = _slug(name, sused, f"s{si}")
        ser.append(
            {
                "series_id": sid,
                "name": name,
                "values": [None if v is None else str(v) for v in values],
                "color": color or colors[si % len(colors)],
            }
        )
    if domain:
        lo, hi = float(domain[0]), float(domain[1])
        step = (hi - lo) / 4
        ticks = []
        for i in range(5):
            v = lo + step * i
            ticks.append(str(int(v)) if v == int(v) else str(round(v, 4)))
        dom = {"kind": "fixed", "min": domain[0], "max": domain[1], "ticks": ticks}
    else:
        dom = {"kind": "generated", "target_ticks": 5}
    primary = {
        "visible": True,
        "format_id": fmt,
        "domain": dom,
    }
    if leading_break is not None:
        primary["leading_break"] = {"to": leading_break}
    visual = {
        "type": "chart",
        "surface_id": surface_id,
        "chart_type": "horizontal_bar",
        "chart_data": {"categories": cats, "series": ser},
        "category_axis": {"visible": True},
        "value_axes": {"primary": primary},
        "display": {"ordinary_values": "show", "series_identity": "auto"},
    }
    if heading:
        visual["heading"] = heading
    return visual


def stacked_bar(
    surface_id: str,
    categories: list[str],
    series: list[tuple[str, list, str | None]],
    *,
    heading: str | None = None,
    fmt: str = "usd_1",
    totals: list | None = None,
) -> dict:
    used: set[str] = set()
    cats = []
    for i, c in enumerate(categories):
        cid = _slug(str(c), used, f"cat{i}")
        cats.append({"category_id": cid, "label": str(c)})
    ser = []
    sused: set[str] = set()
    colors = ["navy", "primary_blue", "sky_blue", "neutral", "warning", "primary_blue"]
    for si, (name, values, color) in enumerate(series):
        sid = _slug(name, sused, f"s{si}")
        ser.append(
            {
                "series_id": sid,
                "name": name,
                "values": [None if v is None else str(v) for v in values],
                "color": color or colors[si % len(colors)],
            }
        )
    visual = {
        "type": "chart",
        "surface_id": surface_id,
        "chart_type": "stacked_bar",
        "chart_data": {"categories": cats, "series": ser},
        "category_axis": {"visible": True},
        "value_axes": {
            "primary": {
                "visible": True,
                "format_id": fmt,
                "domain": {"kind": "generated", "target_ticks": 5},
            }
        },
        "display": {"series_identity": "legend"},
    }
    if heading:
        visual["heading"] = heading
    if totals is not None:
        visual["auxiliary_series"] = [
            {
                "auxiliary_id": f"{surface_id}-totals",
                "role": "authored_stack_total",
                "label": "Total",
                "format_id": fmt,
                "values": [None if v is None else str(v) for v in totals],
            }
        ]
    return visual


def bullets_to_narrative(items: list[str], block_id: str = "highlights") -> dict:
    """Convert markdown-ish bullets to D224 prose runs."""
    prose_items = []
    for b in items:
        runs = []
        # split **strong**
        parts = re.split(r"(\*\*[^*]+\*\*)", b)
        for p in parts:
            if not p:
                continue
            if p.startswith("**") and p.endswith("**"):
                runs.append({"text": p[2:-2], "emphasis": "strong"})
            else:
                runs.append({"text": p})
        # merge adjacent ordinary
        merged = []
        for r in runs:
            if (
                merged
                and "emphasis" not in r
                and "emphasis" not in merged[-1]
            ):
                merged[-1]["text"] += r["text"]
            else:
                merged.append(r)
        # drop empty
        merged = [r for r in merged if r.get("text")]
        if not merged:
            continue
        prose_items.append({"runs": merged})
    return {
        "blocks": [
            {
                "block_id": block_id,
                "type": "bullet_list",
                "items": prose_items,
            }
        ]
    }


def disclosure_from_text(surface_id: str, title: str, body: str) -> dict:
    return {
        "sections": [
            {
                "surface_id": surface_id,
                "title": title,
                "items": [{"kind": "paragraph", "text": body}],
            }
        ]
    }


def ordinary(
    n: int,
    layout: str,
    title: str,
    section_id: str,
    payload: dict,
    *,
    subtitle: str | None = None,
    disclosure: dict | None = None,
) -> dict:
    s: dict = {
        "slide_number": n,
        "layout_type": layout,
        "section_id": section_id,
        "title": title,
        "payload": payload,
        "evidence_ids": [ev_id(n)],
    }
    if subtitle:
        s["content"] = {"subtitle": subtitle}
    if disclosure:
        s["disclosure"] = disclosure
    return s


def load_v10() -> dict:
    return json.loads((FIX / "amex_v10_44_slide_handoff.json").read_text(encoding="utf-8"))


def build() -> dict:
    v10 = load_v10()
    slides_in = {s["slide_number"]: s for s in v10["slides"]}

    sections = [
        {"section_id": "earnings", "label": "Earnings"},
        {"section_id": "appendix", "label": "Appendix"},
        {"section_id": "legal", "label": "Legal"},
    ]

    slides: list[dict] = []

    # 1 opening_cover
    slides.append(
        {
            "slide_number": 1,
            "layout_type": "opening_cover",
            "payload": {
                "title": "American Express Earnings Conference Call",
                "period_label": "Q1'26",
                "date_label": "April 23, 2026",
            },
            "evidence_ids": [ev_id(1)],
        }
    )

    # 2 narrative highlights
    b2 = slides_in[2]["content"]["bullets"]
    slides.append(
        ordinary(
            2,
            "narrative",
            "Business Highlights",
            "earnings",
            bullets_to_narrative(b2, "biz-highlights"),
            disclosure=disclosure_from_text(
                "s2-disc",
                "Statistical Tables",
                "See Statistical Tables for additional information.",
            ),
        )
    )

    # 3 period_comparison
    steps3 = slides_in[3]["visual_spec"]["primary_visual"]["steps_or_data"]
    slides.append(
        ordinary(
            3,
            "period_comparison",
            "Summary Financial Performance",
            "earnings",
            {
                "table": period_table(
                    "s3-fin",
                    steps3,
                    labels=("Q1'26", "Q1'25", "YoY"),
                )
            },
            subtitle=slides_in[3]["content"].get("subtitle") or None,
            disclosure=disclosure_from_text(
                "s3-disc",
                "Non-GAAP / footnotes",
                slides_in[3]["disclosure"]["panels"][0]["body"],
            ),
        )
    )

    # 4 line reported/FX + leap-year + G&S/T&E support
    cats = ["Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"]
    chart4 = line_chart(
        "s4-bb",
        cats,
        [
            ("Reported", [6, 7, 9, 9, 10], "neutral"),
            ("FX-adjusted", [6, 7, 8, 8, 9], "navy"),
        ],
        fmt="pct_0",
        domain=("0", "15"),
        styles=["dashed", "solid"],
        ticks=TICKS_0_15,
    )
    chart4["annotations"] = leap_year_ann()
    slides.append(
        ordinary(
            4,
            "single_chart",
            "Total Billed Business",
            "earnings",
            {
                "chart": chart4,
                "support": support_from_v2(
                    "s4-support",
                    slides_in[4]["visual_spec"]["secondary_visual"]["steps_or_data"],
                    alignment="independent",
                ),
            },
            subtitle=slides_in[4]["content"].get("subtitle"),
        )
    )

    # 5 UCS line + independent generation mix table + Leap Year / G&S T&E facts
    chart5 = line_chart(
        "s5-ucs",
        cats,
        [("UCS Billings", [7, 7, 9, 9, 10], "navy")],
        fmt="pct_0",
        domain=("0", "15"),
        ticks=TICKS_0_15,
    )
    chart5["annotations"] = leap_year_ann()
    chart5["context_labels"] = yoy_context("9% YoY", "11% YoY")
    slides.append(
        ordinary(
            5,
            "single_chart",
            "U.S. Consumer Services Billed Business",
            "earnings",
            {
                "chart": chart5,
                "support": support_from_v2(
                    "s5-support",
                    slides_in[5]["visual_spec"]["secondary_visual"]["steps_or_data"],
                    alignment="independent",
                ),
            },
            subtitle=slides_in[5]["content"].get("subtitle"),
        )
    )

    # 6 dual_chart spend + retention + PDF +6pp elbow on the left chart
    spend6 = grouped_bar(
        "s6-spend",
        cats,
        [("Spend growth", [7, 7, 9, 9, 10], "navy")],
        heading="Spend Growth is Accelerating",
        fmt="pct_0",
        domain=("0", "12"),
    )
    spend6["annotations"] = spend_elbow_ann() + [refresh_chip_ann()]
    spend6["subtitle"] = "% Increase/(decrease) vs. Prior year"
    ret6 = hbar(
        "s6-ret",
        ["January", "February", "March"],
        [
            ("2025", [94, 95, 95], "primary_blue"),
            ("2026", [96, 97, 97], "navy"),
        ],
        heading="Retention Rates Remain High and Very Stable",
        fmt="pct_0",
        leading_break="90",
        domain=("90", "100"),
    )
    ret6["category_axis"]["title"] = "Anniversary Month"
    ret6["value_axes"]["primary"]["title"] = (
        "Account Retention Rate for Card Members in Renewal Anniversary Month"
    )
    slides.append(
        ordinary(
            6,
            "dual_chart",
            "U.S. Consumer Platinum Performance",
            "earnings",
            {
                "charts": [
                    spend6,
                    ret6,
                ]
            },
            disclosure=disclosure_from_text(
                "s6-disc",
                "Source claims",
                "Refresh event at Q3'25. Authored approximate measurement: + ~6 percentage points (source claim; not recomputed from displayed endpoints).",
            ),
        )
    )

    # 7 comparison_cards
    slides.append(
        ordinary(
            7,
            "comparison_cards",
            "U.S. Consumer: Membership Model Engagement",
            "earnings",
            {
                "table": {
                    "surface_id": "s7-cards",
                    "stub_header": {"label": "Peer"},
                    "columns": [
                        {"column_id": "premium", "label": "Premium growth"},
                        {"column_id": "ucs", "label": "UCS benchmark"},
                        {"column_id": "mult", "label": "Multiplier"},
                    ],
                    "rows": [
                        {
                            "row_id": "lodging",
                            "label": "Lodging",
                            "cells": {
                                "premium": {
                                    "type": "number",
                                    "value": "50",
                                    "format_id": "pct_0",
                                },
                                "ucs": {
                                    "type": "number",
                                    "value": "5",
                                    "format_id": "pct_0",
                                },
                                "mult": {"type": "text", "text": "10x"},
                            },
                        },
                        {
                            "row_id": "restaurants",
                            "label": "Restaurants",
                            "cells": {
                                "premium": {
                                    "type": "number",
                                    "value": "20",
                                    "format_id": "pct_0",
                                },
                                "ucs": {
                                    "type": "number",
                                    "value": "10",
                                    "format_id": "pct_0",
                                },
                                "mult": {"type": "text", "text": "2x"},
                            },
                        },
                        {
                            "row_id": "airlines",
                            "label": "Airlines",
                            "cells": {
                                "premium": {
                                    "type": "number",
                                    "value": "21",
                                    "format_id": "pct_0",
                                },
                                "ucs": {
                                    "type": "number",
                                    "value": "11",
                                    "format_id": "pct_0",
                                },
                                "mult": {"type": "text", "text": "2x"},
                            },
                        },
                    ],
                }
            },
            subtitle=slides_in[7]["content"].get("subtitle"),
            disclosure=disclosure_from_text(
                "s7-disc",
                "Member Airfares footnote",
                slides_in[7]["disclosure"]["panels"][0]["body"],
            ),
        )
    )

    # 8 lodging line + right-side KPI stack (PDF 3,400+ / 300+ / $600 / $550)
    lodging8 = line_chart(
        "s8-lodging",
        cats,
        [
            ("FHR+THC", [40, 40, 40, 50, 50], "primary_blue"),
            ("UCS Lodging", [5, 5, 5, 5, 5], "sky_blue"),
        ],
        fmt="pct_0",
        domain=("0", "60"),
    )
    lodging8["annotations"] = [tenx_callout_ann()]
    slides.append(
        ordinary(
            8,
            "single_chart",
            "Membership Model Engagement: Proprietary Lodging Assets",
            "earnings",
            {
                "chart": lodging8,
                "support": {
                    "support_type": "metric_strip",
                    "surface_id": "s8-kpis",
                    "metrics": [
                        {
                            "metric_id": "properties",
                            "label": "Premium Global Properties",
                            "value": {"type": "text", "text": "3,400+"},
                        },
                        {
                            "metric_id": "new-properties",
                            "label": "New Properties Selected (2026)",
                            "value": {"type": "text", "text": "300+"},
                        },
                        {
                            "metric_id": "statement-credit",
                            "label": "Annual U.S. Plat Statement Credit",
                            "value": {
                                "type": "number",
                                "value": "600",
                                "format_id": "usd_0",
                            },
                        },
                        {
                            "metric_id": "stay-value",
                            "label": "Avg CM Value 2-Night Stay",
                            "value": {
                                "type": "number",
                                "value": "550",
                                "format_id": "usd_0",
                            },
                        },
                    ],
                },
            },
            subtitle=slides_in[8]["content"].get("subtitle"),
            disclosure=disclosure_from_text(
                "s8-disc",
                "Program metrics",
                "Partner-Funded 100%. Context fact: 10x.",
            ),
        )
    )

    # 9 commercial + independent segment table + Leap Year / G&S T&E facts
    chart9 = line_chart(
        "s9-comm",
        cats,
        [("Commercial FX-adj", [2, 2, 4, 3, 4], "navy")],
        fmt="pct_0",
        domain=("0", "15"),
        ticks=TICKS_0_15,
    )
    chart9["annotations"] = leap_year_ann()
    chart9["context_labels"] = yoy_context("3% YoY", "6% YoY")
    slides.append(
        ordinary(
            9,
            "single_chart",
            "Commercial Services Billed Business",
            "earnings",
            {
                "chart": chart9,
                "support": support_from_v2(
                    "s9-support",
                    slides_in[9]["visual_spec"]["secondary_visual"]["steps_or_data"],
                    alignment="independent",
                ),
            },
            subtitle=slides_in[9]["content"].get("subtitle"),
        )
    )

    # 10 ICS + independent segment table (no duplicate Reported annotation)
    chart10 = line_chart(
        "s10-ics",
        cats,
        [
            ("FX-adjusted", [13, 12, 13, 12, 13], "navy"),
            ("Reported", [9, 15, 14, 17, 20], "neutral"),
        ],
        fmt="pct_0",
        domain=("0", "25"),
        styles=["solid", "dashed"],
        ticks=TICKS_0_25,
    )
    chart10["annotations"] = leap_year_ann()
    chart10["context_labels"] = yoy_context("14% YoY", "10% YoY")
    slides.append(
        ordinary(
            10,
            "single_chart",
            "International Card Services Billed Business",
            "earnings",
            {
                "chart": chart10,
                "support": support_from_v2(
                    "s10-support",
                    slides_in[10]["visual_spec"]["secondary_visual"]["steps_or_data"],
                    alignment="independent",
                ),
            },
            subtitle=slides_in[10]["content"].get("subtitle"),
        )
    )

    # 11 transaction growth
    s11 = slides_in[11]
    steps11 = s11["visual_spec"]["primary_visual"]["steps_or_data"]
    vals11 = [r.get("value") for r in steps11]
    labs11 = [r["label"] for r in steps11]
    chart11 = line_chart(
        "s11-txn",
        labs11,
        [("Transaction Growth", vals11, "navy")],
        fmt="pct_0",
        domain=("0", "15"),
        ticks=TICKS_0_15,
    )
    chart11["annotations"] = leap_year_ann()
    slides.append(
        ordinary(
            11,
            "single_chart",
            s11["title"],
            "earnings",
            {
                "chart": chart11
            },
            subtitle=s11["content"].get("subtitle") or None,
            disclosure=disclosure_from_text(
                "s11-disc",
                "Notes",
                "Leap-year chart explanation applies to transaction growth.",
            ),
        )
    )

    # 12 chart_hero_dual — PDF three-band NCA stack (UCS / Commercial / ICS)
    s12 = slides_in[12]
    pv12 = s12["visual_spec"]["primary_visual"]
    steps12 = pv12.get("steps_or_data") or []
    from decimal import Decimal, InvalidOperation

    if steps12 and isinstance(steps12[0], list):
        header12 = steps12[0]
        labs12 = [r[0] for r in steps12[1:]]
        series12 = []
        colors12 = ["navy", "primary_blue", "neutral"]
        for ci, name in enumerate(header12[1:]):
            series12.append(
                (
                    str(name),
                    [r[ci + 1] if ci + 1 < len(r) else None for r in steps12[1:]],
                    colors12[ci] if ci < len(colors12) else None,
                )
            )
        totals12 = []
        for r in steps12[1:]:
            try:
                totals12.append(str(sum(Decimal(str(v)) for v in r[1:] if v is not None)))
            except (InvalidOperation, TypeError, ValueError):
                totals12.append(None)
        chart12 = stacked_bar(
            "s12-cards",
            labs12,
            series12,
            heading="Proprietary New Cards Acquired",
            fmt="num_1",
            totals=totals12,
        )
    else:
        chart12 = stacked_bar(
            "s12-cards",
            cats,
            [
                ("U.S. Consumer Services", [1.5, 1.5, 1.5, 1.3, 1.3], "navy"),
                ("Commercial Services", [0.8, 0.7, 0.7, 0.7, 0.8], "primary_blue"),
                ("International Card Services", [1.1, 0.9, 1.0, 0.9, 1.0], "neutral"),
            ],
            heading="Proprietary New Cards Acquired",
            fmt="num_1",
            totals=["3.4", "3.1", "3.2", "2.9", "3.1"],
        )
    chart12["subtitle"] = "in millions"
    chart12["display"]["stack_segments"] = "show"
    slides.append(
        ordinary(
            12,
            "chart_hero_dual",
            s12["title"],
            "earnings",
            {
                "chart": chart12,
                "hero": {
                    "hero_type": "metric_stack",
                    "surface_id": "s12-hero",
                    "heading": "Proprietary New Accounts Acquired",
                    "subtitle": "Q1'2026",
                    "metrics": [
                        {
                            "metric_id": "share-66",
                            "label": (
                                "Global Consumer New Accounts Acquired from "
                                "Millennial / Gen-Z"
                            ),
                            "value": {
                                "type": "number",
                                "value": "66",
                                "format_id": "pct_0",
                            },
                        },
                        {
                            "metric_id": "share-73",
                            "label": (
                                "Global New Accounts Acquired on Fee-Paying "
                                "Products*"
                            ),
                            "value": {
                                "type": "number",
                                "value": "73",
                                "format_id": "pct_0",
                            },
                        },
                    ],
                },
            },
            disclosure=disclosure_from_text(
                "s12-disc",
                "Definitions",
                "Proprietary new cards/accounts definitions per source statistical tables.",
            ),
        )
    )

    # 13 grouped bars balances
    s13 = json.loads((FIX / "amex_s13_s14_corrected.json").read_text(encoding="utf-8"))[
        "slides"
    ][0]
    steps13 = s13["visual_spec"]["primary_visual"]["steps_or_data"]
    labs13 = [r["label"] for r in steps13]
    bal = [r["values"]["Total Balances"] for r in steps13]
    bb = [r["values"]["Billed Business"] for r in steps13]
    slides.append(
        ordinary(
            13,
            "single_chart",
            "Total Balances and Billed Business",
            "earnings",
            {
                "chart": grouped_bar(
                    "s13-bal",
                    labs13,
                    [
                        ("Total Balances", bal, "navy"),
                        ("Billed Business", bb, "primary_blue"),
                    ],
                    fmt="pct_0",
                    domain=("0", "15"),
                )
            },
            subtitle=s13["content"].get("subtitle"),
        )
    )

    # 14 dual credit metrics
    s14 = json.loads((FIX / "amex_s13_s14_corrected.json").read_text(encoding="utf-8"))[
        "slides"
    ][1]
    p14 = s14["visual_spec"]["primary_visual"]
    sec14 = s14["visual_spec"]["secondary_visual"]
    slides.append(
        ordinary(
            14,
            "dual_chart",
            "Credit Metrics",
            "earnings",
            {
                "charts": [
                    grouped_bar(
                        "s14-dpd",
                        [r["label"] for r in p14["steps_or_data"]],
                        [
                            (
                                "30+ Days Past Due",
                                [r["value"] for r in p14["steps_or_data"]],
                                "navy",
                            )
                        ],
                        heading="30+ Days Past Due",
                        fmt="pct_1",
                        domain=("0", "3"),
                    ),
                    grouped_bar(
                        "s14-nwo",
                        [r["label"] for r in sec14["steps_or_data"]],
                        [
                            (
                                "Net Write-Off Rates",
                                [r["value"] for r in sec14["steps_or_data"]],
                                "primary_blue",
                            )
                        ],
                        heading="Net Write-Off Rates",
                        fmt="pct_1",
                        domain=("0", "3"),
                    ),
                ]
            },
            subtitle=s14["content"].get("subtitle"),
        )
    )

    # 15 stacked provision — from v10
    s15 = slides_in[15]
    steps15 = s15["visual_spec"]["primary_visual"]["steps_or_data"]
    if steps15 and isinstance(steps15[0], list):
        header = steps15[0]
        labs15 = [r[0] for r in steps15[1:]]
        series15 = []
        s15_colors = {"Write-offs": "primary_blue", "Reserve Build/(Release)": "navy"}
        for ci, name in enumerate(header[1:]):
            series15.append(
                (
                    str(name),
                    [r[ci + 1] if ci + 1 < len(r) else None for r in steps15[1:]],
                    s15_colors.get(str(name)),
                )
            )
        from decimal import Decimal, InvalidOperation

        totals15 = []
        for r in steps15[1:]:
            try:
                totals15.append(str(Decimal(str(r[1])) + Decimal(str(r[2]))))
            except (InvalidOperation, TypeError, ValueError, IndexError):
                totals15.append(None)
        chart15 = stacked_bar(
            "s15-prov", labs15, series15, fmt="usd_0", totals=totals15
        )
    else:
        chart15 = stacked_bar(
            "s15-prov",
            cats,
            [
                ("Card Member", [1, 1, 1, 1, 1], "navy"),
                ("Other", [0.5, 0.5, 0.5, 0.5, 0.5], "primary_blue"),
            ],
            fmt="usd_0",
            totals=["1150", "1405", "1287", "1414", "1251"],
        )
    chart15["display"]["stack_segments"] = "show"
    sec15 = s15["visual_spec"].get("secondary_visual") or {}
    support15 = outlined_from_v2(
        "s15-reserve", sec15["steps_or_data"], fmt="pct_1"
    )
    # PDF Q2–Q4 reserve rate is 2.9% (#248 C-G′); Q1 / Q1'26 already match.
    row15 = support15["table"]["rows"][0]["cells"]
    for cid in ("q2-25", "q3-25", "q4-25"):
        row15[cid]["value"] = "2.9"
    slides.append(
        ordinary(
            15,
            "single_chart",
            s15["title"],
            "earnings",
            {
                "chart": chart15,
                "support": support15,
            },
            subtitle=s15["content"].get("subtitle") or None,
            disclosure=disclosure_from_text(
                "s15-disc",
                "Provision notes",
                "See Variance Commentary in the appendix section for an explanation of the provision variance versus last year.",
            ),
        )
    )

    # 16 revenue table
    s16 = slides_in[16]
    steps16 = s16["visual_spec"]["primary_visual"]["steps_or_data"]
    slides.append(
        ordinary(
            16,
            "data_table",
            s16["title"],
            "earnings",
            {"table": matrix_table("s16-rev", steps16[0], steps16[1:])},
            subtitle=s16["content"].get("subtitle"),
        )
    )

    # 17 dual net card fees
    s17 = slides_in[17]
    vs17 = s17["visual_spec"]
    p17 = vs17["primary_visual"]
    sec17 = vs17.get("secondary_visual") or {}
    # primary grouped bars Q1'19-Q1'26
    if p17.get("steps_or_data") and isinstance(p17["steps_or_data"][0], dict):
        labs17 = [r["label"] for r in p17["steps_or_data"]]
        vals17 = [r.get("value") for r in p17["steps_or_data"]]
        pane_a = grouped_bar(
            "s17-ncf",
            labs17,
            [("Net Card Fees", vals17, "navy")],
            heading="Net Card Fees (Q1: 2019-2026)",
            fmt="usd_1",
        )
    else:
        steps = p17.get("steps_or_data") or []
        if steps and isinstance(steps[0], list):
            labs17 = [r[0] for r in steps[1:]]
            vals17 = [r[1] if len(r) > 1 else None for r in steps[1:]]
            pane_a = grouped_bar(
                "s17-ncf",
                labs17,
                [("Net Card Fees", vals17, "navy")],
                heading="Net Card Fees (Q1: 2019-2026)",
                fmt="usd_1",
            )
        else:
            pane_a = grouped_bar(
                "s17-ncf",
                cats,
                [("Net Card Fees", [10, 11, 12, 13, 14], "navy")],
                heading="Net Card Fees (Q1: 2019-2026)",
                fmt="usd_1",
            )
    cats17 = [c["category_id"] for c in pane_a["chart_data"]["categories"]]
    pane_a["measurements"] = [
        {
            "measurement_id": "s17-ncf-cagr",
            "role": "cagr",
            "series_id": pane_a["chart_data"]["series"][0]["series_id"],
            "from_category_id": cats17[0],
            "to_category_id": cats17[-1],
            "value": "17",
            "format_id": "pct_0",
            "approximate": False,
        }
    ]
    if sec17.get("steps_or_data"):
        st = sec17["steps_or_data"]
        if st and isinstance(st[0], dict):
            pane_b = line_chart(
                "s17-fx",
                [r["label"] for r in st],
                [("FX-adjusted YoY", [r.get("value") for r in st], "navy")],
                heading="Net Card Fees YoY% (Q1'24-Q1'26)",
                fmt="pct_0",
            )
        else:
            pane_b = line_chart(
                "s17-fx",
                cats[-3:],
                [("FX-adjusted YoY", [12, 14, 15], "navy")],
                heading="Net Card Fees YoY% (Q1'24-Q1'26)",
                fmt="pct_0",
            )
    else:
        pane_b = line_chart(
            "s17-fx",
            ["Q1'24", "Q1'25", "Q1'26"],
            [("FX-adjusted YoY", [12, 14, 15], "navy")],
            heading="Net Card Fees YoY% (Q1'24-Q1'26)",
            fmt="pct_0",
        )
    pane_a["display"]["series_identity"] = "pane_title"
    pane_b["display"]["series_identity"] = "pane_title"
    slides.append(
        ordinary(
            17,
            "dual_chart",
            s17["title"],
            "earnings",
            {"charts": [pane_a, pane_b]},
            subtitle=(
                "$ in billions - % Increase/(decrease) vs. Prior year "
                "& CAGR (FX-adjusted)"
            ),
            disclosure=disclosure_from_text(
                "s17-disc",
                "Qualification",
                "Authored 17% CAGR measurement is a source claim retained in disclosure.",
            ),
        )
    )

    # 18 chart_hero NII + driver
    s18 = slides_in[18]
    steps18 = s18["visual_spec"]["primary_visual"]["steps_or_data"]
    if steps18 and isinstance(steps18[0], dict):
        labs18 = [r["label"] for r in steps18]
        vals18 = [r.get("value") for r in steps18]
    elif steps18 and isinstance(steps18[0], list):
        labs18 = [r[0] for r in steps18[1:]]
        vals18 = [r[1] if len(r) > 1 else None for r in steps18[1:]]
    else:
        labs18, vals18 = cats, [5, 6, 7, 8, 9]
    slides.append(
        ordinary(
            18,
            "chart_hero_dual",
            s18["title"],
            "earnings",
            {
                "chart": _s18_nii(labs18, vals18),
                "hero": _s18_driver(),
            },
        )
    )

    # 19 revenue line + leap-year + independent navy-header USD support
    s19 = slides_in[19]
    st19 = s19["visual_spec"]["primary_visual"]["steps_or_data"]
    if st19 and isinstance(st19[0], dict):
        chart19 = line_chart(
            "s19-rev",
            [r["label"] for r in st19],
            [
                ("FX-adjusted", [r.get("series_2", r.get("value")) for r in st19], "navy"),
                ("Reported", [r.get("value") for r in st19], "neutral"),
            ],
            fmt="pct_0",
            domain=("0", "15"),
            styles=["solid", "dashed"],
            ticks=TICKS_0_15,
        )
    else:
        chart19 = line_chart(
            "s19-rev",
            cats,
            [
                ("FX-adjusted", [8, 9, 11, 9, 10], "navy"),
                ("Reported", [7, 9, 11, 10, 11], "neutral"),
            ],
            fmt="pct_0",
            domain=("0", "15"),
            styles=["solid", "dashed"],
            ticks=TICKS_0_15,
        )
    chart19["annotations"] = leap_year_ann()
    slides.append(
        ordinary(
            19,
            "single_chart",
            s19["title"],
            "earnings",
            {
                "chart": chart19,
                "support": support_from_v2(
                    "s19-support",
                    s19["visual_spec"]["secondary_visual"]["steps_or_data"],
                    alignment="independent",
                    fmt="usd_1",
                ),
            },
            subtitle=s19["content"].get("subtitle") or None,
        )
    )

    # 20 expense period_comparison + VCE strip
    s20 = slides_in[20]
    steps20 = s20["visual_spec"]["primary_visual"]["steps_or_data"]
    slides.append(
        ordinary(
            20,
            "period_comparison",
            s20["title"],
            "earnings",
            {
                "table": period_table(
                    "s20-exp",
                    steps20,
                    labels=("Q1'26", "Q1'25", "Variance"),
                ),
                "metric_strip": {
                    "type": "metric_strip",
                    "surface_id": "s20-vce",
                    "metrics": [
                        {
                            "metric_id": "vce",
                            "label": "VCE",
                            "value": {
                                "type": "number",
                                "value": "44.7",
                                "format_id": "pct_1",
                            },
                        }
                    ],
                },
            },
            subtitle=s20["content"].get("subtitle"),
            disclosure=disclosure_from_text(
                "s20-disc",
                "Commentary",
                "See additional commentary slides for expense variance detail.",
            ),
        )
    )

    # 21 capital chart_hero_dual: stacked combo + shares line + exact ROE
    s21 = json.loads((FIX / "amex_s21_v10_broken.json").read_text(encoding="utf-8"))[
        "slides"
    ][0]
    tile = s21["visual_spec"]["primary_visual"]["tiles"][0]
    steps21 = tile["steps_or_data"]
    labs21 = [r[0] for r in steps21[1:]]
    series21 = [
        (str(name), [r[ci + 1] for r in steps21[1:]])
        for ci, name in enumerate(steps21[0][1:])
    ]
    from decimal import Decimal, InvalidOperation
    totals21 = []
    for r in steps21[1:]:
        try:
            totals21.append(str(Decimal(str(r[1])) + Decimal(str(r[2]))))
        except (InvalidOperation, TypeError, ValueError):
            totals21.append(None)
    shares21 = ["702", "701", "696", "689", "686", "682"]
    roe21 = ["35", "34", "36", "36", "34", "35"]
    slides.append(
        ordinary(
            21,
            "chart_hero_dual",
            "Capital",
            "earnings",
            {
                "chart": _s21_combo(labs21, series21, shares21, totals21),
                "hero": {
                    "hero_type": "driver_card",
                    "surface_id": "s21-summary",
                    "heading": "Capital Summary",
                    "rows": [
                        {
                            "row_id": "div-share",
                            "label": "Dividend/share ↑ (3yr)",
                            "value": {
                                "type": "number",
                                "value": "58",
                                "format_id": "pct_0",
                            },
                        },
                        {
                            "row_id": "ni-ret",
                            "label": "NI Returned (3yr)",
                            "value": {
                                "type": "number",
                                "value": "74",
                                "format_id": "pct_0",
                            },
                        },
                        {
                            "row_id": "cet1",
                            "label": "CET1 Ratio Q1'26",
                            "value": {
                                "type": "number",
                                "value": "10.5",
                                "format_id": "pct_1",
                            },
                        },
                        {
                            "row_id": "cet1-tgt",
                            "label": "CET1 Target",
                            "value": {
                                "type": "range",
                                "lower": "10",
                                "upper": "11",
                                "format_id": "pct_0",
                            },
                        },
                    ],
                },
                "support": outlined_from_v2(
                    "s21-roe",
                    [["", *labs21], ["ROE", *roe21]],
                    fmt="pct_0",
                ),
            },
            subtitle=s21["content"].get("subtitle"),
            disclosure=disclosure_from_text(
                "s21-disc",
                "Regulatory notes",
                "Capital Summary heading is approved neutral structural wording (D170/D314). ROE outlined support is category-aligned.",
            ),
        )
    )

    # 22 guidance metric_overview
    slides.append(
        ordinary(
            22,
            "metric_overview",
            "2026 Guidance",
            "earnings",
            {
                "surface_id": "s22-guide",
                "heading": "Full-Year 2026 Guidance",
                "metrics": [
                    {
                        "metric_id": "rev-growth",
                        "label": "Revenue growth",
                        "value": {
                            "type": "range",
                            "lower": "9",
                            "upper": "10",
                            "format_id": "pct_0",
                        },
                    },
                    {
                        "metric_id": "eps",
                        "label": "EPS",
                        "value": {
                            "type": "range",
                            "lower": "17.30",
                            "upper": "17.90",
                            "format_id": "usd_2",
                        },
                    },
                ],
                "detail": {
                    "surface_id": "s22-qual",
                    "heading": "Qualification",
                    "blocks": [
                        {
                            "block_id": "qual",
                            "type": "paragraphs",
                            "paragraphs": [
                                {
                                    "runs": [
                                        {
                                            "text": "Guidance as reported; no midpoint, status, or tone is inferred."
                                        }
                                    ]
                                }
                            ],
                        }
                    ],
                },
            },
        )
    )

    # 23 appendix divider
    slides.append(
        {
            "slide_number": 23,
            "layout_type": "section_divider",
            "payload": {"section_id": "appendix"},
            "evidence_ids": [ev_id(23)],
        }
    )

    # 24 six growth bars, above group chrome, $486B callout, outlined %-of-total
    s24 = json.loads((FIX / "amex_s24_v10_broken.json").read_text(encoding="utf-8"))[
        "slides"
    ][0]
    labs24 = [
        "U.S. Consumer Services",
        "U.S. SME",
        "U.S. Large & Global Corp.",
        "Int'l Consumer",
        "Int'l SME & Large Corp.",
        "Processed Volumes",
    ]
    shorts24 = {
        "U.S. Consumer Services": "U.S. Consumer",
        "U.S. Large & Global Corp.": "U.S. Large & Global",
        "Int'l SME & Large Corp.": "Int'l SME & Large",
    }
    vals24 = ["10", "4", "4", "13", "12", "9"]
    share24 = ["37", "22", "5", "15", "8", "12"]
    chart24 = grouped_bar(
        "s24-growth",
        labs24,
        [("YoY growth", vals24, "navy")],
        fmt="pct_0",
    )
    for cat in chart24["chart_data"]["categories"]:
        short = shorts24.get(cat["label"])
        if short:
            cat["short_label"] = short
    cat_ids24 = [c["category_id"] for c in chart24["chart_data"]["categories"]]
    chart24["category_groups"] = [
        {
            "group_id": "commercial-services",
            "label": "Commercial Services",
            "category_ids": cat_ids24[1:3],
            "placement": "above",
        },
        {
            "group_id": "international-card-services",
            "label": "International Card Services",
            "category_ids": cat_ids24[3:5],
            "placement": "above",
        },
    ]
    chart24["annotations"] = [
        {
            "annotation_id": "s24-tnv",
            "role": "explanation",
            "text": "$486B Total Network Volumes",
            "anchor": {"type": "chart"},
        }
    ]
    share_support = outlined_from_v2(
        "s24-share",
        [["", *labs24], ["% of Total Network Volumes", *share24]],
        fmt="pct_0",
    )
    share_support["table"]["stub_header"]["short_label"] = "% of Total"
    slides.append(
        ordinary(
            24,
            "single_chart",
            s24["title"],
            "appendix",
            {
                "chart": chart24,
                "support": share_support,
            },
            subtitle=s24["content"].get("subtitle") or None,
            disclosure=disclosure_from_text(
                "s24-disc",
                "FX-adjusted reporting note",
                "See Annex 1 for reported rates. Processed Volumes growth is FX-adjusted.",
            ),
        )
    )

    # 25 FX table
    s25 = slides_in[25]
    steps25 = s25["visual_spec"]["primary_visual"]["steps_or_data"]
    slides.append(
        ordinary(
            25,
            "data_table",
            s25["title"],
            "appendix",
            {"table": matrix_table("s25-fx", steps25[0], steps25[1:])},
            subtitle=s25["content"].get("subtitle"),
            disclosure=disclosure_from_text(
                "s25-disc",
                "FX notes",
                "See source for FX-adjusted methodology. Unavailable values are missing.",
            ),
        )
    )

    # 26 T&E orientation from corrected fixture
    s26 = json.loads(
        (FIX / "amex_slide26_te_billed_business.json").read_text(encoding="utf-8")
    )
    steps26 = s26["visual_spec"]["primary_visual"]["steps_or_data"]
    # header row is periods/categories: Q1'26 is stub period label in broken form;
    # corrected orientation: columns are categories, rows metrics
    header = steps26[0]
    # If first cell is Q1'26, columns are Restaurants...
    slides.append(
        ordinary(
            26,
            "data_table",
            s26["title"],
            "appendix",
            {
                "table": matrix_table(
                    "s26-te",
                    header,
                    steps26[1:],
                    stub_header="Metric",
                )
            },
            subtitle=s26["content"].get("subtitle"),
        )
    )

    # 27 dual scenarios
    s27 = json.loads((FIX / "amex_s27_corrected.json").read_text(encoding="utf-8"))[
        "slides"
    ][0]
    p27 = s27["visual_spec"]["primary_visual"]
    sec27 = s27["visual_spec"]["secondary_visual"]
    names = p27["chart_config"]["series_names"]

    def _series_from_steps(steps, names):
        labs = [r["label"] for r in steps]
        sers = []
        keys = ["value", "series_2", "series_3"]
        for i, name in enumerate(names):
            key = keys[i]
            sers.append((name, [r.get(key) for r in steps], None))
        return labs, sers

    labs_u, sers_u = _series_from_steps(p27["steps_or_data"], names)
    labs_g, sers_g = _series_from_steps(sec27["steps_or_data"], names)
    slides.append(
        ordinary(
            27,
            "dual_chart",
            s27["title"],
            "appendix",
            {
                "charts": [
                    line_chart(
                        "s27-unemp",
                        labs_u,
                        sers_u,
                        heading=p27.get("heading") or "U.S. Unemployment Rate %",
                        fmt="pct_1",
                        domain=("0", "10"),
                    ),
                    line_chart(
                        "s27-gdp",
                        labs_g,
                        sers_g,
                        heading=sec27.get("heading") or "U.S. GDP Growth* %",
                        fmt="pct_1",
                    ),
                ]
            },
            disclosure=disclosure_from_text(
                "s27-disc",
                "Scenario / SAAR",
                (s27.get("disclosure") or {}).get("panels", [{}])[0].get(
                    "body",
                    "Scenario identities are stable. GDP is SAAR where noted.",
                )
                if isinstance(s27.get("disclosure"), dict)
                else "Scenario identities are stable. GDP is SAAR where noted.",
            ),
        )
    )

    # 28 dual funding
    s28 = json.loads((FIX / "amex_s28_corrected.json").read_text(encoding="utf-8"))[
        "slides"
    ][0]
    tiles = s28["visual_spec"]["primary_visual"]["tiles"]

    def tile_to_stacked(tile, sid, totals, colors):
        steps = tile["steps_or_data"]
        labs = [r[0] for r in steps[1:]]
        series = []
        for ci, name in enumerate(steps[0][1:]):
            series.append(
                (
                    str(name),
                    [r[ci + 1] if ci + 1 < len(r) else None for r in steps[1:]],
                    colors[ci],
                )
            )
        chart = stacked_bar(
            sid,
            labs,
            series,
            heading=tile.get("label") or None,
            fmt="pct_0",
            totals=totals,
        )
        chart["auxiliary_series"][0]["format_id"] = "usd_0"
        chart["display"]["stack_segments"] = "show"
        return chart

    chart_tiles = [t for t in tiles if t.get("kind") == "chart"][:2]
    p0 = tile_to_stacked(
        chart_tiles[0],
        "s28-fund",
        ["210", "219"],
        ["navy", "primary_blue", "sky_blue"],
    )
    p0["subtitle"] = "$ in billions"
    p1 = tile_to_stacked(
        chart_tiles[1],
        "s28-dep",
        ["151", "157"],
        ["navy", "primary_blue", "sky_blue", "neutral"],
    )
    p1["subtitle"] = "$ in billions"
    p1["annotations"] = [
        {
            "annotation_id": "s28-fdic",
            "role": "explanation",
            "text": "92% FDIC insured at Q1'26",
            "anchor": {"type": "chart"},
        }
    ]
    slides.append(
        ordinary(
            28,
            "dual_chart",
            s28["title"],
            "appendix",
            {"charts": [p0, p1]},
            disclosure=disclosure_from_text(
                "s28-disc",
                "FDIC coverage",
                "Approved 92% FDIC coverage callout. No pseudo-title totals.",
            ),
        )
    )

    # 29-30 narrative variance
    for n in (29, 30):
        s = slides_in[n]
        bullets = s["content"].get("bullets") or []
        title = "Additional Commentary — Variance Analysis"
        slides.append(
            ordinary(
                n,
                "narrative",
                title,
                "appendix",
                bullets_to_narrative(bullets, f"var-{n}"),
                subtitle=s["content"].get("subtitle") or None,
            )
        )

    # 31 annex
    s31 = slides_in[31]
    steps31 = s31["visual_spec"]["primary_visual"]["steps_or_data"]
    slides.append(
        ordinary(
            31,
            "annex_table",
            s31["title"].replace("â€”", "—").replace("â€“", "–"),
            "appendix",
            {"table": matrix_table("s31-annex", steps31[0], steps31[1:])},
            subtitle=s31["content"].get("subtitle"),
        )
    )

    # 32 grouped annex
    s32 = json.loads(
        (FIX / "amex_slide32_grouped_annex.json").read_text(encoding="utf-8")
    )
    groups32 = s32["visual_spec"]["primary_visual"]["groups"]
    peers = []
    for gi, g in enumerate(groups32[:2]):
        headers = g["headers"]
        rows_raw = g["rows"]
        # build matrix: header + rows
        data = []
        for r in rows_raw:
            data.append(r["cells"])
        table = matrix_table(
            f"s32-peer-{gi}",
            headers,
            data,
            stub_header=headers[0],
        )
        # matrix_table treats headers[0] as stub — columns from headers[1:]
        # but data rows include stub as cells[0]; matrix_table expects that.
        peers.append(
            {
                "heading": g["heading"],
                "table": table,
            }
        )
    slides.append(
        ordinary(
            32,
            "grouped_annex_table",
            "Annex 1 (2 of 2) Billed Business — Reported & FX-Adjusted",
            "appendix",
            {"tables": peers},
            subtitle=s32["content"].get("subtitle"),
        )
    )

    # 33-37 annex restored
    ann = json.loads(
        (FIX / "amex_annex_33_37_restored_handoff.json").read_text(encoding="utf-8")
    )
    for s in ann["slides"]:
        n = s["slide_number"]
        steps = s["visual_spec"]["primary_visual"]["steps_or_data"]
        slides.append(
            ordinary(
                n,
                "annex_table",
                s["title"].replace("â€”", "—"),
                "appendix",
                {"table": matrix_table(f"s{n}-annex", steps[0], steps[1:])},
                subtitle=s["content"].get("subtitle"),
            )
        )

    # 38-43 legal
    for n in range(38, 44):
        s = slides_in[n]
        body = s["content"].get("body_text")
        bullets = s["content"].get("bullets") or []
        paras = []
        if body:
            # split long body into paragraphs if needed
            if isinstance(body, str):
                chunks = [p.strip() for p in re.split(r"\n\n+", body) if p.strip()]
                paras.extend(chunks or [body])
        paras.extend([b for b in bullets if isinstance(b, str)])
        if n == 38:
            paras = [S38_PREAMBLE] + [f"- {p}" if not p.lstrip().startswith(("- ", "* ", "• ")) else p for p in paras]
        # legal max 6 paragraphs
        paras = paras[:6]
        if not paras:
            paras = ["See source PDF for forward-looking statements."]
        # ensure non-empty and not too long issues
        payload = {
            "notice_id": "forward-looking-statements",
            "part": n - 37,
            "total_parts": 6,
            "paragraphs": paras,
        }
        if n == 38:
            payload["title"] = "Cautionary Note Regarding Forward-Looking Statements"
        slides.append(
            {
                "slide_number": n,
                "layout_type": "legal_notice",
                "section_id": "legal",
                "payload": payload,
                "evidence_ids": [ev_id(n)],
            }
        )

    # 44 closing
    slides.append(
        {
            "slide_number": 44,
            "layout_type": "closing_cover",
            "payload": {"title": "American Express"},
            "evidence_ids": [ev_id(44)],
        }
    )

    # First legal needs divider? D314: legal is section; section_divider only for appendix.
    # Contiguity: earnings 2-22, appendix 24-37, legal 38-43. Need legal section divider?
    # D178: divider immediately precedes first ordinary slide of section.
    # Insert legal divider before 38.
    legal_div = {
        "slide_number": 0,  # renumber
        "layout_type": "section_divider",
        "payload": {"section_id": "legal"},
        "evidence_ids": [ev_id(38)],  # pin to first legal page; will fix unique evidence
    }
    # Actually evidence must all be referenced; reusing p38 is ok if slide 38 also refs it.
    # Insert before legal slides without changing 1-44 numbers — CANNOT insert extra slide.
    # D314 maps 38-43 as legal_notice only; section contiguity can start without divider
    # if no divider is required for every section. Check Deck validator: divider only
    # validated when present. Unused section? legal is used by 38-43. OK without divider.

    deck = {
        "meta": {"handoff_schema_version": 1},
        "sections": sections,
        "number_formats": nfmt(),
        "evidence_registry": evidence_registry(),
        "slides": slides,
    }

    # Drop unused number formats after a dry validate pass in main.
    return _clean_obj(deck)


def ascii_fold(s: str) -> str:
    if not isinstance(s, str):
        return s
    table = {
        0x2014: " - ", 0x2013: "-", 0x2019: "'", 0x2018: "'",
        0x201c: '"', 0x201d: '"', 0x00b7: " / ", 0x2022: "*",
        0x2191: " up ", 0x2193: " down ", 0x20ac: "EUR ", 0x00a3: "GBP ",
        0x00a5: "JPY ", 0x2122: "", 0x00ae: "", 0x00a0: " ",
    }
    s = s.translate(table)
    while "  " in s:
        s = s.replace("  ", " ")
    return s


def fold_obj(o):
    if isinstance(o, str):
        return ascii_fold(o)
    if isinstance(o, list):
        return [fold_obj(x) for x in o]
    if isinstance(o, dict):
        return {k: fold_obj(v) for k, v in o.items()}
    return o


def prune_formats(deck: dict) -> dict:
    """Keep only referenced format ids."""
    blob = json.dumps(deck)
    used = {k for k in deck["number_formats"] if f'"format_id": "{k}"' in blob or f'"format_id":"{k}"' in blob}
    # also value_axes format_id
    import re as _re

    used |= set(_re.findall(r'"format_id": "([a-z0-9_-]+)"', blob))
    deck["number_formats"] = {
        k: v for k, v in deck["number_formats"].items() if k in used
    }
    return deck


def main() -> None:
    deck = fold_obj(prune_formats(build()))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(deck, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT} slides={len(deck['slides'])}")


if __name__ == "__main__":
    main()
