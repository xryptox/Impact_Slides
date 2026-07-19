# SCOPE: Renderer v2 MVP1 (Locked)

**Status:** Locked after alignment grill — **not** an implementation ticket  
**Date:** 2026-03-26  
**Owner:** Ag1Le  
**Source material:**  
`wiki/RESEARCH_renderer_v2_goal_summary.md`,  
`wiki/RESEARCH_renderer_v2_libraries.md`,  
`wiki/RESEARCH_renderer_v2_extension_opportunities.md`,  
`wiki/RESEARCH_renderer_v2_priority_list.md`,  
`wiki/RESEARCH_renderer_v2_alignment_brief.md`  
**Plan under review:** `wiki/renderer_v2_improvement_plan.md` (where present)

---

## 1. One-paragraph freeze

Improve renderer v2 **without replacing** Boardroom / `gl-*`. **Production default is self-contained HTML**; CDN is **dev-only**. Ship a **curated Open Props → Boardroom semantic token** layer with a **single spec owner**. **JS is feature-gated** and **auto-enabled from handoff**, with **soft size warnings** (hard limits only after real bundle measurement). **Chart.js** is the numeric path via `charts.py`, with a **static fallback**. **Progressive disclosure is native-only in MVP1** (no Alpine).  

**Out of MVP1:** Mermaid, Alpine, Swiper, Lucide subset work, composition recipes as productized layouts, and full PDF parity (PDF remains a **parallel track** with a future ready-state seam).  

**Done when** offline self-contained generation is tested and **one golden deck** exercises charts + native disclosure with network off.  

**Next artifacts (in order):** this scope (done) → **P0 engineering spec** → tickets. **No implementation until P0 spec + tickets exist.**

---

## 2. Goals this MVP serves

| Code | Goal | MVP1 contribution |
|------|------|-------------------|
| **G1** | Visual aesthetic + Boardroom | Curated Open Props primitives under Boardroom semantics |
| **G2** | Human digestibility | Native disclosure patterns (tabs/accordion/detail via HTML/CSS) |
| **G3** | Complex explanations | Chart.js path (+ static fallback); Mermaid deferred to 1.1 |
| **G4** | Offline / corporate | Self-contained default, dual-mode, URL guards, size warn |
| **G5** | Enhance, don’t replace | Boardroom + `gl-*` stay foundation; modular inliner + flags |

---

## 3. Alignment decisions (authoritative)

| ID | Decision |
|----|----------|
| **D1** | Self-contained **default** for production outputs; CDN = dev-only escape hatch |
| **D2** | Soft size **warn** + report now; hard fail threshold **after** measured pins |
| **D3** | **Token/CSS always on**; all JS libraries feature-gated |
| **D4** | **One** merged Open Props / semantic-token owner — reconcile with existing `renderer_v2_open_props_*` specs; no dual-track |
| **D5** | **Curated subset** of Open Props (not full bundle) mapped into Boardroom |
| **D6** | **Chart.js** via evolving `charts.py` + **static/SVG/table fallback** when charts off or for export-oriented paths |
| **D7** | Constrained Mermaid is **product direction** → **MVP1.1**, not thin MVP1 |
| **D8** | Content taxonomy (product rule): quantitative → Chart.js; process/architecture/sequence/timeline text → Mermaid (when shipped); brand-locked catalog SVG → `diagram/` |
| **D9** | **Native-first** disclosure; Alpine only where native is insufficient |
| **D10** | **Swiper later** — after `gl-*` recipes prove remaining gaps |
| **D11** | First recipes: **data-heavy**, **process-with-details**, **comparison** (no Swiper) → **MVP1.1** |
| **D12** | PDF/print = **parallel track** + ready-state/export seam later; do not block P0–P5 HTML work |
| **D13** | Handoff is **semi-trusted** — generate-time validation; restrictive Mermaid settings when Mermaid lands |
| **D14** | Process: locked scope → **P0 spec** → tickets → implement |
| **D15** | **No animation focus** — Chart duration 0 / calm defaults; no motion workstream |
| **P1 policy** | **Auto-enable** features detected from handoff; soft size-warn; fail closed only on unknown/unsupported constructs |
| **Mermaid allowlist (1.1)** | `flowchart` + `sequence` + `timeline` only |
| **Alpine in MVP1** | **No** — native disclosure only |
| **MVP1 done bar** | Engineering acceptance (**§5**) **+ one golden offline deck** |

---

## 4. In scope vs out of scope

### 4.1 In MVP1 (themes)

| Theme | Intent |
|-------|--------|
| **P0** | Self-contained foundation, dual-mode CLI/contract, centralized inliner, tests that self-contained output has no unexpected remote URLs |
| **P1** | Feature×size gating; auto-enable from handoff; size warning/report |
| **P2** | Open Props curated subset under Boardroom; single semantic-token owner (merge/reconcile existing open-props wiki) |
| **P3** | Chart.js integration path from `charts.py`; static fallback; animations off by default |
| **P5** | Native-first progressive disclosure — at least three patterns (e.g. detail/expand, accordion-equivalent, simple tab-like CSS/HTML without Alpine) |

