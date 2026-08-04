#!/usr/bin/env bash
# GNHF v9 simulation: re-baseline Amex Q1 2026 PDF fidelity on current main.
#
# This is a measure-only observation run. It creates a separate GNHF worktree,
# archives full artifacts on its GNHF branch, and writes a cherry-pickable v9
# baseline document. It never edits renderer production code.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

PDF="C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf"
REAL_HOME="${REAL_HOME:-C:/Users/Ag1Le}"
V9_HOME="${LOCALAPPDATA:-C:/Users/Ag1Le/AppData/Local}/Temp/gnhf-v9-supergrok"
PI_CLI="C:/Users/Ag1Le/AppData/Roaming/npm/node_modules/@earendil-works/pi-coding-agent/dist/cli.js"

if [[ ! -f "$PDF" ]]; then
  echo "Missing source PDF: $PDF" >&2
  exit 1
fi
if [[ ! -f "$PI_CLI" ]]; then
  echo "Missing pi CLI: $PI_CLI" >&2
  exit 1
fi

# gnhf has no per-run model flag and reads its config from os.homedir(), so an
# isolated temporary home pins this run without mutating ~/.gnhf/config.yml.
#
# But pi ALSO resolves ~/.pi (settings, auth.json, the supergrok extension) from
# the home dir, so pointing HOME at the temp dir would leave pi with no
# credentials at all ("No models available"). The agent wrapper therefore
# restores the real HOME/USERPROFILE before launching pi, and pins the model
# itself instead of using agentArgsOverride.
rm -rf "$V9_HOME"
mkdir -p "$V9_HOME/.gnhf"
PI_WRAPPER="$V9_HOME/pi-supergrok.cmd"

{
  printf '@ECHO off\r\n'
  printf 'SET "USERPROFILE=%s"\r\n' "$(cygpath -w "$REAL_HOME" 2>/dev/null || echo "$REAL_HOME")"
  printf 'SET "HOME=%s"\r\n' "$(cygpath -w "$REAL_HOME" 2>/dev/null || echo "$REAL_HOME")"
  printf 'node "%s" --provider supergrok --model grok-4.5 --thinking medium %%*\r\n' \
    "$(cygpath -w "$PI_CLI" 2>/dev/null || echo "$PI_CLI")"
} > "$PI_WRAPPER"

cat > "$V9_HOME/.gnhf/config.yml" <<EOF
agent: pi
agentPathOverride:
  pi: "$(cygpath -m "$PI_WRAPPER" 2>/dev/null || echo "$PI_WRAPPER")"
maxConsecutiveFailures: 3
preventSleep: true
EOF

# Fail fast if the pinned model is not actually reachable. Run this from the
# temp dir, not the repo: cmd.exe with a redirected HOME drops a stray
# Microsoft/Windows/PowerShell cache into the current working directory.
if ! ( cd "$V9_HOME" && USERPROFILE="$V9_HOME" HOME="$V9_HOME" \
       cmd //c "$(cygpath -w "$PI_WRAPPER" 2>/dev/null || echo "$PI_WRAPPER")" \
         --list-models grok-4.5 2>/dev/null ) \
     | grep -q '^supergrok[[:space:]]\+grok-4\.5'; then
  echo "supergrok/grok-4.5 is not reachable through the pinned wrapper." >&2
  echo "Check ~/.pi/agent/auth.json and the pi-supergrok extension." >&2
  exit 1
fi

read -r -d '' PROMPT <<'EOF' || true
Objective: Produce a fresh, evidence-led v9 baseline for the Amex Q1 2026
Earnings Presentation PDF on the current renderer. This is a SIMULATION /
OBSERVATION run. Exercise the post-v8 handoff capabilities, verify what really
changed, and report only residual gaps supported by fresh geometry and
side-by-side evidence. Do NOT implement renderer fixes.

Read every applicable AGENTS.md before editing. Work only in this GNHF-created
worktree. Preserve existing state.

