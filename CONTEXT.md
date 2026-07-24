# Impact Slides

A pipeline that turns business source files (Excel, PPTX, PDF, DOCX, images) into evidence-backed presentation decks. It combines a Python preprocessor and validator with custom GPT roles (Analyst, Builder) and a Python renderer, using a hybrid split between deterministic extraction and LLM reasoning.

## Language

### Pipeline & Workflow

**Hybrid Workflow**:
The four-step division of labor: Step 1 Python Preprocessor → Step 2 Analyst → Step 3 Builder → Step 4 Renderer/Validator. Python owns extraction, measurement, and validation; GPTs own interpretation, narrative, and design direction.
_Avoid_: pipeline, process (when ambiguous with the `process_step` evidence type)

**Step 1 Preprocessor**:
The Python preprocessor (`impact_slides.preprocessor`, entered via `step1_preprocessor_v4.py`) that ingests source files and emits the Evidence Register plus companion artifacts. The current canonical version is **v4**; v2 and v3 are frozen regression baselines and must never be modified.
_Avoid_: preprocessor (unqualified when it could mean v1–v3), extractor

**Analyst**:
The *Impact Slide Analyst* custom GPT role. Analyzes source material and preprocessor outputs to produce an audience-specific, evidence-backed Slide Update Plan. Does not write final slide content.
_Avoid_: planner, strategist

**Builder**:
The *Impact Slide Builder* custom GPT role. Turns an approved Slide Update Plan into Final Slide Content (titles, bullets, speaker notes, visual design specs).
_Avoid_: generator, author

**Renderer**:
The Python renderer (`impact_slides.renderer_v2`) that turns Builder handoff JSON + Evidence Register into standalone HTML decks. Also the *Impact Slide Renderer* GPT role that produces layout/rendering guidance.
_Avoid_: converter, exporter

**Handoff**:
A structured JSON or Markdown artifact passed from one step to the next (e.g. Builder handoff JSON fed to the Renderer). Semi-trusted: validated at generate time, never executed blindly.

### Evidence & Narrative

**Evidence Register**:
A source-backed, priority-ordered list of evidence entries distilled from source files. The single source of truth for what claims a deck may make. Canonical schema lives in `schemas.py`.
_Avoid_: evidence list, findings

**Evidence ID (EID)**:
A stable identifier (e.g. `E0020`) assigned to one evidence entry. Preserved across steps so any slide claim can be traced back to its source.
_Avoid_: ref, citation id

**Evidence Entry**:
One unit of evidence: a typed finding (metric, quote, claim, story, visual, brand_cue, etc.) with a source file, exact location, priority score, and narrative-use stages.
_Avoid_: evidence item, record

**Priority Score**:
A 0–1 score ranking how narrative-useful an evidence entry is. May be boosted by user keywords (capped at 0.98) and is capped per evidence type.
_Avoid_: relevance, weight

**Narrative Use**:
The set of framework stages (Why / What / How / Now) an evidence entry can support. Drives stage coverage and readiness scoring.
_Avoid_: stage mapping (that is the mechanism), bucket

**Why → What → How → Now**:
The mandatory narrative framework. *Why* creates urgency, *What* gives the strategic answer, *How* makes it tangible, *Now* demands action. Every slide belongs to one section.
_Avoid_: the pyramid, SCQA

**Stage Coverage / Readiness**:
A measure of how completely evidence populates all four framework stages. A single-source PDF typically lands everything in *What* and scores low readiness; this is expected, not a bug.

### Planning Artifacts (Analyst → Builder)

**Slide Update Plan**:
The Analyst's primary deliverable: a per-slide plan (action, purpose, title, key message, evidence, recommended visual, priority) produced *before* any final content. Requires user approval before proceeding.
_Avoid_: deck plan, outline

**Slide Operation**:
The action prescribed for a slide when updating an existing deck: `keep | revise | delete | split | merge | add | reorder | convert | brand_refresh`. Closed vocabulary.
_Avoid_: edit type, change type

**Alignment Summary**:
The section the Analyst produces after evidence/audience analysis and before the Slide Update Plan, ending in five alignment questions that must be answered before planning proceeds.

**Audience Adaptation**:
The mandatory step of tuning narrative, evidence, tone, and visual depth to a specific audience before planning slides.

**Brand Style Summary**:
An extracted description of the target brand's colors, typography, grid, icons, charts, and logo rules. Drives token generation; falls back to a clean neutral style when brand data is weak.

**Final Slide Content**:
The Builder's deliverable: execution-ready per-slide content (headline, bullets, key stats, evidence sources, visual spec, speaker notes) in Markdown or the Final Slide JSON schema.

### Rendering & Output

**Boardroom**:
The locked default visual brand/theme for generated decks (palette, Source Sans 3 / IBM Plex Sans typography). Must not be replaced; only enhanced.
_Avoid_: the theme (when ambiguous), default style

**`gl-*` / Grid Foundation**:
The existing CSS grid primitive system and layout catalog underpinning Boardroom decks. Stays foundational; new work layers on top rather than replacing it.

**Self-Contained**:
The production-default delivery mode: the generated `presentation.html` requires no network request to render (no remote CSS/JS/font URLs). Fonts and libs are vendored and inlined.
_Avoid_: offline mode, bundled

