"""Stamp comparison_manifest classifications and emit GAP_ANALYSIS.md."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COMPARE = ROOT / "passes" / "pass_01" / "compare"
MANIFEST = COMPARE / "comparison_manifest.json"
LEDGER = COMPARE / "ledger_rows.json"
GAP = ROOT / "GAP_ANALYSIS.md"

IDENTITY = json.loads((ROOT / "passes" / "pass_01" / "render_identity.json").read_text(encoding="utf-8"))

# class, recipe, observation
ROWS: dict[int, tuple[str, str, str]] = {
    1: (
        "accepted v3 design divergence",
        "opening_cover",
        "Boardroom opening_cover carries the title and January 25, 2022 date. PDF is navy/cyan brand chrome plus Centurion seal. Seal/brand cover is excluded (CONTEXT.md); not a capture failure.",
    ),
    2: (
        "accepted v3 design divergence",
        "data_table",
        "Six-row Q4/FY grid matches PDF figures. Boardroom data_table vs Amex pill columns is accepted chrome. Gray Notable Impacts side callout has no mixed grid+callout recipe and was folded into disclosure (Type B secondary).",
    ),
    3: (
        "corpus/extraction residual (Type A)",
        "data_table",
        "PDF is an 8-quarter line (Billed Business / Processed / Total) plus a 3-row summary table. single_chart line + support_table can hold that composition. Quarterly plot points were not glyph-readable and were omitted; only the readable table was authored.",
    ),
    4: (
        "candidate renderer defect or capability gap (Type B)",
        "data_table",
        "PDF is FY stacked G&S/T&E bars + 8-quarter growth line + Q4 table (3 panes). dual_chart is exactly two charts and has no support_table. Least-lossy legal stand-in is data_table of the readable Q4/FY figures. Missing recipe: 3-pane chart+chart+table.",
    ),
    5: (
        "corpus/extraction residual (Type A)",
        "data_table",
        "PDF is Online/Offline/Total G&S line plus Q4 table. single_chart line + support_table is legal. Quarterly points were not glyph-readable; table-only authored.",
    ),
    6: (
        "candidate renderer defect or capability gap (Type B)",
        "dual_chart",
        "PDF is stacked mix bars with dollar totals and vs-2019 callouts plus an 8-quarter 4-series line, each with an under-plot table. dual_chart has no per-pane support_table and no geometric vs-2019 callouts. Authored stacked_bar mix + grouped_bar of the Q4 cohort table. Missing recipe: dual chart + two support tables; unread line is a Type A secondary.",
    ),
    7: (
        "candidate renderer defect or capability gap (Type B)",
        "dual_chart",
        "Same 2-chart + 2-table ceiling as s6 (Commercial G&S/T&E stack + SME vs L&G line). Authored stacked_bar + grouped_bar Q4 snapshot. Missing recipe: dual chart with under-plot tables.",
    ),
    8: (
        "corpus/extraction residual (Type A)",
        "data_table",
        "PDF is T&E-by-customer 8-quarter line plus Q4 table. single_chart line + support_table is legal. Line points unread; table authored.",
    ),
    9: (
        "candidate renderer defect or capability gap (Type B)",
        "dual_chart",
        "PDF is two 8-quarter lines plus two Q4 tables. dual_chart can take the two lines but not the tables. Authored two grouped_bar Q4 snapshots. Missing recipe: dual chart + support tables; unread lines are Type A secondary.",
    ),
    10: (
        "corpus/extraction residual (Type A)",
        "dual_chart",
        "PDF is two Q3-Q4 grouped-bar panes with in-bar YoY boxes and year groups. dual_chart grouped_bar is the right recipe; boxed-label auxiliary_series and category_groups exist. Handoff authored dollar bars only (YoY boxes and year separators omitted).",
    ),
    11: (
        "corpus/extraction residual (Type A)",
        "dual_chart",
        "PDF is two bar panes with 30+ DPD strips plus a GCP write-off strip. dual_chart grouped_bar can hold the two main panes; 3+ canvas for the GCP strip is Type B secondary. Handoff used line marks and swapped loan write-off bars (2.5% to 0.6%) onto the receivables 30+ series — a re-author would restore the two bar panes.",
    ),
    12: (
        "corpus/extraction residual (Type A)",
        "chart_hero_dual",
        "PDF is signed stacked write-off/reserve bars with total labels plus an FY Better/(Worse) table. combo with bar_mode stacked + line, and hero for the FY table, is legal. Handoff used grouped combo, so negatives sit side-by-side instead of stacked. Hero KPIs match $2,127 / $4,022 / $6,149.",
    ),
    13: (
        "corpus/extraction residual (Type A)",
        "data_table",
        "PDF is a reserve walk (beginning, builds, releases, endings) with percent boxes. waterfall (and stacked_bar) exist. Handoff authored a 4-row ending snapshot table and dropped the $1.5 / $5.8 / ($2.2) flow columns.",
    ),
    14: (
        "accepted v3 design divergence",
        "data_table",
        "Six metrics x Q4/FY/% vs-2019 match the PDF grid. Boardroom table vs pill columns is accepted chrome.",
    ),
    15: (
        "corpus/extraction residual (Type A)",
        "single_chart",
        "PDF is Q3-Q4 bars with in-bar YoY boxes, average-rate boxes, and an FY inset. combo + boxed-label auxiliary + support_table/metric_strip are legal. Handoff plotted $B bars + rate as a line and omitted YoY boxes and the FY $25.7 inset.",
    ),
    16: (
        "corpus/extraction residual (Type A)",
        "single_chart",
        "PDF is 12 quarterly NCF bars with in-bar YoY and an FY inset ($5.2, 10%, 28%). combo bar+YoY line is a fair stand-in for the boxes; support_table would hold the FY inset and was not authored.",
    ),
    17: (
        "corpus/extraction residual (Type A)",
        "single_chart",
        "Same Q3-Q4 bar + YoY-box + yield-box pattern as s15. combo plots $B + yield line; in-bar YoY and FY $7.8 inset were not authored (boxed labels / support_table / metric_strip).",
    ),
    18: (
        "accepted v3 design divergence",
        "single_chart",
        "Two-series line (YoY and vs-2019) matches the PDF path and labeled points. Boardroom chrome vs PDF inset FY'21 $42.4 box is accepted; support_table could hold the inset (Type A secondary).",
    ),
    19: (
        "accepted v3 design divergence",
        "data_table",
        "Expense grid including Variable CM Engagement and Effective Tax Rate matches. Boardroom table vs pill columns is accepted chrome.",
    ),
    20: (
        "corpus/extraction residual (Type A)",
        "dual_chart",
        "dual_chart grouped_bar is the right two-pane recipe (Marketing $B, Proprietary NCA). NCA bars match 1.4 to 2.7. Marketing Value Injection hatch split was not extracted as a second series; stacked_bar would hold it if the hatch amounts were readable.",
    ),
    21: (
        "candidate renderer defect or capability gap (Type B)",
        "chart_hero_dual",
        "PDF is CET1 bars + Capital Return bars + dividend strip (3 surfaces). chart_hero_dual is one chart + hero KPIs, so CET1 becomes 10.5% text. dual_chart would drop the dividend row. Missing recipe: two charts + metric strip. Capital Return $6.0/$2.3/$9.0 match.",
    ),
    22: (
        "corpus/extraction residual (Type A)",
        "metric_overview",
        "PDF is three equal cards (2022 Guidance / 2023 Expectations / 2024+ Aspiration) plus two qualifier bars. feature_cards (2-6) is the closer legal recipe. metric_overview flattened 2022-2024 into one KPI row and mixed years.",
    ),
    23: (
        "accepted v3 design divergence",
        "section_divider",
        "Boardroom section_divider Appendix vs navy brand divider with Centurion seal. Label matches. Brand chrome excluded.",
    ),
    24: (
        "candidate renderer defect or capability gap (Type B)",
        "data_table",
        "PDF is signed vs-2019 bars with percent share boxes, brace-grouped YoY tables, and a consumer/commercial legend. No recipe composes waterfall/bars + share chips + two grouped tables. data_table holds readable shares/YoY; several vs-2019 bar labels were not fully attributed (Type A secondary).",
    ),
    25: (
        "candidate renderer defect or capability gap (Type B)",
        "grouped_annex_table",
        "PDF is an 8-quarter Online/Offline/G&S line plus two Q4 tables. grouped_annex_table holds the two tables. single_chart cannot also carry two annex matrices. Missing recipe: chart + grouped_annex. Unread line is Type A secondary.",
    ),
    26: (
        "corpus/extraction residual (Type A)",
        "data_table",
        "PDF is T&E-by-industry 8-quarter line plus Q4 table. single_chart line + support_table is legal. Points unread; table authored (Restaurants/Lodging/Airlines/Other/Total match).",
    ),
    27: (
        "candidate renderer defect or capability gap (Type B)",
        "dual_chart",
        "PDF is two mix donuts (Loan 68/12/20; Receivables 28/14/24/34). Closed chart set has no pie/donut. stacked_bar dual_chart is the least-lossy legal stand-in; mix percent match, radial geometry does not.",
    ),
    28: (
        "corpus/extraction residual (Type A)",
        "single_chart",
        "stacked_bar holds Delinquent / FRP / CPR stacks including Apr'20 $8.5 CPR. metric_strip would hold the below-plot Total Loans / CM Receivables boxes and was not authored.",
    ),
    29: (
        "corpus/extraction residual (Type A)",
        "single_chart",
        "PDF is GCP write-off bars plus a Q2'21 bankruptcy side table. grouped_bar + support_table is legal. Handoff used a line and put the side table only in disclosure.",
    ),
    30: (
        "corpus/extraction residual (Type A)",
        "narrative",
        "PDF is two 4-series macro line charts (unemployment, GDP). dual_chart line is legal. Quarterly scenario points were not glyph-readable; authored narrative with an explicit extraction residual. No invented series.",
    ),
    31: (
        "corpus/extraction residual (Type A)",
        "single_chart",
        "stacked_bar of Unsecured Term / Card ABS / Deposits / Short-term is the right recipe and mix percent match. Authored stack totals $126/$138/$132 follow extraction reading order; PDF visual is $138/$132/$126 on Q4'19/Q4'20/Q4'21. Re-author the auxiliary totals.",
    ),
    32: (
        "candidate renderer defect or capability gap (Type B)",
        "data_table",
        "PDF is two 4-quarter Reported vs FX-Adj lines plus a 6-currency table. dual_chart can take the lines but not the table. Unread plot points (Type A secondary). Currency table authored. Missing recipe: dual chart + support table.",
    ),
    33: (
        "faithful reproduction",
        "narrative",
        "Variance commentary bullets match the PDF (Discount Revenue 35%, NCF 10%, OFC 32%, Other 218%, Interest Income 5%, Interest Expense (25%), Provisions 148%). Boardroom narrative chrome only.",
    ),
    34: (
        "faithful reproduction",
        "narrative",
        "Continuation bullets match (Marketing+BD 46%, Rewards 32% with 96% URR, Services 127%, Operating 7%).",
    ),
    35: (
        "candidate renderer defect or capability gap (Type B)",
        "hierarchy",
        "PDF is a freeform ESG strategy board (mission band, stakeholders, governance, three pillars with objective lists, committee stack). hierarchy 5-node tree and layered_architecture 4x4 cannot hold the board. Authored a 5-node part_of tree; objective bullets and committee layers dropped. Missing recipe: freeform strategy / org board.",
    ),
    36: (
        "corpus/extraction residual (Type A)",
        "narrative",
        "narrative can hold the full nested DE&I / Financial Confidence / Climate bullets. Handoff condensed to three summary bullets (Type A authoring miss), not a recipe ceiling.",
    ),
    37: (
        "candidate renderer defect or capability gap (Type B)",
        "annex_table",
        "PDF Annex 1 is an 18-period reported/FX matrix. annex_table cannot present that IR history at 1920x1080 (fit/column ceiling). Authored a 4-column Q4/FY vs-2019 subset. Missing recipe: wide multi-year annex matrix.",
    ),
    38: (
        "candidate renderer defect or capability gap (Type B)",
        "annex_table",
        "Annex 1 (2 of 2) is the same wide matrix for L&G / Int'l SME / SME. 4-column subset only. Same Type B ceiling as s37.",
    ),
    39: (
        "corpus/extraction residual (Type A)",
        "annex_table",
        "Annex 2 PDF is 12 period columns of GAAP/FX discount revenue. Schema allows up to the table column budget; handoff authored only Q3'21/Q4'21/FY'21. Re-author a wider annex_table before calling this a fit ceiling.",
    ),
    40: (
        "candidate renderer defect or capability gap (Type B)",
        "annex_table",
        "Annex 3 PDF is a 19-period NCF history. Same wide-matrix ceiling as Annex 1. Authored Q4'21/FY'21 only.",
    ),
    41: (
        "corpus/extraction residual (Type A)",
        "annex_table",
        "Annex 4 PDF is 12 period columns. Authored Q3'21/Q4'21/FY'21 only; wider annex_table not yet tried.",
    ),
    42: (
        "faithful reproduction",
        "annex_table",
        "Six Q3/Q4 2019-2021 columns for NII / exclusions / yield match the PDF walk ($2,203 to $2,107; yield 11.2% to 10.3%). Boardroom annex chrome only.",
    ),
    43: (
        "candidate renderer defect or capability gap (Type B)",
        "annex_table",
        "Annex 6 (1 of 2) is a 19-period revenue history. Authored Q4'21/FY'21 only. Wide-matrix ceiling.",
    ),
    44: (
        "corpus/extraction residual (Type A)",
        "annex_table",
        "Annex 6 (2 of 2) is 10 period columns (2019 + 2021). Authored the five 2021 columns and dropped the 2019 block; 10 columns are within budget.",
    ),
    45: (
        "faithful reproduction",
        "annex_table",
        "TDR / delinquent FRP / non-delinquent FRP across Dec'19-Dec'21 match ($0.8 to $1.3 / $0.1 / $0.7 to $1.3).",
    ),
    46: (
        "faithful reproduction",
        "annex_table",
        "GCP Q2'21 write-off reconciliation matches: ($24), $37, $13, $11,087, (0.9%), 0.5%.",
    ),
    47: (
        "accepted v3 design divergence",
        "legal_notice",
        "Forward-looking part 1 of 6. Legal body is present; Boardroom legal_notice vs PDF dense wrapping is accepted chrome.",
    ),
    48: (
        "accepted v3 design divergence",
        "legal_notice",
        "Forward-looking continuation; Boardroom legal chrome.",
    ),
    49: (
        "accepted v3 design divergence",
        "legal_notice",
        "Forward-looking continuation; Boardroom legal chrome.",
    ),
    50: (
        "accepted v3 design divergence",
        "legal_notice",
        "Forward-looking continuation; Boardroom legal chrome.",
    ),
    51: (
        "accepted v3 design divergence",
        "legal_notice",
        "Forward-looking continuation; Boardroom legal chrome.",
    ),
    52: (
        "accepted v3 design divergence",
        "legal_notice",
        "Forward-looking part 6 of 6 plus 10-K/10-Q pointer; Boardroom legal chrome.",
    ),
    53: (
        "accepted v3 design divergence",
        "closing_cover",
        "Boardroom closing_cover American Express vs PDF navy wordmark. Brand cover excluded; blank/logo page still emitted.",
    ),
}

TITLES = {
    1: "American Express Earnings Conference Call Q4'21",
    2: "Summary Financial Performance",
    3: "Total Network Volumes Growth",
    4: "Billed Business (G&S vs T&E)",
    5: "Goods & Services Billed Business (Online vs Offline)",
    6: "Global Consumer Billed Business",
    7: "Global Commercial Billed Business",
    8: "Billed Business T&E Growth",
    9: "Billed Business Growth by Region",
    10: "Worldwide Total Loans and Card Member Receivables",
    11: "Card Member Credit Metrics",
    12: "Total Provision",
    13: "Total Reserves",
    14: "Revenue Performance",
    15: "Discount Revenue",
    16: "Net Card Fees",
    17: "Net Interest Income",
    18: "Total Revenue Net of Interest Expense",
    19: "Expense Performance",
    20: "Marketing Investments and New Cards Acquired",
    21: "Capital",
    22: "The Growth Plan",
    23: "Appendix",
    24: "Q4'21 Network Volumes Growth by Customer Type",
    25: "Global Consumer G&S Growth",
    26: "Travel & Entertainment Billed Business",
    27: "Worldwide Total Loans and Card Member Receivables Mix",
    28: "Delinquent and Financial Relief Program Balances",
    29: "Global Corporate Payments Card Member Credit Metrics",
    30: "Credit Reserve Build Macroeconomic Assumptions",
    31: "Funding Mix",
    32: "FX Impact on Network Volumes and Revenue Growth",
    33: "Additional Commentary – Variance Analysis",
    34: "Additional Commentary – Variance Analysis",
    35: "Environmental, Social and Governance (ESG) Strategy",
    36: "2021 ESG Highlights",
    37: "Annex 1 Network Volumes – Reported & FX-Adjusted",
    38: "Annex 1 Network Volumes – Reported & FX-Adjusted",
    39: "Annex 2 Discount Revenue – Reported & FX-Adjusted",
    40: "Annex 3 Net Card Fees – Reported & FX-Adjusted",
    41: "Annex 4 Net Interest Income – Reported & FX-Adjusted",
    42: "Annex 5 Consolidated Net Interest Yield on Average Card Member Loans",
    43: "Annex 6 Revenues Net of Interest Expense",
    44: "Annex 6 Revenues Net of Interest Expense",
    45: "Annex 7 Troubled Debt Restructurings (TDR) Balance",
    46: "Annex 8 GCP Card Member Receivables Net Write-Off rates",
    47: "Forward Looking Statements",
    48: "Forward Looking Statements",
    49: "Forward Looking Statements",
    50: "Forward Looking Statements",
    51: "Forward Looking Statements",
    52: "Forward Looking Statements",
    53: "closing cover",
}

VOCAB = [
    "faithful reproduction",
    "accepted v3 design divergence",
    "candidate renderer defect or capability gap (Type B)",
    "corpus/extraction residual (Type A)",
    "source/PDF artifact",
    "capture failure",
]


def stamp_manifest() -> dict:
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if set(ROWS) != set(range(1, 54)):
        raise SystemExit(f"missing rows {set(range(1,54)) - set(ROWS)}")
    counts: Counter[str] = Counter()
    for s in m["slides"]:
        n = int(s["slide_number"])
        cls, recipe, obs = ROWS[n]
        if s["layout_type"] != recipe:
            raise SystemExit(f"layout mismatch s{n}: manifest={s['layout_type']} ledger={recipe}")
        s["classification"] = cls
        s["observation"] = obs
        s["recipe"] = recipe
        counts[cls] += 1
    m["classification_vocab"] = VOCAB
    m["classification_counts"] = dict(counts)
    MANIFEST.write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
    LEDGER.write_text(
        json.dumps(
            {str(k): {"class": v[0], "recipe": v[1], "observation": v[2], "title": TITLES[k]} for k, v in ROWS.items()},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return m


def bucket_slides(cls: str) -> list[int]:
    return [n for n, v in ROWS.items() if v[0] == cls]


def write_report(m: dict) -> None:
    art = IDENTITY["artifacts"]
    counts = Counter(v[0] for v in ROWS.values())
    faithful = bucket_slides("faithful reproduction")
    accepted = bucket_slides("accepted v3 design divergence")
    type_a = bucket_slides("corpus/extraction residual (Type A)")
    type_b = bucket_slides("candidate renderer defect or capability gap (Type B)")
    replicated = faithful + accepted

    ledger_lines = [
        "| Slide | Title | Layout | SBS | Class | Observation |",
        "|------:|-------|--------|-----|-------|-------------|",
    ]
    for n in range(1, 54):
        cls, recipe, obs = ROWS[n]
        sbs = f"passes/pass_01/compare/sbs/slide_{n:02d}.png"
        ledger_lines.append(
            f"| {n} | {TITLES[n]} | `{recipe}` | `{sbs}` | {cls} | {obs} |"
        )

    recipes_used = sorted({v[1] for v in ROWS.values()})
    chart_types = {
        6: "stacked_bar + grouped_bar",
        7: "stacked_bar + grouped_bar",
        9: "grouped_bar + grouped_bar",
        10: "grouped_bar + grouped_bar",
        11: "line + line",
        12: "combo (grouped) + hero",
        15: "combo",
        16: "combo",
        17: "combo",
        18: "line",
        20: "grouped_bar + grouped_bar",
        21: "grouped_bar + hero",
        27: "stacked_bar + stacked_bar (donut stand-in)",
        28: "stacked_bar",
        29: "line",
        31: "stacked_bar",
    }

    def slist(nums: list[int]) -> str:
        return ", ".join(f"s{n:02d}" for n in nums) if nums else "(none)"

    md = f"""# Q4 2021 renderer_v3 recipe-coverage baseline

