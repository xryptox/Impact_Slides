# Gen Renderer v2 — Complete Layout Expansion + Grid Design System Refactoring Plan

**Version:** 1.1 (Updated with Diagram Capabilities)  
**Date:** July 17, 2026  
**Document Type:** Exhaustive Implementation Plan  
**Goal:** Transform `_gen_renderer_v2.py` into a powerful renderer capable of producing **varied, professional, and high-density evidence-rich slides** using a unified Grid Design System.

---

## 1. Executive Summary

This plan provides a complete roadmap to evolve `_gen_renderer_v2.py` by:

1. Implementing a **unified Grid Design System** (design tokens + reusable primitives).
2. Building a **comprehensive Theming & Design Token System** that matches or exceeds `frontend-slides` in design token quality, brand consistency, and theming flexibility.
3. Significantly expanding the supported **layout catalog** (from ~10 to ~28+ layouts), including strong diagram support.
4. Adding **diagram capabilities** using inline SVG to explain complex topics clearly.
5. Ensuring strong support for **dense, evidence-heavy, and varied slide types** required for Impact Slides.
6. Maintaining zero-dependency, standalone HTML output with a fixed 1920×1080 stage.

**Target Outcome:**  
By the end of this plan, `_gen_renderer_v2.py` (vNext) will be able to generate a wide range of high-quality slides — from clean narrative slides to complex, data-dense evidence decks **and visually clear diagrams** — while keeping the codebase maintainable through a strong Grid Design System and reusable diagram components.

---

## 2. Current State

### 2.1 Existing Layouts in `_gen_renderer_v2.py`

| Layout                    | Type          | Density | Grid Maturity | Notes |
|---------------------------|---------------|---------|---------------|-------|
| `title_or_opening`        | Title         | Low     | Low           | Basic |
| `split_text_visual`       | Split         | Medium  | Medium        | Uses custom Grid |
| `metric_dashboard`        | Dashboard     | Medium-High | Good     | Uses dynamic `--col-count` |
| `data_table`              | Data          | Medium  | Low           | Table-focused |
| `full_process_flow`       | Process       | Medium  | Medium        | Grid-based |
| `timeline`                | Timeline      | Medium  | Medium        | Grid-based |
| `roadmap`                 | Roadmap       | Medium  | Medium        | Grid-based |
| `comparison_grid`         | Comparison    | Medium-High | Medium    | Card grid |
| `quote_card`              | Quote         | Low     | Low           | Basic |
| `icon_grid`               | Icon          | Medium  | Medium        | Grid-based |
| `other` (fallback)        | -             | -       | -             | Falls back to split |

**Gap:** The current set is insufficient for **high-density evidence slides**, complex comparisons, and varied analytical content.

---

## 3. Target Vision

### 3.1 Grid Design System (Foundation)

All new and existing layouts must be built on top of a **centralized Grid Design System**:

- **Design Tokens** (CSS Custom Properties)
- **Core Primitives**: `.grid`, `.grid-2`, `.grid-3`, `.grid-auto`, `.card`, gap modifiers, `.slide-grid`
- **Dynamic Control** via CSS variables (`--col-count`, `--step-count`)
- **Named Areas** support via `.slide-grid`
- **Component Layer** built on primitives (cards, panels, KPI grids, etc.)

### 3.2 Expanded Layout Philosophy

- Move from "few general layouts" → **"composable, purpose-built layouts"**
- Support both **low-density speaker slides** and **high-density reading-first slides**
- Add strong support for **visual diagrams** to explain complex topics clearly
- Every layout should leverage the Grid Design System + reusable diagram primitives (where applicable)

### 3.3 Theming & Design Tokens (Must Match or Exceed frontend-slides)

Theming and design tokens are currently one of the weakest areas in `_gen_renderer_v2.py`. This section defines the requirements to bring theming **to parity or beyond** the `frontend-slides` skill.

#### Goals

| Area                        | Target State                                      | Comparison to frontend-slides |
|-----------------------------|---------------------------------------------------|-------------------------------|
| **Design Token System**     | Comprehensive CSS Custom Properties               | At parity or better           |
| **Brand Consistency**       | Strict enforcement of brand rules                 | At parity or better           |
| **Theming Flexibility**     | Easy theme switching / multi-brand support        | Better than current frontend-slides |
| **Alignment with Grid**     | Tokens drive Grid spacing, cards, diagrams        | Fully integrated              |

