# Delegated ticket delivery

Use this workflow for parallel issue implementation, adversarial host review, no-mistakes correction, and approved PR merging.

## External prerequisites

This process depends on user-global tools and configuration, not files vendored in this repository:

- Pi Extensible Workflows (PEW)
- Herdr
- `no-mistakes axi`
- `gh` authenticated for `xryptox/Impact_Slides`
- workflow roles in `~/.pi/agent/pi-extensible-workflows/roles/`
- model aliases in `~/.pi/agent/pi-extensible-workflows/settings.json`

Expected roles:

- `implementer` — implements one issue in an isolated feature worktree
- `gate-driver` — recovery-only driver for an existing no-mistakes run; Kimi `review` model, `bash` only, all skills/extensions disabled (the role invokes the installed `no-mistakes` CLI directly)
- `reviewer` — Kimi read-only correctness/data-loss review with project/cwd DOX context, CodeMapper only, and no unrelated extensions
- `general-purpose` subagent in `~/.pi/agent/agents/general-purpose.md` — read-only Grok Latest worker required by the implement skill's two-axis `code-review` pass
- `merger` — cheap-model, approval-gated merge of one exact PR head; `bash` only with all skills/extensions disabled

The current `dev` alias and general-purpose Standards/Spec subagent use `openrouter/~x-ai/grok-latest` with high thinking. `review` remains the independent Kimi model and `cheap` remains reserved for merging. Terra is not used by the active delegated-delivery pipeline.

## Why Herdr wraps implementation

PEW's native child runtime resolves models before dynamically registered providers are loaded. A provider registered by an extension, such as SuperGrok, may therefore work in normal Pi but fail in native `agent(...)` calls with `UNKNOWN_MODEL`.

When that applies, use PEW for orchestration and isolated worktrees, but launch each full interactive Pi implementer in a visible tab in the supervising session's current Herdr workspace. Do not create a separate workspace or use `pi --print`: progress must remain observable alongside the supervisor. Start a supervising workflow watcher for each launched wave so idle/done/blocked panes—especially no-mistakes `ask-user` gates—produce a follow-up in the host session; Herdr status alone does not notify the host. Close a temporary tab only after collecting its final report and Git/no-mistakes state.

Durable workflow scripts:

- `~/.pi/agent/pi-extensible-workflows/scripts/start-ticket-wave.ps1` — primary interface: generates a delivery RunId, resolves the focused repo workspace and `dev` model, creates run-owned worktrees, launches tabs, and persists `wave.json` plus watcher targets
- `~/.pi/agent/pi-extensible-workflows/scripts/inspect-ticket-wave.ps1` — derives branch heads, cleanliness, exact-branch PRs, closing-reference state, CI metadata, and branch-bound no-mistakes state from `wave.json`
- `~/.pi/agent/pi-extensible-workflows/scripts/watch-ticket-wave.ps1` — persistent outer supervisor around the return-on-first-event watcher; keeps polling automatically and writes each event to the manifest's host follow-up file
- `~/.pi/agent/pi-extensible-workflows/scripts/resume-ticket-wave.ps1` — explicit restart for a wave paused after two unanswered decision notifications; clears only the selected decision reminder state and starts a replacement watcher
- `~/.pi/agent/extensions/ticket-wave-followups.ts` — global Pi extension that watches active-wave follow-up files for the current session and injects each event as a real supervising-session user follow-up
- `~/.pi/agent/pi-extensible-workflows/scripts/cleanup-ticket-wave.ps1` — derives merged PR numbers from run-owned branches, supports issue-scoped partial cleanup, updates manifest/targets, and delegates dry-run/apply deletion to verified cleanup
- `~/.pi/agent/pi-extensible-workflows/scripts/create-run-owned-worktree.ps1` — internal primitive that creates `pi-extensible-workflows/<RunId>/issue-<N>`
- `~/.pi/agent/pi-extensible-workflows/scripts/launch-visible-implementer.ps1` — internal primitive that verifies run ownership, creates the current-workspace tab, and starts a genuine interactive Pi TUI
- `~/.pi/agent/pi-extensible-workflows/scripts/orchestrate-herdr-implement-visible.ps1` — writes the implementation contract and launches the visible implementer
- `~/.pi/agent/pi-extensible-workflows/scripts/orchestrate-herdr-repair-visible.ps1` — writes the host-repair contract and launches the visible repair session
- `~/.pi/agent/pi-extensible-workflows/scripts/restart-visible-implementer.ps1` — crash-only restart in the existing pane; requires an exact clean branch/head plus recovery brief before relaunching the genuine TUI
- `~/.pi/agent/pi-extensible-workflows/scripts/watch-visible-implementers.ps1` — deduplicating return-on-first-event watcher that returns one idle/done/blocked or loop-limit event and no-mistakes state, raises a Herdr notification, persists its seen-state for rearming, and applies verified cleanup after every run-owned PR is merged and linked issue closed
- `~/.pi/agent/pi-extensible-workflows/scripts/cleanup-merged-workflow.ps1` — dry-run-first cleanup of merged workflow worktrees/branches after exact PR-head verification; tolerates already-deleted GitHub branches and partial waves
- `~/.pi/agent/pi-extensible-workflows/scripts/preflight-approved-pr.ps1` — deterministic base/head/check/mergeability/closing-reference preflight
- `~/.pi/agent/pi-extensible-workflows/scripts/Invoke-ApprovedMerge.ps1` — exact-head approved squash merge outside PEW persistence, used when Windows journal renames are unreliable