Companion-mode AUTHORING + OBSERVATION. Handoff JSON and simulation artifacts only. No production paths, no new recipes, no GitHub issues, no image scoring.

## Identity

| Field | Value |
|-------|-------|
| Source PDF | `C:/Users/Ag1Le/Downloads/Q4-2021-Earnings-Presentation.pdf` |
| SHA-256 | `8e113208a6df838861fc06cdbfb82514f01f43c42a21e02005801f8fdf545e21` |
| Pages | 53 (720x404 landscape, rasterized to 1920x1080) |
| Handoff | `simulation/amex_q4_2021/handoff_v1.json` |
| Handoff schema | 1 (`meta.handoff_schema_version`) |
| Slides | 53 (`slide_number` 1..53; evidence `amex-q4-2021-p01`..`p53`) |
| Renderer | renderer_v3 **3.0.0**, theme `boardroom_amex` |
| Repository commit at render | `{IDENTITY["repository_commit"]}` |
| Branch | `{IDENTITY["branch"]}` |
| Render | strict, exit 0, `run_meta.status=clean`, `ok=true`, warnings=0 errors=0 |
| HTML identity | 53 unique `data-slide-number` 1..53; `data-layout` matches authored `layout_type` |
| Capture viewport | 1920x1080, `deviceScaleFactor=1`; stacked-deck fit transforms cleared before element screenshots |
| Console | empty (no error/warning/pageerror) |

