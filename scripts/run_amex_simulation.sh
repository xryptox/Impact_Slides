#!/usr/bin/env bash
# GNHF simulation: replicate Amex Q1 2026 earnings PDF with renderer_v2,
# <=10 screenshot-comparison passes, output a capability gap analysis.
#
# Prereqs (verified on this machine):
#   - PDF:       C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf
#   - Playwright Chromium installed (python -m playwright install chromium)
#   - impact_slides.renderer_v2 importable
#
# Run from the repo root (main checkout). GNHF --worktree isolates artifacts.
set -euo pipefail

PDF="C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf"

# NOTE: read -d '' returns 1 at EOF (no NUL found); || true keeps set -e alive.
read -r -d '' PROMPT << 'EOF' || true
Objective: Produce a gap-analysis document stating which capabilities the current impact_slides.renderer_v2 LACKS to end-to-end replicate a real earnings PDF as standalone HTML slides, based on <=10 iterative visual-comparison passes. The deliverable is the analysis, NOT renderer changes.

This is a SIMULATION / OBSERVATION run.
- Do NOT modify production renderer code, layouts, CSS, schemas, or existing tests.
- Create new files ONLY, under simulation/amex_q1_2026/.
- Commit your work to the GNHF worktree branch as you go. IMPORTANT: simulation/ is gitignored on main (since 1628633), so a plain `git add simulation/` stages NOTHING and your commits will be empty — always `git add -f simulation/` (plus any other new files) before every commit. The --push flag then preserves each iteration on origin.
- Preserve all existing repo state.

Source PDF (read-only; the visual source of truth):
  C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf

Baseline reference (LAST completed sim — tracked in wiki):
  wiki/baseline_v7_GAP_ANALYSIS.md
  Companion evidence (v7 full artifacts — passes/, handoffs, screenshots): archived on the remote branch origin/gnhf/objective-produce-a-845b83 under simulation/amex_q1_2026/. To consult a file: git fetch origin gnhf/objective-produce-a-845b83, then git show origin/gnhf/objective-produce-a-845b83:simulation/amex_q1_2026/<path> (single file) or git checkout origin/gnhf/objective-produce-a-845b83 -- simulation/ (whole tree into your worktree).
  POLICY: simulation/ is gitignored on main and lives only in GNHF worktrees/branches to avoid bloating the repo. After each sim run humans (1) store the new GAP_ANALYSIS.md in wiki/ as wiki/baseline_v<N>_GAP_ANALYSIS.md (tracked), (2) keep the run's gnhf branch on origin as the full-artifact archive, (3) update the launcher's baseline path + open list. Always use the LATEST wiki baseline as the before-snapshot. Do not expect simulation/ archives on main.

  The v7 run measured the renderer after round-4 (T1/T2). Its headline: T1's callout geometry held live under a fresh handoff; T2's exterior-name knobs serialized but bought almost nothing on their own; the largest wins that round came from REMOVING handoff-side chrome (a triple-legend conflict on slide 27), not from renderer features.

=== MEASUREMENT METHOD CHANGED IN v8 — READ THIS CAREFULLY ===

Pixel-diff MAE percentages have been REMOVED from this simulation. Do NOT compute, report, rank, or compare mean-absolute-error or any whole-image similarity percentage. Do not produce a "visual similarity %" column.

Why: the metric was measured against a mostly-white canvas, so it was dominated by background agreement and compressed every real difference into a ~86-90% band where a genuine fix and pure noise were indistinguishable. Seven rounds of it never once ranked a gap correctly, it wrongly made real fixes look inert, and it actively caused mistakes — gaps were closed as "unfalsifiable inside the noise band" and one slide's numbers were scoring a table-transcription defect rather than the renderer. Worse, it created false confidence: chrome that was verifiably in the wrong coordinate frame still scored ~89%.

Replace it with TWO kinds of evidence, both Playwright-driven:

(1) GEOMETRY ASSERTIONS (the primary evidence — objective, falsifiable, cheap).
    Drive a real browser, read live layout, and compare NUMBERS THAT HAVE A CORRECT ANSWER against the PDF recipe. This is what has actually caught every real bug for two rounds. Examples of the shape wanted:
      - element bounding boxes vs the geometry they claim to reference (a callout capsule's edges vs the from/to bar centres from ch.scales.x.getPixelForValue)
      - a value-anchored node's centre vs ch.scales.y.getPixelForValue(value)
      - chrome that must sit OUTSIDE the plot: assert its top >= chartArea.bottom (or its right <= chartArea.left), not merely that it "looks below"
      - overlap checks: bounding-box intersection between overlays and the content they must not cover, asserted as zero
      - counts and structure: how many legends, headings, columns, label sets a slide actually emits
    Report these as measured-vs-expected pairs with a pass/fail and a pixel delta (e.g. "capsule left 97.5 vs bar-0 centre 97.5 — PASS (0.0px)"). A tolerance of +/-4px is the house standard. Write the numbers into the pass notes and cite them in GAP_ANALYSIS.md. Save the probe scripts under simulation/amex_q1_2026/probes/ so a human can re-run them.

(2) SIDE-BY-SIDE VISUAL READING (the qualitative evidence).
    For each slide, screenshot the rendered HTML at 1920x1080 and place it beside the rasterized PDF page. Then DESCRIBE the differences in words: what furniture is missing, what is the wrong colour or weight, what is mispositioned, what is present but too small, what the PDF has that no handoff key can express. A composite side-by-side PNG per interesting slide is far more useful than a diff heatmap — generate those, and keep a pixel-diff image ONLY if it helps a human see a specific misalignment (never as a score).

Rank gaps by SEVERITY OF THE VISUAL DEFECT and how structural it is, using your own judgment and the geometry results — NOT by any percentage. A useful ranking heuristic: chrome in the wrong coordinate frame or content being covered/hidden > missing structural furniture > wrong colour/weight > type-scale and density polish.

Two Playwright facts you need, both load-bearing:
  - Decks navigate by toggling an .active class on section.slide elements. scrollIntoView does NOT navigate. To inspect slide N: remove .active from all section.slide, add it to the Nth, then wait ~1s for Chart.js to lay out.
  - .deck-stage carries a CSS transform scale via fitStage(). At a 1920x1080 viewport the scale is 1.0, so canvas pixels and wrap-relative DOM pixels agree; if you change the viewport, account for the scale before comparing numbers.
  - Chart.js instances are reachable as Chart.getChart(canvasEl), giving you .scales.x/.y (with getPixelForValue) and .chartArea. That is the source of truth for expected geometry.

=== END MEASUREMENT METHOD ===

SINCE v7, all of round 5 has LANDED on main (PRs #117, #120, #119, #118). These are FIXED — do not rediscover them as gaps. Several change what you should EXPECT to see, so read this list before authoring pass 01:
  - T10 (PR #117) DEFAULT CHART PALETTE, and this one matters more than it sounds: _BAR_SERIES_COLORS held CSS custom-property strings like 'var(--navy, #00175a)', but Chart.js paints to canvas where CSS variables never resolve — so EVERY chart that omitted chart_config.series_colors was silently painting BLACK. Thirteen charts in the v7 handoff were affected (slides 05, 08, 10, 13x2, 16x2, 17, 20x2, 26x2, 27). The palette is now literal hex, so default-palette charts are navy/blue as intended. Consequence: v7 and earlier evidence for those slides was measured against BLACK charts, so treat their old conclusions as unreliable and re-observe from scratch.
  - T6 (PR #120) AXIS BREAK: y_axis_break used to paint a hardcoded 2px dashed line across the MIDDLE of the plot (reading as a false data threshold). It is now a small '//' hatch glyph positioned from the scales at the axis origin, entirely outside the plot area. This deliberately changed output for any deck using y_axis_break.
  - T7 (PR #120) CHEVRON: the callout chevron was one welded 34x22 node (triangle fused to its label via a CSS border-top). It is now a separate triangle + rounded pill, stacked below the tick-label row. Note: anchoring the chevron to the right category is a HANDOFF value (chart_config callout at:N) — the PDF anchors 'Refresh' to Q3'25 (at:2); v7's handoff declared at:4. Declare the correct anchor yourself.
  - T9 (PR #120) ANNOTATION BOXES: .chartjs-annotation was pinned at a hardcoded top:12%/left:22% and the handoff's declared x/y were DISCARDED. Annotations now honour x/y, interpreted as PIXEL OFFSETS INSIDE THE PLOT AREA (chartArea origin + (x,y), clamped inside, failing closed when unreadable). So you can now place Leap Year boxes deliberately — declare x/y and verify where they land.
  - T11 (PR #119) PANE HEADINGS: dual_chart panes emitted no heading, so a pane's series name fell through to a Chart.js legend swatch. Panes now render a real in-card heading and the redundant single-series legend is suppressed. Multi-series legends are KEPT by design (they carry information). If you see a stray legend swatch that merely restates a heading, that is now a finding, not expected.
  - T12 (PR #118) INSET COLLISIONS: .gl-inset was absolutely positioned with no layout reservation and covered content (on slide 19 it hid a column header and a value under a 204px overlap). Insets now reserve a gutter that the table shrinks into. Verify by bounding-box intersection, and report ANY remaining overlap anywhere in the deck as a bug.
  - T13 (PR #118) ANNEX BANDING: annex group headers alternated navy / light-blue purely by column index. They are now uniformly navy, matching the PDF. The white-on-navy quarter sub-header row stays.
  Also still current from round 4: T1 (#115) callout coordinate-frame geometry, T2 (#116) opt-in exterior-name typography knobs (segment_name_font_size, _line_height, _wrap_chars, _max_lines, _offset, _gutter — PDF-measured targets ~20px font, ~27px offset, ~117px gutter, ~11-char wrap; DECLARE these when tuning slide 27).

v8 re-test checklist (REQUIRED — every row must appear in the delta table, each with geometry numbers and/or a side-by-side reading, and NO percentage):
P0-verify: T10 default palette — confirm the previously-black charts (slides 05, 08, 10, 13, 16, 17, 20, 26, 27) now paint navy/blue. Assert no serialized Chart.js config contains 'var(--'. State plainly whether correct chart colour changes your reading of any slide that earlier rounds ranked as a packing/furniture gap.
P0-verify: T6 axis-break glyph (slide 05 right tile) — assert the glyph sits OUTSIDE the plot at the axis origin and that NO line crosses the plot.
P1-verify: T7 chevron split (slide 05 left tile) — assert triangle and pill are separate nodes, both clear of the tick-label row, centred on the anchored category. Declare at:2 per the PDF.
P1-verify: T9 annotation anchoring (slides 03, 10, 18 Leap Year boxes; slide 09 'Reported') — declare x/y and assert each box lands at chartArea origin + (x,y).
P1-verify: T11 pane headings (slide 16 Net Card Fees) — assert each pane has a heading and no redundant single-series legend swatch, while multi-series panes (05, 27) keep their legends.
P1-verify: T12 inset collisions (slides 19, 23) — assert ZERO bounding-box overlaps, and sweep all 44 slides for any other overlap.
P2-verify: T13 annex banding (slides 30, 31, 32) — assert group header cells are uniformly navy with the sub-header row still white-on-navy.
P1: F4+ (freestanding pill-column packing finish; slide 02) — still open. Measure before judging: report column widths, cell heights and the board's height as a fraction of the slide.
P2: N6 (provision furniture: freestanding reserve-rate boxed cells + exterior series legend; slide 14) — still open. Note exterior_segment_names and under-chart tables already exist; engage them before calling anything missing.
P1: N5 / F11 residual (slide 27 Funding density) — still open after T2. The v7 win here came from removing a triple-legend conflict; start from a clean single legend source.
P3: R4 (hero dual % type scale; slide 11) — still open; PDF target is ~110px digits with a smaller % glyph and the caption beside the number.
ACCEPTED DIVERGENCE — R1, F12+, and N2 chip weight are CLOSED, NOT GAPS (locked in wiki/SPEC_renderer_v2_amex_fidelity_r4.md D11): R1 flat-stage residual and F12+ annex multi-level header precision were each fixed once (#113, #114) and returned as exists-but-weak, and N2 in-bar chips are already bold 14px (heavier would look wrong on non-Amex decks). Do NOT report R1, F12+, or N2 chip weight as gaps in the delta table, the future-feature list, the divergence catalog, or the recommended order. Record each once as 'closed: accepted divergence per r4 spec D11' and move on.
ALSO ACCEPTED DIVERGENCE — the R2 elbow L-bracket-arm silhouette (the PDF's vertical bracket arms dropping from the capsule ends to the axis, per PDF p6/p7) is CLOSED, NOT A GAP (locked in wiki/SPEC_renderer_v2_amex_fidelity_r5.md L3). T1 places the capsule, stem and arrowhead to +/-0.1px; the residual is subjective silhouette matching. Record once as 'closed: accepted divergence per r5 spec L3'.
Also carry forward any other residual named in v7's future-feature list or divergence catalog.

PERMANENT EXCLUSION — R3 (Centurion seal / brand-asset replication) is a WONTFIX, NOT A GAP:
    CONTEXT.md rule: no third-party trademarks or brand assets in the renderer or asset pack; vendored marks (e.g. seal_lockup) are original artwork only; real companies bring their own mark via the handoff escape hatch. Therefore:
    - Do NOT report the missing Centurion seal asset or the cover/divider placement recipe as a gap, in any table, list, or divergence catalog.
    - Do NOT try to recreate the Centurion mark (or any Amex trademark) as SVG or any other form.
    - The generic seal_lockup placeholder on cover/dividers is the ACCEPTED by-design output. Cover/divider divergence attributable to the absent Amex mark is EXPECTED — call it by-design, exclude it from gap counts, and do not let it inflate divergence rankings (tag it 'R3 wontfix — excluded').
    - R3 must NOT appear in the delta table, the future-feature list, or the recommended implementation order. If the baseline lists R3 as open, record it once as 'dropped: wontfix per CONTEXT.md brand-asset rule' and move on.
  USE THE v7 GAP ANALYSIS AS THE BEFORE-SNAPSHOT. Your job is the AFTER picture against the CURRENT renderer: for EACH ID above, independently re-test and record resolved / partial / still-gap with YOUR fresh evidence. Do NOT inherit v7 conclusions blindly — verify each claim fresh. You may consult the v7 archive branch (see Companion evidence above) for reference, but your passes/ under THIS worktree's simulation/amex_q1_2026/ must be freshly generated.

Tools available (all verified installed):
- Extraction is VISION-BASED. Do NOT run impact_slides.preprocessor or step1_preprocessor_v4 — no heuristics/EID/priority pipeline. Instead: (1) rasterize each PDF page to a PNG with a PRIMITIVE PyMuPDF call (this is just rasterization, not the preprocessor):
      import fitz
      doc = fitz.open(r"C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf")
      for i, page in enumerate(doc):
          page.get_pixmap(dpi=200).save(f"simulation/amex_q1_2026/extracted/pdf_page_{i:02d}.png")
  and (2) TRANSCRIBE each page image yourself by LOOKING at it (you have vision). You may also use primitive page.get_text("dict") for structural text/layout/font/bbox data to cross-check your reading of a page — that is raw PyMuPDF, not the preprocessor, and is explicitly allowed.
  TABLE TRANSCRIPTION RULES (mandatory — v7 got these wrong and the renderer cannot recover from it): (a) Transcribe every table as a real 2-D grid: first cell is the row label, then ONE COLUMN PER PERIOD/CATEGORY, matching the PDF's column count exactly. NEVER flatten a table into ['Item','Detail'] key/value pairs with one PDF cell per row — v7 slides 33-36 did this and lost the entire column structure, so those slides were scoring a transcription defect, not the renderer. (b) Preserve sub-rows: annex metrics have an unbolded 'FX-Adjusted*' companion row under the bold GAAP/Reported row; keep them as separate rows sharing the column grid. (c) If ONE PDF page shows TWO separate tables (e.g. a values block plus a CAGR block, as on Annex 2), emit TWO visuals (primary_visual + secondary_visual, or two tiles) — do NOT merge them into a single wide table padded with empty cells. (d) After transcribing any table, sanity-check that no column is more than half empty; if it is, you have merged or flattened something and must re-read the page.
- impact_slides.renderer_v2 to render handoff JSON to standalone HTML (see its CLI/module docs and the v7 archive's handoff.json for a known-good schema example).
- Playwright (Chromium) for screenshots AND for the geometry probes described in the MEASUREMENT METHOD section.
- Pillow / numpy for compositing side-by-side images.

Workspace layout (create under the worktree):
  simulation/amex_q1_2026/
    extracted/                      # pdf_page_*.png (rasterized) + slides.json (vision-transcribed)
    probes/                         # reusable Playwright geometry probe scripts
    passes/
      pass_01/{handoff.json, output/, screenshots/, side_by_side/, geometry.json, notes.md}
      pass_02/...
      ...
    GAP_ANALYSIS.md                 # final deliverable

Worker loop (this is YOUR internal loop; <=10 passes HARD CAP):
1. Inspect the repo, the renderer_v2 surface, the handoff schema, and the PDF. Set up the workspace dirs.
2. Rasterize each PDF page to extracted/pdf_page_*.png (primitive PyMuPDF, NOT the preprocessor). Then vision-transcribe each page image into extracted/slides.json: per slide -> title, section, bullets, metrics, table cells (per the TABLE TRANSCRIPTION RULES), chart type+series+categories, speaker-note text, detectable brand colors/fonts.
3. Pass 01: hand-author a builder handoff JSON that uses renderer_v2 features as fully as possible (Boardroom tokens, gl-* layouts, charts.py / Chart.js for numeric slides, native disclosure, KPI/metric layouts) to recreate each PDF slide. Render to HTML. Playwright-screenshot each slide at 1920x1080 (navigate via the .active class). Build side-by-side composites against the matching pdf_page_*.png. Run your geometry probes and save the measured-vs-expected results to geometry.json. Write passes/pass_01/notes.md recording: what matched, what diverged, the geometry pass/fails, and FOR EACH divergence whether it is (A) a handoff-tuning gap (fixable by editing JSON) or (B) a renderer CAPABILITY gap (no handoff can express it).
4. Passes 02..<=10: adjust ONLY the handoff JSON (layout choices, content mapping, chart config, token usage) to close divergences of type (A). Re-render, re-screenshot, re-probe, append notes per pass. Do NOT edit renderer code to fix a gap; if a feature is missing, that is a finding to record, not something to implement now. Record failed (A) attempts honestly — a lever that made things worse is a real finding (v7's failed side_legend strip on slide 05 was one of its most useful results).
5. Stop adjusting early if remaining divergences are ALL type (B) capability gaps, even if <10 passes used.
6. Write simulation/amex_q1_2026/GAP_ANALYSIS.md containing:
   - A per-pass summary table: pass #, what changed in the handoff, geometry assertions passed/failed, top 3 remaining divergences, type (A/B). NO similarity percentage, NO MAE column.
   - A GEOMETRY RESULTS table: every assertion as [slide | node | measured | expected | delta px | pass/fail]. This is your objective evidence.
   - A before/after delta table cross-referencing the v7 open list: for EACH required ID (the T10/T6/T7/T9/T11/T12/T13 verify rows, plus F4+, N6, N5/F11 residual, R4 and any other v7 residual — but NOT R3, and NOT R1/F12+/N2-chip-weight, which are excluded per the wontfix and accepted-divergence blocks above), row = [baseline finding + slide | new status (resolved/partial/still-gap) | fresh evidence: geometry numbers and/or side-by-side observation | notes]. This is the headline deliverable. For the seven round-5 rows the question is VERIFICATION, not discovery: state plainly whether the landed fix holds under a fresh handoff, citing measured numbers. Also note any NEW gaps (continue N# numbering if useful).
   - A prioritized list of renderer features still open AFTER this run, each entry: feature name, what it enables, the SPECIFIC PDF slide + pass/side-by-side/geometry evidence that motivates it, whether it is "missing entirely" vs "exists but weak", and whether it is handoff-tunable (A) or a renderer capability gap (B). Rank by visual severity and how structural the defect is — NOT by any percentage. (If a baseline gap is now resolved, it drops OFF this future list. False-positive fixes stay on the list.)
   - A short "what renderer_v2 already does well" section (credit where due).

Constraints:
- <=10 comparison passes. Hard cap. Stop earlier if only capability gaps remain.
- No edits to impact_slides/ production code or tests. New files under simulation/ only.
- Every capability-gap claim in GAP_ANALYSIS.md MUST cite a specific PDF slide + the pass evidence (side-by-side image and/or geometry measurement) that demonstrates it.
- Do NOT report any MAE / similarity percentage anywhere in the deliverable. If you feel the need for a single number, use counts of failed geometry assertions instead.
- Do not invent renderer features; only document gaps observed against the real PDF.
- If a pass reveals the handoff schema cannot express something, that is a capability gap (record it), do not hack around it by editing renderer code.
- Verify every baseline claim against the CURRENT renderer before marking it resolved — do not assume commits or PR titles mean the visual gap is gone. A gap is only "resolved" if YOUR fresh evidence in THIS worktree shows it. Equally, do not assume a round-5 fix is broken because a slide still looks imperfect: check whether the residual is handoff-side (A) before blaming the renderer.
- This is MEASURE-ONLY. Do not start implementing renderer fixes in this run even if a gap looks easy — the fix phase (feature branch + no-mistakes gate) comes after GAP_ANALYSIS.md exists.
- FINAL STEP (required deliverable, after GAP_ANALYSIS.md is written): copy it into the tracked wiki as the next baseline — `cp simulation/amex_q1_2026/GAP_ANALYSIS.md wiki/baseline_v8_GAP_ANALYSIS.md` — then commit BOTH the baseline and the artifacts: `git add wiki/baseline_v8_GAP_ANALYSIS.md && git add -f simulation/ && git commit -m "v8 Amex sim: baseline + artifacts"`. The wiki/ path is tracked (plain add works); simulation/ is gitignored so it needs -f. The --push flag then preserves this iteration on origin. Do not try to merge simulation/ onto main.
- After this run completes, humans keep THIS run's gnhf branch on origin as the artifact archive and retarget the launcher (baseline path + open list) for the next run.

Stop only when: simulation/amex_q1_2026/GAP_ANALYSIS.md exists with a per-pass table, a geometry results table, a before/after delta table and a prioritized future-feature list (each citing PDF slide evidence, and none citing an MAE percentage), <=10 passes are recorded under simulation/amex_q1_2026/passes/, AND the final-step commit above (wiki baseline + force-added artifacts) has been made.
EOF

gnhf \
  --agent pi \
  --max-iterations 30 \
  --max-tokens 10000000 \
  --worktree \
 --push \
  --prevent-sleep on \
  --stop-when "simulation/amex_q1_2026/GAP_ANALYSIS.md exists with a per-pass table, a geometry results table, a before/after delta table and a prioritized future-feature list, <=10 passes are recorded under simulation/amex_q1_2026/passes/, and the final-step commit (wiki/baseline_v8_GAP_ANALYSIS.md plus force-added simulation/ artifacts) has been made" \
  "$PROMPT"
