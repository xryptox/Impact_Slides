# RESEARCH: Renderer v2 Priority List (High-Level Themes)

**Status:** Research / alignment material (not a sprint backlog or ticket dump)  
**Date:** 2026-03-25  
**Primary source:** `wiki/renderer_v2_improvement_plan.md`  
**Depends on:**  
`wiki/RESEARCH_renderer_v2_goal_summary.md`,  
`wiki/RESEARCH_renderer_v2_libraries.md`,  
`wiki/RESEARCH_renderer_v2_extension_opportunities.md`

**Sibling:** `wiki/RESEARCH_renderer_v2_alignment_brief.md` (**done**)

---

## How to read this document

This is an **ordered list of high-level change themes**, not implementation tasks.

Each theme includes:

| Field | Meaning |
|-------|---------|
| **Problem** | Why it matters against plan goals |
| **Outcome** | Observable product/engineering result |
| **Dependencies** | What must exist first |
| **Effort** | Rough band: **S** (days), **M** (1–2 weeks), **L** (multi-week / multi-sub-system) |
| **Risk** | Primary failure modes |
| **Prerequisites** | Docs/decisions/assets before build |
| **User alignment?** | Whether product direction must be confirmed before specs/tickets |
| **Ext refs** | Related extension IDs from the extension-opportunities doc (`E01`…) |
| **SC refs** | Success-criteria IDs from the goal summary (`SC-*`) |

**Goal codes (from goal summary / plan):**  
G1 Visual aesthetic · G2 Human digestibility · G3 Complex explanations · G4 Offline/corporate · G5 Enhance-don’t-replace / maintainability

---

## 1. Recommended sequence (one glance)

```text
P0  Self-contained foundation + dual-mode contract
 ↓
P1  Feature×size gating + generate-time validation envelope
 ↓
P2  Open Props under Boardroom (single semantic owner)     } can start design
P3  Chart.js path + charts.py contract                      } after P0 path exists
P4  Mermaid path + chart/diagram taxonomy                   } (parallel OK carefully)
 ↓
P5  Native-first progressive disclosure (+ optional Alpine)
 ↓
P6  Lucide / icon sprite policy (subset)
 ↓
P7  gl-* composition recipes / storytelling layouts (before Swiper)
 ↓
P8  Swiper as bounded in-slide layout only (medium priority)
 ↓
P9  PDF/export seam + corporate pack + goldens + docs hardening
```

**Parallelism note:** After **P0**, visual tokens (**P2**) and viz (**P3/P4**) can proceed on separate tracks if ownership of CSS vs chart modules is clear. **Do not** parallelize Swiper or heavy Alpine patterns before disclosure and layout taxonomy are decided.

---

## 2. Ordered priority themes

### P0 — Self-contained foundation & dual-mode generation contract

| | |
|--|--|
| **Problem** | Plan and current state both call out CDN dependence as a corporate/VPN failure mode; without a single inlining path, every later library is a reliability regression. |
| **Outcome** | Generator can emit **fully offline** HTML via `--self-contained` (or equivalent); dev may use `--use-cdn`; inliner centralizes vendor assets; tests prove no unexpected external network refs in self-contained mode. |
| **Dependencies** | None (true foundation). Plan modules: `lib_inliner.py`, `assets/libs/`, `shell.py`, `load.py`, CLI. |
| **Effort** | **M** |
| **Risk** | Incorrect embedding (MIME/order/CSP); absolute CDN left in CSS `@import`; version drift of vendored files. |
| **Prerequisites** | Pick default mode for “release” vs “dev”; pin library versions listing (see libraries doc). |
| **User alignment?** | **Yes — light:** confirm self-contained as **default for production outputs**. |
| **Ext / SC** | E01, E02, E14 · SC-OFFLINE-*, SC-CORP-1, SC-CLI-1, SC-MOD-1, SC-REG-1 · **G4, G5** |

---

### P1 — Feature-gated bundles & size accountability

