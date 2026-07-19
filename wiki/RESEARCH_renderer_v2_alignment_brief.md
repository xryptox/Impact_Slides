# RESEARCH: Renderer v2 Alignment Brief

**Audience:** Product owner / maintainer (Ag1Le) before any specs or tickets  
**Status:** Research package complete — **ready for alignment**, not implementation  
**Date:** 2026-03-25  
**Plan under review:** `wiki/renderer_v2_improvement_plan.md` (Draft for Review)

---

## 1. Why this brief exists

A GNHF research run produced **wiki-only** material to explore Renderer v2 improvement options from the plan: goals, library fit, extension ideas beyond a naive checklist, and a **high-level priority sequence**.

**This is not:**

- A sprint plan or GitHub issue dump  
- Permission to implement Phases 0–5  
- A replacement for existing open-props / phase2 / PDF wiki specs  

**This is:** material so you can decide **direction and tradeoffs**, then authorize a later pass that writes real specs/tickets.

---

## 2. Pointers to the research pack

| Doc | Role | Path |
|-----|------|------|
| **Goal summary** | Restated goals, in/out of scope, success-criteria language (`SC-*`) | `wiki/RESEARCH_renderer_v2_goal_summary.md` |
| **Libraries** | Full inventory of plan libraries + implied stacks; capabilities ↔ goals; explored checklist | `wiki/RESEARCH_renderer_v2_libraries.md` |
| **Extension opportunities** | E01–E20 high-level extensions (critical vs nice-to-have) | `wiki/RESEARCH_renderer_v2_extension_opportunities.md` |
| **Priority list** | Ordered themes **P0–P9**, dependencies, effort bands, what **not** to do next | `wiki/RESEARCH_renderer_v2_priority_list.md` |
| **This brief** | Decisions + proposed next step after you reply | `wiki/RESEARCH_renderer_v2_alignment_brief.md` |
| **Source plan** | Original phased roadmap | `wiki/renderer_v2_improvement_plan.md` |

**Related context (do not ignore when writing later specs):**  
`renderer_v2_open_props_spec.md`, `renderer_v2_open_props_upgrade_specs.md`, `renderer_v2_phase2_spec.md`, `renderer_v2_pdf_fidelity_spec.md`, spatial/layout/grid wiki notes, `CONTEXT.md` / ADRs as needed.

---

## 3. Bottom line (research synthesis)

1. **Keep Boardroom + `gl-*`.** Libraries layer on; they do not replace the design system.  
2. **Self-contained HTML is non-negotiable** for corporate/VPN use; treat CDN as dev-only.  
3. **Do not ship “all six libs in every deck.”** Feature×size gating is as important as the libs themselves (especially **Mermaid** weight).  
4. **Strongest “extend further” value is product contract**, not more npm packages: disclosure patterns, chart-vs-Mermaid-vs-`diagram/` taxonomy, composition recipes, dual-mode CI guards.  
5. **Reorder slightly vs raw plan weeks:** foundation + gates first; **native-first disclosure** before heavy Alpine; **`gl-*` recipes before Swiper**; Swiper stays **medium / optional**; PDF is a **named seam**, not a silent add-on.  
6. **Parallel wiki tracks** (open-props tokens, phase2 layouts, PDF fidelity) can collide with Phase 1/4/5 — alignment must name a single owner per concern.

**Plan library checklist (research coverage):**  
Open Props · Chart.js · Mermaid.js · Alpine.js · Swiper.js · Lucide — **all explored** in the libraries doc with capabilities mapped to goals (plus implied inliner/CDN/Boardroom stacks).

---

## 4. Decisions needed from you

Answer in whatever form you prefer (inline replies, annotated copy). Items marked ★ block a coherent first MVP scope.

### 4.1 Product defaults ★

| # | Decision | Options / prompt | Research lean |
|---|----------|------------------|---------------|
| D1 | **Production generate default** | Self-contained always vs opt-in flag | Self-contained **default** for “release” outputs |
| D2 | **Max HTML budget** | Soft target (e.g. “warn > N MB”) / hard fail / no limit | Measure per feature; warn + feature gates (P1) |
| D3 | **Always-on libraries** | None vs Open Props CSS only vs icons always | Prefer **minimal always-on** (tokens/CSS); JS feature-gated |

### 4.2 Design system ownership ★

| # | Decision | Prompt | Research lean |
|---|----------|--------|---------------|
| D4 | **Semantic token owner** | New Open Props work vs existing `renderer_v2_open_props_*` specs — one sequence | **One owner doc**; subsume/merge, don’t dual-track |
| D5 | **Open Props surface** | Full props vs curated subset in shipped CSS | Curated subset mapped to Boardroom |

### 4.3 Visualization ★

| # | Decision | Prompt | Research lean |
|---|----------|--------|---------------|
| D6 | **Chart.js confirmed?** | Keep vs lighter lib if size dominates | Keep Chart.js if numeric story slides are core |
| D7 | **Mermaid in MVP1?** | Yes full / yes constrained types / defer | **Constrained types** or defer if size/security dominate |
| D8 | **Three-way taxonomy** | Who owns process diagrams: Mermaid vs existing `diagram/` | Explicit routing table before build (E06) |

