# SPEC: Renderer v2 — P5 Native-First Progressive Disclosure

**Status:** Engineering PRD — ready to ticket  
**Date:** 2026-07-19  
**Theme:** P5 (MVP1)  
**Scope lock:** `wiki/SCOPE_renderer_v2_mvp1.md`  
**Depends on:** P0 complete (shell/CSS). **Not blocked on P1** (no Alpine/JS lib). **Soft dependency on P2** (spacing/radius/focus tokens). Independent of P3 except shared golden later.  
**Alignment:** D9 (native-first; Alpine only where native insufficient — Alpine **out of MVP1**), D3 (no new always-on JS for disclosure), D15 (no motion focus), SC-IX-1, SC-IX-2, SC-COMPAT-1, SC-GOLDEN-1 (disclosure half)  
**Success criteria:** SC-IX-1 (≥3 native patterns), SC-IX-2 (readable with JS libs absent), contribution to SC-GOLDEN-1 with P3  
**Confirmed seams (user lock):** primary = `render_deck` generated markup; supporting = declarative handoff → native HTML/CSS expansion. **Three patterns:** (A) `<details>`/summary expand, (B) accordion-equivalent, (C) simple tab-like without Alpine.

---

## Problem Statement

Dense Boardroom slides bury secondary content (methodology, footnotes, alternate cuts, definitions) in the same visual plane as the headline story. Viewers cannot progressively reveal detail without clutter. Research called for progressive disclosure, but MVP1 explicitly **rejects Alpine** for this phase. There is no small, renderer-understood set of **native** disclosure patterns, so authors cannot request tabs/accordion/detail portably, and SC-IX-1 remains unmet.

## Solution

Ship **three native-only disclosure patterns** as productized generator output:

1. **Detail / expand** — `<details>` + `<summary>` (and Boardroom-styled chrome).  
2. **Accordion-equivalent** — multiple expandable sections using native details (or equivalent pure HTML/CSS) with documented open behavior (multi-open via independent details is the default MVP; exclusive-open only if achievable without JS — do not pull Alpine).  
3. **Simple tab-like** — mutually exclusive panels via **native HTML/CSS only** (e.g. radio-group CSS tabs or accessible tablist implemented without Alpine/Swiper). Must work offline and remain readable if advanced CSS fails (all panel content still in DOM or first panel visible + others reachable).

Authors opt in through a **small declarative handoff convention** (additive). The renderer expands declarations into markup + CSS. **No Alpine, no Swiper, no new JS library.** Deck chrome JS (fitStage/nav) stays as today; disclosure must not require it.

## User Stories

