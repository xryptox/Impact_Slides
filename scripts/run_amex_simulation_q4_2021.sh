#!/usr/bin/env bash
# GNHF Q4 2021 recipe-coverage sim: author a schema-v1 handoff from the
# Q4 2021 Amex earnings PDF using only existing renderer_v3 recipes, render
# strict, and observe which slides the current composition set can replicate.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

PDF="C:/Users/Ag1Le/Downloads/Q4-2021-Earnings-Presentation.pdf"
REAL_HOME="${REAL_HOME:-C:/Users/Ag1Le}"
Q4_HOME="${LOCALAPPDATA:-C:/Users/Ag1Le/AppData/Local}/Temp/gnhf-q4-2021-supergrok"
PI_CLI="C:/Users/Ag1Le/AppData/Roaming/npm/node_modules/@earendil-works/pi-coding-agent/dist/cli.js"
PDF_SHA256="8e113208a6df838861fc06cdbfb82514f01f43c42a21e02005801f8fdf545e21"

[[ -f "$PDF" ]] || { echo "Missing source PDF: $PDF" >&2; exit 1; }
[[ -f "$PI_CLI" ]] || { echo "Missing pi CLI: $PI_CLI" >&2; exit 1; }
ACTUAL_SHA="$(python -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$PDF")"
[[ "$ACTUAL_SHA" == "$PDF_SHA256" ]] || {
  echo "PDF SHA-256 mismatch: got $ACTUAL_SHA want $PDF_SHA256" >&2; exit 1;
}

rm -rf "$Q4_HOME"
mkdir -p "$Q4_HOME/.gnhf"
PI_WRAPPER="$Q4_HOME/pi-supergrok.cmd"
{
  printf '@ECHO off\r\n'
  printf 'SET "USERPROFILE=%s"\r\n' "$(cygpath -w "$REAL_HOME" 2>/dev/null || echo "$REAL_HOME")"
  printf 'SET "HOME=%s"\r\n' "$(cygpath -w "$REAL_HOME" 2>/dev/null || echo "$REAL_HOME")"
  printf 'node "%s" --provider supergrok --model grok-4.6 --thinking high %%*\r\n' \
    "$(cygpath -w "$PI_CLI" 2>/dev/null || echo "$PI_CLI")"
} > "$PI_WRAPPER"

cat > "$Q4_HOME/.gnhf/config.yml" <<EOF
agent: pi
agentPathOverride:
  pi: "$(cygpath -m "$PI_WRAPPER" 2>/dev/null || echo "$PI_WRAPPER")"
maxConsecutiveFailures: 3
preventSleep: true
EOF

if ! (cd "$Q4_HOME" && USERPROFILE="$Q4_HOME" HOME="$Q4_HOME" \
  cmd //c "$(cygpath -w "$PI_WRAPPER" 2>/dev/null || echo "$PI_WRAPPER")" \
  --list-models grok-4.6 2>/dev/null) \
  | grep -q '^supergrok[[:space:]]\+grok-4\.6'; then
  echo "supergrok/grok-4.6 is not reachable through the pinned wrapper." >&2
  echo "Check ~/.pi/agent/auth.json and the pi-supergrok extension." >&2
  exit 1
fi

read -r -d '' PROMPT <<'EOF' || true
Objective: Given the Q4 2021 American Express earnings PDF, author a
schema-v1 renderer_v3 handoff that copies that deck's content as closely
as existing recipes allow, render it strict, and produce a 53-page
PDF↔HTML observation of which slides the current recipe set can replicate
and which it cannot (and why). This is a Companion-mode AUTHORING +
OBSERVATION run. Handoff JSON is in scope. Renderer code, new recipes,
schema changes, and GitHub issues are not.

Read every applicable AGENTS.md before acting. Work only in this
GNHF-created worktree. Preserve repository state. If wiki/AGENT_LEARNINGS.md
exists, read it and apply its capture lessons (identity, paint-ready
charts, 1920x1080 stacked-deck screenshots). Use CONTEXT.md Type (A)
(handoff-only) vs Type (B) (capability/recipe) vocabulary.

