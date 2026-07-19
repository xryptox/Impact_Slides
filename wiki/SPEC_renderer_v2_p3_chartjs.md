# SPEC: Renderer v2 — P3 Chart.js Path + Static Fallback

**Status:** Engineering PRD — ready to ticket  
**Date:** 2026-07-19  
**Theme:** P3 (MVP1)  
**Scope lock:** `wiki/SCOPE_renderer_v2_mvp1.md`  
**Depends on:** P0 complete; **P1 hard prereq** (feature gate + inliner `charts` id). Soft dependency on P2 (prefer Boardroom/semantic colors in chart chrome).  
**Alignment:** D6 (Chart.js via `charts.py` + static fallback), D8 (quantitative → Chart.js), D15 (no animation focus; duration 0 / reduced-motion friendly), D3 (JS feature-gated), D1 (self-contained default)  
**Success criteria:** SC-CHART-1, SC-CHART-FALLBACK, SC-OFFLINE-1/2 (charts path), SC-SIZE-1 (charts row measurable), SC-COMPAT-1  
**Confirmed seams (user lock):** primary = `render_deck` → HTML + `run_meta`; supporting = chart HTML builder evolution + `build_head_assets` when `charts` on. **Smaller first Chart.js set: bar + line + combo only.** Current SVG remains static fallback when `charts` off or static path selected.

---

## Problem Statement

Executive decks need credible numeric storytelling. Today renderer_v2 already paints **static SVG charts** (and optional external pack paths) for several layout types, but there is no **self-contained Chart.js** interactive path, no vendored chart library behind the P1 `charts` feature gate, and no product rule that says “feature on → Chart.js; feature off / export-oriented → readable static.” Without P3, SC-CHART-1 stays unmet and the P1 gate never carries real payload for the main MVP1 viz theme.

## Solution

Evolve the existing chart paint path so that:

1. When the **`charts` feature is enabled** (auto-detect from handoff per P1, or forced), the generator **inlines a pinned Chart.js** build and emits canvas + init for a **small MVP set**: **grouped/vertical bar, line, and combo (bar+line)**.
2. When **`charts` is off**, or a **static/export-oriented path** is selected, the deck still shows **readable static content** using the **current SVG** (and existing table/matrix fallbacks where already used) — no blank holes.
3. **Animations default off** (duration 0); calm / `prefers-reduced-motion` friendly.
4. Chart.js loads **only** via the centralized inliner when `charts` is on; self-contained mode embeds bytes; CDN mode may use a documented pinned CDN URI for dev only.
5. Boardroom brand/semantic colors are preferred for series/chrome where practical (no full redesign).
6. Layout types outside the MVP Chart.js set (**stacked bar, waterfall, heatmap, icon_grid**, etc.) **keep today’s SVG/pack behavior** in P3; they may still flip the `charts` feature on for “deck needs charts” detection, but do not require Chart.js canvas in this theme unless trivially shared — **normative interactive Chart.js = bar + line + combo only**.

## User Stories

