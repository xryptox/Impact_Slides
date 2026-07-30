# Renderer v2 — Agent-Usability Refactor Hotspots

**Date:** 2026-03-28
**Scope:** `impact_slides/renderer_v2`
**Focus:** Make the codebase cheaper for agents to navigate, edit, and extend — not a full redesign.

Public surface is fine (`render_deck` only). Pain is **where agents have to edit**.

---

## P0 — biggest agent tax

| Area | Why it hurts agents | Lazy fix |
|------|---------------------|----------|
| **`layout/dispatch.py` ~40-branch if-ladder** | Adding/changing a layout = hunt string + wire call. No single map. Chart layouts double-listed (`is_chart_layout` **and** extra `in (...)`). `icon_grid` handled twice. | One `LAYOUT_RECIPES: dict[str, Callable]` (+ aliases). Export it. Dispatch becomes lookup + fallback. |
| **`layout/recipes.py` ~2.6k / 41 `render_*`** | Every layout change loads the whole catalog. Helpers + recipes mixed. | Split by family only: `recipes/text.py`, `charts_wrap.py`, `diagrams.py`, `process.py`, `_helpers.py`. Keep `recipes/__init__.py` re-export so imports stay stable. **Don’t** invent a recipe framework. |
| **`charts.py` ~2.5k** | ChartJS configs, SVG builders, geometry, pack soft-import, callouts, icon_grid — one file. | Split: `chart_svg.py`, `chart_js.py`, `chart_geom.py`, keep `charts.py` as façade (`build_chart_html`, `is_chart_layout`). |
| **Layout catalog triplicated** | `schemas.py` Literals ≈52, dispatch strings ≈45, `_CHART_LAYOUTS` / `_CHARTJS_LAYOUTS`, plus `COVER_LAYOUTS` in `load.py`. Drift is silent. | One `layouts.py` with `LAYOUT_TYPES`, `CHART_LAYOUTS`, `ALIASES`. Schemas/dispatch/features import it. |
| **Validation discarded** | `cli.py`: `_validated_slides, errs = validate_handoff(...)` then paints **raw** `handoff["slides"]`. Schemas lie to agents about the runtime contract. | Paint validated models (or `.model_dump()`). One-line intent fix, big trust win. |

---

## P1 — navigation / contract clarity

| Area | Issue | Lazy fix |
|------|--------|----------|
| **No layout index for agents** | Agent must grep 5 files to answer “what does `pill_comparison` need?” | Tiny `LAYOUT.md` or docstring table: `layout_type → recipe fn → required fields → fixture`. Or generate from the registry. |
| **Slide field access ad hoc** | `_content`, `_vs_steps`, `_so_what`, `_steps` (charts), freeform copies of `_bullets_html` | One `slide_view.py` (`content()`, `steps()`, `so_what()`, `sources()`). Delete duplicates. |
| **Soft-import pack path** (`charts._find_pack_path`) | Walks `~/Documents/realworld_test/...` — machine-local, invisible. Agents “fix” charts by editing fallbacks that never run if pack exists. | Drop external path hunt. Vendor or drop pack; one in-repo module only. |
| **`shell.py` 434 + giant HTML/JS strings** | Deck chrome + runtime JS buried in Python strings. | Extract JS to `assets/deck.js` (inline at build — you already do fonts that way). |
| **Fail-open defaults** | Unknown layout → `render_split` with no loud breadcrumb in output/meta. | Always log + stamp `data-layout-fallback` / run_meta. Agents need the signal. |

---

## P2 — worth doing later (not first)

- **`diagram/builder.py`**: scene fns are OK size; fine as-is. Only split if a scene grows past ~150 lines.
- **Wave tests** (`test_wave1a`…`4b`) are good seams — keep; add one fixture per layout next to the registry, not more waves.
- **Wiki SPECs** are many and historical (`amex_fidelity_r*`). Agent noise. One `wiki/renderer_v2_CURRENT.md` pointer > reading 15 SPECs.
- **`regions.py` / `strip.py` / `disclosure.py` / `features.py`**: already deep-ish. Leave them.

---

## What *not* to refactor

- Don’t build a plugin/recipe class hierarchy.
- Don’t merge charts into recipes (opposite direction).
- Don’t rewrite CSS token system for agent-nav — already split under `css/`.
- Don’t touch test waves while splitting files; re-export keeps them green.

---

## Suggested order (smallest → most leverage)

1. **Registry in `dispatch.py`** (delete the ladder; single catalog source starts here).
2. **Paint validated slides** in `cli.py`.
3. **`slide_view` helpers** — kill accessor dupes.
4. **Kill external chart-pack path**.
5. **Split `recipes.py` / `charts.py` by family** (façade keeps imports).
6. **One layout index doc** (or generated from registry).

---

## Agent-usability score (current)