### 4.4 Interactivity & layout ★

| # | Decision | Prompt | Research lean |
|---|----------|--------|---------------|
| D9 | **Disclosure strategy** | Alpine-default vs **native-first** + Alpine where needed | **Native-first** (E04) |
| D10 | **Swiper in MVP?** | Implement medium-priority carousels now / later / never | **Later**; prove recipes first (P7 before P8) |
| D11 | **Supported layout recipes** | Which 2–4 “story” compositions are product-supported first | Data-heavy + process-with-details as starters |

### 4.5 Export & corporate

| # | Decision | Prompt | Research lean |
|---|----------|--------|---------------|
| D12 | **PDF/print in this roadmap?** | In-scope parity vs interactive-HTML-only + parallel PDF track | **Parallel track** with ready-state seam (E13); don’t block P0–P5 |
| D13 | **Trust model** | Handoff always trusted internal vs need sanitize Mermaid/HTML | Document trust boundary; sanitize if any untrusted input |

### 4.6 Process

| # | Decision | Prompt | Research lean |
|---|----------|--------|---------------|
| D14 | **Next artifact after alignment** | Specs only / tickets only / thin vertical slices | **Locked scope note → Phase-0/P0 spec → tickets** |
| D15 | **Animation policy** | Confirm plan deferral | **Defer** motion focus |

---

## 5. Open questions (research could not close)

- Exact **byte weights** of chosen minified builds in *our* inliner (need measure in a later engineering spike — libraries doc has qualitative/public notes only).  
- How much of **current** `renderer_v2` (`charts.py`, `diagram/`, sprite, shell) already overlaps the plan vs true greenfield — tree was noticed as partial; no production changes made this run.  
- **CI environment** constraints for vendoring (license scan, pinned hashes, offline npm/cache).  
- Whether **evidence_manifest / handoff schema** versioning is willing to move in lockstep with chart/mermaid blocks.  
- Corporate **CSP** expectations for inline scripts (Alpine/Chart/Mermaid) in locked-down browsers.  
- Printer/PDF engine choice doesn’t live fully in the improvement plan — fidelity wiki is the better source once D12 is chosen.

---

## 6. Proposed priority after your OK (no tickets yet)

If you accept the research lean without major changes, the **first engineering epic family** should be:

1. **P0** Self-contained inliner + dual-mode CLI + tests  
2. **P1** Feature gates + size reporting  
3. Then **either** token track **P2** **or** Chart track **P3** depending on which pain is hotter  
4. **P5** disclosure (native-first) before Swiper  
5. **P4 / P8** only with explicit yes on Mermaid weight and carousel value  

Explicitly **not** first: animation systems, React islands, full Lucide dump, deck-level Swiper, silent PDF rewrite.

See full theme write-ups: `wiki/RESEARCH_renderer_v2_priority_list.md`.

---

## 7. Proposed next step **after** alignment (you drive)

| Step | Owner | Output |
|------|-------|--------|
| 1. You answer §4 (even partially) | User | Annotated decisions |
| 2. Freeze an **MVP scope paragraph** (which P’s, which libs) | User + agent | Short wiki note or ADR stub |
| 3. Write **engineering specs** only for unlocked themes (start P0) | Agent/human | Spec markdown (not this research run) |
| 4. File **tickets** from specs | Human/`gh` when asked | Issues with acceptance ≈ `SC-*` |
| 5. Implement | Dev run | Production renderer — **out of this research charter** |

**Do not skip to tickets** while D1, D4, D7, D9, D10 remain open — those reorder the backlog.

---

## 8. Risks to watch in alignment discussion

| Risk | Why it matters |
|------|----------------|
| Mermaid + Chart + Swiper + Alpine all “on” | Offline HTML size and paint cost |
| Ignoring existing open-props/PDF specs | Rework and brand inconsistency |
| Alpine-only disclosure | Heavier JS and weaker no-JS degrade |
| Swiper as deck chrome | Fights fixed slide model / export |
| CDN “just for now” in customer builds | VPN failures — violates primary corporate goal |

---

## 9. Research charter compliance (this run)

| Constraint | Met? |
|------------|------|
| No full plan implementation | Yes |
| No production renderer feature work | Yes (wiki only) |
| No invented GitHub tickets | Yes |
| Additive `wiki/` research docs | Yes |
| All plan-named libraries researched + goal-mapped | Yes — see libraries explored checklist |
| Ordered high-level priorities + alignment material | Yes — priority list + this brief |

---

## 10. One-page ask

**Please confirm or override:**

1. Self-contained **default** for production output.  
2. **Feature-gated** JS libraries with a size conscience.  
3. **Open Props** under Boardroom with **one** token-spec owner.  
4. Chart.js **yes**; Mermaid **constrained or phased**; taxonomy with existing `diagram/`.  
5. **Native-first** disclosure; Alpine secondary.  
6. **Swiper later**, in-slide only.  
7. PDF **parallel**, with an export seam — not a blocker for P0–P5.  
8. Next: **you reply → MVP freeze → P0 spec** (still no drive-by implementation).

Once those land, the research package has done its job and implementation planning can begin under a separate charter.