The launcher deliberately uses the user's normal Pi settings plus the `dev` alias resolved from the global PEW settings and the `implement` skill. The alias is the single model source; `wave.json` records its resolved value. This path preserves the real Pi TUI, repository tools, code-review subagents, and no-mistakes behavior. The former lean/RPC path was removed because injected lean sessions intermittently lost tools and RPC exposed raw JSON instead of the requested TUI. A workflow may create ticket briefs and result artifacts under `%TEMP%`, but must not depend on temporary launcher copies.

### Canonical launch and supervision

1. Start a wave with `start-ticket-wave.ps1 -Issue N,N,...`; normally provide no RunId, model, workspace, branch, worktree, pane, or targets-file input. The script infers and persists them in `wave.json`.
2. `start-ticket-wave.ps1` starts `watch-ticket-wave.ps1` automatically as the persistent outer supervisor (pass `-SkipWatcherStart` only for deterministic tests). A manifest-scoped singleton lock permits only one outer watcher per wave. It repeatedly invokes the deduplicating return-on-first-event watcher and keeps polling without manual rearm; unchanged idle/done/blocked signatures emit once, while `ask-user` alone retains the two-notification pause policy. Startup records the supervising `PI_SESSION_ID` and append-only follow-up queue in the active-wave registry; the global `ticket-wave-followups.ts` extension injects every queued event into that exact session. If no session ID is available, the watcher still persists and prints events for the caller.
3. Treat each delivered watcher event as the host notification. If it surfaces `ask-user`, present the finding verbatim and send the decision to the same pane. An unchanged unanswered decision is notified at most twice; the second event is `ask-user-paused`, sets `rearm: false`, and stops supervision without changing Git or no-mistakes custody. Resume only after an explicit user instruction with `resume-ticket-wave.ps1 -ManifestPath <wave.json> [-Issue N]`. If an event surfaces `loop-limit`, approve no further fixes: preserve custody and request controlled recovery. Default limits are more than 5 review-fix rounds, more than 90 minutes in review fixing, or quiet time confirmed by a CPU-delta check that finds the agent process dead or CPU-flat: more than 10 minutes during an active fix round, or more than 25 minutes during the initial review (a single long model call). Persisted state suppresses other unchanged repeats until the reminder interval.
4. Use `inspect-ticket-wave.ps1 -ManifestPath <wave.json>` for authoritative branch/PR/gate collection instead of manually copying identifiers.
5. Launch returned host findings with `orchestrate-herdr-repair-visible.ps1 -RunId <wave RunId>` against the manifest worktree. It writes `repair-prompt.md`, copies the authoritative host findings, and explicitly supersedes the original implementation prompt. Do not substitute direct branches, `herdr pane run`, RPC, `pi --print`, or another workspace.
6. Keep tabs open while a decision or pipeline action remains outstanding. Inspection and watching bind no-mistakes status to the ticket branch's recorded run ID rather than trusting the CLI's most-recent run. After every run-owned PR is `MERGED`, every linked issue is closed, and each implementer is terminal with its final report collectible, the watcher closes the tabs, runs `cleanup-ticket-wave.ps1` dry-run then `-Apply`, emits the cleanup result, and exits. For an already merged subset, pass `-Issue N,...`; partial cleanup updates `wave.json` and `targets.json`.
7. A PR that is only `CLOSED` is not cleanup authorization. The watcher reports the block and preserves all artifacts. Herdr desktop notifications are best-effort and must never terminate supervision. Cleanup treats Git-registration removal plus a temporarily locked empty Windows directory as partial success: it retries the manifest-recorded directory independently and remains idempotent after registration or refs disappear. If automatic cleanup still fails, inspect `wave.json` and rerun `cleanup-ticket-wave.ps1 -ManifestPath <wave.json>` manually.

