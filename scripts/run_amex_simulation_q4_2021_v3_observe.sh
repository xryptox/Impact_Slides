#!/usr/bin/env bash
# GNHF Q4 2021 observation: reset gnhf/objective-given-the-d60385 onto
# origin/main (renderer_v3 through #339/#340/#341), recapture 53 SBS on that
# corpus, refresh identity hashes + ledger.
# No re-author. Reset, not rebase: the branch's Type B commits add/add-conflict
# the Q4 corpus already on main. Does not --push.
set -euo pipefail

REAL_HOME="${REAL_HOME:-C:/Users/Ag1Le}"
Q4_HOME="${LOCALAPPDATA:-C:/Users/Ag1Le/AppData/Local}/Temp/gnhf-q4-2021-v3-observe-supergrok"
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
echo "Resetting $BRANCH onto origin/main ($(git rev-parse --short origin/main))..."
# Observation wants main's Q4 handoff. Rebase of the Type B history
# add/add-conflicts GAP_ANALYSIS.md / build_handoff.py / handoff_v1.json.
CC_SRC="simulation/amex_q4_2021/capture_compare.py"
CC_BAK=""
if [[ -f "$CC_SRC" ]]; then
  CC_BAK="$(mktemp)"
  cp "$CC_SRC" "$CC_BAK"
fi
git reset --hard origin/main
if [[ -n "$CC_BAK" && ! -f "$CC_SRC" ]]; then
  mkdir -p simulation/amex_q4_2021
  cp "$CC_BAK" "$CC_SRC"
fi
[[ -n "$CC_BAK" ]] && rm -f "$CC_BAK"
echo "Post-reset HEAD $(git rev-parse --short HEAD) $(git log -1 --format=%s)"
echo "Contains origin/main? $(git merge-base --is-ancestor origin/main HEAD && echo yes || echo NO)"

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

