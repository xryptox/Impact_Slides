# SPEC: Renderer v2 — P2 Open Props under Boardroom (Single Token Owner)

**Status:** Engineering PRD — ready to ticket  
**Date:** 2026-07-19  
**Theme:** P2 (MVP1)  
**Scope lock:** `wiki/SCOPE_renderer_v2_mvp1.md`  
**Depends on:** P0 complete (CSS emission path stable). Soft dependency on P1 (not blocked: tokens are always-on).  
**Alignment:** D3 (token/CSS always on), D4 (one merged token-spec owner), D5 (curated subset, not full bundle), D14  
**Success criteria:** SC-VIS-1..2 (components prefer tokens; Boardroom remains default brand), SC-COMPAT-1, SC-MOD-1 (CSS still centralized)  
**Confirmed seams (user lock):** primary = CSS-in-output / theme regression via `render_deck` (+ existing theme tests); owner wiki doc is the documentation seam. **Lighter path — formalize & document the already-present Open Props–style scales; do not vendor full upstream Open Props in P2.**

---

## Problem Statement

Boardroom decks already look intentional, but the token story is split across tribal knowledge, parallel research notes, and CSS files that grew “Open Props–style” scales without a single product owner. Contributors (human and agent) do not know:

- which layer is primitive vs brand vs component,
- whether upstream Open Props is a dependency or just an inspiration,
- which names are stable for theme injection,
- or how to add a token without hard-coding another magic px in `components.css`.

Without a freeze, P3 chart theming and P5 disclosure styling will keep inventing one-off values, and any future “real Open Props import” risks a second source of truth against `semantic-tokens.css`.

## Solution

Make **one documented, curated token system** the law of the renderer CSS stack:

1. **Declare ownership:** a single wiki token-spec (this theme’s owner doc, merged intent of any historical `renderer_v2_open_props_*` notes) is authoritative for names, layers, and extension rules.
2. **Keep the lighter implementation path:** retain and formalize the **already-shipped** primitive scales in Boardroom CSS (`--size-*`, `--radius-*`, `--shadow-*`, and related curated scales) as the Open Props–*inspired* primitive layer — **not** a full upstream Open Props bundle.
3. **Preserve layering:** primitives → Boardroom brand / semantic map → `gl-*` components / chart CSS. Brand stays Boardroom (navy/blue/ink/fonts).
4. **Prefer tokens in components:** reduce remaining hard-coded spacing/radius/shadow literals in component CSS where a primitive/semantic token already exists or is cheap to add — without a full visual redesign.
5. **Prove via render seam:** theme injection and default paint still work; Boardroom defaults remain; curated primitives remain present; kitchen-sink Open Props utility surface is absent.
6. **Always on:** token CSS ships in every deck (D3); not feature-gated.

## User Stories

