# SPEC — renderer_v2 Amex Q1'26 IR Fidelity (sim capability gaps)

**Status:** Spec stub — locked grilling decisions recorded; full ACs live in child tickets.
**Source / evidence:** `simulation/amex_q1_2026/GAP_ANALYSIS.md` (+ `passes/pass_*/screenshots/compare_YY.png`).
**Parent epic:** GitHub issue (created from this stub). Children filed F1–F15 (merged where noted).
**Relation to MVP1:** MVP1 (P0–P5) is closed. This epic is the sim-driven capability-gap backlog that MVP1 surfaced but did not address. It is **not** MVP2 — it is a fidelity backlog prioritized by the Amex Q1'26 IR replication.

## Locked decisions (grilling session Q1–Q12)

1. **Ticket classification = C.** One epic, children dual-labeled. **Renderer Bug** (`bug`) = broken/inconsistent behavior on an *existing* surface (path-split, ignored config, wrong geometry on supplied data, no-op on a layout that claims support). **Renderer Enhancement** (`enhancement`) = missing first-class layout/recipe/asset/painter. Missing layout ≠ bug.
2. **One epic.** Parent issue holds the F-map + waves; points to `GAP_ANALYSIS.md`.
3. **Full catalog filed** — all F1–F15 become tickets now (some deferred/blocked).
4. **Granularity = B (merge couples).** `F1+F2+F15` → one "IR line-chart contract" ticket (one handoff surface, two painters). `F3` separate. Rest 1:1. ~13 children.
5. **Blocking = soft waves (B).** Parallel within a wave; next wave blocked only on the prior wave's *critical parent*. Exception: Wave 1 (tables) does **not** wait on Wave 0 (charts) — tables need no chart code. Edges are priority gates, not hard code deps; relax if more parallelism is wanted.
6. **Bug/enhancement split** per the table below (F12 and F13 = `enhancement`).
7. **F14 is a general Chrome Level** (Boardroom full default vs stage-only/minimal), **not** an Amex-only "IR mode." Boardroom remains default; minimal is an optional delivery choice for parity/export hygiene.
8. **Done bar = C.** Contract tests (handoff fixture → assert DOM/SVG/Chart-config markers) + a human visual-check checklist citing `compare_YY.png`. **No CI MAE** (white-biased per gap doc caveats).
9. **Chart.js is canonical** for IR house style. SVG stays static fallback (`<noscript>`/export) and need not match every IR cue.
10. **`chart_config` minimal extension (A).** Honor already-defined fields (`y_axis_min/max/ticks/unit/unit_position/label`, `series_styles` `solid`/`dashed`, `series_colors`, `annotation`); add only `point_labels` and `force_ticks`. No new IR namespace; no `chart_config.series[]` rewrite.

## Ticket map

| # | Ticket | F-id | Label | Wave | Critical parent of wave? |
|---|--------|------|-------|------|--------------------------|
| 1 | IR line-chart contract: `chart_config` parity + annotation + forced ticks | F1+F2+F15 | bug | 0 | **yes (W0)** |
| 2 | Below-axis negative stacked bars (reserve release) | F3 | bug | 0 | no |
| 3 | Floating inset KPI / `key_stats` on `data_table` expense layout | F9 | bug | 1 | no |
| 4 | Pill-column comparison table layout | F4 | enhancement | 1 | **yes (W1)** |
| 5 | Chart \| hero-KPI dual card layout | F5 | enhancement | 2 | **yes (W2)** |
| 6 | Brand cover + section/trailing divider assets | F6 | enhancement | 3 | **yes (W3)** |
| 7 | IR bullet sheet + inline rich-text spans | F7 | enhancement | 3 | no |
| 8 | IR guidance / statement card recipe | F8 | enhancement | 3 | no |
| 9 | Broken / discontinuous y-axis painter | F10 | enhancement | 4 | no |
| 10 | Multi-region / multi-chart freeform host | F11 | enhancement | 4 | **yes (W4)** |
| 11 | Dense widescreen annex table packing | F12 | enhancement | 4 | no |
| 12 | Handoff-native theme/token map through CLI | F13 | enhancement | 5 | no |
| 13 | Presentation chrome level (Boardroom default vs stage-only) | F14 | enhancement | 5 | no |

## Waves (priority order; soft blocking)

- **Wave 0 (charts bugs):** #1 ∥ #2 — frontier.
- **Wave 1 (tables):** #3 ∥ #4 — frontier (do not block on Wave 0).
- **Wave 2:** #5 — blocked by #4 (W1 critical).
- **Wave 3 (brand/chrome):** #6 ∥ #7 ∥ #8 — blocked by #5 (W2 critical).
- **Wave 4 (specialized boards):** #9 ∥ #10 ∥ #11 — blocked by #6 (W3 critical).
- **Wave 5 (shell plumbing):** #12 ∥ #13 — blocked by #10 (W4 critical).

## Out of scope for this epic

- MVP2 roadmap commitment (this is a fidelity backlog, not a versioned release).
- CI visual-regression / MAE thresholds (deferred until a non-white-biased metric exists).
- Rewriting `chart_config` into a `series[]` object model (blast radius too large; minimal extension only).
- A second Amex-specific brand skin (F14 is a general chrome level, not a brand fork).

## Further notes

- Every child ticket body cites: the F-id(s), the PDF slide index, and `pass_XX/screenshots/compare_YY.png` from the gap doc.
- Glossary terms added to `CONTEXT.md` this session: **Type (A) Divergence**, **Type (B) Divergence / Capability Gap**, **Renderer Bug**, **Renderer Enhancement**, **Chrome Level**.
- Blocking uses body-top `Blocked by: #n` lines (+ mirror comments) per `docs/agents/issue-tracker.md`, since the native dependencies endpoint returns 404 on this repo.
