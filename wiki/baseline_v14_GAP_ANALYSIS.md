# Gap Analysis v14: renderer_v3 vs Amex Q1'26 Earnings PDF **(Complete 44-page PDF↔HTML observation with DP-6 + #249 design ledger — Companion-mode SIMULATION only)**

**Simulation:** `simulation/amex_q1_2026/`
**Source of truth:** `C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf`
**PDF identity:** SHA-256 `a87c11625c84e0dabb02d523f6a2d2508b892f18ee242ef197a9b40157bd3faf` · 44 pages · page0 rect 959.76×540.0
**Renderer under test:** `impact_slides.renderer_v3` **3.0.0** @ `fb0beb02987b3a076b3f64302a64835a11614f97`
**Canonical input (read-only; no mutations):** `tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json`
**Handoff SHA-256:** `9397bbc9f4107020995ae4eef9a5a1eb7a01ba2aa758d163b7ec3d1a940d40b3`
**Prior baseline:** v13 report via `git show ea541bf:wiki/baseline_v13_GAP_ANALYSIS.md` (never merged to main; renderer @ `a76b65f`, handoff `dc7742a6…`)
**Method:** One strict `python -m impact_slides.renderer_v3` publish → Playwright capture via `scripts/simulation_probe.wait_for_paint_ready_charts` + `measured_tick_styles` + `furniture_presence` (DP-6) + #249 extensions (`measured_stub_ratio`, `measured_support_chrome`, `measured_series_palette`, `measured_metric_value_styles`, `measured_bar_occupancy`) + section isolate (lesson 32) → PyMuPDF 1920×1080 PDF rasters → full-resolution SBS. **No MAE / similarity % / pixel-diff scores / heatmaps.**

This run re-validates the deck after post-v13 renderer fixes: **#246** table stub-slack cap + sparse bar occupancy, **#247** category-aligned support-table chrome, **#248** sky-blue palette activation + green-cycle removal + KPI metric floor + line-label contrast freeze.

---

## 1. Scope gate, mapping assertion, run identity

