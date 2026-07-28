#!/usr/bin/env bash
# GNHF simulation: replicate Amex Q1 2026 earnings PDF with renderer_v2,
# <=10 screenshot-comparison passes, output a capability gap analysis.
#
# Prereqs (verified on this machine):
#   - PDF:       C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf
#   - Playwright Chromium installed (python -m playwright install chromium)
#   - impact_slides.renderer_v2 + impact_slides.preprocessor importable
#
# Run from the repo root (main checkout). GNHF --worktree isolates artifacts.
set -euo pipefail

PDF="C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf"

# NOTE: read -d '' returns 1 at EOF (no NUL found); || true keeps set -e alive.
read -r -d '' PROMPT << 'EOF' || true
Objective: Produce a gap-analysis document stating which capabilities the current impact_slides.renderer_v2 LACKS to end-to-end replicate a real earnings PDF as standalone HTML slides, based on <=10 iterative screenshot-comparison passes. The deliverable is the analysis, NOT renderer changes.

This is a SIMULATION / OBSERVATION run.
- Do NOT modify production renderer code, layouts, CSS, schemas, or existing tests.
- Create new files ONLY, under simulation/amex_q1_2026/.
- Commit your work to the GNHF worktree branch as you go. IMPORTANT: simulation/ is gitignored on main (since 1628633), so a plain `git add simulation/` stages NOTHING and your commits will be empty — always `git add -f simulation/` (plus any other new files) before every commit. The --push flag then preserves each iteration on origin.
- Preserve all existing repo state.

Source PDF (read-only; the visual source of truth):
  C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf

Baseline reference (LAST completed sim — tracked in wiki):
  wiki/baseline_v6_GAP_ANALYSIS.md
  Companion evidence (v6 full artifacts — passes/, handoffs, screenshots): archived on the remote branch origin/gnhf/objective-produce-a-03e1d0 under simulation/amex_q1_2026/. To consult a file: git fetch origin gnhf/objective-produce-a-03e1d0, then git show origin/gnhf/objective-produce-a-03e1d0:simulation/amex_q1_2026/<path> (single file) or git checkout origin/gnhf/objective-produce-a-03e1d0 -- simulation/ (whole tree into your worktree).
  POLICY: simulation/ is gitignored on main and lives only in GNHF worktrees/branches to avoid bloating the repo. After each sim run humans (1) store the new GAP_ANALYSIS.md in wiki/ as wiki/baseline_v<N>_GAP_ANALYSIS.md (tracked), (2) keep the run's gnhf branch on origin as the full-artifact archive, (3) update the launcher's baseline path + open list. Always use the LATEST wiki baseline as the before-snapshot. Do not expect simulation/ archives on main.

  That v6 run measured the renderer BEFORE round-4 fixes. Its headline: #114 verified working (slide 05 +2.00pp, slide 11 +2.67pp under frozen handoff); R2 was the only P0 with capsule + chevron painting but GEOMETRY wrong; everything else exists-but-weak; mean MAE 89.31% best (flat vs v5 89.38% — white-canvas noise).

  SINCE v6, round-4 tickets T1 and T2 have LANDED on main (PRs #115, #116) — v7 is measuring them for the first time. Do not rediscover them as unfixed:
  - T1 (PR #115) fixed R2's ROOT CAUSE, a coordinate-frame bug: callout overlays were positioned as percentages of the chart wrap while the data they referenced lived in Chart.js chartArea pixel space (on slide 05 the value-11 capsule landed 28px high and spanned the full wrap instead of bar-centre to bar-centre). A calloutGeometry inline plugin now repositions the nodes from live chart geometry on afterLayout. Verified to +/-0.1px on all six acceptance criteria: capsule edges on the from/to bar centres, capsule centre on scales.y.getPixelForValue(value), stem spanning capsule bottom to the from-bar top, chevron centred on the category tick below chartArea.bottom. It also fixed grouped bars silently ignoring declared y_axis_min/max (the third instance of that bug after #96), and the capsule painting as a lens rather than a pill.
  - T2 (PR #116) addressed N5/F11 after measuring: bar width was ALREADY right (144px vs 140px-equiv), so the real divergence was exterior-name typography. New opt-in chart_config knobs: segment_name_font_size, segment_name_line_height, segment_name_wrap_chars, segment_name_max_lines, segment_name_offset, segment_name_gutter. A top-clamp bug that crushed spacing on 100%-stack boards was also fixed.
  Both are opt-in/default-unchanged, so DECLARE the T2 knobs in your handoff when tuning slide 27 — the PDF-measured targets were ~20px-equiv font, ~27px offset, ~117px gutter, ~11-char wrap.

v7 re-test checklist (REQUIRED — every row must appear in the delta table):
P0-verify: R2 callout geometry after T1 (slide 05, was 75.90%) — is the L-elbow pill now spanning bar-centre to bar-centre at its value with the chevron below the axis? Report whether exact geometry actually moved the slide MAE, since that is this round's central open question.
P1-verify: N5 / F11 exterior segment-name density after T2 (slide 27, was 78.60%) — declare the new knobs and report the delta.
P1: F4+ (freestanding pill-column packing finish; slide 02, was 90.56%) — still open, unmeasured.
P2: N6 (provision furniture: freestanding reserve-rate boxed cells + exterior series legend; slide 14, was 86.07%)
P3: R4 (hero % type scale; slide 11, was 85.67%)
ACCEPTED DIVERGENCE — R1, F12+, and N2 chip weight are CLOSED, NOT GAPS (locked in wiki/SPEC_renderer_v2_amex_fidelity_r4.md D11): R1 flat-stage residual (~92.6%) and F12+ annex multi-level header precision (~91-95%) sit inside the noise band of white-biased MAE so a fix is unfalsifiable, and N2 in-bar chips are already bold 14px (heavier would look wrong on non-Amex decks). All three were fixed once (#113, #114) and returned as exists-but-weak. Therefore: do NOT report R1, F12+, or N2 chip weight as gaps in the delta table, the future-feature list, the divergence catalog, or the recommended order. Record each once as 'closed: accepted divergence per r4 spec D11' and move on. Their slide MAE may be noted but must not inflate gap rankings.
ALSO ACCEPTED DIVERGENCE — the R2 elbow L-bracket-arm silhouette (the PDF's vertical bracket arms dropping from the capsule ends to the axis, per PDF p6/p7) is CLOSED, NOT A GAP (locked in wiki/SPEC_renderer_v2_amex_fidelity_r5.md L3). T1 (PR #115) already places the capsule, stem and arrowhead to +/-0.1px; three verified-correct fixes (#97, #104, #115) have landed and the residual is subjective silhouette matching. Do NOT report the L-elbow silhouette or bracket-arm geometry as a gap. Record once as 'closed: accepted divergence per r5 spec L3'.
Also carry forward any other residual named in v5's future-feature list or divergence catalog.

PERMANENT EXCLUSION — R3 (Centurion seal / brand-asset replication) is a WONTFIX, NOT A GAP:
    CONTEXT.md rule: no third-party trademarks or brand assets in the renderer or asset pack; vendored marks (e.g. seal_lockup) are original artwork only; real companies bring their own mark via the handoff escape hatch. Therefore:
    - Do NOT report the missing Centurion seal asset or the cover/divider placement recipe as a gap, in any table, list, or divergence catalog.
    - Do NOT try to recreate the Centurion mark (or any Amex trademark) as SVG or any other form.
    - The generic seal_lockup placeholder on cover/dividers is the ACCEPTED by-design output. Cover/divider pixel divergence attributable to the absent Amex mark is EXPECTED — call it by-design, exclude it from gap counts, and do not let it inflate divergence rankings (note the slide's MAE but tag it 'R3 wontfix — excluded').
    - R3 must NOT appear in the delta table, the future-feature list, or the recommended implementation order. If the baseline (v4) lists R3 as open, record it once as 'dropped: wontfix per CONTEXT.md brand-asset rule' and move on.
  USE THAT v4 GAP AS THE BEFORE-SNAPSHOT. Your job is the AFTER picture against the CURRENT renderer: for EACH ID above, independently re-test and record resolved / partial / still-gap with YOUR fresh pass/screenshot evidence. Do NOT inherit v4 conclusions blindly — verify each claim fresh. You may consult the v5 archive branch (see Companion evidence above) for passes/screenshots/handoff.json reference, but your passes/ under THIS worktree's simulation/amex_q1_2026/ must be freshly generated.

Tools available (all verified installed):
- Extraction is VISION-BASED. Do NOT run impact_slides.preprocessor or step1_preprocessor_v4 — no heuristics/EID/priority pipeline. Instead: (1) rasterize each PDF page to a PNG with a PRIMITIVE PyMuPDF call (this is just rasterization, not the preprocessor):
      import fitz
      doc = fitz.open(r"C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf")
      for i, page in enumerate(doc):
          page.get_pixmap(dpi=200).save(f"simulation/amex_q1_2026/extracted/pdf_page_{i:02d}.png")
  (2) The worker (you, a vision LLM) READS each pdf_page_*.png and transcribes structured content into extracted/slides.json: per slide -> title, section, bullets, metrics, table cells, chart type + series + categories, speaker-note text, detectable brand colors/fonts/layout cues. Your vision is the extractor. (Alternative if you want zero PDF libs: serve the PDF via pdf.js in headless Chrome and Playwright-screenshot each page — only use this if the PyMuPDF rasterize fails.)
  TABLE TRANSCRIPTION RULES (mandatory — v7 got these wrong and the renderer cannot recover from it): (a) Transcribe every table as a real 2-D grid: first cell is the row label, then ONE COLUMN PER PERIOD/CATEGORY, matching the PDF's column count exactly. NEVER flatten a table into ['Item','Detail'] key/value pairs with one PDF cell per row — v7 slides 33-36 did this and lost the entire column structure, so their MAE measured a transcription defect, not the renderer. (b) Preserve sub-rows: annex metrics have an unbolded 'FX-Adjusted*' companion row under the bold GAAP/Reported row; keep them as separate rows sharing the column grid. (c) If ONE PDF page shows TWO separate tables (e.g. a values block plus a CAGR block, as on Annex 2), emit TWO visuals (primary_visual + secondary_visual, or two tiles) — do NOT merge them into a single wide table padded with empty cells. (d) After transcribing any table, sanity-check that no column is more than half empty; if it is, you have merged or flattened something and must re-read the page.
- Renderer: `python -m impact_slides.renderer_v2 --handoff <handoff.json> --out <dir>` (entrypoint render_deck() in impact_slides/renderer_v2/cli.py; supports --debug, --self-contained/--use-cdn, --seed). Learn the handoff JSON schema from impact_slides/renderer_v2/schemas.py and wiki/SPEC_renderer_v2_p0_self_contained.md, wiki/SPEC_renderer_v2_p3_chartjs.md, wiki/SPEC_renderer_v2_p5_native_disclosure.md, wiki/alignment_spec.md.
- Screenshots + compare: Playwright Chromium. Use it to (a) screenshot the generated presentation.html at 1920x1080 (navigate each .slide and capture), and (b) compute a per-slide visual diff vs the corresponding extracted/pdf_page_*.png (pixel diff / SSIM or similar). Save side-by-side comparison images per pass.
- Domain vocabulary: read C:/Users/Ag1Le/Documents/Impact_Slides/CONTEXT.md for canonical terms (Boardroom, gl-*, handoff, layout, delivery mode, design tokens, feature gating, static fallback).

Workspace layout to create:
  simulation/amex_q1_2026/
    extracted/                      # pdf_page_*.png (rasterized) + slides.json (vision-transcribed)
    passes/
      pass_01/{handoff.json, output/, screenshots/, diff.png, notes.md}
      pass_02/...
      ...
    GAP_ANALYSIS.md                 # final deliverable

Worker loop (this is YOUR internal loop; <=10 passes HARD CAP):
1. Inspect the repo, the renderer_v2 surface, the handoff schema, and the PDF. Set up the workspace dirs.
2. Rasterize each PDF page to extracted/pdf_page_*.png (primitive PyMuPDF, NOT the preprocessor). Then vision-transcribe each page image into extracted/slides.json: per slide -> title, section, bullets, metrics, table cells, chart type+series+categories, speaker-note text, detectable brand colors/fonts.
3. Pass 01: hand-author a builder handoff JSON that uses renderer_v2 features as fully as possible (Boardroom tokens, gl-* layouts, charts.py / Chart.js for numeric slides, native disclosure, KPI/metric layouts) to recreate each PDF slide. Render to HTML. Playwright-screenshot each HTML slide at 1920x1080. Pixel-diff each HTML screenshot against the matching extracted/pdf_page_*.png. Write passes/pass_01/notes.md recording: what matched, what diverged, and FOR EACH divergence whether it is (A) a handoff-tuning gap (fixable by editing JSON) or (B) a renderer CAPABILITY gap (no handoff can express it).
4. Passes 02..<=10: adjust ONLY the handoff JSON (layout choices, content mapping, chart config, token usage) to close divergences of type (A). Re-render, re-screenshot, re-diff, append notes per pass. Do NOT edit renderer code to fix a gap; if a feature is missing, that is a finding to record, not something to implement now.
5. Stop adjusting early if remaining divergences are ALL type (B) capability gaps, even if <10 passes used.
6. Write simulation/amex_q1_2026/GAP_ANALYSIS.md containing:
   - A per-pass summary table: pass #, overall visual similarity (%), top 3 divergences, type (A/B). Also report mean MAE vs the baseline worktree's final mean (v6 pass_01 was 89.29%; v6 pass_02 (final) was 89.31%) so the delta is numeric.
   - A before/after delta table cross-referencing the baseline (v6) open list: for EACH required ID (R2, N5 residual/F11 packing, F4+, N6, R4 and any other baseline residual — but NOT R3, and NOT R1/F12+/N2-chip-weight, which are excluded per the wontfix and accepted-divergence blocks above), row = [baseline finding + slide/pass | new status (resolved/partial/still-gap) | new slide/pass evidence | notes]. This is the headline deliverable. For the two rows that round-4 already fixed (R2 via T1, N5/F11 via T2) the question is verification, not discovery: state plainly whether the landed fix holds under a fresh handoff and what it did to slide MAE. Also note any NEW gaps (continue N# numbering if useful).
   - A prioritized list of renderer features still open AFTER this run, each entry: feature name, what it enables, the SPECIFIC PDF slide + pass/screenshot that motivates it, and whether the feature is "missing entirely" vs "exists but weak". (If a baseline gap is now resolved, it drops OFF this future list. False-positive fixes stay on the list.)
   - A short "what renderer_v2 already does well" section (credit where due).

Constraints:
- <=10 comparison passes. Hard cap. Stop earlier if only capability gaps remain.
- No edits to impact_slides/ production code or tests. New files under simulation/ only.
- Every capability-gap claim in GAP_ANALYSIS.md MUST cite a specific PDF slide + the pass/screenshot that demonstrates it.
- Do not invent renderer features; only document gaps observed against the real PDF.
- If a pass reveals the handoff schema cannot express something, that is a capability gap (record it), do not hack around it by editing renderer code.
- The baseline is the LAST completed sim worktree (absolute path above), not anything under main's simulation/ (that path is gitignored and absent on main). Verify every baseline claim against the CURRENT renderer before marking it resolved — do not assume commits or PR titles mean the visual gap is gone. A gap is only "resolved" if YOUR fresh pass/screenshot in THIS worktree shows it.
- This is MEASURE-ONLY. Do not start implementing renderer fixes in this run even if a gap looks easy — Phase B (fix branch + no-mistakes gate) comes after GAP_ANALYSIS.md exists.
- FINAL STEP (required deliverable, after GAP_ANALYSIS.md is written): copy it into the tracked wiki as the next baseline — `cp simulation/amex_q1_2026/GAP_ANALYSIS.md wiki/baseline_v7_GAP_ANALYSIS.md` — then commit BOTH the baseline and the artifacts: `git add wiki/baseline_v7_GAP_ANALYSIS.md && git add -f simulation/ && git commit -m "v7 Amex sim: baseline + artifacts"`. The wiki/ path is tracked (plain add works); simulation/ is gitignored so it needs -f. The --push flag then preserves this iteration on origin. Do not try to merge simulation/ onto main.
- After this run completes, humans keep THIS run's gnhf branch on origin as the artifact archive and retarget the launcher (baseline path + open list) for the next run.

Stop only when: simulation/amex_q1_2026/GAP_ANALYSIS.md exists with a per-pass table AND a prioritized future-feature list (each citing PDF slide evidence), <=10 passes are recorded under simulation/amex_q1_2026/passes/, AND the final-step commit above (wiki baseline + force-added artifacts) has been made.
EOF

gnhf \
  --agent pi \
  --max-iterations 30 \
  --max-tokens 10000000 \
  --worktree \
 --push \
  --prevent-sleep on \
  --stop-when "simulation/amex_q1_2026/GAP_ANALYSIS.md exists with a per-pass table and a prioritized future-feature list, <=10 passes are recorded under simulation/amex_q1_2026/passes/, and the final-step commit (wiki/baseline_v7_GAP_ANALYSIS.md plus force-added simulation/ artifacts) has been made" \
  "$PROMPT"
