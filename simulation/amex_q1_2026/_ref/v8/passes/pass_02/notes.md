# Pass 02 — handoff A-tunes after pass_01 geometry baseline

**Date:** 2026-07-29
**Renderer:** `origin/main` @ `a72e7bb` (unchanged; measure-only).
**Base handoff:** pass_01 + A-lever edits only.
**Render:** `python -m impact_slides.renderer_v2 --handoff …/pass_02/handoff.json --out …/pass_02/output` → 44 slides OK.
**Evidence:** `geometry.json` (**57/57 pass**, 0 fail), `side_by_side/compare_{02,05,11,14,16,19,27}.png`.
**Method:** geometry (±4px) + SBS reading. **No MAE %.**

## Handoff deltas vs pass_01

| Slide | Change | Intent | Outcome |
|------:|--------|--------|---------|
| **05** tile0 | `show_legend: false`; clear `side_legend: []` | close multi_panel single-series legend residual (pass_01 sole FAIL) | **A closed** — geometry now 57/57; pane0 legend display false / nDS=1 |
| **05** tile1 | keep multi-series `side_legend` + Chart.js legend | multi-series must stay informational | held (legend display true / nDS=2) |
| **16** left | `callouts: [{elbow_arrow, from:0, to:7, text:"17% CAGR"}]` + point labels | recover CAGR spanning chrome | **A partial** — capsule paints (`17% CAGR`, w≈678h≈30) but silhouette is full-width filled elbow/arrow, not PDF thin line + mid pill + dual end ticks + `% CAGR` under-label. `$` prefix still missing on labels (`2.8` vs `$2.8`) despite bars correct |
| **16** right | `show_point_labels` + `y_axis_unit: %` | match PDF % dots | **A closed** on series labels (`16%`…); dual-card skin still B |
| **14** | exterior name knobs: wrap 18 / gutter 150 / font 18 / max_lines 2 | stop mid-token wrap on "Build/(Reli…" | **A improved** — "Reserve Build/(Release)" readable as one exterior name; furniture still sheet-row not freestanding boxed cells |
| **27** both tiles | wrap 16 / gutter 150 / font 16 / max_lines 4; `show_legend:false` | N5 density residual | **A minor** — names readable, no Chart.js legend conflict; bar cards still narrower / FDIC callout is footer so_what not on-card chip |
| **11** | slight exterior gutter/font tighten | free chart room for R4 | **no meaningful R4 effect** (hero digits already 110px — see below) |

## Geometry summary

| Bucket | Result |
|--------|--------|
| Total assertions | **57** |
| Passed | **57** |
| Failed | **0** |

Key deltas vs pass_01 fail:

| Assertion | pass_01 | pass_02 |
|-----------|---------|---------|
| s05 pane0 single-series legend suppressed | **FAIL** (`display:true`, nDS=1) | **PASS** (`display:false`) |
| All T6/T7/T9/T10/T11 dual/T12/T13 | PASS | PASS (reconfirmed) |
| Funding side_legend count | 0 | 0 |
| Deck-wide inset overlap | 0 | 0 |

R2 geometry still exact (elbow left/width/stem vs bar centres Δ 0.00 within wrap; chevron at:2 centre = bar2; axis-break outside plot).

## Hero type-scale probe (s11) — **updates R4**

| Node | Measured | PDF target | Status |
|------|---------:|------------|--------|
| `.gl-hero-value-num` "66" / "73" | **font-size 110px**, weight 700, h≈157 | ~110px digits | **digit scale resolved** |
| `.gl-hero-value-unit` "%" | **46.2px** | smaller % glyph | **unit split exists** |
| `.gl-hero-label` | **17px**, stacked **under** the number, truncates long lines | caption **beside** large number on one card | **layout residual B** |

pass_01 called R4 "boardroom scale not 110px" from SBS alone. Live computed style shows digits **are** 110px. Residual is **card recipe**: two hug-width stacked cards with under-number wrapping captions vs PDF one framed panel with caption to the **right** of 66%/73%. No handoff type-scale knob; no caption-placement knob.

## Side-by-side readings (focus)

