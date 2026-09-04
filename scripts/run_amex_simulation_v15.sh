#!/usr/bin/env bash
# GNHF v15: 44-page PDF vs renderer_v3 SBS with DP-6 design ledger,
# validating the post-v14 ticket set (#254 s24 placement-above groups,
# #255 series/ticks/FHR/Leap Year/s38 preamble, #256 hide_header chrome
# probe, #257 legal title+type, #258 s17 pane headings, #259 s6 axis
# titles, #260 s12/s15/s21 stack_segments).
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

PDF="C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf"
REAL_HOME="${REAL_HOME:-C:/Users/Ag1Le}"
V15_HOME="${LOCALAPPDATA:-C:/Users/Ag1Le/AppData/Local}/Temp/gnhf-v15-supergrok"
PI_CLI="C:/Users/Ag1Le/AppData/Roaming/npm/node_modules/@earendil-works/pi-coding-agent/dist/cli.js"
V14_REPORT_COMMIT="b6d8ed8"

[[ -f "$PDF" ]] || { echo "Missing source PDF: $PDF" >&2; exit 1; }
[[ -f "$PI_CLI" ]] || { echo "Missing pi CLI: $PI_CLI" >&2; exit 1; }
[[ -f tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json ]] || {
  echo "Missing canonical schema-v1 Amex corpus fixture." >&2; exit 1;
}
git cat-file -e "$V14_REPORT_COMMIT" 2>/dev/null || {
  echo "Missing v14 report commit: $V14_REPORT_COMMIT" >&2; exit 1;
}

rm -rf "$V15_HOME"
mkdir -p "$V15_HOME/.gnhf"
PI_WRAPPER="$V15_HOME/pi-supergrok.cmd"
{
  printf '@ECHO off\r\n'
  printf 'SET "USERPROFILE=%s"\r\n' "$(cygpath -w "$REAL_HOME" 2>/dev/null || echo "$REAL_HOME")"
  printf 'SET "HOME=%s"\r\n' "$(cygpath -w "$REAL_HOME" 2>/dev/null || echo "$REAL_HOME")"
  printf 'node "%s" --provider supergrok --model grok-4.5 --thinking high %%*\r\n' \
    "$(cygpath -w "$PI_CLI" 2>/dev/null || echo "$PI_CLI")"
} > "$PI_WRAPPER"

cat > "$V15_HOME/.gnhf/config.yml" <<EOF
agent: pi
agentPathOverride:
  pi: "$(cygpath -m "$PI_WRAPPER" 2>/dev/null || echo "$PI_WRAPPER")"
maxConsecutiveFailures: 3
preventSleep: true
EOF

if ! (cd "$V15_HOME" && USERPROFILE="$V15_HOME" HOME="$V15_HOME" \
  cmd //c "$(cygpath -w "$PI_WRAPPER" 2>/dev/null || echo "$PI_WRAPPER")" \
  --list-models grok-4.5 2>/dev/null) \
  | grep -q '^supergrok[[:space:]]\+grok-4\.5'; then
  echo "supergrok/grok-4.5 is not reachable through the pinned wrapper." >&2
  echo "Check ~/.pi/agent/auth.json and the pi-supergrok extension." >&2
  exit 1
fi

read -r -d '' PROMPT <<'EOF' || true
Objective: Produce the v15 Amex Q1 2026 observation baseline: a complete
44-page side-by-side comparison of the source PDF deck against HTML slides
rendered by renderer_v3 (schema-v1) from the canonical D314 corpus, with
both the qualitative content ledger and the DP-6 design ledger. This run
re-validates the deck after the post-v14 ticket set: #254 s24
placement-above groups + outlined %-of-total, #255 s4/s19 series swap +
PDF ticks + s8 FHR step + Leap Year/G&S–T&E facts + s38 preamble, #256
hide_header + hairline body support-chrome probe, #257 legal_notice
repeating part-1 title + 56/21 type, #258 s17 dated pane headings +
subtitle, #259 s6 Anniversary Month + retention axis titles, #260
stack_segments show on s12/s15/s21. This is a Companion-mode SIMULATION /
OBSERVATION run, not implementation. Do not implement fixes or file issues.

Read every applicable AGENTS.md before acting. Work only in this GNHF-created
worktree. Preserve repository state. If wiki/AGENT_LEARNINGS.md exists, read
it and apply its capture lessons.

Source PDF (read-only):
  C:/Users/Ag1Le/Downloads/Q1-2026-Earnings-Presentation.pdf

Canonical renderer_v3 input (read-only; already incorporates the v2-era
authoring corrections and the #254–#260 corpus updates — do NOT run
amex_handoff_mutations.py on it):
  tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json

Prior evidence:
  v14 report (never merged to main; read via:
    git show b6d8ed8:wiki/baseline_v14_GAP_ANALYSIS.md)
  wiki/SPEC_renderer_v3_pdf_design_parity.md (DP-1..DP-7)
  scripts/simulation_probe.py (identity, paint-ready, design-ledger helpers)

=== STRICT SCOPE ===