1. As a deck viewer, I want Boardroom colors and typography unchanged by default, so that brand trust is preserved.
2. As a deck viewer, I want visual rhythm (spacing, radius, shadow) to feel consistent across layouts, so that slides read as one system.
3. As a presentation author, I want theme overrides via semantic token names to keep working, so that light rebrands do not fork layouts.
4. As a presentation author, I want overrides to not require knowing primitive scale indices, so that I set `--color-primary` not `--size-7`.
5. As a renderer developer, I want a single owner doc for tokens, so that I never invent a parallel open-props spec.
6. As a renderer developer, I want a clear primitive vs semantic vs brand split, so that I know where a new value belongs.
7. As a renderer developer, I want curated primitives only, so that we do not ship unused Open Props kitchen-sink CSS.
8. As a renderer developer, I want existing `--size-*` / `--radius-*` / `--shadow-*` scales recognized as the official primitive set, so that components already using them are legitimized not rewritten blindly.
9. As a renderer developer, I want guidance for when to add a semantic alias vs a raw primitive use, so that `components.css` does not become two dialects.
10. As a renderer developer, I want chart CSS to consume Boardroom/semantic color tokens where practical, so that P3 can theme charts without hex hunting.
11. As a renderer developer, I want load order of CSS fragments documented and stable, so that override specificity stays predictable.
12. As an agent implementer, I want tests at `render_deck` HTML/CSS output, so that I do not couple to private CSS concat helpers.
13. As an agent implementer, I want explicit non-goals (no full upstream pin, no utility-class framework), so that review rejects scope creep.
14. As a CI maintainer, I want theme regression tests to stay green, so that token edits cannot silently drop the theme `<style>` contract.
15. As a CI maintainer, I want assertions that key Boardroom brand markers remain in default CSS, so that “token cleanup” cannot bleach the brand.
16. As a CI maintainer, I want assertions that full Open Props marker baggage is absent (e.g. no mass `--font-flat`/`--ease-elastic` dump unless curated), so that subset discipline is enforced.
17. As a design editor, I want semantic names for surfaces, ink, accent, space, radius, and shadow, so that I can reason without reading every layout recipe.
18. As a design editor, I want gradients and stage tokens documented if they remain first-class, so that they are not accidental API.
19. As a corporate brand manager, I want navy/blue/Source Sans/IBM Plex to remain the default stack, so that decks match Boardroom Earnings language.
20. As a corporate brand manager, I want theme injection to be the supported escape hatch, so that one-off hex edits inside recipes are discouraged.
21. As a docs reader, I want the owner doc to supersede scattered research bullets on Open Props, so that research stays historical and the spec stays normative.
22. As a docs reader, I want a short “how to add a token” procedure, so that contributions stay reviewable.
23. As a P1/P3 developer, I want tokens always present regardless of feature flags, so that gated JS never gates brand CSS.
24. As a P5 disclosure developer, I want spacing/radius/focus tokens available, so that native disclosure patterns do not hard-code a third scale.
25. As a PDF-track developer, I want tokenized colors/fonts rather than ad-hoc values, so that print/CSS capture stays coherent later.
26. As a support engineer, I want DECK_META/theme behavior unchanged except additive docs, so that field support playbooks still work.
27. As an open-source license reviewer, I want clarity that P2 does **not** vendor upstream Open Props code, so that THIRD_PARTY.md is not falsely expanded.
28. As an open-source license reviewer, I want any future upstream pin deferred and explicit, so that MIT attribution is handled in that later theme.
29. As a layout author, I want `gl-*` geometry to remain the layout system, so that Open Props never becomes a second grid.
30. As a layout author, I want padding/gap tokens to map to the primitive size scale, so that 4px rhythm stays intact.
31. As a quality reviewer, I want a light pass reducing obvious duplicate literals in components when tokens already exist, so that SC-VIS improves without a rewrite.
32. As a quality reviewer, I want “no drive-by layout redesign” as a rule, so that token PRs are not secret visual refounds.
33. As a product owner, I want D4 satisfied by one owner doc + matching CSS, so that dual-track open-props wiki debt is closed.
34. As a product owner, I want D5 satisfied by curation rules in that doc, so that “full bundle” cannot sneak in via dependency addition.
35. As a historical-research reader, I want research files left in place but marked non-normative relative to the owner doc, so that archaeology remains possible.
36. As a new contributor, I want examples of good vs bad token usage, so that code review is faster.
37. As a theme API user, I want the documented override surface to match what `render_deck(..., theme=)` actually applies, so that docs do not lie.
38. As a self-contained-mode user, I want token CSS still fully inlined with no CDN, so that P0 offline guarantees hold.
39. As a CDN-dev-mode user, I want the same token CSS inlined (fonts may differ), so that brand does not depend on delivery mode.
40. As an MVP1 acceptance owner, I want SC-VIS language testable enough to check off in the golden path later, so that P2 is not vibes-only.

## Implementation Decisions