#### 3.3.1 Design Token System Requirements

Implement a full set of CSS Custom Properties in `:root` (or a dedicated theme layer). The system must include:

```css
:root {
  /* === Typography === */
  --font-display: 'Sora', system-ui, sans-serif;
  --font-body: 'DM Sans', system-ui, sans-serif;
  --font-mono: 'IBM Plex Mono', monospace;
  --font-num: 'IBM Plex Sans', var(--font-body);

  /* === Color Palette (Brand) === */
  --color-primary: #00175a;          /* Navy */
  --color-accent: #006fcf;           /* Signal Blue */
  --color-accent-2: #0a7d55;         /* Success / Positive */
  --color-warn: #b35900;             /* Warning */
  --color-ink: #0b0f1a;
  --color-ink-soft: #5b6478;
  --color-surface: #ffffff;
  --color-surface-alt: #f8fafc;
  --color-border: #e5e7eb;
  --color-rule: #e6e9f0;

  /* === Spacing Scale === */
  --space-xs: 12px;
  --space-sm: 20px;
  --space-md: 32px;
  --space-lg: 48px;
  --space-xl: 64px;
  --space-2xl: 96px;

  /* === Grid Tokens === */
  --grid-gap-sm: var(--space-sm);
  --grid-gap-md: var(--space-md);
  --grid-gap-lg: var(--space-lg);

  /* === Radius & Shadow === */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --shadow-sm: 0 2px 8px rgba(11, 15, 26, 0.06);
  --shadow-md: 0 4px 12px rgba(11, 15, 26, 0.08);
  --shadow-lg: 0 8px 24px rgba(11, 15, 26, 0.12);

  /* === Stage === */
  --stage-bg: #0b0f1a;
  --slide-bg: #ffffff;
  --slide-padding: 96px;
}
```

All layout, card, diagram, and typography styles **must** consume these tokens. No hardcoded colors, gaps, or radii in layout CSS.

#### 3.3.2 Brand Consistency Requirements

- Every generated deck must enforce the brand style guide (colors, typography, spacing).
- Cards, panels, KPI tiles, and diagram nodes must share the same visual language.
- Source of truth for brand values should live in the design token layer (not scattered across layout functions).
- Support for brand overrides via a simple theme configuration object that maps into CSS variables at render time.

#### 3.3.3 Theming Flexibility Requirements

The system must support:

1. **Easy theme swapping** — Change a small set of CSS variables (or a theme JSON) to produce different brand looks without rewriting layout CSS.
2. **Multi-brand support** — Ability to inject different token sets for different clients or internal brands.
3. **Runtime theme injection** — The renderer should accept an optional `theme` or `brand_style` object and map it into the `:root` variables.
4. **Dark / Light variants** (optional future) — Tokens should be structured so that a dark theme can be added later with minimal changes.

This goes **beyond** current `frontend-slides` by making theming first-class and data-driven rather than hard-coded per presentation.

#### 3.3.4 Integration with Grid Design System & Diagrams

- Grid gaps, card padding, and diagram spacing must use the spacing tokens.
- Diagram node colors, connection colors, and annotation styles must use brand color tokens.
- All new layouts and diagram components must be built exclusively on top of the token system.
- The same token set must be used by both the Grid primitives and the SVG diagram components so visual consistency is automatic.

#### 3.3.5 Implementation Requirements in `_gen_renderer_v2.py`

1. Extract all visual values into the design token block at the top of the CSS.
2. Create a small helper that can inject or override tokens from a brand style configuration.
3. Refactor every layout and diagram component to use tokens only.
4. Document the token system clearly in comments so future layout authors follow it.
5. Align token naming and values as closely as possible with the `frontend-slides` approach while improving flexibility.

#### Success Criteria for Theming

- Changing brand colors or spacing requires editing only the token layer (or a theme config).
- Generated decks look at least as polished and consistent as high-quality `frontend-slides` output.
- New layouts automatically inherit brand consistency.
- Theme switching can be demonstrated with at least two different brand configurations.

---

## 4. Complete Layout Catalog (Current + Proposed)

### 4.1 Existing Layouts (Keep & Improve)

