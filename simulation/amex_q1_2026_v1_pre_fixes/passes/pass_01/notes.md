# Pass 01 — Amex Q1'26 vs renderer_v2

## Setup
- Source PDF: `Q1-2026-Earnings-Presentation.pdf` (44 pages, 16:9).
- Rasterization: primitive PyMuPDF at 200 DPI → `extracted/pdf_page_*.png` (not preprocessor).
- Vision+text transcription → `extracted/slides.json`.
- Handoff: hand-authored 44-slide `handoff.json` maximizing v2 surface (title, split_text, data_table, line/stacked/combo/dual charts, metric_dashboard, three_column, section_divider, native disclosure).
- Render: `python -m impact_slides.renderer_v2 --handoff ... --self-contained --no-strict` → 44 slides OK.
- Capture: Playwright Chromium 1920×1080 per `.slide`; pixel MAE similarity + side-by-side compares in `screenshots/`.

## Aggregate scores (pixel MAE — **optimistic**, high white-area bias)
| Metric | Value |
|--------|------:|
| Mean similarity | **86.12%** |
| Mean SSIM-approx | **85.71%** |
| Worst slides | 43 (20%), 22 (24%), 5 (77%) |
| Best slides | 10 (95%), 21 (94%), 30 (93%) |

**Scoring caveat:** MAE similarity is inflated when both PDF and HTML are mostly white. Structural layout fidelity is *much* lower than ~86%. Treat scores as relative trends within this run, not absolute IR-fidelity.

Full scores: `diff_scores.json`. Montage: `diff.png`.

---

## What matched (credit)

1. **Cover chromatic scaffold** (slide 00 / PDF p1): two-tone navy over bright blue band is approached well by `title_or_opening` — colors are in the Amex neighborhood without theme plumbing via CLI `--theme`.
2. **Numeric content intake**: tables and Chart.js paths accept the IR numbers (summary financials, billings lines, stacked NCA bars, guidance KPIs) without schema rejection.
3. **Line + under-chart table pattern** (PDF p4 Total Billed Business): `line_chart` + `secondary_visual` data_table is a real v2 feature and did render a secondary G&S/T&E grid under the chart (`compare_03.png`).
4. **Stacked bar acquisitions** (PDF p12): segment stack (UCS / Commercial / ICS) + KPI chips is directionally correct (`compare_11.png`) — Chart.js stacked path works.
5. **Native disclosure** pedestals footnotes off the main canvas (methodologically sound for Boardroom; not IR collapsible chrome but valid v2 feature usage).
6. **Guidance KPIs** (PDF p22): two big metric cards communicate the same two ranges (`compare_21.png`).

---

## Per-area divergences (A = handoff-tunable, B = renderer capability gap)

### D1 — Full-bleed brand cover with lockup / seal watermark
- **Evidence:** `screenshots/compare_00.png` (PDF page 00 vs HTML slide 00).
- **Diff:** PDF has Amex centurion seal line-art + AMEX ribbon lower-right, date in lower-left blue band, title block left-mid. HTML has Boardroom cover chrome (COVER eyebrow, footer "Boardroom Earnings", slide controls) and **no seal / no brand mark asset**.
- **Type:** **(B)** missing brand-mark / full-bleed asset layout and IR cover recipe. Partial **(A)** for title line-breaks and date placement only.

### D2 — Centered single-column bullet list with inline emphasis
- **Evidence:** `screenshots/compare_01.png` (Business Highlights).
- **Diff:** PDF = centered title + large single-column bullets with selective bold phrases on partner/product names. HTML forced `split_text_visual` into **two cards** ("The case" / "In the evidence"), denatured body size, dropped bold spans, omega empty right rail / icon placeholder, omitted last highlight bullet visually crowded.
- **Type:** **(B)** no first-class "IR bullet sheet" / full-width prose list layout; no handoff field for **inline rich-text bold spans** inside bullets. Relayout via freeform_grid may mitigate chrome but not bold spans → still **(B)** for rich text. Mild **(A)** if freeform single-column bullets improve geometry next pass.

### D3 — Columnar pill-header comparison table (not row-grid)
- **Evidence:** `screenshots/compare_02.png` (Summary Financial Performance).
- **Diff:** PDF has row labels outside three **vertical pill columns** (Q1'26 / Q1'25 / YoY) with rounded navy caps. HTML `data_table` paints a conventional **row-striped grid with a single header row**. Footnotes on PDF sit as micro-type under stage; v2 puts them in disclosure strip.
- **Type:** **(B)** no "statement-style / pill-column comparison table" layout. Content values themselves = **(A)** (already correct).

### D4 — IR line chart house style (0–15% axis, point value labels, dashed series, callout box)
- **Evidence:** `screenshots/compare_03.png` (Total Billed Business).
- **Diff:** PDF chart is stage-dominant with:
  - fixed 0/5/10/15% y-axis
  - navy solid + gray **dashed** secondary series
  - **percent labels on every point**
  - "Leap Year Approx. (1%)" dashed annotation box
  - "Reported" end-label
  - full-width under-chart navy-header table aligned to categories  
  HTML Chart.js: auto-scaled ~6–10 y domain, solid dual series (legend "Value"/"S2"), no point percent labels, no annotation box, table present but **not full-width category-aligned** like PDF house style; KPI chips added under chart.