| | |
|--|--|
| **Problem** | Inlining *all* libraries on every deck destroys SC-SIZE-1 and may make G4 politically hard (large HTML email/share). |
| **Outcome** | Feature flags (charts / mermaid / alpine / swiper / icons) drive **what gets inlined**; documented size matrix; CI or generate-time report of approximate payload. |
| **Dependencies** | **P0** complete enough to plug modules into the inliner. |
| **Effort** | **S–M** |
| **Risk** | Flag explosion; handoffs that need a feature but generator omits it silently. |
| **Prerequisites** | Policy: fail closed vs warn when handoff needs missing feature. |
| **User alignment?** | **Yes:** max acceptable single-file size / which features are always-on. |
| **Ext / SC** | E01, E15 · SC-SIZE-1, SC-IX-2, SC-COMPAT-1 · **G4, G5** |

---

### P2 — Design tokens: Open Props under Boardroom (single owner)

> **Non-normative (research).** Normative owner: `wiki/SPEC_renderer_v2_tokens_owner.md`.

| | |
|--|--|
| **Problem** | Visual polish lag; hard-coded values; parallel open-props wiki specs risk **two sources of truth** for semantic tokens. |
| **Outcome** | Open Props (or subset) feeds primitive scales; **Boardroom remains brand**; `semantic-tokens` / theme injection has **one documented owner**; components prefer tokens (SC-VIS-*). |
| **Dependencies** | **P0** helpful for consistent CSS emission; can partially start earlier on CSS-only. |
| **Effort** | **M** (larger if full rewrite of components.css). |
| **Risk** | Brand drift; fighting existing open-props upgrade specs; specificity wars with `gl-*`. |
| **Prerequisites** | Align this research with `renderer_v2_open_props_*.md` — **merge ownership**, don’t dual-track silently. |
| **User alignment?** | **Yes:** who owns semantic tokens and how much Open Props utility surface is allowed in output. |
| **Ext / SC** | E08 · SC-VIS-1..3 · **G1, G5** |

---

### P3 — Data visualization path (Chart.js) + `charts.py` evolution

| | |
|--|--|
| **Problem** | Static/basic charts limit complex numeric storytelling (G3); plan calls Chart.js high priority. |
| **Outcome** | Handoff → Chart.js configs for common types (bar, line, pie/doughnut…); charts only inlined when used; evidence/callout composition still Boardroom/`gl-*`. |
| **Dependencies** | **P0**, **P1** (feature gate). |
| **Effort** | **M** |
| **Risk** | Huge Chart.js build if not tree-subset; theming fights Boardroom colors; a11y/color; print/PDF rasterization mismatches. |
| **Prerequisites** | Handoff schema fields for chart specs; theme color bridge from tokens. |
| **User alignment?** | Partial — confirm **Chart.js** vs lighter alternative if size budget is tight. |
| **Ext / SC** | E05, E06 · SC-CHART-1, SC-COMPOSE-1 · **G3, G1** |

---

### P4 — Process/structure diagrams (Mermaid) + viz taxonomy

| | |
|--|--|
| **Problem** | Flows/architecture/timeline stories need text-defined diagrams; without taxonomy, Chart.js + Mermaid + existing `diagram/` **triplicate** pipelines. |
| **Outcome** | Mermaid supported for named diagram kinds; **documented when-to-use** Chart vs Mermaid vs current diagram path; safe render + fit-in-slide rules; optional CLI `--diagrams=mermaid`. |
| **Dependencies** | **P0**, **P1**; design coordination with existing `diagram/`. |
| **Effort** | **M–L** (Mermaid weight + security + layout fit). |
| **Risk** | **Largest self-contained size risk** (libraries research); XSS if raw mermaid from untrusted handoff; overflow at 1920×1080; version churn. |
| **Prerequisites** | Security stance (trusted handoff only?); subset of diagram types; layout slot rules. |
| **User alignment?** | **Yes — strong:** accept Mermaid weight **or** constrain types / alternative. |
| **Ext / SC** | E06, E07 · SC-DIAG-1, SC-COMPOSE-1 · **G3, G4** |

---

### P5 — Progressive disclosure: native-first, Alpine optional

| | |
|--|--|
| **Problem** | Dense slides need tabs/accordions/details without clutter (G2); premature Alpine everywhere increases JS surface. |
| **Outcome** | At least three disclosure patterns in generated HTML; **native `<details>` / CSS-first tier** where enough; Alpine reserved for multi-state filters/tabs that native can’t express cleanly; safe degrade when Alpine off. |
| **Dependencies** | **P0–P1**; patterns documented for handoff authors (E03, E04). |
| **Effort** | **M** |
| **Risk** | Inconsistent pattern zoo; Alpine attributes leaking into non-interactive layouts; a11y (focus, keyboard). |
| **Prerequisites** | **Product decision:** native-first vs Alpine-default (extension doc favors native-first). |
| **User alignment?** | **Yes** on Alpine foot-gun vs progressive enhancement story. |
| **Ext / SC** | E03, E04, E10, E18, E19 · SC-IX-1..3 · **G2, G5** |

