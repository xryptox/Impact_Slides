# PLAN — Impact Slide Builder Prompt for Copilot (Teams) & ChatGPT

> Research + planning document for creating a new Step-3 Builder prompt that
> mirrors the discipline of the new Step-2 Analyst prompt
> (`Impact Slide Analyst - Copilot and ChatGPT.md`). **Plan only — no prompt
> file written yet, no code changes.**

---

## 1. Inventory of prompt / workflow Markdown files in the repo

Verified via `ls -la *.md` and `find . -name "*.md"` (repo root only; tests/
and impact_slides/ excluded).

### Prompt files (Analyst / Builder / Architect roles)

| File | Size | Role | Notes |
|---|---|---|---|
| `Impact Slide Analyst - Copilot and ChatGPT.md` | 23.5 KB | **Step 2 — Analyst (NEW)** | The prompt we just created. Copilot/Teams + ChatGPT. References only real v4 outputs. Emits `presentation_plan` + `slide_update_plan` + `quality_checklist` JSON handoff. |
| `Impact Slide Analyst GPT 5.5 Instant Optimized.md` | 9.2 KB | Step 2 — Analyst (OLD) | ChatGPT-only. Has the `pptx_slide_audit.json` drift and aspirational files. Superseded by the new prompt. |
| `Impact Slide Analyst v1 - Custom GPT Prompt.md` | 17.5 KB | Step 2 — Analyst (v1) | Earliest Analyst prompt. ChatGPT-only. |
| `Impact Slide Builder GPT 5.5 Instant Optimized.md` | 10.2 KB | **Step 3 — Builder (OLD, current)** | The current Builder prompt. ChatGPT-only. See §2. |
| `Impact Slide Builder v1 - Custom GPT Prompt.md` | 11.8 KB | Step 3 — Builder (v1) | Earliest Builder prompt. ChatGPT-only. Nearly identical structure to 5.5. |
| `Impact Slide Architect v3.md` | 28.8 KB | **Combined Analyst+Builder (legacy)** | The all-in-one predecessor (does analysis AND final slide content). Superseded by the Analyst/Builder split. |
| `# Impact Slide Architect v2 (Updated).md` | 10.8 KB | Combined Analyst+Builder (legacy v2) | Earlier all-in-one. |
| `Impact Slide Custom GPTs - Names and Descriptions.md` | 2.1 KB | GPT catalog | Names/descriptions for the Custom GPT store. Lists `Slide_Update_Plan.md/.json` and `Final_Slide_Content.md/.json` as handoff filenames. |

### Workflow / planning docs

| File | Size | Role |
|---|---|---|
| `Best Hybrid Workflow.md` | 6.2 KB | 4-step workflow overview. **Contains the aspirational file list** (`pptx_slide_audit.json`, `brand_style_summary.json`, `image_ocr_summary.json`, `asset_manifest.json`, `extracted_documents.md`) — same drift as the old prompts. |
| `Step4_Builder_Validator_Updated_Plan.md` | 4.4 KB | Step 4 design plan. Inputs: `Final_Slide_Content.json` + `brand_style_summary.json`. |
| `Step1_Test_Report.md`, `TESTING_PLAN.md`, `V2 Improvements.md`, `python_packages_Impact_Slides.md`, `Evidence_Register_Q3_Test.md` | — | Test/planning docs (out of scope). |

### Real v4 preprocessor output inventory (source of truth)

Verified by grepping `impact_slides/preprocessor.py` for written filenames:

```
analyst_briefing.json, analyst_briefing.md, coverage_map.json,
entities_summary.json, evidence_register.csv, evidence_register.md,
evidence_register_seed.json, evidence_schema.json, excel_profile.json,
file_inventory.json, filtering_log.json, pptx_profile.json,
preprocessor_summary.md, processing_errors.json, run.log, run_metadata.json
```

**Aspirational files v4 does NOT produce** (referenced by old prompts / workflow
docs): `pptx_slide_audit.json` (v4 writes `pptx_profile.json`), `brand_style_summary.json`,
`image_ocr_summary.json`, `extracted_documents.md`, `asset_manifest.json`,
`file_inventory.md` (v4 only `.json`).

