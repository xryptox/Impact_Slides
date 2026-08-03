# Renderer v2 — Agent-Usability Refactor Hotspots

> ## ✅ COMPLETE — Steps 1–6 shipped; Steps 7–8 deliberately NOT done (2026-07-31)
>
> **Do not re-plan this work.** Everything in the plan below is either done or
> explicitly rejected. This file is kept for the analysis and rationale, not as a
> backlog. Current state lives in the code; the layout catalog is generated at
> `wiki/renderer_v2_LAYOUTS.md`.
>
> ⚠️ **Steps 7 and 8 below are superseded — read the "Steps 7–8: reassessed"
> section before acting on them.** Step 7's main item would ship a data-loss bug
> (issue #133). Most of Step 8 was measured to be unnecessary.
>
> | Step | What shipped | Where |
> |---|---|---|
> | 1 | `layouts.py` single catalog (`CHART_LAYOUTS`, `CHARTJS_LAYOUTS`, `COVER_LAYOUTS`, `ALIASES`, `canonical()`) | PR #127 |
> | 2 | `LAYOUT_RECIPES` registry replaced the ~40-branch if-ladder in `dispatch.py` | PR #127 |
> | 3 | `scripts/gen_layout_index.py` → generated `wiki/renderer_v2_LAYOUTS.md`, gated in CI | 09f632d, 3d1fdc9 |
> | 4a | In-repo `heatmap` + `waterfall` painters (`charts/matrix.py`) | PR #127 |
> | 4 | External Boardroom charts pack deleted; no `Path.home()` in `renderer_v2` | PR #127 |
> | 5 | `slide_view.py` shared accessors; `icon_grid` per-step `description` fix (#126) | PR #128 |
> | 6 | `charts.py` → `charts/` (8 modules), `layout/recipes.py` → `recipes/` (9 modules), behind facades | PR #131 |
> | — | GitHub Actions CI: layout-index gate, `Path.home()` gate, tests | fc5ec2a, 2f8d329 |
>
> **Result:** largest renderer file 2,630 → 751 lines. Test suite 1296 → 1341 passing,
> zero behaviour regressions outside the two bug fixes below.
>
> ### Bugs found and fixed en route (none had test coverage)
>
> 1. **`metric` / `table` aliases silently dropped `content.key_stats`.** Schemas
>    accepted both `layout_type` values and tests asserted them, but dispatch never
>    honoured the aliases — both fell through to `render_split`, discarding stats
>    with no error. Fixed by `ALIASES` + `canonical()` in Step 1.
> 2. **`heatmap` and `waterfall_chart` rendered `chart-empty` everywhere except one
>    dev machine.** They had no in-repo SVG painter and depended on a chart pack
>    soft-imported from `~/Documents/realworld_test/...`. Fixed in Step 4a before the
>    pack was deleted.
> 3. **`icon_grid` silently discarded per-step `description`** (#126), rendering an
>    empty `tile-body`. Fixed in Step 5, with a test pinning the spec rule that
>    *primary_visual*-level `description` must stay unrendered.
>
> ### Method note worth keeping
>
> A green suite was misleading **five** times during this work: it passed through a
> broken registry, through simulated pack deletion, through a circular parity test,
> through a dead waterfall bridge, and through all four missing `isinstance` guards.
> Mutation testing caught every one. For changes in this area, prefer:
> mutation-test the new assertions, diff rendered fixture output, and assert object
> **identity** for anything re-exported (`LAYOUT_RECIPES` binds function objects at
> import time, so a wrapper re-export makes `mock.patch` miss silently).
>
> Renderer output is **not** deterministic — three random ids per run
> (`rv2-chart-<hex>`, `data-tabs-id`, and the tabs id repeated in `name=`/`id=`/`for=`).
> Normalise all three before comparing hashes, and validate any harness by hashing the
> same unchanged tree twice.
>
> ### Deliberately NOT done
>
> - **`recipes._bullets_html` and `freeform._bullets_html` were not merged.** They look
>   like duplicates but differ in the empty case (`""` vs `'<p class="gl-empty">—</p>'`);
>   merging changes rendered HTML.
> - **P2 items below remain open by choice**: `shell.py` JS extraction, loud fallback
>   breadcrumbs (`data-layout-fallback`), painting validated models in `cli.py`, the
>   72KB root README split, and `wiki/renderer_v2_CURRENT.md`. None block agent
>   navigation now that the layout index is generated.
> - Known follow-ups tracked as issues: #129 (structlog test gap), #130
>   (`gen_layout_index.py` fails silently without ripgrep).

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


> 🛑 **SUPERSEDED — do not implement as written. See "Steps 7–8: reassessed" at the end of this file.**


- `cli.py`: paint validated slides instead of discarding `_validated_slides` and
  painting raw `handoff["slides"]`. **May change output** — run the golden and visual
  regression suites deliberately.
- Stamp layout fallbacks: log + `data-layout-fallback` attribute + `run_meta` entry, so
  a silent `render_split` fallback is visible instead of inferred.

### Step 8 — context hygiene


> ⚠️ **Mostly rejected on measurement. See "Steps 7–8: reassessed" at the end of this file.**


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

---

## Steps 7-8: reassessed (2026-07-31)

Steps 1-6 shipped. Before implementing 7 and 8 their premises were re-measured
against the post-refactor code. Both were largely wrong. Recording the evidence so
they are not resurrected from the plan text above.

### Step 7a - "paint validated slides" - REJECTED, would cause data loss

The premise is still true: `cli.py:169` validates into `_validated_slides`, then
`cli.py:175` paints raw `handoff["slides"]`. But making it paint the models would
**delete data**.

`validate_handoff` (`schemas.py:372`) replaces a failed slide with a hand-built
`SplitTextVisualSlide` copying only 4 fields. Measured drops on an unknown
`layout_type`: `disclosure`, `evidence_ids`, `evidence_sources`, `kicker`,
`packing_mode`, `source_line`, `speaker_notes`, plus `content.key_stats` and
`content.so_what`.

Those are consumed by `manifest.py:64`, `notes.py:66,74`, `load.py:62,78,80,87`.
On the committed fixture `freeform_handoff.json` (slide 2 is `layout_type: "other"`),
painting models loses the speaker notes, the packing mode, and the deck's only
`evidence_sources` entry.

So **painting raw is load-bearing, not accidental.** The plan labelled this a
"correctness win"; it is the reverse. Note it is not a pydantic `extra` issue - all
47 slide models already set `ConfigDict(extra="allow")`; the loss is purely the
manual field copy in the fallback.

Tracked as **issue #133**. Fix that first if Step 7a is ever wanted. Scope is
narrow: 0 of 49 routable layouts fail validation, so only unknown/misspelled
`layout_type` values reach the lossy path.

### Step 7b - "stamp layout fallbacks" - mostly already true

Fallbacks are no longer silent:

- unknown `layout_type` prints `[validation] slide N (x): unknown layout_type: 'x'`
- rendered HTML already carries `data-layout="split_text_visual"`
- Step 1 fixed the genuinely silent case (`metric`/`table` aliases)

Remaining real gap: `run_meta` still reports `errors: []` and `ok: True` when a
validation warning was printed, and `strict=True` does not raise on an unknown
layout. That is a change to the public API contract, so it belongs in its own
issue rather than a refactor step. No `data-layout-fallback` attribute is needed -
`data-layout` plus the warning already answers "did this fall back?".

### Step 8 - README split - REJECTED

The stated reason ("largest context tax, and it is the first file an agent opens")
is false. `AGENTS.md` (422 bytes) routes agents to `CONTEXT.md` (11 KB); the 72 KB
`README.md` is scoped to the **preprocessor** and mentions `renderer_v2` only 12
times. It is also not stale post-refactor: 0 references to the split monoliths.

Splitting 72 KB of accurate, correctly-scoped docs is churn with merge-conflict
risk and no measured agent benefit. Skipped.

### Step 8 - stale spec markers - STILL WORTH DOING

This half is real, and the refactor made it worse:

- `wiki/PLAN_renderer_v2_gridlines.md` still documents `_boardroom_charts_pack`,
  which Step 4 **deleted**. An agent grepping for chart fallbacks finds
  instructions for code that no longer exists.
- 6 overlapping `SPEC_renderer_v2_amex_fidelity{,_r2..r6}.md` files; 54 wiki files
  total. `heatmap` appears in 12 wiki files vs 8 source files - docs outnumber code
  on chart questions.

Do **not** add `wiki/renderer_v2_CURRENT.md` as originally planned: a
hand-maintained live pointer becomes another catalog that drifts, exactly the
failure this refactor spent Steps 1-3 eliminating. The cheap fix is a one-line
`> **Superseded - historical.** See X.` header on each dead spec, so repo-wide
greps self-identify as stale.
