# RESEARCH: Renderer v2 Goal Summary

**Status:** Research / alignment material (not a ticket spec)  
**Date:** 2026-03-25  
**Primary source:** `wiki/renderer_v2_improvement_plan.md` (Draft for Review, 2026-07-18)  
**Related wiki (context only):**  
`renderer_v2_open_props_spec.md`, `renderer_v2_open_props_upgrade_specs.md`,  
`renderer_v2_phase2_spec.md`, `renderer_v2_pdf_fidelity_spec.md`,  
`renderer_v2_spatial_composition.md`, `Gen_Renderer_v2_Complete_Layout_Grid_Refactoring_Plan.md`,  
`PLAN_renderer_v2_gridlines.md`, `builder_renderer_layout_css_interaction.md`

**Sibling research deliverables (this run):**  
- `wiki/RESEARCH_renderer_v2_libraries.md` (**done** — inventory + goals map for all six plan libraries)  
- `wiki/RESEARCH_renderer_v2_extension_opportunities.md` (**done** — high-level extensions beyond naive phase checklist)  
- `wiki/RESEARCH_renderer_v2_priority_list.md` (**done** — ordered themes P0–P9, sequencing, what not to do)  
- `wiki/RESEARCH_renderer_v2_alignment_brief.md` (**done** — decisions + next step after user alignment)

---

## 1. Concise restatement of the improvement goal

**Renderer v2** turns Builder handoff JSON + Evidence Register into **standalone HTML presentations** (fixed 1920×1080, Boardroom aesthetic, `gl-*` / grid foundation).

The improvement plan’s **primary goal** is not a wholesale rewrite. It is to **raise the quality of those HTML decks** along five linked dimensions:

| Dimension | Intent (from plan) |
|-----------|--------------------|
| **Visual aesthetic** | Modern design-system polish (tokens, depth, consistency) while keeping Boardroom branding |
| **Human digestibility** | Better layouts + progressive disclosure so dense content is skim-able and presentable |
| **Complex explanations** | Rich combinations of diagrams, charts, and light interactivity for narrative storytelling |
| **Corporate / offline reliability** | Fully self-contained HTML (libraries inlined at generation time; no CDN dependence in company VPNs) |
| **Enhance, don’t replace** | Preserve Boardroom + existing grid/primitives; keep generation modular and extendable |

**In one sentence:**  
Make generated presentations *look professional, tell denser stories without clutter, and open offline everywhere*—by layering an open design-token base plus carefully chosen, **inlined** JS/CSS libraries on top of the current Boardroom renderer—not by abandoning it.

**Key product decisions already stated in the plan (treat as constraints unless user realigns):**

1. **Inlining strategy** — external libraries are downloaded/vendored and embedded at generation time (`--self-contained`); CDN remains a **dev-only** fallback.  
2. **No animation focus** in this phase (explicitly deferred).  
3. **Library shortlist** — Open Props, Chart.js, Mermaid.js, Alpine.js, Swiper.js (medium priority), Lucide Icons.  
4. **Boardroom + `gl-*` remain the foundation.**

---

## 2. What “extend further” means (scope boundaries)

This research run explores **how far** we might extend beyond a naive checklist of the plan’s phases—**without implementing features or filing tickets yet**. Use these bounds when reading sibling research docs.

### 2.1 In scope for “extend further” *thinking*

- Refining or re-sequencing the plan’s phases (0–5) and high-level themes.  
- Mapping **each recommended library** to concrete renderer goals, gaps, size/risk, and alternatives.  
- Progressive disclosure patterns that remain **standalone HTML** (tabs, accordions, details, filters, light carousels).  
- Stronger chart/diagram storytelling composition (chart + callout + evidence; Mermaid in layout slots).  
- Token / design-system modernization that still maps Boardroom colors/fonts as the locked brand layer (as already sketched in open-props specs).  
- CLI surface ideas: `--self-contained`, `--use-cdn`, feature flags (`charts`, `mermaid`, `alpine`, `swiper`).  
- Offline / corporate hardening (bundle size, trusted minified sources, VPN-safe generation).  
- Backward compatibility strategies (old handoffs still render; opt-in features).  
- Layout compositions that combine existing `gl-*` / layout catalog with new interactive or diagram affordances (high-level only).  
- Extension opportunities that deliberately **avoid** a library (native HTML `<details>`, CSS-only polish, SVG sprite already in tree).  
- Success-criteria language precise enough to become acceptance tests later.  
- Explicit **non-goals** and “what not to do next” for user alignment.

### 2.2 Out of scope for this research run / for near-term “extend further”

