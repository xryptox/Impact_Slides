# Q4 2021 renderer_v3 recipe-coverage baseline

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
| Repository commit at render | parent `510eb564742b10eb382767933967506f20be0adf` plus #317 s11 domain pin |
| Branch | `ticket-wave/031c70ad-4842-4187-9907-714f386441e1/issue-317` |
| Render | strict, exit 0, `run_meta.status=clean`, `ok=true`, warnings=0 errors=0 |
| HTML identity | 53 unique `data-slide-number` 1..53; `data-layout` matches authored `layout_type` |
| Capture viewport | 1920x1080, `deviceScaleFactor=1`; stacked-deck fit transforms cleared before element screenshots |
| Console | empty (no error/warning/pageerror) |

### Published render artifacts (`passes/pass_01/renderer_v3_out/`)

| Artifact | Bytes | SHA-256 |
|----------|------:|---------|
| presentation.html | 1037882 | `103668429a4e11a89376a786c92ea449b2c8082788532e66830917a6c2ab802a` |
| slide_notes.md | 3361 | `1e7f90090b726e5bf9cbbc081b9b557b5f7a04219b535fb087fac259a8984b41` |
| evidence_manifest.json | 25028 | `1e0f9031d87ad8429479964732bbafd89a5bf4ce69b560559d4777e5a69f3751` |
| run_meta.json | 252862 | `b97f59d013d735175d097a1f473e51186505ad7633ca86f621cec9a133e7112c` |
| handoff_schema_v1.json | 242133 | `fedbfa48837f7de5f53700ba7d77ebbcd124776395f42ba87dcb9e7782ca68f1` |

`run_meta` info events (not errors): 53 `plan.typography_grown`, 18 `plan.text_wrapped`, 9 `plan.synchronized`, 2 `plan.label_ellipsized`, 2 `plan.short_label_used`.

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
- Optional `measured_tick_styles` on chart slides as a note, not a stop.
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

Counts: faithful 5; accepted Boardroom chrome 42; Type A 5; Type B 1; source/PDF artifact 0; capture failure 0.