A deliberately stopped or superseded watcher may report `CANCELLED`; verify the replacement run ID and implementation state, then treat that notification as expected rather than an implementation failure.

## Delivery sequence

### 1. Prepare a dependency wave

- Read the root and applicable child `AGENTS.md` files.
- Fetch each issue and its comments/labels.
- Group only independent tickets in the same parallel wave.
- Give every ticket its own run-owned branch and worktree via `create-run-owned-worktree.ps1`; use one shared RunId for a cleanup batch.
- Record the RunId, starting SHA, issue number, worktree, branch, and expected changed paths.

### 2. Implement in visible tabs

Each implementer must:

- launch through `orchestrate-herdr-implement-visible.ps1` (or `orchestrate-herdr-repair-visible.ps1` for returned work), which delegates tab creation to `launch-visible-implementer.ps1` in the supervising session's current Herdr workspace;
- immediately start one background return-on-first-event watcher using `watch-visible-implementers.ps1` for every pane in the wave; rearm it after each delivered event until every implementer reaches its collected terminal report;
- invoke/read the `implement` skill explicitly;
- use TDD where practical and run the `code-review` skill's parallel Standards and Spec subagents before no-mistakes;
- change only its issue scope;
- run focused checks, mutation/adversarial proof, one final full suite, and `python scripts/gen_layout_index.py --check` when relevant;
- complete the DOX pass;
- commit on the feature branch;
- run the full no-mistakes gate itself;
- report commits, tests, mutations, review results, no-mistakes run ID/findings/fixes, PR URL, CI state, and blockers.

`ask-user` findings are escalation points. An implementer must not decide them without explicit standing consent. The watcher sends at most two notifications for the same unanswered decision, then pauses until the user explicitly resumes that ticket or wave.

No-mistakes review loops are also escalation points. After more than 5 review-fix rounds, 90 minutes in review fixing, or CPU-confirmed stalled quiet time (10 minutes in a fix round, 25 minutes in the initial review; growing CPU means a long model call, not a stall), approve no further fix: report the run, head, round/time, and current findings, preserve pipeline custody, and wait for controlled recovery.

### 3. Respect no-mistakes custody

A live no-mistakes pipeline owns unpublished correction commits.