| Layout                    | Status     | Action |
|---------------------------|------------|--------|
| `title_or_opening`        | Keep       | Minor polish |
| `split_text_visual`       | Keep       | Refactor to use new primitives |
| `metric_dashboard`        | Keep       | Enhance with new tokens |
| `data_table`              | Keep       | Improve wrapping |
| `full_process_flow`       | Keep       | Refactor |
| `timeline`                | Keep       | Refactor |
| `roadmap`                 | Keep       | Refactor |
| `comparison_grid`         | Keep       | Refactor to `.grid-auto` + `.card` |
| `quote_card`              | Keep       | Improve with `.card` |
| `icon_grid`               | Keep       | Enhance |

### 4.2 New High-Priority Layouts (Add in vNext)

#### Evidence & Data Heavy (Core for Dense Slides)

| New Layout                        | Category          | Density | Description | Grid Pattern | Priority |
|-----------------------------------|-------------------|---------|-------------|--------------|----------|
| `evidence_cards`                  | Evidence          | High    | 3–6 evidence cards in responsive grid | `.grid-auto` + `.card` | High |
| `two_column_with_lead`            | Analytical        | High    | Lead insight + two content columns | `.grid` + lead section | High |
| `data_table_with_insight`         | Data              | High    | Table + key insight/callout | Grid (table + card) | High |
| `comparison_with_metrics`         | Comparison        | High    | Side-by-side options with metrics | `.grid-2` + inner grids | High |
| `metric_row_with_breakdown`       | Dashboard         | High    | Top KPIs + detailed breakdown grid | Combined grids | High |
| `insight_with_evidence`           | Narrative         | High    | Strong insight + supporting evidence cards | Lead + `.grid-auto` | High |

#### Strategic & Decision Support

| New Layout                    | Category       | Density | Description | Grid Pattern | Priority |
|-------------------------------|----------------|---------|-------------|--------------|----------|
| `priority_matrix`             | Strategic      | High    | 2x2 or 3x3 impact/effort matrix | Named areas or Grid | High |
| `before_after`                | Transformation | Medium  | Before vs After or Current vs Future | `.grid-2` | Medium |
| `risk_opportunity`            | Strategic      | Medium  | Risks on one side, Opportunities on other | `.grid-2` with variants | Medium |
| `recommendation_with_rationale` | Action       | Medium  | Strong recommendation + evidence | Quote-style + cards | Medium |

#### Diagram & Visual Explanation Layouts (New in vNext)

These layouts focus on explaining complex topics through clear visual diagrams.

| New Layout                    | Category              | Density | Description                                      | Technology          | Priority |
|-------------------------------|-----------------------|---------|--------------------------------------------------|---------------------|----------|
| `system_architecture`         | Diagram               | High    | System components with connections & relationships | Inline SVG + Grid   | High |
| `data_flow_diagram`           | Diagram               | High    | Data/process flow between entities               | Inline SVG + Grid   | High |
| `causal_loop`                 | Diagram               | High    | Cause-effect and feedback loops                  | Inline SVG          | High |
| `decision_tree`               | Diagram               | Medium  | Decision logic with branches                     | SVG + Grid          | Medium |
| `hierarchy_tree`              | Diagram               | Medium  | Hierarchical structures (org, concepts)          | SVG + Grid          | Medium |
| `before_after_detailed`       | Transformation        | Medium  | Detailed transformation journey with visuals     | Grid + SVG          | High |
| `ecosystem_map`               | Diagram               | Medium  | Stakeholders/entities and their connections      | Inline SVG          | Medium |
| `process_with_decisions`      | Process               | Medium  | Linear process combined with decision points     | Grid + SVG          | Medium |

#### Process & Flow Enhancements

| New Layout                | Category   | Density | Description | Grid Pattern | Priority |
|---------------------------|------------|---------|-------------|--------------|----------|
| `horizontal_process`      | Process    | Medium  | Clean horizontal process flow | Grid columns | Medium |
| `circular_process`        | Process    | Low     | Circular/continuous improvement loop | Creative Grid | Low |
| `decision_flow`           | Process    | Medium  | Simple decision tree | Grid + branches | Low |

#### Supporting Layouts

| New Layout               | Category     | Density | Description | Priority |
|--------------------------|--------------|---------|-------------|----------|
| `section_divider`        | Structure    | Low     | Clean section break with message | Medium |
| `kpi_trend_cards`        | Dashboard    | Medium  | Metrics with trend indicators | Medium |
| `three_column_comparison`| Comparison   | Medium  | Three-way comparison | Medium |
| `source_deep_dive`       | Appendix     | High    | Dense source/evidence summary | Low |

---

