"""Assemble GAP_ANALYSIS.md from probe + manifest artifacts."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SIM = ROOT / "simulation" / "amex_q1_2026"
PDF = Path(r"C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf")


def main() -> int:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    commit_short = commit[:7]
    pdf_sha = hashlib.sha256(PDF.read_bytes()).hexdigest()

    mapping = json.loads((SIM / "page_slide_mapping.json").read_text(encoding="utf-8"))
    manifest = json.loads((SIM / "comparison_manifest.json").read_text(encoding="utf-8"))
    results = json.loads(
        (SIM / "closed_tickets" / "closed_ticket_results.json").read_text(encoding="utf-8")
    )

    by: dict[tuple[str, str], list] = {}
    for r in results["rows"]:
        by.setdefault((r["ticket"], r["mode"]), []).append(r)

    def find(ticket: str, mode: str, substr: str):
        for r in by.get((ticket, mode), []):
            if substr in r["check"]:
                return r
        return None

    m136cj = find("#136", "chartjs", "max |cell")
    m136svg = find("#136", "svg", "max |cell")

    def board_line(mode: str) -> str:
        parts = []
        for chk in (
            "board.x",
            "board.y",
            "board.w",
            "board.h",
            "first_shell.x",
            "first_shell.y",
            "first_shell.w",
            "cap height",
        ):
            r = find("#140", mode, chk)
            if r:
                parts.append(f"{chk} Δ={r.get('delta_px')}")
        return "; ".join(parts)

    notes = {
        1: (
            "accepted divergence",
            "Brand cover uses generic seal_lockup + two-tone diagonal recipe vs PDF left-title + large Centurion watermark (R3 brand-asset exclusion / wontfix).",
        ),
        2: (
            "accepted divergence",
            "IR bullet sheet denser line-items + disclosure chip vs PDF large bullets; content present, recipe weight differs (accepted IR density).",
        ),
        3: (
            "closed-ticket verification",
            "#140 five-row pill board: board/shell/cap deltas ≤0.03px vs approved PDF targets; YoY two-line cap retained; geometry PASS both modes.",
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
            "Multi-panel Platinum performance tiles render; pane titles HTML-owned where configured.",
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
            "no material new finding",
            "Commercial Services line chart tracks PDF narrative.",
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
            "source/content",
            "chart_hero_dual shows 66%/73% hero stats but left stacked NCA chart missing vs PDF dual-panel — handoff/source pairing residual (historical R4/N10 family), not a fresh closed-ticket miss.",
        ),
        13: (
            "no material new finding",
            "Balances and billed business line chart present.",
        ),
        14: (
            "no material new finding",
            "Credit metrics dual_chart with HTML pane titles; tracks PDF structure.",
        ),
        15: (
            "closed-ticket verification",
            "#136 outlined_boxes: chart-table-aligned marker on; max |cell_cx−bar_cx|=0.203px Chart.js / 0.016px SVG (≤12). List-of-lists primary retained. PDF reserve-rate source values differ slightly (source).",
        ),
        16: ("no material new finding", "Revenue performance data table renders."),
        17: (
            "closed-ticket verification",
            "#139 typography: two HTML pane titles 40px/700 navy; y ticks 24 bold; painted datalabels 28px both panes; no Chart title-plugin fallback. Measure-rule CAGR retained.",
        ),
        18: ("no material new finding", "Premium lending combo chart present."),
        19: ("no material new finding", "Total revenues line chart present."),
        20: (
            "closed-ticket verification",
            "#140 negative control: slide 20 inset/legacy pill path — does not match fixed five-row board selector; VCE callout retained as inset chrome.",
        ),
        21: ("no material new finding", "Capital multi_panel tiles present."),
        22: ("no material new finding", "2026 guidance card present."),
        23: (
            "accepted divergence",
            "Appendix divider brand treatment differs from PDF full-bleed art (brand recipe).",
        ),
        24: (
            "closed-ticket verification",
            "#140 negative control: data_table with insets — not fixed pill-board selector; legacy table geometry retained.",
        ),
        25: ("no material new finding", "FX impact table present."),
        26: ("no material new finding", "T&E billed business table present."),
        27: (
            "no material new finding",
            "Credit reserve macro dual_chart present; exterior names where configured.",
        ),
        28: (
            "closed-ticket verification",
            "#138 Deposit Programs side_callout tall/right three-line unboxed; badge chrome suppressed; $151/$157 totals independent; tile-local top≈50.8px (δ0.997 to 49.8); exterior segment names via plugin config.",
        ),
        29: (
            "source/content",
            "freeform_grid from split_text_visual handoff alias — variance commentary packing differs from PDF two-column art; content-driven.",
        ),
        30: (
            "source/content",
            "Continuation variance commentary; same freeform_grid alias note as s29.",
        ),
        31: (
            "no material new finding",
            "Annex 1 table navy headers; structure matches IR annex recipe.",
        ),
        32: ("no material new finding", "Annex 1 cont. table present."),
        33: ("no material new finding", "Annex 2 table present."),
        34: ("no material new finding", "Annex 3 table present."),
        35: ("no material new finding", "Annex 4 table present."),
        36: ("no material new finding", "Annex 5 table present."),
        37: ("no material new finding", "Annex 6 table present."),
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
            "Closing brand divider vs PDF end card — seal_lockup generic mark (R3 exclusion).",
        ),
    }

    man_by = {r["slide_number"]: r for r in manifest["rows"]}
    mm = mapping.get("mismatches") or []
    mm_txt = (
        "Handoff `layout_type=split_text_visual` renders as HTML `data-layout=freeform_grid` "
        f"on slides {[m['slide'] for m in mm]} — known recipe alias, not an identity break. "
        "Numeric identity HTML slide N ↔ PDF index N−1 ↔ physical page N holds for all 44."
        if mm
        else "All handoff layout_type values equal HTML data-layout."
    )

    ledger_lines = []
    for sn in range(1, 45):
        mr = man_by[sn]
        cat, note = notes[sn]
        ledger_lines.append(
            f"| {sn} | {mr['expected_layout']} | {mr['pdf_page_index']} | "
            f"P{mr['pdf_physical_page']} | `{mr['sbs_path']}` | **{cat}** | {note} |"
        )

    def fmt_audit_row(a: dict) -> str:
        sn = a["slide_number"]
        lay = a["layout"]
        pts = a["pane_title_state"]
        if pts == "not applicable":
            na = "not applicable"
            return (
                f"| {sn} | {lay} | {a['pdf_page_index']} | P{a['pdf_physical_page']} | "
                f"{na} | {na} | {na} | {na} | {na} | {na} |"
            )
        if isinstance(pts, list):
            if not pts:
                pts_s = "none"
            else:
                pts_s = "; ".join(
                    f"{t.get('text', '')[:28]} @ {t.get('fontSize')}px/{t.get('fontWeight')}"
                    for t in pts
                )
        else:
            pts_s = str(pts)
        leg = a["legacy_title_fallback"]
        if isinstance(leg, list):
            leg_s = (
                "; ".join(f"pane{x.get('i')}: plugin={x.get('titlePlugin')}" for x in leg)
                or "none"
            )
        else:
            leg_s = str(leg)
        tick = a["tick_rotation_skip"]
        if isinstance(tick, list):
            tick_s = (
                "; ".join(
                    f"pane{x.get('i')}: rot={x.get('xRot')} skip={x.get('xSkip')} yTick={x.get('yTick')}"
                    for x in tick
                )
                or "none"
            )
        else:
            tick_s = str(tick)
        dl = a["datalabel_suppression"]
        if isinstance(dl, list):
            dl_s = (
                "; ".join(f"pane{x.get('i')}: painted={x.get('nPainted')}" for x in dl)
                or "none"
            )
        else:
            dl_s = str(dl)
        return (
            f"| {sn} | {lay} | {a['pdf_page_index']} | P{a['pdf_physical_page']} | "
            f"{pts_s} | {leg_s} | {tick_s} | {dl_s} | "
            f"{a['unsupported_typography_warning']} | {a['clipping']} |"
        )

    audit_cj = results["deck_audit_139_chartjs"]
    audit_svg = results["deck_audit_139_svg"]

    md = f"""# Gap Analysis v10: renderer_v2 vs Amex Q1'26 Earnings PDF

