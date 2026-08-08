# ponytail: one-shot v11 GAP_ANALYSIS writer for this observation run
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def main() -> None:
    ha = json.loads((BASE / "handoff_assertion.json").read_text(encoding="utf-8"))
    pm = json.loads((BASE / "page_slide_mapping.json").read_text(encoding="utf-8"))
    mf = json.loads((BASE / "comparison_manifest.json").read_text(encoding="utf-8"))
    sc = json.loads(
        (BASE / "closed_tickets/scorecard_136_159.json").read_text(encoding="utf-8")
    )
    res = json.loads(
        (BASE / "closed_tickets/closed_ticket_results_v11.json").read_text(
            encoding="utf-8"
        )
    )
    ft = json.loads(
        (BASE / "closed_tickets/focused_tests_summary.json").read_text(encoding="utf-8")
    )
    rm = json.loads(
        (BASE / "passes/pass_01/output/run_meta.json").read_text(encoding="utf-8")
    )

    meas: dict[tuple[str, str, str], dict] = {}
    for c in res["rows"]:
        meas[(str(c.get("ticket")), str(c.get("check")), str(c.get("mode")))] = c

    def mget(ticket: str, check: str, mode: str = "chartjs"):
        c = meas.get((ticket, check, mode))
        return c.get("measured") if c else None

    rows = mf["rows"]
    assert len(rows) == 44 and mf["all_artifacts_present"] is True

    ledger = {
        1: (
            "accepted divergence",
            "Brand cover uses generic seal_lockup + two-tone diagonal recipe vs PDF left-title + large Centurion watermark (brand-asset exclusion / wontfix).",
        ),
        2: (
            "accepted divergence",
            "IR bullet sheet denser line-items + disclosure chip vs PDF large bullets; content present, recipe weight differs (accepted IR density).",
        ),
        3: (
            "solved-ticket verification",
            "#140 five-row pill board: board geometry holds vs PDF targets (+/-4px); five stubs present; geometry PASS (class may include gl-pill-free; geometry is authoritative).",
        ),
        4: (
            "no material new finding",
            "Line chart series and labels track PDF; axis/label chrome differs slightly within house recipe.",
        ),
        5: (
            "no material new finding",
            "U.S. Consumer billed business line + callouts present; no new geometry residual beyond prior accepted callout silhouette locks.",
        ),
        6: (
            "no material new finding",
            "Multi-panel spend/performance tiles render; pane titles HTML-owned where configured.",
        ),
        7: (
            "no material new finding",
            "Three-column membership comparison furniture present; packing differs cosmetically from PDF.",
        ),
        8: (
            "no material new finding",
            "Metric row + breakdown renders; no new evidence-backed gap.",
        ),
        9: (
            "solved-ticket verification",
            "#137/#146 paint-ready: formerly blank risk — 1 canvas paint-ready under activate_slide; identity HOLD.",
        ),
        10: (
            "no material new finding",
            "ICS billed business line chart tracks PDF narrative.",
        ),
        11: (
            "no material new finding",
            "Transaction growth line chart tracks PDF narrative.",
        ),
        12: (
            "source/content residual",
            "#147 partial: chart_hero_dual paints 66%/73% heroes + stacked NCA bars paint-ready (ex-blank #146 PASS), but canonical handoff lacks explicit left/right pane headings/subtitles (PDF has 'Proprietary New Cards Acquired' / 'Proprietary New Accounts Acquired'); mutations do not author them. No duplicate Chart.js title plugin.",
        ),
        13: (
            "solved-ticket verification",
            "#148 vertical grouped bars (indexAxis=x) Total Balances + Billed Business after mutation; paint-ready.",
        ),
        14: (
            "solved-ticket verification",
            "#148 dual_chart pane order 30+ Days Past Due then Net Write-Off Rates; both panes vertical bars.",
        ),
        15: (
            "solved-ticket verification",
            "#136/#149 outlined_boxes: max |cell_cx-bar_cx|=0.188px Chart.js (<=12); label lane gap_px=0.0 vs first value cell; SVG parity. Source reserve-rate values still differ slightly from PDF (source).",
        ),
        16: (
            "no material new finding",
            "Revenue performance data table renders.",
        ),
        17: (
            "solved-ticket verification",
            "#139/#150: two HTML pane titles Net Card Fees ($B)/YoY Growth % @40px; y ticks 24; painted datalabels both panes; typography.mode=auto; no title-plugin duplicate; no clipping.",
        ),
        18: (
            "solved-ticket verification",
            "#151 chart_hero_dual: five boxed YoY labels 11/12/12/12/12%; four-row driver card includes Margin 5%; no synthetic combo YoY line (nDS=1 bar only). Cosmetic: PDF exterior boxed labels vs in-bar paint — accepted recipe.",
        ),
        19: (
            "no material new finding",
            "Total revenues net of interest expense line chart present.",
        ),
        20: (
            "solved-ticket verification",
            "#140 negative control: slide 20 pill path does not match fixed five-row board geometry selector.",
        ),
        21: (
            "solved-ticket verification",
            "#155 capital chart_hero_dual: stacked Dividends+Share Repurchases; shares line 702->682; ROE 35/34/36/36/34/35%; four right-side KPIs. Cosmetic stack color order / KPI wording vs PDF — content present, recipe chrome differs (accepted).",
        ),
        22: (
            "no material new finding",
            "2026 guidance statement card present.",
        ),
        23: (
            "accepted divergence",
            "Appendix divider brand treatment differs from PDF full-bleed art (brand recipe).",
        ),
        24: (
            "solved-ticket verification",
            "#154 six bars + three painted group brackets + aligned support row + exact '$486B Total Network Volumes' + FX note; #140 neg control not fixed pill board. Bracket silhouette differs from PDF dashed callout boxes (accepted recipe).",
        ),
        25: (
            "no material new finding",
            "FX impact table present.",
        ),
        26: (
            "source/content residual",
            "#153 FAIL: handoff still category-row matrix (Category/YoY/% of Total) vs PDF period-column orientation with Q1'26 header; values match but matrix is transposed. amex_handoff_mutations.py does not include #153. Renderer correctly renders the supplied table.",
        ),
        27: (
            "solved-ticket verification",
            "#156 two paint-ready panes; Q1'25-Q1'28; three scenarios each; Unemployment+GDP titles; E0026/PDF page 27 citation; SAAR note in disclosure HTML (not above-fold innerText). #137/#146 ex-blank recheck PASS (2 charts).",
        ),
        28: (
            "solved-ticket verification",
            "#138/#158 one shared-column FDIC callout (92% FDIC / insured at / Q1'26); no pseudo top_total/duplicate badge; pane titles Funding Mix + Deposit Programs with $ in billions subtitles; independent stack totals.",
        ),
        29: (
            "source/content residual",
            "freeform_grid from split_text_visual handoff alias — variance commentary packing differs from PDF two-column art; content-driven.",
        ),
        30: (
            "source/content residual",
            "Continuation variance commentary; same freeform_grid alias note as s29.",
        ),
        31: (
            "no material new finding",
            "Annex 1 table navy headers; structure matches IR annex recipe.",
        ),
        32: (
            "solved-ticket verification",
            "#159 two peer grouped annex tables with deck-unique heading IDs gl-grouped-annex-heading-32-0/1 (Commercial Services / International Card Services).",
        ),
        33: (
            "solved-ticket verification",
            "#157 annex matrix present with stubs, units, FX footnote context.",
        ),
        34: (
            "solved-ticket verification",
            "#157 annex matrix present with stubs, units, FX footnote context.",
        ),
        35: (
            "solved-ticket verification",
            "#157 annex matrix present with stubs, units, FX footnote context.",
        ),
        36: (
            "solved-ticket verification",
            "#157 annex matrix present with stubs, units, FX footnote context.",
        ),
        37: (
            "solved-ticket verification",
            "#157 annex matrix present with stubs, units, FX footnote context.",
        ),
        38: (
            "accepted divergence",
            "Forward-looking statements freeform_grid vs PDF legal layout — content complete, packing recipe differs.",
        ),
        39: (
            "accepted divergence",
            "FLS continuation; same accepted packing divergence.",
        ),
        40: (
            "accepted divergence",
            "FLS continuation; same accepted packing divergence.",
        ),
        41: (
            "accepted divergence",
            "FLS continuation; same accepted packing divergence.",
        ),
        42: (
            "accepted divergence",
            "FLS continuation; same accepted packing divergence.",
        ),
        43: (
            "accepted divergence",
            "FLS continuation; same accepted packing divergence.",
        ),
        44: (
            "accepted divergence",
            "Closing brand divider vs PDF end card — seal_lockup generic mark (brand exclusion).",
        ),
    }
    assert set(ledger) == set(range(1, 45))

    def fmt_ticket_row(t: dict) -> str:
        residual = ", ".join(t.get("residuals") or []) or "—"
        slides = ", ".join(str(s) for s in t.get("slides") or [])
        modes = "+".join(t.get("modes") or [])
        return (
            f"| {t['ticket']} | {t['title']} | `presentation.html` pass_01 | "
            f"DOM/geometry/content probes ({t['n_pass']}/{t['n_checks']} pass) | {modes} | "
            f"slides {slides} | `{t['evidence']}` | **{t['result'].upper()}** | {residual} |"
        )

    mut = ha["mutation_changed_slides"]
    mut_detail = ha.get("mutation_change_detail") or []
    contracts = ha["contracts"]

    L: list[str] = []
    A = L.append

    A("# Gap Analysis v11: renderer_v2 vs Amex Q1'26 Earnings PDF")
    A("")
    A(
        "**(Closed-ticket revalidation #136–#159 + full 44-page PDF↔HTML comparison — observation only)**"
    )
    A("")
    A("**Simulation:** `simulation/amex_q1_2026/`  ")
    A(
        "**Source of truth:** `C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf`  "
    )
    A(
        f"**PDF identity:** SHA-256 `{ha['pdf_sha256']}` · {ha['pdf_pages']} pages · "
        f"page0 rect {ha['pdf_page0_rect'][0]:.2f}×{ha['pdf_page0_rect'][1]:.1f}  "
    )
    A(
        f"**Renderer under test:** `impact_slides.renderer_v2` @ `{ha['renderer_commit_short']}` "
        f"(`{ha['renderer_commit']}`) — current main line; **no production edits this run**  "
    )
    A(
        "**Prior baseline:** `simulation/amex_q1_2026/extracted/baseline_v10_GAP_ANALYSIS.md` "
        "(from origin/gnhf/objective-produce-an-74065a) + `wiki/baseline_v10_VERIFIER_CORRECTION_146.md`  "
    )
    A(
        f"**Handoff source:** `{ha['handoff_source']}` → `passes/pass_01/handoff.pre_mutations.json`  "
    )
    A(
        f"**Handoff SHA-256 pre/post mutations:** `{ha['handoff_pre_sha256']}` / `{ha['handoff_post_sha256']}`  "
    )
    A(
        "**Mutations:** `python scripts/amex_handoff_mutations.py` only — **no hand edits**.  "
    )
    A(f"**Mutation changed slides:** {mut}  ")
    A(
        "**Method:** Playwright geometry via `scripts/simulation_probe.py` "
        "(`activate_slide`, `wait_for_paint_ready_charts`, `painted_datalabel_lines`) + "
        "1920×1080 full-resolution PDF/HTML side-by-sides. House tol ±4px; #136 centres ≤12px.  "
    )
    A("**No MAE / similarity percent / pixel-diff scores / heatmaps.**")
    A("")
    A("---")
    A("")
    A("## 1. Scope gate, mapping assertion, run identity")
    A("")
    A("| Gate | Result |")
    A("|------|--------|")
    A(f"| Renderer commit | `{ha['renderer_commit_short']}` — main HEAD at sim start |")
    A(
        "| Production paths touched | **None** (`impact_slides/`, tests, scripts, configs untouched) |"
    )
    A(
        "| Handoff | Single pass_01 from canonical fixture + `amex_handoff_mutations.py` only; no pass_02 |"
    )
    A(f"| PDF pages | {ha['pdf_pages']} |")
    A(f"| HTML `data-slide-number` unique values | {ha['slide_count']} (1…44) |")
    A("| Identity map | **HTML slide N → PDF index N−1 → physical page N** |")
    A(
        f"| Mapping assertion | **HOLD** (`page_slide_mapping.json` ok={pm.get('ok')}; "
        f"hard_mismatches={pm.get('hard_mismatches')}) |"
    )
    A(
        "| Recipe aliases | handoff `split_text_visual` → HTML `freeform_grid` on slides 29,30,38–43 (known alias, not identity break) |"
    )
    A(
        "| Capture contract | `activate_slide` + `wait_for_paint_ready_charts`; no nth selectors; no fixed sleeps |"
    )
    A(
        f"| Comparison artifacts | 44 PDF + 44 HTML + 44 SBS @1920×1080; contact sheet; "
        f"`all_artifacts_present={mf['all_artifacts_present']}` |"
    )
    A(f"| Console warnings (comparison) | {mf.get('warnings', 0)} |")
    A(
        f"| Image scoring | **forbidden / absent** (`no_image_scoring={mf.get('no_image_scoring')}`) |"
    )
    A(
        "| Scope-gate | PASS — only `simulation/amex_q1_2026/**` + final wiki report; no production edits |"
    )
    A("")
    A("### Handoff contract assertions (pre-capture)")
    A("")
    A("| Contract | Pass | Notes |")
    A("|----------|------|-------|")
    for key, label in [
        ("slide_12_pane_headings", "slide 12 pane headings (#147)"),
        (
            "slide_17_typography_auto",
            "slide 17 typography.mode=auto both panes (#139/#150)",
        ),
        (
            "slide_18_driver_card_boxed_labels",
            "slide 18 driver_card + boxed_labels (#151)",
        ),
        ("slide_26_q1_26_matrix", "slide 26 Q1'26 matrix orientation (#153)"),
    ]:
        c = contracts[key]
        note = c.get("note") or json.dumps(
            {k: c[k] for k in c if k not in ("pass", "note")}, ensure_ascii=False
        )[:200]
        A(f"| {label} | **{'PASS' if c['pass'] else 'FAIL'}** | {note} |")
    A("")
    A(
        f"**all_required_contracts_pass:** `{ha['all_required_contracts_pass']}` — "
        "fails are handoff/fixture gaps (#147, #153), not renderer defects."
    )
    A("")
    A("### Mutation diff (exact changed slides)")
    A("")
    A(f"Script-only changes on slides **{mut}**. Top-key diffs:")
    A("")
    A("| Slide | Title | Diff top keys | layout_type |")
    A("|------:|-------|---------------|-------------|")
    for d in mut_detail:
        keys = ", ".join(d.get("diff_top_keys") or [])
        A(
            f"| {d['slide_number']} | {d.get('title', '')} | {keys} | `{d.get('layout_type', '')}` |"
        )
    A("")
    A("### Page / slide mapping assertion")
    A("")
    A(
        "Numeric identity HTML slide N ↔ PDF index N−1 ↔ physical page N holds for all 44.  "
    )
    A("Full row dump: `simulation/amex_q1_2026/page_slide_mapping.json`.  ")
    A(
        "Every artifact name and scorecard/ledger row carries `slide_number`, "
        "`expected_layout` (HTML `data-layout`), `pdf_page_index`, `pdf_physical_page`."
    )
    A("")
    A("### #137 / #146 process compliance")
    A("")
    A("| Requirement | Evidence |")
    A("|-------------|----------|")
    A(
        "| `activate_slide(page, slide_number, expected_layout)` only | `probes/build_full_comparison.py`, `probes/v11_closed_ticket_probes.py` |"
    )
    A("| No `section.slide[i]` / nth / scrollIntoView activation | Confirmed in probe sources |")
    A(
        "| `wait_for_paint_ready_charts` before every chart screenshot | Full comparison + closed-ticket probes |"
    )
    A(
        "| `painted_datalabel_lines` for Chart.js datalabel evidence | #139/#150, #151 boxed labels, #154 brackets |"
    )
    A(
        "| Zero selector match / missing painted model / zero-size canvas = failure | ProbeError paths; no successful empty observations |"
    )
    A("| Readiness across one animation frame | simulation_probe contract |")
    A(
        "| JSON rows include slide identity | `comparison_manifest.json`, `closed_ticket_results_v11.json` |"
    )
    A(
        "| Console / run_meta with identity | manifest warnings=0; `passes/pass_01/output/run_meta.json` |"
    )
    A("| Formerly blank 9 / 12 / 27 recheck | paint-ready 1 / 1 / 2 charts respectively |")
    A("")
    A(
        "**#137/#146 verdict: PASS (tooling + paint-ready capture contract on full deck).**"
    )
    A("")
    A("---")
    A("")
    A("## 2. Closed-ticket scorecard (#136–#159)")
    A("")
    A(
        "Fresh rendered probes only. Closed GitHub issues are **not** proof. Supporting focused pytest: "
        f"**{ft['summary_line']}** (`closed_tickets/focused_tests_summary.json`) — "
        "unit evidence only, not scorecard substitutes."
    )
    A("")
    A(
        f"Probe totals: **{res['n_pass']}/{res['n_checks']} pass**, **{res['n_fail']} fail** "
        f"(all six fails are #147×2 + #153×4 handoff residuals across chartjs+svg)."
    )
    A("")
    A(
        "| Ticket | Title | Input | Assertion | Runtime(s) | "
        "Slides | Evidence | Result | Residual |"
    )
    A("|--------|-------|-------|-----------|------------|--------|----------|--------|----------|")
    for t in sc:
        A(fmt_ticket_row(t))
    A("")
    A("### Scorecard detail (key measurements)")
    A("")
    A("#### #136 / #149 — slide 15 outlined support + label lane")
    A("")
    A("- Input: mutated pass_01 HTML; list-of-lists primary retained.")
    mx = mget("#136", "max |cell-bar| over 5") or {}
    A(
        f"- Chart.js max |cell_cx−bar_cx| over 5 bars: **{mx.get('max_abs')}px** (≤12)."
    )
    lane = mget("#149", "label lane no overlap first value cell") or {}
    A(f"- Label lane vs first value cell: gap_px=**{lane.get('gap_px')}** (no overlap).")
    A("- SVG mode: same checks PASS (see `closed_ticket_results_v11.json`).")
    A("- **Result: PASS** both modes.")
    A("")
    A("#### #137 / #146 — identity-safe paint-ready capture")
    A("")
    A("- 44 unique `data-slide-number` 1..44; identity activate_slide on 9/12/27.")
    A("- Paint-ready canvases: slide 9 → 1, slide 12 → 1, slide 27 → 2.")
    A("- Console warn/error count: 0.")
    A("- **Result: PASS**.")
    A("")
    A("#### #138 / #158 — slide 28 FDIC callout + pane titles")
    A("")
    A(
        "- One shared-column FDIC callout lines: `92% FDIC` / `insured at` / `Q1'26`; badges=[]."
    )
    A(
        "- No pseudo top_total; pane titles Funding Mix + Deposit Programs; subtitles `$ in billions` ×2."
    )
    A("- Two independent pane charts; stack totals independent.")
    A("- SVG parity PASS.")
    A("- **Result: PASS**.")
    A("")
    A("#### #139 / #150 — slide 17 typography + auto sizes")
    A("")
    A("- Semantic pane titles @40px: Net Card Fees ($B), YoY Growth %.")
    A(
        "- yTick=24 both panes; painted datalabels n=8/9; titlePlugin=false; clipping=false."
    )
    A("- Handoff `typography.mode=auto` both panes retained.")
    A("- **Result: PASS**.")
    A("")
    A("#### #140 — slide 3 pill board + negative controls")
    A("")
    A("- Five-row board geometry vs PDF targets within ±4px (board x/y/w/h).")
    A(
        "- Class may include `gl-pill-free` + empty head stub; **geometry is authoritative**."
    )
    A("- Slide 20: pill layout exists but **not** fixed five-row board geometry.")
    A("- Slide 24: layout `grouped_bar_chart`, hasBoard=false.")
    A("- **Result: PASS**.")
    A("")
    A("#### #147 — slide 12 pane headings")
    A("")
    A("- paint-ready PASS; no duplicate internal chart title PASS.")
    A(
        "- explicit left/right pane headings **FAIL** both modes: `paneTitles=[]`; heroes only (66%/73% copy)."
    )
    A(
        "- Ownership: **handoff** — canonical fixture lacks headings; mutations do not add them."
    )
    A(
        "- SBS confirms PDF has dual titled panels; HTML has stacked bars + hero stats without those pane titles."
    )
    A(
        "- **Result: PARTIAL** (renderer paints supplied content; heading content missing upstream)."
    )
    A("")
    A("#### #148 — slides 13–14 vertical bars + pane order")
    A("")
    A("- Slide 13: indexAxis=x, series Total Balances + Billed Business.")
    A(
        "- Slide 14: pane order 30+ Days Past Due then Net Write-Off Rates; both vertical."
    )
    A("- **Result: PASS**.")
    A("")
    A("#### #151 — slide 18 boxed labels + driver card")
    A("")
    A("- chart_hero_dual + driver_card (4 rows) including Margin 5%.")
    A(
        "- Five boxed YoY labels painted 11/12/12/12/12%; nDS=1 bar; comboLine=false."
    )
    A("- **Result: PASS**.")
    A("")
    A("#### #152 — gridlines default off")
    A("")
    A("- Ordinary plot gridlines off on slides 9/13/15/18 Chart.js + SVG.")
    A("- Mixed-sign domain retains zero context (yMin negative, includesZero).")
    A("- Axes / support borders remain.")
    A("- **Result: PASS**.")
    A("")
    A("#### #153 — slide 26 Q1'26 matrix orientation")
    A("")
    A(
        "- Heads observed: Category / YoY Growth / % of Total Billed Business; hasQ126=false."
    )
    A("- PDF expects period-as-column with Q1'26 header row orientation.")
    A("- Values numerically consistent with PDF but **transposed**.")
    A(
        "- Ownership: **handoff** — fixture still v10 matrix; mutations lack #153."
    )
    A(
        "- **Result: FAIL** (content/orientation; renderer faithful to bad input)."
    )
    A("")
    A("#### #154 — slide 24 growth brackets + $486B")
    A("")
    A(
        "- six bars; three painted semantic group brackets; aligned support % cells."
    )
    A("- exact `$486B Total Network Volumes`; FX-adjusted note present.")
    A("- **Result: PASS**.")
    A("")
    A("#### #155 — slide 21 capital return composition")
    A("")
    A("- stacked Dividends + Share Repurchases; shares line [702…682].")
    A("- ROE support 35/34/36/36/34/35%; four right-side KPIs.")
    A("- **Result: PASS**.")
    A("")
    A("#### #156 — slide 27 macro scenarios")
    A("")
    A(
        "- two paint-ready panes; labels Q1'25–Q1'28; three scenarios each pane."
    )
    A(
        "- titles Unemployment + GDP; E0026 source citation; SAAR in disclosure HTML."
    )
    A("- **Result: PASS**.")
    A("")
    A("#### #157 — slides 33–37 annex matrices")
    A("")
    A(
        "- Each annex: matrix stubs present, correct unit strings, FX footnote/context."
    )
    A("- 30/30 checks PASS across chartjs+svg.")
    A("- **Result: PASS**.")
    A("")
    A("#### #159 — slide 32 grouped annex heading IDs")
    A("")
    A(
        "- two peer tables; headings Commercial Services / International Card Services."
    )
    A(
        "- deck-unique IDs `gl-grouped-annex-heading-32-0`, `…-32-1`."
    )
    A("- **Result: PASS**.")
    A("")
    A("---")
    A("")
    A("## 3. Full 44-page qualitative ledger")
    A("")
    A(
        "Each row links its SBS. Classifications are qualitative only (no image scores)."
    )
    A("")
    A(
        "| # | layout | pdf_idx | physical | SBS | Class | Observation |"
    )
    A("|--:|--------|--------:|----------|-----|-------|-------------|")
    for r in rows:
        n = r["slide_number"]
        cls, obs = ledger[n]
        A(
            f"| {n} | `{r['expected_layout']}` | {r['pdf_page_index']} | "
            f"P{r['pdf_physical_page']} | `{r['sbs_path']}` | **{cls}** | {obs} |"
        )
    A("")
    A("### Manifest summary")
    A("")
    A(f"- Viewport: {mf['viewport']['width']}×{mf['viewport']['height']}")
    A(f"- all_artifacts_present: **{mf['all_artifacts_present']}**")
    A(f"- contact_sheet: `{mf['contact_sheet']}`")
    A(f"- capture_contract: {json.dumps(mf['capture_contract'])}")
    A(f"- no_image_scoring: **{mf['no_image_scoring']}**")
    A("")
    A("---")
    A("")
    A("## 4. v10 → v11 delta")
    A("")
    A("| Area | v10 | v11 |")
    A("|------|-----|-----|")
    A(
        "| Renderer commit | `00d4eb0` (v10 launcher era) | `af3662b` current main (includes #136–#159 ship + #173/#174) |"
    )
    A(
        "| Handoff | v9 archive + limited closed-ticket settings (#138/#139) | Canonical `amex_v10_44_slide_handoff.json` + full `amex_handoff_mutations.py` |"
    )
    A("| Scorecard span | #136–#140 only | **#136–#159** complete |")
    A(
        "| Capture | activate_slide + painted datalabels | + mandatory `wait_for_paint_ready_charts`; ex-blank 9/12/27 recheck |"
    )
    A(
        "| #148 13–14 | line/dual without forced vertical mutation story | **PASS** vertical bars + pane order after mutation |"
    )
    A(
        "| #151 slide 18 | combo_chart narrative | **PASS** chart_hero_dual + boxed labels + driver_card Margin 5% |"
    )
    A(
        "| #154 slide 24 | data_table / pill neg control only | **PASS** grouped_bar + 3 brackets + $486B support |"
    )
    A(
        "| #155 slide 21 | multi_panel capital tiles | **PASS** chart_hero_dual capital return composition |"
    )
    A(
        "| #156 slide 27 | dual_chart present | **PASS** full scenario/horizon/citation/SAAR checks; paint-ready |"
    )
    A(
        "| #157/#159 annex | structural presence | **PASS** units/FX + grouped heading IDs |"
    )
    A(
        "| #147 slide 12 | source residual (missing left stacked pairing called out) | Still **handoff residual** on pane headings; bars+heroes now paint-ready |"
    )
    A(
        "| #153 slide 26 | not in v10 closed set | **New explicit FAIL** — fixture matrix still transposed |"
    )
    A("| Image scoring | none | none |")
    A("")
    A("### Solved since v10 (evidence-backed)")
    A("")
    A(
        "- Paint-ready capture contract holds on formerly blank slides **9, 12, 27** (#146)."
    )
    A("- Slide **13–14** vertical bar semantics after mutations (#148).")
    A(
        "- Slide **18** Premium Lending driver_card + boxed YoY labels without combo line (#151)."
    )
    A(
        "- Slide **21** capital return stack + shares line + ROE + KPIs (#155 / #174)."
    )
    A(
        "- Slide **24** six-bar growth with three brackets + $486B support (#154)."
    )
    A("- Slide **27** full macro scenario dual panes with citation (#156).")
    A(
        "- Slide **28** FDIC shared callout + pane titles without badge chrome (#138/#158)."
    )
    A(
        "- Slides **32–37** annex grouping IDs + matrix units/FX (#157/#159)."
    )
    A("- Default ordinary gridlines off with zero-line retention (#152).")
    A(
        "- Slide **15** outlined support alignment still ≤12px; label lane non-overlap (#136/#149)."
    )
    A(
        "- Slide **17** auto typography + semantic pane titles (#139/#150)."
    )
    A(
        "- Slide **3** fixed pill-board geometry with 20/24 negative controls (#140)."
    )
    A("")
    A("---")
    A("")
    A("## 5. Residual triage")
    A("")
    A("Only residuals with **fresh v11 evidence**. No fixes designed or filed.")
    A("")
    A("### 5.1 Still-open evidence-backed renderer residuals")
    A("")
    A("**None proven in this run.**")
    A("")
    A(
        "Every closed-ticket geometry/DOM failure traced to missing or transposed handoff content (#147, #153). "
        "Cosmetic recipe differences (brand covers, FLS packing, bracket silhouette vs dashed PDF callouts, "
        "in-bar vs exterior YoY boxes) are accepted recipe divergence, not capability defects under the shipped contracts."
    )
    A("")
    A("### 5.2 Still-open handoff / source residuals")
    A("")
    A(
        "| ID | Location | Impact | Likely ownership | Smallest next verification |"
    )
    A(
        "|----|----------|--------|------------------|----------------------------|"
    )
    A(
        "| H1 #147 | slide 12 / P12 `chart_hero_dual` | PDF pane titles/subtitles "
        "('Proprietary New Cards/Accounts Acquired') absent in HTML; heroes 66%/73% present | "
        "Canonical fixture + `amex_handoff_mutations.py` (no #147 authoring) | "
        "Add left/right `heading`+`subtitle` on primary/secondary visuals in fixture or mutation; re-run #147 probe only |"
    )
    A(
        "| H2 #153 | slide 26 / P26 `data_table` | Matrix transposed: category rows vs PDF Q1'26 "
        "period columns; values match but orientation wrong | Canonical fixture still v10 matrix; "
        "mutations lack #153 | Replace slide 26 table with period-column orientation including visible "
        "Q1'26 context; re-run #153 probe |"
    )
    A(
        "| H3 historical pairing note | slide 12 | PDF left panel is titled stacked NCA; HTML supplies "
        "stacked bars without those titles (related to H1) | handoff content pairing | Covered by H1 verification |"
    )
    A(
        "| H4 freeform variance | slides 29–30 | freeform_grid packing vs PDF two-column variance art | "
        "handoff `split_text_visual` → recipe alias | Content completeness check only; not a renderer geometry ticket |"
    )
    A("")
    A("### 5.3 Accepted / non-actionable differences")
    A("")
    A(
        "- Brand covers / dividers (slides 1, 23, 44): generic seal_lockup vs Centurion/full-bleed art — brand-asset exclusion."
    )
    A(
        "- IR bullet density (slide 2) and FLS freeform packing (38–43): recipe weight, content complete."
    )
    A(
        "- Slide 18: exterior PDF YoY callout boxes vs in-plot boxed datalabels — shipped #151 contract met."
    )
    A(
        "- Slide 21: stack series color order / KPI microcopy vs PDF — composition contract met."
    )
    A(
        "- Slide 24: group bracket chrome vs PDF dashed multi-box callouts — three semantic brackets painted."
    )
    A(
        "- Slide 15: minor reserve-rate source value drift vs PDF — source/content, alignment geometry PASS."
    )
    A(
        "- Known layout alias `split_text_visual` → `freeform_grid` (29,30,38–43): not an identity break."
    )
    A("")
    A("### 5.4 Screenshot / probe failures")
    A("")
    A(
        "**None.** All 44 comparison rows `artifacts_exist=true`, paint_ready.ok where charts present, "
        "manifest warnings=0. Closed-ticket fails are assertion failures on handoff content, not capture failures."
    )
    A("")
    A("### 5.5 What renderer_v2 now does well")
    A("")
    A(
        "- Identity-safe, paint-ready Chart.js capture across a 44-slide IR deck, including dual-pane macros."
    )
    A(
        "- Outlined support-cell ↔ bar centre alignment at sub-pixel error with non-overlapping label lanes."
    )
    A("- Shared-column side callouts without badge/top_total duplication.")
    A(
        "- Auto typography on dual charts with HTML-owned pane titles (no Chart.js title-plugin fallback)."
    )
    A(
        "- chart_hero_dual compositions: driver cards, boxed bar labels, capital return stack+line+ROE+KPI."
    )
    A(
        "- Grouped bar brackets + aligned footer support rows with exact total copy."
    )
    A(
        "- Default gridline suppression while preserving axes, support borders, and semantic zero lines."
    )
    A(
        "- Annex tables with units, FX footnotes, and deck-unique grouped heading IDs."
    )
    A(
        "- JS-off/SVG parity on the closed-ticket geometry surface area exercised here."
    )
    A("")
    A("---")
    A("")
    A("## 6. Diagnostics & artifact index")
    A("")
    A("| Artifact | Path |")
    A("|----------|------|")
    A("| GAP (simulation) | `simulation/amex_q1_2026/GAP_ANALYSIS.md` |")
    A("| GAP (wiki copy) | `wiki/baseline_v11_GAP_ANALYSIS.md` |")
    A("| Handoff pre | `passes/pass_01/handoff.pre_mutations.json` |")
    A("| Handoff post | `passes/pass_01/handoff.json` |")
    A("| Handoff assertion | `handoff_assertion.json` |")
    A("| Page/slide map | `page_slide_mapping.json` |")
    A("| Rendered HTML | `passes/pass_01/output/presentation.html` |")
    A("| run_meta | `passes/pass_01/output/run_meta.json` |")
    A("| Comparison manifest | `comparison_manifest.json` |")
    A("| PDF rasters (44) | `comparison/pdf/` |")
    A("| HTML shots (44) | `comparison/html/` |")
    A("| SBS (44) | `comparison/sbs/` |")
    A("| Contact sheet | `comparison/contact_sheet.png` |")
    A("| Qualitative ledger JSON | `comparison/qualitative_ledger_v11.json` |")
    A("| Scorecard | `closed_tickets/scorecard_136_159.json` |")
    A("| Probe results | `closed_tickets/closed_ticket_results_v11.json` |")
    A("| Probe raw | `closed_tickets/closed_ticket_raw_v11.json` |")
    A("| Focused tests | `closed_tickets/focused_tests_summary.json` |")
    A(
        "| Probes | `probes/build_full_comparison.py`, `probes/v11_closed_ticket_probes.py` |"
    )
    A("| Prior v10 extract | `extracted/baseline_v10_GAP_ANALYSIS.md` |")
    A("")
    A(
        f"**run_meta:** generator={rm.get('generator')} v{rm.get('version')}; "
        f"style={rm.get('style_preset')}; total_slides={rm.get('total_slides')}; "
        f"html_bytes={rm.get('html_bytes')}; delivery={rm.get('delivery')}."
    )
    A("")
    A("---")
    A("")
    A("## 7. Stop proofs (pre-commit checklist)")
    A("")
    A("| Proof | Status |")
    A("|-------|--------|")
    A("| 44 PDF + 44 HTML + 44 SBS exist | HOLD |")
    A("| comparison_manifest all_artifacts_present | HOLD |")
    A("| #136–#159 scorecard rows with fresh evidence | HOLD |")
    A("| No MAE/similarity/pixel-diff scoring | HOLD |")
    A("| No production/test/script/config path changed | HOLD (observation run) |")
    A("| Report byte-identical sim ↔ wiki | enforced at docs commit |")
    A("| Exactly two allowed commits | sim artifacts, then wiki report |")
    A("")
    A(
        "*End of v11 observation baseline. Companion-mode only — no fixes, no tickets filed.*"
    )
    A("")

    text = "\n".join(L)
    out = BASE / "GAP_ANALYSIS.md"
    out.write_text(text, encoding="utf-8", newline="\n")
    print("wrote", out, "bytes", out.stat().st_size)

    ql = []
    for r in rows:
        n = r["slide_number"]
        cls, obs = ledger[n]
        ql.append(
            {
                "slide_number": n,
                "expected_layout": r["expected_layout"],
                "pdf_page_index": r["pdf_page_index"],
                "pdf_physical_page": r["pdf_physical_page"],
                "sbs_path": r["sbs_path"],
                "title": r.get("title"),
                "class": cls,
                "observation": obs,
            }
        )
    (BASE / "comparison" / "qualitative_ledger_v11.json").write_text(
        json.dumps(ql, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("ledger rows", len(ql))


if __name__ == "__main__":
    main()