Source PDF (read-only):
  C:/Users/Ag1Le/Downloads/Q4-2021-Earnings-Presentation.pdf
  SHA-256 8e113208a6df838861fc06cdbfb82514f01f43c42a21e02005801f8fdf545e21
  53 pages, 720x404 landscape (scale to 1920x1080 for capture).

Do NOT use tests/fixtures/renderer_v3/canonical_amex_handoff_v1.json as
content. That is the Q1 2026 corpus. Use it only as a schema-v1 shape
reference (root keys, layout payloads, number_formats, evidence locators).
Also read tests/fixtures/renderer_v3/minimal_*.json and
impact_slides/renderer_v3/models.py LAYOUT_TYPES / chart types.

=== STRICT SCOPE ===

Allowed:
- New files only below simulation/amex_q4_2021/.
- One new tracked report: wiki/baseline_q4_2021_RECIPE_COVERAGE.md, copied
  verbatim from simulation/amex_q4_2021/GAP_ANALYSIS.md in the docs commit.
- Read-only use of the source PDF, renderer_v3 models/fixtures/docs,
  scripts/simulation_probe.py (identity + paint-ready only), and issue/PR
  history as recipe documentation.

Forbidden:
- Changes to impact_slides/, tests/, scripts/, existing wiki docs, configs,
  CI, GitHub issues/PRs/labels, or any production path.
- New layouts, chart types, painters, theme tokens, or schema fields.
- amex_handoff_mutations.py (v2 Q1 2026 mutations).
- MAE, similarity percentages, pixel-diff scores, or heatmaps.
- Invented numbers. Every metric/category/series value must come from the
  PDF page (PyMuPDF text/tables). If a glyph cannot be read, leave it out
  and mark an extraction residual — do not guess.

simulation/ is gitignored; force-add it only in the artifact commit. Never
merge the simulation artifact commit to main.

=== EXISTING RECIPES (closed set) ===

Layouts (models.LAYOUT_TYPES): opening_cover, section_divider, closing_cover,
single_chart, dual_chart, chart_hero_dual, data_table, annex_table,
grouped_annex_table, period_comparison, comparison_cards, metric_overview,
narrative, legal_notice, process_flow, timeline, decision_tree,
feedback_loop, layered_architecture, data_pipeline, hierarchy,
stakeholder_map, quadrant_matrix, feature_cards, quotation,
evidence_review, risk_opportunity_review, recommendation_case,
state_transition.

Axis chart_type on single_chart / dual_chart / chart_hero_dual: line,
grouped_bar, horizontal_bar, stacked_bar, combo (bar_mode grouped|stacked
+ per-series mark_type bar|line), waterfall, heatmap.

single_chart optional support: support_table, outlined_support, metric_strip.
dual_chart = exactly two charts. chart_hero_dual = chart + hero KPIs +
optional support. No pie, donut, treemap, map, or 3+ chart canvas.

Pick the closest legal composition per page. Do not invent a layout name.

=== AUTHOR ===

Write simulation/amex_q4_2021/handoff_v1.json as a complete schema-v1 deck:

- meta.handoff_schema_version = 1
- sections covering earnings / appendix / legal (add more only if needed)
- number_formats actually referenced (usd_0/usd_1/pct_0/pct_1/num_0/num_1
  as in the Q1 corpus are a fine starting set; add only what you use)
- evidence_registry: one id per PDF page, semantic id
  amex-q4-2021-pNN (01..53), source_name
  "American Express Q4 2021 Earnings Presentation", locator.kind pdf_page,
  sha256 the hash above, page N, index N-1
- slides 1..53, slide_number matching physical PDF page N, evidence_ids
  pointing at that page. HTML slide N maps to PyMuPDF index N-1.