Source PDF (read-only):
  C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf

Tracked before-snapshot:
  wiki/baseline_v8_GAP_ANALYSIS.md

Complete v8 artifact archive:
  origin/gnhf/objective-produce-a-b7e827:simulation/amex_q1_2026/

Start from v8 passes/pass_03/handoff.json, copied to the new
simulation/amex_q1_2026/passes/pass_01/handoff.json. Do NOT follow
scripts/run_amex_simulation.sh as a task brief: it is v8-era and still starts
from v7 / names v8 output paths.

=== STRICT SCOPE ===

Allowed:
- New files under simulation/amex_q1_2026/ only.
- One new tracked baseline: wiki/baseline_v9_GAP_ANALYSIS.md, copied verbatim
  from the simulation report as a separate final commit for later cherry-pick.

Forbidden:
- Any impact_slides/ production source, CSS, schemas, layouts, or tests.
- Existing wiki docs, scripts, config, or CI.
- MAE, visual-similarity percentages, or diff heatmaps as a score.
- Claims based solely on a PR title.
- Refiling accepted/wontfix items: R1, F12+, N2 chip weight, R2 L-bracket arm,
  R3 Centurion seal, or the Annex 33–36 vision-transcription defect as a
  renderer defect.

simulation/ is gitignored. Force-add it with git add -f simulation/ when
committing artifacts. The GNHF branch is the complete artifact archive; never
merge simulation/ into main.

=== METHOD ===

Use Playwright geometry as primary evidence, with a ±4px house tolerance:
measured-vs-expected positions, overlap counts, structure/DOM counts, and
Chart.js scales/chartArea/bar centres. Use PDF/HTML 1920x1080 side-by-side PNGs
as secondary qualitative evidence. Never report MAE or a similarity percentage.

At 1920x1080 the deck stage scale is 1.0. Save re-runnable probes under
simulation/amex_q1_2026/probes/.