1. As a presentation author, I want to declare a detail/expand block in the handoff, so that methodology stays one click away from the headline.
2. As a presentation author, I want an accordion-equivalent for several secondary sections, so that long appendices do not dominate the slide.
3. As a presentation author, I want simple tabs for two–few alternate views, so that comparison-within-slide is possible without Swiper.
4. As a presentation author, I want an additive schema/convention, so that old handoffs without disclosure still render (SC-COMPAT-1).
5. As a presentation author, I want defaults for “which panel starts open,” so that live presenting is predictable.
6. As a viewer, I want disclosure controls usable with mouse and keyboard at presentation scale, so that I am not stuck.
7. As a viewer, I want Boardroom styling on disclosure chrome, so that controls do not look like raw browser widgets only (styled, still native).
8. As a viewer with no optional JS libraries loaded, I want disclosure still usable, so that SC-IX-2 holds.
9. As a viewer with network disabled, I want disclosure CSS present in the single file, so that offline decks work.
10. As a corporate recipient, I want no Alpine runtime, so that MVP1 security/size story stays simple.
11. As a screen-reader user, I want native semantics preferred (`details`/`summary`; tabs with appropriate roles only if implemented carefully), so that a11y is not an afterthought.
12. As a renderer developer, I want one expansion path from declaration → HTML, so that recipes do not fork three ad-hoc implementations.
13. As a renderer developer, I want pattern ids stable (`detail` / `accordion` / `tabs` or equivalent), so that tests and Builder docs share vocabulary.
14. As a renderer developer, I want CSS for disclosure in the always-on Boardroom CSS stack (or a small dedicated fragment always loaded), so that we do not invent a `disclosure` JS feature id in MVP1.
15. As a layout author, I want disclosure blocks to compose inside existing `gl-*` regions, so that G5 holds.
16. As a layout author, I want productized full-slide recipes (data-heavy, process-with-details) deferred to MVP1.1, so that P5 stays pattern-sized not recipe-sized.
17. As a CI maintainer, I want fixture handoffs exercising all three patterns, so that SC-IX-1 is mechanical.
18. As a CI maintainer, I want assertions that Alpine/Swiper markers are absent in these outputs, so that scope creep is caught.
19. As a CI maintainer, I want tests via `render_deck` HTML inspection, so that seams stay high.
20. As a support engineer, I want failed/unknown pattern ids to fail closed or ignore with clear validation messaging (pick one; recommendation: **fail closed on unknown pattern id** when disclosure is explicitly declared), so that typos do not silent-no-op.
21. As a product owner, I want exactly three patterns in MVP1, so that the zoo does not explode.
22. As a product owner, I want Alpine deferred to MVP1.1 for multi-state cases native cannot express, so that D9 remains honest.
23. As a design editor, I want tokens (space/radius/ink) used for disclosure chrome when P2 exists, so that styling is not a third parallel scale.
24. As a keyboard presenter, I want focus not trapped in a way that breaks slide arrow navigation, so that deck JS and disclosure coexist.
25. As a mobile/narrow viewer (secondary), I want details/accordion usable even if tabs degrade, so that the simplest patterns remain robust.
26. As a Builder/prompt author, I want documented JSON shapes for panels (title, body, defaultOpen), so that LLM handoffs can target them.
27. As a Builder/prompt author, I want content bodies to accept existing rich text/list structures the renderer already escapes safely, so that we do not invent a new HTML-injection channel.
28. As a security reviewer, I want panel bodies passed through existing escape/sanitization paths, so that disclosure is not an XSS footgun (handoff semi-trusted — D13 spirit).
29. As an agent implementer, I want non-goals listing Alpine/Swiper/recipes, so that `/implement` stays bounded.
30. As an MVP1 acceptance owner, I want disclosure fixtures ready to combine with P3 charts in a later golden deck (SC-GOLDEN-1), so that done-bar work is staged.
31. As a docs reader, I want README or authoring notes listing the three patterns and example handoff snippets, so that humans discover them.
32. As a QA explorer, I want each pattern demoable on its own slide in a fixture, so that manual check is fast.
33. As a theme user, I want disclosure chrome to respect theme overrides for colors where practical, so that light rebrands do not leave unstyled islands.
34. As a print-curious user, I want details content available in DOM for print expansions where browser allows, so that we do not rely on JS open state (best-effort; not a PDF project).
35. As a localization-minded author, I want summary labels to be handoff-provided strings, so that UI chrome is not English-hardcoded only (default English labels allowed for built-in “Details” if needed).
36. As a performance-minded operator, I want no new JS library bytes for disclosure, so that P1 size story is unchanged by P5.
37. As a future Alpine owner (1.1), I want native pattern ids reusable so Alpine can replace only the patterns that need it later, so that handoffs do not fully rewrite.
38. As a future recipes owner (P7), I want to compose these primitives into process-with-details without redefining markup, so that P5 is the substrate.
39. As a gridlines debugger, I want disclosure regions still understandable under `--debug` outlines where applicable, so that layout debugging continues.
40. As a strict validator, I want optional schema validation hooks for disclosure declarations if handoff validation already runs, so that bad shapes surface early.

## Implementation Decisions

1. **Primary seam:** `render_deck` HTML output. Tests assert pattern markers and structure in `presentation.html`.
2. **Supporting seam:** declarative disclosure expansion — handoff fragment → HTML string(+CSS). Prefer a single helper/module used by layout recipes rather than copy-paste per layout.
3. **Normative pattern set:**  
   - **`detail`** — one `<details>`/`<summary>` block.  
   - **`accordion`** — list of sections as details (multi-open default).  
   - **`tabs`** — simple tab-like panels without Alpine (implementation technique free if CSS/HTML-only and tested).  
