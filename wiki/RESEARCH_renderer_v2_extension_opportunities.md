# RESEARCH: Renderer v2 Extension Opportunities

**Status:** Research / alignment material (not a ticket spec)  
**Date:** 2026-03-25  
**Primary sources:** `wiki/renderer_v2_improvement_plan.md`, `wiki/RESEARCH_renderer_v2_goal_summary.md`, `wiki/RESEARCH_renderer_v2_libraries.md`  
**Related context (do not absorb blindly):** open-props specs, phase2 layout catalog, PDF fidelity, spatial composition, existing `diagram/`, `charts.py`, `sprite.py`

**Sibling research deliverables:**  
- `wiki/RESEARCH_renderer_v2_goal_summary.md` (**done**)  
- `wiki/RESEARCH_renderer_v2_libraries.md` (**done**)  
- `wiki/RESEARCH_renderer_v2_priority_list.md` (**done**)  
- `wiki/RESEARCH_renderer_v2_alignment_brief.md` (**done**)

---

## 0. Purpose and guardrails

This document lists **high-level extensions** we could apply to renderer_v2 **beyond a naive checklist** of plan Phases 0–5. It is intentionally:

- **Not** a sprint backlog or GitHub Issues dump  
- **Not** production implementation guidance  
- **Tied** to stated goals (G1–G5) and either library capabilities or deliberate **no-library** approaches  

**Goal codes** (from goal summary / libraries doc):

| Code | Goal |
|------|------|
| G1 | Visual aesthetic / tokens-polish + Boardroom |
| G2 | Human digestibility / progressive disclosure |
| G3 | Complex explanations (diagram + chart + interaction) |
| G4 | Self-contained offline / corporate VPN-safe |
| G5 | Enhance Boardroom + `gl-*`; modular maintainability |

**Criticality labels:**

| Label | Meaning |
|-------|---------|
| **Goal-critical** | Without this (or an equivalent), primary plan success criteria stay weak even if libraries are “wired in” |
| **Goal-amplifying** | Strongly multiplies value of a naive library hook-up; should inform sequencing |
| **Nice-to-have** | Attractive after core goals; safe to defer without blocking alignment on the plan itself |
| **Alignment-gated** | Technically fine, but needs an explicit user decision before specs/tickets |

**Hard non-extension of this research run:** animations-first redesign, CDN-only production, SPA host replacement (Reveal/Slidev as shell), live browser data fetches, filing tickets.

---

## 1. Opportunity map (summary table)