## 5. Diagram Capabilities & Visual Explanation Support

To effectively explain complex topics, the renderer needs strong diagram capabilities beyond basic grids and cards.

### 5.1 Recommended Technical Approach

Since the renderer must remain **zero-dependency**, we will use:

- **Inline SVG** as the primary technology for diagrams (nodes, arrows, connectors, shapes).
- **CSS Grid + positioned elements** for structured diagram layouts.
- **Reusable diagram primitives** (Node, Arrow, Connector, Group, Annotation).
- **Data-driven rendering** where possible (define nodes/edges in JSON → render SVG).

**Avoid:** External libraries like Mermaid.js (breaks zero-dependency requirement).

### 5.2 Diagram Building Blocks to Implement

| Component              | Purpose                                   | Technology     | Priority |
|------------------------|-------------------------------------------|----------------|----------|
| `Node / Box`           | Basic element with title + body           | HTML + CSS     | High |
| `Arrow / Connector`    | Directed lines between elements           | Inline SVG     | High |
| `Labeled Connection`   | Arrow with text label                     | Inline SVG     | High |
| `Group Container`      | Visual grouping of related elements       | CSS + SVG      | High |
| `Annotation / Callout` | Explanatory notes on diagrams             | Positioned HTML| High |
| `Layered Background`   | Background layers for context             | CSS Grid       | Medium |
| `Icon Node`            | Node containing an icon                   | SVG symbols    | High |

### 5.3 Integration with Grid Design System

Diagram layouts should combine:
- Grid primitives for overall structure (`.grid`, `.grid-2`, `.slide-grid`)
- SVG components for visual connections and shapes
- Design tokens for consistent spacing, colors, and sizing

---

## 6. Detailed Layout Specifications – Top Diagram Layouts

This section provides detailed specifications for the highest-priority diagram layouts. These should serve as the implementation guide when building support in `_gen_renderer_v2.py`.

### 6.1 `system_architecture`

**Purpose**  
Visually represent the components of a system and how they relate to each other. Ideal for explaining complex systems, platforms, or technical architectures in a clear, digestible way.

**When to Use**
- Explaining system design or platform architecture
- Showing how different parts of a business or technical system connect
- High-level overviews of multi-component solutions

**Expected Input Fields (from Builder)**
- `title`
- `components[]`: List of system components (name, description, type)
- `connections[]`: Relationships between components (from, to, label, type)
- `groups[]` (optional): Logical grouping of components
- `annotations[]` (optional): Key insights or notes

**Recommended Structure**
```html
<div class="slide-grid diagram system-architecture">
  <!-- Optional header / lead text -->
  <div class="lead">...</div>

  <!-- Main diagram area -->
  <div class="diagram-container">
    <!-- SVG for nodes + connections -->
    <svg class="architecture-svg">...</svg>
    
    <!-- Optional legend -->
    <div class="diagram-legend">...</div>
  </div>
</div>
```

**Technical Approach**
- Use **CSS Grid** for overall layout and positioning of major sections.
- Use **Inline SVG** for:
  - Nodes (rounded rectangles with title + short description)
  - Connection lines with optional arrows
  - Grouping boundaries (dashed or colored backgrounds)
- Support **data-driven rendering** (Python generates SVG based on components + connections JSON).

**Visual Characteristics**
- Clean, professional boxes with subtle shadows
- Color-coded by component type (e.g., Frontend, Backend, Data, External)
- Clear directional arrows
- Good use of whitespace and alignment
- Optional annotations/callouts

**Example Use Case**
"Payment Platform Architecture" showing Frontend Apps → API Gateway → Services → Databases with external payment providers.

---

### 6.2 `causal_loop`

**Purpose**  
Visualize cause-and-effect relationships and feedback loops. Excellent for explaining complex dynamics, system behavior, or strategic cause-effect chains.

**When to Use**
- Explaining reinforcing or balancing loops
- Strategy or systems thinking slides
- Root cause analysis with feedback effects
- Policy or business model dynamics

**Expected Input Fields**
- `title`
- `variables[]`: Key variables/nodes in the system
- `relationships[]`: Causal links (from → to, polarity: + or -, delay?)
- `loops[]`: Identified feedback loops (name, type: reinforcing/balancing, description)
- `key_insight` (optional)