| Out of scope | Why |
|--------------|-----|
| Full production implementation of Phases 0–5 | Run charter: research/wiki only |
| GitHub Issues / detailed ticket specs | Deferred until user alignment |
| Replacing Boardroom with another visual brand by default | Plan: preserve Boardroom |
| Heavy animation / motion-first redesign | Explicitly deferred in plan |
| CDN-only production output | Conflicts with corporate / offline primary objective |
| Multi-page SPA presentation frameworks (e.g. full Reveal/Slidev as the host) | Violates “enhance don’t replace” and fixed shell model unless user changes direction |
| Server-side dynamic content after generation | Standalone HTML is the product |
| Live data fetches from the browser in produced decks | Breaks offline + corporate data posture |
| Upstream evidence/analysis pipeline overhauls (PPTX/Excel/PDF extraction etc.) | Covered elsewhere (`V2 Improvements.md` etc.); not this renderer-libraries plan |
| PDF pixel-fidelity engineering as the main track | Separate concern (`renderer_v2_pdf_fidelity_spec.md`); note collisions only |
| Full theme-marketplace / multi-brand engine | Phase-2 specs discuss theme injection; do not expand into a product without alignment |
| Inventing new evidence schema without need | Only if a library capability *requires* handoff shape changes—flag for later, don’t invent tickets |

### 2.3 Grounding: what the tree already roughly has (factual check, not a gap audit)

Under `impact_slides/renderer_v2/` today (high level):

- Present: `shell.py`, `charts.py`, `cli.py`, `load.py`, `layout/`, `diagram/`, `css/`, `sprite.py`, etc.  
- Plan-proposed but **not assumed complete** for this research: `lib_inliner.py`, vendored `assets/libs/`, first-class Mermaid/Alpine/Swiper/Open Props package integration.

Research conclusions should assume **gaps vs the plan** until implementation work (a later run) proves otherwise. Do not treat the improvement plan status as shipped.

Existing detailed specs (Open Props token work, Phase 2 layouts, PDF fidelity, spatial composition) are **adjacent tracks**. They may overlap Phase 1 tokens or layout catalog work; priority research should call out **dependency / seq conflicts**, not silently merge them into this libraries plan.

---

## 3. Guiding principles (carry-forward checklist)

Copied/adapted from the plan §2 for success-criteria mapping:

1. **Self-Contained First** — generated `presentation.html` works fully offline.  
2. **Enhance, Don’t Replace** — Boardroom + `gl-*` stay foundational.  
3. **Storytelling Focus** — layouts × diagrams × charts × light interaction.  
4. **Human Digestible** — progressive disclosure over wall-of-text slides.  
5. **Corporate Friendly** — VPNs, restricted networks, reviewable third-party code.  
6. **Maintainability** — modular hooks (`lib_inliner`, feature flags, CSS token layers).

---

## 4. Success criteria language (later → acceptance tests)

Below is **testable intent**, not an implementation checklist. Wording is reusable in future specs.

### 4.1 Corporate / self-contained

- **SC-OFFLINE-1:** With self-contained mode enabled, a generated deck opens and supports declared interactive features with network access disabled (no required requests to CDNs or first-party servers).  
- **SC-OFFLINE-2:** Produced HTML either embeds required CSS/JS or references only files emitted next to the deck under generator control—not arbitrary remote URLs.  
- **SC-CORP-1:** Documented path exists to use only pinned, official minified artifacts of approved libraries (version-pinned vendoring).  
- **SC-SIZE-1:** Bundle-size impact of each optional feature is measurable (baseline deck vs +charts / +mermaid / +alpine / +swiper / +icons) for later CDR or VPN pay-load limits.

### 4.2 Visual system (Open Props × Boardroom)

- **SC-VIS-1:** Component styling prefers design tokens over new hard-coded decorative px/hex (consistent with open-props upgrade specs).  
- **SC-VIS-2:** Boardroom core brand tokens (palette + display/body fonts as defined today) remain the default theme after token modernization.  
- **SC-VIS-3:** Depth/hierarchy (e.g. elevation/radius scales) is available and used on designated card/panel components without breaking 1920×1080 stage rules.

### 4.3 Charts & diagrams

- **SC-CHART-1:** Handoff can drive common chart types (at least bar, line, pie/doughnut or plan-equivalent set) via Chart.js (or an explicitly chosen alternative) in self-contained mode.  
- **SC-DIAG-1:** Handoff can include text-defined diagrams rendered via Mermaid (flowchart and at least one of timeline / mindmap / architecture-style graphs) offline.  
- **SC-COMPOSE-1:** A single slide can host chart and/or diagram content **with** existing grid layouts without escaping the Boardroom shell.

### 4.4 Progressive disclosure & interactivity

- **SC-IX-1:** At least three disclosure patterns are supportable in generated markup (e.g. tabs, accordion/expandable, modal or detail view)—implementable with Alpine and/or native HTML where sufficient.  
- **SC-IX-2:** Interactive behavior degrades safely when a feature flag is off (static content remains readable).  
- **SC-IX-3:** Interactivity does not require a build step inside the browser or external module loaders beyond the inlined bundle.

### 4.5 Advanced layout polish (medium priority)

- **SC-LAY-1:** Optional carousel/gallery patterns (Swiper or chosen alternative) can express multi-step or comparison content **inside** a slide without breaking deck navigation assumptions.  
- **SC-ICON-1:** Iconography path exists (Lucide or existing sprite strategy) that remains self-contained and visually consistent with Boardroom.

### 4.6 Compatibility & maintainability