### Published render artifacts (`passes/pass_01/renderer_v3_out/`)

| Artifact | Bytes | SHA-256 |
|----------|------:|---------|
| presentation.html | {art["presentation.html"]["bytes"]} | `{art["presentation.html"]["sha256"]}` |
| slide_notes.md | {art["slide_notes.md"]["bytes"]} | `{art["slide_notes.md"]["sha256"]}` |
| evidence_manifest.json | {art["evidence_manifest.json"]["bytes"]} | `{art["evidence_manifest.json"]["sha256"]}` |
| run_meta.json | {art["run_meta.json"]["bytes"]} | `{art["run_meta.json"]["sha256"]}` |
| handoff_schema_v1.json | {art["handoff_schema_v1.json"]["bytes"]} | `{art["handoff_schema_v1.json"]["sha256"]}` |

`run_meta` info events (not errors): 40 `plan.typography_grown`, 11 `plan.text_wrapped`, 6 `plan.synchronized`.

## Scope audit

Allowed this run: new files under `simulation/amex_q4_2021/` plus one wiki report copy. Forbidden: `impact_slides/`, `tests/`, `scripts/`, existing wiki docs, configs, CI, GitHub issues/PRs, new layouts/chart types/painters/theme tokens/schema fields, MAE/similarity/pixel-diff scores, invented numbers.