**Recommended Structure**
```html
<div class="slide-grid diagram causal-loop">
  <div class="lead">...</div>
  
  <div class="diagram-container">
    <svg class="causal-loop-svg">...</svg>
  </div>
  
  <div class="loop-legend">
    <!-- Reinforcing vs Balancing loop explanations -->
  </div>
</div>
```

**Technical Approach**
- **Inline SVG** is strongly preferred.
- Nodes as circles or rounded boxes.
- Curved arrows with polarity labels (+ / −).
- Visual distinction between reinforcing (R) and balancing (B) loops.
- Optional delay markers on arrows.

**Visual Characteristics**
- Clean node styling with consistent sizing
- Clear polarity indicators on arrows
- Color coding for loop types
- Good spacing to avoid visual clutter
- Legend explaining symbols

**Example Use Case**
"Growth Flywheel in a Marketplace Business" showing how more sellers → more buyers → more sellers (reinforcing loop) with a balancing loop on pricing pressure.

---

### 6.3 `data_flow_diagram`

**Purpose**  
Show how data moves between systems, processes, or entities. Useful for explaining data pipelines, integration flows, or information movement.

**When to Use**
- Data architecture and integration slides
- ETL / data pipeline explanations
- System integration overviews
- Privacy or compliance data flow discussions

**Expected Input Fields**
- `title`
- `entities[]`: Systems, processes, or actors
- `data_flows[]`: Flow of data (from, to, data_type, description)
- `stores[]` (optional): Data stores
- `processes[]` (optional): Transformation steps

**Recommended Structure**
Similar to `system_architecture`, but optimized for flow direction (often left-to-right or top-to-bottom).

**Technical Approach**
- Combination of **CSS Grid** (for layout) and **Inline SVG** (for arrows and flow lines).
- Support for different arrow styles (solid, dashed for optional flows).
- Labels on flows showing what data is moving.

**Visual Characteristics**
- Clear start and end points
- Consistent flow direction
- Good visual hierarchy between entities and flows
- Use of color to differentiate data types or sensitivity levels

---

These three layouts (`system_architecture`, `causal_loop`, and `data_flow_diagram`) should be prioritized in **Phase 3 Wave 2**.

---

## 8. Refactoring Guidance for Existing Layouts

This section provides practical guidance on migrating the current layouts in `_gen_renderer_v2.py` to the new Grid Design System.

### General Refactoring Principles

- Replace custom/hardcoded Grid CSS with shared primitives (`.grid`, `.grid-2`, `.grid-auto`, `.card`).
- Use design tokens (`--grid-gap-md`, `--space-lg`, etc.) instead of hardcoded values.
- Extract repeated patterns (cards, panels, KPI items) into reusable classes.
- Maintain backward compatibility during transition where possible.
- Leverage dynamic column control (`--col-count`) more consistently.

### Layout-by-Layout Refactoring Guidance

| Existing Layout          | Current Issues                              | Refactoring Steps                                                                 | Target Primitives                  | Effort | Priority |
|--------------------------|---------------------------------------------|-----------------------------------------------------------------------------------|------------------------------------|--------|----------|
| `title_or_opening`       | Very basic                                  | Improve visual hierarchy using tokens.                                            | Design tokens                      | Low    | Low      |
| `split_text_visual`      | Custom `.split-layout` Grid                 | Replace with `.grid-2`. Wrap panels in `.card`. Use tokens for gaps.              | `.grid-2`, `.card`                 | Medium | High     |
| `metric_dashboard`       | Already uses dynamic columns                | Enhance with `.card` for KPIs. Standardize spacing with tokens.                   | `.grid`, `.card`, dynamic columns  | Low    | High     |
| `data_table`             | Limited visual treatment                    | Wrap table in `.card`. Add optional insight area.                                 | Grid + `.card`                     | Low    | Medium   |
| `full_process_flow`      | Custom Grid                                 | Standardize using `.grid` + dynamic columns. Improve connections.                 | `.grid`, dynamic columns           | Medium | High     |
| `timeline`               | Custom implementation                       | Refactor to `.grid`. Add variants if needed.                                      | `.grid`                            | Medium | Medium   |
| `roadmap`                | Similar to timeline                         | Align with `timeline`. Use consistent card treatment.                             | `.grid`, `.card`                   | Low    | Medium   |
| `comparison_grid`        | Custom Grid for cards                       | Replace with `.grid-auto` + `.card`.                                              | `.grid-auto`, `.card`              | Medium | High     |
| `quote_card`             | Basic                                       | Wrap in `.card`. Improve typography with tokens.                                  | `.card`                            | Low    | Low      |
| `icon_grid`              | Custom Grid                                 | Standardize with `.grid-2` / `.grid-3` + cards.                                   | `.grid-2` / `.grid-3`, `.card`     | Low    | Medium   |

