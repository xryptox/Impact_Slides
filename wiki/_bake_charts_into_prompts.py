# -*- coding: utf-8 -*-
"""Bake Boardroom charts pack contracts into Renderer + Builder prompts."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
RENDERER = ROOT / "Impact Slide Renderer - Copilot and ChatGPT.md"
BUILDER = ROOT / "Impact Slide Builder - Copilot and ChatGPT.md"

CHARTS_AND_ICON = r'''### Chart layouts (`grouped_bar_chart` · `stacked_bar_chart` · `waterfall_chart` · `heatmap`)

These are **first-class `layout_type` values**, not `other` fallbacks. When the
Builder set `layout_type` to one of them — or set `layout_type: other` /
`split_text_visual` but `visual_spec.primary_visual.type` is one of the four —
**dispatch to the matching chart renderer**. Do **not** fall through to split
text + lone icon.

#### Palette + paint rules (Boardroom-safe)

- Series 1 = navy `#00175A`; series 2 = signal blue `#006FCF`.
- Optional third/fourth stack segments: ink `#63666A`, soft `#9BB5D1` only.
- **No Chart.js / D3 / CDN charts.** Hand-built **inline SVG** (bars /
  waterfall) or a **CSS grid/table** (heatmap). Zero external plot libs.
- Max **2 series** on grouped bars. Stacked: ≤4 segments, prefer 2–3.
- Reading-first: 3–7 categories; tabular numerals; axis/value labels ≥14–16px
  at 1920×1080 scale inside the SVG `viewBox`.
- Pack-from-top; soft gray chart frame; **no drop shadows / gradients**.
- **Zero on-slide `E####`.** Source names may sit in `source-strip` only.
- **One label per value — never double-stamp.** Put the number **outside**
  the bar tip (grouped) or **above** the column (waterfall). Do **not** also
  draw a callout pill on the same tip that repeats the same number (that
  produced a stacked "55 over 55" bug on max-series bars).
- Optional insight: `content.so_what` as `insight-strip` / `so-what-callout`
  **under** the chart, not on top of it.

#### Data contracts (`visual_spec.primary_visual.steps_or_data`)

**Grouped / stacked / heatmap (matrix form preferred):**

```json
[
  ["Category", "Series A", "Series B"],
  ["Gen Z", 42, 28],
  ["Millennials", 55, 36]
]
```

Or object form: `{ "label": "Gen Z", "values": { "US": 42, "EU": 28 } }`.

**Waterfall:**

```json
[
  { "label": "Announced", "value": 700, "kind": "total" },
  { "label": "NWC", "value": -18, "kind": "down" },
  { "label": "Synergy", "value": 25, "kind": "up" },
  { "label": "Adjusted", "value": 695, "kind": "total" }
]
```

`kind` ∈ `total | up | down`. Totals are navy columns; up = blue; down = ink.
**Empty data** → short empty-state line (`No chart data provided.`) + optional
insight — never a silent split panel.

#### `grouped_bar_chart`

Horizontal grouped SVG bars (long labels read cleanly). Cap 2 series.

```html
<h2 class="slide-title"><!-- title --></h2>
<p class="subtitle"><!-- optional --></p>
<div class="chart-frame layout-chart">
  <svg class="chart-svg" viewBox="0 0 1200 400" role="img" aria-label="Grouped bar chart">
    <!-- gridlines + category labels left; navy/blue rects; ONE end-of-bar value text each -->
  </svg>
  <div class="chart-legend"><!-- Series A (navy) · Series B (blue) --></div>
</div>
<div class="so-what-callout"><!-- optional content.so_what --></div>
<div class="source-strip"><!-- source_file names only --></div>
```

#### `stacked_bar_chart`

Horizontal stacked SVG. Segments share one bar per category; total at bar end.
In-segment white labels only when the segment is wide enough; do not double with
external pills.

#### `waterfall_chart`

Vertical bridge columns: total → bridges → total. Labels above each column
(`+25`, `-18`, `700`). **No** second highlight pill that repeats the bridge number.

#### `heatmap`

Not SVG-heavy — CSS matrix (soft blue intensity). Header row = column names;
first cell of each body row = row label. Cap ~4×5 cells for board readability.
Values drawn in each cell; `—` for nulls. No E####.

```html
<div class="chart-frame heatmap-wrap">
  <table class="heatmap-table">
    <thead><tr><th></th><th>US</th><th>EU</th></tr></thead>
    <tbody>
      <tr><th class="row-head">Resy</th>
          <td class="heatmap-cell" style="background: rgba(0,111,207,0.8)">90</td>
          <td class="heatmap-cell" style="background: rgba(0,111,207,0.2)">15</td></tr>
    </tbody>
  </table>
</div>
```

#### Shared CSS classes (add to `<style>` when any chart slide exists)

```css
.layout-chart .slide-main { display:flex; flex-direction:column; gap:18px; }
.chart-frame { background:#EFF0F0; border:1px solid #D8DCE3; border-radius:16px; padding:22px 28px 18px; }
.chart-svg { width:100%; height:auto; display:block; }
.chart-legend { display:flex; flex-wrap:wrap; gap:18px 28px; margin-top:14px; font-weight:600; }
.chart-legend .swatch { display:inline-block; width:14px; height:14px; border-radius:3px; margin-right:8px; }
.chart-bar-navy { fill:#00175A; } .chart-bar-blue { fill:#006FCF; }
.chart-bar-ink  { fill:#63666A; } .chart-bar-soft { fill:#9BB5D1; }
.heatmap-table { border-collapse:separate; border-spacing:6px; width:100%; }
.heatmap-cell { min-width:88px; height:64px; border-radius:10px; text-align:center;
  font-weight:700; font-variant-numeric:tabular-nums; color:#00175A; }
```

Set inline `fill="#00175A"` / `fill="#006FCF"` on SVG `<rect>`s as well as CSS
classes so fills survive partial style cascades.

### `icon_grid` (Claim — first-class grid, never a split fallback)

Dedicated layout: soft gray tiles with Lucide sprite icon + title + one body
line. **Never** fall through to `split_text_visual` with a lone SVG — that was
the Python Step-4 bug.

**Data** (`steps_or_data`), prefer:

```json
[
  { "title": "Frequency", "body": "Premium dining moments…", "icon": "ic-growth" },
  { "title": "Closed loop", "body": "Payments + loyalty + discovery.", "icon": "ic-layers" }
]
```

Also accept `"Title: body"` strings or 2-cell arrays `[title, body]`. Cap **4–6**
tiles (9 max). Grid: 2×2 for 4; 3-up for 3 or 5–6; 2-col for 2.

If `icon` missing, pick from the curated sprite via Icon mapping guidance
(financial → `ic-credit-card` / `ic-dollar`; growth → `ic-growth`; risk →
`ic-warning`; quote → `ic-quote`; default cycle is fine).

```html
<h2 class="slide-title"><!-- title --></h2>
<p class="subtitle"><!-- optional --></p>
<div class="icon-grid cols-2"><!-- or cols-3 / cols-4 -->
  <article class="icon-tile">
    <svg class="icon tile-icon icon-lg" aria-hidden="true"><use href="#ic-growth"/></svg>
    <h3><!-- title --></h3>
    <p><!-- body — one line; no E#### --></p>
  </article>
</div>
<div class="so-what-callout"><!-- optional --></div>
```

Pack-from-top; content-height tiles — **do not** flex-stretch 2–3 tiles to fill
the full column just to kill whitespace.

```css
.icon-grid { display:grid; gap:22px; width:100%; align-content:start; }
.icon-grid.cols-2 { grid-template-columns:repeat(2,minmax(0,1fr)); }
.icon-grid.cols-3 { grid-template-columns:repeat(3,minmax(0,1fr)); }
.icon-tile { background:#EFF0F0; border:1px solid #D8DCE3; border-radius:16px;
  padding:22px 24px 20px; display:flex; flex-direction:column; gap:10px; }
.icon-tile h3 { margin:0; font-size:24px; font-weight:700; color:#00175A; }
.icon-tile p  { margin:0; font-size:18px; color:#53565A; line-height:1.35; }
```

### Chart / icon dispatch (must honor)

| `layout_type` | Renderer |
|---|---|
| `grouped_bar_chart` | Chart — grouped horizontal SVG |
| `stacked_bar_chart` | Chart — stacked horizontal SVG |
| `waterfall_chart` | Chart — bridge columns |
| `heatmap` | Chart — CSS matrix |
| `icon_grid` | Dedicated icon tile grid |
| `metric_dashboard` · `data_table` · process · comparison · quote · split · title | Existing layouts |
| `other` | Split shell **unless** `primary_visual.type` is a chart/icon type above — then remap |

If both `layout_type` and `primary_visual.type` name a chart, prefer `layout_type`.

'''

BUILDER_LAYOUT = r'''## Controlled Layout Types

Use these `layout_type` values whenever possible:

- `title_or_opening`
- `split_text_visual`
- `metric_dashboard`
- `comparison_grid`
- `full_process_flow`
- `timeline`
- `roadmap`
- `data_table`
- `quote_card`
- `icon_grid`
- `grouped_bar_chart`
- `stacked_bar_chart`
- `waterfall_chart`
- `heatmap`
- `other`

> **Slide 1 is always `title_or_opening`.** Step 4 / the HTML Renderer hard-codes
> `slide_number == 1` to the deck cover. Any other `layout_type` you set on
> slide 1 is treated as the cover by Step 4 and may be displaced to slide 2 by
> the Copilot/ChatGPT Renderer. Build slide 1 as a deck cover (title, subtitle,
> audience, primary goal) and place your first semantic layout (`quote_card`,
> `metric_dashboard`, chart, `icon_grid`, …) at slide 2 or later.

### When to choose chart / icon layouts

| `layout_type` | Prefer when | `packing_mode` | Required payload in `steps_or_data` |
|---|---|---|---|
| `grouped_bar_chart` | Compare 1–2 series across 3–7 categories | `stat-led` | Header + numeric rows **or** `{label, values:{…}}` objects |
| `stacked_bar_chart` | Composition / mix across categories (≤4 segments) | `stat-led` | Same matrix form; ≥2 series columns |
| `waterfall_chart` | Bridge start → add/subtract → end | `stat-led` | Ordered `{label, value, kind: total\|up\|down}` |
| `heatmap` | 2-axis density matrix (platform × region, etc.) | `stat-led` | Full matrix with header row |
| `icon_grid` | 4–6 parallel mechanisms / thesis tiles | `argument-led` | `{title, body, icon?}` or `Title: body` strings |

**Use `layout_type` = the chart/icon name** (not only `primary_visual.type`).
Mirroring only in `primary_visual.type` while leaving `layout_type` as
`split_text_visual` / `other` risks a Renderer remapping miss.

Cite supporting `E####` in `evidence_sources` and (for metrics) `key_stats[].source`.
Never put `E####` into category labels or cell strings that will render on face —
the Renderer strips them, but clean input is better.

### Chart payload examples

**Grouped / stacked / heatmap**

```json
"layout_type": "grouped_bar_chart",
"packing_mode": "stat-led",
"visual_spec": {
  "primary_visual": {
    "type": "grouped_bar_chart",
    "description": "",
    "steps_or_data": [
      ["Cohort", "US dining", "EU dining"],
      ["Gen Z", 42, 28],
      ["Millennials", 55, 36]
    ]
  }
}
```

**Waterfall**

```json
"layout_type": "waterfall_chart",
"visual_spec": {
  "primary_visual": {
    "type": "waterfall_chart",
    "steps_or_data": [
      { "label": "Announced", "value": 700, "kind": "total" },
      { "label": "NWC", "value": -18, "kind": "down" },
      { "label": "Synergy", "value": 25, "kind": "up" },
      { "label": "Adjusted", "value": 695, "kind": "total" }
    ]
  }
}
```

**Icon grid**

```json
"layout_type": "icon_grid",
"packing_mode": "argument-led",
"visual_spec": {
  "primary_visual": {
    "type": "icon_grid",
    "steps_or_data": [
      { "title": "Frequency", "body": "Dining creates premium brand moments.", "icon": "ic-growth" },
      { "title": "Closed loop", "body": "Payments + loyalty + discovery.", "icon": "ic-layers" }
    ]
  }
}
```

Use these `primary_visual.type` values whenever possible (may match `layout_type`
for charts/icons):

- `horizontal_process_flow`
- `vertical_timeline`
- `grouped_bar_chart`
- `stacked_bar_chart`
- `waterfall_chart`
- `heatmap`
- `data_table`
- `icon_grid`
- `key_stat_callout`
- `dashboard`
- `comparison_grid`
- `roadmap`
- `quote_card`
- `other`

'''


def must_replace(hay: str, old: str, new: str, label: str) -> str:
    if old not in hay:
        raise SystemExit(f"MISS {label}: {old[:80]!r}")
    return hay.replace(old, new, 1)


def patch_renderer(t: str) -> str:
    # packing defaults
    t = must_replace(
        t,
        "| `metric_dashboard`, `data_table` | `stat-led` | numbers dominate; **one** of so_what or body_text, not always both; omit body_text when ≥3 clear KPIs |",
        "| `metric_dashboard`, `data_table`, `grouped_bar_chart`, `stacked_bar_chart`, `waterfall_chart`, `heatmap` | `stat-led` | numbers/chart dominate; **one** of so_what or body_text; omit body_text when the visual self-reads |",
        "r.pack",
    )

    start = t.find("### `icon_grid`")
    end = t.find("### `other`", start)
    if start < 0 or end < 0:
        raise SystemExit("MISS r.icon_grid/other anchors")
    t = t[:start] + CHARTS_AND_ICON + "\n" + t[end:]

    t = must_replace(
        t,
        "| Correct layout renderer per `layout_type` | Pass / Risk / Needs input | (note any `icon_grid`/`data_table` rendered) |\n",
        "| Correct layout renderer per `layout_type` | Pass / Risk / Needs input | note chart / `icon_grid` / `data_table` |\n"
        "| **Chart labels not double-stamped** (no pill + end-label same number) | Pass / Risk | hard-fail if max series shows stacked values |\n"
        "| **Charts are SVG/CSS, no external plot lib** | Pass / Risk | grouped/stacked/waterfall/heatmap when layout_type requires |\n"
        "| **`icon_grid` is a real tile grid** (never text-only / split fallback) | Pass / Risk |  |\n",
        "r.qc",
    )

    if "Honor chart / `icon_grid` layouts" not in t:
        t = must_replace(
            t,
            "- **Slide 1 is always `title_or_opening`** — the render hard-codes it. If the\n",
            "- **Honor chart / `icon_grid` layouts.** When `layout_type` is\n"
            "  `grouped_bar_chart` / `stacked_bar_chart` / `waterfall_chart` / `heatmap`\n"
            "  / `icon_grid` (or `primary_visual.type` names them under `other`), paint\n"
            "  the dedicated Boardroom chart/icon renderer — never a loner icon on a\n"
            "  split panel. One on-chart label per value; no duplicate callout pills.\n"
            "- **Slide 1 is always `title_or_opening`** — the render hard-codes it. If the\n",
            "r.guard",
        )
    return t


def patch_builder(t: str) -> str:
    start = t.find("## Controlled Layout Types")
    end = t.find("## Detect the Current Mode", start)
    if start < 0 or end < 0:
        raise SystemExit("MISS b.controlled/detect")
    # preserve trailing separator style
    t = t[:start] + BUILDER_LAYOUT.rstrip() + "\n\n---\n\n" + t[end:]

    t = must_replace(
        t,
        "| **`stat-led`** | `metric_dashboard`, `data_table` | title · headline · key_stats/table · **one** of so_what *or* body_text · bridge preferred | subtitle if title is clear; both body and so_what together |",
        "| **`stat-led`** | `metric_dashboard`, `data_table`, `grouped_bar_chart`, `stacked_bar_chart`, `waterfall_chart`, `heatmap` | title · headline · numbers/matrix in `steps_or_data` or key_stats · **one** of so_what *or* body_text · bridge preferred | subtitle if title is clear; both body and so_what together |",
        "b.pack.stat",
    )
    t = must_replace(
        t,
        "| **`argument-led`** | `split_text_visual`, `comparison_grid` | title · 3–5 sharp bullets · **one** of so_what *or* body_text · bridge preferred | extra restating band |",
        "| **`argument-led`** | `split_text_visual`, `comparison_grid`, `icon_grid` | title · 3–5 sharp bullets *or* 4–6 icon tiles · **one** of so_what *or* body_text · bridge preferred | extra restating band |",
        "b.pack.arg",
    )

    t = must_replace(
        t,
        '"layout_type": "title_or_opening | split_text_visual | metric_dashboard | comparison_grid | full_process_flow | timeline | roadmap | data_table | quote_card | other",',
        '"layout_type": "title_or_opening | split_text_visual | metric_dashboard | comparison_grid | full_process_flow | timeline | roadmap | data_table | quote_card | icon_grid | grouped_bar_chart | stacked_bar_chart | waterfall_chart | heatmap | other",',
        "b.json.lt",
    )

    old_s4 = (
        "- `visual_spec.primary_visual.steps_or_data` must be an array, even if empty. "
        "For controlled layouts (`metric_dashboard`/`full_process_flow`/`timeline`/`roadmap`/"
        "`comparison_grid`/`data_table`/`quote_card`) this array — not `description` — is what "
        "Step 4 renders. `description` is rendered only for `layout_type: other` and the PPTX placeholder panel.\n"
    )
    new_s4 = (
        "- `visual_spec.primary_visual.steps_or_data` must be an array, even if empty. "
        "For controlled layouts (`metric_dashboard`/`full_process_flow`/`timeline`/`roadmap`/"
        "`comparison_grid`/`data_table`/`quote_card`/`icon_grid`/`grouped_bar_chart`/"
        "`stacked_bar_chart`/`waterfall_chart`/`heatmap`) this array — not `description` — "
        "is the render-critical carrier. `description` is rendered only for `layout_type: other` "
        "and the PPTX placeholder panel.\n"
        "- Chart / `icon_grid` layouts are fully painted by the **Copilot/ChatGPT Impact Slide "
        "Renderer**. The Python `step4_builder_validator.py` fallback does **not** yet have "
        "native bar/waterfall/heatmap renderers — prefer the HTML Renderer handoff for those "
        "slides, and still emit clean matrix/`kind` payloads so either path can consume them later.\n"
    )
    if "Chart / `icon_grid` layouts are fully painted" not in t:
        t = must_replace(t, old_s4, new_s4, "b.s4")

    anchor = (
        "Do not underfill either — meet the density floor (≥2 non-redundant story layers beyond the visual) "
        "**without** monotonous four-band chrome or banned openers.\n"
    )
    add = (
        anchor
        + "- When `layout_type` is a chart, **do not** ship empty or prose-only `steps_or_data`. "
        "Emit a numeric matrix or waterfall `{label,value,kind}` list. When using `icon_grid`, "
        "emit 4–6 `{title, body, icon?}` tiles (or `Title: body` strings).\n"
    )
    if "When `layout_type` is a chart" not in t:
        t = must_replace(t, anchor, add, "b.guard")
    return t


def main() -> None:
    r0 = RENDERER.read_text(encoding="utf-8")
    b0 = BUILDER.read_text(encoding="utf-8")
    r1 = patch_renderer(r0)
    b1 = patch_builder(b0)
    RENDERER.write_text(r1, encoding="utf-8")
    BUILDER.write_text(b1, encoding="utf-8")
    print("RENDERER", len(r0), "->", len(r1))
    print("BUILDER ", len(b0), "->", len(b1))

    r = RENDERER.read_text(encoding="utf-8")
    b = BUILDER.read_text(encoding="utf-8")
    cr = {
        "grouped": "grouped_bar_chart" in r,
        "waterfall": "waterfall_chart" in r and "kind" in r,
        "heatmap": "heatmap-table" in r,
        "no double stamp": "never double-stamp" in r,
        "icon never split": "never a split fallback" in r,
        "dispatch": "Chart / icon dispatch" in r,
        "qc": "Chart labels not double-stamped" in r,
        "guard": "Honor chart / `icon_grid` layouts" in r,
        "pack": "grouped_bar_chart`, `stacked_bar_chart`" in r,
    }
    cb = {
        "layouts list": all(x in b for x in ("grouped_bar_chart", "waterfall_chart", "icon_grid", "heatmap")),
        "payload": '"kind": "total"' in b or '"kind": "total"' in b,
        "json": "grouped_bar_chart | stacked_bar_chart" in b,
        "pack": "waterfall_chart`, `heatmap`" in b or "waterfall_chart" in b,
        "renderer note": "Copilot/ChatGPT Impact Slide Renderer" in b,
        "guard matrix": "numeric matrix" in b,
    }
    print("R", cr)
    print("B", cb)
    assert all(cr.values()), cr
    assert all(cb.values()), cb
    print("PASS bake")


if __name__ == "__main__":
    main()