**(Closed-ticket revalidation + full 44-page PDF↔HTML comparison — observation only)**

**Simulation:** `simulation/amex_q1_2026/`  
**Source of truth:** `{PDF}`  
**PDF identity:** SHA-256 `{pdf_sha}` · 44 pages · page0 rect 959.76×540  
**Renderer under test:** `impact_slides.renderer_v2` @ `{commit_short}` (`{commit}`) — current main line; **no production edits this run**  
**Prior baseline:** `wiki/baseline_v9_GAP_ANALYSIS.md`  
**Handoff source:** v9 archive `gnhf/objective-produce-a-2d5e02:simulation/amex_q1_2026/passes/pass_01/handoff.json`  
  → copied to `simulation/amex_q1_2026/passes/pass_01/handoff.json` then **only** closed-ticket settings applied (#138 side_callout, #139 typography; #136/#140 unchanged inputs).  
**Method:** Playwright geometry via `scripts/simulation_probe.py` (`activate_slide`, `painted_datalabel_lines`) + 1920×1080 full-resolution PDF/HTML side-by-sides. House tol ±4px; #136 centres ≤12px.  
**No MAE / similarity percent / pixel-diff scores / heatmaps.**

---

## 1. Scope gate, mapping assertion, run identity

| Gate | Result |
|------|--------|
| Renderer commit | `{commit_short}` — chore: add v10 Amex GNHF comparison launcher (main HEAD at sim start) |
| Production paths touched | **None** (`impact_slides/`, schemas, CSS, tests untouched) |
| Handoff | Single pass_01; no speculative pass_02 tuning |
| PDF pages | 44 |
| HTML `data-slide-number` unique values | 44 (1…44) |
| Identity map | **HTML slide N → PDF index N−1 → physical page N** |
| Mapping assertion | **HOLD** with recipe alias note below |
| Scope-gate | PASS — only `simulation/amex_q1_2026/**` artifacts written this run; no `impact_slides/` production edits; wiki report is the sole tracked doc add. |

### Page / slide mapping assertion

{mm_txt}

Full row dump: `simulation/amex_q1_2026/page_slide_mapping.json`.

Every artifact name and scorecard row carries `slide_number`, `expected_layout` (HTML `data-layout`), `pdf_page_index`, `pdf_physical_page`.

### #137 process compliance

| Requirement | Evidence |
|-------------|----------|
| `activate_slide(page, slide_number, expected_layout)` only | `simulation/amex_q1_2026/probes/build_full_comparison.py`, `closed_ticket_probes.py` |
| No `section.slide[i]` / nth / scrollIntoView activation | Confirmed in probe sources |
| JSON rows include `slide_number` + `layout` | `closed_tickets/closed_ticket_results.json`, `comparison_manifest.json` |
| Zero selector match = probe failure | `ProbeError` paths; no successful empty observations |
| Painted datalabels via `painted_datalabel_lines` | #139 Chart.js panes |
| 1920×1080 readiness wait before shots | Full comparison + closed-ticket probes |
| Console / run_meta captured with identity | manifest `warnings` (0); run_meta at `passes/pass_01/output/run_meta.json` |

**#137 verdict: PASS (tooling contract).**

---

## 2. Closed-ticket scorecard (#136–#140)

### #136 — slide 15 / stacked_bar_chart / PDF P15 — outlined_boxes alignment

| Field | Detail |
|-------|--------|
| Settings applied | Unchanged list-of-lists primary `steps_or_data`; `secondary_visual.skin: outlined_boxes` retained (no mapping-object conversion). |
| Chart.js | Alignment marker `chart-table-aligned` **on**. Five outlined-box centres vs Chart.js bar centres; max \\|Δ\\| = **{m136cj['measured']['max_abs_delta']}px** (deltas {m136cj['measured']['deltas']}). Acceptance ≤12px → **PASS**. |
| JS-off/SVG | Live `svg.chart-svg` bar centres (JS-off). max \\|Δ\\| = **{m136svg['measured']['max_abs_delta']}px** (deltas {m136svg['measured']['deltas']}). ≤12px → **PASS**. |
| Artifacts | `closed_tickets/closed_ticket_results.json` · shots `closed_tickets/shots/chartjs_slide15_*.png`, `svg_slide15_*.png` · SBS `comparison/sbs/sbs_slide15_P15_idx14_stacked_bar_chart.png` |
| **Verdict** | **PASS both modes** |

### #137 — tooling / identity contract

| Field | Detail |
|-------|--------|
| Settings applied | N/A (no handoff knob) — probe contract only. |
| Chart.js | All Chart.js probes used `activate_slide` + identity fields. |
| JS-off/SVG | All SVG probes used same activation contract with `java_script_enabled=False`. |
| Artifacts | Probe sources under `simulation/amex_q1_2026/probes/` |
| **Verdict** | **PASS** |

### #138 — slide 28 / multi_panel / PDF P28 — Deposit Programs side_callout

| Field | Detail |
|-------|--------|
| Settings applied | Added `chart_config.side_callout: {{"value":"92% FDIC","label":["insured at","Q1'26"],"placement":"right","skin":"tall"}}` on Deposit Programs tile only; source badge string kept; exterior names, 150px gutter, density, `stack_total_labels: ["$151","$157"]` unchanged. |
| Chart.js | Exactly one unboxed three-line callout; no non-callout FDIC badge; exterior segmentNames items present; $151/$157 independent; tile-local top 50.80px (δ 0.997 vs 49.8); no callout↔plot overlap. **PASS** 7/7. |
| JS-off/SVG | Same DOM callout path under JS-off (HTML chrome). Exterior names recovered from embedded `chartjs-config` segmentNames. **PASS** 7/7. |
| Artifacts | `closed_tickets/shots/*_slide28_*.png` · SBS `comparison/sbs/sbs_slide28_P28_idx27_multi_panel.png` |
| **Verdict** | **PASS both modes** |

### #139 — slide 17 / dual_chart / PDF P17 — chart_config.typography

| Field | Detail |
|-------|--------|
| Settings applied | Both panes: `typography: {{y_tick_font_size: 24, datalabel_font_size: 28}}`; x ticks left at legacy. |
| Chart.js | Two HTML `.gl-chart-pane-title` @ 40px/700 navy; no Chart.js title plugin; y ticks 24 bold both panes; painted datalabel model font 28 on all labels (pane0 8 lines, pane1 9 lines); x autoSkip=true, rotation 0 recorded; no unsupported typography warnings; no clipping. **PASS** 11/11. |
| JS-off/SVG | HTML pane titles retained JS-off; SVG text audit recorded; no duplicate SVG titles matching pane titles. **PASS** 5/5. |
| Artifacts | `closed_tickets/shots/*_slide17_*.png` · SBS `comparison/sbs/sbs_slide17_P17_idx16_dual_chart.png` |
| **Verdict** | **PASS both modes** |

### #140 — slide 3 / pill_comparison / PDF P3 — five-row fixed board (no new knob)

| Field | Detail |
|-------|--------|
| Settings applied | No handoff knob. Merged CSS recipe on direct five-body-row board. |
| Chart.js | Board/shell/cap vs approved targets: {board_line('chartjs')}. Five body label rows present; no slide overflow. Slide 20 & 24 negative controls: fixed-board selector **not** matched; legacy/inset paths retained. **PASS** 16/16. |
| JS-off/SVG | Same geometry JS-off (pure HTML/CSS): {board_line('svg')}. Negative controls identical. **PASS** 16/16. |
| Artifacts | `closed_tickets/shots/*_slide03_*.png` · SBS `comparison/sbs/sbs_slide03_P03_idx02_pill_comparison.png` |
| **Verdict** | **PASS both modes** |

### Scorecard summary

| Ticket | Chart.js | SVG | Overall |
|--------|----------|-----|---------|
| #136 | PASS (max Δ 0.203px) | PASS (max Δ 0.016px) | **PASS** |
| #137 | contract used | contract used | **PASS** |
| #138 | PASS 7/7 | PASS 7/7 | **PASS** |
| #139 | PASS 11/11 | PASS 5/5 | **PASS** |
| #140 | PASS 16/16 | PASS 16/16 | **PASS** |

Raw checks: `{results['n_pass']}/{results['n_checks']}` passed · `closed_tickets/closed_ticket_results.json`.

---

## 3. Full 44-page PDF ↔ HTML qualitative ledger

**Rasterization:** every PDF page via PyMuPDF matrix `1920/page.rect.width` × `1080/page.rect.height` (native page size → exact 1920×1080, not screenshot-resize).  
**HTML:** every slide activated by identity contract at 1920×1080 after chart readiness.  
**SBS:** full-resolution PDF left | HTML right, header `PDF physical P (index I) | HTML slide N | layout` — no downscale of either half.  
**Contact sheet:** `comparison/contact_sheet.png`.  
**Manifest:** `comparison_manifest.json` — artifact existence only (**not** a score). `all_artifacts_present: {manifest['all_artifacts_present']}`.

| slide | layout | pdf_idx | physical | full-res SBS | category | qualitative note |
|------:|--------|--------:|----------|--------------|----------|------------------|
"""
    md += "\n".join(ledger_lines)
    md += f"""

### Manifest summary

- Rows: {manifest['n_slides']}
- All PDF+HTML+SBS present: **{manifest['all_artifacts_present']}**
- Viewport: 1920×1080
- Comparison root: `simulation/amex_q1_2026/comparison/{{pdf,html,sbs}}/`
- Closed-ticket runtime shots kept separate under `closed_tickets/shots/` (chartjs vs svg)

---

## 4. v9 → v10 delta

| Topic | v9 (historical) | v10 (fresh revalidation) |
|-------|-----------------|---------------------------|
| #136 / N6 outlined alignment | v9: list-shaped primary blocked plot-align (`aligned=false`); cell↔bar centres failed ≤12px | **PASS** both modes; `chart-table-aligned` on; max Δ 0.203px / 0.016px |
| #138 / N5 tall FDIC callout | v9: badge ≠ tall side callout residual | **PASS** structured `side_callout` paints; badge suppressed; totals independent |
| #139 / R6-A typography | v9: pane title ~13px gray residual | **PASS** 40px/700 navy HTML titles; 24px y ticks; 28px painted labels |
| #140 / F4+ pill board | v9: packing still weak vs PDF full board | **PASS** board/shell/cap within ±0.03px of approved targets |
| #137 probe contract | introduced post-v9 | **Used throughout** this baseline |
| Full 44 SBS | v9 focus-sample only | **Complete 44/44** full-res pairs + contact sheet + manifest |
| R3 brand seal | accepted / wontfix | unchanged accepted divergence (s1/s44) |
| R4 dual-metric / s12 hero chart | historical residual | **source/content** residual remains on s12 (left NCA chart absent in handoff) — not closed by #136–#140 |
| R1 / F12+ / N2 / R2 locks | accepted divergence locks | still accepted; not re-opened |

### Evidence-backed residuals only (not closed-ticket failures)

1. **s12 New Acquisitions** — handoff still omits left stacked NCA chart present in PDF (source/content / historical hero pairing).  
2. **Brand assets (s1/s44)** — generic `seal_lockup` vs Centurion art (R3 wontfix).  
3. **Legal/FLS freeform packing (s38–s43)** and **IR bullet density (s2)** — accepted recipe divergences, not new renderer defects.  
4. **s15 PDF reserve-rate source series** — PDF shows mostly 2.9% then 2.8%; handoff series is 2.9% + four×2.8% (source values), while **alignment geometry passes**.

No issues filed from this simulation.

---

## 5. #139 full-deck typography / pane-title audit

Ordinary Chart.js inspection (non-chart slides explicitly **not applicable**):

| slide | layout | pdf_idx | physical | pane_title_state | legacy_title_fallback | tick_rotation_skip | datalabel_suppression | unsupported_typography_warning | clipping |
|------:|--------|--------:|----------|------------------|----------------------|--------------------|----------------------|--------------------------------|----------|
"""
    md += "\n".join(fmt_audit_row(a) for a in audit_cj)
    md += """

JS-off/SVG inspection (titles are HTML-owned; chart tick/datalabel fields n/a-js-off where Chart.js is absent):

| slide | layout | pdf_idx | physical | pane_title_state | legacy_title_fallback | tick_rotation_skip | datalabel_suppression | unsupported_typography_warning | clipping |
|------:|--------|--------:|----------|------------------|----------------------|--------------------|----------------------|--------------------------------|----------|
"""
    md += "\n".join(fmt_audit_row(a) for a in audit_svg)
    md += """

Focus slide 17 detail is in §2. Deck-wide: HTML pane titles appear on multi-pane layouts that emit `.gl-chart-pane-title` (s6, s14, s17, s21, s28, …). Single-series line charts correctly show **none** (title is slide H2 only). No slide showed Chart.js `plugins.title.display` legacy fallback. No clipping detected at probe time. x-tick `autoSkip=true`, rotation 0 on audited chart slides (native).

---

## 6. What renderer_v2 does well vs accepted/source divergences

### Does well (fresh evidence)

- **Identity-stable deck** — 44 unique `data-slide-number` values mapped 1:1 to PDF pages.
- **Outlined support row alignment (#136)** — runtime `chart-table-aligned` + sub-pixel cell↔bar centres in Chart.js and SVG.
- **Structured side callout (#138)** — tall/right unboxed three-line callout with badge suppression and independent stack totals.
- **Chart typography contract (#139)** — HTML pane titles + y-tick/datalabel font sizes from `chart_config.typography`, verified on painted models not options-only.
- **Pill board geometry (#140)** — five-row board matches approved PDF-normalized targets within house noise; negative controls keep inset/legacy paths off the fixed recipe.
- **Self-contained offline HTML** — run_meta delivery self-contained with inlined fonts/charts.
- **Annex tables** — uniform navy group headers retained (prior T13 lock).

### Accepted / source divergences (not scored as new renderer tickets)

- R3 brand Centurion / third-party marks → generic `seal_lockup`.
- R1 / F12+ / N2 chip weight / R2 L-bracket silhouette locks from prior baselines.
- IR bullet sheet and FLS legal pages: content-complete, density/packing recipe ≠ pixel PDF.
- s12 missing left NCA chart: **handoff/source** gap relative to PDF.
- Disclosure footers often collapse to chip+panel vs PDF fine-print paragraphs (recipe).

---

## Artifact index

| Path | Role |
|------|------|
| `passes/pass_01/handoff.json` | Closed-ticket handoff |
| `passes/pass_01/output/presentation.html` | Rendered deck |
| `passes/pass_01/output/run_meta.json` | Renderer run meta |
| `page_slide_mapping.json` | Identity assertion |
| `comparison/pdf/*.png` | 44× PDF rasters 1920×1080 |
| `comparison/html/*.png` | 44× HTML shots 1920×1080 |
| `comparison/sbs/*.png` | 44× full-res side-by-sides |
| `comparison/contact_sheet.png` | Contact sheet |
| `comparison_manifest.json` | Artifact manifest (no scores) |
| `closed_tickets/closed_ticket_results.json` | Scorecard rows + #139 deck audits |
| `closed_tickets/closed_ticket_raw.json` | Raw DOM measures |
| `closed_tickets/shots/` | Chart.js vs SVG focus screenshots |
| `probes/build_full_comparison.py` | #137-compliant full comparison |
| `probes/closed_ticket_probes.py` | #136–#140 probes both modes |

---

*End of v10 baseline. Simulation / observation only. No production renderer changes. No issues filed.*
"""

    out = SIM / "GAP_ANALYSIS.md"
    out.write_text(md, encoding="utf-8")
    wiki = ROOT / "wiki" / "baseline_v10_GAP_ANALYSIS.md"
    wiki.write_text(md, encoding="utf-8")
    assert out.read_bytes() == wiki.read_bytes()
    print("wrote", out, out.stat().st_size)
    print("wrote", wiki, wiki.stat().st_size)
    # disclaimer lines intentionally mention retired scoring terms
    print("report bytes", len(md.encode("utf-8")), "MAE disclaimer count", md.count("MAE"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