---

### P6 — Iconography policy (Lucide subset vs extended sprite)

| | |
|--|--|
| **Problem** | Visual polish and wayfinding need consistent icons; full Lucide inline blows size; tree may already have sprite paths. |
| **Outcome** | Documented **subset** or generate-time icon pick-list; sprite or partial Lucide; SC-ICON-1 met without shipping the whole set. |
| **Dependencies** | **P0** for asset pipeline; mild dependency on **P2** for sizing/color tokens. |
| **Effort** | **S–M** |
| **Risk** | License/attr hygiene (Lucide ISC); duplicate systems (sprite + Lucide). |
| **Prerequisites** | Inventory existing sprite usage; pick one primary path. |
| **User alignment?** | Light — brand icon style preferences. |
| **Ext / SC** | E11 · SC-ICON-1 · **G1, G4** |

---

### P7 — `gl-*` storytelling composition recipes (pre-Swiper)

| | |
|--|--|
| **Problem** | Libraries alone don’t create narrative slides; compositions (chart + evidence + disclosure) are the real G2/G3 lever (**E09**, **E20**). |
| **Outcome** | Named high-level layout recipes on existing grid (e.g. process-with-details, data-heavy + callouts) **without** requiring Swiper; handoff examples; optional deferred-init hooks. |
| **Dependencies** | Practical use of **P2–P5** pieces; should **precede** P8. |
| **Effort** | **M** |
| **Risk** | Spec sprawl colliding with phase2 / spatial-composition wiki; over-constraining layouts. |
| **Prerequisites** | Cross-walk to existing layout catalog docs; avoid inventing a second layout language. |
| **User alignment?** | Yes for which recipes are “supported product” vs experimental. |
| **Ext / SC** | E09, E16, E20 · SC-COMPOSE-1, SC-LAY-* (recipes path) · **G2, G3, G5** |

---

### P8 — Swiper as **bounded in-slide** advanced layout (medium priority)

| | |
|--|--|
| **Problem** | Comparisons/galleries/multi-step *within a slide* can benefit from carousels; plan marks Swiper **medium** priority. |
| **Outcome** | Optional Swiper only for named layout types (`comparison-carousel`, etc.); modular build; **not** used as deck navigation competing with slide model. |
| **Dependencies** | **P0–P1**, **P7** (prove native/`gl-*` first); preferably post-**P5**. |
| **Effort** | **M** |
| **Risk** | Module weight; touch/a11y; print/PDF disastrous without freeze-frame strategy; double navigation confusion. |
| **Prerequisites** | Explicit ban-list: no full-deck Swiper unless future product decision. |
| **User alignment?** | **Yes** — is medium-priority carousel worth Mermaid-class cost at all? |
| **Ext / SC** | E12, E20 · SC-LAY-1 · **G2, G3** (conditional), **G4** risk |

---

### P9 — Hardening: PDF/export seams, corporate pack, goldens, docs

| | |
|--|--|
| **Problem** | Interactive + heavy libs break print/PDF fidelity and corporate acceptance without an intentional seam; Phase 5 of plan is under-specified vs parallel PDF wiki. |
| **Outcome** | Corporate readiness checklist; goldens for self-contained offline; export/print CSS or “ready state” hooks; example decks (data-heavy, process story); schema validation extras; README inlining docs. |
| **Dependencies** | Meaningful slices of **P0–P7** done; PDF work **coordinates** with `renderer_v2_pdf_fidelity_spec.md` rather than replacing it. |
| **Effort** | **M–L** (spread; not one PR). |
| **Risk** | Treating PDF as an afterthought → visual regressions; goldens flaky with JS chart paint timing. |
| **Prerequisites** | Define “supported export modes” (interactive HTML only vs print-static). |
| **User alignment?** | **Yes** on whether PDF parity is in-scope for *this* library roadmap or a parallel track. |
| **Ext / SC** | E13, E14, E15, E17 · SC-CORP-*, SC-REG-1, SC-COMPAT-1 · **G4, G5** |