| Module | Agent-edit cost |
|--------|-----------------|
| `cli`, `load`, `disclosure`, `features`, `regions`, `strip` | Low |
| `freeform`, `diagram/*`, `schemas` | Medium |
| `dispatch` | High (ladder) |
| `recipes.py`, `charts.py` | Very high (god files + hidden pack) |

---

## Agent tool-call efficiency

The rankings above optimise **maintainability**. Tool-call efficiency is a different
objective and re-orders the list. Recorded separately rather than overwriting, because
both views are valid for different readers.

### The two cost axes

Agent cost splits in two, and they trade against each other:

| Axis | What drives it | What makes it worse |
|------|----------------|---------------------|
| **Calls** | round trips to *locate* the right place | many small files with no index |
| **Tokens** | context burned once you are there | few huge files |

Big files are **cheap in calls, expensive in tokens**. Many small files are
**cheap in tokens, expensive in calls**. So "split `recipes.py`" does *not* by itself
improve tool-call efficiency — it converts token cost into call cost. It only pays off
once an index tells the agent which file to open.

**Therefore: the index is a prerequisite for the split, not a follow-up.**

### Re-ranked by calls saved per task

| # | Item | Calls saved | Rank in maintainability list |
|---|------|-------------|------------------------------|
| 1 | **Generated layout index** (`layout_type → fn → file:line → fixture → test`) | 4–6 → 1 | #6 (too low) |
| 2 | **Registry in dispatch** | 2 → 1, and makes #1 generable | #1 (agrees) |
| 3 | **Kill external chart-pack path** | high *variance* saver; prevents ~10-call confusion loops | #4 |
| 4 | **Single layout catalog** | kills the edit-1-of-3 → test-fail → re-grep loop | #4 |
| 5 | `slide_view` helpers | ~1 | #3 |
| 6 | Split god files | **negative** without #1; mildly positive with it | #5 (too high) |
| 7 | Paint validated slides | ~0 — correctness win, not a call win | #2 (too high) |

### Evidence for #1

Measured while reviewing this doc:

- "Which test covers `pill_comparison`?" → required a grep; answer was
  `tests/test_renderer_v2_charts_js.py`, which is not guessable from the name.
- `source_deep_dive` is covered in two unrelated files
  (`test_visual_regression_deck.py`, `test_wave4b_layouts.py`).

That grep expedition repeats on **every** layout task. It is the single most
repeated avoidable cost in the repo.

### Two taxes the maintainability view omits

| Tax | Measured | Why it is an agent problem |
|-----|----------|----------------------------|
| **`README.md` is 72 KB** | 73,749 bytes at repo root | Largest single-file context tax, and it is the first file an agent opens. Split: thin README + `docs/`. |
| **`wiki/` holds 61 files** | many superseded (`amex_fidelity_r2..r5`) | Every repo-wide `rg` returns dead guidance formatted like current guidance. This is active misinformation risk, not untidiness. |

### Design constraint discovered

Recipe signatures are **not** uniform, which shapes the registry:

- 37 recipes: `(slide, total, notes, active=False)`
- 4 recipes take `use_chartjs`: `render_chart`, `render_dual_chart`,
  `render_chart_hero_dual`, `render_multi_panel`
- `brand_divider` reuses `render_brand_cover` with `divider=True`

So a naive `dict[str, Callable]` is not sufficient. Use `functools.partial` for bound
kwargs (stdlib, rung 3) plus one explicit frozenset for the chartjs-aware layouts.
Do **not** solve this by runtime signature inspection — that is the clever-at-3am option.

---

## Refactor plan — lean calls, precise context

**Invariant for every step:** `python -m pytest -q` stays at the baseline of
**1296 passed, 15 skipped**. Baseline verified before planning. No step changes
rendered HTML unless explicitly stated.

Each step is one commit, independently revertable, ordered so every step makes the
next one cheaper.

### Step 1 — `layouts.py`: one catalog

**Why first:** every later step imports from it.

New `impact_slides/renderer_v2/layouts.py`:

```python
LAYOUT_TYPES: frozenset[str]      # all valid layout_type values
CHART_LAYOUTS: frozenset[str]     # the 8 chart layouts
CHARTJS_LAYOUTS: frozenset[str]   # chartjs-capable subset
COVER_LAYOUTS: frozenset[str]     # moved from load.py
ALIASES: dict[str, str]           # cover→title_or_opening, table→data_table, metric→metric_dashboard
```

Then point `charts.py`, `load.py`, `features.py` at it. Keep old names as
re-export aliases so no caller changes.

**Done when:** tests green, and `rg 'frozenset' impact_slides/renderer_v2` shows layout
sets defined in exactly one file.

### Step 2 — registry replaces the if-ladder

In `layout/dispatch.py`:

```python
from functools import partial

LAYOUT_RECIPES: dict[str, Callable] = {
    "title_or_opening": recipes.render_title,
    "split_text_visual": recipes.render_split,
    "brand_divider": partial(recipes.render_brand_cover, divider=True),
    ...
}
_PASSES_CHARTJS = frozenset({"chart", "dual_chart", "chart_hero_dual", "multi_panel"})
```

Dispatch body becomes: resolve alias → look up → call with `use_chartjs` only when the
layout is in `_PASSES_CHARTJS` → fall back to `render_split`.

Also fix while here: `icon_grid` currently handled twice, and chart layouts are listed
both in `is_chart_layout` and an inline tuple. Both collapse into the registry.

**Done when:** tests green, zero `if lt ==` remaining in `dispatch.py`, and
`LAYOUT_RECIPES` is exported.

### Step 3 — generated layout index (the payoff step)

`scripts/gen_layout_index.py`, ~30 lines, emitting `wiki/renderer_v2_LAYOUTS.md`:

| layout_type | recipe | source | fixture | test |
|---|---|---|---|---|

Implementation notes:
- Walk `LAYOUT_RECIPES`; unwrap `functools.partial` via `.func` before `inspect`.
- `inspect.getsourcefile` + `getsourcelines()[1]` gives `file:line`.
- Test column: `rg -l <layout_type> tests/` — cheap and good enough.

**Generated, never hand-written.** A hand-maintained index becomes catalog #4 and
drifts exactly like the three this refactor is merging.

**Done when:** an agent can answer "where do I edit `pill_comparison` and which test
guards it" in **one** `read` of the index. That is the 4–6 calls → 1 win.

### Step 4 — kill the external chart-pack path

Delete `charts._find_pack_path` / `_load_pack` path-hunting into
`~/Documents/realworld_test/...`. Keep one in-repo module or drop the pack.

**Highest variance reduction in the plan.** Today, chart behaviour depends on whether
an unrelated directory exists on the machine — an agent edits a fallback that never
runs, tests pass locally and not in CI, and burns ~10 calls before noticing.

**Done when:** no `Path.home()` in `renderer_v2`, tests green.

### Step 5 — `slide_view.py`, delete accessor dupes

One module with `content()`, `steps()`, `so_what()`, `sources()`, `bullets_html()`.
Delete `_content`, `_vs_steps`, `_so_what`, `_source_names` from `recipes.py`,
`_steps` from `charts.py`, and the `_bullets_html` / `_steps_html` copies in
`freeform.py`.

**Done when:** each accessor is defined once repo-wide, tests green.

### Step 6 — split god files (now safe)

Only now, because Step 3 makes the pieces findable.

- `recipes.py` → `recipes/{text,charts_wrap,diagrams,process,_helpers}.py`
- `charts.py` → `chart_svg.py`, `chart_js.py`, `chart_geom.py`

Both keep a façade `__init__.py` / `charts.py` re-exporting the existing public names,
so the 58 test files and the wave suites need **zero** edits.

**Done when:** tests green with no test-file changes, no module over ~600 LOC, and
Step 3 regenerated so `file:line` still resolves.

### Step 7 — correctness and signal (independent of the above)

- `cli.py`: paint validated slides instead of discarding `_validated_slides` and
  painting raw `handoff["slides"]`. **May change output** — run the golden and visual
  regression suites deliberately.
- Stamp layout fallbacks: log + `data-layout-fallback` attribute + `run_meta` entry, so
  a silent `render_split` fallback is visible instead of inferred.

### Step 8 — context hygiene

- Split the 72 KB `README.md`: thin root README + `docs/`.
- Add `wiki/renderer_v2_CURRENT.md` as the single live pointer; mark superseded specs
  (`amex_fidelity_r2..r5`) as historical in a header line so greps self-identify as stale.

### Ordering rationale

1–2 build the single source of truth. 3 converts it into the artefact that collapses
locate-cost. 4 removes the worst variance. 5 removes duplicate edit sites. 6 is
deferred until 3 makes it a net win. 7 is correctness, deliberately isolated because it
can move pixels. 8 is repo-wide and independent — parallelisable.

### Explicitly out of scope

Plugin/recipe class hierarchy; dependency injection; per-layout packages; merging
charts into recipes; CSS token restructuring; new test waves. Revisit only if
steps 1–6 still leave thrash on multi-layout changes.

---

## Notes

- Skipped: full interface redesign, dependency injection, per-layout packages. Add only if registry + split still leaves thrash on multi-layout changes.
- Size snapshot at analysis time: `recipes.py` ~2593 LOC, `charts.py` ~2504 LOC, `shell.py` ~434 LOC, `schemas.py` ~411 LOC, `dispatch.py` ~173 LOC.
- Schema layout types ≈52; dispatch explicit ≈45; chart layouts = 8 (`grouped_bar_chart`, `stacked_bar_chart`, `horizontal_bar_chart`, `waterfall_chart`, `heatmap`, `icon_grid`, `line_chart`, `combo_chart`).