### Step 4 integration point (critical)

`step4_builder_validator.py` (83.9 KB) EXISTS in the repo root. Its
`normalize_final_json()` (lines 421-445) already accepts BOTH schemas:
```python
presentation = data.get("presentation") or data.get("presentation_plan") or {}
slides = data.get("slides") or data.get("final_slides") or data.get("slide_update_plan") or []
```
So the Builder's JSON output (the `presentation`+`slides` shape) and the
Analyst's handoff (`presentation_plan`+`slide_update_plan`) are BOTH valid
inputs to Step 4. The validator also reads per-slide fields flexibly:
`title`/`proposed_title`, `purpose`/`new_slide_purpose`,
`audience_takeaway`/`key_message`. **The new Builder prompt must emit the
`presentation`+`slides` shape (the Builder's own contract), NOT just forward
the Analyst's handoff** — the Builder enriches each slide with final copy +
visual_spec, which is what Step 4 builds from.

Step 4 brand input: `--brand brand_style_summary.json` (line 2119). v4 does NOT
produce this file. Step 4 already falls back gracefully ("No brand file
supplied; using fallback theme", line 2178). **The real brand-cue source in v4
is `pptx_profile.json` → per-slide `details.theme_colors`** (verified: the
Performance.pptx run produces `pptx_profile.json[0].slides[*].details.theme_colors`).
A future improvement could teach Step 4 to read brand cues from
`pptx_profile.json`; for now the Builder should extract brand cues from
`pptx_profile.json` and inline them into its JSON `presentation.brand_style_summary`
string field so Step 4 gets them without the nonexistent file.

---

## 2. Deep analysis of the existing Step-3 Builder prompts

### 2a. `Impact Slide Builder GPT 5.5 Instant Optimized.md` (the current Builder)

**Role** (line 7): "presentation content and design execution GPT" — transforms
an approved Slide Update Plan from the Analyst into final slide titles,
headlines, bullets, key stats, evidence references, speaker notes, visual
design specs, optional Step-4 JSON. "You are not the primary analyst. Build
from the approved handoff."

**Input contract** (lines 52-65): expects an "approved handoff" containing
Audience Strategy, Evidence Register, **Brand Style Summary (if available)**,
Narrative Strategy, Slide Update Plan, Plan Notes/Open Questions. Accepted
files: `Slide_Update_Plan.md`, `Slide_Update_Plan.json`, or equivalent pasted
handoff. ⚠️ The handoff filename `Slide_Update_Plan.md/.json` does NOT match
what the new Analyst emits — the new Analyst produces a handoff the user saves
as `analyst_handoff.md`/`.json` (or any name), with a `presentation_plan` +
`slide_update_plan` JSON shape. **Contract mismatch #1.**

**Output contract** (Phases 2-3 + JSON Mode): Markdown slide-by-slide content
(headline, bullets, key stats, evidence) + Visual Design Spec table + Final
Quality Checklist; JSON Mode emits `presentation`+`slides`+`quality_checklist`
compatible with `step4_builder_validator.py` (line 34, 353).

**Mode/phase structure**: 4 phases (Handoff Verification → Final Slide Content
→ Visual Design Spec → Final Quality Checklist). Output modes: Default
Markdown / Visual Spec Only / Step 4 JSON. **No A/B/C/D mode-gating** (unlike
the Analyst's Mode A/B/C/D). The Builder assumes the plan is already approved
and proceeds in one pass (with a single "is this approved?" gate).

**Why→What→How→Now**: Each slide carries a `Section` field (Why/What/How/Now/
Appendix). The framework is respected but not phase-gated.

**File references**: References `step4_builder_validator.py` (correct — it
exists). References `Slide_Update_Plan.md/.json` (does NOT match the new
Analyst's `analyst_handoff` output). The `brand_style_summary` JSON field
(line 274) is a string field in the schema — but v4 produces no
`brand_style_summary.json` file. ⚠️ **Contract mismatch #2 (brand data).**

**Copilot/Teams awareness**: NONE. Zero mentions of Copilot, Teams, ChatGPT, or
thinking models. Pure ChatGPT/Custom-GPT framing ("Use this as the Custom GPT
Instructions").

**New-field awareness**: NONE. Zero mentions of `semantic_type`, `readiness_score`,
`quality_flags`, `narrative_readiness`, `focus_area`, `coverage_map`. The
Builder does not consume the Analyst's new pass-through fields. ⚠️ **Contract
mismatch #3 (new Analyst fields ignored).**

**Quality gates / guardrails** (Final Guardrails, line ~360): don't restate the
handoff; don't add unsupported claims; don't overfill slides; no vague filler.
Hard Boundaries section: don't invent numbers/quotes/sources/examples/timelines/
ROI/market claims/commitments; emit "Evidence needed: ..." for gaps; emit "Plan
conflict detected: ..." for conflicts. Solid — should be preserved.

**Controlled layout/visual types** (lines ~90-115): `layout_type` enum
(title_or_opening, split_text_visual, metric_dashboard, comparison_grid,
full_process_flow, timeline, roadmap, data_table, quote_card, other) and
visual-type enum (horizontal_process_flow, vertical_timeline, grouped_bar_chart,
stacked_bar_chart, waterfall_chart, heatmap, data_table, icon_grid,
key_stat_callout, dashboard, comparison_grid, roadmap, quote_card, other).
These are good controlled vocabularies and Step 4's `infer_layout_type()` uses
some of them — preserve and align with Step 4.

### 2b. `Impact Slide Builder v1 - Custom GPT Prompt.md`

Nearly identical structure to 5.5 (Role, Mission, Required Inputs, 5
Non-Negotiable Rules, Workflow Steps 1-5, Output Modes, JSON schema, Handling
Problems, Tone). Same contract mismatches as 5.5 (expects
`Slide_Update_Plan.md/.json`, references Brand Style Summary, no
readiness/semantic_type awareness, ChatGPT-only). The 5.5 version is a
slightly tightened v1 (adds Controlled Layout Types, Step 4 Compatibility
Rules). The v1 has a richer "Handling Problems" section (default neutral brand
style spec). Both are ChatGPT-only and predate the v4 preprocessor + new
Analyst contract.

---

## 3. Comparison vs the new Analyst prompt — top contract mismatches

| # | Mismatch | Old Builder | New Analyst (source of truth) |
|---|---|---|---|
| 1 | **Handoff filename** | expects `Slide_Update_Plan.md/.json` | emits a handoff the user saves as `analyst_handoff.md/.json` (JSON shape: `presentation_plan`+`slide_update_plan`+`quality_checklist`+...) |
| 2 | **Brand data source** | expects `Brand Style Summary` / `brand_style_summary.json` (v4 doesn't produce it) | v4 produces `pptx_profile.json` with per-slide `details.theme_colors`; new Analyst skips Brand Audit if no pptx and notes "Brand cues not available" |
| 3 | **`semantic_type`** | not mentioned | Analyst emits per-evidence `semantic_type` (Metric/Claim/Quote/Risk) and the Builder should use it to pick visuals (Metric→chart/stat callout, Quote→quote_card, Risk→conflict callout) |
| 4 | **`readiness_score` / `quality_flags`** | not mentioned | Analyst copies these from `analyst_briefing.json` into the handoff's `presentation_plan`; Builder should carry them through to its own JSON `presentation` block so Step 4 sees the same gap signals |
| 5 | **Copilot/Teams awareness** | none (ChatGPT-only) | new Analyst has a Teams Copilot + ChatGPT usage note + Source Priority tuned for attached-file delivery |
| 6 | **Source Priority list** | none (just "approved handoff") | new Analyst has a 15-item ordered Source Priority list referencing only real v4 outputs — the Builder needs its own (Analyst handoff first, then preprocessor outputs for verification) |

Additional structural gaps vs the new Analyst prompt:
- The Analyst prompt has a "How to read the v4 preprocessor outputs" section
  (EvidenceEntry shape, analyst_briefing consumption, coverage_map,
  entities_summary). The Builder has no equivalent — it doesn't know the v4
  output shapes it may need to consult for verification.
- The Analyst prompt has an active `analyst_briefing.md` consumption section
  with a quality-flag → action table. The Builder has no such guidance for
  consuming the Analyst's readiness/flags.
- The Analyst prompt's Final Guardrails include "If the user asks to skip
  alignment, mark assumptions with `[assumption]`" and "text truncated to 800
  chars" handling. The Builder has no equivalent for plan-skipping or
  truncated-evidence awareness.

---

## 4. The update plan

### 4.1 Recommendation: CREATE a new file (coexist), do NOT overwrite

Create `Impact Slide Builder - Copilot and ChatGPT.md` as a **new** file,
mirroring what we did for the Analyst. Reasons:
- The old `Impact Slide Builder GPT 5.5 Instant Optimized.md` is still a valid
  ChatGPT Custom-GPT instruction set for users on the legacy workflow; keeping
  it avoids breaking existing Custom GPTs.
- The new prompt targets Copilot Chat in Teams (file-attachment delivery model)
  AND ChatGPT, references only real v4 outputs, consumes the new Analyst
  handoff fields, and aligns with `step4_builder_validator.py`'s actual
  `normalize_final_json()` contract — a clean break is clearer than patching.
- Coexistence lets users A/B test, and the Custom GPTs catalog doc can list
  both.
- This mirrors the Analyst precedent exactly (new `... - Copilot and ChatGPT.md`
  alongside the old `GPT 5.5 Instant Optimized.md`).

### 4.2 Proposed structure of the new Builder prompt

Mirror the Analyst prompt's section discipline. Sections:

1. **Title + usage note** — `# Impact Slide Builder — Copilot (Teams) & ChatGPT`
   + a blockquote: "Use this as Step 3 of the 4-step workflow. In Microsoft
   Teams Copilot Chat, attach the Analyst's handoff file(s) and any
   preprocessor outputs you want the Builder to verify against. In ChatGPT,
   paste or upload the same. If a model selector is available, a thinking
   setting (o-series / Opus) improves spec precision."
2. **Role** — presentation content + design execution GPT; builds ONLY from an
   approved Analyst handoff; never re-analyzes.
3. **Core Mission** — produce final slide content + visual design specs +
   Step-4-ready JSON, Why→What→How→Now.
4. **Performance Rules** (~10) — adapt the old Builder's 10 rules + add:
   - Consume the Analyst's `semantic_type` to pick visuals.
   - Carry `readiness_score`/`quality_flags` through to your JSON.
   - Verify handoff is approved before building; if skipped, mark assumptions
     `[assumption]`.
   - Truncated evidence (text ends with `…`) → note `text truncated`, consult
     source.
   - Use controlled `layout_type` / visual-type vocabularies aligned with Step 4.
5. **Source Priority — use the attached Analyst handoff + preprocessor outputs**
   (NEW section for the Builder). Ordered list:
   1. `analyst_handoff.md` / `.json` — **the approved Analyst handoff; your
      primary source of truth** (contains presentation_plan, evidence_register,
      slide_update_plan, quality_checklist, readiness_score, quality_flags).
   2. `evidence_register_seed.json` — verify evidence IDs/text the Analyst
      cited; consult for full text when the Analyst's Key Finding looks
      truncated.
   3. `analyst_briefing.json` — original readiness/flags if you need to
      re-check a gap signal the Analyst acted on.
   4. `pptx_profile.json` — **brand-cue source** (per-slide
      `details.theme_colors`); extract brand cues for the Visual Design Spec
      when a deck was provided.
   5. `coverage_map.json` — confirms stage coverage the Analyst addressed.
   6. `preprocessor_summary.md` — run overview.
   7. `file_inventory.json` — confirms what was processed.
   8. Optional exports `evidence_register.md/.csv` — for cross-checking.
   9. `run_metadata.json`, `run.log` — low priority, diagnostic only.
   (Drop `brand_style_summary.json`, `asset_manifest.json`, `image_ocr_summary.json`,
   `extracted_documents.md`, `pptx_slide_audit.json` — v4 does not produce them.)
6. **How to read the Analyst handoff** (NEW section). Document:
   - The handoff JSON shape: `presentation_plan` (with `readiness_score`,
     `readiness_components`, `quality_flags`, `status`), `evidence_register[]`
     (each with `evidence_id`, `semantic_type`, refined Type/Best Slide
     Use/Confidence), `slide_update_plan[]` (Proposed Slide #, Section, Action,
     Purpose, Proposed Title, Key Message, Evidence, Recommended Visual,
     Audience Rationale, Priority), `quality_checklist[]`, `open_questions[]`.
   - The Markdown handoff has the same content in tables.
   - How to use `semantic_type` → visual: Metric→`metric_dashboard`/
     `key_stat_callout`/chart; Claim→`split_text_visual`/`icon_grid`;
     Quote→`quote_card`; Risk→`comparison_grid`/conflict callout.
   - Carry `readiness_score`/`quality_flags` into your output JSON's
     `presentation` block so Step 4 sees the gap signals.
7. **Detect the Current Mode** (mirror the Analyst's A/B/C/D, adapted for the
   Builder):
   - **Mode A — Build from Approved Plan** (default): user provides the
     approved Analyst handoff. Do Phase 1 (Handoff Verification) → Phase 2
     (Final Slide Content) → Phase 3 (Visual Design Spec) → Phase 4 (Final
     Quality Checklist). Stop and ask for approval to emit JSON/Step-4 handoff.
   - **Mode B — JSON / Step-4 Handoff Requested**: user asks for JSON, Gamma
     JSON, machine-readable, or Step-4-ready. Output ONLY valid JSON (no fences,
     no commentary) using the §"JSON Mode" schema.
   - **Mode C — Visual Spec Only**: user says "Visual Spec Only" / "Design
     Blueprint". Output only the Visual Design Specs.
   - **Mode D — User asks for actual PPTX/PDF/HTML files**: respond briefly
     that final file generation belongs to Step 4 (Python Builder/Validator);
     provide clean JSON/Markdown for them to save and pass to Step 4.
   (Keep it simpler than the Analyst's alignment-gating — the Builder's gate is
   just "is the plan approved?", since alignment already happened in Step 2.)
8. **Required Outputs by Phase**:
   - **Phase 1 — Handoff Verification** (table: Required Component | Status |
     Notes; components: Approved Analyst Handoff, Evidence Register, Narrative
     Strategy, Slide Update Plan, Quality Checklist/Open Questions, Brand Cues
     (from pptx_profile.json or "not available")). If the handoff is missing or
     unapproved → stop and ask.
   - **Phase 2 — Final Slide Content** (per slide: Section, Source/Existing
     Slide, Action, Layout Type, Purpose, Audience Takeaway, Headline, Bullets
     (3-5, <12 words), Key Stats (label/value/source-EID), Key Evidence (EIDs),
     Speaker Notes). Rules: preserve E#### IDs; use `semantic_type` to inform
     visual; demote `Needs evidence` slides honestly.
   - **Phase 3 — Visual Design Spec** (table: Position | Element Type |
     Content/Data Mapping | Visual Treatment | Brand Reference | Rationale).
     Pull brand cues from `pptx_profile.json` `details.theme_colors` when
     available; else clean neutral fallback labeled "proposed". Align visual
     types to the controlled vocabulary.
   - **Phase 4 — Final Quality Checklist** (table; add a row "Readiness gaps
     addressed" citing which Analyst `quality_flags` the Builder's plan
     addresses, mirroring the Analyst's checklist discipline).
9. **Accessibility Rules** — preserve the old Builder's list (font sizes,
   contrast, no color-only meaning, alt-text-ready, legible tables).
10. **JSON Mode** — the Step-4-ready schema. Use the old Builder's
    `presentation`+`slides`+`quality_checklist` shape (which
    `step4_builder_validator.py` already accepts), but EXTEND
    `presentation` to carry the Analyst's pass-through fields and add a
    `semantic_type` hint per slide. Proposed schema (see §4.3).
11. **Step 4 Compatibility Rules** — preserve the old rules (presentation must
    exist; slides is an array; every slide has slide_number/title/section/
    layout_type/content/visual_spec/evidence_sources; content.bullets and
    key_stats are arrays even if empty; visual_spec.primary_visual.steps_or_data
    is an array; lowercase action values). ADD: carry `readiness_score` and
    `quality_flags` in `presentation`; include `semantic_type` per evidence
    source.
12. **Final Guardrails** — preserve old + add:
    - Never silently drop an evidence ID the Analyst cited; if you can't use
      it, say why.
    - If the Analyst's handoff has `quality_flags` you didn't address, list them
      in the Quality Checklist as "Needs input".
    - If the Analyst's Key Finding ends with `…`, note `text truncated` and
      consult `evidence_register_seed.json` for full text.
    - If the user skipped Analyst alignment (handoff full of `[assumption]`),
      preserve those tags in your slide rationale and flag in the checklist.
    - Do not produce final PPTX/PDF/HTML — that is Step 4.

### 4.3 Proposed JSON schema for the Builder's Step-4 handoff

Extend the old Builder schema (which Step 4 already ingests) with Analyst
pass-through fields. Step 4's `normalize_final_json()` reads `presentation` /
`presentation_plan` and `slides` / `slide_update_plan` flexibly, so this is
forward-compatible.

```jsonc
{
  "presentation": {
    "title": "",
    "subtitle": "",
    "audience": "",
    "primary_goal": "",
    "desired_action": "",
    "total_recommended_slides": 0,
    "framework": "Why-What-How-Now",
    "brand_style_summary": "",          // extract from pptx_profile.json theme_colors, or "proposed neutral"
    "readiness_score": 0,               // carried from Analyst handoff presentation_plan
    "readiness_components": {            // carried from Analyst
      "coverage_balance": 0,
      "priority_quality": 0,
      "cross_file_connectivity": 0,
      "recommendation_strength": 0,
      "signal_ratio": 0
    },
    "quality_flags": []                 // carried from Analyst
  },
  "slides": [
    {
      "slide_number": 1,
      "section": "Why | What | How | Now | Appendix",
      "source_or_existing_slide": "",
      "action": "keep | revise | delete | split | merge | add | reorder | convert | brand_refresh",
      "priority": "must-have | should-have | could-have",   // from Analyst slide_update_plan
      "purpose": "",
      "audience_takeaway": "",
      "title": "",
      "subtitle": "",
      "layout_type": "title_or_opening | split_text_visual | metric_dashboard | comparison_grid | full_process_flow | timeline | roadmap | data_table | quote_card | other",
      "content": {
        "headline": "",
        "bullets": [],
        "key_stats": [
          { "label": "", "value": "", "source": "E####" }
        ],
        "body_text": ""
      },
      "evidence_sources": [
        {
          "evidence_id": "E####",
          "semantic_type": "Metric | Claim | Quote | Risk",  // carried from Analyst/seed
          "source_file": "",
          "exact_location": "",
          "usage": ""
        }
      ],
      "visual_spec": {
        "overall_layout_description": "",
        "primary_visual": {
          "type": "horizontal_process_flow | vertical_timeline | grouped_bar_chart | stacked_bar_chart | waterfall_chart | heatmap | data_table | icon_grid | key_stat_callout | dashboard | comparison_grid | roadmap | quote_card | other",
          "description": "",
          "steps_or_data": [],
          "data_source": "E####",
          "brand_mapping": ""
        },
        "supporting_visuals": [
          { "type": "", "position": "", "value_or_content": "", "style_notes": "" }
        ],
        "typography_notes": "",
        "color_usage": "",
        "assets_to_use": [],
        "accessibility_notes": "",
        "avoid": ""
      },
      "data_visualization": {
        "chart_type": "",
        "data_source": "",
        "highlight_numbers": [],
        "units_and_date_range": ""
      },
      "speaker_notes": ""
    }
  ],
  "quality_checklist": [
    { "check": "", "status": "pass | risk | needs_input", "notes": "" }
  ],
  "open_questions": []                  // carried from Analyst handoff
}
```

Key additions vs the old Builder schema:
- `presentation.readiness_score` / `readiness_components` / `quality_flags`
  (carried from the Analyst so Step 4 sees the same gap signals).
- `presentation.primary_goal` / `desired_action` (match the Analyst's
  `presentation_plan` field names — Step 4 reads `presentation` as-is).
- `slides[].priority` (Must/Should/Could-have from the Analyst's
  `slide_update_plan`).
- `slides[].evidence_sources[].semantic_type` (so Step 4 / a designer knows
  Metric vs Quote vs Risk → visual treatment).
- `open_questions` carried through.

### 4.4 Exact real-v4 file list the Builder should reference

In Source Priority order (Analyst handoff first, preprocessor outputs for
verification):
1. `analyst_handoff.md` / `analyst_handoff.json` (the approved Analyst
   handoff — primary source of truth)
2. `evidence_register_seed.json` (verify EIDs + full text)
3. `analyst_briefing.json` (original readiness/flags)
4. `pptx_profile.json` (brand cues: per-slide `details.theme_colors`) — only
   if a PPTX was among the Step-1 inputs
5. `coverage_map.json`
6. `preprocessor_summary.md`
7. `file_inventory.json`
8. `evidence_register.md` / `evidence_register.csv` (optional exports)
9. `run_metadata.json`, `run.log` (diagnostic)

### 4.5 Aspirational/wrong filenames to correct

The new Builder prompt must NOT reference (v4 doesn't produce them):
- ~~`brand_style_summary.json`~~ → use `pptx_profile.json` `details.theme_colors`
  for brand cues; inline them into `presentation.brand_style_summary` string.
- ~~`pptx_slide_audit.json`~~ → v4 writes `pptx_profile.json`.
- ~~`image_ocr_summary.json`~~, ~~`extracted_documents.md`~~,
  ~~`asset_manifest.json`~~, ~~`file_inventory.md`~~ → drop.
- ~~`Slide_Update_Plan.md/.json`~~ as the required handoff filename → accept
  the Analyst's handoff under whatever name the user saved it
  (`analyst_handoff.md/.json` by convention), with the
  `presentation_plan`+`slide_update_plan` JSON shape.

### 4.6 How the Builder consumes the new Analyst fields

- **Evidence IDs** (`E####`): preserve in every slide's `evidence_sources`; the
  Builder never invents new IDs (it may only cite the Analyst's). Step 4's
  `collect_slide_evidence_refs()` reads `evidence_sources[].evidence_id`.
- **`semantic_type`** (Metric/Claim/Quote/Risk): use to pick
  `layout_type`/`primary_visual.type` (Metric→`metric_dashboard`/
  `key_stat_callout`/chart; Claim→`split_text_visual`/`icon_grid`;
  Quote→`quote_card`; Risk→`comparison_grid` or conflict callout). Carry it into
  `evidence_sources[].semantic_type` so Step 4 / a designer sees it.
- **`readiness_score` / `readiness_components` / `quality_flags`**: copy from
  the Analyst handoff's `presentation_plan` into the Builder's
  `presentation` block verbatim (mirroring the Analyst's "copy from
  analyst_briefing.json" discipline — never retype, copy by reference when
  building the JSON). This guarantees Step 4 sees the same gap signals.
- **`slide_update_plan`**: each row (Proposed Slide #, Section, Action,
  Purpose, Proposed Title, Key Message, Evidence, Recommended Visual,
  Audience Rationale, Priority) drives one Builder slide. The Builder
  enriches with final headline/bullets/specs but preserves the Analyst's
  Section/Action/Priority/Evidence.
- **`quality_checklist` / `open_questions`**: the Builder adds a "Readiness
  gaps addressed" row to its own checklist citing which flags it addressed,
  and carries `open_questions` through to its JSON.

### 4.7 Risks / open questions for the user to decide

1. **Phase-gating depth**: should the Builder keep simple A/B/C/D modes
   (recommended) or adopt the Analyst's heavier alignment-gating? Recommended:
   keep it light (the Builder's only gate is "is the plan approved?"; alignment
   already happened in Step 2). **Open Q for user.**
2. **PPTX vs slide-content JSON**: the Builder produces JSON/Markdown, NOT
   PPTX (that's Step 4). Confirm this stays the boundary. (Old Builder already
   honors this; new one should too.)
3. **Brand cues from `pptx_profile.json`**: the new prompt should teach the
   Builder to read `pptx_profile.json[].slides[*].details.theme_colors` and
   inline them into `presentation.brand_style_summary`. Alternatively, teach
   Step 4 to read brand cues from `pptx_profile.json` directly (a code change,
   out of scope for this prompt). **Open Q: prompt-side now, code-side later?**
4. **`step4_builder_validator.py` already accepts the Analyst's
   `presentation_plan`+`slide_update_plan` shape** — so technically a user
   could skip the Builder and feed the Analyst handoff straight to Step 4. But
   Step 4 expects final slide copy (headline/bullets/visual_spec), which only
   the Builder produces. The new prompt should make clear the Builder enriches
   the Analyst's plan into buildable slides. No code change needed.
5. **Should the old `Impact Slide Builder GPT 5.5 Instant Optimized.md` be
   marked superseded** (e.g., add a one-line "Superseded by ... Copilot and
   ChatGPT.md" pointer at top, like we did for the Analyst)? Recommended yes,
   low-risk. **Open Q for user.**
6. **Custom GPTs catalog doc** (`Impact Slide Custom GPTs - Names and
   Descriptions.md`) lists `Slide_Update_Plan.md/.json` and
   `Final_Slide_Content.md/.json` as handoff filenames — should be updated to
   `analyst_handoff.md/.json` and the Builder's output (e.g.
   `final_slide_content.md/.json`). Minor, deferred. **Open Q for user.**
7. **`Best Hybrid Workflow.md`** still lists all the aspirational files in its
   Step 1/2/3 file lists. Same drift as the old prompts. A parallel cleanup pass
   (not part of this Builder prompt) could correct it. **Open Q for user.**

### 4.8 Sequencing (when the user approves)

1. Write `Impact Slide Builder - Copilot and ChatGPT.md` per §4.2 (new file,
   coexist).
2. Optionally add a one-line "Superseded by ..." pointer to the top of the old
   `Impact Slide Builder GPT 5.5 Instant Optimized.md` (§4.7 #5).
3. Update `Impact Slide Custom GPTs - Names and Descriptions.md` handoff
   filenames (§4.7 #6) — deferred unless user wants it now.
4. Test the new Builder prompt against the `analyst_handoff.md/.json` we
   already generated for the AmEx/TheFork case (in
   `realworld_test/amex_thefork_acquisition/analyst_handoff/`) by simulating
   Step 3 in a fork — produces `final_slide_content.md/.json`, then run
   `step4_builder_validator.py` on the JSON to confirm end-to-end Step 3→Step 4
   compatibility.

---

## 5. Biggest open question for the user

**Should brand cues flow through the prompt (Builder extracts
`pptx_profile.json` theme_colors and inlines them into its JSON) or through the
code (teach `step4_builder_validator.py` to read `pptx_profile.json` directly
via a new `--pptx-profile` flag)?** The prompt path is zero-code and works
today; the code path is more robust (Step 4 always sees real brand data even
if the Builder omitted it) but is a separate code change. Recommended: do the
prompt path now (it's in scope for this Builder-prompt task), and file the code
path as a deferred follow-up.