Allowed:
- New files only below simulation/amex_q1_2026/.
- One new tracked report: wiki/baseline_v15_GAP_ANALYSIS.md, copied verbatim
  from simulation/amex_q1_2026/GAP_ANALYSIS.md in the final docs commit.
- Read-only use of source PDF, canonical corpus fixture, current tests,
  scripts/simulation_probe.py, the v14 report via git show, and issue/PR
  history.

Forbidden:
- Changes to impact_slides/, tests/, scripts/, existing wiki docs, configs,
  CI, GitHub issues/PRs/labels, or any production path.
- Renderer fixes, corpus/handoff edits, or a mutation pass.
- MAE, similarity percentages, pixel-diff scores, or heatmaps.
- Claims based only on PR titles, old screenshots, fixed sleeps, ordinal slide
  selectors, zero-match probes, unpainted Chart.js geometry, or SVG
  presentation attributes without computed style.

simulation/ is gitignored; force-add it only in the artifact commit. Never
merge the simulation artifact commit to main.

=== RENDER ===

Render exactly once, strict, from the committed corpus:
  python -m impact_slides.renderer_v3 \
    --handoff tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json \
    --out simulation/amex_q1_2026/passes/pass_01/renderer_v3_out
Exit 0 with run_meta status clean is required. Record renderer version,
repository commit, and the run_meta artifact hashes in the report. If the
strict render fails, record the typed error plus every diagnostic line
verbatim, render again with --no-strict into renderer_v3_out_degraded, label
every downstream artifact and report section DEGRADED, and name the degraded
surfaces from run_meta events. Never hand-edit published artifacts.

=== IDENTITY / CAPTURE CONTRACT ===

renderer_v3 publishes presentation.html as a stacked scroll deck: all 44
<section class="slide" data-slide-number data-layout> elements live inside
.deck-stage, all are visible, and there is no active-class or hash
navigation. A resize-fit script scales slides by min(innerWidth/1920,
innerHeight/1080), so capture with a viewport of exactly 1920x1080 and
deviceScaleFactor 1 to keep scale 1 and exact pixel sizes.

HTML slide N maps to PyMuPDF index N-1 and physical PDF page N. Before any
capture assert: 44 unique data-slide-number values 1..44, each slide's
data-layout matches the corpus layout_type for that slide number, and the PDF
has 44 pages. Every artifact and JSON row states slide number, layout_type,
PDF index, and physical page.

Probe discipline (import scripts/simulation_probe.py):
- Before every chart-slide screenshot call
  wait_for_paint_ready_charts(page, slide_number, layout_type); it also
  enforces identity (unique data-slide-number + matching data-layout).
- Zero matches, wrong layouts, missing Chart instances, zero-size canvases,
  degenerate chartArea, or missing dataset geometry are failures. Readiness
  must hold across one animation frame. No nth selectors, no fixed sleeps.
- Do NOT call painted_datalabel_lines on the v3 deck: it targets the
  chartjs-plugin-datalabels state renderer_v2 used; v3 paints labels through
  its own context_labels/annotations/measurements chrome.
- Capture slides by scrolling the target section into view and taking an
  element screenshot of the section: exactly 1920x1080 PNG per slide.
- Capture console errors and run_meta diagnostics with slide identity.
- v3 decks also carry a no-JS SVG fallback; capture the primary JS-on
  Chart.js surface for the comparison.

=== DP-6 DESIGN LEDGER ===

After paint-ready, for every chart slide call measured_tick_styles(page,
slide_number, layout_type). That helper reads computed font-size/font-weight
on overlay tick <text> (not presentation attributes) and fails if any tick
is below 20px or weight 600, or if zero ticks match.

For every entry in DESIGN_LEDGER_FURNITURE call furniture_presence with that
selector and expected_text. Zero matches or missing text are failures, never
a green row.

Also run the #249/#256 DP-6 extension probes (import the DESIGN_LEDGER_* maps and
helpers from simulation_probe.py; zero matches / ProbeError = failure):
- measured_stub_ratio on DESIGN_LEDGER_STUB_RATIO_SLIDES (s3/s16/s31-37;
  stub share <= 0.45) — held from #246
- measured_support_chrome on DESIGN_LEDGER_SUPPORT_CHROME_SLIDES (s4/s19;
  hide_header + hairline body cells; missing body frame fails; painted
  .head still asserts navy band + hairlines) — validates #256 (v14 P-247-head
  should now pass)
