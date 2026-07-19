# RESEARCH: Renderer v2 Libraries Inventory

**Status:** Research / alignment material (not a ticket spec)  
**Date:** 2026-03-25  
**Primary source:** `wiki/renderer_v2_improvement_plan.md`  
**Goal framing:** `wiki/RESEARCH_renderer_v2_goal_summary.md`  
**Method:** Capabilities claimed only where backed by official docs / well-known project endpoints. Offline değerl notes where network verification was incomplete. Bundle sizes are approximate from public CDN/npm conventions—**re-measure at pin time**.

---

## 0. Explored checklist (plan coverage gate)

Every CSS/JS library **named** in the improvement plan, plus **implied** library-like stacks required by architecture section.

| # | Name in plan | Kind | Covered here | Capabilites § | Goals map § | Status |
|---|--------------|------|--------------|---------------|-------------|--------|
| 1 | **Open Props** | CSS design tokens | Yes | §2.1 | Yes | **PASS** |
| 2 | **Chart.js** | JS charts | Yes | §2.2 | Yes | **PASS** |
| 3 | **Mermaid.js** | JS diagrams | Yes | §2.3 | Yes | **PASS** |
| 4 | **Alpine.js** | JS interactivity | Yes | §2.4 | Yes | **PASS** |
| 5 | **Swiper.js** | JS carousels / advanced layout | Yes | §2.5 | Yes | **PASS** |
| 6 | **Lucide** (Lucide Icons) | Icons (SVG / sprite) | Yes | §2.6 | Yes | **PASS** |
| A | **lib_inliner + assets/libs/** | Generation tooling | Yes | §3.1 | Yes | **PASS** (implied) |
| B | **CDN vs self-contained dual mode** | Delivery mode | Yes | §3.2 | Yes | **PASS** (implied) |
| C | **Boardroom + gl-\* + tokens.css stack** | Existing design foundation | Yes | §3.3 | Yes | **PASS** (foundation) |
| D | **charts.py / diagram/ enhancement surface** | Integration surface | Yes | §3.4 | Yes | **PASS** (implied) |
| E | **Icon sprite system** (inline Lucide *or* sprite) | Alternative integration | Yes | §3.5 | Yes | **PASS** (plan “or”) |

**Gate result:** All **six** named libraries have non-empty capability summaries mapped to Renderer v2 goals. Implied stacks documented so Phase 0 architecture is not invisible in research.

---

## 1. How to read each entry

Each library section includes:

- **What it is** — short definition  
- **Maturity / license** — project status + OSI-style license  
- **Size / perf notes** — rough/minified order-of-magnitude; caveats  
- **Core capabilities** — what we would actually use  
- **Gaps** — what it does *not* solve for us  
- **Map to OUR goals** — aesthetic / digestible / complex story / offline / enhance-don’t-replace  
- **Risks & integration cost** — for generator + handoff schema  
- **Alternatives** — brief, not full bake-offs  
- **Primary sources** — URLs to re-check when pinning versions  

**Renderer goal codes (from goal summary):**

| Code | Goal |
|------|------|
| G1 | Visual aesthetic / modern tokens-polish + Boardroom |
| G2 | Human digestibility / progressive disclosure |
| G3 | Complex explanations (diagram + chart + interaction combo) |
| G4 | Self-contained offline / corporate VPN-safe |
| G5 | Enhance Boardroom + `gl-*`; modular maintainability |

---

## 2. Named libraries (plan shortlist)

### 2.1 Open Props

> **Non-normative (research).** Implementation authority for tokens is
> `wiki/SPEC_renderer_v2_tokens_owner.md` (P2). MVP1 does **not** vendor the
> full upstream Open Props package.

| Field | Detail |
|-------|--------|
| **What** | A comprehensive set of **CSS custom properties** (design tokens) for colors, spacing, shadows, radii, fonts, easings, gradients, z-index, etc. Consumed as plain CSS (or bundled subsets); not a component framework. |
| **Maturity** | Mature open-source design-token pack; widely used; actively maintained under openprops.style branding. Stable enough for production CSS foundations. |
| **License** | **MIT** (project standard; confirm in the pinned package `LICENSE` at vendor time). |
| **Size / perf** | Full bundle is larger than a curated subset. Typical approach for decks: import **only needed props** (colors, size, shadow, radius, font) so CSS cost stays modest vs full “kitchen sink.” Runtime cost is near-zero (no JS). Print/PDF paths care about CSS variable support (modern Chromium OK). |
| **Core capabilities** | Token vocabulary (`--size-*`, `--shadow-*`, `--radius-*`, color scales, fluid type helpers, media predicates via props ecosystem). Composes with existing custom properties. Optional normalize / utility layers exist but are optional for us. |
| **Gaps** | Does **not** define Boardroom brand values. Does not “look Boardroom” until `semantic-tokens.css` remaps brand colors/fonts onto Open Props primitives. No charts, diagrams, or interactivity. |
| **Map to goals** | **G1 primary** (Phase 1). Supports **G5** if we layer: Open Props primitives → Boardroom semantic tokens → `components.css`. Neutral for G2/G3; enables G4 (CSS-only, easy to inline as text). |
| **Risks / cost** | Medium design cost, low runtime risk. Collision with existing parallel wiki (`renderer_v2_open_props_spec.md`, upgrade specs)—must not double-specify. Over-importing utilities can bloat or fight `gl-*`. Theme injection in `shell.py` must stay single owner of brand overrides. |
| **Alternatives** | Keep hand-rolled tokens only; Style Dictionary pipeline; Open Props **subset** copy-paste; Tailwind token export (heavier paradigm shift—usually worse fit). |
| **Sources** | https://open-props.style/ · https://github.com/argyleink/open-props · https://www.npmjs.com/package/open-props |

**Recommended use (high-level):** Extend `css/tokens.css` with Open Props **primitives**; keep Boardroom in `semantic-tokens.css`; avoid adopting Open Props as a second grid system.

---

### 2.2 Chart.js

| Field | Detail |
|-------|--------|
| **What** | Canvas-based charting library for common business chart types, configured via JSON-like option objects and datasets. |
| **Maturity** | Very mature (v3/v4 lineage); de-facto standard for simple dashboards; large ecosystem of plugins. |
| **License** | **MIT**. |
| **Size / perf** | Core minified alone is on the order of **~60–200+ KB** depending on version and whether tree-shaken / modular build is used; plugins add more. Canvas redraw is cheap for typical executive slide series (few charts per deck). Inlined into every HTML increases **file size** (plan risk table). Prefer **one shared Chart.js** in the shell, not per-slide copies. |
| **Core capabilities** | bar, line, pie, doughnut, radar, polarArea, scatter, bubble (exact set version-dependent); mixed types; scales/axes; tooltips/legends; responsive resize; scriptable options; animations (we may **disable** per “no animation focus”). Plugins for datalabels, annotation, zoom (zoom less relevant offline). |
| **Gaps** | Not a dashboard framework. Complex financial waterfalls / Gantt / network graphs need plugins or other libs. Accessibility of canvas is weaker than SVG unless we add text fallbacks. SSR/static snapshot for PDF fidelity is a **separate** problem (see PDF wiki track). |
| **Map to goals** | **G3 + G1** (Phase 2 high priority). Right object model for enhancing existing `charts.py` toward Chart.js configs. Offline via inline = **G4**. Storytelling when paired with callouts/evidence = G2/G3. |
| **Risks / cost** | High value, medium integration: need stable handoff → Chart.js config mapping; version pin; minified vendor under `assets/libs/`. Canvas + print/PDF may hash against fidelity aims. Learning curve low vs D3. |
| **Alternatives** | Apache ECharts (larger, richer); Chart.xkcd (novelty); pure SVG generators we already partly have; Observable Plot (less classic corporate). Stick to Chart.js unless ECharts-level chart density is required later. |
| **Sources** | https://www.chartjs.org/docs/latest/ · https://github.com/chartjs/Chart.js · https://www.npmjs.com/package/chart.js |

**Recommended use:** Generate Chart.js config from `charts.py`; render `<canvas>` + init script in shell; default animation **off** or minimal for corporate calm + predictable capture.

---

### 2.3 Mermaid.js

| Field | Detail |
|-------|--------|
| **What** | Text-to-diagram library: authors write Mermaid DSL; JS parses and renders SVG (or similar) diagrams in-browser. |
| **Maturity** | Mature and ubiquitous in docs tooling (GitHub, many wikis). Large surface of diagram types; occasional breaking changes between major versions—**pin carefully**. |
| **License** | **MIT**. |
| **Size / perf** | One of the **heaviest** candidates on the shortlist (often **hundreds of KB to ~1+ MB** minified depending on bundle and included diagram types). Cold parse/render cost matters if many diagrams fire on load. Prefer deferred render (visible slide / intersection) when interactivity stack allows—but keep first-paint acceptable offline. |
| **Core capabilities** | flowchart, sequence, class, state, ER, gantt, pie, user journey, git, mindmap, timeline, quadrant, sankey, architecture-style diagrams (availability depends on Mermaid version). Themable via CSS/JS config. Fits “process story” slides. |
| **Gaps** | Not a freeform illustration tool. Layout algorithms can produce awkward SVG in tight 1920×1080 cells—need max-width container rules. Complexity of DSL may push content quality issue upstream (Builder must emit valid Mermaid or we sanitize). Security: treat handoff Mermaid as **untrusted text**; follow Mermaid security guidance (e.g. `securityLevel`) so generated HTML does not become an injection path. |
| **Map to goals** | **G3 primary** (Phase 2). Complements Chart.js (**data** vs **structure/process**). Supports G1 via theming to Boardroom tokens. G4 via inlining (size pain). G5 via new `mermaid.py` or `diagram/` extension—not a second renderer. |
| **Risks / cost** | **Bundle weight** #1 concern. Version churn. Theming to Boardroom needs deliberate CSS. PDF/print capture of client-rendered SVG needs post-render wait (collision with PDF fidelity track). Integration medium–high. |
| **Alternatives** | Keep/extend custom `diagram/` SVG builders; Graphviz/dot server-side at generation (offline browser then simpler, but generation env needs Graphviz); Kroki remote (fails G4); D2, PlantUML (similar tradeoffs). Client Mermaid wins when **authoring text in JSON** is the product bet. |
| **Sources** | https://mermaid.js.org/ · https://github.com/mermaid-js/mermaid · https://www.npmjs.com/package/mermaid |

**Recommended use:** Handoff field with Mermaid source + diagram type hint; renderer inlines Mermaid core; init with Boardroom theme variables; document size impact in Phase 5 performance checklist.

---

### 2.4 Alpine.js

| Field | Detail |
|-------|--------|
| **What** | Lightweight declarative JS framework for HTML: `x-data`, `x-show`, `x-on`, `x-bind`, etc. “jQuery-sized behavior without a build step SPA.” |
| **Maturity** | Mature (v3 era widely deployed); strong docs; used for partial interactivity in static sites. |
| **License** | **MIT**. |
| **Size / perf** | Typically **~15–45 KB** min+gz class depending on version and build—**small** vs Mermaid/Chart. Fast enough for deck-scale DOM. |
| **Core capabilities** | Local component state; show/hide; class toggles; event handlers; simple lists; transitions (optional—align with deferred animation policy); plugins (collapse, focus, intersect, persist—evaluate only if needed). Ideal for **tabs, accordions, modals, simple filters**. |
| **Gaps** | Not a full app framework. Large global state or multi-slide synchronized stores get awkward—prefer **per-component** `x-data`. Does not replace layout/CSS. Screen-reader patterns need careful markup (`aria-*`), not automatic. |
| **Map to goals** | **G2 primary** (Phase 3). Unlocks progressive disclosure for dense evidence. Supports G3 when wrapping chart/diagram detail panes. Tiny inline cost helps **G4**. **G5** if we ship CSS component patterns that pair with Alpine attributes rather than rewriting layout core. |
| **Risks / cost** | Low–medium. Generator must emit valid Alpine attributes without breaking non-Alpine fallback (prefer progressive enhancement: content visible if JS fails where possible). Corporate review of inlined JS still applies. Learning curve called “low” in plan—still need example patterns. |
| **Alternatives** | Native `<details>`/`<summary>`, CSS `:target`/radio hacks (zero JS, limited UX); htmx (wrong model for offline file); Stimulus; petite-vue; full Vue/React (overkill, G5 damage). |
| **Sources** | https://alpinejs.dev/ · https://github.com/alpinejs/alpine · https://www.npmjs.com/package/alpinejs |

**Recommended use:** Ship Alpine for interactive primitives **documented as patterns** in components.css + layout templates; default to native `<details>` where adequate so not every slide pays cognitive/JS tax.

---

### 2.5 Swiper.js

| Field | Detail |
|-------|--------|
| **What** | Modern touch slider / carousel library (modules for navigation, pagination, keyboard, a11y, grid, free-mode, etc.). |
| **Maturity** | Mature, very widely used for mobile/web carousels; modular architecture in recent majors. |
| **License** | **MIT**. |
| **Size / perf** | Core + modules often **tens to low hundreds of KB** depending on imports. Prefer **modular build** (navigation + pagination + keyboard + a11y only) over full bundle. Nested horizontal swipe inside a vertical deck browser needs UX care (scroll capture). |
| **Core capabilities** | Carousels for comparisons, galleries, multi-step processes; keyboard control; accessibility module; lazy options; responsive breakpoints. Fits plan’s `comparison-carousel`, multi-step process stories. |
| **Gaps** | Not a general layout engine—**do not** replace `gl-*`. Overuse turns boardroom decks into “app carousels” (storytelling risk). Print/PDF: only first slide of carousel may capture unless expanded. |
| **Map to goals** | **G2/G3** medium priority (Phase 4). Secondary to Open Props / charts / Mermaid / Alpine per plan. G1 polish if styled to Boardroom. G4 OK if modular + inlined. G5 only as **optional layout type**, feature-flagged (`--features=swiper`). |
| **Risks / cost** | Medium. Touch vs click presenter remote behavior; a11y; CSS conflicts with grid. File size less severe than Mermaid but non-trivial. Plan correctly marks **medium priority**—should not block Phase 0–3. |
| **Alternatives** | CSS scroll-snap carousels (no/low JS); Alpine-only panel switcher; multi-slide instead of in-slide carousel (often clearer for executives). |
| **Sources** | https://swiperjs.com/ · https://github.com/nolimits4web/swiper · https://www.npmjs.com/package/swiper |

**Recommended use:** Optional feature; 1–2 layout templates max at first; keyboard + visible bullets mandatory for presenter use.

---

### 2.6 Lucide Icons

| Field | Detail |
|-------|--------|
| **What** | Open-source SVG icon set (community fork lineage of Feather-style icons); consistent 24px grid stroke icons; available as SVGs, sprite, or framework packages. |
| **Maturity** | Very active icon project; large catalog; stable naming. |
| **License** | **ISC** (confirm on pinned release; historically ISC for Lucide)—treat as permissive OSS suitable for corporate embedding after license file copy into `assets/libs/`. |
| **Size / perf** | **Do not** inline the entire icon set. Per-icon SVG is tiny; a **subset sprite** or per-use inline paths keeps decks small. Full set would be wasteful vs G4. |
| **Core capabilities** | UI chrome icons (chevron, info, warning, check, building blocks for tabs/headers); visual polish without custom illustration pipeline. Works with Alpine triggers (icon buttons). |
| **Gaps** | Not a diagram system. Not brand illustration. Does not replace evidence imagery. |
| **Map to goals** | **G1** Phase 4 polish; supports G2 affordances (disclose controls). G4 via subset sprite/inliner. G5: sprite module can rest beside existing sprite approaches in tree. |
| **Risks / cost** | Low if subsetting discipline holds. High if “import all icons.” Slight license string difference vs MIT-only mental model—still permissive but copy LICENSE. |
| **Alternatives** | Heroicons, Feather, Phosphor, Material Symbols, custom Boardroom pictograms, Unicode-only. Existing renderer sprite paths if already sufficient. |
| **Sources** | https://lucide.dev/ · https://github.com/lucide-icons/lucide · https://www.npmjs.com/package/lucide |

**Recommended use:** Build **curated sprite** (or inline only referenced icons at generation from handoff/layout templates); never ship full Lucide npm browser bundle into every deck by default.

---

## 3. Implied stacks & integration surfaces

### 3.1 `lib_inliner.py` + `assets/libs/`

| Field | Detail |
|-------|--------|
| **What** | Plan’s **critical** generation-time pipeline: vendor minified CSS/JS under `impact_slides/renderer_v2/assets/libs/`, embed into HTML when `--self-contained` (plan: base64 for CSS, raw for JS—exact encoding is an implementation detail to validate later). |
| **Maturity** | **Not assumed present** as finished product in current tree (gap until build run). Design is standard static asset inlining. |
| **License** | N/A (our code); must retain **upstream** license files for vendored libs. |
| **Size / perf** | Determines whether G4 is real. Single shared shell include vs per-slide duplication is the main architecture decision. |
| **Capabilities needed** | Fetch or commit pins; integrity (checksum); minify preference; feature-flag subsetting (`--features=...`); CDN fallback path for dev. |
| **Goals** | **G4 backbone**; enables all library phases. |
| **Risks** | Supply-chain (pin versions, preferably commit vendored files); stale CDN URI when not self-contained; base64 CSS size overhead. |
| **Alternatives** | Single build step packing with esbuild; service-worker caching (usually fails corporate USB-passivate use cases); pure commit of libs without downloader. |

### 3.2 CDN vs self-contained dual mode

| Field | Detail |
|-------|--------|
| **What** | `--self-contained` production path + `--use-cdn` (or default dev) for speed. |
| **Goals** | G4 without punishing day-to-day renderer development. |
| **Risks** | Accidental ship of CDN mode to customers; version skew between CDN URI and vendored pin. |
| **Mitigation** | Default **self-contained** for release CLI examples; CI assert no `https://` script src in release fixtures. |

### 3.3 Boardroom + `gl-*` + tokens / components CSS

| Field | Detail |
|-------|--------|
| **What** | Existing design foundation: custom Boardroom look, grid primitives, `tokens.css` / `semantic-tokens.css` / `components.css`, shell theme injection. |
| **Role vs libraries** | **Not replaceable** by Open Props/Swiper. Open Props feeds tokens; Alpine/Swiper decorate components; Chart/Mermaid occupy content regions inside grid cells. |
| **Goals** | **G5 / G1 non-negotiable constraint.** |

### 3.4 `charts.py` / `diagram/` / planned `mermaid.py`

| Field | Detail |
|-------|--------|
| **What** | Python generation surface producing markup + config for Chart.js and Mermaid (and any legacy static charts). |
| **Goals** | G3 without forcing Builder to invent frontend code. |
| **Risks** | Dual diagram pipelines (custom SVG vs Mermaid) if both remain—need clear “when to use which.” |

### 3.5 Icon sprite system (Lucide or existing)

| Field | Detail |
|-------|--------|
| **What** | Plan allows “inline Lucide **or** create icon sprite system.” Sprite is often superior for repeated icons + caching in one HTML file. |
| **Goals** | G1 + G4 size control. |
| **Note** | Research tree may already have sprite-related code—prefer **extend** over third concurrent icon pipeline. |

---

## 4. Comparative snapshot (for prioritization later)

| Library | Phase (plan) | Priority | Approx size impact | Goal primary | Offline ease | Integration difficulty |
|---------|--------------|----------|--------------------|--------------|--------------|------------------------|
| Open Props | 1 | High | Low (CSS subset) | G1 | Easy | Low–Med (design) |
| Chart.js | 2 | High | Med | G3 | Easy | Med |
| Mermaid.js | 2 | High | **High** | G3 | Easy but heavy | Med–High |
| Alpine.js | 3 | High | Low | G2 | Easy | Low–Med |
| Swiper.js | 4 | Medium | Med | G2/G3 | Easy | Med |
| Lucide | 4 | Medium | Low **if subset** | G1 | Easy | Low |
| Inliner stack | 0 | Critical | N/A (enabler) | G4 | — | Med |

**Suggested dependency spine (research view, not schedule):**  
Inliner (0) → Open Props tokens (1) → Chart + Mermaid feature flags (2) → Alpine patterns (3) → Swiper optional + Lucide sprite (4) → harden/docs (5).

---

## 5. Mapping matrix: library × plan success criteria

| Success criterion (plan §5) | Open Props | Chart.js | Mermaid | Alpine | Swiper | Lucide | Inliner |
|----------------------------|------------|----------|---------|--------|--------|--------|---------|
| More modern / professional look | ●●● | ●● | ● | ● | ●● | ●●● | ● |
| Rich data viz + diagrams | · | ●●● | ●●● | ● | ● | · | ● |
| Progressive disclosure | · | · | · | ●●● | ●● | ● | ● |
| Corporate offline reliability | ● | ●● | ●● | ●●● | ●● | ●● | ●●● |
| Backward compatible Boardroom/grid | ●●●* | ●● | ●● | ●● | ●* | ●●● | ●● |
| Easy to extend later | ●● | ●● | ●● | ●●● | ●● | ●● | ●●● |

\*Only if we refuse to let Swiper/Open Props utilities replace `gl-*`.

---

## 6. Explicit non-claims / research limits

1. **Versions not pinned** in this research doc—pinning is an implementation/alignment step (record exact npm versions + SRI/checksums then).  
2. **Exact KB numbers** should be re-measured from the chosen minified files; table uses order-of-magnitude maturity knowledge.  
3. **No production vendoring** performed in this run (docs only).  
4. Security/corporate review of third-party minified JS is assumed required before customer ship—not waved away.  
5. Parallel PDF fidelity work may constrain Chart.js animation, Web fonts, and Mermaid async render—flag in priority/alignment docs, not solved here.

---

## 7. Completeness self-check (against objective)

| Check | Result |
|-------|--------|
| Every named plan library has capabilities § | **Yes** (§2.1–2.6) |
| Goals mapping on each | **Yes** |
| Risks + alternatives on each | **Yes** |
| Sources cited | **Yes** (official sites + GitHub + npm) |
| Explored checklist table | **Yes** (§0) PASS on all six |
| Implied inliner/CDN/Boardroom/charts-diagram/sprite | **Yes** (§3) |
| No production feature implementation | **Yes** (wiki only) |

---

## 8. Pointers to sibling research

| Deliverable | Role |
|-------------|------|
| `wiki/RESEARCH_renderer_v2_goal_summary.md` | Goals / scope / success language |
| `wiki/RESEARCH_renderer_v2_extension_opportunities.md` | **Done** — extensions beyond naïve checklist |
| `wiki/RESEARCH_renderer_v2_priority_list.md` | **Done** — ordered themes P0–P9, S/M/L |
| `wiki/RESEARCH_renderer_v2_alignment_brief.md` | **Done** — user decisions + next step |

---

*End of libraries research inventory. Re-verify licenses, versions, and bundle bytes at pin time before any implementation.*