Q1 2026 `tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json` was used only as a schema-v1 shape reference. Content is from the Q4 2021 PDF (PyMuPDF text/tables). Glyph-unread plot points were omitted, not guessed.

## Mapping assertion

HTML slide N maps to PyMuPDF index N-1 and physical PDF page N. Before capture: 53 unique `data-slide-number` values 1..53, each slide `data-layout` matches authored `layout_type`, PDF has 53 pages. Every comparison row states slide number, layout_type, PDF index, and physical page.

## Capture contract

- `scripts/simulation_probe.py`: `wait_for_paint_ready_charts` before every chart-slide screenshot (also enforces identity).
- Zero matches, wrong layouts, missing Chart instances, zero-size canvases, degenerate chartArea, or missing dataset geometry are failures.
- Did **not** call `painted_datalabel_lines`.
- Did **not** run `DESIGN_LEDGER_*` maps (those are Q1 2026 slide numbers).
- Optional `measured_tick_styles` on all 16 chart slides as a note, not a stop.
- Capture: scroll target `section.slide` into view; element screenshot exactly 1920x1080 PNG.
- PDF pages rasterized with PyMuPDF to exactly 1920x1080.
- Side-by-sides 3840x1080, PDF left / renderer_v3 right, no downscaling of either half.
- Labeled 53-slide contact sheet: `passes/pass_01/compare/contact_sheet.png`.
- Manifest: `passes/pass_01/compare/comparison_manifest.json` (53 rows, each with layout_type + classification).
- Primary JS-on Chart.js surface; noscript SVG fallback not captured.