4. **Declaration shape (conceptual — names flexible):** a disclosure object with `pattern` (or `type`), `panels[]` with `title`/`label` + `body` (structured content or safe text lines), and optional `default_index` / `default_open`. Additive under existing content/visual_spec areas; exact path documented in owner notes for Builder.
5. **No Alpine / no Swiper / no new feature id required** for disclosure CSS/JS library. Do not put `alpine` in `features_enabled` for these patterns.
6. **CSS:** always-on Boardroom styling for disclosure chrome (components or small dedicated CSS in the existing concat). Soft-prefer P2 tokens when present.
7. **A11y baseline:** prefer native elements; if tabs use ARIA tablist, follow core keyboard expectations or choose a simpler radio/CSS pattern with documented tradeoffs in the spec notes during impl — do not ship inaccessible fake tabs.
8. **Unknown pattern id:** fail closed when disclosure is explicitly requested with an unknown pattern (validation error / strict path).
9. **Escaping:** all author strings through existing escape helpers; no raw HTML passthrough from handoff unless an already-trusted path exists (default: no).
10. **Recipes out of scope:** do not implement full data-heavy / process-with-details / comparison recipe products (P7 / MVP1.1). Optional: one layout can *host* a disclosure block to prove composition.
11. **Golden:** P5 delivers disclosure fixtures; combined charts+disclosure golden may land when P3+P5 both done (can be a small follow-on ticket under MVP1 done-bar, not mandatory inside P5 if P3 incomplete).
12. **Ticket slicing suggestion:** (1) handoff convention + `detail` pattern end-to-end; (2) `accordion`; (3) `tabs`; (4) CSS polish + a11y pass; (5) docs + fixture pack.
13. **Labels:** `ready-for-agent`, `renderer-v2`, `P5`.

## Testing Decisions

**What good tests look like**

- `render_deck` on fixture handoffs → HTML contains expected native structures (`<details>`, tab markers, etc.).
- Assert Alpine.js / Swiper strings absent.
- Assert content titles/bodies escaped and present.
- Assert unknown pattern fails closed.
- Assert handoffs without disclosure unchanged (compat).
- Do not require browser automation for MVP if static HTML structure + CSS presence suffice; optional manual QA note for keyboard tabs.

**Prior art**

- `tests/test_renderer_v2_gates.py`, themes, self_contained — HTML inspection patterns.
- Mini handoff fixtures under `tests/fixtures/renderer_v2/`.

**Suggested home:** `tests/test_renderer_v2_disclosure.py` + fixtures.

## Out of Scope

- Alpine.js (MVP1.1).
- Swiper / carousels.
- Productized composition recipes (P7).
- Mermaid, Chart.js (P3/P4) except coexistence.
- Animation/transition packs.
- Exclusive-open accordion **if** it requires JS — do not add JS just for exclusive open.
- Filters, client-side search, advanced multi-state UIs (E19).
- PDF-specific disclosure behavior.
- Replacing Boardroom/`gl-*`.

## Further Notes

### Why CSS always-on (not feature-gated)

Disclosure patterns are HTML/CSS-only and small. Gating them behind a JS feature id would confuse the P1 vocabulary (`alpine` is not used). Always-on CSS keeps SC-IX-2 simple.

### Pattern notes

| Pattern | Native substrate | MVP behavior |
|---------|------------------|--------------|
| detail | `<details>`/`<summary>` | Single expand block |
| accordion | multiple `<details>` | Multi-open |
| tabs | CSS/HTML only | 2–few panels; default panel selected |

### Acceptance checklist

| ID | Criterion |
|----|-----------|
| P5-AC1 | Declarative handoff can request `detail` and get `<details>`/`<summary>` in output |
| P5-AC2 | Declarative `accordion` emits multi-section expandable native markup |
| P5-AC3 | Declarative `tabs` emits simple tab-like native markup without Alpine |
| P5-AC4 | Boardroom-styled chrome for the three patterns in always-on CSS |
| P5-AC5 | No Alpine/Swiper dependency or feature enablement required |
| P5-AC6 | Unknown pattern id fails closed when disclosure declared |
| P5-AC7 | Author text escaped; no new HTML injection channel |
| P5-AC8 | Handoffs without disclosure still render (SC-COMPAT-1) |
| P5-AC9 | Fixture(s) cover all three patterns; docs describe convention |
| P5-AC10 | Suites green; offline self-contained still valid |

### Seams locked (2026-07-19)

4. Primary = `render_deck` + declarative expansion — **yes**  
5. Three patterns detail / accordion / tabs — **yes**  
6. P5 not blocked on P1; soft on P2; P3 hard-blocked on P1 only — **yes**  

*End of P5 spec.*