=== PROBE CONTRACT (#137) ===

Copy/import scripts/simulation_probe.py into every reusable probe. Do not
reinvent raw slide selectors.

- Address slides ONLY via section.slide[data-slide-number="…"] plus the
  expected data-layout. Never use undocumented zero-based ordinal indices
  (section.slide[index] / nth). Activate only after asserting exactly one
  match and layout equality; otherwise fail the probe.
- Every JSON result row MUST include both slide_number and layout.
- A selector that matches zero elements inside a valid target is inconclusive
  / probe failure — never successful evidence of absence (never count: 0 as a
  pass).
- N9 / Chart.js value labels: read painted plugin models
  chart.$datalabels._labels[*].model().lines (or the helper's equivalent).
  Do NOT judge labels from options.plugins.datalabels / pre-bind config.
- Correct identities for this deck:
    R4  = data-slide-number 12 / data-layout chart_hero_dual
          (NOT ordinal index 11; slide 11 is line_chart)
    R6-C inset slides = data-slide-number 20 and 24
          (PDF pages may still be referred to as p19/p23; do not call the
          HTML slides 19/23)

=== PASS 01: REQUIRED FRESH CURRENT-RENDERER CHECK ===

1. Restore/copy v8 artifacts, render v8 pass 03 with current main, then make
   pass_01 from it.
2. Apply and probe these already-shipped handoff levers:

   a. Slide 17 / PDF p16 (N8/R6-B): Replace the primary-chart band callout
      (from 0, to 7) with measure_rule, meaningful text, and a separate '% CAGR'
      caption. Do not retain a translucent band. Prove rule endpoints/arrow tips
      align to first/last bar centres, pill is centered on the rule, and caption
      is centered beneath it.

   b. Slide 15 / PDF p14 (N6): Set secondary_visual.skin to outlined_boxes on
      the existing reserve-rate support path. Verify unfilled gray-stroked,
      plot-aligned boxes and no duplicated header. If source data violates the
      skin's documented single-row/aligned contract, record that instead of
      changing renderer code.

   c. Slide 28 / PDF p28 (N5/F11): Set per-tile stacked-bar knobs
      bar_percentage: 0.58, category_percentage: 1.0, and fill_tile: true.
      Measure tile/wrap height, bar width, stack height, and bar-to-gap ratio
      against the PDF. Do not pretend an ordinary badge is the missing tall side
      FDIC callout; classify remaining callout, on-stack-total, or tile-chrome
      gaps honestly.

3. Freshly re-probe all 57 v8 geometry contracts on this rendered deck. Port
   the v8 Playwright probes; historical passes are not fresh evidence.
4. Make 1920x1080 HTML/PDF side-by-sides for every affected slide and every
   slide carrying an open/residual finding.

=== ITEMS TO VERIFY, NOT ASSUME ===

- N9: grouped-bar $ labels still land correctly (painted datalabel models,
  not options.plugins.datalabels).
- R2: line-style elbow remains correct where exercised.
- N10: dual_chart paints two separate framed cards.
- R4: dual-metric hero on slide_number 12 / chart_hero_dual is one framed 2:1
  panel (not slide 11 / line_chart).
- F4+: pill comparison has 28px type and measured rail/column dimensions.
- R6-A: Slide 17/PDF p16 pane-title, tick, and datalabel size, colour, weight,
  clipping, and rotation. This may be a renderer B gap; do not add font knobs
  or CSS.
- R6-C: slide_number 20 and 24 inset skin (PDF p19/p23). Establish the PDF
  recipe more carefully if possible; recheck collision geometry. Do not
  restyle CSS on assumption.
- F5: Mention only if this deck proves a theme override cannot tint the default
  chart palette; otherwise record it as not triggered.

=== FOLLOW-UP PASSES ===

Use at most four total comparison passes. Stop after pass_01 if no remaining
divergence is handoff-tunable. In passes 02–04, edit only copied handoff JSON.
Every adjustment must state a hypothesis, geometry result, and side-by-side
result. Stop once remaining items are renderer B gaps, accepted divergences, or
source-transcription defects. Do not manufacture passes.

=== REQUIRED REPORT ===

Write simulation/amex_q1_2026/GAP_ANALYSIS.md and copy it verbatim to
wiki/baseline_v9_GAP_ANALYSIS.md. It must contain:

1. per-pass table: handoff change, geometry pass/fail count, top remaining
   divergences, A/B classification;
2. full geometry-results table: slide, node, measured, expected, delta,
   pass/fail;
3. v8 delta table covering every prior verified/open row and every item above,
   with fresh evidence and status: resolved, partial, still-gap, accepted, or
   not triggered;
4. prioritized future renderer features, each tied to a PDF page and v9
   screenshot/probe path, explicitly marked missing vs weak and A vs B;
5. concise credit for what renderer_v2 does well.

A capability is not resolved merely because a PR exists. An imperfection is not
a renderer gap merely because it is visible.

=== FINAL COMMITS AND STOP ===

Create exactly these two final commits, in this order:
1. sim: store v9 Amex measurement artifacts
   Force-add only simulation/amex_q1_2026/.
2. docs: store v9 Amex simulation baseline
   Add only wiki/baseline_v9_GAP_ANALYSIS.md.

Push is handled by GNHF. If the PDF, Playwright/Chromium, or v8 archive is
inaccessible, record the exact blocker and stop without claiming a baseline.

Stop only when both commits exist; report/artifacts exist; no forbidden path
changed; and the report contains no MAE or similarity score.
EOF

USERPROFILE="$V9_HOME" HOME="$V9_HOME" \
gnhf \
  --agent pi \
  --max-iterations 10 \
  --max-tokens 10000000 \
  --worktree \
  --push \
  --prevent-sleep on \
  --stop-when "A v9 evidence baseline, complete simulation artifacts, and the two required commits exist; no production paths changed." \
  "$PROMPT"
