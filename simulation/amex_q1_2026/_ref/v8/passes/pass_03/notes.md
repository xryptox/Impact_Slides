# Pass 03 — final type-A micro-levers (then freeze)

**Date:** 2026-07-29
**Renderer:** `origin/main` @ `a72e7bb` (unchanged; measure-only).
**Base:** pass_02 handoff + A-only micro edits.
**Render:** `python -m impact_slides.renderer_v2 …/pass_03/handoff.json → output/` (44 slides OK).
**Evidence:** `geometry.json` (**57/57 pass**, 0 fail); focus SBS `compare_{02,05,11,14,16,19,27}.png`.
**Method:** geometry (±4px) + SBS reading. **No MAE %.**

## Handoff deltas vs pass_02

| Slide | Change | Intent | Outcome |
|------:|--------|--------|---------|
| **05** both tiles | clear `top_total` | drop IR head chips (`+ ~6 pp`, `94–97%`) PDF lacks | **A closed for head chips** — DOM no longer emits `.gl-tile-ir-total`. Residual B: full elbow continuum + dual right legend + in-bar year chips + closed L3 silhouette |
| **05** left | force `point_labels`/`bar_labels_inside` off | clean bars | **held** (no in-bar spend chips). Right tile still has series-inside year chips (PDF also labels years inside bars — print OK) |
| **16** left | `y_axis_unit:"$"`, `y_axis_unit_position:"prefix"` | `$0.9` bar tops | **A fail** — live labels still `0.9`…`2.8` (no `$`). Unit path does not reach dual_chart bar datalabel formatter here |
| **16** left | CAGR callout type `band` (was `elbow_arrow`) | prefer PDF thin rule + mid pill | **A worse** — band paints full-height span chrome (`17% CAGR` node **w≈678 h≈413**), not a thin mid rule. Elbow was wrong silhouette; band is worse mass. Recipe is **B** either type |
| **27** right tile | `badge: "92% of deposits FDIC insured*"`; clear `so_what` | on-card FDIC chip | **A partial** — badge paints (top-right navy pill, measured), but PDF’s vertical multi-line callout beside Deposit Programs is still a different density/position. Density residual remains B |
| **11** | no further type-scale knobs | R4 check | digits still **110px** / unit **46.2px**; `.gl-hero-label` already sits **beside** the number in live CSS. Residual = two stacked cards vs PDF single framed dual-metric panel + missing in-card chart title — not digit scale |

## Geometry

| Bucket | Result |
|--------|--------|
| Total | **57** |
| Passed | **57** |
| Failed | **0** |

All round-5 verify rows reconfirmed (T6/T7/T9/T10/T11/T12/T13), s05 multi_panel legend off, s16 dual headings, deck-wide inset overlap 0, annex navy uniform, no `var(--` in chart scripts, F4+ board h/slide = **0.673**.

## Live probes (extras vs shared probe script)

| Slide | Finding |
|------:|---------|
| **16** | band callout DOM class `chartjs-callout-band`, box **678×413**; no `$` in bar label canvas/DOM; `$` only in subtitle/`gl-tile-label` |
| **05** | no `.gl-tile-ir-total`; titles only; chevron tip+pill still split & at bar2 |
| **27** | badge node present w≈174 h≈19 top-right of tile1; `so_what` null |
| **11** | hero-label left of text is **to the right of** 66/73 (beside, not under). pass_02 "caption-under" was an SBS misread of stacked **cards**; caption-aside within each card already works |
| **14** | under-chart remains one dense `data_table` row (Reserve Rate…), not freestanding boxed cells |

## Side-by-side readings

- **05 (`compare_05.png`):** Cleaner heads (no top_total chips). Elbow still full-span continuum + stem; PDF short L-elbow + pill. Right card dual legends (side_legend + Chart.js). Axis-break `//` OK (T6). **Geometry identity held; furniture chrome still B art.**
- **16 (`compare_16.png`):** band callout = tall translucent span + small top label — far from PDF thin dual-ended rule + mid `17% / Year` pill + `% CAGR` under. Bars correct colour/shape; labels lack `$`. Linked dual pane vs two rounded cards.
- **27 (`compare_27.png`):** FDIC badge on; exterior names single source; cards still less padded, on-stack `$210/$219` placement differs (tile top_total band vs PDF above each column). Density/pack still **N5 residual B**.
- **11 (`compare_11.png`):** 110px held; captions beside in-card; residual single-panel dual-metric recipe + chart in-card title "Proprietary New Cards Acquired".
- **14 / 02 / 19:** unchanged structural B (N6 boxes, F4+ packing weak, inset skin cosmetic).

## A vs B after pass_03

| Class | Items |
|-------|-------|
| **(A) closed** | s05 IR `top_total` heads; earlier pass_02 legend/`name` wraps |
| **(A) attempted & exhausted** | s16 `$` prefix labels (lever exists, dual_chart bar path ignores); s16 `band` vs `elbow_arrow` CAGR (neither is PDF thin-rule); s27 badge (lands, not PDF tall side callout); s11 no further lever |
| **(B) residual freeze set** | F4+ pill packing; N6 freestanding reserve-rate cells; N5 funding density / on-stack dollars; R4 dual-metric card recipe (digit scale resolved); s16 CAGR chrome recipe + dual cards + `$` labels; s05 elbow art continuum (L3 silhouette accepted closed) / dual legend right |
| **Resolved / excluded** | T6 T7 T9 T10 T11 T12 T13; R1/F12+/N2 D11; R2 L3; R3 wontfix |

## Stop decision

Further handoff passes cannot invent freestanding rate cells, thin CAGR rules, IR board art, or dual-metric single-frame. **Freeze at pass_03.** Next iteration writes `GAP_ANALYSIS.md` only.

## Artifacts
- `handoff.json`, `output/presentation.html`
- `geometry.json` (57/57)
- focus screenshots + SBS for 02,05,11,14,16,19,27
