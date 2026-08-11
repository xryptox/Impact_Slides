# Agent Learnings

Operational learnings from supervised ticket-wave delivery. **Live document: delegated-wave supervisors and implementers must read this before starting wave work.** Update it after every wave that produces durable lessons; delete entries that stop being true instead of keeping history.

Source: renderer-v3 wave `ab6a85b4` (2026-08-11; #184/#186/#189/#193/#194/#196 — four merged, two parked to #215/#216).

## Verification and measurement

1. **Verify bytes, never displayed text.** The supervisor terminal wrapper silently drops comma-space sequences in all displayed output (grep, sed, od, read, git show). This made correct comma-separated CSS look "compound" for three review rounds; the fixer had landed the edit every time. For byte-critical claims (CSS selectors, literal strings, file equality) use Python byte counts (`d.count(b'...')`) or file hashes. Rule also documented in `docs/agents/delegated-delivery.md`.
2. **When the same fix "fails to land" repeatedly, suspect the measurement channel before the fixer.** Three identical failures were a corrupted read, not a broken write.
3. **Discriminating probes beat suite-green as evidence.** Build a minimal mutation that flips behavior between fixed and unfixed code (e.g. content that exceeds the stage budget only when the defect is present). It proves the fix works *and* produces no false positives. Keep the probe content calibrated: overshooting windows trigger unrelated overflows and destroy discrimination.
4. **Playwright full-deck audit tests flake under full-suite concurrency.** Before calling a regression, rerun the failing test standalone on both the PR head and main.

## Pipeline mechanics (no-mistakes + herdr)

5. **The pipeline owns the branch.** Fix-round commits live in daemon worktrees (`~/.no-mistakes/worktrees/<repo-hash>/<runId>/`); pane worktrees stay stale. Event-reported heads can be transient sync artifacts. Ground truth is the GitHub API `headRefOid` plus byte-level diffs; the push step rebases onto current main.
6. **Every merge to main CONFLICTS all other in-flight branches.** Budget one rebase pass per merge for each remaining ticket. Let the pipeline's AI-assisted rebase do union merges; hand-resolving 1000+ line diverged hunks is higher risk (aborted once in this wave).
7. **Parallel waves over shared files duplicate work.** #196 re-implemented #214's stacked-bar code because both cut from the same base. Sequence tickets that touch the same files, and tell rebasing implementers to prefer MAIN on overlap.
8. **herdr `BrokenPipe` (Windows error 232) is transient.** Retry once after a short sleep; confirm pane liveness with `herdr pane list` before assuming a pane died.
9. **Watcher dedup signatures must use stable fields only.** Heads advance per fixer commit and `axi status` summary strings churn on parse wobble (the false update banner on stderr); both flooded follow-ups. Stable axes: run + breached-kind + review-fix-round for loop limits; run + head + finding-count for parked gates.
10. **PowerShell traps:** pass int arrays via `pwsh -Command "& script -Issue 1,2,3"` (not `-File` with commas); backticks inside double-quoted here-strings are consumed as escapes and silently corrupt generated prompts (this garbled every implementer contract for an entire wave generation) — render generated templates and inspect them, not just parse-check; Python on Windows needs `%LOCALAPPDATA%`-style paths, and UTF-8 output needs explicit encoding.
11. **Layout index staleness is a recurring CI class.** Any fixture change requires regenerating `wiki/renderer_v2_LAYOUTS.md` via `scripts/gen_layout_index.py`; every branch in the wave hit this once.

## Supervision and escalation

12. **Contract wording alone does not bind implementers.** All six early parked gates were self-decided by implementers despite explicit "escalate, never decide" text. What worked: explicit parked-gate parking rules + relay-execution-exactly rules + live relays into active panes + md5-pinned staged files the pane only copies. Delegate verified artifacts, not decisions.
13. **Park with a pre-staged recovery.** Before releasing a parked pane: implement and host-verify the next fix yourself, commit it on a recovery branch, stage the file md5-pinned in `%LOCALAPPDATA%\Temp\`, and rewrite the follow-up issue with exact resume head, outstanding finding, repro, and tooling notes. Parking is then a state, not a loss.
14. **When the supervisor authors the code, the supervisor owns its findings.** Late-round defects came from supervisor-staged fixes; the honest move is to verify and relay the correction under an explicit hard stop, not to invoke the stop selectively.
15. **Hard stops need user consent per exception round.** State the stop, report the new finding with an A/B recommendation, and let the user authorize any further round. Batched approvals with explicit options and a recommendation keep long waves moving on few user tokens.
16. **Intentional parks require stopping the wave watcher**, or quiet-limit escalation events re-escalate the parked gate as noise.

## Renderer-v3 architecture

17. **Fit/paint CSS parity is the systemic defect class of this renderer.** Constants must be read from the emitted CSS in `publish.py` (e.g. padding 12 vs a fitter's `CARD_PAD` 16), including flex gaps, per-element margins, and list indent (`ul` padding-left plus global `li` margin-left stacks). Incremental finding-by-finding fixes cannot converge on a systemic class; after 2-3 findings in one family, park to a focused audit ticket. Collapse stacked list indents to one `LIST_INDENT_EM`; always-on trailing margins (`.item-statement` mb 4) count even without detail.
18. **Mirror failure: chrome double-counting.** Once a fitter returns full painted height *including* card padding, the plan's `_chrome_h` for that surface must be zero, or dual-band math adds the padding twice. Whenever a fit function changes what it includes, audit every `_chrome_h` consumer.
19. **Clamps need membership-accurate filters.** The hero_restore stage clamp first filtered siblings by `layout_type` (matched everything on the slide → no-op), then by `_chart_spec is None` (over-counted left-column support inside `left_total` → false clamps). Correct set = same-slide surfaces minus the dual-band members (chart/hero/support from the slot map). Prove both directions: false-clamp windows go clean, true overages still fail strict with `plan.unresolved_overflow`.
20. **Measurement architecture: per-row fitters for mixed-size boards.** `hero_card`/`metric_overview` paint mixed font sizes and CSS gaps; a single-size `_required_height` collapses them. Model each painted row with its role size plus the exact painted gaps/margins (see `_hero_fit_height` / `_metric_overview_fit_height`), and keep newline unit sentinels between text groups so `_split_units` measures per row.
