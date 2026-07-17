# Spec: Renderer v2 Alignment Refactor

> Derived from the Gen Renderer v2 Layout Expansion Plan vs. the current `impact_slides/renderer_v2/` implementation. This spec tracks misalignments and defines the work required to bring the renderer into full compliance with the vNext vision.

---

## Problem Statement

The current `renderer_v2` is a mature, production-ready **Phase 6** engine (Boardroom theme, speaker notes, EID scrubbing, debug mode). However, it is structurally a **Phase 1–2** deliverable in terms of the Grid Design System and layout catalog defined in the original refactoring plan. The renderer:

- **Has** a working grid primitive system and existing layout refactorings.
- **Lacks** the comprehensive design-token system required for multi-brand and advanced theming.
- **Lacks** the Pydantic data-contract layer for builder handoffs (Manual Map is missing).
- **Lacks** 18 of the 28 proposed layouts, including all high-priority diagram and evidence layouts.
- **Lacks** the reusable SVG diagram primitive library required for `system_architecture`, `causal_loop`, and other diagram types.

The goal is to bridge the renderer from its current functional state to the full architectural specification while maintaining backward compatibility with the existing Boardroom Earnings pipeline.

---

## Solution

Implement a phased migration that introduces the missing architectural layers (Validation, Token System, Diagram Primitives, Layout Expansion) in backward-compatible increments.

The renderer should continue to produce valid Boardroom Earnings output today, while gaining the structural capacity to handle the full vNext layout catalog and theme targets tomorrow.

---

## User Stories

1. **As a developer**, I want a Pydantic-validated slide contract so that errors in builder handoffs are caught before rendering, not during SVG paint.
2. **As a designer**, I want a comprehensive design-token system (matching the frontend-slides specification) so that I can inject a new brand theme without touching layout CSS.
3. **As a builder user**, I want to use `evidence_cards`, `system_architecture`, and `causal_loop` layouts in my handoff so that I can produce dense, diagram-rich slides.
4. **As a maintainer**, I want SVG diagram primitives (Node, Arrow, Connector) as reusable macros so that new diagram layouts are data-driven and consistent.
5. **As a QA engineer**, I want visual regression tests for layout density (low vs. high) and fixed-stage snapping so that 1920×1080 integrity is never regressed.
6. **As a product owner**, I want the existing 10 layouts to remain untouched in output until their refactor ticket is explicitly picked up, so there is no risk of breaking the current pipeline.

---

## Implementation Decisions

### 1. Design Token System (Phase 1 Retrofit)
**Decision:** Introduce a **mapping shim** rather than a full token rename. The original plan enforces strict token names (`--color-primary`, `--color-accent`) for multi-brand swaps. The current renderer uses boardroom-specific names (`--navy`, `--blue`) for specificity.

- **Approach:** Add a new `css/semantic-tokens.css` layer that maps semantic names to the existing boardroom tokens.
  ```css
  :root {
    --color-primary: var(--navy, #00175a);
    --color-accent:  var(--blue, #006fcf);
    --font-display:  var(--font-body, "Source Sans 3", sans-serif);
    /* ... etc */
  }
  ```
- **Rationale:** This satisfies the plan's requirement for "theme switching without rewriting layout CSS" while immediately inheriting the existing, polished Boardroom values. Future brands override the semantic tokens at the `:root` level; legacy layouts continue to work.
- **Impact:** Low risk. Purely additive CSS file.

### 2. Pydantic Validation Layer (Phase 0)
**Decision:** Implement a **Discriminated Union** for the builder handoff contract, per the plan's Section 9 recommendation.

- **Approach:** Create `impact_slides/renderer_v2/schemas.py`.
- Define a `ValidatedSlide` model using `Tag[...]` for each layout type.
- The `render_deck` entry point in `cli.py` will attempt to validate the handoff JSON. If validation fails, it logs a detailed error and falls back to the current "soft-reject" behavior (rendering as default `split_text_visual`).
- **Rationale:** This fulfills the plan's requirement for strong data contracts without breaking malformed handoffs that the old renderer handled gracefully. It catches real bugs early (e.g., a `system_architecture` slide missing its `components` array).
- **Priority:** High. Foundation for all new layouts.

### 3. Diagram SVG Primitives (Phase 4 Foundation)
**Decision:** Build a zero-dependency, macro-based SVG library.

- **Approach:** Create a new `impact_slides/renderer_v2/diagram/` package.
- Core primitives:
  - `node_box(...)`: Generates a rounded-rect HTML/SVG group with optional icon.
  - `arrow_connector(...)`: Generates a `<path>` or `<line>` with arrowheads.
  - `group_boundary(...)`: Generates a dashed SVG `<rect>` background.
  - `annotation_callout(...)`: A positioned HTML div with a connector line.