| ID | Opportunity | Goals | Criticality | Primary lever |
|----|-------------|-------|-------------|----------------|
| E01 | Feature-gated self-contained matrix (not one monolithic always-on bundle) | G4, G5, SC-SIZE | **Goal-critical** | Inliner + CLI flags |
| E02 | Official dual-mode contract: self-contained default vs CDN-dev only | G4, G5 | **Goal-critical** | `shell` + CLI + CI URL guard |
| E03 | Declarative handoff patterns for disclosure (tabs/accordion/detail) | G2, G3, G5 | **Goal-critical** | Schema/conventions + Alpine *or* native |
| E04 | Native-first progressive disclosure tier (zero JS where enough) | G2, G4, G5 | **Goal-amplifying** | `<details>`, CSS, a11y |
| E05 | Chart.js path as enhancement of `charts.py`, with static/SVG fallback mode | G3, G4, PDF collision | **Goal-critical** | Chart.js + existing charts |
| E06 | Explicit **when Chart vs Mermaid vs custom diagram/** routing policy | G3, G5 | **Goal-critical** | Content taxonomy |
| E07 | Mermaid security + layout containment package (not just “inline the lib”) | G3, G4, corp risk | **Goal-critical** | Mermaid config + CSS slots |
| E08 | Open Props as **primitive layer only**; single semantic owner for Boardroom | G1, G5 | **Goal-critical** | Tokens pipeline (align w/ open-props specs) |
| E09 | Composition recipes: chart + evidence + callout / process + Mermaid + steps | G2, G3 | **Goal-amplifying** | Layout catalog + examples |
| E10 | Deferred / on-demand init for heavy libs (Mermaid, optional Chart) | G4, perf | **Goal-amplifying** | Shell init strategy |
| E11 | Icon strategy: Lucide subset *or* sprite coexistence with policy | G1, G4 | **Goal-amplifying** | Lucide + `sprite.py` |
| E12 | Swiper as **opt-in layout primitive**, not default navigation host | G2, G3, G5 | Medium / **Alignment-gated** weight | Swiper modular |
| E13 | Print / static snapshot hooks coordinated with PDF fidelity track | G3 ∩ PDF track | **Alignment-gated** | Capture timing, not Motion |
| E14 | Corporate readiness pack: pin lockfile, SBOM-ish note, offline test fixture | G4, SC-CORP | **Goal-amplifying** | Phase 5 hardening |
| E15 | Builder validation / lint for Mermaid + chart configs at generate time | G3, G5 | **Goal-amplifying** | Generator validation |
| E16 | Storytelling “acts” / slide narrative metadata (progressive path hints) | G2, G3 | **Nice-to-have** | Handoff conventions |
| E17 | Theme injection dry-run + visual regression golden decks | G1, G5 | **Nice-to-have** → later | Test fixtures |
| E18 | Accessible canvas/chart text fallbacks and reduced-motion defaults | G2, corp | **Goal-amplifying** | Chart.js options + copy |
| E19 | Filter / simple compare patterns beyond tabs (Alpine `x-show` sets) | G2, G3 | **Nice-to-have** | Alpine patterns |
| E20 | Deliberate **no new layout framework**: deepen `gl-*` instead of Swiper-first | G5 | **Alignment-gated** alternative | CSS grid only |

---

## 2. Extensions in detail

### E01 — Feature-gated self-contained matrix  
**Problem:** Naively inlining *all* libraries into every deck maximizes offline success but fails SC-SIZE realism and corporate email/SharePoint limits (libraries research: Mermaid dominates weight).  
**Extension:** Treat `--features=…` (plan CLI sketch) as a **real product surface**: baseline deck ships Boardroom only; charts / mermaid / alpine / swiper / icons each add a measurable delta. Inliner emits only selected assets.  
**Outcome:** G4 without forcing G4-at-any-size; matches SC-SIZE-1/SC-CLI-1.  
**Library tie:** Inliner stack (libraries §3.1); every named lib becomes optional payload.  
**Criticality:** **Goal-critical** — without this, Phase 2–4 become one inseparable megabundle.

### E02 — Dual-mode contract with CI guardrails  
**Problem:** Plan allows CDN for dev; production accidental CDN is a silent G4 regression.  
**Extension:** Document and enforce: default path for “ship” artifacts is self-contained; `--use-cdn` is non-ship; add fixture/assert “no unexpected remote URLs” (SC-REG-1).  
**Outcome:** Corporate trust story is operational, not aspirational.  
**Library tie:** §3.2 dual mode; all six libs.  
**Criticality:** **Goal-critical**.

### E03 — Declarative disclosure patterns in handoff  
**Problem:** Dropping Alpine into the shell without **authored patterns** yields ad-hoc `x-data` in templates and non-portable decks.  
**Extension:** Define a small set of **renderer-understood patterns** (e.g. `disclosure: tabs | accordion | detail`, panels[], defaultIndex) that layout code expands to Alpine *or* native markup. Keep schema additive (SC-COMPAT-1).  
**Outcome:** G2 becomes repeatable for Builder; SC-IX-1/2 testable.  
**Library tie:** Alpine primary; native path as degrade (E04).  
**Criticality:** **Goal-critical** for Phase 3 seriousness.

### E04 — Native-first disclosure tier (no-library path)  
**Problem:** Alpine has cost and review surface; some decks only need one expandable section.  
**Extension:** Prefer `<details>`/`<summary>`, CSS-only tabs where accessibility is acceptable, or single-panel expand **without** Alpine when feature flag off or pattern is trivial. Alpine reserved for multi-tab state, filters, simple client filters.  
**Outcome:** Smaller decks; SC-IX-2 degrade story; G4 friendliness.  
**Library tie:** **Deliberate no-library** / HTML platform; Alpine optional upgrade.  
**Criticality:** **Goal-amplifying** (reduces over-dependency on Alpine learning curve risk in plan §6).

### E05 — Chart.js as evolution of `charts.py` + fallback  
**Problem:** “Add Chart.js” without integrating existing chart generation creates two pipelines.  
**Extension:** Map existing chart model → Chart.js config as the **primary interactive path**; keep or add a **static fallback** (table, SVG, or pre-rendered image) when charts feature off or for print-oriented export paths. Default **animations off** (plan: no animation focus).  
**Outcome:** G3 without abandoning current charts investment; better PDF coexistence options.  
**Library tie:** Chart.js + §3.4 charts.py surface.  
**Criticality:** **Goal-critical**.

### E06 — Chart vs Mermaid vs `diagram/` routing policy  
**Problem:** Libraries research flagged dual Chart + Mermaid collision with existing `diagram/`.  
**Extension:** Publish a **content taxonomy** one-pager for authors/Builder:

| Content intent | Preferred path |
|----------------|----------------|
| Quantitative series / comparisons | Chart.js via `charts.py` |
| Process / architecture / sequence / mindmap from text | Mermaid |
| Brand-locked custom SVG illustrations already in catalog | Keep `diagram/` |
| Simple pie that must match Mermaid theme in a process doc | Prefer Chart for data integrity; avoid Mermaid pie unless narrative-only |

**Outcome:** One mental model; fewer redundant implementations (G5).  
**Library tie:** Chart.js, Mermaid, diagram stack.  
**Criticality:** **Goal-critical** before deep Phase 2 build.

### E07 — Mermaid “safe+fit” package  
**Problem:** Inlining Mermaid alone ignores injection risk (`securityLevel`), theme drift, and SVG overflow in 1920×1080 cells.  
**Extension:** Standard init: pinned version, restrictive security settings per Mermaid docs, Boardroom theme variables, max-height/overflow rules in `gl-*` slots, optional render-on-visible. Treat Mermaid source as untrusted input.  
**Outcome:** G3 credible in corporate review; fewer broken layouts.  
**Library tie:** Mermaid capabilities + risks in libraries doc.  
**Criticality:** **Goal-critical** if Mermaid stays on shortlist.

### E08 — Open Props primitives only; one semantic owner  
**Problem:** Parallel open-props wiki specs + plan Phase 1 can fork token truth.  
**Extension:** Rule: Open Props = **primitive vocabulary**; Boardroom brand lives only in semantic mapping; components never bind to random raw Open Props brand colors. Align implementation later with *one* chosen open-props spec track—not both divergent docs.  
**Outcome:** G1 + G5; SC-VIS-1/2.  
**Library tie:** Open Props; foundation stack §3.3.  
**Criticality:** **Goal-critical** (process, not more tokens).

### E09 — Composition recipes (story packs)  
**Problem:** Plan Phase 5 “example templates” is easy to under-do; libraries alone don’t create storytelling.  
**Extension:** Curate a few **recipes** as first-class research/product targets:  
1. Data-heavy: KPI strip + Chart.js + evidence footnotes + accordion methodology  
2. Process story: Mermaid flowchart + stepped Alpine/native panels  
3. Comparison: two-column `gl-*` + optional Swiper for >2 alternatives  
4. Architecture: Mermaid (or diagram/) + Lucide markers + detail drawer  

**Outcome:** G2/G3 “combinations” principle becomes tangible; feeds Phase 5 docs.  
**Library tie:** All six as optional ingredients.  
**Criticality:** **Goal-amplifying**.

### E10 — Deferred init for heavy libraries  
**Problem:** Mermaid (and full Chart) on every `DOMContentLoaded` hurts first paint of large decks.  
**Extension:** Init Chart only where canvases exist; Mermaid only for nodes present / near viewport; never parse Mermaid for decks that didn’t request the feature.  
**Outcome:** Makes G4 + large Mermaid coexist better.  
**Library tie:** Mermaid size notes; shell architecture.  
**Criticality:** **Goal-amplifying**.

### E11 — Icon policy: Lucide subset vs sprite  
**Problem:** Plan says “Lucide or sprite”; full Lucide set fights G4; duplicate systems fight G5.  
**Extension:** Default **subset** export (or generate SVG sprite from needed Lucide names at build/vendor time); document coexistence: sprite for legacy slides, Lucide subset for new semantic icon names; one CSS sizing scale.  
**Outcome:** SC-ICON-1 without multi-megabyte icon tragedy.  
**Library tie:** Lucide + sprite §3.5.  
**Criticality:** **Goal-amplifying** (Phase 4 polish can wait, policy should not conflict).

### E12 — Swiper as in-slide primitive only  
**Problem:** Misusing Swiper as deck navigation would fight fixed shell and Boardroom stage model.  
**Extension:** Swiper **only** inside slide chrome (comparison garage, gallery of 3+ options, multi-step within one beat). Disable conflicting keyboard capture vs deck-level keys; modular build (modules tree-shake). Medium priority stays medium.  
**Outcome:** SC-LAY-1 without shell takeover (G5).  
**Library tie:** Swiper.  
**Criticality:** Medium; **alignment-gated** if product wants carousel-heavy storytelling.

### E13 — Snapshot hooks for PDF / static capture  
**Problem:** Client-rendered Chart/Mermaid collide with PDF fidelity workstream.  
**Extension:** Do **not** own full PDF engineering here; define a minimal contract: “diagrams/charts expose ready state / class when painted” so PDF track can wait or pre-render. Optional generation-time static bake later.  
**Outcome:** Avoids two teams stepping on each other.  
**Library tie:** Chart + Mermaid lifecycle.  
**Criticality:** **Alignment-gated** (coordinate with PDF wiki, not freestyle).

### E14 — Corporate readiness pack  
**Problem:** Plan Phase 5 checklist is vague for security reviewers.  
**Extension:** Pin versions + checksums of vendored min files; short third-party inventory (name, version, license, source URL); offline open test; feature × size table published in docs.  
**Outcome:** SC-CORP-1 / SC-SIZE-1 operational.  
**Library tie:** All vendored libs + inliner.  
**Criticality:** **Goal-amplifying** (blocks adoption after tech works).

### E15 — Generate-time validation  
**Problem:** Invalid Mermaid or Chart config fails in the browser at present time—late and presenter-hostile.  
**Extension:** Lightweight validate/lint at generation: Mermaid parse if feasible in Python env or subprocess; Chart config schema check; fail build or emit structured warnings.  
**Outcome:** Quality bar for G3 content.  
**Library tie:** Mermaid/Chart.js integration surfaces.  
**Criticality:** **Goal-amplifying**.

### E16 — Narrative / “acts” metadata (light)  
**Problem:** Progressive disclosure without narrative intent becomes random UI chrome.  
**Extension:** Optional handoff hints: `story_role: setup | conflict | resolution`, `reveal_order`, presenter notes for what expands when—consumed only if present.  
**Outcome:** Stronger G2 storytelling; still enhance-don’t-replace.  
**Library tie:** Mostly no-library; Alpine can honor reveal_order.  
**Criticality:** **Nice-to-have**.

### E17 — Golden decks + visual regression  
**Problem:** Token + upgrades risk silent Boardroom drift.  
**Extension:** Small set of golden handoffs (minimal, charts, mermaid, alpine, mixed) for screenshot or HTML hash smoke tests after CSS changes.  
**Outcome:** SC-COMPAT + SC-VIS confidence.  
**Library tie:** None required.  
**Criticality:** **Nice-to-have** early; becomes important mid-implementation.

### E18 — A11y and reduced-motion defaults  
**Problem:** Canvas charts and carousels can exclude parts of audience; Animate defaults fight plan’s calm aesthetic.  
**Extension:** Chart animation duration 0 by default; honor `prefers-reduced-motion`; provide table or aria summary for key charts where practical; Lucide SVGs with meaningful titles when not decorative.  
**Outcome:** Digestibility (G2) for more humans; corporate friendliness.  
**Library tie:** Chart.js, Swiper, Lucide.  
**Criticality:** **Goal-amplifying**.

### E19 — Filter / multi-dimension simple UI  
**Problem:** Plan lists “simple filters” under Alpine; easy to scope-creep into mini-BI.  
**Extension:** Allow only **pre-bundled facet filters** over already-inlined slide data (e.g. show/hide cards by tag)—no network, no arbitrary query language.  
**Outcome:** Controlled G2/G3 depth.  
**Library toe:** Alpine.  
**Criticality:** **Nice-to-have**.

### E20 — Explicit alternative: deeper `gl-*` before Swiper  
**Problem:** Some comparison/story needs may be solvable with grid + disclosure without Swiper weight.  
**Extension:** Spike (later) a **CSS-only multi-panel** comparison using existing grid before accepting Swiper as default Phase 4. Keep Swiper for true swipe/overflow sequences.  
**Outcome:** Possible removal or further demotion of Swiper after alignment.  
**Library tie:** No-library alternative to Swiper.  
**Criticality:** **Alignment-gated** alternative path.

---

## 3. Cross-cutting themes (how extensions cluster)

### 3.1 “Library install ≠ product capability”
Naïve checklist = vendor file + script tag. **Product capability** = handoff pattern + layout slot + feature flag + offline pin + degrade path + validation. Extensions E01–E07, E15 embody this theme.

### 3.2 Weight budget is a product feature
Mermaid and unsubset Lucide/Swiper dominate risk. E01, E10, E11, E12, E14 treat size as design input, not an afterthought in Phase 5.

### 3.3 Parallel wiki tracks need seams, not merges
Open Props specs (E08), layout catalog/Phase2 (E09, E12, E20), PDF fidelity (E05, E13) must remain **named dependencies** in the priority list—not silently rewritten by this research.

### 3.4 No-library options are first-class
E04, E20, parts of E11 (sprite), static chart fallbacks: plan libraries are **not mandates** where platform HTML/CSS + existing modules suffice.

### 3.5 Animation remains out
Micro-affordances (instant show/hide, zero-duration Chart) may exist; cinematic motion, slide transition engines, and Swiper effect demos stay **non-goals** unless user realigns goal summary §2.2 / §4.7.

---

## 4. Mapping extensions → plan phases (beyond naive checklist)

| Plan phase | Naive checklist | High-leverage extensions to fold in |
|------------|-----------------|-------------------------------------|
| **0 Foundation** | Flag + lib_inliner + shell dual mode | **E01, E02, E14 (start pins)**, size matrix harness |
| **1 Open Props** | Import tokens | **E08** single semantic owner; no second grid |
| **2 Charts + Mermaid** | Wire libraries | **E05, E06, E07, E10, E15**, cautious E13 hooks |
| **3 Alpine** | Include Alpine + examples | **E03, E04, E18**, limit E19 |
| **4 Swiper + Lucide** | Add both | **E11, E12, E20 alternative**, keep medium priority honest |
| **5 Polish** | Docs + perf | **E09 recipes, E14 pack, E17 goldens** |

---

## 5. What “extend further” should *not* mean (link to later priority “NOT next”)

These look like extensions but **conflict** with goals or run charter:

| Anti-pattern | Why reject / defer |
|--------------|-------------------|
| Replace Boardroom with a stock Open Props aesthetic | Violates G1/G5 brand lock |
| Full Reveal.js / Slidev host | Different product |
| Always-on full Mermaid + Swiper + all Chart controllers | G4 size failure mode |
| CDN default for customer deliverables | Corporate objective |
| Live Chrome plugins / runtime npm in the deck | Breaks standalone model |
| Animation-forward “delight” pack | Plan deferral |
| Rebuild evidence pipeline to emit perfect Mermaid | Wrong layer; optional later |
| Ticketing every extension as P0 | Needs prioritisation + human alignment first |

---

## 6. Suggested inputs into priority list (preview, not ordered final)

**Likely front of queue (themes, not tickets):**  
1. Self-contained foundation + feature matrix + URL guards (E01, E02)  
2. Token layering policy aligned with existing open-props work (E08)  
3. Chart path + diagram routing policy (E05, E06) before Mermaid deep dive  
4. Mermaid safe+fit + weight controls (E07, E10)  
5. Disclosure patterns with native tier (E03, E04)  
6. Recipes + corporate pack (E09, E14)  
7. Icons subset policy (E11)  
8. Swiper only after grid-only gap proven (E12 vs E20)  

Final ordering and effort bands belong in `RESEARCH_renderer_v2_priority_list.md`.

---

## 7. Completeness relative to research objective

| Check | Status |
|-------|--------|
| Opportunities tied to plan goals | Yes (§1–2) |
| Library capabilities referenced | Yes (all six + inliner/sprite/diagram) |
| No-library approaches included | Yes (E04, E20, sprite, static chart) |
| Nice-to-have vs goal-critical labeled | Yes |
| No production implementation in this doc | Yes (research only) |
| Ready to feed priority list + alignment brief | Yes |

---

## 8. Document control

| Field | Value |
|-------|--------|
| Implementation | **None** |
| Priority + alignment | **Done** → `RESEARCH_renderer_v2_priority_list.md`, `RESEARCH_renderer_v2_alignment_brief.md` |

*End of extension opportunities.*