This is Companion-mode OBSERVATION of the Q4 2021 deck on current
renderer_v3 (origin/main through #339/#340/#341). The worktree was already
reset hard onto origin/main.

No further production path edits. No new recipes/schema/painters. No
GitHub issues. Do NOT re-author slides. Do NOT invent numbers. Do NOT
change build_handoff.py, handoff_v1.json, charts.py, or tests unless a
strict render proves the existing handoff is now illegal — then stop
and name the blocker. Do NOT revert #339/#340/#341.

Read every applicable AGENTS.md and wiki/AGENT_LEARNINGS.md if present.
Use CONTEXT.md Type A vs Type B vocabulary.

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

=== ALREADY ON THIS BRANCH — DO NOT REDO ===

Keep the current Q4 handoff (includes #335 s13 two-tone and #339/#340/#341 s27 24px).
Named Type A leftovers stay leftovers (do not invent unread plot points):
s05, s08, s20, s26, s30.
#301 unlabeled interiors on s06/s07/s09/s25/s32 stay leftovers.
Type B remainder: s35 freeform ESG strategy board. Leave.

s22 feature_cards stay unswapped:
  guide-2022 / expect-2023 / aspire-2024 as already authored.

=== OBSERVE THESE KERNEL RESULTS ===

Strict-render the existing handoff with live renderer_v3. Recapture SBS.
Check each against the PDF page and the ticket contract. Record pass/fail
in the ledger with fresh identity hashes. Do not "fix" by re-authoring.

#315 s03: Chart.js y domain −40…20, 7 ticks. Interiors stay Type A leftover.
#316 s06/s07/s09: independent navy-header support_table (not category boxes).
#336 s06/s07/s09: both independent support tables freeze at the larger type
  (24px), not floor 14. Column widths stay independent.
#317 s11: both panes fixed domain 0…5.
#318 s12: stacked_bar Write-offs + Reserve Build, no Total Provision line.
#319/#335 s13: waterfall two-tone loans (primary_blue) + receivables (navy)
  on six of seven steps; Change to Q4'21 component-less net; thin/$0.0 caps
  still painted; never fit-drop non-zero components.
#320 s15/s17: chart_grouped_annex grouped_bar + rate/yield annex; no combo line.
#321 s24: chart_grouped_annex + share chips + two tables.
#322 s27: dual donuts; names outside the ring; same-slide slice_id fill
  identity; small-wedge % sits with the outside name (not back in the ring).
#339/#340 s27: both donuts ordinary_values 24px; equal outside pads grow so
  the ring shrinks (pad_l == pad_r > 160); no slice_label_overflow; mix
  percents unchanged (loans 68/12/20, rec 28/14/24/34).
#341 s27: outside name/percent AABB clears the painted disk (not just the
  name anchor); Corporate Card does not cross the ring; still 24px; still
  no slice_label_overflow at 1920x1080.
#323/#342 s28: two-row category-aligned Total Loans / CM Receivables boxes with
  frozen 24px row gap, stub-safe wider centered boxes, borderless stubs;
  not a navy IR table; figures unchanged.
#324 s28/s31: same-column stack labels do not share an AABB; $0.0 CPR stays
  a cap; s31 4%/1%/2% still visible; never fit-drop non-zero.

If a kernel result is missing or still collides at 1920×1080, name it as a
residual in the ledger. Do not drop labels, shrink floors, or invent recipes.

=== RENDER / CAPTURE ===

ONE published strict render:
  python -m impact_slides.renderer_v3 \
    --handoff simulation/amex_q4_2021/handoff_v1.json \
    --out simulation/amex_q4_2021/passes/pass_01/renderer_v3_out
Exit 0, run_meta.status=clean (or fully labeled DEGRADED). Never hand-edit HTML.

Reuse capture_compare.py (gitignored prior-run copy is fine): 1920x1080 dsf 1;
wait_for_paint_ready_charts before every chart-slide screenshot; no
painted_datalabel_lines; no DESIGN_LEDGER_* maps; no nth/fixed sleeps;
stacked-deck fit transforms cleared; 53 PDF + 53 HTML + 53 SBS (3840x1080)
+ contact sheet + comparison_manifest.json. HTML slide N = PDF page N =
PyMuPDF index N-1.

After capture, kill the browser. Confirm no chrome/playwright still holding PNGs.

=== LEDGER / COMMITS / STOP ===

Refresh simulation/amex_q4_2021/GAP_ANALYSIS.md identity table (bytes +
SHA-256 of presentation.html and run_meta.json from THIS published render —
do not leave prior-run pins). Copy byte-for-byte to
wiki/baseline_q4_2021_RECIPE_COVERAGE.md.
Reclassify only with fresh SBS. Counts must match the manifest. Do not
embed PNGs. Do not score images.

Type B remainder stays s35 unless a kernel check newly fails a previously
accepted slide — then name that residual; do not invent a recipe to clear it.
Type A leftovers stay 5.

Create exactly two NEW commits after origin/main
(you make them; GNHF must see a clean tree):
1. `sim: recapture Q4 2021 on post-#341 renderer_v3`
   `git add -f simulation/amex_q4_2021/` then commit
2. `docs: refresh Q4 2021 recipe-coverage after #315-#341`
   add only wiki/baseline_q4_2021_RECIPE_COVERAGE.md then commit

`git status` clean. Do not push (wincredman). Push is outside this worker.

Stop when:
- those two commits exist on this branch after origin/main
- report copies byte-identical
- identity table hashes match this render's presentation.html and run_meta.json
- handoff 53 / schema 1 / p01..p53
- each #315-#341 check above is pass or a named residual
- s35 still Type B; s05/s08/s20/s26/s30 still named Type A leftovers
- strict render clean or fully labeled degraded
- all 53 PDF/HTML/SBS exist at exact sizes
- manifest 53 rows
- no MAE/scoring; no production/test/script/config/handoff re-author
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
  --stop-when "Q4 2021 observation on gnhf/objective-given-the-d60385 is done: worktree is origin/main plus two new commits; existing Q4 handoff strictly rendered; 53 SBS recaptured; GAP identity hashes match this render; wiki report byte-identical; #315-#341 checks are pass or named residuals; s35 stays Type B; Type A leftovers stay; working tree clean; no re-author, no production path changes, no image scoring." \
  "$PROMPT"