### Recommended Migration Order

1. **Quick Wins (High Impact, Lower Effort)**
   - `metric_dashboard`
   - `comparison_grid`
   - `split_text_visual`

2. **High Value Process Layouts**
   - `full_process_flow`
   - `timeline`
   - `roadmap`

3. **Lower Priority**
   - `data_table`, `icon_grid`, `quote_card`, `title_or_opening`

### Migration Tips

- Keep old class names working during transition (compatibility layer).
- Use new design tokens everywhere, even in legacy layouts.
- Remove deprecated custom CSS after successful refactoring.
- Add comments linking each layout back to the Grid Design System.

---

---

## 7. Detailed Layout Specifications for All New Layouts

This section provides implementation-ready specifications for the new layouts proposed in this plan.

### 7.1 Evidence & Data Heavy Layouts

#### `evidence_cards`

**Purpose**: Display multiple pieces of evidence or findings in a clean, scannable card-based grid.

**When to Use**: High-density evidence slides with 3–8 distinct items.

**Key Fields**: `title`, `cards[]` (headline, body, metric, source), optional `insight`.

**Grid Pattern**: `.grid-auto` + `.card` elements (2–4 columns recommended).

**Visual Style**: Consistent cards with strong internal hierarchy using design tokens.

---

#### `two_column_with_lead`

**Purpose**: Lead with a strong insight, followed by two supporting columns.

**When to Use**: Analytical/persuasive slides.

**Grid Pattern**: Vertical lead section + `.grid-2` below.

---

#### `data_table_with_insight`

**Purpose**: Table + prominent key insight.

**Grid Pattern**: Grid layout with table area + insight callout (use `.card`).

---

#### `comparison_with_metrics`

**Purpose**: Side-by-side comparison with metrics and qualitative points.

**Grid Pattern**: `.grid-2` with inner structured content.

---

#### `metric_row_with_breakdown`

**Purpose**: Headline KPIs on top + detailed breakdown below.

**Grid Pattern**: Dynamic KPI row + `.grid` / `.grid-auto` below.

---

#### `insight_with_evidence`

**Purpose**: Strong insight supported by evidence cards.

**Grid Pattern**: Prominent insight area + `.grid-auto` or `.grid-2` for evidence.

---

### 7.2 Strategic & Decision Support Layouts

#### `priority_matrix`

**Purpose**: 2x2 or 3x3 matrix for prioritization (Impact vs Effort, etc.).

**Technical Approach**: CSS Grid + positioned or data-driven items. Consider lightweight SVG for axes.

**Visual Style**: Clean quadrants with well-placed items.

---

#### `before_after`

**Purpose**: Show transformation from current to future state.

**Grid Pattern**: `.grid-2` with directional visual treatment.

---

#### `risk_opportunity`

**Purpose**: Balanced view of risks vs opportunities.

**Grid Pattern**: `.grid-2` with differentiated styling (color coding recommended).

---

#### `recommendation_with_rationale`

**Purpose**: Clear recommendation backed by rationale and evidence.

**Grid Pattern**: Strong headline + supporting grid/cards.

---

### 7.3 Diagram Layouts

Detailed specifications for `system_architecture`, `causal_loop`, and `data_flow_diagram` are provided in **Section 6**.

The remaining diagram layouts (`decision_tree`, `hierarchy_tree`, `ecosystem_map`, `process_with_decisions`) should follow the same technical approach:
- **Inline SVG** for visual elements
- Reuse diagram primitives (Node, Arrow, Connector, Annotation)
- Combine with Grid primitives for overall structure

---

### 7.4 Process & Supporting Layouts (Lightweight)

These can be implemented with moderate effort once the core system is in place:

| Layout                    | Recommended Approach                     | Effort |
|---------------------------|------------------------------------------|--------|
| `horizontal_process`      | Grid columns + SVG arrows                | Medium |
| `process_with_decisions`  | Grid + SVG decision nodes                | Medium |
| `section_divider`         | Centered content + visual accent         | Low    |
| `kpi_trend_cards`         | `.grid-auto` + simple trend viz          | Medium |
| `three_column_comparison` | `.grid-3` with cards                     | Low    |