1. **Owner document (normative):** Publish / maintain one wiki owner spec for renderer_v2 tokens (this PRD is the engineering PRD; the owner doc may be this file’s token appendix **or** a dedicated `wiki/SPEC_renderer_v2_tokens_owner.md` linked from README and CONTEXT if present). It **supersedes** any dual-track `renderer_v2_open_props_*` plans for implementation decisions. Research markdown remains historical.
2. **Implementation depth (user lock):** **Lighter path.** Do **not** vendor npm `open-props` or copy the full upstream prop set into `assets/`. Formalize the scales already in Boardroom CSS as the curated primitive layer (“Open Props–inspired,” Boardroom-owned).
3. **Layer model (normative):**  
   - **Primitives** — scales such as `--size-1…15`, `--radius-1…6`, `--radius-round`, `--shadow-1…6`, shadow strength/color knobs; optional curated additions only with owner-doc update.  
   - **Brand / Boardroom** — navy, blue, ink, fonts, stage, pads, type sizes tied to Boardroom Earnings.  
   - **Semantic** — `--color-*`, `--space-*`, `--radius-sm|md|lg`, `--shadow-sm|md|lg`, `--text-*`, etc., mapping brand+primitives for themeable consumption.  
   - **Components / gl-*** — consume semantic first, primitives second; avoid bare hex/px where a token exists.
4. **CSS concat order stays:** primitives/brand tokens → semantic-tokens → viewport → gridlines → components → chart CSS → optional theme override block. Font `@font-face` from P0 still prepends as today.
5. **Always-on:** token CSS is not a P1 feature id and must not appear in `features_enabled`.
6. **Theme injection contract:** existing `render_deck(..., theme={css_var: value})` remains the override API. Owner doc lists the **supported semantic override keys** (the public theme surface). Unknown keys may pass through as today or warn — pick one behavior and test it; recommendation: **pass through** custom properties to match current permissiveness, document that only semantic keys are supported.
7. **Curation rules:**  
   - No Open Props normalize/utility class frameworks.  
   - No second grid system.  
   - No easings/animation token packs beyond what calm UI already needs (D15).  
   - New primitives require a one-line rationale in the owner doc.
8. **Components pass (bounded):** identify high-frequency hard-coded spacing/radius/shadow in component CSS and replace with existing tokens where equality is exact or intentionally nearest-scale. Do **not** restyle layouts for aesthetics alone. Visual diffs should be negligible; if a value would change appearance, leave it or add a named token with the **current** value first.
9. **Chart CSS:** where chart styles hard-code Boardroom blues/navy, prefer semantic/brand variables when safe. No Chart.js work.
10. **No runtime JS token system.** Plain CSS custom properties only.
11. **THIRD_PARTY.md:** no new row for Open Props in P2 (nothing vendored). If comments reference “Open Props-style,” that is attribution of inspiration, not a packaged dependency.
12. **README:** Step 4 points to the token owner doc; notes always-on tokens and theme override surface.
13. **Parallel research:** do not delete research files in this theme unless the user asks; add “non-normative; see owner spec” pointers where those files claim authority.
14. **P1 interaction:** none required. If both land close together, avoid conflicting docs about `run_meta` fields.
15. **Ticket slicing suggestion:** (1) owner doc + layer map + supported theme keys; (2) tests for brand+primitive presence and non-presence of kitchen-sink; (3) bounded components token prefer pass; (4) README/research pointers.

## Testing Decisions

**What good tests look like**

- Assert on **emitted CSS/HTML** from `render_deck` (and theme tests), not on private file read order unless a dedicated pure helper is introduced (prefer not to).
- Check presence of representative primitive and semantic custom properties, Boardroom brand color markers, and theme override block behavior.
- Check absence of an obviously non-curated upstream dump (define a small denylist of props we deliberately do **not** ship, or assert total CSS size / prop count stays under a soft documented bound if useful — prefer denylist of known kitchen-sink names over fragile counts).
- Do not screenshot-diff the whole deck in P2 unless already practiced in repo; this theme is contract/CSS presence oriented.

