# Plan: Copilot/ChatGPT-only Step 4 Builder Prompt (frontend-slides aligned)

**Status:** Research + planning only. No prompt file or code written.
**Goal:** A GPT/Copilot prompt that produces the slide deck (HTML + PPTX) directly, replicating the `frontend-slides` skill as closely as possible, while staying aligned with the existing Builder handoff contract (evidence-focused, `analyst_handoff`-driven). Replaces the Python `step4_builder_validator.py` renderer as the source of truth for visual output.

---

## (A) frontend-slides skill research

**Canonical repo:** `zarazhangrui/frontend-slides` — "Create beautiful slides on the web using a coding agent's frontend skills." A Claude Code skill (ships as `SKILL.md` + assets). Reachable and scraped.

### Architecture (what makes it higher quality than step4)

| Aspect | frontend-slides | current step4_builder_validator.py |
|---|---|---|
| Output | Single zero-dependency HTML file, inline CSS/JS | Single HTML file, inline CSS/JS (copied the stage model) |
| Stage | Fixed 1920×1080, scaled as a whole, `.active`/`.visible` switching | Same (step4 already copied `viewport-base.css`) |
| Typography | Distinctive fonts via Fontshare/Google Fonts CDN; **explicitly bans** Inter/Roboto/Arial/system fonts as "AI slop" | Generic system font stack / Manrope fallback |
| Theming | CSS custom properties (design tokens); brand tokens injected | `resolve_brand_theme` → CSS vars (similar, but neutral-only since v4 has no brand file) |
| Icons | **Inline SVG** hand-authored per slide; no icon library, no emoji as primary | **None** — no icon system at all (root cause of icon_grid bug) |
| Charts | Hand-built CSS/SVG bars/grids — no chart library | Hand-built CSS grids (kpi-grid, comparison-grid) — similar but cruder |
| Motion | Staggered `animation-delay` reveals, `prefers-reduced-motion` support | Same reveal classes (copied) |
| Content density | Two explicit modes (speaker-led low-density vs reading-first high-density) | No density mode; fixed bullet cap of 6 |
| Speaker notes | PPT conversion preserves notes **as HTML comments**; no native notes pane | **None** — no notes anywhere (confirmed: 0 `notes_slide` refs) |
| PPTX | **Input only** (`extract-pptx.py` reads .pptx → content). Output is HTML + PDF (Playwright). **No native PPTX generation.** | python-pptx generates .pptx natively (the only PPTX path that exists) |
| Style discovery | "Show don't tell": generates 3 style-preview slides before the deck | None — deterministic neutral theme |

### Key structural pieces (quoted from `SKILL.md` + `viewport-base.css`)

1. **`viewport-base.css` (mandatory, included verbatim in every deck):** `.deck-viewport` (fixed, inset 0) → `.deck-stage` (1920×1080, `transform-origin: 0 0`, JS sets `translate+scale`) → `.slide` (absolute, `visibility:hidden` until `.active`/`.visible`). Print media query renders one fixed slide per page. `prefers-reduced-motion` support. **step4 already replicates this exactly** — so the stage mechanics are not the gap; the gap is content/typography/icons/notes.

2. **Non-negotiable fixed stage:** "Every slide is authored inside a fixed 1920×1080 stage. The stage scales uniformly to fit the viewport. It may letterbox; it must not re-layout content." No responsive breakpoints for slide content.

3. **Content density modes** (directly relevant to our evidence decks): low-density/speaker-led = 1 idea/slide, 1–3 bullets; high-density/reading-first = 4–8 bullets or 4–6 cards. **Our evidence decks are reading-first** (analyst handoff, async review) → high-density mode applies, but with the evidence-grounding discipline.

4. **PPT conversion rule (Phase 4):** "preserving all text, images, slide order, and speaker notes (as HTML comments)." This is the only notes pattern frontend-slides defines — HTML comments, not a visible notes pane.

5. **Anti-"AI-slop" rules:** no purple-gradient-on-white; no generic dashboard/card look; dominant color + sharp accents > timid even palettes. Relevant because step4's neutral theme is exactly the timid look frontend-slides warns against.