### 4.2 Explicitly out of MVP1

| Item | Deferred to |
|------|-------------|
| Mermaid (even constrained) | **MVP1.1** (P4) |
| Alpine.js | **MVP1.1** (P5 upgrade) |
| Swiper | Later (P8), after recipes |
| Lucide / icon subset policy implementation | Later (P6) |
| Productized composition recipes (data-heavy, process-with-details, comparison) | **MVP1.1** (P7) |
| Full PDF fidelity engineering | Parallel track (P9 seam only when needed) |
| Animation / motion pack | Non-goal (D15) |
| Replacing Boardroom or `gl-*` | Non-goal |
| CDN-default production | Non-goal |
| React/Vue/Svelte (or other SPA) in deck output | Non-goal |
| Live network fetches inside generated decks | Non-goal |

### 4.3 MVP1.1 (direction only — not specified here)

When MVP1 is done, expected follow-on (unless re-aligned):

1. **P4** — Constrained Mermaid (`flowchart` \| `sequence` \| `timeline`) + taxonomy enforcement + safe init  
2. **P5+** — Alpine for multi-state patterns native can’t express  
3. **P7** — Named recipes: data-heavy, process-with-details, comparison  
4. **P6** — Icon subset / sprite policy  
5. Ready-state hooks coordination with PDF track as needed  

---

## 5. Success criteria (MVP1 acceptance language)

Reusable from research `SC-*` where applicable; MVP1 must demonstrate:

| ID | Criterion |
|----|-----------|
| **SC-OFFLINE-1** | With self-contained mode (default production path), golden deck opens and supports declared MVP1 features **with network disabled** |
| **SC-OFFLINE-2** | Produced HTML embeds required CSS/JS or only generator-controlled local assets — no required CDN/remote script/style URLs in self-contained output |
| **SC-CLI-1** | Explicit controls exist for self-contained vs CDN-dev (and feature subsetting as designed in P1) |
| **SC-MOD-1** | Library/CSS embedding is centralized (inliner/asset module), not ad-hoc pastes across layouts |
| **SC-REG-1** | Automated tests cover inliner/self-contained “no unexpected external URL” for fixtures |
| **SC-SIZE-1** | Generator reports or warns on payload impact (baseline vs +charts at minimum); hard fail optional later |
| **SC-VIS-1..2** | Components prefer tokens; Boardroom brand remains default after Open Props primitive layer |
| **SC-CHART-1** | Handoff can drive common chart types via Chart.js in self-contained mode |
| **SC-CHART-FALLBACK** | When charts feature is off or static path selected, content remains readable (table/SVG/static) |
| **SC-IX-1** | At least three **native** disclosure patterns supported in generated markup |
| **SC-IX-2** | With JS libraries absent/off, static content remains readable |
| **SC-COMPAT-1** | Existing handoffs that don’t opt into new features still render without required schema break |
| **SC-GOLDEN-1** | One checked-in (or documented fixture) golden handoff → HTML deck exercises **charts + disclosure** and passes offline open check |

**Non-failure for MVP1:** perfect PDF twin, Mermaid, Alpine, Swiper, full Lucide, cinematic motion.

---

## 6. Risks to carry into P0 spec

| Risk | Mitigation direction |
|------|----------------------|
| Accidental CDN in “ship” output | Default self-contained; CI/fixture URL guard |
| Token dual-track with existing open-props specs | P2 starts by naming/merging owner doc |
| Chart.js weight on every deck | Feature gate + auto-enable only when handoff needs charts |
| Unknown real KB sizes | Warn-only until pins measured |
| Disclosure pattern zoo | Spec a small closed set of native patterns |
| Scope creep into Mermaid/Alpine/Swiper | This document is the cut line |

---

## 7. Next step

| Step | Output | Status |
|------|--------|--------|
| 1. Alignment grill | Decisions D1–D15 + MVP cut | **Done** |
| 2. Scope freeze | This file | **Done** |
| 3. **P0 engineering spec** | Spec markdown: inliner, dual-mode CLI, assets layout, tests, acceptance → SC-OFFLINE/CLI/MOD/REG | **Next** |
| 4. Tickets from P0 spec | GitHub issues (when asked) | Blocked on step 3 |
| 5. Implement P0 | Code | Blocked on step 4 |

Do **not** start production renderer feature work from this scope note alone.

---

## 8. Document control

| Field | Value |
|-------|--------|
| Charter | Alignment → scope; **no** implementation in the grill run |
| Supersedes | Informal “improve renderer v2” intent with locked MVP1 cut |
| Amend via | Re-open alignment on named decision IDs; don’t silently expand MVP1 |

*End of MVP1 scope lock.*