**Modules / behaviors under test**

- Default render contains Boardroom brand tokens (e.g. navy/blue hex or var chain) and curated primitive scales.
- Default render contains semantic aliases used by theme docs.
- Theme override still adds a second `<style>` (or documented equivalent) and applies override values — compatible with existing `tests/test_renderer_v2_themes.py`.
- Self-contained mode still has no remote CSS for tokens.
- Optional: components reference `var(--space-*)` / `var(--radius-*)` in spots touched by the bounded pass (avoid asserting entire file).

**Prior art**

- `tests/test_renderer_v2_themes.py` — theme injection and `<style>` count.
- `tests/test_renderer_v2_self_contained.py` — offline / delivery contracts.
- `tests/test_renderer_v2_gates.py` — Boardroom token presence gates in HTML.

**Suggested home:** extend theme tests and/or add `tests/test_renderer_v2_tokens.py` focused on token contract.

## Out of Scope

- Vendoring upstream Open Props package or full prop copy (deferred; would be a new decision + THIRD_PARTY row).
- Feature gating tokens (contradicts D3).
- Chart.js / Mermaid / Alpine / Swiper / Lucide.
- P1 size matrix implementation (owned by P1) except not breaking always-on CSS size reporting.
- Native disclosure patterns (P5) beyond leaving tokens ready for them.
- Composition recipes (P7).
- PDF fidelity.
- Animation/easing systems (D15).
- Replacing `gl-*` or Boardroom brand identity.
- Dark-mode productization (unless already partially present — do not expand).
- Tailwind or utility-class adoption.
- Automated large-scale visual regression suite (unless already standard).

## Further Notes

### Current baseline (factual)

- `tokens.css` already defines Boardroom brand values **and** Open Props–style size/radius/shadow scales plus Boardroom-tinted gradients.
- `semantic-tokens.css` already maps semantic color/space/radius/shadow/text names onto brand/primitives.
- `components.css` already consumes many `var(--size-*)`, `var(--radius-*)`, `var(--shadow-*)` values.
- Theme injection via `render_deck(..., theme=)` already emits an override `<style>` block.

P2 is therefore **ownership, curation rules, documentation, tests, and a bounded prefer-tokens pass** — not a greenfield token architecture.

### Layer diagram (conceptual)

```
@font-face (P0 inliner)
→ primitives + Boardroom brand (tokens.css)
→ semantic map (semantic-tokens.css)
→ viewport / gridlines / components / chart_css
→ optional theme override (:root { ... })
```

### Acceptance checklist (engineering)

| ID | Criterion |
|----|-----------|
| P2-AC1 | Single owner doc published and linked from README Step 4 |
| P2-AC2 | Owner doc defines primitive / brand / semantic / component layers and curation rules (D4/D5) |
| P2-AC3 | No upstream Open Props package vendored; THIRD_PARTY.md gains no false Open Props row |
| P2-AC4 | Default `render_deck` CSS still includes Boardroom brand markers and curated primitive scales |
| P2-AC5 | Theme override contract tests remain green |
| P2-AC6 | Documented public theme keys match supported semantic surface |
| P2-AC7 | Bounded components pass lands without intentional visual redesign |
| P2-AC8 | Tokens remain always-on (not in feature gates) |
| P2-AC9 | Self-contained offline CSS contract preserved |
| P2-AC10 | Existing renderer_v2 suites green (SC-COMPAT-1) |

### Seams locked with user (2026-07-19)

1. Primary seam = CSS-in-output via `render_deck` / theme tests — **yes**  
2. Lighter path = document/formalize existing scales, no full upstream pin — **yes**  

### Suggested follow-on (not P2)

If later measurement shows primitive scales drifting from true Open Props names enough to hurt hiring/docs, reopen alignment for an optional **vendored subset pin** theme with license inventory — do not sneak it into P2.

*End of P2 spec.*