Page titles (largest type; use these unless the PDF clearly differs):
  1 opening cover — American Express Earnings Conference Call Q4'21,
    January 25, 2022
  2 Summary Financial Performance
  3 Total Network Volumes Growth
  4 Billed Business (G&S vs T&E)
  5 Goods & Services Billed Business (Online vs Offline)
  6 Global Consumer Billed Business
  7 Global Commercial Billed Business
  8 Billed Business T&E Growth
  9 Billed Business Growth by Region
  10 Worldwide Total Loans and Card Member Receivables
  11 Card Member Credit Metrics
  12 Total Provision
  13 Total Reserves
  14 Revenue Performance
  15 Discount Revenue
  16 Net Card Fees
  17 Net Interest Income
  18 Total Revenue Net of Interest Expense
  19 Expense Performance
  20 Marketing Investments and New Cards Acquired
  21 Capital
  22 The Growth Plan
  23 Appendix (section divider)
  24 Q4'21 Network Volumes Growth by Customer Type
  25 Global Consumer G&S Growth
  26 Travel & Entertainment Billed Business
  27 Worldwide Total Loans and Card Member Receivables Mix
  28 Delinquent and Financial Relief Program Balances
  29 Global Corporate Payments Card Member Credit Metrics
  30 Credit Reserve Build Macroeconomic Assumptions
  31 Funding Mix
  32 FX Impact on Network Volumes and Revenue Growth
  33-34 Additional Commentary – Variance Analysis
  35 Environmental, Social and Governance (ESG) Strategy
  36 2021 ESG Highlights
  37-38 Annex 1 Network Volumes – Reported & FX-Adjusted
  39 Annex 2 Discount Revenue – Reported & FX-Adjusted
  40 Annex 3 Net Card Fees – Reported & FX-Adjusted
  41 Annex 4 Net Interest Income – Reported & FX-Adjusted
  42 Annex 5 Consolidated Net Interest Yield on Average Card Member Loans
  43-44 Annex 6 Revenues Net of Interest Expense
  45 Annex 7 Troubled Debt Restructurings (TDR) Balance
  46 Annex 8 GCP Card Member Receivables Net Write-Off rates
  47-52 Forward Looking Statements
  53 closing cover (blank/logo page — still emit closing_cover)

Match titles, categories, series names, numbers, footnotes/disclosures, and
pane headings from each PDF page. Prefer dual_chart when the PDF is two
plots; period_comparison / data_table for summary grids; annex_table for
annex matrices; metric_overview for guidance; legal_notice for forward-
looking parts; hierarchy for the ESG org chart; narrative for commentary
and ESG highlights. Mix pies/donuts (likely s27) have no recipe — use the
least-lossy legal stand-in (stacked_bar or metric_overview) and classify
Type (B).

Validate as you go (python -c using validate_handoff, or render --out a
scratch dir). Iterate the handoff until a strict render is clean, or until
the remaining errors are recipe/schema ceilings you cannot express. Record
those typed errors verbatim as Type (B) blockers. Never hand-edit published
HTML.

=== RENDER ===

Render exactly once for publication, strict, from the authored handoff:
  python -m impact_slides.renderer_v3 \
    --handoff simulation/amex_q4_2021/handoff_v1.json \
    --out simulation/amex_q4_2021/passes/pass_01/renderer_v3_out
Exit 0 with run_meta status clean is required. Record renderer version,
repository commit, and run_meta artifact hashes. If strict still fails after
handoff iteration, record the typed error plus every diagnostic line
verbatim, render again with --no-strict into renderer_v3_out_degraded, label
every downstream artifact and report section DEGRADED, and name the
degraded surfaces from run_meta events.

=== IDENTITY / CAPTURE CONTRACT ===

renderer_v3 publishes presentation.html as a stacked scroll deck: all 53
<section class="slide" data-slide-number data-layout> elements live inside
.deck-stage, all are visible, and there is no active-class or hash
navigation. Capture with viewport exactly 1920x1080 and deviceScaleFactor 1.

HTML slide N maps to PyMuPDF index N-1 and physical PDF page N. Before any
capture assert: 53 unique data-slide-number values 1..53, each slide's
data-layout matches the authored layout_type for that slide number, and the
PDF has 53 pages. Every artifact and JSON row states slide number,
layout_type, PDF index, and physical page.

Probe discipline (import scripts/simulation_probe.py):
- Before every chart-slide screenshot call
  wait_for_paint_ready_charts(page, slide_number, layout_type); it also
  enforces identity (unique data-slide-number + matching data-layout).
- Zero matches, wrong layouts, missing Chart instances, zero-size canvases,
  degenerate chartArea, or missing dataset geometry are failures. Readiness
  must hold across one animation frame. No nth selectors, no fixed sleeps.