---

## 3. Dependency graph (condensed)

| Theme | Hard deps | Soft / coordination |
|-------|-----------|---------------------|
| P0 Foundation | — | CLI UX |
| P1 Feature gates | P0 | Size budget from user |
| P2 Open Props | P0 (soft) | open-props wiki specs |
| P3 Chart.js | P0, P1 | Boardroom color tokens (P2) |
| P4 Mermaid | P0, P1 | existing `diagram/`, security |
| P5 Disclosure | P0, P1 | a11y guidelines |
| P6 Icons | P0 | P2 metrics |
| P7 Recipes | P2–P5 as available | phase2 / spatial wiki |
| P8 Swiper | P0, P1, **P7** | PDF strategy |
| P9 Hardening | P0 + chosen features | PDF fidelity track |

---

## 4. Mapping to plan phases (not 1:1)

| Plan phase | Primary themes | Notes |
|------------|----------------|-------|
| Phase 0 Foundation | **P0**, **P1** | P1 is amplified beyond plan text (from extension research). |
| Phase 1 Design system | **P2** | Must reconcile parallel open-props specs. |
| Phase 2 Charts & diagrams | **P3**, **P4** | Split intentional; taxonomy mandatory. |
| Phase 3 Interactivity | **P5** | Native-first option **before** full Alpine. |
| Phase 4 Advanced layouts & polish | **P6**, **P7**, **P8** | Reordered: recipes & icons before/with Swiper. |
| Phase 5 Polish & hardening | **P9** | Continuous from P0 tests, not only end. |

---

## 5. What NOT to do next

Explicit deferred / anti-goals for the **first build run after alignment** (extends goal-summary non-goals):

1. **Do not** implement all six libraries in one vertical slice without **P0/P1**.  
2. **Do not** make CDN the production default.  
3. **Do not** replace Boardroom / rewrite off `gl-*` into a generic CSS framework.  
4. **Do not** prioritize **animation-heavy** or cinematic motion (plan deferral).  
5. **Do not** adopt Swiper as **whole-deck** navigation.  
6. **Do not** dump full Lucide or full Mermaid+Chart+Swiper into every HTML.  
7. **Do not** open a second semantic-token or layout-spec track that ignores existing wiki specs—**coordinate**.  
8. **Do not** treat this priority list as GitHub tickets—**alignment brief first**, then specs.  
9. **Do not** pull React/Vue/Svelte runtime into renderer output for disclosure.  
10. **Do not** merge PDF fidelity work as a silent subtask of Chart/Mermaid without an export contract.  
11. **Do not** expand research into production `impact_slides/renderer_v2/**` feature commits under the research charter.  
12. **Do not** invent issue-tracker epics until the user accepts sequencing and Mermaid/Alpine/Swiper weight tradeoffs.

---

## 6. Effort portfolio (indicative)

| Band | Themes |
|------|--------|
| **S** | Parts of P1 (flags), P6 (subset icons) once P0 exists |
| **M** | P0, P2, P3, P5, P7, much of P9 |
| **L** | P4 (Mermaid + taxonomy + fit/safe), full P8+P9 corporate/PDF matrix |

Rough **critical path to a credible “offline polished story deck” MVP**:  
**P0 → P1 → (P2 ∥ P3) → P5 → P7**, with **P4** only if process diagrams are must-have for the first customer narrative, and **P8** explicitly optional.

---

## 7. User-alignment gates (summary)

| Gate | Blocks |
|------|--------|
| Self-contained default + size budget | P0/P1 production policy |
| Open Props ownership vs existing specs | P2 |
| Mermaid weight / allowed diagram types | P4 |
| Native-first vs Alpine-default | P5 |
| Swiper worth medium-priority investment | P8 |
| PDF/export in or out of this roadmap | P9 |

Decisions and open questions are collected in `wiki/RESEARCH_renderer_v2_alignment_brief.md`.

---

## 8. Self-check

| Check | Status |
|-------|--------|
| Ordered high-level themes (not ticket dump) | Yes — P0–P9 |
| Problem / outcome / deps / effort / risk / alignment | Yes per theme |
| Sequence + what NOT to do | §§1, 5 |
| Tied to goals, SC IDs, extensions | Yes |
| Ready as input to user alignment (not implementation) | Yes |
