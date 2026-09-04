#!/usr/bin/env bash
# GNHF Q4 2021 Type B re-author: rebase gnhf/objective-given-the-d60385 onto
# origin/main (recipes from #283/#284/#286/#287/#288), re-author the 11
# unblocked Type B slides, strict-render, recapture 53 SBS, refresh ledger.
# User triggers this script. Does not --push (wincredman).
set -euo pipefail

REAL_HOME="${REAL_HOME:-C:/Users/Ag1Le}"
Q4_HOME="${LOCALAPPDATA:-C:/Users/Ag1Le/AppData/Local}/Temp/gnhf-q4-2021-typeb-supergrok"
PI_CLI="C:/Users/Ag1Le/AppData/Roaming/npm/node_modules/@earendil-works/pi-coding-agent/dist/cli.js"
PDF="C:/Users/Ag1Le/Downloads/Q4-2021-Earnings-Presentation.pdf"
PDF_SHA256="8e113208a6df838861fc06cdbfb82514f01f43c42a21e02005801f8fdf545e21"
BRANCH="gnhf/objective-given-the-d60385"

[[ -f "$PDF" ]] || { echo "Missing source PDF: $PDF" >&2; exit 1; }
[[ -f "$PI_CLI" ]] || { echo "Missing pi CLI: $PI_CLI" >&2; exit 1; }
ACTUAL_SHA="$(python -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$PDF")"
[[ "$ACTUAL_SHA" == "$PDF_SHA256" ]] || {
  echo "PDF SHA-256 mismatch: got $ACTUAL_SHA want $PDF_SHA256" >&2; exit 1;
}

# Resolve the existing Q4 worktree (do not mint a new GNHF worktree).
START="$(git rev-parse --show-toplevel)"
cd "$START"
WT="$(python - "$BRANCH" <<'PY'
import subprocess, sys
want = sys.argv[1]
out = subprocess.check_output(["git", "worktree", "list", "--porcelain"], text=True)
block = []
for line in out.splitlines() + [""]:
    if not line.strip():
        path = branch = None
        for item in block:
            if item.startswith("worktree "):
                path = item.split(" ", 1)[1]
            elif item.startswith("branch "):
                branch = item.split(" ", 1)[1].replace("refs/heads/", "")
        if path and branch == want:
            print(path)
            raise SystemExit(0)
        block = []
    else:
        block.append(line)
raise SystemExit(f"no worktree for {want}")
PY
)"
cd "$WT"
[[ "$(git branch --show-current)" == "$BRANCH" ]] || {
  echo "worktree $WT is not on $BRANCH" >&2; exit 1;
}
if [[ -n "$(git status --porcelain)" ]]; then
  echo "worktree is dirty; commit or stash before launching." >&2
  git status -sb >&2
  exit 1
fi

git fetch origin main
echo "Rebasing $BRANCH onto origin/main ($(git rev-parse --short origin/main))..."
git rebase origin/main
echo "Post-rebase HEAD $(git rev-parse --short HEAD) $(git log -1 --format=%s)"

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
Continue on branch `gnhf/objective-given-the-d60385`. Do not create another
worktree. Do not merge to main. Do not amend existing commits. Do not push.