- Do NOT call painted_datalabel_lines (v2 plugin state).
- Do NOT run DESIGN_LEDGER_FURNITURE / DESIGN_LEDGER_*_SLIDES maps — those
  are Q1 2026 Amex slide numbers and will false-fail this deck.
- Optional: measured_tick_styles on chart slides as a generic note (not a
  stop condition).
- Capture by scrolling the target section into view and taking an element
  screenshot of the section: exactly 1920x1080 PNG per slide.
- Capture console errors and run_meta diagnostics with slide identity.
- Capture the primary JS-on Chart.js surface, not the noscript SVG fallback.

=== FULL 53-PAGE COMPARISON ===

Rasterize all 53 PDF pages directly to exactly 1920x1080 with PyMuPDF.
Screenshot all 53 HTML slides at exactly 1920x1080 after identity and
paint-readiness. Create full-resolution side-by-sides (3840x1080, PDF left /
renderer_v3 right) without downscaling either half, a labeled 53-slide
contact sheet, and comparison_manifest.json proving every PDF/HTML/SBS
artifact exists with its slide identity, chosen layout_type, and
classification.

Write a 53-row qualitative ledger. Each row links its SBS and classifies
exactly one of: faithful reproduction, accepted v3 design divergence,
candidate renderer defect or capability gap (Type B), corpus/extraction
residual (Type A — recipe could hold it, handoff missed it), source/PDF
artifact, or capture failure. Explain observations qualitatively; do not
score images. Name the recipe used and, for failures, the missing recipe
or the schema ceiling (pie, 3+ panes, freeform callouts, etc.).

=== RESIDUAL TRIAGE ===

After the 53-row ledger, split:
1. Replicated with existing recipes (faithful + accepted Boardroom chrome).
2. Type (A) handoff misses — would likely replicate if re-authored.
3. Type (B) recipe/capability gaps — no adequate existing composition.
4. Source/PDF artifact or capture failure.

Only list a residual when fresh SBS/probe evidence proves it. Give location,
impact, likely ownership (handoff vs renderer recipe), and the smallest
next verification. Do not design or implement the fix and do not create
tickets.

Add a short section on which recipes this deck actually exercised and which
PDF patterns had no recipe.

=== REPORT / COMMITS / STOP ===

Write simulation/amex_q4_2021/GAP_ANALYSIS.md and copy it byte-for-byte to
wiki/baseline_q4_2021_RECIPE_COVERAGE.md. Include renderer commit and
version, PDF identity (path + sha256 + 53 pages), handoff path, render
outcome (clean or DEGRADED with diagnostics), scope audit, mapping
assertion, capture contract, 53-row qualitative ledger, residual triage,
recipe coverage summary, diagnostics, and artifact links. Do not embed
PNGs in the report.

Create exactly two commits in order:
1. `sim: store Q4 2021 renderer_v3 recipe-coverage artifacts`
   Force-add only simulation/amex_q4_2021/.
2. `docs: store Q4 2021 renderer_v3 recipe-coverage report`
   Add only wiki/baseline_q4_2021_RECIPE_COVERAGE.md.

Before stopping prove:
- both commits exist and only allowed paths changed;
- report copies are byte-identical;
- handoff_v1.json has 53 slides and validates (or degraded path is labeled);
- all 53 PDF/HTML/SBS rows and files exist at exact 1920x1080 halves;
- comparison_manifest.json has a row for every slide with layout_type + class;
- the strict render exited 0 clean, or the degraded path is fully labeled;
- no MAE/similarity/pixel-diff scoring exists;
- no production/test/script/config path changed.

Stop only when all proofs pass, or stop with a precise blocker and no false
success. Push is handled by GNHF.
EOF

USERPROFILE="$Q4_HOME" HOME="$Q4_HOME" \
gnhf \
  --agent pi \
  --max-iterations 15 \
  --max-tokens 10000000 \
  --worktree \
  --push \
  --prevent-sleep on \
  --stop-when "A Q4 2021 renderer_v3 recipe-coverage baseline exists: authored 53-slide schema-v1 handoff, strict (or fully labeled degraded) render, all 53 PDF/HTML side-by-sides, qualitative ledger classifying replicated vs Type A vs Type B recipe gaps, residual triage, and exactly two allowed commits; no production paths changed and no image scoring was used." \
  "$PROMPT"