1. As a deck operator, I want chart-heavy handoffs to embed Chart.js only when charts are needed, so that non-chart decks stay small.
2. As a deck operator, I want self-contained chart decks to open offline, so that corporate VPN and air-gapped review work.
3. As a deck operator, I want CDN-dev mode to still paint charts for local iteration, so that I am not blocked without vendored files in a broken tree (dev hatch only).
4. As a deck operator, I want `features_enabled` to list `charts` when Chart.js is in play, so that support can see why HTML grew.
5. As a deck operator, I want size reporting to reflect Chart.js bytes when enabled, so that SC-SIZE-1 gains a real +charts row.
6. As a presentation author, I want existing bar/line/combo handoffs to keep working without a schema break, so that Builder output remains valid.
7. As a presentation author, I want stacked/waterfall/heatmap/icon_grid to keep rendering as today, so that P3 does not regress those layouts.
8. As a presentation author, I want suppressing `charts` to still leave readable static charts, so that I can ship no-JS-lib decks on purpose.
9. As a viewer, I want bar/line/combo charts to be legible at 1920×1080 Boardroom scale, so that live presentation works.
10. As a viewer, I want no gratuitous chart animation, so that the deck feels calm and capture-friendly (D15).
11. As a viewer, I want reduced-motion environments not to fight the deck, so that accessibility baseline holds.
12. As a viewer with JS disabled or charts feature off, I want SVG/table fallback content still visible, so that progressive enhancement holds (SC-CHART-FALLBACK, SC-IX-2 spirit).
13. As a corporate brand viewer, I want chart colors to read as Boardroom (navy/blue/ink family), so that charts do not look like a default Chart.js demo.
14. As a renderer developer, I want Chart.js config mapping owned next to existing chart geometry/data extraction, so that one module remains the viz brain.
15. As a renderer developer, I want a single vendored Chart.js pin under the assets libs layout, so that generate-time network fetch is never required.
16. As a renderer developer, I want THIRD_PARTY inventory updated for Chart.js (version, license, source), so that compliance is explicit.
17. As a renderer developer, I want init scripts not duplicated per slide naively in a way that double-loads the library, so that one shared Chart.js serves the deck.
18. As a renderer developer, I want fallback selection to be explicit (feature off vs static mode vs unsupported type), so that behavior is testable.
19. As a CI maintainer, I want fixture tests that assert Chart.js markers present only when `charts` on for bar/line/combo, so that gating cannot silently break.
20. As a CI maintainer, I want tests that assert no remote chart CDN in self-contained mode, so that P0 guards still apply to the new payload.
21. As a CI maintainer, I want static fallback tests with `charts` suppressed, so that SC-CHART-FALLBACK is mechanical.
22. As a CI maintainer, I want existing SVG chart gates for non-MVP types to remain green, so that P3 is additive.
23. As a support engineer, I want run_meta to show charts enabled and payload impact, so that “huge HTML” tickets are diagnosable.
24. As a product owner, I want quantitative series routed to Chart.js for the MVP set, so that D8 starts being real before Mermaid exists.
25. As a product owner, I want icon_grid to remain icon/sprite territory, so that Chart.js is not misused for icon matrices.
26. As a PDF-track developer, I want static SVG fallback retained as the print-friendly cousin, so that a future export path has something to capture without running canvas.
27. As a security reviewer, I want Chart.js to be a pinned local/CDN-allowlisted asset only, so that handoff cannot point at arbitrary script URLs.
28. As a security reviewer, I want chart config generated by our code from handoff data, so that we do not eval author JS.
29. As an agent implementer, I want seams limited to render_deck + charts builder + inliner, so that `/tdd` has a short list.
30. As an agent implementer, I want explicit non-goals (full chart-type parity, plugins zoo, animation packs), so that review rejects scope creep.
31. As a layout author, I want chart slides to still sit inside `gl-*` / Boardroom chrome, so that G5 holds.
32. As a layout author, I want dual-chart and pack compositions that already call the chart builder to inherit bar/line/combo behavior automatically, so that I do not rewire every recipe by hand where the builder is already shared.
33. As a data author, I want missing/empty series to degrade to the existing empty/fallback messaging, so that broken data does not throw opaque canvas errors.
34. As a keyboard user, I want deck navigation (arrows, etc.) unaffected by chart canvas focus quirks as much as practical, so that presenting still works.
35. As an a11y-minded author, I want a short text alternative or table fallback available for key charts where already practical, so that canvas is not the only representation when static path is used.
36. As a release manager, I want Chart.js version bumps to be a deliberate pin change with size re-measure, so that P1 soft-warn stays meaningful.
37. As a docs reader, I want operator docs to say which layout types get Chart.js in MVP1, so that expectations match.
38. As a docs reader, I want the size matrix +charts row filled after pin, so that P1’s TBD becomes a number.
39. As a future P3.x owner, I want stacked/waterfall/heatmap Chart.js deferred cleanly, so that a follow-on ticket can extend the map without redesigning gating.
40. As an MVP1 acceptance owner, I want golden-path readiness for “charts + disclosure offline” to be unblocked on the charts half once P5 exists (SC-GOLDEN-1).

## Implementation Decisions

1. **Primary public seam:** `render_deck` / CLI paint. Observable: `presentation.html` contains inlined Chart.js + canvas/init for MVP types when `charts` on; static SVG/table when off; `run_meta` / `DECK_META` feature + size fields remain honest.
2. **Supporting builder seam:** evolve the existing chart HTML entry (`build_chart_html` and helpers). Responsibility: slide + layout_type → either Chart.js payload (config + canvas markup) or static SVG/fallback HTML.
3. **Supporting inliner seam:** when `charts` ∈ feature_ids, inline pinned Chart.js (self-contained: script body or equivalent embed; CDN mode: documented pinned URL only). No per-layout ad-hoc `<script src>`.
4. **Hard dependency on P1:** feature detection, `features_enabled`, and `build_head_assets(feature_ids=)` must exist. If P1 is only partially landed, P3 does not invent a second gate.
5. **MVP Chart.js layout set (normative):**  
   - **In:** `grouped_bar_chart` (vertical bar), `line_chart`, `combo_chart`.  
   - **Out of Chart.js for P3:** `stacked_bar_chart`, `waterfall_chart`, `heatmap`, `icon_grid` — keep current SVG/pack/fallback behavior.  
   - Detection may still enable feature `charts` if any chart layout is present (per P1); only the MVP set switches interactive renderer.