- **05 Platinum (`compare_05.png`):** Single-series legend gone on left tile. Residual chrome recipe remaining for **B**:
  1. Elbow is **full mid-span blue capsule + right arrowhead** with vertical stem from left end; PDF is **short L-elbow** (vertical arm + short pill + arrow). L-bracket silhouette remains **closed accepted r5 L3** — do not reopen as gap.
  2. IR `top_total` head chips (`+ ~6 pp`, `94–97%`) + dual Chart.js legends on right card vs PDF title-only board tops.
  3. Left bars show in-bar value chips (`7/7/9/9/10`); PDF has clean bars.
  4. Chevron correct under Q3'25 but smaller than PDF capsule.
  5. Right tile axis footprint (90–100 with `//` hatch) OK T6; month labels left of pairs not "Anniversary Month" column head style.

- **16 Net Card Fees (`compare_16.png`):** CAGR elbow # lands as thick blue continuum bar over the left chart — **wrong chrome recipe vs PDF thin rule + mid "% CAGR" pill with end ticks**. Dual panes are one linked enclosure vs PDF **two rounded separate cards** with in-card titles. `$` prefixes on bar tops still missing (unit wiring exists for `%` suffix but `$` prefix path weak / not engaged). Point labels + colours correct.

- **14 Provision (`compare_14.png`):** Exterior series names paint; mid-token wrap fixed. Under-chart **navy dense table sheet** (`Reserve Rate… 2.9%…`) + footer KPI `$1,251` — PDF freestanding **left label box + five bordered white cells**. No handoff produces boxed period cells.

- **11 Acquisitions (`compare_11.png`):** Exterior stack names + stack totals good. Hero **110px** digits render; cards still **undersized / caption-under**, labels truncate ("Millennial and"). Chart panel loses PDF’s in-card title "Proprietary New Cards Acquired". Residual = layout recipe densification / caption-aside, **not digit scale**.

- **27 Funding (`compare_27.png`):** Clean single exterior-name source (no triple legend). Long names wrap OK at wrap_chars=16. Residuals: bar width density, PD on-card "92% FDIC…" chip sits as bottom so_what not right-card callout; header dollars as tile `top_total` not on-stack like PDF.

- **02 Summary (`compare_02.png`):** Unchanged structure — exterior labels + three navy-header free pills. Board/slide height frac **0.673**. PDF has darker perimeter lines, tighter row rhythm, stronger stub bold. No packing A knobs remain → **F4+ B weak**.

- **19 Expense inset:** not re-toured beyond geometry; pass_01 settled T12 overlap=0. Skin (solid navy pill vs outlined VCE box) remains cosmetic **B**.

## A vs B after pass_02

| Class | Items |
|-------|-------|
| **(A) closed this pass** | multi_panel single-series legend on s05; s16 YoY point labels; s14 name wrap; funding Chart.js legend off |
| **(A) partial / exhausted** | s16 CAGR elbow exists but wrong pill-line silhouette + no `$` prefixes; further `band` vs `elbow_arrow` swaps unlikely to yield PDF thin-rule (elbow is the full span recipe). No further density knobs for F4+/N5 packing. |
| **(B) confirmed residual** | R2 IR board chrome (top_total band, dual legend right, clean-bar vs in-bar chips, elbow silhouette art — L3 accepted); F4+ packing; N6 freestanding reserve-rate boxes; N5 multi_panel card density / on-card FDIC chip; R4 **caption-aside layout** (digit scale itself resolved); s16 dual rounded cards + thin CAGR rule + `$` bar labels |
| **Resolved / excluded (carry)** | T6 T7 T9 T10 T11(dual+multi_panel A) T12 T13; R1/F12+/N2 D11; R2 L3 silhouette; R3 wontfix |

## Stop check for further passes

Remaining open items are almost all **type B** (no handoff expresses freestanding boxed rate cells, IR title-only boards without top_total chrome, PDF thin CAGR rule, caption-beside-hero, pill packing density). A few micro A tries remain (s16 `y_axis_unit_position: prefix` + unit `$`; s05 strip `top_total` / `point_labels` for cleaner IR board; s27 move FDIC into tile `badge`) — worth **one more short pass** then freeze for GAP_ANALYSIS.

## Artifacts

- `handoff.json`, `output/presentation.html`
- `geometry.json` (57/57)
- focus screenshots + SBS for indices 02,05,11,14,16,19,27
