#!/usr/bin/env bash
# GNHF v10 simulation: re-verify closed v9 tickets and compare every Amex PDF
# page against its HTML slide. This is an observation-only artifact run.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

PDF="C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf"
REAL_HOME="${REAL_HOME:-C:/Users/Ag1Le}"
V10_HOME="${LOCALAPPDATA:-C:/Users/Ag1Le/AppData/Local}/Temp/gnhf-v10-supergrok"
PI_CLI="C:/Users/Ag1Le/AppData/Roaming/npm/node_modules/@earendil-works/pi-coding-agent/dist/cli.js"

if [[ ! -f "$PDF" ]]; then
  echo "Missing source PDF: $PDF" >&2
  exit 1
fi
if [[ ! -f "$PI_CLI" ]]; then
  echo "Missing pi CLI: $PI_CLI" >&2
  exit 1
fi

# GNHF reads its config from os.homedir(), so isolate its config for this run.
# Pi also resolves ~/.pi from home; the wrapper restores the real user home so
# its authenticated SuperGrok extension remains available while pinning only
# this launch to grok-4.5.
rm -rf "$V10_HOME"
mkdir -p "$V10_HOME/.gnhf"
PI_WRAPPER="$V10_HOME/pi-supergrok.cmd"

{
  printf '@ECHO off\r\n'
  printf 'SET "USERPROFILE=%s"\r\n' "$(cygpath -w "$REAL_HOME" 2>/dev/null || echo "$REAL_HOME")"
  printf 'SET "HOME=%s"\r\n' "$(cygpath -w "$REAL_HOME" 2>/dev/null || echo "$REAL_HOME")"
  printf 'node "%s" --provider supergrok --model grok-4.5 --thinking medium %%*\r\n' \
    "$(cygpath -w "$PI_CLI" 2>/dev/null || echo "$PI_CLI")"
} > "$PI_WRAPPER"

cat > "$V10_HOME/.gnhf/config.yml" <<EOF
agent: pi
agentPathOverride:
  pi: "$(cygpath -m "$PI_WRAPPER" 2>/dev/null || echo "$PI_WRAPPER")"
maxConsecutiveFailures: 3
preventSleep: true
EOF

# Fail before allocating a GNHF worktree if the pinned provider is unavailable.
if ! ( cd "$V10_HOME" && USERPROFILE="$V10_HOME" HOME="$V10_HOME" \
       cmd //c "$(cygpath -w "$PI_WRAPPER" 2>/dev/null || echo "$PI_WRAPPER")" \
         --list-models grok-4.5 2>/dev/null ) \
     | grep -q '^supergrok[[:space:]]\+grok-4\.5'; then
  echo "supergrok/grok-4.5 is not reachable through the pinned wrapper." >&2
  echo "Check ~/.pi/agent/auth.json and the pi-supergrok extension." >&2
  exit 1
fi

read -r -d '' PROMPT <<'EOF' || true
Objective: Produce an evidence-led v10 Amex Q1 2026 renderer baseline on the
current main. This is a SIMULATION / OBSERVATION run, not implementation work.
It has two equal deliverables:

1. Re-verify every renderer-facing ticket closed after v9 (#136, #138, #139,
   #140) with the actual closed-ticket handoff configuration; use #137's probe
   contract throughout.
2. Create a full, human-reviewable PDF-versus-HTML comparison for all 44 pages
   at 1920×1080, plus a per-slide qualitative ledger. Do not score images.

Read every applicable AGENTS.md before editing. Work only in this GNHF-created
worktree. Preserve existing state. Do not implement renderer fixes.

Source PDF (read-only):
  C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf

Tracked prior baseline:
  wiki/baseline_v9_GAP_ANALYSIS.md

Complete v9 artifact archive:
  origin/gnhf/objective-produce-a-2d5e02:simulation/amex_q1_2026/

Start from that archive's passes/pass_01/handoff.json. Copy it to the new
simulation/amex_q1_2026/passes/pass_01/handoff.json before applying ONLY the
closed-ticket handoff settings below. Do not follow
scripts/run_amex_simulation.sh: it is v8-era and has stale inputs and paths.

=== STRICT SCOPE ===

Allowed:
- New files below simulation/amex_q1_2026/ only.
- One new tracked report: wiki/baseline_v10_GAP_ANALYSIS.md, copied verbatim
  from simulation/amex_q1_2026/GAP_ANALYSIS.md in the final documentation
  commit.

Forbidden:
- impact_slides/ production source, CSS, schemas, layouts, and tests.
- Existing wiki docs, scripts, configuration, CI, GitHub issues, PRs, or labels.
- Renderer implementation, handoff tuning beyond the explicit closed-ticket
  settings, MAE, visual-similarity percentages, pixel-diff scores, and diff
  heatmaps.
- Claims based solely on a PR title, stale v9 observations, or a zero-match
  probe result.

simulation/ is gitignored. Force-add it with `git add -f simulation/` when
committing artifacts. The GNHF branch is the complete artifact archive; never
merge simulation artifacts into main.

=== PAGE / SLIDE IDENTITY ===

The v9 handoff has 44 slides numbered 1 through 44. For this source deck,
HTML data-slide-number N maps to PyMuPDF page index N-1, physical PDF page N.
Before making evidence, assert this mapping against the copied handoff's title
order and the rendered deck's 44 unique data-slide-number values. If it does
not hold, record the exact mismatch and stop rather than silently using ordinal
selectors.

Every artifact name and every report row must state all of:
- slide_number (1-based HTML identity),
- expected data-layout,
- PDF page index (0-based), and
- physical PDF page (1-based).

=== METHOD / PROBE CONTRACT (#137) ===

Use Playwright geometry as primary evidence and 1920×1080 PDF/HTML
side-by-sides as qualitative evidence. The house tolerance is ±4px unless a
closed-ticket acceptance threshold below says otherwise. Never publish an
image-score, similarity percent, MAE, or heatmap.

Use scripts/simulation_probe.py in every reusable Playwright probe. Do not
reinvent raw slide selectors.

- Select/activate slides ONLY with `activate_slide(page, slide_number,
  expected_layout)`. It asserts exactly one `data-slide-number` match and the
  expected `data-layout`; never use section.slide[index], nth selectors, or
  scrollIntoView.
- Every JSON result row includes slide_number and layout. A zero selector match
  or missing expected rendered node is a probe failure, not a successful
  observation of absence.
- Use `painted_datalabel_lines` for all Chart.js label evidence. It waits for
  the Chart instance plus nonempty painted `$datalabels._labels`; do not read
  pre-bind options.plugins.datalabels or sleep blindly after activation.
- Before every screenshot of a chart slide, call
  `wait_for_paint_ready_charts(page, slide_number, expected_layout)`. A Chart.js
  canvas is ready only when the instance exists, `chart.width`/`height` are
  nonzero, `chart.chartArea` is non-degenerate, every visible dataset has
  painted element geometry, and readiness holds across one animation frame.
  Do not treat `Chart.getChart(canvas)` alone as ready and do not substitute a
  fixed sleep (#146).
- At the fixed 1920×1080 stage, wait for layout/Chart.js paint-ready geometry
  after each activation before screenshotting. Capture console warnings and
  run_meta warnings with the relevant slide identity.

=== PASS 01 — CLOSED-TICKET REVALIDATION ===

Render exactly one current-main pass, in both ordinary Chart.js mode and a
JS-off/SVG render for the renderer-specific checks. Do not make speculative
pass_02 handoff edits. Record an honest failure or residual rather than tuning
past the supplied closed-ticket configuration.

Apply these settings to the copied v9 pass_01 handoff:

1. #136 — slide_number 15 / stacked_bar_chart / PDF physical page 15
   The existing list-of-lists primary data and `secondary_visual.skin:
   outlined_boxes` are the regression input. Do not convert its source rows to
   mapping objects. In Chart.js mode, verify the emitted runtime alignment
   marker and measure each outlined-cell centre against the live Chart.js bar
   centre. In JS-off/SVG mode, measure the same five centres against SVG bars.
   Acceptance: every delta is ≤12px in BOTH modes (record the maximum).

2. #138 — slide_number 28 / multi_panel / PDF physical page 28
   On only the `Deposit Programs` stacked-bar tile, add the approved structured
   chart_config.side_callout:

       {"value":"92% FDIC","label":["insured at","Q1'26"],
        "placement":"right","skin":"tall"}

   Leave the source badge present: the renderer must suppress competing badge
   chrome when the active opt-in callout paints. Keep its existing exterior
   segment names, 150px gutter, density settings, and explicit
   stack_total_labels. In Chart.js AND JS-off/SVG, verify exactly one unboxed
   three-line callout, shared right column with exterior names, tile-local top
   near the approved 49.8px, no callout/name/plot overlap, no duplicate badge,
   and independent "$151" / "$157" total labels. Record fit omissions or
   console/run_meta diagnostics as failures; never silently accept a missing
   callout.

3. #139 — slide_number 17 / dual_chart / PDF physical page 17
   Add `chart_config.typography` to BOTH panes with
   `y_tick_font_size: 24` and `datalabel_font_size: 28`; leave x ticks at their
   legacy size unless evidence needs to record their native rotation/skip.
   In both Chart.js and JS-off/SVG, verify two HTML-owned pane titles only
   (40px, 700, navy; no duplicate SVG title), 24px bold y ticks, and 28px
   ordinary painted datalabels where they fit. Record native tick rotation or
   skipping, collision suppressions, unsupported typography warnings, legacy
   title fallbacks, and clipping. For Chart.js label evidence use painted model
   lines and rendered model geometry; do not infer it from serialized options.

4. #140 — slide_number 3 / pill_comparison / PDF physical page 3
   Do NOT add a handoff knob. The merged CSS recipe applies to the direct,
   five-body-row board. Re-measure it against the approved normalized PDF
   targets:

       virtual board: x=127.312, y=262.680, w=1564.911, h=624.640
       first shell:   x=769.592, y=262.680, w=295.914
       cap height:    115.200

   Record board/shell/cap deltas, five label/value row-centre deltas, the 28px
   two-line YoY cap, and overflow state. Also prove slide 20's inset-backed
   pill board and slide 24's two data-table insets do not match the fixed-board
   selector and retain their legacy/inset geometry.

#137 is tooling-only: its acceptance is use of this identity/readiness contract
in the committed probes and every result row, not a visual claim.

=== FULL 44-PAGE PDF ↔ HTML COMPARISON ===

This is mandatory, not a focus-slide sample.

1. Rasterize ALL 44 source PDF pages directly from the source PDF at exactly
   1920×1080. Use each page's actual dimensions (e.g. PyMuPDF matrix
   1920/page.rect.width by 1080/page.rect.height), not a screenshot resize.
2. Render and screenshot ALL 44 matching HTML slides at exactly 1920×1080.
   Use the identity contract above to activate each slide.
3. Produce one full-resolution side-by-side PNG per mapped pair without
   downscaling either half: PDF left, HTML right, with a short header carrying
   `PDF physical P (index I) | HTML slide N | layout`.
4. Produce a labeled contact sheet of all 44 comparisons for fast human review.
5. Write `simulation/amex_q1_2026/comparison_manifest.json` with one row per
   slide containing identity, PDF/HTML/SBS artifact paths, and whether all
   three files exist. It is an artifact manifest, NOT a score.
6. Write a 44-row qualitative comparison ledger in the report. Each row must
   link its full-resolution SBS path and say either `no material new finding`,
   `closed-ticket verification`, `accepted divergence`, `source/content`, or
   a concise evidence-backed candidate renderer gap. Do not manufacture a
   renderer ticket from normal visual differences; do not hide a real mismatch
   in a blanket “looks good” claim.

Store PDF rasters, HTML shots, full-size side-by-sides, contact sheet, probes,
probe JSON, console/warning captures, and manifest under
simulation/amex_q1_2026/. Keep the normal comparison artifacts separate from
any JS-off/SVG closed-ticket evidence so a reviewer can tell which runtime is
shown.

=== REQUIRED REPORT ===

Write simulation/amex_q1_2026/GAP_ANALYSIS.md and copy it verbatim to
wiki/baseline_v10_GAP_ANALYSIS.md. It must contain:

1. renderer commit, source PDF identity, current handoff source, page/slide
   mapping assertion, and scope-gate result;
2. a closed-ticket scorecard for #136–#140 (including #137 process compliance):
   settings applied, Chart.js result, SVG result where required, exact geometry
   / DOM evidence, artifact/probe paths, and pass/fail;
3. the complete 44-row PDF ↔ HTML qualitative ledger and artifact manifest
   summary; no image-derived numeric score;
4. a v9→v10 delta table that distinguishes historical observations from fresh
   revalidation, plus a short list of only evidence-backed residuals;
5. a #139 full-deck audit table enumerating per-slide pane-title state,
   legacy-title fallback, tick rotation/skip, datalabel suppression, unsupported
   typography warning, and clipping state for both ordinary and JS-off/SVG
   inspection; write “not applicable” explicitly for non-chart slides;
6. a concise account of what renderer_v2 does well and a separate list of
   accepted/source divergences. Do not file issues from this simulation.

A capability is not verified because a PR exists. An imperfection is not a
renderer gap merely because it is visible.

=== FINAL COMMITS AND STOP ===

Create exactly these two final commits, in this order:
1. `sim: store v10 Amex full comparison artifacts`
   Force-add only `simulation/amex_q1_2026/`.
2. `docs: store v10 Amex closed-ticket revalidation`
   Add only `wiki/baseline_v10_GAP_ANALYSIS.md`.

Push is handled by GNHF. If the PDF, PyMuPDF, Playwright/Chromium, v9 archive,
or required renderer runtime is inaccessible, record the exact blocker and
stop without claiming a baseline.

Stop only when both commits exist; the v10 report and all 44 PDF/HTML/SBS pairs
exist; every #136–#140 scorecard is evidence-backed; no forbidden path changed;
and no report/artifact contains MAE, a similarity percentage, or pixel-diff
scoring.
EOF

USERPROFILE="$V10_HOME" HOME="$V10_HOME" \
gnhf \
  --agent pi \
  --max-iterations 10 \
  --max-tokens 10000000 \
  --worktree \
  --push \
  --prevent-sleep on \
  --stop-when "A v10 evidence baseline, 44 full PDF/HTML comparisons, all closed-ticket scorecards, and the two required commits exist; no production paths changed." \
  "$PROMPT"