**CDN Mode**:
The dev-only escape hatch (`--use-cdn`) that may emit remote CDN links for fonts/libs. Never the production default.
_Avoid_: online mode, default mode

**Delivery Mode**:
The self-contained vs CDN selection threaded through `render_deck`, the CLI, `run_meta.json`, and `DECK_META`. Mutually exclusive flags; conflicting flags fail closed.

**Inliner** (`lib_inliner`):
The single module that owns embedding of third-party/vendored assets (fonts now; future CSS/JS libs). No other module may emit head asset tags.
_Avoid_: asset embedder, bundler

**Design Tokens**:
CSS custom properties (colors, fonts, spacing, radii) that components prefer over hard-coded values. Boardroom tokens are the brand layer; semantic tokens map on top for multi-brand theming.
_Avoid_: CSS variables (generic), theme vars

**Open Props**:
A curated subset of an open design-token primitive library, mapped into Boardroom semantic tokens. Always on (CSS), unlike JS libs which are feature-gated.

**Feature Gating**:
The mechanism by which optional JS libraries (charts, mermaid, alpine, swiper, icons) are auto-enabled from handoff content, with soft size warnings. Reserved `feature_ids` select what the inliner includes.

**Layout**:
A named slide composition in the layout catalog (e.g. `split_text_visual`, `metric_dashboard`, `comparison_grid`, `evidence_cards`). New layouts must use strict `gl-*` primitives.
_Avoid_: template, slide type (use *layout*)

**Diagram Primitive**:
A zero-dependency, macro-based SVG building block (node, arrow, connector, group boundary, callout) used by diagram layouts. The project rejects external diagram libs (e.g. Mermaid) to keep the zero-dependency constraint, except where Mermaid is explicitly product direction.
_Avoid_: shape, figure

**Static Fallback**:
The readable non-JS form of a feature (e.g. a table/SVG for charts, static disclosure for interactivity) used when a feature flag is off or for export paths. Content must stay readable with JS absent.

**Golden Deck**:
A checked-in fixture handoff that exercises charts + native disclosure and passes the offline open check. The MVP1 "done" bar beyond engineering acceptance.

**Fixed Stage**:
The 1920×1080 canvas every slide targets. The stage scales uniformly to the viewport; content never reflows responsively.
_Avoid_: viewport (that scales), canvas (generic)

**Type (A) Divergence**:
A sim/fidelity gap closable by editing handoff JSON only (content, layout choice, freeform geometry) with no renderer code change.
_Avoid_: content bug (when the renderer is fine), handoff miss

**Type (B) Divergence** / **Capability Gap**:
A sim/fidelity gap with no adequate handoff expression (or an expression the renderer ignores/weakly honors) that requires renderer schema, layout, chart painter, or shell work.
_Avoid_: bug (unqualified), missing feature (when the type is still unsettled)

**Renderer Bug** (tracker label `bug`):
Broken or inconsistent behavior on an *existing* renderer surface — e.g. Chart.js ignoring `chart_config` the SVG path honors, negative series geometry absorbing below-zero segments, `key_stats` no-op on a layout that claims to support them.
_Avoid_: calling every Amex visual mismatch a bug

**Renderer Enhancement** (tracker label `enhancement`):
A missing first-class layout, recipe, asset, or painter capability (pill-column table, brand seal cover, broken axis, chrome level, etc.).
_Avoid_: bug (for greenfield recipes)

**Chrome Level**:
How much product shell surrounds the Fixed Stage (e.g. full Boardroom chrome vs stage-only / minimal). Boardroom full chrome remains the default; minimal is an optional delivery choice for parity and export hygiene, not a second brand.
_Avoid_: IR mode, IR shell, bare mode (when unqualified), theme (theme is tokens/brand; chrome level is shell chrome)

**Anniversary Retention Board**:
An IR chart recipe of grouped *horizontal* bars in a discontinuous high-window axis (e.g. 90–100% with a break), year labels inside bars — the Platinum retention card shape. Built on the `horizontal_bar_chart` layout; anniversary polish is Chart.js-only while the SVG fallback paints basic horizontal geometry.
_Avoid_: broken-axis chart (that's the `y_axis_break` field, a general mechanism), vertical retention bars

**Geometric Callout**:
Drawable annotation chrome (elbow arrows, chevrons, bands) attached to chart geometry — distinct from the text-only `chart_config.annotation` box. Part of the chart painter layer, not slide chrome.
_Avoid_: annotation (reserved for the text callout field), caption, footnote

## Rules

- Every major claim in a deck must cite an Evidence ID. Never invent statistics, quotes, or figures.
- The Slide Update Plan must be approved before Final Slide Content is generated.
- Boardroom and `gl-*` are foundational and must not be replaced — only enhanced.
- Production output defaults to self-contained; CDN is dev-only and never implied by ship docs.
- No third-party trademarks or brand assets in the renderer or asset pack. Vendored brand marks (e.g. `seal_lockup`) are original artwork only; real companies bring their own mark via the handoff escape hatch.
- The Inliner is the single owner of vendored asset embedding; layouts must not grow their own `<script src="https://...">`.
- v2 and v3 preprocessors are frozen regression baselines; v4 (`impact_slides/`) is canonical.
- `schemas.py` is the single source of truth for output shapes; README, code, and GPT prompts all derive from it.