- These primitives will heavily consume the new semantic tokens for colors and spacing.
- **Rationale:** The plan explicitly rejects external libraries (like Mermaid.js) to maintain the zero-dependency constraint. Macros allow data-driven rendering.
- **Priority:** High. Required for `system_architecture`, `causal_loop`, etc.

### 4. Missing Layout Catalog (Phases 3 & 4)
**Decision:** Implement layouts in two waves, strictly gated by the availability of the Diagram Primitives and Validation Layer.

- **Wave 1 (Evidence & Data Heavy):**
  - `evidence_cards`
  - `data_table_with_insight`
  - `comparison_with_metrics`
  - `metric_row_with_breakdown`
  - `insight_with_evidence`
  - `priority_matrix`
- **Wave 2 (Strategic & Diagram):**
  - `system_architecture` (uses diagram primitives)
  - `data_flow_diagram` (uses diagram primitives)
  - `causal_loop` (uses diagram primitives)
  - `before_after`

- **Layout Consolidation:** `split_text_visual` is the canonical implementation of the `two_column_with_lead` pattern. The existing recipe already provides a lead insight band + arg/proof dual-rail. No separate `two_column_with_lead` layout will be created; builder handoffs should continue to use `split_text_visual` for this pattern.

### 5. Refactoring Existing Layouts
**Decision:** Defer hard refactoring of existing layouts until Wave 1 is complete.

- The plan’s Section 8 calls for replacing custom grids in `split_text_visual` and `comparison_grid` with strict `.grid-2` / `.grid-auto`.
- **Current State:** The existing layouts (`split_text_visual`, `title_or_opening`, etc.) already produce correct Boardroom output. Forcing a CSS refactor now risks regressions.
- **New Approach:** New layouts (Wave 1 & 2) **must** be built using strict primitives. Existing layouts will be refactored only when a specific bug or enhancement requires touching that file.
- **Exception:** The `metric_dashboard` adaptation to use `.card` for KPIs is trivial and can be done inline during Wave 1.

---

## Testing Decisions

1. **Pydantic Contract Tests:** Create `tests/test_renderer_v2_validation.py`.
   - Feed the renderer intentionally malformed handoffs (missing required fields for `system_architecture`) and assert it produces clear error logs without crashing.
   - Feed valid handoffs and assert the `ValidatedSlide` structure matches.

2. **Diagram Primitive Tests:**
   - Create a standalone HTML fixture (`tests/fixtures/diagram_test_deck.html`) that renders one of each primitive (Node, Arrow, Group) to confirm SVG validity.

3. **Layout Density Tests:**
   - For `evidence_cards`, assert that the number of CSS grid columns adapts correctly based on item count (2 vs 3 vs 4 columns).
   - Use the existing `tests/test_renderer_v2_gridlines.py` patterns to check stage snapping.

4. **Visual Regression / Gut Check:**
   - Generate a `test_deck_vnext.html` containing all Wave 1 and Wave 2 layouts.
   - Visually inspect that high-density slides do not overflow the 1920×1080 fixed stage and that low-density slides maintain proper whitespace.

---

## Out of Scope

- **Dark/Light Theme Toggle:** The token system is structured to support it (`--slide-bg`, `--ink`), but specific dark-theme color values and UI toggles are deferred to a future milestone.
- **Mermaid.js Integration:** Explicitly excluded per the plan's zero-dependency mandate.
- **`step4_builder_validator.py` Merge:** The plan mentions potential merging in Phase 6. This is a broader architectural decision and is kept out of this renderer-specific spec.
- **`ecosystem_map`, `hierarchy_tree`, `decision_tree`:** These are medium-priority diagram layouts. While they require the same primitives as Wave 2, they are not part of the initial Wave 2 implementation to save time.
- **`horizontal_process`, `circular_process`:** Process enhancements are low priority in the plan and are out of scope for this spec.

---

## Further Notes

- **Layout Usage Guide:** The GPT Renderer Prompt guide (Phase 5) will be maintained as a **Wiki artifact** in the `wiki/` folder, not committed to the main codebase under `docs/`. This keeps renderer documentation close to the plan docs without cluttering the product surface.
- **Font Loading:** The current `shell.py` uses Google Fonts (`Source Sans 3`, `IBM Plex Sans`). The plan does not mention font loading strategy. Ensure the new `semantic-tokens.css` does not introduce new font dependencies that break offline rendering if the renderer is used in an air-gapped environment.
- **Title Slide Coverage:** The existing `normalize_handoff` logic forces slide 1 to `title_or_opening`. This must remain untouched as it ensures the builder handoff always starts with a valid title slide, regardless of what the builder sends.