- Never edit, reset, rebase, or start a duplicate run while it owns the branch.
- Inspect with `no-mistakes axi status`.
- If local and pipeline heads differ, use `no-mistakes axi sync`; use `sync --recover` only when AXI explicitly reports recoverable divergence.
- Preserve pipeline commits and rerun affected checks after reconciliation.
- The CI stage normally remains active until its PR is merged or closed. A green PR plus `all CI checks passed - still monitoring until merged or closed` is the correct implementer handoff state, not a stuck run.
- The implementer must report that monitoring state and end its Pi turn without stopping the monitor. Never run `no-mistakes axi abort` merely because the implementer is forbidden to merge; abort only on an explicit user instruction or an authoritative no-mistakes recovery instruction.

Treat update notices on stderr as notices, not task failures. Verify GitHub, Git, and `no-mistakes axi status` directly when a wrapper reports `BLOCKED`.

### 4. Host verification

A green suite is not sufficient in this repository. The supervising host must inspect the final pipeline head and use the smallest relevant combination of:

- mutation testing;
- same-worktree before/after output comparison;
- Playwright geometry on the real archived handoff;
- facade/registry identity checks;
- malformed-input sweeps;
- focused tests plus the full suite and layout-index gate.

Return real defects to the same implementer and existing no-mistakes run. Do not patch pipeline-owned branches from the host.

### 5. Prepare merge metadata

Before approval, run `preflight-approved-pr.ps1` (or equivalent inspection) and verify that every PR:

- targets `main`;
- is open and non-draft;
- is clean/mergeable;
- has green required checks;
- has the reviewed exact head SHA;
- contains `Closes #N` (or equivalent). The watcher emits `metadata-blocked` before terminal delivery when this is absent.

Record the exact head SHA presented for approval.

### 6. Approval and merge

The user may approve one exact PR or a named batch. Batch approval is conditional and serial:

1. Launch the `merger` role once per PR, or invoke `Invoke-ApprovedMerge.ps1` with the same literal approval and exact-head inputs when Windows PEW persistence is unreliable.
2. Supply PR number, reviewed head SHA, and literal `HUMAN_APPROVAL: true`.
3. Recheck against current `main` after every preceding merge.
4. Squash-merge and delete the remote branch only when all role checks pass.
5. Stop the batch on a changed head, conflict, pending/failed check, missing closing reference, or changed scope.

A feature-head change invalidates approval and requires fresh host review and approval. A `main` change caused only by an earlier approved merge does not invalidate the batch, but the next PR must still be recalculated and clean.

The merger role must not edit code/metadata, force, use admin bypass, update local `main`, or clean worktrees.

### 7. Closeout

After merges:

- fetch and fast-forward/reconcile the root checkout without discarding local commits;
- confirm linked issues closed;
- let no-mistakes monitors reach terminal state;
- let the rearmed watcher close collected tabs and run the manifest-derived cleanup dry-run plus `-Apply`; if it reports failure, use `cleanup-ticket-wave.ps1 -ManifestPath <wave.json>` manually rather than bypassing verification;
- delete the terminal run from `/workflow` after Git cleanup to remove persisted metadata;
- report merge SHAs, unresolved PRs, and any cleanup intentionally deferred.

## Windows failure modes

- PEW journal persistence can fail with `EPERM` during atomic rename after an external merge succeeded. Prefer `Invoke-ApprovedMerge.ps1` for the deterministic merge side effect; if a PEW merger was used, query the PR before retrying and never assume exactly-once external effects.
- PowerShell native stderr can be promoted to an exception. Classify using exit code and authoritative state, not stderr text alone.
- Herdr marks a completed interactive Pi as `done`; `herdr wait agent-status --status idle` does not accept/observe that terminal state. Poll `herdr pane list` for `done` or `idle`, then collect the report and close the tab.
- Quote Git revision ranges as one normal argument (`base..head`); malformed nested quoting can make Git treat the range as a filename.
- PEW workflow JavaScript is sandboxed: do not assume `Date.now()` or Bash shell syntax is available; `shell()` uses the host Windows shell.
- A local branch deletion may fail while its linked worktree exists even though the GitHub merge and remote branch deletion succeeded.