- **SC-COMPAT-1:** Existing handoffs that do not opt into new features render with no required schema break (backward compatible default).  
- **SC-CLI-1:** Generator exposes explicit controls for self-contained vs CDN-dev and for feature subsets.  
- **SC-MOD-1:** Library embedding is centralized (single inliner/asset module) rather than ad-hoc string pastes across layout files.  
- **SC-REG-1:** Automated tests cover at least inliner correctness and “no unexpected external URL” checks for self-contained fixtures.

### 4.7 Explicit non-success (do not treat as failure of this goal)

- Motion-rich animated transitions between slides.  
- Parity with PowerPoint authoring UX.  
- Perfect print/PDF pixel twin (tracked under PDF fidelity specs separately).  
- Real-time collaborative editing of decks.

---

## 5. Plan phases → goal anchors (for prioritization research)

| Phase (plan) | Goal anchor |
|--------------|-------------|
| **0 Foundation** | SC-OFFLINE-*, SC-CLI-1, SC-MOD-1, SC-REG-1 |
| **1 Design system (Open Props)** | SC-VIS-* |
| **2 Chart.js + Mermaid** | SC-CHART-*, SC-DIAG-*, SC-COMPOSE-1 |
| **3 Alpine progressive disclosure** | SC-IX-* |
| **4 Swiper + Lucide** | SC-LAY-1, SC-ICON-1 |
| **5 Polish & hardening** | SC-SIZE-1, SC-CORP-1, docs/examples, schema only if required |

**Research implication:** Phase 0 is a **hard prerequisite** for production claims on all library-backed features. Phases 2–4 should stay **feature-flagged** so Deck A can stay minimal while Deck B opts into weight.

---

## 6. Risks the goal must continue to acknowledge

From plan §6, restated as goal-level risks:

| Risk | Goal impact |
|------|-------------|
| Inlined payload size | Offline wins vs email/SharePoint size limits |
| Alpine (or any IX) learning curve | Author/builder complexity in handoff JSON |
| Breaking existing slides | Undermines “enhance don’t replace” |
| Corporate security review of vendored JS | Blocks adoption even if offline works |
| Overlap with parallel layout/token specs | Double work or conflicting CSS sources of truth |

Mitigations stay at **principle** level here: minified pins, compatibility tests, official dist only, single token pipeline, feature flags.

---

## 7. Library inventory pointer (completeness gate)

The improvement plan **names / recommends** these libraries (must each appear in `RESEARCH_renderer_v2_libraries.md` with capabilities → goals mapping):

| # | Library | Plan priority signal |
|---|---------|----------------------|
| 1 | **Open Props** | Phase 1 primary (design tokens) |
| 2 | **Chart.js** | Phase 2 high |
| 3 | **Mermaid.js** | Phase 2 high |
| 4 | **Alpine.js** | Phase 3 primary |
| 5 | **Swiper.js** | Phase 4 medium |
| 6 | **Lucide Icons** | Phase 4 polish |

**Library-like stacks / mechanisms implied by the plan** (not always separate npm packages, but must be treated in libraries or architecture notes):

| Item | Role |
|------|------|
| **Generation-time inliner** (`lib_inliner.py` concept) | Enables SC-OFFLINE-* for all of the above |
| **CDN dev fallback** (`--use-cdn`) | Dev ergonomics only |
| **Existing Boardroom CSS + `gl-*` grid** | Foundation being extended |
| **Existing chart path (`charts.py`)** | Integration surface for Chart.js |
| **Existing `diagram/` package** | Integration surface for Mermaid vs custom SVG |
| **Existing `sprite.py` / icon approach** | Alternative or complement to Lucide |

Future library research must not skip any of rows 1–6 above.

---

## 8. Deferred decisions (need user alignment later)

Captured so later docs do not pretend consensus:

1. Approve vs amend the library shortlist (especially **Swiper** medium priority, Chart.js vs alternatives, Mermaid vs pure `diagram/`).  
2. Maximum acceptable **self-contained HTML size** per deck class.  
3. Whether progressive disclosure is **builder-authored** (JSON patterns) or **renderer-inferred**.  
4. How Open Props is consumed (full CSS import vs cherry-picked tokens already partially specified in open-props docs).  
5. How firm the **no animations** line is for micro-interactions (hover, accordion height).  
6. Sequencing vs **layout catalog / Phase 2 layout specs** and **PDF fidelity** workstreams.  
7. Whether Lucide replaces or coexists with the current sprite pipeline.

---

## 9. What “done” looks like for *this research objective* (not for product build)

Research is ready for user alignment when:

1. This goal summary exists and stays consistent with the plan.  
2. Every plan-named library has a capabilities summary mapped to the goals above.  
3. Extension opportunities and an ordered **high-level** priority list exist.  
4. An alignment brief lists open questions and proposed **next** step (specs/tickets only after human alignment).  
5. No production renderer feature implementation was required to complete the research.

---

## 10. Document control

| Field | Value |
|-------|--------|
| Objective run | GNHF research: renderer v2 improvement options |
| Implementation | **None** in this run |
| Priority + alignment | **Done** → `RESEARCH_renderer_v2_priority_list.md`, `RESEARCH_renderer_v2_alignment_brief.md` |

*End of goal summary.*