- measured_series_palette on DESIGN_LEDGER_PALETTE_SLIDES (s24/s28; no
  #0A7D55 series fill; require_sky_blue per map)
- measured_metric_value_styles on DESIGN_LEDGER_METRIC_FLOOR_SLIDES (s8/s12;
  value font-size >= 40px)
- measured_bar_occupancy on DESIGN_LEDGER_BAR_OCCUPANCY_SLIDES (s28;
  bar width / category pitch >= 0.5)

Record one design-ledger object per slide in comparison_manifest.json:
  slide_number, layout, tick_count, min_font_size_px, min_font_weight,
  furniture rows (selector, expected_text, count, ok), #249/#256 extension rows
  present for the slides above (stub_ratio / support_chrome / palette /
  metric_floor / bar_occupancy), and overall ok.
Non-chart slides without an extension target record design_ledger:
  {ok: true, ticks: null, furniture: []}.
A ProbeError is a capture/design failure for that slide — do not invent a
green row. Classification may add "design-parity verified" only when the
slide's design ledger is ok.

=== FULL 44-PAGE COMPARISON ===

Rasterize all 44 PDF pages directly to exactly 1920x1080 with PyMuPDF.
Screenshot all 44 HTML slides at exactly 1920x1080 after the identity,
paint-readiness, and design-ledger checks. Create full-resolution
side-by-sides (3840x1080, PDF left / renderer_v3 right) without downscaling
either half, a labeled 44-slide contact sheet, and comparison_manifest.json
proving every PDF/HTML/SBS artifact exists with its slide identity and
design-ledger row.

Write a 44-row qualitative ledger. Each row links its SBS and classifies the
result as exactly one of: faithful reproduction, accepted v3 design
divergence, candidate renderer defect or capability gap, corpus/extraction
residual, source/PDF artifact, or capture failure. Explain observations
qualitatively; do not score images. Note design-parity verified when the
design ledger is green.

=== V14 -> V15 DELTA ===

Read the v14 report with `git show b6d8ed8:wiki/baseline_v14_GAP_ANALYSIS.md`
(it was never merged to main). For every residual it names, state whether the
current render resolves it, preserves it, or replaces it with a different
divergence, citing the v15 SBS and design-ledger evidence. Explicitly cover
the post-v14 ticket surfaces:
- #254 s24: under-axis stack gone (at most one category-tick row);
  Commercial / ICS group chrome above the bars; %-of-total in outlined
  boxes under the plot (not in-bar); singleton UCS group gone.
- #255 s4/s19 series identity (dashed upper Reported on s4; navy FX-adj
  ends at 9% s4 / 10% s19); authored ticks 0/5/10/15 (s4/s5/s9/s11/s19)
  and 0/5/10/15/20/25 on s10; s8 FHR+THC step 40/40/40/50/50; Leap Year
  + G&S/T&E facts on s5/s9/s10/s11; s38 forward-looking preamble before
  the risk lists.
- #256 s4/s19 support_chrome probe: hide_header + hairline body (no
  required navy period .head band) — v14 P-247-head should flip green.
- #257 s38–43: part-1 legal title repeats on every part (no
  "— continued"); type scale 56/21 if it still fits; v14 R-D packing.
- #258 s17: dated pane headings + subtitle; series_identity pane_title
  (no leftover 1-series legends).
- #259 s6: right-pane Anniversary Month category title + retention-rate
  value-axis title; left-pane prior-year subtitle if authored.
- #260 s12/s15/s21: on-stack segment labels visible (not just column
  totals); s28 already showed segments in v14.
- any v14 residual outside those tickets (typography, furniture, corpus).
Add a short section on what renderer_v3 now does well.

=== RESIDUAL TRIAGE ===

For every visible mismatch in the 44-row ledger distinguish:
1. renderer_v3 defect/capability gap;
2. corpus/extraction/content residual;
3. source/PDF artifact or accepted divergence;
4. screenshot/probe/design-ledger failure.

Only list a candidate residual when fresh evidence proves it. Give location,
impact, likely ownership, and the smallest next verification. Do not design
or implement the fix and do not create tickets.

=== REPORT / COMMITS / STOP ===

Write simulation/amex_q1_2026/GAP_ANALYSIS.md and copy it byte-for-byte to
wiki/baseline_v15_GAP_ANALYSIS.md. Include renderer commit and version,
source identities, render outcome (clean or DEGRADED with diagnostics), scope
audit, mapping assertion, capture contract, design ledger, 44-row qualitative
ledger, v14->v15 delta, residual triage, diagnostics, and artifact links.

Create exactly two commits in order:
1. `sim: store v15 renderer_v3 Amex full comparison artifacts`
   Force-add only simulation/amex_q1_2026/.
2. `docs: store v15 renderer_v3 complete-deck comparison`
   Add only wiki/baseline_v15_GAP_ANALYSIS.md.

Before stopping prove:
- both commits exist and only allowed paths changed;
- report copies are byte-identical;
- all 44 PDF/HTML/SBS rows and files exist at exact 1920x1080 halves;
- comparison_manifest.json has a design-ledger row for every slide;
- the strict render exited 0 clean, or the degraded path is fully labeled;
- no MAE/similarity/pixel-diff scoring exists;
- no production/test/script/config path changed.

Stop only when all proofs pass, or stop with a precise blocker and no false
success. Push is handled by GNHF.
EOF

USERPROFILE="$V15_HOME" HOME="$V15_HOME" \
gnhf \
  --agent pi \
  --max-iterations 10 \
  --max-tokens 10000000 \
  --worktree \
  --push \
  --prevent-sleep on \
  --stop-when "A v15 renderer_v3 observation baseline with all 44 PDF/HTML side-by-sides, a qualitative ledger, a DP-6 design ledger, v14->v15 delta covering #254-#260, residual triage, and exactly two allowed commits exists; no production paths changed and no image scoring was used." \
  "$PROMPT"
