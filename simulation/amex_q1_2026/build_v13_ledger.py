"""Build v13 qualitative ledger JSON from comparison_manifest + fresh SBS review."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

SIM = Path(__file__).resolve().parent
m = json.loads((SIM / "comparison_manifest.json").read_text(encoding="utf-8"))
layouts = {int(k): v for k, v in m["layouts"].items()}
dled_by = {d["slide_number"]: d for d in m["design_ledgers"]}
CHART = {"single_chart", "dual_chart", "chart_hero_dual"}

# Fresh SBS observations (no image scores). One class per slide.
OBS: dict[int, tuple[str, str]] = {
    1: (
        "accepted v3 design divergence",
        "PDF full-bleed navy/cyan brand cover with Centurion seal. v3 minimal white title "
        "(title + Q1'26 + April 23, 2026). Brand-seal omission is standing R3 wontfix; "
        "cover recipe intentional.",
    ),
    2: (
        "faithful reproduction",
        "Seven Business Highlights bullets match PDF substance and bold emphasis. Packing "
        "tighter/smaller type than PDF; footnote collapses to notes affordance. Content-complete.",
    ),
    3: (
        "accepted v3 design divergence",
        "All five KPI rows/values match. PDF uses large period pills; v3 compact right-hand "
        "matrix — schema-v1 period_comparison recipe, not a value error.",
    ),
    4: (
        "faithful reproduction",
        "Dual FX-adj + Reported lines with endpoint labels 9%/10%. Leap Year Approx. (1%) "
        "annotation and bottom G&S/T&E support table both present (v12 residual resolved). "
        "Minor axis tick density vs PDF only.",
    ),
    5: (
        "faithful reproduction",
        "UCS billings line 7→10% paints. Generation-mix support table (Gen-Z…) present "
        "(v12 residual resolved). Side G&S/T&E callout styling differs slightly from PDF "
        "but content present via support.",
    ),
    6: (
        "faithful reproduction",
        "Both panes paint with titles. '+ ~6 percentage points' annotation present "
        "(v12 residual resolved). PDF 'Refresh' chip under spend bars still absent — minor "
        "chrome gap, not content loss. Retention y-window readable.",
    ),
    7: (
        "accepted v3 design divergence",
        "v13 paints circular dual-metric cards with 10x/2x multipliers (v12 was plain text "
        "columns). Values 50/5, 20/10, 21/11 present. Left/right premium-vs-benchmark "
        "orientation and card scale still differ from PDF art; no longer a missing-capability blank.",
    ),
    8: (
        "faithful reproduction",
        "Dual lodging lines (FHR+THC 40→50%, UCS 5%) paint. Metric strip 3,400+ / 300+ / "
        "$600 / $550 present (v12 residual resolved). PDF vertical 10x callout between "
        "lines still absent — accepted chrome difference.",
    ),
    9: (
        "faithful reproduction",
        "Commercial FX-adj line paints. Support table with U.S. SME present "
        "(v12 residual resolved).",
    ),
    10: (
        "faithful reproduction",
        "ICS dual line paints with markers. Support table Intl Consumer present "
        "(v12 residual resolved).",
    ),
    11: (
        "faithful reproduction",
        "Series 9/9/10/9/10 on fixed 0–15% domain — v12 false-V domain collapse resolved. "
        "Leap Year box present on PDF only; line geometry now matches PDF frame.",
    ),
    12: (
        "faithful reproduction",
        "Three-band stacked NCA bars (UCS/Commercial/ICS totaling ~3.x) paint with segment "
        "legend (v12 single-series residual resolved). Hero 66%/73% shares present. Hero "
        "copy shorter than PDF long sentences — accepted v3 hero recipe.",
    ),
    13: (
        "faithful reproduction",
        "Grouped Total Balances vs Billed Business bars and labels match PDF structure/values "
        "through Q1'26.",
    ),
    14: (
        "faithful reproduction",
        "30+ DPD ~1.3% and Net Write-off panes paint with correct labels; dual-card chrome "
        "is v3 recipe.",
    ),
    15: (
        "corpus/extraction residual",
        "Stacked write-offs + reserve build/release geometry paints; Reserve Rate outlined "
        "row present (v12 furniture residual resolved). Remaining: mid-quarter reserve-rate "
        "cells show 2.8% for Q2–Q4 vs PDF 2.9%/2.9%/2.9%/2.9%/2.8%; series color recipe "
        "inverted vs PDF (write-offs dark vs light).",
    ),
    16: (
        "accepted v3 design divergence",
        "All revenue line items and YoY/FX columns match. PDF pill columns vs v3 dense data "
        "grid is table recipe difference.",
    ),
    17: (
        "faithful reproduction",
        "Both panes paint. Left Net Card Fees bars correctly labeled $0.9…$2.8 (v12 pct_0 "
        "mislabel resolved). 17% CAGR measurement chrome present. Right FX YoY line matches. "
        "Qualification disclosure collapsed to notes affordance.",
    ),
    18: (
        "faithful reproduction",
        "NII bars $4.2…$4.7 with under-bar YoY boxed labels 11–12%. Driver card rows Billed "
        "Business 8% / NII 13% / Volume 7% / Margin 5% present (v12 residual resolved). "
        "Driver chrome is list not green-arrow table — accepted recipe.",
    ),
    19: (
        "faithful reproduction",
        "Dual revenue line paints. Leap Year annotation and $B support row $17.0…$18.9 "
        "present (v12 residual resolved).",
    ),
    20: (
        "accepted v3 design divergence",
        "Expense values match incl. VCE. Nested indent flattened vs PDF hierarchy — recipe "
        "difference with matching numbers.",
    ),
    21: (
        "faithful reproduction",
        "Capital stacked combo with Common Shares Outstanding line 702→682 and ROE row "
        "35/34/36/36/34/35% present (v12 residual resolved). Right Capital Summary KPIs match.",
    ),
    22: (
        "accepted v3 design divergence",
        "Guidance figures present; sparse list vs centered PDF card is metric_overview recipe.",
    ),
    23: (
        "accepted v3 design divergence",
        "Appendix title; white plate vs navy brand divider — intentional v3 section_divider.",
    ),
    24: (
        "faithful reproduction",
        "Six growth bars with category-group braces (UCS/Commercial/ICS), $486B Total Network "
        "Volumes annotation, and on-bar %-of-total boxed labels present (v12 residual resolved).",
    ),
    25: (
        "faithful reproduction",
        "FX currency rows and YoY match PDF.",
    ),
    26: (
        "faithful reproduction",
        "T&E matrix orientation and values match PDF.",
    ),
    27: (
        "faithful reproduction",
        "Unemployment+GDP scenario fans paint-ready and track PDF.",
    ),
    28: (
        "faithful reproduction",
        "Funding/deposit stacks paint with on-stack % and $ totals. 92% FDIC annotation "
        "present (v12 residual resolved).",
    ),
    29: (
        "faithful reproduction",
        "Variance commentary matches PDF substance.",
    ),
    30: (
        "faithful reproduction",
        "Continuation commentary matches PDF substance.",
    ),
    31: (
        "accepted v3 design divergence",
        "Annex1 values present; nested groups flattened to metric names vs PDF grouping chrome.",
    ),
    32: (
        "faithful reproduction",
        "Two peer groups with correct numbers. Column headers fully readable "
        "(Q1'26 Reported / FX-Adj.*) — v12 header-clip residual resolved.",
    ),
    33: (
        "faithful reproduction",
        "Annex2 balances grid matches.",
    ),
    34: (
        "faithful reproduction",
        "Annex3 revenue grid populated.",
    ),
    35: (
        "faithful reproduction",
        "Annex4 NCF grid populated.",
    ),
    36: (
        "faithful reproduction",
        "Annex5 NII grid populated.",
    ),
    37: (
        "faithful reproduction",
        "Annex6 RNIE grid populated.",
    ),
    38: (
        "candidate renderer defect or capability gap",
        "Full cautionary text present as dense continuous bullets; PDF multi-paragraph "
        "hierarchy/spacing largely collapsed. Same legal_notice packing class as v12 (R-D preserved).",
    ),
    39: (
        "candidate renderer defect or capability gap",
        "Continuation of legal packing class (dense wall vs PDF hierarchy).",
    ),
    40: (
        "candidate renderer defect or capability gap",
        "Same legal_notice packing class.",
    ),
    41: (
        "candidate renderer defect or capability gap",
        "Same legal_notice packing class.",
    ),
    42: (
        "candidate renderer defect or capability gap",
        "Same legal_notice packing class.",
    ),
    43: (
        "candidate renderer defect or capability gap",
        "Same legal_notice packing class.",
    ),
    44: (
        "accepted v3 design divergence",
        "PDF navy wordmark cover vs v3 minimal white lockup — accepted cover recipe.",
    ),
}


def main() -> None:
    rows = []
    for sn in range(1, 45):
        layout = layouts[sn]
        cls, observation = OBS[sn]
        d = dled_by[sn]
        d_ok = bool(d.get("ok"))
        if d_ok and layout in CHART:
            observation = observation.rstrip(".") + ". **design-parity verified**."
        rows.append(
            {
                "slide_number": sn,
                "layout_type": layout,
                "pdf_index": sn - 1,
                "physical_page": sn,
                "sbs": f"side_by_side/slide_{sn:02d}.png",
                "pdf_path": f"pdf_pages/slide_{sn:02d}.png",
                "html_path": f"html_slides/slide_{sn:02d}.png",
                "class": cls,
                "observation": observation,
                "design_ledger_ok": d_ok,
                "design_ledger": {
                    "ok": d_ok,
                    "tick_count": d.get("tick_count"),
                    "min_font_size_px": d.get("min_font_size_px"),
                    "min_font_weight": d.get("min_font_weight"),
                    "furniture": d.get("furniture") or [],
                },
            }
        )

    ledger = {
        "baseline": "v13",
        "renderer_version": m["renderer_version"],
        "repository_commit": m["repository_commit"],
        "run_meta_status": m["run_meta_status"],
        "slide_count": 44,
        "class_counts": dict(Counter(r["class"] for r in rows)),
        "rows": rows,
    }
    out = SIM / "qualitative_ledger_v13.json"
    out.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    print(json.dumps(ledger["class_counts"], indent=2))
    print("design_ok", sum(1 for r in rows if r["design_ledger_ok"]), "/ 44")
    print("wrote", out)


if __name__ == "__main__":
    main()