---

## 7. Grid Design System Requirements for Layouts

All layouts (old and new) must follow these rules:

1. Use **design tokens** for all spacing and gaps.
2. Prefer **shared primitives** (`.grid*`, `.card`) over custom Grid CSS.
3. Use **dynamic columns** (`--col-count`) where column count varies.
4. Use **named grid areas** (`.slide-grid`) for complex structured slides.
5. Extract repeated patterns into reusable components (e.g., `.evidence-card`, `.kpi-card`).
6. Maintain **fixed 1920×1080** stage integrity.

---

## 6. Phased Implementation Plan

### Phase 0: Preparation (1 day)
- Finalize Grid Design System tokens and primitives.
- Create internal documentation for the new system.
- Set up a visual regression test deck.

### Phase 1: Grid Design System Foundation (2–3 days)
- Add all design tokens to centralized CSS.
- Implement core primitives: `.grid`, `.grid-2`, `.grid-3`, `.grid-auto`, `.card`, gap modifiers.
- Add `.slide-grid` with named area support.
- Update existing global styles.

### Phase 2: Refactor Existing Layouts (4–6 days)
Refactor all current layouts to use the new system:

| Layout                    | Effort | Key Changes |
|---------------------------|--------|-------------|
| `split_text_visual`       | Medium | Replace custom Grid with `.grid-2` + cards |
| `metric_dashboard`        | Low    | Enhance with tokens + `.card` |
| `comparison_grid`         | Medium | Use `.grid-auto` + `.card` |
| `process_flow` / `timeline` / `roadmap` | Medium | Standardize with primitives |
| `icon_grid` / `quote_card` | Low   | Wrap with `.card` |
| `data_table`              | Low    | Improve container |

### Phase 3: Implement High-Priority New Layouts (7–9 days)

**Wave 1 – Evidence & Analytical (Most Critical):**
- `evidence_cards`
- `two_column_with_lead`
- `data_table_with_insight`
- `comparison_with_metrics`
- `metric_row_with_breakdown`
- `insight_with_evidence`

**Wave 2 – Strategic & Diagram (High Value):**
- `priority_matrix`
- `before_after`
- `system_architecture`
- `data_flow_diagram`
- `causal_loop`

### Phase 4: Diagram Primitives + Medium-Priority Layouts (5–6 days)

**Diagram Foundation:**
- Build reusable SVG diagram components (Node, Arrow, Connector, Annotation, Group)
- Create data-driven diagram rendering helpers

**Medium-Priority Layouts:**
- Process enhancements (`horizontal_process`, `process_with_decisions`)
- Supporting layouts (`section_divider`, `kpi_trend_cards`, `hierarchy_tree`)

### Phase 5: Validation, Polish & Documentation (3–4 days)
- Generate comprehensive test decks (low + high density).
- Visual QA and iteration.
- Update inline documentation and comments.
- Create a **Layout Usage Guide** for the GPT Renderer Prompt.

### Phase 6: Alignment with Broader System (Ongoing)
- Update GPT Renderer Prompt to support new layouts.
- Align with `step4_builder_validator.py` if merging is desired.
- Create shared Grid Design System CSS snippet for reuse.

**Estimated Total Effort:** 20–25 working days (depending on team size and testing rigor).

---

## 7. Layout Specification Template (Example)

For every new layout, define:

- **Name**
- **Purpose**
- **When to Use**
- **Content Fields Expected**
- **Grid Structure**
- **Visual Example** (text description)
- **Edge Cases**

Example for `evidence_cards`:

- **Purpose**: Display multiple pieces of evidence in a clean, scannable card grid.
- **Density**: High
- **Grid**: `.grid-auto` + multiple `.card` elements
- **Recommended Columns**: 2–4 depending on content volume
- **Key Tokens**: `--grid-gap-md`, card tokens

---

## 8. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|----------|
| Scope creep from too many layouts | High | Prioritize strictly by business value (start with Wave 1) |
| GPT Renderer Prompt falls behind | High | Update prompt in parallel during Phase 5 |
| Visual inconsistency during transition | Medium | Maintain backward compatibility for old class names initially |
| Over-engineering the design system | Medium | Keep primitives simple and practical |

---

## 9. Pydantic Validation & Data Contract Layer

As the number of layouts grows (especially complex diagram layouts), having a strong **validation layer** in `_gen_renderer_v2.py` becomes essential.

