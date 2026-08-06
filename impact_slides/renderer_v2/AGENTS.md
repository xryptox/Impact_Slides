# renderer_v2

## Purpose

Step 4 deterministic renderer: Builder handoff JSON → self-contained 1920×1080 HTML deck.

## Ownership

- Layout catalog, dispatch registry, recipes, charts, shell/CSS, validation schemas for handoff slides
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
- Delivery default: self-contained (`DeliveryMode.SELF_CONTAINED`)
- Chart pane titles: HTML-owned `.gl-chart-pane-title` via `charts/typography.chart_pane_title_html` (recipe label → `chart_config.title` → single series name). Hosts pass `chart_host_size(kind)` so remaining-canvas 320×240 is enforced (strict fail / non-strict legacy). Ordinary non-chart `.gl-tile-label` stays 13px gray
- Opt-in `chart_config.typography` (`x_tick_font_size` 8–24, `y_tick_font_size` 8–28, `datalabel_font_size` 8–32): absent → legacy Chart.js 13/13/11. Invalid group: strict raises; non-strict drops whole group + warns. Tick sizes honored on Chart.js + SVG painters (grouped/stacked/line/combo/hbar). `datalabel_font_size` + collision only on ordinary-label layouts (`grouped_bar_chart` / `line_chart` with `point_labels`) — not stacked in-segment/totals or hbar chips (`charts/typography.py`)

## Work Guidance

- Before touching a layout: read `wiki/renderer_v2_LAYOUTS.md` (recipe, source line, tests)
- After layout/registry/recipe moves: regenerate index (`python scripts/gen_layout_index.py`) and keep `--check` green
- Do not merge `recipes` vs `freeform` `_bullets_html` variants (different caps/empty markup)
- Prefer root-cause fixes at shared accessors over per-caller guards
- Output is nondeterministic (chart canvas ids, disclosure tab ids) — normalize before byte compares:
  - `rv2-chart-[0-9a-f-]+`
  - `gl-tabs-[0-9a-f]{6,}`
  - `data-tabs-id="..."`
- Cross-worktree HTML diffs are unreliable (CRLF on vendored Chart.js); toggle sources in one worktree
- `render_deck` sets typography strict/warnings contextvars; SVG collision warnings land in `run_meta.json` `warnings`

## Verification

- `python -m pytest -q` — suite must stay green
- `python scripts/gen_layout_index.py --check`
- CI also greps this tree for home-directory lookups (`Path` + `.home()`)
- For dispatch/registry and crash-degrade changes: mutation-test the new assertions (green suite alone has lied here before)

## Child DOX Index

- No child AGENTS.md under `charts/`, `layout/`, `diagram/`, `css/`, or `assets/` — those packages are implementation slices of this boundary, not separate operating contracts.
