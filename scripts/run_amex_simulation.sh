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

read -r -d '' PROMPT << 'EOF'
Objective: Produce a gap-analysis document stating which capabilities the current impact_slides.renderer_v2 LACKS to end-to-end replicate a real earnings PDF as standalone HTML slides, based on <=10 iterative screenshot-comparison passes. The deliverable is the analysis, NOT renderer changes.

This is a SIMULATION / OBSERVATION run.
- Do NOT modify production renderer code, layouts, CSS, schemas, or existing tests.
- Create new files ONLY, under simulation/amex_q1_2026/.
- Commit your work to the GNHF worktree branch as you go.
- Preserve all existing repo state.

Source PDF (read-only; the visual source of truth):
  C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf

Baseline reference (LAST completed sim worktree — NOT on main):
  C:/Users/Ag1Le/Documents/Impact_Slides-gnhf-worktrees/objective-produce-a-9c5007/simulation/amex_q1_2026/GAP_ANALYSIS.md
  Companion evidence (read-only): same worktree under simulation/amex_q1_2026/passes/ and extracted/.
  POLICY: simulation/ is gitignored on main and lives only in GNHF worktrees to avoid bloating the repo. Always use the LAST completed Amex sim worktree's GAP_ANALYSIS.md as the before-snapshot. Do not expect simulation/ archives on main.

  That v4 run measured the renderer AFTER round-3 fidelity work. Headline: F10+ and N1 RESOLVED; F11+/N2/N3 wires hold with visual polish residuals; R2 still weak; R3 Centurion asset still missing; mean MAE ~89.19% (flat vs v3).
  v4 open list (your REQUIRED re-test checklist — every row must appear in the next delta table):
    P0: R2 (IR callout chrome recipe), N2 residual (IR-weight year chips inside bars)
    P1: F11+ residual / N5 (exterior segment labels + denser packing), N3 residual / N4 (dual stack labels + signed paren chips)
    P2: F4+ (pill packing finish), R3 (Centurion seal asset + cover placement)
    P3: R1, R4, F12+
    Also carry forward any other residual named in v4's future-feature list or divergence catalog (N4, N5, …).
  USE THAT v4 GAP AS THE BEFORE-SNAPSHOT. Your job is the AFTER picture against the CURRENT renderer: for EACH ID above, independently re-test and record resolved / partial / still-gap with YOUR fresh pass/screenshot evidence. Do NOT inherit v4 conclusions blindly — verify each claim fresh. You may read the baseline worktree's passes/screenshots/handoff.json for reference, but your passes/ under THIS worktree's simulation/amex_q1_2026/ must be freshly generated.

Tools available (all verified installed):
- Extraction is VISION-BASED. Do NOT run impact_slides.preprocessor or step1_preprocessor_v4 — no heuristics/EID/priority pipeline. Instead: (1) rasterize each PDF page to a PNG with a PRIMITIVE PyMuPDF call (this is just rasterization, not the preprocessor):
      import fitz
      doc = fitz.open(r"C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf")
      for i, page in enumerate(doc):
          page.get_pixmap(dpi=200).save(f"simulation/amex_q1_2026/extracted/pdf_page_{i:02d}.png")
  (2) The worker (you, a vision LLM) READS each pdf_page_*.png and transcribes structured content into extracted/slides.json: per slide -> title, section, bullets, metrics, table cells, chart type + series + categories, speaker-note text, detectable brand colors/fonts/layout cues. Your vision is the extractor. (Alternative if you want zero PDF libs: serve the PDF via pdf.js in headless Chrome and Playwright-screenshot each page — only use this if the PyMuPDF rasterize fails.)
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
   - A per-pass summary table: pass #, overall visual similarity (%), top 3 divergences, type (A/B). Also report mean MAE vs the baseline worktree's final mean (v4 pass_01 was 89.19%; v4 pass_02 was 89.15%) so the delta is numeric.
   - A before/after delta table cross-referencing the baseline (v4) open list: for EACH required ID (R2, N2 residual, F11+/N5, N3/N4, F4+, R3, R1, R4, F12+ and any other baseline residual), row = [baseline finding + slide/pass | new status (resolved/partial/still-gap) | new slide/pass evidence | notes]. This is the headline deliverable. Also note any NEW gaps (continue N# numbering if useful).
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
- After this run completes, humans will treat THIS worktree as the new baseline for the next simulation (update the absolute baseline path in scripts/run_amex_simulation.*). Do not try to merge simulation/ onto main.

Stop only when: simulation/amex_q1_2026/GAP_ANALYSIS.md exists with a per-pass table AND a prioritized future-feature list (each citing PDF slide evidence), and <=10 passes are recorded under simulation/amex_q1_2026/passes/.
EOF

gnhf \
  --agent pi \
  --max-iterations 30 \
  --max-tokens 10000000 \
  --worktree \
  --prevent-sleep on \
  --stop-when "simulation/amex_q1_2026/GAP_ANALYSIS.md exists with a per-pass table and a prioritized future-feature list, and <=10 passes are recorded under simulation/amex_q1_2026/passes/" \
  "$PROMPT"