## Render outcome

**Clean strict render.** Not DEGRADED. No `--no-strict` path.

## 53-row qualitative ledger

No MAE, similarity percentages, pixel-diff scores, or heatmaps. Classes are mutually exclusive per row.

Counts: faithful {counts['faithful reproduction']}; accepted Boardroom chrome {counts['accepted v3 design divergence']}; Type A {counts['corpus/extraction residual (Type A)']}; Type B {counts['candidate renderer defect or capability gap (Type B)']}; source/PDF artifact 0; capture failure 0.

{chr(10).join(ledger_lines)}

## Residual triage

Only residuals with fresh SBS/probe evidence. No fix designed. No tickets.

### 1. Replicated with existing recipes (faithful + accepted Boardroom chrome)

{slist(replicated)} — {len(replicated)} slides.

Cover, appendix divider, closing cover, Q4/FY summary grids (s02/s14/s19), revenue growth line (s18), variance commentary (s33/s34), compact annexes (s42/s45/s46), and legal_notice parts 1–6 (s47–s52) land on existing recipes. Remaining visual difference is Boardroom chrome vs Amex brand furniture (pill columns, Centurion seal, navy full-bleed).

### 2. Type (A) handoff misses — would likely replicate if re-authored

{slist(type_a)} — {len(type_a)} slides.

