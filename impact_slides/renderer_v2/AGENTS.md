# renderer_v2

## Purpose

Step 4 deterministic renderer: Builder handoff JSON → self-contained 1920×1080 HTML deck.

## Ownership

- Layout catalog, dispatch registry, recipes, charts, shell/CSS, validation schemas for handoff slides; `grouped_annex_table` holds 1–2 independently headed annex matrices without flattening peer groups
- Generated layout index consumer: `wiki/renderer_v2_LAYOUTS.md` (produced by `scripts/gen_layout_index.py`)

## Local Contracts

- Public API: `from impact_slides.renderer_v2 import render_deck` (also `python -m impact_slides.renderer_v2`)
- Single layout catalog: `layouts.py` (`CHART_LAYOUTS`, `CHARTJS_LAYOUTS`, `COVER_LAYOUTS`, `ALIASES`, `canonical()`)
- Dispatch: `layout/dispatch.py` → `LAYOUT_RECIPES` registry (no if-ladder)
- Recipe/chart packages expose **identity-preserving** facades — `LAYOUT_RECIPES` binds callables at import; wrappers break `mock.patch`
- Shared field accessors: `slide_view.py` only (`content`, `steps`, `primary_visual`, `visual_type`). `content()` must keep the `isinstance(..., dict)` guard — bare `or {}` crashes on string content
- `cli.py` paints **raw** `handoff["slides"]` after `validate_handoff` (load-bearing; do not paint validated models without fixing fallback field loss — see issue history #133)
- `validate_handoff` fallback must be non-lossy **and** total (spread raw + degrade path)
- No external chart pack; no home-directory lookups anywhere under this tree
- `grouped_annex_table` accepts 1–2 schema-validated `primary_visual.groups`; each group has a heading, headers, author-ordered rows, and optional `aggregate|child` role plus indentation. Strict hosts reject blocks below the annex readability floor; non-strict hosts stack and warn. Ordinary `annex_table` remains unchanged
- Delivery default: self-contained (`DeliveryMode.SELF_CONTAINED`)
- Chart pane titles: HTML-owned `.gl-chart-pane-title` via `charts/typography.chart_pane_title_html` / `resolve_pane_heading` (`heading` → `label` → `chart_config.title` → single series name). Optional pane `subtitle` → `.gl-chart-pane-subtitle` (dek treatment; empty reserves no space). Emit title+subtitle together through `chart_pane_headings_html` so remaining-canvas 320×240 subtracts one combined title/subtitle reservation (title-only exact boundary still succeeds; title+subtitle at that boundary strict-fails / non-strict legacy). `chart_hero_dual` accepts both fields on `primary_visual` and `secondary_visual` (right heading sits above hero facts, not per-KPI). `multi_panel` chart tiles use the same `heading`/`label`/`subtitle` resolve helpers via `chart_pane_headings_html` (#158); legitimate `top_total` remains opt-in (#90). Hosts pass `chart_host_size(kind)`. Ordinary non-chart `.gl-tile-label` stays 13px gray
- Opt-in `chart_config.typography`: explicit-only mode preserves `x_tick_font_size` 8–24, `y_tick_font_size` 8–28, `datalabel_font_size` 8–32; `mode: "auto"` uses the shared `charts/auto_typography.py` resolver for axis-based line/grouped/stacked/horizontal/combo/waterfall charts. Auto selects whole-pixel x 12–24, y 12–28, ordinary datalabel 11–32 sizes; explicit auto channels use those floors and stay local. Absent mode remains legacy Chart.js 13/13/11. Invalid group: strict raises; non-strict drops whole group + warns. Auto records plan diagnostics in `run_meta.json` and chart wrapper data attributes; sibling panes synchronize only non-explicit channels. Tick sizes are honored on Chart.js + SVG painters; stacked plans use category stack sums, combo SVG preserves its overlay, and waterfall auto sizing applies only to axes (value labels remain 18px). `datalabel_font_size` + collision only apply to ordinary-label grouped-bar/line paths, never stacked in-segment/totals or hbar chips (`charts/typography.py`)
- Plot gridlines default **off** (Chart.js `scales.*.grid.display: false` + SVG painters omit tick grid strokes). Axis baselines, tick labels, legends, measure rules, connectors, support-row borders, heatmap cell boundaries stay. Mixed negative/positive Chart.js charts get `options.plugins.zeroLine` (shell `beforeDatasetsDraw` paints `getPixelForValue(0)`); all-positive omit it. SVG negative domains keep their zero baseline. Legacy `show_gridlines` / `gridlines` keys are ignored — no public force-on. Waterfall/heatmap remain SVG/HTML, not Chart.js (`charts/chartjs.py`, `shell.py`, #152)
- `chart_config.bar_groups` on vertical grouped bars is opt-in: Chart.js receives `options.plugins.barGroups.items` and the shell plugin paints labeled category-span brackets; absent or malformed groups leave Chart.js unchanged, while SVG retains its native bracket behavior (#154)
- Outlined support rows (`secondary_visual.skin: outlined_boxes` + plot-aligned): `charts/geometry.outlined_lane_layout` reserves ≥200px label lane + ≥8px gap before first value box; wrap may extend left of `.chart-col`. Same model in static attrs and `_CHART_TABLE_ALIGN_JS` (active-only, no `shell.py` hook). Strict fails when host cannot fit; non-strict stacks + warns

## Work Guidance

- Before touching a layout: read `wiki/renderer_v2_LAYOUTS.md` (recipe, source line, tests)
- After layout/registry/recipe moves: regenerate index (`python scripts/gen_layout_index.py`) and keep `--check` green
- Do not merge `recipes` vs `freeform` `_bullets_html` variants (different caps/empty markup)
- Prefer root-cause fixes at shared accessors over per-caller guards
- Output is nondeterministic (chart canvas ids, disclosure tab ids) — normalize before byte compares:
  - `rv2-chart-[0-9a-f-]+`
  - `gl-tabs-[0-9a-f]{6,}`
  - `data-tabs-id="..."`
- Self-contained HTML is LF-stable across OS: `lib_inliner` normalizes vendored Chart.js newlines; `cli._write_presentation` uses `newline="\n"`
- `render_deck` sets typography strict/warnings contextvars; SVG collision warnings land in `run_meta.json` `warnings`

## Verification

- `python -m pytest -q` — suite must stay green
- `python scripts/gen_layout_index.py --check`
- CI also greps this tree for home-directory lookups (`Path` + `.home()`)
- For dispatch/registry and crash-degrade changes: mutation-test the new assertions (green suite alone has lied here before)

## Child DOX Index

- No child AGENTS.md under `charts/`, `layout/`, `diagram/`, `css/`, or `assets/` — those packages are implementation slices of this boundary, not separate operating contracts.