| Slide | Title | Layout | SBS | Class | Observation |
|------:|-------|--------|-----|-------|-------------|
| 1 | American Express Earnings Conference Call Q4'21 | `opening_cover` | `passes/pass_01/compare/sbs/slide_01.png` | accepted v3 design divergence | Boardroom opening_cover carries the title and January 25, 2022 date. PDF is navy/cyan brand chrome plus Centurion seal. Seal/brand cover is excluded (CONTEXT.md); not a capture failure. |
| 2 | Summary Financial Performance | `data_table` | `passes/pass_01/compare/sbs/slide_02.png` | accepted v3 design divergence | Six-row Q4/FY grid matches PDF figures. Boardroom data_table vs Amex pill columns is accepted chrome. Gray Notable Impacts side callout was folded into disclosure (`data_table.side_callout` shipped #303; Q4 s02 re-author is follow-up). |
| 3 | Total Network Volumes Growth | `single_chart` | `passes/pass_01/compare/sbs/slide_03.png` | accepted v3 design divergence | single_chart line + support_table holds labeled Q3'21/Q4'21 vs-2019 endpoints (Billed 4/12, TNV 4/11, Processed 3/3) plus the Q3/Q4/FY table. Axis ticks pinned to PDF (40%)…20% (`domain.kind=fixed`, #315). Q1'20-Q2'21 interiors unlabeled (nulls; Type A secondary). Boardroom chrome vs Amex full path. |
| 4 | Billed Business (G&S vs T&E) | `dual_chart` | `passes/pass_01/compare/sbs/slide_04.png` | accepted v3 design divergence | dual_chart + shared independent support_table: FY stacked G&S/T&E mix $1,071 / $871 / $1,090 and mix 70/30, 85/15, 81/19; grouped_bar of labeled Q4 vs-'19 endpoints 24/(18)/12. Shared Q4 table G&S 24/19, T&E (18)/132, Total 12/33. Q1'20-Q3'21 line interiors unlabeled so the growth pane is not a line (Type A secondary). Boardroom chrome vs Amex 8-quarter path. |
| 5 | Goods & Services Billed Business (Online vs Offline) | `data_table` | `passes/pass_01/compare/sbs/slide_05.png` | corpus/extraction residual (Type A) | PDF is Online/Offline/Total G&S 8-quarter vs-2019 line plus Q4 table. Page-5 glyphs: axis ticks (40)/(20)/0/20/40, quarter labels, series names, Q4 table vs-'19 31/12/24. No second labeled plot point (#296). Line leftover stands; table authored. Do not invent interiors. |
| 6 | Global Consumer Billed Business | `dual_chart` | `passes/pass_01/compare/sbs/slide_06.png` | accepted v3 design divergence | dual_chart per-pane support: stacked G&S/T&E mix $119-$174 with independent navy-header Q4 YoY table, plus age-cohort grouped_bar of labeled vs-2019 endpoints 50/17/0 with independent navy-header Q4 table (stub `Q4'21`; vs. '19 / YoY / % of Total). Geometric vs-2019 callouts omitted (`geometric_callouts` shipped #302; Q4 geometric authoring stays out of scope). Age-cohort 8-quarter interiors unlabeled (#301 leftover). Page-6 glyphs: axis ticks (50)/(30)/(10)/10/30/50, quarter labels, series names, Q4 table vs-'19 50/17/(0). No second labeled plot point. Boardroom chrome vs Amex callouts. |
| 7 | Global Commercial Billed Business | `dual_chart` | `passes/pass_01/compare/sbs/slide_07.png` | accepted v3 design divergence | dual_chart per-pane support: Commercial G&S/T&E mix $104-$141 with independent navy-header Q4 YoY table, plus SME vs L&G grouped_bar of labeled vs-2019 endpoints 25/17/(33) with independent navy-header Q4 table (stub `Q4'21`; vs. '19 / YoY / % of Total). Geometric vs-2019 callouts omitted (`geometric_callouts` shipped #302; Q4 geometric authoring stays out of scope). SME 8-quarter interiors unlabeled (#301 leftover). Page-7 glyphs: axis ticks (80)/(60)/(40)/(20)/0/20/40, quarter labels, series names, Q4 table vs-'19 25/17/(33). No second labeled plot point. |
| 8 | Billed Business T&E Growth | `data_table` | `passes/pass_01/compare/sbs/slide_08.png` | corpus/extraction residual (Type A) | PDF is T&E-by-customer 5-series vs-2019 line plus Q4 table. Page-8 glyphs: axis ticks (100)/(80)/(60)/(40)/(20)/0, quarter labels, series names (US Consumer / Total SME / Total T&E / Intl Consumer / Large & Global Corporate), Q4 table, and Q4'21 % of Q4'19 callouts 108/83/82/78/36. Those callouts are not vs-2019 plot glyphs. No interior vs-2019 labels (#297). Line leftover stands (5 series exceeds line max 4; two-finite-value rule). Table authored. Do not raise the line ceiling; do not plot 108/83/82/78/36 as vs-2019. |
| 9 | Billed Business Growth by Region | `dual_chart` | `passes/pass_01/compare/sbs/slide_09.png` | accepted v3 design divergence | dual_chart per-pane support: US vs International grouped_bar of labeled Q4 vs-2019 16/(1)/12 plus independent navy-header Q4 table; G&S vs T&E by region grouped_bar of labeled Q4 vs-2019 26/19/24/(10)/(36)/(18) plus independent navy-header 6-col Q4 table (stub `Q4'21`; vs. '19 / YoY / % of Total). 8-quarter interiors unlabeled (#301 leftover). Page-9 glyphs: axis ticks (100)/(80)/(60)/(40)/(20)/0/20, quarter labels, series names, Q4 tables. No second labeled plot point. Boardroom bars vs Amex lines. |
| 10 | Worldwide Total Loans and Card Member Receivables | `dual_chart` | `passes/pass_01/compare/sbs/slide_10.png` | accepted v3 design divergence | dual grouped_bar with boxed YoY and year groups. Dollar bars and YoY match ($88.1-$91.5 loans; $56.6-$53.6 receivables). Boardroom boxed labels vs in-bar YoY boxes. |
| 11 | Card Member Credit Metrics | `dual_chart` | `passes/pass_01/compare/sbs/slide_11.png` | accepted v3 design divergence | dual grouped_bar restores loan write-offs 2.5% to 0.6% and receivables 2.0% to 0.3% with 30+ as a second series. Both panes pin `domain.kind=fixed` 0–5 with ticks 0/1/2/3/4/5 (#317) so DP-3's 15-pt generated span does not crush the 2.5%/2.0% bars. PDF 30+ strips sit under the plot; GCP write-off strip has no third canvas (Type B secondary). Boardroom grouped bars vs under-plot strips. |
| 12 | Total Provision | `chart_hero_dual` | `passes/pass_01/compare/sbs/slide_12.png` | accepted v3 design divergence | chart_hero_dual stacked_bar (Write-offs navy, Reserve Build/(Release)* primary_blue) with `stack_segments: show` and authored stack totals $2,621 … $53. No Total Provision line. Hero KPIs $2,127 / $4,022 / $6,149 unchanged. Boardroom stack labels vs Amex in-bar furniture. |
| 13 | Total Reserves | `single_chart` | `passes/pass_01/compare/sbs/slide_13.png` | accepted v3 design divergence | single_chart waterfall + percent support_table. Walk totals $4.3 / $1.5 / $5.8 / ($2.2) / $3.6 / ($0.2) / $3.4 and reserve % boxes match. PDF two-tone loans+receivables overlay is Boardroom net waterfall. |
| 14 | Revenue Performance | `data_table` | `passes/pass_01/compare/sbs/slide_14.png` | accepted v3 design divergence | Six metrics x Q4/FY/% vs-2019 match the PDF grid. Boardroom table vs pill columns is accepted chrome. |
| 15 | Discount Revenue | `chart_grouped_annex` | `passes/pass_01/compare/sbs/slide_15.png` | accepted v3 design divergence | grouped_bar $B + boxed YoY + Average Discount Rate annex (2.39 / 2.36 / 2.27 / 2.25 / 2.32 / 2.30) + FY'21 $25.7 peer. No rate line, no secondary axis. Boardroom annex vs PDF under-plot boxes. |
| 16 | Net Card Fees | `single_chart` | `passes/pass_01/compare/sbs/slide_16.png` | accepted v3 design divergence | grouped_bar + boxed YoY + FY'21 $5.2 / 10% / 28% support_table. Bars $0.9 to $1.3 match. Boardroom boxed labels vs in-bar YoY boxes. |
| 17 | Net Interest Income | `chart_grouped_annex` | `passes/pass_01/compare/sbs/slide_17.png` | accepted v3 design divergence | grouped_bar $B + boxed YoY + WW Net Interest Yield annex (11.2 / 11.3 / 11.6 / 11.4 / 10.8 / 10.3) + FY'21 $7.8 peer. No yield line, no secondary axis. Boardroom annex vs PDF under-plot boxes. |
| 18 | Total Revenue Net of Interest Expense | `single_chart` | `passes/pass_01/compare/sbs/slide_18.png` | accepted v3 design divergence | Two-series line (YoY and vs-2019) matches the PDF path and labeled points. Boardroom chrome vs PDF inset FY'21 $42.4 box is accepted; support_table could hold the inset (Type A secondary). |
| 19 | Expense Performance | `data_table` | `passes/pass_01/compare/sbs/slide_19.png` | accepted v3 design divergence | Expense grid including Variable CM Engagement and Effective Tax Rate matches. Boardroom table vs pill columns is accepted chrome. |
| 20 | Marketing Investments and New Cards Acquired | `dual_chart` | `passes/pass_01/compare/sbs/slide_20.png` | corpus/extraction residual (Type A) | dual grouped_bar Marketing $1.1 to $1.6 and Proprietary NCA 1.4 to 2.7 match. Page-20 glyphs: Marketing totals $1.1/$1.0/$1.0/$1.3/$1.4/$1.6, NCA 1.4/1.7/2.1/2.4/2.6/2.7, Value Injection legend, FY'21 Marketing $5.3. Hatch has no numeric labels (#298). Hatch leftover stands; Marketing stays one total series. Do not invent hatch split dollars. Do not add a hatch fill recipe. FY $5.3 inset is optional on shared dual support and does not change Type A ownership. |
| 21 | Capital | `dual_chart` | `passes/pass_01/compare/sbs/slide_21.png` | accepted v3 design divergence | dual_chart + shared metric_strip: CET1 bars 10.7/13.5/10.5, Capital Return $6.0/$2.3/$9.0, Q4 dividend $0.43 x3. PDF stack split (buybacks vs dividends) unread; authored one Capital Return series. Boardroom metric_strip vs PDF under-plot dividend row. |
| 22 | The Growth Plan | `feature_cards` | `passes/pass_01/compare/sbs/slide_22.png` | accepted v3 design divergence | feature_cards x3 holds 2022 Guidance / 2023 Expectations / 2024+ Aspiration with PDF sentences. Qualifier bars folded into the 2024+ card. Boardroom cards vs Amex outlined tiles. |
| 23 | Appendix | `section_divider` | `passes/pass_01/compare/sbs/slide_23.png` | accepted v3 design divergence | Boardroom section_divider Appendix vs navy brand divider with Centurion seal. Label matches. Brand chrome excluded. |
| 24 | Q4'21 Network Volumes Growth by Customer Type | `chart_grouped_annex` | `passes/pass_01/compare/sbs/slide_24.png` | accepted v3 design divergence | chart_grouped_annex: grouped_bar of labeled vs-2019 bars 22/18/5/12/(33)/3 (consumer `primary_blue` / commercial `navy` / processed `neutral`) plus six share chips 35/27/12/5/6/14 and two headed peer tables (US Consumer+SME Q3/Q4 YoY 33/33 vs-'19 14/20; Int'l Consumer+SME 25/32 vs-'19 (2)/8). Attribution is PDF x-order + fill. On-bar YoY% 37/29/32/31/34/15 is not a vs-2019 glyph and is omitted, not invented. Brace geometry is peer headings. Boardroom chrome vs Amex chips-above-bars. |
| 25 | Global Consumer G&S Growth | `chart_grouped_annex` | `passes/pass_01/compare/sbs/slide_25.png` | accepted v3 design divergence | chart_grouped_annex: grouped_bar of labeled Q4'21 vs-2019 Online/G&S/Offline 42/26/10 plus two Q4 annex peers (Global Consumer G&S and Holiday Spend). 8-quarter interiors unlabeled (#301 leftover). Page-25 glyphs: axis ticks (40)/(30)/(20)/(10)/0/10/20/30/40/50, quarter labels, series names, Q4 tables vs-'19 42/10/26 and Holiday 55/9/29. No second labeled plot point. Boardroom bars vs Amex line. |
| 26 | Travel & Entertainment Billed Business | `data_table` | `passes/pass_01/compare/sbs/slide_26.png` | corpus/extraction residual (Type A) | PDF is T&E-by-industry 8-quarter vs-2019 line plus Q4 table. Page-26 glyphs: axis ticks (120)/(100)/(80)/(60)/(40)/(20)/0/20, quarter labels, series names (Restaurants / Lodging / Other / Airlines / Total T&E), Q4 table vs-'19 10/(24)/(43)/(14)/(18). No interior vs-2019 labels (#299). Line leftover stands (5 series exceeds line max 4; two-finite-value rule). Table authored. Do not raise the line ceiling; do not invent interiors. |
| 27 | Worldwide Total Loans and Card Member Receivables Mix | `dual_chart` | `passes/pass_01/compare/sbs/slide_27.png` | accepted v3 design divergence | dual_chart of two donuts: Loan mix U.S. Consumer 68 / Intl. Consumer 12 / Small Business 20; Receivables U.S. Consumer 28 / Intl. Consumer 14 / Corporate Card 24 / Small Business 34. Mix percents match. Boardroom default slice cycle vs Amex navy/blue/gray. |
| 28 | Delinquent and Financial Relief Program Balances | `single_chart` | `passes/pass_01/compare/sbs/slide_28.png` | accepted v3 design divergence | stacked_bar Delinquent/FRP/CPR including Apr'20 $8.5 plus two-row category-aligned Total Loans / CM Receivables support boxes ($1.9/$7.1/$3.0/$1.7/$1.6 and $0.9/$4.4/$1.0/$0.6/$0.6) with a frozen 8px row gap. Same-column Delinquent/FRP/CPR/$ total labels do not share an AABB; $0.0 CPR stays a stack-cap label. Figures match. Boardroom isolated boxes vs PDF outlined boxes; not a navy IR grid. |
| 29 | Global Corporate Payments Card Member Credit Metrics | `single_chart` | `passes/pass_01/compare/sbs/slide_29.png` | accepted v3 design divergence | grouped_bar GCP write-offs 2.4% to 0.2% plus Q2'21 bankruptcy support_table ($37 / $33 / $4). Boardroom chart+table vs PDF side table. |
| 30 | Credit Reserve Build Macroeconomic Assumptions | `narrative` | `passes/pass_01/compare/sbs/slide_30.png` | corpus/extraction residual (Type A) | PDF is two 4-series lines (Unemployment, GDP) Q3'20-Q4'23: Q3 Baseline / Q3 Downside / Q4 Baseline / Q4 Downside. Page-30 glyphs: axis ticks (Unemployment 0-18%, GDP (10%)-40%), quarter labels, series names. No labeled endpoints (#300). dual_chart line is legal; two-finite-value rule fails if interiors are unread. Narrative leftover stands. Do not invent series. Do not digitize unlabeled curves. Axis ticks are not observations. |
| 31 | Funding Mix | `single_chart` | `passes/pass_01/compare/sbs/slide_31.png` | accepted v3 design divergence | stacked_bar mix percent and auxiliary totals $138/$132/$126 match Q4'19/Q4'20/Q4'21. Thin Short-term caps 4%/1%/2% stay visible and do not share an AABB with Deposits or the $ total. Boardroom stack vs Amex labeled mix. |
| 32 | FX Impact on Network Volumes and Revenue Growth | `dual_chart` | `passes/pass_01/compare/sbs/slide_32.png` | accepted v3 design divergence | dual_chart + shared independent support_table: 6-currency grouped bars (volumes 4/5/5/3/2/1 and FX 7/1/11/6/(1)/3) plus the currency matrix. Q1'21-Q4'21 Reported vs FX-Adj interiors unlabeled (#301 leftover). Page-32 glyphs: axis ticks (15%)/50%, quarter labels, Reported/FX Adj. series names, 6-currency table. No labeled plot endpoints; axis ticks are not observations. ASCII EUR/GBP/JPY labels. Boardroom bars vs Amex lines. |
| 33 | Additional Commentary – Variance Analysis | `narrative` | `passes/pass_01/compare/sbs/slide_33.png` | faithful reproduction | Variance commentary bullets match the PDF (Discount Revenue 35%, NCF 10%, OFC 32%, Other 218%, Interest Income 5%, Interest Expense (25%), Provisions 148%). Boardroom narrative chrome only. |
| 34 | Additional Commentary – Variance Analysis | `narrative` | `passes/pass_01/compare/sbs/slide_34.png` | faithful reproduction | Continuation bullets match (Marketing+BD 46%, Rewards 32% with 96% URR, Services 127%, Operating 7%). |
| 35 | Environmental, Social and Governance (ESG) Strategy | `hierarchy` | `passes/pass_01/compare/sbs/slide_35.png` | candidate renderer defect or capability gap (Type B) | PDF is a freeform ESG strategy board (mission band, stakeholders, governance, three pillars with objective lists, committee stack). hierarchy 5-node tree and layered_architecture 4x4 cannot hold the board. Authored a 5-node part_of tree; objective bullets and committee layers dropped. Missing recipe: freeform strategy / org board. |
| 36 | 2021 ESG Highlights | `narrative` | `passes/pass_01/compare/sbs/slide_36.png` | accepted v3 design divergence | Three full-text ESG lists (DE&I / Financial Confidence / Climate) match the PDF sentences. Schema has no nested bullets, so nesting is flattened. Boardroom narrative vs PDF nested list. |
| 37 | Annex 1 Network Volumes – Reported & FX-Adjusted | `annex_table` | `passes/pass_01/compare/sbs/slide_37.png` | accepted v3 design divergence | compact annex_table 18-col reported/FX matrix (Q1'19-FY'21 plus five vs-2019 columns) matches the PDF figures. Boardroom annex chrome vs Amex nested Reported/FX stubs. |
| 38 | Annex 1 Network Volumes – Reported & FX-Adjusted | `annex_table` | `passes/pass_01/compare/sbs/slide_38.png` | accepted v3 design divergence | compact annex_table 14-col L&G / Int'l SME / SME matrix matches the PDF figures. Boardroom annex chrome vs Amex nested stubs. |
| 39 | Annex 2 Discount Revenue – Reported & FX-Adjusted | `annex_table` | `passes/pass_01/compare/sbs/slide_39.png` | accepted v3 design divergence | Annex 2 12-column GAAP/FX discount revenue table matches the PDF periods. Boardroom annex chrome vs Amex year-grouped headers. |
| 40 | Annex 3 Net Card Fees – Reported & FX-Adjusted | `annex_table` | `passes/pass_01/compare/sbs/slide_40.png` | accepted v3 design divergence | compact annex_table 20-col Net Card Fees history matches the PDF figures (GAAP $0.8-$5.2; vs-2019 29/28 on FY'21). Headers ellipsize at the compact floor (plan.label_ellipsized); values stay unwrapped. Boardroom annex chrome vs Amex year-grouped headers. |
| 41 | Annex 4 Net Interest Income – Reported & FX-Adjusted | `annex_table` | `passes/pass_01/compare/sbs/slide_41.png` | accepted v3 design divergence | Annex 4 12-column NII GAAP/FX table matches the PDF periods. Boardroom annex chrome vs Amex year-grouped headers. |
| 42 | Annex 5 Consolidated Net Interest Yield on Average Card Member Loans | `annex_table` | `passes/pass_01/compare/sbs/slide_42.png` | faithful reproduction | Six Q3/Q4 2019-2021 columns for NII / exclusions / yield match the PDF walk ($2,203 to $2,107; yield 11.2% to 10.3%). Boardroom annex chrome only. |
| 43 | Annex 6 Revenues Net of Interest Expense | `annex_table` | `passes/pass_01/compare/sbs/slide_43.png` | accepted v3 design divergence | compact annex_table 20-col Revenues Net of Interest Expense history matches the PDF figures (GAAP $9.7-$42.4). Headers ellipsize at the compact floor; values stay unwrapped. Boardroom annex chrome vs Amex year-grouped headers. |
| 44 | Annex 6 Revenues Net of Interest Expense | `annex_table` | `passes/pass_01/compare/sbs/slide_44.png` | accepted v3 design divergence | Annex 6 (2 of 2) 10-column 2019+2021 revenue table matches the PDF periods. Boardroom annex chrome vs Amex year-grouped headers. |
| 45 | Annex 7 Troubled Debt Restructurings (TDR) Balance | `annex_table` | `passes/pass_01/compare/sbs/slide_45.png` | faithful reproduction | TDR / delinquent FRP / non-delinquent FRP across Dec'19-Dec'21 match ($0.8 to $1.3 / $0.1 / $0.7 to $1.3). |
| 46 | Annex 8 GCP Card Member Receivables Net Write-Off rates | `annex_table` | `passes/pass_01/compare/sbs/slide_46.png` | faithful reproduction | GCP Q2'21 write-off reconciliation matches: ($24), $37, $13, $11,087, (0.9%), 0.5%. |
| 47 | Forward Looking Statements | `legal_notice` | `passes/pass_01/compare/sbs/slide_47.png` | accepted v3 design divergence | Forward-looking part 1 of 6. Legal body is present; Boardroom legal_notice vs PDF dense wrapping is accepted chrome. |
| 48 | Forward Looking Statements | `legal_notice` | `passes/pass_01/compare/sbs/slide_48.png` | accepted v3 design divergence | Forward-looking continuation; Boardroom legal chrome. |
| 49 | Forward Looking Statements | `legal_notice` | `passes/pass_01/compare/sbs/slide_49.png` | accepted v3 design divergence | Forward-looking continuation; Boardroom legal chrome. |
| 50 | Forward Looking Statements | `legal_notice` | `passes/pass_01/compare/sbs/slide_50.png` | accepted v3 design divergence | Forward-looking continuation; Boardroom legal chrome. |
| 51 | Forward Looking Statements | `legal_notice` | `passes/pass_01/compare/sbs/slide_51.png` | accepted v3 design divergence | Forward-looking continuation; Boardroom legal chrome. |
| 52 | Forward Looking Statements | `legal_notice` | `passes/pass_01/compare/sbs/slide_52.png` | accepted v3 design divergence | Forward-looking part 6 of 6 plus 10-K/10-Q pointer; Boardroom legal chrome. |
| 53 | closing cover | `closing_cover` | `passes/pass_01/compare/sbs/slide_53.png` | accepted v3 design divergence | Boardroom closing_cover American Express vs PDF navy wordmark. Brand cover excluded; blank/logo page still emitted. |

## Residual triage

Only residuals with fresh SBS/probe evidence. No fix designed. No tickets.

### 1. Replicated with existing recipes (faithful + accepted Boardroom chrome)

s33, s34, s42, s45, s46, s01, s02, s03, s04, s06, s07, s09, s10, s11, s12, s13, s14, s15, s16, s17, s18, s19, s21, s22, s23, s24, s25, s27, s28, s29, s31, s32, s36, s37, s38, s39, s40, s41, s43, s44, s47, s48, s49, s50, s51, s52, s53 — 47 slides.

Cover, appendix divider, closing cover, Q4/FY summary grids (s02/s14/s19), revenue growth line (s18), variance commentary (s33/s34), compact annexes (s42/s45/s46), and legal_notice parts 1–6 (s47–s52) land on existing recipes. Remaining visual difference is Boardroom chrome vs Amex brand furniture (pill columns, Centurion seal, navy full-bleed).

### 2. Type (A) handoff misses — would likely replicate if re-authored

s05, s08, s20, s26, s30 — 5 slides. s03 Boardroom chrome stays accepted; axis is fixed −40…20 (#315); unlabeled interiors are Type A secondary leftover. s06/s07/s09/s25/s32 Boardroom chrome stays accepted; unlabeled interiors are Type A secondary leftovers (#301).

| Slide | Location | Impact | Ownership | Smallest next verification |
|------:|----------|--------|-----------|----------------------------|
| 3 | vs-2019 line interiors | Axis chrome pinned −40…20 (#315); Q1'20–Q2'21 interiors unlabeled | handoff / extraction | Axis accepted/fixed; interiors stay Type A leftover — do not digitize the unread path |
| 5 | G&S Online/Offline line | Table only; Q4'21 endpoints 31/24/12 are one finite value per series | handoff / extraction | Accepted leftover (#296): no second labeled glyph; two-finite-value rule holds |
| 8 | T&E-by-customer line | Table only; 5 series exceeds line max 4; interiors unlabeled | handoff / extraction | Accepted leftover (#297): 5th series required for PDF fidelity is a separate recipe ticket; 108/83/82/78/36 stay in the table |
| 20 | Marketing Value Injection hatch | Hatch has no numeric labels; Marketing stays one total series | handoff / extraction | Accepted leftover (#298): no labeled hatch dollars; do not invent split series; hatch fill recipe is out of scope |
| 26 | T&E-by-industry line | Table only; Q4'21 endpoints 10/(24)/(43)/(14)/(18) are one finite value; Total T&E is a 5th series | handoff / extraction | Accepted leftover (#299): 5th series required for PDF fidelity is a separate recipe ticket; no second labeled glyph; two-finite-value rule holds |
| 30 | Unemployment/GDP scenario lines | Narrative only; no labeled endpoints, axis ticks are not series values | handoff / extraction | Accepted leftover (#300): no labeled endpoints; axis ticks are not series values; do not invent interiors |
| 6 | Age-cohort vs-2019 line | Grouped bar of Q4'21 endpoints 50/17/(0); interiors unlabeled | handoff / extraction | Accepted leftover (#301): no second labeled glyph; two-finite-value rule holds |
| 7 | SME vs L&G vs-2019 line | Grouped bar of Q4'21 endpoints 25/17/(33); interiors unlabeled | handoff / extraction | Accepted leftover (#301): no second labeled glyph; two-finite-value rule holds |
| 9 | Region vs-2019 lines | Grouped bars of Q4'21 endpoints; interiors unlabeled | handoff / extraction | Accepted leftover (#301): no second labeled glyph; two-finite-value rule holds |
| 25 | Online/Offline/G&S vs-2019 line | Grouped bar of Q4'21 endpoints 42/26/10; interiors unlabeled | handoff / extraction | Accepted leftover (#301): no second labeled glyph; two-finite-value rule holds |
| 32 | Reported vs FX-Adj lines | Grouped bars of labeled 6-currency points; Q1'21-Q4'21 interiors unlabeled | handoff / extraction | Accepted leftover (#301): no labeled plot endpoints; axis ticks are not series values |

### 3. Type (B) recipe/capability gaps — no adequate existing composition

s35 — 1 slide.

| Slide | Missing recipe / schema ceiling | Impact | Ownership | Smallest next verification |
|------:|--------------------------------|--------|-----------|----------------------------|
| 35 | freeform strategy / org board | 5-node hierarchy drop | renderer recipe | hierarchy max depth/shape cannot paint the PDF board |

s02 Notable Impacts callout remains folded into disclosure (`side_callout` shipped #303; Q4 re-author out of scope).

### 4. Source/PDF artifact or capture failure

None. s03 HTML/SBS recaptured (#315) at 1920x1080 / 3840x1080; paint-ready identity held (`data-layout=single_chart`, Chart.js y −40…20). s11 HTML/SBS recaptured (#317) at 1920x1080 / 3840x1080; paint-ready identity held (`data-layout=dual_chart`, two Chart.js canvases, y-axis 0%–5%). s12 HTML/SBS recaptured (#318) at 1920x1080 / 3840x1080; paint-ready identity held (`data-layout=chart_hero_dual`, one Chart.js canvas, `data-chart-type=stacked_bar`). s15 and s17 HTML/SBS recaptured (#320) at 1920x1080 / 3840x1080; paint-ready identity held (`data-layout=chart_grouped_annex`, one Chart.js canvas, two annex peers). s24 HTML/SBS recaptured (#321) at 1920x1080 / 3840x1080; paint-ready identity held (`data-layout=chart_grouped_annex`, one Chart.js canvas, six share chips, two peers). s06/s07/s09 HTML/SBS recaptured (#316) at 1920x1080 / 3840x1080; paint-ready identity held (`data-layout=dual_chart`, two Chart.js canvases, independent navy-header supports). s28 HTML recaptured this ticket (#323) at 1920x1080; paint-ready identity held (`data-layout=single_chart`, `data-chart-type=stacked_bar`, category-aligned `s28-boxes` with two body rows and frozen 8px gap). s28 and s31 HTML recaptured this ticket (#324) at 1920x1080; paint-ready identity held (`data-layout=single_chart`, `data-chart-type=stacked_bar`; same-column stack labels uncollided; s31 1%/2%/4% still painted). Other halves were not regenerated.

## Recipe coverage summary

### Recipes this deck exercised

- `annex_table`
- `chart_grouped_annex`
- `chart_hero_dual`
- `closing_cover`
- `data_table`
- `dual_chart`
- `feature_cards`
- `hierarchy`
- `legal_notice`
- `narrative`
- `opening_cover`
- `section_divider`
- `single_chart`

Chart types actually painted:

- s03: line + support_table
- s04: stacked_bar + grouped_bar + independent support_table
- s06: stacked_bar + grouped_bar
- s07: stacked_bar + grouped_bar
- s09: grouped_bar + grouped_bar
- s10: grouped_bar + grouped_bar
- s11: grouped_bar + grouped_bar
- s12: stacked_bar + hero
- s13: waterfall + support_table
- s15: grouped_bar + boxed_label + two annex peers
- s16: grouped_bar + boxed_label + support_table
- s17: grouped_bar + boxed_label + two annex peers
- s18: line
- s20: grouped_bar + grouped_bar
- s21: grouped_bar + grouped_bar + metric_strip
- s24: grouped_bar + share chips + two annex peers
- s25: grouped_bar + two annex peers
- s27: donut + donut
- s28: stacked_bar + support_table
- s29: grouped_bar + support_table
- s31: stacked_bar
- s32: grouped_bar + grouped_bar + independent support_table

Also used: per-pane independent `support_table` on s06/s07/s09; shared `metric_strip` on s21; shared independent `support_table` on s04/s32; `chart_grouped_annex` on s15/s17/s24/s25 (s24 with share chips); donut on s27; compact `annex_table` on s37/s38/s40/s43; `support_table` on s03/s13/s16/s28/s29; `hero` on s12; `hierarchy` on s35; `feature_cards` on s22; `legal_notice` parts 1–6.

### Closed-set recipes not used

`period_comparison` (locked to current/comparison/variance — Q4+FY grids used `data_table`), `comparison_cards`, `process_flow`, `timeline`, `decision_tree`, `feedback_loop`, `layered_architecture`, `data_pipeline`, `stakeholder_map`, `quadrant_matrix`, `metric_overview`, `quotation`, `evidence_review`, `risk_opportunity_review`, `recommendation_case`, `state_transition`, `horizontal_bar`, `heatmap`, `outlined_support`, `grouped_annex_table`.

### PDF patterns with no recipe

- Brand full-bleed cover / divider / closing wordmark (Centurion seal) — accepted Boardroom chrome.
- Freeform callouts, hatch fills, brace groups (s2, s20). s24 share chips now paint; brace geometry stays peer headings.
- Freeform ESG strategy board (s35).

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

Simulation working copy: `simulation/amex_q4_2021/GAP_ANALYSIS.md`.

Do not embed PNGs in this report.
