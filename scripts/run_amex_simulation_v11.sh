#!/usr/bin/env bash
# GNHF v11: observe current-main Amex fidelity after tickets #136-#159.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

PDF="C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf"
REAL_HOME="${REAL_HOME:-C:/Users/Ag1Le}"
V11_HOME="${LOCALAPPDATA:-C:/Users/Ag1Le/AppData/Local}/Temp/gnhf-v11-grok-latest"
PI_CLI="C:/Users/Ag1Le/AppData/Roaming/npm/node_modules/@earendil-works/pi-coding-agent/dist/cli.js"

[[ -f "$PDF" ]] || { echo "Missing source PDF: $PDF" >&2; exit 1; }
[[ -f "$PI_CLI" ]] || { echo "Missing pi CLI: $PI_CLI" >&2; exit 1; }
[[ -f tests/fixtures/renderer_v2/amex_v10_44_slide_handoff.json ]] || {
  echo "Missing canonical 44-slide handoff fixture." >&2; exit 1;
}

rm -rf "$V11_HOME"
mkdir -p "$V11_HOME/.gnhf"
PI_WRAPPER="$V11_HOME/pi-grok-latest.cmd"
{
  printf '@ECHO off\r\n'
  printf 'SET "USERPROFILE=%s"\r\n' "$(cygpath -w "$REAL_HOME" 2>/dev/null || echo "$REAL_HOME")"
  printf 'SET "HOME=%s"\r\n' "$(cygpath -w "$REAL_HOME" 2>/dev/null || echo "$REAL_HOME")"
  printf 'node "%s" --provider openrouter --model x-ai/grok-latest --thinking high %%*\r\n' \
    "$(cygpath -w "$PI_CLI" 2>/dev/null || echo "$PI_CLI")"
} > "$PI_WRAPPER"

cat > "$V11_HOME/.gnhf/config.yml" <<EOF
agent: pi
agentPathOverride:
  pi: "$(cygpath -m "$PI_WRAPPER" 2>/dev/null || echo "$PI_WRAPPER")"
maxConsecutiveFailures: 3
preventSleep: true
EOF

if ! (cd "$V11_HOME" && USERPROFILE="$V11_HOME" HOME="$V11_HOME" \
  cmd //c "$(cygpath -w "$PI_WRAPPER" 2>/dev/null || echo "$PI_WRAPPER")" \
  --list-models x-ai/grok-latest 2>/dev/null) \
  | grep -q '^openrouter[[:space:]]\+.*x-ai/grok-latest'; then
  echo "openrouter/x-ai/grok-latest is unavailable through the pinned wrapper." >&2
  exit 1
fi

read -r -d '' PROMPT <<'EOF' || true
Objective: Produce the evidence-led v11 Amex Q1 2026 fidelity baseline on
current main after all renderer and handoff tickets #136 through #159 shipped.
This is a Companion-mode SIMULATION / OBSERVATION run, not implementation.
Determine what is demonstrably solved across the complete 44-page PDF deck and
what still needs further work.

Read every applicable AGENTS.md before acting. Work only in this GNHF-created
worktree. Preserve repository state. Do not implement fixes or file issues.

Source PDF (read-only):
  C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf

Canonical current-main handoff source:
  tests/fixtures/renderer_v2/amex_v10_44_slide_handoff.json

Prior evidence:
  wiki/baseline_v10_GAP_ANALYSIS.md when available from
  origin/gnhf/objective-produce-an-74065a
  wiki/baseline_v10_VERIFIER_CORRECTION_146.md

=== STRICT SCOPE ===

Allowed:
- New files only below simulation/amex_q1_2026/.
- One new tracked report: wiki/baseline_v11_GAP_ANALYSIS.md, copied verbatim
  from simulation/amex_q1_2026/GAP_ANALYSIS.md in the final docs commit.
- Read-only use of source PDF, current tests, scripts/simulation_probe.py,
  scripts/amex_handoff_mutations.py, prior baselines, and issue/PR history.

Forbidden:
- Changes to impact_slides/, tests/, scripts/, existing wiki docs, configs, CI,
  GitHub issues/PRs/labels, or any production path.
- Renderer fixes, speculative handoff tuning, or a pass_02.
- MAE, similarity percentages, pixel-diff scores, or heatmaps.
- Claims based only on PR titles, old screenshots, fixed sleeps, ordinal slide
  selectors, zero-match probes, or unpainted Chart.js options.

simulation/ is gitignored; force-add it only in the artifact commit. Never
merge the simulation artifact commit to main.

=== HANDOFF ===

1. Copy the canonical fixture unchanged to:
   simulation/amex_q1_2026/passes/pass_01/handoff.pre_mutations.json
2. Produce passes/pass_01/handoff.json only by running:
   python scripts/amex_handoff_mutations.py \
     passes/pass_01/handoff.pre_mutations.json \
     -o passes/pass_01/handoff.json
   using full paths under simulation/amex_q1_2026/.
3. Record the exact changed slide numbers. Do not hand-edit the result.
4. Assert that the resulting handoff has exactly 44 unique slides numbered
   1..44 and retains current contracts for slide 12 pane headings, slide 17
   typography.mode=auto in both panes, slide 18 driver_card + boxed_labels,
   and slide 26 Q1'26 matrix orientation.

