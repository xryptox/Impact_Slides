"""Author pass_01 handoff against CURRENT renderer_v2 (post F-feature work).

Starts from the v1 pass_03 content baseline (already content-complete after
handoff tuning) and remaps slides onto new first-class layouts / chart_config
keys that did not exist in the pre-fix snapshot:

  F4  pill_comparison          summary + expense tables
  F5  chart_hero_dual          new acquisitions
  F6  brand_cover / brand_divider  cover, appendix, trailing
  F7  ir_bullet_sheet          highlights (+ selective **bold**)
  F8  guidance_statement_card  2026 guidance
  F9  key_stats inset          already on expense via pill path
  F10 y_axis_break             platinum retention panel
  F11 multi_panel              capital + platinum dual board
  F12 annex_table              dense annex grids
  F13 presentation.theme       keep Amex token map
  F14 chrome_level=minimal     IR parity hygiene
  F1/F2/F15 line chart_config  force_ticks + annotation kept
  F3  negative stack values    true negatives kept on provision

This is the AFTER baseline: every F1–F15 claim will be verified visually.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # simulation/amex_q1_2026
OUT = Path(__file__).resolve().parent / "handoff.json"
# Prefer local extracted baseline of content from v1 pass_03 handoff
V1_HANDOFF = (
    Path(__file__).resolve().parents[3]
    / "amex_q1_2026_v1_pre_fixes"
    / "passes"
    / "pass_03"
    / "handoff.json"
)

# Simple centurion-ish geometric seal (generic brand_mark_svg; not trademark art)
BRAND_MARK_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">'
    '<circle cx="60" cy="60" r="54" fill="none" stroke="#FFFFFF" stroke-width="4"/>'
    '<circle cx="60" cy="60" r="40" fill="none" stroke="#FFFFFF" stroke-width="2"/>'
    '<polygon points="60,22 72,48 100,52 80,72 86,100 60,86 34,100 40,72 20,52 48,48" '
    'fill="#FFFFFF" fill-opacity="0.95"/>'
    "</svg>"
)

THEME = {
    "--color-bg": "#ffffff",
    "--color-surface": "#ffffff",
    "--color-ink": "#001B4D",
    "--color-ink-muted": "#3A4A6B",
    "--color-accent": "#006FCF",
    "--color-accent-2": "#00175A",
    "--color-border": "#E0E3EB",
    "--color-stage-bg": "#00175A",
    "--color-primary": "#00175A",
    "--navy": "#00175A",
}


def _ensure_slide_numbers(slides: list[dict]) -> None:
    for i, s in enumerate(slides):
        s["slide_number"] = i + 1


def _boldify_highlights(bullets: list[str]) -> list[str]:
    """Selective **bold** on partner/product phrases for ir_bullet_sheet."""
    phrases = [
        "Official Payments Partner of the NFL",
        "multi-year partnership extension with the NBA",
        "American Express Graphite Business Cash Unlimited Card",
        "Amex Agentic Commerce Experiences",
        "Amex Agent Purchase Protection",
        "Resy dining platform",
        "Resy and Tock",
        "Las Vegas Sidecar",
        "New Delhi Centurion Lounge",
        "Great Place to Work 2026",
        "revenue growth of 11%",
        "EPS of $4.28",
    ]
    out = []
    for b in bullets:
        nb = b
        for p in phrases:
            if p in nb and f"**{p}**" not in nb:
                nb = nb.replace(p, f"**{p}**", 1)
        out.append(nb)
    return out


def transform(slides: list[dict]) -> list[dict]:
    s = deepcopy(slides)
    assert len(s) == 44

    # ---- 00 cover → title_or_opening ----
    # renderer load.normalize_handoff FORCES slide 1 to title_or_opening and will
    # INSERT an extra cover when layout_type != title_or_opening, shifting all
    # indices vs the 44-page PDF. Keep slide 1 as title_or_opening for 1:1 page
    # alignment; exercise brand_cover budget on the appendix divider (F6) instead.
    s[0] = {
        "slide_number": 1,
        "layout_type": "title_or_opening",
        "packing_mode": "cover-led",
        "title": "American Express Earnings Conference Call",
        "section": "Cover",
        "content": {
            "headline": "American Express Earnings Conference Call",
            "subtitle": "Q1'26  \u00b7  APRIL 23, 2026",
            # brand_mark_svg is accepted only by brand_cover recipe; noted as B-path:
            # handoff cannot paint a seal on title_or_opening without forced remap.
            "brand_mark_svg": BRAND_MARK_SVG,
            "brand_tone": "two-tone",
            "bullets": [],
            "key_stats": [],
            "so_what": "",
        },
        "speaker_notes": (
            "v2 pass_01: title_or_opening forced by load path; brand seal on cover "
            "requires brand_cover which gets remapped/inserted (F6 load interaction)."
        ),
    }

    # ---- 01 Business Highlights → ir_bullet_sheet (F7) ----
    bh = s[1]
    bullets = list((bh.get("content") or {}).get("bullets") or [])
    s[1] = {
        "slide_number": 2,
        "layout_type": "ir_bullet_sheet",
        "packing_mode": "argument-led",
        "title": "Business Highlights",
        "section": "Highlights",
        "content": {
            "headline": "Business Highlights",
            "subtitle": "",
            "bullets": _boldify_highlights(bullets),
            "key_stats": [],
            "so_what": "",
        },
        "disclosure": bh.get("disclosure"),
        "speaker_notes": "v2 pass_01: ir_bullet_sheet with selective **bold** (F7).",
    }

    # ---- 02 Summary Financial Performance → pill_comparison (F4) ----
    fin = s[2]
    frows = ((fin.get("visual_spec") or {}).get("primary_visual") or {}).get("steps_or_data")
    s[2] = {
        "slide_number": 3,
        "layout_type": "pill_comparison",
        "packing_mode": "stat-led",
        "title": "Summary Financial Performance",
        "section": "Financials",
        "content": {
            "subtitle": (fin.get("content") or {}).get("subtitle") or "",
            "so_what": "",
            "key_stats": [],
        },
        "visual_spec": {
            "primary_visual": {
                "type": "pill_comparison",
                "steps_or_data": frows,
            }
        },
        "disclosure": fin.get("disclosure"),
        "speaker_notes": "v2 pass_01: pill_comparison layout (F4).",
    }

    # ---- 03 Total Billed Business line — enrich chart_config (F1/F2/F15) ----
    bill = s[3]
    pv = (bill.get("visual_spec") or {}).get("primary_visual") or {}
    cfg = dict(pv.get("chart_config") or {})
    cfg.update(
        {
            "force_ticks": True,
            "show_point_labels": True,
            "point_labels": True,
            "y_axis_min": 0,
            "y_axis_max": 15,
            "y_axis_ticks": [0, 5, 10, 15],
            "y_axis_unit": "%",
            "y_axis_label": "%",
            "gridlines": True,
            "annotation": {
                "text": "Leap Year Approx. (1%)",
                "x": 420,
                "y": 90,
            },
            "series_names": cfg.get("series_names") or ["FX-adjusted", "Reported"],
            "series_styles": cfg.get("series_styles") or ["solid", "dashed"],
            "series_colors": cfg.get("series_colors") or ["#00175A", "#8A93A6"],
        }
    )
    pv = {**pv, "chart_config": cfg}
    bill["visual_spec"] = {**(bill.get("visual_spec") or {}), "primary_visual": pv}
    bill["speaker_notes"] = (
        "v2 pass_01: force_ticks + annotation + dashed series for Chart.js parity (F1/F2/F15)."
    )
    s[3] = bill

    # ---- 05 Platinum → multi_panel + y_axis_break on retention (F10/F11) ----
    plat = s[5]
    pvs = plat.get("visual_spec") or {}
    p_pv = pvs.get("primary_visual") or {}
    p_sv = pvs.get("secondary_visual") or {}
    # Retention series (was secondary) gets broken axis 0→90
    ret_cfg = dict((p_sv.get("chart_config") or {}))
    ret_cfg.update(
        {
            "y_axis_break": {"from": 0, "to": 90},
            "y_axis_min": 0,
            "y_axis_max": 100,
            "y_axis_ticks": [90, 92, 94, 96, 98, 100],
            "force_ticks": True,
            "y_axis_unit": "%",
            "series_names": ret_cfg.get("series_names")
            or ["Pre-refresh", "Post-refresh"],
        }
    )
    spend_cfg = dict((p_pv.get("chart_config") or {}))
    spend_cfg.update(
        {
            "y_axis_min": 0,
            "y_axis_max": 15,
            "y_axis_ticks": [0, 5, 10, 15],
            "force_ticks": True,
            "y_axis_unit": "%",
            "series_names": spend_cfg.get("series_names") or ["Spend growth"],
        }
    )
    s[5] = {
        "slide_number": 6,
        "layout_type": "multi_panel",
        "packing_mode": "chart-led",
        "title": plat.get("title") or "U.S. Consumer Platinum Performance",
        "section": plat.get("section") or "US Consumer",
        "content": {
            "subtitle": (plat.get("content") or {}).get("subtitle") or "",
            "so_what": "",
            "key_stats": (plat.get("content") or {}).get("key_stats") or [],
        },
        "visual_spec": {
            "primary_visual": {
                "type": "multi_panel",
                "tiles": [
                    {
                        "kind": "chart",
                        "chart_type": "line_chart",
                        "label": "Spend Growth",
                        "steps_or_data": p_pv.get("steps_or_data") or [],
                        "chart_config": spend_cfg,
                    },
                    {
                        "kind": "chart",
                        "chart_type": "line_chart",
                        "label": "Retention Rates",
                        "steps_or_data": p_sv.get("steps_or_data") or [],
                        "chart_config": ret_cfg,
                    },
                    {
                        "kind": "metric",
                        "label": "Retention lift callout",
                        "value": "+~6 pp",
                    },
                ],
            }
        },
        "speaker_notes": "v2 pass_01: multi_panel + y_axis_break on retention (F10/F11).",
    }

    # ---- 11 New Acquisitions → chart_hero_dual (F5) ----
    acq = s[11]
    a_pv = (acq.get("visual_spec") or {}).get("primary_visual") or {}
    # PDF order in test fixture: Millennial/Gen-Z 66% then Fee-Paying 73% — keep deck values
    stats = list((acq.get("content") or {}).get("key_stats") or [])
    # Prefer fee-paying 66% / millennial 73% as in source handoff labels
    s[11] = {
        "slide_number": 12,
        "layout_type": "chart_hero_dual",
        "packing_mode": "chart-led",
        "title": acq.get("title") or "New Acquisitions",
        "section": acq.get("section") or "Acquisitions",
        "content": {
            "subtitle": (acq.get("content") or {}).get("subtitle") or "",
            "so_what": "",
            "key_stats": stats,
        },
        "visual_spec": {
            "primary_visual": {
                "type": a_pv.get("type") or "stacked_bar_chart",
                "steps_or_data": a_pv.get("steps_or_data") or [],
                "chart_config": a_pv.get("chart_config") or {},
            }
        },
        "disclosure": acq.get("disclosure"),
        "speaker_notes": "v2 pass_01: chart_hero_dual chart|hero peers (F5).",
    }

    # ---- 14 Total Provision — keep negatives; ensure stack config (F3) ----
    prov = s[14]
    ppv = (prov.get("visual_spec") or {}).get("primary_visual") or {}
    pcfg = dict(ppv.get("chart_config") or {})
    pcfg.update(
        {
            "allow_negative": True,
            "stacked": True,
            "series_names": pcfg.get("series_names")
            or ["Write-offs", "Reserve Build/(Release)"],
            "series_colors": pcfg.get("series_colors") or ["#00175A", "#006FCF"],
        }
    )
    prov["visual_spec"] = {
        **(prov.get("visual_spec") or {}),
        "primary_visual": {**ppv, "chart_config": pcfg},
    }
    prov["speaker_notes"] = (
        "v2 pass_01: true-negative reserve release values; verify below-axis geometry (F3)."
    )
    s[14] = prov

    # ---- 19 Expense Performance → pill_comparison + VCE key_stats inset (F4/F9) ----
    exp = s[19]
    erows = ((exp.get("visual_spec") or {}).get("primary_visual") or {}).get("steps_or_data")
    estat = list((exp.get("content") or {}).get("key_stats") or [])
    if not estat:
        estat = [{"label": "VCE of Revenue", "value": "44.7%"}]
    s[19] = {
        "slide_number": 20,
        "layout_type": "pill_comparison",
        "packing_mode": "stat-led",
        "title": exp.get("title") or "Expense Performance",
        "section": exp.get("section") or "Expenses",
        "content": {
            "subtitle": (exp.get("content") or {}).get("subtitle") or "$ in millions",
            "so_what": "",
            "key_stats": estat,
        },
        "visual_spec": {
            "primary_visual": {
                "type": "pill_comparison",
                "steps_or_data": erows,
            }
        },
        "disclosure": exp.get("disclosure"),
        "speaker_notes": "v2 pass_01: pill_comparison + key_stats VCE inset (F4/F9).",
    }

    # ---- 20 Capital → multi_panel (F11) ----
    cap = s[20]
    cstats = list((cap.get("content") or {}).get("key_stats") or [])
    c_pv = (cap.get("visual_spec") or {}).get("primary_visual") or {}
    # Build tiles from available metrics + any chart
    tiles = []
    if c_pv.get("type") and c_pv.get("steps_or_data"):
        tiles.append(
            {
                "kind": "chart",
                "chart_type": c_pv.get("type") or "stacked_bar_chart",
                "label": "Capital composition",
                "steps_or_data": c_pv.get("steps_or_data") or [],
                "chart_config": c_pv.get("chart_config") or {},
            }
        )
    for st in cstats:
        if isinstance(st, dict):
            tiles.append(
                {
                    "kind": "metric",
                    "label": st.get("label") or st.get("name") or "",
                    "value": st.get("value") or st.get("stat") or "",
                }
            )
    if len(tiles) < 2:
        # fallback keep metric_dashboard
        pass
    else:
        s[20] = {
            "slide_number": 21,
            "layout_type": "multi_panel",
            "packing_mode": "stat-led",
            "title": cap.get("title") or "Capital",
            "section": cap.get("section") or "Capital",
            "content": {
                "subtitle": (cap.get("content") or {}).get("subtitle") or "",
                "so_what": "",
                "key_stats": cstats,
            },
            "visual_spec": {
                "primary_visual": {"type": "multi_panel", "tiles": tiles[:6]}
            },
            "speaker_notes": "v2 pass_01: multi_panel capital board (F11).",
        }

    # ---- 21 Guidance → guidance_statement_card (F8) ----
    guid = s[21]
    gstats = list((guid.get("content") or {}).get("key_stats") or [])
    gbullets = list((guid.get("content") or {}).get("bullets") or [])
    if not gbullets:
        gbullets = [
            "Subject to the macroeconomic environment and other factors beyond the Company's control."
        ]
    s[21] = {
        "slide_number": 22,
        "layout_type": "guidance_statement_card",
        "packing_mode": "stat-led",
        "title": guid.get("title") or "2026 Guidance",
        "section": guid.get("section") or "Guidance",
        "content": {
            "subtitle": "Full-Year 2026 Guidance",
            "key_stats": gstats
            or [
                {
                    "label": "FX-adjusted billed business growth",
                    "value": "~10–12%",
                },
                {"label": "Diluted EPS", "value": "≥ $18"},
            ],
            "bullets": gbullets[:3],
            "so_what": "",
        },
        "speaker_notes": "v2 pass_01: guidance_statement_card (F8).",
    }

    # ---- 22 Appendix divider → brand_divider (F6) ----
    s[22] = {
        "slide_number": 23,
        "layout_type": "brand_divider",
        "packing_mode": "cover-led",
        "title": "Appendix",
        "section": "Appendix",
        "content": {
            "subtitle": "Supplemental Information",
            "brand_mark_svg": BRAND_MARK_SVG,
            "brand_tone": "two-tone",
        },
        "speaker_notes": "v2 pass_01: brand_divider appendix opener (F6).",
    }

    # ---- 30–36 annex tables → annex_table (F12) where data_table ----
    for idx in range(30, 37):
        if idx >= len(s):
            break
        sl = s[idx]
        if sl.get("layout_type") not in ("data_table", "table", "annex_table"):
            continue
        rows = ((sl.get("visual_spec") or {}).get("primary_visual") or {}).get(
            "steps_or_data"
        )
        if not rows:
            continue
        sl = deepcopy(sl)
        sl["layout_type"] = "annex_table"
        pv = (sl.get("visual_spec") or {}).get("primary_visual") or {}
        pv = {**pv, "type": "annex_table"}
        # heuristic multi-level groups if many columns
        head = rows[0] if rows else []
        if len(head) >= 6:
            # split remaining cols into two groups
            data_cols = len(head) - 1
            g1 = max(1, data_cols // 2)
            g2 = data_cols - g1
            pv["header_groups"] = [
                {"label": "Prior / Reported", "span": g1},
                {"label": "Current / FX-Adj", "span": g2},
            ]
        sl["visual_spec"] = {
            **(sl.get("visual_spec") or {}),
            "primary_visual": pv,
        }
        sl["speaker_notes"] = (
            (sl.get("speaker_notes") or "")
            + " | v2 pass_01: annex_table density (F12)."
        ).strip(" |")
        s[idx] = sl

    # ---- 43 trailing → brand_divider (F6) ----
    s[43] = {
        "slide_number": 44,
        "layout_type": "brand_divider",
        "packing_mode": "cover-led",
        "title": "American Express",
        "section": "End",
        "content": {
            "subtitle": "Q1'26 Earnings",
            "brand_mark_svg": BRAND_MARK_SVG,
            "brand_tone": "two-tone",
        },
        "speaker_notes": "v2 pass_01: trailing brand plate (F6).",
    }

    _ensure_slide_numbers(s)
    return s


def main() -> None:
    src = json.loads(V1_HANDOFF.read_text(encoding="utf-8"))
    slides = transform(src["slides"])
    assert len(slides) == 44, len(slides)
    handoff = {
        "presentation": {
            "title": "American Express Earnings Conference Call Q1'26",
            "subtitle": "Simulation handoff · v2 pass_01 · post F-feature surface",
            "audience": "Investors / IR",
            "primary_goal": (
                "Exercise new IR layouts (brand/pill/hero/guidance/multi_panel/annex) "
                "and chart_config parity against current renderer_v2"
            ),
            "readiness_score": 70,
            "quality_flags": ["simulation", "amex_q1_2026", "pass_01", "v2_post_fixes"],
            "theme": THEME,
            "chrome_level": "minimal",
        },
        "slides": slides,
    }
    OUT.write_text(json.dumps(handoff, indent=2), encoding="utf-8")
    layouts = sorted({sl.get("layout_type") for sl in slides})
    print(f"wrote {OUT} slides={len(slides)} bytes={OUT.stat().st_size}")
    print("layouts:", layouts)


if __name__ == "__main__":
    main()