| Gate | Result |
|------|--------|
| Renderer commit | `fb0beb02987b3a076b3f64302a64835a11614f97` |
| Renderer version | `3.0.0` |
| Production paths touched | **None** (only `simulation/amex_q1_2026/**` + final `wiki/baseline_v14_GAP_ANALYSIS.md`) |
| Handoff | Committed D314 corpus only — **no** `amex_handoff_mutations.py`, no hand edits |
| Handoff delta vs v13 | `dc7742a6…` → `9397bbc9…` (post-v13 #248 corpus updates already in fixture) |
| Render command | `python -m impact_slides.renderer_v3 --handoff tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json --out simulation/amex_q1_2026/passes/pass_01/renderer_v3_out` |
| Render outcome | **strict exit 0**, `run_meta.status=clean`, `ok=true`, `options.strict=true` |
| `run_meta` events | 65 × `info` · **0** warn/error |
| PDF pages | 44 |
| HTML `data-slide-number` | 44 unique values **1…44** |
| HTML `data-layout` vs corpus `layout_type` | **44/44 match** |
| Identity map | **HTML slide N → PDF index N−1 → physical page N** |
| Capture contract | viewport **1920×1080**, `deviceScaleFactor=1` (fit scale 1); isolate target `section.slide` (siblings `display:none`, stage/slide transform none); element screenshot; `wait_for_paint_ready_charts` before every chart-slide shot; DP-6 ticks/furniture + #249 extensions after paint-ready; **no** `painted_datalabel_lines`; no nth selectors; no fixed sleeps |
| Comparison artifacts | 44 PDF + 44 HTML + 44 SBS @ exact 1920×1080 halves (SBS 3840×1080); contact sheet; `comparison_manifest.json` `missing_or_bad_size=[]` |
| Design ledger | **44/44 rows** in manifest; **42/44 overall ok**; fails are s4/s19 `support_chrome` probe selector miss (see §2.3) — ticks/furniture still green on those slides |
| HTML PNG uniqueness | **44 distinct SHA-256** |
| Console errors | `[]` |
| Image scoring | **forbidden / absent** |
| Scope-gate | **PASS** |

### Published artifact hashes (`passes/pass_01/renderer_v3_out/`)

| File | SHA-256 |
|------|---------|
| `presentation.html` | `6a1f48eb1b69197bce66508c9895e2c7b77f2ecb398474213c4940716c8be02c` |
| `run_meta.json` | `66f56bdb7284f67bccf8c7b6429d1ace5346ef1efbc5287e38a9115c2a49a8bb` |
| `evidence_manifest.json` | `6b8c217a8b2384a4d09c7b24d2b52b3d5472d3761867ef8d0b3cc0af0244e3c5` |
| `handoff_schema_v1.json` | `8a650ad61f5c8a4a1b97f0d16cf53c03f651b958bc23339a3f7b5824ea0622c1` |
| `slide_notes.md` | `78823a5fba725aa5deb5961399a066b9a6935af1cf724bc851f2a8b079b4ae8e` |

### Capture contract detail

- Deck is a stacked scroll of all 44 `section.slide` nodes inside `.deck-stage` (no `.active` hide rule; resize-fit scales by `min(innerWidth/1920, innerHeight/1080)`).
- Capture forces transform/scale identity and screenshots the section node after paint-ready settle.
- Chart slides with paint-ready geometry (nonzero canvas, non-degenerate `chartArea`, painted dataset elements across one rAF): **4–6, 8–15, 17–19, 21, 24, 27–28**.
- Primary surface is JS-on Chart.js (SVG noscript fallback not used for comparison).
- DP-6 tick measurement uses **computed style** on overlay tick `<text>` (not presentation attributes alone). Furniture uses `DESIGN_LEDGER_FURNITURE` selectors + expected_text; zero matches = failure.
- #249 extensions run only on their mapped slides (see §2.2); a `ProbeError` is recorded as failure — never invented green.

### Mapping assertion

| slide | layout_type (corpus = HTML) | pdf_index | physical_page |
|------:|-----------------------------|----------:|--------------:|
| 1 | `opening_cover` | 0 | 1 |
| 2 | `narrative` | 1 | 2 |
| 3 | `period_comparison` | 2 | 3 |
| 4 | `single_chart` | 3 | 4 |
| 5 | `single_chart` | 4 | 5 |
| 6 | `dual_chart` | 5 | 6 |
| 7 | `comparison_cards` | 6 | 7 |
| 8 | `single_chart` | 7 | 8 |
| 9 | `single_chart` | 8 | 9 |
| 10 | `single_chart` | 9 | 10 |
| 11 | `single_chart` | 10 | 11 |
| 12 | `chart_hero_dual` | 11 | 12 |
| 13 | `single_chart` | 12 | 13 |
| 14 | `dual_chart` | 13 | 14 |
| 15 | `single_chart` | 14 | 15 |
| 16 | `data_table` | 15 | 16 |
| 17 | `dual_chart` | 16 | 17 |
| 18 | `chart_hero_dual` | 17 | 18 |
| 19 | `single_chart` | 18 | 19 |
| 20 | `period_comparison` | 19 | 20 |
| 21 | `chart_hero_dual` | 20 | 21 |
| 22 | `metric_overview` | 21 | 22 |
| 23 | `section_divider` | 22 | 23 |
| 24 | `single_chart` | 23 | 24 |
| 25 | `data_table` | 24 | 25 |
| 26 | `data_table` | 25 | 26 |
| 27 | `dual_chart` | 26 | 27 |
| 28 | `dual_chart` | 27 | 28 |
| 29 | `narrative` | 28 | 29 |
| 30 | `narrative` | 29 | 30 |
| 31 | `annex_table` | 30 | 31 |
| 32 | `grouped_annex_table` | 31 | 32 |
| 33 | `annex_table` | 32 | 33 |
| 34 | `annex_table` | 33 | 34 |
| 35 | `annex_table` | 34 | 35 |
| 36 | `annex_table` | 35 | 36 |
| 37 | `annex_table` | 36 | 37 |
| 38 | `legal_notice` | 37 | 38 |
| 39 | `legal_notice` | 38 | 39 |
| 40 | `legal_notice` | 39 | 40 |
| 41 | `legal_notice` | 40 | 41 |
| 42 | `legal_notice` | 41 | 42 |
| 43 | `legal_notice` | 42 | 43 |
| 44 | `closing_cover` | 43 | 44 |

**HOLD** for all 44 rows.

---

## 2. DP-6 design ledger (+ #249 extensions)

Machine-readable twin: `comparison_manifest.json` → `design_ledgers[]` (one object per slide).

**Contract:** chart layouts run `measured_tick_styles` (computed font-size ≥ 20px, font-weight ≥ 600, tick_count > 0) and every `DESIGN_LEDGER_FURNITURE` entry for that slide via `furniture_presence`. Non-chart slides without an extension target record `{ok: true, ticks: null, furniture: []}`. Extension targets add stub_ratio / support_chrome / palette / metric_floor / bar_occupancy rows. A `ProbeError` is recorded as failure — never invented green. Classification may add **design-parity verified** only when the slide's design ledger is overall `ok`.

### 2.1 Summary

| metric | result |
|--------|--------|
| Design-ledger rows | **44/44** |
| Overall ok | **42/44** |
| Chart slides measured | 4–6, 8–15, 17–19, 21, 24, 27–28 |
| Min tick font-size (all chart slides) | **20.0 px** (floor met) |
| Min tick font-weight (all chart slides) | **600** (floor met) |
| C1 furniture slides green | **4, 5, 6, 8, 9, 10, 12, 15, 17, 18, 19, 21, 24, 28** (all expected selectors) |
| #246 stub_ratio (s3/s16/s31–37) | **9/9 ok** — max share ≤ 0.45 on every target |
| #246 bar_occupancy (s28) | **ok** — min observed ratio **0.55** (≥ 0.5) |
| #248 metric_floor (s8/s12) | **ok** — min value font-size **44 px** (≥ 40) |
| #248 palette (s24/s28) | **ok** — no series `#0A7D55`; s28 `has_sky_blue=true` (`#80C8FF`); s24 navy-only single series (`require_sky_blue=false`) |
| #247 support_chrome (s4/s19) | **2/2 probe fail** — see §2.3 (DOM contract mismatch; furniture + SBS still show support content) |
| Capture failures (identity/paint/screenshot) | **none** (`missing_or_bad_size=[]`, `console_errors=[]`; capture_log flags design_ledger_not_ok only for s4/s19) |

### 2.2 Chart-slide tick + furniture detail

| # | layout | tick_count | min_px | min_wt | furniture rows (all ok) | extensions |
|--:|--------|----------:|-------:|-------:|-------------------------|------------|
| 4 | `single_chart` | 10 | 20 | 600 | `[data-annotation-id]` “Leap Year Approx. (1%)”; `.support-table` “G&S” | support_chrome **FAIL** (0 `.head` cells) |
| 5 | `single_chart` | 10 | 20 | 600 | `.support-table` “Gen-Z” | — |
| 6 | `dual_chart` | 18 | 20 | 600 | `[data-annotation-id]` “+ ~6 percentage points”; `[data-annotation-id]` “Refresh” | — |
| 8 | `single_chart` | 10 | 20 | 600 | `.metric-strip` “3,400+”; `[data-annotation-id]` “10x” | metric_floor **ok** (44px ×4) |
| 9 | `single_chart` | 10 | 20 | 600 | `.support-table` “U.S. SME” | — |
| 10 | `single_chart` | 10 | 20 | 600 | `.support-table` “Intl Consumer” | — |
| 11 | `single_chart` | 10 | 20 | 600 | *(none expected)* | — |
| 12 | `chart_hero_dual` | 10 | 20 | 600 | `[data-chart-type="stacked_bar"]` “International Card Services” | metric_floor **ok** (44px on 66%/73%) |
| 13 | `single_chart` | 10 | 20 | 600 | *(none expected)* | — |
| 14 | `dual_chart` | 20 | 20 | 600 | *(none expected)* | — |
| 15 | `single_chart` | 11 | 20 | 600 | `.outlined-support` “Reserve Rate for Total Balances” | — |
| 17 | `dual_chart` | 28 | 20 | 600 | `[data-measurement-id][data-role="cagr"]` “17%” | — |
| 18 | `chart_hero_dual` | 9 | 20 | 600 | `.boxed-label` “11%”; `[data-hero-type="driver_card"]` “Billed Business” | — |
| 19 | `single_chart` | 11 | 20 | 600 | `[data-annotation-id]` “Leap Year Approx. (1%)”; `.support-table` “$17.0” | support_chrome **FAIL** (0 `.head` cells) |
| 21 | `chart_hero_dual` | 16 | 20 | 600 | combo semantic table “Common Shares Outstanding”; `.outlined-support` “ROE” | — |
| 24 | `single_chart` | 11 | 20 | 600 | `.category-group` “Commercial Services”; annotation “$486B Total Network Volumes”; `.boxed-label` “37%” | palette **ok** (navy `#00175A` only) |
| 27 | `dual_chart` | 36 | 20 | 600 | *(none expected)* | — |
| 28 | `dual_chart` | 16 | 20 | 600 | `[data-annotation-id]` “92% FDIC” | palette **ok** (`#00175A/#006FCF/#63666A/#80C8FF`, sky present, no green series); bar_occupancy **ok** (ratio 0.55) |

### 2.3 #249 extension detail

#### #246 stub-slack cap (`measured_stub_ratio`, share ≤ 0.45)

| slide | layout | max_stub_share | table_count | ok |
|------:|--------|---------------:|------------:|:--:|
| 3 | `period_comparison` | 0.450 | 1 | ✓ |
| 16 | `data_table` | 0.449 | 1 | ✓ |
| 31 | `annex_table` | 0.449 | 1 | ✓ |
| 32 | `grouped_annex_table` | 0.449 | 2 | ✓ |
| 33 | `annex_table` | 0.449 | 1 | ✓ |
| 34 | `annex_table` | 0.449 | 1 | ✓ |
| 35 | `annex_table` | 0.344 | 1 | ✓ |
| 36 | `annex_table` | 0.449 | 1 | ✓ |
| 37 | `annex_table` | 0.449 | 1 | ✓ |

#### #246 bar occupancy (`measured_bar_occupancy`, bar width / category pitch ≥ 0.5)

| slide | charts | observed ratios | min_ratio gate | ok |
|------:|--------|-----------------|---------------:|:--:|
| 28 | 2 canvases (n_cat=2 each) | 0.55 / 0.55 (bar_width≈188.1, pitch=342) | 0.5 | ✓ |

#### #248 KPI metric floor (`measured_metric_value_styles`, ≥ 40px)

| slide | values | min_font_size_px | ok |
|------:|--------|-----------------:|:--:|
| 8 | 3,400+ / 300+ / $600 / $550 | 44.0 | ✓ |
| 12 | 66% / 73% | 44.0 | ✓ |

#### #248 series palette (`measured_series_palette`)

| slide | colors observed | has_sky_blue | require_sky_blue | `#0A7D55` series | ok |
|------:|-----------------|:------------:|:----------------:|:----------------:|:--:|
| 24 | `#00175A` | false | false | none | ✓ |
| 28 | `#00175A`, `#006FCF`, `#63666A`, `#80C8FF` | true | true | none | ✓ |

Note: theme CSS still defines `--color-success: #0A7D55` once as a token; **no Chart.js series fill** uses it on the palette targets (probe series colors above).

#### #247 support chrome (`measured_support_chrome`) — probe red, visual nuance

| slide | probe result | furniture | SBS visual |
|------:|--------------|-----------|------------|
| 4 | **FAIL** — `0 visible support header cells` | G&S + Leap Year **ok** | Category-aligned G&S/T&E value grid present; **no painted navy period band** like PDF (stub labels + values only; quarter labels live on chart axis) |
| 19 | **FAIL** — same selector miss | $17.0 + Leap Year **ok** | $B support row $17.0…$18.9 present; **no painted navy period band** |

**DOM facts (published HTML, slide 4):** `.support-table.category-aligned` exists with absolute `.support-cat-stub` / `.support-cat-cell.num` nodes and an `sr-only` semantic `<table>`. There are **no** `.support-cat-cell.head` / `.support-cat-stub.head` nodes. Probe `measured_support_chrome` selects only those `.head` classes, so it returns zero matches even when the painted value grid is present.

**Ownership split for #247 residual:**

1. **Probe/DOM contract mismatch** — ledger cannot certify band+hairline chrome without `.head` nodes (screenshot/probe class in §6.4).
2. **Visual chrome gap vs PDF** — SBS shows category-aligned numbers without the PDF navy header band (accepted-recipe vs capability nuance; see residual R-247).

C2 typography floor and C1 furniture backfills from v13 remain **held**.

---

## 3. Full 44-page qualitative ledger

Classification is exactly one of:
`faithful reproduction` · `accepted v3 design divergence` · `candidate renderer defect or capability gap` · `corpus/extraction residual` · `source/PDF artifact` · `capture failure`.

SBS paths are relative to `simulation/amex_q1_2026/`. Machine-readable twin: `comparison_manifest.json` (identity + design_ledgers).

**Class counts:** faithful **29** · accepted divergence **9** · corpus residual **0** · candidate defect **6** · capture failure **0**.
(s15 reserve-rate mid-quarter values now match PDF 2.9%→2.8% on SBS — prior v13 corpus residual cleared for those cells; series-color recipe still inverted vs PDF but treated as accepted recipe under faithful content.)

| # | layout_type | pdf_idx | page | SBS | class | observation (qualitative; no scores) |
|--:|-------------|--------:|-----:|-----|-------|--------------------------------------|
| 1 | `opening_cover` | 0 | P1 | `side_by_side/slide_01.png` | **accepted v3 design divergence** | PDF full-bleed navy/cyan brand cover with Centurion seal. v3 minimal white title (title + Q1'26 + April 23, 2026). Brand-seal omission is standing R3 wontfix; cover recipe intentional. |
| 2 | `narrative` | 1 | P2 | `side_by_side/slide_02.png` | **faithful reproduction** | Seven Business Highlights bullets match PDF substance and bold emphasis. Packing tighter/smaller type than PDF; footnote collapses to notes affordance. Content-complete. |
| 3 | `period_comparison` | 2 | P3 | `side_by_side/slide_03.png` | **accepted v3 design divergence** | All five KPI rows/values match. PDF uses large period pills; v3 compact right-hand matrix — schema-v1 period_comparison recipe. **#246 stub share 0.450 ≤ 0.45** (design extension ok; overall ledger ok). |
| 4 | `single_chart` | 3 | P4 | `side_by_side/slide_04.png` | **faithful reproduction** | Dual FX-adj + Reported lines with endpoint labels 9%/10%. Leap Year annotation and bottom G&S/T&E support values present. Support chrome is category-aligned value grid without PDF navy period band; ticks 20px/600. Furniture green; **design ledger overall not ok** solely due to support_chrome probe miss (§2.3) — not labeled design-parity verified. |
| 5 | `single_chart` | 4 | P5 | `side_by_side/slide_05.png` | **faithful reproduction** | UCS billings line paints. Generation-mix support table (Gen-Z…) present. **design-parity verified**. |
| 6 | `dual_chart` | 5 | P6 | `side_by_side/slide_06.png` | **faithful reproduction** | Both panes paint. “+ ~6 percentage points” and **Refresh** annotations present (v13 noted Refresh chip absent — now furniture-green). Retention y-window readable. **design-parity verified**. |
| 7 | `comparison_cards` | 6 | P7 | `side_by_side/slide_07.png` | **accepted v3 design divergence** | Circular dual-metric cards with multipliers. Values present. Card scale/orientation still differ from PDF art. |
| 8 | `single_chart` | 7 | P8 | `side_by_side/slide_08.png` | **faithful reproduction** | Dual lodging lines paint. Metric strip 3,400+ / 300+ / $600 / $550 at **44px** (#248 floor). **10x** annotation present (v13 accepted absence now closed). Bottom strip layout vs PDF right stack is recipe difference. **design-parity verified**. |
| 9 | `single_chart` | 8 | P9 | `side_by_side/slide_09.png` | **faithful reproduction** | Commercial FX-adj line paints. Support table with U.S. SME present. **design-parity verified**. |
| 10 | `single_chart` | 9 | P10 | `side_by_side/slide_10.png` | **faithful reproduction** | ICS dual line paints with markers. Support table Intl Consumer present. **design-parity verified**. |
| 11 | `single_chart` | 10 | P11 | `side_by_side/slide_11.png` | **faithful reproduction** | Series on fixed 0–15% domain. Line geometry PDF-like. **design-parity verified**. |
| 12 | `chart_hero_dual` | 11 | P12 | `side_by_side/slide_12.png` | **faithful reproduction** | Three-band stacked NCA bars paint with segment legend. Hero 66%/73% at **44px** (#248 floor). Hero copy shorter than PDF long sentences — accepted v3 hero recipe. **design-parity verified**. |
| 13 | `single_chart` | 12 | P13 | `side_by_side/slide_13.png` | **faithful reproduction** | Grouped Total Balances vs Billed Business bars/labels match structure through Q1'26. **design-parity verified**. |
| 14 | `dual_chart` | 13 | P14 | `side_by_side/slide_14.png` | **faithful reproduction** | 30+ DPD and Net Write-off panes paint with correct labels; dual-card chrome is v3 recipe. **design-parity verified**. |
| 15 | `single_chart` | 14 | P15 | `side_by_side/slide_15.png` | **faithful reproduction** | Stacked write-offs + reserve build/release geometry paints. Reserve Rate row **2.9 / 2.9 / 2.9 / 2.9 / 2.8%** matches PDF (v13 mid-quarter 2.8% residual cleared on this capture). Series color recipe still inverted vs PDF (write-offs dark vs light) — content-complete. **design-parity verified**. |
| 16 | `data_table` | 15 | P16 | `side_by_side/slide_16.png` | **accepted v3 design divergence** | All revenue line items and YoY/FX columns match. PDF pill columns vs v3 dense data grid. **#246 stub share 0.449**. |
| 17 | `dual_chart` | 16 | P17 | `side_by_side/slide_17.png` | **faithful reproduction** | Net Card Fees $ labels + 17% CAGR chrome; FX YoY line matches. **design-parity verified**. |
| 18 | `chart_hero_dual` | 17 | P18 | `side_by_side/slide_18.png` | **faithful reproduction** | NII bars with YoY boxed labels; driver card rows present. **design-parity verified**. |
| 19 | `single_chart` | 18 | P19 | `side_by_side/slide_19.png` | **faithful reproduction** | Dual revenue line paints. Leap Year annotation and $B support $17.0…$18.9 present. Same #247 band absence / probe miss as s4 — furniture green; **not** design-parity verified. |
| 20 | `period_comparison` | 19 | P20 | `side_by_side/slide_20.png` | **accepted v3 design divergence** | Expense values match incl. VCE. Nested indent flattened vs PDF hierarchy. |
| 21 | `chart_hero_dual` | 20 | P21 | `side_by_side/slide_21.png` | **faithful reproduction** | Capital stacked combo with shares line 702→682 and varying ROE; Capital Summary KPIs match. **design-parity verified**. |
| 22 | `metric_overview` | 21 | P22 | `side_by_side/slide_22.png` | **accepted v3 design divergence** | Guidance figures present; sparse list vs centered PDF card is metric_overview recipe. |
| 23 | `section_divider` | 22 | P23 | `side_by_side/slide_23.png` | **accepted v3 design divergence** | Appendix title; white plate vs navy brand divider — intentional v3 section_divider. |
| 24 | `single_chart` | 23 | P24 | `side_by_side/slide_24.png` | **faithful reproduction** | Six growth bars with category-group braces, $486B annotation, on-bar %-of-total boxed labels. Palette navy-only single series (no green cycle). **design-parity verified**. |
| 25 | `data_table` | 24 | P25 | `side_by_side/slide_25.png` | **faithful reproduction** | FX currency rows and YoY match PDF. |
| 26 | `data_table` | 25 | P26 | `side_by_side/slide_26.png` | **faithful reproduction** | T&E matrix orientation and values match PDF. |
| 27 | `dual_chart` | 26 | P27 | `side_by_side/slide_27.png` | **faithful reproduction** | Unemployment+GDP scenario fans paint-ready and track PDF. **design-parity verified**. |
| 28 | `dual_chart` | 27 | P28 | `side_by_side/slide_28.png` | **faithful reproduction** | Funding/deposit stacks paint with on-stack % and $ totals. 92% FDIC annotation present. **#248** sky-blue series active (`#80C8FF`); no `#0A7D55` series. **#246** bar occupancy 0.55. **design-parity verified**. |
| 29 | `narrative` | 28 | P29 | `side_by_side/slide_29.png` | **faithful reproduction** | Variance commentary matches PDF substance. |
| 30 | `narrative` | 29 | P30 | `side_by_side/slide_30.png` | **faithful reproduction** | Continuation commentary matches PDF substance. |
| 31 | `annex_table` | 30 | P31 | `side_by_side/slide_31.png` | **accepted v3 design divergence** | Annex1 values present; nested groups flattened. **#246 stub share 0.449**. |
| 32 | `grouped_annex_table` | 31 | P32 | `side_by_side/slide_32.png` | **faithful reproduction** | Two peer groups with correct numbers; headers fully readable. **#246 stub share 0.449**. |
| 33 | `annex_table` | 32 | P33 | `side_by_side/slide_33.png` | **faithful reproduction** | Annex2 balances grid matches. **#246 stub ok**. |
| 34 | `annex_table` | 33 | P34 | `side_by_side/slide_34.png` | **faithful reproduction** | Annex3 revenue grid populated. **#246 stub ok**. |
| 35 | `annex_table` | 34 | P35 | `side_by_side/slide_35.png` | **faithful reproduction** | Annex4 NCF grid populated. **#246 stub 0.344**. |
| 36 | `annex_table` | 35 | P36 | `side_by_side/slide_36.png` | **faithful reproduction** | Annex5 NII grid populated. **#246 stub ok**. |
| 37 | `annex_table` | 36 | P37 | `side_by_side/slide_37.png` | **faithful reproduction** | Annex6 RNIE grid populated. **#246 stub ok**. |
| 38 | `legal_notice` | 37 | P38 | `side_by_side/slide_38.png` | **candidate renderer defect or capability gap** | Full cautionary text present as dense continuous bullets; PDF multi-paragraph hierarchy/spacing largely collapsed. Same legal_notice packing class (R-D preserved). |
| 39 | `legal_notice` | 38 | P39 | `side_by_side/slide_39.png` | **candidate renderer defect or capability gap** | Continuation of legal packing class. |
| 40 | `legal_notice` | 39 | P40 | `side_by_side/slide_40.png` | **candidate renderer defect or capability gap** | Same legal_notice packing class. |
| 41 | `legal_notice` | 40 | P41 | `side_by_side/slide_41.png` | **candidate renderer defect or capability gap** | Same legal_notice packing class. |
| 42 | `legal_notice` | 41 | P42 | `side_by_side/slide_42.png` | **candidate renderer defect or capability gap** | Same legal_notice packing class. |
| 43 | `legal_notice` | 42 | P43 | `side_by_side/slide_43.png` | **candidate renderer defect or capability gap** | Same legal_notice packing class. |
| 44 | `closing_cover` | 43 | P44 | `side_by_side/slide_44.png` | **accepted v3 design divergence** | PDF navy wordmark cover vs v3 minimal white lockup — accepted cover recipe. |

---

## 4. What renderer_v3 now does well

1. **Strict clean full-deck publish** of the 44-slide D314 corpus (`run_meta.status=clean`, 65 info / 0 warn-error).
2. **Identity-stable stacked deck** — 44 `data-slide-number` + matching `data-layout`; paint-ready + isolate capture yields 44 unique HTML digests at exact 1920×1080.
3. **Chart.js paint-ready geometry** on every chart slide (including s12 stacked NCA and s27 scenario fans).
4. **DP-6 design floors held** — every chart slide measures tick computed style ≥20px/≥600; C1 furniture probes all green.
5. **#246 stub-slack cap held** on s3/s16/s31–37 (all shares ≤ 0.45, several tables sit just under the gate).
6. **#246 sparse bar occupancy held** on s28 (ratio 0.55 ≥ 0.5 on both funding/deposit canvases).
7. **#248 KPI metric floor held** — s8 strip and s12 hero values measure 44px.
8. **#248 palette activation held** on s28 (sky `#80C8FF` present; multi-stop navy/blue/neutral; no green series fill on palette targets).
9. **Post-v13 furniture gains** — s6 Refresh annotation and s8 10x callout now furniture-green; s15 reserve-rate row values match PDF on this capture.
10. **Dual-pane / hero / annex compositions** continue to mount with independent charts and metric/driver chrome.

---

## 5. V13 → V14 delta

Prior: `git show ea541bf:wiki/baseline_v13_GAP_ANALYSIS.md` (renderer `a76b65f`, handoff `dc7742a6…`, design ledger 44/44 ok without #249 extensions).

### 5.1 Explicit #246 / #247 / #248 surfaces

| residual / ticket surface | v13 state | v14 state | evidence |
|---------------------------|-----------|-----------|----------|
| **#246 stub share** s3/s16/s31–37 | not instrumented in v13 ledger | **RESOLVED / held** — all ≤ 0.45 | design_ledgers stub_ratio rows; SBS table slides |
| **#246 bar occupancy** s28 | not instrumented | **RESOLVED / held** — ratio 0.55 | design_ledger s28 bar_occupancy; SBS `side_by_side/slide_28.png` |
| **#247 support chrome** s4/s19 navy band + hairlines | furniture green; no chrome probe | **PARTIALLY RESOLVED** — category-aligned value grid paints; **no `.head` band nodes**; probe red; SBS lacks PDF navy period band | design_ledger errors; HTML DOM; SBS s04/s19 |
| **#248 sky-blue + green-cycle** s24/s28 | not instrumented | **RESOLVED / held** on probe targets — s28 sky present; no series `#0A7D55`; s24 navy single-series ok | design_ledger palette; SBS s24/s28 |
| **#248 KPI metric floor** s8/s12 | furniture present; size not measured | **RESOLVED / held** — 44px ≥ 40 | design_ledger metric_floor; SBS s08/s12 |
| **#248 line/point label contrast on white** | qualitative only | **HELD** on inspected chart SBS (endpoint/on-bar labels readable on white field; no green series labels on s24/s28) | SBS s04/s08/s24/s28; no separate contrast probe in `simulation_probe` |

### 5.2 Other v13 residuals

| ID | topic | v14 state | evidence |
|----|-------|-----------|----------|
| C2 ticks 20/600 | typography floor | **HELD** | all chart design_ledger rows |
| C1 furniture set | Leap Year / supports / strip / stack / reserve / CAGR / drivers / braces / FDIC | **HELD** (plus s6 Refresh + s8 10x newly green) | furniture rows; SBS |
| R-D s38–43 legal packing | dense bullet wall | **PRESERVED** | SBS s38–43; candidate defect class unchanged |
| C-G s15 reserve-rate values | Q2–Q4 2.8% vs PDF 2.9% | **RESOLVED** on this capture (row shows 2.9×4 then 2.8) | SBS `side_by_side/slide_15.png` |
| C-chip s6 Refresh | absent in v13 | **RESOLVED** (furniture matches “Refresh”) | design_ledger s6; SBS s06 |
| A-1.. covers / recipe chrome | accepted divergences | **PRESERVED** | s1/s3/s7/s16/s20/s22/s23/s31/s44 |
| Handoff identity | `dc7742a6…` | **replaced** by `9397bbc9…` (#248 corpus already committed) | comparison_manifest handoff_sha256 |

### 5.3 What changed in classification counts

| class | v13 | v14 |
|-------|----:|----:|
| faithful reproduction | 28 | 29 |
| accepted v3 design divergence | 9 | 9 |
| corpus/extraction residual | 1 | 0 |
| candidate renderer defect or capability gap | 6 | 6 |
| capture failure | 0 | 0 |

Net: s15 moved corpus residual → faithful (values aligned). Legal packing six-pack unchanged. No new capture failures.

---

## 6. Residual triage

Only residuals with fresh v14 evidence. No fixes designed or ticketed here.

### 6.1 Candidate renderer_v3 defect / capability gap

| ID | location | impact | likely ownership | smallest next verification |
|----|----------|--------|------------------|----------------------------|
| R-D | s38–43 `legal_notice` | Dense continuous bullets vs PDF multi-paragraph hierarchy; readability/pack density | renderer_v3 legal_notice layout / paragraph grouping | Diff one legal slide's block model vs PDF paragraph breaks; confirm whether unmarked grouping (#247 note) is still absent in corpus |
| R-247-visual | s4/s19 category-aligned support | PDF navy period header band + hairlines not painted; values/stubs only | renderer support-table chrome path for category-aligned surfaces | Inspect computed styles on painted `.support-cat-*` nodes vs PDF band; confirm whether #247 override emits header band without `.head` class |

### 6.2 Corpus / extraction / content residual

| ID | location | impact | likely ownership | smallest next verification |
|----|----------|--------|------------------|----------------------------|
| *(none newly proven)* | — | v13 C-G s15 value drift not reproduced on this capture | — | If regresses, re-check handoff reserve-rate cells vs PDF |

### 6.3 Source/PDF artifact or accepted divergence

| ID | location | notes |
|----|----------|-------|
| A-cover | s1/s44 | Brand full-bleed vs minimal v3 covers (standing wontfix) |
| A-recipe | s3/s7/s16/s20/s22/s23/s31 | Schema-v1 recipe chrome (pills, cards, dividers, flattened nests) with matching numbers |
| A-color-recipe | s15 | Write-off/reserve series color inversion vs PDF while values match — recipe, not missing data |
| A-hero-copy | s12 | Shorter hero sentences vs PDF long form |

### 6.4 Screenshot / probe / design-ledger failures

| ID | location | impact | likely ownership | smallest next verification |
|----|----------|--------|------------------|----------------------------|
| P-247-head | s4/s19 `measured_support_chrome` | Design ledger overall `ok=false` despite furniture green and visible value grid; blocks “design-parity verified” label | probe selector expects `.support-cat-cell.head` / `.support-cat-stub.head`; published DOM has `.support-cat-cell.num` + `.support-cat-stub` only | Align probe selectors with actual category-aligned markup **or** confirm renderer should emit `.head` band nodes; re-run ledger only (no image scoring) |

Identity, paint-ready, tick floors, furniture presence, stub_ratio, palette, metric_floor, and bar_occupancy probes did **not** fail.

---

## 7. Diagnostics & artifact index

### Render diagnostics

- `run_meta.status`: **clean**
- `run_meta.ok`: **true**
- `options.strict`: **true**
- Events: **65 info**, 0 warn, 0 error (codes dominated by `plan.text_wrapped` / `plan.typography_grown` / geometry reallocations — informational only)
- Console errors during capture: **[]**

### Artifact tree (`simulation/amex_q1_2026/`)

| path | role |
|------|------|
| `passes/pass_01/renderer_v3_out/presentation.html` | strict published deck |
| `passes/pass_01/renderer_v3_out/run_meta.json` | clean run meta + events |
| `passes/pass_01/renderer_v3_out/evidence_manifest.json` | publish evidence |
| `passes/pass_01/renderer_v3_out/handoff_schema_v1.json` | frozen handoff snapshot |
| `passes/pass_01/renderer_v3_out/slide_notes.md` | notes affordance dump |
| `pdf_pages/slide_XX.png` | 44 × 1920×1080 PDF rasters |
| `html_slides/slide_XX.png` | 44 × 1920×1080 HTML section screenshots |
| `side_by_side/slide_XX.png` | 44 × 3840×1080 PDF\|HTML pairs |
| `contact_sheet.png` | labeled 44-slide contact sheet (3840×954) |
| `comparison_manifest.json` | identities, sizes, design_ledgers[44], hashes |
| `capture_log.json` | per-slide capture + design_ledger_not_ok notes for s4/s19 |
| `build_v14_comparison.py` | capture driver used for this baseline |
| `GAP_ANALYSIS.md` | this report (source of wiki copy) |

### Contact sheet

- path: `contact_sheet.png`
- size: 3840×954
- sha256: `575516faf7b94083abf036263393da028d3f7eb4f55eab96d86e65ea2c670d5e`

---

## 8. Stop proofs

| proof | result |
|-------|--------|
| Strict render exit 0 clean | **PASS** (`status=clean`, `ok=true`) |
| 44 PDF / 44 HTML / 44 SBS @ exact 1920×1080 halves | **PASS** (`missing_or_bad_size=[]`) |
| `comparison_manifest.json` design-ledger row per slide | **PASS** (44 rows; 42 ok / 2 support_chrome probe fails documented) |
| Report at `simulation/amex_q1_2026/GAP_ANALYSIS.md` | **PASS** |
| Wiki copy `wiki/baseline_v14_GAP_ANALYSIS.md` byte-identical | **PASS** (docs commit) |
| Exactly two commits: sim artifacts + docs report | **PASS** (see git log on branch) |
| Only allowed paths changed | **PASS** (`simulation/amex_q1_2026/**`, `wiki/baseline_v14_GAP_ANALYSIS.md`) |
| No MAE / similarity / pixel-diff scoring | **PASS** |
| No production / tests / scripts / config edits | **PASS** |
| No mutations / issues / implementation | **PASS** (Companion observation only) |

**Stop condition:** v14 observation baseline complete with full 44-page comparison, qualitative ledger, DP-6+#249 design ledger, v13→v14 delta, residual triage, and the two allowed commits.