| Slide | Location | Impact | Ownership | Smallest next verification |
|------:|----------|--------|-----------|----------------------------|
| 3, 5, 8, 26, 30 | 8-quarter (or scenario) line plots with unread glyphs | Plot absent; table/narrative only | handoff / extraction | Re-read labeled endpoints from the PDF (not guess interiors); author `single_chart`/`dual_chart` line + `support_table` |
| 10 | dual grouped_bar | Dollar bars present; in-bar YoY boxes and year groups omitted | handoff | Author boxed-label `auxiliary_series` + `category_groups` |
| 11 | dual_chart line vs PDF bars | Wrong mark; loan write-off series swapped onto receivables 30+ | handoff | Re-author two `grouped_bar` panes; leave GCP strip as Type B |
| 12 | chart_hero_dual combo | Grouped combo instead of stacked signed bars | handoff | `bar_mode: stacked` + line for Total Provision |
| 13 | data_table | Ending snapshot; reserve walk omitted | handoff | Author `waterfall` (or stacked_bar walk) from PDF flow labels |
| 15, 16, 17 | single_chart combo | Rate/yield as line; YoY boxes and FY insets omitted | handoff | boxed-label auxiliary + `support_table`/`metric_strip` for FY inset |
| 20 | dual_chart Marketing pane | Value Injection hatch not a second series | handoff / extraction | If hatch dollars are readable, stacked_bar; else leave as accepted single series |
| 22 | metric_overview | Three-horizon cards flattened | handoff | Re-author as `feature_cards` (3 cards) |
| 28 | stacked_bar | Below-plot loan/receivable boxes omitted | handoff | `metric_strip` on single_chart |
| 29 | single_chart line | Bars + side table collapsed | handoff | `grouped_bar` + `support_table` |
| 31 | stacked_bar totals | Auxiliary totals $126/$138/$132 vs PDF $138/$132/$126 | handoff | Swap authored_stack_total order to match categories |
| 36 | narrative | Nested ESG bullets condensed | handoff | Restore full nested list from page_36.txt |
| 39, 41, 44 | annex_table | Recent-period subset of a still-legal column count | handoff | Re-author wider annex_table (12 / 12 / 10 columns) and re-fit |