This is Companion-mode AUTHORING of the 11 Type B slides unblocked by recipes
now on origin/main (#283 shared dual support, #284 per-pane support, #286
chart_grouped_annex, #287 pie/donut, #288 annex compact). No production path
edits. No new recipes/schema/painters. No GitHub issues.

Read every applicable AGENTS.md and wiki/AGENT_LEARNINGS.md if present.
Read impact_slides/renderer_v3/models.py for DualChartPane, DualChartPayload,
ChartGroupedAnnexPayload, PieChartVisual, DonutChartVisual, ChartSlice,
AnnexTablePayload.density. Use CONTEXT.md Type A vs Type B vocabulary.

Source PDF (read-only):
  C:/Users/Ag1Le/Downloads/Q4-2021-Earnings-Presentation.pdf
  SHA-256 8e113208a6df838861fc06cdbfb82514f01f43c42a21e02005801f8fdf545e21
  53 pages, 720x404 landscape (capture at 1920x1080).

CRITICAL HOST BUG: GNHF runs `git add -A` after the agent returns. In this
repo `simulation/` is gitignored; that command fatals on a dirty tree and
kills the run. You MUST leave a clean working tree before returning success.

How:
1. Close playwright/chrome/python render processes first.
2. `git add -f simulation/amex_q4_2021/` (and the wiki report in commit 2).
3. Commit yourself. Then `git status` must be clean (no M files).
4. Only then return the iteration JSON.

Do not rely on GNHF to commit. If you return success with a dirty tree,
the orchestrator dies.

=== ALREADY DONE — DO NOT REDO ===

Type A pass is complete. Keep those slides. Named leftovers stay leftovers
(do not invent unread plot points): s05, s08, s20, s26, s30.

s22 feature_cards already unswapped from the PDF (commit message starts
`sim: unswap s22`). Keep:
  guide-2022: 2022 Guidance / Revenue Growth 18-20%. EPS $9.25-$9.65.
  expect-2023: 2023 Expectations / Higher than long-term aspirational levels of Revenue growth.
  aspire-2024: 2024+ Aspiration / Revenue Growth in excess of 10%. EPS Growth Mid-teens.
Do not swap them back. Do not fold qualifier bars into 2024+ (no recipe).

=== STILL TYPE B — DO NOT INVENT A RECIPE ===

s04 3-pane (stack + line + table). dual_chart is exactly two panes. Leave.
s24 share chips / brace groups. No mixed composition. Leave as data_table.
s35 freeform ESG strategy board. hierarchy cannot paint it. Leave.

=== RE-AUTHOR THESE 11 ===

Numbers only from the PDF page (PyMuPDF text/tables). Unreadable glyphs:
omit and name an extraction residual — do not guess. ASCII-only labels
(spell EUR/GBP/JPY, no dagger) so plan.conservative_metrics stays off.

s06, s07, s09 — dual_chart + PER-PANE support (#284).
  payload.charts: exactly two DualChartPane `{chart, support?}`.
  Do NOT set payload.support (shared and per-pane are mutually exclusive).
  Per-pane support_table may be category or independent; columns must match
  THAT pane's category_id order. outlined_support and metric_strip also
  legal per pane. Geometric vs-2019 callouts still have no recipe — omit
  them; tables + charts are enough to leave Type B.
  s06/s07 PDF: stacked mix + time series, each with an under-plot table.
  s09 PDF: two 8-quarter lines + two Q4 tables. Prefer line if each series
  has >=2 finite values (line validator rejects one-point series); else
  grouped_bar of labeled points + tables.

s21, s32 — dual_chart + SHARED support (#283).
  payload.support once under both panes. Do NOT also set pane.support.
  Shared support_table MUST be alignment: independent. Shared
  outlined_support is illegal. metric_strip 1-6 is legal.
  s21 PDF: CET1 bars + Capital Return bars + dividend strip. Two charts +
  shared metric_strip. Not 3-pane. Not chart_hero_dual.
  s32 PDF: two FX lines + 6-currency table. Two line charts (or grouped_bar
  if a series has <2 finite values) + shared independent support_table.
  dual_chart headings required (D170).

s25 — layout_type chart_grouped_annex (#286).
  payload `{chart, tables}` where tables is 1-2 GroupedAnnexPeer
  `{heading, table}` (optional short_heading). No payload.support.
  Chart is an axis ChartVisual (line/grouped_bar/stacked_bar/combo/
  waterfall; heatmap illegal). Unique surface_ids across chart + peers.
  PDF: 8-quarter Online/Offline/G&S line + two Q4 tables.

s27 — pie/donut chart_type on ChartVisual (#287).
  2-8 ChartSlice `{slice_id, label, value}` finite number >= 0.
  No chart_data / category_axis / value_axes / waterfall_data / table_data
  / boxed-label / authored-stack-total / coverage / display.stack_*.
  dual_chart accepts pie/donut (heatmap still forbidden).
  PDF: two mix donuts (Loan 68/12/20; Receivables 28/14/24/34). Author
  dual_chart of two donuts. Do not kernel-enforce sum-to-100.
  single_chart pie/donut may omit support or use independent support_table
  only (no category-aligned, no outlined_support).

s37, s38, s40, s43 — annex_table with payload.density: "compact" (#288).
  Keep layout_type annex_table. Omit density is today's annex; you WANT
  compact. Tightens cell x-pad to 4+4 (.annex-compact). Values unwrapped,
  no scroll, no ellipsis. Stub slack <=45% unless stub min exceeds that.
  grouped_annex_table has no compact switch — do not put density there.
  Author the full labeled period matrix from the PDF (18-19 columns), not
  the 2-4 column Q4/FY subset.
  If 18-col fits at compact, that slide leaves Type B.
  If 19-col still unresolved_overflow at the compact floor: do NOT drop
  columns, ellipsize, or invent a second page. Leave that slide Type B
  named leftover (fit ceiling remains). Prefer a clean strict deck: do
  not ship a handoff that fails strict because one annex overflowed —
  keep the last-known-strict subset only if compact full-width overflowed,
  and name it Type B leftover.

Update simulation/amex_q4_2021/build_handoff.py as the source of the
handoff, then write handoff_v1.json from it (or edit both in lockstep).
Validate as you go. dual_chart charts field is now DualChartPane; the
kernel wraps a bare ChartVisual as `{chart: item}` on read, but per-pane
support requires the pane envelope.

Also update capture_compare.py CHART_LAYOUTS to include
chart_grouped_annex so s25 paint-ready waits still run.

=== RENDER / CAPTURE ===

ONE published strict render after authoring:
  python -m impact_slides.renderer_v3 \
    --handoff simulation/amex_q4_2021/handoff_v1.json \
    --out simulation/amex_q4_2021/passes/pass_01/renderer_v3_out
Exit 0, run_meta.status=clean (or fully labeled DEGRADED). Never hand-edit HTML.

Reuse capture_compare.py: 1920x1080 dsf 1; wait_for_paint_ready_charts
before every chart-slide screenshot; no painted_datalabel_lines; no
DESIGN_LEDGER_* maps; no nth/fixed sleeps; stacked-deck fit transforms
cleared; 53 PDF + 53 HTML + 53 SBS (3840x1080) + contact sheet +
comparison_manifest.json. HTML slide N = PDF page N = PyMuPDF index N-1.

After capture, kill the browser. Confirm no chrome/playwright still holding PNGs.

=== LEDGER / COMMITS / STOP ===

Refresh simulation/amex_q4_2021/GAP_ANALYSIS.md; copy byte-for-byte to
wiki/baseline_q4_2021_RECIPE_COVERAGE.md. Reclassify only with fresh SBS.
Counts must match the manifest. Do not embed PNGs. Do not score images.

Expected remainder Type B: s04, s24, s35. Plus any compact-19 annex that
still overflows (named). Type B must drop from 14. Type A leftovers stay 5.

Create exactly two NEW commits (you make them; GNHF must see a clean tree):
1. `sim: re-author Q4 2021 Type B slides unblocked by #283-#288`
   `git add -f simulation/amex_q4_2021/` then commit
2. `docs: refresh Q4 2021 Type B recipe-coverage report`
   add only wiki/baseline_q4_2021_RECIPE_COVERAGE.md then commit

`git status` clean. Do not push (wincredman). Push is outside this worker.

Stop when:
- those two commits exist on this branch after the s22 unswap commit
- report copies byte-identical
- handoff 53 / schema 1 / p01..p53
- s22 cards still unswapped as above
- s06/s07/s09 have per-pane support; s21/s32 shared support; s25
  chart_grouped_annex; s27 pie/donut; s37/s38/s40/s43 compact or named
  19-col leftover
- s04/s24/s35 still Type B
- s05/s08/s20/s26/s30 still named Type A leftovers
- strict render clean or fully labeled degraded
- all 53 PDF/HTML/SBS exist at exact sizes
- manifest 53 rows; Type B count dropped vs 14
- no MAE/scoring; no production/test/script/config path changed
- working tree clean

Stop only on those proofs, or a precise blocker and no false success.
EOF

USERPROFILE="$Q4_HOME" HOME="$Q4_HOME" \
gnhf \
  --agent pi \
  --max-iterations 15 \
  --max-tokens 10000000 \
  --current-branch \
  --prevent-sleep on \
  --stop-when "Q4 2021 Type B re-author is done on gnhf/objective-given-the-d60385: the 11 unblocked slides (s06/s07/s09 per-pane support, s21/s32 shared support, s25 chart_grouped_annex, s27 pie/donut, s37/s38/s40/s43 compact annex) are re-authored from the PDF; s04/s24/s35 remain Type B; s22 stays unswapped; strict (or fully labeled degraded) render; 53 SBS; ledger Type B count dropped from 14; exactly two new commits; working tree clean; no production paths changed and no image scoring." \
  "$PROMPT"