6. **Static fallback (normative):**  
   - Prefer **existing SVG builders** already used for bar/line/combo.  
   - Matrix/table empty fallbacks remain for degenerate data.  
   - Triggers: `charts` feature off/suppressed; explicit static/export mode if exposed; Chart.js asset missing in self-contained (fail closed on missing vendor file when charts on — same spirit as missing fonts); optional force-static flag if cheap — not required if suppress `charts` is enough.
7. **Animation:** Chart.js `animation: false` or duration 0 by default; no animation workstream; respect reduced-motion if easy via Chart.js defaults / CSS.
8. **Theming:** map series and axis chrome toward Boardroom/semantic tokens (navy, blue, ink, grid). Do not adopt Chart.js default multi-hue candy palette as the product default.
9. **One library copy per deck:** single inlined Chart.js; per-slide configs only.
10. **No handoff schema break:** read existing visual_spec / steps_or_data / series shapes the SVG path already understands; additive optional fields only if essential and documented.
11. **No generate-time download** of Chart.js in normal CI/render; commit vendored min build under assets libs; record in THIRD_PARTY.
12. **Security:** do not execute author-supplied JavaScript; configs are generator-built JSON-serializable objects.
13. **External boardroom pack:** may remain for types not on Chart.js path; do not require pack for MVP bar/line/combo self-contained success.
14. **CDN mode:** may reference pinned Chart.js CDN for dev; self-contained must not.
15. **Docs:** README / chart notes list MVP Chart.js types, fallback behavior, and pin version; size matrix +charts row measured post-pin.
16. **Ticket slicing suggestion:** (1) vendor Chart.js + inliner payload for `charts`; (2) bar Chart.js + fallback tests; (3) line + combo; (4) theme/brand colors + animation off; (5) docs + size matrix row.
17. **Labels:** `ready-for-agent`, `renderer-v2`, `P3` (create if missing).

## Testing Decisions

**What good tests look like**

- Assert external behavior at `render_deck`: file output, presence/absence of Chart.js bootstrap, canvas vs SVG for MVP types, feature metadata, remote-URL guard, fallback when charts suppressed.
- Do not assert exact minified Chart.js contents or pixel-perfect canvas.
- Prefer stable markers (e.g. chart config JSON block id/class, `Chart(` init pattern agreed in impl, `chart-svg` for fallback).

**Behaviors under test**

- Bar/line/combo + `charts` on → Chart.js inlined (self-contained), no remote script in self-contained mode.
- Same handoffs + `charts` suppressed → SVG/static readable; no Chart.js required payload.
- Non-MVP chart layouts still render (SVG/pack) without regression.
- Non-chart handoff does not inline Chart.js.
- Missing vendored Chart.js file + charts on + self-contained → clear failure.
- Animation defaults off (config assertion).
- Existing gates/gridlines chart tests updated only as needed; suite green.

**Prior art**

- `tests/test_renderer_v2_self_contained.py` — features, remote URLs, inliner.
- `tests/test_renderer_v2_gates.py` / gridlines — mini handoff chart layouts.
- Chart empty/fallback messaging patterns in current chart builders.

## Out of Scope

- Chart.js for stacked, waterfall, heatmap, icon_grid (follow-on).
- Mermaid / diagram taxonomy beyond “quantitative stays on charts path.”
- Alpine, Swiper, Lucide.
- Heavy Chart.js plugins (datalabels/annotation/zoom) unless a single plugin is required for combo parity — default **no plugins** in P3.
- Animation/motion design.
- PDF canvas rasterization fidelity.
- Replacing Boardroom/`gl-*` chrome.
- New Builder schema versions as a hard requirement.
- ECharts or alternate chart libraries.
- Hard size fail thresholds.

## Further Notes

### Dependency

| Dep | Nature |
|-----|--------|
| P0 | Inliner, self-contained, URL guard |
| P1 | `charts` feature id, detect, metadata, size report |
| P2 | Soft — token colors for series |

### Acceptance checklist

| ID | Criterion |
|----|-----------|
| P3-AC1 | Vendored Chart.js pin + THIRD_PARTY row; inlined only when `charts` on |
| P3-AC2 | `grouped_bar_chart` + charts on → Chart.js path in self-contained HTML |
| P3-AC3 | `line_chart` + charts on → Chart.js path |
| P3-AC4 | `combo_chart` + charts on → Chart.js path |
| P3-AC5 | charts off/suppressed → static SVG/readable fallback for those types |
| P3-AC6 | Self-contained: no remote Chart.js URL |
| P3-AC7 | Animation default off |
| P3-AC8 | Non-MVP chart layouts do not regress |
| P3-AC9 | Size matrix / run_meta reflect charts payload when on |
| P3-AC10 | Docs list MVP types + fallback; suites green |

### Seams locked (2026-07-19)

1. Primary = `render_deck` + real Chart.js when charts on — **yes**  
2. SVG = static fallback when off/static — **yes**  
3. Smaller set bar+line+combo — **yes**  
6. P1 hard prereq — **yes**  

*End of P3 spec.*