### 3. Type (B) recipe/capability gaps — no adequate existing composition

{slist(type_b)} — {len(type_b)} slides.

| Slide | Missing recipe / schema ceiling | Impact | Ownership | Smallest next verification |
|------:|--------------------------------|--------|-----------|----------------------------|
| 4 | 3+ pane canvas (stack + line + table) | Table-only stand-in | renderer recipe | Confirm dual_chart still rejects a third pane |
| 6, 7, 9 | dual_chart + per-pane support tables; geometric vs-2019 callouts | Q4 snapshot bars instead of time series + tables | renderer recipe | dual_chart + support is still illegal; do not invent a layout |
| 21 | two charts + metric strip (CET1 + Capital Return + dividend) | CET1 demoted to hero text | renderer recipe | chart_hero_dual remains one chart |
| 24 | waterfall/bars + share chips + brace-grouped tables | data_table stand-in | renderer recipe | No mixed composition exists |
| 25 | line chart + grouped_annex_table | Tables without the line | renderer recipe | single_chart cannot host two annex matrices |
| 27 | pie / donut | stacked_bar mix stand-in | renderer recipe | Closed chart set has no pie/donut |
| 32 | dual_chart + currency support table | Currency table without the two FX lines | renderer recipe | dual_chart has no support_table |
| 35 | freeform strategy / org board | 5-node hierarchy drop | renderer recipe | hierarchy max depth/shape cannot paint the PDF board |
| 37, 38, 40, 43 | wide multi-year annex matrix (~18–19 period columns at 1920x1080) | 2–4 column subset | renderer recipe | annex_table column/fit ceiling; do not add columns in this run |