### What step4 already got right (don't reinvent)
- The 1920×1080 fixed-stage + `.active`/`.visible` switching + print media query + reduced-motion — step4 copied `viewport-base.css` faithfully.
- Staggered `reveal-*` `animation-delay` classes.
- CSS-var theming via `resolve_brand_theme`.

### What step4 is missing (the real gaps)
- **No icon system** (icon_grid has nothing to render).
- **No `data_table` renderer** (table-row data shoehorned through comparison_grid).
- **No speaker notes** (HTML or PPTX).
- **Generic typography** (no distinctive font; neutral theme only).
- **Visible evidence IDs on-slide** (frontend-slides would never show raw IDs).
- **No density mode** (fixed caps instead of adaptive).

### `Frontend_Slides_Enhancement_vs_Marp_Full_Chat.md` (in-repo prior chat)
This file documents a prior session that proposed enhancing frontend-slides with: a `tokens.css` design-token system, a 7-component library (kpi-card, metrics-grid, bar-chart-horizontal, process-flow, evidence-box, data-table, two-column), a Jinja2 Python mapping layer (`component_map.py`/`renderer.py`), and BeautifulSoup validation. **That proposal kept the Python renderer** (it's literally an enhancement of step4). The current task inverts it: keep frontend-slides' *approach* but move the renderer into the prompt itself (Copilot/GPT emits the HTML), dropping Python as the source of truth.

---

## (B) Concrete bug diagnosis (with file:line citations)

### Bug 1: `icon_grid` renders text with no icons
- **Root cause:** there is **no `icon_grid` renderer** in step4. `grep -n "icon_grid" step4_builder_validator.py` returns **zero matches**. The dispatch at `step4:1641-1649` has no `icon_grid` branch, so it falls through to the `else` → `render_html_default_slide` (`step4:1670`).
- `render_html_default_slide` emits a `<div class="visual-type">icon grid</div>` label + `<p class="visual-description">…</p>` (`step4:1689-1690`) — pure text, no icons, no grid.
- **Fix target:** a dedicated icon_grid renderer that emits a responsive grid of `<article>` cards each with an inline SVG icon + label. See (F).

### Bug 2: slide 6 data-point cards "broken" (rendered as Python list reprs)
- **Actual HTML (quoted from `presentation.html` slide 6, `layout-data-table`):**
  ```html
  <article class="comparison-card reveal-scale delay-2">
      <h3>Point 1</h3>
      <p>[&#x27;Metric&#x27;, &#x27;Value&#x27;, &#x27;Source&#x27;]</p>
  </article>
  <article class="comparison-card reveal-scale delay-3">
      <h3>Point 2</h3>
      <p>[&#x27;Countries&#x27;, &#x27;11 European&#x27;, &#x27;E0132&#x27;]</p>
  </article>
  ```
- **Root cause:** `data_table` routes to `render_html_comparison_slide` (`step4:1636`: `comparison_grid, data_table` share one renderer). The Builder put table rows in `visual_spec.primary_visual.steps_or_data` as **row arrays** (`['Countries','11 European','E0132']`). `render_html_comparison_slide` (`step4:1755`) treats each item as a string and does `item.split(":", 1)` (`step4:1772`); on a list this fails, so it falls back to `heading = "Point N"`, `body = str(item)` → the Python list repr is HTML-escaped and printed verbatim.
- **Fix target:** a dedicated `data_table` renderer that reads `steps_or_data` as a list of row arrays and emits a real `<table>` with a header row + body rows. See (F).

### Bug 3: Evidence IDs rendered visibly on every slide
- **HTML:** `step4:1648` — `evidence_html = f'<div class="evidence-row">Evidence: {html_escape(", ".join(evidence[:8]))}</div>'` injected into every non-title slide. Title slide: `step4:1665`. Confirmed in slide 6 HTML above (`<div class="evidence-row">Evidence: E0132, E0170, E0131</div>`).
- **PPTX:** `add_evidence_line` (`step4:1043`) writes the same IDs as an 8.5pt textbox on every PPTX slide.
- **Fix target:** remove both; move IDs into speaker notes. See (E).

### Bug 4: No speaker notes anywhere
- `grep -cn "notes_slide|speaker_notes|notes_tf|has_notes_slide" step4_builder_validator.py` = **0**. Neither HTML nor PPTX has any notes concept. See (E) for the design.

### Bug 5: `metric_dashboard` silently caps at 4 stats
- `render_html_metric_slide` (`step4:1721`): `for i, stat in enumerate(stats[:4])`. If the Builder emits 6 KPIs (as on a scale slide), only 4 render; the rest vanish with no warning. Not strictly "broken" but loses data.

### Bug 6: `quote_card` on slide 1 is silently overridden
- `infer_layout_type` (`step4:452`): `if slide.get("slide_number") == 1 or "title" in title: return "title_or_opening"`. Any layout set on slide 1 is ignored. (Already addressed in the Builder prompt; the Step-4 prompt must also respect this.)

### Per-layout renderer audit (AmEx deck)

| layout | renderer (step4 line) | AmEx status | verdict |
|---|---|---|---|
| `title_or_opening` | `render_html_title_slide` :1651 | slide 1 OK | works |
| `metric_dashboard` | `render_html_metric_slide` :1702 | slides 4,5 OK but capped at 4 | partial |
| `full_process_flow`/`timeline`/`roadmap` | `render_html_process_slide` :1732 | slides 2,7,11,13 OK | works |
| `comparison_grid` | `render_html_comparison_slide` :1755 | slide 12 OK | works |
| `data_table` | (shares comparison :1636) | **slide 6 BROKEN** (list reprs) | broken |
| `quote_card` | `render_html_quote_slide` :1783 | not on deck (slide 1 forced to title) | works if not slide 1 |
| `split_text_visual` | `render_html_default_slide` :1670 | slides 3,8,9,10,14 OK | works |
| `icon_grid` | (none → default :1670) | not on AmEx deck, but **BROKEN by design** | broken |
| `other` | `render_html_default_slide` :1670 | n/a | works |

---

## (C) Prompt architecture recommendation

**Recommendation: SPLIT into 2 prompts.** A single prompt covering handoff-parse + per-slide HTML layout + full-deck HTML generation + PPTX is too long for reliable Copilot Chat (Teams) adherence; ChatGPT could manage it but Copilot drops instructions past ~3-4k tokens of rules.

### Prompt 1 — `Impact Slide Renderer - Copilot and ChatGPT.md` (HTML deck)
- **Purpose:** Read the Builder handoff + evidence register → emit one self-contained `presentation.html` (frontend-slides style: 1920×1080 fixed stage, inline CSS/JS, distinctive fonts, inline-SVG icons, real tables, no on-slide evidence IDs, hidden notes pane).
- **Inputs (attached each session):** `builder_handoff.md`, `builder_handoff.json`, `evidence_register_seed.json`, `analyst_briefing.md` (for readiness passthrough), optionally `pptx_profile.json` (brand cues, read-only).
- **Outputs:** `presentation.html` (single file) + `slide_notes.md` (one notes block per slide, human-readable, also embedded as a hidden `<aside class="speaker-notes">` in the HTML).
- **Why split here:** HTML generation is the high-token-density step (CSS + per-slide markup). Isolating it lets the prompt fully specify the component library and typography without competing with PPTX mechanics.

### Prompt 2 — `Impact Slide PPTX Builder - Copilot and ChatGPT.md` (PPTX)
- **Purpose:** Read `presentation.html` (from Prompt 1) + `slide_notes.md` → emit a python-pptx script (`build_pptx.py`) the user runs, OR emit the `.pptx` directly if the environment allows. Produces native PPTX with speaker notes on every slide.
- **Inputs:** `presentation.html`, `slide_notes.md`, `builder_handoff.json` (for section/slide_number/order).
- **Outputs:** `build_pptx.py` (preferred — deterministic, re-runnable) + the resulting `presentation.pptx`.
- **Why split here:** PPTX generation is mechanical and benefits from being a script the user can re-run after HTML edits, rather than a one-shot LLM blob. See (G).

### Why not 3+ prompts
A "planner" pre-prompt (decide per-slide layout) is unnecessary — the Builder handoff already decides layout (`layout_type` per slide). Adding a planner would duplicate the Builder's role and risk drift. The two-prompt split is the minimum that respects Copilot context limits.

### Coexistence
Both new prompts **coexist** with the existing `Impact Slide Builder - Copilot and ChatGPT.md` (Step 3). The Step-3 Builder decides narrative + slide plan; the new Step-4 Renderer prompts materialize visuals. `step4_builder_validator.py` is kept as a fallback (see open questions) but is no longer the source of truth.

---

## (D) Handoff & evidence alignment

### Source Priority (mirrors the Step-3 Builder's, shifted one layer down)
1. `builder_handoff.md` — the approved slide plan, phase by phase (highest authority).
2. `builder_handoff.json` — machine-readable slides: `slide_number`, `title`, `section`, `layout_type`, `content`, `visual_spec`, `evidence_sources`.
3. `evidence_register_seed.json` — single source of truth for facts; confirm/expand every `E####` here.
4. `analyst_briefing.md` / `analyst_briefing.json` — `readiness_score`/`readiness_components`/`quality_flags` to carry into the deck metadata (do not re-derive).
5. `pptx_profile.json` — brand cues (read-only; v4 may not produce it → neutral theme).
6. `file_inventory.json`, `preprocessor_summary.md` — context only.

### The new prompt does NOT re-derive narrative
It only **renders** what the Builder decided. No new slides, no stage re-mapping, no evidence re-curation. If a slide's evidence is weak, the Builder already tagged it `SYNTHESIZED` in `content`/`speaker_notes`; the Renderer preserves that tag.

### Render-critical fields per slide (read from `builder_handoff.json`)
| field | path | used for |
|---|---|---|
| `slide_number` | slide.slide_number | ordering; slide-1 title override |
| `title` | slide.title | slide H1 |
| `section` | slide.section | kicker/section-label (Why/What/How/Now) |
| `layout_type` | slide.layout_type | picks the renderer |
| `content.headline` | slide.content.headline | subtitle/takeaway |
| `content.bullets` | slide.content.bullets[] | bullet list (split_text_visual) |
| `content.key_stats` | slide.content.key_stats[]{label,value,source} | metric_dashboard KPI cards |
| `content.body_text` | slide.content.body_text | quote_card body |
| `visual_spec.primary_visual.type` | …primary_visual.type | sub-layout (chart/icon style) |
| `visual_spec.primary_visual.description` | …primary_visual.description | human caption (HTML `other` only) |
| `visual_spec.primary_visual.steps_or_data` | …primary_visual.steps_or_data[] | process steps / table rows / comparison items |
| `evidence_sources[]` | slide.evidence_sources[]{evidence_id,source,source_file} | speaker notes (NOT on-slide) |

### Evidence fidelity rule (carried from Builder)
Every fact on every slide traces to ≥1 `E####` verified in `evidence_register_seed.json`. The Renderer cites IDs **only in speaker notes**, never on-slide. 0 invented IDs.

---

## (E) Evidence-ID removal + speaker notes

### On-slide: remove all visible E#### IDs
- HTML: delete the `evidence-row` div (`step4:1648`, `:1665`).
- PPTX: delete `add_evidence_line` (`step4:1043`).
- No `E####`, no `Evidence:` label, no source-file names appear anywhere in the visible slide body.

### Speaker notes: per-slide, well-formed
**Template (PPTX notes pane + HTML hidden `<aside class="speaker-notes" data-slide-number="N">`):**
```
SLIDE N — <title>
Section: <Why|What|How|Now|Appendix>
Grounding: <1-2 sentence claim this slide makes>
Evidence: <E0###> <source_file> — <one-line what it says>; <E0###> …
Confidence: <high|medium|low> (<reason if low, e.g. "OCR'd press-kit page", "synthesized from E0### + E0###">
Synthesized: <yes|no>  (carry the Builder's SYNTHESIZED tag)
```
- **HTML parity:** each `<section class="slide">` contains a hidden `<aside class="speaker-notes">…</aside>` (CSS `display:none` in normal view; a `?notes=1` URL param or a toggle button reveals them for review). This gives the HTML deck a notes pane frontend-slides lacks natively.
- **PPTX:** `slide.notes_slide.notes_text_frame.text = <the block above>` (python-pptx native API).
- **Optional `evidence_manifest.json`:** the Renderer can emit a separate flat file mapping `slide_number → [evidence_id, …]` for automated grounding checks (replaces the on-slide ID as the verification mechanism). The user/Builder verifies grounding via notes + manifest, not via on-slide text.

### Verification without on-slide IDs
- Speaker notes carry the IDs + source files + a grounding sentence.
- `evidence_manifest.json` gives a machine-checkable slide→evidence map.
- A future validation script can diff manifest IDs against `evidence_register_seed.json` (the old `validate_evidence` role from the Marp chat, but prompt-emitted not Python-embedded).

---

## (F) Visual quality bar + HTML/CSS sketches

### Icon system: inline SVG (recommended)
- **Why:** Copilot/ChatGPT can inline SVG markup directly; a Teams-attached HTML file cannot reliably load an external icon font (no CDN guarantee, offline). Emoji render inconsistently across platforms and read as unprofessional. Inline SVG is self-contained, themeable via `currentColor`, and matches frontend-slides' approach.
- **Icon set:** curate ~20 inline SVGs covering common evidence-deck concepts (growth↑, decline↓, globe, users, dollar, percent, warning⚠, check✓, flow, calendar, scale/balance, building, restaurant, travel, etc.). The prompt includes an `<svg>` sprite block the Renderer picks from by name. The Builder's `visual_spec.primary_visual.type` (e.g. `icon_grid`) + `steps_or_data` (icon-name + label pairs) drive selection.
- **Fallback:** if no named icon matches, emit a generic dot/marker, never empty.

### Layout sketches (target HTML for each fixed/broken layout)

**icon_grid** (new):
```html
<div class="icon-grid" style="--col-count:3">
  <article class="icon-card reveal-scale delay-2">
    <svg class="icon" viewBox="0 0 24 24"><path d="…"/></svg>
    <h3>50,000+</h3><p>Restaurants</p>
  </article>
  …
</div>
```

**data_table** (new, fixes slide 6):
```html
<table class="data-table">
  <thead><tr><th>Metric</th><th>Value</th><th>Source</th></tr></thead>
  <tbody>
    <tr><td>Countries</td><td>11 European</td><td>E0132</td></tr>
    <tr><td>Restaurants</td><td>50,000+</td><td>E0132</td></tr>
    …
  </tbody>
</table>
```
(Source column shown in-table here is fine for a data_table — it's tabular reference, not decorative; alternatively move to notes. User decision in (H).)

**metric_dashboard** (fix cap): `for i, stat in enumerate(stats[:6])` — raise cap to 6, auto-grid via `--col-count`.

**quote_card**: keep current `render_html_quote_slide` but ensure cite comes from `evidence_sources[0].source_file` (person/role), not raw E####.

### Typography (frontend-slides anti-slop)
- Use a distinctive font pair via Google Fonts/Fontshare CDN `<link>` (e.g. display: "Sora"/"Space Grotesk" — but frontend-slides warns Space Grotesk is overused; body: "Inter" is banned). Recommend display "Fraunces" or "Sora", body "DM Sans" or "Hanken Grotesk".
- CSS vars: `--font-display`, `--font-body`, `--font-mono`.
- The prompt should offer 2-3 font-pair presets (corporate / editorial / modern) since v4 has no brand file to drive the choice.

---

## (G) PPTX generation strategy

**Recommendation: Option 1 — Prompt 2 emits a `build_pptx.py` script (python-pptx) the user runs.**

| Option | Verdict | Why |
|---|---|---|
| 1. Prompt emits HTML + a `build_pptx.py` script | **RECOMMENDED** | HTML is the visual source of truth (frontend-slides style); PPTX is a deterministic materialization. Script is re-runnable after HTML/notes edits. Speaker notes work natively (`notes_slide`). |
| 2. Prompt emits HTML + PPTX-structure JSON a script consumes | rejected | just moves step4_builder_validator.py into a thinner shell; doesn't remove Python, and the JSON is a redundant intermediate |
| 3. HTML only + user runs HTML-to-PPTX converter | rejected | no converter reliably preserves layout/notes; fidelity loss |
| 4. Prompt writes OOXML/.pptx XML directly | rejected | extremely brittle, huge token cost, no notes support |

### How Option 1 works
- Prompt 1 (Renderer) emits `presentation.html` + `slide_notes.md` + `evidence_manifest.json`.
- Prompt 2 (PPTX Builder) reads those + `builder_handoff.json`, emits `build_pptx.py`:
  - python-pptx builds 1920×1080 (13.333"×7.5") slides.
  - Per slide: title, section kicker, body (bullets/KPI cards/table/quote per `layout_type`), **speaker notes** from `slide_notes.md`.
  - No `add_evidence_line`; IDs live only in notes.
  - Theme from `pptx_profile.json` if present, else neutral.
- User runs `python build_pptx.py` → `presentation.pptx`. Re-runnable.

### Notes parity
- HTML: hidden `<aside class="speaker-notes">` (revealed via toggle).
- PPTX: `slide.notes_slide.notes_text_frame`.
- Both populated from the same `slide_notes.md` block → no drift.

### Relationship to step4_builder_validator.py
- `step4_builder_validator.py` is **kept as a fallback** (not deleted) for users who want the old Python path. The new prompts are the recommended path. (User decision in (H) whether to eventually delete step4.)

---

## (H) Open questions for the user

1. **Icon set source:** curate ~20 inline SVGs in the prompt (my recommendation), or allow the LLM to free-generate SVG paths per slide (higher variance, risk of bad paths)?
2. **Prompt split confirmation:** approve the 2-prompt split (HTML Renderer + PPTX Builder), or force a single combined prompt (ChatGPT-only, Copilot may struggle)?
3. **PPTX strategy confirmation:** Option 1 (prompt emits `build_pptx.py` the user runs) — confirm, or do you want HTML-only with no PPTX?
4. **`step4_builder_validator.py` fate:** keep as fallback (recommended), or delete once the new prompts ship?
5. **Coexistence:** new Step-4 prompts coexist with the Step-3 Builder prompt (recommended) — confirm the layering: Step 3 Builder decides narrative → Step 4 Renderer materializes visuals.
6. **data_table source column:** show `E0132` in the table's Source column (tabular reference, my sketch in F), or move it to notes only for full consistency with the no-on-slide-IDs rule?
7. **Font presets:** ship 2-3 font-pair presets in the prompt (corporate/editorial/modern), or one default pair, or let the LLM choose freely each run (frontend-slides' anti-slop stance, but less deterministic)?
8. **Brand theme:** v4 produces no `brand_style_summary.json`; Step 4 resolves brand only from a user-supplied `--brand` file. Should the new Renderer prompt (a) stay neutral, (b) infer a theme from `pptx_profile.json` colors if present, or (c) offer the style-preview discovery flow from frontend-slides (3 preview slides before the deck)? (c) adds a round-trip; likely too heavy for an evidence deck.
9. **Density mode:** lock to high-density/reading-first (evidence decks are async-review), or expose the frontend-slides density choice?
10. **Notes toggle in HTML:** hidden `<aside>` revealed by a `?notes=1` URL param / toggle button — approve, or always-visible notes pane, or notes only in PPTX?

---

## Implementation order (once questions resolved)
1. Write Prompt 1 (`Impact Slide Renderer - Copilot and ChatGPT.md`) — HTML deck + notes + manifest. This is the bulk of the work.
2. Write Prompt 2 (`Impact Slide PPTX Builder - Copilot and ChatGPT.md`) — python-pptx script emitter.
3. Test Prompt 1 on the AmEx `builder_handoff_detection/` corpus → compare `presentation.html` vs the step4-rendered one (icon_grid, slide-6 table, no on-slide IDs, notes pane).
4. Test Prompt 2 → run emitted `build_pptx.py` → verify PPTX + notes.
5. Decide step4_builder_validator.py fate based on test results.