- **Type:** primarily **(B)** — chart annotation layer, forced axis domain / % tick formatter, dashed series style reliably from handoff, on-point value labels, end-series callouts. Secondary table alignment exists in code for some paths but weak vs PDF → **(B) weak**. Series naming / dropping extra KPI chips = **(A)** for next pass.

### D5 — Dual enterprise panels (stacked bar + oversized KPI callouts side-by-side)
- **Evidence:** `screenshots/compare_11.png` (New Acquisitions).
- **Diff:** PDF = two cards: left stacked bars with exterior legend hierarchy, right **giant 66% / 73%** callout stack. HTML collapses to single full-width chart + thin KPI chips — loses the IR "hero % callout column".
- **Type:** **(B)** no layout for "chart | hero KPI stack" buttoned card pair (dual_chart is two charts, not chart+hero metrics). Partial **(A)** via freeform_grid metric_stack (try in later pass).

### D6 — Two-metric centered guidance card
- **Evidence:** `screenshots/compare_21.png` (2026 Guidance).
- **Diff:** PDF = single bordered card, navy header "2026 Guidance", two underlined label/value pairs centered. HTML = two separate metric cards left-aligned + so_what sentence + disclosure. Footnote packing differs.
- **Type:** mixed — values **(A)** ok; single floating statement card chrome = **(B)** missing "IR guidance card" recipe (or weak freeform).

### D7 — Brand section divider / appendix cover fidelity
- **Evidence:** mean scores for slides 22 & 43 (~20–24%); HTML nearly white (`html_slide_22/43` white_frac ~0.97) while PDF appendix divider is full navy/blue brand bleed.
- **Diff:** `section_divider` did not reproduce two-tone Amex appendix cover.
- **Type:** **(B)** section_divider not brand-asset capable / not full-bleed poorly parameterized from handoff.

### D8 — Multi-panel capital / platinum / specialized broken-axis charts
- **Evidence:** PDF pages 05 (Platinum dual panels + broken 90–100% retention axis), 20 (Capital multi-panel ROE + stacked returns + shares + CET1). HTML dual_chart / metric_dashboard approximations (scores mid-high but structure wrong).
- **Type:** **(B)** no broken-axis support, no multi-region IR dashboard recipe, no multi-tile capital returns board.

### D9 — Dense annex widescreen tables
- **Evidence:** annex scaffold slides 30–36 use placeholder rows; PDF has dense multi-ydimension IR grids.
- **Type:** content completeness **(A)** (fill cells in later passes). Wide financial annex density, small type, multi-header stubs = likely **(B)** if table recipe cannot pack 10+ columns legibly at 1920×1080 (verify next passes after filling numbers).

### D10 — Boardroom shell chrome vs IR chrome
- **Evidence:** all compares — HTML shows slide index controls, "Boardroom" foot brands, left title rail freuqently left-aligned vs PDF centered titles.
- **Type:** **(B)** delivery shell is Boardroom product chrome, not pass-through IR viewer chrome; accepted as product difference but blocks pixel-level replication.

### D11 — Negative stacked bar (reserve release)
- **Evidence:** provision slide handoff stripped negatives to 0 in pass_01 to avoid bad stacks (`handoff` slide 15 notes).
- **Type:** **(B)** if stacked bars cannot express negative reserve release segments below axis (needs confirmation with true negative values next pass — capability candidate).

### D12 — Theme tokens from handoff JSON ignored
- **Evidence:** `presentation.theme` put Amex CSS variables in handoff, but CLI `render_deck(theme=)` is only a Python kwarg — schema theme was **not** injected automatically.
- **Type:** **(B)** weak — no handoff-native theme map wired through CLI load path (or undocumented). Workaround would be renderer/code change; even with tokens, Amex seal still missing.

---

## Top 3 divergences for pass table

1. **IR line-chart house style** (annotations, dashed series, 0–max% axis, on-point labels) — **(B)** — `compare_03.png`.
2. **Pill-column financial comparison table vs row grid** — **(B)** — `compare_02.png`.
3. **Full-width IR bullet list + inline bold + brand cover seal** — **(B)** — `compare_01.png`, `compare_00.png`.

---

## Type (A) actions queue for pass_02 (handoff only)
1. Prefer remaining **freeform_grid** layouts for Highlights (single full-width bullets) and Guidance (one centered card slot).
2. Clean chart series names via `chart_config.series_names`; remove redundant key_stats chips where they fight IR layout.
3. Fill expense (p20) and key annex tables from PDF text with real cells.
4. Try metric_row / freeform for New Acquisitions right-rail giant %.
5. Re-test stacked bar with true negative reserve values to confirm D11.
6. Drop so_what sentences that invent Boardroom narrative not on PDF.

Do **not** expect (A)-only passes to close D1/D3/D4/D7/D8/D10 — those stay as capability gaps.

## Files
- `handoff.json`, `output/presentation.html`
- `screenshots/html_slide_XX.png`, `screenshots/compare_XX.png`
- `diff.png`, `diff_scores.json`
- builders: `_build_handoff.py`, `_screenshot_and_diff.py`