s02 Notable Impacts callout is a Type B secondary on an otherwise accepted table.

### 4. Source/PDF artifact or capture failure

None. Console empty. All 53 PDF/HTML halves are 1920x1080 and all SBS are 3840x1080. Paint-ready identity held on every chart slide.

## Recipe coverage summary

### Recipes this deck exercised

{chr(10).join(f"- `{name}`" for name in recipes_used)}

Chart types actually painted:

{chr(10).join(f"- s{n:02d}: {desc}" for n, desc in chart_types.items())}

Also used: `support` none on these slides; `hero` on s12 and s21; `grouped_annex_table` on s25; `hierarchy` on s35; `metric_overview` on s22; `legal_notice` parts 1–6.

### Closed-set recipes not used

`period_comparison` (locked to current/comparison/variance — Q4+FY grids used `data_table`), `comparison_cards`, `process_flow`, `timeline`, `decision_tree`, `feedback_loop`, `layered_architecture`, `data_pipeline`, `stakeholder_map`, `quadrant_matrix`, `feature_cards` (should have been s22), `quotation`, `evidence_review`, `risk_opportunity_review`, `recommendation_case`, `state_transition`, `horizontal_bar`, `heatmap`, `waterfall` (should have been tried on s13), `outlined_support`, `metric_strip`, `support_table`.

### PDF patterns with no recipe

- Brand full-bleed cover / divider / closing wordmark (Centurion seal) — accepted Boardroom chrome.
- Pie / donut mix (s27).
- 3+ chart or chart+chart+table canvases (s4, s21, and several volume pages).
- dual_chart with per-pane support tables (s6, s7, s9, s32).
- Freeform callouts, hatch fills, brace groups, share chips (s2, s20, s24).
- Freeform ESG strategy board (s35).
- 18–19 column IR annex histories at 1920x1080 (s37, s38, s40, s43).

## Diagnostics

- Strict render: clean. No typed validation errors.
- Capture console: `[]`.
- No MAE / similarity % / pixel-diff / heatmap anywhere in this baseline.
- ASCII-only labels (dagger / EUR / GBP / JPY spelled out) so `plan.conservative_metrics` stayed off.

## Artifact links

Relative to `simulation/amex_q4_2021/`:

- `handoff_v1.json`
- `passes/pass_01/renderer_v3_out/presentation.html`
- `passes/pass_01/renderer_v3_out/run_meta.json`
- `passes/pass_01/render_identity.json`
- `passes/pass_01/compare/comparison_manifest.json`
- `passes/pass_01/compare/contact_sheet.png`
- `passes/pass_01/compare/pdf/slide_01.png` … `slide_53.png`
- `passes/pass_01/compare/html/slide_01.png` … `slide_53.png`
- `passes/pass_01/compare/sbs/slide_01.png` … `slide_53.png`

Wiki copy (docs commit only): `wiki/baseline_q4_2021_RECIPE_COVERAGE.md` — byte-identical to this file.

Do not embed PNGs in this report.
"""
    GAP.write_text(md, encoding="utf-8", newline="\n")
    print(f"wrote {GAP} bytes={GAP.stat().st_size}")
    print("counts", dict(counts))


def main() -> None:
    m = stamp_manifest()
    write_report(m)
    # prove 53 classified rows
    missing = [s["slide_number"] for s in m["slides"] if not s.get("classification")]
    if missing:
        raise SystemExit(f"unclassified {missing}")
    print("ok")


if __name__ == "__main__":
    main()