### 9.1 Why We Need It

- The Builder GPT can produce inconsistent or malformed data.
- Diagram layouts require structured data (`components`, `connections`, `relationships`, etc.).
- Early validation prevents runtime errors during HTML/SVG generation.
- It creates a clear contract between the Builder GPT and the renderer.

### 9.2 Recommended Strategy

Use **Pydantic models** to validate and normalize the `content` field based on `layout_type`.

Two approaches are possible:

| Approach                    | Complexity | Maintainability | Recommendation |
|-----------------------------|------------|------------------|----------------|
| Manual `CONTENT_MODELS` map | Low        | Medium           | Good for early development |
| **Discriminated Unions**    | Medium     | High             | **Preferred for production** |

### 9.3 Discriminated Unions (Recommended)

Pydantic v2’s Discriminated Unions allow automatic selection of the correct content model using the `layout_type` field.

**Example Structure:**

```python
from pydantic import BaseModel, Field
from typing import Annotated, Union, Literal

class TaggedEvidenceCardsContent(EvidenceCardsContent):
    layout_type: Literal["evidence_cards"]

class TaggedSystemArchitectureContent(SystemArchitectureContent):
    layout_type: Literal["system_architecture"]

class TaggedCausalLoopContent(CausalLoopContent):
    layout_type: Literal["causal_loop"]

# ... add Tagged* versions for all layouts

ContentUnion = Annotated[
    Union[
        TaggedEvidenceCardsContent,
        TaggedSystemArchitectureContent,
        TaggedCausalLoopContent,
        # Add remaining tagged models
    ],
    Field(discriminator="layout_type")
]

class ValidatedSlide(BaseModel):
    slide_number: int
    layout_type: str
    title: str
    content: ContentUnion
    evidence_ids: List[str] = Field(default_factory=list)
    speaker_notes: str
```

### 9.4 Benefits of Using Discriminated Unions

- Much cleaner validation code
- Excellent error messages per layout type
- Strong IDE and type checker support
- Easy to extend when adding new layouts
- Single source of truth (`layout_type` drives everything)

### 9.5 Implementation in `_gen_renderer_v2.py`

Add a validation step early in the rendering pipeline:

```python
def process_builder_handoff(handoff_data: dict):
    validated_slides = []
    for slide_data in handoff_data["slides"]:
        try:
            validated = ValidatedSlide(**slide_data)
            validated_slides.append(validated)
        except Exception as e:
            print(f"Validation failed for slide {slide_data.get('slide_number')}: {e}")
    return validated_slides
```

### 9.6 Recommendation

- Use the **manual map approach** during initial development for speed.
- Migrate to **Discriminated Unions** once the layout catalog stabilizes.
- Define Pydantic models for all new layouts (especially diagram layouts) as they are implemented.

This validation layer should be considered part of the core renderer infrastructure alongside the Grid Design System.

---

## 10. Success Metrics

- All existing layouts refactored to use the Grid Design System.
- At least **18–20 new high/medium priority layouts** implemented (including diagram layouts).
- Reusable **diagram component library** (SVG-based) is available.
- Clear ability to create **visually clear diagrams** for complex topics.
- Clear reduction in duplicated Grid CSS.
- Ability to comfortably create **dense, evidence-rich decks** and **complex explanatory slides**.
- Both low-density speaker slides and high-density reading slides are well supported.
- Documentation exists for layout selection, Grid usage, and diagram components.
- **Theming & Design Tokens** reach parity or better than `frontend-slides`:
  - Full design token system in place and used by all layouts/diagrams.
  - Brand consistency is strictly enforced.
  - Theme switching is possible via a simple configuration object.
  - Visual quality of generated decks matches or exceeds high-quality `frontend-slides` output.

---

## 10. Final Recommendations

1. **Start with Phase 1 + Phase 2** — Build the foundation first.
2. **Prioritize Wave 1 new layouts** — These will deliver the biggest impact on dense slide capability.
3. **Treat the Grid Design System as the single source of truth** for all future layout development.
4. **Keep the GPT Renderer Prompt in sync** throughout the process.
5. Consider creating a **visual layout gallery** (HTML demo) once the system is stable.

---

**This document serves as the authoritative implementation guide** for the next major version of `_gen_renderer_v2.py`.

It is designed to be followed sequentially while allowing parallel work on high-priority layouts once the Grid foundation is in place.

---

*End of Document*