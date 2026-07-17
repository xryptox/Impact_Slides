# PLAN — Impact Slide Renderer v2 (Gridlines Design System + Script)

**Status:** Phases 0–7 implemented (2026-07-13) — package `impact_slides.renderer_v2`  
**Source brief:** `gridlines_implementation.md` (2026-07-13 assessment of the Renderer prompt)  
**Target deliverable:** a **v2 Python renderer script** that implements a unified CSS Grid design system and composition model, while preserving Boardroom Earnings theme + component physics.  
**Related sources of truth:**

| Asset | Path | Role |
|---|---|---|
| Assessment / mandate | `gridlines_implementation.md` | Why + high-level what |
| LLM prompt (human path) | `Impact Slide Renderer - Copilot and ChatGPT.md` | Boardroom theme, physics, contracts |
| Mature sim generator | `realworld_test/.../live_copilot_sim/_gen_live.py` | Full Boardroom paint (~4054 LOC) |
| Charts pack | `.../live_copilot_sim/_boardroom_charts_pack.py` | Chart SVG/CSS |
| Early plan sims | `_gen_renderer.py`, `_gen_renderer_v2.py` | Pre-Boardroom generators (stale) |
| Python Step-4 fallback | `step4_builder_validator.py` | Separate PPTX/HTML path — align later |

---

## 1. Executive summary

`gridlines_implementation.md` is **not** a token-level design kit. It is an **architecture diagnosis**:

- Today the Renderer is **layout_type-driven** and uses CSS Grid **inside many special-case templates** (dual-rail, dense-2x2, icon_grid cols, comparison).
- What is missing is a **unified Grid Design System** — shared CSS variables + reusable primitives (`.grid`, `.grid-2`, `.card`, named `grid-template-areas`) — so layouts **compose** rather than each re-declare Grid CSS.
- Goal of v2: keep strict render contracts (fixed 1920×1080, no face E####, notes-only bridges, packing, Boardroom) but **re-platform** HTML/CSS generation on composable grid primitives.

**v2 renderer script** = deterministic Python (not LLM) that:

1. Reads approved `builder_handoff.json` (+ optional seed register).  
2. Applies slide-1 hard-title and Boardroom physics contracts.  
3. Emits `presentation.html` / `slide_notes.md` / `evidence_manifest.json` using a **central `gridlines` CSS module** + composition helpers.  
4. Becomes the regression/bake target parallel to (then gradually part of) the Renderer prompt.

---

## 2. Key design rules extracted from `gridlines_implementation.md`

### 2.1 Current strengths to keep

- CSS Grid already used in places.
- **layout_type-driven** mapping from Builder fields → HTML.
- Dual-rail `1fr 1fr`, metric `dense-2x2`, icon_grid `cols-2/3`, comparison grids.
- Fixed **1920×1080** stage, frontend-slides single-file model.
- Strict deterministic content mapping (anti-AI-slop).

### 2.2 Gaps the doc names explicitly

| Gap | Doc language |
|---|---|
| No unified system | “does **not** have a unified, reusable **Grid design system**” |
| No primitives | missing `.grid`, `.grid-2`, `.card`, named areas |
| Fragmented CSS | “Grid usage is fragmented across layout types” |
| Rigid templates | “collection of special templates” not composable foundation |
| Prompt bloat | “Prompt is very long because of per-layout rules” |
| step4 lag | aligning `step4_builder_validator.py` is Medium, not blocking |

### 2.3 Recommended directions (from doc)

1. **Grid Design System section first** — CSS vars + reusable classes; all layouts use them.  
2. **Composition over proliferation** — fewer high-level intentions built from stronger primitives (`two_col`, `card_grid`, `metric_grid`, named areas).  
3. Promote **`grid-template-areas`** + named slots for complex evidence slides.  
4. **Keep** no face E####, packing modes, notes-only bridges, fixed stage, Boardroom contracts already in prompt.  
5. Priority: Foundation + mapping **High**; reduce layout_type count **Medium**; step4 align **Medium**.

### 2.4 What the brief does *not* specify (must design in plan)

Exact token tables, named area vocab, Python packaging, CLI, schemas for “dynamic” placement, migration path from current physics, test goldens. The plan invents those below, compatible with Boardroom (`ef2eed9` / `edf1c81` prompt bake).

---

## 3. Relation to current Boardroom stack (gaps / conflicts)

### 3.1 Layer map today

```
Builder handoff (layout_type + content + visual_spec)
        │
        ├─ LLM path → Impact Slide Renderer prompt (Boardroom sole theme + physics text)
        │
        ├─ live_copilot_sim/_gen_live.py (full specialty render_* + huge CSS string)
        │
        ├─ _gen_renderer_v2.py (older simulation; Boardroom freeform not complete)
        │
        └─ step4_builder_validator.py (HTML partial + PPTX; buggy icon_grid/data_table)
```

### 3.2 Strengths already beyond the brief

Post-bake Renderer prompt already owns:

- Sole **Boardroom Earnings** theme (no Phase 0 / font presets).  
- Component physics: dual-rail hats, table-as-KPI, dense-2x2, vertical timeline years, multi-quote stack, process-outcome, spoken bridge off-face.  
- Chart pack contracts.  

live_sim implements most of that in Python; it is the **paint reference**, not a grid system.

### 3.3 Conflicts / friction with a pure “flexible gridlines placement” reading

| Tension | Decision for v2 |
|---|---|
| Doc wants less rigid templates | **Keep** `layout_type` as the normal Builder contract; implement it *via* primitives, do not require Builder to send freeform areas yet |
| Doc wants arbitrary bloc placement | Phase 1 = **internal** composition only; optional future `grid_areas` carrier later |
| live_sim CSS is ad-hoc specialty selectors | **Extract** shared primitives; re-express specialty as thin layouts over primitives |
| Prompt is human-facing length vs script | Script is source of **CSS truth**; prompt later cites “use v2 gridlines CSS” and deleted duplicate selectors |
| Charts pack is SVG-centric | Keep; wrap chart frame in `.gl-region--hero` / `.gl-card` |

### 3.4 Design decision (locked for plan)

**Hybrid,** not pure freeform:

> **v2 = hybrid skeleton + named-area slots.**  
> Builder still chooses `layout_type`. Renderer v2 maps each type to a **recipe** built from Grid primitives. Optional extended handoff field `content.regions` / `visual_spec.grid` may override slot fill later; Phase 1 ignores unknown keys.

This satisfies the brief’s maintainability/density goals without breaking A→B→R handoffs.

---

## 4. Recommended architecture — v2 renderer script

### 4.1 Package layout (new)

Prefer a small package under the repo (not another 4k-line monofile):

```
impact_slides/
  renderer_v2/                 # NEW
    __init__.py
    cli.py                     # entry: python -m impact_slides.renderer_v2
    load.py                    # handoff + seed load / slide-1 normalize
    strip.py                   # E#### scrub, clean_quote_body, dek merge
    notes.py                   # spoken prose assembly (bridge notes-only)
    manifest.py                # evidence_manifest + slide_notes.md
    shell.py                   # stage HTML + DECK_META JS + sprite inject
    css/
      tokens.css               # Boardroom :root only
      viewport.css             # fixed stage (viewport-base)
      gridlines.css            # ★ Grid Design System
      components.css           # cards, hats, KPI, process, quote, table, chart frame
    layout/
      dispatch.py              # layout_type → recipe
      recipes.py               # title, split, metric, table, process, compare, quote, icon, charts
      regions.py               # named-area templates + fill helpers
    charts.py                  # adapt _boardroom_charts_pack builders (import or copy)
tests/
  test_renderer_v2_gridlines.py
  fixtures/renderer_v2/...
```

**Thin CL shim (optional):** `step4_renderer_v2.py` at repository root for one-command runs, similar to `step1_preprocessor_v4.py` pattern.

### 4.2 Inputs / outputs

**Inputs**

| Arg | Required | Notes |
|---|---|---|
| `--handoff path/to/builder_handoff.json` | yes | presentation + slides[] |
| `--seed path/to/evidence_register_seed.json` | preferred | for note rigor / ID verify |
| `--out dir` | yes | write artifacts |
| `--sprite path` | optional | Lucide sprite HTML fragment; default extract from Renderer prompt or ship embedded |
| `--style-preset` | optional | fixed default `BoardroomEarnings` only |

**Outputs (always)**

1. `presentation.html` — single self-contained file  
2. `slide_notes.md`  
3. `evidence_manifest.json` with `style_preset: "BoardroomEarnings"`  
4. `run_meta.json` (optional) — generator version, layout recipe keys used  

### 4.3 Core data flow

```
builder_handoff.json
   → normalize(slide-1 title force, renumber, strip face E####)
   → for each slide:
         recipe = DISPATCH[layout_type]
         model = recipe.build_view_model(slide)   # dek, regions, items, insights
         html_body = recipe.render(model)          # uses gl-* primitives only
         notes = notes.build(slide, next_title)
   → shell.wrap(bodies, css_concat, sprite, DECK_META)
   → write three artifacts + validate(internal checks)
```

### 4.4 Grid Design System (`gridlines.css`) — proposed primitives

Central tokens also live in Boardroom `:root` (already defined). Grid system **adds layout primitives only**, not a second palette.

```css
/* Spacing slots on the 1920×1080 face (pack-from-top) */
.gl-slide {
  display: grid;
  grid-template-rows: auto 1fr auto;   /* header / main / footer */
  grid-template-areas:
    "header"
    "main"
    "footer";
  height: 100%;
  padding: var(--pad-top) var(--pad-x) var(--pad-bottom);
  box-sizing: border-box;
  align-content: start;
}
.gl-header { grid-area: header; }
.gl-main   { grid-area: main;   min-height: 0; align-content: start; }
.gl-footer { grid-area: footer; }

/* Composition grids */
.gl-grid        { display: grid; gap: var(--gap-md); align-content: start; width: 100%; }
.gl-grid-2      { grid-template-columns: 1fr 1fr; }
.gl-grid-3      { grid-template-columns: repeat(3, minmax(0,1fr)); }
.gl-grid-4      { grid-template-columns: repeat(4, minmax(0,1fr)); }
.gl-grid-dense-2x2 { grid-template-columns: 1fr 1fr; grid-auto-rows: auto; }

/* Named multi-panel frames used by complex slides */
.gl-areas-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-areas: "lead lead" "arg proof";
  gap: 40px 22px;
  align-items: start;
}
.gl-areas-split .gl-lead  { grid-area: lead; }
.gl-areas-split .gl-arg   { grid-area: arg; }
.gl-areas-split .gl-proof { grid-area: proof; }

.gl-areas-cover {
  display: grid;
  grid-template-rows: 62% 38%;
  grid-template-areas: "band-navy" "band-blue";
  height: 100%;
}

/* Card / region */
.gl-card {
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: var(--card-radius);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 0;                 /* hats full-bleed */
  flex: 0 0 auto;             /* pack-from-top; no stretch of short lists */
}
.gl-card-hat {
  background: var(--navy);
  color: #fff;
  font-size: 26px;
  font-weight: 700;
  min-height: 64px;
  padding: 16px 22px;
}
.gl-card-body { padding: 6px 22px 16px; }
```

**debug (optional CLI flag):** outline areas with light rules (not on by default) for QA.

### 4.5 Composition recipes (layout_type → primitives)

| `layout_type` | Recipe skeleton (using gl-*) |
|---|---|
| `title_or_opening` | `gl-areas-cover` + title stack in navy band |
| `split_text_visual` | `gl-slide` + `gl-areas-split` (lead/arg/proof) dual hats |
| `metric_dashboard` | `gl-grid` dense-2x2 when n==4 else row; each KPI = `gl-card` variant |
| `data_table` | short 2-col → same metric recipe; else table in `gl-card` frame |
| `comparison_grid` | `gl-grid-2` of risk `gl-card` (navy hat) |
| `icon_grid` | `gl-grid-2/3` of icon tiles |
| `full_process_flow` | horizontal `gl-grid` of step cards + optional outcome row spanning full |
| `timeline`/`roadmap` | vertical list (1-col grid) with rail chrome (physics undue purely flex) |
| charts / heatmap | `gl-card` `.chart-frame` wrapping pack SVG/table |
| `quote_card` | single wide card or `gl-grid` 1-col stack of compact cards |
| `other` | remap via `primary_visual.type` then split recipe |

**Principle:** recipe code may add layout-specific chrome classes, but **must not** invent a third parallel grid system (no duplicate custom `display:grid` without `gl-` base).

### 4.6 Content mapping (keep Boardroom physics)

Port as pure functions (from live_sim / prompt bake):

| Function | Behavior |
|---|---|
| `chosen_dek(slide)` | one under-title line |
| `strip_eids(text)` | face scrub |
| `clean_quote_body` | first spoken span |
| `pair_comparison` | Head:body ¦ step+bullet[i] ¦ bullets — no house bodies |
| `split_step_copy` | year/date on timeline kicks |
| `right_panel_model` | fact-tiles vs proof-list vs icon fallback |
| `argument_kicker` / `panel_kicker` | dynamic hats |
| `table_as_kpi?` | ≤2-col × ≤6 rows |
| `is_closed_loop_outcome` | last process step pull-out |
| `build_spoken_notes` | notes claim language; bridge off-face |

### 4.7 CLI sketch

```bash
python -m impact_slides.renderer_v2 \
  --handoff .../builder_handoff.json \
  --seed .../evidence_register_seed.json \
  --out .../renderer_v2_out
```

Exit non-zero if validation hard-fails (missing slides, face E#### residual, missing Boardroom tokens).

---

## 5. Phased implementation

### Phase 0 — Scaffold (0.5 day)

- Create `impact_slides/renderer_v2/` package + empty modules.  
- `css/tokens.css` + `viewport.css` extracted from Renderer Brand & Theme / stage.  
- `shell.py` emits empty deck with working fitStage JS + Notes.  
- CLI loads handoff and dumps slide inventory.

**Exit:** 1 blank white Boardroom slide + nav works.

### Phase 1 — Grid Foundation (1 day)

- Implement `gridlines.css` primitives as above.  
- Implement `gl-slide` header/main/footer for all layouts.  
- `components.css` for `gl-card`, RPC hats, KPI value/label Boardroom type scale.  
- Unit-test CSS class vocabulary presence (string assertions on rendered fragment).

**Exit:** metric + comparison + icon_grid can render with **only** gl- classes (no specialty bare `display:grid` orphans).

### Phase 2 — Core recipes (2 days)

Migrate live_sim physics for:

1. cover bi-band  
2. split dual-rail + kickers + fact panel  
3. metric dense-2x2  
4. table-as-KPI / true table  
5. comparison pairing  
6. process horizontal + outcome  
7. timeline vertical + year parse  
8. quote single/stack  

**Do not** rewrite business logic — port contracts; re-skin as gl-*.

**Exit:** Re-render AmEx live_copilot_sim builder handoff; visual parity checklist (≥ checklist §7).

### Phase 3 — Charts + icon_grid (0.5–1 day)

- Import/adapt `_boardroom_charts_pack.py` into `charts.py` (or soft-import path).  
- Wrap outputs in `gl-card` chart frames.  
- icon_grid as pure `gl-grid` tiles.

**Exit:** `renderer_live_charts` builder payloads still ALL_PASS style checks.

### Phase 4 — Notes / manifest / strip (0.5 day)

- Port spoken notes rules (no leave-slide cadence, no readiness sticky).  
- Manifest with style_preset + evidence list.  
- Slide_notes.md writer.

### Phase 5 — Validation harness + golden (1 day)

- `tests/test_renderer_v2_gridlines.py`  
  - class presence for every recipe  
  - zero face E####  
  - Boardroom hex tokens present  
  - n==4 metric → dense-2x2 class  
  - split dual hats  
  - multi-quote stack  
  - no face story-bridge elements  
- Fixture = slim 8-slide chart/split handoff.  
- Optional visual screenshot later (not required Phase 5).

### Phase 6 — Prompt alignment (after script green)

- Shorter Renderer section: “Layout recipes are composed from Grid Design System; full CSS ships as/from renderer_v2 tokens.”  
- Do **not** delete physics contracts—reference primitives.  
- Medium: inventory which step4 HTML paths would share selectors (no rewrite yet unless user asks).

### Phase 7 — Optional freeform areas (future)

Only if Builder monetizes:
```json
"visual_spec": {
  "grid": {
    "template_areas": ["header header", "main aside"],
    "columns": "1.2fr 0.8fr",
    "slots": { "main": {"kind":"bullets"}, "aside": {"kind":"metric_stack"} }
  }
}
```
Out of Phase 1–5 scope.

---

## 6. File paths to create / modify

### Create

| Path | Purpose |
|---|---|
| `impact_slides/renderer_v2/**` | Package (see §4.1) |
| `tests/test_renderer_v2_gridlines.py` | Contract tests |
| `tests/fixtures/renderer_v2/mini_handoff.json` | Slim builder fixture |
| `step4_renderer_v2.py` (optional shim) | CLI entry for users |
| `PLAN_renderer_v2_gridlines.md` | this plan |

### Modify later (not Phase 0–1)

| Path | When |
|---|---|
| `Impact Slide Renderer - Copilot and ChatGPT.md` | Phase 6 — section Grid Design System; de-dupe ad-hoc grid CSS |
| `Impact Slide Builder - Copilot and ChatGPT.md` | only if new optional `grid` field; **not required Phase 1** |
| `step4_builder_validator.py` | Medium priority alignment | 
| README | Document `python -m impact_slides.renderer_v2` |

### Explicitly do **not** modify

| Path | Why |
|---|---|
| `step1_preprocessor_v2_full.py` / `v3` | frozen baselines |
| `SESSION_HANDOFF.md` | untracked |
| live_copilot_sim artifacts | remain reference; may soft-import charts pack only |

---

## 7. Validation checklist (v2 script hard gates)

| # | Check | Fail if |
|---|---|---|
| 1 | Fixed 1920×1080 + working fitStage (pixel translate) | miss / `-50%` center pattern |
| 2 | Boardroom tokens only (`#00175A`, `#006FCF`, Source Sans 3 + IBM Plex) | other font stacks |
| 3 | Every non-cover recipe body built on `.gl-*` primitives | layout reinvents raw grid zero base class |
| 4 | Zero face `E####` | regex residual |
| 5 | Zero face story-bridge / Why-What-How tags | residual class or text |
| 6 | Metric n==4 → dense-2×2 | 1×4 still present |
| 7 | Split dual-rail hats when argument-led with proof data | loner icon only |
| 8 | Fact tiles entity-primary (not dual US) | region-as-hero |
| 9 | Short 2-col table → KPI | wash table |
| 10 | Timeline 4-step vertical year kicks | 2×2 faux grid |
| 11 | Comparison no house body invention | “Keep this open…” |
| 12 | Multi-quote stack shows all quotes | only first |
| 13 | Charts: one label per value, no double pill | stacked 55/55 |
| 14 | Notes: no readiness sticky / leave-slide cadence | residual phrases |
| 15 | Manifest IDs ⊆ seed; style_preset BoardroomEarnings | invent / missing |
| 16 | Controls + Notes toggle work | dead UI |

Soft: visual parity with live_copilot_sim on AmEx 15 slides (human QA).

---

## 8. Open questions / risks

| # | Question | Default if unanswered |
|---|---|---|
| 1 | Is v2 script **authoritative paint** for production, or **dev mirror** of the LLM prompt? | **Authoritative deterministic path** for IC decks; prompt stays for Copilot Chat path |
| 2 | Should we delete / freeze `_gen_renderer_v2.py`? | Keep untracked legacy; mark superseded in plan only |
| 3 | Import charts pack by path vs copy module into package? | Soft-import first; copy when packaging for install |
| 4 | How far to reduce public `layout_type` set in Builder now? | **Zero reduction Phase 1–5** — composition is internal |
| 5 | Named-area freeform in Builder JSON? | Defer (Phase 7) |
| 6 | Align step4 in same epic? | No — Medium follow-on |
| 7 | Risk of CSS bloat (gridlines + components + specialty) | Budget: gridlines ≤ ~8KB, components ≤ ~20KB |
| 8 | Packable as `python -m` with relative fixture paths on Windows? | Use `pathlib`, UTF-8 always; avoid heredoc generators |

**Main risk:** re-implementing live_sim specialty CSS without consolidating into `gl-*` → v2 becomes monofile 2.0. Mitigation: PR gate “no new `display:grid` outside gridlines.css without `gl-` class.”

**Secondary risk:** prompt and script drift. Mitigation: Phase 6 prompt cites package CSS as source; golden HTML snippets shared.

---

## 9. Explicit non-goals

- Replacing Copilot/ChatGPT prompt with Python in Teams (prompt remains for LLM path).  
- Implementing freeform designer drag-and-drop.  
- Rewriting Builder JSON contract or Analyst spine.  
- Deleting step4 or v1/v2 baselines.  
- Reintroducing Phase 0 font presets.  
- PPTX emitter (still deferred).  
- Live-token ChatGPT 5.5 subagent A→B→R as part of this epic.  
- Flex-stretch “fill whitespace” spacing (anti-pattern already rejected).  
- Mat / Long-table alternate themes.

---

## 10. Suggested next action when implementing

1. Approve this plan’s **hybrid** decision (§3.4) and Phase 0–2 scipe.  
2. Scaffold `impact_slides/renderer_v2` + `gridlines.css`.  
3. Port **metric + split + comparison** first (highest density payoff).  
4. Golden AmEx mini fixture before full 15-slide port.  
5. Only then Phase 6 prompt rewrite.

---

## 11. Traceability to `gridlines_implementation.md` priorities

| Doc priority | Plan phase |
|---|---|
| Unified Grid Foundation | Phase 1 |
| Composable primitives / content mapping | Phase 1–2 |
| High-density card multi-panel first-class | Phase 2 split/metric/compare/icon |
| Maintainability / shorter rules later | Phase 6 prompt notation |
| Fewer layout_types | Non-goal Phase 1–5; future composition-only internal |
| Align step4 | Out of band Medium |

---

*Implementation complete: Phases 0–4 paint path; Phase 5 gates+fixtures; Phase 6 prompt/README alignment; Phase 7 optional visual_spec.grid freeform.*