=== IDENTITY / CAPTURE CONTRACT (#137, #146) ===

HTML slide N maps to PyMuPDF index N-1 and physical PDF page N. Assert the
mapping from handoff titles, 44 unique data-slide-number values, and PDF page
count before capturing evidence. Every artifact and JSON row states slide
number, expected data-layout, PDF index, and physical page.

All reusable Playwright probes must import scripts/simulation_probe.py:
- activate_slide(page, slide_number, expected_layout) only;
- wait_for_paint_ready_charts before every chart screenshot;
- painted_datalabel_lines for Chart.js datalabel evidence.
Zero matches, wrong layouts, missing painted models, zero-size canvases,
degenerate chartArea, or missing dataset geometry are failures. Readiness must
hold across one animation frame. Do not use nth selectors or fixed sleeps.
Capture console and run_meta diagnostics with slide identity.

=== FULL 44-PAGE COMPARISON ===

Render one current-main pass. Rasterize all 44 PDF pages directly to exactly
1920x1080. Screenshot all 44 matching HTML slides at exactly 1920x1080 after
identity and paint-readiness checks. Create full-resolution side-by-sides
without downscaling either half, a labeled 44-slide contact sheet, and
comparison_manifest.json proving every PDF/HTML/SBS artifact exists.

Write a 44-row qualitative ledger. Each row links its SBS and classifies the
result as one of: solved-ticket verification, no material new finding,
accepted divergence, source/content residual, or candidate renderer residual.
Explain observations qualitatively; do not score images.

=== CLOSED-TICKET REVALIDATION (#136-#159) ===

Create a scorecard row for every ticket #136 through #159. Each row must name
the actual current input, DOM/geometry/content assertion, runtime(s), evidence
path, result (pass/fail/partial/not-applicable), and any residual. A closed
issue is not proof. At minimum exercise:

- #136/#149 slide 15: outlined support-cell centres align to bars <=12px and
  the label lane does not overlap the first value cell, in Chart.js and SVG.
- #137/#146: identity-safe and paint-ready capture contract on every chart;
  explicitly recheck formerly blank slides 9, 12, and 27.
- #138/#158 slide 28: one shared-column FDIC callout, independent stack totals,
  pane subtitles, no pseudo top_total/duplicate badge, Chart.js and SVG.
- #139/#150 slide 17: semantic pane titles plus auto typography. Record chosen
  sizes, adaptations, suppression, clipping, and Chart.js/SVG consistency.
- #140 slide 3: fixed five-row pill-board PDF geometry; prove slide 20 and
  slide 24 inset compositions do not match its selector.
- #147 slide 12: explicit left/right headings and subtitles, exactly one
  semantic title per pane and no duplicate internal chart title.
- #148 slides 13-14: vertical bars and correct pane semantics/order.
- #151 slide 18: Premium Lending chart_hero_dual, five boxed YoY labels and
  four-row driver card including Margin 5%, without the synthetic combo line.
- #152: ordinary plot gridlines absent by default in Chart.js and SVG while
  axes, support borders, and mixed-sign semantic zero lines remain.
- #153 slide 26: visible Q1'26 context and source matrix orientation.
- #154 slide 24: six bars, three visible semantic group brackets in settled
  Chart.js plus SVG, aligned support row, exact "$486B Total Network Volumes",
  and FX-adjusted note.
- #155 slide 21: stacked Dividends/Share Repurchases, shares line 702->682,
  stack totals, aligned ROE 35/34/36/36/34/35%, and right-side KPIs.
- #156 slide 27: two paint-ready panes, all three scenarios, Q1'25-Q1'28,
  SAAR note, and E0026 source citation.
- #157 slides 33-37: complete semantic annex matrices, correct units, and FX
  footnotes.
- #159 slide 32: two peer grouped annex tables with deck-unique heading IDs.

Use focused probes for these assertions and preserve their JSON. Run JS-off/SVG
checks where the ticket changes SVG or claims runtime parity. Also run the
existing focused ticket tests as supporting evidence, but never substitute a
green unit test for rendered evidence.

=== RESIDUAL TRIAGE ===

For every visible mismatch in the 44-row ledger distinguish:
1. renderer defect/capability gap;
2. handoff/extraction/content error;
3. source/PDF artifact or accepted divergence;
4. screenshot/probe failure.

Only list a candidate residual when fresh evidence proves it. Give location,
impact, likely ownership, and the smallest next verification. Do not design or
implement the fix and do not create tickets. Include separate sections:
- solved since v10;
- still-open evidence-backed renderer residuals;
- still-open handoff/source residuals;
- accepted/non-actionable differences;
- what renderer_v2 now does well.

=== REPORT / COMMITS / STOP ===

Write simulation/amex_q1_2026/GAP_ANALYSIS.md and copy it byte-for-byte to
wiki/baseline_v11_GAP_ANALYSIS.md. Include renderer commit, source identities,
mutation diff, scope audit, mapping assertion, ticket scorecard #136-#159,
44-row ledger, v10->v11 delta, residual triage, diagnostics, and artifact links.

Create exactly two commits in order:
1. `sim: store v11 Amex full comparison artifacts`
   Force-add only simulation/amex_q1_2026/.
2. `docs: store v11 Amex complete-deck revalidation`
   Add only wiki/baseline_v11_GAP_ANALYSIS.md.

Before stopping prove:
- both commits exist and only allowed paths changed;
- report copies are byte-identical;
- all 44 PDF/HTML/SBS rows and files exist;
- every #136-#159 scorecard row has fresh evidence;
- no MAE/similarity/pixel-diff scoring exists;
- no production/test/script/config path changed.

Stop only when all proofs pass, or stop with a precise blocker and no false
success. Push is handled by GNHF.
EOF

USERPROFILE="$V11_HOME" HOME="$V11_HOME" \
gnhf \
  --agent pi \
  --max-iterations 10 \
  --max-tokens 10000000 \
  --worktree \
  --push \
  --prevent-sleep on \
  --stop-when "A v11 observation baseline with all 44 PDF/HTML comparisons, fresh #136-#159 scorecards, residual triage, and exactly two allowed commits exists; no production paths changed and no image scoring was used." \
  "$PROMPT"
