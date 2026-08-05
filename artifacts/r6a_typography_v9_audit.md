# R6-A chart-internal typography — synthetic contract audit (#139)

**Honest scope:** this is a **synthetic 44-slide contract audit**, not a full archived-v9 handoff run.

The worktree has no archived v9 44-slide handoff/deck. Historical v8/v9 artifacts must not be modified. Therefore:

- **Completed here:** synthetic deck covering dual_chart / chart_hero_dual / multi_panel / grouped / line / stacked / combo / hbar hosts under Chart.js and SVG painters, with opt-in typography, invalid/unsupported knobs, and pane-title emission.
- **Outstanding:** full 44-slide **archived v9** audit against the real Amex v9 handoff/deck (Chart.js + SVG), enumerating clipped titles, legacy title fallbacks, rotations/skips, suppressed labels, and unsupported warnings on production content. Do that when the archived handoff is available in a GNHF/sim worktree without touching historical artifacts in-repo.

See `r6a_typography_v9_audit.json` for the last synthetic run counts.

## Repair evidence (host canvas + Chart.js collision)

- Production hosts (`dual_chart`, `chart_hero_dual`, `multi_panel`) pass `chart_host_size(...)` into `chart_pane_title_html`.
- Default viable hosts still emit 40px `.gl-chart-pane-title`.
- Tight host (monkeypatched) via `render_deck`: strict raises; non-strict → legacy title + stderr/`run_meta.warnings`.
- Chart.js collision JS walks **flat** `chart.$datalabels._labels` via `$context.datasetIndex` / `dataIndex`.
- Playwright proof: dense multi-series deck sets `data-datalabel-suppressed="N"` (N>0), keeps earlier series/category, console.warn details, no collision boot when `datalabel_font_size` absent.
